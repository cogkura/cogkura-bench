# Core 0.20.2 hardening: initial four-backend baseline

**Status: baseline only; candidate acceptance remains open.**

At Bench commit `31da167`, the existing independent embedded-freeze runner
compared the released 0.20.1 Core source (checkout `a62196b`, whose Core source
matches release commit `4c53eb6`) across in-memory, SQLite, reopened SQLite and
a disposable local PostgreSQL 14.18 instance. All recorded signatures matched
across these four backends for `mini`, `authoritative_corrections_v1`,
`persistent_inhibition_v1` and `source_aware_metamemory_v1`. A separate mini
run also passed the PostgreSQL cleanup and repeat check. The reports retain
complete query signatures:

- [Four workloads and backends](core-0202-baseline-four-backends.json.gz)
- [Mini with PostgreSQL repeat](core-0202-baseline-mini-backends.json.gz)

The local Bench virtual environment had a broken Python link; the runner used
the Core checkout's CPython 3.11 environment with Bench imported from its own
source tree. This does not validate a candidate artifact, new historical cases,
the full frozen gold comparison, or independent approval of any future
candidate differences. Those remain required.

The same four workloads were subsequently run against the in-progress 0.20.2
working source with `--allow-dirty-source`. Memory, SQLite, reopened SQLite and
PostgreSQL signatures matched for every workload. The complete report is
[retained separately](core-0202-working-four-backends.json.gz). This is a
working-tree parity check; it is not a frozen candidate or a review of
candidate-specific differences against the original gold.
