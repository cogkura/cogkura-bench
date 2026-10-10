# Persistent inhibition — CogKuraBench 0.3.6

**CogKuraBench:** 0.3.6  
**CogKura:** 0.17.4  
**Datasets:** `persistent_inhibition_v1` (new); `interference_v1` and `transient_interference_v1` unchanged

Query text on the new fixture includes the structured slot terms (`payments-api deployment system`, and the matching phrases for cache, database, identity, and historical tooling). That overlap is what lets both competitors clear Core's behavioural strength gate (`minimum_behavioral_strength` 0.60). Scope still comes from `entity_ids` and `predicate`. Use-source queries use `retrieval_limit` 2 so each selected event maps to one semantic memory. Episode copies of the same event are outside that cached result, which keeps use unambiguous.

Rank movement and threshold suppression were not designated. On the applied profile, Jenkins rank stayed put and `crossed_activation_threshold` stayed false. Those flags would not have been stable, so they are omitted.

## A — Induction

**Does explicit selective use create the correct persistent inhibitory traces?**

**Yes.** On both the recording and application profiles, selective GitHub Actions use persists one trace against Jenkins. Co-consumption of Redis and Memcached persists none.

| Metric | Result |
| --- | ---: |
| inhibition trace precision | 1.000 |
| inhibition trace recall | 1.000 |
| inhibition trace F1 | 1.000 |
| unexpected trace rate | 0.000 |
| unmapped traces | 0 |

## B — Scope

**Do those traces affect only future retrievals in the intended scope?**

**Yes.** Scope-isolation accuracy is 1.000. Database, identity-service, historical-tooling, and cache queries show no Jenkins penalty. The pre-induction deployment query shows no penalty. The later deployment query with `valid_at` in February still shows a penalty, because `as_of` is the current benchmark time.

| Metric | Recording only | Applied |
| --- | ---: | ---: |
| effect precision | N/A | 1.000 |
| effect recall | N/A | 1.000 |
| effect F1 | N/A | 1.000 |
| unexpected effect rate | N/A | 0.000 |
| scope isolation accuracy | N/A | 1.000 |
| history accuracy | N/A | 1.000 |
| rank effect accuracy | N/A | not designated |
| threshold accuracy | N/A | not designated |
| invariant violations | 0 | 0 |

Control `cogkura` reports effect and trace metrics as N/A. Control and recording-only retrieval identities, order, and scores match (0 mismatches). Application changes with no mapped `penalty < 0` : 0. The historical `valid_at` query (`pi-cognitive`) changes the returned set and has a mapped Jenkins penalty.

## C — Behaviour

**Do matching traces reduce accessibility without violating retrieval invariants?**

**Yes.** Every designated deployment query after the first selective use shows `penalty < 0` on Jenkins. Positive penalties, activation increases caused by inhibition, out-of-scope penalties, and future-trace visibility are all 0. Unmapped candidate and contribution counts are 0.

Jenkins remains retrievable on `pi-semantic` while carrying a penalty. Continued retrieval is not scored as an inhibition failure.

## D — Recovery

**Does repeated selective use strengthen inhibition and elapsed time weaken it?**

**Yes.** Repetition-strengthening accuracy is 1.000. Recovery-order accuracy is 1.000. Magnitudes below are absolute penalties on Jenkins for the applied profile.

| Stage | Trace/use history | Penalty magnitude |
| --- | --- | ---: |
| fresh | one selective use (`pi-immediate`) | 0.083 |
| repeated | three selective uses (`pi-repeated`) | 0.164 |
| one half-life later | same traces, +7 days (`pi-half`) | 0.096 |
| later recovery | same traces, +14 days (`pi-later`) | 0.052 |

The order is repeated > fresh, then fresh-at-repetition > half-life > later. Bench does not check a 50% formula.

## Earlier fixtures on Core 0.17.4

`interference_v1` competition metrics match the 0.3.5 / Core 0.17.1 baseline: F1 0.476, precision 0.357, recall 0.714, direction accuracy 0.600, forbidden rate 0.000.

`transient_interference_v1` with `cogkura-interference` no longer shows behavioural effects. Effect recall and F1 are 0.000, precision is 1.000, and the unexpected rate is 0.000. Invariant penalty violations are 0. On Core 0.17.1 the same frozen fixture had effect F1 0.500. The fixture was not changed. Behavioural eligibility in 0.17.4 is stricter than the pairs in that fixture, so transient interference is still not a Demo candidate.

Control `cogkura` runs, with persistent inhibition left off:

| Dataset | recall@5 |
| --- | ---: |
| mini | 1.000 |
| software_project_v1 | 1.000 |
| helios_v1 | 0.800 |
| customer_decision_context_v1 | 0.600 |

## Demo go/no-go

**Recommendation: persistent inhibition can be demonstrated on this controlled fixture. Do not enable it by default, and do not enable transient interference.**

- Trace induction precision/recall = 1.0: **pass**
- Behavioural effect precision/recall = 1.0: **pass**
- Unexpected effect rate = 0: **pass**
- Scope isolation = 1.0: **pass**
- Recovery ordering: **pass**
- Invariant violations = 0: **pass**
- Unattributed application drift: **pass** (0)
- Rank and threshold movement: **not designated**
- Transient interference on the frozen 0.3.5 fixture: **fail** (effect F1 0.000)

`InhibitionConfig.apply_to_recall=True` as a Core default remains a separate product decision.

## Reproduce

```bash
uv run python scripts/run_persistent_inhibition_benchmark.py
uv run cogkura-bench run --dataset persistent_inhibition_v1 --backend cogkura-inhibition --quiet
uv run cogkura-bench inspect pi-immediate --dataset persistent_inhibition_v1 --backend cogkura-inhibition
uv run cogkura-bench inspect pi-use-gha-1 --dataset persistent_inhibition_v1 --backend cogkura-inhibition
```
