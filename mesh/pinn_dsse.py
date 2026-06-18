"""ECDSA-P256 DSSE signer for PINN Λ-receipts (Yachay 2026-06-01, PINN/DINN finish).

uds-mesh already ships ``formula_receipts.py``, which is an HMAC-SHA-256 receipt
layer (symmetric, keyid ``szl-formula-hmac-sha256-v1``). That layer is unchanged.

This module ADDS an *asymmetric* signer so a PINN Λ-receipt can be sealed and
then verified with a published public key (cross-repo, key-only verification):

    keyid (label): szlholdings-cosign  (see KEYID-COLLISION note below)
    algorithm:     ECDSA P-256 over SHA-256 of the DSSE PAE preimage (DSSEv1)
    private key:   env SZL_COSIGN_PRIVATE_PEM (PKCS8 PEM; NEVER committed)
    public key:    the uds-bundles signing key, SHA-256(DER SPKI) ``daa4aeca…7cb40b``
                   — committed at ``uds-bundles/bundles/v0.1.0/cosign_signing_key.pub``
                   (this is the key embedded as ``COSIGN_PUBLIC_PEM`` below).

KEYID-COLLISION NOTE (honest): this module shares the ``szlholdings-cosign`` keyid
*string* with the root ``szl_dsse.py`` and amaru's ``sidecar/src/amaru/dinn_dsse.py``,
but it does NOT use the same key. ``szl_dsse.py``/``dinn_dsse.py`` embed the ORG key
``a1f6d323…2826ab`` (``szl-holdings/.github/cosign.pub``); this module embeds the
uds-bundles key ``daa4aeca…7cb40b``. They are DISTINCT ECDSA-P256 keys. Therefore a
PINN receipt and a DINN/org receipt do NOT verify with the same key — the matching
keyid string is a label collision, not a shared trust domain. Verify a PINN receipt
with the uds-bundles key only (command below). See ``COSIGN_KEYS.md`` for the full
key-to-artifact map and the exact working verify commands.

Verify a PINN Λ-receipt (extract the base64 sig + PAE'd payload, then):
    cosign verify-blob --key bundles/v0.1.0/cosign_signing_key.pub \
        --signature <sig> <pae-preimage-or-payload-blob>
(equivalently, ``pinn_dsse.verify_envelope(env)`` checks the embedded
``daa4aeca`` key in-process — no network call.)

HONESTY: the signature attests the *receipt bytes*, not the PINN's physics. The
underlying Lean obligation (``confidence_monotone_in_residual`` and any Λ-aggregator
claim) ships as a ``sorry`` placeholder where not yet discharged; none is claimed
proven beyond what Lean actually checks. Λ uniqueness is Conjecture 1, never a
theorem. SLSA L1 (honest). When ``cryptography`` or the secret is absent this
returns an UNSIGNED envelope with an explicit marker — NO signature is fabricated.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

KEYID = "szlholdings-cosign"  # label only; see KEYID-COLLISION note in module docstring
PINN_PAYLOAD_TYPE = "application/vnd.szl.pinn-lambda-receipt+json"
# Verify-key for PINN receipts = the uds-bundles signing key (daa4aeca…7cb40b),
# NOT the org key (a1f6d323). Published public half:
PUB_KEY_URL = "https://github.com/szl-holdings/uds-bundles/blob/main/bundles/v0.1.0/cosign_signing_key.pub"

# Published public key (uds-bundles/bundles/v0.1.0/cosign_signing_key.pub) — PUBLIC,
# embedded so verification needs no network call. SHA-256(DER SPKI) = daa4aeca…7cb40b.
# This is NOT the org key in szl_dsse.COSIGN_PUBLIC_PEM (a1f6d323) — it is a distinct
# key, despite the shared keyid string. See COSIGN_KEYS.md.
COSIGN_PUBLIC_PEM = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE7mrYWDnz8TvT7o4/65XGqYxo9OoV
vaB/grNuz+kVP1Xsaw0RokBKG0xT/XlV5Fz90AOwtgqC2yMBP0blK455gQ==
-----END PUBLIC KEY-----
"""


def canonical_json(obj: Any) -> bytes:
    """Deterministic canonical JSON: sorted keys, compact separators, UTF-8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def pae(payload_type: str, body: bytes) -> bytes:
    """DSSE Pre-Authentication Encoding (DSSEv1).

    >>> pae("t", b"x") == b"DSSEv1 1 t 1 x"
    True
    """
    t = payload_type.encode("utf-8")
    return (
        b"DSSEv1 " + str(len(t)).encode() + b" " + t + b" "
        + str(len(body)).encode() + b" " + body
    )


def _load_private_key():
    """Load the cosign EC private key from SZL_COSIGN_PRIVATE_PEM. None if absent."""
    pem = os.environ.get("SZL_COSIGN_PRIVATE_PEM")
    if not pem:
        return None
    try:
        if "BEGIN" not in pem:
            pem = base64.b64decode(pem).decode("utf-8")
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        return load_pem_private_key(pem.encode("utf-8"), password=None)
    except Exception:
        return None


def signing_available() -> bool:
    return _load_private_key() is not None


def public_key_fingerprint() -> str:
    """SHA-256 of the embedded public key PEM (stable identifier).

    >>> len(public_key_fingerprint()) == 64
    True
    """
    return hashlib.sha256(COSIGN_PUBLIC_PEM.strip().encode()).hexdigest()


def sign_payload(payload_obj: Any, payload_type: str = PINN_PAYLOAD_TYPE) -> dict[str, Any]:
    """Produce a DSSE envelope over the canonical JSON of ``payload_obj``.

    Returns the DSSE envelope. If no private key is present, returns an UNSIGNED
    envelope with an explicit honesty marker (no fabricated signature).

    >>> env = sign_payload({"residual": 0.0})  # doctest: +ELLIPSIS
    >>> env["payloadType"]
    'application/vnd.szl.pinn-lambda-receipt+json'
    >>> env["_dsse"]
    'DSSEv1'
    >>> isinstance(env["signed"], bool)
    True
    """
    body = canonical_json(payload_obj)
    to_sign = pae(payload_type, body)
    env: dict[str, Any] = {
        "payloadType": payload_type,
        "payload": base64.b64encode(body).decode("ascii"),
        "_dsse": "DSSEv1",
        "_pae_sha256": hashlib.sha256(to_sign).hexdigest(),
        "_signed_at": datetime.now(timezone.utc).isoformat(),
        "verify_key_url": PUB_KEY_URL,
    }
    priv = _load_private_key()
    if priv is None:
        env["signatures"] = []
        env["signed"] = False
        env["honesty"] = (
            "UNSIGNED — SZL_COSIGN_PRIVATE_PEM secret not present in this runtime; "
            "no signature fabricated. Receipt bytes + PAE hash are still "
            "integrity-bound and verifiable once the key is provided."
        )
        return env
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes
    sig = priv.sign(to_sign, ec.ECDSA(hashes.SHA256()))
    env["signatures"] = [{"sig": base64.b64encode(sig).decode("ascii"), "keyid": KEYID}]
    env["signed"] = True
    env["honesty"] = (
        "REAL — ECDSA-P256-SHA256 over DSSE PAE; verifiable by `cosign verify-blob "
        "--key uds-bundles/bundles/v0.1.0/cosign_signing_key.pub` (the daa4aeca key, "
        "NOT the org key a1f6d323). The signature attests the receipt bytes, NOT the "
        "PINN's physics. Lean obligation ships as `sorry` where not discharged; "
        "Λ uniqueness is Conjecture 1 (never a theorem)."
    )
    return env


def verify_envelope(env: dict[str, Any]) -> dict[str, Any]:
    """Verify a DSSE envelope against the embedded cosign public key."""
    out: dict[str, Any] = {
        "keyid_expected": KEYID,
        "pub_fingerprint_sha256": public_key_fingerprint(),
        "verify_key_url": PUB_KEY_URL,
    }
    try:
        payload_b64 = env.get("payload")
        payload_type = env.get("payloadType")
        sigs = env.get("signatures") or []
        if not payload_b64 or not payload_type:
            return {**out, "verified": False, "reason": "missing payload/payloadType"}
        if not sigs:
            return {**out, "verified": False, "reason": "no signatures (unsigned envelope)"}
        body = base64.b64decode(payload_b64)
        to_verify = pae(payload_type, body)
        out["pae_sha256"] = hashlib.sha256(to_verify).hexdigest()
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes
        from cryptography.exceptions import InvalidSignature
        pub = load_pem_public_key(COSIGN_PUBLIC_PEM.encode("utf-8"))
        any_ok = False
        for s in sigs:
            try:
                pub.verify(base64.b64decode(s.get("sig", "")), to_verify, ec.ECDSA(hashes.SHA256()))
                any_ok = any_ok or (s.get("keyid") == KEYID)
            except InvalidSignature:
                pass
        return {**out, "verified": any_ok, "keyid_match": any_ok}
    except Exception as e:  # pragma: no cover - defensive
        return {**out, "verified": False, "reason": f"{type(e).__name__}: {e}"}


if __name__ == "__main__":
    import doctest
    fails, _ = doctest.testmod(verbose=False)
    if fails == 0:
        print("✓ pinn_dsse doctests passed (DSSE PAE v1 + ECDSA-P256 cosign signer)")
