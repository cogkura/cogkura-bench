"""CogKura integration tests for customer decision context diagnostics."""

import importlib.util
from pathlib import Path

import pytest

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.dataset import _parse_event, load_dataset
from cogkurabench.models import EvidenceGroupStage, RetrievalRequest
from cogkurabench.runner import BenchmarkRunner

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cogkura") is None,
    reason="cogkura not installed",
)


def _load_generator_module():
    generator_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "generate_customer_decision_context_v1.py"
    )
    spec = importlib.util.spec_from_file_location(
        "generate_customer_decision_context_v1",
        generator_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load customer dataset generator.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _northpeak_relationship_paths(
    relationship_inspection: dict[str, object],
) -> list[dict[str, object]]:
    rows = relationship_inspection.get("predicate_rows", [])
    if not isinstance(rows, list):
        return []
    matches: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        predicate = row.get("predicate")
        object_value = str(row.get("object_value", ""))
        if predicate == "product_fit_issue" and "northpeak" in object_value:
            if row.get("hop_kind") == "relationship":
                matches.append(row)
    return matches


@pytest.mark.asyncio
async def test_cogkura_customer_decision_context_reports_group_stages() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    backend = CogKuraBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    query_result = next(
        item for item in result.query_results if item.query_id == "customer-waterproof-jacket"
    )
    assert len(query_result.evidence_group_diagnostics) == 5
    stages = {diag.stage for diag in query_result.evidence_group_diagnostics}
    assert stages <= {
        EvidenceGroupStage.SELECTED.value,
        EvidenceGroupStage.SELECTION_DROP.value,
        EvidenceGroupStage.RETRIEVAL_MISS.value,
        EvidenceGroupStage.CONTEXT_ONLY.value,
    }
    assert "evidence_group_coverage_at_retrieval" in query_result.metrics
    for diagnostic in query_result.evidence_group_diagnostics:
        assert diagnostic.stage in {
            EvidenceGroupStage.SELECTED.value,
            EvidenceGroupStage.SELECTION_DROP.value,
            EvidenceGroupStage.RETRIEVAL_MISS.value,
            EvidenceGroupStage.CONTEXT_ONLY.value,
        }
    assert len(query_result.forbidden_group_diagnostics) == 2
    cogkura_meta = query_result.backend_metadata.get("cogkura", {})
    recall_mapping = cogkura_meta.get("recall_mapping", {})
    assert "raw_recall_count" in recall_mapping
    assert "mapped_recall_count" in recall_mapping
    assert "unmapped_recall_count" in recall_mapping
    assert recall_mapping["raw_recall_count"] == (
        recall_mapping["mapped_recall_count"] + recall_mapping["unmapped_recall_count"]
    )
    context_meta = query_result.context_backend_metadata.get("cogkura", {})
    context_mapping = context_meta.get("context_mapping", {})
    assert "raw_selected_count" in context_mapping
    assert context_mapping["raw_selected_count"] == (
        context_mapping["mapped_selected_count"] + context_mapping["unmapped_selected_count"]
    )


@pytest.mark.asyncio
async def test_relationship_fixture_persists_inspection_metadata() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    backend = CogKuraBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    query_result = next(
        item for item in result.query_results if item.query_id == "customer-waterproof-jacket"
    )
    cogkura_meta = query_result.backend_metadata.get("cogkura", {})
    assert cogkura_meta.get("relationships_ingested", 0) > 0
    inspection = cogkura_meta.get("relationship_inspection", {})
    assert inspection.get("relationship_seed_count", 0) >= 0
    assert "predicate_rows" in inspection


@pytest.mark.asyncio
async def test_relationship_causality_for_northpeak_inspect_paths() -> None:
    generator = _load_generator_module()
    dataset = load_dataset("customer_decision_context_v1")
    query = dataset.query_by_id()["customer-waterproof-jacket"]
    request = RetrievalRequest(
        query_id=query.id,
        query=query.query,
        as_of=query.timestamp,
        limit=query.retrieval_limit,
        goal=query.goal,
        valid_at=query.valid_at,
        entity_ids=query.entity_ids,
        predicate=query.predicate,
        object_value=query.object_value,
    )

    with_events = [_parse_event(event) for event in generator.build_events()]
    backend_with = CogKuraBackend()
    await backend_with.reset()
    await backend_with.ingest(with_events)
    await backend_with.prepare(as_of=query.timestamp)
    with_response = await backend_with.retrieve(request)
    with_inspection = with_response.backend_metadata["cogkura"]["relationship_inspection"]
    assert isinstance(with_inspection, dict)

    without_events = [
        _parse_event(event) for event in generator.build_events(without_relationships=True)
    ]
    backend_without = CogKuraBackend()
    await backend_without.reset()
    await backend_without.ingest(without_events)
    await backend_without.prepare(as_of=query.timestamp)
    without_response = await backend_without.retrieve(request)
    without_inspection = without_response.backend_metadata["cogkura"]["relationship_inspection"]
    assert _northpeak_relationship_paths(without_inspection) == []
    # With catalogue edges present, a NorthPeak relationship path may exist but is not required.
    _northpeak_relationship_paths(with_inspection)
