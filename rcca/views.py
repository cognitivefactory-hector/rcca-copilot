import json

from django.db import OperationalError, connection
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import corpus, state
from .agent.orchestrator import run_investigation
from .agent.persist import persist_draft
from .agent.tools import get_process_data
from .export import render_markdown
from .models import CandidateCause, Investigation, Nonconformance, Section


def _db_ok() -> bool:
    """True if Postgres answers a trivial query — the M0 connectivity check."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except OperationalError:
        return False


def home(request):
    return render(request, "rcca/home.html", {"samples": corpus.SAMPLE_NCS.values()})


def healthz(request):
    ok = _db_ok()
    return JsonResponse({"status": "ok" if ok else "degraded", "db": ok}, status=200 if ok else 503)


def _has_draft(investigation) -> bool:
    return investigation.sections.exclude(agent_proposed_text="").exists()


def start_sample(request, nc_id):
    """Pick a sample: create the investigation and (once) run the agent."""
    sample = corpus.SAMPLE_NCS.get(nc_id)
    if sample is None:
        from django.http import Http404

        raise Http404(f"Unknown sample: {nc_id}")

    nc, _ = Nonconformance.objects.get_or_create(
        nc_id=sample.nc_id,
        defaults=dict(
            title=sample.title,
            part_number=sample.part_number,
            lot=sample.lot,
            process=sample.process,
            defect_description=sample.defect_description,
            spec_violated=sample.spec_violated,
            measured_value=sample.measured_value,
            required_value=sample.required_value,
        ),
    )
    investigation = nc.investigations.first() or Investigation.create_for(nc)

    # Idempotent: only run the agent if this investigation hasn't been drafted.
    if not _has_draft(investigation):
        draft = run_investigation(sample)
        persist_draft(investigation, draft)

    return redirect("rcca:workspace", pk=investigation.pk)


def _process_chart(lot):
    """Numeric process-data series for the lot, shaped for Plotly (or None)."""
    try:
        data = get_process_data(lot)
    except LookupError:
        return None
    series = {}
    for row in data["rows"]:
        series.setdefault(row["parameter"], {"x": [], "y": [], "name": row["parameter"]})
        series[row["parameter"]]["x"].append(row["locator"])
        series[row["parameter"]]["y"].append(row["value"])
    return {"source_id": data["source_id"], "lot": data["lot"], "series": list(series.values())}


def _gate_ctx(investigation):
    approved = investigation.sections.filter(state=Section.State.APPROVED).count()
    return {
        "investigation": investigation,
        "capa_ready": investigation.is_capa_ready,
        "approved_count": approved,
        "pips": [i < approved for i in range(5)],
    }


def workspace(request, pk):
    investigation = get_object_or_404(Investigation, pk=pk)
    sections = list(investigation.sections.order_by("d_number"))
    d4 = next((s for s in sections if s.d_number == "D4"), None)
    causes = (
        CandidateCause.objects.filter(section=d4).prefetch_related("evidence_refs")
        if d4
        else []
    )
    chart = _process_chart(investigation.nonconformance.lot)
    return render(
        request,
        "rcca/workspace.html",
        {
            "nc": investigation.nonconformance,
            "sections": sections,
            "causes": causes,
            "chart_json": json.dumps(chart) if chart else "null",
            **_gate_ctx(investigation),
        },
    )


def _engineer(request):
    return (request.POST.get("engineer") or "Engineer").strip() or "Engineer"


def _render_card(request, section, error=""):
    return render(
        request,
        "rcca/partials/_section_card.html",
        {
            "section": section,
            "error": error,
            "swap_export": True,
            **_gate_ctx(section.investigation),
        },
    )


def edit_section(request, pk):
    section = get_object_or_404(Section, pk=pk)
    state.edit_section(section, request.POST.get("text", ""), actor=_engineer(request))
    return _render_card(request, section)


def approve_section(request, pk):
    section = get_object_or_404(Section, pk=pk)
    try:
        state.approve_section(section, approver_name=_engineer(request))
    except ValueError as exc:
        return _render_card(request, section, error=str(exc))
    return _render_card(request, section)


def _blocked(request, investigation):
    return HttpResponseForbidden(
        render(request, "rcca/export_blocked.html", {"investigation": investigation}).content
    )


def export(request, pk):
    """Preview the rendered 8D / CAPA document (gated on CAPA-ready)."""
    investigation = get_object_or_404(Investigation, pk=pk)
    if not investigation.is_capa_ready:
        return _blocked(request, investigation)
    return render(
        request,
        "rcca/export_preview.html",
        {"investigation": investigation, "document": render_markdown(investigation)},
    )


def export_md(request, pk):
    """Download the 8D / CAPA document as Markdown (gated on CAPA-ready)."""
    investigation = get_object_or_404(Investigation, pk=pk)
    if not investigation.is_capa_ready:
        return _blocked(request, investigation)
    response = HttpResponse(render_markdown(investigation), content_type="text/markdown")
    filename = f"{investigation.nonconformance.nc_id}-8D.md"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def audit(request, pk):
    """The audit trail: agent proposal vs. engineer's final, per section, plus the
    event timeline. Available anytime — it is the record."""
    investigation = get_object_or_404(Investigation, pk=pk)
    rows = [
        {
            "section": s,
            "proposed": s.agent_proposed_text,
            "final": s.current_text,
            "edited": s.current_text != s.agent_proposed_text,
        }
        for s in investigation.sections.order_by("d_number")
    ]
    return render(
        request,
        "rcca/audit.html",
        {
            "investigation": investigation,
            "nc": investigation.nonconformance,
            "rows": rows,
            "events": investigation.audit_events.all(),
        },
    )
