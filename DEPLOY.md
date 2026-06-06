# SZL UDS Deploy Guide

**Canonical bundles (going forward):** `a11oy:0.5.0` (command platform) and `killinchu:0.5.0` (field node).
**Still-working full-mesh bundle:** `szl-mesh:0.4.0` (published + cosign-signed; NOT changed).
**Repo:** `szl-holdings/uds-bundles`
**Updated:** 2026-06-05
**Doctrine:** v11 LOCKED 749/14/163 @ kernel `c7c0ba17` · Λ = Conjecture 1 · SLSA **L2 on organ images** (`.att` = `slsa.dev/provenance/v0.2`, cosign-verifiable); **bundle-level build-provenance attestation NOT earned** — the cosign **signature** is the bundle provenance. **No L3 / FedRAMP / CMMC / Iron Bank.** Section 889 = 5 vendors.
**Signed-off-by:** Stephen P. Lutar Jr. \<stephenlutar2@gmail.com\>

---

## The Two Canonical Bundles (INGEST model)

The fleet consolidated onto **two self-contained UDS bundles**. Each ingests everything it needs into one air-gap-deployable artifact.

| Bundle | Name / version | What it is | Composes |
|--------|----------------|-----------|----------|
| **a11oy.uds** | `a11oy` 0.5.0 | The command platform / orchestrating brain + its backend organs + mesh interconnect | a11oy + sentra + amaru + rosie (+ mesh CRs; OTEL/MCP/receipts roadmap) |
| **killinchu.uds** | `killinchu` 0.5.0 | Self-contained field node (drones + vessels) with inherited a11oy orchestration + governance prerequisites | killinchu + sentra + amaru (+ mesh CRs; rosie optional; OTEL/receipts roadmap) |

The **mesh interconnect** (Istio AuthorizationPolicy + NetworkPolicy + strict PeerAuthentication) is not a separate package — it ships inside each per-organ Zarf package as its **UDS Package CR** (`manifests/uds-package.yaml`). The UDS Operator reconciles the cross-organ allow/expose matrix at deploy time, so the mesh wiring deploys with the bundle. Governance span schemas live in `szl-holdings/uds-mesh` + `uds-bundles/mesh/schemas/spans/*.yaml`.

---

## ⚠️ PUBLISH STATUS — READ THIS (honest)

| OCI ref | Status |
|---------|--------|
| `oci://ghcr.io/szl-holdings/szl-mesh:0.4.0` | **PUBLISHED + cosign-SIGNED** (verified on GHCR: tags `0.4.0`/`v0.4.0`/`latest` + 3 `.sig`). |
| `oci://ghcr.io/szl-holdings/a11oy-bundle:0.5.0` | **AUTHORED-ONLY — NOT yet published.** Build via the `uds-bundle-publish` workflow (a11oy target). |
| `oci://ghcr.io/szl-holdings/killinchu-bundle:0.5.0` | **AUTHORED-ONLY — NOT yet published.** Build via the `uds-bundle-publish` workflow (killinchu target). |

> **Why `-bundle` suffix?** `ghcr.io/szl-holdings/a11oy` and `.../killinchu` already hold the organ **IMAGES** (verified pullable at `:uds-v0.2.0`). A UDSBundle pushed to the same repo path would collide image-vs-bundle, so the bundles publish to `a11oy-bundle` / `killinchu-bundle`. The CEO-facing deploy commands below use the conceptual names; the actual published OCI path is the `-bundle` repo. Do **not** claim `a11oy:0.5.0` is published — only `szl-mesh:0.4.0` is verified published today.

---

## Deploy Commands

### Platform — a11oy.uds
```bash
# CANONICAL (once built + published via the workflow):
uds deploy oci://ghcr.io/szl-holdings/a11oy-bundle:0.5.0 --confirm
# USB / air-gap tarball (after `uds create bundles/a11oy`):
uds-cli bundle deploy uds-bundle-a11oy-amd64-0.5.0.tar.zst --confirm
```

### Field — killinchu.uds
```bash
# CANONICAL (once built + published via the workflow):
uds deploy oci://ghcr.io/szl-holdings/killinchu-bundle:0.5.0 --confirm
# USB / air-gap tarball (after `uds create bundles/killinchu`):
uds-cli bundle deploy uds-bundle-killinchu-amd64-0.5.0.tar.zst --confirm
```

### Full 5-organ mesh — szl-mesh (PUBLISHED, still works)
```bash
uds deploy oci://ghcr.io/szl-holdings/szl-mesh:0.4.0 --confirm
```

---

## GHCR Image Verification (anonymous token + manifest HEAD, 2026-06-05)

All organ images pinned by the bundles are **verified pullable** (HTTP 200):

| Image | Tag | HTTP | Digest |
|-------|-----|------|--------|
| `ghcr.io/szl-holdings/a11oy` | `uds-v0.2.0` | 200 | `sha256:45fa2365…f276f0b` |
| `ghcr.io/szl-holdings/sentra` | `uds-v0.2.0` | 200 | `sha256:60a0efc1…05ac3639` |
| `ghcr.io/szl-holdings/amaru` | `uds-v0.2.0` | 200 | `sha256:53301e26…52b289ff` |
| `ghcr.io/szl-holdings/rosie` | `uds-v0.2.0` | 200 | `sha256:1984a15f…43302848` |
| `ghcr.io/szl-holdings/killinchu` | `uds-v0.2.0` | 200 | `sha256:e0fb6c3a…5f29ca548` |
| `ghcr.io/szl-holdings/hatun-mcp` | `latest` | 200 | `sha256:fba23f0e…aab0feb8f247` |

**Roadmap prerequisites — NOT yet anonymously pullable (HTTP 403; listed as TODO, never fake-pinned):**
`vsp-otel` (OTEL), `szl-lake`, `szl-receipts-server`, `vessels`, `khipu-consensus`. Add the Zarf package + uncomment the bundle entry once the image is public + verified.

---

## Verify Signatures / Provenance

```bash
# Bundle signature — szl-mesh is cosign-SIGNED (PASSES today):
cosign verify ghcr.io/szl-holdings/szl-mesh:0.4.0 \
  --certificate-identity-regexp="^https://github.com/szl-holdings/" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Organ-image SLSA L2 provenance attestation (.att):
cosign verify-attestation --type slsaprovenance \
  ghcr.io/szl-holdings/a11oy:uds-v0.2.0 \
  --certificate-identity-regexp='^https://github.com/szl-holdings/' \
  --certificate-oidc-issuer='https://token.actions.githubusercontent.com'
```

> **Honest provenance statement.** Organ images carry SLSA **L2** `.att` provenance (verified). The **bundle** carries a cosign **signature** only — the GitHub `attest-build-provenance` step does **NOT** succeed on the bundle (CI token lacks `attestations: write`), so there is **no bundle-level SLSA attestation**. The cosign signature is the real bundle provenance. **L3 is not claimed.** Once `a11oy-bundle:0.5.0` / `killinchu-bundle:0.5.0` are published, re-run the `cosign verify` above against those refs to confirm their signatures.

---

## Prerequisites & Verify-After-Deploy

Same as the full mesh: an existing **UDS Core v1.x** cluster (Istio + Pepr UDS Operator + Keycloak + Prometheus), `uds-cli v0.32.0` (bundles Zarf v0.77.0), and `kubectl`. After deploy, check namespaces, wait for `Available` deployments, confirm UDS `packages` reconciled, and port-forward `/healthz`:

```bash
kubectl get packages -A | grep szl-
kubectl port-forward -n szl-a11oy svc/a11oy 8080:8080 &
curl -sf http://localhost:8080/api/a11oy/healthz && echo "a11oy OK"; kill %1
```

---

## Honesty Doctrine
- Organ images = SLSA **L2** (`.att` provenance verifies via `cosign verify-attestation`). Bundle = cosign-**signed** only; **no bundle-level SLSA attestation** (token lacks `attestations: write`). **L3 NOT claimed.**
- `a11oy-bundle:0.5.0` and `killinchu-bundle:0.5.0` are **authored-only** until built/published + verified on GHCR. Only `szl-mesh:0.4.0` is verified published today.
- Λ = **Conjecture 1** (NEVER a theorem). 163 sorries open in the locked kernel (disclosed).
- **No Iron Bank, No FedRAMP, No CMMC.** Section 889 = exactly 5 vendors (Huawei, ZTE, Hytera, Hikvision, Dahua).
