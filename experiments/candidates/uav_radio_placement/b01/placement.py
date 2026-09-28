"""Finite spatial placement policies for the S7-S2 H/G/R comparison."""

from __future__ import annotations

import time

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import TransitHoldHeuristic
from experiments.candidates.energy_relay_benchmark.b01.evaluation import central_plan_inputs
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    LayoutHeuristic, estimator_kmeans, variant,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    S7S2_LAYOUT, own_energy, own_positions,
)


PARAMS = variant("H1", information="central", replan_period=30)
SCORE_TOL = 1e-10
TRAVEL_TOL_M = 1e-6
_DIRECTIONS = ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1))


def _finite(value, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f"{name} must be finite")
    return array


def _lloyd(points: np.ndarray, initial: np.ndarray, iterations: int = 30):
    """The original estimator's update, empty-center and allclose semantics."""
    centers = initial.copy()
    count = 0
    for _ in range(iterations):
        count += 1
        distances = np.sum((points[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(distances, axis=1)
        updated = np.array([
            np.mean(points[labels == cluster], axis=0) if np.any(labels == cluster)
            else centers[cluster]
            for cluster in range(len(centers))
        ])
        if np.allclose(updated, centers):
            break
        centers = updated
    distances = np.sum((points[:, None, :] - centers[None, :, :]) ** 2, axis=2)
    labels = np.argmin(distances, axis=1)
    return centers, np.bincount(labels, minlength=len(centers)), float(np.sum(np.min(distances, axis=1))), count


def best_geometric_centers(users: np.ndarray, k: int = 6):
    """H initialization and seven fixed farthest-first initializations; first wins ties."""
    points = _finite(users, "users")
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < k:
        raise ValueError("users must be (n, 2) with at least k rows")
    starts = [points[np.linspace(0, len(points) - 1, k, dtype=int)].copy()]
    for first in np.linspace(0, len(points) - 1, 7, dtype=int):
        indices = [int(first)]
        while len(indices) < k:
            distance = np.min(np.sum((points[:, None, :] - points[indices][None, :, :]) ** 2, axis=2), axis=1)
            distance[indices] = -np.inf
            indices.append(int(np.argmax(distance)))
        starts.append(points[indices].copy())
    results = [_lloyd(points, initial) for initial in starts]
    best = min(range(len(results)), key=lambda index: results[index][2])
    centers, counts, sse, _ = results[best]
    return centers, counts, {"kmeans_solve_count": 8,
                              "kmeans_iteration_count": int(sum(row[3] for row in results)),
                              "kmeans_selected_start": int(best), "kmeans_sse": sse,
                              "kmeans_start_sse": [row[2] for row in results]}


class GeometricHeuristic(LayoutHeuristic):
    """H1's target construction and assignment with best-of-eight centroids."""

    def plan(self, observations, modes, plan_inputs=None):
        if plan_inputs is None:
            raise ValueError("central plan inputs required")
        users = _finite(plan_inputs["users_xy"], "users_xy")
        bs = _finite(plan_inputs["bs_xy"], "bs_xy").reshape(-1, 2)
        if users.ndim != 2 or users.shape[1] != 2 or not len(bs):
            raise ValueError("invalid central plan inputs")
        centers, counts, solve = best_geometric_centers(users, self.params.n_service)
        bs_xy = np.mean(bs, axis=0)
        center_xy = np.mean(centers, axis=0)
        relays = np.asarray([bs_xy + (index + 1) / (self.params.n_relay + 1) * (center_xy - bs_xy)
                             for index in range(self.params.n_relay)]).reshape(self.params.n_relay, 2)
        priority = np.concatenate((relays, centers[np.argsort(-counts, kind="stable")]), axis=0)
        own_xy = own_positions(observations, self.layout)[:, :2]
        available = np.flatnonzero(~np.asarray(modes, dtype=bool))
        targets = np.full((self.params.n_uavs, 2), np.nan)
        assigned = self._assign_targets(own_xy, available, priority[:len(available)], targets)
        if len(assigned) != len(available):
            raise RuntimeError("central geometric plan left a movable UAV unassigned")
        self.targets_xy = targets
        self.last_plan = {"targets": targets.copy(), "search": False, "centroids": centers,
                          "counts": counts, "relays": relays, **solve}
        return self.last_plan


def _layout(targets_xy: np.ndarray, own_xyz: np.ndarray, fixed: np.ndarray) -> np.ndarray:
    result = own_xyz.copy()
    good = np.isfinite(targets_xy).all(axis=1) & ~fixed
    result[good, :2] = targets_xy[good]
    result[good, 2] = PARAMS.height_m
    return result


def _travel(layout: np.ndarray, own_xyz: np.ndarray) -> float:
    return float(np.sum(np.linalg.norm(layout - own_xyz, axis=1), dtype=np.float64))


def _better(score: float, travel: float, best_score: float, best_travel: float) -> bool:
    if score > best_score + SCORE_TOL:
        return True
    return abs(score - best_score) <= SCORE_TOL and travel < best_travel - TRAVEL_TOL_M


class PlacementController:
    def __init__(self, arm, env, model_env):
        if arm not in ("H", "G", "R"):
            raise ValueError("arm must be H, G or R")
        if env is model_env or getattr(env, "env", env) is getattr(model_env, "env", model_env):
            raise ValueError("scoring model must be separate from the live environment")
        self.arm, self.env, self.model_env = arm, env, model_env
        self.heuristic = LayoutHeuristic(PARAMS) if arm == "H" else GeometricHeuristic(PARAMS)
        self.reset()

    def reset(self):
        self.heuristic.reset()
        self.targets_xyz = np.full((PARAMS.n_uavs, 3), np.nan)
        self.decision_records = []
        self.plan_input_steps = []
        self.search_replan_steps = []
        self._calls = 0
        self.snapshot_calls_started = 0
        self.snapshot_calls_completed = 0
        self._previous_F = np.zeros(PARAMS.n_uavs, dtype=bool)

    @property
    def targets_xy(self):
        return self.targets_xyz[:, :2].copy()

    def _score(self, inputs, layout, battery):
        self.snapshot_calls_started += 1
        score = TransitHoldHeuristic._service_qos_at_snapshot(
            getattr(self.model_env, "env", self.model_env), inputs, layout, battery)
        self.snapshot_calls_completed += 1
        if not np.isfinite(score):
            raise FloatingPointError("native radio score is non-finite")
        return float(score)

    def _actions(self, observations):
        own = _finite(own_positions(observations, S7S2_LAYOUT), "own_xyz")
        actions = np.zeros((PARAMS.n_uavs, 4), dtype=np.float32)
        for uav in range(PARAMS.n_uavs):
            target = self.targets_xyz[uav]
            delta = (target[:2] - own[uav, :2]) if np.isfinite(target[:2]).all() else np.zeros(2)
            velocity = delta / PARAMS.time_step_s
            speed = float(np.linalg.norm(velocity))
            if speed > PARAMS.cruise_mps:
                velocity = velocity * (PARAMS.cruise_mps / speed)
            height = target[2] if np.isfinite(target[2]) else PARAMS.height_m
            vertical = float(np.clip((height - own[uav, 2]) / PARAMS.time_step_s,
                                     -PARAMS.vertical_cap_mps, PARAMS.vertical_cap_mps))
            actions[uav] = np.clip(np.asarray((velocity[0] / PARAMS.horizontal_speed_mps,
                                              velocity[1] / PARAMS.horizontal_speed_mps,
                                              vertical / PARAMS.vertical_speed_mps, 0.0)), -1.0, 1.0)
        return actions

    def propose(self, observations, state, step, previous_done, modes):
        if int(step) != self._calls:
            raise ValueError("placement controller requires sequential evaluator steps")
        modes = np.asarray(modes, dtype=bool)
        if modes.shape != (PARAMS.n_uavs,):
            raise ValueError("F mask shape differs from S2")
        if step % PARAMS.replan_period != 0:
            self._calls += 1
            if self.arm == "H":
                action = self.heuristic.act(observations, modes)
                self.targets_xyz = np.column_stack((self.heuristic.targets_xy,
                                                    np.full(PARAMS.n_uavs, PARAMS.height_m)))
                return action
            if self.arm == "G":
                action = self.heuristic.act(observations, modes)
                self.targets_xyz = np.column_stack((self.heuristic.targets_xy,
                                                    np.full(PARAMS.n_uavs, PARAMS.height_m)))
                return action
            return self._actions(observations)

        wall_start, cpu_start = time.perf_counter(), time.process_time()
        inputs = central_plan_inputs(self.env)
        own = _finite(own_positions(observations, S7S2_LAYOUT), "own_xyz")
        energy = own_energy(observations, S7S2_LAYOUT)
        battery = _finite(energy["battery"], "battery")
        available = np.asarray(energy["available"], dtype=bool)
        self.plan_input_steps.append(int(step))
        records = []

        def query(identity, layout, *, sweep=None, member=None, direction=None):
            layout = _finite(layout, "candidate layout")
            score = self._score(inputs, layout, battery)
            travel = _travel(layout, own)
            row = {"identity": identity, "score": score, "travel_m": travel,
                   "targets_xyz": layout.tolist(), "sweep": sweep, "member": member,
                   "direction": direction, "accepted": False, "selected": False}
            records.append(row)
            return len(records) - 1

        if self.arm in ("H", "G"):
            action = self.heuristic.act(observations, modes, inputs)
            self.targets_xyz = np.column_stack((self.heuristic.targets_xy,
                                                np.full(PARAMS.n_uavs, PARAMS.height_m)))
            scored = _layout(self.heuristic.targets_xy, own, modes)
            index = query(self.arm, scored)
            records[index]["accepted"] = records[index]["selected"] = True
            selected_score = records[index]["score"]
            solve = self.heuristic.last_plan if self.arm == "G" else {"kmeans_solve_count": 1}
            initial_scores = {f"initial_{self.arm}_qos": selected_score}
        else:
            previous = self.targets_xyz.copy()
            prior_xy = previous[:, :2].copy()
            h = LayoutHeuristic(PARAMS)
            h.targets_xy = prior_xy.copy()
            h.plan(observations, modes, inputs)
            g = GeometricHeuristic(PARAMS)
            g.targets_xy = prior_xy.copy()
            g.plan(observations, modes, inputs)
            carried = np.where(np.isfinite(previous), previous, own)
            carried[self._previous_F] = own[self._previous_F]
            initial = (("H", _layout(h.targets_xy, own, modes)),
                       ("G", _layout(g.targets_xy, own, modes)),
                       ("carried_R", carried),
                       ("current", own.copy()))
            best = None
            for identity, raw_layout in initial:
                layout = _finite(raw_layout, "initial layout").copy()
                layout[modes] = own[modes]
                index = query(identity, layout)
                if best is None or _better(records[index]["score"], records[index]["travel_m"],
                                           records[best]["score"], records[best]["travel_m"]):
                    best = index
                    records[index]["accepted"] = True
            initial_scores = {"initial_H_qos": records[0]["score"],
                              "initial_G_qos": records[1]["score"]}
            bounds_low = np.asarray([0.0, 0.0, S7S2_LAYOUT.height_min_m])
            bounds_high = np.asarray([S7S2_LAYOUT.area_size_m, S7S2_LAYOUT.area_size_m,
                                      S7S2_LAYOUT.height_max_m])
            for sweep, (horizontal, vertical) in enumerate(((500.0, 50.0), (125.0, 25.0))):
                for offset in range(PARAMS.n_uavs):
                    member = (step // PARAMS.replan_period + offset) % PARAMS.n_uavs
                    if modes[member]:
                        continue
                    incumbent = np.asarray(records[best]["targets_xyz"], dtype=np.float64)
                    winner = best
                    for axis, sign in _DIRECTIONS:
                        candidate = incumbent.copy()
                        candidate[member, axis] += sign * (vertical if axis == 2 else horizontal)
                        candidate[member] = np.clip(candidate[member], bounds_low, bounds_high)
                        index = query("pattern", candidate, sweep=sweep, member=member,
                                      direction=[axis, sign])
                        if _better(records[index]["score"], records[index]["travel_m"],
                                   records[winner]["score"], records[winner]["travel_m"]):
                            winner = index
                    if winner != best:
                        best = winner
                        records[best]["accepted"] = True
            records[best]["selected"] = True
            self.targets_xyz = np.asarray(records[best]["targets_xyz"], dtype=np.float64)
            self._previous_F = modes.copy()
            selected_score = records[best]["score"]
            solve = dict(g.last_plan)
            solve["kmeans_solve_count"] += 1  # The independently built H layout is also solved.
            solve["kmeans_iteration_count"] = None
            action = self._actions(observations)
        self.decision_records.append({
            "step": int(step), "clock_index": int(step // PARAMS.replan_period),
            "selected_targets_xyz": [[float(x) if np.isfinite(x) else None for x in row]
                                     for row in self.targets_xyz],
            "available_mask": available.tolist(), "F_mask": modes.tolist(),
            **initial_scores, "selected_qos": float(selected_score),
            "query_count": len(records),
            "kmeans_solve_count": int(solve["kmeans_solve_count"]),
            "kmeans_iteration_count": solve.get("kmeans_iteration_count"),
            "planner_wall_seconds": time.perf_counter() - wall_start,
            "planner_cpu_seconds": time.process_time() - cpu_start,
            "candidates": records,
        })
        self._calls += 1
        return action
