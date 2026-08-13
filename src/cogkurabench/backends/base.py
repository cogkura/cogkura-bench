"""Neutral memory backend protocol."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

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
)


class MemoryBackend(Protocol):
    """Contract for benchmark memory backends."""

    @property
    def name(self) -> str:
        """Backend identifier."""
        ...

    @property
    def version(self) -> str | None:
        """Optional backend version string."""
        ...

    @property
    def capabilities(self) -> BackendCapabilities:
        """Supported optional features."""
        ...

    async def reset(self) -> None:
        """Reset backend state for a new benchmark run."""
        ...

    async def ingest(self, events: Sequence[ProjectEvent]) -> None:
        """Ingest newly visible project events."""
        ...

    async def prepare(self, *, as_of: datetime) -> None:
        """Prepare memory state as of the simulated time."""
        ...

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Retrieve memories for a query."""
        ...

    async def select_context(self, request: ContextRequest) -> ContextResponse | None:
        """Select working-memory context under a budget, if supported."""
        ...

    async def assess(self, request: AssessmentRequest) -> AssessmentResponse | None:
        """Assess memory state for metamemory queries, if supported."""
        ...

    async def apply_feedback(self, feedback: BenchmarkFeedback) -> None:
        """Apply learning feedback, if supported."""
        ...

    async def maintain(self, *, as_of: datetime) -> None:
        """Run scheduled maintenance such as forgetting, if supported."""
        ...
