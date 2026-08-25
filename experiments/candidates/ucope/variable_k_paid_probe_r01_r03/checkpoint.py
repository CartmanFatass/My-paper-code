"""Atomic TEST-only model/optimizer/counter frontier for the retained S0 coupon."""

from __future__ import annotations

import hashlib
import io
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
    TEST_NAMESPACE,
    require_s1_test_request,
)
from .model import LearnerBundle
from .training import ReductionFrontier, SupportCounters


SCHEMA = "UCOPE_R01_R03_S0_TEST_CHECKPOINT_V1"
S1_FRONTIER_SCHEMA = "UCOPE_R01_R03_S1_TEST_WORK_UNIT_FRONTIER_V1"
S1_MANIFEST_SCHEMA = "UCOPE_R01_R03_S1_TEST_90_SLOT_MANIFEST_V1"


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
        digest = metadata[name]
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"S1 {name} must be one lowercase SHA-256")
    reduction = metadata["reduction_frontier"]
    if not isinstance(reduction, Mapping):
        raise ValueError("S1 reduction frontier is malformed")
    if set(reduction) != {"schema", "count", "ordered_values_sha256", "total_fp32_bits"}:
        raise ValueError("S1 reduction frontier fields differ from the frozen schema")
    if reduction.get("schema") != "UCOPE_R01_R03_S1_REDUCTION_FRONTIER_V1":
        raise ValueError("S1 reduction frontier identity mismatch")
    if not isinstance(reduction.get("count"), int) or int(reduction["count"]) <= 0:
        raise ValueError("S1 reduction frontier count must be positive")
    reduction_digest = reduction.get("ordered_values_sha256")
    if not isinstance(reduction_digest, str) or len(reduction_digest) != 64:
        raise ValueError("S1 reduction frontier digest is malformed")
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


def expected_s1_manifest_slots() -> tuple[str, ...]:
    return tuple(
        f"panel{panel}:test_seed_slot{seed_slot}:learned_arm{arm}"
        for panel in range(3)
        for seed_slot in range(10)
        for arm in range(3)
    )


def build_s1_structural_manifest(
    slot_state_sha256: Mapping[str, str], *, namespace: str, request: str,
) -> dict[str, object]:
    require_s1_test_request(namespace, S1_TEST_SEEDS[0], request)
    expected = expected_s1_manifest_slots()
    if set(slot_state_sha256) != set(expected) or len(slot_state_sha256) != FINAL_CHECKPOINT_SLOT_COUNT:
        raise ValueError("S1 structural manifest must contain exactly 90 unique slots")
    rows: list[dict[str, object]] = []
    for slot in expected:
        digest = slot_state_sha256[slot]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("S1 slot state identity must be one lowercase SHA-256")
        panel = int(slot[5])
        seed_slot = int(slot.split("test_seed_slot", 1)[1].split(":", 1)[0])
        arm = int(slot.rsplit("learned_arm", 1)[1])
        rows.append(
            {
                "slot": slot,
                "panel": panel,
                "test_seed_slot": seed_slot,
                "test_seed": S1_TEST_SEEDS[seed_slot],
                "learned_arm": arm,
                "synthetic_state_sha256": digest,
            }
        )
    manifest = {
        "schema": S1_MANIFEST_SCHEMA,
        "object_revision": OBJECT_REVISION,
        "component": COMPONENT,
        "namespace": S1_TEST_NAMESPACE,
        "request": S1_TEST_REQUEST,
        "structural_slots_complete": True,
        "slot_count": FINAL_CHECKPOINT_SLOT_COUNT,
        "question_relevant": False,
        "partial_result": False,
        "complete_r03_package": False,
        "slots": rows,
    }
    validate_s1_structural_manifest(manifest)
    return manifest


def validate_s1_structural_manifest(manifest: Mapping[str, object]) -> None:
    if manifest.get("schema") != S1_MANIFEST_SCHEMA or manifest.get("object_revision") != OBJECT_REVISION:
        raise ValueError("S1 structural manifest identity mismatch")
    if manifest.get("component") != COMPONENT or manifest.get("namespace") != S1_TEST_NAMESPACE:
        raise ValueError("S1 structural manifest component/namespace mismatch")
    if manifest.get("request") != S1_TEST_REQUEST:
        raise ValueError("S1 structural manifest request mismatch")
    if manifest.get("structural_slots_complete") is not True or manifest.get("slot_count") != FINAL_CHECKPOINT_SLOT_COUNT:
        raise ValueError("S1 structural manifest is incomplete")
    if any(manifest.get(name) is not False for name in ("question_relevant", "partial_result", "complete_r03_package")):
        raise ValueError("S1 structural manifest crossed the result firewall")
    rows = manifest.get("slots")
    if not isinstance(rows, list) or len(rows) != FINAL_CHECKPOINT_SLOT_COUNT:
        raise ValueError("S1 structural manifest slot list is incomplete")
    observed = {str(row.get("slot")) for row in rows if isinstance(row, Mapping)}
    if observed != set(expected_s1_manifest_slots()) or len(observed) != FINAL_CHECKPOINT_SLOT_COUNT:
        raise ValueError("S1 structural manifest slots are not the exact unique cross-product")
    expected_keys = {
        "slot", "panel", "test_seed_slot", "test_seed", "learned_arm",
        "synthetic_state_sha256",
    }
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != expected_keys:
            raise ValueError("S1 structural manifest row fields differ from the frozen schema")
        slot = str(row["slot"])
        panel = int(slot[5])
        seed_slot = int(slot.split("test_seed_slot", 1)[1].split(":", 1)[0])
        arm = int(slot.rsplit("learned_arm", 1)[1])
        if row["panel"] != panel or row["test_seed_slot"] != seed_slot:
            raise ValueError("S1 structural manifest panel/seed-slot identity mismatch")
        if row["test_seed"] != S1_TEST_SEEDS[seed_slot] or row["learned_arm"] != arm:
            raise ValueError("S1 structural manifest TEST seed/arm identity mismatch")
        digest = row["synthetic_state_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("S1 structural manifest state digest is malformed")
