> **Trademark notice.** SZL Holdings' use of "UDS" references Defense Unicorns' Unified Defense Stack (USPTO Serial 99831122). SZL Holdings is not affiliated with Defense Unicorns. SZL contributions to the UDS ecosystem are made through upstream PRs. See: https://defenseunicorns.com/uds

# uds-bundles

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Doctrine v11 LOCKED](https://img.shields.io/badge/Doctrine-v11_LOCKED-d4a444.svg)](https://github.com/szl-holdings/lutar-lean)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19944926.svg)](https://doi.org/10.5281/zenodo.19944926)
[![SLSA L1](https://img.shields.io/badge/SLSA-L1_honest-22c55e.svg)](https://slsa.dev/spec/v1.0/levels)
[![Security Policy](https://img.shields.io/badge/Security-Policy-red.svg)](SECURITY.md)

**Five airgap-deployable Zarf bundles for the SZL governed agentic mesh — built on Unified Defense Stack (UDS) Core v1.5.0.**

---

## What this is

`uds-bundles` packages the five SZL flagship organs as Unified Defense Stack (UDS)-compatible Zarf bundles:

| Bundle | Organ | Role |
|--------|-------|------|
| `szl-a11oy` | Governance gate | Policy overlay + Λ-gate + agentic /code orchestrator |
| `szl-sentra` | Immune system | 8-gate fail-CLOSED verdict pipeline |
| `szl-amaru` | Memory cortex | Khipu Merkle DAG + DSSE-signed receipt chain |
| `szl-rosie` | Operator console | Human-in-loop decision approval gates |
| `szl-killinchu` | Counter-UAS | Λ-gate defensive application (ADS-B + MAVLink) |

Each bundle ships: `uds-bundle.yaml` · `zarf.yaml` · Helm chart · Pepr policies + ValidatingAdmissionPolicy + Cilium NetworkPolicy · SPDX + CycloneDX SBOMs · SLSA v1.2 provenance · `serviceMesh.mode: ambient`.

Three K8s-native CRDs in `crds/`: **LambdaGate** · **KhipuReceipt** · **DoctrineLock**.

---

## How to use

### Prerequisites

```bash
# Install Zarf v0.77.0+
brew install zarf   # or: https://zarf.dev/install

# Install uds-cli
brew install defenseunicorns/tap/uds

# Running UDS Core v1.5.0 cluster required
```

### Deploy a single bundle

```bash
git clone https://github.com/szl-holdings/uds-bundles
cd uds-bundles

# Build the Zarf package locally (requires Docker)
zarf package create bundles/szl-sentra/ --confirm

# Deploy to a running UDS Core cluster
zarf package deploy zarf-package-szl-sentra-amd64-0.2.0.tar.zst --confirm
```

See `bundles/DEPLOY_RUNBOOK.md` for Scenario A (single organ), B (sentra + amaru), C (full mesh).

---

## How to verify

```bash
# Verify cosign signature (keyless)
cosign verify-blob   --certificate-identity "https://github.com/szl-holdings/uds-bundles/.github/workflows/zarf-bundle-build.yml@refs/tags/v0.2.0"   --certificate-oidc-issuer "https://token.actions.githubusercontent.com"   bundle.tar.zst

# Inspect SLSA provenance
cat bundles/szl-a11oy/attestations/a11oy.slsa-provenance.json

# Check Doctrine lock
kubectl get doctrinelock -n szl-a11oy
```

---

## Per-organ SLSA Build-level matrix (honest)

Each organ image is referenced in this bundle by **immutable digest** (not a floating tag). SLSA levels below are the **honestly verified** build levels for each organ — four organs are SLSA Build **L2** (hosted GitHub Actions builder + signed in-toto provenance, verifiable downstream); **killinchu is held at SLSA Build L1 (honest)** in this bundle and L2/L3 are explicitly NOT claimed for it here.

| Organ | Image (digest-pinned) | SLSA Build level (bundle) | Verification evidence |
|-------|------------------------|---------------------------|------------------------|
| `szl-a11oy` | `ghcr.io/szl-holdings/a11oy@sha256:8aaea251609104b554baaac161a0e44cb59a909296e0b37d25ba94b3ab921530` | **L2 — verified** | `slsa-verifier verify-image` / `gh attestation verify` against signed `slsa.dev/provenance/v1`; DSSE **VALID**; Rekor logIndex **1710578865** |
| `szl-sentra` | `ghcr.io/szl-holdings/sentra@sha256:32360746e0084ca0c7233bbca2709c1b1e907b6ffa91c166444d8aeb196fa002` | **L2 — verified** | DSSE **VALID**; Rekor logIndex **1710576247** |
| `szl-amaru` | `ghcr.io/szl-holdings/amaru@sha256:435ac605a21feaa9c273c6877232307e88f304f81b2248b73c6dcfa31d997993` | **L2 — verified** | DSSE **VALID**; Rekor logIndex **1712902861** |
| `szl-rosie` | `ghcr.io/szl-holdings/rosie@sha256:86429fd4a07e209c02004e0ddd5ec408a2587a720a7e91cf5fbe1fe88e188a01` | **L2 — verified** | DSSE **VALID**; Rekor logIndex **1710599687** |
| `szl-killinchu` | `ghcr.io/szl-holdings/killinchu@sha256:e872344f2fc8e7d8085042d5b5660c8bd62887a7d2f2353f44f882d782e8cd75` | **L1 — honest (L2/L3 NOT claimed)** | Build provenance generated (`slsa.dev/provenance/v1`); cosign image signature verifies; see `bundles/szl-killinchu/attestations/killinchu.slsa-provenance.json` (`slsaLevel: "SLSA Build L1 (honest)"`). The bundle deliberately does **not** propagate any higher-level claim for killinchu. |

**slsa-verifier exit-code convention:** `slsa-verifier verify-image` returns **exit 0 = PASSED: verified SLSA provenance**; non-zero = FAILED. The four L2 organs verify to exit 0 against their published digests (DSSE VALID, Rekor entries above). For killinchu the honest claim is L1 only — a `verify-image` L2 assertion is intentionally **not** made in this bundle.

The bundle artifact `oci://ghcr.io/szl-holdings/szl-uds-bundle:uds-v0.2.1` is itself **cosign keyless-signed (OIDC, SLSA L1 honest)** — Rekor logIndex **1713162450** (`uds-v0.2.1`), **1713160435** (`0.2.0`), **1713166045** (`latest`).

## Honest disclosure

- **Bundle SLSA L1 honest** — the bundle artifact ships keyless-signed build provenance; four organ images are independently SLSA **L2** (see matrix above); **killinchu is L1 honest** in this bundle. L3 is NOT claimed anywhere (doctrine: L3 is banned).
- **Λ = Conjecture 1**, NOT a theorem — Lake Verifier testing the proof now; 163 sorries open
- **Section 889** = exactly 5 banned vendors: Huawei, ZTE, Hytera, Hikvision, Dahua
- **v0.2.0 is a source-only release** — run `zarf package create bundles/szl-<flagship>/` locally to build deployable `.tar.zst`; v0.3.0 targets signed packages via CI
- No Iron Bank, no FedRAMP, no CMMC — deploy on YOUR operational hardware

---

## Compatibility

| Component | Version |
|-----------|---------|
| UDS Core | v1.5.0 |
| Zarf | ≥ v0.77.0 |
| Kubernetes | v1.35+ (tested on v1.36.1) |
| cosign | v3.0.6 (GHSA-w6c6-c85g-mmv6 patched) |

---

**Doctrine v11 LOCKED 749/14/163 · Λ = Conjecture 1 (NOT a theorem) · Apache-2.0**

*Signed-off-by: Yachay <yachay@szlholdings.ai>*

