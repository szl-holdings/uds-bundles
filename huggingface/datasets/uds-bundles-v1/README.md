---
license: apache-2.0
pretty_name: SZL UDS Bundles v1
tags:
- szl-holdings
- uds-core
- zarf
- cosign
- slsa
- airgap
- agentic-ai
- governance
- doi:10.5281/zenodo.19944926
language:
- en
task_categories:
- other
---

<!-- SZL-ESTATE-CARD:v2:START -->
<p align="center"><a href="https://a-11-oy.com/"><img src="https://huggingface.co/spaces/SZLHOLDINGS/README/resolve/main/assets/estate-banner-v2.svg" alt="SZL Holdings — governed, receipted, verifiable" width="100%"></a></p>
<p align="center">
  <a href="https://github.com/szl-holdings/.github/tree/main/doctrine"><img src="https://img.shields.io/badge/doctrine-v11%20LOCKED-0B1F3A?style=flat-square" alt="doctrine v11"></a>
  <a href="https://a-11-oy.com/"><img src="https://img.shields.io/badge/evidence%20wall-LIVE%20%C2%B7%20verify%20in%20browser-3AF4C8?style=flat-square" alt="live evidence wall"></a>
  <a href="https://huggingface.co/datasets/SZLHOLDINGS/szl-lake"><img src="https://img.shields.io/badge/szl--lake-offline%20verifiable-C9B787?style=flat-square" alt="szl-lake offline verifiable"></a>
  <a href="https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab"><img src="https://img.shields.io/badge/estate%20map-Atlas-5B8DEE?style=flat-square" alt="SZL Atlas estate map"></a>
</p>
<p align="center"><sub>Part of the <a href="https://huggingface.co/SZLHOLDINGS">SZL Holdings</a> governed estate — claims are designed to carry checkable receipts. Verification proves integrity &amp; origin, never accuracy or performance.</sub></p>
<!-- SZL-ESTATE-CARD:v2:END -->

<div align="center">
<p>

[![dataset](https://img.shields.io/badge/dataset-UDS%20%2F%20Zarf%20bundles-3af4c8?style=flat-square)](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/tree/main)
[![license](https://img.shields.io/badge/license-apache--2.0-7e8aa3?style=flat-square)](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1)

</p>
</div>

# SZL UDS Bundles v1

[UDS Core](https://uds.defenseunicorns.com/) / [Zarf](https://zarf.dev/) packaging artifacts (airgap-targeted; airgap deploy not yet demonstrated) for the SZL Holdings organ substrate (a11oy, amaru, sentra, killinchu, rosie).

## Contents

- `uds_productionization/PER_BUNDLE/<organ>/` — per-organ Dockerfile, Helm chart, and UDS manifests (namespace, authorization policy, service, deployment).
- `uds_productionization/artifacts/` — the five image-free proof packages listed under Architecture, their detached cosign signatures (`<organ>-proof.uds.sig`), a copy of the public key `cosign_signing_key.pub`, and the 2026-06-01 capture logs (`SHA256SUMS_PROOF.txt`, `PROOF_CAPTURE.txt`, `VERIFY_RECHECK.txt`, `DEPLOY_DRYRUN.txt`).
- [`uds_productionization/AIRGAP_TEST_REPORT.md`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/blob/main/uds_productionization/AIRGAP_TEST_REPORT.md) — airgap test status report (PARTIAL: image-free proof packages only; image-bearing build and kind airgap test not run).
- [`uds_productionization/GAP_CHECK.md`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/blob/main/uds_productionization/GAP_CHECK.md) — phase-by-phase status, including the blocked items.
- `uds_productionization/COSIGN_SIGNING_LOG.md` — cosign signing provenance.
- `uds_productionization/INVENTORY.md` — bundle inventory.
- `uds_productionization/FOUNDER_DEPLOY_QUICKSTART.md` — operator deployment guide.

## Architecture

The five Zarf packages below are **image-free proof packages** (about 2 KB each, built with zarf v0.51.0 without the `images:` layer). They are files of this dataset under `uds_productionization/artifacts/`. Hub commit `ab5cc3ff7977b06083bc8114de0b79f419112d7c` (2026-06-01) added them, and a read-only listing of Hub revision `28c14086211944cfc2ceb6ece0f729153b545575` on 2026-10-13 showed all five with LFS sha256 object ids equal to the values below and to `uds_productionization/artifacts/SHA256SUMS_PROOF.txt`. `uds_productionization/HF_PUSH_LOG.md` records only the earlier upload (Hub commit `bcfd121a0e56969c48a09045c282508d46fd0d81`), which excluded `artifacts/*`.

| Package | Version | File | sha256 |
|---|---|---|---|
| `a11oy-runtime-proof` | `0.3.1` | `zarf-package-a11oy-runtime-proof-amd64-0.3.1.tar.zst` | `800c75865b588cc56d9042ac029d67e11999fd54c09e1c6b3631667ab0984d79` |
| `amaru-attestation-proof` | `0.3.1` | `zarf-package-amaru-attestation-proof-amd64-0.3.1.tar.zst` | `041e8ac703689ad2f8dcb123862ab3aab32bd7290d96c4e05f5cfc3aca32cfef` |
| `sentra-gates-proof` | `0.3.1` | `zarf-package-sentra-gates-proof-amd64-0.3.1.tar.zst` | `4109db4c278d4a02f8f32be7fde575dda756a8b338e028d1dfef8d491c2e464b` |
| `killinchu-bundle-proof` | `0.3.1` | `zarf-package-killinchu-bundle-proof-amd64-0.3.1.tar.zst` | `0e581c9f73de8187ee5d14c7cdeeeff1f55f85820e117b031cee987478d53874` |
| `rosie-replay-proof` | `0.3.1` | `zarf-package-rosie-replay-proof-amd64-0.3.1.tar.zst` | `ed04612ee6738e90fd0c6acc3ac70dea9240b24e51cef3ac751c08cb7b1ac5e2` |

**Signing key.** Each package has a detached cosign signature (`<organ>-proof.uds.sig`) made with the **uds-bundles signing key**: SHA-256 of the DER SubjectPublicKeyInfo `daa4aeca263251e97125fd227ff82e024a64ec970d1c74828463ffba097cb40b`, public key [`bundles/v0.1.0/cosign_signing_key.pub`](https://github.com/szl-holdings/uds-bundles/blob/main/bundles/v0.1.0/cosign_signing_key.pub) in the GitHub source (`uds_productionization/artifacts/cosign_signing_key.pub` in this dataset is the same file). The signer is not the SZL org receipts key `a1f6d323…2826ab` (`szl-holdings/.github/cosign.pub`); verifying these packages against the org key fails by design. See [`COSIGN_KEYS.md`](https://github.com/szl-holdings/uds-bundles/blob/main/COSIGN_KEYS.md). The signatures were made offline (`--tlog-upload=false`), so they have no transparency-log entry. The 2026-06-01 logs (`uds_productionization/COSIGN_SIGNING_LOG.md`, `VERIFY_RECHECK.txt`) record `Verified OK` for each package from `cosign verify-blob --insecure-ignore-tlog=true` (offline key verification, no transparency-log check).

**Deploy preview: one package only.** [`DEPLOY_DRYRUN.txt`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/blob/main/uds_productionization/artifacts/DEPLOY_DRYRUN.txt) records one `zarf package deploy` run, for `a11oy-runtime-proof` `0.3.1`: zarf loaded the package, validated its checksums and printed the deploy preview, then the deployment was cancelled at the confirmation prompt. Nothing was deployed, and no deploy preview is recorded for the other four packages.

What has **not** been done for this dataset's payload:

- the image-bearing production packages (with the organ container images baked in) were not built or signed;
- no SBOM was generated or attested;
- no package was deployed: the one recorded deploy run was cancelled before deployment;
- the kind / k3d air-gapped deploy test was not run.

The statements above cite the 2026-06-01 logs. No signature was re-verified and nothing was re-run to write this card.

See [`AIRGAP_TEST_REPORT.md`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/blob/main/uds_productionization/AIRGAP_TEST_REPORT.md) and [`GAP_CHECK.md`](https://huggingface.co/datasets/SZLHOLDINGS/uds-bundles-v1/blob/main/uds_productionization/GAP_CHECK.md).

In the GitHub source repository, CI proves the deploy *pipeline* on an online, ephemeral k3d cluster ([`deploy-proof.yml`](https://github.com/szl-holdings/uds-bundles/blob/main/.github/workflows/deploy-proof.yml)); that cluster is not air-gapped. No cable-pulled air-gap proof has been captured: [`STATUS.md`](https://github.com/szl-holdings/uds-bundles/blob/main/STATUS.md) records that `releases/szl-warhacker-uds-v1.0.0/airgap-proof/PROOF.json` does not exist yet. Do not read this dataset as evidence of an air-gapped deployment.

A future air-gap deployment claim for these packages needs a captured `PROOF.json` that records `overall: PASS` and `network.result: OFFLINE`, and whose bundle identity matches every package the claim covers: the package name and version in `bundle.expected_ref`, and the file sha256 in `bundle.local_sha256`. A proof captured for a different artifact does not count. For example, [`scripts/capture_airgap_proof.sh`](https://github.com/szl-holdings/uds-bundles/blob/main/scripts/capture_airgap_proof.sh) currently targets the image-bearing `szl-mesh:v0.4.0` bundle, not these `0.3.1` proof packages. `tests/test_hf_dataset_cards.py` in the GitHub source enforces this rule. It is an admission rule for a future claim, not evidence: no such proof exists today.

## Demo

Live status: ~~https://huggingface.co/spaces/SZLHOLDINGS/status~~ *(Space removed — see [SZLHOLDINGS/a11oy](https://huggingface.co/spaces/SZLHOLDINGS/a11oy) for live substrate status)*

## License

Apache-2.0. See the SZL Holdings monorepo for the canonical license.

## Citation


**Cite this.** Part of the SZL Holdings *Ouroboros Thesis* (Governed Post-Determinism).  
Concept DOI (always-latest): [10.5281/zenodo.19944926](https://doi.org/10.5281/zenodo.19944926).  
Author: Stephen P. Lutar Jr. · [ORCID 0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173) · Dataset license: Apache-2.0; the cited program publication is CC-BY-4.0.  
Full DOI-pinned lineage (v1→v26) + the 8 papers: [szl-papers PAPERS_INDEX](https://github.com/szl-holdings/szl-papers/blob/main/PAPERS_INDEX.md).  
No artifact-specific DOI is minted for this dataset; the concept DOI above covers the program.

Honesty (Doctrine v11): Λ unconditional uniqueness is **Conjecture 1** (machine-checked FALSE as stated) — never a theorem; conditional uniqueness is **Theorem U** (axiom-free). Locked-proven formulas = **exactly 8** {F1,F4,F7,F11,F12,F18,F19,F22}; ~185 experimental theorems are a separate CI-green tier; Khipu BFT safety = Conjecture 2. Trust never 100%.

Concept DOI: [10.5281/zenodo.19944926](https://doi.org/10.5281/zenodo.19944926)

```bibtex
@misc{szl_uds_bundles_v1,
  title  = {SZL UDS Bundles v1},
  author = {SZL Holdings},
  year   = {2026},
  doi    = {10.5281/zenodo.19944926}
}
```

## Doctrine attestation

Doctrine v11 LOCKED (749/14/163). Λ Conjecture 1. Honest-by-default.

---

### ◇ Explore the SZL Holdings estate
[▶ a11oy console (a-11-oy.com)](https://a-11-oy.com) · [a11oy Space](https://huggingface.co/spaces/SZLHOLDINGS/a11oy) · [killinchu](https://huggingface.co/spaces/SZLHOLDINGS/killinchu) · [holographic (3D)](https://huggingface.co/spaces/SZLHOLDINGS/holographic) · [all datasets & models → SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS) · [GitHub org](https://github.com/szl-holdings)

---

<div align="center">

**[🛡️ SZLHOLDINGS on Hugging Face →](https://huggingface.co/SZLHOLDINGS)**   ·   **[a-11-oy.com →](https://a-11-oy.com)**   ·   **[SZL Atlas — estate map →](https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab)**

### Governed AI you can prove.

<sub>SLSA: L1 honest · L2 attested · L3 roadmap. Λ = Conjecture 1 (advisory, never a theorem). Trust ceiling 0.97 — never 100%. Labels honest by default: MEASURED / REPORTED / MODELED / HEURISTIC / UNKNOWN / UNAVAILABLE. locked-proven = exactly 8 {F1,F4,F7,F11,F12,F18,F19,F22}.</sub>

</div>

## Viewer and artifact boundary

This repository is a deployment-artifact archive, not a homogeneous table. Zarf bundles, Helm/Kubernetes manifests, signatures, scripts, and operator documentation must be consumed by path at a pinned revision. No `size_categories` value is declared because file count is not an example count, and a Hub table-viewer failure does not establish bundle validity.
