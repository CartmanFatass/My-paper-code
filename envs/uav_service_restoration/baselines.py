"""Non-training diagnostic controllers.

Information conditions
----------------------
Every controller here reads **only** ``env.get_current_state()``: the permitted
centralized telemetry that also forms the environment's ``state()``.  None of them sees
future demand, future events, the event schedule, the trace cursor or unsensed demand.
That is the point - a greedy comparator that peeked at the future would not be a
comparator at all.

Each controller returns normalised velocity requests, so it passes through exactly the
same vector-norm speed limit, boundary handling and fixed scheduler as any learned
policy.

``RandomController`` is for API and numerical smoke testing only.  It is not a
scientifically sufficient comparator, and no result should be reported against it alone.
"""

from __future__ import annotations

from typing import Any, Protocol

import numpy as np

from .config import EnvConfig
from .dynamics import ACTION_DIM
from .radio import capacity_mbps


class Controller(Protocol):
    """Maps permitted telemetry to normalised velocity requests."""

    name: str

    def reset(self) -> None: ...

    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]: ...


def _zero_actions(agents: list[str]) -> dict[str, np.ndarray]:
    return {agent: np.zeros(ACTION_DIM, dtype=np.float32) for agent in agents}


def _unit_towards(source_xy: np.ndarray, target_xy: np.ndarray) -> np.ndarray:
    delta = np.asarray(target_xy, dtype=np.float64) - np.asarray(source_xy, dtype=np.float64)
    norm = float(np.linalg.norm(delta))
    if norm < 1e-9:
        return np.zeros(2, dtype=np.float64)
    return delta / norm


class StaticUavController:
    """Hold the valid initial deployment positions.

    A useful null: it isolates "does repositioning matter at all" from "is the network
    already sufficient".
    """

    name = "static_uav"

    def __init__(self, config: EnvConfig) -> None:
        self._config = config

    def reset(self) -> None:
        return None

    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]:
        del view
        return _zero_actions(agents)


class RandomController:
    """Uniform random velocity requests.  Smoke testing only."""

    name = "random"

    def __init__(self, config: EnvConfig, seed: int = 0) -> None:
        self._config = config
        self._seed = int(seed)
        self._rng = np.random.default_rng(self._seed)

    def reset(self) -> None:
        self._rng = np.random.default_rng(self._seed)

    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]:
        del view
        return {
            agent: self._rng.uniform(-1.0, 1.0, size=ACTION_DIM).astype(np.float32)
            for agent in agents
        }


class DemandGreedyController:
    """Move toward the highest estimated unmet demand that telemetry actually reports.

    Targets are assigned by a deterministic rule: demand slots are ranked by estimated
    unmet rate, then handed out one per UAV in slot order, so several UAVs do not all
    stack on the single largest slot.  Unobserved slots are not targets - the controller
    cannot chase demand it has no record of.
    """

    name = "demand_greedy"

    def __init__(self, config: EnvConfig, min_unmet_mbps: float = 1e-6) -> None:
        self._config = config
        self._min_unmet = float(min_unmet_mbps)

    def reset(self) -> None:
        return None

    def _targets(self, view: dict[str, Any], n_uavs: int) -> list[int]:
        offered = np.asarray(view["telemetry_demand_offered_mbps"], dtype=np.float64)
        delivered = np.asarray(view["telemetry_demand_delivered_mbps"], dtype=np.float64)
        observed = np.asarray(view["telemetry_demand_observed"], dtype=bool)
        unmet = np.where(observed, np.maximum(offered - delivered, 0.0), 0.0)
        candidates = [
            index for index in np.argsort(-unmet, kind="stable") if unmet[index] > self._min_unmet
        ]
        if not candidates:
            return []
        return [int(candidates[index % len(candidates)]) for index in range(n_uavs)]

    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]:
        positions = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        targets = self._targets(view, positions.shape[0])
        if not targets:
            return _zero_actions(agents)
        actions: dict[str, np.ndarray] = {}
        for index, agent in enumerate(agents):
            direction = _unit_towards(positions[index, :2], demand_xy[targets[index]])
            actions[agent] = np.asarray(
                [direction[0], direction[1], 0.0], dtype=np.float32
            )
        return actions


class BackhaulAwareGreedyController:
    """Greedy over positions that are *also* reachable for backhaul.

    Same information as :class:`DemandGreedyController`.  The difference is the score: a
    candidate target is worth moving to only if, from the position it implies, the UAV
    would still have usable wireless backhaul to a site that telemetry reports as having a
    live radio **and** a live core link.  A UAV parked over demand with no way back to the
    core delivers nothing, which the network model already enforces; this controller
    simply does not walk into that.

    It also draws one inference that the naive controller does not, entirely from
    permitted telemetry: the management plane reports site capability, so when a demand
    point's last known offered demand was positive and **no** site whose radio telemetry
    still reads up now covers it, that point's last known offered demand is treated as
    now unmet.  This is last-known demand combined with a currently reported site
    failure - not a look at the true current demand, which remains unknown wherever
    nothing senses it.

    The score trades estimated unmet demand against the backhaul capacity available at
    the candidate position:

        score = min(unmet_estimate, backhaul_capacity)

    i.e. the deliverable part of the unmet demand, ignoring contention - a deliberately
    optimistic but cheap surrogate, not a solve of the scheduler.
    """

    name = "backhaul_aware_greedy"

    def __init__(self, config: EnvConfig, min_unmet_mbps: float = 1e-6) -> None:
        self._config = config
        self._min_unmet = float(min_unmet_mbps)
        self._backhaul_model = config.network.radio_models["site_uav_backhaul"]
        self._access_model = config.network.radio_models["uav_access"]

    def reset(self) -> None:
        return None

    def _live_gateway_positions(self, view: dict[str, Any]) -> np.ndarray:
        """Sites whose telemetry reports both a live radio and a live core link."""

        capability = np.asarray(view["telemetry_site_capability"], dtype=np.float64)
        observed = np.asarray(view["telemetry_site_observed"], dtype=bool)
        sites = np.asarray(view["site_positions"], dtype=np.float64).reshape(-1, 3)
        live = observed & (capability[:, 0] > 0.5) & (capability[:, 1] > 0.5)
        return sites[live]

    def _unmet_estimate(self, view: dict[str, Any]) -> np.ndarray:
        """Estimated unmet rate per demand slot from permitted telemetry only."""

        offered = np.asarray(view["telemetry_demand_offered_mbps"], dtype=np.float64)
        delivered = np.asarray(view["telemetry_demand_delivered_mbps"], dtype=np.float64)
        observed = np.asarray(view["telemetry_demand_observed"], dtype=bool)
        ever_reported = np.isfinite(np.asarray(view["telemetry_demand_age_s"], dtype=np.float64))
        reported_unmet = np.where(observed, np.maximum(offered - delivered, 0.0), 0.0)

        capability = np.asarray(view["telemetry_site_capability"], dtype=np.float64)
        site_observed = np.asarray(view["telemetry_site_observed"], dtype=bool)
        sites = np.asarray(view["site_positions"], dtype=np.float64).reshape(-1, 3)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        radius = float(view["site_registration_radius_m"])
        demand_xyz = np.zeros((demand_xy.shape[0], 3), dtype=np.float64)
        demand_xyz[:, :2] = demand_xy
        radio_live = site_observed & (capability[:, 0] > 0.5)
        if radio_live.any():
            distance = np.sqrt(
                np.sum((demand_xyz[:, None, :] - sites[None, radio_live, :]) ** 2, axis=-1)
            )
            still_covered = (distance <= radius).any(axis=1)
        else:
            still_covered = np.zeros(demand_xy.shape[0], dtype=bool)
        lost_coverage = ever_reported & (~still_covered) & (offered > 0.0)
        return np.where(lost_coverage, offered, reported_unmet)

    def act(self, view: dict[str, Any], agents: list[str]) -> dict[str, np.ndarray]:
        positions = np.asarray(view["uav_positions"], dtype=np.float64).reshape(-1, 3)
        demand_xy = np.asarray(view["demand_point_positions"], dtype=np.float64).reshape(-1, 2)
        unmet = self._unmet_estimate(view)
        gateways = self._live_gateway_positions(view)
        if gateways.shape[0] == 0 or not (unmet > self._min_unmet).any():
            # No live egress, or nothing reported unmet: repositioning cannot help, and
            # saying so is a legitimate diagnostic outcome.
            return _zero_actions(agents)

        altitude = float(np.clip(
            positions[:, 2].mean(),
            self._config.dynamics.altitude_range_m[0],
            self._config.dynamics.altitude_range_m[1],
        ))
        candidate = np.zeros((demand_xy.shape[0], 3), dtype=np.float64)
        candidate[:, :2] = demand_xy
        candidate[:, 2] = altitude
        gateway_distance = np.sqrt(
            np.sum((candidate[:, None, :] - gateways[None, :, :]) ** 2, axis=-1)
        )
        backhaul = capacity_mbps(gateway_distance, self._backhaul_model).max(axis=1)
        score = np.minimum(unmet, backhaul)
        score = np.where(unmet > self._min_unmet, score, 0.0)

        order = [int(index) for index in np.argsort(-score, kind="stable") if score[index] > 0.0]
        if not order:
            return _zero_actions(agents)
        actions: dict[str, np.ndarray] = {}
        assigned: set[int] = set()
        for index, agent in enumerate(agents):
            target = None
            for slot in order:
                if slot not in assigned:
                    target = slot
                    break
            if target is None:
                target = order[index % len(order)]
            else:
                assigned.add(target)
            direction = _unit_towards(positions[index, :2], demand_xy[target])
            actions[agent] = np.asarray([direction[0], direction[1], 0.0], dtype=np.float32)
        return actions


def build_controller(name: str, config: EnvConfig, *, seed: int = 0) -> Controller:
    """Construct a diagnostic controller by name."""

    if name == "static_uav":
        return StaticUavController(config)
    if name == "random":
        return RandomController(config, seed=seed)
    if name == "demand_greedy":
        return DemandGreedyController(config)
    if name == "backhaul_aware_greedy":
        return BackhaulAwareGreedyController(config)
    raise ValueError(
        f"unknown controller {name!r}; available: static_uav, random, demand_greedy, "
        "backhaul_aware_greedy (ground_only is a network-model reference, not a "
        "controller)"
    )


CONTROLLER_NAMES = ("static_uav", "demand_greedy", "backhaul_aware_greedy", "random")
