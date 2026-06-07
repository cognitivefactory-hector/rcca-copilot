# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

**M1 complete (trust backbone).** The domain model + sign-off state machine are built TDD and fully tested; **M2 (synthetic corpus + retrieval tools) is next.** The source of truth for design is the planning docs: `SPEC.md` (design spec), `PLAN.md` (milestones M0→M7), `DECISIONS.md` (decision record), and per-milestone specs under `docs/superpowers/specs/`. Read those before writing code.

Project shape: `config/` (Django project package: settings/urls/wsgi/asgi) + `rcca/` (the app) + `tests/` (pytest, top-level). Settings are environment-driven; `.env` (gitignored) feeds local dev, copied from `.env.example`.

**The state machine is the heart of the project — respect its boundary:**
- All section transitions go through `rcca/state.py` (`edit_section`, `approve_section`, `is_capa_ready`) so every change is logged to `AuditEvent`. Do not mutate `Section.state`/`current_text` directly in views or the agent — call the state functions.
- `Investigation.is_capa_ready` is a **derived property with no setter** — it's a function of section states, never stored. Keep it that way; that's what makes "you cannot force CAPA-ready" true.
- Models live in `rcca/models.py` (declarative); behavior lives in `rcca/state.py`. `CandidateCause`/`EvidenceRef` exist but are inert until the agent fills them in M3.
- Schema changes: one migration so far (`rcca/migrations/0001_initial.py`). Run `makemigrations` after model edits; CI runs `makemigrations --check`.

## What this project is

RCCA Copilot is an AI agent that drafts a structured 8D / 5-Why root-cause-and-corrective-action investigation from a manufacturing nonconformance. It is a **job-search portfolio project** with three deliverables of *equal weight* (`SPEC.md` §0):

1. The working app
2. `DECISIONS.md` — the decision record
3. A recorded whiteboard session

This matters for how you work here: the app alone is not the deliverable. The judgment behind the human-in-the-loop design is the point. When a decision is made during the build (model choice, export format, schema shape), record the reasoning in `DECISIONS.md` while it's still fresh — that is a first-class task, not cleanup.

## Non-negotiable design rules

These are the thesis of the project. Do not "simplify" them away — they are the reason the project exists, not incidental constraints.

1. **No autonomous filing — ever.** The agent drafts; it never closes or files a CAPA. (`SPEC.md` §4.4)
2. **Grounding rule (hard requirement).** Every candidate cause must carry a citation to a retrieved evidence item *or* be explicitly labeled `insufficient_evidence`. The agent must never assert an uncited root cause as confirmed. (`SPEC.md` §7)
3. **Evidence via tool use, not recall.** All evidence comes through the retrieval tools (`get_process_data`, `get_spec`, `search_prior_ncs`) so every claim is traceable. The model fetches; it does not remember.
4. **Sign-off gate.** Each section moves `Drafted → Engineer-edited → Approved`. `Investigation.is_capa_ready` is true *only* when all required sections are `Approved`. Export is blocked until then.
5. **Synthetic data only.** Hand-built, obviously fictional corpus. No real employer (TAT/MSI) NCs, data, specs, or recipes — ever. (`SPEC.md` §5)
6. **`ANTHROPIC_API_KEY` is never committed.** It lives in `.env` (gitignored) and host secrets.

## Build order (this sequencing is deliberate)

Build the **trust backbone before the AI.** The state machine and grounding enforcement are "the crown jewels" — the LLM is the easy part layered on top. The order from `PLAN.md`:

- **M1** — Domain model + sign-off state machine, **TDD**. Models: `Nonconformance`, `Investigation`, `Section` (D2/D3/D4/D5/D7), `CandidateCause`, `EvidenceRef`, `AuditEvent`. Tests first: export blocked unless all sections approved; editing a section logs an `AuditEvent`.
- **M2** — Synthetic corpus + the three retrieval tools (structured, citable records with **stable IDs** for reproducible demos).
- **M3** — Agent orchestration: Anthropic SDK, tool use wired to M2, structured output (JSON schema per 8D section), prompt caching of system prompt + method guide + corpus, grounding enforcement. **Invoke the `claude-api` skill here** for current SDK best practices.
- **M4–M7** — Workspace UI, export + audit trail, deploy, then the decision record + whiteboard recording.

## Testing strategy

- **The state machine and grounding rules get tested hard** — they encode the judgment. Other areas (UI) are demonstrated by the recording, not chased for coverage.
- **Mock the Anthropic API in unit tests.** Keep the one or two live integration runs out of CI to avoid burning tokens.
- **Adversarial fixture is mandatory:** an NC with no supporting evidence must yield `insufficient_evidence`, never a fabricated root cause. This single behavior is the core defense (`WHITEBOARD-DRILL.md` Q3).

## Planned stack & commands

Stack (from `README.md` / `SPEC.md` §6): Django + Postgres backend, Anthropic SDK (Claude) agent layer, Django templates + HTMX + Plotly frontend, Docker packaging, pytest + ruff + GitHub Actions CI. Model choice (`claude-opus-4-8` vs `claude-sonnet-4-6`) is an open question to resolve and record in `DECISIONS.md`.

Commands (M0 onward):

```bash
docker compose up --build              # run app + Postgres locally; serves http://localhost:8000
# Host 8000 taken? WEB_PORT=8001 docker compose up

docker compose exec web pytest -q      # run the test suite (needs the DB service up)
docker compose exec web pytest tests/test_smoke.py::test_healthz_ok   # a single test
docker compose exec web ruff check .   # lint

# Outside Docker (needs a local Postgres + .env): pytest -q · ruff check . · python manage.py <cmd>
```

Note: tests need Postgres, so run them against the `web` container (or a local Postgres). CI spins up a Postgres service container and runs `ruff check .` then `pytest -q`.

## Domain reference (8D structure)

The draft follows 8D sections, labeled by D-number so auditors recognize them (`SPEC.md` §7):
- **D2** Problem description — what/where/when/how big, measured vs. required
- **D3** Interim containment — quarantine, 100% inspect
- **D4** Root cause — 5-Why chains + Ishikawa / 6M (Man, Machine, Method, Material, Measurement, Environment); candidate causes proposed under each, cited
- **D5** Permanent corrective action — addresses the confirmed root cause, not the symptom
- **D7** Prevent recurrence — systemic change (control plan, SPC, poka-yoke, spec update)

Confidence is High/Med/Low per candidate cause, tied to evidence strength.
