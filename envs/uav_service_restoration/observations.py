"""Permitted telemetry, masks, ages and flattening.

Information condition (``central_delayed_telemetry``, the v0 default)
--------------------------------------------------------------------
A reliable, low-bandwidth management/control channel is assumed.  It aggregates UAV poses,
terrestrial site capability reports and service measurements **from completed control
intervals** and redistributes them after ``telemetry_delay_s``.  This channel carries no
traffic: it grants no backhaul capacity, and it does not establish decentralised execution
under bandwidth limits.

Stated assumptions, so that nothing here is mistaken for a measurement:

* Site capability reports are delivered over the management plane and are therefore
  observed every interval (after the telemetry delay).  Operators do know when a site
  drops.
* Demand is observed only where it is **sensed or registered**: a demand point served by a
  live site's access radio, or lying within ``sensing_radius_m`` of a UAV.  Elsewhere it
  is *unknown* - mask zero - and never a numeric zero and never the true full-map value.
* Every observed item carries its measurement age.  Past ``telemetry_ttl_s`` the item is
  marked stale, i.e. mask zero, rather than treated as permanently current.

What is excluded by construction: future demand intervals, future events, the event
schedule, the trace cursor, the episode id, the source file, offered demand at unsensed
points, and any internal simulator state.

``ideal_full_current_demand`` is a separately named diagnostic condition that reveals the
true current offered demand everywhere.  It is never mixed into primary results; the
configuration refuses it without a recorded rationale.

Layout
------
Observation and state dimensions are fixed at construction.  Demand-point identity is a
fixed slot index that never re-sorts by distance, and padding slots are flagged
separately from true zeros.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np

from .config import EnvConfig
from .radio import capacity_mbps
from .types import SiteState, TelemetryRecord

_ROME = ZoneInfo("Europe/Rome")

#: Per-entity feature widths, documented so the layout is auditable.
SELF_FEATURES = 6
PEER_FEATURES = 5
SITE_FEATURES = 8
DEMAND_FEATURES = 7


def capacity_feature(capacity_mbps_value: np.ndarray | float) -> np.ndarray:
    """Monotone bounded encoding of a link capacity: ``log1p(C_mbps) / 10``."""

    return np.log1p(np.maximum(np.asarray(capacity_mbps_value, dtype=np.float64), 0.0)) / 10.0


class EntityLimitExceeded(ValueError):
    """More demand points than the configured limit, and no aggregation was permitted."""


@dataclass
class DemandPointLayout:
    """Fixed mapping from source cells to demand-point slots.

    When the source has more cells than ``max_demand_points`` and aggregation is
    permitted, cells are grouped by their fixed ordering into contiguous near-equal
    groups.  Group demand is the **sum** of member demand, so total offered demand is
    conserved exactly and the hardest-to-serve cells are never dropped.
    """

    n_slots: int
    n_cells: int
    positions_m: np.ndarray
    group_of_cell: np.ndarray
    aggregated: bool
    group_sizes: np.ndarray

    @classmethod
    def build(
        cls,
        cell_positions_m: np.ndarray,
        max_demand_points: int,
        on_limit: str,
    ) -> "DemandPointLayout":
        positions = np.asarray(cell_positions_m, dtype=np.float64).reshape(-1, 2)
        n_cells = int(positions.shape[0])
        limit = int(max_demand_points)
        if n_cells == 0:
            raise ValueError("the demand source exposes no cells")
        if n_cells <= limit:
            return cls(
                n_slots=n_cells,
                n_cells=n_cells,
                positions_m=positions.copy(),
                group_of_cell=np.arange(n_cells, dtype=np.int64),
                aggregated=False,
                group_sizes=np.ones(n_cells, dtype=np.int64),
            )
        if on_limit == "error":
            raise EntityLimitExceeded(
                f"the demand source has {n_cells} cells but "
                f"source.max_demand_points is {limit}. Raise the limit or set "
                "observations.on_entity_limit_exceeded='aggregate'; demand points are "
                "never dropped."
            )
        if on_limit != "aggregate":
            raise ValueError(f"unsupported on_entity_limit_exceeded {on_limit!r}")
        # Contiguous grouping over the source's own fixed cell ordering.
        boundaries = np.linspace(0, n_cells, limit + 1).astype(np.int64)
        group_of_cell = np.zeros(n_cells, dtype=np.int64)
        slot_positions = np.zeros((limit, 2), dtype=np.float64)
        group_sizes = np.zeros(limit, dtype=np.int64)
        for slot in range(limit):
            start, stop = int(boundaries[slot]), int(boundaries[slot + 1])
            if stop <= start:
                raise EntityLimitExceeded(
                    "aggregation produced an empty demand slot; reduce "
                    "source.max_demand_points"
                )
            group_of_cell[start:stop] = slot
            slot_positions[slot] = positions[start:stop].mean(axis=0)
            group_sizes[slot] = stop - start
        return cls(
            n_slots=limit,
            n_cells=n_cells,
            positions_m=slot_positions,
            group_of_cell=group_of_cell,
            aggregated=True,
            group_sizes=group_sizes,
        )

    def aggregate_demand(self, cell_demand: np.ndarray) -> np.ndarray:
        """Sum cell demand into slots; total demand is conserved exactly."""

        values = np.asarray(cell_demand, dtype=np.float64).reshape(-1)
        if values.shape[0] != self.n_cells:
            raise ValueError("cell_demand length does not match the source cell count")
        if not self.aggregated:
            return values.copy()
        out = np.zeros(self.n_slots, dtype=np.float64)
        np.add.at(out, self.group_of_cell, values)
        return out

    def aggregate_mask(self, cell_mask: np.ndarray) -> np.ndarray:
        """A slot is observed only when every contributing cell is observed."""

        mask = np.asarray(cell_mask, dtype=bool).reshape(-1)
        if mask.shape[0] != self.n_cells:
            raise ValueError("cell_mask length does not match the source cell count")
        if not self.aggregated:
            return mask.copy()
        out = np.ones(self.n_slots, dtype=bool)
        np.logical_and.at(out, self.group_of_cell, mask)
        return out


@dataclass
class TelemetryStore:
    """Per-entity latest released report with its own measurement time."""

    n_uavs: int
    n_sites: int
    n_demand_slots: int

    uav_positions_m: np.ndarray = field(init=False)
    uav_velocities_mps: np.ndarray = field(init=False)
    uav_time_s: np.ndarray = field(init=False)
    site_vectors: np.ndarray = field(init=False)
    site_time_s: np.ndarray = field(init=False)
    demand_offered_mbps: np.ndarray = field(init=False)
    demand_delivered_mbps: np.ndarray = field(init=False)
    demand_time_s: np.ndarray = field(init=False)
    pending: list[TelemetryRecord] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.uav_positions_m = np.zeros((self.n_uavs, 3), dtype=np.float64)
        self.uav_velocities_mps = np.zeros((self.n_uavs, 3), dtype=np.float64)
        self.uav_time_s = np.full(self.n_uavs, np.nan, dtype=np.float64)
        self.site_vectors = np.zeros((self.n_sites, 4), dtype=np.float64)
        self.site_time_s = np.full(self.n_sites, np.nan, dtype=np.float64)
        self.demand_offered_mbps = np.zeros(self.n_demand_slots, dtype=np.float64)
        self.demand_delivered_mbps = np.zeros(self.n_demand_slots, dtype=np.float64)
        self.demand_time_s = np.full(self.n_demand_slots, np.nan, dtype=np.float64)
        self.pending = []

    def submit(self, record: TelemetryRecord) -> None:
        """Queue a completed interval's report; it becomes visible at its release time."""

        self.pending.append(record)

    def release_due(self, now_s: float) -> int:
        """Ingest every queued report whose release time has arrived."""

        released = 0
        remaining: list[TelemetryRecord] = []
        for record in self.pending:
            if float(record.release_time_s) <= float(now_s) + 1e-12:
                self._ingest(record)
                released += 1
            else:
                remaining.append(record)
        self.pending = remaining
        return released

    def _ingest(self, record: TelemetryRecord) -> None:
        stamp = float(record.interval_end_s)
        self.uav_positions_m[:] = np.asarray(record.uav_positions_m, dtype=np.float64)
        self.uav_velocities_mps[:] = np.asarray(record.uav_velocities_mps, dtype=np.float64)
        self.uav_time_s[:] = stamp
        site_observed = np.asarray(record.site_state_observed, dtype=bool)
        vectors = np.asarray(record.site_state_vectors, dtype=np.float64)
        self.site_vectors[site_observed] = vectors[site_observed]
        self.site_time_s[site_observed] = stamp
        demand_observed = np.asarray(record.demand_observed, dtype=bool)
        self.demand_offered_mbps[demand_observed] = np.asarray(
            record.demand_offered_mbps, dtype=np.float64
        )[demand_observed]
        self.demand_delivered_mbps[demand_observed] = np.asarray(
            record.demand_delivered_mbps, dtype=np.float64
        )[demand_observed]
        self.demand_time_s[demand_observed] = stamp

    def snapshot(self) -> dict[str, np.ndarray]:
        return {
            "uav_positions_m": self.uav_positions_m.copy(),
            "uav_velocities_mps": self.uav_velocities_mps.copy(),
            "uav_time_s": self.uav_time_s.copy(),
            "site_vectors": self.site_vectors.copy(),
            "site_time_s": self.site_time_s.copy(),
            "demand_offered_mbps": self.demand_offered_mbps.copy(),
            "demand_delivered_mbps": self.demand_delivered_mbps.copy(),
            "demand_time_s": self.demand_time_s.copy(),
            "pending": [record for record in self.pending],
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.uav_positions_m = np.array(snapshot["uav_positions_m"], dtype=np.float64)
        self.uav_velocities_mps = np.array(snapshot["uav_velocities_mps"], dtype=np.float64)
        self.uav_time_s = np.array(snapshot["uav_time_s"], dtype=np.float64)
        self.site_vectors = np.array(snapshot["site_vectors"], dtype=np.float64)
        self.site_time_s = np.array(snapshot["site_time_s"], dtype=np.float64)
        self.demand_offered_mbps = np.array(snapshot["demand_offered_mbps"], dtype=np.float64)
        self.demand_delivered_mbps = np.array(
            snapshot["demand_delivered_mbps"], dtype=np.float64
        )
        self.demand_time_s = np.array(snapshot["demand_time_s"], dtype=np.float64)
        self.pending = list(snapshot["pending"])


class ObservationBuilder:
    """Builds float32 observations and the centralized state vector."""

    def __init__(
        self,
        config: EnvConfig,
        layout: DemandPointLayout,
    ) -> None:
        self._config = config
        self._layout = layout
        self._n_uavs = int(config.n_uavs)
        self._n_sites = len(config.network.sites)
        self._n_slots = int(layout.n_slots)
        self._max_slots = max(int(config.source.max_demand_points), self._n_slots)
        self._site_positions = np.asarray(
            [site.position_m for site in config.network.sites], dtype=np.float64
        )
        self._time_features = (1 if config.observations.include_time_of_day else 0) * 2 + (
            1 if config.observations.include_episode_progress else 0
        )
        self._obs_dim = (
            SELF_FEATURES
            + PEER_FEATURES * (self._n_uavs - 1)
            + SITE_FEATURES * self._n_sites
            + DEMAND_FEATURES * self._max_slots
            + self._n_sites
            + (self._n_uavs - 1)
            + self._time_features
            + 2
        )
        self._state_dim = (
            6 * self._n_uavs
            + self._n_uavs  # per-UAV pose age/validity flag
            + SITE_FEATURES * self._n_sites
            + DEMAND_FEATURES * self._max_slots
            + self._time_features
            + 2
        )

    # -- dimensions ---------------------------------------------------------------------

    @property
    def obs_dim(self) -> int:
        return int(self._obs_dim)

    @property
    def state_dim(self) -> int:
        return int(self._state_dim)

    @property
    def n_demand_slots(self) -> int:
        return int(self._n_slots)

    @property
    def max_demand_slots(self) -> int:
        return int(self._max_slots)

    def schema(self) -> dict[str, Any]:
        """Human-readable field layout, for the delivery report and the README."""

        return {
            "obs_dim": self.obs_dim,
            "state_dim": self.state_dim,
            "mode": self._config.observations.mode,
            "obs_blocks": [
                {"name": "self_position_xyz_normalised", "width": 3},
                {"name": "self_velocity_xyz_over_max_speed", "width": 3},
                {
                    "name": "peer_uav[rel_xyz, age, mask]",
                    "width": PEER_FEATURES * (self._n_uavs - 1),
                    "entities": self._n_uavs - 1,
                },
                {
                    "name": (
                        "site[rel_xy, radio_up, core_link_up, access_scale, "
                        "backhaul_scale, age, mask]"
                    ),
                    "width": SITE_FEATURES * self._n_sites,
                    "entities": self._n_sites,
                },
                {
                    "name": (
                        "demand_slot[rel_xy, offered_est, unmet_est, age, observed_mask, "
                        "slot_valid_mask]"
                    ),
                    "width": DEMAND_FEATURES * self._max_slots,
                    "entities": self._max_slots,
                },
                {"name": "backhaul_capacity_feature_to_sites", "width": self._n_sites},
                {"name": "backhaul_capacity_feature_to_peers", "width": self._n_uavs - 1},
                {"name": "time_features", "width": self._time_features},
                {"name": "alert_raised, held_at_standby", "width": 2},
            ],
            "state_blocks": [
                {"name": "uav_positions_normalised", "width": 3 * self._n_uavs},
                {"name": "uav_velocities_over_max_speed", "width": 3 * self._n_uavs},
                {"name": "uav_pose_mask", "width": self._n_uavs},
                {
                    "name": "site[rel_to_region_origin_xy, capability(4), age, mask]",
                    "width": SITE_FEATURES * self._n_sites,
                },
                {
                    "name": (
                        "demand_slot[xy, offered_est, unmet_est, age, observed_mask, "
                        "slot_valid_mask]"
                    ),
                    "width": DEMAND_FEATURES * self._max_slots,
                },
                {"name": "time_features", "width": self._time_features},
                {"name": "alert_raised, held_at_standby", "width": 2},
            ],
            "excluded_by_construction": [
                "future demand intervals",
                "future or scheduled events",
                "episode_id / source_file / trace_cursor",
                "offered demand at unsensed demand points",
                "internal simulator state and privileged diagnostics",
            ],
        }

    # -- helpers ------------------------------------------------------------------------

    def _normalise_position(self, positions_m: np.ndarray) -> np.ndarray:
        observations = self._config.observations
        low_z, high_z = self._config.dynamics.altitude_range_m
        out = np.asarray(positions_m, dtype=np.float64).reshape(-1, 3).copy()
        out[:, 0] /= float(observations.position_reference_m)
        out[:, 1] /= float(observations.position_reference_m)
        span = max(float(high_z) - float(low_z), 1e-9)
        out[:, 2] = (out[:, 2] - float(low_z)) / span
        return out

    def _age_and_mask(self, observed_time_s: np.ndarray, now_s: float) -> tuple[np.ndarray, np.ndarray]:
        ttl = float(self._config.observations.telemetry_ttl_s)
        stamps = np.asarray(observed_time_s, dtype=np.float64)
        age = float(now_s) - stamps
        valid = np.isfinite(stamps) & (age >= -1e-9) & (age <= ttl + 1e-9)
        normalised_age = np.where(valid, np.clip(age, 0.0, ttl) / ttl, 1.0)
        return normalised_age, valid

    def _time_feature_vector(self, timestamp_utc_ms: int, progress: float) -> np.ndarray:
        values: list[float] = []
        observations = self._config.observations
        if observations.include_time_of_day:
            moment = datetime.fromtimestamp(int(timestamp_utc_ms) / 1000.0, tz=timezone.utc)
            local = moment.astimezone(_ROME)
            seconds = local.hour * 3600 + local.minute * 60 + local.second
            angle = 2.0 * np.pi * seconds / 86400.0
            values.extend([float(np.sin(angle)), float(np.cos(angle))])
        if observations.include_episode_progress:
            values.append(float(progress))
        return np.asarray(values, dtype=np.float64)

    def _demand_block(
        self,
        reference_xy_m: np.ndarray | None,
        offered_est: np.ndarray,
        delivered_est: np.ndarray,
        age: np.ndarray,
        valid: np.ndarray,
    ) -> np.ndarray:
        observations = self._config.observations
        block = np.zeros((self._max_slots, DEMAND_FEATURES), dtype=np.float64)
        positions = self._layout.positions_m
        scale = float(observations.position_reference_m)
        demand_ref = float(observations.demand_reference_mbps)
        for slot in range(self._n_slots):
            if reference_xy_m is None:
                dx = positions[slot, 0] / scale
                dy = positions[slot, 1] / scale
            else:
                dx = (positions[slot, 0] - float(reference_xy_m[0])) / scale
                dy = (positions[slot, 1] - float(reference_xy_m[1])) / scale
            observed = bool(valid[slot])
            offered = float(offered_est[slot]) if observed else 0.0
            unmet = max(offered - float(delivered_est[slot]), 0.0) if observed else 0.0
            block[slot] = (
                dx,
                dy,
                offered / demand_ref,
                unmet / demand_ref,
                float(age[slot]),
                1.0 if observed else 0.0,
                1.0,  # slot_valid_mask: this slot maps to a real demand point
            )
        # Padding slots keep slot_valid_mask == 0 so padding is never read as a true zero.
        return block.reshape(-1)

    def _site_block(self, reference_xy_m: np.ndarray | None, store: TelemetryStore, now_s: float) -> np.ndarray:
        observations = self._config.observations
        scale = float(observations.position_reference_m)
        age, valid = self._age_and_mask(store.site_time_s, now_s)
        block = np.zeros((self._n_sites, SITE_FEATURES), dtype=np.float64)
        for index in range(self._n_sites):
            if reference_xy_m is None:
                dx = self._site_positions[index, 0] / scale
                dy = self._site_positions[index, 1] / scale
            else:
                dx = (self._site_positions[index, 0] - float(reference_xy_m[0])) / scale
                dy = (self._site_positions[index, 1] - float(reference_xy_m[1])) / scale
            vector = store.site_vectors[index] if valid[index] else np.zeros(4, dtype=np.float64)
            block[index] = (
                dx,
                dy,
                float(vector[0]),
                float(vector[1]),
                float(vector[2]),
                float(vector[3]),
                float(age[index]),
                1.0 if valid[index] else 0.0,
            )
        return block.reshape(-1)

    # -- public builders -----------------------------------------------------------------

    def build_observation(
        self,
        *,
        uav_index: int,
        own_position_m: np.ndarray,
        own_velocity_mps: np.ndarray,
        store: TelemetryStore,
        now_s: float,
        timestamp_utc_ms: int,
        progress: float,
        alert_raised: bool,
        held_at_standby: bool,
        ideal_offered_mbps: np.ndarray | None = None,
    ) -> np.ndarray:
        config = self._config
        own_position = np.asarray(own_position_m, dtype=np.float64).reshape(3)
        own_velocity = np.asarray(own_velocity_mps, dtype=np.float64).reshape(3)

        parts: list[np.ndarray] = [
            self._normalise_position(own_position[None, :]).reshape(-1),
            own_velocity / float(config.dynamics.max_speed_mps),
        ]

        peer_age, peer_valid = self._age_and_mask(store.uav_time_s, now_s)
        peer_rows: list[np.ndarray] = []
        for other in range(self._n_uavs):
            if other == int(uav_index):
                continue
            if peer_valid[other]:
                relative = store.uav_positions_m[other] - own_position
                relative = relative / float(config.observations.position_reference_m)
            else:
                relative = np.zeros(3, dtype=np.float64)
            peer_rows.append(
                np.concatenate(
                    [
                        relative,
                        np.asarray([peer_age[other], 1.0 if peer_valid[other] else 0.0]),
                    ]
                )
            )
        if peer_rows:
            parts.append(np.concatenate(peer_rows))

        parts.append(self._site_block(own_position[:2], store, now_s))

        demand_age, demand_valid = self._age_and_mask(store.demand_time_s, now_s)
        if config.observations.mode == "ideal_full_current_demand":
            if ideal_offered_mbps is None:
                raise ValueError("ideal_full_current_demand requires the true offered demand")
            offered_est = np.asarray(ideal_offered_mbps, dtype=np.float64)
            delivered_est = store.demand_delivered_mbps
            demand_valid = np.ones(self._n_slots, dtype=bool)
            demand_age = np.zeros(self._n_slots, dtype=np.float64)
        else:
            offered_est = store.demand_offered_mbps
            delivered_est = store.demand_delivered_mbps
        parts.append(
            self._demand_block(own_position[:2], offered_est, delivered_est, demand_age, demand_valid)
        )

        # Reachable-link quality from the UAV's current position: own pose plus fixed
        # geography and shared peer poses, so nothing privileged enters here.
        backhaul_model = config.network.radio_models["site_uav_backhaul"]
        site_distances = np.sqrt(
            np.sum((self._site_positions - own_position[None, :]) ** 2, axis=1)
        )
        parts.append(capacity_feature(capacity_mbps(site_distances, backhaul_model)))
        peer_model = config.network.radio_models["uav_uav_backhaul"]
        peer_features: list[float] = []
        for other in range(self._n_uavs):
            if other == int(uav_index):
                continue
            if peer_valid[other]:
                distance = float(
                    np.sqrt(np.sum((store.uav_positions_m[other] - own_position) ** 2))
                )
                peer_features.append(float(capacity_feature(capacity_mbps(distance, peer_model))))
            else:
                peer_features.append(0.0)
        if peer_features:
            parts.append(np.asarray(peer_features, dtype=np.float64))

        parts.append(self._time_feature_vector(timestamp_utc_ms, progress))
        parts.append(
            np.asarray(
                [1.0 if alert_raised else 0.0, 1.0 if held_at_standby else 0.0],
                dtype=np.float64,
            )
        )

        flat = np.concatenate([np.asarray(part, dtype=np.float64).reshape(-1) for part in parts])
        if flat.shape[0] != self._obs_dim:
            raise AssertionError(
                f"observation width {flat.shape[0]} does not match declared {self._obs_dim}"
            )
        if not np.isfinite(flat).all():
            raise AssertionError("observation contains non-finite values")
        return flat.astype(np.float32)

    def build_state(
        self,
        *,
        store: TelemetryStore,
        now_s: float,
        timestamp_utc_ms: int,
        progress: float,
        alert_raised: bool,
        held_at_standby: bool,
        ideal_offered_mbps: np.ndarray | None = None,
    ) -> np.ndarray:
        """Centralized state for a critic or a high-level actor.

        Contains only information the management plane may legitimately hold: released
        telemetry, fixed geography and wall-clock time.  No future trace, no future event,
        no hidden simulator state.
        """

        config = self._config
        peer_age, peer_valid = self._age_and_mask(store.uav_time_s, now_s)
        del peer_age
        positions = self._normalise_position(store.uav_positions_m)
        positions = np.where(peer_valid[:, None], positions, 0.0)
        velocities = store.uav_velocities_mps / float(config.dynamics.max_speed_mps)
        velocities = np.where(peer_valid[:, None], velocities, 0.0)

        demand_age, demand_valid = self._age_and_mask(store.demand_time_s, now_s)
        if config.observations.mode == "ideal_full_current_demand":
            if ideal_offered_mbps is None:
                raise ValueError("ideal_full_current_demand requires the true offered demand")
            offered_est = np.asarray(ideal_offered_mbps, dtype=np.float64)
            demand_valid = np.ones(self._n_slots, dtype=bool)
            demand_age = np.zeros(self._n_slots, dtype=np.float64)
        else:
            offered_est = store.demand_offered_mbps

        parts = [
            positions.reshape(-1),
            velocities.reshape(-1),
            peer_valid.astype(np.float64),
            self._site_block(None, store, now_s),
            self._demand_block(
                None, offered_est, store.demand_delivered_mbps, demand_age, demand_valid
            ),
            self._time_feature_vector(timestamp_utc_ms, progress),
            np.asarray(
                [1.0 if alert_raised else 0.0, 1.0 if held_at_standby else 0.0],
                dtype=np.float64,
            ),
        ]
        flat = np.concatenate([np.asarray(part, dtype=np.float64).reshape(-1) for part in parts])
        if flat.shape[0] != self._state_dim:
            raise AssertionError(
                f"state width {flat.shape[0]} does not match declared {self._state_dim}"
            )
        if not np.isfinite(flat).all():
            raise AssertionError("state contains non-finite values")
        return flat.astype(np.float32)


def sensed_demand_mask(
    demand_positions_m: np.ndarray,
    uav_positions_m: np.ndarray,
    site_positions_m: np.ndarray,
    site_states: tuple[SiteState, ...],
    sensing_radius_m: float,
    site_registration_radius_m: float,
) -> np.ndarray:
    """Which demand points are legitimately sensed or registered this interval.

    A point is known if a live site's access radio covers it (the site holds its own
    service records for those terminals) or a UAV is within ``sensing_radius_m``.
    Everything else is *unknown*: not zero, and not the true full-map value.

    ``site_registration_radius_m`` is the effective coverage radius of a site's access
    radio; the caller passes the configured access radius or, when unbounded, the access
    model's ``max_range_m``.
    """

    demands = np.asarray(demand_positions_m, dtype=np.float64).reshape(-1, 3)
    mask = np.zeros(demands.shape[0], dtype=bool)
    sites = np.asarray(site_positions_m, dtype=np.float64).reshape(-1, 3)
    for index, state in enumerate(site_states):
        if not state.radio_up:
            continue
        distances = np.sqrt(np.sum((demands - sites[index][None, :]) ** 2, axis=1))
        mask |= distances <= float(site_registration_radius_m)
    uavs = np.asarray(uav_positions_m, dtype=np.float64).reshape(-1, 3)
    if uavs.shape[0]:
        distances = np.sqrt(
            np.sum((demands[:, None, :] - uavs[None, :, :]) ** 2, axis=-1)
        )
        mask |= (distances <= float(sensing_radius_m)).any(axis=1)
    return mask
