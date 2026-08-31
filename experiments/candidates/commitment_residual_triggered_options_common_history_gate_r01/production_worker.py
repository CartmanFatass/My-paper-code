"""Isolated CRTO production worker; native thread environment is set by its parent."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence


_THREAD_ENVIRONMENT = (
    "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
)
_WORKER_ENV = "HMASD_CRTO_PRODUCTION_WORKER"
_WORKER_SENTINEL = "CRTO-COMMON-HISTORY-GATE-20260830-01"


def _require_process_environment() -> None:
    failures = [name for name in _THREAD_ENVIRONMENT if os.environ.get(name) != "1"]
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        failures.append("CUDA_VISIBLE_DEVICES")
    if os.environ.get(_WORKER_ENV) != _WORKER_SENTINEL:
        failures.append(_WORKER_ENV)
    if failures:
        raise RuntimeError(
            "isolated CRTO worker thread/GPU environment was not bound before import: "
            + ", ".join(failures)
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="CRTO-COMMON-HISTORY-GATE-PRODUCTION-WORKER")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--preflight-receipt", type=Path, required=True)
    parser.add_argument("--launch-resource-receipt", type=Path, required=True)
    parser.add_argument("--launch-run-resource-receipt", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _require_process_environment()
    arguments = build_parser().parse_args(argv)
    try:
        preflight = json.loads(arguments.preflight_receipt.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"prospective preflight receipt is unreadable: {error}") from error
    if not isinstance(preflight, dict):
        raise RuntimeError("prospective preflight receipt must be a JSON object")
    # This import is deliberately after the process-start environment check.
    from .production import execute_fresh_pipeline

    execute_fresh_pipeline(
        output_root=arguments.output_root,
        result_path=arguments.result,
        preflight=preflight,
        launch_resource_receipt_path=arguments.launch_resource_receipt,
        launch_run_resource_receipt_path=arguments.launch_run_resource_receipt,
    )
    print(json.dumps({
        "status": "PUBLISHED",
        "object_id": _WORKER_SENTINEL,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
