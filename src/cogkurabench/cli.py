"""CogKuraBench command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from cogkurabench.backends.base import MemoryBackend
from cogkurabench.backends.full_history import FullHistoryBackend
from cogkurabench.backends.oracle import OracleBackend
from cogkurabench.backends.token_overlap import TokenOverlapBackend
from cogkurabench.dataset import ensure_valid_dataset, list_datasets, validate_dataset
from cogkurabench.runner import BenchmarkRunner


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    return asyncio.run(_dispatch(args))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogkura-bench")
    subparsers = parser.add_subparsers(dest="command")

    datasets_parser = subparsers.add_parser("datasets", help="List available datasets")
    datasets_parser.add_argument(
        "--datasets-root",
        type=Path,
        default=None,
        help="Override datasets directory",
    )

    validate_parser = subparsers.add_parser("validate-dataset", help="Validate a dataset")
    validate_parser.add_argument("dataset", help="Dataset name")
    validate_parser.add_argument("--datasets-root", type=Path, default=None)

    run_parser = subparsers.add_parser("run", help="Run a benchmark")
    run_parser.add_argument("--dataset", default="mini", help="Dataset name")
    run_parser.add_argument(
        "--backend",
        required=True,
        choices=["oracle", "token-overlap", "full-history"],
        help="Memory backend to evaluate",
    )
    run_parser.add_argument("--datasets-root", type=Path, default=None)
    run_parser.add_argument("--results-dir", type=Path, default=Path("results"))
    run_parser.add_argument("--quiet", action="store_true", help="Suppress summary output")
    run_parser.add_argument("--no-write", action="store_true", help="Do not write result files")

    return parser


async def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "datasets":
        names = list_datasets(args.datasets_root)
        for name in names:
            print(name)
        return 0

    if args.command == "validate-dataset":
        errors = validate_dataset(args.dataset, root=args.datasets_root)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"Dataset {args.dataset!r} is valid.")
        return 0

    if args.command == "run":
        dataset = ensure_valid_dataset(args.dataset, root=args.datasets_root)
        backend = _create_backend(args.backend, dataset)
        runner = BenchmarkRunner()
        result = await runner.run(
            dataset,
            backend,
            results_dir=args.results_dir,
            write_results=not args.no_write,
        )
        if not args.quiet:
            print(
                f"backend={result.backend_name} dataset={result.dataset_version} "
                f"queries={len(result.query_results)} duration_ms={result.duration_ms:.1f}"
            )
            for capability_name, capability_result in sorted(result.capability_results.items()):
                recall = capability_result.metrics.get("recall@5", 0.0)
                print(f"  {capability_name}: recall@5={recall:.3f}")
        return 0

    return 1


def _create_backend(name: str, dataset: object) -> MemoryBackend:
    from cogkurabench.models import BenchmarkDataset

    if not isinstance(dataset, BenchmarkDataset):
        raise TypeError("dataset must be a BenchmarkDataset")
    if name == "oracle":
        return OracleBackend(dataset.queries, dataset.events)
    if name == "token-overlap":
        return TokenOverlapBackend()
    if name == "full-history":
        return FullHistoryBackend()
    raise ValueError(f"Unsupported backend: {name}")


if __name__ == "__main__":
    raise SystemExit(main())
