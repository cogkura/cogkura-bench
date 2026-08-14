# Backends

| Backend | Purpose |
|---------|---------|
| `oracle` | Returns declared expected evidence. Validation infrastructure. |
| `token-overlap` | Shallow deterministic retrieval baseline. |
| `full-history` | All visible events in chronological order. |
| `cogkura` | CogKura 0.12.x adapter (optional extra). |

## CogKura adapter

Install with `uv sync --extra cogkura --dev`. The adapter uses CogKura's public `Memory` API only:

- `observe` → ingest project events (`source_record_id` = benchmark event ID)
- `encode_episodes(..., as_of=)` / `consolidate_semantics(..., as_of=)` → prepare (simulated clock)
- `recall` → retrieve (provenance maps to benchmark event IDs; no automatic `record_access`)
- `select_working_memory` → select_context
- `assess_memory` → assess
- `learn` → apply_feedback
- `apply_forgetting` → maintain

Ingest maps benchmark `entities` to observation `metadata["entity_ids"]` so CogKura's encoder can attach them to episodes. When a query or request carries optional `entity_ids`, `predicate`, or `object_value`, the adapter passes a structured `RetrievalCue` to `recall` / `select_working_memory` / `assess_memory`; otherwise it passes the query string unchanged. Retrieval presentation does not imply use: learning still flows through `apply_feedback` → `learn`, not through automatic access recording on retrieve.

Every `RetrievedItem.source_event_ids` value is a benchmark event ID, never a CogKura memory key. CogKura 0.12 stamps durable-memory `created_at` / `updated_at` from `as_of` on encode and consolidate, so the adapter uses CogKura's default in-memory stores. Ranking (string-cue entity seeding, semantic slot admission, superseded penalty, numeric collapse) stays inside CogKura; the adapter does not post-filter hits.

### Known CogKura limitations

- CogKura 0.12.0 still exports `__version__ = "0.10.0"`; the adapter reports the installed distribution version from package metadata.
- CogKura scores are not golden-filed in CI.

Unsupported optional capabilities return `None`. Backends must not fake functionality they do not provide.
