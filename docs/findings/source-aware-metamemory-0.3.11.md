# Source-aware metamemory — CogKuraBench 0.3.11 candidate

**Verdict: REQUIRED CORE/BENCH VALIDATION PASSED. Candidate remains unreleased.**

**Date:** 14 November 2026.
**Core:** 0.18.3, `4d3ba737cf372bf5e59ab183570b3370e896e7d3`.
**Bench implementation:** `63f7d73`, followed by inspection output/reset checks in `39bde91`.
**PostgreSQL:** local disposable PostgreSQL 14.18 (Homebrew).

All declared source-assessment cases pass on both backends. Frozen results and
paired diagnostics agree with the controlled baseline. Following the approved
Core ordering fix, strict backend comparison now matches all 26 checkpoints,
including capped source attribution. The original failed gate is retained below
and in its original artifact. Bench updates pin the validated Core fix and
strengthen its PostgreSQL test; no fixture gold, Demo or Agent was changed and
no release was published.

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
| Strict PostgreSQL report parity after the fix | **PASS: 26 / 26 checkpoints agree** |

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

All **393 query signatures across 22 dataset/profile runs**, **46 recorded use results**,
and non-latency metrics match exactly. Signatures include evidence/order, text,
scores, activation components, neutral competition/interference/inhibition
observations, semantic state/provenance, old counters and correction context prose.
Fingerprints are retained in `tests/golden/cogkura_0182_frozen.json`.

The earlier summary's “46 uses” count described trace-qualified `UseResult`
records. The runner actually executes **73 explicit use actions** across these
profiles, including controls without inhibition-trace results. The post-fix
summary distinguishes these units; inputs and frozen fingerprints are unchanged.

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

## PostgreSQL execution and the resolved gate

PostgreSQL was **EXECUTED**, with migrations applied and fixture tenants isolated.
Adoption, replacement, withdrawal, replay, effective boundaries, knowledge-time
projection and the supported source-coverage contracts pass. The earlier 0.3.10
unexecuted database gap is not carried forward as an implied success or silently
left skipped.

Strict comparison preserves event identities, even under evidence truncation.
The original run against Core `9ab2241` failed at `sm-evidence-cap`:
`max_evidence=1` on two contested assertions with four source references returned:

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
promise and originally exited **1**, with `release_gate_passed=false`.

Inspection of the original Core code explained the difference: semantic evidence is
ordered by sequence number, observation UUID and revision in
`provenance._memory_evidence`; source assessment then slices that population by
the evidence cap. Stored semantic sequences themselves were assigned in UUID
order, so changing only an equal-sequence tie-break would not fix the defect.
Even a shared UUID allocator produces different IDs because the backends allocate
additional internal records.

**Approved resolution:** the user approved Core's slot-only canonical ordering
by source namespace, record ID, and numeric observation revision, before one
global occurrence cap. Revision population order, stored evidence sequences,
context provenance, cognitive behavior and counters remain unchanged. Unknown
source identities form an explicitly unavailable per-revision suffix; no inferred
trust, independence or portable opaque-ID ordering is claimed.

The same strict validator was rerun against Core `4d3ba73`, without modifying its
comparison or frozen fingerprints. It now exits **0**, with
`release_gate_passed=true`, PostgreSQL status **PASS**, and no source, frozen or
diagnostics mismatches. All 26 neutral source reports match, including exact
`sm-evidence-cap` event identities. Bench does not fetch beyond the requested cap.
Core separately passed 898 tests with zero skips on each Python 3.11–3.13 runtime,
including real PostgreSQL regression cases with opposite UUID-derived sequences.

## Required gates

The full Python matrix installs the locked environment with all extras, then runs
Ruff, format checking, MyPy, pytest with PostgreSQL, and every dataset/profile CLI
step in CI. The new CI service ensures database tests execute on 3.11–3.13.

| Runtime | Locked sync / Ruff / format / MyPy | Full pytest with PostgreSQL | Skipped tests | CI dataset/profile CLI steps |
| --- | --- | --- | --- | --- |
| Python 3.11.15 | PASS | **289 passed** | **0** | PASS |
| Python 3.12.8 | PASS | **289 passed** | **0** | PASS |
| Python 3.13.0 | PASS | **289 passed** | **0** | PASS |

The complete matrix was rerun against the updated pin with fresh PostgreSQL
databases: **289 passed, zero skips** on each runtime, and all required CLI steps
passed. PostgreSQL pytest now requires exact source identities for
capped reports too; the former eligible-population exception has been removed.
The separate strict release validator still checks frozen and paired outputs.

Reproduce with the commands in [source metamemory](../source-metamemory.md).
The checked-in [post-fix summary](data/source-metamemory-0.3.11-ordering-validation.json)
records the successful strict gate. The [original failed summary](data/source-metamemory-0.3.11-validation.json)
retains the original mismatch evidence. Full local reports remain under
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
- Canonical slot attribution closes the evidence-bound identity issue. Ordinary
  UUID-dependent retrieval/prose variability remains a separate existing behavior;
  frozen comparisons control identity allocation rather than claiming arbitrary-ID
  determinism.

The required Core and independent Bench gates are closed for this candidate.
Tags and publication remain within the separate release process.
