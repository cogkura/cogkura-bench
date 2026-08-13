"""Dataset loading, validation, and action-stream compilation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cogkurabench.exceptions import ValidationError
from cogkurabench.models import (
    BenchmarkAction,
    BenchmarkDataset,
    BenchmarkFeedback,
    BenchmarkQuery,
    Capability,
    DatasetManifest,
    EventType,
    ExpectedFact,
    FeedbackAction,
    FeedbackOutcome,
    IngestAction,
    ProjectEvent,
    QueryAction,
    SemanticFact,
)


def default_datasets_root() -> Path:
    """Return the repository datasets directory."""
    return Path(__file__).resolve().parents[2] / "datasets"


def list_datasets(root: Path | None = None) -> list[str]:
    """List available dataset names."""
    datasets_dir = root or default_datasets_root()
    if not datasets_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in datasets_dir.iterdir()
        if path.is_dir() and (path / "manifest.json").is_file()
    )


def load_dataset(name: str, root: Path | None = None) -> BenchmarkDataset:
    """Load a benchmark dataset by name."""
    datasets_dir = root or default_datasets_root()
    dataset_dir = datasets_dir / name
    if not dataset_dir.is_dir():
        raise ValidationError(f"Dataset not found: {name}")

    manifest = _load_manifest(dataset_dir / "manifest.json")
    events = _load_events(dataset_dir / "events.jsonl")
    queries = _load_queries(dataset_dir / "queries.jsonl")
    feedback = _load_feedback(dataset_dir / "feedback.jsonl")
    actions = _compile_actions(events, queries, feedback)

    return BenchmarkDataset(
        manifest=manifest,
        events=events,
        queries=queries,
        feedback=feedback,
        actions=actions,
        root=str(dataset_dir),
    )


def validate_dataset(name: str, root: Path | None = None) -> list[str]:
    """Validate a dataset and return a list of error messages (empty if valid)."""
    errors: list[str] = []
    try:
        dataset = load_dataset(name, root=root)
    except (ValidationError, json.JSONDecodeError, OSError) as exc:
        return [str(exc)]

    events_by_id = dataset.event_by_id()
    queries_by_id = dataset.query_by_id()

    if len(events_by_id) != len(dataset.events):
        errors.append("duplicate event IDs detected")

    if len(queries_by_id) != len(dataset.queries):
        errors.append("duplicate query IDs detected")

    feedback_ids = [item.id for item in dataset.feedback]
    if len(set(feedback_ids)) != len(feedback_ids):
        errors.append("duplicate feedback IDs detected")

    if len(dataset.events) != dataset.manifest.events:
        errors.append(
            f"manifest events count {dataset.manifest.events} "
            f"does not match loaded {len(dataset.events)}"
        )
    if len(dataset.queries) != dataset.manifest.queries:
        errors.append(
            f"manifest queries count {dataset.manifest.queries} "
            f"does not match loaded {len(dataset.queries)}"
        )
    if len(dataset.feedback) != dataset.manifest.feedback:
        errors.append(
            f"manifest feedback count {dataset.manifest.feedback} "
            f"does not match loaded {len(dataset.feedback)}"
        )

    present_capabilities = {query.capability for query in dataset.queries}
    for capability in dataset.manifest.required_capabilities:
        if capability not in present_capabilities:
            errors.append(f"missing required capability coverage: {capability.value}")

    for event in dataset.events:
        if event.timestamp.tzinfo is None:
            errors.append(f"event {event.id} timestamp is not timezone-aware")

    for query in dataset.queries:
        if query.timestamp.tzinfo is None:
            errors.append(f"query {query.id} timestamp is not timezone-aware")
        for evidence_id in (
            *query.expected_evidence_ids,
            *query.acceptable_evidence_ids,
        ):
            if evidence_id not in events_by_id:
                errors.append(f"query {query.id} references unknown event {evidence_id}")
            else:
                evidence_event = events_by_id[evidence_id]
                if evidence_event.timestamp > query.timestamp:
                    errors.append(f"query {query.id} references future evidence {evidence_id}")
        for evidence_id in query.forbidden_evidence_ids:
            if evidence_id not in events_by_id:
                errors.append(f"query {query.id} references unknown forbidden event {evidence_id}")
        if query.valid_at is not None:
            for evidence_id in query.expected_evidence_ids:
                historical_event = events_by_id.get(evidence_id)
                if historical_event is not None and historical_event.timestamp > query.valid_at:
                    errors.append(
                        f"query {query.id} expected evidence {evidence_id} is after valid_at"
                    )

    for item in dataset.feedback:
        if item.query_id not in queries_by_id:
            errors.append(f"feedback {item.id} references unknown query {item.query_id}")
        for event_id in item.target_event_ids:
            if event_id not in events_by_id:
                errors.append(f"feedback {item.id} references unknown event {event_id}")

    for event in dataset.events:
        for superseded_id in event.supersedes:
            if superseded_id not in events_by_id:
                errors.append(f"event {event.id} supersedes unknown event {superseded_id}")
        for related_id in event.related_events:
            if related_id not in events_by_id:
                errors.append(f"event {event.id} references unknown related event {related_id}")

    sequences = [(event.timestamp, event.sequence, event.id) for event in dataset.events]
    if len({(ts, seq) for ts, seq, _ in sequences}) != len(sequences):
        errors.append("event (timestamp, sequence) pairs are not unique")

    return errors


def _load_manifest(path: Path) -> DatasetManifest:
    data = _read_json(path)
    capabilities = tuple(Capability(value) for value in data.get("required_capabilities", []))
    return DatasetManifest(
        name=str(data["name"]),
        schema_version=int(data["schema_version"]),
        events=int(data["events"]),
        queries=int(data["queries"]),
        feedback=int(data.get("feedback", 0)),
        description=str(data.get("description", "")),
        required_capabilities=capabilities,
    )


def _load_events(path: Path) -> tuple[ProjectEvent, ...]:
    records = _read_jsonl(path)
    events = tuple(_parse_event(record) for record in records)
    return tuple(sorted(events, key=lambda e: (e.timestamp, e.sequence, e.id)))


def _load_queries(path: Path) -> tuple[BenchmarkQuery, ...]:
    records = _read_jsonl(path)
    return tuple(_parse_query(record) for record in records)


def _load_feedback(path: Path) -> tuple[BenchmarkFeedback, ...]:
    if not path.is_file():
        return ()
    records = _read_jsonl(path)
    return tuple(_parse_feedback(record) for record in records)


def _compile_actions(
    events: tuple[ProjectEvent, ...],
    queries: tuple[BenchmarkQuery, ...],
    feedback: tuple[BenchmarkFeedback, ...],
) -> tuple[BenchmarkAction, ...]:
    actions: list[BenchmarkAction] = [
        IngestAction(timestamp=event.timestamp, sequence=event.sequence, event=event)
        for event in events
    ]
    actions.extend(
        QueryAction(timestamp=query.timestamp, sequence=10_000 + index, query=query)
        for index, query in enumerate(queries)
    )
    actions.extend(
        FeedbackAction(timestamp=item.timestamp, sequence=20_000 + index, feedback=item)
        for index, item in enumerate(feedback)
    )
    return tuple(sorted(actions, key=_action_sort_key))


def _action_sort_key(action: BenchmarkAction) -> tuple[datetime, int, str]:
    if isinstance(action, IngestAction):
        suffix = f"ingest:{action.event.id}"
    elif isinstance(action, QueryAction):
        suffix = f"query:{action.query.id}"
    elif isinstance(action, FeedbackAction):
        suffix = f"feedback:{action.feedback.id}"
    else:
        suffix = "maintenance"
    return (action.timestamp, action.sequence, suffix)


def _parse_event(data: dict[str, Any]) -> ProjectEvent:
    semantic_facts = tuple(_parse_semantic_fact(item) for item in data.get("semantic_facts", []))
    return ProjectEvent(
        id=str(data["id"]),
        timestamp=_parse_datetime(data["timestamp"]),
        sequence=int(data["sequence"]),
        subject_id=str(data["subject_id"]),
        event_type=EventType(str(data["event_type"])),
        content=str(data["content"]),
        entities=tuple(str(item) for item in data.get("entities", [])),
        semantic_facts=semantic_facts,
        tags=tuple(str(item) for item in data.get("tags", [])),
        supersedes=tuple(str(item) for item in data.get("supersedes", [])),
        related_events=tuple(str(item) for item in data.get("related_events", [])),
    )


def _parse_query(data: dict[str, Any]) -> BenchmarkQuery:
    expected_fact = data.get("expected_fact")
    parsed_fact = None
    if expected_fact is not None:
        parsed_fact = ExpectedFact(
            subject=str(expected_fact["subject"]),
            predicate=str(expected_fact["predicate"]),
            object=str(expected_fact["object"]),
        )
    valid_at = data.get("valid_at")
    return BenchmarkQuery(
        id=str(data["id"]),
        timestamp=_parse_datetime(data["timestamp"]),
        capability=Capability(str(data["capability"])),
        query=str(data["query"]),
        goal=data.get("goal"),
        expected_evidence_ids=tuple(str(item) for item in data.get("expected_evidence_ids", [])),
        acceptable_evidence_ids=tuple(
            str(item) for item in data.get("acceptable_evidence_ids", [])
        ),
        forbidden_evidence_ids=tuple(str(item) for item in data.get("forbidden_evidence_ids", [])),
        expected_fact=parsed_fact,
        valid_at=_parse_datetime(valid_at) if valid_at is not None else None,
        should_abstain=bool(data.get("should_abstain", False)),
        retrieval_limit=int(data.get("retrieval_limit", 5)),
        prompt_budget_tokens=data.get("prompt_budget_tokens"),
    )


def _parse_feedback(data: dict[str, Any]) -> BenchmarkFeedback:
    return BenchmarkFeedback(
        id=str(data["id"]),
        timestamp=_parse_datetime(data["timestamp"]),
        query_id=str(data["query_id"]),
        outcome=FeedbackOutcome(str(data["outcome"])),
        target_event_ids=tuple(str(item) for item in data.get("target_event_ids", [])),
    )


def _parse_semantic_fact(data: dict[str, Any]) -> SemanticFact:
    return SemanticFact(
        subject=str(data["subject"]),
        predicate=str(data["predicate"]),
        object=str(data.get("object", data.get("object_value", ""))),
        cardinality=str(data.get("cardinality", "many")),
        polarity=str(data.get("polarity", "affirm")),
        qualifiers={str(k): str(v) for k, v in dict(data.get("qualifiers", {})).items()},
    )


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValidationError("datetime values must be timezone-aware.")
        return value.astimezone(UTC)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValidationError(f"datetime {value!r} must be timezone-aware.")
    return parsed.astimezone(UTC)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValidationError(f"{path} must contain a JSON object.")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise ValidationError(f"Missing required file: {path}")
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValidationError(f"{path}:{line_number} must contain a JSON object.")
            records.append(payload)
    return records


def ensure_valid_dataset(name: str, root: Path | None = None) -> BenchmarkDataset:
    """Load and validate a dataset, raising on errors."""
    errors = validate_dataset(name, root=root)
    if errors:
        raise ValidationError("; ".join(errors))
    return load_dataset(name, root=root)
