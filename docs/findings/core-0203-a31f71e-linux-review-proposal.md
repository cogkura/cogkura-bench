# Proposed Core 0.20.3 `a31f71e` hosted Linux frozen review

**Proposed; no Linux frozen differences are approved.** The hosted
[raw candidate matrix](https://github.com/cogkura/cogkura-bench/actions/runs/45702415539)
ran the fixed candidate on Linux
`Linux-7.0.0-1020-azure-x86_64-with-glibc2.43`. Each Python job passed its
Bench suite, diagnostic/PostgreSQL parity and four-backend comparison, but
failed its strict unapproved frozen comparison against unchanged 0.18.2 gold.

| Python | Raw mismatched runs | Withdrawn-readmission correction | Other exact fields |
| --- | ---: | ---: | ---: |
| 3.11.18 | 20 | 1 | 87 |
| 3.12.16 | 9 | 1 | 17 |
| 3.13.18 | 9 | 1 | 17 |
| 3.14.10 | 9 | 1 | 17 |
| 3.15.2 | 9 | 1 | 17 |

For each Python version, all 22 run fingerprints and the full query-detail
reports match the corresponding previously retained 0.20.2 `fb72911` hosted
run, including the same Python patch version. That is comparison evidence, not
an existing Linux approval for this candidate. The 3.12–3.15 candidate run
fingerprints also match one another. Raw 0.20.3 reports and the corresponding
0.20.2 reference reports are retained in
[`data/core-0203-a31f71e-linux-initial`](data/core-0203-a31f71e-linux-initial/)
and [`data/core-0202-fb72911-linux-reference`](data/core-0202-fb72911-linux-reference/).

The initial hosted workflow did not capture the source-history v2 fixture. A
[subsequent hosted run](https://github.com/cogkura/cogkura-bench/actions/runs/45703402418)
recorded v2 on all five Python versions: each passed 191/191 source checks,
diagnostic and PostgreSQL parity, and four-backend comparison. Its frozen
fingerprints matched the initial runs and the strict unapproved comparison
remained failed. [Raw v2 reports](data/core-0203-a31f71e-linux-v2/) are
retained. The proposed [correction](proposals/core-0203-a31f71e-correction-DRAFT.json)
and [exact Linux fields](proposals/core-0203-a31f71e-exact-linux-DRAFT.json)
contain no approval date and are not approvals. The exact Linux draft is scoped
to the platform string and Python patch versions above. No Mac decision
implicitly approves Linux, no frozen gold is changed, and a frozen review does
not authorize release.
