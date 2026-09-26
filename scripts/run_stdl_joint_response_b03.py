"""One admitted B03 joint-outcome conditioning fit on nonrepeating contexts."""

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
from scripts.run_stdl_joint_replay_b01 import write_json


DIRECTION = "skill_teammate_drift_learning"
OBJECT = "STDL_JOINT_RESPONSE_B03"
ARMS = (
    "joint_response", "fingerprint_full", "fingerprint_recent", "uniform",
    "recent", "additive_response",
)
SEEDS = (93001, 93002, 93003)
ARTIFACTS = (
    "config.json", "summary.json", "curves.json", "transitions.npz", "learner_state.npz",
)


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


def write_arrays(path, arrays, np):
    """Retain only finite numeric data and verify a no-pickle round trip."""
    if not isinstance(arrays, dict) or not arrays:
        raise ValueError(f"Missing scientific arrays for {path.name}")
    converted = {}
    for key, array in arrays.items():
        values = np.asarray(array)
        if values.dtype.kind not in "buif" or not np.isfinite(values).all():
            raise ValueError(f"Nonfinite or nonnumeric scientific array: {key}")
        converted[key] = values
    np.savez_compressed(path, **converted)
    with np.load(path, allow_pickle=False) as retained:
        if set(retained.files) != set(converted):
            raise IOError(f"Array publication keys differ: {path}")
        for key, array in converted.items():
            if not np.array_equal(retained[key], array):
                raise IOError(f"Array publication mismatch: {path.name}/{key}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if re.fullmatch(r"[0-9a-f]{40}", args.launch_sha) is None:
        parser.error("--launch-sha must be a full lowercase commit SHA")

    # No scientific import, learner, evaluator or output exists before this guard.
    admission = require_admission(__file__, direction="skill_teammate_drift_learning")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"

    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.joint_response_b03.study import (
        Config,
        run_fit,
    )

    cfg = Config()
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACTS:
        if (args.out / name).exists():
            raise FileExistsError(f"Scientific artifact already exists: {args.out / name}")
    identity = {
        "object": OBJECT,
        "direction": DIRECTION,
        "arm": args.arm,
        "seed": args.seed,
        "launch_sha": args.launch_sha,
    }
    config_record = {
        **identity,
        "config": asdict(cfg),
        "python": sys.version,
        "numpy": np.__version__,
        "numeric_thread_environment": {
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }
    summary = {
        **identity,
        "status": "running",
        "started_fits": 0,
        "scientific_scope": (
            "exploratory constructed joint-response existence test; "
            "known scripted controller law and stationary outcome-conditioned reward"
        ),
    }
    write_json(args.out / "config.json", config_record)
    write_json(args.out / "summary.json", summary)
    try:
        summary["started_fits"] = 1
        write_json(args.out / "summary.json", summary)
        result = run_fit(cfg, arm=args.arm, seed=args.seed, object_name=OBJECT)
        write_arrays(args.out / "transitions.npz", result["transitions"], np)
        write_arrays(args.out / "learner_state.npz", result["learner_state"], np)
        write_json(args.out / "curves.json", result["curves"])
        summary["learning"] = result["summary"]
        summary["artifacts"] = list(ARTIFACTS)
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
