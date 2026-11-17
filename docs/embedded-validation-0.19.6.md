# Embedded validation for published Core 0.19.6

Bench's development lock selects Core `0.19.6` commit `9745201bfcc5410d678a07737a4c935dd294e5b4`, which is the published `v0.19.6` tag. The optional dependency floor is `0.19.6`; the exact frozen approvals below apply only to this commit and version, the original gold digest, named fingerprints and explicitly listed Linux values. A later release requires its own review.

Install and test with a supported SQLite runtime and a disposable PostgreSQL database:

```bash
uv sync --all-extras --dev --locked
export COGKURA_POSTGRES_MEMORY_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/DISPOSABLE_DB
uv run pytest
```

For a strict frozen run with diagnostics and PostgreSQL enabled, use a fresh process and preserve both the raw report and query details:

```bash
PYTHONHASHSEED=0 uv run python scripts/run_source_metamemory_validation.py \
  --diagnostics-parity --postgres \
  --approved-corrections tests/reviewed_corrections/cogkura_0196_9745201.json \
  --details-output results/core-0196-frozen-details.json \
  --output results/core-0196-frozen.json
```

The command may exit 1 on Linux because the original gold also has separately reviewed platform-specific differences. Do not discard that report or change the gold. On the explicitly approved Linux CPython patch versions, run:

```bash
uv run python scripts/review_frozen_exact_differences.py \
  --gold tests/golden/cogkura_0182_frozen.json \
  --report results/core-0196-frozen.json \
  --approval tests/reviewed_corrections/cogkura_0196_9745201_linux_exact.json \
  --output results/core-0196-frozen-reviewed.json
```

The reviewer fails for a different Core commit, Python patch version, unexpected or missing differences, failed PostgreSQL/source diagnostics, or a changed gold digest. It uses exact values rather than a general tolerance.

For backend parity, use a **separate, empty disposable database**: the harness migrates it and clears fixture tenant data. `--verify-postgres-repeat` verifies cleanup between runs.

```bash
PYTHONHASHSEED=0 uv run python scripts/run_embedded_freeze_validation.py \
  --postgres-url postgresql+asyncpg://USER:PASSWORD@localhost:5432/SEPARATE_DISPOSABLE_DB \
  --verify-postgres-repeat --details --output results/core-0196-backends-raw.json
uv run python scripts/review_embedded_freeze.py \
  --report results/core-0196-backends-raw.json \
  --approval tests/reviewed_corrections/order_0196_9745201.json \
  --output results/core-0196-backends-reviewed.json
```

The raw comparison records known supporting-event ordering differences, so it exits 1 before the separate reviewed comparison. It tests memory, SQLite, SQLite with close/reopen, and PostgreSQL across four representative workloads; it is not an assertion that every Core behavior has been duplicated in Bench. Fresh-process SQLite persistence is checked separately in the Bench integration suite.

See the [public 0.19.6 Bench findings](findings/embedded-core-0.19.6-public-release.md) and [release-commit review](findings/embedded-core-0.19.6-9745201-release-candidate.md) for raw and reviewed reports, wheel identity and approval details. The [0.19.5 guide](embedded-validation-0.19.5.md) remains historical; its approval manifests do not authorise 0.19.6.
