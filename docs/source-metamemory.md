# Source-aware metamemory validation (0.3.11 candidate)

Bench 0.3.12 now pins Core 0.18.4 `93cb7f6a6daae30333008600f3556e6af4f99b3d`.
The preceding 0.3.11 validation pinned Core 0.18.3 `4d3ba73`, including the approved
slot evidence ordering fix. The source-assessment contracts below are retained.
The source fixture extends the existing action stream and scoring pipeline. It
uses public Core APIs; it does not implement another memory or authority engine.

`cogkura-source-control` and `cogkura-source` both use recurrence threshold 2,
explicit source authority, corrections, and source inspection. Only the latter
enables pass-local semantic decision diagnostics. Earlier profiles keep their
previous settings, datasets and scoring. Oracle's source capability is N/A.

```bash
uv sync --all-extras --dev --locked
uv run cogkura-bench validate-dataset source_aware_metamemory_v1
uv run cogkura-bench run --dataset source_aware_metamemory_v1 --backend cogkura-source-control --quiet
uv run cogkura-bench run --dataset source_aware_metamemory_v1 --backend cogkura-source --quiet
```

`source_inspection` declares subject, predicate, scalar qualifiers, limits,
optional context assessment and an optional historical `as_of`. It contains no
gold answer. The runner combines it with tenant, storage subject and simulated
time. `expected_source_assessment` contains named checks and optional diagnostic
checks. Only metrics consume it. Explicit `null` means expected unknown/N/A;
omission means no assertion. Typoed field names, malformed bounds, unknown event
references and future knowledge requests are rejected.

The adapter maps observation ID **and revision** to fixture event ID. It never
falls back to the latest source event. Slot state and evidence adequacy are
separate. Episodic relation coverage is not applicable; an unresolved semantic
relation is unknown. Distinct records do not imply independent sources. History
is unavailable unless the public output can establish it. Decisions are only the
immediately preceding pass, including withdrawal replay deferrals. They do not
form a durable unresolved-request inventory.

The inherited 0.18.2 limitation remains: re-adoption prose can appear in context
while the semantic assertion stays withdrawn. Source inspection does not add a
retrieval suppression policy or infer an application's abstention decision.

## Release validator

Use a disposable PostgreSQL database. Tests apply migrations and database
validation clears the source fixture's tenant scopes. The CI matrix provides
PostgreSQL and installs all extras. Without a URL, parity is NOT EXECUTED.

```bash
export COGKURA_POSTGRES_MEMORY_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cogkura_bench
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -r s
PYTHONHASHSEED=0 uv run python scripts/run_source_metamemory_validation.py \
  --diagnostics-parity --postgres \
  --output results/source-metamemory-0.3.11-validation.json
```

The validator must start before Core is imported. It supplies a seeded
standard-library UUID allocator before Core imports, solely to control storage
identity allocation. It does not patch Core methods or change cognitive rules.
Hash seed 0 controls iteration order. This preserves exact output comparisons,
including episode text and tied ranks, instead of sorting away retrieval changes.
The random-ID comparison and its known variability are documented in findings.

The frozen fingerprint file records 393 per-query signatures across 22 runs of
all earlier fixtures/profiles. Each signature includes rank, evidence, text,
scores, activation components, neutral diagnostics, semantic observations, old
counters and rendered correction context. Explicit use results and non-latency
metrics are also checked. Wall-clock latency and internal UUID metadata are not
identities. The baseline imported unchanged Core `1a8bc04` source; fixture ground
truth was not edited. `--write-baseline` is for a deliberate baseline capture,
not for making a failing comparison pass.

Diagnostics parity checks all 22 earlier runs plus both new source profiles.
PostgreSQL compares neutral reports, retaining exact capped event identities.
Pytest separately verifies supported coverage/state contracts and now asserts
exact capped source selection between backends. Core regression tests also
compare ordered namespace/record/revision prefixes under opposite UUID-derived
stored sequences. The release validator retains its original stricter comparison.

**0.3.11 / Core 0.18.3 result:** the strict validator passed after the canonical
ordering fix, with all 393 frozen signatures unchanged. See its retained
[findings](findings/source-aware-metamemory-0.3.11.md).

**0.3.12 / Core 0.18.4 candidate:** the separately approved stale-readmission
correction intentionally removes current prose at `ac-q-c20`. The unmodified raw
comparison must report this fingerprint change. All other source/frozen/diagnostics
comparisons are required to pass; an exact scoped exception requires separate
approval. See the [review](review-0.18.4-withdrawn-readmission-deviation.md) and
[candidate findings](findings/source-provenance-freeze-0.3.12.md).
