# Decision Record — RCCA Copilot

The four questions that make judgment portable. These are **first-draft answers** (from `SPEC.md` §1.1) — pressure-test and revise them in the recorded whiteboard session, then keep what survives.

## Situation
A nonconformance lands — say, anodize coating thickness below the spec floor on a lot. The engineer has to run an RCCA: investigate, find the true root cause, and write a corrective action that survives a NADCAP / customer audit. The work is slow (hours digging through process logs, travelers, and prior NCs) and inconsistent (quality depends on who's on shift). Facts I have: the NC, process data, the spec, prior NCs. Facts I'm missing: a clean causal link — the data rarely *says* why; a human has to reason it.

## Decision
An **agent that drafts the investigation** (problem statement, 5-Why chains, Ishikawa/6M candidate causes, proposed containment and corrective action) **with every claim grounded in a cited piece of evidence**, and a **mandatory human sign-off gate on every section** before anything becomes a CAPA.
**Rejected:** the fully-autonomous "auto-file the CAPA" version (an unsigned machine conclusion is a liability in a regulated shop); and a pure free-form chatbot (it must produce the *structured* 8D fields an auditor expects).

## Risk
The killer risk is a **confident, plausible, wrong root cause** that reads well and sails into a CAPA — then fails an audit or lets the real defect recur. Mitigation: the agent must **cite evidence for every cause or explicitly say "insufficient evidence,"** surface a confidence level, and **cannot advance a section the engineer hasn't approved.** "The model output didn't go into production without review."
**Consciously accepted:** this makes the tool slower than full autonomy — the right trade in a regulated process.

## Change
Investigation drafting drops from hours to minutes, every RCCA comes out in a consistent audit-ready structure, and **accountability stays with the engineer** whose name is on the sign-off. The prevented loss: a bad corrective action that would have passed unnoticed and let the defect return.

## Whiteboard session
- Recording: _TBD_
- What I refused to let the agent do: _close a CAPA; assert an uncited root cause._
- What I revised under push-back / held the line on: _…_

---

## Engineering decisions (recorded as built)
- **Backend:** Django + Postgres — one stack across the portfolio.
- **AI:** Anthropic SDK; tool-use for evidence retrieval (the agent fetches, doesn't recall, so claims are traceable); structured output per 8D section; prompt caching of the method guide + corpus; citations per cause.
- **Trust backbone built first:** the `Drafted → Edited → Approved` state machine and the grounding rule (cite or "insufficient evidence") — before the agent.
- **Host:** Render (Dockerized + Postgres) behind Cloudflare. `ANTHROPIC_API_KEY` never committed.

### M0 — scaffold (recorded as built)
- **Runtime:** Python 3.12, Django 5.1, Postgres 16, `psycopg` 3 (binary). `django-htmx` in from the start so the M4 section-state UI has its middleware ready.
- **Project shape:** `config/` project package + a single `rcca/` app; settings are environment-driven (12-factor) so the same image runs locally and on Render. `python-dotenv` loads `.env` in dev; the host injects real env vars in prod.
- **Local run:** one command — `docker compose up` brings up Postgres + the web app, runs migrations, and serves on `:8000`. A `/healthz` endpoint and the home page both assert live DB connectivity (the M0 acceptance criterion).
- **Quality gate:** `pytest` + `ruff` wired into GitHub Actions CI against a Postgres service container. **No `ANTHROPIC_API_KEY` in CI** — the agent gets mocked in unit tests (per `PLAN.md` testing strategy), so live API calls never run in CI.
- **Model choice (default, revisit at M3):** orchestration will be written model-agnostic (model id read from config). Default to **`claude-sonnet-4-6`** for the cost-capped public demo (`SPEC.md` §9), with **`claude-opus-4-8`** as the drop-in option when D4 root-cause reasoning needs the extra depth. Rationale belongs on camera; this is the starting position, not a locked call. *(Open question from `SPEC.md` §11.)*

### M1 — domain model + sign-off state machine (recorded as built)
Built TDD; full design + transition table in `docs/superpowers/specs/2026-06-07-m1-state-machine-design.md`.
- **All transitions funnel through `rcca/state.py`** so every change writes an `AuditEvent` — the audit trail is a side effect of the only path that can change a section, not something callers must remember to do.
- **`is_capa_ready` is derived, never stored** (no setter). CAPA-readiness is purely a function of section states, so it cannot be forced — this is the mechanism behind "nothing reaches CAPA without sign-off."
- **Editing an Approved section reverts it** to `Engineer-edited` and clears the approver. Approved text can never silently change, and readiness self-corrects the instant any section is touched.
- **All five sections (D2/D3/D4/D5/D7) required**; approver captured as a free-text name + timestamp (no auth — a demo session is enough, `SPEC.md` §4.4).
- **Tests validated by mutation:** after the suite went green, each invariant (revert, empty-text guard, no-op re-approve, `is_capa_ready`) was broken to confirm a test caught it — guarding against tests that pass for the wrong reason.

### M2 — synthetic corpus + retrieval tools (recorded as built)
Built TDD; full design in `docs/superpowers/specs/2026-06-07-m2-corpus-tools-design.md`.
- **Static Python corpus, pure-function tools.** The corpus (`rcca/corpus/`) is frozen dataclasses with stable IDs; the tools (`rcca/agent/tools.py`) are pure functions over it. Reproducible demos, isolation-testable, and no DB coupling — the agent fetches evidence rather than recalling it.
- **The answer key is structurally isolated.** Each NC's planted true root cause lives only on `SampleNC`, which no tool returns; a test asserts no tool result ever leaks it. This is what lets me honestly judge whether the agent *found* the cause vs. was handed it — the backbone of the M3 grounding claim.
- **A deliberately thin-evidence NC** (near-nominal data) is authored now so M3's "insufficient evidence, not a fabricated cause" behavior can be demonstrated on real data.
- **Citation envelope on every result** (`source_type`/`source_id`/`locator`) so grounding in M3 maps a tool result straight to an `EvidenceRef`. Prior-NC root causes are legitimately citable (closed NCs); recurrence is an intended signal, distinct from the current NC's hidden answer key.
