# M3 Design — Grounded Claude agent

**Milestone:** M3 (`PLAN.md`). **Approach:** TDD (Anthropic API mocked in CI).
**Status:** approved 2026-06-07.

The milestone where the thesis gets real: the agent drafts cited 8D content via
tool-use retrieval, and **no uncited root cause may be asserted as confirmed.**
Built on the M1 sign-off models and the M2 corpus/tools.

## Decisions (confirmed in session)

1. **Model default `claude-opus-4-8`** (SPEC §11 locked). Orchestration is
   model-agnostic — id read from `settings.RCCA_MODEL`, env-overridable; sonnet
   is a one-line swap. Opus chosen for the D4 root-cause reasoning that is the
   demo's signal; cost controlled via prompt caching + token caps.
2. **Two-phase (gather → emit).** Phase 1 is a manual agentic tool-use loop that
   gathers cited evidence; Phase 2 is one structured-output call that emits the
   8D JSON. Clean contracts, each phase independently mockable.
3. **Return draft + persist to DB.** The orchestrator returns a pure
   `InvestigationDraft`; a separate `persist_draft` writes it into the M1 models.

## Config

`RCCA_MODEL = os.environ.get("RCCA_MODEL", "claude-opus-4-8")` in settings.

## Module layout (`rcca/agent/`)

- `tools.py` *(M2)* — the three retrieval functions over the corpus.
- `tool_defs.py` — Anthropic tool definitions (name / description /
  `input_schema`) for `get_process_data` / `get_spec` / `search_prior_ncs`, plus
  a name→callable dispatch. A tool `LookupError` becomes an `is_error`
  tool_result so the model can recover rather than crashing the loop.
- `prompts.py` — the system prompt: the 8D / 5-Why / Ishikawa-6M method guide and
  the **hard grounding rule** (every candidate cause cites tool-retrieved
  evidence *or* is flagged `insufficient_evidence`; never assert an uncited
  cause; fetch via tools, do not recall). Built as a cache-controlled block.
- `schemas.py` — the JSON schema for the structured 8D output, and the
  `InvestigationDraft` / `DraftSection` / `DraftCause` / `DraftEvidence`
  dataclasses, plus `parse_draft(data)`.
- `orchestrator.py` — `run_investigation(nc, *, client=None, model=None)` and
  `enforce_grounding(draft)`.
- `persist.py` — `persist_draft(investigation, draft)`.

## Orchestrator flow

```
run_investigation(nc, *, client=None, model=None) -> InvestigationDraft
  client = client or anthropic.Anthropic()
  model  = model or settings.RCCA_MODEL
  system = [cache-controlled SYSTEM_PROMPT block]
  messages = [user: rendered NC intake]

  # Phase 1 — gather (manual agentic loop)
  loop:
    resp = client.messages.create(model, system, tools=TOOL_DEFS, messages,
                                   thinking={"type":"adaptive"},
                                   output_config={"effort":"high"}, max_tokens=…)
    if resp.stop_reason != "tool_use": break
    append assistant resp.content
    for each tool_use block: dispatch → tool_result (is_error on LookupError)
    append user tool_results

  # Phase 2 — emit (structured output)
  append assistant resp.content; append user EMIT_INSTRUCTION
  final = client.messages.create(model, system, messages,
                                 output_config={"format":{"type":"json_schema",
                                                          "schema": INVESTIGATION_SCHEMA}},
                                 max_tokens=…)
  draft = parse_draft(json.loads(<text block of final>))
  enforce_grounding(draft)   # raises GroundingError on a naked claim
  return draft
```

Opus 4.8 surface: adaptive thinking only (no `budget_tokens`), no sampling
params. Structured outputs work with extended thinking; read the response's text
block for the JSON. Non-streaming `max_tokens` ~16000.

## Structured 8D schema (output_config.format)

Object with: `d2_problem`, `d3_containment`, `d4_root_cause_summary`,
`candidate_causes[]`, `d5_corrective_action`, `d7_prevent_recurrence` (all
required, `additionalProperties:false`). Each candidate cause:
`category` (6M enum), `description`, `confidence` (high/medium/low enum),
`insufficient_evidence` (bool), `evidence[]` of
`{source_type, source_id, locator, excerpt}`.

## Grounding enforcement

`enforce_grounding(draft)` raises `GroundingError` for any candidate cause that
has an empty `evidence` list **and** `insufficient_evidence` is false — the
"no naked claims" guarantee, in code, not just in the prompt. Cited causes and
explicitly-insufficient causes pass.

## Persistence

`persist_draft(investigation, draft)`:
- For each D-section: set `agent_proposed_text`, seed `current_text` with the
  draft, keep state `Drafted`, log a `draft` AuditEvent (actor `agent`,
  `text_snapshot` = the proposal) — this is the "what the agent proposed" side of
  the audit trail.
- For each candidate cause: create a `CandidateCause` under the D4 section and an
  `EvidenceRef` per cited evidence item.

## Tests

`tests/test_agent.py` + `tests/test_grounding.py`, using a `FakeAnthropicClient`
that returns scripted responses (tool_use turn → end_turn → structured-JSON
emit). Mock the API in CI (per `PLAN.md`).

- The Phase-1 loop **calls the retrieval tools** — the tool_result fed back
  carries a real corpus `source_id` (e.g. `PD-LOT-AN-42`).
- A tool `LookupError` produces an `is_error` tool_result, not a crash.
- `enforce_grounding` **rejects a naked claim** and **accepts** cited /
  `insufficient_evidence` causes.
- **Adversarial:** the thin-evidence NC path yields a cause with
  `insufficient_evidence=true` and no fabricated cited cause — grounding passes.
- `parse_draft` maps schema JSON into the dataclasses.
- `persist_draft` writes `agent_proposed_text`, seeds `current_text`, keeps state
  `Drafted`, creates `CandidateCause` + `EvidenceRef`, and logs a `draft`
  AuditEvent.
- One **live** integration test (`tests/test_agent_live.py`) on `NC-DEMO-001`,
  `@pytest.mark.skipif(not ANTHROPIC_API_KEY)` — runs the real client, asserts
  tools were called and grounding holds. Naturally excluded from CI (no key).

## Out of scope for M3

UI, intake / "pick a sample", export, audit-diff view (M4–M5). The model's real
find-the-cause / insufficient-evidence behavior is shown by the live test and the
whiteboard demo; CI tests the mechanism.
