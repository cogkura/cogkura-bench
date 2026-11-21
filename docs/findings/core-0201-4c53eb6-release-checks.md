# Core 0.20.1 `4c53eb6`: backend and artifact checks

The exact Core commit `4c53eb6a5f77cb9c275c7b39529f08fac7e809b1` was
installed from the official Git origin and tested under CPython 3.11.15 and
SQLite 3.53.1 with seed 183 and `PYTHONHASHSEED=0`. Bench was
`72bec9f33601e1485d11dca7cf81d870e905e2a7`.

The [raw backend report](data/core-0201-4c53eb6-backends.json.gz) passed exact
comparisons for memory, SQLite, reopened SQLite and PostgreSQL across mini,
authoritative corrections, persistent inhibition and source metamemory.
PostgreSQL mini also matched on repeat after cleanup. The comparisons retain
query details and source assessments. No supporting-event ordering exceptions
were observed, so no backend-order approval was required for this candidate.

A clean clone from the official origin at the same commit produced a wheel and
sdist; both passed `twine check`. Their SHA-256 hashes were:

- Wheel: `7ad25f72bcfee3ff743533d72ae2c600f229a1818b115ce4acb0bc17507d44a9`
- Sdist: `28a2dd8b19e829def643ea157f46ad1ed05452d102be24c6d1b97a675671363c`

All 87 packaged Core Python, SQL and typing-marker files matched that commit
byte-for-byte. A separate dependency-free wheel environment passed installed
identity, SQLite migration, recall and fresh-process restart checks. Another
wheel environment ran the [raw frozen/source diagnostic](data/core-0201-4c53eb6-wheel-raw.json.gz)
with PostgreSQL; the [query details](data/core-0201-4c53eb6-wheel-details.json.gz),
aggregate non-latency metrics and use signatures matched the Git-installed
candidate exactly. Source-history v2 passed 191/191, PostgreSQL source parity
and diagnostic parity passed. As expected, the wheel is identified by its local
artifact URL, not Git; the separately retained [official Git reviewed gate](core-0201-4c53eb6-frozen-gate-resolution.md)
provides candidate provenance and the explicit frozen approvals.

These are pre-publication artifacts and checks. Any tag and published package
must be checked against the approved commit and the actual published artifacts.
