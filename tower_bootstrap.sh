#!/usr/bin/env bash
# Copyright 2026 SZL Holdings — SPDX-License-Identifier: Apache-2.0
#
# tower_bootstrap.sh — ONE-USB tower bootstrap for the founder's RTX 4060 Ti tower.
#
# Founder directive: "plug a USB in and deploy." This script is the bare-tower
# half of that story. The published szl-mesh:v0.4.0 bundle deploys INTO a cluster;
# a fresh tower has no cluster. This script stands one up, then runs the single
# bundle-deploy command so all 5 organs come up from the one USB tarball.
#
# WHAT IT DOES (idempotent, founder-runnable):
#   1. Install uds-cli v0.32.0 (bundles Zarf v0.77.0) if not already present.
#   2. Install k3d v5.8.3 if not already present (needs Docker on the tower for
#      k3d only — NOT for the bundle deploy itself; Zarf serves the baked images).
#   3. Stand up a local cluster aligned to UDS Core 1.0:
#        MODE=core  (default) → uds deploy k3d-core-demo:0.42.0 (full UDS Core:
#                               Istio Ambient + Keycloak + Pepr + monitoring).
#                               REQUIRES INTERNET the first time to pull UDS Core.
#        MODE=k3d           → plain k3d cluster + `uds zarf init` only. No internet
#                               needed beyond the k3d node image. The szl-mesh
#                               bundle still deploys; SSO/Istio features are absent.
#   4. Deploy the ONE USB artifact: uds-cli bundle deploy <tarball> --confirm
#   5. Wait for all 5 organs Available + print a green/red summary.
#
# AIR-GAP NOTE: step 4 needs NO network — every organ image is baked into the
# tarball at CI create time. Steps 1-3 (tool + cluster install) are the ONE-TIME
# online prep done before demo day; on a truly air-gapped tower, pre-stage the
# uds/k3d binaries and the UDS Core / k3d node images, then run with MODE=k3d.
#
# USAGE:
#   bash tower_bootstrap.sh                         # MODE=core, finds tarball in CWD
#   BUNDLE=/media/usb/szl-mesh-v0.4.0.tar.zst bash tower_bootstrap.sh
#   MODE=k3d bash tower_bootstrap.sh                # plain k3d (lighter / air-gap)
#   SKIP_CLUSTER=1 bash tower_bootstrap.sh          # cluster already up, just deploy
#
# Doctrine v11 LOCKED 749/14/163 @ c7c0ba17 · Λ = Conjecture 1 · SLSA L1 honest
# Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>
set -euo pipefail

UDS_VERSION="${UDS_VERSION:-v0.32.0}"
K3D_VERSION="${K3D_VERSION:-v5.8.3}"
UDS_CORE_TAG="${UDS_CORE_TAG:-0.42.0}"           # k3d-core-demo per uds_latest_specs.md
MODE="${MODE:-core}"                              # core | k3d
CLUSTER="${CLUSTER:-szl}"
SKIP_CLUSTER="${SKIP_CLUSTER:-0}"
ORGANS=(szl-a11oy szl-sentra szl-amaru szl-rosie szl-killinchu)

log()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*" >&2; exit 1; }

# ── Locate the single USB tarball ──────────────────────────────────────────
find_bundle() {
  if [[ -n "${BUNDLE:-}" ]]; then echo "$BUNDLE"; return; fi
  local c
  for c in szl-mesh-v0.4.0.tar.zst uds-bundle-szl-mesh-amd64-0.4.0.tar.zst \
           /media/*/szl-mesh-v0.4.0.tar.zst /media/*/uds-bundle-szl-mesh-amd64-0.4.0.tar.zst; do
    [[ -f "$c" ]] && { echo "$c"; return; }
  done
  die "Bundle tarball not found. Set BUNDLE=/path/to/szl-mesh-v0.4.0.tar.zst"
}

# ── 1. uds-cli ──────────────────────────────────────────────────────────────
install_uds() {
  if command -v uds >/dev/null 2>&1 && uds version 2>/dev/null | grep -q "${UDS_VERSION#v}"; then
    ok "uds-cli $(uds version) already installed"; return
  fi
  log "Install uds-cli ${UDS_VERSION}"
  local dst="/usr/local/bin/uds"; [[ -w /usr/local/bin ]] || dst="$HOME/.local/bin/uds"
  mkdir -p "$(dirname "$dst")"
  curl -fsSLo "$dst" \
    "https://github.com/defenseunicorns/uds-cli/releases/download/${UDS_VERSION}/uds-cli_${UDS_VERSION}_Linux_amd64"
  chmod +x "$dst"
  command -v uds >/dev/null 2>&1 || export PATH="$(dirname "$dst"):$PATH"
  ok "uds $(uds version) (zarf $(uds zarf version))"
}

# ── 2. k3d ────────────────────────────────────────────────────────────────--
install_k3d() {
  if command -v k3d >/dev/null 2>&1; then ok "k3d $(k3d version | head -1) already installed"; return; fi
  log "Install k3d ${K3D_VERSION}"
  curl -fsSL https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG="${K3D_VERSION}" bash
  ok "k3d $(k3d version | head -1)"
}

# ── 3. Cluster aligned to UDS Core 1.0 ───────────────────────────────────────
stand_up_cluster() {
  [[ "$SKIP_CLUSTER" == "1" ]] && { ok "SKIP_CLUSTER=1 — using existing kube-context"; return; }
  command -v docker >/dev/null 2>&1 || die "Docker required for k3d (only for cluster creation, not the deploy)."
  if k3d cluster list 2>/dev/null | grep -q "^${CLUSTER}\b"; then
    ok "k3d cluster '${CLUSTER}' already exists"
  else
    log "Create k3d cluster '${CLUSTER}' (RTX 4060 Ti: --gpus 1 if NVIDIA runtime present)"
    k3d cluster create "$CLUSTER" --gpus 1 2>/dev/null || k3d cluster create "$CLUSTER"
  fi
  kubectl wait --for=condition=Ready nodes --all --timeout=120s

  if [[ "$MODE" == "core" ]]; then
    log "Deploy UDS Core 1.0 (k3d-core-demo:${UDS_CORE_TAG}) — Istio Ambient + Keycloak + Pepr"
    uds deploy "k3d-core-demo:${UDS_CORE_TAG}" --confirm \
      || uds deploy "oci://ghcr.io/defenseunicorns/packages/uds/bundles/k3d-core-demo:${UDS_CORE_TAG}" --confirm
    ok "UDS Core ${UDS_CORE_TAG} deployed"
  else
    log "MODE=k3d — plain Zarf init only (no UDS Core; lighter / air-gap path)"
    uds zarf tools download-init 2>/dev/null || true
    uds zarf init --confirm
    ok "Zarf initialized (internal registry up; SSO/Istio NOT present in this mode)"
  fi
}

# ── 4. THE ONE COMMAND ───────────────────────────────────────────────────────
deploy_bundle() {
  local b; b="$(find_bundle)"
  log "ONE-USB DEPLOY: uds-cli bundle deploy ${b} --confirm"
  uds-cli bundle deploy "$b" --confirm || uds bundle deploy "$b" --confirm
  ok "Bundle deploy returned success"
}

# ── 5. Verify all 5 organs ───────────────────────────────────────────────────
verify() {
  log "Wait for all 5 organs Available"
  local ns rc=0
  for ns in "${ORGANS[@]}"; do
    if kubectl wait --for=condition=Available deploy --all -n "$ns" --timeout=180s 2>/dev/null; then
      ok "$ns Available"
    else
      printf '\033[1;31m[RED]\033[0m %s not Available\n' "$ns"; rc=1
    fi
  done
  log "UDS Package CRs (reconciled by UDS Operator; MODE=core only)"
  kubectl get packages -A 2>/dev/null | grep szl- || echo "(no Package CRs — expected under MODE=k3d)"
  log "SUMMARY"
  kubectl get deploy -A | grep szl- || true
  [[ $rc -eq 0 ]] && ok "ALL 5 ORGANS GREEN — one USB, one command, everything deployed." \
                  || die "One or more organs did not reach Available — see above."
}

main() {
  log "SZL ONE-USB TOWER BOOTSTRAP  (MODE=${MODE}, cluster=${CLUSTER})"
  install_uds
  [[ "$SKIP_CLUSTER" == "1" ]] || install_k3d
  stand_up_cluster
  deploy_bundle
  verify
}
main "$@"
