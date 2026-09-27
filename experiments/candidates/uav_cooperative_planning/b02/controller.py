"""Direction-owned choice adapter over the accepted B04 transit library."""

from __future__ import annotations

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    BASELINE_HOLD_ID, H1_CENTRAL_10, TransitHoldHeuristic,
    hold_plan_candidates, project_h1_positions,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import HeuristicController
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy, own_positions, station_records,
)

WIDTH = 248
MAX_CANDIDATES = 9


def candidate_features(heuristic, observations, modes, plan_inputs, record):
    """Only legal observations, central plan snapshot and inherited scores enter L."""
    layout = heuristic.layout
    xyz = own_positions(observations, layout)
    energy = own_energy(observations, layout)
    station = station_records(observations, layout)
    stations = []
    for index in range(2):
        valid = np.flatnonzero(station["valid"][:, index])
        if not valid.size:
            raise ValueError("legal station record missing")
        stations.extend((station["xyz_m"][valid[0], index, :2] / layout.area_size_m).tolist())
    users = np.asarray(plan_inputs["users_xy"], dtype=np.float64)
    bs = np.asarray(plan_inputs["bs_xy"], dtype=np.float64)
    if users.shape != (30, 2) or bs.shape != (1, 2) or xyz.shape != (8, 3):
        raise ValueError("B02 central S7-S2 feature geometry changed")
    base = np.asarray(heuristic.h1_targets_xy, dtype=np.float64)
    valid_target = np.isfinite(base).all(axis=1)
    filled_base = np.where(valid_target[:, None], base, xyz[:, :2])
    candidates = hold_plan_candidates(base, xyz[:, :2], energy["available"], modes)
    if record["fallback"] is not None:
        candidates = candidates[:1]
    if [key for key, _ in candidates] != ([BASELINE_HOLD_ID] if record["fallback"]
                                            else [item["hold_uav"] for item in record["candidate_scores"]]):
        raise ValueError("inherited candidate order differs from B02 feature order")
    scored = {item["hold_uav"]: item for item in record["candidate_scores"]}
    coordinate_scale = np.asarray([layout.area_size_m, layout.area_size_m,
                                   layout.height_max_m], dtype=np.float64)
    common = [
        np.asarray([heuristic.calls / 3000.0]),
        (xyz / coordinate_scale).ravel(),
        np.column_stack((energy["battery"], energy["available"], energy["charging"],
                         energy["returning"], energy["dock_request"],
                         energy["return_margin"])).ravel().astype(np.float64),
        np.asarray(stations), (users / layout.area_size_m).ravel(),
        (bs / layout.area_size_m).ravel(),
        (filled_base / layout.area_size_m).ravel(), valid_target.astype(np.float64),
        np.asarray(modes, dtype=np.float64),
    ]
    features = []
    for hold_id, targets in candidates:
        hold = np.zeros(8, dtype=np.float64)
        if hold_id >= 0:
            hold[hold_id] = 1.0
        filled = np.where(np.isfinite(targets), targets, xyz[:, :2])
        projected = [project_h1_positions(xyz, targets, energy["available"],
                                         heuristic.params, step, layout.area_size_m)
                     for step in (5, 10)]
        score = scored.get(hold_id)
        values = (np.zeros(4, dtype=np.float64) if score is None else
                  np.asarray([score["qos_0"], score["qos_5"], score["qos_10"],
                              score["integrated_qos"]], dtype=np.float64))
        feature = np.concatenate((*common, hold, (filled / layout.area_size_m).ravel(),
                                  *[(point / coordinate_scale).ravel() for point in projected],
                                  values, np.asarray([float(score is None)])))
        if feature.shape != (WIDTH,) or not np.isfinite(feature).all():
            raise ValueError("B02 candidate feature width or finiteness violated")
        features.append(feature.astype(np.float32))
    result = np.zeros((MAX_CANDIDATES, WIDTH), dtype=np.float32)
    result[:len(features)] = features
    mask = np.zeros(MAX_CANDIDATES, dtype=bool)
    mask[:len(features)] = True
    return result, mask, candidates


class ValueTransitHeuristic(TransitHoldHeuristic):
    """Preserve B04 scoring and H1 memory; replace only the selected commitment."""

    def __init__(self, params, raw_env, *, policy, rng=None, model=None):
        self.policy = policy
        self.behavior_rng = rng
        self.model = model
        super().__init__(params, raw_env)

    def reset(self):
        super().reset()
        self.contexts = []
        self.inference_candidate_count = 0

    def plan(self, observations, modes, plan_inputs=None):
        plan = super().plan(observations, modes, plan_inputs)
        record = self.decision_records[-1]
        features, mask, candidates = candidate_features(
            self, observations, modes, plan_inputs, record)
        suggestion = int(record["selected_hold_uav"])
        suggestion_index = next(i for i, (hold_id, _) in enumerate(candidates)
                                if hold_id == suggestion)
        if self.policy == "collect" and len(candidates) > 1:
            if self.behavior_rng is None:
                raise ValueError("collection needs its independent behavior RNG")
            if self.behavior_rng.random() < 0.5:
                index = suggestion_index
            else:
                index = int(self.behavior_rng.integers(len(candidates)))
            probability = 0.5 / len(candidates) + (0.5 if index == suggestion_index else 0.0)
        elif self.policy == "L" and len(candidates) > 1:
            values = self.model(features, mask)
            if values.shape != (len(candidates),) or not np.isfinite(values).all():
                raise FloatingPointError("learner candidate values invalid")
            self.inference_candidate_count += len(candidates)
            best = float(np.max(values))
            tied = np.flatnonzero(values == best)
            scores = record["candidate_scores"]
            # B04 candidate order is all-move, then increasing UAV index; argmax
            # keeps its first entry when both learned value and P score tie.
            index = int(max(tied, key=lambda i: scores[int(i)]["integrated_qos"]))
            probability = 1.0
        else:
            index = suggestion_index
            probability = 1.0
        hold_id, targets = candidates[index]
        self.targets_xy = targets.copy()
        plan["targets"] = self.targets_xy.copy()
        plan["transit_hold"]["selected_uav"] = int(hold_id)
        self.last_plan = plan
        record["p_suggested_hold_uav"] = suggestion
        record["selected_hold_uav"] = int(hold_id)
        record["chosen_index"] = int(index)
        record["behavior_probability"] = float(probability)
        self.contexts.append((features, mask, int(index), int(suggestion_index),
                              float(probability)))
        return plan


class ValueTransitController(HeuristicController):
    def __init__(self, env, *, policy, rng=None, model=None):
        super().__init__(H1_CENTRAL_10, env=env)
        self.heuristic = ValueTransitHeuristic(self.heuristic.params, env.env,
                                               policy=policy, rng=rng, model=model)
