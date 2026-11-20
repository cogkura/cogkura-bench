# Candidate-population scoring experiment

Date: 20 November 2026. Diagnostic evidence, not a release approval or replacement baseline.

## Method

Core `d5c009faae3e90d63c44196b2e91c6c77412ef9b` was installed from the official Git origin. The two scoring runs used fresh Python 3.12.16 processes, `PYTHONHASHSEED=0`, deterministic UUID seed 183, the same 22 dataset/profile runs and the same Core candidate. The IDF-off process locally sets the existing public `ActivationConfig(enable_candidate_idf=False)` when constructing `Memory`; it does not alter Core or Bench defaults. The default experiment reproduced the saved candidate fingerprints. Source-aware v2 was additionally run in each mode.

The detailed [default](data/scoring-0201-default-policy.json.gz) and [IDF-off](data/scoring-0201-idf-off-config.json.gz) records and [comparison](data/scoring-0201-scoring-diff.json.gz) preserve the individual outcomes. The comparison counts query/profile outcomes, not unique natural-language queries.

## Results

Of 393 query/profile outcomes, 361 signatures change, 25 retrieved-item identity/order sequences change, four flattened retrieved-event sequences change, and one context item selection changes. Eight query/profile metric outputs, six aggregate metric runs and six recorded-use runs change. The distinction between item order and flattened event IDs matters: the latter alone understates the ranking impact. Relative to the 0.20.0 successor gold there are three default fingerprint differences and 363 with IDF off; neither count is an approval decision.

Examples: `helios-forget-003` precision@5 falls from 0.4 to 0.2 and nDCG@5 from 0.5013 to 0.4307. For `helios-temporal-curr-003`, nDCG@3 rises from 0.3869 to 0.6309 while precision@5 falls from 0.4 to 0.2. For `pi-db` in each of three profiles, precision@5 falls from 0.4 to 0.2 and nDCG@5 from 0.5013 to 0.2641. `atlas-wm-001` changes its selected context from six items to five. Recorded-use differences include inhibition and induction-pressure state. Source-aware v2 passes 191/191 in both modes and its per-query source assessments match, but this does not establish historical-time safety or general quality parity.

A separate four-workload IDF-off check covered memory, SQLite, SQLite reopen and disposable PostgreSQL, with a repeat for mini. The [raw backend results](data/scoring-0201-idf-off-backends.json.gz) and [review](data/scoring-0201-idf-off-backend-review.json.gz) match after normalizing only supporting-event order. Nine query/backend cases have those already-known order differences; ordered results are not identical and normalization is not release approval.

A small exploratory 250-observation in-memory comparison used 30 sequential queries per mode. The median of the last 29 was 0.2331 seconds with default IDF and 0.2256 seconds with IDF off. See [default timing](data/scoring-0201-idf-default-perf.json.gz) and [IDF-off timing](data/scoring-0201-idf-off-perf.json.gz). These are uncontrolled sequential runs and cannot establish a meaningful performance advantage or satisfy the release performance targets.

## Temporal boundary finding

The same-tenant later-episode probe fails earlier `as_of`-only recall with `ValidationError: Memory reference cannot occur after the activation timestamp.` This reproduces for both IDF modes in memory, SQLite and PostgreSQL on [0.20.0](data/scoring-0200-temporal-three.json.gz) and [0.20.1](data/scoring-0201-temporal-three.json.gz). The earlier result remains unchanged after adding a different tenant's record, and after adding the later record when the fixture supplies the earlier `valid_at`. This is an inherited, separate issue; `as_of` and `valid_at` are not generally interchangeable. The Core historical-candidate regression tests now cover the fix; this evidence records the behavior of the earlier candidates.

## Reproduction

Use an isolated environment with the exact candidate installed from the official Git source and Bench dependencies. From the Bench root, with Python and SQLite versions recorded by the reports:

```sh
PYTHONHASHSEED=0 python scripts/experiment_stable_scoring.py --policy default --output /tmp/default.json
PYTHONHASHSEED=0 python scripts/experiment_stable_scoring.py --policy idf-off --output /tmp/idf-off.json
python scripts/compare_scoring_experiments.py --default /tmp/default.json --alternative /tmp/idf-off.json --output /tmp/scoring-diff.json
python scripts/experiment_temporal_scoring.py --output /tmp/temporal.json
python -m pytest -q --no-cov tests/unit/test_scoring_population_experiment.py
```

The optional PostgreSQL temporal probe and backend experiment require a dedicated disposable database; their fixture tenants are cleared. Use `--help` on `experiment_temporal_scoring.py` and `experiment_stable_backends.py` before running them. The 0.20.0 temporal comparison used the editable `b30433c` candidate checkout; the 0.20.1 report records the official installed Core origin. The proposed policy and remaining work are described in [Core's design note](../../../cogkura/docs/design-scoring-population-contract.md).

## Local fix validation — 20 November 2026

The local Core fix, committed as `7f945cd` after validation against the working tree based on `d5c009f`, excludes candidates containing future cognitive evidence before scoring. The original temporal probe passes in memory, SQLite and PostgreSQL with IDF enabled and disabled: [probe output](data/historical-fix-temporal.json.gz). The fix conservatively omits a mixed-time episode or semantic aggregate when it cannot reconstruct a safe historical snapshot; this can omit evidence that was already known.

The same 22 default dataset/profile runs produced 393 query/profile outcomes: none of the query signatures, aggregate metric or recorded-use outputs changed from the earlier `d5c009f` run, and the source-aware v2 assessments matched. [Full local output](data/historical-fix-local-run.json.gz) and the [comparison and source hashes](data/historical-fix-review.json.gz) retain the evidence. The run imported modified local source; installed distribution metadata still names the base Git commit and `installed_module` is false. It is not an official candidate run or an approval of the three previously rejected differences. Release performance and independent validation must be rerun for any resulting candidate.
