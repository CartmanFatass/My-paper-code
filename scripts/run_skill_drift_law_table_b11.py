"""Native B11 whole-table by external-law crossing over sealed B09 states."""

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


OBJECT = "skill_drift_law_table_b11"
STAGE = "prospective_diagnostic"
SEEDS = (95401, 95402, 95403)
PLAN_SOURCE = "548ae30195031322d38804b3ac90bd37cb4d2b44"
B09_EVIDENCE_COMMIT = "69a55e71d9f1bca4e8cdd204adce256cd05a7676"
INPUT_SUFFIX = Path("runs/skill_teammate_drift_learning/b09_native_joint")
INPUT_ROOT = ROOT / INPUT_SUFFIX
OUTPUT_SUFFIX = Path("runs/skill_teammate_drift_learning/b11_law_table_crossing")
OUTPUT_ROOT = ROOT / OUTPUT_SUFFIX
ROOT_ARTIFACTS_SHA256 = "236734838b59a4609f71bf305c806cc205eecec97cc379c28b5483701eadbc45"
EXPECTED_B10_STUDY_SHA256 = "8d66fbc2b144bebfe2871c20cbdda51626ed4ae701b0411d48c1d4c88ab45b6f"


def json_bytes(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()


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
    parts = Path(path).resolve().parts
    suffix = OUTPUT_SUFFIX.parts
    return len(parts) >= len(suffix) and parts[-len(suffix) :] == suffix


def prepare_output_directory(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise NotADirectoryError(path)
    protected = (
        "summary.json",
        "input-manifest.json",
        "source-manifest.json",
        "artifacts.json",
    )
    present = [name for name in protected if (path / name).exists()]
    present.extend(child.name for child in path.glob("seed_*") if child.exists())
    if present:
        raise FileExistsError(
            f"refusing existing B11 scientific output: {sorted(present)}"
        )
    return path


def stable_science_digests(path):
    path = Path(path).resolve()
    stable = [
        path / "summary.json",
        path / "input-manifest.json",
        path / "source-manifest.json",
    ]
    stable.extend(
        candidate
        for block in sorted(path.glob("seed_*"))
        for candidate in sorted(block.rglob("*"))
        if candidate.is_file()
    )
    missing = [candidate.name for candidate in stable[:3] if not candidate.is_file()]
    if missing:
        raise FileNotFoundError(f"missing stable B11 science files: {missing}")
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

        result["peak_rss_kib"] = int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        )
        result["rss_scope"] = "single process high-water mark on local_linux"
    except ImportError:
        result["peak_rss_kib"] = None
        result["resources_unmeasured"] = ["peak_rss"]
    return result


def _require_sources():
    for commit in (PLAN_SOURCE, B09_EVIDENCE_COMMIT):
        subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def source_manifest():
    paths = {
        "study": ROOT
        / "experiments/candidates/skill_teammate_drift_learning/law_table_b11/study.py",
        "runner": Path(__file__).resolve(),
        "b10_study": ROOT
        / "experiments/candidates/skill_teammate_drift_learning/fixed_radial_b10/study.py",
        "b09_study": ROOT
        / "experiments/candidates/skill_teammate_drift_learning/native_joint_b09/study.py",
        "scenario1": ROOT / "envs/pettingzoo/scenario1.py",
        "native_environment": ROOT / "envs/pettingzoo/uav_env.py",
        "array_adapter": ROOT / "envs/pettingzoo/env_adapter.py",
    }
    return {
        "plan_source": PLAN_SOURCE,
        "b09_evidence_commit": B09_EVIDENCE_COMMIT,
        "files": {
            name: {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for name, path in paths.items()
        },
    }


def validate_source_manifest(manifest, b09_source_manifest):
    if (
        manifest.get("plan_source") != PLAN_SOURCE
        or manifest.get("b09_evidence_commit") != B09_EVIDENCE_COMMIT
    ):
        raise ValueError("B11 source identity mismatch")
    expected = {
        "study",
        "runner",
        "b10_study",
        "b09_study",
        "scenario1",
        "native_environment",
        "array_adapter",
    }
    if set(manifest.get("files", {})) != expected:
        raise ValueError("B11 source manifest file set mismatch")
    for record in manifest["files"].values():
        if sha256(ROOT / record["path"]) != record["sha256"]:
            raise ValueError(f"B11 source digest mismatch: {record['path']}")
    if manifest["files"]["b10_study"]["sha256"] != EXPECTED_B10_STUDY_SHA256:
        raise ValueError("B10 sealed loader/helper source changed since B11 prospective")
    links = {
        "b09_study": "study",
        "scenario1": "scenario1",
        "native_environment": "native_environment",
        "array_adapter": "array_adapter",
    }
    for current, prior in links.items():
        if (
            manifest["files"][current]["sha256"]
            != b09_source_manifest["files"][prior]["sha256"]
        ):
            raise ValueError(f"B09 helper changed since sealed evidence: {current}")
    return True


def load_all_inputs():
    from experiments.candidates.skill_teammate_drift_learning.law_table_b11.study import (
        load_frozen_state,
    )

    _require_sources()
    frozen = {
        seed: load_frozen_state(
            INPUT_ROOT,
            seed,
            expected_root_artifacts_sha256=ROOT_ARTIFACTS_SHA256,
        )
        for seed in SEEDS
    }
    source_manifest_identity = frozen[SEEDS[0]]["b09_source_manifest"]
    if any(
        item["b09_source_manifest"] != source_manifest_identity
        for item in frozen.values()
    ):
        raise ValueError("B09 blocks do not share one source manifest")
    manifest = {
        "b09_evidence_commit": B09_EVIDENCE_COMMIT,
        "plan_source": PLAN_SOURCE,
        "input_root": INPUT_SUFFIX.as_posix(),
        "root_artifacts_sha256": ROOT_ARTIFACTS_SHA256,
        "b09_launch_sha": frozen[SEEDS[0]]["b09_launch_sha"],
        "b09_plan_source": frozen[SEEDS[0]]["b09_plan_source"],
        "verified_seeds": {
            str(seed): frozen[seed]["verified_digests"] for seed in SEEDS
        },
    }
    return frozen, manifest


def begin_evaluation(metadata, seed, exposure):
    attempt = {
        "seed": int(seed),
        "status": "RUNNING",
        "partial_exposure": exposure,
        "partial_exposure_scope": "completed native calls in this process; an interrupted native call is not reported as zero",
        "exposure_complete": False,
        "unfinished_work_not_counted_as_zero": True,
        "saved": False,
    }
    metadata["evaluation_attempts"].append(attempt)
    metadata["started_evaluation_blocks"] += 1
    return attempt


def complete_evaluation(metadata, attempt, result):
    if attempt["status"] != "RUNNING":
        raise RuntimeError("B11 evaluation attempt was not running")
    attempt.update(
        status="COMPLETE",
        partial_exposure=result["actual_exposure"],
        exposure_complete=True,
        unfinished_work_not_counted_as_zero=False,
        counts=result["summary"]["counts"],
        compute_wall_seconds=result["summary"]["compute_wall_seconds"],
    )
    metadata["completed_evaluation_blocks"] += 1


def aggregate_completed_exposure(attempts):
    completed = [item for item in attempts if item["status"] == "COMPLETE"]
    if len(completed) != len(SEEDS) or any(
        not item["exposure_complete"] for item in completed
    ):
        raise ValueError("B11 exposure aggregation requires three completed blocks")
    keys = set(completed[0]["partial_exposure"])
    if any(set(item["partial_exposure"]) != keys for item in completed):
        raise ValueError("B11 exposure schemas differ")
    return {
        key: sum(int(item["partial_exposure"][key]) for item in completed)
        for key in sorted(keys)
    }


def save_block(out, seed, result, launch_sha):
    import numpy as np

    block = Path(out) / f"seed_{seed}"
    block.mkdir(exist_ok=False)
    np.savez_compressed(block / "trajectory.npz", **result["trajectory"])
    np.savez_compressed(block / "planning.npz", **result["planning"])
    np.savez_compressed(block / "frozen_state.npz", **result["frozen_state"])
    summary = dict(result["summary"])
    summary.update(
        object=OBJECT,
        stage=STAGE,
        launch_sha=launch_sha,
        plan_source=PLAN_SOURCE,
        b09_evidence_commit=B09_EVIDENCE_COMMIT,
    )
    write_json(block / "summary.json", summary)
    digests = {
        path.relative_to(block).as_posix(): sha256(path)
        for path in sorted(block.rglob("*"))
        if path.is_file()
    }
    write_json(block / "artifacts.json", digests)
    return summary


def run_stage(args, admission):
    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.law_table_b11.study import (
        Config,
        EXPOSURE_KEYS,
        reduce_blocks,
        run_evaluation,
    )

    args.out = prepare_output_directory(args.out)
    metadata = {
        "object": OBJECT,
        "stage": STAGE,
        "status": "RUNNING",
        "launch_sha": args.launch_sha,
        "admission": admission,
        "plan_source": PLAN_SOURCE,
        "b09_evidence_commit": B09_EVIDENCE_COMMIT,
        "input_root": INPUT_SUFFIX.as_posix(),
        "output_root": str(args.out),
        "seeds": list(args.seeds),
        "config": asdict(Config()),
        "planned_new_fits": 0,
        "started_new_fits": 0,
        "completed_new_fits": 0,
        "started_evaluation_blocks": 0,
        "completed_evaluation_blocks": 0,
        "evaluation_attempts": [],
        "completed_blocks": [],
        "numpy_version": np.__version__,
        "numeric_threads": 1,
        "zero_learning_semantics": {
            "new_fits": 0,
            "training_observations": 0,
            "count_updates": 0,
            "gradients": 0,
            "actor_value_network_forwards": 0,
            "learner_probability_queries": 0,
        },
        "historical_input_cost": {
            "source_object": "three sealed B09 final64 states",
            "historical_fits": 3,
            "source_observations": 192,
            "target_observations": 192,
            "role": "already incurred method-construction cost; excluded from B11 new exposure",
        },
        "serialization_contract": "atomic JSON with readback; compressed trajectory, planning, and frozen-state arrays; per-block and root digests",
    }
    write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    try:
        frozen, input_manifest = load_all_inputs()
        current_source_manifest = source_manifest()
        validate_source_manifest(
            current_source_manifest, frozen[SEEDS[0]]["b09_source_manifest"]
        )
        write_json(args.out / "input-manifest.json", input_manifest)
        write_json(args.out / "source-manifest.json", current_source_manifest)
        for seed in args.seeds:
            metadata["current_seed"] = int(seed)
            exposure = {key: 0 for key in EXPOSURE_KEYS}
            attempt = begin_evaluation(metadata, seed, exposure)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            result = run_evaluation(
                Config(), int(seed), frozen[int(seed)], exposure=exposure
            )
            complete_evaluation(metadata, attempt, result)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            block = save_block(args.out, int(seed), result, args.launch_sha)
            attempt["saved"] = True
            metadata["completed_blocks"].append(block)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_complete", "seed": seed}), flush=True)

        observed = aggregate_completed_exposure(metadata["evaluation_attempts"])
        expected = {
            "custom_geometry_channel_refreshes": 192,
            "deep_copies": 98304,
            "evaluation_native_step_calls": 12288,
            "implicit_constructor_resets": 192,
            "logical_episode_initializations": 192,
            "native_constructors": 192,
            "planner_native_step_calls": 98304,
            "training_native_step_calls": 0,
        }
        if observed != expected:
            raise RuntimeError(
                f"completed B11 exposure disagrees with declaration: {observed}"
            )
        metadata.update(
            status="COMPLETE",
            observed_exposure=observed,
            reduction=reduce_blocks(metadata["completed_blocks"]),
            total_native_step_calls=110592,
            actual_native_step_calls=12288,
            planning_native_step_calls=98304,
            loaded_fixed_states=3,
            loaded_source_probability_views=3,
            loaded_target_probability_views=3,
            loader_unused_marginal_product_views=3,
            learner_probability_queries=0,
            response_tables=12288,
            source_table_q_vectors=12288,
            target_table_q_vectors=12288,
            source_table_candidate_choices=12288,
            target_table_candidate_choices=12288,
            actual_focal_policy_choices=12288,
            external_innovation_draw_calls=12288,
            unique_external_innovation_addresses=3072,
            native_constructors=192,
            implicit_constructor_resets=192,
            logical_episode_initializations=192,
            custom_geometry_channel_refreshes=192,
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
        parser.error("seeds/order must equal the prospective B11 declaration")
    if not has_fixed_output_suffix(args.out):
        parser.error("out must end with the fixed B11 output suffix")
    args.out = args.out.resolve()
    admission = require_admission(
        __file__, direction="skill_teammate_drift_learning"
    )
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")
    run_stage(args, admission)


if __name__ == "__main__":
    main()
