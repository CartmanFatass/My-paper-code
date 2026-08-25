"""Zero-runtime EC4G-A3 two-snapshot prospective binding audit.

The module reads exactly two immutable blobs: the complete contract from C0
and its non-self-referential binding record from C1.  It validates serialized
declarations only.  It never invokes either action map, compiles or compares
programs, or calculates D_RER3.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Mapping, Protocol, Sequence


C0_COMMIT = "c0beef960f5f731f0c994ecd2298a1e889210c7b"
C0_CONTRACT_BLOB_OID = "6d37b33c933ee16f89186a507e67e1080b674ca0"
C0_CONTRACT_SHA256 = "0d0c9b6f24ae2bb96fc0a3f542c737557f1cd66be1edbdb72d809dfce9bb0183"
CONTRACT_PATH = "docs/research/candidates/ec4g_r1/EC4G_RER3_COMPLETE_CONTRACT_V1.json"
BINDING_PATH = "docs/research/candidates/ec4g_r1/EC4G_RER3_BINDING_RECORD_V1.json"
SOURCE_PATH = "experiments/candidates/ec4g_r1/rer3_complete_prospective_binding_audit.py"
TREATMENT_ID = "EC4G-A3-RER3-COMPLETE-PROSPECTIVE-BINDING-AUDIT"
CANDIDATE_VERSION = "CAND-VAP-EC4G-R1@rer3-prospective-complete-v8"
CONTRACT_ID = "EC4G-RER3-CONTRACT@1.0.0"
SCHEMA_VERSION = 1
REMOTE_BLOB_ROOT = "https://github.com/CartmanFatass/My-paper-code/blob"

ROLE_SPECS = (
    (0, "objective_contract", "ec4g.rer3.v1.objective", "/objective_contract"),
    (1, "cell_registry_K", "ec4g.rer3.v1.K", "/cell_registry_K"),
    (2, "receipt_registry_R_k", "ec4g.rer3.v1.R", "/receipt_registry_R_k"),
    (3, "seven_arm_mean_and_covariance", "ec4g.rer3.v1.moments", "/seven_arm_mean_and_covariance"),
    (4, "cost_object", "ec4g.rer3.v1.cost", "/cost_object"),
    (5, "decision_parameters", "ec4g.rer3.v1.theta", "/decision_parameters"),
    (6, "total_EC4G_action_map_M_E", "ec4g.rer3.v1.M_E", "/total_EC4G_action_map_M_E"),
    (7, "total_Direct_tau_action_map_M_D", "ec4g.rer3.v1.M_D", "/total_Direct_tau_action_map_M_D"),
    (8, "fallback_program_F", "ec4g.rer3.v1.F", "/fallback_program_F"),
    (9, "donor_operator_J", "ec4g.rer3.v1.J", "/donor_operator_J"),
    (10, "canonicalizer_equality_Gamma", "ec4g.rer3.v1.Gamma", "/canonicalizer_equality_Gamma"),
    (11, "support_predicate_s", "ec4g.rer3.v1.s", "/support_predicate_s"),
    (12, "deployed_measure_m", "ec4g.rer3.v1.m", "/deployed_measure_m"),
    (13, "cross_cutting_freeze_manifest", "ec4g.rer3.v1.freeze", "/cross_cutting_freeze_manifest"),
)
ROLE_ORDER = tuple(item[1] for item in ROLE_SPECS)

COMMON_LITERAL_FIELDS = (
    "agent_order",
    "arm_order",
    "gate_action_order",
    "tick_domain",
    "reward_unit",
    "weight_encoding",
    "serialization_id",
    "population_id",
    "horizon_id",
    "domain_id",
    "ordering_id",
    "semantic_snapshot_id",
    "freeze_order_id",
    "canonical_json",
)

_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class AuditBranch(str, Enum):
    FREEZE_PAIR_INVALID = "A3_FREEZE_PAIR_INVALID"
    POST_FREEZE_CHANGE_OR_IMPORT = "A3_POST_FREEZE_CHANGE_OR_IMPORT"
    AMBIGUOUS_ROLE_BINDING = "A3_AMBIGUOUS_ROLE_BINDING"
    PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT = (
        "A3_PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT"
    )
    COMPLETE_PROSPECTIVE_CONTRACT_BINDING = "A3_COMPLETE_PROSPECTIVE_CONTRACT_BINDING"


class SnapshotReadError(RuntimeError):
    """An immutable snapshot cannot provide its declared blob."""


class StrictJsonError(ValueError):
    """Serialized JSON violates the frozen UTF-8/canonical-number contract."""


@dataclass(frozen=True)
class FreezeFailure:
    code: str
    detail: str
    path: str | None = None

    def payload(self) -> dict[str, object]:
        return {"code": self.code, "detail": self.detail, "path": self.path}


@dataclass(frozen=True)
class FrozenBlob:
    commit: str
    path: str
    blob_oid: str
    sha256: str
    content: bytes

    @property
    def public_locator(self) -> str:
        return f"{REMOTE_BLOB_ROOT}/{self.commit}/{self.path}"

    def payload(self) -> dict[str, str]:
        return {
            "blob_oid": self.blob_oid,
            "commit": self.commit,
            "path": self.path,
            "public_locator": self.public_locator,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class FrozenPair:
    c0_commit: str
    c1_commit: str
    entries: tuple[FrozenBlob, ...]
    failures: tuple[FreezeFailure, ...]
    frozen_pair_digest: str | None
    contract: Mapping[str, object] | None
    binding_record: Mapping[str, object] | None

    @property
    def valid(self) -> bool:
        return not self.failures and len(self.entries) == 2 and self.frozen_pair_digest is not None


@dataclass(frozen=True)
class PostFreezeEvent:
    kind: str
    detail: str
    path: str | None = None

    def payload(self) -> dict[str, object]:
        return {"detail": self.detail, "kind": self.kind, "path": self.path}


class SnapshotReader(Protocol):
    requested_commit: str
    resolved_commit: str

    def read_blob(self, path: str) -> tuple[str, bytes]: ...


class GitSnapshotReader:
    """Read one immutable Git snapshot without checking it out."""

    def __init__(self, repository_root: Path, commit: str):
        self.repository_root = repository_root.resolve()
        self.requested_commit = commit
        self.resolved_commit = self._text("rev-parse", "--verify", f"{commit}^{{commit}}").strip()

    def _run(self, *arguments: str, text: bool = False) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                ["git", "-C", str(self.repository_root), *arguments],
                check=True,
                capture_output=True,
                text=text,
                encoding="utf-8" if text else None,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SnapshotReadError(f"git snapshot read failed: {arguments!r}: {exc}") from exc

    def _text(self, *arguments: str) -> str:
        return self._run(*arguments, text=True).stdout

    def read_blob(self, path: str) -> tuple[str, bytes]:
        spec = f"{self.resolved_commit}:{path}"
        oid = self._text("rev-parse", "--verify", spec).strip()
        if self._text("cat-file", "-t", oid).strip() != "blob":
            raise SnapshotReadError(f"snapshot object is not a blob: {path}")
        return oid, self._run("cat-file", "blob", oid).stdout


class MappingSnapshotReader:
    """Proof-sized immutable reader used by focused structural tests."""

    def __init__(self, commit: str, blobs: Mapping[str, bytes | str]):
        self.requested_commit = commit
        self.resolved_commit = commit
        self._blobs = {
            path: value.encode("utf-8") if isinstance(value, str) else bytes(value)
            for path, value in blobs.items()
        }

    def read_blob(self, path: str) -> tuple[str, bytes]:
        try:
            content = self._blobs[path]
        except KeyError as exc:
            raise SnapshotReadError(f"missing snapshot blob: {path}") from exc
        return git_blob_oid(content), content


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def git_blob_oid(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _reject_constant(value: str) -> object:
    raise StrictJsonError(f"nonfinite JSON number forbidden: {value}")


def _reject_float(value: str) -> object:
    raise StrictJsonError(f"JSON noninteger must be an exact decimal string: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJsonError(f"duplicate JSON key forbidden: {key}")
        result[key] = value
    return result


def parse_strict_json(content: bytes, *, require_canonical: bool = False) -> object:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise StrictJsonError(f"not strict UTF-8: {exc}") from exc
    if text.startswith("\ufeff"):
        raise StrictJsonError("UTF-8 BOM is forbidden")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (json.JSONDecodeError, StrictJsonError) as exc:
        raise StrictJsonError(str(exc)) from exc
    if require_canonical and content != canonical_json_bytes(value) + b"\n":
        raise StrictJsonError("binding record is not canonical JSON plus one LF")
    return value


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _resolve_pointer(document: object, pointer: str) -> object:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must be RFC6901 absolute")
    current = document
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ValueError(f"JSON pointer does not resolve: {pointer}")
    return current


def derive_binding_record(contract: Mapping[str, object]) -> dict[str, object]:
    """Derive the only permitted C1 record from the exact C0 semantic object."""

    common = _require_mapping(contract.get("common_literals"), "common_literals")
    if tuple(common) != COMMON_LITERAL_FIELDS:
        raise ValueError("common_literals key order/content differs from the frozen contract")
    declared = contract.get("ordered_role_bindings")
    expected_declared = [
        {"ordinal": ordinal, "role": role, "object_id": object_id}
        for ordinal, role, object_id, _pointer in ROLE_SPECS
    ]
    if declared != expected_declared:
        raise ValueError("ordered_role_bindings differs from the frozen fourteen-role order")
    if contract.get("contract_id") != CONTRACT_ID or contract.get("version_id") != CANDIDATE_VERSION:
        raise ValueError("contract identity differs from the frozen A3 identity")

    rows: list[dict[str, object]] = []
    for ordinal, role, object_id, pointer in ROLE_SPECS:
        subtree = _resolve_pointer(contract, pointer)
        rows.append(
            {
                "coherence": dict(common),
                "json_pointer": pointer,
                "object_id": object_id,
                "ordinal": ordinal,
                "role": role,
                "source_blob_oid": C0_CONTRACT_BLOB_OID,
                "source_blob_sha256": C0_CONTRACT_SHA256,
                "source_commit": C0_COMMIT,
                "source_path": CONTRACT_PATH,
                "subtree_sha256": hashlib.sha256(canonical_json_bytes(subtree)).hexdigest(),
                "total": True,
            }
        )
    return {
        "bindings": rows,
        "coherence": dict(common),
        "contract_id": CONTRACT_ID,
        "contract_source": {
            "blob_oid": C0_CONTRACT_BLOB_OID,
            "commit": C0_COMMIT,
            "path": CONTRACT_PATH,
            "sha256": C0_CONTRACT_SHA256,
        },
        "direction_id": contract.get("direction_id"),
        "document_kind": "ec4g_rer3_binding_record",
        "freeze_protocol": "two_snapshot_non_self_referential_v1",
        "role_order": list(ROLE_ORDER),
        "schema_version": SCHEMA_VERSION,
        "version_id": CANDIDATE_VERSION,
    }


def derive_binding_record_bytes(contract: Mapping[str, object]) -> bytes:
    return canonical_json_bytes(derive_binding_record(contract)) + b"\n"


def freeze_repository_pair(repository_root: Path, c1_commit: str) -> FrozenPair:
    try:
        c0_reader = GitSnapshotReader(repository_root, C0_COMMIT)
        c1_reader = GitSnapshotReader(repository_root, c1_commit)
    except SnapshotReadError as exc:
        return _invalid_pair(c1_commit, "SNAPSHOT_COMMIT_UNREADABLE", str(exc))
    return freeze_snapshot_pair(c0_reader, c1_reader, expected_c1_commit=c1_commit)


def freeze_snapshot_pair(
    c0_reader: SnapshotReader,
    c1_reader: SnapshotReader,
    *,
    expected_c1_commit: str,
) -> FrozenPair:
    """Freeze exactly the C0 contract blob and C1 binding blob before inspection."""

    failures: list[FreezeFailure] = []
    entries: list[FrozenBlob] = []
    if not _REVISION_RE.fullmatch(expected_c1_commit):
        failures.append(FreezeFailure("INVALID_C1_COMMIT", "C1 must be lowercase 40-hex"))
    if expected_c1_commit == C0_COMMIT:
        failures.append(FreezeFailure("C1_NOT_DISTINCT_FROM_C0", "two snapshots must be distinct"))
    identities = (
        (c0_reader, C0_COMMIT, CONTRACT_PATH, "C0"),
        (c1_reader, expected_c1_commit, BINDING_PATH, "C1"),
    )
    for reader, expected_commit, path, label in identities:
        if reader.requested_commit != expected_commit or reader.resolved_commit != expected_commit:
            failures.append(
                FreezeFailure(
                    f"{label}_COMMIT_IDENTITY_MISMATCH",
                    f"expected {expected_commit}; requested={reader.requested_commit}; resolved={reader.resolved_commit}",
                    path,
                )
            )
        try:
            oid, content = reader.read_blob(path)
        except SnapshotReadError as exc:
            failures.append(FreezeFailure(f"{label}_BLOB_UNREADABLE", str(exc), path))
            continue
        computed_oid = git_blob_oid(content)
        if not _OID_RE.fullmatch(oid) or oid != computed_oid:
            failures.append(
                FreezeFailure(f"{label}_BLOB_OID_MISMATCH", f"declared={oid}; computed={computed_oid}", path)
            )
        entries.append(
            FrozenBlob(expected_commit, path, oid, hashlib.sha256(content).hexdigest(), content)
        )

    contract: Mapping[str, object] | None = None
    binding: Mapping[str, object] | None = None
    by_path = {entry.path: entry for entry in entries}
    contract_blob = by_path.get(CONTRACT_PATH)
    binding_blob = by_path.get(BINDING_PATH)
    if contract_blob is not None:
        if contract_blob.blob_oid != C0_CONTRACT_BLOB_OID:
            failures.append(FreezeFailure("C0_CONTRACT_BLOB_MISMATCH", "contract blob OID differs from C0", CONTRACT_PATH))
        if contract_blob.sha256 != C0_CONTRACT_SHA256:
            failures.append(FreezeFailure("C0_CONTRACT_SHA256_MISMATCH", "contract SHA-256 differs from C0", CONTRACT_PATH))
        try:
            contract = _require_mapping(parse_strict_json(contract_blob.content), "C0 contract")
        except (StrictJsonError, ValueError) as exc:
            failures.append(FreezeFailure("C0_CONTRACT_JSON_INVALID", str(exc), CONTRACT_PATH))
    if binding_blob is not None:
        try:
            binding = _require_mapping(
                parse_strict_json(binding_blob.content, require_canonical=True), "C1 binding record"
            )
        except (StrictJsonError, ValueError) as exc:
            failures.append(FreezeFailure("C1_BINDING_JSON_INVALID", str(exc), BINDING_PATH))
        else:
            if _contains_scalar(binding, expected_c1_commit):
                failures.append(
                    FreezeFailure(
                        "C1_SELF_REFERENCE",
                        "binding record contains its own containing C1 commit",
                        BINDING_PATH,
                    )
                )
    digest = None
    if not failures and len(entries) == 2:
        digest = hashlib.sha256(canonical_json_bytes([entry.payload() for entry in entries])).hexdigest()
    return FrozenPair(
        C0_COMMIT,
        expected_c1_commit,
        tuple(entries),
        tuple(failures),
        digest,
        contract,
        binding,
    )


def _contains_scalar(value: object, target: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_scalar(key, target) or _contains_scalar(item, target) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_scalar(item, target) for item in value)
    return value == target


def audit_frozen_pair(
    frozen: FrozenPair,
    *,
    run_id: str,
    post_freeze_events: Sequence[PostFreezeEvent] = (),
    registered_audit: bool = False,
) -> "Rer3BindingAuditResult":
    if not run_id.strip():
        raise ValueError("run_id must be nonempty")
    if not frozen.valid:
        return _result(
            AuditBranch.FREEZE_PAIR_INVALID,
            frozen,
            run_id,
            _not_inspected_rows("freeze pair invalid"),
            first_failure=(
                frozen.failures[0].payload()
                if frozen.failures
                else {"code": "FREEZE_PAIR_INVALID", "detail": "freeze validity predicate failed", "path": None}
            ),
            freeze_witnesses=tuple(item.payload() for item in frozen.failures),
            registered_audit=registered_audit,
            role_inspections=0,
        )
    if post_freeze_events:
        return _result(
            AuditBranch.POST_FREEZE_CHANGE_OR_IMPORT,
            frozen,
            run_id,
            _not_inspected_rows("post-freeze change or import observed"),
            first_failure=post_freeze_events[0].payload(),
            post_freeze_witnesses=tuple(item.payload() for item in post_freeze_events),
            registered_audit=registered_audit,
            role_inspections=0,
        )

    assert frozen.contract is not None and frozen.binding_record is not None
    contract = frozen.contract
    record = frozen.binding_record
    metadata_issues = _binding_metadata_issues(record, contract)
    raw_bindings = record.get("bindings")
    if not isinstance(raw_bindings, list):
        metadata_issues.append(_issue("INVALID_BINDINGS_COLLECTION", "bindings must be an array"))
        raw_bindings = []

    rows: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    ambiguous: list[dict[str, object]] = []
    incoherent: list[dict[str, object]] = list(metadata_issues)
    for ordinal, role, object_id, pointer in ROLE_SPECS:
        matches = [item for item in raw_bindings if isinstance(item, dict) and item.get("role") == role]
        base = {"candidate_count": len(matches), "json_pointer": pointer, "ordinal": ordinal, "role": role}
        if not matches:
            issue = _issue("MISSING_ROLE_BINDING", "no binding row for frozen role", role)
            missing.append(issue)
            rows.append({**base, "issues": [issue], "object_id": None, "status": "MISSING"})
        elif len(matches) > 1:
            issue = _issue("MULTIPLE_ROLE_BINDINGS", "more than one binding row for frozen role", role)
            ambiguous.append(issue)
            rows.append({**base, "issues": [issue], "object_id": None, "status": "AMBIGUOUS"})
        else:
            issues = _binding_row_issues(matches[0], contract, frozen, ordinal, role, object_id, pointer)
            incoherent.extend(issues)
            rows.append(
                {
                    **base,
                    "issues": issues,
                    "object_id": matches[0].get("object_id"),
                    "status": "INCOHERENT" if issues else "BOUND",
                    "subtree_sha256": matches[0].get("subtree_sha256"),
                }
            )

    science_issues, science_checks, normalization_checks, shape_counts = _scientific_issues(contract)
    incoherent.extend(science_issues)
    if ambiguous:
        branch = AuditBranch.AMBIGUOUS_ROLE_BINDING
        first_failure = ambiguous[0]
    elif missing or incoherent:
        branch = AuditBranch.PARTIAL_OR_SCIENTIFICALLY_INCOHERENT_CONTRACT
        first_failure = _first_failure(rows, incoherent)
    else:
        branch = AuditBranch.COMPLETE_PROSPECTIVE_CONTRACT_BINDING
        first_failure = None
    return _result(
        branch,
        frozen,
        run_id,
        rows,
        first_failure=first_failure,
        missing_witnesses=missing,
        ambiguous_witnesses=ambiguous,
        incoherent_witnesses=incoherent,
        science_checks=science_checks,
        normalization_checks=normalization_checks,
        shape_counts=shape_counts,
        registered_audit=registered_audit,
        role_inspections=14,
    )


def _binding_metadata_issues(record: Mapping[str, object], contract: Mapping[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    expected = derive_binding_record(contract)
    for field in (
        "coherence",
        "contract_id",
        "contract_source",
        "direction_id",
        "document_kind",
        "freeze_protocol",
        "role_order",
        "schema_version",
        "version_id",
    ):
        if record.get(field) != expected[field]:
            issues.append(_issue("BINDING_METADATA_MISMATCH", f"{field} differs from deterministic C0 derivation"))
    allowed = set(expected)
    if set(record) != allowed:
        issues.append(_issue("BINDING_RECORD_FIELDS_MISMATCH", "binding record fields are not exact"))
    bindings = record.get("bindings")
    ordered_roles = (
        [item.get("role") for item in bindings]
        if isinstance(bindings, list) and all(isinstance(item, dict) for item in bindings)
        else None
    )
    if not isinstance(bindings, list) or len(bindings) != 14 or ordered_roles != list(ROLE_ORDER):
        issues.append(
            _issue(
                "BINDING_ROW_ORDER_MISMATCH",
                "binding record must contain exactly fourteen rows in frozen role order",
            )
        )
    return issues


def _binding_row_issues(
    row: Mapping[str, object],
    contract: Mapping[str, object],
    frozen: FrozenPair,
    ordinal: int,
    role: str,
    object_id: str,
    pointer: str,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    expected = derive_binding_record(contract)["bindings"][ordinal]
    assert isinstance(expected, dict)
    expected_fields = set(expected)
    if set(row) != expected_fields:
        issues.append(_issue("BINDING_ROW_FIELDS_MISMATCH", "binding row fields are not exact", role))
    checks = {
        "ordinal": ordinal,
        "role": role,
        "object_id": object_id,
        "json_pointer": pointer,
        "source_commit": C0_COMMIT,
        "source_path": CONTRACT_PATH,
        "source_blob_oid": C0_CONTRACT_BLOB_OID,
        "source_blob_sha256": C0_CONTRACT_SHA256,
        "coherence": contract.get("common_literals"),
        "total": True,
    }
    for field, value in checks.items():
        if row.get(field) != value:
            issues.append(_issue("BINDING_FIELD_MISMATCH", f"{field} differs from frozen value", role))
    try:
        subtree = _resolve_pointer(contract, pointer)
    except ValueError as exc:
        issues.append(_issue("RFC6901_POINTER_UNRESOLVED", str(exc), role))
    else:
        expected_sha = hashlib.sha256(canonical_json_bytes(subtree)).hexdigest()
        if row.get("subtree_sha256") != expected_sha:
            issues.append(_issue("SUBTREE_SHA256_MISMATCH", "canonical subtree SHA-256 differs", role))
    if _contains_scalar(row, frozen.c1_commit):
        issues.append(_issue("C1_SELF_REFERENCE", "row contains its C1 commit", role))
    return issues


def _scientific_issues(
    contract: Mapping[str, object],
) -> tuple[list[dict[str, object]], dict[str, object], dict[str, object], dict[str, int]]:
    """Inspect declared literals only; this function never evaluates either map."""

    issues: list[dict[str, object]] = []
    common = contract.get("common_literals")
    coherence_ok = isinstance(common, dict) and tuple(common) == COMMON_LITERAL_FIELDS
    expected_common = {
        "agent_order": ["a0", "a1", "a2"],
        "arm_order": ["R0", "RV", "RB", "RS", "PV", "PB", "PS"],
        "gate_action_order": ["P", "N", "A"],
        "tick_domain": [0, 1],
        "reward_unit": "integer_task_point",
        "weight_encoding": "exact_base10_decimal_string",
        "serialization_id": "ec4g-rer3-cjson-v1",
        "population_id": "ec4g-rer3-configured-start-law-v1",
        "horizon_id": "two-tick-post-roster-event-v1",
        "domain_id": "ec4g-rer3-three-cell-domain-v1",
        "ordering_id": "agents-a0a1a2_arms-R0RV_RBRS_PVPBPS_actions-PNA-v1",
        "semantic_snapshot_id": "ec4g-rer3-semantic-freeze-v1",
        "freeze_order_id": "objective-K-Rk-moments-cost-theta-ME-MD-F-J-Gamma-s-m-manifest-v1",
        "canonical_json": "UTF-8; keys lexicographically sorted; array order preserved; no whitespace; signed base-10 integers without leading zero; exact nonintegers encoded as strings; duplicate keys and nonfinite numbers forbidden",
    }
    coherence_ok = coherence_ok and common == expected_common
    if not coherence_ok:
        issues.append(_issue("COMMON_LITERALS_MISMATCH", "common_literals is not the exact coherence tuple"))

    cells_obj = contract.get("cell_registry_K")
    cells = cells_obj.get("cells") if isinstance(cells_obj, dict) else None
    cell_ids = [item.get("cell") for item in cells] if isinstance(cells, list) and all(isinstance(item, dict) for item in cells) else []
    cells_ok = cell_ids == ["k_join", "k_leave", "k_rejoin"]
    if not cells_ok:
        issues.append(_issue("CELL_DOMAIN_MISMATCH", "cell registry must declare join, leave, rejoin in order", "cell_registry_K"))

    receipt = contract.get("receipt_registry_R_k")
    arm_semantics = receipt.get("arm_semantics") if isinstance(receipt, dict) else None
    arms_ok = isinstance(arm_semantics, dict) and list(arm_semantics) == expected_common["arm_order"]
    if not arms_ok:
        issues.append(_issue("ARM_REGISTRY_MISMATCH", "receipt registry must declare seven ordered arms", "receipt_registry_R_k"))

    moments = contract.get("seven_arm_mean_and_covariance")
    noise = moments.get("noise") if isinstance(moments, dict) else None
    gross = moments.get("gross_mean_by_cell_in_arm_order") if isinstance(moments, dict) else None
    covariance = moments.get("covariance") if isinstance(moments, dict) else None
    vector_lengths_ok = (
        isinstance(gross, dict)
        and list(gross) == cell_ids
        and all(isinstance(gross[cell], list) and len(gross[cell]) == 7 for cell in cell_ids)
    )
    finite_means = vector_lengths_ok and all(
        _finite_number(value) for cell in cell_ids for value in gross[cell]  # type: ignore[index]
    )
    if not finite_means:
        issues.append(_issue("MEAN_DIMENSION_OR_FINITE_FAILURE", "gross means must be finite 3x7 vectors", "seven_arm_mean_and_covariance"))

    probabilities = noise.get("probabilities") if isinstance(noise, dict) else None
    probability_sum: Decimal | None = None
    probabilities_ok = False
    if isinstance(probabilities, list) and len(probabilities) == 3:
        try:
            decimal_probabilities = [_exact_decimal(value) for value in probabilities]
            probability_sum = sum(decimal_probabilities, Decimal(0))
            probabilities_ok = all(value >= 0 for value in decimal_probabilities) and probability_sum == Decimal("1.00")
        except (InvalidOperation, ValueError):
            probabilities_ok = False
    outcome_per_cell = noise.get("outcome_vectors_per_cell") if isinstance(noise, dict) else None
    total_outcomes = noise.get("total_outcome_vectors") if isinstance(noise, dict) else None
    support_ok = (
        isinstance(noise, dict)
        and noise.get("support") == [-1, 0, 1]
        and noise.get("noisy_arms") == ["R0", "RV", "RB", "RS"]
        and noise.get("zero_noise_arms") == ["PV", "PB", "PS"]
        and noise.get("independent_components") is True
        and outcome_per_cell == 81
        and total_outcomes == 243
        and probabilities_ok
    )
    if not support_ok:
        issues.append(_issue("OUTCOME_SUPPORT_MISMATCH", "finite 81-per-cell/243-total support law differs", "seven_arm_mean_and_covariance"))

    diagonal = covariance.get("diagonal") if isinstance(covariance, dict) else None
    psd_ok = False
    if isinstance(diagonal, list) and len(diagonal) == 7 and covariance.get("off_diagonal") == "0":  # type: ignore[union-attr]
        try:
            psd_ok = all(_exact_decimal(value) >= 0 for value in diagonal)
        except (InvalidOperation, ValueError):
            psd_ok = False
    if not psd_ok:
        issues.append(_issue("COVARIANCE_NOT_DECLARED_PSD", "diagonal covariance must be finite nonnegative with zero off-diagonal", "seven_arm_mean_and_covariance"))

    costs = contract.get("cost_object")
    cost_vector = costs.get("external_cost_in_arm_order") if isinstance(costs, dict) else None
    net = costs.get("net_mean_by_cell_in_arm_order") if isinstance(costs, dict) else None
    finite_costs = (
        isinstance(cost_vector, list)
        and len(cost_vector) == 7
        and all(_finite_number(value) for value in cost_vector)
    )
    subtraction_ok = (
        isinstance(costs, dict)
        and costs.get("subtract_exactly_once") is True
        and costs.get("unlisted_cost") is False
        and finite_costs
        and isinstance(net, dict)
        and finite_means
        and all(
            net.get(cell) == [gross[cell][index] - cost_vector[index] for index in range(7)]  # type: ignore[index,operator]
            for cell in cell_ids
        )
    )
    if not subtraction_ok:
        issues.append(_issue("ONE_TIME_COST_SUBTRACTION_MISMATCH", "net means must equal gross minus the one exact cost vector", "cost_object"))

    totality_checks = {
        "state_total": (
            isinstance(cells_obj, dict)
            and cells_obj.get("terminal_absorbing") is True
            and isinstance(cells_obj.get("state_tuple"), list)
            and len(cells_obj["state_tuple"]) == 6
        ),
        "receipt_total": arms_ok and isinstance(receipt, dict) and receipt.get("body_length_bytes") == 4,
        "maps_declared": _map_definition_present(
            contract.get("total_EC4G_action_map_M_E"),
            {"k_join": "P", "k_leave": "A", "k_rejoin": "N"},
        )
        and _map_definition_present(
            contract.get("total_Direct_tau_action_map_M_D"),
            {"k_join": "P", "k_leave": "P", "k_rejoin": "N"},
        ),
        "fallback_total": _fallback_total(contract.get("fallback_program_F"), cell_ids),
        "donor_total": _donor_total(contract.get("donor_operator_J"), cell_ids),
        "compiler_total": _compiler_definition_present(contract.get("canonicalizer_equality_Gamma")),
        "support_total_and_independent": _support_total(contract.get("support_predicate_s"), cell_ids),
    }
    for name, passed in totality_checks.items():
        if not passed:
            issues.append(_issue("TOTAL_DEFINITION_MISMATCH", f"{name} failed", _totality_role(name)))

    measure = contract.get("deployed_measure_m")
    masses = measure.get("values") if isinstance(measure, dict) else None
    mass_sum: Decimal | None = None
    mass_positive = False
    mass_exact = False
    if isinstance(masses, dict) and list(masses) == cell_ids:
        try:
            decimal_masses = [_exact_decimal(masses[cell]) for cell in cell_ids]
            mass_sum = sum(decimal_masses, Decimal(0))
            mass_positive = all(value > 0 for value in decimal_masses)
            mass_exact = mass_sum == Decimal("1.00")
        except (InvalidOperation, ValueError):
            pass
    measure_ok = (
        isinstance(measure, dict)
        and measure.get("all_positive") is True
        and measure.get("exact_normalization") == "1.00"
        and mass_positive
        and mass_exact
    )
    if not measure_ok:
        issues.append(_issue("DEPLOYED_MEASURE_MISMATCH", "all three masses must be positive and normalize exactly to 1.00", "deployed_measure_m"))

    science_checks = {
        "coherence_tuple_exact": coherence_ok,
        "cost_subtracted_exactly_once": subtraction_ok,
        "covariance_positive_semidefinite": psd_ok,
        "finite_outcome_law": support_ok and finite_means,
        "map_definitions_present_but_not_invoked": totality_checks["maps_declared"],
        "support_independent_of_maps_program_equality_and_D_RER3": totality_checks["support_total_and_independent"],
        "total_definitions": totality_checks,
    }
    normalization_checks = {
        "configured_mass_all_positive": mass_positive,
        "configured_mass_declared_normalization": measure.get("exact_normalization") if isinstance(measure, dict) else None,
        "configured_mass_sum": format(mass_sum, "f") if mass_sum is not None else None,
        "noise_probability_sum": format(probability_sum, "f") if probability_sum is not None else None,
    }
    shape_counts = {
        "declared_arms": len(cell_ids) * 7 if cells_ok and arms_ok and vector_lengths_ok else 0,
        "declared_cells": len(cell_ids) if cells_ok else 0,
        "declared_outcome_support_points": total_outcomes if support_ok else 0,
    }
    return issues, science_checks, normalization_checks, shape_counts


def _finite_number(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and math.isfinite(value)


def _exact_decimal(value: object) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", value):
        raise ValueError("not an unsigned exact base-10 decimal string")
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError("nonfinite decimal")
    return result


def _map_definition_present(value: object, prediction: Mapping[str, str]) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("ordered_rule"), list)
        and len(value["ordered_rule"]) == 4
        and value["ordered_rule"][-1] == "else return A"
        and value.get("predeclared_prediction") == prediction
    )


def _fallback_total(value: object, cell_ids: list[object]) -> bool:
    return (
        isinstance(value, dict)
        and value.get("domain") == {"cell": cell_ids, "spent": [0, 1]}
        and all(isinstance(value.get(field), str) and value.get(field) for field in ("spent_0", "spent_1", "routing", "state_effect"))
    )


def _donor_total(value: object, cell_ids: list[object]) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("pool"), dict) or not isinstance(value.get("mapping"), dict):
        return False
    pool = value["pool"]
    mapping = value["mapping"]
    if list(mapping) != cell_ids or set(mapping.values()) != set(pool):
        return False
    try:
        return all(
            isinstance(item, dict)
            and item.get("tick") == -1
            and isinstance(item.get("body_hex"), str)
            and len(bytes.fromhex(item["body_hex"])) == 4
            for item in pool.values()
        )
    except ValueError:
        return False


def _compiler_definition_present(value: object) -> bool:
    return (
        isinstance(value, dict)
        and all(isinstance(value.get(field), str) and value.get(field) for field in ("P_transition", "N_transition", "A_transition", "failure_rule", "equality"))
        and isinstance(value.get("canonical_fields"), list)
        and value.get("excluded_fields") == ["map_identity", "symbolic_gate_label"]
    )


def _support_total(value: object, cell_ids: list[object]) -> bool:
    return (
        isinstance(value, dict)
        and value.get("map_independent") is True
        and value.get("forbidden_inputs") == ["M_E", "M_D", "map_output", "program_equality", "D_RER3"]
        and value.get("values") == {cell: True for cell in cell_ids}
        and value.get("unknown_cell_rule") == "reject rather than assign zero mass"
    )


def _totality_role(name: str) -> str:
    return {
        "state_total": "cell_registry_K",
        "receipt_total": "receipt_registry_R_k",
        "maps_declared": "total_EC4G_action_map_M_E",
        "fallback_total": "fallback_program_F",
        "donor_total": "donor_operator_J",
        "compiler_total": "canonicalizer_equality_Gamma",
        "support_total_and_independent": "support_predicate_s",
    }[name]


@dataclass(frozen=True)
class Rer3BindingAuditResult:
    payload_value: Mapping[str, object]

    @property
    def terminal_branch(self) -> AuditBranch:
        return AuditBranch(str(self.payload_value["terminal_branch"]))

    def payload(self) -> dict[str, object]:
        return dict(self.payload_value)

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(self.payload_value)


def _result(
    branch: AuditBranch,
    frozen: FrozenPair,
    run_id: str,
    rows: Sequence[Mapping[str, object]],
    *,
    first_failure: Mapping[str, object] | None,
    freeze_witnesses: Sequence[Mapping[str, object]] = (),
    post_freeze_witnesses: Sequence[Mapping[str, object]] = (),
    missing_witnesses: Sequence[Mapping[str, object]] = (),
    ambiguous_witnesses: Sequence[Mapping[str, object]] = (),
    incoherent_witnesses: Sequence[Mapping[str, object]] = (),
    science_checks: Mapping[str, object] | None = None,
    normalization_checks: Mapping[str, object] | None = None,
    shape_counts: Mapping[str, int] | None = None,
    registered_audit: bool,
    role_inspections: int,
) -> Rer3BindingAuditResult:
    shape_counts = shape_counts or {"declared_arms": 0, "declared_cells": 0, "declared_outcome_support_points": 0}
    identity_material = [run_id, branch.value, frozen.c0_commit, frozen.c1_commit, frozen.frozen_pair_digest]
    result_id = "ec4g-a3-" + hashlib.sha256(canonical_json_bytes(identity_material)).hexdigest()
    complete = branch is AuditBranch.COMPLETE_PROSPECTIVE_CONTRACT_BINDING
    zero_activity = {
        "d_rer3_calculations": 0,
        "environment_transitions": 0,
        "learner_calls": 0,
        "map_calls": 0,
        "model_fits": 0,
        "optimizer_updates": 0,
        "policy_calls": 0,
        "program_comparisons": 0,
        "program_compilations": 0,
        "rescans": 0,
        "rescues": 0,
        "retries": 0,
        "return_evaluations": 0,
        "stochastic_calls": 0,
        "sweeps": 0,
        "trainer_calls": 0,
    }
    activity = {
        **zero_activity,
        "declared_arms": shape_counts["declared_arms"],
        "declared_cells": shape_counts["declared_cells"],
        "declared_outcome_support_points": shape_counts["declared_outcome_support_points"],
        "inventory_freezes": 1,
        "registered_audit_runs": int(registered_audit),
        "role_inspections": role_inspections,
        "scientific_inventory_blobs": len(frozen.entries),
    }
    entries = [entry.payload() for entry in frozen.entries]
    payload: dict[str, object] = {
        "activity_counts": activity,
        "ambiguous_witnesses": list(ambiguous_witnesses),
        "candidate_version": CANDIDATE_VERSION,
        "complete_prospective_contract_binding": complete,
        "document_kind": "ec4g_a3_rer3_complete_prospective_binding_audit_result",
        "eligible_for_explorer_to_consider_separate_future_census": complete,
        "first_failure": first_failure,
        "freeze_witnesses": list(freeze_witnesses),
        "frozen_pair": {
            "c0_commit": frozen.c0_commit,
            "c1_commit": frozen.c1_commit,
            "digest": frozen.frozen_pair_digest,
            "entries": entries,
            "path_order": [CONTRACT_PATH, BINDING_PATH],
        },
        "incoherent_witnesses": list(incoherent_witnesses),
        "missing_witnesses": list(missing_witnesses),
        "normalization_checks": dict(normalization_checks or {}),
        "post_freeze_witnesses": list(post_freeze_witnesses),
        "public_locators": {
            "binding_record": f"{REMOTE_BLOB_ROOT}/{frozen.c1_commit}/{BINDING_PATH}",
            "contract": f"{REMOTE_BLOB_ROOT}/{C0_COMMIT}/{CONTRACT_PATH}",
            "implementation_source": f"{REMOTE_BLOB_ROOT}/{frozen.c1_commit}/{SOURCE_PATH}",
            "result": None,
        },
        "result_id": result_id,
        "result_revision": None,
        "result_revision_status": "assigned only when the one-shot artifact is published",
        "role_witness_table": list(rows),
        "route_status": (
            "ELIGIBLE_FOR_EXPLORER_TO_CONSIDER_SEPARATE_FUTURE_CENSUS"
            if complete
            else "STOPPED_WITHOUT_REPAIR_RETRY_RESCAN_IMPUTATION_OR_SUBSTITUTE"
        ),
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "scientific_checks": dict(science_checks or {}),
        "source_identities": {
            "c0_contract_commit": C0_COMMIT,
            "c0_contract_blob_oid": C0_CONTRACT_BLOB_OID,
            "c0_contract_sha256": C0_CONTRACT_SHA256,
            "c1_implementation_and_binding_commit": frozen.c1_commit,
        },
        "technical_acceptance": {
            "id": result_id + "-technical-acceptance",
            "owner": "code_project_manager",
            "status": "pending_code_project_manager_acceptance",
        },
        "execution_readiness": {
            "id": result_id + "-execution-readiness",
            "owner": "code_project_manager",
            "status": "pending_registered_execution_readiness",
        },
        "terminal_branch": branch.value,
        "treatment_id": TREATMENT_ID,
    }
    return Rer3BindingAuditResult(payload)


def _issue(code: str, detail: str, role: str | None = None) -> dict[str, object]:
    return {"code": code, "detail": detail, "role": role}


def _first_failure(rows: Sequence[Mapping[str, object]], issues: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    for row in rows:
        row_issues = row.get("issues")
        if isinstance(row_issues, list) and row_issues:
            return row_issues[0]
    return issues[0]


def _not_inspected_rows(detail: str) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "candidate_count": None,
            "issues": [],
            "json_pointer": pointer,
            "object_id": None,
            "ordinal": ordinal,
            "role": role,
            "status": "NOT_INSPECTED",
            "status_detail": detail,
        }
        for ordinal, role, _object_id, pointer in ROLE_SPECS
    )


def _invalid_pair(c1_commit: str, code: str, detail: str) -> FrozenPair:
    return FrozenPair(
        C0_COMMIT,
        c1_commit,
        (),
        (FreezeFailure(code, detail),),
        None,
        None,
        None,
    )
