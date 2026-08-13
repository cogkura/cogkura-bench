"""Helios dataset integration tests."""

import json
import re
from pathlib import Path

import pytest

from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.runner import BenchmarkRunner

DATASET_ROOT = Path(__file__).resolve().parents[2] / "datasets" / "helios_v1"

_PARAPHRASE_CORE_QUERY_IDS = (
    "helios-update-001",
    "helios-temporal-curr-001",
    "helios-assoc-001",
    "helios-forget-001",
    "helios-learn-pre-001",
    "helios-learn-post-001",
)


def test_helios_v1_validates() -> None:
    assert validate_dataset("helios_v1") == []


def test_helios_manifest_counts_match() -> None:
    dataset = load_dataset("helios_v1")
    assert dataset.manifest.events == 550
    assert dataset.manifest.queries == 49
    assert dataset.manifest.feedback == 3


def test_no_fill_queries_or_team_prefix_mill() -> None:
    queries = (DATASET_ROOT / "queries.jsonl").read_text(encoding="utf-8").splitlines()
    for line in queries:
        if not line.strip():
            continue
        record = json.loads(line)
        assert not str(record["id"]).startswith("helios-fill-")

    events = (DATASET_ROOT / "events.jsonl").read_text(encoding="utf-8").splitlines()
    for line in events:
        if not line.strip():
            continue
        record = json.loads(line)
        content = str(record["content"])
        assert not content.startswith("Helios team ")


def test_no_numbered_distractor_mill() -> None:
    events = (DATASET_ROOT / "events.jsonl").read_text(encoding="utf-8").splitlines()
    for line in events:
        if not line.strip():
            continue
        record = json.loads(line)
        content = str(record["content"])
        assert "{n}" not in content
        assert not re.search(r"scenario \d+", content, flags=re.IGNORECASE)


def test_core_queries_include_structured_cues() -> None:
    dataset = load_dataset("helios_v1")
    queries = dataset.query_by_id()
    assert queries["helios-update-001"].entity_ids == ("charge-ledger",)
    assert queries["helios-wm-001"].goal == "Prefer the live ledger store; ignore stale wiki pages."
    assert queries["helios-assoc-001"].entity_ids == ("finance", "charge-ledger")


@pytest.mark.asyncio
async def test_oracle_recall_at_five_is_perfect_on_expected_evidence() -> None:
    dataset = load_dataset("helios_v1")
    backend = OracleBackend(dataset.queries, dataset.events)
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    scored = [qr for qr in result.query_results if qr.expected_event_ids]
    assert scored
    assert all(qr.metrics["recall@5"] == 1.0 for qr in scored)


@pytest.mark.asyncio
async def test_learning_delta_zero_with_identical_wording() -> None:
    dataset = load_dataset("helios_v1")
    backend = TokenOverlapBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    post = next(qr for qr in result.query_results if qr.query_id == "helios-learn-post-001")
    assert post.metrics.get("delta_recall@5", 0.0) == 0.0


def test_learn_pre_post_share_query_text() -> None:
    dataset = load_dataset("helios_v1")
    queries = dataset.query_by_id()
    pre = queries["helios-learn-pre-001"]
    post = queries["helios-learn-post-001"]
    assert pre.query == post.query


@pytest.mark.asyncio
async def test_token_overlap_not_perfect_on_paraphrase_core_queries() -> None:
    dataset = load_dataset("helios_v1")
    backend = TokenOverlapBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    by_id = {qr.query_id: qr for qr in result.query_results}
    recalls = [
        by_id[query_id].metrics.get("recall@5", 0.0) for query_id in _PARAPHRASE_CORE_QUERY_IDS
    ]
    assert any(recall < 1.0 for recall in recalls), recalls
