"""Deterministic token-overlap retrieval baseline."""

from __future__ import annotations

import re
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

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens."""
    return set(_TOKEN_PATTERN.findall(text.lower()))


def overlap_score(query: str, content: str) -> float:
    """Jaccard-like overlap between query and content tokens."""
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    content_tokens = tokenize(content)
    if not content_tokens:
        return 0.0
    intersection = query_tokens & content_tokens
    return len(intersection) / len(query_tokens)


class TokenOverlapBackend:
    """Shallow deterministic retrieval baseline."""

    def __init__(self) -> None:
        self._events: list[ProjectEvent] = []

    @property
    def name(self) -> str:
        return "token-overlap"

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
        scored = [
            (overlap_score(request.query, event.content), event.timestamp, event.sequence, event)
            for event in visible
        ]
        scored.sort(key=lambda item: (-item[0], item[1], item[2], item[3].id))

        items: list[RetrievedItem] = []
        for rank, (score, _, _, event) in enumerate(scored[: request.limit], start=1):
            if score <= 0.0:
                continue
            items.append(
                RetrievedItem(
                    source_event_ids=(event.id,),
                    text=event.content,
                    score=score,
                    rank=rank,
                    memory_type="token_overlap",
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
