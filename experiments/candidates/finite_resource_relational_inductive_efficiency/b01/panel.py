"""Exact primitive-only B01 complete-panel validators."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ..host import native_endpoint
from .constants import (
    CHECKPOINTS, EVALUATION_EPISODES, EVALUATION_ROSTERS, INTERVENTIONS,
    LEARNED_ARMS, PANEL_SCHEMA, TEST_MANIFEST_SCHEMA, QUANTITY_ORDER,
    PRIMITIVE_ROWS_PER_SEED, ARM_UPDATE_RECEIPTS_PER_SEED,
    PAIRED_CHECKPOINT_RESTORES_PER_SEED, QUANTITY_VALUES_PER_SEED,
    SHADOW_ACTION_PAIRS_PER_SEED, HELDOUT_ROSTERS, HORIZON, UPDATES,
    TRAIN_ROSTERS,
)
from .contract import (
    B01ContractError, validate_invocation_binding, validate_manifest,
    validate_test_manifest, validate_formal_source_gate,
)
from .native_batch import performance_readiness
from .raw_control import validate_raw_control_receipt

_ROW_FIELDS = {
    "seed_label", "arm", "checkpoint", "roster", "intervention", "episode",
    "tape_binding", "J", "D_W", "D_E", "WASTE", "role_action_counts",
    "successful_scan", "successful_uplink", "successful_receive",
    "successful_delivery", "expired", "duplicate", "collision", "empty_radio",
}


_VALIDATED_CELL_TOKEN = object()


@dataclass(frozen=True, slots=True, init=False)
class ValidatedCellSet:
    """Internal product of complete streamed direct-shard validation only."""

    seed_label: str
    checkpoint: int
    cells: tuple[Mapping[str, Any], ...]
    support_by_cell: tuple[bool, ...]
    source_surface: str

    def __init__(
        self, token: object, *, seed_label: str, checkpoint: int,
        cells: tuple[Mapping[str, Any], ...], support_by_cell: tuple[bool, ...],
    ) -> None:
        if token is not _VALIDATED_CELL_TOKEN:
            raise B01ContractError("validated cells require the internal streamed-shard token")
        if len(cells) != len(support_by_cell) or not cells:
            raise B01ContractError("validated cell support inventory differs")
        object.__setattr__(self, "seed_label", seed_label)
        object.__setattr__(self, "checkpoint", checkpoint)
        object.__setattr__(self, "cells", cells)
        object.__setattr__(self, "support_by_cell", support_by_cell)
        object.__setattr__(self, "source_surface", "STREAMED_DIRECT_SHARDS_ONLY")


def _seed_order(seed_labels: Any) -> tuple[str, ...]:
    if not isinstance(seed_labels, (list, tuple)) or not seed_labels:
        raise B01ContractError("candidate seed labels must be a nonempty manifest-order sequence")
    labels = tuple(seed_labels)
    if len(set(labels)) != len(labels) or any(
        not isinstance(label, str) or not label for label in labels
    ):
        raise B01ContractError("candidate seed labels must be unique nonempty strings")
    return labels


def iter_primitive_coordinates(seed_labels: Any):
    """Canonical C-order coordinates; production shards store only implicit indices."""

    for seed_label in _seed_order(seed_labels):
        for checkpoint in CHECKPOINTS:
            for arm in LEARNED_ARMS:
                for roster in EVALUATION_ROSTERS:
                    for intervention in INTERVENTIONS:
                        for episode in range(EVALUATION_EPISODES):
                            yield seed_label, arm, checkpoint, roster, intervention, episode
        for roster in (9, 15):
            for episode in range(EVALUATION_EPISODES):
                yield seed_label, "UNIFORM_LEGAL", None, roster, "INTACT", episode


def iter_arm_update_coordinates(seed_labels: Any):
    for seed_label in _seed_order(seed_labels):
        for update in range(1, UPDATES + 1):
            for arm in LEARNED_ARMS:
                yield seed_label, arm, update


def iter_checkpoint_restore_coordinates(seed_labels: Any):
    for seed_label in _seed_order(seed_labels):
        for checkpoint in CHECKPOINTS:
            yield seed_label, checkpoint


def iter_quantity_coordinates(seed_labels: Any):
    for seed_label in _seed_order(seed_labels):
        for checkpoint in CHECKPOINTS:
            for quantity in QUANTITY_ORDER:
                yield seed_label, checkpoint, quantity


def iter_shadow_action_pair_coordinates(seed_labels: Any):
    """PHY/intact heldout one-step shadow order, never the ROTATE trajectory."""

    for seed_label in _seed_order(seed_labels):
        for checkpoint in CHECKPOINTS:
            for roster in HELDOUT_ROSTERS:
                for episode in range(EVALUATION_EPISODES):
                    for slot in range(HORIZON):
                        for entity in range(roster):
                            yield seed_label, checkpoint, roster, episode, slot, entity


def exact_inventory_cardinalities(seed_labels: Any) -> dict[str, int]:
    seeds = len(_seed_order(seed_labels))
    return {
        "primitive_rows": PRIMITIVE_ROWS_PER_SEED * seeds,
        "arm_update_receipts": ARM_UPDATE_RECEIPTS_PER_SEED * seeds,
        "paired_checkpoint_restores": PAIRED_CHECKPOINT_RESTORES_PER_SEED * seeds,
        "quantity_values": QUANTITY_VALUES_PER_SEED * seeds,
        "shadow_action_pairs": SHADOW_ACTION_PAIRS_PER_SEED * seeds,
    }


_RAW_ARRAY_DESCRIPTOR_FIELDS = {"path", "dtype", "shape", "order", "byte_count"}
_PRIMITIVE_ARRAYS = {
    "dw": ("|u1", (EVALUATION_EPISODES,)),
    "de": ("|u1", (EVALUATION_EPISODES,)),
    "radio_actions": ("<u2", (EVALUATION_EPISODES,)),
    "waste_actions": ("<u2", (EVALUATION_EPISODES,)),
    "successful_scan": ("<u2", (EVALUATION_EPISODES,)),
    "successful_uplink": ("<u2", (EVALUATION_EPISODES,)),
    "successful_receive": ("<u2", (EVALUATION_EPISODES,)),
    "successful_delivery": ("<u2", (EVALUATION_EPISODES,)),
    "expired": ("<u2", (EVALUATION_EPISODES,)),
    "duplicate": ("<u2", (EVALUATION_EPISODES,)),
    "collision": ("<u2", (EVALUATION_EPISODES,)),
    "empty_radio": ("<u2", (EVALUATION_EPISODES,)),
    "role_action_counts": ("<u2", (EVALUATION_EPISODES, 3, 6)),
    "terminal_delivered": ("|u1", (EVALUATION_EPISODES, 2, 3)),
}


def _mmap_direct_array(value: Any, *, dtype: str, shape: tuple[int, ...], name: str):
    import numpy as np

    if not isinstance(value, Mapping) or set(value) != _RAW_ARRAY_DESCRIPTOR_FIELDS:
        raise B01ContractError(f"{name} raw-array descriptor fields differ")
    path = Path(value["path"])
    if not path.is_absolute() or value["dtype"] != dtype or value["shape"] != list(shape):
        raise B01ContractError(f"{name} raw-array dtype/shape/path differs")
    if value["order"] != "C":
        raise B01ContractError(f"{name} must use implicit canonical C-order")
    expected_bytes = math.prod(shape) * np.dtype(dtype).itemsize
    if value["byte_count"] != expected_bytes:
        raise B01ContractError(f"{name} direct byte count differs")
    try:
        if path.stat().st_size != expected_bytes:
            raise B01ContractError(f"{name} persisted raw byte length differs")
        array = np.memmap(path, dtype=np.dtype(dtype), mode="r", shape=shape, order="C")
    except OSError as error:
        raise B01ContractError(f"{name} persisted raw array is unreadable") from error
    return array


def validate_candidate_primitive_shard(value: Any) -> dict[str, Any]:
    """Stream/mmap one full 256-episode direct primitive cell shard.

    The returned cell reduction remains candidate evidence; only a complete
    top-level index can mint ``ValidatedCellSet`` for the production reducer.
    """

    fields = {
        "schema", "seed_label", "arm", "checkpoint", "roster", "intervention",
        "coordinate_order", "tape_surface", "arrays", "complete",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("candidate primitive shard fields differ")
    shard = dict(value)
    if shard["schema"] != "FRRIE_B01_PRIMITIVE_RAW_SHARD_V1" or shard["complete"] is not True:
        raise B01ContractError("candidate primitive shard identity differs")
    if not isinstance(shard["seed_label"], str) or not shard["seed_label"]:
        raise B01ContractError("candidate primitive shard seed differs")
    if shard["arm"] not in (*LEARNED_ARMS, "UNIFORM_LEGAL"):
        raise B01ContractError("candidate primitive shard arm differs")
    if shard["roster"] not in EVALUATION_ROSTERS or shard["intervention"] not in INTERVENTIONS:
        raise B01ContractError("candidate primitive shard cell differs")
    if shard["arm"] == "UNIFORM_LEGAL":
        if shard["checkpoint"] is not None or (
            shard["roster"] not in TRAIN_ROSTERS or shard["intervention"] != "INTACT"
        ):
            raise B01ContractError("candidate U shard schedule differs")
    elif shard["checkpoint"] not in CHECKPOINTS:
        raise B01ContractError("candidate learned shard checkpoint differs")
    if shard["coordinate_order"] != ["episode"]:
        raise B01ContractError("candidate primitive shard coordinate order differs")
    expected_tape = {
        "schema": "FRRIE_B01_EVALUATION_TAPE_SURFACE_V1",
        "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
        "checkpoint_role": "METADATA_ONLY", "arm_independent": True,
        "intervention_independent": True, "checkpoint_independent": True,
    }
    if shard["tape_surface"] != expected_tape:
        raise B01ContractError("candidate primitive shard common tape surface differs")
    if not isinstance(shard["arrays"], Mapping) or set(shard["arrays"]) != set(_PRIMITIVE_ARRAYS):
        raise B01ContractError("candidate primitive shard array inventory differs")
    arrays = {
        name: _mmap_direct_array(
            shard["arrays"][name], dtype=dtype, shape=shape, name=f"primitive.{name}",
        )
        for name, (dtype, shape) in _PRIMITIVE_ARRAYS.items()
    }
    role_total = 12 * (shard["roster"] // 3)
    legal_by_role = ({0, 1, 5}, {0, 1, 5}, {2, 3, 4, 5})
    endpoints: list[float] = []
    west: list[float] = []
    east: list[float] = []
    support = Counter()
    for episode in range(EVALUATION_EPISODES):
        delivered = arrays["terminal_delivered"][episode]
        if not bool(((delivered == 0) | (delivered == 1)).all()):
            raise B01ContractError("terminal delivered mask is not literal binary state")
        dw = int(delivered[0].sum())
        de = int(delivered[1].sum())
        if int(arrays["dw"][episode]) != dw or int(arrays["de"][episode]) != de:
            raise B01ContractError("D_W/D_E differ from terminal delivered mask")
        radio = int(arrays["radio_actions"][episode])
        waste_actions = int(arrays["waste_actions"][episode])
        if waste_actions > radio or (radio == 0 and waste_actions != 0):
            raise B01ContractError("direct waste/radio action ledger differs")
        waste = 0.0 if radio == 0 else waste_actions / radio
        counts = arrays["role_action_counts"][episode]
        for role in range(3):
            if int(counts[role].sum()) != role_total or any(
                int(counts[role, action]) != 0
                for action in range(6) if action not in legal_by_role[role]
            ):
                raise B01ContractError("direct role/action opportunity ledger differs")
        scan = int(counts[0, 0]) + int(counts[1, 0])
        uplink = int(counts[0, 1]) + int(counts[1, 1])
        receive = int(counts[2, 2]) + int(counts[2, 3])
        if (
            int(arrays["successful_scan"][episode]) > scan
            or int(arrays["successful_uplink"][episode]) > uplink
            or int(arrays["successful_receive"][episode]) > receive
            or int(arrays["successful_delivery"][episode]) != dw + de
            or int(arrays["empty_radio"][episode]) > radio
        ):
            raise B01ContractError("direct event/success ledger exceeds opportunities")
        endpoint = native_endpoint(dw, de, waste)
        endpoints.append(float(endpoint))
        west.append(dw / 3.0)
        east.append(de / 3.0)
        support[(dw, de, waste_actions, radio)] += 1
    return {
        "schema": "FRRIE_B01_VALIDATED_PRIMITIVE_CELL_CANDIDATE_V1",
        "seed_label": shard["seed_label"], "checkpoint": shard["checkpoint"],
        "arm": shard["arm"], "roster": shard["roster"],
        "intervention": shard["intervention"],
        "native_return": math.fsum(endpoints) / EVALUATION_EPISODES,
        "basin_west": math.fsum(west) / EVALUATION_EPISODES,
        "basin_east": math.fsum(east) / EVALUATION_EPISODES,
        "support_census": [
            {
                "D_W": key[0], "D_E": key[1], "waste_actions": key[2],
                "radio_actions": key[3], "episodes": count,
            }
            for key, count in sorted(support.items())
        ],
        "support_classification": None,
        "legal_tv": None, "tv_sup": None,
        "candidate_only": True,
    }


_DIRECT_METRICS = (
    "dw", "de", "radio_actions", "waste_actions", "new_timely_deliveries",
    "expired_arrivals", "duplicate_arrivals", "collision_loss", "empty_actions",
)


def validate_direct_primitive_trace_shard(value: Any, *, root: bytes) -> dict[str, Any]:
    """Validate the production-format per-slot direct primitive surface.

    This component is necessary but not sufficient for a production token:
    top-index, checkpoint, training, shadow, and support-classification seams
    must also close before ``ValidatedCellSet`` can be constructed.
    """

    import numpy as np
    from ..policy import LEGAL_ACTION_INDICES
    from .tapes import evaluation_tape

    fields = {
        "schema", "seed_label", "arm", "checkpoint", "roster", "intervention",
        "coordinate_order", "arrays", "complete",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("direct primitive trace shard fields differ")
    shard = dict(value)
    if shard["schema"] != "FRRIE_B01_PRIMITIVE_TRACE_SHARD_V1" or shard["complete"] is not True:
        raise B01ContractError("direct primitive trace shard identity differs")
    if shard["arm"] not in (*LEARNED_ARMS, "UNIFORM_LEGAL"):
        raise B01ContractError("direct primitive trace arm differs")
    roster = shard["roster"]
    if roster not in EVALUATION_ROSTERS or shard["intervention"] not in INTERVENTIONS:
        raise B01ContractError("direct primitive trace cell differs")
    if shard["arm"] == "UNIFORM_LEGAL":
        if shard["checkpoint"] is not None or roster not in TRAIN_ROSTERS or shard["intervention"] != "INTACT":
            raise B01ContractError("direct U primitive trace schedule differs")
    elif shard["checkpoint"] not in CHECKPOINTS:
        raise B01ContractError("direct learned primitive checkpoint differs")
    if shard["coordinate_order"] != ["episode", "slot", "entity"]:
        raise B01ContractError("direct primitive trace coordinate order differs")
    arrays_contract = {
        "observation": ("<f4", (EVALUATION_EPISODES, HORIZON, roster, 22)),
        "actions": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "predecision_previous_action": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "predecision_previous_success": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "poststep_previous_success": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "terminal_delivered": ("|u1", (EVALUATION_EPISODES, 2, 3)),
        **{
            f"metric_{name}": ("<u4", (EVALUATION_EPISODES, HORIZON))
            for name in _DIRECT_METRICS
        },
    }
    if not isinstance(shard["arrays"], Mapping) or set(shard["arrays"]) != set(arrays_contract):
        raise B01ContractError("direct primitive trace array inventory differs")
    arrays = {
        name: _mmap_direct_array(
            shard["arrays"][name], dtype=dtype, shape=shape,
            name=f"primitive_trace.{name}",
        )
        for name, (dtype, shape) in arrays_contract.items()
    }
    observations = arrays["observation"]
    actions = arrays["actions"]
    previous_action = arrays["predecision_previous_action"]
    previous_success = arrays["predecision_previous_success"]
    poststep_success = arrays["poststep_previous_success"]
    roles = np.repeat(np.arange(3, dtype=np.uint8), roster // 3)
    if not np.isfinite(observations).all() or not np.array_equal(
        observations[:, :, :, 21].astype(np.uint8), previous_success,
    ):
        raise B01ContractError("direct primitive observation/success bytes differ")
    if (
        bool((previous_success > 1).any()) or bool((poststep_success > 1).any())
        or bool((arrays["terminal_delivered"] > 1).any())
    ):
        raise B01ContractError("direct primitive trace binary state differs")
    if bool((previous_success[:, 0, :] != 0).any()):
        raise B01ContractError("slot-zero predecision cannot carry prior success")
    if bool((previous_action[:, 0, :] != 255).any()):
        raise B01ContractError("slot-zero previous_action must use the explicit unset sentinel 255")
    if bool((previous_action[:, 1:, :] != actions[:, :-1, :]).any()):
        raise B01ContractError("predecision previous_action differs from prior direct action")
    previous_onehot = observations[:, :, :, 15:21]
    if bool((previous_onehot[:, 0] != 0.0).any()) or not np.array_equal(
        previous_onehot[:, 1:].sum(axis=-1),
        np.ones(previous_action[:, 1:].shape, dtype=np.float32),
    ) or not np.array_equal(
        previous_onehot[:, 1:].argmax(axis=-1).astype(np.uint8), previous_action[:, 1:],
    ):
        raise B01ContractError("direct primitive observation previous-action one-hot differs")
    if bool((poststep_success[:, :-1, :] != previous_success[:, 1:, :]).any()):
        raise B01ContractError("poststep success differs from the next predecision bytes")
    if bool((poststep_success[:, -1, :] != 0).any()):
        raise B01ContractError("terminal slot poststep success must be zero")
    for entity, role in enumerate(roles):
        legal = LEGAL_ACTION_INDICES[int(role)]
        if not bool(np.isin(actions[:, :, entity], legal).all()):
            raise B01ContractError("direct action trace violates role-legal support")
    endpoint_values: list[float] = []
    west_values: list[float] = []
    east_values: list[float] = []
    support = Counter()
    cell_counts = {
        "successful_scan": 0, "successful_uplink": 0,
        "successful_receive": 0, "successful_delivery": 0,
    }
    execution_census = Counter()
    event_census = Counter()
    for episode in range(EVALUATION_EPISODES):
        tape = evaluation_tape(
            root, seed_label=shard["seed_label"], roster=roster, episode=episode,
        )
        for basin in range(2):
            for event_slot in map(int, tape.event_times[basin]):
                event_census[(basin, event_slot)] += 1
        for slot in range(HORIZON):
            for entity, role in enumerate(roles):
                action = int(actions[episode, slot, entity])
                execution_census[(int(role), action)] += 1
                if action == 0 and role < 2:
                    ordinal_present = bool((tape.event_times[int(role)] == slot).any())
                    local = entity % (roster // 3)
                    if ordinal_present and float(tape.detection_uniform[slot, int(role), local]) < 0.75:
                        cell_counts["successful_scan"] += 1
                if slot > 0 and int(previous_success[episode, slot, entity]) == 1:
                    prior = int(previous_action[episode, slot, entity])
                    if prior == 1:
                        cell_counts["successful_uplink"] += 1
                    elif prior in (2, 3):
                        cell_counts["successful_receive"] += 1
                    elif prior == 4:
                        cell_counts["successful_delivery"] += 1
        for metric in _DIRECT_METRICS:
            trajectory = arrays[f"metric_{metric}"][episode]
            if bool((trajectory[1:] < trajectory[:-1]).any()):
                raise B01ContractError("native cumulative metric trajectory regressed")
        delivered = arrays["terminal_delivered"][episode]
        dw = int(delivered[0].sum())
        de = int(delivered[1].sum())
        final = {metric: int(arrays[f"metric_{metric}"][episode, -1]) for metric in _DIRECT_METRICS}
        if (
            final["dw"] != dw or final["de"] != de
            or final["new_timely_deliveries"] != dw + de
        ):
            raise B01ContractError("native terminal metrics differ from delivered mask")
        radio = final["radio_actions"]
        direct_radio = int(np.isin(actions[episode], (1, 2, 3, 4)).sum())
        if radio != direct_radio or final["waste_actions"] > radio:
            raise B01ContractError("native radio/waste metric differs from direct actions")
        waste = 0.0 if radio == 0 else final["waste_actions"] / radio
        endpoint_values.append(float(native_endpoint(dw, de, waste)))
        west_values.append(dw / 3.0)
        east_values.append(de / 3.0)
        support[(dw, de, final["waste_actions"], radio)] += 1
    return {
        "schema": "FRRIE_B01_DIRECT_PRIMITIVE_CELL_COMPONENT_V1",
        "seed_label": shard["seed_label"], "checkpoint": shard["checkpoint"],
        "arm": shard["arm"], "roster": roster, "intervention": shard["intervention"],
        "native_return": math.fsum(endpoint_values) / EVALUATION_EPISODES,
        "basin_west": math.fsum(west_values) / EVALUATION_EPISODES,
        "basin_east": math.fsum(east_values) / EVALUATION_EPISODES,
        "direct_success_counts": cell_counts,
        "role_action_execution_census": [
            {"role": key[0], "action": key[1], "count": count}
            for key, count in sorted(execution_census.items())
        ],
        "legal_action_opportunity_census": [
            {
                "role": role, "action": action,
                "count": EVALUATION_EPISODES * HORIZON * (roster // 3),
            }
            for role, legal in enumerate(LEGAL_ACTION_INDICES) for action in legal
        ],
        "event_opportunity_census": [
            {
                "basin": key[0], "slot": key[1], "scheduled_events": count,
                "scan_opportunities": count * (roster // 3),
            }
            for key, count in sorted(event_census.items())
        ],
        "endpoint_outcome_census": [
            {"D_W": key[0], "D_E": key[1], "waste_actions": key[2],
             "radio_actions": key[3], "episodes": count}
            for key, count in sorted(support.items())
        ],
        "support_inputs": ["legal_action_opportunity_census", "event_opportunity_census"],
        "support_classification": None, "legal_tv": None, "tv_sup": None,
        "component_complete": True, "production_token_minted": False,
    }


def validate_direct_shadow_trace_shard(
    value: Any, *, manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Reopen a literal checkpoint and reproduce heldout PHY/intact actor bytes."""

    import numpy as np
    import torch
    from ..arms import LearnedArm
    from ..policy import FRRIEActorCritic, LEGAL_ACTION_INDICES
    from .checkpoint import decode_checkpoint

    fields = {
        "schema", "seed_label", "checkpoint", "roster", "checkpoint_path",
        "coordinate_order", "trace_arrays", "shadow_arrays", "shadow_semantics", "complete",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("direct shadow trace shard fields differ")
    shard = dict(value)
    if shard["schema"] != "FRRIE_B01_PHY_INTACT_SHADOW_TRACE_SHARD_V1" or shard["complete"] is not True:
        raise B01ContractError("direct shadow trace shard identity differs")
    if shard["checkpoint"] not in CHECKPOINTS or shard["roster"] not in HELDOUT_ROSTERS:
        raise B01ContractError("direct shadow trace coordinate differs")
    if shard["coordinate_order"] != ["episode", "slot", "entity"]:
        raise B01ContractError("direct shadow trace coordinate order differs")
    if shard["shadow_semantics"] != {
        "operation": "SEMANTIC_COLUMN_ROTATE_ONE_STEP_ONLY",
        "incoming_hidden_source": "SAME_ACTUAL_TRACE_INCOMING_HIDDEN",
        "shadow_hidden": "DISCARDED",
        "native_action_effect": False,
        "actual_rotate_trajectory": "SEPARATE_12_SLOT_SEQUENTIAL_PRIMITIVE_CELL",
    }:
        raise B01ContractError("direct shadow semantics differ")
    checkpoint_path = Path(shard["checkpoint_path"])
    if not checkpoint_path.is_absolute():
        raise B01ContractError("shadow checkpoint path must be absolute")
    try:
        checkpoint_bytes = checkpoint_path.read_bytes()
    except OSError as error:
        raise B01ContractError("shadow checkpoint literal file is unreadable") from error
    decoded = decode_checkpoint(
        checkpoint_bytes, manifest=manifest, expected_seed_label=shard["seed_label"],
        expected_update=shard["checkpoint"], expected_test_only=False,
    )
    model = FRRIEActorCritic(LearnedArm.from_parameter_bytes(
        "PHY_TRUST", decoded["arm_state_bytes"]["PHY_TRUST"],
    ))
    roster = shard["roster"]
    common = (EVALUATION_EPISODES, HORIZON, roster)
    trace_contract = {
        "observation": ("<f4", (*common, 22)),
        "incoming_hidden": ("<f4", (*common, 64)),
        "intact_probability": ("<f4", (*common, 6)),
        "role": ("|u1", common), "legal_mask": ("|u1", (*common, 6)),
    }
    shadow_contract = {"shadow_probability": ("<f4", (*common, 6))}
    if not isinstance(shard["trace_arrays"], Mapping) or set(shard["trace_arrays"]) != set(trace_contract):
        raise B01ContractError("direct actual trace array inventory differs")
    if not isinstance(shard["shadow_arrays"], Mapping) or set(shard["shadow_arrays"]) != set(shadow_contract):
        raise B01ContractError("direct shadow array inventory differs")
    arrays = {
        name: _mmap_direct_array(
            shard["trace_arrays"][name], dtype=dtype, shape=shape,
            name=f"shadow_trace.{name}",
        )
        for name, (dtype, shape) in trace_contract.items()
    }
    arrays.update({
        name: _mmap_direct_array(
            shard["shadow_arrays"][name], dtype=dtype, shape=shape,
            name=f"shadow_trace.{name}",
        )
        for name, (dtype, shape) in shadow_contract.items()
    })
    expected_roles = np.repeat(np.arange(3, dtype=np.uint8), roster // 3)
    expected_mask = np.zeros((roster, 6), dtype=np.uint8)
    for entity, role in enumerate(expected_roles):
        expected_mask[entity, list(LEGAL_ACTION_INDICES[int(role)])] = 1
    if not np.isfinite(arrays["observation"]).all() or not np.isfinite(arrays["incoming_hidden"]).all():
        raise B01ContractError("direct observation/hidden trace is nonfinite")
    if not bool((arrays["role"] == expected_roles.reshape(1, 1, roster)).all()):
        raise B01ContractError("direct shadow trace role bytes differ")
    if not bool((arrays["legal_mask"] == expected_mask.reshape(1, 1, roster, 6)).all()):
        raise B01ContractError("direct shadow trace legal-mask bytes differ")
    tv_sum = 0.0
    tv_sup_sum = 0.0
    pairs = EVALUATION_EPISODES * HORIZON * roster
    roles_tensor = torch.from_numpy(expected_roles.astype(np.int64))
    with torch.no_grad():
        for episode in range(EVALUATION_EPISODES):
            expected_incoming = np.zeros((roster, 64), dtype=np.float32)
            for slot in range(HORIZON):
                incoming = np.asarray(arrays["incoming_hidden"][episode, slot], dtype=np.float32)
                if incoming.tobytes(order="C") != expected_incoming.tobytes(order="C"):
                    raise B01ContractError("actual incoming-hidden trace continuity differs")
                observation = np.asarray(arrays["observation"][episode, slot], dtype=np.float32)
                observation_tensor = torch.from_numpy(observation.copy())
                incoming_tensor = torch.from_numpy(incoming.copy())
                actual = model.actor_step(observation_tensor, roles_tensor, incoming_tensor)
                shadow = model.shadow_step(observation_tensor, roles_tensor, incoming_tensor)
                actual_bytes = actual.probabilities.detach().numpy().astype("<f4", copy=False).tobytes()
                shadow_bytes = shadow.probabilities.detach().numpy().astype("<f4", copy=False).tobytes()
                if actual_bytes != arrays["intact_probability"][episode, slot].tobytes(order="C"):
                    raise B01ContractError("stored intact actor probability bytes differ")
                if shadow_bytes != arrays["shadow_probability"][episode, slot].tobytes(order="C"):
                    raise B01ContractError("stored shadow actor probability bytes differ")
                actual_np = actual.probabilities.detach().numpy()
                shadow_np = shadow.probabilities.detach().numpy()
                for entity, role in enumerate(expected_roles):
                    legal = LEGAL_ACTION_INDICES[int(role)]
                    tv_sum += 0.5 * math.fsum(
                        abs(float(actual_np[entity, action]) - float(shadow_np[entity, action]))
                        for action in legal
                    )
                    m = len(legal)
                    tv_sup_sum += 1.0 - (m - 1) * (0.04 / m) - min(
                        float(actual_np[entity, action]) for action in legal
                    )
                expected_incoming = actual.hidden.detach().numpy().astype(np.float32, copy=True)
    return {
        "schema": "FRRIE_B01_DIRECT_SHADOW_CELL_COMPONENT_V1",
        "seed_label": shard["seed_label"], "checkpoint": shard["checkpoint"],
        "arm": "PHY_TRUST", "roster": roster, "intervention": "INTACT",
        "legal_tv": tv_sum / pairs, "tv_sup": tv_sup_sum / pairs,
        "direct_pair_count": pairs, "checkpoint_literal_reopened": True,
        "actor_and_shadow_bytes_recomputed": True, "shadow_hidden_discarded": True,
        "native_action_effect": False, "component_complete": True,
        "production_token_minted": False,
    }


def replay_direct_primitive_trace_shard(
    value: Any, *, manifest: Mapping[str, Any], invocation_binding: Mapping[str, Any],
    adapter: Any,
) -> dict[str, Any]:
    """Replay one full cell through the admitted package-native width-32 ABI."""

    import numpy as np
    from dataclasses import asdict
    from ..native.native_abi import STATE_SIZE, NativeStateV1
    from .native_batch import B01NativeBatchEnvironment
    from .tapes import evaluation_tape

    manifest0 = validate_manifest(manifest)
    validate_invocation_binding(invocation_binding, require_test_only=False)
    adapter.assert_live_contract()
    if value["seed_label"] not in manifest0["seed_packet"]["contract"]["labels"]:
        raise B01ContractError("native replay seed is absent from persisted seed packet")
    root_index = manifest0["seed_packet"]["contract"]["labels"].index(value["seed_label"])
    root = bytes.fromhex(manifest0["seed_packet"]["contract"]["roots_hex"][root_index])
    component = validate_direct_primitive_trace_shard(value, root=root)
    roster = value["roster"]
    arrays_contract = {
        "observation": ("<f4", (EVALUATION_EPISODES, HORIZON, roster, 22)),
        "actions": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "predecision_previous_action": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "predecision_previous_success": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "poststep_previous_success": ("|u1", (EVALUATION_EPISODES, HORIZON, roster)),
        "terminal_delivered": ("|u1", (EVALUATION_EPISODES, 2, 3)),
        **{
            f"metric_{name}": ("<u4", (EVALUATION_EPISODES, HORIZON))
            for name in _DIRECT_METRICS
        },
    }
    arrays = {
        name: _mmap_direct_array(
            value["arrays"][name], dtype=dtype, shape=shape,
            name=f"native_replay.{name}",
        )
        for name, (dtype, shape) in arrays_contract.items()
    }
    reset_calls = observe_calls = step_calls = environment_slots = 0
    for start in range(0, EVALUATION_EPISODES, 32):
        stop = min(start + 32, EVALUATION_EPISODES)
        episodes = list(range(start, stop))
        tapes = [
            evaluation_tape(root, seed_label=value["seed_label"], roster=roster, episode=episode)
            for episode in episodes
        ]
        environment = B01NativeBatchEnvironment(
            adapter, roster=roster, lanes=len(episodes),
        )
        environment.reset(tapes)
        reset_calls += 1
        prior_step_success = None
        for slot in range(HORIZON):
            observation = environment.observe()
            observe_calls += 1
            obs = observation.observations
            if obs.astype("<f4", copy=False).tobytes(order="C") != arrays[
                "observation"
            ][start:stop, slot].tobytes(order="C"):
                raise B01ContractError("native replay full observation bytes differ")
            if observation.terminals != (False,) * len(episodes) or observation.slots != (
                slot,
            ) * len(episodes):
                raise B01ContractError("native replay became terminal before its step")
            if not np.array_equal(
                observation.roles,
                np.broadcast_to(
                    np.repeat(np.arange(3, dtype=np.int64), roster // 3),
                    (len(episodes), roster),
                ),
            ):
                raise B01ContractError("native replay role bytes differ")
            from ..policy import LEGAL_ACTION_INDICES
            expected_masks = np.zeros((len(episodes), roster, 6), dtype=np.bool_)
            for entity, role in enumerate(np.repeat(np.arange(3), roster // 3)):
                expected_masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
            if not np.array_equal(observation.legal_masks, expected_masks):
                raise B01ContractError("native replay legal-mask bytes differ")
            if not np.array_equal(
                obs[:, :, 21].astype(np.uint8),
                arrays["predecision_previous_success"][start:stop, slot],
            ):
                raise B01ContractError("native replay predecision success differs")
            if slot > 0:
                onehot = obs[:, :, 15:21]
                if not np.array_equal(onehot.sum(axis=-1), np.ones((len(episodes), roster), dtype=np.float32)):
                    raise B01ContractError("native replay previous-action one-hot differs")
                if not np.array_equal(
                    onehot.argmax(axis=-1).astype(np.uint8),
                    arrays["predecision_previous_action"][start:stop, slot],
                ):
                    raise B01ContractError("native replay prior action differs")
                if not np.array_equal(
                    prior_step_success,
                    arrays["predecision_previous_success"][start:stop, slot],
                ):
                    raise B01ContractError("StepOutput success differs from next native observe")
            step = environment.step(arrays["actions"][start:stop, slot])
            step_calls += 1
            environment_slots += len(episodes)
            if step.terminals != ((slot == HORIZON - 1),) * len(episodes):
                raise B01ContractError("native replay terminal frontier differs")
            if not np.array_equal(
                step.previous_success.astype(np.uint8),
                arrays["poststep_previous_success"][start:stop, slot],
            ):
                raise B01ContractError("native replay StepOutput success bytes differ")
            prior_step_success = step.previous_success.astype(np.uint8, copy=True)
            for lane, primitive in enumerate(step.primitives):
                direct = asdict(primitive)
                metrics = {
                    "dw": direct["dw"], "de": direct["de"],
                    "radio_actions": direct["radio_actions"],
                    "waste_actions": direct["waste_actions"],
                    "new_timely_deliveries": direct["successful_deliveries"],
                    "expired_arrivals": direct["expired"],
                    "duplicate_arrivals": direct["duplicate"],
                    "collision_loss": direct["collision"],
                    "empty_actions": direct["empty_radio"],
                }
                if any(
                    int(arrays[f"metric_{name}"][start + lane, slot]) != int(observed)
                    for name, observed in metrics.items()
                ):
                    raise B01ContractError("native replay cumulative metric bytes differ")
        if bool((prior_step_success != 0).any()):
            raise B01ContractError("native replay terminal StepOutput success is nonzero")
        snapshots = environment.snapshot()
        for lane, episode in enumerate(episodes):
            state = NativeStateV1.from_buffer_copy(
                snapshots[lane * STATE_SIZE:(lane + 1) * STATE_SIZE]
            )
            delivered = np.ctypeslib.as_array(state.delivered).reshape(2, 3)
            if not np.array_equal(delivered, arrays["terminal_delivered"][episode]):
                raise B01ContractError("native replay terminal delivered mask differs")
            if state.pending_uplink_count != 0 or state.pending_base_present != 0:
                raise B01ContractError("native replay terminal state retained pending effects")
    expected_work = {
        "native_reset_calls": 8, "native_observe_calls": 96,
        "native_step_calls": 96, "environment_slots": EVALUATION_EPISODES * HORIZON,
        "native_width": 32,
    }
    observed_work = {
        "native_reset_calls": reset_calls, "native_observe_calls": observe_calls,
        "native_step_calls": step_calls, "environment_slots": environment_slots,
        "native_width": 32,
    }
    if observed_work != expected_work:
        raise B01ContractError("native replay work ledger differs")
    return {
        **component, "schema": "FRRIE_B01_NATIVE_REPLAYED_PRIMITIVE_CELL_COMPONENT_V1",
        "native_replay": True, "validation_replay_work": observed_work,
        "scientific_work_accounting": "EXCLUDED_POSTHOC_DETERMINISTIC_VALIDATION",
        "stepoutput_to_next_observe_revalidated": True,
        "terminal_no_pending_revalidated": True,
        "production_token_minted": False,
    }


def validate_between_arm_tv_shard(value: Any, *, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the Pro-selected symmetric between-arm descriptive diagnostic."""

    import numpy as np
    import torch
    from ..arms import LearnedArm
    from ..policy import FRRIEActorCritic, LEGAL_ACTION_INDICES
    from .checkpoint import decode_checkpoint

    fields = {
        "schema", "seed_label", "checkpoint", "roster", "intervention",
        "checkpoint_path", "seed_contact_ledger", "availability", "coordinate_order",
        "tape_surface", "raw_row_schema",
        "trace_arrays", "raw_arrays", "complete",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError("between-arm TV shard fields differ")
    shard = dict(value)
    if shard["schema"] != "FRRIE_B01_BETWEEN_ARM_TV_SHARD_V1" or shard["complete"] is not True:
        raise B01ContractError("between-arm TV shard identity differs")
    checkpoint = shard["checkpoint"]
    roster = shard["roster"]
    intervention = shard["intervention"]
    if checkpoint not in CHECKPOINTS or roster not in EVALUATION_ROSTERS or intervention not in INTERVENTIONS:
        raise B01ContractError("between-arm TV cell coordinate differs")
    if shard["coordinate_order"] != ["episode", "slot", "entity", "anchor_PHY_EDGE"]:
        raise B01ContractError("between-arm TV coordinate order differs")
    if shard["raw_row_schema"] != "FRRIE_B01_BETWEEN_ARM_TV_RAW_V1":
        raise B01ContractError("between-arm TV raw row schema differs")
    if shard["tape_surface"] != {
        "schema": "FRRIE_B01_EVALUATION_TAPE_SURFACE_V1",
        "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
        "checkpoint_role": "METADATA_ONLY", "arm_independent": True,
        "intervention_independent": True, "checkpoint_independent": True,
    }:
        raise B01ContractError("between-arm TV tape surface differs")
    path = Path(shard["checkpoint_path"])
    if not path.is_absolute():
        raise B01ContractError("between-arm TV checkpoint path must be absolute")
    try:
        checkpoint_bytes = path.read_bytes()
    except OSError as error:
        raise B01ContractError("between-arm TV checkpoint is unreadable") from error
    decoded = decode_checkpoint(
        checkpoint_bytes, manifest=manifest, expected_seed_label=shard["seed_label"],
        expected_update=checkpoint, expected_test_only=False,
    )
    ledger = shard["seed_contact_ledger"]
    if not isinstance(ledger, Mapping) or set(ledger) != {
        "schema", "final_checkpoint_path", "complete_projection_ledger",
        "first_tight_contact_update",
    } or ledger["schema"] != "FRRIE_B01_SEED_CONTACT_LEDGER_V1" or ledger[
        "complete_projection_ledger"
    ] is not True:
        raise B01ContractError("between-arm seed contact ledger fields differ")
    final_path = Path(ledger["final_checkpoint_path"])
    if not final_path.is_absolute():
        raise B01ContractError("between-arm final contact checkpoint path must be absolute")
    try:
        final_bytes = final_path.read_bytes()
    except OSError as error:
        raise B01ContractError("between-arm final contact checkpoint is unreadable") from error
    final_decoded = decode_checkpoint(
        final_bytes, manifest=manifest, expected_seed_label=shard["seed_label"],
        expected_update=512, expected_test_only=False,
    )
    contact = final_decoded["projection_audit"]["first_tight_contact_update"]
    if ledger["first_tight_contact_update"] != contact:
        raise B01ContractError("between-arm final contact ledger differs from checkpoint512")
    current_contact = decoded["projection_audit"]["first_tight_contact_update"]
    expected_current_contact = contact if contact is not None and contact <= checkpoint else None
    if current_contact != expected_current_contact:
        raise B01ContractError("between-arm current checkpoint contact frontier differs")
    availability = shard["availability"]
    if not isinstance(availability, Mapping) or set(availability) != {
        "status", "available", "first_tight_contact_update", "checkpoint",
    } or availability["checkpoint"] != checkpoint or availability[
        "first_tight_contact_update"
    ] != contact:
        raise B01ContractError("between-arm TV availability binding differs")
    available = contact is not None and contact <= checkpoint
    if availability["available"] is not available:
        raise B01ContractError("between-arm TV availability differs from tight contact")
    if not available:
        expected_status = "NO_TIGHT_CONTACT_BY_512" if contact is None else "PRE_TIGHT_CONTACT"
        if availability["status"] != expected_status or (
            shard["trace_arrays"] is not None or shard["raw_arrays"] is not None
        ):
            raise B01ContractError("unavailable between-arm cell must contain no raw rows")
        return {
            "schema": "FRRIE_B01_BETWEEN_ARM_TV_CELL_V1",
            "seed_label": shard["seed_label"], "checkpoint": checkpoint,
            "roster": roster, "intervention": intervention,
            "status": expected_status, "available": False,
            "first_tight_contact_update": contact, "raw_row_count": 0,
            "individual_cell_mean": None, "diagnostic_only": True,
            "included_in_ordered_28": False, "production_token_minted": False,
        }
    if availability["status"] != "AVAILABLE":
        raise B01ContractError("available between-arm TV cell status differs")
    common = (EVALUATION_EPISODES, HORIZON, roster)
    trace_contract = {
        "observation": ("<f4", (*common, 2, 22)),
        "incoming_hidden": ("<f4", (*common, 2, 64)),
        "role": ("|u1", common), "legal_mask": ("|u1", (*common, 6)),
        "selected_action": ("|u1", (*common, 2)),
    }
    raw_contract = {
        "probability_bits": ("<u4", (*common, 2, 2, 6)),
        "tv64": ("<f8", (*common, 2)),
    }
    if not isinstance(shard["trace_arrays"], Mapping) or set(shard["trace_arrays"]) != set(trace_contract):
        raise B01ContractError("between-arm full-roster trace inventory differs")
    if not isinstance(shard["raw_arrays"], Mapping) or set(shard["raw_arrays"]) != set(raw_contract):
        raise B01ContractError("between-arm raw-bit inventory differs")
    arrays = {
        name: _mmap_direct_array(
            shard["trace_arrays"][name], dtype=dtype, shape=shape,
            name=f"between_arm.{name}",
        )
        for name, (dtype, shape) in trace_contract.items()
    }
    arrays.update({
        name: _mmap_direct_array(
            shard["raw_arrays"][name], dtype=dtype, shape=shape,
            name=f"between_arm.{name}",
        )
        for name, (dtype, shape) in raw_contract.items()
    })
    roles = np.repeat(np.arange(3, dtype=np.uint8), roster // 3)
    masks = np.zeros((roster, 6), dtype=np.uint8)
    for entity, role in enumerate(roles):
        masks[entity, list(LEGAL_ACTION_INDICES[int(role)])] = 1
    if not np.array_equal(arrays["role"], np.broadcast_to(roles, common)) or not np.array_equal(
        arrays["legal_mask"], np.broadcast_to(masks, (*common, 6)),
    ):
        raise B01ContractError("between-arm role/legal mask bytes differ")
    if not np.isfinite(arrays["observation"]).all() or not np.isfinite(arrays["incoming_hidden"]).all():
        raise B01ContractError("between-arm full-roster input is nonfinite")
    models = {
        arm: FRRIEActorCritic(LearnedArm.from_parameter_bytes(
            arm, decoded["arm_state_bytes"][arm],
        ))
        for arm in LEARNED_ARMS
    }
    role_tensor = torch.from_numpy(roles.astype(np.int64))
    from ..tapes import inverse_cdf_action
    from .tapes import evaluation_tape
    labels = manifest["seed_packet"]["contract"]["labels"]
    roots = manifest["seed_packet"]["contract"]["roots_hex"]
    root = bytes.fromhex(roots[labels.index(shard["seed_label"])])
    tv_values: list[float] = []
    rotate = intervention == "SEMANTIC_COLUMN_ROTATE"
    with torch.no_grad():
        for episode in range(EVALUATION_EPISODES):
            tape = evaluation_tape(
                root, seed_label=shard["seed_label"], roster=roster, episode=episode,
            )
            expected_hidden = {
                "PHY_TRUST": np.zeros((roster, 64), dtype=np.float32),
                "EDGE_FLEX": np.zeros((roster, 64), dtype=np.float32),
            }
            for slot in range(HORIZON):
                for anchor_index in range(2):
                    anchor = LEARNED_ARMS[anchor_index]
                    observation = np.asarray(
                        arrays["observation"][episode, slot, :, anchor_index], dtype=np.float32,
                    )
                    hidden = np.asarray(
                        arrays["incoming_hidden"][episode, slot, :, anchor_index], dtype=np.float32,
                    )
                    if hidden.tobytes(order="C") != expected_hidden[anchor].tobytes(order="C"):
                        raise B01ContractError("between-arm anchor natural hidden continuity differs")
                    steps = [
                        models[arm].actor_step(
                            torch.from_numpy(observation.copy()), role_tensor,
                            torch.from_numpy(hidden.copy()), rotate_columns=rotate,
                        )
                        for arm in LEARNED_ARMS
                    ]
                    outputs = [
                        step.probabilities.detach().numpy().astype("<f4", copy=False)
                        for step in steps
                    ]
                    bits = np.stack(outputs, axis=1).view("<u4")
                    if not np.array_equal(
                        bits, arrays["probability_bits"][episode, slot, :, anchor_index],
                    ):
                        raise B01ContractError("between-arm exact FP32 probability bits differ")
                    own = outputs[anchor_index]
                    for entity in range(roster):
                        selected = inverse_cdf_action(
                            own[entity], float(tape.action_uniform[slot, entity]),
                        )
                        if int(arrays["selected_action"][episode, slot, entity, anchor_index]) != selected:
                            raise B01ContractError(
                                "between-arm own-policy selected action/tape binding differs"
                            )
                    for entity, role in enumerate(roles):
                        legal = LEGAL_ACTION_INDICES[int(role)]
                        tv = 0.5 * math.fsum(
                            abs(float(outputs[0][entity, action]) - float(outputs[1][entity, action]))
                            for action in legal
                        )
                        stored = float(arrays["tv64"][episode, slot, entity, anchor_index])
                        if np.float64(stored).tobytes() != np.float64(tv).tobytes():
                            raise B01ContractError("between-arm stored tv64 differs")
                        tv_values.append(tv)
                    expected_hidden[anchor] = steps[anchor_index].hidden.detach().numpy().astype(
                        np.float32, copy=True,
                    )
    expected_rows = EVALUATION_EPISODES * HORIZON * roster * 2
    if len(tv_values) != expected_rows:
        raise B01ContractError("between-arm raw row cardinality differs")
    return {
        "schema": "FRRIE_B01_BETWEEN_ARM_TV_CELL_V1",
        "seed_label": shard["seed_label"], "checkpoint": checkpoint,
        "roster": roster, "intervention": intervention,
        "status": "AVAILABLE", "available": True,
        "first_tight_contact_update": contact, "raw_row_count": expected_rows,
        "individual_cell_mean": math.fsum(tv_values) / expected_rows,
        "anchor_reduction": "SYMMETRIC_HALF_PHY_HALF_EDGE",
        "diagnostic_only": True, "included_in_ordered_28": False,
        "own_policy_action_tape_bound": True,
        "top_primitive_action_crossbind_required": True,
        "actor_forward_calls": EVALUATION_EPISODES * HORIZON * 2 * 2,
        "actor_forward_topology": "TWO_POLICIES_PER_ANCHOR_NO_THIRD_ANCHOR_FORWARD",
        "production_token_minted": False,
    }


def crossbind_between_arm_tv_to_native_traces(
    value: Any, *, primitive_shards: Mapping[str, Mapping[str, Any]],
    manifest: Mapping[str, Any], invocation_binding: Mapping[str, Any], adapter: Any,
) -> dict[str, Any]:
    """TEST/component seam for top-index O/action crossbinding; never mints a token."""

    component = validate_between_arm_tv_shard(value, manifest=manifest)
    if not component["available"]:
        if primitive_shards:
            raise B01ContractError("unavailable between-arm cell must not request anchor replay")
        return {**component, "native_trace_crossbind": "NOT_APPLICABLE_NO_RAW_ROWS"}
    if not isinstance(primitive_shards, Mapping) or set(primitive_shards) != set(LEARNED_ARMS):
        raise B01ContractError("between-arm native crossbind requires both anchor primitive shards")
    roster = value["roster"]
    common = (EVALUATION_EPISODES, HORIZON, roster)
    between_observation = _mmap_direct_array(
        value["trace_arrays"]["observation"], dtype="<f4", shape=(*common, 2, 22),
        name="between_arm_crossbind.observation",
    )
    between_action = _mmap_direct_array(
        value["trace_arrays"]["selected_action"], dtype="|u1", shape=(*common, 2),
        name="between_arm_crossbind.selected_action",
    )
    replay_work = {}
    for anchor_index, arm in enumerate(LEARNED_ARMS):
        primitive = primitive_shards[arm]
        if (
            primitive.get("seed_label") != value["seed_label"]
            or primitive.get("checkpoint") != value["checkpoint"]
            or primitive.get("roster") != roster
            or primitive.get("intervention") != value["intervention"]
            or primitive.get("arm") != arm
        ):
            raise B01ContractError("between-arm anchor primitive cell coordinate differs")
        replay = replay_direct_primitive_trace_shard(
            primitive, manifest=manifest, invocation_binding=invocation_binding, adapter=adapter,
        )
        primitive_observation = _mmap_direct_array(
            primitive["arrays"]["observation"], dtype="<f4", shape=(*common, 22),
            name=f"between_arm_crossbind.{arm}.observation",
        )
        primitive_action = _mmap_direct_array(
            primitive["arrays"]["actions"], dtype="|u1", shape=common,
            name=f"between_arm_crossbind.{arm}.action",
        )
        if primitive_observation.tobytes(order="C") != between_observation[
            :, :, :, anchor_index
        ].tobytes(order="C"):
            raise B01ContractError("between-arm anchor observation differs from native factual trace")
        if primitive_action.tobytes(order="C") != between_action[
            :, :, :, anchor_index
        ].tobytes(order="C"):
            raise B01ContractError("between-arm selected action differs from native factual trace")
        replay_work[arm] = replay["validation_replay_work"]
    return {
        **component, "native_trace_crossbind": "EXACT_FULL_ROSTER_OBSERVATION_AND_ACTION",
        "validation_replay_work_by_anchor": replay_work,
        "scientific_work_accounting": "EXCLUDED_POSTHOC_DETERMINISTIC_VALIDATION",
        "production_token_minted": False,
    }


def validate_primitive_row(value: Any, *, seed_labels: set[str], test_only: bool) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _ROW_FIELDS:
        raise B01ContractError("B01 primitive row fields differ")
    row = dict(value)
    if row["seed_label"] not in seed_labels:
        raise B01ContractError("primitive row seed label differs")
    if row["arm"] not in (*LEARNED_ARMS, "UNIFORM_LEGAL"):
        raise B01ContractError("primitive row arm differs")
    if row["roster"] not in EVALUATION_ROSTERS or row["intervention"] not in INTERVENTIONS:
        raise B01ContractError("primitive row cell differs")
    if type(row["episode"]) is not int or not 0 <= row["episode"] < EVALUATION_EPISODES:
        raise B01ContractError("primitive row episode differs")
    if row["arm"] == "UNIFORM_LEGAL":
        if row["checkpoint"] is not None or row["roster"] not in (9, 15) or row["intervention"] != "INTACT":
            raise B01ContractError("UNIFORM_LEGAL must be once per seed at intact N9/N15")
    elif row["checkpoint"] not in CHECKPOINTS:
        raise B01ContractError("learned primitive checkpoint differs")
    tape = row["tape_binding"]
    metadata_checkpoint = 0 if row["checkpoint"] is None else row["checkpoint"]
    if not isinstance(tape, Mapping) or tape != {
        "schema": "FRRIE_B01_EVALUATION_TAPE_V1",
        "seed_label": row["seed_label"], "roster": row["roster"],
        "episode": row["episode"], "checkpoint": metadata_checkpoint,
        "checkpoint_role": "METADATA_ONLY",
        "address_fields": ["seed_label", "roster", "episode", "semantic_variable"],
        "arm_independent": True, "intervention_independent": True,
        "checkpoint_independent": True, "uniform_mapping": "TOP24 / 2**24",
    }:
        raise B01ContractError("primitive row tape binding is not common/addressed")
    for field in ("J", "WASTE"):
        if isinstance(row[field], bool) or not isinstance(row[field], (int, float)) or not math.isfinite(row[field]):
            raise B01ContractError(f"primitive row {field} is nonfinite")
        if not 0.0 <= float(row[field]) <= 1.0:
            raise B01ContractError(f"primitive row {field} is outside [0,1]")
    if (
        type(row["D_W"]) is not int or type(row["D_E"]) is not int
        or not 0 <= row["D_W"] <= 3 or not 0 <= row["D_E"] <= 3
    ):
        raise B01ContractError("primitive delivery counts must be integers")
    expected_j = native_endpoint(row["D_W"], row["D_E"], row["WASTE"])
    if float(row["J"]).hex() != float(expected_j).hex():
        raise B01ContractError("primitive J differs from terminal primitives")
    counts = row["role_action_counts"]
    if (
        not isinstance(counts, list) or len(counts) != 3
        or any(not isinstance(role, list) or len(role) != 6 for role in counts)
        or any(type(item) is not int or item < 0 for role in counts for item in role)
    ):
        raise B01ContractError("role action counts are incomplete")
    role_total = 12 * (row["roster"] // 3)
    legal_by_role = ({0, 1, 5}, {0, 1, 5}, {2, 3, 4, 5})
    for role in range(3):
        if sum(counts[role]) != role_total or any(
            counts[role][action] != 0 for action in range(6) if action not in legal_by_role[role]
        ):
            raise B01ContractError("role action counts violate exact role opportunities")
    for field in (
        "successful_scan", "successful_uplink", "successful_receive",
        "successful_delivery", "expired", "duplicate", "collision", "empty_radio",
    ):
        if type(row[field]) is not int or row[field] < 0:
            raise B01ContractError(f"primitive {field} must be nonnegative integer")
    scan_opportunities = counts[0][0] + counts[1][0]
    uplink_opportunities = counts[0][1] + counts[1][1]
    receive_opportunities = counts[2][2] + counts[2][3]
    radio_opportunities = uplink_opportunities + receive_opportunities + counts[2][4]
    if (
        row["successful_scan"] > scan_opportunities
        or row["successful_uplink"] > uplink_opportunities
        or row["successful_receive"] > receive_opportunities
        or row["successful_delivery"] != row["D_W"] + row["D_E"]
        or row["empty_radio"] > radio_opportunities
    ):
        raise B01ContractError("primitive success/empty counts exceed direct action opportunities")
    return row


def validate_complete_panel(panel: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    manifest0 = validate_manifest(manifest)
    fields = {
        "schema", "manifest_contract", "invocation_binding", "performance_evidence",
        "rows", "training_primitives", "checkpoint_restore_receipts",
        "action_probability_rows", "raw_control_receipt", "complete",
    }
    if not isinstance(panel, Mapping) or set(panel) != fields:
        raise B01ContractError("complete production panel fields differ")
    value = dict(panel)
    if value["schema"] != PANEL_SCHEMA or value["manifest_contract"] != manifest0 or value["complete"] is not True:
        raise B01ContractError("complete production panel identity differs")
    validate_invocation_binding(value["invocation_binding"], require_test_only=False)
    raise B01ContractError(
        "PRODUCTION_PANEL_VALIDATION_UNAVAILABLE/REPAIR_REQUIRED: exact training, "
        "checkpoint-restore, action-probability, support, and 28-quantity inventories are not implemented"
    )


def formal_validate_complete_panel(panel: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Formal runner entry: actual source gate precedes production panel validation."""

    validate_formal_source_gate(manifest)
    return validate_complete_panel(panel, manifest)


def validate_candidate_panel_index_contract(
    panel: Any, manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate top-level create-once locators/cardinalities without minting CLEAN."""

    import json

    manifest0 = validate_manifest(manifest)
    fields = {
        "schema", "manifest_contract", "invocation_inventory",
        "analysis_invocation_binding", "primitive_index",
        "training_index", "checkpoint_index", "ordered_shadow_index",
        "between_arm_index", "quantity_coordinates", "work_ledger",
        "raw_control_receipt", "inventory_cardinalities", "complete",
    }
    if not isinstance(panel, Mapping) or set(panel) != fields:
        raise B01ContractError("candidate panel top-index fields differ")
    value = dict(panel)
    if (
        value["schema"] != "FRRIE_B01_EXACT_PANEL_CANDIDATE_INDEX_V1"
        or value["manifest_contract"] != manifest0 or value["complete"] is not True
    ):
        raise B01ContractError("candidate panel top-index identity differs")
    seeds = manifest0["execution_labels"]
    inventory = value["invocation_inventory"]
    if not isinstance(inventory, Mapping) or set(inventory) != {"schema", "entries"} or inventory[
        "schema"
    ] != "FRRIE_B01_INVOCATION_INVENTORY_V1" or not isinstance(inventory["entries"], list):
        raise B01ContractError("candidate panel invocation inventory fields differ")
    invocation_by_id = {}
    receipt_paths_by_id = {}
    for entry in inventory["entries"]:
        if not isinstance(entry, Mapping) or set(entry) != {"seed_label", "phase", "binding"}:
            raise B01ContractError("candidate panel invocation inventory entry differs")
        if entry["seed_label"] not in seeds or entry["phase"] != manifest0["phase"]:
            raise B01ContractError("candidate panel invocation seed/phase differs")
        binding = validate_invocation_binding(entry["binding"], require_test_only=False)
        invocation_id = binding["invocation_id"]
        if invocation_id in invocation_by_id:
            raise B01ContractError("candidate panel invocation IDs must be unique")
        invocation_by_id[invocation_id] = (entry["seed_label"], binding)
        receipt_path = str(Path(binding["receipt_path"]).resolve(strict=True))
        if receipt_path in receipt_paths_by_id:
            raise B01ContractError(
                "candidate panel each invocation requires its own fresh receipt file"
            )
        receipt_paths_by_id[receipt_path] = invocation_id
    analysis_binding = validate_invocation_binding(
        value["analysis_invocation_binding"], require_test_only=False,
    )
    if analysis_binding["operation"] != "ANALYZE":
        raise B01ContractError("candidate panel analysis invocation operation differs")
    analysis_id = analysis_binding["invocation_id"]
    analysis_receipt = str(Path(analysis_binding["receipt_path"]).resolve(strict=True))
    if analysis_id in invocation_by_id or analysis_receipt in receipt_paths_by_id:
        raise B01ContractError(
            "candidate panel analysis invocation/receipt must be independent"
        )
    if value["inventory_cardinalities"] != exact_inventory_cardinalities(seeds):
        raise B01ContractError("candidate panel inventory cardinalities differ")

    primitive_coordinates = []
    for seed in seeds:
        for checkpoint in CHECKPOINTS:
            for arm in LEARNED_ARMS:
                for roster in EVALUATION_ROSTERS:
                    for intervention in INTERVENTIONS:
                        primitive_coordinates.append((seed, arm, checkpoint, roster, intervention))
        for roster in TRAIN_ROSTERS:
            primitive_coordinates.append((seed, "UNIFORM_LEGAL", None, roster, "INTACT"))
    expected = {
        "primitive_index": primitive_coordinates,
        "training_index": [(seed, arm) for seed in seeds for arm in LEARNED_ARMS],
        "checkpoint_index": list(iter_checkpoint_restore_coordinates(seeds)),
        "ordered_shadow_index": [
            (seed, checkpoint, roster)
            for seed in seeds for checkpoint in CHECKPOINTS for roster in HELDOUT_ROSTERS
        ],
        "between_arm_index": [
            (seed, checkpoint, roster, intervention)
            for seed in seeds for checkpoint in CHECKPOINTS
            for roster in (9, 15, 6, 21) for intervention in INTERVENTIONS
        ],
    }
    coordinate_fields = {
        "primitive_index": ("seed_label", "arm", "checkpoint", "roster", "intervention"),
        "training_index": ("seed_label", "arm"),
        "checkpoint_index": ("seed_label", "checkpoint"),
        "ordered_shadow_index": ("seed_label", "checkpoint", "roster"),
        "between_arm_index": ("seed_label", "checkpoint", "roster", "intervention"),
    }
    allowed_operations = {
        "primitive_index": {"EVALUATE"}, "training_index": {"TRAIN"},
        "checkpoint_index": {"TRAIN", "RESUME"}, "ordered_shadow_index": {"EVALUATE"},
        "between_arm_index": {"EVALUATE"},
    }
    used_invocation_ids = set()
    for name, coordinates in expected.items():
        rows = value[name]
        if not isinstance(rows, list) or len(rows) != len(coordinates):
            raise B01ContractError(f"candidate panel {name} cardinality differs")
        names = coordinate_fields[name]
        for index, (row, coordinate) in enumerate(zip(rows, coordinates)):
            if not isinstance(row, Mapping) or set(row) != {
                *names, "descriptor_path", "invocation_id",
            } or tuple(
                row[field] for field in names
            ) != coordinate:
                raise B01ContractError(f"candidate panel {name} order differs at {index}")
            invocation_id = row["invocation_id"]
            if invocation_id not in invocation_by_id:
                raise B01ContractError(f"candidate panel {name} invocation ID is unregistered")
            invocation_seed, binding = invocation_by_id[invocation_id]
            if invocation_seed != row["seed_label"] or binding["operation"] not in allowed_operations[name]:
                raise B01ContractError(f"candidate panel {name} invocation binding differs")
            used_invocation_ids.add(invocation_id)
            path = Path(row["descriptor_path"])
            if not path.is_absolute():
                raise B01ContractError(f"candidate panel {name} locator must be absolute")
            try:
                descriptor = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise B01ContractError(f"candidate panel {name} descriptor is unreadable") from error
            if not isinstance(descriptor, Mapping) or descriptor.get(
                "invocation_id"
            ) != invocation_id or any(
                descriptor.get(field) != wanted for field, wanted in zip(names, coordinate)
            ):
                raise B01ContractError(f"candidate panel {name} descriptor coordinate differs")
    if used_invocation_ids != set(invocation_by_id):
        raise B01ContractError("candidate panel invocation inventory has missing/unused IDs")
    if value["quantity_coordinates"] != [list(row) for row in iter_quantity_coordinates(seeds)]:
        raise B01ContractError("candidate panel quantity coordinate inventory differs")
    expected_work_rows = []
    for seed in seeds:
        for arm in LEARNED_ARMS:
            expected_work_rows.append({
                "seed_label": seed, "arm": arm,
                "training": {
                    "factual": 393_216, "seven_nonfactual_alternatives": 1_490_944,
                    "three_audits": 638_976, "total": 2_523_136,
                },
                "evaluation": 147_456,
                "raw_native_calls": value["work_ledger"][len(expected_work_rows)].get(
                    "raw_native_calls"
                ) if isinstance(value["work_ledger"], list) and len(
                    value["work_ledger"]
                ) > len(expected_work_rows) and isinstance(
                    value["work_ledger"][len(expected_work_rows)], Mapping
                ) else None,
            })
    if not isinstance(value["work_ledger"], list) or len(value["work_ledger"]) != len(expected_work_rows):
        raise B01ContractError("candidate panel work ledger cardinality differs")
    for observed, wanted in zip(value["work_ledger"], expected_work_rows):
        if not isinstance(observed, Mapping) or set(observed) != set(wanted) or any(
            observed[field] != wanted[field] for field in wanted if field != "raw_native_calls"
        ) or not isinstance(observed["raw_native_calls"], Mapping) or set(
            observed["raw_native_calls"]
        ) != {"reset_calls", "observe_calls", "step_calls"} or any(
            type(count) is not int or count < 0 for count in observed["raw_native_calls"].values()
        ):
            raise B01ContractError("candidate panel work ledger differs")
    validate_raw_control_receipt(value["raw_control_receipt"])
    return {
        **value, "candidate_index_validated": True,
        "component_content_validation_complete": False,
        "production_token_minted": False,
    }


def validate_checkpoint_restore_inventory(
    rows: Any, *, manifest: Mapping[str, Any], seed_labels: Any,
) -> dict[str, Any]:
    """Reopen/decode/paired-restore every literal checkpoint in canonical order."""

    import json
    from .checkpoint import reopen_decode_restore_checkpoint

    labels = _seed_order(seed_labels)
    expected = list(iter_checkpoint_restore_coordinates(labels))
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise B01ContractError("checkpoint restore inventory cardinality differs")
    receipts = []
    for index, (row, coordinate) in enumerate(zip(rows, expected)):
        if not isinstance(row, Mapping) or set(row) != {
            "seed_label", "checkpoint", "descriptor_path",
        } or (row["seed_label"], row["checkpoint"]) != coordinate:
            raise B01ContractError(f"checkpoint restore inventory order differs at {index}")
        descriptor_path = Path(row["descriptor_path"])
        if not descriptor_path.is_absolute():
            raise B01ContractError("checkpoint restore descriptor path must be absolute")
        try:
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise B01ContractError("checkpoint restore descriptor is unreadable") from error
        if not isinstance(descriptor, Mapping) or set(descriptor) != {
            "schema", "seed_label", "checkpoint", "checkpoint_path", "complete",
        } or descriptor != {
            "schema": "FRRIE_B01_CHECKPOINT_LOCATOR_V1",
            "seed_label": coordinate[0], "checkpoint": coordinate[1],
            "checkpoint_path": descriptor.get("checkpoint_path"), "complete": True,
        }:
            raise B01ContractError("checkpoint restore descriptor identity differs")
        receipts.append(reopen_decode_restore_checkpoint(
            descriptor["checkpoint_path"], manifest=manifest,
            seed_label=coordinate[0], update=coordinate[1],
        ))
    return {
        "schema": "FRRIE_B01_CHECKPOINT_RESTORE_INVENTORY_V1",
        "seed_order": list(labels), "checkpoint_order": list(CHECKPOINTS),
        "receipts": receipts, "receipt_count": len(receipts),
        "complete": True, "production_token_minted": False,
    }


def validate_test_panel(panel: Any, manifest: Mapping[str, Any]) -> dict[str, Any]:
    manifest0 = validate_test_manifest(manifest)
    fields = {"schema", "manifest_contract", "invocation_binding", "rows", "complete"}
    if not isinstance(panel, Mapping) or set(panel) != fields:
        raise B01ContractError("TEST panel fields differ")
    value = dict(panel)
    if value["schema"] != "FRRIE_B01_TEST_ONLY_PANEL_V1" or value["manifest_contract"] != manifest0 or value["complete"] is not True:
        raise B01ContractError("TEST panel identity differs")
    validate_invocation_binding(value["invocation_binding"], require_test_only=True)
    if not isinstance(value["rows"], list) or not value["rows"]:
        raise B01ContractError("TEST panel needs direct primitive rows")
    for row in value["rows"]:
        validate_primitive_row(row, seed_labels={manifest0["seed_label"]}, test_only=True)
    return value
