"""M1 — sign-off state machine and audit trail (the trust backbone).

These are the crown-jewel tests per PLAN.md: CAPA-readiness can never be forced,
edits are logged, and approved text cannot silently change.
"""
import pytest

from rcca import state
from rcca.models import AuditEvent, Investigation, Nonconformance, Section


@pytest.fixture
def nc(db):
    return Nonconformance.objects.create(
        nc_id="NC-001",
        title="Anodize coating thickness below spec floor",
        part_number="PN-1234",
        lot="LOT-42",
        process="Type II anodize",
        defect_description="Coating thickness measured below the spec minimum on lot LOT-42.",
        spec_violated="SPEC-AN-7",
        measured_value="0.4 mil",
        required_value="0.7-1.2 mil",
    )


def test_create_for_spins_up_five_drafted_sections(nc):
    investigation = Investigation.create_for(nc)

    sections = investigation.sections.all()
    assert {s.d_number for s in sections} == set(state.REQUIRED_D_NUMBERS)
    assert all(s.state == Section.State.DRAFTED for s in sections)
    assert len(sections) == 5


def test_fresh_investigation_is_not_capa_ready(nc):
    investigation = Investigation.create_for(nc)
    assert investigation.is_capa_ready is False


def test_edit_drafted_section_transitions_to_engineer_edited_and_logs_event(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")

    state.edit_section(section, "Coating thickness 0.4 mil vs 0.7 mil floor.", actor="Hector")

    section.refresh_from_db()
    assert section.state == Section.State.ENGINEER_EDITED
    assert section.current_text == "Coating thickness 0.4 mil vs 0.7 mil floor."

    event = AuditEvent.objects.get(section=section)
    assert event.event_type == AuditEvent.EventType.EDIT
    assert event.actor == "Hector"
    assert event.from_state == Section.State.DRAFTED
    assert event.to_state == Section.State.ENGINEER_EDITED


def test_approve_sets_state_approver_timestamp_and_logs_event(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")
    state.edit_section(section, "Problem described.", actor="Hector")

    state.approve_section(section, approver_name="Hector Garza")

    section.refresh_from_db()
    assert section.state == Section.State.APPROVED
    assert section.approver_name == "Hector Garza"
    assert section.approved_at is not None

    event = AuditEvent.objects.filter(
        section=section, event_type=AuditEvent.EventType.APPROVE
    ).get()
    assert event.actor == "Hector Garza"
    assert event.to_state == Section.State.APPROVED


def test_candidate_cause_and_evidence_models_link_to_a_section(nc):
    # Inert in M1 (the agent fills them in M3); here we only assert the schema
    # graph so the single initial migration is complete.
    from rcca.models import CandidateCause, EvidenceRef

    investigation = Investigation.create_for(nc)
    d4 = investigation.sections.get(d_number="D4")
    cause = CandidateCause.objects.create(
        section=d4,
        category=CandidateCause.Category.MACHINE,
        description="Rectifier voltage drift during the lot run.",
        confidence=CandidateCause.Confidence.MEDIUM,
    )
    evidence = EvidenceRef.objects.create(
        candidate_cause=cause,
        source_type="process_data",
        source_id="PD-LOT-42",
        locator="row 17",
        excerpt="Voltage dipped to 11.2 V for 40 min.",
    )

    assert cause in d4.candidate_causes.all()
    assert evidence in cause.evidence_refs.all()
    assert cause.insufficient_evidence is False


def _approve_all(investigation, approver="Hector"):
    for section in investigation.sections.all():
        state.edit_section(section, f"{section.d_number} content.", actor=approver)
        state.approve_section(section, approver_name=approver)


def test_editing_an_approved_section_reverts_it_and_clears_approver(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")
    state.edit_section(section, "Draft problem.", actor="Hector")
    state.approve_section(section, approver_name="Hector Garza")

    state.edit_section(section, "Revised problem.", actor="Hector")

    section.refresh_from_db()
    assert section.state == Section.State.ENGINEER_EDITED
    assert section.approver_name == ""
    assert section.approved_at is None

    revert = AuditEvent.objects.filter(
        section=section, event_type=AuditEvent.EventType.REVERT
    ).get()
    assert revert.from_state == Section.State.APPROVED
    assert revert.to_state == Section.State.ENGINEER_EDITED


def test_capa_ready_only_when_all_five_approved(nc):
    investigation = Investigation.create_for(nc)
    # Approve only four of the five sections.
    for d in ("D2", "D3", "D4", "D5"):
        section = investigation.sections.get(d_number=d)
        state.edit_section(section, f"{d} content.", actor="Hector")
        state.approve_section(section, approver_name="Hector")

    assert investigation.is_capa_ready is False

    last = investigation.sections.get(d_number="D7")
    state.edit_section(last, "D7 content.", actor="Hector")
    state.approve_section(last, approver_name="Hector")

    assert investigation.is_capa_ready is True


def test_capa_ready_flips_back_to_false_when_an_approved_section_is_edited(nc):
    investigation = Investigation.create_for(nc)
    _approve_all(investigation)
    assert investigation.is_capa_ready is True

    state.edit_section(investigation.sections.get(d_number="D4"), "New cause.", actor="Hector")

    assert investigation.is_capa_ready is False


def test_cannot_approve_a_section_with_empty_text(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")

    with pytest.raises(ValueError):
        state.approve_section(section, approver_name="Hector")

    section.refresh_from_db()
    assert section.state == Section.State.DRAFTED


def test_approving_an_already_approved_section_is_a_noop(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")
    state.edit_section(section, "Content.", actor="Hector")
    state.approve_section(section, approver_name="Hector")

    state.approve_section(section, approver_name="Someone Else")

    assert AuditEvent.objects.filter(
        section=section, event_type=AuditEvent.EventType.APPROVE
    ).count() == 1
    section.refresh_from_db()
    assert section.approver_name == "Hector"


def test_audit_log_is_ordered_and_append_only(nc):
    investigation = Investigation.create_for(nc)
    section = investigation.sections.get(d_number="D2")
    state.edit_section(section, "First.", actor="Hector")
    state.edit_section(section, "Second.", actor="Hector")
    state.approve_section(section, approver_name="Hector")

    events = list(investigation.audit_events.all())
    assert [e.event_type for e in events] == [
        AuditEvent.EventType.EDIT,
        AuditEvent.EventType.EDIT,
        AuditEvent.EventType.APPROVE,
    ]
    assert [e.text_snapshot for e in events] == ["First.", "Second.", "Second."]
