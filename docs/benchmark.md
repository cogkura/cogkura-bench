# Benchmark methodology

CogKuraBench evaluates memory systems in two layers:

```mermaid
flowchart TB
    History["Identical events, timestamps, queries, and limits"] --> LayerA["Layer A memory evaluation"]
    LayerA --> Scores["Per-capability scores on benchmark event IDs"]
    Scores -.-> LayerB["Layer B downstream reasoning<br/>future optional LLM pass"]
```

## Layer A — memory evaluation (0.1.0)

No LLM required. Measures evidence retrieval, ranking, temporal correctness, updates, forgetting, working-memory selection, learning, and metamemory where supported.

## Layer B — downstream reasoning (future)

Optional LLM evaluation using identical retrieved context across backends.

## Principles

- All backends receive identical events, timestamps, queries, and limits.
- Ground truth is checked into the repository and versioned.
- Expected evidence refers to benchmark event IDs, not backend-internal IDs.
- No single benchmark score: capability scores are reported separately.
