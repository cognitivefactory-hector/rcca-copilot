"""M2 — synthetic corpus + retrieval tools.

The agent must fetch evidence via these tools, never recall it. Tools are pure
functions over a static corpus with stable IDs, so demos are reproducible and
every result is citable.
"""
import json

import pytest

from rcca import corpus
from rcca.agent import tools


def test_get_spec_returns_known_spec_with_stable_id():
    result = tools.get_spec("SPEC-AN-7")

    assert result["source_type"] == "spec"
    assert result["source_id"] == "SPEC-AN-7"
    assert result["locator"]  # the clause is the citation locator
    assert "requirement" in result
    assert result["text"]


def test_get_spec_unknown_id_raises():
    with pytest.raises(LookupError):
        tools.get_spec("SPEC-DOES-NOT-EXIST")


def test_get_process_data_returns_citable_rows_with_stable_locators():
    result = tools.get_process_data("LOT-AN-42")

    assert result["source_type"] == "process_data"
    assert result["source_id"] == "PD-LOT-AN-42"
    assert result["lot"] == "LOT-AN-42"
    assert result["rows"]
    first = result["rows"][0]
    assert first["locator"] == "PD-AN-42-01"  # stable row id
    assert {"timestamp", "parameter", "value", "note"} <= set(first)


def test_get_process_data_unknown_lot_raises():
    with pytest.raises(LookupError):
        tools.get_process_data("LOT-NOPE")


def test_search_prior_ncs_finds_relevant_match():
    results = tools.search_prior_ncs("anodize coating thickness")

    assert results  # at least one hit
    top = results[0]
    assert top["source_type"] == "prior_nc"
    assert top["source_id"] == "NC-PRIOR-101"
    assert top["locator"] == "root_cause"
    assert "root_cause" in top


def test_search_prior_ncs_no_match_returns_empty_list():
    assert tools.search_prior_ncs("xyzzy plugh nonsense") == []


def test_search_prior_ncs_ordering_is_deterministic():
    a = tools.search_prior_ncs("plating adhesion")
    b = tools.search_prior_ncs("plating adhesion")
    assert [r["source_id"] for r in a] == [r["source_id"] for r in b]


def test_every_sample_nc_resolves_to_real_spec_and_process_data():
    for nc in corpus.SAMPLE_NCS.values():
        assert nc.spec_violated in corpus.SPECS, f"{nc.nc_id} cites missing spec"
        assert nc.lot in corpus.PROCESS_DATA, f"{nc.nc_id} cites missing process data"


def test_all_tool_results_are_json_serializable():
    json.dumps(tools.get_spec("SPEC-AN-7"))
    json.dumps(tools.get_process_data("LOT-AN-42"))
    json.dumps(tools.search_prior_ncs("anodize"))


def test_no_tool_ever_returns_a_planted_root_cause():
    """The answer key lives only on SampleNC, which no tool returns. Verify
    that no tool result leaks any planted root cause to the agent."""
    planted = [nc.planted_root_cause for nc in corpus.SAMPLE_NCS.values()]

    served = []
    for spec_id in corpus.SPECS:
        served.append(json.dumps(tools.get_spec(spec_id)))
    for lot in corpus.PROCESS_DATA:
        served.append(json.dumps(tools.get_process_data(lot)))
    for nc in corpus.SAMPLE_NCS.values():
        served.append(json.dumps(tools.search_prior_ncs(nc.title)))
    blob = "\n".join(served)

    for answer in planted:
        assert answer not in blob


def test_corpus_carries_a_synthetic_data_disclaimer():
    assert corpus.DISCLAIMER
    assert "fictional" in corpus.DISCLAIMER.lower()
