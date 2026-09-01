from experiments.candidates.ucope.competence_first_scout_r01 import (
    ScoutConfig,
    RunBinding,
    run_workload,
    sanitize_assess_result,
    stage_checkpoint_inventory,
    validate_checkpoint_inventory,
)
from experiments.candidates.ucope.competence_first_scout_r01.checkpoint import load_checkpoint, validate_checkpoint
import pytest


def test_reduced_assess_runs_all_three_arms_and_sanitizes(tmp_path):
    binding = RunBinding.assess("c" * 64)
    events = []
    result = run_workload(ScoutConfig.assess(), tmp_path / "assess", stage_callback=events.append, run_binding=binding)
    artifact = sanitize_assess_result(result)
    assert artifact["activity"]["policies_completed"] == 6
    assert artifact["activity"]["root_optimizer_updates"] == 96
    assert artifact["activity"]["tail_optimizer_updates"] == 48
    assert artifact["activity"]["checkpoint_writes"] == 12
    assert artifact["activity"]["environment_episodes"] == 2_560
    assert artifact["activity"]["environment_transitions"] == 12_800
    assert all("gradient" not in row and "clipping" not in row for row in artifact["activity"]["per_policy"].values())
    assert "internal_result" not in artifact
    assert not (tmp_path / "assess" / "scientific_checkpoints").exists()
    assert (tmp_path / "assess" / "non_scientific_assess_state").is_dir()
    checkpoint_events = [event for event in events if event["stage"] == "checkpoint"]
    assert len(checkpoint_events) == 12
    assert all(set(event) == {"stage", "arm_id", "seed_id", "fold_id", "root_update", "activity"} for event in checkpoint_events)
    histograms = result.internal_result["support_histograms"][result.config.seed_ids[0]]
    assert len(histograms) == 8
    assert all(len(row[fold]) == 7 and sum(row[fold]) == 80 for row in histograms.values() for fold in ("fold-0", "fold-1"))

    complete_root = tmp_path / "complete"
    inventory = stage_checkpoint_inventory(result.config, result.checkpoints, staging_root=complete_root, run_binding=binding)
    assert len(inventory) == 12
    assert all(not __import__("pathlib").Path(record["locator"]).is_absolute() for record in inventory)
    validate_checkpoint_inventory(inventory, config=result.config, artifact_root=complete_root, run_binding=binding)
    payload = load_checkpoint(complete_root / inventory[0]["locator"])
    forbidden = {"evaluations", "scores", "regret", "competence", "acquisition", "returns", "gates"}
    assert not (set(payload) & forbidden)
    raw = (complete_root / inventory[0]["locator"]).read_bytes().lower()
    assert all(token not in raw for token in (b"evaluations", b"scores", b"regret", b"acquisition", b"root_actions", b"tail_agreement"))
    tampered_payload = dict(payload)
    tampered_payload["activity"] = dict(payload["activity"], root_example_exposures=1)
    with pytest.raises(ValueError):
        validate_checkpoint(tampered_payload)
    tampered_inventory = [dict(record) for record in inventory]
    tampered_inventory[0]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate_checkpoint_inventory(tampered_inventory, config=result.config, artifact_root=complete_root, run_binding=binding)
    absolute_inventory = [dict(record) for record in inventory]
    absolute_inventory[0]["locator"] = str((complete_root / inventory[0]["locator"]).resolve())
    with pytest.raises(ValueError):
        validate_checkpoint_inventory(absolute_inventory, config=result.config, run_binding=binding)
