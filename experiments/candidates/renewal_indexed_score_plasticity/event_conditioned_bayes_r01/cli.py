"""Strict result-blind CLI separation for RISP-ECR-R01."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import sys
import threading
import time
from typing import Sequence

from .artifact import ArtifactError, atomic_write_once
from .contract import (
    MAX_RSS_BYTES,
    MAX_WALL_SECONDS,
    ContractError,
    canonical_json_bytes,
    description,
    load_registered_spec,
    structural_check,
)


class CLIError(RuntimeError):
    """The requested CLI transaction failed closed."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m experiments.candidates.renewal_indexed_score_plasticity.event_conditioned_bayes_r01"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("describe", help="print the frozen pre-result contract")
    check = subparsers.add_parser("check", help="validate exact spec structure only")
    check.add_argument("--spec", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    certify = subparsers.add_parser("certify", help="run the sole registered result transaction")
    certify.add_argument("--spec", type=Path, required=True)
    certify.add_argument("--output-root", type=Path, required=True)
    return parser


def _peak_rss_bytes() -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.argtypes = []
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(Counters),
            ctypes.c_ulong,
        ]
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        handle = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            raise CLIError("unable to observe process RSS")
        return int(counters.PeakWorkingSetSize)
    import resource

    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _run_certification(spec_path: Path, output_root: Path) -> Path:
    """Execute exactly one registered census after all structural gates pass."""

    # These checks intentionally precede imports of controller/action logic.
    spec = load_registered_spec(spec_path)
    if output_root.exists():
        raise CLIError(f"refusing existing output root: {output_root}")
    if threading.active_count() != 1:
        raise CLIError("registered certification requires one active CPU thread")

    from .analysis import analyze_complete_census
    from .artifact import publish_complete_result
    from .controllers import evaluate_registered_census

    start = time.perf_counter()
    rss_before = _peak_rss_bytes()
    census = evaluate_registered_census(spec)
    elapsed = time.perf_counter() - start
    rss_after = _peak_rss_bytes()
    resource_observation = {
        "cpu_threads_start": 1,
        "cpu_threads_end": threading.active_count(),
        "gpu_used": False,
        "network_used": False,
        "scientific_rng_draws": 0,
        "wall_seconds": elapsed,
        "peak_rss_bytes_before": rss_before,
        "peak_rss_bytes_after": rss_after,
        "wall_seconds_upper": MAX_WALL_SECONDS,
        "rss_bytes_upper": MAX_RSS_BYTES,
    }
    result = analyze_complete_census(
        census,
        binding_class="REGISTERED",
        resource_observation=resource_observation,
    )
    return publish_complete_result(output_root, result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "describe":
            sys.stdout.buffer.write(canonical_json_bytes(description()) + b"\n")
            return 0
        if arguments.command == "check":
            spec = load_registered_spec(arguments.spec)
            atomic_write_once(arguments.output, structural_check(spec))
            return 0
        if arguments.command == "certify":
            result = _run_certification(arguments.spec, arguments.output_root)
            sys.stdout.write(json.dumps({"complete_result": str(result)}, sort_keys=True) + "\n")
            return 0
        raise CLIError("unknown command")
    except (ArtifactError, ContractError, CLIError, OSError, ValueError, RuntimeError) as error:
        sys.stderr.write(f"RISP-ECR-R01 {arguments.command} failed: {error}\n")
        return 2


__all__ = ["CLIError", "build_parser", "main"]
