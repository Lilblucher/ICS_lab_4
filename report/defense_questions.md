# Defense Questions — Draft Answers

Fill in the `[ ]` placeholders with your real screenshots/output. Explanations of jargon
are included inline so you can speak to these confidently in the oral defense, not just
read them off the page.

---

## Part A — TLS 1.3 Packet Analysis (produced on Kali)

### Q1.1 Handshake Capture
**Ask:** Screenshot of Wireshark showing ClientHello, ServerHello, Encrypted Extensions,
with exact frame numbers annotated.

**[ Paste screenshot here once captured. Annotate: "Frame #N: ClientHello", etc. ]**

### Q1.2 Cipher Analysis
**Ask:** Which curves were offered in ClientHello `key_share`? Why are static RSA cipher
suites absent in TLS 1.3?

**What to look for:** In the ClientHello's `key_share` extension, Wireshark lists each
curve offered (commonly `x25519`, `secp256r1`, `secp384r1`). **[ fill in what your capture
actually shows ]**

**Why static RSA is gone:** "Static RSA" key exchange means the client encrypts a secret
directly with the server's long-term RSA public key. The problem: if that private key is
ever stolen (even years later), an attacker who recorded the traffic can decrypt it
retroactively — there's no **forward secrecy**. TLS 1.3 *mandates* (EC)DHE instead: both
sides generate a fresh, temporary (ephemeral) key pair for every single session. Even if
the server's long-term key leaks later, each past session's traffic was protected by a
key that existed only for that one handshake and was then discarded — nothing recorded
earlier can be decrypted after the fact.

### Q1.3 Privacy Analysis
**Ask:** Why are Server Certificate messages encrypted in TLS 1.3? Contrast with TLS 1.2.

In TLS 1.2, the server's certificate (which reveals the exact domain/service you're
connecting to) is sent in the clear, before encryption keys exist — anyone passively
watching the network (an ISP, a Wi-Fi snooper) can see exactly which site you're visiting,
even though the actual page content is encrypted. TLS 1.3's 1-RTT handshake derives
encryption keys from the ephemeral key exchange *before* the certificate is sent, so the
certificate — and all of Keycloak/Cloudflare's handshake metadata — travels encrypted.
This closes a metadata-leakage gap: the "who are you talking to" information is now
protected, not just the "what did you say."

### Q1.4 Decryption & 0-RTT
**Ask:** Screenshot of decrypted HTTP/2 payload after loading sslkeys.log. Explain 0-RTT
mechanics and replay risk.

**[ Paste decrypted payload screenshot here ]**

**0-RTT explained:** On a *repeat* connection to a server you've recently talked to, TLS
1.3 lets the client send encrypted application data in its very first flight, before the
handshake even finishes round-tripping — using a key derived from a previous session's
secret ("session resumption"). This saves a full round trip of latency.

**Replay risk:** Because that 0-RTT data is encrypted with a key the client already had
*before* this connection started, there is no fresh randomness tying it to *this specific*
connection attempt. An attacker who captures that very first encrypted flight can
literally resend (replay) the exact same bytes to the server again, and the server has no
built-in way to tell "this is the original request" from "this is a copy sent a second
time" — which is dangerous for anything non-idempotent (e.g., "transfer $100") and fine
for idempotent GETs. This is why TLS 1.3 0-RTT is opt-in and servers are expected to
either reject it for sensitive operations or deduplicate requests.

---

## Part B — Keycloak OIDC & JWT Validation

### Q2.1 Token Anatomy
**Ask:** Decoded JSON payload for ID Token, Access Token, Refresh Token. Purpose of each.

**[ Paste decoded payloads here — decode at https://jwt.io or with
`python -c "import jwt,sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))"` ]**

- **ID Token** — proves *who the user is* to your application (python-oidc-app). Meant to
  be read by your app only, never forwarded to another API.
- **Access Token** — proves *what the user/app is allowed to do*. This is what you send to
  an API (like our `lab4_verifier.py` target) to prove you're authorized.
- **Refresh Token** — a long-lived credential used to get a *new* access token once the
  current one expires, without making the user log in again.

### Q2.2 Verifier Code
**Ask:** Paste Python code that fetches JWKS and verifies RS256 locally using N and e.

See [`part-c-jwt/lab4_verifier.py`](../part-c-jwt/lab4_verifier.py) — specifically
`verify_manually()`, which reconstructs the RSA public key from the JWK's `n`/`e` fields
and verifies the signature using `cryptography`'s `PKCS1v15` + `SHA256`, rather than
relying on PyJWT to do it under the hood.

### Q2.3 Exploit Analysis
**Ask:** Explain the exact security failure of alg:none and algorithm confusion. Show
whitelisting code.

- **alg:none failure:** the verifier let the *token itself* dictate which algorithm to
  trust, including "no signature needed at all." Security decisions must never be made by
  trusting attacker-controlled input — the verifier, not the token, should decide what's
  acceptable.
- **Algorithm confusion failure:** the verifier reused the *same key material* across two
  cryptographically incompatible algorithms (asymmetric RS256 vs. symmetric HS256)
  without checking which one that key was actually meant for. Because RS256 public keys
  are, by design, public, an attacker can fetch one and use it as an HMAC secret — and a
  verifier that doesn't pin "this key is RSA-only" will accept the forgery.
- **The fix (see [`part-c-jwt/verify_hardened.py`](../part-c-jwt/verify_hardened.py)):**
  hardcode `algorithms=["RS256"]` as the *only* accepted value, decided by the verifier in
  advance — never read off the incoming token.

### Q2.4 Storage Security
**Ask:** Compare storing JWTs in `localStorage` vs. `HttpOnly; Secure; SameSite=Strict`
cookies regarding XSS and CSRF.

| | `localStorage` | `HttpOnly` cookie |
|---|---|---|
| **XSS** | Any JavaScript running on the page (including injected attacker script) can read `localStorage` directly and steal the token. | `HttpOnly` means JavaScript *cannot* read the cookie at all — even an XSS payload can't exfiltrate it directly. |
| **CSRF** | Not automatically sent by the browser — you must manually attach it to requests (e.g., an `Authorization` header), so a forged cross-site request from another tab doesn't carry it. Effectively immune to CSRF. | Cookies are sent *automatically* by the browser on matching requests, including ones triggered by another site — unless `SameSite=Strict` (or `Lax`) blocks cross-site sending. `Secure` ensures it's only sent over HTTPS. |

**Bottom line:** `localStorage` trades CSRF-immunity for XSS-vulnerability; `HttpOnly`
cookies trade XSS-resistance for needing `SameSite`/CSRF-token defenses. Neither is a free
lunch — the right choice depends on which threat model your app is more exposed to.

---

## Part C — Team Role Synthesis

### Q3.1 IT Role
Container deployment: `docker-compose.yml` → `docker compose up -d` pulls and runs
Keycloak in dev mode on port 8080. Networking: host port 8080 maps to the container's
internal 8080; the realm/client/redirect URI config controls which origins can complete
the OIDC flow. Realm exports: Keycloak can export a realm's full config
(Admin Console → Realm Settings → Action → Partial/Full Export) for reproducible
redeployment — **[ do this and attach the export if your group wants to show it ]**.

### Q3.2 CS Role
Walk through `lab4_verifier.py`: fetch JWKS → match `kid` → verify RS256 signature (both
via PyJWT and manually via raw RSA math) → extract claims. Token refreshing: the refresh
token (Q2.1) is exchanged via the same `/token` endpoint with
`grant_type=refresh_token` to get a new access token without re-authenticating.

### Q3.3 Cyber Role
Residual threat vectors even after hardening:
- **Token theft** — if an access token is exfiltrated (XSS, malware, logging it by
  accident), it's valid until expiry regardless of who holds it; short expiry times limit
  the blast radius.
- **Refresh token hijacking** — refresh tokens are long-lived and powerful; if stolen, an
  attacker can mint fresh access tokens indefinitely. Mitigations: refresh token rotation
  (Keycloak can invalidate the old one each time a new one is issued), binding tokens to a
  client/device fingerprint, short refresh-token lifetimes.
- **JWKS endpoint trust** — the verifier trusts whatever `KEYCLOAK_URL` points at; if that
  URL were ever attacker-controlled (e.g., SSRF, DNS hijack) the attacker could serve their
  own keys. This is why hardcoding the realm URL (not reading it from the token) matters.
