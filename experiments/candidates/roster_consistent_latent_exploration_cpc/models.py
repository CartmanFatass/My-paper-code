from __future__ import annotations

import math

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .authorization import ProductionPermit, require_active_permit
from .config import ARMS, REGISTERED
from .host import MISSING_CLUE
from .rng import generator


class DeterministicZeroLinear(nn.Linear):
    """Registered Linear shape without nn.Linear's constructor-time RNG draw."""

    def reset_parameters(self) -> None:
        with torch.no_grad():
            self.weight.zero_()
            if self.bias is not None:
                self.bias.zero_()


class Manager(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.element1 = DeterministicZeroLinear(3, 32, dtype=torch.float64)
        self.element2 = DeterministicZeroLinear(32, 32, dtype=torch.float64)
        self.macro = DeterministicZeroLinear(33, 2, dtype=torch.float64)
        self.refinement = DeterministicZeroLinear(33, 8, dtype=torch.float64)
        for parameter in self.parameters():
            parameter.data.zero_()

    def forward(self, roles: torch.Tensor, clues: torch.Tensor, n: int) -> tuple[torch.Tensor, torch.Tensor]:
        role_onehot = F.one_hot(roles.to(torch.int64), num_classes=2).to(torch.float64)
        elements = torch.cat((role_onehot, clues[..., None].to(torch.float64)), dim=-1)
        pooled = torch.tanh(self.element2(torch.tanh(self.element1(elements)))).mean(dim=1)
        summary = torch.cat((pooled, torch.full((pooled.shape[0], 1), n / 9.0, dtype=torch.float64)), dim=1)
        macro = torch.softmax(self.macro(summary), dim=-1)
        refinement = sparsemax(self.refinement(summary).reshape(-1, 2, 4), dim=-1)
        return macro, refinement


class Actor(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.first = DeterministicZeroLinear(16, 64, dtype=torch.float64)
        self.second = DeterministicZeroLinear(64, 64, dtype=torch.float64)
        self.head = DeterministicZeroLinear(64, 3, dtype=torch.float64)
        for parameter in self.parameters():
            parameter.data.zero_()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.head(torch.tanh(self.second(torch.tanh(self.first(inputs)))))


class ArmModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.manager = Manager()
        self.macro_base = nn.Parameter(torch.zeros((2, 8), dtype=torch.float64))
        self.residual = nn.Parameter(torch.zeros((2, 4, 8), dtype=torch.float64))
        self.actor = Actor()

    def latent(self, macro: torch.Tensor, refinement: torch.Tensor | None, flexible: bool) -> torch.Tensor:
        base = self.macro_base[macro]
        return base + self.residual[macro, refinement] if flexible and refinement is not None else base


def actor_inputs(roles: np.ndarray, clues: np.ndarray, phase: int, n: int, latent: torch.Tensor) -> torch.Tensor:
    roles_t = torch.from_numpy(np.asarray(roles, dtype=np.int64))
    clues_np = np.asarray(clues, dtype=np.int64)
    role_onehot = F.one_hot(roles_t, num_classes=2).to(torch.float64)
    clue_index = np.where(clues_np < 0, 0, np.where(clues_np > 0, 1, 2)).astype(np.int64, copy=False)
    clue_onehot = F.one_hot(torch.from_numpy(clue_index), num_classes=3).to(torch.float64)
    phase_onehot = torch.zeros((*roles_t.shape, 2), dtype=torch.float64)
    phase_onehot[..., phase] = 1.0
    n_field = torch.full((*roles_t.shape, 1), n / 9.0, dtype=torch.float64)
    if latent.ndim == 2:
        expanded_latent = latent[:, None, :].expand(-1, roles_t.shape[1], -1)
    elif latent.ndim == 3 and tuple(latent.shape[:2]) == tuple(roles_t.shape):
        expanded_latent = latent
    else:
        raise ValueError("latent must be episode-common [B,8] or agent-private [B,N,8]")
    return torch.cat((role_onehot, clue_onehot, phase_onehot, n_field, expanded_latent), dim=-1)


class _Sparsemax(torch.autograd.Function):
    @staticmethod
    def forward(ctx, values: torch.Tensor, dim: int) -> torch.Tensor:
        dim = dim if dim >= 0 else values.ndim + dim
        if not 0 <= dim < values.ndim:
            raise IndexError("sparsemax dimension out of range")
        shifted = values - values.max(dim=dim, keepdim=True).values
        ordered = shifted.sort(dim=dim, descending=True).values
        ranks_shape = [1] * values.ndim
        ranks_shape[dim] = values.shape[dim]
        ranks = torch.arange(1, values.shape[dim] + 1, device=values.device, dtype=values.dtype).reshape(ranks_shape)
        support = 1 + ranks * ordered > ordered.cumsum(dim=dim)
        support_size = support.sum(dim=dim, keepdim=True)
        tau_sum = ordered.cumsum(dim=dim).gather(dim, support_size - 1)
        tau = (tau_sum - 1) / support_size.to(values.dtype)
        output = torch.clamp(shifted - tau, min=0)
        ctx.dim = dim
        ctx.save_for_backward(output)
        return output

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> tuple[torch.Tensor, None]:
        (output,) = ctx.saved_tensors
        active = output > 0
        active_count = active.sum(dim=ctx.dim, keepdim=True).clamp_min(1)
        active_grad = torch.where(active, grad_output, torch.zeros_like(grad_output))
        active_mean = active_grad.sum(dim=ctx.dim, keepdim=True) / active_count.to(grad_output.dtype)
        # The registered boundary convention is exactly zero on output-zero
        # coordinates, including ties that land on the inactive side.
        return torch.where(active, grad_output - active_mean, torch.zeros_like(grad_output)), None


def sparsemax(values: torch.Tensor, dim: int = -1) -> torch.Tensor:
    return _Sparsemax.apply(values, dim)


def _xavier_fill(permit: ProductionPermit, seed: int, name: str, tensor: torch.Tensor) -> None:
    require_active_permit(permit)
    fan_out, fan_in = int(tensor.shape[0]), int(tensor.shape[1])
    bound = math.sqrt(6.0 / float(fan_in + fan_out))
    values = generator(permit, seed, "initialization", name).uniform(-bound, bound, size=tuple(tensor.shape))
    require_active_permit(permit)
    tensor.copy_(torch.from_numpy(values).to(torch.float64))


def initialized_model(permit: ProductionPermit, seed: int) -> ArmModel:
    require_active_permit(permit)
    model = ArmModel()
    with torch.no_grad():
        for module_name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                _xavier_fill(permit, seed, f"{module_name}.weight", module.weight)
                module.bias.zero_()
        bound = 1.0 / math.sqrt(REGISTERED.latent_dim)
        values = generator(permit, seed, "initialization", "macro_base").uniform(
            -bound, bound, size=tuple(model.macro_base.shape),
        )
        require_active_permit(permit)
        model.macro_base.copy_(torch.from_numpy(values).to(torch.float64))
        model.residual.zero_()
    if sum(parameter.numel() for parameter in model.manager.parameters()) != REGISTERED.manager_parameters:
        raise RuntimeError("manager parameter count mismatch")
    if model.macro_base.numel() + model.residual.numel() != REGISTERED.embedding_parameters:
        raise RuntimeError("embedding parameter count mismatch")
    if sum(parameter.numel() for parameter in model.actor.parameters()) != REGISTERED.actor_parameters:
        raise RuntimeError("actor parameter count mismatch")
    if sum(parameter.numel() for parameter in model.parameters()) != REGISTERED.parameters_per_arm:
        raise RuntimeError("complete parameter count mismatch")
    return model


def paired_models(permit: ProductionPermit, seed: int) -> dict[str, ArmModel]:
    require_active_permit(permit)
    reference = initialized_model(permit, seed)
    require_active_permit(permit)
    models = {arm: ArmModel() for arm in ARMS}
    for model in models.values():
        model.load_state_dict(reference.state_dict())
    require_active_permit(permit)
    return models


def inverse_cdf(
    permit: ProductionPermit,
    probabilities: torch.Tensor,
    uniforms: np.ndarray,
) -> torch.Tensor:
    require_active_permit(permit)
    u = torch.from_numpy(np.asarray(uniforms, dtype=np.float64)).to(probabilities.device)
    indices = (u[..., None] >= probabilities.cumsum(dim=-1)).sum(dim=-1)
    return indices.clamp_max(probabilities.shape[-1] - 1).to(torch.int64)
