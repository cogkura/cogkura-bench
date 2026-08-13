"""Atlas dataset integration tests."""

import pytest

from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.runner import BenchmarkRunner


def test_software_project_v1_validates() -> None:
    assert validate_dataset("software_project_v1") == []


@pytest.mark.asyncio
async def test_learning_delta_zero_with_identical_wording() -> None:
    dataset = load_dataset("software_project_v1")
    backend = TokenOverlapBackend()
    result = await BenchmarkRunner().run(dataset, backend, write_results=False)
    post = next(qr for qr in result.query_results if qr.query_id == "atlas-learn-post-001")
    assert post.metrics.get("delta_recall@5", 0.0) == 0.0


@pytest.mark.asyncio
async def test_learn_pre_post_share_query_text() -> None:
    dataset = load_dataset("software_project_v1")
    queries = dataset.query_by_id()
    pre = queries["atlas-learn-pre-001"]
    post = queries["atlas-learn-post-001"]
    assert pre.query == post.query
