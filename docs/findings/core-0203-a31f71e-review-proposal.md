# Proposed Core 0.20.3 `a31f71e` frozen comparison review

**Historical proposal; subsequently approved.** See the [reviewed resolution](core-0203-a31f71e-frozen-gate-resolution.md). The fixed candidate is Core
`a31f71e222dd231ed9643bc1d1cc109e3e8153dd`, installed from the official Git
origin. The raw run used the confirmed reference Mac, Python 3.11.15, macOS
15.8.3, SQLite 3.53.1 and clean Bench commit
`70cec0a084b343bbe7fe960be662baa34c18b132`. The raw comparison against the
unchanged 0.18.2 gold fails in 20 runs and remains preserved.

The candidate's 22 run fingerprints and full query details exactly match the
previously reviewed 0.20.2 `fb72911` report. Comparing every frozen field to
the unchanged gold yields the same one withdrawn-readmission correction and 82
other exact fields described below. Prior approval applied only to the 0.20.2
candidate and does not transfer to this one. Approval of these differences
would apply only to this candidate on the specified reference environment; it
would not approve Linux comparisons, change the gold, authorize a release or
approve a later candidate.

The unapproved drafts list the exact before/after fingerprints and fields:
[one-correction draft](proposals/core-0203-a31f71e-correction-DRAFT.json) and
[82-field draft](proposals/core-0203-a31f71e-exact-macos311-DRAFT.json). They
are marked `PROPOSED`, carry no approval date and cannot be used as approvals.

The candidate's source-history v2 fixture passed 191/191 checks, diagnostics
and PostgreSQL parity passed, and the local Bench suite passed 367 tests. The
four recorded workloads matched across memory, SQLite, reopened SQLite and
PostgreSQL; the separate mini PostgreSQL repeat passed. The PostgreSQL
source-parity check uses the retained v1 fixture; the v2 result is reported
separately. Raw evidence: [frozen report](core-0203-a31f71e-frozen-raw.json.gz),
[full query details](core-0203-a31f71e-frozen-details.json.gz), and
[four-backend report](core-0203-a31f71e-backends.json.gz).

Core's hosted matrix, artifact checks, timing/state evidence and final release
approval have their own gates. Preserve all raw results regardless of review.
