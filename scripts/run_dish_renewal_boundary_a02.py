"""DISH-RENEWAL-BOUNDARY-A02-CORRECTION entry. Thread env is set before torch is imported."""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import argparse
import ctypes
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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


def peak_rss_bytes():
    if sys.platform != "win32":
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(_ProcessMemoryCounters), ctypes.c_uint32,
    ]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise OSError("GetProcessMemoryInfo failed")
    return int(counters.peak_working_set_size)


def _log(stream, message):
    stream.write(message + "\n")
    stream.flush()


def main(argv=None):
    from experiments.candidates.degraded_incumbent_shadow_handover.forecast_package_b02 import (
        renewal_boundary_a02 as a02,
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--checkpoint-sha256", default=a02.EXPECTED_CHECKPOINT_SHA256)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--profile", choices=("formal", "check"), required=True)
    args = parser.parse_args(argv)
    started = time.perf_counter()
    args.out.mkdir(parents=True, exist_ok=True)
    log_path = args.out / "run.log"
    summary = {
        "object": a02.OBJECT, "status": "INCOMPLETE", "profile": args.profile,
        "launch_sha": args.launch_sha, "checkpoint": str(args.checkpoint.resolve()),
        "expected_checkpoint_sha256": args.checkpoint_sha256,
        "planned_cost": a02.planned_cost(args.profile),
        "exposure": {
            "new_models_trained": 0, "training_transitions": 0, "optimizer_steps": 0,
            "consultation_exposure": 0,
        },
        "projection_source": "python reconstruction of rbhr_r06_production_backend.cpp:261-263; native ABI not called",
    }
    with log_path.open("w", encoding="utf-8") as log:
        try:
            digest, payload = a02.verify_checkpoint(args.checkpoint, args.checkpoint_sha256)
            summary["checkpoint_sha256"] = digest
            summary["checkpoint_bytes"] = len(payload)
            _log(log, f"checkpoint digest {digest} bytes {len(payload)}")
            import torch
            torch.set_num_threads(1)
            summary["configuration"] = {
                "host": a02.HOST, "forecast_package": True, "arm": "STRUCTURED",
                "torch_threads": torch.get_num_threads(), "training_dtype": "float32",
                "native_dtype": "float64", "b02_object": a02.a01.B02_OBJECT,
                "b02_master_hex": a02.b02_master().hex(),
            }
            rows, windows = a02.run_measurement(checkpoint_bytes=payload, profile=args.profile)
            reduction = a02.reduce_rows(rows)
            overall = reduction["overall"]
            summary.update(
                status="COMPLETE", windows=windows, reduction=reduction,
                live_tick_count=len(rows),
                primary_agreement={
                    "measure": "renew_completed (native out.renew) versus policy_renew",
                    "native_out_renew_equals_policy_renew": overall[
                        "native_out_renew_equals_policy_renew"
                    ],
                    "native_out_true_policy_false": overall["native_out_true_policy_false"],
                    "policy_true_native_out_false": overall["policy_true_native_out_false"],
                },
                secondary_countdown_consistency={
                    "label": (
                        "countdown-based native_admission versus policy_renew; "
                        "same int32 field after overlay"
                    ),
                    "matched_renewals": overall["matched_renewals"],
                    "matched_non_renewals": overall["matched_non_renewals"],
                    "native_true_policy_false": overall["native_true_policy_false"],
                    "policy_true_native_false": overall["policy_true_native_false"],
                },
            )
            (args.out / "rows.json").write_text(
                json.dumps(a02.json_ready(rows), indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            _log(log, f"live ticks {len(rows)} windows {len(windows)}")
            _log(log, (
                "acceptance primary native_out_renew_equals_policy_renew "
                f"{overall['native_out_renew_equals_policy_renew']} "
                f"native_out_true_policy_false {overall['native_out_true_policy_false']} "
                f"policy_true_native_out_false {overall['policy_true_native_out_false']}"
            ))
            _log(log, (
                "acceptance secondary countdown consistency "
                f"matched_renewals {overall['matched_renewals']} "
                f"matched_non_renewals {overall['matched_non_renewals']} "
                f"native_true_policy_false {overall['native_true_policy_false']} "
                f"policy_true_native_false {overall['policy_true_native_false']}"
            ))
        except Exception as error:
            summary["exception"] = {
                "type": type(error).__name__, "message": str(error),
                "traceback": traceback.format_exc(),
            }
            _log(log, summary["exception"]["traceback"])
        try:
            rss = peak_rss_bytes()
            unmeasured = False
        except (ImportError, OSError):
            rss, unmeasured = None, True
        summary["wall_seconds"] = time.perf_counter() - started
        summary["peak_rss_bytes"] = rss
        summary["resources_unmeasured"] = unmeasured
        summary["scratch_unmeasured"] = True
        (args.out / "summary.json").write_text(
            json.dumps(a02.json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        _log(log, f"status {summary['status']} wall {summary['wall_seconds']}")
    print(json.dumps(a02.json_ready({
        "status": summary["status"], "profile": args.profile,
        "live_tick_count": summary.get("live_tick_count"),
        "wall_seconds": summary["wall_seconds"],
        "peak_rss_bytes": summary["peak_rss_bytes"],
        "primary_agreement": summary.get("primary_agreement"),
        "secondary_countdown_consistency": summary.get("secondary_countdown_consistency"),
        "out": str(args.out),
    }), sort_keys=True))
    return 0 if summary["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
