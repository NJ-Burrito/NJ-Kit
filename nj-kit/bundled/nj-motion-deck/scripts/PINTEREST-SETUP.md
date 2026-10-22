# Pinterest API v5 — setup path (not executed; no account/app created)

No Pinterest credentials exist (`ls credentials/` — no `pinterest.env`). This is instructions
+ a script only, per the brief ("Do NOT create accounts or apps"). the owner runs the steps below
himself when he wants Pinterest sourcing; the Lead/worker never registers an app.

## Steps (the owner does these)

1. Sign in at https://developers.pinterest.com with the Pinterest account that will own the
   references board(s).
2. Register an app: https://developers.pinterest.com/docs/getting-started/set-up-app/ — set
   redirect URI, note the **App ID** and **App secret**.
3. New apps start in **Trial access** (self-serve, mostly read endpoints; content created is
   visible only to the creator — "Sandbox"). This is enough for read-only reference search.
   **Standard access** (higher limits, production) needs a separate review with a recorded
   OAuth-flow demo — skip this for a one-off research pull.
4. Request scopes `boards:read` and `pins:read` (read-only; no `pins:write`/`boards:write`
   needed for this use case).
5. Generate an OAuth token: https://developers.pinterest.com/docs/api/v5/oauth-token/ — either
   the full OAuth redirect flow, or a **test token** (Trial apps can issue one without wiring
   OAuth; expires in 24h — fine for a single research session).
6. Rate limits: Trial = per-day-per-app cap (check the current number on the Access Tiers page
   at request time — it changes); Standard = per-minute-per-user.
7. Save the token to `credentials/pinterest.env` (gitignored) as:
   ```
   PINTEREST_TOKEN=<token>
   ```

## Source

developers.pinterest.com: Access Tiers (docs/key-concepts/access-tiers/), Connect app
(docs/getting-started/set-up-app/), OAuth token (docs/api/v5/oauth-token/) — read 2026-09-25,
not independently corroborated against a second host (this doc is a setup guide, not a KB
`verified` claim; do not cite it as a KB entry without a second source).

## Script

`pinterest_search.py` (stdlib only — `urllib`, no `requests`) reads `PINTEREST_TOKEN` from
`credentials/pinterest.env`, calls `GET /v5/search/pins` with a query, prints
id/title/description/link/image URL per result. Exits 3 with a clear message if the token is
missing — verified this run (see receipt).
