"""Serialization-family checks for the R39A fixed-HMASD analyzer."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import torch


_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_r39a_fixed_hmasd_anchor.py"
)
_SPEC = importlib.util.spec_from_file_location("r39a_anchor_analyzer", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
analyzer = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(analyzer)


def _optimizer_state() -> dict[object, object]:
    return {
        "param_groups": [{"params": [0]}],
        "state": {
            0: {
                "step": torch.tensor(1),
                "exp_avg": torch.zeros(1),
                "exp_avg_sq": torch.zeros(1),
            }
        },
    }


def _runtime() -> tuple[SimpleNamespace, SimpleNamespace]:
    agent = SimpleNamespace(
        skill_coordinator=torch.nn.Linear(2, 2),
        skill_discoverer=torch.nn.Linear(2, 2),
        team_discriminator=torch.nn.Linear(2, 2),
        individual_discriminator=torch.nn.Linear(2, 2),
        team_discriminator_optimizer=object(),
        individual_discriminator_optimizer=object(),
        team_discriminator_scheduler=None,
        individual_discriminator_scheduler=None,
    )
    return agent, SimpleNamespace(state_dim=7, obs_dim=11)


def _valid_checkpoint(agent: SimpleNamespace) -> dict[object, object]:
    config_values = {
        **analyzer.EXPECTED_CHECKPOINT_CONFIG,
        "state_dim": 7,
        "obs_dim": 11,
        "disable_high_level_training": False,
        "disable_discriminator_training": False,
        "disable_discriminator_rewards": False,
        **{name: 0.0 for name in analyzer.SHAPING_FIELDS},
    }
    checkpoint: dict[object, object] = {
        "skill_coordinator": agent.skill_coordinator.state_dict(),
        "skill_discoverer": agent.skill_discoverer.state_dict(),
        "team_discriminator": agent.team_discriminator.state_dict(),
        "individual_discriminator": agent.individual_discriminator.state_dict(),
        "coordinator_optimizer": _optimizer_state(),
        "discoverer_actor_optimizer": _optimizer_state(),
        "discoverer_critic_optimizer": _optimizer_state(),
        "discriminator_optimizer": _optimizer_state(),
        "config": SimpleNamespace(**config_values),
        "policy_interface": dict(analyzer.EXPECTED_POLICY_INTERFACE),
        "training_interface": {
            "skill_interval": analyzer.SKILL_INTERVAL,
            "rollout_length": analyzer.ROLLOUT_LENGTH,
            "episode_length": analyzer.EPISODE_STEPS,
        },
        "training_diagnostics": {
            "high_replay_likelihood": {
                "global_max_abs_error": 0.0,
                "global_sample_count": 1,
            }
        },
        "scenario7_safety_dual_state": {},
        "valuenorm_state": {
            "coordinator": {"mean": 0.0, "var": 1.0, "count": 1.0},
            "discoverer": {"mean": 0.0, "var": 1.0, "count": 1.0},
        },
    }
    return checkpoint


def _valid_summary(checkpoint_path: Path) -> dict[str, object]:
    return {
        "contract_total_steps": analyzer.TOTAL_TIMESTEPS,
        "outer_updates": analyzer.EXPECTED_OUTER_UPDATES,
        "successful_outer_updates": analyzer.EXPECTED_OUTER_UPDATES,
        "failed_outer_updates": 0,
        "r39a_strict_contract": True,
        "total_steps": analyzer.TOTAL_TIMESTEPS,
        "r39a_contract": {
            "seed": analyzer.TRAIN_SEED,
            "preset": "S7-S1",
            "n_agents": 8,
            "action_dim": 4,
            "scenario7_interface_version": 3,
            "scenario7_experiment_arm": "C",
            "scenario7_reward_variant": "qos_fixed_safety",
            "use_graph_pbrs": False,
            "num_envs": analyzer.NUM_ENVS,
            "rollout_length": analyzer.ROLLOUT_LENGTH,
            "skill_interval": analyzer.SKILL_INTERVAL,
            "total_timesteps": analyzer.TOTAL_TIMESTEPS,
            "algorithm": "hmasd_original",
        },
        "final_checkpoint_path": str(checkpoint_path),
        "numerical_stability": {"total_repairs": 0},
    }


def _validate(
    checkpoint: dict[object, object], tmp_path: Path
) -> tuple[list[str], dict[str, object]]:
    agent, env = _runtime()
    checkpoint_path = tmp_path / "checkpoint.pt"
    failures: list[str] = []
    evidence = analyzer._validate_checkpoint_and_summary(
        checkpoint,
        _valid_summary(checkpoint_path),
        checkpoint_path,
        agent,
        env,
        failures,
    )
    return failures, evidence


def test_analyzer_accepts_strict_legacy_combined_discriminator_optimizer(tmp_path):
    agent, _env = _runtime()
    failures, evidence = _validate(_valid_checkpoint(agent), tmp_path)

    assert failures == []
    assert evidence["checkpoint_discriminator_optimizer_format"] == "legacy_combined_adam"
    assert evidence["checkpoint_optimizer_states"][-1] == "discriminator_optimizer"


def test_analyzer_accepts_complete_split_discriminator_checkpoint(tmp_path):
    agent, _env = _runtime()
    checkpoint = _valid_checkpoint(agent)
    del checkpoint["discriminator_optimizer"]
    checkpoint.update(
        {
            "discriminator_optimizer_schema": "split_team_individual_adam_v1",
            "team_discriminator_optimizer": _optimizer_state(),
            "individual_discriminator_optimizer": _optimizer_state(),
            "team_discriminator_scheduler": None,
            "individual_discriminator_scheduler": None,
        }
    )

    failures, evidence = _validate(checkpoint, tmp_path)

    assert failures == []
    assert evidence["checkpoint_discriminator_optimizer_format"] == "split_team_individual_adam_v1"
    assert evidence["checkpoint_optimizer_states"][-4:] == [
        "team_discriminator_optimizer",
        "individual_discriminator_optimizer",
        "team_discriminator_scheduler",
        "individual_discriminator_scheduler",
    ]


def test_analyzer_rejects_mixed_legacy_and_split_discriminator_payload(tmp_path):
    agent, _env = _runtime()
    checkpoint = _valid_checkpoint(agent)
    checkpoint.update(
        {
            "discriminator_optimizer_schema": "split_team_individual_adam_v1",
            "team_discriminator_optimizer": _optimizer_state(),
            "individual_discriminator_optimizer": _optimizer_state(),
            "team_discriminator_scheduler": None,
            "individual_discriminator_scheduler": None,
        }
    )

    failures, _evidence = _validate(checkpoint, tmp_path)

    assert any("must not include legacy discriminator" in failure for failure in failures)


def test_analyzer_rejects_partial_split_discriminator_payload(tmp_path):
    agent, _env = _runtime()
    checkpoint = _valid_checkpoint(agent)
    del checkpoint["discriminator_optimizer"]
    checkpoint.update(
        {
            "discriminator_optimizer_schema": "split_team_individual_adam_v1",
            "team_discriminator_optimizer": _optimizer_state(),
            "team_discriminator_scheduler": None,
            "individual_discriminator_scheduler": None,
        }
    )

    failures, _evidence = _validate(checkpoint, tmp_path)

    assert "checkpoint.individual_discriminator_optimizer is missing from split discriminator format" in failures


def test_analyzer_rejects_partial_split_scheduler_payload(tmp_path):
    agent, _env = _runtime()
    checkpoint = _valid_checkpoint(agent)
    del checkpoint["discriminator_optimizer"]
    checkpoint.update(
        {
            "discriminator_optimizer_schema": "split_team_individual_adam_v1",
            "team_discriminator_optimizer": _optimizer_state(),
            "individual_discriminator_optimizer": _optimizer_state(),
            "team_discriminator_scheduler": {"last_epoch": 1},
            "individual_discriminator_scheduler": None,
        }
    )

    failures, _evidence = _validate(checkpoint, tmp_path)

    assert any("team_discriminator_scheduler is present" in failure for failure in failures)
