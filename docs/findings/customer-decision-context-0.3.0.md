# Customer Decision Context — CogKuraBench 0.3.0 findings

Recorded from an actual benchmark run on commit `935fb8d` with CogKuraBench **0.3.0** and **cogkura 0.15.0**.

## Scenario

- **Dataset:** `customer_decision_context_v1` (149 events, 1 query)
- **Query:** `customer-waterproof-jacket`
- **Broad recall limit:** 50
- **Bounded context budget:** 750 tokens
- **Expected groups:** 5 (`current_jacket_size`, `hiking_interest`, `colour_preference`, `lightweight_preference`, `northpeak_fit_issue`)
- **Forbidden groups:** 2 (`stale_jacket_size`, `old_skiing_interest`)

## CogKura results

| Metric | Value |
| --- | ---: |
| Broad recall items | 0 |
| Context items | 0 |
| Context tokens | 0 |
| `evidence_group_coverage_at_retrieval` | 0.0 |
| `evidence_group_coverage_at_budget` | 0.0 |
| Forbidden groups in context | 0 / 2 |

### Per-group stages

| Group | Broad recall | Context | Stage |
| --- | --- | --- | --- |
| Current jacket size | no | no | `retrieval_miss` |
| Established hiking interest | no | no | `retrieval_miss` |
| Neutral colour preference | no | no | `retrieval_miss` |
| Prefers lightweight outerwear | no | no | `retrieval_miss` |
| Previous NorthPeak sleeve-fit issue | no | no | `retrieval_miss` |

Forbidden groups `stale_jacket_size` and `old_skiing_interest` were absent from both broad recall and bounded context.

### Interpretation

With incremental ingest and a single end-of-timeline query, CogKura returned no provenance-mapped recall items for this scenario. All five expected concept groups classify as **retrieval miss** — the harness cannot distinguish retrieval failure from selection drop because bounded context is empty.

Bulk ingest of the same event set followed by one `prepare` and `recall` call does return items in isolation. Helios-style interleaved queries also restore recall. This release documents the behaviour; it does not change CogKura algorithms or add query-specific adapter ranking.

## Baseline comparison (same dataset)

| Backend | Broad recall items | Group coverage (retrieval) | Context evaluated |
| --- | ---: | ---: | --- |
| `oracle` | 5 | 1.0 | no (`select_context` unsupported) |
| `token-overlap` | 50 | 0.6 | no |
| `full-history` | 50 | 0.2 | no |
| `cogkura` | 0 | 0.0 | yes (empty) |

Oracle returns the first event ID from each expected group (5/5 broad recall). Token-overlap retrieves hiking, lightweight, and current-size groups but misses colour preference and NorthPeak fit issue under lexical overlap. Full-history at `retrieval_limit=50` retains only the oldest visible events, so most decision-relevant late evidence is outside the window.

## Harness notes

- Evidence groups are **scoring-only** concept clusters; flat `expected_evidence_ids` still drive Recall@K and working-memory coverage.
- **Broad recall** is the `retrieve()` response (`Memory.recall` in CogKura). Do not call it the internal candidate pool.
- **Unclassified** context items are provenance-labelled items that match neither expected nor forbidden groups. They are not automatic precision penalties.
- Repeated hiking browse events are intentional competition for bounded working memory.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run cogkura-bench validate-dataset customer_decision_context_v1
uv run cogkura-bench run --dataset customer_decision_context_v1 --backend cogkura --quiet
uv run cogkura-bench inspect customer-waterproof-jacket --backend cogkura --dataset customer_decision_context_v1
```
