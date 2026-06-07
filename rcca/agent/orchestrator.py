"""The grounded agent: gather evidence via tool use, then emit a structured 8D.

Two phases. Phase 1 runs a manual agentic tool-use loop so every claim is fetched,
not recalled. Phase 2 emits the structured 8D via output_config.format. Then the
grounding rule is enforced in code — not just asked for in the prompt.
"""
import json

from .prompts import EMIT_INSTRUCTION, SYSTEM_PROMPT, render_intake
from .schemas import INVESTIGATION_SCHEMA, InvestigationDraft, parse_draft
from .tool_defs import TOOL_DEFS, handle_tool_use

# Headroom for the structured 8D; non-streaming stays under the SDK timeout.
MAX_TOKENS = 16000
# Cap the tool-use loop so a misbehaving model can't spin forever.
MAX_TOOL_ROUNDS = 12


class GroundingError(Exception):
    """Raised when a candidate cause asserts a root cause with no citation."""


_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
MAX_CAUSES = 4


def _cause_strength(cause):
    """Sort key: cited beats insufficient, then confidence, then evidence count."""
    cited = 1 if cause.evidence and not cause.insufficient_evidence else 0
    return (cited, _CONFIDENCE_RANK.get(cause.confidence, 0), len(cause.evidence))


def focus_causes(causes, max_total=MAX_CAUSES):
    """Trim the model's candidate causes to a focused, non-redundant set.

    A presentation/selection layer over the agent output (grounding is untouched —
    every kept cause keeps its citations): dedupe identical causes, keep the
    best-supported cause per 6M category, and cap to `max_total`, best first.
    Guarantees a tight list regardless of how verbose the model was.
    """
    seen = set()
    deduped = []
    for cause in causes:
        key = (cause.category, cause.description.strip().lower())
        if key not in seen:
            seen.add(key)
            deduped.append(cause)

    best_per_category = {}
    for cause in deduped:
        current = best_per_category.get(cause.category)
        if current is None or _cause_strength(cause) > _cause_strength(current):
            best_per_category[cause.category] = cause

    ordered = sorted(best_per_category.values(), key=_cause_strength, reverse=True)
    return ordered[:max_total]


def _system_blocks():
    # Stable prefix — prompt-cached so the method guide + corpus aren't re-billed.
    return [{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]


def _first_text(response) -> str:
    return next(block.text for block in response.content if block.type == "text")


def run_investigation(nc, *, client=None, model=None) -> InvestigationDraft:
    """Run the grounded agent: gather evidence via tools, emit a structured 8D.

    `client` defaults to a real Anthropic client; tests inject a fake. `model`
    defaults to settings.RCCA_MODEL.
    """
    if client is None:
        import anthropic

        client = anthropic.Anthropic()
    if model is None:
        from django.conf import settings

        model = settings.RCCA_MODEL

    system = _system_blocks()
    messages = [{"role": "user", "content": render_intake(nc)}]

    # Phase 1 — gather evidence through the retrieval tools.
    response = None
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=TOOL_DEFS,
            messages=messages,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
        )
        if response.stop_reason != "tool_use":
            break
        messages.append({"role": "assistant", "content": response.content})
        tool_results = [
            handle_tool_use(block)
            for block in response.content
            if getattr(block, "type", None) == "tool_use"
        ]
        messages.append({"role": "user", "content": tool_results})

    # Phase 2 — emit the structured 8D from the gathered evidence.
    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": EMIT_INSTRUCTION})
    final = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
        output_config={"format": {"type": "json_schema", "schema": INVESTIGATION_SCHEMA}},
    )

    draft = parse_draft(json.loads(_first_text(final)))
    draft.causes = focus_causes(draft.causes)  # tighten to a focused, non-redundant set
    enforce_grounding(draft)
    return draft


def enforce_grounding(draft: InvestigationDraft) -> None:
    """Reject any naked claim: a cause with no evidence that isn't flagged
    insufficient. Cited causes and explicitly-insufficient causes pass."""
    for cause in draft.causes:
        if not cause.evidence and not cause.insufficient_evidence:
            raise GroundingError(
                f"Uncited cause asserted without evidence: {cause.description!r}. "
                "Every cause must cite retrieved evidence or be flagged "
                "insufficient_evidence."
            )
