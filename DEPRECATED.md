# Codename Deprecation & Honest-Role Mapping

> Status: the internal codenames below are **deprecated as public/product names**. They survive only as
> the *signed, immutable identity* of already-published, cosign-signed + Rekor-attested OCI artifacts, which
> must stay byte-stable so existing signatures, SLSA attestations, and governance receipts remain verifiable
> forever. New work uses the honest role names. See `bundles/v0.1.0/CODENAME_HONEST_ROLES.md` for the full map.

## Honest role mapping (canonical, public-facing)

| Deprecated internal codename | Honest role name (public) | What it is |
|------------------------------|---------------------------|------------|
| `amaru`  | **Provenance Anchor** | Ledger/transparency anchoring + post-quantum-hardened provenance (roadmap capability) |
| `rosie`  | **Operator**          | Receipt orchestration / fleet proof-routing control plane (roadmap capability) |
| `sentra` | **Policy**            | Policy/drift observability gate (roadmap capability) |

Shipping products today are exactly two: **a11oy** (governed execution fabric) and **killinchu**
(counter-UAS C2). The roles above are roadmap, named as ambition, not achievement.

## Why these aren't renamed in place

The published images `ghcr.io/szl-holdings/{amaru,rosie,sentra}:uds-v0.2.0` carry **live cosign `.sig`
signatures + SLSA build-provenance `.att` attestations**, and their digests are pinned into the signed
Zarf packages, bundle manifests, and `ClusterImagePolicy`. Blind-renaming the paths would desync each
artifact from its signature / Rekor transparency-log entry — a provenance break that is strictly worse than
the deprecated codename. Renaming is therefore done **forward**, by cutting a new signed version.

## Roadmap: the honest-named release (`uds-v0.3.0`)

A future signing-capable release builds `ghcr.io/szl-holdings/{provenance-anchor,operator,policy}:uds-v0.3.0`,
cosign-signs + `attest --type slsaprovenance` them (keyless Fulcio/Rekor), re-authors all coupled
charts/manifests/CRs under the honest names, re-signs the Zarf packages with a fresh `SHA256SUMS.txt`, and
**deprecates v0.1.0/v0.2.0 immutably** (kept published so all existing signatures/attestations/receipts stay
verifiable). The a11oy `infra/` + `organs/` vendored mirrors migrate in the same window to preserve
GitHub↔HF byte-identical parity.

Honest supply-chain posture: **SLSA L1+L2 attested** where `actions/attest-build-provenance` runs and
`cosign verify-attestation` / `gh attestation verify` succeed; **SLSA L3 is roadmap**. Not Iron Bank,
not FedRAMP, not CMMC, not a real ATO — ATO-aligned roadmap only. Not affiliated with Defense Unicorns
(USPTO Serial 99831122); UDS / Zarf / Pepr patterns referenced as the open FOSS stack they are.

_© 2026 Lutar, Stephen P. — SZL Holdings · ORCID 0009-0001-0110-4173_
