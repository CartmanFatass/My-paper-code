"""Service-weighted scheduling around the frozen B03 R execution path."""

from __future__ import annotations

import copy
import math

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.feedback import decode_legal_observations
from experiments.candidates.energy_relay_benchmark.b01.heuristic import LayoutHeuristic
from experiments.candidates.energy_relay_benchmark.b01.observation import (
    layout_from_env, own_energy, own_positions, station_records,
)
from experiments.candidates.uav_persistent_service.b03.controller import (
    ReassignmentController, TRANSFER_BASE, transfer_action,
)
from experiments.candidates.uav_persistent_service.controllers import (
    BATTERY_WH, CAPTURE_RADIUS_M, DURATIONS, HOVER_W, N_ACTIONS,
    _effective_modes,
)

from .forecast import ForecastInput, ForecastOption, _capture_point, forecast


class ServiceShiftController(ReassignmentController):
    def __init__(self, env, config):
        super().__init__(env, config)
        self.heuristic.layout = layout_from_env(env.env)

    def reset(self) -> None:
        super().reset()
        self.scheduler_snapshot_calls = 0
        self.member_bin_updates = 0
        self.forecast_grids = 0
        self._charged_without_decoded_arrival: set[tuple[str, int, int]] = set()

    def _observe(self, observations, step: int) -> None:
        if self._last_observed_step == step:
            return
        super()._observe(observations, step)
        energy = own_energy(observations, self.heuristic.layout)
        unresolved = set()
        for kind, source in (("ordinary", self.options), ("transfer", self.transfers)):
            for member, option in source.items():
                if option.arrival is None:
                    key = (kind, member, option.start)
                    unresolved.add(key)
                    if energy["charging"][member] or energy["waiting_steps"][member] > 0:
                        self._charged_without_decoded_arrival.add(key)
        self._charged_without_decoded_arrival.intersection_update(unresolved)

    def _radio_weights(self, observations, modes, xyz, stations, battery, nearest):
        # LayoutHeuristic.plan uses only the copied H1 continuation memory and legal central snapshot.
        shadow = copy.copy(self.heuristic)
        shadow.targets_xy = self.heuristic.h1_targets_xy.copy()
        full = LayoutHeuristic.plan(shadow, observations, np.zeros(8, dtype=bool), self._central)
        priority = full["priority"]
        base = full["targets"].copy()
        nominal = np.c_[base, np.full(8, self.heuristic.params.height_m)]
        if not np.isfinite(nominal).all():
            raise ValueError("full-fleet H1 target is non-finite")
        scorer = self.heuristic._service_qos_at_snapshot
        q0 = scorer(self.env.env, self._central, nominal, battery)
        self.scheduler_snapshot_calls += 1
        weights = np.zeros(8, dtype=float)
        intended = nearest.copy()
        for member, option in self.transfers.items():
            intended[member] = option.station
        for member in range(8):
            station = int(intended[member])
            point = _capture_point(xyz[member], stations[station])
            rematched = np.full((8, 2), np.nan)
            shadow.targets_xy = self.heuristic.h1_targets_xy.copy()
            others = np.asarray([i for i in range(8) if i != member], dtype=int)
            shadow._assign_targets(xyz[:, :2], others, priority[:7], rematched)
            if not np.isfinite(rematched[others]).all():
                raise ValueError("H1 rematch is non-finite")
            projected = np.c_[rematched, np.full(8, self.heuristic.params.height_m)]
            projected[member] = point
            qi = scorer(self.env.env, self._central, projected, battery)
            self.scheduler_snapshot_calls += 1
            weights[member] = max(0.0, q0-qi)
        return float(q0), weights, base

    def _transfer_alternatives(self):
        expanded = []
        for item in self._prepared["transfer_candidates"]:
            slack, load, tau, member, _, station, required, peer, outbound, counts = item
            for j, duration in enumerate(DURATIONS):
                if tau+duration <= peer and tau+duration+10+outbound <= self._prepared["remaining"]:
                    expanded.append((slack, load, tau, member, j, station,
                                     required, peer, outbound, counts))
        return expanded

    def _ordinary_alternatives(self, modes):
        p = self._prepared
        effective = _effective_modes(modes, p["margin"])
        eligible = p["eligible"] & ~effective
        deadline = np.maximum(0.0, p["margin"])*BATTERY_WH*3600/np.maximum(HOVER_W, p["draw_w"])
        limit = min(1200, p["remaining"])
        result = []
        for member in np.flatnonzero(eligible & (deadline <= limit)):
            arrivals = [deadline[other]+p["tau_in"][other] for other in range(8)
                        if other != member and p["free"][other]
                        and p["station"][other] == p["station"][member]
                        and np.isfinite(p["tau_in"][other])]
            peer = min(arrivals, default=math.inf)
            for j, duration in enumerate(DURATIONS):
                if (p["tau_in"][member]+duration <= peer and
                        p["tau_in"][member]+duration+10+p["tau_out"][member] <= p["remaining"]):
                    result.append(1+3*int(member)+j)
        return result

    def _forecast_input(self, observations, modes, q0, weights, nominal_targets):
        layout = self.heuristic.layout
        xyz = own_positions(observations, layout)
        energy = own_energy(observations, layout)
        records = station_records(observations, layout)
        stations = records["xyz_m"][0]
        slots = np.rint(records["capacity_ratio"][0].astype(float)*8).astype(int)
        options = []
        for source in (self.options, self.transfers):
            for member, option in source.items():
                kind = "transfer" if source is self.transfers else "ordinary"
                key = (kind, member, option.start)
                options.append(ForecastOption(
                    member, option.station, option.duration, int(self._prepared["step"]-option.start),
                    None if option.arrival is None else int(option.arrival-option.start),
                    bool(option.arrival is None and
                         (key in self._charged_without_decoded_arrival
                          or energy["charging"][member]
                          or energy["waiting_steps"][member] > 0)),
                    source is self.transfers,
                ))
        return ForecastInput(
            xyz=xyz, stations=stations, targets_xy=nominal_targets,
            battery=energy["battery"], available=energy["available"],
            modes=_effective_modes(modes, self._prepared["margin"]),
            charging=energy["charging"], waiting=energy["waiting_steps"],
            draw_w=self._prepared["draw_w"], slots=slots, weights=weights, q0=q0,
            options=tuple(options), remaining=int(self._prepared["remaining"]),
            limp_power_w=self.limp_power_w, max_power_w=self.max_power_w,
            reserve_ratio=float(self.env.env.return_reserve_ratio),
            cutoff_ratio=float(self.env.env.service_cutoff_threshold),
            emergency_ratio=float(self.env.env.emergency_return_threshold),
        )

    def prepare(self, observations, modes, step: int):
        features = super().prepare(observations, modes, step)
        p = self._prepared
        if "scheduler" in p:
            return features
        r_action = super().ordinary_action()
        expanded = self._transfer_alternatives()
        if expanded:
            p["transfer_candidates"] = expanded
            actions = [0] + [transfer_action(item[3], item[4]) for item in expanded]
        else:
            actions = [0] + self._ordinary_alternatives(np.asarray(modes, dtype=bool))
        actions = list(dict.fromkeys([*actions, int(r_action)]))
        p["scheduler"] = {"r_action": int(r_action), "candidate_actions": actions,
                          "fallback": None, "q0": None, "weights": None,
                          "candidate_scores": [], "chosen_forecast": None}
        starting_queries = self.scheduler_snapshot_calls
        starting_updates = self.member_bin_updates
        starting_grids = self.forecast_grids
        try:
            energy = own_energy(observations, self.heuristic.layout)
            xyz = own_positions(observations, self.heuristic.layout)
            stations = station_records(observations, self.heuristic.layout)["xyz_m"][0]
            _, _, nearest, _, _ = decode_legal_observations(observations)
            q0, weights, nominal_targets = self._radio_weights(
                observations, modes, xyz, stations, energy["battery"], nearest)
            view = self._forecast_input(observations, modes, q0, weights, nominal_targets)
            arrays = (view.xyz, view.stations, view.targets_xy, view.battery, view.draw_w,
                      view.weights, view.waiting)
            if not all(np.isfinite(array).all() for array in arrays):
                raise ValueError("non-finite scheduler input")
            if not (0 <= q0 <= 1) or np.any(weights < 0) or np.any(view.slots < 0):
                raise ValueError("inconsistent scheduler input")
            scored = []
            selected_forecast = None
            best_key = None
            for action in actions:
                option = None
                if action:
                    member = ((action-TRANSFER_BASE)//3 if action >= TRANSFER_BASE else (action-1)//3)
                    j = ((action-TRANSFER_BASE)%3 if action >= TRANSFER_BASE else (action-1)%3)
                    station = (next(item[5] for item in expanded if item[3] == member and item[4] == j)
                               if action >= TRANSFER_BASE else int(p["station"][member]))
                    immediate_arrival = (action < TRANSFER_BASE
                                         and p["distance"][member] <= CAPTURE_RADIUS_M)
                    option = ForecastOption(member, station, DURATIONS[j], 0,
                                            0 if immediate_arrival else None,
                                            transfer=action >= TRANSFER_BASE)
                result = forecast(view, option)
                self.member_bin_updates += result["member_bin_updates"]
                self.forecast_grids += result["grid_bins"]
                score = (result["cutoff_ticks"]+result["depletion_ticks"],
                         -result["min_qhat"], -result["integral_qhat"],
                         result["reserve_ticks"])
                tie = (0 if action == r_action else 1,
                       8 if action == 0 else option.member,
                       0 if action == 0 else option.duration)
                key = (*score, *tie)
                scored.append({"action": int(action), "score": [float(x) for x in score]})
                if best_key is None or key < best_key:
                    best_key, selected_forecast = key, result
                    selected = int(action)
            p["scheduler"].update(q0=q0, weights=weights.tolist(), candidate_scores=scored,
                                  chosen_action=selected, chosen_forecast=selected_forecast,
                                  scheduler_snapshot_calls=self.scheduler_snapshot_calls-starting_queries,
                                  member_bin_updates=self.member_bin_updates-starting_updates,
                                  grid_bins=selected_forecast["grid_bins"])
        except (ValueError, FloatingPointError, OverflowError) as exc:
            p["scheduler"].update(chosen_action=int(r_action), fallback=str(exc),
                                  candidate_scores=[],
                                  scheduler_snapshot_calls=self.scheduler_snapshot_calls-starting_queries,
                                  member_bin_updates=self.member_bin_updates-starting_updates,
                                  grid_bins=self.forecast_grids-starting_grids)
        margin = np.asarray(p["margin"], dtype=float)
        deadline = np.maximum(0.0, margin)*BATTERY_WH*3600/np.maximum(HOVER_W, p["draw_w"])
        transfer_slack = []
        for item in expanded:
            slack, _, tau, member, duration_index, _, _, peer, outbound, _ = item
            duration = DURATIONS[duration_index]
            next_access = bool(0 < slack-30 <= 630 and tau+duration <= peer-30
                               and tau+duration+10+outbound <= p["remaining"]-30)
            transfer_slack.append({
                "member": int(member), "duration": int(duration),
                "trip_energy_slack_s": float(slack),
                "next_clock_trip_energy_slack_s": float(slack-30),
                "next_clock_nominal_access": next_access,
            })
        p["scheduler"]["defer"] = {
            "return_deadline_s": deadline.tolist(),
            "next_clock_return_deadline_s": (deadline-30).tolist(),
            "transfer_candidates": transfer_slack,
            "transfer_access_now": bool(expanded),
            "transfer_access_next_clock_nominal": [item["next_clock_nominal_access"]
                                                   for item in transfer_slack],
            "predicted_access_loss": bool(expanded) and not any(
                item["next_clock_nominal_access"] for item in transfer_slack),
        }
        return features

    def ordinary_action(self) -> int:
        if self._prepared is None or "scheduler" not in self._prepared:
            raise RuntimeError("prepare before ordinary_action")
        return int(self._prepared["scheduler"]["chosen_action"])

    def apply_choice(self, action: int) -> dict:
        scheduler = copy.deepcopy(self._prepared["scheduler"])
        record = super().apply_choice(action)
        scheduler["requested_action"] = int(action)
        scheduler["executed_action"] = int(record["executed_action"])
        scheduler["member"] = record["member"]
        scheduler["duration"] = record["duration"]
        record["scheduler"] = scheduler
        self.diagnostics[-1]["scheduler"] = scheduler
        return record

    @property
    def costs(self) -> dict[str, int]:
        return {**super().costs,
                "scheduler_snapshot_calls": self.scheduler_snapshot_calls,
                "member_bin_updates": self.member_bin_updates,
                "forecast_grid_bins": self.forecast_grids}
