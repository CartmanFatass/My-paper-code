from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from .authorization import ProductionPermit, require_active_permit
from .config import ALT_GRAPHON, ARM_CENTERS, ARMS, GRAPHON, REGISTERED, RESIDUAL_SCALES
from .rng import initialization_uniform


@dataclass(frozen=True)
class PolicyOutput:
    logits: torch.Tensor
    probabilities: torch.Tensor
    messages: torch.Tensor
    weighted_mass_by_role: torch.Tensor
    numerator_by_role: torch.Tensor
    normalized_summary_by_role: torch.Tensor
    declared_center: tuple[tuple[float, float], tuple[float, float]] | None


class SharedSGSPPolicy(nn.Module):
    """One shared implicit O(N) policy with no identity, row-position, or N input."""

    def __init__(self, arm: str) -> None:
        super().__init__()
        if arm not in ARMS:
            raise ValueError(f"unknown arm: {arm}")
        self.arm = arm
        self.encoder_A = nn.Parameter(torch.zeros((32, 1), dtype=torch.float64))
        self.encoder_bias = nn.Parameter(torch.zeros(32, dtype=torch.float64))
        if arm != "ANON-MEAN":
            self.gamma = nn.Parameter(torch.zeros((2, 2), dtype=torch.float64))
        else:
            self.register_parameter("gamma", None)
        self.actor_hidden_weight = nn.Parameter(torch.zeros((32, 36), dtype=torch.float64))
        self.actor_hidden_bias = nn.Parameter(torch.zeros(32, dtype=torch.float64))
        self.actor_head_weight = nn.Parameter(torch.zeros((2, 32), dtype=torch.float64))
        self.actor_head_bias = nn.Parameter(torch.zeros(2, dtype=torch.float64))

    def encode(self, sender_messages: torch.Tensor) -> torch.Tensor:
        if sender_messages.ndim != 1:
            raise ValueError("sender_messages must have shape [N]")
        nonlinear = torch.tanh(
            sender_messages[:, None] * self.encoder_A[:, 0] + self.encoder_bias
        )
        return torch.cat((sender_messages[:, None], nonlinear), dim=1)

    def _aggregate(
        self,
        encoded: torch.Tensor,
        sender_roles: torch.Tensor,
        declared_center: tuple[tuple[float, float], tuple[float, float]] | None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        n = int(encoded.shape[0])
        if encoded.shape != (n, 33) or sender_roles.shape != (n,):
            raise ValueError("aggregate expects encoded [N,33] and sender roles [N]")
        if self.arm == "ANON-MEAN":
            mean = encoded.sum(dim=0) / float(n)
            normalized = mean.expand(2, -1)
            mass = torch.ones(2, dtype=encoded.dtype, device=encoded.device)
            return mass, normalized.clone(), normalized
        if declared_center not in (GRAPHON, ALT_GRAPHON):
            raise ValueError("edge-aware aggregation requires a registered declared center")

        role_masks = tuple(sender_roles == sender for sender in (0, 1))
        block_sums = torch.stack([
            encoded[role_masks[sender]].sum(dim=0) / float(n)
            for sender in (0, 1)
        ])
        block_mass = torch.stack([
            role_masks[sender].to(encoded.dtype).sum() / float(n)
            for sender in (0, 1)
        ])
        center = torch.as_tensor(declared_center, dtype=encoded.dtype, device=encoded.device)
        residual = RESIDUAL_SCALES[self.arm] * torch.tanh(self.gamma)
        omega = center * torch.exp(residual)
        numerator = omega @ block_sums
        weighted_mass = omega @ block_mass
        normalized = numerator / (weighted_mass[:, None] + REGISTERED.summary_epsilon)
        return weighted_mass, numerator, normalized

    def forward(
        self,
        sender_messages: torch.Tensor,
        receiver_roles: torch.Tensor,
        sender_roles_override: torch.Tensor | None = None,
        center_swap: bool = False,
    ) -> PolicyOutput:
        n = int(sender_messages.shape[0])
        if sender_messages.shape != (n,) or receiver_roles.shape != (n,):
            raise ValueError("policy accepts messages [N] and semantic receiver roles [N]")
        if center_swap and self.arm != "SGSP-W":
            raise ValueError("the registered anchor-only center swap applies only to SGSP-W")
        sender_roles = receiver_roles if sender_roles_override is None else sender_roles_override
        if sender_roles.shape != (n,):
            raise ValueError("sender role override must preserve agent shape")
        declared_center = None if self.arm == "ANON-MEAN" else ARM_CENTERS[self.arm]
        if center_swap:
            declared_center = ALT_GRAPHON

        encoded = self.encode(sender_messages)
        d_by_role, m_by_role, z_by_role = self._aggregate(
            encoded, sender_roles, declared_center,
        )
        z = z_by_role[receiver_roles]
        d = d_by_role[receiver_roles, None]
        receiver_onehot = torch.nn.functional.one_hot(receiver_roles, num_classes=2).to(
            sender_messages.dtype
        )
        actor_input = torch.cat((z, d, receiver_onehot), dim=1)
        hidden = torch.tanh(actor_input @ self.actor_hidden_weight.T + self.actor_hidden_bias)
        logits = hidden @ self.actor_head_weight.T + self.actor_head_bias
        probabilities = (
            REGISTERED.support_softmax_mass * torch.softmax(logits, dim=1)
            + REGISTERED.support_floor
        )
        return PolicyOutput(
            logits, probabilities, encoded, d_by_role, m_by_role, z_by_role, declared_center,
        )

    @staticmethod
    def output_relevant_work(n: int, regime: str, panel: str = "intact") -> dict[str, int | str]:
        if n not in (6, 8, 12, 16) or regime not in ("SAME", "OPPOSED"):
            raise ValueError("work replay requires a registered valid tuple")
        if panel not in ("intact", "identity", "sender_reassociation", "center_swap"):
            raise ValueError("unknown registered panel")
        return {
            "n": n,
            "regime": regime,
            "panel": panel,
            "sender_scalars": n,
            "public_role_coordinates": n,
            "encoder_calls": n,
            "role_pair_exponentials": 4,
            "receiver_role_block_reductions": 2,
            "actor_calls": n,
            "legal_action_probabilities": 2 * n,
            "scalar_multiplications": {
                "encoder": 32 * n,
                "edge_residual_and_anchor": 8,
                "numerator_and_mass": 136,
                "actor_hidden": 1152 * n,
                "actor_head": 64 * n,
                "support_mix": 2 * n,
            },
            "scalar_additions": {
                "encoder_bias": 32 * n,
                "block_message_sums": 33 * (n - 2),
                "block_count_sums": 2 * (n - 1),
                "numerator_and_mass": 68,
                "summary_epsilon": 2,
                "actor_hidden_including_bias": 1152 * n,
                "actor_head_including_bias": 64 * n,
                "softmax_shift_sum_and_floor": 5 * n,
            },
            "scalar_comparisons": {
                "sender_role_membership": 2 * n,
                "binary_softmax_max": n,
            },
            "scalar_tanh": 64 * n + 4,
            "scalar_exp": 2 * n + 4,
            "scalar_divisions": 134 + 2 * n,
            "reduction_invocations": {
                "block_message": 66,
                "block_count": 2,
                "actor_dot_products": 34 * n,
                "softmax_sum": n,
            },
            "learned_nxn_objects": 0,
            "aggregation_time_class": "O(2N)",
            "input_storage_class": "O(N)",
            "edge_table_storage": 4,
        }


def _glorot_matrix(
    permit: ProductionPermit, seed: int, layer: str, rows: int, columns: int,
) -> torch.Tensor:
    require_active_permit(permit)
    limit = float(np.sqrt(6.0 / float(columns + rows)))
    values = np.asarray([
        limit * (2.0 * initialization_uniform(permit, seed, layer, row, column) - 1.0)
        for row in range(rows) for column in range(columns)
    ], dtype=np.float64).reshape(rows, columns)
    return torch.from_numpy(values.copy())


def paired_policy_set(
    permit: ProductionPermit, seed: int,
) -> dict[str, SharedSGSPPolicy]:
    """Materializes the first registered stochastic object for one seed."""
    common = {
        "encoder_A": _glorot_matrix(permit, seed, "encoder_A", 32, 1),
        "actor_hidden_weight": _glorot_matrix(
            permit, seed, "actor_hidden_weight", 32, 36,
        ),
        "actor_head_weight": _glorot_matrix(permit, seed, "actor_head_weight", 2, 32),
    }
    models = {arm: SharedSGSPPolicy(arm) for arm in ARMS}
    with torch.no_grad():
        for model in models.values():
            model.encoder_A.copy_(common["encoder_A"])
            model.actor_hidden_weight.copy_(common["actor_hidden_weight"])
            model.actor_head_weight.copy_(common["actor_head_weight"])
            model.encoder_bias.zero_()
            model.actor_hidden_bias.zero_()
            model.actor_head_bias.zero_()
            if model.gamma is not None:
                model.gamma.zero_()
    return models


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def common_tensors_bitwise_equal(models: dict[str, SharedSGSPPolicy]) -> bool:
    names = (
        "encoder_A", "encoder_bias", "actor_hidden_weight", "actor_hidden_bias",
        "actor_head_weight", "actor_head_bias",
    )
    anchor = models["SGSP-W"]
    return all(
        torch.equal(getattr(anchor, name), getattr(models[arm], name))
        for name in names for arm in ("ALT-CENTER", "EDGE-PE", "ANON-MEAN")
    )


def actions_from_uniforms(probabilities: torch.Tensor, uniforms: torch.Tensor) -> torch.Tensor:
    if probabilities.shape != (uniforms.numel(), 2):
        raise ValueError("one paired action uniform is required per agent")
    return (uniforms < probabilities[:, 1]).to(torch.int64)
