# Architecture — uds-bundles

> Doctrine v11 LOCKED `749/14/163` · Kernel commit `c7c0ba17` · Λ = **Conjecture 1**
> (conditional Theorem U) · SLSA L1 · L2-attested (images) · L3 roadmap; bundle-level L2 NOT earned.

> **Trademark notice.** SZL's use of "UDS" references Defense Unicorns' Unified Defense
> Stack (USPTO Serial 99831122). SZL Holdings is **not affiliated** with Defense
> Unicorns. SZL contributions to the UDS ecosystem are made through upstream PRs.

`uds-bundles` packages the SZL governed agentic mesh as Unified Defense Stack
(UDS)-compatible **Zarf bundles** — airgap-deployable and cosign-sign-ready.

## Where this sits in the deployment chain

```
uds-bundles            ← bundle manifests (THIS repo)
szl-fleet-overlay      ← UDS Operator packages (entry point)
szl-mesh               ← CRDT coordination layer
uds-mesh               ← observability spine (DSSE governance spans)
szl-uds-deployment     ← live reference air-gap deployment (k3d + uds-cli + Pepr)
```

## Repository layout

```
uds-bundles/
├── uds-bundle.yaml             Top-level UDS bundle manifest.
├── bundles/                    Per-product / per-capability Zarf packages.
├── charts/                     Helm charts shipped inside each bundle.
├── crds/                       K8s CRDs: LambdaGate · KhipuReceipt · DoctrineLock.
├── mesh/                       Mesh / peat-node manifests.
├── bigbang/                    Big Bang integration assets.
├── releases/                   Released bundle artifacts (.zst, .sig).
├── scripts/, tower_bootstrap.sh  Build + tower-bootstrap automation.
├── test/                       Bundle/airgap self-tests.
└── VERSION                     Canonical uds-v* version string.
```

## Bundle set

Only **two products ship** as standalone signed images — **a11oy** (governed command
platform) and **killinchu** (drones & vessels). They are composed from internal
capability packages: `szl-policy` (8-gate fail-CLOSED immune inspector), `szl-provenance`
(Khipu Merkle DAG + DSSE receipt chain), `szl-operator` (human-on-the-loop console),
and `szl-sda` (clean-room anomaly / Space-Domain-Awareness, image
`ghcr.io/szl-holdings/khipu-sda-core`).

Each bundle ships: `uds-bundle.yaml` · `zarf.yaml` · Helm chart · Pepr policies +
ValidatingAdmissionPolicy + Cilium NetworkPolicy · SPDX + CycloneDX SBOMs · SLSA v1.2
provenance · `serviceMesh.mode: ambient`.

## Signing & provenance honesty

Bundles are **cosign-sign-ready**. Image digests are left blank until the founder-gated
Forge build signs the release — no signature or digest is ever fabricated. SLSA is
claimed at **L1 · L2-attested for images · L3 roadmap; bundle-level L2 is NOT earned** (the bundle artifact carries only post-publish provenance), never L3.

## CI gates (required on `main`)

`DCO` · `Scorecard analysis workflow`. Build/deploy proof, gitleaks, SBOM, Trivy/Grype,
pin-check, and version-doctrine guards also run.

DOI [10.5281/zenodo.19944926](https://doi.org/10.5281/zenodo.19944926).

---

© 2026 Lutar, Stephen P. — SZL Holdings · Apache-2.0
