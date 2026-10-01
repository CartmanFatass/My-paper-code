"""Exact native radio arithmetic batched over conditional RF trajectories."""

from __future__ import annotations

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss
from . import contract as c
from .protocol import LOW, HIGH, mask_array, require


def move(position, command):
    before = np.asarray(position, dtype=np.float64)
    after = np.clip(before + np.asarray(command, dtype=np.float64) * c.COMPONENT_METRES,
                    LOW, HIGH)
    displacement = np.sqrt(np.sum((after - before) ** 2, axis=-1))
    rho = np.exp(-displacement / c.CORRELATION_METRES)
    return after, rho


def moments_step(mean, variance, rho):
    coefficient = np.asarray(rho, dtype=np.float64)[:, None]
    square = coefficient * coefficient
    return coefficient * mean, square * variance + c.SIGMA_DB ** 2 * (1.0 - square)


def particles_step(residual, rho, innovation):
    coefficient = np.asarray(rho, dtype=np.float64)[None, :, None]
    scale = c.SIGMA_DB * np.sqrt(np.maximum(0.0, 1.0 - coefficient * coefficient))
    return coefficient * residual + scale * innovation


def expected_loss(nominal, mean, variance):
    """Convert the stated analytic expected power to the native loss interface."""
    a = np.log(10.0) / 10.0
    expected = 10.0 ** ((c.TRANSMIT_DBM - nominal) / 10.0)
    expected = expected * np.exp(-a * mean + 0.5 * a * a * variance)
    return c.TRANSMIT_DBM - 10.0 * np.log10(expected)


def native_batch(losses, mask):
    """Return each particle's J/served/quality, SINR and exact native grants.

    At a positive (>0 dB) SINR threshold with common interference/noise, two
    transmitters cannot both be eligible for one user. Native global stable
    greedy allocation is therefore each row's stable top-capacity eligible
    entries. This identity is checked rather than assumed for arbitrary input.
    The native dBm round trip and row-major quality accumulation are retained.
    """
    loss = np.asarray(losses, dtype=np.float64)
    require(loss.ndim == 3 and loss.shape[1:] == (c.N_UAVS, c.N_USERS)
            and np.isfinite(loss).all(), "finite particle loss matrices required")
    mask_values = mask_array(mask)
    rx = c.TRANSMIT_DBM - loss
    linear = 10.0 ** (rx / 10.0)
    linear[:, ~mask_values, :] = 0.0
    interference = np.zeros_like(loss)
    for source in range(c.N_UAVS):
        for other in range(c.N_UAVS):
            if other != source:
                interference[:, source, :] += linear[:, other, :]
    positive = interference > 0.0
    total_dbm = 10.0 * np.log10(np.where(positive, interference, 1.0))
    denominator = np.where(positive,
        10.0 * np.log10(10.0 ** (c.NOISE_DBM / 10.0) + 10.0 ** (total_dbm / 10.0)),
        c.NOISE_DBM)
    sinr = rx - denominator
    sinr[:, ~mask_values, :] = -np.inf
    eligible = sinr >= c.MIN_SINR_DB
    require(np.all(eligible.sum(axis=1) <= 1), "native SINR eligibility is not disjoint")
    order = np.argsort(-sinr, axis=-1, kind="stable")[:, :, :c.CAPACITY]
    assigned = np.zeros_like(eligible)
    np.put_along_axis(assigned, order, np.take_along_axis(eligible, order, axis=-1), axis=-1)
    served = assigned.sum(axis=(1, 2))
    quality_terms = np.where(assigned, np.clip((sinr - c.MIN_SINR_DB) / 30.0, 0.0, 1.0), 0.0)
    total = np.cumsum(quality_terms.reshape(loss.shape[0], -1), axis=1)[:, -1]
    quality = total / np.maximum(served, 1)
    native_j = 0.7 * (served / c.N_USERS) + 0.3 * quality
    return np.stack((native_j, served, quality), axis=1), sinr, assigned


def nominal_loss(positions, sites):
    return free_space_user_path_loss(positions, sites, c.CARRIER_HZ)
