# Metrics

## Retrieval (0.1.0)

- Recall@K (1, 3, 5, 10)
- Precision@K
- Mean Reciprocal Rank (MRR)
- nDCG (expected=2, acceptable=1, else=0)
- Forbidden intrusion rate

## Cognitive capabilities (future phases)

- Temporal current vs historical accuracy
- Knowledge update: stale intrusion, current-state ranking
- Forgetting: stale suppression, long-term retention, noise intrusion
- Working memory: evidence coverage, context precision, token efficiency
- Learning: delta Recall@K, delta MRR
- Metamemory: missing-knowledge and conflict detection
- Efficiency: latency, token counts

Each metric has hand-calculated unit tests.
