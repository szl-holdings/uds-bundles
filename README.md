> **Trademark notice.** SZL Holdings' use of "UDS" references Defense Unicorns' Unified Defense Stack (USPTO Serial 99831126). SZL Holdings is not affiliated with Defense Unicorns. SZL contributions to the UDS ecosystem are made through upstream PRs. See: https://defenseunicorns.com/uds

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

## Honest disclosure

- **SLSA L1 honest** — L2 in progress via build-service provenance (see SLSA L3 migration plan)
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
