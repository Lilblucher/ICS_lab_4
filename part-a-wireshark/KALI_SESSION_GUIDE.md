# Kali Session Guide — Part A: Wireshark TLS 1.3 Capture

**Read this whole file before doing anything.** This is a handoff document for a Claude Code
session running on the Kali Linux partition, picking up Part A of ICS341 Lab 4 (Wireshark
TLS 1.3 packet analysis). Part B (Keycloak) and Part C (JWT verifier) are being done
separately on the Ubuntu partition and are **already complete** — nothing here touches them.

## Context

- Full brief: the user has `ICS341-Lab4.pdf` in the project root on the Ubuntu side; it may
  or may not be present in this Kali working directory. If it's not here, don't block on it —
  everything needed for Part A is in this file.
- This repo lives at `~/Documents/ICS_lab_4` on Ubuntu. On Kali, the user may be working from
  a copy, a shared folder, or a fresh clone — confirm the working directory with the user
  before writing files, and ask where they want Part A output saved if `part-a-wireshark/`
  doesn't already exist here.
- Deadline: the lab is due same-day (check with the user for the exact current date/deadline
  — don't assume). Move efficiently, but confirm anything destructive or ambiguous first.
- The user is a student, not deeply fluent in networking/crypto jargon — explain terms as you
  go (what a ClientHello is, what key_share means, etc.), don't just execute silently.

## Your job: Tasks A1–A5 from the brief

Goal: capture a real TLS 1.3 handshake in Wireshark, decrypt it using the browser's session
keys, and produce the screenshots + notes needed to answer Q1.1–Q1.4 in the report.

### Tools you'll need

- **Wireshark** (GUI packet analyzer) — for capture and inspection. This is a GUI app; you
  cannot drive it headlessly from a terminal. Guide the user through the GUI steps — they
  click, you tell them where and explain why.
- **A browser** (Firefox is pre-installed on Kali by default; Chrome if available) — to
  generate the HTTPS traffic to capture, launched from a terminal with `SSLKEYLOGFILE` set.
- **Terminal** — for setting the environment variable and verifying the key log file fills in.
- You do **not** need Docker, Python, or anything from Part B/C here.

### Step 1 — SSLKEYLOGFILE setup

This environment variable makes the browser dump TLS session secrets to a file as it browses,
so Wireshark can decrypt the capture afterward. Without it, TLS 1.3 traffic is just unreadable
ciphertext — this is by design (perfect forward secrecy), and it's *supposed* to be unreadable
unless you hold these session-specific keys.

**Important ordering gotcha:** the variable must be exported in the shell *before* the browser
process is launched from that shell. Setting it after the browser is already open does nothing
for that running instance — you must close the browser fully and relaunch it from a shell that
has the variable set.

Run:
```bash
export SSLKEYLOGFILE="$HOME/sslkeys.log"
echo 'export SSLKEYLOGFILE="$HOME/sslkeys.log"' >> ~/.bashrc
```

Then:
1. Close **all** open browser windows completely (check `ps aux | grep -i firefox` /
   `chrome` to confirm nothing's lingering).
2. Open a **new** terminal (so `.bashrc` is re-read and the export takes effect there too —
   or just reuse the terminal you just ran `export` in, since it already has the variable live
   for this session).
3. Launch the browser **from that terminal**: `firefox &` (or `google-chrome &` if using
   Chrome).
4. Visit any HTTPS site, then check: `cat ~/sslkeys.log` — you should see lines starting with
   something like `CLIENT_RANDOM ...` or similar key material. If the file is empty, the
   browser wasn't actually launched from a shell with the variable exported — stop and fix
   this before proceeding, since nothing downstream will decrypt without it.

### Step 2 — Capture the handshake (Task A1–A2)

1. Launch Wireshark (as root or with capture permissions — Kali's Wireshark is normally
   pre-configured for packet capture without needing `sudo`, but if the interface list is
   empty/greyed out, that's a permissions issue to flag to the user, not silently work around).
2. Select the active network interface (Wi-Fi or Ethernet — whichever shows traffic).
3. Set the **capture filter** (not display filter — this is set *before* starting capture, in
   the filter box next to the interface list) to: `tcp port 443`
4. Start the capture.
5. In the browser window that was launched with `SSLKEYLOGFILE` set, navigate to
   `https://www.cloudflare.com` and let it fully load.
6. Stop the capture once the page is loaded.

### Step 3 — Inspect ClientHello (Task A3, feeds Q1.1 and Q1.2)

1. In Wireshark's display filter bar (top, different from the capture filter used above),
   type: `tls` and press Enter. This filters the capture down to just TLS-layer packets.
2. Find the **ClientHello** frame (it's the very first TLS packet in the stream — client
   initiates). Note its **frame number** (shown in the leftmost column) — Q1.1 asks for this
   annotated explicitly.
3. Expand it (click the arrow / use the `+` in the packet details pane) down through:
   `Transport Layer Security > TLSv1.3 Record Layer: Handshake Protocol: Client Hello >
   Extension: supported_groups` and separately `Extension: key_share`.
4. **`supported_groups`** lists which elliptic curves the client is willing to use for key
   exchange (e.g. `x25519`, `secp256r1`, `secp384r1`). **`key_share`** is where the client
   actually sends its ephemeral public key material for one or more of those curves — this is
   the "front-loaded" part of TLS 1.3's 1-RTT design (compare to TLS 1.2, which needed an
   extra round trip to negotiate the curve before exchanging keys).
5. Screenshot this expanded view, clearly showing the frame number and both extensions.

### Step 4 — Inspect ServerHello (Task A4, feeds Q1.1)

1. Still filtered on `tls`, find the **ServerHello** frame (next TLS frame after ClientHello,
   or search for it — frame number again needed for Q1.1).
2. Expand to find:
   - **Cipher Suite** — the one the server chose from what the client offered (e.g.
     `TLS_AES_256_GCM_SHA384`). This is a TLS 1.3 cipher suite name: it bundles the bulk
     encryption algorithm (AES-256-GCM) with the hash used for the handshake's key derivation
     (SHA384) — TLS 1.3 simplified naming compared to TLS 1.2's much longer suite names, since
     TLS 1.3 dropped the ability to mix-and-match key exchange/signature algorithms into the
     suite name (key exchange is always (EC)DHE now, so it doesn't need naming).
   - **Server's `key_share`** — which curve the server picked and its own ephemeral public key.
3. Also locate the **Encrypted Extensions** frame nearby (Q1.1 asks for it too) — note that in
   TLS 1.3 this frame is, as the name says, already encrypted at this point, which is the whole
   point of Q1.3 (see below) — Wireshark will show it as an opaque "Application Data" style
   blob until you complete Step 5's decryption.
4. Screenshot ServerHello's cipher suite + key_share, with frame number annotated.

### Step 5 — Decrypt with sslkeys.log (Task A5, feeds Q1.4)

1. In Wireshark: **Edit → Preferences → Protocols → TLS**.
2. Find the field **"(Pre)-Master-Secret log filename"** and set it to the full path of the
   key log file: `/home/<username>/sslkeys.log` (use the actual home directory path, not a
   relative one).
3. Click OK/Apply.
4. Wireshark should now show plaintext **HTTP/2** data inside what were previously opaque
   "Application Data" TLS records — you may need to re-apply the `tls` filter or switch to
   `http2` to see it cleanly. The **Encrypted Extensions** frame from Step 4 should now also be
   readable.
5. Screenshot a decrypted HTTP/2 request/response — this is the Q1.4 screenshot requirement.

### What NOT to do

- Don't capture traffic beyond what's needed for this lab (no broad/continuous capture of
  unrelated personal browsing — minimize what's recorded, per good practice and because
  `.pcap` files are gitignored and shouldn't be committed anyway).
- Don't commit `sslkeys.log` or any `.pcap`/`.pcapng` file to git — these are already covered
  by the repo's root `.gitignore`, but double-check if working from a fresh clone that doesn't
  have it.
- Don't attempt to touch Keycloak, Docker, or the Python verifier from this session — that's
  all already done on Ubuntu and is out of scope here.

## What to bring back (deliverables)

Save these into `part-a-wireshark/` in whatever form is convenient (PNG screenshots, or
exported via Wireshark's File → Export Packet Dissections for text), named descriptively,
e.g.:
- `01_clienthello.png` (frame number visible, supported_groups + key_share expanded)
- `02_serverhello.png` (frame number visible, cipher suite + key_share expanded)
- `03_encrypted_extensions.png`
- `04_decrypted_http2.png`

Also jot down in a short notes file (`part-a-wireshark/notes.md`) — in plain language, as if
explaining to someone who hasn't seen the capture — the frame numbers for each of the three
frames Q1.1 asks about, and which curves appeared in `key_share`. This saves re-deriving it
later when writing up the report answers.

Once this is copied back to the Ubuntu-side repo (or this Kali working directory *is* the
repo, if shared/synced), the user will combine it with the already-drafted answers in
`report/defense_questions.md` (Q1.1–Q1.4 sections already have explanations written, just
need the real screenshots dropped in) to finish the report.

## Reminders for whoever's driving this session

- Confirm the working directory and whether `.gitignore` is present before writing any file.
- Explain jargon as you go (ClientHello, key_share, cipher suite, forward secrecy, 0-RTT) —
  the user explicitly asked for this, don't just execute silently.
- If Wireshark capture requires elevated permissions and fails, don't just add `sudo` blindly —
  flag it and explain the actual fix (usually being in the `wireshark`/`pcap` group, which
  Kali typically sets up out of the box).
- If something depends on a GUI click you can't perform yourself, say so clearly and tell the
  user exactly what to click — same approach used in the Ubuntu-side session for the Keycloak
  admin console.
