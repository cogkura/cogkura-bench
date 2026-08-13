"""CogKura in-memory stores aligned to benchmark simulated time."""

from __future__ import annotations

from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from cogkura.models import (
    EpisodeInput,
    EpisodeWriteStatus,
    SemanticMemoryInput,
    SemanticWriteStatus,
    StoredEpisode,
)
from cogkura.storage.in_memory_episode import InMemoryEpisodeStore
from cogkura.storage.in_memory_semantic import InMemorySemanticMemoryStore, _stored_from_input


def _simulated_now(episode: EpisodeInput) -> datetime:
    """Use episode temporal bounds as durable-memory timestamps."""
    return episode.ended_at.astimezone(UTC)


class BenchmarkEpisodeStore(InMemoryEpisodeStore):
    """Episode store that stamps created_at from observation time, not wall clock."""

    async def upsert(self, episode: EpisodeInput) -> EpisodeWriteStatus:
        key = self._key(episode.tenant_id, episode.memory_key)
        existing = self._episodes.get(key)
        now = _simulated_now(episode)
        fingerprint = episode.metadata["episode"]["content_fingerprint"]
        if existing is not None:
            existing_fingerprint = existing.metadata["episode"]["content_fingerprint"]
            if existing_fingerprint == fingerprint:
                return EpisodeWriteStatus.UNCHANGED
            stored = StoredEpisode(
                id=existing.id,
                tenant_id=episode.tenant_id,
                subject_id=episode.subject_id,
                memory_key=episode.memory_key,
                statement=episode.statement,
                started_at=episode.started_at,
                ended_at=episode.ended_at,
                confidence=episode.confidence,
                importance=episode.importance,
                is_active=True,
                evidence=episode.evidence,
                entities=episode.entities,
                metadata=MappingProxyType(dict(episode.metadata)),
                created_at=existing.created_at,
                updated_at=now,
            )
            self._episodes[key] = stored
            return EpisodeWriteStatus.UPDATED

        stored = StoredEpisode(
            id=str(uuid4()),
            tenant_id=episode.tenant_id,
            subject_id=episode.subject_id,
            memory_key=episode.memory_key,
            statement=episode.statement,
            started_at=episode.started_at,
            ended_at=episode.ended_at,
            confidence=episode.confidence,
            importance=episode.importance,
            is_active=True,
            evidence=episode.evidence,
            entities=episode.entities,
            metadata=MappingProxyType(dict(episode.metadata)),
            created_at=now,
            updated_at=now,
        )
        self._episodes[key] = stored
        return EpisodeWriteStatus.CREATED


class BenchmarkSemanticMemoryStore(InMemorySemanticMemoryStore):
    """Semantic store that stamps created_at from supported-at time, not wall clock."""

    async def upsert(self, memory: SemanticMemoryInput) -> SemanticWriteStatus:
        key = self._memory_key(memory.tenant_id, memory.memory_key)
        existing = self._memories.get(key)
        now = memory.last_supported_at.astimezone(UTC)
        fingerprint = memory.metadata["semantic"]["content_fingerprint"]
        if existing is not None:
            existing_fingerprint = existing.metadata["semantic"]["content_fingerprint"]
            if existing_fingerprint == fingerprint:
                return SemanticWriteStatus.UNCHANGED
            stored = _stored_from_input(
                memory,
                memory_id=existing.id,
                created_at=existing.created_at,
                now=now,
            )
            self._memories[key] = stored
            return SemanticWriteStatus.UPDATED

        stored = _stored_from_input(
            memory,
            memory_id=str(uuid4()),
            created_at=memory.first_supported_at.astimezone(UTC),
            now=now,
        )
        self._memories[key] = stored
        return SemanticWriteStatus.CREATED

    async def apply_reconciliation(
        self,
        plan: Any,
    ) -> Any:
        from cogkura.models import (  # noqa: PLC0415
            SemanticReconciliationPlan,
            SemanticReconciliationWriteResult,
            StoredSemanticRevision,
        )

        if not isinstance(plan, SemanticReconciliationPlan):
            return await super().apply_reconciliation(plan)

        memories = dict(self._memories)
        revisions = dict(self._revisions)
        relations = dict(self._relations)
        created = 0
        updated = 0
        unchanged = 0
        revisions_created = 0
        revisions_updated = 0
        relations_written = 0

        for revision in plan.revisions:
            key = self._revision_key(revision.tenant_id, revision.revision_key)
            existing = revisions.get(key)
            revision_time = revision.first_supported_at.astimezone(UTC)
            stored_revision = StoredSemanticRevision(
                revision_key=revision.revision_key,
                memory_key=revision.memory_key,
                tenant_id=revision.tenant_id,
                revision_number=revision.revision_number,
                status=revision.status,
                valid_from=revision.valid_from,
                valid_until=revision.valid_until,
                confidence=revision.confidence,
                importance=revision.importance,
                support_count=revision.support_count,
                contradiction_count=revision.contradiction_count,
                first_supported_at=revision.first_supported_at,
                last_supported_at=revision.last_supported_at,
                derivations=revision.derivations,
                created_at=existing.created_at if existing is not None else revision_time,
                updated_at=revision.last_supported_at.astimezone(UTC),
            )
            if existing is None:
                revisions_created += 1
            else:
                revisions_updated += 1
            revisions[key] = stored_revision

        for memory in plan.current_memories:
            key = self._memory_key(memory.tenant_id, memory.memory_key)
            existing_memory = memories.get(key)
            fingerprint = memory.metadata["semantic"]["content_fingerprint"]
            memory_time = memory.first_supported_at.astimezone(UTC)
            if (
                existing_memory is not None
                and existing_memory.metadata["semantic"]["content_fingerprint"] == fingerprint
            ):
                unchanged += 1
            elif existing_memory is None:
                created += 1
            else:
                updated += 1
            memories[key] = _stored_from_input(
                memory,
                memory_id=existing_memory.id if existing_memory is not None else str(uuid4()),
                created_at=(
                    existing_memory.created_at if existing_memory is not None else memory_time
                ),
                now=memory.last_supported_at.astimezone(UTC),
            )

        for relation in plan.relations:
            rel_key = (
                relation.tenant_id,
                relation.left_revision_key,
                relation.right_revision_key,
                relation.relation.value,
            )
            if rel_key not in relations:
                relations_written += 1
            relations[rel_key] = (
                relation.left_revision_key,
                relation.right_revision_key,
                relation.relation.value,
                relation.effective_at.isoformat() if relation.effective_at else None,
            )

        self._memories = memories
        self._revisions = revisions
        self._relations = relations
        return SemanticReconciliationWriteResult(
            created=created,
            updated=updated,
            unchanged=unchanged,
            revisions_created=revisions_created,
            revisions_updated=revisions_updated,
            relations_written=relations_written,
        )
