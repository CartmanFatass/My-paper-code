from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

import numpy as np

from .config import SCORED_REGIMES, TARGET_REGIMES
from .evaluation import ScoredEpisode

DIRECT_VALUE_THRESHOLDS = {
    "performance_delta_task_lcb_97_5": 0.015,
    "failure_delta_fail_lcb_97_5": 0.05,
    "failure_route_delta_task_lcb_95": -0.005,
    "target_and_seen_nonharm_lcb_98_75": -0.005,
}
MECHANISM_THRESHOLDS = {
    "delta_comp_real_lcb_95": 0.10,
    "delta_pred_real_lcb_95": 0.05,
    "delta_rob_lcb_95": 0.010,
    "delta_spec_lcb_95": 0.005,
}
ADVERSE_THRESHOLDS = {
    "family_size": 12,
    "per_estimand_confidence": 1.0 - 0.05 / 12.0,
    "reward_upper_bound": -0.005,
    "failure_upper_bound": -0.05,
}
DELETION_UPPER_THRESHOLDS = {
    "target_reward_each_ub_95": 0.010,
    "target_failure_each_ub_95": 0.03,
    "delta_spec_ub_95": 0.005,
    "word_reward_each_ub_95": 0.010,
}


def seed_summary(values: Sequence[float]) -> dict[str, float | int]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (8,):
        raise ValueError("registered inference requires exactly eight seed-level values")
    if not np.all(np.isfinite(array)):
        raise ValueError("nonfinite seed-level estimand")
    sample_sd = np.std(array, axis=None, dtype=np.float64, ddof=1)
    return {
        "n": 8,
        "mean": float(np.mean(array, dtype=np.float64)),
        "sample_standard_deviation": float(sample_sd),
        "standard_error": float(sample_sd / np.sqrt(np.float64(8.0))),
    }


def one_sided_t_bound(
    values: Sequence[float], confidence: float, *, side: str,
) -> dict[str, float | int | str]:
    from scipy.stats import t

    summary = seed_summary(values)
    critical = float(t.ppf(confidence, df=7))
    displacement = critical * float(summary["standard_error"])
    mean = float(summary["mean"])
    if side == "lower":
        bound = mean - displacement
    elif side == "upper":
        bound = mean + displacement
    else:
        raise ValueError("side must be lower or upper")
    return {**summary, "df": 7, "confidence": confidence, "side": side, "bound": bound}


def paired_sign_randomization(values: Sequence[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (8,):
        raise ValueError("registered sign randomization requires eight paired seed effects")
    observed = float(np.mean(array, dtype=np.float64))
    permutation_means = np.asarray([
        np.mean(array * np.asarray(signs, dtype=np.float64), dtype=np.float64)
        for signs in itertools.product((-1.0, 1.0), repeat=8)
    ], dtype=np.float64)
    positive_p = float(np.count_nonzero(permutation_means >= observed) / 256.0)
    negative_p = float(np.count_nonzero(permutation_means <= observed) / 256.0)
    return {
        "permutations": 256,
        "observed_mean": observed,
        "one_sided_positive_p": positive_p,
        "one_sided_negative_p": negative_p,
        "two_sided_p": min(1.0, 2.0 * min(positive_p, negative_p)),
    }


def _effect(values: Sequence[float], bounds: Sequence[tuple[str, float, str]]) -> dict[str, object]:
    return {
        "seed_values": [float(value) for value in values],
        "summary": seed_summary(values),
        "sign_randomization": paired_sign_randomization(values),
        "bounds": {
            name: one_sided_t_bound(values, confidence, side=side)
            for name, confidence, side in bounds
        },
    }


def analysis_contract() -> dict[str, object]:
    return {
        "unit_of_inference": "eight paired algorithm-seed effects",
        "episodes_are_training_replicates": False,
        "direct_value_thresholds": DIRECT_VALUE_THRESHOLDS,
        "mechanism_thresholds": MECHANISM_THRESHOLDS,
        "adverse": ADVERSE_THRESHOLDS,
        "deletion_upper_thresholds": DELETION_UPPER_THRESHOLDS,
        "adverse_precedes_positive": True,
        "real_only_conclusion_bearing": [
            "oracle_headroom", "composition_defect", "true_prediction_error",
            "actor_disagreement", "subgroup_bounds",
        ],
        "sham_and_pooled_role": "control_or_descriptive_only",
    }


def _selected(
    rows: Sequence[ScoredEpisode], seed: int, dynamics_class: str, regime: str, arm: str,
) -> list[ScoredEpisode]:
    result = [
        row for row in rows if row.algorithm_seed == seed
        and row.dynamics_class == dynamics_class and row.regime == regime and row.arm == arm
    ]
    if len(result) != 16:
        raise ValueError(
            f"seed={seed} class={dynamics_class} regime={regime} arm={arm} "
            f"has {len(result)} rows, expected 16"
        )
    return sorted(result, key=lambda row: row.episode_index)


def _arm_episode_summary(rows: Sequence[ScoredEpisode]) -> dict[str, object]:
    mean_fields = (
        "normalized_return", "failure", "collision_steps", "clipping_steps",
        "position_error_rms", "worst_agent_position_error", "velocity_error_rms",
        "joint_action_changes", "scalar_action_changes", "energy_proxy",
        "boundary_latency_seconds", "boundary_count", "boundary_message_count",
    )
    minimum_gaps = sorted(float(row.minimum_gap) for row in rows)
    tail_count = max(1, int(math.ceil(0.10 * len(minimum_gaps))))
    return {
        **{name: float(np.mean([getattr(row, name) for row in rows], dtype=np.float64))
           for name in mean_fields},
        "collision_probability": float(np.mean(
            [row.collision_steps > 0 for row in rows], dtype=np.float64,
        )),
        "clipping_probability": float(np.mean(
            [row.clipping_steps > 0 for row in rows], dtype=np.float64,
        )),
        "minimum_gap_mean": float(np.mean(minimum_gaps, dtype=np.float64)),
        "minimum_gap_lower_tail_cvar_10": float(np.mean(minimum_gaps[:tail_count], dtype=np.float64)),
        "minimum_gap_cvar_tail_count": tail_count,
        "episode_values": {
            "normalized_return": [float(row.normalized_return) for row in rows],
            "failure": [int(row.failure) for row in rows],
            "minimum_gap": [float(row.minimum_gap) for row in rows],
        },
    }


def scored_seed_effects(rows: Sequence[ScoredEpisode]) -> dict[str, object]:
    if not rows:
        raise ValueError("complete scored rows are required")
    seeds = sorted({row.algorithm_seed for row in rows})
    if seeds != list(range(8)):
        raise ValueError("registered analysis requires algorithm seeds 0..7")
    by_seed: dict[str, object] = {}
    delta_j: dict[str, list[float]] = {regime: [] for regime in SCORED_REGIMES}
    delta_fail: dict[str, list[float]] = {regime: [] for regime in SCORED_REGIMES}
    delta_task: list[float] = []
    delta_fail_target: list[float] = []
    delta_spec: list[float] = []
    delta_rob: list[float] = []
    word_effects: dict[int, list[float]] = {row: [] for row in range(4)}
    for seed in seeds:
        seed_report: dict[str, object] = {}
        class_effect_cache: dict[str, dict[str, dict[str, float]]] = {}
        arm_return_cache: dict[str, dict[str, float]] = {
            arm: {} for arm in ("SCDMP", "SCDMP-NOCOMP")
        }
        for dynamics_class in ("REAL", "SHAM"):
            class_report: dict[str, object] = {}
            class_effect_cache[dynamics_class] = {}
            for regime in SCORED_REGIMES:
                arm_rows = {
                    arm: _selected(rows, seed, dynamics_class, regime, arm)
                    for arm in ("SCDMP", "SCDMP-NOCOMP")
                }
                d_j = float(np.mean([
                    left.normalized_return - right.normalized_return
                    for left, right in zip(arm_rows["SCDMP"], arm_rows["SCDMP-NOCOMP"])
                ], dtype=np.float64))
                d_failure = float(np.mean([
                    right.failure - left.failure
                    for left, right in zip(arm_rows["SCDMP"], arm_rows["SCDMP-NOCOMP"])
                ], dtype=np.float64))
                class_effect_cache[dynamics_class][regime] = {"d_J": d_j, "d_fail": d_failure}
                per_word: dict[str, object] = {}
                for word_row in range(4):
                    word_arm_rows = {
                        arm: [row for row in arm_rows[arm] if row.initial_word_row == word_row]
                        for arm in arm_rows
                    }
                    if any(len(items) != 4 for items in word_arm_rows.values()):
                        raise ValueError("each class/regime/arm initial-word subgroup needs four episodes")
                    per_word[str(word_row)] = {
                        "d_J": float(np.mean([
                            left.normalized_return - right.normalized_return
                            for left, right in zip(
                                word_arm_rows["SCDMP"], word_arm_rows["SCDMP-NOCOMP"]
                            )
                        ], dtype=np.float64)),
                        "d_fail": float(np.mean([
                            right.failure - left.failure
                            for left, right in zip(
                                word_arm_rows["SCDMP"], word_arm_rows["SCDMP-NOCOMP"]
                            )
                        ], dtype=np.float64)),
                        "arms": {
                            arm: _arm_episode_summary(items)
                            for arm, items in word_arm_rows.items()
                        },
                    }
                class_report[regime] = {
                    "d_J": d_j, "d_fail": d_failure,
                    "arms": {arm: _arm_episode_summary(arm_rows[arm]) for arm in arm_rows},
                    "by_initial_word_row": per_word,
                }
                if dynamics_class == "REAL":
                    delta_j[regime].append(d_j)
                    delta_fail[regime].append(d_failure)
                    for arm in arm_rows:
                        arm_return_cache[arm][regime] = float(np.mean(
                            [episode.normalized_return for episode in arm_rows[arm]], dtype=np.float64,
                        ))
            seed_report[dynamics_class] = class_report
        real_target = float(np.mean([
            class_effect_cache["REAL"][regime]["d_J"] for regime in TARGET_REGIMES
        ], dtype=np.float64))
        sham_target = float(np.mean([
            class_effect_cache["SHAM"][regime]["d_J"] for regime in TARGET_REGIMES
        ], dtype=np.float64))
        fail_target = float(np.mean([
            class_effect_cache["REAL"][regime]["d_fail"] for regime in TARGET_REGIMES
        ], dtype=np.float64))
        gap = {
            arm: float(np.mean([arm_return_cache[arm][r] for r in SCORED_REGIMES[:2]])
                       - np.mean([arm_return_cache[arm][r] for r in TARGET_REGIMES]))
            for arm in arm_return_cache
        }
        seed_word: dict[str, float] = {}
        for word_row in range(4):
            regime_effects = []
            for regime in TARGET_REGIMES:
                paired = []
                for arm in ("SCDMP", "SCDMP-NOCOMP"):
                    arm_rows = _selected(rows, seed, "REAL", regime, arm)
                    chosen = [row for row in arm_rows if row.episode_index % 4 == word_row]
                    if len(chosen) != 4:
                        raise ValueError("REAL word subgroup must have four episodes")
                    paired.append(float(np.mean([row.normalized_return for row in chosen])))
                regime_effects.append(paired[0] - paired[1])
            value = float(np.mean(regime_effects, dtype=np.float64))
            seed_word[str(word_row)] = value
            word_effects[word_row].append(value)
        delta_task.append(real_target)
        delta_fail_target.append(fail_target)
        delta_spec.append(real_target - sham_target)
        delta_rob.append(gap["SCDMP-NOCOMP"] - gap["SCDMP"])
        seed_report["derived"] = {
            "Delta_task": real_target, "Delta_fail_target_mean": fail_target,
            "Delta_spec": real_target - sham_target, "Gap_by_arm": gap,
            "Delta_rob": gap["SCDMP-NOCOMP"] - gap["SCDMP"],
            "d_word": seed_word,
        }
        by_seed[str(seed)] = seed_report
    return {
        "by_seed": by_seed,
        "seed_vectors": {
            "Delta_J_REAL": delta_j, "Delta_fail_REAL": delta_fail,
            "Delta_task": delta_task, "Delta_fail_target_mean": delta_fail_target,
            "Delta_spec": delta_spec, "Delta_rob": delta_rob,
            "Delta_J_word_REAL": {str(key): value for key, value in word_effects.items()},
        },
    }


def _audit_seed_vectors(audits: Sequence[dict[str, object]]) -> dict[str, object]:
    if [int(item["algorithm_seed"]) for item in audits] != list(range(8)):
        raise ValueError("audit summaries must be in seed order 0..7")
    vectors: dict[str, object] = {
        "D_comp": {arm: {cls: [] for cls in ("REAL", "SHAM", "POOLED")}
                   for arm in ("SCDMP", "SCDMP-NOCOMP")},
        "E_pred": {arm: {cls: [] for cls in ("REAL", "SHAM", "POOLED")}
                  for arm in ("SCDMP", "SCDMP-NOCOMP")},
        "actor_disagreement": {cls: [] for cls in ("REAL", "SHAM", "POOLED")},
        "headroom_fraction": {arm: {cls: [] for cls in ("REAL", "SHAM", "POOLED")}
                              for arm in ("SCDMP", "SCDMP-NOCOMP")},
        "headroom_regret": {arm: {cls: [] for cls in ("REAL", "SHAM", "POOLED")}
                            for arm in ("SCDMP", "SCDMP-NOCOMP")},
        "score_sensitivity": {arm: {cls: [] for cls in ("REAL", "SHAM", "POOLED")}
                              for arm in ("SCDMP", "SCDMP-NOCOMP")},
    }
    for audit in audits:
        for arm in ("SCDMP", "SCDMP-NOCOMP"):
            arm_report = audit["arms"][arm]  # type: ignore[index]
            for cls in ("REAL", "SHAM", "POOLED"):
                report = arm_report["by_class"][cls]
                vectors["D_comp"][arm][cls].append(report["D_comp"])  # type: ignore[index]
                vectors["E_pred"][arm][cls].append(report["E_pred"])  # type: ignore[index]
                vectors["headroom_fraction"][arm][cls].append(report["oracle_headroom_fraction_ge_0_02"])  # type: ignore[index]
                vectors["headroom_regret"][arm][cls].append(report["oracle_mean_regret_per_step"])  # type: ignore[index]
                vectors["score_sensitivity"][arm][cls].append(report["candidate_score_sensitivity_fraction"])  # type: ignore[index]
        for cls in ("REAL", "SHAM", "POOLED"):
            vectors["actor_disagreement"][cls].append(audit["actor_disagreement"][cls])  # type: ignore[index]
    vectors["Delta_comp_REAL"] = [
        right - left for right, left in zip(
            vectors["D_comp"]["SCDMP-NOCOMP"]["REAL"],  # type: ignore[index]
            vectors["D_comp"]["SCDMP"]["REAL"],  # type: ignore[index]
        )
    ]
    vectors["Delta_pred_REAL"] = [
        right - left for right, left in zip(
            vectors["E_pred"]["SCDMP-NOCOMP"]["REAL"],  # type: ignore[index]
            vectors["E_pred"]["SCDMP"]["REAL"],  # type: ignore[index]
        )
    ]
    return vectors


def complete_inference(
    scored_rows: Sequence[ScoredEpisode], audits: Sequence[dict[str, object]],
) -> dict[str, object]:
    scored = scored_seed_effects(scored_rows)
    vectors = scored["seed_vectors"]
    audit_vectors = _audit_seed_vectors(audits)
    conf_adverse = float(ADVERSE_THRESHOLDS["per_estimand_confidence"])
    regime_reports: dict[str, object] = {}
    adverse_reward: list[dict[str, object]] = []
    adverse_failure: list[dict[str, object]] = []
    for regime in SCORED_REGIMES:
        reward_values = vectors["Delta_J_REAL"][regime]
        failure_values = vectors["Delta_fail_REAL"][regime]
        reward = _effect(reward_values, (
            ("lower_98_75", 0.9875, "lower"),
            ("upper_95", 0.95, "upper"),
            ("adverse_upper", conf_adverse, "upper"),
        ))
        failure = _effect(failure_values, (
            ("upper_95", 0.95, "upper"),
            ("adverse_upper", conf_adverse, "upper"),
        ))
        regime_reports[regime] = {"Delta_J": reward, "Delta_fail": failure}
        adverse_reward.append({
                "estimand": f"Delta_J({regime})", "kind": "reward",
                "upper_bound": reward["bounds"]["adverse_upper"]["bound"],
                "harm_margin": -0.005,
                "strictly_below_margin": reward["bounds"]["adverse_upper"]["bound"] < -0.005,
            })
        adverse_failure.append({
                "estimand": f"Delta_fail({regime})", "kind": "failure",
                "upper_bound": failure["bounds"]["adverse_upper"]["bound"],
                "harm_margin": -0.05,
                "strictly_below_margin": failure["bounds"]["adverse_upper"]["bound"] < -0.05,
            })
    adverse = adverse_reward + adverse_failure
    word_reports = {
        str(word_row): _effect(values, (("upper_95", 0.95, "upper"),))
        for word_row, values in vectors["Delta_J_word_REAL"].items()
    }
    main = {
        "Delta_task": _effect(vectors["Delta_task"], (
            ("lower_97_5", 0.975, "lower"), ("lower_95", 0.95, "lower"),
        )),
        "Delta_fail_target_mean": _effect(
            vectors["Delta_fail_target_mean"], (("lower_97_5", 0.975, "lower"),)
        ),
        "Delta_rob": _effect(vectors["Delta_rob"], (("lower_95", 0.95, "lower"),)),
        "Delta_spec": _effect(vectors["Delta_spec"], (
            ("lower_95", 0.95, "lower"), ("upper_95", 0.95, "upper"),
        )),
        "Delta_comp_REAL": _effect(
            audit_vectors["Delta_comp_REAL"], (("lower_95", 0.95, "lower"),)
        ),
        "Delta_pred_REAL": _effect(
            audit_vectors["Delta_pred_REAL"], (("lower_95", 0.95, "lower"),)
        ),
    }
    return {
        "contract": analysis_contract(),
        "scored": scored,
        "audit_seed_vectors": audit_vectors,
        "main_estimands": main,
        "regime_estimands": regime_reports,
        "real_word_subgroups": word_reports,
        "adverse_family": {
            "count": len(adverse), "expected_count": 12,
            "per_estimand_confidence": conf_adverse,
            "members": adverse,
            "triggering_members": [item["estimand"] for item in adverse if item["strictly_below_margin"]],
        },
        "interpretation": None,
        "interpretation_owner": "EM_semigroup_consistent_duration_model_policy_after_CM_acceptance",
    }
