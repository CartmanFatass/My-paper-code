"""Registered ACVC-B1 aggregation and prespecified confidence limits."""

from __future__ import annotations

from collections import Counter
import math
import statistics
from typing import Mapping, Sequence


TWO_SIDED_T_95_DF9 = 2.2621571628540993
ONE_SIDED_T_95_DF9 = 1.8331129326536335


def mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else float("nan")


def t_interval_95(values: Sequence[float]) -> dict[str, float]:
    if len(values) != 10:
        raise ValueError("registered seed-level interval requires exactly ten values")
    center = mean(values)
    se = statistics.stdev(values) / math.sqrt(len(values))
    margin = TWO_SIDED_T_95_DF9 * se
    return {"mean": center, "lower": center - margin, "upper": center + margin, "standard_error": se}


def one_sided_limits_95(values: Sequence[float]) -> dict[str, float]:
    if len(values) != 10:
        raise ValueError("registered seed-level limit requires exactly ten values")
    center = mean(values)
    se = statistics.stdev(values) / math.sqrt(len(values))
    margin = ONE_SIDED_T_95_DF9 * se
    return {"mean": center, "lower": center - margin, "upper": center + margin, "standard_error": se}


class ArmAccumulator:
    def __init__(self) -> None:
        self.scenes = 0
        self.event_scenes = 0
        self.clean_scenes = 0
        self.transitions = 0
        self.event_reward = 0.0
        self.clean_reward = 0.0
        self.false_complete = 0
        self.d_joint = 0
        self.event_clean_harm_sum = 0.0
        self.event_clean_targets = 0
        self.all_clean_harm_sum = 0.0
        self.all_clean_targets = 0
        self.components: Counter[str] = Counter()

    def add(self, row: Mapping[str, object]) -> None:
        self.scenes += 1
        self.transitions += int(row["transitions"])
        components = row["reward_components"]
        for key, value in components.items():  # type: ignore[union-attr]
            self.components[str(key)] += float(value)
        target_returns = [float(value) for value in row["target_returns"]]  # type: ignore[union-attr]
        if bool(row["event"]):
            self.event_scenes += 1
            self.event_reward += float(row["scene_reward"])
            self.false_complete += int(bool(row["false_complete"]))
            self.d_joint += int(bool(row["d_joint"]))
            true_target = int(row["true_target"])
            for index, value in enumerate(target_returns):
                if index != true_target:
                    self.event_clean_harm_sum += 1.0 - value
                    self.event_clean_targets += 1
        else:
            self.clean_scenes += 1
            self.clean_reward += float(row["scene_reward"])
            for value in target_returns:
                self.all_clean_harm_sum += 1.0 - value
                self.all_clean_targets += 1

    def summary(self) -> dict[str, object]:
        return {
            "scenes": self.scenes,
            "event_scenes": self.event_scenes,
            "all_clean_scenes": self.clean_scenes,
            "transitions": self.transitions,
            "mean_event_reward": self.event_reward / self.event_scenes,
            "mean_all_clean_reward": self.clean_reward / self.clean_scenes,
            "invalid_false_complete_rate": self.false_complete / self.event_scenes,
            "d_joint_rate": self.d_joint / self.event_scenes,
            "clean_harm_event_clean_targets": self.event_clean_harm_sum / self.event_clean_targets,
            "clean_harm_all_clean_scenes": self.all_clean_harm_sum / self.all_clean_targets,
            "reward_component_totals": dict(self.components),
        }


def analyze_registered(seed_rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if len(seed_rows) != 10:
        raise ValueError("registered analysis requires ten seed rows")
    correct = [row["arms"]["LEARN-CORRECT"] for row in seed_rows]  # type: ignore[index]
    perm = [row["arms"]["LEARN-PERM"] for row in seed_rows]  # type: ignore[index]
    det = [row["arms"]["DET-BOUND"] for row in seed_rows]  # type: ignore[index]
    auth = [row["arms"]["AUTH-PROBE"] for row in seed_rows]  # type: ignore[index]
    tau = [float(a["mean_event_reward"]) - float(b["mean_event_reward"]) for a, b in zip(correct, perm)]
    correct_det = [float(a["mean_event_reward"]) - float(b["mean_event_reward"]) for a, b in zip(correct, det)]
    d_perm = [float(a["d_joint_rate"]) - float(b["d_joint_rate"]) for a, b in zip(correct, perm)]
    d_auth = [float(a["d_joint_rate"]) - float(b["d_joint_rate"]) for a, b in zip(correct, auth)]
    result = {
        "tau_neg": {"seed_values": tau, "student_t_95": t_interval_95(tau)},
        "correct_minus_det_bound": {"seed_values": correct_det, "student_t_95": t_interval_95(correct_det)},
        "correct_false_complete": one_sided_limits_95([float(row["invalid_false_complete_rate"]) for row in correct]),
        "correct_clean_harm_all_clean": one_sided_limits_95([float(row["clean_harm_all_clean_scenes"]) for row in correct]),
        "correct_clean_harm_event_clean_targets": one_sided_limits_95([float(row["clean_harm_event_clean_targets"]) for row in correct]),
        "correct_d_joint": one_sided_limits_95([float(row["d_joint_rate"]) for row in correct]),
        "d_joint_gap_correct_minus_perm": {"seed_values": d_perm, **one_sided_limits_95(d_perm)},
        "d_joint_gap_correct_minus_auth_probe": {"seed_values": d_auth, **one_sided_limits_95(d_auth)},
    }
    criteria = {
        "tau_mean_at_least_0_40": result["tau_neg"]["student_t_95"]["mean"] >= 0.40,  # type: ignore[index]
        "tau_lower_above_0_25": result["tau_neg"]["student_t_95"]["lower"] > 0.25,  # type: ignore[index]
        "correct_false_complete_upper_below_0_01": result["correct_false_complete"]["upper"] < 0.01,  # type: ignore[index]
        "correct_clean_harm_all_clean_mean_at_most_0_02": result["correct_clean_harm_all_clean"]["mean"] <= 0.02,  # type: ignore[index]
        "correct_clean_harm_all_clean_upper_below_0_05": result["correct_clean_harm_all_clean"]["upper"] < 0.05,  # type: ignore[index]
        "correct_clean_harm_event_mean_at_most_0_02": result["correct_clean_harm_event_clean_targets"]["mean"] <= 0.02,  # type: ignore[index]
        "correct_clean_harm_event_upper_below_0_05": result["correct_clean_harm_event_clean_targets"]["upper"] < 0.05,  # type: ignore[index]
        "correct_d_joint_mean_at_least_0_90": result["correct_d_joint"]["mean"] >= 0.90,  # type: ignore[index]
        "d_joint_gap_perm_lower_above_0_40": result["d_joint_gap_correct_minus_perm"]["lower"] > 0.40,  # type: ignore[index]
        "d_joint_gap_auth_lower_above_0_40": result["d_joint_gap_correct_minus_auth_probe"]["lower"] > 0.40,  # type: ignore[index]
        "correct_minus_det_lower_above_minus_0_05": result["correct_minus_det_bound"]["student_t_95"]["lower"] > -0.05,  # type: ignore[index]
    }
    result["prespecified_criteria"] = criteria
    result["all_prespecified_criteria_hold"] = all(criteria.values())
    return result

