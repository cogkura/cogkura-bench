"""Metamemory detection metrics."""

from __future__ import annotations


def classification_scores(
    *,
    positives: int,
    true_positives: int,
    predicted_positives: int,
) -> dict[str, float]:
    """Compute precision, recall, and F1 for a binary classification."""
    precision = true_positives / predicted_positives if predicted_positives else 0.0
    recall = true_positives / positives if positives else 1.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def missing_knowledge_detection(
    *,
    should_abstain: bool,
    indicates_missing_knowledge: bool | None,
) -> dict[str, float]:
    """Score one missing-knowledge prediction."""
    if indicates_missing_knowledge is None:
        return {}
    predicted = indicates_missing_knowledge
    if should_abstain and predicted:
        return {"missing_knowledge_tp": 1.0}
    if should_abstain and not predicted:
        return {"missing_knowledge_fn": 1.0}
    if not should_abstain and predicted:
        return {"missing_knowledge_fp": 1.0}
    return {"missing_knowledge_tn": 1.0}


def conflict_detection(
    *,
    has_conflict_evidence: bool,
    indicates_conflict: bool | None,
) -> dict[str, float]:
    """Score one conflict detection prediction."""
    if indicates_conflict is None:
        return {}
    predicted = indicates_conflict
    if has_conflict_evidence and predicted:
        return {"conflict_tp": 1.0}
    if has_conflict_evidence and not predicted:
        return {"conflict_fn": 1.0}
    if not has_conflict_evidence and predicted:
        return {"conflict_fp": 1.0}
    return {"conflict_tn": 1.0}


def aggregate_binary_metrics(counts: dict[str, float], prefix: str) -> dict[str, float]:
    """Aggregate TP/FP/FN/TN counts into precision/recall/F1."""
    tp = int(counts.get(f"{prefix}_tp", 0))
    fp = int(counts.get(f"{prefix}_fp", 0))
    fn = int(counts.get(f"{prefix}_fn", 0))
    tn = int(counts.get(f"{prefix}_tn", 0))
    positives = tp + fn
    predicted_positives = tp + fp
    scores = classification_scores(
        positives=positives,
        true_positives=tp,
        predicted_positives=predicted_positives,
    )
    return {
        f"{prefix}_precision": scores["precision"],
        f"{prefix}_recall": scores["recall"],
        f"{prefix}_f1": scores["f1"],
        f"{prefix}_support": float(positives),
        f"{prefix}_negatives": float(tn + fp),
    }
