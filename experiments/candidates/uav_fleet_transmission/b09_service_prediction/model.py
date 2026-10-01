"""B09's independent, instantaneous native radio/service model.

Only represented anonymous users compete for bandwidth. Missing users contribute
zero to the public 30-user QoS denominator. This is not a service lower bound.
No live environment, reset, transition, user identity or serving history enters
this boundary. ``raw`` is also the nominal forecast's public physics provider.
Native ``last_user_rates_mbps`` retains Mbps; access/backhaul/demand/delivery
diagnostics and returned ``delivered_bps`` use bps; native SINR uses dB.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np

from configs.config_1 import Config
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv


N_UAVS = 8
PUBLIC_USERS = 30
DEMAND_BPS = 1e6


def public_model_config(*, seed: int = 0) -> Config:
    """Public frozen S2 config, without ``make_config``'s native shape probe."""
    config = Config("S7-S2")
    config.num_envs = 1
    config.rollout_length = 3000
    config.episode_length = 3000
    config.max_steps = 3000
    config.k = 10
    config.scenario7_comparison_gate_enabled = False
    config.scenario7_run_physical_feasibility_check = False
    config.seed = int(seed)
    return config


def _increment(counters: dict, name: str) -> None:
    counters[name] = counters.get(name, 0) + 1


def _array(value, shape: tuple[int, ...], name: str) -> np.ndarray:
    result = np.array(value, dtype=np.float64, order="C", copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite with shape {shape}")
    return result


def native_output_digest(raw) -> str:
    """Exact same-source/node replay identity, not cross-platform equivalence.

    Named, length-framed dtype/shape/bytes cover geometry and the actual native
    RF, association, directed routes, access/backhaul and delivered outputs.
    Routing capacities use hex floats, with sorted UAV keys and path order intact.
    Empty queries encode explicitly absent geometry/RF rather than stale tensors.
    """
    digest = hashlib.sha256(b"B09-native-service-v1\0")

    def frame(value: bytes) -> None:
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)

    def array(name: str, value) -> None:
        data = np.ascontiguousarray(value)
        frame(json.dumps([name, data.dtype.str, list(data.shape)],
                         separators=(",", ":")).encode("utf-8"))
        frame(data.tobytes(order="C"))

    geometry = raw._relay_geometry_state
    radio_cache = raw._step_communication_cache
    for name in ("access_path_loss", "air_path_loss", "base_path_loss"):
        if geometry is None:
            frame(f"geometry/{name}:absent".encode("ascii"))
        else:
            array(f"geometry/{name}", geometry[name])
    for name in ("access_sinr", "air_sinr", "uav_to_base_sinr", "base_to_uav_sinr"):
        if radio_cache is None:
            frame(f"radio/{name}:absent".encode("ascii"))
        else:
            array(f"radio/{name}", getattr(radio_cache["radio"], name))
    for name in ("sinr_matrix", "connections", "uav_connections", "uav_bs_connections",
                 "user_serving_uav", "last_access_capacity_bps",
                 "last_backhaul_capacities_bps", "last_user_rates_mbps",
                 "last_user_demand_bps", "last_delivered_traffic_bps"):
        array(name, getattr(raw, name))
    array("user_rates_bps", raw._b09_user_rates_bps)
    array("unavailable", raw._communication_unavailable_mask())
    frame(json.dumps([[int(uav) for uav in row] for row in raw.user_serving_sets],
                     separators=(",", ":")).encode("utf-8"))
    routes = [[int(uav), [[str(kind), int(index)] for kind, index in path],
               float(capacity).hex()]
              for uav, (path, capacity) in sorted(raw.routing_paths.items())]
    frame(json.dumps(routes, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


class LawfulServiceModel:
    """Exactly one private raw native construction; no reset or step."""

    def __init__(self, counters: dict, *, seed: int = 0):
        self.counters = counters
        _increment(counters, "model_constructions")
        self.raw = UAVEnergyAwareRelayEnv(config=public_model_config(seed=seed), seed=int(seed))

    def _install(self, xyz, battery, user_xy, bs_xy) -> None:
        raw = self.raw
        q = len(user_xy)
        raw.n_users = q
        raw.uav_positions = xyz
        raw.user_positions = np.column_stack((user_xy, np.full(q, 1.5)))
        raw.ground_bs_positions = np.array([[bs_xy[0], bs_xy[1], 30.0]], dtype=np.float64)
        raw.uav_battery_ratios = battery
        raw.uav_failed = np.zeros(N_UAVS, dtype=bool)
        raw.uav_failure_timers = np.zeros(N_UAVS, dtype=int)
        raw.current_step = 0

        raw.sinr_matrix = np.zeros((N_UAVS, q), dtype=np.float64)
        raw.connections = np.zeros((N_UAVS, q), dtype=bool)
        raw.uav_connections = np.zeros((N_UAVS, N_UAVS), dtype=bool)
        raw.uav_bs_connections = np.zeros((N_UAVS, 1), dtype=bool)
        raw.user_serving_sets = [[] for _ in range(q)]
        raw.user_serving_uav = np.full(q, -1, dtype=int)
        raw.user_handover_history = [[] for _ in range(q)]
        for name in ("handover_count", "ping_pong_count", "serving_set_changes",
                     "uav_joins_count", "uav_leaves_count"):
            setattr(raw, name, 0)
        for name in ("user_serviced_status", "prev_user_serviced_status",
                     "prev_effective_user_service_status"):
            setattr(raw, name, np.zeros(q, dtype=bool))
        raw.previous_connections_snapshot = raw.connections.copy()
        raw.previous_routing_paths_snapshot = {}
        raw.previous_serving_uavs = set()
        raw.previous_bottleneck_capacities = np.zeros(N_UAVS, dtype=np.float64)
        raw.user_velocities = np.zeros((q, 3), dtype=np.float64)
        raw.user_waypoints = np.zeros((q, 2), dtype=np.float64)
        raw.user_cluster_assignments = np.zeros(q, dtype=int)
        raw.user_pause_times = np.zeros(q, dtype=np.float64)

        raw.last_user_rates_mbps = np.zeros(q, dtype=np.float64)
        raw._b09_user_rates_bps = np.zeros(q, dtype=np.float64)
        raw.last_user_demand_bps = np.full(q, DEMAND_BPS, dtype=np.float64)
        raw.last_delivered_traffic_bps = np.zeros(q, dtype=np.float64)
        raw.last_reward_demand_bps = raw.last_user_demand_bps.copy()
        raw.last_graph_potential_demand_bps = raw.last_user_demand_bps.copy()
        raw.last_access_capacity_bps = np.zeros((N_UAVS, q), dtype=np.float64)
        raw.last_backhaul_capacities_bps = np.zeros(N_UAVS, dtype=np.float64)
        raw.last_widest_backhaul_capacities_bps = np.zeros(N_UAVS, dtype=np.float64)
        raw.last_constrained_reward_metrics = {}
        raw.routing_paths = {}
        raw.hop_map = {i: float("inf") for i in range(N_UAVS)}
        raw.global_bs_cache = {}
        raw._relay_geometry_state = None
        raw._step_communication_cache = None
        raw._channel_update_cache_active = False
        raw._retained_radio_validation_active = False
        # These native caches include input or configuration state, and must not
        # survive a new query even when their poisoned signatures happen to match.
        for name in ("_routing_link_capacity_cache", "_sinr_uav_positions",
                     "_sinr_user_positions", "_sinr_unavailable",
                     "_noise_power_linear_cache", "_interference_radius_cache"):
            raw.__dict__.pop(name, None)

    def score(self, xyz, battery, user_xy, bs_xy) -> dict:
        _increment(self.counters, "model_score_calls")
        xyz = _array(xyz, (N_UAVS, 3), "xyz")
        battery = _array(battery, (N_UAVS,), "battery")
        users = np.array(user_xy, dtype=np.float64, order="C", copy=True)
        if users.ndim != 2 or users.shape[1] != 2 or not 0 <= len(users) <= PUBLIC_USERS:
            raise ValueError("user_xy must have shape (q,2), q in [0,30]")
        users = _array(users, (len(users), 2), "user_xy")
        bs = _array(bs_xy, (2,), "bs_xy")
        self._install(xyz, battery, users, bs)
        raw = self.raw
        if len(users):
            _increment(self.counters, "model_rf_calls")
            raw._update_channel_state()
            raw._update_uav_connections()
            raw._compute_routing_paths()
            rates, access, backhaul = raw._calculate_end_to_end_user_rates()
            if not np.isfinite(rates).all() or np.any(rates < 0.0):
                raise FloatingPointError("native service rates must be finite and nonnegative")
            raw.last_user_rates_mbps = np.array(rates / 1e6, dtype=np.float64, copy=True)
            raw._b09_user_rates_bps = np.array(rates, dtype=np.float64, copy=True)
            raw.last_access_capacity_bps = np.array(access, dtype=np.float64, copy=True)
            raw.last_backhaul_capacities_bps = np.array(backhaul, dtype=np.float64, copy=True)
            # Native reward delivery is capped by demand, after native per-user MAX.
            raw.last_delivered_traffic_bps = np.minimum(rates, raw.last_user_demand_bps)
        delivered = np.array(raw.last_delivered_traffic_bps, dtype=np.float64, copy=True)
        qos = float(np.sum(np.clip(delivered / DEMAND_BPS, 0.0, 1.0)) / PUBLIC_USERS)
        return {"qos": qos, "delivered_bps": delivered, "digest": native_output_digest(raw)}

    def close(self) -> None:
        self.raw.close()
