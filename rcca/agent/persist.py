"""Write an InvestigationDraft into the M1 sign-off models.

The agent's proposal lands as agent_proposed_text and seeds the engineer's
working copy, but sections stay Drafted — nothing is signed until the engineer
acts. Each proposal is logged as a `draft` AuditEvent, the "what the agent
proposed" side of the trail.
"""
from django.db import transaction

from ..models import AuditEvent, CandidateCause, EvidenceRef, Section
from .schemas import InvestigationDraft

AGENT_ACTOR = "agent"


@transaction.atomic
def persist_draft(investigation, draft: InvestigationDraft) -> None:
    for d_number, text in draft.sections.items():
        section = investigation.sections.get(d_number=d_number)
        section.agent_proposed_text = text
        section.current_text = text  # seed the engineer's editable copy
        section.save()
        AuditEvent.objects.create(
            investigation=investigation,
            section=section,
            event_type=AuditEvent.EventType.DRAFT,
            actor=AGENT_ACTOR,
            from_state=Section.State.DRAFTED,
            to_state=Section.State.DRAFTED,
            text_snapshot=text,
        )

    d4 = investigation.sections.get(d_number="D4")
    for cause in draft.causes:
        candidate = CandidateCause.objects.create(
            section=d4,
            category=cause.category,
            description=cause.description,
            confidence=cause.confidence,
            insufficient_evidence=cause.insufficient_evidence,
        )
        for ev in cause.evidence:
            EvidenceRef.objects.create(
                candidate_cause=candidate,
                source_type=ev.source_type,
                source_id=ev.source_id,
                locator=ev.locator,
                excerpt=ev.excerpt,
            )
