# Cogkura Core 0.20.1

This release improves retrieval performance and preserves more historical
memory state through reinforcement, corrections and withdrawals.

- Reduces repeated retrieval work and scopes SQLite semantic reads.
- Retains episode, semantic-memory, revision and relation snapshots for supported
  historical reconstruction, including linked and inactive memories.
- Preserves correction and withdrawal transitions in source inspection.
- Detects ambiguous backdated tenant history in the built-in stores and raises
  `HistoricalStateUnavailableError` for affected historical queries.
- Includes SQLite migrations through `008_history_order` and PostgreSQL
  migrations through `015_history_order`.

Historical reconstruction remains subject to documented limits for legacy or
custom stores, missing snapshots and concurrent writes. SQLite files are not
encrypted by default and network filesystems remain unsupported for WAL.

The candidate-specific reviewed frozen gate passed with the explicitly approved
exact differences; the original raw failure and baseline remain available.
Exact backend comparisons passed across memory, SQLite, reopened SQLite and
PostgreSQL. On the selected 2018 Mac, the synthetic 1,000-observation workload
measured p95 recall at 1.191 s in memory and 1.741 s on SQLite. These are
single-environment synthetic measurements, not production guarantees.

The release is intended to target Core commit
`4c53eb6a5f77cb9c275c7b39529f08fac7e809b1`. Its [frozen review](https://github.com/cogkura/cogkura-bench/blob/e6d8f2d/docs/findings/core-0201-4c53eb6-frozen-gate-resolution.md)
and [backend and artifact checks](https://github.com/cogkura/cogkura-bench/blob/e6d8f2d/docs/findings/core-0201-4c53eb6-release-checks.md)
retain the validation evidence and approval scope. Core CI passed all 25 jobs on
a documentation-only descendant of the candidate; the exact-commit hosted CI
run is still to be performed after the release tag exists.
