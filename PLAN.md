# RCCA Copilot — Implementation Plan

Companion to `SPEC.md`. The build sequence: milestones, concrete tasks, acceptance criteria, and the definition of done. Self-contained — hand this repo to a fresh session and start.

- **Repo:** `rcca-copilot` (public, under `cognitivefactory-hector`)
- **Approach:** build the **state machine and grounding rules first** (the parts that make this trustworthy), then layer the agent on top. The LLM is the easy part; the discipline around it is the project.

---

## The spine (carry through every milestone)

Keep `DECISIONS.md` open and capture reasoning live:

> **Situation** · **Decision** (incl. what you *rejected* — the autonomy option) · **Risk** (incl. what you *accepted* — the speed trade) · **Change**.

The hardest decision (human sign-off gate + grounding over autonomy) is the spine of the **recorded whiteboard session** — see `SPEC.md` §3.

---

## Prerequisites
- Python 3.11+, Docker, a GitHub account (`gh` authenticated).
- An `ANTHROPIC_API_KEY` (in `.env`, gitignored — **never committed**).
- A host that runs a real backend + Postgres for the live demo (Render / Railway / Fly.io / VPS).

---

## Milestones

### M0 — Repo scaffold *(½ day)*
- [ ] Folder + `SPEC.md` + `PLAN.md`.
- [ ] `README.md` (stub), `DECISIONS.md` (paste template from `SPEC.md` §10), `.gitignore` (Python **+ `.env`**), `LICENSE` (MIT).
- [ ] Django project + Postgres via `docker-compose.yml`; `pyproject.toml`/`requirements.txt`; `Dockerfile`.
- [ ] Record the framework + model choice in `DECISIONS.md`.
- [ ] `gh repo create … --public --push`.
- **Acceptance:** `docker compose up` serves a page and connects to Postgres; repo on GitHub.

### M1 — Domain model + sign-off state machine (TDD) *(1–2 days)*
**Goal:** the trust backbone, before any AI.
- [ ] Models: `Nonconformance`, `Investigation`, `Section` (D2/D3/D4/D5/D7), `CandidateCause`, `EvidenceRef`, `AuditEvent`.
- [ ] Section state: `Drafted → Engineer-edited → Approved`. `Investigation.is_capa_ready` is true **only** when all required sections are `Approved`.
- [ ] **Tests first:** export/CAPA-ready is blocked unless every required section is approved; editing a section logs an `AuditEvent`.
- **Acceptance:** `pytest` green; you cannot mark CAPA-ready with any section unapproved.

### M2 — Synthetic corpus + retrieval tools *(1–2 days)*
**Goal:** something for the agent to ground in.
- [ ] Author 3–5 fictional NCs, each with a planted "true" root cause; synthetic process-data table per lot; 2–3 fake spec snippets; a few prior NCs. (See `SPEC.md` §5.)
- [ ] Implement tools: `get_process_data(lot)`, `get_spec(id)`, `search_prior_ncs(query)` — return structured, citable records with stable IDs.
- [ ] Tests: each tool returns the expected fixture; IDs are stable for reproducible demos.
- **Acceptance:** tools callable in isolation; corpus is obviously synthetic and disclaimed.

### M3 — Agent orchestration with tool use + grounding *(2–3 days)*
**Goal:** the agent drafts cited 8D content; **no uncited root cause may be asserted as confirmed.**
- [ ] Anthropic SDK integration: system prompt with the 8D/5-Why/Ishikawa method guide; **prompt-cache** the stable prompt + corpus; **tool use** wired to M2 tools; **structured outputs** (JSON schema per section).
- [ ] Grounding enforcement: every `CandidateCause` carries either an `EvidenceRef` or an explicit `insufficient_evidence` flag; assign High/Med/Low confidence.
- [ ] Tests: feed a sample NC → assert the agent calls the retrieval tools and that every returned cause is either cited or flagged (no naked claims). A "no evidence" NC yields "insufficient evidence," not a fabricated cause.
- **Acceptance:** `pytest` green; grounding rule holds on the adversarial "no evidence" fixture.
- **Note:** if building in Claude Code, invoke the `claude-api` skill here for current SDK best practices.

### M4 — Investigation workspace UI *(2–3 days)*
**Goal:** the clickable demo where the human is visibly in control.
- [ ] NC intake (form + "pick a sample").
- [ ] 8D section cards with **Draft / Edit / Approve** controls; an **evidence panel** showing each cause's citation; confidence badges.
- [ ] Export blocked until CAPA-ready; clear visual state.
- [ ] Footer disclaimer: "Simulated data; not affiliated with any employer. Drafting aid — a qualified engineer signs every CAPA."
- **Acceptance:** pick a sample → agent drafts → you edit + approve sections → export unlocks only when all approved.

### M5 — Export + audit trail *(1 day)*
- [ ] Render an 8D / CAPA document (Markdown first, PDF optional) with approver name + timestamp.
- [ ] Audit view: agent's original proposal vs. engineer's final text per section (the diff = evidence of human judgment).
- **Acceptance:** export produces a clean, auditor-recognizable 8D; audit trail shows what changed.

### M6 — Polish, README, deploy *(1 day)*
- [ ] `README.md`: what/why, one-command local run, screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video.
- [ ] Deploy with `ANTHROPIC_API_KEY` as a host secret; token cap + caching on; smoke-test in prod.
- [ ] Optional: point `rcca.hector-garza.com` at it.
- **Acceptance:** public URL works from a fresh browser; demo flow runs end-to-end on the deployed instance.

### M7 — Decision Record + Whiteboard session *(½ day)* — **do not skip; this is the differentiator**
- [ ] Complete `DECISIONS.md` (Situation/Decision/Risk/Change; the rejected autonomy; the accepted speed trade).
- [ ] Record the 5–8 min whiteboard session using the challenge script in `SPEC.md` §3.1 — especially challenge #3 (the confident-wrong root cause).
- [ ] Embed/link the recording in README and on hector-garza.com.
- **Acceptance:** a stranger can read `DECISIONS.md` + watch the video and explain *why* you refused to let the agent file a CAPA.

---

## Testing strategy
- **State machine + grounding are the crown jewels — test them hard.** They encode the judgment.
- Mock the Anthropic API in unit tests; use one or two live "integration" runs to sanity-check tool-calling and structured output (kept out of CI to avoid burning tokens).
- Adversarial fixture: an NC with no supporting evidence must yield "insufficient evidence," never a fabricated root cause.
- UI is demonstrated by the recording; don't chase UI coverage.

## Suggested repo layout
```
rcca-copilot/
├── README.md
├── SPEC.md
├── PLAN.md
├── DECISIONS.md
├── Dockerfile
├── docker-compose.yml
├── .env.example              # ANTHROPIC_API_KEY=... (real .env is gitignored)
├── manage.py / pyproject.toml
├── rcca/
│   ├── models.py             # NC, Investigation, Section, CandidateCause, EvidenceRef, AuditEvent
│   ├── state.py              # sign-off state machine + is_capa_ready
│   ├── agent/  orchestrator.py tools.py schemas.py prompts.py
│   ├── corpus/               # synthetic NCs, process data, specs, prior NCs
│   ├── export.py             # 8D / CAPA renderer
│   └── views.py / templates/
└── tests/  test_state.py test_grounding.py test_tools.py
```

## Risk register (project execution)
| Risk | Mitigation |
|---|---|
| Demo "wows" but the grounding is fake (prose only) | The grounding/citation tests are non-negotiable; clicking a cause must reveal real evidence. |
| Scope creep into a real QMS integration | Synthetic-only is in Non-Goals; hold it. |
| Over-claiming autonomy to look impressive | The whole thesis is *restraint*. Lead with the sign-off gate; say plainly what the agent can't do. |
| API cost runs away on the live demo | Prompt caching + token caps + a single demo session; consider a "run agent" button rather than auto-run. |
| Leaking `ANTHROPIC_API_KEY` or employer data | `.env` gitignored; secrets in host; synthetic corpus only. |
| Skipping M7 because the app "looks done" | M7 *is* the portfolio. The app without the decision record is exactly the "shiny artifact that stopped working." |

## Definition of Done
See `SPEC.md` §8 — all three deliverables (app, decision record, whiteboard recording) exist and are linked from the README, and the grounding rule demonstrably holds.
