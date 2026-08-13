# Backends

| Backend | Purpose |
|---------|---------|
| `oracle` | Returns declared expected evidence. Validation infrastructure. |
| `token-overlap` | Shallow deterministic retrieval baseline. |
| `full-history` | All visible events in chronological order. |
| `cogkura` | CogKura 0.11.x adapter (optional extra). |

## CogKura adapter

Install with `uv sync --extra cogkura --dev`. The adapter uses CogKura's public `Memory` API only:

- `observe` → ingest project events (`source_record_id` = benchmark event ID)
- `encode_episodes(..., as_of=)` / `consolidate_semantics(..., as_of=)` → prepare (simulated clock)
- `recall` / `record_access` → retrieve (provenance maps to benchmark event IDs)
- `select_working_memory` → select_context
- `assess_memory` → assess
- `learn` → apply_feedback
- `apply_forgetting` → maintain

Every `RetrievedItem.source_event_ids` value is a benchmark event ID, never a CogKura memory key. CogKura 0.11 stamps durable-memory `created_at` / `updated_at` from `as_of` on encode and consolidate, so the adapter uses CogKura's default in-memory stores.

### Known CogKura limitations

- CogKura 0.11.0 still exports `__version__ = "0.10.0"`; the adapter reports the installed distribution version from package metadata.
- CogKura scores are not golden-filed in CI.

Unsupported optional capabilities return `None`. Backends must not fake functionality they do not provide.
