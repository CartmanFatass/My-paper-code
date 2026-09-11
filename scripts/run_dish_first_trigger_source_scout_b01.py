from __future__ import annotations

import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.degraded_incumbent_shadow_handover.first_trigger_source_scout_b01.study import run_seed


UPDATES = 64
SECONDS_PER_UPDATE = 10.672341100056656
FIXED_SECONDS = 300.0
MARGIN = 1.5
CAP_SECONDS = 1_800.0
ARMS = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_uint32), ("page_fault_count", ctypes.c_uint32),
        ("peak_working_set_size", ctypes.c_size_t), ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_nonpaged_pool_usage", ctypes.c_size_t),
        ("quota_nonpaged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t), ("peak_pagefile_usage", ctypes.c_size_t),
    ]


def _peak_rss_bytes() -> int:
    if sys.platform != "win32":
        import resource

        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    counters = _ProcessMemoryCounters(); counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.peak_working_set_size)


def projected_seconds() -> float:
    return MARGIN * (UPDATES * SECONDS_PER_UPDATE + FIXED_SECONDS)


def project_cost() -> dict[str, object]:
    seconds = projected_seconds()
    return {
        "mode": "project-cost",
        "law": "1.5 * (updates * 10.672341100056656 + 300)",
        "updates": UPDATES, "cap_seconds": CAP_SECONDS,
        "seed_rows": [
            {"seed": seed, "projected_seed_seconds": seconds}
            for seed in (11, 29, 47)
        ],
        "arm_rows": [
            {"arm": arm, "full_seed_charge_seconds": seconds, "within_cap": seconds <= CAP_SECONDS}
            for arm in ARMS
        ],
    }


def _run(seed: int, admission: Path, output: Path) -> dict[str, object]:
    receipt = json.loads(admission.read_text(encoding="utf-8"))
    if not (
        receipt.get("passed") is True
        and receipt.get("physical_floor_pass") is True
        and receipt.get("effective_floor_pass") is True
        and int(receipt.get("available_physical_bytes", 0)) >= 2**32
        and int(receipt.get("effective_available_bytes", 0)) >= 2**32
    ):
        raise RuntimeError("fresh memory admission did not pass")
    launch_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    summary, checkpoint = run_seed(seed, launch_sha=launch_sha)
    try:
        peak_rss = _peak_rss_bytes(); resources_unmeasured = False
    except OSError:
        peak_rss = None; resources_unmeasured = True
    result = {
        "object": "DISH-FIRST-TRIGGER-SOURCE-SCOUT-B01", "launch_sha": launch_sha,
        "admission_receipt": str(admission.resolve()), "peak_rss_bytes": peak_rss,
        "resources_unmeasured": resources_unmeasured,
        **summary,
    }
    output.mkdir(parents=True)
    (output / "checkpoint.pt").write_bytes(checkpoint)
    (output / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    modes.add_parser("project-cost")
    run = modes.add_parser("run")
    run.add_argument("--seed", type=int, choices=(11, 29, 47), required=True)
    run.add_argument("--admission", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    payload = project_cost() if args.mode == "project-cost" else _run(args.seed, args.admission, args.out)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
