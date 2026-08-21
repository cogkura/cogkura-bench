# Architecture

CogKuraBench separates benchmark domain models, backend adapters, metrics, and evaluation. New-user install and first-run steps are in the [README](../README.md).

```mermaid
flowchart LR
    DS["datasets/"] --> Dataset["BenchmarkDataset<br/>action stream"]
    Dataset --> Runner["BenchmarkRunner"]
    Runner --> Clock["Simulated clock<br/>no future leakage"]
    Clock --> Backend["MemoryBackend"]
    Backend --> Items["RetrievedItem<br/>benchmark event IDs"]
    Items --> Result["Metrics and BenchmarkResult"]
```

Dependency direction:

```mermaid
flowchart TB
    Bench["CogKuraBench"]
    Bench --> Domain["Benchmark domain"]
    Bench --> Datasets["Datasets"]
    Bench --> Metrics["Metrics"]
    Bench --> Evaluation["Evaluation"]
    Bench --> Adapters["Backend adapters"]
    Adapters --> Oracle["oracle"]
    Adapters --> Token["token-overlap"]
    Adapters --> Full["full-history"]
    Adapters --> Cogkura["cogkura extra"]
```

CogKuraBench is a consumer of memory systems, not part of CogKura.
