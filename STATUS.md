# STATUS.md — uds-bundles (Airgap-Deployable Defense Artifact)

**Updated:** 2026-06-13
**Doctrine v11 — 749 / 14 / 163 — replay hash c7c0ba17**

---

## What's Live

- **UDS bundle** — airgap-deployable artifact for defense / enterprise deployment
- **SLSA-aligned build** — build provenance tracked; **organ images are SLSA L1 honest · L2 build-attested** (each carries a `.sig` cosign signature AND a `.att` SLSA provenance attestation on GHCR). The mesh/product bundle is **cosign-signed only** — bundle-level SLSA provenance attestation is **NOT yet earned (roadmap)**; the cosign signature is currently the bundle's sole provenance.
- **EU AI Act Article 12 alignment** — audit trail requirements addressed via Wire D receipts

## Air-Gap Deploy Proof (Raven proof) — HONEST status

The Warhacker challenge is BUILD → PACKAGE → **DEPLOY**; the deploy is the answer. Two distinct things, kept separate so nothing is overclaimed:

| Claim | Status |
|---|---|
| **Deploy *pipeline* proven in CI** — real ephemeral k3d cluster: `zarf package create` → `zarf init` → `zarf package deploy` → pod Ready → `/healthz` 200 → DSSE receipt `cosign verify-blob` → Verified OK, `receipts.in == receipts.out` | ✅ **DONE** — `.github/workflows/deploy-proof.yml` (every push to `main`, hard-asserted gates) |
| **Organ images SLSA L1 honest · L2 build-attested + cosign-signed on GHCR** (all 5 resolve HTTP 200; digests pinned in the harness) | ✅ **DONE** — verified 2026-06-13 |
| **Air-gap package + verify harness proven WITHOUT a privileged box** — harness lints (`bash -n`+`shellcheck`+LINT mode), pins all 5 organ digests + the bundle digest, `uds-bundle.yaml` composes all 5 organs, smoke Zarf package builds, and the OFFLINE `cosign verify-blob --insecure-ignore-tlog=true` path verifies a real signature AND rejects a tampered byte | ✅ **DONE** — `.github/workflows/airgap-package-builds.yml` (green `airgap-package-builds` signal) |
| **Full 5-organ cable-pulled `uds deploy` captured end-to-end** — network physically down, deploy from local store, all 5 organs up, offline signature verify, `PROOF.json` + transcript receipt | ⏳ **RUNBOOK READY · FOUNDER-RUN · TRANSCRIPT PENDING** — `AIRGAP_PROOF_RUNBOOK.md` + `scripts/capture_airgap_proof.sh`. The privileged/cable-pull step is the founder gate (box = prod). **NOT yet captured** — no `PROOF.json` exists until the founder runs it. Do NOT claim "air-gap proof captured" until `releases/szl-warhacker-uds-v1.0.0/airgap-proof/PROOF.json` exists with `overall=PASS` and `network.result=OFFLINE`. |

**Bottom line (honest):** the deploy *pipeline* is proven in CI; the air-gap *package + offline-verify path* is proven in CI; the **full cable-pulled run is plug-and-play (runbook + honesty-gated capture harness) but founder-run** — its receipt is captured on the disconnected box, not in CI (CI cannot pull a cable or fit the 3.6 GB bundle on an ephemeral runner). The harness **refuses to record a proof while online**, so a captured `PROOF.json` is trustworthy by construction.

## What's Experimental

- **SLSA L1 honest · L2 build-attested on organs** — each organ image carries source + build provenance and an L2 SLSA provenance attestation that cryptographically verifies (`cosign verify-attestation`, keyless Fulcio+Rekor); the matching `.att` is published alongside each image `.sig` on GHCR. The mesh bundle (`szl-mesh:v0.4.0` / `a11oy-bundle:0.5.0`) is **cosign-signed only** — its build-provenance attestation is **roadmap**, blocked on an owner-only GHCR package-write grant. Do NOT claim the bundle is L2-attested until `cosign verify-attestation` returns a provenance payload for the bundle. **L3 is NOT claimed** (no FedRAMP, Iron Bank, or CMMC).
- **Automated bundle signing** — Sigstore/cosign integration under development

## What's Deprecated

Nothing deprecated in this repo.

---

*Co-Authored-By: Perplexity Computer Agent*
*Doctrine v11 — 749/14/163 — c7c0ba17 · SLSA L1 honest · L2 attested (organs) · bundle-attestation + L3 roadmap*
