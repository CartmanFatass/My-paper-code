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
    args = parser.parse_args()
    root = args.repository_root.resolve(); sys.path.insert(0, str(root))
    module_name, function_name = args.lease_loader.split(":", 1)
    loader = getattr(importlib.import_module(module_name), function_name)
    authority, data_plane = loader(repository_root=root, lease_path=args.lease.resolve(), request_path=args.request.resolve())
    from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_full_panel import FullPanelExecutor
    value = FullPanelExecutor(authority=authority, data_plane=data_plane, run_root=args.run_root.resolve()).run_slice(max_units=args.max_units)
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0 if value["status"] in ("COMPLETE", "SLICE_COMPLETE", "HARD_GUARD") else 2


if __name__ == "__main__":
    raise SystemExit(main())
