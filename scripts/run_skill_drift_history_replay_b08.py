"""Native B08 fixed-history crossing over the sealed B07 evidence."""

import argparse
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


OBJECT = "skill_drift_history_replay_b08"
STAGE = "prospective_diagnostic"
SEEDS = (95301, 95302, 95303)
EVIDENCE_COMMIT = "6ab8db786a2dc2397d883e8476ccb0303b059f0e"
SCIENTIFIC_SOURCE = "03d3633bd55b4095d7b195ad5ecd3f44eb3c864a"
PLAN_COMMIT = "9d7f9a4d9624bec3a5ea69e88f04e1d9912ade78"
INPUT_ROOT = ROOT / "runs/skill_teammate_drift_learning/b07_own_collection_exploration"
OUTPUT_SUFFIX = Path(
    "runs/skill_teammate_drift_learning/b08_fixed_history_crossing"
)
OUTPUT_ROOT = ROOT / OUTPUT_SUFFIX
ROOT_SUMMARY_SHA256 = "b3f9cae1d6bcffde868b659db345a8eac4952768ffc6f2c785e021c014cf4fcb"
MANIFEST_SHA256 = {
    95301: "ce1ff62b8d5c0ee2113faf3861cb19f3c2d5c7920aba8746fc4cbd4409e6e620",
    95302: "2ab5f14494eeaa231a57ad4b1e3fbd35837e9b2d7a8ef3d0033d0f767feddf37",
    95303: "c011ab2891fdc5030afa446bc7ad8da9b160fd4e691b611864dd83c51782a57d",
}
CONTINUATION_IDS = ("R_on_F_E_history", "F_on_R_E_history")


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)
    if json.loads(path.read_bytes()) != value:
        raise IOError(f"JSON readback mismatch: {path}")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def has_fixed_output_suffix(path):
    actual = Path(path).resolve().parts
    suffix = OUTPUT_SUFFIX.parts
    return len(actual) >= len(suffix) and actual[-len(suffix) :] == suffix


def prepare_output_directory(path):
    """Accept launcher bookkeeping, but never an earlier scientific operation."""
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise NotADirectoryError(path)
    protected = ("summary.json", "input-manifest.json", "artifacts.json")
    present = [name for name in protected if (path / name).exists()]
    present.extend(child.name for child in path.glob("seed_*") if child.exists())
    if present:
        raise FileExistsError(
            f"refusing existing B08 scientific output: {sorted(present)}"
        )
    return path


def stable_science_digests(path):
    """Hash owned immutable science files, excluding mutable launcher records."""
    path = Path(path).resolve()
    stable = [path / "summary.json", path / "input-manifest.json"]
    stable.extend(
        candidate
        for block in sorted(path.glob("seed_*"))
        for candidate in sorted(block.rglob("*"))
        if candidate.is_file()
    )
    missing = [candidate.name for candidate in stable[:2] if not candidate.is_file()]
    if missing:
        raise FileNotFoundError(f"missing stable B08 science files: {missing}")
    return {
        candidate.relative_to(path).as_posix(): sha256(candidate)
        for candidate in stable
    }


def begin_fit_attempt(metadata, *, seed, continuation):
    attempt = {
        "seed": int(seed),
        "continuation": continuation.id,
        "recipient_branch": continuation.recipient_branch,
        "donor_branch": continuation.donor_branch,
        "status": "RUNNING",
    }
    metadata["fit_attempts"].append(attempt)
    metadata["started_decision_fits"] += 1
    return attempt


def complete_fit_attempt(metadata, attempt, fit_summary):
    if attempt["status"] != "RUNNING":
        raise RuntimeError("fit attempt was not running")
    attempt.update(
        status="COMPLETE",
        saved=False,
        records_read=int(fit_summary["records_read"]),
        recorded_feedback_updates=int(fit_summary["recorded_feedback_updates"]),
        compute_wall_seconds=float(fit_summary["compute_wall_seconds"]),
        counts=fit_summary["counts"],
    )
    metadata["completed_decision_fits"] += 1


def mark_fit_attempts_saved(attempts):
    for attempt in attempts:
        if attempt["status"] != "COMPLETE" or attempt.get("saved") is not False:
            raise RuntimeError("only completed unsaved fits can be marked saved")
        attempt["saved"] = True


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


def _require_evidence_commit():
    subprocess.run(
        ["git", "cat-file", "-e", f"{EVIDENCE_COMMIT}^{{commit}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", EVIDENCE_COMMIT, "HEAD"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def load_all_inputs():
    """Validate all fixed evidence bytes before any continuation starts."""
    from experiments.candidates.skill_teammate_drift_learning.history_replay_b08.study import (
        validate_block_inputs,
    )

    _require_evidence_commit()
    root_summary = INPUT_ROOT / "summary.json"
    if sha256(root_summary) != ROOT_SUMMARY_SHA256:
        raise ValueError("B07 root summary digest mismatch")
    summary = json.loads(root_summary.read_text())
    if (
        summary.get("status") != "COMPLETE"
        or summary.get("source_identity") != SCIENTIFIC_SOURCE
        or summary.get("seeds") != list(SEEDS)
    ):
        raise ValueError("B07 root result identity mismatch")
    blocks = {
        seed: validate_block_inputs(
            input_root=INPUT_ROOT,
            seed=seed,
            expected_manifest_sha256=MANIFEST_SHA256[seed],
            expected_source_identity=SCIENTIFIC_SOURCE,
        )
        for seed in SEEDS
    }
    manifest = {
        "evidence_commit": EVIDENCE_COMMIT,
        "scientific_source": SCIENTIFIC_SOURCE,
        "plan_commit": PLAN_COMMIT,
        "input_root": str(INPUT_ROOT.relative_to(ROOT)),
        "root_summary_sha256": ROOT_SUMMARY_SHA256,
        "seeds": {
            str(seed): {
                "artifact_manifest_sha256": MANIFEST_SHA256[seed],
                "verified_required_artifacts": blocks[seed]["verified_digests"],
            }
            for seed in SEEDS
        },
    }
    return blocks, manifest


def _save_block(out, seed, loaded, continuations, reduction, launch_sha):
    import numpy as np

    block_root = Path(out) / f"seed_{seed}"
    block_root.mkdir(exist_ok=False)
    for continuation_id, payload in continuations.items():
        path = block_root / continuation_id
        path.mkdir()
        np.savez_compressed(path / "trajectory.npz", **payload["trajectory"])
        np.savez_compressed(path / "state.npz", **payload["state"])
        write_json(path / "summary.json", payload["summary"])
    np.savez_compressed(
        block_root / "reused_diagonals.npz",
        R_on_R_context=loaded["branches"]["R_E"]["diagonal"]["context"],
        R_on_R_matched_epsilon_expected_return=loaded["branches"]["R_E"][
            "diagonal"
        ]["matched_epsilon_expected_return"],
        F_on_F_context=loaded["branches"]["F_E"]["diagonal"]["context"],
        F_on_F_matched_epsilon_expected_return=loaded["branches"]["F_E"][
            "diagonal"
        ]["matched_epsilon_expected_return"],
    )
    write_json(block_root / "reduction.json", reduction)
    summary = {
        "object": OBJECT,
        "stage": STAGE,
        "status": "COMPLETE",
        "seed": seed,
        "launch_sha": launch_sha,
        "evidence_commit": EVIDENCE_COMMIT,
        "scientific_source": SCIENTIFIC_SOURCE,
        "input_manifest_sha256": loaded["manifest_sha256"],
        "continuations": list(CONTINUATION_IDS),
        "settings": {
            "response": "response_all__response__prior2",
            "full": "fingerprint_full__hybrid__prior2",
        },
        "config": {
            "source_state_after_macros": 2048,
            "target_records_per_fit": 256,
            "contexts": 4,
            "matched_epsilon": 0.20,
        },
        "decision_fits": 2,
        "target_records_read": 512,
        "new_preupdate_q_predictions": 512,
        "scalar_policy_reductions": 1024,
        "source_fits": 0,
        "law_fits": 0,
        "environment_ticks": 0,
        "sampled_rewards": 0,
        "gradient_optimizer_calls": 0,
        "reduction": reduction,
    }
    write_json(block_root / "summary.json", summary)
    digests = {}
    for path in sorted(block_root.rglob("*")):
        if path.is_file():
            digests[path.relative_to(block_root).as_posix()] = sha256(path)
    write_json(block_root / "artifacts.json", digests)
    return summary


def run_stage(args, admission):
    for variable in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        os.environ[variable] = "1"
    import numpy as np

    from experiments.candidates.skill_teammate_drift_learning.history_replay_b08.study import (
        CONTINUATIONS,
        reduce_crossed_histories,
        run_continuation,
    )

    args.out = prepare_output_directory(args.out)
    metadata = {
        "object": OBJECT,
        "stage": STAGE,
        "status": "RUNNING",
        "launch_sha": args.launch_sha,
        "admission": admission,
        "evidence_commit": EVIDENCE_COMMIT,
        "scientific_source": SCIENTIFIC_SOURCE,
        "plan_commit": PLAN_COMMIT,
        "input_root": str(INPUT_ROOT.relative_to(ROOT)),
        "output_root": str(args.out),
        "seeds": list(args.seeds),
        "continuations": list(CONTINUATION_IDS),
        "source_training_records_read": 0,
        "source_observations_per_restored_state": 2048,
        "planned_validation_source_state_roundtrips": 6,
        "planned_fit_source_state_restorations": 6,
        "target_macros_per_fit": 256,
        "planned_decision_fits": 6,
        "started_decision_fits": 0,
        "completed_decision_fits": 0,
        "fit_attempts": [],
        "completed_blocks": [],
        "numpy_version": np.__version__,
        "dtype": "float64",
        "blas_threads": 1,
        "readout_role": "off-collector fixed-history matched-epsilon recommendation value",
        "no_actual_collector_or_sampled_reward_claim": True,
    }
    write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    try:
        loaded_blocks, input_manifest = load_all_inputs()
        write_json(args.out / "input-manifest.json", input_manifest)
        metadata["input_manifest_output_sha256"] = sha256(
            args.out / "input-manifest.json"
        )
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
        for seed in args.seeds:
            loaded = loaded_blocks[seed]
            metadata["current_seed"] = seed
            results = {}
            block_attempts = []
            for continuation in CONTINUATIONS:
                metadata["current_continuation"] = continuation.id
                attempt = begin_fit_attempt(
                    metadata, seed=seed, continuation=continuation
                )
                block_attempts.append(attempt)
                write_json(args.out / "summary.json", {**metadata, **resource_fields()})
                recipient = loaded["branches"][continuation.recipient_branch]
                donor = loaded["branches"][continuation.donor_branch]
                payload = run_continuation(
                    spec=continuation.spec,
                    source_state=recipient["source_state"],
                    donor_rows=donor["donor_rows"],
                    expected_first_raw_prediction=recipient["first_raw_prediction"],
                )
                payload["summary"].update(
                    continuation=continuation.id,
                    recipient_branch=continuation.recipient_branch,
                    donor_branch=continuation.donor_branch,
                    donor_manifest_sha256=loaded["manifest_sha256"],
                    donor_required_artifact_digests=loaded["verified_digests"],
                    seed=seed,
                    launch_sha=args.launch_sha,
                    evidence_commit=EVIDENCE_COMMIT,
                    scientific_source=SCIENTIFIC_SOURCE,
                )
                complete_fit_attempt(metadata, attempt, payload["summary"])
                results[continuation.id] = payload
                write_json(args.out / "summary.json", {**metadata, **resource_fields()})

            reduction = reduce_crossed_histories(
                r_on_r=loaded["branches"]["R_E"]["diagonal"],
                f_on_r=results["F_on_R_E_history"]["trajectory"],
                r_on_f=results["R_on_F_E_history"]["trajectory"],
                f_on_f=loaded["branches"]["F_E"]["diagonal"],
            )
            block_summary = _save_block(
                args.out, seed, loaded, results, reduction, args.launch_sha
            )
            mark_fit_attempts_saved(block_attempts)
            metadata["completed_blocks"].append(block_summary)
            metadata.pop("current_continuation", None)
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_complete", "seed": seed}), flush=True)

        metadata.update(
            status="COMPLETE",
            total_target_records_read=1536,
            total_recorded_feedback_updates=1536,
            total_new_preupdate_q_predictions=1536,
            total_scalar_policy_reductions=3072,
            total_source_fits=0,
            total_law_fits=0,
            total_environment_ticks=0,
            total_sampled_rewards=0,
            total_gradient_optimizer_calls=0,
            completed_validation_source_state_roundtrips=6,
            completed_fit_source_state_restorations=6,
            total_source_state_restore_events=12,
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
        parser.error("seeds/order must equal the prospective B08 declaration")
    if not has_fixed_output_suffix(args.out):
        parser.error("out must end with the fixed B08 output suffix")
    args.out = args.out.resolve()
    admission = require_admission(
        __file__, direction="skill_teammate_drift_learning"
    )
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")
    run_stage(args, admission)


if __name__ == "__main__":
    main()
