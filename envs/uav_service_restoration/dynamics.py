"""UAV kinematics for ``uav_service_restoration_v0``.

Actions are three normalised velocity requests per UAV.  The speed limit is applied to the
**vector norm**, not per axis, so a request of ``(1, 1, 1)`` does not travel at
``sqrt(3) * max_speed`` diagonally.

Motion is integrated over physical substeps.  A UAV is never teleported to the end of a
decision interval before its service is evaluated.

``motion_effort`` is the mean squared speed relative to the speed limit - a dimensionless
proxy.  It is **not** electrical energy.  There is no battery, hover-power, endurance or
return-to-base model in v0, so energy fields are reported as unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import DynamicsConfig, RegionConfig

ACTION_DIM = 3


@dataclass(frozen=True)
class MotionResult:
    positions_m: np.ndarray
    velocities_mps: np.ndarray
    distance_m: np.ndarray
    motion_effort: float
    clipped: np.ndarray


def clamp_actions(actions: np.ndarray) -> np.ndarray:
    """Clamp each request to the unit ball; the norm, not the axes, is limited."""

    requested = np.asarray(actions, dtype=np.float64).reshape(-1, ACTION_DIM)
    if not np.isfinite(requested).all():
        raise ValueError("velocity requests must be finite")
    norms = np.linalg.norm(requested, axis=1, keepdims=True)
    scale = np.where(norms > 1.0, 1.0 / np.maximum(norms, 1e-12), 1.0)
    return requested * scale


def requested_velocity_mps(actions: np.ndarray, dynamics: DynamicsConfig) -> np.ndarray:
    """Map normalised requests to metres per second under the vector-norm speed limit."""

    return clamp_actions(actions) * float(dynamics.max_speed_mps)


def advance(
    positions_m: np.ndarray,
    velocities_mps: np.ndarray,
    dt_s: float,
    dynamics: DynamicsConfig,
    region: RegionConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Advance one physical substep and enforce the geographic and altitude box.

    Returns ``(positions, realised_velocities, clipped_mask)``.  When a boundary clips an
    axis, that axis's realised velocity becomes the achieved displacement over ``dt_s``,
    so reported velocity always matches reported motion.
    """

    position = np.asarray(positions_m, dtype=np.float64).reshape(-1, 3)
    velocity = np.asarray(velocities_mps, dtype=np.float64).reshape(-1, 3)
    dt = float(dt_s)
    if dt < 0.0:
        raise ValueError("dt_s must be non-negative")

    margin = float(dynamics.bounds_margin_m)
    low = np.array(
        [
            float(region.min_xy_m[0]) + margin,
            float(region.min_xy_m[1]) + margin,
            float(dynamics.altitude_range_m[0]),
        ],
        dtype=np.float64,
    )
    high = np.array(
        [
            float(region.max_xy_m[0]) - margin,
            float(region.max_xy_m[1]) - margin,
            float(dynamics.altitude_range_m[1]),
        ],
        dtype=np.float64,
    )
    if (low > high).any():
        raise ValueError("dynamics.bounds_margin_m leaves an empty flight box")

    proposed = position + velocity * dt
    clamped = np.clip(proposed, low[None, :], high[None, :])
    clipped = ~np.isclose(clamped, proposed, rtol=0.0, atol=1e-12)
    realised = (clamped - position) / dt if dt > 0.0 else np.zeros_like(velocity)
    return clamped, realised, clipped


def motion_effort(velocities_mps: np.ndarray, dynamics: DynamicsConfig) -> float:
    """Mean squared speed relative to the speed limit; dimensionless, not energy."""

    velocity = np.asarray(velocities_mps, dtype=np.float64).reshape(-1, 3)
    if velocity.shape[0] == 0:
        return 0.0
    speed = np.linalg.norm(velocity, axis=1)
    ratio = speed / float(dynamics.max_speed_mps)
    return float(np.mean(ratio**2))


def min_pairwise_separation_m(positions_m: np.ndarray) -> float:
    """Smallest UAV-to-UAV distance; ``inf`` for fewer than two UAVs.

    Recorded for diagnostics only.  v0 implements no collision avoidance and therefore
    claims no safe-flight guarantee.
    """

    position = np.asarray(positions_m, dtype=np.float64).reshape(-1, 3)
    n = position.shape[0]
    if n < 2:
        return float("inf")
    diff = position[:, None, :] - position[None, :, :]
    distance = np.sqrt(np.sum(diff**2, axis=-1))
    np.fill_diagonal(distance, np.inf)
    return float(np.min(distance))


def valid_initial_positions(
    positions_m: np.ndarray, dynamics: DynamicsConfig, region: RegionConfig
) -> bool:
    """True when every position is inside the geographic box and altitude range."""

    position = np.asarray(positions_m, dtype=np.float64).reshape(-1, 3)
    inside_xy = (
        (position[:, 0] >= float(region.min_xy_m[0]) - 1e-9)
        & (position[:, 0] <= float(region.max_xy_m[0]) + 1e-9)
        & (position[:, 1] >= float(region.min_xy_m[1]) - 1e-9)
        & (position[:, 1] <= float(region.max_xy_m[1]) + 1e-9)
    )
    inside_z = (position[:, 2] >= float(dynamics.altitude_range_m[0]) - 1e-9) & (
        position[:, 2] <= float(dynamics.altitude_range_m[1]) + 1e-9
    )
    return bool(np.all(inside_xy & inside_z))
