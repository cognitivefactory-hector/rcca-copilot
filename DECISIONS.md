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
