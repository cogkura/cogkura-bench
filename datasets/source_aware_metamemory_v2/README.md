# Source-aware metamemory v2

This version retains the events and queries of v1, changing only the expected
transition event IDs for `sm-withdrawn`. That query follows an authoritative
correction (`sm-chain-replace`) and a later withdrawal (`sm-chain-withdraw`).
Both transitions were known by the query time, so v2 requires both identities.
Earlier knowledge-time and pending-effective checks remain unchanged. No source
identity implies independence, factual truth, or trust.

The released v1 data remains unchanged and continues to score its original
expectation. The versions have different ground truth and their source scores
must be reported separately.
