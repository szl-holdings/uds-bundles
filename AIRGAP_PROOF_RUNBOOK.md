<!--
Copyright 2026 SZL Holdings · SPDX-License-Identifier: Apache-2.0
Doctrine v11 LOCKED 749/14/163 @ kernel c7c0ba17 · Λ = Conjecture 1 (NEVER theorem)
SLSA L1 honest · L2 attested (organs) · bundle-attestation + L3 roadmap
Section 889 = 5 vendors (Huawei, ZTE, Hytera, Hikvision, Dahua)
Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>
Co-Authored-By: Perplexity Computer Agent <agent@perplexity.ai>
-->

# AIR-GAP PROOF RUNBOOK — the REAL cable-pulled `uds deploy` (Raven proof)

**Audience:** Stephen (founder), on the disconnected box (RTX 4060 Ti tower or any Linux box).
**Goal:** Capture the single most valuable defense-credibility artifact — a genuine, reproducible, **fully air-gapped** deploy of all 5 SZL organs from a local store, with the network **physically pulled**, signatures verified **offline** (no Rekor, no internet), and a tamper-evident **PROOF.json + transcript** receipt produced as evidence.
**Why this exists:** CI (`deploy-proof.yml`) already proves the deploy **pipeline** on a real k3d cluster. What has **never** been captured end-to-end is the **cable-pulled** 5-organ run. This runbook + `scripts/capture_airgap_proof.sh` make that plug-and-play. **You** run the privileged/cable-pull step; everything around it is built.

> **Honesty contract.** This proof is only valid if the box is genuinely offline when it runs. The capture script **refuses to record a proof if it can reach the internet** (it probes Cloudflare, Google, GHCR, Rekor, and GitHub and aborts if any answer). It **never re-signs anything** and **never touches a private key** — signature verification is read-only against the existing public key. Re-signing / bundle-level attestation is the separate, founder-gated P-2-b task. Do **not** claim the air-gap proof is captured until you have actually run this and `PROOF.json` exists with `"overall": "PASS"` and `"network": {"result": "OFFLINE"}`.

---

## 0. What you need (one-time, while ONLINE — NOT on demo day)

Install the toolchain (versions match `deploy-proof.yml` / `JUNE9_DEPLOY_PROOF.md`):

```bash
# uds-cli v0.32.0 (bundles Zarf v0.77.0)
curl -sLo /usr/local/bin/uds \
  "https://github.com/defenseunicorns/uds-cli/releases/download/v0.32.0/uds-cli_v0.32.0_Linux_amd64"
chmod +x /usr/local/bin/uds && uds version

# Zarf v0.77.0 (standalone, for zarf init / package ops)
curl -sLo /usr/local/bin/zarf \
  "https://github.com/zarf-dev/zarf/releases/download/v0.77.0/zarf_v0.77.0_Linux_amd64"
chmod +x /usr/local/bin/zarf && zarf version

# cosign v2.4.3 (offline verify)
curl -fsSLo /usr/local/bin/cosign \
  "https://github.com/sigstore/cosign/releases/download/v2.4.3/cosign-linux-amd64"
chmod +x /usr/local/bin/cosign && cosign version

# k3d v5.8.3 (only needed if the box has no cluster yet)
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | TAG=v5.8.3 bash

# kubectl + Linux inotify limits (Istio sidecars under UDS Core)
sudo sysctl fs.inotify.max_user_watches=1048576
sudo sysctl fs.inotify.max_user_instances=8192
```

You also need, copied locally (next to the bundle, e.g. on a USB stick):
- the **bundle tarball** (Step A produces it),
- the **public key** `cosign.pub` (in this repo at `releases/szl-warhacker-uds-v1.0.0/cosign.pub`, keyid `szlholdings-cosign`, PEM fingerprint `a4d73120c312d94bdd6cbdfa6f3d629cfff4b85e7addde5f9c3fd4c02341eb30`),
- the bundle's **detached signature** `<bundle>.sig` (Step A.4),
- `scripts/capture_airgap_proof.sh` from this repo.

---

## A. STAGE the bundle + all 5 organ images into a LOCAL store — while ONLINE

You will pull everything you need to disk now, so that at deploy time **no registry is contacted**.

### A.1 — Pre-flight signature check (online, anywhere)

```bash
cosign verify ghcr.io/szl-holdings/szl-mesh:v0.4.0 \
  --certificate-identity-regexp="^https://github.com/szl-holdings/" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
# Expect: "Verified OK" + the JSON claim blocks. This is the supply-chain proof you show first.
```

### A.2 — Pull the bundle into a LOCAL OCI store (no deploy yet)

The published bundle `szl-mesh:v0.4.0` bakes all 5 organ images. Pull it to a local tarball:

```bash
mkdir -p ~/szl-airgap && cd ~/szl-airgap
# uds-cli pull -> a self-contained .tar.zst with every organ image baked in:
uds pull oci://ghcr.io/szl-holdings/szl-mesh:v0.4.0 -o .
# Result (name may vary by uds-cli version):
#   uds-bundle-szl-mesh-amd64-0.4.0.tar.zst   (a.k.a. szl-mesh-v0.4.0.tar.zst)
ls -lh *.tar.zst
BUNDLE="$(ls -1 *szl-mesh*amd64*0.4.0.tar.zst 2>/dev/null | head -1)"
echo "BUNDLE=$BUNDLE"
```

> If your `uds-cli` build lacks `uds pull`, use the Zarf equivalent:
> `uds zarf package pull oci://ghcr.io/szl-holdings/szl-mesh:v0.4.0` (writes a `zarf-package-*.tar.zst`).
> Either tarball is self-contained — every organ image layer is inside it.

### A.3 — Record the staged digests (so the proof is honest)

These are the **live GHCR ground-truth digests** (resolved 2026-06-13, all HTTP 200 anonymously). The deployed organs must match these:

| Organ | Image | Digest |
|---|---|---|
| a11oy | `ghcr.io/szl-holdings/a11oy:uds-v0.2.0` | `sha256:c285293c72b7a952743313d98a69d9eb0e641a60eeb48289e61c6e2f23d21526` |
| sentra | `ghcr.io/szl-holdings/sentra:uds-v0.2.0` | `sha256:60a0efc14366ba392bfe3f3cd4196863fe148bb87a17428be6a57f0a05ac3639` |
| amaru | `ghcr.io/szl-holdings/amaru:uds-v0.2.0` | `sha256:53301e26adcde49e73df28d8c3b790f2496da9d495307fe8587ffa7452b289ff` |
| rosie | `ghcr.io/szl-holdings/rosie:uds-v0.2.0` | `sha256:1984a15f53c2e1b91c7dafaa0ed5df9148d57e3e86eb73db879c2b0443302848` |
| killinchu | `ghcr.io/szl-holdings/killinchu:uds-v0.2.0` | `sha256:fda40c1afb565323e8a5b3503dec85e8f47cada11e311e24185b744dcb3b277d` |
| **bundle** | `ghcr.io/szl-holdings/szl-mesh:v0.4.0` | `sha256:7f5fce3238ce3d255b322340bbe18cad1eb656e677065a2757637337300cac7f` |

(These same digests are pinned inside `scripts/capture_airgap_proof.sh`, so the receipt cross-checks automatically.)

### A.4 — Stage the public key + detached signature next to the bundle

```bash
# Public key (read-only — you are VERIFYING, not signing):
cp /path/to/uds-bundles/releases/szl-warhacker-uds-v1.0.0/cosign.pub ~/szl-airgap/cosign.pub

# Detached signature for the bundle tarball. If you already have a published .sig
# (e.g. releases/.../bundle.tar.zst.sig is for the release artifact), use the one that
# matches THIS tarball's sha256. If the published .sig is for a different artifact,
# the honest path is: sign THIS tarball once on a CONNECTED box with the org key
# (that is the founder-gated signing step — do it deliberately, off the air-gap box):
#   cosign sign-blob --key <org.key> --tlog-upload=false --yes \
#     "$BUNDLE" > "$BUNDLE.sig"
# Then copy "$BUNDLE.sig" onto the USB next to the bundle.
ls -lh ~/szl-airgap/*.sig ~/szl-airgap/cosign.pub
```

> **Why a detached `.sig`?** On a cable-pulled box there is no registry to `cosign verify` an OCI ref against. The detached `cosign verify-blob` over the tarball is the airtight offline path. If you instead stand up a **local OCI registry mirror** (advanced), the script will fall back to `cosign verify --insecure-ignore-tlog=true <ref>`.

### A.5 — Make sure a cluster is available (online prep)

Either bring your own UDS Core cluster, or stand one up now (this is the only step that may touch the network — do it BEFORE you pull the cable):

```bash
# Option 1 — full UDS Core (Istio Ambient + Keycloak + Pepr): needs internet ONCE.
uds deploy k3d-core-demo:0.42.0 --confirm
# Option 2 — lighter / air-gap-friendly plain k3d + zarf init:
k3d cluster create szl && uds zarf tools download-init && uds zarf init --confirm
```

The repo's `tower_bootstrap.sh` automates Step A.5 (`MODE=core` or `MODE=k3d`).

---

## B. PHYSICALLY DISCONNECT — pull the cable (the founder/privileged gate)

Do **one** of these (any is sufficient; doing more is better). After this point, **nothing** should touch the internet.

```bash
# B.1 — Physically unplug the Ethernet cable. (The most convincing for a judge.)

# B.2 — Disable the NIC(s) by software (replace eth0/wlan0 with your interfaces):
sudo ip link set eth0 down
sudo ip link set wlan0 down 2>/dev/null || true
nmcli networking off 2>/dev/null || true       # if NetworkManager is present

# B.3 — Drop the default route (kills all egress without downing the local cluster net):
sudo ip route del default 2>/dev/null || true
ip route show default        # expect: (empty)

# B.4 — (optional, belt-and-suspenders) firewall-drop all egress:
sudo iptables -P OUTPUT DROP 2>/dev/null || true
```

**Confirm you are offline before deploying** (the capture script also does this as a hard gate):

```bash
for hp in 1.1.1.1 8.8.8.8 ghcr.io rekor.sigstore.dev github.com; do
  timeout 4 bash -c "exec 3<>/dev/tcp/$hp/443" 2>/dev/null \
    && echo "REACHABLE: $hp  <-- STILL ONLINE, do not proceed" \
    || echo "unreachable: $hp (good)"
done
```

> The local k3d/UDS cluster network is internal (loopback / docker bridge / kube DNS) and keeps working with the default route dropped — only **egress to the internet** is cut. That is exactly the air-gap condition.

---

## C. DEPLOY fully offline from the local store

You can run the deploy by hand, then capture; or just run the capture script (Section E), which does the deploy + verify + receipt in one honest pass. Hand path:

```bash
cd ~/szl-airgap
# uds-cli path (preferred):
uds bundle deploy "$BUNDLE" --confirm          # or: uds-cli bundle deploy "$BUNDLE" --confirm
# Zarf path (if you pulled a zarf-package tarball):
#   zarf package deploy "$BUNDLE" --confirm
```

No registry is contacted: every image layer is inside `$BUNDLE`. If you see any `ghcr.io` pull attempt or `ImagePullBackOff`, the bundle was not fully self-contained — stop and re-stage (Step A.2) while online.

---

## D. VERIFY all 5 organs come up + cosign-verify OFFLINE

### D.1 — Organs up

```bash
for ns in szl-a11oy szl-sentra szl-amaru szl-rosie szl-killinchu; do
  echo "=== $ns ==="
  kubectl wait --for=condition=Available deploy --all -n "$ns" --timeout=300s
done
kubectl get deploy -A | grep szl-     # expect each organ READY 1/1
# Under UDS Core (MODE=core) also confirm the UDS Operator reconciled the Package CRs:
kubectl get packages -A | grep szl-   # expect phase Ready
```

**Health ports/paths** (per `JUNE9_DEPLOY_PROOF.md`): a11oy/sentra/amaru = **8080**, rosie/killinchu = **7860**. Example:

```bash
kubectl port-forward -n szl-killinchu svc/killinchu 7860:7860 &
curl -fsS http://localhost:7860/api/killinchu/healthz && echo "  <- killinchu OK"; kill %1
```

### D.2 — Record the deployed image digests (proves what actually ran)

```bash
for ns in szl-a11oy szl-sentra szl-amaru szl-rosie szl-killinchu; do
  echo -n "$ns: "
  kubectl get pods -n "$ns" -o jsonpath='{.items[*].status.containerStatuses[*].imageID}{"\n"}'
done
# Each imageID should carry the digest from the table in A.3.
```

### D.3 — OFFLINE signature verify (no Rekor, no network)

```bash
cosign verify-blob \
  --key cosign.pub \
  --insecure-ignore-tlog=true \
  --signature "$BUNDLE.sig" \
  "$BUNDLE"
# EXPECTED OUTPUT (tail):
#   Verified OK
```

`--insecure-ignore-tlog=true` is what makes this an **offline** verify: it skips the Sigstore transparency-log (Rekor) round-trip, so it works with the cable pulled. This is the supply-chain claim that survives the air-gap.

> If you staged a local OCI registry mirror instead of a detached `.sig`, the offline ref verify is:
> `cosign verify --key cosign.pub --insecure-ignore-tlog=true ghcr.io/szl-holdings/szl-mesh:v0.4.0`

---

## E. CAPTURE the proof receipt — `scripts/capture_airgap_proof.sh`

Instead of running C + D by hand, run the harness. It asserts the box is offline, deploys, waits for all 5 organs, records the running digests, runs the offline verify, and emits **PROOF.json + a timestamped transcript** with a sha256 of the run. It **fails loudly** if the box is online or any gate is RED — so the receipt is honest.

```bash
cd ~/szl-airgap
sudo bash /path/to/uds-bundles/scripts/capture_airgap_proof.sh \
  --bundle "$BUNDLE" \
  --pubkey ./cosign.pub \
  --outdir ./airgap-proof-$(date -u +%Y%m%dT%H%M%SZ)
```

**Expected tail on success:**

```
[ ... ] ========== 1. NETWORK-DOWN ASSERTION ... ==========
[ ... ] PASS: all 5 probes unreachable — box is genuinely air-gapped.
[ ... ] PASS: offline deploy returned success.
[ ... ] organs GREEN: 5/5
[ ... ] PASS: cosign verify-blob -> Verified OK (offline)
[ ... ] ========== DONE — overall=PASS ==========
[ ... ] Receipt:    .../airgap-proof-<ts>/PROOF.json
[ ... ] Transcript: .../airgap-proof-<ts>/transcript.log  (sha256 <hash>)
```

`PROOF.json` contains: the network-down evidence (`"result":"OFFLINE"` + per-probe results), `deploy_result`, per-organ `status` + `running_image` vs `expected_digest`, `offline_verify_result` (`Verified OK`), the bundle local sha256, the signing-key fingerprints/keyid, `transcript_sha256`, and `overall`. **A proof is only real when `overall == "PASS"` and `network.result == "OFFLINE"`.**

### Script options (env or flags)
- `--tool uds|zarf` — force the deployer (default auto: prefer uds-cli, fall back to zarf).
- `WAIT_TIMEOUT=300` — per-organ Available wait (seconds).
- `ALLOW_DEGRADED=1` — record a missing organ RED without aborting (default 0 = all 5 must be GREEN).
- `SKIP_DEPLOY=1` — bundle already deployed; only run verify + capture (re-capture a receipt).
- `LINT=1 ... --lint` — syntax/plan only, **no network, no cluster** (this is what CI runs).

---

## F. ATTACH the proof + re-connect

```bash
# Copy the receipt into the release tree so it ships with the bundle:
cp -r ./airgap-proof-<ts> /path/to/uds-bundles/releases/szl-warhacker-uds-v1.0.0/airgap-proof/
# Commit PROOF.json + transcript.log (these are the Raven proof artifact).

# Re-enable networking when done (reverse Step B):
sudo ip link set eth0 up; sudo ip route add default via <gw> dev eth0 2>/dev/null || true
sudo iptables -P OUTPUT ACCEPT 2>/dev/null || true
```

Update `STATUS.md` from "runbook ready; transcript pending" to "**captured**" only **after** `PROOF.json` exists with `overall=PASS`. Until then, the honest state is: pipeline proven in CI; full air-gap deploy = runbook + harness ready, founder-run, transcript pending.

---

## G. Teardown / troubleshooting (carried from `JUNE9_DEPLOY_PROOF.md`)

```bash
k3d cluster delete szl     # if you stood up a throwaway cluster
```

| Symptom | Cause | Fix |
|---|---|---|
| Script aborts "box reached N external endpoint(s)" | NIC/route still up | Re-do Step B (cable / `ip link down` / `ip route del default`); re-confirm with the probe loop. |
| `ImagePullBackOff` on an organ | bundle not self-contained / wrong tarball | Re-pull with `uds pull` while online (Step A.2); the tarball must bake every image layer. |
| `cosign verify-blob` cert/sig mismatch | `.sig` doesn't match this tarball | Use the `.sig` produced for THIS exact tarball (Step A.4); sha256 must match. |
| Pod `Pending` never schedules | restricted PodSecurity | Organs ship hardened securityContext (non-root, RO rootfs, drop ALL); keep those if you patched values. |
| killinchu `/healthz` 404 on `:8080` | wrong port | killinchu/rosie listen on **7860**, not 8080. |
| `kubectl get packages` empty under MODE=k3d | no UDS Operator | Expected without UDS Core — organs run as plain Deployments; Package CR reconcile is a Core feature. |

---

*Doctrine v11 LOCKED 749/14/163 @ c7c0ba17 · Λ = Conjecture 1 (NEVER theorem) · SLSA L1 honest · L2 attested (organs) · bundle-attestation + L3 roadmap · Apache-2.0*
*Signed-off-by: Stephen P. Lutar Jr. <stephenlutar2@gmail.com>*
