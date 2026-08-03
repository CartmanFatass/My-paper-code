from copy import deepcopy
from dataclasses import replace
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process import standalone_train_runner
from ha_ctse_process.standalone_event_support import (
    _event_identity_normalizers,
    _event_live_checkpoint_paths,
    _event_prefix_rows,
    _summarize_event_prefix_rows,
    _summarize_forced_audit,
    enforce_variable_roster_event_resume_boundary,
)
from ha_ctse_process.variable_roster_event import (
    JOIN,
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
    VariableRosterEventCore,
)
from ha_ctse_process.variable_roster_event_checkpoint import (
    event_model_only_checkpoint_payload,
    restore_event_model_only_checkpoint,
    restore_vector_event_checkpoint,
    vector_event_checkpoint_payload,
)
from ha_ctse_process.variable_roster_event_types import (
    BoundaryMember,
    BoundarySnapshot,
    MembershipDelta,
    MembershipTransaction,
)


OBS_DIM = 3
CRITIC_MEMBER_DIM = 2
CRITIC_GLOBAL_DIM = 2
N_SKILLS = 3
ACTION_DIM = 2


def _load_runner():
    path = Path(__file__).parents[1] / "scripts" / "run_dynamic_roster_stage_c.py"
    spec = importlib.util.spec_from_file_location("stage_c_runner_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _SnapshotOnlyEnvironment:
    obs_dim = OBS_DIM
    state_dim = CRITIC_GLOBAL_DIM
    action_dim = ACTION_DIM
    n_uavs = 2
    action_space = SimpleNamespace(dtype=np.dtype(np.int64))

    def __init__(self, value: int):
        self.value = int(value)
        self.restored = False
        self.rng = np.random.default_rng(500 + self.value)

    def event_runtime_snapshot_capability(self):
        return {
            "name": SNAPSHOT_CAPABILITY_NAME,
            "version": SNAPSHOT_CAPABILITY_VERSION,
        }

    def snapshot_event_runtime(self):
        return {
            "active_presentation": ["a", "b"],
            "pending_membership_transaction": None,
            "pending_command_response_state": {"phase": "boundary"},
            "worker_environment_snapshot": {"value": self.value},
            "environment_rng_state": deepcopy(self.rng.bit_generator.state),
        }

    def restore_event_runtime(self, snapshot):
        self.restored = True
        self.value = int(snapshot["worker_environment_snapshot"]["value"])
        self.rng.bit_generator.state = deepcopy(snapshot["environment_rng_state"])

    def close(self):
        pass


def _model_owner(mode: str = "f1", *, seed: int = 17057):
    torch.manual_seed(seed)
    return VariableRosterEventCore(
        architecture_mode=mode,
        obs_dim=OBS_DIM,
        critic_member_dim=CRITIC_MEMBER_DIM,
        critic_global_dim=CRITIC_GLOBAL_DIM,
        n_skills=N_SKILLS,
        action_dim=ACTION_DIM,
        member_hidden_dim=12,
        high_hidden_dim=10,
        low_hidden_dim=8,
        skill_embedding_dim=5,
        gamma=0.99,
        gae_lambda=0.95,
        environment_index=-1,
        device="cpu",
    )


def _runtime(owner, environment_index: int):
    return VariableRosterEventCore(
        architecture_mode=owner.architecture_mode,
        obs_dim=owner.obs_dim,
        critic_member_dim=owner.critic_member_dim,
        critic_global_dim=owner.critic_global_dim,
        n_skills=owner.n_skills,
        action_dim=owner.action_dim,
        member_hidden_dim=owner.member_hidden_dim,
        high_hidden_dim=owner.high_hidden_dim,
        low_hidden_dim=owner.low_hidden_dim,
        skill_embedding_dim=owner.skill_embedding_dim,
        gamma=owner.gamma,
        gae_lambda=owner.gae_lambda,
        environment_index=environment_index,
        opportunity_seed=77_057,
        frontier_seed=77_057,
        action_seed=97_057,
        rng_episode_id=environment_index,
        opportunity_stream_id=0,
        frontier_stream_id=1,
        action_stream_id=0,
        device="cpu",
        shared_models_from=owner,
    )


def _snapshot(core, *, frontier=()):
    members = (
        BoundaryMember.make(
            "a",
            0,
            [0.1, 0.2, 0.3],
            [0.4, -0.1],
            obs_dim=OBS_DIM,
            critic_member_dim=CRITIC_MEMBER_DIM,
        ),
        BoundaryMember.make(
            "b",
            0,
            [-0.2, 0.5, 0.7],
            [-0.3, 0.6],
            obs_dim=OBS_DIM,
            critic_member_dim=CRITIC_MEMBER_DIM,
        ),
    )
    return BoundarySnapshot.make(
        core.physical_time,
        members,
        [float(core.physical_time), -0.25],
        critic_global_dim=CRITIC_GLOBAL_DIM,
        frontier=frontier,
    )


def _initial_join(core):
    pre = BoundarySnapshot.make(
        0,
        (),
        [0.0, -0.25],
        critic_global_dim=CRITIC_GLOBAL_DIM,
    )
    post = _snapshot(core, frontier=("a", "b"))
    core.apply_transaction(
        MembershipTransaction(
            pre,
            (MembershipDelta(JOIN, "a", 0), MembershipDelta(JOIN, "b", 0)),
            post,
        ),
        teacher_order=("a", "b"),
        teacher_actions={"a": 0, "b": 1},
    )
    return post


def _assert_model_equal(left, right):
    for left_module, right_module in (
        (left.commitment_model, right.commitment_model),
        (left.event_critic, right.event_critic),
        (left.low_actor, right.low_actor),
        (left.low_critic, right.low_critic),
    ):
        for name, tensor in left_module.state_dict().items():
            assert torch.equal(tensor, right_module.state_dict()[name])


def test_strict_sixteen_env_vector_roundtrip_preserves_future_behavior():
    owner = _model_owner()
    cores = [_runtime(owner, index) for index in range(16)]
    boundaries = []
    for core in cores:
        boundaries.append(
            {
                "physical_time": 0,
                "episode_id": core.environment_index,
                "snapshot": _initial_join(core),
            }
        )
    source_envs = [_SnapshotOnlyEnvironment(100 + index) for index in range(16)]
    source_collector = SyncEnvCollector(source_envs)
    counters = {
        "total_steps": 0,
        "update_idx": 0,
        "high_optimizer_steps": 0,
        "low_optimizer_steps": 0,
        "next_episode_id": 16,
        "intrinsic_applied_count": 0,
    }
    optimizer_states = {"high": {"steps": 0}, "low": {"steps": 0}}
    normalizers = _event_identity_normalizers()
    payload = vector_event_checkpoint_payload(
        model_owner=owner,
        cores=cores,
        collector_snapshot=source_collector.snapshot_event_runtime(),
        current_boundaries=boundaries,
        optimizer_states=optimizer_states,
        normalizer_states=normalizers,
        counters=counters,
    )
    bundle = payload["event_architecture"]
    assert len(bundle["runtime_payloads"]) == 16
    assert "commitment_model_state" not in bundle["runtime_payloads"][0]
    assert "collector_snapshot" not in bundle["runtime_payloads"][0]

    restored_owner = _model_owner(seed=999)
    restored_cores = [_runtime(restored_owner, index) for index in range(16)]
    restored_envs = [_SnapshotOnlyEnvironment(-index - 1) for index in range(16)]
    restored_collector = SyncEnvCollector(restored_envs)
    restored_optimizer, restored_normalizers, restored_counters = (
        restore_vector_event_checkpoint(
            payload,
            model_owner=restored_owner,
            cores=restored_cores,
            collector=restored_collector,
        )
    )
    _assert_model_equal(owner, restored_owner)
    assert restored_optimizer == optimizer_states
    assert restored_normalizers == normalizers
    assert restored_counters == counters
    assert [env.value for env in restored_envs] == list(range(100, 116))

    for original, restored in zip(cores, restored_cores):
        original_snapshot = _snapshot(original)
        restored_snapshot = _snapshot(restored)
        original_actions, original_logp, original_values = original.low_step(
            original_snapshot, deterministic=True
        )
        restored_actions, restored_logp, restored_values = restored.low_step(
            restored_snapshot, deterministic=True
        )
        assert torch.equal(original_actions, restored_actions)
        assert torch.allclose(original_logp, restored_logp, atol=1e-7, rtol=0.0)
        assert torch.allclose(original_values, restored_values, atol=1e-7, rtol=0.0)
        original.complete_primitive_transition(0.25)
        restored.complete_primitive_transition(0.25)
        original_tx = MembershipTransaction(
            _snapshot(original), (), _snapshot(original)
        )
        restored_tx = MembershipTransaction(
            _snapshot(restored), (), _snapshot(restored)
        )
        original_result = original.apply_transaction(
            original.bind_due_frontier(original_tx), deterministic_policy=True
        )
        restored_result = restored.apply_transaction(
            restored.bind_due_frontier(restored_tx), deterministic_policy=True
        )
        assert original_result.final_skills == restored_result.final_skills
        assert [row.combined_action for row in original_result.token_rows] == [
            row.combined_action for row in restored_result.token_rows
        ]
        assert [row.old_token_log_probability for row in original.high_ledger] == pytest.approx(
            [row.old_token_log_probability for row in restored.high_ledger], abs=1e-7
        )
        assert [row.old_log_probability for row in original.low_ledger] == pytest.approx(
            [row.old_log_probability for row in restored.low_ledger], abs=1e-7
        )
        assert int(original.opportunity_rng.integers(1, 20)) == int(
            restored.opportunity_rng.integers(1, 20)
        )
        assert tuple(original.frontier_rng.permutation(["a", "b"])) == tuple(
            restored.frontier_rng.permutation(["a", "b"])
        )
        assert float(original.action_rng.random()) == pytest.approx(
            float(restored.action_rng.random()), abs=0.0
        )

    missing = deepcopy(payload)
    del missing["event_architecture"]["runtime_payloads"][3]["rng_ledger"]
    rejection_owner = _model_owner()
    with pytest.raises(ValueError, match="runtime field schema mismatch"):
        restore_vector_event_checkpoint(
            missing,
            model_owner=rejection_owner,
            cores=[_runtime(rejection_owner, index) for index in range(16)],
            collector=SyncEnvCollector(
                [_SnapshotOnlyEnvironment(index) for index in range(16)]
            ),
        )


def test_model_only_fresh_eval_and_dual_prefix_reads_are_strict():
    f0_owner = _model_owner("f0")
    model_payload = event_model_only_checkpoint_payload(
        model_owner=f0_owner,
        normalizer_states=_event_identity_normalizers(),
        total_steps=320_000,
        update_idx=250,
    )
    assert model_payload["event_architecture"][
        "runtime_state_absent_for_fresh_eval"
    ] is True
    assert "runtime_payloads" not in model_payload["event_architecture"]
    restored_owner = _model_owner("f0", seed=99)
    normalizers, total_steps, update_idx = restore_event_model_only_checkpoint(
        model_payload, model_owner=restored_owner
    )
    _assert_model_equal(f0_owner, restored_owner)
    assert normalizers == _event_identity_normalizers()
    assert (total_steps, update_idx) == (320_000, 250)

    core = _runtime(f0_owner, 0)
    snapshot = _initial_join(core)
    core.low_step(snapshot, deterministic=True)
    core.complete_primitive_transition(0.0)
    core.records["a"].active_gap_remaining = 0
    core.records["b"].active_gap_remaining = 0
    unbound = MembershipTransaction(_snapshot(core), (), _snapshot(core))
    result = core.apply_transaction(
        core.bind_due_frontier(unbound),
        teacher_order=("a", "b"),
        teacher_actions={"a": 2, "b": 1},
    )
    rows = _event_prefix_rows(core, result.token_rows, episode_id=7)
    assert len(rows) == 1
    row = rows[0]
    assert row["token_position"] == 1
    assert np.array_equal(
        np.asarray(row["p_initial"]) > 0.0,
        np.asarray(row["p_working"]) > 0.0,
    )
    assert row["actual_replay_logp_error"] <= 1e-6
    assert row["actual_replay_probability_error"] <= 1e-6
    assert row["common_support_applied_vs_initial_tv"] <= 1e-12
    assert np.allclose(
        row["p_actual_replay"], row["p_initial"], atol=0.0, rtol=0.0
    )

    corrupted = replace(
        result.token_rows[1],
        old_token_log_probability=(
            float(result.token_rows[1].old_token_log_probability) + 0.25
        ),
    )
    corrupted_row = _event_prefix_rows(core, [corrupted], episode_id=7)[0]
    assert corrupted_row["actual_replay_logp_error"] > 0.20

    summary_rows = [
        {
            **row,
            "episode_id": 1,
            "owner_index": 1,
            "owner_incumbent_skill": 1,
            "working_skills": [1, 1],
            "p_initial": [0.20, 0.50, 0.30],
            "p_working": [0.30, 0.40, 0.30],
        },
        {
            **row,
            "episode_id": 2,
            "owner_index": 1,
            "owner_incumbent_skill": 2,
            "working_skills": [1, 2],
            "p_initial": [0.20, 0.50, 0.30],
            "p_working": [0.30, 0.40, 0.30],
        },
        {
            **row,
            "episode_id": 3,
            "owner_index": 1,
            "owner_incumbent_skill": 2,
            "working_skills": [2, 2],
            "p_initial": [0.20, 0.30, 0.50],
            "p_working": [0.20, 0.40, 0.40],
        },
    ]
    direction_summary = _summarize_event_prefix_rows(
        summary_rows, persistent_skill=1, architecture_mode="f1"
    )
    assert direction_summary["directional_eligible_rows"] == 2
    assert direction_summary["directional_case_counts"] == {
        "no_persistent_in_roster": 1,
        "other_persistent_in_roster": 1,
        "excluded_focal_persistent": 1,
    }

    missing = deepcopy(model_payload)
    del missing["event_architecture"]["low_actor_state"]
    with pytest.raises(ValueError, match="missing fields"):
        restore_event_model_only_checkpoint(
            missing, model_owner=_model_owner("f0")
        )


def test_forced_audit_summary_has_registered_shape_and_no_training_side_effect():
    effects = np.zeros((128, 3, 2, 4), dtype=np.float64)
    effects[:, 0, :, :] = np.array([0.10, 0.90, 0.05, 0.75])
    effects[:, 1, :, :] = np.array([0.90, 0.10, 0.80, 0.05])
    effects[:, 2, :, :] = np.array([0.40, 0.40, 0.30, 0.30])
    summary = _summarize_forced_audit(
        effects,
        natural_skill_counts=[400, 400, 400],
    )
    assert summary["snapshot_count"] == 128
    assert summary["skills_per_snapshot"] == 3
    assert summary["replicas_per_skill"] == 2
    assert summary["steps_per_replica"] == 12
    assert summary["forced_environment_steps"] == 9_216
    assert summary["effect_shape"] == [128, 3, 2, 4]
    assert summary["persistent_like_skill"] != summary["reactive_like_skill"]
    assert summary["executable_naturally_used_skills"] is True


def test_runner_dry_validation_and_registered_outcome_priority(
    tmp_path, monkeypatch
):
    runner = _load_runner()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("dry preflight crossed a forbidden execution boundary")

    monkeypatch.setattr(runner.subprocess, "Popen", forbidden)
    monkeypatch.setattr(standalone_train_runner, "create_collector", forbidden)
    monkeypatch.setattr(standalone_train_runner, "train_loop", forbidden)
    monkeypatch.setattr(torch.optim.Adam, "step", forbidden)
    output_root = tmp_path / "dry"
    result = runner.run_pair(
        SimpleNamespace(
            output_root=output_root,
            python="python",
            poll_seconds=0.0,
            resume_f0=None,
            resume_f1=None,
            dry_validate=True,
        )
    )
    assert result["status"] == "DRY_VALID"
    assert result["environment_steps"] == 0
    assert result["optimizer_steps"] == 0
    assert result["preflight"]["commands_validated"] == 2
    assert result["preflight"]["checkpoint_schema_version"] == 3
    assert not output_root.exists()
    assert result["contract"] == {
        "num_envs_per_arm": 16,
        "steps_per_arm": 320_000,
        "updates": 250,
        "optimizer_steps_per_path": 1_000,
        "concurrent_arms": True,
    }
    for mode in ("f0", "f1"):
        command = result["commands"][mode]
        assert command[command.index("--event_architecture_mode") + 1] == mode
        assert command[command.index("--num_envs") + 1] == "16"
        assert command[command.index("--collector_backend") + 1] == "subproc"
        assert command[command.index("--device") + 1] == "cuda"
        assert command[command.index("--rollout_length") + 1] == "80"
        assert command[command.index("--total_timesteps") + 1] == "320000"

    classify = runner._classify_outcome
    defaults = dict(
        implementation_valid=True,
        h1_supported=False,
        f0_task=False,
        f1_task=False,
        f0_skills=False,
        f1_skills=False,
        timing_prerequisites=False,
        conditional_h3_supported=False,
    )
    invalid = {**defaults, "implementation_valid": False, "h1_supported": True}
    assert classify(**invalid)[0] == "INVALID_IMPLEMENTATION"
    assert classify(**{**defaults, "h1_supported": True})[0] == "SUPPORT_H1_ON_TESTBED"
    assert classify(**{**defaults, "f0_task": True})[0] == "SUPPORT_H0_STOP_AT_F0"
    assert classify(**defaults)[0] == "SUPPORT_H2_SKILL_LIMIT"
    timing = {
        **defaults,
        "f1_task": True,
        "f1_skills": True,
        "timing_prerequisites": True,
        "conditional_h3_supported": True,
    }
    assert classify(**timing)[0] == "CONDITIONAL_H3_TIMING_LIMIT"
    assert classify(**{**timing, "conditional_h3_supported": False})[0] == (
        "VALID_MIXED_UNCATEGORIZED"
    )


def test_nonexistent_resume_path_fails_closed_before_runtime(tmp_path):
    config = SimpleNamespace(high_controller="variable_roster_event")
    args = SimpleNamespace(resume_from=str(tmp_path / "missing.pt"))
    with pytest.raises(ValueError, match="--resume_from fails closed"):
        enforce_variable_roster_event_resume_boundary(config, args)

    checkpoint_dir = tmp_path / "checkpoints"
    assert [path.name for path in _event_live_checkpoint_paths(
        checkpoint_dir, update_idx=0, save_interval=10
    )] == ["latest.pt", "update_000_live.pt"]
    assert [path.name for path in _event_live_checkpoint_paths(
        checkpoint_dir, update_idx=1, save_interval=10
    )] == ["latest.pt"]
    assert [path.name for path in _event_live_checkpoint_paths(
        checkpoint_dir, update_idx=10, save_interval=10
    )] == ["latest.pt", "update_010_live.pt"]


def test_timing_read_uses_recorded_opportunities_and_post_action_completion():
    runner = _load_runner()

    def timing_row(time, wave, arrival, opportunities, completed):
        return {
            "episode_id": 0,
            "physical_time": time,
            "active_keys": ["a", "b"],
            "active_skills": [0, 0],
            "opportunity_keys_at_time": opportunities,
            "wave_index": wave,
            "wave_arrival_time": arrival,
            "wave_required": 2,
            "wave_completed_before_action": max(completed - 1, 0),
            "wave_completed_after_action": completed,
            "persistent_owner_exists": True,
            "persistent_owner_exists_after_action": True,
        }

    arm = {
        "forced_audit": {
            "persistent_like_skill": 1,
            "reactive_like_skill": 2,
        },
        "timing_rows": [
            timing_row(0, 0, 0, ["a"], 0),
            timing_row(1, 0, 0, [], 1),
            timing_row(2, 0, 0, ["b"], 2),
            timing_row(10, 1, 10, [], 0),
            timing_row(11, 1, 10, [], 0),
            timing_row(12, 1, 10, [], 0),
        ],
    }
    timing = runner._timing_read(arm)
    assert timing["opportunity_evidence_source"] == (
        "natural_frontier_t_w_through_t_w_plus_2"
    )
    assert timing["opportunity_window_member_counts"] == [2, 0]
    assert timing["timing_infeasible_uncompleted_fraction"] == pytest.approx(1.0)
    assert timing["feasible_minus_infeasible_completion_ci95"][0] > 0.0
    assert timing["conditional_h3_supported"] is True
    assert runner._timing_prerequisites(
        f1_skills=True,
        eligible_natural_rows=1_023,
        natural_prefix_tv=True,
        directional_composition=True,
        f1_minus_f0_utility=False,
    ) is False
    assert runner._timing_prerequisites(
        f1_skills=True,
        eligible_natural_rows=1_024,
        natural_prefix_tv=True,
        directional_composition=True,
        f1_minus_f0_utility=False,
    ) is True
