"""Pure observation-to-command return feedback for the fixed B06 evaluation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FeedbackLayout:
    """The fixed legal-observation suffix and physical command scales."""

    n_uavs: int = 8
    observation_dim: int = 365
    uav_record_fields: int = 13
    station_count: int = 2
    station_record_fields: int = 8
    xy_scale_m: float = 8000.0
    z_scale_m: float = 150.0
    horizontal_speed_mps: float = 30.0
    vertical_speed_mps: float = 5.0
    docking_radius_m: float = 160.0
    enter_margin: float = 0.0
    exit_margin: float = 0.05

    @property
    def suffix_fields(self) -> int:
        return (
            self.n_uavs * self.uav_record_fields
            + self.station_count * self.station_record_fields
        )

    def validate(self) -> None:
        if (
            self.n_uavs != 8
            or self.observation_dim != 365
            or self.uav_record_fields != 13
            or self.station_count != 2
            or self.station_record_fields != 8
            or self.suffix_fields != 120
            or self.xy_scale_m != 8000.0
            or self.z_scale_m != 150.0
            or self.horizontal_speed_mps != 30.0
            or self.vertical_speed_mps != 5.0
            or self.docking_radius_m != 160.0
            or self.enter_margin != 0.0
            or self.exit_margin != 0.05
        ):
            raise ValueError("B06 feedback layout is not the fixed production contract")


@dataclass(frozen=True)
class FeedbackDecision:
    submitted_actions: np.ndarray
    modes: np.ndarray
    entered: np.ndarray
    exited: np.ndarray
    margins: np.ndarray
    batteries: np.ndarray
    selected_stations: np.ndarray
    station_distances_m: np.ndarray
    station_vectors_m: np.ndarray


PRODUCTION_LAYOUT = FeedbackLayout()


def _decode(observations: np.ndarray, layout: FeedbackLayout):
    layout.validate()
    obs = np.asarray(observations)
    if obs.shape != (layout.n_uavs, layout.observation_dim):
        raise ValueError(
            f"observations must have shape {(layout.n_uavs, layout.observation_dim)}, "
            f"got {obs.shape}"
        )
    if not np.issubdtype(obs.dtype, np.floating) or not np.isfinite(obs).all():
        raise ValueError("legal observations must be finite floating-point values")

    suffix = obs[:, -layout.suffix_fields :]
    uav_width = layout.n_uavs * layout.uav_record_fields
    uavs = suffix[:, :uav_width].reshape(
        layout.n_uavs, layout.n_uavs, layout.uav_record_fields
    )
    stations = suffix[:, uav_width:].reshape(
        layout.n_uavs, layout.station_count, layout.station_record_fields
    )
    own = np.arange(layout.n_uavs)
    margins = uavs[own, own, 12].astype(np.float32, copy=True)
    batteries = uavs[own, own, 3].astype(np.float32, copy=True)

    valid = stations[:, :, 7] == 1.0
    if np.any(~np.logical_or(stations[:, :, 7] == 0.0, valid)):
        raise ValueError("station validity fields must be exactly zero or one")
    if np.any(~valid.any(axis=1)):
        raise ValueError("each UAV observation must contain a valid charging station")

    vectors = stations[:, :, :3].astype(np.float64, copy=True)
    vectors[:, :, :2] *= layout.xy_scale_m
    vectors[:, :, 2] *= layout.z_scale_m
    distances = np.linalg.norm(vectors, axis=2)
    distances[~valid] = np.inf
    # np.argmin returns the first occurrence, which fixes exact ties to the lower index.
    selected = np.argmin(distances, axis=1).astype(np.int64)
    chosen_vectors = vectors[own, selected]
    chosen_distances = distances[own, selected]
    if not np.isfinite(chosen_distances).all():
        raise ValueError("valid station vectors must produce finite physical distances")
    return margins, batteries, selected, chosen_distances, chosen_vectors


def decode_legal_observations(
    observations: np.ndarray,
    *,
    layout: FeedbackLayout = PRODUCTION_LAYOUT,
):
    """Decode only fields available in each member's legal actor observation."""

    return _decode(observations, layout)


def apply_feedback(
    observations: np.ndarray,
    proposed_actions: np.ndarray,
    modes: np.ndarray,
    *,
    layout: FeedbackLayout = PRODUCTION_LAYOUT,
) -> FeedbackDecision:
    """Apply the fixed hysteretic rule using only legal observations and mode bits."""

    actions = np.asarray(proposed_actions)
    prior_modes = np.asarray(modes)
    if actions.shape != (layout.n_uavs, 4):
        raise ValueError(f"proposed actions must have shape {(layout.n_uavs, 4)}")
    if not np.issubdtype(actions.dtype, np.floating) or not np.isfinite(actions).all():
        raise ValueError("proposed actions must be finite floating-point values")
    if prior_modes.shape != (layout.n_uavs,) or prior_modes.dtype != np.bool_:
        raise ValueError(f"modes must be a bool array with shape {(layout.n_uavs,)}")

    margins, batteries, selected, distances, vectors = _decode(observations, layout)
    new_modes = prior_modes.copy()
    new_modes[margins <= layout.enter_margin] = True
    new_modes[margins >= layout.exit_margin] = False
    entered = new_modes & ~prior_modes
    exited = ~new_modes & prior_modes

    submitted = actions.astype(np.float32, copy=True)
    active = np.flatnonzero(new_modes)
    for index in active:
        vector = vectors[index]
        distance = float(distances[index])
        if distance <= layout.docking_radius_m:
            submitted[index] = np.asarray((0.0, 0.0, 0.0, 1.0), dtype=np.float32)
            continue
        duration = max(
            1.0,
            float(np.linalg.norm(vector[:2])) / layout.horizontal_speed_mps,
            abs(float(vector[2])) / layout.vertical_speed_mps,
        )
        velocity = vector / duration
        submitted[index] = np.asarray(
            (
                velocity[0] / layout.horizontal_speed_mps,
                velocity[1] / layout.horizontal_speed_mps,
                velocity[2] / layout.vertical_speed_mps,
                1.0,
            ),
            dtype=np.float32,
        )

    return FeedbackDecision(
        submitted_actions=submitted,
        modes=new_modes,
        entered=entered,
        exited=exited,
        margins=margins,
        batteries=batteries,
        selected_stations=selected,
        station_distances_m=distances.astype(np.float32),
        station_vectors_m=vectors.astype(np.float32),
    )
