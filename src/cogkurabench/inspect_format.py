"""Formatting helpers for query inspection output."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.models import BenchmarkQuery, ProjectEvent, RetrievedItem


def format_query_header(query: BenchmarkQuery) -> str:
    """Render query identity, capability, and cue fields."""
    lines = [
        f"Query id: {query.id}",
        f"Capability: {query.capability.value}",
        f"Query: {query.query}",
        f"Timestamp: {query.timestamp.isoformat()}",
    ]
    if query.valid_at is not None:
        lines.append(f"Valid at: {query.valid_at.isoformat()}")
    if query.goal is not None:
        lines.append(f"Goal: {query.goal}")
    if query.entity_ids:
        lines.append(f"Entity ids: {', '.join(query.entity_ids)}")
    if query.predicate is not None:
        lines.append(f"Predicate: {query.predicate}")
    if query.object_value is not None:
        lines.append(f"Object value: {query.object_value}")
    if query.should_abstain:
        lines.append("Should abstain: true")
    return "\n".join(lines)


def format_evidence_ids(
    title: str,
    event_ids: Sequence[str],
    events_by_id: Mapping[str, ProjectEvent],
) -> str:
    """Render a titled list of benchmark event IDs."""
    lines = [title]
    if not event_ids:
        lines.append("  (none)")
        return "\n".join(lines)
    for event_id in event_ids:
        event = events_by_id.get(event_id)
        content = event.content if event is not None else "missing"
        lines.append(f"  - {event_id}: {content}")
    return "\n".join(lines)


def format_retrieved_item(item: RetrievedItem) -> str:
    """Render one retrieved item with optional backend metadata."""
    lines = [
        f"Rank {item.rank}",
        f"Kind: {item.memory_type or 'unknown'}",
        f"Events: {', '.join(item.source_event_ids)}",
        f"Score: {item.score if item.score is not None else 'n/a'}",
        f"Text: {item.text}",
    ]
    if item.metadata:
        lines.append("Metadata:")
        for key in sorted(item.metadata):
            value = item.metadata[key]
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_retrieved_items_section(
    title: str,
    items: Sequence[RetrievedItem],
) -> str:
    """Render a titled block of retrieved items."""
    lines = [title]
    if not items:
        lines.append("  (none)")
        return "\n".join(lines)
    for item in items:
        lines.append("")
        lines.extend(f"  {line}" for line in format_retrieved_item(item).splitlines())
    return "\n".join(lines)


def format_query_inspection(
    query: BenchmarkQuery,
    query_result: QueryResult,
    events_by_id: Mapping[str, ProjectEvent],
) -> str:
    """Render a full inspection report for one query."""
    sections = [
        format_query_header(query),
        "",
        format_evidence_ids("Expected evidence:", query.expected_evidence_ids, events_by_id),
        "",
        format_evidence_ids(
            "Acceptable evidence:",
            query.acceptable_evidence_ids,
            events_by_id,
        ),
        "",
        format_evidence_ids(
            "Forbidden evidence:",
            query.forbidden_evidence_ids,
            events_by_id,
        ),
        "",
        format_retrieved_items_section("Retrieved items:", query_result.retrieved_items),
    ]
    if query_result.context_items or query_result.context_event_ids:
        sections.extend(
            [
                "",
                format_retrieved_items_section("Context items:", query_result.context_items),
                f"Context tokens: {query_result.context_tokens}",
            ]
        )
    if query_result.assessment_flags:
        sections.extend(
            [
                "",
                f"Assessment flags: {', '.join(query_result.assessment_flags)}",
                f"Missing knowledge: {query_result.indicates_missing_knowledge}",
                f"Conflict: {query_result.indicates_conflict}",
            ]
        )
    sections.extend(["", "Metrics:"])
    for key in sorted(query_result.metrics):
        sections.append(f"  {key}: {query_result.metrics[key]:.4f}")
    return "\n".join(sections)
