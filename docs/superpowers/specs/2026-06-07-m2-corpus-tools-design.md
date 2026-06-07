# M2 Design — Synthetic corpus + retrieval tools

**Milestone:** M2 (`PLAN.md`). **Approach:** TDD. **Status:** approved 2026-06-07.

Something for the agent to ground in (M3). The agent must *fetch* evidence via
tools, never recall it — so the corpus is real, structured, citable data with
stable IDs, and the tools are the only way to reach it.

## Decisions (confirmed in session)

1. **Static Python corpus, pure-function tools.** The corpus lives in
   `rcca/corpus/` as frozen dataclasses — the single source of truth, no DB.
   Tools are pure functions over it: reproducible, testable in isolation, and
   the agent's evidence reads straight from the corpus. (DB seeding for the
   "pick a sample" demo is M4.)
2. **3 NCs + 1 thin-evidence case.** Three clean NCs (anodize thickness low,
   plating adhesion fail, etch over-cut) each with a planted true root cause,
   plus one deliberately thin-evidence NC so M3's "insufficient evidence" test
   has real data to bite on.

## Corpus (`rcca/corpus/`)

Frozen, JSON-serializable dataclasses with stable IDs.

- **`SampleNC`** — intake fields (`nc_id`, `title`, `part_number`, `lot`,
  `process`, `defect_description`, `spec_violated` → a `Spec.spec_id`,
  `measured_value`, `required_value`) **plus `planted_root_cause`**. The planted
  cause is the **answer key**: test-only, never returned by any tool, never fed
  to the agent. One NC's data is intentionally thin (no clear causal signal).
- **`Spec`** — `spec_id`, `title`, invented `clause`, `text`, measurable
  `requirement`.
- **`ProcessDataRow`** — `row_id` (stable; the citation locator), `timestamp`
  (authored string, not real-time), `parameter`, `value`, `note`.
- **`ProcessData`** — `source_id`, `lot`, `process`, `rows: tuple[...]`.
- **`PriorNC`** — `nc_id`, `title`, `process`, `defect_description`,
  `root_cause` (documented — legitimately citable, unlike the current NC's
  hidden answer key), `corrective_action`, `keywords: tuple[str, ...]`.

A `DISCLAIMER` constant states the corpus is fictional; NC IDs are obviously
synthetic.

## Tools (`rcca/agent/tools.py`)

Pure functions over the corpus. Every result carries the citation envelope
(`source_type`, `source_id`, `locator`) so M3 builds `EvidenceRef` directly.

- `get_process_data(lot)` →
  `{source_type: "process_data", source_id, lot, process, rows: [{locator: row_id, timestamp, parameter, value, note}, ...]}`
- `get_spec(spec_id)` →
  `{source_type: "spec", source_id, locator: clause, title, clause, text, requirement}`
- `search_prior_ncs(query)` → ranked list of
  `{source_type: "prior_nc", source_id, locator: "root_cause", title, defect_description, root_cause, corrective_action, score}`
  via simple keyword/substring matching (no embeddings — YAGNI for a demo).

Behavior: unknown lot / spec id → `LookupError`. No search match → `[]`. Search
ordering is deterministic (stable sort by score then id) for reproducible demos.

## Tests first (`tests/test_tools.py`)

- Each tool returns the expected record for known fixtures.
- **Stable IDs:** specific known IDs (e.g. `SPEC-AN-7`, a known lot) resolve —
  demos are reproducible.
- Unknown lot/spec → `LookupError`; empty/nonsense query → `[]`;
  search ordering is deterministic.
- **Corpus integrity:** every `SampleNC.spec_violated` resolves to a real
  `Spec`; every `SampleNC.lot` has `ProcessData`.
- **JSON-serializable:** `json.dumps(tool_result)` succeeds for every tool.
- **Answer-key leak guard:** no tool result ever contains any
  `SampleNC.planted_root_cause` text — the agent cannot be handed the answer.
- A synthetic-data disclaimer is present.

## Out of scope for M2

The Claude agent, structured outputs, grounding enforcement (M3); DB seeding,
"pick a sample" intake, any UI (M4). Tools are plain Python, callable in isolation.
