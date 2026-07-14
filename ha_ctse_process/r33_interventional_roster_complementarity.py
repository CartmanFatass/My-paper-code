"""R33 interventional roster-complementarity primitives.

R33 scores complete two-agent skill rosters from randomized fixed-window
branches.  The score removes all additive agent/skill main effects before the
role-swap contrast, so an independently executed pair of distinct skills is
not mislabeled as team complementarity.  The score is detached and updates
only the R30 conditional skill-selection head through an exactly enumerated
joint-roster expectation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Any, Mapping

import numpy as np
import torch

from ha_ctse_process.r30_fixed_clock import (
    INVALID_SKILL,
    KEEP_TOKEN,
    SET_TOKEN,
    FixedClockAREditPolicy,
)


ArrayOrTensor = np.ndarray | torch.Tensor


@dataclass(frozen=True)
class RosterInterventionContext:
    """One natural pre-check R30 context and its executable snapshot."""

    context_id: int
    reset_group: int
    observations: np.ndarray = field(repr=False, compare=False)
    state: np.ndarray = field(repr=False, compare=False)
    prev_skills: np.ndarray = field(repr=False, compare=False)
    prev_ages: np.ndarray = field(repr=False, compare=False)
    prev_active: np.ndarray = field(repr=False, compare=False)
    agent_order: np.ndarray = field(repr=False, compare=False)
    natural_token_kind: np.ndarray = field(repr=False, compare=False)
    natural_set_skill: np.ndarray = field(repr=False, compare=False)
    natural_old_token_logp: np.ndarray = field(repr=False, compare=False)
    env_snapshot: Any = field(repr=False, compare=False)
    policy_runtime: Mapping[str, np.ndarray] = field(repr=False, compare=False)
    team_code: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        if int(self.context_id) < 0 or int(self.reset_group) < 0:
            raise ValueError("context and reset identifiers must be non-negative")
        if np.asarray(self.observations).ndim != 2:
            raise ValueError("joint observations must have shape [agent, feature]")
        n_agents = int(np.asarray(self.observations).shape[0])
        for name in (
            "prev_skills",
            "prev_ages",
            "prev_active",
            "agent_order",
            "natural_token_kind",
            "natural_set_skill",
            "natural_old_token_logp",
        ):
            if np.asarray(getattr(self, name)).reshape(-1).shape[0] != n_agents:
                raise ValueError(f"{name} must contain one value per agent")


@dataclass(frozen=True)
class JointRosterBranch:
    """One forced complete-roster branch and stochastic replica."""

    context_id: int
    roster: np.ndarray = field(repr=False, compare=False)
    replica: int
    effect: np.ndarray = field(repr=False, compare=False)
    steps: int
    branch_seed: int

    def __post_init__(self) -> None:
        roster = np.asarray(self.roster)
        effect = np.asarray(self.effect)
        if int(self.context_id) < 0:
            raise ValueError("context_id must be non-negative")
        if int(self.replica) not in (0, 1):
            raise ValueError("R33 requires replicas 0 and 1")
        if roster.shape != (2,):
            raise ValueError("R33 roster must have shape [2]")
        if effect.shape != (2, 4):
            raise ValueError("R33 persistent effect must have shape [2,4]")
        if int(self.steps) <= 0:
            raise ValueError("branch length must be positive")
        if not np.all(np.isfinite(effect)):
            raise ValueError("branch effect must be finite")


def enumerate_final_rosters(
    n_skills: int = 4,
    n_agents: int = 2,
) -> np.ndarray:
    """Return the lexicographic exhaustive final-roster table."""

    if int(n_skills) <= 1 or int(n_agents) <= 0:
        raise ValueError("roster enumeration requires at least two skills")
    return np.asarray(
        list(product(range(int(n_skills)), repeat=int(n_agents))),
        dtype=np.int64,
    )


def final_roster_tokens(
    prev_skills: ArrayOrTensor,
    prev_active: ArrayOrTensor,
    final_roster: ArrayOrTensor,
    agent_order: ArrayOrTensor,
) -> tuple[np.ndarray, np.ndarray]:
    """Map one final roster to its unique R30 KEEP/SET token sequence."""

    previous = np.asarray(prev_skills, dtype=np.int64).reshape(-1)
    active = np.asarray(prev_active, dtype=np.bool_).reshape(-1)
    roster = np.asarray(final_roster, dtype=np.int64).reshape(-1)
    order = np.asarray(agent_order, dtype=np.int64).reshape(-1)
    if not (previous.shape == active.shape == roster.shape == order.shape):
        raise ValueError("R30 roster/token arrays must share the agent dimension")
    if sorted(order.tolist()) != list(range(order.size)):
        raise ValueError("agent_order must be a permutation")
    token_kind = np.empty(order.size, dtype=np.int64)
    set_skill = np.full(order.size, INVALID_SKILL, dtype=np.int64)
    for position, agent_id in enumerate(order):
        agent_id = int(agent_id)
        if bool(active[agent_id]) and int(roster[agent_id]) == int(previous[agent_id]):
            token_kind[position] = KEEP_TOKEN
        else:
            token_kind[position] = SET_TOKEN
            set_skill[position] = int(roster[agent_id])
    return token_kind, set_skill


def agent_persistent_effect(effect_views: ArrayOrTensor) -> ArrayOrTensor:
    """Return endpoint and late-half displacement for every agent.

    Input shape is [W+1, agent, 2].  Output shape is [agent, 4].
    """

    if effect_views.ndim != 3 or int(effect_views.shape[-1]) != 2:
        raise ValueError("position views must have shape [W+1, agent, 2]")
    window = int(effect_views.shape[0]) - 1
    if window <= 1 or window % 2:
        raise ValueError("R33 requires a positive even window")
    if isinstance(effect_views, torch.Tensor):
        start = effect_views[0]
        endpoint = effect_views[-1] - start
        late = (effect_views[window // 2 + 1 :] - start).mean(dim=0)
        result = torch.cat([endpoint, late], dim=-1)
        if not bool(torch.isfinite(result).all().item()):
            raise ValueError("persistent effects must be finite")
        return result
    views = np.asarray(effect_views)
    start = views[0]
    endpoint = views[-1] - start
    late = np.mean(views[window // 2 + 1 :] - start, axis=0)
    result = np.concatenate([endpoint, late], axis=-1)
    if not np.all(np.isfinite(result)):
        raise ValueError("persistent effects must be finite")
    return result


def _two_way_interaction_residual(roster_effects: ArrayOrTensor) -> ArrayOrTensor:
    """Remove both roster-axis additive main effects per replica/agent."""

    if isinstance(roster_effects, torch.Tensor):
        row = roster_effects.mean(dim=1, keepdim=True)
        column = roster_effects.mean(dim=0, keepdim=True)
        grand = roster_effects.mean(dim=(0, 1), keepdim=True)
        return roster_effects - row - column + grand
    values = np.asarray(roster_effects)
    row = values.mean(axis=1, keepdims=True)
    column = values.mean(axis=0, keepdims=True)
    grand = values.mean(axis=(0, 1), keepdims=True)
    return values - row - column + grand


def role_swap_complementarity_u(
    roster_effects: ArrayOrTensor,
    *,
    return_residuals: bool = False,
) -> tuple[ArrayOrTensor, np.ndarray] | tuple[ArrayOrTensor, np.ndarray, ArrayOrTensor]:
    """Compute signed non-additive role-swap complementarity per skill pair.

    The input shape is [K,K,2 replicas,2 agents,d_E].  Each replica is
    double-centered over the two roster axes before the role-swap contrast.
    Thus any model whose effects are only additive functions of the two
    assigned skills has exactly zero population target.  The symmetric
    orientation component is subtracted from the antisymmetric component:
    a one-sided pair effect therefore scores zero, while a stable sign reversal
    under role swap scores positively.
    """

    shape = tuple(roster_effects.shape)
    if len(shape) != 5 or shape[0] != shape[1] or shape[2] != 2 or shape[3] != 2:
        raise ValueError("roster effects must have shape [K,K,2,2,d_E]")
    if shape[0] <= 1 or shape[-1] <= 0:
        raise ValueError("R33 needs at least two skills and one effect dimension")
    if isinstance(roster_effects, torch.Tensor):
        if not bool(torch.isfinite(roster_effects).all().item()):
            raise ValueError("roster effects must be finite")
    elif not np.all(np.isfinite(np.asarray(roster_effects))):
        raise ValueError("roster effects must be finite")

    residual = _two_way_interaction_residual(roster_effects)
    pairs = np.asarray(
        [(left, right) for left in range(shape[0]) for right in range(left + 1, shape[0])],
        dtype=np.int64,
    )
    values = []
    for left, right in pairs:
        forward = residual[left, right, :, 0, :] - residual[left, right, :, 1, :]
        reverse = residual[right, left, :, 0, :] - residual[right, left, :, 1, :]
        role_swap = 0.5 * (forward - reverse)
        symmetric = 0.5 * (forward + reverse)
        if isinstance(roster_effects, torch.Tensor):
            values.append(
                0.25
                * (
                    torch.sum(role_swap[0] * role_swap[1])
                    - torch.sum(symmetric[0] * symmetric[1])
                )
            )
        else:
            values.append(
                0.25
                * (
                    np.sum(role_swap[0] * role_swap[1])
                    - np.sum(symmetric[0] * symmetric[1])
                )
            )
    pair_scores = (
        torch.stack(values)
        if isinstance(roster_effects, torch.Tensor)
        else np.asarray(values, dtype=np.asarray(roster_effects).dtype)
    )
    if return_residuals:
        return pair_scores, pairs, residual
    return pair_scores, pairs


def standardized_roster_scores(
    pair_scores: ArrayOrTensor,
    pairs: np.ndarray,
    *,
    n_skills: int = 4,
    pair_source_indices: np.ndarray | None = None,
    epsilon: float = 1e-8,
) -> tuple[ArrayOrTensor, ArrayOrTensor]:
    """Expand unordered-pair scores to 16 ordered rosters and standardize."""

    pairs = np.asarray(pairs, dtype=np.int64)
    if pairs.shape != (int(n_skills) * (int(n_skills) - 1) // 2, 2):
        raise ValueError("unordered skill-pair table has the wrong shape")
    if int(pair_scores.shape[0]) != int(pairs.shape[0]):
        raise ValueError("one score is required per unordered skill pair")
    source = (
        np.arange(pairs.shape[0], dtype=np.int64)
        if pair_source_indices is None
        else np.asarray(pair_source_indices, dtype=np.int64).reshape(-1)
    )
    if sorted(source.tolist()) != list(range(pairs.shape[0])):
        raise ValueError("pair_source_indices must be a permutation")

    if isinstance(pair_scores, torch.Tensor):
        raw = torch.zeros(
            int(n_skills),
            int(n_skills),
            dtype=pair_scores.dtype,
            device=pair_scores.device,
        )
        for target_index, (left, right) in enumerate(pairs):
            value = pair_scores[int(source[target_index])]
            raw[int(left), int(right)] = value
            raw[int(right), int(left)] = value
        flat = raw.reshape(-1)
        standardized = (flat - flat.mean()) / (flat.std(unbiased=False) + float(epsilon))
        return flat, standardized

    values = np.asarray(pair_scores)
    raw = np.zeros((int(n_skills), int(n_skills)), dtype=values.dtype)
    for target_index, (left, right) in enumerate(pairs):
        value = values[int(source[target_index])]
        raw[int(left), int(right)] = value
        raw[int(right), int(left)] = value
    flat = raw.reshape(-1)
    standardized = (flat - flat.mean()) / (flat.std(ddof=0) + float(epsilon))
    return flat, standardized


def exact_roster_probabilities(
    policy: FixedClockAREditPolicy,
    *,
    joint_obs: torch.Tensor,
    compact: torch.Tensor,
    team_vector: torch.Tensor,
    prev_skills: torch.Tensor,
    prev_ages: torch.Tensor,
    prev_active: torch.Tensor,
    agent_order: torch.Tensor,
    final_rosters: ArrayOrTensor,
    omega: torch.Tensor | None = None,
    agent_relevance: torch.Tensor | None = None,
) -> torch.Tensor:
    """Teacher-force every final roster and return its exact joint probability."""

    rosters = np.asarray(
        final_rosters.detach().cpu().numpy()
        if isinstance(final_rosters, torch.Tensor)
        else final_rosters,
        dtype=np.int64,
    )
    expected_shape = (policy.n_skills ** policy.n_agents, policy.n_agents)
    if rosters.shape != expected_shape:
        raise ValueError(f"final_rosters must have shape {expected_shape}")
    previous_np = prev_skills.detach().cpu().numpy()
    active_np = prev_active.detach().cpu().numpy()
    order_np = agent_order.detach().cpu().numpy()
    log_probabilities = []
    for roster in rosters:
        token_kind, set_skill = final_roster_tokens(
            previous_np,
            active_np,
            roster,
            order_np,
        )
        token_logp, _entropy = policy.evaluate_sequence(
            joint_obs=joint_obs,
            compact=compact,
            team_vector=team_vector,
            prev_skills=prev_skills,
            prev_ages=prev_ages,
            prev_active=prev_active,
            agent_order=agent_order,
            token_kind=torch.as_tensor(
                token_kind, dtype=torch.long, device=joint_obs.device
            ),
            set_skill=torch.as_tensor(
                set_skill, dtype=torch.long, device=joint_obs.device
            ),
            omega=omega,
            agent_relevance=agent_relevance,
        )
        log_probabilities.append(token_logp.sum())
    return torch.exp(torch.stack(log_probabilities))


def exact_expected_complementarity_loss(
    roster_probabilities: torch.Tensor,
    standardized_scores: ArrayOrTensor,
) -> torch.Tensor:
    """Return the negative exact score expectation over complete rosters."""

    if roster_probabilities.ndim != 2 or int(roster_probabilities.shape[1]) <= 1:
        raise ValueError("roster probabilities must have shape [batch, roster]")
    scores = torch.as_tensor(
        standardized_scores,
        dtype=roster_probabilities.dtype,
        device=roster_probabilities.device,
    )
    if tuple(scores.shape) != tuple(roster_probabilities.shape):
        raise ValueError("roster probabilities and scores must share shape")
    if not bool(torch.isfinite(roster_probabilities).all().item()):
        raise ValueError("roster probabilities must be finite")
    if not bool(torch.isfinite(scores).all().item()):
        raise ValueError("standardized scores must be finite")
    return -(roster_probabilities * scores.detach()).sum(dim=-1).mean()


def parameter_drift_metrics(
    before: Mapping[str, ArrayOrTensor],
    after: Mapping[str, ArrayOrTensor],
    *,
    selected_prefix: str = "high.skill_head",
    epsilon: float = 1e-12,
) -> dict[str, Any]:
    """Measure selected-head and all-other parameter movement."""

    if set(before) != set(after) or not before:
        raise ValueError("parameter snapshots must expose the same non-empty names")
    selected_prefix = str(selected_prefix).strip(".")
    totals = {
        "selected": {"base": 0.0, "delta": 0.0, "max_abs": 0.0, "count": 0},
        "other": {"base": 0.0, "delta": 0.0, "max_abs": 0.0, "count": 0},
    }
    per_parameter: dict[str, dict[str, Any]] = {}
    for name in sorted(before):
        left = np.asarray(
            before[name].detach().cpu().numpy()
            if isinstance(before[name], torch.Tensor)
            else before[name],
            dtype=np.float64,
        )
        right = np.asarray(
            after[name].detach().cpu().numpy()
            if isinstance(after[name], torch.Tensor)
            else after[name],
            dtype=np.float64,
        )
        if left.shape != right.shape or not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
            raise ValueError(f"invalid parameter snapshot for {name}")
        delta = right - left
        selected = name == selected_prefix or name.startswith(selected_prefix + ".")
        group = "selected" if selected else "other"
        base_sq = float(np.sum(left * left))
        delta_sq = float(np.sum(delta * delta))
        max_abs = float(np.max(np.abs(delta))) if delta.size else 0.0
        totals[group]["base"] += base_sq
        totals[group]["delta"] += delta_sq
        totals[group]["max_abs"] = max(float(totals[group]["max_abs"]), max_abs)
        totals[group]["count"] += int(delta.size)
        per_parameter[name] = {
            "selected": selected,
            "relative_l2": float(np.sqrt(delta_sq)) / (float(np.sqrt(base_sq)) + float(epsilon)),
            "max_abs": max_abs,
        }
    if totals["selected"]["count"] <= 0:
        raise ValueError(f"no parameters matched {selected_prefix!r}")
    return {
        "selected_parameter_count": int(totals["selected"]["count"]),
        "selected_relative_l2": float(np.sqrt(totals["selected"]["delta"]))
        / (float(np.sqrt(totals["selected"]["base"])) + float(epsilon)),
        "selected_max_abs": float(totals["selected"]["max_abs"]),
        "other_parameter_count": int(totals["other"]["count"]),
        "other_relative_l2": float(np.sqrt(totals["other"]["delta"]))
        / (float(np.sqrt(totals["other"]["base"])) + float(epsilon)),
        "other_max_abs": float(totals["other"]["max_abs"]),
        "parameters": per_parameter,
    }
