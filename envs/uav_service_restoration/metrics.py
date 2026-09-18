"""Raw per-substep quantities and episode summaries.

Units are never mixed: ``*_mbps`` fields are rates, ``*_mbit`` fields are the time
integrals of those rates.  Both are kept, because a rate summary alone cannot answer "how
much traffic went undelivered" and a volume alone cannot answer "how bad was it at the
worst moment".

Energy is reported as unavailable rather than estimated: v0 has no battery model, so
``motion_effort`` (dimensionless) and ``flight_distance_m`` are the honest fields.

Path-change and allocation-change counts come from the **fixed scheduler**.  They measure
how often that network-control component re-routed, and are not evidence of skill
switching or of any learned behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class SubintervalRecord:
    """One physical substep's raw quantities, before any aggregation."""

    start_s: float
    duration_s: float
    offered_mbps: np.ndarray
    delivered_mbps: np.ndarray
    domain_utilization: dict[str, float]
    gateway_utilization: dict[int, float]
    link_utilization: dict[int, float]
    max_constraint_residual: float
    motion_effort: float
    distance_m: np.ndarray
    active_path_signature: tuple[int, ...]
    min_separation_m: float


@dataclass
class EpisodeAccumulator:
    """Integrates raw substep quantities over an episode."""

    n_demand_points: int
    n_uavs: int
    affected_mask: np.ndarray | None = None

    offered_mbit: np.ndarray = field(init=False)
    delivered_mbit: np.ndarray = field(init=False)
    unmet_mbit: np.ndarray = field(init=False)
    total_time_s: float = field(default=0.0, init=False)
    flight_distance_m: np.ndarray = field(init=False)
    motion_effort_integral_s: float = field(default=0.0, init=False)
    peak_unmet_mbps: float = field(default=0.0, init=False)
    max_constraint_residual: float = field(default=0.0, init=False)
    domain_peak_utilization: dict[str, float] = field(default_factory=dict, init=False)
    gateway_peak_utilization: dict[int, float] = field(default_factory=dict, init=False)
    link_peak_utilization: dict[int, float] = field(default_factory=dict, init=False)
    path_signature_changes: int = field(default=0, init=False)
    allocation_change_events: int = field(default=0, init=False)
    disconnected_time_s: np.ndarray = field(init=False)
    min_separation_m: float = field(default=float("inf"), init=False)
    _last_signature: tuple[int, ...] | None = field(default=None, init=False)
    _last_delivered: np.ndarray | None = field(default=None, init=False)
    delivered_series_mbps: list[tuple[float, float, np.ndarray]] = field(
        default_factory=list, init=False
    )
    offered_series_mbps: list[np.ndarray] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.offered_mbit = np.zeros(int(self.n_demand_points), dtype=np.float64)
        self.delivered_mbit = np.zeros(int(self.n_demand_points), dtype=np.float64)
        self.unmet_mbit = np.zeros(int(self.n_demand_points), dtype=np.float64)
        self.flight_distance_m = np.zeros(int(self.n_uavs), dtype=np.float64)
        self.disconnected_time_s = np.zeros(int(self.n_demand_points), dtype=np.float64)

    # -- accumulation -------------------------------------------------------------------

    def add(self, record: SubintervalRecord, *, allocation_tolerance: float = 1e-9) -> None:
        duration = float(record.duration_s)
        offered = np.asarray(record.offered_mbps, dtype=np.float64)
        delivered = np.asarray(record.delivered_mbps, dtype=np.float64)
        unmet = np.maximum(offered - delivered, 0.0)

        self.offered_mbit += offered * duration
        self.delivered_mbit += delivered * duration
        self.unmet_mbit += unmet * duration
        self.total_time_s += duration
        self.flight_distance_m += np.asarray(record.distance_m, dtype=np.float64)
        self.motion_effort_integral_s += float(record.motion_effort) * duration
        self.peak_unmet_mbps = max(self.peak_unmet_mbps, float(unmet.sum()))
        if np.isfinite(record.max_constraint_residual):
            self.max_constraint_residual = max(
                self.max_constraint_residual, float(record.max_constraint_residual)
            )
        for key, value in record.domain_utilization.items():
            self.domain_peak_utilization[key] = max(
                self.domain_peak_utilization.get(key, 0.0), float(value)
            )
        for key, value in record.gateway_utilization.items():
            self.gateway_peak_utilization[int(key)] = max(
                self.gateway_peak_utilization.get(int(key), 0.0), float(value)
            )
        for key, value in record.link_utilization.items():
            self.link_peak_utilization[int(key)] = max(
                self.link_peak_utilization.get(int(key), 0.0), float(value)
            )
        # A demand point with positive offered demand and no delivery is disconnected.
        self.disconnected_time_s += np.where(
            (offered > 0.0) & (delivered <= allocation_tolerance), duration, 0.0
        )
        if record.active_path_signature != self._last_signature:
            if self._last_signature is not None:
                self.path_signature_changes += 1
            self._last_signature = record.active_path_signature
        if self._last_delivered is not None and not np.allclose(
            self._last_delivered, delivered, rtol=0.0, atol=allocation_tolerance
        ):
            self.allocation_change_events += 1
        self._last_delivered = delivered.copy()
        self.min_separation_m = min(self.min_separation_m, float(record.min_separation_m))
        self.delivered_series_mbps.append((float(record.start_s), duration, delivered.copy()))
        self.offered_series_mbps.append(offered.copy())

    # -- summarisation ------------------------------------------------------------------

    def satisfaction(self, mask: np.ndarray | None = None) -> float:
        """Demand-weighted satisfaction over the selected demand points.

        Returns NaN when the selection offered no demand at all: there is no meaningful
        satisfaction ratio without demand, and a zero-demand point must not be counted as
        a perfectly served user.
        """

        offered = self.offered_mbit if mask is None else self.offered_mbit[mask]
        delivered = self.delivered_mbit if mask is None else self.delivered_mbit[mask]
        total = float(offered.sum())
        if total <= 0.0:
            return float("nan")
        return float(delivered.sum() / total)

    def service_ratio_distribution(self) -> dict[str, float]:
        """Per-point service ratios, restricted to points with positive offered volume."""

        positive = self.offered_mbit > 0.0
        if not positive.any():
            return {
                "n_points_with_demand": 0,
                "mean": float("nan"),
                "p05": float("nan"),
                "p10": float("nan"),
                "p25": float("nan"),
                "median": float("nan"),
                "min": float("nan"),
            }
        ratios = self.delivered_mbit[positive] / self.offered_mbit[positive]
        return {
            "n_points_with_demand": int(positive.sum()),
            "mean": float(np.mean(ratios)),
            "p05": float(np.quantile(ratios, 0.05)),
            "p10": float(np.quantile(ratios, 0.10)),
            "p25": float(np.quantile(ratios, 0.25)),
            "median": float(np.median(ratios)),
            "min": float(np.min(ratios)),
        }

    def summary(self) -> dict[str, Any]:
        affected = self.affected_mask
        return {
            "total_time_s": float(self.total_time_s),
            "offered_mbit_total": float(self.offered_mbit.sum()),
            "delivered_mbit_total": float(self.delivered_mbit.sum()),
            "unmet_mbit_total": float(self.unmet_mbit.sum()),
            "offered_mbit_per_point": self.offered_mbit.tolist(),
            "delivered_mbit_per_point": self.delivered_mbit.tolist(),
            "unmet_mbit_per_point": self.unmet_mbit.tolist(),
            "mean_offered_mbps": float(
                self.offered_mbit.sum() / self.total_time_s
            )
            if self.total_time_s > 0.0
            else 0.0,
            "mean_delivered_mbps": float(
                self.delivered_mbit.sum() / self.total_time_s
            )
            if self.total_time_s > 0.0
            else 0.0,
            "peak_unmet_mbps": float(self.peak_unmet_mbps),
            "satisfaction_all": self.satisfaction(),
            "satisfaction_affected": (
                self.satisfaction(affected) if affected is not None else float("nan")
            ),
            "service_ratio_distribution": self.service_ratio_distribution(),
            "disconnected_time_s_per_point": self.disconnected_time_s.tolist(),
            "disconnected_time_s_max": float(self.disconnected_time_s.max())
            if self.disconnected_time_s.size
            else 0.0,
            "flight_distance_m_per_uav": self.flight_distance_m.tolist(),
            "flight_distance_m_total": float(self.flight_distance_m.sum()),
            "motion_effort_integral_s": float(self.motion_effort_integral_s),
            "energy_joules": None,
            "energy_status": "unavailable: v0 implements no battery or hover-power model",
            "domain_peak_utilization": dict(sorted(self.domain_peak_utilization.items())),
            "gateway_peak_utilization": {
                int(key): float(value)
                for key, value in sorted(self.gateway_peak_utilization.items())
            },
            "link_peak_utilization": {
                int(key): float(value)
                for key, value in sorted(self.link_peak_utilization.items())
            },
            "max_constraint_residual": float(self.max_constraint_residual),
            "scheduler_path_signature_changes": int(self.path_signature_changes),
            "scheduler_allocation_change_events": int(self.allocation_change_events),
            "scheduler_change_attribution": (
                "computed by the fixed path-flow scheduler; not evidence of skill "
                "switching or learned routing"
            ),
            "min_uav_separation_m": (
                None if not np.isfinite(self.min_separation_m) else float(self.min_separation_m)
            ),
            "collision_avoidance": "not implemented; no safe-flight guarantee is claimed",
        }

    def delivered_rate_at(self, time_s: float) -> np.ndarray:
        """Delivered rate during the substep containing ``time_s``."""

        target = float(time_s)
        for start, duration, delivered in self.delivered_series_mbps:
            if start <= target < start + duration:
                return delivered
        return np.zeros(int(self.n_demand_points), dtype=np.float64)
