"""TEST-only streaming fixtures for the exact B01 direct-training shard axes.

The sparse mode creates exact-size descriptor fixtures without pretending that
zero-filled holes are a replayable training result.  Dense mode accepts one
fully typed row at a time, validates its direct row laws, and writes its bytes
without accumulating a 512-update Python object.  Neither mode is a launch or
production surface, and neither self-certifies the authoritative full-shard
validator.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from itertools import zip_longest
from typing import Any, Iterable, Mapping

import numpy as np

from ..arms import LAYER_SHAPES, PARAMETER_BYTE_COUNT, PROJECTION_BOXES, LearnedArm
from ..contracts.core import ContractError
from ..state_codec import OPTIMIZER_STATE_BYTE_COUNT, decode_optimizer_state
from ..training import exact_loss_reduction_contract, validate_loss_reduction_receipt
from .constants import (
    CHECKPOINTS,
    LEARNED_ARMS,
    TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED,
    TRAIN_AUDIT_WORK_PER_ARM_SEED,
    TRAIN_FACTUAL_WORK_PER_ARM_SEED,
    TRAIN_TOTAL_WORK_PER_ARM_SEED,
    UPDATES,
)
from .contract import B01ContractError
from .contract import canonical_json_bytes


SYNTHETIC_COMPONENT_ONLY = "SYNTHETIC_COMPONENT_ONLY"


@dataclass(frozen=True, slots=True)
class SyntheticTrainingRow:
    """One dense update row; values are exact C-order raw bytes."""

    update: int
    array_shards: Mapping[str, bytes]
    state_blobs: Mapping[str, bytes]


@dataclass(frozen=True, slots=True)
class SyntheticSparseTrainingRow:
    """Only an update coordinate; sparse fixtures contain no valid payload."""

    update: int


@dataclass(frozen=True, slots=True)
class ActualDirectTrainingRow:
    """One runner-produced row with typed common exogenous provenance."""

    update: int
    arm: str
    array_shards: Mapping[str, bytes]
    state_blobs: Mapping[str, bytes]
    typed_exogenous_receipts: tuple[Mapping[str, Any], ...]


def _typed_common_exogenous_receipt(value: Any) -> dict[str, Any]:
    """Retain semantic tape/address fields; never collapse them to one opaque blob."""

    from .trainer import DirectExogenousEpisode

    if type(value) is not DirectExogenousEpisode:
        raise B01ContractError("actual row exogenous receipt is not direct/token-produced")
    return {
        "update": value.update, "position": value.position, "roster": value.roster,
        "tape_bytes": value.tape_bytes, "tape_coordinate": value.tape_coordinate,
        "law_revisions": value.law_revisions,
        "relations_bytes": value.relations_bytes,
        "relations_shape": value.relations_shape,
        "relations_dtype": value.relations_dtype,
        "masks_bytes": value.masks_bytes, "masks_shape": value.masks_shape,
        "masks_dtype": value.masks_dtype,
        "origin_coordinates": value.origin_coordinates,
        "origin_addresses": value.origin_addresses,
    }


def actual_direct_training_row(
    *, receipt: Any, batch: Any, collection_audit: Any,
) -> ActualDirectTrainingRow:
    """Convert only actual collector/trainer objects into one direct shard row."""

    from .batch_collector import BatchCollectionAudit
    from .native_batch import BatchWorkLedger
    from .trainer import ArmUpdateReceipt, B01ArmBatch

    if type(receipt) is not ArmUpdateReceipt or type(batch) is not B01ArmBatch or type(
        collection_audit
    ) is not BatchCollectionAudit:
        raise B01ContractError("actual direct row requires typed trainer/collector receipts")
    update = receipt.update
    arm = receipt.arm
    if arm not in LEARNED_ARMS or collection_audit.update != update:
        raise B01ContractError("actual direct row arm/update coordinate differs")
    batch.validate(update=update)
    if any(type(item) is not BatchWorkLedger for item in batch.collection_ledgers):
        raise B01ContractError("actual direct row native ledger is not token-produced")
    if (
        collection_audit.factual_slots != 768
        or collection_audit.nonfactual_suffix_slots != 2_912
        or collection_audit.factual_suffix_audit_slots != 1_248
        or collection_audit.total_environment_slots != 4_928
        or collection_audit.factual_trace_direct_equal is not True
        or collection_audit.model_bytes_unchanged is not True
    ):
        raise B01ContractError("actual direct row collection work/audit differs")
    reduction = receipt.loss_reduction_receipt
    if (
        reduction.schema != "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1"
        or len(reduction.per_episode_u32_bits) != 64
        or len(reduction.aggregate_u32_bits) != 4
    ):
        raise B01ContractError("actual direct row loss reduction receipt differs")
    blobs = {
        "model_pre": receipt.model_pre_bytes,
        "model_post_adam": receipt.model_post_adam_bytes,
        "model_post_projection": receipt.model_post_projection_bytes,
        "optimizer_pre": receipt.optimizer_pre_bytes,
        "optimizer_post_adam": receipt.optimizer_post_adam_bytes,
        "optimizer_post_projection": receipt.optimizer_post_projection_bytes,
    }
    beta_offset = 0
    for name, shape in LAYER_SHAPES:
        if name == "beta":
            break
        beta_offset += 4 * math.prod(shape)
    beta_stop = beta_offset + 18 * 4
    changed = np.zeros(18, dtype="|u1")
    changed[list(receipt.projection_changed_indices)] = 1
    native_calls = np.asarray([
        sum(item.native_reset_calls for item in batch.collection_ledgers),
        sum(item.native_observe_calls for item in batch.collection_ledgers),
        sum(item.native_step_calls for item in batch.collection_ledgers),
    ], dtype="<u4")
    arrays = {
        "beta_pre_bits": blobs["model_pre"][beta_offset:beta_stop],
        "beta_post_adam_bits": blobs["model_post_adam"][beta_offset:beta_stop],
        "beta_post_projection_bits": blobs["model_post_projection"][beta_offset:beta_stop],
        "loss_terms": np.asarray([
            receipt.loss, receipt.score, receipt.entropy, receipt.critic,
            receipt.preclip_global_norm,
        ], dtype="<f4").tobytes(),
        "loss_episode_component_bits": np.asarray(
            reduction.per_episode_u32_bits, dtype="<u4",
        ).tobytes(order="C"),
        "loss_aggregate_bits": np.asarray(
            reduction.aggregate_u32_bits, dtype="<u4",
        ).tobytes(order="C"),
        "changed_mask": changed.tobytes(),
        "box_contact": np.asarray(receipt.box_contact, dtype="|u1").tobytes(),
        "maximum_box_overshoot": np.asarray(
            receipt.maximum_box_overshoot, dtype="<f8",
        ).tobytes(),
        "projection_l1_displacement": np.asarray(
            receipt.projection_displacement, dtype="<f8",
        ).tobytes(),
        "optimizer_moments_unchanged": np.asarray(
            receipt.optimizer_moments_unchanged_by_projection, dtype="|u1",
        ).tobytes(),
        "work": np.asarray([768, 2_912, 1_248, 4_928], dtype="<u4").tobytes(),
        "raw_native_calls": native_calls.tobytes(),
    }
    contract = direct_training_row_contract()
    _exact_row_bytes(arrays, contract["array_shards"], group="actual array shard")
    _exact_row_bytes(blobs, contract["state_blobs"], group="actual state blob")
    return ActualDirectTrainingRow(
        update=update, arm=arm, array_shards=arrays, state_blobs=blobs,
        typed_exogenous_receipts=tuple(
            _typed_common_exogenous_receipt(row) for row in batch.exogenous_receipts
        ),
    )


def validate_actual_paired_direct_rows(
    rows: Mapping[str, ActualDirectTrainingRow],
    *, expected_update: int, expected_seed_label: str,
    expected_root: bytes,
) -> dict[str, Any]:
    """Validate each semantic receipt canonically, then compare paired inputs."""

    if not isinstance(rows, Mapping) or set(rows) != set(LEARNED_ARMS) or any(
        type(rows[arm]) is not ActualDirectTrainingRow or rows[arm].arm != arm
        for arm in LEARNED_ARMS
    ):
        raise B01ContractError("actual paired direct row inventory differs")
    left, right = (rows[arm] for arm in LEARNED_ARMS)
    if left.update != right.update or left.update != expected_update:
        raise B01ContractError("actual paired direct row update differs")
    if not isinstance(expected_seed_label, str) or not expected_seed_label.startswith("FRRIE-"):
        raise B01ContractError("actual paired direct row expected seed label differs")

    fields = {
        "update", "position", "roster", "tape_bytes", "tape_coordinate",
        "law_revisions", "relations_bytes", "relations_shape", "relations_dtype",
        "masks_bytes", "masks_shape", "masks_dtype", "origin_coordinates",
        "origin_addresses",
    }
    law_revisions = (
        "RIDGEGATE_2Z_NATIVE_STEP_ABI_V2", "OBSERVATION_22_V1",
        "K0_RELATION_FUNCTION_V1", "ROLE_LEGAL_MASK_FUNCTION_V1",
    )
    from ..policy import LEGAL_ACTION_INDICES

    def validate_receipts(values: tuple[Mapping[str, Any], ...]) -> None:
        if len(values) != 64:
            raise B01ContractError("actual paired direct row requires 64 typed receipts")
        for position, value in enumerate(values):
            roster = 9 if position % 2 == 0 else 15
            episode = position // 2
            if not isinstance(value, Mapping) or set(value) != fields or (
                value["update"], value["position"], value["roster"]
            ) != (left.update, position, roster) or value["tape_coordinate"] != (
                expected_seed_label, "TRAIN", roster, left.update, episode,
            ) or value["law_revisions"] != law_revisions:
                raise B01ContractError("actual typed tape coordinate/law differs")
            expected_tape_bytes = (
                2 * 3 * 8 + 12 * 2 * (roster // 3) * 4
                + 12 * roster * roster * 4 + 12 * roster * 4 + 12 * roster * 4
            )
            roles = np.repeat(np.arange(3, dtype=np.int64), roster // 3)
            masks = np.zeros((12, roster, 6), dtype=np.bool_)
            for entity, role in enumerate(roles):
                masks[:, entity, list(LEGAL_ACTION_INDICES[int(role)])] = True
            if (
                type(value["tape_bytes"]) is not bytes
                or len(value["tape_bytes"]) != expected_tape_bytes
                or value["relations_shape"] != (roster,)
                or value["relations_dtype"] != "int64"
                or value["relations_bytes"] != roles.tobytes(order="C")
                or value["masks_shape"] != (12, roster, 6)
                or value["masks_dtype"] != "bool"
                or value["masks_bytes"] != masks.tobytes(order="C")
            ):
                raise B01ContractError("actual typed tape/role/mask payload differs")
            origins = value["origin_coordinates"]
            if (
                not isinstance(origins, tuple) or len(origins) != 3
                or tuple(item[0] for item in origins) != (0, 1, 2)
                or any(
                    not isinstance(item, tuple) or len(item) != 3
                    or not 0 <= item[1] < 12 or not 0 <= item[2] < roster
                    or int(roles[item[2]]) != item[0]
                    for item in origins
                )
            ):
                raise B01ContractError("actual typed origin coordinates differ")
            expected_addresses = tuple(canonical_json_bytes({
                "schema": "FRRIE_B01_ORIGIN_ADDRESS_V1",
                "seed_block": expected_seed_label, "update": left.update,
                "batch_position": position, "roster": roster,
                "role": role, "slot": slot, "entity": entity,
            }) for role, slot, entity in origins)
            if value["origin_addresses"] != expected_addresses:
                raise B01ContractError("actual typed canonical origin addresses differ")

    validate_receipts(left.typed_exogenous_receipts)
    validate_receipts(right.typed_exogenous_receipts)
    if left.typed_exogenous_receipts != right.typed_exogenous_receipts:
        raise B01ContractError("actual paired direct row typed tape/address receipts differ")
    from .batch_collector import make_test_update_inputs

    tapes, origins = make_test_update_inputs(
        expected_root, seed_label=expected_seed_label, update=expected_update,
    )
    for position, (value, tape, origin_rows) in enumerate(zip(
        left.typed_exogenous_receipts, tapes, origins,
    )):
        expected_tape = b"".join(getattr(tape, field).tobytes(order="C") for field in (
            "event_times", "detection_uniform", "uplink_uniform",
            "base_uniform", "action_uniform",
        ))
        expected_origins = tuple(
            (row.role, row.slot, row.entity) for row in origin_rows
        )
        if (
            value["position"] != position
            or value["tape_bytes"] != expected_tape
            or value["origin_coordinates"] != expected_origins
        ):
            raise B01ContractError(
                "actual paired direct row differs from root-regenerated canonical input"
            )
    for name in ("work", "raw_native_calls"):
        if left.array_shards[name] != right.array_shards[name]:
            raise B01ContractError(f"actual paired direct row {name} differs")
    return {
        "schema": "FRRIE_B01_ACTUAL_PAIRED_DIRECT_ROW_V1",
        "update": left.update, "typed_tape_address_equal": True,
        "native_work_equal": True, "outcome_equality_required": False,
        "test_component_only": True, "production_token": False,
    }


def validate_actual_direct_row_chain_step(
    row: ActualDirectTrainingRow, *, expected_update: int,
    previous_model_post_projection: bytes,
    previous_optimizer_post_projection: bytes,
) -> dict[str, Any]:
    """Validate one actual row's frontier and direct state chain in constant memory."""

    if type(row) is not ActualDirectTrainingRow or row.update != expected_update:
        raise B01ContractError("actual direct row stream update differs")
    contract = direct_training_row_contract()
    arrays = _exact_row_bytes(
        row.array_shards, contract["array_shards"], group="actual array shard",
    )
    blobs = _exact_row_bytes(
        row.state_blobs, contract["state_blobs"], group="actual state blob",
    )
    if (
        blobs["model_pre"] != previous_model_post_projection
        or blobs["optimizer_pre"] != previous_optimizer_post_projection
    ):
        raise B01ContractError("actual direct row stream prestate differs")
    if (
        decode_optimizer_state(blobs["optimizer_pre"]).step != expected_update - 1
        or decode_optimizer_state(blobs["optimizer_post_adam"]).step != expected_update
        or decode_optimizer_state(blobs["optimizer_post_projection"]).step != expected_update
        or blobs["optimizer_post_adam"] != blobs["optimizer_post_projection"]
    ):
        raise B01ContractError("actual direct row stream optimizer frontier differs")
    try:
        for name in ("model_pre", "model_post_adam", "model_post_projection"):
            LearnedArm.from_parameter_bytes(row.arm, blobs[name])
    except ContractError as error:
        raise B01ContractError("actual direct row stream model bytes differ") from error
    beta_offset = 0
    for name, shape in LAYER_SHAPES:
        if name == "beta":
            break
        beta_offset += 4 * math.prod(shape)
    beta_stop = beta_offset + 18 * 4
    pre_bits = np.frombuffer(blobs["model_pre"][beta_offset:beta_stop], dtype="<u4")
    adam_bits = np.frombuffer(blobs["model_post_adam"][beta_offset:beta_stop], dtype="<u4")
    projected_bits = np.frombuffer(
        blobs["model_post_projection"][beta_offset:beta_stop], dtype="<u4",
    )
    if (
        arrays["beta_pre_bits"] != pre_bits.tobytes()
        or arrays["beta_post_adam_bits"] != adam_bits.tobytes()
        or arrays["beta_post_projection_bits"] != projected_bits.tobytes()
    ):
        raise B01ContractError("actual direct row stream beta bits differ")
    before = adam_bits.view("<f4")
    after = projected_bits.view("<f4")
    low, high = PROJECTION_BOXES[row.arm]
    wanted = np.clip(before, np.float32(low), np.float32(high)).astype("<f4")
    changed = adam_bits != projected_bits
    if (
        wanted.tobytes() != after.tobytes()
        or arrays["changed_mask"] != changed.astype("|u1").tobytes()
        or arrays["box_contact"] != np.asarray(changed.any(), dtype="|u1").tobytes()
        or blobs["model_post_adam"][:beta_offset]
        + blobs["model_post_adam"][beta_stop:]
        != blobs["model_post_projection"][:beta_offset]
        + blobs["model_post_projection"][beta_stop:]
    ):
        raise B01ContractError("actual direct row stream projection bytes differ")
    overshoot = max(
        max((float(low) - float(item) for item in before), default=0.0),
        max((float(item) - float(high) for item in before), default=0.0), 0.0,
    )
    displacement = math.fsum(abs(float(a) - float(b)) for a, b in zip(after, before))
    if (
        float(np.frombuffer(arrays["maximum_box_overshoot"], dtype="<f8")[0]).hex()
        != float(overshoot).hex()
        or float(np.frombuffer(arrays["projection_l1_displacement"], dtype="<f8")[0]).hex()
        != float(displacement).hex()
        or arrays["optimizer_moments_unchanged"] != b"\x01"
    ):
        raise B01ContractError("actual direct row stream projection scalars differ")
    terms = np.frombuffer(arrays["loss_terms"], dtype="<f4")
    if not np.isfinite(terms).all():
        raise B01ContractError("actual direct row stream loss scalars are nonfinite")
    reduction = {
        "schema": "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
        "component_order": ["loss", "score", "entropy", "critic"],
        "roster_order": exact_loss_reduction_contract()["roster_order"],
        "per_episode_u32_bits": np.frombuffer(
            arrays["loss_episode_component_bits"], dtype="<u4",
        ).reshape(64, 4).tolist(),
        "reduction_law": exact_loss_reduction_contract()["reduction_law"],
        "divisor": 64, "dtype": "CPU_FP32",
        "aggregate_u32_bits": np.frombuffer(
            arrays["loss_aggregate_bits"], dtype="<u4",
        ).tolist(),
    }
    try:
        validate_loss_reduction_receipt(
            reduction,
            aggregate_scalars={
                name: float(terms[index])
                for index, name in enumerate(("loss", "score", "entropy", "critic"))
            },
        )
    except ContractError as error:
        raise B01ContractError("actual direct row stream loss bits differ") from error
    if arrays["work"] != np.asarray([768, 2_912, 1_248, 4_928], dtype="<u4").tobytes():
        raise B01ContractError("actual direct row stream work partition differs")
    native = np.frombuffer(arrays["raw_native_calls"], dtype="<u4")
    if not native.any():
        raise B01ContractError("actual direct row stream native ledger is empty")
    return {
        "schema": "FRRIE_B01_ACTUAL_DIRECT_ROW_CHAIN_STEP_V1",
        "update": expected_update, "arm": row.arm,
        "next_model_bytes": blobs["model_post_projection"],
        "next_optimizer_bytes": blobs["optimizer_post_projection"],
        "direct_state_chain_validated": True, "native_work_nonempty": True,
        "test_component_only": True, "production_token": False,
    }


@dataclass(frozen=True, slots=True)
class SyntheticPairedResumeRow:
    """One paired TEST replay row plus its common direct tape/address bytes."""

    update: int
    address_tape_receipt_bytes: bytes
    arm_rows: Mapping[str, SyntheticTrainingRow]


def validate_synthetic_resume_suffix_fixture(
    *, checkpoint: int,
    checkpoint_states: Mapping[str, Mapping[str, bytes]],
    uninterrupted_rows: Iterable[SyntheticPairedResumeRow],
    resumed_rows: Iterable[SyntheticPairedResumeRow],
) -> dict[str, Any]:
    """Directly compare one complete TEST/component resume suffix.

    This validator closes the static coverage seam only.  It requires every
    update after the selected checkpoint, validates each dense row and its
    state chain, and compares the uninterrupted/resumed row and common
    tape/address bytes directly.  Checkpoint 512 has an empty suffix, so this
    function reports no state-chain or codec/restore validation there; that
    evidence must come from the separate literal checkpoint inventory.  It
    never upgrades synthetic evidence into an authoritative full-512 training
    or launch claim.
    """

    if type(checkpoint) is not int or checkpoint not in CHECKPOINTS:
        raise B01ContractError("synthetic resume checkpoint lies outside the B01 curve")
    state_fields = {"model_state_bytes", "optimizer_state_bytes"}
    if not isinstance(checkpoint_states, Mapping) or set(checkpoint_states) != set(
        LEARNED_ARMS
    ):
        raise B01ContractError("synthetic resume checkpoint state requires both arms")
    initial: dict[str, tuple[bytes, bytes]] = {}
    for arm in LEARNED_ARMS:
        state = checkpoint_states[arm]
        if not isinstance(state, Mapping) or set(state) != state_fields:
            raise B01ContractError("synthetic resume checkpoint state fields differ")
        model = state["model_state_bytes"]
        optimizer = state["optimizer_state_bytes"]
        if type(model) is not bytes or type(optimizer) is not bytes:
            raise B01ContractError("synthetic resume checkpoint state must be direct bytes")
        initial[arm] = (model, optimizer)

    previous = {
        stream: {arm: initial[arm] for arm in LEARNED_ARMS}
        for stream in ("uninterrupted", "resumed")
    }
    missing = object()
    count = 0
    for expected_update, pair in enumerate(
        zip_longest(uninterrupted_rows, resumed_rows, fillvalue=missing),
        start=checkpoint + 1,
    ):
        left, right = pair
        if left is missing or right is missing:
            raise B01ContractError("synthetic resume suffix stream lengths differ")
        if expected_update > UPDATES:
            raise B01ContractError("synthetic resume suffix extends beyond update 512")
        for row in (left, right):
            if (
                not isinstance(row, SyntheticPairedResumeRow)
                or row.update != expected_update
                or type(row.address_tape_receipt_bytes) is not bytes
                or not row.address_tape_receipt_bytes
                or not isinstance(row.arm_rows, Mapping)
                or set(row.arm_rows) != set(LEARNED_ARMS)
            ):
                raise B01ContractError("synthetic resume suffix row contract differs")
        if left.address_tape_receipt_bytes != right.address_tape_receipt_bytes:
            raise B01ContractError("synthetic resume suffix address/tape bytes differ")
        for arm in LEARNED_ARMS:
            if left.arm_rows[arm] != right.arm_rows[arm]:
                raise B01ContractError("synthetic resume suffix direct arm row bytes differ")
            for stream, row in (("uninterrupted", left), ("resumed", right)):
                prior_model, prior_optimizer = previous[stream][arm]
                validated = validate_synthetic_training_row(
                    row.arm_rows[arm], arm=arm,
                    previous_model_post_projection=prior_model,
                    previous_optimizer_post_projection=prior_optimizer,
                )
                previous[stream][arm] = (
                    validated["next_model_bytes"], validated["next_optimizer_bytes"],
                )
        count += 1
    expected_count = UPDATES - checkpoint
    if count != expected_count:
        raise B01ContractError("synthetic resume suffix does not cover the exact update range")
    return {
        "schema": "FRRIE_B01_SYNTHETIC_RESUME_SUFFIX_COMPONENT_V1",
        "role": SYNTHETIC_COMPONENT_ONLY,
        "checkpoint": checkpoint,
        "first_update": checkpoint + 1 if checkpoint < UPDATES else None,
        "last_update": UPDATES if checkpoint < UPDATES else None,
        "update_count": count,
        "direct_state_work_loss_bytes_equal": True,
        "common_address_tape_bytes_equal": True,
        "checkpoint_state_direct_bytes_supplied": True,
        "checkpoint_codec_or_restore_validated": False,
        "state_chain_from_checkpoint_validated": count > 0,
        "terminal_empty_suffix_only": checkpoint == UPDATES,
        "authoritative_full512_validation_complete": False,
        "training_validation_replay_complete": False,
        "production_token": False,
    }


def direct_training_row_contract() -> dict[str, dict[str, tuple[str, tuple[int, ...]]]]:
    """Return the per-update form of ``validate_direct_training_shard`` axes."""

    return {
        "array_shards": {
            "beta_pre_bits": ("<u4", (18,)),
            "beta_post_adam_bits": ("<u4", (18,)),
            "beta_post_projection_bits": ("<u4", (18,)),
            "loss_terms": ("<f4", (5,)),
            "loss_episode_component_bits": ("<u4", (64, 4)),
            "loss_aggregate_bits": ("<u4", (4,)),
            "changed_mask": ("|u1", (18,)),
            "box_contact": ("|u1", ()),
            "maximum_box_overshoot": ("<f8", ()),
            "projection_l1_displacement": ("<f8", ()),
            "optimizer_moments_unchanged": ("|u1", ()),
            "work": ("<u4", (4,)),
            "raw_native_calls": ("<u4", (3,)),
        },
        "state_blobs": {
            "model_pre": ("|u1", (PARAMETER_BYTE_COUNT,)),
            "model_post_adam": ("|u1", (PARAMETER_BYTE_COUNT,)),
            "model_post_projection": ("|u1", (PARAMETER_BYTE_COUNT,)),
            "optimizer_pre": ("|u1", (OPTIMIZER_STATE_BYTE_COUNT,)),
            "optimizer_post_adam": ("|u1", (OPTIMIZER_STATE_BYTE_COUNT,)),
            "optimizer_post_projection": ("|u1", (OPTIMIZER_STATE_BYTE_COUNT,)),
        },
    }


def _exact_row_bytes(
    values: Mapping[str, bytes],
    contract: Mapping[str, tuple[str, tuple[int, ...]]],
    *,
    group: str,
) -> dict[str, bytes]:
    if not isinstance(values, Mapping) or set(values) != set(contract):
        raise B01ContractError(f"synthetic training {group} inventory differs")
    result: dict[str, bytes] = {}
    for name, (dtype, shape) in contract.items():
        value = values[name]
        expected = math.prod(shape) * np.dtype(dtype).itemsize
        if type(value) is not bytes or len(value) != expected:
            raise B01ContractError(
                f"synthetic training {group} {name} exact byte length differs"
            )
        result[name] = value
    return result


def _array(data: bytes, dtype: str, shape: tuple[int, ...]) -> np.ndarray:
    return np.frombuffer(data, dtype=dtype).reshape(shape, order="C")


def validate_synthetic_training_row(
    row: Any,
    *,
    arm: str,
    previous_model_post_projection: bytes | None = None,
    previous_optimizer_post_projection: bytes | None = None,
) -> dict[str, Any]:
    """Validate the direct laws of one dense synthetic update row.

    This is intentionally a component check, not a substitute for the canonical
    512-row ``validate_direct_training_shard`` replay.
    """

    if not isinstance(row, SyntheticTrainingRow):
        raise B01ContractError("synthetic fixture requires one typed dense row")
    if arm not in LEARNED_ARMS:
        raise B01ContractError("synthetic training arm differs")
    if type(row.update) is not int or not 1 <= row.update <= UPDATES:
        raise B01ContractError("synthetic training update coordinate differs")
    if (previous_model_post_projection is None) != (
        previous_optimizer_post_projection is None
    ):
        raise B01ContractError(
            "previous model and optimizer chain inputs must be both absent or both present"
        )
    contract = direct_training_row_contract()
    arrays_raw = _exact_row_bytes(
        row.array_shards, contract["array_shards"], group="array shard",
    )
    blobs = _exact_row_bytes(row.state_blobs, contract["state_blobs"], group="state blob")
    if previous_model_post_projection is not None and (
        blobs["model_pre"] != previous_model_post_projection
        or blobs["optimizer_pre"] != previous_optimizer_post_projection
    ):
        raise B01ContractError("synthetic training consecutive state chain differs")

    try:
        for name in ("model_pre", "model_post_adam", "model_post_projection"):
            LearnedArm.from_parameter_bytes(arm, blobs[name])
        optimizer_pre = decode_optimizer_state(blobs["optimizer_pre"])
        optimizer_adam = decode_optimizer_state(blobs["optimizer_post_adam"])
        optimizer_projected = decode_optimizer_state(blobs["optimizer_post_projection"])
    except ContractError as error:
        raise B01ContractError("synthetic training state bytes differ") from error
    if (
        optimizer_pre.step != row.update - 1
        or optimizer_adam.step != row.update
        or optimizer_projected.step != row.update
    ):
        raise B01ContractError("synthetic training Adam step frontier differs")
    optimizer_unchanged = _array(
        arrays_raw["optimizer_moments_unchanged"], "|u1", (),
    ).item()
    if (
        blobs["optimizer_post_adam"] != blobs["optimizer_post_projection"]
        or int(optimizer_unchanged) != 1
    ):
        raise B01ContractError("synthetic projection changed Adam moment bytes")

    beta_offset = 0
    for name, shape in LAYER_SHAPES:
        if name == "beta":
            break
        beta_offset += 4 * math.prod(shape)
    beta_stop = beta_offset + 18 * 4
    beta_by_stage = {
        name: np.frombuffer(blobs[name][beta_offset:beta_stop], dtype="<u4")
        for name in ("model_pre", "model_post_adam", "model_post_projection")
    }
    for stage, array_name in (
        ("model_pre", "beta_pre_bits"),
        ("model_post_adam", "beta_post_adam_bits"),
        ("model_post_projection", "beta_post_projection_bits"),
    ):
        if not np.array_equal(
            beta_by_stage[stage], _array(arrays_raw[array_name], "<u4", (18,)),
        ):
            raise B01ContractError("synthetic training beta literal bits differ")
    before = beta_by_stage["model_post_adam"].view("<f4")
    after = beta_by_stage["model_post_projection"].view("<f4")
    low, high = PROJECTION_BOXES[arm]
    wanted = np.clip(before, np.float32(low), np.float32(high)).astype("<f4")
    if wanted.tobytes() != after.tobytes():
        raise B01ContractError("synthetic training projection differs from exact box clip")
    if (
        blobs["model_post_adam"][:beta_offset]
        + blobs["model_post_adam"][beta_stop:]
        != blobs["model_post_projection"][:beta_offset]
        + blobs["model_post_projection"][beta_stop:]
    ):
        raise B01ContractError("synthetic projection changed non-beta model bytes")
    changed = (beta_by_stage["model_post_adam"] != beta_by_stage["model_post_projection"])
    changed_recorded = _array(arrays_raw["changed_mask"], "|u1", (18,))
    contact_recorded = int(_array(arrays_raw["box_contact"], "|u1", ()).item())
    if not np.array_equal(changed.astype(np.uint8), changed_recorded) or (
        contact_recorded != int(changed.any())
    ):
        raise B01ContractError("synthetic training projection contact mask differs")
    overshoot = max(
        max((float(low) - float(item) for item in before), default=0.0),
        max((float(item) - float(high) for item in before), default=0.0),
        0.0,
    )
    displacement = math.fsum(abs(float(a) - float(b)) for a, b in zip(after, before))
    stored_overshoot = float(
        _array(arrays_raw["maximum_box_overshoot"], "<f8", ()).item()
    )
    stored_displacement = float(
        _array(arrays_raw["projection_l1_displacement"], "<f8", ()).item()
    )
    if stored_overshoot.hex() != float(overshoot).hex() or (
        stored_displacement.hex() != float(displacement).hex()
    ):
        raise B01ContractError("synthetic training projection movement scalars differ")

    terms = _array(arrays_raw["loss_terms"], "<f4", (5,))
    if not np.isfinite(terms).all():
        raise B01ContractError("synthetic training loss scalars are nonfinite")
    reduction_contract = exact_loss_reduction_contract()
    reduction = {
        "schema": "FRRIE_RSCF_LOSS_REDUCTION_RECEIPT_V1",
        "component_order": ["loss", "score", "entropy", "critic"],
        "roster_order": reduction_contract["roster_order"],
        "per_episode_u32_bits": _array(
            arrays_raw["loss_episode_component_bits"], "<u4", (64, 4),
        ).tolist(),
        "reduction_law": reduction_contract["reduction_law"],
        "divisor": 64,
        "dtype": "CPU_FP32",
        "aggregate_u32_bits": _array(
            arrays_raw["loss_aggregate_bits"], "<u4", (4,),
        ).tolist(),
    }
    try:
        validate_loss_reduction_receipt(
            reduction,
            aggregate_scalars={
                name: float(terms[position])
                for position, name in enumerate(("loss", "score", "entropy", "critic"))
            },
        )
    except ContractError as error:
        raise B01ContractError("synthetic training loss reduction provenance differs") from error
    work = _array(arrays_raw["work"], "<u4", (4,))
    if not np.array_equal(work, np.asarray([768, 2_912, 1_248, 4_928], dtype="<u4")):
        raise B01ContractError("synthetic training per-update work partition differs")
    return {
        "schema": "FRRIE_B01_SYNTHETIC_TRAINING_ROW_VALIDATED_V1",
        "role": SYNTHETIC_COMPONENT_ONLY,
        "update": row.update,
        "next_model_bytes": blobs["model_post_projection"],
        "next_optimizer_bytes": blobs["optimizer_post_projection"],
        "production_token": False,
        "training_validation_replay_complete": False,
    }


def _work_contract() -> dict[str, Any]:
    return {
        "per_update": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED // UPDATES,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED // UPDATES,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED // UPDATES,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED // UPDATES,
        },
        "per_arm_seed": {
            "factual": TRAIN_FACTUAL_WORK_PER_ARM_SEED,
            "seven_nonfactual_alternatives": TRAIN_ALTERNATIVE_WORK_PER_ARM_SEED,
            "three_audits": TRAIN_AUDIT_WORK_PER_ARM_SEED,
            "total": TRAIN_TOTAL_WORK_PER_ARM_SEED,
        },
        "raw_native_call_counts": "RECORDED_NOT_FROZEN",
    }


def write_synthetic_training_fixture(
    rows: Iterable[SyntheticTrainingRow | SyntheticSparseTrainingRow],
    *,
    directory: str | os.PathLike[str],
    seed_label: str,
    arm: str,
    sparse: bool,
    production: bool = False,
    launch: bool = False,
) -> dict[str, Any]:
    """Write an exact-axis TEST fixture while buffering no more than one row.

    ``sparse=True`` consumes only update coordinates, then sizes raw files to
    the canonical axes.  Those holes are deliberately not replayable state.
    ``sparse=False`` requires dense typed rows and writes each raw row directly.
    Its row checks remain component-local; the caller must separately submit
    the descriptors to the authoritative full-512 validator.
    """

    if not isinstance(seed_label, str) or not seed_label.startswith("TEST-"):
        raise B01ContractError("synthetic training fixture requires a TEST seed")
    if arm not in LEARNED_ARMS:
        raise B01ContractError("synthetic training fixture arm differs")
    if production is not False or launch is not False:
        raise B01ContractError("synthetic training fixture is never production or launch")
    if type(sparse) is not bool:
        raise B01ContractError("synthetic training sparse selector must be bool")
    root = Path(directory)
    if not root.is_absolute() or not root.is_dir():
        raise B01ContractError("synthetic training directory must already exist and be absolute")
    root = root.resolve()
    contract = direct_training_row_contract()
    paths = {
        group: {name: root / f"{group}__{name}.raw" for name in entries}
        for group, entries in contract.items()
    }
    if any(path.exists() for entries in paths.values() for path in entries.values()):
        raise B01ContractError("synthetic training fixture output already exists")

    handles: dict[tuple[str, str], Any] = {}
    created: list[Path] = []
    previous_model = previous_optimizer = None
    count = 0
    try:
        for group, entries in paths.items():
            for name, path in entries.items():
                handles[(group, name)] = path.open("xb")
                created.append(path)
        for count, row in enumerate(rows, start=1):
            if count > UPDATES:
                raise B01ContractError("synthetic training fixture requires exactly 512 rows")
            if not isinstance(row, (SyntheticSparseTrainingRow, SyntheticTrainingRow)) or (
                type(row.update) is not int or row.update != count
            ):
                raise B01ContractError("synthetic training fixture strict update order differs")
            if sparse:
                if not isinstance(row, SyntheticSparseTrainingRow):
                    raise B01ContractError("sparse fixture requires sparse coordinate rows")
                continue
            if not isinstance(row, SyntheticTrainingRow):
                raise B01ContractError("synthetic fixture requires one typed dense row")
            validated = validate_synthetic_training_row(
                row,
                arm=arm,
                previous_model_post_projection=previous_model,
                previous_optimizer_post_projection=previous_optimizer,
            )
            for group, entries in contract.items():
                source = row.array_shards if group == "array_shards" else row.state_blobs
                for name in entries:
                    handles[(group, name)].write(source[name])
            previous_model = validated["next_model_bytes"]
            previous_optimizer = validated["next_optimizer_bytes"]
        if count != UPDATES:
            raise B01ContractError("synthetic training fixture requires exactly 512 rows")
        for handle in handles.values():
            handle.close()
        handles.clear()
        if sparse:
            for group, entries in contract.items():
                for name, (dtype, row_shape) in entries.items():
                    os.truncate(
                        paths[group][name],
                        UPDATES * math.prod(row_shape) * np.dtype(dtype).itemsize,
                    )
    except Exception:
        for handle in handles.values():
            handle.close()
        for path in created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        raise

    descriptors: dict[str, dict[str, dict[str, Any]]] = {}
    for group, entries in contract.items():
        descriptors[group] = {}
        for name, (dtype, row_shape) in entries.items():
            shape = (UPDATES, *row_shape)
            byte_count = math.prod(shape) * np.dtype(dtype).itemsize
            descriptors[group][name] = {
                "path": str(paths[group][name]),
                "dtype": dtype,
                "shape": list(shape),
                "order": "C",
                "byte_count": byte_count,
            }
    if sparse:
        return {
            "schema": "FRRIE_B01_SYNTHETIC_SPARSE_DESCRIPTOR_FIXTURE_V1",
            "role": SYNTHETIC_COMPONENT_ONLY,
            "seed_label": seed_label,
            "arm": arm,
            "coordinate_order": ["update_1_512"],
            "descriptor_shards": descriptors,
            "work_contract": _work_contract(),
            "loss_reduction_contract": exact_loss_reduction_contract(),
            "max_buffered_rows": 1,
            "payload_validated": False,
            "row_payloads_validated": False,
            "canonical_full512_validation_complete": False,
            "canonical_training_shard": None,
            "production_token": False,
            "training_validation_replay_complete": False,
        }
    return {
        "schema": "FRRIE_B01_SYNTHETIC_DENSE_DESCRIPTOR_FIXTURE_V1",
        "role": SYNTHETIC_COMPONENT_ONLY,
        "seed_label": seed_label,
        "arm": arm,
        "coordinate_order": ["update_1_512"],
        "write_mode": "DENSE_ROW_STREAM",
        "descriptor_shards": descriptors,
        "work_contract": _work_contract(),
        "loss_reduction_contract": exact_loss_reduction_contract(),
        "max_buffered_rows": 1,
        "row_payloads_validated": True,
        "canonical_full512_validation_complete": False,
        "canonical_training_shard": None,
        "production_token": False,
        "training_validation_replay_complete": False,
    }
