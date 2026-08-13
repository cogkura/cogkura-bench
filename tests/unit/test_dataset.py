"""Dataset loading and validation tests."""

from cogkurabench.dataset import ensure_valid_dataset, load_dataset, validate_dataset


def test_mini_dataset_loads() -> None:
    dataset = load_dataset("mini")
    assert dataset.manifest.name == "mini"
    assert len(dataset.events) == 15
    assert len(dataset.queries) == 12
    assert len(dataset.feedback) == 2


def test_mini_dataset_validates() -> None:
    assert validate_dataset("mini") == []


def test_action_stream_is_sorted() -> None:
    dataset = ensure_valid_dataset("mini")
    timestamps = [action.timestamp for action in dataset.actions]
    assert timestamps == sorted(timestamps)


def test_event_ids_unique() -> None:
    dataset = load_dataset("mini")
    assert len({event.id for event in dataset.events}) == len(dataset.events)
