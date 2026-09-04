"""Equal-capacity recurrent actor/critic modules for VNFC-B2."""

from __future__ import annotations

from dataclasses import dataclass

import torch


# Local public fields, cue fields, four reserved capsule fields, and the
# chronological primitive lifecycle relation fields.  No opaque identifier is
# represented in these rows.
ROW_WIDTH = 2 + 1 + 2 + 1 + 1 + 4 + 4 + 12
ACTION_COUNT = 5


@dataclass
class PolicyOutput:
    logits: torch.Tensor
    actor_hidden: torch.Tensor
    value: torch.Tensor
    critic_hidden: torch.Tensor


class RecurrentSetActorCritic(torch.nn.Module):
    """Parameter-shared local actor with masked DeepSets summaries."""

    def __init__(self) -> None:
        super().__init__()
        self.row_encoder = torch.nn.Sequential(
            torch.nn.Linear(ROW_WIDTH, 64), torch.nn.SiLU(),
            torch.nn.Linear(64, 64), torch.nn.SiLU(),
        )
        self.actor_gru = torch.nn.GRUCell(64 * 3, 64)
        self.actor_head = torch.nn.Linear(64, ACTION_COUNT)
        self.critic_gru = torch.nn.GRUCell(64 * 2 + 1, 64)
        self.critic_head = torch.nn.Linear(64, 1)

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def step(
        self, rows: torch.Tensor, actor_hidden: torch.Tensor,
        critic_hidden: torch.Tensor,
    ) -> PolicyOutput:
        if rows.ndim != 2 or rows.shape[1] != ROW_WIDTH:
            raise ValueError(f"policy rows must have shape [N,{ROW_WIDTH}]")
        encoded = self.row_encoder(rows)
        mean = encoded.mean(dim=0)
        total = encoded.sum(dim=0)
        actor_input = torch.cat((
            encoded,
            mean.unsqueeze(0).expand(rows.shape[0], -1),
            total.unsqueeze(0).expand(rows.shape[0], -1),
        ), dim=-1)
        next_actor = self.actor_gru(actor_input, actor_hidden)
        logits = self.actor_head(next_actor)
        critic_input = torch.cat((mean, total, torch.tensor([rows.shape[0] / 5.0])))
        next_critic = self.critic_gru(critic_input.unsqueeze(0), critic_hidden.unsqueeze(0)).squeeze(0)
        value = self.critic_head(next_critic).squeeze(0)
        return PolicyOutput(logits, next_actor, value, next_critic)


def initialize_model(base_seed: int, arm: str, seed_fn) -> RecurrentSetActorCritic:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed_fn(base_seed, arm, "model_initialization"))
        return RecurrentSetActorCritic()
