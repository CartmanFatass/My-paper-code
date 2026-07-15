"""Decide the lightweight R39 native-categorical temporal mechanism gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean
from typing import Any


EXPERIMENT_ID = "EXP-20260715-r39-toy-native-categorical"
SCENARIO = "two_timescale_role_free_actions"
ARMS = ("adaptive_retention", "force_refresh")
CONFIGS = {
    "adaptive_retention": "ha_ctse_process.config_r39_toy_native_categorical",
    "force_refresh": "ha_ctse_process.config_r39_toy_shared_refresh",
}
FIXED_PRIMITIVES = False
DIRECT_STATE_CONTEXT = False
EXPECTED_FORCE_REFRESH = {"adaptive_retention": False, "force_refresh": True}
EVAL_METRICS = (
    "r39_toy_task_reward",
    "r39_toy_match_score",
    "r39_toy_slow_match",
    "r39_toy_fast_match",
)
TRAIN_REQUIRED = (
    "update",
    "total_steps",
    "r30_decision_rows",
    "r30_tokens_per_decision",
    "r30_continuation_actor_tokens",
    "r30_replay_logp_max_error",
    "r30_normal_decision_rows",
    "r30_full_sync_set_rows",
    "r30_mixed_age_fraction",
    "r30_spell_gt_4k0_count",
    "r30_spell_le_4k0_count",
    "high_policy_actor_grad_norm",
    "high_policy_skill_head_grad_norm",
    "low_optimizer_steps",
    "low_return_env_count",
    "low_replay_logp_max_error",
    "low_squashed_action_policy",
    "low_fixed_primitive_policy",
    "combined_intrinsic_env_ratio",
)


def load_numeric_csv(path: Path) -> tuple[list[dict[str, float]], tuple[str, ...]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows: list[dict[str, float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        for line, raw in enumerate(reader, start=2):
            row: dict[str, float] = {}
            for key, value in raw.items():
                if key is None or key == "checkpoint" or value in (None, ""):
                    continue
                try:
                    number = float(value)
                except ValueError as exc:
                    raise ValueError(f"non-numeric {key} at {path}:{line}") from exc
                if not math.isfinite(number):
                    raise ValueError(f"non-finite {key} at {path}:{line}")
                row[key] = number
            rows.append(row)
    return rows, fields


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def add_reason(reasons: list[str], message: str) -> None:
    if message not in reasons:
        reasons.append(message)


def values(rows: list[dict[str, float]], field: str) -> list[float]:
    return [row[field] for row in rows if field in row]


def mean(rows: list[dict[str, float]], field: str) -> float | None:
    items = values(rows, field)
    return float(fmean(items)) if items else None


def total(rows: list[dict[str, float]], field: str) -> float:
    return float(sum(values(rows, field)))


def weighted_mean(
    rows: list[dict[str, float]], field: str, weight_field: str
) -> float | None:
    pairs = [
        (row[field], row[weight_field])
        for row in rows
        if field in row and row.get(weight_field, 0.0) > 0.0
    ]
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0.0:
        return None
    return float(sum(value * weight for value, weight in pairs) / denominator)


def require_equal(
    actual: object, expected: object, label: str, reasons: list[str]
) -> None:
    if isinstance(expected, float):
        try:
            matches = math.isclose(float(actual), expected, abs_tol=1e-12, rel_tol=1e-12)
        except (TypeError, ValueError):
            matches = False
    else:
        matches = actual == expected
    if not matches:
        add_reason(reasons, f"{label}={actual!r} != {expected!r}")


def validate_manifest(
    manifest: dict[str, Any],
    *,
    arm: str,
    seed: int,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
    reasons: list[str],
) -> None:
    require_equal(manifest.get("total_steps"), total_timesteps, f"{arm} total_steps", reasons)
    require_equal(manifest.get("update_idx"), expected_updates, f"{arm} update_idx", reasons)
    args = manifest.get("args")
    if not isinstance(args, dict):
        add_reason(reasons, f"{arm} manifest args missing")
        args = {}
    expected_args = {
        "config": CONFIGS[arm],
        "scenario": SCENARIO,
        "seed": seed,
        "n_agents": 2,
        "collector_backend": "subproc",
        "collector_start_method": "spawn",
        "num_envs": 16,
        "rollout_length": 40,
        "skill_interval": 5,
        "total_timesteps": total_timesteps,
        "eval_interval": total_timesteps,
        "eval_episodes": eval_episodes,
        "eval_max_steps": 40,
        "eval_action_mode": "stochastic",
        "high_controller": "r30_fixed_clock_ar_edit",
        "device": "cuda",
        "save_interval": 0,
        "checkpoint_keep_last": 1,
        "plot_interval": 0,
    }
    for field, expected in expected_args.items():
        require_equal(args.get(field), expected, f"{arm} args.{field}", reasons)

    algorithm = manifest.get("algorithm_config")
    if not isinstance(algorithm, dict):
        add_reason(reasons, f"{arm} algorithm_config missing")
        algorithm = {}
    expected_algorithm = {
        "r39_native_categorical_edit": True,
        "r39_toy_fixed_skill_primitives": FIXED_PRIMITIVES,
        "r39_toy_direct_state_context": DIRECT_STATE_CONTEXT,
        "r30_force_refresh_every_check": EXPECTED_FORCE_REFRESH[arm],
        "use_recurrent_low_level": False,
        "low_level_architecture": "feedforward",
        "n_z": 4,
        "process_reward_injection": "none",
        "process_reward_coef": 0.0,
        "process_contrast_coef": 0.0,
        "process_outcome_coef": 0.0,
        "use_process_posterior_mi": False,
        "use_residual_process_posterior": False,
        "use_transition_skill_discriminator": False,
        "transition_skill_reward_coef": 0.0,
        "use_outcome_residual_probe": False,
        "outcome_residual_injection": "none",
        "use_topology_role_probe": False,
        "topology_role_injection": "none",
        "use_topology_potential_shaping": False,
        "topology_potential_injection": "none",
        "opt_cd_coef": 0.0,
        "opt_cmi_coef": 0.0,
        "alice_bob_semantic_reward_enabled": False,
        "r31_effect_mode": "off",
    }
    for field, expected in expected_algorithm.items():
        require_equal(
            algorithm.get(field), expected, f"{arm} algorithm_config.{field}", reasons
        )
    if DIRECT_STATE_CONTEXT:
        for field, expected in {
            "opt_compact_dim": 8,
            "team_code_dim": 1,
            "team_bridge_type": "none",
        }.items():
            require_equal(
                algorithm.get(field),
                expected,
                f"{arm} algorithm_config.{field}",
                reasons,
            )
    if FIXED_PRIMITIVES:
        require_equal(
            algorithm.get("r39_toy_fixed_skill_action_schema"),
            "axis4_xy_v1",
            f"{arm} algorithm_config.r39_toy_fixed_skill_action_schema",
            reasons,
        )
    require_equal(
        algorithm.get("aem_joint_novelty_enabled", False),
        False,
        f"{arm} algorithm_config.aem_joint_novelty_enabled",
        reasons,
    )
    training = manifest.get("training_config")
    if not isinstance(training, dict):
        add_reason(reasons, f"{arm} training_config missing")
        training = {}
    require_equal(
        training.get("r29_action_info_mode"),
        "off",
        f"{arm} training_config.r29_action_info_mode",
        reasons,
    )
    model = manifest.get("model_config")
    if not isinstance(model, dict):
        add_reason(reasons, f"{arm} model_config missing")
    else:
        require_equal(model.get("hidden_size"), 32, f"{arm} model_config.hidden_size", reasons)


def summarize_arm(
    root: Path,
    *,
    arm: str,
    seed: int,
    total_timesteps: int,
    expected_updates: int,
    eval_episodes: int,
) -> tuple[dict[str, Any], list[str]]:
    reasons: list[str] = []
    try:
        train, train_fields = load_numeric_csv(root / "metrics" / "train_updates.csv")
        evaluation, eval_fields = load_numeric_csv(root / "metrics" / "eval_episodes.csv")
        manifest = load_json(root / "metadata" / "run_manifest.json")
    except Exception as exc:
        return {"run_root": str(root)}, [f"{arm} artifact read failed: {exc}"]

    validate_manifest(
        manifest,
        arm=arm,
        seed=seed,
        total_timesteps=total_timesteps,
        expected_updates=expected_updates,
        eval_episodes=eval_episodes,
        reasons=reasons,
    )
    for field in TRAIN_REQUIRED:
        if field not in train_fields or any(field not in row for row in train):
            add_reason(reasons, f"{arm} training CSV missing complete field {field}")
    for field in ("reward", "length", "reset_seed", *EVAL_METRICS):
        if field not in eval_fields or any(field not in row for row in evaluation):
            add_reason(reasons, f"{arm} evaluation CSV missing complete field {field}")

    train.sort(key=lambda row: row.get("total_steps", -1.0))
    latest_eval_step = max((row.get("total_steps", -1.0) for row in evaluation), default=-1.0)
    final_eval = [row for row in evaluation if row.get("total_steps") == latest_eval_step]
    late = train[-max(1, len(train) // 2) :]

    if len(train) != expected_updates:
        add_reason(reasons, f"{arm} update count {len(train)} != {expected_updates}")
    expected_step_sequence = list(range(640, total_timesteps + 1, 640))
    actual_step_sequence = [int(row.get("total_steps", -1.0)) for row in train]
    if actual_step_sequence != expected_step_sequence:
        add_reason(reasons, f"{arm} outer-update step sequence is not exact")
    if latest_eval_step != total_timesteps or len(final_eval) != eval_episodes:
        add_reason(reasons, f"{arm} final evaluation is not {eval_episodes} episodes at {total_timesteps}")

    replay_error = max(values(train, "r30_replay_logp_max_error"), default=math.inf)
    decision_rows = [row for row in train if row.get("r30_decision_rows", 0.0) > 0.0]
    if not decision_rows or any(
        abs(row.get("r30_tokens_per_decision", math.inf) - 2.0) > 1e-9
        for row in decision_rows
    ):
        add_reason(reasons, f"{arm} did not execute exactly two tokens per high decision")
    if replay_error > 1e-5:
        add_reason(reasons, f"{arm} replay log-probability error {replay_error} > 1e-5")
    low_replay_error = max(values(train, "low_replay_logp_max_error"), default=math.inf)
    if any(abs(row.get("low_return_env_count", -1.0) - 16.0) > 1e-9 for row in train):
        add_reason(reasons, f"{arm} low returns were not grouped over exactly 16 environments")
    if FIXED_PRIMITIVES:
        if any(abs(row.get("low_optimizer_steps", -1.0)) > 1e-9 for row in train):
            add_reason(reasons, f"{arm} fixed primitives executed a low optimizer step")
        if any(abs(row.get("low_fixed_primitive_policy", 0.0) - 1.0) > 1e-9 for row in train):
            add_reason(reasons, f"{arm} did not execute the fixed primitive carrier")
        if int(manifest.get("agent_runtime_spec", {}).get("parameter_counts", {}).get("low", -1)) != 0:
            add_reason(reasons, f"{arm} fixed primitive carrier had trainable low parameters")
        runtime = manifest.get("agent_runtime_spec", {})
        require_equal(
            runtime.get("direct_state_high_context", False),
            DIRECT_STATE_CONTEXT,
            f"{arm} runtime direct_state_high_context",
            reasons,
        )
        require_equal(
            runtime.get("fixed_skill_action_schema"),
            "axis4_xy_v1",
            f"{arm} runtime fixed_skill_action_schema",
            reasons,
        )
        require_equal(
            runtime.get("fixed_skill_action_table"),
            [[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]],
            f"{arm} runtime fixed_skill_action_table",
            reasons,
        )
        for field in ("low_loss", "low_actor_grad_norm", "low_critic_grad_norm"):
            if any(abs(row.get(field, 0.0)) > 1e-12 for row in train):
                add_reason(reasons, f"{arm} fixed primitives had nonzero {field}")
        if not any(row.get("high_grad_norm", 0.0) > 1e-8 for row in train):
            add_reason(reasons, f"{arm} high controller had no nonzero gradient")
        if not any(
            row.get("high_policy_actor_grad_norm", 0.0) > 1e-8 for row in train
        ):
            add_reason(reasons, f"{arm} high actor received no policy gradient")
        if not any(
            row.get("high_policy_skill_head_grad_norm", 0.0) > 1e-8
            for row in train
        ):
            add_reason(reasons, f"{arm} high skill head received no policy gradient")
    else:
        if low_replay_error > 1e-5:
            add_reason(reasons, f"{arm} low replay log-probability error {low_replay_error} > 1e-5")
        if any(abs(row.get("low_optimizer_steps", -1.0) - 3.0) > 1e-9 for row in train):
            add_reason(reasons, f"{arm} did not execute exactly three low PPO epochs per update")
        if any(abs(row.get("low_squashed_action_policy", 0.0) - 1.0) > 1e-9 for row in train):
            add_reason(reasons, f"{arm} did not use the registered squashed continuous policy")
        if any(abs(row.get("low_fixed_primitive_policy", 0.0)) > 1e-9 for row in train):
            add_reason(reasons, f"{arm} unexpectedly used fixed primitives")
    if total(train, "r30_continuation_actor_tokens") != 0.0:
        add_reason(reasons, f"{arm} continuation rows contained actor tokens")

    intrinsic_fields = sorted(
        field
        for field in train_fields
        if field == "combined_intrinsic_env_ratio"
        or field.endswith("reward_applied_steps")
        or field.endswith("reward_active")
        or field.endswith("reward_env_ratio")
        or field in {"aem_bonus_applied_steps", "aem_bonus_sum", "aem_bonus_max"}
    )
    nonzero_intrinsic = [
        field
        for field in intrinsic_fields
        if any(abs(row.get(field, 0.0)) > 1e-12 for row in train)
    ]
    if nonzero_intrinsic:
        add_reason(reasons, f"{arm} nonzero intrinsic fields: {','.join(nonzero_intrinsic)}")

    normal_rows = total(late, "r30_normal_decision_rows")
    full_sync_rows = total(late, "r30_full_sync_set_rows")
    long_spells = total(late, "r30_spell_gt_4k0_count")
    short_spells = total(late, "r30_spell_le_4k0_count")
    spell_total = long_spells + short_spells
    per_step_rewards = [
        row["reward"] / row["length"]
        for row in final_eval
        if row.get("length", 0.0) > 0.0
    ]
    summary: dict[str, Any] = {
        "run_root": str(root),
        "train_updates": len(train),
        "final_train_steps": int(train[-1].get("total_steps", -1.0)) if train else -1,
        "final_eval_episodes": len(final_eval),
        "parameter_counts": manifest.get("agent_runtime_spec", {}).get("parameter_counts", {}),
        "implementation": {
            "replay_logp_max_error": replay_error,
            "policy_actor_grad_norm_mean": mean(
                train, "high_policy_actor_grad_norm"
            ),
            "policy_skill_head_grad_norm_mean": mean(
                train, "high_policy_skill_head_grad_norm"
            ),
            "low_replay_logp_max_error": low_replay_error,
            "low_optimizer_steps_per_update": mean(train, "low_optimizer_steps"),
            "low_return_env_count": mean(train, "low_return_env_count"),
            "low_squashed_action_policy": mean(train, "low_squashed_action_policy"),
            "low_fixed_primitive_policy": mean(train, "low_fixed_primitive_policy"),
            "continuation_actor_tokens": total(train, "r30_continuation_actor_tokens"),
            "intrinsic_fields_checked": intrinsic_fields,
            "nonzero_intrinsic_fields": nonzero_intrinsic,
        },
        "evaluation": {
            "per_step_reward_mean": float(fmean(per_step_rewards)) if per_step_rewards else None,
            **{field: mean(final_eval, field) for field in EVAL_METRICS},
            "reset_seeds": [int(row["reset_seed"]) for row in final_eval if "reset_seed" in row],
        },
        "late_half_temporal": {
            "normal_decision_rows": normal_rows,
            "full_sync_set_rate": full_sync_rows / normal_rows if normal_rows > 0.0 else None,
            "mixed_age_fraction": weighted_mean(
                late, "r30_mixed_age_fraction", "r30_normal_decision_rows"
            ),
            "long_spell_count": long_spells,
            "short_spell_count": short_spells,
            "long_spell_fraction": long_spells / spell_total if spell_total > 0.0 else None,
            "short_spell_fraction": short_spells / spell_total if spell_total > 0.0 else None,
        },
    }
    return summary, reasons


def decide(m0: bool, m1: bool, m2: bool) -> str:
    if not m0:
        return "INVALID_R39_TOY_IMPLEMENTATION"
    if not m1:
        if FIXED_PRIMITIVES and DIRECT_STATE_CONTEXT:
            return "FAIL_R39_TOY_HIGH_CREDIT"
        return "FAIL_R39_TOY_HIGH_ACCESS" if FIXED_PRIMITIVES else "NO_ACCESS_R39_TOY_32"
    if not m2:
        return "FAIL_R39_TOY_NATIVE_CATEGORICAL"
    if FIXED_PRIMITIVES and DIRECT_STATE_CONTEXT:
        return "PASS_R39_TOY_DIRECT_STATE"
    return (
        "PASS_R39_TOY_FIXED_PRIMITIVES"
        if FIXED_PRIMITIVES
        else "PASS_R39_TOY_NATIVE_CATEGORICAL"
    )


def main() -> None:
    global CONFIGS, DIRECT_STATE_CONTEXT, EXPERIMENT_ID, FIXED_PRIMITIVES
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--seed", type=int, default=39041)
    parser.add_argument("--total-timesteps", type=int, default=12_800)
    parser.add_argument("--expected-updates", type=int, default=20)
    parser.add_argument("--eval-episodes", type=int, default=32)
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    parser.add_argument("--adaptive-config", default=CONFIGS["adaptive_retention"])
    parser.add_argument("--control-config", default=CONFIGS["force_refresh"])
    parser.add_argument("--fixed-primitives", action="store_true")
    parser.add_argument("--direct-state-context", action="store_true")
    parser.add_argument("--result-name", default="r39_toy_native_categorical.json")
    args = parser.parse_args()

    EXPERIMENT_ID = str(args.experiment_id)
    CONFIGS = {
        "adaptive_retention": str(args.adaptive_config),
        "force_refresh": str(args.control_config),
    }
    FIXED_PRIMITIVES = bool(args.fixed_primitives)
    DIRECT_STATE_CONTEXT = bool(args.direct_state_context)

    run_root = Path(args.run_root).resolve()
    summaries: dict[str, dict[str, Any]] = {}
    invalid_reasons: list[str] = []
    for arm in ARMS:
        summary, reasons = summarize_arm(
            run_root / "runs" / arm / f"seed{args.seed}",
            arm=arm,
            seed=args.seed,
            total_timesteps=args.total_timesteps,
            expected_updates=args.expected_updates,
            eval_episodes=args.eval_episodes,
        )
        summaries[arm] = summary
        invalid_reasons.extend(reasons)

    adaptive_eval = summaries.get("adaptive_retention", {}).get("evaluation", {})
    control_eval = summaries.get("force_refresh", {}).get("evaluation", {})
    adaptive_temporal = summaries.get("adaptive_retention", {}).get("late_half_temporal", {})
    control_temporal = summaries.get("force_refresh", {}).get("late_half_temporal", {})
    paired_reset_match = (
        adaptive_eval.get("reset_seeds") == control_eval.get("reset_seeds")
        and len(adaptive_eval.get("reset_seeds", [])) == args.eval_episodes
    )
    if not paired_reset_match:
        add_reason(invalid_reasons, "paired evaluation reset seeds do not match")

    m0 = not invalid_reasons
    access_threshold = 0.70
    component_access_threshold = 0.65
    m1 = bool(
        m0
        and all(
            evaluation.get("r39_toy_match_score") is not None
            and evaluation["r39_toy_match_score"] >= access_threshold
            and evaluation.get("r39_toy_slow_match") is not None
            and evaluation["r39_toy_slow_match"] >= component_access_threshold
            and evaluation.get("r39_toy_fast_match") is not None
            and evaluation["r39_toy_fast_match"] >= component_access_threshold
            for evaluation in (adaptive_eval, control_eval)
        )
    )
    match_difference = None
    if (
        adaptive_eval.get("r39_toy_match_score") is not None
        and control_eval.get("r39_toy_match_score") is not None
    ):
        match_difference = (
            adaptive_eval["r39_toy_match_score"]
            - control_eval["r39_toy_match_score"]
        )
    m2 = bool(
        m1
        and control_temporal.get("full_sync_set_rate") is not None
        and abs(control_temporal["full_sync_set_rate"] - 1.0) <= 1e-6
        and adaptive_temporal.get("full_sync_set_rate") is not None
        and adaptive_temporal["full_sync_set_rate"] <= 0.75
        and adaptive_temporal.get("mixed_age_fraction") is not None
        and adaptive_temporal["mixed_age_fraction"] >= 0.25
        and adaptive_temporal.get("long_spell_count", 0.0) > 0.0
        and adaptive_temporal.get("short_spell_count", 0.0) > 0.0
        and match_difference is not None
        and match_difference >= -0.05
    )
    status = decide(m0, m1, m2)

    if status in {
        "PASS_R39_TOY_NATIVE_CATEGORICAL",
        "PASS_R39_TOY_FIXED_PRIMITIVES",
        "PASS_R39_TOY_DIRECT_STATE",
    }:
        decision = {
            "conclusion": "native categorical retention is usable on the lightweight two-timescale positive control",
            "next_action": "return to the registered current-interface fixed-k anchor before any UAV temporal comparison",
        }
    elif status == "FAIL_R39_TOY_HIGH_ACCESS":
        decision = {
            "conclusion": "the high controller did not access the dense task even with exact fixed skill primitives",
            "next_action": "diagnose high-level context or credit on the toy; do not enter S7",
        }
    elif status == "FAIL_R39_TOY_HIGH_CREDIT":
        decision = {
            "conclusion": "the high controller failed even with direct centralized state and exact fixed primitives",
            "next_action": "diagnose actor-only high credit and optimizer exposure; do not enter S7",
        }
    elif status == "NO_ACCESS_R39_TOY_32":
        decision = {
            "conclusion": "one or both tiny policies did not learn the dense role-free task",
            "next_action": "repair only toy access or capacity; do not interpret temporal efficacy",
        }
    elif status == "FAIL_R39_TOY_NATIVE_CATEGORICAL":
        decision = {
            "conclusion": "dense access passed but adaptive categorical retention did not produce safe mixed lifetimes",
            "next_action": "revise or retire this temporal action contract before S7",
        }
    else:
        decision = {
            "conclusion": "the lightweight paired run violated its implementation contract",
            "next_action": "repair the concrete wiring failure and rerun the unchanged gate",
        }

    result = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "scope": "single-seed dense synthetic temporal mechanism gate; not sparse exploration or UAV efficacy evidence",
        "seed": args.seed,
        "total_timesteps_per_arm": args.total_timesteps,
        "expected_outer_updates_per_arm": args.expected_updates,
        "evaluation_episodes_per_arm": args.eval_episodes,
        "direct_state_context": DIRECT_STATE_CONTEXT,
        "implementation_valid": m0,
        "invalid_reasons": invalid_reasons,
        "arms": summaries,
        "gates": {
            "M0_implementation": {
                "passed": m0,
                "paired_reset_match": paired_reset_match,
                "invalid_reasons": invalid_reasons,
            },
            "M1_dense_access": {
                "passed": m1,
                "final_match_score_min": access_threshold,
                "final_slow_and_fast_match_min": component_access_threshold,
            },
            "M2_temporal_semantics": {
                "passed": m2,
                "thresholds": {
                    "control_full_sync_set_rate_target": 1.0,
                    "control_full_sync_set_rate_tolerance": 1e-6,
                    "adaptive_full_sync_set_rate_max": 0.75,
                    "adaptive_mixed_age_fraction_min": 0.25,
                    "adaptive_short_and_long_spell_count_strict_min": 0,
                    "adaptive_minus_control_match_score_min": -0.05,
                },
                "adaptive_minus_control_match_score": match_difference,
            },
        },
        "decision": {"status": status, **decision},
    }
    output = run_root / "result" / str(args.result_name)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False), encoding="utf-8"
    )
    temporary.replace(output)
    print(output)


if __name__ == "__main__":
    main()
