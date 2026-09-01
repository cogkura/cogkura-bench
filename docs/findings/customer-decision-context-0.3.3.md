# Customer Decision Context — CogKuraBench 0.3.3 structured relationship fixture

Recorded from benchmark runs on `customer_decision_context_v1` with CogKuraBench **0.3.3** and **cogkura 0.15.8**.

> **Non-comparability:** 0.3.3 adds catalogue `is_a` relationships and category entity IDs on product-bearing events only. Query text, gold groups, scoring, retrieval limit, and context budget are unchanged. Pre/post 0.3.3 CogKura scores are **not** algorithm deltas unless compared against the same fixture. Use the A/B/C table below to separate core-version and fixture-data effects.

## Fixture additions (0.3.3)

| Item | Pre-0.3.3 | Post-0.3.3 |
| --- | --- | --- |
| Catalogue relationships | absent | four `is_a` edges (`provenance=catalog`) |
| Category entities on product events | product IDs only | `waterproof-shell`, `jacket`, `outerwear` where applicable |
| `lightweight-purchase-001` entities | `featherlite-packable-shell` | also `jacket`, `outerwear` |
| NorthPeak product events | `northpeak-alpine-shell` | also `waterproof-shell`, `jacket` + three `is_a` edges |
| Event count | 149 | 149 (unchanged) |

Catalogue design (source/PIM structure, not gold):

```text
northpeak-alpine-shell  --is_a-->  waterproof-shell  --is_a-->  jacket  --is_a-->  outerwear
featherlite-packable-shell  --is_a-->  jacket
```

Catalogue inspection (`scripts/generate_customer_decision_context_v1.py --inspect-catalogue`):

```text
catalogue_entities: 5
catalogue_relationships: 4
attached_relationships: 14
relationship_type_counts:
  is_a: 14
catalogue_entities_on_events: 5
```

Ground truth unchanged: 149 events, 1 query, 0 feedback; 5 expected groups, 2 forbidden groups; `retrieval_limit=50`, `prompt_budget_tokens=750`.

## Attribution (mandatory)

| Condition | CogKura core | Bench fixture | Groups (budget) | Recall@5 | MRR | Broad recall | Context items | NorthPeak disposition | Relationship paths used |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| A | 0.15.7 | 0.3.2 (no relationships) | 4 / 5 | 0.6 | — | 9 | 8 | `filtered_insufficient_relevance` | 0 |
| B | 0.15.8 | 0.3.2 (no relationships) | 4 / 5 | 0.6 | — | 9 | 8 | `filtered_insufficient_relevance` | 0 |
| C | 0.15.8 | 0.3.3 (catalogue relationships) | **5 / 5** | 0.6 | 0.5 | 11 | 8 | `returned` (`structured_relation`, 2-hop `is_a` path via `jacket`) | 2 |

Condition A from [0.3.2 findings](customer-decision-context-0.3.2.md) progression notes (CogKura 0.15.7 pin). Condition B from the 0.15.8 pin on the 0.3.2 fixture before relationship regeneration. Condition C from this release.

## Scenario

- **Dataset:** `customer_decision_context_v1` (149 events, 1 query)
- **Query:** `customer-waterproof-jacket`
- **Broad recall limit:** 50
- **Bounded context budget:** 750 tokens

## CogKura 0.15.8 condition C replay

| Metric | Condition B (0.3.2 fixture) | Condition C (0.3.3 fixture) |
| --- | ---: | ---: |
| Relationships ingested | 0 | 14 |
| Raw broad recall | 9 | 11 |
| Mapped broad recall | 9 | 11 |
| Evidence groups (retrieval) | 4 / 5 | 5 / 5 |
| Evidence groups (budget) | 4 / 5 | 5 / 5 |
| Context tokens | 124 | 124 |
| Retrieval latency (ms) | ~290 | ~291 |

### NorthPeak fit issue (condition C)

`product_fit_issue / northpeak-alpine-shell:sleeves_too_short` is returned in broad recall and selected into bounded context. `inspect_recall` shows:

- **Disposition:** `returned`
- **Relevance tier:** `structured_relation`
- **Association path:** `hop_kind=relationship`, `hop_count=2`, seed entity `jacket`, bridge `northpeak-alpine-shell`
- **Relationship edges:** reverse `is_a` hops through `waterproof-shell` and `northpeak-alpine-shell` (catalog provenance)

The episodic return event (`northpeak-return-001`) is also returned and selected.

### Lightweight preference (condition C)

`outerwear_weight_preference / lightweight` is returned with `relevance_tier=structured_relation` and a 1-hop relationship path via `featherlite-packable-shell is_a jacket`.

## Conclusion

0.3.3 adds realistic product-catalogue structure as source data mapped through CogKura 0.15.8 `metadata["relationships"]`. Harness correctness is confirmed (Oracle 5/5). On condition C, CogKura reaches **5/5** expected groups at both retrieval and budget; the NorthPeak miss under conditions A/B is attributable to missing fixture relationship data on 0.15.8, not a core-only delta. Relationship inspection diagnostics are persisted in `backend_metadata` for attribution without affecting scores.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run python scripts/generate_customer_decision_context_v1.py --inspect-catalogue
uv run cogkura-bench validate-dataset customer_decision_context_v1
uv run cogkura-bench run --dataset customer_decision_context_v1 --backend oracle --quiet
uv run cogkura-bench compare full-history token-overlap cogkura --dataset customer_decision_context_v1
uv run cogkura-bench inspect customer-waterproof-jacket --backend cogkura --dataset customer_decision_context_v1
```

For condition B causality, regenerate with `--without-relationships` into a scratch directory or use the generator flag in integration tests.
