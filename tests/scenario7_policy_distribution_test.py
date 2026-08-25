from types import SimpleNamespace
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
gymnasium = pytest.importorskip("gymnasium")

from config_1 import Config
from hmasd.agent import HMASDAgent
from hmasd.r_mappo_utils import ACTLayer, DiagGaussian, TanhDiagGaussian
from train_multiproc_config_1 import (
    build_structured_log_dir,
    evaluate_scenario7_comparison_gate,
    save_scenario7_training_plots,
)


def make_args(distribution="tanh_gaussian"):
    return SimpleNamespace(
        continuous_action_distribution=distribution,
        continuous_logstd_init=-1.0,
        continuous_logstd_min=-5.0,
        continuous_logstd_max=0.0,
    )


def test_scenario7_tanh_gaussian_is_bounded_and_log_prob_is_consistent():
    layer = ACTLayer(
        gymnasium.spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32),
        inputs_dim=16,
        use_orthogonal=True,
        gain=0.01,
        args=make_args(),
    )
    assert isinstance(layer.action_out, TanhDiagGaussian)

    features = torch.randn(128, 16)
    actions, sampled_log_probs = layer(features)
    evaluated_log_probs, entropy = layer.evaluate_actions(features, actions)

    assert torch.all(actions <= 1.0)
    assert torch.all(actions >= -1.0)
    assert torch.allclose(sampled_log_probs, evaluated_log_probs, atol=2e-4, rtol=2e-4)
    assert torch.isfinite(entropy)


def test_scenario7_logstd_is_initialized_and_clamped_per_forward():
    distribution = TanhDiagGaussian(8, 4, args=make_args())
    np.testing.assert_allclose(
        distribution.logstd._bias.detach().cpu().numpy().reshape(-1),
        np.full(4, -1.0),
    )

    with torch.no_grad():
        distribution.logstd._bias.fill_(10.0)
    dist = distribution._distribution(torch.zeros(2, 8))
    assert torch.all(dist.scale <= 1.0)

    with torch.no_grad():
        distribution.logstd._bias.fill_(-10.0)
    dist = distribution._distribution(torch.zeros(2, 8))
    assert torch.all(dist.scale >= np.exp(-5.0) - 1e-7)


def test_other_continuous_scenarios_keep_the_existing_gaussian():
    layer = ACTLayer(
        gymnasium.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
        inputs_dim=8,
        use_orthogonal=True,
        gain=0.01,
        args=make_args("gaussian"),
    )
    assert isinstance(layer.action_out, DiagGaussian)


def test_scenario7_entropy_coefficient_is_fixed():
    config = Config("S7-S3")
    assert config.config_revision == "unified-scenario7-qos-safety-pbrs-v5-20260620"
    assert config.active_config_revision == "scenario7-qos-safety-pbrs-v5"
    assert config.scenario7_reward_model == "constrained_qos_safety_pbrs_v2"
    assert config.scenario7_reward_variant == "qos_fixed_safety_graph_pbrs"
    assert config.scenario7_experiment_arm == "C"
    assert config.battery_capacity_wh == 160.0
    assert config.return_cost_cap == 1.0
    assert config.gamma == 0.99
    assert config.return_margin_scale == 0.05
    assert config.lambda_return == 2.0
    assert config.cutoff_event_penalty == 5.0
    assert config.depletion_event_penalty == 10.0
    assert config.lambda_l == 0.005
    assert config.lambda_l_initial == 0.005
    assert config.lambda_l_final == 0.005
    assert config.use_entropy_annealing is False
    assert config.k == 50
    assert config.total_timesteps == 9_600_000
    assert config.scenario7_intermediate_eval_episodes == 20
    assert config.scenario7_key_eval_episodes == 100
    assert Path(config.scenario7_baseline_metrics_path).is_file()


def test_old_three_dimensional_checkpoint_is_rejected(tmp_path):
    checkpoint_path = tmp_path / "old_scenario7.pt"
    torch.save({
        "policy_interface": {
            "action_dim": 3,
            "action_space_type": "continuous",
            "continuous_action_distribution": "gaussian",
            "scenario7_interface_version": 1,
        }
    }, checkpoint_path)

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = Config("S7-S3")
    agent.device = torch.device("cpu")
    with pytest.raises(ValueError, match="Scenario 7"):
        agent.load_model(checkpoint_path)


def test_previous_reward_model_checkpoint_is_rejected(tmp_path):
    checkpoint_path = tmp_path / "scenario7_old_reward.pt"
    torch.save({
        "policy_interface": {
            "action_dim": 4,
            "action_space_type": "continuous",
            "continuous_action_distribution": "tanh_gaussian",
            "scenario7_interface_version": 3,
            "scenario7_reward_model": "constrained_energy_efficiency_pbrs_v1",
            "scenario7_reward_variant": "constrained_ee_graph_pbrs",
        }
    }, checkpoint_path)

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = Config("S7-S3")
    agent.device = torch.device("cpu")
    with pytest.raises(ValueError, match="reward模型"):
        agent.load_model(checkpoint_path)


def test_cross_skill_interval_checkpoint_is_rejected(tmp_path):
    checkpoint_path = tmp_path / "scenario7_k10.pt"
    torch.save({
        "policy_interface": {
            "action_dim": 4,
            "action_space_type": "continuous",
            "continuous_action_distribution": "tanh_gaussian",
            "scenario7_interface_version": 3,
            "scenario7_reward_model": "constrained_qos_safety_pbrs_v2",
            "scenario7_reward_variant": "qos_fixed_safety_graph_pbrs",
            "scenario7_experiment_arm": "C",
            "battery_capacity_wh": 160.0,
            "return_cost_cap": 1.0,
        },
        "training_interface": {
            "skill_interval": 10,
            "rollout_length": 500,
            "episode_length": 1500,
        },
    }, checkpoint_path)

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = Config("S7-S3")
    agent.device = torch.device("cpu")
    with pytest.raises(ValueError, match="技能间隔不兼容"):
        agent.load_model(checkpoint_path)


def test_v1_or_200wh_checkpoint_is_rejected_by_arm_c(tmp_path):
    checkpoint_path = tmp_path / "scenario7_v1_200wh.pt"
    torch.save({
        "policy_interface": {
            "action_dim": 4,
            "action_space_type": "continuous",
            "continuous_action_distribution": "tanh_gaussian",
            "scenario7_interface_version": 3,
            "scenario7_reward_model": "constrained_qos_safety_pbrs_v1",
            "scenario7_reward_variant": "qos_fixed_safety_unbounded_graph_pbrs",
            "scenario7_experiment_arm": "A",
            "battery_capacity_wh": 200.0,
            "return_cost_cap": None,
        },
        "training_interface": {
            "skill_interval": 50,
            "rollout_length": 500,
            "episode_length": 1500,
        },
    }, checkpoint_path)

    agent = HMASDAgent.__new__(HMASDAgent)
    agent.config = Config("S7-S3")
    agent.device = torch.device("cpu")
    with pytest.raises(ValueError, match="检查点接口不兼容"):
        agent.load_model(checkpoint_path)


def test_scenario7_comparison_gate_decisions(tmp_path):
    config = Config("S7-S3")
    config.scenario7_comparison_gate_enabled = True
    baseline_path = tmp_path / "arm_a_diagnostics.json"
    baseline_path.write_text(
        """{
          "training_steps": 2400000,
          "experiment_arm": "A",
          "reward_model": "constrained_qos_safety_pbrs_v1",
          "battery_capacity_wh": 200.0,
          "return_cost_cap": null,
          "median_episode_qos_utility": 0.50,
          "q10_episode_reward": -1000.0,
          "return_violation_episode_ratio": 0.40
        }""",
        encoding="utf-8",
    )
    config.scenario7_baseline_metrics_path = str(baseline_path)
    passing = evaluate_scenario7_comparison_gate(config, {
        "training_steps": 2_400_000,
        "episode_count": 100,
        "median_episode_qos_utility": 0.48,
        "q10_episode_reward": -400.0,
        "return_violation_episode_ratio": 0.20,
        "effective_charging_episode_ratio": 0.50,
        "catastrophe_episode_ratio": 0.05,
        "numerical_failure_count": 0,
    })
    assert passing["passed"]
    assert not passing["should_stop"]

    failing = evaluate_scenario7_comparison_gate(config, {
        "training_steps": 2_400_000,
        "episode_count": 100,
        "median_episode_qos_utility": 0.40,
        "q10_episode_reward": -800.0,
        "return_violation_episode_ratio": 0.35,
        "effective_charging_episode_ratio": 0.20,
        "catastrophe_episode_ratio": 0.10,
        "numerical_failure_count": 0,
    })
    assert not failing["passed"]
    assert failing["should_stop"]

    config.apply_scenario7_experiment_arm("A")
    baseline = evaluate_scenario7_comparison_gate(config, {
        "training_steps": 2_400_000,
        "episode_count": 100,
    })
    assert baseline["reason"] == "arm_a_baseline_complete"
    assert baseline["should_stop"]


def test_scenario7_experiment_arms_change_only_reward_physics_contract():
    config = Config("S7-S3")

    config.apply_scenario7_experiment_arm("A")
    assert config.scenario7_reward_model == "constrained_qos_safety_pbrs_v1"
    assert config.battery_capacity_wh == 200.0
    assert config.return_cost_cap is None

    config.apply_scenario7_experiment_arm("B")
    assert config.scenario7_reward_model == "constrained_qos_safety_pbrs_v2"
    assert config.battery_capacity_wh == 200.0
    assert config.return_cost_cap == 1.0

    config.apply_scenario7_experiment_arm("C")
    assert config.scenario7_reward_model == "constrained_qos_safety_pbrs_v2"
    assert config.battery_capacity_wh == 160.0
    assert config.return_cost_cap == 1.0
    assert config.gamma == 0.99
    assert config.k == 50


def test_structured_log_directory_records_skill_interval(tmp_path):
    config = Config("S7-S3")
    args = SimpleNamespace(
        algorithm="hmasd",
        scenario="energy",
        preset="S7-S3",
        mode="train",
        config="config_1",
        seed=1,
        collector_backend="sharded",
        training_metrics_level="light",
        num_workers=20,
        envs_per_worker=2,
        metrics_mode="light",
        exp_name="hmasd_experiment",
        log_dir=str(tmp_path),
        run_timestamp="20260619_000000",
    )
    path = build_structured_log_dir(args, config)
    assert "k-50" in path
    assert "arm-C" in path
    assert "battery-160wh" in path


def test_scenario7_training_diagnostic_plots_are_created(tmp_path):
    rewards = np.linspace(-500.0, 300.0, 120)
    summaries = [
        {
            "episode_qos_utility_sum": float(episode),
            "episode_return_risk_penalty_sum": float(120 - episode),
            "episode_graph_pbrs_sum": float(np.sin(episode / 10.0)),
            "episode_event_penalty_sum": float(episode % 7 == 0),
            "episode_return_risk_steps": float(episode < 80),
            "episode_charging_session_count": float(episode > 40),
            "episode_first_effective_charge_step": (
                float(1000 - episode) if episode > 40 else -1.0
            ),
        }
        for episode in range(120)
    ]

    save_scenario7_training_plots(
        str(tmp_path),
        rewards.tolist(),
        summaries,
        window=20,
    )

    for filename in (
        "rewards_distribution.png",
        "scenario7_reward_components.png",
        "scenario7_tail_risk.png",
        "scenario7_charging_progress.png",
    ):
        assert (tmp_path / filename).is_file()
