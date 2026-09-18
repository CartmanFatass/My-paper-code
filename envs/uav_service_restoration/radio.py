"""Parameterized wireless link model for ``uav_service_restoration_v0``.

Every function here is pure: same inputs, same outputs, no state, no RNG, no I/O.

Model family, stated in full because a code comment saying "standard" establishes
nothing:

    PL(d) [dB] = reference_loss_db
                 + 10 * path_loss_exponent * log10(max(d, d0) / d0)
                 + extra_loss_db

    N  [dBm]   = noise_density_dbm_per_hz + 10 * log10(bandwidth_hz) + noise_figure_db
    SNR [dB]   = tx_power_dbm + antenna_gain_db - PL(d) - N
    C  [Mbps]  = spectral_efficiency * bandwidth_hz * log2(1 + SNR_linear) / 1e6

There is no fast fading, no shadowing realisation, no interference term and no
standards-compliant resource grid.  ``spectral_efficiency`` is an assumed implementation
loss.  This is a deterministic geometric benchmark, not a cellular physical layer.

Linear power ratios are computed in watts; bandwidth is in Hz; capacities are reported in
Mbps.  Computation is float64 throughout.
"""

from __future__ import annotations

import numpy as np

from .config import RadioModelConfig

#: Distances below this many metres are treated as the reference distance.
_MIN_DISTANCE_EPS_M = 1e-9


def dbm_to_watt(dbm: np.ndarray | float) -> np.ndarray:
    """Convert dBm to watts."""

    return np.power(10.0, (np.asarray(dbm, dtype=np.float64) - 30.0) / 10.0)


def watt_to_dbm(watt: np.ndarray | float) -> np.ndarray:
    """Convert watts to dBm."""

    value = np.asarray(watt, dtype=np.float64)
    return 10.0 * np.log10(np.maximum(value, np.finfo(np.float64).tiny)) + 30.0


def db_to_linear(db: np.ndarray | float) -> np.ndarray:
    """Convert a dB power ratio to a linear ratio."""

    return np.power(10.0, np.asarray(db, dtype=np.float64) / 10.0)


def linear_to_db(linear: np.ndarray | float) -> np.ndarray:
    """Convert a linear power ratio to dB."""

    value = np.asarray(linear, dtype=np.float64)
    return 10.0 * np.log10(np.maximum(value, np.finfo(np.float64).tiny))


def noise_power_dbm(model: RadioModelConfig) -> float:
    """Thermal noise floor over the link's bandwidth, including the noise figure."""

    return float(
        model.noise_density_dbm_per_hz
        + 10.0 * np.log10(float(model.bandwidth_hz))
        + model.noise_figure_db
    )


def path_loss_db(distance_m: np.ndarray | float, model: RadioModelConfig) -> np.ndarray:
    """Log-distance path loss in dB, clamped below at the reference distance."""

    distance = np.asarray(distance_m, dtype=np.float64)
    d0 = float(model.reference_distance_m)
    effective = np.maximum(np.maximum(distance, d0), _MIN_DISTANCE_EPS_M)
    return (
        float(model.reference_loss_db)
        + 10.0 * float(model.path_loss_exponent) * np.log10(effective / d0)
        + float(model.extra_loss_db)
    )


def snr_db(distance_m: np.ndarray | float, model: RadioModelConfig) -> np.ndarray:
    """Signal-to-noise ratio in dB at the given separation."""

    return (
        float(model.tx_power_dbm)
        + float(model.antenna_gain_db)
        - path_loss_db(distance_m, model)
        - noise_power_dbm(model)
    )


def capacity_mbps(distance_m: np.ndarray | float, model: RadioModelConfig) -> np.ndarray:
    """Shannon capacity with an assumed efficiency factor, in Mbps.

    Returns exactly 0.0 beyond ``max_range_m`` or below ``min_snr_db``: a link that is out
    of range or below the usable SNR floor carries nothing, rather than an arbitrarily
    small trickle.
    """

    distance = np.asarray(distance_m, dtype=np.float64)
    snr = snr_db(distance, model)
    snr_linear = db_to_linear(snr)
    raw = (
        float(model.spectral_efficiency)
        * float(model.bandwidth_hz)
        * np.log2(1.0 + snr_linear)
        / 1.0e6
    )
    usable = (distance <= float(model.max_range_m)) & (snr >= float(model.min_snr_db))
    return np.where(usable, raw, 0.0)


def link_budget(
    distance_m: np.ndarray | float, model: RadioModelConfig
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(capacity_mbps, snr_db)`` in one pass."""

    snr = snr_db(distance_m, model)
    return capacity_mbps(distance_m, model), snr


def euclidean_distance_m(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise 3-D distances between ``a`` [..., 3] and ``b`` [..., 3]."""

    left = np.asarray(a, dtype=np.float64)
    right = np.asarray(b, dtype=np.float64)
    return np.sqrt(np.sum((left - right) ** 2, axis=-1))


def pairwise_distance_matrix_m(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distance matrix of shape ``[len(a), len(b)]`` between two position arrays."""

    left = np.asarray(a, dtype=np.float64).reshape(-1, 3)
    right = np.asarray(b, dtype=np.float64).reshape(-1, 3)
    if left.size == 0 or right.size == 0:
        return np.zeros((left.shape[0], right.shape[0]), dtype=np.float64)
    diff = left[:, None, :] - right[None, :, :]
    return np.sqrt(np.sum(diff**2, axis=-1))
