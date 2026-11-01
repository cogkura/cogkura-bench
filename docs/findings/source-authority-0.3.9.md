# Source authority — CogKuraBench 0.3.9

**CogKuraBench:** 0.3.9  
**CogKura:** 0.18.1 (`d45627e`)  
**Git commit at measurement:** `8fdd31a` plus the 0.3.9 working tree  
**Fixture:** `source_authority_v1` (27 events, 19 checkpoints, A1–A16)

Both authority profiles use `minimum_supporting_episodes=2`. `cogkura-authority-control` leaves `allow_authoritative_single_episode` off. `cogkura-authority` turns it on. Existing `cogkura`, interference, and inhibition profiles still use threshold 1.

Gold expectations are in the fixture. Bench reads durable semantic memories and `semantic_promotion_from_metadata`. It does not recompute Core's eligibility rule.

## Admission

**Can one authorised observation become semantic memory, while an ordinary one cannot?**

**Yes.** On `cogkura-authority`, admission precision and recall are 1.000 across 10 expected promotions. On `cogkura-authority-control`, precision and recall are 1.000 across 4 recurrence promotions. Unauthorized promotions, scope leaks, idempotency violations, and declared-case mismatches are 0 on both profiles.

| Profile | Expected promotions | Precision | Recall | Basis accuracy | Unauthorized |
| --- | ---: | ---: | ---: | ---: | ---: |
| authority control | 4 | 1.000 | 1.000 | 1.000 | 0 |
| authority | 10 | 1.000 | 1.000 | 1.000 | 0 |

Ordinary single observations stay episodic on both profiles, including high confidence, `status=confirmed`, and a source reference with no authority declaration. An invalid basis (`confirmed`) produces `authority_invalid_count` 1 and no memory when authority is enabled. Invalid accuracy is 1.000.

Two independent ordinary episodes still promote by recurrence on both profiles. A cardinality-one update from Jest to pytest keeps the recurring pytest claim and drops the active Jest claim.

One valid authoritative fact promotes only when authority is enabled, with support count 1, promotion support count 1, and revision count 1. A second fact in the same observation, without authority, stays episodic.

## Deferral and revisions

Competing authority-only cardinality-one claims in one batch are both deferred (`authority_deferred_count` 2). Neither becomes semantic memory. Deferral accuracy is 1.000.

A new single-support authority claim does not replace a current cardinality-one fact that already has two ordinary supports. The current claim remains, and the new claim is deferred once.

A newer source revision does not authorise the episode encoded from the older revision. That checkpoint skips a fresh episode encode after the new revision is ingested. The new claim is not promoted, and the pass reports one invalid authority. Clearing the stored revision before consolidation also fails closed: `authority_invalid` 1 and no semantic memory.

Revision-binding accuracy is 1.000. Promotion evidence maps to the declared event revision, not to whichever event last shared the source record.

Repeating consolidation leaves one memory, support count 1, and revision count 1. A later independent support raises the memory support count to 2 and keeps the original explicit-authority basis and promotion support count 1. On the control profile the same two episodes promote by recurrence instead, which is the declared control outcome.

Authority does not leak to another fact in the same observation, another subject in the tenant, or another tenant.

## Retrieval and activation

No-authority checkpoints return the same ranked evidence on both profiles, except the billing query in a tenant that also holds an authorised payments fact. That query's semantic state stays empty on both profiles. Its recall can include the payments memory only when authority is enabled, because that memory then exists.

An authority-only promotion is not required to be rank 1. The same claim produced by threshold-1 ordinary promotion and by threshold-2 authority promotion has equal confidence, importance, and recall score. Working-memory render text does not contain `explicit_source_authority` or `application_asserted`.

## Legacy regression

Control `cogkura` recall@5 is unchanged: mini 1.000, `software_project_v1` 1.000, `helios_v1` 0.800, `customer_decision_context_v1` 0.600.

`persistent_inhibition_v1` and both inhibition workloads still score trace and effect precision and recall at 1.000, with unexpected rates at 0. `transient_interference_v2` still scores precision, recall, F1, and direction at 1.000, with unexpected effects at 0. `interference_v1` competition F1 is 0.435, precision 0.312, recall 0.714, and direction accuracy 0.600, the same as the 0.17.6.1 run.

## Limitations

Correction, withdrawal, and historical supersession are not labelled. CogKura 0.18.1 does not retract a semantic memory from one new authoritative event.

The stale-revision checkpoint has to skip episode encoding after the new revision is ingested. A normal prepare would encode the new revision into its own episode and then admit it. That is a different case from "the old episode is not retroactively authorised."

Postgres parity is implemented and runs only when `COGKURA_POSTGRES_MEMORY_URL` is set. It was not set for this measurement.

## Verdict

`NO CORE CHANGE INDICATED`
