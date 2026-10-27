#!/usr/bin/env python3
"""
verify_hardened.py — Task C2 (hardening half)

A strict verifier that blocks both the alg:none attack and RS256/HS256
algorithm confusion. The fix for both is the same root cause: NEVER let
the token being verified choose its own algorithm. The verifier must
decide in advance what it expects, and refuse everything else.

Concretely:
  - algorithms=["RS256"] is passed EXPLICITLY and is the ONLY entry.
    PyJWT will reject any token whose header 'alg' isn't RS256 — this
    alone blocks alg:none (not in the list) and HS256 confusion (not in
    the list either).
  - The verification key always comes from OUR OWN trusted JWKS fetch,
    keyed by 'kid', never from anything embedded in or inferred from the
    token itself (some insecure examples online even read a 'jku'/'x5u'
    header from the token to decide WHERE to fetch the key from — don't
    do that, it lets an attacker point you at their own key server).
  - We never special-case "if alg is none, skip verification" or "accept
    either RS256 or HS256" — there is exactly one accepted algorithm,
    full stop.
"""

import jwt

KEYCLOAK_URL = "http://localhost:8080"
REALM = "CybersecurityLab"
JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"

ALLOWED_ALGORITHMS = ["RS256"]  # exactly one, on purpose


def verify_strict(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    alg = header.get("alg")

    if alg not in ALLOWED_ALGORITHMS:
        raise ValueError(
            f"Rejected: token alg={alg!r} is not in the allowed list {ALLOWED_ALGORITHMS}"
        )

    # Only now, having confirmed the algorithm is one we trust, do we go
    # fetch a verification key for it — and we always fetch it ourselves
    # from our own trusted JWKS URL, never from the token.
    jwk_client = jwt.PyJWKClient(JWKS_URL)
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=ALLOWED_ALGORITHMS,  # explicit again at decode time
        options={"verify_aud": False},
    )
    return claims


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <access_token>")
        sys.exit(1)

    import json
    claims = verify_strict(sys.argv[1])
    print(json.dumps(claims, indent=2))
