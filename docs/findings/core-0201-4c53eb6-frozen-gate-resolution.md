# Core 0.20.1 `4c53eb6`: reviewed frozen gate

**The candidate-specific reviewed frozen gate passed on macOS/Python 3.11.15.**
The original raw frozen comparison still fails, and the original gold has not
changed. This is a frozen-gate result, not a package publication or a general
approval of other commits, environments, backend ordering differences, or the
remaining release work.

On 21 November 2026, the user explicitly approved the three reviewed query
differences and the inherited original-gold differences for Core commit
`4c53eb6a5f77cb9c275c7b39529f08fac7e809b1` and the stated macOS/Python 3.11.15
environment. Their exact scope and field values are in the [review package](core-0201-4c53eb6-frozen-gate-proposal.md).
The dated, candidate-scoped [withdrawn-readmission approval](../../tests/reviewed_corrections/cogkura_0201_4c53eb6.json)
and [exact-field approval](../../tests/reviewed_corrections/cogkura_0201_4c53eb6_macos311_exact.json)
are separate from the unchanged gold and the original failed raw report.

The candidate was installed in a separate environment from
`https://github.com/cogkura/cogkura.git` at the full approved commit. The captured
PEP 610 metadata records Git, the official URL, the exact commit and an installed
module. Bench code was clean at `70359e69a9c1221055c0c0c85733e5ddbf7f8967`;
the validation used seed 183, `PYTHONHASHSEED=0`, CPython 3.11.15 and SQLite
3.53.1. A fresh disposable PostgreSQL database was used.

The raw frozen comparison and raw release gate failed as expected. The existing
strict reviewer passed with the explicitly approved withdrawn-readmission
correction and all **82** other exact original-gold differences. The reviewer
checks the gold digest, exact candidate origin and identity, operating system,
Python patch version, fixture seed, hash seed, diagnostics, PostgreSQL, source
history and every approved before/after field. It leaves the raw failure intact.
The current v2 source-history fixture passed **191/191** on memory and
PostgreSQL, preserving both correction and withdrawal; PostgreSQL source parity
and diagnostic parity passed. The official-install query details, aggregate
non-latency metrics and use signatures matched the locally tested `4c53eb6`
run exactly.

Retained evidence: [raw report](data/core-0201-4c53eb6-official-raw.json.gz),
[query details](data/core-0201-4c53eb6-official-details.json.gz) and
[reviewed report](data/core-0201-4c53eb6-official-reviewed.json.gz).
The [Core validation note](../../../cogkura/docs/findings/0.20.1-shared-history-validation.md)
records local tests and performance.

The pushed Core `main` commit `2fd96a76e1745ed2828e0231ab5d301f3a8c5f52`
passed [all 25 hosted CI jobs](https://github.com/cogkura/cogkura/actions/runs/44931529383).
It differs from `4c53eb6` only in documentation and retained evidence; this is
not an exact-commit CI run for `4c53eb6`. Additional release checks, including
any required backend-order disposition, packaging and release sequence, remain
separate. The approval and the passing gate must not be transferred to a new
candidate or environment.
