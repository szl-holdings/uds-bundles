# STATUS.md — uds-bundles (Airgap-Deployable Defense Artifact)

**Updated:** 2026-06-13
**Doctrine v11 — 749 / 14 / 163 — replay hash c7c0ba17**

---

## What's Live

- **UDS bundle** — airgap-deployable artifact for defense / enterprise deployment
- **SLSA-aligned build** — build provenance tracked; **organ images are SLSA L1 honest · L2 build-attested** (each carries a `.sig` cosign signature AND a `.att` SLSA provenance attestation on GHCR). The mesh/product bundle is **cosign-signed only** — bundle-level SLSA provenance attestation is **NOT yet earned (roadmap)**; the cosign signature is currently the bundle's sole provenance.
- **EU AI Act Article 12 alignment** — audit trail requirements addressed via Wire D receipts

## What's Experimental

- **SLSA L1 honest · L2 build-attested on organs** — each organ image carries source + build provenance and an L2 SLSA provenance attestation that cryptographically verifies (`cosign verify-attestation`, keyless Fulcio+Rekor); the matching `.att` is published alongside each image `.sig` on GHCR. The mesh bundle (`szl-mesh:v0.4.0` / `a11oy-bundle:0.5.0`) is **cosign-signed only** — its build-provenance attestation is **roadmap**, blocked on an owner-only GHCR package-write grant. Do NOT claim the bundle is L2-attested until `cosign verify-attestation` returns a provenance payload for the bundle. **L3 is NOT claimed** (no FedRAMP, Iron Bank, or CMMC).
- **Automated bundle signing** — Sigstore/cosign integration under development

## What's Deprecated

Nothing deprecated in this repo.

---

*Co-Authored-By: Perplexity Computer Agent*
*Doctrine v11 — 749/14/163 — c7c0ba17 · SLSA L1 honest · L2 attested (organs) · L3 roadmap*
