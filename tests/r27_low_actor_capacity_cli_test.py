from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

import ha_ctse_process.low_actor_capacity_audit as capacity_audit
from ha_ctse_process.low_actor_capacity_audit import CapacitySnapshotBatch
from ha_ctse_process.collectors import EnvStep
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
    def __init__(self, num_envs: int = 1) -> None:
        self.n_agents = 2
        self.n_skills = 4
        self.duration_candidates = (3, 7, 13, 24)
        self.active_skills = np.zeros((num_envs, 2), dtype=np.int64)
        self.active_duration_indices = np.zeros((num_envs, 2), dtype=np.int64)
        self.duration_remaining = np.zeros((num_envs, 2), dtype=np.int64)
        self.skill_age = np.zeros((num_envs, 2), dtype=np.int64)
        self.has_active_skill = np.zeros((num_envs, 2), dtype=np.bool_)
        self.active_team_codes = np.zeros(num_envs, dtype=np.int64)
        self.team_intent_remaining = np.zeros(num_envs, dtype=np.int64)
        self.team_intent_age = np.zeros(num_envs, dtype=np.int64)
        self.low_actor_hxs = np.zeros((num_envs, 2, 4), dtype=np.float32)
        self.low_critic_hxs = np.zeros((num_envs, 2, 4), dtype=np.float32)
        self.segments = SimpleNamespace(
            active=[[None, None] for _ in range(num_envs)]
        )
        self.assignment_grad_enabled: list[bool] = []
        self.action_grad_enabled: list[bool] = []
        self.current_step = 0
        self.current_steps = np.zeros(num_envs, dtype=np.int64)

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
        self.current_steps[env_id] = int(step)
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
        if int(self.current_steps[env_id]) == 0:
            self.low_actor_hxs[env_id, 0] = np.asarray(
                [1.0, 2.0, 3.0, 4.0], dtype=np.float32
            )
        return (
            np.zeros((2, 2), dtype=np.float32),
            np.zeros(2, dtype=np.float32),
            np.zeros(2, dtype=np.float32),
        )


class FakeParallelCollector:
    def __init__(self, num_envs: int = 4) -> None:
        self.num_envs = int(num_envs)
        self.step_orders: list[list[int]] = []
        self.steps = np.zeros(num_envs, dtype=np.int64)

    def reset_all(self, seed: int):
        observations = [
            np.asarray(
                [[float(env_id), 0.5], [float(env_id) + 1.0, 1.5]],
                dtype=np.float32,
            )
            for env_id in range(self.num_envs)
        ]
        states = [
            np.asarray([float(seed + env_id)], dtype=np.float32)
            for env_id in range(self.num_envs)
        ]
        infos = [{"state": state.copy()} for state in states]
        return observations, states, infos

    def step_selected(self, indexed_actions):
        pairs = list(indexed_actions)
        env_ids = [int(env_id) for env_id, _action in pairs]
        self.step_orders.append(env_ids)
        results: dict[int, EnvStep] = {}
        for env_id, _action in pairs:
            env_id = int(env_id)
            self.steps[env_id] += 1
            step = int(self.steps[env_id])
            terminated = env_id == 1 and step == 1
            truncated = env_id == 3 and step == 2
            obs = np.asarray(
                [[float(step), 0.5], [float(step) + 1.0, 1.5]],
                dtype=np.float32,
            )
            results[env_id] = EnvStep(
                obs=obs,
                reward=0.0,
                terminated=terminated,
                truncated=truncated,
                info={"next_state": np.asarray([float(step)], dtype=np.float32)},
            )
        return results

    def close(self) -> None:
        pass


class ManifestParallelCollector(FakeParallelCollector):
    def reset_all(self, seed: int):
        observations = []
        states = []
        for env_id in range(self.num_envs):
            observation = np.zeros((2, 6), dtype=np.float32)
            observation[:, 0] = np.asarray(
                [float(env_id), float(env_id) + 1.0]
            )
            state = np.full(7, float(seed + env_id), dtype=np.float32)
            observations.append(observation)
            states.append(state)
        return observations, states, [{"state": state} for state in states]

    def step_selected(self, indexed_actions):
        pairs = list(indexed_actions)
        env_ids = [int(env_id) for env_id, _action in pairs]
        self.step_orders.append(env_ids)
        results: dict[int, EnvStep] = {}
        for env_id, _action in pairs:
            env_id = int(env_id)
            self.steps[env_id] += 1
            step = int(self.steps[env_id])
            results[env_id] = EnvStep(
                obs=np.full((2, 6), float(step), dtype=np.float32),
                reward=0.0,
                terminated=False,
                truncated=False,
                info={"next_state": np.full(7, float(step), dtype=np.float32)},
            )
        return results


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
    def __init__(self, num_envs: int = 1) -> None:
        super().__init__(num_envs=num_envs)
        self.low_actor_hxs = np.zeros((num_envs, 2, 8), dtype=np.float32)
        self.low_critic_hxs = np.zeros((num_envs, 2, 8), dtype=np.float32)
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


def test_parallel_collector_uses_one_reset_per_env_and_stops_finished_envs():
    env_collector = FakeParallelCollector(4)
    agent = FakeAgent(num_envs=4)

    batches, stats, evidence = collector.collect_capacity_parallel(
        env_collector,
        agent,
        base_seed=1,
        n_resets=4,
        skill_interval=10,
        episode_max_steps=3,
        checkpoint_id="fixture",
        checkpoint_update=25,
    )

    assert sorted(batches) == [0, 1, 2, 3]
    assert stats.resets == 4
    assert evidence["env_id_to_reset_id"] == {"0": 0, "1": 1, "2": 2, "3": 3}
    assert evidence["env_id_to_reset_seed"] == {"0": 1, "1": 2, "2": 3, "3": 4}
    assert evidence["active_steps_by_env"] == {"0": 3, "1": 1, "2": 3, "3": 2}
    assert evidence["termination_reason_by_env"] == {
        "0": "step_limit",
        "1": "terminated",
        "2": "step_limit",
        "3": "truncated",
    }
    assert env_collector.step_orders == [[0, 1, 2, 3], [0, 2, 3], [0, 2]]
    for env_id, batch in batches.items():
        assert set(batch.env_id.tolist()) <= {env_id}
        assert set(batch.reset_id.tolist()) <= {env_id}
        assert set(batch.episode_id.tolist()) <= {env_id}
        assert set(batch.reset_seed.tolist()) <= {1 + env_id}


def test_parallel_collector_repeated_fixture_has_identical_shard_hash(tmp_path):
    hashes: list[str] = []
    for run_id in range(2):
        batches, _stats, _evidence = collector.collect_capacity_parallel(
            FakeParallelCollector(4),
            FakeAgent(num_envs=4),
            base_seed=1,
            n_resets=4,
            skill_interval=10,
            episode_max_steps=3,
            checkpoint_id="fixture",
            checkpoint_update=25,
        )
        snapshot_dir = tmp_path / f"run_{run_id}"
        for env_id, batch in batches.items():
            capacity_audit.write_capacity_snapshot_shard(
                snapshot_dir / f"reset_{env_id:04d}.npz", batch
            )
        hashes.append(collector._snapshot_shards_sha256(snapshot_dir))

    assert hashes[0] == hashes[1]


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


def test_json_writer_rejects_nonfinite_payload(tmp_path):
    with pytest.raises(ValueError, match="Out of range float values"):
        collector._write_json(tmp_path / "nonfinite.json", {"value": float("nan")})


def test_scientific_contract_rejects_collect_reset_override():
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
            "--output-dir",
            "unused",
            "--checkpoint-id",
            "arm0_update25",
            "--checkpoint-update",
            "25",
            "--n-resets",
            "8",
        ]
    )

    with pytest.raises(ValueError, match="n_resets must equal 64"):
        collector.validate_scientific_args(args)


def test_collect_parser_exposes_fixed_parallel_defaults():
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "fixture.pt",
            "--output-dir",
            "unused",
        ]
    )

    assert args.num_envs == 64
    assert args.collector_backend == "subproc"
    assert args.collector_start_method == "spawn"


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("num_envs", 32, "num_envs must equal 64"),
        ("collector_backend", "sync", "collector_backend must equal"),
        (
            "collector_start_method",
            "fork",
            "collector_start_method must equal",
        ),
    ],
)
def test_scientific_parallel_contract_rejects_override(name, value, message):
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
            "--output-dir",
            "unused",
            "--checkpoint-id",
            "arm0_update25",
            "--checkpoint-update",
            "25",
        ]
    )
    setattr(args, name, value)

    with pytest.raises(ValueError, match=message):
        collector.validate_scientific_args(args)


def test_scientific_contract_rejects_synthetic_seed_and_budget_overrides():
    args = collector.parse_args(
        [
            "synthetic",
            "--checkpoint",
            "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt",
            "--snapshot-dir",
            "unused-snapshots",
            "--output-dir",
            "unused",
            "--synthetic-seeds",
            "17",
            "23",
            "--max-steps",
            "10",
        ]
    )

    with pytest.raises(ValueError, match="synthetic_seeds must equal"):
        collector.validate_scientific_args(args)


def test_explicit_fixture_mode_allows_reduced_contract_but_marks_non_scientific():
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "fixture.pt",
            "--output-dir",
            "unused",
            "--checkpoint-id",
            "fixture_update25",
            "--checkpoint-update",
            "25",
            "--n-resets",
            "5",
            "--non-scientific-fixture",
        ]
    )

    contract = collector.validate_scientific_args(args)

    assert contract["mode"] == "NON_SCIENTIFIC_FIXTURE"
    assert contract["eligible_for_aggregate"] is False


def test_scientific_contract_binds_every_decision_threshold():
    assert collector.SCIENTIFIC_CONTRACT["decision_thresholds"] == (
        collector.SCIENTIFIC_DECISION_THRESHOLDS
    )
    assert collector.SCIENTIFIC_DECISION_THRESHOLDS["static_checkpoint"] == {
        "symmetric_kl_min": 0.02,
        "standardized_mean_distance_min": 0.20,
        "bootstrap_lower": "> 0.0",
        "inactive_tolerance": 1e-8,
        "parity_tolerance": 1e-6,
    }
    assert collector.SCIENTIFIC_DECISION_THRESHOLDS["static_family"] == {
        "agreeing_checkpoints_min": 2,
        "recurrent_retention_max": 0.50,
    }
    assert collector.SCIENTIFIC_DECISION_THRESHOLDS["synthetic_seed"] == {
        "active_accuracy_min": 0.90,
        "active_macro_f1_min": 0.90,
        "active_minus_sham_accuracy_min": 0.50,
        "bootstrap_lower": "> 0.0",
        "sham_accuracy_max": 0.35,
        "train_minus_test_accuracy_max": 0.20,
    }
    assert collector.SCIENTIFIC_DECISION_THRESHOLDS["synthetic_family"] == {
        "passing_seeds_min": 2,
        "fixed_seed_count": 3,
        "minimum_reset_groups": 5,
    }
    assert collector.SCIENTIFIC_DECISION_THRESHOLDS["codebook_norm"] == 0.5


def _write_valid_scientific_aggregate_fixture(tmp_path: Path) -> list[str]:
    checkpoint_ids = ["arm0_update25", "arm0_update30", "arm0_final"]
    scientific_contract = {
        "mode": "R27_G1_SCIENTIFIC",
        "eligible_for_aggregate": True,
        "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
        "resolved_contract": collector.SCIENTIFIC_CONTRACT,
    }
    for checkpoint_id in checkpoint_ids:
        registered = collector.REGISTERED_CHECKPOINTS[checkpoint_id]
        root = tmp_path / checkpoint_id
        root.mkdir(parents=True)
        snapshot_dir = root / "capacity_snapshots"
        snapshot_dir.mkdir()
        for reset_id in range(64):
            collector.write_capacity_snapshot_shard(
                snapshot_dir / f"reset_{reset_id:04d}.npz",
                CapacitySnapshotBatch(
                    observation=np.zeros((1, 6), dtype=np.float32),
                    actor_hidden=np.zeros((1, 8), dtype=np.float32),
                    natural_skill=np.zeros(1, dtype=np.int64),
                    previous_skill=np.zeros(1, dtype=np.int64),
                    duration_idx=np.zeros(1, dtype=np.int64),
                    skill_age=np.zeros(1, dtype=np.int64),
                    episode_done_mask=np.zeros(1, dtype=np.bool_),
                    reset_id=np.asarray([reset_id], dtype=np.int64),
                    reset_seed=np.asarray([reset_id + 1], dtype=np.int64),
                    episode_id=np.asarray([reset_id], dtype=np.int64),
                    env_id=np.asarray([reset_id], dtype=np.int64),
                    agent_id=np.zeros(1, dtype=np.int64),
                    checkpoint_id=np.asarray([checkpoint_id]),
                    checkpoint_update=np.asarray(
                        [registered["update_idx"]], dtype=np.int64
                    ),
                ),
            )
        snapshot_sha256 = collector._snapshot_shards_sha256(snapshot_dir)
        static = {
            "checkpoint_id": checkpoint_id,
            "checkpoint_update": registered["update_idx"],
            "source_checkpoint_sha256": registered["sha256"],
            "snapshot_shards_sha256": snapshot_sha256,
            "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
            "status": "FAIL",
            "zero_h": {
                "pass": False,
                "mean_skl": 0.0,
                "mean_stdmean_distance": 0.0,
                "bootstrap": {"mean": 0.0, "lower": 0.0, "upper": 0.0},
                "shared_logstd_max_abs_error": 0.0,
                "film_feature_between": 0.0,
                "post_gru_feature_between": 0.0,
                "finite": True,
            },
            "rollout_h": {
                "pass": False,
                "mean_skl": 0.0,
                "mean_stdmean_distance": 0.0,
                "bootstrap": {"mean": 0.0, "lower": 0.0, "upper": 0.0},
                "shared_logstd_max_abs_error": 0.0,
                "film_feature_between": 0.0,
                "post_gru_feature_between": 0.0,
                "finite": True,
            },
            "hidden_retention_ratio": 0.0,
            "inactive_control": {
                "max_abs_symmetric_kl": 0.0,
                "max_stdmean_distance": 0.0,
            },
            "parity": {
                "pass": True,
                "max_action_abs_error": 0.0,
                "max_hidden_abs_error": 0.0,
            },
            "film_code_parameters": {
                "gamma_by_skill": [[1.0]],
                "beta_by_skill": [[0.0]],
                "consistency_max_abs_error": 0.0,
            },
            "thresholds": collector.SCIENTIFIC_DECISION_THRESHOLDS[
                "static_checkpoint"
            ],
        }
        static_path = root / "static_capacity.json"
        collector._write_json(static_path, static)
        manifest = {
            "checkpoint": registered["path"],
            "checkpoint_id": checkpoint_id,
            "checkpoint_update": registered["update_idx"],
            "checkpoint_sha256_before": registered["sha256"],
            "checkpoint_sha256_after": registered["sha256"],
            "checkpoint_sha256_equal": True,
            "policy_parameter_sha256_before": f"policy-{checkpoint_id}",
            "policy_parameter_sha256_after": f"policy-{checkpoint_id}",
            "policy_parameter_sha256_equal": True,
            "n_resets": 64,
            "num_envs": 64,
            "collector_backend": "subproc",
            "collector_start_method": "spawn",
            "parallel_collection_schedule": "step_major_env_id_ascending",
            "reset_seeds": list(range(1, 65)),
            "env_id_to_reset_id": {
                str(env_id): env_id for env_id in range(64)
            },
            "env_id_to_reset_seed": {
                str(env_id): env_id + 1 for env_id in range(64)
            },
            "active_steps_by_env": {
                str(env_id): 500 for env_id in range(64)
            },
            "termination_reason_by_env": {
                str(env_id): "step_limit" for env_id in range(64)
            },
            "stats": {
                "resets": 64,
                "renewal_events": 64,
                "snapshot_rows": 64,
            },
            "device": "cuda",
            "snapshot_shards_sha256": snapshot_sha256,
            "static_report_sha256": collector._file_sha256(static_path),
            "scientific_contract": scientific_contract,
            "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
            "checkpoint_identity": {
                "eligible_for_aggregate": True,
                "checkpoint_id": checkpoint_id,
                "checkpoint_update": registered["update_idx"],
                "checkpoint_sha256": registered["sha256"],
                "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
            },
            "parameter_counts": {"low_actor": 558344},
        }
        collector._write_json(root / "collector_manifest.json", manifest)

    def seed_report(seed: int, *, passed: bool) -> dict[str, object]:
        actor_sha = f"actor-{seed}"
        schedule_sha = f"schedule-{seed}"
        accuracy = 1.0 if passed else 0.50
        return {
            "seed": seed,
            "status": "PASS" if passed else "FAIL",
            "pass": passed,
            "reasons": [],
            "support": {"test_reset_groups": 12},
            "evidence_finite": True,
            "control_contract_valid": True,
            "synthetic_code_accuracy": accuracy,
            "synthetic_code_macro_f1": accuracy,
            "synthetic_target_mse": 0.01,
            "synthetic_train_accuracy": accuracy,
            "sham_accuracy": 0.25,
            "synthetic_active_minus_sham_accuracy": accuracy - 0.25,
            "synthetic_train_minus_test_accuracy": 0.0,
            "active_minus_sham_bootstrap": {
                "mean": accuracy - 0.25,
                "lower": 0.10,
                "upper": 0.90,
            },
            "source_actor_sha256_before": actor_sha,
            "source_actor_sha256_after_active_fit": actor_sha,
            "source_actor_sha256_after": actor_sha,
            "source_actor_sha256_equal": True,
            "active_initial_actor_sha256": actor_sha,
            "sham_initial_actor_sha256": actor_sha,
            "active_sham_initialization_equal": True,
            "source_actor_parameter_count": 558344,
            "active_actor_parameter_count": 558344,
            "sham_actor_parameter_count": 558344,
            "active_sham_parameter_count_equal": True,
            "minibatch_schedule_sha256": schedule_sha,
            "active_minibatch_schedule_sha256": schedule_sha,
            "sham_minibatch_schedule_sha256": schedule_sha,
            "active_sham_shared_minibatch_schedule": True,
            "active_optimizer_contract": {
                "class": "torch.optim.adam.Adam",
                "learning_rate": 3e-4,
                "betas": [0.9, 0.999],
                "eps": 1e-8,
                "weight_decay": 0.0,
                "amsgrad": False,
                "maximize": False,
            },
            "sham_optimizer_contract": {
                "class": "torch.optim.adam.Adam",
                "learning_rate": 3e-4,
                "betas": [0.9, 0.999],
                "eps": 1e-8,
                "weight_decay": 0.0,
                "amsgrad": False,
                "maximize": False,
            },
            "active_train_rows_sha256": "train-rows",
            "sham_train_rows_sha256": "train-rows",
            "active_validation_rows_sha256": "validation-rows",
            "sham_validation_rows_sha256": "validation-rows",
            "active_train_targets_sha256": "train-targets",
            "sham_train_targets_sha256": "train-targets",
            "active_validation_targets_sha256": "validation-targets",
            "sham_validation_targets_sha256": "validation-targets",
            "thresholds": collector.SCIENTIFIC_DECISION_THRESHOLDS[
                "synthetic_seed"
            ],
        }

    seed_reports = [
        seed_report(17, passed=True),
        seed_report(23, passed=True),
        seed_report(41, passed=False),
    ]
    family = collector.gate_synthetic_family(seed_reports)
    final_registered = collector.REGISTERED_CHECKPOINTS["arm0_final"]
    final_manifest_path = tmp_path / "arm0_final" / "collector_manifest.json"
    final_manifest = collector._read_json_strict(final_manifest_path)
    synthetic = {
        **family,
        "checkpoint": final_registered["path"],
        "checkpoint_sha256_before": final_registered["sha256"],
        "checkpoint_sha256_after": final_registered["sha256"],
        "checkpoint_sha256_equal": True,
        "policy_parameter_sha256_before": "policy-arm0-final",
        "policy_parameter_sha256_after": "policy-arm0-final",
        "policy_parameter_sha256_equal": True,
        "device": "cuda",
        "seed_reports": seed_reports,
        "codebook_norm": 0.5,
        "fit_config": {
            "learning_rate": 3e-4,
            "batch_size": 256,
            "max_steps": 1000,
            "validation_interval": 25,
            "patience": 20,
            "min_delta": 1e-4,
        },
        "source_collector_manifest_sha256": collector._file_sha256(
            final_manifest_path
        ),
        "source_snapshot_shards_sha256": final_manifest[
            "snapshot_shards_sha256"
        ],
        "scientific_contract": scientific_contract,
        "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
        "checkpoint_identity": {
            "eligible_for_aggregate": True,
            "checkpoint_id": "arm0_final",
            "checkpoint_update": 32,
            "checkpoint_sha256": final_registered["sha256"],
            "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
        },
        "parameter_counts": {"low_actor": 558344},
        "thresholds": collector.SCIENTIFIC_DECISION_THRESHOLDS[
            "synthetic_seed"
        ],
    }
    collector._write_json(tmp_path / "synthetic_control.json", synthetic)
    return checkpoint_ids


def test_aggregate_recomputes_valid_leaf_evidence(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "CAPACITY_PRESENT_OBJECTIVE_MISSING"
    assert result["artifact_identity"] == {
        "pass": True,
        "errors": [],
        "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
    }
    markdown = (tmp_path / "r27_capacity_autopsy.md").read_text(encoding="utf-8")
    assert "Artifact identity: `True`" in markdown
    assert collector.SCIENTIFIC_CONTRACT_SHA256 in markdown
    assert "inactive tolerance <= 1e-08" in markdown
    assert "parity tolerance <= 1e-06" in markdown
    assert "codebook norm = 0.5" in markdown


def test_aggregate_rejects_missing_or_altered_threshold_evidence(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    static_path = tmp_path / "arm0_update25" / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static.pop("thresholds")
    collector._write_json(static_path, static)
    manifest_path = tmp_path / "arm0_update25" / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)
    synthetic_path = tmp_path / "synthetic_control.json"
    synthetic = collector._read_json_strict(synthetic_path)
    synthetic["seed_reports"][0]["thresholds"]["active_accuracy_min"] = 0.80
    collector._write_json(synthetic_path, synthetic)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )
    reasons = " ".join(result["reasons"])

    assert result["classification"] == "INVALID"
    assert "arm0_update25 threshold evidence mismatch" in reasons
    assert "seed 17 threshold evidence mismatch" in reasons


def test_aggregate_rejects_cross_mapped_parallel_snapshot_rows(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    checkpoint_id = "arm0_update25"
    snapshot_dir = tmp_path / checkpoint_id / "capacity_snapshots"
    shard = snapshot_dir / "reset_0000.npz"
    registered = collector.REGISTERED_CHECKPOINTS[checkpoint_id]
    collector.write_capacity_snapshot_shard(
        shard,
        CapacitySnapshotBatch(
            observation=np.zeros((1, 6), dtype=np.float32),
            actor_hidden=np.zeros((1, 8), dtype=np.float32),
            natural_skill=np.zeros(1, dtype=np.int64),
            previous_skill=np.zeros(1, dtype=np.int64),
            duration_idx=np.zeros(1, dtype=np.int64),
            skill_age=np.zeros(1, dtype=np.int64),
            episode_done_mask=np.zeros(1, dtype=np.bool_),
            reset_id=np.zeros(1, dtype=np.int64),
            reset_seed=np.ones(1, dtype=np.int64),
            episode_id=np.zeros(1, dtype=np.int64),
            env_id=np.ones(1, dtype=np.int64),
            agent_id=np.zeros(1, dtype=np.int64),
            checkpoint_id=np.asarray([checkpoint_id]),
            checkpoint_update=np.asarray(
                [registered["update_idx"]], dtype=np.int64
            ),
        ),
    )
    snapshot_hash = collector._snapshot_shards_sha256(snapshot_dir)
    static_path = tmp_path / checkpoint_id / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static["snapshot_shards_sha256"] = snapshot_hash
    collector._write_json(static_path, static)
    manifest_path = tmp_path / checkpoint_id / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["snapshot_shards_sha256"] = snapshot_hash
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert "reset_0000.npz env_id mapping mismatch" in " ".join(
        result["reasons"]
    )


def test_parallel_manifest_contract_requires_stats_and_cross_field_consistency():
    manifest = {
        "num_envs": 64,
        "n_resets": 64,
        "reset_seeds": list(range(1, 65)),
        "collector_backend": "subproc",
        "collector_start_method": "spawn",
        "parallel_collection_schedule": "step_major_env_id_ascending",
        "env_id_to_reset_id": {
            str(env_id): env_id for env_id in range(64)
        },
        "env_id_to_reset_seed": {
            str(env_id): env_id + 1 for env_id in range(64)
        },
        "active_steps_by_env": {
            str(env_id): 500 for env_id in range(64)
        },
        "termination_reason_by_env": {
            str(env_id): "step_limit" for env_id in range(64)
        },
        "stats": {
            "resets": 64,
            "renewal_events": 128,
            "snapshot_rows": 128,
        },
    }

    assert collector._parallel_manifest_contract_valid(manifest) is True
    missing_stats = dict(manifest)
    missing_stats.pop("stats")
    assert collector._parallel_manifest_contract_valid(missing_stats) is False
    impossible_dwell = dict(manifest)
    impossible_dwell["active_steps_by_env"] = {
        str(env_id): 1 for env_id in range(64)
    }
    assert collector._parallel_manifest_contract_valid(impossible_dwell) is False
    wrong_reset_count = dict(manifest)
    wrong_reset_count["stats"] = dict(manifest["stats"], resets=63)
    assert collector._parallel_manifest_contract_valid(wrong_reset_count) is False
    float_reset_count = dict(manifest)
    float_reset_count["stats"] = dict(manifest["stats"], resets=64.0)
    assert collector._parallel_manifest_contract_valid(float_reset_count) is False
    boolean_steps = dict(manifest)
    boolean_steps["active_steps_by_env"] = {
        str(env_id): True for env_id in range(64)
    }
    boolean_steps["termination_reason_by_env"] = {
        str(env_id): "terminated" for env_id in range(64)
    }
    assert collector._parallel_manifest_contract_valid(boolean_steps) is False


def test_aggregate_structures_corrupt_snapshot_archive_as_invalid(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    checkpoint_id = "arm0_update25"
    snapshot_dir = tmp_path / checkpoint_id / "capacity_snapshots"
    shard = snapshot_dir / "reset_0000.npz"
    shard.write_bytes(b"PK\x03\x04truncated")
    snapshot_hash = collector._snapshot_shards_sha256(snapshot_dir)
    static_path = tmp_path / checkpoint_id / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static["snapshot_shards_sha256"] = snapshot_hash
    collector._write_json(static_path, static)
    manifest_path = tmp_path / checkpoint_id / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["snapshot_shards_sha256"] = snapshot_hash
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert "reset_0000.npz identity read failed" in " ".join(result["reasons"])
    assert collector._read_json_strict(
        tmp_path / "r27_capacity_autopsy.json"
    )["classification"] == "INVALID"


def test_aggregate_rejects_fractional_and_cross_arm_snapshot_identity(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    checkpoint_id = "arm0_update25"
    snapshot_dir = tmp_path / checkpoint_id / "capacity_snapshots"
    shard = snapshot_dir / "reset_0000.npz"
    with np.load(shard, allow_pickle=False) as original:
        fields = {name: original[name] for name in original.files}
    fields["env_id"] = np.asarray([0.9], dtype=np.float64)
    fields["checkpoint_id"] = np.asarray(["arm0_final"])
    np.savez_compressed(shard, **fields)
    snapshot_hash = collector._snapshot_shards_sha256(snapshot_dir)
    static_path = tmp_path / checkpoint_id / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static["snapshot_shards_sha256"] = snapshot_hash
    collector._write_json(static_path, static)
    manifest_path = tmp_path / checkpoint_id / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["snapshot_shards_sha256"] = snapshot_hash
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )
    reasons = " ".join(result["reasons"])

    assert result["classification"] == "INVALID"
    assert "reset_0000.npz env_id dtype mismatch" in reasons
    assert "reset_0000.npz checkpoint_id mapping mismatch" in reasons


def test_generated_static_invalid_remains_artifact_valid_through_aggregate(
    monkeypatch, tmp_path
):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    rows = 10
    reset_ids = np.arange(rows, dtype=np.int64)
    snapshots = CapacitySnapshotBatch(
        observation=np.zeros((rows, 6), dtype=np.float32),
        actor_hidden=np.zeros((rows, 8), dtype=np.float32),
        natural_skill=np.arange(rows, dtype=np.int64) % 4,
        previous_skill=np.zeros(rows, dtype=np.int64),
        duration_idx=np.zeros(rows, dtype=np.int64),
        skill_age=np.zeros(rows, dtype=np.int64),
        episode_done_mask=np.zeros(rows, dtype=np.bool_),
        reset_id=reset_ids,
        reset_seed=27000 + reset_ids,
        episode_id=reset_ids.copy(),
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 6,
        checkpoint_id=np.full(rows, "arm0_update25"),
        checkpoint_update=np.full(rows, 25, dtype=np.int64),
    )

    def nonfinite_parity(*_args, **_kwargs):
        raise FloatingPointError("non-finite live parity evidence")

    monkeypatch.setattr(capacity_audit, "_parity_metrics", nonfinite_parity)
    report = capacity_audit.evaluate_static_checkpoint(
        ManifestAgent().low,
        snapshots,
        checkpoint_id="arm0_update25",
        bootstrap_reps=20,
        bootstrap_seed=27021,
    )
    static_path = tmp_path / "arm0_update25" / "static_capacity.json"
    previous = collector._read_json_strict(static_path)
    registered = collector.REGISTERED_CHECKPOINTS["arm0_update25"]
    report.update(
        {
            "checkpoint_update": registered["update_idx"],
            "source_checkpoint_sha256": registered["sha256"],
            "snapshot_shards_sha256": previous["snapshot_shards_sha256"],
            "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
        }
    )
    collector._write_json(static_path, report)
    manifest_path = tmp_path / "arm0_update25" / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert result["artifact_identity"]["pass"] is True
    assert "threshold evidence mismatch" not in " ".join(result["reasons"])


def test_aggregate_emits_underpowered_for_terminal_synthetic_seed_reports(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    synthetic_path = tmp_path / "synthetic_control.json"
    synthetic = collector._read_json_strict(synthetic_path)
    seed_reports = [
        {
            "seed": seed,
            "status": "UNDERPOWERED",
            "pass": False,
            "reasons": ["fewer than five represented reset groups"],
            "support": {
                "available_rows": 4,
                "available_reset_groups": 4,
                "train_rows": 0,
                "validation_rows": 0,
                "test_rows": 0,
                "train_reset_groups": 0,
                "validation_reset_groups": 0,
                "test_reset_groups": 0,
            },
            "source_actor_sha256_before": f"actor-{seed}",
            "source_actor_sha256_after": f"actor-{seed}",
            "source_actor_sha256_equal": True,
            "source_actor_parameter_count": 558344,
            "thresholds": collector.SCIENTIFIC_DECISION_THRESHOLDS[
                "synthetic_seed"
            ],
        }
        for seed in collector.SCIENTIFIC_SYNTHETIC_SEEDS
    ]
    synthetic.update(collector.gate_synthetic_family(seed_reports))
    synthetic["seed_reports"] = seed_reports
    collector._write_json(synthetic_path, synthetic)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "UNDERPOWERED"
    assert result["artifact_identity"]["pass"] is True


def test_aggregate_rejects_mislabeled_arm_and_update_hash_mismatch(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    manifest_path = tmp_path / "arm0_update25" / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["checkpoint"] = "dist/arm2/standalone_process_core_update_25.pt"
    manifest["checkpoint_update"] = 30
    collector._write_json(manifest_path, manifest)
    static_path = tmp_path / "arm0_update30" / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static["source_checkpoint_sha256"] = "wrong-hash"
    collector._write_json(static_path, static)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )
    reasons = " ".join(result["reasons"])

    assert result["classification"] == "INVALID"
    assert "arm0_update25 manifest path mismatch" in reasons
    assert "arm0_update25 manifest update mismatch" in reasons
    assert "arm0_update30 static report checkpoint hash mismatch" in reasons
    assert "arm0_update30 static report file hash mismatch" in reasons


def test_aggregate_rejects_duplicate_missing_seeds_and_forged_summary(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    synthetic_path = tmp_path / "synthetic_control.json"
    synthetic = collector._read_json_strict(synthetic_path)
    synthetic["seed_reports"] = [
        {"seed": 17, "status": "PASS", "pass": True},
        {"seed": 17, "status": "PASS", "pass": True},
        {"seed": 23, "status": "FAIL", "pass": False},
    ]
    synthetic["passing_seeds"] = 3
    collector._write_json(synthetic_path, synthetic)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )
    reasons = " ".join(result["reasons"])

    assert result["classification"] == "INVALID"
    assert "synthetic seeds must be exactly" in reasons
    assert "synthetic top-level passing_seeds" in reasons


def test_aggregate_rejects_seed_status_inconsistent_with_leaf_metrics(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    synthetic_path = tmp_path / "synthetic_control.json"
    synthetic = collector._read_json_strict(synthetic_path)
    synthetic["seed_reports"][0]["synthetic_code_accuracy"] = 0.0
    synthetic["seed_reports"][0]["synthetic_code_macro_f1"] = 0.0
    synthetic["seed_reports"][0]["synthetic_active_minus_sham_accuracy"] = -0.25
    collector._write_json(synthetic_path, synthetic)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert "seed 17 status/pass mismatch" in " ".join(result["reasons"])


def test_aggregate_rejects_static_pass_inconsistent_with_leaf_metrics(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    static_path = tmp_path / "arm0_update25" / "static_capacity.json"
    static = collector._read_json_strict(static_path)
    static["zero_h"]["pass"] = True
    collector._write_json(static_path, static)
    manifest_path = tmp_path / "arm0_update25" / "collector_manifest.json"
    manifest = collector._read_json_strict(manifest_path)
    manifest["static_report_sha256"] = collector._file_sha256(static_path)
    collector._write_json(manifest_path, manifest)

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert "arm0_update25 zero_h pass mismatch" in " ".join(result["reasons"])


def test_aggregate_structures_nonfinite_input_json_as_invalid(tmp_path):
    checkpoint_ids = _write_valid_scientific_aggregate_fixture(tmp_path)
    (tmp_path / "synthetic_control.json").write_text(
        '{"status": "PASS", "value": NaN}\n', encoding="utf-8"
    )

    result = collector.run_aggregate(
        SimpleNamespace(run_root=str(tmp_path), checkpoint_ids=checkpoint_ids)
    )

    assert result["classification"] == "INVALID"
    assert "non-finite JSON constant" in " ".join(result["reasons"])
    strict_result = collector._read_json_strict(
        tmp_path / "r27_capacity_autopsy.json"
    )
    assert strict_result["classification"] == "INVALID"


def test_aggregate_rejects_forged_top_level_synthetic_summary(tmp_path):
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
                "synthetic_target_mse": 0.01,
                "sham_accuracy": 0.25,
                "synthetic_active_minus_sham_accuracy": 0.70,
                "synthetic_train_minus_test_accuracy": 0.05,
                "active_minus_sham_bootstrap": {"lower": 0.55},
                "active_sham_initialization_equal": True,
                "active_sham_parameter_count_equal": True,
                "active_sham_shared_minibatch_schedule": True,
                "initial_actor_sha256": "actor-init-sha",
                "source_actor_sha256_before": "actor-before-sha",
                "source_actor_sha256_after": "actor-after-sha",
                "source_actor_sha256_equal": True,
                "minibatch_schedule_sha256": "batch-schedule-sha",
                "evidence_finite": True,
                "control_contract_valid": True,
                "active_optimizer_contract": {"class": "Adam"},
                "sham_optimizer_contract": {"class": "Adam"},
                "active_train_rows_sha256": "train-rows-sha",
                "sham_train_rows_sha256": "train-rows-sha",
                "active_validation_rows_sha256": "validation-rows-sha",
                "sham_validation_rows_sha256": "validation-rows-sha",
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

    assert result["classification"] == "INVALID"
    json_result = json.loads(
        (tmp_path / "r27_capacity_autopsy.json").read_text(encoding="utf-8")
    )
    markdown = (tmp_path / "r27_capacity_autopsy.md").read_text(
        encoding="utf-8"
    )
    assert json_result["classification"] == result["classification"]
    assert "INVALID" in markdown
    assert "synthetic seeds must be exactly" in " ".join(result["reasons"])
    assert "No q_A, q_d, q_D, or intrinsic reward" in markdown


def test_registered_checkpoint_identity_rejects_loaded_update_and_hash_mismatch():
    args = collector.parse_args(
        [
            "collect-static",
            "--checkpoint",
            "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
            "--output-dir",
            "unused",
            "--checkpoint-id",
            "arm0_update25",
            "--checkpoint-update",
            "25",
        ]
    )
    contract = collector.validate_scientific_args(args)
    metadata = {
        "update_idx": 25,
        "total_steps": 800000,
        "n_agents": 6,
        "n_skills": 4,
        "preset": "S7-S1",
        "scenario": "energy",
        "low_actor_condition_on_team_code": False,
        "enable_team_intent": True,
    }
    expected_hash = collector.REGISTERED_CHECKPOINTS["arm0_update25"]["sha256"]

    with pytest.raises(ValueError, match="loaded update"):
        collector.validate_registered_checkpoint_identity(
            args,
            metadata,
            loaded_update=30,
            checkpoint_sha256=str(expected_hash),
            scientific_contract=contract,
        )
    with pytest.raises(ValueError, match="checkpoint SHA256"):
        collector.validate_registered_checkpoint_identity(
            args,
            metadata,
            loaded_update=25,
            checkpoint_sha256="wrong-hash",
            scientific_contract=contract,
        )


def test_synthetic_snapshot_binding_rejects_nonfinal_row_identity(tmp_path):
    snapshot_dir = tmp_path / "arm0_final" / "capacity_snapshots"
    batch = CapacitySnapshotBatch(
        observation=np.zeros((1, 6), dtype=np.float32),
        actor_hidden=np.zeros((1, 8), dtype=np.float32),
        natural_skill=np.zeros(1, dtype=np.int64),
        previous_skill=np.zeros(1, dtype=np.int64),
        duration_idx=np.zeros(1, dtype=np.int64),
        skill_age=np.zeros(1, dtype=np.int64),
        episode_done_mask=np.zeros(1, dtype=np.bool_),
        reset_id=np.zeros(1, dtype=np.int64),
        reset_seed=np.ones(1, dtype=np.int64),
        episode_id=np.zeros(1, dtype=np.int64),
        env_id=np.zeros(1, dtype=np.int64),
        agent_id=np.zeros(1, dtype=np.int64),
        checkpoint_id=np.asarray(["arm2_final"]),
        checkpoint_update=np.asarray([32], dtype=np.int64),
    )
    collector.write_capacity_snapshot_shard(
        snapshot_dir / "reset_0000.npz", batch
    )
    final_registered = collector.REGISTERED_CHECKPOINTS["arm0_final"]
    manifest = {
        "checkpoint": final_registered["path"],
        "checkpoint_id": "arm0_final",
        "checkpoint_update": 32,
        "checkpoint_sha256_before": final_registered["sha256"],
        "checkpoint_sha256_equal": True,
        "policy_parameter_sha256_equal": True,
        "n_resets": 64,
        "reset_seeds": list(range(1, 65)),
        "device": "cuda",
        "snapshot_shards_sha256": collector._snapshot_shards_sha256(
            snapshot_dir
        ),
        "scientific_contract_sha256": collector.SCIENTIFIC_CONTRACT_SHA256,
        "scientific_contract": {
            "mode": "R27_G1_SCIENTIFIC",
            "eligible_for_aggregate": True,
        },
    }
    collector._write_json(snapshot_dir.parent / "collector_manifest.json", manifest)
    args = collector.parse_args(
        [
            "synthetic",
            "--checkpoint",
            str(final_registered["path"]),
            "--snapshot-dir",
            str(snapshot_dir),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    contract = collector.validate_scientific_args(args)

    with pytest.raises(ValueError, match="snapshot rows are not arm0_final"):
        collector.validate_synthetic_snapshot_source(
            snapshot_dir,
            batch,
            scientific_contract=contract,
        )


def test_collect_static_writes_shards_manifest_and_immutability(monkeypatch, tmp_path):
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"immutable-checkpoint")
    env_collector = ManifestParallelCollector(5)
    agent = ManifestAgent(num_envs=5)
    config = SimpleNamespace(scenario="energy")
    metadata = {"n_agents": 2, "n_skills": 4, "update_idx": 25}
    monkeypatch.setattr(
        collector, "require_cuda_device", lambda device: torch.device("cpu")
    )
    monkeypatch.setattr(
        collector,
        "_configure_parallel_agent",
        lambda args: (config, metadata, env_collector, agent, 25),
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
            "--num-envs",
            "5",
            "--episode-max-steps",
            "2",
            "--bootstrap-reps",
            "20",
            "--non-scientific-fixture",
        ]
    )

    result = collector.run_collect_static(args)

    assert len(list((output_dir / "capacity_snapshots").glob("*.npz"))) == 5
    manifest = json.loads(
        (output_dir / "collector_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["checkpoint_sha256_equal"] is True
    assert manifest["policy_parameter_sha256_equal"] is True
    assert manifest["scientific_contract"]["mode"] == "NON_SCIENTIFIC_FIXTURE"
    assert manifest["scientific_contract"]["eligible_for_aggregate"] is False
    assert manifest["checkpoint_identity"]["eligible_for_aggregate"] is False
    assert manifest["num_envs"] == 5
    assert manifest["collector_backend"] == "subproc"
    assert manifest["collector_start_method"] == "spawn"
    assert manifest["parallel_collection_schedule"] == (
        "step_major_env_id_ascending"
    )
    assert manifest["env_id_to_reset_id"] == {
        str(env_id): env_id for env_id in range(5)
    }
    assert manifest["snapshot_shards_sha256"] == collector._snapshot_shards_sha256(
        output_dir / "capacity_snapshots"
    )
    assert manifest["static_report_sha256"] == collector._file_sha256(
        output_dir / "static_capacity.json"
    )
    assert manifest["stats"] == {
        "renewal_events": 5,
        "resets": 5,
        "snapshot_rows": 5,
    }
    assert result["static"]["checkpoint_id"] == "fixture_update25"
    assert (output_dir / "static_capacity.md").is_file()


def test_synthetic_fewer_than_five_reset_groups_writes_underpowered_artifacts(
    monkeypatch, tmp_path
):
    checkpoint = tmp_path / "fixture.pt"
    checkpoint.write_bytes(b"immutable-checkpoint")
    snapshot_dir = tmp_path / "snapshots"
    rows = 4
    reset_ids = np.arange(rows, dtype=np.int64)
    snapshots = CapacitySnapshotBatch(
        observation=np.zeros((rows, 6), dtype=np.float32),
        actor_hidden=np.zeros((rows, 8), dtype=np.float32),
        natural_skill=np.arange(rows, dtype=np.int64) % 4,
        previous_skill=np.zeros(rows, dtype=np.int64),
        duration_idx=np.zeros(rows, dtype=np.int64),
        skill_age=np.zeros(rows, dtype=np.int64),
        episode_done_mask=np.zeros(rows, dtype=np.bool_),
        reset_id=reset_ids,
        reset_seed=27000 + reset_ids,
        episode_id=reset_ids.copy(),
        env_id=np.zeros(rows, dtype=np.int64),
        agent_id=np.arange(rows, dtype=np.int64) % 2,
        checkpoint_id=np.full(rows, "fixture_final"),
        checkpoint_update=np.full(rows, 32, dtype=np.int64),
    )
    collector.write_capacity_snapshot_shard(snapshot_dir / "reset_0000.npz", snapshots)
    env = ManifestEnv()
    agent = ManifestAgent()
    monkeypatch.setattr(
        collector, "require_cuda_device", lambda _device: torch.device("cpu")
    )
    monkeypatch.setattr(
        collector,
        "_configure_agent",
        lambda _args: (
            SimpleNamespace(scenario="energy"),
            {"update_idx": 32},
            env,
            agent,
            32,
        ),
    )
    monkeypatch.setattr(
        collector,
        "validate_registered_checkpoint_identity",
        lambda *_args, **_kwargs: {"eligible_for_aggregate": False},
    )
    monkeypatch.setattr(
        collector,
        "validate_synthetic_snapshot_source",
        lambda *_args, **_kwargs: {
            "source_collector_manifest_sha256": "fixture-manifest",
            "source_snapshot_shards_sha256": "fixture-snapshots",
        },
    )
    monkeypatch.setattr(
        collector,
        "evaluate_synthetic_seed",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("underpowered snapshots must not enter fitting")
        ),
    )
    output_dir = tmp_path / "out"
    args = collector.parse_args(
        [
            "synthetic",
            "--checkpoint",
            str(checkpoint),
            "--snapshot-dir",
            str(snapshot_dir),
            "--output-dir",
            str(output_dir),
            "--non-scientific-fixture",
        ]
    )

    result = collector.run_synthetic(args)

    assert result["status"] == "UNDERPOWERED"
    assert [item["seed"] for item in result["seed_reports"]] == [17, 23, 41]
    assert all(item["status"] == "UNDERPOWERED" for item in result["seed_reports"])
    assert result["split"] == {
        "train_reset_ids": [],
        "validation_reset_ids": [],
        "test_reset_ids": [],
    }
    assert (output_dir / "synthetic_control.json").is_file()
    assert (output_dir / "synthetic_control.md").is_file()


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


def test_runner_rejects_nonregistered_reset_count_in_dry_run():
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            "scripts/run_r27_g1_capacity_autopsy_local_cuda.ps1",
            "-DryRun",
            "-NResets",
            "8",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "requires -NResets 64" in output
