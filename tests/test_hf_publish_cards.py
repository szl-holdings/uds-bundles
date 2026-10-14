"""Offline tests for scripts/hf_publish_cards.py (no network, no credentials)."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import hf_publish_cards as pub  # noqa: E402

WORKFLOW = ROOT / ".github" / "workflows" / "hf-dataset-cards-publish.yml"
RealHubClient = pub.HubClient  # setUpModule replaces pub.HubClient with an inert guard
_INERT = []


def setUpModule():
    """Inert transport: any real socket, git process or Hub client fails the test instead."""
    def refuse(*_args, **_kwargs):
        raise AssertionError("offline test attempted a real network connection")

    for inert in (
        patch.object(socket.socket, "connect", refuse),
        patch.object(socket, "create_connection", refuse),
        patch.object(pub.subprocess, "check_output",
                     side_effect=AssertionError("offline test attempted to run git")),
        patch.object(pub, "HubClient",
                     side_effect=AssertionError("offline test attempted to build a real Hub client")),
    ):
        inert.start()
        _INERT.append(inert)


def tearDownModule():
    while _INERT:
        _INERT.pop().stop()


class FakeHub:
    """In-memory Hub: one README per repo, revisions as strings."""

    def __init__(self, readme, corrupt_upload=False, stale_head=False):
        self.revisions = {"rev0": readme}
        self.head_rev = "rev0"
        self.uploads = []
        self.corrupt_upload = corrupt_upload
        self.stale_head = stale_head

    def head(self, repo_id):
        return self.head_rev

    def read_readme(self, repo_id, revision):
        return self.revisions.get(revision)

    def upload_readme(self, repo_id, data, parent, message, description):
        if self.stale_head:
            return self.head_rev
        self.uploads.append({"repo_id": repo_id, "parent": parent, "message": message})
        new = f"rev{len(self.revisions)}"
        self.revisions[new] = data + b"x" if self.corrupt_upload else data
        self.head_rev = new
        return new


class PublishOneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        card = pub.card_path(self.root, "uds-bundles-v1")
        card.parent.mkdir(parents=True)
        card.write_bytes(b"---\nlicense: apache-2.0\n---\nnew card\n")
        self.local = card.read_bytes()

    def tearDown(self):
        self.tmp.cleanup()

    def run_one(self, hub, dry_run=False):
        return pub.publish_one(hub, self.root, "uds-bundles-v1", "abc123", "desc", dry_run,
                               source_guard=lambda dataset: None)

    def test_identical_card_is_not_uploaded(self):
        hub = FakeHub(self.local)
        result = self.run_one(hub)
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(hub.uploads, [])

    def test_changed_card_is_uploaded_and_read_back(self):
        hub = FakeHub(b"old card\n")
        result = self.run_one(hub)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["action"], "uploaded")
        self.assertEqual(result["hub_sha256"], pub.sha256_hex(self.local))
        self.assertEqual(len(hub.uploads), 1)
        upload = hub.uploads[0]
        self.assertEqual(upload["repo_id"], "SZLHOLDINGS/uds-bundles-v1")
        self.assertEqual(upload["parent"], "rev0")
        self.assertIn("szl-holdings/uds-bundles@abc123", upload["message"])

    def test_readback_mismatch_fails(self):
        result = self.run_one(FakeHub(b"old card\n", corrupt_upload=True))
        self.assertFalse(result["ok"])
        self.assertIn("read-back", result["error"])

    def test_no_new_revision_fails(self):
        result = self.run_one(FakeHub(b"old card\n", stale_head=True))
        self.assertFalse(result["ok"])
        self.assertIn("no new Hub revision", result["error"])

    def test_missing_hub_readme_is_uploaded(self):
        hub = FakeHub(None)
        result = self.run_one(hub)
        self.assertTrue(result["ok"], result)
        self.assertIsNone(result["hub_sha256_before"])

    def test_dry_run_never_uploads(self):
        hub = FakeHub(b"old card\n")
        result = self.run_one(hub, dry_run=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "would-upload")
        self.assertEqual(hub.uploads, [])

    def test_unchanged_card_rejects_a_concurrent_head_change(self):
        hub = FakeHub(self.local)
        with patch.object(hub, "head", side_effect=["rev0", "rev1"]):
            result = self.run_one(hub)
        self.assertFalse(result["ok"])
        self.assertIn("head changed", result["error"])
        self.assertEqual(hub.uploads, [])

    def test_uploaded_card_rejects_a_concurrent_head_change(self):
        hub = FakeHub(b"old card\n")
        with patch.object(hub, "head", side_effect=["rev0", "rev2"]):
            result = self.run_one(hub)
        self.assertFalse(result["ok"])
        self.assertIn("head changed", result["error"])

    def test_main_advance_before_upload_prevents_the_write(self):
        hub = FakeHub(b"old card\n")
        with self.assertRaisesRegex(RuntimeError, "stale"):
            pub.publish_one(hub, self.root, "uds-bundles-v1", "abc123", "desc",
                            source_guard=unittest.mock.Mock(side_effect=[None, RuntimeError("stale")]))
        self.assertEqual(hub.uploads, [])

    def test_main_advance_after_readback_is_not_reported_as_success(self):
        hub = FakeHub(b"old card\n")
        with self.assertRaisesRegex(RuntimeError, "stale"):
            pub.publish_one(hub, self.root, "uds-bundles-v1", "abc123", "desc",
                            source_guard=unittest.mock.Mock(side_effect=[None, None, RuntimeError("stale")]))
        self.assertEqual(len(hub.uploads), 1)


class SourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sha = "a" * 40
        card = pub.card_path(self.root, "uds-bundles-v1")
        card.parent.mkdir(parents=True)
        card.write_bytes(b"card\n")
        self.guard = pub.SourceGuard(self.root, self.sha)

    def check(self, replies):
        with patch.object(self.guard, "git", side_effect=replies):
            self.guard("uds-bundles-v1")

    def test_current_tracked_card_is_accepted(self):
        self.check([self.sha.encode(), b"card\n", f"{self.sha}\trefs/heads/main\n".encode()])

    def test_old_source_revision_is_rejected(self):
        # Canonical main advanced and carries a different card blob at the same path.
        card = "huggingface/datasets/uds-bundles-v1/README.md"
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.check([self.sha.encode(), b"card\n", f"{'b' * 40}\trefs/heads/main\n".encode(), b"",
                        f"100644 blob {'2' * 40}\t{card}\n".encode(),
                        f"100644 blob {'1' * 40}\t{card}\n".encode()])

    def test_worktree_edits_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Git blob"):
            self.check([self.sha.encode(), b"different card\n"])

    def test_wrong_checkout_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "checkout"):
            self.check([b"b" * 40])

    def test_missing_remote_main_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.check([self.sha.encode(), b"card\n", b""])

    def test_short_or_invalid_revision_is_rejected(self):
        for sha in ("abc123", "a" * 40 + "\n", "" ):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                pub.SourceGuard(self.root, sha)


class MainTests(unittest.TestCase):
    def test_refuses_without_token(self):
        saved = pub.os.environ.pop("HF_TOKEN", None)
        try:
            self.assertEqual(pub.main(["--git-sha", "abc123"]), 2)
        finally:
            if saved is not None:
                pub.os.environ["HF_TOKEN"] = saved

    def test_source_cards_exist_for_every_dataset(self):
        for dataset in pub.DATASETS:
            with self.subTest(dataset=dataset):
                self.assertTrue(pub.card_path(ROOT, dataset).is_file())


# --- Source freshness, destination-tip qualification and write scheduling -------------------
# Everything below runs the real publish logic against inert fakes: FakeCanonicalGit stands in
# for the git CLI and canonical main, MovingHub for the Hub. Neither opens a connection.

SHA_A, SHA_B, SHA_C = "a" * 40, "b" * 40, "c" * 40
CARD = {d: f"huggingface/datasets/{d}/README.md" for d in pub.DATASETS}
PUBLISHER_FILES = (
    "scripts/hf_publish_cards.py",
    "tests/test_hf_publish_cards.py",
    ".github/workflows/hf-dataset-cards-publish.yml",
)
PLACEHOLDER_ENV = {"HF_TOKEN": "offline-placeholder-not-a-token"}
REPO = f"{pub.HUB_ORG}/uds-bundles-v1"


def snapshot(cards, publisher=b"publisher v1\n", extra=None):
    """One commit's tree as {path: bytes}: the three cards, the publisher files and extras."""
    tree = {CARD[d]: cards[d] for d in pub.DATASETS}
    tree.update({path: publisher for path in PUBLISHER_FILES})
    tree.update(extra or {})
    return tree


class FakeCanonicalGit:
    """Inert stand-in for the git CLI behind SourceGuard.

    `commits` maps a SHA to its tree; `head` is the checkout; `main` is what canonical
    refs/heads/main points at (tests move it). As in a depth-1 CI checkout, the tree of any
    commit other than the checkout can be read only after it has been fetched.
    """

    def __init__(self, commits, head):
        self.commits, self.head, self.main = commits, head, head
        self.local = {head}
        self.calls = []

    @staticmethod
    def blob_id(data):
        return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()

    def __call__(self, *args):
        self.calls.append(args)
        cmd = args[0]
        if args == ("rev-parse", "HEAD"):
            return f"{self.head}\n".encode()
        if cmd == "show":
            sha, path = args[1].split(":", 1)
            return self.commits[sha][path]
        if cmd == "ls-remote":
            return f"{self.main}\trefs/heads/main\n".encode() if self.main else b""
        if cmd == "fetch":
            self.local.add(args[-1])
            return b""
        if cmd == "ls-tree":
            sha, paths = args[1], args[args.index("--") + 1:]
            if sha not in self.local:
                raise AssertionError(f"tree of {sha} read before it was fetched")
            tree = self.commits[sha]
            return "".join(f"100644 blob {self.blob_id(tree[p])}\t{p}\n"
                           for p in sorted(paths) if p in tree).encode()
        raise AssertionError(f"unexpected git call: {args}")


class ParentConflict(Exception):
    """Stands in for the Hub's HTTP 412 when parent_commit is no longer the head."""


class MovingHub:
    """Inert multi-dataset Hub with parent-commit compare-and-swap and concurrent writers."""

    def __init__(self, readmes):
        self.revisions, self.heads, self.uploads, self.head_reads = {}, {}, [], []
        self.churn = False           # another writer commits around every one of our reads
        self.null_heads = set()      # repos whose head cannot be observed
        self.fail_upload = {}        # repo_id -> exception raised instead of committing
        self.fail_readback = set()   # repo_ids whose read of our own new revision fails
        self.after_upload = None     # callback(repo_id, data) after each of our commits
        self.after_read = None       # callback(repo_id) after each pre-upload README read
        self._n = 0
        for repo_id, data in readmes.items():
            self.commit(repo_id, data)

    def commit(self, repo_id, data=b"edited on the Hub by another writer\n"):
        self._n += 1
        rev = f"{self._n:040x}"
        self.revisions[(repo_id, rev)] = data
        self.heads[repo_id] = rev
        return rev

    def readme(self, repo_id):
        return self.revisions[(repo_id, self.heads[repo_id])]

    def _churn(self, repo_id):
        if self.churn:  # e.g. a data-file commit: the head moves, the README stays the same
            self.commit(repo_id, self.readme(repo_id))

    def head(self, repo_id):
        self.head_reads.append(repo_id)
        self._churn(repo_id)
        return None if repo_id in self.null_heads else self.heads[repo_id]

    def read_readme(self, repo_id, revision):
        ours = any(u["revision"] == revision for u in self.uploads)
        if ours and repo_id in self.fail_readback:
            raise ConnectionError("transport reset while reading back")
        data = self.revisions.get((repo_id, revision))
        self._churn(repo_id)
        if self.after_read and not ours:
            self.after_read(repo_id)
        return data

    def upload_readme(self, repo_id, data, parent, message, description):
        if repo_id in self.fail_upload:
            raise self.fail_upload[repo_id]
        if parent is not None and parent != self.heads[repo_id]:  # None: no CAS, as on the Hub
            raise ParentConflict(f"412 Precondition Failed: {parent[:8]} is not the head")
        rev = self.commit(repo_id, data)
        self.uploads.append({"repo_id": repo_id, "parent": parent, "revision": rev, "data": data})
        if self.after_upload:
            self.after_upload(repo_id, data)
        return rev


class CanonicalSourceCase(unittest.TestCase):
    """Runs the real main() and SourceGuard against FakeCanonicalGit and MovingHub."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.v1 = {d: f"card {d} v1\n".encode() for d in pub.DATASETS}
        self.commits = {SHA_A: snapshot(self.v1)}
        self.git = FakeCanonicalGit(self.commits, SHA_A)

    def move_main(self, sha, tree):
        self.commits[sha] = tree
        self.git.main = sha

    def stale_hub(self):
        return MovingHub({f"{pub.HUB_ORG}/{d}": b"old card\n" for d in pub.DATASETS})

    def checkout(self, sha):
        root = Path(self.tmp.name) / sha[:8]
        for path, data in self.commits[sha].items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_bytes(data)
        return root

    def run_main(self, hub, sha=SHA_A, extra=()):
        root = self.checkout(sha)
        self.git.head = sha
        self.git.local = {sha}
        out = io.StringIO()
        with patch.object(pub, "ROOT", root), \
                patch.object(pub, "HubClient", lambda token: hub), \
                patch.object(pub.SourceGuard, "git", lambda _guard, *args: self.git(*args)), \
                patch.dict(pub.os.environ, PLACEHOLDER_ENV), \
                contextlib.redirect_stdout(out):
            code = pub.main(["--git-sha", sha, *extra])
        return code, {r["dataset"].split("/", 1)[1]: r for r in json.loads(out.getvalue())}


class SourceFreshnessTests(CanonicalSourceCase):
    """Canonical main is re-read after serialization and around every write in the batch."""

    def test_unrelated_main_commit_before_the_run_does_not_block_it(self):
        self.move_main(SHA_B, snapshot(self.v1, extra={"docs/unrelated.md": b"bump\n"}))
        hub = self.stale_hub()
        code, results = self.run_main(hub)
        self.assertEqual(code, 0, results)
        self.assertTrue(all(r["ok"] and r["action"] == "uploaded" for r in results.values()))

    def test_unrelated_main_commit_mid_batch_does_not_stop_publication(self):
        hub = self.stale_hub()
        unrelated = snapshot(self.v1, extra={"docs/unrelated.md": b"bump\n"})
        hub.after_upload = lambda repo_id, data: self.move_main(SHA_B, unrelated)
        code, results = self.run_main(hub)
        self.assertEqual(code, 0, results)
        for dataset in pub.DATASETS:
            with self.subTest(dataset=dataset):
                self.assertTrue(results[dataset]["ok"])
                self.assertEqual(hub.readme(f"{pub.HUB_ORG}/{dataset}"), self.v1[dataset])

    def test_card_change_on_main_before_the_run_publishes_nothing(self):
        first = pub.DATASETS[0]
        self.move_main(SHA_B, snapshot({**self.v1, first: b"card v2\n"}))
        hub = self.stale_hub()
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(hub.uploads, [])
        self.assertEqual(results[first]["action"], "stale-source")
        self.assertIn("stale", results[first]["error"])
        for dataset in pub.DATASETS[1:]:
            self.assertEqual(results[dataset]["action"], "not-attempted")

    def test_card_change_on_main_mid_batch_supersedes_the_remaining_datasets(self):
        first, second, third = pub.DATASETS
        hub = self.stale_hub()
        changed = snapshot({**self.v1, second: b"card v2\n"})
        hub.after_upload = lambda repo_id, data: self.move_main(SHA_B, changed)
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertTrue(results[first]["ok"], results[first])  # its card is unchanged on main
        self.assertEqual(results[second]["action"], "stale-source")
        self.assertIn("stale", results[second]["error"])
        self.assertEqual(results[third]["action"], "not-attempted")
        self.assertEqual([u["repo_id"] for u in hub.uploads], [f"{pub.HUB_ORG}/{first}"])
        self.assertEqual(hub.readme(f"{pub.HUB_ORG}/{second}"), b"old card\n")
        self.assertNotIn(f"{pub.HUB_ORG}/{third}", hub.head_reads)

    def test_publisher_change_on_main_after_upload_is_not_reported_as_success(self):
        first = pub.DATASETS[0]
        hub = self.stale_hub()
        changed = snapshot(self.v1, publisher=b"publisher v2\n")
        hub.after_upload = lambda repo_id, data: self.move_main(SHA_B, changed)
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(results[first]["action"], "uploaded")  # the write stays on record
        self.assertTrue(results[first]["hub_revision"])
        self.assertFalse(results[first]["ok"])
        self.assertIn("stale", results[first]["error"])
        for dataset in pub.DATASETS[1:]:
            self.assertEqual(results[dataset]["action"], "not-attempted")
        self.assertEqual(len(hub.uploads), 1)

    def test_every_upload_carries_the_current_canonical_card(self):
        hub = self.stale_hub()
        seen = []
        hub.after_upload = lambda repo_id, data: seen.append(
            data == self.commits[self.git.main][CARD[repo_id.split("/", 1)[1]]])
        self.run_main(hub)
        self.assertEqual(seen, [True, True, True])

    def test_main_that_cannot_be_read_stops_the_batch(self):
        self.git.main = ""
        hub = self.stale_hub()
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(hub.uploads, [])
        self.assertEqual([r["action"] for r in results.values()],
                         ["stale-source", "not-attempted", "not-attempted"])

    def test_canonical_main_is_fetched_once_per_observed_commit(self):
        self.move_main(SHA_B, snapshot(self.v1, extra={"docs/unrelated.md": b"bump\n"}))
        self.run_main(self.stale_hub())
        fetches = [c for c in self.git.calls if c[0] == "fetch"]
        self.assertEqual(len(fetches), 1)
        self.assertEqual(fetches[0][-1], SHA_B)

    def test_card_deleted_on_main_is_stale(self):
        tree = snapshot(self.v1)
        del tree[CARD["uds-bundles-v1"]]
        self.move_main(SHA_B, tree)
        guard = pub.SourceGuard(self.checkout(SHA_A), SHA_A)
        with patch.object(guard, "git", self.git), self.assertRaisesRegex(RuntimeError, "stale"):
            guard("uds-bundles-v1")


class DestinationTipTests(unittest.TestCase):
    """No-op and upload outcomes are qualified by a Hub head read before and after."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        card = pub.card_path(self.root, "uds-bundles-v1")
        card.parent.mkdir(parents=True)
        card.write_bytes(b"new card\n")
        self.local = card.read_bytes()

    def run_one(self, hub, guard=None, dry_run=False):
        return pub.publish_one(hub, self.root, "uds-bundles-v1", SHA_A, "desc", dry_run,
                               source_guard=guard or (lambda dataset: None))

    def guard_moving_hub_on_check(self, hub, check):
        calls = []

        def guard(dataset):
            calls.append(dataset)
            if len(calls) == check:  # the Hub moves while the source is being re-checked
                hub.commit(REPO, hub.readme(REPO))
        return guard

    def test_unchanged_outcome_needs_a_tip_read_after_the_last_source_check(self):
        hub = MovingHub({REPO: self.local})
        result = self.run_one(hub, self.guard_moving_hub_on_check(hub, 2))
        self.assertFalse(result["ok"], result)
        self.assertIn("head changed", result["error"])

    def test_dry_run_outcome_needs_a_tip_read_after_the_last_source_check(self):
        hub = MovingHub({REPO: b"old card\n"})
        result = self.run_one(hub, self.guard_moving_hub_on_check(hub, 2), dry_run=True)
        self.assertFalse(result["ok"], result)
        self.assertIn("head changed", result["error"])
        self.assertEqual(hub.uploads, [])

    def test_uploaded_outcome_needs_a_tip_read_after_the_last_source_check(self):
        hub = MovingHub({REPO: b"old card\n"})
        result = self.run_one(hub, self.guard_moving_hub_on_check(hub, 3))
        self.assertEqual(result["action"], "uploaded")
        self.assertFalse(result["ok"], result)
        self.assertIn("head changed", result["error"])

    def test_outcomes_record_the_tip_observed_before_and_after(self):
        hub = MovingHub({REPO: self.local})
        unchanged = self.run_one(hub)
        self.assertEqual(unchanged["hub_head_before"], unchanged["hub_head_after"])
        self.assertEqual(unchanged["hub_revision"], unchanged["hub_head_after"])
        hub = MovingHub({REPO: b"old card\n"})
        uploaded = self.run_one(hub)
        self.assertTrue(uploaded["ok"], uploaded)
        self.assertEqual(uploaded["hub_head_after"], uploaded["hub_revision"])
        self.assertEqual(hub.uploads[0]["parent"], uploaded["hub_head_before"])

    def test_unobserved_hub_head_cannot_disable_compare_and_swap(self):
        hub = MovingHub({REPO: b"old card\n"})
        hub.null_heads.add(REPO)
        with self.assertRaisesRegex(RuntimeError, "head"):
            self.run_one(hub)
        self.assertEqual(hub.uploads, [])

    def test_parent_conflict_fails_without_overwriting_the_other_writer(self):
        hub = MovingHub({REPO: b"old card\n"})
        hub.after_read = lambda repo_id: hub.commit(repo_id, b"other writer's card\n")
        with self.assertRaises(ParentConflict):
            self.run_one(hub)
        self.assertEqual(hub.uploads, [])
        self.assertEqual(hub.readme(REPO), b"other writer's card\n")

    def test_persistent_instability_fails_closed_without_retrying(self):
        hub = MovingHub({REPO: self.local})
        hub.churn = True
        result = self.run_one(hub)
        self.assertFalse(result["ok"])
        self.assertEqual(len(hub.head_reads), 2)
        hub = MovingHub({REPO: b"old card\n"})
        hub.churn = True
        with self.assertRaises(ParentConflict):
            self.run_one(hub)
        self.assertEqual(hub.uploads, [])
        self.assertEqual(len(hub.head_reads), 1)


class PerDatasetOutcomeTests(CanonicalSourceCase):
    """Every requested dataset gets an outcome that keeps what was observed before a failure."""

    def test_partial_failure_keeps_every_dataset_outcome(self):
        first, second, third = pub.DATASETS
        hub = self.stale_hub()
        head_before = hub.heads[f"{pub.HUB_ORG}/{second}"]
        hub.fail_upload[f"{pub.HUB_ORG}/{second}"] = ConnectionError("HTTP 503 from the Hub")
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(list(results), list(pub.DATASETS))
        self.assertTrue(results[first]["ok"])
        self.assertTrue(results[third]["ok"])
        self.assertFalse(results[second]["ok"])
        self.assertIn("ConnectionError", results[second]["error"])
        self.assertEqual(results[second]["hub_head_before"], head_before)
        self.assertEqual(results[second]["local_sha256"], pub.sha256_hex(self.v1[second]))
        self.assertNotIn("action", results[second])

    def test_readback_failure_after_upload_keeps_the_uploaded_outcome(self):
        first = pub.DATASETS[0]
        hub = self.stale_hub()
        hub.fail_readback.add(f"{pub.HUB_ORG}/{first}")
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(results[first]["action"], "uploaded")
        self.assertEqual(results[first]["hub_revision"], hub.uploads[0]["revision"])
        self.assertFalse(results[first]["ok"])
        self.assertTrue(all(results[d]["ok"] for d in pub.DATASETS[1:]))

    def test_parent_conflict_is_one_dataset_outcome(self):
        first = pub.DATASETS[0]
        repo = f"{pub.HUB_ORG}/{first}"
        hub = self.stale_hub()
        head_before = hub.heads[repo]

        def other_writer(repo_id):
            if repo_id == repo and hub.heads[repo_id] == head_before:
                hub.commit(repo_id, b"other writer's card\n")
        hub.after_read = other_writer
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertIn("ParentConflict", results[first]["error"])
        self.assertEqual(results[first]["hub_head_before"], head_before)
        self.assertNotIn("action", results[first])
        self.assertEqual(hub.readme(repo), b"other writer's card\n")
        self.assertTrue(all(results[d]["ok"] for d in pub.DATASETS[1:]))

    def test_persistent_hub_instability_fails_every_dataset_closed(self):
        hub = self.stale_hub()
        hub.churn = True
        code, results = self.run_main(hub)
        self.assertEqual(code, 1)
        self.assertEqual(hub.uploads, [])
        self.assertFalse(any(r["ok"] for r in results.values()))

    def test_a_write_cannot_be_narrowed_to_one_dataset(self):
        hub = self.stale_hub()
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            self.run_main(hub, extra=("--dataset", pub.DATASETS[0]))
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(hub.head_reads, [])

    def test_a_dry_run_may_be_narrowed_to_one_dataset(self):
        hub = self.stale_hub()
        code, results = self.run_main(hub, extra=("--dry-run", "--dataset", pub.DATASETS[1]))
        self.assertEqual(code, 0, results)
        self.assertEqual(list(results), [pub.DATASETS[1]])
        self.assertEqual(results[pub.DATASETS[1]]["action"], "would-upload")
        self.assertEqual(hub.uploads, [])


def job_block(text, job):
    match = re.search(rf"(?ms)^  {job}:\n(.*?)(?=^  \S|\Z)", text)
    if not match:
        raise AssertionError(f"job {job!r} not found in {WORKFLOW.name}")
    return match.group(1)


WRITE_GROUP = "hf-dataset-cards-publish"
ISOLATING_GROUP = ("${{ (github.event_name == 'pull_request' || inputs.dry_run) && "
                   "format('hf-dataset-cards-validate-{0}', github.run_id) || "
                   "'hf-dataset-cards-publish' }}")


def publish_group(event, dry_run, run_id):
    """The publish job's concurrency group for one run, as the workflow declares it."""
    block = job_block(WORKFLOW.read_text(encoding="utf-8"), "publish")
    group = re.search(r"(?m)^    concurrency:\n      group: (.+)$", block).group(1).strip()
    if "${{" not in group:
        return group  # a constant: every run of the job shares one queue
    if group != ISOLATING_GROUP:
        raise AssertionError(f"unmodelled concurrency expression: {group}")
    return f"hf-dataset-cards-validate-{run_id}" if event == "pull_request" or dry_run else WRITE_GROUP


def workflow_args(dry_run, dataset):
    """The publisher arguments the publish step builds (pinned by test_only_dry_runs_...)."""
    args = []
    if dry_run:
        args.append("--dry-run")
        if dataset != "all":
            args += ["--dataset", dataset]
    return args


class ConcurrencyModel:
    """GitHub's documented job-concurrency rule with cancel-in-progress: false.

    Per group, one job runs and at most one waits; queuing another cancels the waiting one.
    This models the documented rule; it is not GitHub.
    """

    def __init__(self):
        self.running, self.pending, self.started, self.cancelled = {}, {}, [], []

    def queue(self, group, job):
        if group not in self.running:
            self.running[group] = job
            self.started.append(job)
            return
        if group in self.pending:
            self.cancelled.append(self.pending[group])
        self.pending[group] = job

    def finish(self, job):
        groups = [g for g, j in self.running.items() if j == job]
        if not groups:
            raise AssertionError(f"{job} is not running")
        group = groups[0]
        del self.running[group]
        if group in self.pending:
            self.queue(group, self.pending.pop(group))


class WriteSchedulingTests(CanonicalSourceCase):
    """PR and dry-run validation never enter the write queue; writes cover what they displace."""

    def test_workflow_concurrency_contract(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"(?m)^concurrency:")
        self.assertNotIn("concurrency:", job_block(text, "test"))
        publish = job_block(text, "publish")
        self.assertIn("if: github.event_name != 'pull_request' && github.ref == 'refs/heads/main'",
                      publish)
        self.assertRegex(publish, r"(?m)^      cancel-in-progress: false$")
        self.assertEqual(publish_group("push", False, 1), WRITE_GROUP)
        self.assertEqual(publish_group("workflow_dispatch", False, 2), WRITE_GROUP)
        self.assertNotEqual(publish_group("workflow_dispatch", True, 3), WRITE_GROUP)
        self.assertNotEqual(publish_group("pull_request", False, 4), WRITE_GROUP)
        self.assertNotEqual(publish_group("workflow_dispatch", True, 3),
                            publish_group("workflow_dispatch", True, 5))

    def test_workflow_grants_no_write_permission(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"(?m)^\s+(\S+): (read|write)$", text), [("contents", "read")])

    def test_only_dry_runs_pass_a_dataset_subset(self):
        step = job_block(WORKFLOW.read_text(encoding="utf-8"), "publish")
        self.assertEqual(step.count("--dataset"), 1)
        self.assertRegex(step, r'if \[ "\$INPUT_DRY_RUN" = "true" \]; then\n\s+args\+=\(--dry-run\)\n'
                               r'(?:\s+#.*\n)*'
                               r'\s+if \[ "\$INPUT_DATASET" != "all" \]; then args\+=\(--dataset '
                               r'"\$INPUT_DATASET"\); fi\n\s+fi\n')

    def test_every_freshness_input_triggers_its_own_publish_run(self):
        on = WORKFLOW.read_text(encoding="utf-8").split("\njobs:")[0]
        for event in ("push", "pull_request"):
            block = re.search(rf"(?ms)^  {event}:\n.*?paths:\n((?:      - [^\n]+\n)+)", on).group(1)
            self.assertEqual(re.findall(r'- "(.+)"', block),
                             ["huggingface/datasets/*/README.md", *PUBLISHER_FILES], event)
        self.assertEqual(tuple(pub.PUBLISHER_PATHS), PUBLISHER_FILES)

    def test_validation_neither_waits_for_nor_displaces_a_write(self):
        model = ConcurrencyModel()
        model.queue(publish_group("push", False, 1), "push@A")
        model.queue(publish_group("push", False, 2), "push@B")
        model.queue(publish_group("workflow_dispatch", True, 3), "dry-run")
        model.queue(publish_group("pull_request", False, 4), "pr")
        self.assertEqual(model.cancelled, [])
        self.assertEqual(model.pending, {WRITE_GROUP: "push@B"})
        self.assertIn("dry-run", model.started)
        model.queue(publish_group("push", False, 5), "push@C")
        self.assertEqual(model.cancelled, ["push@B"])  # a write displaces only a write
        self.assertIn("dry-run", model.running.values())

    def test_queue_overflow_newest_write_covers_every_displaced_request(self):
        first, second, third = pub.DATASETS
        hub = self.stale_hub()
        model, runs, outcomes, current = ConcurrencyModel(), {}, {}, []
        hub.after_upload = lambda repo_id, data: current.append(
            data == self.commits[self.git.main][CARD[repo_id.split("/", 1)[1]]])

        def request(job, sha, event, run_id, dry_run=False, dataset="all"):
            runs[job] = (sha, workflow_args(dry_run, dataset))
            model.queue(publish_group(event, dry_run, run_id), job)

        def execute(job):
            sha, extra = runs[job]
            outcomes[job] = self.run_main(hub, sha, extra)
            model.finish(job)

        request("push@A", SHA_A, "push", 1)  # running
        self.move_main(SHA_B, snapshot({**self.v1, second: b"second v2\n"}))
        request("push@B", SHA_B, "push", 2)  # waits
        request("dry-run@B", SHA_B, "workflow_dispatch", 3, dry_run=True, dataset=third)
        execute("dry-run@B")  # ran at once in its own group
        request("dispatch@B", SHA_B, "workflow_dispatch", 4, dataset=second)  # displaces push@B
        self.move_main(SHA_C, snapshot({**self.v1, second: b"second v2\n", third: b"third v2\n"}))
        request("push@C", SHA_C, "push", 5)  # displaces dispatch@B
        self.assertEqual(model.cancelled, ["push@B", "dispatch@B"])

        execute("push@A")  # main is now C: first is current, second is superseded
        code, results = outcomes["push@A"]
        self.assertEqual(code, 1)
        self.assertTrue(results[first]["ok"])
        self.assertEqual(results[second]["action"], "stale-source")
        self.assertEqual(model.running[WRITE_GROUP], "push@C")
        execute("push@C")
        code, results = outcomes["push@C"]
        self.assertEqual(code, 0, results)
        self.assertEqual(outcomes["dry-run@B"][0], 0)
        self.assertEqual(current, [True] * len(hub.uploads))  # no upload ever carried stale bytes
        for dataset in pub.DATASETS:
            with self.subTest(dataset=dataset):
                self.assertEqual(hub.readme(f"{pub.HUB_ORG}/{dataset}"), self.commits[SHA_C][CARD[dataset]])

    def test_a_write_dispatch_that_displaces_a_push_still_covers_it(self):
        first, _, third = pub.DATASETS
        hub = self.stale_hub()
        model, runs = ConcurrencyModel(), {}

        def request(job, sha, event, run_id, dataset="all"):
            runs[job] = (sha, workflow_args(False, dataset))
            model.queue(publish_group(event, False, run_id), job)

        request("push@A", SHA_A, "push", 1)
        self.move_main(SHA_B, snapshot({**self.v1, first: b"first v2\n"}))
        request("push@B", SHA_B, "push", 2)
        request("dispatch@B", SHA_B, "workflow_dispatch", 3, dataset=third)
        self.assertEqual(model.cancelled, ["push@B"])
        code, results = self.run_main(hub, *runs["push@A"])
        self.assertEqual(results[first]["action"], "stale-source")
        model.finish("push@A")
        self.assertEqual(model.running[WRITE_GROUP], "dispatch@B")
        code, results = self.run_main(hub, *runs["dispatch@B"])
        self.assertEqual(code, 0, results)
        self.assertEqual(hub.readme(f"{pub.HUB_ORG}/{first}"), b"first v2\n")  # push@B's change


class HubClientContractTests(unittest.TestCase):
    """The real HubClient against a recording stand-in for HfApi; huggingface_hub is not loaded."""

    class RecordingApi:
        def __init__(self, path):
            self.calls, self.path = [], path

        def upload_file(self, **kwargs):
            self.calls.append(("upload_file", kwargs))
            return type("CommitInfo", (), {"oid": "f" * 40})()

        def hf_hub_download(self, *args, **kwargs):
            self.calls.append(("hf_hub_download", args, kwargs))
            return str(self.path)

    def client(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "README.md"
        path.write_bytes(b"card\n")
        client = object.__new__(RealHubClient)  # skip __init__: it would import huggingface_hub
        client._api, client._token = self.RecordingApi(path), PLACEHOLDER_ENV["HF_TOKEN"]
        return client

    def test_upload_writes_readme_only_against_the_parent_commit(self):
        client = self.client()
        self.assertEqual(client.upload_readme(REPO, b"card\n", "e" * 40, "msg", "desc"), "f" * 40)
        name, kwargs = client._api.calls[-1]
        self.assertEqual((name, kwargs["path_in_repo"], kwargs["repo_type"], kwargs["parent_commit"]),
                         ("upload_file", "README.md", "dataset", "e" * 40))

    def test_readback_is_pinned_to_the_revision_and_bypasses_the_cache(self):
        client = self.client()
        errors = type(sys)("huggingface_hub.errors")
        errors.EntryNotFoundError = type("EntryNotFoundError", (Exception,), {})
        package = type(sys)("huggingface_hub")
        package.errors = errors
        with patch.dict(sys.modules, {"huggingface_hub": package, "huggingface_hub.errors": errors}):
            self.assertEqual(client.read_readme(REPO, "d" * 40), b"card\n")
        _, args, kwargs = client._api.calls[-1]
        self.assertEqual(args, (REPO, "README.md"))
        self.assertEqual((kwargs["revision"], kwargs["force_download"]), ("d" * 40, True))

    def test_publisher_makes_no_other_hub_call(self):
        import ast
        tree = ast.parse((ROOT / "scripts" / "hf_publish_cards.py").read_text(encoding="utf-8"))
        api_calls = {node.func.attr for node in ast.walk(tree)
                     if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                     and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "_api"}
        self.assertEqual(api_calls, {"dataset_info", "hf_hub_download", "upload_file"})
        paths = {kw.value.value for node in ast.walk(tree) if isinstance(node, ast.Call)
                 for kw in node.keywords if kw.arg == "path_in_repo"}
        self.assertEqual(paths, {"README.md"})


if __name__ == "__main__":
    unittest.main()
