"""Oracle backend for benchmark validation."""

from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import datetime

from cogkurabench.models import (
    AssessmentRequest,
    AssessmentResponse,
    BackendCapabilities,
    BenchmarkFeedback,
    BenchmarkQuery,
    ContextRequest,
    ContextResponse,
    ProjectEvent,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedItem,
)


class OracleBackend:
    """Returns declared expected evidence for each query."""

    def __init__(
        self, queries: tuple[BenchmarkQuery, ...], events: tuple[ProjectEvent, ...]
    ) -> None:
        self._queries = {query.id: query for query in queries}
        self._events = {event.id: event for event in events}

    @property
    def name(self) -> str:
        return "oracle"

    @property
    def version(self) -> str | None:
        return None

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            retrieve=True,
            select_context=False,
            assess=False,
            learn=False,
            forget=False,
            maintain=False,
        )

    async def reset(self) -> None:
        return None

    async def ingest(self, events: Sequence[ProjectEvent]) -> None:
        return None

    async def prepare(self, *, as_of: datetime) -> None:
        return None

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        start = time.perf_counter()
        query = self._queries[request.query_id]
        ordered_event_ids = _oracle_retrieval_event_ids(query)
        items: list[RetrievedItem] = []
        for rank, event_id in enumerate(ordered_event_ids[: request.limit], start=1):
            event = self._events[event_id]
            items.append(
                RetrievedItem(
                    source_event_ids=(event_id,),
                    text=event.content,
                    score=1.0,
                    rank=rank,
                    memory_type="oracle",
                )
            )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return RetrievalResponse(items=tuple(items), latency_ms=latency_ms)

    async def select_context(self, request: ContextRequest) -> ContextResponse | None:
        return None

    async def assess(self, request: AssessmentRequest) -> AssessmentResponse | None:
        return None

    async def apply_feedback(self, feedback: BenchmarkFeedback) -> None:
        return None

    async def maintain(self, *, as_of: datetime) -> None:
        return None


def _oracle_retrieval_event_ids(query: BenchmarkQuery) -> tuple[str, ...]:
    """Return oracle retrieval event IDs, preferring one hit per expected group."""
    ordered: list[str] = []
    seen: set[str] = set()
    if query.expected_evidence_groups:
        for group in query.expected_evidence_groups:
            if group.event_ids:
                first_id = group.event_ids[0]
                if first_id not in seen:
                    ordered.append(first_id)
                    seen.add(first_id)
    for event_id in query.expected_evidence_ids:
        if event_id not in seen:
            ordered.append(event_id)
            seen.add(event_id)
    return tuple(ordered)
