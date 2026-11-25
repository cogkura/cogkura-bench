"""Independent source-assessment gold and backend parity through public Core APIs."""

from __future__ import annotations

import importlib.metadata
import importlib.util
import os
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.evaluation.report import _format_metric_value
from cogkurabench.runner import BenchmarkRunner

AVAILABLE = importlib.util.find_spec("cogkura") is not None


def source_fixture_for_version(version: str) -> str:
    """Use the explicitly versioned transition contract for tested Core versions."""
    return (
        "source_aware_metamemory_v2"
        if version in {"0.20.1", "0.20.2", "0.20.3"}
        else "source_aware_metamemory_v1"
    )


def current_source_fixture() -> str:
    return source_fixture_for_version(importlib.metadata.version("cogkura"))


def test_source_fixture_selection_is_explicit() -> None:
    assert source_fixture_for_version("0.20.0") == "source_aware_metamemory_v1"
    assert source_fixture_for_version("0.20.1") == "source_aware_metamemory_v2"
    assert source_fixture_for_version("0.20.2") == "source_aware_metamemory_v2"
    assert source_fixture_for_version("0.20.3") == "source_aware_metamemory_v2"
    assert source_fixture_for_version("0.20.4") == "source_aware_metamemory_v1"


def test_fixture_valid_and_all_six_states_declared_or_fault_tested() -> None:
    assert validate_dataset("source_aware_metamemory_v1") == []
    dataset = load_dataset("source_aware_metamemory_v1")
    assert len(dataset.events) == 23
    assert len(dataset.queries) == 26
    assert {q.expected_source_assessment.checks["state"] for q in dataset.queries} == {
        "known",
        "unknown",
        "contested",
        "withdrawn",
        "historical_only",
        "indeterminate",
    }


@pytest.mark.asyncio
async def test_unsupported_backend_is_na() -> None:
    from cogkurabench.models import Capability

    dataset = load_dataset("source_aware_metamemory_v1")
    result = await BenchmarkRunner().run(
        dataset, create_backend("oracle", dataset), write_results=False
    )
    metrics = result.capability_results["source_assessment"].metrics
    assert "source_assessment_accuracy" not in metrics
    assert (
        _format_metric_value(Capability.SOURCE_ASSESSMENT, "source_assessment_accuracy", None)
        == "N/A"
    )


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
@pytest.mark.parametrize("name", ("cogkura-source-control", "cogkura-source"))
async def test_source_profile_gate(name: str) -> None:
    dataset = load_dataset(current_source_fixture())
    result = await BenchmarkRunner().run(
        dataset, create_backend(name, dataset), write_results=False
    )
    metrics = result.capability_results["source_assessment"].metrics
    for key, value in metrics.items():
        if key.startswith("source_") and key.endswith(("accuracy", "precision", "recall")):
            assert value == 1, (key, value)
    assert metrics["source_assessment_mismatch_count"] == 0
    assert metrics["source_false_certainty_count"] == 0
    assert metrics["source_future_leak_count"] == 0
    inaccessible = next(q for q in result.query_results if q.query_id == "sm-inaccessible")
    assert inaccessible.retrieved_items == ()
    assert inaccessible.source_assessment.state == "known"
    cutoff = next(q for q in result.query_results if q.query_id == "sm-knowledge-cutoff")
    assert cutoff.source_assessment.decisions_available is False
    assert cutoff.source_assessment.decisions == ()
    contested = next(q for q in result.query_results if q.query_id == "sm-contested")
    assert len(contested.retrieved_items) <= 1
    assert set(contested.source_assessment.event_ids) > set(contested.retrieved_event_ids)


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_0201_retains_v1_mismatch_and_reports_both_transitions() -> None:
    if importlib.metadata.version("cogkura") not in {"0.20.1", "0.20.2", "0.20.3"}:
        pytest.skip("complete transition history applies to the 0.20.1–0.20.3 candidates")
    for fixture, expected_mismatches in (
        ("source_aware_metamemory_v1", 1),
        ("source_aware_metamemory_v2", 0),
    ):
        data = load_dataset(fixture)
        result = await BenchmarkRunner().run(
            data, create_backend("cogkura-source", data), write_results=False
        )
        metrics = result.capability_results["source_assessment"].metrics
        assert metrics["source_assessment_check_count"] == 191
        assert metrics["source_assessment_mismatch_count"] == expected_mismatches
        withdrawn = next(q for q in result.query_results if q.query_id == "sm-withdrawn")
        assert list(withdrawn.source_assessment.transition_event_ids) == [
            "sm-chain-replace",
            "sm-chain-withdraw",
        ]


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_inspection_does_not_mutate_public_state_counters_or_recall() -> None:
    from cogkurabench.source_models import SourceAssessmentRequest

    data = load_dataset("source_aware_metamemory_v1")
    event = next(e for e in data.events if e.id == "sm-adopt")
    query = data.query_by_id()["sm-known"]
    backend = create_backend("cogkura-source", data)
    await backend.reset()
    await backend.ingest((event,))
    await backend.prepare(as_of=query.timestamp)
    memory = backend._require_memory()

    async def snapshot() -> tuple[object, ...]:
        return (
            await memory.list_episodes(tenant_id="known"),
            await memory.list_semantic_memories(tenant_id="known"),
            await memory.list_semantic_revisions(tenant_id="known"),
            await memory.recall(query.query, tenant_id="known", as_of=query.timestamp),
            dict(backend._last_consolidation_by_tenant),
        )

    before = await snapshot()
    for _ in range(2):
        await backend.inspect_sources(
            SourceAssessmentRequest(
                query=query.query,
                as_of=query.timestamp,
                valid_at=None,
                tenant_id="known",
                subject_id="service",
                spec=query.source_inspection,
            )
        )
    assert await snapshot() == before


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_missing_revision_is_not_a_missing_locator_or_unknown_fact() -> None:
    from cogkura import Memory, ObservationInput, SemanticSlotQuery
    from cogkura.algorithms.semantic import ComplementaryLearningSemanticConsolidator
    from cogkura.storage.in_memory_observation import InMemoryObservationStore

    class UnavailableRevisionStore(InMemoryObservationStore):
        unavailable = False

        async def get_revisions_many(self, **kwargs: object) -> dict[object, object]:
            if self.unavailable:
                return {}
            return await super().get_revisions_many(**kwargs)

    store = UnavailableRevisionStore()
    memory = Memory(
        observation_store=store,
        semantic_consolidator=ComplementaryLearningSemanticConsolidator(
            allow_authoritative_single_episode=True
        ),
    )
    clock = datetime(2026, 11, 1, tzinfo=UTC)
    await memory.observe(
        ObservationInput(
            tenant_id="fault",
            subject_id="service",
            source_namespace="fixture",
            source_record_id="one",
            observed_at=clock,
            content="The policy is startup.",
            metadata={
                "semantic_facts": [
                    {
                        "subject_entity_id": "service",
                        "predicate": "policy",
                        "object_value": "startup",
                        "cardinality": "one",
                        "authority": {"basis": "application_asserted"},
                    }
                ]
            },
        )
    )
    await memory.process(tenant_id="fault", as_of=clock)
    slot = SemanticSlotQuery("service", "policy")
    locator = await memory.inspect_semantic_slot(slot, tenant_id="fault", as_of=clock)
    assert locator.quality.revision_coverage_complete
    assert not locator.quality.locator_coverage_complete
    store.unavailable = True
    missing = await memory.inspect_semantic_slot(slot, tenant_id="fault", as_of=clock)
    assert missing.state.value == "known"
    assert not missing.quality.revision_coverage_complete
    assert "revision_unavailable" in {r.value for r in missing.reasons}


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_missing_optional_capability_and_legacy_snapshot_stay_indeterminate() -> None:
    from cogkura import Memory, SemanticSlotQuery, SemanticSlotRecords
    from cogkura.storage.in_memory_semantic import InMemorySemanticMemoryStore

    class LegacyStore:
        def __init__(self) -> None:
            self.delegate = InMemorySemanticMemoryStore()

        def __getattr__(self, name: str) -> object:
            if name == "inspect_slot":
                raise AttributeError(name)
            return getattr(self.delegate, name)

    unavailable = Memory(semantic_store=LegacyStore())
    slot = SemanticSlotQuery("service", "deployment_policy")
    clock = datetime(2026, 11, 1, 10, tzinfo=UTC)
    report = await unavailable.inspect_semantic_slot(slot, tenant_id="legacy", as_of=clock)
    assert report.state.value == "indeterminate"
    assert "inspection_capability_unavailable" in {r.value for r in report.reasons}

    data = load_dataset("source_aware_metamemory_v1")
    backend = create_backend("cogkura-source", data)
    await backend.reset()
    await backend.ingest((next(e for e in data.events if e.id == "sm-adopt"),))
    await backend.prepare(as_of=clock)
    memory = backend._require_memory()
    memories = await memory.list_semantic_memories(tenant_id="known")
    revisions = await memory.list_semantic_revisions(tenant_id="known")

    class EmptySnapshots:
        async def inspect_slot(self, **_kwargs: object) -> SemanticSlotRecords:
            return SemanticSlotRecords(
                memories=tuple(memories),
                revisions=tuple(replace(r, snapshot={}) for r in revisions),
            )

    legacy = Memory(semantic_inspection_store=EmptySnapshots())
    report = await legacy.inspect_semantic_slot(slot, tenant_id="known", as_of=clock)
    assert report.state.value == "indeterminate"
    assert "legacy_history_incomplete" in {r.value for r in report.reasons}
    assert all(r.projected_status is None for r in report.revisions)


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_context_currentness_compares_exact_retained_revision_with_store_view() -> None:
    from cogkura import Memory, ObservationInput

    memory = Memory()
    clock = datetime(2026, 11, 1, 10, tzinfo=UTC)
    original = ObservationInput(
        tenant_id="currency",
        subject_id="service",
        source_namespace="handbook",
        source_record_id="deployment",
        source_version="1",
        content="Service deployment policy uses startup.",
        observed_at=clock,
    )
    await memory.observe(original)
    await memory.process(tenant_id="currency", as_of=clock)
    context = await memory.prepare_context("service deployment", tenant_id="currency", as_of=clock)
    assert context.working_memory.items
    await memory.observe(
        replace(
            original,
            source_version="2",
            content="Service deployment policy now uses a pipeline.",
            observed_at=datetime(2026, 11, 2, 10, tzinfo=UTC),
        )
    )
    assessed = await memory.assess_source_memory(context)
    assert assessed.quality.revision_coverage_complete
    assert any(item.currentness.older_revision_count > 0 for item in assessed.items)
    assert all(
        source.is_latest_known_revision is False
        for item in assessed.provenance.items
        for source in item.sources
    )


@pytest.mark.skipif(not AVAILABLE, reason="cogkura extra not installed")
@pytest.mark.asyncio
async def test_pass_report_cap_and_replay_preserve_durable_state_and_counters() -> None:
    from cogkura import Memory, ObservationInput, SemanticDiagnosticsConfig
    from cogkura.algorithms.semantic import ComplementaryLearningSemanticConsolidator

    from cogkurabench.backends.cogkura import _semantic_facts_to_metadata

    data = load_dataset("source_aware_metamemory_v1")
    inputs = [e for e in data.events if e.id in ("sm-adopt", "sm-no-locator", "sm-negative")]
    runs = []
    for enabled in (False, True):
        memory = Memory(
            semantic_diagnostics_config=SemanticDiagnosticsConfig(enabled=enabled, max_items=1),
            semantic_consolidator=ComplementaryLearningSemanticConsolidator(
                minimum_supporting_episodes=2, allow_authoritative_single_episode=True
            ),
        )
        for event in inputs:
            await memory.observe(
                ObservationInput(
                    tenant_id="report-cap",
                    subject_id=event.subject_id,
                    source_namespace="fixture",
                    source_record_id=event.id,
                    content=event.content,
                    observed_at=event.timestamp,
                    metadata={
                        "session_id": event.id,
                        "semantic_facts": [
                            {**f, "qualifiers": {"case": event.id}}
                            for f in _semantic_facts_to_metadata(event.semantic_facts)
                        ],
                    },
                )
            )
        result = await memory.process(tenant_id="report-cap", as_of=inputs[0].timestamp)
        state = await memory.list_semantic_memories(tenant_id="report-cap")
        runs.append(
            (
                result.semantics.created,
                result.semantics.authority_promoted,
                sorted((m.object_value, m.support_count) for m in state),
            )
        )
        if enabled:
            report = result.semantics.decisions
            assert report.total_decisions == 3
            assert report.is_truncated
            assert len(report.items) == 1
        else:
            assert result.semantics.decisions is None
        replay = await memory.consolidate_semantics(
            tenant_id="report-cap", as_of=inputs[0].timestamp
        )
        assert replay.created == 0
        assert await memory.list_semantic_memories(tenant_id="report-cap") == state
    assert runs[0] == runs[1]


@pytest.mark.skipif(
    not os.environ.get("COGKURA_POSTGRES_MEMORY_URL"),
    reason="COGKURA_POSTGRES_MEMORY_URL is not set; parity NOT EXECUTED",
)
@pytest.mark.asyncio
async def test_postgres_source_fixture_and_correction_replay_match_memory() -> None:
    from cogkura import Memory
    from cogkura.storage.postgres import (
        PostgresEpisodeStore,
        PostgresObservationStore,
        PostgresSemanticMemoryStore,
    )
    from sqlalchemy.ext.asyncio import create_async_engine

    url = os.environ["COGKURA_POSTGRES_MEMORY_URL"]
    data = load_dataset(current_source_fixture())
    engine = create_async_engine(url)
    cleaner = Memory(
        observation_store=PostgresObservationStore(engine),
        episode_store=PostgresEpisodeStore(engine),
        semantic_store=PostgresSemanticMemoryStore(engine),
    )
    backend = CogKuraBackend(
        minimum_supporting_episodes=2,
        allow_authoritative_single_episode=True,
        corrections_enabled=True,
        source_assessment=True,
        semantic_diagnostics=True,
        postgres_url=url,
    )
    try:
        for tenant in {e.tenant_id for e in data.events}:
            await cleaner.clear(tenant_id=tenant)
        expected = await BenchmarkRunner().run(
            data, create_backend("cogkura-source", data), write_results=False
        )
        actual = await BenchmarkRunner().run(data, backend, write_results=False)
        assert (
            actual.capability_results["source_assessment"].metrics[
                "source_assessment_mismatch_count"
            ]
            == 0
        )
        for left, right in zip(expected.query_results, actual.query_results, strict=True):
            assert left.query_id == right.query_id
            # Core's slot-only canonical order must preserve exact capped source
            # identities even with independently allocated physical storage IDs.
            left_source, right_source = left.source_assessment, right.source_assessment
            assert replace(left_source, revisions=(), decisions=()) == replace(
                right_source, revisions=(), decisions=()
            )
            assert set(left_source.revisions) == set(right_source.revisions)
            assert set(left_source.decisions) == set(right_source.decisions)
        await backend.reset()
        for tenant in {e.tenant_id for e in data.events}:
            assert await backend._require_memory().list_semantic_memories(tenant_id=tenant) == []
    finally:
        await backend.close()
        await engine.dispose()
