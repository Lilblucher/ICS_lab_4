#!/usr/bin/env python3
"""
lab4_verifier.py — Task B5

Fetches the JWKS (JSON Web Key Set) from Keycloak's realm certs endpoint
and cryptographically verifies the RS256 signature on an access token.

Two verification paths are shown on purpose:
  1. verify_with_pyjwt()   — the normal, correct way to do this in real code.
  2. verify_manually()     — reconstructs the RSA public key from its raw
                              'n' (modulus) and 'e' (exponent) components and
                              verifies the signature by hand, so you can
                              explain the actual math in your defense (Q2.2
                              explicitly asks for this).

Usage:
    python lab4_verifier.py <access_token>

The access token comes from Task B4 (the curl token exchange) — copy the
"access_token" value out of that JSON response.
"""

import base64
import json
import sys

import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.exceptions import InvalidSignature

KEYCLOAK_URL = "http://localhost:8080"
REALM = "CybersecurityLab"
CLIENT_ID = "python-oidc-app"  # expected audience, see note in verify_with_pyjwt

JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"


def fetch_jwks() -> dict:
    """GET the realm's public signing keys. No auth needed — these are public."""
    resp = requests.get(JWKS_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()


def b64url_to_int(value: str) -> int:
    """JWK numbers (n, e) are base64url-encoded big-endian integers, no padding."""
    padded = value + "=" * (-len(value) % 4)
    raw_bytes = base64.urlsafe_b64decode(padded)
    return int.from_bytes(raw_bytes, byteorder="big")


def find_key_for_token(jwks: dict, token: str) -> dict:
    """
    JWTs carry a 'kid' (key ID) in their header telling you which key in the
    JWKS signed them — a realm can rotate through several keys at once.
    """
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return key
    raise ValueError(f"No matching key for kid={kid!r} in JWKS")


def verify_with_pyjwt(token: str) -> dict:
    """The standard, recommended way: let PyJWT's JWKS client handle key
    selection, algorithm checking, expiry, etc. This is what real
    production code should look like."""
    jwk_client = jwt.PyJWKClient(JWKS_URL)
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    # NOTE: algorithms=["RS256"] is explicit and singular on purpose — see
    # the hardened verifier (verify_hardened.py) for why this matters.
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},  # Keycloak access tokens often omit a
                                         # simple 'aud' matching the client id;
                                         # disabled here for lab simplicity.
    )
    return claims


def verify_manually(token: str) -> dict:
    """
    Manual RS256 verification using the raw public key components (n, e)
    from the JWKS — demonstrates what PyJWT is doing internally.

    RS256 = RSASSA-PKCS1-v1_5 signature using SHA-256.
    The signed material is: base64url(header) + "." + base64url(payload)
    """
    jwks = fetch_jwks()
    jwk = find_key_for_token(jwks, token)

    n = b64url_to_int(jwk["n"])
    e = b64url_to_int(jwk["e"])
    public_key = rsa.RSAPublicNumbers(e, n).public_key()

    header_b64, payload_b64, signature_b64 = token.split(".")
    signed_data = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))

    try:
        public_key.verify(signature, signed_data, PKCS1v15(), SHA256())
    except InvalidSignature:
        raise ValueError("Signature verification FAILED — token is not authentic")

    padded_payload = payload_b64 + "=" * (-len(payload_b64) % 4)
    claims = json.loads(base64.urlsafe_b64decode(padded_payload))
    return claims


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <access_token>")
        sys.exit(1)

    token = sys.argv[1]

    print("=== Verifying via PyJWT (standard path) ===")
    claims = verify_with_pyjwt(token)
    print(json.dumps(claims, indent=2))

    print("\n=== Verifying manually (raw RSA math, using n/e from JWKS) ===")
    claims_manual = verify_manually(token)
    print(json.dumps(claims_manual, indent=2))
    print("\nSignature is mathematically valid — both paths agree.")


if __name__ == "__main__":
    main()
