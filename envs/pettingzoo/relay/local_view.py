"""Shared pure local-view queries for UAV relay environments."""

import numpy as np


def _update_observations_dict(self, observations_dict):
    """Return the observation dictionary without adding redundant hop data."""
    return observations_dict


def _get_local_users(self, agent_idx):
    """Return in-range users sorted by distance as ``(index, SINR)`` pairs."""
    local_users_within_radius = []
    own_pos = self.uav_positions[agent_idx]

    for user_idx in range(self.n_users):
        user_pos = self.user_positions[user_idx]
        dist = np.linalg.norm(own_pos - user_pos)

        if dist <= self.observation_radius:
            sinr_db = self._compute_sinr(agent_idx, user_idx)
            local_users_within_radius.append((user_idx, dist, sinr_db))

    local_users_within_radius.sort(key=lambda x: x[1])
    return [(idx, sinr) for idx, dist, sinr in local_users_within_radius]


def _get_local_uavs(self, agent_idx):
    """Return in-range peer UAVs sorted by distance as ``(index, SINR)`` pairs."""
    local_uavs_within_radius = []
    own_pos = self.uav_positions[agent_idx]

    for other_idx in range(self.n_uavs):
        if other_idx == agent_idx:
            continue

        other_pos = self.uav_positions[other_idx]
        dist = np.linalg.norm(own_pos - other_pos)

        if dist <= self.observation_radius:
            sinr_db = self._compute_uav_to_uav_sinr(agent_idx, other_idx)
            local_uavs_within_radius.append((other_idx, dist, sinr_db))

    local_uavs_within_radius.sort(key=lambda x: x[1])
    return [(idx, sinr) for idx, dist, sinr in local_uavs_within_radius]


def _get_local_bs(self, agent_idx):
    """Return in-range ground base stations sorted by distance."""
    local_bs_within_radius = []
    own_pos = self.uav_positions[agent_idx]

    for bs_idx in range(self.n_ground_bs):
        bs_pos = self.ground_bs_positions[bs_idx]
        dist = np.linalg.norm(own_pos - bs_pos)

        if dist <= self.observation_radius:
            local_bs_within_radius.append((bs_idx, dist))

    local_bs_within_radius.sort(key=lambda x: x[1])
    return local_bs_within_radius
