"""Runner for SCDMP-D6-CROSS-K-Q-SHARING-B01.

Scientific order is a plain list: gate, three data commands, six D6/D8 arm
commands, then summarize.  Smoke is technical-only and creates no result state.
"""

from __future__ import annotations

import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.candidates.scdmp_variable_k.d6_cross_k_q_sharing_b01 import decide_branch, study
from experiments.candidates.scdmp_variable_k.d6_cross_k_q_sharing_b01.native import Host


OBJECT_ID = "SCDMP-D6-CROSS-K-Q-SHARING-B01"
CAP_SECONDS = 1800.0


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _launch_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
    ).strip()


def _peak_rss() -> int | None:
    if sys.platform == "win32":
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
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        try:
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.PeakWorkingSetSize)
        except OSError:
            pass
        return None
    try:
        import resource
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(value if sys.platform == "darwin" else value * 1024)
    except (ImportError, OSError):
        return None


def _admit(receipt: Path) -> dict[str, object]:
    completed = subprocess.run([
        sys.executable, str(ROOT / "scripts" / "hmasd_resource_preflight.py"),
        "admit-memory", "--out", str(receipt),
    ])
    value = _read(receipt)
    if completed.returncode != 0 or value.get("passed") is not True:
        raise SystemExit("mandatory 4 GiB physical/effective admission failed")
    return value


def _scientific_metadata(
    command: str, seed: int, admission: dict[str, object], started: float, launch_sha: str,
) -> dict[str, object]:
    peak_rss = _peak_rss()
    return {
        "object_id": OBJECT_ID, "command": command, "fixed_seed": seed,
        "launch_sha": launch_sha, "admission": admission,
        "wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak_rss,
        "resources_unmeasured": peak_rss is None,
    }


def _run_scientific(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    admission = _admit(args.receipt)
    launch_sha = _launch_sha()
    output = args.output_root.resolve(strict=False)
    output.mkdir(parents=True, exist_ok=True)
    timing = {"_deadline": started + CAP_SECONDS}
    with Host(output / "native-build") as host:
        if args.command == "gate":
            if args.seed != 9029:
                raise SystemExit("gate fixed seed must be evaluation domain 9029")
            result = study.run_gate(host, timing=timing)
            result["integrity_valid"] = (
                result["native_missions"] == 1152 and result["native_transitions"] > 0
                and result["source_transitions"] > 0 and admission.get("passed") is True
            )
            if result["host_pass"] is not True:
                result["branch"] = decide_branch({
                    "integrity_valid": result["integrity_valid"], "host_pass": False,
                })
        elif args.command == "data":
            if args.seed not in study.LEARNER_SEEDS:
                raise SystemExit(f"data seed must be one of {study.LEARNER_SEEDS}")
            gate = _read(args.gate)
            if gate.get("host_pass") is not True:
                raise SystemExit("host gate did not pass; dataset creation is not allowed")
            result = study.generate_dataset(host, gate, args.seed, timing=timing)
        else:
            if args.seed not in study.LEARNER_SEEDS:
                raise SystemExit(f"arm seed must be one of {study.LEARNER_SEEDS}")
            gate, dataset = _read(args.gate), _read(args.dataset)
            if gate.get("host_pass") is not True:
                raise SystemExit("host gate did not pass; learner creation is not allowed")
            if int(dataset["learner_seed"]) != args.seed:
                raise SystemExit("dataset seed differs from fixed arm seed")
            result = study.train_arm(host, gate, dataset, args.arm, timing=timing)
            result["data_admission"] = dataset["admission"]
    result.update(_scientific_metadata(args.command, args.seed, admission, started, launch_sha))
    if float(result["wall_seconds"]) > CAP_SECONDS:
        raise SystemExit("1,800 second invocation cap exceeded without scientific polarity")
    _write(output / "summary.json", result)
    return 0


def _summarize(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    launch_sha = _launch_sha()
    gate = _read(args.gate)
    arms = [_read(path) for path in args.arm_results]
    result = study.summarize(gate, arms)
    peak_rss = _peak_rss()
    result.update({
        "object_id": OBJECT_ID, "command": "summarize", "fixed_seed": args.seed,
        "launch_sha": launch_sha, "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": peak_rss, "resources_unmeasured": peak_rss is None,
    })
    _write(args.output_root.resolve(strict=False) / "summary.json", result)
    return 0


def _smoke(args: argparse.Namespace) -> int:
    started = time.perf_counter()
    output = args.output_root.resolve(strict=False)
    output.mkdir(parents=True, exist_ok=True)
    timing: dict[str, float] = {}
    with Host(output / "native-build") as host:
        gate = study.run_gate(host, tapes=1, targets=(7, 14, 27), timing=timing)
        data = study.generate_dataset(host, gate, 3119, updates=1, timing=timing)
        arms = [
            study.train_arm(host, gate, data, arm, checkpoints=(0, 1), tapes=1, timing=timing)
            for arm in ("D6", "D8")
        ]
    native_count = gate["native_missions"] + data["native_missions"] + sum(
        row["native_evaluation_missions"] for row in arms
    )
    adamw_count = sum(row["learner_steps"] for row in arms)
    score_count = sum(row["candidate_scores"] for row in arms)
    peak_rss = _peak_rss()
    technical = {
        "mode": "smoke", "scientific_result_state_created": False,
        "counts": {
            "native_missions": native_count, "adamw_steps": adamw_count,
            "candidate_scores": score_count,
        },
        "unit_seconds": {
            "native_mission": timing["native_seconds"] / native_count,
            "adamw_step": timing["adamw_seconds"] / adamw_count,
            "candidate_score": timing["candidate_score_seconds"] / score_count,
        },
        "wall_seconds": time.perf_counter() - started, "peak_rss_bytes": peak_rss,
        "resources_unmeasured": peak_rss is None,
    }
    _write(output / "technical-timing-counts.json", technical)
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--seed", type=int, required=True, help="fixed scientific seed/domain")
    commands = result.add_subparsers(dest="command", required=True)
    for name in ("gate", "data", "arm"):
        item = commands.add_parser(name)
        item.add_argument("--output-root", type=Path, required=True)
        item.add_argument("--receipt", type=Path, required=True)
        if name in ("data", "arm"):
            item.add_argument("--gate", type=Path, required=True)
        if name == "arm":
            item.add_argument("--dataset", type=Path, required=True)
            item.add_argument("--arm", choices=("D6", "D8"), required=True)
    summary = commands.add_parser("summarize")
    summary.add_argument("--gate", type=Path, required=True)
    summary.add_argument("--arm-results", type=Path, nargs=6, required=True)
    summary.add_argument("--output-root", type=Path, required=True)
    smoke = commands.add_parser("smoke")
    smoke.add_argument("--output-root", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "smoke":
        return _smoke(args)
    if args.command == "summarize":
        return _summarize(args)
    return _run_scientific(args)


if __name__ == "__main__":
    raise SystemExit(main())
