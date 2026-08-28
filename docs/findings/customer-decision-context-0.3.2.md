# Customer Decision Context — CogKuraBench 0.3.2 fixture-integrity findings

Recorded from benchmark runs on the regenerated `customer_decision_context_v1` fixture with CogKuraBench **0.3.2** and **cogkura 0.15.2**.

> **Non-comparability:** 0.3.2 changes fixture session metadata and adds one structured semantic fact on `lightweight-purchase-001`. Query text, gold groups, scoring, retrieval limit, and context budget are unchanged. Pre/post 0.3.2 CogKura scores on this dataset are **not** algorithm deltas. Compare against 0.3.0/0.3.1 only with the fixture delta in mind.

## Fixture corrections (0.3.2)

| Item | Pre-0.3.2 | Post-0.3.2 |
| --- | --- | --- |
| Session fallback for ungrouped events | `timeline-{month}` (month-wide) | `session-{event_id}` (one per event) |
| `lightweight-purchase-001` semantic fact | absent | `outerwear_weight_preference=lightweight` (`cardinality=one`) |
| Session count | 21 (month buckets + explicit clusters) | 143 |
| Largest session size | 106 (`noise-014` … `noise-119` in one month bucket) | 2 (explicit browse clusters only) |
| Multi-event sessions | month-wide noise + explicit clusters | explicit clusters only |

Session inspection (`scripts/generate_customer_decision_context_v1.py --inspect-sessions`):

```text
events: 149
sessions: 143
largest_session_size: 2
multi_event_sessions:
  hiking-session-001: 2 events -> hiking-browse-001, hiking-browse-002
  hiking-session-002: 2 events -> hiking-browse-003, hiking-browse-004
  hiking-session-003: 2 events -> hiking-browse-007, hiking-browse-008
  lightweight-session-001: 2 events -> lightweight-browse-001, lightweight-browse-002
  scotland-waterproof-session-001: 2 events -> hiking-browse-005, hiking-browse-006
  ski-session-001: 2 events -> ski-browse-001, ski-browse-002
```

Ground truth unchanged: 149 events, 1 query, 0 feedback; 5 expected groups, 2 forbidden groups; `retrieval_limit=50`, `prompt_budget_tokens=750`.

## Scenario

- **Dataset:** `customer_decision_context_v1` (149 events, 1 query)
- **Query:** `customer-waterproof-jacket`
- **Broad recall limit:** 50
- **Bounded context budget:** 750 tokens

## Backend comparison (0.3.2 fixture)

| Backend | Broad recall items | Group coverage (retrieval) | Group coverage (budget) |
| --- | ---: | ---: | ---: |
| `oracle` | 5 | 1.0 (5/5) | — |
| `token-overlap` | 50 | 0.6 (3/5) | — |
| `full-history` | 50 | 0.2 (1/5) | — |
| `cogkura` | 1 | 0.0 (0/5) | 0.0 |

### Per-group stages (0.3.2 fixture)

| Group | Oracle | token-overlap | full-history | CogKura |
| --- | --- | --- | --- | --- |
| `current_jacket_size` | hit | hit | miss | miss |
| `hiking_interest` | hit | hit | hit | miss |
| `colour_preference` | hit | miss | miss | miss |
| `lightweight_preference` | hit | hit | miss | miss |
| `northpeak_fit_issue` | hit | miss | miss | miss |

Oracle still returns 5/5 expected groups. Token-overlap and full-history scores are unchanged from the pre-fixture baseline (3/5 and 1/5 respectively).

## CogKura 0.15.2 standard replay

| Metric | Pre-0.3.2 fixture | Post-0.3.2 fixture |
| --- | ---: | ---: |
| Episodes (inventory) | 21 | 143 |
| Semantics (inventory) | 6 | 7 |
| Largest episode source-event count | 106 | 2 |
| Raw broad recall | 1 | 1 |
| Mapped broad recall | 1 | 1 |
| Raw semantic recall | 0 | 0 |
| Evidence groups (retrieval) | 0 / 5 | 0 / 5 |
| Context items | 1 | 1 |

The giant month-wide noise episode is gone. CogKura now forms one episode per ungrouped event (143 episodes). Recall still returns a single episodic item with zero semantic recall and zero evidence-group coverage.

`outerwear_weight_preference / lightweight` is present in the semantic inventory after encoding (support from `lightweight-purchase-001`) but is not returned by `Memory.recall()` under standard replay.

### Semantic inventory at query time

| Predicate | Object | Status | Active |
| --- | --- | --- | --- |
| `activity_interest` | `hiking` | active | yes |
| `activity_interest` | `skiing` | active | yes |
| `colour_preference` | `neutral` | active | yes |
| `jacket_size` | `l` | active | yes |
| `jacket_size` | `m` | active | yes |
| `outerwear_weight_preference` | `lightweight` | active | yes |
| `product_fit_issue` | `northpeak-alpine-shell:sleeves_too_short` | active | yes |

Both `jacket_size` / `m` and `jacket_size` / `l` remain active (no supersession in the fixture).

### `inspect_recall` per-semantic diagnostics

All seven stored semantics were considered (`inspect_considered=150`) but only one episodic item was returned (`inspect_returned=1`). Semantic dispositions:

| Predicate | Object | Base | Cue fit | Disposition |
| --- | --- | ---: | ---: | --- |
| `activity_interest` | `hiking` | −4.55 | 0.12 | `filtered_below_soft_floor` |
| `activity_interest` | `skiing` | −4.62 | 0.00 | `filtered_insufficient_relevance` |
| `colour_preference` | `neutral` | −4.41 | 0.00 | `filtered_insufficient_relevance` |
| `jacket_size` | `l` | −4.44 | 0.15 | `filtered_below_soft_floor` |
| `jacket_size` | `m` | −3.72 | 0.32 | `filtered_below_soft_floor` |
| `outerwear_weight_preference` | `lightweight` | −4.29 | 0.00 | `filtered_insufficient_relevance` |
| `product_fit_issue` | `northpeak-alpine-shell:sleeves_too_short` | −4.13 | 0.00 | `filtered_insufficient_relevance` |

Lexical cue-fit misses (`lightweight`, `neutral`, `northpeak`) and below-soft-floor activations (`hiking`, both jacket sizes) persist. The new lightweight semantic fact is encoded but filtered at recall time.

## Conclusion

0.3.2 fixes two fixture defects: month-wide session concatenation for noise events, and the missing structured lightweight preference on the purchase event. Harness correctness is confirmed (Oracle 5/5). CogKura still scores 0/5 on standard replay; the recall profile changed (no giant noise episode, lightweight semantic in inventory) but group coverage did not improve. Lifecycle findings from [customer-decision-context-0.3.1.md](customer-decision-context-0.3.1.md) remain relevant for incremental-prepare behaviour.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run python scripts/generate_customer_decision_context_v1.py --inspect-sessions
uv run cogkura-bench validate-dataset customer_decision_context_v1
uv run cogkura-bench run --dataset customer_decision_context_v1 --backend oracle --quiet
uv run cogkura-bench compare full-history token-overlap cogkura --dataset customer_decision_context_v1
uv run cogkura-bench inspect customer-waterproof-jacket --backend cogkura --dataset customer_decision_context_v1
uv run python scripts/diagnose_customer_decision_lifecycle.py
```
