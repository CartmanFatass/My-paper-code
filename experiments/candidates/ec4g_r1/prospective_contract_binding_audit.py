"""Read-only EC4G-A2 audit of pre-existing prospective contract bindings.

The publication inventory is frozen before role inspection.  The analyzer only
validates explicit, already-serialized binding declarations in that inventory;
it never constructs, repairs, infers, or imports a scientific object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Mapping, Protocol, Sequence


PUBLICATION_COMMIT = "497d1429beaf648b0cb6672523d0e87370ad736e"
SOURCE_COMMIT = "d4248863c55bdac294cb2b494e794ffa680f5222"
CANDIDATE_VERSION = "CAND-VAP-EC4G-R1@adversarial-revision-v7"
TREATMENT_ID = "EC4G-A2-PROSPECTIVE-CONTRACT-BINDING-AUDIT"
DECLARATION_KIND = "ec4g_prospective_contract_binding_v1"
SCHEMA_VERSION = 1
REMOTE_BLOB_ROOT = "https://github.com/CartmanFatass/My-paper-code/blob"

RESULT_PATH = (
    "docs/research/candidates/ec4g_r1/"
    "EC4G_A1_EXECUTION_DIGEST_CENSUS_RESULT.json"
)
SOURCE_PATH = "experiments/candidates/ec4g_r1/execution_digest_census.py"
RUNNER_PATH = "scripts/run_ec4g_a1_execution_digest_census.py"
TEST_PATH = "tests/experiments/candidates/ec4g_r1/test_execution_digest_census.py"
INDEX_PATH = "docs/research/candidates/ec4g_r1/CODE_SCIENCE_INDEX.md"

# The handoff freezes this seed order: result, source, runner, test, index.
SEED_INVENTORY_PATHS = (RESULT_PATH, SOURCE_PATH, RUNNER_PATH, TEST_PATH, INDEX_PATH)

ROLE_SPECS = (
    ("objective_contract", "objective contract"),
    ("K", "K"),
    ("R_k", "R_k"),
    ("seven_arm_mean_covariance", "coherent seven-arm mean/covariance"),
    ("cost_object", "cost object"),
    ("decision_parameters", "decision parameters"),
    ("M_E", "M_E"),
    ("M_D", "M_D"),
    ("fallback_F", "fallback F"),
    ("donor_J", "donor J"),
    ("canonicalizer_equality_Gamma", "canonicalizer/equality Gamma"),
    ("support_s", "support s"),
    ("deployed_measure_m", "deployed measure m"),
    ("freeze_manifest", "freeze manifest"),
)
ROLE_IDS = tuple(role_id for role_id, _ in ROLE_SPECS)

COHERENCE_FIELDS = (
    "population_id",
    "horizon_id",
    "unit_id",
    "snapshot_commit",
    "domain_id",
    "ordering_id",
    "serialization_id",
    "freeze_order_id",
)

_A1_NEGATIVE_ROLE_MAP = {
    "objective_contract": "objective_contract",
    "K": "decision_cell_registry",
    "R_k": "receipt_registry",
    "seven_arm_mean_covariance": "seven_arm_joint_moments",
    "cost_object": "cost_contract",
    "decision_parameters": "decision_parameter_registry",
    "M_E": "ec4g_action_map",
    "M_D": "direct_tau_action_map",
    "fallback_F": "fallback_program_registry",
    "donor_J": "payload_preserving_donor_operator",
    "canonicalizer_equality_Gamma": "canonical_execution_compiler",
    "support_s": "prospective_support_registry",
    "deployed_measure_m": "prospective_deployed_mass_registry",
    "freeze_manifest": "freeze_manifest",
}

_PROJECT_PREFIXES = (
    "configs/",
    "docs/",
    "experiments/",
    "ha_ctse_process/",
    "results/",
    "scripts/",
    "src/",
    "tests/",
)
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CODE_SPAN_RE = re.compile(r"`([^`\r\n]+)`")


class AuditBranch(str, Enum):
    INVENTORY_FREEZE_INVALID = "A2_INVENTORY_FREEZE_INVALID"
    POST_FREEZE_OBJECT_OR_REPAIR = "A2_POST_FREEZE_OBJECT_OR_REPAIR"
    AMBIGUOUS_BINDING = "A2_AMBIGUOUS_BINDING"
    PARTIAL_OR_INCOHERENT_BINDING = "A2_PARTIAL_OR_INCOHERENT_BINDING"
    COMPLETE_PREEXISTING_BINDING = "A2_COMPLETE_PREEXISTING_BINDING"


@dataclass(frozen=True)
class FreezeFailure:
    code: str
    path: str | None
    detail: str

    def payload(self) -> dict[str, object]:
        return {"code": self.code, "detail": self.detail, "path": self.path}


@dataclass(frozen=True)
class FrozenBlob:
    path: str
    blob_oid: str
    sha256: str
    content: bytes

    @property
    def public_locator(self) -> str:
        return f"{REMOTE_BLOB_ROOT}/{PUBLICATION_COMMIT}/{self.path}"

    def manifest_payload(self) -> dict[str, str]:
        return {
            "blob_oid": self.blob_oid,
            "path": self.path,
            "public_locator": self.public_locator,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class FrozenInventory:
    requested_commit: str
    resolved_commit: str | None
    entries: tuple[FrozenBlob, ...]
    failures: tuple[FreezeFailure, ...]
    inventory_digest: str | None

    @property
    def valid(self) -> bool:
        return (
            not self.failures
            and self.resolved_commit == PUBLICATION_COMMIT
            and self.inventory_digest is not None
        )

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(entry.path for entry in self.entries)


@dataclass(frozen=True)
class PostFreezeEvent:
    """Externally observed forbidden activity after the inventory was frozen."""

    kind: str
    detail: str
    path: str | None = None

    def payload(self) -> dict[str, object]:
        return {"detail": self.detail, "kind": self.kind, "path": self.path}


@dataclass(frozen=True)
class BindingCandidate:
    declaration_path: str
    ordinal: int
    raw: Mapping[str, object]
    declared_freeze_manifest: Mapping[str, object] | None


class SnapshotReader(Protocol):
    requested_commit: str
    resolved_commit: str

    def read_blob(self, path: str) -> tuple[str, bytes]: ...


class SnapshotReadError(RuntimeError):
    pass


class GitSnapshotReader:
    """Read blobs from one immutable Git commit without checking files out."""

    def __init__(self, repository_root: Path, commit: str = PUBLICATION_COMMIT):
        self.repository_root = repository_root.resolve()
        self.requested_commit = commit
        self.resolved_commit = self._text(
            "rev-parse", "--verify", f"{commit}^{{commit}}"
        ).strip()

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
    """Proof-sized in-memory reader for structural validator tests."""

    def __init__(
        self,
        blobs: Mapping[str, bytes | str],
        *,
        commit: str = PUBLICATION_COMMIT,
    ):
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
        header = f"blob {len(content)}\0".encode("ascii")
        return hashlib.sha1(header + content).hexdigest(), content


def freeze_publication_inventory(repository_root: Path) -> FrozenInventory:
    try:
        reader = GitSnapshotReader(repository_root, PUBLICATION_COMMIT)
    except SnapshotReadError as exc:
        return _invalid_inventory("PUBLICATION_COMMIT_UNREADABLE", str(exc))
    return freeze_inventory(reader)


def freeze_inventory(reader: SnapshotReader) -> FrozenInventory:
    """Resolve the index references once, deduplicate them, and freeze blobs."""

    failures: list[FreezeFailure] = []
    if reader.requested_commit != PUBLICATION_COMMIT:
        failures.append(
            FreezeFailure(
                "WRONG_REQUESTED_COMMIT",
                None,
                f"expected {PUBLICATION_COMMIT}, got {reader.requested_commit}",
            )
        )
    if reader.resolved_commit != PUBLICATION_COMMIT:
        failures.append(
            FreezeFailure(
                "PUBLICATION_COMMIT_IDENTITY_MISMATCH",
                None,
                f"expected {PUBLICATION_COMMIT}, got {reader.resolved_commit}",
            )
        )

    cache: dict[str, tuple[str, bytes]] = {}

    def read(path: str) -> tuple[str, bytes] | None:
        if path in cache:
            return cache[path]
        try:
            cache[path] = reader.read_blob(path)
        except SnapshotReadError as exc:
            failures.append(FreezeFailure("MISSING_OR_UNREADABLE_BLOB", path, str(exc)))
            return None
        return cache[path]

    index_blob = read(INDEX_PATH)
    references: tuple[str, ...] = ()
    if index_blob is not None:
        try:
            index_text = index_blob[1].decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            failures.append(FreezeFailure("INDEX_NOT_UTF8", INDEX_PATH, str(exc)))
        else:
            references = _direct_project_paths(index_text)

    ordered_paths = _deduplicate((*SEED_INVENTORY_PATHS, *references))
    entries: list[FrozenBlob] = []
    for path in ordered_paths:
        value = read(path)
        if value is None:
            continue
        oid, content = value
        try:
            content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            failures.append(FreezeFailure("INVENTORY_BLOB_NOT_UTF8", path, str(exc)))
        entries.append(
            FrozenBlob(path, oid, hashlib.sha256(content).hexdigest(), content)
        )

    if tuple(entry.path for entry in entries) != ordered_paths:
        failures.append(
            FreezeFailure(
                "INVENTORY_PATH_SET_INCOMPLETE",
                None,
                "not every seed or same-commit index reference resolved to a blob",
            )
        )
    digest = None if failures else _inventory_digest(entries)
    return FrozenInventory(
        requested_commit=reader.requested_commit,
        resolved_commit=reader.resolved_commit,
        entries=tuple(entries),
        failures=tuple(failures),
        inventory_digest=digest,
    )


def _json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def audit_frozen_inventory(
    inventory: FrozenInventory,
    *,
    source_revision: str,
    run_id: str,
    post_freeze_events: Sequence[PostFreezeEvent] = (),
    registered_audit: bool = False,
) -> "ProspectiveContractAuditResult":
    """Inspect exactly fourteen roles with the frozen fail-closed precedence."""

    _require_revision(source_revision, "source_revision")
    if not run_id.strip():
        raise ValueError("run_id must be nonempty")

    if not inventory.valid:
        rows = _not_inspected_rows("inventory freeze invalid")
        return _result(
            AuditBranch.INVENTORY_FREEZE_INVALID,
            inventory,
            source_revision,
            run_id,
            rows,
            first_failure=(
                inventory.failures[0].payload()
                if inventory.failures
                else {
                    "code": "INVENTORY_FREEZE_INVALID",
                    "detail": "inventory validity predicate failed",
                    "path": None,
                }
            ),
            freeze_failures=tuple(item.payload() for item in inventory.failures),
            registered_audit=registered_audit,
            role_inspections=0,
        )

    if post_freeze_events:
        rows = _not_inspected_rows("forbidden post-freeze activity observed")
        return _result(
            AuditBranch.POST_FREEZE_OBJECT_OR_REPAIR,
            inventory,
            source_revision,
            run_id,
            rows,
            first_failure=post_freeze_events[0].payload(),
            post_freeze_witnesses=tuple(item.payload() for item in post_freeze_events),
            registered_audit=registered_audit,
            role_inspections=0,
        )

    candidates, declaration_issues = _binding_candidates(inventory)
    negative_evidence = _a1_negative_evidence(inventory)
    role_rows: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    ambiguous: list[dict[str, object]] = []
    incoherent: list[dict[str, object]] = list(declaration_issues)
    singleton_candidates: dict[str, BindingCandidate] = {}

    for ordinal, (role_id, label) in enumerate(ROLE_SPECS):
        matches = tuple(item for item in candidates if item.raw.get("role") == role_id)
        base = {
            "candidate_count": len(matches),
            "freeze_ordinal": ordinal,
            "role": role_id,
            "role_label": label,
        }
        if not matches:
            witness = {
                "code": "MISSING_PREEXISTING_BINDING",
                "detail": "no explicit pre-existing prospective binding declaration",
                "negative_evidence": negative_evidence.get(role_id, ()),
                "role": role_id,
            }
            missing.append(witness)
            role_rows.append({**base, "issues": [witness], "object_id": None, "status": "MISSING"})
        elif len(matches) > 1:
            witness = {
                "candidate_locators": [
                    f"{item.declaration_path}#/objects/{item.ordinal}" for item in matches
                ],
                "code": "MULTIPLE_PREEXISTING_BINDINGS",
                "detail": "role has more than one explicit binding candidate",
                "role": role_id,
            }
            ambiguous.append(witness)
            role_rows.append({**base, "issues": [witness], "object_id": None, "status": "AMBIGUOUS"})
        else:
            singleton_candidates[role_id] = matches[0]
            issues = _candidate_issues(matches[0], role_id, ordinal, inventory)
            incoherent.extend(issues)
            role_rows.append(
                {
                    **base,
                    "declaration_locator": (
                        f"{matches[0].declaration_path}#/objects/{matches[0].ordinal}"
                    ),
                    "issues": issues,
                    "object_id": matches[0].raw.get("object_id"),
                    "status": "INCOHERENT" if issues else "BOUND",
                }
            )

    cross_issues = _cross_object_issues(singleton_candidates, inventory)
    incoherent.extend(cross_issues)
    if cross_issues:
        by_role = {row["role"]: row for row in role_rows}
        for issue in cross_issues:
            role = issue.get("role")
            if role in by_role:
                by_role[role]["issues"].append(issue)
                by_role[role]["status"] = "INCOHERENT"

    if ambiguous:
        branch = AuditBranch.AMBIGUOUS_BINDING
        first_failure = ambiguous[0]
    elif missing or incoherent:
        branch = AuditBranch.PARTIAL_OR_INCOHERENT_BINDING
        first_failure = _first_role_failure(role_rows, incoherent)
    else:
        branch = AuditBranch.COMPLETE_PREEXISTING_BINDING
        first_failure = None

    return _result(
        branch,
        inventory,
        source_revision,
        run_id,
        tuple(role_rows),
        first_failure=first_failure,
        missing_witnesses=tuple(missing),
        ambiguous_witnesses=tuple(ambiguous),
        incoherent_witnesses=tuple(incoherent),
        registered_audit=registered_audit,
        role_inspections=len(ROLE_SPECS),
    )


@dataclass(frozen=True)
class ProspectiveContractAuditResult:
    payload_value: Mapping[str, object]

    @property
    def terminal_branch(self) -> AuditBranch:
        return AuditBranch(str(self.payload_value["terminal_branch"]))

    def payload(self) -> dict[str, object]:
        return dict(self.payload_value)

    def to_bytes(self) -> bytes:
        return json.dumps(
            self.payload_value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")


def _result(
    branch: AuditBranch,
    inventory: FrozenInventory,
    source_revision: str,
    run_id: str,
    role_rows: Sequence[Mapping[str, object]],
    *,
    first_failure: Mapping[str, object] | None,
    freeze_failures: Sequence[Mapping[str, object]] = (),
    post_freeze_witnesses: Sequence[Mapping[str, object]] = (),
    missing_witnesses: Sequence[Mapping[str, object]] = (),
    ambiguous_witnesses: Sequence[Mapping[str, object]] = (),
    incoherent_witnesses: Sequence[Mapping[str, object]] = (),
    registered_audit: bool,
    role_inspections: int,
) -> ProspectiveContractAuditResult:
    inventory_entries = [entry.manifest_payload() for entry in inventory.entries]
    acceptance_material = json.dumps(
        [run_id, branch.value, inventory.inventory_digest],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    acceptance_id = "ec4g-a2-" + hashlib.sha256(acceptance_material).hexdigest()
    complete = branch is AuditBranch.COMPLETE_PREEXISTING_BINDING
    payload: dict[str, object] = {
        "activity_counts": {
            "environment_transitions": 0,
            "inventory_blob_reads": len(inventory.entries),
            "inventory_freezes": 1,
            "learner_calls": 0,
            "model_fits": 0,
            "optimizer_updates": 0,
            "policy_calls": 0,
            "registered_audit_runs": int(registered_audit),
            "return_evaluations": 0,
            "role_inspections": role_inspections,
            "stochastic_calls": 0,
            "trainer_calls": 0,
        },
        "ambiguous_witnesses": list(ambiguous_witnesses),
        "audited_result_commit": PUBLICATION_COMMIT,
        "audited_source_commit": SOURCE_COMMIT,
        "candidate_version": CANDIDATE_VERSION,
        "complete_preexisting_binding": complete,
        "document_kind": "ec4g_a2_prospective_contract_binding_audit_result",
        "eligible_to_consider_new_frozen_census": complete,
        "first_failure": first_failure,
        "freeze_failures": list(freeze_failures),
        "frozen_inventory": {
            "entries": inventory_entries,
            "inventory_digest": inventory.inventory_digest,
            "path_order": list(inventory.paths),
            "requested_commit": inventory.requested_commit,
            "resolved_commit": inventory.resolved_commit,
        },
        "incoherent_witnesses": list(incoherent_witnesses),
        "missing_witnesses": list(missing_witnesses),
        "post_freeze_witnesses": list(post_freeze_witnesses),
        "publication_commit": PUBLICATION_COMMIT,
        "public_locators": {
            "inventory": [entry["public_locator"] for entry in inventory_entries],
            "result": None,
            "source": f"{REMOTE_BLOB_ROOT}/{source_revision}/{SOURCE_PATH.rsplit('/', 1)[0]}/prospective_contract_binding_audit.py",
        },
        "result_revision": None,
        "result_revision_status": "assigned only when the one-shot artifact is published",
        "role_witness_table": list(role_rows),
        "route_status": (
            "ELIGIBLE_TO_CONSIDER_NEW_FROZEN_CENSUS"
            if complete
            else "PARKED_PENDING_FUTURE_COMPLETE_PROSPECTIVE_CONTRACT"
        ),
        "run_id": run_id,
        "schema_version": SCHEMA_VERSION,
        "source_commit": source_revision,
        "implementation_source_commit": source_revision,
        "source_predecessor_commit": SOURCE_COMMIT,
        "technical_acceptance": {
            "id": acceptance_id,
            "owner": "code_project_manager",
            "scope": "read-only prospective contract-binding audit only",
        },
        "terminal_branch": branch.value,
        "treatment_id": TREATMENT_ID,
    }
    return ProspectiveContractAuditResult(payload)


def _binding_candidates(
    inventory: FrozenInventory,
) -> tuple[tuple[BindingCandidate, ...], tuple[dict[str, object], ...]]:
    candidates: list[BindingCandidate] = []
    issues: list[dict[str, object]] = []
    for entry in inventory.entries:
        try:
            document = json.loads(entry.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(document, dict) or document.get("document_kind") != DECLARATION_KIND:
            continue
        if document.get("schema_version") != SCHEMA_VERSION:
            issues.append(
                {
                    "code": "DECLARATION_SCHEMA_VERSION_MISMATCH",
                    "detail": f"schema_version must equal {SCHEMA_VERSION}",
                    "path": entry.path,
                    "role": None,
                }
            )
        objects = document.get("objects")
        if not isinstance(objects, list):
            issues.append(
                {
                    "code": "DECLARATION_OBJECTS_NOT_A_LIST",
                    "detail": "prospective binding document must contain an objects list",
                    "path": entry.path,
                    "role": None,
                }
            )
            continue
        for ordinal, raw in enumerate(objects):
            if not isinstance(raw, dict):
                issues.append(
                    {
                        "code": "DECLARATION_OBJECT_NOT_A_MAPPING",
                        "detail": f"objects[{ordinal}] is not a mapping",
                        "path": entry.path,
                        "role": None,
                    }
                )
                continue
            if raw.get("role") not in ROLE_IDS:
                issues.append(
                    {
                        "code": "UNREGISTERED_ROLE",
                        "detail": f"objects[{ordinal}] does not name one of the fourteen frozen roles",
                        "path": entry.path,
                        "role": raw.get("role"),
                    }
                )
            manifest = document.get("freeze_manifest")
            candidates.append(
                BindingCandidate(
                    entry.path,
                    ordinal,
                    raw,
                    manifest if isinstance(manifest, dict) else None,
                )
            )
    return tuple(candidates), tuple(issues)


def _candidate_issues(
    candidate: BindingCandidate,
    role_id: str,
    ordinal: int,
    inventory: FrozenInventory,
) -> list[dict[str, object]]:
    raw = candidate.raw
    issues: list[dict[str, object]] = []

    def add(code: str, detail: str) -> None:
        issues.append({"code": code, "detail": detail, "role": role_id})

    object_id = raw.get("object_id")
    if not isinstance(object_id, str) or not object_id.strip():
        add("INVALID_OBJECT_IDENTITY", "object_id must be a nonempty string")
    source_path = raw.get("source_path")
    if source_path not in inventory.paths:
        add(
            "SOURCE_OUTSIDE_FROZEN_INVENTORY",
            "source_path is not already present in the frozen inventory",
        )
    else:
        frozen_source = next(entry for entry in inventory.entries if entry.path == source_path)
        source_digest = raw.get("source_blob_sha256")
        if not isinstance(source_digest, str) or not _DIGEST_RE.fullmatch(source_digest):
            add("INVALID_SOURCE_BLOB_DIGEST", "source_blob_sha256 must be lowercase 64-hex")
        elif source_digest != frozen_source.sha256:
            add(
                "SOURCE_BLOB_DIGEST_MISMATCH",
                "source_blob_sha256 does not bind the frozen provenance blob",
            )
    if raw.get("source_commit") != PUBLICATION_COMMIT:
        add("SOURCE_COMMIT_MISMATCH", "source_commit must equal the publication snapshot")
    fragment = raw.get("source_fragment")
    if not isinstance(fragment, str) or not fragment.strip():
        add("INVALID_SOURCE_FRAGMENT", "source_fragment must explicitly locate the object")
    if raw.get("frozen_before_inspection") is not True:
        add("NOT_FROZEN_BEFORE_INSPECTION", "binding is not declared frozen before role inspection")
    if raw.get("total") is not True:
        add("NON_TOTAL_OBJECT", "binding is not declared total over its frozen domain")
    if raw.get("freeze_ordinal") != ordinal:
        add("FREEZE_ORDINAL_MISMATCH", f"freeze_ordinal must equal {ordinal}")
    coherence = raw.get("coherence")
    if not isinstance(coherence, dict):
        add("MISSING_COHERENCE_TUPLE", "coherence must be a mapping")
    else:
        if set(coherence) != set(COHERENCE_FIELDS):
            add(
                "INVALID_COHERENCE_FIELDS",
                "coherence fields must exactly match the frozen contract",
            )
        for field in COHERENCE_FIELDS:
            value = coherence.get(field)
            if not isinstance(value, str) or not value:
                add("INVALID_COHERENCE_VALUE", f"{field} must be a nonempty string")
        if coherence.get("snapshot_commit") != PUBLICATION_COMMIT:
            add("COHERENCE_SNAPSHOT_MISMATCH", "coherence snapshot is not the publication commit")
    return issues


def _cross_object_issues(
    candidates: Mapping[str, BindingCandidate], inventory: FrozenInventory
) -> list[dict[str, object]]:
    if set(candidates) != set(ROLE_IDS):
        return []
    issues: list[dict[str, object]] = []
    reference = candidates[ROLE_IDS[0]].raw.get("coherence")
    if isinstance(reference, dict):
        for role_id in ROLE_IDS[1:]:
            coherence = candidates[role_id].raw.get("coherence")
            if coherence != reference:
                issues.append(
                    {
                        "code": "CROSS_OBJECT_COHERENCE_MISMATCH",
                        "detail": "population/horizon/unit/snapshot/domain/ordering/serialization/freeze-order tuple differs",
                        "role": role_id,
                    }
                )
    manifest = candidates["freeze_manifest"].declared_freeze_manifest
    expected_manifest = {
        "inventory_paths": list(inventory.paths),
        "publication_commit": PUBLICATION_COMMIT,
        "role_order": list(ROLE_IDS),
    }
    if manifest != expected_manifest:
        issues.append(
            {
                "code": "FREEZE_MANIFEST_MISMATCH",
                "detail": "freeze manifest does not exactly bind publication, inventory path order, and role order",
                "role": "freeze_manifest",
            }
        )
    return issues


def _a1_negative_evidence(inventory: FrozenInventory) -> dict[str, tuple[dict[str, object], ...]]:
    by_role: dict[str, list[dict[str, object]]] = {role_id: [] for role_id in ROLE_IDS}
    result = next((entry for entry in inventory.entries if entry.path == RESULT_PATH), None)
    if result is None:
        return {key: tuple(value) for key, value in by_role.items()}
    try:
        document = json.loads(result.content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {key: tuple(value) for key, value in by_role.items()}
    if not isinstance(document, dict) or document.get("document_kind") != "ec4g_a1_execution_digest_census_result":
        return {key: tuple(value) for key, value in by_role.items()}
    bindings = document.get("object_bindings")
    if not isinstance(bindings, list):
        return {key: tuple(value) for key, value in by_role.items()}
    by_object = {
        item.get("object_id"): (ordinal, item)
        for ordinal, item in enumerate(bindings)
        if isinstance(item, dict)
    }
    for role_id, a1_id in _A1_NEGATIVE_ROLE_MAP.items():
        located = by_object.get(a1_id)
        if located is None:
            continue
        ordinal, item = located
        by_role[role_id].append(
            {
                "detail": item.get("detail"),
                "evidence_locator": f"{RESULT_PATH}#/object_bindings/{ordinal}",
                "frozen": item.get("frozen"),
                "identity": item.get("identity"),
                "note": "A1 result is negative evidence only, never a role object",
                "source_locator": item.get("source_locator"),
                "total": item.get("total"),
            }
        )
    return {key: tuple(value) for key, value in by_role.items()}


def _first_role_failure(
    role_rows: Sequence[Mapping[str, object]],
    global_issues: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    for row in role_rows:
        issues = row.get("issues")
        if isinstance(issues, list) and issues:
            return issues[0]
    return global_issues[0]


def _not_inspected_rows(detail: str) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "candidate_count": None,
            "freeze_ordinal": ordinal,
            "issues": [],
            "object_id": None,
            "role": role_id,
            "role_label": label,
            "status": "NOT_INSPECTED",
            "status_detail": detail,
        }
        for ordinal, (role_id, label) in enumerate(ROLE_SPECS)
    )


def _direct_project_paths(index_text: str) -> tuple[str, ...]:
    paths: list[str] = []
    for span in _CODE_SPAN_RE.findall(index_text):
        candidate = span.split("::", 1)[0]
        if not candidate.startswith(_PROJECT_PREFIXES):
            continue
        if "\\" in candidate or ":" in candidate:
            continue
        path = PurePosixPath(candidate)
        if path.is_absolute() or ".." in path.parts or str(path) != candidate:
            continue
        paths.append(candidate)
    return _deduplicate(paths)


def _deduplicate(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _inventory_digest(entries: Sequence[FrozenBlob]) -> str:
    payload = [
        {"blob_oid": entry.blob_oid, "path": entry.path, "sha256": entry.sha256}
        for entry in entries
    ]
    return _json_sha256(payload)


def _invalid_inventory(code: str, detail: str) -> FrozenInventory:
    return FrozenInventory(
        requested_commit=PUBLICATION_COMMIT,
        resolved_commit=None,
        entries=(),
        failures=(FreezeFailure(code, None, detail),),
        inventory_digest=None,
    )


def _require_revision(value: str, name: str) -> None:
    if not _REVISION_RE.fullmatch(value):
        raise ValueError(f"{name} must be lowercase 40-hex")
