# Persistent-inhibition workloads — CogKuraBench 0.3.8

**CogKuraBench:** 0.3.8  
**CogKura:** 0.17.6.1  
**Git commit at measurement:** `b53755f` plus the 0.3.8 working tree  
**Fixtures:** `persistent_inhibition_software_v1` and `persistent_inhibition_customer_v1` (new). `persistent_inhibition_v1`, `transient_interference_v1`, `transient_interference_v2`, and `interference_v1` unchanged.

The controlled fixture stays the mechanism check. The two new datasets ask the same question across longer software and customer histories: repeated selection, another service or category, co-consumption, recovery, and a later use of the previously inhibited alternative. Uses are fixed event IDs. They are not taken from each profile's top hit.

Competing alternatives use cardinality `many`. Query text names the slot. Use-source recall is narrow enough that each selected event maps to one memory, and wide enough that the declared events stay in the cached retrieval after earlier uses have raised activation. Co-consumption source queries use limit 3. Later software source queries that would otherwise drop the selected memory use limit 4. Labelled effect queries stay at limit 2.

## Accuracy

**Do selective uses write the declared traces, and do labelled checkpoints show the declared effects?**

**Yes.** Recording and application both score trace precision, recall, and F1 at 1.000, with an unexpected trace rate of 0. Application effect precision, recall, and F1 are 1.000, with an unexpected effect rate of 0.

| Workload | Traces | Unique pairs | Repeated traces | Uses with traces |
| --- | ---: | ---: | ---: | ---: |
| software | 10 | 5 | 5 | 9 of 11 |
| customer | 9 | 4 | 5 | 7 of 8 |

The two software uses without traces are Redis+Memcached co-consumption and the notifications-service Kafka use, which has no same-slot competitor in the cached retrieval. The customer use without traces is waterproof+lightweight co-consumption. Mutual traces on those uses are 0.

`persistent_inhibition_v1` on `cogkura-inhibition` still scores trace and effect precision, recall, and F1 at 1.000, with scope, repetition, and recovery at 1.000. `transient_interference_v2` on `cogkura-interference` still scores precision, recall, F1, and direction at 1.000, with unexpected effects at 0.

## Scope

**Do traces stay inside the slot that was used?**

**Yes.** Scope-isolation accuracy is 1.000 on both workloads. Software isolation queries for PostgreSQL, identity-service deployment, and the archived catalogue show no payments-api deployment penalty. Customer isolation queries for olive jacket colour and express delivery show no footwear-colour penalty.

Future-trace visibility, positive penalties, and activation increases are 0. Recording-only versus control retrieval drift is 0. Unattributed application changes are 0. Returned-set identity changes versus recording-only are 0.

Software produced 4 scope keys (deployment, queue, observability, testing). Customer produced 3 (footwear colour, purchase priority, jacket colour).

## Frequency and growth

Repetition is the same pair written again. It is reported here and is not a failure.

| Window | Software uses / traces / unique / repeated | Customer uses / traces / unique / repeated |
| --- | --- | --- |
| early | 3 / 3 / 1 / 2 | 2 / 2 / 1 / 1 |
| middle | 7 / 6 / 3 / 3 | 5 / 5 / 2 / 3 |
| late | 11 / 10 / 5 / 5 | 8 / 9 / 4 / 5 |

The maximum traces written by one use is 2. The maximum traces accumulated on one inhibited memory is 3 in the software workload and 4 in the customer workload. Neither run reached 32 traces on a use or 64 stored traces on a candidate.

## Recovery

Penalty magnitude on the designated candidate rises after repeated selection, then falls at about one and two 7-day half-lives. The comparison is weaker-later order, not a 50% formula.

| Workload | After first use | After repetition | +7 days | +14 days |
| --- | ---: | ---: | ---: | ---: |
| software, Jenkins | 0.080 | 0.164 | 0.096 | 0.052 |
| customer, black footwear | 0.085 | 0.170 | 0.101 | 0.055 |

Repetition-strengthening accuracy and recovery-order accuracy are 1.000 on both workloads.

## Re-selection

On 20 April the previously inhibited memory is retrieved and used. Software selects Jenkins, which is rank 1, and writes a new trace against GitHub Actions (penalty −0.150). Jenkins still carries the recovering traces from the earlier GitHub Actions uses (penalty −0.036). Customer selects black footwear at rank 1 (residual penalty −0.038) and inhibits neutral footwear (penalty −0.163). Re-selection is the memory being retrievable and newly used. The residual penalty is an expected labelled effect, not an erasure of the earlier traces.

## Operations

Mean query latency, milliseconds, on the application profile:

| Window | Software | Customer |
| --- | ---: | ---: |
| early | 580 | 201 |
| middle | 546 | 169 |
| late | 611 | 224 |

Latency does not climb with the trace count in this range. No threshold suppression occurred (`crossed_activation_threshold` stayed false).

### Returned-set changes

None. Application and recording-only returned the same event IDs on every query.

### Threshold suppressions

None.

### Rank changes

All three have a mapped negative penalty.

| Query | Candidate | Rank | Penalty |
| --- | --- | --- | ---: |
| `sw-obs-now` | `sw-pay-datadog` | 4 → 6 | −0.082 |
| `sw-obs-src-2` | `sw-pay-datadog` | 4 → 6 | −0.081 |
| `sw-reselect-src` | `sw-pay-jenkins` | 2 → 3 | −0.036 |

The customer workload had no rank changes.

### Other applied penalties

These are mapped `penalty < 0` observations whose returned identity did not change. Labelled checkpoints are the persistent-inhibition queries. Direct-recall rows are source queries for a later fixed use; they are not effect-labelled, and the penalty is the trace from an earlier use in the same slot.

| Query | Candidate | Rank | Penalty | Classification |
| --- | --- | --- | ---: | --- |
| `sw-deploy-now` | `sw-pay-jenkins` | 2 → 2 | −0.080 | labelled |
| `sw-deploy-src-2` | `sw-pay-jenkins` | 2 → 2 | −0.073 | source query |
| `sw-deploy-src-3` | `sw-pay-jenkins` | 2 → 2 | −0.127 | source query |
| `sw-deploy-repeated` | `sw-pay-jenkins` | 2 → 2 | −0.164 | labelled |
| `sw-queue-now` | `sw-pay-rabbit` | 5 → 5 | −0.087 | labelled |
| `sw-queue-src-2` | `sw-pay-rabbit` | 5 → 5 | −0.087 | source query |
| `sw-test-now` | `sw-rep-jest` | 3 → 3 | −0.110 | labelled |
| `sw-deploy-half` | `sw-pay-jenkins` | 4 → 4 | −0.096 | labelled |
| `sw-deploy-later` | `sw-pay-jenkins` | 4 → 4 | −0.052 | labelled |
| `sw-reselect-now` | `sw-pay-jenkins` | 1 → 1 | −0.036 | labelled residual |
| `sw-reselect-now` | `sw-pay-gha` | 2 → 2 | −0.150 | labelled |
| `cu-colour-now` | `cu-black` | 2 → 2 | −0.085 | labelled |
| `cu-colour-src-2` | `cu-black` | 2 → 2 | −0.078 | source query |
| `cu-colour-src-3` | `cu-black` | 2 → 2 | −0.134 | source query |
| `cu-colour-repeated` | `cu-black` | 2 → 2 | −0.170 | labelled |
| `cu-budget-now` | `cu-price` | 5 → 5 | −0.087 | labelled |
| `cu-budget-src-2` | `cu-price` | 5 → 5 | −0.086 | source query |
| `cu-jacket-now` | `cu-navy` | 6 → 6 | −0.088 | labelled |
| `cu-colour-half` | `cu-black` | 4 → 4 | −0.101 | labelled |
| `cu-colour-later` | `cu-black` | 3 → 3 | −0.055 | labelled |
| `cu-reselect-src` | `cu-black` | 2 → 2 | −0.038 | source query |
| `cu-reselect-now` | `cu-black` | 1 → 1 | −0.038 | labelled residual |
| `cu-reselect-now` | `cu-neutral` | 2 → 2 | −0.163 | labelled |

## Control regression

Ordinary `cogkura` recall@5 matches the 0.3.7 run: mini 1.000, `software_project_v1` 1.000, `helios_v1` 0.800, `customer_decision_context_v1` 0.600. Workload control recall@5 is 1.000 on both new datasets.

## Verdict

`NO CORE CHANGE INDICATED`

Labelled traces, effects, scope, repetition, and recovery hold on both workloads. Co-consumption writes no mutual traces. Recording-only does not move retrieval relative to control. Every application change in this run has a mapped negative penalty. Trace caps and stored-trace caps were not approached, so this run does not justify compaction. `apply_to_recall` stays off unless a run explicitly selects `cogkura-inhibition`.

The workloads are the labelled checkpoint histories (software 24 events, 23 queries, 11 uses; customer 14 events, 18 queries, 8 uses). They are long enough to repeat selection, cross slots, recover, and re-select. They are not a saturation stress.
