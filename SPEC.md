# RCCA Copilot — Design Spec

**Project 2 of the Hector Garza portfolio.** Self-contained: everything needed to start this as its own repository is in this file and its companion `PLAN.md`. You do not need any other file from the `career/` folder to build this.

- **Owner:** Hector Garza · hectorg@smartxchain.com · hector-garza.com
- **Status:** Spec — ready to build
- **Suggested repo name:** `rcca-copilot`
- **One-liner:** An AI agent that drafts a structured root-cause-and-corrective-action (8D / 5-Why) investigation from a nonconformance and the process data behind it — built so the engineer stays the decider and nothing reaches a CAPA without human sign-off.

---

## 0. Read this first — what this project is *really* for

This is a job-search portfolio project, but it is **not** a "look, an LLM wrote a report" demo. In 2026 anyone can wrap an LLM in a form; that proves nothing about judgment. The hireable signal is **how you designed the human's role** — what you let the agent do, what you deliberately *withheld* from it, the failure mode you engineered against, and what changed in the work as a result.

So this project has **three deliverables of equal weight**:

1. **The working app** (hosted, clickable).
2. **A Decision Record** (`DECISIONS.md`) structured around the four questions below.
3. **A recorded whiteboard session** (5–8 min) where you defend the human-in-the-loop design against push-back.

A hiring manager who opens this repo should learn *how you think about putting AI into a regulated process*, not just that you can call an API.

---

## 1. The spine — four questions that make judgment portable

Every project in this portfolio is organized around these four questions. They appear here, in `DECISIONS.md`, and on the project's page at hector-garza.com. Fill them in *as you build*, while the reasoning is still alive.

> **1 · Situation** — What's happening, who's involved, the constraints, the facts you have and the facts that are *missing*. Context is where judgment begins.
>
> **2 · Decision** — The plausible paths, the one you took, and the credible options you *rejected*. Rejection shows what you refused to hand-wave.
>
> **3 · Risk** — What could go wrong, what you removed, and what you *consciously accepted*. Prevented losses count — name the bad outcome that didn't happen.
>
> **4 · Change** — What's different now: clearer, safer, faster. Connect the judgment to a real change in the work, not a diary entry.

### 1.1 First-draft answers for RCCA Copilot (defend/revise these on camera)

These are your starting position. The whiteboard session (§3) exists to pressure-test them.

- **Situation.** A nonconformance (NC) lands — say, anodize coating thickness below the spec floor on a lot. The engineer has to run an RCCA: investigate, find the true root cause, and write a corrective action that survives a NADCAP / customer audit. The work is slow (hours of digging through process logs, travelers, and prior NCs) and inconsistent (quality of the write-up depends on who's on shift). Facts you have: the NC, process data, the spec, prior NCs. Facts you're missing: a clean causal link — the data rarely *says* why; a human has to reason it.
- **Decision.** Build an **agent that drafts the investigation** (problem statement, 5-Why chains, Ishikawa/6M candidate causes, a proposed containment and corrective action) **with every claim grounded in a cited piece of evidence**, and a **mandatory human sign-off gate on every section** before anything becomes a CAPA. **You rejected the fully-autonomous "auto-file the CAPA" version on purpose** — in a regulated shop, an unsigned machine conclusion is a liability, not a feature. You also rejected a pure free-form chatbot: it must produce the *structured* 8D fields an auditor expects.
- **Risk.** The killer risk is a **confident, plausible, wrong root cause** that reads well and sails into a CAPA — then fails an audit or, worse, lets the real defect recur. Mitigation: the agent must **cite evidence for every cause or explicitly say "insufficient evidence,"** surface a confidence level, and **cannot advance a section the engineer hasn't approved**. "The model output didn't go into production without review." You consciously accept that this makes the tool slower than full autonomy — that's the right trade in a regulated process.
- **Change.** Investigation drafting drops from hours to minutes, every RCCA comes out in a consistent, audit-ready structure, and **accountability stays with the engineer** whose name is on the sign-off. The prevented loss: a bad corrective action that would have passed unnoticed and let the defect return.

---

## 2. Why this project (market fit)

- **Agentic AI is the 2026 manufacturing mandate** — but the credible framing everywhere (Gartner, the field) is *agents that act with a human keeping final approval.* This project is a textbook demonstration of that discipline.
- RCCA / CAPA / 8D is a universal pain in regulated manufacturing (aerospace, medical, auto). The buyer feels it.
- It directly backs a resume claim ("Developed AI-assisted NCA/RCCA tooling that drafts root-cause narratives and corrective actions") — a manager can *click and verify* it.
- **Your unfair advantage is rare and hard to fake:** you have *written* 8Ds, run the 5-Whys, and survived NADCAP and customer audits. Almost no AI engineer knows what a good CAPA looks like or why an auditor rejects one. The judgment in §1.1 is yours.

---

## 3. The staged whiteboard session (recorded deliverable)

**Format.** 5–8 minutes. Screen + voice (Loom, or OBS → MP4), at the "whiteboard" (a diagram of the agent loop, or the running app), defending the design while an adversary pushes back. Use a strong engineer friend, or answer the scripted challenges below on camera as if in an interview. Preserve the surviving reasoning in `DECISIONS.md`.

**The point is not to be right on the first take.** Show you can hold a sound line and update on a fair one — "learning in public without becoming mushy."

### 3.1 Adversarial challenge script (the push-back)

1. **"This is just a prompt wrapped around an LLM with a nice form. Where's the engineering?"**
   *(Defend the grounding + citation layer, the structured 8D schema, the tool-use retrieval, and the sign-off state machine. Distinguish "drafting" from "deciding.")*
2. **"If the engineer has to review every section anyway, what did you actually save? Maybe it's net slower."**
   *(Quantify: drafting + consistency + audit-readiness. Be honest about where it does *not* save time.)*
3. **"The LLM will hallucinate a root cause that sounds perfect. A tired engineer will rubber-stamp it. You've built a liability."**
   *(This is the core challenge. Defend: forced citations, "insufficient evidence" path, confidence display, no-advance-without-approval, and a UI that makes the evidence — not the prose — the thing being approved.)*
4. **"How would this pass a NADCAP audit? Auditors hate black boxes."**
   *(Defend traceability: every cause links to evidence; the human approver of record; an audit trail of what the agent proposed and what the engineer changed.)*
5. **"You trained/tested this on synthetic NCs you wrote. Real ones are messier and the data is dirtier. Why should I believe it?"**
   *(Name the gap honestly; describe what you'd validate first on real NCs and what could break.)*
6. **"Who is legally responsible when a corrective action fails — you, the tool, or the engineer?"**
   *(Defend the accountability design: the engineer signs, the tool assists; the sign-off gate exists precisely to keep responsibility human.)*

### 3.2 What the recording must show
- The **Situation → Decision → Risk → Change** arc (§1.1), in your words.
- A clear articulation of **what you refused to let the agent do** and why.
- At least one place you **revised** under push-back (or a crisp reason you held).
- A pointer to where the surviving reasoning lives (`DECISIONS.md`).

---

## 4. Product specification

### 4.1 Users
- **Primary:** a process/quality engineer running an RCCA on a nonconformance.
- **Demo viewer:** a hiring manager who must "get it" in 60 seconds and see that the human is in control.

### 4.2 Core features (MVP)
1. **NC intake.** A form (or pick a sample) capturing the nonconformance: part/lot, process, defect description, spec violated, measured vs. required.
2. **Evidence retrieval (tool use).** The agent pulls relevant context from a synthetic corpus: process data around the lot, the spec text, and prior similar NCs — via defined tools, not free recall.
3. **Structured investigation draft.** The agent produces the 8D skeleton (see §7): problem statement (D2), interim containment (D3), **5-Why chains** and an **Ishikawa / 6M cause map** (D4), proposed corrective action (D5), and prevent-recurrence notes (D7).
4. **Grounding & citations.** Every candidate cause and claim links to a specific piece of retrieved evidence, or is explicitly marked **"insufficient evidence."** A confidence indicator per cause.
5. **Human sign-off gate (the heart of it).** Each section has a state: `Drafted → Engineer-edited → Approved`. **Nothing can be marked "CAPA-ready" until every required section is Approved.** The engineer can edit any text; edits are tracked.
6. **Audit trail.** A record of what the agent proposed, what the engineer changed, and who approved — exportable.
7. **Export.** Produce a clean 8D / CAPA document (PDF or Markdown) with the approver's name and timestamp.

### 4.3 Screens
- **NC intake** → **Investigation workspace** (the 8D sections with draft/edit/approve controls, evidence panel, confidence) → **Review & export**.
- **About / Decision Record** (or link to hector-garza.com): the SDRC story + embedded whiteboard recording.

### 4.4 Explicit non-goals (YAGNI)
- **No autonomous filing.** The agent never closes a CAPA. By design.
- No integration with a real QMS/MES; synthetic corpus only.
- No fine-tuning a model; use a frontier model with tool use + grounding.
- No multi-user workflow/approvals chain beyond a single engineer sign-off.
- No authenticated multi-tenant SaaS; a simple demo session is enough.

---

## 5. Synthetic data (no employer IP — ever)

A small, hand-built corpus that is obviously fictional. **No TAT/MSI NCs, data, specs, or recipes.**

- **3–5 sample nonconformances** across processes (e.g., anodize thickness low; plating adhesion failure; etch over-cut), each with a short backstory and a "true" root cause you authored (so you can judge whether the agent finds it).
- **A synthetic process-data table** per lot (the kind of trend the cause would leave).
- **2–3 fake "spec" snippets** (generic requirement text — invent clause numbers).
- **A few prior NCs** so retrieval has something to find and the agent can spot recurrence.
- Ship fixed sample IDs so demos are reproducible.

> Building the corpus is also where *your* expertise shows: realistic NCs with believable-but-fictional causes is something only a domain expert can author. Note that in `DECISIONS.md`.

---

## 6. Architecture & stack

Matches the owner's stack (Django · Postgres · Docker) with Claude tool-use as the agent layer.

```
┌──────────────────────────────────────────────────────────┐
│  Browser — Investigation workspace                          │
│   • 8D sections with Draft / Edit / Approve state            │
│   • Evidence panel (citations) + confidence per cause        │
│   • Export (8D / CAPA) button                                │
└───────────────▲──────────────────────────┬──────────────────┘
                │ REST/HTMX                  │
┌───────────────┴──────────────────────────▼──────────────────┐
│  Backend — Django + Postgres                                  │
│   • Investigation state machine (Drafted→Edited→Approved)     │
│   • Agent orchestrator (Anthropic SDK, tool use)              │
│   • Tools: get_process_data(lot), get_spec(id),               │
│            search_prior_ncs(query)                            │
│   • Grounding/citation enforcement + confidence               │
│   • Audit-trail log; export renderer                          │
└───────────────────────────────────────────────────────────────┘
```

**Claude integration (decide details at build, then record them):**
- Use a current frontier model — **`claude-opus-4-8`** for best reasoning, or **`claude-sonnet-4-6`** to cut cost; pick and record why.
- **Tool use** for all evidence retrieval — the agent must fetch, not recall, so every claim is traceable.
- **Structured outputs** for the 8D fields (a JSON schema per section) so the UI can render and gate them.
- **Prompt caching** for the system prompt + RCCA/8D method guide + spec corpus (stable, reused across calls).
- **Citations**: each cause references the tool result it came from.

> When you build the Claude layer, follow Anthropic SDK best practices (prompt caching, tool use, structured outputs). If working in Claude Code, invoke the `claude-api` skill at that point.

**Libraries:** `anthropic` (SDK), Django, `psycopg`, a PDF/Markdown export lib. Keep it lean.

---

## 7. RCCA / 8D logic (the substance)

Ground the agent in the real method — this is where your domain credibility lives.

- **8D structure** the draft should follow (label sections by D-number so auditors recognize it):
  - **D2 Problem description** — what, where, when, how big, measured vs. required.
  - **D3 Interim containment** — stop the bleeding (quarantine lot, 100% inspect).
  - **D4 Root cause** — **5-Why** chains + **Ishikawa / 6M** categories: *Man, Machine, Method, Material, Measurement, Environment*. The agent proposes candidate causes under each, cited.
  - **D5 Permanent corrective action** — addresses the confirmed root cause, not the symptom.
  - **D7 Prevent recurrence** — systemic change (control plan, SPC, poka-yoke, spec update).
- **Grounding rule (hard requirement):** every candidate cause is either backed by a cited evidence item or labeled **"insufficient evidence — investigate."** The agent must never assert an uncited root cause as confirmed.
- **Confidence:** per candidate cause, a simple High/Medium/Low tied to evidence strength.
- **Sign-off state machine:** `Drafted → Engineer-edited → Approved`; `CAPA-ready` is computed only when all required sections are `Approved`.
- **Audit trail:** persist the agent's original proposal and the engineer's final text per section (diff is the evidence of human judgment).

---

## 8. Definition of Done

Portfolio-ready when **all three** exist and are linked together:

- [ ] **App** deployed at a public URL; pick a sample NC → agent drafts a cited 8D → engineer edits/approves → export a clean CAPA. The sign-off gate visibly blocks export until approved.
- [ ] **`README.md`** — what/why, one-command local run (Docker), screenshots/GIF, links to live demo + `DECISIONS.md` + whiteboard video, and the synthetic-data disclaimer.
- [ ] **`DECISIONS.md`** — the §1 four-question template completed, including the rejected autonomy option and the accepted speed trade-off.
- [ ] **Whiteboard recording** (5–8 min) linked from README and embedded on hector-garza.com.
- [ ] **Grounding works:** a viewer can click any cause and see its cited evidence (or the "insufficient evidence" flag).
- [ ] Tests pass for the state machine and the grounding/citation enforcement (see `PLAN.md`).

---

## 9. Hosting / deployment
- Containerize (`Dockerfile` + `docker-compose.yml` with Postgres).
- Host on Render / Railway / Fly.io / VPS (needs a real backend + an `ANTHROPIC_API_KEY` secret — never commit it).
- Optional subdomain: `rcca.hector-garza.com`; link from the resume's future "Selected Work" section.
- **Cost guard:** cache aggressively and cap tokens; this is a demo, not a service.

---

## 10. Repo bootstrap (how to start this as its own repo)

```bash
mkdir rcca-copilot && cd rcca-copilot
cp /path/to/02-rcca-copilot/SPEC.md .
cp /path/to/02-rcca-copilot/PLAN.md .
# seed: README.md, DECISIONS.md (paste template below), .gitignore (python + .env!), LICENSE (MIT)

git init && git add -A && git commit -m "chore: scaffold rcca-copilot (spec + plan)"
git branch -M main
gh repo create cognitivefactory-hector/rcca-copilot --public --source=. --remote=origin --push
```

> PUBLIC repo. **Never commit `ANTHROPIC_API_KEY`** — put it in `.env` (gitignored) and the host's secrets. Never commit real employer data.

### `DECISIONS.md` starter (paste into the new repo)

```markdown
# Decision Record — RCCA Copilot

## Situation
<the NC, the RCCA burden, facts you have, the missing causal link>

## Decision
<agent drafts + grounds + human sign-off gate; the autonomy option you REJECTED and why>

## Risk
<confident-wrong root cause; grounding/citation/confidence/gate mitigations; the speed trade you ACCEPTED>

## Change
<hours→minutes, consistent audit-ready output, accountability stays human; the prevented loss>

## Whiteboard session
- Recording: <link>
- What I refused to let the agent do: <…>
- What I revised under push-back: <…>
- What I held the line on, and why: <…>
```

---

## 11. Open questions to resolve in the plan
- Model choice: `claude-opus-4-8` vs `claude-sonnet-4-6` (record cost/quality reasoning).
- Django templates + HTMX vs. a small JS front end for the section state UI.
- Export format first pass: Markdown (fast) vs. PDF (prettier).
- How rich the synthetic corpus needs to be for the agent to find the planted root cause.
