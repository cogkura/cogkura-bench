# Independent validation for Core 0.20.2

This is an in-progress procedure, not an approval of a candidate or its frozen
output. The Bench development lock still pins the published 0.19.6 Git commit;
install the exact 0.20.2 candidate distribution in an isolated environment and
verify its version, Git origin and commit before candidate validation. A
source checkout run is exploratory and cannot replace candidate-artifact checks.
The original gold and raw reports must not be edited.

Use supported Python versions and disposable PostgreSQL databases. The frozen
runner and backend runner clear their fixture tenants; use separate databases.
Run the full Bench checks in `AGENTS.md` against the candidate, retaining skipped
checks and failures in the findings. Capture raw frozen output and query details
without reusing an earlier candidate's approval:

```bash
PYTHONHASHSEED=0 python scripts/run_source_metamemory_validation.py \
  --diagnostics-parity --postgres --source-history-v2 \
  --details-output results/core-0202-frozen-details.json \
  --output results/core-0202-frozen-raw.json
```

Set `COGKURA_POSTGRES_MEMORY_URL` to the disposable database before running the
command. A nonzero exit does not authorize discarding a raw mismatch. Investigate
all differences and seek exact candidate-specific review where required. The
0.20.1 correction and platform manifests name a different candidate and do not
approve 0.20.2. Selecting the versioned v2 source fixture defines that
fixture's expectations; it does not approve differences in the frozen gold.

Run four-backend parity with a separate disposable database:

```bash
PYTHONHASHSEED=0 python scripts/run_embedded_freeze_validation.py \
  --postgres-url "$COGKURA_POSTGRES_MEMORY_URL" --details \
  --output results/core-0202-backends-raw.json
PYTHONHASHSEED=0 python scripts/run_embedded_freeze_validation.py \
  --dataset mini --postgres-url "$COGKURA_POSTGRES_MEMORY_URL" \
  --verify-postgres-repeat --details --output results/core-0202-mini-repeat.json
```

Record source identity, host and Python version. Preserve complete raw outputs
and any separately reviewed exact comparisons. The existing [0.20.1-source
baseline](findings/core-0202-baseline-backends.md) is evidence for the released
baseline only; no 0.20.2 candidate has passed this procedure yet.

## Compatibility probe

The 0.20.2 allowlist, v2 fixture selection and refusal to reuse the 0.20.1
approval were exercised against an installed **synthetic version probe** on
CPython 3.15.2: 31 relevant Bench tests passed and one skipped. The probe was
built from Core commit `a62196b8ec37ca07f36900ea6173514083ae7d40` after
changing only its package and runtime version strings from 0.20.1 to 0.20.2.
Its temporary wheel SHA-256 was
`ad29a8e3ecff445e31b656b3c50d944aae59f789d92026d5411109e2f44f7f92`.
This verifies version routing against the old runtime; the probe is not a
0.20.2 candidate, an approved frozen comparison, or a release artifact.
