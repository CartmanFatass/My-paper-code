"""Frozen OR/DUM/EHC event-held commitment package for noncalendar G0."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
import math
from pathlib import Path
import random
from typing import Any, Iterable, Literal, Mapping

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_direct import (
    DirectPrimitiveARPolicy,
    ENTROPY_COEFFICIENT,
    GAE_LAMBDA,
    GAMMA,
    GRADIENT_CLIP,
    LEARNING_RATE,
    PPO_CLIP,
    PPO_PASSES,
    VALUE_CLIP,
    VALUE_COEFFICIENT,
    model_state_copy,
    nested_state_maximum_difference,
)
from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, HORIZON, MAX_LIFECYCLES, OBSERVATION_DIM
from ha_ctse_process.noncalendar_commitment_testbed import (
    ADDED_PARAMETER_COUNT,
    CHECKPOINT_KIND,
    CHECKPOINT_SCHEMA_VERSION,
    EVENT_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_NUM_ENVS,
    FORMAL_TRAIN_EPISODES,
    FORMAL_TRANSITIONS_PER_ARM,
    FORMAL_UPDATES,
    HELD_OUT_EVAL_TASK_SEED,
    IID_EVAL_TASK_SEED,
    MARK_SEED,
    MODEL_INITIALIZATION_SEED,
    OPPORTUNITY_SEED,
    PARAMETER_COUNT,
    REGISTERED_CONTRACT,
    TRAIN_ORDER_SEED,
    TRAIN_TASK_SEED,
    TRAIN_ACTION_SEED,
    frontier_order,
    make_noncalendar_ledger,
    registered_contract,
    NoncalendarLedger,
    NoncalendarTrackingEnv,
    TrackingOutcome,
)

ArmName = Literal["OR", "DUM", "EHC"]
EVENT_INPUT_DIM = OBSERVATION_DIM + 32 + 32 + 8
MARK_DIM = 8
OPPORTUNITY_SUPPORT = np.asarray((4, 8, 12), dtype=np.int64)
CREATE, KEEP, RENEW = 1, 2, 3
EVENT_ENTROPY_COEFFICIENT = 0.01
REPLAY_TOLERANCE = 1e-6
RESUME_TOLERANCE = 1e-7
RNG_NAMES = ("ledger", "order", "primitive", "opportunity", "event", "mark")


@dataclass
class SegmentRecord:
    episode_id: int
    key: int
    membership_epoch: int
    segment_id: int
    start_active_step: int
    end_active_step: int
    censored: bool
    close_reason: str
    opportunity_count: int

    @property
    def active_lifetime(self) -> int:
        return self.end_active_step - self.start_active_step


@dataclass
class LifecycleState:
    membership_epoch: int
    z: torch.Tensor
    q: int
    segment_id: int
    segment_start_active_step: int
    active_steps: int = 0
    non_create_opportunities: int = 0
    spell_opportunity_count: int = 0
    """Running `K` (KEEP/RENEW opportunities so far) for the currently open
    spell only; reset to 0 only when a RENEW closes that spell and opens the
    next one. At CREATE (`LifecycleState` construction) it is
    zero-initialized, not reset -- there is no prior spell to reset from.
    Distinct from `non_create_opportunities`, which accumulates across all
    spells of this lifecycle and is never reset."""


@dataclass
class CollectionCursor:
    episode_ids: tuple[int, ...]
    ledgers: tuple[NoncalendarLedger, ...]
    environments: list[NoncalendarTrackingEnv]
    hidden: torch.Tensor
    lifecycles: list[dict[int, LifecycleState]]
    segments: list[list[SegmentRecord]]


@dataclass
class EventTrajectory:
    observations: torch.Tensor
    active_mask: torch.Tensor
    orders: torch.Tensor
    actions: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    rewards: torch.Tensor
    terminal: torch.Tensor
    hidden_before: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    primitive_z: torch.Tensor
    event_kind: torch.Tensor
    event_inputs: torch.Tensor
    event_categorical_actions: torch.Tensor
    event_u: torch.Tensor
    event_z_pre: torch.Tensor
    event_new_z: torch.Tensor
    candidate_u: torch.Tensor
    candidate_z: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_old_cat_logp: torch.Tensor
    event_old_mark_component_logp: torch.Tensor
    event_old_joint_logp: torch.Tensor
    membership_epoch: torch.Tensor
    segment_id: torch.Tensor
    q_before: torch.Tensor
    outcomes: tuple[TrackingOutcome, ...]
    segments: tuple[tuple[SegmentRecord, ...], ...]
    ledger_ids: tuple[int, ...]
    cutoff: bool
    bootstrap_values: torch.Tensor
    cursor: CollectionCursor | None

    @property
    def time_steps(self) -> int:
        return int(self.rewards.shape[0])


class CommitmentArm(nn.Module):
    """Ordinary source base plus the exact DUM/EHC additions."""

    def __init__(self, arm: ArmName) -> None:
        super().__init__()
        if arm not in ("OR", "DUM", "EHC"):
            raise ValueError("invalid commitment arm")
        self.arm: ArmName = arm
        self.base = DirectPrimitiveARPolicy()
        if arm != "OR":
            self.W_z = nn.Linear(MARK_DIM, ACTION_COUNT, bias=False)
            self.event_head = nn.Linear(EVENT_INPUT_DIM, 2)
            self.mark_head = nn.Linear(EVENT_INPUT_DIM, 2 * MARK_DIM)
        else:
            self.W_z = None
            self.event_head = None
            self.mark_head = None

    @property
    def treatment(self) -> int:
        return int(self.arm == "EHC")

    @property
    def base_parameter_count(self) -> int:
        return sum(p.numel() for p in self.base.parameters())

    @property
    def added_parameter_count(self) -> int:
        return sum(p.numel() for n, p in self.named_parameters() if not n.startswith("base."))

    def primitive_bias(self, z: torch.Tensor) -> torch.Tensor | None:
        if self.W_z is None:
            return None
        return self.W_z(float(self.treatment) * z.detach())

    def event_parameters(self) -> list[nn.Parameter]:
        if self.arm == "OR":
            return []
        assert self.event_head is not None and self.mark_head is not None
        return [*self.event_head.parameters(), *self.mark_head.parameters()]

    def base_optimizer_parameters(self) -> list[nn.Parameter]:
        values = list(self.base.parameters())
        if self.W_z is not None:
            values.extend(self.W_z.parameters())
        return values


@dataclass
class TrainingState:
    arm: ArmName
    replicate: int
    profile: Literal["train", "iid", "held_out"] = "train"
    seed_map: dict[str, int] = field(default_factory=dict)
    completed_update: int = 0
    next_episode_id: int = 0
    base_optimizer_steps: int = 0
    event_optimizer_steps: int = 0
    pending_cursor: CollectionCursor | None = None
    rngs: dict[str, np.random.Generator] = field(default_factory=dict)


def _seed(base: int, replicate: int) -> int:
    return int(base + 1000 * replicate)


def authoritative_seed_map(
    profile: Literal["train", "iid", "held_out"], replicate: int
) -> dict[str, int]:
    ledger_base = TRAIN_TASK_SEED if profile == "train" else (
        IID_EVAL_TASK_SEED if profile == "iid" else HELD_OUT_EVAL_TASK_SEED
    )
    return {
        "ledger": _seed(ledger_base, replicate),
        "order": _seed(TRAIN_ORDER_SEED, replicate),
        "primitive": _seed(TRAIN_ACTION_SEED, replicate),
        "opportunity": _seed(OPPORTUNITY_SEED, replicate),
        "event": _seed(EVENT_SEED, replicate),
        "mark": _seed(MARK_SEED, replicate),
    }


def make_training_state(
    arm: ArmName,
    replicate: int,
    *,
    profile: Literal["train", "iid", "held_out"] = "train",
) -> TrainingState:
    seed_map = authoritative_seed_map(profile, replicate)
    return TrainingState(
        arm=arm,
        replicate=int(replicate),
        profile=profile,
        seed_map=seed_map,
        rngs={name: np.random.default_rng(seed_map[name]) for name in RNG_NAMES},
    )


def initialize_arms(
    device: torch.device,
    *,
    replicate: int = 0,
    event_seed: int = EVENT_SEED,
    mark_seed: int = MARK_SEED,
) -> tuple[dict[ArmName, CommitmentArm], dict[ArmName, torch.optim.Optimizer], dict[ArmName, torch.optim.Optimizer | None]]:
    cpu_rng = torch.get_rng_state().clone()
    cuda_rngs = [value.clone() for value in torch.cuda.get_rng_state_all()] if torch.cuda.is_available() else []
    try:
        torch.manual_seed(_seed(MODEL_INITIALIZATION_SEED, replicate))
        ordinary = CommitmentArm("OR")
        base_state = deepcopy(ordinary.base.state_dict())
        dum = CommitmentArm("DUM")
        dum.base.load_state_dict(base_state, strict=True)
        assert dum.W_z is not None and dum.event_head is not None and dum.mark_head is not None
        torch.manual_seed(_seed(event_seed, replicate))
        dum.W_z.reset_parameters()
        dum.event_head.reset_parameters()
        torch.manual_seed(_seed(mark_seed, replicate))
        dum.mark_head.reset_parameters()
        ehc = CommitmentArm("EHC")
        ehc.base.load_state_dict(base_state, strict=True)
        assert ehc.W_z is not None and ehc.event_head is not None and ehc.mark_head is not None
        ehc.W_z.load_state_dict(deepcopy(dum.W_z.state_dict()), strict=True)
        ehc.event_head.load_state_dict(deepcopy(dum.event_head.state_dict()), strict=True)
        ehc.mark_head.load_state_dict(deepcopy(dum.mark_head.state_dict()), strict=True)
    finally:
        torch.set_rng_state(cpu_rng)
        if torch.cuda.is_available():
            torch.cuda.set_rng_state_all(cuda_rngs)
    arms: dict[ArmName, CommitmentArm] = {"OR": ordinary.to(device), "DUM": dum.to(device), "EHC": ehc.to(device)}
    base_optimizers = {
        name: torch.optim.Adam(arm.base_optimizer_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0)
        for name, arm in arms.items()
    }
    event_optimizers: dict[ArmName, torch.optim.Optimizer | None] = {
        "OR": None,
        "DUM": torch.optim.Adam(arms["DUM"].event_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0),
        "EHC": torch.optim.Adam(arms["EHC"].event_parameters(), lr=LEARNING_RATE, eps=1e-5, weight_decay=0.0),
    }
    if ordinary.base_parameter_count != PARAMETER_COUNT:
        raise RuntimeError("ordinary source parameter count drift")
    if dum.added_parameter_count != ADDED_PARAMETER_COUNT or ehc.added_parameter_count != ADDED_PARAMETER_COUNT:
        raise RuntimeError("commitment addition parameter count drift")
    return arms, base_optimizers, event_optimizers


def _normal_parameters(mark_output: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    mu, raw_scale = mark_output.split(MARK_DIM, dim=-1)
    return mu, 0.1 + 0.9 * torch.sigmoid(raw_scale)


def transformed_mark_component_logp(u: torch.Tensor, mu: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
    normal = -0.5 * torch.square((u - mu) / sigma) - torch.log(sigma) - 0.5 * math.log(2.0 * math.pi)
    log_jacobian = 2.0 * (math.log(2.0) - u - F.softplus(-2.0 * u))
    return normal - log_jacobian


def _event_input(observation: torch.Tensor, h_pre: torch.Tensor, context: torch.Tensor, z_pre: torch.Tensor) -> torch.Tensor:
    value = torch.cat((observation, h_pre, context, z_pre), dim=-1).detach()
    if value.shape[-1] != EVENT_INPUT_DIM:
        raise RuntimeError("event input width mismatch")
    return value


def _new_cursor(state: TrainingState, episode_ids: tuple[int, ...], device: torch.device, *, profile: Literal["train", "iid", "held_out"]) -> CollectionCursor:
    if state.profile != profile or state.seed_map != authoritative_seed_map(profile, state.replicate):
        raise ValueError("collector state/profile seed map mismatch")
    ledgers = tuple(make_noncalendar_ledger(v, profile=profile, task_seed=state.seed_map["ledger"], order_seed=state.seed_map["order"]) for v in episode_ids)
    return CollectionCursor(
        episode_ids=episode_ids,
        ledgers=ledgers,
        environments=[NoncalendarTrackingEnv(v) for v in ledgers],
        hidden=torch.zeros((len(episode_ids), MAX_LIFECYCLES, 32), device=device),
        lifecycles=[{} for _ in episode_ids],
        segments=[[] for _ in episode_ids],
    )


def _close_segment(cursor: CollectionCursor, env_index: int, key: int, *, reason: str, censored: bool) -> None:
    life = cursor.lifecycles[env_index].pop(key)
    cursor.segments[env_index].append(SegmentRecord(cursor.episode_ids[env_index], key, life.membership_epoch, life.segment_id, life.segment_start_active_step, life.active_steps, censored, reason, life.spell_opportunity_count))


def _zeros(shape: tuple[int, ...], *, dtype: torch.dtype = torch.float32) -> torch.Tensor:
    return torch.zeros(shape, dtype=dtype)


def collect_trajectory(
    arm: CommitmentArm,
    state: TrainingState,
    *,
    device: torch.device,
    episode_ids: Iterable[int] | None = None,
    cursor: CollectionCursor | None = None,
    max_steps: int | None = None,
    deterministic: bool = False,
    profile: Literal["train", "iid", "held_out"] = "train",
) -> EventTrajectory:
    if state.arm != arm.arm or set(state.rngs) != set(RNG_NAMES):
        raise ValueError("collector arm or owned-RNG key set mismatch")
    if cursor is None:
        ids = tuple(int(v) for v in episode_ids) if episode_ids is not None else tuple(
            range(state.next_episode_id, state.next_episode_id + FORMAL_NUM_ENVS)
        )
        if not ids:
            raise ValueError("collection requires episodes")
        cursor = _new_cursor(state, ids, device, profile=profile)
    else:
        if episode_ids is not None:
            raise ValueError("cursor continuation does not accept episode_ids")
        cursor_profile = cursor.ledgers[0].profile
        if any(ledger.profile != cursor_profile for ledger in cursor.ledgers):
            raise ValueError("mixed-profile collection cursor")
        profile = cursor_profile
        if state.profile != profile:
            raise ValueError("cursor/state profile mismatch")
    env_count = len(cursor.environments)
    remaining = HORIZON - cursor.environments[0].time
    steps = remaining if max_steps is None else min(int(max_steps), remaining)
    if steps <= 0 or any(env.time != cursor.environments[0].time for env in cursor.environments):
        raise ValueError("invalid synchronized collection cursor")

    names = (
        "observations", "active", "orders", "actions", "logp", "values", "rewards",
        "terminal", "h_before", "h_after", "prefix", "z", "kind", "event_input",
        "event_action", "event_u", "event_z_pre", "event_new_z", "candidate_u",
        "candidate_z", "cat_mask",
        "mark_mask", "old_cat", "old_mark", "old_joint", "epoch", "segment", "q",
    )
    rows: dict[str, list[torch.Tensor]] = {name: [] for name in names}
    arm.eval()
    with torch.no_grad():
        for _ in range(steps):
            time = cursor.environments[0].time
            cursor.hidden = cursor.hidden.detach().clone()
            obs_np = np.zeros((env_count, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
            active_np = np.zeros((env_count, MAX_LIFECYCLES), dtype=np.bool_)
            views = []
            for env_index, env in enumerate(cursor.environments):
                view = env.observe()
                views.append(view)
                for row_index, key in enumerate(view.active_keys):
                    obs_np[env_index, key] = view.observations[row_index]
                    active_np[env_index, key] = True
                for key in view.membership_change.terminally_left:
                    if arm.arm != "OR":
                        _close_segment(cursor, env_index, key, reason="TERMINAL_LEAVE", censored=True)
                    cursor.hidden[env_index, key].zero_()
                if arm.arm != "OR":
                    for key in view.membership_change.rejoined:
                        life = cursor.lifecycles[env_index].get(key)
                        if life is None:
                            raise RuntimeError("REJOIN lacks owned commitment lifecycle")
                        environment_epoch = cursor.environments[env_index].members[key].membership_epoch
                        if environment_epoch != life.membership_epoch + 1:
                            raise RuntimeError("REJOIN membership epoch is not the next owned epoch")
                        life.membership_epoch = environment_epoch
                    for key in view.membership_change.joined:
                        if key in cursor.lifecycles[env_index]:
                            raise RuntimeError("JOIN reused commitment lifecycle")
                        epoch = cursor.environments[env_index].members[key].membership_epoch
                        cursor.lifecycles[env_index][key] = LifecycleState(
                            epoch, torch.zeros(MARK_DIM, device=device), -1, 0, 0
                        )

            observations = torch.as_tensor(obs_np, device=device)
            active = torch.as_tensor(active_np, device=device)
            order = torch.as_tensor(frontier_order(cursor.ledgers, active_np, time), device=device)
            h_before = cursor.hidden.clone()
            prepared = arm.base.prepare_step(
                observations=observations, active_mask=active, validated=True
            )

            kind = torch.zeros((env_count, MAX_LIFECYCLES), dtype=torch.long, device=device)
            event_inputs = torch.zeros((env_count, MAX_LIFECYCLES, EVENT_INPUT_DIM), device=device)
            event_actions = torch.full((env_count, MAX_LIFECYCLES), -1, dtype=torch.long, device=device)
            event_u = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            event_z_pre = torch.zeros_like(event_u)
            event_new_z = torch.zeros_like(event_u)
            candidate_u = torch.zeros_like(event_u)
            candidate_z = torch.zeros_like(event_u)
            cat_mask = torch.zeros((env_count, MAX_LIFECYCLES), dtype=torch.bool, device=device)
            mark_mask = torch.zeros_like(cat_mask)
            old_cat = torch.zeros((env_count, MAX_LIFECYCLES), device=device)
            old_mark = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            old_joint = torch.zeros((env_count, MAX_LIFECYCLES), device=device)
            epochs = torch.full((env_count, MAX_LIFECYCLES), -1, dtype=torch.long, device=device)
            segments = torch.full_like(epochs, -1)
            q_before = torch.full_like(epochs, -1)
            primitive_z = torch.zeros((env_count, MAX_LIFECYCLES, MARK_DIM), device=device)
            requests: list[tuple[int, int, int, torch.Tensor, torch.Tensor]] = []

            if arm.arm != "OR":
                for env_index, view in enumerate(views):
                    for key in view.active_keys:
                        life = cursor.lifecycles[env_index][key]
                        primitive_z[env_index, key] = life.z
                        epochs[env_index, key] = life.membership_epoch
                        segments[env_index, key] = life.segment_id
                        q_before[env_index, key] = life.q
                        request_kind = CREATE if life.q < 0 else (KEEP if life.q == 0 else 0)
                        if request_kind:
                            z_pre = life.z.detach()
                            inp = _event_input(
                                observations[env_index, key],
                                h_before[env_index, key],
                                prepared.context[env_index],
                                z_pre,
                            )
                            requests.append((env_index, key, request_kind, inp, z_pre))

            selected_kind_grid = torch.zeros_like(kind)
            request_q = np.empty(len(requests), dtype=np.int64)
            if requests:
                assert arm.event_head is not None and arm.mark_head is not None
                packed_inputs = torch.stack([value[3] for value in requests])
                packed_z_pre = torch.stack([value[4] for value in requests])
                logits = arm.event_head(packed_inputs)
                mu, sigma = _normal_parameters(arm.mark_head(packed_inputs))
                create_mask = torch.as_tensor(
                    [value[2] == CREATE for value in requests], dtype=torch.bool, device=device
                )
                if deterministic:
                    selected_cat = torch.argmax(logits, dim=-1)
                    u = mu
                else:
                    event_uniforms = torch.as_tensor(
                        state.rngs["event"].random(len(requests)),
                        dtype=logits.dtype,
                        device=device,
                    )
                    selected_cat = torch.sum(
                        event_uniforms.unsqueeze(-1) > torch.cumsum(torch.softmax(logits, -1), -1),
                        dim=-1,
                    ).clamp(max=1)
                    mark_eps = torch.as_tensor(
                        state.rngs["mark"].standard_normal(
                            (len(requests), MARK_DIM)
                        ),
                        dtype=mu.dtype,
                        device=device,
                    )
                    u = mu + sigma * mark_eps
                selected_kind = torch.where(create_mask, torch.full_like(selected_cat, CREATE), selected_cat + KEEP)
                derived_cat_mask = ~create_mask
                derived_mark_mask = create_mask | selected_kind.eq(RENEW)
                component_logp = transformed_mark_component_logp(u.detach(), mu, sigma)
                categorical_logp = torch.gather(
                    F.log_softmax(logits, -1), 1, selected_cat.unsqueeze(-1)
                ).squeeze(-1)
                categorical_logp = torch.where(derived_cat_mask, categorical_logp, 0.0)
                component_logp = torch.where(
                    derived_mark_mask.unsqueeze(-1), component_logp, 0.0
                )
                candidate_tanh_u = torch.tanh(u).detach()
                packed_new_z = torch.where(
                    derived_mark_mask.unsqueeze(-1), candidate_tanh_u, packed_z_pre
                )
                env_indices = torch.as_tensor([v[0] for v in requests], dtype=torch.long, device=device)
                key_indices = torch.as_tensor([v[1] for v in requests], dtype=torch.long, device=device)
                kind[env_indices, key_indices] = selected_kind
                selected_kind_grid[env_indices, key_indices] = selected_kind
                event_inputs[env_indices, key_indices] = packed_inputs
                event_actions[env_indices, key_indices] = torch.where(
                    derived_cat_mask, selected_cat, torch.full_like(selected_cat, -1)
                )
                event_u[env_indices, key_indices] = torch.where(
                    derived_mark_mask.unsqueeze(-1), u.detach(), torch.zeros_like(u)
                )
                candidate_u[env_indices, key_indices] = u.detach()
                candidate_z[env_indices, key_indices] = candidate_tanh_u
                event_z_pre[env_indices, key_indices] = packed_z_pre
                event_new_z[env_indices, key_indices] = packed_new_z
                cat_mask[env_indices, key_indices] = derived_cat_mask
                mark_mask[env_indices, key_indices] = derived_mark_mask
                old_cat[env_indices, key_indices] = categorical_logp
                old_mark[env_indices, key_indices] = component_logp
                old_joint[env_indices, key_indices] = categorical_logp + component_logp.sum(-1)
                primitive_z[env_indices, key_indices] = packed_new_z
                request_q[:] = state.rngs["opportunity"].choice(
                    OPPORTUNITY_SUPPORT, size=len(requests)
                )

            if deterministic:
                primitive_kwargs: dict[str, Any] = {"deterministic": True}
            else:
                uniforms = torch.as_tensor(
                    state.rngs["primitive"].random(
                        (env_count, MAX_LIFECYCLES), dtype=np.float32
                    ),
                    device=device,
                )
                primitive_kwargs = {"sampling_uniforms": uniforms}
            output = arm.base.forward_step(
                observations=observations,
                active_mask=active,
                order=order,
                hidden=cursor.hidden,
                primitive_logit_bias=arm.primitive_bias(primitive_z),
                prepared=prepared,
                validated=True,
                **primitive_kwargs,
            )
            # The sole device-to-host metadata transfer for this physical row
            # contains both primitive actions and event decisions.
            host_metadata = torch.stack((output.actions, selected_kind_grid), dim=-1).cpu().numpy()
            for index, (env_index, key, request_kind, _inp, _z_pre) in enumerate(requests):
                life = cursor.lifecycles[env_index][key]
                selected_kind = int(host_metadata[env_index, key, 1])
                if request_kind == CREATE and selected_kind != CREATE:
                    raise RuntimeError("CREATE support drift")
                if request_kind != CREATE and selected_kind not in (KEEP, RENEW):
                    raise RuntimeError("opportunity support drift")
                if selected_kind != CREATE:
                    life.spell_opportunity_count += 1
                if selected_kind == RENEW:
                    cursor.segments[env_index].append(
                        SegmentRecord(
                            cursor.episode_ids[env_index], key, life.membership_epoch,
                            life.segment_id, life.segment_start_active_step,
                            life.active_steps, False, "RENEW",
                            life.spell_opportunity_count,
                        )
                    )
                    life.segment_id += 1
                    life.segment_start_active_step = life.active_steps
                    life.spell_opportunity_count = 0
                if selected_kind != CREATE:
                    life.non_create_opportunities += 1
                life.z = event_new_z[env_index, key].detach()
                life.q = int(request_q[index])
                epochs[env_index, key] = life.membership_epoch
                segments[env_index, key] = life.segment_id

            reward_np = np.zeros(env_count, dtype=np.float32)
            terminal_np = np.zeros(env_count, dtype=np.bool_)
            for env_index, (env, view) in enumerate(zip(cursor.environments, views)):
                reward, terminal_value, _ = env.step(
                    {key: int(host_metadata[env_index, key, 0]) for key in view.active_keys}
                )
                reward_np[env_index] = reward
                terminal_np[env_index] = terminal_value
                if arm.arm != "OR":
                    for key in view.active_keys:
                        life = cursor.lifecycles[env_index][key]
                        life.active_steps += 1
                        life.q -= 1
                    if terminal_value:
                        for key in tuple(cursor.lifecycles[env_index]):
                            _close_segment(
                                cursor, env_index, key,
                                reason="EPISODE_END", censored=True,
                            )

            values = {
                "observations": observations,
                "active": active,
                "orders": order,
                "actions": output.actions,
                "logp": output.token_log_probs,
                "values": output.value,
                "rewards": torch.as_tensor(reward_np, device=device),
                "terminal": torch.as_tensor(terminal_np, device=device),
                "h_before": h_before,
                "h_after": output.next_hidden,
                "prefix": output.prefix_counts,
                "z": primitive_z,
                "kind": kind,
                "event_input": event_inputs,
                "event_action": event_actions,
                "event_u": event_u,
                "event_z_pre": event_z_pre,
                "event_new_z": event_new_z,
                "candidate_u": candidate_u,
                "candidate_z": candidate_z,
                "cat_mask": cat_mask,
                "mark_mask": mark_mask,
                "old_cat": old_cat,
                "old_mark": old_mark,
                "old_joint": old_joint,
                "epoch": epochs,
                "segment": segments,
                "q": q_before,
            }
            for name, value in values.items():
                rows[name].append(value.detach())
            cursor.hidden = output.next_hidden.detach()

    finished = all(env.time == HORIZON for env in cursor.environments)
    outcomes = tuple(env.outcome() for env in cursor.environments) if finished else ()
    if finished:
        state.next_episode_id = max(cursor.episode_ids) + 1
        state.pending_cursor = None
        bootstrap = torch.zeros(env_count, device=device)
        next_cursor = None
    else:
        state.pending_cursor = cursor
        obs_np = np.zeros((env_count, MAX_LIFECYCLES, OBSERVATION_DIM), dtype=np.float32)
        active_np = np.zeros((env_count, MAX_LIFECYCLES), dtype=np.bool_)
        for env_index, env in enumerate(cursor.environments):
            clone = NoncalendarTrackingEnv.from_snapshot_state(env.snapshot_state())
            view = clone.observe()
            for row_index, key in enumerate(view.active_keys):
                obs_np[env_index, key] = view.observations[row_index]
                active_np[env_index, key] = True
        bootstrap = arm.base.prepare_step(
            observations=torch.as_tensor(obs_np, device=device),
            active_mask=torch.as_tensor(active_np, device=device),
            validated=True,
        ).value.detach()
        next_cursor = cursor
    stacked = {name: torch.stack(rows[name]) for name in names}
    return EventTrajectory(
        observations=stacked["observations"],
        active_mask=stacked["active"],
        orders=stacked["orders"],
        actions=stacked["actions"],
        old_log_probs=stacked["logp"],
        old_values=stacked["values"],
        rewards=stacked["rewards"],
        terminal=stacked["terminal"],
        hidden_before=stacked["h_before"],
        hidden_after=stacked["h_after"],
        prefix_counts=stacked["prefix"],
        primitive_z=stacked["z"],
        event_kind=stacked["kind"],
        event_inputs=stacked["event_input"],
        event_categorical_actions=stacked["event_action"],
        event_u=stacked["event_u"],
        event_z_pre=stacked["event_z_pre"],
        event_new_z=stacked["event_new_z"],
        candidate_u=stacked["candidate_u"],
        candidate_z=stacked["candidate_z"],
        event_cat_mask=stacked["cat_mask"],
        event_mark_mask=stacked["mark_mask"],
        event_old_cat_logp=stacked["old_cat"],
        event_old_mark_component_logp=stacked["old_mark"],
        event_old_joint_logp=stacked["old_joint"],
        membership_epoch=stacked["epoch"],
        segment_id=stacked["segment"],
        q_before=stacked["q"],
        outcomes=outcomes,
        segments=tuple(tuple(value) for value in cursor.segments),
        ledger_ids=cursor.episode_ids,
        cutoff=not finished,
        bootstrap_values=bootstrap,
        cursor=next_cursor,
    )

@dataclass
class ReplayOutput:
    log_probs: torch.Tensor
    entropies: torch.Tensor
    values: torch.Tensor
    hidden_after: torch.Tensor
    prefix_counts: torch.Tensor
    contexts: torch.Tensor
    event_inputs: torch.Tensor
    event_cat_mask: torch.Tensor
    event_mark_mask: torch.Tensor
    event_actions: torch.Tensor
    event_new_z: torch.Tensor
    event_cat_logp: torch.Tensor
    event_mark_component_logp: torch.Tensor
    event_joint_logp: torch.Tensor
    event_cat_entropy: torch.Tensor


def _replay_primitive(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    hidden = trajectory.hidden_before[0].to(device)
    logps: list[torch.Tensor] = []
    entropies: list[torch.Tensor] = []
    values: list[torch.Tensor] = []
    hidden_rows: list[torch.Tensor] = []
    prefixes: list[torch.Tensor] = []
    contexts: list[torch.Tensor] = []
    for time in range(trajectory.time_steps):
        reset_mask = trajectory.hidden_before[time].to(device).abs().sum(-1).eq(0.0)
        hidden = torch.where(reset_mask.unsqueeze(-1), torch.zeros_like(hidden), hidden)
        observations = trajectory.observations[time].to(device)
        active = trajectory.active_mask[time].to(device)
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        output = arm.base.forward_step(
            observations=observations,
            active_mask=active,
            order=trajectory.orders[time].to(device),
            hidden=hidden,
            teacher_actions=trajectory.actions[time].to(device),
            primitive_logit_bias=arm.primitive_bias(trajectory.primitive_z[time].to(device)),
            prepared=prepared,
            validated=True,
        )
        logps.append(output.token_log_probs)
        entropies.append(output.token_entropies)
        values.append(output.value)
        hidden_rows.append(output.next_hidden)
        prefixes.append(output.prefix_counts)
        contexts.append(prepared.context)
        hidden = output.next_hidden
    return (
        torch.stack(logps), torch.stack(entropies), torch.stack(values),
        torch.stack(hidden_rows), torch.stack(prefixes), torch.stack(contexts),
    )


def _replay_event_heads(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    contexts: torch.Tensor | None,
) -> tuple[
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
    torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor,
]:
    kind = trajectory.event_kind.to(device)
    cat_mask = kind.eq(KEEP) | kind.eq(RENEW)
    mark_mask = kind.eq(CREATE) | kind.eq(RENEW)
    event_mask = cat_mask | mark_mask
    actions = torch.where(cat_mask, kind - KEEP, torch.full_like(kind, -1))
    if contexts is None:
        reconstructed_inputs = trajectory.event_inputs.to(device)
    else:
        expanded_context = contexts.unsqueeze(2).expand(
            -1, -1, MAX_LIFECYCLES, -1
        )
        reconstructed_inputs = torch.cat(
            (
                trajectory.observations.to(device),
                trajectory.hidden_before.to(device),
                expanded_context,
                trajectory.event_z_pre.to(device),
            ),
            dim=-1,
        ).detach()
    cat_logp = torch.zeros_like(trajectory.event_old_cat_logp, device=device)
    mark_component = torch.zeros_like(
        trajectory.event_old_mark_component_logp, device=device
    )
    cat_entropy = torch.zeros_like(cat_logp)
    if arm.arm != "OR":
        assert arm.event_head is not None and arm.mark_head is not None
        inputs = reconstructed_inputs[event_mask]
        logits = arm.event_head(inputs)
        log_probability = F.log_softmax(logits, dim=-1)
        probability = torch.exp(log_probability)
        cat_entropy[event_mask] = -(probability * log_probability).sum(-1)
        safe_actions = actions[event_mask].clamp(min=0)
        cat_values = torch.gather(
            log_probability, 1, safe_actions.unsqueeze(-1)
        ).squeeze(-1)
        cat_logp[event_mask] = cat_values
        mu, sigma = _normal_parameters(arm.mark_head(inputs))
        u = trajectory.event_u.to(device)[event_mask]
        mark_component[event_mask] = transformed_mark_component_logp(u, mu, sigma)
    cat_logp = torch.where(cat_mask, cat_logp, 0.0)
    mark_component = torch.where(mark_mask.unsqueeze(-1), mark_component, 0.0)
    joint = cat_logp + mark_component.sum(-1)
    u = trajectory.event_u.to(device)
    z_pre = trajectory.event_z_pre.to(device)
    reconstructed_new_z = torch.where(
        mark_mask.unsqueeze(-1),
        torch.tanh(u),
        torch.where(cat_mask.unsqueeze(-1), z_pre, torch.zeros_like(z_pre)),
    ).detach()
    return (
        reconstructed_inputs, cat_mask, mark_mask, actions,
        reconstructed_new_z, cat_logp, mark_component, joint, cat_entropy,
    )


def replay_trajectory(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
) -> ReplayOutput:
    primitive = _replay_primitive(arm, trajectory, device=device)
    events = _replay_event_heads(
        arm, trajectory, device=device, contexts=primitive[5]
    )
    return ReplayOutput(
        log_probs=primitive[0],
        entropies=primitive[1],
        values=primitive[2],
        hidden_after=primitive[3],
        prefix_counts=primitive[4],
        contexts=primitive[5],
        event_inputs=events[0],
        event_cat_mask=events[1],
        event_mark_mask=events[2],
        event_actions=events[3],
        event_new_z=events[4],
        event_cat_logp=events[5],
        event_mark_component_logp=events[6],
        event_joint_logp=events[7],
        event_cat_entropy=events[8],
    )


def replay_errors(replay: ReplayOutput, trajectory: EventTrajectory) -> dict[str, float]:
    device = replay.log_probs.device
    active = trajectory.active_mask.to(device)
    stored_cat = trajectory.event_cat_mask.to(device)
    stored_mark = trajectory.event_mark_mask.to(device)
    derived_event = replay.event_cat_mask | replay.event_mark_mask

    def maximum(value: torch.Tensor, mask: torch.Tensor | None = None) -> float:
        selected = value if mask is None else value[mask]
        return float(selected.abs().max().detach().cpu()) if selected.numel() else 0.0

    event_input_mask = derived_event.unsqueeze(-1).expand_as(replay.event_inputs)
    mark_component_mask = replay.event_mark_mask.unsqueeze(-1).expand_as(
        replay.event_mark_component_logp
    )
    kind = trajectory.event_kind.to(device)
    kind_support = kind.eq(0) | kind.eq(CREATE) | kind.eq(KEEP) | kind.eq(RENEW)
    action_exact = torch.equal(
        trajectory.event_categorical_actions.to(device)[replay.event_cat_mask],
        replay.event_actions[replay.event_cat_mask],
    )
    detached_exact = (
        not trajectory.event_inputs.requires_grad
        and not trajectory.event_z_pre.requires_grad
        and not trajectory.event_new_z.requires_grad
    )
    return {
        "primitive_component": maximum(
            replay.log_probs - trajectory.old_log_probs.to(device), active
        ),
        "primitive_joint": maximum(
            torch.where(
                active, replay.log_probs - trajectory.old_log_probs.to(device), 0.0
            ).sum(-1)
        ),
        "value": maximum(replay.values - trajectory.old_values.to(device)),
        "hidden": maximum(
            replay.hidden_after - trajectory.hidden_after.to(device)
        ),
        "prefix": maximum(
            replay.prefix_counts - trajectory.prefix_counts.to(device)
        ),
        "event_input": maximum(
            replay.event_inputs - trajectory.event_inputs.to(device), event_input_mask
        ),
        "categorical_component": maximum(
            replay.event_cat_logp - trajectory.event_old_cat_logp.to(device),
            replay.event_cat_mask,
        ),
        "mark_component": maximum(
            replay.event_mark_component_logp
            - trajectory.event_old_mark_component_logp.to(device),
            mark_component_mask,
        ),
        "event_joint": maximum(
            replay.event_joint_logp - trajectory.event_old_joint_logp.to(device),
            derived_event,
        ),
        "event_new_z": maximum(
            replay.event_new_z - trajectory.event_new_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "primitive_event_z": maximum(
            replay.event_new_z - trajectory.primitive_z.to(device),
            derived_event.unsqueeze(-1).expand_as(replay.event_new_z),
        ),
        "mask_mismatch": float(
            not torch.equal(stored_cat, replay.event_cat_mask)
            or not torch.equal(stored_mark, replay.event_mark_mask)
        ),
        "kind_support_mismatch": float(not bool(kind_support.all())),
        "event_action_mismatch": float(not action_exact),
        "detach_mismatch": float(not detached_exact),
    }


def validate_replay(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    tolerance: float = REPLAY_TOLERANCE,
) -> tuple[ReplayOutput, dict[str, float]]:
    replay = replay_trajectory(arm, trajectory, device=device)
    errors = replay_errors(replay, trajectory)
    exact_names = (
        "mask_mismatch", "kind_support_mismatch",
        "event_action_mismatch", "detach_mismatch",
    )
    if any(errors[name] != 0.0 for name in exact_names):
        raise RuntimeError(f"semantic replay exact-support mismatch {errors}")
    approximate_names = tuple(name for name in errors if name not in exact_names)
    if any(errors[name] > tolerance for name in approximate_names):
        raise RuntimeError(f"semantic replay tolerance mismatch {errors}")
    return replay, errors


def action_distribution_tv(
    logits_natural: torch.Tensor, logits_perm: torch.Tensor
) -> torch.Tensor:
    """Primitive action-distribution total variation from two logit vectors.

    `I_TV = 0.5 * sum_a |pi(a) - pi(a_perm)|`, where `pi`/`pi_perm` are the
    softmax distributions induced by `logits_natural`/`logits_perm` along
    their last dimension. This is exactly zero whenever the two logit
    vectors differ only by a constant (softmax is shift-invariant), and it
    always lies in `[0, 1]` because it is the total-variation distance
    between two categorical distributions over the same three actions.
    """

    pi_natural = torch.softmax(logits_natural, dim=-1)
    pi_perm = torch.softmax(logits_perm, dim=-1)
    return 0.5 * torch.abs(pi_natural - pi_perm).sum(dim=-1)


def base_primitive_logits(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    env_index: int,
    time: int,
    device: torch.device,
) -> dict[int, torch.Tensor]:
    """Recompute pre-bias primitive logits for one recorded physical step.

    Reuses `DirectPrimitiveARPolicy`'s exact member/context encoding, GRU
    cell and action head with the natural recorded hidden state and
    teacher-forced natural actions, so the reconstructed autoregressive
    prefix matches the one that actually produced the stored trajectory
    (each active key's own hidden slot is untouched until its own position,
    so its pre-step hidden state always equals `trajectory.hidden_before`).
    `primitive_logit_bias` is intentionally not added here; callers combine
    the result with `arm.primitive_bias(z)` themselves, exactly reproducing
    `forward_step`'s `logits = base_logits + primitive_logit_bias`
    composition.
    """

    observations = trajectory.observations[time, env_index : env_index + 1].to(device)
    active = trajectory.active_mask[time, env_index : env_index + 1].to(device)
    order = trajectory.orders[time, env_index : env_index + 1].to(device)
    hidden_before = trajectory.hidden_before[time, env_index : env_index + 1].to(device)
    natural_actions = trajectory.actions[time, env_index : env_index + 1].to(device)
    logits_by_key: dict[int, torch.Tensor] = {}
    with torch.no_grad():
        prepared = arm.base.prepare_step(
            observations=observations, active_mask=active, validated=True
        )
        active_count = int(active.sum(dim=1).item())
        prefix = torch.zeros(
            (1, ACTION_COUNT), dtype=observations.dtype, device=device
        )
        for position in range(active_count):
            focal = int(order[0, position].item())
            local_embedding = prepared.member_embeddings[:, focal]
            local_hidden = hidden_before[:, focal]
            candidate_hidden = arm.base.actor_rnn(
                torch.cat((local_embedding, prepared.context, prefix), dim=-1),
                local_hidden,
            )
            logits = arm.base.action_head(
                torch.cat((candidate_hidden, prefix), dim=-1)
            )
            logits_by_key[focal] = logits[0]
            selected = int(natural_actions[0, focal].item())
            prefix = prefix.clone()
            prefix[0, selected] += 1.0
    return logits_by_key


def natural_and_permuted_action_tv(
    arm: CommitmentArm,
    trajectory: EventTrajectory,
    *,
    env_index: int,
    time: int,
    device: torch.device,
) -> list[float]:
    """Per-active-key primitive `I_TV` under a same-step `z` derangement.

    Empty unless the arm carries the `W_z` treatment (EHC) and at least two
    lifecycles are active at this step. Derangement reuses the registered
    `torch.roll(z, 1, 0)` strategy over the active keys at this physical
    step. Observation, recurrent hidden state, action mask, active-set
    context and primitive prefix are held fixed at their natural recorded
    values (via `base_primitive_logits`); only `z` differs between the two
    action distributions being compared.
    """

    if arm.arm != "EHC" or arm.W_z is None:
        return []
    active_row = trajectory.active_mask[time, env_index].to(device)
    keys = torch.nonzero(active_row, as_tuple=True)[0]
    if keys.numel() < 2:
        return []
    z = trajectory.primitive_z[time, env_index, keys].to(device)
    perm_z = torch.roll(z, 1, 0)
    base_logits = base_primitive_logits(
        arm, trajectory, env_index=env_index, time=time, device=device
    )
    values: list[float] = []
    with torch.no_grad():
        for index, key in enumerate(keys.tolist()):
            logits = base_logits[key]
            natural_logits = logits + arm.primitive_bias(z[index])
            perm_logits = logits + arm.primitive_bias(perm_z[index])
            tv = action_distribution_tv(natural_logits, perm_logits)
            values.append(float(tv.detach().cpu()))
    return values


def _pack_trajectory_once(trajectory: EventTrajectory, device: torch.device) -> EventTrajectory:
    """Transfer the collected tensor package once and reuse it for all epochs."""

    tensor_fields = (
        "observations", "active_mask", "orders", "actions", "old_log_probs",
        "old_values", "rewards", "terminal", "hidden_before", "hidden_after",
        "prefix_counts", "primitive_z", "event_kind", "event_inputs",
        "event_categorical_actions", "event_u", "event_new_z", "event_cat_mask",
        "event_mark_mask", "event_old_cat_logp", "event_old_mark_component_logp",
        "event_old_joint_logp", "event_z_pre", "candidate_u", "candidate_z",
        "membership_epoch", "segment_id", "q_before",
        "bootstrap_values",
    )
    return replace(
        trajectory,
        **{name: getattr(trajectory, name).to(device) for name in tensor_fields},
    )


def compute_gae(trajectory: EventTrajectory, *, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    rewards = trajectory.rewards.to(device); values = trajectory.old_values.to(device); terminal = trajectory.terminal.to(device); advantages = torch.zeros_like(rewards); running = torch.zeros(rewards.shape[1], device=device); next_value = trajectory.bootstrap_values.to(device)
    for time in reversed(range(rewards.shape[0])):
        continuation = (~terminal[time]).to(rewards.dtype); delta = rewards[time] + GAMMA * next_value * continuation - values[time]; running = delta + GAMMA * GAE_LAMBDA * continuation * running; advantages[time] = running; next_value = values[time]
    returns = advantages + values; return (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-8), returns


def optimize_update(
    arm: CommitmentArm,
    base_optimizer: torch.optim.Optimizer,
    event_optimizer: torch.optim.Optimizer | None,
    state: TrainingState,
    trajectory: EventTrajectory,
    *,
    device: torch.device,
    ppo_passes: int = PPO_PASSES,
) -> dict[str, Any]:
    if trajectory.cutoff:
        raise ValueError("updates require a complete episode rollout")
    packed = _pack_trajectory_once(trajectory, device)
    arm.train()
    _validated_replay, errors = validate_replay(
        arm, packed, device=device, tolerance=REPLAY_TOLERANCE
    )
    advantages, returns = compute_gae(packed, device=device)
    active = packed.active_mask
    old_logp = packed.old_log_probs
    old_values = packed.old_values
    event_mask = packed.event_kind.eq(CREATE) | packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)
    old_joint = packed.event_old_joint_logp
    has_categorical_events = bool(
        (packed.event_kind.eq(KEEP) | packed.event_kind.eq(RENEW)).any().detach().cpu()
    )
    metrics: dict[str, Any] = {
        "replay": errors,
        "base_steps": 0,
        "event_steps": 0,
        "primitive_replays": 0,
        "event_head_replays": 0,
        "packed_trajectory_count": 1,
        "finite": True,
        "base_non_none_gradients": [],
        "base_zero_gradients": [],
        "event_non_none_gradients": [],
    }
    for _ in range(int(ppo_passes)):
        primitive = _replay_primitive(arm, packed, device=device)
        metrics["primitive_replays"] += 1
        ratio = torch.exp(primitive[0] - old_logp)
        expanded_advantage = advantages.unsqueeze(-1)
        surrogate = torch.minimum(
            ratio * expanded_advantage,
            torch.clamp(ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
            * expanded_advantage,
        )
        counts = active.sum(-1).clamp_min(1)
        policy_loss = -(
            torch.where(active, surrogate, 0.0).sum(-1) / counts
        ).mean()
        entropy = (
            torch.where(active, primitive[1], 0.0).sum(-1) / counts
        ).mean()
        clipped_values = old_values + torch.clamp(
            primitive[2] - old_values, -VALUE_CLIP, VALUE_CLIP
        )
        value_loss = torch.maximum(
            (primitive[2] - returns).square(),
            (clipped_values - returns).square(),
        ).mean()
        base_loss = (
            policy_loss + VALUE_COEFFICIENT * value_loss
            - ENTROPY_COEFFICIENT * entropy
        )
        base_optimizer.zero_grad(set_to_none=True)
        base_loss.backward()
        base_parameters = arm.base_optimizer_parameters()
        base_norm = torch.nn.utils.clip_grad_norm_(base_parameters, GRADIENT_CLIP)
        metrics["finite"] = metrics["finite"] and bool(
            torch.isfinite(base_loss).detach().cpu()
        ) and bool(torch.isfinite(base_norm).detach().cpu())
        metrics["base_non_none_gradients"].append(
            sum(parameter.grad is not None for parameter in base_parameters)
        )
        metrics["base_zero_gradients"].append(
            sum(
                parameter.grad is not None
                and bool(torch.count_nonzero(parameter.grad).eq(0).detach().cpu())
                for parameter in base_parameters
            )
        )
        base_optimizer.step()
        metrics["base_steps"] += 1

        if event_optimizer is not None:
            events = _replay_event_heads(
                arm, packed, device=device, contexts=None
            )
            metrics["event_head_replays"] += 1
            event_advantage = advantages.unsqueeze(-1).expand_as(event_mask)[event_mask]
            event_ratio = torch.exp(events[7][event_mask] - old_joint[event_mask])
            event_surrogate = torch.minimum(
                event_ratio * event_advantage,
                torch.clamp(event_ratio, 1.0 - PPO_CLIP, 1.0 + PPO_CLIP)
                * event_advantage,
            )
            categorical_mask = events[1]
            categorical_entropy = (
                events[8][categorical_mask].mean()
                if has_categorical_events
                else torch.zeros((), device=device)
            )
            event_loss = (
                -event_surrogate.mean()
                - EVENT_ENTROPY_COEFFICIENT * categorical_entropy
            )
            event_optimizer.zero_grad(set_to_none=True)
            event_loss.backward()
            event_parameters = arm.event_parameters()
            event_norm = torch.nn.utils.clip_grad_norm_(
                event_parameters, GRADIENT_CLIP
            )
            metrics["finite"] = metrics["finite"] and bool(
                torch.isfinite(event_loss).detach().cpu()
            ) and bool(torch.isfinite(event_norm).detach().cpu())
            metrics["event_non_none_gradients"].append(
                sum(parameter.grad is not None for parameter in event_parameters)
            )
            event_optimizer.step()
            metrics["event_steps"] += 1
    if metrics["primitive_replays"] != int(ppo_passes):
        raise RuntimeError("primitive replay count drift")
    state.completed_update += 1
    state.base_optimizer_steps += int(ppo_passes)
    state.event_optimizer_steps += int(
        ppo_passes if event_optimizer is not None else 0
    )
    return metrics

def _rng_states(state: TrainingState) -> dict[str, Any]:
    if set(state.rngs) != set(RNG_NAMES):
        raise ValueError("owned-RNG key set mismatch")
    return {name: deepcopy(state.rngs[name].bit_generator.state) for name in RNG_NAMES}


def runtime_rng_snapshot() -> dict[str, Any]:
    return {
        "python": deepcopy(random.getstate()),
        "numpy": deepcopy(np.random.get_state()),
        "torch_cpu": torch.get_rng_state().clone(),
        "torch_cuda": [
            value.clone() for value in torch.cuda.get_rng_state_all()
        ] if torch.cuda.is_available() else [],
    }


def _nested_equal(left: Any, right: Any) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return torch.equal(left.detach().cpu(), right.detach().cpu())
    if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
        return np.array_equal(left, right)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _nested_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(
            _nested_equal(a, b) for a, b in zip(left, right)
        )
    return bool(left == right)


def runtime_rng_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _nested_equal(dict(left), dict(right))


def save_checkpoint(
    path: Path,
    *,
    arm: CommitmentArm,
    base_optimizer: torch.optim.Optimizer,
    event_optimizer: torch.optim.Optimizer | None,
    state: TrainingState,
) -> None:
    if state.pending_cursor is not None:
        raise ValueError("checkpoint requires an empty rollout buffer")
    if state.arm != arm.arm or (event_optimizer is None) != (arm.arm == "OR"):
        raise ValueError("checkpoint arm/optimizer ownership mismatch")
    if state.seed_map != authoritative_seed_map(state.profile, state.replicate):
        raise ValueError("checkpoint seed map drift")
    path.parent.mkdir(parents=True, exist_ok=True)
    global_state = runtime_rng_snapshot()
    payload = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "kind": CHECKPOINT_KIND,
        "contract": registered_contract(),
        "arm": arm.arm,
        "replicate": state.replicate,
        "profile": state.profile,
        "seed_map": dict(state.seed_map),
        "model_state": arm.state_dict(),
        "base_optimizer_state": base_optimizer.state_dict(),
        "event_optimizer_state": (
            None if event_optimizer is None else event_optimizer.state_dict()
        ),
        "completed_update": state.completed_update,
        "next_episode_id": state.next_episode_id,
        "exposure": {
            "base": state.base_optimizer_steps,
            "event": state.event_optimizer_steps,
        },
        "normalizers": None,
        "collector": {
            "position": 0,
            "pending_environments": [],
            "membership_snapshots": [],
            "accumulators": [],
            "lifecycles": [],
            "segments": [],
            "masks": [],
        },
        "python_rng": global_state["python"],
        "numpy_global_rng": global_state["numpy"],
        "torch_cpu_rng": global_state["torch_cpu"],
        "torch_cuda_rng": global_state["torch_cuda"],
        "owned_rngs": _rng_states(state),
    }
    torch.save(payload, path)


def load_checkpoint(
    path: Path,
    *,
    device: torch.device,
    expected_arm: ArmName,
    expected_replicate: int,
    formal_evaluation: bool = False,
) -> tuple[
    CommitmentArm,
    torch.optim.Optimizer,
    torch.optim.Optimizer | None,
    TrainingState,
]:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    required = {
        "schema_version", "kind", "contract", "arm", "replicate", "profile",
        "seed_map", "model_state", "base_optimizer_state",
        "event_optimizer_state", "completed_update", "next_episode_id",
        "exposure", "normalizers", "collector", "python_rng",
        "numpy_global_rng", "torch_cpu_rng", "torch_cuda_rng", "owned_rngs",
    }
    if set(payload) != required:
        raise ValueError("checkpoint key set mismatch")
    if (
        payload["schema_version"] != CHECKPOINT_SCHEMA_VERSION
        or payload["kind"] != CHECKPOINT_KIND
        or payload["contract"] != registered_contract()
    ):
        raise ValueError("checkpoint registered contract mismatch")
    if payload["arm"] != expected_arm or int(payload["replicate"]) != int(expected_replicate):
        raise ValueError("checkpoint expected arm/replicate mismatch")
    profile = payload["profile"]
    if profile not in ("train", "iid", "held_out"):
        raise ValueError("checkpoint profile mismatch")
    expected_seed_map = authoritative_seed_map(profile, expected_replicate)
    if payload["seed_map"] != expected_seed_map:
        raise ValueError("checkpoint seed map mismatch")
    if set(payload["owned_rngs"]) != set(RNG_NAMES):
        raise ValueError("checkpoint owned-RNG key set mismatch")
    event_state = payload["event_optimizer_state"]
    if (expected_arm == "OR" and event_state is not None) or (
        expected_arm != "OR" and event_state is None
    ):
        raise ValueError("checkpoint event optimizer ownership mismatch")
    if payload["normalizers"] is not None or payload["collector"] != {
        "position": 0,
        "pending_environments": [],
        "membership_snapshots": [],
        "accumulators": [],
        "lifecycles": [],
        "segments": [],
        "masks": [],
    }:
        raise ValueError("checkpoint boundary is not empty")
    completed_update = int(payload["completed_update"])
    next_episode_id = int(payload["next_episode_id"])
    base_steps = int(payload["exposure"]["base"])
    event_steps = int(payload["exposure"]["event"])
    expected_event_steps = 0 if expected_arm == "OR" else completed_update * PPO_PASSES
    if base_steps != completed_update * PPO_PASSES or event_steps != expected_event_steps:
        raise ValueError("checkpoint optimizer exposure mismatch")
    if formal_evaluation and (
        profile != "train"
        or completed_update != FORMAL_UPDATES
        or next_episode_id != FORMAL_TRAIN_EPISODES
        or base_steps != FORMAL_UPDATES * PPO_PASSES
        or event_steps != (0 if expected_arm == "OR" else FORMAL_UPDATES * PPO_PASSES)
    ):
        raise ValueError("formal evaluation accepts only the registered update-250 boundary")
    if len(payload["torch_cuda_rng"]) != (
        torch.cuda.device_count() if torch.cuda.is_available() else 0
    ):
        raise ValueError("checkpoint CUDA RNG device-set mismatch")

    arms, base_optimizers, event_optimizers = initialize_arms(
        device, replicate=expected_replicate
    )
    arm = arms[expected_arm]
    base_optimizer = base_optimizers[expected_arm]
    event_optimizer = event_optimizers[expected_arm]
    arm.load_state_dict(payload["model_state"], strict=True)
    base_optimizer.load_state_dict(payload["base_optimizer_state"])
    if event_optimizer is not None:
        event_optimizer.load_state_dict(event_state)
    for optimizer in (base_optimizer, event_optimizer):
        if optimizer is not None:
            for optimizer_state in optimizer.state.values():
                for key, value in optimizer_state.items():
                    if isinstance(value, torch.Tensor):
                        optimizer_state[key] = value.to(device)
    state = make_training_state(
        expected_arm, expected_replicate, profile=profile
    )
    state.completed_update = completed_update
    state.next_episode_id = next_episode_id
    state.base_optimizer_steps = base_steps
    state.event_optimizer_steps = event_steps
    for name in RNG_NAMES:
        state.rngs[name].bit_generator.state = deepcopy(payload["owned_rngs"][name])
    random.setstate(payload["python_rng"])
    np.random.set_state(payload["numpy_global_rng"])
    torch.set_rng_state(payload["torch_cpu_rng"])
    if torch.cuda.is_available():
        torch.cuda.set_rng_state_all(payload["torch_cuda_rng"])
    return arm, base_optimizer, event_optimizer, state


def compare_continuations(
    left_arm: CommitmentArm,
    right_arm: CommitmentArm,
    left_trajectory: EventTrajectory,
    right_trajectory: EventTrajectory,
    left_optimizer: torch.optim.Optimizer,
    right_optimizer: torch.optim.Optimizer,
    left_event_optimizer: torch.optim.Optimizer | None,
    right_event_optimizer: torch.optim.Optimizer | None,
    left_state: TrainingState,
    right_state: TrainingState,
    left_global_rng: Mapping[str, Any],
    right_global_rng: Mapping[str, Any],
) -> dict[str, Any]:
    discrete_names = (
        "active_mask", "orders", "actions", "terminal", "event_kind",
        "event_categorical_actions", "event_cat_mask", "event_mark_mask",
        "membership_epoch", "segment_id", "q_before",
    )
    continuous_names = (
        "observations", "old_log_probs", "old_values", "hidden_before",
        "hidden_after", "prefix_counts", "primitive_z", "event_inputs",
        "event_u", "event_z_pre", "event_new_z", "event_old_cat_logp",
        "event_old_mark_component_logp", "event_old_joint_logp",
    )
    discrete_equal = all(
        torch.equal(getattr(left_trajectory, name), getattr(right_trajectory, name))
        for name in discrete_names
    )
    continuous_error = max(
        float(
            torch.max(
                torch.abs(
                    getattr(left_trajectory, name)
                    - getattr(right_trajectory, name)
                )
            ).detach().cpu()
        )
        for name in continuous_names
    )
    lifecycle_equal = (
        left_trajectory.ledger_ids == right_trajectory.ledger_ids
        and left_trajectory.outcomes == right_trajectory.outcomes
        and left_trajectory.segments == right_trajectory.segments
    )
    return {
        "discrete_equal": discrete_equal,
        "lifecycle_equal": lifecycle_equal,
        "owned_rng_equal": _nested_equal(
            _rng_states(left_state), _rng_states(right_state)
        ),
        "global_rng_equal": runtime_rng_equal(left_global_rng, right_global_rng),
        "continuous_error": continuous_error,
        "model_error": nested_state_maximum_difference(
            left_arm.state_dict(), right_arm.state_dict()
        ),
        "base_optimizer_error": nested_state_maximum_difference(
            left_optimizer.state_dict(), right_optimizer.state_dict()
        ),
        "event_optimizer_error": nested_state_maximum_difference(
            None if left_event_optimizer is None else left_event_optimizer.state_dict(),
            None if right_event_optimizer is None else right_event_optimizer.state_dict(),
        ),
    }

def factor_counts(trajectory: EventTrajectory) -> dict[str, int]:
    return {"create": int((trajectory.event_kind == CREATE).sum()), "keep": int((trajectory.event_kind == KEEP).sum()), "renew": int((trajectory.event_kind == RENEW).sum()), "categorical": int(trajectory.event_cat_mask.sum()), "mark": int(trajectory.event_mark_mask.sum())}


def parameter_and_optimizer_counts(arm: CommitmentArm, base_optimizer: torch.optim.Optimizer, event_optimizer: torch.optim.Optimizer | None) -> dict[str, int]:
    optimizer_count = lambda opt: 0 if opt is None else sum(p.numel() for group in opt.param_groups for p in group["params"])
    return {"base_model": arm.base_parameter_count, "added_model": arm.added_parameter_count, "base_optimizer": optimizer_count(base_optimizer), "event_optimizer": optimizer_count(event_optimizer)}
