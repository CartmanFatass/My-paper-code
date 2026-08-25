"""Shared set actor-critic and exact action decoders for VNFC-B1."""

from __future__ import annotations

from dataclasses import dataclass
import itertools
from typing import Mapping, Sequence

import numpy as np
import torch
from torch import nn

from .host import (
    DROP, EVENT_KINDS, JOIN, RESET, ROLE_COUNT, TASK_COUNT, World,
    allocation_metrics,
)


G_MEAN = "G-MEAN"
A_MASS = "A-MASS"
A_JOINT = "A-JOINT"
B_REBIND = "B-REBIND"
GREEDY_ORACLE = "GREEDY-ORACLE"
LEARNED_ARMS = (G_MEAN, A_MASS, A_JOINT, B_REBIND)
JOINT_ARMS = (A_JOINT, B_REBIND)


@dataclass
class Observation:
    handles: tuple[int, ...]
    agent_features: torch.Tensor
    task_features: torch.Tensor
    demands: torch.Tensor
    capacities: torch.Tensor
    segment: int
    event_kind: str
    previous: dict[int, int]

    @property
    def n(self) -> int:
        return len(self.handles)


def make_observation(
    world: World,
    segment: int,
    ordered_handles: Sequence[int],
    previous: Mapping[int, int] | None,
) -> Observation:
    roster = tuple(ordered_handles)
    capacities_by_handle = world.capacities(segment)
    prior = dict(previous or {})
    rows: list[list[float]] = []
    before = set(world.rosters[segment - 1]) if segment > 0 else set()
    for handle in roster:
        prev_one_hot = [0.0] * ROLE_COUNT
        if handle in prior:
            prev_one_hot[prior[handle]] = 1.0
        survived = float(segment > 0 and handle in before)
        newly_joined = float(segment > 0 and handle not in before)
        rows.append([
            *[float(value) for value in capacities_by_handle[handle]],
            *prev_one_hot,
            survived,
            newly_joined,
        ])
    task_rows = [
        [
            *[1.0 if task == index else 0.0 for index in range(TASK_COUNT)],
            float(world.demands[task]),
        ]
        for task in range(TASK_COUNT)
    ]
    return Observation(
        handles=roster,
        agent_features=torch.tensor(rows, dtype=torch.float32),
        task_features=torch.tensor(task_rows, dtype=torch.float32),
        demands=torch.tensor(world.demands, dtype=torch.float32),
        capacities=torch.stack([
            torch.as_tensor(capacities_by_handle[handle], dtype=torch.float32)
            for handle in roster
        ]),
        segment=segment,
        event_kind=world.event_kind(segment),
        previous=prior,
    )


class SetActorCritic(nn.Module):
    """Identical-width actor-critic used by all four learned arms."""

    COMMON_WIDTH = 237
    BID_INPUT_WIDTH = 64 + 32 + COMMON_WIDTH

    def __init__(self, arm: str) -> None:
        super().__init__()
        if arm not in LEARNED_ARMS:
            raise ValueError(arm)
        self.arm = arm
        self.agent_encoder = nn.Sequential(
            nn.Linear(9, 64), nn.SiLU(), nn.Linear(64, 64), nn.SiLU(),
        )
        self.task_encoder = nn.Sequential(
            nn.Linear(4, 32), nn.SiLU(), nn.Linear(32, 32), nn.SiLU(),
        )
        self.dummy_embedding = nn.Parameter(torch.zeros(32))
        self.bid_mlp = nn.Sequential(
            nn.Linear(self.BID_INPUT_WIDTH, 64), nn.SiLU(),
            nn.Linear(64, 64), nn.SiLU(), nn.Linear(64, 1),
        )
        self.critic = nn.Sequential(
            nn.Linear(self.COMMON_WIDTH, 64), nn.SiLU(),
            nn.Linear(64, 64), nn.SiLU(), nn.Linear(64, 1),
        )

    @property
    def parameter_count(self) -> int:
        return sum(parameter.numel() for parameter in self.parameters())

    def _context(self, observation: Observation) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        agent_embeddings = self.agent_encoder(observation.agent_features)
        task_embeddings = self.task_encoder(observation.task_features)
        mean_embedding = agent_embeddings.mean(dim=0)
        sum_embedding = agent_embeddings.sum(dim=0)
        segment = torch.nn.functional.one_hot(
            torch.tensor(observation.segment), num_classes=3
        ).to(dtype=torch.float32)
        event_index = {RESET: 0, JOIN: 1, DROP: 2}.get(observation.event_kind, 0)
        event = torch.nn.functional.one_hot(torch.tensor(event_index), num_classes=3).to(torch.float32)
        base = torch.cat((
            mean_embedding,
            task_embeddings.flatten(),
            observation.demands,
            segment,
            event,
            torch.tensor([observation.n / 7.0], dtype=torch.float32),
        ))
        pressure = torch.log(
            (observation.demands + 1e-6) /
            (observation.capacities.sum(dim=0) + 1e-6)
        )
        if self.arm == G_MEAN:
            reserved = torch.zeros(67, dtype=torch.float32)
        else:
            reserved = torch.cat((sum_embedding, pressure))
        context = torch.cat((base, reserved))
        if context.numel() != self.COMMON_WIDTH:
            raise RuntimeError(f"context width {context.numel()} != {self.COMMON_WIDTH}")
        return agent_embeddings, task_embeddings, context

    def forward(self, observation: Observation) -> tuple[torch.Tensor, torch.Tensor]:
        agent_embeddings, task_embeddings, context = self._context(observation)
        role_embeddings = torch.cat((task_embeddings, self.dummy_embedding.unsqueeze(0)), dim=0)
        n = observation.n
        agent_expanded = agent_embeddings[:, None, :].expand(n, ROLE_COUNT, 64)
        role_expanded = role_embeddings[None, :, :].expand(n, ROLE_COUNT, 32)
        context_expanded = context[None, None, :].expand(n, ROLE_COUNT, self.COMMON_WIDTH)
        bid_input = torch.cat((agent_expanded, role_expanded, context_expanded), dim=-1)
        logits = self.bid_mlp(bid_input).squeeze(-1)
        value = self.critic(context).squeeze(-1)
        return logits, value


_ASSIGNMENT_CACHE: dict[int, torch.Tensor] = {}


def assignments_for_n(n: int) -> torch.Tensor:
    cached = _ASSIGNMENT_CACHE.get(n)
    if cached is None:
        cached = torch.tensor(list(itertools.product(range(ROLE_COUNT), repeat=n)), dtype=torch.long)
        _ASSIGNMENT_CACHE[n] = cached
    return cached


def coverage_scores(observation: Observation, assignments: torch.Tensor) -> torch.Tensor:
    n_assignments = assignments.shape[0]
    ratios = observation.capacities / observation.demands[None, :]
    x = torch.zeros((n_assignments, TASK_COUNT), dtype=torch.float32)
    for task in range(TASK_COUNT):
        mask = (assignments == task).to(torch.float32)
        x[:, task] = (mask * ratios[:, task][None, :]).sum(dim=1)
    service = torch.minimum(x, torch.ones_like(x))
    waste = torch.minimum(torch.clamp(x - 1.0, min=0.0), torch.ones_like(x))
    return service.mean(dim=1) - 0.10 * waste.mean(dim=1)


def keep_scores(observation: Observation, assignments: torch.Tensor) -> torch.Tensor:
    survivors = [index for index, handle in enumerate(observation.handles) if handle in observation.previous]
    if not survivors:
        return torch.zeros(assignments.shape[0], dtype=torch.float32)
    retained = torch.zeros(assignments.shape[0], dtype=torch.float32)
    for index in survivors:
        retained += (assignments[:, index] == observation.previous[observation.handles[index]]).to(torch.float32)
    return retained / len(survivors)


def joint_scores(arm: str, observation: Observation, logits: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    assignments = assignments_for_n(observation.n)
    rows = torch.arange(observation.n)
    bid = logits[rows[None, :], assignments].sum(dim=1) / observation.n
    score = bid + coverage_scores(observation, assignments)
    if arm == B_REBIND and observation.segment > 0:
        score = score + 0.04 * keep_scores(observation, assignments)
    return assignments, score


def action_logprob_entropy(
    arm: str, observation: Observation, logits: torch.Tensor, action: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    if arm in (G_MEAN, A_MASS):
        distribution = torch.distributions.Categorical(logits=logits)
        return distribution.log_prob(action).sum(), distribution.entropy().sum()
    assignments, scores = joint_scores(arm, observation, logits)
    matches = torch.all(assignments == action[None, :], dim=1)
    index = int(torch.nonzero(matches, as_tuple=False)[0, 0])
    distribution = torch.distributions.Categorical(logits=scores)
    return distribution.log_prob(torch.tensor(index)), distribution.entropy()


def sample_action(
    arm: str, observation: Observation, logits: torch.Tensor, generator: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    if arm in (G_MEAN, A_MASS):
        probabilities = torch.softmax(logits, dim=-1)
        action = torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
    else:
        assignments, scores = joint_scores(arm, observation, logits)
        index = int(torch.multinomial(torch.softmax(scores, dim=0), 1, generator=generator)[0])
        action = assignments[index]
    logprob, entropy = action_logprob_entropy(arm, observation, logits, action)
    return action, logprob, entropy


def greedy_action(
    arm: str, observation: Observation, logits: torch.Tensor,
) -> tuple[dict[int, int], float, list[list[float]]]:
    """Greedy physical assignment with stable-handle tie order."""
    stable_indices = sorted(range(observation.n), key=lambda index: observation.handles[index])
    stable_handles = tuple(observation.handles[index] for index in stable_indices)
    stable_logits = logits[stable_indices]
    stable_observation = Observation(
        handles=stable_handles,
        agent_features=observation.agent_features[stable_indices],
        task_features=observation.task_features,
        demands=observation.demands,
        capacities=observation.capacities[stable_indices],
        segment=observation.segment,
        event_kind=observation.event_kind,
        previous=observation.previous,
    )
    if arm in (G_MEAN, A_MASS):
        stable_action = torch.argmax(stable_logits, dim=-1)
        selected_probability = float(
            torch.softmax(stable_logits, dim=-1)[torch.arange(observation.n), stable_action].prod()
        )
        probabilities = torch.softmax(stable_logits, dim=-1).detach().cpu().tolist()
    else:
        assignments, scores = joint_scores(arm, stable_observation, stable_logits)
        selected = int(torch.argmax(scores))
        stable_action = assignments[selected]
        selected_probability = float(torch.softmax(scores, dim=0)[selected])
        # Marginals are the permutation-comparison probability observable.
        weights = torch.softmax(scores, dim=0)
        probabilities = [
            [float(weights[assignments[:, agent] == role].sum()) for role in range(ROLE_COUNT)]
            for agent in range(observation.n)
        ]
    allocation = {handle: int(stable_action[index]) for index, handle in enumerate(stable_handles)}
    return allocation, selected_probability, probabilities


def assignment_tensor(observation: Observation, allocation: Mapping[int, int]) -> torch.Tensor:
    return torch.tensor([allocation[handle] for handle in observation.handles], dtype=torch.long)


def exact_best_response(
    world: World, segment: int, previous: Mapping[int, int] | None,
) -> tuple[dict[int, int], dict[str, object]]:
    roster = tuple(sorted(world.rosters[segment]))
    capacities = world.capacities(segment)
    observation = make_observation(world, segment, roster, previous)
    assignments = assignments_for_n(len(roster))
    scores = coverage_scores(observation, assignments)
    prior = dict(previous or {})
    survivors = [index for index, handle in enumerate(roster) if handle in prior]
    if survivors:
        switches = torch.zeros(assignments.shape[0], dtype=torch.float32)
        for index in survivors:
            switches += (assignments[:, index] != prior[roster[index]]).to(torch.float32)
        scores = scores - 0.04 * switches / len(survivors)
    selected = int(torch.argmax(scores))
    roles = assignments[selected].tolist()
    allocation = dict(zip(roster, (int(role) for role in roles)))
    metrics = allocation_metrics(roster, capacities, world.demands, allocation, prior)
    return allocation, metrics
