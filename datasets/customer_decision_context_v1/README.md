# Customer Decision Context v1

Independently authored benchmark scenario for bounded working-memory diagnostics in a customer-memory / outdoor-retail domain.

> This scenario is independently authored for CogKuraBench and has no data dependency on any demo application.

## Purpose

The scenario models one fictional outdoor-retail customer with approximately 17 months of history. It reproduces a working-memory failure pattern where repeated hiking evidence can crowd out distinct decision-relevant customer knowledge under a bounded context budget.

The benchmark answers:

> When bounded working memory misses important customer knowledge, was that knowledge absent from broad recall or present in recall but dropped during working-memory selection?

## Customer history

The customer has:

- Repeated hiking browsing, purchases, and positive outcomes
- Lightweight outerwear interest (browse-only plus strong purchase/outcome evidence)
- A NorthPeak Alpine Shell fit issue (return and support follow-up)
- Historical jacket size L superseded by current size M
- Neutral colour preference (black, navy, grey)
- A short stale skiing phase
- Unrelated noise (backpacks, trousers, accessories, order questions)

Repeated hiking evidence is intentional: it creates realistic competition for working-memory capacity.

## Expected concepts

Five expected evidence groups:

| Group | Strong evidence |
| --- | --- |
| `current_jacket_size` | Current size M only (`size-current-m-001`) |
| `hiking_interest` | Semantic fact, purchase, positive outcomes |
| `colour_preference` | Explicit neutral colour preference |
| `lightweight_preference` | Purchase (structured semantic fact) and positive outcome (episodic support) |
| `northpeak_fit_issue` | Return and support follow-up only (not browsing or purchase alone) |

Two forbidden evidence groups:

| Group | Evidence |
| --- | --- |
| `stale_jacket_size` | Historical size L |
| `old_skiing_interest` | Complete skiing phase |

Browse-only lightweight activity does not satisfy the lightweight preference group. Product browsing or purchase alone does not satisfy the NorthPeak fit issue group. Skiing is stale history, not a contradictory current interest.

## Session semantics

Explicit `session_id` values represent coherent customer interactions (for example `hiking-session-001`, `lightweight-session-001`). Events without an explicit session receive a deterministic standalone session (`session-{event_id}`). Synthetic month is timeline organisation only; it is **not** a session boundary.

## Lightweight semantic contract

`lightweight-purchase-001` carries the structured semantic assertion `outerwear_weight_preference = lightweight` (`cardinality = one`). `lightweight-positive-001` provides additional episodic evidence for the same concept without duplicating the structured fact. Browse-only lightweight events remain weaker evidence only.

## Product catalogue relationships

Product-bearing events include source catalogue structure (PIM-style `is_a` edges and category entity IDs). This is **source knowledge**, independent of query text and gold evidence groups. The lightweight preference remains a customer semantic fact, not an ontology edge. Generator `--inspect-catalogue` reports attachment counts; `--without-relationships` emits 0.3.2-shaped events for causality checks.

## Primary query

- **ID:** `customer-waterproof-jacket`
- **Capability:** `working_memory`
- **Retrieval limit:** 50 (broad recall diagnostic)
- **Prompt budget:** 750 tokens (bounded context selection)
- **Timestamp:** After current size M, lightweight evidence, NorthPeak fit issue, and skiing phase

## Usage

```bash
uv run cogkura-bench validate-dataset customer_decision_context_v1
uv run cogkura-bench run --dataset customer_decision_context_v1 --backend oracle --quiet
uv run cogkura-bench compare full-history token-overlap cogkura --dataset customer_decision_context_v1
uv run cogkura-bench inspect customer-waterproof-jacket --backend cogkura --dataset customer_decision_context_v1
```

## Dataset stats

- **Events:** 149
- **Queries:** 1
- **Feedback:** 0
