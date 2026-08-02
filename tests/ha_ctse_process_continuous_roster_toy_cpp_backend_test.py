from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from ha_ctse_process import continuous_roster_random_process_g34 as g34
from ha_ctse_process import continuous_roster_six_coordinate_cs_g38 as g38
from envs.continuous_roster import cpp_backend as cpp
from envs.continuous_roster import runtime_capacity as roster_env
from scripts import benchmark_continuous_roster_toy_cpp_backend as benchmark


@pytest.mark.parametrize("capacity", g34.CAPACITIES)
@pytest.mark.parametrize("process_kind", ("fixed", "random"))
def test_native_batch_is_bitwise_equal_across_lifecycle_processes(
    capacity: int, process_kind: str
) -> None:
    processes = g34.make_process_ledgers(
        replicate=0, capacity=capacity, episode_count=4
    )
    reference = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in processes
    )
    accelerated = tuple(
        g34.RandomProcessRosterEnv(row)
        if process_kind == "random"
        else roster_env.RuntimeCapacityRosterEnv(row.base)
        for row in processes
    )
    batch = cpp.ContinuousRosterToyBatch(accelerated)
    noise = roster_env.make_action_noise(
        (row.episode_id for row in processes),
        action_seed=10_996_000,
        member_capacity=capacity,
    )

    for time in range(roster_env.HORIZON):
        expected_views = tuple(
            g38.observe_g38_actor_source(env, input_mode=g38.FOLD6_INPUT)
            for env in reference
        )
        actual_views = batch.observe_six()
        for expected, actual in zip(expected_views, actual_views):
            assert actual.membership_change == expected.membership_change
            assert np.array_equal(actual.active_mask, expected.active_mask)
            assert np.array_equal(actual.observations, expected.observations)
            assert np.array_equal(actual.critic_state, expected.critic_state)
            assert actual.load == expected.load
            assert actual.target_mix == expected.target_mix

        actions = np.tanh(noise[time]).astype(np.float32)
        actions[~np.stack([view.active_mask for view in expected_views])] = 0.0
        expected_rewards = np.asarray(
            [
                g38.advance_g38_environment(env, view, action)
                for env, view, action in zip(reference, expected_views, actions)
            ],
            dtype=np.float64,
        )
        actual_rewards = batch.advance(
            actual_views, np.ascontiguousarray(actions)
        )
        assert np.array_equal(actual_rewards, expected_rewards)
        for expected, actual in zip(reference, accelerated):
            assert expected.time == actual.time
            assert expected._change == actual._change
            assert expected._terminated == actual._terminated
            assert np.array_equal(expected.active, actual.active)
            assert np.array_equal(expected.age, actual.age)
            assert np.array_equal(expected.previous_actions, actual.previous_actions)

    assert tuple(env.outcome() for env in accelerated) == tuple(
        env.outcome() for env in reference
    )


def test_python_boundary_rejects_invalid_native_inputs_before_execution() -> None:
    capabilities = np.ones((1, 2, 2), dtype=np.float32)
    active = np.asarray(((True, False),), dtype=np.bool_)
    loads = np.asarray((0.5,), dtype=np.float32)
    mixes = np.asarray((0.5,), dtype=np.float32)
    actions = np.zeros((1, 2, 2), dtype=np.float32)

    with pytest.raises(TypeError, match="dtype float32"):
        cpp.reward_batch(
            capabilities=capabilities.astype(np.float64),
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )
    with pytest.raises(ValueError, match="C-contiguous"):
        cpp.reward_batch(
            capabilities=capabilities[:, ::-1],
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )
    actions[0, 1, 0] = np.float32(0.25)
    with pytest.raises(ValueError, match="inactive actions"):
        cpp.reward_batch(
            capabilities=capabilities,
            active_mask=active,
            actions=actions,
            loads=loads,
            target_mixes=mixes,
        )


def test_python_boundary_rejects_malformed_native_outputs(monkeypatch: pytest.MonkeyPatch) -> None:
    capabilities = np.ones((1, 2, 2), dtype=np.float32)
    priorities = np.ones((1, 2), dtype=np.float32)
    active = np.asarray(((True, False),), dtype=np.bool_)
    loads = np.asarray((0.5,), dtype=np.float32)
    mixes = np.asarray((0.5,), dtype=np.float32)
    logs = np.asarray((np.log(2.0),), dtype=np.float32)
    malformed = SimpleNamespace(
        observe_six_batch=lambda *_args: (
            np.ones((1, 2, 6), dtype=np.float32),
            np.ones((1, 6), dtype=np.float32),
        )
    )
    monkeypatch.setattr(
        cpp, "load_continuous_roster_toy_cpp_backend", lambda: malformed
    )
    with pytest.raises(RuntimeError, match="inactive member"):
        cpp.observe_six_batch(
            capabilities=capabilities,
            priorities=priorities,
            loads=loads,
            target_mixes=mixes,
            active_mask=active,
            log_counts=logs,
            time_fraction=np.float32(0.0),
        )


def test_native_loader_reuses_the_source_keyed_cpu_module() -> None:
    first = cpp.load_continuous_roster_toy_cpp_backend()
    second = cpp.load_continuous_roster_toy_cpp_backend()
    assert first is second
    assert first.__name__.startswith("hmasd_continuous_roster_toy_")


def test_benchmark_schema_is_bounded_and_oracle_gated() -> None:
    result = benchmark.run_benchmark(batch_size=2, capacity=8, repeats=1)
    assert result["schema"] == "continuous_roster_toy_cpp_benchmark_v1"
    assert result["cpu_only"] is True
    assert result["bitwise_outcome_oracle"] is True
    assert result["batch_size"] == 2
    assert result["capacity"] == 8
    assert result["horizon"] == 48
    assert result["repeats"] == 1
    assert result["python_median_seconds"] > 0.0
    assert result["native_median_seconds"] > 0.0
    assert result["speedup"] > 0.0
