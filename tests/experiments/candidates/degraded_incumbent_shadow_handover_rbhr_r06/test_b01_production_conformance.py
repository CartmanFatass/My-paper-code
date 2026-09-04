from __future__ import annotations

from io import BytesIO

import numpy as np
import pytest
import torch

from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_backend import (
    ProductionBackendError,
    b01_production_test_fixture,
    empty_step_rows,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_recurrent_trainer import (
    BatchedRecurrentPolicy,
    RecurrentRolloutState,
    _promotion,
)
from experiments.candidates.degraded_incumbent_shadow_handover_rbhr_r06.production_training_engine import (
    ExactPolicyGraph,
    WelfordState,
    _policy_log_prob,
    _role_policy_heads,
    deterministic_test_initialize,
)


class _Sampler:
    def normal(self, *, lane: int, tick: int, field: str) -> float:
        return 0.0

    def bernoulli(self, *, lane: int, tick: int, field: str, probability: float) -> int:
        return int(probability >= 0.5)


def _checkpoint(model: ExactPolicyGraph, *, nonempty_welford: bool = False) -> bytes:
    actor = WelfordState.empty(54)
    if nonempty_welford:
        actor.update(torch.stack((torch.zeros(54), torch.ones(54))))
    stream = BytesIO()
    torch.save({
        "model": model.state_dict(), "optimizer": {}, "update": 0,
        "welford": {
            "actor": actor, "snapshot": WelfordState.empty(18),
            "critic": WelfordState.empty(58),
        },
    }, stream)
    return stream.getvalue()


def test_live_fragment_replay_has_one_exact_fp32_behavior_law() -> None:
    torch.set_num_threads(1)
    model = ExactPolicyGraph(); deterministic_test_initialize(model)
    state = RecurrentRolloutState.fresh("STRUCTURED", width=2)
    initial = torch.linspace(-0.8, 0.8, 2 * 4 * 128).reshape(2, 4, 128)
    state.hidden = initial.clone()
    policy = BatchedRecurrentPolicy(
        arm="STRUCTURED", checkpoint_bytes=_checkpoint(model, nonempty_welford=True), state=state,
    )
    assert policy.state.actor_welford.count == 2
    actor_raw = torch.sin(
        torch.arange(2)[:, None, None, None] * 0.2
        + torch.arange(64)[None, :, None, None] * 0.01
        + torch.arange(4)[None, None, :, None] * 0.1
        + torch.arange(54)[None, None, None, :] * 0.003
    )
    owner = ((torch.arange(2)[:, None] + torch.arange(64)[None]) % 2).long()
    reset_mask = torch.ones((2, 64)); reset_mask[0, 17] = 0; reset_mask[1, 41] = 0
    snapshot = torch.cos(
        torch.arange(2)[:, None, None] * 0.3
        + torch.arange(64)[None, :, None] * 0.02
        + torch.arange(18)[None, None] * 0.01
    )
    snapshot_mask = torch.zeros((2, 64), dtype=torch.bool); snapshot_mask[:, (5, 33)] = True
    promotion_mask = torch.zeros((2, 64), dtype=torch.bool)
    promotion_mask[0, 20] = True; promotion_mask[1, 50] = True
    alpha = torch.ones((2, 64))
    renew = (torch.arange(64)[None] % 3 != 1).expand(2, -1).clone()
    live_states = []; live_rows = []; normalized = []; behavior = []
    post_promotion = None
    for tick in range(64):
        observation = {
            "actor": actor_raw[:, tick].numpy(), "owner": owner[:, tick].numpy(),
            "snapshot_delivery_mask": snapshot_mask[:, tick].numpy(),
            "snapshot_payload": snapshot[:, tick].numpy(),
            "renew": renew[:, tick].numpy(), "terminal": np.zeros(2, dtype=np.int32),
        }
        normalized.append(policy.normalized_actor(observation).clone())
        rows = policy.step_rows(
            observation, sampler=_Sampler(), global_tick=tick, deterministic=True,
            reset_lanes=(reset_mask[:, tick] == 0).numpy(),
        )
        live_states.append(policy.state.hidden.clone()); live_rows.append(rows.copy())
        behavior.append(policy.last_behavior_log_prob.clone())
        expected_promoted = _promotion(
            policy.state.hidden, promotion_mask[:, tick].numpy(), owner[:, tick].numpy(),
            np.ones(2, dtype=np.float32),
        )
        policy.apply_native_promotion(
            owner_before=owner[:, tick].numpy(), step_rows=rows,
            observation_after={"cas_applied": promotion_mask[:, tick].numpy()},
        )
        assert torch.equal(policy.state.hidden, expected_promoted)
        if tick == 20:
            post_promotion = policy.state.hidden.clone()
    normalized_actor = torch.stack(normalized, dim=1)
    replay_states, replay_heads = model.replay(
        normalized_actor, initial, snapshot, snapshot_mask, reset_mask, owner,
        promotion_mask, alpha, training_heads_only=True,
    )
    assert torch.equal(replay_states, torch.stack(live_states, dim=1))
    assert torch.equal(normalized_actor, policy.state.actor_welford.normalized(actor_raw))
    assert post_promotion is not None and not torch.equal(post_promotion, live_states[20])
    motion, prepare, commit = _role_policy_heads(replay_heads, owner)
    expected_action = 3.0 * torch.tanh(motion)
    for lane in range(2):
        for tick in range(64):
            if not renew[lane, tick]:
                u0 = 0 if owner[lane, tick] == 0 else 1
                u1 = 2 if owner[lane, tick] == 1 else 3
                expected_action[lane, tick] = actor_raw[
                    lane, tick, (u0, u0, u1, u1), (8, 9, 8, 9)
                ]
    actual_action = torch.from_numpy(
        np.stack(live_rows)["raw_action"].transpose(1, 0, 2)
    ).float()
    assert torch.equal(actual_action, expected_action)
    actual_prepare = torch.from_numpy(np.stack([
        rows["prepare"][np.arange(2), owner[:, tick].numpy()]
        for tick, rows in enumerate(live_rows)
    ], axis=1)).float()
    actual_commit = torch.from_numpy(np.stack([
        rows["commit"][np.arange(2), owner[:, tick].numpy()]
        for tick, rows in enumerate(live_rows)
    ], axis=1)).float()
    assert torch.equal(actual_prepare, ((prepare >= 0) & renew).float())
    assert torch.equal(actual_commit, ((commit >= 0) & renew).float())
    _, replay_log_prob = _policy_log_prob(
        "STRUCTURED", motion, model.log_std, actual_action, prepare, commit,
        actual_prepare, actual_commit, renew,
    )
    behavior_log_prob = torch.stack(behavior, dim=1)
    assert torch.equal(behavior_log_prob, replay_log_prob)
    assert torch.equal(
        torch.exp(replay_log_prob - behavior_log_prob), torch.ones_like(replay_log_prob)
    )


def test_native_prepared_clone_is_immutable_action_independent_and_one_shot() -> None:
    batch = b01_production_test_fixture(2)
    parent = batch.snapshot_bytes(); prepared = batch.prepare_b01_tick()
    prepared_bytes = prepared.snapshot_bytes()
    assert batch.snapshot_bytes() == parent
    assert prepared.origin_valid.tolist() == [True, True]
    current = prepared.observe()
    hidden = np.empty((2, 4, 128), dtype=np.float64)
    for copy, value in enumerate((0.1, 0.2, 0.3, 0.4)):
        hidden[:, copy] = value
    branches, observations, metadata = batch.clone_b01_prepared_batches(prepared, hidden)
    assert prepared.snapshot_bytes() == prepared_bytes and batch.snapshot_bytes() == parent
    assert all(name in metadata["branch_prepared"] for name in branches)
    assert all(
        int(observations[name]["tick"][0]) == int(current["tick"][0])
        for name in branches
    )
    assert all(
        np.all(
            observations[name]["protocol_wire_messages"]
            == current["protocol_wire_messages"] + 1
        ) for name in branches
    )
    assert all(
        np.all(observations[name]["protocol_bytes"] == current["protocol_bytes"] + 24)
        and np.allclose(observations[name]["total_energy"], current["total_energy"] + 0.48)
        and np.all(observations[name]["protocol_wire_hash"] != current["protocol_wire_hash"])
        for name in branches
    )
    copy_hidden = metadata["branch_hidden"]["TRANSFER_COPY"]
    shadow_hidden = metadata["branch_hidden"]["TRANSFER_SHADOW"]
    assert np.all(copy_hidden[0, 2] == 0.1) and np.all(shadow_hidden[0, 2] == 0.4)
    assert np.all(copy_hidden[1, 0] == 0.3) and np.all(shadow_hidden[1, 0] == 0.2)
    model = ExactPolicyGraph(); deterministic_test_initialize(model); checkpoint = _checkpoint(model)
    physics_energy = []; continuation_bytes = []; continuation_messages = []
    for name, branch in branches.items():
        branch_state = RecurrentRolloutState.fresh("STRUCTURED", width=2)
        branch_state.hidden = torch.from_numpy(
            metadata["branch_hidden"][name].astype(np.float32)
        )
        policy = BatchedRecurrentPolicy(
            arm="STRUCTURED", checkpoint_bytes=checkpoint, state=branch_state,
        )
        rows = policy.step_rows(
            observations[name], sampler=_Sampler(), global_tick=100,
            deterministic=True, recurrent_prepared=True,
        )
        after = branch.complete_b01_tick(metadata["branch_prepared"][name], rows)
        assert np.all(after["tick"] == observations[name]["tick"] + 1)
        physics_energy.append(after["total_energy"] - observations[name]["total_energy"])
        continuation_bytes.append(after["protocol_bytes"] - observations[name]["protocol_bytes"])
        continuation_messages.append(
            after["protocol_wire_messages"] - observations[name]["protocol_wire_messages"]
        )
        assert np.all(after["protocol_wire_hash"] != observations[name]["protocol_wire_hash"])
    assert all(np.allclose(value, physics_energy[0]) for value in physics_energy[1:])
    assert all(np.array_equal(value, continuation_bytes[0]) for value in continuation_bytes[1:])
    assert all(np.array_equal(value, continuation_messages[0]) for value in continuation_messages[1:])
    malformed = hidden.copy(); malformed[0, 0, 0] = 1.01
    with pytest.raises(ProductionBackendError, match="values differ"):
        batch.clone_b01_prepared_batches(prepared, malformed)
    invalid_batch = b01_production_test_fixture(1, origin_valid=False)
    invalid = invalid_batch.prepare_b01_tick()
    with pytest.raises(ProductionBackendError, match="rejected"):
        invalid_batch.clone_b01_prepared_batches(invalid, np.zeros((1, 4, 128)))
    low = b01_production_test_fixture(1); high = b01_production_test_fixture(1)
    low_prepared = low.prepare_b01_tick(); high_prepared = high.prepare_b01_tick()
    low_rows = empty_step_rows(1); high_rows = empty_step_rows(1)
    high_rows["raw_action"] = 1e6
    low_after = low.complete_b01_tick(low_prepared, low_rows)
    high_after = high.complete_b01_tick(high_prepared, high_rows)
    assert low_prepared.origin_valid.tolist() == high_prepared.origin_valid.tolist() == [True]
    assert low_after["cas_applied"].tolist() == high_after["cas_applied"].tolist() == [1]
    assert low_after["owner"].tolist() == high_after["owner"].tolist()
