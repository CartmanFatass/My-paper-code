"""Sole command-line entry point for the frozen EGRCR-T3 prerequisite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
import traceback

from . import prerequisite_config as C
from .prerequisite_experiment import run_prerequisite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all",), required=True)
    parser.add_argument("--result-output", required=True)
    return parser


def _write_json_atomic(path: str, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _technical_stop(exc: BaseException, result_path: str, started: float) -> dict[str, object]:
    return {
        "artifact_kind": C.ARTIFACT_KIND,
        "artifact_schema_version": C.ARTIFACT_SCHEMA_VERSION,
        "treatment": C.TREATMENT,
        "starting_commit": C.STARTING_COMMIT,
        "artifact_identity": {
            "treatment": C.TREATMENT,
            "starting_commit": C.STARTING_COMMIT,
            "implementation": "isolated-dependency-free-three-agent-finite-host",
            "result_path": result_path,
        },
        "stage": "technical_stop",
        "branch": "representation_or_comparator_invalid",
        "interpretation_valid": False,
        "scientific_null": False,
        "complete_terminal_artifact": True,
        "error": {"type": type(exc).__name__, "message": str(exc)},
        "traceback": traceback.format_exc(),
        "frozen": {
            "calibration_roots": list(C.CALIBRATION_ROOTS),
            "confirmation_roots": list(C.CONFIRMATION_ROOTS),
            "lambda_candidates": list(C.GAE_LAMBDAS),
            "namespaces": dict(C.NAMESPACES),
            "selected_lambda": None,
            "trust_scale": None,
        },
        "support": None,
        "noiseless_competence": None,
        "per_root": [],
        "intervals": {},
        "criteria": {},
        "accounting": {
            "three_agent_physical_ticks": 0,
            "physical_tick_cap": C.MAX_THREE_AGENT_PHYSICAL_TICKS,
            "cpu_workers": 1,
            "restarts": 0,
            "sweeps": 0,
            "seed_replacement": False,
            "threshold_repair": False,
            "post_result_enlargement": False,
        },
        "anomalies": ["unhandled technical exception"],
        "runtime_seconds": time.perf_counter() - started,
        "cap_status": {
            "wall_seconds_limit": C.MAX_WALL_SECONDS,
            "rss_bytes_limit": C.MAX_RSS_BYTES,
            "physical_tick_limit": C.MAX_THREE_AGENT_PHYSICAL_TICKS,
            "one_cpu_worker": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    started = time.perf_counter()
    try:
        result = run_prerequisite()
        result["artifact_identity"]["result_path"] = args.result_output
    except BaseException as exc:  # terminal witness must retain technical stops
        result = _technical_stop(exc, args.result_output, started)
    _write_json_atomic(args.result_output, result)
    print(
        json.dumps(
            {
                "artifact_kind": result["artifact_kind"],
                "branch": result["branch"],
                "path": args.result_output,
                "stage": result["stage"],
            },
            sort_keys=True,
        )
    )
    if result["stage"] == "technical_stop":
        return 4
    if result["branch"] == "representation_or_comparator_invalid":
        return 3
    if not result.get("complete_terminal_artifact", False):
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
