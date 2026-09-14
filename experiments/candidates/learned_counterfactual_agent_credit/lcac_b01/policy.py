"""Identical decentralized categorical actors; central V or factual joint Q."""
import copy

import torch
from torch import nn
from torch.nn import functional as F

from experiments.candidates.metric_ground_transport_allocation.mgtap_native_ground_geometry_b01.geometry import (
    DenseResidualEncoder,
)


COMMANDS = torch.tensor([[0., 0., 0.], [1., 0., 0.], [-1., 0., 0.],
                         [0., 1., 0.], [0., -1., 0.], [0., 0., 1.], [0., 0., -1.]])


class Actor(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = DenseResidualEncoder()
        # Retain the DENSE residual architecture's zero initial residual output.
        nn.init.zeros_(self.encoder.hidden.bias)
        nn.init.zeros_(self.encoder.context.weight)
        self.gru = nn.GRU(64, 64)
        self.head = nn.Linear(64, 7)

    def forward(self, observations, hidden):
        output, hidden = self.gru(torch.tanh(self.encoder(observations)), hidden)
        return self.head(output), output, hidden


class Critic(nn.Module):
    def __init__(self, inputs):
        super().__init__()
        self.network = nn.Sequential(nn.Linear(inputs, 128), nn.Tanh(),
                                     nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 1))

    def forward(self, inputs):
        return self.network(inputs).squeeze(-1)


def build_pair(master):
    base = 100000 * master
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(base + 11)
        actor = Actor()
        torch.manual_seed(base + 12)
        value = Critic(136)
        action_value = Critic(171)
        with torch.no_grad():
            action_value.network[0].weight[:, :136].copy_(value.network[0].weight)
            action_value.network[0].weight[:, 136:].zero_()
            action_value.network[0].bias.copy_(value.network[0].bias)
            for layer in (2, 4):
                action_value.network[layer].load_state_dict(value.network[layer].state_dict())
    return {"V": (copy.deepcopy(actor), value), "Q": (copy.deepcopy(actor), action_value)}


def action_terms(logits, actions):
    log_probs = logits.log_softmax(-1)
    selected = log_probs.gather(-1, actions[..., None]).squeeze(-1)
    entropy = -(log_probs.exp() * log_probs).sum(-1)
    return selected, entropy


def sample_actions(logits, rng):
    probabilities = logits.softmax(-1)
    cdf = probabilities.cumsum(-1)
    cdf = cdf / cdf[..., -1:]
    # One independent draw for each agent, with fixed consumption at every tick.
    uniforms = torch.rand(logits.shape[:-1] + (1,), generator=rng)
    actions = torch.searchsorted(cdf.contiguous(), uniforms, right=True).squeeze(-1)
    logp, _ = action_terms(logits, actions)
    return actions, probabilities, logp


def factual_inputs(states, actions):
    return torch.cat((states, F.one_hot(actions, 7).to(states.dtype).flatten(-2)), -1)


@torch.no_grad()
def counterfactual_baseline(critic, states, actions, probabilities):
    """35 Q rows/team tick; replace the entire focal one-hot, fixing teammates."""
    leading = states.shape[:-1]
    state = states.reshape(-1, 136)
    action = actions.reshape(-1, 5)
    one_hot = F.one_hot(action, 7).to(states.dtype)
    alternatives = one_hot[:, None, None].expand(-1, 5, 7, -1, -1).clone()
    for focal in range(5):
        alternatives[:, focal, :, focal, :] = torch.eye(7, dtype=states.dtype)
    inputs = torch.cat((state[:, None, None].expand(-1, 5, 7, -1),
                        alternatives.flatten(-2)), -1)
    values = critic(inputs)
    baseline = (probabilities.reshape(-1, 5, 7) * values).sum(-1)
    # Every focal contains the same factual joint action; reuse focal zero's entry.
    factual = values[:, 0].gather(-1, action[:, :1]).squeeze(-1)
    return baseline.reshape(*leading, 5), factual.reshape(leading)


def snapshot(actor, critic):
    return {name: torch.cat([p.detach().flatten() for p in module.parameters()]).clone()
            for name, module in (("actor", actor), ("critic", critic))}


def movement(initial, actor, critic):
    current = snapshot(actor, critic)
    result = {}
    for name, start in initial.items():
        norm = float(start.norm())
        displacement = float((current[name] - start).norm())
        result[name] = {"parameters": start.numel(), "initial_norm": norm,
                        "displacement": displacement,
                        "relative_displacement": displacement / norm if norm else None}
    return result
