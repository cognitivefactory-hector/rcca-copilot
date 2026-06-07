"""Live integration test — hits the real Anthropic API.

Skipped without ANTHROPIC_API_KEY, so it never runs in CI (no key there). Run it
locally to sanity-check tool-calling, structured output, and that the grounding
rule holds against the real model.
"""
import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="no ANTHROPIC_API_KEY; live agent test skipped (kept out of CI)",
)


def test_run_investigation_on_a_real_nc_is_grounded():
    from rcca import corpus
    from rcca.agent import orchestrator

    nc = corpus.SAMPLE_NCS["NC-DEMO-001"]

    # run_investigation calls enforce_grounding internally — if a cause were
    # uncited and unflagged it would raise GroundingError here.
    draft = orchestrator.run_investigation(nc)

    assert draft.sections["D4"]
    assert draft.causes, "expected at least one candidate cause"
    for cause in draft.causes:
        assert cause.evidence or cause.insufficient_evidence
