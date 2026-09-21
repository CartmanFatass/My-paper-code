"""Native B09 joint-frequency versus marginal-projection experiment."""

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


for _variable in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
):
    os.environ[_variable] = "1"

START_WALL = time.monotonic()
START_CPU = time.process_time()
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.hmasd_admission import require_admission


OBJECT = "skill_drift_native_joint_b09"
STAGE = "prospective_diagnostic"
SEEDS = (95401, 95402, 95403)
PLAN_SOURCE = "ee2d70c69abc0c5a45881da6e74937a7ac166689"
OUTPUT_SUFFIX = Path("runs/skill_teammate_drift_learning/b09_native_joint")
OUTPUT_ROOT = ROOT / OUTPUT_SUFFIX


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    encoded = json_bytes(value)
    canonical = json.loads(encoded)
    temporary.write_bytes(encoded)
    temporary.replace(path)
    if json.loads(path.read_bytes()) != canonical:
        raise IOError(f"JSON readback mismatch: {path}")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def has_fixed_output_suffix(path):
    actual = Path(path).resolve().parts
    suffix = OUTPUT_SUFFIX.parts
    return len(actual) >= len(suffix) and actual[-len(suffix) :] == suffix


def prepare_output_directory(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise NotADirectoryError(path)
    protected = ("summary.json", "source-manifest.json", "artifacts.json")
    present = [name for name in protected if (path / name).exists()]
    present.extend(child.name for child in path.glob("seed_*") if child.exists())
    if present:
        raise FileExistsError(
            f"refusing existing B09 scientific output: {sorted(present)}"
        )
    return path


def stable_science_digests(path):
    path = Path(path).resolve()
    stable = [path / "summary.json", path / "source-manifest.json"]
    stable.extend(
        candidate
        for block in sorted(path.glob("seed_*"))
        for candidate in sorted(block.rglob("*"))
        if candidate.is_file()
    )
    missing = [candidate.name for candidate in stable[:2] if not candidate.is_file()]
    if missing:
        raise FileNotFoundError(f"missing stable B09 science files: {missing}")
    return {
        candidate.relative_to(path).as_posix(): sha256(candidate)
        for candidate in stable
    }


def resource_fields():
    result = {
        "runner_wall_seconds": time.monotonic() - START_WALL,
        "runner_cpu_seconds": time.process_time() - START_CPU,
        "cpu_scope": "single sequential native process, user plus system",
    }
    try:
        import resource

        result["peak_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        result["rss_scope"] = "single process high-water mark on local_linux"
    except ImportError:
        result["peak_rss_kib"] = None
        result["resources_unmeasured"] = ["peak_rss"]
    return result


def _require_plan_source():
    subprocess.run(
        ["git", "cat-file", "-e", f"{PLAN_SOURCE}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", PLAN_SOURCE, "HEAD"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def source_manifest():
    paths = {
        "study": ROOT / "experiments/candidates/skill_teammate_drift_learning/native_joint_b09/study.py",
        "runner": Path(__file__).resolve(),
        "scenario1": ROOT / "envs/pettingzoo/scenario1.py",
        "native_environment": ROOT / "envs/pettingzoo/uav_env.py",
        "array_adapter": ROOT / "envs/pettingzoo/env_adapter.py",
    }
    return {
        "plan_source": PLAN_SOURCE,
        "files": {
            name: {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for name, path in paths.items()
        },
    }


def validate_source_manifest(manifest):
    if manifest.get("plan_source") != PLAN_SOURCE:
        raise ValueError("B09 plan source identity mismatch")
    for record in manifest.get("files", {}).values():
        path = ROOT / record["path"]
        if sha256(path) != record["sha256"]:
            raise ValueError(f"B09 source digest mismatch: {record['path']}")
    if len(manifest.get("files", {})) != 5:
        raise ValueError("B09 source manifest file set mismatch")
    return True


def begin_fit(metadata, seed):
    attempt = {
        "seed": int(seed),
        "status": "RUNNING",
        "partial_exposure": {},
        "partial_exposure_scope": "completed native calls in this process; an interrupted call is not reported as zero",
        "exposure_complete": False,
        "unfinished_work_not_counted_as_zero": True,
    }
    metadata["fit_attempts"].append(attempt)
    metadata["started_fits"] += 1
    return attempt


def complete_fit(metadata, attempt, result):
    if attempt["status"] != "RUNNING":
        raise RuntimeError("fit attempt was not running")
    attempt.update(
        status="COMPLETE",
        saved=False,
        partial_exposure=result["actual_exposure"],
        counts=result["summary"]["counts"],
        compute_wall_seconds=result["summary"]["compute_wall_seconds"],
        exposure_complete=True,
        unfinished_work_not_counted_as_zero=False,
    )
    metadata["completed_fits"] += 1


def save_block(out, seed, result, launch_sha):
    import numpy as np

    block = Path(out) / f"seed_{seed}"
    block.mkdir(exist_ok=False)
    np.savez_compressed(block / "training.npz", **result["training"])
    np.savez_compressed(block / "evaluation.npz", **result["evaluation"])
    np.savez_compressed(block / "state.npz", **result["state"])
    summary = dict(result["summary"])
    summary.update(
        object=OBJECT,
        stage=STAGE,
        launch_sha=launch_sha,
        plan_source=PLAN_SOURCE,
    )
    write_json(block / "summary.json", summary)
    digests = {
        path.relative_to(block).as_posix(): sha256(path)
        for path in sorted(block.rglob("*"))
        if path.is_file()
    }
    write_json(block / "artifacts.json", digests)
    return summary


def aggregate(blocks):
    if [block["seed"] for block in blocks] != list(SEEDS):
        raise ValueError("B09 aggregation requires the three fixed blocks in order")
    paired_seed_values = []
    episode_values = []
    for block in blocks:
        primary_key = str(block["config"]["snapshot_steps"][-1])
        primary = block["reductions"]["by_snapshot"][primary_key]
        paired_seed_values.append(primary["mean_J_minus_M_adapter_return"])
        episode_values.append(primary["paired_J_minus_M_adapter_returns"])
    return {
        "primary": "mean-over-four-episodes J_emp minus M_proj cumulative 64-tick adapter return at target observation 64",
        "paired_seed_values": paired_seed_values,
        "paired_episode_values_by_seed": episode_values,
        "three_block_mean": sum(paired_seed_values) / len(paired_seed_values),
        "early_snapshot_role": "descriptive",
        "no_threshold_or_selection": True,
        "independent_units": "three training histories",
    }


def aggregate_completed_exposure(attempts):
    completed = [attempt for attempt in attempts if attempt["status"] == "COMPLETE"]
    if len(completed) != len(SEEDS) or any(not attempt["exposure_complete"] for attempt in completed):
        raise ValueError("B09 exposure aggregation requires three complete fits")
    keys = set(completed[0]["partial_exposure"])
    if any(set(attempt["partial_exposure"]) != keys for attempt in completed):
        raise ValueError("B09 completed exposure schemas differ")
    return {
        key: sum(int(attempt["partial_exposure"][key]) for attempt in completed)
        for key in sorted(keys)
    }


def run_stage(args, admission):
    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.native_joint_b09.study import (
        Config,
        EXPOSURE_KEYS,
        run_block,
    )

    args.out = prepare_output_directory(args.out)
    metadata = {
        "object": OBJECT,
        "stage": STAGE,
        "status": "RUNNING",
        "launch_sha": args.launch_sha,
        "admission": admission,
        "plan_source": PLAN_SOURCE,
        "output_root": str(args.out),
        "seeds": list(args.seeds),
        "config": asdict(Config()),
        "started_fits": 0,
        "completed_fits": 0,
        "fit_attempts": [],
        "completed_blocks": [],
        "numpy_version": np.__version__,
        "dtype": "float64 physics/count evidence plus float32 native commands/observations",
        "numeric_threads": 1,
        "information_contract": "external B-owned mixture probabilities are not exposed to the focal learner",
        "no_standard_hmasd_claim": True,
    }
    write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    try:
        _require_plan_source()
        manifest = source_manifest()
        validate_source_manifest(manifest)
        write_json(args.out / "source-manifest.json", manifest)
        for seed in args.seeds:
            metadata["current_seed"] = int(seed)
            attempt = begin_fit(metadata, seed)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            exposure = {key: 0 for key in EXPOSURE_KEYS}
            attempt["partial_exposure"] = exposure
            result = run_block(Config(), int(seed), exposure=exposure)
            complete_fit(metadata, attempt, result)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            block_summary = save_block(args.out, seed, result, args.launch_sha)
            attempt["saved"] = True
            metadata["completed_blocks"].append(block_summary)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_complete", "seed": seed}), flush=True)

        observed = aggregate_completed_exposure(metadata["fit_attempts"])
        expected_observed = {
            "custom_geometry_channel_refreshes": 54,
            "deep_copies": 24576,
            "evaluation_native_step_calls": 3072,
            "implicit_constructor_resets": 54,
            "logical_episode_initializations": 54,
            "native_constructors": 54,
            "planner_native_step_calls": 24576,
            "training_native_step_calls": 384,
        }
        if observed != expected_observed:
            raise RuntimeError(
                f"completed B09 exposure disagrees with declaration: {observed}"
            )
        trace_totals = {
            key: sum(int(block["counts"][key]) for block in metadata["completed_blocks"])
            for key in metadata["completed_blocks"][0]["counts"]
        }
        metadata.update(
            status="COMPLETE",
            reduction=aggregate(metadata["completed_blocks"]),
            observed_exposure=observed,
            trace_derived_totals=trace_totals,
        )
        metadata.pop("current_seed", None)
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
        write_json(args.out / "artifacts.json", stable_science_digests(args.out))
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
        parser.error("seeds/order must equal the prospective B09 declaration")
    if not has_fixed_output_suffix(args.out):
        parser.error("out must end with the fixed B09 output suffix")
    args.out = args.out.resolve()
    admission = require_admission(
        __file__, direction="skill_teammate_drift_learning"
    )
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")
    run_stage(args, admission)


if __name__ == "__main__":
    main()
