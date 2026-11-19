# Core 0.20.1 `d5c009f`: exact frozen review

**Status: proposed for candidate-specific decision; not approval.** Core
`d5c009faae3e90d63c44196b2e91c6c77412ef9b` was installed from the official Git
origin on macOS, CPython 3.12.13. Bench was `0e17236`. The original 0.18.2 gold
and 0.20.0 successor reference are unchanged. Against the successor, 390 of
393 query fingerprints match; all 22 aggregate non-latency metrics and use
signatures match. The [machine-readable comparison](data/core-0201-d5c009f-exact-review.json)
verifies both query-detail hashes and records all 19 differing fields.

| Query | Exact difference in query details |
| --- | --- |
| `ac-q-c17` | Six score/activation fields change for the withdrawal episode. Its score changes from `0.916140217766221` to `0.9105275236243557`. |
| `ac-q-hist-at-withdraw` | Five score/activation fields change for the withdrawal episode. Its score changes from `0.7222706799682321` to `0.7190600922364386`. |
| `ac-q-hist-before-withdraw` | The historical correction relation changes from absent to `supersedes`; seven score/activation fields change across two retrieved items. The episode score changes from `0.3619826117190307` to `0.3671746256591035`. |

Retrieved identities, ranks, source-event IDs and query metrics are unchanged.
The [earlier investigation](core-020-cb52362-exact-review.md) explains and
counterfactually tests the cause: correctly excluding an already superseded
episode changes inverse-document-frequency weights for the remaining candidates.
The official candidate reproduces the earlier candidate's query signatures; the
historical relation is now preserved. This supports the explanation but does not
itself grant approval. Diagnostics match and the source-history v2 fixture passes
191/191 with both correction and withdrawal; PostgreSQL source parity passes.
The raw original-gold gate still fails and no numerical tolerance is changed.

A decision applies only to this exact Core commit and these three differences.
All other query, use, metric and source changes remain failures. Formal release
also depends on independent backend checks, performance, hosted CI, official
artifact verification and the user's release-sequence decision.
