"""Create-only TEST generations for source-factored transaction scaffolding."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import tempfile
from typing import Mapping

from .production_backend import ProductionBackendError, decode_promotion_source_receipt
from .production_source_factored_contract import ClaimCoordinate, ResourceCeilings


class SourceFactoredDataPlaneError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


_PAYLOAD_FILES = ("native_snapshot.bin", "rollout_welford.bin", "checkpoint.bin", "rng_frontier.bin")
_RECEIPT_FILES = {
    "RETAIN": "receipt-retain.bin", "TRANSFER_COPY": "receipt-transfer-copy.bin",
    "TRANSFER_SHADOW": "receipt-transfer-shadow.bin",
}
_MANIFEST_KEYS = {
    "schema", "coordinate", "sealed", "test_only", "payload_hex", "receipt_hex",
    "receipt_bytes", "receipt_schema_version", "branch_receipts_direct", "resource_observation",
    "complete_result_firewall", "result_values_exposed", "question_relevant_output",
}
_FINAL_FILES = {*_PAYLOAD_FILES, *_RECEIPT_FILES.values(), "manifest.json"}


def _install_no_replace(root: Path, name: str, payload: bytes) -> None:
    """Install one complete request-bound file atomically without coauthoring."""

    expected = bytes(payload); target = root / name
    if target.exists():
        if not target.is_file() or target.read_bytes() != expected:
            raise SourceFactoredDataPlaneError("staged generation byte mismatch")
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{root.name}.{name}.", suffix=".request-private", dir=root.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(expected); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError:
            if not target.is_file() or target.read_bytes() != expected:
                raise SourceFactoredDataPlaneError("staged no-replace installation differs")
    finally:
        temporary.unlink(missing_ok=True)


def _load_canonical_json(raw: bytes) -> Mapping[str, object]:
    def reject_duplicates(rows: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in rows:
            if key in result:
                raise SourceFactoredDataPlaneError("canonical manifest has duplicate keys")
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceFactoredDataPlaneError("canonical manifest bytes differ") from error
    try:
        canonical = _canonical(value)
    except (TypeError, ValueError) as error:
        raise SourceFactoredDataPlaneError("canonical manifest bytes differ") from error
    if not isinstance(value, dict) or canonical != raw:
        raise SourceFactoredDataPlaneError("canonical manifest bytes differ")
    return value


def _decode_lower_hex(value: object, label: str) -> bytes:
    if (not isinstance(value, str) or value != value.lower() or len(value) % 2 or
            any(character not in "0123456789abcdef" for character in value)):
        raise SourceFactoredDataPlaneError(f"canonical lowercase {label} differs")
    try:
        return bytes.fromhex(value)
    except ValueError as error:
        raise SourceFactoredDataPlaneError(f"canonical lowercase {label} differs") from error


def _validate_direct_receipts(receipts: Mapping[str, bytes]) -> None:
    expected_modes = {"RETAIN": 0, "TRANSFER_COPY": 1, "TRANSFER_SHADOW": 2}
    try:
        decoded = {name: decode_promotion_source_receipt(receipts[name]) for name in expected_modes}
    except (KeyError, ProductionBackendError) as error:
        raise SourceFactoredDataPlaneError("direct branch receipt schema differs") from error
    common = ("owner_before", "tick", "service_epoch_after", "next_payload_sequence", "k_epoch", "intent_origin_tick")
    if any(decoded[name]["source_mode"] != mode for name, mode in expected_modes.items()):
        raise SourceFactoredDataPlaneError("direct branch receipt source mode differs")
    if any(decoded[name][field] != decoded["RETAIN"][field] for name in expected_modes for field in common):
        raise SourceFactoredDataPlaneError("direct branch receipt transaction tuple differs")
    before = decoded["RETAIN"]["owner_before"]
    if before not in (0, 1):
        raise SourceFactoredDataPlaneError("direct branch receipt owner differs")
    recipient = 1 - before
    shapes = {
        "RETAIN": (0, 1, before, before),
        "TRANSFER_COPY": (1, 0, recipient, recipient),
        "TRANSFER_SHADOW": (1, 0, recipient, recipient),
    }
    for name, (cas, retained, owner_after, actuator_after) in shapes.items():
        row = decoded[name]
        if (row["cas_applied"], row["retained_by_design"], row["owner_after"], row["actuator_after"]) != (cas, retained, owner_after, actuator_after):
            raise SourceFactoredDataPlaneError("direct branch receipt semantics differ")


def validate_resource_observation(value: Mapping[str, object]) -> Mapping[str, object]:
    required = ("workers", "cpu_cores", "torch_threads", "gpu", "cpu_hours", "wall_hours",
                "rss_gib", "scratch_gib", "durable_gib", "io_gib")
    if set(value) != set(required):
        raise SourceFactoredDataPlaneError("resource observation schema differs")
    ceilings = ResourceCeilings()
    integers = ("workers", "cpu_cores", "torch_threads", "gpu")
    if any(type(value[name]) is not int for name in integers):
        raise SourceFactoredDataPlaneError("integer resource observation type differs")
    continuous = tuple(name for name in required if name not in integers)
    if any(isinstance(value[name], bool) or not isinstance(value[name], (int, float)) for name in continuous):
        raise SourceFactoredDataPlaneError("numeric resource observation type differs")
    numeric = {name: float(value[name]) for name in required}
    if any(not math.isfinite(numeric[name]) for name in required):
        raise SourceFactoredDataPlaneError("resource observation is not finite")
    observed = {name: int(numeric[name]) if name in integers else numeric[name] for name in required}
    limits = ceilings.__dict__
    if any(observed[name] < 0 for name in required):
        raise SourceFactoredDataPlaneError("resource observation is negative")
    if any(observed[name] > limits[name] for name in required):
        raise SourceFactoredDataPlaneError("resource observation exceeds frozen ceiling")
    if observed["torch_threads"] != 1 or observed["gpu"] != 0:
        raise SourceFactoredDataPlaneError("Torch/GPU observation differs")
    if observed["workers"] < 1 or observed["cpu_cores"] < 1:
        raise SourceFactoredDataPlaneError("worker/core observation domain differs")
    return observed


class TestOnlySourceFactoredDataPlane:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _coordinate_root(self, coordinate: ClaimCoordinate) -> Path:
        return (
            self.root / f"block-{coordinate.block:02d}" / coordinate.package /
            coordinate.schedule / f"speed-{coordinate.speed}" / f"slot-{coordinate.slot:02d}"
        )

    def _staging_root(self, coordinate: ClaimCoordinate) -> Path:
        target = self._coordinate_root(coordinate)
        return target.with_name(f".{target.name}.source-factored-staging")

    def create_generation(
        self, *, coordinate: ClaimCoordinate, native_snapshot: bytes, rollout_welford: bytes,
        checkpoint: bytes, rng_frontier: bytes, receipts: Mapping[str, bytes],
        resource_observation: Mapping[str, object],
        _test_fail_after_staged_files: int | None = None,
    ) -> Mapping[str, object]:
        payloads = {
            "native_snapshot.bin": bytes(native_snapshot), "rollout_welford.bin": bytes(rollout_welford),
            "checkpoint.bin": bytes(checkpoint), "rng_frontier.bin": bytes(rng_frontier),
        }
        if any(not payload for payload in payloads.values()):
            raise SourceFactoredDataPlaneError("generation inventory contains an empty payload")
        if set(receipts) != {"RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW"}:
            raise SourceFactoredDataPlaneError("transaction receipt inventory differs")
        receipt_rows = {name: bytes(receipts[name]) for name in _RECEIPT_FILES}
        if any(len(row) != 24 for row in receipt_rows.values()):
            raise SourceFactoredDataPlaneError("direct branch receipt size differs")
        _validate_direct_receipts(receipt_rows)
        resources = validate_resource_observation(resource_observation)
        manifest = {
            "schema": "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_TEST_GENERATION_V2",
            "coordinate": coordinate.key(), "sealed": True, "test_only": True,
            "payload_hex": {name: payload.hex() for name, payload in payloads.items()},
            "receipt_hex": {mode: payload.hex() for mode, payload in receipt_rows.items()},
            "receipt_bytes": 24, "receipt_schema_version": 1, "branch_receipts_direct": True,
            "resource_observation": resources, "complete_result_firewall": True,
            "result_values_exposed": False, "question_relevant_output": False,
        }
        target = self._coordinate_root(coordinate); staging = self._staging_root(coordinate)
        if target.exists():
            raise SourceFactoredDataPlaneError("sealed coordinate cannot be forked again")
        if staging.exists() and not staging.is_dir():
            raise SourceFactoredDataPlaneError("staged generation path differs")
        staging.mkdir(parents=True, exist_ok=True)
        manifest_bytes = _canonical(manifest)
        _install_no_replace(staging, "manifest.json", manifest_bytes)
        if (staging / "manifest.json").read_bytes() != manifest_bytes:
            raise SourceFactoredDataPlaneError("retry request bytes differ")
        staged_rows = [(name, payloads[name]) for name in _PAYLOAD_FILES]
        staged_rows.extend((_RECEIPT_FILES[mode], receipt_rows[mode]) for mode in _RECEIPT_FILES)
        if _test_fail_after_staged_files is not None and not 1 <= _test_fail_after_staged_files <= len(staged_rows):
            raise SourceFactoredDataPlaneError("TEST failure-injection frontier differs")
        for index, (name, payload) in enumerate(staged_rows, start=1):
            _install_no_replace(staging, name, payload)
            if _test_fail_after_staged_files == index:
                raise SourceFactoredDataPlaneError("injected staged-generation interruption")
        if {path.name for path in staging.iterdir()} != _FINAL_FILES:
            raise SourceFactoredDataPlaneError("staged generation inventory differs")
        try:
            staging.rename(target)
        except FileExistsError as error:
            raise SourceFactoredDataPlaneError("sealed coordinate cannot be forked again") from error
        return self.resume_exact(coordinate)

    def resume_exact(self, coordinate: ClaimCoordinate) -> Mapping[str, object]:
        target = self._coordinate_root(coordinate); manifest_path = target / "manifest.json"
        if not manifest_path.is_file():
            raise SourceFactoredDataPlaneError("generation is incomplete and cannot expose scaffold accounting")
        if {path.name for path in target.iterdir()} != _FINAL_FILES:
            raise SourceFactoredDataPlaneError("sealed coordinate file inventory differs")
        manifest = _load_canonical_json(manifest_path.read_bytes())
        if (
            set(manifest) != _MANIFEST_KEYS or
            set(manifest.get("payload_hex", {})) != set(_PAYLOAD_FILES) or
            set(manifest.get("receipt_hex", {})) != set(_RECEIPT_FILES) or
            manifest.get("schema") != "DISH_BLOCK_CERTIFICATE_PREVALENCE_R02_TEST_GENERATION_V2" or
            manifest.get("coordinate") != coordinate.key() or manifest.get("sealed") is not True or
            manifest.get("test_only") is not True or manifest.get("complete_result_firewall") is not True or
            manifest.get("receipt_bytes") != 24 or manifest.get("receipt_schema_version") != 1 or
            manifest.get("branch_receipts_direct") is not True or
            manifest.get("result_values_exposed") is not False or
            manifest.get("question_relevant_output") is not False
        ):
            raise SourceFactoredDataPlaneError("sealed coordinate direct binding differs")
        for name in _PAYLOAD_FILES:
            expected = _decode_lower_hex(manifest["payload_hex"][name], "payload hex")
            path = target / name
            if not path.is_file() or path.read_bytes() != expected:
                raise SourceFactoredDataPlaneError("cold/crash resume payload bytes differ")
        rows = []
        for mode, name in _RECEIPT_FILES.items():
            expected = _decode_lower_hex(manifest["receipt_hex"][mode], "receipt hex")
            path = target / name
            if not path.is_file() or path.read_bytes() != expected:
                raise SourceFactoredDataPlaneError("cold/crash resume receipt bytes differ")
            rows.append(path.read_bytes())
        if any(len(row) != 24 for row in rows):
            raise SourceFactoredDataPlaneError("resumed receipt size differs")
        _validate_direct_receipts(dict(zip(_RECEIPT_FILES, rows)))
        resources = validate_resource_observation(manifest.get("resource_observation", {}))
        return {
            "schema": manifest["schema"], "coordinate": manifest["coordinate"],
            "sealed": True, "test_only": True,
            "payload_hex": {name: bytes.fromhex(manifest["payload_hex"][name]).hex() for name in _PAYLOAD_FILES},
            "receipt_hex": {name: bytes.fromhex(manifest["receipt_hex"][name]).hex() for name in _RECEIPT_FILES},
            "receipt_bytes": 24, "receipt_schema_version": 1, "branch_receipts_direct": True,
            "resource_observation": resources, "complete_result_firewall": True,
            "result_values_exposed": False, "question_relevant_output": False,
        }

    def complete_result(self, coordinate: ClaimCoordinate) -> Mapping[str, object]:
        self.resume_exact(coordinate)
        raise SourceFactoredDataPlaneError("complete-result firewall forbids question-relevant output")


TestOnlySourceFactoredDataPlane.__test__ = False


__all__ = [
    "SourceFactoredDataPlaneError", "TestOnlySourceFactoredDataPlane", "validate_resource_observation",
]
