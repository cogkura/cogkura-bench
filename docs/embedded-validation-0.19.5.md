# Embedded storage validation for Core 0.19.5

This independent candidate check adds no dataset or benchmark gold. It compares the existing mini, authoritative-corrections, persistent-inhibition and source-aware-metamemory workloads with the in-memory and SQLite stores, and optionally the complete PostgreSQL storage bundle. The SQLite runs cover both a continuously open owner and closing and reopening the owner after every preparation. The latter retains Bench's event-to-observation mapping between reopenings; it tests Core storage reopening within one Bench process, not restoration of a new Bench process's adapter state.

The script uses the existing CogKura adapter and Core's storage and memory interfaces. It installs a deterministic UUID allocator before importing Core and reseeds it for each run, as in the source-metamemory validator. Independently allocated UUIDs are not guaranteed to be identical across backends. Query fingerprints retain ordered results, evidence and correction observations; use signatures, non-latency metrics and source-assessment observations are compared too. Output includes all raw fingerprints and fails on any difference. Use `--details` to include complete query signatures and observation-ID mappings for investigation; it does not alter the comparison. Existing strict frozen gold and approved-correction checks remain separate.

Run with a Core source checkout at a clean commit or a Git-installed Core distribution, linked to a SQLite release supported by Core. For a source checkout, place its `src` ahead of Bench in `PYTHONPATH`. The output records the loaded module, source commit, distribution identity, Python and SQLite versions. For example:

```bash
PYTHONHASHSEED=0 PYTHONPATH=/path/to/cogkura/src:/path/to/cogkura-bench/src \
  python scripts/run_embedded_freeze_validation.py \
  --postgres-url "$COGKURA_POSTGRES_MEMORY_URL" --verify-postgres-repeat --details \
  --output results/embedded-0.19.5-validation.json
```

To include PostgreSQL, supply `--postgres-url` with a **disposable** database: this applies migrations and clears all fixture tenant data before and after each workload. The raw report compares the full PostgreSQL bundle separately and records all differences. `--verify-postgres-repeat` repeats the mini workload on the same database and checks that cleanup prevents cognitive state leaking into a later run.
The raw run exits with status 1 when it finds the approved order differences; retain its output and run the separate reviewer below. A crash or missing output is not an approved difference.

The earlier 0.19.5 candidate was Core commit `fa9c993d82fd2dda74a9b18f2b80c3b857a26fc7`; its development package metadata still declares 0.18.4. A separate explicit user approval permits the previously reviewed `ac-q-c20` frozen correction only for this exact candidate, in `tests/reviewed_corrections/cogkura_0195_fa9c993.json`. The [strict source-metamemory validator](source-metamemory.md) must be run with that manifest and an exact Git-installed Core distribution. The original frozen baseline and raw mismatch are retained.

The user separately approved three specific SQLite supporting-event order differences for this candidate. `tests/reviewed_corrections/sqlite_order_0195_fa9c993.json` pins the original and observed fingerprints, and `scripts/review_embedded_freeze.py` accounts for those fingerprints in a separate report without changing the original comparison. It requires all four workloads, matching candidate and exact fingerprints, and fails for any other SQLite difference. Neither approval applies to PostgreSQL differences or to other candidates.

After a PostgreSQL learning-cleanup fix, the user separately approved the frozen correction and the same three order differences on SQLite and PostgreSQL for exact Core commit `f289035351e3c101fd932f4d6d9e9cd56583ace0`. The corresponding manifests are `tests/reviewed_corrections/cogkura_0195_f289035.json` and `tests/reviewed_corrections/order_0195_f289035.json`. The latter explicitly lists all three backend modes; the reviewer also checks PostgreSQL query fingerprints, uses, metrics and source observations. Earlier approvals remain restricted to their original candidate.

```bash
python scripts/review_embedded_freeze.py \
  --report results/embedded-0.19.5-validation.json \
  --approval tests/reviewed_corrections/order_0195_f289035.json \
  --output results/embedded-0.19.5-reviewed.json
```

The independent comparison and its diagnosed ordering differences are recorded in Core's 0.19.5 findings. The development lock selects the exact `f289035` commit, although its package metadata remains `0.18.4` until Core's separate release process. It covers four representative workloads, not every dataset or a fresh-process Bench adapter reconstruction. It does not replace Core's full PostgreSQL-enabled gates or the original strict Bench validator.

The original frozen comparison passes under Python 3.12 and 3.13 with the exact approved correction. Under Python 3.11 it reports additional unapproved differences from the original gold; a separate, digest-pinned same-runtime comparison verifies that the previous Core and this candidate have identical results. This diagnostic does not alter or approve the raw differences. See the [independent findings](findings/embedded-core-0.19.5.md) for both reports and the CI boundary.
