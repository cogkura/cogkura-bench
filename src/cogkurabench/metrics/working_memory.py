"""Working-memory metrics."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.models import BenchmarkQuery


def evidence_coverage_at_budget(
    selected_ids: Sequence[str],
    expected_ids: Sequence[str],
) -> float:
    """Required evidence selected divided by required evidence available."""
    if not expected_ids:
        return 1.0
    selected = set(selected_ids)
    hits = sum(1 for event_id in expected_ids if event_id in selected)
    return hits / len(expected_ids)


def context_precision(
    selected_ids: Sequence[str],
    relevant_ids: Sequence[str],
) -> float:
    """Relevant selected memories divided by all selected memories."""
    if not selected_ids:
        return 0.0
    relevant = set(relevant_ids)
    hits = sum(1 for event_id in selected_ids if event_id in relevant)
    return hits / len(selected_ids)


def token_efficiency(
    selected_ids: Sequence[str],
    relevant_ids: Sequence[str],
    *,
    estimated_tokens: int,
    events_text: dict[str, str],
) -> float:
    """Relevant evidence token share of total context tokens."""
    if estimated_tokens <= 0 or not selected_ids:
        return 0.0
    relevant = set(relevant_ids)
    relevant_tokens = sum(
        len(events_text.get(event_id, "").split())
        for event_id in selected_ids
        if event_id in relevant
    )
    return min(1.0, relevant_tokens / estimated_tokens)


def compute_working_memory_metrics(
    selected_ids: Sequence[str],
    query: BenchmarkQuery,
    *,
    estimated_tokens: int | None,
    events_text: dict[str, str],
) -> dict[str, float]:
    """Compute working-memory metrics for one query."""
    if query.capability.value != "working_memory":
        return {}
    if estimated_tokens is None:
        return {}
    relevant_ids = tuple(
        dict.fromkeys([*query.expected_evidence_ids, *query.acceptable_evidence_ids])
    )
    return {
        "evidence_coverage_at_budget": evidence_coverage_at_budget(
            selected_ids,
            query.expected_evidence_ids,
        ),
        "context_precision": context_precision(selected_ids, relevant_ids),
        "token_efficiency": token_efficiency(
            selected_ids,
            relevant_ids,
            estimated_tokens=estimated_tokens,
            events_text=events_text,
        ),
        "total_context_tokens": float(estimated_tokens),
        "selected_memory_count": float(len(selected_ids)),
        "unused_token_budget": float(max((query.prompt_budget_tokens or 0) - estimated_tokens, 0)),
    }
