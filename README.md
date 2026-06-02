# RCCA Copilot

An AI agent that drafts a structured root-cause-and-corrective-action (8D / 5-Why) investigation from a nonconformance and its process data — built so the engineer stays the decider and nothing reaches a CAPA without human sign-off.

> **Status:** scaffolded (spec + plan in place). Build follows `PLAN.md` (M0 → M9). Flagship-scale (~3–4 weeks).
> **Illustrative tool on synthetic data — not a quality system of record; a qualified engineer signs every CAPA.**

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of three equal deliverables: the app, a **Decision Record** ([`DECISIONS.md`](./DECISIONS.md)), and a recorded whiteboard session. A working demo no longer proves competence — the judgment behind it does. See [`SPEC.md`](./SPEC.md) §0.

## What it does
- Takes a nonconformance and drafts the **8D skeleton** (D2 problem, D3 containment, D4 root cause via **5-Why + Ishikawa/6M**, D5 corrective action, D7 prevent-recurrence).
- **Grounds every claim in cited evidence** — or marks it *"insufficient evidence."* Confidence per cause.
- **Human sign-off gate** on every section: `Drafted → Engineer-edited → Approved`. Nothing is CAPA-ready until every section is approved.
- Audit trail (agent proposal vs. engineer's final text) + clean 8D/CAPA export.

## Tech stack
- **Backend:** Django + Postgres
- **AI:** Anthropic SDK (Claude) — tool-use retrieval, structured 8D outputs, grounding/citations, prompt caching
- **Frontend:** Django templates + HTMX + Plotly
- **Packaging:** Docker · **Quality:** pytest + ruff + GitHub Actions CI

## Deployment
- **Live demo:** Dockerized Django app + Postgres on **Render**, fronted by **Cloudflare** (planned subdomain `rcca.hector-garza.com`).
- `ANTHROPIC_API_KEY` lives in `.env` (gitignored) / host secrets — **never committed.**
- Local run: one command via Docker (added in build step M0).

## Links (filled in as the build progresses)
- 🔗 Live demo: _TBD_
- 🧠 Decision record: [`DECISIONS.md`](./DECISIONS.md)
- 🎥 Whiteboard walkthrough: _TBD_

## Build
See [`PLAN.md`](./PLAN.md) — M0 (scaffold) → M9. The sign-off state machine and grounding/citation enforcement are built first; the agent goes on top.
