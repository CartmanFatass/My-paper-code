"""Direct, digest-free B01 paired checkpoint and atomic resume codec."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Mapping

from ..arms import LearnedArm, PARAMETER_BYTE_COUNT
from ..state_codec import (
    OPTIMIZER_STATE_BYTE_COUNT, decode_optimizer_state,
    encode_optimizer_state, load_actor_and_optimizer_state,
)
from .constants import (
    CHECKPOINTS, CHECKPOINT_SCHEMA, DEFAULT_THREADS_PER_WORKER, DEFAULT_WORKERS,
    LEARNED_ARMS, TEST_CHECKPOINT_SCHEMA, TEST_SEED_LABEL,
)
from .contract import (
    B01ContractError, canonical_json_bytes, validate_invocation_binding,
    validate_manifest, validate_test_manifest,
)


def _bound_manifest(value: Mapping[str, Any], *, test_only: bool) -> dict[str, Any]:
    return validate_test_manifest(value) if test_only else validate_manifest(value)


def _decode_blob(value: Any, expected: int, name: str) -> bytes:
    if not isinstance(value, str):
        raise B01ContractError(f"{name} must be base64 text")
    try:
        blob = base64.b64decode(value, validate=True)
    except ValueError as exc:
        raise B01ContractError(f"{name} is not canonical base64") from exc
    if len(blob) != expected or base64.b64encode(blob).decode("ascii") != value:
        raise B01ContractError(f"{name} byte length/base64 form differs")
    return blob


def _validate_work(value: Any, update: int) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(LEARNED_ARMS):
        raise B01ContractError("checkpoint work must bind both learned arms")
    rows: dict[str, Any] = {}
    fields = {
        "training_update", "episodes", "environment_slots", "backward_calls",
        "adam_steps", "native_batch_calls", "native_batch_ledger",
        "worker_count", "thread_count",
    }
    for arm in LEARNED_ARMS:
        row = value[arm]
        if not isinstance(row, Mapping) or set(row) != fields:
            raise B01ContractError("checkpoint arm work fields differ")
        scalar_fields = fields - {"native_batch_ledger"}
        if any(type(row[field]) is not int or row[field] < 0 for field in scalar_fields):
            raise B01ContractError("checkpoint arm work must be nonnegative integers")
        if (
            row["training_update"] != update
            or row["backward_calls"] != update
            or row["adam_steps"] != update
            or row["episodes"] != update * 64
            or row["environment_slots"] != update * 4_928
            or row["worker_count"] != DEFAULT_WORKERS
            or row["thread_count"] != DEFAULT_THREADS_PER_WORKER
        ):
            raise B01ContractError("checkpoint arm work differs from completed-update frontier")
        ledger = row["native_batch_ledger"]
        ledger_fields = {
            "reset_calls", "observe_calls", "step_calls", "environment_slots",
        }
        if (
            not isinstance(ledger, Mapping) or set(ledger) != ledger_fields
            or any(type(ledger[field]) is not int or ledger[field] < 0 for field in ledger_fields)
            or ledger["environment_slots"] != row["environment_slots"]
            or row["native_batch_calls"] != (
                ledger["reset_calls"] + ledger["observe_calls"] + ledger["step_calls"]
            )
        ):
            raise B01ContractError("native batch ledger does not reconcile arm work")
        if update == 0 and any(ledger.values()):
            raise B01ContractError("update-zero native batch ledger must be zero")
        rows[arm] = dict(row)
    if rows[LEARNED_ARMS[0]] != rows[LEARNED_ARMS[1]]:
        raise B01ContractError("paired arm work exposure differs")
    return rows


def _validate_projection_audit(value: Any, update: int) -> dict[str, Any]:
    base_fields = {
        "first_tight_contact_update", "precontact_full_state_equal",
        "tight_projection_changed_coordinates", "wide_boundary_contact",
        "maximum_tight_overshoot", "cumulative_tight_displacement",
    }
    fields = set(value) if isinstance(value, Mapping) else set()
    accepted = (
        base_fields,
        base_fields | {"tight_projection_changed_indices"},
        base_fields | {
            "tight_projection_changed_indices", "continuation_audit_complete",
        },
    )
    if fields not in accepted:
        raise B01ContractError("checkpoint projection audit fields differ")
    audit = dict(value)
    contact = audit["first_tight_contact_update"]
    if contact is not None and (type(contact) is not int or not 1 <= contact <= update):
        raise B01ContractError("first tight contact update is invalid")
    if audit["precontact_full_state_equal"] is not True:
        raise B01ContractError("B01 checkpoint cannot preserve pre-contact divergence")
    changed = audit["tight_projection_changed_coordinates"]
    if type(changed) is not int or not 0 <= changed <= 18:
        raise B01ContractError("tight changed-coordinate count is outside the 18 beta coordinates")
    indices = audit.get("tight_projection_changed_indices")
    if indices is None:
        indices = [] if changed == 0 else None
    if indices is not None and (
        not isinstance(indices, list)
        or any(type(item) is not int or not 0 <= item < 18 for item in indices)
        or indices != sorted(set(indices))
        or len(indices) != changed
    ):
        raise B01ContractError("checkpoint tight changed-coordinate inventory differs")
    complete = indices is not None
    if "continuation_audit_complete" in audit and audit["continuation_audit_complete"] is not complete:
        raise B01ContractError("checkpoint continuation audit completeness differs")
    audit["tight_projection_changed_indices"] = None if indices is None else list(indices)
    audit["continuation_audit_complete"] = complete
    if type(audit["wide_boundary_contact"]) is not bool:
        raise B01ContractError("wide boundary contact must be literal bool")
    for field in ("maximum_tight_overshoot", "cumulative_tight_displacement"):
        item = audit[field]
        if isinstance(item, bool) or not isinstance(item, (int, float)) or item < 0:
            raise B01ContractError(f"projection audit {field} is invalid")
    if contact is None:
        if (
            changed != 0 or audit["wide_boundary_contact"]
            or audit["maximum_tight_overshoot"] != 0
            or audit["cumulative_tight_displacement"] != 0
        ):
            raise B01ContractError("no-contact projection audit must be the untouched state")
    elif (
        changed <= 0 or audit["maximum_tight_overshoot"] <= 0
        or audit["cumulative_tight_displacement"] <= 0
    ):
        raise B01ContractError("contact requires changed coordinates and positive projection movement")
    return audit


def encode_checkpoint(
    *, manifest: Mapping[str, Any], seed_label: str, update: int,
    arm_state_bytes: Mapping[str, bytes], optimizer_state_bytes: Mapping[str, bytes],
    work: Mapping[str, Mapping[str, int]], invocation_binding: Mapping[str, Any],
    projection_audit: Mapping[str, Any],
) -> bytes:
    binding = validate_invocation_binding(invocation_binding)
    manifest0 = _bound_manifest(manifest, test_only=binding["test_only"])
    allowed_labels = (
        [manifest0["seed_label"]] if binding["test_only"]
        else manifest0["execution_labels"]
    )
    if seed_label not in allowed_labels:
        raise B01ContractError("checkpoint seed label is outside this execution phase")
    if update not in CHECKPOINTS:
        raise B01ContractError("checkpoint update is outside the B01 curve")
    if set(arm_state_bytes) != set(LEARNED_ARMS) or set(optimizer_state_bytes) != set(LEARNED_ARMS):
        raise B01ContractError("checkpoint state must bind exactly both arms")
    encoded_models: dict[str, str] = {}
    encoded_optimizers: dict[str, str] = {}
    for arm in LEARNED_ARMS:
        model = arm_state_bytes[arm]
        optimizer = optimizer_state_bytes[arm]
        LearnedArm.from_parameter_bytes(arm, model)
        decoded = decode_optimizer_state(optimizer)
        if decoded.step != update:
            raise B01ContractError("checkpoint Adam step differs from update")
        encoded_models[arm] = base64.b64encode(model).decode("ascii")
        encoded_optimizers[arm] = base64.b64encode(optimizer).decode("ascii")
    work0 = _validate_work(work, update)
    audit = _validate_projection_audit(projection_audit, update)
    if audit["continuation_audit_complete"] is not True:
        raise B01ContractError(
            "new checkpoint encoding requires exact changed-coordinate continuation audit"
        )
    if audit["first_tight_contact_update"] is None and (
        arm_state_bytes[LEARNED_ARMS[0]] != arm_state_bytes[LEARNED_ARMS[1]]
        or optimizer_state_bytes[LEARNED_ARMS[0]] != optimizer_state_bytes[LEARNED_ARMS[1]]
    ):
        raise B01ContractError("no-contact checkpoint requires full paired model/optimizer equality")
    checkpoint_schema = TEST_CHECKPOINT_SCHEMA if binding["test_only"] else CHECKPOINT_SCHEMA
    payload = {
        "schema": checkpoint_schema,
        "manifest_contract": manifest0,
        "seed_label": seed_label,
        "update": update,
        "frontier": {
            "training_update": update,
            "training_episode_cursor": update * 64,
            "evaluation_checkpoint_cursor": 0,
            "completed_checkpoints": [item for item in CHECKPOINTS if item <= update],
        },
        "arm_state_b64": encoded_models,
        "optimizer_state_b64": encoded_optimizers,
        "work": work0,
        "invocation_binding": binding,
        "projection_audit": audit,
    }
    return canonical_json_bytes(payload)


def decode_checkpoint(
    data: bytes, *, manifest: Mapping[str, Any], expected_seed_label: str,
    expected_update: int, expected_test_only: bool | None = None,
) -> dict[str, Any]:
    if type(data) is not bytes:
        raise B01ContractError("checkpoint must be immutable bytes")
    try:
        payload = json.loads(data.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise B01ContractError("checkpoint is not canonical JSON") from exc
    fields = {
        "schema", "manifest_contract", "seed_label", "update", "frontier",
        "arm_state_b64", "optimizer_state_b64", "work", "invocation_binding",
        "projection_audit",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields or canonical_json_bytes(payload) != data:
        raise B01ContractError("checkpoint fields/canonical bytes differ")
    binding = validate_invocation_binding(
        payload.get("invocation_binding"), require_test_only=expected_test_only,
    )
    expected_schema = TEST_CHECKPOINT_SCHEMA if binding["test_only"] else CHECKPOINT_SCHEMA
    manifest0 = _bound_manifest(manifest, test_only=binding["test_only"])
    if payload["schema"] != expected_schema or payload["manifest_contract"] != manifest0:
        raise B01ContractError("checkpoint schema or manifest binding differs")
    allowed_labels = (
        [manifest0["seed_label"]] if binding["test_only"]
        else manifest0["execution_labels"]
    )
    if expected_seed_label not in allowed_labels:
        raise B01ContractError("expected checkpoint seed is outside this execution phase")
    if payload["seed_label"] != expected_seed_label or payload["update"] != expected_update:
        raise B01ContractError("checkpoint seed/update binding differs")
    if expected_update not in CHECKPOINTS:
        raise B01ContractError("expected checkpoint is outside the B01 curve")
    expected_frontier = {
        "training_update": expected_update,
        "training_episode_cursor": expected_update * 64,
        "evaluation_checkpoint_cursor": 0,
        "completed_checkpoints": [item for item in CHECKPOINTS if item <= expected_update],
    }
    if payload["frontier"] != expected_frontier:
        raise B01ContractError("checkpoint frontier differs")
    model_blobs: dict[str, bytes] = {}
    optimizer_blobs: dict[str, bytes] = {}
    if set(payload["arm_state_b64"]) != set(LEARNED_ARMS) or set(payload["optimizer_state_b64"]) != set(LEARNED_ARMS):
        raise B01ContractError("checkpoint arm state keys differ")
    for arm in LEARNED_ARMS:
        model_blobs[arm] = _decode_blob(payload["arm_state_b64"][arm], PARAMETER_BYTE_COUNT, f"model.{arm}")
        optimizer_blobs[arm] = _decode_blob(
            payload["optimizer_state_b64"][arm], OPTIMIZER_STATE_BYTE_COUNT, f"optimizer.{arm}",
        )
        LearnedArm.from_parameter_bytes(arm, model_blobs[arm])
        if decode_optimizer_state(optimizer_blobs[arm]).step != expected_update:
            raise B01ContractError("decoded Adam step differs")
    audit = _validate_projection_audit(payload["projection_audit"], expected_update)
    if audit["first_tight_contact_update"] is None and (
        model_blobs[LEARNED_ARMS[0]] != model_blobs[LEARNED_ARMS[1]]
        or optimizer_blobs[LEARNED_ARMS[0]] != optimizer_blobs[LEARNED_ARMS[1]]
    ):
        raise B01ContractError("decoded no-contact paired state differs")
    payload = dict(payload)
    payload["arm_state_bytes"] = model_blobs
    payload["optimizer_state_bytes"] = optimizer_blobs
    _validate_work(payload["work"], expected_update)
    payload["projection_audit"] = audit
    payload["invocation_binding"] = binding
    return payload


def _resume_bridge_coordinate_order(update: int) -> tuple[str, ...]:
    """Return the sole direct-byte coordinate inventory for one checkpoint."""

    if update not in CHECKPOINTS:
        raise B01ContractError("resume bridge checkpoint is outside the B01 curve")
    coordinates: list[str] = []
    if update == 0:
        coordinates.append("uninterrupted_update_001_prestate")
    else:
        coordinates.append(f"uninterrupted_update_{update:03d}_postprojection")
    if update < CHECKPOINTS[-1]:
        next_update = update + 1
        if update > 0:
            coordinates.append(f"uninterrupted_update_{next_update:03d}_prestate")
        coordinates.append(f"resumed_update_{next_update:03d}_prestate")
    return tuple(coordinates)


def validate_checkpoint_resume_bridge(
    data: bytes, *, manifest: Mapping[str, Any], expected_seed_label: str,
    expected_update: int,
    state_coordinates: Mapping[str, Mapping[str, Mapping[str, bytes]]],
    expected_test_only: bool | None = None,
) -> dict[str, Any]:
    """Validate the component-only direct-byte checkpoint/resume bridge.

    The supplied coordinates are observations made by a caller around an
    uninterrupted and a resumed execution.  This function validates those
    bytes against the canonical checkpoint codec.  Codec validation decodes
    each parameter blob into a ``LearnedArm`` value object, but this helper
    does not construct or restore a Torch actor, optimizer, RNG, native
    runtime, or file.  It therefore deliberately makes no training-transition
    or production-readiness claim.
    """

    decoded = decode_checkpoint(
        data,
        manifest=manifest,
        expected_seed_label=expected_seed_label,
        expected_update=expected_update,
        expected_test_only=expected_test_only,
    )
    expected_coordinates = _resume_bridge_coordinate_order(expected_update)
    if (
        not isinstance(state_coordinates, Mapping)
        or set(state_coordinates) != set(expected_coordinates)
    ):
        raise B01ContractError("resume bridge coordinate inventory differs")

    fields = {"model_state_bytes", "optimizer_state_bytes"}
    for coordinate in expected_coordinates:
        states = state_coordinates[coordinate]
        if not isinstance(states, Mapping) or set(states) != set(LEARNED_ARMS):
            raise B01ContractError(
                f"resume bridge {coordinate} must bind exactly both learned arms"
            )
        for arm in LEARNED_ARMS:
            arm_state = states[arm]
            if not isinstance(arm_state, Mapping) or set(arm_state) != fields:
                raise B01ContractError(
                    f"resume bridge {coordinate}.{arm} direct state fields differ"
                )
            model = arm_state["model_state_bytes"]
            optimizer = arm_state["optimizer_state_bytes"]
            if type(model) is not bytes or model != decoded["arm_state_bytes"][arm]:
                raise B01ContractError(
                    f"resume bridge {coordinate}.{arm} direct model bytes differ"
                )
            if (
                type(optimizer) is not bytes
                or optimizer != decoded["optimizer_state_bytes"][arm]
            ):
                raise B01ContractError(
                    f"resume bridge {coordinate}.{arm} direct optimizer bytes differ"
                )

    terminal = expected_update == CHECKPOINTS[-1]
    return {
        "schema": "FRRIE_B01_CHECKPOINT_RESUME_BRIDGE_COMPONENT_V1",
        "seed_label": expected_seed_label,
        "checkpoint": expected_update,
        "coordinate_order": list(expected_coordinates),
        "checkpoint_decode_complete": True,
        "provided_resume_prestate_bytes_validated": not terminal,
        "terminal_no_next_bridge": terminal,
        "codec_only": True,
        "training_transition_proven": False,
        "training_validation_replay_complete": False,
        "production_token": False,
    }


def continuation_state_from_decoded_checkpoint(decoded: Mapping[str, Any]) -> dict[str, Any]:
    """Extract every non-model continuation field from one validated decode."""

    required = {
        "seed_label", "update", "frontier", "work", "projection_audit",
        "arm_state_bytes", "optimizer_state_bytes",
    }
    if not isinstance(decoded, Mapping) or not required.issubset(decoded):
        raise B01ContractError("decoded continuation checkpoint fields differ")
    update = decoded["update"]
    if update not in CHECKPOINTS:
        raise B01ContractError("decoded continuation checkpoint update differs")
    audit = _validate_projection_audit(decoded["projection_audit"], update)
    if audit["continuation_audit_complete"] is not True:
        raise B01ContractError("decoded checkpoint lacks exact continuation audit state")
    work = _validate_work(decoded["work"], update)
    expected_frontier = {
        "training_update": update,
        "training_episode_cursor": update * 64,
        "evaluation_checkpoint_cursor": 0,
        "completed_checkpoints": [item for item in CHECKPOINTS if item <= update],
    }
    if decoded["frontier"] != expected_frontier:
        raise B01ContractError("decoded continuation frontier differs")
    return {
        "schema": "FRRIE_B01_TRAINER_CONTINUATION_STATE_V1",
        "seed_label": decoded["seed_label"],
        "update": update,
        "first_tight_contact_update": audit["first_tight_contact_update"],
        "precontact_full_state_equal": audit["precontact_full_state_equal"],
        "tight_projection_changed_indices": list(
            audit["tight_projection_changed_indices"]
        ),
        "wide_boundary_contact": audit["wide_boundary_contact"],
        "maximum_tight_overshoot": audit["maximum_tight_overshoot"],
        "cumulative_tight_displacement": audit["cumulative_tight_displacement"],
        "work": work,
        "frontier": dict(expected_frontier),
    }


def restore_trainer_continuation_state(
    target: Any, decoded: Mapping[str, Any],
) -> dict[str, Any]:
    """Restore via an explicit trainer-like continuation API and read back exactly."""

    state = continuation_state_from_decoded_checkpoint(decoded)
    restore = getattr(target, "restore_checkpoint_continuation_state", None)
    observe = getattr(target, "checkpoint_continuation_state", None)
    if not callable(restore) or not callable(observe):
        raise B01ContractError(
            "trainer target lacks explicit checkpoint continuation restore/readback API"
        )
    restore(state)
    if observe() != state:
        raise B01ContractError("trainer continuation state readback differs")
    return {
        "schema": "FRRIE_B01_TRAINER_CONTINUATION_RESTORE_RECEIPT_V1",
        "seed_label": state["seed_label"], "checkpoint": state["update"],
        "audit_state_complete": True, "work_frontier_complete": True,
        "explicit_restore_api_used": True, "direct_readback_equal": True,
        "complete": True,
    }


def snapshot_runtime(
    *, manifest: Mapping[str, Any], seed_label: str, update: int,
    models: Mapping[str, Any], optimizers: Mapping[str, Any],
    work: Mapping[str, Mapping[str, int]], invocation_binding: Mapping[str, Any],
    projection_audit: Mapping[str, Any],
) -> bytes:
    if set(models) != set(LEARNED_ARMS) or set(optimizers) != set(LEARNED_ARMS):
        raise B01ContractError("runtime snapshot requires exactly both arms")
    return encode_checkpoint(
        manifest=manifest, seed_label=seed_label, update=update,
        arm_state_bytes={arm: models[arm].parameter_bytes() for arm in LEARNED_ARMS},
        optimizer_state_bytes={
            arm: encode_optimizer_state(models[arm], optimizers[arm]) for arm in LEARNED_ARMS
        },
        work=work, invocation_binding=invocation_binding, projection_audit=projection_audit,
    )


def restore_runtime(
    data: bytes, *, manifest: Mapping[str, Any], seed_label: str, update: int,
    models: Mapping[str, Any], optimizers: Mapping[str, Any],
) -> dict[str, Any]:
    decoded = decode_checkpoint(
        data, manifest=manifest, expected_seed_label=seed_label, expected_update=update,
    )
    if set(models) != set(LEARNED_ARMS) or set(optimizers) != set(LEARNED_ARMS):
        raise B01ContractError("runtime restore requires exactly both arms")
    # Dry-load the complete target pair into temporary live objects.  This
    # validates model type, optimizer type/order, and Torch state shape before
    # either caller-owned arm mutates.
    from ..policy import FRRIEActorCritic
    from ..training import make_optimizer

    backups: dict[str, tuple[bytes, bytes, int]] = {}
    for arm in LEARNED_ARMS:
        current_model = models[arm].parameter_bytes()
        current_optimizer = encode_optimizer_state(models[arm], optimizers[arm])
        current_step = decode_optimizer_state(current_optimizer).step
        backups[arm] = (current_model, current_optimizer, current_step)
        temporary = FRRIEActorCritic(
            LearnedArm.from_parameter_bytes(arm, decoded["arm_state_bytes"][arm])
        )
        temporary_optimizer = make_optimizer(temporary)
        load_actor_and_optimizer_state(
            temporary, temporary_optimizer, decoded["arm_state_bytes"][arm],
            decoded["optimizer_state_bytes"][arm], expected_update=update,
        )
    try:
        for arm in LEARNED_ARMS:
            load_actor_and_optimizer_state(
                models[arm], optimizers[arm], decoded["arm_state_bytes"][arm],
                decoded["optimizer_state_bytes"][arm], expected_update=update,
            )
    except Exception as exc:
        rollback_failures: list[str] = []
        for arm in LEARNED_ARMS:
            model_bytes, optimizer_bytes, prior_step = backups[arm]
            try:
                load_actor_and_optimizer_state(
                    models[arm], optimizers[arm], model_bytes, optimizer_bytes,
                    expected_update=prior_step,
                )
            except Exception as rollback_exc:  # pragma: no cover - catastrophic runtime corruption
                rollback_failures.append(f"{arm}:{rollback_exc}")
        if rollback_failures:
            raise RuntimeError(
                "B01 paired restore rollback failed: " + ";".join(rollback_failures)
            ) from exc
        raise B01ContractError("B01 paired restore failed; both arms rolled back") from exc
    return decoded


def reopen_decode_restore_checkpoint(
    path: str | Path, *, manifest: Mapping[str, Any], seed_label: str, update: int,
) -> dict[str, Any]:
    """Literal-path readback plus paired temporary restore for panel validation."""

    return _reopen_decode_restore_checkpoint(
        path, manifest=manifest, seed_label=seed_label, update=update,
        expected_test_only=False,
    )


def reopen_decode_restore_test_checkpoint0(
    path: str | Path, *, manifest: Mapping[str, Any], seed_label: str,
) -> dict[str, Any]:
    """Explicit TEST-only checkpoint-0 integration seam; never a panel helper."""

    if seed_label != TEST_SEED_LABEL:
        raise B01ContractError("TEST checkpoint0 helper requires the canonical TEST seed")
    return _reopen_decode_restore_checkpoint(
        path, manifest=manifest, seed_label=seed_label, update=0,
        expected_test_only=True,
    )


def reopen_decode_restore_test_checkpoint(
    path: str | Path, *, manifest: Mapping[str, Any], seed_label: str, update: int,
) -> dict[str, Any]:
    """Literal TEST checkpoint restore at any legal B01 curve coordinate."""

    from .constants import TEST_SEED_LABELS

    if seed_label not in TEST_SEED_LABELS or update not in CHECKPOINTS:
        raise B01ContractError("TEST checkpoint restore coordinate differs")
    return _reopen_decode_restore_checkpoint(
        path, manifest=manifest, seed_label=seed_label, update=update,
        expected_test_only=True,
    )


def _reopen_decode_restore_checkpoint(
    path: str | Path, *, manifest: Mapping[str, Any], seed_label: str,
    update: int, expected_test_only: bool,
) -> dict[str, Any]:

    checkpoint_path = Path(path)
    if not checkpoint_path.is_absolute():
        raise B01ContractError("panel checkpoint locator must be absolute")
    try:
        data = checkpoint_path.read_bytes()
    except OSError as error:
        raise B01ContractError("panel checkpoint literal file is unreadable") from error
    decoded = decode_checkpoint(
        data, manifest=manifest, expected_seed_label=seed_label,
        expected_update=update, expected_test_only=expected_test_only,
    )
    from ..policy import FRRIEActorCritic
    from ..training import make_optimizer
    models = {
        arm: FRRIEActorCritic(LearnedArm.from_parameter_bytes(
            arm, decoded["arm_state_bytes"][arm],
        ))
        for arm in LEARNED_ARMS
    }
    optimizers = {arm: make_optimizer(models[arm]) for arm in LEARNED_ARMS}
    restored = restore_runtime(
        data, manifest=manifest, seed_label=seed_label, update=update,
        models=models, optimizers=optimizers,
    )
    for arm in LEARNED_ARMS:
        if (
            models[arm].parameter_bytes() != decoded["arm_state_bytes"][arm]
            or encode_optimizer_state(models[arm], optimizers[arm])
            != decoded["optimizer_state_bytes"][arm]
        ):
            raise B01ContractError("panel checkpoint temporary restore bytes differ")
    return {
        "schema": "FRRIE_B01_CHECKPOINT_RESTORE_RECEIPT_V1",
        "seed_label": seed_label, "checkpoint": update,
        "literal_path": str(checkpoint_path.resolve(strict=True)),
        "literal_byte_count": len(data), "paired_decode_complete": True,
        "paired_restore_complete": True,
        "model_byte_count_by_arm": {
            arm: len(restored["arm_state_bytes"][arm]) for arm in LEARNED_ARMS
        },
        "optimizer_byte_count_by_arm": {
            arm: len(restored["optimizer_state_bytes"][arm]) for arm in LEARNED_ARMS
        },
        "complete": True,
    }
