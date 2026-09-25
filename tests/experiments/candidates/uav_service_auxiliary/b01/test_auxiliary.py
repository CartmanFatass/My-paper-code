import copy

import pytest
import torch
from torch import nn

from experiments.candidates.uav_service_auxiliary.b01.auxiliary import (
    AuxiliaryReplay,
    future_window_targets,
    recurrent_entry_masks,
)
from hmasd.r_mappo_utils import RNNLayer


class ToyActor(nn.Module):
    """Small R_Actor-shaped fixture using the production recurrent layer."""

    def __init__(self, obs_dim=3, hidden_size=5, n_skills=3):
        super().__init__()
        self.hidden_size = hidden_size
        self.base = nn.Sequential(nn.Linear(obs_dim, hidden_size), nn.Tanh())
        self.film_generator = nn.Linear(n_skills, 2 * hidden_size)
        self.rnn = RNNLayer(hidden_size, hidden_size, 1, False)
        self.act = nn.Linear(hidden_size, 2)
        with torch.no_grad():
            self.film_generator.weight.zero_()
            self.film_generator.bias[:hidden_size].fill_(1.0)
            self.film_generator.bias[hidden_size:].zero_()


def make_actor(seed=17):
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        return ToyActor()


def make_replay(T=8, E=1, N=2, D=3):
    generator = torch.Generator().manual_seed(29)
    observations = torch.randn(T, E, N, D, generator=generator)
    skills = torch.arange(T * E * N).reshape(T, E, N) % 3
    dones = torch.zeros(T, E, dtype=torch.bool)
    dones[3::4] = True
    qos = torch.linspace(0.1, 0.9, T).unsqueeze(1).expand(T, E).clone()
    return observations, skills, dones, qos


def clone_state(module):
    return {name: value.detach().clone() for name, value in module.state_dict().items()}


def assert_state_equal(left, right):
    assert left.keys() == right.keys()
    for name in left:
        torch.testing.assert_close(left[name], right[name], rtol=0, atol=0)


def state_moved(before, module):
    after = module.state_dict()
    return any(not torch.equal(before[name], after[name]) for name in before)


def test_future_targets_align_at_current_transition_and_censor_boundaries():
    qos = torch.stack((torch.arange(7), torch.arange(10, 17)), dim=1).float()
    dones = torch.zeros(7, 2, dtype=torch.bool)
    dones[2, 0] = True
    dones[6, 0] = True
    dones[3, 1] = True

    targets, valid = future_window_targets(qos, dones, window=3)

    torch.testing.assert_close(
        targets[:5],
        torch.tensor([[1.0, 11.0], [2.0, 12.0], [3.0, 13.0],
                      [4.0, 14.0], [5.0, 15.0]]),
    )
    torch.testing.assert_close(targets[5:], torch.zeros(2, 2))
    torch.testing.assert_close(
        valid,
        torch.tensor(
            [[True, True], [False, True], [False, False], [True, False],
             [True, True], [False, False], [False, False]]
        ),
    )


def test_entry_masks_shift_transition_done_and_initial_hidden_is_an_anchor():
    dones = torch.tensor([[False], [True], [False], [False]])
    masks = recurrent_entry_masks(dones, 2)
    torch.testing.assert_close(
        masks[:, 0, 0, 0], torch.tensor([1.0, 1.0, 0.0, 1.0])
    )
    torch.testing.assert_close(masks[:, 0, 0], masks[:, 0, 1])

    actor = make_actor()
    learner = AuxiliaryReplay(
        actor, "detach", initialization_seed=41, window=2, chunk_length=2
    )
    observations, skills, _, _ = make_replay(T=4, E=1, N=2)
    zero = torch.zeros(1, 2, actor.hidden_size)
    anchored = torch.full_like(zero, 2.0)
    prediction_zero = learner.predict(
        actor, observations, skills, dones, initial_hidden=zero
    )
    prediction_anchored = learner.predict(
        actor, observations, skills, dones, initial_hidden=anchored
    )
    assert not torch.equal(prediction_zero[:2], prediction_anchored[:2])
    torch.testing.assert_close(
        prediction_zero[2:], prediction_anchored[2:], rtol=0, atol=0
    )


def test_detach_updates_head_only_and_preserves_rng_and_incomplete_labels():
    actor = make_actor()
    observations, skills, dones, qos = make_replay()
    actor_before = clone_state(actor)

    torch.manual_seed(991)
    rng_before_construction = torch.random.get_rng_state().clone()
    learner = AuxiliaryReplay(
        actor, "detach", initialization_seed=43, window=2, chunk_length=4
    )
    torch.testing.assert_close(
        torch.random.get_rng_state(), rng_before_construction, rtol=0, atol=0
    )
    head_before = clone_state(learner.head)
    rng_before_update = torch.random.get_rng_state().clone()
    observed = learner.update(actor, observations, skills, dones, qos)

    torch.testing.assert_close(
        torch.random.get_rng_state(), rng_before_update, rtol=0, atol=0
    )
    assert_state_equal(actor_before, actor.state_dict())
    assert state_moved(head_before, learner.head)
    assert observed.supervised_team_rows == 6
    assert observed.supervised_agent_samples == 12
    assert observed.optimizer_steps == 2
    assert observed.head_gradient_norm > 0
    assert observed.representation_gradient_norm == 0
    assert learner.representation_optimizer is None
    assert learner.head_optimizer.param_groups[0]["lr"] == 3e-4

    censored_actor = make_actor()
    censored = AuxiliaryReplay(
        censored_actor, "detach", initialization_seed=43, window=10
    )
    censored_actor_before = clone_state(censored_actor)
    censored_head_before = clone_state(censored.head)
    no_label = censored.update(
        censored_actor, observations[:5], skills[:5], dones[:5], qos[:5]
    )
    assert no_label.optimizer_steps == no_label.supervised_agent_samples == 0
    assert_state_equal(censored_actor_before, censored_actor.state_dict())
    assert_state_equal(censored_head_before, censored.head.state_dict())


def test_joint_moves_only_base_and_rnn_and_clips_parameter_groups_separately(monkeypatch):
    actor = make_actor()
    observations, skills, dones, qos = make_replay()
    base_before = clone_state(actor.base)
    rnn_before = clone_state(actor.rnn)
    film_before = clone_state(actor.film_generator)
    action_before = clone_state(actor.act)
    learner = AuxiliaryReplay(
        actor, "joint", initialization_seed=47, window=2, chunk_length=4
    )

    clipped = []
    real_clip = torch.nn.utils.clip_grad_norm_

    def record_clip(parameters, *args, **kwargs):
        parameters = tuple(parameters)
        clipped.append(frozenset(id(parameter) for parameter in parameters))
        return real_clip(parameters, *args, **kwargs)

    monkeypatch.setattr(torch.nn.utils, "clip_grad_norm_", record_clip)
    observed = learner.update(actor, observations, skills, dones, qos)

    assert state_moved(base_before, actor.base)
    assert state_moved(rnn_before, actor.rnn)
    assert_state_equal(film_before, actor.film_generator.state_dict())
    assert_state_equal(action_before, actor.act.state_dict())
    assert all(parameter.grad is None for parameter in actor.film_generator.parameters())
    assert all(parameter.grad is None for parameter in actor.act.parameters())
    assert observed.representation_gradient_norm > 0
    assert learner.representation_optimizer.param_groups[0]["lr"] == 3e-5

    head_ids = frozenset(id(parameter) for parameter in learner.head.parameters())
    representation_ids = frozenset(
        id(parameter)
        for module in (actor.base, actor.rnn)
        for parameter in module.parameters()
    )
    assert head_ids.isdisjoint(representation_ids)
    assert clipped == [head_ids, representation_ids, head_ids, representation_ids]


def test_common_replay_is_deterministic_uses_explicit_normalized_obs_and_restores():
    actor = make_actor()
    observations, skills, dones, qos = make_replay()
    normalized = observations * 0.25 + 0.7
    learner = AuxiliaryReplay(
        actor, "joint", initialization_seed=53, window=2, chunk_length=3
    )
    learner.update(
        actor,
        observations,
        skills,
        dones,
        qos,
        normalized_observations=normalized,
    )

    torch.manual_seed(997)
    rng_before = torch.random.get_rng_state().clone()
    first = learner.predict(
        actor,
        observations,
        skills,
        dones,
        normalized_observations=normalized,
    )
    second = learner.predict(
        actor,
        observations,
        skills,
        dones,
        normalized_observations=normalized.clone(),
    )
    torch.testing.assert_close(first, second, rtol=0, atol=0)
    torch.testing.assert_close(torch.random.get_rng_state(), rng_before, rtol=0, atol=0)

    # The explicit normalized array is the actual replay input; no normalized
    # observation or normalizer state is retained by the component.
    explicit_as_raw = learner.predict(actor, normalized, skills, dones)
    torch.testing.assert_close(first, explicit_as_raw, rtol=0, atol=0)
    assert not torch.equal(first, learner.predict(actor, observations, skills, dones))

    actor_state = copy.deepcopy(actor.state_dict())
    checkpoint = learner.checkpoint_state()
    restored_actor = make_actor(seed=999)
    restored_actor.load_state_dict(actor_state)
    restored = AuxiliaryReplay(
        restored_actor, "joint", initialization_seed=53, window=2, chunk_length=3
    )
    restored.load_checkpoint_state(checkpoint)
    restored_prediction = restored.predict(
        restored_actor,
        observations,
        skills,
        dones,
        normalized_observations=normalized,
    )
    torch.testing.assert_close(first, restored_prediction, rtol=0, atol=0)
    assert restored.checkpoint_state()["updates"] == 1
    assert restored.checkpoint_state()["representation_optimizer"]["state"]


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_cuda_float32_smoke_preserves_rng_and_gradient_isolation():
    actor = make_actor().to("cuda")
    observations, skills, dones, qos = make_replay()
    film_before = clone_state(actor.film_generator)
    action_before = clone_state(actor.act)
    base_before = clone_state(actor.base)
    rnn_before = clone_state(actor.rnn)

    torch.manual_seed(1009)
    torch.cuda.manual_seed_all(1013)
    cpu_rng_before = torch.random.get_rng_state().clone()
    cuda_rng_before = [state.clone() for state in torch.cuda.get_rng_state_all()]
    learner = AuxiliaryReplay(
        actor, "joint", initialization_seed=59, window=2, chunk_length=4
    )
    observed = learner.update(actor, observations, skills, dones, qos)
    prediction = learner.predict(actor, observations, skills, dones)

    torch.testing.assert_close(
        torch.random.get_rng_state(), cpu_rng_before, rtol=0, atol=0
    )
    for before, after in zip(cuda_rng_before, torch.cuda.get_rng_state_all()):
        torch.testing.assert_close(after, before, rtol=0, atol=0)
    assert prediction.device.type == "cuda" and prediction.dtype == torch.float32
    assert torch.isfinite(prediction).all()
    assert torch.isfinite(torch.tensor(observed.loss))
    assert observed.representation_gradient_norm > 0
    assert state_moved(base_before, actor.base)
    assert state_moved(rnn_before, actor.rnn)
    assert_state_equal(film_before, actor.film_generator.state_dict())
    assert_state_equal(action_before, actor.act.state_dict())
