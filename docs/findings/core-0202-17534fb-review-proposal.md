# Proposed frozen comparison review for Core 0.20.2 `17534fb`

**Proposed only; no approval is recorded for this commit.** The changelog
successor is `17534fb3715b5822ee3e695565f650c677f2ddd6`. It differs from the
previously approved `64f85f7` in documentation, tests and measurement tooling;
Core package source, metadata and lockfile are unchanged. A wheel built from
each exact Git archive has SHA-256
`ad29a8e3ecff445e31b656b3c50d944aae59f789d92026d5411109e2f44f7f92`.
The approval for `64f85f7` is candidate-specific and does not transfer.

On the confirmed reference Mac, Core `17534fb` was installed from the official
Git origin at that exact commit, and Bench ran from clean commit
`d40acd55b2e693b9d197b1f976cec8eef4fb2efd`, using Python 3.11.15, SQLite
3.53.1, seed 183 and `PYTHONHASHSEED=0`. The raw frozen comparison has 20
unapproved run-level mismatches; every run fingerprint matches the recorded
`64f85f7` official-origin result. Diagnostic and PostgreSQL parity passed, as
did the v2 source-history fixture (191/191 checks), all four backend comparisons
and a separate PostgreSQL repeat. The local Bench suite passed 366 tests. These
checks ran against separate databases concurrently, so their timing values are
not performance evidence.

The exact successor passed [all 25 hosted Core CI jobs](https://github.com/cogkura/cogkura/actions/runs/45290815513)
and [CodeQL](https://github.com/cogkura/cogkura/actions/runs/45290814856).
In the [independent hosted candidate matrix](https://github.com/cogkura/cogkura-bench/actions/runs/45290892933),
all five Python jobs passed their Bench tests and backend checks but failed the
strict unapproved frozen comparison. The macOS candidate decision below would
not approve those Linux raw comparisons.

The proposed scope remains one withdrawn-readmission correction and 82 other
exact macOS/Python 3.11.15 fields. The [previous candidate review](core-0202-64f85f7-review-proposal.md)
and its [resolution](core-0202-64f85f7-frozen-gate-resolution.md) explain the
differences and the earlier approval. The drafts below intentionally contain
no approval date and remain marked `PROPOSED`:

- [correction draft](proposals/core-0202-17534fb-correction-DRAFT.json)
- [exact-field draft](proposals/core-0202-17534fb-exact-macos311-DRAFT.json)

Evidence: [raw frozen comparison](core-0202-17534fb-official-raw.json.gz),
[query details](core-0202-17534fb-official-details.json.gz), and
[four-backend comparison](core-0202-17534fb-official-backends.json.gz). The
raw failure and original gold remain unchanged. Review or approval of these
exact differences would not itself authorize a tag or publication.
