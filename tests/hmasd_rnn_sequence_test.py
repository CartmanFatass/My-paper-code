from types import SimpleNamespace

import pytest
import torch
from torch import nn

from hmasd.networks import SkillDiscoverer
from hmasd.r_mappo_utils import RNNLayer


def _run_with_grad(layer, x, hxs, masks, weight):
    layer.zero_grad(set_to_none=True)
    x = x.detach().clone().requires_grad_(True)
    hxs = hxs.detach().clone().requires_grad_(True)
    output, final_hidden = layer(x, hxs, masks)
    loss = (output * weight).sum() + final_hidden.square().sum()
    loss.backward()
    parameter_grads = {
        name: parameter.grad.detach().clone()
        for name, parameter in layer.named_parameters()
    }
    return (
        output.detach(),
        final_hidden.detach(),
        x.grad.detach(),
        hxs.grad.detach(),
        parameter_grads,
    )


@pytest.mark.parametrize(
    "reset_rows",
    [(), (1,), (2, 3, 7), (1, 2, 3, 4, 5, 6, 7)],
)
def test_segmented_rnn_matches_step_reference_forward_hidden_and_gradients(reset_rows):
    torch.manual_seed(8102026)
    reference = RNNLayer(7, 11, 1, True, sequence_backend="step_reference").double()
    segmented = RNNLayer(7, 11, 1, True, sequence_backend="segmented").double()
    segmented.load_state_dict(reference.state_dict())

    x = torch.randn(8, 5, 7, dtype=torch.float64)
    hxs = torch.randn(5, 11, dtype=torch.float64)
    masks = torch.ones(8, 5, dtype=torch.float64)
    for row in reset_rows:
        masks[row, row % 5] = 0.0
    weight = torch.randn(8, 5, 11, dtype=torch.float64)

    reference_result = _run_with_grad(reference, x, hxs, masks, weight)
    segmented_result = _run_with_grad(segmented, x, hxs, masks, weight)
    for reference_tensor, segmented_tensor in zip(
        reference_result[:4], segmented_result[:4]
    ):
        torch.testing.assert_close(reference_tensor, segmented_tensor, rtol=0.0, atol=1e-12)
    for name in reference_result[4]:
        torch.testing.assert_close(
            reference_result[4][name],
            segmented_result[4][name],
            rtol=0.0,
            atol=1e-12,
        )


def test_segmented_rnn_rejects_ineligible_recurrent_depth():
    with pytest.raises(ValueError, match="recurrent_N == 1"):
        RNNLayer(4, 4, 2, True, sequence_backend="segmented")


class _CaptureActor(nn.Module):
    def __init__(self):
        super().__init__()
        self.masks = None

    def evaluate_actions(self, observations, initial_hxs, actions, masks, skills):
        self.masks = masks.detach().clone()
        return torch.zeros_like(masks), torch.tensor(0.0)


class _CaptureCritic(nn.Module):
    def __init__(self):
        super().__init__()
        self.masks = None

    def forward(self, states, initial_hxs, masks, skills):
        self.masks = masks.detach().clone()
        return torch.zeros((*masks.shape, 1)), initial_hxs


def _discoverer_config():
    return SimpleNamespace(
        hidden_size=8,
        obs_dim=4,
        state_dim=5,
        n_z=3,
        n_Z=2,
        action_dim=2,
        action_bound=1.0,
        action_space_type="discrete",
        use_compact_in_low_level_actor=False,
        rnn_sequence_backend="step_reference",
    )


def test_skill_discoverer_shifts_transition_done_to_next_rnn_entry_mask():
    discoverer = SkillDiscoverer(_discoverer_config(), device=torch.device("cpu"))
    actor = _CaptureActor()
    critic = _CaptureCritic()
    discoverer.actor = actor
    discoverer.critic = critic

    observations = torch.zeros(4, 2, 4)
    states = torch.zeros(4, 2, 5)
    skills = torch.zeros(4, 2, dtype=torch.long)
    actions = torch.zeros(4, 2, dtype=torch.long)
    dones = torch.tensor(
        [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]
    )
    initial_hxs = torch.ones(2, 8)

    discoverer.evaluate_sequence(
        observations,
        skills,
        actions,
        states,
        skills,
        initial_hxs=initial_hxs,
        dones_seq=dones,
        initial_critic_hxs=initial_hxs,
    )

    expected = torch.tensor(
        [[1.0, 1.0], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]]
    )
    torch.testing.assert_close(actor.masks, expected)
    torch.testing.assert_close(critic.masks, expected)


def test_skill_discoverer_keeps_reference_backend_as_unconfigured_default():
    config = _discoverer_config()
    delattr(config, "rnn_sequence_backend")
    discoverer = SkillDiscoverer(config, device=torch.device("cpu"))
    assert discoverer.actor.rnn.sequence_backend == "step_reference"
    assert discoverer.critic.rnn.sequence_backend == "step_reference"
