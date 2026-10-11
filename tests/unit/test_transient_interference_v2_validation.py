"""Validation tests for transient_interference_v2 ground truth."""

from __future__ import annotations

import json
from pathlib import Path

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import Capability, UseAction


def test_v2_dataset_validates() -> None:
    assert validate_dataset("transient_interference_v2") == []
    dataset = load_dataset("transient_interference_v2")
    assert dataset.manifest.events == len(dataset.events)
    assert dataset.manifest.queries == len(dataset.queries)
    assert dataset.manifest.uses == len(dataset.uses)
    assert all(query.capability is Capability.TRANSIENT_INTERFERENCE for query in dataset.queries)


def test_v1_and_persistent_fixtures_are_unchanged() -> None:
    v1 = load_dataset("transient_interference_v1")
    assert v1.manifest.events == 20
    assert v1.manifest.queries == 10
    assert v1.uses == ()
    persistent = load_dataset("persistent_inhibition_v1")
    assert persistent.manifest.uses == 4


def test_opposite_directions_are_allowed_and_uses_follow_queries() -> None:
    dataset = load_dataset("transient_interference_v2")
    pair = dataset.query_by_id()["ti2-pair"]
    directions = {item.direction.value for item in pair.expected_interference_effects}
    assert directions == {"proactive", "retroactive"}
    uses = [action for action in dataset.actions if isinstance(action, UseAction)]
    queries = {
        action.query.id: action.timestamp
        for action in dataset.actions
        if action.__class__.__name__ == "QueryAction"
    }
    for action in uses:
        assert action.use.query_id in queries
        assert action.timestamp >= queries[action.use.query_id]


def test_same_directed_pair_cannot_be_expected_and_forbidden(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    dataset_dir = root / "clash"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "clash",
                "schema_version": 1,
                "events": 2,
                "queries": 1,
                "feedback": 0,
                "description": "",
                "required_capabilities": ["transient_interference"],
            }
        ),
        encoding="utf-8",
    )
    (dataset_dir / "events.jsonl").write_text(
        "\n".join(
            json.dumps(
                {
                    "id": event_id,
                    "timestamp": "2026-01-01T00:00:00+00:00",
                    "sequence": index,
                    "subject_id": "s",
                    "event_type": "documentation",
                    "content": event_id,
                }
            )
            for index, event_id in enumerate(("a", "b"), start=1)
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "queries.jsonl").write_text(
        json.dumps(
            {
                "id": "q",
                "timestamp": "2026-02-01T00:00:00+00:00",
                "capability": "transient_interference",
                "query": "q",
                "expected_interference_effects": [
                    {
                        "id": "exp",
                        "candidate_event_ids": ["a"],
                        "competitor_event_ids": ["b"],
                        "direction": "proactive",
                    }
                ],
                "forbidden_interference_effects": [
                    {
                        "id": "forb",
                        "candidate_event_ids": ["a"],
                        "competitor_event_ids": ["b"],
                        "direction": "proactive",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dataset_dir / "feedback.jsonl").write_text("", encoding="utf-8")
    errors = validate_dataset("clash", root=root)
    assert any("conflicts" in error for error in errors)
