"""Synthetic engineering checks, not a native experiment or learning result."""
import copy

import numpy as np
import pytest
import torch

from experiments.candidates.ucope.reactive_renewal_b01 import reactive
from experiments.candidates.ucope.uav_motion_prefix_b01.environment import SyntheticAdapter
from experiments.candidates.ucope.uav_motion_prefix_b01.policy import arm_copy, generator, templates
from tools.analysis.temporal_alignment import (
    _commands, exchange_calendars, frozen_episode, paired_effects, random_inputs,
    validate_calendar,
)


@pytest.fixture(scope="module", autouse=True)
def single_thread():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


def model():
    return arm_copy(templates(9901), True, duration_head_seed=990100012)[0]


def force_branch(actor, branch):
    with torch.no_grad():
        actor.duration[-1].weight.zero_()
        actor.duration[-1].bias.fill_(-1000)
        actor.duration[-1].bias[branch] = 0


def episode(actor, world, horizon=12, calendar=None):
    epsilon, uniforms = random_inputs(67031, world, horizon)
    return frozen_episode(actor, SyntheticAdapter(world, horizon), world,
                          epsilon, uniforms, calendar)


def test_self_calendar_identity_preserves_parameters_and_global_rng():
    actor = model()
    weights = copy.deepcopy(actor.state_dict())
    torch_rng = torch.get_rng_state().clone()
    numpy_rng = np.random.get_state()
    first = episode(actor, 11)
    replay = episode(actor, 11, calendar=first.fresh)
    for key in ("commands", "fresh", "actor_inputs", "rewards"):
        np.testing.assert_array_equal(getattr(first, key), getattr(replay, key))
    for name, initial in weights.items():
        torch.testing.assert_close(actor.state_dict()[name], initial, rtol=0, atol=0)
    assert all(parameter.grad is None for parameter in actor.parameters())
    assert torch.equal(torch.get_rng_state(), torch_rng)
    current = np.random.get_state()
    assert current[0] == numpy_rng[0] and current[2:] == numpy_rng[2:]
    np.testing.assert_array_equal(current[1], numpy_rng[1])
    assert first.score == float(first.rewards.sum() / 12)


def test_hold_copies_own_command_but_observation_and_gru_advance():
    actor = model()
    force_branch(actor, reactive.KEEP)
    hidden = []
    handle = actor.register_forward_hook(lambda _m, _i, output: hidden.append(output[2].clone()))
    try:
        trace = episode(actor, 21, 6)
    finally:
        handle.remove()
    np.testing.assert_array_equal(trace.fresh[:, 0], [True, False, True, False, True, False])
    for tick in (1, 3, 5):
        np.testing.assert_array_equal(trace.commands[tick], trace.commands[tick - 1])
        np.testing.assert_array_equal(trace.actor_inputs[tick, :, 104:107], trace.commands[tick - 1])
        assert not np.array_equal(trace.actor_inputs[tick, :, :3], trace.actor_inputs[tick - 1, :, :3])
        assert not torch.equal(hidden[tick], hidden[tick - 1])
    assert len(hidden) == 6
    np.testing.assert_array_equal(trace.actor_inputs[:, 0, -1], [0, .25, 0, .25, 0, .25])


@pytest.mark.parametrize("branch", [reactive.KEEP, reactive.END])
def test_command_step_matches_existing_reactive_sampler(branch):
    actor = model()
    force_branch(actor, branch)
    with torch.no_grad():
        actor.log_std.copy_(torch.tensor([-8., .3, 4.]))
    previous = np.linspace(-.9, .9, 15, dtype=np.float32).reshape(5, 3)
    eligible = np.array([True, False, True, False, True])
    mean = torch.linspace(-.3, .3, 15).reshape(5, 3)
    recurrent = torch.zeros(5, 64)
    reference = reactive.draw_commands(actor, mean, recurrent, previous, eligible,
                                       generator(41), generator(42))
    noise = np.zeros((5, 3), dtype=np.float32)
    noise_rng = generator(41)
    for agent in np.flatnonzero(reference[3].numpy()):
        noise[agent] = torch.randn(3, generator=noise_rng).numpy()
    sent, fresh = _commands(actor, mean, recurrent, previous, eligible,
                            noise, np.full(5, .3), None)
    np.testing.assert_array_equal(sent, reference[0])
    np.testing.assert_array_equal(fresh, reference[3].numpy())


def test_exchange_preserves_whole_calendars_and_uses_recipient_history():
    actor = model()
    traces = [episode(actor, world) for world in (11, 12, 13, 14)]
    original = np.stack([trace.fresh for trace in traces])
    swapped = exchange_calendars(original)
    np.testing.assert_array_equal(swapped, original[[1, 0, 3, 2]])
    np.testing.assert_array_equal(exchange_calendars(swapped), original)
    np.testing.assert_array_equal(swapped.sum(axis=(0, 1)), original.sum(axis=(0, 1)))
    assert sorted(row.tobytes() for row in swapped) == sorted(row.tobytes() for row in original)
    assert not np.shares_memory(original, swapped)
    recipient = episode(actor, 11, calendar=swapped[0])
    np.testing.assert_array_equal(recipient.fresh, original[1])
    assert not np.array_equal(recipient.commands, traces[1].commands)
    for tick in range(1, 12):
        held = ~recipient.fresh[tick]
        np.testing.assert_array_equal(recipient.commands[tick, held], recipient.commands[tick - 1, held])
        np.testing.assert_array_equal(recipient.actor_inputs[tick, :, 104:107], recipient.commands[tick - 1])


@pytest.mark.parametrize("calendar", [
    np.zeros((3, 5), bool),
    np.array([[True] * 5, [False] * 5, [False] * 5]),
    np.ones((3, 5), int), np.ones((3, 4), bool), np.ones((0, 5), bool),
])
def test_invalid_calendars_are_rejected(calendar):
    with pytest.raises(ValueError):
        validate_calendar(calendar)


@pytest.mark.parametrize("count", [0, 1, 3])
def test_exchange_requires_disjoint_complete_pairs(count):
    with pytest.raises(ValueError):
        exchange_calendars(np.ones((count, 3, 5), bool))


def test_random_tables_have_stable_slots_and_separate_worlds():
    short = random_inputs(7, 9, 3)
    long = random_inputs(7, 9, 12)
    other = random_inputs(7, 10, 12)
    for small, large, independent in zip(short, long, other):
        np.testing.assert_array_equal(small, large[:3])
        assert not np.array_equal(large, independent)
    assert long[0].dtype == np.float32
    assert ((long[1] >= 0) & (long[1] < 1)).all()


def test_pair_reducer_keeps_adverse_worlds_and_returns_pair_units():
    effects = paired_effects([0, 5, 6, 1], [2, 4, 3, 8])
    np.testing.assert_array_equal(effects, [-.5, -2.])
    assert effects.shape == (2,)
    assert effects.mean() == np.mean(np.array([0, 5, 6, 1]) - [2, 4, 3, 8])


@pytest.mark.parametrize("online, exchanged", [
    ([], []), ([1], [2]), ([1, 2], [1]), ([1, np.nan], [1, 2]),
    ([1, 2], [1, np.inf]), ([[1, 2]], [[1, 2]]),
])
def test_reducer_rejects_incomplete_or_nonfinite_panels(online, exchanged):
    with pytest.raises(ValueError):
        paired_effects(online, exchanged)


def test_bad_random_tables_and_early_termination_fail():
    actor = model()
    epsilon, uniforms = random_inputs(7, 9, 6)
    bad = epsilon.copy()
    bad[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        frozen_episode(actor, SyntheticAdapter(9, 6), 9, bad, uniforms)
    bad_uniforms = uniforms.copy()
    bad_uniforms[0, 0] = 1
    with pytest.raises(ValueError, match="uniforms"):
        frozen_episode(actor, SyntheticAdapter(9, 6), 9, epsilon, bad_uniforms)
    with pytest.raises(ValueError, match="incomplete"):
        frozen_episode(actor, SyntheticAdapter(9, 3), 9, epsilon, uniforms)
    with pytest.raises(ValueError, match="same horizon"):
        frozen_episode(actor, SyntheticAdapter(9, 6), 9, epsilon, uniforms,
                       np.ones((4, 5), bool))


def test_short_tables_do_not_score_an_unfinished_episode():
    epsilon, uniforms = random_inputs(7, 9, 3)
    with pytest.raises(ValueError, match="not terminated"):
        frozen_episode(model(), SyntheticAdapter(9, 6), 9, epsilon, uniforms)


class SwitchWorld:
    """Three-tick manufactured example; reward matters only at tick one."""
    def __init__(self, constant_reward=False):
        self.constant_reward = constant_reward

    def reset(self, seed):
        self.world, self.tick = seed, 0
        return self.observation(), {}

    def observation(self):
        obs = np.zeros((5, 104), dtype=np.float32)
        obs[:, 0] = -.5 if self.world == 1 and self.tick > 0 else .5
        return obs

    def step(self, command):
        target = self.observation()[:, 0]
        reward = (np.zeros(5) if self.constant_reward or self.tick != 1
                  else -np.square(command[:, 0] - target))
        self.tick += 1
        return self.observation(), 0., self.tick == 3, False, {
            "rewards_dict": {f"uav_{i}": value for i, value in enumerate(reward)}}


class SwitchActor(torch.nn.Module):
    """Keep an already suitable command, otherwise request a fresh one."""
    def __init__(self):
        super().__init__()
        self.log_std = torch.nn.Parameter(torch.zeros(3), requires_grad=False)

    def forward(self, x, hidden):
        mean = torch.zeros(1, 5, 3)
        mean[0, :, 0] = torch.atanh(x[0, :, 0])
        recurrent = hidden.clone() + 1
        recurrent[0, :, 0] = (x[0, :, 0] - x[0, :, 104]).abs()
        return mean, recurrent, recurrent

    def duration(self, recurrent):
        matched = recurrent[:, 0] < .01
        return torch.stack((matched.float(), (~matched).float()), -1) * 1000


@pytest.mark.parametrize("constant_reward", [False, True])
def test_known_alignment_example_and_null_preserve_calendars(constant_reward):
    actor = SwitchActor()
    epsilon, uniforms = np.zeros((3, 5, 3), np.float32), np.full((3, 5), .5)
    online = [frozen_episode(actor, SwitchWorld(constant_reward), world, epsilon, uniforms)
              for world in (0, 1)]
    calendars = exchange_calendars(np.stack([trace.fresh for trace in online]))
    exchanged = [frozen_episode(actor, SwitchWorld(constant_reward), world, epsilon, uniforms, calendar)
                 for world, calendar in enumerate(calendars)]
    effects = paired_effects([x.score for x in online], [x.score for x in exchanged])
    np.testing.assert_allclose(effects, [0. if constant_reward else 5 / 6], atol=1e-7)
    np.testing.assert_array_equal(calendars.sum(axis=(0, 1)),
                                  np.stack([x.fresh for x in online]).sum(axis=(0, 1)))
