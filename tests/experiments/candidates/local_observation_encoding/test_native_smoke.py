import json
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[4]
for directory in (ROOT, ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from experiments.candidates.local_observation_encoding import b01
import run_local_observation_encoding_b01 as entry


@pytest.mark.parametrize("arm", ["ORIGINAL", "DENSE"])
def test_mocked_admission_short_native_fit(monkeypatch, tmp_path, arm):
    shared = b01.native.shared
    monkeypatch.setattr(shared, "TRAIN_LANES", 2)
    monkeypatch.setattr(shared, "EVAL_LANES", 2)
    monkeypatch.setattr(shared, "HORIZON", 20)
    monkeypatch.setattr(shared, "PROCESS_START", shared.time.perf_counter())
    monkeypatch.setattr(b01, "ROLLOUTS", 2)
    monkeypatch.setattr(b01, "PANEL_ROLLOUTS", (1, 2))
    sha = shared.e0._git("rev-parse", "HEAD")
    monkeypatch.setattr(
        entry, "require_admission",
        lambda *args, **kwargs: {"sha": sha, "command_sha256": "mocked-admission"},
    )

    out = tmp_path / arm.lower()
    assert entry.main([
        "--arm", arm, "--seed", str(b01.TRAINING_SEED), "--launch-sha", sha,
        "--output-root", str(out),
    ]) == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["counts"]["update_stages"] == 2
    assert summary["counts"]["model_constructions"] == 2
    assert summary["learner_config"]["total_timesteps"] == 2 * 20 * 2
    assert not any(summary["active_plain_hmasd_flags"][name] for name in (
        "use_horizon_window", "use_team_bridge", "use_opt_compact",
        "use_compact_in_low_level_actor", "use_process_exploration",
        "disable_high_level_training", "disable_discriminator_training",
        "disable_discriminator_rewards",
    ))
    assert summary["encoder_arm"] == arm
    assert summary["parameter_counts"]["active_base_type"] == (
        "MLPBase" if arm == "ORIGINAL" else "DenseObservationEncoder"
    )
    assert all(summary["optimizer_calls"][name] > 0 for name in b01.NETWORKS)
    assert not any(summary["evaluation_optimizer_calls"].values())
    assert summary["actor_timing"]["learner"]["total_calls"] > 0
    assert summary["actor_timing"]["evaluator"]["forward_calls"] > 0
    assert summary["phase_wall_seconds"]["total"] > 0
    assert summary["final_checkpoint"]["bytes"] > 0
    checkpoint_path = out / summary["final_checkpoint"]["path"]
    assert checkpoint_path.is_file()
    for panel in summary["panels"]:
        assert panel["connected_users_mean_per_step"]
        assert panel["native_scores_J"] == pytest.approx(
            panel["component_means"]["total_reward"], rel=1e-7, abs=1e-7
        )
    assert list(b01.fit_endpoint(summary)) == [1, 2]

    # Reconstruct the recorded arm before loading: Dense changes the actor-base state schema.
    envs = shared.e0._make_envs(shared.TRAIN_LANES, b01.TRAINING_SEED,
                                shared.N_UAVS, shared.N_USERS, shared.HORIZON)
    with b01.scoped_native_bindings():
        config = b01.native.make_config(arm, envs, b01.TRAINING_SEED)
    restored = shared.HMASDAgent(config, log_dir=str(tmp_path / f"restore-{arm}"),
                                 device=torch.device("cpu"))
    b01.install_actor_encoder(restored, arm)
    restored.load_model(checkpoint_path)
    stored = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    restored_state = restored.skill_discoverer.state_dict()
    assert stored["skill_discoverer"].keys() == restored_state.keys()
    for key, value in stored["skill_discoverer"].items():
        torch.testing.assert_close(value, restored_state[key], rtol=0, atol=0)
