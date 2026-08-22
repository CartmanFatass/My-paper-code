"""Write-once, same-coordinate lifecycle and final-result firewall for r03."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Iterable
import uuid

from .contracts import (
    BINDING_KEYS,
    CM_ACCEPTANCE_SCHEMA,
    COMPLETE_SCHEMA,
    HOST_ID,
    PRODUCTION_NAMESPACE,
    PORTFOLIO_EM_SEQUENCING_RECEIPT_SCHEMA,
    RESULT_SCHEMA,
    RESULT_RELEASE_AUTHORIZATION_SCHEMA,
    RESULT_RELEASE_ID_SCHEMA,
    RESULT_RELEASE_RECEIPT_SCHEMA,
    SCIENCE_REVISION,
    SIDECAR_SCHEMAS,
    STAGE,
    canonical_json_bytes,
    document_sha256,
)
from .serialization import (
    CellIdentity,
    SerializationError,
    build_panel_commit,
    cell_commit_path,
    cell_packet_path,
    expected_cell_identities,
    sha256_bytes,
    sidecar_path,
    validate_cell_commit,
    validate_cell_packet,
    validate_panel_commit,
    validate_sidecar_payload,
)


PANEL_COMMIT_NAME = "PANEL_COMMIT.json"
COMPLETE_NAME = "COMPLETE.json"
CM_ACCEPTANCE_NAME = "CM_TECHNICAL_ACCEPTANCE.json"
RESULT_V2_NAME = "RESULT_V2.json"
RESULT_V2_RELEASE_AUTHORIZATION_NAME = "RESULT_V2_RELEASE_AUTHORIZATION.json"
PORTFOLIO_EM_SEQUENCING_RECEIPT_NAME = (
    "PORTFOLIO_EM_RESULT_INTAKE_SEQUENCING_RECEIPT.json"
)
PORTFOLIO_EM_ACTOR = "/root/em_onlgr_tbvuus_r03"
RELEASE_OPERATOR = "/root"
COMPLETE_BINDING_KEYS = (
    "panel_sha256",
    "backend_receipt_sha256",
    "coordinate_binding_sha256",
    "lease_scope_sha256",
    "lease_receipt_inventory_sha256",
    "activity_intent_sha256",
    "activity_started_sha256",
    "rebuilt_panel_commit_sha256",
    "validation_sha256",
)
_PARTIAL_FIELD_NAMES = frozenset(
    {
        "partial",
        "partial_result",
        "partial_results",
        "interim",
        "interim_result",
        "interim_results",
        "selected_cells",
        "selected_replicates",
        "best_attempt",
        "early_stop",
    }
)


class LifecycleError(RuntimeError):
    pass


def _require_under(path: Path, root: Path) -> tuple[Path, Path]:
    resolved_path, resolved_root = path.resolve(strict=False), root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise LifecycleError("artifact path escapes its authorized root") from exc
    return resolved_path, resolved_root


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: Path, payload: bytes, *, authorized_root: Path) -> Path:
    """Install bytes once after file fsync; exact replay is idempotent."""

    destination, root = _require_under(Path(path), Path(authorized_root))
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() == payload:
            return destination
        raise FileExistsError(f"write-once artifact differs: {destination}")
    pending = destination.with_name(f".{destination.name}.pending")
    if pending.exists():
        if pending.read_bytes() != payload:
            raise FileExistsError(f"same-coordinate pending payload differs: {pending}")
        pending.unlink()
    with pending.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(pending, destination)
    except FileExistsError:
        if destination.read_bytes() != payload:
            raise FileExistsError(f"concurrent write-once artifact differs: {destination}")
    finally:
        if pending.exists():
            pending.unlink()
    _fsync_directory(destination.parent)
    return destination


def atomic_write_once(path: Path, value: object, *, authorized_root: Path) -> Path:
    return atomic_write_bytes(path, canonical_json_bytes(value), authorized_root=authorized_root)


def read_canonical_json(path: Path) -> dict[str, object]:
    encoded = Path(path).read_bytes()
    try:
        value = json.loads(encoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"artifact is not valid UTF-8 JSON: {path}") from exc
    try:
        canonical = canonical_json_bytes(value)
    except ValueError as exc:
        raise LifecycleError(f"{label} is not finite canonical JSON") from exc
    if not isinstance(value, dict) or canonical != encoded:
        raise LifecycleError(f"artifact is not canonical JSON plus LF: {path}")
    return value


@dataclass(frozen=True)
class ResumeInventory:
    committed: tuple[CellIdentity, ...]
    uncommitted_packets: tuple[CellIdentity, ...]
    pending: tuple[CellIdentity, ...]
    missing: tuple[CellIdentity, ...]
    unexpected_paths: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            len(self.committed) == len(expected_cell_identities())
            and not self.uncommitted_packets
            and not self.pending
            and not self.missing
            and not self.unexpected_paths
        )


def _expected_artifact_paths(root: Path) -> set[Path]:
    expected: set[Path] = set()
    for identity in expected_cell_identities():
        expected.add(cell_packet_path(root, identity).resolve(strict=False))
        expected.add(cell_commit_path(root, identity).resolve(strict=False))
        for kind in SIDECAR_SCHEMAS:
            expected.add(sidecar_path(root, identity, kind).resolve(strict=False))
    return expected


def _unexpected_private_paths(root: Path) -> tuple[str, ...]:
    expected = _expected_artifact_paths(root)
    observed: set[Path] = set()
    for directory in ("private-cells", "private-commits", "private-sidecars"):
        base = root / directory
        if base.exists():
            observed.update(path.resolve() for path in base.rglob("*") if path.is_file())
    return tuple(sorted(str(path) for path in observed - expected if not path.name.endswith(".pending")))


def _validate_committed_cell(root: Path, identity: CellIdentity) -> None:
    packet_path = cell_packet_path(root, identity)
    commit_path = cell_commit_path(root, identity)
    packet = read_canonical_json(packet_path)
    commit = read_canonical_json(commit_path)
    if validate_cell_packet(packet) != identity or validate_cell_commit(commit) != identity:
        raise LifecycleError("retained cell identity differs from its path")
    if commit["cell_sha256"] != document_sha256(packet):
        raise LifecycleError("cell commit does not authenticate its packet")
    sidecars = packet["sidecars"]
    assert isinstance(sidecars, Mapping)
    commit_sidecars = commit["sidecar_sha256"]
    assert isinstance(commit_sidecars, Mapping)
    for kind in SIDECAR_SCHEMAS:
        retained = sidecar_path(root, identity, kind)
        payload = retained.read_bytes()
        validate_sidecar_payload(kind, identity, payload)
        reference = sidecars[kind]
        assert isinstance(reference, Mapping)
        if len(payload) != reference["bytes"] or sha256_bytes(payload) != reference["sha256"]:
            raise LifecycleError(f"{kind} sidecar bytes differ from the cell reference")
        if commit_sidecars[kind] != reference["sha256"]:
            raise LifecycleError(f"{kind} sidecar commit digest differs")


def resume_inventory(root: Path) -> ResumeInventory:
    """Return a blinded exact-coordinate resume inventory; never replace cells."""

    root = Path(root).resolve()
    committed: list[CellIdentity] = []
    uncommitted: list[CellIdentity] = []
    pending: list[CellIdentity] = []
    missing: list[CellIdentity] = []
    for identity in expected_cell_identities():
        packet = cell_packet_path(root, identity)
        commit = cell_commit_path(root, identity)
        expected_files = (packet, commit) + tuple(
            sidecar_path(root, identity, kind) for kind in SIDECAR_SCHEMAS
        )
        pending_files = tuple(
            path.with_name(f".{path.name}.pending") for path in expected_files
        )
        if any(path.exists() for path in pending_files):
            pending.append(identity)
            continue
        if commit.exists():
            if not all(path.exists() for path in expected_files):
                raise LifecycleError("committed cell is missing its packet or sidecar")
            _validate_committed_cell(root, identity)
            committed.append(identity)
        elif packet.exists() or any(path.exists() for path in expected_files[2:]):
            uncommitted.append(identity)
        else:
            missing.append(identity)
    return ResumeInventory(
        tuple(committed),
        tuple(uncommitted),
        tuple(pending),
        tuple(missing),
        _unexpected_private_paths(root),
    )


def _load_commits(root: Path, identities: Iterable[CellIdentity]) -> list[dict[str, object]]:
    return [read_canonical_json(cell_commit_path(root, identity)) for identity in identities]


def validate_complete_package(root: Path) -> dict[str, object]:
    """Authenticate exactly 512 committed cells and one uniform binding set."""

    root = Path(root).resolve()
    inventory = resume_inventory(root)
    if not inventory.complete:
        raise LifecycleError("complete package requires exactly 512 clean committed cells")
    identities = expected_cell_identities()
    commits = _load_commits(root, identities)
    panel_commit = build_panel_commit(commits)
    validate_panel_commit(panel_commit)
    binding_sets: set[tuple[tuple[str, str], ...]] = set()
    for identity in identities:
        packet = read_canonical_json(cell_packet_path(root, identity))
        bindings = packet["bindings"]
        assert isinstance(bindings, Mapping)
        binding_sets.add(tuple((key, str(bindings[key])) for key in BINDING_KEYS))
    if len(binding_sets) != 1:
        raise LifecycleError("complete package mixes distinct immutable binding sets")
    uniform_bindings = dict(next(iter(binding_sets)))
    receipt = {
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "cell_count": len(identities),
        "panel_commit": panel_commit,
        "uniform_bindings": uniform_bindings,
        "no_missing_duplicate_substituted_imputed_deleted_or_selected_cell": True,
        "complete": True,
    }
    return {**receipt, "validation_sha256": document_sha256(receipt)}


def build_complete_marker(
    validation: Mapping[str, object], *, receipt_bindings: Mapping[str, object]
) -> dict[str, object]:
    if validation.get("complete") is not True or validation.get("cell_count") != 512:
        raise LifecycleError("complete marker requires a successful 512-cell validation")
    panel = validation.get("panel_commit")
    if not isinstance(panel, Mapping):
        raise LifecycleError("complete marker requires the authenticated panel commit")
    validate_panel_commit(panel)
    if set(receipt_bindings) != set(COMPLETE_BINDING_KEYS):
        raise LifecycleError("COMPLETE retained-receipt binding schema differs")
    checked_bindings: dict[str, str] = {}
    for key in COMPLETE_BINDING_KEYS:
        digest = receipt_bindings[key]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise LifecycleError(f"COMPLETE {key} must be lowercase SHA-256")
        checked_bindings[key] = digest
    if checked_bindings["rebuilt_panel_commit_sha256"] != panel["panel_commit_sha256"]:
        raise LifecycleError("COMPLETE rebuilt panel commit differs from cell validation")
    if checked_bindings["validation_sha256"] != validation.get("validation_sha256"):
        raise LifecycleError("COMPLETE validation receipt differs")
    body = {
        "schema": COMPLETE_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "panel_commit_sha256": panel["panel_commit_sha256"],
        **checked_bindings,
        "cell_count": 512,
        "all_assigned_cells_complete": True,
        "atomic_package": True,
        "partial_release_allowed": False,
    }
    return {**body, "complete_sha256": document_sha256(body)}


def validate_complete_marker(value: Mapping[str, object]) -> dict[str, object]:
    keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "panel_commit_sha256",
        "cell_count",
        "all_assigned_cells_complete",
        "atomic_package",
        "partial_release_allowed",
        "complete_sha256",
        *COMPLETE_BINDING_KEYS,
    }
    if set(value) != keys:
        raise LifecycleError("COMPLETE marker schema differs")
    fixed = {
        "schema": COMPLETE_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "cell_count": 512,
        "all_assigned_cells_complete": True,
        "atomic_package": True,
        "partial_release_allowed": False,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise LifecycleError("COMPLETE marker frozen identity differs")
    body = {key: value[key] for key in value if key != "complete_sha256"}
    for key in ("panel_commit_sha256", *COMPLETE_BINDING_KEYS):
        digest = value[key]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise LifecycleError(f"COMPLETE {key} digest differs")
    if value["panel_commit_sha256"] != value["rebuilt_panel_commit_sha256"]:
        raise LifecycleError("COMPLETE retained and rebuilt panel commits differ")
    if value["complete_sha256"] != document_sha256(body):
        raise LifecycleError("COMPLETE marker digest differs")
    return dict(value)


def seal_complete_package(
    root: Path, *, receipt_bindings: Mapping[str, object]
) -> dict[str, object]:
    validation = validate_complete_package(root)
    panel = validation["panel_commit"]
    assert isinstance(panel, Mapping)
    atomic_write_once(Path(root) / PANEL_COMMIT_NAME, panel, authorized_root=Path(root))
    marker = build_complete_marker(validation, receipt_bindings=receipt_bindings)
    atomic_write_once(Path(root) / COMPLETE_NAME, marker, authorized_root=Path(root))
    return marker


def build_cm_acceptance(*, complete_sha256: str, acceptance_facts_sha256: str) -> dict[str, object]:
    for label, digest in (
        ("complete", complete_sha256),
        ("acceptance facts", acceptance_facts_sha256),
    ):
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise LifecycleError(f"{label} digest must be lowercase SHA-256")
    body = {
        "schema": CM_ACCEPTANCE_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "complete_sha256": complete_sha256,
        "acceptance_facts_sha256": acceptance_facts_sha256,
        "technically_accepted": True,
        "complete_panel": True,
        "partial_interpretation_allowed": False,
    }
    return {**body, "cm_acceptance_sha256": document_sha256(body)}


def validate_cm_acceptance(value: Mapping[str, object]) -> dict[str, object]:
    expected = build_cm_acceptance(
        complete_sha256=str(value.get("complete_sha256", "")),
        acceptance_facts_sha256=str(value.get("acceptance_facts_sha256", "")),
    )
    if dict(value) != expected:
        raise LifecycleError("CM technical acceptance schema or digest differs")
    return expected


def _require_lowercase_sha256(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise LifecycleError(f"{label} must be lowercase SHA-256")
    return value


@dataclass(frozen=True)
class InstalledPortfolioEMSequencingReceipt:
    path: Path
    document: dict[str, object]
    installed_bytes_sha256: str


def _read_installed_canonical_regular_file(path: Path, *, label: str) -> tuple[dict[str, object], bytes]:
    """Read exact installed bytes while rejecting links, reparse points, and drift."""

    path = Path(path)
    try:
        before = path.lstat()
    except FileNotFoundError as exc:
        raise LifecycleError(f"{label} is missing") from exc
    file_attributes = getattr(before, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if stat.S_ISLNK(before.st_mode) or file_attributes & reparse_flag:
        raise LifecycleError(f"{label} must not be a symlink or reparse target")
    if not stat.S_ISREG(before.st_mode):
        raise LifecycleError(f"{label} must be an installed regular file")
    encoded = path.read_bytes()
    after = path.lstat()
    if (
        stat.S_ISLNK(after.st_mode)
        or getattr(after, "st_file_attributes", 0) & reparse_flag
        or not stat.S_ISREG(after.st_mode)
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or getattr(before, "st_ino", None) != getattr(after, "st_ino", None)
    ):
        raise LifecycleError(f"{label} changed while its installed bytes were read")
    try:
        decoded = encoded.decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"{label} is not valid BOM-free UTF-8 JSON") from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) != encoded:
        raise LifecycleError(
            f"{label} is not exact canonical compact sorted JSON with one final LF"
        )
    return value, encoded


def validate_installed_portfolio_em_sequencing_receipt(
    *,
    result_root: Path,
    complete: Mapping[str, object],
    cm_acceptance: Mapping[str, object],
) -> InstalledPortfolioEMSequencingReceipt:
    """Authenticate the exact installed, result-blind Portfolio-EM intake receipt."""

    root = Path(result_root).resolve()
    destination = root / RESULT_V2_NAME
    receipt_path = root / PORTFOLIO_EM_SEQUENCING_RECEIPT_NAME
    validated_complete = validate_complete_marker(complete)
    validated_acceptance = validate_cm_acceptance(cm_acceptance)
    if validated_acceptance["complete_sha256"] != validated_complete["complete_sha256"]:
        raise LifecycleError("CM acceptance does not bind this COMPLETE marker")
    value, encoded = _read_installed_canonical_regular_file(
        receipt_path, label="Portfolio-EM sequencing receipt"
    )
    keys = {
        "schema",
        "serializer",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "result_root",
        "result_destination_path",
        "complete_sha256",
        "cm_acceptance_sha256",
        "receipt_id",
        "portfolio_em_actor",
        "result_blind_accepted_complete_intake",
        "legacy_result_used",
        "root_release_authority_granted",
    }
    if set(value) != keys:
        raise LifecycleError("Portfolio-EM sequencing receipt schema differs")
    fixed = {
        "schema": PORTFOLIO_EM_SEQUENCING_RECEIPT_SCHEMA,
        "serializer": "UTF8-CANONICAL-JSON-SORTED-COMPACT-LF-v1",
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "result_root": str(root),
        "result_destination_path": str(destination),
        "complete_sha256": validated_complete["complete_sha256"],
        "cm_acceptance_sha256": validated_acceptance["cm_acceptance_sha256"],
        "portfolio_em_actor": PORTFOLIO_EM_ACTOR,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise LifecycleError("Portfolio-EM sequencing receipt identity or binding differs")
    if value.get("result_blind_accepted_complete_intake") is not True:
        raise LifecycleError("Portfolio-EM receipt does not record accepted-COMPLETE intake")
    if value.get("legacy_result_used") is not False:
        raise LifecycleError("Portfolio-EM receipt must not use the legacy result")
    if value.get("root_release_authority_granted") is not False:
        raise LifecycleError("Portfolio-EM receipt cannot grant Root release authority")
    receipt_id = value.get("receipt_id")
    if not isinstance(receipt_id, str):
        raise LifecycleError("Portfolio-EM receipt_id must be a canonical lowercase UUID")
    try:
        parsed_receipt_id = uuid.UUID(receipt_id)
    except (ValueError, AttributeError) as exc:
        raise LifecycleError("Portfolio-EM receipt_id must be a canonical lowercase UUID") from exc
    if str(parsed_receipt_id) != receipt_id:
        raise LifecycleError("Portfolio-EM receipt_id must be a canonical lowercase UUID")
    return InstalledPortfolioEMSequencingReceipt(
        path=receipt_path,
        document=value,
        installed_bytes_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def validate_result_release_authorization(
    value: Mapping[str, object],
    *,
    result_root: Path,
    complete: Mapping[str, object],
    cm_acceptance: Mapping[str, object],
) -> dict[str, object]:
    """Validate one exact, path-bound Operational-Root sequencing token."""

    validated_complete = validate_complete_marker(complete)
    validated_acceptance = validate_cm_acceptance(cm_acceptance)
    resolved_root = Path(result_root).resolve()
    resolved_destination = resolved_root / RESULT_V2_NAME
    resolved_authorization_path = resolved_root / RESULT_V2_RELEASE_AUTHORIZATION_NAME
    installed_receipt = validate_installed_portfolio_em_sequencing_receipt(
        result_root=resolved_root,
        complete=validated_complete,
        cm_acceptance=validated_acceptance,
    )
    if validated_acceptance["complete_sha256"] != validated_complete["complete_sha256"]:
        raise LifecycleError("CM acceptance does not bind this COMPLETE marker")
    keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "result_root",
        "result_destination_path",
        "complete_sha256",
        "cm_acceptance_sha256",
        "authorization_id",
        "operator",
        "release_authorization_path",
        "portfolio_em_sequencing_receipt_path",
        "portfolio_em_sequencing_receipt_sha256",
        "result_release_authorized",
    }
    if set(value) != keys:
        raise LifecycleError("result release authorization schema differs")
    fixed = {
        "schema": RESULT_RELEASE_AUTHORIZATION_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "result_root": str(resolved_root),
        "result_destination_path": str(resolved_destination),
        "complete_sha256": validated_complete["complete_sha256"],
        "cm_acceptance_sha256": validated_acceptance["cm_acceptance_sha256"],
        "operator": RELEASE_OPERATOR,
        "release_authorization_path": str(resolved_authorization_path),
        "portfolio_em_sequencing_receipt_path": str(installed_receipt.path),
        "portfolio_em_sequencing_receipt_sha256": (
            installed_receipt.installed_bytes_sha256
        ),
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise LifecycleError("result release authorization owner, path, identity, or binding differs")
    if value.get("result_release_authorized") is not True:
        raise LifecycleError("Operational Root did not authorize result release")
    authorization_id = value.get("authorization_id")
    if not isinstance(authorization_id, str):
        raise LifecycleError("release authorization_id must be a canonical lowercase UUID")
    try:
        parsed_authorization_id = uuid.UUID(authorization_id)
    except (ValueError, AttributeError) as exc:
        raise LifecycleError("release authorization_id must be a canonical lowercase UUID") from exc
    if str(parsed_authorization_id) != authorization_id:
        raise LifecycleError("release authorization_id must be a canonical lowercase UUID")
    canonical_json_bytes(dict(value))
    return dict(value)


def result_release_authorization_sha256(value: Mapping[str, object]) -> str:
    return document_sha256(dict(value))


def derive_result_release_id(value: Mapping[str, object]) -> str:
    """Derive a stable release ID solely from immutable token bindings."""

    body = {
        "schema": RESULT_RELEASE_ID_SCHEMA,
        "release_authorization_sha256": result_release_authorization_sha256(value),
        "complete_sha256": value["complete_sha256"],
        "cm_acceptance_sha256": value["cm_acceptance_sha256"],
        "authorization_id": value["authorization_id"],
        "result_destination_path": value["result_destination_path"],
        "portfolio_em_sequencing_receipt_path": value[
            "portfolio_em_sequencing_receipt_path"
        ],
        "portfolio_em_sequencing_receipt_sha256": value[
            "portfolio_em_sequencing_receipt_sha256"
        ],
    }
    return document_sha256(body)


def build_result_release_receipt(
    authorization: Mapping[str, object],
    *,
    result_root: Path,
    complete: Mapping[str, object],
    cm_acceptance: Mapping[str, object],
) -> dict[str, object]:
    """Embed the immutable, result-blind release receipt in RESULT_V2 itself."""

    checked = validate_result_release_authorization(
        authorization,
        result_root=result_root,
        complete=complete,
        cm_acceptance=cm_acceptance,
    )
    installed_receipt = validate_installed_portfolio_em_sequencing_receipt(
        result_root=result_root,
        complete=complete,
        cm_acceptance=cm_acceptance,
    )
    return {
        "schema": RESULT_RELEASE_RECEIPT_SCHEMA,
        "release_id": derive_result_release_id(checked),
        "release_authorization_sha256": result_release_authorization_sha256(checked),
        "result_destination_path": checked["result_destination_path"],
        "complete_sha256": checked["complete_sha256"],
        "cm_acceptance_sha256": checked["cm_acceptance_sha256"],
        "authorization_id": checked["authorization_id"],
        "portfolio_em_sequencing_receipt_id": installed_receipt.document["receipt_id"],
        "portfolio_em_sequencing_receipt_path": checked[
            "portfolio_em_sequencing_receipt_path"
        ],
        "portfolio_em_sequencing_receipt_sha256": checked[
            "portfolio_em_sequencing_receipt_sha256"
        ],
        "release_outcome": "PUBLISHED_ONCE",
        "result_blind": True,
    }


def validate_result_release_receipt(
    value: Mapping[str, object],
    *,
    authorization: Mapping[str, object],
    result_root: Path,
    complete: Mapping[str, object],
    cm_acceptance: Mapping[str, object],
) -> dict[str, object]:
    """Validate the embedded receipt without inspecting the analysis payload."""

    checked = validate_result_release_authorization(
        authorization,
        result_root=result_root,
        complete=complete,
        cm_acceptance=cm_acceptance,
    )
    expected = build_result_release_receipt(
        checked,
        result_root=result_root,
        complete=complete,
        cm_acceptance=cm_acceptance,
    )
    if dict(value) != expected:
        raise LifecycleError("result release receipt schema or authorization binding differs")
    return expected


def _reject_partial_fields(value: object, *, path: str = "result") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise LifecycleError(f"{path} has a non-string field")
            if key.lower().replace("-", "_") in _PARTIAL_FIELD_NAMES:
                raise LifecycleError(f"{path}.{key} is forbidden by the result firewall")
            _reject_partial_fields(item, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_partial_fields(item, path=f"{path}[{index}]")


def validate_result_firewall(
    *,
    result_root: Path,
    complete: Mapping[str, object],
    cm_acceptance: Mapping[str, object],
    result_envelope: Mapping[str, object],
    release_authorization: Mapping[str, object],
) -> dict[str, object]:
    """Admit one atomic RESULT_V2 receipt under exact Root sequencing authority."""

    validated_complete = validate_complete_marker(complete)
    validated_acceptance = validate_cm_acceptance(cm_acceptance)
    if validated_acceptance["complete_sha256"] != validated_complete["complete_sha256"]:
        raise LifecycleError("CM acceptance does not bind this COMPLETE marker")
    keys = {
        "schema",
        "science_revision",
        "stage",
        "host",
        "namespace",
        "complete_sha256",
        "cm_acceptance_sha256",
        "complete_panel",
        "analysis",
        "release_receipt",
    }
    if set(result_envelope) != keys:
        raise LifecycleError("result envelope schema differs")
    fixed = {
        "schema": RESULT_SCHEMA,
        "science_revision": SCIENCE_REVISION,
        "stage": STAGE,
        "host": HOST_ID,
        "namespace": PRODUCTION_NAMESPACE,
        "complete_sha256": validated_complete["complete_sha256"],
        "cm_acceptance_sha256": validated_acceptance["cm_acceptance_sha256"],
        "complete_panel": True,
    }
    if any(result_envelope.get(key) != expected for key, expected in fixed.items()):
        raise LifecycleError("result is not bound to the accepted complete panel")
    if not isinstance(result_envelope["analysis"], Mapping) or not result_envelope["analysis"]:
        raise LifecycleError("complete result analysis payload is absent")
    receipt = result_envelope["release_receipt"]
    if not isinstance(receipt, Mapping):
        raise LifecycleError("result release receipt is absent")
    validate_result_release_receipt(
        receipt,
        result_root=result_root,
        complete=validated_complete,
        cm_acceptance=validated_acceptance,
        authorization=release_authorization,
    )
    _reject_partial_fields(result_envelope)
    canonical_json_bytes(dict(result_envelope))
    return dict(result_envelope)


def publish_result_once(
    root: Path,
    result_envelope: Mapping[str, object],
) -> Path:
    """Publish RESULT_V2 as the one atomic durable release receipt."""

    root = Path(root).resolve()
    destination = root / RESULT_V2_NAME
    authorization_path = root / RESULT_V2_RELEASE_AUTHORIZATION_NAME
    complete = read_canonical_json(root / COMPLETE_NAME)
    acceptance = read_canonical_json(root / CM_ACCEPTANCE_NAME)
    current_authorization = read_canonical_json(authorization_path)
    validate_result_release_authorization(
        current_authorization,
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
    )
    checked = validate_result_firewall(
        result_root=root,
        complete=complete,
        cm_acceptance=acceptance,
        result_envelope=result_envelope,
        release_authorization=current_authorization,
    )
    if destination.exists():
        raise FileExistsError("TBVUUS RESULT_V2 release is write-once")
    return atomic_write_once(destination, checked, authorized_root=root)
