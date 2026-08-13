"""Backend factory registry."""

from __future__ import annotations

from collections.abc import Callable

from cogkurabench.backends.base import MemoryBackend
from cogkurabench.backends.full_history import FullHistoryBackend
from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.models import BenchmarkDataset


def create_backend(name: str, dataset: BenchmarkDataset) -> MemoryBackend:
    """Create a benchmark backend by name."""
    factories: dict[str, Callable[[BenchmarkDataset], MemoryBackend]] = {
        "oracle": lambda data: OracleBackend(data.queries, data.events),
        "token-overlap": lambda _data: TokenOverlapBackend(),
        "full-history": lambda _data: FullHistoryBackend(),
        "cogkura": _create_cogkura_backend,
    }
    try:
        factory = factories[name]
    except KeyError as exc:
        supported = ", ".join(sorted(factories))
        raise ValueError(f"Unsupported backend {name!r}. Supported: {supported}") from exc
    return factory(dataset)


def _create_cogkura_backend(_dataset: BenchmarkDataset) -> MemoryBackend:
    from cogkurabench.backends.cogkura import CogKuraBackend  # noqa: PLC0415

    return CogKuraBackend()


def available_backends() -> tuple[str, ...]:
    """Return supported backend names."""
    return ("oracle", "token-overlap", "full-history", "cogkura")
