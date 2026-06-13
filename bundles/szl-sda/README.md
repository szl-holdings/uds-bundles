# killinchu SDA · Operational UDS Drop (`szl-sda`)

**Sovereign Domain-Awareness layer.** Engine: `khipu-sda-core` (clean-room anomaly/SDA core).
User-visible surface: *"killinchu SDA / Domain Awareness."*

## WHAT THIS DOES (operational)
- Deploys on UDS Core via `uds-cli bundle deploy oci://ghcr.io/szl-holdings/szl-mesh:v0.4.0 --confirm` (SDA ships inside the meta-bundle) or standalone via `zarf package deploy szl-sda.uds.tar.zst --confirm`.
- Runs air-gapped — pull the network cable, it still works. Sovereign own-metal, 0 CDN.
- **Clean-room multivariate + graph anomaly / Threat-Warning engine.** Detector bank: IsolationForest (PyOD-lineage, BSD-2), Autoencoder (Merlion/TODS-lineage, BSD-3/Apache-2.0), RobustZScore (tsod-lineage, MIT), GraphDeviation (GDN/PyGOD-lineage, MIT/BSD-2).
- Scores air/maritime tracks; emits an **advisory Λ-gated** verdict (Λ = Conjecture 1, *never* a theorem) with a **conformal confidence interval labeled ESTIMATE** (not a certainty claim).
- Every detection emits an **in-toto Statement v1 DSSE provenance receipt** into the **Khipu Merkle DAG**. Verify with `cosign verify-blob`.
- Capability **inspired by True Anomaly's Mosaic** ([trueanomaly.space/mosaic](https://www.trueanomaly.space/mosaic)) — *the capability only; no proprietary Mosaic code, assets, or internals were seen or copied.*

### Fills this UDS Core gap
**The sovereign, governed Domain-Superiority operating layer** on top of UDS Core + killinchu: every track, detection, and threat-call carries a signed provenance receipt and an honest Λ-gated confidence.

### Operational endpoints
- `/sda/healthz`
- `POST /sda/evaluate` → the SDA verdict envelope (`anomaly_score`, advisory `lambda_axis`, `confidence{lo,hi,label:ESTIMATE}`, in-toto `receipt`, `_signing.status`)
- killinchu calls this in its fusion path; verdicts route into killinchu's existing `_lake_receipt` Khipu append and surface in a11oy's "Domain Awareness" oversight tab.

## WHAT WE'RE NOT CLAIMING
- **Orbital SDA is ROADMAP.** Today the engine scores **air + maritime** tracks. The orbital-track surface (python-sgp4, MIT) is honest future work — `sda.orbitalRoadmapEnabled: false` by default.
- Λ is **Conjecture 1**, NOT a theorem. The anomaly score is an **advisory** Λ-axis, never "proven trust."
- The SDA engine is an **engineering capability**, NOT folded into the locked-proven count (still exactly 8: `{F1,F4,F7,F11,F12,F18,F19,F22}`). No "kernel-verified/proven" badge on anomaly verdicts.
- **SLSA L1 honest** — L2 build-attestation present where CI runs (`attest-build-provenance` + `cosign verify-attestation`); **L2-verified / L3 are roadmap**. L3 is never claimed.
- Khipu BFT 3-of-4 multi-witness agreement is **Conjecture 2** (open), not proven BFT.
- No fabricated signatures. Until Forge builds + signs `uds-v0.4.0`, the verdict's `_signing.status` is `UNSIGNED` and a11oy treats it as **STRUCTURAL-ONLY** — never a false green. `image.digest` is blank (tag-pinned only) until the real signed digest exists.
- `alibi-detect` is **excluded** (relicensed to BSL 1.1, 2024-01-22 — [Seldon](https://www.seldon.io/strengthening-our-commitment-to-open-core/)) and blocked in CI.

## CLEAN-ROOM ATTRIBUTION (cite-never-plagiarize)
- **Inspiration (capability only, no code):** True Anomaly Mosaic — DTID → Characterize → ML Threat-Warning → fuse/forecast → Common Operating Picture ([Mosaic page](https://www.trueanomaly.space/mosaic); [Eric Hilmer, True Anomaly, LinkedIn](https://www.linkedin.com/posts/erichilmer_true-anomaly-lands-174m-contract-from-us-activity-7110684034724233216-371t)).
- **Permissive lineage (implemented from scratch, attributed):** PyOD (BSD-2), PyGOD (BSD-2), Merlion (BSD-3), TODS (Apache-2.0), tsod (MIT), GDN (MIT, AAAI'21 arXiv 2106.06947), GraGOD (MIT), python-sgp4 (MIT). See `khipu-sda-core/ATTRIBUTION.md` + `THIRD_PARTY_NOTICES`.

## SUBSTRATE
- Engine source: `github.com/szl-holdings/khipu-sda-core` (Apache-2.0, clean-room)
- Wired into: `github.com/szl-holdings/killinchu`
- Doctrine v11 LOCKED 749/14/163; Lean 4 kernel `github.com/szl-holdings/lutar-lean`

## BUNDLE CONTENTS
| Artifact | Path |
|---|---|
| Helm chart | `chart/` |
| Zarf package def | `zarf.yaml` |
| UDS bundle spec | `uds-bundle.yaml` |
| UDS Package CR | `manifests/uds-package.yaml` |
| Pepr + K8s policies | `policies/` |
| Cosign verify reference (PENDING sign) | `attestations/khipu-sda-core.cosign-verify.txt` |
| SLSA provenance stub (PENDING Forge) | `attestations/khipu-sda-core.slsa-provenance.json` |
| SBOM (SPDX + CycloneDX, PENDING Forge) | `sbom/` |

## VERSION
`uds-v0.4.0` — the single canonical UDS version (see repo CHANGELOG version-reconciliation note). The immutable signed `uds-v0.2.0` flagship set is unchanged (forward-only; never renamed).

*Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>*
