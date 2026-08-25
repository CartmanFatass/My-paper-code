"""Canonical blinded storage for the exact HEADLAND-90 full panel.

Cell packets are private production staging objects, never result packets.  A
packet contains exact counts and conformance ledgers for one controller and
replicate, but no selector conclusion or cross-controller contrast.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct

from .config import CARD_REVISION, HOST_ID


CELL_SCHEMA = "ONLGR-HEADLAND90-R03-BLINDED-CELL-v2"
TRACE_SCHEMA = "ONLGR-HEADLAND90-R03-RETAINED-TRACE-v1"
OPPORTUNITY_LEDGER_FORMAT = "ONLGR-H90-OPP-v2-BBBHBQ"
CROSS_LEDGER_FORMAT = "ONLGR-H90-CROSS-v1-BBBh"
MAX_CELL_BYTES = 32 * 1024
CAL_REPLICATES = 48
HOLD_REPLICATES = 128
BLOCKS_PER_REPLICATE = 20
CONTROLLER_REPLICATE_TICKS = 20 * (48 + 144)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CONTROLLER_ID = re.compile(r"theta-(\d{3})")
_FAILURE_KEYS = (
    "terrain_penetrations",
    "geofence_exits",
    "separation_breaches",
    "no_safe_control",
    "no_planner_solution",
    "battery_exhaustions",
    "numerical_faults",
)
_BINDING_KEYS = (
    "preactivity_freeze_sha256",
    "coordinate_binding_sha256",
    "lease_scope_sha256",
    "backend_receipt_sha256",
    "source_set_sha256",
    "config_sha256",
    "schema_sha256",
)


class SerializationError(ValueError):
    pass


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SerializationError("payload must contain finite canonical JSON values") from exc


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def document_sha256(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise SerializationError(f"{label} must be lowercase SHA-256")
    return value


def _controller_ordinal(controller_id: str) -> int:
    match = _CONTROLLER_ID.fullmatch(controller_id)
    if match is None or int(match.group(1)) not in range(192):
        raise SerializationError("physical controller id must be theta-000,...,theta-191")
    return int(match.group(1))


@dataclass(frozen=True, order=True)
class CellIdentity:
    split: str
    physical_controller_id: str
    replicate: int

    def __post_init__(self) -> None:
        if self.split not in ("CAL", "HOLD"):
            raise SerializationError("cell split must be CAL or HOLD")
        _controller_ordinal(self.physical_controller_id)
        limit = CAL_REPLICATES if self.split == "CAL" else HOLD_REPLICATES
        if isinstance(self.replicate, bool) or not isinstance(self.replicate, int):
            raise TypeError("cell replicate must be an integer")
        if self.replicate not in range(limit):
            raise SerializationError("cell replicate is outside its exact split")

    def as_dict(self) -> dict[str, object]:
        return {
            "split": self.split,
            "physical_controller_id": self.physical_controller_id,
            "replicate": self.replicate,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CellIdentity":
        if set(value) != {"split", "physical_controller_id", "replicate"}:
            raise SerializationError("cell identity schema differs")
        return cls(
            str(value["split"]),
            str(value["physical_controller_id"]),
            value["replicate"],  # type: ignore[arg-type]
        )


def expected_encounter_order(replicate: int, block: int) -> tuple[str, str]:
    return ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")


def expected_template(replicate: int, block: int) -> int:
    return (replicate + 3 * block) % 4


def _validate_encounter(value: Mapping[str, object], *, route_class: str) -> dict[str, object]:
    keys = {
        "valid_ticks",
        "scored_ticks",
        "tracking_valid_ticks",
        "packet_valid_ticks",
        "raw_link_success_tr",
        "raw_link_success_rb",
        "blackout_ticks",
        "lockout_ticks",
        "voluntary_updates",
        "voluntary_keeps",
        "opportunity_rows",
        "safety_overrides",
        "override_causes",
        "failures",
        "tracker_energy_final",
        "relay_energy_final",
        "update_energy_joules_per_uav",
    }
    if set(value) != keys:
        raise SerializationError(f"{route_class} encounter summary schema differs")
    scored = 32 if route_class == "SHORT" else 128
    physical = scored + 16
    integer_keys = keys - {"failures", "override_causes", "tracker_energy_final", "relay_energy_final"}
    for key in integer_keys:
        item = value[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise SerializationError(f"{route_class}.{key} must be a nonnegative integer")
    if value["scored_ticks"] != scored or value["valid_ticks"] > scored:
        raise SerializationError(f"{route_class} scored/valid counts differ from the card")
    if value["safety_overrides"] > physical:
        raise SerializationError(f"{route_class} override count exceeds physical intervals")
    for key in (
        "tracking_valid_ticks", "packet_valid_ticks", "raw_link_success_tr",
        "raw_link_success_rb", "blackout_ticks", "lockout_ticks",
    ):
        if value[key] > physical:
            raise SerializationError(f"{route_class}.{key} exceeds physical intervals")
    causes = value["override_causes"]
    if not isinstance(causes, Mapping) or set(causes) != {"terrain","geofence","separation"}:
        raise SerializationError(f"{route_class} override-cause ledger schema differs")
    for key, item in causes.items():
        if isinstance(item, bool) or not isinstance(item, int) or not 0 <= item <= value["safety_overrides"]:
            raise SerializationError(f"{route_class}.override_causes.{key} is invalid")
    if sum(causes.values()) < value["safety_overrides"]:
        raise SerializationError(f"{route_class} override causes do not cover every override")
    if value["voluntary_updates"] + value["voluntary_keeps"] != value["opportunity_rows"]:
        raise SerializationError(f"{route_class} voluntary action accounting is not exhaustive")
    if value["update_energy_joules_per_uav"] != 200 * (1 + value["voluntary_updates"]):
        raise SerializationError(f"{route_class} update-energy ledger differs from BOOT plus updates")
    for key, maximum in (("tracker_energy_final", 40_000.0), ("relay_energy_final", 45_000.0)):
        item = value[key]
        if not isinstance(item, float) or not math.isfinite(item) or not 0.0 <= item <= maximum:
            raise SerializationError(f"{route_class}.{key} is outside its battery ledger")
    failures = value["failures"]
    if not isinstance(failures, Mapping) or set(failures) != set(_FAILURE_KEYS):
        raise SerializationError(f"{route_class} hard-failure ledger schema differs")
    for key in _FAILURE_KEYS:
        item = failures[key]
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise SerializationError(f"{route_class}.failures.{key} must be nonnegative")
    return json.loads(canonical_json_bytes(dict(value)))


def validate_block_summary(value: Mapping[str, object], *, replicate: int) -> dict[str, object]:
    if set(value) != {"block", "template", "encounter_order", "SHORT", "LONG"}:
        raise SerializationError("block summary schema differs")
    block = value["block"]
    if isinstance(block, bool) or not isinstance(block, int) or block not in range(20):
        raise SerializationError("block index must be 0,...,19")
    if value["template"] != expected_template(replicate, block):
        raise SerializationError("block template differs from the frozen coordinate identity")
    if tuple(value["encounter_order"]) != expected_encounter_order(replicate, block):  # type: ignore[arg-type]
        raise SerializationError("block encounter order differs from the frozen balance")
    result: dict[str, object] = {
        "block": block,
        "template": value["template"],
        "encounter_order": list(expected_encounter_order(replicate, block)),
    }
    for route_class in ("SHORT", "LONG"):
        encounter = value[route_class]
        if not isinstance(encounter, Mapping):
            raise SerializationError(f"{route_class} summary must be an object")
        result[route_class] = _validate_encounter(encounter, route_class=route_class)
    return result


def _aggregate(blocks: Sequence[Mapping[str, object]]) -> dict[str, object]:
    totals = {
        "short_valid_ticks": 0,
        "long_valid_ticks": 0,
        "voluntary_updates": {"SHORT": 0, "LONG": 0},
        "voluntary_keeps": {"SHORT": 0, "LONG": 0},
        "opportunity_rows": {"SHORT": 0, "LONG": 0},
        "safety_overrides": 0,
        "override_causes": {"terrain":0,"geofence":0,"separation":0},
        "failures": {key: 0 for key in _FAILURE_KEYS},
        "physical_ticks": CONTROLLER_REPLICATE_TICKS,
    }
    for block in blocks:
        for route_class in ("SHORT", "LONG"):
            row = block[route_class]  # type: ignore[assignment]
            assert isinstance(row, Mapping)
            if route_class == "SHORT":
                totals["short_valid_ticks"] += row["valid_ticks"]  # type: ignore[operator]
            else:
                totals["long_valid_ticks"] += row["valid_ticks"]  # type: ignore[operator]
            for key in ("voluntary_updates", "voluntary_keeps", "opportunity_rows"):
                totals[key][route_class] += row[key]  # type: ignore[index,operator]
            totals["safety_overrides"] += row["safety_overrides"]  # type: ignore[operator]
            for key in totals["override_causes"]:
                totals["override_causes"][key] += row["override_causes"][key]  # type: ignore[index,operator]
            for key in _FAILURE_KEYS:
                totals["failures"][key] += row["failures"][key]  # type: ignore[index,operator]
    return totals


def build_cell_packet(
    identity: CellIdentity,
    *,
    bindings: Mapping[str, str],
    blocks: Sequence[Mapping[str, object]],
    trace_retained: bool,
    opportunity_ledger: Mapping[str, object] | None = None,
    cross_eval_ledger: Mapping[str, object] | None = None,
) -> dict[str, object]:
    if set(bindings) != set(_BINDING_KEYS):
        raise SerializationError("cell binding schema differs")
    checked_bindings = {key: _require_sha256(bindings[key], key) for key in _BINDING_KEYS}
    if len(blocks) != BLOCKS_PER_REPLICATE:
        raise SerializationError("cell requires exactly 20 complete blocks")
    checked = tuple(validate_block_summary(row, replicate=identity.replicate) for row in blocks)
    if tuple(row["block"] for row in checked) != tuple(range(20)):
        raise SerializationError("cell blocks must appear exactly once in block order")
    if not isinstance(trace_retained, bool):
        raise TypeError("trace_retained must be boolean")
    packet = {
        "schema": CELL_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "blinded": True,
        "partial_interpretation_allowed": False,
        "cell": identity.as_dict(),
        "bindings": checked_bindings,
        "blocks": list(checked),
        "aggregate": _aggregate(checked),
        "trace_retained": trace_retained,
        "opportunity_ledger": dict(opportunity_ledger) if opportunity_ledger is not None else None,
        "cross_eval_ledger": dict(cross_eval_ledger) if cross_eval_ledger is not None else None,
        "complete": True,
    }
    encoded = canonical_json_bytes(packet)
    if len(encoded) > MAX_CELL_BYTES:
        raise SerializationError("cell summary exceeds the frozen 32 KiB allocation")
    return packet


def validate_cell_packet(value: Mapping[str, object]) -> CellIdentity:
    keys = {
        "schema", "card_revision", "host", "blinded", "partial_interpretation_allowed",
        "cell", "bindings", "blocks", "aggregate", "trace_retained", "opportunity_ledger",
        "cross_eval_ledger", "complete",
    }
    if set(value) != keys:
        raise SerializationError("cell packet top-level schema differs")
    fixed = {
        "schema": CELL_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "blinded": True,
        "partial_interpretation_allowed": False,
        "complete": True,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise SerializationError("cell packet frozen identity differs")
    if not isinstance(value["cell"], Mapping):
        raise SerializationError("cell identity must be an object")
    identity = CellIdentity.from_dict(value["cell"])
    if not isinstance(value["bindings"], Mapping) or set(value["bindings"]) != set(_BINDING_KEYS):
        raise SerializationError("cell binding schema differs")
    for key in _BINDING_KEYS:
        _require_sha256(value["bindings"][key], key)
    blocks = value["blocks"]
    if not isinstance(blocks, list) or len(blocks) != 20:
        raise SerializationError("cell must contain exactly 20 block summaries")
    checked = tuple(validate_block_summary(row, replicate=identity.replicate) for row in blocks)
    if tuple(row["block"] for row in checked) != tuple(range(20)):
        raise SerializationError("cell blocks are absent, duplicated, or reordered")
    if value["aggregate"] != _aggregate(checked):
        raise SerializationError("cell aggregate differs from exact block counts")
    if not isinstance(value["trace_retained"], bool):
        raise SerializationError("cell trace-retention flag must be boolean")
    _validate_sidecar_ref(value["opportunity_ledger"], OPPORTUNITY_LEDGER_FORMAT, "opportunity")
    _validate_sidecar_ref(value["cross_eval_ledger"], CROSS_LEDGER_FORMAT, "cross-evaluation")
    if len(canonical_json_bytes(value)) > MAX_CELL_BYTES:
        raise SerializationError("cell summary exceeds the frozen 32 KiB allocation")
    return identity


def _validate_sidecar_ref(value: object, expected_format: str, label: str) -> None:
    if value is None:
        return
    if not isinstance(value, Mapping) or set(value) != {"format", "row_count", "sha256"}:
        raise SerializationError(f"{label} sidecar reference schema differs")
    if value["format"] != expected_format:
        raise SerializationError(f"{label} sidecar format differs")
    if isinstance(value["row_count"], bool) or not isinstance(value["row_count"], int) or value["row_count"] < 0:
        raise SerializationError(f"{label} sidecar row count is invalid")
    _require_sha256(value["sha256"], f"{label} sidecar")


def sidecar_path(root: Path, identity: CellIdentity, kind: str) -> Path:
    if kind not in ("opportunity", "cross"):
        raise ValueError("sidecar kind must be opportunity or cross")
    return root / "private-sidecars" / identity.split / identity.physical_controller_id / (
        f"replicate-{identity.replicate:03d}.{kind}.bin"
    )


def atomic_write_bytes(path: Path, payload: bytes, *, authorized_root: Path) -> Path:
    destination, root = Path(path), Path(authorized_root)
    _require_under(destination, root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() == payload:
            return destination
        raise FileExistsError(f"write-once binary artifact differs: {destination}")
    temporary = destination.with_name(f".{destination.name}.pending")
    if temporary.exists():
        if temporary.read_bytes() != payload:
            raise FileExistsError(f"same-coordinate binary recovery differs: {temporary}")
        temporary.unlink()
    with temporary.open("xb") as stream:
        stream.write(payload); stream.flush(); os.fsync(stream.fileno())
    try:
        os.link(temporary, destination)
    finally:
        if temporary.exists(): temporary.unlink()
    return destination


def encode_opportunity_rows(rows: Sequence[tuple[int, int, int, int, int, int]]) -> bytes:
    return b"H90O2\0" + b"".join(struct.pack(">BBBHBQ", *row) for row in rows)


def decode_opportunity_rows(payload: bytes) -> tuple[tuple[int, int, int, int, int, int], ...]:
    if not payload.startswith(b"H90O2\0") or (len(payload) - 6) % 14:
        raise SerializationError("opportunity sidecar framing differs")
    return tuple(struct.unpack(">BBBHBQ", payload[index:index + 14]) for index in range(6, len(payload), 14))


def encode_cross_rows(rows: Sequence[tuple[int, int, int, int]]) -> bytes:
    return b"H90X1\0" + b"".join(struct.pack(">BBBh", *row) for row in rows)


def decode_cross_rows(payload: bytes) -> tuple[tuple[int, int, int, int], ...]:
    if not payload.startswith(b"H90X1\0") or (len(payload) - 6) % 5:
        raise SerializationError("cross sidecar framing differs")
    return tuple(struct.unpack(">BBBh", payload[index:index + 5]) for index in range(6, len(payload), 5))


def cell_path(root: Path, identity: CellIdentity) -> Path:
    return (
        Path(root)
        / "private-cells"
        / identity.split
        / identity.physical_controller_id
        / f"replicate-{identity.replicate:03d}.json"
    )


def _require_under(path: Path, root: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise SerializationError("artifact path escapes its authorized root") from exc


def atomic_write_once(path: Path, value: object, *, authorized_root: Path) -> Path:
    destination = Path(path)
    root = Path(authorized_root)
    _require_under(destination, root)
    encoded = canonical_json_bytes(value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() == encoded:
            return destination
        raise FileExistsError(f"write-once artifact differs: {destination}")
    temporary = destination.with_name(f".{destination.name}.pending")
    if temporary.exists():
        if temporary.read_bytes() != encoded:
            raise FileExistsError(f"same-coordinate recovery payload differs: {temporary}")
        temporary.unlink()
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, destination)
    except FileExistsError:
        if destination.read_bytes() != encoded:
            raise FileExistsError(f"concurrent write-once artifact differs: {destination}")
    finally:
        if temporary.exists():
            temporary.unlink()
    return destination


def write_cell_packet(root: Path, packet: Mapping[str, object]) -> Path:
    identity = validate_cell_packet(packet)
    return atomic_write_once(cell_path(root, identity), packet, authorized_root=root)


def read_cell_packet(root: Path, identity: CellIdentity) -> dict[str, object]:
    path = cell_path(root, identity)
    encoded = path.read_bytes()
    try:
        value = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SerializationError("cell is not valid UTF-8 JSON") from exc
    if canonical_json_bytes(value) != encoded:
        raise SerializationError("cell is not canonical JSON plus LF")
    if validate_cell_packet(value) != identity:
        raise SerializationError("cell path and retained identity differ")
    return value
