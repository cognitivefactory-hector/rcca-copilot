# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

**M4 complete (workspace UI).** The full pipeline is now clickable: pick a sample → the agent drafts a cited 8D → edit/approve each section → export unlocks only when CAPA-ready. **M5 (export document + audit-diff view) is next.** The source of truth for design is the planning docs: `SPEC.md` (design spec), `PLAN.md` (milestones M0→M7), `DECISIONS.md` (decision record), and per-milestone specs under `docs/superpowers/specs/`. Read those before writing code.

Project shape: `config/` (Django project package: settings/urls/wsgi/asgi) + `rcca/` (the app) + `tests/` (pytest, top-level). Settings are environment-driven; `.env` (gitignored) feeds local dev, copied from `.env.example`.

**The state machine is the heart of the project — respect its boundary:**
- All section transitions go through `rcca/state.py` (`edit_section`, `approve_section`, `is_capa_ready`) so every change is logged to `AuditEvent`. Do not mutate `Section.state`/`current_text` directly in views or the agent — call the state functions.
- `Investigation.is_capa_ready` is a **derived property with no setter** — it's a function of section states, never stored. Keep it that way; that's what makes "you cannot force CAPA-ready" true.
- Models live in `rcca/models.py` (declarative); behavior lives in `rcca/state.py`. `CandidateCause`/`EvidenceRef` exist but are inert until the agent fills them in M3.
- Schema changes: one migration so far (`rcca/migrations/0001_initial.py`). Run `makemigrations` after model edits; CI runs `makemigrations --check`.

**Corpus + retrieval tools (M2):**
- `rcca/corpus/` is the single source of truth for synthetic data — frozen dataclasses with **stable IDs** (`records.py` = types, `data.py` = authored instances). Fictional only; never add real employer data.
- `rcca/agent/tools.py` holds the pure retrieval tools (`get_spec`, `get_process_data`, `search_prior_ncs`). Every result carries a citation envelope (`source_type`, `source_id`, `locator`) so M3 builds `EvidenceRef` directly. The agent must reach the corpus **only** through these tools (fetch, not recall).
- **Answer key:** `SampleNC.planted_root_cause` is the planted true cause for judging the agent — test-only, never returned by any tool, never put in a prompt. A test (`test_no_tool_ever_returns_a_planted_root_cause`) enforces this; keep it passing.
- `NC-DEMO-004` / `LOT-MX-55` is the deliberately thin-evidence case for M3's "insufficient evidence" grounding test — its data reads near-nominal on purpose.

**Grounded agent (M3):**
- Two-phase orchestration in `rcca/agent/orchestrator.py`: Phase 1 is a manual tool-use loop (gather evidence via `tool_defs.TOOL_DEFS`/`handle_tool_use`); Phase 2 emits the structured 8D via `output_config.format` (schema in `schemas.py`). Model id comes from `settings.RCCA_MODEL` (default `claude-opus-4-8`); pass `client=`/`model=` to override (tests inject a fake).
- **`enforce_grounding(draft)` is the load-bearing guarantee** — it raises `GroundingError` on any cause with no evidence that isn't flagged `insufficient_evidence`. `run_investigation` always calls it. Don't weaken it; it's the "no naked claims" rule in code, and it's mutation-tested.
- `persist.py` writes a draft into the M1 models: `agent_proposed_text` + seeded `current_text`, sections stay `Drafted`, a `draft` AuditEvent (actor `agent`) per section, plus D4 `CandidateCause`/`EvidenceRef`. The agent never advances sign-off state — only the engineer does (M1 rule).
- **Anthropic API is mocked in CI** (`FakeAnthropicClient` in `tests/test_agent.py`). The real-model behavior is covered by `tests/test_agent_live.py`, which skips without `ANTHROPIC_API_KEY` (so it never runs in CI). Keep live calls out of CI to avoid burning tokens.
- SDK surface (Opus 4.8): adaptive thinking only (no `budget_tokens`), no `temperature`/`top_p`; structured outputs via `output_config.format`. If touching the agent and unsure about SDK details, invoke the `claude-api` skill.

**Workspace UI (M4):**
- Views in `rcca/views.py`, templates in `rcca/templates/rcca/`, design system in `rcca/static/rcca/app.css` (engineering-document aesthetic: Saira/Hanken Grotesk/JetBrains Mono, blueprint grid, semantic state colors). HTMX for edit/approve (swap the section-card partial; the readiness gate updates via `hx-swap-oob`). Plotly (CDN) charts the cited lot's process data.
- **Picking a sample auto-runs the agent once** (`start_sample`), then is idempotent — re-picking shows the existing investigation without re-running (the cost guard). The agent call needs `ANTHROPIC_API_KEY`; to view the workspace without a key, seed an investigation + `persist_draft` via `manage.py shell`.
- All section mutations go through `state.py` (edit/approve) — the views never touch `Section.state` directly. **Export is gated on `is_capa_ready`** (`export` view returns 403 until every section is approved); that gate is mutation-tested.
- View tests (`tests/test_views.py`) mock the agent (`monkeypatch rcca.views.run_investigation`). The M0 home smoke test moved DB connectivity to `/healthz` when home became the sample picker.

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
