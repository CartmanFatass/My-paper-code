"""Narrow R02 collector adapter preserving the B02 tape identity."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from ..b01.batch_collector import (
    BatchCollectionAudit,
    CollectedUpdate,
    _audit_factual_suffixes,
    _collect_factual_roster,
    _collect_nonfactual_suffixes,
    _normalize_origins,
    _validate_tapes,
)
from ..b01.contract import B01ContractError, canonical_json_bytes
from ..b01.trainer import B01ArmBatch, DirectExogenousEpisode, _EXOGENOUS_TOKEN
from ..orchestration import OriginCoordinate
from ..policy import FRRIEActorCritic, LEGAL_ACTION_INDICES, require_torch
from ..tapes import EpisodeTape
from ..training import RSCFEpisode


def _capture_exogenous_episode(
    *, update: int, position: int, roster: int, tape: EpisodeTape,
    observations: Any, roles: Any, masks: Any,
    origins: Sequence[OriginCoordinate], seed_label: str,
) -> DirectExogenousEpisode:
    expected_episode = position // 2
    if (
        type(tape) is not EpisodeTape
        or tape.seed_block != seed_label
        or tape.purpose != "TRAIN"
        or tape.roster != roster
        or tape.update != update
        or tape.episode != expected_episode
    ):
        raise B01ContractError("R02 direct TRAIN tape coordinate differs from batch position")
    fields = ("event_times", "detection_uniform", "uplink_uniform", "base_uniform", "action_uniform")
    tape_bytes = b"".join(getattr(tape, field).tobytes(order="C") for field in fields)
    observation_array = np.asarray(observations)
    role_array = np.asarray(roles)
    mask_array = np.asarray(masks)
    expected_roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
    expected_masks = np.zeros((12, roster, 6), dtype=np.bool_)
    for entity, role in enumerate(expected_roles):
        expected_masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
    if (
        observation_array.dtype != np.dtype(np.float32)
        or observation_array.shape != (12, roster, 22)
        or not observation_array.flags.c_contiguous
        or not np.isfinite(observation_array).all()
    ):
        raise B01ContractError("R02 direct observations differ")
    if (
        role_array.dtype != np.dtype(np.int64)
        or role_array.shape != (roster,)
        or not role_array.flags.c_contiguous
        or not np.array_equal(role_array, expected_roles)
    ):
        raise B01ContractError("R02 direct roles differ")
    if (
        mask_array.dtype != np.dtype(np.bool_)
        or mask_array.shape != (12, roster, 6)
        or not mask_array.flags.c_contiguous
        or not np.array_equal(mask_array, expected_masks)
    ):
        raise B01ContractError("R02 direct masks differ")
    coordinates = tuple((row.role, row.slot, row.entity) for row in origins)
    if (
        len(coordinates) != 3
        or tuple(value[0] for value in coordinates) != (0, 1, 2)
        or any(
            not 0 <= slot < 12
            or not 0 <= entity < roster
            or int(role_array[entity]) != role
            for role, slot, entity in coordinates
        )
    ):
        raise B01ContractError("R02 origin coordinates differ")
    origin_addresses = tuple(canonical_json_bytes({
        "schema": "FRRIE_B01_ORIGIN_ADDRESS_V1",
        "seed_block": tape.seed_block,
        "update": update,
        "batch_position": position,
        "roster": roster,
        "role": role,
        "slot": slot,
        "entity": entity,
    }) for role, slot, entity in coordinates)
    return DirectExogenousEpisode(
        _EXOGENOUS_TOKEN,
        update=update,
        position=position,
        roster=roster,
        tape_bytes=tape_bytes,
        tape_coordinate=(tape.seed_block, tape.purpose, tape.roster, tape.update, tape.episode),
        law_revisions=(
            "RIDGEGATE_2Z_NATIVE_STEP_ABI_V2",
            "OBSERVATION_22_V1",
            "K0_RELATION_FUNCTION_V1",
            "ROLE_LEGAL_MASK_FUNCTION_V1",
        ),
        observations_bytes=observation_array.tobytes(order="C"),
        observations_shape=tuple(observation_array.shape),
        observations_dtype=str(observation_array.dtype),
        relations_bytes=role_array.tobytes(order="C"),
        relations_shape=tuple(role_array.shape),
        relations_dtype=str(role_array.dtype),
        masks_bytes=mask_array.tobytes(order="C"),
        masks_shape=tuple(mask_array.shape),
        masks_dtype=str(mask_array.dtype),
        origin_coordinates=coordinates,
        origin_addresses=origin_addresses,
    )


def collect_r02_arm_update(
    *, model: FRRIEActorCritic, adapter: object, tapes: Sequence[EpisodeTape],
    origins: Sequence[Sequence[OriginCoordinate]], update: int, seed_label: str,
) -> CollectedUpdate:
    """Collect the existing real RSCF work without rewriting its B02 identity."""

    require_torch()
    import torch

    if torch.get_num_threads() != 1 or not isinstance(model, FRRIEActorCritic):
        raise B01ContractError("R02 collector requires one-thread production actor/critic")
    tapes0 = _validate_tapes(tapes, update=update, allowed_seed_labels=(seed_label,))
    origins0 = _normalize_origins(origins, tapes0)
    initial_model = model.parameter_bytes()
    rosters = {}
    all_ledgers = []
    audit_slots = alternative_slots = actor_calls = 0
    alternative_values = {}
    for roster, positions in (
        (9, tuple(range(0, 64, 2))),
        (15, tuple(range(1, 64, 2))),
    ):
        factual = _collect_factual_roster(
            model=model,
            adapter=adapter,
            roster=roster,
            positions=positions,
            tapes=tuple(tapes0[position] for position in positions),
            origins=tuple(origins0[position] for position in positions),
        )
        rosters[roster] = factual
        all_ledgers.append(factual.ledger)
        actor_calls += factual.actor_batch_calls
        with torch.no_grad():
            audit_ledgers, roster_audit_slots, audit_calls = _audit_factual_suffixes(
                model=model, adapter=adapter, factual=factual,
            )
            values, alternative_ledgers, alternative_roster_slots, alternative_calls = (
                _collect_nonfactual_suffixes(model=model, adapter=adapter, factual=factual)
            )
        all_ledgers.extend(audit_ledgers)
        all_ledgers.extend(alternative_ledgers)
        audit_slots += roster_audit_slots
        alternative_slots += alternative_roster_slots
        actor_calls += audit_calls + alternative_calls
        alternative_values[roster] = values

    critic_graphs = {}
    for roster, factual in rosters.items():
        observations = torch.from_numpy(np.ascontiguousarray(factual.observations.transpose(1, 0, 2, 3)))
        roles = torch.from_numpy(np.ascontiguousarray(factual.roles[0]))
        critic_graphs[roster] = model.critic_values_batch(observations, roles)

    episodes = []
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
            ]
            for role in range(3)
        ]).to(torch.int64)
        legal = torch.zeros((3, 6), dtype=torch.bool)
        q_targets = torch.full((3, 6), torch.nan, dtype=torch.float32)
        for role in range(3):
            legal[role, list(LEGAL_ACTION_INDICES[role])] = True
            factual_action = int(factual_actions[role].item())
            for action in LEGAL_ACTION_INDICES[role]:
                q_targets[role, action] = float(
                    factual.terminal_returns[lane]
                    if action == factual_action
                    else alternative_values[roster][(lane, role, action)]
                )
        all_probabilities = torch.stack([row[lane] for row in factual.probability_graphs])
        episodes.append(RSCFEpisode(
            roster_size=roster,
            selected_probabilities=selected,
            q_targets=q_targets.detach(),
            legal_masks=legal,
            factual_actions=factual_actions,
            all_probabilities=all_probabilities,
            critic_values=critic_graphs[roster][lane],
            terminal_return=torch.tensor(factual.terminal_returns[lane], dtype=torch.float32),
        ))
        receipts.append(_capture_exogenous_episode(
            update=update,
            position=position,
            roster=roster,
            tape=tape,
            observations=np.ascontiguousarray(factual.observations[:, lane]),
            roles=np.ascontiguousarray(factual.roles[0, lane]),
            masks=np.ascontiguousarray(factual.masks[:, lane]),
            origins=lane_origins,
            seed_label=seed_label,
        ))
    if model.parameter_bytes() != initial_model:
        raise B01ContractError("R02 collection mutated immutable model bytes")
    batch = B01ArmBatch(tuple(episodes), tuple(receipts), tuple(all_ledgers)).validate(update=update)
    factual_slots = sum(rosters[roster].ledger.environment_slots for roster in (9, 15))
    total_slots = sum(item.environment_slots for item in all_ledgers)
    if (factual_slots, audit_slots, alternative_slots, total_slots) != (768, 1_248, 2_912, 4_928):
        raise B01ContractError("R02 direct one-update work partition differs")
    audit = BatchCollectionAudit(
        schema="FRRIE_B01_BATCH_COLLECTION_AUDIT_V1",
        update=update,
        factual_episodes=64,
        native_width=32,
        factual_slots=factual_slots,
        factual_suffix_audit_slots=audit_slots,
        nonfactual_suffix_slots=alternative_slots,
        total_environment_slots=total_slots,
        factual_suffixes_audited=192,
        alternative_suffixes_executed=448,
        factual_trace_direct_equal=True,
        model_bytes_unchanged=True,
        torch_actor_batch_calls=actor_calls,
        torch_critic_batch_calls=2,
        maximum_actor_lanes=32,
        shared_model_worker_count=1,
    )
    return CollectedUpdate(batch=batch, audit=audit)
