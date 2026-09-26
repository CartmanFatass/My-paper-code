"""Decode of the S7-S2 legal per-UAV observation (365 fields).

Source: ``UAVEnergyAwareRelayEnv._get_observation`` = ``UAVRoutedRelayEnv._get_observation_cached_body``
(``envs/pettingzoo/relay/routed_core.py``) followed by ``_energy_observation``
(``envs/pettingzoo/relay/energy_aware.py``).  ``belief_map.py`` and ``progressive.py`` are not in
the S7-S2 class hierarchy and have different layouts.

S7-S2 flags: ``enable_soft_handover=True``, ``predictive_handover=False`` -> 6 fields per user.
Users, peer UAVs (base block), the nearest-neighbour block and the nearest-BS self-state fields
are gated by ``observation_radius`` (1500 m, 3-D distance) and sorted by distance; unfilled slots
are zero.  BS slots hold in-radius BS first, then the global BS cache (refreshed every
``hggr_update_interval`` steps from whatever any UAV sees).  The 120-field energy suffix is not
radius gated: every UAV record and both station records are always present.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class ObservationLayout:
    area_size_m: float = 8000.0
    height_min_m: float = 50.0
    height_max_m: float = 200.0
    max_steps: int = 3000
    observation_radius_m: float = 1500.0
    n_uavs: int = 8
    user_slots: int = 30
    user_fields: int = 6
    uav_slots: int = 8
    uav_fields: int = 4
    bs_slots: int = 3
    bs_fields: int = 4
    overloaded_slots: int = 3
    overloaded_fields: int = 3
    self_state_fields: int = 5
    energy_uav_records: int = 8
    energy_uav_fields: int = 13
    energy_station_records: int = 2
    energy_station_fields: int = 8
    max_connections: int = 25
    max_hops: int = 5
    n_users: int = 30
    serving_set_size: int = 3

    @property
    def height_span_m(self) -> float:
        return self.height_max_m - self.height_min_m

    # Offsets ---------------------------------------------------------------------------
    @property
    def own(self) -> slice:
        return slice(0, 3)

    @property
    def nearest_uav(self) -> slice:
        return slice(3, 6)

    @property
    def self_state(self) -> slice:
        return slice(6, 6 + self.self_state_fields)

    @property
    def users(self) -> slice:
        start = self.self_state.stop
        return slice(start, start + self.user_slots * self.user_fields)

    @property
    def uavs(self) -> slice:
        start = self.users.stop
        return slice(start, start + self.uav_slots * self.uav_fields)

    @property
    def bs(self) -> slice:
        start = self.uavs.stop
        return slice(start, start + self.bs_slots * self.bs_fields)

    @property
    def overloaded(self) -> slice:
        start = self.bs.stop
        return slice(start, start + self.overloaded_slots * self.overloaded_fields)

    @property
    def step(self) -> int:
        return self.overloaded.stop

    @property
    def energy_uavs(self) -> slice:
        start = self.step + 1
        return slice(start, start + self.energy_uav_records * self.energy_uav_fields)

    @property
    def energy_stations(self) -> slice:
        start = self.energy_uavs.stop
        return slice(start, start + self.energy_station_records * self.energy_station_fields)

    @property
    def dim(self) -> int:
        return self.energy_stations.stop

    def offsets(self) -> dict[str, list[int]]:
        return {
            name: [getattr(self, name).start, getattr(self, name).stop]
            for name in ("own", "nearest_uav", "self_state", "users", "uavs", "bs",
                         "overloaded", "energy_uavs", "energy_stations")
        } | {"step": [self.step, self.step + 1], "dim": [0, self.dim]}

    def record(self) -> dict:
        return {"parameters": asdict(self), "offsets": self.offsets(),
                "fields": FIELD_NAMES}


FIELD_NAMES = {
    "own": ["x/area", "y/area", "(z-hmin)/hspan"],
    "nearest_uav": ["dist/area", "rel_x/area", "rel_y/area"],
    "self_state": ["connected_users/max_connections", "has_backhaul", "hops/max_hops",
                   "nearest_bs_rel_x/area", "nearest_bs_rel_y/area"],
    "users": ["rel_x/area", "rel_y/area", "clip((sinr_db+10)/50,0,1)", "connected_to_self",
              "serviced_by_any", "serving_set_len/serving_set_size"],
    "uavs": ["rel_x/area", "rel_y/area", "(rel_z-hmin)/hspan", "clip((sinr_db+10)/50,0,1)"],
    "bs": ["rel_x/area", "rel_y/area", "rel_z/hmax", "visibility_flag"],
    "overloaded": ["rel_x/area", "rel_y/area", "load/max_connections"],
    "step": ["current_step/max_steps"],
    "energy_uavs": ["rel_x/area", "rel_y/area", "rel_z/hspan", "battery_ratio", "charging",
                    "available", "returning(limp_home or dock_request)", "load=connections/n_users",
                    "dock_request", "target_station/(n_stations-1) or -1",
                    "charging_wait_steps/max_steps", "return_threshold_ratio",
                    "return_energy_margin"],
    "energy_stations": ["rel_x/area", "rel_y/area", "rel_z/hspan", "dist3d/map_diag3d",
                        "capacity_ratio", "available_ratio", "queue_len/n_uavs", "valid"],
}

S7S2_LAYOUT = ObservationLayout()

# Energy-suffix UAV record field indices.
E_BATTERY, E_CHARGING, E_AVAILABLE, E_RETURNING, E_LOAD = 3, 4, 5, 6, 7
E_DOCK, E_TARGET, E_WAITING, E_THRESHOLD, E_MARGIN = 8, 9, 10, 11, 12


def layout_from_env(raw_env) -> ObservationLayout:
    """Derive the layout from a live raw environment's actual flags and sizes."""

    user_fields = 7 if raw_env.predictive_handover else (6 if raw_env.enable_soft_handover else 5)
    layout = ObservationLayout(
        area_size_m=float(raw_env.area_size),
        height_min_m=float(raw_env.height_range[0]),
        height_max_m=float(raw_env.height_range[1]),
        max_steps=int(raw_env.max_steps),
        observation_radius_m=float(raw_env.observation_radius),
        n_uavs=int(raw_env.n_uavs),
        user_slots=int(raw_env.max_observed_users),
        user_fields=user_fields,
        uav_slots=int(raw_env.max_observed_uavs),
        bs_slots=int(raw_env.max_observed_bs),
        overloaded_slots=int(raw_env.max_observed_overloaded_uavs),
        energy_uav_records=int(raw_env.max_energy_observed_uavs),
        energy_uav_fields=int(raw_env.energy_uav_obs_dim),
        energy_station_records=int(raw_env.max_energy_charging_stations),
        energy_station_fields=int(raw_env.energy_station_obs_dim),
        max_connections=int(raw_env.max_connections),
        max_hops=int(raw_env.max_hops),
        n_users=int(raw_env.n_users),
        serving_set_size=int(raw_env.serving_set_size),
    )
    if layout.dim != int(raw_env.obs_dim):
        raise ValueError(f"derived layout dim {layout.dim} != env obs_dim {raw_env.obs_dim}")
    return layout


def _check(obs: np.ndarray, layout: ObservationLayout) -> np.ndarray:
    obs = np.asarray(obs)
    if obs.ndim != 2 or obs.shape[1] != layout.dim:
        raise ValueError(f"observations must have shape (n, {layout.dim}), got {obs.shape}")
    return obs


def own_positions(obs, layout: ObservationLayout = S7S2_LAYOUT) -> np.ndarray:
    """Absolute own xyz in metres, (n, 3)."""
    obs = _check(obs, layout).astype(np.float64)
    own = obs[:, layout.own]
    return np.stack((own[:, 0] * layout.area_size_m, own[:, 1] * layout.area_size_m,
                     own[:, 2] * layout.height_span_m + layout.height_min_m), axis=1)


def user_records(obs, layout: ObservationLayout = S7S2_LAYOUT) -> dict[str, np.ndarray]:
    """Per-UAV observed-user slots; ``present`` marks filled (non-zero) records."""
    obs = _check(obs, layout)
    records = obs[:, layout.users].reshape(len(obs), layout.user_slots, layout.user_fields)
    records64 = records.astype(np.float64)
    own = own_positions(obs, layout)
    xy = own[:, None, :2] + records64[:, :, :2] * layout.area_size_m
    result = {
        "present": np.any(records != 0.0, axis=2),
        "xy_m": xy,
        "sinr_norm": records[:, :, 2],
        "connected_to_self": records[:, :, 3],
        "serviced_by_any": records[:, :, 4],
    }
    if layout.user_fields >= 6:
        result["serving_set_ratio"] = records[:, :, 5]
    return result


def peer_uav_records(obs, layout: ObservationLayout = S7S2_LAYOUT) -> dict[str, np.ndarray]:
    """Radius-gated base-block peer slots (no identity); z field kept as encoded."""
    obs = _check(obs, layout)
    records = obs[:, layout.uavs].reshape(len(obs), layout.uav_slots, layout.uav_fields)
    own = own_positions(obs, layout)
    return {
        "present": np.any(records != 0.0, axis=2),
        "xy_m": own[:, None, :2] + records[:, :, :2].astype(np.float64) * layout.area_size_m,
        "z_field": records[:, :, 2],
        "sinr_norm": records[:, :, 3],
    }


def bs_records(obs, layout: ObservationLayout = S7S2_LAYOUT) -> dict[str, np.ndarray]:
    """BS slots; present = visibility flag 1 (both in-radius and cached slots)."""
    obs = _check(obs, layout)
    records = obs[:, layout.bs].reshape(len(obs), layout.bs_slots, layout.bs_fields).astype(np.float64)
    own = own_positions(obs, layout)
    xyz = np.empty(records.shape[:2] + (3,), dtype=np.float64)
    xyz[:, :, :2] = own[:, None, :2] + records[:, :, :2] * layout.area_size_m
    xyz[:, :, 2] = own[:, None, 2] + records[:, :, 2] * layout.height_max_m
    return {"present": records[:, :, 3] == 1.0, "xyz_m": xyz}


def energy_uav_records(obs, layout: ObservationLayout = S7S2_LAYOUT) -> np.ndarray:
    """(n_observers, n_uavs, 13) raw energy UAV records."""
    obs = _check(obs, layout)
    return obs[:, layout.energy_uavs].reshape(
        len(obs), layout.energy_uav_records, layout.energy_uav_fields)


def energy_uav_positions(obs, layout: ObservationLayout = S7S2_LAYOUT) -> np.ndarray:
    """Absolute xyz of every UAV as seen from each observer (not radius gated)."""
    records = energy_uav_records(obs, layout).astype(np.float64)
    own = own_positions(obs, layout)
    scale = np.asarray((layout.area_size_m, layout.area_size_m, layout.height_span_m))
    return own[:, None, :] + records[:, :, :3] * scale


def station_records(obs, layout: ObservationLayout = S7S2_LAYOUT) -> dict[str, np.ndarray]:
    obs = _check(obs, layout)
    records = obs[:, layout.energy_stations].reshape(
        len(obs), layout.energy_station_records, layout.energy_station_fields)
    own = own_positions(obs, layout)
    scale = np.asarray((layout.area_size_m, layout.area_size_m, layout.height_span_m))
    return {
        "xyz_m": own[:, None, :] + records[:, :, :3].astype(np.float64) * scale,
        "distance_norm": records[:, :, 3],
        "capacity_ratio": records[:, :, 4],
        "available_ratio": records[:, :, 5],
        "queue_ratio": records[:, :, 6],
        "valid": records[:, :, 7] == 1.0,
    }


def own_energy(obs, layout: ObservationLayout = S7S2_LAYOUT) -> dict[str, np.ndarray]:
    """Each UAV's own energy record (row i of observer i)."""
    records = energy_uav_records(obs, layout)
    own = records[np.arange(len(records)), np.arange(len(records))]
    return {
        "battery": own[:, E_BATTERY].astype(np.float32),
        "charging": own[:, E_CHARGING] == 1.0,
        "available": own[:, E_AVAILABLE] == 1.0,
        "returning": own[:, E_RETURNING] == 1.0,
        "dock_request": own[:, E_DOCK] == 1.0,
        "waiting_steps": np.rint(own[:, E_WAITING].astype(np.float64) * layout.max_steps).astype(np.int64),
        "return_threshold": own[:, E_THRESHOLD].astype(np.float32),
        "return_margin": own[:, E_MARGIN].astype(np.float32),
    }
