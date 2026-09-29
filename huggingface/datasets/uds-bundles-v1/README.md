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
size_categories:
- n<1K
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

Airgap-deployable [UDS Core](https://uds.defenseunicorns.com/) / [Zarf](https://zarf.dev/) productionization artifacts for the SZL Holdings organ substrate (a11oy, amaru, sentra, killinchu, rosie).

## Contents

- `uds_productionization/PER_BUNDLE/<organ>/` — per-organ Dockerfile, Helm chart, and UDS manifests (namespace, authorization policy, service, deployment).
- `uds_productionization/AIRGAP_TEST_REPORT.md` — airgap deployment verification.
- `uds_productionization/COSIGN_SIGNING_LOG.md` — cosign signing provenance.
- `uds_productionization/INVENTORY.md` — bundle inventory.
- `uds_productionization/FOUNDER_DEPLOY_QUICKSTART.md` — operator deployment guide.

## Architecture

Each organ ships as a self-contained, cosign-signed Zarf bundle deployable into an airgapped k3d / UDS Core mesh. Every deployment emits DSSE-signed Khipu receipts onto the Merkle DAG.

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
