import argparse
import json

import torch

from ha_ctse_process import train as train_mod


class _Config:
    skill_lifetime_candidates = (3, 7, 13, 24)
    n_agents = 6
    n_uavs = 6
    max_observed_uavs = 6
    low_actor_condition_on_team_code = True
    team_bridge_type = "stochastic"
    z_assignment_residual_gain = 0.0
    enable_assignment_actionability_probe = False
    enable_assignment_actionability_reward = False
    assignment_actionability_coef = 0.0
    assignment_actionability_clip = 0.0
    assignment_actionability_warmup_steps = 0
    assignment_actionability_include_soft = True


def test_checkpoint_metadata_recovers_q_a_fields_from_adjacent_manifest(tmp_path):
    ckpt = tmp_path / "standalone_process_core_update_40.pt"
    torch.save(
        {
            "duration_candidates": (1, 2, 3, 4),
            "n_agents": 6,
            "n_skills": 4,
            "team_bridge_type": "stochastic",
            "enable_team_intent": True,
            "team_intent_k": 8,
        },
        ckpt,
    )
    manifest_dir = tmp_path / "metadata"
    manifest_dir.mkdir()
    (manifest_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "args": {
                    "z_assignment_residual_gain": 0.5,
                    "enable_assignment_actionability_probe": False,
                    "enable_assignment_actionability_reward": True,
                    "assignment_actionability_coef": 0.02,
                    "assignment_actionability_clip": 1.0,
                    "assignment_actionability_warmup_steps": 20000,
                    "no_assignment_actionability_soft": False,
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = train_mod.load_checkpoint_metadata(ckpt)
    assert metadata["z_assignment_residual_gain"] == 0.5
    assert metadata["enable_assignment_actionability_probe"] is False
    assert metadata["enable_assignment_actionability_reward"] is True
    assert metadata["assignment_actionability_coef"] == 0.02
    assert metadata["assignment_actionability_clip"] == 1.0
    assert metadata["assignment_actionability_warmup_steps"] == 20000
    assert metadata["assignment_actionability_include_soft"] is True

    cfg = _Config()
    args = argparse.Namespace(n_agents=6)
    train_mod.apply_checkpoint_structure(cfg, args, metadata)
    assert cfg.z_assignment_residual_gain == 0.5
    assert cfg.enable_assignment_actionability_probe is False
    assert cfg.enable_assignment_actionability_reward is True
    assert cfg.assignment_actionability_coef == 0.02
    assert cfg.assignment_actionability_clip == 1.0
    assert cfg.assignment_actionability_warmup_steps == 20000
    assert cfg.assignment_actionability_include_soft is True


def test_checkpoint_metadata_prefers_top_level_q_a_fields_over_manifest(tmp_path):
    ckpt = tmp_path / "standalone_process_core_update_40.pt"
    torch.save(
        {
            "z_assignment_residual_gain": 0.75,
            "enable_assignment_actionability_reward": False,
            "assignment_actionability_include_soft": False,
        },
        ckpt,
    )
    manifest_dir = tmp_path / "metadata"
    manifest_dir.mkdir()
    (manifest_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "args": {
                    "z_assignment_residual_gain": 0.5,
                    "enable_assignment_actionability_reward": True,
                    "no_assignment_actionability_soft": False,
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = train_mod.load_checkpoint_metadata(ckpt)
    assert metadata["z_assignment_residual_gain"] == 0.75
    assert metadata["enable_assignment_actionability_reward"] is False
    assert metadata["assignment_actionability_include_soft"] is False
