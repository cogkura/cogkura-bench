"""Runner tests for explicit use actions."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from cogkurabench.backends.base import MemoryBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.exceptions import ValidationError
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
    UseRequest,
    UseResponse,
)
from cogkurabench.runner import BenchmarkRunner


class _UseSpy(MemoryBackend):
    def __init__(self, *, record_use: bool, inhibition_traces: bool = False) -> None:
        self._record_use = record_use
        self._inhibition_traces = inhibition_traces
        self.retrieve_calls: list[str] = []
        self.use_calls: list[UseRequest] = []

    @property
    def name(self) -> str:
        return "use-spy"

    @property
    def version(self) -> str | None:
        return "test"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            record_use=self._record_use,
            inhibition_traces=self._inhibition_traces,
        )

    async def reset(self) -> None:
        self.retrieve_calls.clear()
        self.use_calls.clear()

    async def ingest(self, events: list[ProjectEvent]) -> None:
        return None

    async def prepare(self, *, as_of: datetime) -> None:
        return None

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        self.retrieve_calls.append(request.query_id)
        return RetrievalResponse(items=(), latency_ms=1.0)

    async def select_context(self, request: ContextRequest) -> ContextResponse | None:
        return None

    async def assess(self, request: AssessmentRequest) -> AssessmentResponse | None:
        return None

    async def apply_feedback(self, feedback: BenchmarkFeedback) -> None:
        return None

    async def record_use(self, request: UseRequest) -> UseResponse | None:
        self.use_calls.append(request)
        return UseResponse()

    async def maintain(self, *, as_of: datetime) -> None:
        return None


def _write_dataset(root: Path, *, use_before_cached: bool = False) -> None:
    dataset_dir = root / "uses"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "uses",
                "schema_version": 1,
                "events": 1,
                "queries": 2 if not use_before_cached else 1,
                "feedback": 0,
                "uses": 2 if not use_before_cached else 1,
                "description": "",
                "required_capabilities": ["persistent_inhibition"],
            }
        ),
        encoding="utf-8",
    )
    (dataset_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "id": "evt",
                "timestamp": "2026-04-01T09:00:00+00:00",
                "sequence": 1,
                "subject_id": "s",
                "event_type": "documentation",
                "content": "fact",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    queries = [
        {
            "id": "q1",
            "timestamp": "2026-04-01T10:00:00+00:00",
            "capability": "persistent_inhibition",
            "query": "first",
            "forbidden_persistent_inhibition": [{"id": "f1", "candidate_event_ids": ["evt"]}],
        }
    ]
    uses = [
        {
            "id": "use-1",
            "timestamp": "2026-04-01T10:00:00+00:00",
            "query_id": "q1",
            "selected_event_ids": ["evt"],
        }
    ]
    if not use_before_cached:
        queries.append(
            {
                "id": "q2",
                "timestamp": "2026-04-01T11:00:00+00:00",
                "capability": "persistent_inhibition",
                "query": "second",
                "forbidden_persistent_inhibition": [{"id": "f2", "candidate_event_ids": ["evt"]}],
            }
        )
        uses.append(
            {
                "id": "use-2",
                "timestamp": "2026-04-01T12:00:00+00:00",
                "query_id": "q1",
                "selected_event_ids": ["evt"],
            }
        )
    (dataset_dir / "queries.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in queries),
        encoding="utf-8",
    )
    (dataset_dir / "feedback.jsonl").write_text("", encoding="utf-8")
    (dataset_dir / "uses.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in uses),
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_use_follows_cached_query_and_can_repeat(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    _write_dataset(root)
    dataset = load_dataset("uses", root=root)
    backend = _UseSpy(record_use=True, inhibition_traces=True)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    assert backend.retrieve_calls == ["q1", "q2"]
    assert [call.use_id for call in backend.use_calls] == ["use-1", "use-2"]
    assert all(call.source_query_id == "q1" for call in backend.use_calls)
    assert [item.use_id for item in result.use_results] == ["use-1", "use-2"]


@pytest.mark.asyncio
async def test_unsupported_record_use_is_skipped(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    _write_dataset(root)
    dataset = load_dataset("uses", root=root)
    backend = _UseSpy(record_use=False)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    assert backend.use_calls == []
    assert result.use_results == ()


@pytest.mark.asyncio
async def test_missing_source_retrieval_fails(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    dataset_dir = root / "missing"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "missing",
                "schema_version": 1,
                "events": 1,
                "queries": 1,
                "feedback": 0,
                "uses": 1,
                "description": "",
                "required_capabilities": ["persistent_inhibition"],
            }
        ),
        encoding="utf-8",
    )
    (dataset_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "id": "evt",
                "timestamp": "2026-04-01T09:00:00+00:00",
                "sequence": 1,
                "subject_id": "s",
                "event_type": "documentation",
                "content": "fact",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "queries.jsonl").write_text(
        json.dumps(
            {
                "id": "present",
                "timestamp": "2026-04-01T12:00:00+00:00",
                "capability": "persistent_inhibition",
                "query": "later",
                "forbidden_persistent_inhibition": [{"id": "f", "candidate_event_ids": ["evt"]}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "feedback.jsonl").write_text("", encoding="utf-8")
    (dataset_dir / "uses.jsonl").write_text(
        json.dumps(
            {
                "id": "use-missing",
                "timestamp": "2026-04-01T11:00:00+00:00",
                "query_id": "present",
                "selected_event_ids": ["evt"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    dataset = load_dataset("missing", root=root)
    backend = _UseSpy(record_use=True)
    with pytest.raises(ValidationError, match="no retrieval"):
        await BenchmarkRunner().run(dataset, backend, write_results=False)
