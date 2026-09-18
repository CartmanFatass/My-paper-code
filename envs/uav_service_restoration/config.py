"""Strict, independent configuration for ``uav_service_restoration_v0``.

This module inherits nothing from ``configs/config_1.py`` and reads no legacy preset.
Unknown fields are rejected on load rather than ignored, so a typo cannot silently
select a default.

Unit suffixes are part of the contract: ``_m``, ``_s``, ``_hz``, ``_mbps``, ``_dbm``,
``_db``, ``_utc_ms``.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

SCHEMA_VERSION = "uav_service_restoration_v0.config.1"
ENVIRONMENT_ID = "uav_service_restoration_v0"


_HINT_CACHE: dict[Any, dict[str, Any]] = {}


class ConfigError(ValueError):
    """A configuration document is malformed, incomplete or contains unknown fields."""


# --------------------------------------------------------------------------------------
# Leaf sections
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RadioModelConfig:
    """Parameters of one link class's log-distance link model.

    ``PL(d) = reference_loss_db + 10 * path_loss_exponent * log10(max(d, d0) / d0)
              + extra_loss_db``

    ``SNR(d) [dB] = tx_power_dbm + antenna_gain_db - PL(d) - noise_power_dbm``

    ``C = spectral_efficiency * bandwidth_hz * log2(1 + SNR)``, reported in Mbps.

    ``antenna_gain_db`` is the *combined* transmit-plus-receive gain of the link, kept as
    its own term so a directional backhaul antenna is visible in the budget instead of
    being hidden inside an inflated transmit power.  ``spectral_efficiency`` is an assumed
    implementation-loss factor.  Both are engineering assumptions unless the preset
    records a calibration.
    """

    frequency_hz: float
    bandwidth_hz: float
    tx_power_dbm: float
    antenna_gain_db: float = 0.0
    noise_density_dbm_per_hz: float = -174.0
    noise_figure_db: float = 7.0
    reference_distance_m: float = 1.0
    reference_loss_db: float = 60.0
    path_loss_exponent: float = 2.6
    extra_loss_db: float = 0.0
    spectral_efficiency: float = 0.75
    min_snr_db: float = 0.0
    max_range_m: float = 5000.0
    calibration_status: str = "engineering_assumption"

    def validate(self, where: str) -> None:
        _require_positive(self.frequency_hz, f"{where}.frequency_hz")
        _require_positive(self.bandwidth_hz, f"{where}.bandwidth_hz")
        _require_positive(self.reference_distance_m, f"{where}.reference_distance_m")
        _require_positive(self.max_range_m, f"{where}.max_range_m")
        if not 0.0 < self.spectral_efficiency <= 1.0:
            raise ConfigError(f"{where}.spectral_efficiency must be in (0, 1]")
        if self.path_loss_exponent <= 0.0:
            raise ConfigError(f"{where}.path_loss_exponent must be positive")
        if self.calibration_status not in ("engineering_assumption", "empirically_calibrated"):
            raise ConfigError(
                f"{where}.calibration_status must be 'engineering_assumption' or "
                "'empirically_calibrated'"
            )


@dataclass(frozen=True)
class SiteConfig:
    """One terrestrial site.

    ``accepts_uav_wireless_backhaul`` defaults to False: an ordinary terrestrial site is
    *not* assumed able to accept reverse wireless backhaul from a UAV.  Setting it True
    declares that hardware capability explicitly.
    """

    site_id: str
    position_m: tuple[float, float, float]
    core_egress_capacity_mbps: float
    serves_access: bool = True
    serves_uav_backhaul: bool = True
    accepts_uav_wireless_backhaul: bool = False

    def validate(self, where: str) -> None:
        if len(self.position_m) != 3:
            raise ConfigError(f"{where}.position_m must have three components")
        _require_positive(self.core_egress_capacity_mbps, f"{where}.core_egress_capacity_mbps")


@dataclass(frozen=True)
class NetworkConfig:
    sites: tuple[SiteConfig, ...]
    radio_models: dict[str, RadioModelConfig]
    max_backhaul_hops: int = 2
    access_and_backhaul_share_band: bool = False
    allow_spatial_reuse_between_nodes: bool = True
    max_candidate_paths_per_demand: int = 24
    max_total_candidate_paths: int = 2048
    core_total_egress_mbps: float | None = None
    site_access_radius_m: float | None = None

    REQUIRED_RADIO_CLASSES = (
        "site_access",
        "uav_access",
        "site_uav_backhaul",
        "uav_uav_backhaul",
    )

    def validate(self, where: str) -> None:
        if not self.sites:
            raise ConfigError(f"{where}.sites must not be empty")
        seen: set[str] = set()
        for index, site in enumerate(self.sites):
            site.validate(f"{where}.sites[{index}]")
            if site.site_id in seen:
                raise ConfigError(f"{where}.sites has duplicate site_id {site.site_id!r}")
            seen.add(site.site_id)
        missing = [name for name in self.REQUIRED_RADIO_CLASSES if name not in self.radio_models]
        if missing:
            raise ConfigError(f"{where}.radio_models is missing classes: {missing}")
        unknown = sorted(set(self.radio_models) - set(self.REQUIRED_RADIO_CLASSES))
        if unknown:
            raise ConfigError(f"{where}.radio_models has unknown classes: {unknown}")
        for name, model in self.radio_models.items():
            model.validate(f"{where}.radio_models[{name}]")
        if self.max_backhaul_hops < 0:
            raise ConfigError(f"{where}.max_backhaul_hops must be >= 0")
        if self.max_candidate_paths_per_demand < 1:
            raise ConfigError(f"{where}.max_candidate_paths_per_demand must be >= 1")
        if self.max_total_candidate_paths < 1:
            raise ConfigError(f"{where}.max_total_candidate_paths must be >= 1")
        if self.core_total_egress_mbps is not None:
            _require_positive(self.core_total_egress_mbps, f"{where}.core_total_egress_mbps")
        if self.site_access_radius_m is not None:
            _require_positive(self.site_access_radius_m, f"{where}.site_access_radius_m")


@dataclass(frozen=True)
class SchedulerConfig:
    """Fixed network-control component shared by every control policy."""

    objective: str = "max_delivered"
    secondary_rule: str = "epsilon_resource"
    secondary_weight: float = 1e-6
    feasibility_tolerance: float = 1e-7
    max_variables: int = 20000
    max_constraints: int = 20000
    solver_method: str = "highs"

    def validate(self, where: str) -> None:
        if self.objective != "max_delivered":
            raise ConfigError(f"{where}.objective must be 'max_delivered' in v0")
        if self.secondary_rule not in ("none", "epsilon_resource"):
            raise ConfigError(f"{where}.secondary_rule must be 'none' or 'epsilon_resource'")
        if not 0.0 <= self.secondary_weight < 1e-2:
            raise ConfigError(f"{where}.secondary_weight must be in [0, 1e-2)")
        _require_positive(self.feasibility_tolerance, f"{where}.feasibility_tolerance")
        if self.max_variables < 1 or self.max_constraints < 1:
            raise ConfigError(f"{where}.max_variables/max_constraints must be >= 1")


@dataclass(frozen=True)
class EventTimingConfig:
    """Sampling ranges for one presampled event, or fixed values when the range is a point."""

    event_type: str
    site_index: int | None = None
    site_choice: tuple[int, ...] = ()
    start_s_range: tuple[float, float] = (0.0, 0.0)
    duration_s_range: tuple[float, float] | None = None
    access_capacity_scale: float = 1.0
    backhaul_capacity_scale: float = 1.0

    def validate(self, where: str) -> None:
        if self.event_type not in (
            "full_site_failure",
            "capacity_degradation",
            "wired_backhaul_outage",
        ):
            raise ConfigError(f"{where}.event_type {self.event_type!r} is not supported")
        if self.site_index is None and not self.site_choice:
            raise ConfigError(f"{where} requires site_index or a non-empty site_choice")
        if self.site_index is not None and self.site_choice:
            raise ConfigError(f"{where} must not set both site_index and site_choice")
        lo, hi = self.start_s_range
        if hi < lo or lo < 0.0:
            raise ConfigError(f"{where}.start_s_range must be an ordered non-negative range")
        if self.duration_s_range is not None:
            dlo, dhi = self.duration_s_range
            if dhi < dlo or dlo <= 0.0:
                raise ConfigError(f"{where}.duration_s_range must be an ordered positive range")
        for name in ("access_capacity_scale", "backhaul_capacity_scale"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ConfigError(f"{where}.{name} must be in [0, 1]")


@dataclass(frozen=True)
class EventsConfig:
    source_kind: str = "none"
    events: tuple[EventTimingConfig, ...] = ()

    def validate(self, where: str) -> None:
        if self.source_kind not in ("none", "explicit", "presampled"):
            raise ConfigError(f"{where}.source_kind must be 'none', 'explicit' or 'presampled'")
        if self.source_kind == "none" and self.events:
            raise ConfigError(f"{where}.source_kind 'none' must not declare events")
        if self.source_kind != "none" and not self.events:
            raise ConfigError(f"{where}.source_kind {self.source_kind!r} requires events")
        for index, event in enumerate(self.events):
            event.validate(f"{where}.events[{index}]")


@dataclass(frozen=True)
class EpisodeConfig:
    semantics: str = "continuing"
    duration_s: float = 1800.0
    decision_dt_s: float = 10.0
    physics_dt_s: float = 1.0
    quadrature: str = "midpoint"

    def validate(self, where: str) -> None:
        if self.semantics not in ("continuing", "finite_horizon"):
            raise ConfigError(f"{where}.semantics must be 'continuing' or 'finite_horizon'")
        _require_positive(self.duration_s, f"{where}.duration_s")
        _require_positive(self.decision_dt_s, f"{where}.decision_dt_s")
        _require_positive(self.physics_dt_s, f"{where}.physics_dt_s")
        if self.physics_dt_s > self.decision_dt_s + 1e-12:
            raise ConfigError(f"{where}.physics_dt_s must not exceed decision_dt_s")
        if self.quadrature not in ("midpoint", "left"):
            raise ConfigError(f"{where}.quadrature must be 'midpoint' or 'left'")
        steps = self.duration_s / self.decision_dt_s
        if abs(steps - round(steps)) > 1e-9:
            raise ConfigError(f"{where}.duration_s must be an integer multiple of decision_dt_s")


@dataclass(frozen=True)
class SyntheticFixtureConfig:
    """A fully self-contained, explicitly non-real activity trace.

    The trace is analytic and reproducible from these numbers alone, so the smoke preset
    needs no data download and no cache directory.
    """

    grid_shape: tuple[int, int] = (3, 3)
    cell_spacing_m: float = 900.0
    origin_offset_m: tuple[float, float] = (600.0, 600.0)
    interval_duration_s: float = 600.0
    n_intervals: int = 24
    start_utc_ms: int = 1_383_264_000_000  # 2013-11-01T00:00:00Z, the Milan period
    base_activity: float = 40.0
    diurnal_amplitude: float = 25.0
    hotspot_cell: tuple[int, int] = (2, 1)
    hotspot_gain: float = 3.0
    hotspot_start_interval: int = 8
    hotspot_end_interval: int = 16
    unobserved_cells: tuple[int, ...] = ()
    unobserved_intervals: tuple[int, ...] = ()

    def validate(self, where: str) -> None:
        rows, cols = self.grid_shape
        if rows < 1 or cols < 1:
            raise ConfigError(f"{where}.grid_shape must be positive")
        _require_positive(self.cell_spacing_m, f"{where}.cell_spacing_m")
        _require_positive(self.interval_duration_s, f"{where}.interval_duration_s")
        if self.n_intervals < 2:
            raise ConfigError(f"{where}.n_intervals must be >= 2")
        if self.base_activity < 0.0 or self.diurnal_amplitude < 0.0:
            raise ConfigError(f"{where} activity parameters must be non-negative")
        if self.diurnal_amplitude > self.base_activity:
            raise ConfigError(
                f"{where}.diurnal_amplitude must not exceed base_activity "
                "(activity must stay non-negative)"
            )
        r, c = self.hotspot_cell
        if not (0 <= r < rows and 0 <= c < cols):
            raise ConfigError(f"{where}.hotspot_cell is outside grid_shape")
        if not 0 <= self.hotspot_start_interval <= self.hotspot_end_interval <= self.n_intervals:
            raise ConfigError(f"{where} hotspot interval range is invalid")
        n_cells = rows * cols
        for index in self.unobserved_cells:
            if not 0 <= index < n_cells:
                raise ConfigError(f"{where}.unobserved_cells contains out-of-range index {index}")
        for index in self.unobserved_intervals:
            if not 0 <= index < self.n_intervals:
                raise ConfigError(
                    f"{where}.unobserved_intervals contains out-of-range index {index}"
                )


@dataclass(frozen=True)
class SourceConfig:
    """Which demand source, and how activity maps to a simulated demand rate.

    ``kind`` must be given explicitly.  There is no default that silently substitutes a
    fixture for a real-data configuration.
    """

    kind: str
    demand_scale_mbps: float
    dataset_root: str | None = None
    split: str = "train"
    region_id: str = "default"
    activity_field: str = "internet"
    reference_scale_override: float | None = None
    synthetic_fixture: SyntheticFixtureConfig = field(default_factory=SyntheticFixtureConfig)
    event_overlay: "EventOverlayConfig | None" = None
    max_demand_points: int = 16
    require_fully_observed_episodes: bool = True

    def validate(self, where: str) -> None:
        if self.kind not in ("synthetic_fixture", "milan_activity", "prepared_dataset"):
            raise ConfigError(
                f"{where}.kind must be 'synthetic_fixture', 'prepared_dataset' or "
                "'milan_activity'"
            )
        _require_positive(self.demand_scale_mbps, f"{where}.demand_scale_mbps")
        if self.kind in ("milan_activity", "prepared_dataset") and not self.dataset_root:
            raise ConfigError(
                f"{where}.dataset_root is required for kind {self.kind!r}; a fixture is "
                "never a fallback for a real-data configuration"
            )
        if self.kind == "synthetic_fixture" and self.dataset_root:
            raise ConfigError(
                f"{where}.dataset_root must not be set for the self-contained fixture"
            )
        if self.activity_field != "internet":
            raise ConfigError(
                f"{where}.activity_field must be 'internet' in v0; activity kinds are not summed"
            )
        if self.reference_scale_override is not None:
            _require_positive(self.reference_scale_override, f"{where}.reference_scale_override")
        if self.max_demand_points < 1:
            raise ConfigError(f"{where}.max_demand_points must be >= 1")
        self.synthetic_fixture.validate(f"{where}.synthetic_fixture")
        if self.event_overlay is not None:
            self.event_overlay.validate(f"{where}.event_overlay")


@dataclass(frozen=True)
class EventOverlayConfig:
    """A synthetic demand envelope laid over a real background.

    Recorded as ``event_source='synthetic_overlay'``.  It is a constructed load surge,
    never a real concert, match or dispersal event.
    """

    event_source: str = "synthetic_overlay"
    cell_indices: tuple[int, ...] = ()
    start_s: float = 0.0
    end_s: float = 0.0
    peak_gain: float = 1.0

    def validate(self, where: str) -> None:
        if self.event_source != "synthetic_overlay":
            raise ConfigError(f"{where}.event_source must be 'synthetic_overlay'")
        if not self.cell_indices:
            raise ConfigError(f"{where}.cell_indices must not be empty")
        if self.end_s <= self.start_s:
            raise ConfigError(f"{where} requires end_s > start_s")
        if self.peak_gain < 1.0:
            raise ConfigError(f"{where}.peak_gain must be >= 1")


@dataclass(frozen=True)
class DeploymentConfig:
    mode: str = "prepositioned"
    positions_m: tuple[tuple[float, float, float], ...] = ()
    standby_positions_m: tuple[tuple[float, float, float], ...] = ()
    alert_delay_s: float = 0.0
    launch_delay_s: float = 0.0

    def validate(self, where: str, n_uavs: int) -> None:
        if self.mode not in ("prepositioned", "reactive_launch"):
            raise ConfigError(f"{where}.mode must be 'prepositioned' or 'reactive_launch'")
        if len(self.positions_m) != n_uavs:
            raise ConfigError(f"{where}.positions_m must list exactly n_uavs={n_uavs} positions")
        for index, position in enumerate(self.positions_m):
            if len(position) != 3:
                raise ConfigError(f"{where}.positions_m[{index}] must have three components")
        if self.mode == "reactive_launch":
            if len(self.standby_positions_m) != n_uavs:
                raise ConfigError(
                    f"{where}.standby_positions_m must list exactly n_uavs={n_uavs} positions "
                    "in reactive_launch mode"
                )
            for index, position in enumerate(self.standby_positions_m):
                if len(position) != 3:
                    raise ConfigError(
                        f"{where}.standby_positions_m[{index}] must have three components"
                    )
        elif self.standby_positions_m:
            raise ConfigError(
                f"{where}.standby_positions_m is only meaningful in reactive_launch mode"
            )
        if self.alert_delay_s < 0.0 or self.launch_delay_s < 0.0:
            raise ConfigError(f"{where} delays must be non-negative")


@dataclass(frozen=True)
class DynamicsConfig:
    max_speed_mps: float = 20.0
    altitude_range_m: tuple[float, float] = (80.0, 200.0)
    bounds_margin_m: float = 0.0
    record_min_separation: bool = True
    collision_avoidance: str = "none"

    def validate(self, where: str) -> None:
        _require_positive(self.max_speed_mps, f"{where}.max_speed_mps")
        lo, hi = self.altitude_range_m
        if not 0.0 < lo <= hi:
            raise ConfigError(f"{where}.altitude_range_m must satisfy 0 < low <= high")
        if self.bounds_margin_m < 0.0:
            raise ConfigError(f"{where}.bounds_margin_m must be non-negative")
        if self.collision_avoidance != "none":
            raise ConfigError(
                f"{where}.collision_avoidance is 'none' in v0; no safe-flight guarantee "
                "is claimed"
            )


@dataclass(frozen=True)
class ObservationsConfig:
    mode: str = "central_delayed_telemetry"
    telemetry_delay_s: float = 0.0
    telemetry_ttl_s: float = 120.0
    sensing_radius_m: float = 1200.0
    include_time_of_day: bool = True
    include_episode_progress: bool = False
    position_reference_m: float = 5000.0
    demand_reference_mbps: float = 50.0
    fixed_entity_order: bool = True
    on_entity_limit_exceeded: str = "error"

    def validate(self, where: str) -> None:
        if self.mode not in ("central_delayed_telemetry", "ideal_full_current_demand"):
            raise ConfigError(
                f"{where}.mode must be 'central_delayed_telemetry' or "
                "'ideal_full_current_demand'"
            )
        if self.telemetry_delay_s < 0.0:
            raise ConfigError(f"{where}.telemetry_delay_s must be non-negative")
        _require_positive(self.telemetry_ttl_s, f"{where}.telemetry_ttl_s")
        _require_positive(self.sensing_radius_m, f"{where}.sensing_radius_m")
        _require_positive(self.position_reference_m, f"{where}.position_reference_m")
        _require_positive(self.demand_reference_mbps, f"{where}.demand_reference_mbps")
        if not self.fixed_entity_order:
            raise ConfigError(f"{where}.fixed_entity_order must be true in v0")
        if self.on_entity_limit_exceeded not in ("error", "aggregate"):
            raise ConfigError(f"{where}.on_entity_limit_exceeded must be 'error' or 'aggregate'")


@dataclass(frozen=True)
class RewardConfig:
    reference_scale_mbps: float = 50.0
    reference_dt_s: float = 10.0
    motion_weight: float = 0.0
    motion_weight_rationale: str = ""

    def validate(self, where: str) -> None:
        _require_positive(self.reference_scale_mbps, f"{where}.reference_scale_mbps")
        _require_positive(self.reference_dt_s, f"{where}.reference_dt_s")
        if self.motion_weight < 0.0:
            raise ConfigError(f"{where}.motion_weight must be non-negative")
        if self.motion_weight > 0.0 and not self.motion_weight_rationale.strip():
            raise ConfigError(
                f"{where}.motion_weight_rationale is required when motion_weight > 0"
            )


@dataclass(frozen=True)
class EvaluationConfig:
    recovery_fraction_rho: float = 0.9
    recovery_sustain_s: float = 60.0

    def validate(self, where: str) -> None:
        if not 0.0 < self.recovery_fraction_rho <= 1.0:
            raise ConfigError(f"{where}.recovery_fraction_rho must be in (0, 1]")
        if self.recovery_sustain_s < 0.0:
            raise ConfigError(f"{where}.recovery_sustain_s must be non-negative")


@dataclass(frozen=True)
class OutputConfig:
    run_root: str | None = None
    debug_privileged_dump: bool = False

    def validate(self, where: str) -> None:
        if not isinstance(self.debug_privileged_dump, bool):
            raise ConfigError(f"{where}.debug_privileged_dump must be a boolean")


@dataclass(frozen=True)
class RegionConfig:
    """The metric extent the environment operates in, in the prepared CRS."""

    min_xy_m: tuple[float, float] = (0.0, 0.0)
    max_xy_m: tuple[float, float] = (5000.0, 5000.0)

    def validate(self, where: str) -> None:
        for axis in (0, 1):
            if self.max_xy_m[axis] <= self.min_xy_m[axis]:
                raise ConfigError(f"{where} axis {axis} must satisfy max > min")


# --------------------------------------------------------------------------------------
# Top-level configuration
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EnvConfig:
    environment_id: str
    schema_version: str
    seed: int
    n_uavs: int
    preset_name: str
    source: SourceConfig
    network: NetworkConfig
    deployment: DeploymentConfig
    region: RegionConfig = field(default_factory=RegionConfig)
    episode: EpisodeConfig = field(default_factory=EpisodeConfig)
    events: EventsConfig = field(default_factory=EventsConfig)
    dynamics: DynamicsConfig = field(default_factory=DynamicsConfig)
    observations: ObservationsConfig = field(default_factory=ObservationsConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    parameter_provenance: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def validate(self) -> None:
        if self.environment_id != ENVIRONMENT_ID:
            raise ConfigError(
                f"environment_id must be {ENVIRONMENT_ID!r}; got {self.environment_id!r}"
            )
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigError(
                f"schema_version must be {SCHEMA_VERSION!r}; got {self.schema_version!r}"
            )
        if self.n_uavs < 1:
            raise ConfigError("n_uavs must be >= 1")
        if not self.preset_name:
            raise ConfigError("preset_name must be a non-empty label")
        self.region.validate("region")
        self.source.validate("source")
        self.network.validate("network")
        self.deployment.validate("deployment", self.n_uavs)
        self.episode.validate("episode")
        self.events.validate("events")
        self.dynamics.validate("dynamics")
        self.observations.validate("observations")
        self.reward.validate("reward")
        self.scheduler.validate("scheduler")
        self.evaluation.validate("evaluation")
        self.output.validate("output")

        for index, site in enumerate(self.network.sites):
            if not _inside(site.position_m[:2], self.region):
                raise ConfigError(
                    f"network.sites[{index}].position_m lies outside the configured region"
                )
        lo, hi = self.dynamics.altitude_range_m
        for index, position in enumerate(self.deployment.positions_m):
            if not _inside(position[:2], self.region):
                raise ConfigError(
                    f"deployment.positions_m[{index}] lies outside the configured region"
                )
            if not lo - 1e-9 <= position[2] <= hi + 1e-9:
                raise ConfigError(
                    f"deployment.positions_m[{index}] altitude is outside "
                    f"dynamics.altitude_range_m"
                )
        for index, position in enumerate(self.deployment.standby_positions_m):
            if not _inside(position[:2], self.region):
                raise ConfigError(
                    f"deployment.standby_positions_m[{index}] lies outside the region"
                )
            if not lo - 1e-9 <= position[2] <= hi + 1e-9:
                raise ConfigError(
                    f"deployment.standby_positions_m[{index}] altitude is outside "
                    f"dynamics.altitude_range_m"
                )
        n_sites = len(self.network.sites)
        for index, event in enumerate(self.events.events):
            indices = (
                (event.site_index,) if event.site_index is not None else event.site_choice
            )
            for site_index in indices:
                if not 0 <= int(site_index) < n_sites:
                    raise ConfigError(
                        f"events.events[{index}] references unknown site index {site_index}"
                    )
        if self.observations.mode == "ideal_full_current_demand":
            # Permitted as a separately named diagnostic condition only.
            if not self.notes.strip():
                raise ConfigError(
                    "observations.mode 'ideal_full_current_demand' is a diagnostic "
                    "condition; record why in 'notes' so it is never mixed into primary "
                    "results silently"
                )

    @property
    def n_decision_steps(self) -> int:
        return int(round(self.episode.duration_s / self.episode.decision_dt_s))

    def calibration_summary(self) -> dict[str, list[str]]:
        """Split parameters into empirically calibrated and engineering assumptions."""

        calibrated: list[str] = []
        assumed: list[str] = []
        for name, model in sorted(self.network.radio_models.items()):
            target = calibrated if model.calibration_status == "empirically_calibrated" else assumed
            target.append(f"network.radio_models[{name}]")
        for key, value in sorted(self.parameter_provenance.items()):
            target = calibrated if value == "empirically_calibrated" else assumed
            target.append(key)
        return {"empirically_calibrated": calibrated, "engineering_assumptions": assumed}


# --------------------------------------------------------------------------------------
# Strict JSON decoding
# --------------------------------------------------------------------------------------


def _require_positive(value: float, where: str) -> None:
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ConfigError(f"{where} must be a finite positive number; got {value!r}")


def _inside(xy: tuple[float, float] | Any, region: RegionConfig) -> bool:
    x, y = float(xy[0]), float(xy[1])
    return (
        region.min_xy_m[0] - 1e-9 <= x <= region.max_xy_m[0] + 1e-9
        and region.min_xy_m[1] - 1e-9 <= y <= region.max_xy_m[1] + 1e-9
    )


def _strip_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is None:
        return annotation
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    if origin is not None and len(args) == 1 and len(get_args(annotation)) == 2:
        return args[0]
    return annotation


def _coerce(annotation: Any, value: Any, where: str) -> Any:
    if value is None:
        return None
    resolved = _strip_optional(annotation)
    if is_dataclass(resolved):
        return _from_mapping(resolved, value, where)
    origin = get_origin(resolved)
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise ConfigError(f"{where} must be a list")
        args = get_args(resolved)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_coerce(args[0], item, f"{where}[{i}]") for i, item in enumerate(value))
        if len(args) != len(value):
            raise ConfigError(f"{where} must have exactly {len(args)} entries")
        return tuple(_coerce(arg, item, f"{where}[{i}]") for i, (arg, item) in enumerate(zip(args, value)))
    if origin is dict:
        if not isinstance(value, dict):
            raise ConfigError(f"{where} must be an object")
        key_type, value_type = get_args(resolved)
        del key_type
        return {
            str(key): _coerce(value_type, item, f"{where}[{key}]")
            for key, item in value.items()
        }
    if resolved is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{where} must be a boolean")
        return value
    if resolved is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{where} must be an integer")
        return int(value)
    if resolved is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{where} must be a number")
        return float(value)
    if resolved is str:
        if not isinstance(value, str):
            raise ConfigError(f"{where} must be a string")
        return value
    if resolved is Any:
        return value
    raise ConfigError(f"{where} has unsupported configuration type {annotation!r}")


def _resolved_hints(cls: Any) -> dict[str, Any]:
    """Resolve the string annotations that ``from __future__ import annotations`` leaves."""

    cached = _HINT_CACHE.get(cls)
    if cached is None:
        # No explicit globalns: the defaults resolve names against the *defining* module,
        # which is what lets this decoder serve dataclasses declared in other modules
        # (for example the preprocessing configuration).
        cached = get_type_hints(cls)
        _HINT_CACHE[cls] = cached
    return cached


def _from_mapping(cls: Any, payload: Any, where: str) -> Any:
    if not isinstance(payload, dict):
        raise ConfigError(f"{where} must be an object")
    declared = {f.name for f in fields(cls)}
    hints = _resolved_hints(cls)
    unknown = sorted(set(payload) - declared)
    if unknown:
        raise ConfigError(f"{where} contains unknown fields: {unknown}")
    kwargs: dict[str, Any] = {}
    for name in declared:
        if name not in payload:
            continue
        kwargs[name] = _coerce(hints[name], payload[name], f"{where}.{name}" if where else name)
    try:
        return cls(**kwargs)
    except TypeError as error:
        raise ConfigError(f"{where or cls.__name__}: {error}") from error


def strict_from_mapping(cls: Any, payload: dict[str, Any], where: str = "") -> Any:
    """Decode a mapping into a dataclass, rejecting unknown fields.

    Public entry point for other modules that need the same strictness (the Milan
    preprocessing configuration uses it).
    """

    return _from_mapping(cls, payload, where)


def config_from_dict(payload: dict[str, Any]) -> EnvConfig:
    """Build and validate an :class:`EnvConfig` from a plain mapping."""

    if not isinstance(payload, dict):
        raise ConfigError("configuration document must be a JSON object")
    config = _from_mapping(EnvConfig, payload, "")
    config.validate()
    return config


def load_config(path: str | Path) -> EnvConfig:
    """Load and validate a configuration document from a JSON file."""

    resolved = Path(path)
    if not resolved.is_file():
        raise ConfigError(f"configuration file not found: {resolved}")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ConfigError(f"{resolved}: invalid JSON ({error})") from error
    return config_from_dict(payload)


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {f.name: _to_jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def config_to_dict(config: EnvConfig) -> dict[str, Any]:
    """Round-trippable plain mapping of a configuration."""

    return _to_jsonable(config)
