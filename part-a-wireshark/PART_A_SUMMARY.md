# Part A (Wireshark TLS 1.3) — Done on Kali

Tasks A1–A5 are complete. Screenshots and notes are in `part-a-wireshark/` in this repo.

## What was done

- Captured a TLS 1.3 handshake + HTTP/2 traffic to `www.cloudflare.com` and decrypted it in Wireshark
  using `SSLKEYLOGFILE`.
- **Deviation from the original plan:** used `curl` instead of a GUI browser to generate the traffic.
  Kali's Firefox package links against the system `libnss3.so`, which is compiled *without*
  `SSLKEYLOGFILE` support at all (confirmed — the string isn't present in the library; not a config
  issue, a missing build feature). Mozilla's own binaries bundle a patched NSS that supports it; the
  distro package doesn't. Since the brief's actual deliverables (Q1.1–Q1.4) only require Wireshark
  screenshots — no browser screenshot — this doesn't affect grading, but worth a one-line mention if
  asked about it in the oral defense.
- First two capture attempts had to be discarded: one had stale/mismatched traffic from a 2-hour-old
  session, another captured *all* port-443 traffic on the machine (100+ unrelated connections, heavy
  packet loss) because the capture filter was just `tcp port 443`. The final clean capture used
  `host <cloudflare-ip> and tcp port 443`, forcing curl to connect to that exact IP with
  `--resolve`, which produced a small, clean single-session capture.

## Deliverables (in `part-a-wireshark/`)

| File | Shows |
|---|---|
| `01a_clienthello_sni.png` | ClientHello (frame 5) — SNI, renegotiation_info, server_name, ec_point_formats |
| `01b_clienthello_keyshare.png` | ClientHello (frame 5) — `key_share`: X25519MLKEM768, x25519 |
| `02_serverhello.png` | ServerHello (frame 7) — Cipher Suite `TLS_AES_256_GCM_SHA384`, key_share |
| `03_encrypted_extensions.png` | Frame 11, decrypted: Encrypted Extensions, Certificate, Certificate Verify, Finished |
| `04a_decrypted_http2_200ok.png` | Frame 27 — HTTP/2 `200 OK`, packet list view |
| `04b_decrypted_http2_stream.png` | Frame 27, expanded — `HyperText Transfer Protocol 2: Stream HEADERS ... 200 OK` |
| `notes.md` | Frame numbers, curves, cipher suite, and talking points for Q1.1–Q1.4 |

## Key findings for the report

- **Frame numbers (Q1.1):** ClientHello = 5, ServerHello = 7, Encrypted Extensions = 11.
- **Curves offered/chosen (Q1.2):** `X25519MLKEM768` (post-quantum hybrid: classical X25519 + ML-KEM-768,
  defends against "harvest now, decrypt later") and `x25519` (classical ECDHE).
- **Cipher suite:** `TLS_AES_256_GCM_SHA384`.
- **Static RSA absent in TLS 1.3 (Q1.2):** every TLS 1.3 cipher suite mandates ephemeral (EC)DHE, which
  is what provides forward secrecy — compromising the server's long-term key later can't decrypt past
  sessions.
- **Decryption (Q1.4):** loading `sslkeys.log` into Wireshark's TLS preferences turned frame 11 from an
  opaque record into decoded `Encrypted Extensions/Certificate/Finished`, and frame 27 into a visible
  HTTP/2 `200 OK` response.

## Still open

- `report/defense_questions.md` already has Q1.1–Q1.4 scaffolding in this repo — the frame
  numbers/curves/cipher suite above are ready to drop in.
- The raw capture file (`lab4_afd.pcapng`) is in `~/Documents/` on this Kali machine, not copied into
  the repo (gitignored anyway, and large) — move it manually if you want it archived.
- Part B (Keycloak) and Part C (JWT verifier) were already complete on the Ubuntu side per the handoff
  doc — untouched here.
