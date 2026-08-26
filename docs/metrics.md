# Metrics

## Retrieval scoring unit (0.2.0)

Primary retrieval metrics treat the first K ranked `RetrievedItem` objects as top-K. Each item may cite multiple `source_event_ids`; relevance uses set semantics within the item (any expected ID is a hit).

`QueryResult.retrieved_event_ids` remains a flattened, deduplicated projection for provenance and inspection.

Compare primary capability scores only within the same benchmark version. Retrieval scores from 0.1.x are not directly comparable to 0.2.0 because top-K semantics changed from event positions to retrieved-item rank positions.

## Retrieval (all queries)

- Recall@K (1, 3, 5, 10)
- Precision@K
- Mean Reciprocal Rank (MRR)
- nDCG (expected=2, acceptable=1, else=0)
- Forbidden intrusion rate

## Cognitive capabilities

| Capability | Primary metrics |
|------------|-----------------|
| Temporal recall | `temporal_current_accuracy`, `temporal_historical_accuracy` |
| Knowledge update | `updated_evidence_recall`, `stale_intrusion_rate`, `current_state_ranking` |
| Forgetting | `stale_suppression_rate`, `relevant_long_term_retention`, `noise_intrusion_rate` |
| Working memory | `evidence_coverage_at_budget`, `context_precision`, `token_efficiency` |
| Learning | `delta_recall@5`, `delta_mrr`, `delta_first_relevant_rank` |
| Metamemory | `missing_knowledge_f1`, `conflict_f1` |
| Efficiency | `retrieval_latency_ms`, `memories_retrieved`, `memories_selected`, `total_context_tokens` |

Metrics operate on benchmark event IDs and neutral `QueryResult` fields (`context_event_ids`, `indicates_missing_knowledge`, `indicates_conflict`). `RetrievedItem.metadata` and per-item diagnostics do not influence scoring. Unsupported backend capabilities are omitted.

Metamemory results from CogKuraBench 0.1.0 omitted CogKura's explicit `missing_knowledge` flag. Compare metamemory under 0.1.1 against a corrected baseline (same benchmark version), not against raw 0.1.0 metamemory scores.

## Reporting

- Capability tables show each capability's **primary** metric (for example `temporal_current_accuracy` for temporal recall).
- Temporal recall also reports `temporal_historical_accuracy` as a secondary column.
- Queries may carry optional `tags`; `compare` and summary Markdown include an **All queries** table and a **Core queries** table (queries tagged `core`).
- Core metamemory F1/conflict F1 in the core table use the same count aggregation as the full run (`finalize_metamemory_metrics`), not a naive average of per-query F1 values.
- Abstain/leak queries (`should_abstain`) are excluded from retrieval metric averages but still contribute metamemory counts.

Each specialized metric module has hand-calculated unit tests in `tests/unit/test_specialized_metrics.py` and grouped scoring tests in `tests/unit/test_metrics_group_retrieval.py`.

## Evidence groups (0.3.0)

Queries may declare **evidence groups**: concept clusters scored by provenance intersection (`item.source_event_ids ∩ group.event_ids ≠ ∅`). Flat `expected_evidence_ids` and `forbidden_evidence_ids` remain the ground truth for Recall@K and working-memory coverage.

| Metric | Meaning |
| --- | --- |
| `evidence_group_coverage_at_retrieval` | Expected groups present in broad recall (`retrieve()`) |
| `evidence_group_coverage_at_budget` | Expected groups present in bounded context (`select_context()`) |
| `forbidden_group_intrusion_at_budget` | Forbidden groups present in bounded context |
| `redundant_expected_group_items` | Context items that add no new expected-group coverage |
| `unclassified_context_items` | Context items matching neither expected nor forbidden groups |

**Stages** (when bounded context is evaluated):

| Stage | Meaning |
| --- | --- |
| `selected` | Group in broad recall and bounded context |
| `selection_drop` | Group in broad recall but dropped from bounded context |
| `retrieval_miss` | Group absent from both stages |
| `context_only` | Group only in bounded context |

When a backend does not support `select_context`, stages are not emitted for broad-recall hits (no fake `selection_drop`). Inspect and JSON still report retrieval-side coverage and ranks.

Evidence groups are scoring-only. Source events are ground truth. **Broad recall** is the `retrieve()` response — do not call it the internal candidate pool. Unclassified items are not automatic precision penalties. Repeated topical evidence is intentional in customer-memory scenarios.

Hand-calculated tests live in `tests/unit/test_metrics_evidence_groups.py`.
