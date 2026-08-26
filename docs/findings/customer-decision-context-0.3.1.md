# Customer Decision Context — CogKuraBench 0.3.1 lifecycle findings

Recorded from lifecycle diagnostics on commit `e9f95ddd68f9aaeea67f272eee7b9c5d44e930cd` with CogKuraBench **0.3.1** and **cogkura 0.15.0**.

## Scenario

- **Dataset:** `customer_decision_context_v1` (149 events, 1 query)
- **Query:** `customer-waterproof-jacket`
- **Broad recall limit:** 50
- **Bounded context budget:** 750 tokens

## Standard replay (`benchmark_runner_standard`)

| Metric | Value |
| --- | ---: |
| Ingest calls | 147 |
| Prepare calls | 148 |
| Maintenance calls | 148 |
| Raw broad recall | 0 |
| Mapped broad recall | 0 |
| Raw selected context | 0 |
| Mapped selected context | 0 |
| Evidence groups (retrieval) | 0 / 5 |

### Last forgetting evaluation

| evaluated | active | fading | forgotten |
| ---: | ---: | ---: | ---: |
| 27 | 0 | 27 | 0 |

### Memory inventory at query time

| episodes listed | episodes is_active | semantics listed | semantics is_active |
| ---: | ---: | ---: | ---: |
| 21 | 21 | 6 | 6 |

Memories exist in CogKura stores, but `Memory.recall()` returns zero raw results under standard replay.

## Lifecycle matrix

| Case | Prepare | Maintain | Ingest | Raw recall | Mapped recall | Group coverage |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `benchmark_runner_standard` | incremental | incremental | incremental | 0 | 0 | 0.0 |
| `incremental_prepare_no_maintenance` | incremental | never | incremental | 0 | 0 | 0.0 |
| `incremental_prepare_query_maintenance` | incremental | query-only | incremental | 0 | 0 | 0.0 |
| `incremental_ingest_query_prepare_no_maintenance` | query-only | never | incremental | 23 | 23 | 1.0 |
| `incremental_ingest_query_prepare_query_maintenance` | query-only | query-only | incremental | 23 | 23 | 1.0 |
| `bulk_ingest_query_prepare_no_maintenance` | query-only | never | bulk | 23 | 23 | 1.0 |
| `bulk_ingest_query_prepare_query_maintenance` | query-only | query-only | bulk | 23 | 23 | 1.0 |

## Conclusion

The empty benchmark recall is **not** a provenance-mapping failure (`raw_recall_count` is 0). It is **not** solely caused by repeated maintenance (disabling maintenance does not restore recall). It **is** strongly associated with repeated incremental `prepare()` across 148 lifecycle ticks.

When preparation runs only at query time (with either incremental or bulk ingest), CogKura returns 23 raw results and full mapped broad recall (5/5 evidence groups). Bulk and incremental ingest produce the same recall outcome once prepare cadence is held fixed.

Next investigation belongs in CogKura incremental episode encoding / semantic consolidation idempotency, and separately in whether CogKuraBench's per-timestamp prepare cadence represents intended application semantics.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run python scripts/diagnose_customer_decision_lifecycle.py
uv run python scripts/diagnose_customer_decision_lifecycle.py --json
uv run cogkura-bench inspect customer-waterproof-jacket --backend cogkura --dataset customer_decision_context_v1
```
