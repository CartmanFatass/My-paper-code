"""One admitted B04 source-support intervention fit; all other B03 semantics held."""

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
from scripts.run_stdl_joint_response_b03 import write_arrays


DIRECTION = "skill_teammate_drift_learning"
OBJECT = "STDL_JOINT_RESPONSE_B04"
ARM_CONFIG = {
    "joint_product": ("joint_response", "product"),
    "fingerprint_product": ("fingerprint_full", "product"),
    "joint_permuted": ("joint_response", "permuted"),
    "fingerprint_permuted": ("fingerprint_full", "permuted"),
}
SEEDS = (94001, 94002, 94003)
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


def support_diagnostics(result, config, np):
    """One descriptive source design SVD, with no fit or action modification."""
    transitions = result["transitions"]
    source = slice(0, config.source_macros)
    selected = transitions["collection_skill"][source] == 1
    u = transitions["u"][source][selected]
    v = transitions["v"][source][selected]
    design = np.column_stack(((1-u)*(1-v), (1-u)*v, u*(1-v), u*v))
    singular_values = np.linalg.svd(design, compute_uv=False)
    leading = float(singular_values[0]) if singular_values.size else 0.0
    tolerance = leading * max(design.shape) * np.finfo(np.float64).eps
    first = config.source_macros
    return {
        "cooperative_source_rows": int(design.shape[0]),
        "saturated_source_singular_values": singular_values.tolist(),
        "saturated_source_rank": int(np.sum(singular_values > tolerance)),
        "rank_tolerance": tolerance,
        "source_product_min": float(np.min(transitions["u"][source] * transitions["v"][source])),
        "source_product_max": float(np.max(transitions["u"][source] * transitions["v"][source])),
        "first_target_raw_predictions": result["curves"]["raw_predictions"][first],
        "first_target_true_values": result["curves"]["true_values"][first],
        "first_target_greedy_action": result["curves"]["greedy_action"][first],
        "first_target_value_mae": result["curves"]["value_mae"][first],
        "source_design_svd_calls": 1,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", choices=tuple(ARM_CONFIG), required=True)
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

    from experiments.candidates.skill_teammate_drift_learning.joint_response_b03.study import (
        Config,
        run_fit,
    )

    learner_arm, schedule = ARM_CONFIG[args.arm]
    cfg = Config(source_schedule=schedule)
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACTS:
        if (args.out / name).exists():
            raise FileExistsError(f"Scientific artifact already exists: {args.out / name}")
    identity = {
        "object": OBJECT, "direction": DIRECTION, "arm": args.arm,
        "learner_arm": learner_arm, "source_schedule": schedule,
        "seed": args.seed, "launch_sha": args.launch_sha,
    }
    config_record = {
        **identity,
        "config": asdict(cfg), "python": sys.version, "numpy": np.__version__,
        "numeric_thread_environment": {
            name: os.environ[name]
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }
    summary = {
        **identity, "status": "running", "started_fits": 0,
        "scientific_scope": "exploratory paired source-support intervention; known scripted controller law",
    }
    write_json(args.out / "config.json", config_record)
    write_json(args.out / "summary.json", summary)
    try:
        summary["started_fits"] = 1
        write_json(args.out / "summary.json", summary)
        result = run_fit(cfg, arm=learner_arm, seed=args.seed, object_name=OBJECT)
        summary["source_design"] = support_diagnostics(result, cfg, np)
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
