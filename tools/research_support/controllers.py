"""Explicit named rule controllers for the diagnostic demonstrations.

These are **untuned engineering rules**, not baselines and not policies. They exist so that a
live demonstration shows a simulator doing something legible instead of a fleet holding
still, and so that a recorded trace has an identifiable producer. None of them is evidence
about what a learned policy would do, and none of them establishes baseline competence:
that needs a separate experiment with its own design.

Each controller:

* reads only values the environment already produced and already exposes;
* is deterministic given its seed;
* performs no optimizer update and holds no learned parameter;
* invents no skill sequence. The legacy relay route has no skill layer, so these
  controllers report none, and the viewer shows none.

The service-restoration route already ships its own diagnostic controllers in
``envs.uav_service_restoration.baselines`` (``static_uav``, ``random``, ``demand_greedy``,
``backhaul_aware_greedy``); those are reused rather than duplicated here.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol

import numpy as np


class LegacyController(Protocol):
    """Action source for the legacy array-adapter routes."""

    name: str

    def reset(self) -> None: ...

    def act(self, state_info: Mapping[str, Any], *, n_uavs: int, action_dim: int) -> np.ndarray: ...


def _unit(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    norms = np.where(norms < 1e-9, 1.0, norms)
    return vectors / norms


class LegacyHoldController:
    """Zero action. Useful as the reference that shows what standing still looks like."""

    name = "legacy_hold"

    def reset(self) -> None:
        return None

    def act(
        self, state_info: Mapping[str, Any], *, n_uavs: int, action_dim: int
    ) -> np.ndarray:
        del state_info
        return np.zeros((int(n_uavs), int(action_dim)), dtype=np.float32)


class LegacyClusterCoverageController:
    """Each UAV flies toward one cluster of ground UEs; one UAV holds a relay position.

    The rule, in full:

    1. Partition the current UE positions into ``n_uavs`` groups with a fixed-iteration
       k-means seeded deterministically from the UE positions themselves (no RNG draw from
       the environment, so attaching this controller cannot perturb a simulation's random
       stream).
    2. Assign UAVs to cluster centroids by a greedy nearest-first matching.
    3. If ``relay_fraction`` is positive, the UAVs whose assigned centroid is farthest from
       the ground station are instead sent to a point on the straight line between the
       station and the UE centroid, so a multi-hop backhaul chain can form.
    4. The commanded action is the unit direction to the target, which this route scales by
       ``max_speed``; the vertical component drives altitude toward ``target_altitude_m``.

    This is a coverage heuristic. It does not optimise service, does not know the radio
    model, and is not tuned against anything.
    """

    name = "legacy_cluster_coverage"

    def __init__(
        self,
        *,
        relay_fraction: float = 0.34,
        target_altitude_m: float = 120.0,
        altitude_gain: float = 0.02,
        kmeans_iterations: int = 12,
        arrival_radius_m: float = 40.0,
    ) -> None:
        self.relay_fraction = float(relay_fraction)
        self.target_altitude_m = float(target_altitude_m)
        self.altitude_gain = float(altitude_gain)
        self.kmeans_iterations = int(kmeans_iterations)
        self.arrival_radius_m = float(arrival_radius_m)
        self._targets: np.ndarray | None = None

    def reset(self) -> None:
        self._targets = None

    # ----------------------------------------------------------------------------------

    def act(
        self, state_info: Mapping[str, Any], *, n_uavs: int, action_dim: int
    ) -> np.ndarray:
        uav = np.asarray(state_info.get("uav_positions"), dtype=np.float64)
        users = state_info.get("user_positions")
        action = np.zeros((int(n_uavs), int(action_dim)), dtype=np.float32)
        if uav.size == 0 or users is None:
            return action
        users = np.asarray(users, dtype=np.float64)
        if users.size == 0:
            return action

        centroids = self._kmeans(users[:, :2], min(int(n_uavs), int(users.shape[0])))
        stations = state_info.get("ground_bs_positions")
        station_xy = (
            np.asarray(stations, dtype=np.float64)[0, :2]
            if stations is not None and np.asarray(stations).size
            else None
        )
        targets = self._assign(uav[:, :2], centroids)

        if station_xy is not None and self.relay_fraction > 0.0:
            n_relay = max(1, int(round(self.relay_fraction * uav.shape[0])))
            distances = np.linalg.norm(targets - station_xy, axis=1)
            relay_order = np.argsort(-distances)[:n_relay]
            ue_centroid = users[:, :2].mean(axis=0)
            for rank, index in enumerate(relay_order):
                # Spread relay hops evenly along the station-to-UEs line.
                position = (rank + 1) / (n_relay + 1)
                targets[index] = station_xy + position * (ue_centroid - station_xy)

        self._targets = targets
        delta = targets - uav[:, :2]
        far = np.linalg.norm(delta, axis=1) > self.arrival_radius_m
        horizontal = _unit(delta) * far[:, None]
        action[:, 0] = horizontal[:, 0]
        action[:, 1] = horizontal[:, 1]
        if action_dim >= 3 and uav.shape[1] >= 3:
            vertical = (self.target_altitude_m - uav[:, 2]) * self.altitude_gain
            action[:, 2] = np.clip(vertical, -1.0, 1.0)
        return np.clip(action, -1.0, 1.0).astype(np.float32)

    @property
    def targets_xy(self) -> np.ndarray | None:
        """Last commanded targets, for a report that wants to show the rule's intent."""

        return None if self._targets is None else self._targets.copy()

    # ----------------------------------------------------------------------------------

    def _kmeans(self, points: np.ndarray, k: int) -> np.ndarray:
        """Deterministic k-means with no RNG draw.

        Seeds are the ``k`` points farthest apart under a greedy furthest-point rule, so
        two runs on the same positions produce the same partition and attaching this
        controller cannot consume an environment random stream.
        """

        k = max(1, min(int(k), int(points.shape[0])))
        seeds = [int(np.argmin(points.sum(axis=1)))]
        while len(seeds) < k:
            distances = np.min(
                np.linalg.norm(points[:, None, :] - points[seeds][None, :, :], axis=2), axis=1
            )
            seeds.append(int(np.argmax(distances)))
        centroids = points[seeds].astype(np.float64).copy()
        for _ in range(self.kmeans_iterations):
            assignment = np.argmin(
                np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2), axis=1
            )
            moved = False
            for index in range(k):
                members = points[assignment == index]
                if members.size == 0:
                    continue
                centre = members.mean(axis=0)
                if not np.allclose(centre, centroids[index]):
                    centroids[index] = centre
                    moved = True
            if not moved:
                break
        return centroids

    @staticmethod
    def _assign(uav_xy: np.ndarray, centroids: np.ndarray) -> np.ndarray:
        """Greedy nearest-first matching of UAVs to centroids, reusing centroids if fewer."""

        n_uavs = int(uav_xy.shape[0])
        n_centroids = int(centroids.shape[0])
        targets = np.zeros((n_uavs, 2), dtype=np.float64)
        cost = np.linalg.norm(uav_xy[:, None, :] - centroids[None, :, :], axis=2)
        remaining_uavs = set(range(n_uavs))
        remaining_centroids = set(range(n_centroids))
        while remaining_uavs:
            if not remaining_centroids:
                remaining_centroids = set(range(n_centroids))
            best = min(
                ((u, c) for u in remaining_uavs for c in remaining_centroids),
                key=lambda pair: cost[pair[0], pair[1]],
            )
            targets[best[0]] = centroids[best[1]]
            remaining_uavs.discard(best[0])
            remaining_centroids.discard(best[1])
        return targets


LEGACY_CONTROLLERS: dict[str, type] = {
    LegacyHoldController.name: LegacyHoldController,
    LegacyClusterCoverageController.name: LegacyClusterCoverageController,
}


def build_legacy_controller(name: str, **kwargs: Any) -> LegacyController:
    """Construct a named legacy diagnostic controller."""

    try:
        factory = LEGACY_CONTROLLERS[str(name)]
    except KeyError as error:
        raise ValueError(
            f"unknown legacy controller {name!r}; available: "
            f"{', '.join(sorted(LEGACY_CONTROLLERS))}"
        ) from error
    return factory(**kwargs)
