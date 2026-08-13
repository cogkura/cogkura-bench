# CogKuraBench

CogKuraBench is an open benchmark for evaluating how AI memory systems retain, retrieve, update, forget and use information over time.

## Architecture

```text
Longitudinal project history
        ↓
Memory backend
        ↓
Retrieval / context / assessment
        ↓
Ground truth
        ↓
Capability metrics
```

## Installation

```bash
uv sync --dev --locked
```

Optional CogKura backend (Phase 3+):

```bash
uv sync --dev --locked --extra cogkura
```

## Quick start

```bash
uv run cogkura-bench datasets
uv run cogkura-bench validate-dataset mini
uv run cogkura-bench run --dataset mini --backend oracle
uv run cogkura-bench run --dataset mini --backend token-overlap
uv run cogkura-bench run --dataset mini --backend cogkura   # requires --extra cogkura
uv run cogkura-bench compare cogkura token-overlap --dataset mini
uv run cogkura-bench demo --backend cogkura
uv run cogkura-bench inspect direct-001 --backend cogkura --dataset mini
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/benchmark.md`](docs/benchmark.md)
- [`docs/metrics.md`](docs/metrics.md)
- [`docs/scenarios.md`](docs/scenarios.md)
- [`docs/backends.md`](docs/backends.md)
- [`docs/roadmap.md`](docs/roadmap.md)

## License

Apache 2.0. See [LICENSE](LICENSE).
