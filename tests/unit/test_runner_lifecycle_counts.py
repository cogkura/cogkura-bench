"""Runner lifecycle call-count tests."""

from datetime import datetime

import pytest

from cogkurabench.backends.base import BackendCapabilities, MemoryBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.models import (
    AssessmentRequest,
    AssessmentResponse,
    BenchmarkFeedback,
    ContextRequest,
    ContextResponse,
    ProjectEvent,
    RetrievalRequest,
    RetrievalResponse,
)
from cogkurabench.runner import BenchmarkRunner


class _SpyBackend(MemoryBackend):
    def __init__(self) -> None:
        self.ingest_calls = 0
        self.prepare_calls = 0
        self.maintain_calls = 0
        self.ingested_event_count = 0

    @property
    def name(self) -> str:
        return "spy"

    @property
    def version(self) -> str | None:
        return "test"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            retrieve=True,
            select_context=False,
            assess=False,
            learn=False,
            forget=False,
            maintain=True,
        )

    async def reset(self) -> None:
        self.ingest_calls = 0
        self.prepare_calls = 0
        self.maintain_calls = 0
        self.ingested_event_count = 0

    async def ingest(self, events: list[ProjectEvent]) -> None:
        self.ingest_calls += 1
        self.ingested_event_count += len(events)

    async def prepare(self, *, as_of: datetime) -> None:
        self.prepare_calls += 1

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        return RetrievalResponse(items=(), latency_ms=1.0)

    async def select_context(self, request: ContextRequest) -> ContextResponse | None:
        return None

    async def assess(self, request: AssessmentRequest) -> AssessmentResponse | None:
        return None

    async def apply_feedback(self, feedback: BenchmarkFeedback) -> None:
        return None

    async def maintain(self, *, as_of: datetime) -> None:
        self.maintain_calls += 1


@pytest.mark.asyncio
async def test_customer_dataset_lifecycle_call_counts() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    backend = _SpyBackend()
    await BenchmarkRunner().run(dataset, backend, write_results=False)
    assert backend.ingested_event_count == 149
    assert backend.ingest_calls == 147
    assert backend.prepare_calls == 148
    assert backend.maintain_calls == 148


@pytest.mark.asyncio
async def test_reduced_fixture_lifecycle_counts() -> None:
    dataset = load_dataset("mini")
    backend = _SpyBackend()
    await BenchmarkRunner().run(dataset, backend, write_results=False)
    assert backend.ingested_event_count == len(dataset.events)
    distinct_timestamps = {action.timestamp for action in dataset.actions}
    assert backend.prepare_calls == len(distinct_timestamps)
    assert backend.maintain_calls == len(distinct_timestamps)
