# M5 Design — Export + audit trail

**Milestone:** M5 (`PLAN.md`). **Approach:** TDD. **Status:** approved 2026-06-07.

Produce a clean, auditor-recognizable 8D / CAPA document, and an audit trail that
shows what the agent proposed vs. what the engineer changed — the diff is the
evidence of human judgment.

## Decisions (confirmed in session)

1. **Markdown only.** Render the 8D as Markdown (PLAN: "Markdown first, PDF
   optional"). Pure, dependency-free, trivially testable; PDF deferred.
2. **Audit = side-by-side + event log.** Per section, the agent's original
   proposal next to the engineer's final text (changed sections flagged), plus
   the AuditEvent timeline.

## Renderer — `rcca/export.py`

`render_markdown(investigation) -> str`, pure and deterministic (no
`datetime.now()` — uses the sections' real `approved_at` values):

- Header: `# {nc_id} — {title}` and a metadata block (part / lot / process / spec
  / measured vs. required).
- For each D-section (D2/D3/D4/D5/D7): `## D2 — Problem description`, the **final**
  `current_text`, and an "Approved by {approver} on {approved_at}" line.
- **D4** additionally: a candidate-cause list — category, confidence (or
  *insufficient evidence*), description, and citations
  (`source_id` · `locator` — excerpt).
- Footer: the synthetic-data disclaimer.

## Views / URLs

- `GET /investigations/<pk>/export` — **preview page**: the rendered document in a
  monospace "document" block + a **Download .md** link. Still **403 until
  `is_capa_ready`** (the blocked page is unchanged); keeps a "CAPA-ready" marker
  so the M4 gate test holds.
- `GET /investigations/<pk>/export.md` — downloads `text/markdown` with
  `Content-Disposition: attachment; filename="{nc_id}-8D.md"`; also gated on
  `is_capa_ready`.
- `GET /investigations/<pk>/audit` — the audit trail; **available anytime** (it's
  the record), linked from the workspace.

## Audit view — `audit.html`

Per section, **side-by-side**: `agent_proposed_text` (agent) next to
`current_text` (engineer's final), with an **"Edited" vs "As drafted"** flag
(they differ → edited). Below, the **AuditEvent timeline** (draft → edit →
approve; actor + timestamp). The diff plus the log are what an auditor reads to
see the human's reasoning.

## Tests (TDD)

`tests/test_export.py` (pure render):
- All five D-headings present, each with its final section text.
- Approver names appear.
- D4 candidate causes appear with category, confidence, and citation
  (`source_id` + `locator`).
- An insufficient-evidence cause is marked as such.
- The synthetic-data disclaimer is present.

`tests/test_views.py` additions:
- `.md` download is **403 until CAPA-ready**, then `200` with
  `Content-Type: text/markdown`, an `attachment` Content-Disposition, and a
  D-heading in the body.
- The preview page (when ready) shows the document and the download link.
- The audit view shows the agent proposal and the engineer's final text, flags a
  section the engineer edited, and lists the audit events.

## Out of scope for M5

PDF export (deferred); README polish, deploy (M6); decision record + whiteboard
(M7).
