"""Claim checks for the Hugging Face dataset cards sourced in huggingface/datasets/.

A card may only say what the repository's own evidence supports. These tests read the
card text and the evidence files in this repository; they never touch the network or
verify a signature. The public-key fingerprint is checked against its committed bytes.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import NamedTuple
import unittest


ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "huggingface" / "datasets"
AIRGAP_PROOF = ROOT / "releases" / "szl-warhacker-uds-v1.0.0" / "airgap-proof" / "PROOF.json"

# Evidence for the uds-bundles-v1 payload (the GitHub copy of the dataset's
# uds_productionization/ tree).
PROOF_ARTIFACTS = ROOT / "uds-bundles" / "artifacts"
PROOF_SHA256SUMS = PROOF_ARTIFACTS / "SHA256SUMS_PROOF.txt"
DEPLOY_DRYRUN = PROOF_ARTIFACTS / "DEPLOY_DRYRUN.txt"
COSIGN_KEYS = ROOT / "COSIGN_KEYS.md"
SIGNING_LOG = ROOT / "uds-bundles" / "COSIGN_SIGNING_LOG.md"

# Key fingerprints (SHA-256 of the DER SubjectPublicKeyInfo) as COSIGN_KEYS.md records them.
# The five 0.3.1 proof packages are signed with the uds-bundles key, never the org key.
UDS_BUNDLES_SPKI_SHA256 = "daa4aeca263251e97125fd227ff82e024a64ec970d1c74828463ffba097cb40b"
UDS_BUNDLES_PUBKEY = "bundles/v0.1.0/cosign_signing_key.pub"
ORG_RECEIPTS_SPKI_SHA256 = "a1f6d3233442cdad0801c702e0ff77aa45fd1ba45f532e3919c80d520b2826ab"

# Wording that asserts an air-gapped deployment works. Allowed only once a captured
# cable-pulled proof exists for the claimed artifacts (see STATUS.md and
# AIRGAP_PROOF_RUNBOOK.md).
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

# A reference to the SZL org receipts key by name, fingerprint or file.
ORG_KEY_REF = re.compile(
    r"\b(?:SZL )?org(?:anization)?(?:[- ]receipts?)? key\b|a1f6d323|\.github/cosign\.pub",
    re.IGNORECASE,
)
NEGATION = re.compile(r"\b(?:not|never)\b", re.IGNORECASE)
FAILS = re.compile(r"\bfails?\b", re.IGNORECASE)

# Wording that extends the one recorded deploy preview to more packages than it covered.
COLLECTIVE_PREVIEW_CLAIMS = (
    re.compile(
        r"\b(?:dry-?run|deploy preview|preview)s?\b[^.\n]{0,40}"
        r"\b(?:of|for|on) (?:them|all|each|every|the (?:five|5))\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:all|each|every|the) (?:five|5)\b[^.\n]{0,60}\b(?:dry-?run|previewed|deploy preview)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:all|each|every) (?:of the )?packages?\b[^.\n]{0,60}"
        r"\b(?:dry-?run|previewed|deploy preview)",
        re.IGNORECASE,
    ),
)
# Wording that turns a cancelled deploy into a deployment.
DEPLOY_SUCCESS_CLAIMS = (
    re.compile(r"\b(?:successfully|cleanly) deployed\b", re.IGNORECASE),
    re.compile(r"\bdeployed (?:successfully|cleanly|OK)\b", re.IGNORECASE),
    re.compile(r"\bdeploy(?:ment)? (?:succeeded|passed|completed|OK)\b", re.IGNORECASE),
)
LOADED_PACKAGE = re.compile(r"\bloading package source=\S*?(zarf-package-[^/\s]+\.tar\.zst)")
PACKAGE_FILE = re.compile(
    r"^zarf-package-(?P<name>[a-z0-9-]+?)-(?P<arch>amd64|arm64)-(?P<version>\d+\.\d+\.\d+)\.tar\.zst$"
)
# One row of the card's package table: | `name` | `version` | `file` | `sha256` |
ARTIFACT_ROW = re.compile(
    r"^\|\s*`(?P<name>[a-z0-9-]+)`\s*\|\s*`(?P<version>\d+\.\d+\.\d+)`\s*\|"
    r"\s*`(?P<file>zarf-package-[^`]+\.tar\.zst)`\s*\|\s*`(?P<sha256>[0-9a-f]{64})`\s*\|\s*$",
    re.MULTILINE,
)
# bundle.expected_ref in PROOF.json, e.g. ghcr.io/szl-holdings/szl-mesh:v0.4.0
PROOF_REF = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*://)?(?:[^/@\s]+/)*"
    r"(?P<name>[a-z0-9][a-z0-9._-]*):(?P<version>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"(?:@sha256:[0-9a-f]{64})?$"
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class Artifact(NamedTuple):
    """The identity a card claims for one package, and a proof must carry to cover it."""

    name: str
    version: str
    sha256: str


def read_card(dataset):
    return (CARDS / dataset / "README.md").read_text(encoding="utf-8")


def short_fp(fp):
    """The short fingerprint form used in COSIGN_KEYS.md, e.g. daa4aeca…7cb40b."""
    return f"{fp[:8]}…{fp[-6:]}"


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+|\n\s*\n", text) if s.strip()]


def org_key_signer_claims(text):
    """Sentences that name the org receipts key without saying it is not the signer.

    The org key may appear only to rule it out: a "not"/"never" before the reference, or
    "fails" after it, in the same sentence.
    """
    bad = []
    for sentence in sentences(text):
        for match in ORG_KEY_REF.finditer(sentence):
            ruled_out = NEGATION.search(sentence[: match.start()]) or FAILS.search(
                sentence[match.end():]
            )
            if not ruled_out:
                bad.append(sentence.strip())
                break
    return bad


def names_package_signing_key(text):
    """True if one paragraph names the uds-bundles key and its public-key path."""
    for para in paragraphs(text):
        if (
            "signing key" in para
            and (UDS_BUNDLES_SPKI_SHA256 in para or short_fp(UDS_BUNDLES_SPKI_SHA256) in para)
            and UDS_BUNDLES_PUBKEY in para
        ):
            return True
    return False


def parse_package_file(filename):
    match = PACKAGE_FILE.match(filename)
    if not match:
        return None
    return match["name"], match["version"]


def recorded_deploy_previews(log_text):
    """(name, version) of every package a zarf deploy log loaded, in order."""
    previews = []
    for match in LOADED_PACKAGE.finditer(log_text):
        parsed = parse_package_file(match.group(1))
        if parsed and parsed not in previews:
            previews.append(parsed)
    return previews


def deploy_preview_errors(text, previews, cancelled, other_packages):
    """Problems with how text describes the recorded deploy previews.

    previews: (name, version) pairs the log actually loaded; cancelled: whether the log
    ends in a cancelled deployment; other_packages: package names the log did not load.
    """
    errors = [f"collective preview claim: {p.pattern}" for p in COLLECTIVE_PREVIEW_CLAIMS if p.search(text)]
    errors += [f"deployment success claim: {p.pattern}" for p in DEPLOY_SUCCESS_CLAIMS if p.search(text)]
    preview_paras = [p for p in paragraphs(text) if re.search(r"deploy preview", p, re.IGNORECASE)]
    if previews and not preview_paras:
        errors.append("no paragraph describes the recorded deploy preview")
    for para in preview_paras:
        for name, version in previews:
            if name not in para or version not in para:
                errors.append(f"preview paragraph does not name {name} {version}")
        if cancelled and not re.search(r"cancell?ed", para, re.IGNORECASE):
            errors.append("preview paragraph does not say the deployment was cancelled")
        for name in other_packages:
            if name in para:
                errors.append(f"preview paragraph names {name}, which has no recorded preview")
    return errors


def card_artifact_rows(text):
    return [m.groupdict() for m in ARTIFACT_ROW.finditer(text)]


def card_artifacts(text):
    return [Artifact(r["name"], r["version"], r["sha256"]) for r in card_artifact_rows(text)]


def read_sha256sums(path):
    sums = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, _, name = line.partition("  ")
            sums[name.strip().rsplit("/", 1)[-1]] = digest.strip()
    return sums


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


def load_proof(path):
    try:
        proof = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return proof if isinstance(proof, dict) else None


def airgap_proof_passed(path):
    """True only for a captured proof with overall=PASS recorded while OFFLINE.

    Necessary, not sufficient: see airgap_proof_admits for the identity binding.
    """
    proof = load_proof(path)
    if proof is None:
        return False
    network = proof.get("network")
    return (
        proof.get("overall") == "PASS"
        and isinstance(network, dict)
        and network.get("result") == "OFFLINE"
    )


def proof_identity(proof):
    """The artifact a proof receipt is about, from the capture_airgap_proof.sh schema.

    Name and version come from bundle.expected_ref; the hash is bundle.local_sha256,
    the sha256 of the tarball the harness deployed. None if any part is missing.
    """
    bundle = proof.get("bundle") if isinstance(proof, dict) else None
    if not isinstance(bundle, dict):
        return None
    ref, digest = bundle.get("expected_ref"), bundle.get("local_sha256")
    if not isinstance(ref, str) or not isinstance(digest, str):
        return None
    match = PROOF_REF.match(ref.strip())
    digest = digest.strip().lower()
    if digest.startswith("sha256:"):
        digest = digest[len("sha256:"):]
    if not match or not HEX64.match(digest):
        return None
    return Artifact(match["name"], match["version"], digest)


def airgap_proof_admits(path, artifact):
    """True only for an OFFLINE PASS proof whose name, version and sha256 equal artifact's."""
    return airgap_proof_passed(path) and proof_identity(load_proof(path)) == artifact


def airgap_overclaims(text, proof_paths, artifacts):
    """Return the air-gap deployment claims in text that the proofs do not support.

    A claim is supported only when every artifact the card claims has its own
    identity-bound OFFLINE PASS proof. With no claimed artifacts nothing is admitted.
    """
    artifacts = list(artifacts)
    if artifacts and all(
        any(airgap_proof_admits(path, artifact) for path in proof_paths) for artifact in artifacts
    ):
        return []
    return [p.pattern for p in AIRGAP_DEPLOY_CLAIMS if p.search(text)]


A11OY = Artifact(
    "a11oy-runtime-proof", "0.3.1", "800c75865b588cc56d9042ac029d67e11999fd54c09e1c6b3631667ab0984d79"
)
AMARU = Artifact(
    "amaru-attestation-proof", "0.3.1", "041e8ac703689ad2f8dcb123862ab3aab32bd7290d96c4e05f5cfc3aca32cfef"
)
OFFLINE_PASS = {"overall": "PASS", "network": {"result": "OFFLINE"}}


def receipt(ref, digest, **overrides):
    """A PROOF.json payload in the capture_airgap_proof.sh shape."""
    payload = dict(OFFLINE_PASS)
    payload["bundle"] = {"path": "/media/usb/x.tar.zst", "expected_ref": ref, "local_sha256": digest}
    payload.update(overrides)
    return payload


class AirgapProofGateTests(unittest.TestCase):
    def write_proof(self, directory, payload, name="PROOF.json"):
        path = Path(directory) / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_missing_proof_does_not_pass(self):
        missing = ROOT / "does-not-exist" / "PROOF.json"
        self.assertFalse(airgap_proof_passed(missing))
        self.assertFalse(airgap_proof_admits(missing, A11OY))

    def test_only_offline_pass_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = [
                (OFFLINE_PASS, True),
                ({"overall": "PASS", "network": {"result": "ONLINE"}}, False),
                ({"overall": "PENDING", "network": {"result": "OFFLINE"}}, False),
                ({"overall": "PASS"}, False),
                (["PASS", "OFFLINE"], False),
            ]
            for payload, expected in cases:
                with self.subTest(payload=payload):
                    self.assertIs(airgap_proof_passed(self.write_proof(tmp, payload)), expected)

    def test_offline_pass_must_carry_the_claimed_identity(self):
        ref = "ghcr.io/szl-holdings/packages/a11oy-runtime-proof:0.3.1"
        with tempfile.TemporaryDirectory() as tmp:
            cases = [
                ("matching name, version and sha256", receipt(ref, A11OY.sha256), True),
                ("sha256: prefix", receipt(ref, "sha256:" + A11OY.sha256), True),
                ("PASS/OFFLINE with no bundle identity", OFFLINE_PASS, False),
                (
                    "capture_airgap_proof.sh default bundle (szl-mesh v0.4.0)",
                    receipt("ghcr.io/szl-holdings/szl-mesh:v0.4.0", A11OY.sha256),
                    False,
                ),
                (
                    "wrong package, same version and hash",
                    receipt("ghcr.io/szl-holdings/packages/amaru-attestation-proof:0.3.1", A11OY.sha256),
                    False,
                ),
                (
                    "wrong version",
                    receipt("ghcr.io/szl-holdings/packages/a11oy-runtime-proof:0.3.0", A11OY.sha256),
                    False,
                ),
                ("wrong hash", receipt(ref, AMARU.sha256), False),
                ("missing hash", receipt(ref, None), False),
                ("empty hash", receipt(ref, ""), False),
                ("truncated hash", receipt(ref, A11OY.sha256[:16]), False),
                ("missing ref", receipt(None, A11OY.sha256), False),
                ("ref without a version", receipt("a11oy-runtime-proof", A11OY.sha256), False),
                ("bundle is not an object", dict(OFFLINE_PASS, bundle="a11oy-runtime-proof"), False),
                ("matching identity but ONLINE", receipt(ref, A11OY.sha256, network={"result": "ONLINE"}), False),
                ("matching identity but PENDING", receipt(ref, A11OY.sha256, overall="PENDING"), False),
            ]
            for label, payload, expected in cases:
                with self.subTest(label):
                    self.assertIs(airgap_proof_admits(self.write_proof(tmp, payload), A11OY), expected)

    def test_guard_flags_the_original_wording(self):
        original = (
            "Airgap-deployable UDS Core / Zarf productionization artifacts. "
            "Each organ ships as a self-contained, cosign-signed Zarf bundle deployable "
            "into an airgapped k3d / UDS Core mesh."
        )
        self.assertEqual(len(airgap_overclaims(original, [ROOT / "does-not-exist"], [A11OY])), 2)
        with tempfile.TemporaryDirectory() as tmp:
            no_identity = self.write_proof(tmp, OFFLINE_PASS, "no-identity.json")
            self.assertEqual(len(airgap_overclaims(original, [no_identity], [A11OY])), 2)
            mesh = self.write_proof(
                tmp, receipt("ghcr.io/szl-holdings/szl-mesh:v0.4.0", "7f" * 32), "mesh.json"
            )
            self.assertEqual(len(airgap_overclaims(original, [mesh], [A11OY])), 2)
            matching = self.write_proof(
                tmp, receipt("oci://ghcr.io/szl-holdings/a11oy-runtime-proof:0.3.1", A11OY.sha256)
            )
            self.assertEqual(airgap_overclaims(original, [matching], [A11OY]), [])

    def test_hyphenated_verification_wording_is_flagged(self):
        for wording in ("air-gap deployment verification", "airgap deployment verification"):
            with self.subTest(wording):
                self.assertEqual(
                    len(airgap_overclaims(f"Includes {wording}.", [ROOT / "does-not-exist"], [A11OY])),
                    1,
                )

    def test_one_package_proof_does_not_cover_other_packages(self):
        claim = "Each package is air-gap deployable."
        with tempfile.TemporaryDirectory() as tmp:
            a11oy = self.write_proof(
                tmp, receipt("ghcr.io/szl-holdings/a11oy-runtime-proof:0.3.1", A11OY.sha256), "a.json"
            )
            self.assertNotEqual(airgap_overclaims(claim, [a11oy], [A11OY, AMARU]), [])
            amaru = self.write_proof(
                tmp, receipt("ghcr.io/szl-holdings/amaru-attestation-proof:0.3.1", AMARU.sha256), "b.json"
            )
            self.assertEqual(airgap_overclaims(claim, [a11oy, amaru], [A11OY, AMARU]), [])

    def test_no_claimed_artifact_admits_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = self.write_proof(
                tmp, receipt("ghcr.io/szl-holdings/a11oy-runtime-proof:0.3.1", A11OY.sha256)
            )
            self.assertNotEqual(airgap_overclaims("air-gap deployable", [proof], []), [])


class SigningKeyAttributionTests(unittest.TestCase):
    ORIGINAL = (
        "Each is cosign-signed with the SZL org key and verified with "
        "`cosign verify-blob --insecure-ignore-tlog=true`."
    )

    def test_original_wording_names_the_org_key_as_signer(self):
        self.assertEqual(len(org_key_signer_claims(self.ORIGINAL)), 1)

    def test_org_key_named_as_signer_fails(self):
        for wording in (
            "The packages are signed with the org receipts key `a1f6d323…2826ab`.",
            "Verify them with `szl-holdings/.github/cosign.pub`.",
            "Signer: organization key a1f6d3233442cdad0801c702e0ff77aa45fd1ba45f532e3919c80d520b2826ab.",
        ):
            with self.subTest(wording):
                self.assertEqual(len(org_key_signer_claims(wording)), 1)

    def test_org_key_may_be_named_to_rule_it_out(self):
        for wording in (
            "The signer is not the SZL org receipts key `a1f6d323…2826ab`.",
            "Verifying these packages against the org key fails by design.",
        ):
            with self.subTest(wording):
                self.assertEqual(org_key_signer_claims(wording), [])

    def test_signing_key_must_be_named_with_its_public_key(self):
        good = (
            f"Signing key: the uds-bundles signing key {short_fp(UDS_BUNDLES_SPKI_SHA256)}, "
            f"public key {UDS_BUNDLES_PUBKEY}."
        )
        self.assertTrue(names_package_signing_key(good))
        self.assertFalse(names_package_signing_key(self.ORIGINAL))
        self.assertFalse(
            names_package_signing_key(f"Signing key: {short_fp(ORG_RECEIPTS_SPKI_SHA256)}, {UDS_BUNDLES_PUBKEY}.")
        )
        self.assertFalse(
            names_package_signing_key(f"Signing key: {short_fp(UDS_BUNDLES_SPKI_SHA256)}, .github/cosign.pub.")
        )


class SigningKeyEvidenceTests(unittest.TestCase):
    """The key constants above must match the repository's key map and signing log."""

    def section(self, text, start, end):
        return text[text.index(start):text.index(end)]

    def test_cosign_keys_map_binds_the_fingerprints(self):
        keys = COSIGN_KEYS.read_text(encoding="utf-8")
        uds = self.section(keys, "### Key 2", "### Key 3")
        self.assertIn("UDS-BUNDLES signing key", uds)
        self.assertIn(UDS_BUNDLES_SPKI_SHA256, uds)
        self.assertIn(short_fp(UDS_BUNDLES_SPKI_SHA256), uds)
        self.assertIn(UDS_BUNDLES_PUBKEY, uds)
        org = self.section(keys, "### Key 1", "### Key 2")
        self.assertIn("ORG RECEIPTS key", org)
        self.assertIn(ORG_RECEIPTS_SPKI_SHA256, org)
        self.assertIn("DOES NOT verify: uds bundles", org)

    def test_signing_log_attributes_the_proof_packages_to_the_uds_bundles_key(self):
        log = SIGNING_LOG.read_text(encoding="utf-8")
        self.assertIn(f"signing key** (SHA-256(DER SPKI) `{short_fp(UDS_BUNDLES_SPKI_SHA256)}`", log)
        self.assertIn(f"`{UDS_BUNDLES_PUBKEY}`", log)
        self.assertIn(f"**NOT the SZL org key** `{short_fp(ORG_RECEIPTS_SPKI_SHA256)}`", log)

    def test_public_key_file_is_committed(self):
        # Existence only; the key bytes are not read here.
        self.assertTrue((ROOT / UDS_BUNDLES_PUBKEY).is_file())


class DeployPreviewEvidenceTests(unittest.TestCase):
    def test_the_log_records_one_cancelled_preview(self):
        log = DEPLOY_DRYRUN.read_text(encoding="utf-8")
        self.assertEqual(recorded_deploy_previews(log), [("a11oy-runtime-proof", "0.3.1")])
        self.assertRegex(log, r"(?m)^\s*name: a11oy-runtime-proof$")
        self.assertRegex(log, r"(?m)^\s*version: 0\.3\.1$")
        self.assertIn("failed to deploy package: deployment cancelled", log)


class DeployPreviewWordingTests(unittest.TestCase):
    PREVIEWS = [("a11oy-runtime-proof", "0.3.1")]
    OTHERS = ["amaru-attestation-proof", "sentra-gates-proof"]
    BOUNDED = (
        "Deploy preview: one package only. DEPLOY_DRYRUN.txt records one run, for "
        "a11oy-runtime-proof 0.3.1: zarf printed the deploy preview, then the deployment was "
        "cancelled. Nothing was deployed, and no deploy preview is recorded for the other four "
        "packages."
    )

    def errors(self, text):
        return deploy_preview_errors(text, self.PREVIEWS, True, self.OTHERS)

    def test_bounded_wording_passes(self):
        self.assertEqual(self.errors(self.BOUNDED), [])

    def test_overclaiming_wording_fails(self):
        for label, wording in (
            (
                "original card",
                "A `zarf package deploy` dry-run of them validated checksums and rendered the deploy preview.",
            ),
            ("all five", "All five packages were previewed with zarf package deploy."),
            ("each package", "Each package passed a dry-run and rendered its deploy preview."),
            ("success", self.BOUNDED + " The a11oy package then deployed successfully."),
            ("success", self.BOUNDED + " The deployment succeeded."),
            ("not cancelled", "The deploy preview for a11oy-runtime-proof 0.3.1 rendered."),
            ("wrong package", "The deploy preview for amaru-attestation-proof 0.3.1 was cancelled."),
            ("extra package", self.BOUNDED.replace("other four", "amaru-attestation-proof and three")),
            ("silent", "These are image-free proof packages."),
        ):
            with self.subTest(label):
                self.assertNotEqual(self.errors(wording), [])


class UdsBundlesV1CardTests(unittest.TestCase):
    def setUp(self):
        self.card = read_card("uds-bundles-v1")
        self.rows = card_artifact_rows(self.card)
        self.artifacts = card_artifacts(self.card)

    def test_lists_the_five_proof_packages_from_the_evidence(self):
        sums = read_sha256sums(PROOF_SHA256SUMS)
        packages = {name for name in sums if name.endswith(".tar.zst")}
        self.assertEqual(len(packages), 5)
        self.assertEqual({row["file"] for row in self.rows}, packages)
        self.assertEqual(len(self.rows), 5)
        for row in self.rows:
            with self.subTest(row["file"]):
                self.assertEqual(parse_package_file(row["file"]), (row["name"], row["version"]))
                self.assertEqual(row["sha256"], sums[row["file"]])

    def test_package_hashes_match_the_committed_files(self):
        for row in self.rows:
            with self.subTest(row["file"]):
                data = (PROOF_ARTIFACTS / row["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_names_the_uds_bundles_signing_key(self):
        self.assertTrue(
            names_package_signing_key(self.card),
            f"card must name the uds-bundles key {short_fp(UDS_BUNDLES_SPKI_SHA256)} "
            f"and {UDS_BUNDLES_PUBKEY} as the package signer",
        )

    def test_signing_key_is_bound_to_the_published_bundle_key(self):
        pem = (ROOT / UDS_BUNDLES_PUBKEY).read_text()
        der = base64.b64decode("".join(line for line in pem.splitlines() if not line.startswith("---")))
        self.assertEqual(hashlib.sha256(der).hexdigest(), UDS_BUNDLES_SPKI_SHA256)
        self.assertIn(UDS_BUNDLES_SPKI_SHA256, self.card)

    def test_artifact_archive_does_not_claim_an_example_count(self):
        self.assertNotIn("size_categories", front_matter(self.card))

    def test_does_not_name_the_org_key_as_signer(self):
        self.assertEqual(org_key_signer_claims(self.card), [])

    def test_deploy_preview_is_bounded_to_the_recorded_run(self):
        log = DEPLOY_DRYRUN.read_text(encoding="utf-8")
        previews = recorded_deploy_previews(log)
        previewed = {name for name, _ in previews}
        others = [a.name for a in self.artifacts if a.name not in previewed]
        self.assertEqual(len(others), 4)
        self.assertEqual(
            deploy_preview_errors(self.card, previews, "deployment cancelled" in log, others), []
        )

    def test_no_airgap_deploy_claim_without_identity_bound_proof(self):
        self.assertEqual(
            airgap_overclaims(self.card, [AIRGAP_PROOF], self.artifacts),
            [],
            "card claims an air-gapped deployment but "
            f"{AIRGAP_PROOF.relative_to(ROOT).as_posix()} is missing, not an OFFLINE PASS, "
            "or not bound to every package the card lists",
        )

    def test_does_not_present_a_missing_proof_as_evidence(self):
        self.assertFalse(
            AIRGAP_PROOF.exists(),
            f"{AIRGAP_PROOF.relative_to(ROOT).as_posix()} now exists: update the card's "
            "'no such proof exists today' wording; the identity gate decides what it admits",
        )
        self.assertIn("No cable-pulled air-gap proof has been captured", self.card)
        self.assertIn("no such proof exists today", self.card)

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


class SourceReadmeImportTableTests(unittest.TestCase):
    """huggingface/README.md must say which source cards still match their Hub import."""

    IMPORT_ROW = re.compile(
        r"^\| \[`SZLHOLDINGS/(?P<id>[a-z0-9-]+)`\]\([^)]*\) \| `(?P<rev>[0-9a-f]{40})` \| "
        r"`(?P<sha256>[0-9a-f]{64})` \|$",
        re.MULTILINE,
    )
    BEHIND = re.compile(r"^- `(?P<id>[a-z0-9-]+)`: the Hub copy is \*\*behind\*\*", re.MULTILINE)

    def test_behind_notes_match_the_card_bytes(self):
        text = (ROOT / "huggingface" / "README.md").read_text(encoding="utf-8")
        imported = {m["id"]: m["sha256"] for m in self.IMPORT_ROW.finditer(text)}
        behind = {m["id"] for m in self.BEHIND.finditer(text)}
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
