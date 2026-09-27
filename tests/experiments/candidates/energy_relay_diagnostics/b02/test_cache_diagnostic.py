from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("gymnasium")

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from experiments.candidates.energy_relay_diagnostics.b02.training import (
    StepCommunicationCacheInvariantError,
    collect_with_policy_surrogate_mask,
    install_step_communication_cache_diagnostic,
)
from experiments.candidates.energy_relay_benchmark.b02 import training as benchmark_training
from tests._scenario7_fixtures import make_env


def test_bool_cache_diagnostics_preserve_getter_and_fail_before_active_branch():
    seed = 925131
    core_env = make_env("S7-S2", seed=seed)
    adapter = ParallelToArrayAdapter(core_env, seed=seed)
    restore = None
    try:
        adapter.reset(seed=seed)
        core_env.current_step = 17
        cache = core_env._refresh_step_communication_cache()
        restore = install_step_communication_cache_diagnostic(
            adapter, lane=2, seed=seed
        )

        for active in (False, True):
            core_env._step_communication_cache = None
            core_env._channel_update_cache_active = active
            assert core_env._current_step_communication_cache() is None

            core_env._step_communication_cache = cache
            assert core_env._current_step_communication_cache() is cache

            for invalid in (False, True):
                core_env._step_communication_cache = cache
                assert core_env._current_step_communication_cache() is cache
                core_env._step_communication_cache = invalid
                with pytest.raises(StepCommunicationCacheInvariantError) as caught:
                    core_env._current_step_communication_cache()

                details = caught.value.details
                assert details["stage"] == "before_original_getter"
                assert details["lane"] == 2
                assert details["lane_seed"] == seed
                assert details["environment_step"] == 17
                assert details["cache_type"] == "builtins.bool"
                assert details["cache_value"] == repr(invalid)
                assert details["cache_identity"] == id(invalid)
                assert details["channel_update_cache_active"] == repr(active)
                assert details["getter_module"].endswith("routed_core")
                assert details["getter_module_file"].endswith("routed_core.py")
                reads = details["recent_getter_reads"]
                assert reads[-2]["cache_type"].endswith("dict")
                assert reads[-1]["cache_type"] == "builtins.bool"
                assert reads[-1]["getter_ordinal"] == details["getter_ordinal"]
                assert core_env._step_communication_cache is invalid

        core_env._step_communication_cache = cache
        core_env._channel_update_cache_active = False
        assert core_env._current_step_communication_cache() is cache
    finally:
        if restore is not None:
            restore()
        adapter.close()


def test_collector_installs_probe_and_restores_factory_after_failure(monkeypatch):
    class CoreEnv:
        def __init__(self):
            self._step_communication_cache = None
            self._channel_update_cache_active = True
            self.current_step = 9

        def _current_step_communication_cache(self):
            cache = self._step_communication_cache
            if cache is None:
                return None
            if self._channel_update_cache_active:
                return cache
            return cache["config"]

    class Adapter:
        def __init__(self):
            self.env = CoreEnv()

        def close(self):
            pass

    seed = 925132
    created_cores = []

    def source_factory(_config, _seed):
        env = Adapter()
        created_cores.append(env.env)
        return env

    source_feedback = benchmark_training.apply_feedback
    monkeypatch.setattr(benchmark_training, "make_env", source_factory)
    monkeypatch.setattr(
        "experiments.candidates.energy_relay_diagnostics.b02.training.optimizer_steps",
        lambda _agent: {"low_actor": 0, "low_critic": 0},
    )
    agent = SimpleNamespace(
        rollout_buffer=SimpleNamespace(enable_policy_surrogate_mask=lambda: None),
        store_transition_batch=lambda *args, **kwargs: None,
    )
    source_store_transition_batch = agent.store_transition_batch
    config = SimpleNamespace(num_envs=1, rollout_length=1, n_agents=1)
    spec = SimpleNamespace(lanes=1, rollout_length=1, rollouts=1)

    def fail_after_check(_agent, _config, _spec, **kwargs):
        assert benchmark_training.make_env is not source_factory
        env = benchmark_training.make_env(config, seed)
        try:
            assert env.env._step_communication_cache is None
            env.env._step_communication_cache = False
            with pytest.raises(StepCommunicationCacheInvariantError) as caught:
                env.env._current_step_communication_cache()
            assert caught.value.details["lane"] == 0
            assert caught.value.details["lane_seed"] == seed
        finally:
            env.close()
        raise RuntimeError("collector sentinel")

    monkeypatch.setattr(benchmark_training, "collect_and_train", fail_after_check)
    with pytest.raises(RuntimeError, match="collector sentinel"):
        collect_with_policy_surrogate_mask(
            agent,
            config,
            spec,
            mask_direct_policy_surrogate=False,
            start_rollout=0,
            start_transitions=0,
            env_seed=seed,
        )

    assert benchmark_training.make_env is source_factory
    assert benchmark_training.apply_feedback is source_feedback
    assert agent.store_transition_batch is source_store_transition_batch
    assert len(created_cores) == 1
    assert "_current_step_communication_cache" not in created_cores[0].__dict__
