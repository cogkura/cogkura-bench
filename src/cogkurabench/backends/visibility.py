"""Shared event visibility rules for benchmark backends."""

from __future__ import annotations

from datetime import datetime

from cogkurabench.models import ProjectEvent


def is_event_visible(
    event: ProjectEvent,
    *,
    as_of: datetime,
    valid_at: datetime | None = None,
) -> bool:
    """Return whether an event is visible at the simulated query time."""
    if event.timestamp > as_of:
        return False
    if valid_at is not None and event.timestamp > valid_at:
        return False
    return True


def visible_events(
    events: list[ProjectEvent],
    *,
    as_of: datetime,
    valid_at: datetime | None = None,
) -> list[ProjectEvent]:
    """Filter events visible at the simulated query time."""
    return [event for event in events if is_event_visible(event, as_of=as_of, valid_at=valid_at)]
