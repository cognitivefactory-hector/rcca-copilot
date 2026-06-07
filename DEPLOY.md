# Deploy — RCCA Copilot

Dockerized Django + managed Postgres on **Render**, optionally fronted by
**Cloudflare** at `rcca.hector-garza.com`. The repo ships a Render blueprint
([`render.yaml`](./render.yaml)); the only secret you set by hand is
`ANTHROPIC_API_KEY`.

Prereqs: a Render account, this repo on GitHub, an `ANTHROPIC_API_KEY`, and (for
the subdomain) the `hector-garza.com` zone in Cloudflare.

## 1. Create the services from the blueprint

1. Render Dashboard → **New** → **Blueprint**.
2. Connect this GitHub repo. Render reads `render.yaml` and proposes a **web
   service** (`rcca-copilot`, Docker) + a **Postgres database** (`rcca-db`).
3. **Apply**. The blueprint wires `DATABASE_*` from the database, generates
   `DJANGO_SECRET_KEY`, and sets `DJANGO_DEBUG=False`, `RCCA_MODEL`,
   `DJANGO_ALLOWED_HOSTS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`.

## 2. Set the one secret

Web service → **Environment** → add **`ANTHROPIC_API_KEY`** = your key
(`render.yaml` marks it `sync: false`, so it is never read from the repo). Save —
Render redeploys.

## 3. First deploy

The container runs `migrate` → `collectstatic` → `gunicorn` automatically (see
the Dockerfile `CMD`). Watch the deploy logs until it's live; Render uses
`/healthz` as the health check.

## 4. Smoke-test in prod

- `https://rcca-copilot.onrender.com/healthz` → `{"status":"ok","db":true}`.
- Open `/`, pick a sample, confirm the agent drafts a cited 8D, edit + approve a
  section, approve all, and export the `.md`. (First request after idle is slow —
  Render free tier cold-starts; the agent call also takes ~10–30s.)

## 5. (Optional) Cloudflare subdomain

1. Render web service → **Settings** → **Custom Domains** → add
   `rcca.hector-garza.com`. Render shows a target hostname.
2. Cloudflare → `hector-garza.com` zone → **DNS** → add a **CNAME**
   `rcca` → the Render target. Proxy **on** (orange cloud) is fine — TLS is
   terminated upstream and the app trusts `X-Forwarded-Proto`.
3. Wait for Render to issue the cert; verify `https://rcca.hector-garza.com`.
4. The blueprint already lists both hosts in `DJANGO_ALLOWED_HOSTS` /
   `DJANGO_CSRF_TRUSTED_ORIGINS`; if you use a different host, update those env
   vars on the web service.

## Cost guard (it's a demo, not a service)

- Prompt caching (system prompt + method guide) and a `max_tokens` cap are on.
- The agent runs **once per investigation** — re-picking a sample shows the
  existing draft instead of re-calling the model.
- Consider keeping the demo to a single shared session, or swap
  `RCCA_MODEL=claude-sonnet-4-6` to cut per-run cost.

## After deploy

Fill the live-demo link in [`README.md`](./README.md) and on hector-garza.com,
then record the whiteboard session (M7).
