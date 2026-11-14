# Source-aware metamemory v1

Independently authored gold for source evidence and exact semantic-slot inspection:
23 events, 26 checkpoints, all six knowledge states. Fixtures use source/event
identities and simulated times; no Core UUID, eligibility algorithm or expected
answer enters the adapter request.

The first-pass checkpoints coincide with event timestamps. Later queries can
observe replay outcomes; diagnostics must describe the pass actually executed.
`sm-readoption-deferred` checks withdrawn state and the retained withdrawal
replay's `target_not_unique_current` reason. It does not manufacture a distinct
re-admission decision. Historical attribution is conservative; a complete
historical transition-evidence graph is not required or inferred.

`sm-evidence-cap` requires one returned evidence reference with explicit
incompleteness, while retaining the contested semantic state. The stricter
cross-backend identity check is separate and currently fails because equally
eligible source revisions can differ. See the release findings.

Supplemental integration tests cover missing revisions, legacy snapshots,
optional inspection unavailability, context currentness, report truncation and
read-only behavior without adding fault-injection semantics to source events.

Released earlier datasets are unchanged. No trust ranking, source independence
claim, truth score or automatic abstention policy is scored here.
