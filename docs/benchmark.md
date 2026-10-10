# Benchmark methodology

CogKuraBench evaluates memory systems in two layers:

```mermaid
flowchart TB
    History["Identical events, timestamps, queries, and limits"] --> LayerA["Layer A memory evaluation"]
    LayerA --> Scores["Per-capability scores on benchmark event IDs"]
    Scores -.-> LayerB["Layer B downstream reasoning<br/>future optional LLM pass"]
```

## Layer A — memory evaluation (0.2.0)

No LLM required. Measures evidence retrieval, ranking, temporal correctness, updates, forgetting, working-memory selection, learning, metamemory, competition diagnostics, transient behavioural interference, and persistent inhibition where supported. Primary top-K metrics count ranked `RetrievedItem` groups. Competition diagnostics (0.3.4+) measure relationship detection; transient interference (0.3.5) measures bounded suppression via the `cogkura-interference` profile. Persistent inhibition (0.3.6) measures explicit use, scoped traces, and later recovery via `cogkura-inhibition`. Retrieval alone does not count as use.

## Layer B — downstream reasoning (future)

Optional LLM evaluation using identical retrieved context across backends.

## Principles

- All backends receive identical events, timestamps, queries, and limits.
- Ground truth is checked into the repository and versioned.
- Expected evidence refers to benchmark event IDs, not backend-internal IDs.
- No single benchmark score: capability scores are reported separately.
