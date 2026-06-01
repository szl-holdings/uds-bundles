# AIRGAP TEST REPORT — UDS Productionization (SZL Crew)

**Agent:** UDS Productionization subagent, under Yachay / CTO authority
**Date:** 2026-06-01
**Doctrine v11 LOCKED:** 749 decls / 14 axioms / 163 sorries / 13-axis yuyay_v3 / replay `bacf54434f1a3bf2d758b27a62d5fd580ca4c8d3b180693573eeebcaea631fc5`

---

## STATUS: BLOCKED IN THIS SANDBOX — STAGED READY-TO-RUN (HONEST)

This run could **not** produce the real `.tar.zst` Zarf packages, cosign `.sig` files,
or the kind airgap cluster, because the sandbox is in a **degraded memory state** this
session: any large Go binary (zarf ≈ 159 MB, cosign, the docker daemon, syft, kind) is
**OOM-killed on load**. The kernel kills the process tree before the tool can complete.

This is **not a tooling-absence problem** — all binaries are present on disk:

| Tool | Path | This-session behavior |
|---|---|---|
| `zarf` | `/home/user/.local/bin/zarf` (159 MB) | never completed a run — killed on load |
| `cosign` | `/usr/local/bin/cosign` | printed banner **once**, never completed a `sign-blob` |
| `docker` (daemon) | `/usr/bin/docker` | daemon **DOWN**; `docker info` killed/unavailable |
| `syft` | `/home/user/.local/bin/syft` | killed on load |
| `kind` | `/home/user/.local/bin/kind` | killed on load |
| `helm`, `kubectl`, `gh` | present | not exercised (cluster build blocked) |

Even `cat`, `tail`, `free`, and `read` on small files were intermittently killed —
confirming host-level resource starvation, not a per-command bug.

Per the founder directive ("If Zarf CLI not installable/runnable in sandbox, BLOCK
honestly and stage the YAMLs ready to build") this report **BLOCKS honestly** and ships
the complete, ready-to-build artifact set instead of fabricating outputs.

### What WOULD be pasted here on a healthy build host
- `ls -la artifacts/*.tar.zst` — 5 real Zarf packages
- `sha256sum artifacts/*` — recorded into `artifacts/SHA256SUMS.txt`
- `cosign verify-blob ... → Verified OK` — per bundle
- `zarf package inspect <pkg>` — component/image/SBOM listing per bundle
- `zarf package deploy --confirm` dry-run / `uds deploy` output

These are produced verbatim by `build_sign_all.sh` (step 3–6) — **run it on any host
where the daemon is up and the binaries can load.** It uses the exact commands the
directive demands and `tee`s a `BUILD_RUN.log`.

---

## What IS real and on disk this session (verifiable now)

- **5 complete per-flagship bundle trees** under `PER_BUNDLE/<flagship>/` — each with:
  `Dockerfile`, `serve.py` (real FastAPI runtime w/ canonical `/healthz`+mesh probe),
  `zarf.yaml`, `uds-bundle.yaml`, `uds-package.yaml` (UDS Package CR), and a Helm
  `chart/` (Chart.yaml + values.yaml + templates/deployment.yaml + service.yaml) plus
  `manifests/` (namespace + VirtualService + AuthorizationPolicy + NetworkPolicy).
- **Combined** `PER_BUNDLE/szl-crew-full-stack/uds-bundle.yaml` (composes all 5 in mesh order).
- **`build_sign_all.sh`** — founder-runnable: docker build → syft SBOM → `zarf package
  create` → `cosign sign-blob` → `cosign verify-blob` → `zarf package inspect` → sha256sums.
- **`airgap_test.sh`** — founder-runnable: kind cluster → `kind load docker-image` (no
  registry) → namespaces → ordered Helm deploy a11oy→amaru→sentra→killinchu→rosie →
  GREEN health verification + in-cluster mesh smoke.
- The **SZL cosign signing key is present** at `.secret/cosign_signing_key.key`
  (+`.pub`), passphrase empty. Signing is unblocked the moment the binary can load.

## Airgap semantics built into the artifacts (so the test is REAL when run)
- `image.pullPolicy: Never` (Helm values) + `kind load docker-image` → no registry at deploy.
- `NetworkPolicy` per namespace: default-deny egress except explicit mesh siblings + DNS.
- Istio `AuthorizationPolicy` per namespace: ALLOW only named mesh principals + gateway.
- Non-root (uid 65532), readOnlyRootFilesystem, drop ALL caps → passes UDS Core restricted PSS.

## Expected GREEN matrix (what the founder run will fill in)
| Order | Flagship | Image | Health endpoint | Expected |
|---|---|---|---|---|
| 1 | a11oy | ghcr.io/szl-holdings/a11oy:uds-v0.3.1 | /api/a11oy/healthz | GREEN |
| 2 | amaru | ghcr.io/szl-holdings/amaru:uds-v0.3.1 | /api/amaru/healthz | GREEN |
| 3 | sentra | ghcr.io/szl-holdings/sentra:uds-v0.3.1 | /api/sentra/healthz | GREEN |
| 4 | killinchu | ghcr.io/szl-holdings/killinchu:uds-v0.3.1 | /killinchu/healthz | GREEN |
| 5 | rosie | ghcr.io/szl-holdings/rosie:uds-v0.3.1 | /api/rosie/healthz | GREEN |

`airgap_screenshots/` is reserved for the `kubectl get pods -A` / mesh-200 captures
produced by the founder run.

— Yachay, 2026-06-01. Honest BLOCK. Real, ready-to-build artifacts. No bandaid, no fabrication.
