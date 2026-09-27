"""One-step scoring with the B04 hold neighborhood and ten-step commitment."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    BASELINE_HOLD_ID,
    TransitHoldController,
    TransitHoldHeuristic,
    choose_plan,
    hold_plan_candidates,
    project_h1_positions,
)
from experiments.candidates.energy_relay_benchmark.b01.feedback import PRODUCTION_PARAMS
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic
from experiments.candidates.energy_relay_benchmark.b01.observation import own_energy, own_positions


class OneStepHoldHeuristic(TransitHoldHeuristic):
    """Change only the scoring rule; retain B04's candidate and execution contract."""

    def plan(self, observations: np.ndarray, modes: np.ndarray, plan_inputs=None) -> dict:
        # A temporary hold changes execution, not H1's target-continuation memory.
        # Replanning still uses the latest actual positions in observations.
        self.targets_xy = self.h1_targets_xy.copy()
        base_plan = LayoutHeuristic.plan(self, observations, modes, plan_inputs)
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

        scored = []
        score_records = []
        for hold_id, targets in candidates:
            projected = project_h1_positions(
                own_xyz, targets, energy["available"], self.params,
                1, self.layout.area_size_m,
            )
            q1 = self._service_qos_at_snapshot(
                self.raw_env, plan_inputs, projected, energy["battery"]
            )
            self.service_snapshot_calls += 1
            scored.append((hold_id, q1))
            score_records.append({
                "hold_uav": int(hold_id), "integrated_qos": float(q1),
                "qos_1": float(q1),
            })

        selected = choose_plan(scored)
        selected_targets = next(targets for hold_id, targets in candidates
                                if hold_id == selected)
        self.targets_xy = selected_targets.copy()
        base_plan["targets"] = self.targets_xy.copy()
        base_plan["transit_hold"] = {
            "selected_uav": int(selected), "candidate_count": len(candidates),
            "snapshot_calls": len(candidates), "fallback": None,
            "candidate_scores": score_records,
        }
        self.last_plan = base_plan
        self.decision_records.append({
            "step": int(self.calls), "selected_hold_uav": int(selected),
            "candidate_count": len(candidates), "snapshot_calls": len(candidates),
            "fallback": None, "candidate_scores": score_records,
            "h1_targets_xy": base_targets.copy(),
        })
        return base_plan


class OneStepHoldController(TransitHoldController):
    """Use the unchanged H_central@10 controller with one-step hold scoring."""

    def __init__(self, env):
        super().__init__(env)
        self.heuristic = OneStepHoldHeuristic(self.heuristic.params, env.env)
