"""Reject undeclared source cases, missing identities and future-attribution gold."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from cogkurabench.dataset import default_datasets_root, validate_dataset


def test_v2_changes_only_the_declared_transition_expectation() -> None:
    root = default_datasets_root()
    v1, v2 = (root / f"source_aware_metamemory_v{version}" for version in (1, 2))
    assert validate_dataset(v2.name) == []
    assert (v1 / "events.jsonl").read_bytes() == (v2 / "events.jsonl").read_bytes()
    assert (v1 / "feedback.jsonl").read_bytes() == (v2 / "feedback.jsonl").read_bytes()
    old = [json.loads(line) for line in (v1 / "queries.jsonl").read_text().splitlines()]
    new = [json.loads(line) for line in (v2 / "queries.jsonl").read_text().splitlines()]
    target = next(row for row in new if row["id"] == "sm-withdrawn")
    checks = target["expected_source_assessment"]["checks"]
    assert checks["transition_event_ids"] == ["sm-chain-replace", "sm-chain-withdraw"]
    checks["transition_event_ids"] = ["sm-chain-withdraw"]
    assert new == old


@pytest.mark.parametrize(
    ("change", "message"),
    (
        ("missing", "requires source inspection and expectations"),
        ("future", "cannot see future knowledge"),
        ("bad-event", "unknown source event"),
    ),
)
def test_source_fixture_validation(tmp_path: Path, change: str, message: str) -> None:
    destination = tmp_path / "source_aware_metamemory_v1"
    shutil.copytree(default_datasets_root() / destination.name, destination)
    path = destination / "queries.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if change == "missing":
        rows[0].pop("expected_source_assessment")
    elif change == "future":
        rows[0]["source_inspection"]["as_of"] = "2027-01-01T00:00:00+00:00"
    else:
        rows[0]["expected_source_assessment"]["checks"]["event_ids"] = ["does-not-exist"]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    assert any(message in error for error in validate_dataset(destination.name, tmp_path))
