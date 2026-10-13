"""Offline tests for scripts/hf_publish_cards.py (no network, no credentials)."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import hf_publish_cards as pub  # noqa: E402


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
        with self.assertRaisesRegex(RuntimeError, "stale"):
            self.check([self.sha.encode(), b"card\n", f"{'b' * 40}\trefs/heads/main\n".encode()])

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


if __name__ == "__main__":
    unittest.main()
