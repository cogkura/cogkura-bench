"""Score declared observable facts; no source-trust or qualification algorithm."""

from __future__ import annotations

from collections import defaultdict

from cogkurabench.source_models import (
    FIELD_CATEGORIES,
    CheckValue,
    SourceAssessmentExpectation,
    SourceAssessmentObservation,
)


def observed_fields(observation: SourceAssessmentObservation) -> dict[str, object]:
    values: dict[str, object] = {
        name: getattr(observation, name) for name in observation.__dataclass_fields__
    }
    for prefix in ("quality", "context_quality"):
        quality = getattr(observation, prefix)
        if quality is not None:
            values.update(
                {f"{prefix}.{k}": getattr(quality, k) for k in quality.__dataclass_fields__}
            )
    values["decision_reasons"] = tuple(r for d in observation.decisions for r in d.reasons)
    values["decision_outcomes"] = tuple(d.outcome for d in observation.decisions)
    values["decision_event_ids"] = tuple(e for d in observation.decisions for e in d.event_ids)
    values["revision_views"] = tuple(r.view for r in observation.revisions)
    values["revision_statuses"] = tuple(str(r.status) for r in observation.revisions)
    values["latest_values"] = tuple(str(v).lower() for r in observation.revisions for v in r.latest)
    return values


def check_matches(key: str, expected: CheckValue, fields: dict[str, object]) -> bool:
    mode = "equal"
    for suffix in ("_contains", "_excludes"):
        if key.endswith(suffix):
            key, mode = key.removesuffix(suffix), suffix
            break
    if key not in fields:
        return False
    actual = fields[key]
    if isinstance(expected, tuple):
        if not isinstance(actual, tuple):
            return False
        if mode == "_contains":
            return set(expected) <= set(actual)
        if mode == "_excludes":
            return set(expected).isdisjoint(actual)
        return set(expected) == set(actual)
    # bool and int are distinct in the contract, including explicit unknown None.
    return type(actual) is type(expected) and actual == expected


def compute_source_assessment_metrics(
    expectation: SourceAssessmentExpectation | None,
    observation: SourceAssessmentObservation | None,
    *,
    supported: bool,
    decisions_supported: bool,
) -> dict[str, float]:
    if not supported or expectation is None:
        return {}
    checks = dict(expectation.checks)
    if decisions_supported:
        checks.update(expectation.diagnostic_checks)
    fields = observed_fields(observation) if observation is not None else {}
    totals: dict[str, int] = defaultdict(int)
    hits: dict[str, int] = defaultdict(int)
    for key, expected in checks.items():
        category = FIELD_CATEGORIES[key]
        totals[category] += 1
        hits[category] += int(check_matches(key, expected, fields))
    matched = sum(hits.values())
    metrics = {
        "source_assessment_accuracy": matched / len(checks),
        "source_assessment_mismatch_count": float(len(checks) - matched),
        "source_assessment_check_count": float(len(checks)),
        "source_assessment_match_count": float(matched),
    }
    for category, total in totals.items():
        metrics[f"source_{category}_accuracy"] = hits[category] / total
        metrics[f"source_{category}_check_count"] = float(total)
        metrics[f"source_{category}_match_count"] = float(hits[category])
    metrics["source_false_certainty_count"] = float(
        sum(
            not check_matches(key, expected, fields)
            for key, expected in checks.items()
            if (expected is False and ("complete" in key or key == "quality.has_evidence"))
            or key in ("independence", "decision_history")
            or (key == "state" and expected == "indeterminate")
        )
    )
    forbidden = checks.get("event_ids_excludes", ())
    metrics["source_future_leak_count"] = float(
        len(
            set(forbidden if isinstance(forbidden, tuple) else ())
            & set(observation.event_ids if observation else ())
        )
    )
    if "conflict" in checks:
        expected_conflict = checks["conflict"] == "semantic_conflict"
        actual_conflict = observation is not None and observation.conflict == "semantic_conflict"
        metrics["source_conflict_expected_count"] = float(expected_conflict)
        metrics["source_conflict_observed_count"] = float(actual_conflict)
        metrics["source_conflict_matched_count"] = float(expected_conflict and actual_conflict)
    return metrics


def finalize_source_assessment_metrics(metric_rows: list[dict[str, float]]) -> dict[str, float]:
    """Micro-average declared checks; aggregate violation counts by sum."""
    totals: dict[str, float] = defaultdict(float)
    for row in metric_rows:
        for key, value in row.items():
            if key.startswith("source_") and key.endswith("_count"):
                totals[key] += value
    metrics = dict(totals)
    for key, count in totals.items():
        if key.endswith("_check_count") and count:
            stem = key.removesuffix("_check_count")
            metrics[f"{stem}_accuracy"] = totals[f"{stem}_match_count"] / count
    matched = totals.get("source_conflict_matched_count", 0)
    for kind, denominator in (("precision", "observed"), ("recall", "expected")):
        count = totals.get(f"source_conflict_{denominator}_count", 0)
        if count:
            metrics[f"source_conflict_{kind}"] = matched / count
    return metrics
