"""Persistent inhibition induction and behavioural metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cogkurabench.models import (
    BenchmarkQuery,
    BenchmarkUse,
    Capability,
    InhibitionTraceObservation,
    PersistentInhibitionExpectation,
    PersistentInhibitionObservation,
)

if TYPE_CHECKING:
    from cogkurabench.evaluation.result import QueryResult, UseResult


@dataclass(frozen=True, slots=True)
class InhibitionTraceDiagnostic:
    """Serialized inhibitory-trace classification for one use."""

    use_id: str
    selected_source_event_ids: tuple[str, ...]
    inhibited_source_event_ids: tuple[str, ...]
    induction_pressure: float
    classification: str


@dataclass(frozen=True, slots=True)
class PersistentInhibitionDiagnosticResult:
    """Serialized persistent-inhibition candidate classification."""

    candidate_source_event_ids: tuple[str, ...]
    penalty: float
    classification: str
    matched_expectation_id: str | None = None


def _intersects(left: Sequence[str], right: Sequence[str]) -> bool:
    return bool(set(left) & set(right))


def _harmonic_mean(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _matches_effect(
    observation: PersistentInhibitionObservation,
    expectation: PersistentInhibitionExpectation,
) -> bool:
    if not _intersects(observation.candidate_source_event_ids, expectation.candidate_event_ids):
        return False
    if not expectation.selected_event_ids:
        return True
    return any(
        _intersects(contribution.selected_source_event_ids, expectation.selected_event_ids)
        for contribution in observation.contributions
    )


def _candidate_penalty(
    observations: Sequence[PersistentInhibitionObservation],
    candidate_event_ids: Sequence[str],
) -> float:
    penalties = [
        observation.penalty
        for observation in observations
        if observation.penalty < 0.0
        and _intersects(observation.candidate_source_event_ids, candidate_event_ids)
    ]
    if not penalties:
        return 0.0
    return min(penalties)


def _is_behavioural(observation: PersistentInhibitionObservation) -> bool:
    return observation.penalty < 0.0


def compute_inhibition_trace_metrics(
    use: BenchmarkUse,
    traces: Sequence[InhibitionTraceObservation],
) -> tuple[dict[str, float], tuple[InhibitionTraceDiagnostic, ...]]:
    """Score persisted inhibitory traces for one explicit use."""
    expected_ids = list(use.expected_inhibited_event_ids)
    matched_expected: set[str] = set()
    diagnostics: list[InhibitionTraceDiagnostic] = []
    true_positive = 0
    unexpected = 0

    for trace in traces:
        classification = "unexpected"
        if _intersects(trace.inhibited_source_event_ids, use.forbidden_inhibited_event_ids):
            classification = "forbidden"
            unexpected += 1
        elif _intersects(trace.selected_source_event_ids, use.selected_event_ids) and _intersects(
            trace.inhibited_source_event_ids,
            expected_ids,
        ):
            classification = "expected"
            true_positive += 1
            for event_id in expected_ids:
                if event_id in trace.inhibited_source_event_ids:
                    matched_expected.add(event_id)
        else:
            unexpected += 1
        diagnostics.append(
            InhibitionTraceDiagnostic(
                use_id=use.id,
                selected_source_event_ids=trace.selected_source_event_ids,
                inhibited_source_event_ids=trace.inhibited_source_event_ids,
                induction_pressure=trace.induction_pressure,
                classification=classification,
            )
        )

    expected_total = len(expected_ids)
    observed = len(traces)
    precision = 1.0 if observed == 0 else true_positive / observed
    metrics: dict[str, float] = {
        "inhibition_trace_expected_matched": float(len(matched_expected)),
        "inhibition_trace_expected_total": float(expected_total),
        "inhibition_trace_observed": float(observed),
        "inhibition_trace_true_positive": float(true_positive),
        "inhibition_trace_unexpected": float(unexpected),
        "inhibition_trace_precision": precision,
    }
    if expected_total == 0:
        metrics["inhibition_trace_f1"] = 1.0 if observed == 0 else precision
    else:
        recall = len(matched_expected) / expected_total
        metrics["inhibition_trace_recall"] = recall
        metrics["inhibition_trace_f1"] = _harmonic_mean(precision, recall)
    if observed > 0:
        metrics["unexpected_inhibition_trace_rate"] = unexpected / observed
    else:
        metrics["unexpected_inhibition_trace_rate"] = 0.0
    return metrics, tuple(diagnostics)


def finalize_inhibition_trace_metrics(use_results: Sequence[UseResult]) -> dict[str, float]:
    """Micro-aggregate inhibitory-trace counts across use actions."""
    expected_matched = 0.0
    expected_total = 0.0
    observed = 0.0
    true_positive = 0.0
    unexpected = 0.0
    scored = False
    for result in use_results:
        metrics = result.metrics
        if "inhibition_trace_expected_total" not in metrics:
            continue
        scored = True
        expected_matched += metrics.get("inhibition_trace_expected_matched", 0.0)
        expected_total += metrics.get("inhibition_trace_expected_total", 0.0)
        observed += metrics.get("inhibition_trace_observed", 0.0)
        true_positive += metrics.get("inhibition_trace_true_positive", 0.0)
        unexpected += metrics.get("inhibition_trace_unexpected", 0.0)
    if not scored:
        return {}
    if expected_total == 0.0 and observed == 0.0:
        return {
            "inhibition_trace_precision": 1.0,
            "inhibition_trace_f1": 1.0,
            "unexpected_inhibition_trace_rate": 0.0,
        }
    precision = 1.0 if observed == 0.0 else true_positive / observed
    aggregated: dict[str, float] = {
        "inhibition_trace_precision": precision,
        "unexpected_inhibition_trace_rate": (unexpected / observed) if observed else 0.0,
    }
    if expected_total == 0.0:
        aggregated["inhibition_trace_f1"] = 1.0 if observed == 0.0 else precision
    else:
        recall = expected_matched / expected_total
        aggregated["inhibition_trace_recall"] = recall
        aggregated["inhibition_trace_f1"] = _harmonic_mean(precision, recall)
    return aggregated


def compute_persistent_inhibition_metrics(
    query: BenchmarkQuery,
    observations: Sequence[PersistentInhibitionObservation],
    *,
    persistent_inhibition_supported: bool,
) -> tuple[dict[str, float], tuple[PersistentInhibitionDiagnosticResult, ...]]:
    """Score persistent inhibition observations against query ground truth."""
    if not persistent_inhibition_supported:
        return {}, ()
    if query.capability is not Capability.PERSISTENT_INHIBITION and not (
        query.expected_persistent_inhibition or query.forbidden_persistent_inhibition
    ):
        return {}, ()

    behavioural = [observation for observation in observations if _is_behavioural(observation)]
    expected = [
        expectation
        for expectation in query.expected_persistent_inhibition
        if expectation.expect_negative_effect
    ]
    matched_expected: set[str] = set()
    diagnostics: list[PersistentInhibitionDiagnosticResult] = []
    unexpected = 0

    for observation in behavioural:
        classification = "unexpected"
        matched_id: str | None = None
        for expectation in expected:
            if expectation.id in matched_expected:
                continue
            if _matches_effect(observation, expectation):
                matched_expected.add(expectation.id)
                classification = "expected"
                matched_id = expectation.id
                break
        if classification == "unexpected":
            for expectation in query.forbidden_persistent_inhibition:
                if _matches_effect(observation, expectation):
                    classification = "forbidden"
                    matched_id = expectation.id
                    break
            for expectation in query.expected_persistent_inhibition:
                if expectation.expect_negative_effect:
                    continue
                if _matches_effect(observation, expectation):
                    classification = "forbidden"
                    matched_id = expectation.id
                    break
        if classification != "expected":
            unexpected += 1
        diagnostics.append(
            PersistentInhibitionDiagnosticResult(
                candidate_source_event_ids=observation.candidate_source_event_ids,
                penalty=observation.penalty,
                classification=classification,
                matched_expectation_id=matched_id,
            )
        )

    expected_total = len(expected)
    observed = len(behavioural)
    true_positive = sum(1 for item in diagnostics if item.classification == "expected")
    precision = 1.0 if observed == 0 else true_positive / observed
    positive_penalty = sum(1 for observation in observations if observation.penalty > 0.0)
    activation_increase = sum(
        1
        for observation in observations
        if observation.activation_after > observation.activation_before
        and (observation.penalty != 0.0 or observation.matched_trace_count > 0)
    )
    out_of_scope = 0
    future_visibility = 0
    scope_checks = 0
    scope_passes = 0
    history_checks = 0
    history_passes = 0
    for comparison in query.persistent_inhibition_comparisons:
        penalty = _candidate_penalty(observations, comparison.candidate_event_ids)
        if comparison.scope_isolation:
            scope_checks += 1
            if penalty == 0.0:
                scope_passes += 1
            else:
                out_of_scope += 1
        if comparison.pre_induction:
            history_checks += 1
            if penalty == 0.0:
                history_passes += 1
            else:
                future_visibility += 1
        if comparison.current_cognitive_state:
            history_checks += 1
            if penalty < 0.0:
                history_passes += 1

    metrics: dict[str, float] = {
        "persistent_inhibition_effect_expected_matched": float(len(matched_expected)),
        "persistent_inhibition_effect_expected_total": float(expected_total),
        "persistent_inhibition_effect_observed": float(observed),
        "persistent_inhibition_effect_true_positive": float(true_positive),
        "persistent_inhibition_effect_unexpected": float(unexpected),
        "persistent_inhibition_effect_precision": precision,
        "positive_inhibition_penalty_violations": float(positive_penalty),
        "activation_increase_due_to_inhibition": float(activation_increase),
        "out_of_scope_inhibition_count": float(out_of_scope),
        "future_trace_visibility_count": float(future_visibility),
        "persistent_inhibition_scope_checks": float(scope_checks),
        "persistent_inhibition_scope_passes": float(scope_passes),
        "persistent_inhibition_history_checks": float(history_checks),
        "persistent_inhibition_history_passes": float(history_passes),
    }
    if expected_total == 0:
        metrics["persistent_inhibition_effect_f1"] = 1.0 if observed == 0 else precision
    else:
        recall = len(matched_expected) / expected_total
        metrics["persistent_inhibition_effect_recall"] = recall
        metrics["persistent_inhibition_effect_f1"] = _harmonic_mean(precision, recall)
    metrics["unexpected_persistent_inhibition_rate"] = unexpected / observed if observed else 0.0
    if scope_checks:
        metrics["persistent_inhibition_scope_isolation_accuracy"] = scope_passes / scope_checks
    if history_checks:
        metrics["persistent_inhibition_history_accuracy"] = history_passes / history_checks

    threshold_expectations = [
        expectation
        for expectation in query.expected_persistent_inhibition
        if expectation.expect_threshold_suppression is not None
    ]
    if threshold_expectations:
        threshold_correct = 0
        for expectation in threshold_expectations:
            matched = [
                observation
                for observation in observations
                if _intersects(
                    observation.candidate_source_event_ids,
                    expectation.candidate_event_ids,
                )
            ]
            if matched and matched[0].crossed_activation_threshold == (
                expectation.expect_threshold_suppression is True
            ):
                threshold_correct += 1
        metrics["persistent_inhibition_threshold_checks"] = float(len(threshold_expectations))
        metrics["persistent_inhibition_threshold_passes"] = float(threshold_correct)
        metrics["persistent_inhibition_threshold_suppression_accuracy"] = threshold_correct / len(
            threshold_expectations
        )

    rank_expectations = [
        expectation
        for expectation in query.expected_persistent_inhibition
        if expectation.expect_rank_worsening is True
    ]
    if rank_expectations:
        rank_correct = 0
        for expectation in rank_expectations:
            matched = [
                observation
                for observation in observations
                if _intersects(
                    observation.candidate_source_event_ids,
                    expectation.candidate_event_ids,
                )
            ]
            if (
                matched
                and matched[0].rank_before is not None
                and matched[0].rank_after is not None
                and matched[0].rank_after > matched[0].rank_before
            ):
                rank_correct += 1
        metrics["persistent_inhibition_rank_checks"] = float(len(rank_expectations))
        metrics["persistent_inhibition_rank_passes"] = float(rank_correct)
        metrics["persistent_inhibition_rank_effect_accuracy"] = rank_correct / len(
            rank_expectations
        )

    return metrics, tuple(diagnostics)


def finalize_persistent_inhibition_metrics(
    query_results: Sequence[QueryResult],
    queries_by_id: Mapping[str, BenchmarkQuery],
) -> dict[str, float]:
    """Micro-aggregate persistent inhibition metrics, including cross-query checks."""
    expected_matched = 0.0
    expected_total = 0.0
    observed = 0.0
    true_positive = 0.0
    unexpected = 0.0
    invariant_keys = (
        "positive_inhibition_penalty_violations",
        "activation_increase_due_to_inhibition",
        "out_of_scope_inhibition_count",
        "future_trace_visibility_count",
    )
    invariants = {key: 0.0 for key in invariant_keys}
    scope_checks = 0.0
    scope_passes = 0.0
    history_checks = 0.0
    history_passes = 0.0
    threshold_checks = 0.0
    threshold_passes = 0.0
    rank_checks = 0.0
    rank_passes = 0.0
    scored = False

    observations_by_query = {
        result.query_id: result.persistent_inhibition_observations for result in query_results
    }
    for result in query_results:
        metrics = result.metrics
        if "persistent_inhibition_effect_expected_total" not in metrics:
            continue
        scored = True
        expected_matched += metrics.get("persistent_inhibition_effect_expected_matched", 0.0)
        expected_total += metrics.get("persistent_inhibition_effect_expected_total", 0.0)
        observed += metrics.get("persistent_inhibition_effect_observed", 0.0)
        true_positive += metrics.get("persistent_inhibition_effect_true_positive", 0.0)
        unexpected += metrics.get("persistent_inhibition_effect_unexpected", 0.0)
        for key in invariant_keys:
            invariants[key] += metrics.get(key, 0.0)
        scope_checks += metrics.get("persistent_inhibition_scope_checks", 0.0)
        scope_passes += metrics.get("persistent_inhibition_scope_passes", 0.0)
        history_checks += metrics.get("persistent_inhibition_history_checks", 0.0)
        history_passes += metrics.get("persistent_inhibition_history_passes", 0.0)
        threshold_checks += metrics.get("persistent_inhibition_threshold_checks", 0.0)
        threshold_passes += metrics.get("persistent_inhibition_threshold_passes", 0.0)
        rank_checks += metrics.get("persistent_inhibition_rank_checks", 0.0)
        rank_passes += metrics.get("persistent_inhibition_rank_passes", 0.0)

    if not scored:
        return {}

    precision = 1.0 if observed == 0.0 else true_positive / observed
    aggregated: dict[str, float] = {
        "persistent_inhibition_effect_precision": precision,
        "unexpected_persistent_inhibition_rate": (unexpected / observed) if observed else 0.0,
        **invariants,
    }
    if expected_total == 0.0:
        aggregated["persistent_inhibition_effect_f1"] = 1.0 if observed == 0.0 else precision
    else:
        recall = expected_matched / expected_total
        aggregated["persistent_inhibition_effect_recall"] = recall
        aggregated["persistent_inhibition_effect_f1"] = _harmonic_mean(precision, recall)
    if scope_checks:
        aggregated["persistent_inhibition_scope_isolation_accuracy"] = scope_passes / scope_checks
    if history_checks:
        aggregated["persistent_inhibition_history_accuracy"] = history_passes / history_checks
    if threshold_checks:
        aggregated["persistent_inhibition_threshold_suppression_accuracy"] = (
            threshold_passes / threshold_checks
        )
    if rank_checks:
        aggregated["persistent_inhibition_rank_effect_accuracy"] = rank_passes / rank_checks

    repetition_checks = 0
    repetition_passes = 0
    recovery_checks = 0
    recovery_passes = 0
    for query_id, query in queries_by_id.items():
        if query_id not in observations_by_query:
            continue
        current = observations_by_query[query_id]
        for comparison in query.persistent_inhibition_comparisons:
            if comparison.stronger_than_query_id is not None:
                baseline_id = comparison.stronger_than_query_id
                if baseline_id not in observations_by_query:
                    repetition_checks += 1
                    continue
                repetition_checks += 1
                later = abs(_candidate_penalty(current, comparison.candidate_event_ids))
                earlier = abs(
                    _candidate_penalty(
                        observations_by_query[baseline_id],
                        comparison.candidate_event_ids,
                    )
                )
                if later > earlier:
                    repetition_passes += 1
            if comparison.weaker_than_query_id is not None:
                previous_id = comparison.weaker_than_query_id
                if previous_id not in observations_by_query:
                    recovery_checks += 1
                    continue
                recovery_checks += 1
                current_magnitude = abs(_candidate_penalty(current, comparison.candidate_event_ids))
                previous_magnitude = abs(
                    _candidate_penalty(
                        observations_by_query[previous_id],
                        comparison.candidate_event_ids,
                    )
                )
                if current_magnitude < previous_magnitude:
                    recovery_passes += 1
    if repetition_checks:
        aggregated["repetition_strengthening_accuracy"] = repetition_passes / repetition_checks
    if recovery_checks:
        aggregated["inhibition_recovery_order_accuracy"] = recovery_passes / recovery_checks
    return aggregated
