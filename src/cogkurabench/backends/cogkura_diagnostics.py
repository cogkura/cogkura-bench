"""CogKura adapter diagnostics: recall mapping and lifecycle summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, is_dataclass
from typing import TYPE_CHECKING, Any

from cogkurabench.models import RetrievedItem

if TYPE_CHECKING:
    from cogkura.models import RecallInspectionResult, RecallResult


COGKURA_METADATA_SCHEMA_VERSION = 1

_OPTIONAL_DIAGNOSTIC_FIELDS: tuple[str, ...] = (
    "rank_activation",
    "text_coverage",
    "text_cue_fit",
    "temporal_mode",
    "slot_fit",
    "structured_adjustment",
    "eligibility",
    "admission_reason",
    "slot_fit_source",
    "semantic_slot_key",
    "support_provenance",
    "selected_support_revision_key",
    "observation_evidence_ids",
    "semantic_status",
    "association_path",
    "structured_association_fit",
    "relevance_tier",
)


@dataclass(frozen=True, slots=True)
class ProvenanceMappingDetail:
    """Breakdown of provenance mapping failures."""

    no_provenance_count: int
    wholly_unresolved_count: int
    partially_mapped_count: int
    unresolved_observation_id_count: int


@dataclass(frozen=True, slots=True)
class RecallMappingResult:
    """Mapped benchmark items plus raw recall diagnostics."""

    items: tuple[RetrievedItem, ...]
    raw_count: int
    mapped_count: int
    unmapped_count: int
    raw_episode_count: int
    raw_semantic_count: int
    unmapped_episode_count: int
    unmapped_semantic_count: int
    provenance: ProvenanceMappingDetail


def json_safe_metadata_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value"):
        return value.value
    if is_dataclass(value):
        return dataclass_to_metadata(value)
    if isinstance(value, Mapping):
        return {str(key): json_safe_metadata_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe_metadata_value(item) for item in value]
    return str(value)


def recall_result_to_metadata(result: RecallResult) -> dict[str, object]:
    """Map a CogKura RecallResult to neutral RetrievedItem metadata."""
    metadata: dict[str, object] = {
        "activation": result.activation,
        "score": result.score,
        "latency_seconds": result.latency_seconds,
        "reason": result.reason,
    }
    components = result.components
    metadata["activation_base_level"] = components.base_level
    metadata["activation_spreading"] = components.spreading
    metadata["activation_partial_match"] = components.partial_match
    metadata["activation_noise"] = components.noise
    metadata["activation_total"] = components.total
    metadata["activation_current_state"] = components.current_state

    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is not None:
        for field_name in _OPTIONAL_DIAGNOSTIC_FIELDS:
            if hasattr(diagnostics, field_name):
                metadata[field_name] = json_safe_metadata_value(getattr(diagnostics, field_name))

    memory = result.memory
    if hasattr(memory, "status"):
        metadata["semantic_status"] = json_safe_metadata_value(memory.status)
    if hasattr(memory, "predicate"):
        metadata["semantic_predicate"] = memory.predicate
    if hasattr(memory, "subject_entity_id"):
        metadata["semantic_subject_entity_id"] = memory.subject_entity_id
    if hasattr(memory, "object_value"):
        metadata["semantic_object_value"] = memory.object_value
    if hasattr(memory, "slot_key"):
        metadata["semantic_slot_key"] = memory.slot_key

    return metadata


def dataclass_to_metadata(value: object) -> dict[str, object]:
    """Convert a CogKura result dataclass to JSON-safe metadata."""
    from dataclasses import fields

    if not is_dataclass(value):
        return {}
    payload: dict[str, object] = {}
    for field in fields(value):
        payload[field.name] = json_safe_metadata_value(getattr(value, field.name))
    return payload


def map_ranked_recall_results(
    ranked_results: Sequence[tuple[int, RecallResult]],
    *,
    observation_id_to_event_id: Mapping[str, str],
    statement_for_result: Any,
) -> RecallMappingResult:
    """Map explicit (rank, RecallResult) pairs to benchmark items."""
    items: list[RetrievedItem] = []
    raw_episode = 0
    raw_semantic = 0
    unmapped_episode = 0
    unmapped_semantic = 0
    no_provenance = 0
    wholly_unresolved = 0
    partially_mapped = 0
    unresolved_observation_ids = 0

    for rank, result in ranked_results:
        memory_kind = result.memory_kind.value
        if memory_kind == "episode":
            raw_episode += 1
        elif memory_kind == "semantic":
            raw_semantic += 1

        observation_ids = _observation_ids_for_result(result)
        if not observation_ids:
            no_provenance += 1
            if memory_kind == "episode":
                unmapped_episode += 1
            elif memory_kind == "semantic":
                unmapped_semantic += 1
            continue

        mapped_ids = tuple(
            sorted(
                {
                    observation_id_to_event_id[observation_id]
                    for observation_id in observation_ids
                    if observation_id in observation_id_to_event_id
                }
            )
        )
        unresolved = sum(
            1
            for observation_id in observation_ids
            if observation_id not in observation_id_to_event_id
        )
        if unresolved:
            unresolved_observation_ids += unresolved

        if not mapped_ids:
            wholly_unresolved += 1
            if memory_kind == "episode":
                unmapped_episode += 1
            elif memory_kind == "semantic":
                unmapped_semantic += 1
            continue

        if unresolved:
            partially_mapped += 1

        items.append(
            RetrievedItem(
                source_event_ids=mapped_ids,
                text=statement_for_result(result),
                score=result.score,
                rank=rank,
                memory_type=memory_kind,
                metadata=recall_result_to_metadata(result),
            )
        )

    raw_count = len(ranked_results)
    mapped_count = len(items)
    return RecallMappingResult(
        items=tuple(items),
        raw_count=raw_count,
        mapped_count=mapped_count,
        unmapped_count=raw_count - mapped_count,
        raw_episode_count=raw_episode,
        raw_semantic_count=raw_semantic,
        unmapped_episode_count=unmapped_episode,
        unmapped_semantic_count=unmapped_semantic,
        provenance=ProvenanceMappingDetail(
            no_provenance_count=no_provenance,
            wholly_unresolved_count=wholly_unresolved,
            partially_mapped_count=partially_mapped,
            unresolved_observation_id_count=unresolved_observation_ids,
        ),
    )


def recall_mapping_metadata(mapping: RecallMappingResult) -> dict[str, object]:
    """Serialize recall mapping counts for backend metadata."""
    return {
        "raw_recall_count": mapping.raw_count,
        "mapped_recall_count": mapping.mapped_count,
        "unmapped_recall_count": mapping.unmapped_count,
        "raw_episode_recall_count": mapping.raw_episode_count,
        "raw_semantic_recall_count": mapping.raw_semantic_count,
        "unmapped_episode_recall_count": mapping.unmapped_episode_count,
        "unmapped_semantic_recall_count": mapping.unmapped_semantic_count,
        "results_without_provenance": mapping.provenance.no_provenance_count,
        "results_wholly_unresolved": mapping.provenance.wholly_unresolved_count,
        "partially_mapped_results": mapping.provenance.partially_mapped_count,
        "unresolved_observation_id_count": mapping.provenance.unresolved_observation_id_count,
    }


def _observation_ids_for_result(result: RecallResult) -> set[str]:
    memory = result.memory
    observation_ids: set[str] = set()
    if hasattr(memory, "evidence"):
        for evidence in memory.evidence:
            observation_ids.add(evidence.observation_id)
    if hasattr(memory, "observation_evidence"):
        for evidence in memory.observation_evidence:
            observation_ids.add(evidence.observation_id)
    return observation_ids


def relationship_inspection_to_metadata(
    inspection: RecallInspectionResult,
) -> dict[str, object]:
    """Serialize inspect_recall relationship diagnostics for backend metadata."""
    rows: list[dict[str, object]] = []
    for candidate in (*inspection.returned, *inspection.rejected):
        memory = candidate.memory
        predicate = getattr(memory, "predicate", None)
        object_value = getattr(memory, "object_value", None)
        diagnostics = candidate.diagnostics
        association_path: dict[str, object] | None = None
        relationship_edges: list[dict[str, object]] = []
        hop_kind: str | None = None
        hop_count: int | None = None
        relevance_tier: object = None
        structured_association_fit: float | None = None
        admission_reason: str | None = None
        soft_admitted: bool | None = None
        if diagnostics is not None:
            relevance_tier = json_safe_metadata_value(diagnostics.relevance_tier)
            structured_association_fit = diagnostics.structured_association_fit
            admission_reason = diagnostics.admission_reason
            soft_admitted = diagnostics.soft_admitted
            path = diagnostics.association_path
            if path is not None:
                hop_kind = path.hop_kind
                hop_count = path.hop_count
                association_path = dataclass_to_metadata(path)
                relationship_edges = [
                    dataclass_to_metadata(edge) for edge in path.relationship_edges
                ]
        disposition = json_safe_metadata_value(candidate.disposition)
        rows.append(
            {
                "memory_kind": json_safe_metadata_value(candidate.memory_kind),
                "predicate": predicate,
                "object_value": object_value,
                "disposition": disposition,
                "relevance_tier": relevance_tier,
                "admission_reason": admission_reason,
                "soft_admitted": soft_admitted,
                "association_path": association_path,
                "relationship_edges": relationship_edges,
                "hop_kind": hop_kind,
                "hop_count": hop_count,
                "rank": candidate.rank,
                "selected": disposition == "returned",
                "structured_association_fit": structured_association_fit,
            }
        )
    return {
        "relationship_seed_count": inspection.relationship_seed_count,
        "relationship_paths_used": inspection.relationship_paths_used,
        "association_seed_count": inspection.association_seed_count,
        "association_paths_used": inspection.association_paths_used,
        "considered_count": inspection.considered_count,
        "predicate_rows": rows,
    }
