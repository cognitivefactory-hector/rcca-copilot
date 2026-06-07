"""The sign-off state machine — the trust backbone.

All section state transitions go through here so every change is logged and the
rules (cite-or-revert, no forced CAPA-readiness) live in one auditable place.
"""

# The five 8D sections an investigation must approve to be CAPA-ready.
REQUIRED_D_NUMBERS = ("D2", "D3", "D4", "D5", "D7")

SECTION_TITLES = {
    "D2": "Problem description",
    "D3": "Interim containment",
    "D4": "Root cause",
    "D5": "Permanent corrective action",
    "D7": "Prevent recurrence",
}


def edit_section(section, text, actor):
    """Record an engineer's edit. Moves the section to Engineer-edited.

    Editing an Approved section reverts it (clearing the approver) so approved
    text can never silently change — logged as a `revert`, otherwise an `edit`.
    """
    from .models import AuditEvent, Section

    from_state = section.state
    reverting = from_state == Section.State.APPROVED

    section.current_text = text
    section.state = Section.State.ENGINEER_EDITED
    if reverting:
        section.approver_name = ""
        section.approved_at = None
    section.save()

    AuditEvent.objects.create(
        investigation=section.investigation,
        section=section,
        event_type=AuditEvent.EventType.REVERT if reverting else AuditEvent.EventType.EDIT,
        actor=actor,
        from_state=from_state,
        to_state=section.state,
        text_snapshot=text,
    )
    return section


def approve_section(section, approver_name):
    """Approve a section. No-op if already approved; refuses empty text."""
    from django.utils import timezone

    from .models import AuditEvent, Section

    if section.state == Section.State.APPROVED:
        return section
    if not section.current_text.strip():
        raise ValueError("Cannot approve a section with no content.")

    from_state = section.state
    section.state = Section.State.APPROVED
    section.approver_name = approver_name
    section.approved_at = timezone.now()
    section.save()

    AuditEvent.objects.create(
        investigation=section.investigation,
        section=section,
        event_type=AuditEvent.EventType.APPROVE,
        actor=approver_name,
        from_state=from_state,
        to_state=section.state,
        text_snapshot=section.current_text,
    )
    return section


def is_capa_ready(investigation):
    """True iff every required section exists and is Approved."""
    from .models import Section

    approved = {
        s.d_number
        for s in investigation.sections.filter(state=Section.State.APPROVED)
    }
    return set(REQUIRED_D_NUMBERS).issubset(approved)
