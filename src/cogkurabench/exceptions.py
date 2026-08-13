"""CogKuraBench exceptions."""


class BenchmarkError(Exception):
    """Base exception for benchmark errors."""


class ValidationError(BenchmarkError):
    """Raised when benchmark data or configuration is invalid."""
