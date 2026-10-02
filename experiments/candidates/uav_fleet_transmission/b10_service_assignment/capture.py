"""Read-only typed trajectory capture around the unchanged native serial evaluator."""
from __future__ import annotations

from contextlib import nullcontext
import time

import numpy as np

from .contract import BS_SOURCES, EVENTS


def padded(values, width, *, dtype=None, fill=np.nan):
    values = np.asarray(values, dtype=dtype)
    if len(values) > width:
        raise ValueError("bounded trace width exceeded")
    result = np.full((width, *values.shape[1:]), fill, dtype=values.dtype)
    result[:len(values)] = values
    return result


def plan_record(controller, step):
    plan = controller.heuristic.last_plan
    diagnostic = controller.diagnostics[-1]
    result = dict(
        plan_step=np.int32(step), plan_user_count=np.int16(len(plan["users"])),
        plan_users=padded(plan["users"], 30, dtype=np.float64),
        plan_bs=np.full(2, np.nan) if plan["bs_xy"] is None else np.asarray(plan["bs_xy"]).copy(),
        plan_bs_source=np.int8(BS_SOURCES.index(diagnostic["bs_input_source"])),
        plan_centroid_count=np.int8(len(plan["centroids"])),
        plan_centroids=padded(plan["centroids"], 6, dtype=np.float64),
        plan_counts=padded(plan["counts"], 6, dtype=np.int16, fill=-1),
        plan_relay_count=np.int8(len(plan["relays"])),
        plan_relays=padded(plan["relays"], 2, dtype=np.float64),
        plan_targets=np.asarray(plan["targets"], dtype=np.float64).copy(),
        plan_priority_count=np.int8(len(plan["priority"])),
        plan_priority=padded(plan["priority"],8,dtype=np.float64),
        plan_ring_count=np.int8(len(plan["search_waypoints"])),
        plan_ring=padded(plan["search_waypoints"],8,dtype=np.float64),
        plan_search=np.bool_(plan["search"]),
    )
    targets = getattr(controller, "targets_xyz", None)
    if targets is None:
        targets = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
    detail = getattr(controller, "last_decision", None) or {}
    future = np.full((3, 30, 2), np.nan, dtype=np.float64)
    if "future_xy" in detail and np.asarray(detail["future_xy"]).shape[1]:
        if np.asarray(detail["future_xy"]).shape != (3,len(plan["users"]),2):
            raise AssertionError("current-only future map differs from actual C users")
        future[:, :len(plan["users"])] = detail["future_xy"]
    result.update(plan_targets_xyz=np.asarray(targets, dtype=np.float64).copy(),
                  plan_candidate_first=np.int32(detail.get("candidate_first", 0)),
                  plan_candidate_count=np.int16(detail.get("candidate_count", 0)),
                  plan_selected_candidate=np.int16(detail.get("selected", -1)),
                  plan_fallback=np.int8(detail.get("fallback", -1)),
                  plan_prediction_xy=future)
    velocity=np.full((30,2),np.nan,dtype=np.float64)
    if len(detail.get("current_velocities", [])):
        velocity[:len(plan["users"])]=detail["current_velocities"]
    result.update(
        plan_ordinary_targets=np.asarray(detail.get("ordinary_targets",plan["targets"]),dtype=np.float64).copy(),
        plan_assignment_role=np.asarray(detail.get("assignment_role",np.zeros(8)),dtype=np.int8),
        plan_assignment_call=np.asarray(detail.get("assignment_call",np.zeros(8)),dtype=np.int8),
        plan_assignment_column=np.asarray(detail.get("assignment_column",np.full(8,-1)),dtype=np.int16),
        plan_eligible=np.asarray(detail.get("eligible",np.zeros(8)),dtype=bool),
        plan_selected_pair=np.asarray(detail.get("selected_pair",[-1,-1]),dtype=np.int8),
        plan_current_velocities=velocity,
        plan_clock=np.int32(controller.heuristic.calls),
    )
    return result


def memory_record(trace):
    tracks = trace["tracks"]
    held = np.zeros(30, dtype=tracks.dtype)
    held["birth"] = -1
    held["last_seen"] = -1
    held[:len(tracks)] = tracks
    result = dict(
        trace_current_count=np.int16(len(trace["canonical_xy"])),
        trace_canonical=padded(trace["canonical_xy"], 30, dtype=np.float64),
        trace_kept_slots=padded(trace["kept_flat_indices"], 30, dtype=np.int16, fill=-1),
        trace_slot_merge=np.asarray(trace["raw_to_canonical"], dtype=np.int16),
        trace_track_count=np.int16(len(tracks)), trace_tracks=held,
    )
    for name in EVENTS:
        values = trace["events"][name]
        if int(trace["event_counts"][name]) != len(values):
            raise AssertionError("event count disagrees with event identities")
        result["event_" + name] = padded(values, 30, dtype=np.int32, fill=-1)
        result["event_count_" + name] = np.int16(len(values))
    return result


STATE_FIELDS = {
    "truth_user_xyz": "user_positions", "truth_uav_xyz": "uav_positions",
    "truth_bs_xyz": "ground_bs_positions", "truth_station_xyz": "charging_station_positions",
    "native_connections": "connections", "native_peer_connections": "uav_connections",
    "native_bs_connections": "uav_bs_connections", "native_battery": "uav_battery_ratios",
    "native_charging": "uav_charging", "native_failed": "uav_failed",
    "native_station_occupancy": "charging_station_occupancy",
    "native_station_queue": "charging_station_queue_lengths",
}
# These are already-computed native fields, copied without a radio/model/allocator call.
RAW_FIELDS = {
    "native_velocity": "last_actual_velocities",
    "native_consumed_wh": "last_energy_consumed_wh",
    "native_charged_wh": "last_energy_charged_wh",
    "native_net_charged_wh": "last_net_energy_charged_wh",
    "native_demand_bps": "last_user_demand_bps",
    "native_delivered_bps": "last_delivered_traffic_bps",
    "native_user_rates_mbps": "last_user_rates_mbps",
    "native_access_bps": "last_access_capacity_bps",
    "native_backhaul_bps": "last_backhaul_capacities_bps",
    "native_serviced": "user_serviced_status",
    "native_return_threshold": "uav_return_threshold_ratios",
    "native_return_margin": "uav_return_energy_margins",
    "native_dock": "uav_dock_requests",
    "native_target_station": "uav_target_stations",
    "native_waiting": "charging_wait_steps",
}
PARAMETERS = (
    "time_step", "max_steps", "area_size", "max_speed", "max_vertical_speed_mps",
    "battery_capacity_wh", "service_cutoff_threshold", "depleted_battery_threshold",
    "return_reserve_ratio", "return_margin_scale", "return_cost_cap",
    "limp_home_speed_mps", "charging_power_w", "charging_capture_radius_m",
    "charging_hover_speed_threshold", "P0", "Pi", "v0", "k1", "k2", "k3", "P_z_coeff",
    "reward_discount_gamma", "cutoff_event_penalty", "depletion_event_penalty",
    "observation_radius", "serving_set_size", "max_connections", "user_qos_rate_mbps",
)


class Recorder:
    def __init__(self, limit, arm):
        self.limit, self.arm = int(limit), arm
        self.native_steps = self.decision_steps = 0
        self.boundaries = {}
        self.decisions = {}
        self.plans = {}
        self.plan_count = 0
        self.reward_fields = None
        self.reward_values = None
        self.parameters = None
        self.native_ends = np.zeros((self.limit, 2), dtype=bool)
        self.native_reward = np.zeros(self.limit, dtype=np.float64)
        self.submitted = np.zeros((self.limit, 8, 4), dtype=np.float32)
        self.proposed = np.zeros_like(self.submitted)

    @staticmethod
    def _store(mapping, key, index, length, value):
        value = np.asarray(value)
        if value.dtype.kind == "O":
            raise TypeError("object trace forbidden: " + key)
        if key not in mapping:
            mapping[key] = np.empty((length, *value.shape), dtype=value.dtype)
        target = mapping[key]
        if target.shape[1:] != value.shape or target.dtype != value.dtype:
            raise ValueError("trace schema changed: " + key)
        target[index] = value

    def boundary(self, index, observations, info, raw):
        state = info["state_info"]
        values = {name: np.asarray(state[source]).copy() for name, source in STATE_FIELDS.items()}
        values.update({name: np.asarray(getattr(raw, source)).copy() for name, source in RAW_FIELDS.items()})
        values["observations"] = np.asarray(observations, dtype=np.float32).copy()
        routes = np.full((8, 9), -1, dtype=np.int16)
        capacity = np.zeros(8, dtype=np.float64)
        for member, (path, bandwidth) in state["routing_paths"].items():
            nodes = [int(number) + (8 if kind == "ground_bs" else 0) for kind, number in path]
            if len(nodes) > 9 or any(kind not in ("uav", "ground_bs") for kind, _ in path):
                raise ValueError("invalid native route encoding")
            routes[int(member), :len(nodes)] = nodes
            capacity[int(member)] = bandwidth
        values["native_routes"], values["native_route_capacity"] = routes, capacity
        values["native_serving_set_count"] = np.asarray([len(s) for s in raw.user_serving_sets], dtype=np.int16)
        for name, value in values.items():
            self._store(self.boundaries, name, index, self.limit + 1, value)
        if index == 0:
            self.parameters = {name: getattr(raw, name) for name in PARAMETERS}
            self.parameters.update(height_range=list(raw.height_range),
                                   station_capacity=raw.charging_station_capacity.tolist(),
                                   routing_protocol=raw.routing_protocol,
                                   enable_soft_handover=bool(raw.enable_soft_handover),
                                   predictive_handover=bool(raw.predictive_handover))

    def transition(self, observations, reward, terminated, truncated, info, raw):
        index = self.native_steps
        self.native_steps += 1  # Preserve observed exposure even if later capture rejects a schema.
        self.native_reward[index] = reward
        self.native_ends[index] = (terminated, truncated)
        self.boundary(index + 1, observations, info, raw)
        reward_info = info["reward_info"]
        fields = sorted(key for key, value in reward_info.items()
                        if isinstance(value, (int, float, np.number, bool)))
        if self.reward_fields is None:
            self.reward_fields = fields
            self.reward_values = np.empty((self.limit, len(fields)), dtype=np.float64)
        if fields != self.reward_fields:
            raise ValueError("reward scalar schema changed")
        self.reward_values[index] = [reward_info[key] for key in fields]

    def attach(self, controller):
        return nullcontext()

    def on_step(self, *, t, proposal_t, submitted_t, controller, **unused):
        if t != self.decision_steps or self.native_steps != t + 1:
            raise AssertionError("native/decision chronology differs")
        self.proposed[t] = proposal_t
        if not np.array_equal(self.submitted[t], submitted_t):
            raise AssertionError("collector saw different submitted command")
        if controller.heuristic.calls != t + 1:
            raise AssertionError("H1 call clock differs")
        target_xyz = getattr(controller, "targets_xyz", None)
        if target_xyz is None:
            target_xyz = np.column_stack((controller.heuristic.targets_xy, np.full(8, 100.0)))
        self._store(self.decisions, "decision_targets_xyz", t, self.limit,
                    np.asarray(target_xyz, dtype=np.float64))
        if self.arm in ("H_A", "F_A"):
            trace = controller.last_trace
            if trace["step"] != t or trace["replanned"] != (t % 30 == 0):
                raise AssertionError("tracker clock differs")
            for name, value in memory_record(trace).items():
                self._store(self.decisions, name, t, self.limit, value)
        if t % 30 == 0:
            for name, value in plan_record(controller, t).items():
                self._store(self.plans, name, self.plan_count, (self.limit + 29) // 30, value)
            self.plan_count += 1
        self.decision_steps += 1

    def arrays(self):
        n, d = self.native_steps, self.decision_steps
        result = {key: value[:n + 1] for key, value in self.boundaries.items()}
        result.update({key: value[:d] for key, value in self.decisions.items()})
        result.update({key: value[:self.plan_count] for key, value in self.plans.items()})
        result.update(proposed=self.proposed[:d], submitted=self.submitted[:n],
                      native_reward=self.native_reward[:n], native_ends=self.native_ends[:n],
                      recorded_native_steps=np.asarray(n), recorded_decision_steps=np.asarray(d))
        if self.reward_fields is not None:
            result.update(reward_scalar_fields=np.asarray(self.reward_fields), reward_scalars=self.reward_values[:n])
        return result


class CaptureEnv:
    """Keep the live adapter's returned diagnostics; no second native state/query call."""
    def __init__(self, adapter, recorder, engineering=False):
        self.env = adapter
        self.recorder = recorder
        self.engineering = bool(engineering)
        self.native_cpu_seconds = self.native_wall_seconds = 0.0
        self.reset_cpu_seconds = self.reset_wall_seconds = 0.0

    def reset(self, **kwargs):
        wall, cpu = time.perf_counter(), time.process_time()
        result = self.env.reset(**kwargs)
        self.reset_wall_seconds += time.perf_counter() - wall
        self.reset_cpu_seconds += time.process_time() - cpu
        self.recorder.boundary(0, *result, self.env.env)
        return result

    def step(self, submitted):
        self.recorder.submitted[self.recorder.native_steps] = submitted
        wall, cpu = time.perf_counter(), time.process_time()
        obs, reward, terminated, truncated, info = self.env.step(submitted)
        self.native_wall_seconds += time.perf_counter() - wall
        self.native_cpu_seconds += time.process_time() - cpu
        self.recorder.transition(obs, reward, terminated, truncated, info, self.env.env)
        # Only the evaluator receives this engineering harness stop. The native
        # H3000 configuration, transition reward and native flags remain saved unchanged.
        harness_stop = False
        return obs, reward, terminated, bool(truncated or harness_stop), info

    def close(self):
        self.env.close()


class TimedController:
    def __init__(self, controller):
        self.controller = controller
        self.proposal_cpu_seconds = self.proposal_wall_seconds = 0.0

    def __getattr__(self, name):
        return getattr(self.controller, name)

    def reset(self):
        self.controller.reset()

    def propose(self, *args):
        wall, cpu = time.perf_counter(), time.process_time()
        try:
            return self.controller.propose(*args)
        finally:
            self.proposal_cpu_seconds += time.process_time() - cpu
            self.proposal_wall_seconds += time.perf_counter() - wall
