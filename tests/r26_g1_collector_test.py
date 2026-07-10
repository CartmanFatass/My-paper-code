from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process.r26_g1_dataset import window_summary
from scripts.collect_r26_g1_windows import (
    PendingWindow,
    collect_reset,
    pending_prior_context,
    require_cuda_device,
)


@dataclass
class FakeSegment:
    skill: int
    duration_idx: int
    prev_skill: int
    skill_age_prev: int
    team_code: int
    high_obs: np.ndarray
    omega_start: np.ndarray
    roster_active_skills_start: np.ndarray
    pre_assignment_actions: list[np.ndarray]
    pre_assignment_obs: list[np.ndarray]
    pre_assignment_high_obs: np.ndarray | None
    pre_assignment_end_obs: np.ndarray | None


class FakeEnv:
    def __init__(self, terminate_after: int = 100) -> None:
        self.terminate_after = int(terminate_after)
        self.steps = 0

    def reset(self, *, seed: int):
        self.steps = 0
        obs = np.asarray([[0.0, 0.5], [1.0, 1.5]], dtype=np.float32)
        return obs, {"state": np.asarray([float(seed)], dtype=np.float32)}

    def step(self, actions):
        del actions
        self.steps += 1
        obs = np.asarray(
            [
                [float(self.steps), float(self.steps) + 0.5],
                [float(self.steps) + 1.0, float(self.steps) + 1.5],
            ],
            dtype=np.float32,
        )
        done = self.steps >= self.terminate_after
        return obs, 0.0, done, False, {
            "next_state": np.asarray([float(self.steps)], dtype=np.float32)
        }


class FakeAgent:
    def __init__(self, assignments: dict[int, list[tuple[int, int, int]]]) -> None:
        self.n_agents = 2
        self.n_skills = 3
        self.num_team_codes = 2
        self.duration_candidates = (1, 2)
        self.active_skills = np.zeros((1, 2), dtype=np.int64)
        self.active_duration_indices = np.zeros((1, 2), dtype=np.int64)
        self.duration_remaining = np.zeros((1, 2), dtype=np.int64)
        self.skill_age = np.zeros((1, 2), dtype=np.int64)
        self.has_active_skill = np.zeros((1, 2), dtype=np.bool_)
        self.active_team_codes = np.zeros(1, dtype=np.int64)
        self.segments = SimpleNamespace(active=[[None, None]])
        self.assignments = assignments
        self.current_step = 0
        self.optimizer = SimpleNamespace(step=self._forbidden)

    @staticmethod
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("collector invoked a forbidden update path")

    process_update = _forbidden
    update_high_from_segments = _forbidden
    update_low = _forbidden
    backward = _forbidden

    def reset_env_state(self, env_id: int) -> None:
        self.active_skills[env_id] = 0
        self.active_duration_indices[env_id] = 0
        self.duration_remaining[env_id] = 0
        self.skill_age[env_id] = 0
        self.has_active_skill[env_id] = False
        self.active_team_codes[env_id] = 0
        self.segments.active[env_id] = [None, None]

    def maybe_assign_skills(
        self,
        obs,
        *,
        state,
        step: int,
        k: int,
        env_id: int,
        deterministic: bool,
    ) -> None:
        del state, deterministic
        self.current_step = int(step)
        for agent_id, label, duration_idx in self.assignments.get(int(step), []):
            previous_skill = int(self.active_skills[env_id, agent_id])
            previous_age = int(self.skill_age[env_id, agent_id])
            old = self.segments.active[env_id][agent_id]
            pre_actions = [] if old is None else [
                np.asarray([9.0, 8.0], dtype=np.float32)
            ]
            pre_obs = [] if old is None else [
                np.asarray([7.0, 6.0], dtype=np.float32)
            ]
            segment = FakeSegment(
                skill=int(label),
                duration_idx=int(duration_idx),
                prev_skill=previous_skill,
                skill_age_prev=previous_age,
                team_code=1,
                high_obs=np.asarray(obs[agent_id], dtype=np.float32).copy(),
                omega_start=np.asarray([0.25, 0.75], dtype=np.float32),
                roster_active_skills_start=np.asarray(
                    self.active_skills[env_id], dtype=np.int64
                ).copy(),
                pre_assignment_actions=pre_actions,
                pre_assignment_obs=pre_obs,
                pre_assignment_high_obs=(
                    None
                    if old is None
                    else np.asarray([7.0, 6.0], dtype=np.float32)
                ),
                pre_assignment_end_obs=(
                    None
                    if old is None
                    else np.asarray([8.0, 7.0], dtype=np.float32)
                ),
            )
            self.active_skills[env_id, agent_id] = int(label)
            self.active_duration_indices[env_id, agent_id] = int(duration_idx)
            self.duration_remaining[env_id, agent_id] = int(k)
            self.skill_age[env_id, agent_id] = 0
            self.has_active_skill[env_id, agent_id] = True
            self.segments.active[env_id][agent_id] = segment

    def act_low(
        self,
        obs,
        *,
        env_id: int,
        deterministic: bool,
        state,
    ):
        del obs, deterministic, state
        actions = np.asarray(
            [
                [float(self.current_step), float(self.active_skills[env_id, 0])],
                [float(self.current_step + 10), float(self.active_skills[env_id, 1])],
            ],
            dtype=np.float32,
        )
        return actions, np.zeros(2, dtype=np.float32), np.zeros(2, dtype=np.float32)


def _collect(
    assignments: dict[int, list[tuple[int, int, int]]],
    *,
    skill_interval: int,
    episode_max_steps: int,
    terminate_after: int = 100,
):
    return collect_reset(
        FakeEnv(terminate_after=terminate_after),
        FakeAgent(assignments),
        reset_id=4,
        reset_seed=104,
        episode_id=4,
        skill_interval=skill_interval,
        episode_max_steps=episode_max_steps,
        checkpoint_id="fixture_update25",
        checkpoint_update=25,
    )


def test_new_assignment_opens_exactly_one_pending_window():
    batch, stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=3,
        episode_max_steps=1,
    )
    assert batch.label.size == 0
    assert stats.renewal_events == 1
    assert stats.discarded_incomplete == 1


def test_same_label_reassignment_still_opens_a_window():
    batch, stats = _collect(
        {0: [(0, 2, 0)], 1: [(0, 2, 1)]},
        skill_interval=1,
        episode_max_steps=2,
    )
    assert batch.label.tolist() == [2, 2]
    assert batch.duration_idx.tolist() == [0, 1]
    assert stats.renewal_events == 2
    assert stats.completed_windows == 2


def test_window_finalizes_after_exactly_skill_interval_steps():
    incomplete, incomplete_stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=3,
        episode_max_steps=2,
    )
    assert incomplete.label.size == 0
    assert incomplete_stats.completed_windows == 0

    complete, complete_stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=3,
        episode_max_steps=3,
    )
    expected_actions = np.asarray([[0.0, 1.0], [1.0, 1.0], [2.0, 1.0]])
    expected_observations = np.asarray(
        [[0.0, 0.5], [1.0, 1.5], [2.0, 2.5], [3.0, 3.5]]
    )
    assert complete.segment_length.tolist() == [3]
    assert np.allclose(complete.post_action[0], window_summary(expected_actions, 2))
    assert np.allclose(
        complete.post_effect[0], window_summary(expected_observations, 2)
    )
    assert complete_stats.completed_windows == 1


def test_episode_end_discards_incomplete_post_window():
    batch, stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=3,
        episode_max_steps=10,
        terminate_after=2,
    )
    assert batch.label.size == 0
    assert stats.discarded_incomplete == 1


def test_collector_does_not_call_update_backward_or_optimizer():
    batch, stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=1,
        episode_max_steps=1,
    )
    assert batch.label.tolist() == [1]
    assert stats.completed_windows == 1


def test_prior_context_excludes_current_focal_label():
    agent = FakeAgent({})
    base = PendingWindow(
        agent_id=0,
        label=2,
        duration_idx=1,
        previous_skill=0,
        previous_age=4,
        team_code=1,
        assignment_obs=np.asarray([0.1, 0.2], dtype=np.float32),
        omega=np.asarray([0.4, 0.6], dtype=np.float32),
        teammate_roster=np.asarray([2, 1], dtype=np.int64),
        pre_action=np.zeros(8, dtype=np.float32),
        pre_effect=np.zeros(8, dtype=np.float32),
        pre_valid=False,
        actions=[],
        observations=[],
    )
    changed_focal_slot = PendingWindow(
        **{**base.__dict__, "teammate_roster": np.asarray([0, 1], dtype=np.int64)}
    )
    assert np.array_equal(
        pending_prior_context(agent, base),
        pending_prior_context(agent, changed_focal_slot),
    )


def test_collector_rejects_non_cuda_real_run():
    with pytest.raises(ValueError, match="requires --device cuda"):
        require_cuda_device("cpu")
