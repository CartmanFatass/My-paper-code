"""Package EVENT_HELD_COMMITMENT_LINK_G0 contract, smoke, train, eval, analysis."""

from __future__ import annotations

import argparse
import base64
import binascii
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from time import perf_counter, time_ns
from typing import Any, Mapping
import zlib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.event_held_commitment_link import (
    ArmName,
    ACTION_COUNT,
    CREATE,
    KEEP,
    MARK_DIM,
    RENEW,
    RNG_NAMES,
    authoritative_seed_map,
    collect_trajectory,
    collection_rng_schedules,
    compare_continuations,
    factor_counts,
    fork_opportunities_batched,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    make_rng_binding,
    batched_natural_and_permuted_action_tv,
    nested_state_maximum_difference,
    optimize_update,
    optimizer_ownership_manifest,
    owned_rng_states,
    parameter_and_optimizer_counts,
    replay_errors,
    replay_rng_schedule_end_state,
    replay_rng_schedule_arrays,
    replay_trajectory,
    runtime_rng_snapshot,
    save_checkpoint,
    validate_replay,
    validate_rng_binding,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    ADDED_PARAMETER_COUNT,
    EVENT_JOINT_FACTOR_COUNT,
    FORMAL_EVAL_EPISODES,
    FORMAL_EXECUTION_BACKEND,
    FORMAL_NUM_ENVS,
    FORMAL_TRAIN_EPISODES,
    FORMAL_UPDATES,
    HORIZON,
    MAX_LIFECYCLES,
    NATURAL_FORK_REPLICATES,
    NATURAL_FORK_QUOTA_PER_ACTION,
    NATURAL_FORK_SELECTION_COORDINATE,
    OPTIMIZER_CLIP_EPSILON,
    OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
    OPTIMIZER_NORM_ATOL,
    OPTIMIZER_NORM_RTOL,
    OPTIMIZER_LOSS_ATOL,
    OPTIMIZER_LOSS_RTOL,
    REGISTERED_CONTRACT,
    REGISTERED_EXECUTION_BACKENDS,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_EVENT_JOINT_RATIO_FIELDS,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    REPLAY_LOG_COMPONENT_ATOL,
    REPLAY_LOG_COMPONENT_FIELDS,
    REPLAY_LOG_COMPONENT_RTOL,
    REPLAY_LOG_RATIO_DRIFT_CAP,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_STATE_ATOL,
    REPLAY_STATE_FIELDS,
    REPLAY_WORST_RECORD_FIELDS,
    RNG_BINDING_SCHEMA_VERSION,
    PPO_PASSES,
    VALUE_COEFFICIENT,
    PRIMITIVE_ENTROPY_COEFFICIENT,
    EVENT_ENTROPY_COEFFICIENT,
    PARAMETER_COUNT,
    make_rng,
    make_noncalendar_ledger,
    registered_contract,
    require_registered_backend,
    select_result_branch,
)

FORMAL_AUTHORIZATION = "AUTHORIZE_EVENT_HELD_COMMITMENT_LINK_G0_FORMAL"
TRAIN_MANIFEST_SCHEMA = 6
TRAIN_INDEX_SCHEMA = 2
TRAIN_UPDATE_SCHEMA = 2
# 2: the replay record is the named per-factor error dictionary plus the
# derived joint bounds actually applied and a normalized pass result, not a
# single `maximum_error` scalar. Collapsing them hid which factor moved.
EVALUATION_MANIFEST_SCHEMA = 4
EVALUATION_CELL_SCHEMA = 7
FORMAL_TRAIN_ARTIFACT_SCHEMA = "event_held_commitment_link_g0.formal_train.v6"
FORMAL_TRAIN_INDEX_SCHEMA = "event_held_commitment_link_g0.formal_train.index.v2"
FORMAL_TRAIN_UPDATE_SCHEMA = "event_held_commitment_link_g0.formal_train.update.v2"
FORMAL_EVALUATION_MANIFEST_SCHEMA = "event_held_commitment_link_g0.formal_evaluation_manifest.v4"
FORMAL_EVALUATION_ARTIFACT_SCHEMA = "event_held_commitment_link_g0.formal_evaluation.v7"
FORMAL_ANALYSIS_ARTIFACT_SCHEMA = "event_held_commitment_link_g0.formal_analysis.v4"
EXERCISE_TRAIN_ARTIFACT_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.train.v5"
EXERCISE_TRAIN_INDEX_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.train.index.v2"
EXERCISE_TRAIN_UPDATE_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.train.update.v2"
EXERCISE_EVALUATION_MANIFEST_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.evaluation_manifest.v3"
EXERCISE_EVALUATION_ARTIFACT_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.evaluation.v5"
EXERCISE_MANIFEST_SCHEMA = "event_held_commitment_link_g0.formal_path_exercise.manifest.v2"
ARMS: tuple[ArmName, ...] = ("OR", "DUM", "EHC")
FORK_STREAM_NAMES = ("opportunity", "event", "mark", "primitive")
EVALUATION_CELLS = (
    ("iid", True, "iid_deterministic"),
    ("iid", False, "iid_stochastic"),
    ("held_out", True, "held_out_deterministic"),
    ("held_out", False, "held_out_stochastic"),
)
LIFECYCLE_COUNT_KEYS = frozenset({
    "create", "keep", "renew", "categorical", "mark",
    "invalid_segment_lifetimes", "segment_count",
})
FINITE_CHECK_KEYS = frozenset({
    "old_log_probs", "old_values", "hidden_after", "prefix_counts",
    "event_inputs", "event_old_cat_logp",
    "event_old_mark_component_logp", "event_old_joint_logp",
})
REDUCTION_COUNT_KEYS = frozenset({
    "keep", "renew", "non_create", "multi_opportunity_lifecycles",
    "intervention_values",
})
PAIRED_TENSOR_KEYS = frozenset({
    "observations", "active_mask", "orders", "actions", "old_log_probs",
    "old_values", "hidden_before", "hidden_after", "prefix_counts",
    "rewards", "terminal",
})

_BASE_PARAMETER_SPECS = (
    ("base.member_encoder.0.weight", (32, 15)),
    ("base.member_encoder.0.bias", (32,)),
    ("base.member_encoder.2.weight", (32, 32)),
    ("base.member_encoder.2.bias", (32,)),
    ("base.context_encoder.0.weight", (32, 33)),
    ("base.context_encoder.0.bias", (32,)),
    ("base.actor_rnn.weight_ih", (96, 67)),
    ("base.actor_rnn.weight_hh", (96, 32)),
    ("base.actor_rnn.bias_ih", (96,)),
    ("base.actor_rnn.bias_hh", (96,)),
    ("base.action_head.0.weight", (32, 35)),
    ("base.action_head.0.bias", (32,)),
    ("base.action_head.2.weight", (3, 32)),
    ("base.action_head.2.bias", (3,)),
    ("base.critic.0.weight", (32, 41)),
    ("base.critic.0.bias", (32,)),
    ("base.critic.2.weight", (1, 32)),
    ("base.critic.2.bias", (1,)),
)
_COMMITMENT_BASE_SPECS = (("W_z.weight", (3, 8)),)
_EVENT_PARAMETER_SPECS = (
    ("event_head.weight", (2, 87)),
    ("event_head.bias", (2,)),
    ("mark_head.weight", (16, 87)),
    ("mark_head.bias", (16,)),
)


def _json_default(value: Any) -> Any:
    """Encode one unsupported leaf without recursively copying its container."""

    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "__dict__"):
        return vars(value)
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


def _write_json(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(
                value, handle, indent=2, ensure_ascii=False,
                default=_json_default,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _owned_rng_equal(left: Any, right: Any, names: tuple[str, ...]) -> bool:
    return all(
        repr(left.rngs[name].bit_generator.state)
        == repr(right.rngs[name].bit_generator.state)
        for name in names
    )


def _no_op_equal(ordinary: Any, dummy: Any) -> bool:
    return all(
        torch.equal(getattr(ordinary, name), getattr(dummy, name))
        for name in (
            "observations", "active_mask", "orders", "actions",
            "old_log_probs", "old_values", "hidden_before", "hidden_after",
            "prefix_counts", "rewards", "terminal",
        )
    )


REPLAY_RECORD_KEYS = frozenset(
    {
        "schema_version", "errors", "likelihood_components", "joints",
        "event_joint_ratio", "log_component_atol", "log_component_rtol",
        "ratio_drift_cap", "state_atol", "failures", "passed",
    }
)
# Relative slack for the record's own internal algebra. The reported numbers
# are float64 selections of float64 quantities, so the equalities below hold
# to a few ulps; this is a rounding allowance, never a tolerance on evidence.
RECORD_CONSISTENCY_RELATIVE = 1e-9
RECORD_CONSISTENCY_ABSOLUTE = 1e-15


def _finite_leaves(record: Any) -> bool:
    """Every numeric leaf of a replay record is finite.

    `nan > tol` and `nan > 0.0` are both false, so a record carrying NaN
    satisfies every ordinary threshold test. Non-finiteness is therefore
    checked explicitly and first, in both the validator and the merge.
    """

    def visit(value: Any, *, key: str = "") -> bool:
        if key == "coordinate":
            return value is None or (
                isinstance(value, list)
                and all(type(index) is int and index >= 0 for index in value)
            )
        if isinstance(value, dict):
            return all(visit(child, key=str(name)) for name, child in value.items())
        if isinstance(value, (list, tuple)):
            return all(visit(child) for child in value)
        if isinstance(value, bool) or value is None or isinstance(value, str):
            return True
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError):
            return False

    return isinstance(record, dict) and visit(record)


def _record_severity(record: dict[str, Any]) -> float:
    if record["coordinate"] is None:
        return -1.0
    return max(
        float(record["absolute_error"]) / max(float(record["mixed_bound"]), 1e-300),
        float(record["ratio_drift"]) / REPLAY_LOG_RATIO_DRIFT_CAP,
    )


def merge_replay_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Worst-case merge of several replay records into one, factor by factor.

    Used where one cell or one update covers several validated batches. Each
    named error keeps its own maximum; each derived joint keeps the batch
    that produced the largest joint error, so the reported bound is still
    the bound that reported error was tested against, while `excess` takes
    the maximum over every batch. The three assembly numbers move together
    from the batch with the largest `assembly_excess`, so the merged record
    keeps `assembly_excess == assembly_residual - assembly_allowance`.
    Nothing is reduced to a single scalar.

    Merging is fail-closed on non-finiteness. Python's `max(0.0, nan)`
    returns `0.0` while `max(nan, 0.0)` returns `nan`, so a plain maximum
    would launder a NaN batch out of the evidence depending on batch order.
    """

    if not records:
        raise ValueError("replay merge requires at least one record")
    non_finite = [
        index for index, record in enumerate(records) if not _finite_leaves(record)
    ]
    if non_finite:
        raise ValueError(f"replay merge received non-finite records {non_finite}")
    constant_keys = (
        "schema_version", "log_component_atol", "log_component_rtol",
        "ratio_drift_cap", "state_atol",
    )
    if any(
        any(record[key] != records[0][key] for key in constant_keys)
        for record in records[1:]
    ):
        raise ValueError("replay records disagree on schema or numerical constants")
    errors = {
        name: max(float(record["errors"][name]) for record in records)
        for name in records[0]["errors"]
    }
    joints: dict[str, dict[str, float]] = {}
    for name in REPLAY_JOINT_FIELDS:
        worst = max(records, key=lambda record: float(record["joints"][name]["error"]))
        merged = {key: float(value) for key, value in worst["joints"][name].items()}
        merged["excess"] = max(
            float(record["joints"][name]["excess"]) for record in records
        )
        merged["float64_error"] = max(
            float(record["joints"][name]["float64_error"]) for record in records
        )
        assembly = max(
            records, key=lambda record: float(record["joints"][name]["assembly_excess"])
        )
        for key in ("assembly_residual", "assembly_allowance", "assembly_excess"):
            merged[key] = float(assembly["joints"][name][key])
        merged["rows"] = float(
            sum(float(record["joints"][name]["rows"]) for record in records)
        )
        joints[name] = merged
    likelihood_components = {
        name: dict(max(records, key=lambda record: _record_severity(
            record["likelihood_components"][name]
        ))["likelihood_components"][name])
        for name in REPLAY_LOG_COMPONENT_FIELDS
    }
    event_joint_ratio = dict(max(
        records,
        key=lambda record: float(record["event_joint_ratio"]["ratio_drift"]),
    )["event_joint_ratio"])
    failures = sorted(
        {name for record in records for name in record["failures"]}
    )
    return {
        "schema_version": records[0]["schema_version"],
        "errors": errors,
        "likelihood_components": likelihood_components,
        "joints": joints,
        "event_joint_ratio": event_joint_ratio,
        "log_component_atol": records[0]["log_component_atol"],
        "log_component_rtol": records[0]["log_component_rtol"],
        "ratio_drift_cap": records[0]["ratio_drift_cap"],
        "state_atol": records[0]["state_atol"],
        "failures": failures,
        "passed": all(bool(record["passed"]) for record in records),
    }


def _consistent(left: float, right: float) -> bool:
    """`left == right` up to the record's own float64 rounding."""

    return abs(left - right) <= (
        RECORD_CONSISTENCY_ABSOLUTE
        + RECORD_CONSISTENCY_RELATIVE * max(abs(left), abs(right))
    )


def _joint_factor_error_cap(name: str, errors: dict[str, Any], joint: dict[str, Any]) -> float:
    """Largest `component_sum` the recorded per-factor errors can support.

    `component_sum` is a per-row sum of per-factor replay differences, and
    every factor of both joints is covered by a recorded per-factor maximum
    -- the event joint's out-of-support factors only because
    `categorical_support_leak`/`mark_support_leak` force them to be exactly
    zero on both sides. Without this link a record could declare an
    arbitrarily wide `bound` (`component_sum + allowance`) and validate any
    error beneath it.
    """

    if name == "event_joint":
        return float(errors["categorical_component"]) + float(
            EVENT_JOINT_FACTOR_COUNT - 1
        ) * float(errors["mark_component"])
    return float(joint["factor_count"]) * float(errors["primitive_component"])


def _ordered_float32_encoding(value: np.float32) -> int:
    bits = int(value.view(np.uint32))
    return bits ^ (0xFFFFFFFF if bits & 0x80000000 else 0x80000000)


def _recompute_ulp(stored: float, replayed: float) -> tuple[float, int]:
    stored32, replayed32 = np.float32(stored), np.float32(replayed)
    reference = stored32 if abs(float(stored32)) >= abs(float(replayed32)) else replayed32
    direction = np.float32(np.inf if not np.signbit(reference) else -np.inf)
    neighbor = np.nextafter(reference, direction, dtype=np.float32)
    return (
        abs(float(np.float64(neighbor) - np.float64(reference))),
        abs(_ordered_float32_encoding(stored32) - _ordered_float32_encoding(replayed32)),
    )


def _likelihood_record_valid(
    record: Any, *, dimensions: int, empty_allowed: bool
) -> bool:
    if not isinstance(record, dict) or set(record) != set(REPLAY_WORST_RECORD_FIELDS):
        return False
    coordinate = record.get("coordinate")
    if coordinate is None:
        return empty_allowed and all(
            float(record[name]) == 0.0
            for name in (
                "stored_value", "replayed_value", "absolute_error",
                "mixed_bound", "ratio_drift", "float32_ulp_at_max_magnitude",
                "ulp_distance",
            )
        ) and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
    if not (
        isinstance(coordinate, list)
        and len(coordinate) == dimensions
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    stored = float(record["stored_value"])
    replayed = float(record["replayed_value"])
    absolute_error = abs(replayed - stored)
    mixed_bound = REPLAY_LOG_COMPONENT_ATOL + REPLAY_LOG_COMPONENT_RTOL * max(
        abs(stored), abs(replayed)
    )
    ratio_drift = abs(math.expm1(replayed - stored))
    spacing, distance = _recompute_ulp(stored, replayed)
    return bool(
        _consistent(float(record["absolute_error"]), absolute_error)
        and _consistent(float(record["mixed_bound"]), mixed_bound)
        and _consistent(float(record["ratio_drift"]), ratio_drift)
        and float(record["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
        and float(record["float32_ulp_at_max_magnitude"]) == spacing
        and int(record["ulp_distance"]) == distance
        and absolute_error <= mixed_bound
        and ratio_drift <= REPLAY_LOG_RATIO_DRIFT_CAP
    )


def _replay_record_valid(record: Any, *, event_rows_required: bool = True) -> bool:
    """Fail-closed check of one serialized replay record.

    Re-derives acceptance from the record itself rather than trusting its
    `passed` flag: every numeric leaf must be finite, exact fields must be
    exactly zero, ordinary continuous components must sit at or below the
    registered component tolerance, and each derived joint must sit at or
    below its own compositional bound and match its float64 assembly. A
    record missing any named factor, or any named key of a joint, fails.

    The joint block must also be internally consistent -- `bound` really the
    sum of its own `component_sum` and `allowance`, `excess` dominating
    `error - bound`, the assembly triple self-consistent, and
    `component_sum` no larger than the recorded per-factor errors allow --
    and must have examined a positive number of rows. `event_rows_required`
    is false only for the ordinary source arm, which carries no event head
    and therefore legitimately produces an all-zero event joint.
    """

    if not isinstance(record, dict) or set(record) != REPLAY_RECORD_KEYS:
        return False
    errors = record.get("errors")
    joints = record.get("joints")
    if not isinstance(errors, dict) or not isinstance(joints, dict):
        return False
    if set(errors) != set(
        REPLAY_EXACT_FIELDS + REPLAY_COMPONENT_FIELDS + REPLAY_JOINT_FIELDS
    ):
        return False
    if set(joints) != set(REPLAY_JOINT_FIELDS):
        return False
    if any(
        not isinstance(joints[name], dict)
        or set(joints[name]) != set(REPLAY_JOINT_RECORD_FIELDS)
        for name in REPLAY_JOINT_FIELDS
    ):
        return False
    try:
        if not _finite_leaves(record):
            return False
    except (TypeError, ValueError):
        return False
    if (
        record.get("schema_version") != REPLAY_RECORD_SCHEMA_VERSION
        or float(record.get("log_component_atol", float("nan"))) != REPLAY_LOG_COMPONENT_ATOL
        or float(record.get("log_component_rtol", float("nan"))) != REPLAY_LOG_COMPONENT_RTOL
        or float(record.get("ratio_drift_cap", float("nan"))) != REPLAY_LOG_RATIO_DRIFT_CAP
        or float(record.get("state_atol", float("nan"))) != REPLAY_STATE_ATOL
    ):
        return False
    if record.get("passed") is not True or record.get("failures"):
        return False
    if any(float(errors[name]) != 0.0 for name in REPLAY_EXACT_FIELDS):
        return False
    if any(not float(errors[name]) <= REPLAY_STATE_ATOL for name in REPLAY_STATE_FIELDS):
        return False
    likelihood_components = record.get("likelihood_components")
    if not isinstance(likelihood_components, dict) or set(likelihood_components) != set(
        REPLAY_LOG_COMPONENT_FIELDS
    ):
        return False
    if not _likelihood_record_valid(
        likelihood_components["primitive_component"], dimensions=3,
        empty_allowed=False,
    ):
        return False
    for name, dimensions in (("categorical_component", 3), ("mark_component", 4)):
        if not _likelihood_record_valid(
            likelihood_components[name], dimensions=dimensions,
            empty_allowed=not event_rows_required,
        ):
            return False
    event_ratio = record.get("event_joint_ratio")
    if not isinstance(event_ratio, dict) or set(event_ratio) != set(
        REPLAY_EVENT_JOINT_RATIO_FIELDS
    ):
        return False
    coordinate = event_ratio.get("coordinate")
    if coordinate is None:
        if event_rows_required or any(
            float(event_ratio[name]) != 0.0
            for name in ("stored_value", "replayed_value", "ratio_drift")
        ):
            return False
    elif not (
        isinstance(coordinate, list) and len(coordinate) == 3
        and all(type(index) is int and index >= 0 for index in coordinate)
    ):
        return False
    else:
        recomputed_ratio = abs(math.expm1(
            float(event_ratio["replayed_value"]) - float(event_ratio["stored_value"])
        ))
        if not (
            _consistent(float(event_ratio["ratio_drift"]), recomputed_ratio)
            and float(event_ratio["ratio_cap"]) == REPLAY_LOG_RATIO_DRIFT_CAP
            and recomputed_ratio <= REPLAY_LOG_RATIO_DRIFT_CAP
        ):
            return False
    if coordinate is None and float(event_ratio["ratio_cap"]) != REPLAY_LOG_RATIO_DRIFT_CAP:
        return False
    for name in REPLAY_JOINT_FIELDS:
        joint = {key: float(value) for key, value in joints[name].items()}
        if any(
            joint[key] < 0.0
            for key in (
                "error", "component_sum", "allowance", "bound", "factor_count",
                "float64_error", "assembly_residual", "assembly_allowance",
                "rows",
            )
        ):
            return False
        if not joint["excess"] <= 0.0 or not joint["assembly_excess"] <= 0.0:
            return False
        if not float(errors[name]) <= joint["bound"]:
            return False
        if not _consistent(joint["bound"], joint["component_sum"] + joint["allowance"]):
            return False
        # `excess` is the per-row maximum of `error - bound` while `error`
        # and `bound` are read at the largest-error row, so it dominates
        # rather than equals their difference.
        if joint["excess"] < joint["error"] - joint["bound"] - (
            RECORD_CONSISTENCY_ABSOLUTE
            + RECORD_CONSISTENCY_RELATIVE * abs(joint["bound"])
        ):
            return False
        if not _consistent(
            joint["assembly_excess"],
            joint["assembly_residual"] - joint["assembly_allowance"],
        ):
            return False
        cap = _joint_factor_error_cap(name, errors, joint)
        if joint["component_sum"] > cap + (
            RECORD_CONSISTENCY_ABSOLUTE + RECORD_CONSISTENCY_RELATIVE * abs(cap)
        ):
            return False
        if joint["rows"] <= 0.0:
            # An all-zero joint proves nothing was examined. The one lawful
            # case is the event joint of an arm with no event head, which
            # must then be all-zero rather than merely row-less.
            if name != "event_joint" or event_rows_required:
                return False
            if any(value != 0.0 for value in joint.values()):
                return False
        elif name == "event_joint" and joint["factor_count"] != float(
            EVENT_JOINT_FACTOR_COUNT
        ):
            return False
    return True


def _digest_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        default=_json_default,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _tensor_digest(value: torch.Tensor) -> str:
    tensor = value.detach().cpu().contiguous()
    digest = hashlib.sha256()
    digest.update(str(tensor.dtype).encode("ascii"))
    digest.update(np.asarray(tensor.shape, dtype=np.int64).tobytes())
    digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def _owned_stream_digests(state: Any) -> dict[str, str]:
    return {
        name: _digest_json(state.rngs[name].bit_generator.state)
        for name in RNG_NAMES
    }


def _initial_rng_states(seed_map: Mapping[str, int]) -> dict[str, Any]:
    return {
        name: deepcopy(np.random.default_rng(int(seed_map[name])).bit_generator.state)
        for name in RNG_NAMES
    }


def _collection_rng_bindings(
    *, context: Mapping[str, Any], seed_map: Mapping[str, int],
    start_states: Mapping[str, Any], end_states: Mapping[str, Any],
    trajectory: Any, deterministic: bool,
) -> dict[str, dict[str, Any]]:
    schedules = collection_rng_schedules(
        trajectory, deterministic=deterministic
    )
    return {
        name: make_rng_binding(
            context=context,
            stream=name,
            seed=int(seed_map[name]),
            start_state=start_states[name],
            draw_schedule=schedules[name],
            expected_end_state=end_states[name],
        )
        for name in RNG_NAMES
    }


def _rng_bindings_valid(
    bindings: Any, *, expected_context: Mapping[str, Any],
    seed_map: Mapping[str, int], expected_starts: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    if not isinstance(bindings, dict) or set(bindings) != set(RNG_NAMES):
        return False, {}
    end_states: dict[str, Any] = {}
    integer_context_fields = {
        "replicate", "update", "batch", "episode_id", "time", "key",
        "membership_epoch", "segment_id",
    }
    for name in RNG_NAMES:
        binding = bindings[name]
        context = binding.get("context") if isinstance(binding, dict) else None
        if not isinstance(context, dict) or any(
            field in context and not _is_exact_int(context[field])
            for field in integer_context_fields
        ):
            return False, {}
        valid, end_state = validate_rng_binding(
            binding,
            expected_context=expected_context,
            expected_stream=name,
            expected_seed=int(seed_map[name]),
            expected_start_state=expected_starts[name],
        )
        if not valid or end_state is None:
            return False, {}
        end_states[name] = end_state
    return True, end_states


def _collection_binding_schedules_valid(
    bindings: Mapping[str, Any], *, deterministic: bool,
    lifecycle_counts: Mapping[str, Any], environment_count: int,
) -> bool:
    try:
        schedules = {
            name: bindings[name]["draw_schedule"] for name in RNG_NAMES
        }
        if not schedules["ledger"] or not schedules["order"]:
            return False
        opportunity_total = sum(
            int(entry["shape"][0]) for entry in schedules["opportunity"]
        )
        expected_requests = sum(
            int(lifecycle_counts[name]) for name in ("create", "keep", "renew")
        )
        if opportunity_total != expected_requests:
            return False
        if deterministic:
            return not (
                schedules["event"] or schedules["mark"]
                or schedules["primitive"]
            )
        event_total = sum(int(entry["shape"][0]) for entry in schedules["event"])
        mark_total = sum(int(entry["shape"][0]) for entry in schedules["mark"])
        primitive = schedules["primitive"]
        if not (
            event_total == mark_total == opportunity_total
            and len(primitive) == HORIZON
            and all(
                entry["shape"] == [environment_count, MAX_LIFECYCLES]
                and entry["operation"] == "random"
                and entry["dtype"] == "float32"
                and _is_exact_int(entry["coordinates"]["time"])
                and entry["coordinates"]["time"] == index
                for index, entry in enumerate(primitive)
            )
            and [entry["coordinates"] for entry in schedules["event"]]
            == [entry["coordinates"] for entry in schedules["mark"]]
            == [entry["coordinates"] for entry in schedules["opportunity"]]
        ):
            return False
        for stream, operation, dtype in (
            ("event", "random", "float64"),
            ("mark", "standard_normal", "float64"),
            ("opportunity", "choice_opportunity", "int64"),
        ):
            times = [
                entry["coordinates"]["time"]
                for entry in schedules[stream]
            ]
            if not (
                all(_is_exact_int(value) for value in times)
                and times == sorted(times)
                and len(times) == len(set(times))
                and all(0 <= value < HORIZON for value in times)
                and all(
                    entry["operation"] == operation and entry["dtype"] == dtype
                    for entry in schedules[stream]
                )
            ):
                return False
        return True
    except (KeyError, TypeError, ValueError, IndexError):
        return False


def _ledger_record(ledger: Any) -> dict[str, Any]:
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
    return payload | {"ledger_digest": _digest_json(payload)}


def _rng_audit_evidence_valid(
    evidence: Any, bindings: Mapping[str, Any], *, arm: str, profile: str,
    seed_map: Mapping[str, int], deterministic: bool,
    episode_ids: list[int],
    ledger_cache: dict[tuple[Any, ...], tuple[dict[str, Any], list[Any]]] | None = None,
) -> bool:
    try:
        if not isinstance(evidence, dict) or set(evidence) != {
            "streams", "request_evidence", "ledgers"
        }:
            return False
        streams = evidence["streams"]
        if set(streams) != set(RNG_NAMES) or any(
            streams[name] != bindings[name]["draw_schedule"] for name in RNG_NAMES
        ):
            return False
        cache_key = (
            profile, int(seed_map["ledger"]), int(seed_map["order"]),
            tuple(int(value) for value in episode_ids),
        )
        cached = ledger_cache.get(cache_key) if ledger_cache is not None else None
        if cached is None:
            regenerated_trace = {name: [] for name in RNG_NAMES}
            regenerated_ledgers = [
                make_noncalendar_ledger(
                    episode_id, profile=profile,
                    task_seed=int(seed_map["ledger"]),
                    order_seed=int(seed_map["order"]),
                    audit_trace=regenerated_trace,
                )
                for episode_id in episode_ids
            ]
            if ledger_cache is not None:
                ledger_cache[cache_key] = (regenerated_trace, regenerated_ledgers)
        else:
            regenerated_trace, regenerated_ledgers = cached
        if evidence["ledgers"] != [
            _ledger_record(ledger) for ledger in regenerated_ledgers
        ]:
            return False
        if streams["ledger"] != regenerated_trace["ledger"] or streams["order"] != regenerated_trace["order"]:
            return False
        requests_by_time: dict[int, list[list[int]]] = {}
        frontier_by_time: dict[int, list[list[int]]] = {}
        rows = evidence["request_evidence"]
        if len(rows) != HORIZON:
            return False
        for expected_time, row in enumerate(rows):
            if set(row) != {"time", "environments"} or not (
                _is_exact_int(row["time"]) and row["time"] == expected_time
            ):
                return False
            environments = row["environments"]
            if len(environments) != len(episode_ids):
                return False
            expected_requests: list[list[int]] = []
            frontier_orders: list[list[int]] = []
            for env_index, env in enumerate(environments):
                if set(env) != {"env_index", "episode_id", "frontier"} or not (
                    _is_exact_int(env["env_index"])
                    and _is_exact_int(env["episode_id"])
                    and env["env_index"] == env_index
                    and env["episode_id"] == episode_ids[env_index]
                ):
                    return False
                frontier = env["frontier"]
                if any(set(value) != {"key", "priority", "q_before"} for value in frontier):
                    return False
                if any(not _is_exact_int(value["key"]) for value in frontier):
                    return False
                keys = [value["key"] for value in frontier]
                if len(keys) != len(set(keys)) or keys != [
                    value["key"] for value in sorted(
                        frontier, key=lambda value: float(value["priority"])
                    )
                ]:
                    return False
                ledger = regenerated_ledgers[env_index]
                if any(
                    float(value["priority"])
                    != float(ledger.direct_frontier_priorities[expected_time, value["key"]])
                    for value in frontier
                ):
                    return False
                frontier_orders.append(keys)
                if arm == "OR":
                    if any(value["q_before"] is not None for value in frontier):
                        return False
                else:
                    for value in frontier:
                        q = int(value["q_before"])
                        if q <= 0:
                            expected_requests.append([
                                env_index, int(value["key"]), CREATE if q < 0 else KEEP
                            ])
            requests_by_time[expected_time] = expected_requests
            frontier_by_time[expected_time] = frontier_orders
        for stream in ("event", "mark", "opportunity"):
            if any(
                not _is_exact_int(entry["coordinates"]["time"])
                for entry in streams[stream]
            ):
                return False
            actual = {
                entry["coordinates"]["time"]: entry["coordinates"]["requests"]
                for entry in streams[stream]
            }
            expected = {
                time: requests for time, requests in requests_by_time.items()
                if requests
            }
            if stream in ("event", "mark") and deterministic:
                expected = {}
            if actual != expected:
                return False
        primitive_expected = {} if deterministic else {
            time: {
                "time": time, "episode_ids": episode_ids,
                "frontier_orders": frontier_by_time[time],
            }
            for time in range(HORIZON)
        }
        if any(
            not _is_exact_int(entry["coordinates"]["time"])
            for entry in streams["primitive"]
        ):
            return False
        primitive_actual = {
            entry["coordinates"]["time"]: entry["coordinates"]
            for entry in streams["primitive"]
        }
        return primitive_actual == primitive_expected
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def _expected_parameter_counts(arm: str) -> dict[str, int]:
    commitment_bias = MARK_DIM * ACTION_COUNT if arm != "OR" else 0
    return {
        "base_model": PARAMETER_COUNT,
        "added_model": 0 if arm == "OR" else ADDED_PARAMETER_COUNT,
        "base_optimizer": PARAMETER_COUNT + commitment_bias,
        "event_optimizer": (
            0 if arm == "OR" else ADDED_PARAMETER_COUNT - commitment_bias
        ),
    }


def _expected_optimizer_manifest(arm: str) -> dict[str, Any]:
    def records(specs: tuple[tuple[str, tuple[int, ...]], ...]) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "shape": list(shape),
                "numel": int(math.prod(shape)),
            }
            for name, shape in specs
        ]

    base_specs = _BASE_PARAMETER_SPECS + (
        _COMMITMENT_BASE_SPECS if arm != "OR" else ()
    )
    return {
        "schema_version": OPTIMIZER_EVIDENCE_SCHEMA_VERSION,
        "arm": arm,
        "groups": {
            "base": records(base_specs),
            "event": records(_EVENT_PARAMETER_SPECS if arm != "OR" else ()),
        },
    }


def _optimizer_pass_valid(
    record: Any, *, group: str, pass_index: int, step_before: int,
    manifest: list[dict[str, Any]],
) -> tuple[bool, dict[str, int]]:
    required = {
        "schema_version", "group", "pass_index", "step_before", "step_after",
        "raw_loss", "loss_components", "unclipped_norm", "clip_coefficient",
        "parameters", "payload_raw_bytes", "payload_encoded_bytes",
        "record_digest",
    }
    if not isinstance(record, dict) or set(record) != required:
        return False, {}
    unsigned = {key: deepcopy(value) for key, value in record.items()
                if key != "record_digest"}
    if not (
        record["schema_version"] == OPTIMIZER_EVIDENCE_SCHEMA_VERSION
        and record["group"] == group
        and int(record["pass_index"]) == pass_index
        and int(record["step_before"]) == step_before
        and int(record["step_after"]) == step_before + 1
        and record["record_digest"] == _digest_json(unsigned)
        and isinstance(record["parameters"], list)
        and len(record["parameters"]) == len(manifest)
    ):
        return False, {}
    loss = float(record["raw_loss"])
    norm = float(record["unclipped_norm"])
    coefficient = float(record["clip_coefficient"])
    if not all(math.isfinite(value) for value in (loss, norm, coefficient)):
        return False, {}
    components = record["loss_components"]
    if group == "base":
        if not isinstance(components, dict) or set(components) != {
            "policy_loss", "value_loss", "primitive_entropy"
        }:
            return False, {}
        recomputed_loss = (
            float(components["policy_loss"])
            + VALUE_COEFFICIENT * float(components["value_loss"])
            - PRIMITIVE_ENTROPY_COEFFICIENT * float(components["primitive_entropy"])
        )
    else:
        if not isinstance(components, dict) or set(components) != {
            "event_policy_loss", "categorical_entropy"
        }:
            return False, {}
        recomputed_loss = (
            float(components["event_policy_loss"])
            - EVENT_ENTROPY_COEFFICIENT * float(components["categorical_entropy"])
        )
    if not (
        all(math.isfinite(float(value)) for value in components.values())
        and math.isclose(
            loss, recomputed_loss,
            rel_tol=OPTIMIZER_LOSS_RTOL, abs_tol=OPTIMIZER_LOSS_ATOL,
        )
    ):
        return False, {}
    if norm < 0.0:
        return False, {}
    expected_coefficient = min(
        1.0, 0.5 / (norm + OPTIMIZER_CLIP_EPSILON)
    )
    if coefficient != expected_coefficient:
        return False, {}
    squared_sum = 0.0
    non_none = zero_tensors = nonfinite_values = 0
    parameter_keys = {
        "name", "shape", "numel", "dtype", "gradient_present",
        "nonfinite_count", "zero_count", "squared_l2", "maxabs",
        "preclip_gradient_digest",
        "gradient_payload",
    }
    raw_bytes = encoded_bytes = 0
    for summary, owner in zip(record["parameters"], manifest, strict=True):
        if not isinstance(summary, dict) or set(summary) != parameter_keys:
            return False, {}
        try:
            numel = int(summary["numel"])
            nonfinite = int(summary["nonfinite_count"])
            zeros = int(summary["zero_count"])
            squared = float(summary["squared_l2"])
            maximum = float(summary["maxabs"])
        except (TypeError, ValueError, OverflowError):
            return False, {}
        payload = summary["gradient_payload"]
        if summary["gradient_present"] is not True or not isinstance(payload, dict) or set(payload) != {
            "encoding", "dtype", "shape", "uncompressed_nbytes", "data"
        }:
            return False, {}
        try:
            compressed = base64.b64decode(payload["data"], validate=True)
            raw = zlib.decompress(compressed)
            array = np.frombuffer(raw, dtype=np.dtype(payload["dtype"])).reshape(
                tuple(int(value) for value in payload["shape"])
            )
        except (ValueError, TypeError, zlib.error, binascii.Error):
            return False, {}
        derived_nonfinite = int((~np.isfinite(array)).sum())
        derived_zeros = int((array == 0).sum())
        derived_squared = float(np.square(array.astype(np.float64)).sum())
        derived_maximum = float(np.abs(array.astype(np.float64)).max()) if array.size else 0.0
        derived_digest = hashlib.sha256(raw).hexdigest()
        raw_bytes += len(raw)
        encoded_bytes += len(payload["data"].encode("ascii"))
        if not (
            summary["name"] == owner["name"]
            and summary["shape"] == owner["shape"]
            and numel == owner["numel"]
            and summary["dtype"] == "<f4"
            and payload["encoding"] == "zlib9_base64"
            and payload["dtype"] == "<f4"
            and payload["shape"] == owner["shape"]
            and int(payload["uncompressed_nbytes"]) == owner["numel"] * 4
            and len(raw) == owner["numel"] * 4
            and 0 <= nonfinite <= numel
            and 0 <= zeros <= numel
            and nonfinite == 0
            and math.isfinite(squared) and squared >= 0.0
            and math.isfinite(maximum) and maximum >= 0.0
            and _is_sha256(summary["preclip_gradient_digest"])
            and nonfinite == derived_nonfinite
            and zeros == derived_zeros
            and squared == derived_squared
            and maximum == derived_maximum
            and summary["preclip_gradient_digest"] == derived_digest
            and ((zeros == numel) == (squared == 0.0 and maximum == 0.0))
        ):
            return False, {}
        squared_sum += squared
        non_none += 1
        zero_tensors += int(zeros == numel)
        nonfinite_values += nonfinite
    if not (
        int(record["payload_raw_bytes"]) == raw_bytes
        and int(record["payload_encoded_bytes"]) == encoded_bytes
    ):
        return False, {}
    recomputed_norm = math.sqrt(squared_sum)
    if not math.isclose(
        norm, recomputed_norm,
        rel_tol=OPTIMIZER_NORM_RTOL, abs_tol=OPTIMIZER_NORM_ATOL,
    ):
        return False, {}
    return True, {
        "non_none": non_none,
        "zero_tensors": zero_tensors,
        "nonfinite_values": nonfinite_values,
    }


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_exact_int(value: Any) -> bool:
    return type(value) is int


def _exact_int_fields(value: Any, fields: tuple[str, ...]) -> bool:
    return bool(
        isinstance(value, dict)
        and all(field in value and _is_exact_int(value[field]) for field in fields)
    )


def _tensor_pair_record(left: torch.Tensor, right: torch.Tensor) -> dict[str, Any]:
    left_cpu, right_cpu = left.detach().cpu(), right.detach().cpu()
    mismatch = torch.ne(left_cpu, right_cpu)
    maximum = (
        float((left_cpu.double() - right_cpu.double()).abs().max())
        if left_cpu.numel() else 0.0
    )
    return {
        "left_digest": _tensor_digest(left_cpu),
        "right_digest": _tensor_digest(right_cpu),
        "mismatch_count": int(mismatch.sum()),
        "maximum_absolute_error": maximum,
    }


def _paired_update_evidence(
    trajectories: dict[str, Any], states: dict[str, Any], *, base_noop_error: float
) -> dict[str, Any]:
    fields = (
        "observations", "active_mask", "orders", "actions", "old_log_probs",
        "old_values", "hidden_before", "hidden_after", "prefix_counts",
        "rewards", "terminal",
    )
    def rng_pairs(left: str, right: str, names: tuple[str, ...]) -> dict[str, Any]:
        left_digests = _owned_stream_digests(states[left])
        right_digests = _owned_stream_digests(states[right])
        return {
            name: {"left": left_digests[name], "right": right_digests[name]}
            for name in names
        }
    return {
        "or_dum_tensors": {
            name: _tensor_pair_record(
                getattr(trajectories["OR"], name),
                getattr(trajectories["DUM"], name),
            )
            for name in fields
        },
        "or_dum_rng": rng_pairs(
            "OR", "DUM", ("ledger", "order", "primitive")
        ),
        "dum_ehc_rng": rng_pairs("DUM", "EHC", RNG_NAMES),
        "base_noop_error": float(base_noop_error),
    }


def _finite_checks(trajectory: Any) -> dict[str, int]:
    names = (
        "old_log_probs", "old_values", "hidden_after", "prefix_counts",
        "event_inputs", "event_old_cat_logp",
        "event_old_mark_component_logp", "event_old_joint_logp",
    )
    return {
        name: int((~torch.isfinite(getattr(trajectory, name))).sum())
        for name in names
    }


def _lifecycle_counts(trajectory: Any) -> dict[str, int]:
    counts = factor_counts(trajectory)
    return counts | {
        "invalid_segment_lifetimes": sum(
            int(record.active_lifetime < 1)
            for rows in trajectory.segments for record in rows
        ),
        "segment_count": sum(len(rows) for rows in trajectory.segments),
    }


def _paired_evidence_valid(record: Any, arms: Mapping[str, Any]) -> bool:
    if not isinstance(record, dict) or set(record) != {
        "or_dum_tensors", "or_dum_rng", "dum_ehc_rng", "base_noop_error"
    }:
        return False
    tensors = record["or_dum_tensors"]
    if not isinstance(tensors, dict) or set(tensors) != PAIRED_TENSOR_KEYS:
        return False
    for value in tensors.values():
        if set(value) != {
            "left_digest", "right_digest", "mismatch_count",
            "maximum_absolute_error",
        } or not (
            value["left_digest"] == value["right_digest"]
            and int(value["mismatch_count"]) == 0
            and float(value["maximum_absolute_error"]) == 0.0
        ):
            return False
    for family, expected in (
        ("or_dum_rng", {"ledger", "order", "primitive"}),
        ("dum_ehc_rng", set(RNG_NAMES)),
    ):
        values = record[family]
        if set(values) != expected or any(
            set(pair) != {"left", "right"}
            or not _is_sha256(pair["left"])
            or not _is_sha256(pair["right"])
            or pair["left"] != pair["right"]
            for pair in values.values()
        ):
            return False
    try:
        for name, pair in record["or_dum_rng"].items():
            if not (
                pair["left"] == arms["OR"]["owned_stream_digests"][name]
                and pair["right"] == arms["DUM"]["owned_stream_digests"][name]
            ):
                return False
        for name, pair in record["dum_ehc_rng"].items():
            if not (
                pair["left"] == arms["DUM"]["owned_stream_digests"][name]
                and pair["right"] == arms["EHC"]["owned_stream_digests"][name]
            ):
                return False
    except (KeyError, TypeError):
        return False
    return float(record["base_noop_error"]) == 0.0


def _training_update_valid(
    record: Any, *, update: int, replicate: int,
    formal: bool = True, mode: str = "formal_train",
    rng_starts: Mapping[str, Mapping[str, Any]] | None = None,
    validated_rng_ends: dict[str, dict[str, Any]] | None = None,
    ledger_cache: dict[tuple[Any, ...], tuple[dict[str, Any], list[Any]]] | None = None,
) -> bool:
    if not isinstance(record, dict) or set(record) != {"update", "arms", "paired"}:
        return False
    if not _is_exact_int(record["update"]) or record["update"] != update or set(record["arms"]) != set(ARMS):
        return False
    if not _paired_evidence_valid(record["paired"], record["arms"]):
        return False
    for arm in ARMS:
        evidence = record["arms"][arm]
        if set(evidence) != {
            "arm", "seed_map", "owned_stream_digests", "rng_bindings",
            "rng_evidence", "replay",
            "lifecycle_counts", "finite_checks", "exposure", "optimizer",
            "parameter_counts",
        }:
            return False
        exposure = evidence["exposure"]
        if set(exposure) != {"before", "delta", "after"} or any(
            set(exposure[name]) != {"base", "event"}
            for name in exposure
        ):
            return False
        expected_event = 0 if arm == "OR" else PPO_PASSES
        expected_base_gradient_tensors = 18 if arm == "OR" else 19
        expected_event_gradient_tensors = 0 if arm == "OR" else 4
        expected_base_zero_gradients = 1 if arm == "DUM" else 0
        expected_before = {
            "base": (update - 1) * PPO_PASSES,
            "event": 0 if arm == "OR" else (update - 1) * PPO_PASSES,
        }
        expected_after = {
            "base": update * PPO_PASSES,
            "event": 0 if arm == "OR" else update * PPO_PASSES,
        }
        parameter_counts = evidence["parameter_counts"]
        optimizer = evidence["optimizer"]
        gradient_keys = (
            "base_non_none_gradients", "base_zero_gradients",
            "base_nonfinite_gradient_values", "base_nonfinite_loss_values",
            "base_nonfinite_norm_values", "event_non_none_gradients",
            "event_zero_gradients", "event_nonfinite_gradient_values",
            "event_nonfinite_loss_values", "event_nonfinite_norm_values",
        )
        expected_starts = (
            dict(rng_starts[arm]) if rng_starts is not None and arm in rng_starts
            else _initial_rng_states(evidence["seed_map"]) if update == 1
            else None
        )
        rng_context = {
            "domain": "training", "mode": mode, "formal": bool(formal),
            "replicate": int(replicate), "arm": arm, "update": int(update),
        }
        rng_valid, rng_ends = (
            _rng_bindings_valid(
                evidence["rng_bindings"], expected_context=rng_context,
                seed_map=evidence["seed_map"], expected_starts=expected_starts,
            )
            if expected_starts is not None else (False, {})
        )
        manifest = _expected_optimizer_manifest(arm)
        base_passes = optimizer.get("base_passes", [])
        event_passes = optimizer.get("event_passes", [])
        storage = optimizer.get("evidence_storage", {})
        base_summaries: list[dict[str, int]] = []
        event_summaries: list[dict[str, int]] = []
        pass_records_valid = (
            optimizer.get("ownership_manifest") == manifest
            and isinstance(base_passes, list) and len(base_passes) == PPO_PASSES
            and isinstance(event_passes, list) and len(event_passes) == expected_event
        )
        if pass_records_valid:
            for index, pass_record in enumerate(base_passes):
                valid, summary = _optimizer_pass_valid(
                    pass_record, group="base", pass_index=index + 1,
                    step_before=expected_before["base"] + index,
                    manifest=manifest["groups"]["base"],
                )
                pass_records_valid = pass_records_valid and valid
                base_summaries.append(summary)
            for index, pass_record in enumerate(event_passes):
                valid, summary = _optimizer_pass_valid(
                    pass_record, group="event", pass_index=index + 1,
                    step_before=expected_before["event"] + index,
                    manifest=manifest["groups"]["event"],
                )
                pass_records_valid = pass_records_valid and valid
                event_summaries.append(summary)
        if not (
            evidence["arm"] == arm
            and evidence["seed_map"]
            == authoritative_seed_map("train", replicate)
            and set(evidence["owned_stream_digests"]) == set(RNG_NAMES)
            and rng_valid
            and _collection_binding_schedules_valid(
                evidence["rng_bindings"], deterministic=False,
                lifecycle_counts=evidence["lifecycle_counts"],
                environment_count=FORMAL_NUM_ENVS,
            )
            and _rng_audit_evidence_valid(
                evidence["rng_evidence"], evidence["rng_bindings"],
                arm=arm, profile="train", seed_map=evidence["seed_map"],
                deterministic=False,
                episode_ids=list(range(
                    (update - 1) * FORMAL_NUM_ENVS,
                    update * FORMAL_NUM_ENVS,
                )),
                ledger_cache=ledger_cache,
            )
            and all(
                evidence["owned_stream_digests"][name]
                == _digest_json(rng_ends[name])
                for name in RNG_NAMES
            )
            and set(evidence["lifecycle_counts"]) == LIFECYCLE_COUNT_KEYS
            and set(evidence["finite_checks"]) == FINITE_CHECK_KEYS
            and _replay_record_valid(
                evidence["replay"], event_rows_required=arm != "OR"
            )
            and evidence["lifecycle_counts"]["invalid_segment_lifetimes"] == 0
            and (
                arm == "OR"
                or evidence["lifecycle_counts"]["categorical"]
                == evidence["lifecycle_counts"]["keep"]
                + evidence["lifecycle_counts"]["renew"]
            )
            and (
                arm == "OR"
                or evidence["lifecycle_counts"]["mark"]
                == evidence["lifecycle_counts"]["create"]
                + evidence["lifecycle_counts"]["renew"]
            )
            and all(int(value) == 0 for value in evidence["finite_checks"].values())
            and exposure["delta"] == {"base": PPO_PASSES, "event": expected_event}
            and exposure["before"] == expected_before
            and exposure["after"] == expected_after
            and set(optimizer) == {
                "base_steps", "event_steps", "primitive_replays",
                "event_head_replays", "packed_trajectory_count", *gradient_keys,
                "ownership_manifest", "base_passes", "event_passes",
                "evidence_storage",
            }
            and pass_records_valid
            and set(storage) == {
                "raw_bytes", "encoded_bytes",
                "formal_scale_projected_encoded_bytes",
            }
            and int(storage["raw_bytes"]) == sum(
                int(value["payload_raw_bytes"])
                for value in base_passes + event_passes
            )
            and int(storage["encoded_bytes"]) == sum(
                int(value["payload_encoded_bytes"])
                for value in base_passes + event_passes
            )
            and int(storage["formal_scale_projected_encoded_bytes"])
            == int(storage["encoded_bytes"]) * FORMAL_UPDATES
            and optimizer["base_steps"] == PPO_PASSES
            and optimizer["event_steps"] == expected_event
            and optimizer["primitive_replays"] == PPO_PASSES
            and optimizer["event_head_replays"] == expected_event
            and optimizer["packed_trajectory_count"] == 1
            and all(len(optimizer[name]) == PPO_PASSES for name in gradient_keys[:5])
            and all(len(optimizer[name]) == expected_event for name in gradient_keys[5:])
            and all(
                int(value) == summary.get("non_none", -1)
                for value, summary in zip(
                    optimizer["base_non_none_gradients"], base_summaries,
                    strict=True,
                )
            )
            and all(
                int(value) == summary.get("zero_tensors", -1)
                for value, summary in zip(
                    optimizer["base_zero_gradients"], base_summaries,
                    strict=True,
                )
            )
            and all(
                int(value) == summary.get("nonfinite_values", -1)
                for value, summary in zip(
                    optimizer["base_nonfinite_gradient_values"], base_summaries,
                    strict=True,
                )
            )
            and all(int(value) == 0 for name in gradient_keys[3:5] for value in optimizer[name])
            and (
                expected_event == 0
                or all(
                    int(value) == summary.get("non_none", -1)
                    for value, summary in zip(
                        optimizer["event_non_none_gradients"], event_summaries,
                        strict=True,
                    )
                )
            )
            and all(
                int(value) == summary.get("zero_tensors", -1)
                for value, summary in zip(
                    optimizer["event_zero_gradients"], event_summaries,
                    strict=True,
                )
            )
            and all(
                int(value) == summary.get("nonfinite_values", -1)
                for value, summary in zip(
                    optimizer["event_nonfinite_gradient_values"], event_summaries,
                    strict=True,
                )
            )
            and all(int(value) == 0 for name in gradient_keys[8:] for value in optimizer[name])
            and parameter_counts == _expected_parameter_counts(arm)
        ):
            return False
        if validated_rng_ends is not None:
            validated_rng_ends[arm] = rng_ends
    return (
        record["arms"]["DUM"]["parameter_counts"]
        == record["arms"]["EHC"]["parameter_counts"]
    )


def _expected_fork_stream_consumption(
    *, stream: str, start_state: Mapping[str, Any],
    schedule: list[dict[str, Any]], seed: int, env_index: int,
) -> dict[str, Any]:
    """Derive the exact focal-row bytes consumed by a Stage-2 fork."""

    arrays, end_state = replay_rng_schedule_arrays(
        start_state, schedule, seed=seed
    )
    digest = hashlib.sha256()
    position = 0
    for entry, array in zip(schedule, arrays, strict=True):
        if stream == "primitive":
            selected = np.asarray(array)[env_index]
        else:
            requests = entry["coordinates"]["requests"]
            selected_indices = [
                index for index, request in enumerate(requests)
                if int(request[0]) == env_index
            ]
            selected = np.asarray(array)[selected_indices]
        flat = np.ascontiguousarray(selected).reshape(-1)
        digest.update(flat.tobytes(order="C"))
        position += int(flat.size)
    return {
        "position": position,
        "consumed_bytes_digest": digest.hexdigest(),
        "terminal_state": end_state,
    }


def _natural_fork_valid(
    record: Any, *, replicate: int, episodes: list[dict[str, Any]],
    cell_batches: list[dict[str, Any]], formal: bool = True,
    mode: str = "formal_evaluate",
) -> bool:
    required_keys = {
        "schema", "replicate", "quota_per_action", "eligible_keys",
        "selected_keys", "execution", "fork_rows",
    }
    if not isinstance(record, dict) or set(record) not in (
        required_keys, required_keys | {"telemetry"},
    ):
        return False
    if not (
        record["schema"] == "event_held_commitment_link_g0.natural_fork.v5"
        and _is_exact_int(record["replicate"])
        and record["replicate"] == replicate
        and _is_exact_int(record["quota_per_action"])
        and record["quota_per_action"] == NATURAL_FORK_QUOTA_PER_ACTION
        and set(record["eligible_keys"]) == {"KEEP", "RENEW"}
        and set(record["selected_keys"]) == {"KEEP", "RENEW"}
        and isinstance(record["fork_rows"], list)
    ):
        return False
    execution = record["execution"]
    if not isinstance(execution, dict) or set(execution) != {
        "engine", "registered_width", "selected_pairs", "collector_calls",
    } or not _exact_int_fields(
        execution, ("registered_width", "selected_pairs", "collector_calls")
    ):
        return False
    selected_flat: list[tuple[Any, ...]] = []
    quota_shortfall = any(
        len(record["eligible_keys"][action]) < NATURAL_FORK_QUOTA_PER_ACTION
        for action in ("KEEP", "RENEW")
    )
    for action_index, action in enumerate(("KEEP", "RENEW")):
        try:
            eligible = [tuple(value) for value in record["eligible_keys"][action]]
            selected = [tuple(value) for value in record["selected_keys"][action]]
        except TypeError:
            return False
        if any(
            len(value) != 8 or value[-1] != action
            or any(not _is_exact_int(coordinate) for coordinate in value[:-1])
            for value in eligible
        ):
            return False
        if any(
            len(value) != 8 or value[-1] != action
            or any(not _is_exact_int(coordinate) for coordinate in value[:-1])
            for value in selected
        ):
            return False
        if eligible != sorted(eligible) or len(set(eligible)) != len(eligible):
            return False
        expected: list[tuple[Any, ...]] = []
        if not quota_shortfall:
            rng = make_rng(
                BOOTSTRAP_SEED,
                NATURAL_FORK_SELECTION_COORDINATE,
                replicate,
                action_index,
            )
            expected = [
                eligible[index] for index in sorted(
                    int(value) for value in rng.choice(
                        len(eligible), size=NATURAL_FORK_QUOTA_PER_ACTION,
                        replace=False,
                    )
                )
            ]
        if selected != expected:
            return False
        selected_flat.extend(selected)
    if any(
        not isinstance(row, dict) or not _is_exact_int(row.get("episode_id"))
        for row in episodes
    ):
        return False
    utilities = {row["episode_id"]: float(row["utility"]) for row in episodes}
    rows_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    required = {
        "replicate", "base_episode_id", "episode_id", "sign_parity", "time",
        "key", "membership_epoch", "segment_id", "natural_action",
        "batch_index", "env_index",
        "fork_id", "keep_utility", "renew_utility", "natural_utility",
        "advantage", "natural_errors", "rng_bindings", "stream_consumption",
        "end_rng_digests",
    }
    for row in record["fork_rows"]:
        if not isinstance(row, dict) or set(row) != required:
            return False
        if not _exact_int_fields(row, (
            "replicate", "base_episode_id", "episode_id", "sign_parity", "time",
            "key", "membership_epoch", "segment_id", "batch_index", "env_index",
        )):
            return False
        key = _natural_fork_key(row)
        if key in rows_by_key or key not in selected_flat:
            return False
        try:
            keep = float(row["keep_utility"])
            renew = float(row["renew_utility"])
            natural = float(row["natural_utility"])
            advantage = float(row["advantage"])
        except (TypeError, ValueError):
            return False
        expected_natural = keep if row["natural_action"] == "KEEP" else renew
        expected_advantage = keep - renew if row["natural_action"] == "KEEP" else renew - keep
        natural_errors = row["natural_errors"]
        rng_digests = row["end_rng_digests"]
        batch_index = row["batch_index"]
        env_index = row["env_index"]
        binding_families = row["rng_bindings"]
        rng_binding_valid = (
            0 <= batch_index < len(cell_batches)
            and env_index == int(row["episode_id"]) % FORMAL_NUM_ENVS
            and batch_index == int(row["episode_id"]) // FORMAL_NUM_ENVS
            and isinstance(binding_families, dict)
            and set(binding_families) == {"KEEP", "RENEW"}
        )
        branch_ends: dict[str, dict[str, Any]] = {}
        branch_schedules: dict[str, dict[str, Any]] = {}
        branch_consumption: dict[str, dict[str, Any]] = {}
        if rng_binding_valid:
            cell_bindings = cell_batches[batch_index].get("rng_bindings", {})
            seed_map = authoritative_seed_map("held_out", replicate)
            for branch_action in ("KEEP", "RENEW"):
                expected_starts: dict[str, Any] = {}
                expected_tails: dict[str, list[dict[str, Any]]] = {}
                for name in RNG_NAMES:
                    cell_binding = cell_bindings.get(name, {})
                    full_schedule = cell_binding.get("draw_schedule", [])
                    prefix_schedule = [
                        entry for entry in full_schedule
                        if int(entry.get("coordinates", {}).get("time", -1))
                        < int(row["time"])
                    ]
                    expected_tails[name] = [
                        entry for entry in full_schedule
                        if int(entry.get("coordinates", {}).get("time", -1))
                        >= int(row["time"])
                    ]
                    try:
                        expected_starts[name] = replay_rng_schedule_end_state(
                            cell_binding["start_state"], prefix_schedule,
                            seed=int(seed_map[name]),
                        )
                    except (KeyError, TypeError, ValueError):
                        rng_binding_valid = False
                        break
                if not rng_binding_valid:
                    break
                context = {
                    "domain": "stage2", "mode": mode,
                    "formal": formal, "replicate": int(replicate), "arm": "EHC",
                    "cell": "held_out_stochastic", "batch": batch_index,
                    "fork_id": str(row["fork_id"]),
                    "episode_id": int(row["episode_id"]),
                    "time": int(row["time"]), "key": int(row["key"]),
                    "membership_epoch": int(row["membership_epoch"]),
                    "segment_id": int(row["segment_id"]),
                    "natural_action": str(row["natural_action"]),
                    "branch_action": branch_action,
                }
                valid, ends = _rng_bindings_valid(
                    binding_families[branch_action], expected_context=context,
                    seed_map=seed_map, expected_starts=expected_starts,
                )
                rng_binding_valid = rng_binding_valid and valid
                rng_binding_valid = rng_binding_valid and all(
                    binding_families[branch_action][name]["draw_schedule"]
                    == expected_tails[name]
                    for name in RNG_NAMES
                )
                branch_ends[branch_action] = ends
                branch_schedules[branch_action] = {
                    name: binding_families[branch_action][name]["draw_schedule"]
                    for name in RNG_NAMES
                }
                try:
                    branch_consumption[branch_action] = {
                        name: _expected_fork_stream_consumption(
                            stream=name,
                            start_state=expected_starts[name],
                            schedule=expected_tails[name],
                            seed=int(seed_map[name]),
                            env_index=env_index,
                        )
                        for name in FORK_STREAM_NAMES
                    }
                except (KeyError, TypeError, ValueError, IndexError):
                    rng_binding_valid = False
            rng_binding_valid = rng_binding_valid and (
                branch_ends.get("KEEP") == branch_ends.get("RENEW")
                and branch_schedules.get("KEEP") == branch_schedules.get("RENEW")
                and isinstance(row["stream_consumption"], dict)
                and set(row["stream_consumption"]) == {"KEEP", "RENEW"}
                and row["stream_consumption"] == branch_consumption
                and branch_consumption.get("KEEP")
                == branch_consumption.get("RENEW")
                and all(
                    rng_digests.get(name)
                    == _digest_json(branch_ends["KEEP"][name])
                    for name in RNG_NAMES
                )
            )
        if not (
            all(math.isfinite(value) for value in (keep, renew, natural, advantage))
            and row["episode_id"]
            == 2 * row["base_episode_id"] + row["sign_parity"]
            and natural == expected_natural
            and natural == utilities.get(int(row["episode_id"]))
            and advantage == expected_advantage
            and isinstance(row["fork_id"], str) and bool(row["fork_id"])
            and row["fork_id"] == _digest_json(list(key))
            and set(natural_errors) == {
                "discrete_mismatch", "continuous_error", "segment_equal",
                "outcome_equal",
            }
            and int(natural_errors["discrete_mismatch"]) == 0
            and float(natural_errors["continuous_error"]) <= 1e-7
            and natural_errors["segment_equal"] is True
            and natural_errors["outcome_equal"] is True
            and set(rng_digests) == set(RNG_NAMES)
            and rng_binding_valid
        ):
            return False
        rows_by_key[key] = row
    selected_count = len(selected_flat)
    expected_calls = sum(
        math.ceil(count / 8)
        for count in Counter(key[3] for key in selected_flat).values()
    )
    return bool(
        set(rows_by_key) == set(selected_flat)
        and execution["engine"] == "registered_width_batched_v1"
        and execution["registered_width"] == FORMAL_NUM_ENVS
        and execution["selected_pairs"] == selected_count
        and execution["collector_calls"] == expected_calls
    )


def _reject_monolithic_operational_records(
    training_manifest: dict[str, Any],
    evaluation_payloads: dict[tuple[int, str, str], dict[str, Any]],
    *,
    expected_replicates: tuple[int, ...] = tuple(range(5)),
) -> tuple[bool, list[str]]:
    """The former monolithic contract has no compatibility validation path."""

    raise ValueError("monolithic operational manifests are not supported")


def _evaluation_cell_valid(
    payload: Any, *, replicate: int, arm: str, profile: str,
    deterministic: bool, cell: str, formal: bool, mode: str,
    episodes_per_cell: int, checkpoint_origin: str, checkpoint_path: str,
    ledger_cache: dict[tuple[Any, ...], tuple[dict[str, Any], list[Any]]],
) -> tuple[bool, tuple[int, ...], list[dict[str, str]]]:
    required = {
        "artifact_schema", "schema_version", "formal", "contract", "arm",
        "replicate", "cell", "profile", "mode", "checkpoint",
        "checkpoint_origin", "counts", "batches", "operational", "episodes",
        "natural_fork",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        return False, (), []
    batches = payload["batches"]
    episodes = payload["episodes"]
    expected_artifact_schema = (
        FORMAL_EVALUATION_ARTIFACT_SCHEMA
        if formal else EXERCISE_EVALUATION_ARTIFACT_SCHEMA
    )
    expected_cell_mode = "deterministic" if deterministic else "stochastic"
    if not (
        payload["artifact_schema"] == expected_artifact_schema
        and _is_exact_int(payload["schema_version"])
        and payload["schema_version"] == EVALUATION_CELL_SCHEMA
        and payload["formal"] is formal
        and payload["contract"] == registered_contract()
        and payload["arm"] == arm
        and _is_exact_int(payload["replicate"])
        and payload["replicate"] == replicate
        and payload["cell"] == cell
        and payload["profile"] == profile
        and payload["mode"] == expected_cell_mode
        and payload["checkpoint_origin"] == checkpoint_origin
        and payload["checkpoint"] == checkpoint_path
        and payload["counts"] == {
            "episodes": episodes_per_cell, "horizon": HORIZON,
            "batch_size": FORMAL_NUM_ENVS,
            "batches": episodes_per_cell // FORMAL_NUM_ENVS,
        }
        and _exact_int_fields(
            payload["counts"], ("episodes", "horizon", "batch_size", "batches")
        )
        and isinstance(batches, list)
        and len(batches) == episodes_per_cell // FORMAL_NUM_ENVS
        and isinstance(episodes, list) and len(episodes) == episodes_per_cell
        and all(
            isinstance(row, dict) and _is_exact_int(row.get("episode_id"))
            for row in episodes
        )
        and payload["operational"] is True
    ):
        return False, (), []
    expected_fork = arm == "EHC" and cell == "held_out_stochastic"
    if expected_fork:
        if not _natural_fork_valid(
            payload["natural_fork"], replicate=replicate, episodes=episodes,
            cell_batches=batches, formal=formal, mode=mode,
        ):
            return False, (), []
    elif payload["natural_fork"] is not None:
        return False, (), []
    expected_rng_states = _initial_rng_states(
        authoritative_seed_map(profile, replicate)
    )
    rng_digests: list[dict[str, str]] = []
    for batch_index, batch in enumerate(batches):
        if not isinstance(batch, dict) or set(batch) != {
            "batch_index", "episode_ids", "replay", "lifecycle_counts",
            "finite_checks", "seed_map", "owned_stream_digests",
            "rng_bindings", "rng_evidence", "reduction_counts",
            "checkpoint_origin", "episodes_digest",
        }:
            return False, (), []
        if not (
            _is_exact_int(batch["batch_index"])
            and isinstance(batch["episode_ids"], list)
            and all(_is_exact_int(value) for value in batch["episode_ids"])
            and _is_sha256(batch["episodes_digest"])
        ):
            return False, (), []
        expected_ids = list(range(
            batch_index * FORMAL_NUM_ENVS,
            (batch_index + 1) * FORMAL_NUM_ENVS,
        ))
        rows = episodes[
            batch_index * FORMAL_NUM_ENVS:
            (batch_index + 1) * FORMAL_NUM_ENVS
        ]
        recomputed_counts = {
            "keep": sum(int(row["keep"]) for row in rows),
            "renew": sum(int(row["renew"]) for row in rows),
            "non_create": sum(int(row["non_create"]) for row in rows),
            "multi_opportunity_lifecycles": sum(
                int(row["multi_opportunity_lifecycles"]) for row in rows
            ),
            "intervention_values": sum(len(row["intervention"]) for row in rows),
        }
        rng_valid, rng_ends = _rng_bindings_valid(
            batch["rng_bindings"],
            expected_context={
                "domain": "evaluation", "mode": mode, "formal": formal,
                "replicate": replicate, "arm": arm, "cell": cell,
                "batch": batch_index,
            },
            seed_map=authoritative_seed_map(profile, replicate),
            expected_starts=expected_rng_states,
        )
        if not (
            batch["batch_index"] == batch_index
            and batch["episode_ids"] == expected_ids
            and set(batch["lifecycle_counts"]) == LIFECYCLE_COUNT_KEYS
            and set(batch["finite_checks"]) == FINITE_CHECK_KEYS
            and set(batch["reduction_counts"]) == REDUCTION_COUNT_KEYS
            and _replay_record_valid(
                batch["replay"], event_rows_required=arm != "OR"
            )
            and batch["lifecycle_counts"]["invalid_segment_lifetimes"] == 0
            and all(int(value) == 0 for value in batch["finite_checks"].values())
            and batch["seed_map"] == authoritative_seed_map(profile, replicate)
            and rng_valid
            and _collection_binding_schedules_valid(
                batch["rng_bindings"], deterministic=deterministic,
                lifecycle_counts=batch["lifecycle_counts"],
                environment_count=FORMAL_NUM_ENVS,
            )
            and _rng_audit_evidence_valid(
                batch["rng_evidence"], batch["rng_bindings"], arm=arm,
                profile=profile, seed_map=batch["seed_map"],
                deterministic=deterministic, episode_ids=expected_ids,
                ledger_cache=ledger_cache,
            )
            and all(
                batch["owned_stream_digests"].get(name)
                == _digest_json(rng_ends[name]) for name in RNG_NAMES
            )
            and batch["reduction_counts"] == recomputed_counts
            and batch["checkpoint_origin"] == checkpoint_origin
            and batch["episodes_digest"] == _digest_json(rows)
        ):
            return False, (), []
        expected_rng_states = rng_ends
        rng_digests.append(dict(batch["owned_stream_digests"]))
    episode_ids = tuple(row["episode_id"] for row in episodes)
    if episode_ids != tuple(range(episodes_per_cell)):
        return False, (), []
    return True, episode_ids, rng_digests


def _compact_episode(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        name: row[name] for name in (
            "utility", "keep", "renew", "segments", "intervention",
            "non_create", "multi_opportunity_lifecycles",
        )
    }


def _validate_streamed_operational_records(
    output_root: Path, *, expected_replicates: tuple[int, ...] = tuple(range(5)),
    expected_updates: int = FORMAL_UPDATES,
    episodes_per_cell: int = FORMAL_EVAL_EPISODES, formal: bool = True,
    artifact_observer: Any = None,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate indexed evidence one verbose artifact at a time."""

    errors: list[str] = []
    compact: dict[str, Any] = {"episodes": {}, "fork_rows": {}}
    train_path = output_root / "train_manifest.json"
    evaluation_path = output_root / "evaluation_manifest.json"
    try:
        train_root = _load_json_file(train_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exception:
        return False, [f"training_manifest_read:{type(exception).__name__}"], compact
    expected_train_mode = "formal_train" if formal else "formal_path_exercise_train"
    expected_train_schema = (
        FORMAL_TRAIN_ARTIFACT_SCHEMA if formal else EXERCISE_TRAIN_ARTIFACT_SCHEMA
    )
    if not isinstance(train_root, dict) or set(train_root) != {
        "artifact_schema", "schema_version", "formal", "contract", "mode",
        "status", "branch", "progress", "replicate_indexes",
    }:
        return False, ["training_manifest_schema"], compact
    expected_train_branch = (
        "FORMAL_TRAIN_COMPLETE" if formal
        else "FORMAL_PATH_EXERCISE_TRAIN_COMPLETE"
    )
    if not (
        train_root["artifact_schema"] == expected_train_schema
        and _is_exact_int(train_root["schema_version"])
        and train_root["schema_version"] == TRAIN_MANIFEST_SCHEMA
        and train_root["formal"] is formal
        and train_root["contract"] == registered_contract()
        and train_root["mode"] == expected_train_mode
        and train_root["status"] == "COMPLETE"
        and train_root["branch"] == expected_train_branch
        and train_root["progress"] == {
            "completed_updates": len(expected_replicates) * expected_updates,
            "total_updates": len(expected_replicates) * expected_updates,
            "completed_replicates": len(expected_replicates),
            "total_replicates": len(expected_replicates),
        }
        and _exact_int_fields(
            train_root["progress"], (
                "completed_updates", "total_updates",
                "completed_replicates", "total_replicates",
            )
        )
    ):
        errors.append("training_manifest_identity")
    index_references = train_root["replicate_indexes"]
    if not _ordered_reference_values(
        index_references, "replicate", list(expected_replicates)
    ):
        errors.append("training_replicate_index_order")
        return False, errors, compact
    checkpoint_paths: dict[tuple[int, str], str] = {}
    ledger_cache: dict[tuple[Any, ...], tuple[dict[str, Any], list[Any]]] = {}
    for replicate, index_reference in zip(
        expected_replicates, index_references, strict=True
    ):
        try:
            index_path, index = _verified_json_reference(
                output_root, index_reference,
                identity_keys=frozenset({"replicate", "generation"}),
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exception:
            errors.append(f"training_index_reference:{replicate}:{type(exception).__name__}")
            continue
        expected_index_path = (
            output_root / "train" / f"replicate_{replicate}" / "indexes"
            / f"index_{index_reference['generation']}.json"
        ).resolve()
        if index_path != expected_index_path or index_reference["replicate"] != replicate:
            errors.append(f"training_index_path:{replicate}")
            continue
        expected_index_schema = (
            FORMAL_TRAIN_INDEX_SCHEMA if formal else EXERCISE_TRAIN_INDEX_SCHEMA
        )
        expected_index_branch = (
            "FORMAL_TRAIN_REPLICATE_COMPLETE" if formal
            else "FORMAL_PATH_EXERCISE_TRAIN_REPLICATE_COMPLETE"
        )
        if not isinstance(index, dict) or set(index) != {
            "artifact_schema", "schema_version", "formal", "contract", "mode",
            "replicate", "generation", "status", "branch", "progress", "updates",
            "operational", "arms",
        } or not (
            index["artifact_schema"] == expected_index_schema
            and _is_exact_int(index["schema_version"])
            and index["schema_version"] == TRAIN_INDEX_SCHEMA
            and index["formal"] is formal
            and index["contract"] == registered_contract()
            and index["mode"] == expected_train_mode
            and _is_exact_int(index["replicate"])
            and index["replicate"] == replicate
            and _is_exact_int(index["generation"])
            and index["generation"] == index_reference["generation"]
            and index["status"] == "COMPLETE"
            and index["branch"] == expected_index_branch
            and index["progress"] == {
                "completed_updates": expected_updates,
                "total_updates": expected_updates,
            }
            and _exact_int_fields(
                index["progress"], ("completed_updates", "total_updates")
            )
            and index["operational"] is True
        ):
            errors.append(f"training_index_identity:{replicate}")
            continue
        update_references = index["updates"]
        if not _ordered_reference_values(
            update_references, "update", list(range(1, expected_updates + 1))
        ):
            errors.append(f"training_update_order:{replicate}")
            continue
        evidence_directory = index_path.parent.parent / "evidence"
        indexed_paths: set[Path] = set()
        rng_chain = {
            arm: _initial_rng_states(authoritative_seed_map("train", replicate))
            for arm in ARMS
        }
        expected_update_schema = (
            FORMAL_TRAIN_UPDATE_SCHEMA if formal else EXERCISE_TRAIN_UPDATE_SCHEMA
        )
        for update, reference in enumerate(update_references, start=1):
            try:
                shard_path, shard = _verified_json_reference(
                    output_root, reference,
                    identity_keys=frozenset({"update"}),
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exception:
                errors.append(f"training_update_reference:{replicate}:{update}:{type(exception).__name__}")
                break
            if artifact_observer is not None:
                artifact_observer("loaded", shard_path)
            expected_path = (evidence_directory / f"update_{update}.json").resolve()
            if shard_path != expected_path or reference["update"] != update:
                errors.append(f"training_update_path:{replicate}:{update}")
                if artifact_observer is not None:
                    artifact_observer("released", shard_path)
                break
            indexed_paths.add(shard_path)
            if not isinstance(shard, dict) or set(shard) != {
                "artifact_schema", "schema_version", "formal", "contract",
                "mode", "replicate", "update", "evidence",
            } or not (
                shard["artifact_schema"] == expected_update_schema
                and _is_exact_int(shard["schema_version"])
                and shard["schema_version"] == TRAIN_UPDATE_SCHEMA
                and shard["formal"] is formal
                and shard["contract"] == registered_contract()
                and shard["mode"] == expected_train_mode
                and _is_exact_int(shard["replicate"])
                and shard["replicate"] == replicate
                and _is_exact_int(shard["update"])
                and shard["update"] == update
            ):
                errors.append(f"training_update_identity:{replicate}:{update}")
                if artifact_observer is not None:
                    artifact_observer("released", shard_path)
                break
            ends: dict[str, dict[str, Any]] = {}
            if not _training_update_valid(
                shard["evidence"], update=update, replicate=replicate,
                formal=formal, mode=expected_train_mode, rng_starts=rng_chain,
                validated_rng_ends=ends, ledger_cache=ledger_cache,
            ):
                errors.append(f"training_update_evidence:{replicate}:{update}")
                if artifact_observer is not None:
                    artifact_observer("released", shard_path)
                break
            rng_chain = ends
            del shard
            if artifact_observer is not None:
                artifact_observer("released", shard_path)
        actual_paths = {
            path.resolve() for path in evidence_directory.glob("update_*.json")
            if path.is_file()
        }
        if actual_paths != indexed_paths:
            errors.append(f"training_unindexed_or_missing:{replicate}")
        arms = index["arms"]
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            errors.append(f"training_arm_set:{replicate}")
            continue
        checkpoint_name = f"update_{expected_updates}.pt"
        for arm in ARMS:
            entry = arms[arm]
            expected_event = 0 if arm == "OR" else expected_updates * PPO_PASSES
            if not isinstance(entry, dict) or set(entry) != {
                "arm", "replicate", "checkpoint", "checkpoint_origin",
                "completed_update", "next_episode_id", "exposure", "seed_map",
                "parameter_counts", "roundtrip_errors", "checkpoint_sha256",
                "checkpoint_byte_count",
            }:
                errors.append(f"training_arm_schema:{replicate}:{arm}")
                continue
            if not (
                _exact_int_fields(entry, (
                    "replicate", "completed_update", "next_episode_id",
                    "checkpoint_byte_count",
                ))
                and entry["checkpoint_byte_count"] >= 0
                and _is_sha256(entry["checkpoint_sha256"])
                and _exact_int_fields(entry["exposure"], ("base", "event"))
            ):
                errors.append(f"training_arm_types:{replicate}:{arm}")
                continue
            try:
                checkpoint = _resolve_artifact_path(output_root, entry["checkpoint"])
                checkpoint_digest, checkpoint_bytes = _file_integrity(checkpoint)
            except (OSError, ValueError):
                errors.append(f"training_checkpoint_reference:{replicate}:{arm}")
                continue
            expected_checkpoint = (
                output_root / "train" / f"replicate_{replicate}" / arm
                / checkpoint_name
            ).resolve()
            if not (
                entry["arm"] == arm and entry["replicate"] == replicate
                and checkpoint == expected_checkpoint
                and entry["checkpoint_origin"] == checkpoint_name
                and entry["completed_update"] == expected_updates
                and entry["next_episode_id"] == expected_updates * FORMAL_NUM_ENVS
                and entry["exposure"] == {
                    "base": expected_updates * PPO_PASSES, "event": expected_event,
                }
                and entry["seed_map"] == authoritative_seed_map("train", replicate)
                and entry["parameter_counts"] == _expected_parameter_counts(arm)
                and all(float(value) <= 1e-7 for value in entry["roundtrip_errors"].values())
                and entry["checkpoint_sha256"] == checkpoint_digest
                and entry["checkpoint_byte_count"] == checkpoint_bytes
            ):
                errors.append(f"training_arm_evidence:{replicate}:{arm}")
            checkpoint_paths[(replicate, arm)] = entry["checkpoint"]
    try:
        evaluation_root = _load_json_file(evaluation_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exception:
        errors.append(f"evaluation_manifest_read:{type(exception).__name__}")
        return False, errors, compact
    expected_evaluation_mode = (
        "formal_evaluate" if formal else "formal_path_exercise_evaluate"
    )
    expected_evaluation_root_schema = (
        FORMAL_EVALUATION_MANIFEST_SCHEMA
        if formal else EXERCISE_EVALUATION_MANIFEST_SCHEMA
    )
    expected_evaluation_branch = (
        "FORMAL_EVALUATION_COMPLETE" if formal
        else "FORMAL_PATH_EXERCISE_EVALUATION_COMPLETE"
    )
    expected_cells = [
        (replicate, arm, cell) for replicate in expected_replicates for arm in ARMS
        for _profile, _deterministic, cell in EVALUATION_CELLS
    ]
    if not isinstance(evaluation_root, dict) or set(evaluation_root) != {
        "artifact_schema", "schema_version", "formal", "contract", "mode",
        "status", "branch", "progress", "cells",
    } or not (
        evaluation_root["artifact_schema"] == expected_evaluation_root_schema
        and _is_exact_int(evaluation_root["schema_version"])
        and evaluation_root["schema_version"] == EVALUATION_MANIFEST_SCHEMA
        and evaluation_root["formal"] is formal
        and evaluation_root["contract"] == registered_contract()
        and evaluation_root["mode"] == expected_evaluation_mode
        and evaluation_root["status"] == "COMPLETE"
        and evaluation_root["branch"] == expected_evaluation_branch
        and evaluation_root["progress"] == {
            "completed_cells": len(expected_cells), "total_cells": len(expected_cells),
        }
        and _exact_int_fields(
            evaluation_root["progress"], ("completed_cells", "total_cells")
        )
    ):
        errors.append("evaluation_manifest_identity")
        return False, errors, compact
    cell_references = evaluation_root["cells"]
    if not (
        isinstance(cell_references, list)
        and len(cell_references) == len(expected_cells)
        and all(
            isinstance(reference, dict)
            and _is_exact_int(reference.get("replicate"))
            and type(reference.get("arm")) is str
            and type(reference.get("cell")) is str
            for reference in cell_references
        )
        and [
            (reference["replicate"], reference["arm"], reference["cell"])
            for reference in cell_references
        ] == expected_cells
    ):
        errors.append("evaluation_cell_order")
        return False, errors, compact
    actual_cell_paths = {
        path.resolve() for path in (output_root / "evaluation").rglob("*.json")
        if path.is_file()
    }
    indexed_cell_paths: set[Path] = set()
    paired_ids: dict[tuple[int, str], tuple[int, ...]] = {}
    cell_rng: dict[tuple[int, str, str], list[dict[str, str]]] = {}
    cell_spec = {name: (profile, deterministic) for profile, deterministic, name in EVALUATION_CELLS}
    checkpoint_origin = f"update_{expected_updates}.pt"
    for expected, reference in zip(expected_cells, cell_references, strict=True):
        replicate, arm, cell = expected
        try:
            cell_path, payload = _verified_json_reference(
                output_root, reference,
                identity_keys=frozenset({"replicate", "arm", "cell"}),
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exception:
            errors.append(f"evaluation_cell_reference:{replicate}:{arm}:{cell}:{type(exception).__name__}")
            continue
        if artifact_observer is not None:
            artifact_observer("loaded", cell_path)
        expected_path = (
            output_root / "evaluation" / f"replicate_{replicate}" / arm
            / f"{cell}.json"
        ).resolve()
        if cell_path != expected_path or (
            reference["replicate"], reference["arm"], reference["cell"]
        ) != expected:
            errors.append(f"evaluation_cell_path:{replicate}:{arm}:{cell}")
            if artifact_observer is not None:
                artifact_observer("released", cell_path)
            continue
        indexed_cell_paths.add(cell_path)
        profile, deterministic = cell_spec[cell]
        valid, episode_ids, rng_digests = _evaluation_cell_valid(
            payload, replicate=replicate, arm=arm, profile=profile,
            deterministic=deterministic, cell=cell, formal=formal,
            mode=expected_evaluation_mode, episodes_per_cell=episodes_per_cell,
            checkpoint_origin=checkpoint_origin,
            checkpoint_path=checkpoint_paths.get((replicate, arm), ""),
            ledger_cache=ledger_cache,
        )
        if not valid:
            errors.append(f"evaluation_cell_evidence:{replicate}:{arm}:{cell}")
            if artifact_observer is not None:
                artifact_observer("released", cell_path)
            continue
        pairing_key = (replicate, cell)
        if pairing_key in paired_ids and paired_ids[pairing_key] != episode_ids:
            errors.append(f"evaluation_pairing:{replicate}:{cell}")
        paired_ids[pairing_key] = episode_ids
        cell_rng[(replicate, arm, cell)] = rng_digests
        if cell == "held_out_stochastic":
            compact["episodes"][(replicate, arm)] = [
                _compact_episode(row) for row in payload["episodes"]
            ]
            if arm == "EHC":
                compact["fork_rows"][replicate] = [
                    {
                        "base_episode_id": row["base_episode_id"],
                        "natural_action": row["natural_action"],
                        "advantage": row["advantage"],
                    }
                    for row in payload["natural_fork"]["fork_rows"]
                ]
        del payload
        if artifact_observer is not None:
            artifact_observer("released", cell_path)
    if actual_cell_paths != indexed_cell_paths:
        errors.append("evaluation_unindexed_or_missing")
    for replicate in expected_replicates:
        for _profile, _deterministic, cell in EVALUATION_CELLS:
            arm_digests = {
                arm: cell_rng.get((replicate, arm, cell)) for arm in ARMS
            }
            if any(value is None for value in arm_digests.values()):
                continue
            for batch_index in range(episodes_per_cell // FORMAL_NUM_ENVS):
                if any(
                    arm_digests["OR"][batch_index].get(name)
                    != arm_digests["DUM"][batch_index].get(name)
                    for name in ("ledger", "order", "primitive")
                ):
                    errors.append(f"evaluation_or_dum_rng:{replicate}:{cell}:{batch_index}")
                if any(
                    arm_digests["DUM"][batch_index].get(name)
                    != arm_digests["EHC"][batch_index].get(name)
                    for name in RNG_NAMES
                ):
                    errors.append(f"evaluation_dum_ehc_rng:{replicate}:{cell}:{batch_index}")
    if any(output_root.rglob("*.tmp")):
        errors.append("temporary_artifact_residue")
    return not errors, errors, compact


def _lifecycle_valid(trajectory: Any, arm: ArmName) -> bool:
    counts = factor_counts(trajectory)
    if arm == "OR":
        return all(value == 0 for value in counts.values())
    return bool(
        counts["categorical"] == counts["keep"] + counts["renew"]
        and counts["mark"] == counts["create"] + counts["renew"]
        and all(record.active_lifetime >= 1 for rows in trajectory.segments for record in rows)
    )


def run_smoke(output_root: Path, *, device_name: str) -> dict[str, Any]:
    """One real, bounded, explicitly non-formal package exercise.

    The backend is named by the caller and must be a registered one; there is
    no default, because a default would let the smoke silently run somewhere
    other than the backend the run is registered on.
    """

    device = require_registered_backend(device_name)
    arms, base_optimizers, event_optimizers = initialize_arms(device)
    states = {name: make_training_state(name, 0) for name in ARMS}
    evidence: dict[str, Any] = {}
    trajectories: dict[str, Any] = {}
    for name in ARMS:
        arm = arms[name]
        trajectory = collect_trajectory(
            arm, states[name], device=device, episode_ids=(0,)
        )
        trajectories[name] = trajectory
        _replay, replay = validate_replay(arm, trajectory, device=device)
        update = optimize_update(
            arm, base_optimizers[name], event_optimizers[name],
            states[name], trajectory, device=device,
        )
        checkpoint = output_root / "checkpoints" / name / "smoke_update_001.pt"
        save_checkpoint(
            checkpoint, arm=arm, base_optimizer=base_optimizers[name],
            event_optimizer=event_optimizers[name], state=states[name],
        )
        loaded_arm, loaded_base, loaded_event, loaded_state = load_checkpoint(
            checkpoint, device=device, expected_arm=name, expected_replicate=0
        )
        evidence[name] = {
            "replay": replay,
            "update": update,
            "factors": factor_counts(trajectory),
            "lifecycle_valid": _lifecycle_valid(trajectory, name),
            "counts": parameter_and_optimizer_counts(
                arm, base_optimizers[name], event_optimizers[name]
            ),
            "checkpoint_model_error": nested_state_maximum_difference(
                arm.state_dict(), loaded_arm.state_dict()
            ),
            "checkpoint_base_optimizer_error": nested_state_maximum_difference(
                base_optimizers[name].state_dict(), loaded_base.state_dict()
            ),
            "checkpoint_event_optimizer_error": nested_state_maximum_difference(
                None if event_optimizers[name] is None else event_optimizers[name].state_dict(),
                None if loaded_event is None else loaded_event.state_dict(),
            ),
            "checkpoint_state_equal": (
                states[name].completed_update == loaded_state.completed_update
                and states[name].next_episode_id == loaded_state.next_episode_id
                and states[name].base_optimizer_steps == loaded_state.base_optimizer_steps
                and states[name].event_optimizer_steps == loaded_state.event_optimizer_steps
            ),
            "artifact": str(checkpoint),
        }
    no_op = _no_op_equal(trajectories["OR"], trajectories["DUM"])

    checkpoint = output_root / "checkpoints" / "EHC" / "continuation_origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=states["EHC"],
    )
    left_arm, left_base, left_event, left_state = load_checkpoint(
        checkpoint, device=device, expected_arm="EHC", expected_replicate=0
    )
    left_trajectory = collect_trajectory(
        left_arm, left_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        left_arm, left_base, left_event, left_state,
        left_trajectory, device=device,
    )
    left_global_rng = runtime_rng_snapshot()

    right_arm, right_base, right_event, right_state = load_checkpoint(
        checkpoint, device=device, expected_arm="EHC", expected_replicate=0
    )
    right_trajectory = collect_trajectory(
        right_arm, right_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        right_arm, right_base, right_event, right_state,
        right_trajectory, device=device,
    )
    right_global_rng = runtime_rng_snapshot()
    continuation = compare_continuations(
        left_arm, right_arm, left_trajectory, right_trajectory,
        left_base, right_base, left_event, right_event,
        left_state, right_state, left_global_rng, right_global_rng,
    )
    result = {
        "mode": "non_formal_smoke",
        "device": str(device),
        "registered_contract": REGISTERED_CONTRACT,
        "formal": False,
        "arms": evidence,
        "or_dum_no_op": no_op,
        "continuation": continuation,
    }
    _write_json(output_root / "smoke_result.json", result)
    return result


def _file_integrity(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def _file_sha256(path: Path) -> str:
    return _file_integrity(path)[0]


def _root_relative_path(root: Path, path: Path) -> str:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    try:
        relative = path_resolved.relative_to(root_resolved)
    except ValueError as exception:
        raise ValueError("artifact path escapes evidence root") from exception
    if not relative.parts or any(part in ("", ".", "..") for part in relative.parts):
        raise ValueError("artifact path is not a strict root-relative child")
    return relative.as_posix()


def _resolve_artifact_path(root: Path, relative_path: Any) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError("artifact reference path must be a non-empty string")
    candidate = Path(relative_path)
    if candidate.is_absolute() or candidate.suffix == ".tmp":
        raise ValueError("artifact reference must be authoritative and root-relative")
    resolved = (root / candidate).resolve()
    _root_relative_path(root, resolved)
    return resolved


def _artifact_reference(root: Path, path: Path, **identity: Any) -> dict[str, Any]:
    digest, byte_count = _file_integrity(path)
    return {
        **identity,
        "path": _root_relative_path(root, path),
        "sha256": digest,
        "byte_count": byte_count,
    }


def _load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _verified_json_reference(
    root: Path, reference: Any, *, identity_keys: frozenset[str],
) -> tuple[Path, Any]:
    required = identity_keys | {"path", "sha256", "byte_count"}
    if not isinstance(reference, dict) or set(reference) != required:
        raise ValueError("artifact reference schema mismatch")
    integer_identities = {"replicate", "update", "generation", "batch", "episode"}
    if not (
        type(reference["path"]) is str
        and _is_sha256(reference["sha256"])
        and _is_exact_int(reference["byte_count"])
        and reference["byte_count"] >= 0
        and all(
            (_is_exact_int(reference[key]) if key in integer_identities
             else type(reference[key]) is str)
            for key in identity_keys
        )
    ):
        raise ValueError("artifact reference type mismatch")
    path = _resolve_artifact_path(root, reference["path"])
    if not path.is_file():
        raise ValueError("referenced artifact is missing")
    digest, byte_count = _file_integrity(path)
    if byte_count != reference["byte_count"]:
        raise ValueError("referenced artifact byte count mismatch")
    if digest != reference["sha256"]:
        raise ValueError("referenced artifact digest mismatch")
    return path, _load_json_file(path)


def _ordered_reference_values(
    references: Any, key: str, expected: list[Any],
) -> bool:
    return bool(
        isinstance(references, list)
        and len(references) == len(expected)
        and all(
            isinstance(reference, dict) and key in reference
            and type(reference[key]) is type(expected_value)
            for reference, expected_value in zip(references, expected, strict=True)
        )
        and [reference[key] for reference in references] == expected
    )


def _publish_operational_failure(
    output_root: Path, *, mode: str, formal: bool, stage: str,
    replicate: int | None, arm: str | None, cell: str | None,
    batch: int | None, exception: BaseException,
    completed_paths: list[str], last_evidence: Any,
    manifest_path: Path,
) -> dict[str, Any]:
    failure_path = output_root / "failures" / (
        f"{mode}_{os.getpid()}_{time_ns()}.json"
    )
    failure = {
        "artifact_schema": "event_held_commitment_link_g0.operational_failure.v2",
        "mode": mode, "formal": formal, "stage": stage,
        "replicate": replicate, "arm": arm, "cell": cell, "batch": batch,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "completed_artifact_paths": list(completed_paths),
        "last_complete_evidence": last_evidence,
    }
    _write_json(failure_path, failure)
    failure_reference = _artifact_reference(
        output_root, failure_path, artifact="operational_failure",
    )
    if manifest_path.is_file():
        try:
            current = _load_json_file(manifest_path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            current = None
    else:
        current = None
    terminal = dict(current) if isinstance(current, dict) else {
        "artifact_schema": "event_held_commitment_link_g0.terminal.v2",
        "formal": formal, "mode": mode,
    }
    terminal.update({
        "status": "INVALID_OPERATIONAL", "branch": "INVALID_OPERATIONAL",
        "failure_artifact": failure_reference,
    })
    _write_json(manifest_path, terminal)
    return terminal


def _operational_failure_manifest_valid(
    output_root: Path, manifest_path: Path,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    authoritative_evidence: list[dict[str, Any]] = []
    try:
        terminal = _load_json_file(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exception:
        return False, [f"terminal_read:{type(exception).__name__}"]
    if not isinstance(terminal, dict) or not (
        terminal.get("status") == "INVALID_OPERATIONAL"
        and terminal.get("branch") == "INVALID_OPERATIONAL"
        and isinstance(terminal.get("formal"), bool)
        and isinstance(terminal.get("mode"), str)
    ):
        return False, ["terminal_identity"]
    train_references = terminal.get("replicate_indexes")
    if train_references is None:
        try:
            train_root = _load_json_file(output_root / "train_manifest.json")
            train_references = train_root.get("replicate_indexes")
        except (OSError, UnicodeError, json.JSONDecodeError):
            train_references = None
    if train_references is not None:
        references = train_references
        if not isinstance(references, list) or not _ordered_reference_values(
            references, "replicate", sorted(
                reference.get("replicate") for reference in references
                if isinstance(reference, dict)
                and _is_exact_int(reference.get("replicate"))
            ),
        ):
            errors.append("terminal_train_reference_order")
        else:
            for reference in references:
                try:
                    path, index = _verified_json_reference(
                        output_root, reference,
                        identity_keys=frozenset({"replicate", "generation"}),
                    )
                    expected = (
                        output_root / "train"
                        / f"replicate_{reference['replicate']}" / "indexes"
                        / f"index_{reference['generation']}.json"
                    ).resolve()
                    if path != expected or not (
                        isinstance(index, dict)
                        and _is_exact_int(index.get("replicate"))
                        and _is_exact_int(index.get("generation"))
                        and index["replicate"] == reference["replicate"]
                        and index["generation"] == reference["generation"]
                    ):
                        errors.append("terminal_train_reference")
                    elif isinstance(index.get("updates"), list):
                        authoritative_evidence.extend(index["updates"])
                except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                    errors.append("terminal_train_reference")
    cell_references = terminal.get("cells")
    if cell_references is None:
        try:
            evaluation_root = _load_json_file(
                output_root / "evaluation_manifest.json"
            )
            cell_references = evaluation_root.get("cells")
        except (OSError, UnicodeError, json.JSONDecodeError):
            cell_references = None
    if cell_references is not None:
        references = cell_references
        if not isinstance(references, list):
            errors.append("terminal_cell_references")
        else:
            for reference in references:
                try:
                    _verified_json_reference(
                        output_root, reference,
                        identity_keys=frozenset({"replicate", "arm", "cell"}),
                    )
                    authoritative_evidence.append(reference)
                except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                    errors.append("terminal_cell_references")
    try:
        _failure_path, failure = _verified_json_reference(
            output_root, terminal.get("failure_artifact"),
            identity_keys=frozenset({"artifact"}),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exception:
        return False, [f"failure_reference:{type(exception).__name__}"]
    completed_paths = failure.get("completed_artifact_paths") if isinstance(failure, dict) else None
    completed_paths_valid = isinstance(completed_paths, list)
    if completed_paths_valid:
        for value in completed_paths:
            try:
                if not isinstance(value, str) or Path(value).is_absolute():
                    completed_paths_valid = False
                    break
                _resolve_artifact_path(output_root, value)
            except ValueError:
                completed_paths_valid = False
                break
    if not isinstance(failure, dict) or set(failure) != {
        "artifact_schema", "mode", "formal", "stage", "replicate", "arm",
        "cell", "batch", "exception_type", "exception_message",
        "completed_artifact_paths", "last_complete_evidence",
    } or not (
        failure["artifact_schema"]
        == "event_held_commitment_link_g0.operational_failure.v2"
        and failure["mode"] == terminal["mode"]
        and failure["formal"] is terminal["formal"]
        and completed_paths_valid
        and (
            failure["replicate"] is None
            or _is_exact_int(failure["replicate"])
        )
        and (failure["batch"] is None or _is_exact_int(failure["batch"]))
        and (failure["arm"] is None or type(failure["arm"]) is str)
        and (failure["cell"] is None or type(failure["cell"]) is str)
    ):
        errors.append("failure_identity")
    last = failure.get("last_complete_evidence")
    if last:
        if not isinstance(last, dict) or not {
            "path", "sha256", "byte_count"
        }.issubset(last):
            errors.append("failure_last_reference_schema")
        else:
            identity = frozenset(last) - {"path", "sha256", "byte_count"}
            try:
                _verified_json_reference(
                    output_root, last, identity_keys=identity,
                )
                if last not in authoritative_evidence:
                    errors.append("failure_last_reference_not_indexed")
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                errors.append("failure_last_reference")
    if any(output_root.rglob("*.tmp")):
        errors.append("temporary_artifact_residue")
    return not errors, errors


def _training_core(
    output_root: Path, *, device: torch.device, replicates: tuple[int, ...],
    updates: int, formal: bool, artifact_schema: str,
    completed_paths: list[str], last_evidence: dict[str, Any],
) -> dict[str, Any]:
    mode = "formal_train" if formal else "formal_path_exercise_train"
    index_schema = FORMAL_TRAIN_INDEX_SCHEMA if formal else EXERCISE_TRAIN_INDEX_SCHEMA
    update_schema = FORMAL_TRAIN_UPDATE_SCHEMA if formal else EXERCISE_TRAIN_UPDATE_SCHEMA
    manifest_path = output_root / "train_manifest.json"
    manifest: dict[str, Any] = {
        "artifact_schema": artifact_schema,
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "formal": formal,
        "contract": registered_contract(),
        "mode": mode,
        "status": "IN_PROGRESS", "branch": "IN_PROGRESS",
        "progress": {
            "completed_updates": 0,
            "total_updates": len(replicates) * updates,
            "completed_replicates": 0,
            "total_replicates": len(replicates),
        },
        "replicate_indexes": [],
    }
    _write_json(manifest_path, manifest)
    replicate_progress: dict[int, dict[str, Any]] = {}
    for replicate in replicates:
        arms, base_optimizers, event_optimizers = initialize_arms(
            device, replicate=replicate
        )
        states = {arm: make_training_state(arm, replicate) for arm in ARMS}
        indexes_directory = (
            output_root / "train" / f"replicate_{replicate}" / "indexes"
        )
        generation = 0
        replicate_index: dict[str, Any] = {
            "artifact_schema": index_schema,
            "schema_version": TRAIN_INDEX_SCHEMA,
            "formal": formal,
            "contract": registered_contract(),
            "mode": mode,
            "replicate": replicate, "generation": generation,
            "status": "IN_PROGRESS", "branch": "IN_PROGRESS",
            "progress": {"completed_updates": 0, "total_updates": updates},
            "updates": [], "operational": True, "arms": {},
        }

        def publish_index() -> None:
            nonlocal generation
            generation += 1
            replicate_index["generation"] = generation
            index_path = indexes_directory / f"index_{generation}.json"
            _write_json(index_path, replicate_index)
            reference = _artifact_reference(
                output_root, index_path, replicate=replicate,
                generation=generation,
            )
            manifest["replicate_indexes"] = [
                existing for existing in manifest["replicate_indexes"]
                if existing["replicate"] != replicate
            ] + [reference]
            manifest["replicate_indexes"].sort(key=lambda value: value["replicate"])
            replicate_progress[replicate] = {
                "completed_updates": replicate_index["progress"]["completed_updates"],
                "complete": replicate_index["status"] == "COMPLETE",
            }
            manifest["progress"]["completed_updates"] = sum(
                progress["completed_updates"]
                for progress in replicate_progress.values()
            )
            manifest["progress"]["completed_replicates"] = sum(
                progress["complete"] for progress in replicate_progress.values()
            )
            _write_json(manifest_path, manifest)

        publish_index()
        for update_index in range(updates):
            exposure_before = {
                arm: {
                    "base": states[arm].base_optimizer_steps,
                    "event": states[arm].event_optimizer_steps,
                }
                for arm in ARMS
            }
            rng_starts = {
                arm: owned_rng_states(states[arm]) for arm in ARMS
            }
            trajectories = {
                arm: collect_trajectory(arms[arm], states[arm], device=device)
                for arm in ARMS
            }
            update_metrics = {
                arm: optimize_update(
                    arms[arm], base_optimizers[arm], event_optimizers[arm],
                    states[arm], trajectories[arm], device=device,
                    ppo_passes=PPO_PASSES,
                )
                for arm in ARMS
            }
            base_noop_error = nested_state_maximum_difference(
                arms["OR"].base.state_dict(), arms["DUM"].base.state_dict()
            )
            arms_evidence: dict[str, Any] = {}
            for arm in ARMS:
                metrics = update_metrics[arm]
                before = exposure_before[arm]
                after = {
                    "base": states[arm].base_optimizer_steps,
                    "event": states[arm].event_optimizer_steps,
                }
                rng_context = {
                    "domain": "training", "mode": mode,
                    "formal": bool(formal), "replicate": int(replicate),
                    "arm": arm, "update": update_index + 1,
                }
                rng_bindings = _collection_rng_bindings(
                    context=rng_context,
                    seed_map=states[arm].seed_map,
                    start_states=rng_starts[arm],
                    end_states=owned_rng_states(states[arm]),
                    trajectory=trajectories[arm], deterministic=False,
                )
                arms_evidence[arm] = {
                    "arm": arm,
                    "seed_map": dict(states[arm].seed_map),
                    "owned_stream_digests": _owned_stream_digests(states[arm]),
                    "rng_bindings": rng_bindings,
                    "rng_evidence": deepcopy(trajectories[arm].rng_audit),
                    "replay": metrics["replay"],
                    "lifecycle_counts": _lifecycle_counts(trajectories[arm]),
                    "finite_checks": _finite_checks(trajectories[arm]),
                    "exposure": {
                        "before": before,
                        "delta": {
                            "base": after["base"] - before["base"],
                            "event": after["event"] - before["event"],
                        },
                        "after": after,
                    },
                    "optimizer": {
                        name: metrics[name]
                        for name in (
                            "base_steps", "event_steps", "primitive_replays",
                            "event_head_replays", "packed_trajectory_count",
                            "base_non_none_gradients", "base_zero_gradients",
                            "base_nonfinite_gradient_values",
                            "base_nonfinite_loss_values",
                            "base_nonfinite_norm_values",
                            "event_non_none_gradients", "event_zero_gradients",
                            "event_nonfinite_gradient_values",
                            "event_nonfinite_loss_values",
                            "event_nonfinite_norm_values",
                            "ownership_manifest", "base_passes", "event_passes",
                            "evidence_storage",
                        )
                    },
                    "parameter_counts": parameter_and_optimizer_counts(
                        arms[arm], base_optimizers[arm], event_optimizers[arm]
                    ),
                }
            current = {
                "update": update_index + 1,
                "arms": arms_evidence,
                "paired": _paired_update_evidence(
                    trajectories, states, base_noop_error=base_noop_error
                ),
            }
            if not _training_update_valid(
                current, update=update_index + 1, replicate=replicate,
                formal=formal, mode=mode, rng_starts=rng_starts,
            ):
                raise RuntimeError(
                    f"{mode} recomputable update evidence failed at {replicate}:{update_index + 1}"
                )
            shard = {
                "artifact_schema": update_schema,
                "schema_version": TRAIN_UPDATE_SCHEMA,
                "formal": formal,
                "contract": registered_contract(),
                "mode": mode,
                "replicate": replicate,
                "update": update_index + 1,
                "evidence": current,
            }
            shard_path = (
                output_root / "train" / f"replicate_{replicate}" / "evidence"
                / f"update_{update_index + 1}.json"
            )
            _write_json(shard_path, shard)
            reference = _artifact_reference(
                output_root, shard_path, update=update_index + 1,
            )
            replicate_index["updates"].append(reference)
            replicate_index["progress"]["completed_updates"] = update_index + 1
            publish_index()
            completed_paths.append(reference["path"])
            last_evidence.clear(); last_evidence.update(reference)
            del shard, current, arms_evidence, update_metrics, trajectories

        checkpoint_name = f"update_{updates}.pt"
        arm_records: dict[str, Any] = {}
        for arm in ARMS:
            checkpoint = output_root / "train" / f"replicate_{replicate}" / arm / checkpoint_name
            save_checkpoint(
                checkpoint, arm=arms[arm], base_optimizer=base_optimizers[arm],
                event_optimizer=event_optimizers[arm], state=states[arm],
            )
            completed_paths.append(_root_relative_path(output_root, checkpoint))
            loaded_arm, loaded_base, loaded_event, loaded_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm,
                expected_replicate=replicate, formal_evaluation=formal,
            )
            roundtrip_errors = {
                "model": nested_state_maximum_difference(
                    arms[arm].state_dict(), loaded_arm.state_dict()
                ),
                "base_optimizer": nested_state_maximum_difference(
                    base_optimizers[arm].state_dict(), loaded_base.state_dict()
                ),
                "event_optimizer": nested_state_maximum_difference(
                    None if event_optimizers[arm] is None else event_optimizers[arm].state_dict(),
                    None if loaded_event is None else loaded_event.state_dict(),
                ),
                "state": float(not (
                    states[arm].completed_update == loaded_state.completed_update
                    and states[arm].next_episode_id == loaded_state.next_episode_id
                    and states[arm].base_optimizer_steps == loaded_state.base_optimizer_steps
                    and states[arm].event_optimizer_steps == loaded_state.event_optimizer_steps
                    and states[arm].seed_map == loaded_state.seed_map
                    and _owned_stream_digests(states[arm]) == _owned_stream_digests(loaded_state)
                )),
            }
            if any(value > 1e-7 for value in roundtrip_errors.values()):
                raise RuntimeError(f"checkpoint roundtrip failed {replicate}:{arm}:{roundtrip_errors}")
            arm_records[arm] = {
                "arm": arm, "replicate": replicate,
                "checkpoint": _root_relative_path(output_root, checkpoint),
                "checkpoint_origin": checkpoint_name,
                "completed_update": states[arm].completed_update,
                "next_episode_id": states[arm].next_episode_id,
                "exposure": {
                    "base": states[arm].base_optimizer_steps,
                    "event": states[arm].event_optimizer_steps,
                },
                "seed_map": dict(states[arm].seed_map),
                "parameter_counts": parameter_and_optimizer_counts(
                    arms[arm], base_optimizers[arm], event_optimizers[arm]
                ),
                "roundtrip_errors": roundtrip_errors,
                "checkpoint_sha256": _file_sha256(checkpoint),
                "checkpoint_byte_count": checkpoint.stat().st_size,
            }
            replicate_index["arms"][arm] = arm_records[arm]
            publish_index()
        replicate_index["status"] = "COMPLETE"
        replicate_index["branch"] = (
            "FORMAL_TRAIN_REPLICATE_COMPLETE" if formal
            else "FORMAL_PATH_EXERCISE_TRAIN_REPLICATE_COMPLETE"
        )
        publish_index()
    manifest["status"] = "COMPLETE"
    manifest["branch"] = (
        "FORMAL_TRAIN_COMPLETE" if formal
        else "FORMAL_PATH_EXERCISE_TRAIN_COMPLETE"
    )
    manifest["progress"]["completed_replicates"] = len(replicates)
    _write_json(manifest_path, manifest)
    return manifest


def formal_train(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal train requires the exact authorization token")
    device = require_registered_backend(device_name)
    completed_paths: list[str] = []
    last_evidence: dict[str, Any] = {}
    path = output_root / "train_manifest.json"
    try:
        manifest = _training_core(
            output_root, device=device, replicates=tuple(range(5)),
            updates=FORMAL_UPDATES, formal=True,
            artifact_schema=FORMAL_TRAIN_ARTIFACT_SCHEMA,
            completed_paths=completed_paths, last_evidence=last_evidence,
        )
        return manifest
    except Exception as exception:
        _publish_operational_failure(
            output_root, mode="formal_train", formal=True, stage="training",
            replicate=None, arm=None, cell=None, batch=None,
            exception=exception, completed_paths=completed_paths,
            last_evidence=last_evidence, manifest_path=path,
        )
        raise


def _evaluation_state(
    arm: ArmName, replicate: int, *, profile: str
) -> Any:
    if profile not in ("iid", "held_out"):
        raise ValueError("formal evaluation profile must be iid or held_out")
    return make_training_state(arm, replicate, profile=profile)

def _trajectory_episode_rows(
    trajectory: Any, arm: Any, *, compute_intervention: bool
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Reduce one completed cell batch on device, then transfer it once."""

    device = next(arm.parameters()).device
    kind = trajectory.event_kind.to(device)
    keep = kind.eq(KEEP)
    renew = kind.eq(RENEW)
    opportunity = keep | renew
    counts = torch.stack(
        (
            keep.sum(dim=(0, 2)),
            renew.sum(dim=(0, 2)),
            opportunity.sum(dim=(0, 2)),
            opportunity.sum(dim=0).ge(2).sum(dim=-1),
        ),
        dim=-1,
    )
    if compute_intervention:
        intervention, eligible = batched_natural_and_permuted_action_tv(
            arm, trajectory, device=device
        )
    else:
        intervention = torch.zeros_like(kind, dtype=torch.float32)
        eligible = torch.zeros_like(kind, dtype=torch.bool)
    packed_intervention = torch.stack(
        (eligible.to(intervention.dtype), intervention), dim=-1
    )
    # These are the two completed cell-batch transfer boundaries: reduced
    # episode counts, then packed eligibility/value intervention evidence.
    counts_cpu = counts.detach().cpu()
    intervention_cpu = packed_intervention.detach().cpu()
    rows: list[dict[str, Any]] = []
    for env_index, outcome in enumerate(trajectory.outcomes):
        eligible_values = intervention_cpu[:, env_index, :, 0].bool()
        values = intervention_cpu[:, env_index, :, 1][eligible_values].tolist()
        segments = [
            vars(value) | {"active_lifetime": value.active_lifetime}
            for value in trajectory.segments[env_index]
        ]
        row_counts = counts_cpu[env_index].tolist()
        rows.append({
            "episode_id": trajectory.ledger_ids[env_index],
            "utility": outcome.utility,
            "keep": int(row_counts[0]),
            "renew": int(row_counts[1]),
            "non_create": int(row_counts[2]),
            "multi_opportunity_lifecycles": int(row_counts[3]),
            "segments": segments,
            "intervention": [float(value) for value in values],
        })
    reduction_counts = {
        "keep": sum(row["keep"] for row in rows),
        "renew": sum(row["renew"] for row in rows),
        "non_create": sum(row["non_create"] for row in rows),
        "multi_opportunity_lifecycles": sum(
            row["multi_opportunity_lifecycles"] for row in rows
        ),
        "intervention_values": sum(len(row["intervention"]) for row in rows),
    }
    return rows, reduction_counts


def _natural_fork_key(record: dict[str, Any]) -> tuple[Any, ...]:
    """The frozen action-independent selection key, in registered order."""

    return (
        int(record["replicate"]),
        int(record["base_episode_id"]),
        int(record["sign_parity"]),
        int(record["time"]),
        int(record["key"]),
        int(record["membership_epoch"]),
        int(record["segment_id"]),
        str(record["natural_action"]),
    )


def _collect_natural_fork_evidence(
    arm: Any,
    *,
    replicate: int,
    batches: list[tuple[Any, Any, Mapping[str, Any]]],
    episode_rows: list[dict[str, Any]],
    device: torch.device,
    formal: bool,
    mode: str,
) -> dict[str, Any]:
    """Select before outcome computation, then execute the frozen forks."""

    candidates: dict[str, list[dict[str, Any]]] = {"KEEP": [], "RENEW": []}
    for batch_index, (trajectory, origin_state, _end_states) in enumerate(batches):
        event_metadata = torch.stack(
            (
                trajectory.event_kind,
                trajectory.membership_epoch,
                trajectory.segment_id,
            ),
            dim=-1,
        ).detach().cpu()
        eligible = torch.nonzero(
            event_metadata[..., 0].eq(KEEP) | event_metadata[..., 0].eq(RENEW),
            as_tuple=False,
        ).tolist()
        for time_index, env_index, key in eligible:
            kind = int(event_metadata[time_index, env_index, key, 0])
            action = "KEEP" if kind == KEEP else "RENEW"
            episode_id = int(trajectory.ledger_ids[env_index])
            candidates[action].append({
                "replicate": int(replicate),
                "base_episode_id": episode_id // 2,
                "episode_id": episode_id,
                "sign_parity": episode_id & 1,
                "time": int(time_index),
                "key": int(key),
                "membership_epoch": int(
                    event_metadata[time_index, env_index, key, 1]
                ),
                "segment_id": int(
                    event_metadata[time_index, env_index, key, 2]
                ),
                "natural_action": action,
                "batch_index": batch_index,
                "env_index": int(env_index),
            })
    selected: list[dict[str, Any]] = []
    eligible_keys: dict[str, list[list[Any]]] = {}
    selected_keys: dict[str, list[list[Any]]] = {}
    ordered_by_action = {
        action: sorted(candidates[action], key=_natural_fork_key)
        for action in ("KEEP", "RENEW")
    }
    quota_shortfall = any(
        len(ordered_by_action[action]) < NATURAL_FORK_QUOTA_PER_ACTION
        for action in ("KEEP", "RENEW")
    )
    for action_index, action in enumerate(("KEEP", "RENEW")):
        ordered = ordered_by_action[action]
        eligible_keys[action] = [list(_natural_fork_key(value)) for value in ordered]
        if quota_shortfall:
            selected_keys[action] = []
            continue
        selection_rng = make_rng(
            BOOTSTRAP_SEED,
            NATURAL_FORK_SELECTION_COORDINATE,
            replicate,
            action_index,
        )
        indices = sorted(int(value) for value in selection_rng.choice(
            len(ordered), size=NATURAL_FORK_QUOTA_PER_ACTION, replace=False
        ))
        chosen = [ordered[index] for index in indices]
        selected_keys[action] = [list(_natural_fork_key(value)) for value in chosen]
        selected.extend(chosen)

    utilities = {int(row["episode_id"]): float(row["utility"]) for row in episode_rows}
    fork_rows: list[dict[str, Any]] = []
    selected_for_execution: list[dict[str, Any]] = []
    for record in sorted(selected, key=_natural_fork_key):
        trajectory, origin_state, expected_end_rng_states = batches[
            int(record["batch_index"])
        ]
        key = _natural_fork_key(record)
        selected_for_execution.append({
            **record,
            "fork_id": _digest_json(list(key)),
            "trajectory": trajectory,
            "origin_state": origin_state,
            "expected_end_rng_states": deepcopy(expected_end_rng_states),
        })
    results = fork_opportunities_batched(
        arm, selected_for_execution, device=device
    )
    for record, result in zip(selected_for_execution, results, strict=True):
        natural_utility = utilities[int(record["episode_id"])]
        if record["natural_action"] == "KEEP":
            advantage = float(result["keep_utility"] - result["renew_utility"])
            reproduced = float(result["keep_utility"])
        else:
            advantage = float(result["renew_utility"] - result["keep_utility"])
            reproduced = float(result["renew_utility"])
        if reproduced != natural_utility or result["natural_action"] != record["natural_action"]:
            raise RuntimeError("natural fork failed to reproduce selected episode utility")
        branch_bindings: dict[str, dict[str, Any]] = {}
        for branch_action in ("KEEP", "RENEW"):
            context = {
                "domain": "stage2", "mode": mode, "formal": bool(formal),
                "replicate": int(replicate), "arm": "EHC",
                "cell": "held_out_stochastic",
                "batch": int(record["batch_index"]),
                "fork_id": str(result["fork_id"]),
                "episode_id": int(record["episode_id"]),
                "time": int(record["time"]), "key": int(record["key"]),
                "membership_epoch": int(record["membership_epoch"]),
                "segment_id": int(record["segment_id"]),
                "natural_action": str(record["natural_action"]),
                "branch_action": branch_action,
            }
            branch_bindings[branch_action] = {
                name: make_rng_binding(
                    context=context, stream=name,
                    seed=authoritative_seed_map("held_out", replicate)[name],
                    start_state=result["rng_binding_material"][name]["start_state"],
                    draw_schedule=result["rng_binding_material"][name]["draw_schedule"],
                    expected_end_state=result["rng_binding_material"][name]["end_state"],
                )
                for name in RNG_NAMES
            }
        fork_rows.append({
            **{name: record[name] for name in (
                "replicate", "base_episode_id", "episode_id", "sign_parity",
                "time", "key", "membership_epoch", "segment_id",
                "natural_action",
            )},
            "batch_index": int(record["batch_index"]),
            "env_index": int(record["env_index"]),
            "keep_utility": float(result["keep_utility"]),
            "renew_utility": float(result["renew_utility"]),
            "natural_utility": natural_utility,
            "advantage": advantage,
            "fork_id": str(result["fork_id"]),
            "natural_errors": dict(result["natural_errors"]),
            "rng_bindings": branch_bindings,
            "stream_consumption": {
                action: deepcopy(result["branches"][action]["stream_consumption"])
                for action in ("KEEP", "RENEW")
            },
            "end_rng_digests": {
                name: _digest_json(result["end_rng_states"][name])
                for name in RNG_NAMES
            },
        })
    elapsed = float(results[0]["elapsed_seconds"]) if results else 0.0
    calls = sum(
        math.ceil(count / 8)
        for count in Counter(
            int(value["time"]) for value in selected_for_execution
        ).values()
    )
    return {
        "schema": "event_held_commitment_link_g0.natural_fork.v5",
        "replicate": int(replicate),
        "quota_per_action": NATURAL_FORK_QUOTA_PER_ACTION,
        "eligible_keys": eligible_keys,
        "selected_keys": selected_keys,
        "execution": {
            "engine": "registered_width_batched_v1",
            "registered_width": FORMAL_NUM_ENVS,
            "selected_pairs": len(selected_for_execution),
            "collector_calls": calls,
        },
        "telemetry": {
            "elapsed_seconds": elapsed,
            "pairs_per_second": (
                len(selected_for_execution) / elapsed if elapsed > 0.0 else 0.0
            ),
        },
        "fork_rows": fork_rows,
    }


def _evaluation_core(
    output_root: Path, *, device: torch.device, replicates: tuple[int, ...],
    episodes_per_cell: int, formal: bool, artifact_schema: str,
    checkpoint_name: str, completed_paths: list[str],
    last_evidence: dict[str, Any], failure_context: dict[str, Any],
) -> dict[str, Any]:
    mode = "formal_evaluate" if formal else "formal_path_exercise_evaluate"
    manifest_path = output_root / "evaluation_manifest.json"
    manifest: dict[str, Any] = {
        "artifact_schema": (
            FORMAL_EVALUATION_MANIFEST_SCHEMA
            if formal else EXERCISE_EVALUATION_MANIFEST_SCHEMA
        ),
        "schema_version": EVALUATION_MANIFEST_SCHEMA,
        "formal": formal, "contract": registered_contract(), "mode": mode,
        "status": "IN_PROGRESS", "branch": "IN_PROGRESS",
        "progress": {
            "completed_cells": 0,
            "total_cells": len(replicates) * len(ARMS) * len(EVALUATION_CELLS),
        },
        "cells": [],
    }
    _write_json(manifest_path, manifest)
    publication_ledger_cache: dict[
        tuple[Any, ...], tuple[dict[str, Any], list[Any]]
    ] = {}
    if episodes_per_cell % FORMAL_NUM_ENVS:
        raise ValueError("evaluation cell size must be a whole 16-episode batch")
    for replicate in replicates:
        for arm_name in ARMS:
            failure_context.update({
                "replicate": replicate, "arm": arm_name,
                "cell": None, "batch": None,
            })
            checkpoint = output_root / "train" / f"replicate_{replicate}" / arm_name / checkpoint_name
            arm, _, _, checkpoint_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm_name,
                expected_replicate=replicate, formal_evaluation=formal,
            )
            expected_updates = FORMAL_UPDATES if formal else 1
            if not (
                checkpoint_state.completed_update == expected_updates
                and checkpoint_state.next_episode_id == expected_updates * FORMAL_NUM_ENVS
            ):
                raise RuntimeError("evaluation checkpoint origin state mismatch")
            for profile, deterministic, cell in EVALUATION_CELLS:
                failure_context.update({"cell": cell, "batch": None})
                state = _evaluation_state(arm_name, replicate, profile=profile)
                episode_rows: list[dict[str, Any]] = []
                batches: list[dict[str, Any]] = []
                fork_batches: list[tuple[Any, Any, Mapping[str, Any]]] = []
                for batch_index, start in enumerate(range(0, episodes_per_cell, FORMAL_NUM_ENVS)):
                    failure_context["batch"] = batch_index
                    episode_ids = list(range(start, start + FORMAL_NUM_ENVS))
                    batch_origin = deepcopy(state)
                    trajectory = collect_trajectory(
                        arm, state, device=device, episode_ids=episode_ids,
                        deterministic=deterministic, profile=profile,
                    )
                    _replay, replay_evidence = validate_replay(
                        arm, trajectory, device=device
                    )
                    rows, reduction_counts = _trajectory_episode_rows(
                        trajectory, arm,
                        compute_intervention=(cell == "held_out_stochastic"),
                    )
                    batch_evidence = {
                        "batch_index": batch_index,
                        "episode_ids": episode_ids,
                        "replay": replay_evidence,
                        "lifecycle_counts": _lifecycle_counts(trajectory),
                        "finite_checks": _finite_checks(trajectory),
                        "seed_map": dict(state.seed_map),
                        "owned_stream_digests": _owned_stream_digests(state),
                        "rng_bindings": _collection_rng_bindings(
                            context={
                                "domain": "evaluation", "mode": mode,
                                "formal": bool(formal),
                                "replicate": int(replicate), "arm": arm_name,
                                "cell": cell, "batch": batch_index,
                            },
                            seed_map=state.seed_map,
                            start_states=owned_rng_states(batch_origin),
                            end_states=owned_rng_states(state),
                            trajectory=trajectory,
                            deterministic=deterministic,
                        ),
                        "rng_evidence": deepcopy(trajectory.rng_audit),
                        "reduction_counts": reduction_counts,
                        "checkpoint_origin": checkpoint_name,
                        "episodes_digest": _digest_json(rows),
                    }
                    if not (
                        _replay_record_valid(
                            replay_evidence, event_rows_required=arm_name != "OR"
                        )
                        and batch_evidence["lifecycle_counts"]["invalid_segment_lifetimes"] == 0
                        and all(value == 0 for value in batch_evidence["finite_checks"].values())
                        and batch_evidence["seed_map"] == authoritative_seed_map(profile, replicate)
                    ):
                        raise RuntimeError(
                            f"{mode} recomputable batch evidence failed "
                            f"{replicate}:{arm_name}:{cell}:{batch_index}"
                        )
                    batches.append(batch_evidence)
                    episode_rows.extend(rows)
                    if arm_name == "EHC" and cell == "held_out_stochastic":
                        fork_batches.append((
                            trajectory, batch_origin, owned_rng_states(state)
                        ))
                failure_context["batch"] = None
                natural_fork = (
                    _collect_natural_fork_evidence(
                        arm,
                        replicate=replicate,
                        batches=fork_batches,
                        episode_rows=episode_rows,
                        device=device,
                        formal=formal,
                        mode=mode,
                    )
                    if arm_name == "EHC" and cell == "held_out_stochastic"
                    else None
                )
                payload = {
                    "artifact_schema": artifact_schema,
                    "schema_version": EVALUATION_CELL_SCHEMA,
                    "formal": formal,
                    "contract": registered_contract(),
                    "arm": arm_name, "replicate": replicate, "cell": cell,
                    "profile": profile,
                    "mode": "deterministic" if deterministic else "stochastic",
                    "checkpoint": _root_relative_path(output_root, checkpoint),
                    "checkpoint_origin": checkpoint_name,
                    "counts": {
                        "episodes": len(episode_rows), "horizon": HORIZON,
                        "batch_size": FORMAL_NUM_ENVS, "batches": len(batches),
                    },
                    "batches": batches,
                    "natural_fork": natural_fork,
                    "operational": True,
                    "episodes": episode_rows,
                }
                cell_valid, _episode_ids, _rng_digests = _evaluation_cell_valid(
                    payload, replicate=replicate, arm=arm_name, profile=profile,
                    deterministic=deterministic, cell=cell, formal=formal,
                    mode=mode, episodes_per_cell=episodes_per_cell,
                    checkpoint_origin=checkpoint_name,
                    checkpoint_path=_root_relative_path(output_root, checkpoint),
                    ledger_cache=publication_ledger_cache,
                )
                if not cell_valid:
                    raise RuntimeError(
                        f"{mode} strict cell evidence failed "
                        f"{replicate}:{arm_name}:{cell}"
                    )
                path = output_root / "evaluation" / f"replicate_{replicate}" / arm_name / f"{cell}.json"
                _write_json(path, payload)
                reference = _artifact_reference(
                    output_root, path, replicate=replicate, arm=arm_name, cell=cell,
                )
                manifest["cells"].append(reference)
                manifest["progress"]["completed_cells"] = len(manifest["cells"])
                _write_json(manifest_path, manifest)
                completed_paths.append(reference["path"])
                last_evidence.clear(); last_evidence.update(reference)
                del payload, batches, episode_rows, natural_fork
    manifest["status"] = "COMPLETE"
    manifest["branch"] = (
        "FORMAL_EVALUATION_COMPLETE" if formal
        else "FORMAL_PATH_EXERCISE_EVALUATION_COMPLETE"
    )
    _write_json(manifest_path, manifest)
    return manifest


def formal_evaluate(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal evaluation requires the exact authorization token")
    device = require_registered_backend(device_name)
    completed_paths: list[str] = []
    last_evidence: dict[str, Any] = {}
    failure_context: dict[str, Any] = {
        "replicate": None, "arm": None, "cell": None, "batch": None,
    }
    path = output_root / "evaluation_manifest.json"
    try:
        manifest = _evaluation_core(
            output_root, device=device, replicates=tuple(range(5)),
            episodes_per_cell=FORMAL_EVAL_EPISODES, formal=True,
            artifact_schema=FORMAL_EVALUATION_ARTIFACT_SCHEMA,
            checkpoint_name="update_250.pt", completed_paths=completed_paths,
            last_evidence=last_evidence, failure_context=failure_context,
        )
        return manifest
    except Exception as exception:
        _publish_operational_failure(
            output_root, mode="formal_evaluate", formal=True, stage="evaluation",
            replicate=failure_context["replicate"], arm=failure_context["arm"],
            cell=failure_context["cell"], batch=failure_context["batch"],
            exception=exception, completed_paths=completed_paths,
            last_evidence=last_evidence, manifest_path=path,
        )
        raise


def formal_path_exercise(output_root: Path, *, device_name: str) -> dict[str, Any]:
    """Bounded non-formal CUDA exercise over the exact formal cores."""

    if device_name != "cuda":
        raise ValueError("formal_path_exercise requires cuda and has no CPU fallback")
    device = require_registered_backend(device_name)
    exercise_root = output_root / "formal_path_exercise"
    completed_paths: list[str] = []
    last_evidence: dict[str, Any] = {}
    failure_context: dict[str, Any] = {
        "replicate": None, "arm": None, "cell": None, "batch": None,
    }
    terminal_path = exercise_root / "manifest.json"
    try:
        training = _training_core(
            exercise_root, device=device, replicates=(0,), updates=1,
            formal=False, artifact_schema=EXERCISE_TRAIN_ARTIFACT_SCHEMA,
            completed_paths=completed_paths, last_evidence=last_evidence,
        )
        train_path = exercise_root / "train_manifest.json"
        completed_paths.append(_root_relative_path(exercise_root, train_path))
        evaluation = _evaluation_core(
            exercise_root, device=device, replicates=(0,),
            episodes_per_cell=FORMAL_NUM_ENVS, formal=False,
            artifact_schema=EXERCISE_EVALUATION_ARTIFACT_SCHEMA,
            checkpoint_name="update_1.pt", completed_paths=completed_paths,
            last_evidence=last_evidence, failure_context=failure_context,
        )
        evaluation_path = exercise_root / "evaluation_manifest.json"
        completed_paths.append(_root_relative_path(exercise_root, evaluation_path))
        stage2_reference = next(
            reference for reference in evaluation["cells"]
            if (
                reference["replicate"], reference["arm"], reference["cell"]
            ) == (0, "EHC", "held_out_stochastic")
        )
        stage2_path = _resolve_artifact_path(
            exercise_root, stage2_reference["path"]
        )
        with stage2_path.open("r", encoding="utf-8") as handle:
            stage2 = json.load(handle)["natural_fork"]["execution"]
        if not (
            stage2["engine"] == "registered_width_batched_v1"
            and int(stage2["selected_pairs"]) > 0
            and int(stage2["collector_calls"]) > 0
        ):
            raise RuntimeError("formal path exercise did not execute Stage-2 batches")
        result = {
            "artifact_schema": EXERCISE_MANIFEST_SCHEMA,
            "formal": False,
            "mode": "formal_path_exercise",
            "device": "cuda",
            "replicates": [0],
            "arms": list(ARMS),
            "updates": 1,
            "num_envs": FORMAL_NUM_ENVS,
            "horizon": HORIZON,
            "ppo_passes": PPO_PASSES,
            "evaluation_cells": [cell for _profile, _deterministic, cell in EVALUATION_CELLS],
            "episodes_per_cell": FORMAL_NUM_ENVS,
            "checkpoint_origin": "update_1.pt",
            "stage2": stage2,
            "status": "FORMAL_PATH_EXERCISE_COMPLETE",
            "branch": "FORMAL_PATH_EXERCISE_COMPLETE",
            "training_manifest": str(train_path),
            "evaluation_manifest": str(evaluation_path),
        }
        _write_json(terminal_path, result)
        return result
    except Exception as exception:
        _publish_operational_failure(
            exercise_root, mode="formal_path_exercise", formal=False,
            stage="exercise", replicate=failure_context["replicate"],
            arm=failure_context["arm"], cell=failure_context["cell"],
            batch=failure_context["batch"],
            exception=exception, completed_paths=completed_paths,
            last_evidence=last_evidence, manifest_path=terminal_path,
        )
        raise

def _percentile(values: list[float]) -> tuple[float, float]:
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def _empty_natural_fork_summary() -> dict[str, Any]:
    return {
        "natural_keep_rows_by_replicate": (0,) * NATURAL_FORK_REPLICATES,
        "natural_renew_rows_by_replicate": (0,) * NATURAL_FORK_REPLICATES,
        "a_keep_ci": (0.0, 0.0),
        "a_renew_ci": (0.0, 0.0),
        "a_keep_mean": 0.0,
        "a_renew_mean": 0.0,
    }


def _aggregate_analysis_core(
    output_root: Path, *, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal analysis requires the exact authorization token")
    training_identity = _load_json_file(output_root / "train_manifest.json")
    if isinstance(training_identity, dict) and (
        training_identity.get("formal") is False
        or training_identity.get("artifact_schema") == EXERCISE_TRAIN_ARTIFACT_SCHEMA
    ):
        raise ValueError("formal analyzer rejects non-formal training artifacts")
    operational_valid, operational_errors, compact = (
        _validate_streamed_operational_records(output_root)
    )
    if not operational_valid:
        inputs = {
            "operational_valid": False,
            "non_create_opportunities": 0,
            "multi_opportunity_lifecycles": 0,
            "eligible_keep_rows": 0,
            "eligible_renew_rows": 0,
            "utility_ci": {arm: (0.0, 0.0) for arm in ARMS},
            "g_ci": (0.0, 0.0),
            "k_bin_cis": [(0.0, 0.0)] * 3,
            "intervention_ci": (0.0, 0.0),
            **_empty_natural_fork_summary(),
        }
        result = {
            "artifact_schema": FORMAL_ANALYSIS_ARTIFACT_SCHEMA,
            "formal": True,
            "status": "COMPLETE",
            "branch": select_result_branch(**inputs),
            "predicate_inputs": inputs,
            "operational_errors": operational_errors,
            "registered_contract": REGISTERED_CONTRACT,
        }
        _write_json(output_root / "analysis_result.json", result)
        return result

    data = compact["episodes"]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    utilities = {arm: [] for arm in ARMS}
    gains: list[float] = []
    secondary_gains: list[float] = []
    keep_values: list[float] = []
    renew_values: list[float] = []
    cv_values: list[float] = []
    bin_values: list[list[float]] = [[], [], []]
    k_bin_values: list[list[float]] = [[], [], []]
    k_bin_predicates = (
        lambda k: k == 1, lambda k: k == 2, lambda k: k >= 3,
    )
    intervention_values: list[float] = []
    fork_rows = compact["fork_rows"]
    fork_by_base_episode = {
        action: {
            replicate: {
                base_episode_id: [
                    float(row["advantage"])
                    for row in fork_rows[replicate]
                    if row["natural_action"] == action
                    and int(row["base_episode_id"]) == base_episode_id
                ]
                for base_episode_id in range(FORMAL_EVAL_EPISODES // 2)
            }
            for replicate in range(5)
        }
        for action in ("KEEP", "RENEW")
    }
    a_keep_values: list[float] = []
    a_renew_values: list[float] = []
    for _ in range(BOOTSTRAP_REPETITIONS):
        sampled_replicates = rng.integers(0, 5, size=5)
        sampled: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
        sampled_base_indices: list[np.ndarray] = []
        for replicate in sampled_replicates:
            base_indices = rng.integers(
                0,
                FORMAL_EVAL_EPISODES // 2,
                size=FORMAL_EVAL_EPISODES // 2,
            )
            sampled_base_indices.append(base_indices)
            episode_indices = np.stack(
                (2 * base_indices, 2 * base_indices + 1), axis=-1
            ).reshape(-1)
            for arm in ARMS:
                sampled[arm].extend(
                    data[(int(replicate), arm)][int(index)]
                    for index in episode_indices
                )
        means = {
            arm: float(np.mean([row["utility"] for row in rows]))
            for arm, rows in sampled.items()
        }
        for arm in ARMS:
            utilities[arm].append(means[arm])
        gains.append(means["EHC"] - means["DUM"])
        secondary_gains.append(means["EHC"] - means["OR"])
        ehc = sampled["EHC"]
        keep = sum(row["keep"] for row in ehc)
        renew = sum(row["renew"] for row in ehc)
        opportunities = keep + renew
        keep_values.append(keep / max(opportunities, 1))
        renew_values.append(renew / max(opportunities, 1))
        complete_segments = [
            segment
            for row in ehc for segment in row["segments"]
            if not segment["censored"]
        ]
        lifetimes = [segment["active_lifetime"] for segment in complete_segments]
        cv_values.append(
            float(np.std(lifetimes) / max(np.mean(lifetimes), 1e-12))
            if lifetimes else 0.0
        )
        for index, (low, high) in enumerate(
            ((1, 8), (9, 16), (17, float("inf")))
        ):
            bin_values[index].append(
                sum(low <= value <= high for value in lifetimes)
                / max(len(lifetimes), 1)
            )
        k_values = [segment["opportunity_count"] for segment in complete_segments]
        for index, predicate in enumerate(k_bin_predicates):
            k_bin_values[index].append(
                sum(predicate(value) for value in k_values)
                / max(len(k_values), 1)
            )
        intervention = [value for row in ehc for value in row["intervention"]]
        intervention_values.append(
            float(np.mean(intervention)) if intervention else 0.0
        )
        for action, destination in (
            ("KEEP", a_keep_values), ("RENEW", a_renew_values)
        ):
            sampled_advantages: list[float] = []
            for replicate, base_indices in zip(
                sampled_replicates, sampled_base_indices
            ):
                for base_episode_id in base_indices:
                    sampled_advantages.extend(
                        fork_by_base_episode[action][int(replicate)][
                            int(base_episode_id)
                        ]
                    )
            if not sampled_advantages:
                raise RuntimeError("natural fork bootstrap drew no selected clusters")
            destination.append(float(np.mean(sampled_advantages)))
    utility_ci = {
        arm: _percentile(values) for arm, values in utilities.items()
    }
    ehc_rows = [
        row for replicate in range(5) for row in data[(replicate, "EHC")]
    ]
    complete_segment_count = sum(
        1 for row in ehc_rows for segment in row["segments"]
        if not segment["censored"]
    )
    censored_segment_count = sum(
        1 for row in ehc_rows for segment in row["segments"]
        if segment["censored"]
    )
    inputs = {
        "operational_valid": True,
        "non_create_opportunities": sum(
            row["non_create"] for row in ehc_rows
        ),
        "multi_opportunity_lifecycles": sum(
            row["multi_opportunity_lifecycles"] for row in ehc_rows
        ),
        "eligible_keep_rows": sum(row["keep"] for row in ehc_rows),
        "eligible_renew_rows": sum(row["renew"] for row in ehc_rows),
        "utility_ci": utility_ci,
        "g_ci": _percentile(gains),
        "k_bin_cis": [_percentile(values) for values in k_bin_values],
        "intervention_ci": _percentile(intervention_values),
        "natural_keep_rows_by_replicate": tuple(
            sum(row["natural_action"] == "KEEP" for row in fork_rows[replicate])
            for replicate in range(5)
        ),
        "natural_renew_rows_by_replicate": tuple(
            sum(row["natural_action"] == "RENEW" for row in fork_rows[replicate])
            for replicate in range(5)
        ),
        "a_keep_ci": _percentile(a_keep_values),
        "a_renew_ci": _percentile(a_renew_values),
        "a_keep_mean": float(np.mean([
            row["advantage"] for rows in fork_rows.values() for row in rows
            if row["natural_action"] == "KEEP"
        ])),
        "a_renew_mean": float(np.mean([
            row["advantage"] for rows in fork_rows.values() for row in rows
            if row["natural_action"] == "RENEW"
        ])),
    }
    result = {
        "artifact_schema": FORMAL_ANALYSIS_ARTIFACT_SCHEMA,
        "formal": True,
        "status": "COMPLETE",
        "branch": select_result_branch(**inputs),
        "predicate_inputs": inputs,
        "diagnostics": {
            "keep_ci": _percentile(keep_values),
            "renew_ci": _percentile(renew_values),
            "cv_ci": _percentile(cv_values),
            "physical_time_bin_cis": [_percentile(values) for values in bin_values],
            "complete_segment_count": complete_segment_count,
            "censored_segment_count": censored_segment_count,
        },
        "secondary_v_ci": _percentile(secondary_gains),
        "operational_errors": [],
        "registered_contract": REGISTERED_CONTRACT,
    }
    _write_json(output_root / "analysis_result.json", result)
    return result


def aggregate_analysis(
    output_root: Path, *, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal analysis requires the exact authorization token")
    path = output_root / "analysis_result.json"
    completed_paths: list[str] = []
    try:
        return _aggregate_analysis_core(output_root, authorization=authorization)
    except Exception as exception:
        _publish_operational_failure(
            output_root, mode="formal_analyze", formal=True, stage="analysis",
            replicate=None, arm=None, cell=None, batch=None,
            exception=exception, completed_paths=completed_paths,
            last_evidence=None, manifest_path=path,
        )
        raise

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("contract", "smoke", "train", "evaluate", "analyze", "formal_path_exercise"), default="contract"); parser.add_argument("--output-root", type=Path, default=Path("logs/event_held_commitment_link_g0")); parser.add_argument("--device", choices=REGISTERED_EXECUTION_BACKENDS, default=FORMAL_EXECUTION_BACKEND); parser.add_argument("--authorize-formal", default=""); return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Every mode activates the backend first, including `contract` and
    # `analyze`: the contract carries the execution environment, so it cannot
    # be printed or compared before that environment is registered.
    require_registered_backend(args.device)
    if args.mode == "contract": result = registered_contract()
    elif args.mode == "smoke": result = run_smoke(args.output_root, device_name=args.device)
    elif args.mode == "train": result = formal_train(args.output_root, device_name=args.device, authorization=args.authorize_formal)
    elif args.mode == "evaluate": result = formal_evaluate(args.output_root, device_name=args.device, authorization=args.authorize_formal)
    elif args.mode == "formal_path_exercise":
        if args.authorize_formal:
            raise PermissionError("formal_path_exercise never accepts a formal authorization token")
        result = formal_path_exercise(args.output_root, device_name=args.device)
    else: result = aggregate_analysis(args.output_root, authorization=args.authorize_formal)
    print(json.dumps(result, ensure_ascii=False, default=_json_default)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
