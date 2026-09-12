# Interference competition diagnostics — CogKuraBench 0.3.4

**CogKuraBench:** 0.3.4  
**CogKura:** 0.17.0  
**Dataset:** `interference_v1` (`interference-v1`)  
**Git commit:** `86545ecc1f086dcdef3cc1a11c4197bc5f988efa` (dirty working tree during measurement)

> **Non-comparability:** This release adds competition diagnostic scoring only. Existing dataset gold evidence and retrieval metric semantics are unchanged. Interference metrics are not comparable to pre-0.3.4 runs.

## Harness delta

| Area | Pre-0.3.4 | 0.3.4 |
| --- | --- | --- |
| Capability | — | `interference` |
| Query fields | evidence IDs / groups | optional `expected_competitions`, `forbidden_competitions` |
| Retrieval response | items + metadata | optional `competition_observations` |
| CogKura adapter | 0.16.x | 0.17.x `inspect_recall` competition mapping |
| Dataset | — | `interference_v1` (16 events, 8 queries) |

## Retrieval regression (CogKura 0.17.0 vs 0.16.4 baseline)

Mini `cogkura` ranked evidence IDs match the captured 0.16.4 fingerprints in `tests/golden/cogkura_0164_retrieval_parity.json` for all parity-tracked queries. Existing dataset oracle/token-overlap goldens are unchanged.

## `interference_v1` — CogKura 0.17.0 aggregate

| Metric | Value |
| --- | --- |
| `competition_pair_f1` | 0.476 |
| `competition_pair_precision` | 0.476 |
| `competition_pair_recall` | 0.500 |
| `competition_direction_accuracy` | 0.667 |
| `forbidden_competition_rate` | 0.000 |
| `competition_pairs_unmapped` | 0 (all queries) |

## Per-query highlights

| Query | Pair F1 | Notes |
| --- | ---: | --- |
| `interference-deploy-current` | 1.00 | Both directed Jenkins↔GHA pairs detected with correct direction |
| `interference-deploy-support` | 0.67 | Expected group-vs-Jenkins hit; extra observed pair lowers precision |
| `interference-noncontradictory` | 1.00 | Pairs detected; direction accuracy 0.00 (both classified co-temporal in Core) |
| `interference-prod-db` | 0.00 | Two unexpected competition pairs; forbidden backup pair correctly absent |
| `interference-deploy-subject` | 0.00 | Unexpected pairs; cross-service forbidden pair correctly absent |
| `interference-db-current` | 0.00 | Four unexpected pairs; superseded MySQL correctly not required as competition |
| `interference-cotemporal` | 0.00 | No competition observations emitted for staging/production pair |
| `interference-deploy-historical` | 1.00 | No competition observations; future GHA correctly isolated |

## False-positive controls

Forbidden competition declarations did not match observed pairs (`forbidden_competition_rate = 0.0`). However, **unexpected** observed pairs on `interference-prod-db`, `interference-deploy-subject`, and `interference-db-current` reduce precision. Entity-overlap negative controls are not yet clean at the competition layer.

## Conclusion

Competition detection is **not** yet precise enough to justify CogKura 0.17.1 affecting retrieval activation. Canonical deployment competition (scenario A) and repeated-support grouping (scenario F partial) work, but false competition on related-but-distinct memories and missed co-temporal detection block a confident go-ahead. Forbidden controls pass; precision on unexpected pairs does not.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run cogkura-bench validate-dataset interference_v1
uv run cogkura-bench run --dataset interference_v1 --backend cogkura
uv run cogkura-bench inspect interference-deploy-current --dataset interference_v1 --backend cogkura
uv run cogkura-bench run --dataset mini --backend cogkura --quiet
uv run pytest tests/golden/test_cogkura_retrieval_parity.py
```
