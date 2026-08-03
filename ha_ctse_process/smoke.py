"""Lightweight standalone HA-CTSE smoke checks with log-file output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

from ha_ctse_process.config import Config
from ha_ctse_process import checkpoint_io
from ha_ctse_process import standalone_evaluation as process_evaluation
from ha_ctse_process.standalone_agent import Segment, StandaloneProcessAgent


def make_config():
    cfg = Config()
    cfg.n_Z = 3
    cfg.n_z = 3
    cfg.state_dim = 8
    cfg.skill_lifetime_candidates = (1, 2)
    cfg.hidden_size = 16
    cfg.low_rnn_hidden_size = 16
    cfg.low_sequence_length = 2
    cfg.low_sequence_batch_size = 2
    cfg.low_ppo_epochs = 1
    cfg.low_value_loss_coef = 1.0
    cfg.process_reward_coef = 1.0
    cfg.process_reward_warmup_steps = 0
    cfg.process_shortcut_margin = 0.1
    cfg.process_shortcut_margin_coef = 0.5
    cfg.normalize_process_outcomes = False
    cfg.skill_effect_discovery_on = True
    cfg.skill_effect_reward_on = False
    cfg.skill_effect_reward_injection = "none"
    cfg.skill_effect_horizons = (1, 2)
    cfg.skill_effect_stride = 1
    cfg.skill_effect_max_windows = 32
    cfg.skill_effect_hidden_dim = 16
    cfg.skill_effect_intervention_probe_on = True
    cfg.skill_effect_intervention_max_samples = 16
    cfg.skill_force_probe_on = True
    cfg.enable_skill_forcing_reward = False
    cfg.skill_force_reward_injection = "low_only"
    cfg.skill_force_disc_coef = 0.02
    cfg.skill_force_effect_coef = 0.01
    cfg.skill_force_duration_entropy_coef = 0.0
    cfg.skill_force_warmup_steps = 0
    cfg.skill_force_clip = 0.05
    cfg.skill_force_shortcut_margin = 0.0
    cfg.skill_force_kill_on_shortcut = True
    cfg.skill_force_use_comm_fields = False
    cfg.lr_discoverer_actor = 1e-3
    cfg.lr_coordinator = 1e-3
    cfg.lr_process_encoder = 1e-3
    cfg.process_encoder_embedding_dim = 8
    cfg.opt_compact_dim = 8
    cfg.opt_num_prototypes = 2
    cfg.team_code_dim = 8
    cfg.num_team_codes = 3
    cfg.edit_penalty_alpha = 0.0
    cfg.switch_penalty_beta = 0.0
    cfg.opt_cd_coef = 0.0
    cfg.opt_cmi_coef = 0.0
    cfg.scenario = "base"
    return cfg


def make_args(log_dir: Path):
    return SimpleNamespace(
        config="ha_ctse_process.config",
        preset="",
        scenario="base",
        seed=1,
        skill_interval=2,
        eval_max_steps=3,
        log_dir=str(log_dir),
    )


def make_agent(config):
    return StandaloneProcessAgent(
        obs_dim=4,
        action_dim=3,
        n_agents=2,
        config=config,
        device="cpu",
        action_space_type="discrete",
        num_envs=1,
        state_dim=8,
    )


class DummyEvalEnv:
    obs_dim = 4
    action_dim = 3
    n_uavs = 2
    state_dim = 8

    def __init__(self):
        self.step_count = 0

    def reset(self, seed=None):
        self.step_count = 0
        obs = np.zeros((self.n_uavs, self.obs_dim), dtype=np.float32)
        return obs, {"state": np.zeros(self.state_dim, dtype=np.float32)}

    def step(self, actions):
        self.step_count += 1
        obs = np.full((self.n_uavs, self.obs_dim), self.step_count, dtype=np.float32)
        info = {
            "next_state": np.full(self.state_dim, self.step_count, dtype=np.float32),
            "reward_info": {
                "coverage_ratio": 0.5,
                "qos_satisfaction": 0.25,
                "system_throughput_mbps": 7.0,
                "battery_min_ratio": 0.8,
            },
        }
        return obs, 1.0, self.step_count >= 2, False, info

    def close(self):
        return None


def run_smoke(log_dir: Path) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    cfg = make_config()
    args = make_args(log_dir)
    agent = make_agent(cfg)

    expected = next(agent.high.parameters()).detach().clone()
    ckpt_path = log_dir / "standalone_smoke.pt"
    checkpoint_io.save_checkpoint(ckpt_path, agent, args, cfg, total_steps=12, update_idx=3)
    restored = make_agent(cfg)
    with torch.no_grad():
        next(restored.high.parameters()).add_(1.0)
    total_steps, update_idx = checkpoint_io.load_checkpoint(ckpt_path, restored)
    checkpoint_ok = (
        total_steps == 12
        and update_idx == 3
        and torch.allclose(next(restored.high.parameters()).detach(), expected)
    )

    segment = Segment(
        env_id=0,
        agent_id=1,
        skill=0,
        duration_idx=0,
        start_step=0,
        high_obs=np.zeros(4, dtype=np.float32),
        high_logp=0.0,
        high_value=0.0,
        high_entropy=0.0,
        high_state=np.zeros(8, dtype=np.float32),
        high_joint_obs=np.zeros((2, 4), dtype=np.float32),
    )
    segment.append(
        obs=np.zeros(4, dtype=np.float32),
        action=np.array([1], dtype=np.float32),
        reward=0.25,
        next_obs=np.ones(4, dtype=np.float32),
        rollout_idx=0,
        reward_info={
            "coverage_ratio": 0.2,
            "qos_satisfaction": 0.1,
            "full_network_disconnect": 1.0,
            "uavs_with_backhaul": 0.0,
            "connectivity_ratio": 0.0,
            "current_backhaul_served_users": 0.0,
            "backhaul_outage_ratio": 1.0,
        },
    )
    segment.append(
        obs=np.ones(4, dtype=np.float32),
        action=np.array([2], dtype=np.float32),
        reward=0.5,
        next_obs=np.ones(4, dtype=np.float32) * 2.0,
        rollout_idx=1,
        reward_info={
            "coverage_ratio": 0.3,
            "qos_satisfaction": 0.2,
            "full_network_disconnect": 0.0,
            "uavs_with_backhaul": 2.0,
            "connectivity_ratio": 1.0,
            "current_backhaul_served_users": 3.0,
            "backhaul_outage_ratio": 0.0,
        },
    )
    agent.segments.completed = [segment]
    rollout = SimpleNamespace(rewards=[np.zeros(2, dtype=np.float32), np.zeros(2, dtype=np.float32)])
    metrics = agent.process_update(rollout)
    reward_injection_ok = (
        metrics["process_segments"] == 1.0
        and rollout.rewards[0][0] == 0.0
        and rollout.rewards[1][0] == 0.0
        and rollout.rewards[0][1] == 0.0
        and rollout.rewards[1][1] == 0.0
        and metrics["process_reward_mean"] != 0.0
        and metrics["process_reward_high_mean"] == 0.0
        and metrics["process_reward_low_mean"] == 0.0
    )
    credit_diagnostics_ok = (
        metrics["credit_probe_available_frac"] == 1.0
        and metrics["credit_recovery_rate"] == 1.0
        and metrics["credit_collapse_rate"] == 0.0
        and metrics["credit_delta_connectivity_ratio_mean"] == 1.0
        and metrics["credit_delta_backhaul_served_users_mean"] == 3.0
        and metrics["credit_delta_backhaul_outage_ratio_mean"] == -1.0
    )
    residual_metrics_ok = (
        "process_residual_mi_mean" in metrics
        and "process_shortcut_max_acc" in metrics
        and "posterior_acc_minus_shortcut_max" in metrics
    )
    skill_effect_probe_ok = (
        metrics.get("effect_windows", 0.0) > 0.0
        and "effect_gain_mean" in metrics
        and "effect_gain_group_balanced_mean" in metrics
        and "effect_gain_horizon_0" in metrics
        and "effect_action_skill_eta2" in metrics
        and "effect_target_skill_eta2" in metrics
        and "effect_observed_target_skill_l2_mean" in metrics
        and "effect_observed_action_skill_l2_mean" in metrics
        and "effect_observed_action_target_corr" in metrics
        and "effect_endstate_available_frac" in metrics
        and "effect_window_mean_available_frac" in metrics
        and metrics.get("effect_intervention_active", 0.0) == 1.0
        and metrics.get("effect_intervention_samples", 0.0) > 0.0
        and "effect_intervention_action_l2_mean" in metrics
        and "effect_intervention_pred_effect_l2_mean" in metrics
        and metrics.get("effect_reward_low_mean", 1.0) == 0.0
        and metrics.get("effect_reward_applied_steps", 1.0) == 0.0
        and "force_disc_acc" in metrics
        and "force_shortcut_best_acc" in metrics
        and "force_disc_residual_mean" in metrics
        and "force_effect_residual_mean" in metrics
        and metrics.get("force_gate_active", 1.0) == 0.0
        and metrics.get("force_reward_low_mean", 1.0) == 0.0
        and metrics.get("force_reward_applied_steps", 1.0) == 0.0
        and rollout.rewards[0][1] == 0.0
        and rollout.rewards[1][1] == 0.0
    )

    eval_agent = make_agent(cfg)
    eval_agent.active_skills[:] = np.array([[2, 1]])
    eval_agent.duration_remaining[:] = np.array([[4, 5]])
    eval_agent.skill_age[:] = np.array([[3, 2]])
    eval_agent.has_active_skill[:] = True
    active_before = eval_agent.active_skills.copy()
    duration_before = eval_agent.duration_remaining.copy()
    age_before = eval_agent.skill_age.copy()
    has_before = eval_agent.has_active_skill.copy()
    old_create_env = process_evaluation.create_env
    process_evaluation.create_env = lambda *args, **kwargs: DummyEvalEnv()
    try:
        eval_metrics = process_evaluation.evaluate(eval_agent, cfg, args, episodes=1, total_steps=10)
    finally:
        process_evaluation.create_env = old_create_env
    eval_restore_ok = (
        eval_metrics["reward_mean"] == 2.0
        and eval_metrics["coverage"] == 0.5
        and np.array_equal(eval_agent.active_skills, active_before)
        and np.array_equal(eval_agent.duration_remaining, duration_before)
        and np.array_equal(eval_agent.skill_age, age_before)
        and np.array_equal(eval_agent.has_active_skill, has_before)
    )

    return {
        "checkpoint_ok": bool(checkpoint_ok),
        "reward_injection_ok": bool(reward_injection_ok),
        "credit_diagnostics_ok": bool(credit_diagnostics_ok),
        "residual_metrics_ok": bool(residual_metrics_ok),
        "skill_effect_probe_ok": bool(skill_effect_probe_ok),
        "eval_restore_ok": bool(eval_restore_ok),
        "process_metrics": metrics,
        "eval_metrics": eval_metrics,
        "all_ok": bool(
            checkpoint_ok
            and reward_injection_ok
            and credit_diagnostics_ok
            and residual_metrics_ok
            and skill_effect_probe_ok
            and eval_restore_ok
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", default="logs/ha_ctse_process_smoke")
    args = parser.parse_args()
    log_dir = Path(args.log_dir)
    result = run_smoke(log_dir)
    out_path = log_dir / "smoke_result.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"ha_ctse_process_smoke result={result['all_ok']} path={out_path}")
    if not result["all_ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
