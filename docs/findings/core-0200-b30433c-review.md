# Core 0.20.0 candidate `b30433c`: release evidence

**Status: review evidence, not release approval.** The candidate is Core Git
commit `b30433c9577fe2493072e442b0f4ea307f342fcf`, built from the released
0.19.6 commit `9745201bfcc5410d678a07737a4c935dd294e5b4`. Its only change
under `src/cogkura` is the version string. Profiling tools and their recorded
results are development assets outside the production package. Bench code was
`e2ad9cc` for the runs below. The candidate was installed from its local Git
checkout into a separate CPython 3.12.13 environment; the captured PEP 610 URL
is local. The strict release reviewers require an installation from the official
GitHub origin, so this evidence does not satisfy that provenance requirement.

## Frozen comparison

All 393 query fingerprints and all 22 runs' aggregate non-latency metrics and
use fingerprints match the [released 0.19.6 run](data/embedded-core-0.19.6-public-macos312-frozen.json.gz)
on the same Python and macOS platform. The original 0.18.2 frozen gold remains
unchanged (SHA-256 `927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c`).
It differs for exactly one query, `authoritative_corrections_v1/cogkura-correction`
`ac-q-c20`: original hash
`79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80`, candidate
hash `9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe`.
The previously reviewed 0.19.6 behavior omits the deferred readmission event
`ac-c20-again` from current recall and rendered context; see the [original
review](../review-0.18.4-withdrawn-readmission-deviation.md). Its earlier
approval is specific to 0.19.6 and does not transfer to this candidate. The raw
frozen gate fails pending candidate-specific disposition.

Diagnostics-on/off match. Source-aware metamemory v1 scores 191/191 checks,
and its PostgreSQL comparison passes. These do not establish correctness of
the separate known historical withdrawal/knowledge-time issue documented in
the Core candidate's release preparation; that fix is planned for 0.20.1.

The [raw report](data/core-0200-b30433c-frozen.json.gz), [query details](data/core-0200-b30433c-frozen-details.json.gz), and [comparison summary](data/core-0200-b30433c-frozen-review.json) preserve the evidence.

## Other release checks

Core's full suite on the candidate passed with PostgreSQL enabled: 1,035 passed,
6 skipped. Ruff, formatting and MyPy passed; Bench's suite passed 346 tests with
3 skipped and its static checks passed. The exact candidate wheel and source
distribution passed `twine check`; the wheel passed an isolated Python 3.11
installation, SQLite migration, persistence and restart check. Their SHA-256
hashes are `b668a233f16b9ebe31e623de9cc8e097d6315b2f855dd90936c6441630e757d9`
and `27ebadc50dafade4e8bf4412655681350ec4ce8f5aa180fa1913549c5460477b`,
respectively. Other platform and Python matrix jobs remain to be run.

The Core candidate’s `docs/findings/0.20.0-release-preparation.md`
records the measured baseline, the chosen 2018 Mac reference, and the user-set
0.20.1 targets. No 0.20.0 tag, publication or official-origin candidate has
been created.

## Storage-mode comparison

The [raw backend report](data/core-0200-b30433c-backends.json.gz) covers memory,
SQLite, SQLite close/reopen, and PostgreSQL on four controlled workloads. Each
SQLite reopen case reopened at least six times; the repeated PostgreSQL mini
run matched. Aggregate metrics, source assessments and use signatures match
across modes. All detailed query fingerprints were recalculated and every
differing field was inspected. Only the order of supporting event IDs differs:

| Query | Memory | SQLite, reopened SQLite and PostgreSQL |
| --- | --- | --- |
| `ac-q-c03` | `ac-c03-a`, `ac-c03-b` | `ac-c03-b`, `ac-c03-a` |
| `sm-contested` | `sm-conflict-pipeline-1`, `sm-conflict-pipeline-0` | `sm-conflict-pipeline-0`, `sm-conflict-pipeline-1` |
| `sm-evidence-cap` | `sm-conflict-pipeline-1`, `sm-conflict-pipeline-0` | `sm-conflict-pipeline-0`, `sm-conflict-pipeline-1` |

The exact fingerprints are identical to the [0.19.6 ordering review](../../tests/reviewed_corrections/order_0196_9745201.json).
No earlier approval transfers to this candidate. The raw backend gate therefore
fails pending candidate-specific disposition. An initial run was interrupted by
leftover rows from the previous frozen test in the disposable PostgreSQL
database; the reported run used a newly recreated database.
