"""CogKura integration tests for customer decision context diagnostics."""

import importlib.util

import pytest

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.models import EvidenceGroupStage
from cogkurabench.runner import BenchmarkRunner

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cogkura") is None,
    reason="cogkura not installed",
)


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
