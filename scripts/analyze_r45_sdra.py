"""Analyze the registered R45-SDRA natural-support identifiability gate."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from r45_sdra import (
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    CHECK_ROWS,
    CRITIC_STEPS_PER_MODEL,
    CRITIC_TOTAL_STEPS,
    ENV_STEPS,
    EVAL_EPISODES,
    FACTOR_ROWS,
    NORMAL_ROWS,
    OUTER_UPDATES,
    ROLLOUT_ENVS,
    STRUCTURAL_ROWS,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        with temporary_path.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def interval(values: np.ndarray, point: float) -> dict[str, float]:
    finite = values[np.isfinite(values)]
    if finite.size != values.size or not finite.size:
        return {"lower_95": math.nan, "mean": point, "upper_95": math.nan}
    return {
        "lower_95": float(np.quantile(finite, 0.025)),
        "mean": float(point),
        "upper_95": float(np.quantile(finite, 0.975)),
    }


def cluster_counts(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    samples = rng.integers(
        0, ROLLOUT_ENVS, size=(BOOTSTRAP_REPETITIONS, ROLLOUT_ENVS)
    )
    counts = np.zeros((BOOTSTRAP_REPETITIONS, ROLLOUT_ENVS), dtype=np.float64)
    for repetition in range(BOOTSTRAP_REPETITIONS):
        counts[repetition] = np.bincount(
            samples[repetition], minlength=ROLLOUT_ENVS
        )
    return counts


def _cluster_sums(
    values: np.ndarray, mask: np.ndarray, env_rank: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    sums = np.zeros(ROLLOUT_ENVS, dtype=np.float64)
    counts = np.zeros(ROLLOUT_ENVS, dtype=np.float64)
    for env in range(ROLLOUT_ENVS):
        selected = mask & (env_rank == env)
        sums[env] = float(values[selected].sum())
        counts[env] = float(selected.sum())
    return sums, counts


def bootstrap_group_mean(
    values: np.ndarray,
    mask: np.ndarray,
    env_rank: np.ndarray,
    bootstrap: np.ndarray,
) -> tuple[float, np.ndarray]:
    sums, counts = _cluster_sums(values, mask, env_rank)
    point = float(sums.sum() / counts.sum())
    denominators = bootstrap @ counts
    replicates = np.divide(
        bootstrap @ sums,
        denominators,
        out=np.full(len(bootstrap), np.nan, dtype=np.float64),
        where=denominators > 0,
    )
    return point, replicates


def bootstrap_difference(
    values: np.ndarray,
    top: np.ndarray,
    bottom: np.ndarray,
    env_rank: np.ndarray,
    bootstrap: np.ndarray,
) -> dict[str, float]:
    top_point, top_boot = bootstrap_group_mean(
        values, top, env_rank, bootstrap
    )
    bottom_point, bottom_boot = bootstrap_group_mean(
        values, bottom, env_rank, bootstrap
    )
    return interval(top_boot - bottom_boot, top_point - bottom_point)


def bootstrap_weighted_mse(
    squared_error: np.ndarray,
    weights: np.ndarray,
    env_rank: np.ndarray,
    bootstrap: np.ndarray,
) -> tuple[float, np.ndarray]:
    numerators = np.zeros(ROLLOUT_ENVS, dtype=np.float64)
    denominators = np.zeros(ROLLOUT_ENVS, dtype=np.float64)
    for env in range(ROLLOUT_ENVS):
        selected = env_rank == env
        numerators[env] = float((weights[selected] * squared_error[selected]).sum())
        denominators[env] = float(weights[selected].sum())
    point = float(numerators.sum() / denominators.sum())
    boot_denominator = bootstrap @ denominators
    replicates = np.divide(
        bootstrap @ numerators,
        boot_denominator,
        out=np.full(len(bootstrap), np.nan, dtype=np.float64),
        where=boot_denominator > 0,
    )
    return point, replicates


def exact_trace_equality(result: dict[str, Any]) -> bool:
    values = result.get("exact_trace_equality", {})
    return bool(
        values.get("outcomes")
        and values.get("high_actions")
        and values.get("low_actions")
    )


def validate_m0(
    result: dict[str, Any], arrays: dict[str, np.ndarray]
) -> list[str]:
    reasons: list[str] = []
    collection = result.get("collection", {})
    telemetry = result.get("telemetry", {})
    clock = result.get("training_clock", {})
    boundary = result.get("algorithm_boundary", {})
    critics = result.get("critic_training", {})
    if result.get("scope") != "formal":
        reasons.append("worker result is not the registered formal scope")
    if telemetry.get("outer_updates") != OUTER_UPDATES:
        reasons.append("outer-update count mismatch")
    if telemetry.get("actual_env_steps") != ENV_STEPS:
        reasons.append("environment-step count mismatch")
    if collection.get("env_check_rows") != CHECK_ROWS:
        reasons.append("environment-check row count mismatch")
    if collection.get("structural_rows") != STRUCTURAL_ROWS:
        reasons.append("structural row count mismatch")
    if collection.get("normal_rows") != NORMAL_ROWS:
        reasons.append("normal row count mismatch")
    if collection.get("factor_rows") != FACTOR_ROWS:
        reasons.append("normal factor row count mismatch")
    if collection.get("row_count") != FACTOR_ROWS:
        reasons.append("saved factor row count mismatch")
    if list(collection.get("context_shape", [])) != [FACTOR_ROWS, 148]:
        reasons.append("saved context shape mismatch")
    if result.get("source_frozen_drift", {}).get("exact") is not True:
        reasons.append("source module, optimizer, or ValueNorm drifted")
    if float(result.get("renewal_actor_drift", {}).get("max_abs", math.inf)) != 0.0:
        reasons.append("frozen renewal actor drifted")
    source_steps = telemetry.get("source_optimizer_steps", {})
    if set(source_steps) != {
        "high",
        "low_actor",
        "low_critic",
        "team_discriminator",
        "individual_discriminator",
    } or any(int(value) != 0 for value in source_steps.values()):
        reasons.append("source optimizer step contract failed")
    if int(telemetry.get("renewal_actor_optimizer_steps", -1)) != 0:
        reasons.append("renewal actor received optimizer steps")
    if float(collection.get("source_probability_max_error", math.inf)) > 1e-6:
        reasons.append("source-exact probability error exceeded 1e-6")
    if float(collection.get("binary_replay_logp_max_error", math.inf)) > 1e-6:
        reasons.append("binary replay log-probability error exceeded 1e-6")
    if int(collection.get("working_prefix_mismatch", -1)) != 0:
        reasons.append("working-prefix mismatch was nonzero")
    for name in (
        "auto_reset_high_actions",
        "auto_reset_roster_violations",
        "auto_reset_team_violations",
        "auto_reset_age_violations",
        "low_actor_hidden_reset_violations",
        "low_critic_hidden_reset_violations",
    ):
        if int(clock.get(name, -1)) != 0:
            reasons.append(f"clock invariant failed: {name}")
    for name, expected in (
        ("renewal_actor_updates", False),
        ("source_optimizer_updates", False),
        ("critic_only", True),
        ("forced_branch", False),
        ("simulator_clone", False),
        ("extra_shaping", False),
        ("extra_intrinsic", False),
        ("task_fields_in_context", False),
    ):
        if boundary.get(name) is not expected:
            reasons.append(f"algorithm boundary mismatch: {name}")
    if critics.get("total_optimizer_steps") != CRITIC_TOTAL_STEPS:
        reasons.append("critic total optimizer-step count mismatch")
    if critics.get("all_gradients_finite") is not True:
        reasons.append("critic gradients were non-finite")
    for label in ("A", "B"):
        fold = critics.get("folds", {}).get(label, {})
        if fold.get("true_steps") != CRITIC_STEPS_PER_MODEL:
            reasons.append(f"fold {label} true-Q optimizer-step mismatch")
        if fold.get("sham_steps") != CRITIC_STEPS_PER_MODEL:
            reasons.append(f"fold {label} sham optimizer-step mismatch")
        if fold.get("train_rows") != FACTOR_ROWS // 2:
            reasons.append(f"fold {label} train-row count mismatch")
        if fold.get("heldout_rows") != FACTOR_ROWS // 2:
            reasons.append(f"fold {label} heldout-row count mismatch")
        if fold.get("architecture") != "148->32_GELU->2":
            reasons.append(f"fold {label} critic architecture mismatch")
        if float(fold.get("initial_true_sham_max_difference", math.inf)) != 0.0:
            reasons.append(f"fold {label} true/sham initialization mismatch")
        if int(fold.get("true_nonzero_gradient_steps", 0)) <= 0:
            reasons.append(f"fold {label} true-Q lacked gradient exposure")
        if int(fold.get("sham_nonzero_gradient_steps", 0)) <= 0:
            reasons.append(f"fold {label} sham lacked gradient exposure")
    if not exact_trace_equality(result):
        reasons.append("zero/final frozen-source traces were not exact")

    required = {
        "context",
        "env_rank",
        "update_index",
        "block_index",
        "check_index",
        "event_id",
        "agent",
        "action",
        "propensity_renew",
        "outcome",
        "true_q",
        "sham_q",
        "trained_on_fold",
    }
    if set(arrays) != required:
        reasons.append("saved evidence array schema mismatch")
        return reasons
    if any(len(value) != FACTOR_ROWS for value in arrays.values()):
        reasons.append("saved evidence array length mismatch")
    for name in ("context", "propensity_renew", "outcome", "true_q", "sham_q"):
        if not bool(np.isfinite(arrays[name]).all()):
            reasons.append(f"saved evidence contains non-finite {name}")
    if bool(((arrays["propensity_renew"] <= 0.0) | (arrays["propensity_renew"] >= 1.0)).any()):
        reasons.append("propensity lacks strict natural support")
    if not bool(np.isin(arrays["action"], [0, 1]).all()):
        reasons.append("renewal action is not binary")
    if not bool(np.isin(arrays["agent"], [0, 1]).all()):
        reasons.append("agent index is invalid")
    observed_probability = np.where(
        arrays["action"] == 1,
        arrays["propensity_renew"],
        1.0 - arrays["propensity_renew"],
    )
    weights = 1.0 / observed_probability
    predicted_delta = arrays["true_q"][:, 1] - arrays["true_q"][:, 0]
    dr_score = (
        predicted_delta
        + (arrays["action"] == 1)
        / arrays["propensity_renew"]
        * (arrays["outcome"] - arrays["true_q"][:, 1])
        - (arrays["action"] == 0)
        / (1.0 - arrays["propensity_renew"])
        * (arrays["outcome"] - arrays["true_q"][:, 0])
    )
    if not bool(np.isfinite(weights).all()):
        reasons.append("inverse-propensity weights were non-finite")
    if not bool(np.isfinite(dr_score).all()):
        reasons.append("doubly robust scores were non-finite")
    expected_train_fold = np.where(arrays["env_rank"] <= 7, 1, 0)
    if not bool(np.array_equal(arrays["trained_on_fold"], expected_train_fold)):
        reasons.append("cross-fit train/heldout environments overlap")
    unique_events, counts = np.unique(arrays["event_id"], return_counts=True)
    if len(unique_events) != NORMAL_ROWS or not bool((counts == 2).all()):
        reasons.append("natural checks do not have exactly two focal rows")
    order = np.lexsort((arrays["agent"], arrays["event_id"]))
    ordered_agent = arrays["agent"][order].reshape(-1, 2)
    ordered_outcome = arrays["outcome"][order].reshape(-1, 2)
    if not bool(np.array_equal(ordered_agent, np.tile([0, 1], (NORMAL_ROWS, 1)))):
        reasons.append("paired focal-row agent order is invalid")
    if not bool(np.array_equal(ordered_outcome[:, 0], ordered_outcome[:, 1])):
        reasons.append("same-check agents did not receive the same registered outcome")
    return reasons


def overlap_metrics(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    metrics: dict[str, Any] = {"groups": {}}
    all_pass = True
    action = arrays["action"]
    agent = arrays["agent"]
    env_rank = arrays["env_rank"]
    propensity = arrays["propensity_renew"]
    for focal in (0, 1):
        for selected_action, action_name in ((0, "KEEP"), (1, "RENEW")):
            mask = (agent == focal) & (action == selected_action)
            observed_probability = (
                propensity[mask]
                if selected_action == 1
                else 1.0 - propensity[mask]
            )
            if not len(observed_probability):
                metrics["groups"][f"agent_{focal}_{action_name}"] = {
                    "rows": 0,
                    "ess": 0.0,
                    "maximum_environment_weight_share": 1.0,
                    "pass": False,
                }
                all_pass = False
                continue
            weights = 1.0 / observed_probability
            ess = float(weights.sum() ** 2 / np.square(weights).sum())
            cluster_weights = np.asarray(
                [weights[env_rank[mask] == env].sum() for env in range(ROLLOUT_ENVS)]
            )
            max_share = float(cluster_weights.max() / cluster_weights.sum())
            passed = bool(len(weights) > 0 and ess >= 64.0 and max_share <= 0.10)
            all_pass = all_pass and passed
            metrics["groups"][f"agent_{focal}_{action_name}"] = {
                "rows": int(len(weights)),
                "ess": ess,
                "maximum_environment_weight_share": max_share,
                "pass": passed,
            }
    metrics["pass"] = bool(all_pass)
    return metrics


def scientific_metrics(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    env_rank = arrays["env_rank"]
    action = arrays["action"]
    propensity = arrays["propensity_renew"]
    outcome = arrays["outcome"]
    true_q = arrays["true_q"]
    sham_q = arrays["sham_q"]
    observed_probability = np.where(action == 1, propensity, 1.0 - propensity)
    weights = 1.0 / observed_probability
    row = np.arange(len(action))
    true_prediction = true_q[row, action]
    sham_prediction = (
        (1.0 - propensity) * sham_q[:, 0] + propensity * sham_q[:, 1]
    )
    true_error = np.square(outcome - true_prediction)
    sham_error = np.square(outcome - sham_prediction)
    bootstrap = cluster_counts(BOOTSTRAP_SEED)
    true_wmse, true_boot = bootstrap_weighted_mse(
        true_error, weights, env_rank, bootstrap
    )
    sham_wmse, sham_boot = bootstrap_weighted_mse(
        sham_error, weights, env_rank, bootstrap
    )
    ratio = sham_wmse / true_wmse
    ratio_boot = sham_boot / true_boot
    ratio_ci = interval(ratio_boot, ratio)
    ratio_gain_ci = interval(ratio_boot - 1.0, ratio - 1.0)

    delta = true_q[:, 1] - true_q[:, 0]
    psi = (
        delta
        + (action == 1) / propensity * (outcome - true_q[:, 1])
        - (action == 0) / (1.0 - propensity) * (outcome - true_q[:, 0])
    )
    pooled_q25, pooled_q75 = np.quantile(delta, [0.25, 0.75])
    pooled_bottom = delta <= pooled_q25
    pooled_top = delta >= pooled_q75
    ranking_ci = bootstrap_difference(
        psi, pooled_top, pooled_bottom, env_rank, bootstrap
    )
    m2_pass = bool(
        ratio_gain_ci["lower_95"] > 0.0 and ranking_ci["lower_95"] > 0.0
    )

    agent_sign: dict[str, Any] = {}
    m3_agent_pass = True
    for focal in (0, 1):
        focal_mask = arrays["agent"] == focal
        q25, q75 = np.quantile(delta[focal_mask], [0.25, 0.75])
        bottom = focal_mask & (delta <= q25)
        top = focal_mask & (delta >= q75)
        top_point, top_boot = bootstrap_group_mean(
            psi, top, env_rank, bootstrap
        )
        bottom_point, bottom_boot = bootstrap_group_mean(
            psi, bottom, env_rank, bootstrap
        )
        top_ci = interval(top_boot, top_point)
        bottom_ci = interval(bottom_boot, bottom_point)
        passed = bool(top_ci["lower_95"] > 0.0 and bottom_ci["upper_95"] < 0.0)
        m3_agent_pass = m3_agent_pass and passed
        agent_sign[f"agent_{focal}"] = {
            "predicted_delta_q25": float(q25),
            "predicted_delta_q75": float(q75),
            "top_psi": top_ci,
            "bottom_psi": bottom_ci,
            "pass": passed,
        }

    order = np.lexsort((arrays["agent"], arrays["event_id"]))
    event_delta = delta[order].reshape(-1, 2)
    event_env = env_rank[order].reshape(-1, 2)[:, 0]
    sign_discordance = (
        np.sign(event_delta[:, 0]) != np.sign(event_delta[:, 1])
    ).astype(np.float64)
    discordance_point, discordance_boot = bootstrap_group_mean(
        sign_discordance,
        np.ones(len(sign_discordance), dtype=bool),
        event_env,
        bootstrap,
    )
    discordance_ci = interval(discordance_boot, discordance_point)
    discordance_pass = bool(
        discordance_point >= 0.20 and discordance_ci["lower_95"] > 0.10
    )
    m3_pass = bool(m3_agent_pass and discordance_pass)
    return {
        "m2": {
            "true_q_weighted_mse": true_wmse,
            "action_blind_weighted_mse": sham_wmse,
            "wmse_sham_over_true": ratio_ci,
            "wmse_ratio_gain": ratio_gain_ci,
            "registered_text_ambiguity": (
                "Pro wrote LCB(WMSE_sham/WMSE_true)>0, which is tautological "
                "for finite positive losses; the executable nontrivial reading "
                "is LCB(WMSE_sham/WMSE_true-1)>0."
            ),
            "pooled_predicted_delta_q25": float(pooled_q25),
            "pooled_predicted_delta_q75": float(pooled_q75),
            "top_minus_bottom_dr_score": ranking_ci,
            "pass": m2_pass,
        },
        "m3": {
            "agent_sign_heterogeneity": agent_sign,
            "same_check_sign_discordance": discordance_ci,
            "same_check_sign_discordance_point_floor": 0.20,
            "same_check_sign_discordance_lcb_floor": 0.10,
            "pass": m3_pass,
        },
        "diagnostics": {
            "dr_score_mean": float(psi.mean()),
            "dr_score_std": float(psi.std()),
            "predicted_delta_mean": float(delta.mean()),
            "predicted_delta_std": float(delta.std()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    seed_result_path = run_root / "seed" / "seed_result.json"
    result_path = run_root / "result" / "r45_sdra_identifiability.json"
    seed_result = load_json(seed_result_path)
    evidence_path = Path(seed_result["collection"]["rows_path"])
    with np.load(evidence_path, allow_pickle=False) as loaded:
        arrays = {name: loaded[name] for name in loaded.files}

    invalid_reasons = validate_m0(seed_result, arrays)
    m0 = not invalid_reasons
    final_eval = seed_result.get("evaluation", {})
    m1_service = bool(
        float(final_eval.get("win_rate", 0.0)) >= 0.80
        and float(final_eval.get("key0_rate", 0.0)) >= 0.85
        and float(final_eval.get("key1_rate", 0.0)) >= 0.85
    )
    overlap = overlap_metrics(arrays) if m0 else {"pass": False, "groups": {}}
    m1 = bool(m0 and m1_service and overlap["pass"])
    scientific = scientific_metrics(arrays) if m0 else {
        "m2": {"pass": False},
        "m3": {"pass": False},
        "diagnostics": {},
    }
    m2 = bool(m0 and scientific["m2"]["pass"])
    m3 = bool(m0 and scientific["m3"]["pass"])
    if not m0:
        status = "INVALID_R45_SDRA_WIRING"
        next_action = "repair only the concrete wiring defect and rerun unchanged"
    elif m1 and m2 and m3:
        status = "PASS_R45_SDRA_IDENTIFIABILITY"
        next_action = (
            "prepare one mechanism-matched actor pair using detached "
            "cross-fitted SDRA advantage"
        )
    else:
        status = "VALID_FAIL_R45_SDRA_IDENTIFIABILITY"
        next_action = (
            "retire Alice-Bob K50 natural-support renewal credit and this "
            "temporal-mechanism substrate without rescue"
        )
    payload = {
        "experiment_id": seed_result.get("experiment_id"),
        "status": status,
        "implementation_valid": m0,
        "invalid_reasons": invalid_reasons,
        "gates": {
            "M0_implementation_and_data": m0,
            "M1_service_and_overlap": m1,
            "M2_action_specific_informativeness": m2,
            "M3_sign_heterogeneity": m3,
        },
        "contract": {
            "source_checkpoint": "R41B_seed1_exact_final",
            "seed": 43041,
            "rollout_envs": ROLLOUT_ENVS,
            "outer_updates": OUTER_UPDATES,
            "environment_steps": ENV_STEPS,
            "env_check_rows": CHECK_ROWS,
            "normal_factor_rows": FACTOR_ROWS,
            "source_optimizer_steps": 0,
            "renewal_actor_optimizer_steps": 0,
            "critic_optimizer_steps_per_model": CRITIC_STEPS_PER_MODEL,
            "critic_optimizer_steps_total": CRITIC_TOTAL_STEPS,
            "evaluation_episodes": EVAL_EPISODES,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "m2_executable_threshold": "LCB95(WMSE_sham/WMSE_true - 1) > 0",
        },
        "source_service": {
            "win_rate": final_eval.get("win_rate"),
            "key0_rate": final_eval.get("key0_rate"),
            "key1_rate": final_eval.get("key1_rate"),
            "zero_final_exact_trace": exact_trace_equality(seed_result),
            "pass": m1_service,
        },
        "overlap": overlap,
        "scientific": scientific,
        "implementation": {
            "source_frozen_drift": seed_result.get("source_frozen_drift"),
            "renewal_actor_drift": seed_result.get("renewal_actor_drift"),
            "telemetry": seed_result.get("telemetry"),
            "training_clock": seed_result.get("training_clock"),
            "collection": seed_result.get("collection"),
            "critic_training": seed_result.get("critic_training"),
            "algorithm_boundary": seed_result.get("algorithm_boundary"),
        },
        "next_action": next_action,
        "prohibitions": [
            "no R42-R44 rescue",
            "no extra seeds or data",
            "no propensity clipping",
            "no critic-capacity or threshold changes",
            "no renewal actor update in G0",
            "no task-specific intrinsic reward or shaping",
            "no forced renewal branch or simulator clone",
            "no S7, open-roster, or variable-N promotion",
        ],
    }
    atomic_json(result_path, payload)
    print(f"R45 analysis complete: status={status}; result={result_path}")


if __name__ == "__main__":
    main()
