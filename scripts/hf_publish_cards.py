"""Publish the Hugging Face dataset cards sourced in huggingface/datasets/<id>/README.md.

GitHub is the source of truth for these cards; the Hub copy is downstream. For each
dataset this script:

1. reads the card bytes from the checkout (the git blob for the commit being published),
2. reads the Hub's current README.md at the dataset's current head revision,
3. skips the dataset when the bytes already match,
4. otherwise uploads README.md only (never the payload), pinned to that head revision as
   the parent commit so a concurrent Hub edit makes the upload fail instead of being
   overwritten, with the GitHub commit SHA in the Hub commit message, and
5. reads README.md back at the new Hub revision and fails unless its sha256 equals the
   sha256 of the local card.

The token is read from the HF_TOKEN environment variable. Exit status is non-zero if any
dataset fails.

Source freshness is checked before every step that can write or report success: the card and
the publisher files must have the same blobs on current canonical main as in this checkout.
A main commit that changes none of them (and so is outside the workflow's push paths) does not
stop this run. One that changes any of them stops the batch, leaving the remaining datasets to
the publish run that such a push triggers. A write always covers every dataset, so a queued
write that a newer one displaces is still covered; only a dry run can be narrowed (--dataset).
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HUB_ORG = "SZLHOLDINGS"
DATASETS = ("uds-bundles-v1", "uds-spans-receipts", "uds-governance-receipts")
SOURCE_REPO = "szl-holdings/uds-bundles"
SOURCE_URL = f"https://github.com/{SOURCE_REPO}.git"
ROOT = Path(__file__).resolve().parents[1]
# Besides the cards, the files whose change on main starts a publish run (the workflow's push
# paths). A run is stale once main changes its card or any of these.
PUBLISHER_PATHS = (
    "scripts/hf_publish_cards.py",
    "tests/test_hf_publish_cards.py",
    ".github/workflows/hf-dataset-cards-publish.yml",
)
FULL_SHA = re.compile(r"[0-9a-f]{40}")


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def card_path(root, dataset):
    return Path(root) / "huggingface" / "datasets" / dataset / "README.md"


def commit_message(git_sha):
    return f"docs(card): sync README.md from {SOURCE_REPO}@{git_sha}"


class StaleSource(RuntimeError):
    """Current canonical main no longer has this run's card or publisher (or cannot be read)."""


class SourceGuard:
    """Require the exact tracked card, unchanged on the current canonical main commit."""

    def __init__(self, root, git_sha):
        if not FULL_SHA.fullmatch(git_sha):
            raise ValueError("source revision must be a full Git commit SHA")
        self.root, self.git_sha = Path(root), git_sha
        self._fetched = {git_sha}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], timeout=30)

    def __call__(self, dataset):
        if self.git("rev-parse", "HEAD").decode().strip() != self.git_sha:
            raise RuntimeError("checkout does not match the claimed source revision")
        path = card_path(self.root, dataset)
        card = path.relative_to(self.root).as_posix()
        tracked = self.git("show", f"{self.git_sha}:{card}")
        if tracked != path.read_bytes():
            raise RuntimeError("source card differs from the claimed Git blob")
        remote = self.git("ls-remote", SOURCE_URL, "refs/heads/main").decode().split()
        if len(remote) != 2 or remote[1] != "refs/heads/main" or not FULL_SHA.fullmatch(remote[0]):
            raise StaleSource("canonical main could not be read; treating the source as stale")
        main = remote[0]
        if main == self.git_sha:
            return
        if main not in self._fetched:
            self.git("fetch", "--quiet", "--no-tags", "--depth=1", SOURCE_URL, main)
            self._fetched.add(main)
        inputs = (card, *PUBLISHER_PATHS)
        if self.git("ls-tree", main, "--", *inputs) != self.git("ls-tree", self.git_sha, "--", *inputs):
            raise StaleSource(f"source revision is stale; canonical main {main} changed the card "
                              "or the publisher")


class HubClient:
    """Thin wrapper over huggingface_hub so the publish logic can be tested offline."""

    def __init__(self, token):
        from huggingface_hub import HfApi

        self._api = HfApi(token=token)
        self._token = token

    def head(self, repo_id):
        return self._api.dataset_info(repo_id).sha

    def read_readme(self, repo_id, revision):
        from huggingface_hub.errors import EntryNotFoundError

        with tempfile.TemporaryDirectory() as tmp:
            try:
                path = self._api.hf_hub_download(
                    repo_id,
                    "README.md",
                    repo_type="dataset",
                    revision=revision,
                    cache_dir=tmp,
                    force_download=True,
                )
            except EntryNotFoundError:
                return None
            return Path(path).read_bytes()

    def upload_readme(self, repo_id, data, parent, message, description):
        info = self._api.upload_file(
            path_or_fileobj=data,
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            parent_commit=parent,
            commit_message=message,
            commit_description=description,
        )
        return info.oid


def observe_tip(client, repo_id):
    """The Hub head; an unobservable head must never become parent_commit=None (no CAS)."""
    tip = client.head(repo_id)
    if not isinstance(tip, str) or not tip:
        raise RuntimeError(f"Hub head of {repo_id} could not be observed")
    return tip


def tip_is_stable(client, repo_id, expected, result):
    """Read the head after every other check and require the revision the outcome names."""
    result["hub_head_after"] = observe_tip(client, repo_id)
    return result["hub_head_after"] == expected


def publish_one(client, root, dataset, git_sha, description, dry_run=False, *, source_guard,
                result=None):
    """Publish one card. Returns a result dict; result['ok'] is False on failure.

    A caller-supplied `result` is filled in place, so what was observed (and any upload already
    made) stays on record when this raises.
    """
    repo_id = f"{HUB_ORG}/{dataset}"
    result = {} if result is None else result
    result.update(dataset=repo_id, ok=False)
    source_guard(dataset)
    local = card_path(root, dataset).read_bytes()
    result["local_sha256"] = sha256_hex(local)

    head = observe_tip(client, repo_id)
    result["hub_head_before"] = head
    current = client.read_readme(repo_id, head)
    result["hub_sha256_before"] = sha256_hex(current) if current is not None else None

    if current == local:
        source_guard(dataset)
        if not tip_is_stable(client, repo_id, head, result):
            result["error"] = "Hub head changed during unchanged-card verification"
            return result
        result.update(action="unchanged", hub_revision=head, hub_sha256=result["local_sha256"], ok=True)
        return result
    if dry_run:
        source_guard(dataset)
        if not tip_is_stable(client, repo_id, head, result):
            result["error"] = "Hub head changed during comparison"
            return result
        result.update(action="would-upload", ok=True)
        return result

    source_guard(dataset)
    revision = client.upload_readme(repo_id, local, head, commit_message(git_sha), description)
    result["action"] = "uploaded"
    result["hub_revision"] = revision
    if not revision or revision == head:
        result["error"] = "upload returned no new Hub revision"
        return result

    readback = client.read_readme(repo_id, revision)
    result["hub_sha256"] = sha256_hex(readback) if readback is not None else None
    if result["hub_sha256"] != result["local_sha256"]:
        result["error"] = "read-back sha256 does not match the source card"
        return result
    source_guard(dataset)
    if not tip_is_stable(client, repo_id, revision, result):
        result["error"] = "Hub head changed during uploaded-card verification"
        return result
    result["ok"] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--git-sha", required=True, help="GitHub commit SHA being published")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DATASETS,
        help="dry run only: dataset to compare (repeatable); default: all three",
    )
    parser.add_argument("--run-url", default="", help="URL of the publishing workflow run")
    parser.add_argument("--dry-run", action="store_true", help="compare only; never upload")
    args = parser.parse_args(argv)
    if args.dataset and not args.dry_run:
        parser.error("--dataset narrows a dry run only; a write covers every dataset so that a "
                     "queued write it displaces is still covered")

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("::error::HF_TOKEN is empty; refusing to publish", file=sys.stderr)
        return 2

    description = f"Source: https://github.com/{SOURCE_REPO}/blob/{args.git_sha}/huggingface/datasets"
    if args.run_url:
        description += f"\nPublished by: {args.run_url}"

    client = HubClient(token)
    source_guard = SourceGuard(ROOT, args.git_sha)
    results, stopped = [], None
    for dataset in args.dataset or DATASETS:
        result = {"dataset": f"{HUB_ORG}/{dataset}", "ok": False}
        results.append(result)
        if stopped:
            result.update(action="not-attempted", error=stopped)
            continue
        try:
            publish_one(client, ROOT, dataset, args.git_sha, description, args.dry_run,
                        source_guard=source_guard, result=result)
        except StaleSource as exc:  # never publish stale bytes: stop and leave the rest to main
            result.setdefault("action", "stale-source")  # an upload already made stays "uploaded"
            result.update(ok=False, error=f"{type(exc).__name__}: {exc}")
            stopped = f"stopped after {dataset}: {exc}"
        except Exception as exc:  # report every dataset, then fail
            result.update(ok=False, error=f"{type(exc).__name__}: {exc}")

    print(json.dumps(results, indent=2))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
