from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.r26_g1_dataset import window_summary
from scripts import collect_r26_g1_windows as collector
from scripts.collect_r26_g1_windows import (
    _RUNTIME_ATTRIBUTES,
    PendingWindow,
    collect_reset,
    pending_prior_context,
    policy_parameters_equal,
    require_cuda_device,
    snapshot_policy_parameters,
    write_r28_sidecar_shard,
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

    def close(self) -> None:
        pass


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
        self.assignment_grad_enabled: list[bool] = []
        self.action_grad_enabled: list[bool] = []
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
        self.assignment_grad_enabled.append(torch.is_grad_enabled())
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
        self.action_grad_enabled.append(torch.is_grad_enabled())
        actions = np.asarray(
            [
                [float(self.current_step), float(self.active_skills[env_id, 0])],
                [float(self.current_step + 10), float(self.active_skills[env_id, 1])],
            ],
            dtype=np.float32,
        )
        return actions, np.zeros(2, dtype=np.float32), np.zeros(2, dtype=np.float32)


class FakeR28Env:
    def __init__(self) -> None:
        self.steps = 0

    def _obs(self) -> np.ndarray:
        return np.asarray(
            [[float(self.steps), float(agent_id)] for agent_id in range(6)],
            dtype=np.float32,
        )

    def reset(self, *, seed: int):
        self.steps = 0
        return self._obs(), {"state": np.asarray([float(seed)], dtype=np.float32)}

    def step(self, actions):
        assert np.asarray(actions).shape == (6, 4)
        self.steps += 1
        return self._obs(), 0.0, False, False, {
            "next_state": np.asarray([float(self.steps)], dtype=np.float32)
        }


class FakeR28Agent:
    def __init__(self) -> None:
        self.n_agents = 6
        self.n_skills = 4
        self.num_team_codes = 1
        self.duration_candidates = (1, 2, 3, 4)
        self.active_skills = np.zeros((1, 6), dtype=np.int64)
        self.active_duration_indices = np.zeros((1, 6), dtype=np.int64)
        self.duration_remaining = np.zeros((1, 6), dtype=np.int64)
        self.skill_age = np.zeros((1, 6), dtype=np.int64)
        self.has_active_skill = np.zeros((1, 6), dtype=np.bool_)
        self.active_team_codes = np.zeros(1, dtype=np.int64)
        self.segments = SimpleNamespace(active=[[None for _ in range(6)]])
        self.current_step = 0

    def reset_env_state(self, env_id: int) -> None:
        self.active_skills[env_id] = 0
        self.active_duration_indices[env_id] = 0
        self.duration_remaining[env_id] = 0
        self.skill_age[env_id] = 0
        self.has_active_skill[env_id] = False
        self.segments.active[env_id] = [None for _ in range(6)]

    def maybe_assign_skills(self, obs, *, step: int, env_id: int, **_kwargs) -> None:
        self.current_step = int(step)
        if step not in (0, 10, 20):
            return
        label = {0: 0, 10: 1, 20: 2}[int(step)]
        self.active_skills[env_id, 0] = label
        self.active_duration_indices[env_id, 0] = 0
        self.has_active_skill[env_id, 0] = True
        self.segments.active[env_id][0] = SimpleNamespace(
            skill=label,
            duration_idx=0,
            prev_skill=max(label - 1, 0),
            skill_age_prev=10 if step else 0,
            team_code=0,
            high_obs=np.asarray(obs[0], dtype=np.float32).copy(),
            omega_start=np.asarray([1.0], dtype=np.float32),
            roster_active_skills_start=self.active_skills[env_id].copy(),
        )

    def act_low(
        self,
        obs,
        *,
        env_id: int,
        return_context: bool = False,
        capture_deterministic_action: bool = False,
        **_kwargs,
    ):
        del obs
        deterministic = np.zeros((6, 4), dtype=np.float32)
        for agent_id in range(6):
            deterministic[agent_id] = np.asarray(
                [self.current_step, self.active_skills[env_id, agent_id], agent_id, 1.0],
                dtype=np.float32,
            )
        result = (
            deterministic.copy(),
            np.zeros(6, dtype=np.float32),
            np.zeros(6, dtype=np.float32),
        )
        if return_context:
            assert capture_deterministic_action
            return (*result, {"deterministic_actions": deterministic})
        return result

    def record_environment_step(self, env_id: int) -> None:
        del env_id


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


def test_collector_owns_no_grad_boundary_for_assignment_and_action():
    agent = FakeAgent({0: [(0, 1, 0)]})
    collect_reset(
        FakeEnv(),
        agent,
        reset_id=0,
        reset_seed=1,
        episode_id=0,
        skill_interval=1,
        episode_max_steps=1,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )
    assert agent.assignment_grad_enabled == [False]
    assert agent.action_grad_enabled == [False]


def test_incomplete_replacement_discards_once_and_emits_only_replacement():
    batch, stats = _collect(
        {0: [(0, 0, 0)], 1: [(0, 2, 1)]},
        skill_interval=2,
        episode_max_steps=3,
    )
    expected_actions = np.asarray([[1.0, 2.0], [2.0, 2.0]], dtype=np.float32)
    expected_observations = np.asarray(
        [[1.0, 1.5], [2.0, 2.5], [3.0, 3.5]], dtype=np.float32
    )
    assert batch.label.tolist() == [2]
    assert batch.duration_idx.tolist() == [1]
    assert np.allclose(batch.post_action[0], window_summary(expected_actions, 2))
    assert np.allclose(
        batch.post_effect[0], window_summary(expected_observations, 2)
    )
    assert stats.renewal_events == 2
    assert stats.discarded_incomplete == 1
    assert stats.completed_windows == 1


def test_no_complete_pre_history_emits_zero_summaries_and_invalid_flag():
    batch, _stats = _collect(
        {0: [(0, 1, 0)]},
        skill_interval=2,
        episode_max_steps=2,
    )
    assert batch.pre_valid.tolist() == [0.0]
    assert np.array_equal(batch.pre_action[0], np.zeros(8, dtype=np.float32))
    assert np.array_equal(batch.pre_effect[0], np.zeros(8, dtype=np.float32))


def test_exact_pre_history_emits_expected_summaries_and_valid_flag():
    batch, _stats = _collect(
        {0: [(0, 0, 0)], 2: [(0, 1, 1)]},
        skill_interval=2,
        episode_max_steps=4,
    )
    expected_actions = np.asarray([[0.0, 0.0], [1.0, 0.0]], dtype=np.float32)
    expected_observations = np.asarray(
        [[0.0, 0.5], [1.0, 1.5], [2.0, 2.5]], dtype=np.float32
    )
    assert batch.label.tolist() == [0, 1]
    assert batch.pre_valid.tolist() == [0.0, 1.0]
    assert np.allclose(batch.pre_action[1], window_summary(expected_actions, 2))
    assert np.allclose(
        batch.pre_effect[1], window_summary(expected_observations, 2)
    )


class MutatingFakeAgent(FakeAgent):
    def act_low(self, obs, *, env_id: int, deterministic: bool, state):
        actions = super().act_low(
            obs,
            env_id=env_id,
            deterministic=deterministic,
            state=state,
        )[0]
        segment = self.segments.active[env_id][0]
        segment.skill = 2
        segment.duration_idx = 1
        segment.prev_skill = 2
        segment.skill_age_prev = 99
        segment.team_code = 0
        segment.high_obs[:] = -10.0
        segment.omega_start[:] = -20.0
        segment.roster_active_skills_start[:] = 2
        self.active_skills[env_id, :] = 2
        self.active_team_codes[env_id] = 0
        return actions, np.zeros(2, dtype=np.float32), np.zeros(2, dtype=np.float32)


def test_assignment_time_fields_are_snapshotted_before_later_mutation():
    agent = MutatingFakeAgent({0: [(0, 1, 0)]})
    batch, _stats = collect_reset(
        FakeEnv(),
        agent,
        reset_id=0,
        reset_seed=1,
        episode_id=0,
        skill_interval=1,
        episode_max_steps=1,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )
    expected = PendingWindow(
        agent_id=0,
        label=1,
        duration_idx=0,
        previous_skill=0,
        previous_age=0,
        team_code=1,
        assignment_obs=np.asarray([0.0, 0.5], dtype=np.float32),
        omega=np.asarray([0.25, 0.75], dtype=np.float32),
        teammate_roster=np.asarray([0, 0], dtype=np.int64),
        pre_action=np.zeros(8, dtype=np.float32),
        pre_effect=np.zeros(8, dtype=np.float32),
        pre_valid=False,
        actions=[],
        observations=[],
    )
    assert batch.label.tolist() == [1]
    assert batch.duration_idx.tolist() == [0]
    assert np.array_equal(
        batch.prior_context[0], pending_prior_context(agent, expected)
    )


def test_preserve_agent_runtime_restores_every_owned_attribute_by_identity():
    agent = FakeAgent({0: [(0, 1, 0)]})
    original_segment = FakeSegment(
        skill=2,
        duration_idx=1,
        prev_skill=1,
        skill_age_prev=3,
        team_code=1,
        high_obs=np.asarray([4.0, 5.0], dtype=np.float32),
        omega_start=np.asarray([0.2, 0.8], dtype=np.float32),
        roster_active_skills_start=np.asarray([2, 1], dtype=np.int64),
        pre_assignment_actions=[],
        pre_assignment_obs=[],
        pre_assignment_high_obs=None,
        pre_assignment_end_obs=None,
    )
    agent.segments.active[0][0] = original_segment
    for index, name in enumerate(_RUNTIME_ATTRIBUTES):
        if not hasattr(agent, name):
            setattr(agent, name, {"marker": [index]})
    originals = {name: getattr(agent, name) for name in _RUNTIME_ATTRIBUTES}
    value_snapshots = copy.deepcopy(originals)

    collect_reset(
        FakeEnv(),
        agent,
        reset_id=0,
        reset_seed=1,
        episode_id=0,
        skill_interval=1,
        episode_max_steps=1,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )

    for name, original in originals.items():
        assert getattr(agent, name) is original, name
    assert agent.segments.active[0][0] is original_segment
    assert np.array_equal(agent.active_skills, value_snapshots["active_skills"])
    assert np.array_equal(
        agent.active_duration_indices, value_snapshots["active_duration_indices"]
    )
    assert np.array_equal(
        agent.duration_remaining, value_snapshots["duration_remaining"]
    )
    assert np.array_equal(
        agent.active_team_codes, value_snapshots["active_team_codes"]
    )


def test_parameter_snapshot_is_stable_and_sensitive_to_parameter_changes():
    agent = SimpleNamespace(policy=torch.nn.Linear(2, 1, bias=False))
    stable = snapshot_policy_parameters(agent)
    assert policy_parameters_equal(snapshot_policy_parameters(agent), stable)
    with torch.no_grad():
        agent.policy.weight.add_(1.0)
    assert not policy_parameters_equal(snapshot_policy_parameters(agent), stable)


def test_run_collection_writes_one_shard_per_reset_and_manifest_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    checkpoint = tmp_path / "fixture_update25.pt"
    checkpoint.write_bytes(b"checkpoint-fixture")
    output_dir = tmp_path / "windows"
    env = FakeEnv()
    agent = FakeAgent({0: [(0, 1, 0)]})
    metadata = {
        "n_skills": 4,
        "n_agents": 6,
        "update_idx": 25,
        "total_steps": 800000,
    }
    monkeypatch.setattr(collector, "require_cuda_device", lambda _device: None)
    monkeypatch.setattr(
        collector,
        "_configure_agent",
        lambda _args: (SimpleNamespace(), metadata, env, agent, 25),
    )
    args = SimpleNamespace(
        checkpoint=str(checkpoint),
        output_dir=str(output_dir),
        config="fixture.config",
        scenario="energy",
        preset="S7-S1",
        seed=7,
        n_agents=6,
        device="cuda",
        skill_interval=1,
        n_resets=3,
        episode_max_steps=1,
        checkpoint_id="fixture_update25",
        checkpoint_update=25,
    )

    manifest = collector.run_collection(args)

    assert len(list(output_dir.glob("reset_*.npz"))) == 3
    written = json.loads((output_dir / "collector_manifest.json").read_text())
    assert written == manifest
    assert written["checkpoint_id"] == "fixture_update25"
    assert written["checkpoint_update"] == 25
    assert written["checkpoint_metadata"]["n_skills"] == 4
    assert written["reset_seeds"] == [7, 8, 9]
    assert written["stats"]["resets"] == 3
    assert written["checkpoint_nonempty"] is True
    assert written["policy_parameters_unchanged"] is True


def test_r28_sidecar_records_only_naturally_completed_terminal_windows(tmp_path):
    torch.manual_seed(4)
    phi0 = torch.nn.Linear(2, 256)
    rows: list[dict[str, object]] = []
    r28_stats: dict[str, int] = {"completed": 0, "discarded": 0}
    collect_reset(
        FakeR28Env(),
        FakeR28Agent(),
        reset_id=3,
        reset_seed=28034,
        episode_id=3,
        skill_interval=10,
        episode_max_steps=21,
        checkpoint_id="r28_g1_probe_only_seed28031_final",
        checkpoint_update=52,
        r28_phi0=phi0,
        r28_sidecar_rows=rows,
        r28_stats=r28_stats,
    )

    assert [row["label"] for row in rows] == [0, 1]
    assert [row["pre_valid"] for row in rows] == [False, True]
    assert r28_stats == {"completed": 2, "discarded": 1}
    expected_first = np.asarray(
        [[step, 0, 0, 1.0] for step in range(10)], dtype=np.float32
    )
    expected_second = np.asarray(
        [[step, 1, 0, 1.0] for step in range(10, 20)], dtype=np.float32
    )
    np.testing.assert_array_equal(rows[0]["post_actions"], expected_first)
    np.testing.assert_array_equal(rows[1]["pre_actions"], expected_first)
    np.testing.assert_array_equal(rows[1]["post_actions"], expected_second)

    path = tmp_path / "reset_0003.npz"
    write_r28_sidecar_shard(path, rows)
    with np.load(path, allow_pickle=False) as shard:
        assert str(np.asarray(shard["schema"]).item()) == "r28-g1-natural-sidecar-v1"
        assert shard["phi0"].shape == (2, 256)
        assert shard["pre_actions"].shape == (2, 10, 4)
        assert shard["post_actions"].shape == (2, 10, 4)
