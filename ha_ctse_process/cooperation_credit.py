"""Cooperation-credit diagnostics for standalone HA-CTSE.

These metrics are diagnostics only.  They intentionally stay off the reward
path so relay/backhaul signals are used to expose cooperative credit assignment
failure, not as hard-coded relay-chain targets.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


COOPERATION_CREDIT_FIELDS = (
    "credit_probe_available_frac",
    "credit_full_disconnect_mean",
    "credit_recovery_rate",
    "credit_collapse_rate",
    "credit_delta_uavs_with_backhaul_mean",
    "credit_delta_connectivity_ratio_mean",
    "credit_delta_backhaul_served_users_mean",
    "credit_delta_backhaul_outage_ratio_mean",
    "credit_delta_relay_route_loss_ratio_mean",
    "credit_bottleneck_mbps_mean",
    "credit_backhaul_connected_step_fraction",
    "credit_throughput_when_backhaul_connected_mbps",
    "credit_delta_full_disconnect_streak_mean",
    "credit_reward_conn_corr",
    "credit_reward_served_corr",
    "credit_reward_outage_corr",
)


def empty_cooperation_credit_metrics() -> dict[str, float]:
    return {field: 0.0 for field in COOPERATION_CREDIT_FIELDS}


def _scalar(value) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None
    return float(np.mean(finite))


def _series(segment, aliases: tuple[str, ...]) -> list[float]:
    values: list[float] = []
    for info in getattr(segment, "reward_info_seq", []):
        if not isinstance(info, dict):
            continue
        for key in aliases:
            if key in info:
                scalar = _scalar(info.get(key))
                if scalar is not None:
                    values.append(scalar)
                break
    return values


def _delta(segment, aliases: tuple[str, ...]) -> float:
    values = _series(segment, aliases)
    if len(values) < 2:
        return float("nan")
    return float(values[-1] - values[0])


def _mean(segment, aliases: tuple[str, ...]) -> float:
    values = _series(segment, aliases)
    if not values:
        return float("nan")
    return float(np.mean(values))


def _disconnect_transition(segment) -> tuple[float, float, float]:
    values = _series(
        segment,
        (
            "full_network_disconnect",
            "full_disconnect",
            "network_disconnected",
        ),
    )
    if not values:
        return float("nan"), float("nan"), float("nan")
    start_disconnected = values[0] >= 0.5
    end_disconnected = values[-1] >= 0.5
    mean_disconnected = float(np.mean(values))
    recovery = float(start_disconnected and not end_disconnected)
    collapse = float((not start_disconnected) and end_disconnected)
    return mean_disconnected, recovery, collapse


def _safe_mean(values: Iterable[float]) -> float:
    arr = np.asarray(list(values), dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    return float(np.mean(arr)) if arr.size else 0.0


def _safe_corr(xs: Iterable[float], ys: Iterable[float]) -> float:
    x = np.asarray(list(xs), dtype=np.float64)
    y = np.asarray(list(ys), dtype=np.float64)
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return 0.0
    x = x[mask]
    y = y[mask]
    if float(np.std(x)) <= 1e-8 or float(np.std(y)) <= 1e-8:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def _segment_metrics(segment) -> dict[str, float]:
    full_disconnect, recovery, collapse = _disconnect_transition(segment)
    backhaul_flags: list[float] = []
    conditional_throughputs: list[float] = []
    for info in getattr(segment, "reward_info_seq", []):
        if not isinstance(info, dict):
            continue
        served = _scalar(
            next(
                (info.get(key) for key in (
                    "current_backhaul_served_users",
                    "backhaul_served_users",
                    "effective_connected_users",
                    "served_users",
                ) if key in info),
                None,
            )
        )
        throughput = _scalar(
            next(
                (info.get(key) for key in (
                    "system_throughput_mbps",
                    "effective_end_to_end_throughput_mbps",
                    "total_throughput_mbps",
                    "throughput",
                ) if key in info),
                None,
            )
        )
        disconnect = _scalar(
            next(
                (info.get(key) for key in (
                    "full_network_disconnect",
                    "full_disconnect",
                    "network_disconnected",
                ) if key in info),
                None,
            )
        )
        outage = _scalar(
            next(
                (info.get(key) for key in (
                    "backhaul_outage_ratio",
                    "service_drop_ratio",
                ) if key in info),
                None,
            )
        )
        backhaul_up = (
            served is not None
            and float(served) > 0.0
            and (disconnect is None or float(disconnect) < 0.5)
            and (outage is None or float(outage) < 0.999)
        )
        backhaul_flags.append(1.0 if backhaul_up else 0.0)
        if backhaul_up and throughput is not None:
            conditional_throughputs.append(float(throughput))
    return {
        "credit_full_disconnect_mean": full_disconnect,
        "credit_recovery_rate": recovery,
        "credit_collapse_rate": collapse,
        "credit_delta_uavs_with_backhaul_mean": _delta(
            segment,
            (
                "uavs_with_backhaul",
                "connected_uavs",
                "backhaul_connected_uavs",
            ),
        ),
        "credit_delta_connectivity_ratio_mean": _delta(
            segment,
            (
                "connectivity_ratio",
                "network_connectivity_ratio",
            ),
        ),
        "credit_delta_backhaul_served_users_mean": _delta(
            segment,
            (
                "current_backhaul_served_users",
                "backhaul_served_users",
                "effective_connected_users",
                "served_users",
            ),
        ),
        "credit_delta_backhaul_outage_ratio_mean": _delta(
            segment,
            (
                "backhaul_outage_ratio",
                "service_drop_ratio",
            ),
        ),
        "credit_delta_relay_route_loss_ratio_mean": _delta(
            segment,
            (
                "relay_route_loss_ratio",
                "relay_route_loss_prev_served_ratio",
            ),
        ),
        "credit_bottleneck_mbps_mean": _mean(
            segment,
            (
                "min_serving_backhaul_bottleneck_mbps",
                "avg_serving_backhaul_bottleneck_mbps",
                "backhaul_margin",
            ),
        ),
        "credit_backhaul_connected_step_fraction": _safe_mean(backhaul_flags),
        "credit_throughput_when_backhaul_connected_mbps": _safe_mean(conditional_throughputs),
        "credit_delta_full_disconnect_streak_mean": _delta(
            segment,
            (
                "full_disconnect_streak",
                "backhaul_outage_streak",
            ),
        ),
    }


def aggregate_cooperation_credit(segments) -> dict[str, float]:
    if not segments:
        return empty_cooperation_credit_metrics()

    rows = [_segment_metrics(segment) for segment in segments]
    metrics = empty_cooperation_credit_metrics()
    available = [
        any(np.isfinite(value) for value in row.values())
        for row in rows
    ]
    metrics["credit_probe_available_frac"] = float(np.mean(available)) if available else 0.0

    for field in COOPERATION_CREDIT_FIELDS:
        if field.startswith("credit_reward_") or field == "credit_probe_available_frac":
            continue
        metrics[field] = _safe_mean(row.get(field, float("nan")) for row in rows)

    returns = [float(np.sum(getattr(segment, "rewards", []) or [0.0])) for segment in segments]
    metrics["credit_reward_conn_corr"] = _safe_corr(
        returns,
        (row.get("credit_delta_connectivity_ratio_mean", float("nan")) for row in rows),
    )
    metrics["credit_reward_served_corr"] = _safe_corr(
        returns,
        (row.get("credit_delta_backhaul_served_users_mean", float("nan")) for row in rows),
    )
    metrics["credit_reward_outage_corr"] = _safe_corr(
        returns,
        (row.get("credit_delta_backhaul_outage_ratio_mean", float("nan")) for row in rows),
    )
    return metrics
