"""Run SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02 or its smoke."""

from __future__ import annotations

import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.scdmp_variable_k.d6_event_phase_duration_action_relevance_a02 import (
    decide_branch,
    run_census,
    run_technical_smoke,
)
from experiments.candidates.scdmp_variable_k.d6_event_phase_duration_action_relevance_a02.native import (
    Host,
)


OBJECT_ID = "SCDMP-D6-EVENT-PHASE-DURATION-ACTION-RELEVANCE-A02"
CAP_SECONDS = 1800.0


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _peak_rss() -> int | None:
    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    try:
        if ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb,
        ):
            return int(counters.PeakWorkingSetSize)
    except OSError:
        pass
    return None


def _launch_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _no_result(reason: str) -> dict[str, object]:
    return {
        "object_id": OBJECT_ID,
        "branch": decide_branch(
            resource_ready=False, integrity_valid=False, population_established=False,
            k7=0, k78=0, n7_plus=0, n7_minus=0, n78_minus=0, n78_plus=0,
            all_zero=False,
        ),
        "reason": reason,
    }


def _zero_inventory() -> dict[str, int]:
    return {
        "source_trajectories": 0, "source_renewals": 0, "source_transitions": 0,
        "candidate_missions": 0, "candidate_renewals": 0, "candidate_transitions": 0,
        "native_missions": 0, "native_transitions": 0, "evaluator_calls": 0,
        "models": 0, "training_datasets": 0, "optimizer_updates": 0,
        "adamw_steps": 0, "learner_evaluations": 0,
    }


def _invalid_branch() -> str:
    return decide_branch(
        resource_ready=True, integrity_valid=False, population_established=True,
        k7=0, k78=0, n7_plus=0, n7_minus=0, n78_minus=0, n78_plus=0,
        all_zero=False,
    )


def _invalid_result(reason: str) -> dict[str, object]:
    return {
        "branch": _invalid_branch(),
        "integrity_valid": False,
        "population_established": False,
        "reason": reason,
        "counts": _zero_inventory(),
        "exposure": "NO_LEARNED_PARAMETERS — exposure not applicable",
    }


def _run(args: argparse.Namespace) -> int:
    projection = args.projected_seconds
    if args.seed != 9173 or projection is None or not 0 < projection <= CAP_SECONDS:
        print(json.dumps(_no_result(
            "fixed seed must be 9173 and the prospective projection must be present in (0, 1800]",
        ), sort_keys=True))
        return 2
    completed = subprocess.run([
        sys.executable, str(ROOT / "scripts" / "hmasd_resource_preflight.py"),
        "admit-memory", "--out", str(args.receipt.resolve(strict=False)),
    ])
    admission = json.loads(args.receipt.read_text(encoding="utf-8")) if args.receipt.is_file() else {}
    if completed.returncode != 0 or admission.get("passed") is not True:
        print(json.dumps(_no_result("mandatory 4 GiB physical/effective admission failed"), sort_keys=True))
        return 2

    started = time.perf_counter()
    launch_sha = _launch_sha()
    result: dict[str, object] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="scdmp-a02-run-") as directory:
            with Host(Path(directory)) as host:
                result = run_census(host, deadline=started + CAP_SECONDS)
    except Exception as error:
        if result is None:
            result = _invalid_result(f"host construction or pre-census execution failed: {error}")
        else:
            previous = result.get("reason")
            result["branch"] = _invalid_branch()
            result["integrity_valid"] = False
            result["reason"] = (
                f"{previous}; native host or temporary-directory cleanup failed: {error}"
                if previous else f"native host or temporary-directory cleanup failed: {error}"
            )
    peak = _peak_rss()
    result.update({
        "object_id": OBJECT_ID,
        "fixed_seed": args.seed,
        "launch_sha": launch_sha,
        "command": "run",
        "projected_seconds": projection,
        "admission_passed": True,
        "admission_receipt": str(args.receipt.resolve(strict=False)),
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak,
        "resources_unmeasured": peak is None,
    })
    _write(args.output_root.resolve(strict=False) / "summary.json", result)
    return 0


def _smoke(args: argparse.Namespace) -> int:
    output = args.output.resolve(strict=False)
    with tempfile.TemporaryDirectory(prefix="scdmp-a02-smoke-") as directory:
        build_root = Path(directory)
        technical = run_technical_smoke(build_root)
        inspection_source = output.parent / "native-build" / "d6_a02_native.cpp"
        inspection_source.parent.mkdir(parents=True, exist_ok=True)
        inspection_source.write_bytes((build_root / "d6_a02_native.cpp").read_bytes())
    _write(output, technical)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--seed", type=int, required=True)
    commands = result.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--output-root", type=Path, required=True)
    run.add_argument("--receipt", type=Path, required=True)
    run.add_argument("--projected-seconds", type=float)
    smoke = commands.add_parser("smoke")
    smoke.add_argument("--output", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return _smoke(args) if args.command == "smoke" else _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
