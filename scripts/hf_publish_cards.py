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
ROOT = Path(__file__).resolve().parents[1]


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def card_path(root, dataset):
    return Path(root) / "huggingface" / "datasets" / dataset / "README.md"


def commit_message(git_sha):
    return f"docs(card): sync README.md from {SOURCE_REPO}@{git_sha}"


class SourceGuard:
    """Require the exact tracked card from the current canonical main commit."""

    def __init__(self, root, git_sha):
        if not re.fullmatch(r"[0-9a-f]{40}", git_sha):
            raise ValueError("source revision must be a full Git commit SHA")
        self.root, self.git_sha = Path(root), git_sha

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], timeout=30)

    def __call__(self, dataset):
        if self.git("rev-parse", "HEAD").decode().strip() != self.git_sha:
            raise RuntimeError("checkout does not match the claimed source revision")
        path = card_path(self.root, dataset)
        tracked = self.git("show", f"{self.git_sha}:{path.relative_to(self.root).as_posix()}")
        if tracked != path.read_bytes():
            raise RuntimeError("source card differs from the claimed Git blob")
        remote = self.git("ls-remote", f"https://github.com/{SOURCE_REPO}.git", "refs/heads/main")
        if remote.decode().split() != [self.git_sha, "refs/heads/main"]:
            raise RuntimeError("source revision is stale; canonical main has advanced")


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


def publish_one(client, root, dataset, git_sha, description, dry_run=False, *, source_guard):
    """Publish one card. Returns a result dict; result['ok'] is False on failure."""
    repo_id = f"{HUB_ORG}/{dataset}"
    source_guard(dataset)
    local = card_path(root, dataset).read_bytes()
    result = {"dataset": repo_id, "local_sha256": sha256_hex(local), "ok": False}

    head = client.head(repo_id)
    result["hub_head_before"] = head
    current = client.read_readme(repo_id, head)
    result["hub_sha256_before"] = sha256_hex(current) if current is not None else None

    if current == local:
        if client.head(repo_id) != head:
            result["error"] = "Hub head changed during unchanged-card verification"
            return result
        source_guard(dataset)
        result.update(action="unchanged", hub_revision=head, hub_sha256=result["local_sha256"], ok=True)
        return result
    if dry_run:
        if client.head(repo_id) != head:
            result["error"] = "Hub head changed during comparison"
            return result
        source_guard(dataset)
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
    if client.head(repo_id) != revision:
        result["error"] = "Hub head changed during uploaded-card verification"
        return result
    source_guard(dataset)
    result["ok"] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--git-sha", required=True, help="GitHub commit SHA being published")
    parser.add_argument(
        "--dataset",
        action="append",
        choices=DATASETS,
        help="dataset to publish (repeatable); default: all three",
    )
    parser.add_argument("--run-url", default="", help="URL of the publishing workflow run")
    parser.add_argument("--dry-run", action="store_true", help="compare only; never upload")
    args = parser.parse_args(argv)

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("::error::HF_TOKEN is empty; refusing to publish", file=sys.stderr)
        return 2

    description = f"Source: https://github.com/{SOURCE_REPO}/blob/{args.git_sha}/huggingface/datasets"
    if args.run_url:
        description += f"\nPublished by: {args.run_url}"

    client = HubClient(token)
    source_guard = SourceGuard(ROOT, args.git_sha)
    results = []
    for dataset in args.dataset or DATASETS:
        try:
            results.append(publish_one(client, ROOT, dataset, args.git_sha, description, args.dry_run,
                                       source_guard=source_guard))
        except Exception as exc:  # report every dataset, then fail
            results.append({"dataset": f"{HUB_ORG}/{dataset}", "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    print(json.dumps(results, indent=2))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
