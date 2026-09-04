from __future__ import annotations

import struct

import numpy as np
import pytest

from experiments.candidates.finite_resource_relational_inductive_efficiency.arms import (
    LAYER_SHAPES,
    PARAMETER_BYTE_COUNT,
    architecture_parameter_count,
    initialize_paired_arms,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.contracts.core import (
    ContractError,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.policy import (
    ACTION_NAMES,
    LEGAL_ACTION_INDICES,
    ROLE_NAMES,
    TORCH_AVAILABLE,
    FRRIEActorCritic,
    TorchUnavailableError,
    expected_parameter_names,
    legal_action_mask_array,
    make_actor_critic,
    semantic_column_permutation,
)
from experiments.candidates.finite_resource_relational_inductive_efficiency.rng import AddressedRNG
from experiments.candidates.finite_resource_relational_inductive_efficiency.state_codec import (
    OPTIMIZER_PAYLOAD_BYTE_COUNT,
    OPTIMIZER_STATE_BYTE_COUNT,
    OPTIMIZER_STATE_MAGIC,
    OPTIMIZER_STATE_VERSION,
    decode_optimizer_state,
    encode_optimizer_state,
    load_actor_and_optimizer_state,
    optimizer_state_layout,
)


def _arms():
    return initialize_paired_arms(AddressedRNG(b"T" * 32), "FRRIE-TEST-ONLY-POLICY")


def test_non_torch_structural_inventory_masks_and_rotation() -> None:
    assert architecture_parameter_count() == 35_513
    assert expected_parameter_names() == tuple(name for name, _ in LAYER_SHAPES)
    assert optimizer_state_layout() == LAYER_SHAPES
    assert ROLE_NAMES == ("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")
    assert ACTION_NAMES == (
        "SCAN", "UPLINK", "LISTEN_WEST", "LISTEN_EAST", "FORWARD_BASE", "HOLD"
    )
    assert LEGAL_ACTION_INDICES == ((0, 1, 5), (0, 1, 5), (2, 3, 4, 5))
    assert legal_action_mask_array().sum(axis=1).tolist() == [3, 3, 4]
    assert semantic_column_permutation(False) == (0, 1, 2)
    assert semantic_column_permutation(True) == (2, 0, 1)


def test_optimizer_codec_direct_version_length_and_order_without_torch() -> None:
    first = np.arange(35_513, dtype="<f4")
    second = -first
    payload = first.tobytes() + second.tobytes() + struct.pack("<Q", 17)
    assert len(payload) == OPTIMIZER_PAYLOAD_BYTE_COUNT
    blob = struct.pack(
        "<8sII", OPTIMIZER_STATE_MAGIC, OPTIMIZER_STATE_VERSION, len(payload)
    ) + payload
    assert len(blob) == OPTIMIZER_STATE_BYTE_COUNT
    decoded = decode_optimizer_state(blob)
    assert decoded.step == 17
    cursor = 0
    for name, shape in LAYER_SHAPES:
        size = int(np.prod(shape))
        np.testing.assert_array_equal(
            decoded.first_moment[name].reshape(-1), first[cursor:cursor + size]
        )
        np.testing.assert_array_equal(
            decoded.second_moment[name].reshape(-1), second[cursor:cursor + size]
        )
        assert decoded.first_moment[name].dtype == np.dtype("<f4")
        cursor += size
    with pytest.raises(ContractError, match="exactly"):
        decode_optimizer_state(blob[:-1])
    bad_version = bytearray(blob)
    bad_version[8:12] = struct.pack("<I", 2)
    with pytest.raises(ContractError, match="version"):
        decode_optimizer_state(bytes(bad_version))
    bad_length = bytearray(blob)
    bad_length[12:16] = struct.pack("<I", len(payload) - 1)
    with pytest.raises(ContractError, match="length"):
        decode_optimizer_state(bytes(bad_length))


def test_torch_absence_fails_closed_without_policy_fallback() -> None:
    if TORCH_AVAILABLE:
        pytest.skip("Torch production path is installed")
    with pytest.raises(TorchUnavailableError, match="no Python policy fallback"):
        make_actor_critic(_arms()[0])


pytestmark_torch = pytest.mark.skipif(not TORCH_AVAILABLE, reason="Torch is optional")


@pytestmark_torch
def test_torch_architecture_count_mapping_and_actor_legal_floor() -> None:
    import torch

    arm = _arms()[0]
    model = FRRIEActorCritic(arm)
    assert tuple((name, tuple(value.shape)) for name, value in model.named_parameters()) == LAYER_SHAPES
    assert sum(value.numel() for value in model.parameters()) == 35_513
    assert model.parameter_bytes() == arm.parameter_bytes()
    observations = torch.zeros((3, 22), dtype=torch.float32)
    roles = torch.tensor((0, 1, 2), dtype=torch.int64)
    result = model.actor_step(observations, roles, model.initial_hidden(3))
    assert result.messages.shape == (3, 32)
    assert result.summary.shape == (3, 32)
    assert result.hidden.shape == (3, 64)
    assert result.logits.shape == (3, 6)
    assert result.probabilities.shape == (3, 6)
    masks = torch.from_numpy(legal_action_mask_array()).index_select(0, roles)
    assert torch.equal(result.probabilities.masked_select(~masks), torch.zeros(8))
    for role, count in enumerate((3, 3, 4)):
        assert bool((result.probabilities[role, masks[role]] >= 0.04 / count - 2e-7).all())
    torch.testing.assert_close(result.probabilities.sum(1), torch.ones(3))
    actions = model.actions_from_uniforms(
        result.probabilities, torch.tensor((0.0, 0.5, 0.999), dtype=torch.float32)
    )
    assert actions.dtype == torch.int64
    assert bool(masks.gather(1, actions[:, None]).all())

    actor_input = torch.linspace(-0.4, 0.4, 3 * 55, dtype=torch.float32).reshape(3, 55)
    incoming = torch.linspace(-0.3, 0.2, 3 * 64, dtype=torch.float32).reshape(3, 64)
    input_zrn = torch.nn.functional.linear(
        actor_input, model.gru.weight_input_zrn, model.gru.bias_zrn
    )
    wz, wr, wn = input_zrn.chunk(3, dim=1)
    uz, ur, un = model.gru.weight_hidden_zrn.chunk(3, dim=0)
    z = torch.sigmoid(wz + torch.nn.functional.linear(incoming, uz))
    reset = torch.sigmoid(wr + torch.nn.functional.linear(incoming, ur))
    candidate = torch.tanh(wn + torch.nn.functional.linear(reset * incoming, un))
    expected_hidden = (1.0 - z) * candidate + z * incoming
    torch.testing.assert_close(model.gru(actor_input, incoming), expected_hidden)


@pytestmark_torch
def test_semantic_rotation_changes_only_policy_summary_and_shadow_does_not_propagate() -> None:
    import torch

    model = FRRIEActorCritic(_arms()[1])
    observations = torch.linspace(-0.8, 0.9, 6 * 22, dtype=torch.float32).reshape(6, 22)
    roles = torch.tensor((0, 1, 2, 0, 1, 2), dtype=torch.int64)
    incoming = torch.linspace(-0.2, 0.3, 6 * 64, dtype=torch.float32).reshape(6, 64)
    obs_before = observations.clone()
    hidden_before = incoming.clone()
    parameters_before = model.parameter_bytes()
    intact = model.actor_step(observations, roles, incoming)
    shadow = model.shadow_step(observations, roles, incoming)
    torch.testing.assert_close(intact.messages, shadow.messages, rtol=0.0, atol=0.0)
    assert not torch.equal(intact.summary, shadow.summary)
    assert not torch.equal(intact.denominator, shadow.denominator)
    torch.testing.assert_close(observations, obs_before, rtol=0.0, atol=0.0)
    torch.testing.assert_close(incoming, hidden_before, rtol=0.0, atol=0.0)
    assert model.parameter_bytes() == parameters_before


def _loss_episode(torch, roster_size: int, selected, all_probabilities, critic_values):
    from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
        RSCFEpisode,
    )
    legal = torch.tensor(
        ((1, 1, 0, 0, 0, 1), (1, 1, 0, 0, 0, 1), (0, 0, 1, 1, 1, 1)),
        dtype=torch.bool,
    )
    return RSCFEpisode(
        roster_size=roster_size,
        selected_probabilities=selected,
        q_targets=torch.zeros((3, 6), dtype=torch.float32),
        legal_masks=legal,
        factual_actions=torch.tensor((0, 1, 2), dtype=torch.int64),
        all_probabilities=all_probabilities,
        critic_values=critic_values,
        terminal_return=torch.tensor(0.5, dtype=torch.float32),
    )


def _model_update_episodes(torch, model):
    by_roster = {}
    for roster_size in (9, 15):
        roles = torch.arange(roster_size, dtype=torch.int64) % 3
        observations = torch.linspace(
            -0.5, 0.5, roster_size * 22, dtype=torch.float32
        ).reshape(roster_size, 22)
        output = model.actor_step(observations, roles, model.initial_hidden(roster_size))
        selected = output.probabilities.index_select(
            0, torch.tensor((0, 1, 2), dtype=torch.int64)
        )
        all_probabilities = output.probabilities.unsqueeze(0).expand(12, -1, -1)
        critic_values = model.critic_values(
            observations.unsqueeze(0).expand(12, -1, -1), roles
        )
        by_roster[roster_size] = (selected, all_probabilities, critic_values)
    episodes = []
    for _ in range(32):
        for roster_size in (9, 15):
            episodes.append(_loss_episode(torch, roster_size, *by_roster[roster_size]))
    return episodes

@pytestmark_torch
def test_stopped_policy_weighted_target_and_equal_role_score_gradients() -> None:
    import torch
    from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
        RSCFEpisode, rscf_episode_loss,
    )

    logits = torch.zeros((3, 6), dtype=torch.float32, requires_grad=True)
    legal = torch.tensor(
        ((1, 1, 0, 0, 0, 1), (1, 1, 0, 0, 0, 1), (0, 0, 1, 1, 1, 1)),
        dtype=torch.bool,
    )
    soft = torch.softmax(logits.masked_fill(~legal, -torch.inf), dim=1)
    selected = 0.96 * soft + legal * (0.04 / legal.sum(1, keepdim=True))
    all_logits = torch.zeros((12, 9, 6), dtype=torch.float32, requires_grad=True)
    all_probabilities = torch.softmax(all_logits, dim=2)
    critic_values = torch.zeros(12, dtype=torch.float32, requires_grad=True)
    q_targets = torch.arange(18, dtype=torch.float32).reshape(3, 6)
    episode = RSCFEpisode(
        9, selected, q_targets, legal, torch.tensor((0, 1, 2)),
        all_probabilities, critic_values, torch.tensor(0.75, dtype=torch.float32),
    )
    terms = rscf_episode_loss(episode)
    expected = (selected.detach() * torch.where(legal, q_targets, 0.0)).sum(1)
    torch.testing.assert_close(terms.baselines, expected)
    assert not terms.baselines.requires_grad
    assert not terms.advantages.requires_grad
    terms.loss.backward()
    assert logits.grad is not None
    assert all_logits.grad is not None
    assert critic_values.grad is not None
    assert q_targets.grad is None


@pytestmark_torch
def test_equal_episode_weighting_exact_32_32_and_single_step_projection_codec_roundtrip() -> None:
    import torch
    from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
        RSCFTrainer, make_optimizer, rscf_batch_loss,
    )

    arm = _arms()[0]
    model = FRRIEActorCritic(arm)
    with torch.no_grad():
        model.beta.fill_(2.0)
    episodes = _model_update_episodes(torch, model)
    batch = rscf_batch_loss(episodes)
    first_half = sum(
        __import__(
            "experiments.candidates.finite_resource_relational_inductive_efficiency.training",
            fromlist=["rscf_episode_loss"],
        ).rscf_episode_loss(episode).loss
        for episode in episodes[0::2]
    ) / 32.0
    second_half = sum(
        __import__(
            "experiments.candidates.finite_resource_relational_inductive_efficiency.training",
            fromlist=["rscf_episode_loss"],
        ).rscf_episode_loss(episode).loss
        for episode in episodes[1::2]
    ) / 32.0
    torch.testing.assert_close(batch.loss, 0.5 * (first_half + second_half))

    optimizer = make_optimizer(model)
    receipt = RSCFTrainer(model, optimizer).update(episodes)
    assert receipt.backward_calls == 1
    assert receipt.optimizer_steps == 1
    assert receipt.roster_counts == {9: 32, 15: 32}
    assert receipt.projection_after_step
    assert float(model.beta.max()) <= float(np.float32(0.15))
    beta_moment = optimizer.state[model.beta]["exp_avg"].clone()
    assert bool((beta_moment != 0).any())

    parameter_bytes = model.parameter_bytes()
    optimizer_bytes = encode_optimizer_state(model, optimizer)
    decoded = decode_optimizer_state(optimizer_bytes)
    assert decoded.step == 1
    np.testing.assert_array_equal(decoded.first_moment["beta"], beta_moment.numpy())

    restored = FRRIEActorCritic(_arms()[0])
    restored_optimizer = make_optimizer(restored)
    step = load_actor_and_optimizer_state(
        restored, restored_optimizer, parameter_bytes, optimizer_bytes, expected_update=1
    )
    assert step == 1
    assert restored.parameter_bytes() == parameter_bytes
    assert encode_optimizer_state(restored, restored_optimizer) == optimizer_bytes
    assert len(parameter_bytes) == PARAMETER_BYTE_COUNT

    # The exact loaded FP32 CPU Adam state must make the next full update
    # bit-identical to an uninterrupted update.
    RSCFTrainer(model, optimizer).update(_model_update_episodes(torch, model))
    RSCFTrainer(restored, restored_optimizer).update(
        _model_update_episodes(torch, restored)
    )
    assert restored.parameter_bytes() == model.parameter_bytes()
    assert encode_optimizer_state(restored, restored_optimizer) == encode_optimizer_state(
        model, optimizer
    )


@pytestmark_torch
def test_optimizer_flags_and_resume_step_mismatch_fail_closed() -> None:
    import torch
    from experiments.candidates.finite_resource_relational_inductive_efficiency.training import (
        RSCFTrainer, make_optimizer, validate_update_batch,
    )

    model = FRRIEActorCritic(_arms()[0])
    optimizer = make_optimizer(model)
    optimizer.param_groups[0]["maximize"] = True
    with pytest.raises(ContractError, match="hyperparameters"):
        RSCFTrainer(model, optimizer)

    episodes = _model_update_episodes(torch, model)
    episodes[0], episodes[1] = episodes[1], episodes[0]
    with pytest.raises(ContractError, match="64-position"):
        validate_update_batch(episodes)

    good_optimizer = make_optimizer(model)
    blob = encode_optimizer_state(model, good_optimizer)
    restored = FRRIEActorCritic(_arms()[0])
    with pytest.raises(ContractError, match="expected"):
        load_actor_and_optimizer_state(
            restored, make_optimizer(restored), model.parameter_bytes(), blob,
            expected_update=1,
        )
