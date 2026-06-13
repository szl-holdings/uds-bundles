> **Trademark notice.** SZL Holdings' use of "UDS" references Defense Unicorns' Unified Defense Stack (USPTO Serial 99831122). SZL Holdings is not affiliated with Defense Unicorns. SZL contributions to the UDS ecosystem are made through upstream PRs. See: https://defenseunicorns.com/uds

# uds-bundles

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Doctrine v11 LOCKED](https://img.shields.io/badge/Doctrine-v11_LOCKED-d4a444.svg)](https://github.com/szl-holdings/lutar-lean)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19944926.svg)](https://doi.org/10.5281/zenodo.19944926)
[![Λ Conjecture 1](https://img.shields.io/badge/Λ-Conjecture_1_(conditional_Theorem_U)-B79BD6.svg)](https://github.com/szl-holdings/lutar-lean/blob/main/BOUNTY.md)
[![SLSA](https://img.shields.io/badge/SLSA-L1_honest_%C2%B7_L2_build--attested_%C2%B7_L3_roadmap-c9b787.svg)](https://slsa.dev/spec/v1.0/levels)
[![Security Policy](https://img.shields.io/badge/Security-Policy-red.svg)](SECURITY.md)

**Airgap-deployable Zarf bundles for the SZL governed agentic mesh — built on Unified Defense Stack (UDS) Core v1.5.0.**

**Deployment story:** this repo holds the **Zarf bundle manifests**. The UDS Operator entry point is [szl-fleet-overlay](https://github.com/szl-holdings/szl-fleet-overlay); CRDT coordination is [szl-mesh](https://github.com/szl-holdings/szl-mesh); the observability spine is [uds-mesh](https://github.com/szl-holdings/uds-mesh); the live reference deployment is [szl-uds-deployment](https://github.com/szl-holdings/szl-uds-deployment).

---

## What this is

`uds-bundles` packages the SZL governed agentic mesh as Unified Defense Stack (UDS)-compatible Zarf bundles. The two products — **a11oy** (governed command platform) and **killinchu** (drones & vessels) — are composed from internal capability services (policy, immune-gate, memory, operator console), each shipped as its own Zarf package:

| Bundle | Product / capability | Role |
|--------|----------------------|------|
| `szl-a11oy` | a11oy — governance gate | Policy overlay + Λ-gate + agentic /code orchestrator |
| `szl-policy` | a11oy — **CHAPAQ** egress immune-inspector (policy gate) *(roadmap role, surfaces in a11oy)* | 8-gate fail-CLOSED verdict pipeline |
| `szl-provenance` | a11oy — **Provenance Anchor** (YAWAR receipt bus / receipt memory) *(roadmap role, surfaces in a11oy)* | Khipu Merkle DAG + DSSE-signed receipt chain |
| `szl-operator` | a11oy — operator console *(roadmap role, surfaces in a11oy)* | Human-on-the-loop decision approval gates (full 10-view operator app) |
| `szl-killinchu` | killinchu — counter-UAS | Λ-gate defensive application (ADS-B + MAVLink) |
| `szl-sda` | **killinchu SDA / Domain Awareness** — clean-room anomaly/SDA capability | DTID → CHARACTERIZE → TWA → FUSE; signed DSSE receipt per detection (`sda.detection.*` mesh spans) |

> **New in `uds-v0.4.0`:** the `szl-sda` bundle adds an air-gap-deployable, clean-room
> anomaly / Space-Domain-Awareness capability (engine image `ghcr.io/szl-holdings/khipu-sda-core`).
> Attribution: inspired by the publicly described 4-function SDA framing of True Anomaly's
> "Mosaic" ([trueanomaly.space/mosaic](https://www.trueanomaly.space/mosaic)); SZL's
> implementation is a clean-room build from permissively licensed lineage (PyOD/PyGOD BSD-2,
> Merlion BSD-3, TODS Apache-2.0, tsod/GDN/GraGOD MIT, python-sgp4 MIT). SZL Holdings is
> **not affiliated** with True Anomaly. The image is cosign-sign-ready; its digest is left
> blank until the founder-gated Forge build signs `uds-v0.4.0` (FA-001) — no signature or
> digest is fabricated.

Each bundle ships: `uds-bundle.yaml` · `zarf.yaml` · Helm chart · Pepr policies + ValidatingAdmissionPolicy + Cilium NetworkPolicy · SPDX + CycloneDX SBOMs · SLSA v1.2 provenance · `serviceMesh.mode: ambient`.

Three K8s-native CRDs in `crds/`: **LambdaGate** · **KhipuReceipt** · **DoctrineLock**.

> **Naming note.** Only **two products ship** as standalone signed images — **a11oy** and
> **killinchu**. The other mesh capabilities are **roadmap roles** that surface *inside* a11oy:
> the **CHAPAQ** egress immune-inspector (Policy), the **Provenance Anchor** (receipt memory /
> YAWAR receipt bus), and the **Operator** console. They are not separately-branded live products.

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

### One-command install (public mesh bundle)

The composed 5-organ mesh bundle is **published, cosign-signed, and publicly
(anonymously) pullable** — no GHCR login is needed to pull the bundle artifact:

```bash
# Pull the signed bundle artifact (anonymous — no GHCR auth required)
uds pull oci://ghcr.io/szl-holdings/szl-uds-bundle:uds-v0.2.0

# …or deploy it straight from the registry onto a running UDS Core cluster
uds deploy oci://ghcr.io/szl-holdings/szl-uds-bundle:uds-v0.2.0 --confirm
```

> **Honest scope.** Only the **bundle artifact** is anonymously pullable. The
> deploy step still pulls **UDS Core** from `registry.defenseunicorns.com`, which
> requires a **free** Defense Unicorns registry account (HTTP Basic — not
> anonymous). The bundle ships the two products **published + signed +
> individually deployable** — NOT "all five organs boot together" (cross-organ
> in-cluster mesh is roadmap). Bundle-level SLSA provenance attestation is not yet
> published.

### Deploy a single bundle

```bash
git clone https://github.com/szl-holdings/uds-bundles
cd uds-bundles

# Build a Zarf package locally (requires Docker)
zarf package create bundles/szl-killinchu/ --confirm

# Deploy to a running UDS Core cluster
zarf package deploy zarf-package-szl-killinchu-amd64-0.2.0.tar.zst --confirm
```

See `bundles/DEPLOY_RUNBOOK.md` for Scenario A (single capability bundle), B (policy + memory), C (full mesh).

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

## Per-bundle provenance matrix (SLSA L1 honest — L2 verified-provenance on roadmap)

Each capability image is referenced in this bundle by **immutable digest** (not a floating tag).
**Honest doctrine:** The two shipping product images are **SLSA Build L1 (honest)** — cosign
keyless-signed (Fulcio + Rekor) and verifiable via `cosign verify`. **SLSA L2 verified
build-provenance (isolated builders + verified provenance attestation) is on the roadmap.**
**L3 is NOT claimed** (no FedRAMP, Iron Bank, or CMMC).

| Bundle | Image (digest-pinned) | Build provenance | Rekor entry |
|-------|------------------------|-----------------|-------------|
| `szl-a11oy` | `ghcr.io/szl-holdings/a11oy@sha256:8aaea251609104b554baaac161a0e44cb59a909296e0b37d25ba94b3ab921530` | cosign keyless + `slsa.dev/provenance/v1` DSSE | logIndex **1710578865** |
| `szl-killinchu` | `ghcr.io/szl-holdings/killinchu@sha256:e872344f2fc8e7d8085042d5b5660c8bd62887a7d2f2353f44f882d782e8cd75` | cosign keyless + DSSE | `bundles/szl-killinchu/attestations/killinchu.slsa-provenance.json` |

The roadmap-role capability packages (Policy / Provenance Anchor / Operator) surface inside a11oy and are not listed as separately-branded published products.

The published mesh bundle artifact is `oci://ghcr.io/szl-holdings/szl-uds-bundle:uds-v0.2.0`. **Honest scope:** the two shipping product images are SLSA Build **L1 honest** (cosign keyless-signed, Rekor-anchored); SLSA **L2 verified build-provenance is on the roadmap** for the images and the bundle alike. Bundle-level attestation is not yet published (blocked on an owner-only GHCR `szl-uds-bundle` package-write grant). Do not claim the bundle is L2-attested until `cosign verify-attestation` returns a provenance payload for the bundle.

## Honest disclosure

- **Capability images: SLSA Build L1 (honest).** The shipping product images are cosign
  keyless-signed (Fulcio + Rekor) and verifiable via `cosign verify`. **SLSA L2 verified
  build-provenance is on the roadmap** (isolated builders + verified provenance attestation).
  **L3 is NOT claimed anywhere** (doctrine: no FedRAMP, Iron Bank, or CMMC).
- **Bundle artifact: signed, NOT yet provenance-attested.** The mesh bundle `szl-uds-bundle:uds-v0.2.0` is real and deployable, but the **bundle artifact itself is not yet SLSA-attested** (owner-only GHCR package-write grant pending).
- **Λ = Conjecture 1**, NOT a theorem — Lake Verifier testing the proof; 163 sorries open
- **Proved PURIQ formulas = 8** — F1, F4, F7, F11, F12, F18, F19, F22 (Lean 4, zero-sorry; the no-axiom theorem `locked_count_eight`); the remaining formulas are Roadmap
- **Section 889** = exactly 5 banned vendors: Huawei, ZTE, Hytera, Hikvision, Dahua
- **`uds-v0.2.0` is the published, signed mesh bundle** — the per-capability Zarf source packages under `bundles/szl-<name>/` can also be built locally with `zarf package create bundles/szl-<name>/`.
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

**Doctrine v11 LOCKED · locked kernel 749/14/163 @ c7c0ba17 (8 proven) · experimental main 1304/22 @ 7885fd9 (~36 theorems CI-green, never folded into the locked eight) · Λ = Conjecture 1 (NOT a theorem) · Khipu Conjecture 2 open · Apache-2.0**


