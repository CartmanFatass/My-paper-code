"""Finite nearest-station commitments around the frozen TransitHold service rule."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math

import numpy as np

from experiments.candidates.energy_relay_availability.b04.transit_hold import (
    BASELINE_HOLD_ID, PREDICTION_STEPS, TransitHoldController,
    TransitHoldHeuristic, choose_plan, hold_plan_candidates, project_h1_positions,
)
from experiments.candidates.energy_relay_benchmark.b01.evaluation import central_plan_inputs
from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    DOCKING_RADIUS_M, HORIZONTAL_SPEED_MPS, PRODUCTION_PARAMS,
    VERTICAL_SPEED_MPS, decode_legal_observations,
)
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy, own_positions, station_records,
)


DURATIONS = (120, 300, 600)
N_ACTIONS = 1 + 8 * len(DURATIONS)
# mask, users/BS xy, own xyz, battery/margin/load/availability, station xyz,
# legal energy/station remainder, base H1 targets/mask, real F,
# option station/age/arrival/dwell/duration,
# recent draw/mask, 31 battery samples and masks, and remaining time.
FEATURE_DIM = 8 + 60 + 2 + 24 + 32 + 48 + 6 + 8 + 16 + 8 + 8 + 40 + 16 + 31*8*2 + 1
CAPTURE_RADIUS_M = 20.0
TIMEOUT = 900
HOVER_W = 168.49
BATTERY_WH = 160.0


@dataclass
class Commitment:
    member: int
    station: int
    duration: int
    start: int
    arrival: int | None = None


def _effective_modes(modes: np.ndarray, margin: np.ndarray) -> np.ndarray:
    effective = np.asarray(modes, dtype=bool).copy()
    effective[margin <= PRODUCTION_PARAMS.enter_margin] = True
    effective[margin >= PRODUCTION_PARAMS.exit_margin] = False
    return effective


def _arrival_time(vector: np.ndarray) -> int:
    """Capped straight-vector time to the 20 m capture sphere."""
    distance = float(np.linalg.norm(vector))
    if distance <= CAPTURE_RADIUS_M:
        return 0
    outer = max(0.0, distance - DOCKING_RADIUS_M)
    inner = min(distance, DOCKING_RADIUS_M) - CAPTURE_RADIUS_M
    # Following the stationward line, horizontal and vertical caps act in parallel.
    direction = np.abs(vector) / distance
    outer_time = max(np.linalg.norm(direction[:2]) * outer / HORIZONTAL_SPEED_MPS,
                     direction[2] * outer / VERTICAL_SPEED_MPS)
    inner_time = max(np.linalg.norm(direction[:2]) * inner / 3.0,
                     direction[2] * inner / 1.0)
    return int(math.ceil(outer_time + inner_time))


def _restoration_time(point: np.ndarray, target_xy: np.ndarray) -> int:
    destination = np.asarray((target_xy[0], target_xy[1], 100.0))
    delta = np.abs(destination - point)
    return int(math.ceil(max(np.linalg.norm(delta[:2]) / HORIZONTAL_SPEED_MPS,
                             delta[2] / VERTICAL_SPEED_MPS)))


def ordinary_dispatch(eligible: np.ndarray, free: np.ndarray, station: np.ndarray, margin: np.ndarray,
                      draw_w: np.ndarray, tau_in: np.ndarray, tau_out: np.ndarray,
                      load: np.ndarray, remaining: int) -> int:
    """Corrected O choice, with action 0 for service."""
    deadline = np.maximum(0.0, margin) * BATTERY_WH * 3600.0 / np.maximum(HOVER_W, draw_w)
    candidates = []
    for member in np.flatnonzero(eligible):
        arrivals = [deadline[other] + tau_in[other] for other in range(8)
                    if other != member and free[other] and station[other] == station[member]
                    and np.isfinite(tau_in[other])]
        next_arrival = min(arrivals, default=math.inf)
        feasible = [j for j, duration in enumerate(DURATIONS)
                    if tau_in[member] + duration <= next_arrival
                    and tau_in[member] + duration + 10 + tau_out[member] <= remaining]
        if not feasible:
            continue
        j = feasible[-1]
        if deadline[member] < remaining and deadline[member] <= tau_in[member] + DURATIONS[j] + 30:
            candidates.append((float(deadline[member]), float(load[member]), int(member), j))
    if not candidates:
        return 0
    _, _, member, j = min(candidates)
    return 1 + 3 * member + j


class CommitmentAwareHeuristic(TransitHoldHeuristic):
    """P with voluntary members excluded from matching, not from radio geometry."""

    def reset(self) -> None:
        super().reset()
        self.committed = np.zeros(self.params.n_uavs, dtype=bool)

    def plan(self, observations, modes, plan_inputs=None):
        if not self.committed.any():
            return super().plan(observations, modes, plan_inputs)
        self.targets_xy = self.h1_targets_xy.copy()
        real_modes = np.asarray(modes, dtype=bool)
        base_plan = LayoutHeuristic.plan(
            self, observations, real_modes | self.committed, plan_inputs)
        base_targets = self.targets_xy.copy()
        self.h1_targets_xy = base_targets.copy()
        xyz = own_positions(observations, self.layout)
        energy = own_energy(observations, self.layout)
        fallback = None
        if real_modes.any():
            fallback = "return_shield_active"
        elif np.any(energy["return_margin"] <= PRODUCTION_PARAMS.enter_margin):
            fallback = "return_shield_entry"
        if fallback is not None:
            self.decision_records.append({
                "step": int(self.calls), "selected_hold_uav": BASELINE_HOLD_ID,
                "candidate_count": 1, "snapshot_calls": 0, "fallback": fallback,
                "candidate_scores": [], "h1_targets_xy": base_targets.copy(),
            })
            base_plan["transit_hold"] = {"selected_uav": BASELINE_HOLD_ID,
                                          "candidate_count": 1, "fallback": fallback}
            return base_plan
        candidates = hold_plan_candidates(
            base_targets, xyz[:, :2], energy["available"], real_modes | self.committed)
        if len(candidates) == 1:
            fallback = "no_movable_assigned_member"
            self.decision_records.append({
                "step": int(self.calls), "selected_hold_uav": BASELINE_HOLD_ID,
                "candidate_count": 1, "snapshot_calls": 0, "fallback": fallback,
                "candidate_scores": [], "h1_targets_xy": base_targets.copy(),
            })
            base_plan["transit_hold"] = {"selected_uav": BASELINE_HOLD_ID,
                                          "candidate_count": 1, "fallback": fallback}
            return base_plan
        if plan_inputs is None:
            raise ValueError("central P snapshot required")
        q0 = self._service_qos_at_snapshot(self.raw_env, plan_inputs, xyz, energy["battery"])
        self.service_snapshot_calls += 1
        scored, records = [], []
        for hold_id, targets in candidates:
            scores = []
            for count in PREDICTION_STEPS:
                projected = project_h1_positions(
                    xyz, targets, energy["available"] & ~self.committed,
                    self.params, count, self.layout.area_size_m)
                scores.append(self._service_qos_at_snapshot(
                    self.raw_env, plan_inputs, projected, energy["battery"]))
                self.service_snapshot_calls += 1
            total = float((q0 + 2 * scores[0] + scores[1]) / 4)
            scored.append((hold_id, total))
            records.append({"hold_uav": int(hold_id), "qos_0": float(q0),
                            "qos_5": float(scores[0]), "qos_10": float(scores[1]),
                            "integrated_qos": total})
        selected = choose_plan(scored)
        self.targets_xy = next(targets for hold_id, targets in candidates
                               if hold_id == selected).copy()
        base_plan["targets"] = self.targets_xy.copy()
        base_plan["transit_hold"] = {"selected_uav": int(selected),
                                      "candidate_count": len(candidates),
                                      "snapshot_calls": 1 + 2 * len(candidates),
                                      "fallback": None, "candidate_scores": records}
        self.last_plan = base_plan
        self.decision_records.append({
            "step": int(self.calls), "selected_hold_uav": int(selected),
            "candidate_count": len(candidates), "snapshot_calls": 1 + 2 * len(candidates),
            "fallback": None, "candidate_scores": records,
            "h1_targets_xy": base_targets.copy(),
        })
        return base_plan


class CommitmentController(TransitHoldController):
    def __init__(self, env, config, arm: str = "L"):
        if arm not in ("L", "O"):
            raise ValueError("arm must be L or O")
        super().__init__(env)
        self.heuristic = CommitmentAwareHeuristic(self.heuristic.params, env.env)
        self.config = config
        self.arm = arm
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.options: dict[int, Commitment] = {}
        self._pending_restoration: set[int] = set()
        self.events: list[dict] = []
        self.diagnostics: list[dict] = []
        self.macro_choices = 0
        self.native_steps = 0
        self.source_calls = 0
        self._cached_step: int | None = None
        self._cached_action: np.ndarray | None = None
        self._prepared: dict | None = None
        self._last_observed_step: int | None = None
        self._battery_history: deque[tuple[int, np.ndarray, np.ndarray]] = deque(maxlen=32)
        self._central: dict | None = None

    @property
    def targets_xy(self) -> np.ndarray:
        return self.heuristic.targets_xy.copy()

    def _observe(self, observations, step: int) -> None:
        if self._last_observed_step == step:
            return
        energy = own_energy(observations, self.heuristic.layout)
        battery = np.asarray(energy["battery"], dtype=np.float64)
        self._battery_history.append((step, battery.copy(), energy["charging"].copy()))
        xyz = own_positions(observations, self.heuristic.layout)
        _, _, nearest, distances, _ = decode_legal_observations(observations)
        for member, option in list(self.options.items()):
            if option.station != int(nearest[member]):
                self.events.append({"kind": "station_change", "step": step,
                                    "member": member, "from": option.station,
                                    "to": int(nearest[member])})
                option.station = int(nearest[member])
            if option.arrival is None and distances[member] <= CAPTURE_RADIUS_M:
                option.arrival = step
                self.events.append({"kind": "arrival", "step": step, "member": member})
            reason = None
            if battery[member] >= 1.0:
                reason = "full"
            elif step - option.start >= TIMEOUT:
                reason = "timeout_no_arrival" if option.arrival is None else "timeout"
            elif option.arrival is not None and step - option.arrival >= option.duration:
                reason = "dwell"
            if reason is not None:
                self.events.append({"kind": "release", "step": step, "member": member,
                                    "reason": reason, "arrival": option.arrival,
                                    "dwell_elapsed": None if option.arrival is None else step-option.arrival})
                del self.options[member]
                self._pending_restoration.add(member)
        self.heuristic.committed[:] = False
        self.heuristic.committed[list(self.options)] = True
        self._last_observed_step = step

    def _draw_w(self, step: int) -> tuple[np.ndarray, np.ndarray]:
        draws = np.full(8, HOVER_W, dtype=np.float64)
        valid = np.zeros(8, dtype=bool)
        past = next(((t, b) for t, b, _ in self._battery_history if t == step-30), None)
        if past is not None:
            delta = past[1] - self._battery_history[-1][1]
            charged = np.logical_or.reduce([c for t, _, c in self._battery_history
                                            if step-30 <= t <= step])
            valid = (delta > 0) & ~charged
            draws[valid] = np.maximum(HOVER_W, delta[valid] * BATTERY_WH * 3600 / 30)
        return draws, valid

    def _history_features(self, step: int) -> tuple[np.ndarray, np.ndarray]:
        samples = np.zeros((31, 8), dtype=np.float64)
        masks = np.zeros((31, 8), dtype=np.float64)
        for observed_step, battery, _ in self._battery_history:
            offset = observed_step - (step-30)
            if 0 <= offset <= 30:
                samples[offset] = battery
                masks[offset] = 1.0
        return samples, masks

    def _ordinary(self, observations, state, step, previous_done, modes):
        if self._cached_step == step:
            return self._cached_action.copy()
        self._observe(observations, step)
        replans = self.heuristic.replans_next()
        action = super().propose(observations, state, step, previous_done, modes)
        self.source_calls += 1
        if replans:
            self._central = central_plan_inputs(self.env)
            margin = own_energy(observations, self.heuristic.layout)["return_margin"]
            effective = _effective_modes(modes, margin)
            for member in sorted(self._pending_restoration):
                if not effective[member] and np.isfinite(self.heuristic.h1_targets_xy[member]).all():
                    self.events.append({"kind": "assignment_restored", "step": int(step),
                                        "member": member})
            self._pending_restoration = {
                member for member in self._pending_restoration
                if effective[member] or not np.isfinite(self.heuristic.h1_targets_xy[member]).all()
            }
        self._cached_step = step
        self._cached_action = action.copy()
        return action.copy()

    def prepare(self, observations, modes, step: int) -> np.ndarray:
        if step % 30:
            raise ValueError("prepare requires a 30-step boundary")
        if self._prepared is not None and self._prepared["step"] == step:
            return self._prepared["features"].copy()
        self._ordinary(observations, None, step, None, modes)
        layout = self.heuristic.layout
        xyz = own_positions(observations, layout)
        energy = own_energy(observations, layout)
        stations = station_records(observations, layout)
        margin, battery, nearest, distances, vectors = decode_legal_observations(observations)
        effective = _effective_modes(modes, margin)
        occupied = {o.station for o in self.options.values()}
        occupied.update(int(nearest[i]) for i in np.flatnonzero(effective))
        eligible = np.asarray([
            bool(energy["available"][i] and not effective[i] and battery[i] < 1
                 and i not in self.options and int(nearest[i]) not in occupied
                 and len(self.options) < 2)
            for i in range(8)], dtype=bool)
        free = np.asarray(energy["available"] & ~effective & ~self.heuristic.committed,
                          dtype=bool)
        draws, draw_valid = self._draw_w(step)
        recent_battery, recent_mask = self._history_features(step)
        tau_in = np.asarray([_arrival_time(v) for v in vectors], dtype=np.float64)
        base = self.heuristic.h1_targets_xy.copy()
        tau_out = np.full(8, np.inf)
        for i in range(8):
            if np.isfinite(base[i]).all():
                distance = float(distances[i])
                point = xyz[i] + vectors[i] * (max(0.0, distance-CAPTURE_RADIUS_M) / distance) if distance > CAPTURE_RADIUS_M else xyz[i]
                tau_out[i] = _restoration_time(point, base[i])
        raw_load = np.asarray(observations)[:, layout.energy_uavs].reshape(8, 8, 13)
        own_records = raw_load[np.arange(8), np.arange(8)]
        load = own_records[:, 7].astype(np.float64)
        option_fields = np.zeros((8, 5), dtype=np.float64)
        for i, option in self.options.items():
            option_fields[i] = (1, option.station, (step-option.start)/TIMEOUT,
                                -1 if option.arrival is None else (step-option.arrival)/TIMEOUT,
                                option.duration/600)
        central = self._central
        if central is None:
            raise RuntimeError("P has not supplied its central snapshot")
        scale = layout.area_size_m
        features = np.concatenate((
            eligible.astype(np.float64), central["users_xy"].reshape(-1)/scale,
            central["bs_xy"].reshape(-1)/scale, xyz.reshape(-1)/scale,
            np.stack((battery, margin, load, energy["available"].astype(float)), axis=1).reshape(-1),
            own_records[:, [4, 6, 8, 9, 10, 11]].reshape(-1),
            stations["xyz_m"][0].reshape(-1)/scale,
            np.stack([stations[key][0] for key in
                      ("capacity_ratio", "available_ratio", "queue_ratio", "valid")], axis=1).reshape(-1),
            np.nan_to_num(base, nan=0.0).reshape(-1)/scale,
            np.isfinite(base).all(axis=1).astype(float),
            effective.astype(float), option_fields.reshape(-1),
            draws/HOVER_W, draw_valid.astype(float),
            recent_battery.reshape(-1), recent_mask.reshape(-1),
            np.asarray([(layout.max_steps-step)/layout.max_steps]),
        )).astype(np.float32)
        if features.shape != (FEATURE_DIM,) or not np.isfinite(features).all():
            raise ValueError("non-finite or mis-sized commitment features")
        self._prepared = {"step": step, "eligible": eligible, "free": free,
                          "station": nearest,
                          "margin": margin, "distance": distances, "draw_w": draws, "tau_in": tau_in,
                          "tau_out": tau_out, "load": load, "remaining": layout.max_steps-step,
                          "features": features}
        return features.copy()

    def ordinary_action(self) -> int:
        if self._prepared is None:
            raise RuntimeError("prepare before ordinary_action")
        p = self._prepared
        return ordinary_dispatch(p["eligible"], p["free"], p["station"], p["margin"],
                                 p["draw_w"], p["tau_in"], p["tau_out"],
                                 p["load"], p["remaining"])

    def apply_choice(self, action: int) -> dict:
        if self._prepared is None:
            raise RuntimeError("prepare before apply_choice")
        if not isinstance(action, (int, np.integer)) or not 0 <= action < N_ACTIONS:
            raise ValueError("invalid commitment action")
        p = self._prepared
        if p.get("choice_applied"):
            raise RuntimeError("one choice per macro clock")
        p["choice_applied"] = True
        member = None if action == 0 else (int(action)-1)//3
        duration = None if action == 0 else DURATIONS[(int(action)-1)%3]
        executed = bool(member is not None and p["eligible"][member])
        if executed:
            option = Commitment(member, int(p["station"][member]), duration, int(p["step"]))
            if p["distance"][member] <= CAPTURE_RADIUS_M:
                option.arrival = int(p["step"])
            self.options[member] = option
            self.heuristic.committed[member] = True
            self.events.append({"kind": "start", "step": int(p["step"]), "member": member,
                                "station": option.station, "duration": duration})
            if option.arrival is not None:
                self.events.append({"kind": "arrival", "step": int(p["step"]),
                                    "member": member})
        record = {"step": int(p["step"]), "requested_action": int(action),
                  "executed_action": int(action) if executed else 0,
                  "member": member, "duration": duration,
                  "eligible": bool(p["eligible"].any()),
                  "requested_member_eligible": bool(member is not None and p["eligible"][member]),
                  "active_commitments": len(self.options)}
        self.diagnostics.append(record)
        self.macro_choices += 1
        return record.copy()

    def propose(self, observations, state, step, previous_done, modes):
        action = self._ordinary(observations, state, step, previous_done, modes)
        _, _, _, distances, vectors = decode_legal_observations(observations)
        for member in self.options:
            vector = vectors[member]
            if distances[member] <= DOCKING_RADIUS_M:
                action[member] = np.asarray((0, 0, 0, 1), dtype=np.float32)
            else:
                duration = max(1.0, np.linalg.norm(vector[:2])/HORIZONTAL_SPEED_MPS,
                               abs(float(vector[2]))/VERTICAL_SPEED_MPS)
                velocity = vector/duration
                action[member] = np.asarray((velocity[0]/HORIZONTAL_SPEED_MPS,
                                             velocity[1]/HORIZONTAL_SPEED_MPS,
                                             velocity[2]/VERTICAL_SPEED_MPS, 1), dtype=np.float32)
        self.native_steps += 1
        return action

    def commitment_snapshot(self) -> dict[str, np.ndarray]:
        active = np.zeros(8, dtype=bool)
        station = np.full(8, -1, dtype=np.int64)
        start = np.full(8, -1, dtype=np.int64)
        arrival = np.full(8, -1, dtype=np.int64)
        duration = np.zeros(8, dtype=np.int64)
        for member, option in self.options.items():
            active[member] = True
            station[member] = option.station
            start[member] = option.start
            arrival[member] = -1 if option.arrival is None else option.arrival
            duration[member] = option.duration
        return {"active": active, "station": station, "start_step": start,
                "arrival_step": arrival, "duration": duration}

    @property
    def costs(self) -> dict[str, int]:
        return {"source_calls": self.source_calls, "macro_choices": self.macro_choices,
                "native_steps": self.native_steps,
                "service_snapshot_calls": self.heuristic.service_snapshot_calls,
                "p_plan_calls": len(self.heuristic.decision_records)}

    def finish(self, step: int, observations=None, modes=None) -> None:
        # The last native observation is endpoint evidence; it is not a new decision step.
        if observations is not None:
            self._observe(observations, int(step))
        for member, option in self.options.items():
            self.events.append({"kind": "censored", "step": int(step), "member": member,
                                "arrival": option.arrival, "duration": option.duration})
