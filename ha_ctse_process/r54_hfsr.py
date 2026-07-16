"""R54 hybrid field-slot representation sufficiency components.

This module is intentionally isolated from HMASD and HA-CTSE training.  It is
a supervised representation gate over anonymous active sets.  There is no
environment reward, critic, PPO, skill, membership event, or temporal policy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from scipy.optimize import linear_sum_assignment


TRAIN_TEAM_SIZES = (8, 16, 32)
EVAL_TEAM_SIZES = (8, 16, 32, 64)
MEMBER_FEATURE_DIM = 12
TASK_FEATURE_DIM = 10
HIDDEN_DIM = 64
SLOT_COUNT = 8
RESIDUAL_COUNT = 2
REPRESENTATION_TOKEN_COUNT = SLOT_COUNT + RESIDUAL_COUNT
EXPECTED_PARAMETER_COUNT = 49_576


@dataclass(frozen=True)
class AssignmentCases:
    """A fixed-N collection with model inputs and ledger-only identities."""

    active_n: int
    member_features: np.ndarray
    task_features: np.ndarray
    oracle_assignments: np.ndarray
    oracle_costs: np.ndarray
    cost_matrices: np.ndarray
    member_orders: np.ndarray
    critical_tasks: np.ndarray
    critical_members: np.ndarray
    mean_alias_groups: np.ndarray
    member_keys: np.ndarray
    task_keys: np.ndarray
    unique_margins: np.ndarray

    @property
    def count(self) -> int:
        return int(self.member_features.shape[0])

    def subset(self, indices: np.ndarray) -> "AssignmentCases":
        index = np.asarray(indices, dtype=np.int64)
        return AssignmentCases(
            active_n=self.active_n,
            member_features=self.member_features[index],
            task_features=self.task_features[index],
            oracle_assignments=self.oracle_assignments[index],
            oracle_costs=self.oracle_costs[index],
            cost_matrices=self.cost_matrices[index],
            member_orders=self.member_orders[index],
            critical_tasks=self.critical_tasks[index],
            critical_members=self.critical_members[index],
            mean_alias_groups=self.mean_alias_groups[index],
            member_keys=self.member_keys[index],
            task_keys=self.task_keys[index],
            unique_margins=self.unique_margins[index],
        )

    def validate(self) -> None:
        c, n = self.count, int(self.active_n)
        expected = {
            "member_features": (c, n, MEMBER_FEATURE_DIM),
            "task_features": (c, n, TASK_FEATURE_DIM),
            "oracle_assignments": (c, n),
            "oracle_costs": (c,),
            "cost_matrices": (c, n, n),
            "member_orders": (c, n),
            "critical_tasks": (c,),
            "critical_members": (c,),
            "mean_alias_groups": (c,),
            "member_keys": (c, n),
            "task_keys": (c, n),
            "unique_margins": (c,),
        }
        for name, shape in expected.items():
            if tuple(getattr(self, name).shape) != shape:
                raise ValueError(
                    f"R54 {name} shape {getattr(self, name).shape} != {shape}"
                )
        reference = np.arange(n, dtype=np.int64)
        if not all(np.array_equal(np.sort(row), reference) for row in self.member_orders):
            raise ValueError("R54 external member order is not a permutation")
        if not all(
            np.array_equal(np.sort(row), reference)
            for row in self.oracle_assignments
        ):
            raise ValueError("R54 oracle is not a capacity-one perfect matching")
        if not np.all(np.isfinite(self.member_features)):
            raise ValueError("R54 member features are not finite")
        if not np.all(np.isfinite(self.task_features)):
            raise ValueError("R54 task features are not finite")
        if not np.all(np.isfinite(self.cost_matrices)):
            raise ValueError("R54 cost matrices are not finite")
        if not np.all(self.unique_margins > 0.0):
            raise ValueError("R54 oracle uniqueness margin is not positive")


def _assignment_cost(member: np.ndarray, task: np.ndarray) -> np.ndarray:
    """Registered generic cost: geometry, feasibility, energy, and load."""

    position = ((member[:, None, 0:2] - task[None, :, 0:2]) ** 2).sum(-1)
    tie = 0.05 * (
        member[:, None, 11] - task[None, :, 9]
    ) ** 2
    required = task[None, :, 2:6]
    capability = member[:, None, 4:8]
    feasible = np.all(capability + 1.0e-7 >= required, axis=-1)

    # Member-only and task-only terms are deliberately small.  They make the
    # registered cost depend on energy/load/availability and task pressure but
    # cancel under a complete matching, leaving the geometric unique-matching
    # construction auditable.
    member_burden = (
        0.02 * (1.0 - member[:, 8])
        + 0.02 * member[:, 9]
        + 0.02 * (1.0 - member[:, 10])
    )[:, None]
    task_pressure = (
        0.002 * task[:, 6] + 0.001 * task[:, 7] + 0.002 * task[:, 8]
    )[None, :]
    return (
        6.0 * position
        + tie
        + member_burden
        + task_pressure
        + (~feasible).astype(np.float64) * 1_000.0
    )


def _base_case(
    *, n: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Create two symmetric population modes and one rare-capability pair."""

    half = n // 2
    y = np.linspace(-1.0, 1.0, half, dtype=np.float64)
    y += rng.normal(0.0, 0.015, size=half)
    left_x = -1.0 + rng.normal(0.0, 0.025, size=half)
    left = np.stack((left_x, y), axis=-1)
    right = -left
    positions = np.concatenate((left, right), axis=0)

    left_velocity = rng.normal(0.0, 0.12, size=(half, 2))
    velocities = np.concatenate((left_velocity, -left_velocity), axis=0)
    capabilities = np.zeros((n, 4), dtype=np.float64)
    capabilities[:half, 0] = 1.0
    capabilities[half:, 1] = 1.0

    cluster_start = 0 if int(rng.integers(0, 2)) == 0 else half
    local_pair = rng.choice(half, size=2, replace=False)
    critical_member = cluster_start + int(local_pair[0])
    partner_member = cluster_start + int(local_pair[1])
    capabilities[[critical_member, partner_member], 2] = 1.0

    energy = rng.uniform(0.65, 1.0, size=(n, 1))
    load = rng.uniform(0.0, 0.35, size=(n, 1))
    availability = rng.uniform(0.70, 1.0, size=(n, 1))
    tie = np.linspace(0.05, 0.95, n, dtype=np.float64)
    tie = tie[rng.permutation(n)][:, None]
    member = np.concatenate(
        (positions, velocities, capabilities, energy, load, availability, tie),
        axis=-1,
    )

    task = np.zeros((n, TASK_FEATURE_DIM), dtype=np.float64)
    task[:, 0:2] = positions
    task[:half, 2] = 1.0
    task[half:, 3] = 1.0
    task[:, 6] = rng.uniform(0.25, 1.0, size=n)
    task[:, 7] = rng.uniform(0.20, 1.0, size=n)
    task[:, 8] = rng.uniform(0.25, 1.0, size=n)
    task[:, 9] = member[:, 11]
    task[critical_member, 2:6] = 0.0
    task[critical_member, 5] = 1.0
    task[partner_member, 2:6] = 0.0
    task[partner_member, 4] = 1.0
    return member, task, critical_member, partner_member


def _materialize_case(
    *,
    base_member: np.ndarray,
    task: np.ndarray,
    critical_task: int,
    partner: int,
    rare_member: int,
    member_order: np.ndarray,
    mean_alias_group: int,
    key_offset: int,
) -> dict[str, Any]:
    member = base_member.copy()
    member[:, 7] = 0.0
    member[rare_member, 7] = 1.0
    cost = _assignment_cost(member, task)
    row, col = linear_sum_assignment(cost)
    assignment = np.empty(member.shape[0], dtype=np.int64)
    assignment[row] = col

    expected = np.arange(member.shape[0], dtype=np.int64)
    if rare_member != critical_task:
        expected[critical_task] = partner
        expected[partner] = critical_task
    if not np.array_equal(assignment, expected):
        raise RuntimeError("R54 deterministic Hungarian oracle left construction")

    requirement = task[critical_task, 2:6]
    qualified = np.all(member[:, 4:8] + 1.0e-7 >= requirement, axis=-1)
    if int(qualified.sum()) != 1 or not bool(qualified[rare_member]):
        raise RuntimeError("R54 critical task does not have exactly one qualified member")

    forced = {critical_task, partner}
    free = [index for index in range(member.shape[0]) if index not in forced]
    if len(free) >= 2:
        geometric = (
            6.0
            * (
                (
                    member[np.asarray(free), None, 0:2]
                    - task[None, np.asarray(free), 0:2]
                )
                ** 2
            ).sum(-1)
            + 0.05
            * (
                member[np.asarray(free), None, 11]
                - task[None, np.asarray(free), 9]
            )
            ** 2
        )
        off_diagonal = geometric[~np.eye(len(free), dtype=np.bool_)]
        unique_margin = float(off_diagonal.min())
    else:
        unique_margin = 1.0
    if unique_margin <= 0.0:
        raise RuntimeError("R54 constructed oracle is not uniquely separated")

    n = int(member.shape[0])
    return {
        "member": member.astype(np.float32),
        "task": task.astype(np.float32),
        "assignment": assignment,
        "oracle_cost": float(cost[np.arange(n), assignment].sum()),
        "cost": cost.astype(np.float32),
        "member_order": member_order.astype(np.int64),
        "critical_task": int(critical_task),
        "critical_member": int(rare_member),
        "mean_alias_group": int(mean_alias_group),
        "member_keys": (key_offset + np.arange(n, dtype=np.int64)),
        "task_keys": (key_offset + 100_000 + np.arange(n, dtype=np.int64)),
        "unique_margin": unique_margin,
    }


def generate_assignment_cases(
    *,
    active_n: int,
    count: int,
    seed: int,
    mean_alias_case_count: int,
) -> AssignmentCases:
    """Generate a deterministic fixed-N split, including exact alias twins."""

    n = int(active_n)
    if n not in EVAL_TEAM_SIZES:
        raise ValueError(f"R54 unsupported team size {n}")
    if count <= 0 or mean_alias_case_count < 0 or mean_alias_case_count > count:
        raise ValueError("R54 invalid case counts")
    if mean_alias_case_count % 2 != 0:
        raise ValueError("R54 mean-alias cases must form pairs")
    rng = np.random.default_rng(int(seed) + 10_007 * n)
    rows: list[dict[str, Any]] = []
    alias_pairs = mean_alias_case_count // 2
    case_index = 0
    for group in range(alias_pairs):
        member, task, critical, partner = _base_case(n=n, rng=rng)
        order = rng.permutation(n)
        key_offset = int(seed) * 1_000_000 + n * 10_000 + case_index * 100
        rows.append(
            _materialize_case(
                base_member=member,
                task=task,
                critical_task=critical,
                partner=partner,
                rare_member=critical,
                member_order=order,
                mean_alias_group=group,
                key_offset=key_offset,
            )
        )
        case_index += 1
        rows.append(
            _materialize_case(
                base_member=member,
                task=task,
                critical_task=critical,
                partner=partner,
                rare_member=partner,
                member_order=order,
                mean_alias_group=group,
                key_offset=key_offset,
            )
        )
        case_index += 1

    while len(rows) < count:
        member, task, critical, partner = _base_case(n=n, rng=rng)
        order = rng.permutation(n)
        key_offset = int(seed) * 1_000_000 + n * 10_000 + case_index * 100
        rows.append(
            _materialize_case(
                base_member=member,
                task=task,
                critical_task=critical,
                partner=partner,
                rare_member=critical,
                member_order=order,
                mean_alias_group=-1,
                key_offset=key_offset,
            )
        )
        case_index += 1

    cases = AssignmentCases(
        active_n=n,
        member_features=np.stack([row["member"] for row in rows]),
        task_features=np.stack([row["task"] for row in rows]),
        oracle_assignments=np.stack([row["assignment"] for row in rows]),
        oracle_costs=np.asarray([row["oracle_cost"] for row in rows], dtype=np.float64),
        cost_matrices=np.stack([row["cost"] for row in rows]),
        member_orders=np.stack([row["member_order"] for row in rows]),
        critical_tasks=np.asarray([row["critical_task"] for row in rows], dtype=np.int64),
        critical_members=np.asarray([row["critical_member"] for row in rows], dtype=np.int64),
        mean_alias_groups=np.asarray([row["mean_alias_group"] for row in rows], dtype=np.int64),
        member_keys=np.stack([row["member_keys"] for row in rows]),
        task_keys=np.stack([row["task_keys"] for row in rows]),
        unique_margins=np.asarray([row["unique_margin"] for row in rows], dtype=np.float64),
    )
    cases.validate()
    return cases


@dataclass
class SlotRepresentation:
    tokens: torch.Tensor
    token_mask: torch.Tensor
    alpha: torch.Tensor
    masses: torch.Tensor
    residual_indices: torch.Tensor
    reconstruction_loss: torch.Tensor
    mass_kl: torch.Tensor
    effective_slot_count: torch.Tensor


@dataclass
class SequenceOutput:
    logits: torch.Tensor
    log_probs: torch.Tensor
    actions_by_member: torch.Tensor
    collision_count: int
    slots: SlotRepresentation
    max_context_width: int
    member_member_tensor_count: int


class HFSRPointerModel(nn.Module):
    """Exact 49,576-parameter pointer shared by the two R54 arms."""

    def __init__(self, representation_mode: str):
        super().__init__()
        if representation_mode not in {"full_active_set_reference", "hybrid_m8_l2"}:
            raise ValueError(f"R54 unknown representation mode {representation_mode}")
        self.representation_mode = representation_mode
        self.member_encoder = nn.Sequential(
            nn.Linear(MEMBER_FEATURE_DIM, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.ReLU(),
        )
        self.task_encoder = nn.Sequential(
            nn.Linear(TASK_FEATURE_DIM, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.ReLU(),
        )
        self.context_q = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
        self.context_k = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
        self.context_v = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
        self.context_o = nn.Linear(HIDDEN_DIM, HIDDEN_DIM)
        self.slot_assignment = nn.Sequential(
            nn.Linear(HIDDEN_DIM, 32),
            nn.ReLU(),
            nn.Linear(32, SLOT_COUNT),
        )
        self.ar_query = nn.Sequential(
            nn.Linear(3 * HIDDEN_DIM, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
        )
        self.task_key = nn.Linear(HIDDEN_DIM + 1, HIDDEN_DIM)
        if self.parameter_count() != EXPECTED_PARAMETER_COUNT:
            raise RuntimeError(
                f"R54 parameter count {self.parameter_count()} != {EXPECTED_PARAMETER_COUNT}"
            )

    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def _slots(
        self, member_embeddings: torch.Tensor, member_mask: torch.Tensor
    ) -> SlotRepresentation:
        mask = member_mask.to(member_embeddings.dtype)
        logits = self.slot_assignment(member_embeddings)
        alpha = torch.softmax(logits, dim=-1) * mask.unsqueeze(-1)
        masses_raw = alpha.sum(dim=1)
        slots = torch.einsum("bnm,bnh->bmh", alpha, member_embeddings)
        slots = slots / (masses_raw.unsqueeze(-1) + 1.0e-8)
        reconstruction = torch.einsum("bnm,bmh->bnh", alpha, slots)
        squared_error = ((member_embeddings - reconstruction) ** 2).sum(-1)
        reconstruction_loss = (squared_error * mask).sum() / mask.sum().clamp_min(1.0)
        active_count = mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        masses = masses_raw / active_count
        mass_kl_per_case = (
            masses * torch.log((masses + 1.0e-8) * float(SLOT_COUNT))
        ).sum(-1)
        mass_kl = mass_kl_per_case.mean()
        effective = torch.exp(
            -(masses * torch.log(masses + 1.0e-8)).sum(-1)
        )
        residual_score = squared_error.detach().masked_fill(~member_mask, -torch.inf)
        residual_indices = torch.topk(
            residual_score, k=RESIDUAL_COUNT, dim=1, largest=True, sorted=True
        ).indices
        gather = residual_indices.unsqueeze(-1).expand(-1, -1, HIDDEN_DIM)
        exact_residuals = torch.gather(member_embeddings, 1, gather)
        tokens = torch.cat((slots, exact_residuals), dim=1)
        token_mask = torch.ones(
            tokens.shape[:2], dtype=torch.bool, device=tokens.device
        )
        return SlotRepresentation(
            tokens=tokens,
            token_mask=token_mask,
            alpha=alpha,
            masses=masses,
            residual_indices=residual_indices,
            reconstruction_loss=reconstruction_loss,
            mass_kl=mass_kl,
            effective_slot_count=effective,
        )

    def _context(
        self,
        focal: torch.Tensor,
        tokens: torch.Tensor,
        token_mask: torch.Tensor,
    ) -> torch.Tensor:
        # R54 batches have one active N.  Compact masked padding before the
        # linear algebra so appending arbitrary junk cannot change GEMM shape
        # or floating-point reduction order for the active set.
        if not bool(token_mask.all()):
            active_counts = token_mask.sum(dim=1)
            if not bool(torch.all(active_counts == active_counts[0])):
                raise ValueError("R54 context batches must share one active-set size")
            width = int(active_counts[0].item())
            active_indices = torch.stack(
                [torch.nonzero(row, as_tuple=False).squeeze(-1) for row in token_mask],
                dim=0,
            )
            gather = active_indices.unsqueeze(-1).expand(-1, -1, HIDDEN_DIM)
            tokens = torch.gather(tokens, 1, gather)
            token_mask = torch.ones(
                (tokens.shape[0], width), dtype=torch.bool, device=tokens.device
            )
        query = self.context_q(focal).unsqueeze(1)
        key = self.context_k(tokens)
        value = self.context_v(tokens)
        scores = torch.matmul(query, key.transpose(-1, -2)) / math.sqrt(HIDDEN_DIM)
        scores = scores.masked_fill(~token_mask.unsqueeze(1), -1.0e9)
        weights = torch.softmax(scores, dim=-1)
        return self.context_o(torch.matmul(weights, value).squeeze(1))

    def forward_sequence(
        self,
        *,
        member_features: torch.Tensor,
        task_features: torch.Tensor,
        member_mask: torch.Tensor,
        task_mask: torch.Tensor,
        member_order: torch.Tensor,
        teacher_assignments: torch.Tensor | None,
    ) -> SequenceOutput:
        """Run capacity-masked AR assignment in an external member order."""

        member_embeddings = self.member_encoder(member_features)
        task_embeddings = self.task_encoder(task_features)
        slots = self._slots(member_embeddings, member_mask)
        if self.representation_mode == "full_active_set_reference":
            context_tokens = member_embeddings
            context_mask = member_mask
        else:
            context_tokens = slots.tokens
            context_mask = slots.token_mask

        batch, max_tasks = task_mask.shape
        decision_count = int(member_order.shape[1])
        assigned = torch.zeros_like(task_mask)
        prefix_sum = torch.zeros(
            (batch, HIDDEN_DIM), dtype=task_embeddings.dtype, device=task_embeddings.device
        )
        logits_rows: list[torch.Tensor] = []
        log_prob_rows: list[torch.Tensor] = []
        actions_by_member = torch.full(
            (batch, member_features.shape[1]),
            -1,
            dtype=torch.long,
            device=member_features.device,
        )
        collision_count = 0
        batch_index = torch.arange(batch, device=member_features.device)
        for position in range(decision_count):
            focal_index = member_order[:, position]
            focal = member_embeddings[batch_index, focal_index]
            context = self._context(focal, context_tokens, context_mask)
            if position == 0:
                prefix = torch.zeros_like(prefix_sum)
            else:
                prefix = prefix_sum / float(position)
            query = self.ar_query(torch.cat((focal, context, prefix), dim=-1))
            remaining = (task_mask & ~assigned).to(task_embeddings.dtype)
            keys = self.task_key(
                torch.cat((task_embeddings, remaining.unsqueeze(-1)), dim=-1)
            )
            logits = torch.einsum("bh,bth->bt", query, keys) / math.sqrt(HIDDEN_DIM)
            valid = task_mask & ~assigned
            logits = logits.masked_fill(~valid, -1.0e9)
            if teacher_assignments is None:
                action = torch.argmax(logits, dim=-1)
            else:
                action = teacher_assignments[batch_index, focal_index]
                if not bool(torch.all(valid[batch_index, action])):
                    raise RuntimeError("R54 teacher prefix violates capacity-one support")
            collision_count += int(assigned[batch_index, action].sum().item())
            log_prob = torch.log_softmax(logits, dim=-1)[batch_index, action]
            logits_rows.append(logits)
            log_prob_rows.append(log_prob)
            actions_by_member[batch_index, focal_index] = action
            assigned[batch_index, action] = True
            prefix_sum = prefix_sum + task_embeddings[batch_index, action]

        return SequenceOutput(
            logits=torch.stack(logits_rows, dim=1),
            log_probs=torch.stack(log_prob_rows, dim=1),
            actions_by_member=actions_by_member,
            collision_count=collision_count,
            slots=slots,
            max_context_width=int(context_tokens.shape[1]),
            # Context is computed one focal member at a time.  Hybrid creates
            # [B,N,M] slot weights and [B,1,M+L] context scores, never [B,N,N]
            # member-member interactions.
            member_member_tensor_count=0,
        )

    def supervised_loss(
        self,
        *,
        member_features: torch.Tensor,
        task_features: torch.Tensor,
        member_mask: torch.Tensor,
        task_mask: torch.Tensor,
        member_order: torch.Tensor,
        oracle_assignments: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor], SequenceOutput]:
        output = self.forward_sequence(
            member_features=member_features,
            task_features=task_features,
            member_mask=member_mask,
            task_mask=task_mask,
            member_order=member_order,
            teacher_assignments=oracle_assignments,
        )
        pointer = -output.log_probs.mean()
        total = (
            pointer
            + 0.1 * output.slots.reconstruction_loss
            + 0.01 * output.slots.mass_kl
        )
        return total, {
            "pointer": pointer,
            "slot_reconstruction": output.slots.reconstruction_loss,
            "slot_mass_kl": output.slots.mass_kl,
        }, output


def to_tensors(
    cases: AssignmentCases, *, device: torch.device
) -> dict[str, torch.Tensor]:
    n = int(cases.active_n)
    return {
        "member_features": torch.as_tensor(cases.member_features, device=device),
        "task_features": torch.as_tensor(cases.task_features, device=device),
        "member_mask": torch.ones((cases.count, n), dtype=torch.bool, device=device),
        "task_mask": torch.ones((cases.count, n), dtype=torch.bool, device=device),
        "member_order": torch.as_tensor(cases.member_orders, dtype=torch.long, device=device),
        "oracle_assignments": torch.as_tensor(
            cases.oracle_assignments, dtype=torch.long, device=device
        ),
    }


def model_state_copy(model: nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


def maximum_state_difference(
    left: dict[str, torch.Tensor], right: dict[str, torch.Tensor]
) -> float:
    if left.keys() != right.keys():
        return math.inf
    if not left:
        return 0.0
    return max(float((left[key] - right[key]).abs().max().item()) for key in left)


def state_dict_finite(model: nn.Module) -> bool:
    return all(bool(torch.isfinite(value).all()) for value in model.state_dict().values())


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value
