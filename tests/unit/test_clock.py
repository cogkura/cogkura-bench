"""Benchmark clock tests."""

from datetime import UTC, datetime

from cogkurabench.clock import BenchmarkClock


def test_clock_advance_to() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    clock = BenchmarkClock(current=start)
    later = datetime(2026, 1, 5, tzinfo=UTC)
    clock.advance_to(later)
    assert clock.current == later
