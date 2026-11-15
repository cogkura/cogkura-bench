# Source provenance architecture freeze — Bench 0.3.12 candidate

**Date:** 15 November 2026. **Status:** Required CI gates pass; raw strict frozen
comparison fails on one intentional correction. Freeze acceptance awaits its
explicit review decision. No release was published.
**Core pin:** `93cb7f6a6daae30333008600f3556e6af4f99b3d` (`0.18.4`).
**Prior baseline:** Bench `fca1f90`, Core `f62096a` / validated `0.18.3`.
**Bench implementation validated:** `d857da93eb12bbd7a2dab5bd6b645a089090d913`.

## Changes and scope

Only the Core pin, matching candidate metadata, adapter's explicit version allowlist,
supplemental integration assertions and validation documentation change. Dataset
gold and original frozen fingerprints remain intact. No profile, threshold,
retrieval score, event timing or expected semantic result was retuned. Demo and
Agent are unchanged.

The new assertion checks `ac-q-c20` through public Bench/Core APIs: correction-enabled
current recall excludes `ac-c20-again`, and rendered context excludes its natural-
language assertion while retaining the withdrawal notice. The old fixture's
underscore literal alone did not detect the ordinary-prose sentence.

## Intentional correction review

Both the unchanged source-tree preflight and exact-pinned final run match 392/393
query fingerprints and find
exactly the reviewed correction at `authoritative_corrections_v1/cogkura-correction`,
query `ac-q-c20`. Before, current context included the deferred readmission;
after, it contains only the withdrawal. `memories_retrieved` changes 2 → 1.
Aggregate non-latency metrics and use fingerprints remain equal. All 419 paired
diagnostics outcomes, 191 source checks and 26 PostgreSQL reports agree.

The raw strict gate is **FAIL**, not a hidden success. The
[full review](../review-0.18.4-withdrawn-readmission-deviation.md) contains exact
hashes and before/after content. Approval of the Core fix does not automatically
approve a frozen-baseline exception. No acceptance exception is implemented while
that decision is pending.

## Required gates

Exact-pinned Python 3.11–3.13 locked install, Ruff, format, MyPy, full pytest with
PostgreSQL and every CI dataset/profile CLI step were executed successfully.

| Runtime | Locked sync / Ruff / format / MyPy | Full PostgreSQL pytest | Skips | All CI CLI steps |
| --- | --- | --- | --- | --- |
| Python 3.11.15 | PASS | **289 passed** | **0** | PASS |
| Python 3.12.8 | PASS | **289 passed** | **0** | PASS |
| Python 3.13.0 | PASS | **289 passed** | **0** | PASS |

The unchanged strict command was also executed with `PYTHONHASHSEED=0`, a fresh
process and a disposable PostgreSQL 14.18 database:

```bash
python scripts/run_source_metamemory_validation.py --diagnostics-parity --postgres \
  --output results/source-provenance-freeze-0.18.4-raw-validation.json
```

It exits **1**, with `release_gate_passed=false`. Its retained
[raw summary](data/source-provenance-freeze-0.3.12-raw-validation.json) records the
exact Git distribution, raw mismatch, 392 unchanged query fingerprints, 46 recorded
use results from 73 explicit use actions, no diagnostics mismatches, 191/191 source
checks and PostgreSQL status **PASS** across all 26 reports. This is not a passed
release gate and no comparison exception has been silently applied.

Initial exact-pinned execution exposed the adapter's explicit correction-version
allowlist, which named only 0.18.2/0.18.3. It was extended to the validated 0.18.4
candidate, preserving rejection of unknown versions; this is compatibility, not
benchmark retuning. Full gates are rerun in fresh per-runtime databases afterward.

Core separately passed 923 tests with zero skips per runtime and dependency-free
example execution. Its combined regressions and cost findings live in Core's
`docs/findings/0.18.4-source-provenance-architecture-freeze.md`.

The sole remaining release decision is the documented one-query correction.
Original dataset gold and `tests/golden/cogkura_0182_frozen.json` are byte-for-byte
unchanged. No acceptance manifest/exception is implemented pending explicit approval.

## Retained limitations

Source independence remains unknown; no trust/truth scoring, durable decision
ledger, automatic abstention, full bitemporal reconstruction, atomic cross-store
snapshot or arbitrary-UUID retrieval determinism is claimed. The prose correction
needs available exact structured claim identity; it does not infer every assertion
from arbitrary natural-language text or manufacture missing evidence.

PostgreSQL testing targets local 14.18. Other server versions, concurrent-writer
isolation, production-scale workloads and Agent lifecycle remain outside this
validation. Release tags/publication remain separate actions.
