"""Retrieval tools — the only way the agent reaches the corpus.

Every result carries a citation envelope (source_type, source_id, locator) so the
grounding layer (M3) can build an EvidenceRef directly from any tool result. The
agent must fetch through these tools, never recall — that is what makes each
claim traceable.
"""
from dataclasses import asdict

from rcca import corpus


def get_spec(spec_id: str) -> dict:
    """Return the specification for `spec_id` as a citable record."""
    try:
        spec = corpus.SPECS[spec_id]
    except KeyError as exc:
        raise LookupError(f"Unknown spec id: {spec_id!r}") from exc

    return {
        "source_type": "spec",
        "source_id": spec.spec_id,
        "locator": spec.clause,
        "title": spec.title,
        "clause": spec.clause,
        "text": spec.text,
        "requirement": spec.requirement,
    }


def get_process_data(lot: str) -> dict:
    """Return the process-data table for `lot` as a citable record.

    Each row's stable `row_id` becomes its citation `locator`.
    """
    try:
        data = corpus.PROCESS_DATA[lot]
    except KeyError as exc:
        raise LookupError(f"Unknown lot: {lot!r}") from exc

    rows = []
    for row in data.rows:
        row_dict = asdict(row)
        row_dict["locator"] = row_dict.pop("row_id")
        rows.append(row_dict)

    return {
        "source_type": "process_data",
        "source_id": data.source_id,
        "lot": data.lot,
        "process": data.process,
        "rows": rows,
    }


def search_prior_ncs(query: str) -> list[dict]:
    """Keyword-search closed NCs for recurrence; most relevant first.

    Simple token overlap against each prior NC's keywords + free text — enough
    for a demo corpus, and deterministic so demos reproduce. Empty list if
    nothing matches.
    """
    tokens = {t for t in query.lower().split() if t}
    if not tokens:
        return []

    scored = []
    for nc in corpus.PRIOR_NCS:
        haystack = " ".join(
            (nc.title, nc.process, nc.defect_description, *nc.keywords)
        ).lower()
        score = sum(1 for t in tokens if t in haystack)
        if score:
            scored.append((score, nc))

    # Most relevant first; ties broken by id so ordering is deterministic.
    scored.sort(key=lambda pair: (-pair[0], pair[1].nc_id))

    return [
        {
            "source_type": "prior_nc",
            "source_id": nc.nc_id,
            "locator": "root_cause",
            "title": nc.title,
            "process": nc.process,
            "defect_description": nc.defect_description,
            "root_cause": nc.root_cause,
            "corrective_action": nc.corrective_action,
            "score": score,
        }
        for score, nc in scored
    ]
