# Backends

| Backend | Purpose |
|---------|---------|
| `oracle` | Returns declared expected evidence. Validation infrastructure. |
| `token-overlap` | Shallow deterministic retrieval baseline. |
| `full-history` | All visible events in chronological order. |
| `cogkura` | CogKura 0.17.x adapter (optional extra). |

## CogKura adapter

Install with `uv sync --extra cogkura --dev`. The adapter uses CogKura's public `Memory` API only:

- `observe` → ingest project events (`source_record_id` = benchmark event ID)
- `encode_episodes(..., as_of=)` / `consolidate_semantics(..., as_of=)` → prepare (simulated clock)
- `recall` → retrieve (provenance maps to benchmark event IDs; no automatic `record_access`)
- `select_working_memory` → select_context
- `assess_memory` → assess
- `learn` → apply_feedback
- `apply_forgetting` → maintain

Ingest maps benchmark `entities` to observation `metadata["entity_ids"]` and optional `session_id` to `metadata["session_id"]`. Semantic facts may include `valid_from` / `valid_until` in metadata when present on the benchmark model. When a query or request carries optional `entity_ids`, `predicate`, or `object_value`, the adapter passes a structured `RetrievalCue` to `recall` / `select_working_memory` / `assess_memory`; otherwise it passes the query string unchanged. Retrieval presentation does not imply use: learning still flows through `apply_feedback` → `learn`, not through automatic access recording on retrieve.

Every `RetrievedItem.source_event_ids` value is a benchmark event ID, never a CogKura memory key. CogKura 0.14 stamps durable-memory `created_at` / `updated_at` from `as_of` on encode and consolidate, so the adapter uses CogKura's default in-memory stores. Ranking (gated slot admission, multi-entity association, superseded exclusion, distinctive episodic match) stays inside CogKura; the adapter does not post-filter hits.

The adapter maps CogKura's public `RecallResult` fields into neutral `RetrievedItem.metadata` (activation, activation components, `reason`, and optional typed diagnostics when exposed). CogKura 0.17 `inspect_recall` competition diagnostics are mapped to neutral `CompetitionObservation` values on `RetrievalResponse` when `competition_diagnostics=True`. Raw competition counters and evidence remain in `backend_metadata["cogkura"]["competition_inspection"]`. CogKura 0.16/0.17 inspect/assessment contextual diagnostics are copied into `backend_metadata` when present. Diagnostics are observational only; primary scoring uses ranked `RetrievedItem` groups.

Assessment maps CogKura flags to neutral booleans, including explicit `missing_knowledge` → `indicates_missing_knowledge`. Metamemory scores from CogKuraBench 0.1.0 are not comparable to 0.1.1 metamemory scores without an adapter-corrected baseline. Primary retrieval scores from 0.1.x are not directly comparable to 0.2.0 because top-K is item-based in 0.2.0.

Use `cogkura-bench inspect <query-id> --backend cogkura --dataset helios_v1` to inspect retrieval diagnostics for queries such as `helios-update-001`, `helios-temporal-curr-001`, and `helios-temporal-hist-001`. For evidence-group stages, see `customer_decision_context_v1` and [findings/customer-decision-context-0.3.0.md](findings/customer-decision-context-0.3.0.md).

### Oracle evidence groups

When `expected_evidence_groups` is non-empty, Oracle returns at least the first declared event ID from each expected group, then remaining flat `expected_evidence_ids` up to the retrieval limit. Oracle does not implement `select_context`.

### Known CogKura limitations

- The adapter reports the installed distribution version from package metadata.
- CogKura scores are not golden-filed in CI.

Unsupported optional capabilities return `None`. Backends must not fake functionality they do not provide.
