# M6 Design — Polish, README, deploy

**Milestone:** M6 (`PLAN.md`). **Status:** approved 2026-06-07.

Make the app deployable and the repo legible. Most of M6 is config + docs; the
live deploy itself needs the owner's accounts and secrets, so this milestone ships
everything needed to deploy plus a click-by-click guide.

## Decisions (confirmed in session)

1. **render.yaml blueprint + DEPLOY.md.** Commit a Render blueprint (Docker web
   service + managed Postgres, secrets wired) and a step-by-step deploy guide
   incl. the Cloudflare subdomain. Owner runs it.
2. **Capture screenshots now** (seeded synthetic data, no API key) under
   `docs/media/`, embedded in the README.

## Production hardening

- **whitenoise** for static files (compressed manifest storage when `DEBUG=False`;
  plain storage in dev/CI so no collectstatic is required for tests).
- Settings: `SECURE_PROXY_SSL_HEADER` (Render/Cloudflare terminate TLS),
  and when `DEBUG=False` — `SECURE_SSL_REDIRECT`, secure cookies, HSTS.
  `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` already env-driven.
- Dockerfile prod CMD: `migrate` → `collectstatic --noinput` → gunicorn.

## render.yaml

A web service (`env: docker`) + a managed Postgres. Env vars: `ANTHROPIC_API_KEY`
(`sync: false` — set in dashboard), `DJANGO_SECRET_KEY` (`generateValue`),
`DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `RCCA_MODEL`, and `POSTGRES_*`
mapped `fromDatabase`.

## README

Rewrite the stub: what/why, the three equal deliverables, a screenshot strip
(home → workspace → audit → export), one-command local run, architecture +
milestones, the grounding/sign-off thesis, links (live demo TBD, `DECISIONS.md`,
whiteboard TBD), and the synthetic-data disclaimer.

## DEPLOY.md

Exact steps: fork/connect repo → Render blueprint → set `ANTHROPIC_API_KEY` →
first deploy → smoke test → point `rcca.hector-garza.com` via Cloudflare CNAME.
Cost guard notes (token caps, caching, single demo session).

## Tests

Light (M6 is config/docs): assert whitenoise is in `MIDDLEWARE` and `STATIC_ROOT`
is set; the rest is verified by a local gunicorn + collectstatic smoke run and the
screenshot capture.

## Out of scope / owner-run

The actual Render deploy, the Cloudflare DNS record, the real `ANTHROPIC_API_KEY`,
and the live-demo / whiteboard links (filled once deployed / recorded in M7).
