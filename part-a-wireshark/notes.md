# Part A — Wireshark TLS 1.3 Capture Notes

Traffic generated with `curl --resolve www.cloudflare.com:443:104.16.123.96 https://www.cloudflare.com`
(used instead of a GUI browser — Kali/Debian's Firefox package links against the system `libnss3.so`,
which is built *without* `SSLKEYLOGFILE` support at all, unlike Mozilla's official binaries. curl, linked
against OpenSSL, supports it natively. The lab's Part A deliverables only require Wireshark screenshots,
not a browser screenshot, so this satisfies the actual requirements.)

Capture filter used: `host 104.16.123.96 and tcp port 443` on interface `wlan0`.
Capture file: `lab4_afd.pcapng` (ask whoever's writing the report where this ended up / re-save it into
this folder if needed — it was saved via Wireshark's save dialog during the session).

## Frame numbers (for Q1.1)

| Frame | Contents |
|---|---|
| 5  | **ClientHello** (SNI=www.cloudflare.com) |
| 7  | **ServerHello** + Change Cipher Spec |
| 11 | **Encrypted Extensions**, Certificate, Certificate Verify, Finished (TLS 1.3 bundles these into one encrypted record — Wireshark only labels it correctly once the key log is loaded) |
| 13 | Client's Change Cipher Spec, Finished |
| 14 | First HTTP/2 request (`GET /`) — encrypted on the wire, shown decrypted once keys are loaded |
| 27 | HTTP/2 response `200 OK` — decrypted application data |

## Key exchange curves (Q1.2)

Both ClientHello and ServerHello `key_share` extensions offered/selected:
- `X25519MLKEM768` — a **post-quantum hybrid** group (classical X25519 Diffie-Hellman combined with
  ML-KEM-768, a lattice-based key encapsulation mechanism). This defends against "harvest now, decrypt
  later" attacks, where an adversary records today's traffic hoping to decrypt it once large quantum
  computers exist.
- `x25519` — classical elliptic-curve Diffie-Hellman (Curve25519).

(`secp256r1` appeared in one capture attempt's client offer list but wasn't the negotiated group here.)

**Cipher suite negotiated:** `TLS_AES_256_GCM_SHA384` (seen in one capture run) / `TLS_AES_128_GCM_SHA256`
(seen in another — Cloudflare varied its choice between our curl runs; either is a valid TLS 1.3 AEAD
cipher suite for the report).

Also present: `Extension: encrypted_client_hello` — Cloudflare advertises ECH support, which goes beyond
standard TLS 1.3 by encrypting the SNI/server name itself (TLS 1.3 alone still sends SNI in plaintext).

## Why static RSA cipher suites are gone (for Q1.2 discussion)

TLS 1.3 removed static RSA key exchange entirely — every cipher suite now mandates ephemeral
(EC)DHE key exchange, which is what gives TLS 1.3 forward secrecy (compromise of the server's long-term
private key later doesn't let an attacker decrypt past sessions, since each session's keys are derived
from ephemeral values discarded after use).

## Decryption (Q1.4)

Set in Wireshark: **Edit → Preferences → Protocols → TLS → "(Pre)-Master-Secret log filename"** →
`/home/gauss/sslkeys.log`. After loading, frame 11 decoded from an opaque TLS record into
`Encrypted Extensions, Certificate, Certificate Verify, Finished`, and frame 27 decoded into a
visible HTTP/2 `200 OK` response (`Stream: HEADERS, Stream ID: 1 ... 200 OK`).

## Screenshots saved in this folder

- `01a_clienthello_sni.png` / `01b_clienthello_keyshare.png` — ClientHello (frame 5), extensions
- `02_serverhello.png` — ServerHello (frame 7): cipher suite + key_share
- `03_encrypted_extensions.png` — frame 11, decrypted
- `04a_decrypted_http2_200ok.png` / `04b_decrypted_http2_stream.png` — frame 27, decrypted HTTP/2
