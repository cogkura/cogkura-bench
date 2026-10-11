"""Dataset rules for the 0.3.8 persistent-inhibition workloads."""

from __future__ import annotations

import subprocess

from cogkurabench.dataset import load_dataset, validate_dataset
from cogkurabench.models import Capability, QueryAction, UseAction

_WORKLOADS = (
    "persistent_inhibition_software_v1",
    "persistent_inhibition_customer_v1",
)
_FROZEN = (
    "datasets/persistent_inhibition_v1",
    "datasets/transient_interference_v1",
    "datasets/transient_interference_v2",
    "datasets/interference_v1",
)
_CO_CONSUMPTION = {
    "persistent_inhibition_software_v1": "sw-use-cache",
    "persistent_inhibition_customer_v1": "cu-use-traits",
}
_RESELECTION = {
    "persistent_inhibition_software_v1": ("sw-use-jenkins", "sw-pay-jenkins"),
    "persistent_inhibition_customer_v1": ("cu-use-black", "cu-black"),
}


def test_workloads_validate() -> None:
    for name in _WORKLOADS:
        assert validate_dataset(name) == []
        dataset = load_dataset(name)
        assert dataset.manifest.required_capabilities == ("persistent_inhibition",)
        assert dataset.manifest.uses == len(dataset.uses)
        assert dataset.manifest.events == len(dataset.events)
        assert dataset.manifest.queries == len(dataset.queries)
        assert dataset.feedback == ()


def test_uses_follow_their_source_queries() -> None:
    for name in _WORKLOADS:
        dataset = load_dataset(name)
        seen_queries: set[str] = set()
        for action in dataset.actions:
            if isinstance(action, QueryAction):
                seen_queries.add(action.query.id)
            if isinstance(action, UseAction):
                assert action.use.query_id in seen_queries
                source = dataset.query_by_id()[action.use.query_id]
                assert action.use.timestamp >= source.timestamp


def test_selective_uses_name_losers_and_co_consumption_does_not() -> None:
    for name in _WORKLOADS:
        dataset = load_dataset(name)
        co_consumption = _CO_CONSUMPTION[name]
        assert any(use.id == co_consumption for use in dataset.uses)
        for use in dataset.uses:
            assert set(use.selected_event_ids).isdisjoint(use.expected_inhibited_event_ids)
            if use.id == co_consumption:
                assert use.expected_inhibited_event_ids == ()
                assert len(use.selected_event_ids) == 2
            elif use.expected_inhibited_event_ids:
                assert use.expected_inhibited_event_ids


def test_labelled_queries_declare_effects_and_recovery_links() -> None:
    for name in _WORKLOADS:
        dataset = load_dataset(name)
        recovery = [
            query
            for query in dataset.queries
            if any(item.weaker_than_query_id for item in query.persistent_inhibition_comparisons)
        ]
        assert len(recovery) >= 2
        linked = {query.id for query in dataset.queries}
        for query in dataset.queries:
            if query.capability is not Capability.PERSISTENT_INHIBITION:
                continue
            assert query.expected_persistent_inhibition or query.forbidden_persistent_inhibition
        for query in recovery:
            for comparison in query.persistent_inhibition_comparisons:
                if comparison.weaker_than_query_id is not None:
                    assert comparison.weaker_than_query_id in linked


def test_reselection_follows_the_inhibiting_uses() -> None:
    for name, (use_id, event_id) in _RESELECTION.items():
        dataset = load_dataset(name)
        reselection = next(use for use in dataset.uses if use.id == use_id)
        inhibitors = [
            use
            for use in dataset.uses
            if event_id in use.expected_inhibited_event_ids and use.id != use_id
        ]
        assert inhibitors
        assert all(use.timestamp < reselection.timestamp for use in inhibitors)
        assert event_id in reselection.selected_event_ids
        assert reselection.expected_inhibited_event_ids


def test_frozen_fixtures_are_unchanged() -> None:
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", *_FROZEN],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
