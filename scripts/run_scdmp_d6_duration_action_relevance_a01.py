"""Run SCDMP-D6-DURATION-ACTION-RELEVANCE-A01 or its sole technical smoke."""

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

from experiments.candidates.scdmp_variable_k.d6_duration_action_relevance_a01 import (
    decide_branch,
    run_census,
    run_technical_smoke,
)
from experiments.candidates.scdmp_variable_k.d6_duration_action_relevance_a01.native import Host


OBJECT_ID = "SCDMP-D6-DURATION-ACTION-RELEVANCE-A01"
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


def _metadata(started: float, launch_sha: str, args: argparse.Namespace) -> dict[str, object]:
    peak = _peak_rss()
    return {
        "object_id": OBJECT_ID,
        "fixed_seed": args.seed,
        "launch_sha": launch_sha,
        "command": "run",
        "projected_seconds": args.projected_seconds,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak,
        "resources_unmeasured": peak is None,
    }


def _branch(*, resource_ready: bool, integrity_valid: bool) -> str:
    return decide_branch(
        resource_ready=resource_ready,
        integrity_valid=integrity_valid,
        source_population_established=True,
        w=0,
        r7=0,
        r13=0,
    )


def _run(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    output = args.output_root.resolve(strict=False)
    summary_path = output / "summary.json"
    launch_sha = _launch_sha()
    projection = args.projected_seconds
    if args.seed != 9029 or projection is None or not 0 < projection <= CAP_SECONDS:
        result = {
            "branch": _branch(resource_ready=False, integrity_valid=False),
            "reason": "fixed seed must be 9029 and the prospective projection must be present in (0, 1800]",
        }
        result.update(_metadata(started, launch_sha, args))
        _write(summary_path, result)
        return 0


    completed = subprocess.run([
        sys.executable,
        str(ROOT / "scripts" / "hmasd_resource_preflight.py"),
        "admit-memory",
        "--out",
        str(args.receipt.resolve(strict=False)),
    ])
    admission = (
        json.loads(args.receipt.read_text(encoding="utf-8"))
        if args.receipt.is_file()
        else {}
    )
    if completed.returncode != 0 or admission.get("passed") is not True:
        result = {
            "branch": _branch(resource_ready=False, integrity_valid=False),
            "reason": "mandatory 4 GiB physical/effective admission failed",
            "admission_passed": False,
            "admission_receipt": str(args.receipt.resolve(strict=False)),
        }
        result.update(_metadata(started, launch_sha, args))
        _write(summary_path, result)
        return 0


    deadline = started + CAP_SECONDS
    try:
        with tempfile.TemporaryDirectory(prefix="scdmp-a01-run-") as directory:
            with Host(Path(directory)) as host:
                result = run_census(host, deadline=deadline)
    except Exception as error:
        result = {
            "branch": _branch(resource_ready=True, integrity_valid=False),
            "integrity_valid": False,
            "reason": str(error),
        }
    result["admission_passed"] = True
    result["admission_receipt"] = str(args.receipt.resolve(strict=False))
    result.update(_metadata(started, launch_sha, args))
    _write(summary_path, result)
    return 0


def _smoke(args: argparse.Namespace) -> int:
    output = args.output.resolve(strict=False)
    technical = run_technical_smoke(output.parent / "native-build")
    _write(output, technical)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--seed", type=int, required=True, help="fixed scientific seed/domain")
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
