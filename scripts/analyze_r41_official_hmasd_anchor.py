"""Apply the preregistered R41 official-source reproduction decision gate."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


EXPERIMENT_ID = "EXP-20260716-r41-official-hmasd-alice-bob-anchor"
SOURCE_ARCHIVE = "ref/hmasd.tar"
SOURCE_TREE_LAYOUT = "hmasd/"
SEEDS = (1, 2, 3, 4, 5)
EXPECTED_OUTER_UPDATES = 937
EXPECTED_ENV_STEPS = 2_998_400
EXPECTED_OPTIMIZER_STEPS = 14_055
BOOTSTRAP_REPETITIONS = 10_000
BOOTSTRAP_SEED = 61_041


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def close_float(actual: Any, expected: float) -> bool:
    try:
        return math.isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def validate_seed(result: dict[str, Any], seed: int) -> list[str]:
    reasons: list[str] = []
    prefix = f"seed {seed}: "
    if result.get("experiment_id") != EXPERIMENT_ID:
        reasons.append(prefix + "experiment id mismatch")
    if result.get("seed") != seed or result.get("state") != "completed":
        reasons.append(prefix + "seed result is not completed for the expected seed")

    source = result.get("source", {})
    for boundary in ("before", "after"):
        identity = source.get(boundary, {})
        if identity.get("archive_repo_relative") != SOURCE_ARCHIVE:
            reasons.append(prefix + f"source {boundary} archive mismatch")
        if identity.get("archive_present") is not True:
            reasons.append(prefix + f"source {boundary} archive is missing")
        if identity.get("tree_layout") != SOURCE_TREE_LAYOUT:
            reasons.append(prefix + f"source {boundary} tree layout mismatch")
        if identity.get("required_entry_present") is not True:
            reasons.append(prefix + f"source {boundary} required entry is missing")
    if source.get("archive_repo_relative") != SOURCE_ARCHIVE:
        reasons.append(prefix + "official source archive is not ref/hmasd.tar")
    if source.get("tree_layout") != SOURCE_TREE_LAYOUT:
        reasons.append(prefix + "official source tree layout is not hmasd/")
    if source.get("fresh_extract") is not True:
        reasons.append(prefix + "official source was not recorded as a fresh archive extraction")

    runtime = result.get("runtime", {})
    if runtime.get("cuda_available") is not True:
        reasons.append(prefix + "runtime did not use an available CUDA device")
    if not runtime.get("python") or not runtime.get("torch") or not runtime.get("gpu"):
        reasons.append(prefix + "runtime manifest is incomplete")
    if not isinstance(runtime.get("pip_freeze"), list) or not runtime.get("pip_freeze"):
        reasons.append(prefix + "package-version manifest is missing")

    environment = result.get("environment", {})
    expected_environment = {
        "agents": 2,
        "obs": 11,
        "state": 100,
        "actions": 5,
        "horizon": 100,
    }
    for field, expected in expected_environment.items():
        if environment.get(field) != expected:
            reasons.append(prefix + f"environment {field} mismatch")

    arguments = result.get("official_arguments", {})
    expected_arguments: dict[str, Any] = {
        "game_version": 0,
        "env_name": "alice_and_bob",
        "algorithm_name": "hmasd",
        "experiment_name": "check",
        "seed": seed,
        "num_env_steps": 3_000_000,
        "episode_length": 100,
        "n_rollout_threads": 32,
        "n_eval_rollout_threads": 1,
        "n_training_threads": 16,
        "skill_type": "Discrete",
        "skill_interval": 50,
        "team_skill_dim": 2,
        "indi_skill_dim": 4,
        "use_recurrent_discri": 0,
        "d_epoch": 15,
        "d_num_mini_batch": 1,
        "skill_last_layer": 1,
        "intri_rew_exp": 0,
        "policy_use_both_skill": 0,
        "eval_episodes": 100,
        "h_ppo_epoch": 15,
        "h_num_mini_batch": 1,
        "l_ppo_epoch": 15,
        "l_num_mini_batch": 1,
        "hidden_size": 64,
        "n_embd": 64,
        "n_block": 1,
        "n_head": 1,
        "use_valuenorm": True,
        "use_eval": True,
        "model_dir": None,
    }
    for field, expected in expected_arguments.items():
        if arguments.get(field) != expected:
            reasons.append(
                prefix + f"official argument {field}={arguments.get(field)!r}, expected {expected!r}"
            )
    for field in (
        "h_entropy_coef",
        "h_lr",
        "h_critic_lr",
        "l_lr",
        "l_critic_lr",
        "d_team_lr",
        "d_indi_lr",
    ):
        expected = 0.1 if field == "h_entropy_coef" else 0.0005
        if not close_float(arguments.get(field), expected):
            reasons.append(prefix + f"official argument {field} mismatch")
    for field, expected in (
        ("lambda_env", 0.0),
        ("lambda_team", 0.1),
        ("lambda_indi", 0.2),
    ):
        if not close_float(arguments.get(field), expected):
            reasons.append(prefix + f"official argument {field} mismatch")

    boundary = result.get("algorithm_boundary", {})
    expected_boundary = {
        "source_algorithm": "official_fixed_k_hmasd",
        "high_reward": "environment_reward_only",
        "low_reward": "0.0*environment+0.1*q_D+0.2*q_d",
        "extra_shaping": False,
        "extra_intrinsic": False,
        "current_repo_process_path": False,
        "fresh_initialization": True,
        "logging_sink": "external_synchronous_noop",
    }
    for field, expected in expected_boundary.items():
        if boundary.get(field) != expected:
            reasons.append(prefix + f"algorithm boundary {field} mismatch")

    telemetry = result.get("telemetry", {})
    if telemetry.get("outer_updates") != EXPECTED_OUTER_UPDATES:
        reasons.append(prefix + "outer update count mismatch")
    if telemetry.get("actual_env_steps") != EXPECTED_ENV_STEPS:
        reasons.append(prefix + "actual environment-step count mismatch")
    optimizer_stats = telemetry.get("optimizers", {})
    for name in (
        "high",
        "low_actor",
        "low_critic",
        "team_discriminator",
        "individual_discriminator",
    ):
        stats = optimizer_stats.get(name, {})
        if stats.get("steps") != EXPECTED_OPTIMIZER_STEPS:
            reasons.append(prefix + f"{name} optimizer-step count mismatch")
        if stats.get("all_checked_gradients_finite") is not True:
            reasons.append(prefix + f"{name} gradient was absent or non-finite")
        if stats.get("ever_nonzero_gradient") is not True:
            reasons.append(prefix + f"{name} never exposed a nonzero gradient")

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

    checkpoints = result.get("checkpoints", {})
    required_modules = sorted(
        [
            "high_policy",
            "individual_discriminator",
            "low_actor",
            "low_critic",
            "team_discriminator",
        ]
    )
    required_optimizers = sorted(
        [
            "high",
            "individual_discriminator",
            "low_actor",
            "low_critic",
            "team_discriminator",
        ]
    )
    for stage, expected_selection, expected_updates in (
        ("zero_step", "zero_step", 0),
        ("exact_final", "exact_final", EXPECTED_OUTER_UPDATES),
    ):
        checkpoint = checkpoints.get(stage, {})
        if checkpoint.get("selection") != expected_selection:
            reasons.append(prefix + f"{stage} checkpoint selection mismatch")
        if checkpoint.get("outer_updates") != expected_updates:
            reasons.append(prefix + f"{stage} checkpoint update index mismatch")
        if checkpoint.get("finite") is not True:
            reasons.append(prefix + f"{stage} checkpoint is non-finite")
        components = checkpoint.get("components", {})
        if components.get("modules") != required_modules:
            reasons.append(prefix + f"{stage} checkpoint modules incomplete")
        if components.get("optimizers") != required_optimizers:
            reasons.append(prefix + f"{stage} checkpoint optimizers incomplete")
        if "low" not in components.get("value_norms", []):
            reasons.append(prefix + f"{stage} checkpoint low ValueNorm missing")
        path = checkpoint.get("path")
        if not path or not Path(path).is_file():
            reasons.append(prefix + f"{stage} checkpoint file missing")

    evaluations = result.get("evaluations", {})
    reset_streams = []
    for stage in ("zero_step", "exact_final"):
        evaluation = evaluations.get(stage, {})
        if evaluation.get("evaluator") != "official_deterministic_alice_bob_semantics":
            reasons.append(prefix + f"{stage} evaluator mismatch")
        if evaluation.get("episodes") != 100 or evaluation.get("eval_threads") != 1:
            reasons.append(prefix + f"{stage} evaluator budget mismatch")
        if evaluation.get("high_deterministic") is not True or evaluation.get("low_deterministic") is not True:
            reasons.append(prefix + f"{stage} evaluator was not exact deterministic")
        if len(evaluation.get("episode_wins", [])) != 100:
            reasons.append(prefix + f"{stage} evaluator episode rows missing")
        reset_streams.append(evaluation.get("reset_stream"))
    if len(reset_streams) == 2 and reset_streams[0] != reset_streams[1]:
        reasons.append(prefix + "zero and final evaluation reset streams differ")
    return reasons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    result_root = run_root / "result"
    result_root.mkdir(parents=True, exist_ok=True)

    seed_results: dict[int, dict[str, Any]] = {}
    invalid_reasons: list[str] = []
    for seed in SEEDS:
        path = run_root / "seeds" / f"seed{seed}" / "seed_result.json"
        if not path.is_file():
            invalid_reasons.append(f"seed {seed}: result file missing")
            continue
        result = load_json(path)
        seed_results[seed] = result
        invalid_reasons.extend(validate_seed(result, seed))

    complete = len(seed_results) == len(SEEDS)
    zero_rates = np.asarray(
        [seed_results[seed]["evaluations"]["zero_step"]["win_rate"] for seed in SEEDS],
        dtype=np.float64,
    ) if complete else np.full(5, np.nan)
    final_rates = np.asarray(
        [seed_results[seed]["evaluations"]["exact_final"]["win_rate"] for seed in SEEDS],
        dtype=np.float64,
    ) if complete else np.full(5, np.nan)
    deltas = final_rates - zero_rates
    if complete and np.all(np.isfinite(deltas)):
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        draws = rng.integers(0, len(SEEDS), size=(BOOTSTRAP_REPETITIONS, len(SEEDS)))
        bootstrap_means = deltas[draws].mean(axis=1)
        delta_ci = {
            "mean": float(deltas.mean()),
            "lower_95": float(np.quantile(bootstrap_means, 0.025)),
            "upper_95": float(np.quantile(bootstrap_means, 0.975)),
        }
    else:
        delta_ci = {"mean": None, "lower_95": None, "upper_95": None}

    m0 = complete and not invalid_reasons
    mean_final = float(final_rates.mean()) if complete else None
    seed1_final = float(final_rates[0]) if complete else None
    seeds_above_070 = int(np.sum(final_rates >= 0.70)) if complete else 0
    m1 = bool(m0 and mean_final >= 0.80 and seed1_final >= 0.80)
    m2 = bool(
        m0
        and seeds_above_070 >= 3
        and delta_ci["lower_95"] is not None
        and delta_ci["lower_95"] > 0.50
    )
    if not m0:
        status = "INVALID_R41_HMASD_ALICE_BOB_REPRODUCTION"
        next_action = "repair only the concrete source, wrapper, counter, checkpoint, or evaluator defect and rerun unchanged"
    elif m1 and m2:
        status = "PASS_R41_HMASD_ALICE_BOB_REPRODUCTION"
        next_action = "freeze seed-1 exact-final checkpoint and register only the same-checkpoint fixed-refresh versus native-categorical KEEP/SET comparison"
    else:
        status = "VALID_FAIL_R41_HMASD_ALICE_BOB_REPRODUCTION"
        next_action = "retire the R41 paper-task route and its PASS-only R30 treatment without rescue"

    result = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": m0,
        "source_archive": SOURCE_ARCHIVE,
        "contract": {
            "seeds": list(SEEDS),
            "declared_env_steps_per_seed": 3_000_000,
            "actual_env_steps_per_seed": EXPECTED_ENV_STEPS,
            "outer_updates_per_seed": EXPECTED_OUTER_UPDATES,
            "optimizer_steps_per_path_per_seed": EXPECTED_OPTIMIZER_STEPS,
            "eval_episodes_per_checkpoint": 100,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "gates": {
            "M0": {
                "passed": m0,
                "invalid_reasons": invalid_reasons,
            },
            "M1": {
                "passed": m1,
                "mean_final_win_rate": mean_final,
                "seed1_final_win_rate": seed1_final,
                "mean_final_floor": 0.80,
                "seed1_final_floor": 0.80,
            },
            "M2": {
                "passed": m2,
                "seeds_with_final_win_rate_at_least_0_70": seeds_above_070,
                "required_seed_count": 3,
                "final_minus_zero_bootstrap_ci": delta_ci,
                "strict_lower_bound_floor": 0.50,
            },
        },
        "per_seed": {
            str(seed): {
                "zero_step_win_rate": float(zero_rates[index]) if complete else None,
                "final_win_rate": float(final_rates[index]) if complete else None,
                "final_minus_zero": float(deltas[index]) if complete else None,
                "elapsed_seconds": seed_results.get(seed, {}).get("elapsed_seconds"),
            }
            for index, seed in enumerate(SEEDS)
        },
        "next_action": next_action,
    }
    output_path = result_root / "r41_official_hmasd_alice_bob.json"
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
