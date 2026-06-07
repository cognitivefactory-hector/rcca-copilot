"""Render an investigation as a clean, auditor-recognizable 8D / CAPA document.

Markdown, pure and deterministic — the document is the final approved content
plus the approver of record per section. The audit trail (what changed) lives in
the audit view, not here.
"""
from .corpus import DISCLAIMER
from .models import CandidateCause, Section
from .state import REQUIRED_D_NUMBERS, SECTION_TITLES


def _approval_line(section: Section) -> str:
    if section.state == Section.State.APPROVED and section.approver_name:
        when = section.approved_at.strftime("%Y-%m-%d %H:%M UTC") if section.approved_at else ""
        return f"*Approved by {section.approver_name}{f' on {when}' if when else ''}.*"
    return "*Not yet approved.*"


def _cause_block(cause: CandidateCause) -> list[str]:
    if cause.insufficient_evidence:
        strength = "Insufficient evidence — investigate further"
    else:
        strength = f"{cause.get_confidence_display()} confidence"
    lines = [f"- **{cause.get_category_display()}** ({strength}): {cause.description}"]
    for ev in cause.evidence_refs.all():
        lines.append(f"  - Evidence: `{ev.source_id}` · {ev.locator} — {ev.excerpt}")
    if not cause.evidence_refs.exists() and not cause.insufficient_evidence:
        lines.append("  - Evidence: none cited.")
    return lines


def render_markdown(investigation) -> str:
    nc = investigation.nonconformance
    sections = {s.d_number: s for s in investigation.sections.all()}

    out: list[str] = [
        f"# 8D / CAPA — {nc.nc_id}: {nc.title}",
        "",
        f"- **Part:** {nc.part_number or '—'}",
        f"- **Lot:** {nc.lot or '—'}",
        f"- **Process:** {nc.process or '—'}",
        f"- **Spec violated:** {nc.spec_violated or '—'}",
        f"- **Measured vs. required:** {nc.measured_value or '—'} vs. {nc.required_value or '—'}",
        f"- **CAPA-ready:** {'YES' if investigation.is_capa_ready else 'NO'}",
        "",
    ]

    for d_number in REQUIRED_D_NUMBERS:
        section = sections.get(d_number)
        if section is None:
            continue
        out.append(f"## {d_number} — {SECTION_TITLES[d_number]}")
        out.append("")
        out.append(section.current_text or "_(empty)_")
        out.append("")

        if d_number == "D4":
            causes = CandidateCause.objects.filter(section=section).prefetch_related(
                "evidence_refs"
            )
            if causes:
                out.append("**Candidate causes (Ishikawa / 6M):**")
                out.append("")
                for cause in causes:
                    out.extend(_cause_block(cause))
                out.append("")

        out.append(_approval_line(section))
        out.append("")

    out.append("---")
    out.append(f"_{DISCLAIMER}_")
    return "\n".join(out)
