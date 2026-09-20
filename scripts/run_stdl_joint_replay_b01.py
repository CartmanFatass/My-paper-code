"""One admitted exploratory B01 fit under scripted skill/teammate drift."""

import time

START_WALL = time.monotonic()
START_CPU = time.process_time()

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.hmasd_admission import require_admission


DIRECTION = "skill_teammate_drift_learning"
OBJECT = "STDL_JOINT_REPLAY_B01"
ARMS = ("joint_is", "fingerprint", "recent", "uniform")
SEEDS = (91001, 91002, 91003)


def write_json(path, payload):
    """Publish a complete JSON object and verify its retained bytes are readable."""
    encoded = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)
    if json.loads(path.read_text(encoding="utf-8")) != json.loads(encoded):
        raise IOError(f"JSON publication/readback mismatch: {path}")


def add_resources(summary):
    summary["runner_wall_seconds"] = time.monotonic() - START_WALL
    summary["runner_cpu_seconds"] = time.process_time() - START_CPU
    summary["resource_scope"] = "single scientific child process; CPU user plus system"
    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF)
        summary["peak_rss_kib"] = usage.ru_maxrss
        summary["user_cpu_seconds"] = usage.ru_utime
        summary["system_cpu_seconds"] = usage.ru_stime
    except ImportError:
        summary["peak_rss_kib"] = None
        summary["resources_unmeasured"] = ["peak process RSS and split CPU times"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if re.fullmatch(r"[0-9a-f]{40}", args.launch_sha) is None:
        parser.error("--launch-sha must be a full lowercase commit SHA")

    # This must precede source imports which construct the host, output writes,
    # NumPy initialization, and every learning/evaluation effect.
    admission = require_admission(__file__, direction=DIRECTION)
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"

    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.joint_replay_b01.study import (
        Config,
        run_fit,
    )

    cfg = Config()
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("config.json", "summary.json", "curves.json", "transitions.npz", "q_values.npy"):
        if (args.out / name).exists():
            raise FileExistsError(f"Scientific artifact already exists: {args.out / name}")
    config_record = {
        "object": OBJECT,
        "direction": DIRECTION,
        "arm": args.arm,
        "seed": args.seed,
        "launch_sha": args.launch_sha,
        "config": asdict(cfg),
        "python": sys.version,
        "numpy": np.__version__,
        "numeric_thread_environment": {
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }
    summary = {
        "object": OBJECT,
        "direction": DIRECTION,
        "arm": args.arm,
        "seed": args.seed,
        "launch_sha": args.launch_sha,
        "status": "running",
        "started_fits": 0,
        "scientific_scope": "exploratory scripted joint drift; independent two-agent line host",
    }
    write_json(args.out / "config.json", config_record)
    write_json(args.out / "summary.json", summary)
    try:
        summary["started_fits"] = 1
        write_json(args.out / "summary.json", summary)
        result = run_fit(cfg, arm=args.arm, seed=args.seed)
        transitions = result["transitions"]
        if not isinstance(transitions, dict) or not transitions:
            raise ValueError("The fit must retain its macro-trajectory arrays")
        if any(np.asarray(array).dtype.hasobject for array in transitions.values()):
            raise ValueError("Trajectory arrays may not require pickle")
        np.savez_compressed(args.out / "transitions.npz", **transitions)
        np.save(args.out / "q_values.npy", result["q_values"], allow_pickle=False)
        write_json(args.out / "curves.json", result["curves"])
        with np.load(args.out / "transitions.npz", allow_pickle=False) as retained:
            if set(retained.files) != set(transitions):
                raise IOError("Trajectory publication keys differ")
            for key, array in transitions.items():
                if not np.array_equal(retained[key], array):
                    raise IOError(f"Trajectory publication mismatch: {key}")
        if not np.array_equal(
            np.load(args.out / "q_values.npy", allow_pickle=False), result["q_values"]
        ):
            raise IOError("Q-table publication mismatch")
        summary["learning"] = result["summary"]
        summary["artifacts"] = [
            "config.json", "curves.json", "transitions.npz", "q_values.npy"
        ]
        summary["status"] = "complete"
    except BaseException as exc:
        summary["status"] = "technical_failure"
        summary["error_type"] = type(exc).__name__
        summary["error"] = str(exc)
        raise
    finally:
        add_resources(summary)
        write_json(args.out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "out": str(args.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
