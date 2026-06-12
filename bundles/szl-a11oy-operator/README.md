# SZL Rosie · Operational UDS Drop

> **a11oy vertical re-issue — a11oy Operator.** This signed deployment bundle is the
> a11oy-vertical re-bundling of the `rosie` organ. The bundle, Zarf package,
> namespace and UDS Package CR are re-issued and re-signed (keyless cosign OIDC)
> under the a11oy-vertical name `szl-a11oy-operator`. The underlying container image
> retains its internal codename (`ghcr.io/szl-holdings/rosie`) and continues
> to serve its `/api/rosie/` paths — its build source is archived and is not
> rebuilt here; only the deployment artifact is renamed and re-signed. The codename
> bundle remains published in parallel and is retired only after this verifies.


## WHAT THIS DOES (operational)
- Deploys in 60 seconds on UDS Core via `zarf package deploy szl-a11oy-operator.uds.tar.zst --confirm`
- Runs air-gapped — pull the network cable, it still works
- Operator console with human-in-the-loop decision approval gates. Operators review receipts, approve/deny pending actions, and inspect mesh health from a single surface.
- Every agent action emits a cosign-signed DSSE receipt
- Verify any receipt with: `cosign verify-blob --signature ... --certificate ... <blob>`

### Fills this UDS Core gap
**adds human-in-loop layer UDS Core lacks**

### Operational endpoints
- `/api/rosie/healthz`
- `/ (Gradio 11-tab console)`
- `/v1/* (FastAPI contract)`
- `Receipt Verifier`
- `Decision approval gates`
- `Policy Evaluate`

## WHAT WE'RE NOT CLAIMING
- No Iron Bank certification (not required by scope)
- Not SWFT-listed (we don't need it to work)
- Not FedRAMP authorized (we don't need it to work)
- Λ is Conjecture 1, NOT a theorem
- SLSA L1 + L2 (provenance attestation verifies via cosign verify-attestation); L3 not claimed
- 163 sorries open in the Lean kernel (disclosed, never hidden)

## WHAT WE ASK
- Run it on YOUR operational hardware for one week
- Tell us if it deserves more

## SUBSTRATE
- Doctrine v11 LOCKED 749/14/163
- Lean 4 + Mathlib v4.13.0 kernel: `github.com/szl-holdings/lutar-lean`
- Source: `github.com/szl-holdings/rosie`
- Live HF Space: `huggingface.co/spaces/SZLHOLDINGS/rosie`

## BUNDLE CONTENTS
| Artifact | Path |
|---|---|
| UDS Core bundle spec | `uds-bundle.yaml` |
| Zarf package def | `zarf.yaml` |
| Helm chart | `chart/` |
| SBOM (SPDX 2.3) | `sbom/rosie.spdx.json` |
| SBOM (CycloneDX 1.4) | `sbom/rosie.cyclonedx.json` |
| SLSA provenance (L1+L2, cosign-verified) | `attestations/rosie.slsa-provenance.json` |
| Cosign verify guide | `attestations/rosie.cosign-verify.txt` |
| Pepr policies | `policies/` (namespace isolation · DSSE-receipt egress · Section 889 denylist) |

## BUILD & DEPLOY (operational, 60s)
```bash
# 1. Create the air-gap bundle (bakes image + chart + SBOM into one .tar.zst)
zarf package create . --confirm

# 2. On the operational box (cable pulled), deploy
zarf package deploy szl-a11oy-operator.uds.tar.zst --confirm

# 3. Watch it come up
kubectl -n szl-a11oy-operator get pods -w
```

## SECTION 889
Pepr denylist enforces exactly 5 covered vendors (FAR 52.204-25):
Huawei · ZTE · Hytera · Hikvision · Dahua. Fail-CLOSED.
