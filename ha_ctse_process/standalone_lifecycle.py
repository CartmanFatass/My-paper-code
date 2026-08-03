"""Standalone process-agent lifecycle and transition-buffer methods."""

from __future__ import annotations

import numpy as np

import ha_ctse_process.standalone_segments as standalone_segments
from ha_ctse_process.situation_substrate import (
    PerAgentSituationDebouncer,
    SituationDebouncer,
)
from ha_ctse_process.situation_transition import (
    TeamTransitionInterval,
    skill_count_vector,
)


class StandaloneLifecycleMixin:
    def reset_env_state(self, env_id: int):
        env_id = int(env_id)
        self.episode_steps[env_id] = 0
        self.episode_ids[env_id] += 1
        self.steps_to_check[env_id] = 0
        if self.high_check_buffer is not None:
            self.high_check_buffer.clear_env(env_id)
        self.duration_remaining[env_id, :] = 0
        self.active_skills[env_id, :] = 0
        self.active_duration_indices[env_id, :] = 0
        self.skill_age[env_id, :] = 0
        self.has_active_skill[env_id, :] = False
        self.active_team_codes[env_id] = 0
        self.team_intent_remaining[env_id] = 0
        self.team_intent_age[env_id] = 0
        self.low_actor_hxs[env_id, :, :] = 0.0
        self.low_critic_hxs[env_id, :, :] = 0.0
        self._last_low_context[env_id] = None
        self.situation_debouncer.reset_env(env_id)
        self.per_agent_situation_debouncer.reset_env(env_id)
        self.situation_hazard_guard.reset_env(env_id)
        self._last_situation_state[env_id] = None
        self._last_agent_situation_state[env_id] = [None for _ in range(self.n_agents)]
        if hasattr(self, "_team_transition_open"):
            self._team_transition_open[env_id] = None
        if hasattr(self, "_team_transition_env_steps"):
            self._team_transition_env_steps[env_id] = 0

    def reset_all_policy_state(self):
        if self.r30_enabled:
            raise RuntimeError(
                "R30 policy state cannot be reset at a PPO update boundary"
            )
        self.duration_remaining[:, :] = 0
        self.active_skills[:, :] = 0
        self.active_duration_indices[:, :] = 0
        self.skill_age[:, :] = 0
        self.has_active_skill[:, :] = False
        self.active_team_codes[:] = 0
        self.team_intent_remaining[:] = 0
        self.team_intent_age[:] = 0
        self._team_intent_boundary_count = 0
        self._team_intent_boundary_trunc_fracs = []
        self._team_intent_boundary_trunc_by_duration = {
            int(candidate): [] for candidate in self.duration_candidates
        }
        self._team_intent_dwell_checks = []
        self._team_intent_age_check_samples = []
        self.low_actor_hxs[:, :, :] = 0.0
        self.low_critic_hxs[:, :, :] = 0.0
        self._last_low_context = [None for _ in range(self.num_envs)]
        self.situation_debouncer = SituationDebouncer(self.situation_debouncer.config)
        self.per_agent_situation_debouncer = PerAgentSituationDebouncer(self.situation_debouncer.config)
        self.situation_hazard_guard.reset_all()
        self._last_situation_state = [None for _ in range(self.num_envs)]
        self._last_agent_situation_state = [
            [None for _ in range(self.n_agents)]
            for _ in range(self.num_envs)
        ]
        self._situation_diag_events = []
        self._agent_situation_diag_events = []
        self._situation_hazard_forced_renewals = 0
        self._situation_hazard_events = 0
        self.segments = standalone_segments.SegmentManager(self.num_envs, self.n_agents)
        self._team_transition_open = [None for _ in range(self.num_envs)]
        self._team_transition_closed = []
        self._team_transition_env_steps = np.zeros(self.num_envs, dtype=np.int64)

    def _team_transition_xi(self, env_id: int) -> np.ndarray:
        active = self.has_active_skill[int(env_id)]
        skills = self.active_skills[int(env_id), active]
        return skill_count_vector(skills, self.n_skills)

    def _team_transition_record_check(self, env_id: int, kappa: int, step: int) -> None:
        if self.team_transition is None:
            return
        env_id = int(env_id)
        local_step = int(self._team_transition_env_steps[env_id])
        self._team_transition_env_steps[env_id] = local_step + 1
        interval = int(max(self.situation_hazard_check_interval, 1))
        if local_step % interval != 0:
            return
        current_kappa = int(kappa)
        open_interval = self._team_transition_open[env_id]
        if open_interval is not None:
            closed = TeamTransitionInterval(
                env_id=open_interval.env_id,
                start_step=open_interval.start_step,
                end_step=int(step),
                kappa=open_interval.kappa,
                xi=open_interval.xi,
                kappa_next=current_kappa,
            )
            if closed.end_step > closed.start_step:
                self._team_transition_closed.append(closed)
        self._team_transition_open[env_id] = TeamTransitionInterval(
            env_id=env_id,
            start_step=int(step),
            end_step=int(step),
            kappa=current_kappa,
            xi=self._team_transition_xi(env_id),
            kappa_next=-1,
        )

    def _team_transition_clear_rollout_buffers(self) -> None:
        if not hasattr(self, "_team_transition_open"):
            return
        self._team_transition_open = [None for _ in range(self.num_envs)]
        self._team_transition_closed = []
