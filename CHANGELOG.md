# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [uds-v0.4.0] — 2026-06-13

### Added
- **`szl-sda` bundle — killinchu SDA / Domain Awareness capability.** New air-gap-deployable,
  clean-room anomaly / Space-Domain-Awareness UDS component (engine image
  `ghcr.io/szl-holdings/khipu-sda-core:uds-v0.4.0`). Ships `zarf.yaml`, `uds-bundle.yaml`,
  Helm chart (STIG-aligned securityContext, default-deny NetworkPolicy, STRICT mTLS), UDS
  Package CR, cosign image policy (warn mode), DSSE receipt-egress gate, Λ-gate VAP binding,
  Section 889 denylist, SLSA-provenance ConfigMap, and STUB SBOMs. Pipeline:
  DTID → CHARACTERIZE → TWA → FUSE; each detection emits a signed DSSE receipt.
- **`VERSION` file + `scripts/check_version_doctrine.sh` + `version-doctrine.yml` CI** — declares
  `uds-v0.4.0` as the single canonical UDS ecosystem version and enforces no user-visible
  drift, while allowlisting signed historical tags (forward-only).

### Version reconciliation (drift fix)
- Canonical UDS ecosystem version is **`uds-v0.4.0`**. The five flagship organ images
  (a11oy/sentra/amaru/rosie/killinchu) stay **byte-stable at the signed `uds-v0.2.0`** —
  forward-only, never renamed (renaming would break published cosign signatures + Rekor
  entries). The prior v0.3.1 release plan (`mesh/docs/UDS_v0.3.1_RELEASE_PLAN.md`) is marked **SUPERSEDED**.

### Attribution / honesty
- `szl-sda` is **inspired by** the publicly described 4-function SDA framing of True Anomaly's
  "Mosaic"; it is a **clean-room** SZL implementation from permissively licensed lineage. SZL
  Holdings is **not affiliated** with True Anomaly. The `alibi-detect` library is deliberately
  **excluded** (BSL 1.1 since 2024-01-22). No signature or image digest is fabricated; the SDA
  image digest is blank until the founder-gated Forge build signs `uds-v0.4.0` (FA-001).
- SLSA: **L1 honest**; L2 = roadmap / not yet earned (in-toto provenance to be emitted by the founder-gated Forge build, FA-001);
  L2-verified / L3 = roadmap. Λ = Conjecture 1 (advisory, not a theorem). Doctrine v11 LOCKED.

---

## [1.0.0] — 2026-06-09

### Added
- Doctrine v11 compliance — kernel commit `c7c0ba17` (749 declarations / 14 axioms / 163 sorries)
- SLSA Build Level 1 provenance — honest declaration, not overclaimed
- Section 889 attestation — exactly 5 vendors assessed (Huawei, ZTE, Hytera, Hikvision, Dahua)
- DCO `Signed-off-by:` trailers on all commits per Linux Foundation DCO policy
- OpenTelemetry `traceparent` W3C header propagated end-to-end
- `/api/health` endpoint returning structured JSON with `sovereign: true`
- SBOM (CycloneDX) generated and attached to release
- Cosign keyless OIDC signing for container images
- OpenSSF Scorecard GHA workflow
- SECURITY.md with 90-day responsible disclosure policy
- SUPPORT.md with issue triage SLAs
- CODEOWNERS covering all critical paths
- Dependabot weekly dependency updates
- Trivy/Grype container vulnerability scanning gate
- SLO documentation (p50/p95/p99 targets + error budget)
- Threat model (STRIDE format)
- CITATION.cff for academic citeability

### Security
- Section 889 — no covered telecommunications equipment from Huawei, ZTE, Hytera, Hikvision, or Dahua
- No Iron Bank, FedRAMP, CMMC, or SWFT claims (capability honesty per Anthropic RSP)
- Λ = Conjecture 1 (never a theorem) — mathematical honesty enforced

### Notes
- Warhacker June 9, 2026 release

[Unreleased]: https://github.com/szl-holdings/uds-bundles/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/szl-holdings/uds-bundles/releases/tag/v1.0.0
