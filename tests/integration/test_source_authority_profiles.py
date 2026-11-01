"""Integration gates for source_authority_v1."""

from __future__ import annotations

import importlib.util
import os

import pytest

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.report import _format_metric_value, _primary_metric_name
from cogkurabench.models import Capability
from cogkurabench.runner import BenchmarkRunner

COGKURA_AVAILABLE = importlib.util.find_spec("cogkura") is not None
_NEUTRAL_QUERIES = {
    "sa-q-a1",
    "sa-q-a2",
    "sa-q-a5",
    "sa-q-a6",
    "sa-q-a7",
    "sa-q-a8",
    "sa-q-a9-base",
    "sa-q-a9",
    "sa-q-a10",
    "sa-q-a11",
    "sa-q-a15",
    "sa-q-a16-bill",
    "sa-q-a16-other",
}
_RETRIEVAL_NEUTRAL_QUERIES = _NEUTRAL_QUERIES - {"sa-q-a16-bill"}


def _signature(query_result: object) -> tuple[object, ...]:
    items = query_result.retrieved_items  # type: ignore[attr-defined]
    return tuple((item.source_event_ids, item.score, item.rank) for item in items)


@pytest.mark.asyncio
async def test_oracle_source_authority_is_na() -> None:
    dataset = load_dataset("source_authority_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("oracle", dataset),
        write_results=False,
    )
    capability = result.capability_results[Capability.SOURCE_AUTHORITY.value]
    primary = _primary_metric_name(Capability.SOURCE_AUTHORITY)
    assert primary not in capability.metrics
    assert _format_metric_value(Capability.SOURCE_AUTHORITY, primary, None) == "N/A"


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize("backend_name", ("cogkura-authority-control", "cogkura-authority"))
async def test_source_authority_gate(backend_name: str) -> None:
    dataset = load_dataset("source_authority_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend(backend_name, dataset),
        write_results=False,
    )
    metrics = result.capability_results[Capability.SOURCE_AUTHORITY.value].metrics
    assert metrics["source_authority_admission_precision"] == 1.0
    assert metrics["source_authority_admission_recall"] == 1.0
    assert metrics["source_authority_promotion_basis_accuracy"] == 1.0
    assert metrics["source_authority_unauthorized_promotion_count"] == 0.0
    assert metrics["source_authority_scope_leakage_count"] == 0.0
    assert metrics["source_authority_idempotency_violations"] == 0.0
    assert metrics["source_authority_declared_mismatch_count"] == 0.0
    if backend_name == "cogkura-authority":
        assert metrics["source_authority_deferral_accuracy"] == 1.0
        assert metrics["source_authority_invalid_accuracy"] == 1.0
        assert metrics["source_authority_revision_binding_accuracy"] == 1.0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_no_authority_cases_match_across_profiles() -> None:
    dataset = load_dataset("source_authority_v1")
    runner = BenchmarkRunner()
    control = await runner.run(
        dataset,
        create_backend("cogkura-authority-control", dataset),
        write_results=False,
    )
    enabled = await runner.run(
        dataset,
        create_backend("cogkura-authority", dataset),
        write_results=False,
    )
    control_by_id = {item.query_id: item for item in control.query_results}
    for query_result in enabled.query_results:
        if query_result.query_id not in _NEUTRAL_QUERIES:
            continue
        if query_result.query_id in _RETRIEVAL_NEUTRAL_QUERIES:
            assert _signature(query_result) == _signature(control_by_id[query_result.query_id])
        assert [
            (item.predicate, item.object, item.support_count, item.promotion_basis)
            for item in query_result.source_authority_observations
        ] == [
            (item.predicate, item.object, item.support_count, item.promotion_basis)
            for item in control_by_id[query_result.query_id].source_authority_observations
        ]


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_authority_does_not_boost_equivalent_semantic_activation() -> None:
    from datetime import datetime

    from cogkurabench.backends.cogkura import CogKuraBackend
    from cogkurabench.models import (
        EventType,
        ProjectEvent,
        RetrievalRequest,
        SemanticFact,
        SourceAuthority,
    )

    timestamp = datetime.fromisoformat("2026-05-03T10:00:00+00:00")
    query_time = datetime.fromisoformat("2026-05-03T12:00:00+00:00")

    def build(authority: bool, threshold: int) -> tuple[CogKuraBackend, ProjectEvent]:
        fact = SemanticFact(
            subject="payments-api",
            predicate="migration_execution_strategy",
            object="deployment_pipeline",
            cardinality="one",
            authority=SourceAuthority(basis="application_asserted") if authority else None,
        )
        event = ProjectEvent(
            id="parity",
            timestamp=timestamp,
            sequence=1,
            subject_id="payments-api",
            event_type=EventType.ARCHITECTURE_DECISION,
            content="payments-api deployments use the pipeline for migrations.",
            semantic_facts=(fact,),
            session_id="parity",
            tenant_id="sa-parity",
        )
        backend = CogKuraBackend(
            minimum_supporting_episodes=threshold,
            allow_authoritative_single_episode=authority,
            inspect_source_authority=True,
            name="parity",
        )
        return backend, event

    async def measure(authority: bool, threshold: int) -> tuple[float, float, float | None]:
        backend, event = build(authority, threshold)
        await backend.reset()
        await backend.ingest((event,))
        await backend.prepare(as_of=query_time)
        response = await backend.retrieve(
            RetrievalRequest(
                query_id="parity",
                query="payments-api migration execution strategy",
                as_of=query_time,
                limit=5,
                tenant_id="sa-parity",
                subject_id="payments-api",
            )
        )
        observation = response.source_authority_observations[0]
        score = response.items[0].score if response.items else None
        assert observation.confidence is not None
        assert observation.importance is not None
        return observation.confidence, observation.importance, score

    authority_values = await measure(True, 2)
    ordinary_values = await measure(False, 1)
    for left, right in zip(authority_values, ordinary_values, strict=True):
        assert left is not None and right is not None
        assert abs(left - right) < 1e-9


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_missing_revision_does_not_grant_authority() -> None:
    from datetime import datetime

    from cogkurabench.backends.cogkura import CogKuraBackend
    from cogkurabench.models import EventType, ProjectEvent, SemanticFact, SourceAuthority

    event = ProjectEvent(
        id="missing-revision",
        timestamp=datetime.fromisoformat("2026-05-03T10:00:00+00:00"),
        sequence=1,
        subject_id="payments-api",
        event_type=EventType.ARCHITECTURE_DECISION,
        content="payments-api deployments use the pipeline for migrations.",
        semantic_facts=(
            SemanticFact(
                subject="payments-api",
                predicate="migration_execution_strategy",
                object="deployment_pipeline",
                cardinality="one",
                authority=SourceAuthority(basis="application_asserted"),
            ),
        ),
        tenant_id="sa-missing",
        session_id="sa-missing",
    )
    backend = CogKuraBackend(
        minimum_supporting_episodes=2,
        allow_authoritative_single_episode=True,
        inspect_source_authority=True,
        name="cogkura-authority",
    )
    await backend.reset()
    await backend.ingest((event,))
    await backend._require_memory().encode_episodes(
        tenant_id="sa-missing",
        as_of=event.timestamp,
    )
    stored = await backend._observation_store.get_by_source(
        tenant_id="sa-missing",
        source_namespace="cogkurabench.events",
        source_record_id=event.id,
    )
    assert stored is not None
    backend._observation_store.revisions[stored.id].clear()
    result = await backend._require_memory().consolidate_semantics(
        tenant_id="sa-missing",
        as_of=event.timestamp,
    )
    memories = await backend._require_memory().list_semantic_memories(tenant_id="sa-missing")
    assert result.authority_invalid == 1
    assert result.authority_promoted == 0
    assert memories == []


@pytest.mark.skipif(
    not os.environ.get("COGKURA_POSTGRES_MEMORY_URL"),
    reason="COGKURA_POSTGRES_MEMORY_URL is not set",
)
@pytest.mark.asyncio
async def test_postgres_authority_state_matches_memory() -> None:
    from datetime import datetime

    from cogkura import (
        ComplementaryLearningSemanticConsolidator,
        Memory,
        semantic_promotion_from_metadata,
    )
    from cogkura.observations.models import ObservationInput
    from cogkura.storage.postgres import (
        PostgresEpisodeStore,
        PostgresObservationStore,
        PostgresSemanticMemoryStore,
    )
    from sqlalchemy.ext.asyncio import create_async_engine

    observed_at = datetime.fromisoformat("2026-05-03T10:00:00+00:00")

    def observation() -> ObservationInput:
        return ObservationInput(
            tenant_id="sa-postgres",
            subject_id="payments-api",
            source_namespace="benchmark",
            source_record_id="sa-postgres",
            source_version="1",
            content="payments-api deployments use the pipeline for migrations.",
            observed_at=observed_at,
            metadata={
                "session_id": "sa-postgres",
                "semantic_facts": [
                    {
                        "subject_entity_id": "payments-api",
                        "predicate": "migration_execution_strategy",
                        "object_value": "deployment_pipeline",
                        "cardinality": "one",
                        "authority": {"basis": "application_asserted"},
                    }
                ],
            },
        )

    async def promote(memory: Memory) -> tuple[str, int, int]:
        await memory.observe(observation())
        await memory.process(tenant_id="sa-postgres", as_of=observed_at)
        memories = await memory.list_semantic_memories(
            tenant_id="sa-postgres",
            subject_id="payments-api",
        )
        assert len(memories) == 1
        promotion = semantic_promotion_from_metadata(memories[0].metadata)
        assert promotion is not None
        return promotion.basis.value, memories[0].support_count, promotion.support_count or 0

    engine = create_async_engine(os.environ["COGKURA_POSTGRES_MEMORY_URL"])
    try:
        in_memory = Memory(
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                allow_authoritative_single_episode=True,
                minimum_supporting_episodes=2,
            )
        )
        postgres = Memory(
            observation_store=PostgresObservationStore(engine),
            episode_store=PostgresEpisodeStore(engine),
            semantic_store=PostgresSemanticMemoryStore(engine),
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                allow_authoritative_single_episode=True,
                minimum_supporting_episodes=2,
            ),
        )
        assert await promote(in_memory) == await promote(postgres)
    finally:
        await engine.dispose()
