"""Full-history retrieval baseline."""

from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import datetime

from cogkurabench.models import (
    AssessmentRequest,
    AssessmentResponse,
    BackendCapabilities,
    BenchmarkFeedback,
    ContextRequest,
    ContextResponse,
    ProjectEvent,
    RetrievalRequest,
    RetrievalResponse,
    RetrievedItem,
)


class FullHistoryBackend:
    """Returns all visible events in chronological order."""

    def __init__(self) -> None:
        self._events: list[ProjectEvent] = []

    @property
    def name(self) -> str:
        return "full-history"

    @property
    def version(self) -> str | None:
        return None

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities()

    async def reset(self) -> None:
        self._events.clear()

    async def ingest(self, events: Sequence[ProjectEvent]) -> None:
        self._events.extend(events)
        self._events.sort(key=lambda event: (event.timestamp, event.sequence, event.id))

    async def prepare(self, *, as_of: datetime) -> None:
        return None

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        start = time.perf_counter()
        visible = [event for event in self._events if event.timestamp <= request.as_of]
        items: list[RetrievedItem] = []
        for rank, event in enumerate(visible[: request.limit], start=1):
            items.append(
                RetrievedItem(
                    source_event_ids=(event.id,),
                    text=event.content,
                    score=None,
                    rank=rank,
                    memory_type="full_history",
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
