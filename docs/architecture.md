# Architecture

CogKuraBench separates benchmark domain models, backend adapters, metrics, and evaluation.

```text
datasets/
    ↓
BenchmarkDataset + action stream
    ↓
BenchmarkRunner (simulated clock, future-leakage enforcement)
    ↓
MemoryBackend (neutral protocol)
    ↓
RetrievedItem (benchmark event IDs)
    ↓
Metrics + BenchmarkResult
```

Dependency direction:

```text
CogKuraBench
      ├── benchmark domain
      ├── datasets
      ├── metrics
      ├── evaluation
      └── backend adapters
              ├── Oracle (validation)
              ├── token overlap
              ├── full history
              └── CogKura (optional extra, simulated-time stores)
```

CogKuraBench is a consumer of memory systems, not part of CogKura.
