# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial benchmark scaffold (Phases 0–2).
- Neutral benchmark models, dataset loader, runner, and retrieval metrics.
- Mini golden dataset with Oracle, token-overlap, and full-history backends.
- CLI: `datasets`, `validate-dataset`, `run`.
- CogKura 0.10.x backend adapter with provenance mapping and simulated-time stores.
- Specialized cognitive metrics (temporal, updating, forgetting, working memory, learning, metamemory, efficiency).
- Project Atlas dataset (`software_project_v1`: 250 events, 80 queries).
- CLI: `demo`, `inspect`, `compare`; expanded capability Markdown/JSON reports.
- `valid_at` filtering on token-overlap and full-history baselines.
- `related_query_id` on queries for learning pre/post pairs.
