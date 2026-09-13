# Competition hardening and transient interference — CogKuraBench 0.3.5

**CogKuraBench:** 0.3.5  
**CogKura:** 0.17.1  
**Datasets:** `interference_v1` (unchanged), `transient_interference_v1` (new)

## Verdict A — competition hardening

**Is 0.17.1 competition detection precise enough to drive retrieval?**

**No.** On the unchanged `interference_v1` fixture, aggregate competition metrics remain at the 0.3.4 baseline; the hardening gate (F1/direction = 1.000) is not met.

| Metric | Core 0.17.0 | Core 0.17.1 | Delta |
| --- | ---: | ---: | ---: |
| competition pair precision | 0.476 | 0.357 | −0.119 |
| competition pair recall | 0.500 | 0.714 | +0.214 |
| competition pair F1 | 0.476 | 0.476 | 0.000 |
| direction accuracy | 0.667 | 0.600 | −0.067 |
| forbidden rate | 0.000 | 0.000 | 0.000 |
| unmapped | 0 | 0 | 0 |

### 0.3.4 failure scenarios

| Scenario | 0.3.4 | 0.3.5 | Status |
| --- | --- | --- | --- |
| `interference-deploy-support` | extra pair | extra pair (F1 0.67) | unchanged |
| `interference-prod-db` | unexpected pairs | unexpected pairs (F1 0.00) | unchanged |
| `interference-deploy-subject` | unexpected pairs | unexpected pairs (F1 0.00) | unchanged |
| `interference-db-current` | unexpected pairs | unexpected pairs (F1 0.00) | unchanged |
| `interference-cotemporal` | missed | missed (recall 0.00) | unchanged |
| `interference-noncontradictory` direction | co-temporal | pairs detected (direction N/A on query) | partially fixed |

Known-good scenarios preserved: `interference-deploy-current` (F1 1.00), `interference-deploy-historical` (F1 1.00, no competition).

## Verdict B — transient interference

**When enabled, does transient interference behave safely and predictably enough to demonstrate experimentally?**

**No.** Behavioural effect F1 on `transient_interference_v1` is well below 1.0 and `unexpected_interference_rate` is high. Invariant counters are zero.

| Metric | Control (`cogkura`) | Interference enabled |
| --- | ---: | ---: |
| interference effect precision | N/A | 0.429 |
| interference effect recall | N/A | 0.600 |
| interference effect F1 | N/A | 0.500 |
| direction accuracy | N/A | 1.000 |
| unexpected interference rate | N/A | 0.571 |
| threshold suppression accuracy | N/A | 0.000 |
| rank effect accuracy | N/A | 0.000 |
| invariant violations | 0 | 0 |

### Behavioural scenario table

| Query | Expected | Direction | Effect observed | Threshold | Rank | Unexpected | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ti-proactive` | Jenkins→GHA | proactive | yes | — | — | no | pass |
| `ti-retroactive` | GHA→Jenkins | retroactive | yes | — | — | no | pass |
| `ti-db-backup` | forbidden backup | — | bleed from deploy pool | — | — | yes | fail |
| `ti-cross-service` | forbidden identity | — | deploy bleed | — | — | yes | fail |
| `ti-rank-move` | rank worsening | proactive | wrong candidate pool | no | no | yes | fail |
| `ti-threshold-suppress` | suppression | proactive | not observed | no | — | no | fail |
| `ti-historical` | no future effect | — | none | — | — | no | pass |
| `ti-support-lineage` | Jenkins→GHA | proactive | yes | — | — | no | pass |
| `ti-cotemporal` | no penalty | co_temporal | none | — | — | no | pass |
| `ti-semantic-supersede` | no mysql effect | — | deploy bleed | — | — | yes | fail |

Shared-memory bleed: deployment competition appears in the inspect pool for unrelated queries (database, semantic), inflating unexpected interference.

## Demo go/no-go

**Recommendation: do not enable transient interference in the Demo.**

- Hardening gate: **fail**
- Behavioural effect F1 = 1.0: **fail** (0.500)
- Unexpected interference rate = 0.0: **fail** (0.571)
- Invariant violations = 0: **pass**
- Unexplained control/enabled retrieval drift on regression datasets: not blocking in this run (observational helper reports per-dataset deltas)

Default-on `apply_interference` in Core remains a separate product decision.

## Reproduce

```bash
uv sync --extra cogkura --dev --locked
uv run cogkura-bench validate-dataset interference_v1
uv run cogkura-bench run --dataset interference_v1 --backend cogkura --quiet
uv run cogkura-bench validate-dataset transient_interference_v1
uv run cogkura-bench run --dataset transient_interference_v1 --backend cogkura --quiet
uv run cogkura-bench run --dataset transient_interference_v1 --backend cogkura-interference --quiet
uv run python scripts/run_transient_interference_benchmark.py
```
