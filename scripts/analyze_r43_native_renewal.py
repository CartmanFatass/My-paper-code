"""Apply the registered reset-censored R43-NRC Alice--Bob gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r43-nrc-k50"
MODES = ("fixed_refresh", "r43_nrc")
SEED = 43_041
ENV_STEPS = 320_000
OUTER_UPDATES = 200
CHECK_ROWS = 6_400
GLOBAL_CHECK_CALLS = 400
NORMAL_CHECK_ROWS = 6_384
OPTIMIZER_STEPS = 3_000
EVAL_EPISODES = 100
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 62_043


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def bootstrap_mean(values: np.ndarray, seed_offset: int) -> dict[str, float]:
    rng = np.random.default_rng(BOOTSTRAP_SEED + seed_offset)
    draws = rng.integers(0, values.size, size=(BOOTSTRAP_REPETITIONS, values.size))
    means = values[draws].mean(axis=1)
    return {
        "mean": float(values.mean()),
        "lower_95": float(np.quantile(means, 0.025)),
        "upper_95": float(np.quantile(means, 0.975)),
    }


def event_summary(evaluation: dict[str, Any]) -> dict[str, Any]:
    rows = evaluation.get("renewal_events", [])
    if len(rows) != EVAL_EPISODES:
        raise ValueError(f"renewal event rows={len(rows)}, expected {EVAL_EPISODES}")
    eligible = np.asarray([bool(row.get("eligible")) for row in rows], dtype=bool)
    tokens = np.asarray([row.get("renew_token", [0, 0]) for row in rows], dtype=np.int64)
    if tokens.shape != (EVAL_EPISODES, 2):
        raise ValueError(f"renewal token shape is {tokens.shape}, expected (100, 2)")
    discordant_episode = np.asarray(
        [int(row.get("discordant", 0)) for row in rows], dtype=np.float64
    )
    full_sync_episode = np.asarray(
        [int(row.get("full_sync_renew", 0)) for row in rows], dtype=np.float64
    )
    eligible_tokens = tokens[eligible]
    if eligible_tokens.size:
        renew_rates = (eligible_tokens == 1).mean(axis=0)
        keep_rates = 1.0 - renew_rates
        discordant_rate = float(discordant_episode[eligible].mean())
        full_sync_rate = float(full_sync_episode[eligible].mean())
    else:
        renew_rates = np.zeros(2, dtype=np.float64)
        keep_rates = np.zeros(2, dtype=np.float64)
        discordant_rate = 0.0
        full_sync_rate = 0.0
    skill_counts = np.zeros(4, dtype=np.int64)
    same_label = 0
    for row, row_tokens in zip(rows, tokens):
        if not row.get("eligible"):
            continue
        pre = np.asarray(row["pre_roster"], dtype=np.int64)
        post = np.asarray(row["post_roster"], dtype=np.int64)
        for agent_index in range(2):
            if row_tokens[agent_index] == 1:
                skill_counts[post[agent_index]] += 1
                same_label += int(post[agent_index] == pre[agent_index])
    total_renew = int(skill_counts.sum())
    if total_renew:
        probabilities = skill_counts[skill_counts > 0] / total_renew
        entropy = float(
            -(probabilities * np.log(probabilities)).sum() / math.log(4)
        )
    else:
        entropy = 0.0
    return {
        "episode_rows": len(rows),
        "eligible_rows": int(eligible.sum()),
        "discordant_episode_rows": discordant_episode.astype(int).tolist(),
        "discordant_rate": discordant_rate,
        "full_sync_renew_rate": full_sync_rate,
        "agent_renew_rates": renew_rates.tolist(),
        "agent_keep_rates": keep_rates.tolist(),
        "minimum_keep_renew_marginal": float(
            min(renew_rates.min(), keep_rates.min())
        ),
        "renew_skill_counts": skill_counts.tolist(),
        "renew_skill_entropy_normalized": entropy,
        "same_label_renew": same_label,
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
    checkpoint_source = source.get("checkpoint", {})
    if checkpoint_source.get("schema") != "r41_official_hmasd_complete_checkpoint_v1":
        reasons.append(prefix + "source checkpoint schema mismatch")
    if checkpoint_source.get("seed") != 1 or checkpoint_source.get("outer_updates") != 937:
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
        "controller_clock": "source_global_k50_reset_censored",
        "high_reward": "environment_reward_only",
        "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
        "extra_shaping": False,
        "extra_intrinsic": False,
        "task_fields_in_controller": False,
        "team_z_source_path_unchanged": True,
        "auto_reset_high_action": False,
        "assignment_spell_crosses_reset": True,
        "execution_fragment_censored_at_reset": True,
        "conditional_same_label_masked": mode == "r43_nrc",
        "single_combined_high_optimizer": True,
        "fresh_initialization": False,
    }
    for field, expected in expected_boundary.items():
        if boundary.get(field) != expected:
            reasons.append(prefix + f"algorithm boundary {field} mismatch")

    installation = result.get("installation", {})
    if installation.get("controller_clock") != "source_global_k50_reset_censored":
        reasons.append(prefix + "installation clock mismatch")
    if installation.get("task_specific_inputs") is not False:
        reasons.append(prefix + "task-specific controller input detected")
    if installation.get("intrinsic_reward_changed") is not False:
        reasons.append(prefix + "intrinsic reward changed")
    if installation.get("new_modules_frozen") is not (mode == "fixed_refresh"):
        reasons.append(prefix + "new-module freeze mode mismatch")
    parity = installation.get("zero_init_probability", {})
    for field in (
        "maximum_logp_error",
        "maximum_probability_error",
        "maximum_probability_sum_error",
    ):
        try:
            value = float(parity[field])
        except (KeyError, TypeError, ValueError):
            reasons.append(prefix + f"zero-init parity field {field} missing")
            continue
        if not math.isfinite(value) or value > 1e-6:
            reasons.append(prefix + f"zero-init parity {field}={value} exceeds 1e-6")
    for field, value in installation.get("direct_gradients", {}).items():
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        if not math.isfinite(numeric) or numeric <= 0.0:
            reasons.append(prefix + f"direct gradient {field} is not positive")

    telemetry = result.get("telemetry", {})
    if telemetry.get("outer_updates") != OUTER_UPDATES:
        reasons.append(prefix + "outer-update count mismatch")
    if telemetry.get("actual_env_steps") != ENV_STEPS:
        reasons.append(prefix + "environment-step count mismatch")
    if telemetry.get("high_replay_updates_checked") != OUTER_UPDATES:
        reasons.append(prefix + "not every on-policy high buffer was replay checked")
    if telemetry.get("low_replay_updates_checked") != 1:
        reasons.append(prefix + "low replay was not checked exactly once")
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
        "factor_max_abs_logp_error",
        "high_max_abs_value_error",
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
    if replay.get("prefix_mismatch_count") != 0.0:
        reasons.append(prefix + "teacher-forced working prefix mismatch")

    clock = result.get("training_clock", {})
    expected_counts = {
        "global_check_calls": GLOBAL_CHECK_CALLS,
        "env_check_rows": CHECK_ROWS,
        "structural_env_assignments": 16,
        "normal_env_checks": NORMAL_CHECK_ROWS,
        "auto_reset_high_actions": 0,
        "auto_reset_roster_violations": 0,
        "auto_reset_team_violations": 0,
        "low_actor_hidden_reset_violations": 0,
        "low_critic_hidden_reset_violations": 0,
        "assignment_spell_reset_closures": 0,
        "continuation_actor_valid_count": 0,
    }
    for field, expected in expected_counts.items():
        if clock.get(field) != expected:
            reasons.append(prefix + f"clock {field}={clock.get(field)!r}, expected {expected}")
    if int(clock.get("auto_resets", 0)) <= 0:
        reasons.append(prefix + "no auto-reset was observed")
    if clock.get("execution_fragments_env_reset_censored") != clock.get("auto_resets"):
        reasons.append(prefix + "auto-reset fragment count mismatch")
    if mode == "r43_nrc":
        if clock.get("auto_reset_age_violations") != 0:
            reasons.append(prefix + "commitment age changed incorrectly at reset")
        if clock.get("update_policy_truncations") != CHECK_ROWS:
            reasons.append(prefix + "update-boundary policy truncation count mismatch")
        if clock.get("continuation_critic_only_states") != CHECK_ROWS:
            reasons.append(prefix + "critic-only continuation count mismatch")
        if clock.get("same_label_renew") != 0:
            reasons.append(prefix + "same-label renewal occurred")
        if float(clock.get("zero_init_source_equivalence_max", math.inf)) > 1e-6:
            reasons.append(prefix + "actual-check zero-init source equivalence failed")
        if int(clock.get("early_reset_blocks", 0)) <= 0:
            reasons.append(prefix + "no early reset block exercised reset-censored credit")
        if int(clock.get("early_reset_reward_blocks", 0)) <= 0:
            reasons.append(prefix + "early reset reward was not observed in its block")
        if int(clock.get("post_reset_steps_in_same_block", 0)) <= 0:
            reasons.append(prefix + "no post-reset primitive step remained in the same block")
        gradients = result.get("gradient_stats") or {}
        for field in (
            "renewal_actor_nonzero_steps",
            "renewal_critic_nonzero_steps",
            "skill_event_critic_nonzero_steps",
        ):
            if int(gradients.get(field, 0)) <= 0:
                reasons.append(prefix + f"new gradient path {field} never activated")
        if gradients.get("maximum_prefix_mismatch") != 0:
            reasons.append(prefix + "trainer prefix mismatch")

    drift = result.get("module_drift", {})
    for module_name in (
        "r43_renewal_actor",
        "r43_renewal_critic",
        "r43_skill_event_critic",
    ):
        module = drift.get(module_name, {})
        try:
            max_abs = float(module["max_abs"])
            relative = float(module["relative_l2"])
        except (KeyError, TypeError, ValueError):
            max_abs = math.inf
            relative = 0.0
        if mode == "fixed_refresh" and max_abs > 1e-12:
            reasons.append(prefix + f"frozen {module_name} drifted")
        if mode == "r43_nrc" and (
            not math.isfinite(relative) or relative <= 1e-6
        ):
            reasons.append(prefix + f"treatment {module_name} did not update")

    checkpoint = result.get("checkpoint", {})
    if checkpoint.get("schema") != "r43_native_renewal_checkpoint_v1":
        reasons.append(prefix + "final checkpoint schema mismatch")
    if checkpoint.get("outer_updates") != OUTER_UPDATES:
        reasons.append(prefix + "final checkpoint update mismatch")
    if checkpoint.get("finite") is not True:
        reasons.append(prefix + "final checkpoint is non-finite")
    if checkpoint.get("components", {}).get("controller_carry") is not True:
        reasons.append(prefix + "controller carry missing from checkpoint")
    checkpoint_path = checkpoint.get("path")
    if not checkpoint_path or not Path(checkpoint_path).is_file():
        reasons.append(prefix + "final checkpoint file missing")

    evaluation = result.get("evaluation", {})
    if evaluation.get("evaluator") != "r43_deterministic_alice_bob_reset_aligned_episode":
        reasons.append(prefix + "evaluator mismatch")
    if evaluation.get("episodes") != EVAL_EPISODES:
        reasons.append(prefix + "evaluation episode count mismatch")
    if len(evaluation.get("episode_wins", [])) != EVAL_EPISODES:
        reasons.append(prefix + "evaluation win rows missing")
    if len(evaluation.get("renewal_events", [])) != EVAL_EPISODES:
        reasons.append(prefix + "evaluation renewal rows missing")
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
        try:
            fixed_eval = arm_results["fixed_refresh"]["evaluation"]
            treatment_eval = arm_results["r43_nrc"]["evaluation"]
            if fixed_eval.get("reset_stream") != treatment_eval.get("reset_stream"):
                invalid_reasons.append("paired evaluation reset streams differ")
            fixed_events = event_summary(fixed_eval)
            treatment_events = event_summary(treatment_eval)
            service_delta = np.asarray(
                treatment_eval["episode_wins"], dtype=np.float64
            ) - np.asarray(fixed_eval["episode_wins"], dtype=np.float64)
            service_ci = bootstrap_mean(service_delta, 0)
            discordant_delta = np.asarray(
                treatment_events["discordant_episode_rows"], dtype=np.float64
            ) - np.asarray(
                fixed_events["discordant_episode_rows"], dtype=np.float64
            )
            discordant_ci = bootstrap_mean(discordant_delta, 1)
        except (KeyError, TypeError, ValueError) as exc:
            invalid_reasons.append(f"paired analysis failed: {exc}")
            fixed_eval = arm_results["fixed_refresh"].get("evaluation", {})
            treatment_eval = arm_results["r43_nrc"].get("evaluation", {})
            fixed_events = {}
            treatment_events = {}
            service_ci = {"mean": None, "lower_95": None, "upper_95": None}
            discordant_ci = {"mean": None, "lower_95": None, "upper_95": None}
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
        m1
        and treatment_events["discordant_rate"] >= 0.20
        and discordant_ci["lower_95"] is not None
        and discordant_ci["lower_95"] > 0.0
        and treatment_events["full_sync_renew_rate"] < 0.50
        and treatment_events["minimum_keep_renew_marginal"] >= 0.05
        and treatment_events["renew_skill_entropy_normalized"] > 0.80
        and treatment_events["same_label_renew"] == 0
    )

    if not m0:
        status = "INVALID_R43_NRC_CLOCK_OR_IMPLEMENTATION"
        next_action = "repair only the located clock, mask, replay, buffer, bootstrap, or count defect"
    elif not m1:
        status = "INVALID_R43_FIXED_ANCHOR_LOST"
        next_action = "restore the exact R41B source continuation"
    elif not m2 or not m3:
        status = "VALID_FAIL_R43_NRC"
        next_action = "permanently retire the Alice--Bob k50 reset-censored native renewal route without rescue"
    else:
        status = "PASS_R43_NRC_K50"
        next_action = "register only the unchanged paired multi-seed Alice--Bob verification"

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
            "env_check_rows_per_arm": CHECK_ROWS,
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
                "treatment_minus_fixed_discordance_ci": discordant_ci,
                "discordant_floor": 0.20,
                "discordance_strict_lower_floor": 0.0,
                "full_sync_renew_ceiling": 0.50,
                "minimum_keep_renew_marginal_floor": 0.05,
                "renew_target_entropy_strict_floor": 0.80,
                "same_label_renew_required": 0,
            },
        },
        "arms": arm_results,
        "next_action": next_action,
    }
    output_path = result_root / "r43_native_renewal.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"R43 status={status}; result={output_path}")


if __name__ == "__main__":
    main()
