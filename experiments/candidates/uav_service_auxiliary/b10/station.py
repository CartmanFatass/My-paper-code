"""Candidate-local station allocation; the native physical path remains unchanged."""

from __future__ import annotations

import numpy as np

from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv


class ContinuityStationEnv(UAVEnergyAwareRelayEnv):
    def __init__(self, *args, station_rule: str = "O", **kwargs):
        if station_rule not in {"O", "C"}:
            raise ValueError("station_rule must be O or C")
        self.station_rule = station_rule
        self.selection_snapshots: list[dict] = []
        self._prior_actual_station = None
        super().__init__(*args, **kwargs)

    def _reset_energy_state(self):
        super()._reset_energy_state()
        self._prior_actual_station = np.full(self.n_uavs, -1, dtype=np.int64)
        self.selection_snapshots = []

    def _prepare_energy_actions(self, actions):
        # Native preparation clears/recomputes targets. Capture the station that
        # *actually supplied positive input* before that happens.
        self._prior_actual_station = np.where(
            self.uav_charging & (self.last_energy_charged_wh > 0.0),
            self.uav_target_stations, -1,
        ).astype(np.int64, copy=True)
        return super()._prepare_energy_actions(actions)

    def _select_charging_uavs(self, eligible_by_station):
        original = super()._select_charging_uavs(eligible_by_station)
        selected = {station: list(members) for station, members in original.items()}
        prior = self._prior_actual_station
        if prior is None:
            prior = np.full(self.n_uavs, -1, dtype=np.int64)
        wait_before = self.charging_wait_steps.copy()
        battery_at_selection = self.uav_battery_ratios.copy()
        if self.station_rule == "C":
            for station, candidates in eligible_by_station.items():
                cap = self.charging_station_capacity[station]
                slots = len(candidates) if np.isinf(cap) else max(0, int(cap))
                key = lambda member: (battery_at_selection[member], -wait_before[member], member)
                incumbents = sorted(
                    (member for member in candidates if prior[member] == station), key=key
                )
                newcomers = sorted(
                    (member for member in candidates if prior[member] != station), key=key
                )
                selected[station] = (incumbents + newcomers)[:slots]
        self.selection_snapshots.append({
            "prior_actual_station": prior.astype(int).tolist(),
            "current_target_station": self.uav_target_stations.astype(int).tolist(),
            "battery_after_consumption": battery_at_selection.astype(float).tolist(),
            "wait_age_before_selection": wait_before.astype(int).tolist(),
            "eligible_by_station": {str(k): list(v) for k, v in eligible_by_station.items()},
            "original_selected": {str(k): list(v) for k, v in original.items()},
            "actual_selected": {str(k): list(v) for k, v in selected.items()},
        })
        return selected
