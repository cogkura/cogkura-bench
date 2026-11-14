# Source-aware metamemory — CogKuraBench 0.3.11 candidate

**Verdict: CORE REVIEW REQUIRED. The release is not fully validated.**

**Date:** 14 November 2026.  
**Core:** 0.18.3, `9ab2241ad600ed766b9c6487440e7495fe68254c`.  
**Bench implementation:** `63f7d73`, followed by inspection output/reset checks in `39bde91`.  
**PostgreSQL:** local disposable PostgreSQL 14.18 (Homebrew).

All declared source-assessment cases pass on both backends. Frozen results and
paired diagnostics agree with the controlled baseline. The stricter backend
comparison fails one capped-evidence attribution case. That failed release gate
is retained; passing contract tests do not waive it. No Core, Demo or Agent files
were modified, no earlier fixture gold was changed, and no release was published.

## New source assessment

`source_aware_metamemory_v1` has 23 events and 26 checkpoints. Both source profiles
use threshold 2, explicit authority, corrections and source inspection. Only
`cogkura-source` enables typed pass diagnostics. Source observations are neutral;
gold never enters the adapter request and backend metadata cannot supply answers.

| Measurement | Result |
| --- | --- |
| Source state, conflict, reason, revision attribution, completeness, temporal and uncertainty checks | **1.000** on both profiles |
| Declared checks with diagnostics enabled | **191 / 191 matched** |
| Conflict precision / recall | **1.000 / 1.000** |
| Declared mismatches | **0** |
| False-certainty contract violations | **0** |
| Declared future-evidence leaks | **0** |
| Unsupported Oracle source capability | **N/A** |
| Strict PostgreSQL report parity | **FAIL: 1 of 26 checkpoints differs** |

Coverage includes unknown/known/contested/withdrawn/historical-only/indeterminate
state, empty recall with stored knowledge, conflict evidence outside the recall
limit, locator absence, revision-aware attribution, episodic relation N/A,
cardinality-many coexistence, negative assertions, source edits, scopes, future
effective corrections, historical reads, withdrawals, replay and deferrals.
Supplemental tests cover missing exact revisions, unavailable inspection,
legacy empty snapshots, context currentness, report truncation, and read-only
inspection. These are contract checks, not factual-truth or trust measurements.

First-pass checkpoints coincide with ingest/processing time. A later replay is a
new pass: its actual branch can be `target_not_unique_current`, including when
withdrawal remains durable. The adapter does not fabricate a re-admission outcome
or an unresolved-decision ledger. Decisions without a slot key are attributed
through their public target/result revision keys. Historical inspection hides
later pass diagnostics. Complete historical transition attribution is not assumed.

## Frozen results and non-interference

Unchanged Core `1a8bc04` source was imported in a separate process to capture the
0.18.2 baseline. An initial ordinary random-ID comparison exposed pre-existing
variability: UUID-dependent ordering affects episode prose, provenance order and
some equal-score ranks. That comparison is not called exact parity.

For the independent comparison, both versions used the same seeded standard-library
UUID allocator before Core import, `PYTHONHASHSEED=0`, identical event streams,
clocks, profiles and explicit uses. The harness changes storage identity
allocation only; it does not patch Core algorithms, alter thresholds or normalise
away ranked retrieval differences. This controls the observed source of variability.
It does **not** establish deterministic outputs across arbitrary UUID allocations.

All **393 query signatures across 22 dataset/profile runs**, **46 explicit uses**,
and non-latency metrics match exactly. Signatures include evidence/order, text,
scores, activation components, neutral competition/interference/inhibition
observations, semantic state/provenance, old counters and correction context prose.
Fingerprints are retained in `tests/golden/cogkura_0182_frozen.json`.

Diagnostics-off/on comparisons also match for all 22 earlier runs and the new
source fixture: **419 paired query outcomes**, with zero cognitive/output or
storage-allocation differences. Source report checks differ only as specified by
the advertised diagnostics capability. Read-only tests compare public semantic
history, episodes, recall and old counters before/after repeated inspection.

Authority and correction precision/recall/state accuracy stay **1.000** on their
frozen fixtures. Transient v2 precision/recall/F1/direction and persistent trace/
effect precision/recall stay **1.000**. Competition F1 stays **0.4347826087** on
`interference_v1`. Previously measured control recall values (mini 1.000, software
1.000, Helios 0.800, customer 0.600 in the prior findings) are not retuned or
redefined here; the stronger per-case comparison retains the underlying outputs.

## PostgreSQL execution and the remaining gate

PostgreSQL was **EXECUTED**, with migrations applied and fixture tenants isolated.
Adoption, replacement, withdrawal, replay, effective boundaries, knowledge-time
projection and the supported source-coverage contracts pass. The earlier 0.3.10
unexecuted database gap is not carried forward as an implied success or silently
left skipped.

Strict comparison preserves event identities, even under evidence truncation.
At `sm-evidence-cap`, `max_evidence=1` on two contested assertions with four
source references returns:

| Backend | Cited event in the strict controlled run |
| --- | --- |
| In memory | `sm-conflict-startup-0` |
| PostgreSQL | `sm-conflict-startup-1` |

Both report contested state, four referenced occurrences, one returned reference,
truncation, incomplete exact-revision/relation coverage, unknown independence and
unavailable decision history. The returned source is valid in both runs. The
other 25 neutral reports agree; this case differs in `event_ids` and its revision
source attribution. The declared coverage gold intentionally does not assert
which eligible reference a cap chooses. The strict validator checks that separate
promise and exits **1**, with `release_gate_passed=false`.

Inspection of unchanged Core code explains the difference: semantic evidence is
ordered by sequence number, observation UUID and revision in
`provenance._memory_evidence`; source assessment then slices that population by
the evidence cap. Equal sequence numbers can therefore select different source
records when backend storage IDs differ. Even a shared UUID allocator produces
different IDs because the backends allocate additional internal records.

**Architectural decision required:** confirm whether bounded source selection must
be stable across equivalent backends/storage IDs. The approved strict parity
criterion has not been waived here. If required, Core needs an independently
reviewed ordering fix using stable source identities. If a weaker prefix contract
is intended, explicitly approve and document that exception before declaring
release validation complete. Bench must not hide it by fetching beyond the
requested cap or modifying expected evidence to suit a backend.

## Required gates

The full Python matrix installs the locked environment with all extras, then runs
Ruff, format checking, MyPy, pytest with PostgreSQL, and every dataset/profile CLI
step in CI. The new CI service ensures database tests execute on 3.11–3.13.

| Runtime | Locked sync / Ruff / format / MyPy | Full pytest with PostgreSQL | Skipped tests | CI dataset/profile CLI steps |
| --- | --- | --- | --- | --- |
| Python 3.11.15 | PASS | **289 passed** | **0** | PASS |
| Python 3.12.8 | PASS | **289 passed** | **0** | PASS |
| Python 3.13.0 | PASS | **289 passed** | **0** | PASS |

The strict release validator is separate from pytest's coverage contract test.
That test verifies valid bounded populations and exact agreement for the other
cases; it explicitly does not waive the capped-identity mismatch. Green ordinary
CI gates therefore do not mean that the strict release gate passed.

Reproduce with the commands in [source metamemory](../source-metamemory.md).
The checked-in [validation summary](data/source-metamemory-0.3.11-validation.json)
retains actual mismatch evidence and gate status. Full local reports remain under
ignored `results/`; no database credentials are stored in the summary.

## Limits and next step

- Retained 0.18.2 stale episodic prose behavior is unchanged: re-adoption text can
  render while the semantic claim remains withdrawn. The frozen fixture remains
  the reference; no retrieval redesign was introduced.
- No inferred independence, trust ranking, factual certainty, durable deferred
  ledger, complete bitemporal history or automatic abstention policy is claimed.
- Optional custom stores without inspection stay unavailable/indeterminate.
- Tests cover PostgreSQL 14.18 locally. Other server versions, concurrent writers,
  atomic cross-store reads and production-scale latency were not validated.
- The evidence-bound identity issue and ordinary random-ID output variability
  require explicit interpretation; neither is silently recast as a passing gate.

The Bench update and execution are complete. Review the capped-evidence contract
in Core before treating 0.18.3 as fully validated or publishing a release.
