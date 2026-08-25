"""Topology-conditioned role probes for HA-CTSE.

The role target is not the skill id.  It is a topology counterfactual pseudo
label derived from each UAV's marginal contribution to backhaul connectivity
and direct service during a completed skill segment.  The discriminator then
tests whether segment behavior and OPT context explain that role better than
context/duration/reward shortcuts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


TOPOLOGY_ROLE_NAMES = ("idle", "relay", "service", "relay_service")

TOPOLOGY_ROLE_FIELDS = (
    "cf_backhaul_start",
    "cf_backhaul_mean",
    "cf_backhaul_max",
    "cf_backhaul_delta",
    "cf_components_start",
    "cf_components_mean",
    "cf_components_max",
    "cf_components_delta",
    "cf_disconnect_start",
    "cf_disconnect_mean",
    "cf_disconnect_max",
    "cf_disconnect_delta",
    "service_start",
    "service_mean",
    "service_max",
    "service_delta",
    "coverage_delta",
    "qos_delta",
    "battery_start",
    "battery_delta",
    "length_log",
)


def _mlp(input_dim: int, hidden_dim: int, output_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(input_dim),
        nn.Linear(input_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, hidden_dim),
        nn.GELU(),
        nn.Linear(hidden_dim, output_dim),
    )


def _as_array(value) -> np.ndarray | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value)
    except (TypeError, ValueError):
        return None
    if arr.size == 0:
        return None
    return arr


def _safe_float(value, default: float = 0.0) -> float:
    try:
        scalar = float(np.asarray(value, dtype=np.float64).mean())
    except (TypeError, ValueError, FloatingPointError):
        return float(default)
    return scalar if np.isfinite(scalar) else float(default)


def _metric_series(segment, aliases: tuple[str, ...]) -> list[float]:
    values: list[float] = []
    for info in getattr(segment, "reward_info_seq", []):
        if not isinstance(info, dict):
            continue
        for key in aliases:
            if key in info:
                values.append(_safe_float(info.get(key)))
                break
    return values


def _series_delta(segment, aliases: tuple[str, ...]) -> float:
    values = _metric_series(segment, aliases)
    if len(values) < 2:
        return 0.0
    return float(values[-1] - values[0])


def _count_components(adj: np.ndarray, active_nodes: np.ndarray) -> int:
    active = [int(node) for node in active_nodes if 0 <= int(node) < adj.shape[0]]
    if not active:
        return 0
    active_set = set(active)
    seen: set[int] = set()
    components = 0
    for start in active:
        if start in seen:
            continue
        components += 1
        stack = [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            neighbors = np.flatnonzero(adj[node] > 0)
            for neighbor in neighbors:
                neighbor = int(neighbor)
                if neighbor in active_set and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
    return int(components)


def _reachable_uavs_from_bs(adj: np.ndarray, n_uavs: int, n_bs: int, active_uavs: np.ndarray) -> set[int]:
    if n_bs <= 0:
        return set()
    active_uav_set = {int(node) for node in active_uavs}
    seen = set(range(n_uavs, n_uavs + n_bs))
    stack = list(seen)
    connected: set[int] = set()
    while stack:
        node = stack.pop()
        for neighbor in np.flatnonzero(adj[node] > 0):
            neighbor = int(neighbor)
            if neighbor in seen:
                continue
            seen.add(neighbor)
            stack.append(neighbor)
            if neighbor in active_uav_set:
                connected.add(neighbor)
    return connected


def _connected_uavs_from_bs(adj: np.ndarray, n_uavs: int, n_bs: int, active_uavs: np.ndarray) -> int:
    return int(len(_reachable_uavs_from_bs(adj, n_uavs, n_bs, active_uavs)))


@dataclass
class TopologyRoleSample:
    features: np.ndarray
    label: int
    available: bool
    role_scores: np.ndarray


class TopologyRoleExtractor:
    """Derive role pseudo labels from graph-removal marginal contributions."""

    feature_names = TOPOLOGY_ROLE_FIELDS
    role_names = TOPOLOGY_ROLE_NAMES

    def __init__(self, n_agents: int, min_score: float = 1e-6):
        self.n_agents = int(max(n_agents, 1))
        self.min_score = float(max(min_score, 0.0))

    @property
    def num_features(self) -> int:
        return len(self.feature_names)

    @property
    def num_roles(self) -> int:
        return len(self.role_names)

    def _service_score(self, state_info: dict, agent_id: int) -> tuple[float, bool]:
        connections = _as_array(state_info.get("connections"))
        if connections is None or connections.ndim != 2:
            return 0.0, False
        arr = connections.astype(bool)
        if arr.shape[0] == self.n_agents and 0 <= agent_id < arr.shape[0]:
            served = int(np.count_nonzero(arr[agent_id]))
            denom = max(arr.shape[1], 1)
            return float(served / denom), True
        if arr.shape[1] == self.n_agents and 0 <= agent_id < arr.shape[1]:
            served = int(np.count_nonzero(arr[:, agent_id]))
            denom = max(arr.shape[0], 1)
            return float(served / denom), True
        return 0.0, False

    def _graph_scores(self, state_info: dict, agent_id: int) -> tuple[dict[str, float], bool]:
        uav_conn = _as_array(state_info.get("uav_connections"))
        uav_bs_conn = _as_array(state_info.get("uav_bs_connections"))
        if uav_conn is None or uav_bs_conn is None or uav_conn.ndim != 2 or uav_bs_conn.ndim != 2:
            return {
                "cf_backhaul": 0.0,
                "cf_components": 0.0,
                "cf_disconnect": 0.0,
            }, False
        n_uavs = min(int(uav_conn.shape[0]), int(uav_conn.shape[1]), self.n_agents)
        if n_uavs <= 0 or agent_id < 0 or agent_id >= n_uavs:
            return {
                "cf_backhaul": 0.0,
                "cf_components": 0.0,
                "cf_disconnect": 0.0,
            }, False
        if uav_bs_conn.shape[0] >= n_uavs:
            bs_matrix = uav_bs_conn[:n_uavs]
        elif uav_bs_conn.shape[1] >= n_uavs:
            bs_matrix = uav_bs_conn.T[:n_uavs]
        else:
            bs_matrix = None
        n_bs = int(bs_matrix.shape[1]) if bs_matrix is not None and bs_matrix.ndim == 2 else 0
        if n_bs <= 0:
            return {
                "cf_backhaul": 0.0,
                "cf_components": 0.0,
                "cf_disconnect": 0.0,
            }, False

        adj = np.zeros((n_uavs + n_bs, n_uavs + n_bs), dtype=np.float32)
        uav_edges = uav_conn[:n_uavs, :n_uavs].astype(bool)
        adj[:n_uavs, :n_uavs] = np.logical_or(uav_edges, uav_edges.T).astype(np.float32)
        bs_edges = bs_matrix[:n_uavs, :n_bs].astype(bool)
        adj[:n_uavs, n_uavs:] = bs_edges.astype(np.float32)
        adj[n_uavs:, :n_uavs] = bs_edges.T.astype(np.float32)
        np.fill_diagonal(adj, 0.0)

        active_full = np.arange(n_uavs, dtype=np.int64)
        active_removed = np.asarray([idx for idx in range(n_uavs) if idx != agent_id], dtype=np.int64)
        bs_nodes = np.arange(n_uavs, n_uavs + n_bs, dtype=np.int64)
        connected_full_set = _reachable_uavs_from_bs(adj, n_uavs, n_bs, active_full)
        connected_removed_set = _reachable_uavs_from_bs(adj, n_uavs, n_bs, active_removed)
        connected_full = len(connected_full_set)
        connected_removed = len(connected_removed_set)
        own_connected = 1 if int(agent_id) in connected_full_set else 0
        components_full = _count_components(adj, np.concatenate([active_full, bs_nodes]))
        components_removed = _count_components(adj, np.concatenate([active_removed, bs_nodes]))
        disconnect_full = 1.0 if connected_full <= 0 else 0.0
        disconnect_removed = 1.0 if connected_removed <= 0 else 0.0
        return {
            "cf_backhaul": float(max(0.0, connected_full - connected_removed - own_connected)),
            "cf_components": float(max(0.0, components_removed - components_full)),
            "cf_disconnect": float(max(0.0, disconnect_removed - disconnect_full)),
        }, True

    @staticmethod
    def _summary(values: list[float]) -> tuple[float, float, float, float]:
        if not values:
            return 0.0, 0.0, 0.0, 0.0
        arr = np.asarray(values, dtype=np.float32)
        finite = arr[np.isfinite(arr)]
        if finite.size == 0:
            return 0.0, 0.0, 0.0, 0.0
        return (
            float(finite[0]),
            float(np.mean(finite)),
            float(np.max(finite)),
            float(finite[-1] - finite[0]) if finite.size > 1 else 0.0,
        )

    def extract(self, segment) -> TopologyRoleSample:
        state_infos = [
            info for info in getattr(segment, "state_info_seq", [])
            if isinstance(info, dict) and info
        ]
        agent_id = int(getattr(segment, "agent_id", 0))
        backhaul_values: list[float] = []
        component_values: list[float] = []
        disconnect_values: list[float] = []
        service_values: list[float] = []
        battery_values: list[float] = []
        graph_available = False
        service_available = False

        for state_info in state_infos:
            graph_scores, graph_ok = self._graph_scores(state_info, agent_id)
            service_score, service_ok = self._service_score(state_info, agent_id)
            graph_available = graph_available or graph_ok
            service_available = service_available or service_ok
            backhaul_values.append(graph_scores["cf_backhaul"])
            component_values.append(graph_scores["cf_components"])
            disconnect_values.append(graph_scores["cf_disconnect"])
            service_values.append(service_score)
            battery = _as_array(state_info.get("uav_battery_ratios"))
            if battery is not None and battery.size > agent_id:
                battery_values.append(_safe_float(battery.reshape(-1)[agent_id], default=1.0))

        backhaul = self._summary(backhaul_values)
        components = self._summary(component_values)
        disconnect = self._summary(disconnect_values)
        service = self._summary(service_values)
        battery = self._summary(battery_values)
        coverage_delta = _series_delta(segment, ("coverage_ratio",))
        qos_delta = _series_delta(
            segment,
            (
                "qos_satisfaction_ratio",
                "qos_met_fraction",
                "demand_satisfaction_ratio",
                "qos_satisfaction",
                "qos_score",
            ),
        )
        features = np.asarray(
            [
                *backhaul,
                *components,
                *disconnect,
                *service,
                coverage_delta,
                qos_delta,
                battery[0],
                battery[3],
                float(np.log1p(max(getattr(segment, "length", 0), 0))),
            ],
            dtype=np.float32,
        )
        if features.shape[0] != self.num_features:
            fixed = np.zeros(self.num_features, dtype=np.float32)
            fixed[: min(self.num_features, features.shape[0])] = features[: self.num_features]
            features = fixed

        relay_score = float(max(backhaul[1], backhaul[2], components[1], components[2], disconnect[1], disconnect[2]))
        service_score = float(max(service[1], service[2]))
        bridge_score = float(min(relay_score, service_score))
        idle_score = float(1.0 if relay_score <= self.min_score and service_score <= self.min_score else 0.0)
        role_scores = np.asarray([idle_score, relay_score, service_score, bridge_score], dtype=np.float32)
        available = bool(graph_available or service_available)
        if not available:
            label = 0
        elif bridge_score > self.min_score:
            label = 3
        elif relay_score > self.min_score:
            label = 1
        elif service_score > self.min_score:
            label = 2
        else:
            label = 0
        return TopologyRoleSample(features=features, label=int(label), available=available, role_scores=role_scores)


class TopologyRoleDiscriminator(nn.Module):
    """OPT-conditioned full-vs-shortcut role classifier."""

    def __init__(
        self,
        topology_feature_dim: int,
        embedding_dim: int,
        opt_context_dim: int,
        obs_dim: int,
        n_skills: int,
        num_team_codes: int,
        n_agents: int,
        num_phase_bins: int,
        num_duration_bins: int,
        hidden_dim: int,
        num_roles: int = len(TOPOLOGY_ROLE_NAMES),
    ):
        super().__init__()
        self.topology_feature_dim = int(topology_feature_dim)
        self.embedding_dim = int(embedding_dim)
        self.opt_context_dim = int(opt_context_dim)
        self.obs_dim = int(obs_dim)
        self.n_skills = int(max(n_skills, 1))
        self.num_team_codes = int(max(num_team_codes, 1))
        self.n_agents = int(max(n_agents, 1))
        self.num_phase_bins = int(max(num_phase_bins, 1))
        self.num_duration_bins = int(max(num_duration_bins, 1))
        self.num_roles = int(max(num_roles, 1))
        self.shortcut_dim = (
            self.obs_dim
            + self.opt_context_dim
            + self.num_team_codes
            + self.n_agents
            + self.num_phase_bins
            + self.num_duration_bins
            + 2
        )
        full_dim = self.topology_feature_dim + self.embedding_dim + self.n_skills + self.shortcut_dim
        self.full_head = _mlp(full_dim, hidden_dim, self.num_roles)
        self.shortcut_head = _mlp(self.shortcut_dim, hidden_dim, self.num_roles)

    @staticmethod
    def _standardize(values: torch.Tensor) -> torch.Tensor:
        values = values.float().reshape(-1, 1)
        if values.numel() <= 1:
            return torch.zeros_like(values)
        return ((values - values.mean()) / values.std(unbiased=False).clamp_min(1e-6)).clamp(-5.0, 5.0)

    def shortcut_features(
        self,
        start_obs: torch.Tensor,
        opt_context: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
    ) -> torch.Tensor:
        team = F.one_hot(team_codes.long().clamp(0, self.num_team_codes - 1), self.num_team_codes).float()
        agent = F.one_hot(agent_ids.long().clamp(0, self.n_agents - 1), self.n_agents).float()
        phase = F.one_hot(phase_bins.long().clamp(0, self.num_phase_bins - 1), self.num_phase_bins).float()
        duration = F.one_hot(durations.long().clamp(0, self.num_duration_bins - 1), self.num_duration_bins).float()
        return torch.cat(
            [
                start_obs.float(),
                opt_context.float(),
                team,
                agent,
                phase,
                duration,
                self._standardize(lengths),
                self._standardize(reward_sums),
            ],
            dim=-1,
        )

    def forward(
        self,
        topology_features: torch.Tensor,
        segment_embedding: torch.Tensor,
        labels_z: torch.Tensor,
        start_obs: torch.Tensor,
        opt_context: torch.Tensor,
        team_codes: torch.Tensor,
        agent_ids: torch.Tensor,
        phase_bins: torch.Tensor,
        durations: torch.Tensor,
        lengths: torch.Tensor,
        reward_sums: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        shortcut = self.shortcut_features(
            start_obs,
            opt_context,
            team_codes,
            agent_ids,
            phase_bins,
            durations,
            lengths,
            reward_sums,
        )
        skill = F.one_hot(labels_z.long().clamp(0, self.n_skills - 1), self.n_skills).float()
        full = torch.cat([topology_features.float(), segment_embedding.float(), skill, shortcut], dim=-1)
        return self.full_head(full), self.shortcut_head(shortcut)

    @staticmethod
    def _log_prob_for_labels(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        return F.log_softmax(logits, dim=-1)[torch.arange(labels.shape[0], device=labels.device), labels.long()]

    def losses(
        self,
        full_logits: torch.Tensor,
        shortcut_logits: torch.Tensor,
        role_labels: torch.Tensor,
        available_mask: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        mask = available_mask.float() > 0.0
        if not torch.any(mask):
            zero = torch.zeros((), device=full_logits.device, dtype=full_logits.dtype)
            zero_vec = torch.zeros(full_logits.shape[0], device=full_logits.device, dtype=full_logits.dtype)
            return {
                "full_loss": zero,
                "shortcut_loss": zero,
                "total_loss": zero,
                "full_acc": zero,
                "shortcut_acc": zero,
                "residual_gain": zero_vec,
                "residual_gain_positive_frac": zero,
                "available_frac": zero,
            }
        labels = role_labels.long().clamp(0, full_logits.shape[-1] - 1)
        full_valid = full_logits[mask]
        shortcut_valid = shortcut_logits[mask]
        labels_valid = labels[mask]
        full_loss = F.cross_entropy(full_valid, labels_valid)
        shortcut_loss = F.cross_entropy(shortcut_valid, labels_valid)
        log_full = self._log_prob_for_labels(full_logits, labels)
        log_shortcut = self._log_prob_for_labels(shortcut_logits, labels)
        gain = log_full - log_shortcut
        gain_valid = gain[mask]
        with torch.no_grad():
            full_acc = (full_valid.argmax(dim=-1) == labels_valid).float().mean()
            shortcut_acc = (shortcut_valid.argmax(dim=-1) == labels_valid).float().mean()
            positive_frac = (gain_valid > 0.0).float().mean()
            available_frac = mask.float().mean()
        return {
            "full_loss": full_loss,
            "shortcut_loss": shortcut_loss,
            "total_loss": full_loss + shortcut_loss,
            "full_acc": full_acc,
            "shortcut_acc": shortcut_acc,
            "residual_gain": gain,
            "residual_gain_positive_frac": positive_frac,
            "available_frac": available_frac,
        }


def empty_topology_role_metrics() -> dict[str, float]:
    metrics = {
        "topology_role_samples": 0.0,
        "topology_role_available_frac": 0.0,
        "topology_role_loss": 0.0,
        "topology_role_full_loss": 0.0,
        "topology_role_shortcut_loss": 0.0,
        "topology_role_acc": 0.0,
        "topology_role_shortcut_acc": 0.0,
        "topology_role_resid_gain_mean": 0.0,
        "topology_role_resid_gain_positive_frac": 0.0,
        "topology_role_reward_mean": 0.0,
        "topology_role_reward_active": 0.0,
        "topology_role_reward_unclipped_mean": 0.0,
        "topology_role_z_mi": 0.0,
        "topology_role_g_mi": 0.0,
    }
    for role in TOPOLOGY_ROLE_NAMES:
        metrics[f"topology_role_frac_{role}"] = 0.0
    for field in TOPOLOGY_ROLE_FIELDS:
        metrics[f"topology_{field}_mean"] = 0.0
    return metrics
