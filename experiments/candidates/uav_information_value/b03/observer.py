"""Read-only B03 trace of lawful inputs and exact native realized motion."""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.heuristic import observed_bs_xy
from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT, station_records
from experiments.candidates.uav_information_value.batch import InformationObserver
from experiments.candidates.uav_information_value.b02.readout import battery_reading


SOURCES = ("absent", "inferred", "observed-current", "observed-memory")


class AnchorObserver(InformationObserver):
    def __init__(self, arm, raw_env):
        super().__init__(arm)
        self.raw_env = raw_env
        self.native_battery = []
        self.native_pre_xyz = []
        self.native_post_xyz = []
        self.proposals = []
        self.submitted = []
        self.current_bs_xy = []
        self.memory_bs_xy = []
        self.held_plan_sources = []
        self.prior_bs_xy = None
        self.reset_station_xyz = None
        self.reset_station_valid = None
        self._previous_xyz = None

    @contextmanager
    def attach(self, controller):
        self._previous_xyz = np.asarray(self.raw_env.uav_positions, dtype=np.float64).copy()
        try:
            yield
        finally:
            self._previous_xyz = None

    def on_step(self, *, t, observations_t, proposal_t, submitted_t, controller, **kwargs):
        if t == 0:
            records = station_records(observations_t, S7S2_LAYOUT)
            self.reset_station_xyz = np.asarray(records["xyz_m"], dtype=np.float64).copy()
            self.reset_station_valid = np.asarray(records["valid"], dtype=bool).copy()
        current = observed_bs_xy(observations_t, S7S2_LAYOUT)
        memory = controller._seen_bs_xy
        self.current_bs_xy.append(np.full(2, np.nan) if current is None else current.copy())
        self.memory_bs_xy.append(np.full(2, np.nan) if memory is None else memory.copy())
        self.proposals.append(np.asarray(proposal_t, dtype=np.float32).copy())
        self.submitted.append(np.asarray(submitted_t, dtype=np.float32).copy())
        post = np.asarray(self.raw_env.uav_positions, dtype=np.float64).copy()
        self.native_pre_xyz.append(self._previous_xyz.copy())
        self.native_post_xyz.append(post)
        self._previous_xyz = post
        self.native_battery.append(np.asarray(self.raw_env.uav_battery_ratios, dtype=np.float64).copy())
        super().on_step(t=t, observations_t=observations_t, controller=controller, **kwargs)
        if t % 30 == 0:
            plan = controller.heuristic.last_plan
            diagnostic = controller.diagnostics[-1]
            source = diagnostic.get("bs_input_source", "observed-current" if current is not None
                                    else "observed-memory" if memory is not None else "absent")
            if source == "inferred" and self.bs_seen[-1]:
                raise RuntimeError("anchor used after real BS sighting")
            relay_count = len(plan["relays"])
            # H1 assigns the relay-first priority prefix to available UAVs;
            # finite planner targets count that capacity without another solve.
            targets = np.asarray(plan["targets"], dtype=np.float64)
            assigned = min(relay_count, int(np.isfinite(targets).all(axis=1).sum()))
            row = self.plans[-1]
            row.update(bs_input_source=source, prior_used=bool(diagnostic.get("prior_used", False)),
                       generated_relay_count=relay_count, assigned_relay_count=int(assigned),
                       bs_input_xy=np.full(2, np.nan) if plan["bs_xy"] is None else plan["bs_xy"].copy(),
                       centroids_xy=np.asarray(plan["centroids"]).copy(),
                       relays_xy=np.asarray(plan["relays"]).copy(),
                       targets_xy=targets.copy(),
                       reset_station0_xy=(self.reset_station_xyz[np.flatnonzero(self.reset_station_valid[:, 0])[0], 0, :2].copy()
                                          if self.reset_station_valid[:, 0].any() else np.full(2, np.nan)))
            prior = getattr(controller, "prior_bs_xy", None)
            self.prior_bs_xy = None if prior is None else np.asarray(prior, dtype=np.float64).tolist()
        self.held_plan_sources.append(self.plans[-1]["bs_input_source"])

    def arrays(self):
        result = {
            "info_bs_present": np.asarray(self.bs_present, dtype=bool),
            "info_bs_seen": np.asarray(self.bs_seen, dtype=bool),
        }
        for key in ("step", "legal_user_count", "supplied_user_count", "legal_bs_present",
                    "bs_seen_so_far", "known_bs_omitted", "legal_bs_absent_after_seen",
                    "memory_used", "search", "bs_input_source", "prior_used",
                    "generated_relay_count", "assigned_relay_count", "bs_input_xy",
                    "targets_xy", "reset_station0_xy"):
            result[f"info_plan_{key}"] = np.asarray([row[key] for row in self.plans])
        # Variable centroid counts cannot be represented as a rectangular numeric
        # array; the fixed six slots use NaN padding and an explicit count.
        for key in ("centroids_xy", "relays_xy"):
            width = 6 if key == "centroids_xy" else 2
            padded = np.full((len(self.plans), width, 2), np.nan, dtype=np.float64)
            for index, row in enumerate(self.plans):
                values = row[key]
                padded[index, :len(values)] = values
            result[f"info_plan_{key}"] = padded
        result["info_plan_centroid_count"] = np.asarray([len(row["centroids_xy"]) for row in self.plans], dtype=np.int64)
        result.update(
            info_reset_station_xyz=np.asarray(self.reset_station_xyz, dtype=np.float64),
            info_reset_station_valid=np.asarray(self.reset_station_valid, dtype=bool),
            info_current_bs_xy=np.asarray(self.current_bs_xy, dtype=np.float64),
            info_observed_memory_bs_xy=np.asarray(self.memory_bs_xy, dtype=np.float64),
            info_held_plan_source=np.asarray(self.held_plan_sources, dtype="U16"),
            info_controller_proposal=np.asarray(self.proposals, dtype=np.float32),
            info_shield_submitted=np.asarray(self.submitted, dtype=np.float32),
            info_native_pre_xyz=np.asarray(self.native_pre_xyz, dtype=np.float64),
            info_native_post_xyz=np.asarray(self.native_post_xyz, dtype=np.float64),
            info_native_delta_xyz=np.asarray(self.native_post_xyz, dtype=np.float64) - np.asarray(self.native_pre_xyz, dtype=np.float64),
            info_native_battery=np.asarray(self.native_battery, dtype=np.float64),
        )
        return result

    def reading(self):
        prior_steps = [row["step"] for row in self.plans if row["prior_used"]]
        return super().reading() | battery_reading(self.native_battery) | {
            "prior_bs_xy": self.prior_bs_xy,
            "prior_used_plans": len(prior_steps),
            "first_prior_use_step": prior_steps[0] if prior_steps else None,
            "generated_relay_count_sum": sum(row["generated_relay_count"] for row in self.plans),
            "assigned_relay_count_sum": sum(row["assigned_relay_count"] for row in self.plans),
            "native_movement_m_sum": float(np.linalg.norm(self.arrays()["info_native_delta_xyz"], axis=2).sum()),
        }
