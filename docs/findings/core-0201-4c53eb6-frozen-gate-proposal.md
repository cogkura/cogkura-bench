# Proposed frozen-gate disposition for Core 0.20.1 `4c53eb6`

**Not approved; the release gate remains open.** This is a review package for
Core `4c53eb6a5f77cb9c275c7b39529f08fac7e809b1`, not a change to the frozen
baseline, a new approval, or official-origin evidence. The earlier user decision
was to investigate rather than approve the score and relation differences.

On the selected 2018 Mac, Bench `7373d5ff2d00b10a9dd260e5fc3869b031850c34`
compared the candidate against a locally paired Core `b30433c` source run under
CPython 3.11.15, SQLite 3.53.1, seed 183 and `PYTHONHASHSEED=0`. The candidate
query details were checked against every recorded fingerprint in both reports.
Exactly three of 393 query fingerprints differ; their item identities, order,
metrics and use signatures match the paired reference. The 19 exact detail
fields and both hashes for each query are in the [full review data](data/core-0201-4c53eb6-frozen-gate-proposal.json).

| Query | Change from paired 0.20.0 source run |
| --- | --- |
| `ac-q-c17` | Six activation/score fields; the returned withdrawal episode's score changes from `0.916140217766221` to `0.9105275236243557`. |
| `ac-q-hist-at-withdraw` | Five activation/score fields; the withdrawal episode's score changes from `0.7222706799682321` to `0.7190600922364386`. |
| `ac-q-hist-before-withdraw` | Seven activation/score fields and a correction relation changes from absent to `supersedes`; the episode's score changes from `0.3619826117190307` to `0.3671746256591035`. |

The previously retained [causal investigation](core-0201-d5c009f-further-investigation.md)
shows the scoring changes arise because a superseded episode is excluded from
the eligible inverse-document-frequency population. The relation preserves the
correction after a later withdrawal. Restoring the old numbers by including the
ineligible episode, or removing the correction relation, would change those
semantics. The user's separate choice to report both source transitions is
retained. Neither that choice nor this evidence approves the frozen changes.

The original 0.18.2 gold has 83 differing frozen fields on this platform. Of
these, 80 also differ identically in the paired 0.20.0 run: 61 metric fields and
19 query fingerprints. One of the latter is the `ac-q-c20` withdrawn-readmission
correction, which requires a separate candidate-specific decision; the other
18 are inherited query fingerprints. The remaining three fields are the query
fingerprints above. Every before/after field is retained in the review data;
no tolerance, normalization or changes to the gold are proposed.

Two deliberately non-executable drafts show the proposed exact scope:

- [withdrawn-readmission correction draft](proposals/core-0201-4c53eb6-correction-DRAFT.json);
- [exact macOS/Python 3.11 field draft](proposals/core-0201-4c53eb6-exact-macos311-DRAFT.json),
  which contains the other 82 exact fields, including the three changed fingerprints.

Both omit an approval date and are marked proposed. The existing correction
validator rejects the draft. An in-memory test with a **synthetic** official
identity and hypothetical date exercised the existing reviewer and matched all
82 exact fields; it did not approve anything or establish provenance. The
[raw candidate report](../../../cogkura/docs/findings/data/cogkura-4c53eb6-report.json.gz)
and [candidate details](../../../cogkura/docs/findings/data/cogkura-4c53eb6-details.json.gz)
remain unchanged. The [paired reference report](data/core-0200-b30433c-local-paired-report.json.gz)
and [details](data/core-0200-b30433c-local-paired-details.json.gz) are retained
here. The paired reference used a local source path whose installed-distribution
metadata did not identify that reference; it is diagnostic, not official-origin
verification.

The v2 source-history fixture passed 191/191 on memory and PostgreSQL, with
both transitions, and diagnostic and PostgreSQL source parity passed. The
candidate's Core suite and selected-Mac performance results are recorded in the
[Core validation note](../../../cogkura/docs/findings/0.20.1-shared-history-validation.md).
The frozen decision, an actual Git-installed candidate from official origin,
and fresh hosted CI remain outstanding. Even explicit approval of the listed
fields alone would not establish those other release checks.
