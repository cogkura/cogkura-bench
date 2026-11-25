# Core 0.20.3 `a31f71e`: reviewed frozen comparisons

**The candidate-specific reviewed comparisons passed on the approved Mac and
hosted Linux environments.** The original gold is unchanged, and every raw
frozen comparison remains a failure. This review does not authorize a release,
approve a different candidate or extend approval to other environments.

On 25 November 2026, the release owner approved the exact differences for Core
`a31f71e222dd231ed9643bc1d1cc109e3e8153dd`, as described in the
[Mac proposal](core-0203-a31f71e-review-proposal.md) and
[Linux proposal](core-0203-a31f71e-linux-review-proposal.md). Both decisions
cover the separately identified withdrawn-readmission correction. The dated
[correction manifest](../../tests/reviewed_corrections/cogkura_0203_a31f71e.json),
[Mac exact-field manifest](../../tests/reviewed_corrections/cogkura_0203_a31f71e_macos311_exact.json)
and [Linux exact-field manifest](../../tests/reviewed_corrections/cogkura_0203_a31f71e_linux_exact.json)
record only those decisions.

The strict reviewer verified candidate identity, the original gold digest,
platform and Python scope, the exact correction and all listed fields, and
required diagnostic, PostgreSQL parity and source-history v2 checks. Results:

| Environment | Other exact fields | Reviewed result |
| --- | ---: | --- |
| Reference Mac, macOS 15.8.3 / Python 3.11.15 | 82 | Pass |
| Hosted Linux, Python 3.11.18 | 87 | Pass |
| Hosted Linux, Python 3.12.16 | 17 | Pass |
| Hosted Linux, Python 3.13.18 | 17 | Pass |
| Hosted Linux, Python 3.14.10 | 17 | Pass |
| Hosted Linux, Python 3.15.2 | 17 | Pass |

The Linux platform scope is the exact recorded
`Linux-7.0.0-1020-azure-x86_64-with-glibc2.43` prefix. Raw and reviewed results
are retained separately: [Mac raw](core-0203-a31f71e-frozen-raw.json.gz),
[Mac reviewed](core-0203-a31f71e-macos-reviewed.json.gz),
[Linux raw reports](data/core-0203-a31f71e-linux-v2/), and reviewed Linux
[3.11](core-0203-a31f71e-linux-3.11-reviewed.json.gz),
[3.12](core-0203-a31f71e-linux-3.12-reviewed.json.gz),
[3.13](core-0203-a31f71e-linux-3.13-reviewed.json.gz),
[3.14](core-0203-a31f71e-linux-3.14-reviewed.json.gz), and
[3.15](core-0203-a31f71e-linux-3.15-reviewed.json.gz). The hosted jobs themselves
still report failure in their unapproved strict-raw step; these separate
candidate-specific reviews do not change that historical CI result.
