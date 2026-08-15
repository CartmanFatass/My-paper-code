from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.distributions import Bernoulli, Normal


@dataclass
class PolicyOutput:
    mu: torch.Tensor
    value: torch.Tensor
    lease_probabilities: torch.Tensor
    learned_object_shape_guard: bool
    peak_n_dependent_tensor_words: int


class SetBidActorCritic(nn.Module):
    """Exact v6 fixed-three-task task-to-agent set actor and centralized critic."""

    def __init__(self) -> None:
        super().__init__()
        self.agent_encoder = nn.Sequential(nn.Linear(9, 64), nn.SiLU(), nn.Linear(64, 64), nn.SiLU())
        self.task_encoder = nn.Sequential(nn.Linear(4, 64), nn.SiLU(), nn.Linear(64, 64), nn.SiLU())
        self.task_attention = nn.MultiheadAttention(64, 4, batch_first=True)
        # h_i,g_r,S,M,A_r,g_event,rho,ell_i,leased_load = 330.
        self.bid_head = nn.Sequential(nn.Linear(330, 64), nn.SiLU(), nn.Linear(64, 1))
        # stopgrad h_i,S,M,g_(p_i),A_(p_i),g_event,rho = 326.
        self.lease_head = nn.Sequential(nn.Linear(326, 32), nn.SiLU(), nn.Linear(32, 1))
        # S,M,sum(g),mean(g),g_event,rho = 262.
        self.critic = nn.Sequential(nn.Linear(262, 64), nn.SiLU(), nn.Linear(64, 1))
        self._reset_registered_parameters()

    def _reset_registered_parameters(self) -> None:
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.zeros_(module.bias)
        nn.init.xavier_uniform_(self.task_attention.in_proj_weight)
        nn.init.zeros_(self.task_attention.in_proj_bias)
        nn.init.xavier_uniform_(self.task_attention.out_proj.weight)
        nn.init.zeros_(self.task_attention.out_proj.bias)

    def forward(
        self, agent_rows: torch.Tensor, task_rows: torch.Tensor, global_row: torch.Tensor,
        rho: torch.Tensor | None = None, lease_vector: torch.Tensor | None = None,
    ) -> PolicyOutput:
        if agent_rows.ndim != 2 or agent_rows.shape[1] != 9 or task_rows.shape != (3, 4):
            raise ValueError("model expects agent [N,9] and task [3,4]")
        n = int(agent_rows.shape[0])
        rho = torch.zeros(3, dtype=agent_rows.dtype, device=agent_rows.device) if rho is None else rho
        lease_vector = torch.zeros(n, dtype=agent_rows.dtype, device=agent_rows.device) if lease_vector is None else lease_vector
        if global_row.shape != (3,) or rho.shape != (3,) or lease_vector.shape != (n,):
            raise ValueError("global/rho/lease shapes violate the registered actor contract")

        h = self.agent_encoder(agent_rows)
        g = self.task_encoder(task_rows)
        attended, per_head_weights = self.task_attention(
            g.unsqueeze(0), h.unsqueeze(0), h.unsqueeze(0),
            need_weights=True, average_attn_weights=False,
        )
        if tuple(per_head_weights.shape) != (1, 4, 3, n):
            raise RuntimeError("learned attention violated registered [4,3,N] shape")
        attended = attended.squeeze(0)
        summed = h.sum(dim=0)
        mean = h.mean(dim=0)

        previous = agent_rows[:, 3:7]
        previous_real = previous[:, :3]
        g_previous = previous_real @ g
        a_previous = previous_real @ attended
        lease_features = torch.cat((
            h.detach(), summed.detach().expand(n, -1), mean.detach().expand(n, -1),
            g_previous.detach(), a_previous.detach(), global_row.expand(n, -1), rho.expand(n, -1),
        ), dim=-1)
        lease_probabilities = torch.sigmoid(self.lease_head(lease_features).squeeze(-1))

        capacities = agent_rows[:, :3]
        task_demand = task_rows[:, 3]
        leased_load = (lease_vector[:, None] * previous_real * capacities).sum(dim=0) / task_demand
        bid_features = torch.cat((
            h[:, None, :].expand(n, 3, 64),
            g[None, :, :].expand(n, 3, 64),
            summed[None, None, :].expand(n, 3, 64),
            mean[None, None, :].expand(n, 3, 64),
            attended[None, :, :].expand(n, 3, 64),
            global_row[None, None, :].expand(n, 3, 3),
            rho[None, None, :].expand(n, 3, 3),
            lease_vector[:, None, None].expand(n, 3, 1),
            leased_load[None, None, :].expand(n, 3, 3),
        ), dim=-1)
        mu = self.bid_head(bid_features).squeeze(-1)
        critic_features = torch.cat((summed, mean, g.sum(0), g.mean(0), global_row, rho), dim=-1)
        value = self.critic(critic_features).squeeze(-1)

        # Conservative peak simultaneous float32 census of all N-dependent tensors
        # in the largest (bid-head) phase. Convert bytes to 8-byte machine words.
        peak_float_elements = n * (9 + 64 + 12 + 990 + 3 + 1) + 3 * n
        peak_words = (peak_float_elements * agent_rows.element_size() + 7) // 8
        return PolicyOutput(mu, value, lease_probabilities, False, int(peak_words))

    @staticmethod
    def sample_release_latent(
        output: PolicyOutput, sigma: float, generator: torch.Generator,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        noise = torch.randn(output.mu.shape, generator=generator, dtype=output.mu.dtype, device=output.mu.device)
        latent = output.mu + sigma * noise
        distribution = Normal(output.mu, sigma)
        log_probability = distribution.log_prob(latent).sum()
        entropy = distribution.entropy().mean() if latent.numel() else torch.zeros((), dtype=output.mu.dtype)
        return latent, log_probability, entropy

    @staticmethod
    def joint_log_probability_release(output: PolicyOutput, latent: torch.Tensor, sigma: float) -> torch.Tensor:
        return Normal(output.mu, sigma).log_prob(latent).sum()

    @staticmethod
    def adaptive_joint_log_probability(
        output: PolicyOutput, eligible: torch.Tensor, leases: torch.Tensor,
        edge_mask: torch.Tensor, latent: torch.Tensor, sigma: float,
    ) -> torch.Tensor:
        lease_logp = Bernoulli(output.lease_probabilities[eligible]).log_prob(leases[eligible]).sum()
        bid_logp = Normal(output.mu[edge_mask], sigma).log_prob(latent[edge_mask]).sum()
        return lease_logp + bid_logp

    @staticmethod
    def deterministic_bids(output: PolicyOutput) -> torch.Tensor:
        return torch.tanh(output.mu)

    @staticmethod
    def learned_forward_counts(n: int) -> dict[str, int]:
        return {
            "agent_rows": n, "task_rows": 3, "task_agent_attention_scores": 12 * n,
            "bid_latents": 3 * n, "lease_logits_computed": n, "active_lease_logits": 0,
            "agent_agent_scores": 0, "nxn_tensors": 0,
        }


def parameter_counts(model: nn.Module) -> dict[str, int]:
    return {
        "total": sum(p.numel() for p in model.parameters()),
        "trainable": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "lease_head": sum(p.numel() for p in model.lease_head.parameters()),  # type: ignore[attr-defined]
    }


def pressure_vector(capacities: torch.Tensor, demand: torch.Tensor) -> torch.Tensor:
    """Exact epsilon-free registered pressure; positive support is caller-validated."""
    totals = capacities.sum(dim=0)
    if bool(torch.any(totals <= 0)) or bool(torch.any(demand <= 0)):
        raise ValueError("pressure requires strictly positive demand and capacity sums")
    return torch.log(demand / totals)


def deterministic_adaptive_leases(
    probabilities: torch.Tensor, previous_role_onehot: torch.Tensor,
) -> torch.Tensor:
    """Evaluation tie at 0.5 retains; only real-role survivors are eligible."""
    eligible = previous_role_onehot[:, :3].sum(dim=1) > 0
    return torch.logical_and(eligible, probabilities >= 0.5).to(probabilities.dtype)


def structural_edge_mask(
    capacities: torch.Tensor, demand: torch.Tensor, previous_role_onehot: torch.Tensor,
    leases: torch.Tensor,
) -> torch.Tensor:
    """Outcome-independent lease-first structural mask E(o,ell)."""
    leased_mass = (leases[:, None] * previous_role_onehot[:, :3] * capacities).sum(dim=0)
    delta0 = torch.clamp(demand - leased_mass, min=0)
    free = leases < 0.5
    return free[:, None] & (capacities > 0) & (delta0[None, :] > 0)
