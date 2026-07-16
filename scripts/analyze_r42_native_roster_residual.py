"""Apply the registered paired R42-IRR Alice--Bob gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r42-irr-native-roster-residual"
MODES = ("fixed_refresh", "incumbent_roster_residual")
SEED = 42_041
ENV_STEPS = 320_000
OUTER_UPDATES = 200
OPTIMIZER_STEPS = 3_000
EVAL_EPISODES = 100
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 62_042


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def bootstrap_mean(values: np.ndarray, seed_offset: int) -> dict[str, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    draws = rng.integers(
        0,
        values.size,
        size=(BOOTSTRAP_REPETITIONS, values.size),
    )
    means = values[draws].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "lower_95": float(np.quantile(means, 0.025)),
        "upper_95": float(np.quantile(means, 0.975)),
    }


def event_summary(evaluation: dict[str, Any]) -> dict[str, Any]:
    rows = evaluation.get("renewal_events", [])
    changes = np.asarray([row["changes"] for row in rows], dtype=np.int64)
    if changes.shape != (EVAL_EPISODES, 2):
        raise ValueError(f"renewal event shape is {changes.shape}, expected (100, 2)")
    post_rosters = np.asarray([row["post_roster"] for row in rows], dtype=np.int64)
    discordant = np.asarray([row["discordant"] for row in rows], dtype=np.float64)
    full_sync = np.asarray([row["full_sync_set"] for row in rows], dtype=np.float64)
    skill_counts = np.zeros(4, dtype=np.int64)
    for row_changes, post in zip(changes, post_rosters):
        for agent_index in range(2):
            if row_changes[agent_index]:
                skill_counts[post[agent_index]] += 1
    total_set = int(skill_counts.sum())
    if total_set:
        probabilities = skill_counts[skill_counts > 0] / total_set
        normalized_entropy = float(
            -(probabilities * np.log(probabilities)).sum() / math.log(4)
        )
    else:
        normalized_entropy = 0.0
    set_rates = changes.mean(axis=0)
    keep_rates = 1.0 - set_rates
    return {
        "rows": len(rows),
        "discordant_rows": discordant.astype(int).tolist(),
        "discordant_rate": float(discordant.mean()),
        "full_sync_set_rate": float(full_sync.mean()),
        "agent_set_rates": set_rates.tolist(),
        "agent_keep_rates": keep_rates.tolist(),
        "minimum_keep_set_marginal": float(
            min(set_rates.min(), keep_rates.min())
        ),
        "set_skill_counts": skill_counts.tolist(),
        "set_skill_entropy_normalized": normalized_entropy,
    }


def validate_arm(result: dict[str, Any], mode: str) -> list[str]:
    reasons: list[str] = []
    prefix = f"{mode}: "
    if result.get("experiment_id") != EXPERIMENT_ID:
        reasons.append(prefix + "experiment id mismatch")
    if result.get("state") != "completed" or result.get("mode") != mode:
        reasons.append(prefix + "arm is not completed under the expected mode")
    if result.get("seed") != SEED:
        reasons.append(prefix + "seed mismatch")
    source = result.get("source", {})
    for boundary in ("before", "after"):
        identity = source.get(boundary, {})
        if identity.get("archive_repo_relative") != "ref/hmasd.tar":
            reasons.append(prefix + f"source {boundary} archive mismatch")
        if identity.get("archive_present") is not True:
            reasons.append(prefix + f"source {boundary} archive missing")
        if identity.get("required_entry_present") is not True:
            reasons.append(prefix + f"source {boundary} entry missing")
    if source.get("fresh_extract") is not True:
        reasons.append(prefix + "source tree was not freshly extracted")
    source_checkpoint = source.get("checkpoint", {})
    if source_checkpoint.get("schema") != "r41_official_hmasd_complete_checkpoint_v1":
        reasons.append(prefix + "source checkpoint schema mismatch")
    if source_checkpoint.get("seed") != 1 or source_checkpoint.get("outer_updates") != 937:
        reasons.append(prefix + "source checkpoint is not the R41B final boundary")

    arguments = result.get("official_arguments", {})
    expected_arguments = {
        "num_env_steps": ENV_STEPS,
        "episode_length": 100,
        "n_rollout_threads": 16,
        "n_eval_rollout_threads": 1,
        "n_training_threads": 8,
        "skill_interval": 50,
        "team_skill_dim": 2,
        "indi_skill_dim": 4,
        "use_recurrent_discri": 0,
        "h_ppo_epoch": 15,
        "h_num_mini_batch": 1,
        "l_ppo_epoch": 15,
        "l_num_mini_batch": 1,
        "use_eval": False,
        "model_dir": None,
    }
    for field, expected in expected_arguments.items():
        if arguments.get(field) != expected:
            reasons.append(
                prefix
                + f"argument {field}={arguments.get(field)!r}, expected {expected!r}"
            )
    environment = result.get("environment", {})
    for field, expected in {
        "agents": 2,
        "obs": 11,
        "state": 100,
        "actions": 5,
        "horizon": 100,
    }.items():
        if environment.get(field) != expected:
            reasons.append(prefix + f"environment {field} mismatch")

    boundary = result.get("algorithm_boundary", {})
    expected_boundary = {
        "source_algorithm": "official_hmasd_native_k50_continuation",
        "mode": mode,
        "high_reward": "environment_reward_only",
        "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
        "extra_shaping": False,
        "extra_intrinsic": False,
        "task_fields_in_residual": False,
        "age_in_residual": False,
        "new_duration_action": False,
        "independent_keep_head": False,
        "team_z_resampled_each_native_check": True,
        "incumbent_roster_teacher_forced": True,
        "fresh_initialization": False,
    }
    for field, expected in expected_boundary.items():
        if boundary.get(field) != expected:
            reasons.append(prefix + f"algorithm boundary {field} mismatch")

    parity = result.get("parity", {})
    for field in (
        "sample_action_max_abs_error",
        "sample_logp_max_abs_error",
        "sample_value_max_abs_error",
        "replay_logp_max_abs_error",
        "replay_value_max_abs_error",
        "entropy_abs_error",
        "base_gradient_max_abs_error",
    ):
        try:
            value = float(parity[field])
        except (KeyError, TypeError, ValueError):
            reasons.append(prefix + f"parity field {field} missing")
            continue
        if not math.isfinite(value) or value > 1e-6:
            reasons.append(prefix + f"parity field {field}={value} exceeds 1e-6")
    try:
        residual_gradient = float(parity["residual_gradient_norm"])
    except (KeyError, TypeError, ValueError):
        residual_gradient = 0.0
    if not math.isfinite(residual_gradient) or residual_gradient <= 0.0:
        reasons.append(prefix + "residual has no finite direct gradient")
    if parity.get("residual_parameter_count") != 548:
        reasons.append(prefix + "residual parameter count mismatch")
    if parity.get("rng_restored") is not True:
        reasons.append(prefix + "parity check changed the RNG stream")
    expected_scale = 0.0 if mode == "fixed_refresh" else 1.0
    if parity.get("active_scale") != expected_scale:
        reasons.append(prefix + "residual mode scale mismatch")
    if result.get("initial_residual_zero_output") is not True:
        reasons.append(prefix + "residual was not zero-output at migration")

    telemetry = result.get("telemetry", {})
    if telemetry.get("outer_updates") != OUTER_UPDATES:
        reasons.append(prefix + "outer-update count mismatch")
    if telemetry.get("actual_env_steps") != ENV_STEPS:
        reasons.append(prefix + "environment-step count mismatch")
    for optimizer_name in (
        "high",
        "low_actor",
        "low_critic",
        "team_discriminator",
        "individual_discriminator",
    ):
        stats = telemetry.get("optimizers", {}).get(optimizer_name, {})
        if stats.get("steps") != OPTIMIZER_STEPS:
            reasons.append(prefix + f"{optimizer_name} optimizer count mismatch")
        if stats.get("all_checked_gradients_finite") is not True:
            reasons.append(prefix + f"{optimizer_name} gradients were invalid")
        if stats.get("ever_nonzero_gradient") is not True:
            reasons.append(prefix + f"{optimizer_name} never had a nonzero gradient")
    replay = telemetry.get("replay") or {}
    for field in (
        "high_max_abs_logp_error",
        "low_max_abs_logp_error",
        "global_max_abs_logp_error",
    ):
        try:
            value = float(replay[field])
        except (KeyError, TypeError, ValueError):
            reasons.append(prefix + f"replay field {field} missing")
            continue
        if not math.isfinite(value) or value > 1e-6:
            reasons.append(prefix + f"replay field {field}={value} exceeds 1e-6")

    drift = result.get("residual_drift", {})
    try:
        max_drift = float(drift["max_abs"])
        relative_drift = float(drift["relative_l2"])
    except (KeyError, TypeError, ValueError):
        max_drift = math.inf
        relative_drift = 0.0
    if mode == "fixed_refresh" and max_drift > 1e-12:
        reasons.append(prefix + "disabled residual drifted")
    if mode == "incumbent_roster_residual" and (
        not math.isfinite(relative_drift) or relative_drift <= 1e-6
    ):
        reasons.append(prefix + "treatment residual did not update")

    checkpoint = result.get("checkpoint", {})
    if checkpoint.get("schema") != "r42_native_roster_residual_checkpoint_v1":
        reasons.append(prefix + "final checkpoint schema mismatch")
    if checkpoint.get("outer_updates") != OUTER_UPDATES:
        reasons.append(prefix + "final checkpoint update mismatch")
    if checkpoint.get("finite") is not True:
        reasons.append(prefix + "final checkpoint is non-finite")
    checkpoint_path = checkpoint.get("path")
    if not checkpoint_path or not Path(checkpoint_path).is_file():
        reasons.append(prefix + "final checkpoint file missing")

    evaluation = result.get("evaluation", {})
    if evaluation.get("evaluator") != "r42_deterministic_alice_bob_with_native_roster":
        reasons.append(prefix + "evaluator mismatch")
    if evaluation.get("episodes") != EVAL_EPISODES:
        reasons.append(prefix + "evaluation episode count mismatch")
    if len(evaluation.get("episode_wins", [])) != EVAL_EPISODES:
        reasons.append(prefix + "evaluation win rows missing")
    if len(evaluation.get("renewal_events", [])) != EVAL_EPISODES:
        reasons.append(prefix + "one-renewal rows missing")
    return reasons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    result_root = run_root / "result"
    result_root.mkdir(parents=True, exist_ok=True)
    arm_results: dict[str, dict[str, Any]] = {}
    invalid_reasons: list[str] = []
    for mode in MODES:
        path = run_root / "arms" / mode / "seed_result.json"
        if not path.is_file():
            invalid_reasons.append(f"{mode}: seed result missing")
            continue
        result = load_json(path)
        arm_results[mode] = result
        invalid_reasons.extend(validate_arm(result, mode))

    complete = len(arm_results) == 2
    if complete:
        fixed_eval = arm_results["fixed_refresh"]["evaluation"]
        treatment_eval = arm_results["incumbent_roster_residual"]["evaluation"]
        if fixed_eval.get("reset_stream") != treatment_eval.get("reset_stream"):
            invalid_reasons.append("paired evaluation reset streams differ")
        fixed_events = event_summary(fixed_eval)
        treatment_events = event_summary(treatment_eval)
        service_delta = np.asarray(
            treatment_eval["episode_wins"], dtype=np.float64
        ) - np.asarray(fixed_eval["episode_wins"], dtype=np.float64)
        service_ci = bootstrap_mean(service_delta, 0)
        discordant_delta = np.asarray(
            treatment_events["discordant_rows"], dtype=np.float64
        ) - np.asarray(fixed_events["discordant_rows"], dtype=np.float64)
        discordant_ci = bootstrap_mean(discordant_delta, 1)
    else:
        fixed_eval = {}
        treatment_eval = {}
        fixed_events = {}
        treatment_events = {}
        service_ci = {"mean": None, "lower_95": None, "upper_95": None}
        discordant_ci = {"mean": None, "lower_95": None, "upper_95": None}

    m0 = complete and not invalid_reasons
    m1 = bool(
        m0
        and float(fixed_eval["win_rate"]) >= 0.80
        and float(fixed_eval["key0_rate"]) >= 0.85
        and float(fixed_eval["key1_rate"]) >= 0.85
    )
    m2 = bool(
        m1
        and service_ci["lower_95"] is not None
        and service_ci["lower_95"] > -0.10
    )
    m3 = bool(
        m2
        and treatment_events["discordant_rate"] >= 0.20
        and discordant_ci["lower_95"] is not None
        and discordant_ci["lower_95"] > 0.0
        and treatment_events["full_sync_set_rate"] < 0.50
        and treatment_events["minimum_keep_set_marginal"] >= 0.05
        and treatment_events["set_skill_entropy_normalized"] > 0.80
    )

    if not m0:
        status = "INVALID_R42_IRR_IMPLEMENTATION"
        next_action = "repair only the concrete sampling, replay, checkpoint, counter, or evaluator defect"
    elif not m1:
        status = "INVALID_R42_FIXED_ANCHOR_LOST"
        next_action = "restore the R41B continuation contract; do not interpret the residual"
    elif not m2:
        status = "VALID_FAIL_R42_IRR_SERVICE"
        next_action = "retire the direct native k50 incumbent-roster residual"
    elif not m3:
        status = "VALID_FAIL_R42_IRR_NO_DECOUPLING"
        next_action = "retire this residual as a temporal mechanism; preserve fixed HMASD"
    else:
        status = "PASS_R42_IRR_K50"
        next_action = "register one paired multi-seed verification before any S7 or variable-N promotion"

    result = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": m0,
        "contract": {
            "seed": SEED,
            "arms": list(MODES),
            "rollout_envs_per_arm": 16,
            "concurrent_rollout_envs": 32,
            "environment_steps_per_arm": ENV_STEPS,
            "outer_updates_per_arm": OUTER_UPDATES,
            "optimizer_steps_per_path_per_arm": OPTIMIZER_STEPS,
            "native_check_interval": 50,
            "evaluation_episodes_per_arm": EVAL_EPISODES,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "gates": {
            "M0": {"passed": m0, "invalid_reasons": invalid_reasons},
            "M1_fixed_anchor": {
                "passed": m1,
                "win_rate": fixed_eval.get("win_rate"),
                "win_floor": 0.80,
                "key0_rate": fixed_eval.get("key0_rate"),
                "key1_rate": fixed_eval.get("key1_rate"),
                "key_floor": 0.85,
            },
            "M2_service_noninferiority": {
                "passed": m2,
                "treatment_minus_fixed_win_ci": service_ci,
                "strict_lower_margin": -0.10,
            },
            "M3_temporal_decoupling": {
                "passed": m3,
                "fixed": fixed_events,
                "treatment": treatment_events,
                "treatment_minus_fixed_discordant_ci": discordant_ci,
                "discordant_rate_floor": 0.20,
                "full_sync_set_ceiling": 0.50,
                "minimum_keep_set_marginal_floor": 0.05,
                "set_skill_entropy_strict_floor": 0.80,
            },
        },
        "next_action": next_action,
    }
    output_path = result_root / "r42_irr_native_roster_residual.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
