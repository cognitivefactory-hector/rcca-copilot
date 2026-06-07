"""M3 — the grounding rule, in code: no uncited root cause may be confirmed.

This is the crown-jewel guarantee of the agent layer. Every candidate cause must
cite retrieved evidence or be explicitly flagged insufficient.
"""
import pytest

from rcca.agent import schemas
from rcca.agent.orchestrator import GroundingError, enforce_grounding


def _cause(**kw):
    defaults = dict(
        category="machine",
        description="A cause.",
        confidence="high",
        insufficient_evidence=False,
        evidence=[],
    )
    defaults.update(kw)
    return schemas.DraftCause(**defaults)


def _draft(causes):
    return schemas.InvestigationDraft(
        sections={d: f"{d} text" for d in ("D2", "D3", "D4", "D5", "D7")},
        causes=causes,
    )


def test_enforce_grounding_rejects_a_naked_claim():
    naked = _cause(evidence=[], insufficient_evidence=False)
    with pytest.raises(GroundingError):
        enforce_grounding(_draft([naked]))


def test_enforce_grounding_accepts_a_cited_cause():
    cited = _cause(
        evidence=[
            schemas.DraftEvidence("process_data", "PD-LOT-AN-42", "PD-AN-42-03", "11.3 V")
        ],
        insufficient_evidence=False,
    )
    enforce_grounding(_draft([cited]))  # must not raise


def test_enforce_grounding_accepts_an_insufficient_evidence_cause():
    flagged = _cause(evidence=[], insufficient_evidence=True)
    enforce_grounding(_draft([flagged]))  # must not raise
