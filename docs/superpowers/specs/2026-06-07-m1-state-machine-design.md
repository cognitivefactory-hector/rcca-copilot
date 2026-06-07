# M1 Design — Domain model + sign-off state machine

**Milestone:** M1 (`PLAN.md`). **Approach:** TDD. **Status:** approved 2026-06-07.

The trust backbone, built and tested before any AI. This is the part that makes
the tool credible in a regulated process: nothing reaches CAPA-ready without an
explicit human approval, and every change is logged. The agent (M3) layers on top.

## Decisions recorded here (not in SPEC.md / PLAN.md)

1. **Edit-after-approve reverts.** Editing an `Approved` section drops it back to
   `Engineer-edited` and clears the approver — approved text can never silently
   change, and CAPA-readiness self-corrects the moment any section is touched.
2. **All five sections required.** D2/D3/D4/D5/D7 must all be `Approved` for an
   investigation to be CAPA-ready.
3. **All six models now, behavior on the state machine only.** One migration
   defines every model; `CandidateCause`/`EvidenceRef` are inert until the agent
   fills them in M3. Avoids a second migration churn.
4. **Approver is a free-text name + timestamp.** No auth dependency (SPEC §4.4:
   a demo session is enough).

## Architecture

Logic lives in `rcca/state.py`; models stay declarative in `rcca/models.py`
(matches the `PLAN.md` layout). `Investigation.is_capa_ready` is a property that
delegates to `state.py` — **purely derived, no setter** — so CAPA-readiness can
never be forced; it is only ever a function of section states.

## Models (one migration)

- **`Nonconformance`** — `nc_id` (stable unique slug), `title`, `part_number`,
  `lot`, `process`, `defect_description`, `spec_violated`, `measured_value`,
  `required_value`, `created_at`. Intake UI is M4; this is just the record.
- **`Investigation`** — FK to `Nonconformance`, `created_at`. Built via
  `Investigation.create_for(nc)`, which creates the five `Section`s in `Drafted`.
  Exposes `is_capa_ready` (derived property).
- **`Section`** — `investigation` FK, `d_number` (D2/D3/D4/D5/D7),
  `state` (`drafted`/`engineer_edited`/`approved`), `agent_proposed_text`
  (filled in M3), `current_text`, `approver_name`, `approved_at`, `updated_at`.
  `unique_together(investigation, d_number)`.
- **`CandidateCause`** — FK to its D4 `Section`, `category` (6M: Man/Machine/
  Method/Material/Measurement/Environment), `description`, `confidence`,
  `insufficient_evidence` (bool). *Model only in M1.*
- **`EvidenceRef`** — FK to `CandidateCause`, `source_type`
  (process_data/spec/prior_nc), `source_id` (stable id), `locator`, `excerpt`.
  *Model only in M1.*
- **`AuditEvent`** — append-only: `investigation` FK, `section` FK (nullable),
  `event_type` (`draft`/`edit`/`approve`/`revert`), `actor`, `from_state`,
  `to_state`, `text_snapshot`, `created_at`. No update/delete in app logic.

## State machine (`rcca/state.py`)

| From | Action | To | Side effects |
|---|---|---|---|
| Drafted | `edit(text, actor)` | Engineer-edited | logs `edit` |
| Drafted / Engineer-edited | `approve(name)` | Approved | sets approver + timestamp, logs `approve` |
| Engineer-edited | `edit` | Engineer-edited | logs `edit` |
| Approved | `edit` | Engineer-edited | clears approver/timestamp, logs `revert` |

Rules:
- `approve` on empty `current_text` → raises (can't sign off on nothing).
- `approve` on an already-`Approved` section → no-op (idempotent, no duplicate event).
- `is_capa_ready(investigation)` → True iff all five required sections are
  `approved`; flips back to False automatically when any approved section is edited.

`REQUIRED_D_NUMBERS = ("D2", "D3", "D4", "D5", "D7")`.

## Tests first (`tests/test_state.py`)

- `create_for` spins up exactly five `Drafted` sections.
- A fresh investigation is **not** CAPA-ready.
- `approve` sets state + approver + timestamp and logs one `approve` event.
- `edit` on Drafted → Engineer-edited and logs one `edit` event.
- Edit-after-approve → reverts to Engineer-edited, clears approver, logs `revert`.
- CAPA-ready only after all five approved; approving four leaves it not ready.
- CAPA-ready flips back to False when an approved section is edited.
- `approve` on empty text raises.
- `approve` on an already-approved section is a no-op (no duplicate event).
- The audit log is append-only and ordered by `created_at`.

## Out of scope for M1

The agent, retrieval tools, synthetic corpus, any UI, export. `CandidateCause`
and `EvidenceRef` get behavior in M3.
