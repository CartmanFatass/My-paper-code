"""Decide the registered R36 episodic joint-novelty access gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np


ARMS = ("aem_joint_novelty", "constant_code_mappo")
TREATMENT = "aem_joint_novelty"
CONTROL = "constant_code_mappo"
CYCLE_FIELD = "alice_bob_cycle_success_rate"
COLLECTION_FIELD = "alice_bob_targets_completed"
ZERO_CYCLE_FIELD = "alice_bob_zero_cycle_episode_flag"
COVERAGE_FIELDS = (
    "alice_bob_joint_position_coverage_ratio",
    "alice_bob_joint_position_coverage",
    "alice_bob_joint_position_coverage_fraction",
    "joint_position_coverage",
)
AEM_FIELDS = (
    "aem_active",
    "aem_bonus_applied_steps",
    "aem_bonus_sum",
    "aem_bonus_mean",
    "aem_bonus_min",
    "aem_bonus_max",
    "aem_count_resets",
    "aem_preincrement_count_max",
    "aem_formula_max_abs_error",
    "aem_forbidden_field_reads",
)


def load_numeric_csv(path: Path) -> tuple[list[dict[str, float]], tuple[str, ...]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        for raw in reader:
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None or value in (None, ""):
                    continue
                try:
                    number = float(value)
                except ValueError:
                    continue
                if math.isfinite(number):
                    row[key] = number
            rows.append(row)
    return rows, fieldnames


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"manifest is not an object: {path}")
    return payload


def resolved_path(value: object, base: Path) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def find_coverage_field(fieldnames: tuple[str, ...]) -> str | None:
    return next((name for name in COVERAGE_FIELDS if name in fieldnames), None)


def all_zero(
    rows: list[dict[str, float]], field: str, tolerance: float = 1e-12
) -> bool:
    return all(abs(float(row.get(field, 0.0))) <= tolerance for row in rows)


def finite_sum(rows: list[dict[str, float]], field: str) -> float:
    return float(sum(float(row.get(field, 0.0)) for row in rows))


def shape_signature(manifest: dict) -> dict[str, object]:
    algorithm = manifest.get("algorithm_config", {})
    runtime = manifest.get("agent_runtime_spec", {})
    model = manifest.get("model_config", {})
    if not isinstance(algorithm, dict):
        algorithm = {}
    if not isinstance(runtime, dict):
        runtime = {}
    if not isinstance(model, dict):
        model = {}
    return {
        "state_dim": model.get("state_dim"),
        "obs_dim": model.get("obs_dim"),
        "action_dim": model.get("action_dim"),
        "n_agents": model.get("n_agents"),
        "hidden_size": model.get("hidden_size"),
        "n_skills": runtime.get("n_skills"),
        "low_level_architecture": runtime.get("low_level_architecture"),
        "use_recurrent_low_level": runtime.get("use_recurrent_low_level"),
        "low_actor_condition_on_team_code": runtime.get(
            "low_actor_condition_on_team_code"
        ),
        "use_centralized_low_value": algorithm.get("use_centralized_low_value"),
        "low_rnn_hidden_size": algorithm.get("low_rnn_hidden_size"),
        "low_sequence_length": algorithm.get("low_sequence_length"),
        "low_sequence_batch_size": algorithm.get("low_sequence_batch_size"),
    }


def summarize_arm(
    arm_root: Path,
    *,
    repo_root: Path,
    init_checkpoint: Path,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
    expected_config: str,
    treatment: bool,
) -> tuple[dict, dict[int, dict[str, float]], list[str], dict[str, object]]:
    train, train_fields = load_numeric_csv(arm_root / "metrics" / "train_updates.csv")
    evaluation, eval_fields = load_numeric_csv(
        arm_root / "metrics" / "eval_episodes.csv"
    )
    manifest = load_manifest(arm_root / "metadata" / "run_manifest.json")
    train.sort(key=lambda row: row.get("update", -1.0))
    reasons: list[str] = []

    latest_eval_step = max(
        (int(row.get("total_steps", -1)) for row in evaluation), default=-1
    )
    final_eval = [
        row for row in evaluation if int(row.get("total_steps", -1)) == latest_eval_step
    ]
    by_episode: dict[int, dict[str, float]] = {}
    for row in final_eval:
        episode = int(row.get("episode", -1))
        if episode in by_episode:
            reasons.append(f"duplicate final evaluation episode {episode}")
        by_episode[episode] = row

    coverage_field = find_coverage_field(eval_fields)
    if coverage_field is None:
        reasons.append("final evaluation is missing joint-position coverage")
    for field in (
        CYCLE_FIELD,
        COLLECTION_FIELD,
        ZERO_CYCLE_FIELD,
        "reward",
        "action_mode_code",
    ):
        if field not in eval_fields:
            reasons.append(f"final evaluation CSV is missing {field}")
        elif any(field not in row for row in final_eval):
            reasons.append(f"one or more final evaluation rows omit {field}")
    if coverage_field is not None and any(
        coverage_field not in row for row in final_eval
    ):
        reasons.append(f"one or more final evaluation rows omit {coverage_field}")

    update_ids = [int(row.get("update", -1)) for row in train]
    if len(train) != expected_updates:
        reasons.append(f"train row count {len(train)} != {expected_updates}")
    if update_ids != list(range(1, expected_updates + 1)):
        reasons.append("training update indices are not exactly 1..expected_updates")
    final_train_steps = int(train[-1].get("total_steps", -1)) if train else -1
    if final_train_steps != total_timesteps:
        reasons.append(f"final train steps {final_train_steps} != {total_timesteps}")
    if latest_eval_step != total_timesteps:
        reasons.append(f"final eval steps {latest_eval_step} != {total_timesteps}")
    if len(final_eval) != eval_episodes:
        reasons.append(f"final eval rows {len(final_eval)} != {eval_episodes}")
    if set(by_episode) != set(range(eval_episodes)):
        reasons.append("final evaluation episode indices are not exactly registered")
    low_update_rows = sum(
        float(row.get("low_sequence_chunks", 0.0)) > 0.0 for row in train
    )
    if low_update_rows != expected_updates:
        reasons.append(f"low update rows {low_update_rows} != {expected_updates}")

    args = manifest.get("args", {})
    algorithm = manifest.get("algorithm_config", {})
    runtime = manifest.get("agent_runtime_spec", {})
    if not isinstance(args, dict):
        args = {}
    if not isinstance(algorithm, dict):
        algorithm = {}
    if not isinstance(runtime, dict):
        runtime = {}
    resume_path = resolved_path(args.get("resume_from"), repo_root)
    if resume_path != init_checkpoint:
        reasons.append(f"resume checkpoint {resume_path} != common init {init_checkpoint}")
    if str(args.get("config", "")) != expected_config:
        reasons.append(f"config {args.get('config')!r} != {expected_config!r}")
    if str(args.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
        reasons.append("CLI high controller is not r30_fixed_clock_ar_edit")
    if str(runtime.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
        reasons.append("runtime high controller is not r30_fixed_clock_ar_edit")
    if not bool(algorithm.get("constant_skill_no_high", False)):
        reasons.append("constant_skill_no_high is not enabled")
    if not bool(runtime.get("constant_skill_no_high", False)):
        reasons.append("runtime constant-skill mode is not enabled")
    if int(args.get("num_envs", -1)) != 16:
        reasons.append("num_envs is not 16")
    if int(args.get("rollout_length", -1)) != 80:
        reasons.append("rollout_length is not 80")
    if int(args.get("total_timesteps", -1)) != total_timesteps:
        reasons.append("manifest total_timesteps differs from the gate")
    if str(args.get("collector_backend", "")) != "subproc":
        reasons.append("collector backend is not subproc")
    if str(args.get("collector_start_method", "")) != "spawn":
        reasons.append("collector start method is not spawn")
    if str(args.get("device", "")) != "cuda":
        reasons.append("device is not cuda")
    if int(args.get("save_interval", -1)) != 0:
        reasons.append("save_interval is not zero")
    if int(algorithm.get("low_ppo_epochs", -1)) != 5:
        reasons.append("low_ppo_epochs is not 5")
    if int(algorithm.get("low_sequence_length", -1)) != 10:
        reasons.append("low_sequence_length is not 10")
    if int(algorithm.get("low_sequence_batch_size", -1)) != 64:
        reasons.append("low_sequence_batch_size is not 64")
    if not bool(algorithm.get("use_centralized_low_value", False)):
        reasons.append("centralized low value is disabled")

    for field, expected in (
        ("aem_joint_novelty_enabled", treatment),
        ("aem_joint_position_grid_size", 5),
        ("aem_joint_position_table_size", 625),
        ("aem_episode_horizon", 80),
        ("aem_position_view_name", "alice_bob_normalized_joint_positions_v1"),
        ("aem_bonus_formula", "inverse_horizon_sqrt_preincrement_v1"),
    ):
        actual = algorithm.get(field)
        if actual != expected:
            reasons.append(f"algorithm_config {field}={actual!r} != {expected!r}")

    if bool(algorithm.get("alice_bob_semantic_reward_enabled", True)):
        reasons.append("Alice--Bob semantic reward is enabled")
    if abs(float(algorithm.get("transition_skill_reward_coef", math.inf))) > 1e-12:
        reasons.append("transition-skill reward coefficient is nonzero")
    if str(algorithm.get("process_reward_injection", "")) != "none":
        reasons.append("process reward injection is not none")
    for field in train_fields:
        if not field.endswith("reward_applied_steps"):
            continue
        if field == "aem_bonus_applied_steps":
            continue
        if not all_zero(train, field):
            reasons.append(f"non-AEM intrinsic reward reached policy updates: {field}")
    if "combined_intrinsic_env_ratio" in train_fields and not all_zero(
        train, "combined_intrinsic_env_ratio"
    ):
        reasons.append("non-AEM combined intrinsic reward ratio is nonzero")

    sparse_reward_exact = all(
        abs(float(row.get("reward", math.inf)) - float(row.get(COLLECTION_FIELD, 0.0)))
        <= 1e-9
        for row in final_eval
    )
    if not sparse_reward_exact:
        reasons.append("evaluation reward is not exact sparse collection count")
    if any(
        abs(float(row.get("action_mode_code", -1.0)) - 1.0) > 1e-12
        for row in final_eval
    ):
        reasons.append("final evaluation is not stochastic")
    if any(
        abs(
            float(row.get(ZERO_CYCLE_FIELD, math.inf))
            - float(float(row.get(CYCLE_FIELD, math.nan)) <= 0.0)
        )
        > 1e-12
        for row in final_eval
    ):
        reasons.append("zero-cycle flag disagrees with cycle success")

    high_decision_rows = finite_sum(train, "r30_decision_rows")
    high_update_rows = finite_sum(train, "r30_high_rows")
    if abs(high_decision_rows) > 1e-12 or abs(high_update_rows) > 1e-12:
        reasons.append("constant-code arm produced high decision or optimizer rows")

    missing_aem_fields = [field for field in AEM_FIELDS if field not in train_fields]
    if missing_aem_fields:
        reasons.append("training CSV is missing AEM audit fields: " + ",".join(missing_aem_fields))
    omitted_aem_fields = [
        field for field in AEM_FIELDS if any(field not in row for row in train)
    ]
    if omitted_aem_fields:
        reasons.append(
            "one or more training rows omit AEM audit fields: "
            + ",".join(omitted_aem_fields)
        )
    aem_totals = {field: finite_sum(train, field) for field in AEM_FIELDS}
    aem_maxima = {
        field: max((float(row.get(field, 0.0)) for row in train), default=0.0)
        for field in AEM_FIELDS
    }
    aem_minima = {
        field: min((float(row.get(field, 0.0)) for row in train), default=0.0)
        for field in AEM_FIELDS
    }
    if treatment:
        if any(abs(float(row.get("aem_active", 0.0)) - 1.0) > 1e-12 for row in train):
            reasons.append("treatment does not report aem_active=1 on every update")
        if abs(aem_totals["aem_bonus_applied_steps"] - total_timesteps) > 1e-9:
            reasons.append(
                "treatment AEM applied-step count does not equal total exposure"
            )
        if aem_totals["aem_bonus_sum"] <= 0.0:
            reasons.append("treatment AEM bonus sum is not positive")
        if aem_maxima["aem_bonus_max"] > (1.0 / 80.0) + 1e-12:
            reasons.append("treatment AEM bonus exceeds the registered first-visit maximum")
        if aem_minima["aem_bonus_min"] <= 0.0:
            reasons.append("treatment AEM bonus contains a nonpositive applied value")
        if aem_totals["aem_count_resets"] <= 0.0:
            reasons.append("treatment AEM episodic counts never reset")
        if aem_maxima["aem_formula_max_abs_error"] > 1e-12:
            reasons.append("treatment AEM formula audit is nonzero")
        if aem_totals["aem_forbidden_field_reads"] != 0.0:
            reasons.append("treatment AEM read a forbidden task/skill field")
    else:
        nonzero = [field for field in AEM_FIELDS if not all_zero(train, field)]
        if nonzero:
            reasons.append("control has nonzero AEM metrics: " + ",".join(nonzero))

    periodic_checkpoints = sorted(arm_root.glob("standalone_process_core_update_*.pt"))
    final_checkpoint = arm_root / "standalone_process_core_final.pt"
    if periodic_checkpoints:
        reasons.append("periodic checkpoints were written")
    if not final_checkpoint.is_file():
        reasons.append("final checkpoint is missing")

    model_shape = shape_signature(manifest)
    missing_shape_fields = [key for key, value in model_shape.items() if value is None]
    if missing_shape_fields:
        reasons.append(
            "manifest is missing low-stack shape fields: "
            + ",".join(missing_shape_fields)
        )

    final_cycle = [float(row[CYCLE_FIELD]) for row in final_eval if CYCLE_FIELD in row]
    final_coverage = (
        [float(row[coverage_field]) for row in final_eval if coverage_field in row]
        if coverage_field is not None
        else []
    )
    summary = {
        "arm_root": str(arm_root),
        "config": str(args.get("config", "")),
        "resume_from": str(resume_path) if resume_path is not None else None,
        "train_updates": len(train),
        "low_updates": int(low_update_rows),
        "final_train_steps": final_train_steps,
        "final_eval_steps": latest_eval_step,
        "final_eval_episodes": len(final_eval),
        "coverage_field": coverage_field,
        "cycle_success_mean": fmean(final_cycle) if final_cycle else None,
        "joint_position_coverage_mean": fmean(final_coverage) if final_coverage else None,
        "episodes_with_collection": sum(
            float(row.get(COLLECTION_FIELD, 0.0)) > 0.0 for row in final_eval
        ),
        "zero_cycle_fraction": (
            fmean(float(row[ZERO_CYCLE_FIELD]) for row in final_eval if ZERO_CYCLE_FIELD in row)
            if any(ZERO_CYCLE_FIELD in row for row in final_eval)
            else None
        ),
        "sparse_reward_exact": sparse_reward_exact,
        "high_decision_rows": high_decision_rows,
        "high_update_rows": high_update_rows,
        "aem_totals": aem_totals,
        "aem_maxima": aem_maxima,
        "aem_minima": aem_minima,
        "shape_signature": model_shape,
        "periodic_checkpoint_count": len(periodic_checkpoints),
        "final_checkpoint": str(final_checkpoint),
        "valid": not reasons,
        "invalid_reasons": reasons,
    }
    return summary, by_episode, reasons, manifest


def interval(samples: np.ndarray, observed: float) -> dict[str, float]:
    return {
        "mean": float(observed),
        "lower": float(np.quantile(samples, 0.025)),
        "upper": float(np.quantile(samples, 0.975)),
    }


def safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator > 0.0:
        return float(numerator / denominator)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--init-checkpoint", required=True)
    parser.add_argument("--seed", type=int, default=37_031)
    parser.add_argument("--total-timesteps", type=int, default=320_000)
    parser.add_argument("--expected-updates", type=int, default=250)
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=40_037_031)
    args = parser.parse_args()
    if args.seed != 37_031:
        parser.error("R36 fixes --seed at 37031")
    if args.bootstrap_repetitions != 10_000:
        parser.error("R36 fixes --bootstrap-repetitions at 10000")
    if args.bootstrap_seed != 40_037_031:
        parser.error("R36 fixes --bootstrap-seed at 40037031")

    run_root = Path(args.run_root).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    init_checkpoint = Path(args.init_checkpoint).resolve()
    expected_configs = {
        TREATMENT: "ha_ctse_process.config_alice_bob_aem",
        CONTROL: "ha_ctse_process.config_alice_bob_sparse_mappo",
    }
    summaries: dict[str, dict] = {}
    episode_rows: dict[str, dict[int, dict[str, float]]] = {}
    all_reasons: list[str] = []

    if not init_checkpoint.is_file():
        all_reasons.append(f"common init checkpoint is missing: {init_checkpoint}")
    init_manifest_path = init_checkpoint.parent / "metadata" / "run_manifest.json"
    if not init_manifest_path.is_file():
        all_reasons.append(f"common init manifest is missing: {init_manifest_path}")
    else:
        init_manifest = load_manifest(init_manifest_path)
        init_args = init_manifest.get("args", {})
        init_algorithm = init_manifest.get("algorithm_config", {})
        init_runtime = init_manifest.get("agent_runtime_spec", {})
        if int(init_manifest.get("total_steps", -1)) != 0:
            all_reasons.append("common init checkpoint is not a 0-step checkpoint")
        if int(init_manifest.get("update_idx", -1)) != 0:
            all_reasons.append("common init checkpoint has a nonzero update index")
        if str(init_args.get("config", "")) != expected_configs[CONTROL]:
            all_reasons.append("common init did not use the constant-code config")
        if not bool(init_algorithm.get("constant_skill_no_high", False)):
            all_reasons.append("common init is not constant-code")
        if bool(init_algorithm.get("aem_joint_novelty_enabled", True)):
            all_reasons.append("common init has AEM enabled")
        if str(init_runtime.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
            all_reasons.append("common init did not use the R30 module stack")

    for arm in ARMS:
        try:
            summary, rows, reasons, _manifest = summarize_arm(
                run_root / "runs" / arm / f"seed{args.seed}",
                repo_root=repo_root,
                init_checkpoint=init_checkpoint,
                total_timesteps=args.total_timesteps,
                expected_updates=args.expected_updates,
                eval_episodes=args.eval_episodes,
                expected_config=expected_configs[arm],
                treatment=arm == TREATMENT,
            )
        except Exception as exc:
            all_reasons.append(f"{arm}: unable to read registered artifacts: {exc}")
            continue
        summaries[arm] = summary
        episode_rows[arm] = rows
        all_reasons.extend(f"{arm}: {reason}" for reason in reasons)

    if set(summaries) == set(ARMS):
        if summaries[TREATMENT]["shape_signature"] != summaries[CONTROL]["shape_signature"]:
            all_reasons.append("low actor/centralized critic shape signatures differ")

    implementation_valid = not all_reasons and set(summaries) == set(ARMS)
    status = "INVALID_R36_AEM_IMPLEMENTATION"
    comparison: dict[str, object] = {}
    m1 = {
        "treatment_cycle_success_floor": 0.05,
        "treatment_collection_episode_floor": 10,
        "paired_collection_indicator_gain_floor": 0.10,
        "paired_collection_indicator_ci_lower_strict": 0.0,
        "passed": False,
    }
    m2 = {
        "joint_position_coverage_ratio_floor": 1.50,
        "paired_coverage_difference_ci_lower_strict": 0.0,
        "treatment_zero_cycle_fraction_ceiling_strict": 0.90,
        "passed": False,
    }

    if implementation_valid:
        treatment_rows = episode_rows[TREATMENT]
        control_rows = episode_rows[CONTROL]
        episode_ids = list(range(args.eval_episodes))
        treatment_collection = np.asarray(
            [float(treatment_rows[idx][COLLECTION_FIELD] > 0.0) for idx in episode_ids],
            dtype=np.float64,
        )
        control_collection = np.asarray(
            [float(control_rows[idx][COLLECTION_FIELD] > 0.0) for idx in episode_ids],
            dtype=np.float64,
        )
        collection_difference = treatment_collection - control_collection
        cycle_difference = np.asarray(
            [
                treatment_rows[idx][CYCLE_FIELD] - control_rows[idx][CYCLE_FIELD]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        treatment_coverage_field = summaries[TREATMENT]["coverage_field"]
        control_coverage_field = summaries[CONTROL]["coverage_field"]
        coverage_difference = np.asarray(
            [
                treatment_rows[idx][treatment_coverage_field]
                - control_rows[idx][control_coverage_field]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        zero_cycle_difference = np.asarray(
            [
                treatment_rows[idx][ZERO_CYCLE_FIELD]
                - control_rows[idx][ZERO_CYCLE_FIELD]
                for idx in episode_ids
            ],
            dtype=np.float64,
        )
        rng = np.random.default_rng(args.bootstrap_seed)
        sample_indices = rng.integers(
            0,
            args.eval_episodes,
            size=(args.bootstrap_repetitions, args.eval_episodes),
        )
        collection_ci = interval(
            collection_difference[sample_indices].mean(axis=1),
            float(collection_difference.mean()),
        )
        cycle_ci = interval(
            cycle_difference[sample_indices].mean(axis=1),
            float(cycle_difference.mean()),
        )
        coverage_ci = interval(
            coverage_difference[sample_indices].mean(axis=1),
            float(coverage_difference.mean()),
        )
        zero_cycle_ci = interval(
            zero_cycle_difference[sample_indices].mean(axis=1),
            float(zero_cycle_difference.mean()),
        )
        coverage_ratio = safe_ratio(
            float(summaries[TREATMENT]["joint_position_coverage_mean"]),
            float(summaries[CONTROL]["joint_position_coverage_mean"]),
        )
        comparison = {
            "direction": "aem_joint_novelty_minus_constant_code_mappo",
            "paired_collection_indicator": collection_ci,
            "cycle_success": cycle_ci,
            "joint_position_coverage": coverage_ci,
            "zero_cycle_fraction": zero_cycle_ci,
            "treatment_control_mean_coverage_ratio": coverage_ratio,
            "bootstrap_repetitions": args.bootstrap_repetitions,
            "bootstrap_seed": args.bootstrap_seed,
        }

        treatment_cycle = float(summaries[TREATMENT]["cycle_success_mean"])
        treatment_collection_episodes = int(
            summaries[TREATMENT]["episodes_with_collection"]
        )
        m1_passed = bool(
            treatment_cycle >= 0.05
            and treatment_collection_episodes >= 10
            and collection_ci["mean"] >= 0.10
            and collection_ci["lower"] > 0.0
        )
        m1.update(
            {
                "treatment_cycle_success_mean": treatment_cycle,
                "treatment_episodes_with_collection": treatment_collection_episodes,
                "paired_collection_indicator": collection_ci,
                "passed": m1_passed,
            }
        )
        treatment_zero_cycle = float(summaries[TREATMENT]["zero_cycle_fraction"])
        m2_passed = bool(
            coverage_ratio is not None
            and coverage_ratio >= 1.50
            and coverage_ci["lower"] > 0.0
            and treatment_zero_cycle < 0.90
        )
        m2.update(
            {
                "treatment_control_mean_coverage_ratio": coverage_ratio,
                "paired_coverage_difference": coverage_ci,
                "treatment_zero_cycle_fraction": treatment_zero_cycle,
                "passed": m2_passed,
            }
        )
        if not m1_passed:
            status = "FAIL_M1_RETIRE_R36_AEM"
        elif not m2_passed:
            status = "FAIL_M2_ACCESS_WITHOUT_CARRIER"
        else:
            status = "PASS_R36_AEM_ACCESS"

    result = {
        "experiment_id": "EXP-20260715-r36-aem-access",
        "status": status,
        "scope": "single-seed sparse Alice--Bob task-generic access gate",
        "seed": args.seed,
        "total_timesteps_per_arm": args.total_timesteps,
        "common_init_checkpoint": str(init_checkpoint),
        "implementation_valid": implementation_valid,
        "invalid_reasons": all_reasons,
        "arms": summaries,
        "paired_comparison": comparison,
        "gates": {
            "m0_implementation": {
                "passed": implementation_valid,
                "invalid_reasons": all_reasons,
            },
            "m1_access": m1,
            "m2_visitation_carrier_safety": m2,
        },
    }
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "r36_aem_access.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
