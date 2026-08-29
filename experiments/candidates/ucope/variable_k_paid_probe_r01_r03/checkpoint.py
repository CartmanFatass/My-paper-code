"""Atomic TEST-only S0/S1 checkpoints and persisted fixture-shape schemas."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Mapping

import torch

from .contract import (
    COMPONENT,
    COUNTER_LAYOUT_ID,
    FINAL_CHECKPOINT_SLOT_COUNT,
    OBJECT_REVISION,
    S1_TEST_NAMESPACE,
    S1_TEST_REQUEST,
    S1_TEST_SEEDS,
    TRAINING_BATCHES,
    TEST_NAMESPACE,
    require_s1_test_request,
)
from .model import LearnerBundle
from .training import ReductionFrontier, SupportCounters


SCHEMA = "UCOPE_R01_R03_S0_TEST_CHECKPOINT_V1"
S1_FRONTIER_SCHEMA = "UCOPE_R01_R03_S1_TEST_WORK_UNIT_FRONTIER_V1"
S1_MANIFEST_SCHEMA = "UCOPE_R01_R03_S1_TEST_90_SLOT_MANIFEST_V2"
S1_SLOT_SCHEMA = "UCOPE_R01_R03_S1_TEST_NONPROMOTABLE_SLOT_CHECKPOINT_V1"
S1_CHECKPOINT_SHAPE_SCHEMA = "UCOPE_R01_R03_S1_BATCH_320_FINAL_CHECKPOINT_SHAPE_V1"
S1_CHECKPOINT_DIRECTORY = "ucope_r01_r03_s1_90_slot_checkpoint_shape.TEST_ONLY"
S1_SLOT_DIRECTORY = "slots"
S1_MANIFEST_FILENAME = "manifest.TEST_ONLY.json"


def _require_lower_sha256(value: object, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{name} must be one lowercase SHA-256")
    return value


def _bundle_state(bundle: LearnerBundle) -> dict[str, object]:
    return {
        "scorer": bundle.scorer.state_dict(),
        "baseline": bundle.baseline.state_dict(),
        "optimizer": bundle.optimizer.state_dict(),
    }


def _validate_metadata(metadata: Mapping[str, object]) -> None:
    required = {
        "completed_batch", "next_batch", "counter_frontier", "batch_width",
        "worker_count", "torch_threads", "source_sha256", "native_artifact_sha256",
    }
    if set(metadata) != required:
        raise ValueError("checkpoint metadata fields differ from the frozen S0 schema")
    completed = metadata["completed_batch"]
    next_batch = metadata["next_batch"]
    if isinstance(completed, bool) or not isinstance(completed, int) or completed < 0:
        raise ValueError("completed_batch must be a nonnegative integer")
    if next_batch != completed + 1:
        raise ValueError("next_batch must be exactly completed_batch + 1")
    if metadata["batch_width"] != 768:
        raise ValueError("S0 checkpoints use the natural 768-lane coupon")
    for name in ("counter_frontier", "source_sha256", "native_artifact_sha256"):
        _require_lower_sha256(metadata[name], f"S0 {name}")


def save_atomic(path: Path, bundles: list[LearnerBundle], metadata: Mapping[str, object]) -> str:
    if len(bundles) != 3:
        raise ValueError("S0 checkpoint requires exactly three learned-arm bundles")
    _validate_metadata(metadata)
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": SCHEMA,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": TEST_NAMESPACE,
        "question_relevant": False,
        "complete_r03_package": False,
        "dtype": "torch.float32",
        "recurrent_state": "NOT_APPLICABLE",
        "metadata": dict(metadata),
        "bundles": [_bundle_state(bundle) for bundle in bundles],
    }
    temporary = target.with_name(f".{target.name}.{os.getpid()}.pending")
    try:
        with temporary.open("xb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def load_cold(path: Path, bundles: list[LearnerBundle]) -> dict[str, object]:
    target = Path(path).resolve(strict=True)
    if len(bundles) != 3:
        raise ValueError("S0 checkpoint requires exactly three learned-arm bundles")
    with target.open("rb") as stream:
        payload = torch.load(stream, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise ValueError("checkpoint schema mismatch")
    if payload.get("object_revision") != OBJECT_REVISION or payload.get("component") != COMPONENT:
        raise ValueError("checkpoint object/component identity mismatch")
    if payload.get("namespace") != TEST_NAMESPACE or payload.get("question_relevant") is not False:
        raise ValueError("checkpoint crossed the TEST firewall")
    if payload.get("complete_r03_package") is not False or payload.get("dtype") != "torch.float32":
        raise ValueError("checkpoint completeness/dtype firewall mismatch")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("checkpoint metadata is malformed")
    _validate_metadata(metadata)
    states = payload.get("bundles")
    if not isinstance(states, list) or len(states) != 3:
        raise ValueError("checkpoint learned-arm state is incomplete")
    for bundle, state in zip(bundles, states, strict=True):
        bundle.scorer.load_state_dict(state["scorer"])
        bundle.baseline.load_state_dict(state["baseline"])
        bundle.optimizer.load_state_dict(state["optimizer"])
    return dict(metadata)


def state_bytes(bundles: list[LearnerBundle], metadata: Mapping[str, object]) -> bytes:
    """Canonical in-process equality surface for model/optimizer/frontier bytes."""

    _validate_metadata(metadata)
    output = io.BytesIO()
    for bundle in bundles:
        for label, state in (
            ("scorer", bundle.scorer.state_dict()),
            ("baseline", bundle.baseline.state_dict()),
            ("optimizer", bundle.optimizer.state_dict()),
        ):
            output.write(label.encode("ascii") + b"\0")
            _write_value(output, state)
    _write_value(output, dict(sorted(metadata.items())))
    return output.getvalue()


def _write_value(output: io.BytesIO, value: Any) -> None:
    if torch.is_tensor(value):
        tensor = value.detach().cpu().contiguous()
        output.write(str(tensor.dtype).encode("ascii") + b":" + repr(tuple(tensor.shape)).encode("ascii") + b":")
        output.write(tensor.numpy().tobytes(order="C"))
    elif isinstance(value, Mapping):
        for key in sorted(value, key=lambda item: repr(item)):
            output.write(repr(key).encode("utf-8") + b"=")
            _write_value(output, value[key])
    elif isinstance(value, (list, tuple)):
        for item in value:
            _write_value(output, item)
    else:
        output.write(repr(value).encode("utf-8") + b";")


def state_sha256(bundles: list[LearnerBundle], metadata: Mapping[str, object]) -> str:
    return hashlib.sha256(state_bytes(bundles, metadata)).hexdigest()


def _validate_s1_metadata(metadata: Mapping[str, object]) -> None:
    required = {
        "test_seed", "test_seed_slot", "panel", "completed_batch", "next_batch",
        "counter_frontier", "reduction_frontier", "batch_width", "worker_count",
        "torch_threads", "source_sha256", "native_artifact_sha256",
        "counter_layout_id",
    }
    if set(metadata) != required:
        raise ValueError("S1 frontier metadata fields differ from the frozen schema")
    slot = metadata["test_seed_slot"]
    if isinstance(slot, bool) or not isinstance(slot, int) or not 0 <= slot < 10:
        raise ValueError("S1 test seed slot must be in 0..9")
    if metadata["test_seed"] != S1_TEST_SEEDS[slot]:
        raise ValueError("S1 TEST seed does not match its structural slot")
    require_s1_test_request(S1_TEST_NAMESPACE, int(metadata["test_seed"]), S1_TEST_REQUEST)
    if metadata["panel"] not in (0, 1, 2):
        raise ValueError("S1 frontier panel must be 0..2")
    completed = metadata["completed_batch"]
    if isinstance(completed, bool) or not isinstance(completed, int) or not 0 <= completed <= 320:
        raise ValueError("completed_batch must be in 0..320")
    if metadata["next_batch"] != completed + 1:
        raise ValueError("next_batch must be exactly completed_batch + 1")
    if metadata["batch_width"] != 768 or metadata["counter_layout_id"] != COUNTER_LAYOUT_ID:
        raise ValueError("S1 width/counter-layout identity mismatch")
    if metadata["worker_count"] not in range(1, 17) or metadata["torch_threads"] not in (1, 2):
        raise ValueError("S1 worker/thread metadata is outside the bounded CPU plan")
    for name in ("counter_frontier", "source_sha256", "native_artifact_sha256"):
        _require_lower_sha256(metadata[name], f"S1 {name}")
    reduction = metadata["reduction_frontier"]
    if not isinstance(reduction, Mapping):
        raise ValueError("S1 reduction frontier is malformed")
    if set(reduction) != {"schema", "count", "ordered_values_sha256", "total_fp32_bits"}:
        raise ValueError("S1 reduction frontier fields differ from the frozen schema")
    if reduction.get("schema") != "UCOPE_R01_R03_S1_REDUCTION_FRONTIER_V1":
        raise ValueError("S1 reduction frontier identity mismatch")
    if not isinstance(reduction.get("count"), int) or int(reduction["count"]) <= 0:
        raise ValueError("S1 reduction frontier count must be positive")
    _require_lower_sha256(
        reduction.get("ordered_values_sha256"),
        "S1 reduction frontier ordered_values_sha256",
    )
    if not isinstance(reduction.get("total_fp32_bits"), int) or not 0 <= int(reduction["total_fp32_bits"]) < 1 << 32:
        raise ValueError("S1 reduction frontier FP32 bits are malformed")


def save_s1_frontier_atomic(
    path: Path, bundles: list[LearnerBundle], support: SupportCounters,
    reduction: ReductionFrontier, metadata: Mapping[str, object],
) -> str:
    if len(bundles) != 3:
        raise ValueError("S1 frontier requires exactly three learned-arm bundles")
    support.validate()
    _validate_s1_metadata(metadata)
    if dict(metadata["reduction_frontier"]) != reduction.as_dict():
        raise ValueError("S1 metadata/reduction frontier mismatch")
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": S1_FRONTIER_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "question_relevant": False,
        "partial_result": False,
        "complete_r03_package": False,
        "dtype": "torch.float32",
        "recurrent_state": "NOT_APPLICABLE",
        "metadata": dict(metadata),
        "support": support.as_dict(),
        "bundles": [_bundle_state(bundle) for bundle in bundles],
    }
    temporary = target.with_name(f".{target.name}.{os.getpid()}.pending")
    try:
        with temporary.open("xb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def load_s1_frontier_cold(
    path: Path, bundles: list[LearnerBundle],
) -> tuple[dict[str, object], SupportCounters, ReductionFrontier]:
    target = Path(path).resolve(strict=True)
    if len(bundles) != 3:
        raise ValueError("S1 frontier requires exactly three learned-arm bundles")
    with target.open("rb") as stream:
        payload = torch.load(stream, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or payload.get("schema") != S1_FRONTIER_SCHEMA:
        raise ValueError("S1 frontier schema mismatch")
    if payload.get("object_revision") != OBJECT_REVISION or payload.get("component") != COMPONENT:
        raise ValueError("S1 frontier object/component identity mismatch")
    if payload.get("namespace") != S1_TEST_NAMESPACE or payload.get("request") != S1_TEST_REQUEST:
        raise ValueError("S1 frontier crossed the TEST request firewall")
    if any(payload.get(name) is not False for name in ("question_relevant", "partial_result", "complete_r03_package")):
        raise ValueError("S1 frontier crossed the result firewall")
    if payload.get("dtype") != "torch.float32" or payload.get("recurrent_state") != "NOT_APPLICABLE":
        raise ValueError("S1 frontier dtype/recurrent identity mismatch")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("S1 frontier metadata is malformed")
    _validate_s1_metadata(metadata)
    support_payload = payload.get("support")
    if not isinstance(support_payload, Mapping):
        raise ValueError("S1 support state is malformed")
    support = SupportCounters.from_dict(support_payload)
    reduction_payload = metadata["reduction_frontier"]
    if reduction_payload.get("schema") != "UCOPE_R01_R03_S1_REDUCTION_FRONTIER_V1":
        raise ValueError("S1 reduction-frontier schema mismatch")
    reduction = ReductionFrontier(
        count=int(reduction_payload["count"]),
        ordered_values_sha256=str(reduction_payload["ordered_values_sha256"]),
        total_fp32_bits=int(reduction_payload["total_fp32_bits"]),
    )
    states = payload.get("bundles")
    if not isinstance(states, list) or len(states) != 3:
        raise ValueError("S1 learned-arm frontier is incomplete")
    for bundle, state in zip(bundles, states, strict=True):
        bundle.scorer.load_state_dict(state["scorer"])
        bundle.baseline.load_state_dict(state["baseline"])
        bundle.optimizer.load_state_dict(state["optimizer"])
    return dict(metadata), support, reduction


def s1_state_bytes(
    bundles: list[LearnerBundle], support: SupportCounters,
    reduction: ReductionFrontier, metadata: Mapping[str, object],
) -> bytes:
    _validate_s1_metadata(metadata)
    support.validate()
    output = io.BytesIO()
    for bundle in bundles:
        _write_value(output, _bundle_state(bundle))
    _write_value(output, support.as_dict())
    _write_value(output, reduction.as_dict())
    _write_value(output, dict(sorted(metadata.items())))
    return output.getvalue()


def s1_state_sha256(
    bundles: list[LearnerBundle], support: SupportCounters,
    reduction: ReductionFrontier, metadata: Mapping[str, object],
) -> str:
    return hashlib.sha256(s1_state_bytes(bundles, support, reduction, metadata)).hexdigest()


_S1_FIXTURE_KIND = "INITIAL_PAIRED_NONPROMOTABLE_TEST_LEARNER_STATE"
_S1_SCORER_STATE_SHAPES = {
    "network.0.weight": (64, 13),
    "network.0.bias": (64,),
    "network.2.weight": (64, 64),
    "network.2.bias": (64,),
    "network.4.weight": (1, 64),
    "network.4.bias": (1,),
}
_S1_BASELINE_STATE_SHAPES = {
    "network.0.weight": (32, 9),
    "network.0.bias": (32,),
    "network.2.weight": (1, 32),
    "network.2.bias": (1,),
}
_S1_SLOT_PAYLOAD_KEYS = {
    "schema",
    "object_revision",
    "component",
    "namespace",
    "request",
    "slot",
    "panel",
    "test_seed_slot",
    "test_seed",
    "learned_arm",
    "checkpoint_shape_schema",
    "checkpoint_shape_training_batches",
    "fixture_kind",
    "fixture_completed_training_batches",
    "registered_training_executed",
    "registered_evaluation_executed",
    "dtype",
    "question_relevant_output",
    "partial_result",
    "complete_r03_package",
    "scientific_final_checkpoint",
    "promotable",
    "state_sha256",
    "state_bytes",
    "state",
}
_S1_SLOT_ROW_KEYS = _S1_SLOT_PAYLOAD_KEYS - {"schema", "object_revision", "component", "state"}
_S1_SLOT_ROW_KEYS = _S1_SLOT_ROW_KEYS | {
    "relative_path",
    "artifact_sha256",
    "artifact_bytes",
}
_S1_MANIFEST_KEYS = {
    "schema",
    "slot_schema",
    "checkpoint_shape_schema",
    "checkpoint_shape_training_batches",
    "object_revision",
    "component",
    "namespace",
    "request",
    "fixture_kind",
    "fixture_completed_training_batches",
    "registered_training_executed",
    "registered_evaluation_executed",
    "dtype",
    "slot_count",
    "persisted_slot_count",
    "all_slot_files_present",
    "all_slot_digests_verified",
    "question_relevant_output",
    "partial_result",
    "complete_r03_package",
    "scientific_final_checkpoint",
    "promotable",
    "slots",
}


def _s1_slot_coordinates() -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (panel, seed_slot, learned_arm)
        for panel in range(3)
        for seed_slot in range(10)
        for learned_arm in range(3)
    )


def _s1_slot_name(panel: int, test_seed_slot: int, learned_arm: int) -> str:
    return (
        f"panel{panel}:test_seed_slot{test_seed_slot}:"
        f"learned_arm{learned_arm}"
    )


def _s1_slot_relative_path(
    panel: int, test_seed_slot: int, learned_arm: int,
) -> Path:
    return (
        Path(f"panel{panel}")
        / f"test_seed_slot{test_seed_slot:02d}"
        / f"learned_arm{learned_arm}.TEST_ONLY.pt"
    )


def expected_s1_manifest_slots() -> tuple[str, ...]:
    return tuple(
        _s1_slot_name(panel, seed_slot, learned_arm)
        for panel, seed_slot, learned_arm in _s1_slot_coordinates()
    )


def s1_test_checkpoint_paths(work_root: Path) -> tuple[Path, Path]:
    checkpoint_root = Path(work_root).resolve() / S1_CHECKPOINT_DIRECTORY
    return (
        checkpoint_root / S1_SLOT_DIRECTORY,
        checkpoint_root / S1_MANIFEST_FILENAME,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_fixture_state(state: object) -> None:
    if not isinstance(state, Mapping) or set(state) != {
        "scorer", "baseline", "optimizer",
    }:
        raise ValueError("S1 TEST slot learner-state fields differ from the schema")
    for label, expected_shapes in (
        ("scorer", _S1_SCORER_STATE_SHAPES),
        ("baseline", _S1_BASELINE_STATE_SHAPES),
    ):
        values = state[label]
        if not isinstance(values, Mapping) or set(values) != set(expected_shapes):
            raise ValueError(f"S1 TEST slot {label} state shape schema differs")
        for name, shape in expected_shapes.items():
            tensor = values[name]
            if (
                not torch.is_tensor(tensor)
                or tensor.dtype != torch.float32
                or tuple(tensor.shape) != shape
            ):
                raise ValueError(
                    f"S1 TEST slot {label}.{name} is not the exact FP32 shape"
                )
    optimizer = state["optimizer"]
    if not isinstance(optimizer, Mapping):
        raise ValueError("S1 TEST slot optimizer state is malformed")
    optimizer_state = optimizer.get("state")
    parameter_groups = optimizer.get("param_groups")
    if not isinstance(optimizer_state, Mapping) or optimizer_state:
        raise ValueError("S1 TEST slot must contain zero optimizer activity")
    if not isinstance(parameter_groups, list) or len(parameter_groups) != 1:
        raise ValueError("S1 TEST slot optimizer parameter group is malformed")
    group = parameter_groups[0]
    required_group = {
        "lr": 3e-4,
        "betas": (0.9, 0.999),
        "eps": 1e-8,
        "weight_decay": 1e-4,
        "amsgrad": False,
        "maximize": False,
        "params": list(range(10)),
    }
    if not isinstance(group, Mapping) or any(
        group.get(name) != expected for name, expected in required_group.items()
    ):
        raise ValueError("S1 TEST slot optimizer identity differs from frozen AdamW")


def _fixture_state_bytes(state: Mapping[str, object]) -> bytes:
    _validate_fixture_state(state)
    output = io.BytesIO()
    _write_value(output, state)
    return output.getvalue()


def _validate_s1_slot_coordinate(
    *, panel: int, test_seed_slot: int, learned_arm: int,
) -> int:
    values = (panel, test_seed_slot, learned_arm)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise ValueError("S1 TEST slot coordinates must be integers")
    if panel not in (0, 1, 2) or test_seed_slot not in range(10):
        raise ValueError("S1 TEST slot panel/seed coordinate is outside the schema")
    if learned_arm not in (0, 1, 2):
        raise ValueError("S1 TEST slot learned arm must be 0..2")
    return S1_TEST_SEEDS[test_seed_slot]


def _validate_s1_slot_payload(
    payload: object, *, namespace: str, request: str, panel: int,
    test_seed_slot: int, learned_arm: int,
) -> tuple[str, int]:
    test_seed = _validate_s1_slot_coordinate(
        panel=panel, test_seed_slot=test_seed_slot, learned_arm=learned_arm,
    )
    require_s1_test_request(namespace, test_seed, request)
    if not isinstance(payload, Mapping) or set(payload) != _S1_SLOT_PAYLOAD_KEYS:
        raise ValueError("S1 TEST slot artifact fields differ from the strict schema")
    expected_identity = {
        "schema": S1_SLOT_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": namespace,
        "request": request,
        "slot": _s1_slot_name(panel, test_seed_slot, learned_arm),
        "panel": panel,
        "test_seed_slot": test_seed_slot,
        "test_seed": test_seed,
        "learned_arm": learned_arm,
        "checkpoint_shape_schema": S1_CHECKPOINT_SHAPE_SCHEMA,
        "checkpoint_shape_training_batches": TRAINING_BATCHES,
        "fixture_kind": _S1_FIXTURE_KIND,
        "fixture_completed_training_batches": 0,
        "registered_training_executed": False,
        "registered_evaluation_executed": False,
        "dtype": "torch.float32",
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "scientific_final_checkpoint": False,
        "promotable": False,
    }
    if any(payload.get(name) != expected for name, expected in expected_identity.items()):
        raise ValueError("S1 TEST slot identity/activity firewall mismatch")
    state = payload["state"]
    if not isinstance(state, Mapping):
        raise ValueError("S1 TEST slot serialized learner state is malformed")
    serialized_state = _fixture_state_bytes(state)
    state_sha256 = _require_lower_sha256(
        payload["state_sha256"], "S1 TEST slot state_sha256",
    )
    state_bytes = payload["state_bytes"]
    if (
        isinstance(state_bytes, bool)
        or not isinstance(state_bytes, int)
        or state_bytes != len(serialized_state)
        or state_sha256 != hashlib.sha256(serialized_state).hexdigest()
    ):
        raise ValueError("S1 TEST slot serialized state bytes/digest differ")
    return state_sha256, state_bytes


def save_s1_test_slot_atomic(
    artifact_root: Path, bundle: LearnerBundle, *, namespace: str, request: str,
    panel: int, test_seed_slot: int, learned_arm: int,
) -> dict[str, object]:
    test_seed = _validate_s1_slot_coordinate(
        panel=panel, test_seed_slot=test_seed_slot, learned_arm=learned_arm,
    )
    require_s1_test_request(namespace, test_seed, request)
    root = Path(artifact_root)
    if root.is_symlink():
        raise ValueError("S1 TEST slot artifact root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    relative_path = _s1_slot_relative_path(panel, test_seed_slot, learned_arm)
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = target.parent.resolve(strict=True)
    if resolved_parent != root and root not in resolved_parent.parents:
        raise ValueError("S1 TEST slot artifact path escaped its canonical root")
    if target.is_symlink():
        raise ValueError("S1 TEST slot artifact target must not be a symlink")
    state = _bundle_state(bundle)
    serialized_state = _fixture_state_bytes(state)
    payload = {
        "schema": S1_SLOT_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": namespace,
        "request": request,
        "slot": _s1_slot_name(panel, test_seed_slot, learned_arm),
        "panel": panel,
        "test_seed_slot": test_seed_slot,
        "test_seed": test_seed,
        "learned_arm": learned_arm,
        "checkpoint_shape_schema": S1_CHECKPOINT_SHAPE_SCHEMA,
        "checkpoint_shape_training_batches": TRAINING_BATCHES,
        "fixture_kind": _S1_FIXTURE_KIND,
        "fixture_completed_training_batches": 0,
        "registered_training_executed": False,
        "registered_evaluation_executed": False,
        "dtype": "torch.float32",
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "scientific_final_checkpoint": False,
        "promotable": False,
        "state_sha256": hashlib.sha256(serialized_state).hexdigest(),
        "state_bytes": len(serialized_state),
        "state": state,
    }
    temporary = target.with_name(f".{target.name}.{os.getpid()}.pending")
    try:
        with temporary.open("xb") as stream:
            torch.save(payload, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    artifact_sha256 = _file_sha256(target)
    artifact_bytes = target.stat().st_size
    return {
        key: value
        for key, value in payload.items()
        if key not in {"schema", "object_revision", "component", "state"}
    } | {
        "relative_path": relative_path.as_posix(),
        "artifact_sha256": artifact_sha256,
        "artifact_bytes": artifact_bytes,
    }


def load_s1_test_slot_cold(
    path: Path, *, namespace: str, request: str, panel: int,
    test_seed_slot: int, learned_arm: int, expected_artifact_sha256: str,
    expected_artifact_bytes: int,
) -> tuple[str, int]:
    _require_lower_sha256(
        expected_artifact_sha256, "S1 TEST slot artifact_sha256",
    )
    if (
        isinstance(expected_artifact_bytes, bool)
        or not isinstance(expected_artifact_bytes, int)
        or expected_artifact_bytes <= 0
    ):
        raise ValueError("S1 TEST slot artifact_bytes must be positive")
    source = Path(path)
    if source.is_symlink():
        raise ValueError("S1 TEST slot artifact must not be a symlink")
    target = source.resolve(strict=True)
    if not target.is_file():
        raise ValueError("S1 TEST slot artifact path is not a file")
    encoded = target.read_bytes()
    if len(encoded) != expected_artifact_bytes:
        raise ValueError("S1 TEST slot artifact size differs from its manifest")
    if hashlib.sha256(encoded).hexdigest() != expected_artifact_sha256:
        raise ValueError("S1 TEST slot artifact digest differs from its manifest")
    payload = torch.load(
        io.BytesIO(encoded), map_location="cpu", weights_only=False,
    )
    return _validate_s1_slot_payload(
        payload,
        namespace=namespace,
        request=request,
        panel=panel,
        test_seed_slot=test_seed_slot,
        learned_arm=learned_arm,
    )


def build_s1_structural_manifest(
    slot_artifacts: Mapping[str, Mapping[str, object]], *, artifact_root: Path,
    namespace: str, request: str,
) -> dict[str, object]:
    require_s1_test_request(namespace, S1_TEST_SEEDS[0], request)
    expected_slots = expected_s1_manifest_slots()
    if (
        set(slot_artifacts) != set(expected_slots)
        or len(slot_artifacts) != FINAL_CHECKPOINT_SLOT_COUNT
    ):
        raise ValueError("S1 persisted manifest must contain exactly 90 unique slots")
    manifest = {
        "schema": S1_MANIFEST_SCHEMA,
        "slot_schema": S1_SLOT_SCHEMA,
        "checkpoint_shape_schema": S1_CHECKPOINT_SHAPE_SCHEMA,
        "checkpoint_shape_training_batches": TRAINING_BATCHES,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": namespace,
        "request": request,
        "fixture_kind": _S1_FIXTURE_KIND,
        "fixture_completed_training_batches": 0,
        "registered_training_executed": False,
        "registered_evaluation_executed": False,
        "dtype": "torch.float32",
        "slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "persisted_slot_count": len(slot_artifacts),
        "all_slot_files_present": True,
        "all_slot_digests_verified": True,
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "scientific_final_checkpoint": False,
        "promotable": False,
        "slots": [dict(slot_artifacts[slot]) for slot in expected_slots],
    }
    validate_s1_structural_manifest(manifest, artifact_root=artifact_root)
    return manifest


def validate_s1_structural_manifest(
    manifest: Mapping[str, object], *, artifact_root: Path,
) -> None:
    if set(manifest) != _S1_MANIFEST_KEYS:
        raise ValueError("S1 persisted manifest fields differ from the strict schema")
    expected_identity = {
        "schema": S1_MANIFEST_SCHEMA,
        "slot_schema": S1_SLOT_SCHEMA,
        "checkpoint_shape_schema": S1_CHECKPOINT_SHAPE_SCHEMA,
        "checkpoint_shape_training_batches": TRAINING_BATCHES,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "fixture_kind": _S1_FIXTURE_KIND,
        "fixture_completed_training_batches": 0,
        "registered_training_executed": False,
        "registered_evaluation_executed": False,
        "dtype": "torch.float32",
        "slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "persisted_slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "all_slot_files_present": True,
        "all_slot_digests_verified": True,
        "question_relevant_output": False,
        "partial_result": False,
        "complete_r03_package": False,
        "scientific_final_checkpoint": False,
        "promotable": False,
    }
    if any(manifest.get(name) != expected for name, expected in expected_identity.items()):
        raise ValueError("S1 persisted manifest identity/activity firewall mismatch")
    require_s1_test_request(
        str(manifest["namespace"]), S1_TEST_SEEDS[0], str(manifest["request"]),
    )
    rows = manifest.get("slots")
    if not isinstance(rows, list) or len(rows) != FINAL_CHECKPOINT_SLOT_COUNT:
        raise ValueError("S1 persisted manifest slot list is incomplete")
    root_source = Path(artifact_root)
    if root_source.is_symlink():
        raise ValueError("S1 TEST slot artifact root must not be a symlink")
    root = root_source.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("S1 TEST slot artifact root is not a directory")
    expected_files = {
        _s1_slot_relative_path(panel, seed_slot, learned_arm).as_posix()
        for panel, seed_slot, learned_arm in _s1_slot_coordinates()
    }
    observed_files: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("S1 TEST slot artifact tree must not contain symlinks")
        if path.is_file():
            observed_files.add(path.relative_to(root).as_posix())
    if observed_files != expected_files:
        raise ValueError("S1 TEST slot files are not the exact 90-file cross-product")
    for row, (panel, seed_slot, learned_arm) in zip(
        rows, _s1_slot_coordinates(), strict=True,
    ):
        if not isinstance(row, Mapping) or set(row) != _S1_SLOT_ROW_KEYS:
            raise ValueError("S1 persisted manifest row fields differ from the schema")
        expected_row = {
            "slot": _s1_slot_name(panel, seed_slot, learned_arm),
            "relative_path": _s1_slot_relative_path(
                panel, seed_slot, learned_arm,
            ).as_posix(),
            "panel": panel,
            "test_seed_slot": seed_slot,
            "test_seed": S1_TEST_SEEDS[seed_slot],
            "learned_arm": learned_arm,
            "namespace": S1_TEST_NAMESPACE,
            "request": S1_TEST_REQUEST,
            "checkpoint_shape_schema": S1_CHECKPOINT_SHAPE_SCHEMA,
            "checkpoint_shape_training_batches": TRAINING_BATCHES,
            "fixture_kind": _S1_FIXTURE_KIND,
            "fixture_completed_training_batches": 0,
            "registered_training_executed": False,
            "registered_evaluation_executed": False,
            "dtype": "torch.float32",
            "question_relevant_output": False,
            "partial_result": False,
            "complete_r03_package": False,
            "scientific_final_checkpoint": False,
            "promotable": False,
        }
        if any(row.get(name) != expected for name, expected in expected_row.items()):
            raise ValueError("S1 persisted manifest row coordinate/activity mismatch")
        state_sha256 = _require_lower_sha256(
            row.get("state_sha256"), "S1 persisted slot state_sha256",
        )
        artifact_sha256 = _require_lower_sha256(
            row.get("artifact_sha256"), "S1 persisted slot artifact_sha256",
        )
        state_bytes = row.get("state_bytes")
        artifact_bytes = row.get("artifact_bytes")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in (state_bytes, artifact_bytes)
        ):
            raise ValueError("S1 persisted slot byte sizes must be positive integers")
        loaded_state_sha256, loaded_state_bytes = load_s1_test_slot_cold(
            root / str(row["relative_path"]),
            namespace=S1_TEST_NAMESPACE,
            request=S1_TEST_REQUEST,
            panel=panel,
            test_seed_slot=seed_slot,
            learned_arm=learned_arm,
            expected_artifact_sha256=artifact_sha256,
            expected_artifact_bytes=artifact_bytes,
        )
        if (
            loaded_state_sha256 != state_sha256
            or loaded_state_bytes != state_bytes
        ):
            raise ValueError("S1 persisted slot state identity differs from its bytes")


def save_s1_manifest_atomic(
    path: Path, manifest: Mapping[str, object], *, artifact_root: Path,
) -> str:
    validate_s1_structural_manifest(manifest, artifact_root=artifact_root)
    source = Path(path)
    if source.is_symlink():
        raise ValueError("S1 persisted manifest target must not be a symlink")
    target = source.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8") + b"\n"
    temporary = target.with_name(f".{target.name}.{os.getpid()}.pending")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return _file_sha256(target)


def load_s1_manifest_cold(
    path: Path, *, artifact_root: Path, expected_sha256: str,
) -> dict[str, object]:
    _require_lower_sha256(expected_sha256, "S1 persisted manifest sha256")
    source = Path(path)
    if source.is_symlink():
        raise ValueError("S1 persisted manifest must not be a symlink")
    target = source.resolve(strict=True)
    encoded = target.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != expected_sha256:
        raise ValueError("S1 persisted manifest digest differs from its bytes")
    try:
        payload = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("S1 persisted manifest JSON is malformed") from error
    if not isinstance(payload, dict):
        raise ValueError("S1 persisted manifest payload must be one object")
    validate_s1_structural_manifest(payload, artifact_root=artifact_root)
    return payload
