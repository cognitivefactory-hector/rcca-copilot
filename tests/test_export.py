"""M5 — the 8D / CAPA Markdown renderer (pure).

Produces a clean, auditor-recognizable document from an approved investigation.
"""
import pytest

from rcca import state
from rcca.agent import schemas
from rcca.agent.persist import persist_draft
from rcca.export import render_markdown
from rcca.models import Investigation, Nonconformance


@pytest.fixture
def approved_investigation(db):
    nc = Nonconformance.objects.create(
        nc_id="NC-DEMO-001",
        title="Anodize coating thickness below spec floor",
        part_number="PN-AL-3382",
        lot="LOT-AN-42",
        process="Type II sulfuric anodize",
        spec_violated="SPEC-AN-7",
        measured_value="0.4 mil",
        required_value="0.7-1.2 mil",
    )
    investigation = Investigation.create_for(nc)
    draft = schemas.InvestigationDraft(
        sections={d: f"Final {d} narrative." for d in ("D2", "D3", "D4", "D5", "D7")},
        causes=[
            schemas.DraftCause(
                category="machine",
                description="Rectifier voltage sagged mid-run.",
                confidence="high",
                insufficient_evidence=False,
                evidence=[
                    schemas.DraftEvidence(
                        "process_data", "PD-LOT-AN-42", "PD-AN-42-03", "11.3 V below setpoint"
                    )
                ],
            ),
            schemas.DraftCause(
                category="measurement",
                description="Possible gauge drift.",
                confidence="low",
                insufficient_evidence=True,
                evidence=[],
            ),
        ],
    )
    persist_draft(investigation, draft)
    for section in investigation.sections.all():
        state.approve_section(section, approver_name="Hector Garza")
    return investigation


def test_render_includes_all_d_headings_and_final_text(approved_investigation):
    md = render_markdown(approved_investigation)
    for d in ("D2", "D3", "D4", "D5", "D7"):
        assert d in md
        assert f"Final {d} narrative." in md


def test_render_includes_approver_of_record(approved_investigation):
    md = render_markdown(approved_investigation)
    assert "Hector Garza" in md


def test_render_includes_d4_causes_with_confidence_and_citation(approved_investigation):
    md = render_markdown(approved_investigation)
    assert "Rectifier voltage sagged mid-run." in md
    assert "PD-LOT-AN-42" in md
    assert "PD-AN-42-03" in md
    assert "High" in md or "high" in md  # confidence rendered


def test_render_marks_insufficient_evidence(approved_investigation):
    md = render_markdown(approved_investigation)
    assert "insufficient evidence" in md.lower()


def test_render_includes_synthetic_disclaimer(approved_investigation):
    md = render_markdown(approved_investigation)
    assert "fictional" in md.lower() or "simulated" in md.lower()
