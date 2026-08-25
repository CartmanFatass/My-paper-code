"""EOCIV-B9 receiver-addressed credit-edge candidate.

The sole intervention is the authenticated member row used by an actor-only
score-function update.  For each fresh anchor, twelve native CORRECT episodes
are collected once.  Receiver- and source-addressed gradient vectors are then
computed from the same replay graph before either exact anchor clone is
mutated.  Each clone receives one empty-state Adam step.

Importing this module performs no environment episode, learner update, file
write, predecessor-artifact read, or registered run.
"""

from __future__ import annotations

import copy
import ctypes
import hashlib
import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import torch

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import actuation_runtime as actuation
from experiments.candidates.eociv_lite import real_valve_learning as learner
from experiments.candidates.eociv_lite import recurrent_retention_learnability as retention
from experiments.candidates.eociv_lite import sibling_env as sibling


TREATMENT = "EOCIV-B9-RECEIVER-ADDRESSED-CREDIT-EDGE"
DIRECTION = "CAND-VAP-EOCIV-LITE"
RAW_OUTPUT_BINDING = "eociv_lite.receiver_addressed_credit_edge.b9.v1"
BASE_REVISION = "8144af6273145dd9c64184a654c91f0e06d521ce"
STAGE = "B_EXPLORATORY_REAL_TOY_EXPERIMENT"

RECEIVER_ADDRESSED = "RECEIVER_ADDRESSED"
SOURCE_CONTROL = "AUTHENTICATED_SOURCE_ADDRESSED_CONTROL"
ADDRESSING_BRANCHES = (RECEIVER_ADDRESSED, SOURCE_CONTROL)
ENDPOINTS = ("0", "R", "S")
EVALUATION_BODIES = ("CORRECT", "SWAPPED")

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
COLLECTION_ROOTS: Mapping[tuple[str, str], tuple[int, ...]] = {
    (anchor, profile): tuple(
        990_100 + anchor_index * 100 + profile_index * 10 + shock_index
        for shock_index in range(len(SHOCK_TUPLES))
    )
    for anchor_index, anchor in enumerate(ANCHOR_IDS)
    for profile_index, profile in enumerate(PROFILE_NAMES)
}
HELDOUT_ROOTS = tuple(range(991_001, 991_009))

HORIZON = 48
CRITICAL_SEGMENTS = ((12, 24, 0), (36, 48, 2))
GAMMA = 0.99
GAE_LAMBDA = 0.95
NORMALIZATION_EPSILON = 1e-8
ADAM_LR = 3e-4
K_SEARCH = 0
CPU_THREAD_COUNT = 1
CPU_TIME_CAP_SECONDS = 5 * 60
RSS_CAP_BYTES = 1 << 30
RESULT_RELATIVE_PATH = Path(
    "docs/research/candidates/eociv_lite/"
    "EOCIV_B9_RECEIVER_ADDRESSED_CREDIT_EDGE_RESULT.json"
)
REVISION_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
RUN_ID_PATTERN = re.compile(r"eociv-b9-[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
ACTIVE_ACTOR_PARAMETER_NAMES = (
    "log_std",
    "obs.weight",
    "recurrent.weight",
    "actor.weight",
    "actor.bias",
    "content_embedding.weight",
)

TERMINAL_BRANCHES = (
    "B9_INVALID_BINDING",
    "B9_RECEIVER_ADDRESSED_SEMANTIC_EDGE",
    "B9_GENERIC_OR_SOURCE_HARM_ONLY",
    "B9_RECEIVER_NOT_SUPPORTED",
    "B9_MIXED_UNIDENTIFIED",
)


class BindingFailure(RuntimeError):
    """A protected B9 binding, activity, finite, or resource check failed."""


@dataclass(frozen=True)
class ExecutionPlan:
    anchors: tuple[str, ...]
    profiles: tuple[str, ...]
    shock_tuples: tuple[tuple[str, str], ...]
    heldout_roots: tuple[int, ...]
    endpoints: tuple[str, ...]
    bodies: tuple[str, ...]

    @property
    def collection_episodes(self) -> int:
        return len(self.anchors) * len(self.profiles) * len(self.shock_tuples)

    @property
    def evaluation_episodes(self) -> int:
        return (
            len(self.anchors)
            * len(self.profiles)
            * len(self.heldout_roots)
            * len(self.endpoints)
            * len(self.bodies)
        )

    @property
    def optimizer_calls(self) -> int:
        return len(self.anchors) * len(ADDRESSING_BRANCHES)

    @property
    def expected_counts(self) -> dict[str, int]:
        episodes = self.collection_episodes + self.evaluation_episodes
        return {
            "episodes": episodes,
            "environment_transitions": episodes * HORIZON,
            "policy_calls": episodes * HORIZON,
            "collection_episodes": self.collection_episodes,
            "evaluation_episodes": self.evaluation_episodes,
            "optimizer_calls": self.optimizer_calls,
            "receiver_optimizer_calls": len(self.anchors),
            "source_control_optimizer_calls": len(self.anchors),
            "global_clip_calls": 0,
            "critic_loss_calls": 0,
            "value_gradient_calls": 0,
            "second_updates": 0,
            "retry": 0,
            "rescue": 0,
            "sweep": 0,
            "checkpoint_selection": 0,
            "k_search": K_SEARCH,
            "hypothetical_transitions": 0,
        }


FULL_PLAN = ExecutionPlan(
    ANCHOR_IDS, PROFILE_NAMES, SHOCK_TUPLES, HELDOUT_ROOTS, ENDPOINTS, EVALUATION_BODIES
)
FULL_EXPECTED_COUNTS = FULL_PLAN.expected_counts
_FROZEN_TOTALS = {
    "episodes": 312,
    "environment_transitions": 14_976,
    "collection_episodes": 24,
    "evaluation_episodes": 288,
    "optimizer_calls": 4,
}
if any(FULL_EXPECTED_COUNTS[key] != value for key, value in _FROZEN_TOTALS.items()):
    raise RuntimeError("B9 activity factorization drifted from the frozen totals")

_DEPENDENCY_LITERALS = {
    "horizon": int(roster_env.HORIZON),
    "event_times": tuple(int(value) for value in sibling.EVENT_TIMES),
    "segment_length": int(sibling.SEGMENT_LENGTH),
    "gamma": float(learner.GAMMA),
    "adam_lr": float(learner.ACTOR_LR),
}


@dataclass(frozen=True)
class StoredStep:
    observations: np.ndarray
    active_mask: np.ndarray
    effective_slot_block: np.ndarray
    noise: np.ndarray
    sampled_action: np.ndarray
    action_kernel: np.ndarray
    reward: float


@dataclass(frozen=True)
class StoredTrajectory:
    anchor_id: str
    profile: str
    root_id: int
    shock_index: int
    shock_tuple: tuple[str, str]
    steps: tuple[StoredStep, ...]
    critical_edges: Mapping[int, sibling.EdgeIdentity]
    trajectory_digest: str
    lifecycle_digest: str
    action_noise_digest: str


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _digest_bytes(*values: bytes) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(len(value).to_bytes(8, "little"))
        digest.update(value)
    return digest.hexdigest()


def _array_digest(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    return _digest_bytes(str(value.dtype).encode(), _json_bytes(value.shape), value.tobytes())


def _tensor_digest(tensors: Iterable[torch.Tensor]) -> str:
    return _digest_bytes(
        *(
            _json_bytes((str(tensor.dtype), tuple(tensor.shape)))
            + tensor.detach().cpu().contiguous().numpy().tobytes()
            for tensor in tensors
        )
    )


def _state_digest(state: Mapping[str, torch.Tensor]) -> str:
    return _digest_bytes(
        *(
            name.encode("utf-8") + tensor.detach().cpu().contiguous().numpy().tobytes()
            for name, tensor in state.items()
        )
    )


def _clone_state(actor: learner.RecurrentActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in actor.state_dict().items()}


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in FULL_EXPECTED_COUNTS}


def _correct_body(event_index: int, env: sibling.EocivSiblingRosterEnv) -> bytes:
    if sibling.CELL_CLASS[event_index] == "NEUTRAL":
        return sibling.NEUTRAL_TOKEN
    return env.focal_payload(event_index)


def _swapped_body(event_index: int, env: sibling.EocivSiblingRosterEnv) -> bytes:
    body = _correct_body(event_index, env)
    body_a = sibling.real_payload_body(sibling.SHOCK_A)
    body_b = sibling.real_payload_body(sibling.SHOCK_B)
    if body == sibling.NEUTRAL_TOKEN:
        return body
    if body == body_a:
        return body_b
    if body == body_b:
        return body_a
    raise BindingFailure("critical body is outside the registered A/B support")


BODY_RULES: Mapping[str, Callable[[int, sibling.EocivSiblingRosterEnv], bytes]] = {
    "CORRECT": _correct_body,
    "SWAPPED": _swapped_body,
}


class _RecordingPolicy(retention.RetentionPolicy):
    """Record the native verified-latch inputs used by common-data replay."""

    def forward(
        self,
        observations: np.ndarray,
        active_mask: np.ndarray,
        external_slot_block: np.ndarray,
        hidden: np.ndarray,
        noise: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        result = super().forward(
            observations, active_mask, external_slot_block, hidden, noise
        )
        self.steps[-1]["observations"] = np.asarray(observations, dtype=np.float64).copy()
        return result


def _new_actor(anchor_id: str, state: Mapping[str, torch.Tensor] | None = None) -> learner.RecurrentActorCritic:
    if anchor_id not in ANCHOR_IDS:
        raise BindingFailure(f"unregistered B9 anchor: {anchor_id!r}")
    capacities = {PROFILE_BY_NAME[name].member_capacity for name in PROFILE_NAMES}
    if len(capacities) != 1:
        raise BindingFailure("registered profiles do not share one actor capacity")
    actor = learner.RecurrentActorCritic(
        capacities.pop(), ANCHOR_SEEDS[anchor_id], encoder_kind="content_separating"
    )
    if state is not None:
        actor.load_state_dict(state, strict=True)
    return actor


def _make_env(
    profile: roster_env.RosterProfile,
    root_id: int,
    *,
    shock_seed: int,
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


def _make_runner(
    actor: learner.RecurrentActorCritic,
    profile: roster_env.RosterProfile,
    root_id: int,
    body: str,
    *,
    shock_seed: int,
    action_noise_seed: int,
    shock_tuple: tuple[str, str] | None,
) -> retention.RetentionEpisodeRunner:
    if body not in BODY_RULES:
        raise BindingFailure(f"unregistered B9 body: {body!r}")
    env = _make_env(profile, root_id, shock_seed=shock_seed, shock_tuple=shock_tuple)
    policy = _RecordingPolicy(actor, "SEGMENT_LATCH_RNN")
    runner = retention.RetentionEpisodeRunner(
        env,
        "LR",
        tape_seed=learner.TAPE_SEED,
        d_learned_fn=lambda _: True,
        body_fn=BODY_RULES[body],
        policy=policy,
    )
    runner.action_noise_seed_identity = sibling.profile_stream_identity(
        sibling.ACTION_NOISE_STREAM, action_noise_seed, profile.name
    )
    runner.noise = roster_env.make_action_noise(
        [root_id],
        action_seed=runner.action_noise_seed_identity,
        member_capacity=profile.member_capacity,
    )[:, 0, :, :]
    return runner


def _critical_edge_for_time(
    edges: Mapping[int, sibling.EdgeIdentity], time_index: int
) -> sibling.EdgeIdentity:
    for start, stop, event_index in CRITICAL_SEGMENTS:
        if start <= time_index < stop:
            try:
                edge = edges[start]
            except KeyError as exc:
                raise BindingFailure(f"missing authenticated edge at t={start}") from exc
            if edge.lifecycle_event_index != event_index:
                raise BindingFailure("critical edge event index drift")
            return edge
    raise BindingFailure(f"time {time_index} is outside the critical segments")


def addressed_credit_loss(
    score_rows: Sequence[torch.Tensor],
    active_masks: Sequence[np.ndarray],
    scalar_credits: torch.Tensor,
    critical_edges: Mapping[int, sibling.EdgeIdentity],
    branch: str,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Build one endpoint-addressed loss and its fail-closed term witness.

    ``score_rows`` are the full per-member rows from the native Normal before
    any active-row mean.  Only the authenticated receiver or distinct source
    row changes between branches; scalar credits and common time order do not.
    """
    if branch not in ADDRESSING_BRANCHES:
        raise BindingFailure(f"unknown score-row addressing branch: {branch!r}")
    if len(score_rows) != HORIZON or len(active_masks) != HORIZON:
        raise BindingFailure("score rows and active masks must cover one complete episode")
    if scalar_credits.shape != (HORIZON,):
        raise BindingFailure("scalar-credit vector must cover one complete episode")
    if not torch.isfinite(scalar_credits).all():
        raise BindingFailure("nonfinite detached scalar credit")
    terms: list[torch.Tensor] = []
    common_order: list[int] = []
    address_order: list[tuple[int, int]] = []
    for start, stop, _ in CRITICAL_SEGMENTS:
        for time_index in range(start, stop):
            rows = score_rows[time_index]
            mask = np.asarray(active_masks[time_index], dtype=np.bool_)
            if rows.ndim != 1 or rows.shape[0] != mask.shape[0]:
                raise BindingFailure("score-row/active-mask shape mismatch")
            if not torch.isfinite(rows).all():
                raise BindingFailure("nonfinite score row")
            edge = _critical_edge_for_time(critical_edges, time_index)
            receiver = int(edge.receiver_member_key)
            source = int(edge.source_member_key)
            if receiver == source:
                raise BindingFailure("authenticated source and receiver are not distinct")
            if not (0 <= receiver < len(mask) and 0 <= source < len(mask)):
                raise BindingFailure("authenticated endpoint is outside the score-row capacity")
            if not (bool(mask[receiver]) and bool(mask[source])):
                raise BindingFailure("authenticated endpoint lacks an active score row")
            member = receiver if branch == RECEIVER_ADDRESSED else source
            terms.append(-(rows[member] * scalar_credits[time_index].detach()))
            common_order.append(time_index)
            address_order.append((time_index, member))
    if len(terms) != 24:
        raise BindingFailure("one trajectory must contribute exactly 24 addressed terms")
    return torch.stack(terms).mean(), {
        "branch": branch,
        "term_count": len(terms),
        "common_time_order": common_order,
        "address_order": address_order,
        "common_order_digest": _digest_bytes(_json_bytes(common_order)),
    }


def _normalized_gae_credits(
    rewards: Sequence[float], values: Sequence[torch.Tensor]
) -> torch.Tensor:
    if len(rewards) != HORIZON or len(values) != HORIZON:
        raise BindingFailure("GAE inputs do not cover one complete episode")
    reward_tensor = torch.as_tensor(tuple(float(value) for value in rewards), dtype=torch.float32)
    value_tensor = torch.stack(tuple(values))
    detached_values = value_tensor.detach()
    next_values = torch.cat(
        (detached_values[1:], torch.zeros_like(detached_values[-1:])), dim=0
    )
    deltas = reward_tensor + GAMMA * next_values - detached_values
    raw = torch.empty_like(deltas)
    carry = torch.zeros((), dtype=deltas.dtype)
    for index in range(HORIZON - 1, -1, -1):
        carry = deltas[index] + GAMMA * GAE_LAMBDA * carry
        raw[index] = carry
    divisor = torch.clamp(raw.std(unbiased=False), min=NORMALIZATION_EPSILON)
    normalized = ((raw - raw.mean()) / divisor).detach()
    if not torch.isfinite(normalized).all() or normalized.requires_grad:
        raise BindingFailure("GAE-normalized team-credit scalars are not finite/detached")
    return normalized


def _trajectory_digest(steps: Sequence[StoredStep], edges: Mapping[int, sibling.EdgeIdentity]) -> str:
    return _digest_bytes(
        *(
            np.ascontiguousarray(value).tobytes()
            for step in steps
            for value in (
                step.observations,
                step.active_mask,
                step.effective_slot_block,
                step.noise,
                step.sampled_action,
                step.action_kernel,
            )
        ),
        np.asarray([step.reward for step in steps], dtype=np.float64).tobytes(),
        _json_bytes({str(key): asdict(value) for key, value in edges.items()}),
    )


def _collect_trajectory(
    actor: learner.RecurrentActorCritic,
    anchor_id: str,
    profile_name: str,
    root_id: int,
    shock_index: int,
    counts: dict[str, int],
    guard: "ResourceGuard",
    *,
    runner_factory: Callable[..., retention.RetentionEpisodeRunner] = _make_runner,
    record_activity: bool = True,
) -> StoredTrajectory:
    profile = PROFILE_BY_NAME[profile_name]
    shock_tuple = SHOCK_TUPLES[shock_index]
    runner = runner_factory(
        actor,
        profile,
        root_id,
        "CORRECT",
        shock_seed=root_id + 1_000_000,
        action_noise_seed=root_id + 2_000_000,
        shock_tuple=shock_tuple,
    )
    runner.run_episode()
    guard.check()
    if len(runner.policy.steps) != HORIZON or len(runner.env.reward_trace) != HORIZON:
        raise BindingFailure("common-data collection produced an incomplete episode")
    records = {record.receipt.physical_tick: record for record in runner.boundary_records}
    edges: dict[int, sibling.EdgeIdentity] = {}
    for start, _, event_index in CRITICAL_SEGMENTS:
        if start not in records:
            raise BindingFailure("critical actuation receipt is missing")
        edge = records[start].receipt.opportunity_identity
        if edge.profile_registration_id != profile_name or edge.episode_id != root_id:
            raise BindingFailure("critical edge identity is cross-profile or cross-root")
        if edge.lifecycle_event_index != event_index:
            raise BindingFailure("critical edge event binding drift")
        edges[start] = edge
    steps = tuple(
        StoredStep(
            np.asarray(step["observations"], dtype=np.float64).copy(),
            np.asarray(step["active_mask"], dtype=np.bool_).copy(),
            np.asarray(step["effective_slot_block"], dtype=np.float32).copy(),
            np.asarray(step["noise"], dtype=np.float32).copy(),
            np.asarray(step["sampled_action"], dtype=np.float32).copy(),
            np.asarray(step["action_kernel"], dtype=np.float32).copy(),
            float(step["reward"]),
        )
        for step in runner.policy.steps
    )
    for start, stop, _ in CRITICAL_SEGMENTS:
        edge = edges[start]
        for time_index in range(start, stop):
            slot = steps[time_index].effective_slot_block
            receiver = edge.receiver_member_key
            source = edge.source_member_key
            if not np.any(slot[receiver] != np.float32(0.0)):
                raise BindingFailure("focal receiver lacks its verified retained slot")
            if np.any(slot[source] != np.float32(0.0)):
                raise BindingFailure("authenticated source improperly owns the delivered slot")
            nonreceiver = slot.copy()
            nonreceiver[receiver] = np.float32(0.0)
            if np.any(nonreceiver != np.float32(0.0)):
                raise BindingFailure("nonreceiver row owns delivered-slot/latch content")
    if record_activity:
        counts["episodes"] += 1
        counts["collection_episodes"] += 1
        counts["environment_transitions"] += HORIZON
        counts["policy_calls"] += HORIZON
    lifecycle = _digest_bytes(
        _json_bytes(
            [
                (asdict(record.receipt.opportunity_identity), record.receipt.physical_tick)
                for record in runner.boundary_records
            ]
        )
    )
    return StoredTrajectory(
        anchor_id,
        profile_name,
        root_id,
        shock_index,
        shock_tuple,
        steps,
        edges,
        _trajectory_digest(steps, edges),
        lifecycle,
        _array_digest(runner.noise),
    )


def _actor_path_named_parameters(
    actor: learner.RecurrentActorCritic,
) -> tuple[tuple[str, torch.nn.Parameter], ...]:
    if actor.encoder_kind != "content_separating":
        raise BindingFailure("B9 actor-path selection requires content_separating")
    available = dict(actor.named_parameters())
    if any(name not in available for name in ACTIVE_ACTOR_PARAMETER_NAMES):
        raise BindingFailure("active actor-path parameter set is unavailable")
    values = tuple((name, available[name]) for name in ACTIVE_ACTOR_PARAMETER_NAMES)
    if tuple(name for name, _ in values) != ACTIVE_ACTOR_PARAMETER_NAMES:
        raise BindingFailure("active actor-path parameter order drift")
    forbidden = {"slot.weight", "slot.bias", "value.weight", "value.bias"}
    if forbidden & {name for name, _ in values}:
        raise BindingFailure("inactive raw-byte slot or value parameter entered actor path")
    return values


def _common_gradients(
    actor: learner.RecurrentActorCritic,
    trajectories: Sequence[StoredTrajectory],
) -> tuple[dict[str, tuple[torch.Tensor, ...]], dict[str, Any]]:
    if len(trajectories) != len(PROFILE_NAMES) * len(SHOCK_TUPLES):
        raise BindingFailure("one anchor lacks its exact 12 common trajectories")
    named_parameters = _actor_path_named_parameters(actor)
    receiver_losses: list[torch.Tensor] = []
    source_losses: list[torch.Tensor] = []
    score_tensors: list[torch.Tensor] = []
    scalar_tensors: list[torch.Tensor] = []
    common_order: list[tuple[str, int]] = []
    receiver_addresses: list[tuple[str, int, int]] = []
    source_addresses: list[tuple[str, int, int]] = []
    for trajectory in trajectories:
        previous = torch.zeros((actor.capacity, actor.hidden_dim), dtype=torch.float32)
        score_rows: list[torch.Tensor] = []
        values: list[torch.Tensor] = []
        masks: list[np.ndarray] = []
        for step in trajectory.steps:
            actions, mean, new_hidden, mask = actor._step_tensors(
                step.observations,
                step.active_mask,
                step.effective_slot_block,
                previous,
                step.noise,
            )
            observed_actions = actions.detach().cpu().numpy().astype(np.float32)
            observed_kernel = mean.detach().cpu().numpy().astype(np.float32)
            if not np.array_equal(observed_actions, step.sampled_action):
                raise BindingFailure("stored sampled action does not replay byte-exactly")
            if not np.array_equal(observed_kernel, step.action_kernel):
                raise BindingFailure("stored action kernel does not replay byte-exactly")
            std = torch.exp(torch.clamp(actor.log_std, -4.0, 1.0))
            eps = torch.as_tensor(step.noise, dtype=torch.float32)
            raw = mean + std * eps
            rows = torch.distributions.Normal(mean, std).log_prob(raw.detach()).sum(dim=-1)
            score_rows.append(rows)
            score_tensors.append(rows)
            masks.append(mask.detach().cpu().numpy().astype(np.bool_))
            values.append(actor.value(new_hidden[mask].mean(dim=0)).squeeze(-1))
            previous = new_hidden
        credits = _normalized_gae_credits(
            [step.reward for step in trajectory.steps], values
        )
        scalar_tensors.append(credits)
        receiver_loss, receiver_manifest = addressed_credit_loss(
            score_rows, masks, credits, trajectory.critical_edges, RECEIVER_ADDRESSED
        )
        source_loss, source_manifest = addressed_credit_loss(
            score_rows, masks, credits, trajectory.critical_edges, SOURCE_CONTROL
        )
        if receiver_manifest["common_time_order"] != source_manifest["common_time_order"]:
            raise BindingFailure("branch term order differs on common data")
        receiver_losses.append(receiver_loss)
        source_losses.append(source_loss)
        common_order.extend(
            (trajectory.trajectory_digest, time_index)
            for time_index in receiver_manifest["common_time_order"]
        )
        receiver_addresses.extend(
            (trajectory.trajectory_digest, time_index, member)
            for time_index, member in receiver_manifest["address_order"]
        )
        source_addresses.extend(
            (trajectory.trajectory_digest, time_index, member)
            for time_index, member in source_manifest["address_order"]
        )
    receiver_mean = torch.stack(receiver_losses).mean()
    source_mean = torch.stack(source_losses).mean()
    parameters = tuple(parameter for _, parameter in named_parameters)
    receiver_grad = torch.autograd.grad(
        receiver_mean, parameters, retain_graph=True, allow_unused=False
    )
    source_grad = torch.autograd.grad(
        source_mean, parameters, retain_graph=False, allow_unused=False
    )
    gradients = {
        RECEIVER_ADDRESSED: tuple(value.detach().clone() for value in receiver_grad),
        SOURCE_CONTROL: tuple(value.detach().clone() for value in source_grad),
    }
    flattened = {
        branch: torch.cat(tuple(value.reshape(-1) for value in gradient))
        for branch, gradient in gradients.items()
    }
    if any(
        parameter.grad is not None
        for name, parameter in actor.named_parameters()
        if name.startswith("value.")
    ):
        raise BindingFailure("common-gradient construction populated a value-head gradient")
    if any(not torch.isfinite(value).all() for value in flattened.values()):
        raise BindingFailure("addressed actor gradient is nonfinite")
    if len(common_order) != 12 * 24:
        raise BindingFailure("one anchor does not have exactly 288 addressed terms")
    trajectory_order = [trajectory.trajectory_digest for trajectory in trajectories]
    trajectory_rows = [
        {
            "anchor_id": trajectory.anchor_id,
            "profile": trajectory.profile,
            "root_id": trajectory.root_id,
            "shock_index": trajectory.shock_index,
            "shock_tuple": list(trajectory.shock_tuple),
            "trajectory_digest": trajectory.trajectory_digest,
            "lifecycle_digest": trajectory.lifecycle_digest,
            "action_noise_digest": trajectory.action_noise_digest,
            "critical_edges": {
                str(start): asdict(edge) for start, edge in trajectory.critical_edges.items()
            },
        }
        for trajectory in trajectories
    ]
    trajectory_order_digest = _digest_bytes(_json_bytes(trajectory_order))
    reward_digest = _digest_bytes(
        *(
            np.asarray([step.reward for step in trajectory.steps], dtype=np.float64).tobytes()
            for trajectory in trajectories
        )
    )
    scalar_digest = _tensor_digest(scalar_tensors)
    score_digest = _tensor_digest(score_tensors)
    common_order_digest = _digest_bytes(_json_bytes(common_order))
    shared_binding = {
        "trajectory_order_digest": trajectory_order_digest,
        "reward_digest": reward_digest,
        "scalar_credit_digest": scalar_digest,
        "score_tensor_digest": score_digest,
        "common_term_order_digest": common_order_digest,
        "term_count": len(common_order),
    }
    branch_common_bindings = {
        branch: copy.deepcopy(shared_binding) for branch in ADDRESSING_BRANCHES
    }
    if branch_common_bindings[RECEIVER_ADDRESSED] != branch_common_bindings[SOURCE_CONTROL]:
        raise BindingFailure("branch common-data binding differs before mutation")
    common = {
        "trajectory_count": len(trajectories),
        "trajectory_order": trajectory_order,
        "trajectory_rows": trajectory_rows,
        "trajectory_order_digest": trajectory_order_digest,
        "reward_digest": reward_digest,
        "scalar_credit_digest": scalar_digest,
        "score_tensor_digest": score_digest,
        "common_term_order": common_order,
        "common_term_order_digest": common_order_digest,
        "term_count": len(common_order),
        "receiver_address_rows": receiver_addresses,
        "source_address_rows": source_addresses,
        "receiver_address_digest": _digest_bytes(_json_bytes(receiver_addresses)),
        "source_address_digest": _digest_bytes(_json_bytes(source_addresses)),
        "branch_common_bindings": branch_common_bindings,
        "branch_common_bindings_identical": True,
        "gradients_computed_before_mutation": True,
        "receiver_gradient_digest": _tensor_digest(gradients[RECEIVER_ADDRESSED]),
        "source_gradient_digest": _tensor_digest(gradients[SOURCE_CONTROL]),
        "receiver_gradient_norm": float(torch.linalg.vector_norm(flattened[RECEIVER_ADDRESSED].double())),
        "source_gradient_norm": float(torch.linalg.vector_norm(flattened[SOURCE_CONTROL].double())),
    }
    return gradients, common


def _apply_one_actor_step(
    anchor_id: str,
    anchor_state: Mapping[str, torch.Tensor],
    gradient: Sequence[torch.Tensor],
    branch: str,
    counts: dict[str, int],
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    actor = _new_actor(anchor_id, anchor_state)
    named_parameters = _actor_path_named_parameters(actor)
    if len(named_parameters) != len(gradient):
        raise BindingFailure("gradient/actor-path parameter order mismatch")
    optimizer = torch.optim.Adam(
        [parameter for _, parameter in named_parameters], lr=ADAM_LR
    )
    if optimizer.state:
        raise BindingFailure("B9 branch optimizer is not fresh empty Adam")
    before_state = _clone_state(actor)
    before_values = {
        name: value.clone() for name, value in before_state.items() if name.startswith("value.")
    }
    optimizer.zero_grad(set_to_none=True)
    for (name, parameter), value in zip(named_parameters, gradient):
        if parameter.shape != value.shape or not torch.isfinite(value).all():
            raise BindingFailure(f"invalid addressed gradient for {name}")
        parameter.grad = value.to(dtype=parameter.dtype).clone()
    actor_grad_names = [name for name, parameter in named_parameters if parameter.grad is not None]
    if actor_grad_names != [name for name, _ in named_parameters]:
        raise BindingFailure("actor-path gradient coverage/order drift")
    if any(parameter.grad is not None for name, parameter in actor.named_parameters() if name.startswith("value.")):
        raise BindingFailure("value-head gradient entered the B9 step")
    optimizer.step()
    after_state = _clone_state(actor)
    after_values = {
        name: value for name, value in after_state.items() if name.startswith("value.")
    }
    if any(not torch.equal(before_values[name], after_values[name]) for name in before_values):
        raise BindingFailure("value-head parameter changed during actor-path step")
    if len(optimizer.state) != len(named_parameters):
        raise BindingFailure("fresh Adam did not create exactly one actor-path state row per parameter")
    if any(int(state["step"].item()) != 1 for state in optimizer.state.values()):
        raise BindingFailure("B9 endpoint is not exactly one Adam step")
    counts["optimizer_calls"] += 1
    counts["receiver_optimizer_calls" if branch == RECEIVER_ADDRESSED else "source_control_optimizer_calls"] += 1
    return after_state, {
        "branch": branch,
        "optimizer": "Adam",
        "learning_rate": ADAM_LR,
        "empty_state_before": True,
        "step_index_after": 1,
        "actor_path_parameter_names": actor_grad_names,
        "value_head_unchanged": True,
        "global_clip_calls": 0,
        "critic_loss_calls": 0,
        "endpoint_state_digest": _state_digest(after_state),
        "anchor_state_digest": _state_digest(before_state),
    }


def _critical_reward_mean(rewards: Sequence[float]) -> float:
    selected = [
        float(rewards[index])
        for start, stop, _ in CRITICAL_SEGMENTS
        for index in range(start, stop)
    ]
    if len(selected) != 24 or not np.isfinite(np.asarray(selected, dtype=np.float64)).all():
        raise BindingFailure("critical-segment reward mean lacks 24 finite native rewards")
    return float(np.mean(np.asarray(selected, dtype=np.float64)))


def _evaluate_endpoint(
    anchor_id: str,
    actor_state: Mapping[str, torch.Tensor],
    profile_name: str,
    root_id: int,
    root_index: int,
    endpoint: str,
    body: str,
    counts: dict[str, int],
    guard: "ResourceGuard",
) -> dict[str, Any]:
    actor = _new_actor(anchor_id, actor_state)
    runner = _make_runner(
        actor,
        PROFILE_BY_NAME[profile_name],
        root_id,
        body,
        shock_seed=root_id + 3_000_000,
        action_noise_seed=root_id + 4_000_000,
        shock_tuple=None,
    )
    runner.run_episode()
    guard.check()
    rewards = tuple(float(value) for value in runner.env.reward_trace)
    counts["episodes"] += 1
    counts["evaluation_episodes"] += 1
    counts["environment_transitions"] += HORIZON
    counts["policy_calls"] += HORIZON
    return {
        "anchor_id": anchor_id,
        "profile": profile_name,
        "heldout_root": root_id,
        "root_index": root_index,
        "endpoint": endpoint,
        "body": body,
        "critical_reward_mean": _critical_reward_mean(rewards),
        "shock_tuple": list(runner.env._shock_states),
        "lifecycle_digest": _digest_bytes(
            _json_bytes(
                [
                    (asdict(record.receipt.opportunity_identity), record.receipt.physical_tick)
                    for record in runner.boundary_records
                ]
            )
        ),
        "action_noise_digest": _array_digest(runner.noise),
        "accepted_boundaries": list(runner.accepted_boundary_ticks),
        "latch_started_zero": bool(runner.policy.started_zero),
        "latch_ended_zero": bool(runner.policy.ended_zero),
    }


def _expected_evaluation_coordinates() -> set[tuple[str, str, int, int, str, str]]:
    return {
        (anchor, profile, root_index, root_id, endpoint, body)
        for anchor in ANCHOR_IDS
        for profile in PROFILE_NAMES
        for root_index, root_id in enumerate(HELDOUT_ROOTS)
        for endpoint in ENDPOINTS
        for body in EVALUATION_BODIES
    }


def contrast_cells(
    evaluation_rows: Sequence[Mapping[str, Any]],
    *,
    require_registered_coordinates: bool = True,
) -> list[dict[str, Any]]:
    if require_registered_coordinates:
        observed = [
            (
                str(row["anchor_id"]),
                str(row["profile"]),
                int(row["root_index"]),
                int(row["heldout_root"]),
                str(row["endpoint"]),
                str(row["body"]),
            )
            for row in evaluation_rows
        ]
        expected = _expected_evaluation_coordinates()
        if len(observed) != len(expected) or set(observed) != expected:
            raise BindingFailure("registered held-out coordinate coverage is not exact")
    grouped: dict[tuple[str, str, int], list[Mapping[str, Any]]] = {}
    for row in evaluation_rows:
        key = (str(row["anchor_id"]), str(row["profile"]), int(row["root_index"]))
        grouped.setdefault(key, []).append(row)
    cells: list[dict[str, Any]] = []
    expected_coordinates = {(endpoint, body) for endpoint in ENDPOINTS for body in EVALUATION_BODIES}
    for key, rows in grouped.items():
        coordinates = {(str(row["endpoint"]), str(row["body"])) for row in rows}
        if coordinates != expected_coordinates or len(rows) != len(expected_coordinates):
            raise BindingFailure("held-out endpoint/body cell is incomplete or duplicated")
        matched_fields = ("shock_tuple", "lifecycle_digest", "action_noise_digest", "accepted_boundaries")
        if any(len({_json_bytes(row[field]) for row in rows}) != 1 for field in matched_fields):
            raise BindingFailure("held-out root is not matched across endpoints and bodies")
        values = {
            (str(row["endpoint"]), str(row["body"])): float(row["critical_reward_mean"])
            for row in rows
        }
        phi_0 = values[("0", "CORRECT")] - values[("0", "SWAPPED")]
        phi_r = values[("R", "CORRECT")] - values[("R", "SWAPPED")]
        phi_s = values[("S", "CORRECT")] - values[("S", "SWAPPED")]
        receiver_correct_vs_anchor = values[("R", "CORRECT")] - values[("0", "CORRECT")]
        receiver_correct_vs_source = values[("R", "CORRECT")] - values[("S", "CORRECT")]
        source_correct_vs_anchor = values[("S", "CORRECT")] - values[("0", "CORRECT")]
        generic_gain = 0.5 * (
            receiver_correct_vs_anchor
            + values[("R", "SWAPPED")] - values[("0", "SWAPPED")]
        )
        heldout_root = {int(row["heldout_root"]) for row in rows}
        if len(heldout_root) != 1:
            raise BindingFailure("one root-index cell aliases multiple held-out roots")
        cells.append(
            {
                "anchor_id": key[0],
                "profile": key[1],
                "root_index": key[2],
                "heldout_root": heldout_root.pop(),
                "Y": {endpoint: {body: values[(endpoint, body)] for body in EVALUATION_BODIES} for endpoint in ENDPOINTS},
                "phi_0": phi_0,
                "phi_R": phi_r,
                "phi_S": phi_s,
                "Delta_R": phi_r - phi_0,
                "J": phi_r - phi_s,
                "receiver_correct_vs_anchor": receiver_correct_vs_anchor,
                "receiver_correct_vs_source": receiver_correct_vs_source,
                "source_correct_vs_anchor": source_correct_vs_anchor,
                "receiver_two_arm_generic_gain": generic_gain,
            }
        )
    return sorted(cells, key=lambda row: (row["anchor_id"], row["profile"], row["root_index"]))


_METRICS = (
    "phi_0",
    "phi_R",
    "phi_S",
    "Delta_R",
    "J",
    "receiver_correct_vs_anchor",
    "receiver_correct_vs_source",
    "source_correct_vs_anchor",
    "receiver_two_arm_generic_gain",
)


def _aggregate(cells: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not cells:
        raise BindingFailure("robustness aggregate is empty")
    result = {
        metric: float(np.mean(np.asarray([float(cell[metric]) for cell in cells], dtype=np.float64)))
        for metric in _METRICS
    }
    if not np.isfinite(np.asarray(tuple(result.values()), dtype=np.float64)).all():
        raise BindingFailure("robustness aggregate is nonfinite")
    return result


def robust_aggregates(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = len(ANCHOR_IDS) * len(PROFILE_NAMES) * len(HELDOUT_ROOTS)
    if len(cells) != expected:
        raise BindingFailure(f"held-out cell count drift: {len(cells)} != {expected}")
    coordinates = [
        (
            str(cell["anchor_id"]),
            str(cell["profile"]),
            int(cell["root_index"]),
            int(cell["heldout_root"]),
        )
        for cell in cells
    ]
    expected_coordinates = {
        (anchor, profile, root_index, root_id)
        for anchor in ANCHOR_IDS
        for profile in PROFILE_NAMES
        for root_index, root_id in enumerate(HELDOUT_ROOTS)
    }
    if len(coordinates) != len(expected_coordinates) or set(coordinates) != expected_coordinates:
        raise BindingFailure("robust cell coordinate coverage is not exact")
    return {
        "global": _aggregate(cells),
        "by_anchor": {
            anchor: _aggregate([cell for cell in cells if cell["anchor_id"] == anchor])
            for anchor in ANCHOR_IDS
        },
        "leave_one_profile": {
            profile: _aggregate([cell for cell in cells if cell["profile"] != profile])
            for profile in PROFILE_NAMES
        },
        "leave_one_root": {
            str(root_index): _aggregate([cell for cell in cells if int(cell["root_index"]) != root_index])
            for root_index in range(len(HELDOUT_ROOTS))
        },
    }


def _all_robust_rows(aggregates: Mapping[str, Any]) -> list[Mapping[str, float]]:
    rows: list[Mapping[str, float]] = [aggregates["global"]]
    for family in ("by_anchor", "leave_one_profile", "leave_one_root"):
        rows.extend(aggregates[family].values())
    return rows


def select_terminal_branch(
    aggregates: Mapping[str, Any], *, binding_valid: bool
) -> str:
    """Apply the frozen B9 terminal precedence without tolerance or rescue."""
    if not binding_valid:
        return TERMINAL_BRANCHES[0]
    try:
        rows = _all_robust_rows(aggregates)
        values = np.asarray(
            [float(row[metric]) for row in rows for metric in _METRICS], dtype=np.float64
        )
    except (KeyError, TypeError, ValueError):
        return TERMINAL_BRANCHES[0]
    if values.size == 0 or not np.isfinite(values).all():
        return TERMINAL_BRANCHES[0]
    global_row = aggregates["global"]
    semantic = (
        all(float(row["J"]) > 0.0 and float(row["Delta_R"]) > 0.0 for row in rows)
        and float(global_row["receiver_correct_vs_anchor"]) >= 0.0
        and float(global_row["receiver_correct_vs_source"]) >= 0.0
    )
    if semantic:
        return TERMINAL_BRANCHES[1]
    generic_source_harm_or_damage = (
        float(global_row["receiver_two_arm_generic_gain"]) > 0.0
        or float(global_row["source_correct_vs_anchor"]) < 0.0
        or float(global_row["receiver_correct_vs_anchor"]) < 0.0
        or float(global_row["receiver_correct_vs_source"]) < 0.0
        or any(float(row["Delta_R"]) <= 0.0 for row in rows)
    )
    if generic_source_harm_or_damage:
        return TERMINAL_BRANCHES[2]
    if all(float(row["J"]) <= 0.0 for row in aggregates["by_anchor"].values()):
        return TERMINAL_BRANCHES[3]
    return TERMINAL_BRANCHES[4]


def _windows_rss_from_counters(counters: Any) -> int:
    return int(counters.PeakWorkingSetSize)


def _current_rss_bytes() -> int:
    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        if not ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        ):
            raise BindingFailure("cannot read process RSS for the B9 hard cap")
        return _windows_rss_from_counters(counters)
    import resource
    rss = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return rss if os.uname().sysname == "Darwin" else rss * 1024


class ResourceGuard:
    """Fail closed on process CPU-time or resident-memory cap breach."""

    def __init__(
        self,
        *,
        cpu_clock: Callable[[], float] = time.process_time,
        rss_reader: Callable[[], int] = _current_rss_bytes,
    ) -> None:
        self._cpu_clock = cpu_clock
        self._rss_reader = rss_reader
        self._cpu_start = float(cpu_clock())
        self.peak_rss_bytes = int(rss_reader())
        self.cpu_seconds = 0.0

    def check(self) -> None:
        self.cpu_seconds = float(self._cpu_clock()) - self._cpu_start
        self.peak_rss_bytes = max(self.peak_rss_bytes, int(self._rss_reader()))
        if self.cpu_seconds > CPU_TIME_CAP_SECONDS:
            raise BindingFailure("B9 exceeded the 5 CPU-minute hard cap")
        if self.peak_rss_bytes > RSS_CAP_BYTES:
            raise BindingFailure("B9 exceeded the 1 GiB RSS hard cap")

    def witness(self) -> dict[str, Any]:
        return {
            "cpu_seconds": self.cpu_seconds,
            "cpu_cap_seconds": CPU_TIME_CAP_SECONDS,
            "peak_rss_bytes": self.peak_rss_bytes,
            "rss_cap_bytes": RSS_CAP_BYTES,
            "within_caps": self.cpu_seconds <= CPU_TIME_CAP_SECONDS and self.peak_rss_bytes <= RSS_CAP_BYTES,
        }


def validate_namespace_binding(
    *,
    raw_output_binding: str,
    treatment: str,
    collection_roots: Sequence[int],
    heldout_roots: Sequence[int],
    artifact_inputs: Sequence[str] = (),
) -> list[str]:
    """Reject predecessor names, reused/aliased roots, and artifact inputs."""
    issues: list[str] = []
    collection = [int(root) for root in collection_roots]
    heldout = [int(root) for root in heldout_roots]
    if not raw_output_binding.startswith("eociv_lite.receiver_addressed_credit_edge.b9."):
        issues.append("raw binding is not in the fresh B9 namespace")
    if not treatment.startswith("EOCIV-B9-"):
        issues.append("treatment is not in the fresh B9 namespace")
    forbidden = ("B2", "B3", "B4", "B5", "B6", "B7", "B8", "A8", "HISTORY", "CHECKPOINT")
    material = f"{raw_output_binding}|{treatment}".upper()
    if any(token in material for token in forbidden):
        issues.append("predecessor/root-history/checkpoint namespace reuse")
    if artifact_inputs:
        issues.append("B9 forbids predecessor/history/checkpoint/artifact inputs")
    if len(collection) != len(set(collection)):
        issues.append("collection roots are not unique")
    if len(heldout) != len(set(heldout)):
        issues.append("held-out roots are not unique")
    if set(collection) & set(heldout):
        issues.append("collection and held-out roots overlap")
    if any(root < 990_000 or root >= 992_000 for root in (*collection, *heldout)):
        issues.append("root is outside the fresh B9 root namespace")
    return issues


def _namespace_issues() -> list[str]:
    collection = [root for roots in COLLECTION_ROOTS.values() for root in roots]
    return validate_namespace_binding(
        raw_output_binding=RAW_OUTPUT_BINDING,
        treatment=TREATMENT,
        collection_roots=collection,
        heldout_roots=HELDOUT_ROOTS,
        artifact_inputs=(),
    )


def registered_configuration() -> dict[str, Any]:
    return {
        "treatment": TREATMENT,
        "direction": DIRECTION,
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "parent_base_revision_provenance": BASE_REVISION,
        "anchors": list(ANCHOR_IDS),
        "anchor_seeds": dict(ANCHOR_SEEDS),
        "profiles": list(PROFILE_NAMES),
        "critical_shock_order": [list(value) for value in SHOCK_TUPLES],
        "collection_roots": {f"{key[0]}|{key[1]}": list(value) for key, value in COLLECTION_ROOTS.items()},
        "heldout_roots": list(HELDOUT_ROOTS),
        "endpoints": list(ENDPOINTS),
        "evaluation_bodies": list(EVALUATION_BODIES),
        "critical_segments": [list(value[:2]) for value in CRITICAL_SEGMENTS],
        "encoder_kind": "content_separating",
        "retention_condition": "SEGMENT_LATCH_RNN",
        "learner": "detached_GAE_normalized_team_credit_score_row",
        "addressing_branches": list(ADDRESSING_BRANCHES),
        "horizon": HORIZON,
        "gamma": GAMMA,
        "gae_lambda": GAE_LAMBDA,
        "normalization_epsilon": NORMALIZATION_EPSILON,
        "adam_lr": ADAM_LR,
        "optimizer_state_before_each_branch": "EMPTY",
        "optimizer_steps_per_branch": 1,
        "value_gradient": False,
        "critic_loss": False,
        "global_clipping": False,
        "second_update": False,
        "anchor_endpoint": "0_NO_STEP",
        "k_search": K_SEARCH,
        "cpu_threads": CPU_THREAD_COUNT,
        "cpu_time_cap_seconds": CPU_TIME_CAP_SECONDS,
        "rss_cap_bytes": RSS_CAP_BYTES,
        "full_expected_counts": dict(FULL_EXPECTED_COUNTS),
        "activity_factorization": {
            "collection": "2 anchors x 3 profiles x 4 forced critical-shock tuples",
            "evaluation": "2 anchors x 3 profiles x 8 roots x 3 endpoints x 2 bodies",
            "transitions": "312 episodes x 48",
            "optimizer_calls": "2 anchors x 2 addressing branches",
        },
        "artifact_inputs": [],
        "predecessor_checkpoint_root_history_artifact_reuse": False,
    }


def candidate_identity_issues(
    *,
    candidate_revision: str,
    checkout_revision: str,
    checkout_clean: bool,
) -> list[str]:
    issues: list[str] = []
    if REVISION_PATTERN.fullmatch(candidate_revision) is None:
        issues.append("candidate revision must be explicit 40-lowercase-hex")
    if REVISION_PATTERN.fullmatch(checkout_revision) is None:
        issues.append("checked-out revision must be 40-lowercase-hex")
    if candidate_revision == BASE_REVISION:
        issues.append("parent base revision is provenance only, not candidate identity")
    if candidate_revision != checkout_revision:
        issues.append("candidate revision does not match checked-out HEAD")
    if not checkout_clean:
        issues.append("checked-out candidate is not clean")
    return issues


def readiness(
    *,
    candidate_revision: str,
    checkout_revision: str,
    checkout_clean: bool,
) -> dict[str, Any]:
    """Candidate-bound, zero-episode/zero-update preflight."""
    issues = _namespace_issues()
    issues.extend(
        candidate_identity_issues(
            candidate_revision=candidate_revision,
            checkout_revision=checkout_revision,
            checkout_clean=checkout_clean,
        )
    )
    if tuple(PROFILE_BY_NAME) != PROFILE_NAMES:
        issues.append("registered native profile order drift")
    expected_dependencies = {
        "horizon": HORIZON,
        "event_times": (12, 24, 36),
        "segment_length": 12,
        "gamma": GAMMA,
        "adam_lr": ADAM_LR,
    }
    if _DEPENDENCY_LITERALS != expected_dependencies:
        issues.append("native host/learner dependency literal drift")
    if FULL_PLAN.expected_counts != FULL_EXPECTED_COUNTS:
        issues.append("derived activity counts drift")
    if any(FULL_EXPECTED_COUNTS[key] != value for key, value in _FROZEN_TOTALS.items()):
        issues.append("frozen activity totals drift")
    if torch.get_num_threads() != CPU_THREAD_COUNT:
        issues.append("torch CPU thread count is not exactly one")
    configuration = registered_configuration()
    if configuration["artifact_inputs"] or configuration["predecessor_checkpoint_root_history_artifact_reuse"]:
        issues.append("predecessor/artifact reuse is not rejected")
    return {
        "artifact_kind": "EOCIV_B9_ZERO_COMPUTE_READINESS",
        "ready": not issues,
        "issues": issues,
        "candidate_revision": candidate_revision,
        "checkout_revision": checkout_revision,
        "checkout_clean": bool(checkout_clean),
        "parent_base_revision_provenance": BASE_REVISION,
        "configuration_digest": _digest_bytes(_json_bytes(configuration)),
        "episodes": 0,
        "environment_transitions": 0,
        "optimizer_calls": 0,
        "scientific_terminal_admitted": False,
    }


def _invalid_result(
    candidate_revision: str,
    run_id: str,
    counts: Mapping[str, int],
    reason: str,
    guard: ResourceGuard | None,
) -> dict[str, Any]:
    return {
        "artifact_kind": "EOCIV_B9_REGISTERED_RESULT_IN_MEMORY",
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "treatment": TREATMENT,
        "direction": DIRECTION,
        "stage": STAGE,
        "candidate_revision": candidate_revision,
        "parent_base_revision_provenance": BASE_REVISION,
        "run_id": run_id,
        "terminal_branch": TERMINAL_BRANCHES[0],
        "scientific_terminal_admitted": True,
        "configuration": registered_configuration(),
        "counts": dict(counts),
        "binding_valid": False,
        "binding_failure": reason,
        "resource_witness": None if guard is None else guard.witness(),
        "interpretation_boundary": (
            "Fail-closed B9 binding outcome; the exclusive outer lifecycle may persist this terminal at the sole reserved path, "
            "with no retry, rescue, extension, retained direction, successor, or additional artifact."
        ),
    }


def run_registered(
    *,
    candidate_revision: str,
    checkout_revision: str,
    checkout_clean: bool,
    run_id: str,
) -> dict[str, Any]:
    """Run the exact registered 312-episode candidate in memory.

    This entry point is intentionally never called by readiness or focused
    tests.  It writes no artifact and does not create a run root.
    """
    counts = _empty_counts()
    preflight = readiness(
        candidate_revision=candidate_revision,
        checkout_revision=checkout_revision,
        checkout_clean=checkout_clean,
    )
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        preflight["issues"].append("run id is not a fresh safe eociv-b9 identifier")
        preflight["ready"] = False
    if not preflight["ready"]:
        return _invalid_result(candidate_revision, run_id, counts, "; ".join(preflight["issues"]), None)
    guard: ResourceGuard | None = None
    try:
        guard = ResourceGuard()
        guard.check()
        anchor_records: list[dict[str, Any]] = []
        endpoint_states: dict[str, dict[str, Mapping[str, torch.Tensor]]] = {}
        for anchor_id in ANCHOR_IDS:
            anchor = _new_actor(anchor_id)
            anchor_state = _clone_state(anchor)
            anchor_digest = _state_digest(anchor_state)
            trajectories: list[StoredTrajectory] = []
            for profile_name in PROFILE_NAMES:
                roots = COLLECTION_ROOTS[(anchor_id, profile_name)]
                for shock_index, root_id in enumerate(roots):
                    trajectories.append(
                        _collect_trajectory(
                            anchor, anchor_id, profile_name, root_id, shock_index, counts, guard
                        )
                    )
            gradients, common = _common_gradients(anchor, trajectories)
            if _state_digest(_clone_state(anchor)) != anchor_digest:
                raise BindingFailure("common gradient computation mutated the no-step anchor")
            receiver_state, receiver_step = _apply_one_actor_step(
                anchor_id, anchor_state, gradients[RECEIVER_ADDRESSED], RECEIVER_ADDRESSED, counts
            )
            source_state, source_step = _apply_one_actor_step(
                anchor_id, anchor_state, gradients[SOURCE_CONTROL], SOURCE_CONTROL, counts
            )
            guard.check()
            if not (
                receiver_step["anchor_state_digest"]
                == source_step["anchor_state_digest"]
                == anchor_digest
            ):
                raise BindingFailure("branch clones do not share the exact anchor")
            endpoint_states[anchor_id] = {"0": anchor_state, "R": receiver_state, "S": source_state}
            anchor_records.append(
                {
                    "anchor_id": anchor_id,
                    "initialization_seed": ANCHOR_SEEDS[anchor_id],
                    "anchor_state_digest": anchor_digest,
                    "common_data": common,
                    "receiver_step": receiver_step,
                    "source_control_step": source_step,
                    "collection_trajectory_digests": [value.trajectory_digest for value in trajectories],
                }
            )
        evaluation_rows: list[dict[str, Any]] = []
        for anchor_id in ANCHOR_IDS:
            for profile_name in PROFILE_NAMES:
                for root_index, root_id in enumerate(HELDOUT_ROOTS):
                    for endpoint in ENDPOINTS:
                        for body in EVALUATION_BODIES:
                            evaluation_rows.append(
                                _evaluate_endpoint(
                                    anchor_id,
                                    endpoint_states[anchor_id][endpoint],
                                    profile_name,
                                    root_id,
                                    root_index,
                                    endpoint,
                                    body,
                                    counts,
                                    guard,
                                )
                            )
        guard.check()
        if counts != FULL_EXPECTED_COUNTS:
            raise BindingFailure(f"exact activity count drift: {counts} != {FULL_EXPECTED_COUNTS}")
        cells = contrast_cells(evaluation_rows)
        aggregates = robust_aggregates(cells)
        fidelity = {
            "readiness": bool(preflight["ready"]),
            "fresh_independent_anchors": len({record["anchor_state_digest"] for record in anchor_records}) == 2,
            "common_trajectory_count": all(record["common_data"]["trajectory_count"] == 12 for record in anchor_records),
            "common_term_count": all(record["common_data"]["term_count"] == 288 for record in anchor_records),
            "branch_common_bindings_identical": all(
                record["common_data"]["branch_common_bindings_identical"]
                and record["common_data"]["branch_common_bindings"][RECEIVER_ADDRESSED]
                == record["common_data"]["branch_common_bindings"][SOURCE_CONTROL]
                for record in anchor_records
            ),
            "gradients_before_mutation": all(record["common_data"]["gradients_computed_before_mutation"] for record in anchor_records),
            "endpoint_clone_binding": all(
                record["receiver_step"]["anchor_state_digest"] == record["anchor_state_digest"]
                and record["source_control_step"]["anchor_state_digest"] == record["anchor_state_digest"]
                for record in anchor_records
            ),
            "one_empty_adam_step_each": all(
                record[key]["empty_state_before"] and record[key]["step_index_after"] == 1
                for record in anchor_records
                for key in ("receiver_step", "source_control_step")
            ),
            "actor_only_no_clip": all(
                record[key]["value_head_unchanged"]
                and record[key]["global_clip_calls"] == 0
                and record[key]["critic_loss_calls"] == 0
                for record in anchor_records
                for key in ("receiver_step", "source_control_step")
            ),
            "heldout_coordinate_count": len(evaluation_rows) == FULL_PLAN.evaluation_episodes,
            "heldout_coordinate_coverage_exact": {
                (
                    str(row["anchor_id"]),
                    str(row["profile"]),
                    int(row["root_index"]),
                    int(row["heldout_root"]),
                    str(row["endpoint"]),
                    str(row["body"]),
                )
                for row in evaluation_rows
            }
            == _expected_evaluation_coordinates(),
            "cell_count": len(cells) == len(ANCHOR_IDS) * len(PROFILE_NAMES) * len(HELDOUT_ROOTS),
            "counts_exact": counts == FULL_EXPECTED_COUNTS,
            "resource_caps": bool(guard.witness()["within_caps"]),
            "finite": bool(
                np.isfinite(
                    np.asarray(
                        [float(cell[metric]) for cell in cells for metric in _METRICS], dtype=np.float64
                    )
                ).all()
            ),
        }
        binding_valid = all(fidelity.values())
        branch = select_terminal_branch(aggregates, binding_valid=binding_valid)
        if not binding_valid and branch != TERMINAL_BRANCHES[0]:
            raise BindingFailure("invalid fidelity did not select B9_INVALID_BINDING")
        return {
            "artifact_kind": "EOCIV_B9_REGISTERED_RESULT_IN_MEMORY",
            "raw_output_binding": RAW_OUTPUT_BINDING,
            "treatment": TREATMENT,
            "direction": DIRECTION,
            "stage": STAGE,
            "candidate_revision": candidate_revision,
            "parent_base_revision_provenance": BASE_REVISION,
            "run_id": run_id,
            "terminal_branch": branch,
            "scientific_terminal_admitted": True,
            "configuration": registered_configuration(),
            "counts": counts,
            "binding_valid": binding_valid,
            "fidelity": fidelity,
            "resource_witness": guard.witness(),
            "anchor_records": anchor_records,
            "full_cell_table": cells,
            "aggregates": aggregates,
            "interpretation_boundary": (
                "One immediate shared-policy score-row-address total effect only; no receiver-local weights or mediation, "
                "history comparison, tuning, retry, rescue, extra root, or sustained-learning successor. The inner runner "
                "writes nothing; the exclusive outer lifecycle owns the sole reserved result."
            ),
        }
    except (BindingFailure, RuntimeError, ValueError, FloatingPointError, MemoryError, OSError) as exc:
        return _invalid_result(candidate_revision, run_id, counts, str(exc), guard)


READINESS_PHASES = (
    "interface_smoke",
    "bounded_exercise",
    "artifact_validation",
    "artifact_reload",
    "evaluate_entry",
    "analyze_entry",
)
READINESS_PHASE_FILES = {
    phase: f"{index:02d}_{phase}.json"
    for index, phase in enumerate(READINESS_PHASES, start=1)
}
ZERO_SCIENCE_COUNTS = {
    "episodes": 0,
    "environment_transitions": 0,
    "optimizer_calls": 0,
    "scientific_optimizer_calls": 0,
}


def _configuration_digest() -> str:
    return _digest_bytes(_json_bytes(registered_configuration()))


def _artifact_digest(value: Mapping[str, Any]) -> str:
    material = {key: nested for key, nested in value.items() if key != "artifact_digest"}
    return _digest_bytes(_json_bytes(material))


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _write_json_replace(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _safe_exercise_root(exercise_root: Path, repository_root: Path) -> Path:
    root = Path(exercise_root).resolve()
    repository = Path(repository_root).resolve()
    try:
        inside_repository = root.is_relative_to(repository)
    except AttributeError:
        inside_repository = repository == root or repository in root.parents
    if inside_repository:
        raise BindingFailure("readiness exercise root must be outside the repository")
    reserved = (repository / RESULT_RELATIVE_PATH).resolve()
    if root == reserved or root in reserved.parents or reserved in root.parents:
        raise BindingFailure("readiness exercise root aliases the reserved result destination")
    return root


def _read_phase_artifact(
    root: Path,
    phase: str,
    *,
    candidate_revision: str,
) -> dict[str, Any]:
    path = root / READINESS_PHASE_FILES[phase]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise BindingFailure(f"missing or malformed readiness artifact for {phase}") from exc
    if value.get("phase") != phase:
        raise BindingFailure(f"readiness artifact phase mismatch for {phase}")
    if value.get("candidate_revision") != candidate_revision:
        raise BindingFailure(f"readiness artifact candidate mismatch for {phase}")
    if value.get("configuration_digest") != _configuration_digest():
        raise BindingFailure(f"readiness artifact configuration mismatch for {phase}")
    if value.get("counts") != ZERO_SCIENCE_COUNTS:
        raise BindingFailure(f"readiness artifact contains nonzero science activity for {phase}")
    if value.get("artifact_digest") != _artifact_digest(value):
        raise BindingFailure(f"readiness artifact digest mismatch for {phase}")
    return value


def _synthetic_evaluation_rows() -> list[dict[str, Any]]:
    values = {
        ("0", "CORRECT"): 1.0,
        ("0", "SWAPPED"): 0.0,
        ("R", "CORRECT"): 3.0,
        ("R", "SWAPPED"): 1.0,
        ("S", "CORRECT"): 2.0,
        ("S", "SWAPPED"): 1.5,
    }
    return [
        {
            "anchor_id": anchor,
            "profile": profile,
            "heldout_root": root_id,
            "root_index": root_index,
            "endpoint": endpoint,
            "body": body,
            "critical_reward_mean": values[(endpoint, body)],
            "shock_tuple": ["A", "NONE", "B"],
            "lifecycle_digest": f"synthetic-lifecycle-{anchor}-{profile}-{root_index}",
            "action_noise_digest": f"synthetic-noise-{profile}-{root_index}",
            "accepted_boundaries": [12, 24, 36],
        }
        for anchor in ANCHOR_IDS
        for profile in PROFILE_NAMES
        for root_index, root_id in enumerate(HELDOUT_ROOTS)
        for endpoint in ENDPOINTS
        for body in EVALUATION_BODIES
    ]


def run_readiness_phase(
    phase: str,
    *,
    exercise_root: Path,
    repository_root: Path,
    candidate_revision: str,
    checkout_revision: str,
    checkout_clean: bool,
) -> dict[str, Any]:
    """Run one ordered, temporary, zero-science verifier phase."""
    if phase not in READINESS_PHASES:
        raise BindingFailure(f"unknown B9 readiness phase: {phase!r}")
    preflight = readiness(
        candidate_revision=candidate_revision,
        checkout_revision=checkout_revision,
        checkout_clean=checkout_clean,
    )
    if not preflight["ready"]:
        raise BindingFailure("candidate-bound readiness phase rejected: " + "; ".join(preflight["issues"]))
    root = _safe_exercise_root(exercise_root, repository_root)
    phase_index = READINESS_PHASES.index(phase)
    if phase_index == 0:
        if not root.is_dir():
            raise BindingFailure("interface_smoke requires the wrapper-created exercise root")
        log_root = root / ".hmasd-readiness-logs"
        if log_root.exists() and not log_root.is_dir():
            raise BindingFailure("wrapper readiness log path is not a directory")
        unexpected = [entry for entry in root.iterdir() if entry != log_root]
        if unexpected:
            raise BindingFailure("interface_smoke exercise root contains unexpected preexisting entries")
        if (Path(repository_root).resolve() / RESULT_RELATIVE_PATH).exists():
            raise BindingFailure("reserved B9 result destination is already consumed")
    elif not root.is_dir():
        raise BindingFailure("readiness phase requires the existing exercise root")
    previous: list[dict[str, Any]] = []
    for prior_phase in READINESS_PHASES[:phase_index]:
        previous.append(
            _read_phase_artifact(root, prior_phase, candidate_revision=candidate_revision)
        )
    for index, value in enumerate(previous):
        expected_previous = None if index == 0 else previous[index - 1]["artifact_digest"]
        if value.get("previous_artifact_digest") != expected_previous:
            raise BindingFailure("readiness artifact lifecycle chain mismatch")
    for later_phase in READINESS_PHASES[phase_index:]:
        if (root / READINESS_PHASE_FILES[later_phase]).exists():
            raise BindingFailure(f"readiness phase is repeated or out of order: {later_phase}")
    payload: dict[str, Any]
    if phase == "interface_smoke":
        payload = {
            "interfaces": list(READINESS_PHASES),
            "result_relative_path": RESULT_RELATIVE_PATH.as_posix(),
            "reserved_result_exists": (Path(repository_root) / RESULT_RELATIVE_PATH).exists(),
        }
    elif phase == "bounded_exercise":
        actor = _new_actor("A0")
        payload = {
            "active_actor_parameter_names": [
                name for name, _ in _actor_path_named_parameters(actor)
            ],
            "anchor_endpoint_digest": _state_digest(_clone_state(actor)),
            "k_search": K_SEARCH,
        }
    elif phase == "artifact_validation":
        payload = {
            "validated_phases": [value["phase"] for value in previous],
            "validated_digests": [value["artifact_digest"] for value in previous],
        }
    elif phase == "artifact_reload":
        reloaded = [
            _read_phase_artifact(root, value["phase"], candidate_revision=candidate_revision)
            for value in previous
        ]
        payload = {
            "reloaded_phases": [value["phase"] for value in reloaded],
            "reloaded_digests": [value["artifact_digest"] for value in reloaded],
        }
    elif phase == "evaluate_entry":
        rows = _synthetic_evaluation_rows()
        cells = contrast_cells(rows, require_registered_coordinates=True)
        aggregates = robust_aggregates(cells)
        payload = {
            "synthetic_fixture": True,
            "evaluation_row_count": len(rows),
            "cell_count": len(cells),
            "evaluation_rows_digest": _digest_bytes(_json_bytes(rows)),
            "formula_witness": {key: cells[0][key] for key in _METRICS},
            "aggregates": aggregates,
        }
    else:
        evaluate_artifact = previous[READINESS_PHASES.index("evaluate_entry")]
        aggregates = evaluate_artifact["payload"]["aggregates"]
        branch = select_terminal_branch(aggregates, binding_valid=True)
        payload = {
            "synthetic_fixture": True,
            "terminal_branch": branch,
            "expected_branch": TERMINAL_BRANCHES[1],
            "branch_path_exercised": branch == TERMINAL_BRANCHES[1],
        }
        if not payload["branch_path_exercised"]:
            raise BindingFailure("synthetic analyze entry did not exercise semantic branch")
    artifact: dict[str, Any] = {
        "artifact_kind": "EOCIV_B9_TEMPORARY_READINESS_PHASE",
        "phase": phase,
        "candidate_revision": candidate_revision,
        "checkout_revision": checkout_revision,
        "checkout_clean": bool(checkout_clean),
        "configuration_digest": _configuration_digest(),
        "counts": dict(ZERO_SCIENCE_COUNTS),
        "previous_artifact_digest": None if not previous else previous[-1]["artifact_digest"],
        "payload": payload,
        "scientific_terminal_admitted": False,
    }
    artifact["artifact_digest"] = _artifact_digest(artifact)
    _write_json_exclusive(root / READINESS_PHASE_FILES[phase], artifact)
    return artifact


def interface_smoke(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("interface_smoke", **kwargs)


def bounded_exercise(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("bounded_exercise", **kwargs)


def artifact_validation(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("artifact_validation", **kwargs)


def artifact_reload(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("artifact_reload", **kwargs)


def evaluate_entry(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("evaluate_entry", **kwargs)


def analyze_entry(**kwargs: Any) -> dict[str, Any]:
    return run_readiness_phase("analyze_entry", **kwargs)


def run_registered_lifecycle(
    *,
    repository_root: Path,
    candidate_revision: str,
    checkout_revision: str,
    checkout_clean: bool,
    run_id: str,
    full_runner: Callable[..., Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Exclusive one-shot claim followed by the exact in-memory full."""
    preflight = readiness(
        candidate_revision=candidate_revision,
        checkout_revision=checkout_revision,
        checkout_clean=checkout_clean,
    )
    if not preflight["ready"]:
        raise BindingFailure("registered lifecycle readiness rejected: " + "; ".join(preflight["issues"]))
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise BindingFailure("run id is not a fresh safe eociv-b9 identifier")
    repository = Path(repository_root).resolve()
    result_path = (repository / RESULT_RELATIVE_PATH).resolve()
    if repository not in result_path.parents:
        raise BindingFailure("reserved result path escaped the repository")
    result_path.parent.mkdir(parents=True, exist_ok=True)
    claim: dict[str, Any] = {
        "artifact_kind": "EOCIV_B9_REGISTERED_EXCLUSIVE_CLAIM",
        "status": "CLAIMED_BEFORE_EPISODE_ONE",
        "candidate_revision": candidate_revision,
        "checkout_revision": checkout_revision,
        "checkout_clean": bool(checkout_clean),
        "run_id": run_id,
        "result_relative_path": RESULT_RELATIVE_PATH.as_posix(),
        "configuration_digest": _configuration_digest(),
        "counts": dict(ZERO_SCIENCE_COUNTS),
    }
    claim["claim_digest"] = _digest_bytes(_json_bytes(claim))
    _write_json_exclusive(result_path, claim)
    runner = run_registered if full_runner is None else full_runner
    result = dict(
        runner(
            candidate_revision=candidate_revision,
            checkout_revision=checkout_revision,
            checkout_clean=checkout_clean,
            run_id=run_id,
        )
    )
    if result.get("candidate_revision") != candidate_revision or result.get("run_id") != run_id:
        raise BindingFailure("registered result candidate/run binding mismatch")
    if result.get("terminal_branch") not in TERMINAL_BRANCHES:
        raise BindingFailure("registered result lacks a known terminal branch")
    result["result_relative_path"] = RESULT_RELATIVE_PATH.as_posix()
    result["exclusive_claim_digest"] = claim["claim_digest"]
    _write_json_replace(result_path, result)
    return result
