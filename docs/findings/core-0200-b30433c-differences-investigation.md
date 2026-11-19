# Investigation of the 0.20.0 candidate's unapproved differences

**Status:** Investigation only. The user declined to approve the differences
for candidate `b30433c9577fe2493072e442b0f4ea307f342fcf`. This document does
not approve a new comparison or change the release gate. Raw reports and the
exact fingerprints are preserved in the [candidate review](core-0200-b30433c-review.md).

## Deferred readmission (`ac-q-c20`)

The original 0.18.2 frozen fingerprint includes both the withdrawal and a later
observation claiming the same strategy again in current recall and context. The
later observation's semantic readmission is deferred after the authoritative
withdrawal; showing its unsupported claim as current evidence contradicts that
state. The candidate removes the stale claim and retains the withdrawal. This
is the 0.18.4 fix inherited by 0.19.6, not a regression introduced by 0.20.0.
The released fixture's render-forbidden literal does not catch the prose wording;
the [original review](../review-0.18.4-withdrawn-readmission-deviation.md)
documents the before and after, and the integration test separately checks the
retrieved event IDs. Core also tests that an unrelated sentence in the same
episode survives, historical context remains available, and semantic revisions
are unchanged by inspection.

Returning the old gold fingerprint would restore the stale-claim leak. A sound
alternative to an exception is a separately designed and reviewed successor
baseline with the corrected expected behavior, retaining the original gold and
its raw comparison for audit. Such a baseline needs its own explicit scope and
validation; it must not silently regenerate gold or treat this investigation as
approval.

## Supporting-event order

Bench's CogKura adapter copies semantic memory evidence into
`supporting_event_ids` in the order supplied by Core, de-duplicating event IDs.
The frozen comparison hashes the resulting list in order. Bench's authoritative
correction and source authority metrics compare these IDs as **sets**. Thus the
reported ordering differences do not change those metrics, and the exact raw
query-detail review found no other changed field. This is an observation about
the Bench contract and these test cases, not a claim that Core's public evidence
order is universally meaningless.

Core's SQLite semantic loader orders evidence by sequence number and observation
ID; the PostgreSQL loader orders by sequence number. In-memory storage retains
the tuple it receives. These paths allow differences in the reported sequence;
we have not established the individual tied sequence numbers or the precise
source of each reversal, so this is not a complete root-cause proof for every
backend. UUID-based order must not be interpreted as event chronology.

A read-only diagnostic sorted only `supporting_event_ids` inside the correction
and source-authority observations in the retained detailed backend report.
All 78 query details matched in each of SQLite, reopened SQLite and PostgreSQL
against memory (234 comparisons), without changing any other field. This is a
counterfactual comparison over saved evidence, not a new release gate, API
change, or proof of equality on other workloads.

A potential Bench change is to define and test an order-insensitive comparison
for these specific support-ID collections while retaining raw ordered output,
and test that changes in membership, multiplicity policy and every unrelated
field still fail. Another option is to define and enforce a deterministic order
in Core's storage contract, but that changes a public behavior and needs a
separate review of ordering semantics, migration and all backends. Neither
approach resolves the separate old-gold `ac-q-c20` difference by itself.
