"""M3 — grounded agent orchestration (Anthropic API mocked).

The agent fetches evidence via tools and emits a structured 8D draft; no uncited
root cause may be asserted as confirmed.
"""
import json
import types

import pytest

from rcca.agent import schemas


def _tool_use(name, tool_input, block_id="toolu_1"):
    return types.SimpleNamespace(
        type="tool_use", name=name, input=tool_input, id=block_id
    )


def _text(text):
    return types.SimpleNamespace(type="text", text=text)


def _response(stop_reason, content):
    return types.SimpleNamespace(stop_reason=stop_reason, content=content)


class FakeMessages:
    def __init__(self, scripted):
        self._scripted = list(scripted)
        self.calls = []  # records kwargs of every create() call

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._scripted.pop(0)


class FakeAnthropicClient:
    """Returns scripted responses in order; records every create() call."""

    def __init__(self, scripted):
        self.messages = FakeMessages(scripted)

SAMPLE_DRAFT_JSON = {
    "d2_problem": "Coating thickness 0.4 mil, below the 0.7 mil floor on LOT-AN-42.",
    "d3_containment": "Quarantine LOT-AN-42; 100% eddy-current inspect.",
    "d4_root_cause_summary": "Mid-run voltage sag starved coating growth.",
    "candidate_causes": [
        {
            "category": "machine",
            "description": "Rectifier voltage sagged to ~11 V mid-run.",
            "confidence": "high",
            "insufficient_evidence": False,
            "evidence": [
                {
                    "source_type": "process_data",
                    "source_id": "PD-LOT-AN-42",
                    "locator": "PD-AN-42-03",
                    "excerpt": "bath_voltage_V 11.3 below setpoint",
                }
            ],
        }
    ],
    "d5_corrective_action": "Verify rectifier output each run.",
    "d7_prevent_recurrence": "Add per-run voltage interlock.",
}


def test_parse_draft_maps_schema_json_to_dataclasses():
    draft = schemas.parse_draft(SAMPLE_DRAFT_JSON)

    assert draft.sections["D2"] == SAMPLE_DRAFT_JSON["d2_problem"]
    assert draft.sections["D4"] == SAMPLE_DRAFT_JSON["d4_root_cause_summary"]
    assert len(draft.causes) == 1

    cause = draft.causes[0]
    assert cause.category == "machine"
    assert cause.confidence == "high"
    assert cause.insufficient_evidence is False
    assert cause.evidence[0].source_id == "PD-LOT-AN-42"
    assert cause.evidence[0].locator == "PD-AN-42-03"


def test_tool_defs_expose_the_three_retrieval_tools():
    from rcca.agent import tool_defs

    names = {t["name"] for t in tool_defs.TOOL_DEFS}
    assert names == {"get_process_data", "get_spec", "search_prior_ncs"}
    for tool in tool_defs.TOOL_DEFS:
        assert tool["description"]
        assert tool["input_schema"]["type"] == "object"


def test_handle_tool_use_dispatches_and_returns_citable_result():
    from rcca.agent import tool_defs

    result = tool_defs.handle_tool_use(_tool_use("get_process_data", {"lot": "LOT-AN-42"}))

    assert result["type"] == "tool_result"
    assert result["tool_use_id"] == "toolu_1"
    assert not result.get("is_error")
    payload = json.loads(result["content"])
    assert payload["source_id"] == "PD-LOT-AN-42"


def test_handle_tool_use_turns_lookup_error_into_is_error_result():
    from rcca.agent import tool_defs

    result = tool_defs.handle_tool_use(_tool_use("get_spec", {"spec_id": "NOPE"}))

    assert result["is_error"] is True
    assert result["tool_use_id"] == "toolu_1"
    assert "NOPE" in result["content"]


def test_run_investigation_gathers_via_tools_then_emits_structured_draft():
    from rcca.agent import orchestrator

    client = FakeAnthropicClient([
        # Phase 1: the agent calls a retrieval tool, then finishes gathering.
        _response("tool_use", [_tool_use("get_process_data", {"lot": "LOT-AN-42"})]),
        _response("end_turn", [_text("Gathered the evidence.")]),
        # Phase 2: the structured 8D emit.
        _response("end_turn", [_text(json.dumps(SAMPLE_DRAFT_JSON))]),
    ])

    draft = orchestrator.run_investigation(
        {"nc_id": "NC-DEMO-001", "lot": "LOT-AN-42", "spec_violated": "SPEC-AN-7"},
        client=client,
    )

    # The draft came back parsed and grounded.
    assert draft.causes[0].evidence[0].source_id == "PD-LOT-AN-42"

    # Phase 1 actually called the retrieval tool: a tool_result carrying real
    # corpus data was fed back to the model. Scan all messages across all calls
    # for a tool_result dict referencing the corpus source id.
    tool_results = [
        block
        for call in client.messages.calls
        for message in call["messages"]
        if isinstance(message["content"], list)
        for block in message["content"]
        if isinstance(block, dict) and block.get("type") == "tool_result"
    ]
    assert any("PD-LOT-AN-42" in tr["content"] for tr in tool_results)

    # Phase 2 requested structured output.
    assert any("output_config" in c and "format" in c["output_config"]
               for c in client.messages.calls)


def test_run_investigation_enforces_grounding_on_a_naked_claim():
    from rcca.agent import orchestrator

    naked = dict(SAMPLE_DRAFT_JSON)
    naked["candidate_causes"] = [
        {
            "category": "method",
            "description": "Operator error (no evidence).",
            "confidence": "high",
            "insufficient_evidence": False,
            "evidence": [],
        }
    ]
    client = FakeAnthropicClient([
        _response("end_turn", [_text("done")]),       # phase 1: no tools needed
        _response("end_turn", [_text(json.dumps(naked))]),  # phase 2: naked claim
    ])

    with pytest.raises(orchestrator.GroundingError):
        orchestrator.run_investigation(
            {"nc_id": "X", "lot": "L", "spec_violated": "S"}, client=client
        )


def test_run_investigation_accepts_insufficient_evidence_for_thin_data():
    from rcca.agent import orchestrator

    thin = dict(SAMPLE_DRAFT_JSON)
    thin["candidate_causes"] = [
        {
            "category": "measurement",
            "description": "Indeterminate — data reads nominal; needs gauge R&R.",
            "confidence": "low",
            "insufficient_evidence": True,
            "evidence": [],
        }
    ]
    client = FakeAnthropicClient([
        _response("end_turn", [_text("done")]),
        _response("end_turn", [_text(json.dumps(thin))]),
    ])

    draft = orchestrator.run_investigation(
        {"nc_id": "NC-DEMO-004", "lot": "LOT-MX-55", "spec_violated": "SPEC-DIM-1"},
        client=client,
    )
    assert draft.causes[0].insufficient_evidence is True
    assert draft.causes[0].evidence == []


def test_run_investigation_caps_a_verbose_cause_list():
    from rcca.agent import orchestrator

    cited = {
        "source_type": "process_data", "source_id": "PD-LOT-AN-42",
        "locator": "PD-AN-42-03", "excerpt": "11.3 V",
    }
    verbose = dict(SAMPLE_DRAFT_JSON)
    # A full 6M matrix, emitted twice (like the live model did) — 12 causes.
    verbose["candidate_causes"] = [
        {"category": cat, "description": f"{cat} cause.", "confidence": "high",
         "insufficient_evidence": False, "evidence": [cited]}
        for _ in range(2)
        for cat in ("machine", "man", "method", "material", "measurement", "environment")
    ]
    client = FakeAnthropicClient([
        _response("end_turn", [_text("done")]),
        _response("end_turn", [_text(json.dumps(verbose))]),
    ])

    draft = orchestrator.run_investigation(
        {"nc_id": "X", "lot": "L", "spec_violated": "S"}, client=client
    )
    assert len(draft.causes) <= 4
    assert len({c.category for c in draft.causes}) == len(draft.causes)  # one per category


def test_persist_draft_writes_proposal_causes_evidence_and_audit(db):
    from rcca.agent import schemas
    from rcca.agent.persist import persist_draft
    from rcca.models import (
        AuditEvent,
        CandidateCause,
        EvidenceRef,
        Investigation,
        Nonconformance,
        Section,
    )

    nc = Nonconformance.objects.create(nc_id="NC-DEMO-001", title="Anodize thin")
    investigation = Investigation.create_for(nc)
    draft = schemas.parse_draft(SAMPLE_DRAFT_JSON)

    persist_draft(investigation, draft)

    d2 = investigation.sections.get(d_number="D2")
    assert d2.agent_proposed_text == SAMPLE_DRAFT_JSON["d2_problem"]
    # The proposal seeds the engineer's working copy, but stays Drafted (unsigned).
    assert d2.current_text == SAMPLE_DRAFT_JSON["d2_problem"]
    assert d2.state == Section.State.DRAFTED

    d4 = investigation.sections.get(d_number="D4")
    cause = CandidateCause.objects.get(section=d4)
    assert cause.category == "machine"
    assert cause.confidence == "high"
    assert EvidenceRef.objects.filter(candidate_cause=cause).count() == 1

    # The agent's proposal is logged as the "what the agent proposed" audit side.
    draft_events = AuditEvent.objects.filter(
        investigation=investigation, event_type=AuditEvent.EventType.DRAFT
    )
    assert draft_events.count() == 5
    assert draft_events.first().actor == "agent"
