# Core 0.20.3 release benchmark

On 26 November 2026, released Core 0.20.2 (`fb72911`) and 0.20.3 (`a31f71e`) were run against the same clean Bench commit `86cd97c` on the reference 2018 Mac (macOS 15.8.3, Python 3.11.15, SQLite 3.53.1). The runs used seed 183, `PYTHONHASHSEED=0`, the source-history v2 fixture, diagnostics parity, and separate local PostgreSQL databases. Both Core installations were verified against their official Git origins.

Across 22 dataset/profile runs and 393 query fingerprints, the comparison found **zero changed query fingerprints, use signatures, query details, or non-latency metrics**. Thus all selected scores below are identical in 0.20.2 and 0.20.3. These are fixture-specific metrics, not an aggregate product accuracy score.

| Fixture and metric | 0.20.2 | 0.20.3 | Delta |
| --- | ---: | ---: | ---: |
| Mini: direct recall@10 | 1.000 | 1.000 | 0.000 |
| Software project: associative recall@10 | 0.667 | 0.667 | 0.000 |
| Software project: current / historical temporal accuracy | 1.000 / 1.000 | 1.000 / 1.000 | 0.000 / 0.000 |
| Software project: missing-knowledge F1 | 0.800 | 0.800 | 0.000 |
| Helios: associative recall@10 | 0.333 | 0.333 | 0.000 |
| Helios: current / historical temporal accuracy | 0.500 / 0.750 | 0.500 / 0.750 | 0.000 / 0.000 |
| Helios: missing-knowledge F1 | 0.750 | 0.750 | 0.000 |
| Interference: competition-pair F1 | 0.435 | 0.435 | 0.000 |
| Transient interference v2: interference-effect F1 | 1.000 | 1.000 | 0.000 |

The source-history v2 assessment matched 191 of 191 checks on both releases; PostgreSQL matched its declared results. The older source v1 fixture remains at 190/191, reflecting the previously reviewed withdrawn-readmission correction. Software-project and Helios stale-intrusion rates were 0.067 and 0.033 respectively, unchanged. Helios associative recall and temporal results, and interference competition-pair F1, remain areas for investigation rather than new regressions.

Both raw comparisons against the original frozen gold fail. Applying each release's separately approved exact Mac review (the one correction and 82 specified fields) passes; the frozen gold was not changed. The fresh 0.20.3 backend validation also passed across memory, SQLite, reopened SQLite and PostgreSQL for mini, authoritative corrections, persistent inhibition and source-aware metamemory v1; the mini PostgreSQL repeat matched. The 0.20.3 Bench test suite passed 375 tests with PostgreSQL, and 13 datasets validated across 38 CLI dataset/profile runs.

The paired comparator intentionally excludes latency. These runs do not establish a speed delta or performance equivalence; a controlled timing experiment is required for either claim.

The complete preserved evidence is in [data](data/): `bench-86cd97c-paired-core-0202-{raw,details,reviewed}.json.gz`, `bench-86cd97c-paired-core-0203-{raw,details,reviewed}.json.gz`, `bench-86cd97c-paired-core-0203-backends.json.gz`, and `bench-86cd97c-paired-deltas.json.gz`. Re-run the non-latency comparison using `scripts/compare_core_release_reports.py` with the two raw and detail reports.
