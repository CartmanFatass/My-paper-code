from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, is_dataclass
from functools import partial
import random
from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process.collectors import (
    EVENT_SNAPSHOT_CAPABILITY_NAME,
    EVENT_SNAPSHOT_CAPABILITY_VERSION,
    PIPE_PICKLE_TRANSPORT,
    SHARED_MEMORY_TRANSPORT,
    EventEnvStep,
    EnvStep,
    SubprocEnvCollector,
    SyncEnvCollector,
    _restore_training_env,
)
from ha_ctse_process.config import Config
from ha_ctse_process.dynamic_roster_testbed import DynamicRosterEventEnv
from ha_ctse_process.env_factory import EnvSpec, make_env


class _ActionSpace:
    dtype = np.dtype(np.int64)
    shape = (2,)
    n = 5


class CollectorTestEnv:
    obs_dim = 32
    state_dim = 64
    action_dim = 5
    n_uavs = 2
    action_space = _ActionSpace()

    def __init__(self, rank: int = 0, width: int = 512):
        self.rank = int(rank)
        self.width = int(width)
        self.step_count = 0
        self.episode_id = -1
        self.capability_calls = 0
        self.rng = np.random.default_rng(700 + self.rank)

    def reset(self, seed=None):
        self.rng = np.random.default_rng(seed)
        self.step_count = 0
        return self._obs(), self._info()

    def _obs(self):
        return self.rng.normal(size=(self.n_uavs, self.width)).astype(np.float32)

    def _info(self):
        state = self.rng.normal(size=self.width * 2).astype(np.float64)
        return {
            "state": state,
            "next_state": state.copy(),
            "rank": self.rank,
            "label": f"worker-{self.rank}",
            "process_outcome": {
                "frontier": (self.rank, self.step_count),
                "mask": np.array([True, False, True], dtype=np.bool_),
                "nested": [{"value": np.float32(self.rng.random())}],
            },
        }

    def step(self, action):
        self.step_count += 1
        obs = self._obs()
        info = self._info()
        info["action"] = np.asarray(action).copy()
        return obs, float(self.rng.random()), self.step_count >= 5, False, info

    def event_runtime_snapshot_capability(self):
        self.capability_calls += 1
        return {
            "name": EVENT_SNAPSHOT_CAPABILITY_NAME,
            "version": EVENT_SNAPSHOT_CAPABILITY_VERSION,
        }

    def reset_event_runtime(self, episode_id: int):
        self.episode_id = int(episode_id)
        self.step_count = 0
        self.rng = np.random.default_rng(10_000 + self.rank + self.episode_id)
        return {"episode_id": self.episode_id, "rank": self.rank}

    def step_event_runtime(self, actions):
        self.step_count += 1
        return SimpleNamespace(
            reward=float(self.rng.random()),
            terminated=self.step_count >= 5,
            truncated=False,
            info={"actions": deepcopy(actions), "draw": float(self.rng.random())},
            next_transaction={"step": self.step_count, "rank": self.rank},
        )

    def snapshot_event_runtime(self):
        return {
            "snapshot_capability_name": EVENT_SNAPSHOT_CAPABILITY_NAME,
            "snapshot_capability_version": EVENT_SNAPSHOT_CAPABILITY_VERSION,
            "active_presentation": [self.rank],
            "pending_membership_transaction": {"step": self.step_count},
            "pending_command_response_state": "ready",
            "worker_environment_snapshot": {
                "step_count": self.step_count,
                "episode_id": self.episode_id,
            },
            "environment_rng_state": deepcopy(self.rng.bit_generator.state),
        }

    def restore_event_runtime(self, snapshot):
        if snapshot["snapshot_capability_name"] != EVENT_SNAPSHOT_CAPABILITY_NAME:
            raise ValueError("capability name mismatch")
        if int(snapshot["snapshot_capability_version"]) != EVENT_SNAPSHOT_CAPABILITY_VERSION:
            raise ValueError("capability version mismatch")
        state = snapshot["worker_environment_snapshot"]
        self.step_count = int(state["step_count"])
        self.episode_id = int(state["episode_id"])
        self.rng.bit_generator.state = deepcopy(snapshot["environment_rng_state"])

    def close(self):
        return None


def _assert_tree_equal(left, right):
    if isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray)
        assert left.dtype == right.dtype
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict)
        assert tuple(left) == tuple(right)
        for key in left:
            _assert_tree_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert type(left) is type(right)
        assert len(left) == len(right)
        for left_value, right_value in zip(left, right):
            _assert_tree_equal(left_value, right_value)
    elif isinstance(left, (EnvStep, EventEnvStep)):
        assert type(left) is type(right)
        _assert_tree_equal(left.__dict__, right.__dict__)
    elif is_dataclass(left):
        assert type(left) is type(right)
        for field in fields(left):
            _assert_tree_equal(getattr(left, field.name), getattr(right, field.name))
    else:
        assert type(left) is type(right)
        assert left == right


def test_training_snapshot_preserves_generic_short_active_frontier():
    env = DynamicRosterEventEnv(task_master_seed=901)
    collector = SyncEnvCollector([env])
    transaction = collector.reset_event_runtime([3])[0]
    snapshot = collector.snapshot_training_state()
    actions = {
        int(key): 0
        for key in transaction.post_membership_pre_policy_snapshot.keys
    }
    expected = collector.step_event_runtime([actions])[0]
    collector.restore_training_state(snapshot)
    actual = collector.step_event_runtime([actions])[0]
    _assert_tree_equal(actual, expected)
    collector.close()


def test_training_snapshot_preserves_simple_spread_ezpickle_live_state():
    env = make_env(
        Config(),
        EnvSpec(scenario="simple_spread", seed=177, rank=0, scale_mode="train"),
    )()
    collector = SyncEnvCollector([env])
    collector.reset_all(177)
    snapshot = collector.snapshot_training_state()
    action = np.zeros(env.action_space.shape, dtype=env.action_space.dtype)
    expected = collector.step([action])[0]
    collector.restore_training_state(snapshot)
    actual = collector.step([action])[0]
    _assert_tree_equal(actual, expected)
    collector.close()


def test_default_subproc_shared_memory_restores_simple_spread_live_state():
    collector = SubprocEnvCollector(
        config=Config(),
        scenario="simple_spread",
        seed=177,
        num_envs=1,
        scale_mode="train",
        start_method="spawn",
    )
    try:
        assert collector.transport == SHARED_MEMORY_TRANSPORT
        collector.reset_all(177)
        snapshot = collector.snapshot_training_state()
        action = np.zeros(collector.spec["action_space"].shape, dtype=np.int64)
        expected = collector.step([action])[0]
        collector.restore_training_state(snapshot)
        actual = collector.step([action])[0]
        _assert_tree_equal(actual, expected)
    finally:
        collector.close()


@pytest.mark.parametrize(
    "scenario",
    [
        "base",
        "belief_map",
        "progress",
        "energy",
        "alice_bob_asymmetric_cycles",
        "cooperative_two_timescale_sparse",
        "two_timescale_role_free_actions",
    ],
)
def test_training_snapshot_preserves_next_step_for_constructible_array_scenarios(
    scenario,
):
    env = make_env(
        Config(),
        EnvSpec(scenario=scenario, seed=177, rank=0, scale_mode="train"),
    )()
    collector = SyncEnvCollector([env])
    collector.reset_all(177)
    snapshot = collector.snapshot_training_state()
    action = np.zeros(env.action_space.shape, dtype=env.action_space.dtype)
    python_rng = random.getstate()
    numpy_rng = np.random.get_state()
    expected = collector.step([action])[0]
    collector.restore_training_state(snapshot)
    random.setstate(python_rng)
    np.random.set_state(numpy_rng)
    actual = collector.step([action])[0]
    _assert_tree_equal(actual, expected)
    collector.close()


def test_belief_map_factory_passes_only_supported_config_fields():
    config = Config()
    env = make_env(
        config,
        EnvSpec(scenario="belief_map", seed=177, rank=2, scale_mode="train"),
    )()
    try:
        assert env.env.n_uavs == config.n_agents
        assert env.env.n_users == config.n_users
        assert env.env.seed_val == 179
    finally:
        env.close()


def _make_subproc(transport: str, *, width: int = 512, capacity: int = 1 << 20):
    return SubprocEnvCollector(
        config=SimpleNamespace(),
        scenario="base",
        seed=300,
        num_envs=2,
        scale_mode="train",
        start_method="spawn",
        transport=transport,
        shared_memory_bytes=capacity,
        env_factories=[
            partial(CollectorTestEnv, rank=0, width=width),
            partial(CollectorTestEnv, rank=1, width=width),
        ],
    )


def test_generic_short_factory_binds_task_ledger_to_spec_seed_and_rank():
    config = SimpleNamespace(dynamic_roster_task_ledger_seed=67_057)
    first = make_env(
        config,
        EnvSpec(scenario="generic_short_dynamic_roster", seed=900, rank=2),
    )()
    second = make_env(
        config,
        EnvSpec(scenario="generic_short_dynamic_roster", seed=900, rank=3),
    )()
    assert first.task_master_seed == 902
    assert second.task_master_seed == 903
    assert DynamicRosterEventEnv(task_master_seed=67_057).task_master_seed == 67_057
    assert DynamicRosterEventEnv(task_master_seed=97_057).task_master_seed == 97_057


def test_sync_event_capability_is_pinned_and_identity_changes_fail_closed():
    env = CollectorTestEnv()
    collector = SyncEnvCollector([env])
    assert collector.event_runtime_capability()["version"] == 1
    collector.reset_event_runtime([4])
    collector.step_event_runtime([{0: 1}])
    collector.snapshot_event_runtime()
    assert env.capability_calls == 1

    env.snapshot_event_runtime = lambda: {}
    with pytest.raises(RuntimeError, match="identity changed"):
        collector.snapshot_event_runtime()

    collector = SyncEnvCollector([CollectorTestEnv()])
    collector.event_runtime_capability()
    collector.envs[0] = CollectorTestEnv()
    with pytest.raises(RuntimeError, match="identity changed"):
        collector.step_event_runtime([{0: 1}])


def test_sync_training_state_restores_exact_next_step_and_rejects_corruption():
    collector = SyncEnvCollector([CollectorTestEnv(rank=0)])
    collector.reset_all(51)
    collector.step([np.array([1, 2], dtype=np.int64)])
    snapshot = collector.snapshot_training_state()
    expected = collector.step([np.array([2, 3], dtype=np.int64)])[0]
    collector.step([np.array([4, 0], dtype=np.int64)])
    collector.restore_training_state(snapshot)
    actual = collector.step([np.array([2, 3], dtype=np.int64)])[0]
    _assert_tree_equal(actual, expected)

    broken = deepcopy(snapshot)
    broken["workers"][0]["payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest mismatch"):
        collector.restore_training_state(broken)

    broken_spec = deepcopy(snapshot)
    broken_spec["workers"][0]["environment_spec"]["obs_dim"] += 1
    with pytest.raises(ValueError, match="environment spec mismatch"):
        collector.restore_training_state(broken_spec)


def test_pipe_and_shared_memory_preserve_full_step_event_and_rng_semantics():
    pipe = _make_subproc(PIPE_PICKLE_TRANSPORT)
    shared = _make_subproc(SHARED_MEMORY_TRANSPORT)
    try:
        _assert_tree_equal(pipe.reset_all(91), shared.reset_all(91))
        actions = [
            np.array([1, 2], dtype=np.int64),
            np.array([3, 4], dtype=np.int64),
        ]
        for _ in range(3):
            _assert_tree_equal(pipe.step(actions), shared.step(actions))

        _assert_tree_equal(
            pipe.reset_event_runtime([10, 11]),
            shared.reset_event_runtime([10, 11]),
        )
        routed = [{"a": 1}, {"b": 2}]
        _assert_tree_equal(
            pipe.step_event_runtime(routed),
            shared.step_event_runtime(routed),
        )
        pipe_snapshot = pipe.snapshot_event_runtime()
        shared_snapshot = shared.snapshot_event_runtime()
        _assert_tree_equal(pipe_snapshot, shared_snapshot)
        expected_pipe = pipe.step_event_runtime(routed)
        expected_shared = shared.step_event_runtime(routed)
        pipe.restore_event_runtime(pipe_snapshot)
        shared.restore_event_runtime(shared_snapshot)
        _assert_tree_equal(pipe.step_event_runtime(routed), expected_pipe)
        _assert_tree_equal(shared.step_event_runtime(routed), expected_shared)
        pipe_state = pipe.snapshot_training_state()
        shared_state = shared.snapshot_training_state()
        for state in (pipe_state, shared_state):
            for worker in state["workers"]:
                restored = _restore_training_env(worker)
                assert restored.capability_calls == 1
                restored.close()
    finally:
        pipe.close()
        shared.close()


@pytest.mark.parametrize("transport", [PIPE_PICKLE_TRANSPORT, SHARED_MEMORY_TRANSPORT])
def test_subproc_training_state_restores_worker_rng_and_frontier(transport):
    collector = _make_subproc(transport)
    try:
        collector.reset_all(123)
        collector.step([np.array([0, 1]), np.array([2, 3])])
        snapshot = collector.snapshot_training_state()
        expected = collector.step([np.array([1, 1]), np.array([3, 3])])
        collector.step([np.array([4, 4]), np.array([0, 0])])
        collector.restore_training_state(snapshot)
        actual = collector.step([np.array([1, 1]), np.array([3, 3])])
        _assert_tree_equal(actual, expected)

        broken = deepcopy(snapshot)
        broken["worker_count"] = 3
        with pytest.raises(ValueError, match="worker count mismatch"):
            collector.restore_training_state(broken)
    finally:
        collector.close()


def test_shared_memory_capacity_error_never_falls_back_to_pipe():
    collector = _make_subproc(SHARED_MEMORY_TRANSPORT, width=2048, capacity=512)
    try:
        with pytest.raises(RuntimeError, match="exceeds configured capacity"):
            collector.reset_all(8)
        assert collector._broken
    finally:
        collector.close()


def test_event_snapshot_version_is_strict():
    collector = SyncEnvCollector([CollectorTestEnv()])
    collector.reset_event_runtime([1])
    snapshot = collector.snapshot_event_runtime()
    snapshot["snapshot_capability_version"] = 99
    with pytest.raises(ValueError, match="version mismatch"):
        collector.restore_event_runtime(snapshot)
