# Core 0.19.6 release candidate `9745201`: raw review

This records independent validation of exact Core commit `9745201bfcc5410d678a07737a4c935dd294e5b4`, version `0.19.6`. Its packaged runtime files are byte-identical to the approved `788444d` candidate; documentation and distribution metadata differ. Earlier candidate approvals do not apply automatically. The [raw Linux workflow](https://github.com/cogkura/cogkura-bench/actions/runs/44168447234) retains unapproved strict comparison failures.

On CPython 3.11.18, 3.12.16, 3.13.18, 3.14.10 and 3.15.2, all frozen run values and complete four-backend case outputs exactly match the corresponding recorded `788444d` Linux results. All source diagnostics and PostgreSQL checks pass. Raw reports, detailed query signatures and three-backend comparisons are in `data/embedded-core-0.19.6-9745201-linux-3*-*.json.gz`.

The original gold SHA-256 remains `927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c`. The previously reviewed withdrawn-readmission correction is `authoritative_corrections_v1/cogkura-correction/ac-q-c20`, from `79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80` to `9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe`. The same three supporting-event order differences appear on SQLite, reopened SQLite and PostgreSQL: `ac-q-c03`, `sm-contested` and `sm-evidence-cap`. Their exact fingerprints match the earlier candidate manifest `tests/reviewed_corrections/order_0196_788444d.json`; complete compared case outputs are unchanged. The [unapproved Linux proposal](../proposed-0196-9745201-linux-exact-differences.json) lists every other exact frozen difference by Python version. These are not a general tolerance or approval for any other commit.

The release wheel SHA-256 is `862d1a08b3d939bc1eea81d883c03315a30509c6779e12abec6f5fb85d8252d4`; the sdist SHA-256 is `bc710d5bb4743fff344d011ab0a725128d4e8420eb3411916e0105d716b7c594`. A separate Python 3.12 Bench installation of that wheel produced frozen outputs identical to the prior wheel, with PostgreSQL source diagnostics passing. Its [raw report](data/embedded-core-0.19.6-9745201-macos312-wheel-frozen.json.gz) and [details](data/embedded-core-0.19.6-9745201-macos312-wheel-details.json.gz) identify the installed wheel and retain the unapproved raw failure. Its runtime files match the Git candidate wheel; distribution metadata differs.

On 17 November 2026 the user explicitly approved these exact three classes of differences for `9745201` only. The correction, support-order and Linux field approvals are recorded in `tests/reviewed_corrections/cogkura_0196_9745201.json`, `order_0196_9745201.json` and `cogkura_0196_9745201_linux_exact.json`, respectively. The separate frozen and three-backend reviews pass for all five Python versions and are retained as `data/embedded-core-0.19.6-9745201-linux-3*-*-reviewed.json`. Original gold and raw reports remain intact.

To reproduce one reviewed comparison from a clean checkout (replace `312` for the other versions):

```bash
gzip -dc docs/findings/data/embedded-core-0.19.6-9745201-linux-312-frozen-raw.json.gz > /tmp/core-0196-final-frozen.json
python scripts/review_candidate_frozen_report.py --gold tests/golden/cogkura_0182_frozen.json --raw /tmp/core-0196-final-frozen.json --correction tests/reviewed_corrections/cogkura_0196_9745201.json --exact tests/reviewed_corrections/cogkura_0196_9745201_linux_exact.json --output /tmp/core-0196-final-frozen-reviewed.json
gzip -dc docs/findings/data/embedded-core-0.19.6-9745201-linux-312-threeway-raw.json.gz > /tmp/core-0196-final-threeway.json
python scripts/review_embedded_freeze.py --report /tmp/core-0196-final-threeway.json --approval tests/reviewed_corrections/order_0196_9745201.json --output /tmp/core-0196-final-threeway-reviewed.json
```
