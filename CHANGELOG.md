# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] - 2026-08-26

### Added

- CogKura raw-versus-provenance-mapped recall and bounded-context diagnostics in `backend_metadata` / `context_backend_metadata`.
- CogKura lifecycle counters, prepare/maintenance summaries, and public memory inventory via `diagnostic_snapshot()`.
- Customer decision-context lifecycle diagnostic matrix (`scripts/diagnose_customer_decision_lifecycle.py`, `cogkurabench.diagnostics.lifecycle`).
- `EnvironmentInfo.git_dirty` for reproducibility metadata.
- `QueryResult.context_backend_metadata` JSON persistence and backend-neutral inspect metadata rendering.

### Fixed

- CogKura 0.15 optional retrieval diagnostics now read from `RecallResult.diagnostics`.
- Bounded context mapping preserves `WorkingMemoryItem` selected ranks and selector funnel counters.
- Customer decision-context 0.3.0 findings commit metadata and lifecycle description.

### Unchanged

- Benchmark scoring, dataset evidence groups, default replay/maintenance semantics, and CogKura algorithms.

## [0.3.0] - 2026-08-26

### Added

- **Customer Decision Context** dataset (`customer_decision_context_v1`: 149 events, 1 query) for bounded working-memory diagnostics in a customer-memory / outdoor-retail domain.
- **Evidence groups:** `EvidenceGroup`, `expected_evidence_groups` / `forbidden_evidence_groups` on `BenchmarkQuery`, and `evidence_group_*` metrics with per-group stage classification (`selected`, `selection_drop`, `retrieval_miss`, `context_only`).
- Commerce-oriented `EventType` values, optional `session_id` on `ProjectEvent`, and optional `valid_from` / `valid_until` on `SemanticFact`.
- Evidence-group tables in `inspect`, JSON persistence, `compare` summary, and markdown run summaries.
- Oracle group-aware retrieval: first declared event ID per expected group, then remaining flat expected IDs.
- CogKura adapter: `session_id` metadata, semantic validity fields, docstring for 0.15.x.

### Changed

- CogKura extra requires `cogkura>=0.15.0,<0.16.0`.
- When a backend does not return bounded context, evidence-group stages do not emit fake `selection_drop` for broad-recall hits.

### Unchanged

- `ProjectEvent` name and `schema_version` 1 dataset compatibility.
- Existing mini, Atlas, and Helios dataset semantics and golden expectations.
- Grouped retrieval scoring from 0.2.0.

## [0.2.0] - 2026-08-23

### Changed

- **Grouped retrieval scoring:** top-K primary metrics (`recall@K`, MRR, nDCG, temporal/update/forgetting/learning rank metrics) now count ranked `RetrievedItem` groups. A multi-source memory item occupies one rank position.
- `memories_retrieved` and `memories_selected` efficiency counts use retrieved/context items, not flattened source events.

### Unchanged

- Released datasets, gold IDs, forbidden IDs, and backend adapters.
- Oracle, token-overlap, and full-history primary scores (one source per item).
- Working-memory budget coverage and metamemory scoring.
- `RetrievedItem.metadata` remains observational only.

## [0.1.1] - 2026-08-15

### Fixed

- CogKura `missing_knowledge` assessment flag now maps to neutral `indicates_missing_knowledge=True`.

### Added

- Optional CogKura retrieval diagnostic metadata on `RetrievedItem.metadata`.
- `retrieved_items` and `context_items` on `QueryResult` for JSON and inspect output.
- Richer single-query inspection: query id, structured cues, acceptable/forbidden evidence, per-item score, type, and metadata.

### Changed

- CogKura extra requires `>=0.14.4,<0.15.0`.

### Unchanged

- Retrieval scoring semantics, datasets, gold IDs, forbidden IDs, oracle behaviour, and token-overlap behaviour.

## [0.1.0] - 2026-08-14

### Added

- Initial benchmark scaffold (Phases 0–2).
- Neutral benchmark models, dataset loader, runner, and retrieval metrics.
- Mini golden dataset with Oracle, token-overlap, and full-history backends.
- CLI: `datasets`, `validate-dataset`, `run`.
- CogKura 0.14.x backend adapter with provenance mapping; prepare uses native `as_of` on encode/consolidate.
- Specialized cognitive metrics (temporal, updating, forgetting, working memory, learning, metamemory, efficiency).
- Project Atlas dataset (`software_project_v1`: 61 events, 24 queries) with distinct noise distractors and `core`-tagged story queries.
- Project Helios dataset (`helios_v1`: 550 events, 49 queries) with paraphrase queries and messy-history interference.
- Query `tags` field; core-subset capability tables in `compare` and summary reports.
- Temporal reporting shows both current and historical accuracy; abstain queries excluded from retrieval averages.
- CLI `run` prints each capability's primary metric; `demo` defaults to `software_project_v1`.
- `valid_at` filtering on token-overlap and full-history baselines.
- `related_query_id` on queries for learning pre/post pairs.

### Changed

- CogKura adapter writes `metadata["entity_ids"]` on ingest, stops auto-`record_access` on retrieve, and passes structured `RetrievalCue` when queries/requests include optional cue fields.
- Optional query/request fields: `entity_ids`, `predicate`, `object_value` (Helios core cues; mini and Atlas omit them).
- Helios distractors are distinct authored lines (no numbered template mill); story slots `helios-005` / `helios-016` carry entity and semantic-fact structure for spreading and current-state recall.
- Core capability tables merge metamemory F1 from aggregated counts instead of averaging per-query F1.
- CogKura backend reports the installed distribution version from package metadata.
