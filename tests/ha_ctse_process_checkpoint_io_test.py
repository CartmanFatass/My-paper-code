import argparse
import json
from types import SimpleNamespace

import torch

from ha_ctse_process import checkpoint_io
from ha_ctse_process import standalone_eval_runner
from ha_ctse_process import standalone_train_runner
from ha_ctse_process import train as process_train


def test_checkpoint_metadata_prefers_payload_then_adjacent_manifest(tmp_path):
    checkpoint_path = tmp_path / "standalone.pt"
    torch.save(
        {
            "checkpoint_schema_version": 2,
            "high_controller": "legacy_duration",
            "skill_interval": 7,
        },
        checkpoint_path,
    )
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    (metadata_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "algorithm_config": {
                    "skill_interval": 99,
                    "z_assignment_residual_gain": 0.25,
                }
            }
        ),
        encoding="utf-8",
    )

    metadata = checkpoint_io.load_checkpoint_metadata(checkpoint_path)

    assert metadata["skill_interval"] == 7
    assert metadata["z_assignment_residual_gain"] == 0.25


def test_schema3_metadata_and_structure_are_preserved(tmp_path):
    checkpoint_path = tmp_path / "event.pt"
    torch.save(
        {
            "checkpoint_schema_version": 3,
            "high_controller": "variable_roster_event",
            "event_architecture": {
                "architecture_mode": "f1",
                "event_architecture_schema_version": 4,
                "opportunity_schedule_name": "boundary_opportunities_v1",
                "snapshot_capability_name": "collector_snapshot",
                "snapshot_capability_version": 2,
                "event_semantic": {},
            },
        },
        checkpoint_path,
    )

    metadata = checkpoint_io.load_checkpoint_metadata(checkpoint_path)
    config = SimpleNamespace()
    checkpoint_io.apply_checkpoint_structure(
        config,
        argparse.Namespace(high_controller="", event_architecture_mode=""),
        metadata,
    )

    assert metadata["has_event_semantic"] is True
    assert config.high_controller == "variable_roster_event"
    assert config.event_architecture_mode == "f1"
    assert config.event_architecture_schema_version == 4
    assert config.event_opportunity_schedule == "boundary_opportunities_v1"


def test_checkpoint_callers_use_owner_functions_without_wrappers():
    for name in ("apply_checkpoint_structure", "load_checkpoint_metadata"):
        assert getattr(process_train, name) is getattr(checkpoint_io, name)
    for name in ("load_checkpoint", "prune_periodic_checkpoints", "save_checkpoint"):
        assert getattr(standalone_train_runner, name) is getattr(checkpoint_io, name)
    assert standalone_eval_runner.load_checkpoint is checkpoint_io.load_checkpoint
    for name in (
        "_load_adjacent_run_manifest",
        "load_checkpoint",
        "prune_periodic_checkpoints",
        "save_checkpoint",
    ):
        assert not hasattr(process_train, name)
    assert not hasattr(process_train, "checkpoint_payload")
    assert not hasattr(process_train, "migrate_legacy_high_to_r30")
    assert not hasattr(process_train, "load_reward_pure_legacy_high")
