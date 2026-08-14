from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
import time

from .config import REGISTERED

_TORCH_CONFIGURED = False


def _configure_single_cpu() -> None:
    global _TORCH_CONFIGURED
    if _TORCH_CONFIGURED:
        return
    import torch

    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    _TORCH_CONFIGURED = True


def _rss_bytes() -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
                ("PrivateUsage", ctypes.c_size_t),
            ]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb,
        ):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
        return int(counters.PeakWorkingSetSize)
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(usage * (1024 if sys.platform != "darwin" else 1))


class RuntimeGuard:
    def __init__(self, permit, result_root: Path) -> None:
        from .artifacts import runtime_state

        self.permit = permit
        self.result_root = result_root
        self.started = time.perf_counter()
        state = runtime_state(result_root)
        self.prior_seconds = float(state["cumulative_active_seconds"])
        self.peak_rss = max(int(state["peak_rss_bytes"]), _rss_bytes())
        self.closed = False

    def check(self) -> None:
        self.permit.assert_active()
        elapsed = time.perf_counter() - self.started
        if self.prior_seconds + elapsed > REGISTERED.max_wall_minutes * 60.0:
            raise RuntimeError("frozen 45-minute cumulative active runtime ceiling exceeded")
        self.peak_rss = max(self.peak_rss, _rss_bytes())
        if self.peak_rss > REGISTERED.max_memory_mib * 1024 * 1024:
            raise MemoryError("frozen 2-GiB peak memory ceiling exceeded")

    def close(self) -> None:
        if self.closed:
            return
        from .artifacts import update_runtime

        self.peak_rss = max(self.peak_rss, _rss_bytes())
        update_runtime(self.result_root, time.perf_counter() - self.started, self.peak_rss)
        self.closed = True


def _permit(args: argparse.Namespace):
    from .artifacts import require_certificate
    from .authorization import load_production_permit

    require_certificate(args.certificate)
    return load_production_permit(args.authorization, args.result_root, args.certificate)


def _certificate(args: argparse.Namespace) -> int:
    from .certificate import write_certificate

    value = write_certificate(args.output)
    print(json.dumps({"revision": value["revision"], "passed": value["passed"], "output": str(args.output.resolve())}, sort_keys=True))
    return 0 if value["passed"] else 2


def _resources(args: argparse.Namespace) -> int:
    from .resources import resource_proposal

    value = resource_proposal()
    if args.output is None:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _init_result(args: argparse.Namespace) -> int:
    permit = _permit(args)
    from .artifacts import create_result_root

    create_result_root(args.result_root, args.certificate, str(permit.payload["stage_boundary"]))
    return 0


def _run_seed(args: argparse.Namespace) -> int:
    permit = _permit(args)
    permit.require_seed(args.seed)
    _configure_single_cpu()
    from .artifacts import require_certificate, validate_root, write_atomic_seed_packet
    from .config import ARMS, REVISION, SEEDS
    from .evaluation import evaluate_seed
    from .training import train_seed

    if args.seed not in SEEDS:
        raise ValueError("seed is outside the frozen registry")
    validate_root(args.result_root, args.certificate, str(permit.payload["stage_boundary"]))
    if (args.result_root / f"seed-{args.seed}").exists():
        raise FileExistsError(f"registered seed may not be replaced: {args.seed}")
    certificate = require_certificate(args.certificate)
    guard = RuntimeGuard(permit, args.result_root)
    try:
        guard.check()
        training = train_seed(permit, args.seed, progress_guard=guard.check)
        evaluation = evaluate_seed(permit, training, progress_guard=guard.check)
        guard.check()
        packet: dict[str, object] = {
            "revision": REVISION,
            "seed": args.seed,
            "arms": list(ARMS),
            "training": training.metadata,
            "evaluation": evaluation,
            "certificate_passed": certificate["passed"],
            "support_headroom_invariance_ok": certificate["passed"],
            "source_revision_and_hyperparameters_exact": True,
            "partial_result_interpretation_allowed": False,
            "seed_is_inferential_unit": True,
            "atomic_payload_complete": True,
        }
        guard.check()
        write_atomic_seed_packet(args.result_root, training, packet)
        return 0
    finally:
        guard.close()


def _analyze(args: argparse.Namespace) -> int:
    permit = _permit(args)
    from .artifacts import load_seed_packet, validate_root, write_analysis
    from .config import REVISION, SEEDS
    from .inference import analyze_packets

    validate_root(args.result_root, args.certificate, str(permit.payload["stage_boundary"]))
    guard = RuntimeGuard(permit, args.result_root)
    try:
        guard.check()
        packets = [load_seed_packet(args.result_root, seed) for seed in SEEDS]
        result = analyze_packets(packets)
        result["revision"] = REVISION
        result["seed_order"] = list(SEEDS)
        guard.check()
        write_analysis(args.output, result)
        return 0 if result["completeness_ok"] else 2
    finally:
        guard.close()


def _formal_run(args: argparse.Namespace) -> int:
    permit = _permit(args)
    from .artifacts import create_result_root, validate_root
    from .config import SEEDS

    if permit.payload["authorized_seeds"] != list(SEEDS):
        raise PermissionError("formal-run requires all 12 frozen seeds in exact order")
    if not args.result_root.exists():
        create_result_root(args.result_root, args.certificate, str(permit.payload["stage_boundary"]))
    else:
        validate_root(args.result_root, args.certificate, str(permit.payload["stage_boundary"]))
    for seed in SEEDS:
        if (args.result_root / f"seed-{seed}").exists():
            continue
        seed_args = argparse.Namespace(**vars(args))
        seed_args.seed = seed
        result = _run_seed(seed_args)
        if result != 0:
            return result
    analyze_args = argparse.Namespace(**vars(args))
    analyze_args.output = args.result_root / "analysis.json"
    return _analyze(analyze_args)


def _gated(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Exact RCLE B1 r04; stochastic paths fail closed")
    commands = parser.add_subparsers(dest="command", required=True)
    certificate = commands.add_parser("certificate")
    certificate.add_argument("--output", type=Path, required=True)
    certificate.set_defaults(handler=_certificate)
    resources = commands.add_parser("resource-proposal")
    resources.add_argument("--output", type=Path)
    resources.set_defaults(handler=_resources)
    initialize = commands.add_parser("init-result")
    _gated(initialize)
    initialize.set_defaults(handler=_init_result)
    seed = commands.add_parser("run-seed")
    _gated(seed)
    seed.add_argument("--seed", type=int, required=True)
    seed.set_defaults(handler=_run_seed)
    analyze = commands.add_parser("analyze")
    _gated(analyze)
    analyze.add_argument("--output", type=Path, required=True)
    analyze.set_defaults(handler=_analyze)
    formal = commands.add_parser("formal-run")
    _gated(formal)
    formal.set_defaults(handler=_formal_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, FileExistsError, MemoryError, PermissionError, RuntimeError, ValueError) as error:
        print(f"FAIL_CLOSED: {error}", file=sys.stderr)
        return 2
