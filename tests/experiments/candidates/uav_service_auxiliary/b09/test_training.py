"""Real short native collection/update with F active, early endings and crossing."""

from dataclasses import replace
import gzip
import json

import numpy as np
import pytest
import torch

from experiments.candidates.uav_service_auxiliary.b01.native import make_config
from experiments.candidates.uav_service_auxiliary.b08 import training as old_training
from experiments.candidates.uav_service_auxiliary.b09 import native, training
from experiments.candidates.uav_service_auxiliary.b09.persistence import compact_opportunity


@pytest.mark.parametrize("arm", ("N", "A"))
@pytest.mark.parametrize("device_name", ("cpu", "cuda"))
def test_real_collector_preserves_proposals_endings_and_high_prefixes(tmp_path, monkeypatch, arm, device_name):
    if device_name == "cuda" and not torch.cuda.is_available():
        pytest.skip("requires actual CUDA")
    torch.set_num_threads(4 if device_name == "cuda" else 1)
    if device_name == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
    spec = replace(native.B09Spec(), seed=317731, rollouts=2, rollout_length=12,
                   episode_length=7, hidden_size=32, gru_hidden_size=32, ppo_epochs=1)
    config = make_config(spec)
    config.k = 4
    config.ordinary_completed_segments = True
    config.initial_battery_ratio_range = (0.03, 0.03)
    config.sequence_length = 4
    config.sequence_batch_size = 8
    agent, _ = native.new_initialized_agent(config, device=torch.device(device_name),
                                           log_dir=tmp_path / "logs", seed=spec.seed)
    last_event = None
    summary_write_events = []
    append = training.append_progress
    write = training.write_summary
    def observed_append(out, event, counts):
        nonlocal last_event
        last_event = event["event"]
        append(out, event, counts)
    def observed_write(path, value):
        summary_write_events.append(last_event)
        write(path, value)
    monkeypatch.setattr(training, "append_progress", observed_append)
    monkeypatch.setattr(training, "write_summary", observed_write)
    result = training.train_arm(agent, config, spec, arm=arm, out=tmp_path / arm)
    assert "collection" not in summary_write_events
    assert "phase_complete" in summary_write_events
    assert "episode_complete" in summary_write_events
    assert result["status"] == "COMPLETE"
    assert result["counts"]["transitions"] == 48
    assert result["counts"]["phases"] == 2
    assert result["counts"]["native_episodes"] >= 4
    assert all(value > 0 for value in result["initialization_displacement_l2"].values())
    assert all(row["live_execution_unchanged_by_update_clear"] for row in result["phases"])
    actual_changed = 0
    for phase in (1, 2):
        with np.load(tmp_path / arm / f"training_{phase:02d}.npz", allow_pickle=False) as raw:
            assert raw["valid_execution"].all() and raw["stored_transition"].all()
            assert raw["valid_diagnostics"].all()
            np.testing.assert_array_equal(raw["stored_reward_env"], np.broadcast_to(
                raw["native_reward"].astype(np.float32)[..., None], raw["stored_reward_env"].shape))
            np.testing.assert_array_equal(raw["interaction_index"][:, 0], np.arange((phase-1)*12, phase*12))
            actual_changed += int(raw["command_changed"].sum())
            if arm == "N":
                np.testing.assert_array_equal(raw["original_action"], raw["submitted_action"])
                assert not raw["mode"].any()
            else:
                assert raw["mode"].any()
        with gzip.open(tmp_path / arm / f"high_after_update_{phase:02d}.json.gz", "rt") as handle:
            high = json.load(handle)
        assert high["consumed_records"]
        assert not high["completed_records"]
        assert all(row["consumed_phase_version"] == phase for row in high["consumed_records"])
    assert (actual_changed > 0) == (arm == "A")
    assert high["final"]
    assert len(high["pending_records"]) <= 2
    assert all(row["budget_censored"] for row in high["pending_records"])
    assert result["training_exposure"]["actor_proposal_uav_steps"] == 48 * 8
    for row in result["training_episodes"]:
        assert "intervals" not in row["opportunity"]
        with gzip.open(tmp_path / arm / row["raw_detail"], "rt") as handle:
            full = json.load(handle)
        assert "intervals" in full["opportunity"]
        assert row["raw_detail"] in result["artifacts"]
    if arm == "A":
        assert result["training_exposure"]["feedback_passed_proposal_uav_steps"] < 48 * 8
    # Evaluation receives a separate learner even while the training agent still
    # owns a final censored prefix. It neither resets that prefix nor updates RNG.
    before = native.initialization_identity(agent)
    pending = agent.ordinary_high_level_snapshot()["pending_records"]
    panel, _ = native.evaluate_feedback_panel(
        agent, config, (317761,), torch.device(device_name),
        trace_path=tmp_path / "evaluation.npz", log_dir=tmp_path / "evaluation_logs",
        policy_seed=spec.seed)
    assert panel["new_optimizer_updates"] == 0
    assert panel["actual_transitions"] <= spec.episode_length
    assert native.initialization_identity(agent) == before
    assert agent.ordinary_high_level_snapshot()["pending_records"] == pending


def test_failed_collection_preserves_actual_partial_transitions(tmp_path, monkeypatch):
    torch.set_num_threads(1)
    spec = replace(native.B09Spec(), seed=317739, lanes=1, rollouts=1, rollout_length=4,
                   episode_length=10, hidden_size=32, gru_hidden_size=32, ppo_epochs=1)
    config = make_config(spec)
    config.ordinary_completed_segments = True
    agent, _ = native.new_initialized_agent(config, device=torch.device("cpu"),
                                           log_dir=tmp_path / "logs", seed=spec.seed)
    real_ledger = training.energy_ledger
    calls = 0
    def fail_second(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("fixture ledger rejection")
        return real_ledger(*args)
    monkeypatch.setattr(training, "energy_ledger", fail_second)
    out = tmp_path / "partial"
    with pytest.raises(RuntimeError, match="fixture ledger rejection"):
        training.train_arm(agent, config, spec, arm="A", out=out)
    result = json.loads((out / "summary.json").read_text())
    assert result["status"] == "INCOMPLETE" and result["counts"]["transitions"] == 2
    assert result["failure"]["fully_stored_rows_in_phase"] == 1
    assert result["failure"]["valid_execution_lane_rows"] == 2
    assert result["failure"]["stored_transition_lane_rows"] == 1
    with np.load(out / "training_01_partial.npz", allow_pickle=False) as raw:
        assert raw["valid_execution"][:, 0].tolist() == [True, True]
        assert raw["stored_transition"][:, 0].tolist() == [True, False]
        assert raw["valid_diagnostics"][:, 0].tolist() == [True, False]
        assert len(raw["native_reward"]) == 2
        assert np.isfinite(raw["raw_physical_post_battery"]).all()
        assert np.isfinite(raw["raw_reward_info_metrics"]).all()
        assert (raw["raw_energy_consumed_wh"] > 0).any()
    assert (out / "high_partial_01.json.gz").exists()


def test_short_old_new_collector_substantive_equivalence(tmp_path):
    """Persistence changes preserve a fixed native A transition and update."""
    torch.set_num_threads(1)
    spec = replace(native.B09Spec(), seed=317749, lanes=1, rollouts=1,
                   rollout_length=12, episode_length=7, hidden_size=32,
                   gru_hidden_size=32, ppo_epochs=1)
    config = make_config(spec)
    config.k = 4
    config.ordinary_completed_segments = True
    config.initial_battery_ratio_range = (0.03, 0.03)
    config.sequence_length = 4
    config.sequence_batch_size = 8
    outputs = []
    for label, collector in (("old", old_training), ("new", training)):
        agent, identity = native.new_initialized_agent(
            config, device=torch.device("cpu"), log_dir=tmp_path / label / "logs", seed=spec.seed)
        result = collector.train_arm(agent, config, spec, arm="A", out=tmp_path / label / "arm")
        outputs.append((result, identity, agent))
    old, new = outputs
    assert old[1] == new[1]
    for field in ("counts", "optimizer_steps", "initialization_displacement_l2",
                  "training_exposure", "training_opportunity_aggregate",
                  "final_high_counters", "final_high_prefixes"):
        assert json.dumps(old[0][field], sort_keys=True, default=str) == json.dumps(
            new[0][field], sort_keys=True, default=str), field
    old_episodes = [{**row, "opportunity": compact_opportunity(row["opportunity"])}
                    for row in old[0]["training_episodes"]]
    new_episodes = [{key: value for key, value in row.items() if key != "raw_detail"}
                    for row in new[0]["training_episodes"]]
    assert old_episodes == new_episodes
    for name in ("skill_coordinator", "skill_discoverer", "team_discriminator",
                 "individual_discriminator"):
        old_state = getattr(old[2], name).state_dict()
        new_state = getattr(new[2], name).state_dict()
        assert old_state.keys() == new_state.keys()
        for key in old_state:
            torch.testing.assert_close(old_state[key], new_state[key], rtol=0, atol=0)
    with np.load(tmp_path / "old" / "arm" / "training_01.npz") as previous, \
         np.load(tmp_path / "new" / "arm" / "training_01.npz") as current:
        assert previous.files == current.files
        for key in previous.files:
            np.testing.assert_array_equal(previous[key], current[key], err_msg=key)
