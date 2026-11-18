# Core candidate `cb52362`: exact scoring and ordering review

**Status:** Evidence for review, not an approval or release acceptance. Core is
local Git commit `cb52362e43b43324ace7f88d4ad702cf35a998ee`, based on released
0.19.6 `9745201bfcc5410d678a07737a4c935dd294e5b4`. Bench for the comparisons is
`f7f917f7edd945d1f8de8372b589e4311cf98ad4`. Core was installed from the exact
local Git commit into a separate environment, with PEP 610 provenance retained
in the reports. Its package version remains `0.19.6`; this is a development
candidate, not a released 0.20 distribution. The strict approval scripts require
an installed Git distribution whose origin is the official GitHub URL, so the
local-origin installation does not satisfy that later release requirement.

The original [0.18.2 gold](../../tests/golden/cogkura_0182_frozen.json), SHA-256
`927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c`, is unchanged.
The raw frozen comparison exits 1. On macOS 15.8.1, CPython 3.12.13 and SQLite
3.53.1, all 393 query fingerprints were checked against both original gold and
the [released 0.19.6 run on the same Python and platform](data/embedded-core-0.19.6-public-macos312-frozen.json.gz).
Detailed signatures for every query were verified against their hashes on both
the candidate and 0.19.6 sides. All 22 run-level aggregate non-latency metrics
and use fingerprints match released 0.19.6. This is one runtime/platform, not
the full compatibility matrix. The original gold has hashes rather than full
query details; the field-level comparison is therefore to 0.19.6, with the
original-gold hashes reported separately.

## Frozen query changes

Exactly four fingerprints differ from original gold, all in
`authoritative_corrections_v1/cogkura-correction`. The first is the previously
reviewed 0.19.6 withdrawal-readmission correction; its candidate hash exactly
matches the 0.19.6 hash. It still needs candidate-specific approval. The other
three differ from 0.19.6 as well:

| Query | Difference from 0.19.6 |
| --- | --- |
| `ac-q-c20` | Unchanged from 0.19.6: the deferred readmission `ac-c20-again` is absent from current recall and rendered context. The [earlier review](../review-0.18.4-withdrawn-readmission-deviation.md) records the original before/after behavior. |
| `ac-q-c17` | Six activation/score fields change for the withdrawal episode. Its score changes from `0.916140217766221` to `0.9105275236243557`. |
| `ac-q-hist-at-withdraw` | Five activation/score fields change for the withdrawal episode. Its score changes from `0.7222706799682321` to `0.7190600922364386`. |
| `ac-q-hist-before-withdraw` | The historical correction relation changes from absent to `supersedes`; seven activation/score fields change across its two retrieved items. The episode score changes from `0.3619826117190307` to `0.3671746256591035`. |

There are 19 changed detail fields across the three new fingerprints. Their
retrieved identities, ranks, source-event IDs and query metrics are unchanged.
The [machine-readable review](data/core-020-cb52362-exact-review.json) records
every exact before/after field, all four original and candidate hashes, and the
backend differences below. The [raw frozen report](data/core-020-cb52362-frozen.json.gz)
and [all query details](data/core-020-cb52362-frozen-details.json.gz) remain
unmodified evidence. The original gold's `ac-q-c20` before/after behavior is
supported by the earlier review, not reconstructed from its hash.

## Why scores changed

The historical fix preserves and recovers the incoming correction link when a
later withdrawal closes a revision. In these scenarios, the candidate no longer
scores the earlier `ac-time-adopt` episode describing application-startup
migrations. It was already superseded at the relevant effective times. Removing
it changes the candidate population used for inverse-document-frequency text
weights, which changes partial-match activation and, in turn, scores and some
rank-activation values for the remaining items. The correction relation is now
visible in the historical observation.

This explanation was tested, not inferred solely from correlation. A separate
dataset-only diagnostic recorded the candidates and text weights under the
released Core and candidate. Replaying the candidate with the released run's
text weights restored **all** baseline query fields and scores for these three
queries except the intentional `supersedes` relation. The intervention was
limited to the diagnostic process; it does not alter production behavior or
acceptance thresholds. Its [baseline](data/core-020-cb52362-weight-baseline.json.gz),
[candidate](data/core-020-cb52362-weight-candidate.json.gz), and
[counterfactual](data/core-020-cb52362-weight-counterfactual.json.gz) traces are
retained. `scripts/trace_history_scoring.py` reproduces these runs with
`PYTHONHASHSEED=0`; supply `--override-from` with the uncompressed baseline
trace for the counterfactual.

## Cross-backend ordering

The [raw four-backend report](data/core-020-cb52362-backends.json.gz) covers
in-memory, SQLite, SQLite close/reopen, and PostgreSQL on the four controlled
workloads. SQLite reopening occurred during each case; a repeated PostgreSQL
mini run matched. All source assessments, aggregate metrics and use signatures
match in memory versus each backend. Every differing query detail was checked:

| Query | In memory | SQLite, reopened SQLite and PostgreSQL |
| --- | --- | --- |
| `ac-q-c03` | `ac-c03-a`, `ac-c03-b` | `ac-c03-b`, `ac-c03-a` |
| `sm-contested` | `sm-conflict-pipeline-1`, `sm-conflict-pipeline-0` | `sm-conflict-pipeline-0`, `sm-conflict-pipeline-1` |
| `sm-evidence-cap` | `sm-conflict-pipeline-1`, `sm-conflict-pipeline-0` | `sm-conflict-pipeline-0`, `sm-conflict-pipeline-1` |

Each row is the order of `authoritative_correction_observations[0].supporting_event_ids`;
there are no other changed query-detail fields for those comparisons. These
are the same exact memory and backend fingerprints that were separately approved
for 0.19.6, but that approval does not transfer to this candidate. The raw
backend comparison fails until a candidate-specific disposition exists.

Diagnostics-on/off matched. The v1 source fixture remains 190/191; v2 is
191/191 and its source observations match between in-memory and PostgreSQL.
Both v1 and v2 PostgreSQL parity checks passed. No frozen gold, source fixture
v1 or numerical tolerance was changed.

## Remaining review and release work

The evidence supports retaining the user-selected complete transition history
and identifies the exact scoring and supporting-event order consequences. The
three score changes and the prior `ac-q-c20`/backend-order exceptions are not
automatically approved by that decision. An explicit candidate-specific
decision is still required before creating approval manifests. A formal reviewed
release also needs a correctly versioned candidate installed from the official
Git origin, rerun comparisons on that exact identity and required environments,
and the outstanding performance and compatibility gates. No package was
published and no release tag was created.
