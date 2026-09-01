"""Exact B01 manifest and invocation-resource validators."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

from .constants import (
    CHECKPOINTS, DEFAULT_NATIVE_WIDTH, DEFAULT_THREADS_PER_WORKER,
    DEFAULT_WORKERS, DIRECTION_ID, EPISODES_PER_TRAIN_ROSTER,
    EPISODES_PER_UPDATE, EVALUATION_EPISODES, EVALUATION_ROSTERS,
    EXPERIMENT_ID, HORIZON, INITIAL_ROOT_LABELS, INTERVENTIONS,
    INVOCATION_SCHEMA, LEARNED_ARMS, MANIFEST_SCHEMA, MIN_AVAILABLE_BYTES,
    IMPLEMENTATION_PROFILE, MODEL_DTYPE, MODEL_PARAMETERS, REDUCTION_DTYPE,
    ROOT_LABELS, TEST_EXPERIMENT_ID, TEST_MANIFEST_SCHEMA, TEST_SEED_LABEL,
    TRAIN_ROSTER_ORDER,
    TRAIN_ROSTERS, UNIFORM_MAPPING, UPDATES,
)


class B01ContractError(ValueError):
    """A B01 artifact changes or incompletely binds the selected object."""


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise B01ContractError("value is not canonical finite JSON") from exc


def _exact(value: Any, fields: set[str], name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise B01ContractError(f"{name} fields must be exactly {sorted(fields)}")
    return value


def _literal_int(value: Any, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise B01ContractError(f"{name} must be a literal integer >= {minimum}")
    return value


def _code_revision(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise B01ContractError(f"{name} must be one full 40-character commit revision")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise B01ContractError(f"{name} must be lowercase hexadecimal") from exc
    if len(decoded) != 20 or decoded.hex() != value:
        raise B01ContractError(f"{name} must be canonical lowercase hexadecimal")
    return value


_RESOURCE_RECEIPT_FIELDS = {
    "schema_version", "captured_at", "assessed_at", "measurement_source",
    "minimum_available_bytes", "available_physical_bytes",
    "cgroup_memory_max_bytes", "cgroup_memory_current_bytes",
    "cgroup_headroom_bytes", "effective_available_bytes",
    "physical_floor_pass", "effective_floor_pass", "passed", "failure_reasons",
}


def validate_resource_receipt(value: Any) -> dict[str, Any]:
    """Validate direct output of ``hmasd_resource_preflight.py admit-memory``."""

    receipt = _exact(value, _RESOURCE_RECEIPT_FIELDS, "resource receipt")
    if receipt["schema_version"] != 1:
        raise B01ContractError("resource receipt schema_version differs")
    for field in ("captured_at", "assessed_at", "measurement_source"):
        if not isinstance(receipt[field], str) or not receipt[field].strip():
            raise B01ContractError(f"resource receipt {field} is absent")
    if receipt["minimum_available_bytes"] != MIN_AVAILABLE_BYTES:
        raise B01ContractError("resource receipt uses a different memory floor")
    for field in ("available_physical_bytes", "effective_available_bytes"):
        if type(receipt[field]) is not int or receipt[field] < MIN_AVAILABLE_BYTES:
            raise B01ContractError(f"resource receipt {field} is below 4 GiB")
    for field in ("cgroup_memory_max_bytes", "cgroup_memory_current_bytes", "cgroup_headroom_bytes"):
        item = receipt[field]
        if item is not None and (type(item) is not int or item < 0):
            raise B01ContractError(f"resource receipt {field} is invalid")
    if (
        receipt["physical_floor_pass"] is not True
        or receipt["effective_floor_pass"] is not True
        or receipt["passed"] is not True
        or receipt["failure_reasons"] != []
    ):
        raise B01ContractError("resource receipt did not admit this invocation")
    return dict(receipt)


def bind_invocation_resource(
    *, invocation_id: str, operation: str, receipt_path: str | Path,
    receipt: Mapping[str, Any], test_only: bool,
) -> dict[str, Any]:
    if not isinstance(invocation_id, str) or not invocation_id.strip():
        raise B01ContractError("invocation_id must be nonempty")
    if operation not in {"TRAIN", "EVALUATE", "RESUME", "REPAIR", "TEST_SMOKE"}:
        raise B01ContractError("unknown B01 invocation operation")
    path0 = Path(receipt_path)
    if not path0.is_absolute():
        raise B01ContractError("resource receipt path must be absolute")
    path = path0.resolve(strict=False)
    validated = validate_resource_receipt(receipt)
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B01ContractError("bound resource receipt file is unreadable") from exc
    if stored != validated:
        raise B01ContractError("bound resource receipt file differs from direct receipt")
    value = {
        "schema": INVOCATION_SCHEMA,
        "invocation_id": invocation_id,
        "operation": operation,
        "receipt_path": str(path),
        "receipt": validated,
        "test_only": bool(test_only),
    }
    return validate_invocation_binding(value)


def validate_invocation_binding(value: Any, *, require_test_only: bool | None = None) -> dict[str, Any]:
    fields = {"schema", "invocation_id", "operation", "receipt_path", "receipt", "test_only"}
    binding = dict(_exact(value, fields, "invocation binding"))
    if binding["schema"] != INVOCATION_SCHEMA:
        raise B01ContractError("invocation binding schema differs")
    if not isinstance(binding["invocation_id"], str) or not binding["invocation_id"].strip():
        raise B01ContractError("invocation binding ID is empty")
    if binding["operation"] not in {"TRAIN", "EVALUATE", "RESUME", "REPAIR", "TEST_SMOKE"}:
        raise B01ContractError("invocation binding operation differs")
    if type(binding["test_only"]) is not bool:
        raise B01ContractError("invocation binding test_only must be literal bool")
    if binding["operation"] == "TEST_SMOKE" and not binding["test_only"]:
        raise B01ContractError("TEST_SMOKE requires the TEST-only namespace")
    if require_test_only is not None and binding["test_only"] is not require_test_only:
        raise B01ContractError("invocation binding TEST/production namespace differs")
    path = Path(binding["receipt_path"])
    if not path.is_absolute():
        raise B01ContractError("invocation receipt path must be absolute")
    receipt = validate_resource_receipt(binding["receipt"])
    try:
        stored = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B01ContractError("invocation receipt file is unreadable") from exc
    if stored != receipt:
        raise B01ContractError("invocation receipt file differs")
    binding["receipt"] = receipt
    binding["receipt_path"] = str(path.resolve(strict=False))
    return binding


def named_compute_profile() -> dict[str, Any]:
    """Return one named implementation profile, never an implicit default."""
    return {
        "profile": IMPLEMENTATION_PROFILE,
        "device": "cpu", "gpu": False, "model_dtype": MODEL_DTYPE,
        "reduction_dtype": REDUCTION_DTYPE, "native_width": DEFAULT_NATIVE_WIDTH,
        "workers": DEFAULT_WORKERS, "threads": DEFAULT_THREADS_PER_WORKER,
        "network": False, "backend": "PACKAGE_CPP_BATCH_ABI",
    }


def exact_algorithm_contract() -> dict[str, Any]:
    return {
        "optimizer": {
            "name": "ADAM", "learning_rate": 3.0e-4, "betas": [0.9, 0.999],
            "epsilon": 1.0e-8, "weight_decay": 0.0, "amsgrad": False,
            "maximize": False, "capturable": False, "differentiable": False,
            "foreach": False, "fused": None, "zero_grad_set_to_none": True,
        },
        "loss": {
            "name": "RSCF_FULL_BATCH", "entropy_coefficient": 0.01,
            "critic_coefficient": 0.5, "gradient_clip_l2": 0.5,
            "backward_calls_per_update": 1, "adam_steps_per_update": 1,
            "episodes_per_update": EPISODES_PER_UPDATE,
        },
        "projection_boxes": {
            "PHY_TRUST": [-0.15, 0.15], "EDGE_FLEX": [-1.5, 1.5],
            "application": "POST_ADAM_MOMENTS_UNCHANGED",
        },
        "evaluation": {
            "adaptation_free": True, "checkpoint_selection": False,
            "common_addressed_tapes": True,
        },
        "tuning": "NO_ARM_SPECIFIC_OR_WITHIN_RUN_TUNING",
    }


def _validate_compute(value: Any) -> dict[str, Any]:
    fields = {
        "profile", "device", "gpu", "model_dtype", "reduction_dtype", "native_width",
        "workers", "threads", "network", "backend",
    }
    compute = dict(_exact(value, fields, "compute"))
    if (
        compute["profile"] != IMPLEMENTATION_PROFILE
        or compute["device"] != "cpu" or compute["gpu"] is not False
        or compute["model_dtype"] != MODEL_DTYPE
        or compute["reduction_dtype"] != REDUCTION_DTYPE
        or compute["network"] is not False
        or compute["backend"] != "PACKAGE_CPP_BATCH_ABI"
    ):
        raise B01ContractError("B01 compute backend/dtype contract differs")
    for field in ("native_width", "workers", "threads"):
        _literal_int(compute[field], f"compute.{field}", minimum=1)
    if (
        compute["native_width"], compute["workers"], compute["threads"]
    ) != (DEFAULT_NATIVE_WIDTH, DEFAULT_WORKERS, DEFAULT_THREADS_PER_WORKER):
        raise B01ContractError("named compute profile width/worker/thread values differ")
    if compute["workers"] > compute["native_width"]:
        raise B01ContractError("workers cannot exceed native batch width")
    return compute


def validate_manifest(value: Any, *, require_roots: bool = True) -> dict[str, Any]:
    fields = {
        "schema", "direction_id", "experiment_id", "phase", "seed_packet",
        "execution_labels", "parent_initial", "code_revision", "algorithm_contract",
        "scientific_contract", "compute", "roots", "resource_policy",
    }
    manifest = dict(_exact(value, fields, "manifest"))
    if (
        manifest["schema"] != MANIFEST_SCHEMA
        or manifest["direction_id"] != DIRECTION_ID
        or manifest["experiment_id"] != EXPERIMENT_ID
    ):
        raise B01ContractError("B01 manifest identity differs")
    if manifest["phase"] not in {"INITIAL_001_003", "EXTENSION_004_005"}:
        raise B01ContractError("B01 phase is invalid")
    manifest["code_revision"] = _code_revision(manifest["code_revision"], "B01 code_revision")
    if manifest["algorithm_contract"] != exact_algorithm_contract():
        raise B01ContractError("B01 algorithm/tuning contract differs")

    packet_binding = _exact(manifest["seed_packet"], {"path", "contract"}, "seed_packet")
    packet_path = Path(packet_binding["path"])
    if not packet_path.is_absolute():
        raise B01ContractError("production seed packet path must be absolute")
    from .seed_packet import read_production_seed_packet
    packet = read_production_seed_packet(packet_path)
    if packet != packet_binding["contract"]:
        raise B01ContractError("manifest seed packet differs from persisted packet")
    if manifest["phase"] == "INITIAL_001_003":
        if manifest["execution_labels"] != list(INITIAL_ROOT_LABELS) or manifest["parent_initial"] is not None:
            raise B01ContractError("initial B01 execution must bind only 001..003 and no parent")
    else:
        if manifest["execution_labels"] != list(ROOT_LABELS[3:]):
            raise B01ContractError("extension may add only predeclared roots 004..005")
        parent = _exact(manifest["parent_initial"], {"locator", "manifest_contract"}, "parent_initial")
        if not isinstance(parent["locator"], str) or not parent["locator"].strip():
            raise B01ContractError("extension parent locator is absent")
        locator = Path(parent["locator"])
        if not locator.is_absolute():
            raise B01ContractError("extension parent locator must be absolute")
        try:
            persisted_parent = json.loads(locator.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise B01ContractError("extension persisted initial manifest is unreadable") from exc
        if persisted_parent != parent["manifest_contract"]:
            raise B01ContractError("extension embedded parent differs from persisted initial manifest")

    science = dict(_exact(
        manifest["scientific_contract"],
        {
            "learned_arms", "train_rosters", "train_roster_order", "updates",
            "episodes_per_update", "episodes_per_train_roster", "checkpoints",
            "evaluation_rosters", "interventions", "evaluation_episodes",
            "horizon", "model_parameters", "uniform_mapping",
            "checkpoint_randomness_role", "uniform_baseline_schedule",
        },
        "scientific_contract",
    ))
    expected = {
        "learned_arms": list(LEARNED_ARMS),
        "train_rosters": list(TRAIN_ROSTERS),
        "train_roster_order": list(TRAIN_ROSTER_ORDER),
        "updates": UPDATES,
        "episodes_per_update": EPISODES_PER_UPDATE,
        "episodes_per_train_roster": EPISODES_PER_TRAIN_ROSTER,
        "checkpoints": list(CHECKPOINTS),
        "evaluation_rosters": list(EVALUATION_ROSTERS),
        "interventions": list(INTERVENTIONS),
        "evaluation_episodes": EVALUATION_EPISODES,
        "horizon": HORIZON,
        "model_parameters": MODEL_PARAMETERS,
        "uniform_mapping": UNIFORM_MAPPING,
        "checkpoint_randomness_role": "METADATA_ONLY",
        "uniform_baseline_schedule": "ONCE_PER_SEED_N9_N15_INTACT",
    }
    if science != expected:
        raise B01ContractError("scientific_contract differs from literal B01 constants")
    manifest["scientific_contract"] = science
    manifest["compute"] = _validate_compute(manifest["compute"])

    bound_roots = _exact(manifest["roots"], {"output", "checkpoint", "scratch"}, "roots")
    if require_roots:
        paths = [Path(bound_roots[name]).resolve(strict=False) for name in bound_roots]
        if len(set(paths)) != 3 or any(not path.is_absolute() for path in paths):
            raise B01ContractError("B01 output/checkpoint/scratch roots must be distinct absolute paths")
        if len({path.parent for path in paths}) != 1:
            raise B01ContractError("B01 roots must be siblings under one fresh run parent")
    policy = _exact(
        manifest["resource_policy"],
        {"minimum_available_bytes", "fresh_receipt_each_invocation", "telemetry_required"},
        "resource_policy",
    )
    if policy != {
        "minimum_available_bytes": MIN_AVAILABLE_BYTES,
        "fresh_receipt_each_invocation": True,
        "telemetry_required": True,
    }:
        raise B01ContractError("resource policy differs from the B01 admission contract")
    if manifest["phase"] == "EXTENSION_004_005":
        parent_manifest = validate_manifest(manifest["parent_initial"]["manifest_contract"])
        if parent_manifest["phase"] != "INITIAL_001_003":
            raise B01ContractError("extension parent is not the initial phase")
        for field in (
            "seed_packet", "scientific_contract", "compute", "resource_policy",
            "code_revision", "algorithm_contract",
        ):
            if parent_manifest[field] != manifest[field]:
                raise B01ContractError(f"extension changed frozen parent {field}")
    return manifest


def manifest_template(
    *, seed_packet_path: str | Path, phase: str, roots: Mapping[str, str],
    compute: Mapping[str, Any], code_revision: str,
    parent_initial: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from .seed_packet import read_production_seed_packet
    packet_path = Path(seed_packet_path).resolve(strict=False)
    value = {
        "schema": MANIFEST_SCHEMA,
        "direction_id": DIRECTION_ID,
        "experiment_id": EXPERIMENT_ID,
        "phase": phase,
        "execution_labels": (
            list(INITIAL_ROOT_LABELS) if phase == "INITIAL_001_003" else list(ROOT_LABELS[3:])
        ),
        "parent_initial": None if parent_initial is None else dict(parent_initial),
        "code_revision": code_revision,
        "algorithm_contract": exact_algorithm_contract(),
        "seed_packet": {
            "path": str(packet_path),
            "contract": read_production_seed_packet(packet_path),
        },
        "scientific_contract": {
            "learned_arms": list(LEARNED_ARMS),
            "train_rosters": list(TRAIN_ROSTERS),
            "train_roster_order": list(TRAIN_ROSTER_ORDER),
            "updates": UPDATES,
            "episodes_per_update": EPISODES_PER_UPDATE,
            "episodes_per_train_roster": EPISODES_PER_TRAIN_ROSTER,
            "checkpoints": list(CHECKPOINTS),
            "evaluation_rosters": list(EVALUATION_ROSTERS),
            "interventions": list(INTERVENTIONS),
            "evaluation_episodes": EVALUATION_EPISODES,
            "horizon": HORIZON,
            "model_parameters": MODEL_PARAMETERS,
            "uniform_mapping": UNIFORM_MAPPING,
            "checkpoint_randomness_role": "METADATA_ONLY",
            "uniform_baseline_schedule": "ONCE_PER_SEED_N9_N15_INTACT",
        },
        # Caller must explicitly select and persist a measured implementation profile.
        "compute": dict(compute),
        "roots": dict(roots),
        "resource_policy": {
            "minimum_available_bytes": MIN_AVAILABLE_BYTES,
            "fresh_receipt_each_invocation": True,
            "telemetry_required": True,
        },
    }
    return validate_manifest(value)


def validate_test_manifest(value: Any) -> dict[str, Any]:
    fields = {
        "schema", "namespace", "experiment_id", "seed_label",
        "seed_packet", "source_state", "algorithm_contract", "compute", "roots",
        "resource_policy",
    }
    manifest = dict(_exact(value, fields, "TEST manifest"))
    if (
        manifest["schema"] != TEST_MANIFEST_SCHEMA
        or manifest["namespace"] != "TEST_ONLY"
        or manifest["experiment_id"] != TEST_EXPERIMENT_ID
        or manifest["seed_label"] != TEST_SEED_LABEL
    ):
        raise B01ContractError("TEST manifest identity differs")
    if manifest["algorithm_contract"] != exact_algorithm_contract():
        raise B01ContractError("TEST manifest algorithm contract differs")
    packet_binding = _exact(manifest["seed_packet"], {"path", "contract"}, "TEST seed packet")
    packet_path = Path(packet_binding["path"])
    from .seed_packet import read_test_seed_packet
    packet = read_test_seed_packet(packet_path)
    if packet != packet_binding["contract"]:
        raise B01ContractError("TEST manifest seed packet differs from persisted packet")
    source_state = dict(_exact(
        manifest["source_state"], {"base_commit", "worktree_state"},
        "TEST source_state",
    ))
    source_state["base_commit"] = _code_revision(
        source_state["base_commit"], "TEST base_commit",
    )
    if source_state["worktree_state"] != "DIRTY_UNCOMMITTED_TEST_ONLY":
        raise B01ContractError("TEST worktree_state must identify the uncommitted TEST source")
    manifest["source_state"] = source_state
    manifest["compute"] = _validate_compute(manifest["compute"])
    roots = _exact(manifest["roots"], {"output", "checkpoint", "scratch"}, "TEST roots")
    paths = [Path(roots[name]).resolve(strict=False) for name in roots]
    if len(set(paths)) != 3 or any(not path.is_absolute() for path in paths):
        raise B01ContractError("TEST roots must be three distinct absolute paths")
    if len({path.parent for path in paths}) != 1:
        raise B01ContractError("TEST roots must be siblings under one fresh run parent")
    if manifest["resource_policy"] != {
        "minimum_available_bytes": MIN_AVAILABLE_BYTES,
        "fresh_receipt_each_invocation": True,
        "telemetry_required": True,
    }:
        raise B01ContractError("TEST resource policy differs")
    return manifest


def make_test_manifest(
    *, seed_packet_path: str | Path, roots: Mapping[str, str],
    compute: Mapping[str, Any], base_commit: str, worktree_state: str,
) -> dict[str, Any]:
    from .seed_packet import read_test_seed_packet
    packet_path = Path(seed_packet_path).resolve(strict=False)
    return validate_test_manifest({
        "schema": TEST_MANIFEST_SCHEMA,
        "namespace": "TEST_ONLY",
        "experiment_id": TEST_EXPERIMENT_ID,
        "seed_label": TEST_SEED_LABEL,
        "seed_packet": {"path": str(packet_path), "contract": read_test_seed_packet(packet_path)},
        "source_state": {
            "base_commit": base_commit,
            "worktree_state": worktree_state,
        },
        "algorithm_contract": exact_algorithm_contract(),
        "compute": dict(compute),
        "roots": dict(roots),
        "resource_policy": {
            "minimum_available_bytes": MIN_AVAILABLE_BYTES,
            "fresh_receipt_each_invocation": True,
            "telemetry_required": True,
        },
    })
