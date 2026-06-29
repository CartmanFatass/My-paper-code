"""Topology-potential cooperative credit shaping for HA-CTSE.

This module is separate from the topology role discriminator.  It does not
learn pseudo labels; it computes a bounded network-service potential from the
environment's existing reward_info stream and turns segment-level potential
change into an optional shaping signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


TOPOLOGY_POTENTIAL_FIELDS = (
    "topology_potential_available_frac",
    "topology_potential_active",
    "topology_potential_warmup_active",
    "topology_potential_raw_mean",
    "topology_potential_raw_positive_frac",
    "topology_potential_unclipped_mean",
    "topology_potential_reward_mean",
    "topology_potential_high_mean",
    "topology_potential_low_mean",
    "topology_potential_clip_frac",
    "topology_potential_phi_start_mean",
    "topology_potential_phi_end_mean",
    "topology_potential_delta_mean",
    "topology_potential_discount_mean",
    "topology_potential_backhaul_up_start_mean",
    "topology_potential_backhaul_up_end_mean",
    "topology_potential_full_disconnect_start_mean",
    "topology_potential_full_disconnect_end_mean",
)


def empty_topology_potential_metrics() -> dict[str, float]:
    return {field: 0.0 for field in TOPOLOGY_POTENTIAL_FIELDS}


def _safe_mean(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else 0.0


def _scalar(info: dict, aliases: tuple[str, ...]) -> tuple[float, bool]:
    for key in aliases:
        if key not in info:
            continue
        try:
            arr = np.asarray(info.get(key), dtype=np.float64)
        except (TypeError, ValueError):
            continue
        if arr.size == 0:
            continue
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            continue
        return float(np.mean(finite)), True
    return 0.0, False


def _clip01(value: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.clip(value, 0.0, 1.0))


def _tanh_scale(value: float, scale: float) -> float:
    if not np.isfinite(value):
        return 0.0
    return float(np.tanh(max(value, 0.0) / max(float(scale), 1e-6)))


@dataclass(frozen=True)
class TopologyPotentialPoint:
    phi: float
    available: bool
    backhaul_up: float
    full_disconnect: float


class TopologyPotentialShaper:
    """Compute bounded topology potential changes for completed segments."""

    def __init__(self, config, n_agents: int, gamma: float):
        self.n_agents = int(max(n_agents, 1))
        self.gamma = float(gamma)
        self.enabled = bool(getattr(config, "use_topology_potential_shaping", False))
        self.coef = float(getattr(config, "topology_potential_coef", 0.0))
        self.clip = float(getattr(config, "topology_potential_clip", 0.05))
        self.warmup_steps = int(max(getattr(config, "topology_potential_warmup_steps", 0), 0))
        self.discount_mode = str(getattr(config, "topology_potential_discount_mode", "delta")).lower()
        if self.discount_mode not in {"delta", "one_step", "smdp"}:
            raise ValueError(
                "topology_potential_discount_mode must be one of: delta, one_step, smdp"
            )
        self.positive_only = bool(getattr(config, "topology_potential_positive_only", False))

    def _point(self, info: dict) -> TopologyPotentialPoint:
        if not isinstance(info, dict):
            return TopologyPotentialPoint(0.0, False, 0.0, 0.0)

        coverage, has_coverage = _scalar(info, ("coverage_ratio", "coverage", "final_coverage"))
        qos, has_qos = _scalar(info, ("qos_satisfaction_ratio", "qos_satisfaction", "qos"))
        served, has_served = _scalar(
            info,
            (
                "current_backhaul_served_users",
                "backhaul_served_users",
                "effective_connected_users",
                "served_users",
            ),
        )
        uavs_backhaul, has_uavs = _scalar(
            info,
            ("uavs_with_backhaul", "connected_uavs", "backhaul_connected_uavs"),
        )
        connectivity, has_connectivity = _scalar(
            info,
            ("connectivity_ratio", "network_connectivity_ratio"),
        )
        throughput, has_throughput = _scalar(
            info,
            (
                "system_throughput_mbps",
                "effective_end_to_end_throughput_mbps",
                "total_throughput_mbps",
                "throughput",
            ),
        )
        bottleneck, has_bottleneck = _scalar(
            info,
            (
                "min_serving_backhaul_bottleneck_mbps",
                "avg_serving_backhaul_bottleneck_mbps",
                "backhaul_margin",
            ),
        )
        disconnect, has_disconnect = _scalar(
            info,
            ("full_network_disconnect", "full_disconnect", "network_disconnected"),
        )
        outage, has_outage = _scalar(info, ("backhaul_outage_ratio", "service_drop_ratio"))
        relay_loss, has_relay_loss = _scalar(
            info,
            ("relay_route_loss_ratio", "relay_route_loss_prev_served_ratio"),
        )

        service = _clip01(coverage) if has_coverage else _tanh_scale(served, self.n_agents * 2.0)
        qos_score = _clip01(qos) if has_qos else 0.0
        backhaul_ratio = _clip01(uavs_backhaul / self.n_agents) if has_uavs else 0.0
        conn_ratio = (
            _clip01(connectivity)
            if has_connectivity
            else (_clip01(uavs_backhaul / self.n_agents) if has_uavs else 0.0)
        )
        disconnect_flag = _clip01(disconnect) if has_disconnect else 0.0
        outage_ratio = _clip01(outage) if has_outage else 0.0
        relay_loss_ratio = _clip01(relay_loss) if has_relay_loss else 0.0
        throughput_score = _tanh_scale(throughput, 20.0) if has_throughput else 0.0
        bottleneck_score = _tanh_scale(bottleneck, 20.0) if has_bottleneck else 0.0
        backhaul_up = (
            float(service > 1e-6 and disconnect_flag < 0.5 and outage_ratio < 0.999)
            if (has_served or has_coverage or has_throughput)
            else 0.0
        )

        available = any(
            (
                has_coverage,
                has_qos,
                has_served,
                has_uavs,
                has_connectivity,
                has_throughput,
                has_bottleneck,
                has_disconnect,
                has_outage,
                has_relay_loss,
            )
        )
        positive = (
            0.25 * service
            + 0.15 * qos_score
            + 0.15 * backhaul_ratio
            + 0.15 * conn_ratio
            + 0.15 * backhaul_up
            + 0.10 * throughput_score
            + 0.05 * bottleneck_score
        )
        negative = 0.35 * disconnect_flag + 0.20 * outage_ratio + 0.15 * relay_loss_ratio
        return TopologyPotentialPoint(
            phi=float(positive - negative),
            available=bool(available),
            backhaul_up=float(backhaul_up),
            full_disconnect=float(disconnect_flag),
        )

    def _discount(self, length: int) -> float:
        if self.discount_mode == "delta":
            return 1.0
        if self.discount_mode == "one_step":
            return self.gamma
        return float(self.gamma ** max(int(length), 1))

    def _segment(self, segment) -> tuple[float, float, dict[str, float]]:
        points = [
            self._point(info)
            for info in getattr(segment, "reward_info_seq", [])
            if isinstance(info, dict)
        ]
        points = [point for point in points if point.available]
        if len(points) < 2:
            return 0.0, 0.0, {
                "available": 0.0,
                "phi_start": 0.0,
                "phi_end": 0.0,
                "delta": 0.0,
                "discount": 1.0,
                "backhaul_start": 0.0,
                "backhaul_end": 0.0,
                "disconnect_start": 0.0,
                "disconnect_end": 0.0,
            }
        start = points[0]
        end = points[-1]
        discount = self._discount(getattr(segment, "length", len(points)))
        delta = float(discount * end.phi - start.phi)
        raw = max(delta, 0.0) if self.positive_only else delta
        return raw, self.coef * raw, {
            "available": 1.0,
            "phi_start": start.phi,
            "phi_end": end.phi,
            "delta": delta,
            "discount": discount,
            "backhaul_start": start.backhaul_up,
            "backhaul_end": end.backhaul_up,
            "disconnect_start": start.full_disconnect,
            "disconnect_end": end.full_disconnect,
        }

    def rewards(self, segments, total_steps: int) -> tuple[np.ndarray, dict[str, float]]:
        metrics = empty_topology_potential_metrics()
        if not segments:
            return np.zeros(0, dtype=np.float32), metrics

        raw_values: list[float] = []
        unclipped_values: list[float] = []
        rewards: list[float] = []
        rows: list[dict[str, float]] = []
        warmup_active = int(total_steps) < self.warmup_steps
        active = bool(self.enabled and self.coef != 0.0 and not warmup_active)
        for segment in segments:
            raw, unclipped, row = self._segment(segment)
            reward = unclipped if active and row["available"] > 0.0 else 0.0
            if self.clip > 0.0:
                reward = float(np.clip(reward, -self.clip, self.clip))
            raw_values.append(float(raw))
            unclipped_values.append(float(unclipped))
            rewards.append(float(reward))
            rows.append(row)

        rewards_np = np.asarray(rewards, dtype=np.float32)
        unclipped_np = np.asarray(unclipped_values, dtype=np.float32)
        clip_frac = (
            float(np.mean(np.abs(unclipped_np - rewards_np) > 1e-8))
            if active and unclipped_np.size
            else 0.0
        )
        available = [row["available"] for row in rows]
        metrics.update(
            {
                "topology_potential_available_frac": _safe_mean(available),
                "topology_potential_active": float(active),
                "topology_potential_warmup_active": float(warmup_active),
                "topology_potential_raw_mean": _safe_mean(raw_values),
                "topology_potential_raw_positive_frac": _safe_mean(
                    float(value > 0.0) for value in raw_values
                ),
                "topology_potential_unclipped_mean": _safe_mean(unclipped_values),
                "topology_potential_reward_mean": _safe_mean(rewards),
                "topology_potential_clip_frac": clip_frac,
                "topology_potential_phi_start_mean": _safe_mean(row["phi_start"] for row in rows),
                "topology_potential_phi_end_mean": _safe_mean(row["phi_end"] for row in rows),
                "topology_potential_delta_mean": _safe_mean(row["delta"] for row in rows),
                "topology_potential_discount_mean": _safe_mean(row["discount"] for row in rows),
                "topology_potential_backhaul_up_start_mean": _safe_mean(
                    row["backhaul_start"] for row in rows
                ),
                "topology_potential_backhaul_up_end_mean": _safe_mean(
                    row["backhaul_end"] for row in rows
                ),
                "topology_potential_full_disconnect_start_mean": _safe_mean(
                    row["disconnect_start"] for row in rows
                ),
                "topology_potential_full_disconnect_end_mean": _safe_mean(
                    row["disconnect_end"] for row in rows
                ),
            }
        )
        return rewards_np, metrics
