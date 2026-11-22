# Proposed frozen comparison review for Core 0.20.2 `180010d`

**Proposed only; no 0.20.2 approval is recorded.** The unchanged frozen gold
still fails the raw comparison. This package identifies exactly what a later
candidate-specific review would cover; it does not approve those differences or
authorize a release.

Core `180010df26e4ac820046413f9b64dc2867803d73` was installed from the local
Git repository in a separate environment; its recorded VCS origin is a local
`file://` URL, not the official repository. Bench was at
`a68ec8d22d6e3e0d56c5f262083bc8621f36b298`. The run used the confirmed 2018
Mac, CPython 3.11.15, SQLite 3.53.1, seed 183, `PYTHONHASHSEED=0`, and local
PostgreSQL 14.18. PostgreSQL dependencies came from an existing local test
environment. This is exact local-commit evidence, not official-origin evidence.

The raw comparison reports 20 unapproved run-level mismatches. Its complete
recorded run fingerprints match the retained 0.20.1 `4c53eb6` official-source
run. Against the original 0.18.2 gold, one withdrawn-readmission correction and
82 other exact fields match the earlier 0.20.1 review package. The earlier
approval is explicitly limited to 0.20.1 and does not approve this candidate.
The earlier [review proposal](core-0201-4c53eb6-frozen-gate-proposal.md)
explains the three 0.20.1 candidate-specific query differences and the
inherited differences; the raw 0.20.2 report and query details below retain the
current evidence.

Diagnostic parity and the PostgreSQL comparison passed. The v2 source-history
fixture matched 191/191 checks on memory and PostgreSQL. The independent
four-backend comparison passed for all four tested datasets, and a separate
mini-dataset PostgreSQL repeat also passed. These results do not resolve the
other Core release gates.

The full local Bench suite passed 366 tests against this installed candidate
with PostgreSQL. Ruff, formatting and mypy checks passed. The Bench source and
test dependencies were supplied from the local working environment, so this is
not hosted CI or an official-origin installation.

The following candidate-specific drafts contain exact before/after values but
deliberately have no approval date and are marked `PROPOSED`. The strict
reviewer rejects them until an explicit decision is recorded:

- [withdrawn-readmission correction draft](proposals/core-0202-180010d-correction-DRAFT.json)
- [other exact macOS/Python 3.11 fields draft](proposals/core-0202-180010d-exact-macos311-DRAFT.json)

Evidence: [raw frozen report](core-0202-180010d-frozen-raw.json.gz),
[query details](core-0202-180010d-frozen-details.json.gz),
[four-backend comparison](core-0202-180010d-backends.json.gz), and
[PostgreSQL repeat](core-0202-180010d-mini-repeat.json.gz). A later approved
review must validate the exact candidate and official Git provenance; do not
modify the gold or treat the raw failure as a pass.
