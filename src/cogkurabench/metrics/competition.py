"""Competition diagnostic metrics for interference capability queries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cogkurabench.models import (
    BenchmarkQuery,
    Capability,
    CompetitionDirection,
    CompetitionExpectation,
    CompetitionObservation,
)

if TYPE_CHECKING:
    from cogkurabench.evaluation.result import QueryResult


@dataclass(frozen=True, slots=True)
class CompetitionDiagnosticResult:
    """Serialized competition observation with benchmark classification."""

    candidate_source_event_ids: tuple[str, ...]
    competitor_source_event_ids: tuple[str, ...]
    direction: CompetitionDirection
    strength: float | None
    classification: str
    matched_expectation_id: str | None = None


def _intersects(left: Sequence[str], right: Sequence[str]) -> bool:
    return bool(set(left) & set(right))


def _matches_expectation(
    observation: CompetitionObservation,
    expectation: CompetitionExpectation,
) -> bool:
    return _intersects(
        observation.candidate_source_event_ids,
        expectation.candidate_event_ids,
    ) and _intersects(
        observation.competitor_source_event_ids,
        expectation.competitor_event_ids,
    )


def _canonical_key(
    observation: CompetitionObservation,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    return (
        tuple(sorted(observation.candidate_source_event_ids)),
        tuple(sorted(observation.competitor_source_event_ids)),
        observation.direction.value,
    )


def _canonicalize_observations(
    observations: Sequence[CompetitionObservation],
) -> tuple[CompetitionObservation, ...]:
    seen: set[tuple[tuple[str, ...], tuple[str, ...], str]] = set()
    canonical: list[CompetitionObservation] = []
    for observation in observations:
        key = _canonical_key(observation)
        if key in seen:
            continue
        seen.add(key)
        canonical.append(observation)
    return tuple(canonical)


def _expectation_signature(
    expectation: CompetitionExpectation,
) -> tuple[tuple[str, ...], tuple[str, ...], str | None]:
    direction = expectation.direction.value if expectation.direction is not None else None
    return (
        tuple(sorted(expectation.candidate_event_ids)),
        tuple(sorted(expectation.competitor_event_ids)),
        direction,
    )


def _harmonic_mean(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def compute_competition_metrics(
    query: BenchmarkQuery,
    observations: Sequence[CompetitionObservation],
    *,
    competition_diagnostics_supported: bool,
) -> tuple[dict[str, float], tuple[CompetitionDiagnosticResult, ...]]:
    """Score competition observations against query ground truth."""
    if not competition_diagnostics_supported:
        return {}, ()
    if query.capability is not Capability.INTERFERENCE and not (
        query.expected_competitions or query.forbidden_competitions
    ):
        return {}, ()

    canonical = _canonicalize_observations(observations)
    expected_total = len(query.expected_competitions)
    forbidden_total = len(query.forbidden_competitions)

    matched_expected_ids: set[str] = set()
    direction_correct = 0
    direction_total = 0
    forbidden_hits = 0
    diagnostics: list[CompetitionDiagnosticResult] = []

    for observation in canonical:
        classification = "unexpected"
        matched_id: str | None = None

        for expectation in query.expected_competitions:
            if expectation.id in matched_expected_ids:
                continue
            if _matches_expectation(observation, expectation):
                matched_expected_ids.add(expectation.id)
                classification = "expected"
                matched_id = expectation.id
                if expectation.direction is not None:
                    direction_total += 1
                    if observation.direction is expectation.direction:
                        direction_correct += 1
                break

        if classification == "unexpected":
            for expectation in query.forbidden_competitions:
                if _matches_expectation(observation, expectation):
                    classification = "forbidden"
                    matched_id = expectation.id
                    forbidden_hits += 1
                    break

        diagnostics.append(
            CompetitionDiagnosticResult(
                candidate_source_event_ids=observation.candidate_source_event_ids,
                competitor_source_event_ids=observation.competitor_source_event_ids,
                direction=observation.direction,
                strength=observation.strength,
                classification=classification,
                matched_expectation_id=matched_id,
            )
        )

    matched_expected = len(matched_expected_ids)
    observed_count = len(canonical)

    true_positive_observations = sum(1 for diag in diagnostics if diag.classification == "expected")

    metrics: dict[str, float] = {
        "competition_expected_matched": float(matched_expected),
        "competition_expected_total": float(expected_total),
        "competition_observed_pairs": float(observed_count),
        "competition_true_positive_observations": float(true_positive_observations),
        "competition_forbidden_hit": float(forbidden_hits),
        "competition_forbidden_total": float(forbidden_total),
        "competition_direction_correct": float(direction_correct),
        "competition_direction_total": float(direction_total),
    }

    if observed_count == 0:
        precision = 1.0 if expected_total == 0 else 1.0
    else:
        true_positive_observations = sum(
            1 for diag in diagnostics if diag.classification == "expected"
        )
        precision = true_positive_observations / observed_count

    if expected_total == 0:
        recall_metric: float | None = None
        f1 = 1.0 if observed_count == 0 else precision
    else:
        recall_metric = matched_expected / expected_total
        f1 = _harmonic_mean(precision, recall_metric)

    metrics["competition_pair_precision"] = precision
    metrics["competition_pair_f1"] = f1
    if recall_metric is not None:
        metrics["competition_pair_recall"] = recall_metric

    if direction_total > 0:
        metrics["competition_direction_accuracy"] = direction_correct / direction_total
    if forbidden_total > 0:
        metrics["forbidden_competition_rate"] = forbidden_hits / forbidden_total

    return metrics, tuple(diagnostics)


def finalize_competition_metrics(
    query_results: Sequence[QueryResult],
) -> dict[str, float]:
    """Micro-aggregate competition counts across interference queries."""
    expected_matched = 0.0
    expected_total = 0.0
    observed_pairs = 0.0
    true_positive_observations = 0.0
    forbidden_hit = 0.0
    forbidden_total = 0.0
    direction_correct = 0.0
    direction_total = 0.0

    for result in query_results:
        metrics = result.metrics
        if "competition_expected_total" not in metrics:
            continue
        expected_matched += metrics.get("competition_expected_matched", 0.0)
        expected_total += metrics.get("competition_expected_total", 0.0)
        observed_pairs += metrics.get("competition_observed_pairs", 0.0)
        true_positive_observations += metrics.get("competition_true_positive_observations", 0.0)
        forbidden_hit += metrics.get("competition_forbidden_hit", 0.0)
        forbidden_total += metrics.get("competition_forbidden_total", 0.0)
        direction_correct += metrics.get("competition_direction_correct", 0.0)
        direction_total += metrics.get("competition_direction_total", 0.0)

    if expected_total == 0.0 and observed_pairs == 0.0:
        return {}

    if observed_pairs == 0.0:
        precision = 1.0
    else:
        precision = true_positive_observations / observed_pairs

    if expected_total == 0.0:
        recall: float | None = None
        f1 = 1.0 if observed_pairs == 0.0 else precision
    else:
        recall = expected_matched / expected_total
        f1 = _harmonic_mean(precision, recall)

    aggregated: dict[str, float] = {
        "competition_pair_precision": precision,
        "competition_pair_f1": f1,
    }
    if recall is not None:
        aggregated["competition_pair_recall"] = recall
    if direction_total > 0.0:
        aggregated["competition_direction_accuracy"] = direction_correct / direction_total
    if forbidden_total > 0.0:
        aggregated["forbidden_competition_rate"] = forbidden_hit / forbidden_total
    return aggregated
