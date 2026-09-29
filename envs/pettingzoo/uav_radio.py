"""Pure base-environment user radio and service calculations."""

import numpy as np


def free_space_user_path_loss(uav_positions, user_positions, carrier_frequency=2e9):
    """Return free-space path loss in dB for each UAV and ground user."""
    uav = np.asarray(uav_positions, dtype=float)
    users = np.asarray(user_positions, dtype=float)
    if uav.ndim != 2 or uav.shape[1] != 3:
        raise ValueError("uav_positions must have shape [n_uavs, 3]")
    if users.ndim != 2 or users.shape[1] not in (2, 3):
        raise ValueError("user_positions must have shape [n_users, 2 or 3]")
    user_z = users[:, 2] if users.shape[1] == 3 else np.zeros(users.shape[0], dtype=float)
    delta_x = uav[:, 0][:, None] - users[:, 0][None, :]
    delta_y = uav[:, 1][:, None] - users[:, 1][None, :]
    delta_z = uav[:, 2][:, None] - user_z[None, :]
    distance = np.sqrt(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z)
    safe_distance = np.maximum(distance, 1e-6)
    wavelength = 3e8 / carrier_frequency
    return 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)


def _checked_mask(transmitter_mask, n_uavs):
    if transmitter_mask is None:
        return np.ones(n_uavs, dtype=bool)
    mask = np.asarray(transmitter_mask)
    if mask.dtype != np.dtype(bool) or mask.shape != (n_uavs,):
        raise ValueError("transmitter_mask must be a boolean [n_uavs] array")
    return mask


def user_sinr_from_path_loss(
    path_loss, tx_power=23., noise_power=-80., use_fdma=False, transmitter_mask=None
):
    """Return user SINR in dB; silent transmitter rows are negative infinity."""
    loss = np.asarray(path_loss, dtype=float)
    if loss.ndim != 2:
        raise ValueError("path_loss must have shape [n_uavs, n_users]")
    n_uavs, n_users = loss.shape
    mask = _checked_mask(transmitter_mask, n_uavs)
    rx_power = tx_power - loss
    if use_fdma:
        sinr = rx_power - noise_power
    else:
        linear = 10 ** (rx_power / 10)
        if not np.all(mask):
            linear = linear.copy()
            linear[~mask] = 0.0
        interference = np.zeros_like(loss)
        for source in range(n_uavs):
            accumulator = np.zeros(n_users, dtype=loss.dtype)
            for other in range(n_uavs):
                if other != source:
                    accumulator += linear[other]
            interference[source] = accumulator
        noise_linear = 10 ** (noise_power / 10)
        positive = interference > 0
        safe_interference = np.where(positive, interference, 1.0)
        # Retain the scalar environment's dBm round trip for all-on parity.
        total_interference_dbm = 10 * np.log10(safe_interference)
        denominator_dbm = np.where(
            positive,
            10 * np.log10(noise_linear + 10 ** (total_interference_dbm / 10)),
            float(noise_power),
        )
        sinr = rx_power - denominator_dbm
    if not np.all(mask):
        sinr = sinr.copy()
        sinr[~mask] = -np.inf
    return sinr


def greedy_connection_assignment(sinr, min_sinr=3., max_connections=10):
    """Stable descending-SINR assignment with row-major ties and user exclusivity."""
    values = np.asarray(sinr)
    if values.ndim != 2:
        raise ValueError("sinr must have shape [n_uavs, n_users]")
    n_uavs, n_users = values.shape
    connections = np.zeros((n_uavs, n_users), dtype=bool)
    flat = values.reshape(-1)
    eligible = np.flatnonzero(flat >= min_sinr)
    if eligible.size == 0:
        return connections
    order = eligible[np.argsort(-flat[eligible], kind="stable")]
    uav_connections = [0] * n_uavs
    user_connected = [False] * n_users
    connected_total = 0
    full_uavs = 0
    for position in order.tolist():
        uav_idx = position // n_users
        user_idx = position - uav_idx * n_users
        if user_connected[user_idx] or uav_connections[uav_idx] >= max_connections:
            continue
        connections[uav_idx, user_idx] = True
        uav_connections[uav_idx] += 1
        if uav_connections[uav_idx] >= max_connections:
            full_uavs += 1
        user_connected[user_idx] = True
        connected_total += 1
        if connected_total == n_users or full_uavs == n_uavs:
            break
    return connections


def service_metrics(sinr, connections, min_sinr=3.):
    """Return the base (non-paper) global reward and its service components."""
    values = np.asarray(sinr)
    assigned = np.asarray(connections)
    if values.ndim != 2 or assigned.shape != values.shape:
        raise ValueError("sinr and connections must have matching [n_uavs, n_users] shape")
    served = np.sum(assigned)
    total_sinr = 0
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            if assigned[i, j]:
                total_sinr += np.clip((values[i, j] - min_sinr) / 30, 0, 1)
    quality = total_sinr / max(served, 1)
    J = 0.7 * (served / values.shape[1]) + 0.3 * quality
    return {"J": J, "served": served, "quality": quality}
