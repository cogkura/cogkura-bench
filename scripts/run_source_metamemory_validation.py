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
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import re
import sqlite3
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


def validate_approval(
    manifest: dict[str, Any], baseline_bytes: bytes, identity: dict[str, Any]
) -> None:
    """Fail closed before running an explicitly approved, exact candidate comparison."""
    if (
        set(manifest)
        != {
            "schema_version",
            "candidate",
            "baseline_sha256",
            "approved_on",
            "reason",
            "corrections",
        }
        or manifest["schema_version"] != 1
    ):
        raise ValueError("unsupported reviewed-correction manifest")
    candidate = manifest["candidate"]
    if not isinstance(candidate, dict) or set(candidate) != {"version", "commit"}:
        raise ValueError("candidate must name an exact version and Git commit")
    if not re.fullmatch(r"[0-9a-f]{40}", str(candidate["commit"])):
        raise ValueError("candidate commit must be a full Git commit")
    if (
        identity.get("version") != candidate["version"]
        or identity.get("distribution_version") != candidate["version"]
        or identity.get("commit") != candidate["commit"]
        or identity.get("vcs") != "git"
        or identity.get("url") != "https://github.com/cogkura/cogkura.git"
        or identity.get("installed_module") is not True
    ):
        raise ValueError("installed Core version/Git distribution does not match approval")
    if hashlib.sha256(baseline_bytes).hexdigest() != manifest["baseline_sha256"]:
        raise ValueError("original frozen baseline digest does not match approval")
    if not manifest["reason"] or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", str(manifest["approved_on"])
    ):
        raise ValueError("approval requires a reason and date")
    corrections = manifest["corrections"]
    if not isinstance(corrections, list) or len(corrections) != 1:
        raise ValueError("this review approves exactly one correction")
    correction = corrections[0]
    if not isinstance(correction, dict) or set(correction) != {"run", "query", "before", "after"}:
        raise ValueError("correction must name a run, query and before/after hashes")
    if not all(isinstance(correction[k], str) and correction[k] for k in correction):
        raise ValueError("correction values must be nonempty strings")
    if not all(re.fullmatch(r"[0-9a-f]{64}", correction[k]) for k in ("before", "after")):
        raise ValueError("correction fingerprints must be SHA256 digests")
    if correction["before"] == correction["after"]:
        raise ValueError("correction must require a changed fingerprint")
    baseline = json.loads(baseline_bytes)
    old = baseline["runs"].get(correction["run"], {}).get("queries", {}).get(correction["query"])
    if old != correction["before"]:
        raise ValueError("approved before fingerprint is absent from original baseline")


def compare_frozen(
    runs: dict[str, Any], baseline: dict[str, Any], manifest: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Keep the raw comparison; account separately for the reviewed exact change.

    The caller validates the manifest against the installed distribution and gold
    bytes first. Only a matched query hash is accounted for; run metrics, uses,
    populations and all other fields still participate in the exact comparison.
    """
    old_runs = baseline["runs"]
    keys = sorted(runs.keys() | old_runs.keys())
    raw = [k for k in keys if k not in runs or k not in old_runs or runs[k] != old_runs[k]]
    accounted = copy.deepcopy(runs)
    approved = []
    errors = []
    for correction in manifest["corrections"] if manifest else []:
        key, query = correction["run"], correction["query"]
        before = old_runs.get(key, {}).get("queries", {}).get(query)
        after = runs.get(key, {}).get("queries", {}).get(query)
        if before != correction["before"] or after != correction["after"]:
            errors.append(f"expected reviewed correction missing or changed: {key}/{query}")
            continue
        approved.append(dict(correction))
        accounted[key]["queries"][query] = before
    unapproved = [
        k for k in keys if k not in accounted or k not in old_runs or accounted[k] != old_runs[k]
    ]
    return {
        "frozen_mismatches": raw,
        "raw_frozen_comparison_passed": not raw,
        "approved_frozen_corrections": approved,
        "unapproved_frozen_mismatches": unapproved,
        "approval_errors": errors,
    }


def core_identity(core: Any) -> dict[str, Any]:
    distribution = importlib.metadata.distribution("cogkura")
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    return {
        "version": core.__version__,
        "distribution_version": distribution.version,
        "commit": direct.get("vcs_info", {}).get("commit_id"),
        "vcs": direct.get("vcs_info", {}).get("vcs"),
        "url": direct.get("url"),
        "installed_module": Path(core.__file__).resolve().parent
        == Path(distribution.locate_file("cogkura")).resolve(),
    }


def source_checks_pass(report: dict[str, Any], *, allow_history_v2: bool = False) -> bool:
    """Require v1 by default; the opt-in v2 path accounts for exactly one known check."""
    v1 = report.get("source_metrics", {})
    if not allow_history_v2:
        return v1.get("source_assessment_accuracy") == 1
    history = report.get("source_history_v2", {})
    v2 = history.get("metrics", {})
    withdrawn = history.get("v1_withdrawn_metrics", {})
    return bool(
        report.get("source_fixture") == "source_aware_metamemory_v2"
        and v1.get("source_assessment_check_count") == 191
        and v1.get("source_assessment_match_count") == 190
        and v1.get("source_assessment_mismatch_count") == 1
        and withdrawn.get("source_assessment_mismatch_count") == 1
        and v2.get("source_assessment_check_count") == 191
        and v2.get("source_assessment_match_count") == 191
        and v2.get("source_assessment_mismatch_count") == 0
        and v2.get("source_assessment_accuracy") == 1
        and history.get("outputs_match_v1") is True
        and history.get("transition_event_ids") == ["sm-chain-replace", "sm-chain-withdraw"]
        and history.get("postgres", {}).get("status") == "PASS"
    )


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


async def postgres_parity(dataset: str = "source_aware_metamemory_v1") -> dict[str, Any]:
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
    parser.add_argument(
        "--details-output", type=Path, help="write full query signatures separately"
    )
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--diagnostics-parity", action="store_true")
    parser.add_argument("--postgres", action="store_true")
    parser.add_argument("--approved-corrections", type=Path)
    parser.add_argument(
        "--source-history-v2",
        action="store_true",
        help="also run the versioned complete-transition fixture for candidate review",
    )
    args = parser.parse_args()
    if args.write_baseline and args.approved_corrections:
        parser.error("reviewed corrections cannot be used to write a baseline")
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use a fresh process with PYTHONHASHSEED=0; Core must not be imported yet")
    rng = random.Random(183)

    def fixture_uuid() -> uuid.UUID:
        return uuid.UUID(int=rng.getrandbits(128), version=4)

    uuid.uuid4 = fixture_uuid
    import cogkura

    if args.write_baseline and cogkura.__version__ != "0.18.2":
        parser.error("the frozen baseline must be captured with unchanged Core 0.18.2")
    identity = core_identity(cogkura)
    manifest = None
    if args.approved_corrections:
        try:
            manifest = json.loads(args.approved_corrections.read_text())
            validate_approval(manifest, args.baseline.read_bytes(), identity)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            parser.error(str(exc))
    output: dict[str, Any] = {
        "core_version": cogkura.__version__,
        "core_distribution": identity,
        "python": sys.version,
        "platform": platform.platform(),
        "sqlite_version": sqlite3.sqlite_version,
        "seed": 183,
        "hash_seed": 0,
        "runs": {},
        "diagnostic_mismatches": [],
    }
    if args.source_history_v2:
        output["source_fixture"] = "source_aware_metamemory_v2"
    details: dict[str, Any] = {}
    for dataset, profile in RUNS:
        state = rng.getstate()
        reference = await run(dataset, profile)
        after = rng.getstate()
        key = dataset + "/" + profile
        signature = run_signature(reference)
        output["runs"][key] = fingerprints(signature)
        if args.details_output:
            details[key] = signature
        if args.diagnostics_parity:
            rng.setstate(state)
            observed = await run(dataset, profile, diagnostics=True)
            if paired_signature(reference) != paired_signature(observed):
                output["diagnostic_mismatches"].append(key)
            if rng.getstate() != after:
                output["diagnostic_mismatches"].append(key + "/storage-allocation")
        print(key, len(reference["query_results"]), flush=True)
    if args.details_output:
        args.details_output.parent.mkdir(parents=True, exist_ok=True)
        args.details_output.write_text(json.dumps(details, indent=2, sort_keys=True) + "\n")
    if args.diagnostics_parity:
        rng.seed(183)
        control = await run("source_aware_metamemory_v1", "cogkura-source-control")
        rng.seed(183)
        enabled = await run("source_aware_metamemory_v1", "cogkura-source", diagnostics=True)
        if paired_signature(control) != paired_signature(enabled):
            output["diagnostic_mismatches"].append("source_aware_metamemory_v1")
        output["source_metrics"] = enabled["capability_results"]["source_assessment"]["metrics"]
        if args.source_history_v2:
            rng.seed(183)
            history = await run("source_aware_metamemory_v2", "cogkura-source", diagnostics=True)
            old_query = next(q for q in enabled["query_results"] if q["query_id"] == "sm-withdrawn")
            new_query = next(q for q in history["query_results"] if q["query_id"] == "sm-withdrawn")
            output["source_history_v2"] = {
                "metrics": history["capability_results"]["source_assessment"]["metrics"],
                "v1_withdrawn_metrics": old_query["metrics"],
                "transition_event_ids": new_query["source_assessment"]["transition_event_ids"],
                "outputs_match_v1": paired_signature(enabled) == paired_signature(history)
                and [q["source_assessment"] for q in enabled["query_results"]]
                == [q["source_assessment"] for q in history["query_results"]],
            }
    if args.write_baseline:
        args.baseline.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    baseline = json.loads(args.baseline.read_text())
    output.update(compare_frozen(output["runs"], baseline, manifest))
    if args.approved_corrections:
        output["reviewed_correction_manifest"] = manifest
    if args.postgres:
        output["postgres"] = await postgres_parity()
        if args.source_history_v2 and "source_history_v2" in output:
            output["source_history_v2"]["postgres"] = await postgres_parity(
                "source_aware_metamemory_v2"
            )
    output["release_gate_passed"] = (
        not output["unapproved_frozen_mismatches"]
        and not output["approval_errors"]
        and not output["diagnostic_mismatches"]
        and output.get("postgres", {}).get("status") == "PASS"
        and source_checks_pass(output, allow_history_v2=args.source_history_v2)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {k: v for k, v in output.items() if k not in ("runs", "source_metrics")}, indent=2
        )
    )
    return 0 if args.write_baseline or output["release_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
