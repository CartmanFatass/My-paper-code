"""Analyze the registered R46-HMRV-G0 identifiability gate."""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from r46_hmrv import (
    BEHAVIOR_ACTION_SEED,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    CHECKS_PER_EPISODE,
    CRITIC_EPOCHS,
    CRITIC_MINIBATCH,
    CRITIC_STEPS_PER_MODEL,
    CRITIC_TOTAL_STEPS,
    ENVIRONMENT_SEED,
    ENV_STEPS,
    EPISODES_PER_ENV,
    EVAL_ACTION_SEED,
    EVAL_EPISODES,
    EXPERIMENT_ID,
    FOCAL_ROWS,
    GAMMA,
    K0,
    KEEP,
    N_AGENTS,
    RENEW,
    ROLLOUT_ENVS,
    TOTAL_CHECK_ROWS,
    USABLE_CHECKS,
    USABLE_EVENT_ROWS,
    evaluation_schedule,
    run_evaluation_trace,
    three_block_outcomes,
)


N_CLUSTERS = ROLLOUT_ENVS * EPISODES_PER_ENV


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


def interval(replicates: np.ndarray, point: float) -> dict[str, float]:
    finite = replicates[np.isfinite(replicates)]
    if finite.size != replicates.size or not finite.size:
        return {"lower_95": math.nan, "mean": point, "upper_95": math.nan}
    return {
        "lower_95": float(np.quantile(finite, 0.025)),
        "mean": float(point),
        "upper_95": float(np.quantile(finite, 0.975)),
    }


def bootstrap_samples() -> np.ndarray:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    return rng.integers(
        0,
        N_CLUSTERS,
        size=(BOOTSTRAP_REPETITIONS, N_CLUSTERS),
        dtype=np.uint16,
    )


def _cluster_sums(
    values: np.ndarray, mask: np.ndarray, cluster_id: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    sums = np.bincount(
        cluster_id[mask], weights=values[mask], minlength=N_CLUSTERS
    ).astype(np.float64)
    counts = np.bincount(cluster_id[mask], minlength=N_CLUSTERS).astype(np.float64)
    return sums, counts


def _bootstrap_ratio(
    numerators: np.ndarray, denominators: np.ndarray, samples: np.ndarray
) -> np.ndarray:
    result = np.full(len(samples), np.nan, dtype=np.float64)
    for start in range(0, len(samples), 128):
        selected = samples[start : start + 128]
        numerator = numerators[selected].sum(axis=1)
        denominator = denominators[selected].sum(axis=1)
        result[start : start + len(selected)] = np.divide(
            numerator,
            denominator,
            out=np.full(len(selected), np.nan, dtype=np.float64),
            where=denominator > 0,
        )
    return result


def bootstrap_group_mean(
    values: np.ndarray,
    mask: np.ndarray,
    cluster_id: np.ndarray,
    samples: np.ndarray,
) -> tuple[float, np.ndarray]:
    sums, counts = _cluster_sums(values, mask, cluster_id)
    point = float(sums.sum() / counts.sum())
    return point, _bootstrap_ratio(sums, counts, samples)


def bootstrap_difference(
    values: np.ndarray,
    top: np.ndarray,
    bottom: np.ndarray,
    cluster_id: np.ndarray,
    samples: np.ndarray,
) -> dict[str, float]:
    top_point, top_boot = bootstrap_group_mean(
        values, top, cluster_id, samples
    )
    bottom_point, bottom_boot = bootstrap_group_mean(
        values, bottom, cluster_id, samples
    )
    return interval(top_boot - bottom_boot, top_point - bottom_point)


def bootstrap_weighted_mse(
    squared_error: np.ndarray,
    weights: np.ndarray,
    cluster_id: np.ndarray,
    samples: np.ndarray,
) -> tuple[float, np.ndarray]:
    numerators = np.bincount(
        cluster_id,
        weights=weights * squared_error,
        minlength=N_CLUSTERS,
    ).astype(np.float64)
    denominators = np.bincount(
        cluster_id, weights=weights, minlength=N_CLUSTERS
    ).astype(np.float64)
    point = float(numerators.sum() / denominators.sum())
    return point, _bootstrap_ratio(numerators, denominators, samples)


def validate_m0(
    worker: dict[str, Any], arrays: dict[str, np.ndarray]
) -> list[str]:
    reasons: list[str] = []
    telemetry = worker.get("telemetry", {})
    collection = worker.get("collection", {})
    critics = worker.get("critic_training", {})
    evaluation = worker.get("evaluation", {})
    boundary = worker.get("algorithm_boundary", {})
    seeds = worker.get("seeds", {})

    if worker.get("experiment_id") != EXPERIMENT_ID or worker.get("scope") != "formal":
        reasons.append("worker identity or scope mismatch")
    if worker.get("state") != "completed" or worker.get("device") != "cuda":
        reasons.append("formal worker did not complete on CUDA")
    expected_seeds = {
        "environment": ENVIRONMENT_SEED,
        "behavior_action": BEHAVIOR_ACTION_SEED,
        "evaluation_action": EVAL_ACTION_SEED,
    }
    if seeds != expected_seeds:
        reasons.append("registered RNG seed schedule mismatch")
    for name, expected in (
        ("rollout_envs", ROLLOUT_ENVS),
        ("episodes_per_env", EPISODES_PER_ENV),
        ("environment_steps", ENV_STEPS),
        ("total_check_rows", TOTAL_CHECK_ROWS),
        ("usable_event_rows", USABLE_EVENT_ROWS),
        ("focal_rows", FOCAL_ROWS),
        ("policy_optimizer_steps", 0),
        ("low_optimizer_steps", 0),
        ("skill_optimizer_steps", 0),
        ("intrinsic_optimizer_steps", 0),
        ("critic_optimizer_steps", CRITIC_TOTAL_STEPS),
    ):
        if telemetry.get(name) != expected:
            reasons.append(f"telemetry mismatch: {name}")
    if list(collection.get("context_shape", [])) != [FOCAL_ROWS, 6]:
        reasons.append("six-field context shape mismatch")
    if collection.get("propensity_min") != 0.5 or collection.get("propensity_max") != 0.5:
        reasons.append("behavior propensity is not exactly Bernoulli-0.5")
    if collection.get("behavior_action_replay_mismatch") != 0:
        reasons.append("stored behavior action replay mismatch")
    if int(collection.get("zero_reward_blocks", 0)) <= 0:
        reasons.append("no zero-reward block was observed")
    if int(collection.get("full_service_blocks", 0)) <= 0:
        reasons.append("no full-service block was observed")
    required_boundary = {
        "standalone_synthetic_substrate": True,
        "behavior_policy_fixed_bernoulli_half": True,
        "policy_module_exists": False,
        "low_module_exists": False,
        "skill_module_exists": False,
        "intrinsic_reward_exists": False,
        "task_specific_intrinsic_reward": False,
        "critic_only_learning": True,
        "reward_shaping": False,
        "early_stopping": False,
        "model_selection": False,
    }
    if boundary != required_boundary:
        reasons.append("algorithm boundary differs from registered critic-only G0")
    if critics.get("total_optimizer_steps") != CRITIC_TOTAL_STEPS:
        reasons.append("critic total optimizer-step mismatch")
    if critics.get("all_gradients_finite") is not True:
        reasons.append("critic gradients were non-finite")
    fold_expected = {
        "A": (46_041, 1_046_044, list(range(0, 8)), list(range(8, 16))),
        "B": (56_041, 1_056_044, list(range(8, 16)), list(range(0, 8))),
    }
    for label, (model_seed, shuffle_seed, train_envs, heldout_envs) in fold_expected.items():
        fold = critics.get("folds", {}).get(label, {})
        for name in ("true_steps", "sham_steps"):
            if fold.get(name) != CRITIC_STEPS_PER_MODEL:
                reasons.append(f"fold {label} {name} mismatch")
        if fold.get("train_rows") != FOCAL_ROWS // 2 or fold.get("heldout_rows") != FOCAL_ROWS // 2:
            reasons.append(f"fold {label} row-count mismatch")
        if fold.get("architecture") != "6->32_GELU->2":
            reasons.append(f"fold {label} architecture mismatch")
        if fold.get("epochs") != CRITIC_EPOCHS or fold.get("minibatch") != CRITIC_MINIBATCH:
            reasons.append(f"fold {label} training schedule mismatch")
        if fold.get("drop_last") is not False:
            reasons.append(f"fold {label} drop_last mismatch")
        if fold.get("model_init_seed") != model_seed or fold.get("shuffle_seed") != shuffle_seed:
            reasons.append(f"fold {label} RNG schedule mismatch")
        if fold.get("train_env_ranks") != train_envs or fold.get("heldout_env_ranks") != heldout_envs:
            reasons.append(f"fold {label} environment partition mismatch")
        if float(fold.get("initial_true_sham_max_difference", math.inf)) != 0.0:
            reasons.append(f"fold {label} true/sham initialization mismatch")
        if int(fold.get("true_nonzero_gradient_steps", 0)) <= 0:
            reasons.append(f"fold {label} true-Q lacked gradient exposure")
        if int(fold.get("sham_nonzero_gradient_steps", 0)) <= 0:
            reasons.append(f"fold {label} sham lacked gradient exposure")
    exact_eval = evaluation.get("exact_trace_equality", {})
    if evaluation.get("episodes") != EVAL_EPISODES or evaluation.get("all_exact") is not True:
        reasons.append("paired evaluation trace contract failed")
    if set(exact_eval) != {
        "role_assignments",
        "actions",
        "pre_health",
        "post_health",
        "service_output",
        "block_reward",
    } or not all(exact_eval.values()):
        reasons.append("pre/post critic evaluation traces are not exact")

    expected_keys = {
        "context",
        "env_rank",
        "episode_index",
        "check_index",
        "event_id",
        "cluster_id",
        "agent",
        "action",
        "propensity_renew",
        "outcome",
        "role_d0",
        "role_d1",
        "behavior_actions",
        "degradation",
        "pre_health",
        "post_health",
        "service_output",
        "block_reward",
        "true_q",
        "sham_q",
        "trained_on_fold",
        "eval_role_assignments",
        "eval_actions",
        "eval_pre_health_before",
        "eval_post_health_before",
        "eval_service_output_before",
        "eval_block_reward_before",
        "eval_pre_health_after",
        "eval_post_health_after",
        "eval_service_output_after",
        "eval_block_reward_after",
    }
    if set(arrays) != expected_keys:
        reasons.append("saved evidence array schema mismatch")
        return reasons
    row_keys = {
        "context",
        "env_rank",
        "episode_index",
        "check_index",
        "event_id",
        "cluster_id",
        "agent",
        "action",
        "propensity_renew",
        "outcome",
        "role_d0",
        "role_d1",
        "true_q",
        "sham_q",
        "trained_on_fold",
    }
    if any(len(arrays[name]) != FOCAL_ROWS for name in row_keys):
        reasons.append("saved focal-row array length mismatch")
        return reasons
    for name in ("context", "propensity_renew", "outcome", "true_q", "sham_q"):
        if not np.isfinite(arrays[name]).all():
            reasons.append(f"saved evidence contains non-finite {name}")

    actions = arrays["behavior_actions"]
    degradation = arrays["degradation"]
    pre = arrays["pre_health"]
    post = arrays["post_health"]
    service = arrays["service_output"]
    block_reward = arrays["block_reward"]
    expected_trace_shape = (
        ROLLOUT_ENVS,
        EPISODES_PER_ENV,
        CHECKS_PER_EPISODE,
        N_AGENTS,
    )
    if actions.shape != expected_trace_shape or pre.shape != expected_trace_shape or post.shape != expected_trace_shape:
        reasons.append("formal transition trace shape mismatch")
        return reasons
    if degradation.shape != (ROLLOUT_ENVS, EPISODES_PER_ENV, N_AGENTS):
        reasons.append("degradation trace shape mismatch")
        return reasons
    expected_degradation = np.stack(
        [np.asarray([1, 2]) if episode % 2 == 0 else np.asarray([2, 1]) for episode in range(EPISODES_PER_ENV)]
    )
    if not np.array_equal(degradation, np.broadcast_to(expected_degradation, degradation.shape)):
        reasons.append("balanced role schedule mismatch")
    if not np.all(pre[:, :, 0, :] == 4) or not np.array_equal(pre[:, :, 1:, :], post[:, :, :-1, :]):
        reasons.append("health reset or transition continuity mismatch")
    keep = actions == KEEP
    expected_service = np.where(keep, pre.astype(np.float64) / 4.0, 0.0)
    expected_post = np.where(
        keep,
        np.maximum(0, pre - degradation[:, :, None, :]),
        4,
    )
    expected_reward = np.minimum(1.0, expected_service.sum(axis=-1))
    if not np.array_equal(service, expected_service):
        reasons.append("service-output formula mismatch")
    if not np.array_equal(post, expected_post):
        reasons.append("health transition formula mismatch")
    if not np.array_equal(block_reward, expected_reward):
        reasons.append("external reward formula mismatch")

    env = arrays["env_rank"]
    episode = arrays["episode_index"]
    check = arrays["check_index"]
    agent = arrays["agent"]
    other = 1 - agent
    reconstructed = np.stack(
        [
            pre[env, episode, check, agent] / 4.0,
            pre[env, episode, check, other] / 4.0,
            degradation[env, episode, agent] / 2.0,
            degradation[env, episode, other] / 2.0,
            (agent == 1).astype(np.float64),
            np.where(agent == 1, actions[env, episode, check, 0], 0),
        ],
        axis=1,
    ).astype(np.float32)
    if not np.array_equal(arrays["context"], reconstructed):
        reasons.append("registered six-field context or prefix sentinel mismatch")
    replay_action = actions[env, episode, check, agent]
    if not np.array_equal(arrays["action"], replay_action):
        reasons.append("behavior action replay mismatch")
    if not np.all(arrays["propensity_renew"] == 0.5):
        reasons.append("stored propensity differs from 0.5")
    observed_probability = np.where(
        arrays["action"] == RENEW,
        arrays["propensity_renew"],
        1.0 - arrays["propensity_renew"],
    )
    inverse_weights = 1.0 / observed_probability
    predicted_delta = arrays["true_q"][:, RENEW] - arrays["true_q"][:, KEEP]
    dr_score = (
        predicted_delta
        + (arrays["action"] == RENEW)
        / arrays["propensity_renew"]
        * (arrays["outcome"] - arrays["true_q"][:, RENEW])
        - (arrays["action"] == KEEP)
        / (1.0 - arrays["propensity_renew"])
        * (arrays["outcome"] - arrays["true_q"][:, KEEP])
    )
    if not np.isfinite(inverse_weights).all():
        reasons.append("inverse-propensity weights are non-finite")
    if not np.isfinite(dr_score).all():
        reasons.append("doubly robust scores are non-finite")
    expected_cluster = env * EPISODES_PER_ENV + episode
    expected_event = expected_cluster * USABLE_CHECKS + check
    if not np.array_equal(arrays["cluster_id"], expected_cluster):
        reasons.append("episode bootstrap cluster key mismatch")
    if not np.array_equal(arrays["event_id"], expected_event):
        reasons.append("same-check event key mismatch")
    if not np.array_equal(arrays["role_d0"], degradation[env, episode, 0]) or not np.array_equal(arrays["role_d1"], degradation[env, episode, 1]):
        reasons.append("row-level role assignment mismatch")
    expected_outcome = np.empty(FOCAL_ROWS, dtype=np.float64)
    for env_rank in range(ROLLOUT_ENVS):
        for episode_index in range(EPISODES_PER_ENV):
            values = three_block_outcomes(block_reward[env_rank, episode_index])
            mask = (env == env_rank) & (episode == episode_index)
            expected_outcome[mask] = values[check[mask]]
    if not np.allclose(arrays["outcome"], expected_outcome, rtol=0.0, atol=1e-12):
        reasons.append("three-block discounted outcome mismatch")
    expected_train_fold = np.where(env <= 7, 1, 0)
    if not np.array_equal(arrays["trained_on_fold"], expected_train_fold):
        reasons.append("cross-fit held-out partition mismatch")
    unique_events, counts = np.unique(arrays["event_id"], return_counts=True)
    if len(unique_events) != USABLE_EVENT_ROWS or not np.all(counts == 2):
        reasons.append("usable checks do not have exactly two focal rows")

    eval_roles, eval_actions = evaluation_schedule()
    expected_eval = run_evaluation_trace(eval_roles, eval_actions)
    if not np.array_equal(arrays["eval_role_assignments"], eval_roles) or not np.array_equal(arrays["eval_actions"], eval_actions):
        reasons.append("registered evaluation RNG schedule mismatch")
    for suffix, expected_name in (
        ("pre_health", "pre_health"),
        ("post_health", "post_health"),
        ("service_output", "service_output"),
        ("block_reward", "block_reward"),
    ):
        if not np.array_equal(arrays[f"eval_{suffix}_before"], expected_eval[expected_name]):
            reasons.append(f"pre-fit evaluation {suffix} mismatch")
        if not np.array_equal(arrays[f"eval_{suffix}_after"], expected_eval[expected_name]):
            reasons.append(f"post-fit evaluation {suffix} mismatch")
    return reasons


def overlap_metrics(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    result: dict[str, Any] = {"groups": {}}
    all_pass = True
    for focal in (0, 1):
        for selected_action, label in ((KEEP, "KEEP"), (RENEW, "RENEW")):
            mask = (arrays["agent"] == focal) & (arrays["action"] == selected_action)
            observed_probability = np.where(
                selected_action == RENEW,
                arrays["propensity_renew"][mask],
                1.0 - arrays["propensity_renew"][mask],
            )
            weights = 1.0 / observed_probability
            ess = float(weights.sum() ** 2 / np.square(weights).sum())
            environment_weights = np.asarray(
                [
                    weights[arrays["env_rank"][mask] == env].sum()
                    for env in range(ROLLOUT_ENVS)
                ],
                dtype=np.float64,
            )
            maximum_share = float(environment_weights.max() / environment_weights.sum())
            passed = bool(ess >= 64.0 and maximum_share <= 0.10)
            all_pass = all_pass and passed
            result["groups"][f"agent_{focal}_{label}"] = {
                "rows": int(mask.sum()),
                "ess": ess,
                "maximum_environment_weight_share": maximum_share,
                "pass": passed,
            }
    result["pass"] = bool(all_pass)
    return result


def scientific_metrics(arrays: dict[str, np.ndarray]) -> dict[str, Any]:
    action = arrays["action"]
    propensity = arrays["propensity_renew"]
    outcome = arrays["outcome"]
    true_q = arrays["true_q"]
    sham_q = arrays["sham_q"]
    cluster_id = arrays["cluster_id"]
    samples = bootstrap_samples()
    observed_probability = np.where(action == RENEW, propensity, 1.0 - propensity)
    weights = 1.0 / observed_probability
    row = np.arange(len(action))
    true_prediction = true_q[row, action]
    sham_prediction = (1.0 - propensity) * sham_q[:, KEEP] + propensity * sham_q[:, RENEW]
    true_error = np.square(outcome - true_prediction)
    sham_error = np.square(outcome - sham_prediction)
    true_wmse, true_boot = bootstrap_weighted_mse(
        true_error, weights, cluster_id, samples
    )
    sham_wmse, sham_boot = bootstrap_weighted_mse(
        sham_error, weights, cluster_id, samples
    )
    ratio = sham_wmse / true_wmse
    ratio_boot = sham_boot / true_boot
    ratio_ci = interval(ratio_boot, ratio)
    ratio_gain_ci = interval(ratio_boot - 1.0, ratio - 1.0)

    delta = true_q[:, RENEW] - true_q[:, KEEP]
    psi = (
        delta
        + (action == RENEW) / propensity * (outcome - true_q[:, RENEW])
        - (action == KEEP) / (1.0 - propensity) * (outcome - true_q[:, KEEP])
    )
    pooled_q25, pooled_q75 = np.quantile(delta, [0.25, 0.75])
    pooled_bottom = delta <= pooled_q25
    pooled_top = delta >= pooled_q75
    ranking_ci = bootstrap_difference(
        psi, pooled_top, pooled_bottom, cluster_id, samples
    )
    m2_pass = bool(
        ratio_gain_ci["lower_95"] > 0.0 and ranking_ci["lower_95"] > 0.0
    )

    agent_sign: dict[str, Any] = {}
    agent_pass = True
    for focal in (0, 1):
        focal_mask = arrays["agent"] == focal
        q25, q75 = np.quantile(delta[focal_mask], [0.25, 0.75])
        bottom = focal_mask & (delta <= q25)
        top = focal_mask & (delta >= q75)
        top_point, top_boot = bootstrap_group_mean(
            psi, top, cluster_id, samples
        )
        bottom_point, bottom_boot = bootstrap_group_mean(
            psi, bottom, cluster_id, samples
        )
        top_ci = interval(top_boot, top_point)
        bottom_ci = interval(bottom_boot, bottom_point)
        passed = bool(top_ci["lower_95"] > 0.0 and bottom_ci["upper_95"] < 0.0)
        agent_pass = agent_pass and passed
        agent_sign[f"agent_{focal}"] = {
            "predicted_delta_q25": float(q25),
            "predicted_delta_q75": float(q75),
            "top_psi": top_ci,
            "bottom_psi": bottom_ci,
            "pass": passed,
        }

    order = np.lexsort((arrays["agent"], arrays["event_id"]))
    event_delta = delta[order].reshape(-1, 2)
    event_cluster = cluster_id[order].reshape(-1, 2)[:, 0]
    event_role_d0 = arrays["role_d0"][order].reshape(-1, 2)[:, 0]
    event_role_d1 = arrays["role_d1"][order].reshape(-1, 2)[:, 0]
    discordance = (
        np.sign(event_delta[:, 0]) != np.sign(event_delta[:, 1])
    ).astype(np.float64)
    all_events = np.ones(len(discordance), dtype=bool)
    discordance_point, discordance_boot = bootstrap_group_mean(
        discordance, all_events, event_cluster, samples
    )
    discordance_ci = interval(discordance_boot, discordance_point)
    pooled_pass = bool(
        discordance_point >= 0.20 and discordance_ci["lower_95"] > 0.10
    )
    role_results: dict[str, Any] = {}
    role_pass = True
    for d0, d1 in ((1, 2), (2, 1)):
        mask = (event_role_d0 == d0) & (event_role_d1 == d1)
        point, boot = bootstrap_group_mean(
            discordance, mask, event_cluster, samples
        )
        ci = interval(boot, point)
        passed = bool(ci["lower_95"] > 0.10)
        role_pass = role_pass and passed
        role_results[f"d0_{d0}_d1_{d1}"] = {**ci, "pass": passed}
    m3_pass = bool(agent_pass and pooled_pass and role_pass)
    return {
        "m2": {
            "true_q_weighted_mse": true_wmse,
            "action_blind_weighted_mse": sham_wmse,
            "wmse_sham_over_true": ratio_ci,
            "wmse_ratio_gain": ratio_gain_ci,
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
            "role_stratified_sign_discordance": role_results,
            "role_stratum_lcb_floor": 0.10,
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
    worker_path = run_root / "seed" / "seed_result.json"
    evidence_path = run_root / "seed" / "r46_hmrv_evidence.npz"
    result_path = run_root / "result" / "r46_hmrv_identifiability.json"
    worker = load_json(worker_path)
    with np.load(evidence_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}

    invalid_reasons = validate_m0(worker, arrays)
    m0 = not invalid_reasons
    overlap = overlap_metrics(arrays)
    scientific = scientific_metrics(arrays)
    m1 = bool(overlap["pass"])
    m2 = bool(scientific["m2"]["pass"])
    m3 = bool(scientific["m3"]["pass"])
    if not m0:
        status = "INVALID_R46_HMRV_WIRING"
        next_action = "repair only the explicit implementation defect and rerun the unchanged contract"
    elif m1 and m2 and m3:
        status = "PASS_R46_HMRV_IDENTIFIABILITY"
        next_action = "authorize only a same-substrate per-agent renewal actor versus shared-sync control"
    else:
        status = "VALID_FAIL_R46_HMRV_SUBSTRATE"
        next_action = (
            "permanently retire the exact HMRV dynamics, three-block estimand, "
            "and positive-control substrate without rescue"
        )
    payload: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "status": status,
        "implementation_valid": m0,
        "invalid_reasons": invalid_reasons,
        "gates": {
            "M0_implementation": m0,
            "M1_overlap": m1,
            "M2_action_specific_informativeness": m2,
            "M3_sign_heterogeneity": m3,
        },
        "contract": {
            "execution_target": "local_cuda",
            "environment_seed": ENVIRONMENT_SEED,
            "behavior_action_seed": BEHAVIOR_ACTION_SEED,
            "evaluation_action_seed": EVAL_ACTION_SEED,
            "rollout_envs": ROLLOUT_ENVS,
            "episodes_per_env": EPISODES_PER_ENV,
            "environment_steps": ENV_STEPS,
            "k0": K0,
            "checks_per_episode": CHECKS_PER_EPISODE,
            "usable_checks_per_episode": USABLE_CHECKS,
            "gamma": GAMMA,
            "critic_epochs": CRITIC_EPOCHS,
            "critic_minibatch": CRITIC_MINIBATCH,
            "critic_steps_per_model": CRITIC_STEPS_PER_MODEL,
            "critic_optimizer_steps_total": CRITIC_TOTAL_STEPS,
            "evaluation_episodes": EVAL_EPISODES,
            "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_cluster": "(env_rank,episode_index)",
        },
        "overlap": overlap,
        "scientific": scientific,
        "implementation": {
            "telemetry": worker.get("telemetry"),
            "collection": worker.get("collection"),
            "critic_training": worker.get("critic_training"),
            "evaluation": worker.get("evaluation"),
            "algorithm_boundary": worker.get("algorithm_boundary"),
        },
        "next_action": next_action,
        "prohibitions": [
            "no seed, data, capacity, threshold, clipping, reward, or environment rescue",
            "no task-specific intrinsic reward or reward shaping",
            "no policy, low-level, skill, or intrinsic update in G0",
            "no S7, open-roster, or variable-N promotion without the registered PASS",
        ],
    }
    atomic_json(result_path, payload)
    print(f"R46 analysis complete: status={status}; result={result_path}")


if __name__ == "__main__":
    main()
