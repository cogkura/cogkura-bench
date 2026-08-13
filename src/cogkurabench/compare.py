"""Compare benchmark backends."""

from __future__ import annotations

from cogkurabench.backends.registry import create_backend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.report import format_capability_table
from cogkurabench.runner import BenchmarkRunner


async def compare_backends(
    backend_names: list[str],
    *,
    dataset_name: str,
) -> int:
    """Run and compare multiple backends on one dataset."""
    dataset = load_dataset(dataset_name)
    print(f"CogKuraBench compare — dataset={dataset_name}")
    print("")
    for backend_name in backend_names:
        if backend_name == "oracle":
            print("Note: oracle is validation infrastructure, not a competitor.")
        backend = create_backend(backend_name, dataset)
        result = await BenchmarkRunner().run(dataset, backend, write_results=True)
        print(f"## {backend_name}")
        print(format_capability_table(result))
        print("")
    return 0
