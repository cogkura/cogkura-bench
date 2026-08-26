"""Customer decision context dataset integration tests."""

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import Capability


def test_customer_decision_context_validates() -> None:
    assert validate_dataset("customer_decision_context_v1") == []


def test_customer_decision_context_manifest() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    assert dataset.manifest.name == "customer-decision-context-v1"
    assert dataset.manifest.events == 149
    assert dataset.manifest.queries == 1
    assert Capability.WORKING_MEMORY in dataset.manifest.required_capabilities


def test_customer_decision_context_query_has_evidence_groups() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    query = dataset.query_by_id()["customer-waterproof-jacket"]
    assert query.capability == Capability.WORKING_MEMORY
    assert query.retrieval_limit == 50
    assert query.prompt_budget_tokens == 750
    assert len(query.expected_evidence_groups) == 5
    assert len(query.forbidden_evidence_groups) == 2
    assert "core" in query.tags


def test_current_size_m_after_historical_l() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    events = dataset.event_by_id()
    size_l = events["size-old-l-001"]
    size_m = events["size-current-m-001"]
    query = dataset.query_by_id()["customer-waterproof-jacket"]
    assert size_l.timestamp < size_m.timestamp < query.timestamp


def test_hiking_and_skiing_cardinality_many() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    events = dataset.event_by_id()
    hiking = events["hiking-interest-001"].semantic_facts[0]
    skiing = events["ski-interest-001"].semantic_facts[0]
    assert hiking.cardinality == "many"
    assert skiing.cardinality == "many"


def test_size_cardinality_one() -> None:
    dataset = load_dataset("customer_decision_context_v1")
    events = dataset.event_by_id()
    for event_id in ("size-old-l-001", "size-current-m-001"):
        assert events[event_id].semantic_facts[0].cardinality == "one"


def test_readme_states_independence() -> None:
    readme = load_dataset("customer_decision_context_v1").root + "/README.md"
    from pathlib import Path

    text = Path(readme).read_text(encoding="utf-8")
    assert "independently authored" in text.lower()
    assert "no data dependency" in text.lower()
