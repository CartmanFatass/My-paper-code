"""One-sweep fleet goal choices under a shared analytical itinerary model.

The radio model is a fresh fixed-config environment, never a copy of the live
world. Only the declared current user/BS xy and legal energy/geometry records
cross into it. No native environment step is used for planning.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.evaluation import central_plan_inputs
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    PRODUCTION_PARAMS,
    apply_feedback_params,
    decode_legal_observations,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import (
    LayoutHeuristic,
    estimator_kmeans,
    variant,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy,
    own_positions,
    station_records,
)
from experiments.candidates.uav_service_auxiliary.b01.native import make_env, preserved_rng

from .itinerary import ForecastConfig, forecast_itineraries


PERIOD = 60
FORECAST_SECONDS = 600
SERVICE_HEIGHT = 100.0
MAX_REQUESTS = {"I": 147, "C": 146}


@dataclass(frozen=True)
class Goal:
    xyz: tuple[float, float, float]
    station: int = -1
    kind: str = "service"

    @property
    def key(self):
        return (*self.xyz, self.station)


def goal_arrays(goals: tuple[Goal, ...]) -> tuple[np.ndarray, np.ndarray]:
    return (np.asarray([goal.xyz for goal in goals], dtype=np.float64),
            np.asarray([goal.station for goal in goals], dtype=np.int16))


def decode_stations(observations) -> np.ndarray:
    records = station_records(observations)
    result = []
    for station in range(2):
        visible = np.flatnonzero(records["valid"][:, station])
        if not len(visible):
            raise ValueError("both native stations must be legally decodable")
        result.append(records["xyz_m"][visible[0], station])
    return np.asarray(result, dtype=np.float64)


def goal_library(plan_inputs, stations) -> tuple[Goal, ...]:
    centroids, _ = estimator_kmeans(np.asarray(plan_inputs["users_xy"]), 6)
    base = np.asarray(plan_inputs["bs_xy"], dtype=np.float64).mean(axis=0)
    centre = centroids.mean(axis=0)
    relays = [base + fraction * (centre - base) for fraction in (1 / 3, 2 / 3)]
    midpoints = (base + centroids) / 2
    sites = []
    for kind, points in (("centroid", centroids), ("relay", relays), ("midpoint", midpoints)):
        for point in points:
            sites.append(Goal((float(point[0]), float(point[1]), SERVICE_HEIGHT), kind=kind))
    sites.extend(Goal(tuple(float(x) for x in point), index, "station")
                 for index, point in enumerate(stations))
    return unique_goals(sites)


def unique_goals(goals) -> tuple[Goal, ...]:
    seen = set()
    result = []
    for goal in goals:
        if not np.isfinite(goal.xyz).all() or len(goal.xyz) != 3:
            raise ValueError("goal coordinates must be finite xyz")
        if goal.key not in seen:
            result.append(goal)
            seen.add(goal.key)
    return tuple(result)


def improve_goals(arm: str, incumbent: tuple[Goal, ...], options,
                  score: Callable, clock_index: int, incumbent_score: float):
    """Strict improvements: I has a joint veto; C conditions its single sweep."""
    if arm not in MAX_REQUESTS or len(options) != len(incumbent):
        raise ValueError("unknown arm or mismatched goal options")
    base = tuple(incumbent)
    base_score = float(incumbent_score)
    if not np.isfinite(base_score):
        raise FloatingPointError("non-finite incumbent score")
    order = [(int(clock_index) + index) % len(base) for index in range(len(base))]
    current, current_score = base, base_score
    single, single_score = base, base_score
    independent = list(base)
    for uav in order:
        context = current if arm == "C" else base
        best, best_score = context, current_score if arm == "C" else base_score
        for goal in options[uav]:
            candidate = list(context)
            candidate[uav] = goal
            candidate = tuple(candidate)
            candidate_score = float(score(candidate))
            if not np.isfinite(candidate_score):
                raise FloatingPointError("non-finite candidate score")
            if candidate_score > best_score:
                best, best_score = candidate, candidate_score
        if arm == "C":
            current, current_score = best, best_score
        else:
            independent[uav] = best[uav]
            if best_score > single_score:
                single, single_score = best, best_score
    if arm == "C":
        return current, current_score
    assembled = tuple(independent)
    assembled_score = float(score(assembled))
    if not np.isfinite(assembled_score):
        raise FloatingPointError("non-finite assembled score")
    # Preserve incumbent on exact ties, then assembled before the single fallback.
    best, best_score = base, base_score
    for candidate, candidate_score in ((assembled, assembled_score), (single, single_score)):
        if candidate_score > best_score:
            best, best_score = candidate, candidate_score
    return best, best_score


def track_goals(observations, goals: tuple[Goal, ...]) -> np.ndarray:
    positions = own_positions(observations)
    _, _, nearest, _, _ = decode_legal_observations(observations)
    targets, station_ids = goal_arrays(goals)
    delta = targets - positions
    actions = np.zeros((len(positions), 4), dtype=np.float32)
    horizontal = np.linalg.norm(delta[:, :2], axis=1)
    scale = np.maximum(1.0, horizontal / 30.0)
    actions[:, :2] = delta[:, :2] / scale[:, None] / 30.0
    actions[:, 2] = np.clip(delta[:, 2] / 5.0, -1.0, 1.0)
    actions[:, 3] = ((station_ids >= 0) & (station_ids == nearest)).astype(np.float32)
    return actions


class NativeSnapshotScorer:
    """Fresh association on declared geometry; no live simulator reference."""

    def __init__(self, config):
        # Constructor/reset may use global libraries; preserve caller RNG as well
        # as keeping this object's own stream separate from the native episode.
        with preserved_rng():
            self.env = make_env(config, 0)
            self.env.reset(seed=0)
        self.raw = self.env.env
        raw = self.raw
        if (raw.energy_stage != "S2" or raw.routing_protocol != "widest_path"
                or raw.failure_enabled or raw.n_uavs != 8 or raw.n_users != 30
                or raw.n_ground_bs != 1 or raw.time_step != 1.0
                or not np.all(raw.user_positions[:, 2] == 1.5)
                or not np.all(raw.ground_bs_positions[:, 2] == 30.0)):
            self.close()
            raise ValueError("snapshot model requires the fixed S7-S2 public contract")
        self.calls = 0

    def close(self):
        self.env.close()

    def qos(self, plan_inputs, positions, batteries) -> float:
        raw = self.raw
        users = np.asarray(plan_inputs["users_xy"], dtype=np.float64)
        bases = np.asarray(plan_inputs["bs_xy"], dtype=np.float64)
        positions = np.asarray(positions, dtype=np.float64)
        batteries = np.asarray(batteries, dtype=np.float64)
        if (users.shape != (30, 2) or bases.shape != (1, 2)
                or positions.shape != (8, 3) or batteries.shape != (8,)
                or not all(np.isfinite(item).all() for item in
                           (users, bases, positions, batteries))
                or np.any((batteries < 0) | (batteries > 1))):
            raise ValueError("invalid declared native snapshot")
        raw.user_positions[:, :2] = users
        raw.ground_bs_positions[:, :2] = bases
        raw.uav_positions = positions.copy()
        raw.uav_battery_ratios = batteries.copy()
        raw.uav_failed[:] = False
        raw.user_serving_sets = [[] for _ in range(raw.n_users)]
        raw.user_serving_uav.fill(-1)
        raw.connections.fill(False)
        raw._relay_geometry_state = None
        raw._step_communication_cache = None
        raw._update_channel_state()
        raw._update_uav_connections()
        raw._compute_routing_paths()
        rates, _, _ = raw._calculate_end_to_end_user_rates()
        demands = raw._current_user_qos_demand_bps()
        result = float(np.mean(np.clip(rates / demands, 0, 1)))
        if not np.isfinite(result):
            raise FloatingPointError("non-finite native snapshot QoS")
        self.calls += 1
        return result


class AnalyticalController:
    def __init__(self, arm: str, env, config):
        if arm not in MAX_REQUESTS:
            raise ValueError("analytical controller arm must be I or C")
        self.arm = arm
        self.env = env
        self.horizon = int(config.episode_length)
        self.scorer = NativeSnapshotScorer(config)
        raw = self.scorer.raw
        if (raw.battery_capacity_wh != 160 or raw.charging_power_w != 1000
                or np.any(np.asarray(raw.charging_station_capacity) != 1)
                or raw.return_margin_scale != .05 or raw.return_cost_cap != 1
                or raw.lambda_return != 2 or raw.cutoff_event_penalty != 5
                or raw.depletion_event_penalty != 10):
            self.close()
            raise ValueError("forecast constants differ from fixed native S2")
        self.forecast_config = ForecastConfig(
            capacity_wh=raw.battery_capacity_wh,
            hover_w=float(raw._calculate_power_consumption(0, 0)),
            charge_w=raw.charging_power_w,
            outer_horizontal=raw.max_speed,
            outer_vertical=raw.max_vertical_speed_mps,
            dock_horizontal=raw.docking_horizontal_speed_mps,
            dock_vertical=raw.docking_vertical_speed_mps,
            approach_radius=raw.charging_radius_m,
            capture_radius=raw.charging_capture_radius_m,
            reserve_ratio=raw.return_reserve_ratio,
            release_margin=PRODUCTION_PARAMS.exit_margin,
            cutoff_ratio=raw.service_cutoff_threshold,
            limp_speed=raw.limp_home_speed_mps,
            return_power_w=float(raw._calculate_power_consumption(raw.limp_home_speed_mps, 0)),
        )
        self.reference = LayoutHeuristic(variant("H1", information="central", replan_period=PERIOD))
        self.reset()

    def close(self):
        self.scorer.close()

    def reset(self):
        self.reference.reset()
        self.goal_tuple = None
        self.goals = np.full((8, 3), np.nan)
        self.station_ids = np.full(8, -1, dtype=np.int16)
        self.cutoff_seen = np.zeros(8, dtype=bool)
        self.depletion_seen = np.zeros(8, dtype=bool)
        self.plan_input_steps = []
        self.decision_records = []
        self.costs = dict(score_requests=0, model_evaluations=0, service_snapshots=0,
                          event_count=0, phase_count=0, planner_wall_seconds=0.0)

    @property
    def targets_xy(self):
        return self.goals[:, :2].copy()

    def propose(self, observations, state, step, previous_done, modes):
        batteries = own_energy(observations)["battery"].astype(np.float64)
        self.cutoff_seen |= batteries <= self.forecast_config.cutoff_ratio
        self.depletion_seen |= batteries <= 0
        if int(step) % PERIOD == 0:
            self._plan(observations, int(step), modes)
        if self.goal_tuple is None:
            raise RuntimeError("controller must start at the reset planning clock")
        return track_goals(observations, self.goal_tuple)

    def _plan(self, observations, step, modes):
        started = time.monotonic()
        plan_inputs = central_plan_inputs(self.env)
        self.plan_input_steps.append(step)
        positions = own_positions(observations)
        batteries = own_energy(observations)["battery"].astype(np.float64)
        stations = decode_stations(observations)
        effective = apply_feedback_params(observations, np.zeros((8, 4), dtype=np.float32),
                                          modes, PRODUCTION_PARAMS).modes
        self.reference.plan(observations, effective, plan_inputs)
        reference = tuple(Goal((float(target[0]), float(target[1]), SERVICE_HEIGHT), kind="ordinary")
                          if np.isfinite(target).all() else
                          Goal(tuple(position), kind="hold")
                          for target, position in zip(self.reference.targets_xy, positions))
        carried = reference if self.goal_tuple is None else self.goal_tuple
        model_horizon = min(FORECAST_SECONDS, self.horizon - step)
        times = np.arange(1, 4, dtype=np.float64) * (model_horizon / 3)
        if model_horizon <= 0:
            raise ValueError("planning past native horizon")
        cache = {}
        requests = []
        totals = dict(model_evaluations=0, service_snapshots=0, event_count=0, phase_count=0)

        def score(goals, *, count=True):
            key = tuple(goal.key for goal in goals)
            if key not in cache:
                coordinates, station_ids = goal_arrays(goals)
                forecast = forecast_itineraries(
                    positions, batteries, stations, coordinates, station_ids, effective, times,
                    config=self.forecast_config, power=self.scorer.raw._calculate_power_consumption,
                    cutoff_seen=self.cutoff_seen, depletion_seen=self.depletion_seen)
                qos = np.asarray([self.scorer.qos(plan_inputs, p, b)
                                  for p, b in zip(forecast.positions, forecast.batteries)])
                distances = np.linalg.norm(forecast.positions[:, :, None, :]
                                           - stations[None, None, :, :], axis=-1).min(axis=-1)
                cfg = self.forecast_config
                margins = (forecast.batteries - cfg.reserve_ratio
                           - distances * cfg.return_power_w / (cfg.limp_speed * 3600 * cfg.capacity_wh))
                risk = np.minimum(1.0, np.maximum(0, -margins.min(axis=1)) / .05)
                value = float(model_horizon / 3 * np.sum(qos - 2 * risk)
                              - 5 * forecast.cutoff_events - 10 * forecast.depletion_events)
                if not np.isfinite(value):
                    raise FloatingPointError("non-finite analytical plan score")
                cache[key] = dict(score=value, forecast=forecast, qos=qos, risk=risk)
                totals["model_evaluations"] += 1
                totals["service_snapshots"] += 3
                totals["event_count"] += forecast.event_count
                totals["phase_count"] += forecast.phase_count
            if count:
                requests.append(cache[key]["score"])
            return cache[key]["score"]

        incumbent, incumbent_score = carried, score(carried)
        reference_score = score(reference)
        if reference_score > incumbent_score:
            incumbent, incumbent_score = reference, reference_score
        library = goal_library(plan_inputs, stations)
        options = [unique_goals((incumbent[uav], *library, Goal(tuple(position), kind="hold")))
                   for uav, position in enumerate(positions)]
        if any(len(candidates) > 18 for candidates in options):
            raise RuntimeError("goal neighborhood exceeded the fixed bound")
        selected, selected_score = improve_goals(
            self.arm, incumbent, options, score, step // PERIOD, incumbent_score)
        if len(requests) > MAX_REQUESTS[self.arm]:
            raise RuntimeError("search exceeded the prospective query bound")
        selected_record = cache[tuple(goal.key for goal in selected)]
        forecast = selected_record["forecast"]
        self.goal_tuple = selected
        self.goals, self.station_ids = goal_arrays(selected)
        record = dict(step=step, horizon=model_horizon, sample_times=times,
                      incumbent_score=incumbent_score, selected_score=selected_score,
                      goals=self.goals.copy(), station_ids=self.station_ids.copy(),
                      kinds=np.asarray([goal.kind for goal in selected], dtype="U16"),
                      selected_positions=forecast.positions.copy(),
                      selected_batteries=forecast.batteries.copy(),
                      selected_qos=selected_record["qos"], selected_risk=selected_record["risk"],
                      predicted_cutoff_events=forecast.cutoff_events,
                      predicted_depletion_events=forecast.depletion_events,
                      predicted_input_wh=forecast.input_wh, predicted_consumed_wh=forecast.consumed_wh,
                      predicted_floor_clip_wh=forecast.floor_clip_wh,
                      predicted_arrival_times=forecast.arrival_times,
                      predicted_release_times=forecast.release_times,
                      candidate_scores=np.asarray(requests), score_requests=len(requests), **totals)
        record["planner_wall_seconds"] = time.monotonic() - started
        self.decision_records.append(record)
        self.costs["score_requests"] += len(requests)
        for key, value in totals.items():
            self.costs[key] += value
        self.costs["planner_wall_seconds"] += record["planner_wall_seconds"]

    def decision_arrays(self):
        if not self.decision_records:
            return {}
        result = {}
        for key in self.decision_records[0]:
            if key == "candidate_scores":
                values = np.full((len(self.decision_records), MAX_REQUESTS[self.arm]), np.nan)
                for row, record in enumerate(self.decision_records):
                    values[row, :len(record[key])] = record[key]
            else:
                values = np.asarray([record[key] for record in self.decision_records])
            result[f"planner_{key}"] = values
        return result
