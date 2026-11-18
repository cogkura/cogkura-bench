#!/usr/bin/env python3
"""Trace text weights for the correction-history investigation, not a release run."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import uuid
from pathlib import Path
from typing import Any

QUERIES = ("ac-q-c17", "ac-q-hist-at-withdraw", "ac-q-hist-before-withdraw")
STAMPS = {
    "2026-11-10T12:00:00+00:00",
    "2026-11-12T10:00:00+00:00",
    "2026-11-12T11:00:00+00:00",
}
CUES = {"What is the current migration strategy?", "payments-api migration execution strategy"}


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--override-from", type=Path)
    args = parser.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0" or "cogkura" in sys.modules:
        parser.error("use a fresh process with PYTHONHASHSEED=0")
    rng = random.Random(183)
    uuid.uuid4 = lambda: uuid.UUID(int=rng.getrandbits(128), version=4)

    import cogkura
    from cogkura.algorithms import activation
    from run_source_metamemory_validation import core_identity, run, run_signature

    weights: dict[tuple[str, str], Any] = {}
    if args.override_from:
        for entry in json.loads(args.override_from.read_text())["trace"]:
            key = (entry["as_of"], entry["cue"])
            if key in weights and weights[key] != entry["weights"]:
                raise ValueError(f"ambiguous baseline weights: {key}")
            weights[key] = entry["weights"]
    trace: list[dict[str, Any]] = []
    original = activation._score_candidate

    def score(candidate: Any, **kwargs: Any) -> Any:
        key = (kwargs["as_of"].isoformat(), kwargs["cue"].text)
        if key[0] in STAMPS and key[1] in CUES:
            if args.override_from:
                if key not in weights:
                    raise ValueError(f"baseline weights missing: {key}")
                kwargs["idf_weights"] = weights[key]
            trace.append(
                {
                    "as_of": key[0],
                    "cue": key[1],
                    "text": candidate.text,
                    "weights": kwargs["idf_weights"],
                }
            )
        return original(candidate, **kwargs)

    activation._score_candidate = score
    result = await run("authoritative_corrections_v1", "cogkura-correction")
    signature = run_signature(result)
    output = {
        "core_distribution": core_identity(cogkura),
        "python": sys.version,
        "seed": 183,
        "hash_seed": 0,
        "override_from": str(args.override_from) if args.override_from else None,
        "trace": trace,
        "queries": {key: signature["queries"][key] for key in QUERIES},
    }
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
