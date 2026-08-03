from copy import deepcopy
from dataclasses import fields
import math
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process import standalone_train_runner
from ha_ctse_process import checkpoint_io
from ha_ctse_process import variable_roster_event
from ha_ctse_process import variable_roster_event_batching
from ha_ctse_process import variable_roster_event_models
from ha_ctse_process import variable_roster_event_support
from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.r30_fixed_clock import FixedClockAREditPolicy
from ha_ctse_process.standalone_contracts import (
    enforce_variable_roster_event_contract,
)
from ha_ctse_process.variable_roster_event import (
    ACTIVE,
    EVENT_ARCHITECTURE_SCHEMA_VERSION,
    EVENT_CONTROLLER,
    JOIN,
    OPPORTUNITY_SCHEDULE_NAME,
    REJOIN,
    SNAPSHOT_CAPABILITY_NAME,
    SNAPSHOT_CAPABILITY_VERSION,
    TEMPORARILY_ABSENT,
    TEMPORARY_LEAVE,
    TERMINAL,
    TERMINAL_LEAVE,
    VariableRosterEventCore,
    apply_event_ppo_update,
    centered_logits,
    pack_event_ppo_data,
)
from ha_ctse_process.variable_roster_event_batching import batched_low_step
from ha_ctse_process.variable_roster_event_types import (
    ActiveRoutingView,
    BoundaryMember,
    BoundarySnapshot,
    MembershipDelta,
    MembershipTransaction,
    PackedActiveBatch,
)
from ha_ctse_process.variable_roster_event_support import (
    ROLLOUT_TRUNCATION,
    TEMPORARY_BOUNDARY,
)


OBS_DIM = 3
CRITIC_MEMBER_DIM = 2
CRITIC_GLOBAL_DIM = 2
N_SKILLS = 3
ACTION_DIM = 2

FEATURES = {
    "a": (np.array([0.1, 0.2, 0.3]), np.array([0.5, -0.2])),
    "b": (np.array([-0.4, 0.6, 0.2]), np.array([-0.1, 0.7])),
    "c": (np.array([0.9, -0.3, 0.1]), np.array([0.3, 0.4])),
    "x": (np.array([0.1, 0.2, 0.3]), np.array([0.5, -0.2])),
    "y": (np.array([-0.4, 0.6, 0.2]), np.array([-0.1, 0.7])),
}


def test_variable_roster_event_support_owns_stateless_helpers():
    module = torch.nn.Sequential(torch.nn.Linear(2, 3), torch.nn.Linear(3, 1))
    assert list(variable_roster_event_support._state_dict_shapes(module).items()) == [
        (name, tuple(tensor.shape)) for name, tensor in module.state_dict().items()
    ]
    assert variable_roster_event_support.parameter_count(module) == sum(
        parameter.numel() for parameter in module.parameters()
    )
    assert torch.equal(
        variable_roster_event_support.normalized_log_age(torch.tensor([-4, 0, 499])),
        torch.log1p(torch.tensor([0.0, 0.0, 499.0])) / math.log1p(500.0),
    )

    expected_rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([17, 3, 11]))
    )
    actual_rng = variable_roster_event_support.make_pcg64_rng(17, 3, 11)
    assert np.array_equal(actual_rng.random(5), expected_rng.random(5))
    assert variable_roster_event_support.inverse_cdf_action([1.0, 3.0], 0.249) == 0
    assert variable_roster_event_support.inverse_cdf_action([1.0, 3.0], 0.25) == 1
    with pytest.raises(ValueError, match="probabilities are invalid"):
        variable_roster_event_support.inverse_cdf_action([-1.0, 2.0], 0.5)
    with pytest.raises(ValueError, match=r"\[0,1\)"):
        variable_roster_event_support.inverse_cdf_action([1.0], 1.0)


def test_variable_roster_event_model_and_boundary_owners_are_one_way():
    owner_names = (
        "EventCommitmentPolicy",
        "EventHighCritic",
        "Discrete",
        "Box",
        "EventLowActor",
        "EventActiveSetLowCritic",
        "SuppliedExecutorLowSentinel",
    )
    assert all(hasattr(variable_roster_event_models, name) for name in owner_names)
    assert not any(hasattr(variable_roster_event, name) for name in owner_names)
    assert variable_roster_event_batching.batched_low_step is batched_low_step
    assert not hasattr(variable_roster_event, "batched_low_step")
    assert "variable_roster_event_batching" not in variable_roster_event.__dict__
    assert variable_roster_event_support.BOUNDARY_KINDS == (
        variable_roster_event_support.ORDINARY_BOUNDARY,
        variable_roster_event_support.ROLLOUT_TRUNCATION,
        variable_roster_event_support.TEMPORARY_BOUNDARY,
        variable_roster_event_support.TERMINAL_BOUNDARY,
    )


def make_core(
    mode="f1",
    *,
    model_seed=17,
    opportunity_seed=142,
    action_seed=61,
    rng_episode_id=0,
    environment_index=0,
    shared_models_from=None,
    device="cpu",
):
    torch.manual_seed(int(model_seed))
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
        gamma=0.9,
        gae_lambda=0.8,
        environment_index=environment_index,
        opportunity_seed=opportunity_seed,
        frontier_seed=51,
        action_seed=action_seed,
        rng_episode_id=rng_episode_id,
        device=device,
        shared_models_from=shared_models_from,
    )


def boundary(core, keys, *, frontier=(), epochs=None, reverse=False):
    ordered = list(keys)
    if reverse:
        ordered = list(reversed(ordered))
    epochs = dict(epochs or {})
    members = []
    time_shift = 0.01 * float(core.physical_time)
    for key in ordered:
        if key in epochs:
            epoch = int(epochs[key])
        else:
            epoch = int(core.records[key].membership_epoch)
        obs, critic = FEATURES[key]
        members.append(
            BoundaryMember.make(
                key,
                epoch,
                obs.astype(np.float32) + time_shift,
                critic.astype(np.float32) - time_shift,
                obs_dim=OBS_DIM,
                critic_member_dim=CRITIC_MEMBER_DIM,
            )
        )
    return BoundarySnapshot.make(
        core.physical_time,
        members,
        np.array([float(core.physical_time), -0.25], dtype=np.float32),
        critic_global_dim=CRITIC_GLOBAL_DIM,
        frontier=frontier,
    )


def initial_join(core, keys=("a", "b"), *, order=None, actions=None, reverse=False):
    pre = BoundarySnapshot.make(
        core.physical_time,
        (),
        np.array([0.0, -0.25], dtype=np.float32),
        critic_global_dim=CRITIC_GLOBAL_DIM,
    )
    post = boundary(
        core,
        keys,
        frontier=keys,
        epochs={key: 0 for key in keys},
        reverse=reverse,
    )
    transaction = MembershipTransaction(
        pre,
        tuple(MembershipDelta(JOIN, key, 0) for key in keys),
        post,
    )
    return core.apply_transaction(
        transaction,
        teacher_order=tuple(order or keys),
        teacher_actions=dict(actions or {key: index for index, key in enumerate(keys)}),
    )


def no_membership_transaction(core, keys, frontier):
    pre = boundary(core, keys)
    post = boundary(core, keys, frontier=frontier)
    return MembershipTransaction(pre, (), post)


def low_then_transition(core, keys, reward):
    snapshot = boundary(core, keys)
    core.low_step(snapshot, deterministic=True)
    core.complete_primitive_transition(reward)


def run_trace():
    core = make_core("f1")
    diagnostics = {}

    first = initial_join(core, actions={"a": 0, "b": 1})
    assert first.sampled_order == ("a", "b")
    assert core.records["a"].active_gap_remaining == 1
    assert core.records["b"].active_gap_remaining == 1

    # A stale membership epoch must fail before any lifecycle mutation.
    stale_pre = boundary(core, ("a", "b"))
    stale_post = boundary(core, ("a",))
    before = (core.active_skills(), core.records["b"].status)
    with pytest.raises(ValueError, match="stale epoch"):
        core.apply_transaction(
            MembershipTransaction(
                stale_pre,
                (MembershipDelta(TEMPORARY_LEAVE, "b", 99),),
                stale_post,
            )
        )
    assert (core.active_skills(), core.records["b"].status) == before

    low_then_transition(core, ("a", "b"), 1.0)
    assert set(core.due_frontier()) == {"a", "b"}

    second = core.apply_transaction(
        no_membership_transaction(core, ("a", "b"), ("a", "b")),
        teacher_order=("a", "b"),
        teacher_actions={"a": 2, "b": 1},
    )
    assert [row.action_kind for row in second.token_rows] == ["SET", "KEEP"]
    low_then_transition(core, ("a", "b"), 0.5)

    a_closed_before_leave = sum(
        row.lifecycle_key == "a" for row in core.closed_event_rows
    )
    frozen_b_actor = core.records["b"].low_actor_hidden.copy()
    frozen_b_critic = core.records["b"].low_critic_hidden.copy()
    frozen_b_age = core.records["b"].skill_active_age
    frozen_b_gap = core.records["b"].active_gap_remaining
    leave = MembershipTransaction(
        boundary(core, ("a", "b")),
        (MembershipDelta(TEMPORARY_LEAVE, "b", 0),),
        boundary(core, ("a",)),
    )
    core.apply_transaction(leave)
    assert core.records["b"].status == TEMPORARILY_ABSENT
    assert sum(row.lifecycle_key == "a" for row in core.closed_event_rows) == (
        a_closed_before_leave
    )
    diagnostics["a_closed_before_leave"] = a_closed_before_leave

    low_then_transition(core, ("a",), 7.0)
    low_then_transition(core, ("a",), 7.0)
    assert core.records["b"].skill_active_age == frozen_b_age
    assert core.records["b"].active_gap_remaining == frozen_b_gap
    assert np.array_equal(core.records["b"].low_actor_hidden, frozen_b_actor)
    assert np.array_equal(core.records["b"].low_critic_hidden, frozen_b_critic)

    rejoin_pre = boundary(core, ("a",))
    rejoin_post = boundary(
        core,
        ("a", "b"),
        frontier=("b",),
        epochs={"a": 0, "b": 1},
    )
    rejoin = core.apply_transaction(
        MembershipTransaction(
            rejoin_pre,
            (MembershipDelta(REJOIN, "b", 0),),
            rejoin_post,
        ),
        teacher_order=("b",),
        teacher_actions={"b": 1},
    )
    assert rejoin.token_rows[0].action_kind == "KEEP"
    assert core.records["b"].membership_epoch == 1
    assert np.array_equal(core.records["b"].low_actor_hidden, frozen_b_actor)
    assert np.array_equal(core.records["b"].low_critic_hidden, frozen_b_critic)

    truncate_snapshot = boundary(core, ("a", "b"))
    core.truncate_policy_version(truncate_snapshot)
    assert core.policy_version == 1
    assert all(
        record.open_event_trace is not None
        and not record.open_event_trace.actor_valid
        for record in (core.records["a"], core.records["b"])
    )

    for _ in range(8):
        low_then_transition(core, ("a", "b"), 0.25)
    assert core.due_frontier() == ("a",)
    core.apply_transaction(
        no_membership_transaction(core, ("a", "b"), ("a",)),
        teacher_order=("a",),
        teacher_actions={"a": 2},
    )
    low_then_transition(core, ("a", "b"), 0.25)
    assert core.due_frontier() == ("b",)

    terminal = MembershipTransaction(
        boundary(core, ("a", "b")),
        (MembershipDelta(TERMINAL_LEAVE, "a", 0),),
        boundary(core, ("b",), frontier=("b",), epochs={"b": 1}),
    )
    final = core.apply_transaction(
        terminal,
        teacher_order=("b",),
        teacher_actions={"b": 1},
    )
    assert final.final_skills == {"b": 1}
    assert core.records["a"].status == TERMINAL
    assert core.records["a"].high_hidden.size == 0
    assert any(
        row.lifecycle_key == "b"
        and not row.actor_valid
        and row.policy_version == 1
        for row in core.closed_event_rows
    )
    diagnostics.update(
        {
            "frozen_b_actor": frozen_b_actor,
            "frozen_b_critic": frozen_b_critic,
            "frozen_b_age": frozen_b_age,
            "frozen_b_gap": frozen_b_gap,
        }
    )
    return core, diagnostics


class SnapshotEnv:
    obs_dim = OBS_DIM
    state_dim = CRITIC_GLOBAL_DIM
    action_dim = ACTION_DIM
    n_uavs = 1
    action_space = SimpleNamespace(dtype=np.dtype(np.int64))

    def __init__(self, value=5):
        self.value = int(value)
        self.rng = np.random.default_rng(404)
        self.restored = None

    def event_runtime_snapshot_capability(self):
        return {
            "name": SNAPSHOT_CAPABILITY_NAME,
            "version": SNAPSHOT_CAPABILITY_VERSION,
        }

    def snapshot_event_runtime(self):
        return {
            "active_presentation": ["b"],
            "pending_membership_transaction": None,
            "pending_command_response_state": {"phase": "idle"},
            "worker_environment_snapshot": {"value": self.value},
            "environment_rng_state": deepcopy(self.rng.bit_generator.state),
        }

    def restore_event_runtime(self, snapshot):
        self.restored = deepcopy(snapshot)
        self.value = int(snapshot["worker_environment_snapshot"]["value"])
        self.rng.bit_generator.state = deepcopy(snapshot["environment_rng_state"])

    def close(self):
        pass


def test_hand_authored_lifecycle_transaction_trace():
    core, diagnostics = run_trace()
    assert core.records["b"].status == ACTIVE
    assert core.records["b"].membership_epoch == 1
    assert any(row.boundary_kind == TEMPORARY_BOUNDARY for row in core.closed_event_rows)
    assert any(row.boundary_kind == ROLLOUT_TRUNCATION for row in core.closed_event_rows)
    assert diagnostics["frozen_b_age"] >= 1
    assert diagnostics["frozen_b_gap"] >= 1
    assert all(
        1 <= row.sampled_replacement_gap <= 19 for row in core.high_ledger
    )
    concurrent = [row for row in core.high_ledger if len(row.frontier) == 2]
    assert concurrent
    assert all(
        abs(row.order_log_probability + math.lgamma(3.0)) <= 1.0e-12
        for row in concurrent
    )


def test_sampling_replay_parity_and_no_routing_metadata_in_model_batch():
    core, _ = run_trace()
    errors = [
        abs(core.replay_token_log_probability(row) - row.old_token_log_probability)
        for row in core.high_ledger
    ]
    assert max(errors, default=0.0) <= 1.0e-6
    model_fields = {item.name for item in fields(PackedActiveBatch)}
    assert "lifecycle_key" not in model_fields
    assert "membership_epoch" not in model_fields
    assert ActiveRoutingView.__dataclass_fields__.keys() == {
        "lifecycle_keys",
        "membership_epochs",
    }


def test_permutation_compatibility_relabels_outputs_without_changing_probability():
    left = make_core("f1", model_seed=29, opportunity_seed=142)
    right = make_core("f1", model_seed=29, opportunity_seed=142)
    left_result = initial_join(
        left,
        keys=("a", "b"),
        order=("a", "b"),
        actions={"a": 0, "b": 1},
    )
    right_result = initial_join(
        right,
        keys=("x", "y"),
        order=("x", "y"),
        actions={"x": 0, "y": 1},
        reverse=True,
    )
    assert np.allclose(
        [row.old_token_log_probability for row in left_result.token_rows],
        [row.old_token_log_probability for row in right_result.token_rows],
        atol=1.0e-6,
    )
    assert np.allclose(
        [row.old_owner_value for row in left_result.token_rows],
        [row.old_owner_value for row in right_result.token_rows],
        atol=1.0e-6,
    )
    assert left.active_skills() == {"a": 0, "b": 1}
    assert right.active_skills() == {"x": 0, "y": 1}


def test_f0_f1_capacity_match_reduction_and_constructive_common_support_control():
    f0 = make_core("f0", model_seed=83)
    f1 = make_core("f1", model_seed=83)
    assert f0.model_signature() == f1.model_signature()
    assert f0.model_parameter_count() == f1.model_parameter_count()
    for left_module, right_module in (
        (f0.commitment_model, f1.commitment_model),
        (f0.event_critic, f1.event_critic),
        (f0.low_actor, f1.low_actor),
        (f0.low_critic, f1.low_critic),
    ):
        for name, tensor in left_module.state_dict().items():
            assert torch.equal(tensor, right_module.state_dict()[name])

    collector_snapshot = SyncEnvCollector([SnapshotEnv()]).snapshot_event_runtime()
    common_checkpoint = {
        "collector_snapshot": collector_snapshot,
        "current_observation_state_boundary": {"time": 0},
        "optimizer_states": {"high": {"steps": 0}, "low": {"steps": 0}},
        "normalizer_states": {"high": {"mean": 0.0}, "low": {"mean": 0.0}},
    }
    f0_bundle = f0.checkpoint_payload(**common_checkpoint)["event_architecture"]
    f1_bundle = f1.checkpoint_payload(**common_checkpoint)["event_architecture"]
    assert set(f0_bundle) == set(f1_bundle)
    assert f0_bundle["optimizer_states"] == f1_bundle["optimizer_states"]
    assert f0_bundle["normalizer_states"] == f1_bundle["normalizer_states"]
    assert f0_bundle["architecture_mode"] == "f0"
    assert f1_bundle["architecture_mode"] == "f1"

    member = torch.zeros(f0.member_hidden_dim)
    hidden = torch.zeros(f0.high_hidden_dim)
    initial_summary = torch.zeros(f0.member_hidden_dim + 1)
    changed_summary = initial_summary.clone()
    changed_summary[0] = 1.0
    support = torch.ones(N_SKILLS, dtype=torch.bool)

    reduction = deepcopy(f0.commitment_model)
    reduction.zero_summary_path()
    initial_logits, _ = reduction.logits(member, initial_summary, hidden)
    changed_logits, _ = reduction.logits(member, changed_summary, hidden)
    assert torch.max(
        torch.abs(
            centered_logits(initial_logits, support)
            - centered_logits(changed_logits, support)
        )
    ).item() <= 1.0e-6

    constructive = deepcopy(f1.commitment_model)
    with torch.no_grad():
        for parameter in constructive.parameters():
            parameter.zero_()
        constructive.decoder_hidden[0].weight[
            0, constructive.high_hidden_dim
        ] = 1.0
        constructive.skill_head.weight[0, 0] = 1.0
        constructive.skill_head.weight[1, 0] = -1.0
    f0_first, _ = constructive.logits(member, initial_summary, hidden)
    f0_second, _ = constructive.logits(member, initial_summary, hidden)
    f1_first, _ = constructive.logits(member, initial_summary, hidden)
    f1_second, _ = constructive.logits(member, changed_summary, hidden)
    assert torch.max(
        torch.abs(centered_logits(f0_first, support) - centered_logits(f0_second, support))
    ).item() <= 1.0e-6
    assert torch.max(
        torch.abs(centered_logits(f1_first, support) - centered_logits(f1_second, support))
    ).item() > 1.0e-6


def _replay_low_chunk(core, rows):
    device = core.device
    observations = torch.tensor(
        np.stack([row.observation for row in rows]),
        dtype=torch.float32,
        device=device,
    ).unsqueeze(1)
    skills = torch.tensor(
        [row.skill for row in rows], dtype=torch.long, device=device
    ).unsqueeze(1)
    actions = torch.tensor(
        np.stack([row.action for row in rows]), dtype=torch.long, device=device
    ).reshape(len(rows), 1)
    valid = torch.ones(len(rows), 1, device=device)
    reset = torch.ones(len(rows), 1, device=device)
    actor_logp, _ = core.low_actor.actor_replay(
        observations,
        skills,
        actions,
        torch.tensor(rows[0].actor_hidden_before, device=device).reshape(1, -1),
        valid,
        reset,
    )
    assert torch.max(
        torch.abs(
            actor_logp[:, 0]
            - torch.tensor(
                [row.old_log_probability for row in rows], device=device
            )
        )
    ).item() <= 1.0e-6

    critic_values, _ = core.low_critic.critic_replay(
        torch.tensor(
            np.stack([row.critic_member_features for row in rows]),
            dtype=torch.float32,
            device=device,
        ).unsqueeze(1),
        skills,
        torch.tensor(
            np.stack([row.critic_source_summary for row in rows]),
            dtype=torch.float32,
            device=device,
        ).unsqueeze(1),
        torch.tensor(rows[0].critic_hidden_before, device=device).reshape(1, -1),
        valid,
        reset,
    )
    assert torch.max(
        torch.abs(
            critic_values[:, 0]
            - torch.tensor([row.old_value for row in rows], device=device)
        )
    ).item() <= 1.0e-6


def test_ragged_low_replay_leave_rejoin_and_survivor_continuity():
    core, _ = run_trace()
    assert all(row.reward is not None for row in core.low_ledger)
    assert all(
        row.environment_step_pointer == row.physical_time for row in core.low_ledger
    )
    a_rows = [row for row in core.low_ledger if row.lifecycle_key == "a"]
    b_epoch0 = [
        row
        for row in core.low_ledger
        if row.lifecycle_key == "b" and row.membership_epoch == 0
    ]
    b_epoch1 = [
        row
        for row in core.low_ledger
        if row.lifecycle_key == "b" and row.membership_epoch == 1
    ]
    assert a_rows and b_epoch0 and b_epoch1
    _replay_low_chunk(core, a_rows)
    _replay_low_chunk(core, b_epoch0)
    _replay_low_chunk(core, b_epoch1)
    leave_boundary = next(
        row
        for row in core.low_chunk_boundaries
        if row["lifecycle_key"] == "b"
        and row["boundary_kind"] == TEMPORARY_BOUNDARY
    )
    assert np.array_equal(
        leave_boundary["actor_hidden"], b_epoch1[0].actor_hidden_before
    )
    assert np.array_equal(
        leave_boundary["critic_hidden"], b_epoch1[0].critic_hidden_before
    )
    assert b_epoch0[-1].terminal_or_truncation_kind == TEMPORARY_BOUNDARY
    assert b_epoch0[-1].bootstrap_source == "pre_membership_boundary_snapshot"
    assert b_epoch0[-1].bootstrap_value == pytest.approx(
        leave_boundary["bootstrap_value"]
    )
    assert np.isfinite(leave_boundary["bootstrap_value"])
    assert any(
        row.terminal_or_truncation_kind == ROLLOUT_TRUNCATION
        and row.bootstrap_source == "old_critic_policy_truncation"
        and row.bootstrap_value is not None
        and np.isfinite(row.bootstrap_value)
        for row in a_rows
    )
    assert max(row.lifecycle_chunk_pointer for row in a_rows) >= 1


def test_duration_credit_uses_physical_time_and_owner_local_trace_depth():
    core, _ = run_trace()
    initial_a = next(
        row
        for row in core.closed_event_rows
        if row.lifecycle_key == "a" and row.start_time == 0
    )
    assert initial_a.elapsed_physical_time == 1
    assert initial_a.discounted_reward == pytest.approx(1.0)
    assert initial_a.return_target == pytest.approx(
        1.0 + 0.9 * initial_a.bootstrap_value
    )
    temporary_b = next(
        row
        for row in core.closed_event_rows
        if row.lifecycle_key == "b" and row.boundary_kind == TEMPORARY_BOUNDARY
    )
    assert temporary_b.elapsed_physical_time == 1
    assert temporary_b.discounted_reward == pytest.approx(0.5)
    assert temporary_b.return_target == pytest.approx(
        0.5 + 0.9 * temporary_b.bootstrap_value
    )
    advantages = core.owner_gae()
    assert advantages.shape == (len(core.closed_event_rows),)
    assert np.all(np.isfinite(advantages))


def test_schema3_checkpoint_roundtrip_restores_runtime_collector_and_rngs(tmp_path):
    core, _ = run_trace()
    env = SnapshotEnv(value=17)
    collector = SyncEnvCollector([env])
    collector_snapshot = collector.snapshot_event_runtime()
    payload = core.checkpoint_payload(
        collector_snapshot=collector_snapshot,
        current_observation_state_boundary={"time": core.physical_time, "obs": [0.1]},
        optimizer_states={"high": {"steps": 0}, "low": {"steps": 0}},
        normalizer_states={"high": {"mean": 0.0}, "low": {"mean": 0.0}},
        pending_membership_transaction={"kind": "none"},
    )
    checkpoint_path = tmp_path / "event_schema3.pt"
    torch.save(payload, checkpoint_path)
    metadata = checkpoint_io.load_checkpoint_metadata(checkpoint_path)
    assert metadata["checkpoint_schema_version"] == 3
    assert metadata["high_controller"] == EVENT_CONTROLLER
    assert metadata["event_architecture_mode"] == "f1"
    restored_config = SimpleNamespace()
    checkpoint_io.apply_checkpoint_structure(
        restored_config,
        SimpleNamespace(high_controller="", event_architecture_mode=""),
        metadata,
    )
    assert restored_config.high_controller == EVENT_CONTROLLER
    assert restored_config.event_architecture_mode == "f1"

    restored = make_core("f1", model_seed=999, opportunity_seed=999)
    restored_env = SnapshotEnv(value=-1)
    restored_collector = SyncEnvCollector([restored_env])
    optimizers, normalizers = restored.restore_checkpoint_payload(
        payload, collector=restored_collector
    )
    assert optimizers == {"high": {"steps": 0}, "low": {"steps": 0}}
    assert normalizers == {"high": {"mean": 0.0}, "low": {"mean": 0.0}}
    assert restored.physical_time == core.physical_time
    assert restored.policy_version == core.policy_version
    assert restored.active_skills() == core.active_skills()
    assert restored_env.value == 17
    assert restored.current_observation_state_boundary == {
        "time": core.physical_time,
        "obs": [0.1],
    }
    assert restored.pending_membership_transaction == {"kind": "none"}
    for name, tensor in core.commitment_model.state_dict().items():
        assert torch.equal(tensor, restored.commitment_model.state_dict()[name])
    assert int(core.opportunity_rng.integers(1, 20)) == int(
        restored.opportunity_rng.integers(1, 20)
    )
    assert tuple(core.frontier_rng.permutation(["p", "q", "r"])) == tuple(
        restored.frontier_rng.permutation(["p", "q", "r"])
    )

    missing = deepcopy(payload)
    del missing["event_architecture"]["environment_rng_state"]
    with pytest.raises(ValueError, match="mandatory fields"):
        make_core("f1").restore_checkpoint_payload(
            missing, collector=SyncEnvCollector([SnapshotEnv()])
        )
    bad_optimizer = deepcopy(payload)
    del bad_optimizer["event_architecture"]["optimizer_states"]["low"]
    with pytest.raises(ValueError, match="optimizer state mismatch"):
        make_core("f1").restore_checkpoint_payload(
            bad_optimizer, collector=SyncEnvCollector([SnapshotEnv()])
        )
    wrong_mode = make_core("f0")
    with pytest.raises(ValueError, match="architecture mode mismatch"):
        wrong_mode.restore_checkpoint_payload(
            payload, collector=SyncEnvCollector([SnapshotEnv()])
        )


def test_event_dispatch_is_early_fail_closed_and_legacy_signature_is_unchanged(monkeypatch):
    config = SimpleNamespace(
        high_controller=EVENT_CONTROLLER,
        event_architecture_mode="f1",
        event_architecture_schema_version=EVENT_ARCHITECTURE_SCHEMA_VERSION,
        event_opportunity_schedule=OPPORTUNITY_SCHEDULE_NAME,
    )
    args = SimpleNamespace(num_envs=1)
    enforce_variable_roster_event_contract(config, args, None)

    def forbidden_collector(*_args, **_kwargs):
        raise AssertionError("collector construction must not occur")

    monkeypatch.setattr(
        standalone_train_runner, "create_collector", forbidden_collector
    )
    with pytest.raises(RuntimeError, match="deterministic transaction trace"):
        standalone_train_runner.train_loop(config, args, writer=None)

    torch.manual_seed(707)
    legacy_before = FixedClockAREditPolicy(
        obs_dim=3,
        n_agents=2,
        n_skills=3,
        hidden_dim=8,
        compact_dim=4,
        team_code_dim=4,
    )
    signature_before = {
        name: tuple(value.shape) for name, value in legacy_before.state_dict().items()
    }
    torch.manual_seed(707)
    legacy_after = FixedClockAREditPolicy(
        obs_dim=3,
        n_agents=2,
        n_skills=3,
        hidden_dim=8,
        compact_dim=4,
        team_code_dim=4,
    )
    assert signature_before == {
        name: tuple(value.shape) for name, value in legacy_after.state_dict().items()
    }


def _low_equivalence_groups(device="cpu"):
    scalar = [
        make_core(
            "f1",
            model_seed=811,
            action_seed=901,
            rng_episode_id=11,
            environment_index=0,
            device=device,
        ),
        make_core(
            "f1",
            model_seed=811,
            action_seed=902,
            rng_episode_id=12,
            environment_index=1,
            device=device,
        ),
    ]
    batched_owner = make_core(
        "f1",
        model_seed=811,
        action_seed=901,
        rng_episode_id=11,
        environment_index=0,
        device=device,
    )
    batched = [
        batched_owner,
        make_core(
            "f1",
            model_seed=999,
            action_seed=902,
            rng_episode_id=12,
            environment_index=1,
            shared_models_from=batched_owner,
            device=device,
        ),
    ]
    for group in (scalar, batched):
        initial_join(group[0], keys=("a",), actions={"a": 0})
        initial_join(
            group[1],
            keys=("a", "b", "c"),
            actions={"a": 0, "b": 1, "c": 2},
        )
    keys = (("a",), ("a", "b", "c"))
    return scalar, batched, keys


def _assert_low_row_equal(left, right):
    for item in fields(type(left)):
        lhs = getattr(left, item.name)
        rhs = getattr(right, item.name)
        if isinstance(lhs, np.ndarray):
            assert np.allclose(lhs, rhs, atol=1.0e-6, rtol=0.0), item.name
        elif isinstance(lhs, float):
            assert lhs == pytest.approx(rhs, abs=1.0e-6), item.name
        else:
            assert lhs == rhs, item.name


@pytest.mark.parametrize("device", ("cpu", "cuda"))
def test_cross_environment_ragged_low_batch_matches_scalar_deterministic(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA is unavailable")
    scalar, batched, keys = _low_equivalence_groups(device)
    scalar_results = [
        core.low_step(boundary(core, active), deterministic=True)
        for core, active in zip(scalar, keys)
    ]
    snapshots = [boundary(core, active) for core, active in zip(batched, keys)]
    batch_result = batched_low_step(batched, snapshots, deterministic=True)
    for core_index, (scalar_result, packed_result) in enumerate(
        zip(scalar_results, batch_result.per_core)
    ):
        assert torch.equal(scalar_result[0], packed_result[0])
        assert torch.allclose(
            scalar_result[1], packed_result[1], atol=1.0e-6, rtol=0.0
        )
        assert torch.allclose(
            scalar_result[2], packed_result[2], atol=1.0e-6, rtol=0.0
        )
        expected_routed = {
            key: int(scalar_result[0][index])
            for index, key in enumerate(keys[core_index])
        }
        assert batch_result.routed_actions[core_index] == expected_routed
        assert tuple(batch_result.routed_actions[core_index]) == keys[core_index]
        assert len(scalar[core_index].low_ledger) == len(
            batched[core_index].low_ledger
        )
        for left, right in zip(
            scalar[core_index].low_ledger, batched[core_index].low_ledger
        ):
            _assert_low_row_equal(left, right)
            assert np.allclose(
                scalar[core_index].records[left.lifecycle_key].low_actor_hidden,
                batched[core_index].records[right.lifecycle_key].low_actor_hidden,
                atol=1.0e-6,
                rtol=0.0,
            )
            assert np.allclose(
                scalar[core_index].records[left.lifecycle_key].low_critic_hidden,
                batched[core_index].records[right.lifecycle_key].low_critic_hidden,
                atol=1.0e-6,
                rtol=0.0,
            )


@pytest.mark.parametrize("device", ("cpu", "cuda"))
def test_cross_environment_stochastic_uniforms_preserve_rng_and_replay(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA is unavailable")
    scalar, batched, keys = _low_equivalence_groups(device)
    scalar_results = [
        core.low_step(boundary(core, active), deterministic=False)
        for core, active in zip(scalar, keys)
    ]
    snapshots = [boundary(core, active) for core, active in zip(batched, keys)]
    batch_result = batched_low_step(batched, snapshots, deterministic=False)
    for core_index, (scalar_result, packed_result) in enumerate(
        zip(scalar_results, batch_result.per_core)
    ):
        assert torch.equal(scalar_result[0], packed_result[0])
        assert torch.allclose(
            scalar_result[1], packed_result[1], atol=1.0e-6, rtol=0.0
        )
        assert np.array_equal(
            scalar[core_index].action_rng.random(8),
            batched[core_index].action_rng.random(8),
        )
        for left, right in zip(
            scalar[core_index].low_ledger, batched[core_index].low_ledger
        ):
            assert left.policy_action_uniform == right.policy_action_uniform
            _assert_low_row_equal(left, right)
        for row in batched[core_index].low_ledger:
            _replay_low_chunk(batched[core_index], [row])


def _make_closed_ppo_group(model_seed, device="cpu"):
    owner = make_core(
        "f1",
        model_seed=model_seed,
        action_seed=1001,
        rng_episode_id=21,
        device=device,
    )
    other = make_core(
        "f1",
        model_seed=model_seed + 1,
        action_seed=1002,
        rng_episode_id=22,
        environment_index=1,
        shared_models_from=owner,
        device=device,
    )
    cores = [owner, other]
    keys = (("a", "b"), ("a", "b", "c"))
    initial_join(owner, keys=keys[0], actions={"a": 0, "b": 1})
    initial_join(
        other,
        keys=keys[1],
        actions={"a": 0, "b": 1, "c": 2},
    )
    for step, reward in enumerate((0.0, 0.25, -0.1, 1.0, 0.5)):
        for core_index, (core, active) in enumerate(zip(cores, keys)):
            if core_index == 1 and step >= 2:
                continue
            core.low_step(boundary(core, active), deterministic=True)
            core.complete_primitive_transition(reward)
    for core in cores:
        core.close_terminal()
    return cores


def _event_optimizers(cores):
    owner = cores[0]
    high = torch.optim.Adam(
        tuple(owner.commitment_model.parameters())
        + tuple(owner.event_critic.parameters()),
        lr=3.0e-4,
    )
    low = torch.optim.Adam(
        tuple(owner.low_actor.parameters()) + tuple(owner.low_critic.parameters()),
        lr=3.0e-4,
    )
    return high, low


def _event_parameter_state(cores):
    owner = cores[0]
    return {
        f"{prefix}.{name}": tensor.detach().clone()
        for prefix, module in (
            ("commitment", owner.commitment_model),
            ("event_critic", owner.event_critic),
            ("low_actor", owner.low_actor),
            ("low_critic", owner.low_critic),
        )
        for name, tensor in module.state_dict().items()
    }


@pytest.mark.parametrize("device", ("cpu", "cuda"))
def test_one_time_packed_ppo_matches_reference_and_reuses_for_ppo4(device):
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA is unavailable")
    reference = _make_closed_ppo_group(1201, device)
    packed_cores = _make_closed_ppo_group(1201, device)
    reference_high, reference_low = _event_optimizers(reference)
    packed_high, packed_low = _event_optimizers(packed_cores)
    reference_initial = _event_parameter_state(reference)
    packed_initial = _event_parameter_state(packed_cores)
    assert all(
        torch.equal(reference_initial[name], packed_initial[name])
        for name in reference_initial
    )
    packed_data = pack_event_ppo_data(packed_cores)
    assert packed_data.low.observations.ndim == 3
    assert packed_data.low.observations.shape[1] > 1
    chunk_lengths = packed_data.low.valid_masks.sum(dim=0)
    assert torch.unique(chunk_lengths).numel() > 1
    reference_metrics = apply_event_ppo_update(
        reference,
        high_optimizer=reference_high,
        low_optimizer=reference_low,
    )
    packed_metrics = apply_event_ppo_update(
        packed_data,
        high_optimizer=packed_high,
        low_optimizer=packed_low,
    )
    for name in (
        "high_loss",
        "low_loss",
        "high_policy_loss",
        "high_value_loss",
        "low_policy_loss",
        "low_value_loss",
        "high_entropy",
        "low_entropy",
        "high_logp_max_error",
        "high_value_max_error",
        "low_logp_max_error",
        "low_value_max_error",
    ):
        assert packed_metrics[name] == pytest.approx(
            reference_metrics[name], abs=1.0e-6
        ), name
    assert max(
        packed_metrics[name]
        for name in (
            "high_logp_max_error",
            "high_value_max_error",
            "low_logp_max_error",
            "low_value_max_error",
        )
    ) <= 1.0e-6
    reference_final = _event_parameter_state(reference)
    packed_final = _event_parameter_state(packed_cores)
    for name in reference_initial:
        reference_delta = reference_final[name] - reference_initial[name]
        packed_delta = packed_final[name] - packed_initial[name]
        assert torch.allclose(
            reference_delta, packed_delta, atol=1.0e-6, rtol=0.0
        ), name

    for _pass in range(3):
        apply_event_ppo_update(
            packed_data,
            high_optimizer=packed_high,
            low_optimizer=packed_low,
        )
    for optimizer in (packed_high, packed_low):
        steps = {
            int(state["step"].item())
            for state in optimizer.state.values()
            if "step" in state
        }
        assert steps == {4}
