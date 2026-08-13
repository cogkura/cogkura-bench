# Backends

| Backend | Purpose |
|---------|---------|
| `oracle` | Returns declared expected evidence. Validation infrastructure. |
| `token-overlap` | Shallow deterministic retrieval baseline. |
| `full-history` | All visible events in chronological order. |
| `cogkura` | CogKura 0.10.x adapter (optional extra). |

## CogKura adapter

Install with `uv sync --extra cogkura --dev`. The adapter uses CogKura's public `Memory` API only:

- `observe` → ingest project events (`source_record_id` = benchmark event ID)
- `encode_episodes` / `consolidate_semantics` → prepare
- `recall` / `record_access` → retrieve (provenance maps to benchmark event IDs)
- `select_working_memory` → select_context
- `assess_memory` → assess
- `learn` → apply_feedback
- `apply_forgetting` → maintain

Injected `BenchmarkEpisodeStore` and `BenchmarkSemanticMemoryStore` stamp durable-memory `created_at` from observation/support times so simulated `as_of` queries work. Every `RetrievedItem.source_event_ids` value is a benchmark event ID, never a CogKura memory key.

### Known CogKura limitations

- `Memory.consolidate_semantics()` still passes `datetime.now(UTC)` to semantic reconciliation internally. The adapter compensates by using simulated-time stores; semantic `valid_from` may still reflect wall clock in edge cases.
- CogKura scores are not golden-filed in CI.

Unsupported optional capabilities return `None`. Backends must not fake functionality they do not provide.
