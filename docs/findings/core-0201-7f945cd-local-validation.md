# Core 0.20.1 `7f945cd`: local candidate validation

Status: **not release approved**. Core candidate `7f945cdf5e5e1a8ec4854fda7acc734a959356e7` was built and installed from the clean local Git repository. Bench was `84241a69a940ce3dac27526f3f316b8de880bb72`. The candidate was not available from official origin during these runs; the Git distribution identity records the local file URL. No tag or package was published.

## Frozen differences

The independent [successor comparison](data/core-0201-7f945cd-successor.json.gz) compares all 393 query/profile outcomes to the unchanged 0.20.0 successor. Exactly three queries differ; all query metrics, aggregates and recorded-use signatures match. The [complete field review](data/core-0201-7f945cd-exact-review.json.gz) is byte-for-byte equivalent as JSON to the prior `d5c009f` exact review: six fields on `ac-q-c17`, five on `ac-q-hist-at-withdraw`, and eight on `ac-q-hist-before-withdraw`. The last includes the newly visible `supersedes` relation. The user declined approval of the prior candidate's differences; this run does not grant or imply approval for this candidate.

The previously recorded weight-substitution experiment explains the score changes as effects of removing stale episode content from the candidate-IDF population. Restoring that population would let ineligible content affect scoring. Removing the correct relation would contradict the chosen complete-transition history. The alternative IDF-off experiment changed 361 signatures and 25 item sequences, so it is not a behavior-preserving repair. No baseline, numerical tolerance, result field or approval manifest was altered. [Detailed run](data/core-0201-7f945cd-successor-details.json.gz); [original frozen baseline run](data/core-0201-7f945cd-frozen.json.gz) and [details](data/core-0201-7f945cd-frozen-details.json.gz).

## Independent checks

The isolated Python 3.12.16 Bench run against the exact local Git install passed 360 tests with PostgreSQL. Diagnostics matched; the complete-transition source-history v2 fixture passed 191/191 and PostgreSQL source parity passed for v1 and v2. Strict frozen validation remains failed.

The [raw four-backend report](data/core-0201-7f945cd-backends.json.gz) fails ordered parity for the previously known supporting-event order differences. The [diagnostic review](data/core-0201-7f945cd-support-review.json.gz) found no other differences after normalizing only supporting-event order; it does not approve those differences, and official-origin identity verification correctly failed for this local install. Mini PostgreSQL repeat passed.

The exact wheel and sdist passed `twine check`. Isolated dependency-free wheel installation, migration, persistence and restart checks passed on CPython 3.11.15, 3.12.16, 3.14.10 and 3.15.2. SHA-256: wheel `2c2d5466099738da3f2ef8d24f0f1a5277485324f5e3760f85024d094d025f44`; sdist `fb4d95a1086bbc092bc75e7c0f2da2274629da7fe48fc517c40f2f3fff92f7db`. Python 3.13 and the hosted matrix were not verified in this run. The earlier full Core suite against this candidate passed 1,054 tests with six source-database skips; the final additional mixed-time test passed separately.

## Performance on the chosen 2018 Mac

Clean exact Core commit, CPython 3.11.15, SQLite 3.53.1, sequential uninstrumented calls, five revisions per base observation and uncontrolled OS caches. For 100 and 250, median uses 100 warm samples after the first; for 1,000, nearest-rank p95 uses all 100 samples. One run per size and backend; results are not a production guarantee. At 1,000 the fixture contains 1,006 observations and 5,006 revisions. The rounded recall outputs, counts and applied operations match between memory and SQLite for each size.

| Base observations | Memory | SQLite | Target |
| --- | --- | --- | --- |
| 100 warm median | 0.080 s | 0.117 s | under 1 s |
| 250 warm median | 0.208 s | 0.302 s | under 1 s |
| 1,000 p95 | 1.203 s | 1.727 s | under 2 s |

All targets pass in this run. Every sample is retained as `data/core-0201-7f945cd-{memory,sqlite}-{100,250,1000}.json.gz`. Prior candidate runs included a SQLite p95 miss; this result does not erase that variability.

## Remaining release gates

The user has not approved the three exact differences or the raw backend support-order differences for this candidate. Official-origin installation, hosted CI, official artifact provenance and the release sequence remain outstanding. An attempted push of the candidate to official `main` was rejected by automatic approval review because that consequential shared-branch update was not explicitly authorized.
