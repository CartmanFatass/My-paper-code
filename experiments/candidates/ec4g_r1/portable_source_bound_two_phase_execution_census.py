"""EC4G-A5 portable, source-bound, two-phase execution census.

The source-entry admission in this module is a technical gate.  It completes
before C0/C1 authentication and before any map or compiler call.  The admitted
scientific procedure is the immutable A3-bound RER3 census: six freshly
materialized objects are sealed, reopened from disk, compared in three fixed
pairs, and only then aggregated into ``D_RER3``.

The A4 module is used only as an admitted pure-code dependency.  No A4 runtime
artifact, inferred object, equality witness, or D value is read or reused.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Callable, Mapping, Sequence

from experiments.candidates.ec4g_r1 import two_phase_execution_materialization_census as a4


C0_COMMIT = a4.C0_COMMIT
C0_BLOB_OID = a4.C0_BLOB_OID
C0_SHA256 = a4.C0_SHA256
C1_COMMIT = a4.C1_COMMIT
C1_SHA256 = a4.C1_SHA256
CONTRACT_PATH = a4.CONTRACT_PATH
BINDING_PATH = a4.BINDING_PATH

SOURCE_PATH = "experiments/candidates/ec4g_r1/portable_source_bound_two_phase_execution_census.py"
RUNNER_PATH = "scripts/run_ec4g_a5_portable_source_bound_two_phase_execution_census.py"
PURE_ALGORITHM_DEPENDENCY_PATH = "experiments/candidates/ec4g_r1/two_phase_execution_materialization_census.py"
TREATMENT_ID = "EC4G-A5-PORTABLE-SOURCE-BOUND-TWO-PHASE-EXECUTION-CENSUS"
DESIGN_ID = "DESIGN-2026-08-10-EC4G-A5-PORTABLE-SOURCE-BOUND-TWO-PHASE-EXECUTION-CENSUS-V1"
CANDIDATE_VERSION = "CAND-VAP-EC4G-R1@rer3-prospective-complete-v8"
CONTRACT_ID = "EC4G-RER3-CONTRACT@1.0.0"

CELL_ORDER = a4.CELL_ORDER
MAP_ORDER = a4.MAP_ORDER
PAIR_ORDER = a4.PAIR_ORDER
MASSES = dict(a4.MASSES)
COMPARED_FIELDS = a4.COMPARED_FIELDS
EXCLUDED_FIELDS = a4.EXCLUDED_FIELDS
ROW_SCHEMA = a4.ROW_SCHEMA
ENTRY_POINTS = (
    f"{SOURCE_PATH}::map_ec4g",
    f"{SOURCE_PATH}::map_direct_tau",
    f"{SOURCE_PATH}::compile_gamma",
    f"{SOURCE_PATH}::run_portable_two_phase_census",
)
ORDERED_BRANCHES = (
    "A5_SOURCE_ENTRY_BINDING_INVALID",
    "A5_INPUT_OR_DESIGN_FREEZE_INVALID",
    "A5_FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE",
    "A5_MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS",
    "A5_PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID",
    "A5_PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL",
    "A5_COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS",
)
HARD_CAPS = {
    "runs": 1,
    "entry_records": 1,
    "snapshots": 1,
    "map_calls": 6,
    "compiler_calls": 6,
    "objects": 6,
    "comparisons": 3,
    "pair_witnesses": 3,
    "D": 1,
    "prediction_uses": 0,
    "post_seal_writes": 0,
    "human_decisions_between_phases": 0,
    "all_environment_policy_learning_training_optimizer_evaluation_model_fit_stochastic_calls": 0,
    "retries_repairs_corrected_invocations_rescans_reconstructions": 0,
}

_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOB_RE = re.compile(r"^[0-9a-f]{40,64}$")


class PortableCensusBranch(str, Enum):
    SOURCE_ENTRY_BINDING_INVALID = ORDERED_BRANCHES[0]
    INPUT_OR_DESIGN_FREEZE_INVALID = ORDERED_BRANCHES[1]
    FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE = ORDERED_BRANCHES[2]
    MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS = ORDERED_BRANCHES[3]
    PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID = ORDERED_BRANCHES[4]
    PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL = ORDERED_BRANCHES[5]
    COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS = ORDERED_BRANCHES[6]


@dataclass(frozen=True)
class SourceFileIdentity:
    role: str
    relative_path: str
    absolute_path: str
    sha256: str
    committed_blob_sha256: str
    git_blob_oid: str
    worktree_filtered_blob_oid: str
    match_mode: str

    def payload(self) -> dict[str, str]:
        return {
            "role": self.role,
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
            "sha256": self.sha256,
            "committed_blob_sha256": self.committed_blob_sha256,
            "git_blob_oid": self.git_blob_oid,
            "worktree_filtered_blob_oid": self.worktree_filtered_blob_oid,
            "match_mode": self.match_mode,
        }


@dataclass(frozen=True)
class SourceEntryAdmission:
    accepted: bool
    source_revision: str
    registered_worktree_root: str
    canonical_cwd: str
    main_checkout_root: str
    runner_file: str
    runtime_module_file: str
    pure_algorithm_dependency_file: str
    git_head: str | None
    files: tuple[SourceFileIdentity, ...]
    first_failure: Mapping[str, str] | None

    def payload(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "source_revision": self.source_revision,
            "registered_worktree_root": self.registered_worktree_root,
            "canonical_cwd": self.canonical_cwd,
            "main_checkout_root": self.main_checkout_root,
            "runner_file": self.runner_file,
            "runtime_module___file__": self.runtime_module_file,
            "pure_algorithm_dependency___file__": self.pure_algorithm_dependency_file,
            "git_head": self.git_head,
            "files": [item.payload() for item in self.files],
            "first_failure": dict(self.first_failure) if self.first_failure is not None else None,
            "checks_precede_all_map_and_compiler_calls": True,
        }


@dataclass(frozen=True)
class PortableCensusResult:
    terminal_branch: PortableCensusBranch
    run_id: str
    source_revision: str
    source_entry_admission: SourceEntryAdmission
    first_failure: Mapping[str, object] | None
    design_freeze: Mapping[str, object] | None
    activity_counts: Mapping[str, int]
    partial_rows: tuple[Mapping[str, object], ...] = ()
    seal: a4.Phase1Seal | None = None
    pair_witnesses: tuple[a4.PairWitness, ...] = ()
    equality_vector: Mapping[str, bool] | None = None
    d_fraction: Fraction | None = None
    d_decimal: Decimal | None = None
    seal_evidence: Mapping[str, object] | None = None

    def payload(self) -> dict[str, object]:
        seal_payload = dict(self.seal_evidence) if self.seal_evidence is not None else None
        if seal_payload is None and self.seal is not None:
            seal_payload = {
                "artifact_root": str(self.seal.artifact_root),
                "status": "invalid_or_not_independently_validated",
            }
        return {
            "schema_version": 1,
            "document_kind": "ec4g_a5_portable_source_bound_two_phase_execution_census_result",
            "treatment_id": TREATMENT_ID,
            "design_id": DESIGN_ID,
            "candidate_version": CANDIDATE_VERSION,
            "run_id": self.run_id,
            "result_id": f"ec4g-a5-{self.run_id}",
            "terminal_branch": self.terminal_branch.value,
            "first_failure": dict(self.first_failure) if self.first_failure is not None else None,
            "source_entry_admission": self.source_entry_admission.payload(),
            "source_identities": {
                "c0_commit": C0_COMMIT,
                "c0_blob_oid": C0_BLOB_OID,
                "c0_sha256": C0_SHA256,
                "c1_commit": C1_COMMIT,
                "c1_sha256": C1_SHA256,
                "implementation_source_revision": self.source_revision,
                "result_revision": None,
                "result_revision_status": "assigned only after one-shot publication",
            },
            "design_freeze": dict(self.design_freeze) if self.design_freeze is not None else None,
            "activity_counts": dict(self.activity_counts),
            "partial_rows": [dict(row) for row in self.partial_rows],
            "phase_1_seal": seal_payload,
            "pair_witnesses": [witness.payload() for witness in self.pair_witnesses],
            "equality_vector": dict(self.equality_vector) if self.equality_vector is not None else None,
            "D_RER3": (
                {
                    "fraction": _fraction_text(self.d_fraction),
                    "decimal": format(self.d_decimal, "f"),
                    "meaning": "configured-population structural discordance only",
                }
                if self.d_fraction is not None and self.d_decimal is not None
                else None
            ),
            "fresh_identity": {
                "a4_runtime_artifacts_read": 0,
                "a4_inferred_objects_reused": 0,
                "a4_equality_or_D_reused": 0,
                "fresh_phase_1_required": True,
            },
            "operator_receipt": {"owner": "code_project_manager", "status": "not_invoked_by_source"},
            "execution_readiness": {
                "owner": "code_project_manager",
                "status": "pending_registered_execution_readiness",
            },
            "technical_acceptance": {
                "owner": "code_project_manager",
                "status": "pending_code_project_manager_acceptance",
            },
            "nonclaims": (
                "No A4 retry or repair, natural prevalence, causal value, reward or return superiority, "
                "learning, B, C, formal compute, Pro, promotion, retirement, or automatic successor."
            ),
        }

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(self.payload())


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _failure(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _canonical(path: Path, *, strict: bool) -> Path:
    return path.expanduser().resolve(strict=strict)


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left)) == os.path.normcase(str(right))


def _is_beneath(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_symlink_component(root: Path, relative_path: str) -> bool:
    current = root
    for component in Path(relative_path).parts:
        current = current / component
        if current.is_symlink():
            return True
    return False


def _git(root: Path, *arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=not binary,
        encoding=None if binary else "utf-8",
    )
    return completed.stdout


def _invalid_entry(
    *,
    source_revision: str,
    root: Path,
    cwd: Path,
    main: Path,
    runner: Path,
    runtime_module: Path,
    dependency_module: Path,
    git_head: str | None,
    files: Sequence[SourceFileIdentity],
    detail: str,
) -> SourceEntryAdmission:
    return SourceEntryAdmission(
        False,
        source_revision,
        str(root),
        str(cwd),
        str(main),
        str(runner),
        str(runtime_module),
        str(dependency_module),
        git_head,
        tuple(files),
        _failure("SOURCE_ENTRY_BINDING_INVALID", detail),
    )


def admit_source_entry(
    *,
    source_revision: str,
    registered_worktree_root: Path,
    main_checkout_root: Path,
    runner_file: Path,
    runtime_module_file: Path,
    pure_algorithm_dependency_file: Path,
    cwd: Path | None = None,
) -> SourceEntryAdmission:
    """Bind the actual process entry to one frozen source checkout.

    All failures are converted into one fail-closed record.  This function has
    no access to C0/C1 and cannot call the maps or compiler.
    """

    lexical_root = Path(os.path.abspath(registered_worktree_root))
    lexical_main = Path(os.path.abspath(main_checkout_root))
    lexical_cwd = Path(os.path.abspath(cwd if cwd is not None else Path.cwd()))
    lexical_runner = Path(os.path.abspath(runner_file))
    lexical_runtime = Path(os.path.abspath(runtime_module_file))
    lexical_dependency = Path(os.path.abspath(pure_algorithm_dependency_file))
    root = lexical_root
    main = lexical_main
    canonical_cwd = lexical_cwd
    runner = lexical_runner
    runtime_module = lexical_runtime
    dependency_module = lexical_dependency
    head: str | None = None
    files: list[SourceFileIdentity] = []
    try:
        root = _canonical(lexical_root, strict=True)
        main = _canonical(lexical_main, strict=True)
        canonical_cwd = _canonical(lexical_cwd, strict=True)
        runner = _canonical(lexical_runner, strict=True)
        runtime_module = _canonical(lexical_runtime, strict=True)
        dependency_module = _canonical(lexical_dependency, strict=True)
        if not _REVISION_RE.fullmatch(source_revision):
            raise ValueError("source revision must be exact lowercase 40-hex")
        if not _same_path(canonical_cwd, root):
            raise ValueError("canonical cwd does not equal registered source worktree root")
        if _same_path(root, main):
            raise ValueError("registered source worktree root equals the main checkout")
        toplevel = _canonical(Path(str(_git(root, "rev-parse", "--show-toplevel")).strip()), strict=True)
        if not _same_path(toplevel, root):
            raise ValueError("registered root is not the checkout Git toplevel")
        resolved_commit = str(_git(root, "rev-parse", "--verify", f"{source_revision}^{{commit}}")).strip()
        if resolved_commit != source_revision:
            raise ValueError("declared source revision does not resolve exactly")
        head = str(_git(root, "rev-parse", "HEAD")).strip()
        if head != source_revision:
            raise ValueError("registered worktree HEAD differs from declared frozen source revision")

        declared = (
            ("runner", RUNNER_PATH, runner),
            ("runtime_core_module", SOURCE_PATH, runtime_module),
            ("pure_algorithm_dependency", PURE_ALGORITHM_DEPENDENCY_PATH, dependency_module),
        )
        for role, relative_path, actual_path in declared:
            expected_lexical = Path(os.path.abspath(root / relative_path))
            expected = _canonical(expected_lexical, strict=True)
            if not _same_path(actual_path, expected):
                raise ValueError(f"{role} __file__/entry path differs from registered relative path")
            if not _is_beneath(actual_path, root):
                raise ValueError(f"{role} escapes registered root")
            if _has_symlink_component(root, relative_path):
                raise ValueError(f"{role} has a symlink component")
            if not actual_path.is_file():
                raise ValueError(f"{role} is not a regular file")
            object_type = str(_git(root, "cat-file", "-t", f"{source_revision}:{relative_path}")).strip()
            if object_type != "blob":
                raise ValueError(f"{role} source entry is not a Git blob")
            blob_oid = str(_git(root, "rev-parse", f"{source_revision}:{relative_path}")).strip()
            if not _BLOB_RE.fullmatch(blob_oid):
                raise ValueError(f"{role} Git blob identity is malformed")
            committed = bytes(_git(root, "cat-file", "blob", f"{source_revision}:{relative_path}", binary=True))
            live = actual_path.read_bytes()
            worktree_blob_oid = str(
                _git(root, "hash-object", f"--path={relative_path}", relative_path)
            ).strip()
            if not _BLOB_RE.fullmatch(worktree_blob_oid):
                raise ValueError(f"{role} filtered worktree blob identity is malformed")
            raw_match = live == committed
            filtered_match = worktree_blob_oid == blob_oid
            if not raw_match and not filtered_match:
                raise ValueError(f"{role} live bytes/filtered Git blob differ from frozen source commit")
            files.append(
                SourceFileIdentity(
                    role,
                    relative_path,
                    str(actual_path),
                    hashlib.sha256(live).hexdigest(),
                    hashlib.sha256(committed).hexdigest(),
                    blob_oid,
                    worktree_blob_oid,
                    "raw_bytes" if raw_match else "git_clean_filter_blob",
                )
            )
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        return _invalid_entry(
            source_revision=source_revision,
            root=root,
            cwd=canonical_cwd,
            main=main,
            runner=runner,
            runtime_module=runtime_module,
            dependency_module=dependency_module,
            git_head=head,
            files=files,
            detail=str(exc),
        )
    return SourceEntryAdmission(
        True,
        source_revision,
        str(root),
        str(canonical_cwd),
        str(main),
        str(runner),
        str(runtime_module),
        str(dependency_module),
        head,
        tuple(files),
        None,
    )


def map_ec4g(contract: Mapping[str, object], cell: str) -> str:
    """A5 entry point for the admitted C0-derived EC4G map."""

    return a4.map_ec4g(contract, cell)


def map_direct_tau(contract: Mapping[str, object], cell: str) -> str:
    """A5 entry point for the admitted C0-derived Direct-tau map."""

    return a4.map_direct_tau(contract, cell)


def compile_gamma(
    contract: Mapping[str, object],
    cell: str,
    action: str,
    map_identity: str,
) -> Mapping[str, object]:
    """A5 entry point for the admitted complete execution compiler."""

    return a4.compile_gamma(contract, cell, action, map_identity)


DEFAULT_COMPONENTS = a4.ExecutionComponents(map_ec4g, map_direct_tau, compile_gamma)


def _empty_counts() -> dict[str, int]:
    return {key: 0 for key in HARD_CAPS} | {"runs": 1, "entry_records": 1}


def _legacy_activity() -> dict[str, int]:
    return {key: 0 for key in a4.HARD_CAPS}


def _sync_phase1_counts(counts: dict[str, int], activity: Mapping[str, int]) -> None:
    counts["snapshots"] = int(activity["materialization_snapshots"])
    counts["map_calls"] = int(activity["complete_map_calls"])
    counts["compiler_calls"] = int(activity["complete_program_compilations"])
    counts["objects"] = int(activity["complete_execution_objects"])


def _design(source_revision: str) -> a4.DesignFreeze:
    if not _REVISION_RE.fullmatch(source_revision):
        raise ValueError("implementation source revision must be lowercase 40-hex")
    return a4.DesignFreeze(
        source_revision=source_revision,
        source_path=SOURCE_PATH,
        runner_path=RUNNER_PATH,
        entry_points=ENTRY_POINTS,
        row_schema=ROW_SCHEMA,
        cell_order=CELL_ORDER,
        map_order=MAP_ORDER,
        pair_order=PAIR_ORDER,
        compared_fields=COMPARED_FIELDS,
        excluded_fields=EXCLUDED_FIELDS,
        masses=dict(MASSES),
        ordered_branches=ORDERED_BRANCHES,
        hard_caps=dict(HARD_CAPS),
    )


def _design_payload(design: a4.DesignFreeze) -> dict[str, object]:
    return {
        "source_revision": design.source_revision,
        "source_path": SOURCE_PATH,
        "runner_path": RUNNER_PATH,
        "admitted_pure_algorithm_dependency": PURE_ALGORITHM_DEPENDENCY_PATH,
        "entry_points": list(ENTRY_POINTS),
        "row_schema": list(ROW_SCHEMA),
        "cell_order": list(CELL_ORDER),
        "map_order": list(MAP_ORDER),
        "pair_order": list(PAIR_ORDER),
        "canonical_equality": {
            "compared_fields": list(COMPARED_FIELDS),
            "excluded_fields": list(EXCLUDED_FIELDS),
            "rule": "exact canonical compared-field bytes; hashes are audit evidence only",
        },
        "D": {
            "formula": "0.50*I[join differs]+0.25*I[leave differs]+0.25*I[rejoin differs]",
            "masses": dict(MASSES),
        },
        "ordered_branches": list(ORDERED_BRANCHES),
        "hard_caps": dict(HARD_CAPS),
    }


def _result(
    branch: PortableCensusBranch,
    run_id: str,
    source_revision: str,
    entry: SourceEntryAdmission,
    counts: Mapping[str, int],
    first_failure: Mapping[str, object] | None,
    *,
    design: a4.DesignFreeze | None = None,
    partial: Sequence[Mapping[str, object]] = (),
    seal: a4.Phase1Seal | None = None,
    witnesses: Sequence[a4.PairWitness] = (),
    equality: Mapping[str, bool] | None = None,
    d_fraction: Fraction | None = None,
    d_decimal: Decimal | None = None,
    seal_evidence: Mapping[str, object] | None = None,
) -> PortableCensusResult:
    return PortableCensusResult(
        branch,
        run_id,
        source_revision,
        entry,
        first_failure,
        _design_payload(design) if design is not None else None,
        dict(counts),
        tuple(partial),
        seal,
        tuple(witnesses),
        equality,
        d_fraction,
        d_decimal,
        seal_evidence,
    )


def run_portable_two_phase_census(
    c0_bytes: bytes | None,
    c1_bytes: bytes | None,
    *,
    entry_admission: SourceEntryAdmission,
    artifact_root: Path,
    run_id: str,
    components: a4.ExecutionComponents = DEFAULT_COMPONENTS,
    information_flow_events: Sequence[Mapping[str, object]] = (),
    input_read_failure: str | None = None,
    after_seal: Callable[[a4.Phase1Seal], None] | None = None,
) -> PortableCensusResult:
    """Run the unique A5 treatment after the separately recorded entry gate."""

    counts = _empty_counts()
    source_revision = entry_admission.source_revision
    if not entry_admission.accepted:
        return _result(
            PortableCensusBranch.SOURCE_ENTRY_BINDING_INVALID,
            run_id,
            source_revision,
            entry_admission,
            counts,
            entry_admission.first_failure,
        )
    if not run_id.strip():
        return _result(
            PortableCensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID,
            run_id,
            source_revision,
            entry_admission,
            counts,
            _failure("EMPTY_RUN_ID", "run_id must be nonempty"),
        )
    if input_read_failure is not None:
        return _result(
            PortableCensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID,
            run_id,
            source_revision,
            entry_admission,
            counts,
            _failure("C0_C1_SNAPSHOT_READ_FAILED", input_read_failure),
        )
    try:
        if c0_bytes is None or c1_bytes is None:
            raise ValueError("authenticated C0/C1 bytes are required only after accepted entry admission")
        authenticated = a4.authenticate_immutable_inputs(c0_bytes, c1_bytes)
        design = _design(source_revision)
        if artifact_root.resolve(strict=False).exists():
            raise ValueError("artifact root already exists; one-shot materialization refuses overwrite")
    except PermissionError as exc:
        return _result(
            PortableCensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE,
            run_id,
            source_revision,
            entry_admission,
            counts,
            _failure("SELF_REFERENCE", str(exc)),
        )
    except (OSError, a4.StrictJsonError, ValueError) as exc:
        return _result(
            PortableCensusBranch.INPUT_OR_DESIGN_FREEZE_INVALID,
            run_id,
            source_revision,
            entry_admission,
            counts,
            _failure("INPUT_OR_DESIGN_INVALID", str(exc)),
        )
    if information_flow_events:
        if information_flow_events[0].get("code") == "PREDICTION_FIELD_USE":
            counts["prediction_uses"] = 1
        return _result(
            PortableCensusBranch.FORBIDDEN_INFORMATION_FLOW_OR_SELF_REFERENCE,
            run_id,
            source_revision,
            entry_admission,
            counts,
            dict(information_flow_events[0]),
            design=design,
        )

    seal: a4.Phase1Seal | None = None
    activity = _legacy_activity()
    try:
        seal = a4.materialize_and_seal_phase1(
            authenticated,
            design,
            artifact_root,
            components=components,
            activity=activity,
        )
        _sync_phase1_counts(counts, activity)
    except (OSError, a4.StrictJsonError, ValueError, a4.MaterializationError) as exc:
        _sync_phase1_counts(counts, activity)
        partial = a4._read_partial_rows(artifact_root)
        return _result(
            PortableCensusBranch.MATERIALIZATION_INCOMPLETE_OR_AMBIGUOUS,
            run_id,
            source_revision,
            entry_admission,
            counts,
            _failure("PHASE1_MATERIALIZATION_FAILED", str(exc)),
            design=design,
            partial=partial,
        )
    if after_seal is not None:
        after_seal(seal)

    witnesses, equality, d_fraction, d_decimal, failure = a4.census_sealed_phase2(seal, design)
    if failure is not None and failure.get("code") in {
        "SEALED_BYTES_UNREADABLE",
        "SEALED_ARTIFACT_INTEGRITY_INVALID",
    }:
        if failure.get("code") == "SEALED_ARTIFACT_INTEGRITY_INVALID":
            counts["post_seal_writes"] = 1
        return _result(
            PortableCensusBranch.PHASE_BARRIER_OR_POST_SEAL_CHANGE_INVALID,
            run_id,
            source_revision,
            entry_admission,
            counts,
            failure,
            design=design,
            seal=seal,
        )
    counts["comparisons"] = 3
    counts["pair_witnesses"] = sum(item.status == "COMPLETE" for item in witnesses)
    seal_evidence = a4._seal_evidence_from_disk(seal.artifact_root, design)
    if failure is not None:
        return _result(
            PortableCensusBranch.PAIRED_CENSUS_INCOMPLETE_OR_NONCANONICAL,
            run_id,
            source_revision,
            entry_admission,
            counts,
            failure,
            design=design,
            seal=seal,
            witnesses=witnesses,
            seal_evidence=seal_evidence,
        )
    counts["D"] = 1
    return _result(
        PortableCensusBranch.COMPLETE_PORTABLE_TWO_PHASE_EXECUTION_CENSUS,
        run_id,
        source_revision,
        entry_admission,
        counts,
        None,
        design=design,
        seal=seal,
        witnesses=witnesses,
        equality=equality,
        d_fraction=d_fraction,
        d_decimal=d_decimal,
        seal_evidence=seal_evidence,
    )


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
