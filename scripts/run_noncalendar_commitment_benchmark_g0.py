"""Package EVENT_HELD_COMMITMENT_LINK_G0 contract, smoke, train, eval, analysis."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.event_held_commitment_link import (
    ArmName,
    CREATE,
    KEEP,
    RENEW,
    RNG_NAMES,
    authoritative_seed_map,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    natural_and_permuted_action_tv,
    nested_state_maximum_difference,
    optimize_update,
    parameter_and_optimizer_counts,
    replay_errors,
    replay_trajectory,
    runtime_rng_snapshot,
    save_checkpoint,
    validate_replay,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    EVENT_JOINT_FACTOR_COUNT,
    FORMAL_EVAL_EPISODES,
    FORMAL_EXECUTION_BACKEND,
    FORMAL_UPDATES,
    HORIZON,
    NATURAL_FORK_REPLICATES,
    REGISTERED_CONTRACT,
    REGISTERED_EXECUTION_BACKENDS,
    REPLAY_COMPONENT_FIELDS,
    REPLAY_COMPONENT_TOLERANCE,
    REPLAY_EXACT_FIELDS,
    REPLAY_JOINT_FIELDS,
    REPLAY_JOINT_RECORD_FIELDS,
    registered_contract,
    require_registered_backend,
    select_result_branch,
)

FORMAL_AUTHORIZATION = "AUTHORIZE_EVENT_HELD_COMMITMENT_LINK_G0_FORMAL"
TRAIN_MANIFEST_SCHEMA = 1
# 2: the replay record is the named per-factor error dictionary plus the
# derived joint bounds actually applied and a normalized pass result, not a
# single `maximum_error` scalar. Collapsing them hid which factor moved.
EVALUATION_CELL_SCHEMA = 2
ARMS: tuple[ArmName, ...] = ("OR", "DUM", "EHC")
EVALUATION_CELLS = (
    ("iid", True, "iid_deterministic"),
    ("iid", False, "iid_stochastic"),
    ("held_out", True, "held_out_deterministic"),
    ("held_out", False, "held_out_stochastic"),
)


# Stage 2 (the batched fork engine and its aggregation) is not wired, so this
# runner has no A_KEEP/A_RENEW evidence to supply. It reports the evidence as
# absent rather than as neutral: zero eligible rows per replicate resolves at
# precedence position 2 to BENCHMARK_NON_IDENTIFIABLE, so an unevidenced run
# cannot reach COMMITMENT_SUPPORTED. Replacing these with real aggregates is the
# analyzer-wiring task; nothing here is a default that could survive it.
ABSENT_NATURAL_FORK_EVIDENCE: dict[str, Any] = {
    "natural_keep_rows_by_replicate": (0,) * NATURAL_FORK_REPLICATES,
    "natural_renew_rows_by_replicate": (0,) * NATURAL_FORK_REPLICATES,
    "a_keep_ci": (0.0, 0.0),
    "a_renew_ci": (0.0, 0.0),
    "a_keep_mean": 0.0,
    "a_renew_mean": 0.0,
}


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_json_ready(v) for v in value]
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, torch.Tensor): return value.detach().cpu().tolist()
    if hasattr(value, "__dict__"): return _json_ready(vars(value))
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(value), indent=2, ensure_ascii=False), encoding="utf-8")


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
    {"errors", "joints", "component_tolerance", "failures", "passed"}
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

    if not isinstance(record, dict):
        return False
    for value in record.get("errors", {}).values():
        if not math.isfinite(float(value)):
            return False
    for joint in record.get("joints", {}).values():
        if not isinstance(joint, dict):
            return False
        for value in joint.values():
            if not math.isfinite(float(value)):
                return False
    return math.isfinite(float(record.get("component_tolerance", float("nan"))))


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
    tolerances = {float(record["component_tolerance"]) for record in records}
    if len(tolerances) != 1:
        raise ValueError(f"replay records disagree on component tolerance {tolerances}")
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
    failures = sorted(
        {name for record in records for name in record["failures"]}
    )
    return {
        "errors": errors,
        "joints": joints,
        "component_tolerance": tolerances.pop(),
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
    if float(record["component_tolerance"]) != REPLAY_COMPONENT_TOLERANCE:
        return False
    if record.get("passed") is not True or record.get("failures"):
        return False
    if any(float(errors[name]) != 0.0 for name in REPLAY_EXACT_FIELDS):
        return False
    if any(
        not float(errors[name]) <= REPLAY_COMPONENT_TOLERANCE
        for name in REPLAY_COMPONENT_FIELDS
    ):
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


def validate_operational_records(
    training_manifest: dict[str, Any],
    evaluation_payloads: dict[tuple[int, str, str], dict[str, Any]],
    *,
    expected_replicates: tuple[int, ...] = tuple(range(5)),
) -> tuple[bool, list[str]]:
    """Fail-closed validation of all conclusion-bearing operational evidence."""

    errors: list[str] = []
    if set(training_manifest) != {
        "schema_version", "contract", "mode", "replicates"
    }:
        errors.append("training_manifest_schema")
    if training_manifest.get("schema_version") != TRAIN_MANIFEST_SCHEMA:
        errors.append("training_manifest_version")
    if training_manifest.get("contract") != registered_contract():
        errors.append("training_manifest_contract")
    if training_manifest.get("mode") != "formal_train":
        errors.append("training_manifest_mode")
    replicates = training_manifest.get("replicates", {})
    if set(replicates) != {str(value) for value in expected_replicates}:
        errors.append("training_replicate_set")
    for replicate in expected_replicates:
        record = replicates.get(str(replicate), {})
        if set(record) != {"operational", "updates", "arms"}:
            errors.append(f"training_record_schema:{replicate}")
            continue
        operational = record.get("operational", {})
        required_families = {
            "no_op", "probability_replay", "lifecycle", "finiteness",
            "rng_pairing", "checkpoint_resume", "exposure",
        }
        if set(operational) != required_families or not all(
            operational.get(name) is True for name in required_families
        ):
            errors.append(f"training_operational:{replicate}")
        if len(record.get("updates", [])) != FORMAL_UPDATES:
            errors.append(f"training_update_count:{replicate}")
        arms = record.get("arms", {})
        if set(arms) != set(ARMS):
            errors.append(f"training_arm_set:{replicate}")
            continue
        for arm in ARMS:
            entry = arms[arm]
            expected_event = 0 if arm == "OR" else 1000
            if (
                entry.get("arm") != arm
                or entry.get("replicate") != replicate
                or entry.get("checkpoint_origin") != "update_250.pt"
                or entry.get("completed_update") != 250
                or entry.get("next_episode_id") != 4000
                or entry.get("base_steps") != 1000
                or entry.get("event_steps") != expected_event
                or entry.get("seed_map") != authoritative_seed_map("train", replicate)
                or entry.get("checkpoint_resume") is not True
            ):
                errors.append(f"training_arm_evidence:{replicate}:{arm}")

    expected_keys = {
        (replicate, arm, cell)
        for replicate in expected_replicates
        for arm in ARMS
        for _profile, _deterministic, cell in EVALUATION_CELLS
    }
    if set(evaluation_payloads) != expected_keys:
        errors.append("evaluation_artifact_set")
    for replicate in expected_replicates:
        for profile, deterministic, cell in EVALUATION_CELLS:
            paired_ids: tuple[int, ...] | None = None
            for arm in ARMS:
                payload = evaluation_payloads.get((replicate, arm, cell), {})
                required = {
                    "schema_version", "contract", "arm", "replicate", "cell",
                    "profile", "mode", "checkpoint", "checkpoint_origin",
                    "counts", "seed_map", "replay", "operational", "episodes",
                }
                if set(payload) != required:
                    errors.append(f"evaluation_schema:{replicate}:{arm}:{cell}")
                    continue
                expected_mode = "deterministic" if deterministic else "stochastic"
                counts = payload.get("counts", {})
                operational = payload.get("operational", {})
                training_checkpoint = (
                    replicates.get(str(replicate), {})
                    .get("arms", {}).get(arm, {}).get("checkpoint")
                )
                if (
                    payload.get("schema_version") != EVALUATION_CELL_SCHEMA
                    or payload.get("contract") != registered_contract()
                    or payload.get("arm") != arm
                    or payload.get("replicate") != replicate
                    or payload.get("cell") != cell
                    or payload.get("profile") != profile
                    or payload.get("mode") != expected_mode
                    or payload.get("checkpoint_origin") != "update_250.pt"
                    or payload.get("checkpoint") != training_checkpoint
                    or counts != {"episodes": FORMAL_EVAL_EPISODES, "horizon": HORIZON}
                    or payload.get("seed_map") != authoritative_seed_map(profile, replicate)
                    or set(operational) != {"probability_replay", "lifecycle", "rng", "checkpoint", "finite"}
                    or not all(value is True for value in operational.values())
                    or not _replay_record_valid(
                        payload.get("replay"), event_rows_required=arm != "OR"
                    )
                ):
                    errors.append(f"evaluation_operational:{replicate}:{arm}:{cell}")
                episode_ids = tuple(
                    int(value.get("episode_id", -1))
                    for value in payload.get("episodes", [])
                )
                if episode_ids != tuple(range(FORMAL_EVAL_EPISODES)):
                    errors.append(f"evaluation_episode_ids:{replicate}:{arm}:{cell}")
                if paired_ids is None:
                    paired_ids = episode_ids
                elif episode_ids != paired_ids:
                    errors.append(f"evaluation_pairing:{replicate}:{cell}")
    return not errors, errors


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


def formal_train(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal train requires the exact authorization token")
    device = require_registered_backend(device_name)
    manifest: dict[str, Any] = {
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "contract": registered_contract(),
        "mode": "formal_train",
        "replicates": {},
    }
    for replicate in range(5):
        arms, base_optimizers, event_optimizers = initialize_arms(
            device, replicate=replicate
        )
        states = {arm: make_training_state(arm, replicate) for arm in ARMS}
        update_evidence: list[dict[str, Any]] = []
        all_operational = {
            "no_op": True,
            "probability_replay": True,
            "lifecycle": True,
            "finiteness": True,
            "rng_pairing": True,
            "checkpoint_resume": True,
            "exposure": True,
        }
        for update_index in range(FORMAL_UPDATES):
            trajectories = {
                arm: collect_trajectory(
                    arms[arm], states[arm], device=device
                )
                for arm in ARMS
            }
            no_op = _no_op_equal(trajectories["OR"], trajectories["DUM"])
            rng_pairing = bool(
                _owned_rng_equal(
                    states["OR"], states["DUM"],
                    ("ledger", "order", "primitive"),
                )
                and _owned_rng_equal(
                    states["DUM"], states["EHC"],
                    ("ledger", "order", "primitive", "opportunity", "event", "mark"),
                )
            )
            lifecycle = all(
                _lifecycle_valid(trajectories[arm], arm) for arm in ARMS
            )
            update_metrics = {
                arm: optimize_update(
                    arms[arm], base_optimizers[arm], event_optimizers[arm],
                    states[arm], trajectories[arm], device=device,
                )
                for arm in ARMS
            }
            # Validate per arm, never merged across arms. `merge_replay_records`
            # takes field-wise extrema, which is coherent across batches of one
            # arm but not across arms: the event joint would take `rows` from an
            # event-bearing arm and `factor_count` from OR, which carries no
            # event head, producing a record no single arm ever emitted.
            replay_records = {
                arm: update_metrics[arm]["replay"] for arm in ARMS
            }
            replay_valid = all(
                _replay_record_valid(
                    replay_records[arm], event_rows_required=arm != "OR"
                )
                for arm in ARMS
            )
            finite = all(metrics["finite"] for metrics in update_metrics.values())
            exposure = all(
                metrics["base_steps"] == 4
                and metrics["primitive_replays"] == 4
                and metrics["packed_trajectory_count"] == 1
                and metrics["event_steps"] == (0 if arm == "OR" else 4)
                for arm, metrics in update_metrics.items()
            )
            base_noop_error = nested_state_maximum_difference(
                arms["OR"].base.state_dict(), arms["DUM"].base.state_dict()
            )
            no_op = no_op and base_noop_error == 0.0
            current = {
                "update": update_index + 1,
                "no_op": no_op,
                "base_noop_error": base_noop_error,
                "replay": replay_records,
                "lifecycle": lifecycle,
                "finite": finite,
                "rng_pairing": rng_pairing,
                "exposure": exposure,
            }
            update_evidence.append(current)
            all_operational["no_op"] &= no_op
            all_operational["probability_replay"] &= replay_valid
            all_operational["lifecycle"] &= lifecycle
            all_operational["finiteness"] &= finite
            all_operational["rng_pairing"] &= rng_pairing
            all_operational["exposure"] &= exposure
            if not all(
                (no_op, replay_valid, lifecycle, finite, rng_pairing, exposure)
            ):
                raise RuntimeError(f"formal training operational failure {current}")

        arm_records: dict[str, Any] = {}
        for arm in ARMS:
            checkpoint = (
                output_root / "train" / f"replicate_{replicate}"
                / arm / "update_250.pt"
            )
            save_checkpoint(
                checkpoint, arm=arms[arm], base_optimizer=base_optimizers[arm],
                event_optimizer=event_optimizers[arm], state=states[arm],
            )
            loaded_arm, loaded_base, loaded_event, loaded_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm,
                expected_replicate=replicate, formal_evaluation=True,
            )
            resume_valid = bool(
                nested_state_maximum_difference(
                    arms[arm].state_dict(), loaded_arm.state_dict()
                ) == 0.0
                and nested_state_maximum_difference(
                    base_optimizers[arm].state_dict(), loaded_base.state_dict()
                ) == 0.0
                and nested_state_maximum_difference(
                    None if event_optimizers[arm] is None else event_optimizers[arm].state_dict(),
                    None if loaded_event is None else loaded_event.state_dict(),
                ) == 0.0
                and loaded_state.completed_update == FORMAL_UPDATES
                and loaded_state.next_episode_id == 4000
            )
            all_operational["checkpoint_resume"] &= resume_valid
            arm_records[arm] = {
                "arm": arm,
                "replicate": replicate,
                "checkpoint": str(checkpoint),
                "checkpoint_origin": "update_250.pt",
                "completed_update": states[arm].completed_update,
                "next_episode_id": states[arm].next_episode_id,
                "base_steps": states[arm].base_optimizer_steps,
                "event_steps": states[arm].event_optimizer_steps,
                "seed_map": dict(states[arm].seed_map),
                "checkpoint_resume": resume_valid,
            }
        if not all(all_operational.values()):
            raise RuntimeError(
                f"formal training terminal operational failure {all_operational}"
            )
        manifest["replicates"][str(replicate)] = {
            "operational": all_operational,
            "updates": update_evidence,
            "arms": arm_records,
        }
    _write_json(output_root / "train_manifest.json", manifest)
    return manifest


def _evaluation_state(
    arm: ArmName, replicate: int, *, profile: str
) -> Any:
    if profile not in ("iid", "held_out"):
        raise ValueError("formal evaluation profile must be iid or held_out")
    return make_training_state(arm, replicate, profile=profile)

def _trajectory_episode_rows(
    trajectory: Any, arm: Any, *, compute_intervention: bool
) -> list[dict[str, Any]]:
    rows = []
    device = next(arm.parameters()).device
    for env_index, outcome in enumerate(trajectory.outcomes):
        kinds = trajectory.event_kind[:, env_index]
        intervention: list[float] = []
        if compute_intervention and arm.arm == "EHC" and arm.W_z is not None:
            for time in range(trajectory.time_steps):
                intervention.extend(
                    natural_and_permuted_action_tv(
                        arm, trajectory, env_index=env_index, time=time, device=device
                    )
                )
        segments = [vars(v) | {"active_lifetime": v.active_lifetime} for v in trajectory.segments[env_index]]
        rows.append({"episode_id": trajectory.ledger_ids[env_index], "utility": outcome.utility, "keep": int((kinds == KEEP).sum()), "renew": int((kinds == RENEW).sum()), "non_create": int(((kinds == KEEP) | (kinds == RENEW)).sum()), "multi_opportunity_lifecycles": int(sum(int((((kinds == KEEP) | (kinds == RENEW))[:, key]).sum()) >= 2 for key in range(kinds.shape[-1]))), "segments": segments, "intervention": intervention})
    return rows


def formal_evaluate(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal evaluation requires the exact authorization token")
    device = require_registered_backend(device_name)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "contract": registered_contract(),
        "mode": "formal_evaluate",
        "artifacts": {},
    }
    for replicate in range(5):
        for arm_name in ARMS:
            checkpoint = (
                output_root / "train" / f"replicate_{replicate}"
                / arm_name / "update_250.pt"
            )
            arm, _, _, checkpoint_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm_name,
                expected_replicate=replicate, formal_evaluation=True,
            )
            for profile, deterministic, cell in EVALUATION_CELLS:
                state = _evaluation_state(
                    arm_name, replicate, profile=profile
                )
                episode_rows: list[dict[str, Any]] = []
                replay_records: list[dict[str, Any]] = []
                lifecycle_valid = True
                finite = True
                for start in range(0, FORMAL_EVAL_EPISODES, 16):
                    trajectory = collect_trajectory(
                        arm, state, device=device,
                        episode_ids=range(start, start + 16),
                        deterministic=deterministic, profile=profile,
                    )
                    _replay, replay_evidence = validate_replay(
                        arm, trajectory, device=device
                    )
                    replay_records.append(replay_evidence)
                    lifecycle_valid &= _lifecycle_valid(trajectory, arm_name)
                    finite &= all(
                        bool(torch.isfinite(getattr(trajectory, name)).all().detach().cpu())
                        for name in (
                            "old_log_probs", "old_values", "hidden_after",
                            "event_old_joint_logp",
                        )
                    )
                    episode_rows.extend(
                        _trajectory_episode_rows(
                            trajectory, arm,
                            compute_intervention=(cell == "held_out_stochastic"),
                        )
                    )
                replay_record = merge_replay_records(replay_records)
                operational = {
                    "probability_replay": _replay_record_valid(
                        replay_record, event_rows_required=arm_name != "OR"
                    ),
                    "lifecycle": lifecycle_valid,
                    "rng": (
                        state.seed_map
                        == authoritative_seed_map(profile, replicate)
                        and set(state.rngs) == set(RNG_NAMES)
                    ),
                    "checkpoint": (
                        checkpoint_state.completed_update == 250
                        and checkpoint_state.next_episode_id == 4000
                    ),
                    "finite": finite,
                }
                if not all(operational.values()):
                    raise RuntimeError(
                        f"formal evaluation operational failure "
                        f"{replicate}:{arm_name}:{cell}:{operational}"
                    )
                payload = {
                    "schema_version": EVALUATION_CELL_SCHEMA,
                    "contract": registered_contract(),
                    "arm": arm_name,
                    "replicate": replicate,
                    "cell": cell,
                    "profile": profile,
                    "mode": "deterministic" if deterministic else "stochastic",
                    "checkpoint": str(checkpoint),
                    "checkpoint_origin": "update_250.pt",
                    "counts": {
                        "episodes": len(episode_rows),
                        "horizon": HORIZON,
                    },
                    "seed_map": authoritative_seed_map(profile, replicate),
                    "replay": replay_record,
                    "operational": operational,
                    "episodes": episode_rows,
                }
                path = (
                    output_root / "evaluation" / f"replicate_{replicate}"
                    / arm_name / f"{cell}.json"
                )
                _write_json(path, payload)
                manifest["artifacts"][f"{replicate}:{arm_name}:{cell}"] = str(path)
    _write_json(output_root / "evaluation_manifest.json", manifest)
    return manifest

def _percentile(values: list[float]) -> tuple[float, float]:
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def aggregate_analysis(
    output_root: Path, *, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal analysis requires the exact authorization token")
    training_manifest = json.loads(
        (output_root / "train_manifest.json").read_text(encoding="utf-8")
    )
    evaluation_payloads: dict[tuple[int, str, str], dict[str, Any]] = {}
    for replicate in range(5):
        for arm in ARMS:
            for _profile, _deterministic, cell in EVALUATION_CELLS:
                path = (
                    output_root / "evaluation" / f"replicate_{replicate}"
                    / arm / f"{cell}.json"
                )
                if path.is_file():
                    evaluation_payloads[(replicate, arm, cell)] = json.loads(
                        path.read_text(encoding="utf-8")
                    )
    operational_valid, operational_errors = validate_operational_records(
        training_manifest, evaluation_payloads
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
            **ABSENT_NATURAL_FORK_EVIDENCE,
        }
        result = {
            "branch": select_result_branch(**inputs),
            "predicate_inputs": inputs,
            "operational_errors": operational_errors,
            "registered_contract": REGISTERED_CONTRACT,
        }
        _write_json(output_root / "analysis_result.json", result)
        return result

    data = {
        (replicate, arm): evaluation_payloads[
            (replicate, arm, "held_out_stochastic")
        ]["episodes"]
        for replicate in range(5)
        for arm in ARMS
    }
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
    for _ in range(BOOTSTRAP_REPETITIONS):
        sampled_replicates = rng.integers(0, 5, size=5)
        sampled: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
        for replicate in sampled_replicates:
            episode_indices = rng.integers(
                0, FORMAL_EVAL_EPISODES, size=FORMAL_EVAL_EPISODES
            )
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
        **ABSENT_NATURAL_FORK_EVIDENCE,
    }
    result = {
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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("contract", "smoke", "train", "evaluate", "analyze"), default="contract"); parser.add_argument("--output-root", type=Path, default=Path("logs/event_held_commitment_link_g0")); parser.add_argument("--device", choices=REGISTERED_EXECUTION_BACKENDS, default=FORMAL_EXECUTION_BACKEND); parser.add_argument("--authorize-formal", default=""); return parser.parse_args()


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
    else: result = aggregate_analysis(args.output_root, authorization=args.authorize_formal)
    print(json.dumps(_json_ready(result), ensure_ascii=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
