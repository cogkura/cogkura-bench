#!/usr/bin/env python3
"""Reproduce 0.18.3 frozen comparisons, diagnostic parity, and strict DB parity.

Run in a fresh process with PYTHONHASHSEED=0. A deterministic standard-library
UUID allocator controls storage identity allocation *before* importing Core.
Core algorithms, inputs, clocks, thresholds, fixture gold and retrieval stay intact.
Ordinary random-ID runs remain useful and are documented separately in findings.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import sys
import uuid
from pathlib import Path
from typing import Any

from cogkurabench.backends.cogkura import CogKuraBackend
from cogkurabench.dataset import load_dataset
from cogkurabench.evaluation.report import result_to_dict
from cogkurabench.runner import BenchmarkRunner

RUNS = [
    (d, "cogkura")
    for d in (
        "mini",
        "software_project_v1",
        "helios_v1",
        "customer_decision_context_v1",
        "interference_v1",
    )
]
RUNS += [
    (d, p)
    for d in ("transient_interference_v1", "transient_interference_v2")
    for p in ("cogkura", "cogkura-interference")
]
RUNS += [
    (d, p)
    for d in (
        "persistent_inhibition_v1",
        "persistent_inhibition_software_v1",
        "persistent_inhibition_customer_v1",
    )
    for p in ("cogkura", "cogkura-inhibition-recording", "cogkura-inhibition")
]
RUNS += [("source_authority_v1", p) for p in ("cogkura-authority-control", "cogkura-authority")]
RUNS += [
    ("authoritative_corrections_v1", p)
    for p in ("cogkura-correction-control", "cogkura-correction")
]


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k != "metadata" and "latency" not in k}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def item_signature(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **clean(item),
        "activation": {
            k: v
            for k, v in item["metadata"].items()
            if k.startswith("activation") or k in ("rank_activation", "semantic_status")
        },
    }


def query_signature(query: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "query_id",
        "metrics",
        "retrieved_event_ids",
        "context_event_ids",
        "context_tokens",
        "indicates_missing_knowledge",
        "indicates_conflict",
        "assessment_flags",
        "assessment_signals",
        "competition_observations",
        "transient_interference_observations",
        "persistent_inhibition_observations",
        "source_authority_observations",
        "authoritative_correction_observations",
    )
    value = {k: clean(query[k]) for k in keys}
    for key in ("retrieved_items", "context_items"):
        value[key] = [item_signature(i) for i in query[key]]
    metadata = query["backend_metadata"]
    value["rendered"] = metadata.get("authoritative_correction", {}).get("rendered")
    value["counters"] = clean(metadata.get("cogkura", {}).get("last_prepare", {}))
    value["counters"].get("semantic_consolidation", {}).pop("decisions", None)
    return value


def run_signature(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "queries": {q["query_id"]: query_signature(q) for q in result["query_results"]},
        "uses": [clean(u) for u in result["use_results"]],
        "metrics": clean({k: v["metrics"] for k, v in result["capability_results"].items()}),
    }


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def fingerprints(signature: dict[str, Any]) -> dict[str, Any]:
    return {
        "queries": {key: digest(value) for key, value in signature["queries"].items()},
        "uses": digest(signature["uses"]),
        "metrics": signature["metrics"],
    }


def paired_signature(result: dict[str, Any]) -> dict[str, Any]:
    signature = run_signature(result)
    for query in signature["queries"].values():
        query["metrics"] = {
            k: v for k, v in query["metrics"].items() if not k.startswith("source_")
        }
    signature.pop("metrics")
    # Source observation equality is checked separately; pass reports differ by design.
    signature["sources"] = {}
    for query in result["query_results"]:
        if query.get("source_assessment"):
            source = dict(query["source_assessment"])
            for key in (
                "decisions",
                "decisions_available",
                "decisions_complete",
                "decisions_truncated",
            ):
                source.pop(key)
            signature["sources"][query["query_id"]] = source
    return signature


async def run(
    dataset: str, profile: str, *, diagnostics: bool | None = None, postgres_url: str | None = None
) -> dict[str, Any]:
    from cogkurabench.backends.registry import create_backend

    data = load_dataset(dataset)
    backend = create_backend(profile, data)
    if diagnostics is not None or postgres_url is not None:
        # Reconstruct the named profile using its public constructor options.
        source = profile.startswith("cogkura-source")
        authority = source or "authority" in profile or "correction" in profile
        backend = CogKuraBackend(
            apply_interference=profile == "cogkura-interference",
            inhibition_enabled=profile.startswith("cogkura-inhibition"),
            apply_inhibition=profile == "cogkura-inhibition",
            minimum_supporting_episodes=2 if authority else 1,
            allow_authoritative_single_episode=authority and profile != "cogkura-authority-control",
            inspect_source_authority="authority" in profile,
            corrections_enabled=(profile != "cogkura-correction-control")
            if source or "correction" in profile
            else None,
            source_assessment=source,
            semantic_diagnostics=bool(diagnostics),
            postgres_url=postgres_url,
            name=profile,
        )
    try:
        return result_to_dict(await BenchmarkRunner().run(data, backend, write_results=False))
    finally:
        if isinstance(backend, CogKuraBackend):
            await backend.close()


def canonical_source(source: dict[str, Any]) -> dict[str, Any]:
    source = dict(source)
    # Tuple ordering of unrelated diagnostic records is not a semantic identity.
    for key in ("revisions", "decisions"):
        source[key] = sorted(source[key], key=lambda item: json.dumps(item, sort_keys=True))
    return source


async def postgres_parity() -> dict[str, Any]:
    url = os.environ.get("COGKURA_POSTGRES_MEMORY_URL")
    if not url:
        return {"status": "NOT EXECUTED", "reason": "COGKURA_POSTGRES_MEMORY_URL unset"}
    from cogkura import Memory
    from cogkura.migrations import apply_migrations
    from cogkura.storage.postgres import (
        PostgresEpisodeStore,
        PostgresObservationStore,
        PostgresSemanticMemoryStore,
    )
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url)
    try:
        await apply_migrations(engine)
        memory = Memory(
            observation_store=PostgresObservationStore(engine),
            episode_store=PostgresEpisodeStore(engine),
            semantic_store=PostgresSemanticMemoryStore(engine),
        )
        dataset = "source_aware_metamemory_v1"
        for tenant in {e.tenant_id for e in load_dataset(dataset).events}:
            await memory.clear(tenant_id=tenant)
        reference = await run(dataset, "cogkura-source", diagnostics=True)
        postgres = await run(dataset, "cogkura-source", diagnostics=True, postgres_url=url)
        mismatches = []
        for left, right in zip(reference["query_results"], postgres["query_results"], strict=True):
            a = canonical_source(left["source_assessment"])
            b = canonical_source(right["source_assessment"])
            fields = [key for key in a if a[key] != b[key]]
            if fields:
                mismatches.append(
                    {
                        "query_id": left["query_id"],
                        "fields": fields,
                        "memory": {key: a[key] for key in fields},
                        "postgres": {key: b[key] for key in fields},
                    }
                )
        return {
            "status": "FAIL" if mismatches else "PASS",
            "mismatches": mismatches,
            "declared_metrics": postgres["capability_results"]["source_assessment"]["metrics"],
        }
    finally:
        await engine.dispose()


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline", type=Path, default=Path("tests/golden/cogkura_0182_frozen.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--diagnostics-parity", action="store_true")
    parser.add_argument("--postgres", action="store_true")
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use a fresh process with PYTHONHASHSEED=0; Core must not be imported yet")
    rng = random.Random(183)

    def fixture_uuid() -> uuid.UUID:
        return uuid.UUID(int=rng.getrandbits(128), version=4)

    uuid.uuid4 = fixture_uuid
    import cogkura

    output: dict[str, Any] = {
        "core_version": cogkura.__version__,
        "seed": 183,
        "hash_seed": 0,
        "runs": {},
        "diagnostic_mismatches": [],
    }
    for dataset, profile in RUNS:
        state = rng.getstate()
        reference = await run(dataset, profile)
        after = rng.getstate()
        key = dataset + "/" + profile
        output["runs"][key] = fingerprints(run_signature(reference))
        if args.diagnostics_parity:
            rng.setstate(state)
            observed = await run(dataset, profile, diagnostics=True)
            if paired_signature(reference) != paired_signature(observed):
                output["diagnostic_mismatches"].append(key)
            if rng.getstate() != after:
                output["diagnostic_mismatches"].append(key + "/storage-allocation")
        print(key, len(reference["query_results"]), flush=True)
    if args.diagnostics_parity:
        rng.seed(183)
        control = await run("source_aware_metamemory_v1", "cogkura-source-control")
        rng.seed(183)
        enabled = await run("source_aware_metamemory_v1", "cogkura-source", diagnostics=True)
        if paired_signature(control) != paired_signature(enabled):
            output["diagnostic_mismatches"].append("source_aware_metamemory_v1")
        output["source_metrics"] = enabled["capability_results"]["source_assessment"]["metrics"]
    if args.write_baseline:
        args.baseline.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    baseline = json.loads(args.baseline.read_text())
    output["frozen_mismatches"] = [
        k for k in output["runs"] if output["runs"][k] != baseline["runs"].get(k)
    ]
    if args.postgres:
        output["postgres"] = await postgres_parity()
    output["release_gate_passed"] = (
        not output["frozen_mismatches"]
        and not output["diagnostic_mismatches"]
        and output.get("postgres", {}).get("status") == "PASS"
        and output.get("source_metrics", {}).get("source_assessment_accuracy") == 1
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {k: v for k, v in output.items() if k not in ("runs", "source_metrics")}, indent=2
        )
    )
    return 0 if output["release_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
