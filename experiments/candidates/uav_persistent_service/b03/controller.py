"""O_H with a finite, observed-station cross-basin transfer option."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.feedback import (
    DOCKING_RADIUS_M, HORIZONTAL_SPEED_MPS, VERTICAL_SPEED_MPS,
    decode_legal_observations,
)
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    own_energy, own_positions, station_records,
)
from experiments.candidates.uav_persistent_service.controllers import (
    BATTERY_WH, CAPTURE_RADIUS_M, DURATIONS, HOVER_W, N_ACTIONS, TIMEOUT,
    CommitmentController, _arrival_time, _effective_modes, _restoration_time,
)


TRANSFER_BASE = N_ACTIONS
TRANSFER_ACTIONS = 8 * len(DURATIONS)


@dataclass
class Transfer:
    member: int
    station: int
    duration: int
    start: int
    arrival: int | None = None


def max_nearest_distance(start: np.ndarray, end: np.ndarray,
                         stations: np.ndarray) -> float:
    """Maximum distance to the nearest of two stations along a straight segment."""
    delta = end - start
    a, b = stations
    denominator = 2.0 * float(np.dot(delta, b-a))
    points = [start, end]
    if abs(denominator) > 1e-12:
        crossing = (float(np.dot(b, b) - np.dot(a, a))
                    - 2.0 * float(np.dot(start, b-a))) / denominator
        if 0.0 < crossing < 1.0:
            points.append(start + crossing * delta)
    return max(min(float(np.linalg.norm(point-a)), float(np.linalg.norm(point-b)))
               for point in points)


def transfer_action(member: int, duration_index: int) -> int:
    return TRANSFER_BASE + 3 * member + duration_index


class ReassignmentController(CommitmentController):
    def __init__(self, env, config):
        super().__init__(env, config, arm="O")
        raw = env.env
        self.max_power_w = float(raw._calculate_power_consumption(30.0, 5.0))
        self.limp_power_w = float(raw._calculate_power_consumption(3.0, 0.0))
        if not (math.isfinite(self.max_power_w) and math.isfinite(self.limp_power_w)
                and self.max_power_w > 0 and self.limp_power_w > 0):
            raise ValueError("invalid native physical power model")

    def reset(self) -> None:
        super().reset()
        self.transfers: dict[int, Transfer] = {}
        self.feasibility_rejections: dict[str, int] = {}
        self._real_modes = np.zeros(8, dtype=bool)

    def _ordinary(self, observations, state, step, previous_done, modes):
        self._real_modes = np.asarray(modes, dtype=bool).copy()
        return super()._ordinary(observations, state, step, previous_done, modes)

    def _observe(self, observations, step: int) -> None:
        if self._last_observed_step == step:
            return
        energy = own_energy(observations, self.heuristic.layout)
        _, _, nearest, distances, _ = decode_legal_observations(observations)
        effective = _effective_modes(self._real_modes, energy["return_margin"])
        for member, option in list(self.transfers.items()):
            station = int(nearest[member])
            if effective[member] and station != option.station:
                self._release_transfer(member, step, "f_other_station")
                continue
            if option.arrival is None and station == option.station and distances[member] <= CAPTURE_RADIUS_M:
                option.arrival = step
                self.events.append({"kind": "arrival", "option_type": "transfer",
                                    "step": step, "member": member, "station": option.station})
            reason = None
            if energy["battery"][member] >= 1.0:
                reason = "full"
            elif step - option.start >= TIMEOUT:
                reason = "timeout_no_arrival" if option.arrival is None else "timeout"
            elif option.arrival is not None and step - option.arrival >= option.duration:
                reason = "dwell"
            if reason is not None:
                self._release_transfer(member, step, reason)
        super()._observe(observations, step)
        self.heuristic.committed[list(self.transfers)] = True

    def _release_transfer(self, member: int, step: int, reason: str) -> None:
        option = self.transfers.pop(member)
        self.events.append({"kind": "release", "option_type": "transfer",
                            "step": step, "member": member, "station": option.station,
                            "reason": reason, "arrival": option.arrival,
                            "dwell_elapsed": None if option.arrival is None else step-option.arrival})
        self._pending_restoration.add(member)

    def _candidates(self, observations, modes, step: int) -> list[tuple]:
        layout = self.heuristic.layout
        xyz = own_positions(observations, layout)
        energy = own_energy(observations, layout)
        margin, battery, nearest, _, _ = decode_legal_observations(observations)
        effective = _effective_modes(modes, margin)
        records = station_records(observations, layout)
        stations = records["xyz_m"][0]
        valid = records["valid"][0]
        capacities = records["capacity_ratio"][0].astype(float) * 8 * 1000.0
        intended = nearest.copy()
        for member, option in self.transfers.items():
            intended[member] = option.station
        counts = np.bincount(intended.astype(int), minlength=2)
        occupied = {option.station for option in self.options.values()}
        occupied.update(option.station for option in self.transfers.values())
        occupied.update(int(nearest[i]) for i in np.flatnonzero(effective))
        draw, _ = self._draw_w(step)
        remaining = layout.max_steps - step
        rejected: dict[str, int] = {}
        candidates = []

        def reject(reason):
            rejected[reason] = rejected.get(reason, 0) + 1

        for member in range(8):
            origin = int(nearest[member])
            destination = 1 - origin
            if len(self.options) + len(self.transfers) >= 2:
                reject("option_limit")
                continue
            if member in self.options or member in self.transfers:
                reject("member_active")
                continue
            if effective[member]:
                reject("member_effective_f")
                continue
            if not energy["available"][member]:
                reject("member_unavailable")
                continue
            if not valid[origin] or not valid[destination] or not np.isfinite(stations).all():
                reject("station_unobserved")
                continue
            if counts[origin] * HOVER_W <= capacities[origin]:
                reject("source_under_capacity")
                continue
            if (counts[destination]+1)*HOVER_W > capacities[destination]:
                reject("destination_full")
                continue
            if destination in occupied:
                reject("destination_busy")
                continue
            target = self.heuristic.h1_targets_xy[member]
            if not np.isfinite(target).all():
                reject("no_service_target")
                continue
            vector = stations[destination] - xyz[member]
            tau = _arrival_time(vector)
            max_distance = max_nearest_distance(xyz[member], stations[destination], stations)
            required = .10 + (self.max_power_w*tau + self.limp_power_w*max_distance/3.0)/(BATTERY_WH*3600.0)
            slack = (float(battery[member])-required)*BATTERY_WH*3600.0/max(HOVER_W, float(draw[member]))
            if slack <= 0.0:
                reject("nonpositive_slack")
                continue
            if slack > 630.0:
                reject("nonurgent_slack")
                continue
            distance = float(np.linalg.norm(vector))
            capture = (xyz[member] + vector * max(0.0, distance-CAPTURE_RADIUS_M)/distance
                       if distance > CAPTURE_RADIUS_M else xyz[member])
            tau_out = _restoration_time(capture, target)
            arrivals = []
            for other in range(8):
                if (other == member or int(nearest[other]) != destination or effective[other]
                        or other in self.options or other in self.transfers
                        or not energy["available"][other]):
                    continue
                peer_tau = _arrival_time(stations[destination]-xyz[other])
                peer_deadline = max(0.0, float(margin[other]))*BATTERY_WH*3600.0/max(HOVER_W, float(draw[other]))
                arrivals.append(peer_deadline + peer_tau)
            next_arrival = min(arrivals, default=math.inf)
            peer_feasible = [j for j, dwell in enumerate(DURATIONS)
                             if tau + dwell <= next_arrival]
            if not peer_feasible:
                reject("destination_peer_arrival")
                continue
            feasible = [j for j in peer_feasible
                        if tau + DURATIONS[j] + 10 + tau_out <= remaining]
            if not feasible:
                reject("horizon_restoration")
                continue
            load = np.asarray(observations)[:, layout.energy_uavs].reshape(8, 8, 13)
            own_load = float(load[member, member, 7])
            candidates.append((slack, own_load, tau, member, feasible[-1], destination,
                               required, next_arrival, tau_out, counts.tolist()))
        self.feasibility_rejections = rejected
        return sorted(candidates)

    def prepare(self, observations, modes, step: int):
        features = super().prepare(observations, modes, step)
        self._prepared["eligible"][list(self.transfers)] = False
        self._prepared["free"][list(self.transfers)] = False
        _, _, nearest, _, _ = decode_legal_observations(observations)
        occupied = {option.station for option in self.transfers.values()}
        for member in range(8):
            if int(nearest[member]) in occupied:
                self._prepared["eligible"][member] = False
        self._prepared["eligible"][:] &= len(self.options) + len(self.transfers) < 2
        self._prepared["features"][:8] = self._prepared["eligible"].astype(np.float32)
        self._prepared["transfer_candidates"] = self._candidates(observations, modes, step)
        return self._prepared["features"].copy()

    def ordinary_action(self) -> int:
        candidates = self._prepared["transfer_candidates"]
        if candidates:
            _, _, _, member, j, *_ = candidates[0]
            return transfer_action(member, j)
        return super().ordinary_action()

    def apply_choice(self, action: int) -> dict:
        if not TRANSFER_BASE <= action < TRANSFER_BASE + TRANSFER_ACTIONS:
            if self._prepared is not None:
                self._prepared["eligible"][:] &= len(self.options) + len(self.transfers) < 2
                self._prepared["eligible"][list(self.transfers)] = False
            record = super().apply_choice(action)
            record["active_commitments"] = len(self.options) + len(self.transfers)
            record["feasibility_rejections"] = self.feasibility_rejections.copy()
            self.diagnostics[-1].update(record)
            return record
        p = self._prepared
        if p is None or p.get("choice_applied"):
            raise RuntimeError("prepare and one choice per macro clock required")
        member = (action-TRANSFER_BASE)//3
        j = (action-TRANSFER_BASE)%3
        match = next((item for item in p["transfer_candidates"]
                      if item[3] == member and item[4] == j), None)
        p["choice_applied"] = True
        executed = (match is not None and len(self.options) + len(self.transfers) < 2
                    and member not in self.options and member not in self.transfers)
        if executed:
            _, _, tau, _, _, station, required, peer_arrival, tau_out, counts = match
            option = Transfer(member, station, DURATIONS[j], int(p["step"]))
            self.transfers[member] = option
            self.heuristic.committed[member] = True
            self.events.append({"kind": "start", "option_type": "transfer",
                                "step": int(p["step"]), "member": member,
                                "station": station, "duration": option.duration,
                                "tau": tau, "required_battery": required,
                                "peer_arrival": peer_arrival if math.isfinite(peer_arrival) else None,
                                "tau_out": tau_out, "group_counts": counts})
        record = {"step": int(p["step"]), "requested_action": int(action),
                  "executed_action": int(action) if executed else 0,
                  "member": member, "duration": DURATIONS[j],
                  "eligible": bool(p["transfer_candidates"]),
                  "requested_member_eligible": executed,
                  "active_commitments": len(self.options) + len(self.transfers),
                  "feasibility_rejections": self.feasibility_rejections.copy()}
        self.diagnostics.append(record)
        self.macro_choices += 1
        return record.copy()

    def propose(self, observations, state, step, previous_done, modes):
        action = super().propose(observations, state, step, previous_done, modes)
        xyz = own_positions(observations, self.heuristic.layout)
        records = station_records(observations, self.heuristic.layout)
        _, _, nearest, distances, vectors = decode_legal_observations(observations)
        for member, option in self.transfers.items():
            if int(nearest[member]) == option.station:
                vector = vectors[member]
                dock = 1.0
                if distances[member] <= DOCKING_RADIUS_M:
                    action[member] = np.asarray((0, 0, 0, dock), dtype=np.float32)
                    continue
            else:
                vector = records["xyz_m"][member, option.station] - xyz[member]
                dock = 0.0
            duration = max(1.0, float(np.linalg.norm(vector[:2]))/HORIZONTAL_SPEED_MPS,
                           abs(float(vector[2]))/VERTICAL_SPEED_MPS)
            velocity = vector/duration
            action[member] = np.asarray((velocity[0]/HORIZONTAL_SPEED_MPS,
                                         velocity[1]/HORIZONTAL_SPEED_MPS,
                                         velocity[2]/VERTICAL_SPEED_MPS, dock), dtype=np.float32)
        return action

    def commitment_snapshot(self):
        result = super().commitment_snapshot()
        result["kind"] = np.where(result["active"], 1, 0).astype(np.int8)
        for member, option in self.transfers.items():
            result["active"][member] = True
            result["kind"][member] = 2
            result["station"][member] = option.station
            result["start_step"][member] = option.start
            result["arrival_step"][member] = -1 if option.arrival is None else option.arrival
            result["duration"][member] = option.duration
        return result

    def finish(self, step, observations=None, modes=None):
        if modes is not None:
            self._real_modes = np.asarray(modes, dtype=bool).copy()
        super().finish(step, observations, modes)
        for member, option in self.transfers.items():
            self.events.append({"kind": "censored", "option_type": "transfer",
                                "step": int(step), "member": member,
                                "station": option.station, "arrival": option.arrival,
                                "duration": option.duration})
