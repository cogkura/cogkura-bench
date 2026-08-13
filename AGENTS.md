# CogKuraBench — agent guide

Primary entry point for coding agents working in this repository.

## What this repo is

CogKuraBench is a deterministic benchmark and demonstration framework for evaluating long-term AI memory systems.

The benchmark owns:

- benchmark datasets;
- scenario ground truth;
- neutral backend contracts;
- benchmark execution;
- metrics;
- reports.

It does **not** own:

- CogKura algorithms;
- external memory implementations;
- LLM reasoning behaviour.

## Read first

For substantive changes:

1. [`AGENTS.md`](AGENTS.md) (this file)
2. [`README.md`](README.md)
3. [`docs/architecture.md`](docs/architecture.md)
4. [`docs/benchmark.md`](docs/benchmark.md)
5. [`docs/metrics.md`](docs/metrics.md)
6. [`docs/scenarios.md`](docs/scenarios.md)
7. [`docs/roadmap.md`](docs/roadmap.md)

If working from a design note or PRD, read that as well.

## Design note versus repository

> Use the Design Note for intended concepts, behaviour and acceptance criteria. Use the repository for existing naming, layout, protocols and API shape.

Therefore:

- extend existing modules rather than inventing parallel abstractions;
- do not restructure stable public APIs unless required;
- do not duplicate concepts under different names;
- update documentation after implementation to describe what actually shipped.

## Benchmark invariants

These are hard constraints:

- deterministic benchmark runs must not depend on external APIs;
- future events must never be visible to earlier queries;
- benchmark timestamps come from the simulated clock;
- released dataset ground truth must not be silently changed;
- metrics operate on neutral benchmark models;
- backend-specific details remain inside backend adapters;
- expected evidence refers to benchmark event IDs;
- the CogKura adapter uses CogKura's public API;
- the benchmark must not alter CogKura behaviour;
- unsupported backend capabilities remain unsupported;
- OracleBackend is validation infrastructure, not a competitor;
- benchmark changes must not be made merely to improve CogKura's score.

## Commands (match CI)

```bash
uv sync --extra cogkura --dev --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest

uv run cogkura-bench validate-dataset mini
uv run cogkura-bench run --dataset mini --backend oracle --quiet
uv run cogkura-bench run --dataset mini --backend token-overlap --quiet
uv run cogkura-bench validate-dataset software_project_v1
uv run cogkura-bench run --dataset software_project_v1 --backend oracle --quiet
uv run cogkura-bench validate-dataset helios_v1
uv run cogkura-bench run --dataset helios_v1 --backend oracle --quiet
uv run cogkura-bench run --dataset mini --backend cogkura --quiet
```

## Agent completion contract

An agent must not consider substantive work complete after implementation alone.

Expected flow:

```text
implementation
    ↓
tests
    ↓
Ruff
    ↓
format check
    ↓
MyPy
    ↓
Pytest
    ↓
dataset validation
    ↓
golden benchmark
    ↓
relevant smoke benchmark
    ↓
documentation
```

The completion response should state:

- what changed;
- what tests were added;
- which validation commands passed;
- whether benchmark scores changed;
- any remaining limitations.

Do not commit or push unless explicitly instructed.
