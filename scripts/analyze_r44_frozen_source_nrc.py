"""Apply the registered R44 frozen-source native-renewal gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r44-fsnrc-k50"
MODES = ("frozen_source_nrc0", "frozen_source_nrc")
CONTROL, TREATMENT = MODES
SEED = 43_041
ENV_STEPS = 320_000
OUTER_UPDATES = 200
CHECK_ROWS = 6_400
GLOBAL_CHECK_CALLS = 400
NORMAL_CHECK_ROWS = 6_384
FACTOR_STEPS = 3_000
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
    discordant_rows = np.asarray(
        [int(row.get("discordant", 0)) for row in rows], dtype=np.float64
    )
    full_sync_rows = np.asarray(
        [int(row.get("full_sync_renew", 0)) for row in rows], dtype=np.float64
    )
    eligible_tokens = tokens[eligible]
    if eligible_tokens.size:
        renew_rates = (eligible_tokens == 1).mean(axis=0)
        keep_rates = 1.0 - renew_rates
        discordant_rate = float(discordant_rows[eligible].mean())
        full_sync_rate = float(full_sync_rows[eligible].mean())
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
        entropy = float(-(probabilities * np.log(probabilities)).sum() / math.log(4))
    else:
        entropy = 0.0
    return {
        "episode_rows": len(rows),
        "eligible_rows": int(eligible.sum()),
        "discordant_episode_rows": discordant_rows.astype(int).tolist(),
        "discordant_rate": discordant_rate,
        "full_sync_renew_rate": full_sync_rate,
        "agent_renew_rates": renew_rates.tolist(),
        "agent_keep_rates": keep_rates.tolist(),
        "minimum_keep_renew_marginal": float(min(renew_rates.min(), keep_rates.min())),
        "renew_skill_counts": skill_counts.tolist(),
        "renew_skill_entropy_normalized": entropy,
        "same_label_renew": same_label,
    }


def _finite_at_most(value: Any, ceiling: float) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric <= ceiling


def validate_arm(result: dict[str, Any], mode: str) -> list[str]:
    reasons: list[str] = []
    prefix = f"{mode}: "
    if result.get("experiment_id") != EXPERIMENT_ID:
        reasons.append(prefix + "experiment id mismatch")
    if result.get("state") != "completed" or result.get("scope") != "formal":
        reasons.append(prefix + "arm is not a completed formal run")
    if result.get("mode") != mode or result.get("seed") != SEED:
        reasons.append(prefix + "mode or seed mismatch")

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
        reasons.append(prefix + "source checkpoint is not R41B exact-final")

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
            reasons.append(prefix + f"argument {field} mismatch")
    for field, expected in {
        "agents": 2,
        "obs": 11,
        "state": 100,
        "actions": 5,
        "horizon": 100,
    }.items():
        if result.get("environment", {}).get(field) != expected:
            reasons.append(prefix + f"environment {field} mismatch")

    boundary = result.get("algorithm_boundary", {})
    expected_boundary = {
        "source_algorithm": "frozen_r41b_hmasd_skill_system",
        "mode": mode,
        "controller_clock": "source_global_k50_reset_censored",
        "renewal_return": "next_50_external_reward_steps_reset_censored",
        "conditional_skill": "frozen_source_non_incumbent_distribution",
        "low_executor": "frozen_r41b_low_actor",
        "source_optimizer_updates": False,
        "renewal_actor_enabled": mode == TREATMENT,
        "renewal_entropy": False,
        "extra_shaping": False,
        "extra_intrinsic": False,
        "task_fields_in_controller": False,
        "discriminators_read_only": True,
        "auto_reset_high_action": False,
        "assignment_spell_crosses_reset": True,
        "execution_fragment_censored_at_reset": True,
        "fresh_initialization": False,
    }
    for field, expected in expected_boundary.items():
        if boundary.get(field) != expected:
            reasons.append(prefix + f"algorithm boundary {field} mismatch")
    if boundary.get("factor_optimizer_modules") != ["renewal_actor", "renewal_critic"]:
        reasons.append(prefix + "factor optimizer scope mismatch")

    installation = result.get("installation", {})
    for field, expected in {
        "mode": mode,
        "source_parameters_frozen": True,
        "renewal_actor_trainable": mode == TREATMENT,
        "renewal_critic_trainable": True,
        "conditional_skill_trainable": False,
        "renewal_entropy": False,
        "task_specific_inputs": False,
        "reward_shaping": False,
        "intrinsic_reward_changed": False,
        "factor_optimizer_class": "Adam",
    }.items():
        if installation.get(field) != expected:
            reasons.append(prefix + f"installation {field} mismatch")
    parity = installation.get("zero_init_probability", {})
    for field in (
        "maximum_logp_error",
        "maximum_probability_error",
        "maximum_probability_sum_error",
    ):
        if not _finite_at_most(parity.get(field), 1e-6):
            reasons.append(prefix + f"zero-init parity {field} exceeds 1e-6")

    frozen = result.get("source_frozen_drift", {})
    if frozen.get("exact") is not True:
        reasons.append(prefix + "source state was not exactly frozen")
    if not _finite_at_most(frozen.get("global_max_abs"), 1e-12):
        reasons.append(prefix + "source state drift exceeds 1e-12")

    telemetry = result.get("telemetry", {})
    if telemetry.get("outer_updates") != OUTER_UPDATES:
        reasons.append(prefix + "outer-update count mismatch")
    if telemetry.get("actual_env_steps") != ENV_STEPS:
        reasons.append(prefix + "environment-step count mismatch")
    if telemetry.get("high_replay_updates_checked") != OUTER_UPDATES:
        reasons.append(prefix + "not every high buffer was replay checked")
    if telemetry.get("low_replay_updates_checked") != 1:
        reasons.append(prefix + "low replay was not checked once")
    for name in (
        "high",
        "low_actor",
        "low_critic",
        "team_discriminator",
        "individual_discriminator",
    ):
        if telemetry.get("source_optimizers", {}).get(name, {}).get("steps") != 0:
            reasons.append(prefix + f"source optimizer {name} stepped")
    factor_optimizer = telemetry.get("factor_optimizer", {})
    if factor_optimizer.get("steps") != FACTOR_STEPS:
        reasons.append(prefix + "factor optimizer count mismatch")
    if factor_optimizer.get("all_checked_gradients_finite") is not True:
        reasons.append(prefix + "factor optimizer gradient was non-finite")
    if factor_optimizer.get("ever_nonzero_gradient") is not True:
        reasons.append(prefix + "factor optimizer never received a gradient")
    replay = telemetry.get("replay") or {}
    for field in (
        "high_max_abs_logp_error",
        "factor_max_abs_logp_error",
        "low_max_abs_logp_error",
        "global_max_abs_logp_error",
    ):
        if not _finite_at_most(replay.get(field), 1e-6):
            reasons.append(prefix + f"replay {field} exceeds 1e-6")
    if replay.get("prefix_mismatch_count") != 0.0:
        reasons.append(prefix + "teacher-forced working prefix mismatch")
    if not _finite_at_most(telemetry.get("conditional_skill_ratio_max_deviation"), 1e-6):
        reasons.append(prefix + "conditional skill ratio deviates from one")

    gradients = result.get("factor_gradient_stats", {})
    for field in ("steps", "actor_gradient_checks", "critic_gradient_checks"):
        if gradients.get(field) != FACTOR_STEPS:
            reasons.append(prefix + f"factor gradient field {field} mismatch")
    if gradients.get("actor_all_gradients_finite") is not True:
        reasons.append(prefix + "renewal actor gradient was non-finite")
    if gradients.get("critic_all_gradients_finite") is not True:
        reasons.append(prefix + "renewal critic gradient was non-finite")
    if gradients.get("critic_nonzero_steps") != FACTOR_STEPS:
        reasons.append(prefix + "renewal critic lacked nonzero gradient exposure")
    expected_actor_steps = FACTOR_STEPS if mode == TREATMENT else 0
    if gradients.get("actor_nonzero_steps") != expected_actor_steps:
        reasons.append(prefix + "renewal actor gradient exposure mismatch")
    if gradients.get("source_gradient_tensors") != 0:
        reasons.append(prefix + "source tensor received a gradient")
    if gradients.get("maximum_prefix_mismatch") != 0:
        reasons.append(prefix + "trainer working-prefix mismatch")

    drift = result.get("factor_drift", {})
    actor_drift = drift.get("r43_renewal_actor", {})
    critic_drift = drift.get("r43_renewal_critic", {})
    if mode == CONTROL:
        if not _finite_at_most(actor_drift.get("max_abs"), 1e-12):
            reasons.append(prefix + "inactive renewal actor drifted")
    else:
        try:
            relative = float(actor_drift.get("relative_l2"))
        except (TypeError, ValueError):
            relative = 0.0
        if not math.isfinite(relative) or relative <= 1e-6:
            reasons.append(prefix + "treatment renewal actor did not move")
    if not _finite_at_most(critic_drift.get("max_abs"), math.inf):
        reasons.append(prefix + "renewal critic drift is non-finite")
    if float(critic_drift.get("max_abs", 0.0)) <= 0.0:
        reasons.append(prefix + "renewal critic did not move")

    clock = result.get("training_clock", {})
    for field, expected in {
        "global_check_calls": GLOBAL_CHECK_CALLS,
        "env_check_rows": CHECK_ROWS,
        "structural_env_assignments": 16,
        "normal_env_checks": NORMAL_CHECK_ROWS,
        "auto_reset_high_actions": 0,
        "auto_reset_roster_violations": 0,
        "auto_reset_team_violations": 0,
        "auto_reset_age_violations": 0,
        "low_actor_hidden_reset_violations": 0,
        "low_critic_hidden_reset_violations": 0,
        "same_label_renew": 0,
        "update_policy_truncations": CHECK_ROWS,
        "continuation_critic_only_states": CHECK_ROWS,
    }.items():
        if clock.get(field) != expected:
            reasons.append(prefix + f"clock {field} mismatch")

    checkpoint = result.get("checkpoint", {})
    if checkpoint.get("schema") != "r44_frozen_source_nrc_checkpoint_v1":
        reasons.append(prefix + "checkpoint schema mismatch")
    if checkpoint.get("outer_updates") != OUTER_UPDATES or checkpoint.get("finite") is not True:
        reasons.append(prefix + "checkpoint update or finite contract failed")
    if checkpoint.get("components", {}).get("factor_optimizer") is not True:
        reasons.append(prefix + "factor optimizer missing from checkpoint")
    checkpoint_path = checkpoint.get("path")
    if not checkpoint_path or not Path(checkpoint_path).is_file():
        reasons.append(prefix + "checkpoint file missing")

    for stage in ("zero_step_evaluation", "evaluation"):
        evaluation = result.get(stage, {})
        if evaluation.get("evaluator") != "r44_deterministic_alice_bob_exact_trace":
            reasons.append(prefix + f"{stage} evaluator mismatch")
        if evaluation.get("episodes") != EVAL_EPISODES:
            reasons.append(prefix + f"{stage} episode count mismatch")
        for field in (
            "episode_wins",
            "episode_key0",
            "episode_key1",
            "episode_steps",
            "high_action_traces",
            "low_action_traces",
            "renewal_events",
        ):
            if len(evaluation.get(field, [])) != EVAL_EPISODES:
                reasons.append(prefix + f"{stage} {field} rows missing")
    return reasons


def _exact_trace_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    fields = (
        "episode_wins",
        "episode_key0",
        "episode_key1",
        "episode_steps",
        "high_action_traces",
        "low_action_traces",
    )
    return all(left.get(field) == right.get(field) for field in fields)


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
        arm_results[mode] = load_json(path)
        invalid_reasons.extend(validate_arm(arm_results[mode], mode))

    complete = len(arm_results) == 2
    control_events: dict[str, Any] = {}
    treatment_events: dict[str, Any] = {}
    service_ci = {"mean": 0.0, "lower_95": 0.0, "upper_95": 0.0}
    discordance_ci = {"mean": 0.0, "lower_95": 0.0, "upper_95": 0.0}
    if complete:
        control = arm_results[CONTROL]
        treatment = arm_results[TREATMENT]
        control_zero = control["zero_step_evaluation"]
        control_final = control["evaluation"]
        treatment_zero = treatment["zero_step_evaluation"]
        treatment_final = treatment["evaluation"]
        if control_zero.get("reset_stream") != control_final.get("reset_stream"):
            invalid_reasons.append("control zero/final reset streams differ")
        if control_zero.get("reset_stream") != treatment_zero.get("reset_stream"):
            invalid_reasons.append("two arms zero-step reset streams differ")
        if control_final.get("reset_stream") != treatment_final.get("reset_stream"):
            invalid_reasons.append("paired final reset streams differ")
        if not _exact_trace_equal(control_zero, control_final):
            invalid_reasons.append("control zero-step/final exact traces differ")
        if not _exact_trace_equal(control_zero, treatment_zero):
            invalid_reasons.append("two arms zero-step exact traces differ")
        try:
            control_events = event_summary(control_final)
            treatment_events = event_summary(treatment_final)
            service_delta = np.asarray(
                treatment_final["episode_wins"], dtype=np.float64
            ) - np.asarray(control_final["episode_wins"], dtype=np.float64)
            service_ci = bootstrap_mean(service_delta, 0)
            discordance_delta = np.asarray(
                treatment_events["discordant_episode_rows"], dtype=np.float64
            ) - np.asarray(
                control_events["discordant_episode_rows"], dtype=np.float64
            )
            discordance_ci = bootstrap_mean(discordance_delta, 1)
        except (KeyError, TypeError, ValueError) as exc:
            invalid_reasons.append(f"paired result parsing failed: {exc}")

    m0 = complete and not invalid_reasons
    if m0:
        control_final = arm_results[CONTROL]["evaluation"]
        m1 = bool(
            float(control_final["win_rate"]) >= 0.80
            and float(control_final["key0_rate"]) >= 0.85
            and float(control_final["key1_rate"]) >= 0.85
        )
        m2 = bool(service_ci["lower_95"] > -0.10)
        m3 = bool(
            treatment_events["discordant_rate"] >= 0.20
            and discordance_ci["lower_95"] > 0.0
            and treatment_events["full_sync_renew_rate"] < 0.50
            and treatment_events["minimum_keep_renew_marginal"] >= 0.05
            and treatment_events["renew_skill_entropy_normalized"] > 0.80
            and treatment_events["same_label_renew"] == 0
        )
    else:
        m1 = m2 = m3 = False

    if not m0:
        status = "INVALID_R44_FSNRC_IMPLEMENTATION"
        next_action = "repair the explicit freeze, replay, clock, checkpoint, or evaluation defect and rerun unchanged"
    elif not m1:
        status = "INVALID_R44_FROZEN_ANCHOR"
        next_action = "repair the frozen checkpoint, factorization, or evaluation wiring; do not interpret treatment"
    elif not (m2 and m3):
        status = "VALID_FAIL_R44_FSNRC"
        next_action = "retire the frozen-source K50 renewal timing route without rescue"
    else:
        status = "PASS_R44_FSNRC_K50"
        next_action = "run one paired multi-seed Alice-Bob verification with the same formula, freeze boundary, and thresholds"

    arm_summary = {
        mode: {
            "zero_step": result.get("zero_step_evaluation"),
            "final": result.get("evaluation"),
            "events": control_events if mode == CONTROL else treatment_events,
            "source_frozen_drift": result.get("source_frozen_drift"),
            "factor_drift": result.get("factor_drift"),
            "factor_gradient_stats": result.get("factor_gradient_stats"),
            "optimizer_steps": {
                "source": {
                    name: stats.get("steps")
                    for name, stats in result.get("telemetry", {}).get(
                        "source_optimizers", {}
                    ).items()
                },
                "factor": result.get("telemetry", {}).get(
                    "factor_optimizer", {}
                ).get("steps"),
            },
        }
        for mode, result in arm_results.items()
    }
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": m0,
        "seed": SEED,
        "contract": {
            "source_checkpoint": "R41B seed-1 exact-final",
            "arms": list(MODES),
            "rollout_envs_per_arm": 16,
            "environment_steps_per_arm": ENV_STEPS,
            "outer_updates_per_arm": OUTER_UPDATES,
            "environment_check_rows_per_arm": CHECK_ROWS,
            "factor_optimizer_steps_per_arm": FACTOR_STEPS,
            "source_optimizer_steps_per_path": 0,
            "evaluation_episodes_per_arm": EVAL_EPISODES,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "gates": {
            "M0_implementation_and_frozen_source": m0,
            "M1_frozen_service_anchor": m1,
            "M2_service_safety": m2,
            "M3_temporal_decoupling": m3,
        },
        "invalid_reasons": invalid_reasons,
        "paired": {
            "treatment_minus_control_win": service_ci,
            "treatment_minus_control_discordance": discordance_ci,
        },
        "arms": arm_summary,
        "interpretation_boundary": {
            "tests": "timing-only renewal on a frozen R41B skill system",
            "does_not_test": [
                "new skill discovery",
                "joint low-level adaptation",
                "general asynchronous skill learning",
                "S7 transfer",
                "variable team membership",
            ],
        },
        "next_action": next_action,
    }
    output_path = result_root / "r44_frozen_source_nrc.json"
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps({"status": status, "result": str(output_path)}))


if __name__ == "__main__":
    main()
