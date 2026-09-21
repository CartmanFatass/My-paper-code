"""Provisional B07 own-collection exploration over the frozen B05 engine."""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time


START_WALL = time.monotonic()
START_CPU = time.process_time()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


OBJECT = "skill_drift_collection_b07"
STAGE = "exploration"
SEEDS = (95301, 95302, 95303)
BRANCH_IDS = ("R_U", "F_U", "R_E", "F_E")
EPSILON = 0.20
SOURCE_MACROS = 2048
TARGET_MACROS = 256
CONTEXTS = 4
SKILL_TICKS = 3
RESPONSE_SETTING = "response_all__response__prior2"
FULL_SETTING = "fingerprint_full__hybrid__prior2"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)
    if json.loads(path.read_bytes()) != value:
        raise IOError(f"JSON readback mismatch: {path}")


def resource_fields():
    result = {
        "runner_wall_seconds": time.monotonic() - START_WALL,
        "runner_cpu_seconds": time.process_time() - START_CPU,
        "cpu_scope": "single sequential scientific process, user plus system",
    }
    try:
        import resource

        result["peak_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result["rss_scope"] = "single process high-water mark on local_linux"
    except ImportError:
        result["peak_rss_kib"] = None
        result["resources_unmeasured"] = ["peak_rss"]
    return result


def aggregate_reductions(block_rows):
    """Descriptively aggregate fixed block reductions without an inference rule."""
    actual = [int(row["seed"]) for row in block_rows]
    if len(actual) != len(set(actual)) or set(actual) != set(SEEDS):
        raise ValueError("block reductions must cover the three fixed seeds exactly")
    by_seed = {int(row["seed"]): row["reductions"] for row in block_rows}
    keys = (
        "primary_executed_e_response_minus_full",
        "matched_e_response_minus_full",
        "matched_u_response_minus_full",
        "matched_feedback_interaction",
        "uniform_actual_response_minus_full",
        "sampled_e_response_minus_full",
    )
    endpoints = {}
    for endpoint in ("first64", "full", "late64"):
        endpoints[endpoint] = {}
        for key in keys:
            values = [
                float(by_seed[seed]["by_endpoint"][endpoint][key]) for seed in SEEDS
            ]
            if not all(value == value and abs(value) != float("inf") for value in values):
                raise ValueError("block reduction contains a non-finite value")
            endpoints[endpoint][key] = {
                "paired_values": values,
                "mean": sum(values) / len(values),
                "role": (
                    "primary_exploratory"
                    if endpoint == "full"
                    and key == "primary_executed_e_response_minus_full"
                    else "descriptive"
                ),
            }
    return {
        "primary_endpoint": "full",
        "by_endpoint": endpoints,
        "no_confirmation_threshold": True,
        "interaction_uses_matched_epsilon_in_both_regimes": True,
    }


def save_block(out, result, seed, launch_sha):
    import numpy as np

    block_root = Path(out) / f"seed_{seed}"
    block_root.mkdir(exist_ok=False)
    np.savez_compressed(block_root / "common.npz", **result["common"])
    block_summary = dict(result["summary"])
    block_summary.update(
        object=OBJECT,
        stage=STAGE,
        seed=int(seed),
        launch_sha=launch_sha,
        source_identity=launch_sha,
    )
    write_json(block_root / "summary.json", block_summary)
    for branch, payload in result["branches"].items():
        branch_root = block_root / branch
        branch_root.mkdir()
        np.savez_compressed(branch_root / "trajectory.npz", **payload["trajectory"])
        np.savez_compressed(branch_root / "state.npz", **payload["state"])
        branch_summary = dict(payload["summary"])
        branch_summary.update(
            object=OBJECT,
            stage=STAGE,
            seed=int(seed),
            launch_sha=launch_sha,
            source_identity=launch_sha,
        )
        write_json(branch_root / "summary.json", branch_summary)
    digests = {}
    for path in sorted(block_root.rglob("*")):
        if path.is_file():
            digests[path.relative_to(block_root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    write_json(block_root / "artifacts.json", digests)
    return block_summary


def run_stage(args, admission):
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        os.environ[variable] = "1"
    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.collection_b07.study import (
        BRANCHES,
        Config,
        run_block,
    )

    config = Config()
    if asdict(config) != {
        "source_macros": SOURCE_MACROS,
        "target_macros": TARGET_MACROS,
        "contexts": CONTEXTS,
        "skill_ticks": SKILL_TICKS,
        "epsilon": EPSILON,
    }:
        raise RuntimeError("runner constants disagree with the frozen B07 config")
    actual_branches = {
        branch.id: (branch.collector, branch.spec.id) for branch in BRANCHES
    }
    expected_branches = {
        "R_U": ("uniform", RESPONSE_SETTING),
        "F_U": ("uniform", FULL_SETTING),
        "R_E": ("epsilon_greedy", RESPONSE_SETTING),
        "F_E": ("epsilon_greedy", FULL_SETTING),
    }
    if tuple(branch.id for branch in BRANCHES) != BRANCH_IDS or actual_branches != expected_branches:
        raise RuntimeError("runner branch identities disagree with the frozen B07 study")

    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "summary.json").exists():
        raise FileExistsError("refusing to overwrite an existing scientific summary")
    metadata = {
        "object": OBJECT,
        "stage": STAGE,
        "status": "RUNNING",
        "launch_sha": args.launch_sha,
        "source_identity": args.launch_sha,
        "seeds": list(args.seeds),
        "config": asdict(config),
        "branches": list(BRANCH_IDS),
        "settings": {
            "response": RESPONSE_SETTING,
            "full": FULL_SETTING,
        },
        "numpy_version": np.__version__,
        "dtype": "float64",
        "blas_threads": 1,
        "planned_decision_fits": 12,
        "planned_law_fits": 12,
        "started_decision_fits": 0,
        "started_law_fits": 0,
        "completed_decision_fits": 0,
        "completed_law_fits": 0,
        "completed_blocks": [],
        "block_reductions": [],
        "gradient_optimizer_calls": 0,
        "scope": (
            "four own-history branches on the exogenous correlated B05 terminal host"
        ),
        "source_execution": "duplicated independently in every branch",
        "policy_readouts_per_q_truth_panel": [
            "greedy",
            "matched_epsilon",
            "actual_collector",
        ],
    }
    write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    try:
        for seed in args.seeds:
            metadata["started_decision_fits"] += 4
            metadata["started_law_fits"] += 4
            metadata["current_seed"] = int(seed)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(
                json.dumps(
                    {"event": "block_started", "seed": seed, "branches": BRANCH_IDS}
                ),
                flush=True,
            )
            started = time.monotonic()
            result = run_block(config, seed=int(seed))
            result["summary"]["scientific_block_wall_seconds"] = (
                time.monotonic() - started
            )
            result["summary"]["scientific_block_wall_scope"] = (
                "four actual branch trajectories, learning, and exact readouts; "
                "excludes serialization and import"
            )
            if set(result["branches"]) != set(BRANCH_IDS):
                raise ValueError("scientific block omitted or added a B07 branch")
            block_summary = save_block(args.out, result, seed, args.launch_sha)
            metadata["completed_blocks"].append(block_summary)
            metadata["block_reductions"].append(
                {"seed": int(seed), "reductions": result["summary"]["reductions"]}
            )
            metadata["completed_decision_fits"] += 4
            metadata["completed_law_fits"] += 4
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_complete", "seed": seed}), flush=True)

        metadata.update(
            status="COMPLETE",
            reduction=aggregate_reductions(metadata["block_reductions"]),
            unique_block_laws=3,
            actual_collected_macros=27648,
            duplicated_source_macros=24576,
            actual_primitive_ticks=82944,
            sampled_reward_labels=27648,
            q_truth_panels=27648,
            scalar_policy_values=82944,
            evaluation_environment_ticks=0,
            evaluation_reward_draws=0,
        )
        metadata.pop("current_seed", None)
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    except BaseException as error:
        metadata.update(
            status="TECHNICAL_FAILURE",
            error_type=type(error).__name__,
            error=str(error),
        )
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if tuple(args.seeds) != SEEDS:
        parser.error("seeds/order must equal the prospective B07 declaration")
    admission = require_admission(
        __file__, direction="skill_teammate_drift_learning"
    )
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")
    run_stage(args, admission)


if __name__ == "__main__":
    main()
