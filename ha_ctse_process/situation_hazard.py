"""Reward-pure situation-change hazard components for Round 12 Stage 1."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Bernoulli


@dataclass
class HazardDecision:
    env_id: int
    agent_id: int
    step: int
    kappa: int
    previous_kappa: int
    changed: bool
    prev_skill: int
    skill_age: int
    action: int
    logp: float
    value: float
    reward_start: int


@dataclass
class ConservativeRenewalConfig:
    enabled: bool = False
    min_dwell_checks: int = 0
    confirm_changes: int = 1
    max_force_rate: float = 1.0
    rate_window: int = 128


@dataclass
class ConservativeRenewalDecision:
    env_id: int
    agent_id: int
    allowed: bool
    block_reason: str
    renewal_signal: bool


class ConservativeRenewalGate:
    def __init__(
        self,
        *,
        num_envs: int,
        n_agents: int,
        config: ConservativeRenewalConfig,
    ):
        self.num_envs = int(num_envs)
        self.n_agents = int(n_agents)
        self.config = config
        self._change_counts = [
            [0 for _ in range(self.n_agents)] for _ in range(self.num_envs)
        ]
        self._recent_forced: Deque[int] = deque(
            maxlen=max(int(config.rate_window), 1)
        )
        self._counts = {
            "events": 0,
            "allowed": 0,
            "blocked_confirm": 0,
            "blocked_dwell": 0,
            "blocked_rate_cap": 0,
            "blocked_no_change": 0,
        }

    def reset_env(self, env_id: int) -> None:
        env = int(env_id)
        if 0 <= env < self.num_envs:
            for agent_id in range(self.n_agents):
                self._change_counts[env][agent_id] = 0

    def reset_all(self) -> None:
        for env_id in range(self.num_envs):
            self.reset_env(env_id)
        self._recent_forced.clear()
        self.reset_metrics()

    def reset_metrics(self) -> None:
        for key in self._counts:
            self._counts[key] = 0

    def _rate_cap_allows(self) -> bool:
        max_rate = float(self.config.max_force_rate)
        if max_rate >= 1.0:
            return True
        if len(self._recent_forced) < int(self._recent_forced.maxlen or 0):
            return True
        if max_rate <= 0.0:
            return False
        if not self._recent_forced:
            return True
        recent_rate = sum(self._recent_forced) / float(len(self._recent_forced))
        return recent_rate < max_rate

    def check(
        self,
        *,
        env_id: int,
        agent_id: int,
        situation_changed: bool,
        skill_age: int,
        step: int,
        stable_count: int = 0,
    ) -> ConservativeRenewalDecision:
        env = int(env_id)
        agent = int(agent_id)
        self._counts["events"] += 1
        _ = int(skill_age)
        _ = int(step)

        if not bool(self.config.enabled):
            self._counts["allowed"] += 1
            return ConservativeRenewalDecision(
                env,
                agent,
                True,
                "allow",
                bool(situation_changed),
            )

        pending_count = int(self._change_counts[env][agent])
        has_signal = bool(situation_changed) or pending_count > 0
        if not bool(situation_changed) and pending_count <= 0:
            self._change_counts[env][agent] = 0
            self._counts["blocked_no_change"] += 1
            return ConservativeRenewalDecision(env, agent, False, "no_change", False)

        self._change_counts[env][agent] += 1

        if int(stable_count) < int(max(self.config.min_dwell_checks, 0)):
            self._counts["blocked_dwell"] += 1
            return ConservativeRenewalDecision(env, agent, False, "dwell", has_signal)

        if self._change_counts[env][agent] < int(
            max(self.config.confirm_changes, 1)
        ):
            self._counts["blocked_confirm"] += 1
            return ConservativeRenewalDecision(env, agent, False, "confirm", has_signal)

        if not self._rate_cap_allows():
            self._counts["blocked_rate_cap"] += 1
            return ConservativeRenewalDecision(env, agent, False, "rate_cap", has_signal)

        self._counts["allowed"] += 1
        return ConservativeRenewalDecision(env, agent, True, "allow", True)

    def record_decision(
        self,
        decision: ConservativeRenewalDecision,
        *,
        forced: bool,
    ) -> None:
        if int(self.config.rate_window) > 0:
            self._recent_forced.append(1 if forced else 0)
        if forced:
            self._change_counts[int(decision.env_id)][int(decision.agent_id)] = 0

    def metrics(self, *, reset: bool = True) -> dict[str, float]:
        events = float(max(int(self._counts["events"]), 1))
        values = {
            "situation_hazard_guard_event_count": float(self._counts["events"]),
            "situation_hazard_guard_allow_rate": float(self._counts["allowed"]) / events,
            "situation_hazard_guard_confirm_block_rate": (
                float(self._counts["blocked_confirm"]) / events
            ),
            "situation_hazard_guard_dwell_block_rate": (
                float(self._counts["blocked_dwell"]) / events
            ),
            "situation_hazard_guard_rate_cap_block_rate": (
                float(self._counts["blocked_rate_cap"]) / events
            ),
            "situation_hazard_guard_no_change_block_rate": (
                float(self._counts["blocked_no_change"]) / events
            ),
            "situation_hazard_guard_recent_force_rate": (
                float(sum(self._recent_forced)) / float(len(self._recent_forced))
                if self._recent_forced
                else 0.0
            ),
        }
        if reset:
            self.reset_metrics()
        return values


def should_force_renewal(
    *,
    mode: str,
    situation_changed: bool,
    skill_age: int,
    min_age: int,
    hazard_action: int,
    guard_allowed: bool = True,
) -> bool:
    if int(skill_age) < int(max(min_age, 0)):
        return False
    if not bool(guard_allowed):
        return False
    if mode == "oracle_change":
        return bool(situation_changed)
    if mode == "learned_beta":
        return bool(int(hazard_action) > 0)
    return False


class SituationHazardPolicy(nn.Module):
    def __init__(
        self,
        *,
        obs_dim: int,
        n_skills: int,
        compact_dim: int,
        team_code_dim: int,
        n_kappa: int,
        hidden_dim: int,
    ):
        super().__init__()
        self.n_skills = int(n_skills)
        self.n_kappa = int(max(n_kappa, 1))
        input_dim = (
            int(obs_dim)
            + self.n_skills
            + 1
            + int(compact_dim)
            + int(team_code_dim)
            + self.n_kappa
            + 1
        )
        self.net = nn.Sequential(
            nn.LayerNorm(input_dim),
            nn.Linear(input_dim, int(hidden_dim)),
            nn.GELU(),
            nn.Linear(int(hidden_dim), int(hidden_dim)),
            nn.GELU(),
        )
        self.logit_head = nn.Linear(int(hidden_dim), 1)
        self.value_head = nn.Linear(int(hidden_dim), 1)

    def _features(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
    ) -> torch.Tensor:
        prev_onehot = F.one_hot(
            prev_skill.long().clamp(0, self.n_skills - 1),
            num_classes=self.n_skills,
        ).float()
        kappa_onehot = F.one_hot(
            kappa.long().clamp(0, self.n_kappa - 1),
            num_classes=self.n_kappa,
        ).float()
        age_feature = torch.log1p(age.float()).unsqueeze(-1) / 10.0
        changed_feature = changed.float().unsqueeze(-1)
        inputs = torch.cat(
            [
                obs.float(),
                prev_onehot,
                age_feature,
                compact.float(),
                team_vector.float(),
                kappa_onehot,
                changed_feature,
            ],
            dim=-1,
        )
        return self.net(inputs)

    def logits(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        hidden = self._features(
            obs, prev_skill, age, compact, team_vector, kappa, changed
        )
        return self.logit_head(hidden).squeeze(-1), self.value_head(hidden).squeeze(-1)

    def act(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
        deterministic: bool = False,
    ):
        logits, value = self.logits(
            obs, prev_skill, age, compact, team_vector, kappa, changed
        )
        dist = Bernoulli(logits=logits)
        if deterministic:
            action = (torch.sigmoid(logits) >= 0.5).float()
        else:
            action = dist.sample()
        logp = dist.log_prob(action)
        entropy = dist.entropy()
        return action.long(), logp, entropy, value

    def evaluate(
        self,
        obs: torch.Tensor,
        prev_skill: torch.Tensor,
        age: torch.Tensor,
        compact: torch.Tensor,
        team_vector: torch.Tensor,
        kappa: torch.Tensor,
        changed: torch.Tensor,
        action: torch.Tensor,
    ):
        logits, value = self.logits(
            obs, prev_skill, age, compact, team_vector, kappa, changed
        )
        dist = Bernoulli(logits=logits)
        action_f = action.float().clamp(0.0, 1.0)
        return dist.log_prob(action_f), dist.entropy(), value
