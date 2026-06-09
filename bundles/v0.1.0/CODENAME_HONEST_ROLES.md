# Honest role mapping for signed UDS artifacts (display-name disclosure)

**SPDX-License-Identifier: Apache-2.0 · Copyright 2026 SZL Holdings**

This NOTES file is an **additive disclosure**. It does **not** alter any signed bytes.
The cosign-signed Zarf packages, their `.uds.sig` signatures, the `SHA256SUMS_PROOF.txt`
digests, and the published `ghcr.io/szl-holdings/{amaru,rosie,sentra}:uds-v0.2.0` OCI
image references (each carrying a cosign `.sig` and a SLSA `.att` attestation tag) are
**immutable provenance anchors**. The internal codenames in those signed filenames and
OCI repository paths are part of the signed-artifact identity: renaming them in place
would break `cosign verify` / `cosign verify-blob` and desync the digest proof chain.
They are therefore **retained as historical, verifiable identifiers** and are NOT
user-facing product names.

## Honest product roles (what each component actually is)

| Internal artifact identifier (signed — retained) | Honest role (user-facing name)         | What it does                                                              |
|--------------------------------------------------|----------------------------------------|---------------------------------------------------------------------------|
| `amaru` (image, package, chart, span namespace)  | **Provenance Anchor**                  | Convergent data-sync runtime; KL-drift-bounded replication + hash-chained proof receipts (the memory/provenance cortex). |
| `rosie` (image, package, chart, span namespace)  | **Operator**                           | Operator/replay control surface for governed actions.                     |
| `sentra` (image, package, chart, span namespace) | **Policy**                             | Policy / receipt-gate enforcement (the immune system).                    |

Quechua organ names (YUYAY / YAWAR / YACHAY / MUSQUY / AMARU-shell) are **not** banned and
may continue to appear as internal organ identifiers.

## Why the names persist in *signed* places only

- **Signed Zarf proof packages** `zarf-package-{amaru,rosie,sentra}-*-0.3.1.tar.zst`
  + `{amaru,rosie,sentra}-proof.uds.sig` — offline cosign `sign-blob` signatures
  (`--tlog-upload=false`), verified OK against `cosign_signing_key.pub`. The package
  **filename** is the signed subject and is referenced by name in `SHA256SUMS_PROOF.txt`.
- **Published OCI images** `ghcr.io/szl-holdings/{amaru,rosie,sentra}:uds-v0.2.0` —
  each has a cosign signature (`sha256-<digest>.sig`) and a SLSA provenance attestation
  (`sha256-<digest>.att`) published in GHCR. Their digests are locked into
  `zarf.yaml` (`image:` / `images:`), `uds-bundle.yaml` (`overrides`), and the
  `ClusterImagePolicy` image globs.

## Migration path to honest names (does not touch the v0.2.0 signed set)

Renaming is performed by **cutting a new versioned release** with honest names and
**re-signing**, never by editing the signed v0.2.0 bytes:

1. Build new images `ghcr.io/szl-holdings/{provenance-anchor,operator,policy}:uds-v0.3.0`.
2. `cosign sign` + `cosign attest --type slsaprovenance` the new images (keyed now,
   keyless Fulcio/Rekor on the v0.3.0 CI path — honest SLSA L1, L2 on roadmap, L3 never).
3. Re-author the bundles/charts/manifests under the honest directory names; rebuild and
   `cosign sign-blob` the new Zarf packages; publish a new `SHA256SUMS.txt`.
4. Mark v0.2.0 **deprecated but immutable** — keep it published so existing receipts and
   transparency records remain verifiable forever. Add a `DEPRECATED.md` pointer.

Until that coordinated, signing-capable release happens, every **user-visible** surface
(docs, site, dashboards, READMEs prose) uses the honest roles above; only the
**signed/immutable** identifiers retain the codename for verification integrity.
