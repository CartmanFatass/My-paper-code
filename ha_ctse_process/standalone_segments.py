"""Standalone rollout and segment state containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


R24_PRE_ASSIGNMENT_WINDOW_MAX_STEPS = 32


@dataclass
class Segment:
    env_id: int
    agent_id: int
    skill: int
    duration_idx: int
    start_step: int
    high_obs: np.ndarray
    high_logp: float
    high_value: float
    high_entropy: float
    high_state: np.ndarray | None = None
    high_joint_obs: np.ndarray | None = None
    prev_skill: int = 0
    skill_age_prev: int = 0
    team_code: int = 0
    team_logp_weight: float = 1.0
    team_intent_boundary: bool = False
    team_intent_truncated: bool = False
    skill_assignment_logp: float = 0.0
    duration_assignment_logp: float = 0.0
    ar_parallel_kl_start: float = 0.0
    ar_prefix_start: np.ndarray | None = None
    roster_active_skills_start: np.ndarray | None = None
    roster_active_ages_start: np.ndarray | None = None
    roster_active_mask_start: np.ndarray | None = None
    roster_ar_kl_zeroed_start: float = 0.0
    roster_ar_kl_shuffled_start: float = 0.0
    selection_independence_deficit_start: float = 0.0
    initial_assignment: bool = False
    switched: bool = False
    duration_target: int = 1
    renewal_penalty: float = 0.0
    episode_step_start: int = 0
    episode_id: int = 0
    policy_update: int = 0
    pre_assignment_episode_id: int = -1
    pre_assignment_policy_update: int = -1
    completion_reason: str = "active"
    obs: list[np.ndarray] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    deterministic_actions: list[np.ndarray] = field(default_factory=list)
    pre_assignment_high_obs: np.ndarray | None = None
    pre_assignment_obs: list[np.ndarray] = field(default_factory=list)
    pre_assignment_actions: list[np.ndarray] = field(default_factory=list)
    pre_assignment_deterministic_actions: list[np.ndarray] = field(default_factory=list)
    pre_assignment_end_obs: np.ndarray | None = None
    rewards: list[float] = field(default_factory=list)
    rollout_indices: list[int] = field(default_factory=list)
    reward_info_seq: list[dict] = field(default_factory=list)
    state_info_seq: list[dict[str, Any]] = field(default_factory=list)
    # True segment-start state (BEFORE the first action), captured separately from
    # state_info_seq (which only holds post-step states).  Used by P2 recovery
    # shaping so s0 is the real window start, not the post-first-step state.
    start_state_info: dict[str, Any] | None = None
    start_reward_info: dict[str, Any] | None = None
    end_obs: np.ndarray | None = None
    end_joint_obs: np.ndarray | None = None
    end_state: np.ndarray | None = None
    terminal: bool = False
    kappa_start: int = -1
    kappa_end: int = -1
    raw_kappa_start: int = -1
    raw_kappa_end: int = -1
    agent_kappa_start: int = -1
    raw_agent_kappa_start: int = -1
    omega_start: np.ndarray | None = None
    agent_relevance_start: np.ndarray | None = None
    situation_changed_during_segment: bool = False

    def append(
        self,
        obs,
        action,
        reward,
        next_obs,
        rollout_idx: int,
        reward_info=None,
        state_info=None,
        next_joint_obs=None,
        next_state=None,
        done: bool = False,
        pre_state_info=None,
        pre_reward_info=None,
        deterministic_action=None,
    ):
        # On the segment's first step, record the pre-step (segment-start) state so
        # P2 shaping telescopes over the true window, not the post-first-step state.
        if not self.state_info_seq and self.start_state_info is None and pre_state_info:
            self.start_state_info = dict(pre_state_info)
            self.start_reward_info = dict(pre_reward_info or {})
        self.obs.append(np.asarray(obs, dtype=np.float32))
        action_arr = np.asarray(action, dtype=np.float32)
        self.actions.append(action_arr.reshape(-1))
        if deterministic_action is not None:
            deterministic_arr = np.asarray(deterministic_action, dtype=np.float32).reshape(-1)
            self.deterministic_actions.append(deterministic_arr)
        self.rewards.append(float(reward))
        self.rollout_indices.append(int(rollout_idx))
        self.reward_info_seq.append(dict(reward_info or {}))
        self.state_info_seq.append(dict(state_info or {}))
        self.end_obs = np.asarray(next_obs, dtype=np.float32)
        self.end_joint_obs = None if next_joint_obs is None else np.asarray(next_joint_obs, dtype=np.float32)
        self.end_state = None if next_state is None else np.asarray(next_state, dtype=np.float32)
        self.terminal = bool(done)

    @property
    def length(self) -> int:
        return len(self.rewards)


class SegmentManager:
    def __init__(self, n_envs: int, n_agents: int):
        self.n_envs = int(n_envs)
        self.n_agents = int(n_agents)
        self.active: list[list[Segment | None]] = [
            [None for _ in range(n_agents)]
            for _ in range(n_envs)
        ]
        self.completed: list[Segment] = []

    def renew(
        self,
        env_id: int,
        agent_id: int,
        skill: int,
        duration_idx: int,
        step: int,
        high_obs,
        high_logp: float,
        high_value: float,
        high_entropy: float,
        high_state=None,
        high_joint_obs=None,
        prev_skill: int = 0,
        skill_age_prev: int = 0,
        team_code: int = 0,
        team_logp_weight: float = 1.0,
        team_intent_boundary: bool = False,
        team_intent_truncated: bool = False,
        skill_assignment_logp: float = 0.0,
        duration_assignment_logp: float = 0.0,
        ar_parallel_kl_start: float = 0.0,
        ar_prefix_start=None,
        roster_active_skills_start=None,
        roster_active_ages_start=None,
        roster_active_mask_start=None,
        roster_ar_kl_zeroed_start: float = 0.0,
        roster_ar_kl_shuffled_start: float = 0.0,
        selection_independence_deficit_start: float = 0.0,
        initial_assignment: bool = False,
        switched: bool = False,
        duration_target: int = 1,
        renewal_penalty: float = 0.0,
        kappa_start: int = -1,
        raw_kappa_start: int = -1,
        agent_kappa_start: int = -1,
        raw_agent_kappa_start: int = -1,
        omega_start=None,
        agent_relevance_start=None,
        episode_step_start: int = 0,
        episode_id: int = 0,
        policy_update: int = 0,
    ):
        old = self.active[env_id][agent_id]
        pre_assignment_high_obs = None
        pre_assignment_obs: list[np.ndarray] = []
        pre_assignment_actions: list[np.ndarray] = []
        pre_assignment_deterministic_actions: list[np.ndarray] = []
        pre_assignment_end_obs = None
        pre_assignment_episode_id = -1
        pre_assignment_policy_update = -1
        if old is not None and old.length > 0:
            old.completion_reason = "renewal"
            pre_assignment_high_obs = np.asarray(old.high_obs, dtype=np.float32).copy()
            pre_assignment_obs = [
                np.asarray(row, dtype=np.float32).copy()
                for row in old.obs[-R24_PRE_ASSIGNMENT_WINDOW_MAX_STEPS:]
            ]
            pre_assignment_actions = [
                np.asarray(row, dtype=np.float32).reshape(-1).copy()
                for row in old.actions[-R24_PRE_ASSIGNMENT_WINDOW_MAX_STEPS:]
            ]
            if (
                int(old.episode_id) == int(episode_id)
                and int(old.policy_update) == int(policy_update)
            ):
                pre_assignment_deterministic_actions = [
                    np.asarray(row, dtype=np.float32).reshape(-1).copy()
                    for row in old.deterministic_actions[-10:]
                ]
                pre_assignment_episode_id = int(old.episode_id)
                pre_assignment_policy_update = int(old.policy_update)
            pre_assignment_end_obs = (
                None if old.end_obs is None else np.asarray(old.end_obs, dtype=np.float32).copy()
            )
            if int(kappa_start) >= 0:
                old.kappa_end = int(kappa_start)
                old.situation_changed_during_segment = bool(
                    old.situation_changed_during_segment
                    or (int(old.kappa_start) >= 0 and int(old.kappa_end) != int(old.kappa_start))
                )
            if int(raw_kappa_start) >= 0:
                old.raw_kappa_end = int(raw_kappa_start)
            self.completed.append(old)
        self.active[env_id][agent_id] = Segment(
            env_id=int(env_id),
            agent_id=int(agent_id),
            skill=int(skill),
            duration_idx=int(duration_idx),
            start_step=int(step),
            high_obs=np.asarray(high_obs, dtype=np.float32),
            high_logp=float(high_logp),
            high_value=float(high_value),
            high_entropy=float(high_entropy),
            high_state=None if high_state is None else np.asarray(high_state, dtype=np.float32),
            high_joint_obs=None if high_joint_obs is None else np.asarray(high_joint_obs, dtype=np.float32),
            prev_skill=int(prev_skill),
            skill_age_prev=int(skill_age_prev),
            team_code=int(team_code),
            team_logp_weight=float(team_logp_weight),
            team_intent_boundary=bool(team_intent_boundary),
            team_intent_truncated=bool(team_intent_truncated),
            skill_assignment_logp=float(skill_assignment_logp),
            duration_assignment_logp=float(duration_assignment_logp),
            ar_parallel_kl_start=float(ar_parallel_kl_start),
            ar_prefix_start=(
                None
                if ar_prefix_start is None
                else np.asarray(ar_prefix_start, dtype=np.float32).reshape(-1)
            ),
            roster_active_skills_start=(
                None
                if roster_active_skills_start is None
                else np.asarray(roster_active_skills_start, dtype=np.int64).reshape(-1)
            ),
            roster_active_ages_start=(
                None
                if roster_active_ages_start is None
                else np.asarray(roster_active_ages_start, dtype=np.float32).reshape(-1)
            ),
            roster_active_mask_start=(
                None
                if roster_active_mask_start is None
                else np.asarray(roster_active_mask_start, dtype=np.bool_).reshape(-1)
            ),
            roster_ar_kl_zeroed_start=float(roster_ar_kl_zeroed_start),
            roster_ar_kl_shuffled_start=float(roster_ar_kl_shuffled_start),
            selection_independence_deficit_start=float(selection_independence_deficit_start),
            initial_assignment=bool(initial_assignment),
            switched=bool(switched),
            duration_target=int(duration_target),
            renewal_penalty=float(renewal_penalty),
            episode_step_start=int(episode_step_start),
            episode_id=int(episode_id),
            policy_update=int(policy_update),
            pre_assignment_episode_id=int(pre_assignment_episode_id),
            pre_assignment_policy_update=int(pre_assignment_policy_update),
            kappa_start=int(kappa_start),
            kappa_end=int(kappa_start),
            raw_kappa_start=int(raw_kappa_start),
            raw_kappa_end=int(raw_kappa_start),
            agent_kappa_start=int(agent_kappa_start),
            raw_agent_kappa_start=int(raw_agent_kappa_start),
            omega_start=None if omega_start is None else np.asarray(omega_start, dtype=np.float32),
            agent_relevance_start=(
                None if agent_relevance_start is None else np.asarray(agent_relevance_start, dtype=np.float32)
            ),
            pre_assignment_high_obs=pre_assignment_high_obs,
            pre_assignment_obs=pre_assignment_obs,
            pre_assignment_actions=pre_assignment_actions,
            pre_assignment_deterministic_actions=pre_assignment_deterministic_actions,
            pre_assignment_end_obs=pre_assignment_end_obs,
        )

    def append(
        self,
        env_id: int,
        obs,
        actions,
        rewards,
        next_obs,
        rollout_idx: int,
        reward_info=None,
        state_info=None,
        next_state=None,
        done: bool = False,
        pre_state_info=None,
        pre_reward_info=None,
        deterministic_actions=None,
    ):
        for agent_id, segment in enumerate(self.active[env_id]):
            if segment is None:
                continue
            segment.append(
                obs[agent_id],
                actions[agent_id],
                rewards[agent_id],
                next_obs[agent_id],
                rollout_idx,
                reward_info=reward_info,
                state_info=state_info,
                next_joint_obs=next_obs,
                next_state=next_state,
                done=done,
                pre_state_info=pre_state_info,
                pre_reward_info=pre_reward_info,
                deterministic_action=(
                    None
                    if deterministic_actions is None
                    else deterministic_actions[agent_id]
                ),
            )

    def flush(self, env_id: int | None = None, reason: str = "update"):
        if reason not in {"episode", "update"}:
            raise ValueError("segment flush reason must be episode or update")
        env_ids = range(self.n_envs) if env_id is None else [int(env_id)]
        for current_env in env_ids:
            for agent_id, segment in enumerate(self.active[current_env]):
                if segment is not None and segment.length > 0:
                    segment.completion_reason = reason
                    self.completed.append(segment)
                self.active[current_env][agent_id] = None

    def pop_completed(self) -> list[Segment]:
        segments = self.completed
        self.completed = []
        return segments


@dataclass
class Rollout:
    env_ids: list[int] = field(default_factory=list)
    obs: list[np.ndarray] = field(default_factory=list)
    states: list[np.ndarray] = field(default_factory=list)
    next_states: list[np.ndarray] = field(default_factory=list)
    skills: list[np.ndarray] = field(default_factory=list)
    team_codes: list[int] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)
    deterministic_actions: list[np.ndarray] = field(default_factory=list)
    logp: list[np.ndarray] = field(default_factory=list)
    values: list[np.ndarray] = field(default_factory=list)
    low_actor_hxs: list[np.ndarray] = field(default_factory=list)
    low_critic_hxs: list[np.ndarray] = field(default_factory=list)
    rewards: list[np.ndarray] = field(default_factory=list)
    dones: list[bool] = field(default_factory=list)
    bootstrap_values: dict[int, np.ndarray] = field(default_factory=dict)
