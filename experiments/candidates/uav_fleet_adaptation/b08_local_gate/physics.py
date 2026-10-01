"""Independent scalar arithmetic for every saved N5 radio/assignment state.

This module intentionally imports no environment, native radio kernel or
candidate controller. It reconstructs the fixed free-space physics from
coordinates and the applied transmitter mask, including stable tie order.
"""
import math

import numpy as np


LOSS_OFFSET = 20. * math.log10(4. * math.pi / .15)
NOISE = 10. ** (-80. / 10.)


def _loss(first, second):
    dx = float(first[0]) - float(second[0])
    dy = float(first[1]) - float(second[1])
    dz = float(first[2]) - float(second[2])
    distance = max(math.sqrt(dx * dx + dy * dy + dz * dz), 1e-6)
    return 20. * math.log10(distance) + LOSS_OFFSET


def _denominator(interference):
    if interference <= 0.:
        return -80.
    # Preserve the host's explicit dBm round trip rather than simplifying it.
    dbm = 10. * math.log10(interference)
    return 10. * math.log10(NOISE + 10. ** (dbm / 10.))


def assignment(sinr):
    values = np.asarray(sinr, dtype=np.float64)
    if values.shape != (5, 50) or np.isnan(values).any() or np.isposinf(values).any():
        raise ValueError("finite-or-silent N5/U50 SINR matrix required")
    choices = [(i, j, float(values[i, j])) for i in range(5) for j in range(50)
               if values[i, j] >= 3.]
    choices.sort(key=lambda item: -item[2])  # Stable original row-major ties.
    counts, used = [0] * 5, [False] * 50
    result = np.zeros((5, 50), dtype=bool)
    for i, j, _ in choices:
        if counts[i] < 10 and not used[j]:
            result[i, j] = True
            counts[i] += 1
            used[j] = True
    return result


def observations(positions, users, sinr, peer, tick, horizon):
    result = np.zeros((5, 104), dtype=np.float32)
    for i in range(5):
        x, y, z = map(float, positions[i])
        result[i, :3] = (x / 1000., y / 1000., (z - 50.) / 100.)
        visible = [j for j in range(50) if sinr[i, j] >= 3.]
        visible.sort(key=lambda j: -sinr[i, j])
        for slot, j in enumerate(visible[:20]):
            result[i, 3 + 3 * slot:6 + 3 * slot] = (
                (float(users[j, 0]) - x) / 1000., (float(users[j, 1]) - y) / 1000.,
                min(1., max(0., (float(sinr[i, j]) + 10.) / 50.)))
        neighbors = [j for j in range(5) if j != i and peer[i, j] >= 3.]
        neighbors.sort(key=lambda j: -peer[i, j])
        for slot, j in enumerate(neighbors):
            result[i, 63 + 4 * slot:67 + 4 * slot] = (
                (float(positions[j, 0]) - x) / 1000.,
                (float(positions[j, 1]) - y) / 1000.,
                (float(positions[j, 2]) - z) / 100.,
                min(1., max(0., (float(peer[i, j]) + 10.) / 50.)))
        result[i, -1] = tick / horizon
    return result


def scalar_state(positions, users, mask, tick, horizon=256, *, counts=None):
    positions, users = np.asarray(positions, dtype=np.float64), np.asarray(users, dtype=np.float64)
    mask = np.asarray(mask)
    if (positions.shape != (5, 3) or users.shape != (50, 2)
            or not np.isfinite(positions).all() or not np.isfinite(users).all()
            or mask.shape != (5,) or mask.dtype != np.dtype(bool)
            or not 0 <= tick <= horizon):
        raise ValueError("invalid independent scalar state")
    user_loss = np.empty((5, 50), dtype=np.float64)
    user_power = np.empty((5, 50), dtype=np.float64)
    for i in range(5):
        for j in range(50):
            user_loss[i, j] = _loss(positions[i], (users[j, 0], users[j, 1], 0.))
            user_power[i, j] = 10. ** ((23. - user_loss[i, j]) / 10.)
    peer_loss = np.zeros((5, 5), dtype=np.float64)
    for i in range(5):
        for j in range(i + 1, 5):
            peer_loss[i, j] = peer_loss[j, i] = _loss(positions[i], positions[j])
    peer_power = np.zeros((5, 5), dtype=np.float64)
    for i in range(5):
        for j in range(5):
            if i != j:
                peer_power[i, j] = 10. ** ((23. - peer_loss[i, j]) / 10.)
    sinr = np.full((5, 50), -np.inf, dtype=np.float64)
    peer = np.full((5, 5), -np.inf, dtype=np.float64)
    for i in range(5):
        if not mask[i]:
            continue
        for j in range(50):
            interference = 0.
            for k in range(5):
                if k != i and mask[k]:
                    interference += float(user_power[k, j])
            sinr[i, j] = 23. - user_loss[i, j] - _denominator(interference)
        for j in range(5):
            if not mask[j]:
                continue
            interference = 0.
            for k in range(5):
                if k != i and k != j and mask[k]:
                    interference += float(peer_power[k, j])
            peer[i, j] = 23. - peer_loss[i, j] - _denominator(interference)
    connected = assignment(sinr)
    served, quality_sum = 0, 0.
    for i in range(5):
        for j in range(50):
            if connected[i, j]:
                served += 1
                quality_sum += min(1., max(0., (float(sinr[i, j]) - 3.) / 30.))
    quality = quality_sum / max(served, 1)
    reward = .7 * (served / 50) + .3 * quality
    rows = observations(positions, users, sinr, peer, tick, horizon)
    if counts is not None:
        increments = dict(scalar_states=1, user_distance_links=250, peer_distance_pairs=10,
                          scalar_user_sinrs=int(mask.sum()) * 50,
                          scalar_peer_sinrs=int(mask.sum()) ** 2,
                          logical_dense_sinr_slots=275, observation_rows=5,
                          assignments=1)
        for key, value in increments.items():
            counts[key] = counts.get(key, 0) + value
    return dict(sinr=sinr, peer_sinr=peer, connections=connected, observations=rows,
                reward=reward, served=served, sinr_quality=quality)


def assert_radio_equal(actual, expected, *, tolerance=1e-10):
    """Finite scalar/vector rounding is allowed; silent/eligibility bits are exact."""
    left, right = np.asarray(actual), np.asarray(expected)
    if (left.shape != right.shape or np.isnan(left).any() or np.isnan(right).any()
            or not np.array_equal(np.isneginf(left), np.isneginf(right))
            or np.isposinf(left).any() or np.isposinf(right).any()):
        raise AssertionError("radio shape/nonfinite identity changed")
    finite = np.isfinite(right)
    difference = float(np.max(np.abs(left[finite] - right[finite]), initial=0.))
    if difference > tolerance or not np.array_equal(left >= 3., right >= 3.):
        raise AssertionError(f"scalar radio mismatch, max={difference}")
    return difference
