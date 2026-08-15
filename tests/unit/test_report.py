"""Result serialization tests."""

from datetime import UTC, datetime

from cogkurabench.evaluation.report import result_to_dict, write_result_json
from cogkurabench.evaluation.result import (
    BenchmarkResult,
    CapabilityResult,
    EnvironmentInfo,
    QueryResult,
)
from cogkurabench.models import Capability, RetrievedItem


def test_result_to_dict_round_trip(tmp_path) -> None:
    result = BenchmarkResult(
        benchmark_version="0.1.1",
        dataset_version="mini",
        backend_name="oracle",
        backend_version=None,
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        duration_ms=12.5,
        capability_results={
            "direct_recall": CapabilityResult(
                capability=Capability.DIRECT_RECALL,
                query_count=1,
                metrics={"recall@5": 1.0},
            )
        },
        query_results=(
            QueryResult(
                query_id="direct-001",
                capability=Capability.DIRECT_RECALL,
                retrieved_event_ids=("evt-001",),
                retrieved_items=(
                    RetrievedItem(
                        source_event_ids=("evt-001",),
                        text="FastAPI selected",
                        score=1.0,
                        rank=1,
                        memory_type="episode",
                        metadata={"activation": 2.0},
                    ),
                ),
                expected_event_ids=("evt-001",),
                metrics={"recall@5": 1.0},
                latency_ms=1.0,
                context_tokens=None,
            ),
        ),
        environment=EnvironmentInfo(
            python_version="3.12.0",
            platform="test",
            git_commit=None,
        ),
    )
    payload = result_to_dict(result)
    assert payload["backend_name"] == "oracle"
    assert payload["query_results"][0]["query_id"] == "direct-001"
    assert payload["query_results"][0]["retrieved_items"][0]["metadata"]["activation"] == 2.0

    output = tmp_path / "result.json"
    write_result_json(result, output)
    assert output.is_file()
