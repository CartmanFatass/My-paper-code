"""D4 transforms for the fixed S7-S2 observation, state, and action contract.

The transform acts on horizontal positions about the square map center and on
horizontal displacement/velocity vectors about the origin. Entity slots and
agent identities retain their native order.
"""

from __future__ import annotations

from enum import IntEnum

import numpy as np

from experiments.candidates.energy_relay_benchmark.b01.observation import S7S2_LAYOUT


class D4(IntEnum):
    IDENTITY = 0
    ROT90 = 1
    ROT180 = 2
    ROT270 = 3
    MIRROR_X = 4
    MIRROR_Y = 5
    MIRROR_DIAGONAL = 6
    MIRROR_ANTI_DIAGONAL = 7

    @property
    def matrix(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return _MATRICES[self.value]

    def compose(self, other: D4) -> D4:
        """Return self after other: result(x) = self(other(x))."""
        other = get_transform(other)
        a, b = self.matrix, other.matrix
        product = tuple(
            tuple(sum(a[i][k] * b[k][j] for k in range(2)) for j in range(2))
            for i in range(2)
        )
        return D4(_MATRICES.index(product))

    def inverse(self) -> D4:
        matrix = self.matrix
        transpose = ((matrix[0][0], matrix[1][0]), (matrix[0][1], matrix[1][1]))
        return D4(_MATRICES.index(transpose))


_MATRICES = (
    ((1, 0), (0, 1)),    # identity
    ((0, -1), (1, 0)),   # counterclockwise quarter turn
    ((-1, 0), (0, -1)),  # half turn
    ((0, 1), (-1, 0)),   # clockwise quarter turn
    ((-1, 0), (0, 1)),   # reflect x about map center
    ((1, 0), (0, -1)),   # reflect y about map center
    ((0, 1), (1, 0)),    # reflect across x = y
    ((0, -1), (-1, 0)),  # reflect across x + y = 1
)

IDENTITY = D4.IDENTITY
MIRROR_X = D4.MIRROR_X
MIRROR_Y = D4.MIRROR_Y
ROT180 = D4.ROT180


def get_transform(name: D4 | str) -> D4:
    if isinstance(name, D4):
        return name
    if isinstance(name, str):
        try:
            return D4[name.upper()]
        except KeyError as exc:
            raise ValueError(f"unknown D4 transform: {name}") from exc
    raise TypeError(f"D4 transform must be a D4 or name, got {type(name).__name__}")


def _floating_copy(values, shape: tuple[int, ...], label: str) -> np.ndarray:
    array = np.asarray(values)
    if array.shape != shape:
        raise ValueError(f"{label} must have shape {shape}, got {array.shape}")
    if not np.issubdtype(array.dtype, np.floating):
        raise TypeError(f"{label} must have floating dtype, got {array.dtype}")
    return array.copy()


def _xy(values: np.ndarray, transform: D4, *, absolute: bool) -> None:
    """Transform an array view ending in xy, using only signed permutations."""
    original = values.copy()
    matrix = transform.matrix
    for axis in range(2):
        source = 0 if matrix[axis][0] else 1
        sign = matrix[axis][source]
        values[..., axis] = sign * original[..., source]
        if absolute and sign < 0:
            values[..., axis] += 1.0


def transform_observations(observations, transform: D4 | str) -> np.ndarray:
    """Transform the eight legal per-UAV S7-S2 observations (8, 365)."""
    transform = get_transform(transform)
    layout = S7S2_LAYOUT
    result = _floating_copy(observations, (layout.n_uavs, layout.dim), "observations")
    _xy(result[:, layout.own.start : layout.own.start + 2], transform, absolute=True)
    _xy(result[:, layout.nearest_uav.start + 1 : layout.nearest_uav.stop], transform, absolute=False)
    _xy(result[:, layout.self_state.stop - 2 : layout.self_state.stop], transform, absolute=False)
    for section, slots, fields in (
        (layout.users, layout.user_slots, layout.user_fields),
        (layout.uavs, layout.uav_slots, layout.uav_fields),
        (layout.bs, layout.bs_slots, layout.bs_fields),
        (layout.overloaded, layout.overloaded_slots, layout.overloaded_fields),
        (layout.energy_uavs, layout.energy_uav_records, layout.energy_uav_fields),
        (layout.energy_stations, layout.energy_station_records, layout.energy_station_fields),
    ):
        records = result[:, section].reshape(layout.n_uavs, slots, fields)
        _xy(records[..., :2], transform, absolute=False)
    return result


def transform_state(state, transform: D4 | str) -> np.ndarray:
    """Transform the native S7-S2 state; preserve all scalar and z fields."""
    transform = get_transform(transform)
    layout = S7S2_LAYOUT
    n_uavs, n_users = layout.n_uavs, layout.n_users
    # Native routed state: UAV xyz, UAV loads, user (xy, velocity xy, two
    # scalars), one BS xyz, step. Energy adds UAV x 9, stations x 7, stage x 4.
    uav_end = n_uavs * 3
    user_start = uav_end + n_uavs
    user_end = user_start + n_users * 6
    bs_end = user_end + 3
    station_start = bs_end + 1 + n_uavs * 9
    state_dim = station_start + layout.energy_station_records * 7 + 4
    result = _floating_copy(state, (state_dim,), "state")
    _xy(result[:uav_end].reshape(n_uavs, 3)[:, :2], transform, absolute=True)
    users = result[user_start:user_end].reshape(n_users, 6)
    _xy(users[:, :2], transform, absolute=True)
    _xy(users[:, 2:4], transform, absolute=False)
    _xy(result[user_end:bs_end][:2], transform, absolute=True)
    stations = result[station_start:station_start + layout.energy_station_records * 7].reshape(
        layout.energy_station_records, 7
    )
    _xy(stations[:, :2], transform, absolute=True)
    return result


def transform_actions(actions, transform: D4 | str) -> np.ndarray:
    """Map normalized Cartesian action xy into a D4 frame; keep z and dock."""
    transform = get_transform(transform)
    result = _floating_copy(actions, (S7S2_LAYOUT.n_uavs, 4), "actions")
    _xy(result[:, :2], transform, absolute=False)
    return result


def inverse_actions(actions, transform: D4 | str) -> np.ndarray:
    """Map frame actions back to the original world coordinates."""
    return transform_actions(actions, get_transform(transform).inverse())
