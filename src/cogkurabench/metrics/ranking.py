"""Shared ranking helpers for grouped retrieval scoring."""

from __future__ import annotations

from collections.abc import Sequence

from cogkurabench.models import BenchmarkQuery, RetrievedItem


def order_retrieved_items(items: Sequence[RetrievedItem]) -> tuple[RetrievedItem, ...]:
    """Return items sorted by rank with stable tie-breaking on input order."""
    indexed = list(enumerate(items))
    indexed.sort(key=lambda pair: (pair[1].rank, pair[0]))
    return tuple(item for _, item in indexed)


def top_k_items(items: Sequence[RetrievedItem], k: int) -> tuple[RetrievedItem, ...]:
    """Return the first K ranked retrieved items."""
    if k <= 0:
        return ()
    return order_retrieved_items(items)[:k]


def flatten_source_event_ids(
    items: Sequence[RetrievedItem],
    *,
    deduplicate: bool = True,
) -> tuple[str, ...]:
    """Flatten source event IDs from items preserving item order."""
    ordered = order_retrieved_items(items)
    if not deduplicate:
        return tuple(event_id for item in ordered for event_id in item.source_event_ids)
    seen: set[str] = set()
    ordered_ids: list[str] = []
    for item in ordered:
        for event_id in item.source_event_ids:
            if event_id not in seen:
                seen.add(event_id)
                ordered_ids.append(event_id)
    return tuple(ordered_ids)


def retrieved_event_ids(
    ranked_ids: Sequence[str],
    *,
    deduplicate: bool = True,
) -> tuple[str, ...]:
    """Flatten ranked retrieved event IDs preserving order."""
    if not deduplicate:
        return tuple(ranked_ids)
    seen: set[str] = set()
    ordered: list[str] = []
    for event_id in ranked_ids:
        if event_id not in seen:
            seen.add(event_id)
            ordered.append(event_id)
    return tuple(ordered)


def item_source_set(item: RetrievedItem) -> frozenset[str]:
    """Return the set of source event IDs cited by one retrieved item."""
    return frozenset(item.source_event_ids)


def sources_in_items(items: Sequence[RetrievedItem]) -> set[str]:
    """Union of all source event IDs across items."""
    sources: set[str] = set()
    for item in items:
        sources.update(item.source_event_ids)
    return sources


def item_has_any(item: RetrievedItem, event_ids: Sequence[str]) -> bool:
    """Return whether the item cites any of the given event IDs."""
    if not event_ids:
        return False
    targets = set(event_ids)
    return any(event_id in targets for event_id in item.source_event_ids)


def item_is_forbidden(item: RetrievedItem, forbidden_ids: Sequence[str]) -> bool:
    """Return whether the item cites any forbidden event ID."""
    return item_has_any(item, forbidden_ids)


def relevance_grade(event_id: str, query: BenchmarkQuery) -> int:
    """Return nDCG relevance grade for an event ID."""
    if event_id in query.expected_evidence_ids:
        return 2
    if event_id in query.acceptable_evidence_ids:
        return 1
    return 0


def item_relevance_grade(item: RetrievedItem, query: BenchmarkQuery) -> int:
    """Return the highest relevance grade among an item's source event IDs."""
    return max(relevance_grade(event_id, query) for event_id in item.source_event_ids)
