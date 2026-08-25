"""Fail-closed batch-only CAL/HOLD lifecycle for HEADLAND-90 R03.

Importing and planning are preactivity operations.  Production-coordinate word
materialization and native host calls occur only behind :func:`admit_production`.
There is no Python host fallback and no API that returns partial endpoints.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys

from envs.native.production_backend import (
    ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
    require_cpp_batched_production,
)

from .analysis import panel_endpoints, replicate_endpoints
from . import analysis as az
from . import controllers
from . import host as host_model
from . import serialization as storage_schema
from .config import (
    CARD_REVISION, FIXTURE_NAMESPACE, HOST_ID, PRODUCTION_NAMESPACE,
    ControllerSpec, EncounterSpec, FixtureTape, RouteClass,
)
from .controllers import (
    CONTROLLER_ORDINAL, CONTROLLER_REGISTRY, CalibrationSummary,
    LOGICAL_HELD_OUT_TAGS,
    OrderedNeumaierAccumulator,
    identity_preserving_alias_ledger,
    coefficient_tuple, rate_lambda,
    controller_rate_fraction,
    select_flex, select_global, select_two_stratum,
)
from .coordinates import Coordinate, encode_coordinate
from .native_backend import run_native_batch
from . import native_backend as direction_native
from .event_transform import event_transform_bits, float_bits, float_from_bits
from .preactivity import COORDINATE_PROPOSAL_ID, coordinate_binding_proposal
from .serialization import (
    CAL_REPLICATES,
    HOLD_REPLICATES,
    CellIdentity,
    SerializationError,
    atomic_write_once,
    build_cell_packet,
    atomic_write_bytes, encode_opportunity_rows, decode_opportunity_rows,
    encode_cross_rows, decode_cross_rows, sidecar_path, sha256_bytes,
    canonical_json_bytes,
    cell_path,
    document_sha256,
    read_cell_packet,
    validate_cell_packet,
)


DIRECTION_ID = "opportunity_normalized_lease_gated_rebinding"
STAGE = "ONLGR-HEADLAND90-R03-CAL-HOLD-FULL-PANEL"
FREEZE_SCHEMA = "ONLGR-HEADLAND90-R03-ACCEPTED-PREACTIVITY-FREEZE-v1"
BINDING_SCHEMA = "ONLGR-HEADLAND90-R03-ROOT-COORDINATE-BINDING-v1"
LEASE_SCHEMA = "ONLGR-HEADLAND90-R03-DIRECTION-LEASE-v1"
PANEL_SCHEMA = "ONLGR-HEADLAND90-R03-PRIVATE-PANEL-v1"
SELECTOR_SCHEMA = "ONLGR-HEADLAND90-R03-IMMUTABLE-SELECTORS-v1"
ALIAS_SCHEMA = "ONLGR-HEADLAND90-R03-LOGICAL-ALIASES-v1"
COMPLETE_SCHEMA = "ONLGR-HEADLAND90-R03-COMPLETE-PACKAGE-v1"
RESULT_SCHEMA = "ONLGR-HEADLAND90-R03-RESULT-v1"
TECHNICAL_ACCEPTANCE_SCHEMA = "ONLGR-HEADLAND90-R03-CM-TECHNICAL-ACCEPTANCE-v1"
CAL_CONTROLLER_REPLICATES = 192 * 48
MAX_HOLD_CONTROLLER_REPLICATES = 5 * 128
TOTAL_CONTROLLER_REPLICATES = 9_856
TOTAL_PHYSICAL_TICKS = 37_847_040
MAX_RAM_BYTES = 16 * 1024**3
MAX_STORAGE_BYTES = 4 * 1024**3
MAX_CPU_WORKERS = 8
SHARED_GUARD_BATCH_WIDTH = 192
_ADMISSION_TOKEN = object()
_FIXTURE_ADMISSION_TOKEN = object()
_REPLAY_TOKEN = object()
_ACTIVITY_COMMITTED_PERMITS: dict[int, object] = {}
ACTIVITY_SCHEMA = "ONLGR-HEADLAND90-R03-ACTIVITY-STARTED-v1"
ACTIVITY_INTENT_SCHEMA = "ONLGR-HEADLAND90-R03-ACTIVITY-INTENT-v1"


class ProductionAdmissionError(PermissionError):
    pass


@dataclass(frozen=True, order=True)
class BatchIdentity:
    split: str
    replicate: int
    block: int
    route_class: str

    @property
    def template(self) -> int:
        return (self.replicate + 3 * self.block) % 4

    @property
    def encounter_ordinal(self) -> int:
        order = ("SHORT", "LONG") if (self.replicate + self.block) % 2 == 0 else ("LONG", "SHORT")
        return order.index(self.route_class)


def batch_plan(split: str) -> tuple[BatchIdentity, ...]:
    """Exact encounter batches; controllers are the batch dimension."""

    if split not in ("CAL", "HOLD"):
        raise ValueError("batch plan split must be CAL or HOLD")
    replicates = CAL_REPLICATES if split == "CAL" else HOLD_REPLICATES
    return tuple(
        BatchIdentity(split, replicate, block, route_class)
        for replicate in range(replicates)
        for block in range(20)
        for route_class in (
            ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")
        )
    )


def coordinate_rows_digest() -> str:
    """Stream the complete bound coordinate row set without drawing any word."""

    digest = hashlib.sha256(b"ONLGR-HEADLAND90-CAL-HOLD-BINDING-v1\0")
    previous: bytes | None = None
    state_stream_lanes = (
        ("target_lateral", 0), ("target_lateral", 1),
        ("wind_T", 0), ("wind_T", 1), ("wind_R", 0), ("wind_R", 1),
        ("sensor_x", 0), ("sensor_x", 1), ("sensor_y", 0), ("sensor_y", 1),
        ("shadow_TR", 0), ("shadow_TR", 1), ("shadow_RB", 0), ("shadow_RB", 1),
    )
    for split, replicate_count in (("CAL", 48), ("HOLD", 128)):
        for replicate in range(replicate_count):
            for block in range(20):
                # Encoded class fields are length-prefixed: LONG sorts before SHORT.
                for route_class, scored_ticks in (("LONG", 128), ("SHORT", 32)):
                    batch = BatchIdentity(split, replicate, block, route_class)
                    rows: list[bytes] = []
                    for tick in range(16 + scored_ticks + 1):
                        for stream, lane in state_stream_lanes:
                            rows.append(encode_coordinate(_coordinate(batch, tick=tick, stream=stream, lane=lane)))
                    for tick in range(16 + scored_ticks):
                        for stream in ("link_TR", "link_RB", "action"):
                            rows.append(encode_coordinate(_coordinate(batch, tick=tick, stream=stream, lane=0)))
                    for encoded in sorted(rows):
                        if previous is not None and encoded <= previous:
                            raise AssertionError("complete production coordinate rows are not unique and ordered")
                        digest.update(len(encoded).to_bytes(8, "big"))
                        digest.update(encoded)
                        previous = encoded
    return digest.hexdigest()


def verify_coordinate_binding_rows(binding: Mapping[str, object]) -> str:
    observed = coordinate_rows_digest()
    if observed != binding.get("coordinate_rows_sha256"):
        raise ProductionAdmissionError("Root-bound coordinate row digest differs from exact enumeration")
    return observed


def retained_trace_plan(
    aliases: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Return logical trace requirements without duplicating exact aliases."""

    if tuple(row.get("logical_tag") for row in aliases) != LOGICAL_HELD_OUT_TAGS:
        raise ValueError("trace plan requires the five logical tags in frozen order")
    cal = [
        {"split": "CAL", "physical_controller_id": controller, "replicate": replicate}
        for controller in ("theta-000", "theta-063")
        for replicate in range(8)
    ]
    hold_logical = [
        {
            "split": "HOLD",
            "logical_tag": row["logical_tag"],
            "physical_controller_id": row["physical_map_id"],
            "replicate": replicate,
        }
        for row in aliases
        for replicate in range(8)
    ]
    unique_physical = {
        (row["split"], row["physical_controller_id"], row["replicate"])
        for row in (*cal, *hold_logical)
    }
    if len(cal) + len(hold_logical) != 56 or len(unique_physical) > 56:
        raise AssertionError("retained trace plan differs from the frozen at-most-56 plan")
    return {
        "calibration_physical": cal,
        "held_out_logical": hold_logical,
        "maximum_logical_traces": 56,
        "unique_physical_trace_count": len(unique_physical),
        "exact_aliases_share_physical_trace": True,
    }


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ProductionAdmissionError(f"{label} must be a SHA-256 identity")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ProductionAdmissionError(f"{label} must be lowercase hexadecimal") from exc
    if value != value.lower():
        raise ProductionAdmissionError(f"{label} must be lowercase hexadecimal")
    return value


def validate_accepted_freeze(value: Mapping[str, object]) -> str:
    expected = {
        "schema": FREEZE_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "accepted": True,
        "activity_started": False,
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ProductionAdmissionError("preactivity freeze is absent, changed, or not accepted")
    hash_fields = {
        "preactivity_identity_sha256", "technical_acceptance_sha256",
        "source_set_sha256", "config_sha256", "schema_sha256", "shared_guard_source_sha256",
    }
    if set(value) != set(expected) | hash_fields:
        raise ProductionAdmissionError("accepted preactivity freeze schema differs")
    for key in hash_fields:
        _sha(value[key], key)
    return document_sha256(value)


def live_source_identity() -> dict[str, str]:
    package = Path(__file__).resolve().parent
    source_names = (
        "production.py", "serialization.py", "analysis.py", "controllers.py", "host.py",
        "native_backend.py", "event_transform.py", "coordinates.py", "preactivity.py",
        "native/headland90_backend.cpp", "native/event_transform_table.h",
    )
    digest = hashlib.sha256(b"ONLGR-H90-R03-SOURCE-SET-v1\0")
    for name in source_names:
        payload = (package / name).read_bytes(); encoded = name.encode()
        digest.update(len(encoded).to_bytes(4,"big") + encoded + len(payload).to_bytes(8,"big") + payload)
    config_payload = (package / "config.py").read_bytes()
    schema = {
        "cell": storage_schema.CELL_SCHEMA,
        "trace": "ONLGR-HEADLAND90-R03-PRIVATE-TRACE-v1",
        "opportunity_sidecar": storage_schema.OPPORTUNITY_LEDGER_FORMAT,
        "cross_sidecar": storage_schema.CROSS_LEDGER_FORMAT,
        "cell_commit": "ONLGR-HEADLAND90-R03-CELL-COMMIT-v1",
        "activity": ACTIVITY_SCHEMA,
        "panel": PANEL_SCHEMA, "selector": SELECTOR_SCHEMA, "alias": ALIAS_SCHEMA,
        "complete": COMPLETE_SCHEMA, "result": RESULT_SCHEMA,
        "technical_acceptance": TECHNICAL_ACCEPTANCE_SCHEMA,
        "calibration_cells": 9216, "logical_hold_cells": 640, "physical_ticks": TOTAL_PHYSICAL_TICKS,
    }
    from .preactivity import collect_preactivity_identity
    preactivity = collect_preactivity_identity()
    guard_source = Path(__file__).resolve().parents[4] / "envs" / "native" / "production_backend.py"
    return {"source_set_sha256": digest.hexdigest(), "config_sha256": hashlib.sha256(config_payload).hexdigest(), "schema_sha256": document_sha256(schema), "preactivity_identity_sha256": str(preactivity["identity_sha256"]), "shared_guard_source_sha256": hashlib.sha256(guard_source.read_bytes()).hexdigest()}


def validate_coordinate_binding(value: Mapping[str, object]) -> str:
    proposal = coordinate_binding_proposal()
    expected = {
        "schema": BINDING_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "proposal_id": COORDINATE_PROPOSAL_ID,
        "proposal_schema_sha256": proposal["proposal_schema_sha256"],
        "namespace": PRODUCTION_NAMESPACE,
        "root_authorized": True,
        "complete_required_row_set": True,
        "production_words_materialized": False,
        "controller_identity_in_disturbance_key": False,
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ProductionAdmissionError("Root coordinate binding is absent or differs from the proposal")
    if set(value) != set(expected) | {"coordinate_rows_sha256", "root_authorization_sha256"}:
        raise ProductionAdmissionError("Root coordinate binding schema differs")
    _sha(value["coordinate_rows_sha256"], "coordinate row binding")
    _sha(value["root_authorization_sha256"], "Root coordinate authorization")
    return document_sha256(value)


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProductionAdmissionError("lease not_after_utc must be an ISO-8601 UTC value")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ProductionAdmissionError("lease not_after_utc is invalid") from exc
    return parsed


def validate_direction_lease(
    value: Mapping[str, object], *, result_root: Path, now: datetime | None = None,
    require_active: bool = True,
) -> str:
    expected = {
        "schema": LEASE_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "authorized": True,
        "result_root": str(Path(result_root).resolve()),
        "calibration_controller_replicates": CAL_CONTROLLER_REPLICATES,
        "maximum_held_out_controller_replicates": MAX_HOLD_CONTROLLER_REPLICATES,
        "total_controller_replicates": TOTAL_CONTROLLER_REPLICATES,
        "total_physical_ticks": TOTAL_PHYSICAL_TICKS,
        "calibration_maps": 192,
        "calibration_replicates": 48,
        "held_out_replicates": 128,
        "maximum_unique_held_out_maps": 5,
        "batch_only": True,
        "backend": "cpp",
        "python_fallback": False,
    }
    if any(value.get(key) != item for key, item in expected.items()):
        raise ProductionAdmissionError("direction lease changes the exact panel or native boundary")
    extra = {
        "cpu_workers", "ram_bytes", "storage_bytes", "not_after_utc", "lease_token_sha256"
    }
    if set(value) != set(expected) | extra:
        raise ProductionAdmissionError("direction lease schema differs")
    cpu, ram, storage = value["cpu_workers"], value["ram_bytes"], value["storage_bytes"]
    if isinstance(cpu, bool) or not isinstance(cpu, int) or not 1 <= cpu <= MAX_CPU_WORKERS:
        raise ProductionAdmissionError("lease CPU workers exceed the accepted 1..8 range")
    if isinstance(ram, bool) or not isinstance(ram, int) or not 0 < ram <= MAX_RAM_BYTES:
        raise ProductionAdmissionError("lease RAM exceeds 16 GiB")
    if isinstance(storage, bool) or not isinstance(storage, int) or not 0 < storage <= MAX_STORAGE_BYTES:
        raise ProductionAdmissionError("lease storage exceeds 4 GiB")
    _sha(value["lease_token_sha256"], "lease token")
    current = now or datetime.now(timezone.utc)
    if require_active and _parse_utc(value["not_after_utc"]) <= current:
        raise ProductionAdmissionError("direction lease has expired")
    return document_sha256(value)


def lease_scope_identity(value: Mapping[str, object], *, result_root: Path) -> str:
    """Stable science/resource envelope identity shared by routine lease renewals."""

    stable = dict(value)
    for key in ("cpu_workers", "ram_bytes", "storage_bytes", "not_after_utc", "lease_token_sha256"):
        stable.pop(key, None)
    stable["result_root"] = str(Path(result_root).resolve())
    return document_sha256(stable)


@dataclass(frozen=True)
class ProductionPermit:
    result_root: Path
    preactivity_freeze_sha256: str
    coordinate_binding_sha256: str
    coordinate_binding_document: Mapping[str, object]
    lease_sha256: str
    lease_scope_sha256: str
    lease_document: Mapping[str, object]
    backend_receipt: Mapping[str, object]
    backend_receipt_sha256: str
    not_after_utc: datetime
    source_set_sha256: str
    config_sha256: str
    schema_sha256: str
    _token: object

    def assert_active(self, *, now: datetime | None = None) -> None:
        if self._token not in (_ADMISSION_TOKEN, _FIXTURE_ADMISSION_TOKEN):
            raise ProductionAdmissionError("production permit was not issued by exact admission")
        if (now or datetime.now(timezone.utc)) >= self.not_after_utc:
            raise ProductionAdmissionError("direction lease expired during panel execution")


@dataclass(frozen=True)
class ProductionNativeCarrier:
    """Typed internal carrier: fixture-shaped ABI arrays, production-key provenance."""
    spec: EncounterSpec
    tape: FixtureTape
    coordinate_binding_sha256: str
    production_namespace: str
    _token: object

    def validate(self, permit: ProductionPermit) -> None:
        permit.assert_active()
        if permit._token is not _ADMISSION_TOKEN or self._token is not _ADMISSION_TOKEN or self.coordinate_binding_sha256 != permit.coordinate_binding_sha256 or self.production_namespace != PRODUCTION_NAMESPACE or self.spec.namespace != FIXTURE_NAMESPACE:
            raise ProductionAdmissionError("native carrier lacks exact production-coordinate provenance")


@dataclass(frozen=True)
class PostActivityReplayAuthority:
    root: Path
    coordinate_binding_sha256: str
    native_artifact: str
    native_artifact_sha256: str
    source_identity: Mapping[str, str]
    _token: object


def _validate_admission(
    *,
    preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object],
    direction_lease: Mapping[str, object],
    result_root: Path,
    shared_guard: Callable[..., Mapping[str, object]] = require_cpp_batched_production,
    coordinate_row_verifier: Callable[[Mapping[str, object]], str] = verify_coordinate_binding_rows,
    live_identity_verifier: Callable[[], Mapping[str, str]] = live_source_identity,
    now: datetime | None = None,
    resume: bool = False,
):
    """Validate every nonactivity gate, then call the exact shared C++ guard."""

    root = Path(result_root).resolve()
    if root.exists() and not resume:
        raise FileExistsError(f"production result root must be fresh: {root}")
    if resume and not root.is_dir():
        raise FileNotFoundError(f"resume result root is absent: {root}")
    freeze_digest = validate_accepted_freeze(preactivity_freeze)
    live = dict(live_identity_verifier())
    for key in ("source_set_sha256", "config_sha256", "schema_sha256", "preactivity_identity_sha256", "shared_guard_source_sha256"):
        if live.get(key) != preactivity_freeze.get(key):
            raise ProductionAdmissionError(f"live {key} differs from accepted freeze")
    coordinate_digest = validate_coordinate_binding(coordinate_binding)
    lease_digest = validate_direction_lease(direction_lease, result_root=root, now=now)
    verified_rows = coordinate_row_verifier(coordinate_binding)
    if verified_rows != coordinate_binding.get("coordinate_rows_sha256"):
        raise ProductionAdmissionError("coordinate verifier did not authenticate the Root-bound row set")
    receipt = dict(
        shared_guard(
            ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            backend="cpp",
            batch_width=SHARED_GUARD_BATCH_WIDTH,
            build_root=None,
        )
    )
    required_receipt = {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
        "backend": "cpp",
        "batch_width": SHARED_GUARD_BATCH_WIDTH,
        "full_reset_step_cpp": True,
        "python_fallback": False,
    }
    if any(receipt.get(key) != item for key, item in required_receipt.items()):
        raise ProductionAdmissionError("shared backend receipt is not the exact full-host C++ boundary")
    if not isinstance(receipt.get("native"), Mapping):
        raise ProductionAdmissionError("shared backend receipt lacks native artifact identity")
    return (
        root,
        freeze_digest,
        coordinate_digest,
        dict(coordinate_binding),
        lease_digest,
        lease_scope_identity(direction_lease, result_root=root),
        dict(direction_lease),
        receipt,
        document_sha256(receipt),
        _parse_utc(direction_lease["not_after_utc"]),
        str(preactivity_freeze["source_set_sha256"]),
        str(preactivity_freeze["config_sha256"]),
        str(preactivity_freeze["schema_sha256"]),
    )


def admit_production(
    *, preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object], direction_lease: Mapping[str, object],
    result_root: Path, resume: bool = False,
) -> ProductionPermit:
    """Authority-bearing admission with fixed live verifiers and shared guard."""

    return ProductionPermit(*_validate_admission(
        preactivity_freeze=preactivity_freeze,
        coordinate_binding=coordinate_binding,
        direction_lease=direction_lease,
        result_root=result_root,
        shared_guard=require_cpp_batched_production,
        coordinate_row_verifier=verify_coordinate_binding_rows,
        live_identity_verifier=live_source_identity,
        resume=resume,
    ), _ADMISSION_TOKEN)


def _admit_production_fixture(
    *, preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object], direction_lease: Mapping[str, object],
    result_root: Path,
    shared_guard: Callable[..., Mapping[str, object]],
    coordinate_row_verifier: Callable[[Mapping[str, object]], str],
    live_identity_verifier: Callable[[], Mapping[str, str]],
    now: datetime | None = None, resume: bool = False,
) -> ProductionPermit:
    """Non-authoritative test seam; its token cannot materialize a production word."""

    return ProductionPermit(*_validate_admission(
        preactivity_freeze=preactivity_freeze,
        coordinate_binding=coordinate_binding,
        direction_lease=direction_lease,
        result_root=result_root,
        shared_guard=shared_guard,
        coordinate_row_verifier=coordinate_row_verifier,
        live_identity_verifier=live_identity_verifier,
        now=now,
        resume=resume,
    ), _FIXTURE_ADMISSION_TOKEN)


def initialize_private_panel(
    permit: ProductionPermit,
    *,
    source_set_sha256: str,
    config_sha256: str,
    schema_sha256: str,
) -> Path:
    """Create the private root only after all admission gates are complete."""

    if not isinstance(permit, ProductionPermit):
        raise ProductionAdmissionError("private panel initialization requires a validated permit")
    permit.assert_active()
    supplied = (source_set_sha256, config_sha256, schema_sha256)
    frozen = (permit.source_set_sha256, permit.config_sha256, permit.schema_sha256)
    if supplied != frozen:
        raise ProductionAdmissionError("runner source/config/schema hashes differ from accepted freeze")
    root = permit.result_root
    manifest = {
        "schema": PANEL_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "private_blinded": True,
        "partial_results_exposed": False,
        "calibration_maps": 192,
        "calibration_replicates": 48,
        "held_out_replicates": 128,
        "maximum_unique_held_out_maps": 5,
        "controller_replicates": TOTAL_CONTROLLER_REPLICATES,
        "physical_ticks": TOTAL_PHYSICAL_TICKS,
        "bindings": {
            "preactivity_freeze_sha256": permit.preactivity_freeze_sha256,
            "coordinate_binding_sha256": permit.coordinate_binding_sha256,
            "lease_scope_sha256": permit.lease_scope_sha256,
            "backend_receipt_sha256": permit.backend_receipt_sha256,
            "source_set_sha256": _sha(source_set_sha256, "source set"),
            "config_sha256": _sha(config_sha256, "config"),
            "schema_sha256": _sha(schema_sha256, "schema"),
        },
    }
    if root.exists():
        existing = _load_exact_document(root / "PANEL.json")
        if existing != manifest:
            raise ProductionAdmissionError("resume root differs from the stable lease-scope panel")
        _retain_lease_receipt(root, permit)
        return root
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = root.parent / f".{root.name}.initializing"
    if staging.exists() and not staging.is_dir():
        raise FileExistsError("panel initialization staging path is not a directory")
    staging.mkdir(exist_ok=True)
    atomic_write_once(staging / "PANEL.json", manifest, authorized_root=staging)
    atomic_write_once(
        staging / "BACKEND_RECEIPT.json", permit.backend_receipt, authorized_root=staging
    )
    receipt_dir = staging / "lease-receipts"
    receipt_dir.mkdir()
    atomic_write_once(receipt_dir / f"{permit.lease_sha256}.json", permit.lease_document, authorized_root=staging)
    atomic_write_once(staging / "COORDINATE_BINDING.json", permit.coordinate_binding_document, authorized_root=staging)
    if set(path.name for path in staging.iterdir()) != {"PANEL.json", "BACKEND_RECEIPT.json", "COORDINATE_BINDING.json", "lease-receipts"}:
        raise ProductionAdmissionError("panel initialization staging inventory differs")
    try:
        os.replace(staging, root)
    except FileExistsError as exc:
        raise FileExistsError(f"production result root appeared during atomic initialization: {root}") from exc
    return root


def _retain_lease_receipt(root: Path, permit: ProductionPermit) -> Path:
    return atomic_write_once(
        Path(root) / "lease-receipts" / f"{permit.lease_sha256}.json",
        permit.lease_document,
        authorized_root=root,
    )


def _word(permit: ProductionPermit, coordinate: Coordinate) -> float:
    """Materialize one bound production word; type gate is mandatory."""

    if not isinstance(permit, ProductionPermit):
        raise ProductionAdmissionError("production words require a validated permit")
    permit.assert_active()
    if permit._token is not _ADMISSION_TOKEN:
        raise ProductionAdmissionError("fixture admission cannot materialize production words")
    if coordinate.namespace != PRODUCTION_NAMESPACE:
        raise ProductionAdmissionError("production word source requires the bound namespace")
    digest = hashlib.sha256(encode_coordinate(coordinate)).digest()
    word = (int.from_bytes(digest[:4], "big") + 0.5) / 4294967296.0
    permit_key = id(permit)
    if _ACTIVITY_COMMITTED_PERMITS.get(permit_key) is not permit:
        _commit_first_word(permit, coordinate, word)
        _ACTIVITY_COMMITTED_PERMITS[permit_key] = permit
    return word


def _first_coordinate() -> Coordinate:
    return _coordinate(BatchIdentity("CAL",0,0,"SHORT"),tick=0,stream="target_lateral",lane=0)


def _activity_identity(permit: ProductionPermit) -> dict[str, object]:
    panel = _load_exact_document(permit.result_root / "PANEL.json")
    return {"panel_sha256":document_sha256(panel), "coordinate_binding_sha256":permit.coordinate_binding_sha256, "backend_receipt_sha256":permit.backend_receipt_sha256}


def _write_activity_intent(permit: ProductionPermit) -> None:
    atomic_write_once(permit.result_root / "ACTIVITY_INTENT.json", {
        "schema":ACTIVITY_INTENT_SCHEMA, "first_coordinate":asdict(_first_coordinate()), **_activity_identity(permit)
    }, authorized_root=permit.result_root)


def _commit_first_word(permit: ProductionPermit, coordinate: Coordinate, word: float) -> None:
    intent = _load_exact_document(permit.result_root / "ACTIVITY_INTENT.json")
    expected_intent = {"schema":ACTIVITY_INTENT_SCHEMA,"first_coordinate":asdict(_first_coordinate()),**_activity_identity(permit)}
    started_path = permit.result_root / "ACTIVITY_STARTED.json"
    if started_path.exists():
        started = _load_exact_document(started_path)
        expected_started = {"schema":ACTIVITY_SCHEMA,"activity_started":True,"first_coordinate":asdict(_first_coordinate()),"first_word_bits":float_bits(_permit_word_value(permit,_first_coordinate())),**_activity_identity(permit)}
        if started != expected_started: raise ProductionAdmissionError("durable first-word identity differs")
        return
    if intent != expected_intent or coordinate != _first_coordinate():
        raise ProductionAdmissionError("activity intent permits only the exact first production word")
    atomic_write_once(started_path,{"schema":ACTIVITY_SCHEMA,"activity_started":True,"first_coordinate":asdict(coordinate),"first_word_bits":float_bits(word),**_activity_identity(permit)},authorized_root=permit.result_root)


def _permit_word_value(permit: ProductionPermit, coordinate: Coordinate) -> float:
    if permit._token is not _ADMISSION_TOKEN:
        raise ProductionAdmissionError("production word computation requires a real permit")
    digest = hashlib.sha256(encode_coordinate(coordinate)).digest()
    return (int.from_bytes(digest[:4], "big") + .5) / 4294967296.0


def _action_decision(uniform: float, q: Fraction) -> bool:
    """Pure decision law for synthetic tests; it never accepts a coordinate."""

    if not isinstance(uniform, float) or not math.isfinite(uniform) or not 0.0 < uniform < 1.0:
        raise ValueError("action uniform must be a finite open-unit binary64 value")
    return uniform < controllers.event_probability(q)


def _post_activity_replay_authority(root: Path) -> PostActivityReplayAuthority:
    """Authenticate retained real activity before any coordinate-derived replay."""

    root = Path(root).resolve()
    panel = _load_exact_document(root / "PANEL.json")
    bindings = panel.get("bindings")
    if not isinstance(bindings, Mapping):
        raise ProductionAdmissionError("post-activity replay lacks panel bindings")
    binding = _load_exact_document(root / "COORDINATE_BINDING.json")
    digest = validate_coordinate_binding(binding)
    if digest != bindings.get("coordinate_binding_sha256"):
        raise ProductionAdmissionError("post-activity replay binding differs from panel")
    backend = _load_exact_document(root / "BACKEND_RECEIPT.json")
    if document_sha256(backend) != bindings.get("backend_receipt_sha256"):
        raise ProductionAdmissionError("post-activity replay backend receipt differs from panel")
    expected_identity = {"panel_sha256":document_sha256(panel),"coordinate_binding_sha256":digest,"backend_receipt_sha256":document_sha256(backend)}
    intent_path = root / "ACTIVITY_INTENT.json"
    if not intent_path.is_file():
        raise ProductionAdmissionError("post-activity intent is absent or unauthenticated")
    intent = _load_exact_document(intent_path)
    if intent != {"schema":ACTIVITY_INTENT_SCHEMA,"first_coordinate":asdict(_first_coordinate()),**expected_identity}:
        raise ProductionAdmissionError("post-activity intent differs from the bound first coordinate")
    marker_path = root / "ACTIVITY_STARTED.json"
    if not marker_path.is_file():
        raise ProductionAdmissionError("post-activity replay marker is absent or unauthenticated")
    marker = _load_exact_document(marker_path)
    if any(marker.get(key) != value for key,value in {"schema":ACTIVITY_SCHEMA,"activity_started":True,"first_coordinate":asdict(_first_coordinate()),**expected_identity}.items()) or set(marker) != {"schema","activity_started","first_coordinate","first_word_bits",*expected_identity}:
        raise ProductionAdmissionError("post-activity replay marker is absent or unauthenticated")
    native = backend["native"]
    assert isinstance(native, Mapping)
    artifact = str(Path(str(native["artifact"])).resolve()); artifact_sha = _sha(native["artifact_sha256"],"replay native artifact")
    live = live_source_identity()
    for key in ("source_set_sha256","config_sha256","schema_sha256"):
        if live[key] != bindings.get(key): raise ProductionAdmissionError(f"post-activity live {key} differs from panel")
    authority = PostActivityReplayAuthority(root,digest,artifact,artifact_sha,live,_REPLAY_TOKEN)
    _authenticate_replay_runtime(authority)
    _require_exact_first_word_bits(marker.get("first_word_bits"),float_bits(_replay_word(authority,_first_coordinate())))
    return authority


def _require_exact_first_word_bits(value: object, expected: int) -> None:
    if isinstance(value,bool) or not isinstance(value,int) or value != expected:
        raise ProductionAdmissionError("durable first-word bits differ from exact bound coordinate replay")


def _authenticate_replay_runtime(authority: PostActivityReplayAuthority) -> None:
    if authority._token is not _REPLAY_TOKEN: raise ProductionAdmissionError("native replay authority is invalid")
    identity = direction_native.native_artifact_identity()
    if not _native_identity_matches(authority.native_artifact,authority.native_artifact_sha256,identity):
        raise ProductionAdmissionError("loaded direction native artifact differs from retained backend receipt")
    live = live_source_identity()
    for key in ("source_set_sha256","config_sha256","schema_sha256"):
        if live[key] != authority.source_identity[key]: raise ProductionAdmissionError(f"replay live {key} changed")


def _native_identity_matches(expected_path: str, expected_sha256: str, observed: Mapping[str, object]) -> bool:
    return str(Path(str(observed.get("artifact_path"))).resolve()) == str(Path(expected_path).resolve()) and observed.get("artifact_sha256") == expected_sha256


def _replay_word(authority: PostActivityReplayAuthority, coordinate: Coordinate) -> float:
    if authority._token is not _REPLAY_TOKEN or coordinate.namespace != PRODUCTION_NAMESPACE:
        raise ProductionAdmissionError("coordinate replay lacks authenticated post-activity authority")
    digest = hashlib.sha256(encode_coordinate(coordinate)).digest()
    return (int.from_bytes(digest[:4], "big") + 0.5) / 4294967296.0


def _replay_normal(authority: PostActivityReplayAuthority, coordinate: Coordinate) -> float:
    lower_lane = coordinate.lane - coordinate.lane % 2
    base = {key:getattr(coordinate,key) for key in (
        "namespace","split","replicate","block","route_class","template","tick","stream"
    )}
    radius = _replay_word(authority, Coordinate(**base, lane=lower_lane))
    angle = _replay_word(authority, Coordinate(**base, lane=lower_lane+1))
    magnitude = math.sqrt(-2.0*math.log(radius)); theta = 2.0*math.pi*angle
    return (magnitude*math.cos(theta), magnitude*math.sin(theta))[coordinate.lane % 2]


def _fixture_for_replay(authority: PostActivityReplayAuthority, batch: BatchIdentity) -> tuple[EncounterSpec, FixtureTape]:
    route = RouteClass(batch.route_class); template = ((1,8),(1,-8),(-1,8),(-1,-8))[batch.template]
    spec = EncounterSpec(route, template[0], template[1], namespace=FIXTURE_NAMESPACE)
    states, ticks = spec.total_ticks+1, spec.total_ticks
    normal = lambda tick,stream,lane: _replay_normal(authority,_coordinate(batch,tick=tick,stream=stream,lane=lane))
    word = lambda tick,stream: _replay_word(authority,_coordinate(batch,tick=tick,stream=stream,lane=0))
    tape = FixtureTape.from_sequences(spec,
        target_lateral=[normal(t,"target_lateral",0) for t in range(states)],
        wind_t=[(normal(t,"wind_T",0),normal(t,"wind_T",1)) for t in range(states)],
        wind_r=[(normal(t,"wind_R",0),normal(t,"wind_R",1)) for t in range(states)],
        sensor=[(normal(t,"sensor_x",0),normal(t,"sensor_y",0)) for t in range(states)],
        shadow_tr=[normal(t,"shadow_TR",0) for t in range(states)],
        shadow_rb=[normal(t,"shadow_RB",0) for t in range(states)],
        link_tr=[word(t,"link_TR") for t in range(ticks)], link_rb=[word(t,"link_RB") for t in range(ticks)],
        action=[word(t,"action") for t in range(ticks)])
    return spec,tape


def _normal(permit: ProductionPermit, coordinate: Coordinate) -> float:
    lower_lane = coordinate.lane - coordinate.lane % 2
    base = {
        "namespace": coordinate.namespace,
        "split": coordinate.split,
        "replicate": coordinate.replicate,
        "block": coordinate.block,
        "route_class": coordinate.route_class,
        "template": coordinate.template,
        "tick": coordinate.tick,
        "stream": coordinate.stream,
    }
    radius = _word(permit, Coordinate(**base, lane=lower_lane))
    angle = _word(permit, Coordinate(**base, lane=lower_lane + 1))
    magnitude = math.sqrt(-2.0 * math.log(radius))
    theta = 2.0 * math.pi * angle
    return (magnitude * math.cos(theta), magnitude * math.sin(theta))[coordinate.lane % 2]


def _coordinate(batch: BatchIdentity, *, tick: int, stream: str, lane: int) -> Coordinate:
    return Coordinate(
        namespace=PRODUCTION_NAMESPACE,
        split=batch.split,
        replicate=batch.replicate,
        block=batch.block,
        route_class=batch.route_class,
        template=batch.template,
        tick=tick,
        stream=stream,
        lane=lane,
    )


def _production_fixture(
    permit: ProductionPermit, batch: BatchIdentity
) -> ProductionNativeCarrier:
    route = RouteClass(batch.route_class)
    template = ((1, 8), (1, -8), (-1, 8), (-1, -8))[batch.template]
    spec = EncounterSpec(route, template[0], template[1], namespace=FIXTURE_NAMESPACE)
    states, ticks = spec.total_ticks + 1, spec.total_ticks
    tape = FixtureTape.from_sequences(
        spec,
        target_lateral=[
            _normal(permit, _coordinate(batch, tick=tick, stream="target_lateral", lane=0))
            for tick in range(states)
        ],
        wind_t=[
            tuple(_normal(permit, _coordinate(batch, tick=tick, stream="wind_T", lane=lane)) for lane in (0, 1))
            for tick in range(states)
        ],
        wind_r=[
            tuple(_normal(permit, _coordinate(batch, tick=tick, stream="wind_R", lane=lane)) for lane in (0, 1))
            for tick in range(states)
        ],
        sensor=[
            (
                _normal(permit, _coordinate(batch, tick=tick, stream="sensor_x", lane=0)),
                _normal(permit, _coordinate(batch, tick=tick, stream="sensor_y", lane=0)),
            )
            for tick in range(states)
        ],
        shadow_tr=[
            _normal(permit, _coordinate(batch, tick=tick, stream="shadow_TR", lane=0))
            for tick in range(states)
        ],
        shadow_rb=[
            _normal(permit, _coordinate(batch, tick=tick, stream="shadow_RB", lane=0))
            for tick in range(states)
        ],
        link_tr=[
            _word(permit, _coordinate(batch, tick=tick, stream="link_TR", lane=0))
            for tick in range(ticks)
        ],
        link_rb=[
            _word(permit, _coordinate(batch, tick=tick, stream="link_RB", lane=0))
            for tick in range(ticks)
        ],
        action=[
            _word(permit, _coordinate(batch, tick=tick, stream="action", lane=0))
            for tick in range(ticks)
        ],
    )
    return ProductionNativeCarrier(spec, tape, permit.coordinate_binding_sha256, PRODUCTION_NAMESPACE, _ADMISSION_TOKEN)


def _encounter_summary(result) -> dict[str, object]:
    ticks = result.ticks
    override_causes = {"terrain":0, "geofence":0, "separation":0}
    for row in ticks:
        if not row.safety_override: continue
        causes = _exact_override_causes(
            row.tracker_position,row.relay_position,
            tuple(host_model.AIR_T[row.unconstrained_tracker_index][i]+row.wind_tracker[i] for i in (0,1)),
            tuple(host_model.AIR_R[row.unconstrained_relay_index][i]+row.wind_relay[i] for i in (0,1)),
        )
        if not any(causes.values()): raise RuntimeError("safety override lacks an exact infeasibility cause")
        for key,value in causes.items(): override_causes[key] += int(value)
    failures = {
        "terrain_penetrations": int(any(row.terrain_penetration for row in ticks)),
        "geofence_exits": int(any(row.geofence_exit for row in ticks)),
        "separation_breaches": int(any(row.separation_breach for row in ticks)),
        "no_safe_control": int(result.no_safe_control),
        "no_planner_solution": int(result.no_planner_solution),
        "battery_exhaustions": int(result.battery_exhausted),
        "numerical_faults": 0,
    }
    return {
        "valid_ticks": result.scored_valid_ticks,
        "scored_ticks": result.spec.route_class.scored_ticks,
        "tracking_valid_ticks": sum(row.tracking_valid for row in ticks),
        "packet_valid_ticks": sum(row.packet_valid for row in ticks),
        "raw_link_success_tr": sum(row.raw_trial_tr for row in ticks),
        "raw_link_success_rb": sum(row.raw_trial_rb for row in ticks),
        "blackout_ticks": sum(row.blackout_active for row in ticks),
        "lockout_ticks": sum(row.lockout_active for row in ticks),
        "voluntary_updates": result.voluntary_updates,
        "voluntary_keeps": result.voluntary_keeps,
        "opportunity_rows": result.opportunity_rows,
        "safety_overrides": result.safety_overrides,
        "override_causes": override_causes,
        "failures": failures,
        "tracker_energy_final": float(ticks[-1].tracker_energy_after),
        "relay_energy_final": float(ticks[-1].relay_energy_after),
        "update_energy_joules_per_uav": 200 * (1 + result.voluntary_updates),
    }


def _exact_override_causes(p_t, p_r, vg_t, vg_r) -> dict[str, bool]:
    dt = host_model.DT
    end_t = tuple(p_t[i]+dt*vg_t[i] for i in (0,1)); end_r = tuple(p_r[i]+dt*vg_r[i] for i in (0,1))
    gx,gy = host_model.G_X,host_model.G_Y
    geofence = not all(gx[0] <= p[0] <= gx[1] and gy[0] <= p[1] <= gy[1] for p in (p_t,end_t,p_r,end_r))
    terrain = host_model.segment_distance_to_obstacle_sq(p_t,end_t) < host_model.TERRAIN_CLEARANCE**2 or host_model.segment_distance_to_obstacle_sq(p_r,end_r) < host_model.TERRAIN_CLEARANCE**2
    separation = host_model._minimum_relative_distance(p_t,vg_t,p_r,vg_r) < host_model.MIN_SEPARATION
    return {"terrain":terrain,"geofence":geofence,"separation":separation}


def _trace_safe(value: object) -> object:
    if isinstance(value, float):
        return value if math.isfinite(value) else "NOT_CONSUMED"
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, Mapping):
        return {str(key): _trace_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_trace_safe(item) for item in value]
    return value


def _write_trace(root: Path, identity: CellIdentity, tick_rows: Sequence[object]) -> Path:
    packet = {
        "schema": "ONLGR-HEADLAND90-R03-PRIVATE-TRACE-v1",
        "cell": identity.as_dict(),
        "complete_controller_replicate": True,
        "ticks": _trace_safe([asdict(row) for row in tick_rows]),
    }
    path = (
        root / "private-traces" / identity.split / identity.physical_controller_id
        / f"replicate-{identity.replicate:03d}.json"
    )
    return atomic_write_once(path, packet, authorized_root=root)


def _cell_commit_path(root: Path, identity: CellIdentity) -> Path:
    return Path(root) / "private-commits" / identity.split / identity.physical_controller_id / f"replicate-{identity.replicate:03d}.json"


def _cell_commit_document(root: Path, identity: CellIdentity, *, trace_required: bool) -> dict[str, object]:
    paths = {
        "cell": cell_path(root, identity),
        "opportunity": sidecar_path(root, identity, "opportunity"),
    }
    if identity.split == "HOLD": paths["cross"] = sidecar_path(root, identity, "cross")
    if trace_required:
        paths["trace"] = root / "private-traces" / identity.split / identity.physical_controller_id / f"replicate-{identity.replicate:03d}.json"
    if not all(path.is_file() for path in paths.values()):
        raise SerializationError("cell transaction cannot seal an incomplete artifact set")
    return {"schema":"ONLGR-HEADLAND90-R03-CELL-COMMIT-v1", "cell":identity.as_dict(), "artifacts":{key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in sorted(paths.items())}}


def _seal_cell_transaction(root: Path, identity: CellIdentity, *, trace_required: bool) -> Path:
    return atomic_write_once(_cell_commit_path(root,identity),_cell_commit_document(root,identity,trace_required=trace_required),authorized_root=root)


def _mean_proof_json(value) -> dict[str, object]:
    return {
        "value": value.value,
        "row_count": value.row_count,
        "order_digest": value.order_digest,
        "content_digest": value.content_digest,
    }


def _fraction_json(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _run_split(
    permit: ProductionPermit,
    *,
    split: str,
    controllers: Sequence[ControllerSpec],
    bindings: Mapping[str, str],
    lambda_accumulators: Sequence[OrderedNeumaierAccumulator] | None,
    retain_physical: set[tuple[str, int]],
    cross_maps: tuple[ControllerSpec, ControllerSpec] | None = None,
) -> tuple[list[list[object]], list[int]]:
    """Run one exact split; the sole host call is the C++ batch API."""

    root = permit.result_root
    replicate_endpoints_by_controller: list[list[object]] = [[] for _ in controllers]
    total_updates = [0 for _ in controllers]
    for replicate in range(CAL_REPLICATES if split == "CAL" else HOLD_REPLICATES):
        pending = list(_pending_controller_indices(root, split, replicate, controllers, retain_physical))
        block_rows: list[list[dict[str, object]]] = [
            [
                {
                    "block": block,
                    "template": (replicate + 3 * block) % 4,
                    "encounter_order": list(
                        ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")
                    ),
                }
                for block in range(20)
            ]
            for _ in controllers
        ]
        traces: list[list[object]] = [[] for _ in controllers]
        opportunity_sidecars: list[list[tuple[int, int, int, int, int, int]]] = [[] for _ in controllers]
        cross_sidecars: list[list[tuple[int, int, int, int]]] = [[] for _ in controllers]
        for block in range(20):
            result_by_class: dict[str, tuple[tuple[int, object], ...]] = {}
            for route_class in (
                ("SHORT", "LONG") if (replicate + block) % 2 == 0 else ("LONG", "SHORT")
            ):
                if not pending:
                    continue
                permit.assert_active()
                batch = BatchIdentity(split, replicate, block, route_class)
                carrier = _production_fixture(permit, batch); carrier.validate(permit)
                fixtures = tuple(
                    (carrier.spec, carrier.tape, controller, f"theta-{CONTROLLER_ORDINAL[controller]:03d}")
                    for controller in (controllers[index] for index in pending)
                )
                results = run_native_batch(fixtures)
                if len(results) != len(pending):
                    raise RuntimeError("native batch returned a substituted controller width")
                result_by_class[route_class] = tuple(zip(pending, results))
                for index, result in result_by_class[route_class]:
                    block_rows[index][block][route_class] = _encounter_summary(result)
                    total_updates[index] += result.voluntary_updates
                    controller_id = f"theta-{CONTROLLER_ORDINAL[controllers[index]]:03d}"
                    if (controller_id, replicate) in retain_physical:
                        traces[index].extend(result.ticks)
                    anchor = 0
                    route_code = 0 if route_class == "LONG" else 1
                    for tick in result.ticks:
                        if tick.legal_opportunity:
                            q_units = Fraction(tick.rate_numerator, tick.rate_denominator) * 1024
                            if q_units.denominator != 1: raise RuntimeError("native rate left 1/1024 grid")
                            opportunity_sidecars[index].append((block, route_code, tick.tick, q_units.numerator, int(tick.action == "JOINT-UPDATE"), float_bits(tick.event_lambda)))
                            if cross_maps is not None:
                                scored_ticks = 32 if route_class == "SHORT" else 128
                                remaining = Fraction(scored_ticks - tick.scored_index, scored_ticks)
                                age = min(Fraction(tick.scored_index - anchor, 128), Fraction(1))
                                diff = controller_rate_fraction(cross_maps[0], route_class[0], remaining, age) - controller_rate_fraction(cross_maps[1], route_class[0], remaining, age)
                                units = diff * 1024
                                if units.denominator != 1:
                                    raise RuntimeError("FLEX/TWO cross difference left the 1/1024 grid")
                                cross_sidecars[index].append((block, route_code, tick.tick, units.numerator))
                        if tick.action == "JOINT-UPDATE" and tick.scored:
                            anchor = tick.scored_index
            if lambda_accumulators is not None:
                # Coordinate encoding orders LONG before SHORT (field length 4 before 5),
                # then tick bytes.  Feed only realized legal opportunities in that order.
                for route_class in ("LONG", "SHORT"):
                    batch = BatchIdentity(split, replicate, block, route_class)
                    for index, result in result_by_class.get(route_class, ()):
                        opportunity_rows = []
                        for tick in result.ticks:
                            if tick.legal_opportunity:
                                coordinate = encode_coordinate(
                                    _coordinate(batch, tick=tick.tick, stream="action", lane=0)
                                )
                                opportunity_rows.append((coordinate, tick.event_lambda))
                        for coordinate, event_lambda in sorted(opportunity_rows):
                            lambda_accumulators[index].add(coordinate, event_lambda)
        for index, controller in enumerate(controllers):
            controller_id = f"theta-{CONTROLLER_ORDINAL[controller]:03d}"
            identity = CellIdentity(split, controller_id, replicate)
            if index not in pending:
                packet = read_cell_packet(root, identity)
                block_values = [Fraction(row["SHORT"]["valid_ticks"] + row["LONG"]["valid_ticks"],160) for row in packet["blocks"]]
                replicate_endpoints_by_controller[index].append(replicate_endpoints(block_values))
                total_updates[index] += packet["aggregate"]["voluntary_updates"]["SHORT"] + packet["aggregate"]["voluntary_updates"]["LONG"]
                if lambda_accumulators is not None:
                    replay_authority = _post_activity_replay_authority(root)
                    for coordinate, event_lambda, _, _ in _validated_opportunity_rows(root, identity, packet, replay_authority):
                        lambda_accumulators[index].add(coordinate, event_lambda)
                continue
            opportunity_ref = None
            if split in ("CAL", "HOLD"):
                def address(row):
                    block, route_code, tick = row[:3]
                    route_class = "LONG" if route_code == 0 else "SHORT"
                    return encode_coordinate(_coordinate(BatchIdentity(split, replicate, block, route_class), tick=tick, stream="action", lane=0))
                ordered_opportunities = sorted(opportunity_sidecars[index], key=address)
                payload = encode_opportunity_rows(ordered_opportunities)
                atomic_write_bytes(sidecar_path(root, identity, "opportunity"), payload, authorized_root=root)
                opportunity_ref = {"format": "ONLGR-H90-OPP-v2-BBBHBQ", "row_count": len(opportunity_sidecars[index]), "sha256": sha256_bytes(payload)}
            cross_ref = None
            if split == "HOLD" and cross_maps is not None:
                payload = encode_cross_rows(sorted(cross_sidecars[index], key=lambda row: row[:3]))
                atomic_write_bytes(sidecar_path(root, identity, "cross"), payload, authorized_root=root)
                cross_ref = {"format": "ONLGR-H90-CROSS-v1-BBBh", "row_count": len(cross_sidecars[index]), "sha256": sha256_bytes(payload)}
            packet = build_cell_packet(
                identity,
                bindings=bindings,
                blocks=block_rows[index],
                trace_retained=(controller_id, replicate) in retain_physical,
                opportunity_ledger=opportunity_ref,
                cross_eval_ledger=cross_ref,
            )
            from .serialization import write_cell_packet

            if (controller_id, replicate) in retain_physical:
                _write_trace(root, identity, traces[index])
            write_cell_packet(root, packet)
            _seal_cell_transaction(root, identity, trace_required=(controller_id,replicate) in retain_physical)
            block_values = [
                Fraction(row["SHORT"]["valid_ticks"] + row["LONG"]["valid_ticks"], 160)  # type: ignore[index,operator]
                for row in block_rows[index]
            ]
            replicate_endpoints_by_controller[index].append(replicate_endpoints(block_values))
    return replicate_endpoints_by_controller, total_updates


def _pending_controller_indices(
    root: Path, split: str, replicate: int,
    controller_set: Sequence[ControllerSpec], retain_physical: set[tuple[str, int]],
) -> tuple[int, ...]:
    """Resume frontier: committed same-coordinate cells are never resimulated."""

    pending = []
    for index, controller in enumerate(controller_set):
        controller_id = f"theta-{CONTROLLER_ORDINAL[controller]:03d}"
        identity = CellIdentity(split, controller_id, replicate)
        required = [cell_path(root, identity), sidecar_path(root, identity, "opportunity")]
        if split == "HOLD": required.append(sidecar_path(root, identity, "cross"))
        if (controller_id, replicate) in retain_physical:
            required.append(root / "private-traces" / split / controller_id / f"replicate-{replicate:03d}.json")
        required.append(_cell_commit_path(root,identity))
        if not all(path.is_file() for path in required): pending.append(index)
    return tuple(pending)


def run_full_panel(
    permit: ProductionPermit,
    *,
    source_set_sha256: str,
    config_sha256: str,
    schema_sha256: str,
) -> dict[str, object]:
    """Execute CAL then HOLD in native batches and seal one blinded package."""

    if permit._token is not _ADMISSION_TOKEN:
        raise ProductionAdmissionError("fixture admission cannot execute the production panel")
    root = initialize_private_panel(
        permit,
        source_set_sha256=source_set_sha256,
        config_sha256=config_sha256,
        schema_sha256=schema_sha256,
    )
    panel = _load_exact_document(root / "PANEL.json")
    _write_activity_intent(permit)
    bindings = panel["bindings"]
    assert isinstance(bindings, Mapping)
    cal_trace = {(controller, replicate) for controller in ("theta-000", "theta-063") for replicate in range(8)}
    accumulators = [OrderedNeumaierAccumulator() for _ in CONTROLLER_REGISTRY]
    endpoints, updates = _run_split(
        permit,
        split="CAL",
        controllers=CONTROLLER_REGISTRY,
        bindings=bindings,  # type: ignore[arg-type]
        lambda_accumulators=accumulators,
        retain_physical=cal_trace,
    )
    summaries: dict[ControllerSpec, CalibrationSummary] = {}
    serialized_summaries: dict[str, object] = {}
    for index, controller in enumerate(CONTROLLER_REGISTRY):
        endpoint = panel_endpoints(endpoints[index])  # type: ignore[arg-type]
        proof = accumulators[index].finalize()
        summary = CalibrationSummary(endpoint.mean_value, endpoint.tail_value, updates[index], proof)
        summaries[controller] = summary
        serialized_summaries[f"theta-{index:03d}"] = {
            "mean_value": _fraction_json(summary.mean_value),
            "tail_value": _fraction_json(summary.tail_value),
            "voluntary_updates": summary.voluntary_updates,
            "mean_lambda": _mean_proof_json(proof),
        }
    global_best = select_global(summaries)
    two = select_two_stratum(summaries)
    flex = select_flex(summaries)
    selectors = selector_ledger(
        global_best=global_best,
        two_stratum=two,
        flex=flex,
        calibration_summaries=serialized_summaries,
    )
    aliases = alias_ledger(global_best=global_best, two_stratum=two, flex=flex)
    atomic_write_once(root / "SELECTORS.json", selectors, authorized_root=root)
    atomic_write_once(root / "ALIASES.json", aliases, authorized_root=root)
    physical_ids = aliases["unique_physical_maps"]
    assert isinstance(physical_ids, list)
    hold_controllers = tuple(CONTROLLER_REGISTRY[int(controller_id[6:])] for controller_id in physical_ids)
    hold_trace = {(controller_id, replicate) for controller_id in physical_ids for replicate in range(8)}
    _run_split(
        permit,
        split="HOLD",
        controllers=hold_controllers,
        bindings=bindings,  # type: ignore[arg-type]
        lambda_accumulators=None,
        retain_physical=hold_trace,
        cross_maps=(flex, two),
    )
    trace_plan = retained_trace_plan(aliases["rows"])  # type: ignore[arg-type]
    atomic_write_once(root / "TRACE_INDEX.json", trace_plan, authorized_root=root)
    return seal_complete_package(root)


def selector_ledger(
    *, global_best, two_stratum, flex, calibration_summaries: Mapping[str, object]
) -> dict[str, object]:
    """Seal selected identities once; held-out facts are not accepted here."""

    from .controllers import CONTROLLER_ORDINAL

    for controller in (global_best, two_stratum, flex):
        if controller not in CONTROLLER_ORDINAL:
            raise ValueError("selector identity is outside the immutable registry")
    if set(calibration_summaries) != {f"theta-{i:03d}" for i in range(192)}:
        raise ValueError("selector ledger requires all 192 calibration summaries")
    return {
        "schema": SELECTOR_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "calibration_complete_before_selection": True,
        "selected_once": True,
        "held_out_facts_used": False,
        "selected": {
            "GLOBAL-BEST": f"theta-{CONTROLLER_ORDINAL[global_best]:03d}",
            "TWO-STRATUM/C*": f"theta-{CONTROLLER_ORDINAL[two_stratum]:03d}",
            "FLEX-CONTAIN": f"theta-{CONTROLLER_ORDINAL[flex]:03d}",
        },
        "calibration_summaries": dict(calibration_summaries),
    }


def alias_ledger(*, global_best, two_stratum, flex) -> dict[str, object]:
    rows = []
    for row in identity_preserving_alias_ledger(
        global_best=global_best, two_stratum=two_stratum, flex=flex
    ):
        value = asdict(row)
        value["exact_aliases"] = list(row.exact_aliases)
        rows.append(value)
    return {
        "schema": ALIAS_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "logical_tag_order": list(LOGICAL_HELD_OUT_TAGS),
        "rows": rows,
        "unique_physical_maps": sorted({row["physical_map_id"] for row in rows}),
        "trajectory_deduplication": "exact_coefficient_identity_only",
    }


def _load_exact_document(path: Path) -> dict[str, object]:
    encoded = Path(path).read_bytes()
    try:
        value = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SerializationError(f"invalid JSON artifact: {path}") from exc
    if canonical_json_bytes(value) != encoded:
        raise SerializationError(f"artifact is not canonical JSON plus LF: {path}")
    return value


def _load_aliases(root: Path) -> tuple[dict[str, object], tuple[str, ...]]:
    alias = _load_exact_document(root / "ALIASES.json")
    if (
        alias.get("schema") != ALIAS_SCHEMA
        or alias.get("logical_tag_order") != list(LOGICAL_HELD_OUT_TAGS)
        or not isinstance(alias.get("rows"), list)
    ):
        raise SerializationError("alias ledger is absent or malformed")
    rows = alias["rows"]
    if tuple(row.get("logical_tag") for row in rows) != LOGICAL_HELD_OUT_TAGS:
        raise SerializationError("alias ledger logical tags differ")
    unique = tuple(sorted({str(row["physical_map_id"]) for row in rows}))
    if not 1 <= len(unique) <= 5 or alias.get("unique_physical_maps") != list(unique):
        raise SerializationError("alias ledger unique physical map set differs")
    return alias, unique


def _rational(value: object, label: str) -> Fraction:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        or value[1] <= 0
    ):
        raise SerializationError(f"{label} is not a canonical rational pair")
    exact = Fraction(value[0], value[1])
    if [exact.numerator, exact.denominator] != value or not Fraction(0) <= exact <= Fraction(1):
        raise SerializationError(f"{label} rational is not reduced or bounded")
    return exact


def _validate_selector_alias_identity(
    selector: Mapping[str, object], alias: Mapping[str, object]
) -> None:
    summaries = selector.get("calibration_summaries")
    selected = selector.get("selected")
    if not isinstance(summaries, Mapping) or not isinstance(selected, Mapping):
        raise SerializationError("selector summaries or selected identities are absent")
    parsed: dict[str, tuple[Fraction, Fraction, int, float]] = {}
    for index in range(192):
        controller_id = f"theta-{index:03d}"
        row = summaries.get(controller_id)
        if not isinstance(row, Mapping) or set(row) != {
            "mean_value", "tail_value", "voluntary_updates", "mean_lambda"
        }:
            raise SerializationError("selector summary schema differs")
        updates = row["voluntary_updates"]
        if isinstance(updates, bool) or not isinstance(updates, int) or updates < 0:
            raise SerializationError("selector update count is invalid")
        proof = row["mean_lambda"]
        if not isinstance(proof, Mapping) or set(proof) != {
            "value", "row_count", "order_digest", "content_digest"
        }:
            raise SerializationError("selector mean-lambda proof schema differs")
        mean_lambda = proof["value"]
        if not isinstance(mean_lambda, float) or not math.isfinite(mean_lambda) or mean_lambda < 0:
            raise SerializationError("selector mean-lambda value is invalid")
        if isinstance(proof["row_count"], bool) or not isinstance(proof["row_count"], int) or proof["row_count"] <= 0:
            raise SerializationError("selector mean-lambda row count is invalid")
        _sha(proof["order_digest"], "mean-lambda order")
        _sha(proof["content_digest"], "mean-lambda content")
        parsed[controller_id] = (
            _rational(row["mean_value"], "selector mean"),
            _rational(row["tail_value"], "selector tail"),
            updates,
            mean_lambda,
        )
    diagonal = tuple(i * 8 + i for i in range(8))
    global_index = min(
        diagonal,
        key=lambda index: (
            -parsed[f"theta-{index:03d}"][0], -parsed[f"theta-{index:03d}"][1],
            parsed[f"theta-{index:03d}"][2], Fraction(index // 8, 8),
        ),
    )
    two_index = min(
        range(64),
        key=lambda index: (
            -parsed[f"theta-{index:03d}"][0], -parsed[f"theta-{index:03d}"][1],
            parsed[f"theta-{index:03d}"][2],
            rate_lambda(Fraction(index // 8, 8)) + rate_lambda(Fraction(index % 8, 8)),
            index // 8, index % 8,
        ),
    )
    flex_index = min(
        range(192),
        key=lambda index: (
            -parsed[f"theta-{index:03d}"][0], -parsed[f"theta-{index:03d}"][1],
            parsed[f"theta-{index:03d}"][2], parsed[f"theta-{index:03d}"][3],
            coefficient_tuple(CONTROLLER_REGISTRY[index]),
        ),
    )
    expected_selected = {
        "GLOBAL-BEST": f"theta-{global_index:03d}",
        "TWO-STRATUM/C*": f"theta-{two_index:03d}",
        "FLEX-CONTAIN": f"theta-{flex_index:03d}",
    }
    if dict(selected) != expected_selected:
        raise SerializationError("sealed selectors differ from exact complete-calibration ordering")
    expected_alias = alias_ledger(
        global_best=CONTROLLER_REGISTRY[global_index],
        two_stratum=CONTROLLER_REGISTRY[two_index],
        flex=CONTROLLER_REGISTRY[flex_index],
    )
    if dict(alias) != expected_alias:
        raise SerializationError("logical aliases differ from exact selected controller identity")


def _validate_opportunity_structure(identity: CellIdentity, cell: Mapping[str, object], rows):
    keys = [(row[0],row[1],row[2]) for row in rows]
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise SerializationError("opportunity sidecar addresses are duplicated or out of canonical order")
    for block in range(20):
        for route_code, route_class in ((0,"LONG"),(1,"SHORT")):
            subset = [row for row in rows if row[0] == block and row[1] == route_code]
            encounter = cell["blocks"][block][route_class]  # type: ignore[index]
            if len(subset) != encounter["opportunity_rows"] or sum(row[4] for row in subset) != encounter["voluntary_updates"] or len(subset)-sum(row[4] for row in subset) != encounter["voluntary_keeps"]:
                raise SerializationError("opportunity sidecar action counts differ from retained encounter summary")
            scored_ticks = 128 if route_class == "LONG" else 32
            if any(row[2]-16 not in range(scored_ticks) for row in subset):
                raise SerializationError("opportunity sidecar row is outside scored time")


def _validate_cross_rows(rows, expected_rows) -> None:
    if tuple(rows) != tuple(expected_rows) or len({row[:3] for row in rows}) != len(rows):
        raise SerializationError("HOLD cross-evaluation ledger differs from exact state replay")


def _validated_opportunity_rows(root: Path, identity: CellIdentity, cell: Mapping[str, object], authority: PostActivityReplayAuthority):
    ref = cell.get("opportunity_ledger")
    if not isinstance(ref, Mapping): raise SerializationError("cell lacks opportunity ledger")
    payload = sidecar_path(root, identity, "opportunity").read_bytes(); rows = decode_opportunity_rows(payload)
    if sha256_bytes(payload) != ref["sha256"] or len(rows) != ref["row_count"]: raise SerializationError("opportunity sidecar differs from cell binding")
    controller = CONTROLLER_REGISTRY[int(identity.physical_controller_id[6:])]
    _validate_opportunity_structure(identity, cell, rows)
    validated = []
    for block in range(20):
        for route_code, route_class in ((0,"LONG"),(1,"SHORT")):
            anchor = 0
            subset = sorted((row for row in rows if row[0] == block and row[1] == route_code), key=lambda row: row[2])
            for _, _, tick, q_units, updated, lambda_bits in subset:
                scored_index = tick - 16; scored_ticks = 128 if route_class == "LONG" else 32
                remaining = Fraction(scored_ticks-scored_index, scored_ticks); age = min(Fraction(scored_index-anchor,128), Fraction(1))
                expected_q = controller_rate_fraction(controller, route_class[0], remaining, age)
                batch = BatchIdentity(identity.split, identity.replicate, block, route_class)
                action_coordinate = _coordinate(batch,tick=tick,stream="action",lane=0)
                expected_update = int(_action_decision(_replay_word(authority, action_coordinate), expected_q))
                if expected_q*1024 != q_units or event_transform_bits(expected_q)[1] != lambda_bits or updated != expected_update:
                    raise SerializationError("opportunity sidecar rate/event/action replay differs")
                validated.append((encode_coordinate(_coordinate(batch,tick=tick,stream="action",lane=0)), float_from_bits(lambda_bits), remaining, age))
                if updated: anchor = scored_index
    if len(validated) != len(rows): raise SerializationError("opportunity sidecar has invalid block/class rows")
    return tuple(validated)


def _validate_retained_trace(
    root: Path, identity: CellIdentity, trace: Mapping[str, object],
    cell: Mapping[str, object], authority: PostActivityReplayAuthority,
) -> None:
    """Bind every retained trace encounter to its cell and opportunity evidence."""

    ticks = trace.get("ticks")
    if not isinstance(ticks, list) or len(ticks) != 3840:
        raise SerializationError("private trace does not contain exactly 3,840 ticks")
    opportunity_rows = decode_opportunity_rows(
        sidecar_path(root, identity, "opportunity").read_bytes()
    )
    offset = 0
    for block_index, block in enumerate(cell["blocks"]):  # type: ignore[index]
        for route_class in block["encounter_order"]:
            scored = 32 if route_class == "SHORT" else 128
            physical = scored + 16
            rows = ticks[offset:offset + physical]
            offset += physical
            if any(not isinstance(row, Mapping) or row.get("tick") != tick for tick, row in enumerate(rows)):
                raise SerializationError("private trace tick order differs from its encounter")
            batch = BatchIdentity(identity.split, identity.replicate, block_index, route_class)
            spec, tape = _fixture_for_replay(authority, batch)
            controller = CONTROLLER_REGISTRY[int(identity.physical_controller_id[6:])]
            _authenticate_replay_runtime(authority)
            replayed = run_native_batch(((spec, tape, controller, identity.physical_controller_id),))
            _authenticate_replay_runtime(authority)
            if len(replayed) != 1 or _trace_safe([asdict(row) for row in replayed[0].ticks]) != rows:
                raise SerializationError("private trace differs from authenticated exact native replay")
            summary = block[route_class]
            if _encounter_summary(replayed[0]) != summary:
                raise SerializationError("retained encounter summary differs from authenticated exact native replay")
            sums = {
                "valid_ticks": sum(bool(row["service"]) for row in rows),
                "tracking_valid_ticks": sum(bool(row["tracking_valid"]) for row in rows),
                "packet_valid_ticks": sum(bool(row["packet_valid"]) for row in rows),
                "raw_link_success_tr": sum(bool(row["raw_trial_tr"]) for row in rows),
                "raw_link_success_rb": sum(bool(row["raw_trial_rb"]) for row in rows),
                "blackout_ticks": sum(bool(row["blackout_active"]) for row in rows),
                "lockout_ticks": sum(bool(row["lockout_active"]) for row in rows),
                "voluntary_updates": sum(row["action"] == "JOINT-UPDATE" for row in rows),
                "voluntary_keeps": sum(row["legal_opportunity"] and row["action"] == "KEEP" for row in rows),
                "opportunity_rows": sum(bool(row["legal_opportunity"]) for row in rows),
                "safety_overrides": sum(bool(row["safety_override"]) for row in rows),
            }
            if any(summary[key] != value for key, value in sums.items()):
                raise SerializationError("private trace counts differ from retained encounter summary")
            if summary["tracker_energy_final"] != rows[-1]["tracker_energy_after"] or summary["relay_energy_final"] != rows[-1]["relay_energy_after"]:
                raise SerializationError("private trace energy differs from retained encounter summary")
            failures = {
                "terrain_penetrations": int(any(row["terrain_penetration"] for row in rows)),
                "geofence_exits": int(any(row["geofence_exit"] for row in rows)),
                "separation_breaches": int(any(row["separation_breach"] for row in rows)),
                "no_safe_control": int(any(row["no_safe_control"] for row in rows)),
                "no_planner_solution": int(any(row["no_planner_solution"] for row in rows)),
                "battery_exhaustions": int(any(row["battery_exhausted"] for row in rows)),
                "numerical_faults": 0,
            }
            if failures != summary["failures"]:
                raise SerializationError("private trace hard-safety facts differ from retained encounter summary")
            route_code = 1 if route_class == "SHORT" else 0
            retained = [row for row in opportunity_rows if row[0] == block_index and row[1] == route_code]
            observed = []
            for row in rows:
                if not row["legal_opportunity"]:
                    continue
                if row["scored"] is not True or row["action_uniform_consumed"] is not True:
                    raise SerializationError("private trace opportunity is not a scored consumed action")
                coordinate = _coordinate(batch, tick=row["tick"], stream="action", lane=0)
                if row["action_uniform"] != _replay_word(authority, coordinate):
                    raise SerializationError("private trace action uniform differs from coordinate replay")
                q = Fraction(row["rate_numerator"], row["rate_denominator"])
                expected_lambda, expected_probability = event_transform_bits(q)[1:]
                if float_bits(row["event_lambda"]) != expected_lambda or float_bits(row["event_probability"]) != expected_probability:
                    raise SerializationError("private trace event transform differs from exact replay")
                observed.append((block_index, route_code, row["tick"], int(q*1024), int(row["action"] == "JOINT-UPDATE"), expected_lambda))
            if observed != retained:
                raise SerializationError("private trace opportunities differ from retained sidecar")
    if offset != len(ticks):
        raise SerializationError("private trace encounter partition differs")


def validate_complete_package(root: Path) -> dict[str, object]:
    """Authenticate every mandatory cell before any endpoint consumer is called."""

    root = Path(root)
    panel = _load_exact_document(root / "PANEL.json")
    expected_panel = {
        "schema": PANEL_SCHEMA, "direction_id": DIRECTION_ID, "stage": STAGE,
        "card_revision": CARD_REVISION, "host": HOST_ID, "private_blinded": True,
        "partial_results_exposed": False, "calibration_maps": 192,
        "calibration_replicates": 48, "held_out_replicates": 128,
        "maximum_unique_held_out_maps": 5,
        "controller_replicates": TOTAL_CONTROLLER_REPLICATES,
        "physical_ticks": TOTAL_PHYSICAL_TICKS,
    }
    if any(panel.get(key) != value for key, value in expected_panel.items()) or set(panel) != set(expected_panel) | {"bindings"}:
        raise SerializationError("private panel manifest differs")
    panel_bindings = panel.get("bindings")
    if not isinstance(panel_bindings, Mapping) or set(panel_bindings) != {
        "preactivity_freeze_sha256", "coordinate_binding_sha256", "lease_scope_sha256",
        "backend_receipt_sha256", "source_set_sha256", "config_sha256", "schema_sha256",
    }:
        raise SerializationError("panel binding ledger is absent or malformed")
    for key, value in panel_bindings.items():
        _sha(value, f"panel {key}")
    backend = _load_exact_document(root / "BACKEND_RECEIPT.json")
    if document_sha256(backend) != panel_bindings["backend_receipt_sha256"] or any(
        backend.get(key) != value for key, value in {
            "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
            "component": ONLGR_HEADLAND90_R03_CAL_HOLD_FULL_HOST,
            "backend": "cpp", "batch_width": SHARED_GUARD_BATCH_WIDTH,
            "full_reset_step_cpp": True, "python_fallback": False,
        }.items()
    ) or not isinstance(backend.get("native"), Mapping):
        raise SerializationError("backend receipt differs from the authenticated full-host boundary")
    _sha(backend["native"].get("artifact_sha256"), "backend native artifact")
    lease_paths = tuple((root / "lease-receipts").glob("*.json"))
    if not lease_paths:
        raise SerializationError("panel has no retained direction-lease receipt")
    lease_digests = {}
    for path in lease_paths:
        lease = _load_exact_document(path)
        digest = validate_direction_lease(lease, result_root=root, require_active=False)
        if path.stem != digest or lease_scope_identity(lease, result_root=root) != panel_bindings["lease_scope_sha256"]:
            raise SerializationError("retained direction lease differs from its stable panel scope")
        lease_digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    replay_authority = _post_activity_replay_authority(root)
    selector = _load_exact_document(root / "SELECTORS.json")
    if (
        selector.get("schema") != SELECTOR_SCHEMA
        or selector.get("selected_once") is not True
        or not isinstance(selector.get("calibration_summaries"), Mapping)
        or set(selector["calibration_summaries"]) != {f"theta-{index:03d}" for index in range(192)}
    ):
        raise SerializationError("immutable selector ledger differs")
    alias, unique_hold = _load_aliases(root)
    _validate_selector_alias_identity(selector, alias)

    expected = {
        CellIdentity("CAL", f"theta-{ordinal:03d}", replicate)
        for ordinal in range(192)
        for replicate in range(48)
    }
    expected.update(
        CellIdentity("HOLD", controller_id, replicate)
        for controller_id in unique_hold
        for replicate in range(128)
    )
    actual_paths = tuple((root / "private-cells").glob("*/*/replicate-*.json"))
    if any(root.rglob("*.pending")):
        raise SerializationError("package contains an uncommitted staging artifact")
    actual: set[CellIdentity] = set()
    retained_cells: dict[CellIdentity, Mapping[str, object]] = {}
    cell_digests: dict[str, str] = {}
    for path in actual_paths:
        relative = path.relative_to(root).as_posix()
        value = _load_exact_document(path)
        identity = validate_cell_packet(value)
        if cell_path(root, identity).resolve() != path.resolve():
            raise SerializationError("cell path differs from its retained identity")
        if value.get("bindings") != panel_bindings:
            raise SerializationError("cell binding differs from the private panel")
        if identity in actual:
            raise SerializationError("duplicate cell identity")
        actual.add(identity)
        retained_cells[identity] = value
        cell_digests[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        missing, extra = expected - actual, actual - expected
        raise SerializationError(
            f"package cell set is incomplete or substituted: missing={len(missing)}, extra={len(extra)}"
        )
    expected_commits = {_cell_commit_path(root,identity).resolve() for identity in expected}
    actual_commits = {path.resolve() for path in (root / "private-commits").rglob("*.json")}
    if actual_commits != expected_commits:
        raise SerializationError("cell transaction commit inventory differs from the complete cell set")
    for identity, cell in retained_cells.items():
        commit = _load_exact_document(_cell_commit_path(root,identity))
        expected_commit = _cell_commit_document(root,identity,trace_required=bool(cell["trace_retained"]))
        if commit != expected_commit:
            raise SerializationError("cell transaction commit differs from its atomic artifact set")
    calibration_summaries = selector["calibration_summaries"]
    assert isinstance(calibration_summaries, Mapping)
    for ordinal in range(192):
        replicate_rows = []
        updates = 0
        proof_accumulator = OrderedNeumaierAccumulator()
        for replicate in range(48):
            cell = retained_cells[CellIdentity("CAL", f"theta-{ordinal:03d}", replicate)]
            blocks = cell["blocks"]
            assert isinstance(blocks, list)
            values = []
            for block in blocks:
                assert isinstance(block, Mapping)
                short, long = block["SHORT"], block["LONG"]
                assert isinstance(short, Mapping) and isinstance(long, Mapping)
                values.append(Fraction(short["valid_ticks"] + long["valid_ticks"], 160))  # type: ignore[operator]
                updates += short["voluntary_updates"] + long["voluntary_updates"]  # type: ignore[operator]
            replicate_rows.append(replicate_endpoints(values))
            reconstructed = _validated_opportunity_rows(root, CellIdentity("CAL", f"theta-{ordinal:03d}", replicate), cell, replay_authority)
            for coordinate, event_lambda, _, _ in sorted(reconstructed):
                proof_accumulator.add(coordinate, event_lambda)
        recomputed = panel_endpoints(replicate_rows)
        retained = calibration_summaries[f"theta-{ordinal:03d}"]
        assert isinstance(retained, Mapping)
        if (
            _rational(retained["mean_value"], "selector mean") != recomputed.mean_value
            or _rational(retained["tail_value"], "selector tail") != recomputed.tail_value
            or retained["voluntary_updates"] != updates
        ):
            raise SerializationError("selector endpoints or update count differ from retained CAL cells")
        proof = proof_accumulator.finalize()
        retained_proof = retained["mean_lambda"]
        assert isinstance(retained_proof, Mapping)
        if retained_proof != _mean_proof_json(proof):
            raise SerializationError("selector mean-lambda proof differs from retained CAL opportunities")
    for identity, cell in retained_cells.items():
        if identity.split == "CAL" and cell.get("opportunity_ledger") is None:
            raise SerializationError("CAL cell lacks its opportunity proof sidecar")
        if identity.split == "HOLD" and cell.get("cross_eval_ledger") is None:
            raise SerializationError("HOLD cell lacks its FLEX/TWO cross-evaluation sidecar")
        if identity.split == "HOLD":
            opportunities = _validated_opportunity_rows(root, identity, cell, replay_authority)
            ref = cell["cross_eval_ledger"]
            assert isinstance(ref, Mapping)
            payload = sidecar_path(root, identity, "cross").read_bytes()
            rows = decode_cross_rows(payload)
            if sha256_bytes(payload) != ref["sha256"] or len(rows) != ref["row_count"]:
                raise SerializationError("HOLD cross-evaluation sidecar differs from its cell binding")
            selected_ids = selector["selected"]
            flex_map = CONTROLLER_REGISTRY[int(selected_ids["FLEX-CONTAIN"][6:])]
            two_map = CONTROLLER_REGISTRY[int(selected_ids["TWO-STRATUM/C*"][6:])]
            expected_cross = {}
            state_rows = opportunities
            for raw, state in zip(sorted(decode_opportunity_rows(sidecar_path(root, identity, "opportunity").read_bytes()), key=lambda r:(r[0],r[1],r[2])), state_rows):
                diff = controller_rate_fraction(flex_map, "L" if raw[1]==0 else "S", state[2], state[3]) - controller_rate_fraction(two_map, "L" if raw[1]==0 else "S", state[2], state[3])
                expected_cross[(raw[0],raw[1],raw[2])] = int(diff*1024)
            expected_rows = tuple(
                (block, route, tick, value)
                for (block, route, tick), value in sorted(expected_cross.items())
            )
            _validate_cross_rows(rows, expected_rows)
    expected_sidecars = {
        sidecar_path(root, identity, "opportunity").resolve()
        for identity in retained_cells
    } | {
        sidecar_path(root, identity, "cross").resolve()
        for identity in retained_cells if identity.split == "HOLD"
    }
    actual_sidecars = {path.resolve() for path in (root / "private-sidecars").rglob("*") if path.is_file()}
    if actual_sidecars != expected_sidecars:
        raise SerializationError("sidecar inventory contains an absent, substituted, or unreferenced object")
    trace = _load_exact_document(root / "TRACE_INDEX.json")
    if trace != retained_trace_plan(alias["rows"]):  # type: ignore[arg-type]
        raise SerializationError("retained trace index differs from the prospective plan")
    expected_traces = {
        (str(row["split"]), str(row["physical_controller_id"]), int(row["replicate"]))
        for row in (*trace["calibration_physical"], *trace["held_out_logical"])
    }
    trace_paths = tuple((root / "private-traces").glob("*/*/replicate-*.json"))
    actual_traces: set[tuple[str, str, int]] = set()
    trace_digests: dict[str, str] = {}
    for path in trace_paths:
        value = _load_exact_document(path)
        if value.get("schema") != "ONLGR-HEADLAND90-R03-PRIVATE-TRACE-v1":
            raise SerializationError("private trace schema differs")
        cell = value.get("cell")
        if not isinstance(cell, Mapping):
            raise SerializationError("private trace cell identity is absent")
        identity = CellIdentity.from_dict(cell)
        key = (identity.split, identity.physical_controller_id, identity.replicate)
        expected_path = (
            root / "private-traces" / identity.split / identity.physical_controller_id
            / f"replicate-{identity.replicate:03d}.json"
        )
        if path.resolve() != expected_path.resolve():
            raise SerializationError("private trace path differs from its identity")
        if value.get("complete_controller_replicate") is not True:
            raise SerializationError("private trace is not complete")
        retained_cell = retained_cells.get(identity)
        if retained_cell is None:
            raise SerializationError("private trace has no authenticated retained cell")
        _validate_retained_trace(root, identity, value, retained_cell, replay_authority)
        actual_traces.add(key)
        trace_digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_traces != expected_traces:
        raise SerializationError("private trace set differs from the prospective plan")
    return {
        "schema": COMPLETE_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "calibration_cells": CAL_CONTROLLER_REPLICATES,
        "held_out_physical_cells": len(unique_hold) * 128,
        "logical_held_out_cells": 5 * 128,
        "unique_held_out_maps": list(unique_hold),
        "cell_set_sha256": document_sha256(dict(sorted(cell_digests.items()))),
        "selectors_sha256": document_sha256(selector),
        "aliases_sha256": document_sha256(alias),
        "trace_index_sha256": document_sha256(trace),
        "trace_inventory_sha256": document_sha256(dict(sorted(trace_digests.items()))),
        "lease_receipt_inventory_sha256": document_sha256(dict(sorted(lease_digests.items()))),
        "activity_intent_sha256": hashlib.sha256((root / "ACTIVITY_INTENT.json").read_bytes()).hexdigest(),
        "activity_started_sha256": hashlib.sha256((root / "ACTIVITY_STARTED.json").read_bytes()).hexdigest(),
        "complete": True,
        "partial_results_exposed": False,
    }


def seal_complete_package(root: Path) -> dict[str, object]:
    complete = validate_complete_package(root)
    atomic_write_once(Path(root) / "COMPLETE.json", complete, authorized_root=root)
    return complete


def _common_nonidentification_reason(
    *, nonharm: bool, calibration_headroom: bool, heldout_mean: bool,
    heldout_tail: bool, support: bool,
) -> str | None:
    """Return the card's first failed GLOBAL gate in its frozen order."""

    for passed, reason in (
        (nonharm, "GLOBAL_SELECTED_CONTROLLER_NONHARM_FAILED"),
        (calibration_headroom, "GLOBAL_CALIBRATION_HEADROOM_FAILED"),
        (heldout_mean, "GLOBAL_HELDOUT_MEAN_COMPETENCE_FAILED"),
        (heldout_tail, "GLOBAL_HELDOUT_TAIL_COMPETENCE_FAILED"),
        (support, "GLOBAL_VOLUNTARY_ACTION_SUPPORT_FAILED"),
    ):
        if not passed:
            return reason
    return None


def _two_nonidentification_reason(
    *, response: bool, support: bool, nonharm: bool, reciprocal: bool,
) -> str | None:
    """Return the card's first failed TWO gate in its frozen order."""

    for passed, reason in (
        (response, "TWO_RATE_RESPONSE_NOT_IDENTIFIED"),
        (support, "TWO_VOLUNTARY_ACTION_SUPPORT_FAILED"),
        (nonharm, "TWO_SELECTED_CONTROLLER_NONHARM_FAILED"),
        (reciprocal, "RECIPROCAL_CONTROLS_INVALID"),
    ):
        if not passed:
            return reason
    return None


def _flex_nonidentification_reason(
    *, support: bool, nonharm: bool, algebraically_distinct: bool,
    realized_distinct: bool, timing_member: bool,
) -> str | None:
    for passed, reason in (
        (support, "FLEX_VOLUNTARY_ACTION_SUPPORT_FAILED"),
        (nonharm, "FLEX_SELECTED_CONTROLLER_NONHARM_FAILED"),
        (algebraically_distinct, "FLEX_NOT_ALGEBRAICALLY_DISTINCT"),
        (realized_distinct, "FLEX_REALIZED_SUPPORT_NOT_DISTINCT"),
        (timing_member, "FLEX_NOT_TIMING_MEMBER"),
    ):
        if not passed:
            return reason
    return None


def _complete_panel_analysis(root: Path) -> dict[str, object]:
    selector = _load_exact_document(root / "SELECTORS.json")
    aliases, _ = _load_aliases(root)
    tag_to_id = {row["logical_tag"]: row["physical_map_id"] for row in aliases["rows"]}

    def cell(split: str, controller_id: str, replicate: int):
        return read_cell_packet(root, CellIdentity(split, controller_id, replicate))

    def rep_facts(controller_id: str, replicate: int) -> dict[str, object]:
        packet = cell("HOLD", controller_id, replicate)
        blocks = packet["blocks"]
        pooled, short, long = [], [], []
        overrides = 0
        keeps = {"S": 0, "L": 0}; updates = {"S": 0, "L": 0}
        failures = {key: 0 for key in az.HardSafetyFacts.__dataclass_fields__}
        co = {key: 0 for key in (
            "tracking_valid_ticks", "packet_valid_ticks", "raw_link_success_tr",
            "raw_link_success_rb", "blackout_ticks", "lockout_ticks",
            "voluntary_updates", "voluntary_keeps", "safety_overrides",
        )}
        tracker_energy = []; relay_energy = []; update_energy = 0
        causes = {"terrain":0,"geofence":0,"separation":0}
        for block in blocks:
            s, l = block["SHORT"], block["LONG"]
            short.append(Fraction(s["valid_ticks"], 32)); long.append(Fraction(l["valid_ticks"], 128))
            pooled.append(Fraction(s["valid_ticks"] + l["valid_ticks"], 160))
            overrides += s["safety_overrides"] + l["safety_overrides"]
            keeps["S"] += s["voluntary_keeps"]; keeps["L"] += l["voluntary_keeps"]
            updates["S"] += s["voluntary_updates"]; updates["L"] += l["voluntary_updates"]
            for key in failures: failures[key] += s["failures"][key] + l["failures"][key]
            for row in (s, l):
                for key in co: co[key] += row[key]
                tracker_energy.append(row["tracker_energy_final"])
                relay_energy.append(row["relay_energy_final"])
                update_energy += row["update_energy_joules_per_uav"]
                for key in causes: causes[key] += row["override_causes"][key]
        ep = replicate_endpoints(pooled)
        return {"mean": ep.mean_value, "tail": ep.tail_value, "short": sum(short)/20, "long": sum(long)/20, "overrides": overrides, "keeps": keeps, "updates": updates, "failures": failures, "co": co, "override_causes":causes, "tracker_energy_final_sum":sum(tracker_energy), "relay_energy_final_sum":sum(relay_energy), "update_energy":update_energy}

    ids = set(tag_to_id.values())
    reps = {controller_id: [rep_facts(controller_id, r) for r in range(128)] for controller_id in ids}
    global_id, two_id, flex_id = tag_to_id["GLOBAL-BEST"], tag_to_id["TWO-STRATUM/C*"], tag_to_id["FLEX-CONTAIN"]
    cs_id, cl_id = tag_to_id["C_S<-L"], tag_to_id["C_L<-S"]

    def hard(split: str, controller_id: str, count: int) -> az.HardSafetyFacts:
        totals = {key: 0 for key in az.HardSafetyFacts.__dataclass_fields__}
        for replicate in range(count):
            packet = cell(split, controller_id, replicate)
            for key, value in packet["aggregate"]["failures"].items(): totals[key] += value
        return az.HardSafetyFacts(**totals)

    global_override = [row["overrides"] for row in reps[global_id]]
    override_ucbs = {controller_id: az.override_ucb95([row["overrides"] for row in reps[controller_id]], global_override) for controller_id in ids}
    def nonharm(controller_id: str, selected: bool = True) -> bool:
        ucb = override_ucbs[controller_id]
        return az.selected_controller_nonharm(hard("CAL", controller_id, 48), hard("HOLD", controller_id, 128), ucb) if selected else az.reciprocal_control_nonharm(hard("HOLD", controller_id, 128), ucb)

    def support(controller_id: str) -> dict[str, az.SupportFacts]:
        return {s: az.SupportFacts(sum(row["keeps"][s] for row in reps[controller_id]), sum(row["updates"][s] for row in reps[controller_id]), sum(row["keeps"][s] > 0 and row["updates"][s] > 0 for row in reps[controller_id])) for s in ("S", "L")}

    retained_summaries = selector["calibration_summaries"]
    global_cal = _rational(retained_summaries[global_id]["mean_value"], "global calibration mean")
    global_panel = az.PanelEndpoints(sum(row["mean"] for row in reps[global_id])/128, sum(row["tail"] for row in reps[global_id])/128)
    global_nonharm = nonharm(global_id); global_support = az.voluntary_support_adequate(support(global_id))
    global_ok = az.global_competent(selected_nonharm=global_nonharm, calibration_mean=global_cal, held_out_mean=global_panel.mean_value, held_out_tail=global_panel.tail_value, support_by_stratum=support(global_id))
    common_reason = _common_nonidentification_reason(
        nonharm=global_nonharm,
        calibration_headroom=1-global_cal >= Fraction(1,20),
        heldout_mean=global_panel.mean_value >= Fraction(1,4),
        heldout_tail=global_panel.tail_value >= Fraction(1,10),
        support=global_support,
    )

    two_index = int(two_id[6:]); q_s, q_l = Fraction(two_index // 8, 8), Fraction(two_index % 8, 8)
    def class_value(index: int, half: range, route: str) -> Fraction:
        total = 0
        for replicate in half:
            packet = cell("CAL", f"theta-{index:03d}", replicate)
            total += sum(block[route]["valid_ticks"] for block in packet["blocks"])
        return Fraction(total, len(half)*20*(32 if route == "SHORT" else 128))
    curves = {}; curve_values = {}
    for label, half in (("cal", range(48)), ("c1", range(24)), ("c2", range(24,48))):
        short_curve = {q: class_value(int(q*8)*8 + int(q_l*8), half, "SHORT") for q in controllers.Q}
        long_curve = {q: class_value(int(q_s*8)*8 + int(q*8), half, "LONG") for q in controllers.Q}
        curve_values[label] = (short_curve, long_curve)
        curves[label] = (az.conditional_maxima(short_curve), az.conditional_maxima(long_curve))
    response_ok = az.rate_response_identified(selected_short=q_s, selected_long=q_l, maxima_short_cal=curves["cal"][0], maxima_long_cal=curves["cal"][1], maxima_short_c1=curves["c1"][0], maxima_short_c2=curves["c2"][0], maxima_long_c1=curves["c1"][1], maxima_long_c2=curves["c2"][1])
    reciprocal_ok = nonharm(cs_id, False) and nonharm(cl_id, False)
    two_support = az.voluntary_support_adequate(support(two_id))
    two_nonharm = nonharm(two_id)
    two_ok = az.two_answerable(package_valid=True, global_is_competent=global_ok, response_identified=response_ok, support_adequate=two_support, selected_nonharm=two_nonharm, reciprocal_controls_valid=reciprocal_ok)
    two_reason = _two_nonidentification_reason(
        response=response_ok,
        support=two_support,
        nonharm=two_nonharm,
        reciprocal=reciprocal_ok,
    )

    def interval(left_id: str, right_id: str, field: str) -> az.PairedInterval:
        return az.paired_interval([reps[left_id][i][field] - reps[right_id][i][field] for i in range(128)])
    ds, dl = interval(two_id, cs_id, "short"), interval(two_id, cl_id, "long")
    dm, dtail = interval(two_id, global_id, "mean"), interval(two_id, global_id, "tail")
    two_gates = {"D_S": az.PositiveGate(ds.mean, ds.lower, ds.sample_sd, .02), "D_L": az.PositiveGate(dl.mean, dl.lower, dl.sample_sd, .02), "Delta_mean": az.PositiveGate(dm.mean, dm.lower, dm.sample_sd, .02), "Delta_tail": az.PositiveGate(dtail.mean, dtail.lower, dtail.sample_sd, .05)}

    flex_index = int(flex_id[6:]); flex_controller, two_controller = CONTROLLER_REGISTRY[flex_index], CONTROLLER_REGISTRY[two_index]
    cross_rows = []
    for controller_id in (flex_id, two_id):
        for replicate in range(128):
            packet = cell("HOLD", controller_id, replicate); ref = packet["cross_eval_ledger"]
            payload = sidecar_path(root, CellIdentity("HOLD", controller_id, replicate), "cross").read_bytes()
            if sha256_bytes(payload) != ref["sha256"]: raise SerializationError("HOLD cross sidecar digest differs")
            cross_rows.extend(decode_cross_rows(payload))
    f_diff = Fraction(sum(abs(row[3]) >= 32 for row in cross_rows), len(cross_rows)) if cross_rows else Fraction(0)
    a_diff = Fraction(sum(abs(row[3]) for row in cross_rows), 1024*len(cross_rows)) if cross_rows else Fraction(0)
    realized_distinct = f_diff >= Fraction(1,10) and a_diff >= Fraction(1,64)
    flex_support = az.voluntary_support_adequate(support(flex_id)); flex_nonharm = nonharm(flex_id)
    flex_algebraic = controllers.algebraically_distinct(flex_controller, two_controller); flex_timing = controllers.is_timing_member(flex_controller)
    flex_answerable = az.flex_adaptive_answerable(containment_answerable=az.flex_containment_answerable(package_valid=True, global_is_competent=global_ok, support_adequate=flex_support, selected_nonharm=flex_nonharm, algebraically_distinct=flex_algebraic, realized_support_distinct=realized_distinct), timing_member=flex_timing)
    flex_reason = _flex_nonidentification_reason(support=flex_support, nonharm=flex_nonharm, algebraically_distinct=flex_algebraic, realized_distinct=realized_distinct, timing_member=flex_timing)
    fmean, ftail = interval(flex_id, global_id, "mean"), interval(flex_id, global_id, "tail")
    flex_gates = {"Delta_FLEX_mean": az.PositiveGate(fmean.mean, fmean.lower, fmean.sample_sd, .02), "Delta_FLEX_tail": az.PositiveGate(ftail.mean, ftail.lower, ftail.sample_sd, .05)}
    rel_mean, rel_tail = interval(flex_id, two_id, "mean"), interval(flex_id, two_id, "tail")
    relation = az.flex_two_relation(rel_mean, rel_tail, flex_adaptive_answerable=flex_answerable, two_is_answerable=two_ok)
    outcome = az.evaluate_result_map(az.ResultMapFacts(common_reason, two_ok, two_reason, q_s, q_l, two_gates, flex_answerable, flex_gates, relation))
    def support_json(controller_id: str):
        return {key: asdict(value) for key, value in support(controller_id).items()}
    def coendpoint(controller_id: str):
        rows = reps[controller_id]
        counts = {key: sum(row["co"][key] for row in rows) for key in rows[0]["co"]}
        causes = {key:sum(row["override_causes"][key] for row in rows) for key in ("terrain","geofence","separation")}
        return {"physical_controller_id":controller_id, "mean_value":_fraction_json(sum(row["mean"] for row in rows)/128), "tail_value":_fraction_json(sum(row["tail"] for row in rows)/128), "short_service":_fraction_json(sum(row["short"] for row in rows)/128), "long_service":_fraction_json(sum(row["long"] for row in rows)/128), "counts":counts, "override_causes":causes, "tracker_energy_final_sum":sum(row["tracker_energy_final_sum"] for row in rows), "relay_energy_final_sum":sum(row["relay_energy_final_sum"] for row in rows), "update_energy_joules_per_uav":sum(row["update_energy"] for row in rows), "support":support_json(controller_id), "cal_hard_safety":asdict(hard("CAL",controller_id,48)), "hold_hard_safety":asdict(hard("HOLD",controller_id,128)), "override_ucb95":override_ucbs[controller_id]}
    coendpoints = {tag:coendpoint(controller_id) for tag,controller_id in tag_to_id.items()}
    curve_report = {half:{route:[{"q":_fraction_json(q),"value":_fraction_json(value)} for q,value in curve_values[half][index].items()] for index,route in enumerate(("SHORT","LONG"))} | {"maxima_SHORT":[_fraction_json(q) for q in sorted(curves[half][0])],"maxima_LONG":[_fraction_json(q) for q in sorted(curves[half][1])]} for half in ("cal","c1","c2")}
    return {"package_valid": True, "common_nonidentification_reason": common_reason, "global_competent": global_ok, "global_competence_facts": {"nonharm":global_nonharm,"calibration_headroom":_fraction_json(1-global_cal),"heldout_mean":_fraction_json(global_panel.mean_value),"heldout_tail":_fraction_json(global_panel.tail_value),"support":global_support}, "conditional_rate_response":curve_report, "rate_response_identified": response_ok, "two_answerable": two_ok, "two_nonidentification_reason": two_reason, "two_answerability_facts":{"support":two_support,"support_counts":support_json(two_id),"nonharm":two_nonharm,"reciprocal_controls":reciprocal_ok}, "flex_adaptive_answerable": flex_answerable, "flex_nonidentification_reason":flex_reason, "flex_constituents":{"support":flex_support,"support_counts":support_json(flex_id),"nonharm":flex_nonharm,"algebraically_distinct":flex_algebraic,"realized_support_distinct":realized_distinct,"timing_member":flex_timing}, "realized_support": {"F_diff": [f_diff.numerator,f_diff.denominator], "A_diff": [a_diff.numerator,a_diff.denominator]}, "coendpoints_by_logical_tag":coendpoints, "intervals": {"D_S": asdict(ds), "D_L": asdict(dl), "Delta_mean": asdict(dm), "Delta_tail": asdict(dtail), "FLEX_mean": asdict(fmean), "FLEX_tail": asdict(ftail), "FLEX_TWO_mean": asdict(rel_mean), "FLEX_TWO_tail": asdict(rel_tail)}, "result_map": asdict(outcome)}


def release_result(root: Path) -> dict[str, object]:
    """The sole endpoint firewall: analyzer invocation follows full revalidation."""

    root = Path(root)
    recomputed = validate_complete_package(root)
    retained_complete = _load_exact_document(root / "COMPLETE.json")
    if retained_complete != recomputed:
        raise SerializationError("complete-package commit differs from full revalidation")
    acceptance = _load_exact_document(root / "TECHNICAL_ACCEPTANCE.json")
    expected_acceptance = {
        "schema": TECHNICAL_ACCEPTANCE_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "accepted": True,
        "complete_package_sha256": document_sha256(recomputed),
    }
    if set(acceptance) != set(expected_acceptance) | {"cm_acceptance_sha256"} or any(acceptance.get(key) != value for key,value in expected_acceptance.items()):
        raise ProductionAdmissionError("CM technical acceptance is absent or not bound to COMPLETE")
    _sha(acceptance["cm_acceptance_sha256"], "CM acceptance")
    if (root / "RESULT.json").exists():
        raise FileExistsError("result packet is write-once")
    result = _complete_panel_analysis(root)
    def contains_partial(value: object) -> bool:
        if isinstance(value, Mapping):
            return any(str(key).startswith("partial_") or contains_partial(item) for key, item in value.items())
        if isinstance(value, (list, tuple)):
            return any(contains_partial(item) for item in value)
        return False

    if contains_partial(result):
        raise SerializationError("result analyzer attempted to expose a partial endpoint")
    if validate_complete_package(root) != recomputed:
        raise SerializationError("complete package changed during result analysis")
    packet = {
        "schema": RESULT_SCHEMA,
        "card_revision": CARD_REVISION,
        "host": HOST_ID,
        "complete_package_sha256": document_sha256(recomputed),
        "complete_panel": True,
        "result": result,
    }
    atomic_write_once(root / "RESULT.json", packet, authorized_root=root)
    return packet


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="onlgr-headland90-r03",
        description="Exact batch-only CAL/HOLD runner; every production edge fails closed.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("preflight", help="validate gates and native receipt; no words/ticks")
    for name in ("preactivity-freeze", "coordinate-binding", "lease"):
        preflight.add_argument(f"--{name}", type=Path, required=True)
    preflight.add_argument("--result-root", type=Path, required=True)
    preflight.set_defaults(handler=_preflight_command)
    formal = sub.add_parser("formal-run", help="execute exact CAL/HOLD native batches and seal blinded package")
    for name in ("preactivity-freeze", "coordinate-binding", "lease"):
        formal.add_argument(f"--{name}", type=Path, required=True)
    formal.add_argument("--result-root", type=Path, required=True)
    formal.add_argument("--source-set-sha256", required=True)
    formal.add_argument("--config-sha256", required=True)
    formal.add_argument("--schema-sha256", required=True)
    formal.add_argument("--resume", action="store_true")
    formal.set_defaults(handler=_formal_run_command)
    return parser


def _preflight_command(args: argparse.Namespace) -> int:
    permit = admit_production(
        preactivity_freeze=_read_json(args.preactivity_freeze),
        coordinate_binding=_read_json(args.coordinate_binding),
        direction_lease=_read_json(args.lease),
        result_root=args.result_root,
    )
    print(json.dumps({
        "admitted": True,
        "backend_receipt_sha256": permit.backend_receipt_sha256,
        "activity_started": False,
    }, sort_keys=True))
    return 0


def _formal_run_command(args: argparse.Namespace) -> int:
    permit = admit_production(
        preactivity_freeze=_read_json(args.preactivity_freeze),
        coordinate_binding=_read_json(args.coordinate_binding),
        direction_lease=_read_json(args.lease),
        result_root=args.result_root,
        resume=args.resume,
    )
    complete = run_full_panel(
        permit,
        source_set_sha256=args.source_set_sha256,
        config_sha256=args.config_sha256,
        schema_sha256=args.schema_sha256,
    )
    print(json.dumps({
        "complete_package_sha256": document_sha256(complete),
        "result_exposed": False,
        "complete": True,
    }, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, ValueError, TypeError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
