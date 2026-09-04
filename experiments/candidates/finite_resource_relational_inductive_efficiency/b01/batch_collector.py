"""Production-width B01 RSCF collection over native and Torch batch seams.

This module collects one immutable-model arm/update.  It does not construct a
production seed packet, update an optimizer, publish a result, or select a
scientific branch.  The only Python loops over episodes prepare POD inputs and
assemble stable output order; every environment transition and every policy
forward crosses a multi-lane batch boundary.
"""

from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..arms import initialize_paired_arms
from ..native.native_abi import STATE_SIZE
from ..orchestration import OriginCoordinate
from ..policy import LEGAL_ACTION_INDICES, FRRIEActorCritic, require_torch
from ..rng import AddressedRNG
from ..tapes import EpisodeTape, generate_episode_tape, generate_training_origin_schedule
from ..training import RSCFEpisode, make_optimizer
from .constants import (
    HORIZON, LEARNED_ARMS, MIN_AVAILABLE_BYTES, ROOT_LABELS, TEST_SEED_LABELS,
)
from .contract import B01ContractError, validate_manifest, validate_resource_receipt
from .contract import canonical_json_bytes, named_compute_profile
from .native_batch import B01NativeBatchEnvironment, BatchStep, BatchWorkLedger
from .trainer import B01ArmBatch, capture_exogenous_episode


@dataclass(frozen=True, slots=True)
class BatchCollectionAudit:
    schema: str
    update: int
    factual_episodes: int
    native_width: int
    factual_slots: int
    factual_suffix_audit_slots: int
    nonfactual_suffix_slots: int
    total_environment_slots: int
    factual_suffixes_audited: int
    alternative_suffixes_executed: int
    factual_trace_direct_equal: bool
    model_bytes_unchanged: bool
    torch_actor_batch_calls: int
    torch_critic_batch_calls: int
    maximum_actor_lanes: int
    shared_model_worker_count: int


@dataclass(frozen=True, slots=True)
class CollectedUpdate:
    batch: B01ArmBatch
    audit: BatchCollectionAudit


@dataclass(slots=True)
class _TraceRow:
    observations: np.ndarray
    roles: np.ndarray
    masks: np.ndarray
    incoming_hidden: Any
    postdecision_hidden: Any
    probabilities: Any
    actions: Any
    pre_snapshot: bytes
    post_snapshot: bytes
    step: BatchStep
    step_lane: int


@dataclass(slots=True)
class _Origin:
    episode_lane: int
    role: int
    slot: int
    entity: int
    snapshot: bytes
    incoming_hidden: Any
    postdecision_hidden: Any
    actions: Any
    selected_probabilities: Any


@dataclass(slots=True)
class _FactualRoster:
    roster: int
    positions: tuple[int, ...]
    tapes: tuple[EpisodeTape, ...]
    origins: tuple[tuple[OriginCoordinate, ...], ...]
    observations: np.ndarray
    roles: np.ndarray
    masks: np.ndarray
    probability_graphs: tuple[Any, ...]
    origins_by_lane: tuple[dict[int, _Origin], ...]
    traces: tuple[tuple[_TraceRow, ...], ...]
    terminal_returns: tuple[float, ...]
    ledger: BatchWorkLedger
    actor_batch_calls: int


def _state_lane(snapshot: bytes, lane: int) -> bytes:
    return snapshot[lane * STATE_SIZE:(lane + 1) * STATE_SIZE]


def _same_array(left: np.ndarray, right: np.ndarray) -> bool:
    return left.dtype == right.dtype and left.shape == right.shape and left.tobytes() == right.tobytes()


def _same_float32(left: float, right: float) -> bool:
    return np.float32(left).tobytes() == np.float32(right).tobytes()


def _same_step(observed: BatchStep, lane: int, expected: _TraceRow) -> bool:
    source = expected.step
    source_lane = expected.step_lane
    return (
        observed.terminals[lane] == source.terminals[source_lane]
        and _same_float32(observed.returns[lane], source.returns[source_lane])
        and observed.primitives[lane] == source.primitives[source_lane]
        and _same_array(
            observed.previous_success[lane], source.previous_success[source_lane],
        )
    )


def _expected_masks(roles: np.ndarray) -> np.ndarray:
    masks = np.zeros((*roles.shape, 6), dtype=np.bool_)
    for role, indices in enumerate(LEGAL_ACTION_INDICES):
        masks[roles == role, :][:, list(indices)] = True
    # Boolean advanced indexing above returns a copy.  Assign by action so the
    # direct array itself receives the exact role support.
    masks.fill(False)
    for action in range(6):
        masks[..., action] = np.isin(
            roles, [role for role, indices in enumerate(LEGAL_ACTION_INDICES) if action in indices],
        )
    return masks


def _validate_frame(frame: Any, *, roster: int, lanes: int, slot: int) -> None:
    if (
        frame.observations.dtype != np.float32
        or frame.observations.shape != (lanes, roster, 22)
        or frame.roles.dtype != np.int64
        or frame.roles.shape != (lanes, roster)
        or frame.legal_masks.dtype != np.bool_
        or frame.legal_masks.shape != (lanes, roster, 6)
        or frame.slots != (slot,) * lanes
        or frame.terminals != (False,) * lanes
        or not np.isfinite(frame.observations).all()
    ):
        raise B01ContractError("B01 native batch observation shape/slot contract differs")
    expected_roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
    if not np.array_equal(frame.roles, np.broadcast_to(expected_roles, (lanes, roster))):
        raise B01ContractError("B01 native batch roles differ from fixed thirds")
    if not np.array_equal(frame.legal_masks, _expected_masks(frame.roles)):
        raise B01ContractError("B01 native batch masks differ from fixed role support")


def _normalize_origins(
    origins: Sequence[Sequence[OriginCoordinate | Sequence[int]]],
    tapes: Sequence[EpisodeTape],
) -> tuple[tuple[OriginCoordinate, ...], ...]:
    if len(origins) != 64:
        raise B01ContractError("B01 update requires origins for exactly 64 positions")
    result = []
    for position, (rows, tape) in enumerate(zip(origins, tapes)):
        converted = tuple(
            row if isinstance(row, OriginCoordinate) else OriginCoordinate(*map(int, row))
            for row in rows
        )
        if (
            len(converted) != 3
            or tuple(row.role for row in converted) != (0, 1, 2)
            or any(
                not 0 <= row.slot < HORIZON or not 0 <= row.entity < tape.roster
                or row.entity // (tape.roster // 3) != row.role
                for row in converted
            )
        ):
            raise B01ContractError(f"B01 origin coordinates differ at position {position}")
        result.append(converted)
    return tuple(result)


def _validate_tapes(
    tapes: Sequence[EpisodeTape], *, update: int,
    allowed_seed_labels: Sequence[str] = ROOT_LABELS,
) -> tuple[EpisodeTape, ...]:
    if len(tapes) != 64 or type(update) is not int or not 1 <= update <= 512:
        raise B01ContractError("B01 collector requires one complete update and 64 tapes")
    values = tuple(tapes)
    seed_labels = set()
    for position, tape in enumerate(values):
        roster = 9 if position % 2 == 0 else 15
        if (
            type(tape) is not EpisodeTape or tape.purpose != "TRAIN"
            or tape.roster != roster or tape.update != update
            or tape.episode != position // 2
            or tape.seed_block not in tuple(allowed_seed_labels)
        ):
            raise B01ContractError(f"B01 TRAIN tape differs at position {position}")
        seed_labels.add(tape.seed_block)
    if len(seed_labels) != 1:
        raise B01ContractError("B01 update mixes seed labels")
    return values


def _torch_frame(frame: Any) -> tuple[Any, Any]:
    import torch

    return (
        torch.from_numpy(np.ascontiguousarray(frame.observations)),
        torch.from_numpy(np.ascontiguousarray(frame.roles)),
    )


def _collect_factual_roster(
    *, model: FRRIEActorCritic, adapter: object, roster: int,
    positions: tuple[int, ...], tapes: tuple[EpisodeTape, ...],
    origins: tuple[tuple[OriginCoordinate, ...], ...],
) -> _FactualRoster:
    import torch

    lanes = len(tapes)
    if lanes != 32:
        raise B01ContractError("B01 production collector requires native width 32 per roster")
    environment = B01NativeBatchEnvironment(adapter, roster=roster, lanes=lanes)
    environment.reset(tapes)
    hidden = torch.zeros((lanes, roster, 64), dtype=torch.float32)
    observation_rows: list[np.ndarray] = []
    role_rows: list[np.ndarray] = []
    mask_rows: list[np.ndarray] = []
    probability_graphs: list[Any] = []
    traces: list[list[_TraceRow]] = [[] for _ in range(lanes)]
    origin_maps: list[dict[int, _Origin]] = [dict() for _ in range(lanes)]
    terminal_returns: tuple[float, ...] | None = None
    actor_calls = 0
    for slot in range(HORIZON):
        frame = environment.observe()
        _validate_frame(frame, roster=roster, lanes=lanes, slot=slot)
        observations, roles = _torch_frame(frame)
        incoming = hidden
        pre_snapshot = environment.snapshot()
        actor = model.actor_step_batch(observations, roles, incoming)
        actor_calls += 1
        uniforms = torch.stack([
            torch.from_numpy(np.array(tape.action_uniform[slot], copy=True, order="C"))
            for tape in tapes
        ])
        actions = model.actions_from_uniforms_batch(actor.probabilities, uniforms)
        for lane, lane_origins in enumerate(origins):
            for coordinate in lane_origins:
                if coordinate.slot == slot:
                    origin_maps[lane][coordinate.role] = _Origin(
                        episode_lane=lane, role=coordinate.role, slot=slot,
                        entity=coordinate.entity, snapshot=_state_lane(pre_snapshot, lane),
                        incoming_hidden=incoming[lane].detach().clone(),
                        postdecision_hidden=actor.hidden[lane].detach().clone(),
                        actions=actions[lane].detach().clone(),
                        selected_probabilities=actor.probabilities[lane, coordinate.entity],
                    )
        step = environment.step(actions.detach().numpy())
        post_snapshot = environment.snapshot()
        for lane in range(lanes):
            traces[lane].append(_TraceRow(
                observations=frame.observations[lane].copy(),
                roles=frame.roles[lane].copy(), masks=frame.legal_masks[lane].copy(),
                incoming_hidden=incoming[lane].detach().clone(),
                postdecision_hidden=actor.hidden[lane].detach().clone(),
                probabilities=actor.probabilities[lane].detach().clone(),
                actions=actions[lane].detach().clone(),
                pre_snapshot=_state_lane(pre_snapshot, lane),
                post_snapshot=_state_lane(post_snapshot, lane),
                step=step, step_lane=lane,
            ))
        if step.terminals != ((slot == HORIZON - 1),) * lanes:
            raise B01ContractError("B01 factual batch terminal horizon differs")
        observation_rows.append(frame.observations.copy())
        role_rows.append(frame.roles.copy())
        mask_rows.append(frame.legal_masks.copy())
        probability_graphs.append(actor.probabilities)
        hidden = actor.hidden
        if slot == HORIZON - 1:
            terminal_returns = step.returns
    if terminal_returns is None or any(set(row) != {0, 1, 2} for row in origin_maps):
        raise B01ContractError("B01 factual batch omitted terminal or origin facts")
    return _FactualRoster(
        roster=roster, positions=positions, tapes=tapes, origins=origins,
        observations=np.stack(observation_rows), roles=np.stack(role_rows),
        masks=np.stack(mask_rows), probability_graphs=tuple(probability_graphs),
        origins_by_lane=tuple(origin_maps), traces=tuple(tuple(row) for row in traces),
        terminal_returns=terminal_returns, ledger=environment.work_ledger(),
        actor_batch_calls=actor_calls,
    )


def _chunks(values: Sequence[Any], width: int = 32):
    for start in range(0, len(values), width):
        yield values[start:start + width]


def _audit_factual_suffixes(
    *, model: FRRIEActorCritic, adapter: object, factual: _FactualRoster,
    require_intermediate_bit_equality: bool = True,
) -> tuple[tuple[BatchWorkLedger, ...], int, int]:
    import torch

    tasks = [origin for rows in factual.origins_by_lane for origin in rows.values()]
    ledgers: list[BatchWorkLedger] = []
    actor_calls = 0
    for slot in range(HORIZON):
        selected = [task for task in tasks if task.slot == slot]
        for chunk0 in _chunks(selected):
            chunk = tuple(chunk0)
            environment = B01NativeBatchEnvironment(
                adapter, roster=factual.roster, lanes=len(chunk),
            )
            environment.restore(b"".join(task.snapshot for task in chunk))
            actions = np.stack([task.actions.numpy() for task in chunk])
            step = environment.step(actions)
            snapshot = environment.snapshot()
            for lane, task in enumerate(chunk):
                expected = factual.traces[task.episode_lane][slot]
                if not _same_step(step, lane, expected) or _state_lane(snapshot, lane) != expected.post_snapshot:
                    raise B01ContractError("B01 factual suffix origin transition differs")
            hidden = torch.stack([task.postdecision_hidden for task in chunk])
            for future in range(slot + 1, HORIZON):
                frame = environment.observe()
                _validate_frame(
                    frame, roster=factual.roster, lanes=len(chunk), slot=future,
                )
                for lane, task in enumerate(chunk):
                    expected = factual.traces[task.episode_lane][future]
                    if (
                        _state_lane(environment.snapshot(), lane) != expected.pre_snapshot
                        or not _same_array(frame.observations[lane], expected.observations)
                        or not _same_array(frame.roles[lane], expected.roles)
                        or not _same_array(frame.legal_masks[lane], expected.masks)
                        or (require_intermediate_bit_equality
                            and not torch.equal(hidden[lane], expected.incoming_hidden))
                    ):
                        raise B01ContractError("B01 factual suffix predecision trace differs")
                observations, roles = _torch_frame(frame)
                actor = model.actor_step_batch(observations, roles, hidden)
                actor_calls += 1
                uniforms = torch.stack([
                    torch.from_numpy(np.array(
                        factual.tapes[task.episode_lane].action_uniform[future],
                        copy=True, order="C",
                    )) for task in chunk
                ])
                actions = model.actions_from_uniforms_batch(actor.probabilities, uniforms)
                for lane, task in enumerate(chunk):
                    expected = factual.traces[task.episode_lane][future]
                    if (
                        (require_intermediate_bit_equality and (
                            not torch.equal(actor.hidden[lane], expected.postdecision_hidden)
                            or not torch.equal(actor.probabilities[lane], expected.probabilities)
                        ))
                        or not torch.equal(actions[lane], expected.actions)
                    ):
                        raise B01ContractError("B01 factual suffix actor trace differs")
                step = environment.step(actions.numpy())
                snapshot = environment.snapshot()
                for lane, task in enumerate(chunk):
                    expected = factual.traces[task.episode_lane][future]
                    if not _same_step(step, lane, expected) or _state_lane(
                        snapshot, lane,
                    ) != expected.post_snapshot:
                        raise B01ContractError("B01 factual suffix postdecision trace differs")
                hidden = actor.hidden
            ledgers.append(environment.work_ledger())
    slots = sum(item.environment_slots for item in ledgers)
    if len(tasks) != 96 or slots != 624:
        raise B01ContractError("B01 factual suffix audit inventory differs")
    return tuple(ledgers), slots, actor_calls


def _collect_nonfactual_suffixes(
    *, model: FRRIEActorCritic, adapter: object, factual: _FactualRoster,
) -> tuple[dict[tuple[int, int, int], float], tuple[BatchWorkLedger, ...], int, int]:
    import torch

    tasks: list[tuple[_Origin, int]] = []
    for rows in factual.origins_by_lane:
        for role, origin in rows.items():
            factual_action = int(origin.actions[origin.entity].item())
            for action in LEGAL_ACTION_INDICES[role]:
                if action != factual_action:
                    tasks.append((origin, action))
    values: dict[tuple[int, int, int], float] = {}
    ledgers: list[BatchWorkLedger] = []
    actor_calls = 0
    for slot in range(HORIZON):
        selected = [task for task in tasks if task[0].slot == slot]
        for chunk0 in _chunks(selected):
            chunk = tuple(chunk0)
            environment = B01NativeBatchEnvironment(
                adapter, roster=factual.roster, lanes=len(chunk),
            )
            environment.restore(b"".join(origin.snapshot for origin, _ in chunk))
            actions = np.stack([origin.actions.numpy() for origin, _ in chunk])
            for lane, (origin, action) in enumerate(chunk):
                actions[lane, origin.entity] = action
            step = environment.step(actions)
            hidden = torch.stack([origin.postdecision_hidden for origin, _ in chunk])
            for future in range(slot + 1, HORIZON):
                frame = environment.observe()
                _validate_frame(
                    frame, roster=factual.roster, lanes=len(chunk), slot=future,
                )
                observations, roles = _torch_frame(frame)
                actor = model.actor_step_batch(observations, roles, hidden)
                actor_calls += 1
                uniforms = torch.stack([
                    torch.from_numpy(np.array(
                        factual.tapes[origin.episode_lane].action_uniform[future],
                        copy=True, order="C",
                    )) for origin, _ in chunk
                ])
                actions = model.actions_from_uniforms_batch(actor.probabilities, uniforms)
                step = environment.step(actions.numpy())
                hidden = actor.hidden
            if step.terminals != (True,) * len(chunk):
                raise B01ContractError("B01 nonfactual suffix did not reach terminal")
            for lane, (origin, action) in enumerate(chunk):
                values[(origin.episode_lane, origin.role, action)] = step.returns[lane]
            ledgers.append(environment.work_ledger())
    slots = sum(item.environment_slots for item in ledgers)
    if len(tasks) != 224 or len(values) != 224 or slots != 1_456:
        raise B01ContractError("B01 seven-alternative suffix inventory differs")
    return values, tuple(ledgers), slots, actor_calls


def _collect_b01_arm_update(
    *, model: FRRIEActorCritic, adapter: object, tapes: Sequence[EpisodeTape],
    origins: Sequence[Sequence[OriginCoordinate | Sequence[int]]], update: int,
    allowed_seed_labels: Sequence[str],
) -> CollectedUpdate:
    """Collect exact 64-episode RSCF tensors for one arm/update.

    The shared model is intentionally used by one calling thread.  Width-32
    native lanes and batched Torch inference provide production batching;
    worker parallelism is reserved for independent environment-only tasks.
    """

    require_torch()
    import torch
    if torch.get_num_threads() != 1:
        raise B01ContractError("B01 production batch collector requires one Torch CPU thread")
    if not isinstance(model, FRRIEActorCritic):
        raise B01ContractError("B01 collector requires the production actor/critic")
    tapes0 = _validate_tapes(
        tapes, update=update, allowed_seed_labels=allowed_seed_labels,
    )
    origins0 = _normalize_origins(origins, tapes0)
    initial_model = model.parameter_bytes()
    rosters: dict[int, _FactualRoster] = {}
    all_ledgers: list[BatchWorkLedger] = []
    audit_slots = alternative_slots = actor_calls = 0
    alternative_values: dict[int, dict[tuple[int, int, int], float]] = {}
    for roster, positions in (
        (9, tuple(range(0, 64, 2))), (15, tuple(range(1, 64, 2))),
    ):
        factual = _collect_factual_roster(
            model=model, adapter=adapter, roster=roster, positions=positions,
            tapes=tuple(tapes0[position] for position in positions),
            origins=tuple(origins0[position] for position in positions),
        )
        rosters[roster] = factual
        all_ledgers.append(factual.ledger)
        actor_calls += factual.actor_batch_calls
        with __import__("torch").no_grad():
            audit_ledgers, roster_audit_slots, audit_actor_calls = _audit_factual_suffixes(
                model=model, adapter=adapter, factual=factual,
            )
            values, alternative_ledgers, roster_alternative_slots, alternative_actor_calls = (
                _collect_nonfactual_suffixes(model=model, adapter=adapter, factual=factual)
            )
        all_ledgers.extend(audit_ledgers)
        all_ledgers.extend(alternative_ledgers)
        audit_slots += roster_audit_slots
        alternative_slots += roster_alternative_slots
        actor_calls += audit_actor_calls + alternative_actor_calls
        alternative_values[roster] = values

    critic_graphs: dict[int, Any] = {}
    for roster, factual in rosters.items():
        observation_tensor = torch.from_numpy(
            np.ascontiguousarray(factual.observations.transpose(1, 0, 2, 3)),
        )
        roles_tensor = torch.from_numpy(np.ascontiguousarray(factual.roles[0]))
        critic_graphs[roster] = model.critic_values_batch(observation_tensor, roles_tensor)

    episodes: list[RSCFEpisode] = []
    receipts = []
    for position, (tape, lane_origins) in enumerate(zip(tapes0, origins0)):
        roster = tape.roster
        factual = rosters[roster]
        lane = position // 2
        selected = torch.stack([
            factual.origins_by_lane[lane][role].selected_probabilities for role in range(3)
        ])
        factual_actions = torch.stack([
            factual.origins_by_lane[lane][role].actions[
                factual.origins_by_lane[lane][role].entity
            ] for role in range(3)
        ]).to(torch.int64)
        legal = torch.zeros((3, 6), dtype=torch.bool)
        q_targets = torch.full((3, 6), torch.nan, dtype=torch.float32)
        for role in range(3):
            legal[role, list(LEGAL_ACTION_INDICES[role])] = True
            factual_action = int(factual_actions[role].item())
            for action in LEGAL_ACTION_INDICES[role]:
                value = (
                    factual.terminal_returns[lane]
                    if action == factual_action
                    else alternative_values[roster][(lane, role, action)]
                )
                q_targets[role, action] = float(value)
        all_probabilities = torch.stack([
            row[lane] for row in factual.probability_graphs
        ])
        terminal_return = torch.tensor(
            factual.terminal_returns[lane], dtype=torch.float32,
        )
        episodes.append(RSCFEpisode(
            roster_size=roster, selected_probabilities=selected,
            q_targets=q_targets.detach(), legal_masks=legal,
            factual_actions=factual_actions, all_probabilities=all_probabilities,
            critic_values=critic_graphs[roster][lane],
            terminal_return=terminal_return.detach(),
        ))
        direct_observations = np.ascontiguousarray(factual.observations[:, lane])
        direct_roles = np.ascontiguousarray(factual.roles[0, lane])
        direct_masks = np.ascontiguousarray(factual.masks[:, lane])
        receipts.append(capture_exogenous_episode(
            update=update, position=position, roster=roster, tape=tape,
            observations=direct_observations, relations=direct_roles, masks=direct_masks,
            origin_coordinates=tuple(
                (row.role, row.slot, row.entity) for row in lane_origins
            ),
        ))
    if model.parameter_bytes() != initial_model:
        raise B01ContractError("B01 collection mutated immutable model bytes")
    batch = B01ArmBatch(tuple(episodes), tuple(receipts), tuple(all_ledgers)).validate(
        update=update,
    )
    factual_slots = sum(rosters[roster].ledger.environment_slots for roster in (9, 15))
    total_slots = sum(item.environment_slots for item in all_ledgers)
    audit = BatchCollectionAudit(
        schema="FRRIE_B01_BATCH_COLLECTION_AUDIT_V1", update=update,
        factual_episodes=64, native_width=32, factual_slots=factual_slots,
        factual_suffix_audit_slots=audit_slots,
        nonfactual_suffix_slots=alternative_slots,
        total_environment_slots=total_slots, factual_suffixes_audited=192,
        alternative_suffixes_executed=448, factual_trace_direct_equal=True,
        model_bytes_unchanged=True, torch_actor_batch_calls=actor_calls,
        torch_critic_batch_calls=2, maximum_actor_lanes=32,
        shared_model_worker_count=1,
    )
    if (factual_slots, audit_slots, alternative_slots, total_slots) != (
        768, 1_248, 2_912, 4_928,
    ):
        raise B01ContractError("B01 direct one-update work partition differs")
    return CollectedUpdate(batch=batch, audit=audit)


def collect_b01_arm_update(
    *, model: FRRIEActorCritic, adapter: object, tapes: Sequence[EpisodeTape],
    origins: Sequence[Sequence[OriginCoordinate | Sequence[int]]], update: int,
    manifest: Mapping[str, Any],
) -> CollectedUpdate:
    """Formal collector bound only to this validated manifest's phase labels."""

    validated = validate_manifest(manifest)
    labels = tuple(validated["execution_labels"])
    if not labels or any(label not in ROOT_LABELS for label in labels):
        raise B01ContractError("formal manifest execution labels are not production labels")
    return _collect_b01_arm_update(
        model=model, adapter=adapter, tapes=tapes, origins=origins, update=update,
        allowed_seed_labels=labels,
    )


def _collect_b01_test_arm_update(
    *, model: FRRIEActorCritic, adapter: object, tapes: Sequence[EpisodeTape],
    origins: Sequence[Sequence[OriginCoordinate | Sequence[int]]], update: int,
) -> CollectedUpdate:
    """Private non-result path bound only to the canonical TEST namespace."""

    return _collect_b01_arm_update(
        model=model, adapter=adapter, tapes=tapes, origins=origins, update=update,
        allowed_seed_labels=TEST_SEED_LABELS,
    )


def actor_scalar_batch_equivalence(
    *, model: FRRIEActorCritic, observations: Any, roles: Any,
    hidden: Any, uniforms: Any,
) -> dict[str, Any]:
    """Direct TEST-only scalar/batch actor and critic bit comparison."""

    import torch

    if torch.get_num_threads() != 1:
        raise B01ContractError("scalar/batch bit equivalence requires one Torch CPU thread")

    with torch.no_grad():
        batched = model.actor_step_batch(observations, roles, hidden)
        batch_actions = model.actions_from_uniforms_batch(batched.probabilities, uniforms)
        scalar = [
            model.actor_step(observations[lane], roles[lane], hidden[lane])
            for lane in range(observations.shape[0])
        ]
        scalar_probabilities = torch.stack([row.probabilities for row in scalar])
        scalar_hidden = torch.stack([row.hidden for row in scalar])
        scalar_actions = torch.stack([
            model.actions_from_uniforms(row.probabilities, uniforms[lane])
            for lane, row in enumerate(scalar)
        ])
        trace = observations[:, None, :, :].expand(-1, HORIZON, -1, -1).contiguous()
        batch_critic = model.critic_values_batch(trace, roles)
        scalar_critic = torch.stack([
            model.critic_values(trace[lane], roles[lane])
            for lane in range(trace.shape[0])
        ])
    fields = {
        "probabilities": torch.equal(batched.probabilities, scalar_probabilities),
        "hidden": torch.equal(batched.hidden, scalar_hidden),
        "actions": torch.equal(batch_actions, scalar_actions),
        "critic": torch.equal(batch_critic, scalar_critic),
    }
    return {
        "schema": "FRRIE_B01_ACTOR_SCALAR_BATCH_EQUIVALENCE_V1",
        "lanes": int(observations.shape[0]), "direct_bit_equal": all(fields.values()),
        "fields": fields,
    }


def make_test_update_inputs(
    root: bytes, *, seed_label: str, update: int,
) -> tuple[tuple[EpisodeTape, ...], tuple[tuple[OriginCoordinate, ...], ...]]:
    """Materialize deterministic non-result inputs; never an OS-CSPRNG packet."""

    if type(root) is not bytes or len(root) != 32:
        raise B01ContractError("TEST input root must contain exactly 32 bytes")
    if seed_label not in TEST_SEED_LABELS:
        raise B01ContractError("TEST input label must remain in the TEST-only namespace")
    rng = AddressedRNG(root)
    schedules = {
        roster: generate_training_origin_schedule(
            rng, seed_block=seed_label, roster=roster, update=update, purpose="TRAIN",
        ) for roster in (9, 15)
    }
    by_roster_episode = {
        roster: {
            episode: tuple(
                OriginCoordinate(
                    role=item.public_role_index, slot=item.selected_slot,
                    entity=item.simulator_index,
                )
                for item in sorted(
                    (row for row in schedule.selections if row.episode == episode),
                    key=lambda row: row.public_role_index,
                )
            )
            for episode in range(32)
        }
        for roster, schedule in schedules.items()
    }
    tapes = tuple(
        generate_episode_tape(
            AddressedRNG(root), seed_block=seed_label, purpose="TRAIN",
            roster=(9 if position % 2 == 0 else 15), update=update,
            episode=position // 2,
        ) for position in range(64)
    )
    origins = tuple(
        by_roster_episode[tape.roster][tape.episode] for tape in tapes
    )
    return tapes, origins


def _read_fresh_receipt(path: Path, *, maximum_age_seconds: float = 300.0) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        receipt = validate_resource_receipt(json.loads(raw.decode("utf-8")))
        age = time.time() - path.stat().st_mtime
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise B01ContractError("TEST assessment resource receipt is unreadable") from error
    if age < -5.0 or age > maximum_age_seconds:
        raise B01ContractError("TEST assessment resource receipt is not fresh")
    return receipt


def assess_one_update_test(
    *, receipt_path: str | Path, root: bytes, seed_label: str,
    adapter_factory: Callable[[], Any], update: int = 1,
) -> dict[str, Any]:
    """Execute a non-result one-update collection after direct memory admission.

    Tape/origin construction is result-blind and precedes admission.  Receipt
    validation is immediately followed by native adapter and paired
    model/optimizer construction; no caller-created runtime object is accepted.
    """

    tapes, origins = make_test_update_inputs(
        root, seed_label=seed_label, update=update,
    )
    path = Path(receipt_path).resolve(strict=True)
    receipt = _read_fresh_receipt(path)
    if min(
        receipt["available_physical_bytes"], receipt["effective_available_bytes"],
    ) < MIN_AVAILABLE_BYTES:
        raise B01ContractError("TEST assessment memory admission is below 4 GiB")
    started = time.perf_counter()
    import torch
    torch.set_num_threads(1)
    adapter = adapter_factory()
    phy, edge = initialize_paired_arms(AddressedRNG(root), seed_label)
    models = {
        "PHY_TRUST": FRRIEActorCritic(phy), "EDGE_FLEX": FRRIEActorCritic(edge),
    }
    optimizers = {arm: make_optimizer(model) for arm, model in models.items()}
    # Optimizers are constructed to exercise the real runtime seam but are not
    # stepped: this assessor measures collection only and emits no result.
    collections = {
        arm: _collect_b01_test_arm_update(
            model=model, adapter=adapter, tapes=tapes, origins=origins, update=update,
        ) for arm, model in models.items()
    }
    elapsed = time.perf_counter() - started
    left, right = (collections[arm] for arm in LEARNED_ARMS)
    exogenous_equal = all(
        (
            a.tape_bytes, a.tape_coordinate, a.relations_bytes, a.masks_bytes,
            a.origin_addresses,
        ) == (
            b.tape_bytes, b.tape_coordinate, b.relations_bytes, b.masks_bytes,
            b.origin_addresses,
        )
        for a, b in zip(left.batch.exogenous_receipts, right.batch.exogenous_receipts)
    )
    del optimizers
    return {
        "schema": "FRRIE_B01_ONE_UPDATE_TEST_ASSESSMENT_V1",
        "test_only": True, "result_bearing": False, "scientific_values": None,
        "seed_packet_created": False, "production_roots_created": False,
        "optimizer_steps": 0, "update": update,
        "resource_receipt_path": str(path), "resource_receipt": receipt,
        "arm_audits": {arm: asdict(row.audit) for arm, row in collections.items()},
        "paired_exogenous_direct_equal": exogenous_equal,
        "wall_seconds": elapsed,
        "scientific_work_slots": sum(
            row.audit.total_environment_slots for row in collections.values()
        ),
        "slots_per_second": 9_856 / elapsed,
        "shared_model_worker_count": 1,
        "performance_disposition": "REPAIR_REQUIRED",
        "performance_blocker": "NAMED_WORKERS4_NOT_EFFECTIVE_IN_PRODUCTION_COLLECTOR",
        "complete": True,
    }


def run_actual_test_assessment(*, root: str | Path) -> dict[str, Any]:
    """Create-once retained actual native TEST assessment transaction."""

    from .. import native_adapter as native_adapter_module
    from .recon import _AReconProcessTreeMonitor

    root0 = Path(root).resolve(strict=False)
    staging = root0.with_name(root0.name + ".creating")
    incomplete = root0.with_name(root0.name + ".incomplete")
    if root0.exists() or staging.exists() or incomplete.exists():
        raise B01ContractError("B01 actual TEST assessment root is not fresh")
    staging.mkdir(parents=True)
    scratch = staging / "scratch"
    durable = staging / "durable"
    scratch.mkdir()
    durable.mkdir()
    artifact = native_adapter_module.package_native_artifact_path().resolve(strict=False)
    artifact_preexisted = artifact.exists()
    monitor = _AReconProcessTreeMonitor(
        scratch_root=scratch, durable_root=durable, interval_seconds=0.01,
    )
    compiler_facts: dict[str, Any] = {}
    telemetry: dict[str, Any] | None = None
    try:
        source = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=False, capture_output=True,
            text=True, timeout=10,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"], check=False, capture_output=True,
            text=True, timeout=10,
        )
        source_state = {
            "head": source.stdout.strip(), "head_command_returncode": source.returncode,
            "worktree_porcelain": status.stdout.splitlines(),
            "status_command_returncode": status.returncode,
        }
        monitor.start()
        monitor.set_stage("FRESH_MEMORY_ADMISSION")
        receipt_path = staging / "admit-memory.json"
        admitted = subprocess.run(
            [
                sys.executable,
                str(Path("scripts/hmasd_resource_preflight.py").resolve()),
                "admit-memory", "--out", str(receipt_path.resolve()),
            ],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if admitted.returncode != 0:
            raise B01ContractError(
                "fresh memory admission failed: " + (admitted.stderr or admitted.stdout)
            )

        def adapter_factory():
            monitor.set_stage("NATIVE_BUILD_LOAD")
            if sys.platform == "win32":
                vcvars = native_adapter_module._windows_vcvars64()
                compiler, _ = native_adapter_module._windows_build_environment(vcvars)
                compiler_path = native_adapter_module._validate_vcvars_compiler(vcvars, compiler)
                compiler_facts.update({
                    "vcvars_path": str(vcvars.resolve(strict=True)),
                    "compiler_path": str(compiler_path),
                    "compiler_in_vc_tools": True,
                })
            built = native_adapter_module.build_package_native_artifact()
            compiler_facts.update({
                "native_artifact_path": str(built.resolve(strict=True)),
                "native_artifact_byte_count": built.stat().st_size,
                "native_artifact_sha256": hashlib.sha256(built.read_bytes()).hexdigest(),
            })
            adapter = native_adapter_module.load_package_native_adapter(named_compute_profile())
            monitor.set_stage("ACTUAL_WIDTH32_ONE_UPDATE_TWO_ARMS")
            return adapter

        assessment = assess_one_update_test(
            receipt_path=receipt_path, root=b"\x42" * 32,
            seed_label=TEST_SEED_LABELS[0], adapter_factory=adapter_factory, update=1,
        )
        telemetry = monitor.stop()
        evidence = {
            "schema": "FRRIE_B01_ACTUAL_BATCH_ASSESSMENT_TRANSACTION_V1",
            "test_only": True, "result_bearing": False, "scientific_values": None,
            "argv": list(sys.argv), "source_state": source_state,
            "assessment": assessment, "compiler_and_dll": compiler_facts,
            "process_tree_telemetry": telemetry,
            "artifact_preexisted": artifact_preexisted,
            "artifact_cleanup_required_after_process_exit": (
                sys.platform == "win32" and not artifact_preexisted
            ),
            "terminal_status": "COMPLETE_TEST_ONLY_REPAIR_REQUIRED",
        }
        (staging / "assessment.json").write_bytes(canonical_json_bytes(evidence))
        os.rename(staging, root0)
        return evidence
    except BaseException as error:
        if telemetry is None:
            try:
                telemetry = monitor.stop()
            except BaseException:
                telemetry = None
        marker = {
            "schema": "FRRIE_B01_ACTUAL_BATCH_ASSESSMENT_INCOMPLETE_V1",
            "test_only": True, "result_bearing": False, "scientific_values": None,
            "error_type": type(error).__name__, "error": str(error),
            "compiler_and_dll": compiler_facts, "process_tree_telemetry": telemetry,
            "terminal_status": "INCOMPLETE_TECHNICAL_ARTIFACT",
        }
        try:
            (staging / "incomplete.json").write_bytes(canonical_json_bytes(marker))
            os.rename(staging, incomplete)
        except OSError:
            pass
        raise
    finally:
        if not artifact_preexisted and artifact.exists():
            try:
                artifact.unlink()
            except PermissionError:
                # Windows retains a loaded DLL until interpreter exit.  The
                # calling transaction owns exact-path post-exit cleanup.
                pass
        for suffix in (".obj", ".pdb", ".lib", ".exp"):
            sidecar = artifact.with_suffix(suffix)
            if not artifact_preexisted and sidecar.exists():
                try:
                    sidecar.unlink()
                except PermissionError:
                    pass


__all__ = [
    "BatchCollectionAudit", "CollectedUpdate", "collect_b01_arm_update",
    "actor_scalar_batch_equivalence",
    "make_test_update_inputs", "assess_one_update_test", "run_actual_test_assessment",
]
