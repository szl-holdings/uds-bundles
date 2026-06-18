# COSIGN_KEYS.md — authoritative cosign key-to-artifact map (SZL estate)

This is the single source of truth for "which key signs what, and how do I verify it."
It is plain and honest by design. If anything elsewhere in the repos disagrees with this
file about a key's identity, THIS file is correct and the other place is a stale label.

Last reconciled: 2026-06-18. Reconciliation method: SHA-256 of the DER-encoded SubjectPublicKeyInfo
(`openssl pkey -pubin -in <file> -outform DER | openssl dgst -sha256`) of every committed `.pub`,
cross-checked against the module/policy that embeds it. No artifact was re-signed to produce this
map; it documents the keys exactly as they are today.

--------------------------------------------------------------------------------
THE ONE THING TO READ FIRST
--------------------------------------------------------------------------------

Current / live artifacts verify KEYLESS via Sigstore Fulcio + Rekor (GitHub Actions OIDC).
There is NO single shared keyed "org key." There are FOUR distinct ECDSA-P256 keys, each
bound to its own trust domain.

In particular:

  `cosign verify --key .github/cosign.pub <a uds bundle>`  WILL FAIL.

That is BY DESIGN, not a bug. `.github/cosign.pub` is the ORG receipts key (`a1f6d323`).
Bundles are signed in a DIFFERENT trust domain: live bundles are keyless (Fulcio+Rekor),
and the legacy v0.1.0 keyed bundles use the uds-bundles key (`daa4aeca`), NOT the org key.
The two keys happen to share the cosign keyid STRING `szlholdings-cosign`, which is a label
collision — it does not mean they are the same key. Always verify per the map below.

--------------------------------------------------------------------------------
THE FOUR KEYS
--------------------------------------------------------------------------------

### Key 1 — ORG RECEIPTS key
- Fingerprint (SHA-256 DER SPKI): `a1f6d323…2826ab`
  (full: a1f6d3233442cdad0801c702e0ff77aa45fd1ba45f532e3919c80d520b2826ab)
- Public key file: `szl-holdings/.github/cosign.pub`
- Also embedded in: a11oy `szl_dsse.py` and amaru `organs/amaru/sidecar/src/amaru/dinn_dsse.py`
  (both as `COSIGN_PUBLIC_PEM`), keyid label `szlholdings-cosign`.
- Signs: a11oy/amaru DSSE receipt blobs (Khipu / DINN agent receipts) — `cosign verify-blob --key`.
- Status: ACTIVE (org DSSE receipts).
- Verify a DSSE org/DINN receipt (keyed verify-blob):
    cosign verify-blob --key cosign.pub --signature <sig.b64> <pae-or-payload-blob>
  (or in-process: szl_dsse.verify_envelope(env) / dinn_dsse.verify_envelope(env))
- DOES NOT verify: uds bundles, PINN Λ-receipts, uds-deployment images. Different trust domains.

### Key 2 — UDS-BUNDLES signing key
- Fingerprint (SHA-256 DER SPKI): `daa4aeca…7cb40b`
  (full: daa4aeca263251e97125fd227ff82e024a64ec970d1c74828463ffba097cb40b)
- Public key file: `uds-bundles/bundles/v0.1.0/cosign_signing_key.pub`
  (byte-identical copies also at `artifacts/`, `releases/v0.1.0/`, and
  `releases/szl-warhacker-uds-v1.0.0/cosign.pub`).
- Also embedded in: `mesh/pinn_dsse.py` (`COSIGN_PUBLIC_PEM`) and all nine
  `bundles/*/policies/cosign-image-policy.yaml` `szl-key` authorities.
- Signs:
  - the v0.1.0 `*.uds.sig` proof bundles (keyed legacy path, offline `--tlog-upload=false`);
  - PINN Λ-receipts emitted by `pinn_dsse.sign_payload` (keyid label `szlholdings-cosign`);
  - the optional `szl-key` keyed authority in the image policies (only effective if
    `COSIGN_PRIVATE_KEY` is provisioned — it is not; live images are keyless).
- Status: LEGACY-KEYED (the live bundle `szl-uds-bundle:uds-v0.3.0` and the policies'
  live path are KEYLESS; this key is the legacy keyed fallback).
- IMPORTANT — this is NOT the org key `a1f6d323`. The shared keyid string `szlholdings-cosign`
  is a label collision. A PINN receipt verifies ONLY with this key, never with the org key,
  despite older docstrings that claimed otherwise (now corrected).
- Verify a v0.1.0 keyed bundle / a PINN receipt (keyed verify-blob):
    cosign verify-blob --key bundles/v0.1.0/cosign_signing_key.pub \
      --signature <sig.b64> <bundle-or-pae-blob>
- Verify the CURRENT (v0.3.0) bundle — KEYLESS, no key file:
    cosign verify-blob \
      --certificate-identity "https://github.com/szl-holdings/uds-bundles/.github/workflows/zarf-bundle-build.yml@refs/tags/v0.2.0" \
      --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
      bundle.tar.zst
  Bundle SLSA provenance attestation (keyless, Rekor-anchored):
    cosign verify-attestation --type slsaprovenance \
      --certificate-identity "https://github.com/szl-holdings/szl-uds-deployment/.github/workflows/uds-bundle-attest-existing.yml@refs/heads/main" \
      --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
      oci://ghcr.io/szl-holdings/szl-uds-bundle:uds-v0.3.0

### Key 3 — UDS-DEPLOYMENT IMAGES key
- Fingerprint (SHA-256 DER SPKI): `e136ee4e…66288e`
  (full: e136ee4ef7a59571029be95f8eb994f921d32778d9a9c31630dd7f131166288e)
- Public key file: `szl-uds-deployment/cosign/cosign.pub`
- Signs: nothing live. It is the OPTIONAL image key-pair, used only if `COSIGN_PRIVATE_KEY`
  (+ `COSIGN_PASSWORD`) repo secrets are provisioned — they are not. The receipts-server
  image is signed KEYLESS in CI.
- Status: LEGACY / OPTIONAL (not an active verify path).
- Verify the current receipts-server image — KEYLESS, no key file:
    cosign verify ghcr.io/szl-holdings/szl-receipts-server:uds-v0.4.0 \
      --certificate-identity "https://github.com/szl-holdings/szl-uds-deployment/.github/workflows/receipts-server-image.yml@refs/tags/receipts-server-v0.4.0" \
      --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
- Keyed verify (only meaningful if someone later opts into key-pair signing):
    cosign verify --key szl-uds-deployment/cosign/cosign.pub <image>

### Key 4 — RECEIPTS-PACKAGE key
- Fingerprint (SHA-256 DER SPKI): `e61eee51…01d8a7`
  (full: e61eee51bdb4b7bab48b4ac5d7a2c8446e92ca61c1140bf60c086ade1d01d8a7)
- Public key file: `szl-uds-deployment/cosign/szl-receipts-package.pub`
- Signs: only the RETIRED internal artifact
  `ghcr.io/szl-holdings/packages/szl-receipts:0.3.1-upstream`. Its private half is gone.
  Kept solely so that frozen historical artifact stays independently checkable.
- Status: RETIRED. The current package `szl-receipts:0.4.0-upstream` is KEYLESS.
- Verify the historical frozen artifact (keyed):
    cosign verify --key szl-uds-deployment/cosign/szl-receipts-package.pub \
      ghcr.io/szl-holdings/packages/szl-receipts:0.3.1-upstream
- Verify the current package — KEYLESS, no key file:
    cosign verify ghcr.io/szl-holdings/szl-receipts:0.4.0-upstream \
      --certificate-identity "https://github.com/szl-holdings/szl-uds-deployment/.github/workflows/zarf-package-sign.yml@refs/heads/main" \
      --certificate-oidc-issuer "https://token.actions.githubusercontent.com"

--------------------------------------------------------------------------------
COMMON TRAPS (all by-design, all explained above)
--------------------------------------------------------------------------------

- `cosign verify --key .github/cosign.pub <bundle>` → FAILS. The org key (`a1f6d323`) does
  not sign bundles; live bundles are keyless and the legacy keyed path uses `daa4aeca`.
- Verifying a PINN Λ-receipt against the org key → FAILS. PINN receipts use `daa4aeca`,
  not `a1f6d323`, even though both carry keyid `szlholdings-cosign`.
- `--key szl-uds-deployment/cosign/cosign.pub` / `…/szl-receipts-package.pub` against the
  CURRENT image or package → FAILS. Those are legacy/retired keys; current artifacts are keyless.

--------------------------------------------------------------------------------
SCOPE / HONESTY
--------------------------------------------------------------------------------

- All four committed `.pub` files are genuine PUBLIC ECDSA-P256 keys; no private key is in
  any repo or its history. Never commit a private key.
- This map is documentation only. No artifact was re-signed, no key was converged or rotated,
  and no Rekor entry was created to produce it. Converging onto one key (or retiring all keyed
  paths to pure keyless) is a separate founder-gated decision that touches signing identity.
- SLSA posture (unchanged): L1 · L2-attested(images) · L3 roadmap; bundle-level L2 NOT earned.
  Λ uniqueness is Conjecture 1 (never a theorem).
