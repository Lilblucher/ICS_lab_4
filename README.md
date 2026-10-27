# ICS341 Lab 4 — TLS 1.3 Packet Analysis & Keycloak OIDC Integration

Working directory for ICS341: Cybersecurity Principles, Lab 4 (Mulungushi University).
Full brief: [`ICS341-Lab4.pdf`](./ICS341-Lab4.pdf).

This repo holds the technical artifacts (scripts, configs, captures, screenshots) that
feed into the Moodle report — it is not the report itself.

## Layout

- `part-a-wireshark/` — SSLKEYLOGFILE setup script, Wireshark notes, screenshots (produced
  on the Kali partition, copied in afterward). **Never commit `sslkeys.log` or `.pcap` files**
  — they're gitignored.
- `part-b-keycloak/` — `docker-compose.yml` for the Keycloak IdP container.
- `part-c-jwt/` — Python JWT verifier and exploit demos.
  - `lab4_verifier.py` — fetches JWKS, verifies a real RS256 access token (Task B5).
  - `verify_hardened.py` — strict algorithm-whitelisting verifier (Task C2, hardened half).
  - `exploits/alg_none_attack.py` — alg:none forgery demo (Task C1).
  - `exploits/hs256_confusion_attack.py` — RS256→HS256 confusion demo (Task C2, attack half).
- `report/` — screenshots and draft answers to the defense questions (Q1.1–Q3.3), assembled
  into the final submission PDF.

## Quickstart

```bash
# Part B: start Keycloak
cd part-b-keycloak && docker compose up -d   # or: sudo docker compose up -d

# Part C: Python env
cd part-c-jwt
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# After completing Keycloak realm/client/user setup (admin console) and
# Task B4's curl token exchange, verify a real token:
python lab4_verifier.py <access_token>

# Run the exploit demos (alg_none works standalone; hs256 confusion needs
# Keycloak running, to fetch the real public key)
python exploits/alg_none_attack.py
python exploits/hs256_confusion_attack.py
```

## Status

- [ ] Part A: Wireshark capture (Kali) — not started
- [x] Part B: `docker-compose.yml` ready, Keycloak running
- [x] Part B: realm/client/user configured (`CybersecurityLab`, `python-oidc-app`, `student1`)
- [x] Part B: token exchange + `lab4_verifier.py` run against a real access token — verified
      via both PyJWT and manual RSA math
- [x] Part C: exploit scripts + hardened verifier written
- [x] Part C: both exploits run against live Keycloak — insecure path accepts the forged
      admin token, hardened `verify_strict()` rejects both
- [ ] Report drafted — defense-question skeleton in `report/defense_questions.md`,
      needs Part A screenshots + your group's role-allocation table
