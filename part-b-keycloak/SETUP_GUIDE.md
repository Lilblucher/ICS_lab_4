# Keycloak Admin Console Walkthrough (Tasks B1–B4)

These steps are click-through in the browser — I can't do them for you, but here's exactly
what to do and why, so you're not guessing. Do them in order.

## Task B1: Create the Realm

A **realm** in Keycloak is an isolated namespace — its own set of users, clients, and
settings, independent of any other realm (like a separate tenant). We don't use the
default "master" realm for apps, since that's reserved for administering Keycloak itself.

1. Go to http://localhost:8080 → log in with `admin` / `admin`.
2. Top-left dropdown (currently says "Keycloak" or "master") → **Create Realm**.
3. Realm name: `CybersecurityLab` → **Create**.

## Task B2: Create the Client

A **client** represents your application (`python-oidc-app`) registering itself with
Keycloak so it can request tokens on a user's behalf.

1. Left sidebar → **Clients** → **Create client**.
2. Client ID: `python-oidc-app` → Next.
3. **Enable "Client authentication"** (toggle ON). This matters: it means the client is
   "confidential" — it has a secret and must prove its identity when exchanging the
   authorization code for tokens (Task B4). Public clients (like a pure browser SPA) skip
   this, but our Python backend can safely hold a secret.
4. Authentication flow: leave "Standard flow" (Authorization Code Grant) checked — that's
   the flow this lab tests.
5. Next → **Valid redirect URIs**: `http://localhost:5000/callback`
   (This is where Keycloak sends the browser back to after login, carrying the
   authorization code. It must match exactly or Keycloak will refuse to redirect there —
   a deliberate anti-hijacking check.)
6. Save.
7. Go to the **Credentials** tab of this client → copy the **Client secret**. You'll need
   it for Task B4's curl command. **Don't commit this value to git** (it's covered by
   `.gitignore`, but don't paste it into any tracked file either).

## Task B3: Create the User

1. Left sidebar → **Users** → **Create new user**.
2. Username: `student1` → Create.
3. Go to the **Credentials** tab of this user → **Set password**.
4. Password: `Password123!` → turn **OFF** "Temporary" (otherwise Keycloak forces a
   password change on first login, which complicates the token flow for this lab) → Save.

## Task B4: Retrieve the Authorization Code, Then Exchange It

**Step 1 — get the code.** Paste this URL into your browser (adjust nothing except maybe
the port if you changed it):

```
http://localhost:8080/realms/CybersecurityLab/protocol/openid-connect/auth?client_id=python-oidc-app&response_type=code&scope=openid&redirect_uri=http://localhost:5000/callback
```

Log in as `student1` / `Password123!`. Keycloak will then try to redirect your browser to
`http://localhost:5000/callback?code=...&session_state=...` — **this will fail to load**
(nothing is listening on port 5000, we never built that part), and that's fine. Just copy
the `code=` value out of the browser's address bar before it errors out. Authorization
codes are single-use and short-lived (usually ~60 seconds), so move to Step 2 quickly.

**Step 2 — exchange the code for tokens.** Fill in your real client secret and the code
you just copied:

```bash
curl -d "client_id=python-oidc-app" \
  -d "client_secret=<YOUR_CLIENT_SECRET>" \
  -d "grant_type=authorization_code" \
  -d "code=<AUTH_CODE>" \
  -d "redirect_uri=http://localhost:5000/callback" \
  http://localhost:8080/realms/CybersecurityLab/protocol/openid-connect/token
```

The response is JSON containing `access_token`, `id_token`, `refresh_token`. Copy the
`access_token` value — that's the input to `lab4_verifier.py`:

```bash
cd ../part-c-jwt && source venv/bin/activate
python lab4_verifier.py "<ACCESS_TOKEN>"
```

If the code already expired (curl returns an error like `invalid_grant`), just repeat
Step 1 to get a fresh code — this is normal and expected, not a bug.
