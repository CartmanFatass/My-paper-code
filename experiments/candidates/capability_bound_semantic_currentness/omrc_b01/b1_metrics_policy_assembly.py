"""Production assembly of checkpoint-bound B1 policy metrics tables.

The seam accepts only the canonical staging tree, grouped worker raw slices,
and host-rehydrated held-out tapes.  It does not accept a model factory,
checkpoint summary, policy action trace, reduction, or scientific classifier.
"""

from __future__ import annotations

from dataclasses import asdict
import io
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from . import addressing
from .artifact import canonical_json_bytes
from .b0 import ARMS
from .b1_contract import (
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_RUN_NAME,
    B1_SEEDS,
    B1_SLOT_ORDER,
)
from .b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA,
    B1EngineError,
    _validate_envelope,
)
from .b1_policy_records import (
    POLICY_CURVE_KEY_FIELDS,
    POLICY_RECORD_KEY_FIELDS,
    build_checkpoint_policy_records,
    build_complete_policy_curves,
    build_policy_support_signature_counts,
    build_literal_null_manifest_fields,
)
from .b1_runtime_audit import (
    observe_active_modes,
    require_frozen_execution_modes,
)
from .b1_shared_tables import build_b1_shared_truth_tables
from .checkpoint import model_parameter_digest_from_state
from .checkpoint import restore_checkpoint
from .engine import _ADAPTERS, _optimizer_digest, _project_panel
from .model import CommonRecurrentActorCritic, model_parameter_digest
from .contract import Action
from .ppo import RecurrentPPOTrainer, make_adam
from .tapes import EpisodeTape


B1_METRICS_POLICY_ASSEMBLY_SCHEMA = "cbsc_omrc_b01_b1_metrics_policy_assembly_v1"
FORMAL_POLICY_PROFILE_SCHEMA = "cbsc_omrc_b01_b1_policy_formal_profile_v1"
TEST_ONLY_POLICY_PROFILE_SCHEMA = "cbsc_omrc_b01_b1_policy_test_only_profile_v1"
FORMAL_POLICY_DECISION_COUNT = 73_728
FORMAL_POLICY_CURVE_COUNT = 768
TEST_ONLY_POLICY_DECISION_COUNT = 576
TEST_ONLY_POLICY_CURVE_COUNT = 6
TEST_ONLY_EXECUTION_MODE_RECORD_COUNT = 12
ONE_SLOT_FORMAL_SCHEMA = "cbsc_omrc_b01_b1_policy_one_slot_v1"
ONE_SLOT_TEST_ONLY_SCHEMA = "cbsc_omrc_b01_b1_policy_one_slot_test_only_v1"
ONE_SLOT_FORMAL_POLICY_DECISION_COUNT = 6_144
ONE_SLOT_FORMAL_POLICY_CURVE_COUNT = 64
ONE_SLOT_EXECUTION_MODE_RECORD_COUNT = 4
ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT = 4
POLICY_REPLAY_AGGREGATE_SCHEMA = "cbsc_omrc_b01_policy_replay_aggregate_v1"
POLICY_REPLAY_TEST_AGGREGATE_SCHEMA = "cbsc_omrc_b01_policy_replay_test_aggregate_v1"
_POLICY_REPLAY_RESULT_SCHEMA = "cbsc_omrc_b01_policy_replay_result_v1"
_POLICY_REPLAY_TEST_RESULT_SCHEMA = "cbsc_omrc_b01_policy_replay_test_result_v1"

_TEST_SLOT_ORDER = (
    B1_SLOT_ORDER[1],
    B1_SLOT_ORDER[5],
    B1_SLOT_ORDER[9],
)
_TEST_STOCHASTIC_IDS = (0,)
_TEST_MOTIF_IDS = (0,)
_CHECKPOINT_RECORD_FIELDS = frozenset(
    {
        "update",
        "relative_path",
        "sha256",
        "byte_count",
        "binding",
        "counters",
        "digests",
        "model_parameter_digest",
    }
)


class B1MetricsPolicyAssemblyError(ValueError):
    """Canonical policy assembly inputs or coverage differ from B1."""


def _require_digest(name: str, value: object, length: int = 64) -> str:
    if (
        type(value) is not str
        or len(value) != length
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise B1MetricsPolicyAssemblyError(
            f"{name} must be {length} lowercase hexadecimal characters"
        )
    return value


def _slot_tag(index: int, seed: int, arm: str) -> str:
    return f"{index:02d}-seed-{seed}-{arm}"


def _decode_checkpoint_snapshot(payload: bytes) -> Mapping[str, Any]:
    stream = io.BytesIO(payload)
    try:
        try:
            envelope = torch.load(stream, map_location="cpu", weights_only=True)
        except TypeError:  # pragma: no cover - older PyTorch compatibility
            stream.seek(0)
            envelope = torch.load(stream, map_location="cpu")
        _validate_envelope(envelope)
    except (B1EngineError, EOFError, RuntimeError, TypeError, ValueError) as exc:
        raise B1MetricsPolicyAssemblyError(
            "checkpoint bytes are not a canonical B1 envelope"
        ) from exc
    return envelope


def _expected_tape_keys(
    slot_order: tuple[tuple[int, str], ...],
    stochastic_ids: tuple[int, ...],
    motif_ids: tuple[int, ...],
) -> list[tuple[int, str, int]]:
    seeds = tuple(dict.fromkeys(seed for seed, _ in slot_order))
    return [
        (seed, split, tape_id)
        for seed in seeds
        for split, ids in (
            (addressing.EVAL_STOCHASTIC, stochastic_ids),
            (addressing.EVAL_MOTIF, motif_ids),
        )
        for tape_id in ids
    ]


def _validate_heldout_tapes(
    heldout_tapes: Sequence[EpisodeTape],
    *,
    slot_order: tuple[tuple[int, str], ...],
    stochastic_ids: tuple[int, ...],
    motif_ids: tuple[int, ...],
    attempt_id: str,
    literal_binding_spec_sha256: str,
) -> tuple[tuple[EpisodeTape, ...], list[dict[str, Any]]]:
    if isinstance(heldout_tapes, (str, bytes, bytearray)) or not isinstance(
        heldout_tapes, Sequence
    ):
        raise B1MetricsPolicyAssemblyError("held-out tapes must be a sequence")
    tapes = tuple(heldout_tapes)
    observed = [
        (tape.identity.seed, tape.identity.split, tape.identity.episode_id)
        if type(tape) is EpisodeTape
        else None
        for tape in tapes
    ]
    expected = _expected_tape_keys(slot_order, stochastic_ids, motif_ids)
    if observed != expected:
        raise B1MetricsPolicyAssemblyError(
            "held-out tape coverage is missing, duplicated, or reordered"
        )
    try:
        shared = build_b1_shared_truth_tables(
            tapes,
            attempt_id=attempt_id,
            literal_binding_spec_sha256=literal_binding_spec_sha256,
        )
    except ValueError as exc:
        raise B1MetricsPolicyAssemblyError(
            "held-out tapes differ from canonical host reconstruction"
        ) from exc
    return tapes, shared["evaluator_decision_truth"]


def _validate_group_identity(
    group: object,
    *,
    seed: int,
    arm: str,
    attempt_id: str,
    implementation_commit: str,
    source_conformance_sha256: str,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(group, Sequence) or isinstance(group, (str, bytes, bytearray)):
        raise B1MetricsPolicyAssemblyError("raw slice group must be a sequence")
    slices = tuple(group)
    if not slices:
        raise B1MetricsPolicyAssemblyError("raw slice group is empty")
    expected_start = 0
    for raw in slices:
        if not isinstance(raw, Mapping):
            raise B1MetricsPolicyAssemblyError("raw slice is not a record")
        full = raw.get("full_bindings")
        interval = raw.get("slice")
        if (
            raw.get("schema") != B1_RAW_EVIDENCE_SCHEMA
            or raw.get("attempt_id") != attempt_id
            or raw.get("run_name") != B1_RUN_NAME
            or raw.get("seed") != seed
            or raw.get("arm") != arm
            or raw.get("scientific_branch") is not None
            or not isinstance(full, Mapping)
            or full.get("implementation_commit") != implementation_commit
            or full.get("source_conformance_sha256") != source_conformance_sha256
            or not isinstance(interval, Mapping)
            or set(interval) != {"start_update", "stop_update"}
        ):
            raise B1MetricsPolicyAssemblyError("raw slice identity/source binding differs")
        start = interval["start_update"]
        stop = interval["stop_update"]
        if (
            type(start) is not int
            or type(stop) is not int
            or start != expected_start
            or start not in B1_CHECKPOINT_UPDATES
            or stop not in B1_CHECKPOINT_UPDATES
            or stop <= start
        ):
            raise B1MetricsPolicyAssemblyError(
                "raw slices contain a gap, overlap, duplicate, or reordering"
            )
        expected_start = stop
    if expected_start != B1_CHECKPOINT_UPDATES[-1]:
        raise B1MetricsPolicyAssemblyError("raw slice group does not reach update 48")
    return slices


def _checkpoint_records(
    slices: tuple[Mapping[str, Any], ...]
) -> tuple[Mapping[str, Any], ...]:
    output: list[Mapping[str, Any]] = []
    for raw in slices:
        records = raw.get("checkpoints_created")
        if not isinstance(records, list):
            raise B1MetricsPolicyAssemblyError("raw checkpoint inventory is absent")
        for record in records:
            if not isinstance(record, Mapping) or frozenset(record) != _CHECKPOINT_RECORD_FIELDS:
                raise B1MetricsPolicyAssemblyError("raw checkpoint record schema differs")
            output.append(record)
    if [record["update"] for record in output] != list(B1_CHECKPOINT_UPDATES):
        raise B1MetricsPolicyAssemblyError(
            "raw checkpoint inventory is missing, duplicated, or reordered"
        )
    return tuple(output)


def _policy_rows_for_slot(
    *,
    staging_root: Path,
    slot_index: int,
    seed: int,
    arm: str,
    checkpoint_records: tuple[Mapping[str, Any], ...],
    tapes: tuple[EpisodeTape, ...],
    attempt_id: str,
    implementation_commit: str,
    source_conformance_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    durable = staging_root / "arm-seeds" / _slot_tag(slot_index, seed, arm)
    output: list[dict[str, Any]] = []
    mode_records: list[dict[str, Any]] = []
    for update, record in zip(B1_CHECKPOINT_UPDATES, checkpoint_records, strict=True):
        relative = f"checkpoint-update-{update}.pt"
        path = durable / relative
        if record["relative_path"] != relative or not path.is_file():
            raise B1MetricsPolicyAssemblyError("fixed checkpoint path is absent or differs")
        before = path.read_bytes()
        if (
            type(record["byte_count"]) is not int
            or record["byte_count"] <= 0
            or len(before) != record["byte_count"]
        ):
            raise B1MetricsPolicyAssemblyError(
                "checkpoint bytes count differs from raw inventory"
            )
        if hashlib.sha256(before).hexdigest() != record["sha256"]:
            raise B1MetricsPolicyAssemblyError("checkpoint SHA differs from raw inventory")
        envelope = _decode_checkpoint_snapshot(before)
        binding = envelope["binding"]
        inner = envelope["recurrent_ppo_checkpoint"]
        if (
            binding.get("attempt_id") != attempt_id
            or binding.get("run_name") != B1_RUN_NAME
            or binding.get("seed") != seed
            or binding.get("arm") != arm
            or binding.get("completed_rollout_updates") != update
            or binding.get("implementation_commit") != implementation_commit
            or binding.get("source_conformance_sha256") != source_conformance_sha256
            or record["binding"] != binding
            or record["counters"] != inner["counters"]
            or record["digests"] != inner["digests"]
        ):
            raise B1MetricsPolicyAssemblyError(
                "checkpoint envelope/raw identity or source binding differs"
            )
        parameter_sha256 = model_parameter_digest_from_state(inner["model_state"])
        if record["model_parameter_digest"] != parameter_sha256:
            raise B1MetricsPolicyAssemblyError(
                "checkpoint model digest differs from raw inventory"
            )
        model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
        try:
            model.load_state_dict(inner["model_state"], strict=True)
        except (RuntimeError, TypeError, ValueError) as exc:
            raise B1MetricsPolicyAssemblyError(
                "checkpoint model state cannot load into the canonical model"
            ) from exc
        if model_parameter_digest(model) != parameter_sha256:
            raise B1MetricsPolicyAssemblyError(
                "canonical model differs after checkpoint restore"
            )
        active_modes = observe_active_modes(model)
        required_modes = require_frozen_execution_modes(model)
        if active_modes != required_modes:
            raise B1MetricsPolicyAssemblyError(
                "execution modes changed between direct observation and frozen gate"
            )
        mode_records.append(
            {
                "run_order": 0,
                "seed": seed,
                "arm_order": ARMS.index(arm),
                "checkpoint_update": update,
                "active_modes": list(active_modes),
            }
        )
        if path.read_bytes() != before:
            raise B1MetricsPolicyAssemblyError("checkpoint bytes changed during assembly")
        output.extend(
            build_checkpoint_policy_records(
                run_name=B1_RUN_NAME,
                arm=arm,
                seed=seed,
                checkpoint_update=update,
                checkpoint_bytes=before,
                tapes=tapes,
                model=model,
            )
        )
    return output, mode_records


def validate_execution_mode_records(
    records: Sequence[Mapping[str, Any]], *, test_only: bool = False
) -> list[dict[str, Any]]:
    """Require exact checkpoint coverage and an empty directly observed mode list."""

    if type(test_only) is not bool or not isinstance(records, Sequence) or isinstance(
        records, (str, bytes, bytearray)
    ):
        raise B1MetricsPolicyAssemblyError("execution mode records must be a sequence")
    slot_order = _TEST_SLOT_ORDER if test_only else B1_SLOT_ORDER
    return _validate_execution_mode_records_for_slots(records, slot_order=slot_order)


def _validate_execution_mode_records_for_slots(
    records: Sequence[Mapping[str, Any]],
    *,
    slot_order: tuple[tuple[int, str], ...],
) -> list[dict[str, Any]]:
    arm_order = {arm: index for index, arm in enumerate(ARMS)}
    expected = [
        (0, seed, arm_order[arm], update)
        for seed, arm in slot_order
        for update in B1_CHECKPOINT_UPDATES
    ]
    output: list[dict[str, Any]] = []
    required_fields = {
        "run_order", "seed", "arm_order", "checkpoint_update", "active_modes"
    }
    for record in records:
        if not isinstance(record, Mapping) or set(record) != required_fields:
            raise B1MetricsPolicyAssemblyError("execution mode record schema is tampered")
        modes = record["active_modes"]
        if not isinstance(modes, list) or any(
            type(mode) is not str or not mode for mode in modes
        ):
            raise B1MetricsPolicyAssemblyError("execution active_modes observation differs")
        if modes:
            raise B1MetricsPolicyAssemblyError(
                "prohibited active execution modes cannot enter policy publication"
            )
        output.append(dict(record))
    observed = [
        (
            record["run_order"],
            record["seed"],
            record["arm_order"],
            record["checkpoint_update"],
        )
        for record in output
    ]
    if observed != expected:
        raise B1MetricsPolicyAssemblyError(
            "execution mode record coverage is missing, duplicated, or reordered"
        )
    return output


def _full_checkpoint_records_from_inventory(
    *,
    staging_root: Path,
    slot_index: int,
    seed: int,
    arm: str,
    checkpoint_inventory: Sequence[Mapping[str, Any]],
    attempt_id: str,
    implementation_commit: str,
    source_conformance_sha256: str,
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(checkpoint_inventory, Sequence) or isinstance(
        checkpoint_inventory, (str, bytes, bytearray)
    ) or len(checkpoint_inventory) != len(B1_CHECKPOINT_UPDATES):
        raise B1MetricsPolicyAssemblyError("one-slot checkpoint inventory differs")
    output: list[Mapping[str, Any]] = []
    durable = staging_root / "arm-seeds" / _slot_tag(slot_index, seed, arm)
    for update, compact in zip(
        B1_CHECKPOINT_UPDATES, checkpoint_inventory, strict=True
    ):
        if not isinstance(compact, Mapping) or set(compact) != {
            "update", "path", "sha256"
        }:
            raise B1MetricsPolicyAssemblyError("one-slot checkpoint binding schema differs")
        expected_path = (durable / f"checkpoint-update-{update}.pt").resolve(strict=False)
        try:
            actual_path = Path(compact["path"]).resolve(strict=True)
        except (OSError, TypeError) as exc:
            raise B1MetricsPolicyAssemblyError("one-slot checkpoint path is absent") from exc
        if compact["update"] != update or actual_path != expected_path:
            raise B1MetricsPolicyAssemblyError("one-slot checkpoint path/update differs")
        payload = actual_path.read_bytes()
        observed_sha = hashlib.sha256(payload).hexdigest()
        if compact["sha256"] != observed_sha:
            raise B1MetricsPolicyAssemblyError("one-slot checkpoint SHA differs")
        envelope = _decode_checkpoint_snapshot(payload)
        binding = envelope["binding"]
        inner = envelope["recurrent_ppo_checkpoint"]
        if (
            binding.get("attempt_id") != attempt_id
            or binding.get("run_name") != B1_RUN_NAME
            or binding.get("seed") != seed
            or binding.get("arm") != arm
            or binding.get("completed_rollout_updates") != update
            or binding.get("implementation_commit") != implementation_commit
            or binding.get("source_conformance_sha256") != source_conformance_sha256
        ):
            raise B1MetricsPolicyAssemblyError(
                "one-slot checkpoint source/attempt identity differs"
            )
        output.append(
            {
                "update": update,
                "relative_path": actual_path.name,
                "sha256": observed_sha,
                "byte_count": len(payload),
                "binding": dict(binding),
                "counters": dict(inner["counters"]),
                "digests": dict(inner["digests"]),
                "model_parameter_digest": model_parameter_digest_from_state(
                    inner["model_state"]
                ),
            }
        )
    return tuple(output)


def _join_source_evaluations(
    *,
    staging_root: Path,
    slot_index: int,
    seed: int,
    arm: str,
    checkpoint_inventory: Sequence[Mapping[str, Any]],
    tapes: tuple[EpisodeTape, ...],
    policy_rows: Sequence[Mapping[str, Any]],
    execution_mode_records: Sequence[Mapping[str, Any]],
    source_evaluations: Sequence[Mapping[str, Any]],
    source_active_modes: Sequence[str],
) -> list[dict[str, Any]]:
    if (
        not isinstance(source_evaluations, Sequence)
        or isinstance(source_evaluations, (str, bytes, bytearray))
        or len(source_evaluations) != len(B1_CHECKPOINT_UPDATES)
        or not isinstance(source_active_modes, Sequence)
        or isinstance(source_active_modes, (str, bytes, bytearray))
    ):
        raise B1MetricsPolicyAssemblyError("source held-out evaluation inventory differs")
    if list(source_active_modes):
        raise B1MetricsPolicyAssemblyError("source held-out execution modes are prohibited")
    action_names = {
        0: Action.SERVE.name,
        1: Action.REFRESH.name,
        2: Action.SAFE_FALLBACK.name,
    }
    split_order = {addressing.EVAL_STOCHASTIC: 1, addressing.EVAL_MOTIF: 2}
    policy_by_update: dict[int, list[Mapping[str, Any]]] = {
        update: [row for row in policy_rows if row["checkpoint_update"] == update]
        for update in B1_CHECKPOINT_UPDATES
    }
    modes_by_update = {
        row["checkpoint_update"]: row for row in execution_mode_records
    }
    output: list[dict[str, Any]] = []
    durable = staging_root / "arm-seeds" / _slot_tag(slot_index, seed, arm)
    required_eval_fields = {
        "update", "actions", "heldout_state_observations", "adapter_work_receipt"
    }
    required_state_fields = {
        "model_digest_before", "model_digest_after", "training_mode_before",
        "training_mode_after", "consumed_uniform_rows", "optimizer_digest_before",
        "optimizer_digest_after",
    }
    for update, compact, source in zip(
        B1_CHECKPOINT_UPDATES,
        checkpoint_inventory,
        source_evaluations,
        strict=True,
    ):
        if not isinstance(source, Mapping) or set(source) != required_eval_fields:
            raise B1MetricsPolicyAssemblyError("source held-out evaluation schema differs")
        if source["update"] != update:
            raise B1MetricsPolicyAssemblyError("source held-out evaluation order differs")
        path = durable / f"checkpoint-update-{update}.pt"
        payload = path.read_bytes()
        if compact["sha256"] != hashlib.sha256(payload).hexdigest():
            raise B1MetricsPolicyAssemblyError("source evaluation checkpoint SHA differs")
        envelope = _decode_checkpoint_snapshot(payload)
        inner = envelope["recurrent_ppo_checkpoint"]
        model = CommonRecurrentActorCritic(seed, address_u64=addressing.u64)
        trainer = RecurrentPPOTrainer(
            model,
            run_name=B1_RUN_NAME,
            seed=seed,
            optimizer=make_adam(model),
            address_u64=addressing.u64,
        )
        restore_checkpoint(
            inner,
            trainer,
            expected_arm=arm,
            expected_training_tape_digest=inner["digests"]["training_tape"],
            expected_action_uniform_digest=inner["digests"]["action_uniform"],
        )
        parameter_sha = model_parameter_digest(trainer.model)
        optimizer_sha = _optimizer_digest(trainer)
        _, work = _project_panel(tapes, _ADAPTERS[arm])
        rows = policy_by_update[update]
        indexed = {
            (row["split_order"], row["tape_id"], row["opportunity_id"]): row
            for row in rows
        }
        if len(indexed) != len(rows):
            raise B1MetricsPolicyAssemblyError("replay policy decision key is duplicated")
        replay_actions = []
        for tape in tapes:
            names = []
            for opportunity in range(24):
                key = (
                    split_order[tape.identity.split],
                    tape.identity.episode_id,
                    opportunity,
                )
                if key not in indexed:
                    raise B1MetricsPolicyAssemblyError(
                        "replay policy decision coverage differs from held-out tape"
                    )
                names.append(action_names[indexed[key]["selected_action"]])
            replay_actions.append(
                {"identity": asdict(tape.identity), "decision_actions": names}
            )
        replay_state = {
            "model_digest_before": parameter_sha,
            "model_digest_after": parameter_sha,
            "training_mode_before": True,
            "training_mode_after": True,
            "consumed_uniform_rows": [],
            "optimizer_digest_before": optimizer_sha,
            "optimizer_digest_after": optimizer_sha,
        }
        if (
            not isinstance(source["actions"], list)
            or source["actions"] != replay_actions
            or not isinstance(source["heldout_state_observations"], Mapping)
            or set(source["heldout_state_observations"]) != required_state_fields
            or dict(source["heldout_state_observations"]) != replay_state
            or source["adapter_work_receipt"] != asdict(work)
        ):
            raise B1MetricsPolicyAssemblyError(
                "source/replay held-out action, tape, state, or adapter-work divergence"
            )
        mode_record = modes_by_update.get(update)
        if mode_record is None or mode_record["active_modes"] != list(source_active_modes):
            raise B1MetricsPolicyAssemblyError(
                "source/replay held-out execution-mode divergence"
            )
        source_fact = {
            "update": update,
            "checkpoint_sha256": compact["sha256"],
            "actions": source["actions"],
            "heldout_state_observations": dict(source["heldout_state_observations"]),
            "adapter_work_receipt": source["adapter_work_receipt"],
            "active_modes": list(source_active_modes),
        }
        replay_fact = {
            "update": update,
            "checkpoint_sha256": compact["sha256"],
            "actions": replay_actions,
            "heldout_state_observations": replay_state,
            "adapter_work_receipt": asdict(work),
            "active_modes": mode_record["active_modes"],
        }
        source_sha = hashlib.sha256(canonical_json_bytes(source_fact)).hexdigest()
        replay_sha = hashlib.sha256(canonical_json_bytes(replay_fact)).hexdigest()
        if source_sha != replay_sha:
            raise B1MetricsPolicyAssemblyError("source/replay held-out fact digest differs")
        output.append(
            {
                "run_order": 0,
                "seed": seed,
                "arm_order": ARMS.index(arm),
                "checkpoint_update": update,
                "checkpoint_sha256": compact["sha256"],
                "source_evaluation_sha256": source_sha,
                "replay_evaluation_sha256": replay_sha,
                "joined": True,
            }
        )
    return output


def assemble_one_slot_policy_tables(
    *,
    staging_root: Path,
    attempt_id: str,
    seed: int,
    arm: str,
    original_slot_index: int,
    checkpoint_inventory: Sequence[Mapping[str, Any]],
    source_evaluations: Sequence[Mapping[str, Any]],
    source_active_modes: Sequence[str],
    heldout_tapes: Sequence[EpisodeTape],
    implementation_commit: str,
    source_conformance_sha256: str,
    literal_binding_spec_sha256: str,
    test_only: bool = False,
) -> dict[str, Any]:
    """Rehydrate one exact slot from four checkpoint files after admission."""

    if type(test_only) is not bool or type(original_slot_index) is not int:
        raise B1MetricsPolicyAssemblyError("one-slot profile identity differs")
    if (
        original_slot_index not in range(len(B1_SLOT_ORDER))
        or B1_SLOT_ORDER[original_slot_index] != (seed, arm)
    ):
        raise B1MetricsPolicyAssemblyError("one-slot original index/identity differs")
    test_identities = {(21101, "RAW-GRU", 1), (21121, "RAW-GRU", 5), (21143, "RAW-GRU", 9)}
    if test_only and (seed, arm, original_slot_index) not in test_identities:
        raise B1MetricsPolicyAssemblyError("TEST_ONLY replay slot identity differs")
    root = Path(staging_root).resolve(strict=True)
    _require_digest("implementation commit", implementation_commit, 40)
    _require_digest("source conformance", source_conformance_sha256)
    _require_digest("literal binding specification", literal_binding_spec_sha256)
    stochastic_ids = _TEST_STOCHASTIC_IDS if test_only else B1_EVAL_STOCHASTIC_IDS
    motif_ids = _TEST_MOTIF_IDS if test_only else B1_EVAL_MOTIF_IDS
    tapes, _ = _validate_heldout_tapes(
        heldout_tapes,
        slot_order=((seed, arm),),
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
        attempt_id=attempt_id,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
    )
    records = _full_checkpoint_records_from_inventory(
        staging_root=root,
        slot_index=original_slot_index,
        seed=seed,
        arm=arm,
        checkpoint_inventory=checkpoint_inventory,
        attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
    )
    rows, modes = _policy_rows_for_slot(
        staging_root=root,
        slot_index=original_slot_index,
        seed=seed,
        arm=arm,
        checkpoint_records=records,
        tapes=tapes,
        attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
    )
    rows.sort(key=lambda row: tuple(row[name] for name in POLICY_RECORD_KEY_FIELDS))
    _exact_policy_coverage(
        rows,
        slot_order=((seed, arm),),
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
    )
    modes = _validate_execution_mode_records_for_slots(
        modes, slot_order=((seed, arm),)
    )
    curves = build_complete_policy_curves(rows)
    evaluation_joins = _join_source_evaluations(
        staging_root=root,
        slot_index=original_slot_index,
        seed=seed,
        arm=arm,
        checkpoint_inventory=checkpoint_inventory,
        tapes=tapes,
        policy_rows=rows,
        execution_mode_records=modes,
        source_evaluations=source_evaluations,
        source_active_modes=source_active_modes,
    )
    expected_rows = len(B1_CHECKPOINT_UPDATES) * (
        len(stochastic_ids) + len(motif_ids)
    ) * 24
    expected_curves = len(stochastic_ids) + len(motif_ids)
    if (
        len(rows) != expected_rows
        or len(curves) != expected_curves
        or len(modes) != ONE_SLOT_EXECUTION_MODE_RECORD_COUNT
        or len(evaluation_joins) != ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT
    ):
        raise B1MetricsPolicyAssemblyError("one-slot output coverage differs")
    if not test_only and (
        expected_rows != ONE_SLOT_FORMAL_POLICY_DECISION_COUNT
        or expected_curves != ONE_SLOT_FORMAL_POLICY_CURVE_COUNT
    ):
        raise AssertionError("one-slot formal cardinality differs")
    packet = {
        "schema": ONE_SLOT_TEST_ONLY_SCHEMA if test_only else ONE_SLOT_FORMAL_SCHEMA,
        "test_only": test_only,
        "run_name": B1_RUN_NAME,
        "attempt_id": attempt_id,
        "seed": seed,
        "arm": arm,
        "original_slot_index": original_slot_index,
        "policy_decisions": rows,
        "policy_curves": curves,
        "execution_mode_records": modes,
        "evaluation_join_records": evaluation_joins,
        "literal_nulls": build_literal_null_manifest_fields(),
        "scientific_branch": None,
        "scientific_polarity": None,
        "promotion_eligible": None,
        "b2_extension_trigger": None,
        "counts": {
            "policy_decisions": len(rows),
            "policy_curves": len(curves),
            "execution_mode_records": len(modes),
            "evaluation_join_records": len(evaluation_joins),
        },
    }
    return validate_one_slot_policy_packet(
        packet,
        expected_attempt_id=attempt_id,
        expected_seed=seed,
        expected_arm=arm,
        expected_slot_index=original_slot_index,
        test_only=test_only,
    )


def _all_null(value: object) -> bool:
    if isinstance(value, Mapping):
        return all(_all_null(item) for item in value.values())
    return value is None


def validate_one_slot_policy_packet(
    packet: Mapping[str, Any],
    *,
    expected_attempt_id: str,
    expected_seed: int,
    expected_arm: str,
    expected_slot_index: int,
    test_only: bool = False,
) -> dict[str, Any]:
    required = {
        "schema", "test_only", "run_name", "attempt_id", "seed", "arm",
        "original_slot_index", "policy_decisions", "policy_curves",
        "execution_mode_records", "evaluation_join_records", "literal_nulls", "scientific_branch",
        "scientific_polarity", "promotion_eligible", "b2_extension_trigger", "counts",
    }
    if not isinstance(packet, Mapping) or set(packet) != required:
        raise B1MetricsPolicyAssemblyError("one-slot packet schema differs")
    schema = ONE_SLOT_TEST_ONLY_SCHEMA if test_only else ONE_SLOT_FORMAL_SCHEMA
    if (
        packet["schema"] != schema
        or packet["test_only"] is not test_only
        or packet["run_name"] != B1_RUN_NAME
        or packet["attempt_id"] != expected_attempt_id
        or packet["seed"] != expected_seed
        or packet["arm"] != expected_arm
        or packet["original_slot_index"] != expected_slot_index
    ):
        raise B1MetricsPolicyAssemblyError("one-slot packet identity differs")
    for name in (
        "scientific_branch", "scientific_polarity", "promotion_eligible",
        "b2_extension_trigger",
    ):
        if packet[name] is not None:
            raise B1MetricsPolicyAssemblyError("one-slot packet scientific field is nonnull")
    if not _all_null(packet["literal_nulls"]):
        raise B1MetricsPolicyAssemblyError("one-slot packet literal-null science differs")
    rows = packet["policy_decisions"]
    curves = packet["policy_curves"]
    modes = packet["execution_mode_records"]
    joins = packet["evaluation_join_records"]
    if (
        not isinstance(rows, list) or not isinstance(curves, list)
        or not isinstance(modes, list) or not isinstance(joins, list)
    ):
        raise B1MetricsPolicyAssemblyError("one-slot packet tables are absent")
    _validate_execution_mode_records_for_slots(
        modes, slot_order=((expected_seed, expected_arm),)
    )
    join_fields = {
        "run_order", "seed", "arm_order", "checkpoint_update",
        "checkpoint_sha256", "source_evaluation_sha256",
        "replay_evaluation_sha256", "joined",
    }
    expected_join_keys = [
        (0, expected_seed, ARMS.index(expected_arm), update)
        for update in B1_CHECKPOINT_UPDATES
    ]
    observed_join_keys = []
    for row in joins:
        if not isinstance(row, Mapping) or set(row) != join_fields:
            raise B1MetricsPolicyAssemblyError("one-slot evaluation join schema differs")
        for name in (
            "checkpoint_sha256", "source_evaluation_sha256",
            "replay_evaluation_sha256",
        ):
            _require_digest(name.replace("_", " "), row[name])
        if (
            row["joined"] is not True
            or row["source_evaluation_sha256"] != row["replay_evaluation_sha256"]
        ):
            raise B1MetricsPolicyAssemblyError("one-slot evaluation join did not pass")
        observed_join_keys.append(
            (row["run_order"], row["seed"], row["arm_order"], row["checkpoint_update"])
        )
    if observed_join_keys != expected_join_keys:
        raise B1MetricsPolicyAssemblyError("one-slot evaluation join coverage differs")
    expected_counts = {
        "policy_decisions": 192 if test_only else ONE_SLOT_FORMAL_POLICY_DECISION_COUNT,
        "policy_curves": 2 if test_only else ONE_SLOT_FORMAL_POLICY_CURVE_COUNT,
        "execution_mode_records": ONE_SLOT_EXECUTION_MODE_RECORD_COUNT,
        "evaluation_join_records": ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT,
    }
    if packet["counts"] != expected_counts or (
        len(rows), len(curves), len(modes), len(joins)
    ) != (
        expected_counts["policy_decisions"],
        expected_counts["policy_curves"],
        expected_counts["execution_mode_records"],
        expected_counts["evaluation_join_records"],
    ):
        raise B1MetricsPolicyAssemblyError("one-slot packet counts differ")
    return dict(packet)


def aggregate_b1_policy_replay_results(
    results: Sequence[Mapping[str, Any]],
    *,
    heldout_tapes: Sequence[EpisodeTape],
    expected_attempt_id: str,
    expected_implementation_commit: str,
    expected_source_conformance_sha256: str,
    literal_binding_spec_sha256: str,
    test_only: bool = False,
) -> dict[str, Any]:
    """Validate and aggregate exact worker wrappers without replaying a model."""

    if type(test_only) is not bool or not isinstance(results, Sequence) or isinstance(
        results, (str, bytes, bytearray)
    ):
        raise B1MetricsPolicyAssemblyError("policy replay results must be a sequence")
    slot_order = _TEST_SLOT_ORDER if test_only else B1_SLOT_ORDER
    if len(results) != len(slot_order):
        raise B1MetricsPolicyAssemblyError("policy replay result slot coverage differs")
    _require_digest("implementation commit", expected_implementation_commit, 40)
    _require_digest("source conformance", expected_source_conformance_sha256)
    _require_digest("literal binding specification", literal_binding_spec_sha256)
    stochastic_ids = _TEST_STOCHASTIC_IDS if test_only else B1_EVAL_STOCHASTIC_IDS
    motif_ids = _TEST_MOTIF_IDS if test_only else B1_EVAL_MOTIF_IDS
    tapes, truth_rows = _validate_heldout_tapes(
        heldout_tapes,
        slot_order=slot_order,
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
        attempt_id=expected_attempt_id,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
    )
    required_wrapper_fields = {
        "schema", "test_only", "run_name", "attempt_id", "seed", "arm",
        "original_slot_index", "admission_receipt_sha256", "admission_binding", "implementation_commit",
        "source_conformance_sha256", "literal_binding_spec_sha256",
        "checkpoint_inventory", "source_evaluations_sha256", "slot_packet_schema",
        "policy_decisions", "policy_curves", "execution_mode_records",
        "evaluation_join_records", "literal_nulls", "counts", "scientific_branch",
        "scientific_polarity", "promotion_eligible", "b2_extension_trigger",
        "result_body_sha256",
    }
    all_rows: list[dict[str, Any]] = []
    all_curves: list[dict[str, Any]] = []
    all_modes: list[dict[str, Any]] = []
    all_joins: list[dict[str, Any]] = []
    expected_result_schema = (
        _POLICY_REPLAY_TEST_RESULT_SCHEMA if test_only else _POLICY_REPLAY_RESULT_SCHEMA
    )
    expected_packet_schema = ONE_SLOT_TEST_ONLY_SCHEMA if test_only else ONE_SLOT_FORMAL_SCHEMA
    for (seed, arm), wrapper in zip(slot_order, results, strict=True):
        if not isinstance(wrapper, Mapping) or set(wrapper) != required_wrapper_fields:
            raise B1MetricsPolicyAssemblyError("policy replay result wrapper schema differs")
        slot_index = B1_SLOT_ORDER.index((seed, arm))
        body = {name: wrapper[name] for name in wrapper if name != "result_body_sha256"}
        body_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
        if wrapper["result_body_sha256"] != body_sha:
            raise B1MetricsPolicyAssemblyError("policy replay result SHA drift")
        if (
            wrapper["schema"] != expected_result_schema
            or wrapper["test_only"] is not test_only
            or wrapper["run_name"] != B1_RUN_NAME
            or wrapper["attempt_id"] != expected_attempt_id
            or wrapper["seed"] != seed
            or wrapper["arm"] != arm
            or wrapper["original_slot_index"] != slot_index
            or wrapper["implementation_commit"] != expected_implementation_commit
            or wrapper["source_conformance_sha256"] != expected_source_conformance_sha256
            or wrapper["literal_binding_spec_sha256"] != literal_binding_spec_sha256
            or wrapper["slot_packet_schema"] != expected_packet_schema
        ):
            raise B1MetricsPolicyAssemblyError("policy replay result identity/source differs")
        _require_digest("admission receipt", wrapper["admission_receipt_sha256"])
        admission = wrapper["admission_binding"]
        admission_fields = {
            "schema", "attempt_id", "run_name", "seed", "arm",
            "implementation_commit", "source_conformance_sha256", "receipt_sha256",
            "available_physical_bytes", "effective_available_bytes",
        }
        if (
            not isinstance(admission, Mapping)
            or set(admission) != admission_fields
            or admission["schema"] != "cbsc_omrc_b01_b1_bound_admission_v1"
            or admission["attempt_id"] != expected_attempt_id
            or admission["run_name"] != B1_RUN_NAME
            or admission["seed"] != seed
            or admission["arm"] != arm
            or admission["implementation_commit"] != expected_implementation_commit
            or admission["source_conformance_sha256"] != expected_source_conformance_sha256
            or admission["receipt_sha256"] != wrapper["admission_receipt_sha256"]
            or type(admission["available_physical_bytes"]) is not int
            or type(admission["effective_available_bytes"]) is not int
            or admission["available_physical_bytes"] < 4 * 1024**3
            or admission["effective_available_bytes"] < 4 * 1024**3
        ):
            raise B1MetricsPolicyAssemblyError("policy replay admission binding differs")
        _require_digest("source evaluations", wrapper["source_evaluations_sha256"])
        inventory = wrapper["checkpoint_inventory"]
        if not isinstance(inventory, list) or len(inventory) != 4:
            raise B1MetricsPolicyAssemblyError("policy replay checkpoint inventory differs")
        expected_checkpoint_shas: dict[int, str] = {}
        for update, record in zip(B1_CHECKPOINT_UPDATES, inventory, strict=True):
            if not isinstance(record, Mapping) or set(record) != {"update", "path", "sha256"}:
                raise B1MetricsPolicyAssemblyError("policy replay checkpoint binding differs")
            if record["update"] != update:
                raise B1MetricsPolicyAssemblyError("policy replay checkpoint order differs")
            expected_checkpoint_shas[update] = _require_digest(
                "checkpoint", record["sha256"]
            )
        packet = {
            "schema": expected_packet_schema,
            "test_only": test_only,
            "run_name": B1_RUN_NAME,
            "attempt_id": expected_attempt_id,
            "seed": seed,
            "arm": arm,
            "original_slot_index": slot_index,
            "policy_decisions": wrapper["policy_decisions"],
            "policy_curves": wrapper["policy_curves"],
            "execution_mode_records": wrapper["execution_mode_records"],
            "evaluation_join_records": wrapper["evaluation_join_records"],
            "literal_nulls": wrapper["literal_nulls"],
            "scientific_branch": wrapper["scientific_branch"],
            "scientific_polarity": wrapper["scientific_polarity"],
            "promotion_eligible": wrapper["promotion_eligible"],
            "b2_extension_trigger": wrapper["b2_extension_trigger"],
            "counts": wrapper["counts"],
        }
        validated = validate_one_slot_policy_packet(
            packet,
            expected_attempt_id=expected_attempt_id,
            expected_seed=seed,
            expected_arm=arm,
            expected_slot_index=slot_index,
            test_only=test_only,
        )
        for join in validated["evaluation_join_records"]:
            if join["checkpoint_sha256"] != expected_checkpoint_shas[join["checkpoint_update"]]:
                raise B1MetricsPolicyAssemblyError(
                    "policy replay dual-fact/checkpoint identity differs"
                )
        all_rows.extend(validated["policy_decisions"])
        all_curves.extend(validated["policy_curves"])
        all_modes.extend(validated["execution_mode_records"])
        all_joins.extend(validated["evaluation_join_records"])
    all_rows.sort(key=lambda row: tuple(row[name] for name in POLICY_RECORD_KEY_FIELDS))
    _exact_policy_coverage(
        all_rows,
        slot_order=slot_order,
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
    )
    all_curves.sort(key=lambda row: tuple(row[name] for name in POLICY_CURVE_KEY_FIELDS))
    curve_keys = [tuple(row[name] for name in POLICY_CURVE_KEY_FIELDS) for row in all_curves]
    if len(curve_keys) != len(set(curve_keys)):
        raise B1MetricsPolicyAssemblyError("policy replay curve key is duplicated")
    all_modes = _validate_execution_mode_records_for_slots(all_modes, slot_order=slot_order)
    expected_join_keys = [
        (0, seed, ARMS.index(arm), update)
        for seed, arm in slot_order
        for update in B1_CHECKPOINT_UPDATES
    ]
    observed_join_keys = [
        (row["run_order"], row["seed"], row["arm_order"], row["checkpoint_update"])
        for row in all_joins
    ]
    if observed_join_keys != expected_join_keys:
        raise B1MetricsPolicyAssemblyError("policy replay dual-fact join order differs")
    support = build_policy_support_signature_counts(all_rows, truth_rows)
    support_total = sum(row["support_count"] for row in support)
    expected_rows = TEST_ONLY_POLICY_DECISION_COUNT if test_only else FORMAL_POLICY_DECISION_COUNT
    expected_curves = TEST_ONLY_POLICY_CURVE_COUNT if test_only else FORMAL_POLICY_CURVE_COUNT
    expected_modes = TEST_ONLY_EXECUTION_MODE_RECORD_COUNT if test_only else 48
    if (
        len(all_rows) != expected_rows
        or len(all_curves) != expected_curves
        or len(all_modes) != expected_modes
        or len(all_joins) != expected_modes
        or support_total != expected_rows
    ):
        raise B1MetricsPolicyAssemblyError("policy replay aggregate cardinality differs")
    return {
        "schema": (
            POLICY_REPLAY_TEST_AGGREGATE_SCHEMA if test_only else POLICY_REPLAY_AGGREGATE_SCHEMA
        ),
        "test_only": test_only,
        "formal_policy_coverage_satisfied": not test_only,
        "formal_readiness_authority": False,
        "run_name": B1_RUN_NAME,
        "attempt_id": expected_attempt_id,
        "policy_decisions": all_rows,
        "policy_curves": all_curves,
        "execution_mode_records": all_modes,
        "evaluation_join_records": all_joins,
        "policy_support_signature_counts": support,
        "counts": {
            "worker_results": len(results),
            "heldout_tapes": len(tapes),
            "policy_decisions": len(all_rows),
            "policy_curves": len(all_curves),
            "execution_mode_records": len(all_modes),
            "evaluation_join_records": len(all_joins),
            "policy_support_total": support_total,
        },
    }


def _exact_policy_coverage(
    rows: list[dict[str, Any]],
    *,
    slot_order: tuple[tuple[int, str], ...],
    stochastic_ids: tuple[int, ...],
    motif_ids: tuple[int, ...],
) -> None:
    arm_order = {arm: index for index, arm in enumerate(ARMS)}
    expected = sorted(
        (
            0,
            seed,
            update,
            split_order,
            tape_id,
            opportunity,
            arm_order[arm],
        )
        for seed, arm in slot_order
        for update in B1_CHECKPOINT_UPDATES
        for split_order, ids in ((1, stochastic_ids), (2, motif_ids))
        for tape_id in ids
        for opportunity in range(24)
    )
    observed = [tuple(row[name] for name in POLICY_RECORD_KEY_FIELDS) for row in rows]
    if observed != expected:
        raise B1MetricsPolicyAssemblyError(
            "policy rows are missing, duplicated, injected, or reordered"
        )


def assemble_b1_metrics_policy_tables(
    *,
    staging_root: Path,
    grouped_raw_slices: Sequence[Sequence[Mapping[str, Any]]],
    heldout_tapes: Sequence[EpisodeTape],
    expected_attempt_id: str,
    expected_implementation_commit: str,
    expected_source_conformance_sha256: str,
    literal_binding_spec_sha256: str,
    test_only: bool = False,
) -> dict[str, Any]:
    """Assemble exact policy rows/curves/supports from checkpoint bytes only."""

    if type(test_only) is not bool:
        raise B1MetricsPolicyAssemblyError("test_only must be literal bool")
    if type(expected_attempt_id) is not str or not expected_attempt_id:
        raise B1MetricsPolicyAssemblyError("expected attempt identity is absent")
    _require_digest("implementation commit", expected_implementation_commit, 40)
    _require_digest("source conformance", expected_source_conformance_sha256)
    _require_digest("literal binding specification", literal_binding_spec_sha256)
    root = Path(staging_root).resolve(strict=True)
    if not root.is_dir():
        raise B1MetricsPolicyAssemblyError("canonical staging root is not a directory")
    slot_order = _TEST_SLOT_ORDER if test_only else B1_SLOT_ORDER
    stochastic_ids = _TEST_STOCHASTIC_IDS if test_only else B1_EVAL_STOCHASTIC_IDS
    motif_ids = _TEST_MOTIF_IDS if test_only else B1_EVAL_MOTIF_IDS
    if not isinstance(grouped_raw_slices, Sequence) or isinstance(
        grouped_raw_slices, (str, bytes, bytearray)
    ) or len(grouped_raw_slices) != len(slot_order):
        raise B1MetricsPolicyAssemblyError("grouped raw slice slot coverage differs")
    tapes, truth_rows = _validate_heldout_tapes(
        heldout_tapes,
        slot_order=slot_order,
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
        attempt_id=expected_attempt_id,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
    )
    policy_rows: list[dict[str, Any]] = []
    execution_mode_records: list[dict[str, Any]] = []
    for (seed, arm), raw_group in zip(
        slot_order, grouped_raw_slices, strict=True
    ):
        index = B1_SLOT_ORDER.index((seed, arm))
        slices = _validate_group_identity(
            raw_group,
            seed=seed,
            arm=arm,
            attempt_id=expected_attempt_id,
            implementation_commit=expected_implementation_commit,
            source_conformance_sha256=expected_source_conformance_sha256,
        )
        records = _checkpoint_records(slices)
        seed_tapes = tuple(tape for tape in tapes if tape.identity.seed == seed)
        slot_policy_rows, slot_mode_records = _policy_rows_for_slot(
            staging_root=root,
            slot_index=index,
            seed=seed,
            arm=arm,
            checkpoint_records=records,
            tapes=seed_tapes,
            attempt_id=expected_attempt_id,
            implementation_commit=expected_implementation_commit,
            source_conformance_sha256=expected_source_conformance_sha256,
        )
        policy_rows.extend(slot_policy_rows)
        execution_mode_records.extend(slot_mode_records)
    execution_mode_records = validate_execution_mode_records(
        execution_mode_records, test_only=test_only
    )
    policy_rows.sort(key=lambda row: tuple(row[name] for name in POLICY_RECORD_KEY_FIELDS))
    _exact_policy_coverage(
        policy_rows,
        slot_order=slot_order,
        stochastic_ids=stochastic_ids,
        motif_ids=motif_ids,
    )
    curves = build_complete_policy_curves(policy_rows)
    curve_keys = [tuple(row[name] for name in POLICY_CURVE_KEY_FIELDS) for row in curves]
    if curve_keys != sorted(curve_keys) or len(curve_keys) != len(set(curve_keys)):
        raise B1MetricsPolicyAssemblyError("policy curves are duplicated or reordered")
    support = build_policy_support_signature_counts(policy_rows, truth_rows)
    support_total = sum(row["support_count"] for row in support)
    expected_rows = (
        len(slot_order)
        * len(B1_CHECKPOINT_UPDATES)
        * (len(stochastic_ids) + len(motif_ids))
        * 24
    )
    expected_curves = len(slot_order) * (len(stochastic_ids) + len(motif_ids))
    if (
        len(policy_rows) != expected_rows
        or len(curves) != expected_curves
        or support_total != expected_rows
    ):
        raise B1MetricsPolicyAssemblyError("assembled policy table cardinality differs")
    if not test_only and (
        expected_rows != FORMAL_POLICY_DECISION_COUNT
        or expected_curves != FORMAL_POLICY_CURVE_COUNT
    ):
        raise AssertionError("formal B1 policy cardinality constants differ")
    if test_only and (
        expected_rows != TEST_ONLY_POLICY_DECISION_COUNT
        or expected_curves != TEST_ONLY_POLICY_CURVE_COUNT
        or len(execution_mode_records) != TEST_ONLY_EXECUTION_MODE_RECORD_COUNT
    ):
        raise AssertionError("TEST_ONLY B1 policy profile cardinality differs")
    return {
        "schema": B1_METRICS_POLICY_ASSEMBLY_SCHEMA,
        "profile_schema": (
            TEST_ONLY_POLICY_PROFILE_SCHEMA
            if test_only
            else FORMAL_POLICY_PROFILE_SCHEMA
        ),
        "test_only": test_only,
        "formal_policy_coverage_satisfied": not test_only,
        "formal_readiness_authority": False,
        "run_name": B1_RUN_NAME,
        "attempt_id": expected_attempt_id,
        "execution_mode_records": execution_mode_records,
        "policy_decisions": policy_rows,
        "policy_curves": curves,
        "policy_support_signature_counts": support,
        "counts": {
            "arm_seed_slots": len(slot_order),
            "checkpoints": len(slot_order) * len(B1_CHECKPOINT_UPDATES),
            "heldout_tapes": len(tapes),
            "execution_mode_records": len(execution_mode_records),
            "policy_decisions": len(policy_rows),
            "policy_curves": len(curves),
            "policy_support_total": support_total,
        },
    }


__all__ = [
    "B1_METRICS_POLICY_ASSEMBLY_SCHEMA",
    "B1MetricsPolicyAssemblyError",
    "FORMAL_POLICY_PROFILE_SCHEMA",
    "FORMAL_POLICY_CURVE_COUNT",
    "FORMAL_POLICY_DECISION_COUNT",
    "ONE_SLOT_EXECUTION_MODE_RECORD_COUNT",
    "ONE_SLOT_FORMAL_POLICY_CURVE_COUNT",
    "ONE_SLOT_FORMAL_POLICY_DECISION_COUNT",
    "ONE_SLOT_FORMAL_SCHEMA",
    "ONE_SLOT_TEST_ONLY_SCHEMA",
    "POLICY_REPLAY_AGGREGATE_SCHEMA",
    "POLICY_REPLAY_TEST_AGGREGATE_SCHEMA",
    "TEST_ONLY_EXECUTION_MODE_RECORD_COUNT",
    "TEST_ONLY_POLICY_CURVE_COUNT",
    "TEST_ONLY_POLICY_DECISION_COUNT",
    "TEST_ONLY_POLICY_PROFILE_SCHEMA",
    "assemble_b1_metrics_policy_tables",
    "aggregate_b1_policy_replay_results",
    "assemble_one_slot_policy_tables",
    "validate_execution_mode_records",
    "validate_one_slot_policy_packet",
]
