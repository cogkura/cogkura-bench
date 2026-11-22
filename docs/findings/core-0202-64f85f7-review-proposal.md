# Proposed frozen comparison review for Core 0.20.2 `64f85f7`

**Proposed only; no 0.20.2 approval is recorded.** The strict raw frozen gate
fails. This package provides evidence for an exact candidate-specific decision;
it does not change the gold, approve differences, or authorize release.

Core `64f85f78acd2046cafe0212c84b45c1d221affd4` was installed from the
official `https://github.com/cogkura/cogkura.git` Git origin. The report
records the exact installed commit and official URL. Bench was clean at
`93736e21f218b6f8f52392008c36aae9663572f0`. The reference host was the
confirmed 2018 Mac, running CPython 3.11.15, SQLite 3.53.1, seed 183 and
`PYTHONHASHSEED=0`, with a disposable PostgreSQL 14 database.

The raw comparison reports **20 unapproved run-level mismatches**. All run
fingerprints match the retained `442b5d2` candidate report, which in turn
matches the 0.20.1 reference run. Against the original gold, the proposed scope
is one withdrawn-readmission correction and 82 other exact fields. Their
before/after values are unchanged from the earlier review, but that approval
applied only to 0.20.1 and does not carry over. The earlier [review
proposal](core-0201-4c53eb6-frozen-gate-proposal.md) explains the inherited
differences and three query fingerprints associated with the 0.20.1 eligible
population and historical correction behavior.

Diagnostic parity and PostgreSQL parity passed; the v2 source-history fixture
matched 191/191 checks. The four-backend comparisons passed for all four
datasets and the separate mini PostgreSQL repeat passed. The local Bench suite
passed 366 tests against the official-origin candidate and PostgreSQL. These
results do not approve the raw differences or resolve other Core release gates.

[Hosted Bench CI](https://github.com/cogkura/cogkura-bench/actions/runs/45083945789)
passed. The independent [candidate matrix](https://github.com/cogkura/cogkura-bench/actions/runs/45084445719)
ran Python 3.11–3.15 from the official origin; all five jobs failed the strict
unapproved frozen comparison. In each job the Bench suite and the independent
backend comparison steps passed. The hosted raw reports use Linux and do not
substitute for the exact macOS/Python 3.11 review proposed below.

The following candidate-specific drafts contain the exact proposed fields;
they have no approval date and are marked `PROPOSED`:

- [withdrawn-readmission correction draft](proposals/core-0202-64f85f7-correction-DRAFT.json)
- [other exact macOS/Python 3.11 fields draft](proposals/core-0202-64f85f7-exact-macos311-DRAFT.json)

Evidence: [raw frozen report](core-0202-64f85f7-official-raw.json.gz),
[query details](core-0202-64f85f7-official-details.json.gz), and
[four-backend and repeat report](core-0202-64f85f7-official-backends.json.gz).
The approved review, if granted, must be limited to this commit and environment;
the raw failure must remain visible.
