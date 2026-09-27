"""Bounded one-UAV transit holds scored by native snapshot delivered service."""

from __future__ import annotations

import copy

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import (
    HeuristicController,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    LayoutHeuristic,
    HeuristicParams,
    variant,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy,
    own_positions,
)


PREDICTION_STEPS = (5, 10)
BASELINE_HOLD_ID = -1
H1_CENTRAL_10 = variant("H1", information="central", replan_period=10)


def battery_tail_readings(
    battery: np.ndarray,
    *,
    reserve_ratio: float,
    service_cutoff_ratio: float,
) -> dict[str, float]:
    """Return fixed-reserve and native service-cutoff fractions from post-step ratios."""
    values = np.asarray(battery, dtype=np.float64)
    thresholds = np.asarray([reserve_ratio, service_cutoff_ratio], dtype=np.float64)
    if (values.ndim != 2 or not values.size or not np.isfinite(values).all()
            or np.any((values < 0.0) | (values > 1.0))):
        raise ValueError("battery trace must be a nonempty finite (steps, UAVs) ratio array")
    if (not np.isfinite(thresholds).all()
            or np.any((thresholds < 0.0) | (thresholds > 1.0))):
        raise ValueError("battery thresholds must be finite ratios in [0, 1]")
    return {
        "fixed_reserve_ratio": float(thresholds[0]),
        "service_cutoff_ratio": float(thresholds[1]),
        "below_fixed_reserve_uav_step_fraction": float(np.mean(values <= thresholds[0])),
        "service_cutoff_uav_step_fraction": float(np.mean(values <= thresholds[1])),
    }


def project_h1_positions(
    own_xyz: np.ndarray,
    targets_xy: np.ndarray,
    available: np.ndarray,
    params: HeuristicParams,
    step_count: int,
    area_size_m: float,
) -> np.ndarray:
    """Nominal H1 capped-speed positions after ``step_count`` decisions.

    UAVs without a target or without current service availability remain at their
    observed position in this forecast. Vertical altitude control remains the H1
    policy even when a candidate holds a UAV's horizontal position.
    """
    own = np.asarray(own_xyz, dtype=np.float64)
    targets = np.asarray(targets_xy, dtype=np.float64)
    available = np.asarray(available, dtype=bool)
    if own.ndim != 2 or own.shape[1] != 3:
        raise ValueError("own_xyz must have shape (n_uavs, 3)")
    if targets.shape != (len(own), 2) or available.shape != (len(own),):
        raise ValueError("target and availability shapes must match own_xyz")
    if int(step_count) < 0 or not np.isfinite(own).all():
        raise ValueError("projection inputs must be finite and step_count nonnegative")

    projected = own.copy()
    elapsed = int(step_count) * float(params.time_step_s)
    for uav, target in enumerate(targets):
        if not available[uav] or not np.isfinite(target).all():
            continue
        delta = target - own[uav, :2]
        distance = float(np.linalg.norm(delta))
        travel = min(distance, float(params.cruise_mps) * elapsed)
        if distance > 0.0:
            projected[uav, :2] = own[uav, :2] + delta * (travel / distance)
        projected[uav, :2] = np.clip(projected[uav, :2], 0.0, float(area_size_m))
        vertical_delta = float(params.height_m) - own[uav, 2]
        vertical_travel = float(np.clip(
            vertical_delta,
            -float(params.vertical_cap_mps) * elapsed,
            float(params.vertical_cap_mps) * elapsed,
        ))
        projected[uav, 2] = own[uav, 2] + vertical_travel
    return projected


def hold_plan_candidates(
    base_targets_xy: np.ndarray,
    own_xy: np.ndarray,
    available: np.ndarray,
    modes: np.ndarray,
) -> list[tuple[int, np.ndarray]]:
    """Return all-move first, then one current-position hold per movable UAV."""
    targets = np.asarray(base_targets_xy, dtype=np.float64)
    own = np.asarray(own_xy, dtype=np.float64)
    available = np.asarray(available, dtype=bool)
    modes = np.asarray(modes, dtype=bool)
    if targets.ndim != 2 or targets.shape[1] != 2 or own.shape != targets.shape:
        raise ValueError("target and own xy arrays must have matching (n_uavs, 2) shape")
    if available.shape != (len(targets),) or modes.shape != (len(targets),):
        raise ValueError("availability and mode arrays must match n_uavs")
    candidates = [(BASELINE_HOLD_ID, targets.copy())]
    for uav in range(len(targets)):
        if modes[uav] or not available[uav] or not np.isfinite(targets[uav]).all():
            continue
        hold_targets = targets.copy()
        hold_targets[uav] = own[uav]
        candidates.append((uav, hold_targets))
    return candidates


def choose_plan(scores: list[tuple[int, float]]) -> int:
    """Select the strictly highest score; baseline-first ordering resolves ties."""
    if not scores or scores[0][0] != BASELINE_HOLD_ID:
        raise ValueError("scores must start with the all-move baseline")
    best_id, best_score = scores[0]
    if not np.isfinite(best_score):
        raise ValueError("candidate scores must be finite")
    for hold_id, score in scores[1:]:
        if not np.isfinite(score):
            raise ValueError("candidate scores must be finite")
        if score > best_score:
            best_id, best_score = hold_id, score
    return int(best_id)


class TransitHoldHeuristic(LayoutHeuristic):
    """H1 with a finite service-scored one-UAV hold choice at its replans."""

    def __init__(self, params: HeuristicParams, raw_env):
        if params.information != "central":
            raise ValueError("transit-hold scoring requires H_central plan inputs")
        if raw_env.routing_protocol != "widest_path":
            raise ValueError("transit-hold snapshot scorer is defined for widest_path S2")
        super().__init__(params)
        self.raw_env = raw_env
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.h1_targets_xy = self.targets_xy.copy()
        self.decision_records: list[dict] = []
        self.service_snapshot_calls = 0

    @staticmethod
    def _service_qos_at_snapshot(raw_env, plan_inputs, own_xyz, batteries) -> float:
        """Use native radio/routing/delivery code on an isolated legal snapshot.

        The association starts fresh at each point, avoiding access to hidden live
        serving-set history. Current battery values come from legal own observations.
        The input user/BS positions are the central H1 snapshot; users are otherwise
        held fixed in this short-horizon proxy.
        """
        shadow = copy.deepcopy(raw_env)
        users_xy = np.asarray(plan_inputs["users_xy"], dtype=np.float64)
        bs_xy = np.asarray(plan_inputs["bs_xy"], dtype=np.float64).reshape(-1, 2)
        positions = np.asarray(own_xyz, dtype=np.float64)
        batteries = np.asarray(batteries, dtype=np.float64)
        if users_xy.shape != (shadow.n_users, 2) or bs_xy.shape != (shadow.n_ground_bs, 2):
            raise ValueError("legal central user/BS snapshot shape differs from S2")
        if positions.shape != (shadow.n_uavs, 3) or batteries.shape != (shadow.n_uavs,):
            raise ValueError("legal own position/battery snapshot shape differs from S2")

        shadow.user_positions[:, :2] = users_xy
        shadow.ground_bs_positions[:, :2] = bs_xy
        shadow.uav_positions = positions.copy()
        shadow.uav_battery_ratios = batteries.copy()
        if hasattr(shadow, "user_serving_sets"):
            shadow.user_serving_sets = [[] for _ in range(shadow.n_users)]
        if hasattr(shadow, "user_serving_uav"):
            shadow.user_serving_uav.fill(-1)
        shadow.connections.fill(False)
        shadow._relay_geometry_state = None
        shadow._step_communication_cache = None

        shadow._update_channel_state()
        shadow._update_uav_connections()
        shadow._compute_routing_paths()
        rates_bps, _, _ = shadow._calculate_end_to_end_user_rates()
        demand_bps = np.asarray(shadow._current_user_qos_demand_bps(), dtype=np.float64)
        if demand_bps.shape != (shadow.n_users,) or np.any(demand_bps <= 0.0):
            raise ValueError("native S2 demand vector must be positive and per-user")
        score = float(np.mean(np.clip(rates_bps / demand_bps, 0.0, 1.0)))
        if not np.isfinite(score):
            raise FloatingPointError("native snapshot service score is non-finite")
        return score

    def plan(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> dict:
        # A temporary hold changes execution, not H1's target-continuation memory.
        # Replanning still uses the latest actual positions in observations.
        self.targets_xy = self.h1_targets_xy.copy()
        base_plan = super().plan(observations, modes, plan_inputs)
        base_targets = self.targets_xy.copy()
        self.h1_targets_xy = base_targets.copy()
        own_xyz = own_positions(observations, self.layout)
        energy = own_energy(observations, self.layout)
        mode_array = np.asarray(modes, dtype=bool)
        fallback = None
        if np.any(mode_array):
            fallback = "return_shield_active"
        elif np.any(energy["return_margin"] <= PRODUCTION_PARAMS.enter_margin):
            fallback = "return_shield_entry"

        if fallback is not None:
            self.decision_records.append({
                "step": int(self.calls), "selected_hold_uav": BASELINE_HOLD_ID,
                "candidate_count": 1, "snapshot_calls": 0, "fallback": fallback,
                "candidate_scores": [],
                "h1_targets_xy": base_targets.copy(),
            })
            base_plan["transit_hold"] = {"selected_uav": BASELINE_HOLD_ID,
                                          "candidate_count": 1, "fallback": fallback}
            return base_plan

        if plan_inputs is None:
            raise ValueError("H_central plan inputs are required for service scoring")
        candidates = hold_plan_candidates(
            base_targets, own_xyz[:, :2], energy["available"], mode_array
        )
        if len(candidates) == 1:
            fallback = "no_movable_assigned_member"
            self.decision_records.append({
                "step": int(self.calls), "selected_hold_uav": BASELINE_HOLD_ID,
                "candidate_count": 1, "snapshot_calls": 0, "fallback": fallback,
                "candidate_scores": [],
                "h1_targets_xy": base_targets.copy(),
            })
            base_plan["transit_hold"] = {"selected_uav": BASELINE_HOLD_ID,
                                          "candidate_count": 1, "fallback": fallback}
            return base_plan

        q0 = self._service_qos_at_snapshot(
            self.raw_env, plan_inputs, own_xyz, energy["battery"]
        )
        self.service_snapshot_calls += 1
        scored = []
        score_records = []
        for hold_id, targets in candidates:
            point_scores = []
            for step_count in PREDICTION_STEPS:
                projected = project_h1_positions(
                    own_xyz, targets, energy["available"], self.params,
                    step_count, self.layout.area_size_m,
                )
                q = self._service_qos_at_snapshot(
                    self.raw_env, plan_inputs, projected, energy["battery"]
                )
                self.service_snapshot_calls += 1
                point_scores.append(q)
            integrated = float((q0 + 2.0 * point_scores[0] + point_scores[1]) / 4.0)
            scored.append((hold_id, integrated))
            score_records.append({
                "hold_uav": int(hold_id), "qos_0": float(q0),
                "qos_5": float(point_scores[0]), "qos_10": float(point_scores[1]),
                "integrated_qos": integrated,
            })

        selected = choose_plan(scored)
        selected_targets = next(targets for hold_id, targets in candidates
                                if hold_id == selected)
        self.targets_xy = selected_targets.copy()
        base_plan["targets"] = self.targets_xy.copy()
        base_plan["transit_hold"] = {
            "selected_uav": int(selected), "candidate_count": len(candidates),
            "snapshot_calls": 1 + 2 * len(candidates), "fallback": None,
            "candidate_scores": score_records,
        }
        self.last_plan = base_plan
        self.decision_records.append({
            "step": int(self.calls), "selected_hold_uav": int(selected),
            "candidate_count": len(candidates), "snapshot_calls": 1 + 2 * len(candidates),
            "fallback": None, "candidate_scores": score_records,
            "h1_targets_xy": base_targets.copy(),
        })
        return base_plan


class TransitHoldController(HeuristicController):
    """Controller adapter preserving H_central@10 replan and action semantics."""

    def __init__(self, env):
        super().__init__(H1_CENTRAL_10, env=env)
        self.heuristic = TransitHoldHeuristic(self.heuristic.params, env.env)
