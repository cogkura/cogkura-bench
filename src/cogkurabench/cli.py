"""CogKuraBench command-line interface."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from cogkurabench.backends.registry import available_backends, create_backend
from cogkurabench.compare import compare_backends
from cogkurabench.dataset import ensure_valid_dataset, list_datasets, validate_dataset
from cogkurabench.demo.project_demo import run_demo
from cogkurabench.evaluation.report import _primary_metric_name
from cogkurabench.inspect import inspect_query
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
    datasets_parser.add_argument("--datasets-root", type=Path, default=None)

    validate_parser = subparsers.add_parser("validate-dataset", help="Validate a dataset")
    validate_parser.add_argument("dataset", help="Dataset name")
    validate_parser.add_argument("--datasets-root", type=Path, default=None)

    run_parser = subparsers.add_parser("run", help="Run a benchmark")
    run_parser.add_argument("--dataset", default="mini", help="Dataset name")
    run_parser.add_argument("--backend", required=True, choices=available_backends())
    run_parser.add_argument("--datasets-root", type=Path, default=None)
    run_parser.add_argument("--results-dir", type=Path, default=Path("results"))
    run_parser.add_argument("--quiet", action="store_true")
    run_parser.add_argument("--no-write", action="store_true")

    demo_parser = subparsers.add_parser("demo", help="Narrated benchmark demo")
    demo_parser.add_argument("--dataset", default="software_project_v1")
    demo_parser.add_argument("--backend", default="cogkura", choices=available_backends())

    inspect_parser = subparsers.add_parser("inspect", help="Inspect one query")
    inspect_parser.add_argument("query_id")
    inspect_parser.add_argument("--dataset", default="mini")
    inspect_parser.add_argument("--backend", required=True, choices=available_backends())

    compare_parser = subparsers.add_parser("compare", help="Compare backends")
    compare_parser.add_argument("backends", nargs="+", choices=available_backends())
    compare_parser.add_argument("--dataset", default="mini")

    return parser


async def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "datasets":
        for name in list_datasets(args.datasets_root):
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
        backend = create_backend(args.backend, dataset)
        result = await BenchmarkRunner().run(
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
                primary = _primary_metric_name(capability_result.capability)
                value = capability_result.metrics.get(primary, 0.0)
                print(f"  {capability_name}: {primary}={value:.3f}")
        return 0

    if args.command == "demo":
        return await run_demo(dataset_name=args.dataset, backend_name=args.backend)

    if args.command == "inspect":
        return await inspect_query(
            args.query_id,
            dataset_name=args.dataset,
            backend_name=args.backend,
        )

    if args.command == "compare":
        return await compare_backends(args.backends, dataset_name=args.dataset)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
