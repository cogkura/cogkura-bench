# Core 0.20.2 `64f85f7`: reviewed frozen gate

**The candidate-specific reviewed frozen gate passed on the reference Mac with
Python 3.11.15.** The original raw frozen comparison still fails; the gold is
unchanged. This result does not approve release or extend to other candidates
or environments.

On 22 November 2026, the user explicitly approved the exact differences in the
[review package](core-0202-64f85f7-review-proposal.md): one withdrawn-readmission
correction and 82 other exact fields for Core
`64f85f78acd2046cafe0212c84b45c1d221affd4`. The dated approvals are the
[correction manifest](../../tests/reviewed_corrections/cogkura_0202_64f85f7.json)
and [macOS/Python 3.11.15 exact-field manifest](../../tests/reviewed_corrections/cogkura_0202_64f85f7_macos311_exact.json).

The strict reviewer passed against the [official-origin raw report](core-0202-64f85f7-official-raw.json.gz)
and the unchanged original gold. It verified the exact official Git identity,
gold digest, reference environment, seed, diagnostics, PostgreSQL and source
history, one approved correction, and all 82 other exact before/after fields.
The [separate reviewed report](core-0202-64f85f7-official-reviewed.json.gz)
retains `raw_frozen_comparison_passed: false` and records the passing reviewed
comparison. Source-history v2 matched 191/191 checks. The independent hosted
Linux candidate jobs still have their unapproved raw failures; the macOS
approval is not an approval for Linux.
