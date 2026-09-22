import copy
from types import SimpleNamespace

import pytest
import torch
from torch import nn

from experiments.candidates.goal_conditioned_entity_aggregation.b01.encoder import (
    OBS_DIM,
    OUTPUT_DIM,
    PEER_SLOTS,
    SKILLS,
    USER_SLOTS,
    ConditionalDeepSetsEncoder,
    EarlyAttentionEncoder,
    GoalConditionedActor,
    install_actor_encoder,
)
from hmasd.networks import R_Actor


class Box:
    def __init__(self, shape):
        self.shape = shape


class _Discoverer(nn.Module):
    def __init__(self, actor):
        super().__init__()
        self.actor = actor
        self.actor_context_adapter = None

    def actor_update_parameters(self):
        return list(self.actor.parameters())


def _actor(seed=17):
    torch.manual_seed(seed)
    args = SimpleNamespace(
        hidden_size=OUTPUT_DIM,
        gain=0.01,
        use_orthogonal=True,
        use_policy_active_masks=True,
        use_naive_recurrent_policy=False,
        use_recurrent_policy=True,
        recurrent_N=1,
        rnn_sequence_backend="step_reference",
        use_feature_normalization=False,
        continuous_action_distribution="gaussian",
    )
    return R_Actor(args, Box((OBS_DIM,)), Box((2,)), SKILLS, torch.device("cpu"))


def _agent(seed=17):
    actor = _actor(seed)
    discoverer = _Discoverer(actor)
    return SimpleNamespace(
        config=SimpleNamespace(obs_dim=OBS_DIM),
        skill_discoverer=discoverer,
        low_level_compact_extractor=None,
        discoverer_actor_optimizer=torch.optim.Adam(
            discoverer.actor_update_parameters(), lr=3.0e-4, weight_decay=1.0e-5
        ),
        discoverer_actor_scheduler=None,
    )


@pytest.mark.parametrize("encoder_type", [EarlyAttentionEncoder, ConditionalDeepSetsEncoder])
def test_encoder_exact_shapes_legal_skill_and_skill_gradient(encoder_type):
    encoder = encoder_type()
    assert encoder(torch.zeros(OBS_DIM), torch.tensor(0)).shape == (OUTPUT_DIM,)
    assert encoder(torch.zeros(4, OBS_DIM), torch.arange(4)).shape == (4, OUTPUT_DIM)

    observations = torch.randn(2, 3, OBS_DIM, requires_grad=True)
    held_skills = torch.tensor([[0, 1, 2], [3, 4, 5]])
    output = encoder(observations, held_skills)
    assert output.shape == (2, 3, OUTPUT_DIM)
    output.square().mean().backward()
    assert observations.grad is not None
    assert torch.isfinite(observations.grad).all()
    if encoder_type is EarlyAttentionEncoder:
        gradient = encoder.skill_query.weight.grad
    else:
        gradient = encoder.user_mlp[0].weight.grad[:, -SKILLS:]
    assert gradient is not None
    assert torch.count_nonzero(gradient).item() > 0

    with pytest.raises(ValueError, match="labels"):
        encoder(torch.zeros(OBS_DIM), torch.tensor(SKILLS))
    with pytest.raises(ValueError, match="integer-valued"):
        encoder(torch.zeros(OBS_DIM), torch.tensor(1.5))
    with pytest.raises(ValueError, match="batch shape"):
        encoder(torch.zeros(2, OBS_DIM), torch.zeros(3, dtype=torch.long))


def test_exact_rank_width_attention_and_all_zero_slot_contracts():
    early = EarlyAttentionEncoder()
    torch.testing.assert_close(early.user_rank, torch.linspace(0.0, 1.0, USER_SLOTS))
    torch.testing.assert_close(early.peer_rank, torch.linspace(0.0, 1.0, PEER_SLOTS))
    assert early.user_mlp[0].in_features == 4
    assert early.peer_mlp[0].in_features == 5
    assert early.user_attention.embed_dim == 64 and early.user_attention.num_heads == 4
    assert early.peer_attention.embed_dim == 64 and early.peer_attention.num_heads == 4
    assert not any(
        isinstance(module, nn.LayerNorm) for module in early.modules()
    )

    attended_lengths = []

    def record_length(_module, args):
        attended_lengths.append(args[1].shape[-2])

    handles = [
        early.user_attention.register_forward_pre_hook(record_length),
        early.peer_attention.register_forward_pre_hook(record_length),
    ]
    early(torch.zeros(2, OBS_DIM), torch.tensor([0, 1]))
    for handle in handles:
        handle.remove()
    assert attended_lengths == [USER_SLOTS, PEER_SLOTS]

    pooled = ConditionalDeepSetsEncoder()
    assert pooled.user_mlp[0].in_features == 14
    assert pooled.peer_mlp[0].in_features == 15
    with torch.no_grad():
        for parameter in pooled.parameters():
            parameter.zero_()
        # Map only the fixed rank scalar through each typed MLP.
        pooled.user_mlp[0].weight[0, 3] = 1.0
        pooled.user_mlp[2].weight[0, 0] = 1.0
        pooled.peer_mlp[0].weight[0, 4] = 1.0
        pooled.peer_mlp[2].weight[0, 0] = 1.0
        # Read the typed mean/max coordinates into separate output coordinates.
        pooled.output_projection[0].weight[0, 0] = 1.0
        pooled.output_projection[0].weight[1, 64] = 1.0
        pooled.output_projection[0].weight[2, 128] = 1.0
        pooled.output_projection[0].weight[3, 192] = 1.0
    output = pooled(torch.zeros(OBS_DIM), torch.tensor(0))
    torch.testing.assert_close(output[:4], torch.tensor([0.5, 1.0, 0.5, 1.0]))


def test_o_install_is_numerically_identical_and_rng_neutral():
    agent = _agent(23)
    reference = copy.deepcopy(agent.skill_discoverer.actor)
    observation = torch.randn(3, OBS_DIM)
    hidden = torch.randn(3, OUTPUT_DIM)
    masks = torch.ones(3, 1)
    skill = torch.tensor([0, 2, 5])
    expected = reference(observation, hidden, masks, skill, deterministic=True)
    rng_before = torch.random.get_rng_state().clone()
    installation = install_actor_encoder(agent, "O")
    assert torch.equal(torch.random.get_rng_state(), rng_before)
    actual = agent.skill_discoverer.actor(
        observation, hidden, masks, skill, deterministic=True
    )
    for expected_tensor, actual_tensor in zip(expected, actual):
        torch.testing.assert_close(actual_tensor, expected_tensor, rtol=0, atol=0)
    assert type(agent.skill_discoverer.actor) is R_Actor
    assert installation["original_base_type"] == "MLPBase"
    assert installation["active_base_type"] == "MLPBase"
    assert installation["timing"].as_dict()["forward_calls"] == 1


@pytest.mark.parametrize(
    ("arm", "base_type"),
    [("P", ConditionalDeepSetsEncoder), ("E", EarlyAttentionEncoder)],
)
def test_candidate_install_retains_common_actor_state_rng_and_optimizer(arm, base_type):
    agent = _agent(29)
    actor = agent.skill_discoverer.actor
    common_modules = {
        "film_generator": actor.film_generator,
        "rnn": actor.rnn,
        "act": actor.act,
    }
    common_state = {
        name: {key: value.detach().clone() for key, value in module.state_dict().items()}
        for name, module in common_modules.items()
    }
    rng_before = torch.random.get_rng_state().clone()
    installation = install_actor_encoder(agent, arm)

    assert torch.equal(torch.random.get_rng_state(), rng_before)
    assert type(actor) is GoalConditionedActor
    assert isinstance(actor.base, base_type)
    for name, module in common_modules.items():
        assert getattr(actor, name) is module
        for key, value in common_state[name].items():
            torch.testing.assert_close(module.state_dict()[key], value, rtol=0, atol=0)

    expected = agent.skill_discoverer.actor_update_parameters()
    owned = [
        parameter
        for group in agent.discoverer_actor_optimizer.param_groups
        for parameter in group["params"]
    ]
    assert len(owned) == len(expected)
    assert {id(parameter) for parameter in owned} == {id(parameter) for parameter in expected}
    assert all(id(parameter) in {id(item) for item in owned} for parameter in actor.base.parameters())
    assert installation["encoder_parameters"] == sum(
        parameter.numel() for parameter in actor.base.parameters()
    )
    assert installation["actor_parameters"] == sum(
        parameter.numel() for parameter in actor.parameters()
    )


@pytest.mark.parametrize("arm", ["P", "E"])
def test_raw_action_logprob_replays_with_same_held_skill_across_boundary(arm):
    agent = _agent(31)
    installation = install_actor_encoder(agent, arm)
    actor = agent.skill_discoverer.actor
    observations = torch.randn(3, 2, OBS_DIM)
    held_skills = torch.tensor([[0, 4], [1, 4], [1, 2]])
    hidden = torch.zeros(2, OUTPUT_DIM)
    masks = torch.ones(3, 2)

    torch.manual_seed(991)
    raw_actions, old_log_probs, _ = actor(
        observations, hidden, masks, held_skills, deterministic=False
    )
    replayed_log_probs, entropy = actor.evaluate_actions(
        observations, hidden, raw_actions, masks, held_skills
    )
    torch.testing.assert_close(replayed_log_probs, old_log_probs, rtol=0, atol=1.0e-6)
    assert torch.isfinite(entropy)
    timing = installation["timing"].as_dict()
    assert timing["forward_calls"] == 1
    assert timing["evaluate_actions_calls"] == 1
    assert timing["total_seconds"] >= 0.0


@pytest.mark.parametrize("arm", ["P", "E"])
def test_candidate_actor_checkpoint_roundtrip(arm):
    source = _agent(41)
    target = _agent(43)
    install_actor_encoder(source, arm)
    install_actor_encoder(target, arm)
    target.skill_discoverer.actor.load_state_dict(source.skill_discoverer.actor.state_dict())

    observations = torch.randn(2, OBS_DIM)
    held_skills = torch.tensor([1, 5])
    hidden = torch.zeros(2, OUTPUT_DIM)
    masks = torch.ones(2, 1)
    source_output = source.skill_discoverer.actor(
        observations, hidden, masks, held_skills, deterministic=True
    )
    target_output = target.skill_discoverer.actor(
        observations, hidden, masks, held_skills, deterministic=True
    )
    for source_tensor, target_tensor in zip(source_output, target_output):
        torch.testing.assert_close(target_tensor, source_tensor, rtol=0, atol=0)


def test_unknown_arm_is_rejected():
    with pytest.raises(ValueError, match="expected one of O, P, E"):
        install_actor_encoder(_agent(), "L")
