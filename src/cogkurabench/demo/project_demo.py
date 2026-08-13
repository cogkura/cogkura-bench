"""Narrated benchmark demonstration."""

from __future__ import annotations

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.runner import BenchmarkRunner

_DEMO_QUERY_IDS = (
    "direct-001",
    "episodic-001",
    "assoc-001",
    "update-001",
    "temporal-hist-001",
    "forget-001",
    "wm-001",
    "learn-post-001",
    "meta-001",
)


async def run_demo(*, dataset_name: str = "mini", backend_name: str = "cogkura") -> int:
    """Run a narrated walkthrough of key benchmark scenarios."""
    print("CogKuraBench — Project Atlas demo")
    print("")
    dataset = load_dataset(dataset_name)
    backend = create_backend(backend_name, dataset)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    results_by_id = {item.query_id: item for item in result.query_results}
    events_by_id = dataset.event_by_id()

    for query_id in _DEMO_QUERY_IDS:
        query = dataset.query_by_id()[query_id]
        query_result = results_by_id[query_id]
        print(f"Query: {query.query}")
        print(f"Capability: {query.capability.value}")
        if query_result.retrieved_event_ids:
            print("Retrieved:")
            for rank, event_id in enumerate(query_result.retrieved_event_ids[:5], start=1):
                event = events_by_id.get(event_id)
                text = event.content if event is not None else event_id
                print(f"  {rank}. {text}")
        else:
            print("Retrieved: (none)")
        if query.expected_evidence_ids:
            print("Expected:")
            for event_id in query.expected_evidence_ids:
                event = events_by_id.get(event_id)
                print(f"  - {event.content if event is not None else event_id}")
        recall = query_result.metrics.get("recall@5", 0.0)
        status = (
            "PASS"
            if recall >= 1.0 or (query.should_abstain and not query_result.retrieved_event_ids)
            else "CHECK"
        )
        print(f"Result: {status}")
        if query_result.assessment_flags:
            print(f"Metamemory flags: {', '.join(query_result.assessment_flags)}")
        if query_result.context_event_ids:
            print(f"Working-memory selection: {', '.join(query_result.context_event_ids)}")
        print("")

    return 0
