# Authoritative corrections — CogKuraBench 0.3.10

**CogKuraBench:** 0.3.10  
**CogKura:** 0.18.2 (`1a8bc04`)  
**Git commit at measurement:** `366ae5f` plus the 0.3.10 working tree  
**Fixture:** `authoritative_corrections_v1` (35 events, 26 checkpoints, C01–C23 in the dataset; C24 is the conditional Postgres comparison)

`cogkura-correction-control` and `cogkura-correction` both use recurrence threshold 2 and source authority. Only `cogkura-correction` sets `SemanticCorrectionConfig(enabled=True)`. Existing profiles are unchanged.

Gold expectations are in the fixture. A correction or withdrawal names its predecessor by subject, predicate, and object. The adapter resolves the public revision key at ingest. Bench reads `list_semantic_memories` at `valid_at`, or at `as_of` when `valid_at` is omitted, plus recall and rendered context. It does not recompute Core's correction rule.

## Semantic state

**Can an authorised correction replace the current value and leave the previous value historically available?**

**Yes, when corrections are enabled.** Transition precision and recall are 1.000 on both profiles. State accuracy, retrieval accuracy, and revision-provenance accuracy are 1.000 on both. On the enabled profile, temporal-boundary accuracy and conflict-deferral accuracy are 1.000. The control profile omits those two rates because it does not execute a correction or a deferred conflict.

| Profile | Precision | Recall | State accuracy | Unauthorized | Mismatches |
| --- | ---: | ---: | ---: | ---: | ---: |
| correction control | 1.000 | 1.000 | 1.000 | 0 | 0 |
| correction | 1.000 | 1.000 | 1.000 | 0 | 0 |

On the enabled profile the migration strategy moves from `application_startup` to `deployment_pipeline` at the effective instant, not when the correction is first observed. Before that instant, including a later `as_of` with an earlier `valid_at`, the predecessor remains the value. At and after the effective instant the successor is current, with `valid_from` at the boundary and relation `supersedes`. The control profile keeps `application_startup`.

A withdrawal then leaves no current strategy. A historical query before the withdrawal still returns `deployment_pipeline`. The control profile still has the original value, because it does not execute the withdrawal.

Ordinary single observations stay unpromoted. Two ordinary episodes still promote by recurrence. A correction without authority, an unknown predecessor, a wrong slot, a correction that is not encoded into an episode, two incompatible corrections, and a correction plus withdrawal of the same predecessor leave the current value in place. Re-adoption after withdrawal does not restore a current value. Repeating consolidation does not add a revision. A source edit without a withdrawal does not retract the assertion.

## Retrieval

Retrieval accuracy on the declared recall checks is 1.000. Incorrect current states, incorrect historical states, knowledge-time leaks, stale-context leaks, and false suppressions are 0.

A current query after withdrawal does not render `deployment_pipeline`. The shared-episode case still renders and retrieves PostgreSQL after only the migration strategy is withdrawn. An unrelated release-channel fact that shares the words startup and pipeline stays available. A historical query still retrieves the original migration evidence.

## PostgreSQL parity

**NOT EXECUTED.** `COGKURA_POSTGRES_MEMORY_URL` was not set. The comparison is implemented and skipped unless that URL is present.

## Legacy regression

`source_authority_v1` still scores admission precision, recall, and basis accuracy at 1.000 on both authority profiles: 10 expected promotions when authority is on, and 4 recurrence promotions on the control. Unauthorized promotions, scope leaks, idempotency violations, and declared mismatches stay 0.

Control recall@5 remains mini 1.000, `software_project_v1` 1.000, `helios_v1` 0.800, and `customer_decision_context_v1` 0.600. Persistent-inhibition trace and effect precision and recall remain 1.000. `transient_interference_v2` precision, recall, F1, and direction remain 1.000. `interference_v1` competition F1 remains 0.435.

## Limitations

Re-adoption after withdrawal is deferred, as the 0.18.2 contract specifies. The new episode text can still appear in rendered context; the semantic claim does not become current again.

Postgres parity was not executed in this measurement.

## Verdict

`NO CORE CHANGE INDICATED`
