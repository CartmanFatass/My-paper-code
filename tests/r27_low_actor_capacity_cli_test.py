from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.low_actor_capacity_audit import CapacitySnapshotBatch
from ha_ctse_process.standalone_agent import StrictHMASDMAPPOLowLevelPolicy
from scripts import audit_r27_low_actor_capacity as collector


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FakeSegment:
    skill: int
    duration_idx: int
    prev_skill: int
    skill_age_prev: int


class FakeEnv:
    def __init__(self) -> None:
        self.steps = 0

    def reset(self, *, seed: int):
        self.steps = 0
        obs = np.asarray([[0.0, 0.5], [1.0, 1.5]], dtype=np.float32)
        return obs, {"state": np.asarray([float(seed)], dtype=np.float32)}

    def step(self, actions):
        del actions
        self.steps += 1
        obs = np.asarray(
            [
                [float(self.steps), float(self.steps) + 0.5],
                [float(self.steps) + 1.0, float(self.steps) + 1.5],
            ],
            dtype=np.float32,
        )
        return obs, 99.0, False, False, {
            "next_state": np.asarray([float(self.steps)], dtype=np.float32),
            "coverage_ratio": 1.0,
            "throughput": 123.0,
            "backhaul_connected": True,
        }

    def close(self) -> None:
        pass


class FakeAgent:
    def __init__(self) -> None:
        self.n_agents = 2
        self.n_skills = 4
        self.duration_candidates = (3, 7, 13, 24)
        self.active_skills = np.zeros((1, 2), dtype=np.int64)
        self.active_duration_indices = np.zeros((1, 2), dtype=np.int64)
        self.duration_remaining = np.zeros((1, 2), dtype=np.int64)
        self.skill_age = np.zeros((1, 2), dtype=np.int64)
        self.has_active_skill = np.zeros((1, 2), dtype=np.bool_)
        self.active_team_codes = np.zeros(1, dtype=np.int64)
        self.team_intent_remaining = np.zeros(1, dtype=np.int64)
        self.team_intent_age = np.zeros(1, dtype=np.int64)
        self.low_actor_hxs = np.zeros((1, 2, 4), dtype=np.float32)
        self.low_critic_hxs = np.zeros((1, 2, 4), dtype=np.float32)
        self.segments = SimpleNamespace(active=[[None, None]])
        self.assignment_grad_enabled: list[bool] = []
        self.action_grad_enabled: list[bool] = []
        self.current_step = 0

    @staticmethod
    def _forbidden(*_args, **_kwargs):
        raise AssertionError("frozen collector invoked an update path")

    process_update = _forbidden
    update_high_from_segments = _forbidden
    update_low = _forbidden
    backward = _forbidden

    def reset_env_state(self, env_id: int) -> None:
        self.active_skills[env_id] = 0
        self.active_duration_indices[env_id] = 0
        self.duration_remaining[env_id] = 0
        self.skill_age[env_id] = 0
        self.has_active_skill[env_id] = False
        self.active_team_codes[env_id] = 0
        self.low_actor_hxs[env_id] = 0.0
        self.low_critic_hxs[env_id] = 0.0
        self.segments.active[env_id] = [None, None]

    def maybe_assign_skills(
        self,
        obs,
        *,
        state,
        step: int,
        k: int,
        env_id: int,
        deterministic: bool,
    ) -> None:
        del obs, state, k, deterministic
        self.assignment_grad_enabled.append(torch.is_grad_enabled())
        self.current_step = int(step)
        if int(step) != 1:
            return
        self.segments.active[env_id][0] = FakeSegment(
            skill=1,
            duration_idx=2,
            prev_skill=int(self.active_skills[env_id, 0]),
            skill_age_prev=5,
        )
        self.active_skills[env_id, 0] = 1
        self.active_duration_indices[env_id, 0] = 2
        self.has_active_skill[env_id, 0] = True

    def act_low(self, obs, *, env_id: int, deterministic: bool, state):
        del obs, deterministic, state
        self.action_grad_enabled.append(torch.is_grad_enabled())
        if self.current_step == 0:
            self.low_actor_hxs[env_id, 0] = np.asarray(
                [1.0, 2.0, 3.0, 4.0], dtype=np.float32
            )
        return (
            np.zeros((2, 2), dtype=np.float32),
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
        )


class ManifestEnv(FakeEnv):
    def reset(self, *, seed: int):
        self.steps = 0
        obs = np.zeros((2, 6), dtype=np.float32)
        obs[:, 0] = np.asarray([0.0, 1.0])
        return obs, {"state": np.zeros(7, dtype=np.float32)}

    def step(self, actions):
        del actions
        self.steps += 1
        obs = np.full((2, 6), float(self.steps), dtype=np.float32)
        return obs, 1.0, False, False, {
            "next_state": np.full(7, float(self.steps), dtype=np.float32),
            "coverage_ratio": 0.5,
            "throughput": 7.0,
        }


class ManifestAgent(FakeAgent):
    def __init__(self) -> None:
        super().__init__()
        self.low_actor_hxs = np.zeros((1, 2, 8), dtype=np.float32)
        self.low_critic_hxs = np.zeros((1, 2, 8), dtype=np.float32)
        self.low = StrictHMASDMAPPOLowLevelPolicy(
            obs_dim=6,
            state_dim=7,
            n_skills=4,
            num_team_codes=2,
            action_dim=4,
            hidden_dim=8,
            action_space_type="continuous",
            continuous_action_distribution="tanh_gaussian",
            actor_condition_on_team_code=False,
            device="cpu",
        ).eval()

    def act_low(self, obs, *, env_id: int, deterministic: bool, state):
        del obs, deterministic, state
        self.action_grad_enabled.append(torch.is_grad_enabled())
        if self.current_step == 0:
            self.low_actor_hxs[env_id, 0] = np.arange(1, 9, dtype=np.float32)
        return (
            np.zeros((2, 4), dtype=np.float32),
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
        )

    def parameter_counts(self):
        count = sum(parameter.numel() for parameter in self.low.parameters())
        return {"low_total": int(count)}


def collect_fixture():
    return collector.collect_capacity_reset(
        FakeEnv(),
        FakeAgent(),
        reset_id=3,
        reset_seed=27003,
        episode_id=3,
        skill_interval=10,
        episode_max_steps=2,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )


def test_collector_records_hidden_state_before_natural_assignment():
    batch, stats = collect_fixture()

    np.testing.assert_array_equal(
        batch.actor_hidden[0], [1.0, 2.0, 3.0, 4.0]
    )
    assert batch.natural_skill.tolist() == [1]
    assert batch.previous_skill.tolist() == [0]
    assert batch.duration_idx.tolist() == [2]
    assert batch.skill_age.tolist() == [5]
    assert stats.renewal_events == 1


def test_collector_owns_no_grad_and_does_not_store_task_fields():
    agent = FakeAgent()
    batch, _ = collector.collect_capacity_reset(
        FakeEnv(),
        agent,
        reset_id=3,
        reset_seed=27003,
        episode_id=3,
        skill_interval=10,
        episode_max_steps=2,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )

    assert agent.assignment_grad_enabled == [False, False]
    assert agent.action_grad_enabled == [False, False]
    forbidden = {
        "reward",
        "coverage",
        "throughput",
        "qos",
        "backhaul",
        "topology",
        "recovery",
    }
    assert forbidden.isdisjoint(CapacitySnapshotBatch.__dataclass_fields__)
    assert batch.episode_done_mask.tolist() == [False]


def test_collect_static_rejects_cpu_before_checkpoint_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(
        collector,
        "_configure_agent",
        lambda args: pytest.fail("checkpoint was loaded before CUDA validation"),
    )
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "missing.pt",
            "--output-dir",
            str(tmp_path),
            "--device",
            "cpu",
        ]
    )

    with pytest.raises(ValueError, match="requires --device cuda"):
        collector.run_collect_static(args)


def test_parse_args_exposes_exact_three_subcommands():
    parser = collector.build_parser()
    choices = next(
        action.choices
        for action in parser._actions
        if getattr(action, "choices", None)
    )
    assert set(choices) == {"collect-static", "synthetic", "aggregate"}


def test_aggregate_writes_exact_registered_classification(tmp_path):
    static = {
        "status": "FAIL",
        "zero_h": {
            "pass": False,
            "mean_skl": 0.0,
            "mean_stdmean_distance": 0.0,
            "film_feature_between": 0.1,
            "post_gru_feature_between": 0.01,
        },
        "rollout_h": {
            "pass": False,
            "mean_skl": 0.0,
            "mean_stdmean_distance": 0.0,
            "film_feature_between": 0.1,
            "post_gru_feature_between": 0.01,
        },
        "hidden_retention_ratio": 0.0,
        "inactive_control": {
            "max_abs_symmetric_kl": 0.0,
            "max_stdmean_distance": 0.0,
        },
        "parity": {"pass": True},
        "thresholds": {
            "symmetric_kl_min": 0.02,
            "standardized_mean_distance_min": 0.20,
        },
    }
    checkpoint_ids = ["arm0_update25", "arm0_update30", "arm0_final"]
    for checkpoint_id in checkpoint_ids:
        root = tmp_path / checkpoint_id
        root.mkdir()
        payload = dict(static, checkpoint_id=checkpoint_id)
        (root / "static_capacity.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        manifest = {
            "checkpoint_id": checkpoint_id,
            "checkpoint_sha256_before": f"sha-{checkpoint_id}",
            "checkpoint_sha256_equal": True,
            "policy_parameter_sha256_equal": True,
            "parameter_counts": {"low_actor": 558344},
        }
        (root / "collector_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
    synthetic = {
        "status": "PASS",
        "pass": True,
        "passing_seeds": 2,
        "failed_seeds": 1,
        "checkpoint_sha256_before": "sha-arm0-final",
        "checkpoint_sha256_equal": True,
        "policy_parameter_sha256_equal": True,
        "parameter_counts": {"low_actor": 558344},
        "seed_reports": [
            {
                "seed": 17,
                "status": "PASS",
                "synthetic_code_accuracy": 0.95,
                "synthetic_code_macro_f1": 0.94,
                "sham_accuracy": 0.25,
                "synthetic_active_minus_sham_accuracy": 0.70,
                "synthetic_train_minus_test_accuracy": 0.05,
                "active_minus_sham_bootstrap": {"lower": 0.55},
            }
        ],
    }
    (tmp_path / "synthetic_control.json").write_text(
        json.dumps(synthetic), encoding="utf-8"
    )
    args = SimpleNamespace(
        run_root=str(tmp_path), checkpoint_ids=checkpoint_ids
    )

    result = collector.run_aggregate(args)

    assert result["classification"] == "CAPACITY_PRESENT_OBJECTIVE_MISSING"
    json_result = json.loads(
        (tmp_path / "r27_capacity_autopsy.json").read_text(encoding="utf-8")
    )
    markdown = (tmp_path / "r27_capacity_autopsy.md").read_text(
        encoding="utf-8"
    )
    assert json_result["classification"] == result["classification"]
    assert "CAPACITY_PRESENT_OBJECTIVE_MISSING" in markdown
    assert "No q_A, q_d, q_D, or intrinsic reward" in markdown
    assert "arm0_update25" in markdown
    assert "sha-arm0_update25" in markdown
    assert "low_actor: 558344" in markdown
    assert "Seed 17" in markdown
    assert "macro-F1: 0.94" in markdown
    assert "symmetric KL >= 0.02" in markdown


def test_collect_static_writes_shards_manifest_and_immutability(monkeypatch, tmp_path):
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"immutable-checkpoint")
    env = ManifestEnv()
    agent = ManifestAgent()
    config = SimpleNamespace(scenario="energy")
    metadata = {"n_agents": 2, "n_skills": 4, "update_idx": 25}
    monkeypatch.setattr(
        collector, "require_cuda_device", lambda device: torch.device("cpu")
    )
    monkeypatch.setattr(
        collector,
        "_configure_agent",
        lambda args: (config, metadata, env, agent, 25),
    )
    output_dir = tmp_path / "out"
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            str(checkpoint),
            "--output-dir",
            str(output_dir),
            "--checkpoint-id",
            "fixture_update25",
            "--checkpoint-update",
            "25",
            "--n-resets",
            "5",
            "--episode-max-steps",
            "2",
            "--bootstrap-reps",
            "20",
        ]
    )

    result = collector.run_collect_static(args)

    assert len(list((output_dir / "capacity_snapshots").glob("*.npz"))) == 5
    manifest = json.loads(
        (output_dir / "collector_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["checkpoint_sha256_equal"] is True
    assert manifest["policy_parameter_sha256_equal"] is True
    assert manifest["stats"] == {
        "renewal_events": 5,
        "resets": 5,
        "snapshot_rows": 5,
    }
    assert result["static"]["checkpoint_id"] == "fixture_update25"
    assert (output_dir / "static_capacity.md").is_file()


def test_runner_dry_run_has_exact_arm0_checkpoints_and_no_forbidden_flags(
    tmp_path,
):
    run_root = tmp_path / "dry-run-output"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1",
            "-DryRun",
            "-RunRoot",
            str(run_root),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    output = result.stdout + result.stderr

    assert output.count("PHASE collect-static") == 3
    assert "arm0_update25" in output
    assert "arm0_update30" in output
    assert "arm0_final" in output
    assert "arm2_" not in output
    for forbidden in (
        "process_reward",
        "prototype_disc",
        "team_disc",
        "q_A",
        "q_d",
        "q_D",
        "total_timesteps",
    ):
        assert forbidden not in output
    assert output.count("PHASE synthetic") == 1
    assert output.count("PHASE aggregate") == 1
    assert not run_root.exists()


def test_runner_rejects_cpu_in_dry_run():
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1",
            "-DryRun",
            "-Device",
            "cpu",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "requires -Device cuda" in output
