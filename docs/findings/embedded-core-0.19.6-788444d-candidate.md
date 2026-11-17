# Core 0.19.6 candidate: independent comparison in progress

Core candidate `788444d7a4d5149ea397852cc4cb13552a7ca278` declares runtime and distribution version `0.19.6`. Bench installed that exact Git commit in an isolated Python 3.12.16 environment on macOS 15.8.1, linked to SQLite 3.53.1, with `PYTHONHASHSEED=0` and the validator's deterministic UUID setup. Bench's correction-profile version guard was updated in `dda0893` before the recorded runs. The accompanying raw reports preserve the module/distribution identity and full comparison data; they are not passing release-gate reports.

## Strict frozen comparison

The [raw report](data/embedded-core-0.19.6-788444d-macos312-frozen.json.gz) and [query details](data/embedded-core-0.19.6-788444d-macos312-frozen-details.json.gz) compare against unchanged gold SHA-256 `927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c`. Of 393 fingerprints, 392 match. The sole difference is `authoritative_corrections_v1/cogkura-correction/ac-q-c20`: the original fingerprint is `79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80` and the candidate fingerprint is `9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe`. Aggregate metrics, use signatures and diagnostics parity match; the independent PostgreSQL source check passed, including 191/191 source assessments. These fingerprints match the previously documented withdrawn-readmission correction, but earlier approvals do not cover this candidate.

## Three-backend raw comparison

The [raw detailed report](data/embedded-core-0.19.6-788444d-macos312-threeway.json.gz) compares in-memory, SQLite, reopened SQLite and PostgreSQL. Mini and persistent-inhibition comparisons match; the PostgreSQL repeat cleanup check also matches. The other two workloads have precisely three different query fingerprints on all three persistent modes: `ac-q-c03`, `sm-contested`, and `sm-evidence-cap`. Their before/after fingerprints exactly match the three supporting-event order differences documented and approved for public 0.19.5 in `tests/reviewed_corrections/order_0195_13ad733.json`. Metrics and use signatures match for all cases and modes. The earlier evidence identified the same support population with different ordering; it does not establish that arbitrary ordering differences can be ignored. The 0.19.5 approval does not apply to this candidate.

## Linux Python matrix

The [raw Linux candidate workflow](https://github.com/cogkura/cogkura-bench/actions/runs/44148371084) completed with failed strict comparisons, as expected for unapproved differences; all five PostgreSQL source checks and the diagnostic checks passed. For Python 3.11.18, 3.12.16, 3.13.18, 3.14.10 and 3.15.2, every candidate frozen run's metrics, use signatures and query fingerprints exactly matches the corresponding public 0.19.5 Linux run. Each backend comparison has the same three supporting-event fingerprint differences listed above; all compared metrics and use signatures match. The reports, full query details and cross-backend raw data for each runtime are retained in `data/embedded-core-0.19.6-788444d-linux-3*-*.json.gz`.

The proposed exact Linux exception lists each frozen difference, environment, unchanged gold digest and candidate identity in [the unapproved proposal](../proposed-0196-788444d-linux-exact-differences.json). The prior public-release acceptance is not reused. This proposal contains no numerical tolerance; it separately requires a candidate-specific approval for the withdrawn-readmission correction. No candidate exception has yet been approved.

## Open work

Candidate-specific approvals, candidate-specific reviewed comparisons, the complete candidate artifact review and performance/scaling dispositions remain pending. No 0.19.6 release has been accepted or published.
