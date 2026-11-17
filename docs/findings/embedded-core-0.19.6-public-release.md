# Published Core 0.19.6: Bench results

Bench was updated to the published Core `0.19.6` Git commit `9745201bfcc5410d678a07737a4c935dd294e5b4` (the `v0.19.6` tag). The local validation used CPython 3.12.13, macOS 15.8.1 x86-64, SQLite 3.53.1 and a disposable PostgreSQL database. Core's module path and installed Git distribution identity were checked. This is development validation of Bench 0.3.12, not a Bench package release.

## Validation

- Locked all-extras installation, Ruff, formatting and MyPy passed. The full PostgreSQL-enabled Bench suite passed **345 tests with no skips**; all 13 datasets validated and mini oracle, token-overlap and CogKura smoke runs passed.
- The [frozen report](data/embedded-core-0.19.6-public-macos312-frozen.json.gz) covers 22 runs and 393 query fingerprints. The unmodified raw comparison retains the previously identified `ac-q-c20` failure; the separately approved exact correction for this published commit is accounted for, leaving no unapproved frozen differences. Diagnostics parity and the PostgreSQL check passed, including 191/191 source-assessment checks. [Query details](data/embedded-core-0.19.6-public-macos312-frozen-details.json.gz) remain available.
- All stored run metrics, use signatures and query fingerprints match the retained [public Core 0.19.5 comparison](data/embedded-core-0.19.5-release-frozen-312-raw.json). This comparison excludes latency; it does not establish performance equivalence under all workloads.
- The [raw backend report](data/embedded-core-0.19.6-public-macos312-threeway-raw.json.gz) records the same three supporting-event ordering differences among in-memory, SQLite, reopened SQLite and PostgreSQL. The [reviewed result](data/embedded-core-0.19.6-public-macos312-threeway-reviewed.json) passes with the exact commit-specific approvals and no other mismatches. PostgreSQL repeat cleanup passes. These are four representative workloads, not exhaustive backend equivalence.
- Independent Linux validation for Python 3.11–3.15 and the exact frozen and support-order approvals are retained in the [release-commit review](embedded-core-0.19.6-9745201-release-candidate.md). The strict raw Linux workflow remains failed; its reviewed results are separate.

## Selected retrieval results

These scores apply to the named fixture queries and the default `cogkura` profile. Recall@10 measures expected evidence recovered; precision@10 measures the relevant fraction of returned evidence. They are not aggregate product accuracy or independent model evaluation.

| Dataset | Capability | Recall@10 | Precision@10 |
|---|---|---:|---:|
| mini | Direct recall | 1.000 | 0.667 |
| mini | Episodic recall | 1.000 | 0.500 |
| software_project_v1 | Direct recall | 1.000 | 0.367 |
| software_project_v1 | Associative recall | 0.667 | 0.467 |
| helios_v1 | Direct recall | 0.833 | 0.300 |
| helios_v1 | Associative recall | 0.333 | 0.233 |

The controlled `transient_interference_v2` enabled profile recorded effect precision and recall of 1.0 with zero temporal or sign violations. The `persistent_inhibition_v1` enabled profile recorded effect precision/recall and scope isolation of 1.0, with no future-trace or out-of-scope violations. These use explicitly enabled configurations, not default-on behavior. In `source_authority_v1`, the authority-enabled profile recorded admission precision and recall of 1.0. In `authoritative_corrections_v1`, the correction-enabled profile recorded state, retrieval and temporal-boundary accuracy of 1.0, with zero incorrect-current, incorrect-historical, stale-context or knowledge-time-leak counts.

## Performance boundary

Bench fixture scores are not an uninstrumented performance benchmark. Core's separate [0.19.6 stabilisation findings](https://github.com/cogkura/cogkura/blob/v0.19.6/docs/findings/0.19.6-embedded-stabilisation.md) report one mixed 1,000-observation workload taking approximately 83 seconds for one recall on both SQLite and in-memory storage on a 2018 MacBook Pro. That single exploratory sample indicates an important scaling limit; it does not isolate hardware from implementation cost or establish production latency.
