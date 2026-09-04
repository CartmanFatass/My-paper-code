"""EOCIV-B10 receiver-credit frozen-score exposure curve.

The attempt reuses only B9R1's real sibling episode primitive and stored
episode type.  Collection coordinates come directly from the committed B10
manifest; no B9 result, optimizer, checkpoint, receipt, or outcome is read.
"""

from __future__ import annotations

import json
import math
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from experiments.candidates.eociv_lite import real_valve_learning as learner
from experiments.candidates.eociv_lite.b9r1 import experiment as b9r1


RECEIVER_ADDRESSED = "RECEIVER_ADDRESSED"
SOURCE_CONTROL = "AUTHENTICATED_SOURCE_ADDRESSED_CONTROL"
ANCHOR_IDS = ("A0", "A1", "A2")
ANCHOR_SEEDS = {"A0": 990_031, "A1": 990_032, "A2": 990_033}
PROFILE_NAMES = b9r1.PROFILE_NAMES
HELDOUT_ROOTS = tuple(range(991_001, 991_009))
ENDPOINTS = ("0", "R1", "S1", "R4", "S4", "R16", "S16")
EVALUATION_BODIES = ("CORRECT", "SWAPPED")
MANDATORY_STEPS = (1, 4, 16)
HORIZON = 48
ADAM_LR = 3e-4
ACTIVE_ACTOR_PARAMETER_NAMES = b9r1.ACTIVE_ACTOR_PARAMETER_NAMES
ROOT_SET_SELECTOR = 991_001
CPU_TIME_CAP_SECONDS = 300.0
INVALID_BRANCH = "INVALID_ATTEMPT"
EDGE_BRANCH = "B10_FIXED_SCORE_EXPOSURE_EDGE"
NOT_SUPPORTED_BRANCH = "B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED"
MANIFEST_RELATIVE_PATH = Path(
    "docs/research/candidates/eociv_lite/"
    "EOCIV_B10_FROZEN_COLLECTION_TAPE_MANIFEST_20260904.json"
)


def _metric_names() -> tuple[str, ...]:
    names = ["phi_0"]
    for step in MANDATORY_STEPS:
        names.extend((
            f"phi_R{step}", f"phi_S{step}", f"Delta_R{step}", f"J_{step}",
            f"R_{step}_v0", f"R_{step}_vS", f"S_{step}_v0",
        ))
    return tuple(names)


METRICS = _metric_names()


class CpuTimeLimitExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class EvaluationEpisode:
    anchor_id: str
    profile: str
    heldout_root: int
    root_index: int
    endpoint: str
    body: str
    critical_reward_mean: float
    lifecycle: tuple[Any, ...]
    action_noise: np.ndarray
    shocks: tuple[str, ...]
    active_masks: tuple[np.ndarray, ...]


@dataclass(frozen=True)
class RunPlan:
    mode: str
    anchors: tuple[str, ...]
    evaluation_profiles: tuple[str, ...]
    heldout_roots: tuple[int, ...]

    @property
    def collection_episodes(self) -> int:
        return len(self.anchors) * len(PROFILE_NAMES) * 4

    @property
    def evaluation_episodes(self) -> int:
        return (len(self.anchors) * len(self.evaluation_profiles)
                * len(self.heldout_roots) * len(ENDPOINTS) * len(EVALUATION_BODIES))

    def expected_counts(self) -> dict[str, int]:
        episodes = self.collection_episodes + self.evaluation_episodes
        optimizer_calls = len(self.anchors) * 2 * 16
        return {
            "episodes": episodes,
            "environment_transitions": episodes * HORIZON,
            "policy_calls": episodes * HORIZON,
            "collection_episodes": self.collection_episodes,
            "evaluation_episodes": self.evaluation_episodes,
            "optimizer_calls": optimizer_calls,
            "receiver_optimizer_calls": len(self.anchors) * 16,
            "source_control_optimizer_calls": len(self.anchors) * 16,
            "gradient_computations": len(self.anchors) * 2,
            "gradient_recomputations": 0,
            "critic_updates": 0,
            "critic_loss_calls": 0,
            "value_gradient_calls": 0,
            "global_clip_calls": 0,
            "retry": 0,
            "rescue": 0,
            "sweep": 0,
            "search": 0,
            "checkpoint_selection": 0,
            "hypothetical_transitions": 0,
        }


FULL_PLAN = RunPlan("full", ANCHOR_IDS, PROFILE_NAMES, HELDOUT_ROOTS)
SMOKE_PLAN = RunPlan("smoke", ("A0",), (PROFILE_NAMES[0],), (HELDOUT_ROOTS[0],))


def empty_counts() -> dict[str, int]:
    return {key: 0 for key in FULL_PLAN.expected_counts()}


@dataclass
class RunProgress:
    counts: dict[str, int]
    phase: str = "initialization"


@dataclass
class BoundaryMeter:
    wall_start: float
    cpu_start: float
    peak_rss: int | None
    rss_error: str | None
    rss_failed: bool
    episode_boundaries: int = 0
    adam_boundaries: int = 0

    @classmethod
    def start(cls) -> "BoundaryMeter":
        try:
            return cls(time.perf_counter(), time.process_time(),
                       b9r1.peak_rss_bytes(), None, False)
        except OSError as exc:
            return cls(time.perf_counter(), time.process_time(), None, str(exc), True)

    def check(self, boundary: str) -> None:
        if boundary == "episode":
            self.episode_boundaries += 1
        elif boundary == "adam":
            self.adam_boundaries += 1
        else:
            raise ValueError(f"unknown boundary {boundary}")
        try:
            observed = b9r1.peak_rss_bytes()
            self.peak_rss = observed if self.peak_rss is None else max(self.peak_rss, observed)
        except OSError as exc:
            self.rss_failed, self.rss_error = True, str(exc)
        if self.process_cpu_seconds() > CPU_TIME_CAP_SECONDS:
            raise CpuTimeLimitExceeded(
                f"process CPU exceeded {CPU_TIME_CAP_SECONDS:.0f}s at {boundary} boundary"
            )

    def wall_seconds(self) -> float:
        return float(time.perf_counter() - self.wall_start)

    def process_cpu_seconds(self) -> float:
        return float(time.process_time() - self.cpu_start)

    def telemetry(self) -> dict[str, Any]:
        return {
            "wall_seconds": self.wall_seconds(),
            "process_cpu_seconds": self.process_cpu_seconds(),
            "peak_rss_bytes": self.peak_rss,
            "resources_unmeasured": self.rss_failed,
            "rss_measurement_error": self.rss_error,
            "cpu_cap_seconds": CPU_TIME_CAP_SECONDS,
            "cpu_cap_checked_only_at_episode_and_adam_boundaries": True,
            "episode_boundaries_observed": self.episode_boundaries,
            "adam_boundaries_observed": self.adam_boundaries,
        }


def load_collection_tapes(repository_root: Path) -> tuple[Mapping[str, Any], ...]:
    """Read the ordered manifest rows directly as scientific input."""
    data = json.loads((repository_root / MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8"))
    return tuple(data["tapes"])


def _new_actor(
    anchor_id: str, state: Mapping[str, torch.Tensor] | None = None
) -> learner.RecurrentActorCritic:
    capacities = {b9r1.PROFILE_BY_NAME[name].member_capacity for name in PROFILE_NAMES}
    actor = learner.RecurrentActorCritic(
        capacities.pop(), ANCHOR_SEEDS[anchor_id], encoder_kind="content_separating"
    )
    if state is not None:
        actor.load_state_dict(state, strict=True)
    return actor


def _clone_state(actor: learner.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in actor.state_dict().items()}


def _actor_parameters(
    actor: learner.RecurrentActorCritic,
) -> tuple[tuple[str, torch.nn.Parameter], ...]:
    available = dict(actor.named_parameters())
    return tuple((name, available[name]) for name in ACTIVE_ACTOR_PARAMETER_NAMES)


def exposure_for_anchor(anchor_id: str) -> dict[str, Any]:
    flat = torch.cat([
        parameter.detach().reshape(-1).double()
        for _, parameter in _actor_parameters(_new_actor(anchor_id))
    ])
    count = int(flat.numel())
    initial_l2 = float(torch.linalg.vector_norm(flat))
    one_step = float(ADAM_LR * math.sqrt(count))
    return {
        "anchor_id": anchor_id,
        "initialization_seed": ANCHOR_SEEDS[anchor_id],
        "active_parameter_names": list(ACTIVE_ACTOR_PARAMETER_NAMES),
        "active_parameter_count": count,
        "initial_active_parameter_l2": initial_l2,
        "one_step_adam_l2_upper_bound": one_step,
        "one_step_upper_ratio_vs_initialization": one_step / initial_l2,
        "sixteen_step_triangle_l2_upper_bound": 16.0 * one_step,
        "sixteen_step_triangle_ratio_vs_initialization": 16.0 * one_step / initial_l2,
    }


def endpoint_displacement(
    anchor_state: Mapping[str, torch.Tensor], endpoint_state: Mapping[str, torch.Tensor]
) -> tuple[float, float]:
    before = torch.cat([
        anchor_state[name].reshape(-1).double() for name in ACTIVE_ACTOR_PARAMETER_NAMES
    ])
    after = torch.cat([
        endpoint_state[name].reshape(-1).double() for name in ACTIVE_ACTOR_PARAMETER_NAMES
    ])
    displacement = float(torch.linalg.vector_norm(after - before))
    return displacement, displacement / float(torch.linalg.vector_norm(before))


def _record_episode(counts: dict[str, int], kind: str) -> None:
    counts["episodes"] += 1
    counts[f"{kind}_episodes"] += 1
    counts["environment_transitions"] += HORIZON
    counts["policy_calls"] += HORIZON


def _common_fixed_gradients(
    actor: learner.RecurrentActorCritic, trajectories: Sequence[b9r1.Episode],
) -> tuple[dict[str, tuple[torch.Tensor, ...]], dict[str, Any]]:
    receiver_losses: list[torch.Tensor] = []
    source_losses: list[torch.Tensor] = []
    same_complete_tensor, same_orders, term_count = True, True, 0
    for trajectory in trajectories:
        previous = torch.zeros((actor.capacity, actor.hidden_dim), dtype=torch.float32)
        score_rows: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        masks: list[np.ndarray] = []
        for stored_step in trajectory.steps:
            _, mean, hidden, mask = actor._step_tensors(
                stored_step.observations, stored_step.active_mask,
                stored_step.effective_slot_block, previous, stored_step.noise,
            )
            std = torch.exp(torch.clamp(actor.log_std, -4.0, 1.0))
            raw = mean + std * torch.as_tensor(stored_step.noise, dtype=torch.float32)
            score_rows.append(
                torch.distributions.Normal(mean, std).log_prob(raw.detach()).sum(-1)
            )
            values.append(actor.value(hidden[mask].mean(0)).squeeze(-1))
            masks.append(mask.detach().cpu().numpy().astype(np.bool_))
            previous = hidden
        complete_score_tensor = tuple(score_rows)
        receiver_tensor = complete_score_tensor
        source_tensor = complete_score_tensor
        credits = b9r1._normalized_gae(
            [stored_step.reward for stored_step in trajectory.steps], values
        )
        receiver_loss, receiver_order = b9r1._addressed_loss(
            receiver_tensor, masks, credits, trajectory.critical_edges, RECEIVER_ADDRESSED
        )
        source_loss, source_order = b9r1._addressed_loss(
            source_tensor, masks, credits, trajectory.critical_edges, SOURCE_CONTROL
        )
        same_complete_tensor &= receiver_tensor is source_tensor
        same_orders &= receiver_order == source_order
        term_count += len(receiver_order)
        receiver_losses.append(receiver_loss)
        source_losses.append(source_loss)
    parameters = tuple(parameter for _, parameter in _actor_parameters(actor))
    receiver_gradient = torch.autograd.grad(
        torch.stack(receiver_losses).mean(), parameters, retain_graph=True
    )
    source_gradient = torch.autograd.grad(
        torch.stack(source_losses).mean(), parameters
    )
    gradients = {
        RECEIVER_ADDRESSED: tuple(value.detach().clone() for value in receiver_gradient),
        SOURCE_CONTROL: tuple(value.detach().clone() for value in source_gradient),
    }
    if not all(torch.isfinite(value).all() for values in gradients.values() for value in values):
        raise RuntimeError("fixed gradient is nonfinite")
    norm = lambda values: float(torch.linalg.vector_norm(
        torch.cat([value.reshape(-1) for value in values])
    ))
    common = {
        "trajectory_count": len(trajectories),
        "term_count": term_count,
        "same_trajectory_score_tensors": same_orders,
        "gradients_computed_before_mutation": True,
        "receiver_gradient_norm": norm(receiver_gradient),
        "source_gradient_norm": norm(source_gradient),
        "complete_score_tensor_computations_per_stored_trajectory": 1,
        "normalized_terminal_gae_computations_per_stored_trajectory": 1,
        "same_complete_score_tensor_contracted_for_both_branches": same_complete_tensor,
        "gradient_computations_per_branch": 1,
        "gradient_recomputations": 0,
    }
    return gradients, common


def _apply_fixed_gradient_branch(
    anchor_id: str, anchor_state: Mapping[str, torch.Tensor],
    gradient: Sequence[torch.Tensor], branch: str, counts: dict[str, int],
    meter: BoundaryMeter,
) -> tuple[dict[int, dict[str, torch.Tensor]], dict[str, Any], list[dict[str, Any]]]:
    actor = _new_actor(anchor_id, anchor_state)
    named = _actor_parameters(actor)
    optimizer = torch.optim.Adam([parameter for _, parameter in named], lr=ADAM_LR)
    initial_actor_equal = all(
        torch.equal(value, actor.state_dict()[name]) for name, value in anchor_state.items()
    )
    empty_optimizer_state = not optimizer.state
    value_before = {
        name: value.clone() for name, value in anchor_state.items() if name.startswith("value.")
    }
    fixed = tuple(value.detach().clone() for value in gradient)
    fixed_before = tuple(value.clone() for value in fixed)
    endpoints: dict[int, dict[str, torch.Tensor]] = {}
    step_rows: list[dict[str, Any]] = []
    key = ("receiver_optimizer_calls" if branch == RECEIVER_ADDRESSED
           else "source_control_optimizer_calls")
    for step_index in range(1, 17):
        for (_, parameter), value in zip(named, fixed):
            parameter.grad = value.to(dtype=parameter.dtype).clone()
        gradient_equal_before = all(
            torch.equal(parameter.grad, value)
            for (_, parameter), value in zip(named, fixed_before)
        )
        optimizer.step()
        gradient_equal_after = all(
            torch.equal(parameter.grad, value)
            for (_, parameter), value in zip(named, fixed_before)
        )
        counts["optimizer_calls"] += 1
        counts[key] += 1
        meter.check("adam")
        state = _clone_state(actor)
        value_unchanged = all(
            torch.equal(value, state[name]) for name, value in value_before.items()
        )
        displacement, ratio = endpoint_displacement(anchor_state, state)
        optimizer_steps = {
            int(item["step"].item()) for item in optimizer.state.values()
        }
        step_rows.append({
            "anchor_id": anchor_id,
            "branch": branch,
            "step_index": step_index,
            "optimizer_state_steps": sorted(optimizer_steps),
            "same_fixed_gradient_before_step": gradient_equal_before,
            "same_fixed_gradient_after_step": gradient_equal_after,
            "value_parameters_unchanged": value_unchanged,
            "actual_l2_displacement": displacement,
            "actual_displacement_ratio_vs_initialization": ratio,
        })
        if step_index in MANDATORY_STEPS:
            endpoints[step_index] = state
    fixed_unchanged = all(torch.equal(value, before)
                          for value, before in zip(fixed, fixed_before))
    facts = {
        "anchor_id": anchor_id,
        "branch": branch,
        "optimizer": "Adam",
        "learning_rate": ADAM_LR,
        "initial_actor_tensor_equal_to_anchor": initial_actor_equal,
        "empty_optimizer_state_before": empty_optimizer_state,
        "separate_optimizer_instance": True,
        "fixed_gradient_tensor_equal_before_vs_after_16_steps": fixed_unchanged,
        "all_step_gradient_equalities": all(
            row["same_fixed_gradient_before_step"]
            and row["same_fixed_gradient_after_step"] for row in step_rows
        ),
        "value_parameters_unchanged": all(
            row["value_parameters_unchanged"] for row in step_rows
        ),
        "gradient_recomputations": 0,
        "actor_path_parameter_names": [name for name, _ in named],
    }
    return endpoints, facts, step_rows


def _evaluate(
    anchor_id: str, state: Mapping[str, torch.Tensor], profile: str, root_id: int,
    root_index: int, endpoint: str, body: str,
) -> EvaluationEpisode:
    episode = b9r1._run_episode(
        _new_actor(anchor_id, state), profile, root_id, body,
        shock_seed=root_id + 3_000_000,
        action_noise_seed=root_id + 4_000_000,
        shock_tuple=None,
    )
    rewards = [
        episode.steps[index].reward
        for start, stop, _ in b9r1.CRITICAL_SEGMENTS for index in range(start, stop)
    ]
    return EvaluationEpisode(
        anchor_id, profile, root_id, root_index, endpoint, body,
        float(np.mean(np.asarray(rewards, dtype=np.float64))),
        episode.lifecycle, episode.action_noise, episode.shocks,
        tuple(step.active_mask for step in episode.steps),
    )


def contrast_cells(rows: Sequence[EvaluationEpisode]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, int], list[EvaluationEpisode]] = {}
    for row in rows:
        grouped.setdefault(
            (row.anchor_id, row.profile, row.root_index, row.heldout_root), []
        ).append(row)
    expected = {(endpoint, body) for endpoint in ENDPOINTS for body in EVALUATION_BODIES}
    cells: list[dict[str, Any]] = []
    for key, group in grouped.items():
        if len(group) != 14 or {(row.endpoint, row.body) for row in group} != expected:
            raise RuntimeError("evaluation cell is incomplete")
        first = group[0]
        matched = all(
            row.shocks == first.shocks
            and row.lifecycle == first.lifecycle
            and np.array_equal(row.action_noise, first.action_noise)
            and all(np.array_equal(a, b) for a, b in zip(row.active_masks, first.active_masks))
            for row in group[1:]
        )
        if not matched:
            raise RuntimeError("cell root/shock/lifecycle/noise/boundary matching failed")
        values = {(row.endpoint, row.body): row.critical_reward_mean for row in group}
        phi_0 = values[("0", "CORRECT")] - values[("0", "SWAPPED")]
        cell: dict[str, Any] = {
            "anchor_id": key[0],
            "initialization_seed": ANCHOR_SEEDS[key[0]],
            "profile": key[1],
            "root_index": key[2],
            "heldout_root": key[3],
            "Y": {endpoint: {
                body: values[(endpoint, body)] for body in EVALUATION_BODIES
            } for endpoint in ENDPOINTS},
            "phi_0": phi_0,
            "matched_root_shock_lifecycle_action_noise_boundaries": True,
        }
        for step in MANDATORY_STEPS:
            r, s = f"R{step}", f"S{step}"
            phi_r = values[(r, "CORRECT")] - values[(r, "SWAPPED")]
            phi_s = values[(s, "CORRECT")] - values[(s, "SWAPPED")]
            cell.update({
                f"phi_R{step}": phi_r,
                f"phi_S{step}": phi_s,
                f"Delta_R{step}": phi_r - phi_0,
                f"J_{step}": phi_r - phi_s,
                f"R_{step}_v0": values[(r, "CORRECT")] - values[("0", "CORRECT")],
                f"R_{step}_vS": values[(r, "CORRECT")] - values[(s, "CORRECT")],
                f"S_{step}_v0": values[(s, "CORRECT")] - values[("0", "CORRECT")],
            })
        cells.append(cell)
    return sorted(cells, key=lambda row: (
        row["anchor_id"], row["profile"], row["root_index"]
    ))


def _aggregate(cells: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not cells:
        raise RuntimeError("aggregate is empty")
    return {
        metric: float(np.mean([float(cell[metric]) for cell in cells]))
        for metric in METRICS
    }


def robust_aggregates(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(cells) != 72:
        raise RuntimeError("full result does not contain 72 cells")
    return {
        "global": _aggregate(cells),
        "by_initialization": {
            anchor: _aggregate([cell for cell in cells if cell["anchor_id"] == anchor])
            for anchor in ANCHOR_IDS
        },
        "leave_one_profile": {
            profile: _aggregate([cell for cell in cells if cell["profile"] != profile])
            for profile in PROFILE_NAMES
        },
        "leave_one_root": {
            str(index): _aggregate([cell for cell in cells if cell["root_index"] != index])
            for index in range(8)
        },
    }


def select_branch(aggregates: Mapping[str, Any], *, valid: bool = True) -> str:
    if not valid:
        return INVALID_BRANCH
    try:
        robust_rows: list[Mapping[str, float]] = [aggregates["global"]]
        for family in ("by_initialization", "leave_one_profile", "leave_one_root"):
            robust_rows.extend(aggregates[family].values())
        absolute_rows = [aggregates["global"], *aggregates["by_initialization"].values()]
        values = np.asarray([
            float(row[metric]) for row in robust_rows for metric in METRICS
        ], dtype=np.float64)
    except (KeyError, TypeError, ValueError):
        return INVALID_BRANCH
    if values.size == 0 or not np.isfinite(values).all():
        return INVALID_BRANCH
    if (all(row["J_16"] > 0.0 and row["Delta_R16"] > 0.0 for row in robust_rows)
            and all(row["R_16_v0"] >= 0.0 and row["R_16_vS"] >= 0.0
                    for row in absolute_rows)):
        return EDGE_BRANCH
    return NOT_SUPPORTED_BRANCH


def _anchor_summary(
    anchor_id: str, anchor_state: Mapping[str, torch.Tensor],
    endpoint_states: Mapping[str, Mapping[str, torch.Tensor]],
    common: Mapping[str, Any], branch_facts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    displacements: dict[str, Any] = {}
    for endpoint, state in endpoint_states.items():
        displacement, ratio = endpoint_displacement(anchor_state, state)
        displacements[endpoint] = {
            "actual_l2_displacement": displacement,
            "actual_displacement_ratio_vs_initialization": ratio,
        }
    return {
        "anchor_id": anchor_id,
        "initialization_seed": ANCHOR_SEEDS[anchor_id],
        "exposure": exposure_for_anchor(anchor_id),
        "endpoint_displacements": displacements,
        "common_batch": dict(common),
        "branch_initial_and_fixed_gradient_facts": [dict(row) for row in branch_facts],
    }


def _run_science(
    plan: RunPlan, meter: BoundaryMeter, progress: RunProgress,
    repository_root: Path,
) -> dict[str, Any]:
    tapes = load_collection_tapes(repository_root)
    endpoint_states: dict[str, dict[str, Mapping[str, torch.Tensor]]] = {}
    anchor_rows: list[dict[str, Any]] = []
    all_step_rows: list[dict[str, Any]] = []
    for anchor_id in plan.anchors:
        progress.phase = f"collection:{anchor_id}"
        anchor = _new_actor(anchor_id)
        anchor_state = _clone_state(anchor)
        trajectories: list[b9r1.Episode] = []
        anchor_tapes = [row for row in tapes if row["anchor_id"] == anchor_id]
        if len(anchor_tapes) != 12:
            raise RuntimeError("manifest does not supply 12 ordered tapes for anchor")
        for row in anchor_tapes:
            root_id = int(row["collection_root"])
            trajectories.append(b9r1._run_episode(
                anchor, str(row["profile"]), root_id, "CORRECT",
                shock_seed=root_id + 1_000_000,
                action_noise_seed=root_id + 2_000_000,
                shock_tuple=tuple(row["forced_critical_shock_tuple"]),
            ))
            _record_episode(progress.counts, "collection")
            meter.check("episode")
        progress.phase = f"common_fixed_gradients:{anchor_id}"
        gradients, common = _common_fixed_gradients(anchor, trajectories)
        progress.counts["gradient_computations"] += 2
        states: dict[str, Mapping[str, torch.Tensor]] = {"0": anchor_state}
        branch_facts: list[Mapping[str, Any]] = []
        for branch, prefix in ((RECEIVER_ADDRESSED, "R"), (SOURCE_CONTROL, "S")):
            progress.phase = f"fixed_adam:{anchor_id}:{prefix}"
            retained, facts, step_rows = _apply_fixed_gradient_branch(
                anchor_id, anchor_state, gradients[branch], branch,
                progress.counts, meter,
            )
            branch_facts.append(facts)
            all_step_rows.extend(step_rows)
            states.update({f"{prefix}{step}": retained[step] for step in MANDATORY_STEPS})
        if not all(fact["initial_actor_tensor_equal_to_anchor"]
                   and fact["empty_optimizer_state_before"]
                   and fact["fixed_gradient_tensor_equal_before_vs_after_16_steps"]
                   and fact["all_step_gradient_equalities"]
                   and fact["value_parameters_unchanged"] for fact in branch_facts):
            raise RuntimeError("initial/fixed-gradient/value invariant failed")
        if set(states) != set(ENDPOINTS):
            raise RuntimeError("mandatory endpoint state missing")
        endpoint_states[anchor_id] = states
        anchor_rows.append(_anchor_summary(
            anchor_id, anchor_state, states, common, branch_facts
        ))
    evaluation_rows: list[EvaluationEpisode] = []
    for anchor_id in plan.anchors:
        for profile in plan.evaluation_profiles:
            for root_index, root_id in enumerate(plan.heldout_roots):
                for endpoint in ENDPOINTS:
                    for body in EVALUATION_BODIES:
                        progress.phase = (
                            f"evaluation:{anchor_id}:{profile}:{root_index}:{endpoint}:{body}"
                        )
                        evaluation_rows.append(_evaluate(
                            anchor_id, endpoint_states[anchor_id][endpoint], profile,
                            root_id, root_index, endpoint, body,
                        ))
                        _record_episode(progress.counts, "evaluation")
                        meter.check("episode")
    progress.phase = "counts"
    if progress.counts != plan.expected_counts():
        raise RuntimeError("exact count mismatch")
    if len(all_step_rows) != plan.expected_counts()["optimizer_calls"]:
        raise RuntimeError("step-row count mismatch")
    progress.phase = "cells"
    cells = contrast_cells(evaluation_rows)
    if not all(np.isfinite(float(cell[metric])) for cell in cells for metric in METRICS):
        raise RuntimeError("nonfinite required observable")
    if plan.mode == "full":
        progress.phase = "aggregates"
        aggregates = robust_aggregates(cells)
        progress.phase = "branch"
        branch = select_branch(aggregates)
        if branch == INVALID_BRANCH:
            raise RuntimeError("terminal branch inputs invalid")
        status = "VALID_COMPLETE"
    else:
        aggregates, branch, status = {"global": _aggregate(cells)}, "SMOKE_COMPLETE", "SMOKE_COMPLETE"
    progress.phase = "complete"
    return {
        "status": status,
        "branch": branch,
        "counts": dict(progress.counts),
        "cells": cells,
        "aggregates": aggregates,
        "anchors": anchor_rows,
        "optimizer_step_rows": all_step_rows,
        "common_trajectory_and_complete_score_identity": all(
            row["common_batch"]["same_complete_score_tensor_contracted_for_both_branches"]
            for row in anchor_rows
        ),
    }


def _checkout_head(repository_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def run_experiment(
    *, mode: str, seed: int, run_root: Path, repository_root: Path,
    exact_command: Sequence[str],
) -> dict[str, Any]:
    run_root.mkdir(parents=True, exist_ok=True)
    meter = BoundaryMeter.start()
    progress = RunProgress(empty_counts())
    plan = FULL_PLAN if mode == "full" else SMOKE_PLAN
    summary: dict[str, Any] = {
        "object": "EOCIV-B10-RECEIVER-CREDIT-FROZEN-SCORE-EXPOSURE-CURVE",
        "evidence_class": "B / EXPLORE" if mode == "full" else "NONE / SMOKE_ONLY",
        "result_bearing": mode == "full",
        "mode": mode,
        "launch_sha": _checkout_head(repository_root),
        "exact_command": subprocess.list2cmdline(list(exact_command)),
        "seed": seed,
        "seed_semantics": {
            "role": "object reproduction/root-set selector",
            "registered_selector": ROOT_SET_SELECTOR,
            "does_not_change_anchor_initialization_seeds": True,
            "anchor_initialization_seeds": dict(ANCHOR_SEEDS),
        },
        "cost_law": {
            "full": "M = 1044 * 48 real transitions + 96 fixed-gradient Adam actor steps",
            "full_episodes": 1044,
            "full_transitions_and_policy_calls": 50_112,
            "full_actor_optimizer_calls": 96,
            "swept_quantity": "none; one fixed finite grid",
        },
        "exposure": {anchor: exposure_for_anchor(anchor) for anchor in ANCHOR_IDS},
    }
    if mode == "smoke":
        summary["scientific_polarity"] = None
    try:
        if seed != ROOT_SET_SELECTOR:
            raise ValueError(f"root-set selector must be {ROOT_SET_SELECTOR}; got {seed}")
        summary.update(_run_science(plan, meter, progress, repository_root))
    except Exception as exc:
        summary.update({
            "status": INVALID_BRANCH,
            "branch": INVALID_BRANCH,
            "scientific_polarity": None,
            "counts": dict(progress.counts),
            "failure_phase": progress.phase,
            "failure_type": type(exc).__name__,
            "failure_reason": str(exc),
        })
    telemetry = meter.telemetry()
    episodes = progress.counts["episodes"]
    summary["telemetry"] = telemetry
    summary["cost_law"].update({
        "measured_wall_seconds_per_episode": (
            telemetry["wall_seconds"] / episodes if episodes else None
        ),
        "measured_process_cpu_seconds_per_episode": (
            telemetry["process_cpu_seconds"] / episodes if episodes else None
        ),
    })
    (run_root / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary
