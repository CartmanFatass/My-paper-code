"""Frozen, value-blind FRRIE manifest contract.

Validation here inspects identities and structure only.  It never opens a
seed packet, evaluates a return, or infers a threshold from an observed value.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

FRRIE_MANIFEST_V1 = "FRRIE_MANIFEST_V1"
FRRIE_CHECKPOINT_V1 = "FRRIE_CHECKPOINT_V1"
FRRIE_SEALED_SEED_PACKET_V1 = "FRRIE_SEALED_SEED_PACKET_V1"
FRRIE_COMPLETE_PANEL_RESULT_V1 = "FRRIE_COMPLETE_PANEL_RESULT_V1"
FRRIE_TERMINAL_V1 = "FRRIE_TERMINAL_V1"

EXPERIMENT_ID = "FRRIE-RIDGEGATE-2Z-RSCF-R01"
DIRECTION_ID = "finite_resource_relational_inductive_efficiency"
HOST_ID = "FRRIE-RIDGEGATE-2Z/RSCF"
SOURCE_ID = "FRRIE-RIDGEGATE-2Z-RSCF-FRESH-SOURCE-V1"
NATIVE_COMPONENT = "FRRIE_RIDGEGATE2Z_RSCF_FULL_HOST"
NATIVE_ABI = "FRRIE_RIDGEGATE2Z_RSCF_NATIVE_ABI_V1_FP32"
LEARNED_ARMS = ("PHY_TRUST", "EDGE_FLEX")
EVALUATION_ONLY_ARM = "UNIFORM_LEGAL"
TRAIN_ROSTERS = (9, 15)
HELDOUT_ROSTERS = (6, 21)
INTERVENTIONS = ("INTACT", "SEMANTIC_COLUMN_ROTATE")
MODEL_PARAMETER_COUNT = 35_513
UPDATES = 512
EPISODES_PER_UPDATE = 64
EVALUATIONS_PER_CELL = 256
MAX_SEED_BLOCKS = 24

THRESHOLD_FIELDS = (
    "heldout_direct_return_lower",
    "heldout_minus_seen_interaction_lower",
    "worst_basin_delivery_lower",
    "treatment_cut_loss_lower",
    "legal_action_tv_lower",
    "differential_cut_attenuation_lower",
)
PARITY_FIELDS = (
    "environment_slots", "learned_decisions", "backward_calls", "adam_steps",
    "parameter_bytes", "flops", "workers", "threads", "native_width",
    "dtype", "checkpoint_io", "evaluation_opportunities",
)
FIXTURE_CONTRACTS = {
    "ccic": {"schema": "FRRIE_CCIC_CONTROL_V1", "complete": True},
    "egrcr": {"schema": "FRRIE_EGRCR_CONTROL_V1", "complete": True},
    "raw_value": {"schema": "FRRIE_RAW_VALUE_CONTROL_V1", "complete": True},
    "vqfp": {
        "schema": "FRRIE_VQFP_CONTROLS_V1",
        "complete": True,
        "output_disconnected": True,
        "action_seam": "FRRIE_ACTION_SEAM_ABSENT",
    },
}
class ContractError(ValueError):
    """A frozen structural invariant is absent or false."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise ContractError(f"value is not canonical JSON: {exc}") from exc


def manifest_packet_contract(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Direct packet binding projection, excluding its circular locator."""
    projection = deepcopy(dict(manifest))
    projection.pop("sealed_seed_packet", None)
    return projection


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{field} must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], required: Sequence[str], field: str) -> None:
    missing = set(required) - set(value)
    if missing:
        raise ContractError(f"{field} missing fields: {sorted(missing)}")
    extra = set(value) - set(required)
    if extra:
        raise ContractError(f"{field} has undeclared fields: {sorted(extra)}")


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ContractError(f"{field} must be a positive integer")
    return value


def _fresh_literal(value: Any, expected: str, field: str) -> None:
    if value != expected:
        raise ContractError(f"{field} must equal {expected!r}")


def expected_cells() -> tuple[tuple[str, int, str], ...]:
    return tuple(
        [("TRAIN", n, "INTACT") for n in TRAIN_ROSTERS]
        + [("EVALUATE", n, cut) for n in (*TRAIN_ROSTERS, *HELDOUT_ROSTERS) for cut in INTERVENTIONS]
    )


def _validate_cells(rows: Any) -> None:
    if not isinstance(rows, list):
        raise ContractError("cells must be a list")
    observed: list[tuple[str, int, str]] = []
    for index, row0 in enumerate(rows):
        row = _mapping(row0, f"cells[{index}]")
        _exact_keys(row, ("purpose", "roster", "intervention", "episodes"), f"cells[{index}]")
        triple = (row["purpose"], row["roster"], row["intervention"])
        observed.append(triple)  # type: ignore[arg-type]
        expected_episodes = EPISODES_PER_UPDATE // 2 if row["purpose"] == "TRAIN" else EVALUATIONS_PER_CELL
        if row["episodes"] != expected_episodes:
            raise ContractError(f"cells[{index}].episodes must equal {expected_episodes}")
    if tuple(observed) != expected_cells():
        raise ContractError("cells must exactly equal the frozen ordered train/evaluation cells")


def _validate_arms(rows: Any) -> None:
    if not isinstance(rows, list) or len(rows) != 3:
        raise ContractError("arms must contain exactly three ordered records")
    expected = (
        ("PHY_TRUST", True, False, [-0.15, 0.15]),
        ("EDGE_FLEX", True, False, [-1.5, 1.5]),
        ("UNIFORM_LEGAL", False, True, None),
    )
    for index, (row0, wanted) in enumerate(zip(rows, expected)):
        row = _mapping(row0, f"arms[{index}]")
        _exact_keys(row, ("id", "learned", "evaluation_only", "beta_projection", "parameter_count"), f"arms[{index}]")
        got = (row.get("id"), row.get("learned"), row.get("evaluation_only"), row.get("beta_projection"))
        if got != wanted:
            raise ContractError(f"arms[{index}] violates the frozen learned/evaluation/projection contract")
        if row.get("parameter_count") != (MODEL_PARAMETER_COUNT if wanted[1] else 0):
            raise ContractError(f"arms[{index}].parameter_count is invalid")


def _validate_work(work0: Any, compute: Mapping[str, Any], checkpoints: list[int]) -> None:
    work = _mapping(work0, "work_parity")
    if set(work) != set(LEARNED_ARMS):
        raise ContractError("work_parity must bind exactly both learned arms")
    left = _mapping(work[LEARNED_ARMS[0]], "work_parity.PHY_TRUST")
    right = _mapping(work[LEARNED_ARMS[1]], "work_parity.EDGE_FLEX")
    _exact_keys(left, PARITY_FIELDS, "work_parity.PHY_TRUST")
    _exact_keys(right, PARITY_FIELDS, "work_parity.EDGE_FLEX")
    if dict(left) != dict(right):
        raise ContractError("learned-arm work vectors must match exactly")
    if left["backward_calls"] != UPDATES or left["adam_steps"] != UPDATES:
        raise ContractError("each learned arm requires one backward and Adam step per update")
    if left["parameter_bytes"] != MODEL_PARAMETER_COUNT * 4:
        raise ContractError("parameter byte count must bind 35,513 FP32 parameters")
    if left["workers"] != compute["workers"] or left["threads"] != compute["threads"]:
        raise ContractError("work worker/thread counts must bind compute")
    if left["native_width"] != compute["native_width"] or left["dtype"] != "float32":
        raise ContractError("work native width/dtype must bind compute")
    if left["checkpoint_io"] != len(checkpoints):
        raise ContractError("checkpoint I/O must equal prospective checkpoint opportunities")
    if left["evaluation_opportunities"] != len(checkpoints) * (len(TRAIN_ROSTERS) + len(HELDOUT_ROSTERS)) * len(INTERVENTIONS) * EVALUATIONS_PER_CELL:
        raise ContractError("evaluation opportunities are not exact")
    for field in ("environment_slots", "learned_decisions", "flops"):
        _positive_int(left[field], f"work_parity.{field}")


def validate_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a detached manifest without inspecting result values."""
    manifest = _mapping(value, "manifest")
    required = (
        "schema", "direction_id", "experiment_id", "host", "arms", "cells", "compute",
        "training", "evaluation", "seed_blocks", "sealed_seed_packet",
        "preflight_receipt", "thresholds", "generic_competence", "work_to_threshold",
        "roots", "fixture_contracts", "work_parity", "resource_ceiling",
    )
    _exact_keys(manifest, required, "manifest")
    if manifest["schema"] != FRRIE_MANIFEST_V1:
        raise ContractError(f"schema must equal {FRRIE_MANIFEST_V1}")
    if manifest["direction_id"] != DIRECTION_ID:
        raise ContractError("direction_id mismatch")
    _fresh_literal(manifest["experiment_id"], EXPERIMENT_ID, "experiment_id")

    host = _mapping(manifest["host"], "host")
    _exact_keys(host, (
        "id", "source_id", "component", "abi", "binding_kind",
        "native_required", "python_fallback",
    ), "host")
    _fresh_literal(host["id"], HOST_ID, "host.id")
    _fresh_literal(host["source_id"], SOURCE_ID, "host.source_id")
    if host["component"] != NATIVE_COMPONENT or host["abi"] != NATIVE_ABI:
        raise ContractError("host component/ABI differs from the fresh FRRIE native contract")
    if host["binding_kind"] != "FRRIE_NATIVE_CTYPES_V1":
        raise ContractError("host must use the direct FRRIE ctypes seam")
    if host["native_required"] is not True or host["python_fallback"] is not False:
        raise ContractError("production host must require native execution and forbid Python fallback")

    _validate_arms(manifest["arms"])
    _validate_cells(manifest["cells"])
    compute = _mapping(manifest["compute"], "compute")
    _exact_keys(compute, ("device", "gpu", "model_dtype", "reduction_dtype", "native_width", "workers", "threads", "network"), "compute")
    if (compute["device"], compute["gpu"], compute["model_dtype"], compute["reduction_dtype"], compute["network"]) != ("cpu", False, "float32", "float64", False):
        raise ContractError("compute must be CPU/FP32 with float64 reductions and no network")
    for field in ("native_width", "workers", "threads"):
        _positive_int(compute[field], f"compute.{field}")

    training = _mapping(manifest["training"], "training")
    _exact_keys(training, ("updates", "episodes_per_update", "rosters", "episodes_by_roster", "checkpoints"), "training")
    if training["updates"] != UPDATES or training["episodes_per_update"] != EPISODES_PER_UPDATE:
        raise ContractError("training must use exactly 512 updates and 64 episodes/update")
    if training["rosters"] != list(TRAIN_ROSTERS) or training["episodes_by_roster"] != {"9": 32, "15": 32}:
        raise ContractError("each update must split episodes equally over N=9 and N=15")
    checkpoints = training["checkpoints"]
    if not isinstance(checkpoints, list) or not checkpoints or checkpoints != sorted(set(checkpoints)):
        raise ContractError("prospective checkpoints must be a nonempty sorted unique list")
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 1 or x > UPDATES for x in checkpoints) or checkpoints[-1] != UPDATES:
        raise ContractError("checkpoint opportunities must lie in [1,512] and include update 512")

    evaluation = _mapping(manifest["evaluation"], "evaluation")
    _exact_keys(evaluation, ("episodes_per_cell", "adaptation", "seen_rosters", "heldout_rosters", "interventions"), "evaluation")
    if evaluation != {"episodes_per_cell": 256, "adaptation": False, "seen_rosters": [9, 15], "heldout_rosters": [6, 21], "interventions": list(INTERVENTIONS)}:
        raise ContractError("evaluation must be adaptation-free with 256 episodes per frozen cell")
    blocks = manifest["seed_blocks"]
    if not isinstance(blocks, list) or not (1 <= len(blocks) <= MAX_SEED_BLOCKS) or len(set(blocks)) != len(blocks):
        raise ContractError("seed_blocks must contain 1..24 unique fresh block identities")
    for index, block in enumerate(blocks):
        if not isinstance(block, str) or not block.startswith("FRRIE-FRESH-BLOCK-"):
            raise ContractError(f"seed_blocks[{index}] is not a fresh FRRIE block label")
    for binding_name in ("sealed_seed_packet", "preflight_receipt"):
        binding = _mapping(manifest[binding_name], binding_name)
        _exact_keys(binding, ("path",), binding_name)
        if not isinstance(binding["path"], str) or not binding["path"]:
            raise ContractError(f"{binding_name}.path must be discoverable")

    thresholds = _mapping(manifest["thresholds"], "thresholds")
    if set(thresholds) != set(THRESHOLD_FIELDS):
        raise ContractError("all six prospective threshold fields are required with no defaults")
    for field, number in thresholds.items():
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)):
            raise ContractError(f"thresholds.{field} must be a finite prospective number")

    competence = _mapping(manifest["generic_competence"], "generic_competence")
    competence_fields = (
        "heldout_direct_return_lower", "seen_direct_return_lower",
        "worst_basin_delivery_lower", "legal_action_validity_lower",
    )
    _exact_keys(competence, competence_fields, "generic_competence")
    for field, number in competence.items():
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)):
            raise ContractError(f"generic_competence.{field} must be a finite prospective number")

    work_threshold = _mapping(manifest["work_to_threshold"], "work_to_threshold")
    _exact_keys(work_threshold, ("metric", "thresholds_by_roster", "checkpoints", "crossing_rule"), "work_to_threshold")
    if work_threshold["metric"] != "native_endpoint_J" or work_threshold["crossing_rule"] != "FIRST_PROSPECTIVE_CHECKPOINT_GE_THRESHOLD":
        raise ContractError("work-to-threshold metric/crossing law mismatch")
    if work_threshold["checkpoints"] != checkpoints:
        raise ContractError("work-to-threshold checkpoints must bind training checkpoints")
    roster_thresholds = _mapping(work_threshold["thresholds_by_roster"], "work_to_threshold.thresholds_by_roster")
    _exact_keys(roster_thresholds, ("9", "15", "6", "21"), "work_to_threshold.thresholds_by_roster")
    for roster, number in roster_thresholds.items():
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(float(number)):
            raise ContractError(f"work-to-threshold value for N={roster} must be finite")

    roots = _mapping(manifest["roots"], "roots")
    if set(roots) != {"output", "checkpoint"} or not all(isinstance(v, str) and v for v in roots.values()):
        raise ContractError("fresh output and checkpoint roots are required")
    if Path(roots["output"]) == Path(roots["checkpoint"]):
        raise ContractError("output and checkpoint roots must be distinct")
    fixtures = _mapping(manifest["fixture_contracts"], "fixture_contracts")
    _exact_keys(fixtures, tuple(FIXTURE_CONTRACTS), "fixture_contracts")
    if dict(fixtures) != FIXTURE_CONTRACTS:
        raise ContractError("FRRIE-owned fixture contracts do not match the frozen controls")

    resources = _mapping(manifest["resource_ceiling"], "resource_ceiling")
    if set(resources) != {"wall_seconds", "cpu_core_hours", "rss_bytes", "scratch_bytes", "durable_bytes"}:
        raise ContractError("all resource ceilings must be prospectively supplied")
    for field, number in resources.items():
        _positive_int(number, f"resource_ceiling.{field}")
    _validate_work(manifest["work_parity"], compute, checkpoints)
    canonical_json_bytes(manifest)
    return deepcopy(dict(manifest))


def load_manifest(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read manifest: {exc}") from exc
    return validate_manifest(value)


def structural_description() -> dict[str, Any]:
    """Public facts only; contains no threshold, seed, or scientific value."""
    return {
        "schema": FRRIE_MANIFEST_V1,
        "direction_id": DIRECTION_ID,
        "experiment_id": EXPERIMENT_ID,
        "host_id": HOST_ID,
        "learned_arms": list(LEARNED_ARMS),
        "evaluation_only_arm": EVALUATION_ONLY_ARM,
        "parameter_count": MODEL_PARAMETER_COUNT,
        "updates": UPDATES,
        "episodes_per_update": EPISODES_PER_UPDATE,
        "heldout_rosters": list(HELDOUT_ROSTERS),
        "seen_evaluation_rosters": list(TRAIN_ROSTERS),
        "evaluation_episodes_per_cell": EVALUATIONS_PER_CELL,
        "production_native_backend_bundled": False,
        "vqfp_action_seam": "FRRIE_ACTION_SEAM_ABSENT",
    }
