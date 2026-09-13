"""Transient interference behavioural metrics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    InterferenceContributionObservation,
    TransientInterferenceExpectation,
    TransientInterferenceObservation,
)

if TYPE_CHECKING:
    from cogkurabench.evaluation.result import QueryResult


@dataclass(frozen=True, slots=True)
class TransientInterferenceDiagnosticResult:
    """Serialized behavioural interference contribution with classification."""

    candidate_source_event_ids: tuple[str, ...]
    competitor_source_event_ids: tuple[str, ...]
    direction: CompetitionDirection
    pressure: float
    competition_strength: float
    competitor_accessibility: float
    classification: str
    matched_expectation_id: str | None = None


@dataclass(frozen=True, slots=True)
class TransientInterferenceCandidateDiagnostic:
    """Per-candidate behavioural interference summary."""

    candidate_source_event_ids: tuple[str, ...]
    activation_before: float
    activation_after: float
    total_penalty: float
    crossed_activation_threshold: bool
    rank_before: int | None
    rank_after: int | None


def _intersects(left: Sequence[str], right: Sequence[str]) -> bool:
    return bool(set(left) & set(right))


def _matches_expectation(
    candidate_event_ids: Sequence[str],
    competitor_event_ids: Sequence[str],
    expectation: TransientInterferenceExpectation,
) -> bool:
    return _intersects(candidate_event_ids, expectation.candidate_event_ids) and _intersects(
        competitor_event_ids,
        expectation.competitor_event_ids,
    )


def _contribution_key(
    candidate_event_ids: Sequence[str],
    competitor_event_ids: Sequence[str],
    direction: CompetitionDirection,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    return (
        tuple(sorted(candidate_event_ids)),
        tuple(sorted(competitor_event_ids)),
        direction.value,
    )


def _is_behaviourally_active(
    contribution: InterferenceContributionObservation,
    observation: TransientInterferenceObservation,
) -> bool:
    if contribution.pressure <= 0.0:
        return False
    return observation.total_penalty < 0.0


def _harmonic_mean(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _check_invariants(
    observations: Sequence[TransientInterferenceObservation],
) -> dict[str, float]:
    positive_penalty = 0
    activation_increase = 0
    cotemporal_penalty = 0
    historical_future = 0

    for observation in observations:
        if observation.proactive_penalty > 0.0 or observation.retroactive_penalty > 0.0:
            positive_penalty += 1
        if observation.activation_after > observation.activation_before:
            activation_increase += 1
        for contribution in observation.contributions:
            if (
                contribution.direction is CompetitionDirection.CO_TEMPORAL
                and contribution.pressure > 0.0
                and observation.total_penalty < 0.0
            ):
                cotemporal_penalty += 1
        if observation.total_penalty < 0.0 and not observation.contributions:
            historical_future += 1

    return {
        "positive_penalty_violation_count": float(positive_penalty),
        "activation_increase_due_to_interference_count": float(activation_increase),
        "cotemporal_penalty_violation_count": float(cotemporal_penalty),
        "historical_future_interference_count": float(historical_future),
    }


def compute_transient_interference_metrics(
    query: BenchmarkQuery,
    observations: Sequence[TransientInterferenceObservation],
    *,
    transient_interference_supported: bool,
) -> tuple[
    dict[str, float],
    tuple[TransientInterferenceDiagnosticResult, ...],
    tuple[TransientInterferenceCandidateDiagnostic, ...],
]:
    """Score transient interference observations against query ground truth."""
    if not transient_interference_supported:
        return {}, (), ()

    if query.capability is not Capability.TRANSIENT_INTERFERENCE and not (
        query.expected_interference_effects or query.forbidden_interference_effects
    ):
        return {}, (), ()

    candidate_diagnostics = tuple(
        TransientInterferenceCandidateDiagnostic(
            candidate_source_event_ids=obs.candidate_source_event_ids,
            activation_before=obs.activation_before,
            activation_after=obs.activation_after,
            total_penalty=obs.total_penalty,
            crossed_activation_threshold=obs.crossed_activation_threshold,
            rank_before=obs.rank_before,
            rank_after=obs.rank_after,
        )
        for obs in observations
    )

    invariants = _check_invariants(observations)

    active_contributions: list[
        tuple[
            TransientInterferenceObservation,
            InterferenceContributionObservation,
        ]
    ] = []
    seen_keys: set[tuple[tuple[str, ...], tuple[str, ...], str]] = set()
    for observation in observations:
        for contribution in observation.contributions:
            if not _is_behaviourally_active(contribution, observation):
                continue
            key = _contribution_key(
                observation.candidate_source_event_ids,
                contribution.competitor_source_event_ids,
                contribution.direction,
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            active_contributions.append((observation, contribution))

    expected_total = len(query.expected_interference_effects)
    forbidden_total = len(query.forbidden_interference_effects)
    matched_expected_ids: set[str] = set()
    direction_correct = 0
    direction_total = 0
    forbidden_hits = 0
    diagnostics: list[TransientInterferenceDiagnosticResult] = []

    for observation, contribution in active_contributions:
        classification = "unexpected"
        matched_id: str | None = None

        for expectation in query.expected_interference_effects:
            if expectation.id in matched_expected_ids:
                continue
            if _matches_expectation(
                observation.candidate_source_event_ids,
                contribution.competitor_source_event_ids,
                expectation,
            ):
                matched_expected_ids.add(expectation.id)
                classification = "expected"
                matched_id = expectation.id
                direction_total += 1
                if contribution.direction is expectation.direction:
                    direction_correct += 1
                break

        if classification == "unexpected":
            for expectation in query.forbidden_interference_effects:
                if _matches_expectation(
                    observation.candidate_source_event_ids,
                    contribution.competitor_source_event_ids,
                    expectation,
                ):
                    classification = "forbidden"
                    matched_id = expectation.id
                    forbidden_hits += 1
                    break

        diagnostics.append(
            TransientInterferenceDiagnosticResult(
                candidate_source_event_ids=observation.candidate_source_event_ids,
                competitor_source_event_ids=contribution.competitor_source_event_ids,
                direction=contribution.direction,
                pressure=contribution.pressure,
                competition_strength=contribution.competition_strength,
                competitor_accessibility=contribution.competitor_accessibility,
                classification=classification,
                matched_expectation_id=matched_id,
            )
        )

    observed_count = len(active_contributions)
    matched_expected = len(matched_expected_ids)
    true_positive = sum(1 for diag in diagnostics if diag.classification == "expected")

    metrics: dict[str, float] = {
        "interference_effect_expected_matched": float(matched_expected),
        "interference_effect_expected_total": float(expected_total),
        "interference_effect_observed_pairs": float(observed_count),
        "interference_effect_true_positive_pairs": float(true_positive),
        "interference_effect_forbidden_hit": float(forbidden_hits),
        "interference_effect_forbidden_total": float(forbidden_total),
        "interference_effect_unexpected_pairs": float(
            sum(1 for diag in diagnostics if diag.classification in ("unexpected", "forbidden"))
        ),
        "interference_effect_direction_correct": float(direction_correct),
        "interference_effect_direction_total": float(direction_total),
        **invariants,
    }

    if observed_count == 0:
        precision = 1.0 if expected_total == 0 else 1.0
    else:
        precision = true_positive / observed_count

    if expected_total == 0:
        recall_metric: float | None = None
        f1 = 1.0 if observed_count == 0 else precision
    else:
        recall_metric = matched_expected / expected_total
        f1 = _harmonic_mean(precision, recall_metric)

    metrics["interference_effect_precision"] = precision
    metrics["interference_effect_f1"] = f1
    if recall_metric is not None:
        metrics["interference_effect_recall"] = recall_metric

    if direction_total > 0:
        metrics["interference_effect_direction_accuracy"] = direction_correct / direction_total

    if observed_count > 0:
        unexpected = sum(
            1 for diag in diagnostics if diag.classification in ("unexpected", "forbidden")
        )
        metrics["unexpected_interference_rate"] = unexpected / observed_count
    elif expected_total == 0:
        metrics["unexpected_interference_rate"] = 0.0

    threshold_expectations = [
        exp
        for exp in query.expected_interference_effects
        if exp.expect_threshold_suppression is not None
    ]
    if threshold_expectations:
        threshold_correct = 0
        for expectation in threshold_expectations:
            matched_obs = [
                obs
                for obs in observations
                if _intersects(obs.candidate_source_event_ids, expectation.candidate_event_ids)
            ]
            if not matched_obs:
                continue
            obs = matched_obs[0]
            expected_crossed = expectation.expect_threshold_suppression is True
            if obs.crossed_activation_threshold == expected_crossed:
                threshold_correct += 1
        metrics["threshold_suppression_accuracy"] = threshold_correct / len(threshold_expectations)

    rank_expectations = [
        exp for exp in query.expected_interference_effects if exp.expect_rank_worsening is True
    ]
    if rank_expectations:
        rank_correct = 0
        for expectation in rank_expectations:
            matched_obs = [
                obs
                for obs in observations
                if _intersects(obs.candidate_source_event_ids, expectation.candidate_event_ids)
            ]
            if not matched_obs:
                continue
            obs = matched_obs[0]
            if (
                obs.rank_before is not None
                and obs.rank_after is not None
                and obs.rank_after > obs.rank_before
            ):
                rank_correct += 1
        metrics["rank_effect_accuracy"] = rank_correct / len(rank_expectations)

    return metrics, tuple(diagnostics), candidate_diagnostics


def finalize_transient_interference_metrics(
    query_results: Sequence[QueryResult],
) -> dict[str, float]:
    """Micro-aggregate transient interference counts across queries."""
    expected_matched = 0.0
    expected_total = 0.0
    observed_pairs = 0.0
    true_positive = 0.0
    forbidden_hit = 0.0
    forbidden_total = 0.0
    unexpected_pairs = 0.0
    direction_correct = 0.0
    direction_total = 0.0
    invariant_keys = (
        "positive_penalty_violation_count",
        "activation_increase_due_to_interference_count",
        "cotemporal_penalty_violation_count",
        "historical_future_interference_count",
    )
    invariants: dict[str, float] = {key: 0.0 for key in invariant_keys}

    for result in query_results:
        metrics = result.metrics
        if "interference_effect_expected_total" not in metrics:
            continue
        expected_matched += metrics.get("interference_effect_expected_matched", 0.0)
        expected_total += metrics.get("interference_effect_expected_total", 0.0)
        observed_pairs += metrics.get("interference_effect_observed_pairs", 0.0)
        true_positive += metrics.get("interference_effect_true_positive_pairs", 0.0)
        forbidden_hit += metrics.get("interference_effect_forbidden_hit", 0.0)
        forbidden_total += metrics.get("interference_effect_forbidden_total", 0.0)
        unexpected_pairs += metrics.get("interference_effect_unexpected_pairs", 0.0)
        direction_correct += metrics.get("interference_effect_direction_correct", 0.0)
        direction_total += metrics.get("interference_effect_direction_total", 0.0)
        for key in invariant_keys:
            invariants[key] += metrics.get(key, 0.0)

    if expected_total == 0.0 and observed_pairs == 0.0:
        return {}

    if observed_pairs == 0.0:
        precision = 1.0
    else:
        precision = true_positive / observed_pairs

    if expected_total == 0.0:
        recall: float | None = None
        f1 = 1.0 if observed_pairs == 0.0 else precision
    else:
        recall = expected_matched / expected_total
        f1 = _harmonic_mean(precision, recall)

    aggregated: dict[str, float] = {
        "interference_effect_precision": precision,
        "interference_effect_f1": f1,
        **invariants,
    }
    if recall is not None:
        aggregated["interference_effect_recall"] = recall
    if direction_total > 0.0:
        aggregated["interference_effect_direction_accuracy"] = direction_correct / direction_total
    if observed_pairs > 0.0:
        aggregated["unexpected_interference_rate"] = unexpected_pairs / observed_pairs
    return aggregated
