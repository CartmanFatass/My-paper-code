"""Fail-closed native-first production/lifecycle adapter for TBVUUS r03.

Python owns immutable admission metadata, counter-addressed tape materialization,
batch formation, and durable I/O.  Every reset-to-terminal environment rollout
is executed by the registered C++ full host; there is no Python production
oracle or fallback.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
from typing import Any
import uuid

from envs.native.production_backend import (
    ONLGR_TBVUUS_R03_FULL_HOST,
    require_cpp_batched_production,
)

from . import analysis as az
from . import serialization as storage_schema
from .config import (
    BLACKOUT_TICKS,
    DT,
    FIXTURE_NAMESPACE,
    LOCKOUT_TICKS,
    ROAD_TEMPLATES,
    VG,
    Arm,
    EncounterSpec,
    FixtureCase,
    FixtureTape,
    RouteClass,
)
from .contracts import (
    ACCEPTED_FREEZE_SCHEMA,
    ACTIVITY_INTENT_SCHEMA,
    ACTIVITY_STARTED_SCHEMA,
    ARMS,
    BINDING_KEYS,
    CM_ACCEPTANCE_SCHEMA,
    COORDINATE_BINDING_SCHEMA,
    DIRECTION_ID,
    DIRECTION_LEASE_SCHEMA,
    HARD_FAILURE_KEYS,
    HOST_ID,
    PRIVATE_PANEL_SCHEMA,
    PRODUCTION_NAMESPACE,
    REPLICATES,
    RESULT_SCHEMA,
    SCIENCE_REVISION,
    SIDECAR_SCHEMAS,
    STAGE,
    canonical_json_bytes,
    coordinate_proposal,
    document_sha256,
    prospective_schema_contract,
)
from .coordinates import (
    Coordinate,
    EncounterIdentity,
    coordinate_for,
    coordinate_row_count,
    coordinate_rows_sha256,
    encode_coordinate,
    encounter_plan,
)
from .lifecycle import (
    CM_ACCEPTANCE_NAME,
    COMPLETE_BINDING_KEYS,
    COMPLETE_NAME,
    PANEL_COMMIT_NAME,
    LifecycleError,
    atomic_write_bytes,
    atomic_write_once,
    build_complete_marker as lifecycle_build_complete_marker,
    build_cm_acceptance,
    build_result_release_receipt,
    publish_result_once,
    read_canonical_json,
    resume_inventory,
    validate_cm_acceptance,
    validate_complete_marker,
    validate_complete_package,
    validate_installed_portfolio_em_sequencing_receipt,
    validate_result_release_authorization,
)
from .native_backend import run_native_batch
from .preactivity import validate_live_source_manifest
from .serialization import (
    CellIdentity,
    build_cell_commit,
    build_cell_packet,
    cell_commit_path,
    cell_packet_path,
    encode_sidecar_rows,
    sha256_bytes,
    sidecar_path,
    sidecar_reference,
    validate_panel_commit,
)


SOURCE_MANIFEST_NAME = "SOURCE_MANIFEST.json"
PANEL_NAME = "PANEL.json"
BACKEND_RECEIPT_NAME = "BACKEND_RECEIPT.json"
COORDINATE_BINDING_NAME = "COORDINATE_BINDING.json"
ACTIVITY_INTENT_NAME = "ACTIVITY_INTENT.json"
ACTIVITY_STARTED_NAME = "ACTIVITY_STARTED.json"
LEASE_RECEIPT_DIR = "lease-receipts"
CANONICAL_RESULT_ROOT = Path(
    "C:/Projects/HMASD/artifacts/onlgr_tbvuus_r03_full_panel_20260821"
).resolve()
CANONICAL_RESULT_V2_PATH = CANONICAL_RESULT_ROOT / "RESULT_V2.json"
CANONICAL_RESULT_V2_RELEASE_AUTHORIZATION_PATH = (
    CANONICAL_RESULT_ROOT / "RESULT_V2_RELEASE_AUTHORIZATION.json"
)
CANONICAL_PORTFOLIO_EM_SEQUENCING_RECEIPT_PATH = (
    CANONICAL_RESULT_ROOT / "PORTFOLIO_EM_RESULT_INTAKE_SEQUENCING_RECEIPT.json"
)

PRODUCTION_BATCH_WIDTH = 32
ENCOUNTERS_PER_NATIVE_GROUP = PRODUCTION_BATCH_WIDTH // len(ARMS)
MAX_CPU_WORKERS = 1
MAX_RAM_BYTES = 4 * 1024**3
EXPECTED_STORAGE_BYTES = 1 * 1024**3
MAX_STORAGE_BYTES = 4 * 1024**3
_REAL_PERMIT_TOKEN = object()
_TEST_PERMIT_TOKEN = object()
_ACTIVITY_PERMITS: dict[int, object] = {}
_SHA256 = frozenset("0123456789abcdef")


class ProductionAdmissionError(PermissionError):
    pass


def _sha(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _SHA256 for character in value)
    ):
        raise ProductionAdmissionError(f"{label} must be lowercase SHA-256")
    return value


def _uuid(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ProductionAdmissionError(f"{label} must be a UUID string")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ProductionAdmissionError(f"{label} must be a UUID string") from exc
    if str(parsed) != value:
        raise ProductionAdmissionError(f"{label} must be canonical lowercase UUID")
    return value


def _parse_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ProductionAdmissionError(f"{label} must be ISO-8601 UTC with Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ProductionAdmissionError(f"{label} is not valid ISO-8601 UTC") from exc
    return parsed


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _require_result_root(path: Path) -> Path:
    root = Path(path).resolve(strict=False)
    artifacts = (_repo_root() / "artifacts").resolve(strict=False)
    try:
        relative = root.relative_to(artifacts)
    except ValueError as exc:
        raise ProductionAdmissionError("result root must be under repository artifacts/") from exc
    if not relative.parts:
        raise ProductionAdmissionError("result root cannot be the artifacts directory itself")
    return root


def _manifest_path() -> Path:
    return Path(__file__).resolve().with_name(SOURCE_MANIFEST_NAME)


def _schema_identity() -> dict[str, object]:
    body = {
        "prospective": prospective_schema_contract(),
        "coordinate_proposal": coordinate_proposal(),
        "coordinate_row_count": coordinate_row_count(),
        "production_batch_width": PRODUCTION_BATCH_WIDTH,
        "activity_schemas": [ACTIVITY_INTENT_SCHEMA, ACTIVITY_STARTED_SCHEMA],
        "serialization_payload": storage_schema.serialization_schema_identity(),
        "complete_binding_keys": list(COMPLETE_BINDING_KEYS),
        "admission_schemas": [
            ACCEPTED_FREEZE_SCHEMA,
            COORDINATE_BINDING_SCHEMA,
            DIRECTION_LEASE_SCHEMA,
            PRIVATE_PANEL_SCHEMA,
        ],
    }
    return {**body, "schema_sha256": document_sha256(body)}


def live_source_identity() -> dict[str, str]:
    manifest_path = _manifest_path()
    manifest = read_canonical_json(manifest_path)
    checked = validate_live_source_manifest(manifest, manifest_path.parent)
    files = checked["files"]
    assert isinstance(files, Mapping)
    config = files.get("config.py")
    native_source = files.get("native/tbvuus_backend.cpp")
    if not isinstance(config, Mapping) or not isinstance(native_source, Mapping):
        raise ProductionAdmissionError("FINAL source manifest omits config or native source")
    guard = _repo_root() / "envs" / "native" / "production_backend.py"
    return {
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "source_set_sha256": str(checked["source_set_sha256"]),
        "config_sha256": str(config["sha256"]),
        "schema_sha256": str(_schema_identity()["schema_sha256"]),
        "shared_guard_source_sha256": hashlib.sha256(guard.read_bytes()).hexdigest(),
        "native_source_sha256": str(native_source["sha256"]),
    }


def validate_accepted_freeze(value: Mapping[str, object]) -> str:
    fixed = {
        "schema": ACCEPTED_FREEZE_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "accepted": True,
        "activity_started": False,
    }
    digests = {
        "preactivity_identity_sha256",
        "source_manifest_sha256",
        "source_set_sha256",
        "config_sha256",
        "schema_sha256",
        "shared_guard_source_sha256",
        "native_source_sha256",
        "native_artifact_sha256",
    }
    if set(value) != set(fixed) | digests or any(value.get(key) != item for key, item in fixed.items()):
        raise ProductionAdmissionError("accepted preactivity freeze schema or identity differs")
    for key in digests:
        _sha(value[key], key)
    return document_sha256(dict(value))


def validate_coordinate_binding(
    value: Mapping[str, object], *, row_verifier: Callable[[], str] = coordinate_rows_sha256
) -> str:
    proposal = coordinate_proposal()
    fixed = {
        "schema": COORDINATE_BINDING_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "split": "HOLD",
        "proposal_sha256": proposal["proposal_sha256"],
        "coordinate_row_count": coordinate_row_count(),
        "root_authorized": True,
        "production_words_materialized": False,
        "action_word_domain_present": False,
    }
    extra = {
        "experiment_id",
        "source_set_sha256",
        "coordinate_rows_sha256",
        "root_authorization_sha256",
    }
    if set(value) != set(fixed) | extra or any(value.get(key) != item for key, item in fixed.items()):
        raise ProductionAdmissionError("Root coordinate binding schema or frozen identity differs")
    _uuid(value["experiment_id"], "experiment_id")
    for key in ("source_set_sha256", "coordinate_rows_sha256", "root_authorization_sha256"):
        _sha(value[key], key)
    if value["coordinate_rows_sha256"] != row_verifier():
        raise ProductionAdmissionError("Root coordinate binding row-set digest differs")
    return document_sha256(dict(value))


def lease_scope_body(value: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "direction_id",
        "stage",
        "science_revision",
        "experiment_id",
        "result_root",
        "preactivity_freeze_sha256",
        "coordinate_binding_sha256",
        "source_set_sha256",
        "max_cpu_workers",
        "max_ram_bytes",
        "expected_storage_bytes",
        "max_storage_bytes",
        "batch_width",
    )
    return {key: value.get(key) for key in keys}


def validate_direction_lease(
    value: Mapping[str, object], *, now: datetime | None = None, require_active: bool = True,
    enforce_artifact_root: bool = True,
) -> tuple[str, str, datetime, Path]:
    fixed = {
        "schema": DIRECTION_LEASE_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "max_cpu_workers": MAX_CPU_WORKERS,
        "max_ram_bytes": MAX_RAM_BYTES,
        "expected_storage_bytes": EXPECTED_STORAGE_BYTES,
        "max_storage_bytes": MAX_STORAGE_BYTES,
        "batch_width": PRODUCTION_BATCH_WIDTH,
        "root_authorized": True,
    }
    extra = {
        "lease_id",
        "experiment_id",
        "result_root",
        "preactivity_freeze_sha256",
        "coordinate_binding_sha256",
        "source_set_sha256",
        "lease_scope_sha256",
        "not_before_utc",
        "not_after_utc",
        "root_authorization_sha256",
    }
    if set(value) != set(fixed) | extra or any(value.get(key) != item for key, item in fixed.items()):
        raise ProductionAdmissionError("direction lease schema, resources, or stage differs")
    _uuid(value["lease_id"], "lease_id")
    _uuid(value["experiment_id"], "experiment_id")
    for key in (
        "preactivity_freeze_sha256",
        "coordinate_binding_sha256",
        "source_set_sha256",
        "lease_scope_sha256",
        "root_authorization_sha256",
    ):
        _sha(value[key], key)
    expected_scope = document_sha256(lease_scope_body(value))
    if value["lease_scope_sha256"] != expected_scope:
        raise ProductionAdmissionError("direction lease stable scope digest differs")
    not_before = _parse_utc(value["not_before_utc"], "not_before_utc")
    not_after = _parse_utc(value["not_after_utc"], "not_after_utc")
    current = now or datetime.now(timezone.utc)
    if require_active and not not_before <= current < not_after:
        raise ProductionAdmissionError("direction lease is not currently active")
    result_root = Path(str(value["result_root"])).resolve(strict=False)
    if enforce_artifact_root:
        result_root = _require_result_root(result_root)
    return document_sha256(dict(value)), expected_scope, not_after, result_root


@dataclass(frozen=True)
class ProductionPermit:
    experiment_id: str
    result_root: Path
    preactivity_freeze_sha256: str
    coordinate_binding_sha256: str
    lease_sha256: str
    lease_scope_sha256: str
    source_set_sha256: str
    config_sha256: str
    schema_sha256: str
    native_artifact_sha256: str
    backend_receipt: Mapping[str, object]
    backend_receipt_sha256: str
    coordinate_binding: Mapping[str, object]
    lease_document: Mapping[str, object]
    expires_at: datetime
    _token: object

    def assert_active(self, *, verify_source: bool = False) -> None:
        if self._token not in (_REAL_PERMIT_TOKEN, _TEST_PERMIT_TOKEN):
            raise ProductionAdmissionError("production permit token is invalid")
        if datetime.now(timezone.utc) >= self.expires_at:
            raise ProductionAdmissionError("direction lease expired before the next atomic cell")
        if verify_source:
            live = live_source_identity()
            expected = {
                "source_set_sha256": self.source_set_sha256,
                "config_sha256": self.config_sha256,
                "schema_sha256": self.schema_sha256,
            }
            if any(live[key] != value for key, value in expected.items()):
                raise ProductionAdmissionError("live source/config/schema changed after admission")

    @property
    def bindings(self) -> dict[str, str]:
        return {
            "preactivity_freeze_sha256": self.preactivity_freeze_sha256,
            "coordinate_binding_sha256": self.coordinate_binding_sha256,
            "lease_scope_sha256": self.lease_scope_sha256,
            "source_set_sha256": self.source_set_sha256,
            "config_sha256": self.config_sha256,
            "schema_sha256": self.schema_sha256,
            "native_artifact_sha256": self.native_artifact_sha256,
        }


def _admit(
    *,
    preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object],
    direction_lease: Mapping[str, object],
    result_root: Path,
    shared_guard: Callable[..., Mapping[str, object]],
    row_verifier: Callable[[], str],
    identity_verifier: Callable[[], Mapping[str, str]],
    now: datetime | None,
    token: object,
) -> ProductionPermit:
    freeze_sha = validate_accepted_freeze(preactivity_freeze)
    binding_sha = validate_coordinate_binding(coordinate_binding, row_verifier=row_verifier)
    lease_sha, scope_sha, expires, leased_root = validate_direction_lease(direction_lease, now=now)
    requested_root = _require_result_root(result_root)
    if requested_root != leased_root:
        raise ProductionAdmissionError("requested result root differs from exact Root lease")
    if coordinate_binding["experiment_id"] != direction_lease["experiment_id"]:
        raise ProductionAdmissionError("coordinate binding and lease experiment identities differ")
    if direction_lease["preactivity_freeze_sha256"] != freeze_sha:
        raise ProductionAdmissionError("lease does not bind the accepted preactivity freeze")
    if direction_lease["coordinate_binding_sha256"] != binding_sha:
        raise ProductionAdmissionError("lease does not bind the Root coordinate binding")
    live = dict(identity_verifier())
    for key in (
        "source_manifest_sha256",
        "source_set_sha256",
        "config_sha256",
        "schema_sha256",
        "shared_guard_source_sha256",
        "native_source_sha256",
    ):
        if live.get(key) != preactivity_freeze.get(key):
            raise ProductionAdmissionError(f"live {key} differs from accepted freeze")
    if coordinate_binding["source_set_sha256"] != live["source_set_sha256"]:
        raise ProductionAdmissionError("coordinate binding uses another source identity")
    if direction_lease["source_set_sha256"] != live["source_set_sha256"]:
        raise ProductionAdmissionError("lease uses another source identity")
    receipt = dict(
        shared_guard(
            ONLGR_TBVUUS_R03_FULL_HOST,
            backend="cpp",
            batch_width=PRODUCTION_BATCH_WIDTH,
        )
    )
    fixed_receipt = {
        "schema": "HMASD_CPP_BATCHED_PRODUCTION_PREFLIGHT_V1",
        "component": ONLGR_TBVUUS_R03_FULL_HOST,
        "backend": "cpp",
        "batch_width": PRODUCTION_BATCH_WIDTH,
        "full_reset_step_cpp": True,
        "python_fallback": False,
    }
    if any(receipt.get(key) != value for key, value in fixed_receipt.items()):
        raise ProductionAdmissionError("shared backend receipt is not exact full-host C++")
    native = receipt.get("native")
    if not isinstance(native, Mapping):
        raise ProductionAdmissionError("shared backend receipt lacks native identity")
    native_sha = _sha(native.get("artifact_sha256"), "shared native artifact")
    if native_sha != preactivity_freeze["native_artifact_sha256"]:
        raise ProductionAdmissionError("shared native artifact differs from accepted freeze")
    return ProductionPermit(
        experiment_id=str(coordinate_binding["experiment_id"]),
        result_root=requested_root,
        preactivity_freeze_sha256=freeze_sha,
        coordinate_binding_sha256=binding_sha,
        lease_sha256=lease_sha,
        lease_scope_sha256=scope_sha,
        source_set_sha256=live["source_set_sha256"],
        config_sha256=live["config_sha256"],
        schema_sha256=live["schema_sha256"],
        native_artifact_sha256=native_sha,
        backend_receipt=receipt,
        backend_receipt_sha256=document_sha256(receipt),
        coordinate_binding=dict(coordinate_binding),
        lease_document=dict(direction_lease),
        expires_at=expires,
        _token=token,
    )


def admit_production(
    *,
    preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object],
    direction_lease: Mapping[str, object],
    result_root: Path,
    now: datetime | None = None,
) -> ProductionPermit:
    return _admit(
        preactivity_freeze=preactivity_freeze,
        coordinate_binding=coordinate_binding,
        direction_lease=direction_lease,
        result_root=result_root,
        shared_guard=require_cpp_batched_production,
        row_verifier=coordinate_rows_sha256,
        identity_verifier=live_source_identity,
        now=now,
        token=_REAL_PERMIT_TOKEN,
    )


def _admit_for_test(
    *,
    preactivity_freeze: Mapping[str, object],
    coordinate_binding: Mapping[str, object],
    direction_lease: Mapping[str, object],
    result_root: Path,
    shared_guard: Callable[..., Mapping[str, object]],
    row_verifier: Callable[[], str],
    identity_verifier: Callable[[], Mapping[str, str]],
    now: datetime,
) -> ProductionPermit:
    """Fixture-only admission seam; its token cannot materialize a word."""

    return _admit(
        preactivity_freeze=preactivity_freeze,
        coordinate_binding=coordinate_binding,
        direction_lease=direction_lease,
        result_root=result_root,
        shared_guard=shared_guard,
        row_verifier=row_verifier,
        identity_verifier=identity_verifier,
        now=now,
        token=_TEST_PERMIT_TOKEN,
    )


def _activity_identity(permit: ProductionPermit) -> dict[str, object]:
    panel = read_canonical_json(permit.result_root / PANEL_NAME)
    return {
        "experiment_id": permit.experiment_id,
        "panel_sha256": document_sha256(panel),
        "coordinate_binding_sha256": permit.coordinate_binding_sha256,
        "source_set_sha256": permit.source_set_sha256,
        "native_artifact_sha256": permit.native_artifact_sha256,
    }


def _first_coordinate() -> Coordinate:
    return coordinate_for(
        EncounterIdentity(0, 0, "SHORT"), tick=0, stream="target_lateral", lane=0
    )


def initialize_private_panel(permit: ProductionPermit) -> Path:
    permit.assert_active(verify_source=True)
    root = permit.result_root
    manifest = {
        "schema": PRIVATE_PANEL_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "experiment_id": permit.experiment_id,
        "private_blinded": True,
        "partial_interpretation_allowed": False,
        "arms": list(ARMS),
        "replicates": REPLICATES,
        "controller_replicates": 512,
        "arm_encounters": 20_480,
        "physical_ticks": 1_966_080,
        "batch_width": PRODUCTION_BATCH_WIDTH,
        "bindings": permit.bindings,
        "backend_receipt_sha256": permit.backend_receipt_sha256,
    }
    if root.exists():
        if read_canonical_json(root / PANEL_NAME) != manifest:
            raise ProductionAdmissionError("existing run root differs from stable experiment identity")
        if read_canonical_json(root / BACKEND_RECEIPT_NAME) != permit.backend_receipt:
            raise ProductionAdmissionError("retained backend receipt differs from admitted native host")
        if read_canonical_json(root / COORDINATE_BINDING_NAME) != permit.coordinate_binding:
            raise ProductionAdmissionError("retained coordinate binding differs")
        atomic_write_once(
            root / LEASE_RECEIPT_DIR / f"{permit.lease_sha256}.json",
            permit.lease_document,
            authorized_root=root,
        )
        return root
    root.parent.mkdir(parents=True, exist_ok=True)
    staging = root.parent / f".{root.name}.initializing"
    if staging.exists():
        raise FileExistsError("run-root initialization staging path already exists")
    staging.mkdir()
    try:
        atomic_write_once(staging / PANEL_NAME, manifest, authorized_root=staging)
        atomic_write_once(
            staging / BACKEND_RECEIPT_NAME, permit.backend_receipt, authorized_root=staging
        )
        atomic_write_once(
            staging / COORDINATE_BINDING_NAME,
            permit.coordinate_binding,
            authorized_root=staging,
        )
        atomic_write_once(
            staging / LEASE_RECEIPT_DIR / f"{permit.lease_sha256}.json",
            permit.lease_document,
            authorized_root=staging,
        )
        os.replace(staging, root)
    except Exception:
        # Leave a bounded, explicit staging directory for mechanical diagnosis.
        raise
    return root


def _write_activity_intent(permit: ProductionPermit) -> None:
    permit.assert_active(verify_source=True)
    intent = {
        "schema": ACTIVITY_INTENT_SCHEMA,
        "first_coordinate": asdict(_first_coordinate()),
        **_activity_identity(permit),
    }
    atomic_write_once(
        permit.result_root / ACTIVITY_INTENT_NAME,
        intent,
        authorized_root=permit.result_root,
    )


def _word_bits(value: float) -> int:
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def _counter_word(coordinate: Coordinate) -> float:
    digest = hashlib.sha256(encode_coordinate(coordinate)).digest()
    return (int.from_bytes(digest[:4], "big") + 0.5) / 4294967296.0


def _commit_first_word(permit: ProductionPermit, coordinate: Coordinate, value: float) -> None:
    expected_intent = {
        "schema": ACTIVITY_INTENT_SCHEMA,
        "first_coordinate": asdict(_first_coordinate()),
        **_activity_identity(permit),
    }
    if read_canonical_json(permit.result_root / ACTIVITY_INTENT_NAME) != expected_intent:
        raise ProductionAdmissionError("activity intent is absent or differs")
    if coordinate != _first_coordinate():
        raise ProductionAdmissionError("first materialized word differs from bound first coordinate")
    marker = {
        "schema": ACTIVITY_STARTED_SCHEMA,
        "activity_started": True,
        "first_coordinate": asdict(coordinate),
        "first_word_bits": _word_bits(value),
        **_activity_identity(permit),
    }
    atomic_write_once(
        permit.result_root / ACTIVITY_STARTED_NAME,
        marker,
        authorized_root=permit.result_root,
    )


def _word(permit: ProductionPermit, coordinate: Coordinate) -> float:
    if not isinstance(permit, ProductionPermit) or permit._token is not _REAL_PERMIT_TOKEN:
        raise ProductionAdmissionError("production word requires a real validated permit")
    value = _counter_word(coordinate)
    key = id(permit)
    if _ACTIVITY_PERMITS.get(key) is not permit:
        marker_path = permit.result_root / ACTIVITY_STARTED_NAME
        if marker_path.exists():
            marker = read_canonical_json(marker_path)
            expected = {
                "schema": ACTIVITY_STARTED_SCHEMA,
                "activity_started": True,
                "first_coordinate": asdict(_first_coordinate()),
                "first_word_bits": _word_bits(_counter_word(_first_coordinate())),
                **_activity_identity(permit),
            }
            if marker != expected:
                raise ProductionAdmissionError("retained activity marker differs")
        else:
            _commit_first_word(permit, coordinate, value)
        _ACTIVITY_PERMITS[key] = permit
    return value


def _normal_pair(permit: ProductionPermit, coordinate: Coordinate) -> tuple[float, float]:
    if coordinate.stream not in {
        "target_lateral", "wind_T", "wind_R", "sensor_x", "sensor_y",
        "shadow_TR", "shadow_RB",
    }:
        raise ValueError("normal materialization requested for a uniform stream")
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
    return magnitude * math.cos(theta), magnitude * math.sin(theta)


def _normal(permit: ProductionPermit, coordinate: Coordinate) -> float:
    return _normal_pair(permit, coordinate)[coordinate.lane % 2]


def _template(encounter: EncounterIdentity) -> tuple[int, int]:
    return ((1, 8), (1, -8), (-1, 8), (-1, -8))[encounter.template]


def _materialize_tape(
    permit: ProductionPermit, encounter: EncounterIdentity
) -> tuple[EncounterSpec, FixtureTape]:
    direction, lateral = _template(encounter)
    route = RouteClass[encounter.route_class]
    # FixtureCase is a typed native carrier only.  Production identity remains
    # in the coordinate binding and logical tag; C++ receives no namespace.
    spec = EncounterSpec(route, direction, lateral, namespace=FIXTURE_NAMESPACE)
    states, ticks = spec.total_ticks + 1, spec.total_ticks
    pair = lambda tick, stream: _normal_pair(
        permit, coordinate_for(encounter, tick=tick, stream=stream, lane=0)
    )
    word = lambda tick, stream: _word(
        permit, coordinate_for(encounter, tick=tick, stream=stream, lane=0)
    )
    tape = FixtureTape.from_sequences(
        spec,
        target_lateral=[pair(tick, "target_lateral")[0] for tick in range(states)],
        wind_t=[
            pair(tick, "wind_T")
            for tick in range(states)
        ],
        wind_r=[
            pair(tick, "wind_R")
            for tick in range(states)
        ],
        sensor=[
            (pair(tick, "sensor_x")[0], pair(tick, "sensor_y")[0])
            for tick in range(states)
        ],
        shadow_tr=[pair(tick, "shadow_TR")[0] for tick in range(states)],
        shadow_rb=[pair(tick, "shadow_RB")[0] for tick in range(states)],
        link_tr=[word(tick, "link_TR") for tick in range(ticks)],
        link_rb=[word(tick, "link_RB") for tick in range(ticks)],
    )
    return spec, tape


def _typed_bytes(value: object) -> bytes:
    if value is None:
        return b"n"
    if isinstance(value, bool):
        return b"b" + bytes((int(value),))
    if isinstance(value, int):
        return b"i" + int(value).to_bytes(8, "big", signed=True)
    if isinstance(value, float):
        return b"f" + struct.pack(">d", value)
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        return b"s" + len(encoded).to_bytes(4, "big") + encoded
    if is_dataclass(value):
        result = bytearray(b"d")
        for field in fields(value):
            result.extend(_typed_bytes(field.name))
            result.extend(_typed_bytes(getattr(value, field.name)))
        return bytes(result)
    if isinstance(value, Mapping):
        result = bytearray(b"m")
        for key in sorted(value, key=str):
            result.extend(_typed_bytes(str(key)))
            result.extend(_typed_bytes(value[key]))
        return bytes(result)
    if isinstance(value, (tuple, list)):
        result = bytearray(b"q" + len(value).to_bytes(4, "big"))
        for item in value:
            result.extend(_typed_bytes(item))
        return bytes(result)
    raise TypeError(f"unsupported audit value type: {type(value).__name__}")


def _audit_sha256(value: object) -> str:
    return hashlib.sha256(_typed_bytes(value)).hexdigest()


def _tape_commitment(
    rows: Sequence[tuple[EncounterIdentity, EncounterSpec, FixtureTape]]
) -> str:
    return _audit_sha256(tuple((encounter, spec, tape) for encounter, spec, tape in rows))


def native_group_plan(replicate: int) -> tuple[tuple[EncounterIdentity, ...], ...]:
    plan = encounter_plan(replicate)
    groups = tuple(
        plan[index : index + ENCOUNTERS_PER_NATIVE_GROUP]
        for index in range(0, len(plan), ENCOUNTERS_PER_NATIVE_GROUP)
    )
    if len(groups) != 5 or any(len(group) != 8 for group in groups):
        raise AssertionError("native group plan differs from five paired width-32 batches")
    return groups


def grouped_fixture_cases(
    materialized: Sequence[tuple[EncounterIdentity, EncounterSpec, FixtureTape]],
    *,
    logical_namespace: str = PRODUCTION_NAMESPACE,
) -> tuple[FixtureCase, ...]:
    if len(materialized) != ENCOUNTERS_PER_NATIVE_GROUP:
        raise ValueError("native group requires exactly eight encounter tapes")
    cases: list[FixtureCase] = []
    for encounter, spec, tape in materialized:
        for arm_index, arm_name in enumerate(ARMS):
            cases.append(
                FixtureCase(
                    spec,
                    tape,
                    Arm(arm_index),
                    logical_tag=(
                        f"{logical_namespace}|HOLD|{encounter.replicate}|"
                        f"{encounter.block}|{encounter.route_class}|{arm_name}"
                    ),
                )
            )
    if len(cases) != PRODUCTION_BATCH_WIDTH:
        raise AssertionError("native group is not exact width 32")
    return tuple(cases)


def _route_code(encounter: EncounterIdentity) -> int:
    return 0 if encounter.route_class == "SHORT" else 1


def _expected_action(arm_name: str) -> str:
    return {
        ARMS[0]: "KEEP",
        ARMS[1]: "OVERHEAD-SHAM",
        ARMS[2]: "RAW-PATCH",
        ARMS[3]: "ROAD-PATCH",
    }[arm_name]


@dataclass(frozen=True)
class ArmTransitionAuditFacts:
    scheduled_exact: bool
    shell_exact: bool
    energy_debit_exact: bool
    blackout_exact: bool
    lockout_exact: bool
    buffer_clear_exact: bool
    waypoints_unchanged: bool
    planner_not_invoked: bool
    later_keep_exact: bool

    @property
    def valid(self) -> bool:
        return all(vars(self).values())


def _close(left: float, right: float) -> bool:
    if math.isnan(left) or math.isnan(right):
        return math.isnan(left) and math.isnan(right)
    return math.isclose(left, right, rel_tol=2e-14, abs_tol=2e-12)


def _vec_close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(_close(float(one), float(two)) for one, two in zip(left, right))


def _route_at_time(
    route_class: RouteClass, direction: int, lateral: int, time: float
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    duration = route_class.scored_ticks * DT
    if route_class is RouteClass.SHORT:
        u = max(time, 0.0) / duration
        phi = math.pi / 4.0 + direction * (u - 0.5) * math.pi / 2.0
        base = (
            80.0 + 64.0 * math.cos(phi) + lateral / math.sqrt(2.0),
            80.0 + 64.0 * math.sin(phi) + lateral / math.sqrt(2.0),
        )
        tangent = (direction * -math.sin(phi), direction * math.cos(phi))
        if time < 0.0:
            phi0 = math.pi / 4.0 - direction * math.pi / 4.0
            base0 = (
                80.0 + 64.0 * math.cos(phi0) + lateral / math.sqrt(2.0),
                80.0 + 64.0 * math.sin(phi0) + lateral / math.sqrt(2.0),
            )
            tangent = (direction * -math.sin(phi0), direction * math.cos(phi0))
            base = (
                base0[0] + tangent[0] * time * VG,
                base0[1] + tangent[1] * time * VG,
            )
    else:
        u = max(time, 0.0) / duration
        base = (direction * 64.0 * math.pi * (2.0 * u - 1.0), 200.0 + lateral)
        tangent = (float(direction), 0.0)
        if time < 0.0:
            base = (
                -direction * 64.0 * math.pi + tangent[0] * time * VG,
                200.0 + lateral,
            )
    normal = (-tangent[1], tangent[0])
    return base, tangent, normal


def _arm_transition_audit_facts(arm_name: str, result: Any) -> ArmTransitionAuditFacts:
    if len(result.ticks) != result.spec.total_ticks:
        return ArmTransitionAuditFacts(*(False for _ in range(9)))
    t0 = result.ticks[16]
    expected_shell = arm_name != ARMS[0]
    scheduled_exact = (
        not t0.scheduled_t0_decision
    ) is False and result.scheduled_t0_decisions == 1
    shell_exact = (
        t0.action == _expected_action(arm_name)
        and t0.action_shell is expected_shell
        and result.action_shells == int(expected_shell)
    )
    charge = 200.0 if expected_shell else 0.0
    expected_tracker = max(
        0.0,
        t0.tracker_energy_before
        - DT * (300.0 + sum(value * value for value in t0.tracker_air_velocity))
        - charge,
    )
    expected_relay = max(
        0.0,
        t0.relay_energy_before
        - DT * (350.0 + sum(value * value for value in t0.relay_air_velocity))
        - charge,
    )
    energy_debit_exact = _close(t0.tracker_energy_after, expected_tracker) and _close(
        t0.relay_energy_after, expected_relay
    )
    if expected_shell:
        blackout_exact = (
            [tick.blackout_active for tick in result.ticks[16:20]] == [True] * BLACKOUT_TICKS
            and not any(tick.blackout_active for tick in result.ticks[20:])
        )
        lockout_exact = (
            [tick.lockout_active for tick in result.ticks[16:32]] == [True] * LOCKOUT_TICKS
            and not any(tick.lockout_active for tick in result.ticks[32:])
        )
        buffer_clear_exact = t0.buffer_count_pre == 2 and t0.buffer_count_post == 0
    else:
        blackout_exact = not any(tick.blackout_active for tick in result.ticks[16:])
        lockout_exact = not any(tick.lockout_active for tick in result.ticks[16:])
        buffer_clear_exact = t0.buffer_count_post == t0.buffer_count_pre
    waypoints = (result.ticks[0].tracker_waypoint, result.ticks[0].relay_waypoint)
    waypoints_unchanged = all(
        (tick.tracker_waypoint, tick.relay_waypoint) == waypoints for tick in result.ticks
    )
    planner_not_invoked = waypoints_unchanged and all(
        tick.no_planner_solution == result.ticks[15].no_planner_solution
        for tick in result.ticks[16:]
    )
    later_keep_exact = all(
        (
            tick.action == ("BOOT" if tick.tick == 0 else _expected_action(arm_name) if tick.tick == 16 else "KEEP")
            and tick.scheduled_t0_decision == (tick.tick == 16)
            and tick.action_shell == (tick.tick == 16 and expected_shell)
        )
        for tick in result.ticks
    )
    return ArmTransitionAuditFacts(
        scheduled_exact,
        shell_exact,
        energy_debit_exact,
        blackout_exact,
        lockout_exact,
        buffer_clear_exact,
        waypoints_unchanged,
        planner_not_invoked,
        later_keep_exact,
    )


def _road_fit_audit_facts(arm_name: str, result: Any) -> az.RoadFitAuditFacts:
    t0 = result.ticks[16]
    available_expected = t0.buffer_count_pre == 2
    availability_exact = (
        t0.road_fit_available == available_expected
        and result.road_fit_available_count == int(available_expected)
    )
    every = (
        t0.scheduled_t0_decision
        and result.scheduled_t0_decisions == 1
        and result.effective_road_patch_count == int(t0.effective_road_patch)
    )
    tie_exact = selected_audited = patch_exact = fallback_exact = no_future = True
    if available_expected:
        no_future = (
            math.isfinite(t0.fit_t1)
            and math.isfinite(t0.fit_t2)
            and t0.fit_t1 < t0.fit_t2 <= 0.0
            and all(math.isfinite(value) for value in (*t0.fit_z1, *t0.fit_z2))
        )
        residuals: list[float] = []
        if no_future:
            for route_class, direction, lateral in ROAD_TEMPLATES:
                base1, _, _ = _route_at_time(route_class, direction, lateral, t0.fit_t1)
                base2, _, _ = _route_at_time(route_class, direction, lateral, t0.fit_t2)
                residuals.append(
                    (t0.fit_z1[0] - base1[0]) ** 2
                    + (t0.fit_z1[1] - base1[1]) ** 2
                    + (t0.fit_z2[0] - base2[0]) ** 2
                    + (t0.fit_z2[1] - base2[1]) ** 2
                )
        residual_exact = len(residuals) == 8 and all(
            _close(observed, expected)
            for observed, expected in zip(t0.road_residuals, residuals)
        )
        selected = min(range(8), key=residuals.__getitem__) if residuals else -1
        tie_exact = residual_exact and t0.selected_template == selected
        selected_audited = selected in range(8) and t0.selected_template == selected
        if selected in range(8):
            route_class, direction, lateral = ROAD_TEMPLATES[selected]
            base2, _, normal2 = _route_at_time(route_class, direction, lateral, t0.fit_t2)
            base0, tangent0, normal0 = _route_at_time(route_class, direction, lateral, 0.0)
            eta_raw = (
                (t0.fit_z2[0] - base2[0]) * normal2[0]
                + (t0.fit_z2[1] - base2[1]) * normal2[1]
            )
            eta_patch = min(max(eta_raw, -15.0), 15.0)
            patch_position = (
                base0[0] + eta_patch * normal0[0],
                base0[1] + eta_patch * normal0[1],
            )
            patch_velocity = (VG * tangent0[0], VG * tangent0[1])
            effective = (
                math.hypot(
                    patch_position[0] - t0.estimator_position_pre[0],
                    patch_position[1] - t0.estimator_position_pre[1],
                )
                >= 1.0
                or math.hypot(
                    patch_velocity[0] - t0.estimator_velocity_pre[0],
                    patch_velocity[1] - t0.estimator_velocity_pre[1],
                )
                >= 1.0
            )
            patch_exact = (
                _close(t0.eta_raw, eta_raw)
                and _close(t0.eta_patch, eta_patch)
                and _vec_close(t0.patch_position, patch_position)
                and _vec_close(t0.patch_velocity, patch_velocity)
                and t0.effective_road_patch == effective
            )
            if arm_name == ARMS[3]:
                patch_exact &= _vec_close(t0.estimator_position, patch_position) and _vec_close(
                    t0.estimator_velocity, patch_velocity
                )
            elif arm_name in (ARMS[0], ARMS[1]):
                patch_exact &= t0.estimator_position == t0.estimator_position_pre and t0.estimator_velocity == t0.estimator_velocity_pre
    else:
        fallback_exact = (
            t0.selected_template == -1
            and all(math.isnan(value) for value in t0.road_residuals)
            and math.isnan(t0.eta_raw)
            and math.isnan(t0.eta_patch)
            and t0.patch_position == t0.estimator_position_pre
            and t0.patch_velocity == t0.estimator_velocity_pre
            and not t0.effective_road_patch
            and t0.estimator_position == t0.estimator_position_pre
            and t0.estimator_velocity == t0.estimator_velocity_pre
        )
    return az.RoadFitAuditFacts(
        every_encounter_audited=every,
        availability_exact=availability_exact,
        tie_order_exact=tie_exact,
        selected_template_audited=selected_audited,
        patch_formula_exact=patch_exact,
        identity_fallback_exact=fallback_exact,
        no_future_or_hidden_input=no_future,
    )


def _clip_norm(vector: tuple[float, float], maximum: float) -> tuple[float, float]:
    norm = math.hypot(*vector)
    if norm <= maximum or norm == 0.0:
        return vector
    scale = maximum / norm
    return vector[0] * scale, vector[1] * scale


def _raw_conformant(result: Any) -> bool:
    t0 = result.ticks[16]
    if t0.action != "RAW-PATCH":
        return False
    if not t0.road_fit_available:
        return (
            t0.estimator_position == t0.estimator_position_pre
            and t0.estimator_velocity == t0.estimator_velocity_pre
        )
    delta = t0.fit_t2 - t0.fit_t1
    if not delta > 0.0:
        return False
    expected_velocity = _clip_norm(
        ((t0.fit_z2[0] - t0.fit_z1[0]) / delta, (t0.fit_z2[1] - t0.fit_z1[1]) / delta),
        20.0,
    )
    return t0.estimator_position == t0.fit_z2 and all(
        math.isclose(observed, expected, rel_tol=0.0, abs_tol=2e-12)
        for observed, expected in zip(t0.estimator_velocity, expected_velocity)
    )


_REGISTERED_SHAM_DIFFERENCE_FIELDS = frozenset(
    {
        "action",
        "action_shell",
        "buffer_count_pre",
        "buffer_count_post",
        "blackout_active",
        "lockout_active",
        "tracker_energy_before",
        "relay_energy_before",
        "tracker_energy_after",
        "relay_energy_after",
        "trial_tr",
        "trial_rb",
        "packet_valid",
        "service",
    }
)


def _same_audit_value(left: object, right: object) -> bool:
    if isinstance(left, float) and isinstance(right, float):
        return (
            math.isnan(left) and math.isnan(right)
        ) or struct.pack(">d", left) == struct.pack(">d", right)
    if isinstance(left, tuple) and isinstance(right, tuple):
        return len(left) == len(right) and all(
            _same_audit_value(one, two) for one, two in zip(left, right)
        )
    return left == right


def _sham_validity_facts(
    never: Any, sham: Any, *, common_tapes_equal: bool
) -> az.ShamValidityFacts:
    if never.spec != sham.spec or len(never.ticks) != len(sham.ticks):
        return az.ShamValidityFacts(False, common_tapes_equal, False, False, False, False, False)
    never_t0, sham_t0 = never.ticks[16], sham.ticks[16]
    common_pre = not (
        never_t0.estimator_position_pre != sham_t0.estimator_position_pre
        or never_t0.estimator_velocity_pre != sham_t0.estimator_velocity_pre
        or never_t0.tracker_waypoint != sham_t0.tracker_waypoint
        or never_t0.relay_waypoint != sham_t0.relay_waypoint
        or never_t0.buffer_count_pre != sham_t0.buffer_count_pre
    )
    estimator_unchanged = (
        sham_t0.estimator_position == sham_t0.estimator_position_pre
        and sham_t0.estimator_velocity == sham_t0.estimator_velocity_pre
        and all(
            sham_tick.estimator_position == never_tick.estimator_position
            and sham_tick.estimator_velocity == never_tick.estimator_velocity
            for never_tick, sham_tick in zip(never.ticks, sham.ticks)
        )
    )
    waypoints_unchanged = all(
        sham_tick.tracker_waypoint == never_tick.tracker_waypoint
        and sham_tick.relay_waypoint == never_tick.relay_waypoint
        for never_tick, sham_tick in zip(never.ticks, sham.ticks)
    )
    only_registered = True
    tickwise_q = True
    post_blackout_equal = True
    for never_tick, sham_tick in zip(never.ticks, sham.ticks):
        for field in fields(never_tick):
            if field.name in _REGISTERED_SHAM_DIFFERENCE_FIELDS:
                continue
            if not _same_audit_value(
                getattr(never_tick, field.name), getattr(sham_tick, field.name)
            ):
                only_registered = False
        if sham_tick.service > never_tick.service:
            tickwise_q = False
        if (
            not sham_tick.blackout_active
            and not sham_tick.battery_exhausted
            and not never_tick.battery_exhausted
            and sham_tick.service != never_tick.service
        ):
            post_blackout_equal = False
        # Radio trials and packets may differ only while the registered shell
        # blackout suppresses raw, otherwise-identical link outcomes.
        if not sham_tick.blackout_active and (
            sham_tick.trial_tr != never_tick.trial_tr
            or sham_tick.trial_rb != never_tick.trial_rb
            or sham_tick.packet_valid != never_tick.packet_valid
        ):
            only_registered = False
    return az.ShamValidityFacts(
        common_pre_action_state_equal=common_pre,
        common_tapes_equal=common_tapes_equal,
        estimator_bitwise_unchanged=estimator_unchanged,
        waypoints_bitwise_unchanged=waypoints_unchanged,
        only_registered_shell_differences=only_registered,
        tickwise_q_not_greater_than_never=tickwise_q,
        post_blackout_equal_absent_battery_exhaustion=post_blackout_equal,
    )


def _tick_flags(tick: Any) -> int:
    flags = 0
    for bit, value in enumerate(
        (
            tick.scored,
            tick.scheduled_t0_decision,
            tick.action_shell,
            tick.road_fit_available,
            tick.effective_road_patch,
            bool(tick.service),
            tick.safety_override,
            tick.hard_failure,
        )
    ):
        flags |= int(bool(value)) << bit
    return flags


def _build_cell_material(
    *,
    arm_name: str,
    replicate: int,
    results: Sequence[Any],
    tape_commitment_sha256: str,
    sham_facts: az.ShamValidityFacts,
    raw_valid: bool,
) -> tuple[dict[str, object], dict[str, bytes]]:
    plan = encounter_plan(replicate)
    if len(results) != len(plan):
        raise RuntimeError("cell result set differs from exact 40-encounter plan")
    tick_rows: list[dict[str, object]] = []
    road_rows: list[dict[str, object]] = []
    arm_rows: list[dict[str, object]] = []
    block_counts: dict[int, dict[str, int]] = {
        block: {} for block in range(20)
    }
    tick_valid = endpoint_valid = True
    road_fact_rows: list[az.RoadFitAuditFacts] = []
    transition_fact_rows: list[ArmTransitionAuditFacts] = []
    effective_by_route = {route: 0 for route in ("SHORT", "LONG")}
    for encounter, result in zip(plan, results):
        if result.spec.route_class.name != encounter.route_class:
            raise RuntimeError("native result route differs from deterministic group order")
        tick_valid &= len(result.ticks) == result.spec.total_ticks
        road_fact_rows.append(_road_fit_audit_facts(arm_name, result))
        transition_fact_rows.append(_arm_transition_audit_facts(arm_name, result))
        effective_by_route[encounter.route_class] += int(result.effective_road_patch_count)
        for tick in result.ticks:
            tick_rows.append(
                {
                    "block": encounter.block,
                    "encounter_ordinal": encounter.encounter_ordinal,
                    "tick": tick.tick,
                    "flags": _tick_flags(tick),
                    "digest": _audit_sha256(tick),
                }
            )
        t0 = result.ticks[16]
        road_rows.append(
            {
                "block": encounter.block,
                "encounter_ordinal": encounter.encounter_ordinal,
                "route": _route_code(encounter),
                "available": int(t0.road_fit_available),
                "selected": t0.selected_template,
                "digest": _audit_sha256(
                    (
                        t0.road_fit_available,
                        t0.selected_template,
                        t0.road_residuals,
                        t0.fit_t1,
                        t0.fit_t2,
                        t0.fit_z1,
                        t0.fit_z2,
                        t0.eta_raw,
                        t0.eta_patch,
                        t0.patch_position,
                        t0.patch_velocity,
                        t0.effective_road_patch,
                    )
                ),
            }
        )
        arm_rows.append(
            {
                "block": encounter.block,
                "encounter_ordinal": encounter.encounter_ordinal,
                "route": _route_code(encounter),
                "shell": int(t0.action_shell),
                "digest": _audit_sha256(
                    (
                        t0.action,
                        t0.scheduled_t0_decision,
                        t0.action_shell,
                        t0.estimator_position_pre,
                        t0.estimator_velocity_pre,
                        t0.estimator_position,
                        t0.estimator_velocity,
                        t0.buffer_count_pre,
                        t0.buffer_count_post,
                        t0.blackout_active,
                        t0.lockout_active,
                        t0.tracker_energy_before,
                        t0.relay_energy_before,
                        t0.tracker_energy_after,
                        t0.relay_energy_after,
                        t0.tracker_waypoint,
                        t0.relay_waypoint,
                    )
                ),
            }
        )
        scored_sum = sum(tick.service for tick in result.ticks if tick.scored)
        endpoint_valid &= scored_sum == result.scored_valid_ticks
        block_counts[encounter.block][encounter.route_class] = result.scored_valid_ticks
    endpoint_rows: list[dict[str, object]] = []
    ordered_counts: list[tuple[int, int]] = []
    for block in range(20):
        short_valid = block_counts[block].get("SHORT")
        long_valid = block_counts[block].get("LONG")
        if short_valid is None or long_valid is None:
            raise RuntimeError("endpoint audit lacks a paired SHORT/LONG block")
        ordered_counts.append((short_valid, long_valid))
        endpoint_rows.append(
            {
                "block": block,
                "short_valid": short_valid,
                "long_valid": long_valid,
                "digest": _audit_sha256((block, short_valid, long_valid, short_valid + long_valid, 160)),
            }
        )
    endpoints = az.replicate_endpoints_from_block_counts(ordered_counts)
    road_facts = az.RoadFitAuditFacts(
        **{
            name: all(getattr(row, name) for row in road_fact_rows)
            for name in az.RoadFitAuditFacts.__dataclass_fields__
        }
    )
    transition_facts = ArmTransitionAuditFacts(
        **{
            name: all(getattr(row, name) for row in transition_fact_rows)
            for name in ArmTransitionAuditFacts.__dataclass_fields__
        }
    )
    failures = {
        "terrain_penetrations": sum(result.terrain_penetrations for result in results),
        "geofence_exits": sum(result.geofence_exits for result in results),
        "separation_breaches": sum(result.separation_breaches for result in results),
        "no_safe_control": sum(int(result.no_safe_control) for result in results),
        "no_planner_solution": sum(int(result.no_planner_solution) for result in results),
        "battery_exhaustions": sum(int(result.battery_exhausted) for result in results),
        "numerical_faults": sum(int(result.numerical_fault) for result in results),
    }
    aggregate: dict[str, object] = {
        "blocks": 20,
        "encounters": 40,
        "physical_ticks": sum(len(result.ticks) for result in results),
        "scored_ticks": 3200,
        "short_encounters": 20,
        "long_encounters": 20,
        "scheduled_t0_decisions": sum(result.scheduled_t0_decisions for result in results),
        "action_shell_count": sum(result.action_shells for result in results),
        "road_fit_available_count": sum(result.road_fit_available_count for result in results),
        "effective_road_patch_count": sum(result.effective_road_patch_count for result in results),
        "effective_road_patch_by_route": effective_by_route,
        "valid_scored_ticks": sum(result.scored_valid_ticks for result in results),
        "safety_overrides": sum(result.safety_overrides for result in results),
        "hard_failures": failures,
        "mean_value": endpoints.mean,
        "tail_value": endpoints.tail,
        "tape_commitment_sha256": tape_commitment_sha256,
        "tick_audit_valid": bool(tick_valid),
        "road_fit_audit_valid": road_facts.valid,
        "arm_transition_audit_valid": transition_facts.valid,
        "endpoint_audit_valid": bool(endpoint_valid),
        "raw_conformant": bool(raw_valid),
        "sham_valid": sham_facts.valid,
        "road_fit_facts": asdict(road_facts),
        "arm_transition_facts": asdict(transition_facts),
        "sham_validity_facts": asdict(sham_facts),
    }
    identity = CellIdentity(arm_name, replicate)
    sidecars = {
        "tick_audit": encode_sidecar_rows("tick_audit", identity, tick_rows),
        "road_fit_audit": encode_sidecar_rows("road_fit_audit", identity, road_rows),
        "arm_transition_audit": encode_sidecar_rows("arm_transition_audit", identity, arm_rows),
        "endpoint_audit": encode_sidecar_rows("endpoint_audit", identity, endpoint_rows),
    }
    return aggregate, sidecars


def _commit_cell(
    permit: ProductionPermit,
    identity: CellIdentity,
    aggregate: Mapping[str, object],
    sidecars: Mapping[str, bytes],
) -> None:
    permit.assert_active(verify_source=True)
    _write_cell_material(
        permit.result_root,
        bindings=permit.bindings,
        identity=identity,
        aggregate=aggregate,
        sidecars=sidecars,
    )


def _write_cell_material(
    root: Path,
    *,
    bindings: Mapping[str, str],
    identity: CellIdentity,
    aggregate: Mapping[str, object],
    sidecars: Mapping[str, bytes],
) -> None:
    root = Path(root).resolve()
    if set(sidecars) != set(SIDECAR_SCHEMAS):
        raise RuntimeError("cell sidecar set differs from exact schema")
    references: dict[str, Mapping[str, object]] = {}
    for kind in SIDECAR_SCHEMAS:
        payload = sidecars[kind]
        references[kind] = sidecar_reference(kind, identity, payload)
        atomic_write_bytes(
            sidecar_path(root, identity, kind),
            payload,
            authorized_root=root,
        )
    packet = build_cell_packet(
        identity,
        bindings=bindings,
        aggregate=aggregate,
        sidecars=references,
    )
    atomic_write_once(
        cell_packet_path(root, identity),
        packet,
        authorized_root=root,
    )
    commit = build_cell_commit(identity, packet)
    atomic_write_once(
        cell_commit_path(root, identity),
        commit,
        authorized_root=root,
    )


def _run_replicate(
    permit: ProductionPermit,
    replicate: int,
    *,
    native_runner: Callable[[Sequence[FixtureCase]], Sequence[Any]],
) -> None:
    permit.assert_active(verify_source=True)
    materialized_all: list[tuple[EncounterIdentity, EncounterSpec, FixtureTape]] = []
    results_by_arm: dict[str, list[Any]] = {arm: [] for arm in ARMS}
    for group in native_group_plan(replicate):
        permit.assert_active(verify_source=True)
        materialized = [
            (encounter, *_materialize_tape(permit, encounter)) for encounter in group
        ]
        materialized_all.extend(materialized)
        cases = grouped_fixture_cases(materialized)
        observed = tuple(native_runner(cases))
        if len(observed) != PRODUCTION_BATCH_WIDTH:
            raise RuntimeError("native batch returned another width")
        for index, result in enumerate(observed):
            encounter_index, arm_index = divmod(index, len(ARMS))
            encounter = group[encounter_index]
            arm_name = ARMS[arm_index]
            expected_tag = cases[index].logical_tag
            if (
                result.logical_tag != expected_tag
                or int(result.arm) != arm_index
                or result.spec != materialized[encounter_index][1]
            ):
                raise RuntimeError("native result order/identity differs from grouped four-arm batch")
            results_by_arm[arm_name].append(result)
    tape_sha = _tape_commitment(materialized_all)
    sham_rows = [
        _sham_validity_facts(never, sham, common_tapes_equal=True)
        for never, sham in zip(results_by_arm[ARMS[0]], results_by_arm[ARMS[1]])
    ]
    sham_facts = az.ShamValidityFacts(
        **{
            name: all(getattr(row, name) for row in sham_rows)
            for name in az.ShamValidityFacts.__dataclass_fields__
        }
    )
    raw_valid = all(_raw_conformant(result) for result in results_by_arm[ARMS[2]])
    for arm_name in ARMS:
        aggregate, sidecars = _build_cell_material(
            arm_name=arm_name,
            replicate=replicate,
            results=results_by_arm[arm_name],
            tape_commitment_sha256=tape_sha,
            sham_facts=sham_facts,
            raw_valid=raw_valid,
        )
        _commit_cell(permit, CellIdentity(arm_name, replicate), aggregate, sidecars)


def _retained_receipt_bindings(
    root: Path,
    validation: Mapping[str, object],
    *,
    row_verifier: Callable[[], str] = coordinate_rows_sha256,
    enforce_artifact_root: bool = True,
) -> dict[str, str]:
    """Authenticate every top-level receipt before COMPLETE or result release."""

    root = Path(root).resolve()
    panel = read_canonical_json(root / PANEL_NAME)
    expected_panel_keys = {
        "schema", "direction_id", "stage", "science_revision", "host", "namespace",
        "experiment_id", "private_blinded", "partial_interpretation_allowed",
        "arms", "replicates", "controller_replicates", "arm_encounters",
        "physical_ticks", "batch_width", "bindings", "backend_receipt_sha256",
    }
    fixed_panel = {
        "schema": PRIVATE_PANEL_SCHEMA,
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "private_blinded": True,
        "partial_interpretation_allowed": False,
        "arms": list(ARMS),
        "replicates": REPLICATES,
        "controller_replicates": 512,
        "arm_encounters": 20_480,
        "physical_ticks": 1_966_080,
        "batch_width": PRODUCTION_BATCH_WIDTH,
    }
    if set(panel) != expected_panel_keys or any(panel.get(key) != value for key, value in fixed_panel.items()):
        raise LifecycleError("retained PANEL identity/count schema differs")
    _uuid(panel["experiment_id"], "retained panel experiment_id")
    bindings = panel["bindings"]
    if not isinstance(bindings, Mapping) or set(bindings) != set(BINDING_KEYS):
        raise LifecycleError("retained PANEL immutable binding set differs")
    for key in BINDING_KEYS:
        _sha(bindings[key], f"retained PANEL {key}")
    uniform_bindings = validation.get("uniform_bindings")
    if not isinstance(uniform_bindings, Mapping) or dict(uniform_bindings) != dict(bindings):
        raise LifecycleError("retained PANEL bindings differ from committed cell bindings")
    backend = read_canonical_json(root / BACKEND_RECEIPT_NAME)
    backend_sha = document_sha256(backend)
    if backend_sha != panel["backend_receipt_sha256"]:
        raise LifecycleError("retained backend receipt differs from PANEL")
    native = backend.get("native")
    if (
        backend.get("component") != ONLGR_TBVUUS_R03_FULL_HOST
        or backend.get("backend") != "cpp"
        or backend.get("batch_width") != PRODUCTION_BATCH_WIDTH
        or backend.get("full_reset_step_cpp") is not True
        or backend.get("python_fallback") is not False
        or not isinstance(native, Mapping)
        or native.get("artifact_sha256") != bindings["native_artifact_sha256"]
    ):
        raise LifecycleError("retained backend receipt is not the bound full C++ host")
    binding = read_canonical_json(root / COORDINATE_BINDING_NAME)
    binding_sha = validate_coordinate_binding(binding, row_verifier=row_verifier)
    if (
        binding_sha != bindings["coordinate_binding_sha256"]
        or binding["experiment_id"] != panel["experiment_id"]
        or binding["source_set_sha256"] != bindings["source_set_sha256"]
    ):
        raise LifecycleError("retained coordinate binding differs from PANEL")
    lease_dir = root / LEASE_RECEIPT_DIR
    if not lease_dir.is_dir():
        raise LifecycleError("lease receipt inventory is absent")
    observed = tuple(sorted(path for path in lease_dir.iterdir() if path.is_file()))
    if not observed or any(path.suffix != ".json" for path in observed) or any(path.is_dir() for path in lease_dir.iterdir()):
        raise LifecycleError("lease receipt inventory contains an unexpected object")
    lease_rows: list[dict[str, object]] = []
    for path in observed:
        lease = read_canonical_json(path)
        lease_sha, scope_sha, _, leased_root = validate_direction_lease(
            lease, require_active=False, enforce_artifact_root=enforce_artifact_root
        )
        if path.stem != lease_sha:
            raise LifecycleError("lease receipt filename does not authenticate its document")
        if (
            scope_sha != bindings["lease_scope_sha256"]
            or leased_root != root
            or lease["experiment_id"] != panel["experiment_id"]
            or lease["preactivity_freeze_sha256"] != bindings["preactivity_freeze_sha256"]
            or lease["coordinate_binding_sha256"] != binding_sha
            or lease["source_set_sha256"] != bindings["source_set_sha256"]
        ):
            raise LifecycleError("lease receipt does not preserve PANEL scope/identity")
        lease_rows.append(
            {
                "lease_sha256": lease_sha,
                "lease_scope_sha256": scope_sha,
                "not_before_utc": lease["not_before_utc"],
                "not_after_utc": lease["not_after_utc"],
            }
        )
    lease_inventory_sha = document_sha256(
        {"schema": "ONLGR-TBVUUS-R03-LEASE-RECEIPT-INVENTORY-v1", "rows": lease_rows}
    )
    activity_identity = {
        "experiment_id": panel["experiment_id"],
        "panel_sha256": document_sha256(panel),
        "coordinate_binding_sha256": binding_sha,
        "source_set_sha256": bindings["source_set_sha256"],
        "native_artifact_sha256": bindings["native_artifact_sha256"],
    }
    intent = read_canonical_json(root / ACTIVITY_INTENT_NAME)
    expected_intent = {
        "schema": ACTIVITY_INTENT_SCHEMA,
        "first_coordinate": asdict(_first_coordinate()),
        **activity_identity,
    }
    if intent != expected_intent:
        raise LifecycleError("retained ACTIVITY_INTENT differs from PANEL/binding")
    started = read_canonical_json(root / ACTIVITY_STARTED_NAME)
    expected_started = {
        "schema": ACTIVITY_STARTED_SCHEMA,
        "activity_started": True,
        "first_coordinate": asdict(_first_coordinate()),
        "first_word_bits": _word_bits(_counter_word(_first_coordinate())),
        **activity_identity,
    }
    if started != expected_started:
        raise LifecycleError("retained ACTIVITY_STARTED differs from bound first word")
    rebuilt = validation.get("panel_commit")
    if not isinstance(rebuilt, Mapping):
        raise LifecycleError("rebuilt panel commit is absent")
    validate_panel_commit(rebuilt)
    retained_panel_commit = read_canonical_json(root / PANEL_COMMIT_NAME)
    validate_panel_commit(retained_panel_commit)
    if retained_panel_commit != rebuilt:
        raise LifecycleError("retained PANEL_COMMIT differs from rebuilt cell commit set")
    return {
        "panel_sha256": document_sha256(panel),
        "backend_receipt_sha256": backend_sha,
        "coordinate_binding_sha256": binding_sha,
        "lease_scope_sha256": str(bindings["lease_scope_sha256"]),
        "lease_receipt_inventory_sha256": lease_inventory_sha,
        "activity_intent_sha256": document_sha256(intent),
        "activity_started_sha256": document_sha256(started),
        "rebuilt_panel_commit_sha256": str(rebuilt["panel_commit_sha256"]),
        "validation_sha256": str(validation["validation_sha256"]),
    }


def validate_production_complete_package(root: Path) -> dict[str, object]:
    root = _require_result_root(Path(root))
    validation = validate_complete_package(root)
    receipt_bindings = _retained_receipt_bindings(root, validation)
    complete = read_canonical_json(root / COMPLETE_NAME)
    validated = validate_complete_marker(complete)
    expected = lifecycle_build_complete_marker(validation, receipt_bindings=receipt_bindings)
    if validated != expected:
        raise LifecycleError("retained COMPLETE differs from rebuilt cells and receipts")
    return validation


def run_full_panel(permit: ProductionPermit) -> dict[str, object]:
    """Execute only exact width-32 native groups and seal the blinded package."""

    if permit._token is not _REAL_PERMIT_TOKEN:
        raise ProductionAdmissionError("fixture admission cannot run production")
    initialize_private_panel(permit)
    _write_activity_intent(permit)
    inventory = resume_inventory(permit.result_root)
    if inventory.unexpected_paths:
        raise LifecycleError("resume root contains unexpected private artifacts")
    committed = set(inventory.committed)
    for replicate in range(REPLICATES):
        identities = {CellIdentity(arm, replicate) for arm in ARMS}
        if identities.issubset(committed):
            continue
        permit.assert_active(verify_source=True)
        _run_replicate(permit, replicate, native_runner=run_native_batch)
        committed.update(identities)
    validation = validate_complete_package(permit.result_root)
    if validation.get("cell_count") != 512:
        raise LifecycleError("sealed package does not contain the exact panel")
    panel_commit = validation["panel_commit"]
    assert isinstance(panel_commit, Mapping)
    atomic_write_once(
        permit.result_root / PANEL_COMMIT_NAME,
        panel_commit,
        authorized_root=permit.result_root,
    )
    receipt_bindings = _retained_receipt_bindings(permit.result_root, validation)
    complete = lifecycle_build_complete_marker(
        validation, receipt_bindings=receipt_bindings
    )
    atomic_write_once(
        permit.result_root / COMPLETE_NAME,
        complete,
        authorized_root=permit.result_root,
    )
    return complete


def _load_cell_aggregates(root: Path) -> dict[str, list[Mapping[str, object]]]:
    values: dict[str, list[Mapping[str, object]]] = {arm: [] for arm in ARMS}
    for arm in ARMS:
        for replicate in range(REPLICATES):
            packet = read_canonical_json(cell_packet_path(root, CellIdentity(arm, replicate)))
            aggregate = packet.get("aggregate")
            if not isinstance(aggregate, Mapping):
                raise LifecycleError("complete cell aggregate is absent")
            values[arm].append(aggregate)
    return values


def _interval_json(interval: az.PairedInterval) -> dict[str, object]:
    return {
        "mean": interval.mean,
        "sample_sd": interval.sample_sd,
        "lower": interval.lower,
        "upper": interval.upper,
        "n": interval.n,
    }


def _analyze_aggregate_panel(
    aggregates: Mapping[str, Sequence[Mapping[str, object]]]
) -> dict[str, object]:
    if set(aggregates) != set(ARMS) or any(len(aggregates[arm]) != REPLICATES for arm in ARMS):
        raise LifecycleError("pure analysis requires the exact four-by-128 aggregate panel")
    endpoints = {
        arm: [
            az.ReplicateEndpoints(float(row["mean_value"]), float(row["tail_value"]))
            for row in aggregates[arm]
        ]
        for arm in ARMS
    }
    inference = az.full_panel_inference(endpoints)
    all_rows = [row for arm in ARMS for row in aggregates[arm]]
    road_fit_facts = az.RoadFitAuditFacts(
        **{
            name: all(bool(row["road_fit_facts"][name]) for row in all_rows)  # type: ignore[index]
            for name in az.RoadFitAuditFacts.__dataclass_fields__
        }
    )
    sham_facts = az.ShamValidityFacts(
        **{
            name: all(bool(row["sham_validity_facts"][name]) for row in all_rows)  # type: ignore[index]
            for name in az.ShamValidityFacts.__dataclass_fields__
        }
    )
    tick_audit_valid = all(bool(row["tick_audit_valid"]) for row in all_rows)
    endpoint_audit_valid = all(bool(row["endpoint_audit_valid"]) for row in all_rows)
    arm_transitions_exact = all(bool(row["arm_transition_audit_valid"]) for row in all_rows)
    raw_conformant = all(bool(row["raw_conformant"]) for row in all_rows)
    pairing_valid = all(
        len({str(aggregates[arm][replicate]["tape_commitment_sha256"]) for arm in ARMS}) == 1
        for replicate in range(REPLICATES)
    )
    package_facts = az.PackageValidityFacts(
        exact_identity=True,
        exact_4x128_cells=True,
        exact_20_block_balance=True,
        controller_free_pairing=pairing_valid,
        no_action_word=True,
        arm_transitions_exact=arm_transitions_exact,
        ledgers_complete=tick_audit_valid and endpoint_audit_valid,
        raw_conformant=raw_conformant,
        no_missing_duplicate_substituted_imputed_deleted_or_selected_cell=True,
        atomic_complete_package=True,
        road_fit=road_fit_facts,
    )
    package_valid = package_facts.valid
    sham_valid = sham_facts.valid
    scheduled = {
        arm: sum(int(row["scheduled_t0_decisions"]) for row in aggregates[arm])
        for arm in ARMS
    }
    shells = {
        arm: sum(int(row["action_shell_count"]) for row in aggregates[arm])
        for arm in ARMS
    }
    action_support = az.action_shell_support_ok(
        scheduled_t0_by_arm=scheduled, action_shell_by_arm=shells
    )
    road_rows = aggregates[ARMS[3]]
    effective_encounters = sum(int(row["effective_road_patch_count"]) for row in road_rows)
    effective_replicates = sum(int(row["effective_road_patch_count"]) > 0 for row in road_rows)
    effective_support = az.effective_road_patch_support_ok(
        encounters=effective_encounters,
        replicates_with_any=effective_replicates,
    )

    def hard(arm: str) -> az.HardSafetyFacts:
        totals = {key: 0 for key in HARD_FAILURE_KEYS}
        for row in aggregates[arm]:
            failures = row["hard_failures"]
            assert isinstance(failures, Mapping)
            for key in HARD_FAILURE_KEYS:
                totals[key] += int(failures[key])
        return az.HardSafetyFacts(**totals)

    never_mean = math.fsum(endpoint.mean for endpoint in endpoints[ARMS[0]]) / REPLICATES
    never_tail = math.fsum(endpoint.tail for endpoint in endpoints[ARMS[0]]) / REPLICATES
    never_is_competent = az.never_competent(
        package_valid=package_valid,
        hard_safety=hard(ARMS[0]),
        mean_value=never_mean,
        tail_value=never_tail,
    )
    road_overrides = [int(row["safety_overrides"]) for row in aggregates[ARMS[3]]]
    never_overrides = [int(row["safety_overrides"]) for row in aggregates[ARMS[0]]]
    override_interval = az.override_interval(road_overrides, never_overrides)
    road_is_nonharmful = az.road_nonharm(
        hard_safety=hard(ARMS[3]),
        road_override_counts=road_overrides,
        never_override_counts=never_overrides,
    )
    road_failure = None
    if not road_is_nonharmful:
        failures = hard(ARMS[3]).concrete_failures()
        road_failure = (
            ",".join(failures)
            if failures
            else "paired_override_ucb95_exceeds_0.01"
        )
    common_reason = None
    if not package_valid:
        common_reason = "TBVUUS_PACKAGE_AUDIT_INVALID"
    elif not sham_valid:
        common_reason = "TBVUUS_SHAM_AUDIT_INVALID"
    facts = az.ResultMapFacts(
        package_valid=package_valid,
        sham_valid=sham_valid,
        common_host_valid=True,
        pairing_valid=pairing_valid,
        endpoint_audit_valid=endpoint_audit_valid,
        common_package_nonidentification_reason=common_reason,
        never_is_competent=never_is_competent,
        action_shell_support=action_support,
        effective_payload_support=effective_support,
        road_is_nonharmful=road_is_nonharmful,
        road_nonharm_failure_fact=road_failure,
        gate_statuses=inference.gate_statuses,
    )
    outcome = az.evaluate_result_map(facts)
    return {
        "package_valid": package_valid,
        "sham_valid": sham_valid,
        "pairing_valid": pairing_valid,
        "endpoint_audit_valid": endpoint_audit_valid,
        "package_validity_facts": {
            **{key: value for key, value in asdict(package_facts).items() if key != "road_fit"},
            "road_fit": asdict(road_fit_facts),
        },
        "sham_validity_facts": asdict(sham_facts),
        "never_update_comparator_competent": never_is_competent,
        "action_shell_support": action_support,
        "effective_payload_support": effective_support,
        "road_nonharm": road_is_nonharmful,
        "support_counts": {
            "scheduled_t0_by_arm": scheduled,
            "action_shell_by_arm": shells,
            "effective_road_patch_encounters": effective_encounters,
            "replicates_with_effective_road_patch": effective_replicates,
            "effective_road_patch_by_route": {
                route: sum(
                    int(row["effective_road_patch_by_route"][route])  # type: ignore[index]
                    for row in road_rows
                )
                for route in ("SHORT", "LONG")
            },
        },
        "nonharm_diagnostics": {
            "paired_override_interval": _interval_json(override_interval),
            "road_hard_failures": asdict(hard(ARMS[3])),
            "never_hard_failures": asdict(hard(ARMS[0])),
            "road_hard_safe": hard(ARMS[3]).safe,
            "never_hard_safe": hard(ARMS[0]).safe,
            "override_ucb95_at_most_0_01": override_interval.upper <= 0.01,
            "road_nonharm": road_is_nonharmful,
        },
        "never_endpoints": {"mean": never_mean, "tail": never_tail},
        "intervals": {
            name: _interval_json(interval) for name, interval in inference.intervals.items()
        },
        "gate_statuses": dict(inference.gate_statuses),
        "result_map": {
            "branch": outcome.branch,
            "detail": outcome.detail,
            "gate_statuses": dict(outcome.gate_statuses),
            "timing_question_portfolio_eligible": outcome.timing_question_portfolio_eligible,
        },
    }


def _complete_panel_analysis(root: Path) -> dict[str, object]:
    """Pure exhaustive reduction; caller must cross COMPLETE+CM firewall first."""

    validate_complete_package(root)
    return _analyze_aggregate_panel(_load_cell_aggregates(root))


def _release_result_at_bound_root(
    *,
    root: Path,
    package_validator: Callable[[Path], dict[str, object]],
    analyzer: Callable[[Path], dict[str, object]],
) -> dict[str, object]:
    """Shared fixed-path release core; public callers cannot select these paths."""

    root = Path(root).resolve()
    destination = root / "RESULT_V2.json"
    authorization_path = root / "RESULT_V2_RELEASE_AUTHORIZATION.json"
    complete = read_canonical_json(root / COMPLETE_NAME)
    validate_complete_marker(complete)
    acceptance = read_canonical_json(root / CM_ACCEPTANCE_NAME)
    validate_cm_acceptance(acceptance)
    if acceptance["complete_sha256"] != complete["complete_sha256"]:
        raise ProductionAdmissionError("CM acceptance does not bind retained COMPLETE")
    if destination.exists():
        raise FileExistsError("TBVUUS RESULT_V2 release is write-once")
    authorization = read_canonical_json(authorization_path)
    receipt = build_result_release_receipt(
        authorization,
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )
    installed_receipt_before = validate_installed_portfolio_em_sequencing_receipt(
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )
    before = package_validator(root)
    analysis = analyzer(root)
    after = package_validator(root)
    if before != after:
        raise LifecycleError("complete package changed during pure analysis")
    authorization_after = read_canonical_json(authorization_path)
    if authorization_after != authorization:
        raise LifecycleError("RESULT_V2 release authorization changed during analysis")
    validate_result_release_authorization(
        authorization_after,
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )
    installed_receipt_after = validate_installed_portfolio_em_sequencing_receipt(
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )
    if installed_receipt_after != installed_receipt_before:
        raise LifecycleError("Portfolio-EM sequencing receipt changed during analysis")
    envelope = {
        "schema": RESULT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "complete_sha256": complete["complete_sha256"],
        "cm_acceptance_sha256": acceptance["cm_acceptance_sha256"],
        "complete_panel": True,
        "analysis": analysis,
        "release_receipt": receipt,
    }
    publish_result_once(
        root,
        envelope,
    )
    return envelope


def _release_result_for_test(
    *,
    root: Path,
    package_validator: Callable[[Path], dict[str, object]],
    analyzer: Callable[[Path], dict[str, object]],
) -> dict[str, object]:
    """TEST-only fixture seam; it is never used by the public CLI or release API."""

    fixture_root = Path(root).resolve()
    artifacts_root = (_repo_root() / "artifacts").resolve()
    try:
        fixture_root.relative_to(artifacts_root)
    except ValueError:
        pass
    else:
        raise ProductionAdmissionError("TEST release seam refuses repository artifacts/")
    return _release_result_at_bound_root(
        root=fixture_root,
        package_validator=package_validator,
        analyzer=analyzer,
    )


def release_result() -> dict[str, object]:
    """Release only the frozen canonical RESULT_V2 destination."""

    if _require_result_root(CANONICAL_RESULT_ROOT) != CANONICAL_RESULT_ROOT:
        raise ProductionAdmissionError("canonical TBVUUS result root binding differs")
    return _release_result_at_bound_root(
        root=CANONICAL_RESULT_ROOT,
        package_validator=validate_production_complete_package,
        analyzer=_complete_panel_analysis,
    )


def coordinate_binding_proposal() -> dict[str, object]:
    proposal = coordinate_proposal()
    return {
        **proposal,
        "coordinate_row_count": coordinate_row_count(),
        "coordinate_rows_sha256_present": False,
        "experiment_id_present": False,
        "root_authorization_present": False,
    }


def run_fixture_benchmark(
    fixture_root: Path,
    *,
    native_runner: Callable[[Sequence[FixtureCase]], Sequence[Any]] = run_native_batch,
) -> dict[str, object]:
    """Exercise the full runner seam on literal tapes without production authority.

    The root must be outside repository ``artifacts/``.  This function accepts
    neither a permit nor a namespace, creates no coordinate word or activity
    marker, and produces no COMPLETE/result artifact.
    """

    root = Path(fixture_root).resolve(strict=False)
    artifacts = (_repo_root() / "artifacts").resolve()
    try:
        root.relative_to(artifacts)
    except ValueError:
        pass
    else:
        raise ProductionAdmissionError("fixture benchmark root cannot be under artifacts/")
    marker = {
        "schema": "ONLGR-TBVUUS-R03-FIXTURE-RUNNER-BENCHMARK-v1",
        "namespace": FIXTURE_NAMESPACE,
        "production_eligible": False,
        "production_words": False,
        "activity_marker_allowed": False,
        "replicates": 1,
        "native_batch_width": PRODUCTION_BATCH_WIDTH,
    }
    if root.exists():
        if read_canonical_json(root / "FIXTURE_BENCHMARK.json") != marker:
            raise ProductionAdmissionError("fixture benchmark root is not exact/resumable")
        inventory = resume_inventory(root)
        expected = {CellIdentity(arm, 0) for arm in ARMS}
        if set(inventory.committed) != expected:
            raise LifecycleError("fixture benchmark resume inventory differs")
        return {
            "schema": marker["schema"],
            "native_calls": 0,
            "resume_only": True,
            "committed_cells": len(inventory.committed),
            "missing_production_cells": len(inventory.missing),
            "production_words": False,
            "complete_or_result_written": False,
        }
    root.mkdir(parents=True)
    atomic_write_once(root / "FIXTURE_BENCHMARK.json", marker, authorized_root=root)
    materialized_all: list[tuple[EncounterIdentity, EncounterSpec, FixtureTape]] = []
    results_by_arm: dict[str, list[Any]] = {arm: [] for arm in ARMS}
    call_widths: list[int] = []
    for group in native_group_plan(0):
        materialized: list[tuple[EncounterIdentity, EncounterSpec, FixtureTape]] = []
        for encounter in group:
            direction, lateral = _template(encounter)
            spec = EncounterSpec(RouteClass[encounter.route_class], direction, lateral)
            # Literal fixture values carry no counter address or production word.
            tape = FixtureTape.constant(spec, normal=0.0, uniform=0.5)
            materialized.append((encounter, spec, tape))
        materialized_all.extend(materialized)
        cases = grouped_fixture_cases(materialized, logical_namespace=FIXTURE_NAMESPACE)
        observed = tuple(native_runner(cases))
        call_widths.append(len(cases))
        if len(observed) != PRODUCTION_BATCH_WIDTH:
            raise RuntimeError("fixture benchmark native batch width differs")
        for index, result in enumerate(observed):
            _, arm_index = divmod(index, len(ARMS))
            results_by_arm[ARMS[arm_index]].append(result)
    tape_sha = _tape_commitment(materialized_all)
    sham_rows = [
        _sham_validity_facts(never, sham, common_tapes_equal=True)
        for never, sham in zip(results_by_arm[ARMS[0]], results_by_arm[ARMS[1]])
    ]
    sham_facts = az.ShamValidityFacts(
        **{
            name: all(getattr(row, name) for row in sham_rows)
            for name in az.ShamValidityFacts.__dataclass_fields__
        }
    )
    raw_valid = all(_raw_conformant(result) for result in results_by_arm[ARMS[2]])
    bindings = {
        key: hashlib.sha256(("FIXTURE-ONLY|" + key).encode("ascii")).hexdigest()
        for key in BINDING_KEYS
    }
    aggregates: dict[str, Mapping[str, object]] = {}
    cell_material: dict[str, tuple[Mapping[str, object], Mapping[str, bytes]]] = {}
    for arm in ARMS:
        aggregate, sidecars = _build_cell_material(
            arm_name=arm,
            replicate=0,
            results=results_by_arm[arm],
            tape_commitment_sha256=tape_sha,
            sham_facts=sham_facts,
            raw_valid=raw_valid,
        )
        aggregates[arm] = aggregate
        cell_material[arm] = (aggregate, sidecars)
        _write_cell_material(
            root,
            bindings=bindings,
            identity=CellIdentity(arm, 0),
            aggregate=aggregate,
            sidecars=sidecars,
        )
    inventory = resume_inventory(root)
    expected_cells = {CellIdentity(arm, 0) for arm in ARMS}
    if set(inventory.committed) != expected_cells:
        raise LifecycleError("fixture benchmark did not commit its exact four cells")
    # Exercise idempotent same-coordinate resume without another native call.
    for arm in ARMS:
        aggregate, sidecars = cell_material[arm]
        _write_cell_material(
            root,
            bindings=bindings,
            identity=CellIdentity(arm, 0),
            aggregate=aggregate,
            sidecars=sidecars,
        )
    resumed = resume_inventory(root)
    fixture_analysis = _analyze_aggregate_panel(
        {arm: [aggregates[arm]] * REPLICATES for arm in ARMS}
    )
    analysis_digest = _audit_sha256(fixture_analysis)
    durable_bytes = sum(path.stat().st_size for path in root.rglob("*") if path.is_file())
    return {
        "schema": marker["schema"],
        "native_calls": len(call_widths),
        "native_call_widths": call_widths,
        "resume_only": False,
        "committed_cells": len(resumed.committed),
        "missing_production_cells": len(resumed.missing),
        "analysis_sha256": analysis_digest,
        "analysis_diagnostic_keys": sorted(
            key for key in fixture_analysis if key in {"support_counts", "nonharm_diagnostics"}
        ),
        "durable_bytes": durable_bytes,
        "production_words": False,
        "complete_or_result_written": False,
    }


def future_resource_request() -> dict[str, object]:
    live = live_source_identity()
    module = (
        "experiments.candidates.opportunity_normalized_lease_gated_rebinding."
        "tbvuus_r03.runner"
    )
    return {
        "schema": "ONLGR-TBVUUS-R03-FUTURE-COMMAND-RESOURCE-REQUEST-v1",
        "direction_id": DIRECTION_ID,
        "stage": STAGE,
        "science_revision": SCIENCE_REVISION,
        "activity_started": False,
        "coordinate_binding_required": True,
        "root_lease_required": True,
        "canonical_result_root": str(CANONICAL_RESULT_ROOT),
        "canonical_result_v2_path": str(CANONICAL_RESULT_V2_PATH),
        "canonical_result_v2_release_authorization_path": str(
            CANONICAL_RESULT_V2_RELEASE_AUTHORIZATION_PATH
        ),
        "canonical_portfolio_em_sequencing_receipt_path": str(
            CANONICAL_PORTFOLIO_EM_SEQUENCING_RECEIPT_PATH
        ),
        "backend_component": ONLGR_TBVUUS_R03_FULL_HOST,
        "backend": "cpp",
        "batch_width": PRODUCTION_BATCH_WIDTH,
        "max_cpu_workers": MAX_CPU_WORKERS,
        "max_ram_bytes": MAX_RAM_BYTES,
        "expected_storage_bytes": EXPECTED_STORAGE_BYTES,
        "max_storage_bytes": MAX_STORAGE_BYTES,
        "commands": {
            "preflight": [
                sys.executable, "-m", module, "preflight",
                "--preactivity-freeze", "<ROOT_FREEZE_JSON>",
                "--coordinate-binding", "<ROOT_BINDING_JSON>",
                "--lease", "<ROOT_LEASE_JSON>",
                "--result-root", "<FRESH_ARTIFACT_ROOT>",
            ],
            "run": [
                sys.executable, "-m", module, "run",
                "--preactivity-freeze", "<ROOT_FREEZE_JSON>",
                "--coordinate-binding", "<ROOT_BINDING_JSON>",
                "--lease", "<ROOT_LEASE_JSON>",
                "--result-root", "<FRESH_ARTIFACT_ROOT>",
            ],
            "analyze_after_root_release_authorization": [
                sys.executable, "-m", module, "analyze",
            ],
        },
        "live_identity": live,
    }


def _read(path: Path) -> dict[str, object]:
    return read_canonical_json(path)


def _admit_from_args(args: argparse.Namespace) -> ProductionPermit:
    return admit_production(
        preactivity_freeze=_read(args.preactivity_freeze),
        coordinate_binding=_read(args.coordinate_binding),
        direction_lease=_read(args.lease),
        result_root=args.result_root,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onlgr-tbvuus-r03")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run"):
        command = sub.add_parser(name)
        command.add_argument("--preactivity-freeze", type=Path, required=True)
        command.add_argument("--coordinate-binding", type=Path, required=True)
        command.add_argument("--lease", type=Path, required=True)
        command.add_argument("--result-root", type=Path, required=True)
    analyze = sub.add_parser("analyze")
    sub.add_parser("coordinate-proposal")
    sub.add_parser("resource-request")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            permit = _admit_from_args(args)
            print(json.dumps({"admitted": True, "activity_started": False, "backend_receipt_sha256": permit.backend_receipt_sha256}, sort_keys=True))
        elif args.command == "run":
            complete = run_full_panel(_admit_from_args(args))
            print(json.dumps({"complete": True, "complete_sha256": complete["complete_sha256"], "result_exposed": False}, sort_keys=True))
        elif args.command == "analyze":
            result = release_result()
            print(json.dumps({"complete_result_released": True, "result_sha256": document_sha256(result)}, sort_keys=True))
        elif args.command == "coordinate-proposal":
            print(json.dumps(coordinate_binding_proposal(), sort_keys=True))
        else:
            print(json.dumps(future_resource_request(), sort_keys=True))
        return 0
    except (FileNotFoundError, FileExistsError, PermissionError, RuntimeError, TypeError, ValueError) as exc:
        print(f"FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
