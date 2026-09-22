"""Execution, storage and result-identity checks for GCEA's experimental boundary."""
import copy
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from experiments.candidates.goal_conditioned_entity_aggregation.b01 import runner
from scripts import hmasd_admission
from scripts import run_gcea_b01 as entry


class _MutatingAdapter:
    n_uavs = 2

    def __init__(self):
        self.env = SimpleNamespace(uav_positions=np.zeros((2, 3)), max_speed=2.0, time_step=1.0)
        self.executed = None

    def step(self, actions):
        self.executed = actions.copy()
        self.env.uav_positions = np.clip(self.env.uav_positions + 2.0 * actions, -1.0, 1.0)
        actions[:] = 17.0  # A downstream writer must not corrupt the latent policy sample.
        return "observed-transition"


def test_execution_copy_and_observational_counters_do_not_change_policy_sample_or_rng():
    adapter = _MutatingAdapter()
    stats = runner._empty_action_statistics()
    env = runner.BoundedExecutionEnv(adapter, stats)
    raw = np.array([[2.0, -3.0, .25], [.5, 1.0, -.5]], dtype=np.float32)
    original = raw.copy()
    numpy_state = np.random.get_state()
    torch_state = torch.random.get_rng_state().clone()
    assert env.step(raw) == "observed-transition"
    np.testing.assert_array_equal(raw, original)
    np.testing.assert_array_equal(adapter.executed, np.clip(original, -1.0, 1.0))
    assert stats["raw_outside_coordinates"] == 2
    assert stats["raw_outside_uav_actions"] == 1
    assert stats["raw_outside_team_steps"] == 1
    assert stats["executed_saturated_coordinates"] == 3
    assert stats["executed_saturated_uav_actions"] == 2
    assert stats["coordinates"] == 6
    assert stats["uav_actions"] == 2
    assert stats["team_steps"] == 1
    assert stats["raw_max_abs"] == 3
    assert stats["raw_abs_excess_sum"] == 3
    assert stats["position_absorbed_coordinates"] == 3
    assert stats["position_observed_coordinates"] == 6
    after = np.random.get_state()
    assert after[0] == numpy_state[0] and after[2:] == numpy_state[2:]
    np.testing.assert_array_equal(after[1], numpy_state[1])
    torch.testing.assert_close(torch.random.get_rng_state(), torch_state, rtol=0, atol=0)


@pytest.mark.parametrize("bad", [np.full((2, 3), np.nan), np.zeros((2, 4))])
def test_invalid_raw_sample_is_rejected_before_transition(bad):
    adapter = _MutatingAdapter()
    stats = runner._empty_action_statistics()
    with pytest.raises(ValueError, match="finite raw 3-vector"):
        runner.BoundedExecutionEnv(adapter, stats).step(bad)
    assert adapter.executed is None
    assert stats["team_steps"] == 0


@pytest.mark.parametrize("arm", ["O", "P", "E"])
def test_short_real_pipeline_with_mocked_admission(monkeypatch, tmp_path, arm):
    """80 train + 40 eval fixture steps/arm, with actual updates; no scientific fit."""
    shared = runner.native.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", 2)
    monkeypatch.setattr(shared, "EVAL_LANES", 2)
    monkeypatch.setattr(shared, "HORIZON", 20)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    monkeypatch.setattr(runner, "ROLLOUTS", 2)
    monkeypatch.setattr(runner, "PANEL_ROLLOUTS", (2,))
    sha = shared.e0._git("rev-parse", "HEAD")
    monkeypatch.setattr(hmasd_admission, "require_admission",
                        lambda *args, **kwargs: {"sha": sha, "command_sha256": "mocked-test-only"})

    storage_calls = []
    stored_outside = []
    original_store = shared.HMASDAgent.store_transition_batch

    def checked_store(agent, *args, **kwargs):
        raw = kwargs["actions"].copy()
        log_probs = np.asarray(kwargs["step_data"]["action_logprobs"]).copy()
        skills = np.asarray(kwargs["step_data"]["agent_skills"]).copy()
        result = original_store(agent, *args, **kwargs)
        t = kwargs["rollout_step_idx"]
        np.testing.assert_array_equal(agent.rollout_buffer.actions[t], raw)
        np.testing.assert_array_equal(agent.rollout_buffer.log_probs[t], log_probs)
        np.testing.assert_array_equal(agent.rollout_buffer.agent_skills[t], skills)
        np.testing.assert_array_equal(kwargs["actions"], raw)
        storage_calls.append(t)
        stored_outside.append(int((np.abs(raw) > 1.0).sum()))
        return result

    monkeypatch.setattr(shared.HMASDAgent, "store_transition_batch", checked_store)
    native_env_factory = shared.e0._make_envs
    out = tmp_path / arm
    assert entry.main(["--arm", arm, "--seed", str(runner.TRAINING_SEED),
                       "--launch-sha", sha, "--output-root", str(out)]) == 0
    assert shared.e0._make_envs is native_env_factory
    summary = json.loads((out / "summary.json").read_text())
    assert storage_calls == list(range(20)) * 2
    assert sum(stored_outside) > 0
    assert summary["counts"]["training_transitions"] == 80
    assert summary["counts"]["stored_training_transitions"] == 80
    assert summary["counts"]["training_episodes"] == 4
    assert summary["counts"]["evaluation_steps"] == 40
    assert summary["counts"]["evaluation_episodes"] == 2
    assert summary["counts"]["update_stages"] == 2
    assert [p["panel_rollouts"] for p in summary["panels"]] == [2]
    assert all(summary["optimizer_calls"][name] > 0 for name in runner.NETWORKS)
    assert not any(summary["evaluation_optimizer_calls"].values())
    assert summary["encoder_arm"] == arm
    assert summary["parameter_counts"]["active_base_type"] == (
        "MLPBase" if arm == "O" else type(runner.CURRENT["learner"].skill_discoverer.actor.base).__name__)
    assert not any(summary["active_plain_hmasd_flags"][name] for name in (
        "use_horizon_window", "use_team_bridge", "use_opt_compact", "use_compact_in_low_level_actor",
        "use_process_exploration", "disable_high_level_training", "disable_discriminator_training",
        "disable_discriminator_rewards"))
    train_stats = summary["action_statistics"]["train"]
    assert train_stats["team_steps"] == 80
    assert train_stats["coordinates"] == 80 * 6 * 3
    assert train_stats["raw_outside_coordinates"] == sum(stored_outside)
    assert train_stats["executed_saturated_coordinates"] >= sum(stored_outside)
    assert train_stats["position_observed_team_steps"] == 80
    assert summary["action_statistics"]["evaluation"]["team_steps"] == 40
    assert summary["actor_timing"]["learner"]["forward_calls"] > 0
    assert summary["actor_timing"]["learner"]["evaluate_actions_calls"] > 0
    assert summary["actor_timing"]["evaluator"]["forward_calls"] > 0
    assert summary["phase_wall_seconds"]["total"] > 0
    assert list(runner.fit_endpoint(summary)) == [2]

    # Native terminal reset and independent evaluation must leave a recoverable exact schema.
    checkpoint_path = out / summary["final_checkpoint"]["path"]
    envs = shared.e0._make_envs(2, runner.TRAINING_SEED, 6, 50, 20)
    with runner.scoped_native_bindings():
        config = runner.make_config(arm, envs, runner.TRAINING_SEED)
    restored = shared.HMASDAgent(config, log_dir=str(tmp_path / (arm + "-restore")), device=torch.device("cpu"))
    runner.install_actor_encoder(restored, arm)
    restored.load_model(checkpoint_path)
    stored = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    restored_state = restored.skill_discoverer.state_dict()
    assert stored["skill_discoverer"].keys() == restored_state.keys()
    for key, value in stored["skill_discoverer"].items():
        torch.testing.assert_close(value, restored_state[key], rtol=0, atol=0)
    bad = copy.deepcopy(summary)
    bad["action_statistics"]["train"]["team_steps"] -= 1
    with pytest.raises(ValueError, match="telemetry"):
        runner.fit_endpoint(bad)
    bad = copy.deepcopy(summary)
    bad["panel_rollouts"] = [1, 2]
    with pytest.raises(ValueError, match="wrong arm/block/object"):
        runner.fit_endpoint(bad)


def test_entry_refuses_without_admission_before_creating_output(monkeypatch, tmp_path):
    import os
    for name in list(os.environ):
        if name.startswith("HMASD_ADMISSION"):
            monkeypatch.delenv(name)
    out = tmp_path / "unadmitted"
    with pytest.raises((RuntimeError, ValueError, SystemExit), match="[Aa]dmission"):
        entry.main(["--arm", "O", "--seed", str(runner.TRAINING_SEED),
                    "--launch-sha", "0" * 40, "--output-root", str(out)])
    assert not out.exists()


def test_frozen_arm_seed_and_single_panel_contract():
    assert tuple(runner.ARMS) == ("O", "P", "E")
    assert runner.ROLLOUTS == 45 and runner.PANEL_ROLLOUTS == (45,)
    assert runner.BLOCKS == {922611: 923611}
    with pytest.raises(SystemExit, match="unknown arm"):
        runner.plan_guard("L", runner.TRAINING_SEED)
    with pytest.raises(SystemExit, match="fixes training seed"):
        runner.plan_guard("O", 92101)
