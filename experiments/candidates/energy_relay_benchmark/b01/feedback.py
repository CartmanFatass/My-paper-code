"""Parametrised B06 return shield: same decode, station choice and command, free margins.

The logic is copied from ``uav_service_auxiliary/b06/feedback.py`` (``_decode`` and
``apply_feedback``) with one change: the entry/exit margins come from ``FeedbackParams``
instead of the production-pinned ``FeedbackLayout.validate``.  At (0.0, 0.05) the result is
bit-identical to B06 (pinned by test).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


# Fixed S7-S2 legal-observation suffix and physical command scales (B06 FeedbackLayout values).
N_UAVS = 8
OBSERVATION_DIM = 365
UAV_RECORD_FIELDS = 13
STATION_COUNT = 2
STATION_RECORD_FIELDS = 8
SUFFIX_FIELDS = N_UAVS * UAV_RECORD_FIELDS + STATION_COUNT * STATION_RECORD_FIELDS  # 120
XY_SCALE_M = 8000.0
Z_SCALE_M = 150.0
HORIZONTAL_SPEED_MPS = 30.0
VERTICAL_SPEED_MPS = 5.0
DOCKING_RADIUS_M = 160.0


@dataclass(frozen=True)
class FeedbackParams:
    """Hysteresis margins: enter when own margin <= enter, leave when >= exit.

    Non-production thresholds compare in float32: the decoded margins are float32 and the
    Python-float thresholds are cast to float32 by NumPy (1.26 value-based casting), so a
    threshold t acts as float32(t), not as the float64 value.
    """

    enter_margin: float
    exit_margin: float

    def __post_init__(self) -> None:
        # Python floats keep NumPy's comparison against float32 margins identical to B06.
        enter, exit_ = float(self.enter_margin), float(self.exit_margin)
        if not (math.isfinite(enter) and math.isfinite(exit_)):
            raise ValueError("feedback margins must be finite")
        if not exit_ > enter:
            raise ValueError("feedback exit_margin must exceed enter_margin")
        object.__setattr__(self, "enter_margin", enter)
        object.__setattr__(self, "exit_margin", exit_)

    @property
    def label(self) -> str:
        return f"e{self.enter_margin:.2f}_x{self.exit_margin:.2f}"


PRODUCTION_PARAMS = FeedbackParams(enter_margin=0.0, exit_margin=0.05)


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


def decode_legal_observations(observations: np.ndarray):
    """Own margin/battery and the nearest valid station vector from each legal observation."""

    obs = np.asarray(observations)
    if obs.shape != (N_UAVS, OBSERVATION_DIM):
        raise ValueError(
            f"observations must have shape {(N_UAVS, OBSERVATION_DIM)}, got {obs.shape}"
        )
    if not np.issubdtype(obs.dtype, np.floating) or not np.isfinite(obs).all():
        raise ValueError("legal observations must be finite floating-point values")

    suffix = obs[:, -SUFFIX_FIELDS:]
    uav_width = N_UAVS * UAV_RECORD_FIELDS
    uavs = suffix[:, :uav_width].reshape(N_UAVS, N_UAVS, UAV_RECORD_FIELDS)
    stations = suffix[:, uav_width:].reshape(N_UAVS, STATION_COUNT, STATION_RECORD_FIELDS)
    own = np.arange(N_UAVS)
    margins = uavs[own, own, 12].astype(np.float32, copy=True)
    batteries = uavs[own, own, 3].astype(np.float32, copy=True)

    valid = stations[:, :, 7] == 1.0
    if np.any(~np.logical_or(stations[:, :, 7] == 0.0, valid)):
        raise ValueError("station validity fields must be exactly zero or one")
    if np.any(~valid.any(axis=1)):
        raise ValueError("each UAV observation must contain a valid charging station")

    vectors = stations[:, :, :3].astype(np.float64, copy=True)
    vectors[:, :, :2] *= XY_SCALE_M
    vectors[:, :, 2] *= Z_SCALE_M
    distances = np.linalg.norm(vectors, axis=2)
    distances[~valid] = np.inf
    # np.argmin returns the first occurrence, which fixes exact ties to the lower index.
    selected = np.argmin(distances, axis=1).astype(np.int64)
    chosen_vectors = vectors[own, selected]
    chosen_distances = distances[own, selected]
    if not np.isfinite(chosen_distances).all():
        raise ValueError("valid station vectors must produce finite physical distances")
    return margins, batteries, selected, chosen_distances, chosen_vectors


def apply_feedback_params(
    observations: np.ndarray,
    proposed_actions: np.ndarray,
    modes: np.ndarray,
    params: FeedbackParams,
) -> FeedbackDecision:
    """B06 hysteretic return rule with caller-chosen entry/exit margins."""

    if not isinstance(params, FeedbackParams):
        raise TypeError("params must be a FeedbackParams")
    actions = np.asarray(proposed_actions)
    prior_modes = np.asarray(modes)
    if actions.shape != (N_UAVS, 4):
        raise ValueError(f"proposed actions must have shape {(N_UAVS, 4)}")
    if not np.issubdtype(actions.dtype, np.floating) or not np.isfinite(actions).all():
        raise ValueError("proposed actions must be finite floating-point values")
    if prior_modes.shape != (N_UAVS,) or prior_modes.dtype != np.bool_:
        raise ValueError(f"modes must be a bool array with shape {(N_UAVS,)}")

    margins, batteries, selected, distances, vectors = decode_legal_observations(observations)
    new_modes = prior_modes.copy()
    new_modes[margins <= params.enter_margin] = True
    new_modes[margins >= params.exit_margin] = False
    entered = new_modes & ~prior_modes
    exited = ~new_modes & prior_modes

    submitted = actions.astype(np.float32, copy=True)
    active = np.flatnonzero(new_modes)
    for index in active:
        vector = vectors[index]
        distance = float(distances[index])
        if distance <= DOCKING_RADIUS_M:
            submitted[index] = np.asarray((0.0, 0.0, 0.0, 1.0), dtype=np.float32)
            continue
        duration = max(
            1.0,
            float(np.linalg.norm(vector[:2])) / HORIZONTAL_SPEED_MPS,
            abs(float(vector[2])) / VERTICAL_SPEED_MPS,
        )
        velocity = vector / duration
        submitted[index] = np.asarray(
            (
                velocity[0] / HORIZONTAL_SPEED_MPS,
                velocity[1] / HORIZONTAL_SPEED_MPS,
                velocity[2] / VERTICAL_SPEED_MPS,
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
