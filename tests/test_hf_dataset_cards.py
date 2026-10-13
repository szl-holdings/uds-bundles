"""Claim checks for the Hugging Face dataset cards sourced in huggingface/datasets/.

A card may only say what the repository's own evidence supports. These tests read the
card text and the evidence files in this repository; they never touch the network.
"""
import base64
import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "huggingface" / "datasets"
# GitHub copy of the uds-bundles-v1 payload's artifacts/ directory.
PROOF_ARTIFACTS = ROOT / "uds-bundles" / "artifacts"
PROOF_SHA256SUMS = PROOF_ARTIFACTS / "SHA256SUMS_PROOF.txt"
SOURCE_README = ROOT / "huggingface" / "README.md"
# This dataset contains image-free 0.3.1 proof packages. Evidence about a different
# image-bearing mesh release cannot authorize deployment claims for these bytes.
AIRGAP_DEPLOY_CLAIMS = (
    re.compile(r"air-?gap(ped)?[- ]deployable", re.IGNORECASE),
    re.compile(r"deployable into an air-?gapped", re.IGNORECASE),
    re.compile(r"air-?gap deployment verification", re.IGNORECASE),
)
# Claims about runtime receipts that no artifact in the dataset backs.
UNBACKED_RUNTIME_CLAIMS = (
    re.compile(r"every deployment emits", re.IGNORECASE),
)
AIRGAP_REPORT_LINK = re.compile(r"\]\([^)\s]*AIRGAP_TEST_REPORT\.md\)")
# The uds-spans-receipts span/receipt rows are generated (synthetic: true on every Hub row).
# The card must not present them as mesh output or claim fields the rows do not have.
SYNTHETIC_ROW_OVERCLAIMS = (
    re.compile(r"emitted by the UDS mesh", re.IGNORECASE),
    re.compile(r"actor ORCID", re.IGNORECASE),
    re.compile(r"formula-gate pass/fail bitmap", re.IGNORECASE),
)

# One row of the uds-bundles-v1 package table: | `name` | `version` | `file` | `sha256` |
ARTIFACT_ROW = re.compile(
    r"^\|\s*`(?P<name>[a-z0-9-]+)`\s*\|\s*`(?P<version>\d+\.\d+\.\d+)`\s*\|"
    r"\s*`(?P<file>zarf-package-[^`]+\.tar\.zst)`\s*\|\s*`(?P<sha256>[0-9a-f]{64})`\s*\|\s*$",
    re.MULTILINE,
)
PACKAGE_FILE = re.compile(
    r"^zarf-package-(?P<name>[a-z0-9-]+?)-(?P<arch>amd64|arm64)-(?P<version>\d+\.\d+\.\d+)\.tar\.zst$"
)
# huggingface/README.md import table row and "behind" note.
IMPORT_ROW = re.compile(
    r"^\| \[`SZLHOLDINGS/(?P<id>[a-z0-9-]+)`\]\([^)]*\) \| `(?P<rev>[0-9a-f]{40})` \| "
    r"`(?P<sha256>[0-9a-f]{64})` \|$",
    re.MULTILINE,
)
BEHIND_NOTE = re.compile(r"^- `(?P<id>[a-z0-9-]+)`: the Hub copy is \*\*behind\*\*", re.MULTILINE)


def read_card(dataset):
    return (CARDS / dataset / "README.md").read_text(encoding="utf-8")


def front_matter(text):
    """Minimal parser for the card's YAML header: top-level scalars and string lists."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("- ") and key is not None:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(line[2:].strip())
        elif not line.startswith(" ") and ":" in line:
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            meta[key] = value if value else []
    return meta


def card_artifact_rows(text):
    return [m.groupdict() for m in ARTIFACT_ROW.finditer(text)]


def parse_package_file(filename):
    match = PACKAGE_FILE.match(filename)
    return (match["name"], match["version"]) if match else None


def read_sha256sums(path):
    """{file basename: sha256} from a sha256sum listing (absolute capture paths allowed)."""
    sums = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, _, name = line.partition("  ")
            sums[name.strip().rsplit("/", 1)[-1]] = digest.strip()
    return sums


def airgap_overclaims(text):
    """Reject deployment claims for the dataset's image-free proof packages."""
    return [p.pattern for p in AIRGAP_DEPLOY_CLAIMS if p.search(text)]


class AirgapProofGateTests(unittest.TestCase):
    def test_guard_flags_the_original_wording(self):
        original = (
            "Airgap-deployable UDS Core / Zarf productionization artifacts. "
            "Each organ ships as a self-contained, cosign-signed Zarf bundle deployable "
            "into an airgapped k3d / UDS Core mesh."
        )
        self.assertEqual(len(airgap_overclaims(original)), 2)

    def test_hyphenated_deployment_verification_is_rejected(self):
        for claim in ("airgap deployment verification", "air-gap deployment verification"):
            with self.subTest(claim=claim):
                self.assertTrue(airgap_overclaims(claim))


class UdsBundlesV1CardTests(unittest.TestCase):
    def setUp(self):
        self.card = read_card("uds-bundles-v1")

    def test_no_airgap_deploy_claim_for_image_free_dataset(self):
        self.assertEqual(
            airgap_overclaims(self.card),
            [],
            "image-free 0.3.1 packages cannot inherit proof from a different mesh release",
        )

    def test_signing_key_is_bound_to_the_published_bundle_key(self):
        pem = (ROOT / "bundles/v0.1.0/cosign_signing_key.pub").read_text()
        der = base64.b64decode("".join(line for line in pem.splitlines() if not line.startswith("---")))
        self.assertIn(hashlib.sha256(der).hexdigest(), self.card)
        self.assertNotIn("signed with the SZL org key", self.card)

    def test_deploy_preview_is_scoped_to_the_recorded_package(self):
        preview = (ROOT / "uds-bundles/artifacts/DEPLOY_DRYRUN.txt").read_text()
        package = "zarf-package-a11oy-runtime-proof-amd64-0.3.1.tar.zst"
        self.assertIn(package, preview)
        self.assertIn(package, self.card)
        self.assertIn("only the a11oy proof package", self.card)

    def test_links_the_airgap_test_report(self):
        self.assertTrue(
            AIRGAP_REPORT_LINK.search(self.card), "card must link AIRGAP_TEST_REPORT.md"
        )

    def test_states_the_payload_is_image_free(self):
        self.assertTrue(
            "image-free proof packages" in self.card,
            "card must say the payload packages are image-free proof builds",
        )

    def test_artifact_archive_does_not_claim_an_example_count(self):
        self.assertNotIn("size_categories", front_matter(self.card))

    def test_no_unbacked_runtime_receipt_claim(self):
        for pattern in UNBACKED_RUNTIME_CLAIMS:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(self.card), pattern.pattern)

    def test_package_table_matches_the_recorded_sha256sums(self):
        rows = card_artifact_rows(self.card)
        sums = read_sha256sums(PROOF_SHA256SUMS)
        packages = {name for name in sums if name.endswith(".tar.zst")}
        self.assertEqual(len(packages), 5)
        self.assertEqual(len(rows), 5)
        self.assertEqual({row["file"] for row in rows}, packages)
        for row in rows:
            with self.subTest(row["file"]):
                self.assertEqual(parse_package_file(row["file"]), (row["name"], row["version"]))
                self.assertEqual(row["sha256"], sums[row["file"]])

    def test_package_table_matches_the_committed_files(self):
        rows = card_artifact_rows(self.card)
        self.assertEqual(len(rows), 5)
        for row in rows:
            with self.subTest(row["file"]):
                data = (PROOF_ARTIFACTS / row["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])


class PackageTableParserTests(unittest.TestCase):
    def test_rejects_rows_that_do_not_bind_name_version_and_hash(self):
        digest = hashlib.sha256(b"x").hexdigest()
        good = f"| `a-proof` | `0.3.1` | `zarf-package-a-proof-amd64-0.3.1.tar.zst` | `{digest}` |"
        self.assertEqual(len(card_artifact_rows(good)), 1)
        for bad in (
            good.replace(digest, digest[:16]),
            good.replace("`0.3.1` |", "`latest` |"),
            good.replace(digest, digest.upper()),
            "| `a-proof` | `0.3.1` | `zarf-package-a-proof-amd64-0.3.1.tar.zst` |",
        ):
            with self.subTest(bad):
                self.assertEqual(card_artifact_rows(bad), [])
        self.assertEqual(
            parse_package_file("zarf-package-a11oy-runtime-proof-amd64-0.3.1.tar.zst"),
            ("a11oy-runtime-proof", "0.3.1"),
        )
        self.assertIsNone(parse_package_file("szl-mesh-v0.4.0.tar.zst"))


class SourceReadmeImportTableTests(unittest.TestCase):
    """huggingface/README.md must say which source cards still match their Hub import.

    A card marked behind must differ from its imported bytes; a card not marked behind must
    still equal them. After a publish, update the table row to the published revision and
    sha256 and drop the behind note in the same change.
    """

    def test_behind_notes_match_the_card_bytes(self):
        text = SOURCE_README.read_text(encoding="utf-8")
        imported = {m["id"]: m["sha256"] for m in IMPORT_ROW.finditer(text)}
        behind = {m["id"] for m in BEHIND_NOTE.finditer(text)}
        self.assertEqual(set(imported), {p.name for p in CARDS.iterdir() if p.is_dir()})
        self.assertLessEqual(behind, set(imported))
        for dataset, imported_sha in imported.items():
            actual = hashlib.sha256((CARDS / dataset / "README.md").read_bytes()).hexdigest()
            with self.subTest(dataset):
                if dataset in behind:
                    self.assertNotEqual(actual, imported_sha, "marked behind but unchanged")
                else:
                    self.assertEqual(actual, imported_sha, "edited but not marked behind")


class FrontMatterParserTests(unittest.TestCase):
    def test_reads_scalars_and_lists(self):
        meta = front_matter(
            "---\nlicense: apache-2.0\ntags:\n- a\n- b\npretty_name: X (Y)\n---\nbody\n"
        )
        self.assertEqual(meta["tags"], ["a", "b"])
        self.assertEqual(meta["pretty_name"], "X (Y)")
        self.assertEqual(meta["license"], "apache-2.0")


class UdsSpansReceiptsCardTests(unittest.TestCase):
    def setUp(self):
        self.card = read_card("uds-spans-receipts")
        self.meta = front_matter(self.card)

    def test_tagged_synthetic(self):
        self.assertIn("synthetic", self.meta.get("tags", []))

    def test_pretty_name_says_synthetic(self):
        self.assertIn("SYNTHETIC", self.meta.get("pretty_name", ""))

    def test_rows_not_presented_as_mesh_output(self):
        for pattern in SYNTHETIC_ROW_OVERCLAIMS:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(self.card), pattern.pattern)

    def test_states_rows_carry_synthetic_flag(self):
        self.assertTrue(
            "`synthetic: true`" in self.card,
            "card must say every span/receipt row carries synthetic: true",
        )


if __name__ == "__main__":
    unittest.main()
