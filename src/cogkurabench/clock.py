"""Simulated benchmark clock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class BenchmarkClock:
    """Deterministic simulated time for benchmark execution."""

    current: datetime

    def advance_to(self, timestamp: datetime) -> None:
        """Advance the clock to the given timestamp."""
        self.current = timestamp
