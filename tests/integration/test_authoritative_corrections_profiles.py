"""Integration gates for authoritative_corrections_v1."""

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
_ZERO_COUNTS = (
    "authoritative_correction_unauthorized_transition_count",
    "authoritative_correction_incorrect_current_count",
    "authoritative_correction_incorrect_historical_count",
    "authoritative_correction_knowledge_time_leak_count",
    "authoritative_correction_stale_context_leak_count",
    "authoritative_correction_false_suppression_count",
    "authoritative_correction_idempotency_violations",
    "authoritative_correction_undeclared_mismatch_count",
)


@pytest.mark.asyncio
async def test_oracle_corrections_are_na() -> None:
    dataset = load_dataset("authoritative_corrections_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("oracle", dataset),
        write_results=False,
    )
    capability = result.capability_results[Capability.AUTHORITATIVE_CORRECTION.value]
    primary = _primary_metric_name(Capability.AUTHORITATIVE_CORRECTION)
    assert primary not in capability.metrics
    assert _format_metric_value(Capability.AUTHORITATIVE_CORRECTION, primary, None) == "N/A"


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize("backend_name", ("cogkura-correction-control", "cogkura-correction"))
async def test_correction_profile_gate(backend_name: str) -> None:
    dataset = load_dataset("authoritative_corrections_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend(backend_name, dataset),
        write_results=False,
    )
    metrics = result.capability_results[Capability.AUTHORITATIVE_CORRECTION.value].metrics
    assert metrics["authoritative_correction_transition_precision"] == 1.0
    assert metrics["authoritative_correction_transition_recall"] == 1.0
    assert metrics["authoritative_correction_state_accuracy"] == 1.0
    for key in _ZERO_COUNTS:
        assert metrics[key] == 0.0
    if backend_name == "cogkura-correction":
        assert metrics["authoritative_correction_temporal_boundary_accuracy"] == 1.0
        assert metrics["authoritative_correction_conflict_deferral_accuracy"] == 1.0
        assert metrics["authoritative_correction_revision_provenance_accuracy"] == 1.0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_source_authority_gate_still_holds() -> None:
    dataset = load_dataset("source_authority_v1")
    result = await BenchmarkRunner().run(
        dataset,
        create_backend("cogkura-authority", dataset),
        write_results=False,
    )
    metrics = result.capability_results[Capability.SOURCE_AUTHORITY.value].metrics
    assert metrics["source_authority_admission_precision"] == 1.0
    assert metrics["source_authority_admission_recall"] == 1.0
    assert metrics["source_authority_promotion_basis_accuracy"] == 1.0
    assert metrics["source_authority_unauthorized_promotion_count"] == 0.0
    assert metrics["source_authority_declared_mismatch_count"] == 0.0


@pytest.mark.skipif(not COGKURA_AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_missing_revision_blocks_correction() -> None:
    from datetime import datetime

    from cogkurabench.backends.cogkura import CogKuraBackend
    from cogkurabench.models import (
        EventType,
        ProjectEvent,
        SemanticCorrection,
        SemanticFact,
        SourceAuthority,
    )

    adopt = ProjectEvent(
        id="corr-adopt",
        timestamp=datetime.fromisoformat("2026-10-01T10:00:00+00:00"),
        sequence=1,
        subject_id="payments-api",
        event_type=EventType.ARCHITECTURE_DECISION,
        content="payments-api migrations start with the application.",
        semantic_facts=(
            SemanticFact(
                subject="payments-api",
                predicate="migration_execution_strategy",
                object="application_startup",
                cardinality="one",
                authority=SourceAuthority(basis="application_asserted"),
            ),
        ),
        tenant_id="ac-missing",
        session_id="ac-missing-a",
    )
    backend = CogKuraBackend(
        minimum_supporting_episodes=2,
        allow_authoritative_single_episode=True,
        corrections_enabled=True,
        name="cogkura-correction",
    )
    await backend.reset()
    await backend.ingest((adopt,))
    await backend.prepare(as_of=datetime.fromisoformat("2026-10-01T12:00:00+00:00"))
    stored = await backend._observation_store.get_by_source(
        tenant_id="ac-missing",
        source_namespace="cogkurabench.events",
        source_record_id=adopt.id,
    )
    assert stored is not None
    backend._observation_store.revisions[stored.id].clear()
    edit = ProjectEvent(
        id="corr-edit",
        timestamp=datetime.fromisoformat("2026-10-20T10:00:00+00:00"),
        sequence=1,
        subject_id="payments-api",
        event_type=EventType.ARCHITECTURE_DECISION,
        content="payments-api migrations now run through the deployment pipeline.",
        semantic_facts=(
            SemanticFact(
                subject="payments-api",
                predicate="migration_execution_strategy",
                object="deployment_pipeline",
                cardinality="one",
                authority=SourceAuthority(basis="application_asserted"),
                correction=SemanticCorrection(
                    effective_at=datetime.fromisoformat("2026-10-20T10:00:00+00:00"),
                    replaces_subject="payments-api",
                    replaces_predicate="migration_execution_strategy",
                    replaces_object="application_startup",
                ),
            ),
        ),
        tenant_id="ac-missing",
        session_id="ac-missing-b",
    )
    await backend.ingest((edit,))
    result = await backend._require_memory().consolidate_semantics(
        tenant_id="ac-missing",
        as_of=edit.timestamp,
    )
    memories = await backend._require_memory().list_semantic_memories(
        tenant_id="ac-missing",
        valid_at=edit.timestamp,
    )
    assert result.authoritative_corrections_applied == 0
    assert [item.object_value for item in memories] == ["application_startup"]


@pytest.mark.skipif(
    not os.environ.get("COGKURA_POSTGRES_MEMORY_URL"),
    reason="COGKURA_POSTGRES_MEMORY_URL is not set",
)
@pytest.mark.asyncio
async def test_postgres_correction_matches_memory() -> None:
    from datetime import datetime

    from cogkura import (
        ComplementaryLearningSemanticConsolidator,
        Memory,
        SemanticCorrectionConfig,
    )
    from cogkura.observations.models import ObservationInput
    from cogkura.storage.postgres import (
        PostgresEpisodeStore,
        PostgresObservationStore,
        PostgresSemanticMemoryStore,
    )
    from sqlalchemy.ext.asyncio import create_async_engine

    observed = datetime.fromisoformat("2026-10-01T10:00:00+00:00")
    corrected = datetime.fromisoformat("2026-10-20T10:00:00+00:00")

    async def run(memory: Memory) -> tuple[str, ...]:
        await memory.observe(
            ObservationInput(
                tenant_id="ac-postgres",
                subject_id="payments-api",
                source_namespace="benchmark",
                source_record_id="adopt",
                content="payments-api migrations start with the application.",
                observed_at=observed,
                metadata={
                    "session_id": "adopt",
                    "semantic_facts": [
                        {
                            "subject_entity_id": "payments-api",
                            "predicate": "migration_execution_strategy",
                            "object_value": "application_startup",
                            "cardinality": "one",
                            "authority": {"basis": "application_asserted"},
                        }
                    ],
                },
            )
        )
        await memory.process(tenant_id="ac-postgres", as_of=observed)
        current = await memory.list_semantic_memories(
            tenant_id="ac-postgres",
            subject_id="payments-api",
        )
        predecessor = current[0].revision_key
        await memory.observe(
            ObservationInput(
                tenant_id="ac-postgres",
                subject_id="payments-api",
                source_namespace="benchmark",
                source_record_id="edit",
                content="payments-api migrations now run through the deployment pipeline.",
                observed_at=corrected,
                metadata={
                    "session_id": "edit",
                    "semantic_facts": [
                        {
                            "subject_entity_id": "payments-api",
                            "predicate": "migration_execution_strategy",
                            "object_value": "deployment_pipeline",
                            "cardinality": "one",
                            "authority": {"basis": "application_asserted"},
                            "correction": {
                                "replaces_revision_key": predecessor,
                                "effective_at": corrected.isoformat(),
                            },
                        }
                    ],
                },
            )
        )
        await memory.process(tenant_id="ac-postgres", as_of=corrected)
        historical = await memory.list_semantic_memories(
            tenant_id="ac-postgres",
            subject_id="payments-api",
            valid_at=observed,
        )
        latest = await memory.list_semantic_memories(
            tenant_id="ac-postgres",
            subject_id="payments-api",
            valid_at=corrected,
        )
        return (
            historical[0].object_value,
            historical[0].status.value,
            latest[0].object_value,
            latest[0].status.value,
        )

    engine = create_async_engine(os.environ["COGKURA_POSTGRES_MEMORY_URL"])
    try:
        kwargs = {
            "semantic_consolidator": ComplementaryLearningSemanticConsolidator(
                minimum_supporting_episodes=2,
                allow_authoritative_single_episode=True,
            ),
            "semantic_correction_config": SemanticCorrectionConfig(enabled=True),
        }
        in_memory = Memory(**kwargs)
        postgres = Memory(
            observation_store=PostgresObservationStore(engine),
            episode_store=PostgresEpisodeStore(engine),
            semantic_store=PostgresSemanticMemoryStore(engine),
            **kwargs,
        )
        assert await run(in_memory) == await run(postgres)
    finally:
        await engine.dispose()
