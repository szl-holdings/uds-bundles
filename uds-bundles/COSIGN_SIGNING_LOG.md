# COSIGN SIGNING LOG — UDS Productionization (SZL Crew)

**Agent:** UDS Productionization subagent (signing as Yachay)
**Date:** 2026-06-01
**Signing key:** `audit_2026-05-30_cursor_offline/.secret/cosign_signing_key.key`
(ECDSA P-256, ENCRYPTED SIGSTORE PRIVATE KEY, passphrase **empty**) — provisioned by the
Wire-D + DSSE agent. Public key `.secret/cosign_signing_key.pub`.

## Public key (P-256), per prior session record
```
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE7mrYWDnz8TvT7o4/65XGqYxo9OoV
vaB/grNuz+kVP1Xsaw0RokBKG0xT/XlV5Fz90AOwtgqC2yMBP0blK455gQ==
-----END PUBLIC KEY-----
```

## Honest signing status THIS SESSION

| Bundle | Artifact (to sign) | Signature | Status |
|---|---|---|---|
| a11oy | zarf-package-a11oy-runtime-amd64-0.3.1.tar.zst | a11oy.uds.sig | **PLACEHOLDER** — not yet signed (cosign OOM-killed in sandbox) |
| amaru | zarf-package-amaru-attestation-amd64-0.3.1.tar.zst | amaru.uds.sig | **PLACEHOLDER** |
| sentra | zarf-package-sentra-gates-amd64-0.3.1.tar.zst | sentra.uds.sig | **PLACEHOLDER** |
| killinchu | zarf-package-killinchu-bundle-amd64-0.3.1.tar.zst | killinchu.uds.sig | **PLACEHOLDER** |
| rosie | zarf-package-rosie-replay-amd64-0.3.1.tar.zst | rosie.uds.sig | **PLACEHOLDER** |

**0 of 5 bundles are signed in this session.** The artifacts to sign (`.tar.zst`) do not
yet exist because `zarf package create` could not run (binary OOM-killed), and cosign
itself completed only a banner print, never a `sign-blob`. I will not claim signatures
that were not produced.

## Exact signing command (run by `build_sign_all.sh` step 4–5)
```bash
export COSIGN_PASSWORD=""
KEY=.secret/cosign_signing_key.key
PUB=.secret/cosign_signing_key.pub
for PKG in artifacts/zarf-package-*-0.3.1.tar.zst; do
  cosign sign-blob   --key "$KEY" --tlog-upload=false --yes "$PKG" > "artifacts/$(basename ${PKG%.tar.zst}).sig"
  cosign verify-blob --key "$PUB" --signature "artifacts/$(basename ${PKG%.tar.zst}).sig" \
         --insecure-ignore-tlog=true "$PKG"   # expect: Verified OK
done
```
Offline mode (`--tlog-upload=false`) is intentional: the airgap blocks Rekor at deploy
time. For a public transparency record, drop the flag on an internet-connected host.

## Image attestation (SBOM) — staged
`syft <image> -o spdx-json` → `cosign attest --predicate <sbom> --type spdxjson --key $KEY
--tlog-upload=false --yes <image@digest>` (after image push). Commented in build script
step 7 because it requires a registry-resolvable digest.

— Yachay, 2026-06-01. Key is REAL and present; signatures are honestly PLACEHOLDER until the build host runs the script.
