#!/usr/bin/env python3
"""Measure default versus IDF-off as a diagnostic, not a release timing gate."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-checkout", type=Path, required=True)
    parser.add_argument("--policy", choices=("default", "idf-off"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str((args.core_checkout / "scripts").resolve()))
    import cogkura
    from profile_retrieval import run

    if args.policy == "idf-off":
        original = cogkura.Memory.__init__

        def init_with_idf_off(self: Any, **kwargs: Any) -> None:
            config = kwargs.get("activation_config") or cogkura.ActivationConfig()
            kwargs["activation_config"] = replace(config, enable_candidate_idf=False)
            original(self, **kwargs)

        cogkura.Memory.__init__ = init_with_idf_off
    result = asyncio.run(run(250, 5, 30, "memory", profile=False))
    result["experimental_policy"] = args.policy
    result["diagnostic_only"] = True
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
