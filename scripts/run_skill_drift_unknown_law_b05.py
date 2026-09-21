"""Admitted two-stage B05: causal unknown-law development and held-out exploration."""

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

DIRECTION = "skill_teammate_drift_learning"
OBJECT = "unknown_joint_law_b05"
DEVELOPMENT_SEEDS = (95001, 95002, 95003)
HELDOUT_SEEDS = (95101, 95102, 95103)
FAMILIES = ("response_all", "fingerprint_full", "fingerprint_recent")
SELECTION_SCHEMA = "b05-legal-feedback-selection-v1"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(json_bytes(value))
    temporary.replace(path)
    if json.loads(path.read_bytes()) != value:
        raise IOError(f"JSON readback mismatch: {path}")


def score_feedback(predictions, greedy, collection_action, reward, phase):
    """No evaluator values/probabilities accepted by this selection interface."""
    import numpy as np

    predictions = np.asarray(predictions, dtype=np.float64)
    greedy = np.asarray(greedy)
    action = np.asarray(collection_action)
    reward = np.asarray(reward)
    phase = np.asarray(phase)
    n = len(action)
    if predictions.shape != (n, 2) or any(x.shape != (n,) for x in (greedy, reward, phase)):
        raise ValueError("selection arrays have inconsistent shape")
    if not np.isfinite(predictions).all() or np.any((predictions < 0) | (predictions > 1)):
        raise ValueError("selection requires finite clipped pre-outcome predictions")
    if any(not np.isin(x, (0, 1)).all() for x in (greedy, action, reward, phase)):
        raise ValueError("selection action/reward/phase is not binary")
    if not np.array_equal(greedy, (predictions[:, 1] > predictions[:, 0]).astype(int)):
        raise ValueError("greedy choices disagree with the fixed SAFE tie rule")
    target = np.flatnonzero(phase == 1)
    if not len(target):
        raise ValueError("selection has no target rows")
    early = target[:64]
    row = np.arange(n)
    chosen_q = predictions[row, greedy.astype(int)]
    collected_q = predictions[row, action.astype(int)]
    dr = chosen_q + 2.0 * (greedy == action) * (reward - collected_q)
    brier = (reward - collected_q) ** 2
    return {
        "primary_dr_reward": float(np.mean(dr[early])),
        "whole_target_reward_brier": float(np.mean(brier[target])),
        "primary_rows": int(len(early)),
        "target_rows": int(len(target)),
    }


def choose_settings(score_rows, specs, development_seeds):
    """Fixed, family-specific choice from lawful feedback scores only."""
    import numpy as np

    specs_by_id = {spec.id: spec for spec in specs}
    if len(specs_by_id) != len(specs):
        raise ValueError("duplicate setting id")
    expected = {(int(seed), setting) for seed in development_seeds for setting in specs_by_id}
    actual = [(int(row["seed"]), row["setting_id"]) for row in score_rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("development scores do not cover the fixed bank and seeds exactly")
    ranking = []
    for setting, spec in specs_by_id.items():
        rows = [row for row in score_rows if row["setting_id"] == setting]
        dr = np.asarray([row["primary_dr_reward"] for row in rows], dtype=np.float64)
        brier = np.asarray([row["whole_target_reward_brier"] for row in rows], dtype=np.float64)
        if not np.isfinite(dr).all() or not np.isfinite(brier).all():
            raise ValueError("non-finite development score")
        ranking.append({
            "setting_id": setting,
            "spec": asdict(spec),
            "mean_primary_dr_reward": float(dr.mean()),
            "mean_whole_target_reward_brier": float(brier.mean()),
        })
    selected = {}
    for family in FAMILIES:
        members = [row for row in ranking if row["spec"]["family"] == family]
        if not members:
            raise ValueError(f"missing family: {family}")
        best = max(row["mean_primary_dr_reward"] for row in members)
        tied = [row for row in members if best - row["mean_primary_dr_reward"] <= 1e-12]
        choice = min(tied, key=lambda row: (row["mean_whole_target_reward_brier"], row["setting_id"]))
        selected[family] = {"setting_id": choice["setting_id"], "spec": choice["spec"]}
    return selected, ranking


def validate_selection(payload, config, bank):
    if payload.get("schema") != SELECTION_SCHEMA or payload.get("object") != OBJECT:
        raise ValueError("wrong selection object/schema")
    if payload.get("config") != asdict(config):
        raise ValueError("selection horizon/host differs from held-out contract")
    if payload.get("development_seeds") != list(DEVELOPMENT_SEEDS):
        raise ValueError("selection development identities differ from the fixed batch")
    selected, ranking = choose_settings(payload["score_rows"], bank, DEVELOPMENT_SEEDS)
    if payload.get("selected") != selected or payload.get("ranking") != ranking:
        raise ValueError("selection is not the declared mechanical choice from saved scores")
    by_id = {spec.id: spec for spec in bank}
    return [by_id[selected[family]["setting_id"]] for family in FAMILIES]


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


def save_block(out, result, seed, stage, launch_sha, result_object=OBJECT):
    import numpy as np

    block_root = out / f"seed_{seed}"
    block_root.mkdir(exist_ok=False)
    np.savez_compressed(block_root / "common.npz", **result["common"])
    block_summary = dict(result["summary"])
    block_summary.update(
        seed=seed, stage=stage, launch_sha=launch_sha, object=result_object
    )
    write_json(block_root / "summary.json", block_summary)
    for setting, fit in result["fits"].items():
        fit_root = block_root / setting
        fit_root.mkdir()
        np.savez_compressed(fit_root / "curves.npz", **fit["curves"])
        np.savez_compressed(fit_root / "state.npz", **fit["state"])
        fit_summary = dict(fit["summary"])
        fit_summary.update(
            seed=seed,
            stage=stage,
            setting_id=setting,
            launch_sha=launch_sha,
            object=result_object,
        )
        write_json(fit_root / "summary.json", fit_summary)
    digests = {}
    for path in sorted(block_root.rglob("*")):
        if path.is_file():
            digests[path.relative_to(block_root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(block_root / "artifacts.json", digests)
    return block_summary


def run_stage(
    args,
    admission,
    *,
    result_object=OBJECT,
    result_stage=None,
    batch_metadata=None,
):
    # Set numerical thread policy before importing NumPy in this process.
    for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS"):
        os.environ[variable] = "1"
    import numpy as np
    from experiments.candidates.skill_teammate_drift_learning.unknown_law_b05.study import (
        Config, development_specs, run_block,
    )

    config = Config()
    bank = development_specs()
    selection_bytes = None
    if args.stage == "heldout":
        selection_bytes = args.selection.read_bytes()
        if hashlib.sha256(selection_bytes).hexdigest() != args.selection_sha256:
            raise ValueError("selection digest mismatch; no fit started")
        specs = validate_selection(json.loads(selection_bytes), config, bank)
    else:
        specs = bank
    args.out.mkdir(parents=True, exist_ok=True)  # kernel owns the already-created run root
    if (args.out / "summary.json").exists():
        raise FileExistsError("refusing to overwrite an existing scientific summary")
    if selection_bytes is not None:
        (args.out / "selection-input.json").write_bytes(selection_bytes)
    published_stage = args.stage if result_stage is None else result_stage
    metadata = {
        "object": result_object, "status": "RUNNING", "stage": published_stage,
        "launch_sha": args.launch_sha, "config": asdict(config), "seeds": args.seeds,
        "settings": [{"setting_id": spec.id, "spec": asdict(spec)} for spec in specs],
        "selection_sha256": args.selection_sha256,
        "numpy_version": np.__version__, "dtype": "float64", "blas_threads": 1,
        "planned_decision_fits": len(specs) * len(args.seeds),
        "planned_shared_law_fits": len(args.seeds),
        "started_decision_fits": 0, "started_shared_law_fits": 0,
        "completed_decision_fits": 0, "completed_shared_law_fits": 0,
        "completed_blocks": [], "comparisons_by_seed": [], "gradient_optimizer_calls": 0,
        "selection_uses": "pre-outcome predictions and observed collector feedback only",
        "independent_unit": "fresh block, all decision settings share the collected stream",
        "scope": "exogenous correlated three-tick terminal host; exact expected greedy value under passive collection",
    }
    if batch_metadata is not None:
        metadata["batch_metadata"] = dict(batch_metadata)
    write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    score_rows = []
    try:
        for seed in args.seeds:
            metadata["started_decision_fits"] += len(specs)
            metadata["started_shared_law_fits"] += 1
            metadata["current_seed"] = seed
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_started", "stage": published_stage, "seed": seed, "decision_fits": len(specs)}), flush=True)
            block_started = time.monotonic()
            result = run_block(config, seed=seed, specs=specs)
            result["summary"]["scientific_block_wall_seconds"] = time.monotonic() - block_started
            result["summary"]["scientific_block_wall_scope"] = "common collection, all learners and exact evaluator; excludes serialization and import"
            if set(result["fits"]) != {spec.id for spec in specs}:
                raise ValueError("scientific block omitted or added a setting")
            block = save_block(
                args.out,
                result,
                seed,
                published_stage,
                args.launch_sha,
                result_object=result_object,
            )
            metadata["completed_blocks"].append(block)
            metadata["completed_decision_fits"] += len(specs)
            metadata["completed_shared_law_fits"] += 1
            if args.stage == "development":
                for spec in specs:
                    curves = result["fits"][spec.id]["curves"]
                    common = result["common"]
                    score = score_feedback(curves["clipped_predictions"], curves["greedy_action"],
                                           common["collection_action"], common["reward"], common["phase"])
                    score_rows.append({"seed": seed, "setting_id": spec.id, **score})
            else:
                family_results = {spec.family: result["fits"][spec.id]["summary"] for spec in specs}
                compared = {}
                for endpoint in ("first64", "full", "late64"):
                    response = family_results["response_all"]["target_by_endpoint"][endpoint]
                    compared[endpoint] = {}
                    for reference in ("fingerprint_full", "fingerprint_recent"):
                        ordinary = family_results[reference]["target_by_endpoint"][endpoint]
                        compared[endpoint][f"response_minus_{reference}"] = {
                            "task_value_difference": response["mean_expected_return"] - ordinary["mean_expected_return"],
                            "regret_difference": response["mean_regret"] - ordinary["mean_regret"],
                            "sign_mistake_difference": response["sign_mistakes"] - ordinary["sign_mistakes"],
                        }
                metadata["comparisons_by_seed"].append({"seed": seed, "by_endpoint": compared})
            write_json(args.out / "summary.json", {**metadata, **resource_fields()})
            print(json.dumps({"event": "block_complete", "stage": published_stage, "seed": seed}), flush=True)
        if args.stage == "development":
            selected, ranking = choose_settings(score_rows, specs, args.seeds)
            selection = {
                "schema": SELECTION_SCHEMA, "object": OBJECT, "source_sha": args.launch_sha,
                "config": asdict(config), "development_seeds": args.seeds,
                "score_rows": score_rows, "ranking": ranking, "selected": selected,
                "rule": "max mean first64 DR reward; 1e-12 tie then lower full-target reward Brier then lexical id",
            }
            write_json(args.out / "selection.json", selection)
            metadata["selection_output_sha256"] = hashlib.sha256((args.out / "selection.json").read_bytes()).hexdigest()
            metadata["selected"] = selected
        total_macros = config.total_macros * len(args.seeds)
        metadata.update(
            status="COMPLETE", unique_collection_macros=total_macros,
            unique_primitive_ticks=total_macros * config.skill_ticks,
            decision_reading_macros=total_macros * len(specs),
            decision_reading_tick_exposure=total_macros * len(specs) * config.skill_ticks,
            exact_greedy_evaluation_panels=total_macros * len(specs),
            shared_known_response_diagnostic_panels=total_macros,
            evaluation_environment_ticks=0, evaluation_reward_draws=0,
        )
        metadata.pop("current_seed", None)
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
    except BaseException as error:
        metadata.update(status="TECHNICAL_FAILURE", error_type=type(error).__name__, error=str(error))
        write_json(args.out / "summary.json", {**metadata, **resource_fields()})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("development", "heldout"), required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--launch-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--selection", type=Path)
    parser.add_argument("--selection-sha256")
    args = parser.parse_args(argv)
    expected = DEVELOPMENT_SEEDS if args.stage == "development" else HELDOUT_SEEDS
    if tuple(args.seeds) != expected:
        parser.error("seeds/order must equal the prospective stage declaration")
    if args.stage == "heldout" and (args.selection is None or args.selection_sha256 is None):
        parser.error("heldout requires selection bytes and SHA256")
    if args.stage == "development" and (args.selection is not None or args.selection_sha256 is not None):
        parser.error("development cannot consume a selection")
    admission = require_admission(__file__, direction="skill_teammate_drift_learning")
    if args.launch_sha != admission["sha"]:
        parser.error("launch-sha must equal admitted source SHA")
    run_stage(args, admission)


if __name__ == "__main__":
    main()
