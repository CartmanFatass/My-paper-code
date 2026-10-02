import numpy as np
import torch

from experiments.candidates.uav_message_content.b05.model import Actor
from experiments.candidates.uav_message_content.b07.offline import replay, replay_inputs, fit_learned
from experiments.candidates.uav_message_content.b07.receiver import Receiver, parameter_hash


def episode(horizon=2):
    packet = np.zeros((horizon, 10), dtype=np.float32)
    packet[:, :5] = .3
    packet[:, 6] = .1
    return dict(packet=packet, actor_input=np.zeros((horizon, 5, 186), dtype=np.float32),
                composed_mean=np.zeros((horizon, 5, 3), dtype=np.float32),
                sender=np.arange(horizon) % 5, due=np.arange(horizon) + 1)


def receiver():
    with torch.random.fork_rng():
        torch.manual_seed(81)
        actor = Receiver().requires_grad_(False)
    return actor


def test_original_forward_identical_base_input_gradients_and_frozen_weights():
    actor = receiver()
    old = Actor()
    old.load_state_dict(actor.state_dict())
    rng = torch.Generator().manual_seed(31)
    x = torch.rand(1, 5, 186, generator=rng, requires_grad=True)
    h = torch.rand(1, 5, 64, generator=rng, requires_grad=True)
    before = parameter_hash(actor)
    output = actor.components(x, h)
    expected = old.components(x.detach(), h.detach())
    assert all(torch.equal(a, b) for a, b in zip(output, expected))
    # Fresh residual output is zero: this gradient must pass through the base/GRU.
    output[0].square().sum().backward()
    assert x.grad[..., :171].abs().sum() > 0 and h.grad.abs().sum() > 0
    assert x.grad[..., 171:].abs().sum() == 0
    assert all(p.grad is None for p in actor.parameters())
    assert parameter_hash(actor) == before


def test_own_recurrent_replay_reset_causal_inputs_and_previous_commands():
    actor = receiver()
    e = episode(8)
    e["actor_input"][:, :, 104:107] = .6
    book = torch.full((256, 6), .4, requires_grad=True)
    x = replay_inputs(e, book, torch.ones(6), .25)
    assert torch.equal(x[..., :121], torch.from_numpy(e["actor_input"][..., :121]))
    assert not x[0, :, 121:].any()
    assert torch.equal(x[1, 1, 121:128], torch.tensor([.4, .4, .4, .4, .4, 0., .4]))
    counts = {}
    means, loss = replay(actor, [e], book, torch.ones(6), counts, "fit", .25)
    again = replay(actor, [e], book, torch.ones(6), {}, "fit", .25)[0]
    assert torch.equal(means, again)
    manual = []
    h = torch.zeros(1, 5, 64)
    for row in x:
        mean, _, h = actor(row[None], h)
        manual.append(mean[0])
    assert torch.equal(means[0], torch.stack(manual))
    loss.backward()
    assert book.grad.abs().sum() > 0
    assert counts["fit_actor_rows"] == 40 and counts["nearest_center_comparisons"] == 2048


def test_fixed_120_updates_shuffle_isolation_and_weight_movement():
    actor = receiver()
    before = parameter_hash(actor)
    global_state = torch.random.get_rng_state().clone()
    initial = torch.full((256, 6), .4)
    counts = {}
    fitted, history = fit_learned(actor, [episode() for _ in range(24)], initial, torch.ones(6), 19811, counts)
    assert len(history) == counts["adam_updates"] == 120
    assert counts["fit_actor_rows"] == 20 * 24 * 2 * 5
    assert counts["nearest_center_comparisons"] == 20 * 24 * 2 * 256
    expected_rng = np.random.default_rng(29811)
    for epoch in range(20):
        expected = expected_rng.permutation(24).tolist()
        assert sum((r["episodes"] for r in history if r["epoch"] == epoch), []) == expected
    assert history[0]["temperature"] == .25 and history[-1]["temperature"] == .025
    assert not torch.equal(initial, fitted)
    assert parameter_hash(actor) == before and torch.equal(global_state, torch.random.get_rng_state())
    assert all(p.grad is None for p in actor.parameters())
