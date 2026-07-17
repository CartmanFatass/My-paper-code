from copy import deepcopy
import pickle
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    OBSERVATION_DIM,
    DynamicRosterEventEnv,
)
from ha_ctse_process import train as process_train
from ha_ctse_process.variable_roster_event import (
    EVENT_ARCHITECTURE_SCHEMA_VERSION,
    OPPORTUNITY_SCHEDULE_NAME,
    TEMPORARY_BOUNDARY,
    TERMINAL_BOUNDARY,
    VariableRosterEventCore,
    event_ppo_losses,
)


def _make_core(
    mode: str,
    seed: int = 57_057,
    *,
    environment_index: int = 0,
    episode_id: int = 0,
    shared_models_from: VariableRosterEventCore | None = None,
) -> VariableRosterEventCore:
    torch.manual_seed(seed)
    return VariableRosterEventCore(
        architecture_mode=mode,
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=8,
        n_skills=3,
        action_dim=ACTION_COUNT,
        member_hidden_dim=16,
        high_hidden_dim=16,
        low_hidden_dim=16,
        skill_embedding_dim=8,
        environment_index=environment_index,
        opportunity_seed=77_057,
        frontier_seed=77_057,
        action_seed=87_057,
        rng_episode_id=episode_id,
        opportunity_stream_id=0,
        frontier_stream_id=1,
        action_stream_id=0,
        device="cpu",
        shared_models_from=shared_models_from,
    )


def test_stage_c_generic_short_event_integration_without_optimizer_step(monkeypatch):
    optimizer_steps = {"count": 0}
    original_adam_step = torch.optim.Adam.step

    def forbidden_adam_step(self, *args, **kwargs):
        optimizer_steps["count"] += 1
        raise AssertionError("the focused Stage-C check must not take optimizer.step")

    monkeypatch.setattr(torch.optim.Adam, "step", forbidden_adam_step)

    f0 = _make_core("f0")
    f1 = _make_core("f1")
    assert f0.model_signature() == f1.model_signature()
    assert f0.model_parameter_count() == f1.model_parameter_count()
    for module_name in f0.model_signature():
        left = getattr(f0, module_name).state_dict()
        right = getattr(f1, module_name).state_dict()
        assert left.keys() == right.keys()
        assert all(torch.equal(left[name], right[name]) for name in left)
    assert f0.architecture_mode == "f0" and f1.architecture_mode == "f1"
    assert "environment_index" not in f1.architecture_state()
    shared_env_core = _make_core(
        "f1", environment_index=7, shared_models_from=f1
    )
    assert shared_env_core.commitment_model is f1.commitment_model
    assert shared_env_core.environment_index == 7

    prefix_base = _make_core("f1", seed=71)
    with torch.no_grad():
        for parameter in prefix_base.commitment_model.parameters():
            parameter.zero_()
        prefix_base.commitment_model.skill_embedding.weight[:, 0] = torch.tensor(
            [-1.0, 0.5, 1.5]
        )
        prefix_base.commitment_model.member_encoder[0].weight.fill_(1.0)
        prefix_base.commitment_model.member_encoder[1].weight[
            0, OBSERVATION_DIM
        ] = 1.0
        prefix_base.commitment_model.member_encoder[3].weight[0, 0] = 1.0
        prefix_base.commitment_model.decoder_hidden[0].weight[
            0, prefix_base.high_hidden_dim
        ] = 1.0
        prefix_base.commitment_model.skill_head.weight[0, 0] = 1.0
        prefix_base.commitment_model.skill_head.weight[1, 0] = -1.0
    prefix_state = deepcopy(prefix_base.commitment_model.state_dict())

    def joined_prefix_read(mode: str, first_action: int):
        core = _make_core(mode, seed=73)
        core.commitment_model.load_state_dict(prefix_state, strict=True)
        local_env = DynamicRosterEventEnv(task_master_seed=67_057)
        local_transaction = local_env.reset_event_runtime(0)
        bound = core.bind_due_frontier(local_transaction)
        order = bound.post_membership_pre_policy_snapshot.keys
        teacher_actions = {key: 0 for key in order}
        teacher_actions[order[0]] = int(first_action)
        result = core.apply_transaction(
            bound,
            teacher_order=order,
            teacher_actions=teacher_actions,
        )
        later = result.token_rows[1]
        assert np.all(later.initial_skills == -1)
        assert later.pre_token_working_skills[0] == first_action
        assert bool(later.event_flags[0, 0])
        local_env.close()
        return later.old_token_log_probability

    f0_join_a = joined_prefix_read("f0", 0)
    f0_join_b = joined_prefix_read("f0", 2)
    f1_join_a = joined_prefix_read("f1", 0)
    f1_join_b = joined_prefix_read("f1", 2)
    assert abs(f0_join_a - f0_join_b) <= 1e-6
    assert abs(f1_join_a - f1_join_b) > 1e-6

    env = DynamicRosterEventEnv(task_master_seed=67_057)
    collector = SyncEnvCollector([env])
    transaction = collector.reset_event_runtime([0])[0]
    roster_sizes = []
    rewards = []
    membership_kinds = []
    snapshot_roundtrip_checked = False

    for primitive_time in range(HORIZON):
        membership_kinds.extend(
            delta.kind for delta in transaction.atomic_membership_delta
        )
        bound = f1.bind_due_frontier(transaction)
        result = f1.apply_transaction(bound)
        snapshot = bound.post_membership_pre_policy_snapshot
        roster_sizes.append(len(snapshot.keys))
        assert set(result.final_skills) == set(snapshot.keys)
        assert all(member.observation.shape == (OBSERVATION_DIM,) for member in snapshot.members)
        assert all(
            not np.shares_memory(member.observation, member.critic_member_features)
            for member in snapshot.members
        )
        actions, _logp, _values = f1.low_step(snapshot, deterministic=True)
        step = collector.step_event_runtime(
            [
                {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(snapshot.keys)
                }
            ]
        )[0]
        assert step.info["intrinsic_reward"] == 0.0
        assert step.info["intrinsic_reward_applied_count"] == 0
        rewards.append(step.reward)
        f1.complete_primitive_transition(step.reward)
        if step.terminated:
            assert primitive_time == HORIZON - 1
            assert step.next_transaction is None
            f1.close_terminal()
        else:
            assert step.next_transaction is not None
            transaction = step.next_transaction

        if primitive_time == 40:
            collector_snapshot = collector.snapshot_event_runtime()
            checkpoint = f1.checkpoint_payload(
                collector_snapshot=collector_snapshot,
                current_observation_state_boundary={"physical_time": f1.physical_time},
                pending_membership_transaction=deepcopy(transaction),
                optimizer_states={"high": {"steps": 0}, "low": {"steps": 0}},
                normalizer_states={"high": {}, "low": {}},
            )
            restored_pairs = []
            for restored_seed in (999, 1001):
                restored_env = DynamicRosterEventEnv()
                restored_collector = SyncEnvCollector([restored_env])
                restored = _make_core("f1", seed=restored_seed)
                restored.restore_checkpoint_payload(
                    checkpoint, collector=restored_collector
                )
                assert restored.physical_time == f1.physical_time
                assert restored.active_skills() == f1.active_skills()
                assert pickle.dumps(
                    restored_collector.snapshot_event_runtime()
                ) == pickle.dumps(collector_snapshot)
                restored_pairs.append((restored, restored_collector))

            continuation_results = []
            continuation_low_actions = []
            for restored, _restored_collector in restored_pairs:
                for record in restored.records.values():
                    if record.status == "ACTIVE":
                        record.active_gap_remaining = 0
                continuation_bound = restored.bind_due_frontier(deepcopy(transaction))
                continuation_result = restored.apply_transaction(continuation_bound)
                continuation_actions, _continuation_logp, _continuation_values = (
                    restored.low_step(
                        continuation_bound.post_membership_pre_policy_snapshot,
                        deterministic=False,
                    )
                )
                continuation_results.append(continuation_result)
                continuation_low_actions.append(continuation_actions)
            assert continuation_results[0].sampled_order == continuation_results[1].sampled_order
            assert [row.combined_action for row in continuation_results[0].token_rows] == [
                row.combined_action for row in continuation_results[1].token_rows
            ]
            assert [row.sampled_replacement_gap for row in continuation_results[0].token_rows] == [
                row.sampled_replacement_gap for row in continuation_results[1].token_rows
            ]
            assert [row.policy_action_uniform for row in continuation_results[0].token_rows] == [
                row.policy_action_uniform for row in continuation_results[1].token_rows
            ]
            assert torch.equal(continuation_low_actions[0], continuation_low_actions[1])
            assert [
                row.policy_action_uniform for row in restored_pairs[0][0].low_ledger[-6:]
            ] == [
                row.policy_action_uniform for row in restored_pairs[1][0].low_ledger[-6:]
            ]
            for restored, restored_collector in restored_pairs:
                assert restored.action_rng.bit_generator.state["bit_generator"] == "PCG64"
                restored_collector.close()
            malformed = deepcopy(checkpoint)
            del malformed["event_architecture"]["environment_rng_state"]
            with pytest.raises(ValueError, match="mandatory fields"):
                _make_core("f1").restore_checkpoint_payload(
                    malformed,
                    collector=SyncEnvCollector([DynamicRosterEventEnv()]),
                )
            with pytest.raises(ValueError, match="runtime environment index mismatch"):
                _make_core("f1", environment_index=1).restore_checkpoint_payload(
                    checkpoint,
                    collector=SyncEnvCollector([DynamicRosterEventEnv()]),
                )
            snapshot_roundtrip_checked = True

    assert snapshot_roundtrip_checked
    assert roster_sizes == [4] * 20 + [2] * 20 + [6] * 20 + [4] * 20
    assert membership_kinds.count("JOIN") == 6
    assert membership_kinds.count("TEMPORARY_LEAVE") == 2
    assert membership_kinds.count("REJOIN") == 2
    assert membership_kinds.count("TERMINAL_LEAVE") == 2
    assert rewards[:-1] == [0.0] * (HORIZON - 1)
    assert rewards[-1] >= 0.0
    assert all(row.reward is not None for row in f1.low_ledger)
    assert any(row.boundary_kind == TEMPORARY_BOUNDARY for row in f1.closed_event_rows)
    assert any(row.boundary_kind == TERMINAL_BOUNDARY for row in f1.closed_event_rows)
    assert all(len(chunk) <= 20 for chunk in f1.low_recurrent_chunks())
    assert np.isfinite(f1.owner_gae()).all()
    low_advantages, low_returns = f1.low_gae()
    assert np.isfinite(low_advantages).all() and np.isfinite(low_returns).all()

    replay_errors = []
    replay_value_errors = []
    for row in f1.high_ledger:
        replay_logp, replay_value, _entropy = f1.replay_event_token(row)
        replay_errors.append(
            abs(float(replay_logp.detach()) - row.old_token_log_probability)
        )
        replay_value_errors.append(abs(float(replay_value.detach()) - row.old_owner_value))
    assert replay_errors and max(replay_errors) <= 1e-6
    assert max(replay_value_errors) <= 1e-6

    low_logp_errors = []
    low_value_errors = []
    for chunk in f1.low_recurrent_chunks():
        rows = [f1.low_ledger[index] for index in chunk]
        observations = torch.as_tensor(
            np.stack([row.observation for row in rows])[:, None, :]
        )
        skills = torch.as_tensor([[row.skill] for row in rows])
        actions = torch.as_tensor(
            np.stack([row.action for row in rows])[:, None, ...]
        ).reshape(len(rows), 1)
        valid = torch.ones(len(rows), 1)
        replay_logp, _hidden = f1.low_actor.actor_replay(
            observations,
            skills,
            actions,
            torch.as_tensor(rows[0].actor_hidden_before).reshape(1, -1),
            valid,
            valid,
        )
        max_active = max(len(row.active_skills) for row in rows)
        raw_members = np.zeros(
            (len(rows), 1, max_active, OBSERVATION_DIM), dtype=np.float32
        )
        raw_skills = np.zeros((len(rows), 1, max_active), dtype=np.int64)
        raw_masks = np.zeros((len(rows), 1, max_active), dtype=np.bool_)
        focal_indices = np.zeros((len(rows), 1), dtype=np.int64)
        raw_globals = np.zeros((len(rows), 1, 8), dtype=np.float32)
        for position, row in enumerate(rows):
            active_count = len(row.active_skills)
            raw_members[position, 0, :active_count] = row.active_critic_member_features
            raw_skills[position, 0, :active_count] = row.active_skills
            raw_masks[position, 0, :active_count] = True
            focal_indices[position, 0] = row.focal_active_index
            raw_globals[position, 0] = row.critic_global_features
        replay_values, _critic_hidden, replay_sources = (
            f1.low_critic.critic_replay_from_active_sets(
                torch.as_tensor(raw_members),
                torch.as_tensor(raw_skills),
                torch.as_tensor(raw_masks),
                torch.as_tensor(focal_indices),
                torch.as_tensor(raw_globals),
                torch.as_tensor(rows[0].critic_hidden_before).reshape(1, -1),
                valid,
                valid,
            )
        )
        low_logp_errors.extend(
            abs(float(replay_logp[position, 0].detach()) - row.old_log_probability)
            for position, row in enumerate(rows)
        )
        low_value_errors.extend(
            abs(float(replay_values[position, 0].detach()) - row.old_value)
            for position, row in enumerate(rows)
        )
        assert np.max(
            np.abs(
                replay_sources[:, 0].detach().numpy()
                - np.stack([row.critic_source_summary for row in rows])
            )
        ) <= 1e-6
    assert max(low_logp_errors) <= 1e-6
    assert max(low_value_errors) <= 1e-6

    influence_row = next(row for row in f1.low_ledger if len(row.active_skills) > 1)
    influence_members = torch.as_tensor(
        influence_row.active_critic_member_features[None, None, :, :]
    ).clone().requires_grad_(True)
    influence_skills = torch.as_tensor(influence_row.active_skills[None, None, :])
    influence_masks = torch.ones_like(influence_skills, dtype=torch.bool)
    influence_value, _hidden, _source = f1.low_critic.critic_replay_from_active_sets(
        influence_members,
        influence_skills,
        influence_masks,
        torch.as_tensor([[influence_row.focal_active_index]]),
        torch.as_tensor(influence_row.critic_global_features[None, None, :]),
        torch.as_tensor(influence_row.critic_hidden_before).reshape(1, -1),
        torch.ones(1, 1),
        torch.ones(1, 1),
    )
    influence_gradient = torch.autograd.grad(
        influence_value.sum(), influence_members
    )[0]
    non_focal = [
        index
        for index in range(len(influence_row.active_skills))
        if index != influence_row.focal_active_index
    ]
    assert influence_gradient[0, 0, non_focal].abs().sum().item() > 0.0
    losses = event_ppo_losses([f1])
    assert losses.high_rows > 0 and losses.low_rows == len(f1.low_ledger)
    assert losses.high_loss.requires_grad and losses.low_loss.requires_grad
    assert all(
        torch.isfinite(value).item()
        for value in (losses.high_loss, losses.low_loss)
    )

    dispatch_config = SimpleNamespace(
        high_controller="variable_roster_event",
        event_architecture_mode="f1",
        event_architecture_schema_version=EVENT_ARCHITECTURE_SCHEMA_VERSION,
        event_opportunity_schedule=OPPORTUNITY_SCHEDULE_NAME,
        scenario="generic_short_dynamic_roster",
    )
    dispatch_args = SimpleNamespace(rollout_length=80, resume_from="")
    sentinel = object()
    branch_calls = []
    monkeypatch.setattr(
        process_train,
        "_run_variable_roster_event_branch",
        lambda config, args, writer: branch_calls.append(args) or sentinel,
    )
    assert process_train.train_loop(dispatch_config, dispatch_args, None) is sentinel
    assert len(branch_calls) == 1
    with pytest.raises(ValueError, match="--resume_from fails closed"):
        process_train.train_loop(
            dispatch_config,
            SimpleNamespace(rollout_length=80, resume_from="checkpoint.pt"),
            None,
        )
    assert len(branch_calls) == 1
    assert optimizer_steps["count"] == 0
    monkeypatch.setattr(torch.optim.Adam, "step", original_adam_step)
    collector.close()
