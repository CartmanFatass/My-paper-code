"""One public phase, one team likelihood, ordinary fan-in initialization."""
import math
import numpy as np
import torch
from torch import nn

from experiments.candidates.roster_consistent_latent_exploration_tbcfv.models import DeterministicZeroLinear


class PhasePolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.row1 = DeterministicZeroLinear(8, 32, dtype=torch.float64)
        self.row2 = DeterministicZeroLinear(32, 32, dtype=torch.float64)
        self.head = DeterministicZeroLinear(36, 32, dtype=torch.float64)
        self.score = DeterministicZeroLinear(32, 1, dtype=torch.float64)

    def initialize(self, uniform_entries):
        with torch.no_grad():
            for name, layer in self.named_children():
                if name == "score":
                    continue  # the sole scalar score layer remains zero
                bound = 1.0 / math.sqrt(layer.in_features)
                for field in ("weight", "bias"):
                    parameter = getattr(layer, field)
                    values = uniform_entries(name + "." + field, parameter.numel())
                    parameter.copy_(torch.tensor(values, dtype=torch.float64).reshape_as(parameter)
                                    .mul(2 * bound).sub(bound))

    def forward(self, features, context):
        # [lanes, phases, current entities, 8], no padded entity or phase rows.
        encoded = torch.tanh(self.row2(torch.tanh(self.row1(features))))
        pooled = encoded.mean(dim=-2)
        common = context[:, None, :].expand(-1, pooled.shape[1], -1)
        return self.score(torch.tanh(self.head(torch.cat((pooled, common), dim=-1)))).squeeze(-1)


def quota_arrays(public):
    """N candidate mappings in physical entity-row order; keys are never features."""
    n = len(public[0].positions)
    positions = np.asarray([p.positions for p in public], dtype=np.int64)
    ranks = np.asarray([p.angular_ranks for p in public], dtype=np.int64)
    demands = np.asarray([p.demands for p in public], dtype=np.int64)
    beacons = np.asarray([p.beacon_positions for p in public], dtype=np.int64)
    quota = np.stack([np.repeat(np.arange(6), d) for d in demands])
    indices = (ranks[:, None, :] + np.arange(n)[None, :, None]) % n
    targets = np.take_along_axis(quota[:, None, :], indices, axis=2)
    targets_at = np.take_along_axis(beacons[:, None, :], targets, axis=2)
    delta = (targets_at - positions[:, None, :]) % 120
    signed = np.where(delta <= 60, delta, delta - 120)
    return positions, ranks, demands, targets, targets_at, signed


def phase_features(public):
    x, ranks, demands, targets, target_x, signed = quota_arrays(public)
    shape = targets.shape
    assigned_d = np.take_along_axis(demands[:, None, :], targets, axis=2)
    newcomers = np.asarray([p.newcomers for p in public], dtype=np.float64)
    n = x.shape[1]
    rows = np.stack((
        np.broadcast_to(np.sin(x[:, None, :] * (2 * np.pi / 120)), shape),
        np.broadcast_to(np.cos(x[:, None, :] * (2 * np.pi / 120)), shape),
        np.sin(target_x * (2 * np.pi / 120)), np.cos(target_x * (2 * np.pi / 120)),
        assigned_d / 2, signed / 60,
        np.broadcast_to(ranks[:, None, :] / max(n - 1, 1), shape),
        np.broadcast_to(newcomers[:, None, :], shape)), axis=-1)
    context = [[n / 12, p.tick / 64, float(p.roster_event), float(p.new_epoch)] for p in public]
    return torch.from_numpy(rows), torch.tensor(context, dtype=torch.float64), targets


def sampled_phase(model, public, uniforms):
    features, context, targets = phase_features(public)
    log_probability = torch.log_softmax(model(features, context), dim=-1)
    cdf = log_probability.detach().exp().numpy().cumsum(axis=-1)
    phases = np.minimum((cdf < np.asarray(uniforms)[:, None]).sum(axis=-1), cdf.shape[1] - 1)
    selected = log_probability[torch.arange(len(public)), torch.from_numpy(phases)]
    actions = targets[np.arange(len(public)), phases]
    return actions, selected, phases


def greedy_phase(public):
    _, _, _, targets, _, signed = quota_arrays(public)
    phases = np.abs(signed).sum(axis=-1).argmin(axis=-1)  # first/smallest phase on exact tie
    return targets[np.arange(len(public)), phases]


def adam_update(model, optimizer, returns, scores, cell_indices, baselines):
    """The full-return score gradient is evaluated before either mutable step."""
    advantage = returns.detach() - baselines.detach()[cell_indices]
    loss = -(advantage * scores).mean()
    if not torch.isfinite(loss):
        raise FloatingPointError("nonfinite loss before parameter/baseline mutation")
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    gradients = [p.grad for p in model.parameters() if p.grad is not None]
    if not all(torch.isfinite(g).all() for g in gradients):
        raise FloatingPointError("nonfinite gradient before parameter/baseline mutation")
    before = flat_parameters(model)
    gradient_norm = torch.linalg.vector_norm(torch.cat([g.reshape(-1) for g in gradients])).item()
    optimizer.step()
    means = torch.stack([returns[cell_indices == c].mean() for c in range(len(baselines))])
    updated = (.95 * baselines + (1.0 - .95) * means).detach()
    return updated, dict(loss=float(loss.detach()), gradient_norm=gradient_norm,
                        parameter_step_norm=float(torch.linalg.vector_norm(flat_parameters(model) - before)),
                        backward_calls=1, optimizer_calls=1, baseline_updates=1)


def flat_parameters(model):
    return torch.cat([p.detach().reshape(-1) for p in model.parameters()])
