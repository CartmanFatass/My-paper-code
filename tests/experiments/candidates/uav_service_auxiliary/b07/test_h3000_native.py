from __future__ import annotations

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
from experiments.candidates.uav_service_auxiliary.b04.evaluation import (
    TRACE_FIELDS,
    evaluate as frozen_evaluate,
)
from experiments.candidates.uav_service_auxiliary.b04.native import B04Spec
from experiments.candidates.uav_service_auxiliary.b07 import native
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


def legal_observations():
    observations = np.zeros((8, 365), dtype=np.float32)
    suffix = observations[:, -120:]
    uavs = suffix[:, : 8 * 13].reshape(8, 8, 13)
    stations = suffix[:, 8 * 13 :].reshape(8, 2, 8)
    for agent in range(8):
        uavs[agent, agent, 3] = 1.0
        uavs[agent, agent, 12] = 0.1
        stations[agent, 0, :3] = (0.1, 0.0, 0.0)
        stations[agent, 0, 7] = 1.0
        stations[agent, 1, :3] = (-0.1, 0.0, 0.0)
        stations[agent, 1, 7] = 1.0
    return observations


@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_h3000_loop_keeps_checkpoint_rng_and_normalizers_immutable(
    tmp_path, device_name
):
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
    result, arrays = native.evaluate_panel(
        agent,
        config,
        (937001,),
        device,
        policy_seed=short_spec().seed,
        mode="O",
        log_dir=tmp_path / "b07",
        trace_path=tmp_path / "b07.npz",
    )
    middle = _rng_state()
    frozen = frozen_evaluate(
        agent,
        config,
        (937001,),
        device,
        policy_seed=short_spec().seed,
        log_dir=tmp_path / "frozen",
        trace_path=tmp_path / "frozen.npz",
    )
    after = _rng_state()
    for left, right in ((before, middle), (middle, after)):
        assert left["python"] == right["python"]
        np.testing.assert_array_equal(left["numpy"][1], right["numpy"][1])
        assert left["numpy"][2:] == right["numpy"][2:]
        assert torch.equal(left["torch"], right["torch"])
        if left["cuda"] is not None:
            assert all(torch.equal(a, b) for a, b in zip(left["cuda"], right["cuda"], strict=True))
    with np.load(tmp_path / "frozen.npz", allow_pickle=False) as reference:
        for suffix in ("seed", "native_reward", "metrics", "actions", "ends"):
            np.testing.assert_array_equal(arrays["episode_0_" + suffix], reference["episode_0_" + suffix])
    assert result["new_optimizer_updates"] == frozen["new_optimizer_updates"] == 0
    assert result["normalizers_immutable"]
    assert result["policy_sha256_before_after"] == policy == initialization_fingerprint(agent)
    assert arrays["episode_0_native_station_distance_before_m"].shape == (20, 8)


def test_config_derivation_changes_only_fixed_seven_fields_and_rejects_sources(monkeypatch):
    saved = make_config(B04Spec())
    before = native._json_active(saved)
    evaluation, report = native.derive_evaluation_config(saved)
    assert set(report["differences"]) == native.EXPECTED_CONFIG_DIFF_FIELDS
    assert evaluation.episode_length == evaluation.max_steps == 3000
    assert evaluation.num_envs == 1
    assert native._json_active(saved) == before

    mutated = make_config(B04Spec())
    mutated.episode_length = 1499
    with pytest.raises(ValueError, match="training horizon"):
        native.derive_evaluation_config(mutated)

    binding = types.SimpleNamespace(block="B04")
    checked = {"config": mutated, "spec": types.SimpleNamespace(episode_length=1500)}
    monkeypatch.setattr(native, "verify_source", lambda *args, **kwargs: checked)
    with pytest.raises(ValueError, match="training-horizon identity"):
        native.verify_training_source("unused", binding)


def test_digest_mutated_source_is_rejected_before_checkpoint_use(tmp_path):
    (tmp_path / "summary.json").write_text("{}\n")
    binding = types.SimpleNamespace(block="B04", summary_sha256="0" * 64)
    with pytest.raises(ValueError, match="summary identity mismatch"):
        native.verify_training_source(tmp_path, binding)


def test_h3000_boundary_preserves_actor_clock_and_single_reset():
    class Raw:
        n_uavs = 8
        battery_capacity_wh = 160.0

        def __init__(self):
            self.uav_battery_ratios = np.full(8, 0.75)
            self.uav_charging = np.zeros(8, dtype=bool)
            self.uav_return_energy_margins = np.full(8, 0.5)
            self.uav_dock_requests = np.zeros(8, dtype=bool)
            self.uav_target_stations = np.full(8, -1)
            self.station_occupancy = np.zeros(2, dtype=int)
            self.station_queue_lengths = np.zeros(2, dtype=int)
            self._clear_step()

        def _clear_step(self):
            self.last_energy_consumed_wh = np.zeros(8)
            self.last_energy_charged_wh = np.zeros(8)
            self.last_net_energy_charged_wh = np.zeros(8)
            self.last_charging_eligible = np.zeros(8, dtype=bool)
            self.last_charging_arrival = np.zeros(8, dtype=bool)
            self.charging_wait_steps = np.zeros(8, dtype=int)
            self.last_min_station_distance_before = np.full(8, 1000.0)
            self.last_min_station_distance_after = np.full(8, 1000.0)

    class Env:
        def __init__(self):
            self.env = Raw()
            self.steps = 0
            self.obs = legal_observations()

        def reset(self, seed):
            del seed
            self.steps = 0
            return self.obs.copy(), {
                "state": np.zeros(3, dtype=np.float32),
                "state_info": {"uav_positions": np.zeros((8, 3))},
            }

        def step(self, actions):
            del actions
            self.steps += 1
            self.env._clear_step()
            metrics = {field: 0.0 for field in TRACE_FIELDS}
            metrics["return_penalty_coefficient"] = 2.0
            metrics["battery_min_ratio"] = 0.75
            done = self.steps == 3000
            return self.obs.copy(), 0.0, False, done, {
                "next_state": np.zeros(3, dtype=np.float32),
                "state_info": {"uav_positions": np.zeros((8, 3))},
                "reward_info": metrics,
            }

    class Evaluator:
        def __init__(self):
            self.reset_calls = 0
            self.steps = []

        def reset_env_state(self, env_id):
            assert env_id == 0
            self.reset_calls += 1

        def step(self, state, observations, step, done, **kwargs):
            del state, observations, done, kwargs
            current = int(step[0])
            self.steps.append(current)
            data = {
                "agent_skills": np.zeros((1, 8), dtype=int),
                "team_skills": np.zeros((1, 8), dtype=int),
                "skill_changed": np.full((1, 8), current % 10 == 0),
            }
            return np.zeros((1, 8, 4), dtype=np.float32), None, data

    evaluator, env = Evaluator(), Env()
    world, _, _, _, ends, diagnostics = native.evaluate_world(
        evaluator,
        env,
        types.SimpleNamespace(episode_length=3000),
        937001,
        "O",
    )
    assert evaluator.reset_calls == 1
    assert evaluator.steps[1499:1502] == [1499, 1500, 1501]
    assert not ends[1499].any() and ends[-1, 1]
    assert world["actual_length"] == 3000 and world["second_half"]["actual_steps"] == 1500
    np.testing.assert_array_equal(np.flatnonzero(diagnostics["skill_changed"][:, 0])[-2:], (2980, 2990))


def test_native_h3000_time_limit_and_terminal_pbrs_semantics():
    config, _ = native.derive_evaluation_config(make_config(B04Spec()))
    env = make_env(config, 937001)
    try:
        env.reset(seed=937001)
        env.env.current_step = 1499
        _, _, terminated, truncated, _ = env.step(np.zeros((8, 4), dtype=np.float32))
        assert not terminated and not truncated
        env.env.current_step = 2999
        _, _, terminated, truncated, info = env.step(np.zeros((8, 4), dtype=np.float32))
        reward_info = info["reward_info"]
        assert not terminated and truncated
        assert reward_info["graph_potential_delta"] == pytest.approx(
            -reward_info["graph_potential_before"]
        )
    finally:
        env.close()


def test_energy_ledger_distinguishes_negative_net_and_capacity_clipping():
    raw = types.SimpleNamespace(
        n_uavs=2,
        battery_capacity_wh=160.0,
        uav_battery_ratios=np.asarray((0.49375, 0.0)),
        last_energy_consumed_wh=np.asarray((2.0, 1.0)),
        last_energy_charged_wh=np.asarray((1.0, 0.0)),
        last_net_energy_charged_wh=np.asarray((0.0, 0.0)),
        uav_charging=np.asarray((True, False)),
        last_charging_eligible=np.asarray((True, False)),
        last_charging_arrival=np.asarray((True, False)),
        charging_wait_steps=np.asarray((0, 2)),
        last_min_station_distance_before=np.asarray((50.0, 300.0)),
        last_min_station_distance_after=np.asarray((45.0, 295.0)),
    )
    ledger = native.energy_ledger(raw, np.asarray((0.5, 0.001)), np.zeros(2, dtype=bool))
    assert ledger["native_clipped_positive_net_charge_wh"][0] == 0.0
    assert ledger["signed_stored_energy_delta_wh"][0] == pytest.approx(-1.0)
    assert ledger["lower_capacity_clipped"][1]
    assert ledger["capacity_clipping_residual_wh"][1] == pytest.approx(0.84)
    assert ledger["charging_capture"][0] and ledger["charging_admitted"][0]
    np.testing.assert_array_equal(ledger["native_station_distance_after_m"], (45.0, 295.0))


def _summary_fixture(length, qos):
    rewards = np.ones(length, dtype=np.float64)
    metrics = np.zeros((length, len(TRACE_FIELDS)), dtype=np.float64)
    metrics[:, TRACE_FIELDS.index("qos_satisfaction_ratio")] = qos
    metrics[:, TRACE_FIELDS.index("delivered_end_to_end_throughput_mbps")] = 2 * qos
    ends = np.zeros((length, 2), dtype=bool)
    ends[-1, 0] = length < 3000
    shape = (length, 8)
    diagnostics = {
        "episode_initial_physical_battery": np.ones(8),
        "pre_legal_margin": np.ones(shape),
        "physical_post_return_margin": np.ones(shape),
        "physical_post_battery": np.full(shape, 0.5),
        "actual_displacement_m": np.zeros((length, 8, 3)),
        "charger_input_wh": np.zeros(shape),
        "signed_stored_energy_delta_wh": np.zeros(shape),
        "charging_eligible": np.zeros(shape, dtype=bool),
        "charging_capture": np.zeros(shape, dtype=bool),
        "charging_admitted": np.zeros(shape, dtype=bool),
        "charging_arrival": np.zeros(shape, dtype=bool),
        "charge_started": np.zeros(shape, dtype=bool),
        "charge_ended": np.zeros(shape, dtype=bool),
        "consumed_wh": np.ones(shape),
        "native_clipped_positive_net_charge_wh": np.zeros(shape),
        "capacity_clipping_residual_wh": np.zeros(shape),
        "upper_capacity_clipped": np.zeros(shape, dtype=bool),
        "lower_capacity_clipped": np.zeros(shape, dtype=bool),
        "mode": np.zeros(shape, dtype=bool),
        "entry": np.zeros(shape, dtype=bool),
        "exit": np.zeros(shape, dtype=bool),
        "command_changed": np.zeros(shape, dtype=bool),
    }
    return native.episode_summary(1, rewards, metrics, ends, diagnostics)


def test_early_and_unequal_lengths_keep_planned_denominator_and_censoring():
    early = _summary_fixture(1200, np.zeros(1200))
    full = _summary_fixture(3000, np.ones(3000))
    assert early["planned_window_qos"] == 0.0
    assert early["second_half"]["actual_steps"] == 0
    assert early["descriptive_250_step_bins"][5]["actual_steps"] == 0
    assert early["right_censored_service_free_interval"]
    paired = native.paired_summary(
        {"worlds": [early]},
        {"worlds": [{**full, "seed": early["seed"]}]},
    )
    assert paired["worlds"][0]["effects_F_minus_O"]["actual_length"] == 1800
    assert "actual_length_F_minus_O_max" in paired["aggregate"]


def test_telemetry_failure_after_transition_retains_partial_arrays_and_counts(
    tmp_path, monkeypatch
):
    torch.set_num_threads(1)
    config = make_config(short_spec())
    device = torch.device("cpu")
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    counts = {"attempt": 0, "transition": 0}

    def progress(kind, value):
        if kind in counts:
            counts[kind] += value

    monkeypatch.setattr(
        native,
        "energy_ledger",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("telemetry failure")),
    )
    trace = tmp_path / "partial.npz"
    with pytest.raises(RuntimeError, match="telemetry failure"):
        native.evaluate_panel(
            agent,
            config,
            (937001,),
            device,
            policy_seed=short_spec().seed,
            mode="O",
            log_dir=tmp_path / "eval",
            trace_path=trace,
            progress=progress,
        )
    assert counts == {"attempt": 1, "transition": 1}
    with np.load(trace, allow_pickle=False) as partial:
        assert bool(partial["episode_0_incomplete"])
        assert partial["episode_0_native_reward"].shape == (1,)
        assert partial["episode_0_actions"].shape == (1, 8, 4)
        assert partial["episode_0_metrics"].shape == (0,)
        assert partial["episode_0_raw_reward_info_metrics"].shape == (1, len(TRACE_FIELDS))
        assert partial["episode_0_raw_physical_pre_battery"].shape == (1, 8)
        assert partial["episode_0_raw_physical_post_battery"].shape == (1, 8)
        assert partial["episode_0_raw_energy_consumed_wh"].shape == (1, 8)


def test_second_world_constructor_failure_retains_completed_world(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    config = make_config(short_spec())
    device = torch.device("cpu")
    agent = HMASDAgent(config, log_dir=str(tmp_path / "agent"), device=device)
    real_make_env = native.make_env
    calls = 0

    def fail_second(candidate_config, seed):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("second constructor failure")
        return real_make_env(candidate_config, seed)

    monkeypatch.setattr(native, "make_env", fail_second)
    trace = tmp_path / "partial.npz"
    with pytest.raises(RuntimeError, match="second constructor failure"):
        native.evaluate_panel(
            agent,
            config,
            (937001, 937002),
            device,
            policy_seed=short_spec().seed,
            mode="O",
            log_dir=tmp_path / "eval",
            trace_path=trace,
        )
    with np.load(trace, allow_pickle=False) as partial:
        assert partial["episode_0_native_reward"].shape == (20,)
        assert partial["episode_0_raw_charger_input_wh"].shape == (20, 8)
        assert partial["partial_failure_type"].item() == "RuntimeError"


def test_production_cli_requires_admission_sha_cuda_and_fixed_inputs(monkeypatch, tmp_path):
    entry = importlib.import_module("scripts.run_uav_service_auxiliary_b07")
    events = []
    admission = types.ModuleType("scripts.hmasd_admission")
    admission.require_admission = lambda *args, **kwargs: events.append("admission") or {"sha": "source"}
    monkeypatch.setitem(sys.modules, admission.__name__, admission)
    candidate = types.ModuleType("experiments.candidates.uav_service_auxiliary.b07.native")
    candidate.run_native = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, candidate.__name__, candidate)
    argv = [
        "--b04-source", str(tmp_path / "b04"),
        "--b05-source", str(tmp_path / "b05"),
        "--out", str(tmp_path / "out"),
        "--launch-sha", "source",
    ]
    result = entry.main(argv)
    assert events == ["admission"]
    assert result["device_name"] == "cuda" and result["threads"] == 4
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--device", "cpu"])
    with pytest.raises(SystemExit):
        entry.parse_args([*argv, "--threads", "2"])
    with pytest.raises(RuntimeError, match="SHA"):
        entry.main([*argv[:-1], "other"])

    out = tmp_path / "never-created"
    refused = subprocess.run(
        [
            sys.executable,
            entry.__file__,
            "--b04-source", str(tmp_path / "b04"),
            "--b05-source", str(tmp_path / "b05"),
            "--out", str(out),
            "--launch-sha", "0" * 40,
        ],
        cwd=entry.ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert refused.returncode != 0 and "missing HMASD admission" in refused.stderr
    assert not out.exists()
