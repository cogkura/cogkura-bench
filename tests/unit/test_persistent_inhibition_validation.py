"""Dataset validation for explicit use and persistent inhibition."""

from __future__ import annotations

import json
from pathlib import Path

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import UseAction


def test_persistent_inhibition_dataset_validates() -> None:
    assert validate_dataset("persistent_inhibition_v1") == []


def test_existing_datasets_have_no_uses() -> None:
    for name in ("mini", "interference_v1", "transient_interference_v1"):
        dataset = load_dataset(name)
        assert dataset.uses == ()
        assert dataset.manifest.uses == 0
        assert not any(isinstance(action, UseAction) for action in dataset.actions)


def test_same_timestamp_query_precedes_use(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    dataset_dir = root / "order"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "order",
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
                "id": "q",
                "timestamp": "2026-04-01T10:00:00+00:00",
                "capability": "persistent_inhibition",
                "query": "q",
                "forbidden_persistent_inhibition": [
                    {"id": "forbid", "candidate_event_ids": ["evt"], "selected_event_ids": []}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "feedback.jsonl").write_text("", encoding="utf-8")
    (dataset_dir / "uses.jsonl").write_text(
        json.dumps(
            {
                "id": "use-a",
                "timestamp": "2026-04-01T10:00:00+00:00",
                "query_id": "q",
                "selected_event_ids": ["evt"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    dataset = load_dataset("order", root=root)
    kinds = [type(action).__name__ for action in dataset.actions if action.timestamp.hour == 10]
    assert kinds == ["QueryAction", "UseAction"]


def test_use_before_query_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    dataset_dir = root / "early"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "early",
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
                "id": "q",
                "timestamp": "2026-04-02T10:00:00+00:00",
                "capability": "persistent_inhibition",
                "query": "q",
                "forbidden_persistent_inhibition": [
                    {"id": "forbid", "candidate_event_ids": ["evt"]}
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "feedback.jsonl").write_text("", encoding="utf-8")
    (dataset_dir / "uses.jsonl").write_text(
        json.dumps(
            {
                "id": "use-early",
                "timestamp": "2026-04-01T10:00:00+00:00",
                "query_id": "q",
                "selected_event_ids": ["evt"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    errors = validate_dataset("early", root=root)
    assert any("occurs before source query" in error for error in errors)
