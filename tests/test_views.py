"""M4 — investigation workspace views.

View-level behavior only; the UI itself is shown by the recorded demo
(per PLAN.md). The agent is mocked — these tests never hit the API.
"""
import pytest
from django.urls import reverse

from rcca import corpus
from rcca.agent import schemas
from rcca.models import AuditEvent, CandidateCause, Investigation, Section


def _canned_draft():
    """A small grounded draft, as if the agent had run."""
    return schemas.InvestigationDraft(
        sections={d: f"Agent proposal for {d}." for d in ("D2", "D3", "D4", "D5", "D7")},
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
            )
        ],
    )


@pytest.fixture
def mock_agent(monkeypatch):
    """Replace the real agent call so sample-pick never hits the API."""
    calls = []

    def fake_run(nc, **kwargs):
        calls.append(nc)
        return _canned_draft()

    monkeypatch.setattr("rcca.views.run_investigation", fake_run)
    return calls


def test_home_lists_the_sample_ncs(client, db):
    response = client.get(reverse("rcca:home"))
    assert response.status_code == 200
    for nc_id in corpus.SAMPLE_NCS:
        assert nc_id.encode() in response.content


def test_start_sample_runs_agent_and_creates_drafted_investigation(client, db, mock_agent):
    response = client.post(reverse("rcca:start_sample", args=["NC-DEMO-001"]))

    investigation = Investigation.objects.get(nonconformance__nc_id="NC-DEMO-001")
    assert response.status_code == 302
    assert response.url == reverse("rcca:workspace", args=[investigation.pk])

    sections = investigation.sections.all()
    assert sections.count() == 5
    assert all(s.state == Section.State.DRAFTED for s in sections)
    assert sections.get(d_number="D2").agent_proposed_text == "Agent proposal for D2."
    assert CandidateCause.objects.filter(section__investigation=investigation).count() == 1
    assert len(mock_agent) == 1


def test_re_picking_a_sample_does_not_rerun_the_agent(client, db, mock_agent):
    client.post(reverse("rcca:start_sample", args=["NC-DEMO-001"]))
    client.post(reverse("rcca:start_sample", args=["NC-DEMO-001"]))

    assert len(mock_agent) == 1  # idempotent — agent ran only once
    assert Investigation.objects.filter(nonconformance__nc_id="NC-DEMO-001").count() == 1


def test_start_unknown_sample_returns_404(client, db, mock_agent):
    response = client.post(reverse("rcca:start_sample", args=["NC-NOPE"]))
    assert response.status_code == 404


@pytest.fixture
def investigation(client, db, mock_agent):
    client.post(reverse("rcca:start_sample", args=["NC-DEMO-001"]))
    return Investigation.objects.get(nonconformance__nc_id="NC-DEMO-001")


def test_workspace_renders_sections_evidence_and_gate(client, investigation):
    response = client.get(reverse("rcca:workspace", args=[investigation.pk]))
    assert response.status_code == 200
    body = response.content
    assert b"NC-DEMO-001" in body
    assert b"CAPA READINESS" in body
    assert b"Root cause" in body  # the D4 section title
    assert b"PD-LOT-AN-42" in body  # a cited evidence id in the evidence panel
    assert b"confidence" in body  # a confidence badge


def test_edit_section_transitions_to_engineer_edited_and_logs_audit(client, investigation):
    section = investigation.sections.get(d_number="D2")
    response = client.post(
        reverse("rcca:edit_section", args=[section.pk]),
        {"text": "Engineer-revised problem statement.", "engineer": "Hector"},
    )
    assert response.status_code == 200
    section.refresh_from_db()
    assert section.state == Section.State.ENGINEER_EDITED
    assert section.current_text == "Engineer-revised problem statement."
    assert AuditEvent.objects.filter(
        section=section, event_type=AuditEvent.EventType.EDIT
    ).exists()


def test_approve_section_transitions_to_approved(client, investigation):
    section = investigation.sections.get(d_number="D2")
    response = client.post(
        reverse("rcca:approve_section", args=[section.pk]), {"engineer": "Hector"}
    )
    assert response.status_code == 200
    section.refresh_from_db()
    assert section.state == Section.State.APPROVED
    assert section.approver_name == "Hector"


def test_export_blocked_until_all_sections_approved(client, investigation):
    response = client.get(reverse("rcca:export", args=[investigation.pk]))
    assert response.status_code == 403

    for section in investigation.sections.all():
        client.post(reverse("rcca:approve_section", args=[section.pk]), {"engineer": "Hector"})

    response = client.get(reverse("rcca:export", args=[investigation.pk]))
    assert response.status_code == 200
    assert b"CAPA-ready" in response.content


def _approve_all(client, investigation):
    for section in investigation.sections.all():
        client.post(reverse("rcca:approve_section", args=[section.pk]), {"engineer": "Hector"})


def test_export_download_blocked_until_capa_ready(client, investigation):
    response = client.get(reverse("rcca:export_md", args=[investigation.pk]))
    assert response.status_code == 403

    _approve_all(client, investigation)
    response = client.get(reverse("rcca:export_md", args=[investigation.pk]))
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/markdown")
    assert "attachment" in response["Content-Disposition"]
    assert "NC-DEMO-001" in response["Content-Disposition"]
    assert b"## D2" in response.content


def test_export_preview_shows_document_and_download_link(client, investigation):
    _approve_all(client, investigation)
    response = client.get(reverse("rcca:export", args=[investigation.pk]))
    assert response.status_code == 200
    assert b"8D / CAPA" in response.content  # rendered document heading
    assert reverse("rcca:export_md", args=[investigation.pk]).encode() in response.content


def test_ensure_demo_investigation_is_idempotent_and_capa_ready(db):
    from rcca.demo import DEMO_NC_ID, ensure_demo_investigation

    inv1 = ensure_demo_investigation()
    inv2 = ensure_demo_investigation()

    assert inv1.pk == inv2.pk  # idempotent — one canonical demo investigation
    assert Investigation.objects.filter(nonconformance__nc_id=DEMO_NC_ID).count() == 1
    assert inv1.is_capa_ready
    # the demo NC is not a clickable sample
    assert DEMO_NC_ID not in corpus.SAMPLE_NCS


def test_demo_page_renders_the_full_walkthrough(client, db):
    response = client.get(reverse("rcca:demo"))
    assert response.status_code == 200
    body = response.content
    assert b"PD-LOT-AN-42" in body          # a cited evidence id (D4 panel)
    assert b"5/5" in body                    # the readiness meter, fully signed
    assert b"Agent proposed" in body         # the audit diff columns
    assert b"Engineer" in body
    assert b"8D / CAPA" in body              # the rendered export document heading
    assert reverse("rcca:home").encode() in body  # the "try it yourself" CTA


def test_audit_view_shows_proposal_vs_final_and_events(client, investigation):
    section = investigation.sections.get(d_number="D2")
    client.post(
        reverse("rcca:edit_section", args=[section.pk]),
        {"text": "Engineer-revised D2.", "engineer": "Hector"},
    )

    response = client.get(reverse("rcca:audit", args=[investigation.pk]))
    assert response.status_code == 200
    body = response.content
    assert b"Agent proposal for D2." in body   # the agent's original
    assert b"Engineer-revised D2." in body     # the engineer's final
    assert b"Edited" in body                    # the changed-section flag
    assert b"EDIT" in body or b"Edit" in body   # the event timeline
