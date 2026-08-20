"""Focused contracts for shared MAPPO action and recurrent-policy utilities."""

import ast
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from hmasd.networks import SkillDiscoverer
from hmasd.r_mappo_utils import ACTLayer


class MultiDiscrete:
    """Minimal space with the public surface ACTLayer consumes."""

    def __init__(self, nvec):
        self.nvec = np.asarray(nvec, dtype=np.int64)


def _multi_discrete_layer():
    layer = ACTLayer(
        MultiDiscrete([2, 3]), inputs_dim=1, use_orthogonal=True, gain=0.01
    )
    with torch.no_grad():
        for action_out in layer.action_outs:
            action_out.linear.weight.zero_()
            action_out.linear.bias.zero_()
            action_out.linear.weight[0, 0] = 1.0
            action_out.linear.weight[1, 0] = -1.0
    return layer


def _joint_entropy(layer, features):
    return torch.stack(
        [action_out(features).entropy() for action_out in layer.action_outs], dim=-1
    ).sum(dim=-1)


def test_multidiscrete_entropy_sums_components_then_weights_active_samples():
    layer = _multi_discrete_layer()
    features = torch.tensor([[0.0], [1.0], [-2.0]], dtype=torch.float32)
    actions = torch.zeros((3, 2), dtype=torch.long)
    active_masks = torch.tensor([[1.0], [0.0], [0.5]], dtype=torch.float32)

    log_probs, entropy = layer.evaluate_actions(
        features, actions, active_masks=active_masks
    )

    expected_per_sample = _joint_entropy(layer, features)
    expected = (expected_per_sample * active_masks.squeeze(-1)).sum() / active_masks.sum()
    assert log_probs.shape == (3, 1)
    assert torch.allclose(entropy, expected)


def test_multidiscrete_inactive_extreme_logits_do_not_affect_entropy():
    layer = _multi_discrete_layer()
    actions = torch.zeros((2, 2), dtype=torch.long)
    active_masks = torch.tensor([[1.0], [0.0]], dtype=torch.float32)
    ordinary_inactive = torch.tensor([[0.25], [0.0]], dtype=torch.float32)
    extreme_inactive = torch.tensor([[0.25], [100.0]], dtype=torch.float32)

    _, ordinary_entropy = layer.evaluate_actions(
        ordinary_inactive, actions, active_masks=active_masks
    )
    _, extreme_entropy = layer.evaluate_actions(
        extreme_inactive, actions, active_masks=active_masks
    )

    assert torch.allclose(ordinary_entropy, extreme_entropy)


def test_multidiscrete_entropy_rejects_zero_active_weight():
    layer = _multi_discrete_layer()
    with pytest.raises(ValueError, match="finite positive sum"):
        layer.evaluate_actions(
            torch.zeros((2, 1)),
            torch.zeros((2, 2), dtype=torch.long),
            active_masks=torch.zeros((2, 1)),
        )


class _MaskRecordingActor(torch.nn.Module):
    def forward(self, observation, hidden_state, masks, agent_skill, deterministic=False):
        self.masks = masks.detach().clone()
        return (
            torch.zeros((observation.shape[0], 1), device=observation.device),
            torch.zeros((observation.shape[0], 1), device=observation.device),
            hidden_state,
        )


class _MaskRecordingCritic(torch.nn.Module):
    def forward(self, state, hidden_state, masks, team_skill):
        self.masks = masks.detach().clone()
        return torch.zeros((state.shape[0], 1), device=state.device), hidden_state


def _inference_only_discoverer():
    discoverer = SkillDiscoverer.__new__(SkillDiscoverer)
    torch.nn.Module.__init__(discoverer)
    discoverer.actor_context_adapter = None
    discoverer.critic_context_adapter = None
    discoverer.actor = _MaskRecordingActor()
    discoverer.critic = _MaskRecordingCritic()
    return discoverer


def test_skill_discoverer_inference_callers_supply_ones_masks():
    """Inference callers own episode-boundary hidden-state resets, not ACT/RNN."""
    discoverer = _inference_only_discoverer()
    observations = torch.randn(3, 4)
    states = torch.randn(3, 5)
    hidden_state = torch.randn(3, 1, 2)

    discoverer.forward(
        observations, agent_skill=torch.zeros(3, dtype=torch.long), hidden_state=hidden_state
    )
    discoverer.get_value(
        states, team_skill=torch.zeros(3, dtype=torch.long), critic_hidden_state=hidden_state
    )

    assert torch.equal(discoverer.actor.masks, torch.ones((3, 1)))
    assert torch.equal(discoverer.critic.masks, torch.ones((3, 1)))


_ROOT = Path(__file__).resolve().parents[1]
_HOT_PATHS = (
    "ha_ctse_process/collectors.py",
    "ha_ctse_process/variable_roster_event.py",
    "ha_ctse_process/variable_roster_event_batching.py",
    "hmasd/networks.py",
    "hmasd/r_mappo_utils.py",
    "hmasd/utils.py",
    "envs/pettingzoo/uav_env.py",
    "envs/pettingzoo/uav_cpp_backend.py",
    "envs/pettingzoo/relay/channel_geometry.py",
    "envs/pettingzoo/relay/routed_core.py",
    "envs/pettingzoo/relay/energy_aware.py",
    "envs/pettingzoo/relay/forced_relay.py",
)


def test_safe_tensor_transformer_is_absent_from_production_hot_paths():
    """NaN/Inf repair must never enter event, rollout, RNN, or geometry execution."""
    for relative_path in _HOT_PATHS:
        tree = ast.parse((_ROOT / relative_path).read_text(encoding="utf-8"))
        offenders = [
            node
            for node in ast.walk(tree)
            if (
                isinstance(node, ast.Name) and node.id == "SafeTensorTransformer"
            )
            or (
                isinstance(node, ast.Attribute)
                and node.attr == "SafeTensorTransformer"
            )
            or (
                isinstance(node, ast.ImportFrom)
                and node.module == "hmasd.tensor_utils"
                and any(alias.name == "SafeTensorTransformer" for alias in node.names)
            )
        ]
        assert not offenders, f"{relative_path} must not use SafeTensorTransformer"
