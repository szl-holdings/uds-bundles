# killinchu.uds — SZL Field Node Bundle (drones + vessels)

**UDSBundle name:** `killinchu` · **version:** `0.5.0` · **arch:** `amd64`

One of the two canonical SZL UDS bundles (the other is `a11oy.uds`). It makes the killinchu field surface self-contained and deployable on its own at the edge / Navy: the killinchu image plus the governance-brain prerequisites it inherited from a11oy.

## What it composes
- **killinchu** — counter-UAS (ADS-B/MAVLink/OpenDroneID) + vessels + the inherited a11oy orchestration/console. Carries a **real cosign signing key in-image**, so edge DSSE receipts are genuinely signed offline.
- **sentra** — policy / immune backend (interdiction screening at the edge)
- **amaru** — reasoning / 13-axis Λ-gate memory (threat scoring)
- **rosie** — OPTIONAL at a field node (killinchu's inherited operator views cover the field case; uncomment in `uds-bundle.yaml` to add a standalone console)
- **mesh interconnect** — ships inside each per-organ Zarf package as its UDS Package CR; the UDS Operator reconciles the field allow/expose matrix at deploy time.

## Image pins — verified pullable (anonymous GHCR token + manifest HEAD, 2026-06-05)
| Image | Tag | HTTP |
|-------|-----|------|
| `ghcr.io/szl-holdings/killinchu` | `uds-v0.2.0` | 200 |
| `ghcr.io/szl-holdings/sentra` | `uds-v0.2.0` | 200 |
| `ghcr.io/szl-holdings/amaru` | `uds-v0.2.0` | 200 |

**Roadmap prerequisites (image not yet public — TODO, never fake-pinned):** `vsp-otel` (OTEL), `szl-receipts-server`, `szl-lake`. killinchu signs receipts locally regardless; a central receipts sink is additive.

## Build + deploy
```bash
uds create bundles/killinchu --confirm
uds deploy oci://ghcr.io/szl-holdings/killinchu-bundle:0.5.0 --confirm
```

## PUBLISH STATUS — HONEST
**AUTHORED-ONLY. NOT yet published.** Build via the `Canonical UDS Bundles` workflow (bundle=killinchu). Publish path `ghcr.io/szl-holdings/killinchu-bundle` (the `killinchu` repo already holds the organ IMAGE). Do not claim published/signed until verified on GHCR.

## Honesty
Doctrine v11 LOCKED 749/14/163 @ `c7c0ba17` · Λ = Conjecture 1 · SLSA **L2 on organ images**, cosign-verified (killinchu `.att` = genuine SLSA provenance) · **no bundle-level SLSA attestation** (cosign signature is the provenance) · **Not Iron Bank / FedRAMP / CMMC / L3** · Section 889 = 5 vendors.

Signed-off-by: Stephen P. Lutar Jr. \<stephenlutar2@gmail.com\>
