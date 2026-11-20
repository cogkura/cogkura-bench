# Further investigation of unapproved 0.20.1 frozen differences

**Status: the user declined approval for Core `d5c009f`.** The release gate
remains open. No gold, tolerance, production ranking policy or approval
manifest was changed during this investigation.

## Reproduced causal experiment

The official-origin candidate `d5c009faae3e90d63c44196b2e91c6c77412ef9b` was
replayed with the text weights captured from the 0.20.0 behavior, using the
same diagnostic-only intervention described in the [earlier investigation](core-020-cb52362-exact-review.md).
This overrides weights inside the test process; it is not a production fix.
Comparing its query details with the independently retained 0.20.0 official
query details produced:

| Query | Remaining differences after legacy weights are substituted |
| --- | --- |
| `ac-q-c17` | None |
| `ac-q-hist-at-withdraw` | None |
| `ac-q-hist-before-withdraw` | One: correction relation is now `supersedes` instead of absent |

The [official counterfactual trace](data/core-0201-d5c009f-weight-counterfactual.json.gz)
retains the intervention and output. The independently captured [exact review](data/core-0201-d5c009f-exact-review.json)
contains the 19 original before/after fields, without normalization or approval.

In the investigated `2026-11-10T12:00Z` case, the 0.20.0 scoring population
includes the now-superseded episode `payments-api migrations start with the
application.` alongside the withdrawal; the corrected candidate excludes that
episode. For example, the old IDF weights for `migration` and `strategy` are
approximately 1.405465, whereas the new weights for those terms are 1.0. IDF
weights depend on the complete candidate population, not only the returned
items; the altered population explains the resulting score changes. The visible
`supersedes` relation comes from preserving and recovering the correction link
that the old history had lost after withdrawal.

## Implications

There is a mechanical way to reproduce the old numerical scores for these
queries: use the old weight population while filtering the stale episode from
returned results. The counterfactual supports that narrow statement, but it
supplies weights captured from one run and does not define how to construct a
safe general population. Reintroducing stale candidates into the weight corpus
would change the meaning of scoring and could allow hidden or historically
ineligible content to affect results. It needs a separate design and tests for
knowledge-time boundaries, forgotten memories, tenant isolation and candidate
caps; it would not restore the old missing-relation fingerprint unless correct
provenance were also suppressed. No evidence here establishes that this would be
a safe or behavior-preserving production change.

The clean alternatives are to retain the corrected history and explicitly
review the three consequences, or to design and validate a different weighting
and provenance contract. The user's rejection means the former has not been
approved; relabeling or ignoring the changed fields in Bench would not resolve
that decision. Reverting the underlying fix would reinstate the previously
observed correction/withdrawal knowledge-time defect. No option is silently
selected here.

## Independent release evidence

The [official frozen report](data/core-0201-d5c009f-frozen.json.gz) and [details](data/core-0201-d5c009f-frozen-details.json.gz)
retain the original strict failure. The [backend report](data/core-0201-d5c009f-backends.json.gz)
and [support-order comparison](data/core-0201-d5c009f-support-review.json)
show that the reviewed order-insensitive comparison passes for this official
identity; raw ordered differences remain. Source-history v2 passes 191/191 and
PostgreSQL source parity passes. The official-origin Bench suite passed 356 tests
with PostgreSQL; the hosted Core CI matrix passed all 25 jobs. These checks do
not override the unapproved frozen changes.

## Exact candidate performance and packaging

The exact `d5c009f` checkout was measured on the selected 2018 Mac with
CPython 3.11.15, SQLite 3.53.1, sequential uninstrumented calls and uncontrolled
OS caches. For 100/250 base observations, each warm median uses 100 samples
after the first. For 1,000, nearest-rank p95 includes all 100 samples; the mixed
fixture has 1,006 actual observations and 5,006 observation revisions. Files
`data/core-0201-d5c009f-{memory,sqlite}-{100,250,1000}.json.gz` retain each
sample, source identity and output. The rounded outputs, counts and applied
operations matched between memory and SQLite for every recorded query.

| Base observations | Memory | SQLite | Agreed target |
| --- | --- | --- | --- |
| 100, warm median | 0.076 s | 0.116 s | under 1 s |
| 250, warm median | 0.199 s | 0.300 s | under 1 s |
| 1,000, p95 | 1.223 s | 1.848 s | under 2 s |

All targets passed in this run. Host one/five/fifteen-minute load averages were
2.32/2.15/1.64 at start and 1.75/2.06/1.85 at finish. The host was not isolated;
these synthetic results are not a production guarantee or cold-device study.
The previous candidate's 2.919-second SQLite p95 miss and 1.955-second repeat
remain recorded in Core's `docs/findings/0.20.1-candidate-review.md`.

The exact candidate wheel and sdist passed `twine check`. An isolated Python
3.11 dependency-free wheel install, migration, persistence and restart check
passed. Wheel SHA-256 is
`34e312626340039584952c319c111c5568328a81668bffb71caf7b2200a75bf1`; sdist
SHA-256 is `bd7c01f5d075803f8fe5c29b9ecc759a683005c736360fc681bee31e0ebc3045`.
The [hosted Core CI](https://github.com/cogkura/cogkura/actions/runs/44640933318)
passed all 25 jobs for the exact commit. No tag or package was published.
