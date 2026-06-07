"""Anthropic tool definitions and dispatch for the retrieval tools.

The agent reaches the corpus only through these — fetch, not recall. A tool
LookupError becomes an is_error tool_result so the model can recover (e.g. try a
different lot/spec) instead of crashing the loop.
"""
import json

from . import tools

TOOL_DEFS = [
    {
        "name": "get_process_data",
        "description": (
            "Fetch the process-data table for a manufacturing lot. Returns rows "
            "(each with a stable locator) of measured parameters around the run — "
            "use this to find anomalous trends behind a nonconformance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "lot": {"type": "string", "description": "The lot id, e.g. LOT-AN-42."}
            },
            "required": ["lot"],
        },
    },
    {
        "name": "get_spec",
        "description": (
            "Fetch a specification by id. Returns the clause, requirement text, and "
            "the measurable limit the nonconformance is judged against."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spec_id": {"type": "string", "description": "The spec id, e.g. SPEC-AN-7."}
            },
            "required": ["spec_id"],
        },
    },
    {
        "name": "search_prior_ncs",
        "description": (
            "Keyword-search closed prior nonconformances for recurrence. Returns "
            "matching NCs with their documented root cause and corrective action."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords, e.g. 'anodize coating thickness'.",
                }
            },
            "required": ["query"],
        },
    },
]

DISPATCH = {
    "get_process_data": lambda args: tools.get_process_data(args["lot"]),
    "get_spec": lambda args: tools.get_spec(args["spec_id"]),
    "search_prior_ncs": lambda args: tools.search_prior_ncs(args["query"]),
}


def handle_tool_use(block) -> dict:
    """Execute a tool_use block and return a tool_result message block."""
    try:
        result = DISPATCH[block.name](block.input)
        content = json.dumps(result)
        return {"type": "tool_result", "tool_use_id": block.id, "content": content}
    except (LookupError, KeyError) as exc:
        return {
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": f"Error: {exc}",
            "is_error": True,
        }
