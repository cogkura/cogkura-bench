#!/usr/bin/env python3
"""Compare the existing IDF-off option to default scoring without changing Core.

Run each mode in a fresh process with PYTHONHASHSEED=0. This is diagnostic,
not a release validator or an approval of a changed ranking policy.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from run_source_metamemory_validation import RUNS, clean, core_identity, run, run_signature


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=("default", "idf-off"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use a fresh process with PYTHONHASHSEED=0")
    rng = random.Random(183)
    uuid.uuid4 = lambda: uuid.UUID(int=rng.getrandbits(128), version=4)
    import cogkura

    if args.policy == "idf-off":
        # Set the real public configuration in the diagnostic process, without
        # changing benchmark adapters or the installed Core distribution.
        original_init = cogkura.Memory.__init__

        def init_with_idf_off(self: Any, **kwargs: Any) -> None:
            config = kwargs.get("activation_config") or cogkura.ActivationConfig()
            kwargs["activation_config"] = replace(config, enable_candidate_idf=False)
            original_init(self, **kwargs)

        cogkura.Memory.__init__ = init_with_idf_off
    output: dict[str, Any] = {
        "policy": args.policy,
        "diagnostic_only": True,
        "core_distribution": core_identity(cogkura),
        "python": sys.version,
        "seed": 183,
        "hash_seed": 0,
        "runs": {},
        "source_v2": {},
    }
    for dataset, profile in RUNS:
        result = await run(dataset, profile)
        output["runs"][dataset + "/" + profile] = run_signature(result)
        print(dataset + "/" + profile, len(result["query_results"]), flush=True)
    rng.seed(183)
    source = await run("source_aware_metamemory_v2", "cogkura-source", diagnostics=True)
    output["source_v2"] = {
        "metrics": clean(source["capability_results"]["source_assessment"]["metrics"]),
        "queries": {q["query_id"]: clean(q["source_assessment"]) for q in source["query_results"]},
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
