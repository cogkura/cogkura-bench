# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
