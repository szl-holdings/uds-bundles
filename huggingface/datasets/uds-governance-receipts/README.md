---
license: apache-2.0
language:
- en
tags:
- formal-verification
- lean4
- mathlib
- dsse
- governance
- agentic-ai
- arxiv:2401.05566
- arxiv:2407.11214
- doctrine-v11
- rae-1
- uds
- receipts
- audit-log
- slsa-provenance
- doi:10.5281/zenodo.19944926
pretty_name: UDS Governance Receipts — Decision Audit Log
size_categories:
- n<1K
task_categories:
- other
configs:
- config_name: attestations
  data_files:
  - split: train
    path: extended-attestations.jsonl
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

[![dataset](https://img.shields.io/badge/dataset-governance%20receipts-3af4c8?style=flat-square)](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts/tree/main)
[![license](https://img.shields.io/badge/license-apache--2.0-7e8aa3?style=flat-square)](https://huggingface.co/datasets/SZLHOLDINGS/uds-governance-receipts)

</p>
</div>

# UDS Governance Receipts — Decision Audit Log

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20434276.svg)](https://doi.org/10.5281/zenodo.20434276)
[![Lean Kernel Green](https://img.shields.io/badge/Lean_4.13--kernel--green@c7c0ba17-22c55e?style=flat-square)](https://github.com/szl-holdings/lutar-lean/commit/c7c0ba17)
[![SLSA L1](https://img.shields.io/badge/SLSA-L1_honest-blue?style=flat-square)](https://slsa.dev)
[![RAE-1](https://img.shields.io/badge/RAE--1-v1.0-D97757?style=flat-square)](https://github.com/szl-holdings/a11oy/pull/122)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](https://www.apache.org/licenses/LICENSE-2.0)

> **Doctrine v11 LOCKED.** No marketing. Every number resolves to a CI log, a Lean proof, or a Zenodo DOI.

Append-only, **hash-chained** log of governance attestation records for the Unified Deployment Substrate (UDS) mesh. Each record in `extended-attestations.jsonl` carries a SLSA provenance predicate, the build step it attests, a `prev` link to the previous record's hash, a signer DID (`did:plat:szl-a11oy-prod`), and a SHA-256 record `hash`.

**Evidence boundary (read before citing):** the rows are chain-linked attestation records, **not DSSE envelopes**, and they carry no signature field. What this file lets you check is chain integrity (recompute each `hash`, follow `prev`). Signer authenticity is *not* established by these rows. The cosign signature the chain refers to (`cosign verify-blob --key … pointer-manifest.yaml.sig`) applies to the UDS pointer manifest, and the org cosign public key is [`szl-holdings/.github/cosign.pub`](https://github.com/szl-holdings/.github/blob/main/cosign.pub) (also mirrored under [`szl-lake/keys`](https://huggingface.co/datasets/SZLHOLDINGS/szl-lake/tree/main/keys)). Five records are present, dated 2026-05-27 to 2026-06-17; the chain has not been extended since.

## What is in this repository

| Path | Role |
|---|---|
| `extended-attestations.jsonl` | The five hash-chained attestation records (the only rows the Hub dataset viewer loads) |
| `uds-bundle.yaml`, `bundles/v0.3.1/uds-bundle.yaml`, `uds-mesh-pointer-manifest.yaml` | UDS bundle and pointer manifests the records attest |
| `schemas/spans/` | Span graph schema and its test script |
| `uds_v18_24_substrate.py`, `tests/` | Substrate module and the attestation-chain, bundle-manifest, and span-schema tests |
| `DATASET_PROVENANCE.json`, `PROMOTION_READINESS_AUDIT.json`, `SZL_ESTATE_MANAGED.json` | Source-of-record attestation, readiness audit, estate metadata |

## Snapshot boundary

Counts of Lean declarations, sorries, Spaces, datasets and models that earlier versions of this card carried were dated snapshots and drifted from each other across the estate. They have been removed from this card. The live estate inventory is maintained in [`szl-holdings/.github` `profile/public-inventory.json`](https://github.com/szl-holdings/.github/blob/main/profile/public-inventory.json); the Lean kernel state is pinned at [lutar-lean@c7c0ba17](https://github.com/szl-holdings/lutar-lean/commit/c7c0ba17).

## Cross-references

- **Thesis**: [Ouroboros Thesis v18](https://doi.org/10.5281/zenodo.20434276) · DOI 10.5281/zenodo.20434276
- **Lean companion**: [lutar-lean](https://doi.org/10.5281/zenodo.20424992) · DOI 10.5281/zenodo.20424992
- **Receipt gateway source**: [szl-holdings/hatun-mcp](https://github.com/szl-holdings/hatun-mcp) (GitHub; no public Space is currently published for it)
- **Verifiable corpus**: [SZLHOLDINGS/a11oy-verifiable-corpus](https://huggingface.co/datasets/SZLHOLDINGS/a11oy-verifiable-corpus) — signed receipts + kernel-checked theorems (verify-it-yourself)
- **Live demo**: [a11oy console → a-11-oy.com](https://a-11-oy.com) · [a11oy Space](https://huggingface.co/spaces/SZLHOLDINGS/a11oy) · [killinchu](https://huggingface.co/spaces/SZLHOLDINGS/killinchu)
- **Catalog**: [SZLHOLDINGS on Hugging Face](https://huggingface.co/SZLHOLDINGS)
- **Source of record**: this Hugging Face repository. No byte-level parity with a GitHub build source is claimed (see `DATASET_PROVENANCE.json`); the UDS bundle sources live in [szl-holdings/uds-bundles](https://github.com/szl-holdings/uds-bundles) and [szl-holdings/szl-mesh](https://github.com/szl-holdings/szl-mesh).

## Provenance

| Field | Value |
|---|---|
| Ecosystem stage | `generated-mirror` |
| Doctrine | v11 LOCKED — no marketing language, every number resolves to a CI log or Zenodo DOI |
| Thesis DOI | [10.5281/zenodo.20434276](https://doi.org/10.5281/zenodo.20434276) |
| Lean companion DOI | [10.5281/zenodo.20424992](https://doi.org/10.5281/zenodo.20424992) |
| Author | Stephen Paul Lutar Jr. · [ORCID 0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173) |

---

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19944926.svg)](https://doi.org/10.5281/zenodo.19944926)

## Citation

**Cite this.** Part of the SZL Holdings *Ouroboros Thesis* (Governed Post-Determinism).  
Concept DOI (always-latest): [10.5281/zenodo.19944926](https://doi.org/10.5281/zenodo.19944926).  
Author: Stephen P. Lutar Jr. · [ORCID 0009-0001-0110-4173](https://orcid.org/0009-0001-0110-4173) · Dataset license: Apache-2.0; the cited program publication is CC-BY-4.0.  
Full DOI-pinned lineage (v1→v26) + the 8 papers: [szl-papers PAPERS_INDEX](https://github.com/szl-holdings/szl-papers/blob/main/PAPERS_INDEX.md).  
No artifact-specific DOI is minted for this dataset; the concept DOI above covers the program.

Honesty (Doctrine v11): Λ unconditional uniqueness is **Conjecture 1** (machine-checked FALSE as stated) — never a theorem; conditional uniqueness is **Theorem U** (axiom-free). Locked-proven formulas = **exactly 8** {F1,F4,F7,F11,F12,F18,F19,F22}; ~185 experimental theorems are a separate CI-green tier; Khipu BFT safety = Conjecture 2. Trust never 100%.

```bibtex
@misc{lutar_szl_ouroboros,
  author    = {Lutar, Stephen P., Jr.},
  title     = {SZL Holdings --- The Ouroboros Thesis (Governed Post-Determinism)},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19944926},
  url       = {https://doi.org/10.5281/zenodo.19944926},
  note      = {Concept DOI --- always resolves to the latest version. ORCID 0009-0001-0110-4173. CC-BY-4.0.}
}
```

*Signed-off-by: Stephen Lutar <stephenlutar2@gmail.com>*

---

<div align="center">

**[🛡️ SZLHOLDINGS on Hugging Face →](https://huggingface.co/SZLHOLDINGS)**   ·   **[a-11-oy.com →](https://a-11-oy.com)**   ·   **[SZL Atlas — estate map →](https://huggingface.co/spaces/SZLHOLDINGS/szl-command-lab)**

### Governed AI you can prove.

<sub>SLSA: L1 honest · L2 attested · L3 roadmap. Λ = Conjecture 1 (advisory, never a theorem). Trust ceiling 0.97 — never 100%. Labels honest by default: MEASURED / REPORTED / MODELED / HEURISTIC / UNKNOWN / UNAVAILABLE. locked-proven = exactly 8 {F1,F4,F7,F11,F12,F18,F19,F22}.</sub>

</div>

## Dataset-server loading boundary

The `attestations` config exposes only `extended-attestations.jsonl`. Repository configuration, schemas, provenance JSON, tests, and bundle manifests remain supporting artifacts and are excluded from row-schema inference. Structural loadability is not cryptographic signature or signer-identity verification.
