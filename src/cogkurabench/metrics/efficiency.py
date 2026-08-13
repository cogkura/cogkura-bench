"""Efficiency metrics."""

from __future__ import annotations


def compute_efficiency_metrics(
    *,
    retrieval_latency_ms: float,
    context_latency_ms: float | None,
    retrieved_count: int,
    selected_count: int,
    context_tokens: int | None,
) -> dict[str, float]:
    """Record per-query efficiency metrics."""
    metrics = {
        "retrieval_latency_ms": retrieval_latency_ms,
        "memories_retrieved": float(retrieved_count),
        "memories_selected": float(selected_count),
        "estimated_context_tokens": float(context_tokens or 0),
        "external_api_calls": 0.0,
        "estimated_cost_usd": 0.0,
    }
    if context_latency_ms is not None:
        metrics["context_selection_latency_ms"] = context_latency_ms
    return metrics
