"""Current raw native-margin guard around the B10 station continuity sort."""

from __future__ import annotations

import numpy as np

from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv


class GuardedStationEnv(UAVEnergyAwareRelayEnv):
    def __init__(self, *args, station_rule: str = "O", **kwargs):
        if station_rule not in {"O", "G"}:
            raise ValueError("station_rule must be O or G")
        self.station_rule = station_rule
        self.selection_snapshots: list[dict] = []
        self._prior_actual_station = None
        super().__init__(*args, **kwargs)

    def _reset_energy_state(self):
        super()._reset_energy_state()
        self._prior_actual_station = np.full(self.n_uavs, -1, dtype=np.int64)
        self.selection_snapshots = []

    def _prepare_energy_actions(self, actions):
        # Capture only actual positive-input incumbency before native preparation
        # clears and recomputes targets for the current action.
        self._prior_actual_station = np.where(
            self.uav_charging & (self.last_energy_charged_wh > 0.0),
            self.uav_target_stations, -1,
        ).astype(np.int64, copy=True)
        return super()._prepare_energy_actions(actions)

    def _select_charging_uavs(self, eligible_by_station):
        original = super()._select_charging_uavs(eligible_by_station)
        prior = self._prior_actual_station
        if prior is None:
            prior = np.full(self.n_uavs, -1, dtype=np.int64)
        wait_before = self.charging_wait_steps.copy()
        battery = self.uav_battery_ratios.copy()  # Post-consumption, pre-input.
        margins = np.asarray(self._raw_return_energy_margins(), dtype=np.float64).copy()
        if margins.shape != (self.n_uavs,) or not np.isfinite(margins).all():
            raise RuntimeError("invalid current raw return-energy margins")
        selected = {}
        continuous = {}
        trigger = {}
        for station, candidates in eligible_by_station.items():
            cap = self.charging_station_capacity[station]
            slots = len(candidates) if np.isinf(cap) else max(0, int(cap))
            key = lambda member: (battery[member], -wait_before[member], member)
            incumbents = sorted((m for m in candidates if prior[m] == station), key=key)
            newcomers = sorted((m for m in candidates if prior[m] != station), key=key)
            c = (incumbents + newcomers)[:slots]
            continuous[station] = c
            excluded = set(candidates) - set(c)
            trigger[station] = bool(any(margins[m] < 0.0 for m in excluded))
            selected[station] = list(original[station] if self.station_rule == "O" or trigger[station] else c)
        self.selection_snapshots.append({
            "rule": self.station_rule,
            "prior_actual_station": prior.astype(int).tolist(),
            "current_target_station": self.uav_target_stations.astype(int).tolist(),
            "battery_after_consumption": battery.astype(float).tolist(),
            "raw_margin_before_input": margins.astype(float).tolist(),
            "wait_age_before_selection": wait_before.astype(int).tolist(),
            "eligible_by_station": {str(k): list(v) for k, v in eligible_by_station.items()},
            "original_selected": {str(k): list(v) for k, v in original.items()},
            "continuous_selected": {str(k): list(v) for k, v in continuous.items()},
            "guard_trigger": {str(k): trigger[k] for k in eligible_by_station},
            "actual_selected": {str(k): list(v) for k, v in selected.items()},
        })
        return selected
