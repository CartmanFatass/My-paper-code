"""Causal and information-rights checks for the raw cache actor."""

import torch

from experiments.candidates.vap_folr_core.entity_history_b01.model import (
    Actor as GenericActor,
)
from experiments.candidates.vap_folr_core.last_sighting_a01.model import Actor


def make_batch(batch_size=1, steps=5, all_visible=False):
    generator = torch.Generator().manual_seed(4801)
    continuation = torch.ones(batch_size, steps, 5, dtype=torch.bool)
    continuation[:, 0] = False
    active = torch.ones(batch_size, steps, 5, dtype=torch.bool)
    visible = torch.eye(5, dtype=torch.bool)[None, None].repeat(
        batch_size, steps, 1, 1
    )
    if all_visible:
        visible[:] = True
    seen = torch.zeros_like(visible)
    age = torch.zeros_like(visible, dtype=torch.int16)
    for step in range(steps):
        carry = continuation[:, step, :, None] & continuation[:, step, None, :]
        previous_seen = seen[:, step - 1] if step else torch.zeros_like(seen[:, 0])
        previous_age = age[:, step - 1] if step else torch.zeros_like(age[:, 0])
        carried_seen = previous_seen & carry
        seen[:, step] = carried_seen | visible[:, step]
        age[:, step] = torch.where(carried_seen, previous_age + 1, 0)
        age[:, step].masked_fill_(visible[:, step], 0)
    return {
        "entities": torch.rand(batch_size, steps, 5, 4, generator=generator),
        "previous_action": torch.rand(
            batch_size, steps, 5, 5, generator=generator
        ),
        "entity_mask": ~active,
        "visible": visible,
        "obs_mask": ~visible,
        "seen": seen,
        "age": age,
        "birth": ~continuation,
        "continuation": continuation,
        "departure": torch.zeros_like(continuation),
        "event": torch.zeros(batch_size, steps, dtype=torch.bool),
    }


def cache_from(states):
    return states[..., 64:].reshape(*states.shape[:-1], 5, 9)


def test_constructor_preserves_generic_parameters_buffers_and_rng():
    torch.manual_seed(4411)
    generic = GenericActor("GENERIC_RETAIN")
    generic_rng = torch.random.get_rng_state().clone()
    torch.manual_seed(4411)
    cached = Actor()
    assert torch.equal(generic_rng, torch.random.get_rng_state())
    assert generic.state_dict().keys() == cached.state_dict().keys()
    for name, value in generic.state_dict().items():
        torch.testing.assert_close(value, cached.state_dict()[name], rtol=0, atol=0)
    assert sum(p.numel() for p in generic.parameters()) == sum(
        p.numel() for p in cached.parameters()
    )


def test_cache_matches_hand_sequence_and_clears_both_lifetimes():
    batch = make_batch(steps=4)
    batch["visible"][0, 0, 0, 1] = True
    batch["visible"][0, 1, 2, 1] = True
    # Subject 1 is replaced at t=2; observer 0 is replaced at t=3.
    batch["continuation"][0, 2, 1] = False
    batch["continuation"][0, 3, 0] = False
    # Recompute truthful seen/age after the visibility/lifetime edits.
    batch["seen"].zero_()
    batch["age"].zero_()
    for step in range(4):
        carry = (
            batch["continuation"][:, step, :, None]
            & batch["continuation"][:, step, None, :]
        )
        previous = batch["seen"][:, step - 1] if step else torch.zeros(1, 5, 5, dtype=torch.bool)
        previous_age = batch["age"][:, step - 1] if step else torch.zeros(1, 5, 5, dtype=torch.int16)
        carried = previous & carry
        batch["seen"][:, step] = carried | batch["visible"][:, step]
        batch["age"][:, step] = torch.where(carried, previous_age + 1, 0)
        batch["age"][:, step].masked_fill_(batch["visible"][:, step], 0)

    physical = torch.cat((batch["entities"], batch["previous_action"]), -1)
    _, states = Actor()(batch)
    cache = cache_from(states)
    torch.testing.assert_close(cache[0, 0, 0, 1], physical[0, 0, 1])
    torch.testing.assert_close(cache[0, 1, 0, 1], physical[0, 0, 1])
    torch.testing.assert_close(cache[0, 1, 2, 1], physical[0, 1, 1])
    # The new subject's self-observer immediately overwrites its own cell;
    # every other observer loses the previous subject lifetime.
    assert torch.count_nonzero(cache[0, 2, [0, 2, 3, 4], 1]) == 0
    torch.testing.assert_close(cache[0, 2, 1, 1], physical[0, 2, 1])
    assert torch.count_nonzero(cache[0, 3, 0]) == 9  # new observer sees only itself
    assert torch.count_nonzero(cache[0, 3, 0, 1:]) == 0


def test_hidden_current_and_other_observer_sightings_do_not_leak():
    batch = make_batch(steps=3)
    batch["visible"][0, 0, 0, 1] = True
    batch["seen"][:, 0, 0, 1] = True
    batch["seen"][:, 1:, 0, 1] = True
    changed = {name: value.clone() for name, value in batch.items()}
    # At t=1 observer 0 cannot see subject 1. Observer 2 can, so this also
    # distinguishes observer-private cache rows.
    changed["visible"][0, 1, 2, 1] = True
    changed["seen"][0, 1:, 2, 1] = True
    changed["entities"][0, 1, 1] += 1000
    actor = Actor()
    q_first, h_first = actor(batch)
    q_changed, h_changed = actor(changed)
    torch.testing.assert_close(q_first[0, 1, 0], q_changed[0, 1, 0], rtol=0, atol=0)
    torch.testing.assert_close(
        cache_from(h_first)[0, 1, 0, 1],
        cache_from(h_changed)[0, 1, 0, 1],
        rtol=0,
        atol=0,
    )
    assert not torch.equal(
        cache_from(h_first)[0, 1, 2, 1], cache_from(h_changed)[0, 1, 2, 1]
    )


def test_online_and_whole_sequence_are_exactly_causal_equivalent():
    batch = make_batch(batch_size=2, steps=7)
    batch["visible"][:, 0, 0, 1] = True
    batch["seen"][:, :, 0, 1] = True
    actor = Actor()
    whole_q, whole_state = actor(batch)
    hidden = None
    online_q, online_state = [], []
    for step in range(7):
        one = {name: value[:, step : step + 1] for name, value in batch.items()}
        q, states = actor(one, hidden)
        hidden = states[:, -1]
        online_q.append(q)
        online_state.append(states)
    torch.testing.assert_close(torch.cat(online_q, 1), whole_q, rtol=0, atol=0)
    torch.testing.assert_close(
        torch.cat(online_state, 1), whole_state, rtol=0, atol=0
    )


def test_all_visible_matches_generic_q_and_gru_state_exactly():
    batch = make_batch(batch_size=2, steps=6, all_visible=True)
    torch.manual_seed(4499)
    generic = GenericActor("GENERIC_RETAIN")
    torch.manual_seed(4499)
    cached = Actor()
    generic_q, generic_state = generic(batch)
    cached_q, cached_state = cached(batch)
    # Attention is evaluated one causal step at a time for online/replay
    # identity, whereas Generic batches time into the attention call. The two
    # paths differ only by ordinary FP32 batched-matmul rounding.
    torch.testing.assert_close(cached_q, generic_q, rtol=1e-6, atol=3e-8)
    torch.testing.assert_close(
        cached_state[..., :64], generic_state, rtol=1e-6, atol=3e-8
    )
