"""Standalone process-agent lifecycle and transition-buffer methods."""

from __future__ import annotations

from copy import deepcopy

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
    _STANDALONE_LIFECYCLE_ARRAY_FIELDS = (
        "active_skills",
        "active_duration_indices",
        "duration_remaining",
        "skill_age",
        "has_active_skill",
        "active_team_codes",
        "episode_steps",
        "episode_ids",
        "steps_to_check",
        "team_intent_remaining",
        "team_intent_age",
        "team_intent_prior_counts",
        "low_actor_hxs",
        "low_critic_hxs",
        "_team_transition_env_steps",
    )
    _STANDALONE_LIFECYCLE_OBJECT_FIELDS = (
        "high_check_buffer",
        "segments",
        "_last_low_context",
        "outcome_extractor",
        "outcome_residual_extractor",
        "topology_role_extractor",
        "intrinsic_rewards",
        "p2_computer",
        "situation_debouncer",
        "per_agent_situation_debouncer",
        "situation_hazard_guard",
        "_last_situation_state",
        "_last_agent_situation_state",
        "_situation_diag_events",
        "_agent_situation_diag_events",
        "_team_transition_open",
        "_team_transition_closed",
        "_team_intent_boundary_trunc_fracs",
        "_team_intent_boundary_trunc_by_duration",
        "_team_intent_dwell_checks",
        "_team_intent_age_check_samples",
    )
    _STANDALONE_LIFECYCLE_SCALAR_FIELDS = (
        "_last_forced_z_assignment_kl",
        "_situation_hazard_forced_renewals",
        "_situation_hazard_events",
        "_team_intent_boundary_count",
    )

    def initialize_standalone_rngs(self, seed: int) -> None:
        """Initialize named trainer RNGs without mutating NumPy's global RNG."""

        seed_sequence = np.random.SeedSequence([int(seed), 0x48414354, 0x53484C45])
        self._low_update_shuffle_rng = np.random.default_rng(seed_sequence)

    def standalone_lifecycle_state_dict(self) -> dict:
        """Return the complete mutable policy frontier used by the next action."""

        if not hasattr(self, "_low_update_shuffle_rng"):
            raise RuntimeError("standalone named shuffle RNG has not been initialized")
        arrays = {
            name: np.asarray(getattr(self, name)).copy()
            for name in self._STANDALONE_LIFECYCLE_ARRAY_FIELDS
        }
        objects = {
            name: deepcopy(getattr(self, name))
            for name in self._STANDALONE_LIFECYCLE_OBJECT_FIELDS
        }
        scalars = {
            name: deepcopy(getattr(self, name))
            for name in self._STANDALONE_LIFECYCLE_SCALAR_FIELDS
        }
        return {
            "lifecycle_schema_version": 1,
            "num_envs": int(self.num_envs),
            "n_agents": int(self.n_agents),
            "arrays": arrays,
            "objects": objects,
            "scalars": scalars,
            "low_update_shuffle_rng_state": deepcopy(
                self._low_update_shuffle_rng.bit_generator.state
            ),
        }

    def load_standalone_lifecycle_state_dict(self, state: dict) -> None:
        """Strictly restore a schema-4 standalone policy frontier."""

        if not isinstance(state, dict):
            raise TypeError("standalone lifecycle state must be a mapping")
        required = {
            "lifecycle_schema_version",
            "num_envs",
            "n_agents",
            "arrays",
            "objects",
            "scalars",
            "low_update_shuffle_rng_state",
        }
        if set(state) != required:
            raise ValueError(
                "standalone lifecycle keys mismatch: "
                f"expected={sorted(required)}, actual={sorted(state)}"
            )
        if int(state["lifecycle_schema_version"]) != 1:
            raise ValueError("unsupported standalone lifecycle schema")
        if int(state["num_envs"]) != int(self.num_envs) or int(
            state["n_agents"]
        ) != int(self.n_agents):
            raise ValueError("standalone lifecycle topology mismatch")

        arrays = state["arrays"]
        objects = state["objects"]
        scalars = state["scalars"]
        if set(arrays) != set(self._STANDALONE_LIFECYCLE_ARRAY_FIELDS):
            raise ValueError("standalone lifecycle array schema mismatch")
        if set(objects) != set(self._STANDALONE_LIFECYCLE_OBJECT_FIELDS):
            raise ValueError("standalone lifecycle object schema mismatch")
        if set(scalars) != set(self._STANDALONE_LIFECYCLE_SCALAR_FIELDS):
            raise ValueError("standalone lifecycle scalar schema mismatch")

        restored_arrays: dict[str, np.ndarray] = {}
        for name in self._STANDALONE_LIFECYCLE_ARRAY_FIELDS:
            current = np.asarray(getattr(self, name))
            saved = np.asarray(arrays[name])
            if saved.shape != current.shape or saved.dtype != current.dtype:
                raise ValueError(
                    f"standalone lifecycle array mismatch for {name}: "
                    f"expected={current.shape}/{current.dtype}, "
                    f"actual={saved.shape}/{saved.dtype}"
                )
            restored_arrays[name] = saved.copy()

        rng = np.random.default_rng()
        try:
            rng.bit_generator.state = deepcopy(state["low_update_shuffle_rng_state"])
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid standalone shuffle RNG state") from exc

        for name, value in restored_arrays.items():
            setattr(self, name, value)
        for name in self._STANDALONE_LIFECYCLE_OBJECT_FIELDS:
            setattr(self, name, deepcopy(objects[name]))
        for name in self._STANDALONE_LIFECYCLE_SCALAR_FIELDS:
            setattr(self, name, deepcopy(scalars[name]))
        self._low_update_shuffle_rng = rng

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
