# Source transition history v2

The released `source_aware_metamemory_v1` fixture's `sm-withdrawn` check expects
only the withdrawal event, although its earlier correction was also known. The
user selected reporting both transitions. The new versioned fixture requires
both exact event IDs and otherwise retains v1's queries and event stream; a
dataset test verifies that difference. V1 and its raw score remain intact.

An [exploratory source run](data/source-history-v2-candidate-exploratory.json)
on the uncommitted Core implementation patch identified in that report yielded
190/191 checks on v1 and 191/191 on v2. V1 and v2 produced equal non-source
signatures and source observations; a separate repeat also checked full source
observations, including decisions. The v2 in-memory and PostgreSQL source
observations matched. This is not a clean installed candidate or a full release
validation; it does not approve the frozen scoring changes.

The existing validator continues to run and report v1. To additionally run v2,
pass `--source-history-v2` with `--diagnostics-parity --postgres` to
`scripts/run_source_metamemory_validation.py`. It reports the v1 metrics and
the separate v2 metrics, actual transition IDs, output comparison, and v2
PostgreSQL parity. The opt-in source gate requires the single expected v1
mismatch on `sm-withdrawn`, all 191 v2 checks, exact transition identities,
matching outputs, and PostgreSQL parity. Without the flag, v1 remains mandatory.

Supply `--source-history-v2` explicitly to `review_candidate_frozen_report.py`
or `review_frozen_exact_differences.py` when reviewing that raw report. These
reviewers still require the exact installed Core version and commit,
unchanged original frozen gold, applicable candidate-specific approval
manifests, diagnostic parity, and the other frozen checks. The option does not
make a dirty source tree or an unapproved score difference acceptable. Original
v1 raw failure must be retained alongside the reviewed result.
