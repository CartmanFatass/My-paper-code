"""EOCIV-B9R1 receiver-addressed one-step experiment.

This attempt owns its scientific path. It uses the real sibling environment
and existing actor model, but no historical B9 runner, digest, receipt,
readiness, resource guard, result lifecycle, or artifact.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import real_valve_learning as learner
from experiments.candidates.eociv_lite import sibling_env as sibling


RECEIVER_ADDRESSED = "RECEIVER_ADDRESSED"
SOURCE_CONTROL = "AUTHENTICATED_SOURCE_ADDRESSED_CONTROL"
ADDRESSING_BRANCHES = (RECEIVER_ADDRESSED, SOURCE_CONTROL)
ANCHOR_IDS = ("A0", "A1")
ANCHOR_SEEDS = {"A0": 990_031, "A1": 990_032}
PROFILE_NAMES = ("train_4_3_6_5", "train_5_3_7_6", "train_6_4_8_6")
PROFILE_BY_NAME = {profile.name: profile for profile in learner.PROFILES}
SHOCK_TUPLES = (
    (sibling.SHOCK_A, sibling.SHOCK_A),
    (sibling.SHOCK_A, sibling.SHOCK_B),
    (sibling.SHOCK_B, sibling.SHOCK_A),
    (sibling.SHOCK_B, sibling.SHOCK_B),
)
COLLECTION_ROOTS = {
    (anchor, profile): tuple(
        990_100 + anchor_index * 100 + profile_index * 10 + shock_index
        for shock_index in range(4)
    )
    for anchor_index, anchor in enumerate(ANCHOR_IDS)
    for profile_index, profile in enumerate(PROFILE_NAMES)
}
HELDOUT_ROOTS = tuple(range(991_001, 991_009))
ENDPOINTS = ("0", "R", "S")
EVALUATION_BODIES = ("CORRECT", "SWAPPED")
HORIZON = 48
CRITICAL_SEGMENTS = ((12, 24, 0), (36, 48, 2))
GAMMA = 0.99
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8
ADAM_LR = 3e-4
ACTIVE_ACTOR_PARAMETER_NAMES = (
    "log_std", "obs.weight", "recurrent.weight", "actor.weight", "actor.bias",
    "content_embedding.weight",
)
ROOT_SET_SELECTOR = 991_001
CPU_TIME_CAP_SECONDS = 300.0
VALID_BRANCHES = (
    "B9R1_RECEIVER_ADDRESSED_SEMANTIC_EDGE",
    "B9R1_GENERIC_OR_SOURCE_HARM_ONLY",
    "B9R1_RECEIVER_NOT_SUPPORTED",
    "B9R1_MIXED_UNIDENTIFIED",
)
INVALID_BRANCH = "INVALID_ATTEMPT"
METRICS = (
    "phi_0", "phi_R", "phi_S", "Delta_R", "J",
    "receiver_correct_vs_anchor", "receiver_correct_vs_source",
    "source_correct_vs_anchor", "receiver_two_arm_generic_gain",
)


class CpuTimeLimitExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredStep:
    observations: np.ndarray
    active_mask: np.ndarray
    effective_slot_block: np.ndarray
    noise: np.ndarray
    reward: float


@dataclass(frozen=True)
class Episode:
    steps: tuple[StoredStep, ...]
    critical_edges: Mapping[int, sibling.EdgeIdentity]
    lifecycle: tuple[sibling.EdgeIdentity, ...]
    action_noise: np.ndarray
    shocks: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationEpisode:
    anchor_id: str
    profile: str
    heldout_root: int
    root_index: int
    endpoint: str
    body: str
    critical_reward_mean: float
    lifecycle: tuple[sibling.EdgeIdentity, ...]
    action_noise: np.ndarray
    shocks: tuple[str, ...]


@dataclass(frozen=True)
class RunPlan:
    mode: str
    anchors: tuple[str, ...]
    evaluation_profiles: tuple[str, ...]
    heldout_roots: tuple[int, ...]

    @property
    def collection_episodes(self) -> int:
        return len(self.anchors) * len(PROFILE_NAMES) * len(SHOCK_TUPLES)

    @property
    def evaluation_episodes(self) -> int:
        return (len(self.anchors) * len(self.evaluation_profiles)
                * len(self.heldout_roots) * len(ENDPOINTS) * len(EVALUATION_BODIES))

    def expected_counts(self) -> dict[str, int]:
        episodes = self.collection_episodes + self.evaluation_episodes
        return {
            "episodes": episodes,
            "environment_transitions": episodes * HORIZON,
            "policy_calls": episodes * HORIZON,
            "collection_episodes": self.collection_episodes,
            "evaluation_episodes": self.evaluation_episodes,
            "optimizer_calls": len(self.anchors) * 2,
            "receiver_optimizer_calls": len(self.anchors),
            "source_control_optimizer_calls": len(self.anchors),
            "global_clip_calls": 0, "critic_loss_calls": 0,
            "value_gradient_calls": 0, "second_updates": 0, "retry": 0,
            "rescue": 0, "sweep": 0, "checkpoint_selection": 0,
            "k_search": 0, "hypothetical_transitions": 0,
        }


FULL_PLAN = RunPlan("full", ANCHOR_IDS, PROFILE_NAMES, HELDOUT_ROOTS)
SMOKE_PLAN = RunPlan("smoke", ("A0",), (PROFILE_NAMES[0],), (HELDOUT_ROOTS[0],))


def empty_counts() -> dict[str, int]:
    return {key: 0 for key in FULL_PLAN.expected_counts()}


@dataclass
class RunProgress:
    counts: dict[str, int]
    phase: str = "initialization"


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def windows_peak_rss_bytes() -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes, kernel32.GetCurrentProcess.restype = [], ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.c_void_p, ctypes.POINTER(_ProcessMemoryCounters), ctypes.c_ulong,
    ]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
    return int(counters.PeakWorkingSetSize)


def peak_rss_bytes() -> int:
    if os.name == "nt":
        return windows_peak_rss_bytes()
    import resource
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


@dataclass
class EpisodeBoundaryMeter:
    wall_start: float
    cpu_start: float
    peak_rss: int | None
    rss_error: str | None
    rss_failed: bool
    episode_boundaries: int = 0

    @classmethod
    def start(cls) -> "EpisodeBoundaryMeter":
        try:
            return cls(time.perf_counter(), time.process_time(), peak_rss_bytes(), None, False)
        except OSError as exc:
            return cls(time.perf_counter(), time.process_time(), None, str(exc), True)

    def check(self) -> None:
        self.episode_boundaries += 1
        try:
            observed = peak_rss_bytes()
            self.peak_rss = observed if self.peak_rss is None else max(self.peak_rss, observed)
        except OSError as exc:
            self.rss_failed, self.rss_error = True, str(exc)
        if self.process_cpu_seconds() > CPU_TIME_CAP_SECONDS:
            raise CpuTimeLimitExceeded(
                f"process CPU exceeded {CPU_TIME_CAP_SECONDS:.0f}s at episode boundary"
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
            "cpu_cap_checked_only_at_episode_boundaries": True,
            "episode_boundaries_observed": self.episode_boundaries,
        }


def _slot_features(slot: bytes) -> np.ndarray:
    if len(slot) != sibling.PAYLOAD_SLOT_BYTES:
        raise ValueError("slot width changed")
    return np.frombuffer(slot, dtype=np.uint8).astype(np.float32) / np.float32(255.0)


def _correct_body(event_index: int, env: sibling.EocivSiblingRosterEnv) -> bytes:
    return (sibling.NEUTRAL_TOKEN if sibling.CELL_CLASS[event_index] == "NEUTRAL"
            else env.focal_payload(event_index))


def _swapped_body(event_index: int, env: sibling.EocivSiblingRosterEnv) -> bytes:
    body = _correct_body(event_index, env)
    if body == sibling.NEUTRAL_TOKEN:
        return body
    a, b = (sibling.real_payload_body(value) for value in (sibling.SHOCK_A, sibling.SHOCK_B))
    if body == a:
        return b
    if body == b:
        return a
    raise RuntimeError("critical payload outside A/B support")


BODY_FN = {"CORRECT": _correct_body, "SWAPPED": _swapped_body}


def _new_actor(
    anchor_id: str, state: Mapping[str, torch.Tensor] | None = None
) -> learner.RecurrentActorCritic:
    capacities = {PROFILE_BY_NAME[name].member_capacity for name in PROFILE_NAMES}
    if len(capacities) != 1:
        raise RuntimeError("profiles do not share actor capacity")
    actor = learner.RecurrentActorCritic(
        capacities.pop(), ANCHOR_SEEDS[anchor_id], encoder_kind="content_separating"
    )
    if state is not None:
        actor.load_state_dict(state, strict=True)
    return actor


def _clone_state(actor: learner.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {name: value.detach().cpu().clone() for name, value in actor.state_dict().items()}


def _make_env(
    profile: roster_env.RosterProfile, root_id: int, shock_seed: int,
    shock_tuple: tuple[str, str] | None,
) -> sibling.EocivSiblingRosterEnv:
    world_seed = sibling.profile_stream_identity(
        sibling.BASE_WORLD_STREAM, learner.MASTER_SEED, profile.name
    )
    ledger = roster_env.make_ledger(root_id, master_seed=world_seed, profile=profile)
    shocks = None if shock_tuple is None else (
        shock_tuple[0], sibling.SHOCK_NONE, shock_tuple[1]
    )
    return sibling.EocivSiblingRosterEnv(
        ledger, sibling_seed=shock_seed, shock_states=shocks
    )


def _run_episode(
    actor: learner.RecurrentActorCritic, profile_name: str, root_id: int, body: str,
    *, shock_seed: int, action_noise_seed: int,
    shock_tuple: tuple[str, str] | None,
) -> Episode:
    profile = PROFILE_BY_NAME[profile_name]
    env = _make_env(profile, root_id, shock_seed, shock_tuple)
    noise_seed = sibling.profile_stream_identity(
        sibling.ACTION_NOISE_STREAM, action_noise_seed, profile.name
    )
    noise = roster_env.make_action_noise(
        [root_id], action_seed=noise_seed, member_capacity=profile.member_capacity
    )[:, 0, :, :]
    hidden = actor.initial_state()
    latch = np.zeros((profile.member_capacity, sibling.PAYLOAD_SLOT_BYTES), dtype=np.float32)
    steps: list[StoredStep] = []
    edges: dict[int, sibling.EdgeIdentity] = {}
    for time_index in range(HORIZON):
        event_index = sibling.EVENT_TIMES.index(time_index) if time_index in sibling.EVENT_TIMES else None
        if event_index is not None:
            opportunity = env.opportunity(event_index)
            if not opportunity.eligible:
                raise RuntimeError("critical endpoint is not authenticated and active")
            actuation = sibling.actuate(
                "LR", opportunity, BODY_FN[body](event_index, env),
                d_learned=True, d_control=False,
            )
            if actuation.route != "REAL":
                raise RuntimeError("LR did not deliver the real registered body")
            latch.fill(np.float32(0.0))
            latch[opportunity.identity.receiver_member_key] = _slot_features(actuation.slot)
            edges[time_index] = opportunity.identity
        view = env.observe()
        latch[~view.active_mask] = np.float32(0.0)
        effective = latch.copy()
        actions, _, hidden = actor.forward(
            view.observations, view.active_mask, effective, hidden, noise[time_index]
        )
        env.step(actions)
        steps.append(StoredStep(
            np.asarray(view.observations, dtype=np.float64).copy(),
            np.asarray(view.active_mask, dtype=np.bool_).copy(), effective,
            np.asarray(noise[time_index], dtype=np.float32).copy(),
            float(env.reward_trace[-1]),
        ))
    for start, stop, _ in CRITICAL_SEGMENTS:
        edge = edges[start]
        for step in steps[start:stop]:
            if not np.any(step.effective_slot_block[edge.receiver_member_key]):
                raise RuntimeError("receiver lost its segment latch")
            nonreceiver = step.effective_slot_block.copy()
            nonreceiver[edge.receiver_member_key] = np.float32(0.0)
            if np.any(nonreceiver) or np.any(step.effective_slot_block[edge.source_member_key]):
                raise RuntimeError("delivered content was not receiver-owned")
    return Episode(
        tuple(steps), edges, tuple(edges[t] for t in sibling.EVENT_TIMES),
        noise.copy(), tuple(env._shock_states),
    )


def _record_episode(counts: dict[str, int], kind: str) -> None:
    counts["episodes"] += 1
    counts[f"{kind}_episodes"] += 1
    counts["environment_transitions"] += HORIZON
    counts["policy_calls"] += HORIZON


def _normalized_gae(rewards: Sequence[float], values: Sequence[torch.Tensor]) -> torch.Tensor:
    reward = torch.as_tensor(tuple(rewards), dtype=torch.float32)
    value = torch.stack(tuple(values)).detach()
    next_value = torch.cat((value[1:], torch.zeros_like(value[-1:])))
    deltas = reward + GAMMA * next_value - value
    raw, carry = torch.empty_like(deltas), torch.zeros((), dtype=torch.float32)
    for index in range(HORIZON - 1, -1, -1):
        carry = deltas[index] + GAMMA * GAE_LAMBDA * carry
        raw[index] = carry
    return ((raw - raw.mean()) / torch.clamp(
        raw.std(unbiased=False), min=NORMALIZATION_EPSILON
    )).detach()


def _addressed_loss(
    score_rows: Sequence[torch.Tensor], active_masks: Sequence[np.ndarray],
    credits: torch.Tensor, edges: Mapping[int, sibling.EdgeIdentity], branch: str,
) -> tuple[torch.Tensor, list[int]]:
    terms: list[torch.Tensor] = []
    order: list[int] = []
    for start, stop, _ in CRITICAL_SEGMENTS:
        edge = edges[start]
        member = (edge.receiver_member_key if branch == RECEIVER_ADDRESSED
                  else edge.source_member_key)
        for time_index in range(start, stop):
            if not active_masks[time_index][member]:
                raise RuntimeError("addressed score row is inactive")
            terms.append(-(score_rows[time_index][member] * credits[time_index]))
            order.append(time_index)
    if len(terms) != 24:
        raise RuntimeError("trajectory lacks 24 addressed terms")
    return torch.stack(terms).mean(), order


def _actor_parameters(
    actor: learner.RecurrentActorCritic,
) -> tuple[tuple[str, torch.nn.Parameter], ...]:
    available = dict(actor.named_parameters())
    return tuple((name, available[name]) for name in ACTIVE_ACTOR_PARAMETER_NAMES)


def _common_gradients(
    actor: learner.RecurrentActorCritic, trajectories: Sequence[Episode]
) -> tuple[dict[str, tuple[torch.Tensor, ...]], dict[str, Any]]:
    receiver_losses: list[torch.Tensor] = []
    source_losses: list[torch.Tensor] = []
    common_orders_equal, term_count = True, 0
    for trajectory in trajectories:
        previous = torch.zeros((actor.capacity, actor.hidden_dim), dtype=torch.float32)
        scores: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        masks: list[np.ndarray] = []
        for step in trajectory.steps:
            _, mean, hidden, mask = actor._step_tensors(
                step.observations, step.active_mask, step.effective_slot_block,
                previous, step.noise,
            )
            std = torch.exp(torch.clamp(actor.log_std, -4.0, 1.0))
            raw = mean + std * torch.as_tensor(step.noise, dtype=torch.float32)
            scores.append(torch.distributions.Normal(mean, std).log_prob(raw.detach()).sum(-1))
            values.append(actor.value(hidden[mask].mean(0)).squeeze(-1))
            masks.append(mask.detach().cpu().numpy().astype(np.bool_))
            previous = hidden
        credits = _normalized_gae([step.reward for step in trajectory.steps], values)
        receiver, receiver_order = _addressed_loss(
            scores, masks, credits, trajectory.critical_edges, RECEIVER_ADDRESSED
        )
        source, source_order = _addressed_loss(
            scores, masks, credits, trajectory.critical_edges, SOURCE_CONTROL
        )
        common_orders_equal &= receiver_order == source_order
        term_count += len(receiver_order)
        receiver_losses.append(receiver)
        source_losses.append(source)
    parameters = tuple(parameter for _, parameter in _actor_parameters(actor))
    receiver_gradient = torch.autograd.grad(
        torch.stack(receiver_losses).mean(), parameters, retain_graph=True
    )
    source_gradient = torch.autograd.grad(torch.stack(source_losses).mean(), parameters)
    gradients = {
        RECEIVER_ADDRESSED: tuple(value.detach().clone() for value in receiver_gradient),
        SOURCE_CONTROL: tuple(value.detach().clone() for value in source_gradient),
    }
    norm = lambda values: float(torch.linalg.vector_norm(
        torch.cat([value.reshape(-1) for value in values])
    ))
    return gradients, {
        "trajectory_count": len(trajectories), "term_count": term_count,
        "same_trajectory_score_tensors": common_orders_equal,
        "gradients_computed_before_mutation": True,
        "receiver_gradient_norm": norm(receiver_gradient),
        "source_gradient_norm": norm(source_gradient),
    }


def _apply_actor_step(
    anchor_id: str, anchor_state: Mapping[str, torch.Tensor],
    gradient: Sequence[torch.Tensor], branch: str, counts: dict[str, int],
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    actor = _new_actor(anchor_id, anchor_state)
    named = _actor_parameters(actor)
    optimizer = torch.optim.Adam([parameter for _, parameter in named], lr=ADAM_LR)
    empty_before = not optimizer.state
    value_before = {
        name: value.clone() for name, value in anchor_state.items() if name.startswith("value.")
    }
    for (_, parameter), value in zip(named, gradient):
        parameter.grad = value.to(parameter.dtype).clone()
    optimizer.step()
    state = _clone_state(actor)
    value_unchanged = all(torch.equal(value, state[name]) for name, value in value_before.items())
    counts["optimizer_calls"] += 1
    key = ("receiver_optimizer_calls" if branch == RECEIVER_ADDRESSED
           else "source_control_optimizer_calls")
    counts[key] += 1
    return state, {
        "branch": branch, "optimizer": "Adam", "learning_rate": ADAM_LR,
        "empty_state_before": empty_before, "step_index_after": 1,
        "actor_path_parameter_names": [name for name, _ in named],
        "value_head_unchanged": value_unchanged,
        "global_clip_calls": 0, "critic_loss_calls": 0,
    }


def exposure_for_anchor(anchor_id: str) -> dict[str, Any]:
    actor = _new_actor(anchor_id)
    flat = torch.cat([
        parameter.detach().reshape(-1).double() for _, parameter in _actor_parameters(actor)
    ])
    count, initial_l2 = int(flat.numel()), float(torch.linalg.vector_norm(flat))
    upper = float(ADAM_LR * math.sqrt(count))
    return {
        "anchor_id": anchor_id, "initialization_seed": ANCHOR_SEEDS[anchor_id],
        "active_parameter_names": list(ACTIVE_ACTOR_PARAMETER_NAMES),
        "active_parameter_count": count, "initial_active_parameter_l2": initial_l2,
        "one_step_adam_l2_upper_bound": upper,
        "upper_bound_ratio_vs_initialization": upper / initial_l2,
    }


def endpoint_displacement(
    anchor_state: Mapping[str, torch.Tensor], endpoint_state: Mapping[str, torch.Tensor]
) -> tuple[float, float]:
    before = torch.cat([anchor_state[name].reshape(-1).double()
                        for name in ACTIVE_ACTOR_PARAMETER_NAMES])
    after = torch.cat([endpoint_state[name].reshape(-1).double()
                       for name in ACTIVE_ACTOR_PARAMETER_NAMES])
    displacement = float(torch.linalg.vector_norm(after - before))
    return displacement, displacement / float(torch.linalg.vector_norm(before))


def _evaluate(
    anchor_id: str, state: Mapping[str, torch.Tensor], profile: str, root_id: int,
    root_index: int, endpoint: str, body: str,
) -> EvaluationEpisode:
    episode = _run_episode(
        _new_actor(anchor_id, state), profile, root_id, body,
        shock_seed=root_id + 3_000_000, action_noise_seed=root_id + 4_000_000,
        shock_tuple=None,
    )
    rewards = [episode.steps[index].reward for start, stop, _ in CRITICAL_SEGMENTS
               for index in range(start, stop)]
    return EvaluationEpisode(
        anchor_id, profile, root_id, root_index, endpoint, body,
        float(np.mean(np.asarray(rewards, dtype=np.float64))), episode.lifecycle,
        episode.action_noise, episode.shocks,
    )


def contrast_cells(rows: Sequence[EvaluationEpisode]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int, int], list[EvaluationEpisode]] = {}
    for row in rows:
        grouped.setdefault(
            (row.anchor_id, row.profile, row.root_index, row.heldout_root), []
        ).append(row)
    cells: list[dict[str, Any]] = []
    expected = {(endpoint, body) for endpoint in ENDPOINTS for body in EVALUATION_BODIES}
    for key, group in grouped.items():
        if {(row.endpoint, row.body) for row in group} != expected or len(group) != 6:
            raise RuntimeError("evaluation cell is incomplete")
        first = group[0]
        if any(row.shocks != first.shocks or row.lifecycle != first.lifecycle
               or not np.array_equal(row.action_noise, first.action_noise)
               for row in group[1:]):
            raise RuntimeError("cell root/shock/lifecycle/action-noise matching failed")
        values = {(row.endpoint, row.body): row.critical_reward_mean for row in group}
        phi_0 = values[("0", "CORRECT")] - values[("0", "SWAPPED")]
        phi_r = values[("R", "CORRECT")] - values[("R", "SWAPPED")]
        phi_s = values[("S", "CORRECT")] - values[("S", "SWAPPED")]
        r0 = values[("R", "CORRECT")] - values[("0", "CORRECT")]
        rs = values[("R", "CORRECT")] - values[("S", "CORRECT")]
        s0 = values[("S", "CORRECT")] - values[("0", "CORRECT")]
        cells.append({
            "anchor_id": key[0], "profile": key[1], "root_index": key[2],
            "heldout_root": key[3],
            "Y": {endpoint: {body: values[(endpoint, body)]
                              for body in EVALUATION_BODIES} for endpoint in ENDPOINTS},
            "phi_0": phi_0, "phi_R": phi_r, "phi_S": phi_s,
            "Delta_R": phi_r - phi_0, "J": phi_r - phi_s,
            "receiver_correct_vs_anchor": r0,
            "receiver_correct_vs_source": rs,
            "source_correct_vs_anchor": s0,
            "receiver_two_arm_generic_gain": 0.5 * (
                r0 + values[("R", "SWAPPED")] - values[("0", "SWAPPED")]
            ),
            "matched_root_shock_lifecycle_action_noise": True,
        })
    return sorted(cells, key=lambda row: (
        row["anchor_id"], row["profile"], row["root_index"]
    ))


def _aggregate(cells: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not cells:
        raise RuntimeError("aggregate is empty")
    return {metric: float(np.mean([float(cell[metric]) for cell in cells]))
            for metric in METRICS}


def robust_aggregates(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(cells) != 48:
        raise RuntimeError("full result does not contain 48 cells")
    return {
        "global": _aggregate(cells),
        "by_anchor": {anchor: _aggregate([
            cell for cell in cells if cell["anchor_id"] == anchor
        ]) for anchor in ANCHOR_IDS},
        "leave_one_profile": {profile: _aggregate([
            cell for cell in cells if cell["profile"] != profile
        ]) for profile in PROFILE_NAMES},
        "leave_one_root": {str(index): _aggregate([
            cell for cell in cells if cell["root_index"] != index
        ]) for index in range(8)},
    }


def select_branch(aggregates: Mapping[str, Any], *, valid: bool = True) -> str:
    if not valid:
        return INVALID_BRANCH
    try:
        rows: list[Mapping[str, float]] = [aggregates["global"]]
        for family in ("by_anchor", "leave_one_profile", "leave_one_root"):
            rows.extend(aggregates[family].values())
        values = np.asarray([float(row[metric]) for row in rows for metric in METRICS])
    except (KeyError, TypeError, ValueError):
        return INVALID_BRANCH
    if values.size == 0 or not np.isfinite(values).all():
        return INVALID_BRANCH
    global_row = aggregates["global"]
    if (all(row["J"] > 0.0 and row["Delta_R"] > 0.0 for row in rows)
            and global_row["receiver_correct_vs_anchor"] >= 0.0
            and global_row["receiver_correct_vs_source"] >= 0.0):
        return VALID_BRANCHES[0]
    if (global_row["receiver_two_arm_generic_gain"] > 0.0
            or global_row["source_correct_vs_anchor"] < 0.0
            or global_row["receiver_correct_vs_anchor"] < 0.0
            or global_row["receiver_correct_vs_source"] < 0.0
            or any(row["Delta_R"] <= 0.0 for row in rows)):
        return VALID_BRANCHES[1]
    if all(row["J"] <= 0.0 for row in aggregates["by_anchor"].values()):
        return VALID_BRANCHES[2]
    return VALID_BRANCHES[3]


def _anchor_summary(
    anchor_id: str, anchor_state: Mapping[str, torch.Tensor],
    states: Mapping[str, Mapping[str, torch.Tensor]], common: Mapping[str, Any],
    receiver_step: Mapping[str, Any], source_step: Mapping[str, Any],
) -> dict[str, Any]:
    displacements = {}
    for endpoint, branch in (("R", RECEIVER_ADDRESSED), ("S", SOURCE_CONTROL)):
        l2, ratio = endpoint_displacement(anchor_state, states[endpoint])
        displacements[endpoint] = {
            "addressing_branch": branch, "actual_l2_displacement": l2,
            "actual_displacement_ratio_vs_initialization": ratio,
        }
    return {
        "anchor_id": anchor_id, "initialization_seed": ANCHOR_SEEDS[anchor_id],
        "exposure": exposure_for_anchor(anchor_id),
        "endpoint_displacements": displacements,
        "common_trajectory_count": common["trajectory_count"],
        "common_term_count": common["term_count"],
        "same_trajectory_score_tensors": common["same_trajectory_score_tensors"],
        "gradients_computed_before_mutation": common["gradients_computed_before_mutation"],
        "receiver_gradient_norm": common["receiver_gradient_norm"],
        "source_gradient_norm": common["source_gradient_norm"],
        "receiver_step": dict(receiver_step), "source_control_step": dict(source_step),
    }


def _run_science(
    plan: RunPlan, meter: EpisodeBoundaryMeter, progress: RunProgress
) -> dict[str, Any]:
    endpoint_states: dict[str, dict[str, Mapping[str, torch.Tensor]]] = {}
    anchor_rows: list[dict[str, Any]] = []
    for anchor_id in plan.anchors:
        progress.phase = f"collection:{anchor_id}"
        anchor = _new_actor(anchor_id)
        anchor_state = _clone_state(anchor)
        trajectories: list[Episode] = []
        for profile in PROFILE_NAMES:
            for shock_index, root_id in enumerate(COLLECTION_ROOTS[(anchor_id, profile)]):
                trajectories.append(_run_episode(
                    anchor, profile, root_id, "CORRECT",
                    shock_seed=root_id + 1_000_000,
                    action_noise_seed=root_id + 2_000_000,
                    shock_tuple=SHOCK_TUPLES[shock_index],
                ))
                _record_episode(progress.counts, "collection")
                meter.check()
        progress.phase = f"gradient:{anchor_id}"
        gradients, common = _common_gradients(anchor, trajectories)
        progress.phase = f"receiver_update:{anchor_id}"
        receiver_state, receiver_step = _apply_actor_step(
            anchor_id, anchor_state, gradients[RECEIVER_ADDRESSED],
            RECEIVER_ADDRESSED, progress.counts,
        )
        progress.phase = f"source_update:{anchor_id}"
        source_state, source_step = _apply_actor_step(
            anchor_id, anchor_state, gradients[SOURCE_CONTROL], SOURCE_CONTROL,
            progress.counts,
        )
        states = {"0": anchor_state, "R": receiver_state, "S": source_state}
        endpoint_states[anchor_id] = states
        anchor_rows.append(_anchor_summary(
            anchor_id, anchor_state, states, common, receiver_step, source_step
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
                        meter.check()
    progress.phase = "counts"
    if progress.counts != plan.expected_counts():
        raise RuntimeError("exact count mismatch")
    progress.phase = "cells"
    cells = contrast_cells(evaluation_rows)
    if not all(np.isfinite(cell[metric]) for cell in cells for metric in METRICS):
        raise RuntimeError("nonfinite required observable")
    if plan.mode == "full":
        progress.phase = "aggregates"
        aggregates = robust_aggregates(cells)
        progress.phase = "branch"
        branch = select_branch(aggregates)
    else:
        aggregates, branch = {"global": _aggregate(cells)}, "SMOKE_COMPLETE"
    progress.phase = "complete"
    return {
        "status": "VALID_COMPLETE" if plan.mode == "full" else "SMOKE_COMPLETE",
        "branch": branch, "counts": dict(progress.counts), "cells": cells,
        "aggregates": aggregates, "anchors": anchor_rows,
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
    meter, progress = EpisodeBoundaryMeter.start(), RunProgress(empty_counts())
    plan = FULL_PLAN if mode == "full" else SMOKE_PLAN
    summary: dict[str, Any] = {
        "object": "EOCIV-B9R1-RECEIVER-ADDRESSED-CREDIT",
        "evidence_class": "B / EXPLORE", "mode": mode,
        "launch_sha": _checkout_head(repository_root),
        "exact_command": subprocess.list2cmdline(list(exact_command)), "seed": seed,
        "seed_semantics": {
            "role": "object reproduction/root-set selector",
            "registered_selector": ROOT_SET_SELECTOR,
            "does_not_change_actor_initialization_seeds": True,
            "actor_initialization_seeds": dict(ANCHOR_SEEDS),
        },
        "cost_law": {
            "full": "312 episodes * 48 transitions + 4 actor updates",
            "full_episodes": 312, "full_transitions_and_policy_calls": 14_976,
            "full_actor_optimizer_calls": 4,
        },
    }
    try:
        if seed != ROOT_SET_SELECTOR:
            raise ValueError(f"root-set selector must be {ROOT_SET_SELECTOR}; got {seed}")
        summary.update(_run_science(plan, meter, progress))
    except Exception as exc:
        summary.update({
            "status": INVALID_BRANCH, "branch": INVALID_BRANCH,
            "scientific_polarity": None, "counts": dict(progress.counts),
            "failure_phase": progress.phase, "failure_type": type(exc).__name__,
            "failure_reason": str(exc),
        })
    telemetry, episodes = meter.telemetry(), progress.counts["episodes"]
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
