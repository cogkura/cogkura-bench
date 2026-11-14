"""Translate public Core source reports to neutral, revision-bound observations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from cogkurabench.source_models import (
    EvidenceCoverageObservation,
    SourceAssessmentObservation,
    SourceAssessmentRequest,
    SourceDecisionObservation,
    SourceRevisionObservation,
)

if TYPE_CHECKING:
    from cogkura import EvidenceQuality, Memory, SemanticDecisionReport


def _quality(value: EvidenceQuality) -> EvidenceCoverageObservation:
    return EvidenceCoverageObservation(
        has_evidence=value.has_evidence,
        revision_complete=value.revision_coverage_complete,
        locator_complete=value.locator_coverage_complete,
        relation_complete=value.relation_coverage_complete,
        truncated=value.is_truncated,
        distinct_sources=value.distinct_source_count,
        referenced=value.referenced_count,
        returned=value.returned_count,
        relation_applicable=value.relation_applicable_count,
        relation_not_applicable=value.relation_not_applicable_count,
    )


async def inspect_sources(
    memory: Memory,
    request: SourceAssessmentRequest,
    revision_events: Mapping[tuple[str, int], str],
    decisions: SemanticDecisionReport | None,
) -> SourceAssessmentObservation:
    from cogkura import SemanticSlotQuery, SourceInspectionLimits

    spec = request.spec
    as_of = spec.as_of or request.as_of
    if as_of > request.as_of:
        raise ValueError("source inspection cannot see future knowledge")
    slot = await memory.inspect_semantic_slot(
        SemanticSlotQuery(spec.subject, spec.predicate, spec.qualifiers),
        tenant_id=request.tenant_id,
        subject_id=request.subject_id,
        as_of=as_of,
        valid_at=request.valid_at,
        limits=SourceInspectionLimits(spec.max_revisions, spec.max_relations, spec.max_evidence),
    )
    unmapped = 0

    def event_ids(observation_id: str, revision: int) -> tuple[str, ...]:
        nonlocal unmapped
        event_id = revision_events.get((observation_id, revision))
        if event_id is None:
            unmapped += 1
            return ()
        return (event_id,)

    revisions = tuple(
        SourceRevisionObservation(
            event_ids=tuple(
                sorted(
                    {
                        e
                        for s in r.sources
                        for e in event_ids(s.observation_id, s.observation_revision)
                    }
                )
            ),
            status=r.projected_status.value if r.projected_status is not None else None,
            view=r.view_state.value,
            history_complete=r.historical_attribution_complete,
            valid_from=r.valid_from,
            valid_until=r.valid_until,
            latest=tuple(s.is_latest_known_revision for s in r.sources),
        )
        for r in slot.revisions
    )
    transitions = {t.successor_revision_key: t for r in slot.revisions for t in r.transitions}
    transition_ids = tuple(
        sorted(
            {
                e
                for t in transitions.values()
                if t.asserting_evidence is not None
                for e in event_ids(
                    t.asserting_evidence.observation_id, t.asserting_evidence.observation_revision
                )
            }
        )
    )
    # Reports are only the immediately preceding pass, scoped to this slot.
    # Never expose a later pass's decisions through a historical inspection.
    available = decisions is not None and decisions.evaluated_at <= as_of
    decision_items = tuple(
        SourceDecisionObservation(
            operation=d.operation.value,
            outcome=d.outcome.value,
            reasons=tuple(r.value for r in d.reasons),
            event_ids=event_ids(
                d.asserting_evidence.observation_id, d.asserting_evidence.observation_revision
            )
            if d.asserting_evidence is not None
            else (),
            effective_at=d.effective_at,
        )
        for d in (decisions.items if decisions is not None and available else ())
        if d.slot_key == slot.slot_key
        or d.target_revision_key in {r.revision_key for r in slot.revisions}
        or d.resulting_revision_key in {r.revision_key for r in slot.revisions}
    )
    context_quality = None
    context_ids: tuple[str, ...] = ()
    older = None
    currentness_complete = None
    if spec.context:
        context = await memory.prepare_context(
            request.query,
            tenant_id=request.tenant_id,
            subject_id=request.subject_id,
            as_of=as_of,
            valid_at=request.valid_at,
        )
        assessed = await memory.assess_source_memory(context, max_evidence=spec.max_evidence)
        context_quality = _quality(assessed.quality)
        context_ids = tuple(
            sorted(
                {
                    e
                    for item in assessed.provenance.items
                    for s in item.sources
                    for e in event_ids(s.observation_id, s.observation_revision)
                }
            )
        )
        older = sum(i.currentness.older_revision_count for i in assessed.items)
        currentness_complete = all(i.currentness.is_complete for i in assessed.items)
    return SourceAssessmentObservation(
        state=slot.state.value,
        conflict=slot.conflict.state.value,
        conflict_complete=slot.conflict.is_complete,
        cross_source_disagreement=slot.conflict.cross_source_disagreement,
        independence=slot.conflict.independence.value,
        inventory_complete=slot.inventory_complete,
        decision_history=slot.decision_history.value,
        reasons=tuple(r.value for r in slot.reasons),
        quality=_quality(slot.quality),
        revisions=revisions,
        event_ids=tuple(sorted({e for r in revisions for e in r.event_ids})),
        pending_count=sum(r.view == "pending_effective" for r in revisions),
        indeterminate_revision_count=sum(r.view == "indeterminate" for r in revisions),
        transition_event_ids=transition_ids,
        transition_effective_times=tuple(
            sorted(
                {
                    t.effective_at.isoformat()
                    for t in transitions.values()
                    if t.effective_at is not None
                }
            )
        ),
        unmapped_evidence_count=unmapped,
        decisions=decision_items,
        decisions_available=available,
        decisions_complete=decisions.diagnostics_complete if available and decisions else None,
        decisions_truncated=decisions.is_truncated if available and decisions else None,
        context_quality=context_quality,
        context_event_ids=context_ids,
        context_older_count=older,
        context_currentness_complete=currentness_complete,
    )
