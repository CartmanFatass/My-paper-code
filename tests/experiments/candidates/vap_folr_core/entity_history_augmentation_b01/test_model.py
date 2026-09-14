import copy

import pytest
import torch

from experiments.candidates.vap_folr_core.entity_history_augmentation_b01 import (
    AugmentedActor,
)
from experiments.candidates.vap_folr_core.entity_history_b01.model import Actor


@pytest.fixture(scope="module", autouse=True)
def one_thread():
    torch.set_num_threads(1)


def observations(t=4):
    torch.manual_seed(713)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(2, t, 1, 1)
    visible[:, :, 0, 1] = True
    continuation = torch.ones(2, t, 5, dtype=torch.bool)
    continuation[:, 0] = False
    seen = torch.zeros_like(visible)
    age = torch.zeros_like(visible, dtype=torch.int16)
    for step in range(t):
        previous = seen[:, step - 1] if step else torch.zeros_like(seen[:, 0])
        seen[:, step] = previous | visible[:, step]
        if step:
            age[:, step] = torch.where(previous, age[:, step - 1] + 1, 0)
        age[:, step].masked_fill_(visible[:, step], 0)
    return dict(
        entities=torch.rand(2, t, 5, 4),
        previous_action=torch.zeros(2, t, 5, 5),
        entity_mask=torch.zeros(2, t, 5, dtype=torch.bool),
        visible=visible,
        obs_mask=~visible,
        seen=seen,
        age=age,
        birth=~continuation,
        continuation=continuation,
        departure=torch.zeros_like(continuation),
        event=torch.zeros(2, t, dtype=torch.bool),
    )


def test_generic_initialization_hidden_path_and_downstream_rng_match_reference():
    batch = observations()
    torch.manual_seed(914)
    reference = Actor("GENERIC_RETAIN")
    reference_rng = torch.random.get_rng_state()
    torch.manual_seed(914)
    augmented = AugmentedActor()
    assert torch.equal(reference_rng, torch.random.get_rng_state())
    for name in ("fc1", "attn", "fc2", "rnn"):
        expected = getattr(reference, name).state_dict()
        actual = getattr(augmented, name).state_dict()
        for key in expected:
            torch.testing.assert_close(actual[key], expected[key], rtol=0, atol=0)
    assert "fc3.weight" not in augmented.state_dict()

    generic_hidden = torch.randn(2, 5, 64)
    packed = torch.cat((generic_hidden, torch.zeros(2, 5, 80)), -1)
    _, reference_states = reference(batch, generic_hidden)
    _, augmented_states = augmented(batch, packed)
    torch.testing.assert_close(augmented_states[..., :64], reference_states)


def test_pair_lifetimes_unseen_carry_and_inactive_zeros():
    batch = observations(1)
    batch["continuation"][:] = True
    batch["continuation"][:, 0, 2] = False
    batch["visible"][:] = torch.eye(5, dtype=torch.bool)
    batch["seen"][:] = True
    batch["entity_mask"][:, :, 4] = True
    incoming = torch.randn(2, 5, 144)
    generic_inputs, entity_inputs = [], []
    actor = AugmentedActor()
    generic_hook = actor.rnn.register_forward_pre_hook(
        lambda _, args: generic_inputs.append(args[1].detach().reshape(2, 5, 64))
    )
    entity_hook = actor.entity_rnn.register_forward_pre_hook(
        lambda _, args: entity_inputs.append(args[1].detach().reshape(2, 5, 5, 16))
    )
    q, states = actor(batch, incoming)
    generic_hook.remove()
    entity_hook.remove()

    torch.testing.assert_close(generic_inputs[0][:, 0], incoming[:, 0, :64])
    assert not generic_inputs[0][:, 2].any()
    incoming_entities = incoming[..., 64:].reshape(2, 5, 5, 16)
    torch.testing.assert_close(entity_inputs[0][:, 0, 1], incoming_entities[:, 0, 1])
    assert not entity_inputs[0][:, :, 2].any()
    assert not entity_inputs[0][:, 2].any()
    assert not states[:, :, 4].any() and not q[:, :, 4].any()
    packed_entities = states[..., 64:].reshape(2, 1, 5, 5, 16)
    assert not packed_entities[:, :, :, 4].any()


def test_visible_unseen_reappearance_and_forbidden_current_isolation():
    batch = observations(3)
    batch["visible"][:, 1, 0, 1] = False
    batch["seen"][:, :, 0, 1] = True
    batch["age"][:, 1, 0, 1] = 1
    actor = AugmentedActor()
    q, states = actor(batch)
    entity_states = states[..., 64:].reshape(2, 3, 5, 5, 16)
    torch.testing.assert_close(entity_states[:, 1, 0, 1], entity_states[:, 0, 0, 1])
    assert not torch.equal(entity_states[:, 2, 0, 1], entity_states[:, 1, 0, 1])

    unseen = observations(1)
    unseen["visible"][:, :, 0, 1] = False
    unseen["seen"][:, :, 0, 1] = True
    hidden = torch.randn(2, 5, 144)
    original_q, original_state = actor(unseen, hidden)
    changed = copy.deepcopy(unseen)
    changed["entities"][:, :, 1] = float("nan")
    changed["previous_action"][:, :, 1] = float("nan")
    changed_q, changed_state = actor(changed, hidden)
    assert torch.isfinite(changed_q[:, :, 0]).all()
    torch.testing.assert_close(changed_q[:, :, 0], original_q[:, :, 0])
    torch.testing.assert_close(changed_state[:, :, 0], original_state[:, :, 0])


def test_full_sequence_matches_chunks_without_input_mutation():
    batch = observations(5)
    actor = AugmentedActor()
    before = {key: value.clone() for key, value in batch.items()}
    full_q, full_states = actor(batch)
    hidden, chunk_q, chunk_states = None, [], []
    for start, stop in ((0, 2), (2, 3), (3, 5)):
        q, states = actor({key: value[:, start:stop] for key, value in batch.items()}, hidden)
        hidden = states[:, -1]
        chunk_q.append(q)
        chunk_states.append(states)
    torch.testing.assert_close(torch.cat(chunk_q, 1), full_q)
    torch.testing.assert_close(torch.cat(chunk_states, 1), full_states)
    for key in batch:
        torch.testing.assert_close(batch[key], before[key])


def test_finite_useful_gradients_reach_both_streams_and_fusion():
    batch = observations(3)
    actor = AugmentedActor()
    q, _ = actor(batch)
    q.square().sum().backward()
    for parameter in (
        actor.rnn.weight_hh,
        actor.entity_rnn.weight_hh,
        actor.entity_attn.in_trans.weight,
        actor.head.weight,
    ):
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()
        assert torch.count_nonzero(parameter.grad)
