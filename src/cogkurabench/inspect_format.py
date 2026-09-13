"""Formatting helpers for query inspection output."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from cogkurabench.evaluation.result import QueryResult
from cogkurabench.models import (
    BenchmarkQuery,
    CompetitionExpectation,
    ProjectEvent,
    RetrievedItem,
    TransientInterferenceExpectation,
)


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


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def format_backend_metadata_section(
    metadata: Mapping[str, object],
    *,
    title: str,
    indent: int = 0,
) -> str:
    """Render backend metadata recursively without backend-specific assumptions."""
    if not metadata:
        return ""
    prefix = " " * indent
    lines = [f"{prefix}{title}:"]
    lines.extend(_format_metadata_lines(metadata, indent=indent + 2))
    return "\n".join(lines)


def _format_metadata_lines(value: object, *, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key in sorted(value):
            child = value[key]
            if isinstance(child, Mapping):
                lines.append(f"{prefix}{key}:")
                lines.extend(_format_metadata_lines(child, indent=indent + 2))
            elif isinstance(child, (list, tuple)):
                lines.append(f"{prefix}{key}: {_format_sequence(child)}")
            else:
                lines.append(f"{prefix}{key}: {child}")
        return lines
    return [f"{prefix}{value}"]


def _format_sequence(values: Sequence[object]) -> str:
    return ", ".join(str(item) for item in values)


def format_evidence_groups_section(query_result: QueryResult) -> str:
    """Render evidence-group diagnostic table."""
    if not query_result.evidence_group_diagnostics:
        return ""
    lines = ["Evidence groups", ""]
    lines.append(f"{'Group':<28} {'Recall':<8} {'Context':<8} Stage")
    for diag in query_result.evidence_group_diagnostics:
        lines.append(
            f"{diag.label:<28} {_yes_no(diag.retrieval_present):<8} "
            f"{_yes_no(diag.context_present):<8} {diag.stage or '—'}"
        )
    return "\n".join(lines)


def format_missing_group_retrieval_detail(
    query: BenchmarkQuery,
    query_result: QueryResult,
) -> str:
    """Render retrieval detail for groups absent from bounded context."""
    if not query_result.evidence_group_diagnostics:
        return ""
    lines: list[str] = []
    group_by_id = {group.id: group for group in query.expected_evidence_groups}
    has_context = query_result.context_tokens is not None
    for diag in query_result.evidence_group_diagnostics:
        if diag.context_present:
            continue
        lines.extend(["", f"{diag.label}", ""])
        lines.append(f"Broad recall: {_yes_no(diag.retrieval_present)}")
        if diag.first_retrieval_rank is not None:
            lines.append(f"First rank: {diag.first_retrieval_rank}")
        group = group_by_id.get(diag.group_id)
        if group is not None:
            matching = [
                item
                for item in query_result.retrieved_items
                if any(event_id in group.event_ids for event_id in item.source_event_ids)
            ]
            if matching:
                lines.append("Matching retrieval items:")
                for item in matching[:5]:
                    lines.append(f"  - rank {item.rank}: {', '.join(item.source_event_ids)}")
            else:
                lines.append("Evidence: (none in broad recall)")
        lines.append(f"Context: {'yes' if has_context else 'n/a'}")
        if diag.stage:
            lines.append(f"Stage: {diag.stage}")
    return "\n".join(lines)


def format_context_items_with_groups(query_result: QueryResult) -> str:
    """Render bounded context items with group labels."""
    if not query_result.context_items:
        return ""
    classification_by_rank = {item.rank: item for item in query_result.context_item_classifications}
    lines = ["Context items (with group labels):", ""]
    for item in query_result.context_items:
        lines.append(f"#{item.rank}")
        lines.append(f"  statement: {item.text}")
        lines.append(f"  events: {', '.join(item.source_event_ids)}")
        classification = classification_by_rank.get(item.rank)
        if classification is not None:
            if classification.matched_expected_groups:
                lines.append(f"  groups: {', '.join(classification.matched_expected_groups)}")
            if classification.matched_forbidden_groups:
                lines.append(
                    f"  forbidden groups: {', '.join(classification.matched_forbidden_groups)}"
                )
            if classification.classification == "unclassified":
                lines.append("  classification: unclassified")
            if classification.redundant_labelled_coverage:
                lines.append("  repeated labelled coverage: yes")
        lines.append("")
    return "\n".join(lines)


def _format_competition_expectation(expectation: CompetitionExpectation) -> str:
    candidate = ", ".join(expectation.candidate_event_ids)
    competitor = ", ".join(expectation.competitor_event_ids)
    direction = expectation.direction.value if expectation.direction is not None else "any"
    return f"  {expectation.id}: {candidate} -> {competitor} [{direction}]"


def format_competition_diagnostics_section(
    query: BenchmarkQuery,
    query_result: QueryResult,
) -> str:
    """Render expected, forbidden, and observed competition relationships."""
    if not (
        query.expected_competitions
        or query.forbidden_competitions
        or query_result.competition_diagnostics
    ):
        return ""

    lines = ["Competition diagnostics", ""]
    lines.append("Expected:")
    if query.expected_competitions:
        lines.extend(_format_competition_expectation(item) for item in query.expected_competitions)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Forbidden:")
    if query.forbidden_competitions:
        lines.extend(_format_competition_expectation(item) for item in query.forbidden_competitions)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Observed:")
    if query_result.competition_diagnostics:
        for diag in query_result.competition_diagnostics:
            candidate = ", ".join(diag.candidate_source_event_ids)
            competitor = ", ".join(diag.competitor_source_event_ids)
            lines.append(f"  {candidate} -> {competitor}")
            lines.append(f"    direction: {diag.direction.value}")
            if diag.strength is not None:
                lines.append(f"    strength: {diag.strength:.2f}")
            lines.append(f"    classification: {diag.classification}")
    else:
        lines.append("  (none)")

    expected_total = len(query.expected_competitions)
    expected_matched = sum(
        1 for diag in query_result.competition_diagnostics if diag.classification == "expected"
    )
    unexpected = sum(
        1 for diag in query_result.competition_diagnostics if diag.classification == "unexpected"
    )
    forbidden_matched = sum(
        1 for diag in query_result.competition_diagnostics if diag.classification == "forbidden"
    )
    unmapped = 0
    cogkura_meta = query_result.backend_metadata.get("cogkura", {})
    if isinstance(cogkura_meta, Mapping):
        unmapped = int(cogkura_meta.get("competition_pairs_unmapped", 0))

    lines.extend(
        [
            "",
            "Summary:",
            f"  expected matched: {expected_matched}/{expected_total}",
            f"  unexpected: {unexpected}",
            f"  forbidden matched: {forbidden_matched}",
            f"  unmapped: {unmapped}",
        ]
    )
    return "\n".join(lines)


def _format_interference_expectation(expectation: TransientInterferenceExpectation) -> str:
    candidate = ", ".join(expectation.candidate_event_ids)
    competitor = ", ".join(expectation.competitor_event_ids)
    return f"  {expectation.id}: {candidate} -> {competitor} [{expectation.direction.value}]"


def format_transient_interference_section(
    query: BenchmarkQuery,
    query_result: QueryResult,
) -> str:
    """Render expected, forbidden, and observed transient interference effects."""
    if not (
        query.expected_interference_effects
        or query.forbidden_interference_effects
        or query_result.transient_interference_candidate_diagnostics
        or query_result.transient_interference_diagnostics
    ):
        return ""

    lines = ["Transient interference", ""]
    lines.append("Expected:")
    if query.expected_interference_effects:
        lines.extend(
            _format_interference_expectation(item) for item in query.expected_interference_effects
        )
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Forbidden:")
    if query.forbidden_interference_effects:
        lines.extend(
            _format_interference_expectation(item) for item in query.forbidden_interference_effects
        )
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Candidates:")
    if query_result.transient_interference_candidate_diagnostics:
        for candidate in query_result.transient_interference_candidate_diagnostics:
            candidate_ids = ", ".join(candidate.candidate_source_event_ids)
            delta = candidate.activation_after - candidate.activation_before
            lines.append(f"  {candidate_ids}")
            lines.append(
                f"    activation: {candidate.activation_before:.2f} -> "
                f"{candidate.activation_after:.2f} (delta {delta:+.2f})"
            )
            lines.append(f"    total penalty: {candidate.total_penalty:.2f}")
            if candidate.rank_before is not None and candidate.rank_after is not None:
                lines.append(f"    rank: {candidate.rank_before} -> {candidate.rank_after}")
            lines.append(
                "    crossed threshold: "
                f"{'yes' if candidate.crossed_activation_threshold else 'no'}"
            )
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append("Contributions:")
    if query_result.transient_interference_diagnostics:
        for diag in query_result.transient_interference_diagnostics:
            competitor = ", ".join(diag.competitor_source_event_ids)
            lines.append(f"  -> {competitor}")
            lines.append(f"    direction: {diag.direction.value}")
            lines.append(f"    pressure: {diag.pressure:.2f}")
            lines.append(f"    classification: {diag.classification}")
    else:
        lines.append("  (none)")

    cogkura_meta = query_result.backend_metadata.get("cogkura", {})
    if isinstance(cogkura_meta, Mapping):
        unmapped = int(cogkura_meta.get("interference_contributions_unmapped", 0))
        lines.extend(["", f"Unmapped contributions: {unmapped}"])
    return "\n".join(lines)


def format_cogkura_competition_inspection_section(
    backend_metadata: Mapping[str, object],
) -> str:
    """Render CogKura-specific competition inspection counters."""
    cogkura_meta = backend_metadata.get("cogkura", {})
    if not isinstance(cogkura_meta, Mapping):
        return ""
    inspection = cogkura_meta.get("competition_inspection")
    if not isinstance(inspection, Mapping):
        return ""
    lines = ["Competition inspection", ""]
    lines.append(f"Candidates with competitors: {inspection.get('candidates_with_competitors', 0)}")
    lines.append(f"Competition pairs evaluated: {inspection.get('evaluated_competitor_pairs', 0)}")
    lines.append(f"Competition pairs accepted: {inspection.get('accepted_competition_pairs', 0)}")
    strongest = inspection.get("strongest_competition")
    if strongest is not None:
        lines.append(f"Strongest competition: {strongest}")
    lines.append(f"Proactive: {inspection.get('proactive_count', 0)}")
    lines.append(f"Retroactive: {inspection.get('retroactive_count', 0)}")
    lines.append(f"Co-temporal: {inspection.get('co_temporal_count', 0)}")
    return "\n".join(lines)


def format_structured_relationships_section(
    backend_metadata: Mapping[str, object],
) -> str:
    """Render relationship diagnostics when catalogue relationships were ingested."""
    cogkura_meta = backend_metadata.get("cogkura", {})
    if not isinstance(cogkura_meta, Mapping):
        return ""
    relationships_ingested = cogkura_meta.get("relationships_ingested", 0)
    inspection = cogkura_meta.get("relationship_inspection", {})
    if not relationships_ingested and not (
        isinstance(inspection, Mapping) and inspection.get("relationship_paths_used", 0)
    ):
        return ""
    lines = ["Structured relationships", ""]
    lines.append(f"Relationships ingested: {relationships_ingested}")
    if isinstance(inspection, Mapping):
        lines.append(f"Relationship seed count: {inspection.get('relationship_seed_count', 0)}")
        lines.append(f"Relationship paths used: {inspection.get('relationship_paths_used', 0)}")
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
    group_section = format_evidence_groups_section(query_result)
    if group_section:
        sections.extend(["", group_section])
        sections.append(format_missing_group_retrieval_detail(query, query_result))
    if query_result.context_items or query_result.context_event_ids:
        context_with_groups = format_context_items_with_groups(query_result)
        if context_with_groups:
            sections.extend(["", context_with_groups])
        else:
            sections.extend(
                [
                    "",
                    format_retrieved_items_section("Context items:", query_result.context_items),
                ]
            )
        sections.append(f"Context tokens: {query_result.context_tokens}")
    if query_result.assessment_flags:
        sections.extend(
            [
                "",
                f"Assessment flags: {', '.join(query_result.assessment_flags)}",
                f"Missing knowledge: {query_result.indicates_missing_knowledge}",
                f"Conflict: {query_result.indicates_conflict}",
            ]
        )
    metadata_section = format_backend_metadata_section(
        query_result.backend_metadata,
        title="Retrieval backend metadata",
    )
    if metadata_section:
        sections.extend(["", metadata_section])
    competition_section = format_competition_diagnostics_section(query, query_result)
    if competition_section:
        sections.extend(["", competition_section])
    transient_section = format_transient_interference_section(query, query_result)
    if transient_section:
        sections.extend(["", transient_section])
    cogkura_competition_section = format_cogkura_competition_inspection_section(
        query_result.backend_metadata
    )
    if cogkura_competition_section:
        sections.extend(["", cogkura_competition_section])
    relationship_section = format_structured_relationships_section(query_result.backend_metadata)
    if relationship_section:
        sections.extend(["", relationship_section])
    context_metadata_section = format_backend_metadata_section(
        query_result.context_backend_metadata,
        title="Context backend metadata",
    )
    if context_metadata_section:
        sections.extend(["", context_metadata_section])
    sections.extend(["", "Metrics:"])
    for key in sorted(query_result.metrics):
        sections.append(f"  {key}: {query_result.metrics[key]:.4f}")
    return "\n".join(sections)
