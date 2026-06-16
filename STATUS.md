# STATUS.md — uds-bundles (Airgap-Deployable Defense Artifact)

**Updated:** 2026-06-16
**Doctrine v11 — 749 / 14 / 163 — replay hash c7c0ba17**

---

## What's Live

- **UDS bundle** — airgap-deployable artifact for defense / enterprise deployment
- **SLSA-aligned build** — build provenance tracked; **organ images are SLSA L1 honest (all 5 pinned digests cosign-signed); L2 SLSA provenance is verifiable on 4 of the 5 pinned digests** (killinchu, sentra, amaru, rosie — each carries a `.att` SLSA provenance attestation that `cosign verify-attestation` confirms live). **The pinned a11oy digest `@sha256:8aaea251` is L1-signed only — its L2 re-attestation is pending/founder-gated** (the live `a11oy:uds-v0.2.0` tag IS L2-attested, but the digest pinned into this bundle predates that attestation). Do NOT claim all-5-organ L2 until `cosign verify-attestation --type slsaprovenance` passes on the a11oy *pinned digest*. The mesh/product bundle artifact (`szl-uds-bundle:uds-v0.3.0`) is **cosign-signed AND carries a published, anonymously-verifiable post-publish SLSA provenance attestation** (`slsa.dev/provenance/v0.2`, keyless Sigstore/Rekor); in-line build-provenance (true SLSA L2 for the bundle) is **NOT yet earned (roadmap)**.
- **EU AI Act Article 12 alignment** — audit trail requirements addressed via Wire D receipts

## Air-Gap Deploy Proof (Raven proof) — HONEST status

The Warhacker challenge is BUILD → PACKAGE → **DEPLOY**; the deploy is the answer. Two distinct things, kept separate so nothing is overclaimed:

| Claim | Status |
|---|---|
| **Deploy *pipeline* proven in CI** — real ephemeral k3d cluster: `zarf package create` → `zarf init` → `zarf package deploy` → pod Ready → `/healthz` 200 → DSSE receipt `cosign verify-blob` → Verified OK, `receipts.in == receipts.out` | ✅ **DONE** — `.github/workflows/deploy-proof.yml` (every push to `main`, hard-asserted gates) |
| **Organ images cosign-signed (SLSA L1 honest) on GHCR** — all 5 pinned digests resolve HTTP 200 and `cosign verify` passes | ✅ **DONE** — verified 2026-06-16 (live keyless cosign verify, all 5 pinned digests) |
| **Organ-image L2 SLSA provenance attestation** — `cosign verify-attestation --type slsaprovenance` confirms on the pinned digests of **killinchu, sentra, amaru, rosie (4 of 5)** | ✅ **DONE for 4/5** — verified 2026-06-16. **a11oy pinned digest L2 re-attestation = ⏳ PENDING / founder-gated** (re-sign+re-attest the pinned a11oy digest, or re-pin to the L2-attested tag digest) |
| **Air-gap package + verify harness proven WITHOUT a privileged box** — harness lints (`bash -n`+`shellcheck`+LINT mode), pins all 5 organ digests + the bundle digest, `uds-bundle.yaml` composes all 5 organs, smoke Zarf package builds, and the OFFLINE `cosign verify-blob --insecure-ignore-tlog=true` path verifies a real signature AND rejects a tampered byte | ✅ **DONE** — `.github/workflows/airgap-package-builds.yml` (green `airgap-package-builds` signal) |
| **Full 5-organ cable-pulled `uds deploy` captured end-to-end** — network physically down, deploy from local store, all 5 organs up, offline signature verify, `PROOF.json` + transcript receipt | ⏳ **RUNBOOK READY · FOUNDER-RUN · TRANSCRIPT PENDING** — `AIRGAP_PROOF_RUNBOOK.md` + `scripts/capture_airgap_proof.sh`. The privileged/cable-pull step is the founder gate (box = prod). **NOT yet captured** — no `PROOF.json` exists until the founder runs it. Do NOT claim "air-gap proof captured" until `releases/szl-warhacker-uds-v1.0.0/airgap-proof/PROOF.json` exists with `overall=PASS` and `network.result=OFFLINE`. |

**Bottom line (honest):** the deploy *pipeline* is proven in CI; the air-gap *package + offline-verify path* is proven in CI; the **full cable-pulled run is plug-and-play (runbook + honesty-gated capture harness) but founder-run** — its receipt is captured on the disconnected box, not in CI (CI cannot pull a cable or fit the 3.6 GB bundle on an ephemeral runner). The harness **refuses to record a proof while online**, so a captured `PROOF.json` is trustworthy by construction.

## What's Experimental

- **SLSA L1 honest on all organs; L2 SLSA provenance on 4 of 5 pinned digests** — killinchu/sentra/amaru/rosie pinned digests each carry an L2 SLSA provenance attestation that cryptographically verifies (`cosign verify-attestation --type slsaprovenance`, keyless Fulcio+Rekor); the a11oy *pinned* digest is L1-signed only (L2 re-attestation pending/founder-gated). The mesh bundle (`szl-mesh:v0.4.0` / `a11oy-bundle:0.5.0`) is **cosign-signed only** — its in-line build-provenance attestation is **roadmap**, blocked on an owner-only GHCR package-write grant. Do NOT claim the bundle is L2-attested until `cosign verify-attestation` returns an *in-line build* provenance payload for the bundle (the current bundle attestation is post-publish provenance, not in-line L2). **L3 is NOT claimed** (no FedRAMP, Iron Bank, or CMMC).
- **Automated bundle signing** — Sigstore/cosign integration under development

## What's Deprecated

Nothing deprecated in this repo.

---

*Co-Authored-By: Perplexity Computer Agent*
*Doctrine v11 — 749/14/163 — c7c0ba17 · SLSA L1 honest (all 5 organs signed) · L2 SLSA provenance verified on 4/5 pinned organ digests (a11oy pinned-digest L2 pending) · bundle post-publish provenance; in-line bundle L2 + L3 roadmap*
