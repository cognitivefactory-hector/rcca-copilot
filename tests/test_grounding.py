"""M3 — the grounding rule, in code: no uncited root cause may be confirmed.

This is the crown-jewel guarantee of the agent layer. Every candidate cause must
cite retrieved evidence or be explicitly flagged insufficient.
"""
import pytest

from rcca.agent import schemas
from rcca.agent.orchestrator import GroundingError, enforce_grounding, focus_causes


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


def _ev():
    return [schemas.DraftEvidence("process_data", "PD-LOT-AN-42", "PD-AN-42-03", "11.3 V")]


def test_focus_causes_dedupes_caps_and_keeps_best_per_category():
    # A verbose, duplicated 6M matrix like the live model produced.
    verbose = [
        _cause(category="machine", description="Rectifier voltage sag.",
               confidence="high", evidence=_ev()),
        _cause(category="machine", description="Rectifier voltage sag.",  # exact dup
               confidence="high", evidence=_ev()),
        _cause(category="machine", description="Rectifier voltage sag.",
               confidence="medium", evidence=_ev()),
        _cause(category="man", description="Operator error.", insufficient_evidence=True),
        _cause(category="method", description="Recipe error.", insufficient_evidence=True),
        _cause(category="material", description="Alloy variation.", insufficient_evidence=True),
        _cause(category="measurement", description="Gauge drift.", insufficient_evidence=True),
        _cause(category="environment", description="Bath temp in range.",
               confidence="low", evidence=_ev()),
    ]

    focused = focus_causes(verbose)

    assert len(focused) <= 4
    # no duplicate (category, description)
    keys = [(c.category, c.description) for c in focused]
    assert len(keys) == len(set(keys))
    # at most one per category
    cats = [c.category for c in focused]
    assert len(cats) == len(set(cats))
    # the best-supported cause (cited, high) leads
    assert focused[0].category == "machine"
    assert focused[0].confidence == "high"
    assert focused[0].evidence  # cited


def test_focus_causes_keeps_insufficient_when_thats_all_there_is():
    thin = [
        _cause(category="measurement", description="Indeterminate.", insufficient_evidence=True),
        _cause(category="method", description="Unknown.", insufficient_evidence=True),
    ]
    focused = focus_causes(thin)
    assert len(focused) == 2
    assert all(c.insufficient_evidence for c in focused)
