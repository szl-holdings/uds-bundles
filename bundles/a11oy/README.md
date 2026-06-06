# a11oy.uds — SZL Command Platform Bundle

**UDSBundle name:** `a11oy` · **version:** `0.5.0` · **arch:** `amd64`

This is one of the two canonical SZL UDS bundles (the other is `killinchu.uds`). It ingests the a11oy command platform and everything it needs to run as the orchestrating brain into a single, air-gap-deployable UDS bundle.

## What it composes
- **a11oy** — the command platform / front door (26-tab console, orchestration; ingested organ source + knowledge/doctrine baked into the image)
- **sentra** — policy / immune backend a11oy depends on
- **amaru** — reasoning / memory-cortex backend a11oy depends on
- **rosie** — operator console backend a11oy depends on
- **mesh interconnect** — Istio AuthorizationPolicy + NetworkPolicy + strict PeerAuthentication, carried inside each per-organ Zarf package as its UDS Package CR. The UDS Operator reconciles the cross-organ allow/expose matrix at deploy time.

It reuses the verified per-organ Zarf packages under `bundles/szl-<organ>/` via relative `path:` references — the same packages the published `szl-mesh:0.4.0` uses.

## Image pins — verified pullable (anonymous GHCR token + manifest HEAD, 2026-06-05)
| Image | Tag | HTTP |
|-------|-----|------|
| `ghcr.io/szl-holdings/a11oy` | `uds-v0.2.0` | 200 |
| `ghcr.io/szl-holdings/sentra` | `uds-v0.2.0` | 200 |
| `ghcr.io/szl-holdings/amaru` | `uds-v0.2.0` | 200 |
| `ghcr.io/szl-holdings/rosie` | `uds-v0.2.0` | 200 |

**Roadmap prerequisites (image not yet public — listed as TODO in `uds-bundle.yaml`, never fake-pinned):** `vsp-otel` (OTEL), `hatun-mcp` (MCP; image public but no Zarf package vendored yet), `szl-lake` / `szl-receipts-server` (receipts/lake).

## Build + deploy
```bash
# Build (CI: Canonical UDS Bundles workflow, bundle=a11oy):
uds create bundles/a11oy --confirm

# Deploy (once published — see PUBLISH STATUS):
uds deploy oci://ghcr.io/szl-holdings/a11oy-bundle:0.5.0 --confirm
```

## PUBLISH STATUS — HONEST
**AUTHORED-ONLY. NOT yet published.** Build via the `Canonical UDS Bundles` workflow. The publish path is `ghcr.io/szl-holdings/a11oy-bundle` (the `a11oy` repo already holds the organ IMAGE; `-bundle` avoids collision). Do not claim it is published/signed until verified on GHCR. Only `szl-mesh:0.4.0` is verified published today.

## Honesty
Doctrine v11 LOCKED 749/14/163 @ `c7c0ba17` · Λ = Conjecture 1 (never a theorem) · SLSA **L2 on organ images** (`.att` provenance); **no bundle-level SLSA attestation** (cosign signature is the bundle provenance) · **No L3 / FedRAMP / CMMC / Iron Bank** · Section 889 = 5 vendors.

Signed-off-by: Stephen P. Lutar Jr. \<stephenlutar2@gmail.com\>
