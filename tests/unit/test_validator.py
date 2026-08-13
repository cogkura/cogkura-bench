"""Dataset validation edge-case tests."""

from cogkurabench.dataset import validate_dataset


def test_forbidden_future_evidence_allowed() -> None:
    errors = validate_dataset("mini")
    assert not any("forbidden" in error and "future" in error for error in errors)
