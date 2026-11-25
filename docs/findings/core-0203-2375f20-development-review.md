# Core 0.20.3 `2375f20` development comparison

**Status: development evidence, not frozen-gate or release approval.** Core
`2375f20199a858706192e3f1408fe35f69a2b7fd` was installed from the official Git
origin and compared on the reference Mac with Python 3.11.15 and macOS 15.8.3.
The frozen run records clean Bench commit
`2910b74e1add640f2310cb72374d78a52b583dfa`; the four-backend run and local
Bench suite used the prior Bench compatibility commit `c6bce8c`, whose
subsequent changes only adjust dependency constraints and changelog.

The strict raw comparison against unchanged 0.18.2 gold failed in 20 runs;
all differences remain unapproved for this Core candidate. All 22 run
fingerprints and the full retained query details exactly match the official
0.20.2 `fb72911` report. This is comparison evidence, not a transfer of its
candidate-specific approvals. Diagnostic parity and the PostgreSQL comparison
passed; the source-history v2 fixture passed all 191 checks. The independent
Bench suite passed 367 tests. The four recorded backend workloads matched across
memory, SQLite, reopened SQLite and PostgreSQL, with the separate mini PostgreSQL
repeat passing. The PostgreSQL source-parity check uses the retained v1 fixture;
the v2 result is reported separately.

Raw evidence: [frozen report](core-0203-2375f20-frozen-raw.json.gz),
[full query details](core-0203-2375f20-frozen-details.json.gz), and
[four-backend report](core-0203-2375f20-backends.json.gz). The initial hosted
candidate run using the older Bench version rejected 0.20.3 before the adapter
compatibility gate was extended. Another local frozen attempt correctly stopped
when Bench changed during the run; the retained frozen report was rerun from a
clean checkout after that change.

The final 0.20.3 candidate must be fixed and independently reviewed in its own
right. No gold, prior approval or release authorization was changed here.
