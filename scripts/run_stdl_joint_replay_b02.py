"""One admitted B02 fit: common optimistic initialization under scripted joint drift."""

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
OBJECT = "STDL_JOINT_REPLAY_B02"
ARMS = ("joint_is", "fingerprint", "recent", "uniform", "fingerprint_zero")
SEEDS = (92001, 92002, 92003)


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


def version_adaptation_endpoints(curves, config):
    """Retain the prospective A/B diagnostics without replacing the primary."""
    result = {}
    for version, name in enumerate(config.version_names):
        indices = [
            i for i, (episode, observed_version) in enumerate(
                zip(curves["evaluation_episode"], curves["version_index"])
            )
            if episode in config.primary_evaluation_episodes and observed_version == version
        ]
        values = [curves["normalized_service_return"][i] for i in indices]
        result[name] = {
            "episodes": [curves["evaluation_episode"][i] for i in indices],
            "normalized_service_returns": values,
            "mean_normalized_service_return": sum(values) / len(values) if values else None,
        }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if re.fullmatch(r"[0-9a-f]{40}", args.launch_sha) is None:
        parser.error("--launch-sha must be a full lowercase commit SHA")

    admission = require_admission(__file__, direction="skill_teammate_drift_learning")
    if args.launch_sha != admission["sha"]:
        parser.error("--launch-sha must equal the admitted source SHA")

    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[variable] = "1"

    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.joint_replay_b01.study import (
        Config,
        run_fit,
    )

    replay_arm = "fingerprint" if args.arm == "fingerprint_zero" else args.arm
    initialization = "zero" if args.arm == "fingerprint_zero" else "reward_upper"
    cfg = Config(initialization=initialization)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("config.json", "summary.json", "curves.json", "transitions.npz", "q_values.npy"):
        if (args.out / name).exists():
            raise FileExistsError(f"Scientific artifact already exists: {args.out / name}")
    identity = {
        "object": OBJECT,
        "direction": DIRECTION,
        "arm": args.arm,
        "replay_arm": replay_arm,
        "initialization": initialization,
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
        "scientific_scope": "exploratory common-initialization repair; scripted two-agent line host",
    }
    write_json(args.out / "config.json", config_record)
    write_json(args.out / "summary.json", summary)
    try:
        summary["started_fits"] = 1
        write_json(args.out / "summary.json", summary)
        result = run_fit(cfg, arm=replay_arm, seed=args.seed, object_name=OBJECT)
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
        summary["version_adaptation_endpoints"] = version_adaptation_endpoints(result["curves"], cfg)
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
