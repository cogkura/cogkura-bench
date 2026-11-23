# Core 0.20.2 `fb72911`: reviewed frozen gate

**The candidate-specific reviewed gate passed on the reference Mac with
Python 3.11.15 and macOS 15.8.3.** The original raw comparison still fails;
the frozen gold is unchanged. This decision does not approve other candidates
or environments.

On 23 November 2026 the user approved the exact differences described in the
[review proposal](core-0202-fb72911-review-proposal.md): one correction and
82 other fields for Core `fb72911ce58173bf3669181d0e2c25eeefeaa58d`. The
dated [correction approval](../../tests/reviewed_corrections/cogkura_0202_fb72911.json)
and [exact-field approval](../../tests/reviewed_corrections/cogkura_0202_fb72911_macos311_exact.json)
apply only to that candidate and environment.

The first review attempt correctly rejected the draft's inherited macOS
15.8.1 platform prefix: the current reference machine reported macOS 15.8.3.
The approved exact-field manifest was corrected to the observed platform and
the strict reviewer then passed. The [raw report](core-0202-fb72911-official-raw.json.gz)
and [reviewed report](core-0202-fb72911-official-reviewed.json.gz) are separate;
the reviewed report retains `raw_frozen_comparison_passed: false`. The reviewer
verified the exact official Git identity, original gold digest, environment,
diagnostics, PostgreSQL and source-history checks, the one correction and all
82 other exact before/after fields.
