"""Inspect a single benchmark query."""

from __future__ import annotations

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.inspect_format import format_query_inspection
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

    print(format_query_inspection(query, query_result, events_by_id))
    return 0
