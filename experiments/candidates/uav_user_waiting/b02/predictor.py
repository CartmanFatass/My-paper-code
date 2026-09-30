"""Lawful synthetic native-format observations and reported-state C clones."""

import numpy as np

from envs.pettingzoo.uav_radio import free_space_user_path_loss, user_sinr_from_path_loss
from experiments.candidates.uav_local_history.b01.controller import LocalController
from .protocol import HIGH, LOW, N, U, mask_array


def controller_nav_index(controller):
    """A local sender serializes its own state after its current C call."""
    value = controller._nav_index
    if not isinstance(value, (int, np.integer)) or not 0 <= value < 10:
        raise ValueError('C must have a post-call waypoint index')
    return int(value)


def clone_controller(nav_index):
    if not isinstance(nav_index, (int, np.integer)) or not 0 <= nav_index < 10:
        raise ValueError('invalid decoded C waypoint index')
    clone = LocalController(history=False)
    clone._nav_index = int(nav_index)
    return clone


def synthetic_observations(positions, sites, mask, tick, *, horizon=256):
    """Mirror native eligibility, stable SINR order, truncation and float32 layout.

    User visibility is SINR eligibility (up to20), not greedy capacity assignment.
    Peer SINR is sender-to-receiver, excluding both endpoints from interference.
    """
    positions, sites = np.asarray(positions, dtype=np.float64), np.asarray(sites, dtype=np.float64)
    if positions.shape != (N, 3) or sites.shape != (U, 2) or not np.isfinite(positions).all() or not np.isfinite(sites).all():
        raise ValueError('invalid decoded model geometry')
    if np.any(positions < LOW) or np.any(positions > HIGH) or not 0 <= tick < horizon:
        raise ValueError('invalid synthetic observation clock or bounds')
    active = mask_array(mask)
    loss = free_space_user_path_loss(positions, sites)
    user_sinr = user_sinr_from_path_loss(loss, transmitter_mask=active)
    rows = np.zeros((N, 104), dtype=np.float32)
    rows[:, :3] = (positions - (0., 0., 50.)) / (1000., 1000., 100.)
    peer_links = 0
    for i in range(N):
        eligible = np.flatnonzero(user_sinr[i] >= 3.)
        eligible = eligible[np.argsort(-user_sinr[i, eligible], kind='stable')][:20]
        for slot, user in enumerate(eligible):
            rows[i, 3 + 3 * slot:6 + 3 * slot] = (
                *(sites[user] - positions[i, :2]) / 1000.,
                np.clip((user_sinr[i, user] + 10.) / 50., 0., 1.))
        peers = []
        if active[i]:
            for j in range(N):
                if i == j or not active[j]:
                    continue
                distance = max(float(np.linalg.norm(positions[i] - positions[j])), 1e-6)
                received = 23. - (20. * np.log10(distance) + 20. * np.log10(4. * np.pi / .15))
                peer_links += 1
                interfering = []
                for k in range(N):
                    if k == i or k == j or not active[k]:
                        continue
                    distance = max(float(np.linalg.norm(positions[k] - positions[j])), 1e-6)
                    loss = 20. * np.log10(distance) + 20. * np.log10(4. * np.pi / .15)
                    interfering.append(10. ** ((23. - loss) / 10.))
                    peer_links += 1
                total = np.sum(interfering) if interfering else 0.
                interference_dbm = 10. * np.log10(total) if total > 0 else -np.inf
                denominator = 10. * np.log10(1e-8 + 10. ** (interference_dbm / 10.)) if total > 0 else -80.
                value = received - denominator
                if value >= 3.:
                    peers.append((j, value))
        peers.sort(key=lambda pair: -pair[1])
        for slot, (j, value) in enumerate(peers[:10]):
            rows[i, 63 + 4 * slot:67 + 4 * slot] = (
                *((positions[j] - positions[i]) / (1000., 1000., 100.)),
                np.clip((value + 10.) / 50., 0., 1.))
    rows[:, -1] = tick / horizon
    return rows, {'observation_user_links': N * U, 'observation_peer_links': peer_links}
