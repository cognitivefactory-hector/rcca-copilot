# Deploy automation

Two ways to deploy (full walkthrough in [`../DEPLOY.md`](../DEPLOY.md)):

## A. Dashboard (no API keys leave your control)
Render → New → Blueprint → connect the repo (`render.yaml` is read automatically),
Apply, set `ANTHROPIC_API_KEY` in the service's Environment tab. Cloudflare: add a
`rcca` CNAME to the Render target. ~5–10 min.

## B. API-driven (these scripts)
For when you want it run for you. The Render CLI can only *list* services, so
creation goes through the REST API — which needs a key.

1. Create `deploy/.secrets` (gitignored — never committed):
   ```
   RENDER_API_KEY=rnd_...           # Render → Account Settings → API Keys
   ANTHROPIC_API_KEY=sk-ant-...
   # for DNS, after the service exists:
   CLOUDFLARE_API_TOKEN=...         # scoped: Zone.DNS:Edit on hector-garza.com
   RENDER_TARGET_HOST=rcca-copilot-xxxx.onrender.com
   ```
2. Provision Render (find-or-create Postgres + web service, set env, deploy, poll):
   ```
   python deploy/render_deploy.py
   ```
3. Point the subdomain:
   ```
   python deploy/cloudflare_dns.py
   ```

Both scripts are idempotent and read secrets from `deploy/.secrets` or the
environment. Standard library only — no extra deps.
