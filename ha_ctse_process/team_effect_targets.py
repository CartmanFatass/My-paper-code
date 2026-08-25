"""Reward-off q_D effect-target / timescale audit for HA-CTSE R23.

R23-2 showed the team discriminator q_D(Z | s_next) reads at chance even though Z now
moves the assignment xi. That does not prove q_D is useless; it may mean the current
target/timescale cannot see the Z-induced joint effect. This module compares several
q_D targets, all reward-off, to find which observation space + horizon (if any) carries
a recoverable Z signature:

    s_next                 : q_D(Z | next global state)               (HMASD-like, single step)
    joint_action_summary_H : q_D(Z | normalized joint action histogram over H steps)
    joint_effect_window_H  : q_D(Z | state[i+H] - state[i])           (Delta state over H)
    delta_omega_H          : q_D(Z | omega[i+H] - omega[i])           (OPT interaction-process)

Double-count contract (PR-1): these targets are future effect / process only. q_D must
NOT read xi (skill/duration ids, assignment probs) or the Z label as input — that is q_A's
job. This module never receives xi features. No reward is produced here; it is a probe.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


def _target_field(target: str, horizon: int | None) -> str:
    return f"{target}" if horizon is None else f"{target}_h{int(horizon)}"


# Default audit grid. s_next is single-step (not horizon-keyed); the windowed targets
# are compared across horizons. These constants define the static CSV column set.
DEFAULT_TARGETS = ("s_next", "joint_action", "joint_effect", "delta_omega")
DEFAULT_HORIZONS = (10, 20, 50)

_BASE_FIELDS = (
    "team_effect_audit_active",
    "team_effect_audit_samples",
    "q_d_best_target_acc",
)


def _target_horizon_keys(target: str, horizons: Sequence[int]) -> list[str]:
    if target == "s_next" or not horizons:
        return [target]
    return [_target_field(target, h) for h in horizons]


def _grid_fields(targets: Sequence[str], horizons: Sequence[int]) -> list[str]:
    fields: list[str] = []
    for t in targets:
        for key in _target_horizon_keys(t, horizons):
            fields += [f"q_d_acc_{key}", f"q_d_residual_gain_{key}", f"q_d_best_target_{key}"]
    return fields


TEAM_EFFECT_TARGET_METRIC_FIELDS = _BASE_FIELDS + tuple(_grid_fields(DEFAULT_TARGETS, DEFAULT_HORIZONS))


def empty_team_effect_target_metrics(
    targets: Sequence[str] = DEFAULT_TARGETS, horizons: Sequence[int] = DEFAULT_HORIZONS
) -> dict[str, float]:
    m = {k: 0.0 for k in _BASE_FIELDS}
    for key in _grid_fields(targets, horizons):
        m[key] = 0.0
    return m


def summarize_joint_actions(actions: torch.Tensor, num_actions: int) -> torch.Tensor:
    """Normalized per-boundary histogram of discrete actions across agents.

    actions: (B, n_agents) long. Returns (B, num_actions) rows summing to 1.
    """
    a = actions.long().clamp(0, int(num_actions) - 1)
    oh = F.one_hot(a, int(num_actions)).float()  # (B, n_agents, num_actions)
    return oh.mean(dim=1)


def group_env_sequences(env_ids: Iterable[int]) -> dict[int, list[int]]:
    """Group flat rollout indices by env id, preserving append (time) order."""
    seqs: dict[int, list[int]] = {}
    for idx, e in enumerate(env_ids):
        seqs.setdefault(int(e), []).append(idx)
    return seqs


def build_windows(
    env_sequences: dict[int, list[int]],
    values: np.ndarray,
    horizon: int,
    mode: str = "delta",
) -> tuple[list[int], np.ndarray]:
    """For each boundary index i that has a full H-step window within its env sequence,
    return (boundary_indices, feature). mode="delta" -> values[i+H]-values[i];
    mode="mean" -> mean of values over the window [i, i+H).

    values is indexed by the flat rollout index. Returns [] / empty if no window fits.
    """
    boundary_indices: list[int] = []
    feats: list[np.ndarray] = []
    H = int(horizon)
    for _env, seq in env_sequences.items():
        for pos in range(len(seq)):
            if pos + H < len(seq):
                i = seq[pos]
                if mode == "mean":
                    window_idx = seq[pos:pos + H]
                    feats.append(np.mean([np.asarray(values[k], dtype=np.float32) for k in window_idx], axis=0))
                else:
                    j = seq[pos + H]
                    feats.append(np.asarray(values[j], dtype=np.float32) - np.asarray(values[i], dtype=np.float32))
                boundary_indices.append(i)
    if not boundary_indices:
        return [], np.zeros((0,), dtype=np.float32)
    return boundary_indices, np.stack(feats).astype(np.float32)


def _mlp(in_dim: int, hidden: int, out_dim: int) -> nn.Sequential:
    return nn.Sequential(
        nn.LayerNorm(in_dim), nn.Linear(in_dim, hidden), nn.GELU(),
        nn.Linear(hidden, hidden), nn.GELU(), nn.Linear(hidden, out_dim),
    )


class TeamEffectTargetProbe(nn.Module):
    """One small classifier head per target; trains reward-off, reports per-target acc,
    prior-corrected residual gain, and flags the best-recovering target."""

    def __init__(self, target_dims: dict[str, int], num_team_codes: int, hidden_dim: int = 128, lr: float = 1e-3):
        super().__init__()
        self.num_team_codes = int(max(num_team_codes, 1))
        self.heads = nn.ModuleDict(
            {name: _mlp(int(dim), int(hidden_dim), self.num_team_codes) for name, dim in target_dims.items()}
        )
        self.prior_head = nn.Parameter(torch.zeros(self.num_team_codes))  # context-free prior logits
        # Optimizer is created lazily on first update so it binds to the parameters
        # AFTER the caller has moved the module to its device (.to(device)); building
        # it here would capture pre-move CPU tensors and break on CUDA.
        self._lr = float(lr)
        self.opt = None
        self._last: dict[str, dict[str, float]] = {}

    def _ensure_opt(self) -> None:
        if self.opt is None:
            self.opt = torch.optim.Adam(self.parameters(), lr=self._lr)

    def _forward_head(self, name: str, feats: torch.Tensor) -> torch.Tensor:
        return self.heads[name](feats.detach().float())

    @staticmethod
    def _as_labels_dict(labels, names) -> dict[str, torch.Tensor]:
        if isinstance(labels, dict):
            return labels
        return {name: labels for name in names}

    def update(self, feats_by_target: dict[str, torch.Tensor], labels, prior_probs: torch.Tensor) -> None:
        labels_by = self._as_labels_dict(labels, feats_by_target.keys())
        self._ensure_opt()
        self.opt.zero_grad()
        total = torch.zeros((), device=self.prior_head.device)
        for name, feats in feats_by_target.items():
            y = labels_by[name].detach().long().clamp(0, self.num_team_codes - 1)
            logits = self._forward_head(name, feats)
            total = total + F.cross_entropy(logits, y)
            prior_logits = self.prior_head.unsqueeze(0).expand(y.shape[0], -1)
            total = total + F.cross_entropy(prior_logits, y)
        total.backward()
        self.opt.step()

    @torch.no_grad()
    def evaluate(self, feats_by_target: dict[str, torch.Tensor], labels, prior_probs: torch.Tensor) -> dict[str, float]:
        labels_by = self._as_labels_dict(labels, feats_by_target.keys())
        out: dict[str, float] = {"team_effect_audit_active": 1.0}
        total_samples = 0
        best_name, best_acc = None, -1.0
        per_acc: dict[str, float] = {}
        for name, feats in feats_by_target.items():
            y = labels_by[name].detach().long().clamp(0, self.num_team_codes - 1)
            prior_logits = self.prior_head.unsqueeze(0).expand(y.shape[0], -1)
            prior_acc = float((prior_logits.argmax(-1) == y).float().mean().cpu())
            logits = self._forward_head(name, feats)
            acc = float((logits.argmax(-1) == y).float().mean().cpu())
            per_acc[name] = acc
            total_samples = max(total_samples, int(y.shape[0]))
            out[f"q_d_acc_{name}"] = acc
            out[f"q_d_residual_gain_{name}"] = acc - prior_acc
            if acc > best_acc:
                best_acc, best_name = acc, name
        for name in feats_by_target:
            out[f"q_d_best_target_{name}"] = 1.0 if name == best_name else 0.0
        out["q_d_best_target_acc"] = best_acc if best_acc >= 0.0 else 0.0
        out["team_effect_audit_samples"] = float(total_samples)
        self._last = {"acc": per_acc}
        return out
