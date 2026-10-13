"""Claim checks for the Hugging Face dataset cards sourced in huggingface/datasets/.

A card may only say what the repository's own evidence supports. These tests read the
card text and the evidence files in this repository; they never touch the network.
"""
import json
from pathlib import Path
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "huggingface" / "datasets"
AIRGAP_PROOF = ROOT / "releases" / "szl-warhacker-uds-v1.0.0" / "airgap-proof" / "PROOF.json"

# Wording that asserts an air-gapped deployment works. Allowed only once a captured
# cable-pulled proof exists (see STATUS.md and AIRGAP_PROOF_RUNBOOK.md).
AIRGAP_DEPLOY_CLAIMS = (
    re.compile(r"air-?gap(ped)?[- ]deployable", re.IGNORECASE),
    re.compile(r"deployable into an air-?gapped", re.IGNORECASE),
    re.compile(r"airgap deployment verification", re.IGNORECASE),
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


def airgap_proof_passed(path):
    """True only for a captured proof with overall=PASS recorded while OFFLINE."""
    try:
        proof = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(proof, dict):
        return False
    network = proof.get("network")
    return (
        proof.get("overall") == "PASS"
        and isinstance(network, dict)
        and network.get("result") == "OFFLINE"
    )


def airgap_overclaims(text, proof_path):
    """Return the air-gap deployment claims in text that the proof does not support."""
    if airgap_proof_passed(proof_path):
        return []
    return [p.pattern for p in AIRGAP_DEPLOY_CLAIMS if p.search(text)]


class AirgapProofGateTests(unittest.TestCase):
    def write_proof(self, directory, payload):
        path = Path(directory) / "PROOF.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_missing_proof_does_not_pass(self):
        self.assertFalse(airgap_proof_passed(ROOT / "does-not-exist" / "PROOF.json"))

    def test_only_offline_pass_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = [
                ({"overall": "PASS", "network": {"result": "OFFLINE"}}, True),
                ({"overall": "PASS", "network": {"result": "ONLINE"}}, False),
                ({"overall": "PENDING", "network": {"result": "OFFLINE"}}, False),
                ({"overall": "PASS"}, False),
                (["PASS", "OFFLINE"], False),
            ]
            for payload, expected in cases:
                with self.subTest(payload=payload):
                    self.assertIs(airgap_proof_passed(self.write_proof(tmp, payload)), expected)

    def test_guard_flags_the_original_wording(self):
        original = (
            "Airgap-deployable UDS Core / Zarf productionization artifacts. "
            "Each organ ships as a self-contained, cosign-signed Zarf bundle deployable "
            "into an airgapped k3d / UDS Core mesh."
        )
        self.assertEqual(len(airgap_overclaims(original, ROOT / "does-not-exist")), 2)
        with tempfile.TemporaryDirectory() as tmp:
            proof = self.write_proof(tmp, {"overall": "PASS", "network": {"result": "OFFLINE"}})
            self.assertEqual(airgap_overclaims(original, proof), [])


class UdsBundlesV1CardTests(unittest.TestCase):
    def setUp(self):
        self.card = read_card("uds-bundles-v1")

    def test_no_airgap_deploy_claim_without_captured_proof(self):
        self.assertEqual(
            airgap_overclaims(self.card, AIRGAP_PROOF),
            [],
            "card claims an air-gapped deployment but "
            f"{AIRGAP_PROOF.relative_to(ROOT).as_posix()} is missing or not an OFFLINE PASS",
        )

    def test_links_the_airgap_test_report(self):
        self.assertTrue(
            AIRGAP_REPORT_LINK.search(self.card), "card must link AIRGAP_TEST_REPORT.md"
        )

    def test_states_the_payload_is_image_free(self):
        self.assertTrue(
            "image-free proof packages" in self.card,
            "card must say the payload packages are image-free proof builds",
        )

    def test_no_unbacked_runtime_receipt_claim(self):
        for pattern in UNBACKED_RUNTIME_CLAIMS:
            with self.subTest(pattern=pattern.pattern):
                self.assertIsNone(pattern.search(self.card), pattern.pattern)


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
