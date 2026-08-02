"""Direct owner of event-held commitment trajectory collection."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import math
from time import perf_counter
from typing import Any, Iterable, Literal, Mapping

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

from ha_ctse_process.dynamic_roster_testbed import (
    ACTION_COUNT,
    HORIZON,
    MAX_LIFECYCLES,
    OBSERVATION_DIM,
)
from ha_ctse_process.event_commitment_rng import (
    OPPORTUNITY_SUPPORT,
    RNG_NAMES,
    _canonical_json_digest,
    _float32_payload,
    _raw_event_trace_digest,
    authoritative_seed_map,
    collection_rng_schedules,
    make_rng_binding,
    owned_rng_states,
    validate_rng_binding,
)
from ha_ctse_process.event_commitment_types import (
    CollectionCursor,
    CommitmentArm,
    EVENT_INPUT_DIM,
    EventTrajectory,
    LifecycleState,
    MARK_DIM,
    SegmentRecord,
    TrainingState,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    FORMAL_NUM_ENVS,
    NoncalendarLedger,
    NoncalendarTrackingEnv,
    TrackingOutcome,
    frontier_order,
    make_noncalendar_ledger,
)

CREATE, KEEP, RENEW = 1, 2, 3

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


def _new_cursor(
    state: TrainingState, episode_ids: tuple[int, ...], device: torch.device,
    *, profile: Literal["train", "iid", "held_out"],
    audit_trace: dict[str, list[dict[str, Any]]] | None = None,
) -> CollectionCursor:

    if state.profile != profile or state.seed_map != authoritative_seed_map(profile, state.replicate):
        raise ValueError("collector state/profile seed map mismatch")
    ledgers = tuple(
        make_noncalendar_ledger(
            v, profile=profile, task_seed=state.seed_map["ledger"],
            order_seed=state.seed_map["order"], audit_trace=audit_trace,
        )
        for v in episode_ids
    )
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


def _ledger_audit_evidence(ledger: NoncalendarLedger) -> dict[str, Any]:
    payload = {
        "episode_id": int(ledger.episode_id), "base_id": int(ledger.base_id),
        "sign_parity": int(ledger.sign_parity), "profile": ledger.profile,
        "generation_attempt": int(ledger.generation_attempt),
        "routing_permutation": list(ledger.routing_permutation),
        "initial_count": int(ledger.initial_count),
        "temporary_key": int(ledger.temporary_key),
        "terminal_key": int(ledger.terminal_key),
        "duration_streams": ledger.duration_streams.tolist(),
        "initial_targets": ledger.initial_targets.tolist(),
        "direct_frontier_priorities": ledger.direct_frontier_priorities.tolist(),

    }
    return payload | {"ledger_digest": _canonical_json_digest(payload)}


@dataclass
class _AuditRowStream:
    """One fork-row replay stream with independent consumption state."""

    values: np.ndarray
    position: int = 0

    def _take(self, size: int) -> np.ndarray:
        stop = self.position + int(size)
        if stop > int(self.values.size):
            raise RuntimeError("batched fork row stream exhausted")
        result = self.values.reshape(-1)[self.position:stop].copy()
        self.position = stop
        return result

    def random(

        self, size: int | tuple[int, ...] | None = None, dtype: Any = np.float64
    ) -> np.ndarray | float:
        shape = () if size is None else ((size,) if isinstance(size, int) else tuple(size))
        count = int(np.prod(shape, dtype=np.int64)) if shape else 1
        result = self._take(count).astype(dtype, copy=False)
        return float(result[0]) if not shape else result.reshape(shape)

    def standard_normal(
        self, size: int | tuple[int, ...] | None = None
    ) -> np.ndarray | float:
        return self.random(size=size, dtype=np.float64)

    def choice(self, _support: Any, size: int | tuple[int, ...] | None = None) -> Any:
        result = self.random(size=size, dtype=np.int64)
        return int(result) if size is None else result

    def consumption_record(self, terminal_state: Mapping[str, Any]) -> dict[str, Any]:
        consumed = self.values.reshape(-1)[: self.position]
        return {
            "position": int(self.position),

            "consumed_bytes_digest": hashlib.sha256(
                consumed.tobytes(order="C")
            ).hexdigest(),
            "terminal_state": deepcopy(dict(terminal_state)),
        }


def _audit_row_draw(
    row_rngs: list[Mapping[str, _AuditRowStream]],
    requests: list[tuple[int, int, int, torch.Tensor, torch.Tensor]],
    name: str,
    *,
    width: int = 1,
    dtype: Any = np.float64,
) -> np.ndarray:
    values = np.empty((len(requests), width), dtype=dtype)
    offset = 0
    while offset < len(requests):
        env_index = int(requests[offset][0])
        stop = offset + 1

        while stop < len(requests) and int(requests[stop][0]) == env_index:
            stop += 1
        shape: int | tuple[int, int] = (
            stop - offset if width == 1 else (stop - offset, width)
        )
        method = (
            row_rngs[env_index][name].standard_normal
            if name == "mark"
            else row_rngs[env_index][name].random
        )
        drawn = np.asarray(method(shape), dtype=dtype).reshape(stop - offset, width)
        values[offset:stop] = drawn
        offset = stop
    return values[:, 0] if width == 1 else values


def _row_stable_event_heads(
    inputs: torch.Tensor,
    event_head: nn.Linear,
    mark_head: nn.Linear,

) -> tuple[torch.Tensor, torch.Tensor]:
    """Evaluate both event heads with one row-local float32 reduction path.

    Each output coordinate is reduced only across that row's input features,
    so its binary32 result cannot depend on the number or ordering of other
    packed requests. Collection, fork collection and teacher replay all call
    this helper; there is intentionally no direct ``nn.Linear`` replay path.
    """

    if not (
        inputs.dtype == torch.float32
        and event_head.weight.dtype == torch.float32
        and mark_head.weight.dtype == torch.float32
        and event_head.bias is not None
        and mark_head.bias is not None
        and event_head.bias.dtype == torch.float32
        and mark_head.bias.dtype == torch.float32
    ):
        raise RuntimeError("event/mark heads require explicit float32 evaluation")
    row_count = int(inputs.shape[0])

    # CUDA selects a different small-outer-dimension reduction below the
    # registered 16-environment collection width. Zero-row padding keeps
    # every partition on the same reduction path while retaining the exact
    # arithmetic already used by registered collection (which has at least
    # one live request per environment). Rows remain mutually independent.
    padded_inputs = (
        F.pad(inputs, (0, 0, 0, FORMAL_NUM_ENVS - row_count))
        if row_count < FORMAL_NUM_ENVS
        else inputs
    )

    def evaluate(layer: nn.Linear) -> torch.Tensor:
        output = (
            padded_inputs.unsqueeze(1) * layer.weight.unsqueeze(0)
        ).sum(dim=-1) + layer.bias
        return output[:row_count]

    return evaluate(event_head), evaluate(mark_head)

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
    forced_event: tuple[int, int, int, int, torch.Tensor] | None = None,
    forced_events: Mapping[tuple[int, int, int], tuple[int, torch.Tensor]] | None = None,
    row_rngs: list[Mapping[str, _AuditRowStream]] | None = None,
) -> EventTrajectory:
    if state.arm != arm.arm or set(state.rngs) != set(RNG_NAMES):
        raise ValueError("collector arm or owned-RNG key set mismatch")
    rng_trace: dict[str, list[dict[str, Any]]] = {
        name: [] for name in RNG_NAMES
    }
    request_evidence: list[dict[str, Any]] = []

    raw_event_trace: list[dict[str, Any]] = []
    if cursor is None:
        ids = tuple(int(v) for v in episode_ids) if episode_ids is not None else tuple(
            range(state.next_episode_id, state.next_episode_id + FORMAL_NUM_ENVS)
        )
        if not ids:
            raise ValueError("collection requires episodes")
        cursor = _new_cursor(
            state, ids, device, profile=profile, audit_trace=rng_trace
        )
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
    ledger_evidence = tuple(_ledger_audit_evidence(value) for value in cursor.ledgers)
    if row_rngs is not None and len(row_rngs) != env_count:
        raise ValueError("fork row RNG count must match the collection width")
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
            order_np = frontier_order(cursor.ledgers, active_np, time)
            order = torch.as_tensor(order_np, device=device)
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

            request_coordinates = [
                [int(env_index), int(key), int(request_kind)]
                for env_index, key, request_kind, _inp, _z_pre in requests
            ]
            request_evidence.append({
                "time": int(time),
                "environments": [
                    {
                        "env_index": int(env_index),
                        "episode_id": int(cursor.episode_ids[env_index]),
                        "frontier": [
                            {
                                "key": int(key),
                                "priority": float(
                                    cursor.ledgers[env_index]
                                    .direct_frontier_priorities[time, key]
                                ),
                                "q_before": (
                                    int(cursor.lifecycles[env_index][int(key)].q)
                                    if arm.arm != "OR" else None
                                ),
                            }
                            for key in order_np[env_index] if int(key) >= 0
                        ],
                    }
                    for env_index in range(env_count)
                ],
            })

            selected_kind_grid = torch.zeros_like(kind)
            request_q = np.empty(len(requests), dtype=np.int64)
            trace_payload_values: np.ndarray | None = None
            if requests:
                assert arm.event_head is not None and arm.mark_head is not None
                packed_inputs = torch.stack([value[3] for value in requests])
                packed_z_pre = torch.stack([value[4] for value in requests])
                # All collection modes and teacher replay deliberately share
                # this one row-local binary32 head evaluation.
                logits, mark_output = _row_stable_event_heads(
                    packed_inputs, arm.event_head, arm.mark_head
                )
                mu, sigma = _normal_parameters(mark_output)
                create_mask = torch.as_tensor(
                    [value[2] == CREATE for value in requests], dtype=torch.bool, device=device
                )
                if deterministic:
                    selected_cat = torch.argmax(logits, dim=-1)
                    u = mu
                else:
                    rng_trace["event"].append({
                        "stream": "event", "operation": "random",
                        "dtype": "float64", "shape": [len(requests)],
                        "coordinates": {
                            "time": int(time), "requests": request_coordinates,
                        },
                    })
                    event_values = (
                        state.rngs["event"].random(len(requests))
                        if row_rngs is None
                        else _audit_row_draw(row_rngs, requests, "event")
                    )
                    event_uniforms = torch.as_tensor(
                        event_values,
                        dtype=logits.dtype,
                        device=device,
                    )
                    selected_cat = torch.sum(
                        event_uniforms.unsqueeze(-1) > torch.cumsum(torch.softmax(logits, -1), -1),
                        dim=-1,
                    ).clamp(max=1)
                    rng_trace["mark"].append({
                        "stream": "mark", "operation": "standard_normal",
                        "dtype": "float64", "shape": [len(requests), MARK_DIM],
                        "coordinates": {
                            "time": int(time), "requests": request_coordinates,
                        },
                    })
                    mark_values = (
                        state.rngs["mark"].standard_normal(
                            (len(requests), MARK_DIM)
                        )
                        if row_rngs is None
                        else _audit_row_draw(
                            row_rngs, requests, "mark", width=MARK_DIM
                        )
                    )
                    mark_eps = torch.as_tensor(
                        mark_values,
                        dtype=mu.dtype,
                        device=device,
                    )
                    u = mu + sigma * mark_eps
                selected_kind = torch.where(create_mask, torch.full_like(selected_cat, CREATE), selected_cat + KEEP)
                active_forced: dict[tuple[int, int], tuple[int, torch.Tensor]] = {}
                if forced_event is not None and time == int(forced_event[0]):
                    active_forced[(int(forced_event[1]), int(forced_event[2]))] = (
                        int(forced_event[3]), forced_event[4]
                    )
                if forced_events is not None:
                    active_forced.update({
                        (int(env), int(key)): (int(kind), new_z)
                        for (forced_time, env, key), (kind, new_z)
                        in forced_events.items() if int(forced_time) == time
                    })
                forced_indices: list[tuple[int, torch.Tensor]] = []
                if active_forced:
                    selected_cat = selected_cat.clone()
                    selected_kind = selected_kind.clone()
                for (forced_env, forced_key), (forced_kind, forced_value) in active_forced.items():
                    matching = [
                        index for index, value in enumerate(requests)
                        if value[0] == forced_env and value[1] == forced_key
                    ]
                    if len(matching) != 1:
                        raise RuntimeError("forced event coordinate is not one request")
                    forced_index = matching[0]
                    if forced_kind not in (KEEP, RENEW) or bool(create_mask[forced_index]):
                        raise ValueError("forced event must be a non-CREATE KEEP/RENEW")
                    selected_cat[forced_index] = forced_kind - KEEP
                    selected_kind[forced_index] = forced_kind
                    forced_indices.append((forced_index, forced_value.to(device).detach()))
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
                if forced_indices:
                    packed_new_z = packed_new_z.clone()
                    for forced_index, forced_value in forced_indices:
                        packed_new_z[forced_index] = forced_value
                joint_logp = categorical_logp + component_logp.sum(-1)
                env_indices = torch.as_tensor([v[0] for v in requests], dtype=torch.long, device=device)
                key_indices = torch.as_tensor([v[1] for v in requests], dtype=torch.long, device=device)
                kind[env_indices, key_indices] = selected_kind
                selected_kind_grid[env_indices, key_indices] = selected_kind
                event_actions[env_indices, key_indices] = torch.where(
                    derived_cat_mask, selected_cat, torch.full_like(selected_cat, -1)
                )
                event_inputs[env_indices, key_indices] = packed_inputs
                event_u[env_indices, key_indices] = torch.where(
                    derived_mark_mask.unsqueeze(-1), u.detach(), torch.zeros_like(u)
                )
                candidate_u[env_indices, key_indices] = u.detach()
                candidate_z[env_indices, key_indices] = candidate_tanh_u
                # One packed transfer captures every raw mark field at this
                # physical row.  Individual trace records are then assembled
                # from host binary32 arrays before any environment step can
                # consume reward or terminal outcome information.
                trace_payload_values = torch.stack(
                    (packed_z_pre, u.detach(), candidate_tanh_u), dim=1
                ).cpu().numpy()
                event_z_pre[env_indices, key_indices] = packed_z_pre
                event_new_z[env_indices, key_indices] = packed_new_z
                cat_mask[env_indices, key_indices] = derived_cat_mask
                mark_mask[env_indices, key_indices] = derived_mark_mask
                old_cat[env_indices, key_indices] = categorical_logp
                old_mark[env_indices, key_indices] = component_logp
                old_joint[env_indices, key_indices] = joint_logp
                primitive_z[env_indices, key_indices] = packed_new_z
                rng_trace["opportunity"].append({
                    "stream": "opportunity", "operation": "choice_opportunity",
                    "dtype": "int64", "shape": [len(requests)],
                    "coordinates": {
                        "time": int(time), "requests": request_coordinates,
                    },
                })
                request_q[:] = (
                    state.rngs["opportunity"].choice(
                        OPPORTUNITY_SUPPORT, size=len(requests)
                    )
                    if row_rngs is None
                    else _audit_row_draw(
                        row_rngs, requests, "opportunity", dtype=np.int64
                    )
                )

            if deterministic:
                primitive_kwargs: dict[str, Any] = {"deterministic": True}
            else:
                rng_trace["primitive"].append({
                    "stream": "primitive", "operation": "random",
                    "dtype": "float32",
                    "shape": [env_count, MAX_LIFECYCLES],
                    "coordinates": {
                        "time": int(time),
                        "episode_ids": [int(value) for value in cursor.episode_ids],
                        "frontier_orders": [
                            [int(value) for value in row if int(value) >= 0]
                            for row in order_np
                        ],
                    },
                })
                primitive_values = (
                    state.rngs["primitive"].random(
                        (env_count, MAX_LIFECYCLES), dtype=np.float32
                    )
                    if row_rngs is None
                    else np.stack([
                        value["primitive"].random(
                            MAX_LIFECYCLES, dtype=np.float32
                        )
                        for value in row_rngs
                    ])
                )
                uniforms = torch.as_tensor(
                    primitive_values,
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
                if selected_kind in (KEEP, RENEW):
                    if trace_payload_values is None:
                        raise RuntimeError("eligible event lacks raw trace payload")
                    origin = {
                        "domain": "HMASD_RAW_EVENT_TRACE_V1",
                        "arm": arm.arm,
                        "profile": profile,
                        "replicate": int(state.replicate),
                        "episode_id": int(cursor.episode_ids[env_index]),
                        "ledger_digest": ledger_evidence[env_index]["ledger_digest"],
                    }
                    trace_row = {
                        "coordinate": {
                            "time": int(time),
                            "env_index": int(env_index),
                            "key": int(key),
                            "membership_epoch": int(life.membership_epoch),
                            "segment_id": int(life.segment_id),
                        },
                        "natural_kind": int(selected_kind),
                        "installed_z": _float32_payload(
                            trace_payload_values[index, 0]
                        ),
                        "candidate_u": _float32_payload(
                            trace_payload_values[index, 1]
                        ),
                        "candidate_z": _float32_payload(
                            trace_payload_values[index, 2]
                        ),
                        "origin_binding": origin,
                    }
                    trace_row["origin_binding"] = origin | {
                        "binding_digest": _raw_event_trace_digest(trace_row)
                    }
                    raw_event_trace.append(trace_row)
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
        raw_event_trace=tuple(raw_event_trace),
        outcomes=outcomes,
        segments=tuple(tuple(value) for value in cursor.segments),
        ledger_ids=cursor.episode_ids,
        cutoff=not finished,
        bootstrap_values=bootstrap,
        rng_audit={
            "streams": rng_trace,
            "request_evidence": request_evidence,
            "ledgers": list(ledger_evidence),
        },
        cursor=next_cursor,
    )
