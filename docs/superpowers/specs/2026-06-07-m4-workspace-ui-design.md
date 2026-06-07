# M4 Design — Investigation workspace UI

**Milestone:** M4 (`PLAN.md`). **Approach:** frontend-design for templates; TDD for
view logic. **Status:** approved 2026-06-07.

The clickable demo where the human is visibly in control: pick a sample → the
agent drafts a cited 8D → the engineer edits and approves each section → export
unlocks only when every section is approved.

## Decisions (confirmed in session)

1. **Auto-run on sample pick, idempotent.** Picking a sample runs the agent once
   and persists the draft; re-picking the same sample shows the existing
   investigation without re-running. That idempotence is the cost guard now that
   auto-run replaces a run button (prompt caching + token caps from M3 still apply).
2. **Sample picker only.** Cards for the corpus NCs (reproducible, planted
   causes). Custom free-text intake is deferred — the agent's tools only know the
   corpus lots, so a custom NC would mostly yield insufficient-evidence.
3. **Citation cards + Plotly chart.** The evidence panel shows each cause's
   citation cards and a Plotly chart of the cited lot's process-data trend, so the
   anomaly is visible — "approve the evidence, not the prose."

## Endpoints (`rcca/urls.py` / `views.py`)

- `GET /` — home: cards for `corpus.SAMPLE_NCS`.
- `POST /samples/<nc_id>/start` — get-or-create `Nonconformance` +
  `Investigation.create_for`; if not yet drafted, `run_investigation` +
  `persist_draft`; redirect to the workspace. Unknown `nc_id` → 404.
- `GET /investigations/<pk>/` — the workspace.
- `POST /sections/<pk>/edit` — HTMX: `state.edit_section`, return the updated
  section-card partial.
- `POST /sections/<pk>/approve` — HTMX: `state.approve_section`, return the card
  partial + a refreshed export-button (HTMX out-of-band swap).
- `GET /investigations/<pk>/export` — **gate only in M4**: 403 until
  `is_capa_ready`; a "CAPA-ready ✓" confirmation when ready. The rendered export
  document and the audit-diff view are M5.

"Has the agent drafted yet?" = any section has non-empty `agent_proposed_text`.

## Workspace layout

- NC summary header (part/lot/process, measured vs. required, spec).
- Five 8D section cards, each with: a **state badge**
  (`Drafted`/`Engineer-edited`/`Approved`), the agent's proposal in an editable
  textarea (seeded `current_text`), **Edit** and **Approve** controls (HTMX,
  swap the card). Approving empty text is refused (M1 rule) — surfaced as an error.
- The **D4 card** additionally renders candidate causes with **confidence badges**
  (or an "insufficient evidence" flag) and an **evidence panel**: citation cards
  (`source_type` / `source_id` / `locator` / `excerpt`) plus a **Plotly** line
  chart of the cited lot's process-data trend.
- **Export button** disabled until `investigation.is_capa_ready`; clear visual
  state for what's blocking.
- Footer disclaimer: "Simulated data; not affiliated with any employer. Drafting
  aid — a qualified engineer signs every CAPA."

## Templates (frontend-design)

`base.html` (header, footer disclaimer, htmx + plotly from CDN), `home.html`
(sample picker), `workspace.html`, and `partials/_section_card.html` (the HTMX
swap unit). A distinctive industrial / quality-engineering aesthetic — not a
generic AI-template look.

## Plotly

`get_process_data(nc.lot)` provides the rows; pass them as JSON to a small inline
script that calls `Plotly.newPlot` (plotly.js from CDN — no heavy Python dep).
Plot the measured parameter series over the run so the anomaly is visible.

## Tests (`tests/test_views.py`, TDD on view logic)

UI itself is demonstrated by the recording (per `PLAN.md` — don't chase UI
coverage). The agent is **mocked** (monkeypatch `views.run_investigation` to
return a canned `InvestigationDraft`).

- Home lists the sample NCs.
- Sample-pick creates 5 Drafted sections and populates the draft
  (`agent_proposed_text`, D4 causes/evidence).
- Re-picking the same sample does **not** re-run the agent (called once).
- Unknown sample id → 404.
- `edit` endpoint → Engineer-edited + an AuditEvent; returns the card.
- `approve` endpoint → Approved.
- **Export 403 until all sections approved; allowed once CAPA-ready.**
- Update the M0 home smoke test for the redesigned home (DB connectivity stays on
  `/healthz`).

## Out of scope for M4

The rendered export document and the audit-diff view (M5); custom NC intake;
per-cause chart highlighting.
