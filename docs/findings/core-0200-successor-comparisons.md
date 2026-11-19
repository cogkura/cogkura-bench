# Reviewed successor comparisons for Core 0.20.0

On 19 November 2026 the user agreed to the approach in the [differences
investigation](core-0200-b30433c-differences-investigation.md): a successor to
the original frozen reference that expects the withdrawn readmission to be
excluded, and an order-insensitive comparison of supporting-event IDs. This
records agreement to the comparison design, not approval to publish a release
or a transfer of earlier candidate-specific exception manifests.

The [successor reference](../../tests/golden/cogkura_0200_successor.json)
preserves all 393 original query fingerprints, run metrics, and use hashes
except `authoritative_corrections_v1/cogkura-correction/ac-q-c20`, which is
changed from the 0.18.2 stale-claim fingerprint to the independently reviewed
0.19.6 fingerprint. The original reference remains unchanged. The original
comparison still fails and is reported alongside the successor comparison.
The existing integration test checks both the event IDs and rendered prose.

`scripts/review_successor_frozen.py` verifies the original file digest, verifies
the successor differs in exactly the specified query, compares every run,
requires source, diagnostic and PostgreSQL checks, and separately requires an
installed official-origin Git distribution of the selected exact candidate.
`scripts/review_support_order.py` verifies detailed query hashes before sorting
only the two support-ID fields, retains duplicate IDs, compares all remaining
fields, requires all four datasets, SQLite reopen and PostgreSQL repeat, and
requires the same official-origin identity. Raw reports are unchanged.

The [successor result](data/core-0200-b30433c-successor-review.json) and
[support-order result](data/core-0200-b30433c-support-order-review.json)
use the retained candidate `b30433c` local-origin reports. Their behavioral
comparisons pass; neither reports release acceptance because the distribution
was installed from a local Git URL. They do not prove behavior on other
platforms or fulfill the outstanding CI matrix. No tag or publication has been
made. The old 0.19.6 ordering and frozen-correction approval manifests are not
used for this candidate.

## Official-origin rerun

The exact candidate `b30433c9577fe2493072e442b0f4ea307f342fcf` was pushed to
the user-approved `release/0.20.0` branch on the official Core repository and
installed into the isolated Bench environment from the official Git URL. The
[official frozen run](data/core-0200-b30433c-official-frozen.json.gz) and
[full query details](data/core-0200-b30433c-official-frozen-details.json.gz)
retain the original mismatch and show passing diagnostics and source/PostgreSQL
checks. The [successor review](data/core-0200-b30433c-official-successor-review.json)
passes with official Git identity verified.

The [official backend run](data/core-0200-b30433c-official-backends.json.gz)
retains its raw ordering mismatches. The [support-order review](data/core-0200-b30433c-official-support-review.json)
passes, including SQLite reopen and PostgreSQL repeat, with official identity
verified. Both raw tools exit nonzero under the original strict comparisons;
no raw result has been rewritten. These are individual comparison checks, not
an assertion that all release requirements or CI have passed.

The Bench full suite using the official-origin candidate and a separate local
PostgreSQL database passed **353 tests with no skips** on macOS and Python
3.12.13. Core's [dispatched CI matrix](https://github.com/cogkura/cogkura/actions/runs/44586312144)
completed successfully: all 25 jobs passed across the Python 3.11–3.15 platform,
PostgreSQL and wheel-restart matrices.
