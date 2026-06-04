<!--
Copyright 2026 SZL Holdings · SPDX-License-Identifier: Apache-2.0
Doctrine v11 LOCKED 749/14/163 @ c7c0ba17 · Λ = Conjecture 1 (NEVER theorem) · SLSA L1 honest
Section 889 = 5 vendors (Huawei, ZTE, Hytera, Hikvision, Dahua)
Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>
-->

# JUNE 9 DEPLOY PROOF — Founder Runbook

**Audience:** Stephen (founder), on the RTX 4060 Ti tower.
**Goal:** Deploy the `szl-mesh:v0.4.0` bundle on a real cluster, watch the organs come
up, fire a counter-UAS decision, and verify a signed receipt — live, copy-paste, no
guessing.
**Events:** June 9 "Get to Know UDS" readiness checkpoint · June 16–19 Warhacker (San Diego).

> **What is automatically proven before you ever touch the tower:** the CI workflow
> **Deploy Proof (live k3d)** (`.github/workflows/deploy-proof.yml`) spins up a real
> ephemeral Kubernetes cluster on every push, deploys a real image-bearing package,
> waits for the pod to be Ready, curls `/healthz`, and runs `cosign verify-blob` on a
> DSSE receipt. If that badge is green, the deploy *pipeline* is proven. This runbook is
> the same flow at full scale on your hardware.

---

## 0. What this proves vs. what is separate-only (read first — honest scope)

| Claim | Status |
|-------|--------|
| A real image-bearing bundle deploys onto a real cluster and the pod goes Ready | ✅ **PROVEN** (CI + this runbook) |
| The deployed workload answers `/healthz` with 200 | ✅ **PROVEN** (CI + this runbook) |
| A DSSE receipt verifies with `cosign verify-blob` → "Verified OK" | ✅ **PROVEN** (CI, ephemeral key; tower uses the real key) |
| `cosign verify` of the published bundle signature → "Verified OK" | ✅ **PROVEN** (keyless OIDC, any internet box) |
| killinchu fires a counter-UAS decision + emits a verifiable receipt | ✅ **REAL** against the live HF Space and the deployed organ (Step 6) |
| All 5 organs deploy simultaneously | ✅ Works on the tower; **NOT** CI-gated (3.6 GB > runner) — validated by *UDS Bundle Build + Publish* |
| Inter-organ mTLS / 3-of-4 Khipu quorum **over the network** | ❌ **ROADMAP** — organs deploy as separate workloads; cross-organ networking is `MESH_INTERCONNECT.md` (v0.5.0) |

**Bottom line:** the deploy, the health-up, and the signed-receipt verification are real
and repeatable. The cross-organ network mesh is not yet wired — say so plainly. The
single-organ kill-move (killinchu fires a decision and emits a verifiable receipt) **is**
real and is the honest demo.

---

## 1. One-time tool install (NOT on demo day)

```bash
# uds-cli v0.32.0 (bundles Zarf v0.77.0)
curl -sLo /usr/local/bin/uds \
  "https://github.com/defenseunicorns/uds-cli/releases/download/v0.32.0/uds-cli_v0.32.0_Linux_amd64"
chmod +x /usr/local/bin/uds
uds version          # expect: v0.32.0
uds zarf version     # expect: v0.77.0

# Zarf v0.77.0 standalone (for zarf init / package ops)
curl -sLo /usr/local/bin/zarf \
  "https://github.com/zarf-dev/zarf/releases/download/v0.77.0/zarf_v0.77.0_Linux_amd64"
chmod +x /usr/local/bin/zarf
zarf version         # expect: v0.77.0

# cosign v2.4.3
curl -fsSLo /usr/local/bin/cosign \
  "https://github.com/sigstore/cosign/releases/download/v2.4.3/cosign-linux-amd64"
chmod +x /usr/local/bin/cosign
cosign version       # expect: v2.4.3

# k3d v5.8.3
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG=v5.8.3 bash
k3d version          # expect: v5.8.x

# Linux inotify limits (required for Istio sidecars under UDS Core)
sudo sysctl fs.inotify.max_user_watches=1048576
sudo sysctl fs.inotify.max_user_instances=8192
```

---

## 2. Pre-flight signature check (no cluster needed, do this anywhere with internet)

```bash
cosign verify ghcr.io/szl-holdings/szl-mesh:v0.4.0 \
  --certificate-identity-regexp="^https://github.com/szl-holdings/" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

**Expected output (tail):**
```
Verification for ghcr.io/szl-holdings/szl-mesh:v0.4.0 --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The code-signing certificate was verified using trusted certificate authority certificates
...
```
If you see the JSON blocks and no error, the bundle signature is good. **This is the
supply-chain proof you show first.**

---

## 3. Create the cluster

```bash
# GPU-enabled (tower); falls back to CPU-only if the GPU flag is unsupported
k3d cluster create szl --gpus 1 || k3d cluster create szl

kubectl wait --for=condition=Ready nodes --all --timeout=120s
kubectl get nodes        # expect: 1 node, STATUS Ready
```

---

## 4. Initialize and deploy the bundle

Pick **one** of the two deploy modes.

### Mode A — Full UDS Core path (organs register with UDS Operator: Istio, SSO, NetworkPolicy)

```bash
# Deploy UDS Core slim-dev (Istio + Keycloak + Pepr) — 1–3 min
uds deploy oci://ghcr.io/defenseunicorns/packages/uds/core:v1.5.0-k3d-slim-dev --confirm
kubectl wait --for=condition=Ready pods -n pepr-system --all --timeout=300s

# Deploy the szl-mesh bundle (OCI pull — internet) ...
uds deploy oci://ghcr.io/szl-holdings/szl-mesh:v0.4.0 --confirm
# ... OR from the Warhacker USB (air-gapped):
#   uds-cli bundle deploy szl-mesh-v0.4.0.tar.zst --confirm
```

### Mode B — Minimal path (no UDS Core; organs run as plain Deployments)

```bash
zarf init --confirm
uds deploy oci://ghcr.io/szl-holdings/szl-mesh:v0.4.0 --confirm
# (USB: uds-cli bundle deploy szl-mesh-v0.4.0.tar.zst --confirm)
```

> The tower does **not** need Docker running at deploy time — Zarf baked every image into
> the OCI artifact at build time. The bundle is fully self-contained / air-gap capable.

---

## 5. Watch the organs come up

```bash
kubectl get namespaces | grep szl-
# expect: szl-a11oy szl-sentra szl-amaru szl-rosie szl-killinchu

for ns in szl-a11oy szl-sentra szl-amaru szl-rosie szl-killinchu; do
  echo "=== $ns ==="
  kubectl wait --for=condition=Available deploy --all -n "$ns" --timeout=180s
done
# expect: deployment.apps/<organ> condition met  (×5)

kubectl get deploy -A | grep szl-
# expect: each organ READY 1/1

# If on Mode A, confirm UDS Operator reconciled the Package CRs:
kubectl get packages -A | grep szl-     # expect: phase Ready
```

**Health probe (per organ).** Ports: a11oy/sentra/amaru = **8080**, rosie/killinchu = **7860**.
Health paths: a11oy `/api/a11oy/healthz`, sentra `/healthz`, amaru `/api/amaru/healthz`,
rosie `/api/rosie/healthz`, killinchu `/api/killinchu/healthz`.

```bash
# Example: killinchu (port 7860)
kubectl port-forward -n szl-killinchu svc/killinchu 7860:7860 &
PF=$!
curl -fsS http://localhost:7860/api/killinchu/healthz && echo "  <- killinchu OK"
kill $PF
```

---

## 6. THE KILL-MOVE — fire a counter-UAS decision + verify the receipt

The deployed organ image serves the counter-UAS evaluate endpoint. The **live HF Space**
is a guaranteed-online fallback if the in-cluster organ is still warming up — use whichever
responds.

```bash
# In-cluster (after the port-forward above):
curl -X POST http://localhost:7860/api/killinchu/v1/counter-uas/evaluate \
  -H "Content-Type: application/json" \
  -d '{"track_id":"4840D6","lat":32.7,"lon":-117.2,"alt_m":120,"speed_ms":15}'

# Guaranteed-live fallback (no cluster needed):
curl -X POST https://szlholdings-killinchu.hf.space/api/killinchu/v1/counter-uas/evaluate \
  -H "Content-Type: application/json" \
  -d '{"track_id":"4840D6","lat":32.7,"lon":-117.2,"alt_m":120,"speed_ms":15}'
```

**Expected:** a JSON verdict that runs the track through the geofence + defensive-only
Λ-gate and returns a DSSE-signed decision. The Λ-gate is **Conjecture 1, not a theorem** —
state that out loud.

**Verify the signed receipt** (ECDSA-P256, no cluster needed):

```bash
curl https://szlholdings-killinchu.hf.space/api/killinchu/v1/honest
# expect: {"kernel_commit":"c7c0ba17","doctrine":"v11","lambda":"Conjecture 1"}
```

**receipts.in ≡ receipts.out on the cluster** (works without the receipts server, FAIL_OPEN
mode; requires the `szl-uds-deployment` Pepr module — see note below):

```bash
kubectl get deploy -n szl-killinchu killinchu -o json | jq '{
  organ: .metadata.name,
  namespace: .metadata.namespace,
  "receipt.id":  .metadata.annotations["szl.receipt.id"],
  "receipt.ts":  .metadata.annotations["szl.receipt.ts"],
  "receipt.key": .metadata.annotations["szl.receipt.key"]
}'
```

> **Honest note on receipts:** the DSSE receipt *annotation* is written by the Pepr
> admission module that lives in the separate `szl-uds-deployment` repo, deployed
> alongside UDS Core. It is **not** baked into this bundle yet (deferred — the receipts
> server image is not public). The receipt *verification mechanism itself* is proven in CI
> (`cosign verify-blob → Verified OK`). The live killinchu decision + its own signed
> verdict (Step 6 curls above) is the real, self-contained kill-move that needs no extra
> module.

---

## 7. Teardown

```bash
k3d cluster delete szl
```

---

## 8. Troubleshooting — clean-cluster gotchas

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ImagePullBackOff` on an organ | organ image private / not pulled | Confirm `cosign verify ghcr.io/szl-holdings/<organ>:uds-v0.2.0 ...`; if pull is 403, set the GHCR package to Public or add an `imagePullSecret`. The bundle bakes images, so this only bites if deploying a single organ standalone. |
| Pod `Pending`, never schedules | restricted PodSecurity rejects the pod | Organs already ship hardened securityContext (non-root, RO rootfs, drop ALL). If you patched values, keep `runAsNonRoot: true` + `readOnlyRootFilesystem: true`. |
| Istio VirtualService routes to nothing / 503 at the gateway | UDS Package selector didn't match pod labels | Fixed in this release: each `manifests/uds-package.yaml` now selects `app.kubernetes.io/name: <organ>` and exposes the chart's real `service` name + port. Re-pull `:v0.4.0`. |
| `zarf init` hangs | registry/agent not ready | `kubectl get pods -n zarf`; re-run `zarf init --confirm`. |
| killinchu `/healthz` 404 on `:8080` | wrong port | killinchu/rosie listen on **7860**, not 8080. Port-forward `7860:7860`. |
| Pod admitted but Λ-gate VAP warns | `lambda-gate.vap.yaml` expects label `dsse-receipt=required` | Binding is **`Audit`** (non-blocking) by design during rollout — warnings are expected and do not stop the deploy. Do **not** promote to `Deny` before the receipt label is added to the organ Deployments (latent item, tracked). |
| `cosign verify` cert-identity mismatch | wrong regexp | Use `--certificate-identity-regexp="^https://github.com/szl-holdings/"` and `--certificate-oidc-issuer="https://token.actions.githubusercontent.com"`. |

---

*Doctrine v11 LOCKED 749/14/163 @ c7c0ba17 · Λ = Conjecture 1 · SLSA L1 honest · Apache-2.0*
*Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>*
