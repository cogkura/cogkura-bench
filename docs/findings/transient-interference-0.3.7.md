# Transient interference v2 — CogKuraBench 0.3.7

**CogKuraBench:** 0.3.7  
**CogKura:** 0.17.6  
**Git commit at measurement:** `f329d35` plus the 0.3.7 working tree  
**Fixtures:** `transient_interference_v2` (new), `transient_interference_v1` (frozen), `interference_v1` (frozen), `persistent_inhibition_v1` (frozen)  
**Profiles:** `cogkura`, `cogkura-interference`, `cogkura-inhibition`

```text
Transient interference v2 gate: PASS
Proactive reachable: yes
Retroactive reachable: yes
Unexpected effects: 0
Persistent-inhibition regression: fail on trace precision, pass on behavioural effects
Ordinary retrieval regression: pass
```

`transient_interference_v1` is the historical contract from Core 0.17.1. It stays frozen. `transient_interference_v2` is the current behavioural contract: candidate-directed effects, both directions allowed on one query, and a gate that requires recall and F1, not precision alone. v2 does not replace or invalidate v1.

Rank movement and threshold suppression were not designated. On the applied profile, deployment ranks did not change. One multi-competitor candidate crossed the activation threshold in inspection, and that was not stable enough to make a release gate.

## A — Reachability

**Do proactive and retroactive effects occur under the modern eligibility contract?**

**Yes.** On `ti2-pair`, GitHub Actions receives a proactive contribution from Jenkins, and Jenkins receives a retroactive contribution from GitHub Actions. Direction accuracy is 1.000.

| Scenario | Direction | Expected effect | Observed | Pressure | Penalty | Result |
| --- | --- | --- | --- | ---: | ---: | --- |
| temporal pair / newer candidate | proactive | yes | yes | 0.105 | -0.059 | pass |
| temporal pair / older candidate | retroactive | yes | yes | 0.242 | -0.107 | pass |
| same subject / other predicate | — | no | none | 0 | 0 | pass |
| cross-service | — | no | none | 0 | 0 | pass |
| co-temporal | — | no | none | 0 | 0 | pass |
| historical future competitor | — | no | none | 0 | 0 | pass |

Eligibility is symmetric, so a valid reverse contribution is expected rather than forbidden. One-sided queries would have counted that reverse effect as unexpected.

| Metric | Control | Interference enabled |
| --- | ---: | ---: |
| effect precision | N/A | 1.000 |
| effect recall | N/A | 1.000 |
| effect F1 | N/A | 1.000 |
| direction accuracy | N/A | 1.000 |
| unexpected effect rate | N/A | 0.000 |
| invariant violations | 0 | 0 |

`unattributed_transient_retrieval_change_count` is 0.

## B — Precision

**Do negative controls remain unaffected?**

**Yes.** Database, identity-service, shared-technology, broad-subject, co-temporal, same-lineage, superseded-semantic, and historical queries have no active transient contribution. Reinforcing the backup memory does not make it a deployment competitor.

## C — Behaviour

**Do accessibility and aggregation act as intended?**

**Yes.**

| Comparison | Value |
| --- | ---: |
| GitHub Actions penalty, one competitor (`ti2-pair`) | 0.059 |
| GitHub Actions penalty, two competitors (`ti2-multi`) | 0.147 |
| Jenkins pressure before explicit use | 0.184 |
| Jenkins pressure after explicit use | 0.608 |

The extra competitor increases the bounded penalty. Explicit use of Jenkins, with persistent inhibition off, raises that competitor's transient pressure. The slot relationship does not change.

| Query | Control top | Interference top | Penalty | Attributed |
| --- | --- | --- | ---: | --- |
| `ti2-pair` | gha, jenkins | gha, jenkins | -0.059 | yes |
| `ti2-multi` | circle, gha | circle, gha | -0.147 | yes |
| `ti2-after` | jenkins, circle | jenkins, circle | -0.217 | yes |
| `ti2-db` | postgres, circle | postgres, circle | 0 | yes |
| `ti2-historical` | jenkins, backup | jenkins, backup | 0 | yes |

## D — Regression

**Did the 0.17.6 evidence correction damage persistent inhibition or ordinary retrieval?**

Behavioural persistent inhibition still passes: effect precision and recall 1.000, unexpected effect rate 0.000, scope isolation 1.000, repetition and recovery 1.000, invariant violations 0.

Trace induction precision is **0.600** (recall 1.000). `pi-use-cache`, which selects both cache memories, now persists Redis↔Memcached traces. On Core 0.17.4 that co-consumption use persisted none. The fixture was not changed. Trace precision no longer meets the 0.3.6 gate. Application of inhibition to the deployment scenarios is unchanged.

Ordinary `cogkura` recall@5 matches the 0.3.6 control run: mini 1.000, Atlas 1.000, Helios 0.800, customer decision context 0.600.

### Frozen v1 on three Core versions

| Metric | Core 0.17.1 | Core 0.17.4 | Core 0.17.6 |
| --- | ---: | ---: | ---: |
| transient effect precision | 0.429 | 1.000 | 0.214 |
| transient effect recall | 0.600 | 0.000 | 0.600 |
| transient effect F1 | 0.500 | 0.000 | 0.316 |
| unexpected transient rate | 0.571 | 0.000 | 0.786 |

v1 is not a release gate. Some expected effects are reachable again, and more of the historical forbidden pairs are active than on 0.17.1. That fixture's query-level direction bans do not match the candidate-directed contract.

`interference_v1` competition F1 is 0.435 (0.476 on 0.17.4). Diagnostic competition stays broader than behavioural interference and is not required to improve.

## Verdict

Transient interference on `transient_interference_v2` is reachable, precise, and bounded under CogKura 0.17.6. `apply_interference=True` remains off by default. The next evidence question is the co-consumption trace regression in persistent inhibition, not another transient-interference redesign.

## Reproduce

```bash
uv run python scripts/run_transient_interference_v2_benchmark.py
uv run cogkura-bench run --dataset transient_interference_v2 --backend cogkura-interference --quiet
uv run cogkura-bench inspect ti2-pair --dataset transient_interference_v2 --backend cogkura-interference
```
