"""Scientific-parameter-free infrastructure for FRRIE B/EXPLORE studies.

This module deliberately has no training or evaluation entry point.  It accepts
an externally frozen study specification, validates complete paired learning
curve observations, records result-blind resource high-water marks, and
publishes either one complete curve or one quarantined incomplete artifact.

The conclusion-bearing FRRIE V2 contracts are intentionally not imported.
They remain a separate, frozen C-only evidence object.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Final, Mapping, Sequence


B_SPEC_SCHEMA: Final[str] = "FRRIE_B_EXPLORE_SPEC_V1"
B_CURVE_SCHEMA: Final[str] = "FRRIE_B_PAIRED_CURVE_V1"
B_NAMESPACE_SCHEMA: Final[str] = "FRRIE_B_RESULT_NAMESPACE_V1"
B_QUARANTINE_SCHEMA: Final[str] = "FRRIE_B_INCOMPLETE_QUARANTINE_V1"
B_TELEMETRY_SCHEMA: Final[str] = "FRRIE_B_PROCESS_TREE_TELEMETRY_V1"

_C_ONLY_SCHEMA_PREFIXES: Final[tuple[str, ...]] = (
    "FRRIE_MANIFEST_",
    "FRRIE_CHECKPOINT_",
    "FRRIE_SEALED_SEED_PACKET_",
    "FRRIE_COMPLETE_PANEL_",
    "FRRIE_TERMINAL_",
)
_PERFORMANCE_DISPOSITIONS: Final[frozenset[str]] = frozenset(
    {"PERFORMANCE_READY", "PILOT_ONLY", "REPAIR_REQUIRED", "NOT_APPLICABLE"}
)
_BUDGET_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "wall_seconds",
        "peak_rss_bytes",
        "scratch_peak_bytes",
        "durable_peak_bytes",
        "read_bytes",
        "write_bytes",
        "transitions",
        "optimizer_updates",
        "evaluations",
    }
)
_TELEMETRY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "wall_seconds",
        "cpu_seconds",
        "cpu_occupancy_fraction",
        "peak_rss_bytes",
        "scratch_peak_bytes",
        "durable_peak_bytes",
        "read_bytes",
        "write_bytes",
        "worker_peak",
        "sample_count",
    }
)


class ExploreContractError(ValueError):
    """The B study structure or observation is incomplete or contradictory."""


class ResourceObservationUnavailable(RuntimeError):
    """Required process-tree or filesystem telemetry could not be observed."""


class ExplorePublicationError(RuntimeError):
    """A create-once result namespace or artifact could not be published."""


def _exact_fields(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ExploreContractError(f"{name} fields must be exactly {sorted(expected)}")


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ExploreContractError(f"{name} must be a nonempty trimmed string")
    if any(ord(character) < 33 or ord(character) > 126 for character in value):
        raise ExploreContractError(f"{name} must use printable ASCII without spaces")
    return value


def _positive_int(value: Any, name: str, *, allow_zero: bool = False) -> int:
    lower = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < lower:
        qualifier = "nonnegative" if allow_zero else "positive"
        raise ExploreContractError(f"{name} must be a {qualifier} integer")
    return value


def _finite_number(value: Any, name: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExploreContractError(f"{name} must be numeric")
    number = float(value)
    if not math.isfinite(number) or (nonnegative and number < 0.0):
        raise ExploreContractError(f"{name} must be finite" + (" and nonnegative" if nonnegative else ""))
    return number


def _ordered_unique(values: Any, name: str, *, minimum: int = 1) -> tuple[str, ...]:
    if not isinstance(values, list) or len(values) < minimum:
        raise ExploreContractError(f"{name} must be a list with at least {minimum} entries")
    result = tuple(_identifier(value, f"{name} entry") for value in values)
    if len(set(result)) != len(result):
        raise ExploreContractError(f"{name} entries must be unique")
    return result


@dataclass(frozen=True, slots=True)
class ExploreCell:
    cell_id: str
    roster: int
    split: str
    intervention: str


@dataclass(frozen=True, slots=True)
class ExploreSpec:
    study_id: str
    claim_ceiling: str
    arms: tuple[str, ...]
    competence_arm: str
    seeds: tuple[str, ...]
    checkpoints: tuple[int, ...]
    cells: tuple[ExploreCell, ...]
    counter_semantics: str
    adaptation_record: Mapping[str, Any]
    stopping_rule: Mapping[str, Any]
    interpretation_rule: Mapping[str, Any]
    resource_admission_rule: Mapping[str, Any]
    competence_rule: Mapping[str, Any]
    reassociation_rule: Mapping[str, Any]
    raw_value_rule: Mapping[str, Any]
    budget: Mapping[str, int | float]
    performance_disposition: str
    performance_reason: str
    run_root: Path

    def expected_coordinates(self) -> tuple[tuple[str, str, int, str], ...]:
        return tuple(
            (arm, seed, checkpoint, cell.cell_id)
            for arm in self.arms
            for seed in self.seeds
            for checkpoint in self.checkpoints
            for cell in self.cells
        )


def validate_explore_spec(value: Mapping[str, Any]) -> ExploreSpec:
    """Validate an externally frozen B spec without supplying scientific defaults."""

    expected = {
        "schema",
        "study_id",
        "evidence_class",
        "claim_ceiling",
        "arms",
        "competence_arm",
        "seeds",
        "checkpoints",
        "cells",
        "counter_semantics",
        "adaptation_record",
        "stopping_rule",
        "interpretation_rule",
        "resource_admission_rule",
        "competence_rule",
        "reassociation_rule",
        "raw_value_rule",
        "budget",
        "performance_disposition",
        "performance_reason",
        "run_root",
    }
    _exact_fields(value, expected, "B spec")
    schema = value["schema"]
    if schema != B_SPEC_SCHEMA or any(
        isinstance(schema, str) and schema.startswith(prefix)
        for prefix in _C_ONLY_SCHEMA_PREFIXES
    ):
        raise ExploreContractError("B spec must use its independent B schema, never a C-only schema")
    if value["evidence_class"] != "B_EXPLORE":
        raise ExploreContractError("evidence_class must be B_EXPLORE")

    arms = _ordered_unique(value["arms"], "arms", minimum=2)
    competence_arm = _identifier(value["competence_arm"], "competence_arm")
    if competence_arm not in arms:
        raise ExploreContractError("competence_arm must name one frozen arm")
    seeds = _ordered_unique(value["seeds"], "seeds")

    checkpoints0 = value["checkpoints"]
    if not isinstance(checkpoints0, list) or not checkpoints0:
        raise ExploreContractError("checkpoints must be a nonempty externally frozen list")
    checkpoints = tuple(
        _positive_int(checkpoint, "checkpoint", allow_zero=True)
        for checkpoint in checkpoints0
    )
    if tuple(sorted(set(checkpoints))) != checkpoints:
        raise ExploreContractError("checkpoints must be strictly increasing and unique")

    cells0 = value["cells"]
    if not isinstance(cells0, list) or not cells0:
        raise ExploreContractError("cells must be a nonempty externally frozen list")
    cells: list[ExploreCell] = []
    for index, cell0 in enumerate(cells0):
        _exact_fields(cell0, {"cell_id", "roster", "split", "intervention"}, f"cells[{index}]")
        cells.append(
            ExploreCell(
                cell_id=_identifier(cell0["cell_id"], f"cells[{index}].cell_id"),
                roster=_positive_int(cell0["roster"], f"cells[{index}].roster"),
                split=_identifier(cell0["split"], f"cells[{index}].split"),
                intervention=_identifier(
                    cell0["intervention"], f"cells[{index}].intervention"
                ),
            )
        )
    if len({cell.cell_id for cell in cells}) != len(cells):
        raise ExploreContractError("cell_id values must be unique")

    for rule_name in (
        "adaptation_record",
        "stopping_rule",
        "interpretation_rule",
        "competence_rule",
        "reassociation_rule",
        "raw_value_rule",
    ):
        rule = value[rule_name]
        if not isinstance(rule, Mapping) or not rule:
            raise ExploreContractError(f"{rule_name} must be an explicit nonempty mapping")

    admission = value["resource_admission_rule"]
    _exact_fields(
        admission,
        {
            "receipt_schema",
            "minimum_physical_available_bytes",
            "minimum_effective_available_bytes",
            "fresh_per_invocation",
        },
        "resource_admission_rule",
    )
    _identifier(admission["receipt_schema"], "resource_admission_rule.receipt_schema")
    _positive_int(
        admission["minimum_physical_available_bytes"],
        "resource_admission_rule.minimum_physical_available_bytes",
    )
    _positive_int(
        admission["minimum_effective_available_bytes"],
        "resource_admission_rule.minimum_effective_available_bytes",
    )
    if admission["fresh_per_invocation"] is not True:
        raise ExploreContractError("resource admission must require a fresh receipt per invocation")

    budget0 = value["budget"]
    _exact_fields(budget0, set(_BUDGET_FIELDS), "budget")
    budget: dict[str, int | float] = {
        "wall_seconds": _finite_number(
            budget0["wall_seconds"], "budget.wall_seconds", nonnegative=True
        )
    }
    for field in _BUDGET_FIELDS - {"wall_seconds"}:
        budget[field] = _positive_int(
            budget0[field], f"budget.{field}", allow_zero=True
        )

    disposition = value["performance_disposition"]
    if disposition not in _PERFORMANCE_DISPOSITIONS:
        raise ExploreContractError("performance_disposition is missing or invalid")
    performance_reason = value["performance_reason"]
    if not isinstance(performance_reason, str) or not performance_reason.strip():
        raise ExploreContractError("performance_reason must state evidence for the disposition")

    run_root0 = value["run_root"]
    if not isinstance(run_root0, str) or not run_root0:
        raise ExploreContractError("run_root must be an externally supplied path string")
    run_root = Path(run_root0)
    if not run_root.is_absolute():
        raise ExploreContractError("run_root must be absolute")
    claim_ceiling = value["claim_ceiling"]
    if not isinstance(claim_ceiling, str) or not claim_ceiling.strip():
        raise ExploreContractError("claim_ceiling must be explicit")

    return ExploreSpec(
        study_id=_identifier(value["study_id"], "study_id"),
        claim_ceiling=claim_ceiling.strip(),
        arms=arms,
        competence_arm=competence_arm,
        seeds=seeds,
        checkpoints=checkpoints,
        cells=tuple(cells),
        counter_semantics=_identifier(value["counter_semantics"], "counter_semantics"),
        adaptation_record=dict(value["adaptation_record"]),
        stopping_rule=dict(value["stopping_rule"]),
        interpretation_rule=dict(value["interpretation_rule"]),
        resource_admission_rule=dict(admission),
        competence_rule=dict(value["competence_rule"]),
        reassociation_rule=dict(value["reassociation_rule"]),
        raw_value_rule=dict(value["raw_value_rule"]),
        budget=budget,
        performance_disposition=disposition,
        performance_reason=performance_reason.strip(),
        run_root=run_root.resolve(strict=False),
    )


def _validate_telemetry(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    _exact_fields(value, set(_TELEMETRY_FIELDS), name)
    result: dict[str, Any] = {}
    for field in (
        "wall_seconds",
        "cpu_seconds",
        "cpu_occupancy_fraction",
        "peak_rss_bytes",
        "scratch_peak_bytes",
        "durable_peak_bytes",
        "read_bytes",
        "write_bytes",
    ):
        result[field] = _finite_number(value[field], f"{name}.{field}", nonnegative=True)
    if result["cpu_occupancy_fraction"] > 1.0:
        raise ExploreContractError(f"{name}.cpu_occupancy_fraction must be in [0,1]")
    result["worker_peak"] = _positive_int(value["worker_peak"], f"{name}.worker_peak")
    result["sample_count"] = _positive_int(value["sample_count"], f"{name}.sample_count")
    return result


def _validate_curve_row(value: Mapping[str, Any], spec: ExploreSpec, index: int) -> dict[str, Any]:
    expected = {
        "arm_id",
        "seed_id",
        "checkpoint",
        "cell_id",
        "transitions",
        "optimizer_updates",
        "evaluations",
        "native_return",
        "projection_contact",
        "edge_competence",
        "reassociation",
        "raw_value_control",
        "work_exposure",
        "telemetry",
        "validity",
    }
    _exact_fields(value, expected, f"rows[{index}]")
    row = dict(value)
    coordinate = (
        _identifier(row["arm_id"], f"rows[{index}].arm_id"),
        _identifier(row["seed_id"], f"rows[{index}].seed_id"),
        _positive_int(row["checkpoint"], f"rows[{index}].checkpoint", allow_zero=True),
        _identifier(row["cell_id"], f"rows[{index}].cell_id"),
    )
    if coordinate not in spec.expected_coordinates():
        raise ExploreContractError(f"rows[{index}] coordinate is outside the frozen B spec")
    row["transitions"] = _positive_int(
        row["transitions"], f"rows[{index}].transitions", allow_zero=True
    )
    row["optimizer_updates"] = _positive_int(
        row["optimizer_updates"], f"rows[{index}].optimizer_updates", allow_zero=True
    )
    row["evaluations"] = _positive_int(row["evaluations"], f"rows[{index}].evaluations")
    row["native_return"] = _finite_number(row["native_return"], f"rows[{index}].native_return")

    contact = row["projection_contact"]
    _exact_fields(contact, {"observed", "count", "opportunities"}, f"rows[{index}].projection_contact")
    if contact["observed"] is not True:
        raise ExploreContractError("projection contact must be directly observed for every curve row")
    count = _positive_int(contact["count"], "projection contact count", allow_zero=True)
    opportunities = _positive_int(
        contact["opportunities"], "projection contact opportunities", allow_zero=True
    )
    if count > opportunities:
        raise ExploreContractError("projection contact count exceeds opportunities")

    competence = row["edge_competence"]
    _exact_fields(competence, {"observed", "value", "passed"}, f"rows[{index}].edge_competence")
    if competence["observed"] is not True or not isinstance(competence["passed"], bool):
        raise ExploreContractError("EDGE competence observation and pass/fail must be explicit")
    _finite_number(competence["value"], f"rows[{index}].edge_competence.value")

    reassociation = row["reassociation"]
    _exact_fields(reassociation, {"observed", "native_return"}, f"rows[{index}].reassociation")
    if reassociation["observed"] is not True:
        raise ExploreContractError("reassociation return must be directly observed for every curve row")
    _finite_number(reassociation["native_return"], f"rows[{index}].reassociation.native_return")

    raw_value = row["raw_value_control"]
    _exact_fields(raw_value, {"observed", "value", "passed"}, f"rows[{index}].raw_value_control")
    if raw_value["observed"] is not True or not isinstance(raw_value["passed"], bool):
        raise ExploreContractError("raw-value control observation and pass/fail must be explicit")
    _finite_number(raw_value["value"], f"rows[{index}].raw_value_control.value")

    exposure = row["work_exposure"]
    _exact_fields(
        exposure,
        {
            "information_items",
            "parameter_count",
            "parameter_bytes",
            "optimizer_updates",
            "environment_interactions",
            "evaluations",
            "tuning_opportunities",
            "static_flops",
            "workers",
            "threads",
        },
        f"rows[{index}].work_exposure",
    )
    for field in (
        "information_items",
        "parameter_count",
        "parameter_bytes",
        "optimizer_updates",
        "environment_interactions",
        "evaluations",
        "tuning_opportunities",
    ):
        exposure[field] = _positive_int(
            exposure[field], f"rows[{index}].work_exposure.{field}", allow_zero=True
        )
    exposure["workers"] = _positive_int(
        exposure["workers"], f"rows[{index}].work_exposure.workers"
    )
    exposure["threads"] = _positive_int(
        exposure["threads"], f"rows[{index}].work_exposure.threads"
    )
    static_flops = exposure["static_flops"]
    _exact_fields(static_flops, {"observed", "value"}, f"rows[{index}].work_exposure.static_flops")
    if not isinstance(static_flops["observed"], bool):
        raise ExploreContractError("static FLOP availability must be explicit")
    if static_flops["observed"]:
        static_flops["value"] = _positive_int(
            static_flops["value"], f"rows[{index}].work_exposure.static_flops.value", allow_zero=True
        )
    elif static_flops["value"] is not None:
        raise ExploreContractError("unobserved static FLOPs must use a null value")
    if exposure["optimizer_updates"] != row["optimizer_updates"]:
        raise ExploreContractError("work exposure optimizer updates differ from the curve counter")
    if exposure["environment_interactions"] != row["transitions"]:
        raise ExploreContractError("work exposure environment interactions differ from transitions")
    if exposure["evaluations"] != row["evaluations"]:
        raise ExploreContractError("work exposure evaluations differ from the curve counter")
    row["telemetry"] = _validate_telemetry(row["telemetry"], f"rows[{index}].telemetry")

    validity = row["validity"]
    _exact_fields(validity, {"valid", "issues"}, f"rows[{index}].validity")
    if not isinstance(validity["valid"], bool) or not isinstance(validity["issues"], list):
        raise ExploreContractError("row validity must contain a bool and an issue list")
    if any(not isinstance(issue, str) or not issue for issue in validity["issues"]):
        raise ExploreContractError("row validity issues must be nonempty strings")
    if validity["valid"] != (not validity["issues"]):
        raise ExploreContractError("row validity bool must agree with its issue list")
    return row


def validate_paired_curve(value: Mapping[str, Any], spec: ExploreSpec) -> dict[str, Any]:
    """Require one ordered observation for every frozen arm/seed/checkpoint/cell."""

    expected = {
        "schema",
        "complete",
        "study_id",
        "claim_ceiling",
        "rows",
        "stage_telemetry",
        "end_to_end_telemetry",
        "invocation_inventory",
        "invocation_receipts",
        "validity",
        "observations",
    }
    _exact_fields(value, expected, "paired curve")
    if value["schema"] != B_CURVE_SCHEMA or value["complete"] is not True:
        raise ExploreContractError("paired curve schema/completeness is invalid")
    if value["study_id"] != spec.study_id or value["claim_ceiling"] != spec.claim_ceiling:
        raise ExploreContractError("paired curve study identity or claim ceiling differs")
    rows0 = value["rows"]
    if not isinstance(rows0, list):
        raise ExploreContractError("paired curve rows must be a list")
    rows = [_validate_curve_row(row, spec, index) for index, row in enumerate(rows0)]
    actual = tuple(
        (row["arm_id"], row["seed_id"], row["checkpoint"], row["cell_id"])
        for row in rows
    )
    if actual != spec.expected_coordinates():
        raise ExploreContractError("paired curve rows are partial, duplicated, extra, or out of frozen order")

    by_pair: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_pair.setdefault((row["seed_id"], row["checkpoint"], row["cell_id"]), []).append(row)
    for coordinate, pair in by_pair.items():
        work = {
            (
                row["transitions"],
                row["optimizer_updates"],
                row["evaluations"],
                canonical_json_bytes(row["work_exposure"]),
            )
            for row in pair
        }
        if len(work) != 1:
            raise ExploreContractError(f"paired work differs across arms at {coordinate}")

    stages0 = value["stage_telemetry"]
    if not isinstance(stages0, list) or not stages0:
        raise ExploreContractError("at least one explicit stage telemetry row is required")
    stages: list[dict[str, Any]] = []
    stage_ids: set[str] = set()
    for index, stage0 in enumerate(stages0):
        _exact_fields(stage0, {"stage_id", "telemetry"}, f"stage_telemetry[{index}]")
        stage_id = _identifier(stage0["stage_id"], f"stage_telemetry[{index}].stage_id")
        if stage_id in stage_ids:
            raise ExploreContractError("stage telemetry IDs must be unique")
        stage_ids.add(stage_id)
        stages.append({"stage_id": stage_id, "telemetry": _validate_telemetry(stage0["telemetry"], stage_id)})
    end_to_end = _validate_telemetry(value["end_to_end_telemetry"], "end_to_end_telemetry")

    inventory0 = value["invocation_inventory"]
    receipts0 = value["invocation_receipts"]
    if not isinstance(inventory0, list) or not inventory0:
        raise ExploreContractError("invocation_inventory must list every result-bearing invocation")
    if not isinstance(receipts0, list):
        raise ExploreContractError("invocation_receipts must be a list")
    inventory: list[dict[str, str]] = []
    inventory_ids: list[str] = []
    for index, invocation0 in enumerate(inventory0):
        _exact_fields(
            invocation0,
            {"invocation_id", "seed_id", "phase"},
            f"invocation_inventory[{index}]",
        )
        invocation_id = _identifier(
            invocation0["invocation_id"], f"invocation_inventory[{index}].invocation_id"
        )
        seed_id = _identifier(
            invocation0["seed_id"], f"invocation_inventory[{index}].seed_id"
        )
        if seed_id not in spec.seeds:
            raise ExploreContractError("invocation seed is outside the frozen B spec")
        inventory_ids.append(invocation_id)
        inventory.append(
            {
                "invocation_id": invocation_id,
                "seed_id": seed_id,
                "phase": _identifier(
                    invocation0["phase"], f"invocation_inventory[{index}].phase"
                ),
            }
        )
    if len(set(inventory_ids)) != len(inventory_ids):
        raise ExploreContractError("invocation IDs must be unique")

    receipt_ids: list[str] = []
    receipt_paths: list[Path] = []
    receipts: list[dict[str, Any]] = []
    admission = spec.resource_admission_rule
    for index, receipt0 in enumerate(receipts0):
        _exact_fields(
            receipt0,
            {
                "invocation_id",
                "receipt_path",
                "receipt_schema",
                "physical_available_bytes",
                "effective_available_bytes",
                "fresh",
                "passed",
            },
            f"invocation_receipts[{index}]",
        )
        invocation_id = _identifier(
            receipt0["invocation_id"], f"invocation_receipts[{index}].invocation_id"
        )
        path0 = receipt0["receipt_path"]
        if not isinstance(path0, str) or not path0 or not Path(path0).is_absolute():
            raise ExploreContractError("invocation receipt path must be explicit and absolute")
        path = Path(path0).resolve(strict=False)
        physical = _positive_int(
            receipt0["physical_available_bytes"],
            f"invocation_receipts[{index}].physical_available_bytes",
            allow_zero=True,
        )
        effective = _positive_int(
            receipt0["effective_available_bytes"],
            f"invocation_receipts[{index}].effective_available_bytes",
            allow_zero=True,
        )
        if receipt0["receipt_schema"] != admission["receipt_schema"]:
            raise ExploreContractError("invocation receipt schema differs from the admission rule")
        expected_pass = (
            physical >= admission["minimum_physical_available_bytes"]
            and effective >= admission["minimum_effective_available_bytes"]
        )
        if receipt0["fresh"] is not True or receipt0["passed"] is not True or not expected_pass:
            raise ExploreContractError("every result-bearing invocation requires a fresh passing memory receipt")
        receipt_ids.append(invocation_id)
        receipt_paths.append(path)
        receipts.append(dict(receipt0, receipt_path=str(path)))
    if receipt_ids != inventory_ids:
        raise ExploreContractError("invocation receipts do not exactly cover the ordered invocation inventory")
    if len(set(receipt_paths)) != len(receipt_paths):
        raise ExploreContractError("each invocation must bind a unique fresh receipt path")

    validity = value["validity"]
    _exact_fields(validity, {"valid", "issues"}, "paired curve validity")
    issues = validity["issues"]
    if not isinstance(validity["valid"], bool) or not isinstance(issues, list):
        raise ExploreContractError("paired curve validity must be explicit")
    if any(not isinstance(issue, str) or not issue for issue in issues):
        raise ExploreContractError("paired curve validity issues must be nonempty strings")
    row_issues = [issue for row in rows for issue in row["validity"]["issues"]]
    if validity["valid"] is True and (issues or row_issues):
        raise ExploreContractError("valid paired curve cannot contain declared issues")
    if validity["valid"] is False and not issues and not row_issues:
        raise ExploreContractError("invalid paired curve must name at least one issue")
    if not isinstance(value["observations"], Mapping):
        raise ExploreContractError("observations must be a direct mapping separate from validity")

    result = dict(value)
    result["rows"] = rows
    result["stage_telemetry"] = stages
    result["end_to_end_telemetry"] = end_to_end
    result["invocation_inventory"] = inventory
    result["invocation_receipts"] = receipts
    return result


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        ).encode("ascii") + b"\n"
    except (TypeError, ValueError) as exc:
        raise ExploreContractError("artifact is not canonical finite JSON") from exc


@dataclass(frozen=True, slots=True)
class ExploreNamespace:
    root: Path
    result: Path
    quarantine: Path


def claim_explore_namespace(spec: ExploreSpec) -> ExploreNamespace:
    """Atomically claim one absent B run root with result/quarantine lanes."""

    root = spec.run_root
    staging = root.with_name(root.name + ".FRRIE_B_CLAIM.tmp")
    if root.exists() or staging.exists():
        raise ExplorePublicationError("B run root or stale staging root already exists")
    if not root.parent.exists():
        raise ExplorePublicationError("B run root parent must already exist")
    try:
        staging.mkdir()
        result = staging / "result"
        quarantine = staging / "quarantine"
        result.mkdir()
        quarantine.mkdir()
        marker = {
            "schema": B_NAMESPACE_SCHEMA,
            "study_id": spec.study_id,
            "claim_ceiling": spec.claim_ceiling,
        }
        (staging / "namespace.json").write_bytes(canonical_json_bytes(marker))
        staging.replace(root)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return ExploreNamespace(root=root, result=root / "result", quarantine=root / "quarantine")


def _write_create_once(path: Path, payload: Mapping[str, Any]) -> Path:
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise ExplorePublicationError("artifact target or temporary already exists")
    data = canonical_json_bytes(payload)
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return path


def finalize_paired_curve(
    namespace: ExploreNamespace,
    artifact: Mapping[str, Any],
    spec: ExploreSpec,
) -> Path:
    """Publish a complete curve once, or quarantine the unmodified candidate once."""

    if spec.performance_disposition == "REPAIR_REQUIRED":
        quarantine = {
            "schema": B_QUARANTINE_SCHEMA,
            "complete": False,
            "study_id": spec.study_id,
            "reason": "performance disposition REPAIR_REQUIRED withholds result publication",
            "candidate": artifact,
        }
        _write_create_once(namespace.quarantine / "incomplete_curve.json", quarantine)
        raise ExploreContractError(
            "REPAIR_REQUIRED B path cannot publish a result; candidate was quarantined"
        )
    try:
        validated = validate_paired_curve(artifact, spec)
    except ExploreContractError as exc:
        quarantine = {
            "schema": B_QUARANTINE_SCHEMA,
            "complete": False,
            "study_id": spec.study_id,
            "reason": str(exc),
            "candidate": artifact,
        }
        _write_create_once(namespace.quarantine / "incomplete_curve.json", quarantine)
        raise
    if validated["validity"]["valid"] is not True:
        quarantine = {
            "schema": B_QUARANTINE_SCHEMA,
            "complete": False,
            "study_id": spec.study_id,
            "reason": "artifact declares invalid observation",
            "candidate": validated,
        }
        _write_create_once(namespace.quarantine / "incomplete_curve.json", quarantine)
        raise ExploreContractError("invalid observation was quarantined and not published as a result")
    return _write_create_once(namespace.result / "paired_curve.json", validated)


def recursive_byte_census(root: Path) -> int:
    """Return a direct file-size census; missing roots measure as zero bytes."""

    if not root.exists():
        return 0
    if not root.is_dir():
        raise ResourceObservationUnavailable(f"resource root is not a directory: {root}")
    total = 0
    try:
        for directory, _, files in os.walk(root):
            for name in files:
                total += (Path(directory) / name).stat().st_size
    except OSError as exc:
        raise ResourceObservationUnavailable(f"cannot census resource root: {root}") from exc
    return total


@dataclass(frozen=True, slots=True)
class ProcessTreeSample:
    monotonic_seconds: float
    rss_bytes: int
    cpu_seconds: float
    read_bytes: int
    write_bytes: int
    worker_count: int
    scratch_bytes: int
    durable_bytes: int


def sample_process_tree(scratch_root: Path, durable_root: Path) -> ProcessTreeSample:
    """Measure the current process tree using psutil, refusing partial fallback."""

    try:
        import psutil  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ResourceObservationUnavailable("psutil is required for process-tree telemetry") from exc
    try:
        root = psutil.Process(os.getpid())
        processes = [root, *root.children(recursive=True)]
        rss = 0
        cpu = 0.0
        read_bytes = 0
        write_bytes = 0
        observed = 0
        for process in processes:
            try:
                rss += int(process.memory_info().rss)
                times = process.cpu_times()
                cpu += float(times.user + times.system)
                io = process.io_counters()
                read_bytes += int(io.read_bytes)
                write_bytes += int(io.write_bytes)
                observed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if observed == 0:
            raise ResourceObservationUnavailable("no process-tree member could be observed")
    except ResourceObservationUnavailable:
        raise
    except Exception as exc:
        raise ResourceObservationUnavailable("process-tree telemetry failed") from exc
    return ProcessTreeSample(
        monotonic_seconds=time.monotonic(),
        rss_bytes=rss,
        cpu_seconds=cpu,
        read_bytes=read_bytes,
        write_bytes=write_bytes,
        worker_count=observed,
        scratch_bytes=recursive_byte_census(scratch_root),
        durable_bytes=recursive_byte_census(durable_root),
    )


class ProcessTreePeakMonitor:
    """Background peak sampler with explicit stage and end-to-end reports."""

    def __init__(
        self,
        *,
        scratch_root: Path,
        durable_root: Path,
        interval_seconds: float,
        sampler: Callable[[Path, Path], ProcessTreeSample] = sample_process_tree,
    ) -> None:
        if not math.isfinite(interval_seconds) or interval_seconds <= 0.0:
            raise ValueError("interval_seconds must be finite and positive")
        self._scratch_root = scratch_root
        self._durable_root = durable_root
        self._interval_seconds = interval_seconds
        self._sampler = sampler
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._stage = "UNASSIGNED"
        self._samples: list[tuple[str, ProcessTreeSample]] = []
        self._failure: BaseException | None = None

    def set_stage(self, stage_id: str) -> None:
        stage = _identifier(stage_id, "stage_id")
        running = self._thread is not None and self._thread.is_alive()
        if running:
            self._capture()
        with self._lock:
            self._stage = stage
        if running:
            self._capture()

    def _capture(self) -> None:
        sample = self._sampler(self._scratch_root, self._durable_root)
        with self._lock:
            self._samples.append((self._stage, sample))

    def _run(self) -> None:
        try:
            self._capture()
            while not self._stop.wait(self._interval_seconds):
                self._capture()
        except BaseException as exc:
            self._failure = exc
            self._stop.set()

    def start(self) -> "ProcessTreePeakMonitor":
        if self._thread is not None:
            raise RuntimeError("resource monitor can start only once")
        self._thread = threading.Thread(target=self._run, name="frrie-b-resource-monitor", daemon=True)
        self._thread.start()
        return self

    def stop(self) -> dict[str, Any]:
        if self._thread is None:
            raise RuntimeError("resource monitor was not started")
        self._stop.set()
        self._thread.join(timeout=max(1.0, self._interval_seconds * 4.0))
        if self._thread.is_alive():
            raise ResourceObservationUnavailable("resource monitor did not stop")
        if self._failure is not None:
            raise ResourceObservationUnavailable("resource monitor sampling failed") from self._failure
        # Capture a terminal sample synchronously so short stages are not represented
        # only by their initial state.
        self._capture()
        with self._lock:
            samples = list(self._samples)
        if len(samples) < 2:
            raise ResourceObservationUnavailable("resource monitor requires start and terminal samples")
        return self._report(samples)

    @staticmethod
    def _telemetry(samples: Sequence[ProcessTreeSample]) -> dict[str, Any]:
        start, end = samples[0], samples[-1]
        wall = max(0.0, end.monotonic_seconds - start.monotonic_seconds)
        cpu = max(0.0, end.cpu_seconds - start.cpu_seconds)
        worker_peak = max(sample.worker_count for sample in samples)
        occupancy = 0.0 if wall == 0.0 else min(1.0, cpu / (wall * worker_peak))
        return {
            "wall_seconds": wall,
            "cpu_seconds": cpu,
            "cpu_occupancy_fraction": occupancy,
            "peak_rss_bytes": max(sample.rss_bytes for sample in samples),
            "scratch_peak_bytes": max(sample.scratch_bytes for sample in samples),
            "durable_peak_bytes": max(sample.durable_bytes for sample in samples),
            "read_bytes": max(0, end.read_bytes - start.read_bytes),
            "write_bytes": max(0, end.write_bytes - start.write_bytes),
            "worker_peak": worker_peak,
            "sample_count": len(samples),
        }

    def _report(self, labelled: Sequence[tuple[str, ProcessTreeSample]]) -> dict[str, Any]:
        stage_order: list[str] = []
        grouped: dict[str, list[ProcessTreeSample]] = {}
        for stage, sample in labelled:
            if stage not in grouped:
                stage_order.append(stage)
                grouped[stage] = []
            grouped[stage].append(sample)
        return {
            "schema": B_TELEMETRY_SCHEMA,
            "stages": [
                {"stage_id": stage, "telemetry": self._telemetry(grouped[stage])}
                for stage in stage_order
            ],
            "end_to_end": self._telemetry([sample for _, sample in labelled]),
        }


__all__ = [
    "B_SPEC_SCHEMA",
    "B_CURVE_SCHEMA",
    "B_NAMESPACE_SCHEMA",
    "B_QUARANTINE_SCHEMA",
    "B_TELEMETRY_SCHEMA",
    "ExploreContractError",
    "ResourceObservationUnavailable",
    "ExplorePublicationError",
    "ExploreCell",
    "ExploreSpec",
    "ExploreNamespace",
    "ProcessTreeSample",
    "ProcessTreePeakMonitor",
    "validate_explore_spec",
    "validate_paired_curve",
    "claim_explore_namespace",
    "finalize_paired_curve",
    "recursive_byte_census",
    "sample_process_tree",
]
