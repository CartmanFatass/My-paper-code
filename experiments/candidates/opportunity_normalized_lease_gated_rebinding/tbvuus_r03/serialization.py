"""Canonical prospective cell, sidecar, and commit contracts for TBVUUS r03.

The objects validated here are private blinded production records.  They do
not expose a result and are not themselves a scientific activity launcher.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
import struct

from .contracts import (
    ARMS,
    BINDING_KEYS,
    BLOCKS_PER_CONTROLLER_REPLICATE,
    CELL_COMMIT_SCHEMA,
    CELL_SCHEMA,
    ENCOUNTERS_PER_BLOCK,
    ENCOUNTERS_PER_CONTROLLER_REPLICATE,
    HARD_FAILURE_KEYS,
    HOST_ID,
    PANEL_COMMIT_SCHEMA,
    PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE,
    PRODUCTION_NAMESPACE,
    REPLICATES,
    ROAD_TRACK_ESTIMATE_PATCH,
    ROUTE_CLASSES,
    SCIENCE_REVISION,
    SCORED_TICKS_PER_CONTROLLER_REPLICATE,
    SIDECAR_SCHEMAS,
    STAGE,
    canonical_json_bytes,
)


_SHA256 = re.compile(r"[0-9a-f]{64}")
_PARTIAL_KEYS = frozenset(
    {
        "partial_result",
        "partial_results",
        "interim_result",
        "interim_results",
        "selected_cells",
        "best_attempt",
        "early_stop",
    }
)


class SerializationError(ValueError):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def document_sha256(value: object) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise SerializationError(f"{label} must be lowercase SHA-256")
    return value


def _nonnegative_int(value: object, label: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SerializationError(f"{label} must be a nonnegative integer")
    if maximum is not None and value > maximum:
        raise SerializationError(f"{label} exceeds its exact denominator")
    return value


def _finite_unit(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SerializationError(f"{label} must be a finite scalar")
    scalar = float(value)
    if not math.isfinite(scalar) or not 0.0 <= scalar <= 1.0:
        raise SerializationError(f"{label} must lie in [0,1]")
    return scalar


@dataclass(frozen=True, order=True)
class CellIdentity:
    arm: str
    replicate: int

    def __post_init__(self) -> None:
        if self.arm not in ARMS:
            raise SerializationError("cell arm differs from the exact four-arm domain")
        if (
            isinstance(self.replicate, bool)
            or not isinstance(self.replicate, int)
            or self.replicate not in range(REPLICATES)
        ):
            raise SerializationError("cell replicate must be 0,...,127")

    def as_dict(self) -> dict[str, object]:
        return {"arm": self.arm, "replicate": self.replicate}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CellIdentity":
        if set(value) != {"arm", "replicate"}:
            raise SerializationError("cell identity schema differs")
        return cls(str(value["arm"]), value["replicate"])  # type: ignore[arg-type]


def expected_encounter_order(replicate: int, block: int) -> tuple[str, str]:
    if replicate not in range(REPLICATES) or block not in range(BLOCKS_PER_CONTROLLER_REPLICATE):
        raise SerializationError("replicate or block is outside the frozen domain")
    return ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")


def expected_template(replicate: int, block: int) -> int:
    if replicate not in range(REPLICATES) or block not in range(BLOCKS_PER_CONTROLLER_REPLICATE):
        raise SerializationError("replicate or block is outside the frozen domain")
    return (replicate + 3 * block) % 4


def validate_sidecar_ref(kind: str, value: Mapping[str, object]) -> dict[str, object]:
    if kind not in SIDECAR_SCHEMAS:
        raise SerializationError("unknown TBVUUS sidecar kind")
    if set(value) != {"schema", "row_count", "sha256", "bytes"}:
        raise SerializationError(f"{kind} sidecar reference schema differs")
    expected_schema, expected_rows = SIDECAR_SCHEMAS[kind]
    if value["schema"] != expected_schema:
        raise SerializationError(f"{kind} sidecar schema differs")
    if value["row_count"] != expected_rows:
        raise SerializationError(f"{kind} sidecar row count differs")
    _require_sha256(value["sha256"], f"{kind} sidecar")
    _nonnegative_int(value["bytes"], f"{kind} sidecar bytes")
    return dict(value)


_AGGREGATE_KEYS = {
    "blocks",
    "encounters",
    "physical_ticks",
    "scored_ticks",
    "short_encounters",
    "long_encounters",
    "scheduled_t0_decisions",
    "action_shell_count",
    "road_fit_available_count",
    "effective_road_patch_count",
    "effective_road_patch_by_route",
    "valid_scored_ticks",
    "safety_overrides",
    "hard_failures",
    "mean_value",
    "tail_value",
    "tape_commitment_sha256",
    "tick_audit_valid",
    "road_fit_audit_valid",
    "arm_transition_audit_valid",
    "endpoint_audit_valid",
    "raw_conformant",
    "sham_valid",
    "road_fit_facts",
    "arm_transition_facts",
    "sham_validity_facts",
}

_ROAD_FIT_FACT_KEYS = {
    "every_encounter_audited",
    "availability_exact",
    "tie_order_exact",
    "selected_template_audited",
    "patch_formula_exact",
    "identity_fallback_exact",
    "no_future_or_hidden_input",
}
_ARM_TRANSITION_FACT_KEYS = {
    "scheduled_exact",
    "shell_exact",
    "energy_debit_exact",
    "blackout_exact",
    "lockout_exact",
    "buffer_clear_exact",
    "waypoints_unchanged",
    "planner_not_invoked",
    "later_keep_exact",
}
_SHAM_VALIDITY_FACT_KEYS = {
    "common_pre_action_state_equal",
    "common_tapes_equal",
    "estimator_bitwise_unchanged",
    "waypoints_bitwise_unchanged",
    "only_registered_shell_differences",
    "tickwise_q_not_greater_than_never",
    "post_blackout_equal_absent_battery_exhaustion",
}


def validate_cell_aggregate(identity: CellIdentity, value: Mapping[str, object]) -> dict[str, object]:
    if set(value) != _AGGREGATE_KEYS:
        raise SerializationError("cell aggregate schema differs")
    fixed = {
        "blocks": BLOCKS_PER_CONTROLLER_REPLICATE,
        "encounters": ENCOUNTERS_PER_CONTROLLER_REPLICATE,
        "physical_ticks": PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE,
        "scored_ticks": SCORED_TICKS_PER_CONTROLLER_REPLICATE,
        "short_encounters": BLOCKS_PER_CONTROLLER_REPLICATE,
        "long_encounters": BLOCKS_PER_CONTROLLER_REPLICATE,
        "scheduled_t0_decisions": ENCOUNTERS_PER_CONTROLLER_REPLICATE,
        "action_shell_count": (
            0 if identity.arm == ARMS[0] else ENCOUNTERS_PER_CONTROLLER_REPLICATE
        ),
    }
    for key, expected in fixed.items():
        if value[key] != expected:
            raise SerializationError(f"cell aggregate exact count differs: {key}")
    _nonnegative_int(
        value["road_fit_available_count"],
        "road-fit count",
        maximum=ENCOUNTERS_PER_CONTROLLER_REPLICATE,
    )
    effective = _nonnegative_int(
        value["effective_road_patch_count"],
        "effective road-patch count",
        maximum=ENCOUNTERS_PER_CONTROLLER_REPLICATE,
    )
    if effective > value["road_fit_available_count"]:
        raise SerializationError("effective payload count exceeds available road fits")
    by_route = value["effective_road_patch_by_route"]
    if not isinstance(by_route, Mapping) or set(by_route) != set(ROUTE_CLASSES):
        raise SerializationError("effective payload route diagnostic schema differs")
    for route in ROUTE_CLASSES:
        _nonnegative_int(by_route[route], f"effective payload {route}", maximum=20)
    if sum(int(by_route[route]) for route in ROUTE_CLASSES) != effective:
        raise SerializationError("effective payload route diagnostics do not sum to total")
    _nonnegative_int(
        value["valid_scored_ticks"],
        "valid scored ticks",
        maximum=SCORED_TICKS_PER_CONTROLLER_REPLICATE,
    )
    _nonnegative_int(
        value["safety_overrides"],
        "safety overrides",
        maximum=PHYSICAL_TICKS_PER_CONTROLLER_REPLICATE,
    )
    failures = value["hard_failures"]
    if not isinstance(failures, Mapping) or set(failures) != set(HARD_FAILURE_KEYS):
        raise SerializationError("hard-failure ledger schema differs")
    for key in HARD_FAILURE_KEYS:
        _nonnegative_int(failures[key], f"hard_failures.{key}")
    _finite_unit(value["mean_value"], "mean value")
    _finite_unit(value["tail_value"], "tail value")
    _require_sha256(value["tape_commitment_sha256"], "tape commitment")
    for key in (
        "tick_audit_valid",
        "road_fit_audit_valid",
        "arm_transition_audit_valid",
        "endpoint_audit_valid",
        "raw_conformant",
        "sham_valid",
    ):
        if not isinstance(value[key], bool):
            raise SerializationError(f"{key} must be a boolean audit fact")
    for key, expected_keys in (
        ("road_fit_facts", _ROAD_FIT_FACT_KEYS),
        ("arm_transition_facts", _ARM_TRANSITION_FACT_KEYS),
        ("sham_validity_facts", _SHAM_VALIDITY_FACT_KEYS),
    ):
        facts = value[key]
        if not isinstance(facts, Mapping) or set(facts) != expected_keys:
            raise SerializationError(f"{key} schema differs")
        if any(not isinstance(facts[name], bool) for name in expected_keys):
            raise SerializationError(f"{key} must contain boolean facts")
    return json.loads(canonical_json_bytes(dict(value)))


def build_cell_packet(
    identity: CellIdentity,
    *,
    bindings: Mapping[str, str],
    aggregate: Mapping[str, object],
    sidecars: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    if set(bindings) != set(BINDING_KEYS):
        raise SerializationError("cell binding schema differs")
    checked_bindings = {key: _require_sha256(bindings[key], key) for key in BINDING_KEYS}
    if set(sidecars) != set(SIDECAR_SCHEMAS):
        raise SerializationError("cell sidecar set is incomplete")
    checked_sidecars = {
        kind: validate_sidecar_ref(kind, sidecars[kind]) for kind in SIDECAR_SCHEMAS
    }
    packet = {
        "schema": CELL_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "blinded": True,
        "partial_interpretation_allowed": False,
        "cell": identity.as_dict(),
        "bindings": checked_bindings,
        "aggregate": validate_cell_aggregate(identity, aggregate),
        "sidecars": checked_sidecars,
        "complete": True,
    }
    validate_cell_packet(packet)
    return packet


def validate_cell_packet(value: Mapping[str, object]) -> CellIdentity:
    expected_keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "blinded",
        "partial_interpretation_allowed",
        "cell",
        "bindings",
        "aggregate",
        "sidecars",
        "complete",
    }
    if set(value) != expected_keys:
        raise SerializationError("cell top-level schema differs")
    fixed = {
        "schema": CELL_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "blinded": True,
        "partial_interpretation_allowed": False,
        "complete": True,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise SerializationError("cell frozen identity differs")
    if not isinstance(value["cell"], Mapping):
        raise SerializationError("cell identity must be an object")
    identity = CellIdentity.from_dict(value["cell"])
    bindings = value["bindings"]
    if not isinstance(bindings, Mapping) or set(bindings) != set(BINDING_KEYS):
        raise SerializationError("cell binding schema differs")
    for key in BINDING_KEYS:
        _require_sha256(bindings[key], key)
    aggregate = value["aggregate"]
    if not isinstance(aggregate, Mapping):
        raise SerializationError("cell aggregate must be an object")
    validate_cell_aggregate(identity, aggregate)
    sidecars = value["sidecars"]
    if not isinstance(sidecars, Mapping) or set(sidecars) != set(SIDECAR_SCHEMAS):
        raise SerializationError("cell sidecar set is incomplete")
    for kind in SIDECAR_SCHEMAS:
        item = sidecars[kind]
        if not isinstance(item, Mapping):
            raise SerializationError(f"{kind} sidecar reference must be an object")
        validate_sidecar_ref(kind, item)
    return identity


def build_cell_commit(identity: CellIdentity, packet: Mapping[str, object]) -> dict[str, object]:
    if validate_cell_packet(packet) != identity:
        raise SerializationError("cell packet and commit identity differ")
    sidecars = packet["sidecars"]
    assert isinstance(sidecars, Mapping)
    body = {
        "schema": CELL_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "cell": identity.as_dict(),
        "cell_sha256": document_sha256(packet),
        "sidecar_sha256": {kind: sidecars[kind]["sha256"] for kind in SIDECAR_SCHEMAS},  # type: ignore[index]
        "complete": True,
    }
    return {**body, "commit_sha256": document_sha256(body)}


def validate_cell_commit(value: Mapping[str, object]) -> CellIdentity:
    keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "cell",
        "cell_sha256",
        "sidecar_sha256",
        "complete",
        "commit_sha256",
    }
    if set(value) != keys:
        raise SerializationError("cell commit schema differs")
    fixed = {
        "schema": CELL_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "complete": True,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise SerializationError("cell commit frozen identity differs")
    if not isinstance(value["cell"], Mapping):
        raise SerializationError("cell commit identity must be an object")
    identity = CellIdentity.from_dict(value["cell"])
    _require_sha256(value["cell_sha256"], "cell packet")
    sidecars = value["sidecar_sha256"]
    if not isinstance(sidecars, Mapping) or set(sidecars) != set(SIDECAR_SCHEMAS):
        raise SerializationError("cell commit sidecar digest set differs")
    for kind in SIDECAR_SCHEMAS:
        _require_sha256(sidecars[kind], f"{kind} sidecar")
    body = {key: value[key] for key in value if key != "commit_sha256"}
    if value["commit_sha256"] != document_sha256(body):
        raise SerializationError("cell commit digest differs")
    return identity


def expected_cell_identities() -> tuple[CellIdentity, ...]:
    return tuple(CellIdentity(arm, replicate) for arm in ARMS for replicate in range(REPLICATES))


def build_panel_commit(commits: Sequence[Mapping[str, object]]) -> dict[str, object]:
    by_identity: dict[CellIdentity, Mapping[str, object]] = {}
    for commit in commits:
        identity = validate_cell_commit(commit)
        if identity in by_identity:
            raise SerializationError("duplicate cell commit")
        by_identity[identity] = commit
    expected = expected_cell_identities()
    if set(by_identity) != set(expected):
        raise SerializationError("panel commit does not contain the exact 512 cells")
    body = {
        "schema": PANEL_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "cell_count": len(expected),
        "cells": [
            {
                "cell": identity.as_dict(),
                "commit_sha256": by_identity[identity]["commit_sha256"],
            }
            for identity in expected
        ],
        "missing_cells": [],
        "duplicate_cells": [],
        "substituted_cells": [],
        "complete": True,
    }
    return {**body, "panel_commit_sha256": document_sha256(body)}


def validate_panel_commit(value: Mapping[str, object]) -> tuple[CellIdentity, ...]:
    keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "cell_count",
        "cells",
        "missing_cells",
        "duplicate_cells",
        "substituted_cells",
        "complete",
        "panel_commit_sha256",
    }
    if set(value) != keys:
        raise SerializationError("panel commit top-level schema differs")
    fixed = {
        "schema": PANEL_COMMIT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "cell_count": len(ARMS) * REPLICATES,
        "missing_cells": [],
        "duplicate_cells": [],
        "substituted_cells": [],
        "complete": True,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise SerializationError("panel commit frozen identity/completeness differs")
    rows = value["cells"]
    if not isinstance(rows, list) or len(rows) != len(ARMS) * REPLICATES:
        raise SerializationError("panel commit must list exactly 512 cells")
    identities: list[CellIdentity] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"cell", "commit_sha256"}:
            raise SerializationError("panel commit row schema differs")
        if not isinstance(row["cell"], Mapping):
            raise SerializationError("panel commit cell identity must be an object")
        identities.append(CellIdentity.from_dict(row["cell"]))
        _require_sha256(row["commit_sha256"], "cell commit")
    expected = expected_cell_identities()
    if tuple(identities) != expected:
        raise SerializationError("panel commit cells are absent, duplicated, or reordered")
    body = {key: value[key] for key in value if key != "panel_commit_sha256"}
    if value["panel_commit_sha256"] != document_sha256(body):
        raise SerializationError("panel commit digest differs")
    return expected


def cell_packet_path(root: Path, identity: CellIdentity) -> Path:
    return Path(root) / "private-cells" / identity.arm / f"replicate-{identity.replicate:03d}.json"


def cell_commit_path(root: Path, identity: CellIdentity) -> Path:
    return Path(root) / "private-commits" / identity.arm / f"replicate-{identity.replicate:03d}.json"


def sidecar_path(root: Path, identity: CellIdentity, kind: str) -> Path:
    if kind not in SIDECAR_SCHEMAS:
        raise SerializationError("unknown TBVUUS sidecar kind")
    return (
        Path(root)
        / "private-sidecars"
        / identity.arm
        / f"replicate-{identity.replicate:03d}.{kind}.bin"
    )


_SIDECAR_MAGIC = b"TBVU03\0\0"
_SIDECAR_VERSION = 1
_SIDECAR_KINDS = tuple(SIDECAR_SCHEMAS)
_SIDECAR_HEADER = struct.Struct(">8sBBBHII")
_TICK_ROW = struct.Struct(">BBHH32s")
_ROAD_ROW = struct.Struct(">BBBBb32s")
_ARM_ROW = struct.Struct(">BBBB32s")
_ENDPOINT_ROW = struct.Struct(">BHH32s")
_ROW_STRUCTS = {
    "tick_audit": _TICK_ROW,
    "road_fit_audit": _ROAD_ROW,
    "arm_transition_audit": _ARM_ROW,
    "endpoint_audit": _ENDPOINT_ROW,
}


def _digest_bytes(value: object, label: str) -> bytes:
    return bytes.fromhex(_require_sha256(value, label))


def encode_sidecar_rows(
    kind: str,
    identity: CellIdentity,
    rows: Sequence[Mapping[str, object]],
) -> bytes:
    """Encode compact replay commitments; no scientific endpoint is exposed."""

    if kind not in SIDECAR_SCHEMAS:
        raise SerializationError("unknown TBVUUS sidecar kind")
    _, expected_rows = SIDECAR_SCHEMAS[kind]
    if len(rows) != expected_rows:
        raise SerializationError(f"{kind} requires exactly {expected_rows} rows")
    row_struct = _ROW_STRUCTS[kind]
    payload = bytearray(
        _SIDECAR_HEADER.pack(
            _SIDECAR_MAGIC,
            _SIDECAR_VERSION,
            _SIDECAR_KINDS.index(kind),
            ARMS.index(identity.arm),
            identity.replicate,
            expected_rows,
            row_struct.size,
        )
    )
    for row in rows:
        if kind == "tick_audit":
            if set(row) != {"block", "encounter_ordinal", "tick", "flags", "digest"}:
                raise SerializationError("tick-audit row schema differs")
            packed = row_struct.pack(
                row["block"], row["encounter_ordinal"], row["tick"], row["flags"],
                _digest_bytes(row["digest"], "tick-audit row"),
            )
        elif kind == "road_fit_audit":
            if set(row) != {"block", "encounter_ordinal", "route", "available", "selected", "digest"}:
                raise SerializationError("road-fit-audit row schema differs")
            packed = row_struct.pack(
                row["block"], row["encounter_ordinal"], row["route"],
                row["available"], row["selected"],
                _digest_bytes(row["digest"], "road-fit-audit row"),
            )
        elif kind == "arm_transition_audit":
            if set(row) != {"block", "encounter_ordinal", "route", "shell", "digest"}:
                raise SerializationError("arm-transition-audit row schema differs")
            packed = row_struct.pack(
                row["block"], row["encounter_ordinal"], row["route"], row["shell"],
                _digest_bytes(row["digest"], "arm-transition-audit row"),
            )
        else:
            if set(row) != {"block", "short_valid", "long_valid", "digest"}:
                raise SerializationError("endpoint-audit row schema differs")
            packed = row_struct.pack(
                row["block"], row["short_valid"], row["long_valid"],
                _digest_bytes(row["digest"], "endpoint-audit row"),
            )
        payload.extend(packed)
    encoded = bytes(payload)
    validate_sidecar_payload(kind, identity, encoded)
    return encoded


def validate_sidecar_payload(kind: str, identity: CellIdentity, payload: bytes) -> None:
    if kind not in SIDECAR_SCHEMAS or not isinstance(payload, bytes):
        raise SerializationError("unknown or non-bytes TBVUUS sidecar")
    row_struct = _ROW_STRUCTS[kind]
    if len(payload) < _SIDECAR_HEADER.size:
        raise SerializationError(f"{kind} sidecar is truncated")
    magic, version, kind_id, arm_id, replicate, row_count, row_size = _SIDECAR_HEADER.unpack_from(payload)
    _, expected_rows = SIDECAR_SCHEMAS[kind]
    if (
        magic != _SIDECAR_MAGIC
        or version != _SIDECAR_VERSION
        or kind_id != _SIDECAR_KINDS.index(kind)
        or arm_id != ARMS.index(identity.arm)
        or replicate != identity.replicate
        or row_count != expected_rows
        or row_size != row_struct.size
        or len(payload) != _SIDECAR_HEADER.size + row_count * row_size
    ):
        raise SerializationError(f"{kind} sidecar header or length differs")
    rows = [
        row_struct.unpack_from(payload, _SIDECAR_HEADER.size + index * row_size)
        for index in range(row_count)
    ]
    if kind in ("road_fit_audit", "arm_transition_audit"):
        expected = [
            (block, ordinal)
            for block in range(BLOCKS_PER_CONTROLLER_REPLICATE)
            for ordinal in range(ENCOUNTERS_PER_BLOCK)
        ]
        if [(row[0], row[1]) for row in rows] != expected:
            raise SerializationError(f"{kind} encounter ordering differs")
    elif kind == "endpoint_audit":
        if [row[0] for row in rows] != list(range(BLOCKS_PER_CONTROLLER_REPLICATE)):
            raise SerializationError("endpoint-audit block ordering differs")
    else:
        cursor = 0
        for block in range(BLOCKS_PER_CONTROLLER_REPLICATE):
            for ordinal, route in enumerate(expected_encounter_order(identity.replicate, block)):
                tick_count = 48 if route == "SHORT" else 144
                observed = rows[cursor : cursor + tick_count]
                if [(row[0], row[1], row[2]) for row in observed] != [
                    (block, ordinal, tick) for tick in range(tick_count)
                ]:
                    raise SerializationError("tick-audit ordering differs")
                cursor += tick_count
        if cursor != len(rows):
            raise SerializationError("tick-audit row count differs")


def sidecar_reference(kind: str, identity: CellIdentity, payload: bytes) -> dict[str, object]:
    validate_sidecar_payload(kind, identity, payload)
    schema, row_count = SIDECAR_SCHEMAS[kind]
    return {
        "schema": schema,
        "row_count": row_count,
        "sha256": sha256_bytes(payload),
        "bytes": len(payload),
    }


def serialization_schema_identity() -> dict[str, object]:
    """Return the exact payload/binary schema facts bound before activity."""

    return {
        "cell_aggregate_keys": sorted(_AGGREGATE_KEYS),
        "road_fit_fact_keys": sorted(_ROAD_FIT_FACT_KEYS),
        "arm_transition_fact_keys": sorted(_ARM_TRANSITION_FACT_KEYS),
        "sham_validity_fact_keys": sorted(_SHAM_VALIDITY_FACT_KEYS),
        "sidecar_magic_hex": _SIDECAR_MAGIC.hex(),
        "sidecar_version": _SIDECAR_VERSION,
        "sidecar_kind_order": list(_SIDECAR_KINDS),
        "sidecar_row_sizes": {
            kind: row_struct.size for kind, row_struct in _ROW_STRUCTS.items()
        },
    }
