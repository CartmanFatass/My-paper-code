import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch


def load_runner(name):
    path = Path(__file__).resolve().parents[5] / "scripts/run_folr_action_contrast_a01.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def argv(path, input_root, out):
    return [
        str(path),
        "--seed",
        "1783101",
        "--launch-sha",
        "synthetic-source",
        "--input-root",
        str(input_root),
        "--out",
        str(out),
    ]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_admission_refusal_precedes_input_read_model_and_output(tmp_path, monkeypatch):
    path, runner = load_runner("folr_action_contrast_admission_test")
    out = tmp_path / "unused"
    monkeypatch.setattr(
        runner, "require_admission", lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("refused"))
    )
    monkeypatch.setattr("sys.argv", argv(path, tmp_path / "missing-input", out))
    with pytest.raises(RuntimeError, match="refused"):
        runner.main()
    assert not out.exists()


def make_foreign_inputs(root):
    for tag in (
        "predictive_aux_a01_detached_783101",
        "predictive_aux_a01_coupled_783101",
    ):
        path = root / tag
        path.mkdir(parents=True)
        (path / "final.pt").write_bytes(b"foreign-checkpoint")
        (path / "final-panel.npz").write_bytes(b"foreign-panel")
        (path / "summary.json").write_text("{}")


def test_input_digest_mismatch_publishes_robust_incomplete_summary(tmp_path, monkeypatch):
    path, runner = load_runner("folr_action_contrast_digest_test")
    input_root = tmp_path / "inputs"
    make_foreign_inputs(input_root)
    out = tmp_path / "output"
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_kw: {"sha": "synthetic-source"})
    monkeypatch.setattr("sys.argv", argv(path, input_root, out))
    with pytest.raises(ValueError, match="checkpoint SHA256"):
        runner.main()
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "incomplete"
    assert summary["error"].startswith("ValueError: DETACHED checkpoint SHA256")
    assert summary["fits"] == summary["optimizer_steps"] == summary["parameter_updates"] == 0
    assert summary["activity"]["actor_forward_calls"] == 0
    assert summary["input_hashes_before"] == summary["input_hashes_after"]
    assert summary["source_hashes"]


class FakeActor(torch.nn.Module):
    def __init__(self, _arm):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.ones(1, dtype=torch.float32))


def synthetic_row(arm, index):
    return {
        "arm": arm,
        "episode": index % 128,
        "time": index % 20,
        "agent": index % 5,
        "native_rewards_by_action": [0.0, 1.0, 0.0, 0.0, 0.0],
        "native_collision_deltas_by_action": [0, 0, 0, 0, 0],
        "factual_action": 0,
        "full_action": 0,
        "reset_action": 1,
        "factual_full_regret": 1.0,
        "reset_regret": 0.0,
        "full_minus_reset_immediate_reward": -1.0,
        "action_changed": True,
        "native_reward_range": 1.0,
        "nonflat_action_contrast": True,
        "collision_sensitive": False,
        "event_at_boundary": False,
        "in_post_event_window": False,
        "public_event_stratum": "OUTSIDE_POST_EVENT_WINDOW",
    }


def make_bound_inputs(root, actor):
    specs = {}
    for arm, selected, active in (("DETACHED", 718, 7281), ("COUPLED", 180, 7591)):
        tag = arm.lower()
        path = root / tag
        path.mkdir(parents=True)
        checkpoint = path / "final.pt"
        torch.save(
            {
                "arm": arm,
                "native_actor_arm": "GENERIC_RETAIN",
                "actor": actor.state_dict(),
            },
            checkpoint,
        )
        panel = path / "final-panel.npz"
        np.savez(panel, fixture=np.zeros(1, dtype=np.int8))
        checkpoint_hash, panel_hash = sha(checkpoint), sha(panel)
        (path / "summary.json").write_text(
            json.dumps(
                {
                    "status": "complete",
                    "arm": arm,
                    "evaluation_seed": 1783101,
                    "final_episodes": 128,
                    "final_transitions": 2560,
                    "final_checkpoint_sha256": checkpoint_hash,
                    "final_panel": {"artifact_sha256": panel_hash},
                    "final_returns": [0.0] * 128,
                }
            )
        )
        specs[arm] = {
            "tag": tag,
            "checkpoint_sha256": checkpoint_hash,
            "panel_sha256": panel_hash,
            "selected_rows": selected,
            "active_action_checks": active,
        }
    return specs


def test_complete_runner_keeps_inputs_and_actor_immutable_with_zero_updates(tmp_path, monkeypatch):
    path, runner = load_runner("folr_action_contrast_complete_test")
    from experiments.candidates.vap_folr_core.action_contrast_a01 import diagnostic
    from experiments.candidates.vap_folr_core.entity_history_b01 import environment, model

    input_root = tmp_path / "inputs"
    actor = FakeActor("GENERIC_RETAIN")
    specs = make_bound_inputs(input_root, actor)

    def fake_replay(_env, _actor, _panel, _returns, arm, emit_row, activity):
        selected = specs[arm]["selected_rows"]
        activity.update(
            actor_forward_calls=5376,
            full_forward_calls=2688,
            reset_forward_calls=2688,
            factual_transition_calls=2560,
            counterfactual_transition_calls=selected * 4,
            observation_boundaries_verified=2688,
            active_action_checks=specs[arm]["active_action_checks"],
            factual_reward_checks=2560,
            native_return_checks=128,
            replayed_episodes=128,
            selected_rows=selected,
        )
        for index in range(selected):
            emit_row(synthetic_row(arm, index))
            activity["rows_written"] += 1

    monkeypatch.setattr(diagnostic, "INPUTS", specs)
    monkeypatch.setattr(diagnostic, "replay_panel", fake_replay)
    monkeypatch.setattr(model, "Actor", FakeActor)
    monkeypatch.setattr(environment, "EntityHistoryEnv", lambda **_kw: object())
    monkeypatch.setattr(torch, "set_num_interop_threads", lambda _value: None)
    monkeypatch.setattr(runner, "require_admission", lambda *_a, **_kw: {"sha": "synthetic-source"})
    out = tmp_path / "output"
    monkeypatch.setattr("sys.argv", argv(path, input_root, out))
    runner.main()

    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "complete"
    assert summary["fits"] == summary["optimizer_steps"] == summary["parameter_updates"] == 0
    assert summary["predictor_forward_calls"] == summary["mixer_forward_calls"] == 0
    assert summary["activity"]["actor_forward_calls"] == 10752
    assert summary["native_transition_calls"] == 8712
    assert summary["row_artifact"]["rows"] == 898
    assert summary["input_hashes_before"] == summary["input_hashes_after"]
    for panel in summary["panels"].values():
        assert panel["actor_state_sha256_before"] == panel["actor_state_sha256_after"]

