# Metrics

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
- Abstain/leak queries (`should_abstain`) are excluded from retrieval metric averages (Recall@K, MRR, nDCG, precision, forbidden intrusion) but still contribute metamemory counts.

Each specialized metric module has hand-calculated unit tests in `tests/unit/test_specialized_metrics.py`.
