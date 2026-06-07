# Design — Composite demo experience (`/demo`)

**Status:** approved 2026-06-07. **Approach:** TDD (view) + frontend-design (page).

A single narrated `/demo` page that walks a reviewer through the whole flow on a
pre-baked investigation — the live, in-app version of the README composite. No
agent call, no API key, instant and deterministic, so it's always-on for a
portfolio visitor.

## Decisions (confirmed in session)

1. **One narrated demo page** (not a tour overlay or auto-play).
2. **Pre-baked investigation** (no live agent run — free, instant, reliable).

## Data — `ensure_demo_investigation()`

Idempotent. Get-or-creates a dedicated NC (`nc_id="NC-TOUR-001"`, lot `LOT-AN-42`
so the real corpus evidence + Plotly chart resolve), persists a **curated tight
draft** (one machine cause — high, cited; environment — excluded/low, cited;
measurement — insufficient), edits one section (so the audit diff is non-trivial),
and approves all five (so export + the 5/5 gate render). The curated draft is a
fixed constant — not an agent call, not the corpus answer key.

The demo NC is **not** in `corpus.SAMPLE_NCS`, so it never appears in the sample
picker and never collides with the clickable samples; the demo data stays pristine
(the page is read-only).

## Page — `demo.html` (one scroll, narrated)

Reuses the existing design system; each stage has a short caption:

1. **The nonconformance** — spec sheet (measured vs. required).
2. **The cited 8D draft** — the five D-section cards, read-only (no edit/approve
   forms here).
3. **Approve the evidence, not the prose** — D4 candidate causes + citation cards
   + the Plotly process-data chart.
4. **Human sign-off** — the 5/5 readiness meter; "nothing is CAPA-ready until
   every section is signed."
5. **Audit trail** — side-by-side agent-proposal vs. engineer-final (the edited
   section); "the diff is the evidence of human judgment."
6. **Export** — the rendered 8D / CAPA Markdown + the `.md` download link.
7. **CTA** — "Try it yourself →" to home (run a real sample).

## Wiring

- `GET /demo` view → `ensure_demo_investigation()` then render `demo.html` with the
  sections, causes, chart JSON, audit rows, and the rendered export Markdown.
- A prominent "▶ Watch the 60-second demo" link on the home page (and the masthead).
- Read-only section markup on the demo page so the canonical demo data is never
  mutated.

## Tests (`tests/test_views.py`)

- `ensure_demo_investigation` is idempotent: two calls → one investigation, CAPA-ready.
- `GET /demo` → 200 and renders: a cited `source_id`, the audit diff (proposal ≠
  final on one section), `5/5` signed, the export document heading, and the
  "try it" link to home.

## Out of scope

Auto-play / animation; any change to the existing workspace flow.
