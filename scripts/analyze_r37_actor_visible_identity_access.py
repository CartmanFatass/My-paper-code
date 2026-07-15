"""Decide the registered R37 actor-visible task-identity access gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean

import numpy as np


ARMS = ("identity_visible", "identity_masked")
TREATMENT = "identity_visible"
CONTROL = "identity_masked"
CYCLE_FIELD = "alice_bob_cycle_success_rate"
COLLECTION_FIELD = "alice_bob_targets_completed"
ZERO_CYCLE_FIELD = "alice_bob_zero_cycle_episode_flag"
COVERAGE_FIELDS = (
    "alice_bob_joint_position_coverage_ratio",
    "alice_bob_joint_position_coverage",
    "alice_bob_joint_position_coverage_fraction",
    "joint_position_coverage",
)
IDENTITY_FIELDS = (
    "r37_identity_audit_active",
    "r37_identity_mode_code",
    "r37_identity_audit_rows",
    "r37_identity_slot_max_abs_error",
    "r37_critic_identity_max_abs_error",
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


def all_zero(
    rows: list[dict[str, float]], field: str, tolerance: float = 1e-12
) -> bool:
    return all(abs(float(row.get(field, 0.0))) <= tolerance for row in rows)


def finite_sum(rows: list[dict[str, float]], field: str) -> float:
    return float(sum(float(row.get(field, 0.0)) for row in rows))


def find_coverage_field(fieldnames: tuple[str, ...]) -> str | None:
    return next((name for name in COVERAGE_FIELDS if name in fieldnames), None)


def shape_signature(manifest: dict) -> dict[str, object]:
    model = manifest.get("model_config", {})
    runtime = manifest.get("agent_runtime_spec", {})
    env_runtime = manifest.get("env_runtime_spec", {})
    algorithm = manifest.get("algorithm_config", {})
    for name, value in (
        ("model_config", model),
        ("agent_runtime_spec", runtime),
        ("env_runtime_spec", env_runtime),
        ("algorithm_config", algorithm),
    ):
        if not isinstance(value, dict):
            raise ValueError(f"manifest {name} is not an object")
    return {
        "model_obs_dim": model.get("obs_dim"),
        "model_state_dim": model.get("state_dim"),
        "model_action_dim": model.get("action_dim"),
        "model_n_agents": model.get("n_agents"),
        "model_hidden_size": model.get("hidden_size"),
        "runtime_obs_dim": runtime.get("obs_dim"),
        "runtime_action_dim": runtime.get("action_dim"),
        "runtime_n_agents": runtime.get("n_agents"),
        "env_obs_dim": env_runtime.get("obs_dim"),
        "env_state_dim": env_runtime.get("state_dim"),
        "low_level_architecture": runtime.get("low_level_architecture"),
        "use_recurrent_low_level": runtime.get("use_recurrent_low_level"),
        "use_centralized_low_value": algorithm.get("use_centralized_low_value"),
        "low_rnn_hidden_size": algorithm.get("low_rnn_hidden_size"),
        "low_sequence_length": algorithm.get("low_sequence_length"),
        "low_sequence_batch_size": algorithm.get("low_sequence_batch_size"),
        "parameter_counts": runtime.get("parameter_counts"),
    }


def summarize_arm(
    arm_root: Path,
    *,
    repo_root: Path,
    init_checkpoint: Path,
    seed: int,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
    expected_config: str,
    expected_mode: str,
) -> tuple[dict, dict[int, dict[str, float]], list[str], dict]:
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
    required_eval = (
        CYCLE_FIELD,
        COLLECTION_FIELD,
        ZERO_CYCLE_FIELD,
        "reward",
        "action_mode_code",
        "reset_seed",
        *IDENTITY_FIELDS,
    )
    for field in required_eval:
        if field not in eval_fields:
            reasons.append(f"final evaluation CSV is missing {field}")
        elif any(field not in row for row in final_eval):
            reasons.append(f"one or more final evaluation rows omit {field}")
    if coverage_field is None:
        reasons.append("final evaluation is missing joint-position coverage")
    elif any(coverage_field not in row for row in final_eval):
        reasons.append(f"one or more final evaluation rows omit {coverage_field}")

    update_ids = [int(row.get("update", -1)) for row in train]
    if len(train) != expected_updates:
        reasons.append(f"train row count {len(train)} != {expected_updates}")
    if update_ids != list(range(1, expected_updates + 1)):
        reasons.append("training update indices are not exactly registered")
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

    for field in IDENTITY_FIELDS:
        if field not in train_fields:
            reasons.append(f"training CSV is missing {field}")
        elif any(field not in row for row in train):
            reasons.append(f"one or more training rows omit {field}")
    mode_code = 1.0 if expected_mode == "visible" else 0.0
    if any(abs(float(row.get("r37_identity_audit_active", 0.0)) - 1.0) > 1e-12 for row in train):
        reasons.append("R37 training identity audit is not active on every update")
    if any(abs(float(row.get("r37_identity_mode_code", -9.0)) - mode_code) > 1e-12 for row in train):
        reasons.append("R37 training identity mode code is wrong")
    expected_train_audits = float(total_timesteps * 2)
    if abs(finite_sum(train, "r37_identity_audit_rows") - expected_train_audits) > 1e-9:
        reasons.append("R37 training identity audit row count is not exact")
    for field in (
        "r37_identity_slot_max_abs_error",
        "r37_critic_identity_max_abs_error",
    ):
        if not all_zero(train, field):
            reasons.append(f"R37 training audit has nonzero {field}")
    for episode, row in by_episode.items():
        expected_reset_seed = seed + 100_000 + episode
        if int(row.get("reset_seed", -1)) != expected_reset_seed:
            reasons.append(f"evaluation episode {episode} reset seed is not paired")
        if abs(float(row.get("r37_identity_audit_active", 0.0)) - 1.0) > 1e-12:
            reasons.append(f"evaluation episode {episode} identity audit is inactive")
        if abs(float(row.get("r37_identity_mode_code", -9.0)) - mode_code) > 1e-12:
            reasons.append(f"evaluation episode {episode} identity mode is wrong")
        if abs(float(row.get("r37_identity_audit_rows", -1.0)) - 160.0) > 1e-12:
            reasons.append(f"evaluation episode {episode} audit rows are not 160")
        for field in (
            "r37_identity_slot_max_abs_error",
            "r37_critic_identity_max_abs_error",
        ):
            if abs(float(row.get(field, math.inf))) > 1e-12:
                reasons.append(f"evaluation episode {episode} has nonzero {field}")

    intrinsic_fields = sorted(
        field for field in train_fields if field.endswith("reward_applied_steps")
    )
    nonzero_intrinsic = [
        field for field in intrinsic_fields if not all_zero(train, field)
    ]
    nonzero_intrinsic.extend(
        field for field in train_fields if field.startswith("aem_") and not all_zero(train, field)
    )
    if "combined_intrinsic_env_ratio" in train_fields and not all_zero(
        train, "combined_intrinsic_env_ratio"
    ):
        nonzero_intrinsic.append("combined_intrinsic_env_ratio")
    if nonzero_intrinsic:
        reasons.append(
            "intrinsic reward reached R37 updates: "
            + ",".join(sorted(set(nonzero_intrinsic)))
        )

    sparse_reward_exact = all(
        abs(float(row.get("reward", math.inf)) - float(row.get(COLLECTION_FIELD, 0.0)))
        <= 1e-9
        for row in final_eval
    )
    if not sparse_reward_exact:
        reasons.append("evaluation reward is not exact sparse collection count")
    if any(abs(float(row.get("action_mode_code", -1.0)) - 1.0) > 1e-12 for row in final_eval):
        reasons.append("final evaluation is not stochastic")

    args = manifest.get("args", {})
    algorithm = manifest.get("algorithm_config", {})
    runtime = manifest.get("agent_runtime_spec", {})
    model = manifest.get("model_config", {})
    env_runtime = manifest.get("env_runtime_spec", {})
    for name, value in (
        ("args", args),
        ("algorithm_config", algorithm),
        ("agent_runtime_spec", runtime),
        ("model_config", model),
        ("env_runtime_spec", env_runtime),
    ):
        if not isinstance(value, dict):
            reasons.append(f"manifest {name} is not an object")
    resume_path = resolved_path(args.get("resume_from"), repo_root)
    if resume_path != init_checkpoint:
        reasons.append(f"resume checkpoint {resume_path} != common init")
    if str(args.get("config", "")) != expected_config:
        reasons.append(f"config {args.get('config')!r} != {expected_config!r}")
    exact_args = {
        "seed": seed,
        "n_agents": 2,
        "num_envs": 16,
        "rollout_length": 80,
        "skill_interval": 10,
        "total_timesteps": total_timesteps,
        "eval_interval": total_timesteps,
        "eval_episodes": eval_episodes,
        "eval_max_steps": 80,
        "save_interval": 0,
    }
    for name, expected in exact_args.items():
        if int(args.get(name, -1)) != expected:
            reasons.append(f"manifest arg {name} is not {expected}")
    for name, expected in (
        ("collector_backend", "subproc"),
        ("collector_start_method", "spawn"),
        ("device", "cuda"),
        ("eval_action_mode", "stochastic"),
        ("high_controller", "r30_fixed_clock_ar_edit"),
    ):
        if str(args.get(name, "")) != expected:
            reasons.append(f"manifest arg {name} is not {expected}")

    expected_algorithm = {
        "constant_skill_no_high": True,
        "r37_identity_gate_enabled": True,
        "alice_bob_actor_identity_mode": expected_mode,
        "alice_bob_actor_identity_slots": 4,
        "alice_bob_actor_identity_schema": "active_plate_target_onehot_v1",
        "aem_joint_novelty_enabled": False,
        "alice_bob_semantic_reward_enabled": False,
        "r31_effect_mode": "off",
        "process_reward_injection": "none",
        "low_ppo_epochs": 5,
        "low_sequence_length": 10,
        "low_sequence_batch_size": 64,
    }
    for name, expected in expected_algorithm.items():
        if algorithm.get(name) != expected:
            reasons.append(f"algorithm_config {name}={algorithm.get(name)!r} != {expected!r}")
    if abs(float(algorithm.get("transition_skill_reward_coef", math.inf))) > 1e-12:
        reasons.append("transition-skill reward coefficient is nonzero")
    if not bool(runtime.get("constant_skill_no_high", False)):
        reasons.append("runtime constant-skill mode is disabled")
    if str(runtime.get("high_controller", "")) != "r30_fixed_clock_ar_edit":
        reasons.append("runtime high controller is wrong")

    shape = shape_signature(manifest)
    exact_shape = {
        "model_obs_dim": 16,
        "model_state_dim": 19,
        "model_action_dim": 2,
        "model_n_agents": 2,
        "runtime_obs_dim": 16,
        "runtime_action_dim": 2,
        "runtime_n_agents": 2,
        "env_obs_dim": 16,
        "env_state_dim": 19,
    }
    for name, expected in exact_shape.items():
        if shape.get(name) != expected:
            reasons.append(f"shape {name}={shape.get(name)!r} != {expected}")
    if not isinstance(shape.get("parameter_counts"), dict):
        reasons.append("parameter-count signature is missing")

    high_decision_rows = finite_sum(train, "r30_decision_rows")
    high_update_rows = finite_sum(train, "r30_high_rows")
    if abs(high_decision_rows) > 1e-12 or abs(high_update_rows) > 1e-12:
        reasons.append("R37 constant-code arm produced high rows")
    periodic_checkpoints = sorted(arm_root.glob("standalone_process_core_update_*.pt"))
    final_checkpoint = arm_root / "standalone_process_core_final.pt"
    if periodic_checkpoints:
        reasons.append("periodic checkpoints were written")
    if not final_checkpoint.is_file():
        reasons.append("final checkpoint is missing")

    cycle = [float(row[CYCLE_FIELD]) for row in final_eval if CYCLE_FIELD in row]
    coverage = (
        [float(row[coverage_field]) for row in final_eval if coverage_field in row]
        if coverage_field is not None
        else []
    )
    rewards = [float(row["reward"]) for row in final_eval if "reward" in row]
    summary = {
        "arm_root": str(arm_root),
        "config": str(args.get("config", "")),
        "identity_mode": expected_mode,
        "resume_from": str(resume_path) if resume_path is not None else None,
        "train_updates": len(train),
        "low_updates": low_update_rows,
        "final_train_steps": final_train_steps,
        "final_eval_steps": latest_eval_step,
        "final_eval_episodes": len(final_eval),
        "cycle_success_mean": fmean(cycle) if cycle else None,
        "episodes_with_collection": sum(
            float(row.get(COLLECTION_FIELD, 0.0)) > 0.0 for row in final_eval
        ),
        "episodes_with_cycle": sum(float(row.get(CYCLE_FIELD, 0.0)) > 0.0 for row in final_eval),
        "mean_sparse_reward": fmean(rewards) if rewards else None,
        "zero_cycle_fraction": fmean(
            float(row[ZERO_CYCLE_FIELD]) for row in final_eval if ZERO_CYCLE_FIELD in row
        ) if final_eval else None,
        "coverage_field": coverage_field,
        "joint_position_coverage_mean": fmean(coverage) if coverage else None,
        "training_identity_audit_rows": finite_sum(train, "r37_identity_audit_rows"),
        "shape_signature": shape,
        "sparse_reward_exact": sparse_reward_exact,
        "high_decision_rows": high_decision_rows,
        "high_update_rows": high_update_rows,
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--init-checkpoint", required=True)
    parser.add_argument("--seed", type=int, default=38_031)
    parser.add_argument("--total-timesteps", type=int, default=320_000)
    parser.add_argument("--expected-updates", type=int, default=250)
    parser.add_argument("--eval-episodes", type=int, default=64)
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=40_038_031)
    args = parser.parse_args()
    if args.seed != 38_031:
        parser.error("R37 fixes --seed at 38031")
    if args.bootstrap_repetitions != 10_000:
        parser.error("R37 fixes --bootstrap-repetitions at 10000")
    if args.bootstrap_seed != 40_038_031:
        parser.error("R37 fixes --bootstrap-seed at 40038031")

    run_root = Path(args.run_root).resolve()
    repo_root = Path(__file__).resolve().parents[1]
    init_checkpoint = Path(args.init_checkpoint).resolve()
    expected_configs = {
        TREATMENT: "ha_ctse_process.config_alice_bob_identity_visible",
        CONTROL: "ha_ctse_process.config_alice_bob_identity_masked",
    }
    expected_modes = {TREATMENT: "visible", CONTROL: "masked"}
    summaries: dict[str, dict] = {}
    episode_rows: dict[str, dict[int, dict[str, float]]] = {}
    manifests: dict[str, dict] = {}
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
        init_model = init_manifest.get("model_config", {})
        init_runtime = init_manifest.get("agent_runtime_spec", {})
        if int(init_manifest.get("total_steps", -1)) != 0:
            all_reasons.append("common init checkpoint is not zero-step")
        if int(init_manifest.get("update_idx", -1)) != 0:
            all_reasons.append("common init checkpoint has nonzero update index")
        if str(init_args.get("config", "")) != expected_configs[CONTROL]:
            all_reasons.append("common init did not use the masked R37 config")
        if str(init_algorithm.get("alice_bob_actor_identity_mode", "")) != "masked":
            all_reasons.append("common init identity mode is not masked")
        if not bool(init_algorithm.get("r37_identity_gate_enabled", False)):
            all_reasons.append("common init did not enable the R37 schema")
        if int(init_model.get("obs_dim", -1)) != 16 or int(init_model.get("state_dim", -1)) != 19:
            all_reasons.append("common init model dimensions are not 16/19")
        if not bool(init_runtime.get("constant_skill_no_high", False)):
            all_reasons.append("common init is not constant-code")

    for arm in ARMS:
        try:
            summary, rows, reasons, manifest = summarize_arm(
                run_root / "runs" / arm / f"seed{args.seed}",
                repo_root=repo_root,
                init_checkpoint=init_checkpoint,
                seed=args.seed,
                total_timesteps=args.total_timesteps,
                expected_updates=args.expected_updates,
                eval_episodes=args.eval_episodes,
                expected_config=expected_configs[arm],
                expected_mode=expected_modes[arm],
            )
        except Exception as exc:
            all_reasons.append(f"{arm}: unable to read registered artifacts: {exc}")
            continue
        summaries[arm] = summary
        episode_rows[arm] = rows
        manifests[arm] = manifest
        all_reasons.extend(f"{arm}: {reason}" for reason in reasons)

    if set(summaries) == set(ARMS):
        if summaries[TREATMENT]["shape_signature"] != summaries[CONTROL]["shape_signature"]:
            all_reasons.append("actor/critic shape or parameter signatures differ")
        for section in ("training_config", "model_config", "physical_env_config", "env_runtime_spec"):
            if manifests[TREATMENT].get(section) != manifests[CONTROL].get(section):
                all_reasons.append(f"arm manifests differ in {section}")
        left = dict(manifests[TREATMENT].get("algorithm_config", {}))
        right = dict(manifests[CONTROL].get("algorithm_config", {}))
        for payload in (left, right):
            payload.pop("algorithm", None)
            payload.pop("alice_bob_actor_identity_mode", None)
        if left != right:
            all_reasons.append("algorithm configs differ beyond identity mode/name")

    implementation_valid = not all_reasons and set(summaries) == set(ARMS)
    status = "INVALID_R37_IMPLEMENTATION"
    comparison: dict[str, object] = {}
    m1 = {
        "treatment_cycle_success_floor": 0.05,
        "treatment_collection_episode_floor": 10,
        "paired_collection_indicator_ci_lower_strict": 0.0,
        "passed": False,
    }
    m2 = {
        "treatment_mean_sparse_reward_strict": 0.0,
        "treatment_cycle_episode_floor": 1,
        "passed": False,
    }
    m3 = {"treatment_zero_cycle_fraction_ceiling_strict": 0.90, "passed": False}

    if implementation_valid:
        treatment_rows = episode_rows[TREATMENT]
        control_rows = episode_rows[CONTROL]
        episode_ids = list(range(args.eval_episodes))
        paired: dict[str, np.ndarray] = {
            "collection_indicator": np.asarray(
                [
                    float(treatment_rows[i][COLLECTION_FIELD] > 0.0)
                    - float(control_rows[i][COLLECTION_FIELD] > 0.0)
                    for i in episode_ids
                ],
                dtype=np.float64,
            ),
            "cycle_success": np.asarray(
                [treatment_rows[i][CYCLE_FIELD] - control_rows[i][CYCLE_FIELD] for i in episode_ids],
                dtype=np.float64,
            ),
            "sparse_reward": np.asarray(
                [treatment_rows[i]["reward"] - control_rows[i]["reward"] for i in episode_ids],
                dtype=np.float64,
            ),
            "zero_cycle_fraction": np.asarray(
                [treatment_rows[i][ZERO_CYCLE_FIELD] - control_rows[i][ZERO_CYCLE_FIELD] for i in episode_ids],
                dtype=np.float64,
            ),
        }
        treatment_coverage = summaries[TREATMENT]["coverage_field"]
        control_coverage = summaries[CONTROL]["coverage_field"]
        paired["joint_position_coverage"] = np.asarray(
            [treatment_rows[i][treatment_coverage] - control_rows[i][control_coverage] for i in episode_ids],
            dtype=np.float64,
        )
        rng = np.random.default_rng(args.bootstrap_seed)
        indices = rng.integers(
            0, args.eval_episodes, size=(args.bootstrap_repetitions, args.eval_episodes)
        )
        intervals = {
            name: interval(values[indices].mean(axis=1), float(values.mean()))
            for name, values in paired.items()
        }
        comparison = {
            "direction": "identity_visible_minus_identity_masked",
            **intervals,
            "bootstrap_repetitions": args.bootstrap_repetitions,
            "bootstrap_seed": args.bootstrap_seed,
        }

        treatment_cycle = float(summaries[TREATMENT]["cycle_success_mean"])
        treatment_collections = int(summaries[TREATMENT]["episodes_with_collection"])
        m1_passed = bool(
            treatment_cycle >= 0.05
            and treatment_collections >= 10
            and intervals["collection_indicator"]["lower"] > 0.0
        )
        m1.update(
            {
                "treatment_cycle_success_mean": treatment_cycle,
                "treatment_episodes_with_collection": treatment_collections,
                "paired_collection_indicator": intervals["collection_indicator"],
                "passed": m1_passed,
            }
        )
        treatment_reward = float(summaries[TREATMENT]["mean_sparse_reward"])
        treatment_cycle_episodes = int(summaries[TREATMENT]["episodes_with_cycle"])
        m2_passed = treatment_reward > 0.0 and treatment_cycle_episodes >= 1
        m2.update(
            {
                "treatment_mean_sparse_reward": treatment_reward,
                "treatment_episodes_with_cycle": treatment_cycle_episodes,
                "passed": bool(m2_passed),
            }
        )
        treatment_zero_cycle = float(summaries[TREATMENT]["zero_cycle_fraction"])
        m3_passed = treatment_zero_cycle < 0.90
        m3.update(
            {
                "treatment_zero_cycle_fraction": treatment_zero_cycle,
                "passed": bool(m3_passed),
            }
        )
        status = (
            "PASS_R37_ACCESS"
            if m1_passed and m2_passed and m3_passed
            else "FAIL_R37_ACCESS"
        )

    result = {
        "experiment_id": "EXP-20260715-r37-actor-visible-identity-access",
        "status": status,
        "scope": "single-seed Alice--Bob observation-substrate access gate",
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
            "m2_sparse_task_evidence": m2,
            "m3_stability": m3,
        },
    }
    output_dir = run_root / "result"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "r37_actor_visible_identity_access.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
