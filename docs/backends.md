# Backends

| Backend | Purpose |
|---------|---------|
| `oracle` | Returns declared expected evidence. Validation infrastructure. |
| `token-overlap` | Shallow deterministic retrieval baseline. |
| `full-history` | All visible events in chronological order. |
| `cogkura` | CogKura 0.10.x adapter (optional extra, Phase 3+). |

Unsupported optional capabilities return `None`. Backends must not fake functionality they do not provide.
