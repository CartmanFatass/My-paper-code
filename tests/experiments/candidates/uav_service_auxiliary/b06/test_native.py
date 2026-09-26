from __future__ import annotations

from dataclasses import replace
import importlib
import subprocess
import sys
import types

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import (
    _rng_state,
    initialization_fingerprint,
    make_config,
    make_env,
)
from experiments.candidates.uav_service_auxiliary.b04.native import B04Spec
from experiments.candidates.uav_service_auxiliary.b04.evaluation import evaluate as frozen_evaluate
from experiments.candidates.uav_service_auxiliary.b06 import native
from experiments.candidates.uav_service_auxiliary.b06.feedback import (
    FeedbackDecision,
    apply_feedback,
)
from hmasd.agent import HMASDAgent


def short_spec():
    return B04Spec(
        lanes=1,
        rollouts=1,
        rollout_length=20,
        episode_length=20,
        eval_seeds=(937001,),
        final_seeds=(938001,),
        eval_rollouts=(0, 1),
        ppo_epochs=1,
        threads=1,
        hidden_size=32,
        gru_hidden_size=32,
    )


def set_margin(observations, index, value):
    observations = np.asarray(observations, dtype=np.float32).copy()
    suffix = observations[:, -120:]
    uavs = suffix[:, : 8 * 13].reshape(8, 8, 13)
    uavs[index, index, 12] = value
    return observations


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_off_path_reproduces_rng_recurrence_and_immutable_state(tmp_path, device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("requires actual CUDA")
    torch.set_num_threads(4 if device_name == "cuda" else 1)
    device = torch.device(device_name)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    config = make_config(short_spec())
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    policy = initialization_fingerprint(agent)
    before = _rng_state()
    result_a, arrays_a = native._evaluate_panel(
        agent, config, (937001,), device, policy_seed=short_spec().seed, mode="O",
        log_dir=tmp_path / "eval-a", trace_path=tmp_path / "a.npz",
    )
    middle = _rng_state()
    result_b = frozen_evaluate(
        agent, config, (937001,), device, policy_seed=short_spec().seed,
        log_dir=tmp_path / "eval-b", trace_path=tmp_path / "b.npz",
    )
    after = _rng_state()
    for left, right in ((before, middle), (middle, after)):
        assert left["python"] == right["python"]
        np.testing.assert_array_equal(left["numpy"][1], right["numpy"][1])
        assert left["numpy"][2:] == right["numpy"][2:]
        assert torch.equal(left["torch"], right["torch"])
        if left["cuda"] is not None:
            assert len(left["cuda"]) == len(right["cuda"])
            assert all(torch.equal(a, b) for a, b in zip(left["cuda"], right["cuda"], strict=True))
    with np.load(tmp_path / "b.npz", allow_pickle=False) as arrays_b:
        np.testing.assert_array_equal(arrays_a["metric_fields"], arrays_b["metric_fields"])
        for suffix in native.COMMON_ARRAY_SUFFIXES:
            key = "episode_0_" + suffix
            np.testing.assert_array_equal(arrays_a[key], arrays_b[key])
    assert result_a["new_optimizer_updates"] == result_b["new_optimizer_updates"] == 0
    assert result_a["normalizers_immutable"]
    assert result_a["policy_sha256_before_after"] == policy == initialization_fingerprint(agent)
    world = result_a["worlds"][0]
    assert world["actual_length"] == 20 and world["terminal_type"] == "truncated"
    assert arrays_a["episode_0_agent_skills"].shape == (20, 8)
    assert not arrays_a["episode_0_command_changed"].any()


def test_world_aggregation_handles_mixed_activation_order():
    base = {
        "seed": 1,
        "actual_length": 10,
        "raw_native_J": 2.0,
        "native_J_per_step": 0.2,
        "episode_minimum_battery_ratio": 0.4,
        "episode_minimum_return_margin": -0.1,
        "zero_service_episode": False,
        "mode_uav_steps": 0,
        "entry_count": 0,
        "exit_count": 0,
        "command_override_uav_steps": 0,
        "maximum_simultaneous_modes": 0,
        "first_mode_entry_step": None,
        "first_command_override_step": None,
        "mode_durations_by_uav": [[] for _ in range(8)],
        "descriptive_250_step_bins": [],
    }
    activated = {
        **base,
        "seed": 2,
        "first_mode_entry_step": 3,
        "first_command_override_step": 4,
        "mode_uav_steps": 6,
    }
    for worlds in ((base, activated), (activated, base)):
        aggregate = native._aggregate_worlds(list(worlds))
        assert aggregate["first_mode_entry_step_observed_worlds"] == 1
        assert aggregate["mean_first_mode_entry_step"] == 3.0
        assert aggregate["first_command_override_step_observed_worlds"] == 1
        assert aggregate["mean_first_command_override_step"] == 4.0


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_mode_changes_do_not_reset_real_actor_gru_or_skill_clock(
    tmp_path, monkeypatch, device_name
):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("requires actual CUDA")
    torch.set_num_threads(4 if device_name == "cuda" else 1)
    device = torch.device(device_name)
    if device.type == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    config = make_config(short_spec())
    source = HMASDAgent(config, log_dir=str(tmp_path / "source"), device=device)

    class TrackingAgent(HMASDAgent):
        reset_calls = 0

        def reset_env_state(self, env_id):
            type(self).reset_calls += 1
            return super().reset_env_state(env_id)

    call = 0

    def switching_feedback(observations, actions, modes):
        nonlocal call
        base = apply_feedback(observations, actions, modes)
        new_modes = np.full(8, call % 2 == 0, dtype=bool)
        submitted = np.asarray(actions, dtype=np.float32).copy()
        submitted[:, 3] = 1.0 - submitted[:, 3]
        call += 1
        return FeedbackDecision(
            submitted_actions=submitted,
            modes=new_modes,
            entered=new_modes & ~modes,
            exited=~new_modes & modes,
            margins=base.margins,
            batteries=base.batteries,
            selected_stations=base.selected_stations,
            station_distances_m=base.station_distances_m,
            station_vectors_m=base.station_vectors_m,
        )

    monkeypatch.setattr(native, "HMASDAgent", TrackingAgent)
    monkeypatch.setattr(native, "apply_feedback", switching_feedback)
    result, arrays = native._evaluate_panel(
        source, config, (937001,), device, policy_seed=short_spec().seed, mode="F",
        log_dir=tmp_path / "eval", trace_path=tmp_path / "trace.npz",
    )
    assert TrackingAgent.reset_calls == 1
    assert result["new_optimizer_updates"] == 0
    assert arrays["episode_0_command_changed"].all()
    assert arrays["episode_0_entry"].any() and arrays["episode_0_exit"].any()
    # k=10 remains the only non-reset skill boundary despite a mode change each step.
    changed_steps = np.flatnonzero(np.asarray(arrays["episode_0_skill_changed"]).reshape(-1))
    np.testing.assert_array_equal(changed_steps, (0, 10))


def test_mid_panel_failure_retains_counts_and_partial_raw_trace(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    device = torch.device("cpu")
    config = make_config(short_spec())
    source = HMASDAgent(config, log_dir=str(tmp_path / "source"), device=device)
    original_make_env = native.make_env

    class FailingEnv:
        def __init__(self, wrapped):
            self.wrapped = wrapped
            self.steps = 0

        def reset(self, *args, **kwargs):
            return self.wrapped.reset(*args, **kwargs)

        def step(self, actions):
            self.steps += 1
            if self.steps == 2:
                raise RuntimeError("fixture transition failure")
            return self.wrapped.step(actions)

        def close(self):
            return self.wrapped.close()

    monkeypatch.setattr(
        native, "make_env", lambda candidate_config, seed: FailingEnv(
            original_make_env(candidate_config, seed)
        )
    )
    counts = {"attempt": 0, "transition": 0}

    def progress(kind, value):
        if kind in counts:
            counts[kind] += value

    trace = tmp_path / "partial.npz"
    with pytest.raises(RuntimeError, match="fixture transition failure"):
        native._evaluate_panel(
            source, config, (937001,), device, policy_seed=short_spec().seed, mode="O",
            log_dir=tmp_path / "eval", trace_path=trace, progress=progress,
        )
    assert counts == {"attempt": 1, "transition": 1}
    with np.load(trace, allow_pickle=False) as partial:
        assert bool(partial["episode_0_incomplete"])
        assert partial["episode_0_failure_type"].item() == "RuntimeError"
        assert partial["episode_0_native_reward"].shape == (1,)
        assert partial["episode_0_actions"].shape == (1, 8, 4)
        assert partial["episode_0_pre_legal_margin"].shape == (1, 8)


def test_feedback_commands_use_actual_native_motion_docking_and_blocker():
    torch.set_num_threads(1)
    config = make_config(short_spec())

    # Far station: submitted feedback requests docking and produces motion toward it.
    env = make_env(config, 937001)
    try:
        observations, info = env.reset(seed=937001)
        observations = set_margin(observations, 0, -0.01)
        decision = apply_feedback(observations, np.zeros((8, 4), dtype=np.float32), np.zeros(8, dtype=bool))
        before = np.asarray(info["state_info"]["uav_positions"]).copy()
        _, _, _, _, next_info = env.step(decision.submitted_actions)
        displacement = np.asarray(next_info["state_info"]["uav_positions"]) - before
        assert next_info["reward_info"]["uav_dock_requests"][0]
        assert np.dot(displacement[0], decision.station_vectors_m[0]) > 0.0
    finally:
        env.close()

    # Inside 160 m but outside capture: B06 sends zero movement plus dock, and the
    # unchanged wrapper supplies its slower docking motion.
    env = make_env(config, 937002)
    try:
        env.reset(seed=937002)
        raw = env.env
        raw.uav_positions[0] = raw.charging_station_positions[0] + np.asarray((100.0, 0.0, 0.0))
        raw._update_channel_state()
        raw._update_uav_connections()
        raw._compute_routing_paths()
        raw._update_return_energy_state()
        observations = np.stack([raw._get_observation(agent)["obs"] for agent in raw.agents]).astype(np.float32)
        observations = set_margin(observations, 0, -0.01)
        decision = apply_feedback(observations, np.zeros((8, 4), dtype=np.float32), np.zeros(8, dtype=bool))
        np.testing.assert_array_equal(decision.submitted_actions[0], (0, 0, 0, 1))
        before = raw.uav_positions.copy()
        _, _, _, _, next_info = env.step(decision.submitted_actions)
        displacement = np.asarray(next_info["state_info"]["uav_positions"]) - before
        assert 0.0 < np.linalg.norm(displacement[0]) < 30.0
        assert next_info["reward_info"]["uav_dock_requests"][0]
    finally:
        env.close()

    # Depleted motion is still blocked by the native wrapper.
    env = make_env(config, 937003)
    try:
        observations, info = env.reset(seed=937003)
        env.env.uav_battery_ratios[0] = 0.0
        env.env._update_return_energy_state()
        observations = np.stack([env.env._get_observation(agent)["obs"] for agent in env.env.agents]).astype(np.float32)
        observations = set_margin(observations, 0, -0.01)
        decision = apply_feedback(observations, np.zeros((8, 4), dtype=np.float32), np.zeros(8, dtype=bool))
        before = env.env.uav_positions.copy()
        _, _, _, _, next_info = env.step(decision.submitted_actions)
        displacement = np.asarray(next_info["state_info"]["uav_positions"]) - before
        np.testing.assert_array_equal(displacement[0], np.zeros(3))
    finally:
        env.close()


def test_original_reproduction_compares_common_arrays_not_npz_container(tmp_path):
    retained = tmp_path / "retained.npz"
    current = {"metric_fields": np.asarray(native.TRACE_FIELDS)}
    for index, seed in enumerate((937001, 937002)):
        current.update({
            f"episode_{index}_seed": np.asarray(seed),
            f"episode_{index}_native_reward": np.asarray((0.1, 0.2), dtype=np.float64),
            f"episode_{index}_metrics": np.zeros((2, len(native.TRACE_FIELDS)), dtype=np.float64),
            f"episode_{index}_actions": np.zeros((2, 8, 4), dtype=np.float32),
            f"episode_{index}_ends": np.asarray(((False, False), (False, True))),
        })
    np.savez_compressed(retained, **current)
    current["episode_0_diagnostic_only"] = np.ones((2, 8), dtype=np.float32)
    result = native._compare_retained_original(retained, current)
    assert result["matched"] and result["comparison"] == "array_equal"
    current["episode_1_actions"] = current["episode_1_actions"].copy()
    current["episode_1_actions"][0, 0, 0] = 1.0
    with pytest.raises(RuntimeError, match="episode_1_actions"):
        native._compare_retained_original(retained, current)


def test_production_entry_admission_sha_and_fixed_inputs(monkeypatch, tmp_path):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b06")
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")

    def admit(*args, **kwargs):
        events.append("admission")
        return {"sha": "source"}

    admission.require_admission = admit
    monkeypatch.setitem(sys.modules, admission.__name__, admission)
    candidate = types.ModuleType("experiments.candidates.uav_service_auxiliary.b06.native")

    def run(**kwargs):
        assert events == ["admission"]
        return kwargs

    candidate.run_native = run
    monkeypatch.setitem(sys.modules, candidate.__name__, candidate)
    argv = [
        "--b04-source", str(tmp_path / "b04"), "--b05-source", str(tmp_path / "b05"),
        "--out", str(tmp_path / "out"), "--launch-sha", "source",
    ]
    result = entry.main(argv)
    assert result["device_name"] == "cuda" and result["threads"] == 4
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--device", "cpu"])
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--threads", "2"])
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--seed", "914021"])
    with pytest.raises(RuntimeError, match="SHA"):
        entry.main([*argv[:-1], "other"])


def test_direct_cli_refuses_before_candidate_import_or_output(tmp_path):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b06")
    out = tmp_path / "never-created"
    result = subprocess.run(
        [
            sys.executable, entry.__file__, "--b04-source", str(tmp_path / "b04"),
            "--b05-source", str(tmp_path / "b05"), "--out", str(out),
            "--launch-sha", "0" * 40,
        ],
        cwd=entry.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0 and "missing HMASD admission" in result.stderr
    assert not out.exists()
