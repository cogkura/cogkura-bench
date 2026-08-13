"""Inspect a single benchmark query."""

from __future__ import annotations

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.runner import BenchmarkRunner


async def inspect_query(
    query_id: str,
    *,
    dataset_name: str,
    backend_name: str,
) -> int:
    """Re-run one query and print detailed diagnostics."""
    dataset = load_dataset(dataset_name)
    if query_id not in dataset.query_by_id():
        print(f"Unknown query id: {query_id}")
        return 1

    backend = create_backend(backend_name, dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    query_result = next(item for item in result.query_results if item.query_id == query_id)
    query = dataset.query_by_id()[query_id]
    events_by_id = dataset.event_by_id()

    print(f"Query: {query.query}")
    print(f"Capability: {query.capability.value}")
    print(f"Timestamp: {query.timestamp.isoformat()}")
    if query.valid_at is not None:
        print(f"Valid at: {query.valid_at.isoformat()}")
    print("")
    print("Expected evidence:")
    for event_id in query.expected_evidence_ids:
        event = events_by_id.get(event_id)
        print(f"  - {event_id}: {event.content if event else 'missing'}")
    print("")
    print("Retrieved evidence:")
    for rank, event_id in enumerate(query_result.retrieved_event_ids, start=1):
        event = events_by_id.get(event_id)
        print(f"  {rank}. {event_id}: {event.content if event else 'missing'}")
    if query_result.context_event_ids:
        print("")
        print(f"Context selection: {', '.join(query_result.context_event_ids)}")
        print(f"Context tokens: {query_result.context_tokens}")
    if query_result.assessment_flags:
        print("")
        print(f"Assessment flags: {', '.join(query_result.assessment_flags)}")
        print(f"Missing knowledge: {query_result.indicates_missing_knowledge}")
        print(f"Conflict: {query_result.indicates_conflict}")
    print("")
    print("Metrics:")
    for key in sorted(query_result.metrics):
        print(f"  {key}: {query_result.metrics[key]:.4f}")
    return 0
