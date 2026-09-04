"""Exact resource-guarded CLI for one leased R06 full-panel slice."""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--lease-loader", required=True, help="module:function returning exact authority and data plane")
    parser.add_argument("--lease", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--max-units", type=int, required=True)
    parser.parse_args()
    refusal = {
        "schema": "DISH_RBHR_R06_FULL_PANEL_HOLD_REFUSAL_V1",
        "status": "NOT_READY",
        "exit_code": 2,
        "reason": "LEGACY_R06_OBJECT_NOT_CURRENT_SOURCE_FACTORED_PATH_ONLY",
        "legacy_object": "DISH_RBHR_R06_FULL_PANEL",
        "current_object": "DISH-BLOCK-CERTIFICATE-PREVALENCE-R02",
        "legacy_24_block_bootstrap_allowed": False,
        "lease_loader_imported": False,
        "run_root_created": False,
        "master_created": False,
        "checkpoint_created": False,
        "result_created": False,
    }
    print(json.dumps(refusal, sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
