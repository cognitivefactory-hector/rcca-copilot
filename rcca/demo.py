"""Pre-baked canonical investigation for the in-app /demo walkthrough.

Deterministic and idempotent — no agent call, no API key. The curated draft below
is fixed content (not the corpus answer key, not a model output), so the demo page
always renders the same complete story for a portfolio visitor.
"""
from django.db import transaction

from . import state
from .agent import schemas
from .agent.persist import persist_draft
from .models import Investigation, Nonconformance

# A dedicated NC id that is deliberately NOT in corpus.SAMPLE_NCS, so it never
# appears in the sample picker and never collides with the clickable demos.
DEMO_NC_ID = "NC-TOUR-001"
DEMO_APPROVER = "H. Garza (Quality Eng.)"

_DEMO_DRAFT = schemas.InvestigationDraft(
    sections={
        "D2": (
            "Type II sulfuric anodic coating on lot LOT-AN-42 (PN-AL-3382) measured "
            "0.4 mil, below the SPEC-AN-7 §4.2 floor of 0.7 mil (required 0.7–1.2 mil) "
            "— ~43% under the minimum."
        ),
        "D3": (
            "Quarantine lot LOT-AN-42 and 100% eddy-current inspect at five points per "
            "SPEC-AN-7 §4.2; hold downstream lots on the same rectifier pending the "
            "voltage finding."
        ),
        "D4": (
            "Bath voltage sagged from the ~15 V setpoint to ~11 V mid-run "
            "(PD-AN-42-03/04), dropping current density to 7.9 asf (PD-AN-42-07). "
            "Coating growth is charge-driven, so the sustained low current density is "
            "mechanistically consistent with the 0.4 mil result, and mirrors recurrence "
            "NC-PRIOR-101. Underlying reason for the sag is not yet established."
        ),
        "D5": (
            "Pending root-cause confirmation: retrieve rectifier output/maintenance "
            "logs for the run; if rectifier-confirmed, repair/replace the failing "
            "component (as in NC-PRIOR-101) and verify output under load before "
            "returning the line to service."
        ),
        "D7": (
            "Add in-run SPC/interlock on bath voltage and current density with "
            "auto-alarm; verify per-run rectifier output checks; require recorded "
            "five-point thickness per SPEC-AN-7 §4.2."
        ),
    },
    causes=[
        schemas.DraftCause(
            category="machine",
            description=(
                "Rectifier output sag took bath voltage from ~15 V to ~11 V, pulling "
                "current density to 7.9 asf and starving anodic coating growth — "
                "producing the 0.4 mil result. Mechanism matches recurrence NC-PRIOR-101."
            ),
            confidence="high",
            insufficient_evidence=False,
            evidence=[
                schemas.DraftEvidence(
                    "process_data", "PD-LOT-AN-42", "PD-AN-42-03",
                    "bath_voltage_V 11.3 below setpoint",
                ),
                schemas.DraftEvidence(
                    "process_data", "PD-LOT-AN-42", "PD-AN-42-07",
                    "current_density_asf 7.9 (low)",
                ),
                schemas.DraftEvidence(
                    "prior_nc", "NC-PRIOR-101", "root_cause",
                    "Rectifier B output sagged, lowering current density and starving growth",
                ),
            ],
        ),
        schemas.DraftCause(
            category="environment",
            description=(
                "Bath-temperature excursion as a contributor — excluded by evidence; "
                "bath temp was in range."
            ),
            confidence="low",
            insufficient_evidence=False,
            evidence=[
                schemas.DraftEvidence(
                    "process_data", "PD-LOT-AN-42", "PD-AN-42-09", "bath_temp_F 70.0 (in range)"
                )
            ],
        ),
        schemas.DraftCause(
            category="measurement",
            description=(
                "False-low eddy-current reading (probe calibration or single- vs five-point). "
                "No calibration record or full five-point dataset was retrieved."
            ),
            confidence="low",
            insufficient_evidence=True,
            evidence=[],
        ),
    ],
)

# The engineer's edit to D2 — makes the audit diff (agent vs. final) non-trivial.
_D2_ENGINEER_FINAL = _DEMO_DRAFT.sections["D2"] + (
    " Engineer note: confirmed against the calibrated reference standard; 3 of 5 "
    "points below floor."
)


@transaction.atomic
def ensure_demo_investigation() -> Investigation:
    """Idempotently create the canonical, fully-signed demo investigation."""
    nc, _ = Nonconformance.objects.get_or_create(
        nc_id=DEMO_NC_ID,
        defaults=dict(
            title="Anodize coating thickness below spec floor",
            part_number="PN-AL-3382",
            lot="LOT-AN-42",
            process="Type II sulfuric anodize",
            defect_description="Coating thickness 0.4 mil, below the SPEC-AN-7 floor.",
            spec_violated="SPEC-AN-7",
            measured_value="0.4 mil",
            required_value="0.7–1.2 mil",
        ),
    )
    investigation = nc.investigations.first() or Investigation.create_for(nc)

    if investigation.sections.exclude(agent_proposed_text="").exists():
        return investigation  # already seeded

    persist_draft(investigation, _DEMO_DRAFT)
    state.edit_section(
        investigation.sections.get(d_number="D2"), _D2_ENGINEER_FINAL, actor=DEMO_APPROVER
    )
    for section in investigation.sections.all():
        state.approve_section(section, approver_name=DEMO_APPROVER)
    return investigation
