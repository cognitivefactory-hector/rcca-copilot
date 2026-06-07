"""Structured 8D output: the JSON schema the agent emits, plus the dataclasses
the rest of the system works with.

The schema is what we hand to Claude via output_config.format; parse_draft turns
the validated JSON back into typed Python.
"""
from dataclasses import dataclass, field

# Maps each 8D section's schema key to its D-number.
SECTION_KEYS = {
    "d2_problem": "D2",
    "d3_containment": "D3",
    "d4_root_cause_summary": "D4",
    "d5_corrective_action": "D5",
    "d7_prevent_recurrence": "D7",
}

_CATEGORIES = ["man", "machine", "method", "material", "measurement", "environment"]
_CONFIDENCE = ["high", "medium", "low"]

_EVIDENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "source_type": {"type": "string"},
        "source_id": {"type": "string"},
        "locator": {"type": "string"},
        "excerpt": {"type": "string"},
    },
    "required": ["source_type", "source_id", "locator", "excerpt"],
    "additionalProperties": False,
}

_CAUSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": _CATEGORIES},
        "description": {"type": "string"},
        "confidence": {"type": "string", "enum": _CONFIDENCE},
        "insufficient_evidence": {"type": "boolean"},
        "evidence": {"type": "array", "items": _EVIDENCE_SCHEMA},
    },
    "required": ["category", "description", "confidence", "insufficient_evidence", "evidence"],
    "additionalProperties": False,
}

# The full 8D investigation schema handed to output_config.format.
INVESTIGATION_SCHEMA = {
    "type": "object",
    "properties": {
        "d2_problem": {"type": "string"},
        "d3_containment": {"type": "string"},
        "d4_root_cause_summary": {"type": "string"},
        "candidate_causes": {"type": "array", "items": _CAUSE_SCHEMA},
        "d5_corrective_action": {"type": "string"},
        "d7_prevent_recurrence": {"type": "string"},
    },
    "required": [
        "d2_problem",
        "d3_containment",
        "d4_root_cause_summary",
        "candidate_causes",
        "d5_corrective_action",
        "d7_prevent_recurrence",
    ],
    "additionalProperties": False,
}


@dataclass
class DraftEvidence:
    source_type: str
    source_id: str
    locator: str
    excerpt: str


@dataclass
class DraftCause:
    category: str
    description: str
    confidence: str
    insufficient_evidence: bool
    evidence: list[DraftEvidence] = field(default_factory=list)


@dataclass
class InvestigationDraft:
    # D-number -> proposed narrative text.
    sections: dict[str, str]
    # Candidate root causes, all under D4.
    causes: list[DraftCause]


def parse_draft(data: dict) -> InvestigationDraft:
    """Turn validated schema JSON into an InvestigationDraft."""
    sections = {d_number: data[key] for key, d_number in SECTION_KEYS.items()}
    causes = [
        DraftCause(
            category=c["category"],
            description=c["description"],
            confidence=c["confidence"],
            insufficient_evidence=c["insufficient_evidence"],
            evidence=[DraftEvidence(**e) for e in c["evidence"]],
        )
        for c in data["candidate_causes"]
    ]
    return InvestigationDraft(sections=sections, causes=causes)
