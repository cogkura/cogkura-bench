"""Inspect a single benchmark query."""

from __future__ import annotations

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.inspect_format import format_query_inspection, format_use_inspection
from cogkurabench.runner import BenchmarkRunner


async def inspect_query(
    query_id: str,
    *,
    dataset_name: str,
    backend_name: str,
) -> int:
    """Re-run the dataset and print diagnostics for a query or use id."""
    dataset = load_dataset(dataset_name)
    queries = dataset.query_by_id()
    uses = {item.id: item for item in dataset.uses}
    if query_id not in queries and query_id not in uses:
        print(f"Unknown query or use id: {query_id}")
        return 1

    backend = create_backend(backend_name, dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    if query_id in queries:
        query_result = next(item for item in result.query_results if item.query_id == query_id)
        query = queries[query_id]
        print(format_query_inspection(query, query_result, dataset.event_by_id()))
        related = [item for item in result.use_results if item.source_query_id == query_id]
        for use_result in related:
            print()
            print(format_use_inspection(use_result))
        return 0

    recorded = next((item for item in result.use_results if item.use_id == query_id), None)
    if recorded is None:
        print(f"Use {query_id} was not recorded by backend {backend_name}")
        return 1
    print(format_use_inspection(recorded))
    return 0
