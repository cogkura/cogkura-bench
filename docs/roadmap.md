# Roadmap

## 0.1.0

- [x] Engineering scaffold
- [x] Benchmark kernel and mini dataset
- [x] CogKura backend adapter
- [x] Specialized cognitive metrics
- [x] Project Atlas (`software_project_v1`)
- [x] Project Helios (`helios_v1`) messy-history stress dataset
- [x] Demo, inspect, compare commands

## 0.1.1

- [x] Correct CogKura `missing_knowledge` metamemory mapping
- [x] Preserve optional CogKura retrieval diagnostics on `RetrievedItem.metadata`
- [x] Persist retrieved/context items in results and JSON
- [x] Richer `inspect` output for query gold, cues, and per-item diagnostics

## 0.2.0

- [x] Grouped retrieval scoring: top-K over `RetrievedItem` rank positions
- [x] Grouped temporal, update, forgetting, and learning rank metrics

## 0.3.0

- [x] Customer Decision Context dataset (`customer_decision_context_v1`)
- [x] Evidence-group diagnostics and retrieve-vs-select stage classification
- [x] Commerce event types, `session_id`, semantic validity fields
- [x] CogKura 0.15.x adapter updates

## 0.3.1

- [x] CogKura raw/mapped recall and context diagnostics
- [x] Lifecycle and memory-inventory diagnostic tooling
- [x] Customer decision-context lifecycle findings

## 0.3.2

- [x] Customer decision-context fixture integrity (session fallback, lightweight semantic fact)
- [x] Generator session inspection and fixture-integrity tests
- [x] Customer decision-context 0.3.2 findings

## 0.3.3

- [x] Customer decision-context structured relationship fixture (`EntityRelationship`, catalogue `is_a` edges)
- [x] CogKura relationship ingest and `inspect_recall` diagnostics in backend metadata
- [x] Customer decision-context 0.3.3 findings (A/B/C attribution)

## 0.3.4

- [x] Competition diagnostics benchmarking (`Capability.INTERFERENCE`)
- [x] `interference_v1` controlled fixture and CogKura 0.17.x adapter mapping
- [x] Interference 0.3.4 findings

## Future

- Vector/RAG baseline
- External memory backends (Mem0, Letta, Graphiti, LangMem, Supermemory)
- Optional LLM downstream evaluation layer
- External benchmark adapters (LongMemEval, MemoryAgentBench)
