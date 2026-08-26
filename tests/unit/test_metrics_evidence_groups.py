"""Evidence-group metric unit tests."""

from datetime import UTC, datetime

import pytest

from cogkurabench.evaluation.evaluator import evaluate_query
from cogkurabench.metrics.evidence_groups import (
    classify_stage,
    compute_evidence_group_diagnostics,
    evidence_group_coverage,
    forbidden_group_intrusion,
    redundant_expected_group_items,
    unclassified_context_items,
)
from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    EvidenceGroup,
    EvidenceGroupStage,
    RetrievedItem,
)


def _item(rank: int, *event_ids: str) -> RetrievedItem:
    return RetrievedItem(
        source_event_ids=event_ids,
        text=f"memory-{rank}",
        score=1.0,
        rank=rank,
    )


Hiking = EvidenceGroup(
    id="hiking_interest",
    label="Established hiking interest",
    event_ids=("hiking-interest-001", "hiking-purchase-001"),
)
Size = EvidenceGroup(
    id="current_jacket_size",
    label="Current jacket size",
    event_ids=("size-current-m-001",),
)
Lightweight = EvidenceGroup(
    id="lightweight_preference",
    label="Prefers lightweight outerwear",
    event_ids=("lightweight-purchase-001", "lightweight-positive-001"),
)
StaleSize = EvidenceGroup(
    id="stale_jacket_size",
    label="Historical jacket size",
    event_ids=("size-old-l-001",),
)
Ski = EvidenceGroup(
    id="old_skiing_interest",
    label="Old skiing interest",
    event_ids=("ski-browse-001", "ski-browse-002"),
)


def test_group_coverage_union_hit() -> None:
    items = (_item(1, "noise-001"), _item(2, "lightweight-purchase-001"))
    assert evidence_group_coverage((Lightweight,), items) == 1.0


def test_two_events_same_group_count_once() -> None:
    items = (
        _item(1, "lightweight-purchase-001"),
        _item(2, "lightweight-positive-001"),
    )
    assert evidence_group_coverage((Lightweight,), items) == 1.0


def test_one_item_covers_multiple_groups() -> None:
    items = (_item(1, "hiking-interest-001", "size-current-m-001"),)
    groups = (Hiking, Size)
    assert evidence_group_coverage(groups, items) == 1.0


def test_forbidden_group_intrusion() -> None:
    items = (_item(1, "ski-browse-001"), _item(2, "ski-browse-002"))
    assert forbidden_group_intrusion((Ski,), items) == 1.0


def test_redundant_expected_group_items() -> None:
    items = (
        _item(1, "hiking-interest-001"),
        _item(2, "hiking-purchase-001"),
        _item(3, "size-current-m-001"),
        _item(4, "hiking-interest-001"),
    )
    assert redundant_expected_group_items(items, (Hiking, Size)) == 2


def test_unclassified_context_items() -> None:
    items = (
        _item(1, "hiking-interest-001"),
        _item(2, "noise-backpack-001"),
    )
    assert (
        unclassified_context_items(
            items,
            expected_groups=(Hiking,),
            forbidden_groups=(Ski,),
        )
        == 1
    )


def test_stage_without_context_does_not_emit_selection_drop() -> None:
    diagnostics, _, _, metrics = compute_evidence_group_diagnostics(
        BenchmarkQuery(
            id="q",
            timestamp=datetime(2026, 6, 1, tzinfo=UTC),
            capability=Capability.WORKING_MEMORY,
            query="jacket",
            expected_evidence_groups=(Hiking,),
        ),
        (_item(1, "hiking-interest-001"),),
        (),
        has_context=False,
    )
    assert diagnostics[0].retrieval_present is True
    assert diagnostics[0].stage == ""
    assert metrics["evidence_group_coverage_at_retrieval"] == 1.0
    assert "evidence_group_coverage_at_budget" not in metrics


@pytest.mark.parametrize(
    ("retrieval", "context", "expected"),
    [
        (True, True, EvidenceGroupStage.SELECTED.value),
        (True, False, EvidenceGroupStage.SELECTION_DROP.value),
        (False, False, EvidenceGroupStage.RETRIEVAL_MISS.value),
        (False, True, EvidenceGroupStage.CONTEXT_ONLY.value),
    ],
)
def test_stage_classification(retrieval: bool, context: bool, expected: str) -> None:
    assert classify_stage(retrieval_present=retrieval, context_present=context) == expected


def test_current_size_not_satisfied_by_stale_l() -> None:
    retrieval = (_item(1, "size-old-l-001"),)
    context = (_item(1, "size-old-l-001"),)
    diagnostics, _, _, _ = compute_evidence_group_diagnostics(
        BenchmarkQuery(
            id="q",
            timestamp=datetime(2026, 6, 1, tzinfo=UTC),
            capability=Capability.WORKING_MEMORY,
            query="jacket",
            expected_evidence_groups=(Size,),
            forbidden_evidence_groups=(StaleSize,),
        ),
        retrieval,
        context,
        has_context=True,
    )
    assert diagnostics[0].retrieval_present is False
    assert diagnostics[0].context_present is False
    assert diagnostics[0].stage == EvidenceGroupStage.RETRIEVAL_MISS.value


def test_evaluate_query_attaches_group_diagnostics() -> None:
    query = BenchmarkQuery(
        id="wm-001",
        timestamp=datetime(2026, 6, 1, tzinfo=UTC),
        capability=Capability.WORKING_MEMORY,
        query="waterproof jacket",
        expected_evidence_groups=(Hiking, Size),
        forbidden_evidence_groups=(Ski,),
        prompt_budget_tokens=750,
    )
    retrieved = (
        _item(1, "hiking-interest-001"),
        _item(2, "size-current-m-001"),
        _item(3, "lightweight-purchase-001"),
    )
    context = (_item(1, "hiking-interest-001"),)
    from cogkurabench.models import ContextResponse

    result = evaluate_query(
        query,
        retrieved,
        latency_ms=1.0,
        context_response=ContextResponse(items=context, estimated_tokens=100, latency_ms=1.0),
        context_items=context,
    )
    assert len(result.evidence_group_diagnostics) == 2
    hiking_diag = next(
        d for d in result.evidence_group_diagnostics if d.group_id == "hiking_interest"
    )
    assert hiking_diag.stage == EvidenceGroupStage.SELECTED.value
    size_diag = next(
        d for d in result.evidence_group_diagnostics if d.group_id == "current_jacket_size"
    )
    assert size_diag.stage == EvidenceGroupStage.SELECTION_DROP.value
    assert result.metrics["evidence_group_coverage_at_retrieval"] == 1.0
    assert result.metrics["evidence_group_coverage_at_budget"] == 0.5
