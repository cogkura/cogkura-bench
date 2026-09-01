"""Customer decision context dataset integration tests."""

from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import Capability

EXPECTED_GROUP_IDS = (
    "current_jacket_size",
    "hiking_interest",
    "colour_preference",
    "lightweight_preference",
    "northpeak_fit_issue",
)
FORBIDDEN_GROUP_IDS = ("stale_jacket_size", "old_skiing_interest")

PRIMARY_QUERY_TEXT = (
    "I'm looking for a waterproof jacket for a hiking trip next month. What would you recommend?"
)
PRIMARY_GOAL = "Help the customer choose an appropriate waterproof hiking jacket."


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


def _events_by_id() -> dict[str, object]:
    return load_dataset("customer_decision_context_v1").event_by_id()


def _primary_query():
    return load_dataset("customer_decision_context_v1").query_by_id()["customer-waterproof-jacket"]


def _has_lightweight_semantic(event) -> bool:
    return any(
        fact.predicate == "outerwear_weight_preference" and fact.object == "lightweight"
        for fact in event.semantic_facts
    )


def test_customer_decision_context_validates() -> None:
    assert validate_dataset("customer_decision_context_v1") == []


def test_customer_decision_context_manifest() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    assert dataset.manifest.name == "customer-decision-context-v1"
    assert dataset.manifest.events == 149
    assert dataset.manifest.queries == 1
    assert dataset.manifest.feedback == 0
    assert Capability.WORKING_MEMORY in dataset.manifest.required_capabilities


def test_customer_decision_context_query_has_evidence_groups() -> None:
    query = _primary_query()
    assert query.capability == Capability.WORKING_MEMORY
    assert query.retrieval_limit == 50
    assert query.prompt_budget_tokens == 750
    assert len(query.expected_evidence_groups) == 5
    assert len(query.forbidden_evidence_groups) == 2
    assert "core" in query.tags


def test_customer_decision_context_query_stability() -> None:
    query = _primary_query()
    assert query.query == PRIMARY_QUERY_TEXT
    assert query.goal == PRIMARY_GOAL
    assert tuple(group.id for group in query.expected_evidence_groups) == EXPECTED_GROUP_IDS
    assert tuple(group.id for group in query.forbidden_evidence_groups) == FORBIDDEN_GROUP_IDS


def test_current_size_m_after_historical_l() -> None:
    events = _events_by_id()
    size_l = events["size-old-l-001"]
    size_m = events["size-current-m-001"]
    query = _primary_query()
    assert size_l.timestamp < size_m.timestamp < query.timestamp


def test_hiking_and_skiing_cardinality_many() -> None:
    events = _events_by_id()
    hiking = events["hiking-interest-001"].semantic_facts[0]
    skiing = events["ski-interest-001"].semantic_facts[0]
    assert hiking.cardinality == "many"
    assert skiing.cardinality == "many"


def test_size_cardinality_one() -> None:
    events = _events_by_id()
    for event_id in ("size-old-l-001", "size-current-m-001"):
        assert events[event_id].semantic_facts[0].cardinality == "one"


def test_lightweight_purchase_has_structured_semantic_fact() -> None:
    purchase = _events_by_id()["lightweight-purchase-001"]
    assert len(purchase.semantic_facts) == 1
    fact = purchase.semantic_facts[0]
    assert fact.predicate == "outerwear_weight_preference"
    assert fact.object == "lightweight"
    assert fact.cardinality == "one"
    assert fact.subject == "customer-alex"


def test_lightweight_browse_events_have_no_structured_preference() -> None:
    events = _events_by_id()
    for event_id in ("lightweight-browse-001", "lightweight-browse-002"):
        assert not _has_lightweight_semantic(events[event_id])


def test_lightweight_positive_remains_episodic_only() -> None:
    positive = _events_by_id()["lightweight-positive-001"]
    assert positive.semantic_facts == ()


def test_semantic_gold_parity_for_explicit_concepts() -> None:
    events = _events_by_id()

    size_m = events["size-current-m-001"].semantic_facts[0]
    assert size_m.predicate == "jacket_size"
    assert size_m.object == "M"

    hiking = events["hiking-interest-001"].semantic_facts[0]
    assert hiking.predicate == "activity_interest"
    assert hiking.object == "hiking"

    colour = events["colour-preference-001"].semantic_facts[0]
    assert colour.predicate == "colour_preference"
    assert colour.object == "neutral"

    lightweight = events["lightweight-purchase-001"].semantic_facts[0]
    assert lightweight.predicate == "outerwear_weight_preference"
    assert lightweight.object == "lightweight"

    fit = events["northpeak-return-001"].semantic_facts[0]
    assert fit.predicate == "product_fit_issue"
    assert "northpeak" in fit.object
    assert "sleeves_too_short" in fit.object


def test_explicit_sessions_preserved() -> None:
    events = _events_by_id()
    assert events["ski-browse-001"].session_id == "ski-session-001"
    assert events["ski-browse-002"].session_id == "ski-session-001"
    assert events["hiking-browse-001"].session_id == "hiking-session-001"
    assert events["hiking-browse-002"].session_id == "hiking-session-001"
    assert events["hiking-browse-003"].session_id == "hiking-session-002"
    assert events["hiking-browse-004"].session_id == "hiking-session-002"
    assert events["lightweight-browse-001"].session_id == "lightweight-session-001"
    assert events["lightweight-browse-002"].session_id == "lightweight-session-001"
    assert events["hiking-browse-005"].session_id == "scotland-waterproof-session-001"
    assert events["hiking-browse-006"].session_id == "scotland-waterproof-session-001"
    assert events["hiking-browse-007"].session_id == "hiking-session-003"
    assert events["hiking-browse-008"].session_id == "hiking-session-003"


def test_ungrouped_events_use_event_specific_sessions() -> None:
    events = _events_by_id()
    assert events["ski-interest-001"].session_id == "session-ski-interest-001"
    assert events["hiking-purchase-001"].session_id == "session-hiking-purchase-001"
    assert events["size-current-m-001"].session_id == "session-size-current-m-001"
    assert events["northpeak-return-001"].session_id == "session-northpeak-return-001"


def test_same_month_ungrouped_events_do_not_share_sessions() -> None:
    events = _events_by_id()
    assert events["size-old-l-001"].session_id != events["noise-004"].session_id
    assert events["size-old-l-001"].session_id == "session-size-old-l-001"
    assert events["noise-004"].session_id == "session-noise-004"


def test_noise_events_have_unique_sessions() -> None:
    events = _events_by_id()
    noise_events = [event for event in events.values() if event.id.startswith("noise-")]
    noise_sessions = [event.session_id for event in noise_events]
    assert len(noise_events) > 0
    assert len(set(noise_sessions)) == len(noise_sessions)
    for event in noise_events:
        assert event.session_id == f"session-{event.id}"


def test_no_month_wide_noise_session() -> None:
    events = _events_by_id()
    noise_events = [event for event in events.values() if event.id.startswith("noise-")]
    session_sizes = Counter(event.session_id for event in noise_events)
    assert max(session_sizes.values()) == 1


def test_generator_determinism() -> None:
    generator = _load_generator_module()
    first = generator.build_events()
    second = generator.build_events()
    assert first == second


def test_catalogue_has_four_is_a_edges() -> None:
    generator = _load_generator_module()
    catalogue = generator.build_catalogue()
    relationships = catalogue["relationships"]
    assert len(relationships) == 4
    assert all(relationship["relation_type"] == "is_a" for relationship in relationships)
    assert all(relationship["provenance"] == "catalog" for relationship in relationships)
    assert set(catalogue["entities"]) == {
        "northpeak-alpine-shell",
        "featherlite-packable-shell",
        "waterproof-shell",
        "jacket",
        "outerwear",
    }


def test_catalogue_edges_are_source_knowledge_not_gold() -> None:
    generator = _load_generator_module()
    catalogue = generator.build_catalogue()
    query_terms = {"hiking", "lightweight", "waterproof", "customer-waterproof-jacket"}
    for relationship in catalogue["relationships"]:
        for entity_id in (
            relationship["source_entity_id"],
            relationship["target_entity_id"],
        ):
            assert entity_id not in query_terms
            assert not entity_id.startswith("northpeak_fit")


def test_product_events_carry_catalogue_relationships() -> None:
    events = _events_by_id()
    northpeak_return = events["northpeak-return-001"]
    assert "waterproof-shell" in northpeak_return.entities
    assert "jacket" in northpeak_return.entities
    assert len(northpeak_return.relationships) == 3
    featherlite_purchase = events["lightweight-purchase-001"]
    assert "jacket" in featherlite_purchase.entities
    assert "outerwear" in featherlite_purchase.entities
    assert len(featherlite_purchase.relationships) == 1


def test_semantic_facts_unchanged_with_relationships() -> None:
    events = _events_by_id()
    lightweight = events["lightweight-purchase-001"].semantic_facts[0]
    assert lightweight.predicate == "outerwear_weight_preference"
    assert lightweight.object == "lightweight"
    northpeak = events["northpeak-return-001"].semantic_facts[0]
    assert northpeak.predicate == "product_fit_issue"
    assert "northpeak-alpine-shell:sleeves_too_short" in northpeak.object


def test_build_catalogue_is_neutral_to_queries() -> None:
    generator = _load_generator_module()
    with_relationships = generator.build_events()
    events_without_query_build = generator.build_events()
    generator.build_queries(with_relationships)
    events_after_query_build = generator.build_events()
    relationship_fields_with = [
        event.get("relationships", []) for event in with_relationships if event.get("relationships")
    ]
    relationship_fields_after = [
        event.get("relationships", [])
        for event in events_after_query_build
        if event.get("relationships")
    ]
    assert relationship_fields_with == relationship_fields_after
    assert relationship_fields_with == relationship_fields_after
    assert events_without_query_build == events_after_query_build


def test_without_relationships_emits_no_relationship_fields() -> None:
    generator = _load_generator_module()
    events = generator.build_events(without_relationships=True)
    assert all("relationships" not in event for event in events)


def test_other_datasets_omit_relationship_fields() -> None:
    for dataset_name in ("mini", "software_project_v1", "helios_v1"):
        dataset = load_dataset(dataset_name)
        assert all(not event.relationships for event in dataset.events)


def test_generator_session_stats_acceptable() -> None:
    generator = _load_generator_module()
    stats = generator.session_stats(generator.build_events())
    assert stats["event_count"] == 149
    assert stats["largest_session_size"] <= 2
    assert not any(session_id.startswith("timeline-") for session_id in stats["session_sizes"])


def test_readme_states_independence() -> None:
    readme = load_dataset("customer_decision_context_v1").root + "/README.md"
    text = Path(readme).read_text(encoding="utf-8")
    assert "independently authored" in text.lower()
    assert "no data dependency" in text.lower()
