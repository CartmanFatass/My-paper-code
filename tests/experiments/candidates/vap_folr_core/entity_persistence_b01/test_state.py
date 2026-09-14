"""Counterexamples for the selected recurrent intervention, without native runs."""

import copy

import torch

from experiments.candidates.vap_folr_core.entity_history_augmentation_b01.model import (
    AugmentedActor,
)
from .test_integration import observations


def test_z_discards_incoming_and_temporal_entity_state_but_keeps_generic():
    batch = observations(3)
    batch["continuation"][:] = True
    batch["birth"][:] = False
    batch["visible"][:, 1, 0, 1] = False
    actor = AugmentedActor("AUGMENTED_CURRENT_ONLY")
    incoming = torch.randn(2, 5, 144, requires_grad=True)
    cell_inputs = []
    handle = actor.entity_rnn.register_forward_pre_hook(
        lambda _, args: cell_inputs.append(args[1])
    )
    q, state = actor(batch, incoming)
    handle.remove()
    assert len(cell_inputs) == 3 and not any(x.any() for x in cell_inputs)
    assert not state[:, 1, 0, 64:80].isnan().any()
    entity = state[..., 64:].reshape(2, 3, 5, 5, 16)
    assert not entity[:, 1, 0, 1].any()
    gradient = torch.autograd.grad(q.square().sum(), incoming)[0]
    assert gradient[..., :64].abs().sum() > 0
    assert not gradient[..., 64:].any()
    changed = incoming.detach().clone()
    changed[..., 64:] += 100
    q_changed, state_changed = actor(batch, changed)
    torch.testing.assert_close(q_changed, q)
    torch.testing.assert_close(state_changed, state)


def test_z_visible_tokens_are_current_only_and_chunks_match_without_hidden_leak():
    batch = observations(3)
    actor = AugmentedActor("AUGMENTED_CURRENT_ONLY")
    full_q, full_state = actor(batch)
    for step in range(3):
        one = {key: value[:, step:step + 1] for key, value in batch.items()}
        incoming = full_state[:, step - 1] if step else None
        q, state = actor(one, incoming)
        torch.testing.assert_close(q[:, 0], full_q[:, step])
        torch.testing.assert_close(state[:, 0], full_state[:, step])
        # The entity output is independent of any prior observation or state.
        _, zero_incoming = actor(one)
        torch.testing.assert_close(zero_incoming[..., 64:], state[..., 64:])

    unseen = {key: value[:, :1].clone() for key, value in batch.items()}
    unseen["visible"][:, :, 0, 1] = False
    unseen["seen"][:, :, 0, 1] = True
    base_q, base_state = actor(unseen)
    forbidden = copy.deepcopy(unseen)
    forbidden["entities"][:, :, 1] = float("nan")
    forbidden["previous_action"][:, :, 1] = float("nan")
    changed_q, changed_state = actor(forbidden)
    assert torch.isfinite(changed_q[:, :, 0]).all()
    torch.testing.assert_close(changed_q[:, :, 0], base_q[:, :, 0])
    torch.testing.assert_close(changed_state[:, :, 0], base_state[:, :, 0])


def test_persistent_default_retains_history_and_z_recurrent_weights_have_no_input():
    batch = observations(3)
    torch.manual_seed(935)
    default = AugmentedActor()
    torch.manual_seed(935)
    persistent = AugmentedActor("AUGMENTED_PERSISTENT")
    default_q, default_state = default(batch)
    explicit_q, explicit_state = persistent(batch)
    torch.testing.assert_close(default_q, explicit_q, rtol=0, atol=0)
    torch.testing.assert_close(default_state, explicit_state, rtol=0, atol=0)
    default_q.square().sum().backward()
    assert default.entity_rnn.weight_hh.grad.abs().sum() > 0

    torch.manual_seed(935)
    current = AugmentedActor("AUGMENTED_CURRENT_ONLY")
    z_q, _ = current(batch)
    torch.testing.assert_close(z_q[:, 0], default_q[:, 0], rtol=0, atol=0)
    z_q.square().sum().backward()
    assert current.entity_rnn.weight_hh.grad is not None
    assert not current.entity_rnn.weight_hh.grad.any()
    assert current.entity_rnn.weight_ih.grad.abs().sum() > 0
    assert current.rnn.weight_hh.grad.abs().sum() > 0
