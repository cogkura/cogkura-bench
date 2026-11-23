# Proposed frozen comparison review for Core 0.20.2 `fb72911`

**Historical proposal.** The user subsequently approved this candidate; see the
[review resolution](core-0202-fb72911-frozen-gate-resolution.md). The changelog
successor is `fb72911ce58173bf3669181d0e2c25eeefeaa58d`. It differs from the
previously approved `64f85f7` in documentation, tests and measurement tooling;
Core package source, metadata and lockfile are unchanged. A wheel built from
each exact Git archive has SHA-256
`ad29a8e3ecff445e31b656b3c50d944aae59f789d92026d5411109e2f44f7f92`.
The approval for `64f85f7` is candidate-specific and does not transfer.

On the confirmed reference Mac, Core `fb72911` was installed from the official
Git origin at that exact commit, and Bench ran from clean commit
`ec824faaf335bd7aa3aa3541f513ea22afa08291`, using Python 3.11.15, SQLite
3.53.1, seed 183 and `PYTHONHASHSEED=0`. The raw frozen comparison has 20
unapproved run-level mismatches; every run fingerprint matches the recorded
`64f85f7` official-origin result. Diagnostic and PostgreSQL parity passed, as
did the v2 source-history fixture (191/191 checks), all four backend comparisons
and a separate PostgreSQL repeat. The local Bench suite passed 366 tests. These
checks used separate databases concurrently, so their timing values are not
performance evidence.

The exact successor passed [all 25 hosted Core CI jobs](https://github.com/cogkura/cogkura/actions/runs/45291614702)
and [CodeQL](https://github.com/cogkura/cogkura/actions/runs/45291614851).
In the [hosted independent candidate matrix](https://github.com/cogkura/cogkura-bench/actions/runs/45291723238),
all five Python jobs passed their Bench tests and backend comparisons but failed
the strict unapproved frozen comparison. A macOS decision would not approve
those Linux raw comparisons.
The proposed scope remains one withdrawn-readmission correction and 82 other
exact macOS/Python 3.11.15 fields. The [previous candidate review](core-0202-64f85f7-review-proposal.md)
and its [resolution](core-0202-64f85f7-frozen-gate-resolution.md) explain the
differences and the earlier approval. The drafts below intentionally contain
no approval date and remain marked `PROPOSED`. The second draft inherited the
previous candidate's macOS 15.8.1 prefix; the actual run was on macOS 15.8.3,
and the dated approval records the observed platform:

- [correction draft](proposals/core-0202-fb72911-correction-DRAFT.json)
- [exact-field draft](proposals/core-0202-fb72911-exact-macos311-DRAFT.json)

Evidence: [raw frozen comparison](core-0202-fb72911-official-raw.json.gz),
[query details](core-0202-fb72911-official-details.json.gz), and
[four-backend comparison](core-0202-fb72911-official-backends.json.gz). The
raw failure and original gold remain unchanged. Review or approval of these
exact differences would not itself authorize a tag or publication.
