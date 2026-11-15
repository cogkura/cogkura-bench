# Review: intentional 0.18.4 frozen-output correction

**Status:** Awaiting explicit approval of this deviation and its version-scoped
acceptance mechanism. The retrieval correction itself was approved separately.
**Core:** `93cb7f6` (`0.18.4`); comparison baseline Core `f62096a` (`0.18.3`).
**Bench:** `fca1f90` (`0.3.11`) code with the unchanged strict validator/gold.
**Date:** 15 November 2026.

The same result is now verified with the exact locked Core Git distribution and
Bench implementation `d857da93eb12bbd7a2dab5bd6b645a089090d913` (`0.3.12`). All
required Python 3.11–3.13 gates passed with PostgreSQL (289 tests per runtime,
zero skips) and all dataset/profile CLI steps passed. The exact-pinned raw strict
report still exits 1 for precisely the single fingerprint below.

## Observed difference

The unchanged strict validator was executed in a fresh process against the
candidate source tree with PostgreSQL 14.18. It exits **1**,
`release_gate_passed=false`. This is a preliminary source-tree run, not a claim
that an exact-pinned final release gate passed.

Exactly **one of 393 query fingerprints** differs:

| Field | Result |
| --- | --- |
| Dataset/profile | `authoritative_corrections_v1/cogkura-correction` |
| Query | `ac-q-c20` |
| Old fingerprint | `79f22e969d0389194e19d8ba49769e741c56b9589628961b2846115416b95e80` |
| Candidate fingerprint | `9521ac1807af134198dbca0dc24e5a5268c77af40ec4a6efd8183192fe3e31fe` |
| Retrieved events before | `ac-c20-again`, `ac-c20-withdraw` |
| Retrieved events after | `ac-c20-withdraw` |
| Non-latency query metric change | `memories_retrieved`: 2 → 1 |

Before, current context contained:

```text
Relevant memory:

- The payments-api migration strategy is withdrawn.
- payments-api migrations start with the application again.
```

After, it contains:

```text
Relevant memory:

- The payments-api migration strategy is withdrawn.
```

This removes a deferred readmission from current evidence. Semantic withdrawal,
revision history and processing counters remain unchanged. All **392 other query
fingerprints**, all run-level non-latency metrics and recorded-use fingerprints
match. All **419 diagnostics-paired outcomes** agree. All **191 declared source
checks** and **26 PostgreSQL source reports** pass. Control-profile output is
unchanged. No fixture, expectation, threshold or retrieval score was retuned.

The existing fixture's `render_forbidden` literal is `application_startup`, whereas
the stale episode spells the claim as ordinary prose. Its declared metric did not
detect that sentence. Add a supplemental public-API regression requiring that
the deferred readmission event is absent from current recall/context; preserve
the released fixture rather than retroactively weakening or rewriting it.

## Proposed explicit acceptance

Keep `tests/golden/cogkura_0182_frozen.json` byte-for-byte unchanged and retain
the raw failing comparison. Add a separate reviewed-correction manifest containing
only the exact dataset/profile/query and before/after hashes above, the approved
reason, baseline-file digest, candidate version **0.18.4** and exact Core commit.

The validator would consume it only with an explicit `--approved-corrections`
argument. Require the locked Git distribution's commit/version, original gold
digest, old hash and new hash to match exactly. Reject any other query, metric,
use, population or version difference; reject an absent/reverted expected fix.
No fallback wildcard or automatic future-version acceptance is proposed.

The unchanged baseline file digest is
`927c69031e7d41019ee27a7a7529c2e9fbaa4d91d1f8a44ace0b902755827a1c`.
The exact candidate Core commit is
`93cb7f6a6daae30333008600f3556e6af4f99b3d`.

The report must retain `frozen_mismatches` and mark the **raw** comparison failed,
then separately list the one approved correction and all unapproved differences.
Release acceptance may pass only with this explicit approval, no unapproved
differences, successful source/diagnostics/PostgreSQL checks and the full required
Core/Bench matrix. It must never describe all 393 fingerprints as unchanged.

This changes acceptance for one explicitly reviewed defect correction; it does
not redefine the original comparison or alter released gold. Without approval,
the freeze remains blocked and no exception will be implemented.
