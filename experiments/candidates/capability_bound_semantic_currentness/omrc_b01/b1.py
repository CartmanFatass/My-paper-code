"""Fail-closed canonical orchestration boundary for CBSC-OMRC-B1.

The raw arm/seed engine is deliberately a child process.  This parent owns
source identity, result-blind B0 evidence location, fresh memory admission,
live resource supervision, and create-only transaction boundaries.  Formal
execution remains refused while the prospective .03 analysis decision is
pending; changing that state is not an engineering option in this module.
"""

from __future__ import annotations

import hashlib
import importlib
import inspect
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import uuid
from dataclasses import dataclass

from .artifact import (
    PINNED_EVIDENCE_REF,
    canonical_json_bytes,
    directory_size,
    ensure_confined,
)
from .b0 import ARMS, MIN_AVAILABLE_BYTES, validate_memory_receipt
from .b1_metrics_artifact import (
    FORMAL_ANALYSIS_BOUND,
    LITERAL_BINDING_SPEC_RELATIVE_PATH,
    READINESS_DISPOSITION,
    formal_analysis_record,
    require_parallel_module_protocols,
)
from .b1_metrics_policy_assembly import (
    ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT,
    ONE_SLOT_EXECUTION_MODE_RECORD_COUNT,
    ONE_SLOT_FORMAL_POLICY_CURVE_COUNT,
    ONE_SLOT_FORMAL_POLICY_DECISION_COUNT,
)
from .b1_metrics_production import (
    B1PolicyReplayBatchWitness,
    assemble_and_publish_b1_metrics,
    make_b1_canonical_authority_witness,
    make_b1_policy_replay_batch_witness,
)
from .b1_artifact import (
    B1IncidentLineageWitness,
    create_b1_staging_directory,
    make_b1_incident_lineage_witness,
    publish_b1_incident,
)
from .b1_contract import (
    B1AttemptLedger,
    B1LedgerBinding,
    B1ResumeCheckpointBinding,
    B1SlotLedgerEntry,
    B1SlotStatus,
    B1_LEDGER_PUBLICATION_MODE,
    B1_LEDGER_SCHEMA,
    B1_OBJECT_DURABLE_CAP_BYTES,
    B1_BOUND_ADMISSION_SCHEMA,
    B1_CHECKPOINT_UPDATES,
    B1_EVAL_MOTIF_IDS,
    B1_EVAL_STOCHASTIC_IDS,
    B1_RESOURCE_CAPS,
    B1_RUN_NAME,
    B1_SEEDS,
    B1_TRAIN_EPISODE_IDS,
    B1ArmSeedRequest,
    B1Plan,
)
from .b1_engine import (
    B1_RAW_EVIDENCE_SCHEMA,
    LiteralB1ArmSeedEngine,
    load_b1_checkpoint,
)
from .b1_worker import WORKER_RESULT_SCHEMA, wrap_worker_result
from .b1_policy_replay_worker import encode_policy_replay_request
from .telemetry import (
    ProcessTreeMonitor,
    RECORDED_BUDGET_CAPS,
    ResourceCaps,
    STOPPING_CAPS,
    TelemetryError,
    assess_resource_telemetry,
    validate_telemetry,
)


class B1OrchestrationError(RuntimeError):
    """The formal B1 control path is incomplete or identity-inconsistent."""


@dataclass(frozen=True)
class B1ReadinessResult:
    authorized: bool
    status: str
    disposition: str
    blockers: tuple[str, ...]


def _readiness_result(
    *, source_ready: bool | None = None, b0_ready: bool | None = None,
) -> B1ReadinessResult:
    blockers: list[str] = []
    try:
        require_parallel_module_protocols()
    except ValueError as exc:
        blockers.append(str(exc))
    # Section-11 recast (owner decision 3, 2026-09-02).  The two blockers that
    # stood here --
    #   if not FORMAL_ANALYSIS_BOUND:
    #       blockers.append("formal .03 metrics analysis/publication law is not bound")
    #   if READINESS_DISPOSITION != "READY":
    #       blockers.append(f"canonical metrics readiness disposition is {READINESS_DISPOSITION}")
    # -- are removed.  Evidence spec §11.4 does not permit a formal-analysis
    # flag to hold a B launch and §11.6 demotes it explicitly.  Both values are
    # still reported, in `readiness_document()["formal_analysis_record"]` and in
    # every published manifest, with `gating: false`.
    if source_ready is False:
        blockers.append("implementation commit/source conformance is required")
    if b0_ready is False:
        blockers.append("reviewed B0 evidence locator is required")
    authorized = not blockers
    return B1ReadinessResult(
        authorized=authorized,
        status="B1_FORMAL_READY" if authorized else "B1_RAW_PUBLICATION_INTEGRATION_REPAIR_REQUIRED",
        disposition="READY" if authorized else "REPAIR_REQUIRED",
        blockers=tuple(blockers),
    )


DIRECTION_ID = "capability_bound_semantic_currentness"
DECISION = "DECISION_PENDING"
ARM_SEED_ORDER = tuple((seed, arm) for seed in B1_SEEDS for arm in ARMS)
PRODUCTION_ASSEMBLY = (
    "b1_metrics_rehydrate",
    "b1_metrics_policy_assembly",
    "b1_metrics_training_assembly",
    "exact_15_table_preparation",
    "prospective_final_size_fixed_point",
    "b1_metrics_create_only_publication",
)
B0_REVIEWED_AUTHORITY = {
    "manifest_sha256": "c7c6f73be17e785cbe6ffaba6cfd30c4c8483ecf23e43bbd48df535c676bc298",
    "manifest_bytes": 733_056,
    "manifest_schema": "cbsc_omrc_b01_b_explore_result_v1",
    "source_commit": "888bd9f50eeea2f6b99d23b9b53b9f4724e19939",
    "source_conformance_sha256": "05a24221cd4f64f9bbe2f8cadf5bcc88939b2224d8d5e63a28430b49861bdd4f",
    "review_disposition": "CLEAN",
    "reviewer_scope": "B0_ENGINEERING_EVIDENCE_COMPLETE",
    "inventory_sha256": "184fa6ad3c915d728892923e7b99840c8faba95fe78647f869f81ecf2fb4f9c5",
    "file_count": 33,
    "total_bytes": 12_807_274,
}
B0_REVIEWED_RECEIPT_SHA256 = hashlib.sha256(
    canonical_json_bytes(B0_REVIEWED_AUTHORITY)
).hexdigest()

REPO_ROOT = Path(__file__).resolve().parents[4]
CONFINED_ROOT = (REPO_ROOT / "temp" / "directions" / DIRECTION_ID).resolve(strict=False)
CANONICAL_PREFLIGHT = (REPO_ROOT / "scripts" / "hmasd_resource_preflight.py").resolve()
CANONICAL_ENGINE_MODULE = (
    "experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_engine"
)
CANONICAL_ENGINE_FACTORY = "b1_engine"
CANONICAL_ENGINE_TYPE = "LiteralB1ArmSeedEngine"
CANONICAL_WORKER_MODULE = (
    "experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_worker"
)

CANONICAL_SOURCE_SURFACE = tuple(dict.fromkeys((
    *(path for path in LiteralB1ArmSeedEngine.source_paths if path not in {
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_analysis.py",
        "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_evidence.py",
    }),
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_artifact.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_shared_tables.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_policy_records.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_training_records.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_mechanical.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_descriptive.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_artifact.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_rehydrate.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_policy_assembly.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_training_assembly.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_production.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_policy_replay_worker.py",
    "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md",
    "scripts/hmasd_resource_preflight.py",
    "scripts/run_cbsc_omrc_b01.py",
    "scripts/run_cbsc_omrc_b01_b1.py",
)))


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_commit(value: str) -> str:
    if type(value) is not str or len(value) != 40:
        raise B1OrchestrationError("implementation_commit must be lowercase Git hex")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise B1OrchestrationError("implementation_commit must be lowercase Git hex") from exc
    if len(decoded) != 20 or decoded.hex() != value:
        raise B1OrchestrationError("implementation_commit must be lowercase Git hex")
    return value


def canonical_engine_identity() -> dict[str, str]:
    module = importlib.import_module(CANONICAL_ENGINE_MODULE)
    factory = getattr(module, CANONICAL_ENGINE_FACTORY, None)
    engine_type = getattr(module, CANONICAL_ENGINE_TYPE, None)
    worker = importlib.import_module(CANONICAL_WORKER_MODULE)
    if not callable(factory) or not inspect.isclass(engine_type):
        raise B1OrchestrationError("canonical B1 engine factory/type is absent")
    factory_file = Path(inspect.getsourcefile(factory) or "").resolve()
    type_file = Path(inspect.getsourcefile(engine_type) or "").resolve()
    worker_file = Path(inspect.getsourcefile(worker) or "").resolve()
    expected_engine = (
        REPO_ROOT
        / "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_engine.py"
    ).resolve()
    expected_worker = (
        REPO_ROOT
        / "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_worker.py"
    ).resolve()
    if (
        factory.__module__ != CANONICAL_ENGINE_MODULE
        or engine_type.__module__ != CANONICAL_ENGINE_MODULE
        or factory_file != expected_engine
        or type_file != expected_engine
        or worker.__name__ != CANONICAL_WORKER_MODULE
        or worker_file != expected_worker
    ):
        raise B1OrchestrationError("canonical B1 factory/type/worker identity differs")
    return {
        "module": CANONICAL_ENGINE_MODULE,
        "factory": CANONICAL_ENGINE_FACTORY,
        "type": CANONICAL_ENGINE_TYPE,
        "factory_file": factory_file.relative_to(REPO_ROOT).as_posix(),
        "type_file": type_file.relative_to(REPO_ROOT).as_posix(),
        "worker_module": CANONICAL_WORKER_MODULE,
        "worker_file": worker_file.relative_to(REPO_ROOT).as_posix(),
    }


def verify_source_conformance(
    implementation_commit: str, *, require_head_match: bool = True
) -> dict[str, Any]:
    """Bind every formal source byte to the bound commit.

    ``require_head_match`` is the launch-time requirement that the bound commit
    IS current HEAD, and it stays true there.  At publication time it is false.
    A B1 attempt runs for tens of minutes while other sessions commit to main,
    so which commit HEAD happens to point at when the artifact is written is not
    a property of this run and carries no scientific meaning.  What must hold in
    both cases is that the executing bytes are the bound bytes, and the two
    checks below already establish exactly that: the working tree carries no
    uncommitted change to the canonical surface, and that surface is
    byte-identical to the bound commit's.  A change to the canonical surface
    therefore still refuses, through "source bytes differ from commit", whether
    or not HEAD has moved.

    The returned receipt is deliberately unchanged by this flag: it is hashed
    into ``source_conformance_sha256`` and compared byte-for-byte against the
    launch-time receipt by ``materialize_b1_canonical_authority_witness``, so
    recording the observed HEAD in it would reintroduce the same fragility.
    """

    commit = _require_commit(implementation_commit)

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
            shell=False, timeout=60,
        )

    head = git("rev-parse", "HEAD")
    if head.returncode != 0:
        raise B1OrchestrationError("BLOCKED_UNCOMMITTED: HEAD is unreadable")
    if require_head_match and head.stdout.strip() != commit:
        raise B1OrchestrationError("BLOCKED_UNCOMMITTED: implementation_commit is not current HEAD")
    paths = [(REPO_ROOT / relative).resolve() for relative in CANONICAL_SOURCE_SURFACE]
    if any(not path.is_file() for path in paths):
        raise B1OrchestrationError("BLOCKED_UNCOMMITTED: canonical B1 source surface is incomplete")
    for relative in CANONICAL_SOURCE_SURFACE:
        if git("ls-files", "--error-unmatch", "--", relative).returncode != 0:
            raise B1OrchestrationError(f"BLOCKED_UNCOMMITTED: source is not tracked: {relative}")
    status = git(
        "status", "--porcelain", "--untracked-files=all", "--", *CANONICAL_SOURCE_SURFACE
    )
    if status.returncode != 0 or status.stdout.strip():
        raise B1OrchestrationError("BLOCKED_UNCOMMITTED: implementation source differs from HEAD")
    if git("diff", "--quiet", commit, "--", *CANONICAL_SOURCE_SURFACE).returncode != 0:
        raise B1OrchestrationError("BLOCKED_UNCOMMITTED: source bytes differ from commit")
    receipt: dict[str, Any] = {
        "status": "COMMIT_CONFORMANT",
        "commit": commit,
        "canonical_engine": canonical_engine_identity(),
        "files": [
            {"path": relative, "sha256": _digest(path.read_bytes())}
            for relative, path in zip(CANONICAL_SOURCE_SURFACE, paths)
        ],
    }
    receipt["source_conformance_sha256"] = _digest(canonical_json_bytes(receipt))
    return receipt


def locate_b0_evidence(b0_root: Path) -> dict[str, Any]:
    """Bind exact reviewed B0 manifest bytes without parsing outcome content."""

    root = ensure_confined(Path(b0_root), CONFINED_ROOT)
    manifest = root / "manifest.json"
    if not root.is_dir() or not manifest.is_file():
        raise B1OrchestrationError("B0 complete evidence root/manifest is absent")
    payload = manifest.read_bytes()
    manifest_sha256 = _digest(payload)
    if (
        len(payload) != B0_REVIEWED_AUTHORITY["manifest_bytes"]
        or manifest_sha256 != B0_REVIEWED_AUTHORITY["manifest_sha256"]
    ):
        raise B1OrchestrationError(
            "B0 manifest bytes/hash differ from the fixed reviewed r02 authority"
        )
    inventory: list[dict[str, Any]] = []
    try:
        for path in sorted(
            (candidate for candidate in root.rglob("*") if candidate.is_file()),
            key=lambda candidate: candidate.relative_to(root).as_posix(),
        ):
            file_payload = path.read_bytes()
            inventory.append({
                "path": path.relative_to(root).as_posix(),
                "byte_count": len(file_payload),
                "sha256": _digest(file_payload),
            })
    except OSError as exc:
        raise B1OrchestrationError("B0 evidence inventory cannot be read exactly") from exc
    inventory_sha256 = _digest(canonical_json_bytes(inventory))
    total_bytes = sum(record["byte_count"] for record in inventory)
    if (
        inventory_sha256 != B0_REVIEWED_AUTHORITY["inventory_sha256"]
        or len(inventory) != B0_REVIEWED_AUTHORITY["file_count"]
        or total_bytes != B0_REVIEWED_AUTHORITY["total_bytes"]
    ):
        raise B1OrchestrationError(
            "B0 evidence inventory differs from the fixed reviewed r02 authority"
        )
    return {
        "root": str(root),
        "manifest_path": str(manifest),
        "manifest_sha256": manifest_sha256,
        "manifest_bytes": len(payload),
        "inventory_sha256": inventory_sha256,
        "file_count": len(inventory),
        "total_bytes": total_bytes,
        "reviewed_receipt": dict(B0_REVIEWED_AUTHORITY),
        "reviewed_receipt_sha256": B0_REVIEWED_RECEIPT_SHA256,
        "content_read_policy": "LOCATOR_AND_RAW_BYTE_HASH_ONLY_NO_EVALUATOR_PARSE",
    }


def readiness_document(
    implementation_commit: str | None = None, b0_root: Path | None = None
) -> dict[str, Any]:
    source = verify_source_conformance(implementation_commit) if implementation_commit else None
    b0 = locate_b0_evidence(b0_root) if b0_root else None
    inputs_requested = implementation_commit is not None or b0_root is not None
    readiness = _readiness_result(
        source_ready=(source is not None) if inputs_requested else None,
        b0_ready=(b0 is not None) if inputs_requested else None,
    )
    return {
        "status": readiness.status,
        "engine_bound": True,
        "engine_contract": "CANONICAL_FIXED_FACTORY_AND_WORKER_ONLY",
        "engine_spec": f"{CANONICAL_ENGINE_MODULE}:{CANONICAL_ENGINE_FACTORY}",
        "worker_module": CANONICAL_WORKER_MODULE,
        "source_conformance": source,
        "b0_evidence": b0,
        "arm_seed_order": [[seed, arm] for seed, arm in ARM_SEED_ORDER],
        "resource_caps": B1_RESOURCE_CAPS.as_dict(),
        "formal_analysis_bound": FORMAL_ANALYSIS_BOUND,
        "formal_analysis_record": formal_analysis_record(),
        "production_assembly": list(PRODUCTION_ASSEMBLY),
        "production_assembly_ready": readiness.authorized,
        "start_authorized": readiness.authorized,
        "resume_authorized": readiness.authorized,
        "blockers": list(readiness.blockers),
        "blocker": None if readiness.authorized else "REPAIR_REQUIRED; see blockers",
        "decision": DECISION,
        "scientific_branch": None,
        "performance_disposition": "PILOT_ONLY",
        "readiness_disposition": readiness.disposition,
    }


def _atomic_create_json(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise FileExistsError(f"create-only control record exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def validate_bound_admission(
    value: Mapping[str, Any], *, expected_attempt_id: str, expected_arm: str,
    expected_seed: int, expected_commit: str, expected_receipt_path: Path | None = None,
) -> dict[str, Any]:
    """Validate that a fresh 4-GiB receipt is bound to one exact invocation."""

    bound = dict(value)
    required = {
        "schema", "attempt_id", "run_name", "arm", "seed",
        "implementation_commit", "source_conformance_sha256",
        "bound_receipt_path", "raw_output_path", "python_executable",
        "python_sha256", "preflight_script", "preflight_script_sha256",
        "exact_command", "raw_receipt_sha256", "receipt",
    }
    if set(bound) != required or bound.get("schema") != B1_BOUND_ADMISSION_SCHEMA:
        raise B1OrchestrationError("bound B1 admission schema differs")
    if (
        bound.get("attempt_id") != expected_attempt_id
        or bound.get("run_name") != B1_RUN_NAME
        or bound.get("arm") != expected_arm
        or bound.get("seed") != expected_seed
        or bound.get("implementation_commit") != expected_commit
    ):
        raise B1OrchestrationError("bound B1 admission invocation identity differs")
    executable = Path(sys.executable).resolve()
    if (
        bound.get("python_executable") != str(executable)
        or bound.get("python_sha256") != _digest(executable.read_bytes())
        or bound.get("preflight_script") != str(CANONICAL_PREFLIGHT)
        or bound.get("preflight_script_sha256") != _digest(CANONICAL_PREFLIGHT.read_bytes())
    ):
        raise B1OrchestrationError("bound B1 admission executable/script identity differs")
    bound_path = Path(str(bound.get("bound_receipt_path"))).resolve(strict=False)
    raw_path = Path(str(bound.get("raw_output_path"))).resolve(strict=False)
    command = bound.get("exact_command")
    if (
        not isinstance(command, list)
        or command != [
            str(executable), str(CANONICAL_PREFLIGHT), "admit-memory", "--out", str(raw_path)
        ]
        or raw_path.parent != bound_path.parent
        or not raw_path.name.startswith(f".{bound_path.name}.raw-")
    ):
        raise B1OrchestrationError("bound B1 admission exact command/path differs")
    for field in ("source_conformance_sha256", "raw_receipt_sha256"):
        digest = bound.get(field)
        if (
            type(digest) is not str or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise B1OrchestrationError(f"bound B1 admission {field} differs")
    bound["receipt"] = validate_memory_receipt(bound["receipt"])
    if expected_receipt_path is not None:
        if bound_path != expected_receipt_path.resolve(strict=False):
            raise B1OrchestrationError("bound B1 admission persisted path differs")
        if not raw_path.is_file() or _digest(raw_path.read_bytes()) != bound["raw_receipt_sha256"]:
            raise B1OrchestrationError("bound B1 raw admission bytes differ")
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise B1OrchestrationError("bound B1 raw admission is unreadable") from exc
        if validate_memory_receipt(raw) != bound["receipt"]:
            raise B1OrchestrationError("bound B1 parsed admission differs")
    return bound


def _admission_failure_detail(
    completed: "subprocess.CompletedProcess[str]",
) -> str:
    """Say why the admission was refused, using the preflight's own reasons.

    ``scripts/hmasd_resource_preflight.py`` returns 6 for two different things.
    A ``ValueError`` refusal prints to stderr, but the ordinary floor refusal
    writes the receipt, prints the payload to STDOUT and returns 6 with an empty
    stderr.  Reporting only stderr therefore produced "exit 6: " with no reason
    at all, while ``failure_reasons`` sat in the captured stdout - which is what
    happened to the fifth B1 attempt, refused for
    "available physical memory is below 4 GiB" without saying so.
    """

    detail = (completed.stderr or "").strip()
    reasons: object = None
    try:
        payload = json.loads(completed.stdout or "")
    except (json.JSONDecodeError, TypeError):
        payload = None
    if isinstance(payload, Mapping):
        reasons = payload.get("failure_reasons")
    if isinstance(reasons, (list, tuple)) and reasons:
        joined = "; ".join(str(reason) for reason in reasons)
        return f"{detail}: {joined}" if detail else joined
    return detail


def run_memory_preflight(
    receipt_path: Path, *, attempt_id: str, arm: str, seed: int,
    implementation_commit: str, source_conformance_sha256: str,
) -> dict[str, Any]:
    """Acquire one fresh canonical admission immediately before one child request."""

    if arm not in ARMS or seed not in B1_SEEDS or not attempt_id:
        raise B1OrchestrationError("B1 admission arm/seed/attempt differs")
    if receipt_path.exists():
        raise FileExistsError("create-only B1 bound admission receipt exists")
    executable = Path(sys.executable).resolve()
    raw_path = receipt_path.with_name(f".{receipt_path.name}.raw-{uuid.uuid4().hex}.json")
    command = [
        str(executable), str(CANONICAL_PREFLIGHT), "admit-memory", "--out", str(raw_path)
    ]
    completed = subprocess.run(command, capture_output=True, text=True, shell=False, timeout=120)
    if completed.returncode != 0:
        raise B1OrchestrationError(
            f"B1 memory admission failed with exit {completed.returncode}: "
            f"{_admission_failure_detail(completed)}"
        )
    try:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B1OrchestrationError("B1 memory admission receipt is unreadable") from exc
    receipt = validate_memory_receipt(raw)
    if (
        receipt["available_physical_bytes"] < MIN_AVAILABLE_BYTES
        or receipt["effective_available_bytes"] < MIN_AVAILABLE_BYTES
    ):
        raise B1OrchestrationError("B1 memory admission is below both required 4-GiB floors")
    bound = {
        "schema": B1_BOUND_ADMISSION_SCHEMA,
        "attempt_id": attempt_id,
        "run_name": B1_RUN_NAME,
        "arm": arm,
        "seed": seed,
        "implementation_commit": implementation_commit,
        "source_conformance_sha256": source_conformance_sha256,
        "bound_receipt_path": str(receipt_path.resolve(strict=False)),
        "raw_output_path": str(raw_path.resolve(strict=False)),
        "python_executable": str(executable),
        "python_sha256": _digest(executable.read_bytes()),
        "preflight_script": str(CANONICAL_PREFLIGHT),
        "preflight_script_sha256": _digest(CANONICAL_PREFLIGHT.read_bytes()),
        "exact_command": command,
        "raw_receipt_sha256": _digest(raw_path.read_bytes()),
        "receipt": receipt,
    }
    _atomic_create_json(receipt_path, bound)
    return validate_bound_admission(
        bound, expected_attempt_id=attempt_id, expected_arm=arm,
        expected_seed=seed, expected_commit=implementation_commit,
        expected_receipt_path=receipt_path,
    )


def _validate_invocation_slice(
    start_update: int, stop_update: int, resume_checkpoint: Path | None,
) -> None:
    if start_update not in B1_CHECKPOINT_UPDATES or stop_update not in B1_CHECKPOINT_UPDATES:
        raise B1OrchestrationError("worker slice endpoints are not exact B1 checkpoints")
    if stop_update <= start_update:
        raise B1OrchestrationError("worker slice endpoints differ from the B1 resume contract")
    if resume_checkpoint is None and start_update != 0:
        raise B1OrchestrationError("nonzero worker slice requires a resume checkpoint")
    if resume_checkpoint is not None and start_update not in (0, 12, 24):
        raise B1OrchestrationError("resume checkpoint start is not 0/12/24")


def _prepare_worker_invocation(
    *, staging: Path, attempt_id: str, order_index: int, arm: str, seed: int,
    implementation_commit: str, source_conformance_sha256: str,
    start_update: int = 0, stop_update: int = 48,
    resume_checkpoint: Path | None = None,
) -> tuple[list[str], Path, Path, Path, Path, Path, dict[str, Any]]:
    """Admit, bind, and serialize one canonical worker invocation.

    Directory/control preparation is result-blind.  The memory subprocess is
    intentionally the last operation before the strict worker request is
    serialized; RNG/model/optimizer construction occurs only inside that
    subsequently supervised worker.
    """

    if (seed, arm) not in ARM_SEED_ORDER:
        raise B1OrchestrationError("worker arm/seed is outside the fixed B1 order")
    if type(order_index) is not int or ARM_SEED_ORDER[order_index] != (seed, arm):
        raise B1OrchestrationError("worker invocation order differs from seed-major B1 order")
    _validate_invocation_slice(start_update, stop_update, resume_checkpoint)

    tag = _slot_tag(order_index, seed, arm)
    invocation = f"slice-{start_update:02d}-{stop_update:02d}"
    scratch = staging / "scratch" / tag / invocation
    durable = staging / "arm-seeds" / tag
    worker_root = staging / "workers" / tag / invocation
    admissions = staging / "admissions"
    for path in (scratch, worker_root):
        path.mkdir(parents=True, exist_ok=False)
    durable.mkdir(parents=True, exist_ok=True)
    admissions.mkdir(parents=True, exist_ok=True)
    bound_resume: Path | None = None
    if resume_checkpoint is not None:
        source_checkpoint = Path(resume_checkpoint).resolve(strict=True)
        bound_resume = durable / f"checkpoint-update-{start_update}.pt"
        if source_checkpoint != bound_resume.resolve(strict=False):
            if bound_resume.exists():
                raise FileExistsError("create-only copied resume checkpoint already exists")
            shutil.copyfile(source_checkpoint, bound_resume)
            if _digest(source_checkpoint.read_bytes()) != _digest(bound_resume.read_bytes()):
                raise B1OrchestrationError("copied resume checkpoint bytes differ")
        elif not bound_resume.is_file():
            raise B1OrchestrationError("in-transaction resume checkpoint is absent")
    receipt_path = admissions / f"{tag}-{invocation}-admission.json"
    run_memory_preflight(
        receipt_path, attempt_id=attempt_id, arm=arm, seed=seed,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
    )
    request = B1ArmSeedRequest(
        plan=B1Plan(), attempt_id=attempt_id, arm=arm, seed=seed,
        train_episode_ids=B1_TRAIN_EPISODE_IDS,
        checkpoint_updates=B1_CHECKPOINT_UPDATES,
        eval_stochastic_ids=B1_EVAL_STOCHASTIC_IDS,
        eval_motif_ids=B1_EVAL_MOTIF_IDS,
        scratch_root=scratch.resolve(strict=False),
        durable_root=durable.resolve(strict=False),
        admission_schema=B1_BOUND_ADMISSION_SCHEMA,
        admission_receipt_path=receipt_path.resolve(strict=False),
        admission_receipt_sha256=_digest(receipt_path.read_bytes()),
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        resource_caps=B1_RESOURCE_CAPS,
        scientific_branch=None,
    )
    from .b1_worker import encode_worker_request

    payload = encode_worker_request(
        request, attempt_root=staging, start_update=start_update,
        stop_update=stop_update, resume_checkpoint=bound_resume,
    )
    request_path = worker_root / "request.json"
    result_path = worker_root / "result.json"
    error_path = worker_root / "error.json"
    _atomic_create_json(request_path, payload)
    command = [
        str(Path(sys.executable).resolve()), "-m", CANONICAL_WORKER_MODULE,
        "--request", str(request_path), "--result", str(result_path),
        "--error", str(error_path),
    ]
    return command, request_path, result_path, error_path, scratch, durable, payload


def _kill_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, shell=False, timeout=10,
        )
    else:  # pragma: no cover - declared production host is Windows
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _unwrap_worker_result(value: object) -> dict[str, Any]:
    """Validate the exact worker wrapper and return only canonical raw evidence."""

    if not isinstance(value, Mapping) or set(value) != {
        "schema", "raw_evidence", "scientific_branch"
    }:
        raise B1OrchestrationError("canonical B1 worker result wrapper schema differs")
    if value["schema"] != WORKER_RESULT_SCHEMA or value["scientific_branch"] is not None:
        raise B1OrchestrationError("canonical B1 worker result identity/branch differs")
    raw = value["raw_evidence"]
    if not isinstance(raw, Mapping):
        raise B1OrchestrationError("canonical B1 raw evidence is absent")
    result = dict(raw)
    if (
        result.get("schema") != B1_RAW_EVIDENCE_SCHEMA
        or result.get("scientific_branch") is not None
    ):
        raise B1OrchestrationError("canonical B1 engine raw schema/branch differs")
    try:
        canonical_wrapper = wrap_worker_result(result)
    except ValueError as exc:
        raise B1OrchestrationError("canonical B1 worker wrapper validation failed") from exc
    if dict(value) != canonical_wrapper:
        raise B1OrchestrationError("canonical B1 worker wrapper differs from its codec")
    return result


def _validate_stage_measurements(value: object) -> tuple[int, list[dict[str, Any]]]:
    """Validate engine-measured stages and return their direct transition sum."""

    if not isinstance(value, list) or not value:
        raise B1OrchestrationError("B1 raw stage_measurements must be a nonempty list")
    records: list[dict[str, Any]] = []
    total = 0
    for index, stage in enumerate(value):
        if not isinstance(stage, Mapping):
            raise B1OrchestrationError(f"B1 stage_measurements[{index}] is not a record")
        record = dict(stage)
        if not isinstance(record.get("stage"), str) or not record["stage"].strip():
            raise B1OrchestrationError(f"B1 stage_measurements[{index}].stage is absent")
        for name in ("wall_seconds", "cpu_seconds", "transitions_per_second"):
            raw_number = record.get(name)
            if isinstance(raw_number, bool):
                raise B1OrchestrationError(f"B1 stage_measurements[{index}].{name} differs")
            try:
                number = float(raw_number)
            except (TypeError, ValueError) as exc:
                raise B1OrchestrationError(
                    f"B1 stage_measurements[{index}].{name} differs"
                ) from exc
            if not math.isfinite(number) or number <= 0:
                raise B1OrchestrationError(f"B1 stage_measurements[{index}].{name} differs")
        transitions = record.get("transitions")
        if type(transitions) is not int or transitions <= 0:
            raise B1OrchestrationError(
                f"B1 stage_measurements[{index}].transitions must be positive"
            )
        expected = transitions / float(record["wall_seconds"])
        if not math.isclose(
            float(record["transitions_per_second"]), expected,
            rel_tol=1e-9, abs_tol=1e-12,
        ):
            raise B1OrchestrationError(
                f"B1 stage_measurements[{index}] throughput differs from measured work/wall"
            )
        total += transitions
        records.append(record)
    if total <= 0:
        raise B1OrchestrationError("B1 raw stage work sum is zero")
    return total, records


def supervise_child(
    command: Sequence[str], *, scratch_root: Path, durable_root: Path,
    result_path: Path, stdout_path: Path, stderr_path: Path,
    caps: ResourceCaps = B1_RESOURCE_CAPS, interval_seconds: float = 0.05,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Supervise one canonical arm/seed child and kill its tree on a live cap."""

    supervisor_incident = result_path.with_name("supervisor-incident.json")
    if result_path.exists() or supervisor_incident.exists():
        raise FileExistsError("create-only B1 worker result already exists")
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(command), stdout=stdout, stderr=stderr, shell=False, cwd=REPO_ROOT
        )
        monitor = ProcessTreeMonitor(
            scratch_root, durable_root, worker_count=1, threads_per_worker=1,
            interval_seconds=interval_seconds, root_pid=process.pid,
        )
        try:
            monitor.begin()
        except BaseException as exc:
            if process.poll() is None:
                _kill_process_tree(process)
            try:
                snapshot = monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
            except BaseException:
                snapshot = {
                    "schema": "cbsc_omrc_b01_supervisor_incident_v1",
                    "measurement_complete": False,
                    "measurement_source": "telemetry_initialization_failed",
                    "reason": "TELEMETRY_FAILURE", "cap_failures": [],
                    "sample_interval_seconds": interval_seconds, "sample_count": 0,
                    "observed_wall_seconds": 0.0, "observed_cpu_seconds": 0.0,
                    "process_tree_peak_rss_bytes": 0, "peak_process_count": 0,
                    "peak_thread_count": 0, "io_read_bytes": 0, "io_write_bytes": 0,
                    "scratch_high_water_bytes": 0, "durable_high_water_bytes": 0,
                    "scientific_branch": None,
                }
            _atomic_create_json(supervisor_incident, snapshot)
            raise TelemetryError("process-tree telemetry failed during supervision") from exc
        failures: tuple[str, ...] = ()
        stopping: tuple[str, ...] = ()
        recorded_cap_failures: set[str] = set()
        try:
            while process.poll() is None:
                try:
                    failures = monitor.poll_caps(caps=caps)
                except BaseException as exc:
                    returncode = process.poll()
                    try:
                        snapshot = monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
                    except BaseException:
                        snapshot = {
                            "schema": "cbsc_omrc_b01_supervisor_incident_v1",
                            "measurement_complete": False,
                            "measurement_source": "telemetry_poll_failed",
                            "reason": "TELEMETRY_FAILURE", "cap_failures": [],
                            "sample_interval_seconds": interval_seconds, "sample_count": 0,
                            "observed_wall_seconds": 0.0, "observed_cpu_seconds": 0.0,
                            "process_tree_peak_rss_bytes": 0, "peak_process_count": 0,
                            "peak_thread_count": 0, "io_read_bytes": 0,
                            "io_write_bytes": 0, "scratch_high_water_bytes": 0,
                            "durable_high_water_bytes": 0, "scientific_branch": None,
                        }
                    if returncode == 0 and snapshot.get("sample_count", 0) >= 2:
                        break
                    if returncode is None:
                        _kill_process_tree(process)
                    _atomic_create_json(supervisor_incident, snapshot)
                    raise TelemetryError(
                        "process-tree telemetry failed during supervision"
                    ) from exc
                # Section-11 recast, owner decision 3 (2026-09-02): the RSS,
                # scratch and durable caps are recorded budgets, so a live
                # exceedance is observed and published rather than killing the
                # child.  Only the wall cap stops a run.
                recorded_cap_failures.update(failures)
                stopping = tuple(name for name in failures if name in STOPPING_CAPS)
                if stopping:
                    _kill_process_tree(process)
                    break
                time.sleep(interval_seconds)
        finally:
            if process.poll() is None:
                _kill_process_tree(process)
        if stopping:
            _atomic_create_json(
                supervisor_incident,
                monitor.incident_snapshot(
                    reason="LIVE_RESOURCE_CAP_TERMINATION", cap_failures=stopping
                ),
            )
            raise TelemetryError(f"live wall cap exceeded: {','.join(stopping)}")
        if process.returncode != 0:
            _atomic_create_json(
                supervisor_incident,
                monitor.incident_snapshot(reason=f"WORKER_EXIT_{process.returncode}"),
            )
            raise B1OrchestrationError(f"canonical B1 worker exited {process.returncode}")
        if not result_path.is_file():
            _atomic_create_json(
                supervisor_incident, monitor.incident_snapshot(reason="WORKER_RESULT_ABSENT")
            )
            raise B1OrchestrationError("canonical B1 worker produced no create-only result")
        try:
            wrapper = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _atomic_create_json(
                supervisor_incident, monitor.incident_snapshot(reason="WORKER_RESULT_UNREADABLE")
            )
            raise B1OrchestrationError("canonical B1 worker result is unreadable") from exc
        try:
            raw = _unwrap_worker_result(wrapper)
            scientific_work, stages = _validate_stage_measurements(
                raw.get("stage_measurements")
            )
            declared_work = raw.get("scientific_work_transitions")
            if type(declared_work) is not int or declared_work != scientific_work:
                raise B1OrchestrationError(
                    "B1 raw scientific_work_transitions differs from measured stage sum"
                )
        except B1OrchestrationError:
            _atomic_create_json(
                supervisor_incident,
                monitor.incident_snapshot(reason="WORKER_RESULT_SCHEMA_INVALID"),
            )
            raise
        telemetry = monitor.finish(
            scientific_work_transitions=scientific_work,
            stage_measurements=stages,
        )
        if recorded_cap_failures:
            _atomic_create_json(
                supervisor_incident,
                monitor.incident_snapshot(
                    reason="LIVE_RESOURCE_CAP_RECORDED",
                    cap_failures=tuple(sorted(recorded_cap_failures)),
                ),
            )
    # Recorded budgets: the caps are published by `assess_resource_telemetry`
    # at the slot boundary, so the completeness validation here is uncapped.
    return raw, validate_telemetry(telemetry, caps=RECORDED_BUDGET_CAPS)


def supervise_policy_replay_child(
    command: Sequence[str], *, result_path: Path, scratch_root: Path,
    durable_root: Path, stdout_path: Path, stderr_path: Path,
    test_only: bool = False, caps: ResourceCaps = B1_RESOURCE_CAPS,
    interval_seconds: float = 0.05,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Supervise one fixed replay child and derive work only from validated row counts."""

    incident_path = result_path.with_name("supervisor-incident.json")
    if any(path.exists() for path in (result_path, stdout_path, stderr_path, incident_path)):
        raise FileExistsError("create-only policy replay output already exists")
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(command), stdout=stdout, stderr=stderr, shell=False, cwd=REPO_ROOT
        )
        monitor = ProcessTreeMonitor(
            scratch_root, durable_root, worker_count=1, threads_per_worker=1,
            interval_seconds=interval_seconds, root_pid=process.pid,
        )
        try:
            monitor.begin()
        except BaseException as exc:
            if process.poll() is None:
                _kill_process_tree(process)
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
            )
            raise TelemetryError("policy replay telemetry failed") from exc
        failures: tuple[str, ...] = ()
        try:
            while process.poll() is None:
                try:
                    failures = monitor.poll_caps(caps=caps)
                except BaseException as exc:
                    returncode = process.poll()
                    snapshot = monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
                    if returncode == 0 and snapshot.get("sample_count", 0) >= 2:
                        break
                    if returncode is None:
                        _kill_process_tree(process)
                    _atomic_create_json(incident_path, snapshot)
                    raise TelemetryError("policy replay telemetry failed") from exc
                if failures:
                    _kill_process_tree(process)
                    break
                time.sleep(interval_seconds)
        except TelemetryError:
            raise
        except BaseException as exc:
            if process.poll() is None:
                _kill_process_tree(process)
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
            )
            raise TelemetryError("policy replay telemetry failed") from exc
        finally:
            if process.poll() is None:
                _kill_process_tree(process)
        if failures:
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(
                    reason="LIVE_RESOURCE_CAP_TERMINATION", cap_failures=failures
                ),
            )
            raise TelemetryError(f"policy replay resource cap exceeded: {','.join(failures)}")
        if process.returncode != 0 or not result_path.is_file():
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(
                    reason=(f"WORKER_EXIT_{process.returncode}"
                            if process.returncode != 0 else "WORKER_RESULT_ABSENT")
                ),
            )
            raise B1OrchestrationError("canonical policy replay child failed")
        try:
            payload = result_path.read_bytes()
            wrapper = json.loads(payload.decode("ascii"))
            if canonical_json_bytes(wrapper) + b"\n" != payload:
                raise B1OrchestrationError(
                    "policy replay result is not canonical create-only JSON"
                )
            counts = wrapper.get("counts")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, B1OrchestrationError) as exc:
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="WORKER_RESULT_UNREADABLE")
            )
            raise B1OrchestrationError("policy replay result is unreadable") from exc
        # These are the assembly module's own per-slot counts, imported rather
        # than restated.  The formal branch previously hardcoded
        # "evaluation_join_records": 128 against a canonical value of 4, so no
        # conformant formal run could pass; the test-only branch already carried
        # the correct 4, which is why the test-only integration profile never
        # exercised the wrong constant.
        expected = {
            "policy_decisions": (
                192 if test_only else ONE_SLOT_FORMAL_POLICY_DECISION_COUNT
            ),
            "policy_curves": 2 if test_only else ONE_SLOT_FORMAL_POLICY_CURVE_COUNT,
            "execution_mode_records": ONE_SLOT_EXECUTION_MODE_RECORD_COUNT,
            "evaluation_join_records": ONE_SLOT_EVALUATION_JOIN_RECORD_COUNT,
        }
        if counts != expected or any(wrapper.get(name) is not None for name in (
            "scientific_branch", "scientific_polarity", "promotion_eligible",
            "b2_extension_trigger",
        )) or any(len(wrapper.get(field, ())) != expected[field] for field in expected):
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="WORKER_RESULT_SCHEMA_INVALID")
            )
            raise B1OrchestrationError("policy replay result counts/nulls differ")
        work_units = expected["policy_decisions"]
        measurement = monitor.finish(
            scientific_work_transitions=work_units,
            stage_measurements=[{
                "stage": "policy-replay-model-forward-units", "wall_seconds": 1.0,
                "cpu_seconds": 1.0, "transitions": work_units,
                "transitions_per_second": float(work_units),
            }],
        )
        wall = measurement["end_to_end_wall_seconds"]
        cpu = measurement["end_to_end_cpu_seconds"]
        if not (wall > 0 and cpu > 0):
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
            )
            raise TelemetryError("policy replay direct wall/CPU measurement is incomplete")
        measurement["stage_measurements"] = [{
            "stage": "policy-replay-model-forward-units", "wall_seconds": wall,
            "cpu_seconds": cpu, "transitions": work_units,
            "transitions_per_second": work_units / wall,
        }]
    try:
        return wrapper, validate_telemetry(measurement, caps=caps)
    except TelemetryError:
        if not incident_path.exists():
            _atomic_create_json(
                incident_path, monitor.incident_snapshot(reason="TELEMETRY_FAILURE")
            )
        raise


def run_assess_preflight(receipt_path: Path) -> dict[str, Any]:
    """Run result-blind B1 sizing; this cannot authorize B1."""

    output = ensure_confined(Path(receipt_path), CONFINED_ROOT)
    if output.exists():
        raise FileExistsError(f"create-only assess-run receipt exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(Path(sys.executable).resolve()), str(CANONICAL_PREFLIGHT), "assess-run",
        "--direction", DIRECTION_ID,
        "--run-id", "cbsc_omrc_b1_three_seed_scout",
        "--workers", str(LiteralB1ArmSeedEngine.worker_count),
        "--threads-per-worker", str(LiteralB1ArmSeedEngine.threads_per_worker),
        "--estimated-wall-seconds", str(int(B1_RESOURCE_CAPS.wall_seconds)),
        "--estimated-peak-gib", str(
            B1_RESOURCE_CAPS.process_tree_peak_rss_bytes // 1024**3
        ),
        "--basis", "frozen B1 per-arm-seed cap; result-blind readiness only",
        "--out", str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, shell=False, timeout=120)
    try:
        receipt = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B1OrchestrationError("B1 assess-run receipt is unreadable") from exc
    receipt["command_returncode"] = completed.returncode
    receipt["formal_analysis_bound"] = FORMAL_ANALYSIS_BOUND
    receipt["decision"] = DECISION
    receipt["scientific_branch"] = None
    receipt["performance_disposition"] = "PILOT_ONLY"
    return receipt


def validate_resume_incident(
    incident_root: Path, *, expected_commit: str, expected_source_sha256: str,
    expected_laws_sha256: str, expected_b0_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Load one incident-referenced canonical whole-attempt ledger read-only."""

    root = ensure_confined(Path(incident_root), CONFINED_ROOT)
    incident_path = root / "incident.json"
    try:
        from .b1_artifact import load_b1_attempt_ledger_from_incident

        incident_bytes = incident_path.read_bytes()
        ledger = load_b1_attempt_ledger_from_incident(
            incident_path, allowed_root=CONFINED_ROOT
        )
        if incident_path.read_bytes() != incident_bytes:
            raise B1OrchestrationError(
                "canonical B1 incident changed during validation"
            )
    except (OSError, TypeError, ValueError) as exc:
        raise B1OrchestrationError("canonical B1 incident ledger is invalid") from exc
    binding = ledger.binding
    if (
        binding.implementation_commit != expected_commit
        or binding.source_conformance_sha256 != expected_source_sha256
        or binding.configuration_sha256 != _digest(canonical_json_bytes(B1Plan().as_dict()))
        or binding.laws_sha256 != expected_laws_sha256
        or binding.b0_manifest_sha256 != expected_b0_evidence.get("manifest_sha256")
        or binding.b0_manifest_bytes != expected_b0_evidence.get("manifest_bytes")
        or binding.b0_reviewed_receipt_sha256
        != expected_b0_evidence.get("reviewed_receipt_sha256")
        or binding.b0_inventory_sha256 != expected_b0_evidence.get("inventory_sha256")
        or binding.b0_file_count != expected_b0_evidence.get("file_count")
        or binding.b0_total_bytes != expected_b0_evidence.get("total_bytes")
    ):
        raise B1OrchestrationError(
            "canonical B1 incident ledger source/config/laws/B0 binding differs"
        )
    try:
        incident = json.loads(incident_bytes.decode("ascii"))
        ledger_reference = incident["attempt_ledger"]
        attempt_ledger_sha256 = ledger_reference["sha256"]
        ancestor_references = incident["incident_references"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise B1OrchestrationError("canonical B1 incident lineage is invalid") from exc
    expected_binding = binding.as_dict()
    expected_ledger_sha256 = _digest(canonical_json_bytes(ledger.as_dict()) + b"\n")
    if (
        incident.get("attempt_id") != binding.attempt_id
        or incident.get("attempt_binding") != expected_binding
        or not isinstance(ledger_reference, Mapping)
        or ledger_reference.get("binding") != expected_binding
        or attempt_ledger_sha256 != expected_ledger_sha256
    ):
        raise B1OrchestrationError(
            "canonical B1 incident snapshot ledger reference differs"
        )
    current_reference = {
        "attempt_id": binding.attempt_id,
        "incident_manifest_sha256": _digest(incident_bytes),
        "attempt_ledger_sha256": attempt_ledger_sha256,
        "incident_relative_path": incident_path.relative_to(CONFINED_ROOT).as_posix(),
    }
    try:
        lineage_witness = make_b1_incident_lineage_witness(
            [*ancestor_references, current_reference], allowed_root=CONFINED_ROOT,
            expected_binding=binding,
        )
    except (OSError, TypeError, ValueError) as exc:
        raise B1OrchestrationError("canonical B1 incident ancestor lineage is invalid") from exc
    resumable = [slot for slot in ledger.slots if slot.status.value != "COMPLETE"]
    slot = resumable[0] if resumable else None
    return {
        "incident_root": str(root), "ledger": ledger, "resume_slot": slot,
        "resume_checkpoint": None if slot is None else slot.resume_checkpoint,
        "laws_sha256": binding.laws_sha256,
        "lineage_witness": lineage_witness,
    }


def _law_digests(source_receipt: Mapping[str, Any]) -> dict[str, str]:
    files = source_receipt.get("files")
    if not isinstance(files, list):
        raise B1OrchestrationError("source receipt file inventory is absent")
    indexed = {
        record["path"]: record["sha256"]
        for record in files
        if isinstance(record, Mapping) and set(record) == {"path", "sha256"}
    }
    groups = {
        "environment": (
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/addressing.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/host.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ledger.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/tapes.py",
        ),
        "adapter": (
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/state.py",
        ),
        "token": (
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/contract.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/token.py",
        ),
        "analysis": (
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_shared_tables.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_policy_records.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_training_records.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_mechanical.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_artifact.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_rehydrate.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_policy_assembly.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_training_assembly.py",
            "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_production.py",
            "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md",
        ),
    }
    result: dict[str, str] = {}
    for name, paths in groups.items():
        if any(path not in indexed for path in paths):
            raise B1OrchestrationError(f"canonical {name} law source is absent")
        result[name] = _digest(canonical_json_bytes([
            {"path": path, "sha256": indexed[path]} for path in paths
        ]))
    return result


def _slot_tag(index: int, seed: int, arm: str) -> str:
    return f"{index:02d}-seed-{seed}-{arm}"


def _slot_file_digest(staging: Path, index: int, seed: int, arm: str) -> str:
    tag = _slot_tag(index, seed, arm)
    roots = [
        staging / "arm-seeds" / tag,
        staging / "workers" / tag,
    ]
    admissions_root = staging / "admissions"
    paths = (
        [
            path for path in admissions_root.iterdir()
            if path.is_file() and (
                path.name.startswith(f"{tag}-")
                or path.name.startswith(f".{tag}-")
            )
        ]
        if admissions_root.is_dir() else []
    )
    for root in roots:
        if root.is_dir():
            paths.extend(path for path in root.rglob("*") if path.is_file())
    records = [
        {"path": path.relative_to(staging).as_posix(), "sha256": _digest(path.read_bytes())}
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]
    return _digest(canonical_json_bytes(records))


def _inventory_digest(root: Path, paths: Sequence[Path]) -> str:
    return _digest(canonical_json_bytes([
        {"path": path.relative_to(root).as_posix(), "sha256": _digest(path.read_bytes())}
        for path in sorted(paths, key=lambda item: item.as_posix())
    ]))


def _slot_paths(root: Path, index: int, seed: int, arm: str) -> dict[str, list[Path]]:
    tag = _slot_tag(index, seed, arm)
    worker = root / "workers" / tag
    admissions_root = root / "admissions"
    results = sorted(worker.glob("slice-*/result.json")) if worker.is_dir() else []
    telemetry = sorted(worker.glob("slice-*/telemetry.json")) if worker.is_dir() else []
    admissions = (
        sorted(
            path for path in admissions_root.iterdir()
            if path.is_file() and path.name.startswith(f"{tag}-")
            and path.name.endswith("-admission.json")
        )
        if admissions_root.is_dir() else []
    )
    return {"raw": results, "admission": admissions, "telemetry": telemetry}


def _load_slot_evidence(
    root: Path, index: int, seed: int, arm: str,
    *, expected_attempt_id: str, expected_commit: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, str]]:
    paths = _slot_paths(root, index, seed, arm)
    if not paths["raw"] or len(paths["telemetry"]) > len(paths["raw"]):
        # A telemetry file per invocation is expected; fewer is a resource
        # measurement gap, which decision 7 downgrades below rather than
        # refusing here.  More than one per invocation is an inventory defect.
        raise B1OrchestrationError("slot raw/telemetry invocation inventory differs")
    if len(paths["raw"]) != len(paths["admission"]):
        raise B1OrchestrationError("slot raw/admission invocation inventory differs")
    raw_slices: list[dict[str, Any]] = []
    telemetry_values: list[dict[str, Any]] = []
    for path in paths["raw"]:
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise B1OrchestrationError("slot worker result is unreadable") from exc
        raw = _unwrap_worker_result(wrapper)
        if (
            raw.get("attempt_id") != expected_attempt_id
            or raw.get("seed") != seed or raw.get("arm") != arm
            or raw.get("full_bindings", {}).get("implementation_commit") != expected_commit
        ):
            raise B1OrchestrationError("slot raw attempt/arm/seed/commit binding differs")
        raw_slices.append(raw)
    # Section-11 recast, owner decision 7 (2026-09-02): missing or failed
    # resource telemetry downgrades to `resources_unmeasured` with reasons and
    # never annuls or quarantines; a measured cap exceedance is recorded, and
    # only the wall cap stops the run.  Learner-side instrumentation failure
    # (an absent or unreadable worker result, above) still quarantines.
    resource_assessments: list[dict[str, Any]] = []
    for path in paths["telemetry"]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            assessment = assess_resource_telemetry(None, caps=B1_RESOURCE_CAPS)
            assessment["unmeasured_reasons"] = [f"telemetry_unreadable: {exc}"]
        else:
            assessment = assess_resource_telemetry(value, caps=B1_RESOURCE_CAPS)
        resource_assessments.append(assessment)
        if assessment["stop_run"]:
            raise TelemetryError(
                "B1 wall cap exceeded: "
                + ",".join(assessment["stopping_cap_exceedances"])
            )
        if assessment["measurement"] is not None:
            telemetry_values.append(assessment["measurement"])
    for _ in range(len(paths["raw"]) - len(paths["telemetry"])):
        resource_assessments.append(
            assess_resource_telemetry(None, caps=B1_RESOURCE_CAPS)
        )
    for path in paths["admission"]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            validate_bound_admission(
                value, expected_attempt_id=expected_attempt_id,
                expected_arm=arm, expected_seed=seed, expected_commit=expected_commit,
            )
        except (OSError, json.JSONDecodeError, B1OrchestrationError) as exc:
            raise B1OrchestrationError("slot admission is invalid") from exc
    admission_record = {
        "arm": arm, "seed": seed, "admitted": True,
        "invocations": [
            {"path": path.relative_to(root).as_posix(), "sha256": _digest(path.read_bytes())}
            for path in paths["admission"]
        ],
    }
    unmeasured_reasons = [
        reason
        for assessment in resource_assessments
        for reason in assessment["unmeasured_reasons"]
    ]
    cap_exceedances = sorted({
        name
        for assessment in resource_assessments
        for name in assessment["cap_exceedances"]
    })
    telemetry_record = {
        "arm": arm, "seed": seed,
        "within_caps": not cap_exceedances,
        "resources_unmeasured": bool(unmeasured_reasons),
        "unmeasured_reasons": unmeasured_reasons,
        "recorded_cap_exceedances": cap_exceedances,
        "process_tree_peak_rss_bytes": max(
            (value["process_tree_peak_rss_bytes"] for value in telemetry_values),
            default=0,
        ),
        "scratch_high_water_bytes": max(
            (value["scratch_high_water_bytes"] for value in telemetry_values),
            default=0,
        ),
        "durable_high_water_bytes": max(
            (value["durable_high_water_bytes"] for value in telemetry_values),
            default=0,
        ),
        "wall_seconds": sum(
            value["end_to_end_wall_seconds"] for value in telemetry_values
        ),
        "invocations": telemetry_values,
    }
    digests = {
        "raw_result_sha256": _inventory_digest(root, paths["raw"]),
        "admission_sha256": _inventory_digest(root, paths["admission"]),
        "telemetry_sha256": _inventory_digest(root, paths["telemetry"]),
        "files_sha256": _slot_file_digest(root, index, seed, arm),
    }
    return raw_slices, admission_record, telemetry_record, digests


def _validate_slot_checkpoint_files(
    root: Path, index: int, seed: int, arm: str,
    raw_slices: Sequence[Mapping[str, Any]], *, attempt_id: str,
    implementation_commit: str, source_conformance_sha256: str,
) -> None:
    durable = root / "arm-seeds" / _slot_tag(index, seed, arm)
    observed: set[int] = set()
    for raw in raw_slices:
        checkpoints = raw.get("checkpoints_created")
        if not isinstance(checkpoints, list):
            raise B1OrchestrationError("slot checkpoint raw inventory is absent")
        for record in checkpoints:
            if not isinstance(record, Mapping):
                raise B1OrchestrationError("slot checkpoint raw record differs")
            update = record.get("update")
            path = durable / str(record.get("relative_path"))
            if update in observed or update not in B1_CHECKPOINT_UPDATES or not path.is_file():
                raise B1OrchestrationError("slot checkpoint file coverage differs")
            payload = path.read_bytes()
            byte_count = record.get("byte_count")
            if type(byte_count) is not int or byte_count <= 0 or len(payload) != byte_count:
                raise B1OrchestrationError("slot checkpoint byte_count differs from file bytes")
            if _digest(payload) != record.get("sha256"):
                raise B1OrchestrationError("slot checkpoint file SHA differs")
            envelope = load_b1_checkpoint(path)
            binding = envelope["binding"]
            inner = envelope["recurrent_ppo_checkpoint"]
            if (
                binding["attempt_id"] != attempt_id
                or binding["run_name"] != B1_RUN_NAME
                or binding["seed"] != seed or binding["arm"] != arm
                or binding["completed_rollout_updates"] != update
                or binding["implementation_commit"] != implementation_commit
                or binding["source_conformance_sha256"] != source_conformance_sha256
                or inner["minibatch_order_chain"] != record["digests"]["minibatch_order"]
            ):
                raise B1OrchestrationError("slot checkpoint envelope/order-chain differs")
            observed.add(update)
    if observed != set(B1_CHECKPOINT_UPDATES):
        raise B1OrchestrationError("complete slot does not preserve four checkpoint files")


def _copy_complete_slot(
    *, incident_root: Path, staging: Path, slot: B1SlotLedgerEntry,
    implementation_commit: str, source_conformance_sha256: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, str]]:
    index, seed, arm = slot.slot_index, slot.seed, slot.arm
    raw, admission, telemetry, digests = _load_slot_evidence(
        incident_root, index, seed, arm,
        expected_attempt_id=slot.binding.attempt_id,
        expected_commit=implementation_commit,
    )
    expected = {
        "raw_result_sha256": slot.raw_result_sha256,
        "admission_sha256": slot.admission_sha256,
        "telemetry_sha256": slot.telemetry_sha256,
        "files_sha256": slot.files_sha256,
    }
    if digests != expected:
        raise B1OrchestrationError("complete incident slot ledger/file digests differ")
    _validate_slot_checkpoint_files(
        incident_root, index, seed, arm, raw,
        attempt_id=slot.binding.attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
    )
    tag = _slot_tag(index, seed, arm)
    for relative in (Path("arm-seeds") / tag, Path("workers") / tag):
        source = incident_root / relative
        destination = staging / relative
        if not source.is_dir() or destination.exists():
            raise B1OrchestrationError("complete incident slot tree copy boundary differs")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, copy_function=shutil.copyfile)
    source_admissions = incident_root / "admissions"
    destination_admissions = staging / "admissions"
    destination_admissions.mkdir(parents=True, exist_ok=True)
    for source in source_admissions.iterdir():
        if source.is_file() and (
            source.name.startswith(f"{tag}-") or source.name.startswith(f".{tag}-")
        ):
            destination = destination_admissions / source.name
            if destination.exists():
                raise FileExistsError("create-only copied admission already exists")
            shutil.copyfile(source, destination)
    copied = _load_slot_evidence(
        staging, index, seed, arm,
        expected_attempt_id=slot.binding.attempt_id,
        expected_commit=implementation_commit,
    )
    if copied[3] != expected:
        raise B1OrchestrationError("copied complete slot bytes differ from ledger")
    return copied


def _copy_incomplete_prefix(
    *, incident_root: Path, staging: Path, slot: B1SlotLedgerEntry,
    implementation_commit: str, source_conformance_sha256: str,
) -> tuple[int, Path | None]:
    index, seed, arm = slot.slot_index, slot.seed, slot.arm
    if _slot_file_digest(incident_root, index, seed, arm) != slot.incident_sha256:
        raise B1OrchestrationError("incomplete incident slot file inventory SHA differs")
    resume = slot.resume_checkpoint
    if resume is None:
        return 0, None
    checkpoint_source = ensure_confined(
        incident_root / Path(resume.checkpoint_relative_path), incident_root
    )
    if not checkpoint_source.is_file() or _digest(checkpoint_source.read_bytes()) != resume.checkpoint_sha256:
        raise B1OrchestrationError("incident resume checkpoint bytes differ from ledger")
    envelope = load_b1_checkpoint(checkpoint_source)
    binding = envelope["binding"]
    inner = envelope["recurrent_ppo_checkpoint"]
    if (
        binding["attempt_id"] != slot.binding.attempt_id
        or binding["run_name"] != B1_RUN_NAME
        or binding["seed"] != seed or binding["arm"] != arm
        or binding["completed_rollout_updates"] != resume.completed_rollout_updates
        or binding["implementation_commit"] != implementation_commit
        or binding["source_conformance_sha256"] != source_conformance_sha256
        or inner["minibatch_order_chain"] != resume.order_chain_sha256
    ):
        raise B1OrchestrationError("incident resume checkpoint envelope/order-chain differs")
    tag = _slot_tag(index, seed, arm)
    worker_source = incident_root / "workers" / tag
    worker_destination = staging / "workers" / tag
    worker_destination.mkdir(parents=True, exist_ok=True)
    completed_invocations: list[str] = []
    for result_path in sorted(worker_source.glob("slice-*/result.json")):
        raw = _unwrap_worker_result(json.loads(result_path.read_text(encoding="utf-8")))
        stop = raw.get("slice", {}).get("stop_update")
        if type(stop) is int and stop <= resume.completed_rollout_updates:
            invocation = result_path.parent.name
            destination = worker_destination / invocation
            if destination.exists():
                raise FileExistsError("create-only prior slice copy already exists")
            shutil.copytree(result_path.parent, destination, copy_function=shutil.copyfile)
            completed_invocations.append(invocation)
    if not completed_invocations and resume.completed_rollout_updates != 0:
        raise B1OrchestrationError("resume checkpoint has no completed raw slice provenance")
    admissions_source = incident_root / "admissions"
    admissions_destination = staging / "admissions"
    admissions_destination.mkdir(parents=True, exist_ok=True)
    for invocation in completed_invocations:
        prefix = f"{tag}-{invocation}-"
        matches = [
            path for path in admissions_source.iterdir()
            if path.is_file() and (
                path.name.startswith(prefix) or path.name.startswith(f".{prefix}")
            )
        ]
        if not matches:
            raise B1OrchestrationError("completed prior slice admission provenance is absent")
        for source in matches:
            destination = admissions_destination / source.name
            if destination.exists():
                raise FileExistsError("create-only prior admission copy already exists")
            shutil.copyfile(source, destination)
    durable_destination = staging / "arm-seeds" / tag
    durable_destination.mkdir(parents=True, exist_ok=True)
    durable_source = incident_root / "arm-seeds" / tag
    for update in B1_CHECKPOINT_UPDATES:
        if update >= resume.completed_rollout_updates:
            break
        source = durable_source / f"checkpoint-update-{update}.pt"
        destination = durable_destination / source.name
        if not source.is_file() or destination.exists():
            raise B1OrchestrationError("prior checkpoint prefix copy boundary differs")
        shutil.copyfile(source, destination)
    return resume.completed_rollout_updates, checkpoint_source


def _attempt_binding(
    *, attempt_id: str, implementation_commit: str,
    source_receipt: Mapping[str, Any], laws: Mapping[str, str],
    b0_evidence: Mapping[str, Any],
) -> B1LedgerBinding:
    plan = B1Plan()
    return B1LedgerBinding(
        attempt_id=attempt_id,
        run_name=B1_RUN_NAME,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_receipt["source_conformance_sha256"],
        configuration_sha256=_digest(canonical_json_bytes(plan.as_dict())),
        laws_sha256=_digest(canonical_json_bytes(dict(laws))),
        b0_manifest_sha256=b0_evidence["manifest_sha256"],
        b0_manifest_bytes=b0_evidence["manifest_bytes"],
        b0_reviewed_receipt_sha256=b0_evidence["reviewed_receipt_sha256"],
        b0_inventory_sha256=b0_evidence["inventory_sha256"],
        b0_file_count=b0_evidence["file_count"],
        b0_total_bytes=b0_evidence["total_bytes"],
        object_id=plan.object_id,
        innovator_selection_request_id=plan.innovator_selection_request_id,
        innovator_selection_archive_path=plan.innovator_selection_archive_path,
        innovator_selection_response_sha256=plan.innovator_selection_response_sha256,
        literal_binding_request_id=plan.literal_binding_request_id,
        literal_binding_archive_path=plan.literal_binding_archive_path,
        literal_binding_response_sha256=plan.literal_binding_response_sha256,
        metrics_only_request_id=plan.metrics_only_request_id,
        metrics_only_archive_path=plan.metrics_only_archive_path,
        metrics_only_response_sha256=plan.metrics_only_response_sha256,
    )


def _resume_checkpoint_binding(
    *, staging: Path, binding: B1LedgerBinding, slot_index: int,
    seed: int, arm: str,
) -> B1ResumeCheckpointBinding | None:
    tag = _slot_tag(slot_index, seed, arm)
    durable = staging / "arm-seeds" / tag
    completed_stops: list[int] = []
    for result_path in _slot_paths(staging, slot_index, seed, arm)["raw"]:
        try:
            raw = _unwrap_worker_result(json.loads(result_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, B1OrchestrationError):
            continue
        stop = raw.get("slice", {}).get("stop_update")
        if stop in (12, 24):
            completed_stops.append(stop)
    supported = set(completed_stops)
    for update in (24, 12, 0):
        if update != 0 and update not in supported:
            continue
        path = durable / f"checkpoint-update-{update}.pt"
        if not path.is_file():
            continue
        try:
            payload = path.read_bytes()
            envelope = load_b1_checkpoint(path)
            checkpoint_binding = envelope["binding"]
            if (
                checkpoint_binding["attempt_id"] != binding.attempt_id
                or checkpoint_binding["run_name"] != B1_RUN_NAME
                or checkpoint_binding["implementation_commit"]
                != binding.implementation_commit
                or checkpoint_binding["source_conformance_sha256"]
                != binding.source_conformance_sha256
                or checkpoint_binding["seed"] != seed
                or checkpoint_binding["arm"] != arm
                or checkpoint_binding["completed_rollout_updates"] != update
            ):
                continue
            order_chain = envelope["recurrent_ppo_checkpoint"][
                "minibatch_order_chain"
            ]
            return B1ResumeCheckpointBinding(
                binding=binding, slot_index=slot_index, seed=seed, arm=arm,
                completed_rollout_updates=update,
                checkpoint_relative_path=path.relative_to(staging).as_posix(),
                checkpoint_sha256=_digest(payload),
                order_chain_sha256=order_chain,
            )
        except Exception:
            continue
    return None


def _publish_attempt_incident(
    *, staging: Path, final_path: Path, attempt_id: str,
    implementation_commit: str, source_receipt: Mapping[str, Any],
    laws: Mapping[str, str], completed: Sequence[dict[str, Any]],
    b0_evidence: Mapping[str, Any], failed_index: int | None, exc: BaseException,
    incident_lineage_witness: B1IncidentLineageWitness | None = None,
) -> Path:
    binding = _attempt_binding(
        attempt_id=attempt_id, implementation_commit=implementation_commit,
        source_receipt=source_receipt, laws=laws, b0_evidence=b0_evidence,
    )
    control = staging / "orchestrator-incident.json"
    if not control.exists():
        _atomic_create_json(control, {
            "schema": "cbsc_omrc_b01_b1_orchestrator_incident_v1",
            "attempt_id": attempt_id, "exception_type": type(exc).__name__,
            "detail": str(exc), "decision": DECISION, "scientific_branch": None,
        })
    completed_by_index = {record["slot_index"]: record for record in completed}
    slots: list[B1SlotLedgerEntry] = []
    for index, (seed, arm) in enumerate(ARM_SEED_ORDER):
        if index in completed_by_index:
            record = completed_by_index[index]
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.COMPLETE,
                raw_result_sha256=record["raw_result_sha256"],
                admission_sha256=record["admission_sha256"],
                telemetry_sha256=record["telemetry_sha256"],
                files_sha256=record["files_sha256"],
            ))
        elif failed_index is not None and index == failed_index:
            incident_sha = _slot_file_digest(staging, index, seed, arm)
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.INCOMPLETE, incident_sha256=incident_sha,
                resume_checkpoint=_resume_checkpoint_binding(
                    staging=staging, binding=binding, slot_index=index,
                    seed=seed, arm=arm,
                ),
            ))
        else:
            slots.append(B1SlotLedgerEntry(
                binding=binding, slot_index=index, seed=seed, arm=arm,
                status=B1SlotStatus.PENDING,
            ))
    ledger = B1AttemptLedger(
        schema=B1_LEDGER_SCHEMA, publication_mode=B1_LEDGER_PUBLICATION_MODE,
        binding=binding, slots=tuple(slots),
    )
    return publish_b1_incident(
        staging=staging, incident_root=final_path.parent / "incidents",
        allowed_root=CONFINED_ROOT, attempt_id=attempt_id,
        category="B1_ENGINEERING_ATTEMPT_INCOMPLETE",
        detail=f"{type(exc).__name__}: {exc}",
        completed_arm_seeds=[(record["arm"], record["seed"]) for record in completed],
        attempt_ledger=ledger,
        incident_lineage_witness=incident_lineage_witness,
    )


def _validate_raw_slice_sequence(
    raw_slices: Sequence[Mapping[str, Any]],
) -> list[list[Mapping[str, Any]]]:
    """Reduce a flat slice stream into 12 strict contiguous seed-major slot runs."""

    if not isinstance(raw_slices, Sequence) or isinstance(
        raw_slices, (str, bytes, bytearray)
    ):
        raise B1OrchestrationError("raw slice stream must be a sequence")
    cursor = 0
    groups: list[list[Mapping[str, Any]]] = []
    for seed, arm in ARM_SEED_ORDER:
        expected_start = 0
        group: list[Mapping[str, Any]] = []
        while cursor < len(raw_slices):
            raw = raw_slices[cursor]
            if not isinstance(raw, Mapping):
                raise B1OrchestrationError("raw slice stream contains a non-record")
            identity = (raw.get("seed"), raw.get("arm"))
            if identity != (seed, arm):
                break
            if (
                raw.get("schema") != B1_RAW_EVIDENCE_SCHEMA
                or raw.get("run_name") != B1_RUN_NAME
                or raw.get("scientific_branch") is not None
            ):
                raise B1OrchestrationError("raw slice run identity/schema differs")
            interval = raw.get("slice")
            if not isinstance(interval, Mapping) or set(interval) != {
                "start_update", "stop_update"
            }:
                raise B1OrchestrationError("raw slice interval schema differs")
            start = interval["start_update"]
            stop = interval["stop_update"]
            if (
                type(start) is not int or type(stop) is not int
                or start not in B1_CHECKPOINT_UPDATES
                or stop not in B1_CHECKPOINT_UPDATES
                or start != expected_start or stop <= start
            ):
                raise B1OrchestrationError(
                    "raw slice intervals contain a gap, overlap, duplicate, or illegal boundary"
                )
            group.append(raw)
            cursor += 1
            expected_start = stop
            if stop == B1_CHECKPOINT_UPDATES[-1]:
                break
        if not group or expected_start != B1_CHECKPOINT_UPDATES[-1]:
            raise B1OrchestrationError(
                "raw slice slot coverage is incomplete, interleaved, or reordered"
            )
        groups.append(group)
    if cursor != len(raw_slices):
        raise B1OrchestrationError("raw slice stream has duplicate or out-of-order trailing records")
    return groups


def _prepare_policy_replay_invocation(
    *, staging: Path, attempt_id: str, index: int, seed: int, arm: str,
    raw_group: Sequence[Mapping[str, Any]], implementation_commit: str,
    source_conformance_sha256: str, literal_binding_spec_sha256: str,
    test_only: bool = False,
) -> tuple[list[str], Path, Path, Path, Path]:
    """Create one fixed replay request, with admission as its final pre-child action."""

    if ARM_SEED_ORDER[index] != (seed, arm) or not raw_group:
        raise B1OrchestrationError("policy replay slot identity/order differs")
    slot_root = staging / "policy-replay" / f"{index:02d}"
    scratch = slot_root / "scratch"
    slot_root.mkdir(parents=True, exist_ok=False)
    scratch.mkdir()
    checkpoints: dict[int, dict[str, Any]] = {}
    evaluations: dict[int, dict[str, Any]] = {}
    active_modes: tuple[str, ...] | None = None
    for raw in raw_group:
        if raw.get("seed") != seed or raw.get("arm") != arm:
            raise B1OrchestrationError("policy replay raw slot identity differs")
        mechanical = raw.get("mechanical_direct")
        if not isinstance(mechanical, Mapping) or not isinstance(
            mechanical.get("active_modes"), list
        ):
            raise B1OrchestrationError("policy replay active-mode provenance is absent")
        modes = tuple(mechanical["active_modes"])
        # `b1_runtime_audit.observe_active_modes` records the execution modes that
        # VIOLATE frozen FP32 CPU execution, so a conformant slice records the empty
        # list and `require_frozen_execution_modes` has already refused a non-empty
        # one. The former clause was `if not modes or (...)`, which demanded at least
        # one prohibited mode and so could not be satisfied by any conformant run,
        # while both consumers of this value require it to be empty
        # (b1_metrics_policy_assembly rejects non-empty `source_active_modes`;
        # b1_metrics_training_assembly audits `active_modes` against expected=[]).
        # Absent provenance still refuses, above.
        if modes:
            raise B1OrchestrationError("policy replay source execution modes are prohibited")
        if active_modes is not None and modes != active_modes:
            raise B1OrchestrationError("policy replay active-mode provenance differs")
        active_modes = modes
        for record in raw.get("checkpoints_created", ()):
            update = record.get("update")
            path = staging / "arm-seeds" / _slot_tag(index, seed, arm) / record.get(
                "relative_path", ""
            )
            if update in checkpoints:
                raise B1OrchestrationError("policy replay checkpoint coverage duplicates")
            checkpoints[update] = {
                "update": update, "path": str(path.resolve(strict=True)),
                "sha256": record.get("sha256"),
            }
        for record in raw.get("evaluations", ()):
            # The worker records a held-out evaluation under "update", the same
            # key `checkpoints_created` uses; "checkpoint_update" is a metrics
            # TABLE column, not a field of this raw record. Reading the absent
            # key yielded None for every evaluation, so the second evaluation of
            # a slice always collided at key None and every conformant run
            # refused with "policy replay evaluation coverage duplicates".
            update = record.get("update")
            if update in evaluations:
                raise B1OrchestrationError("policy replay evaluation coverage duplicates")
            evaluations[update] = dict(record)
    if tuple(sorted(checkpoints)) != B1_CHECKPOINT_UPDATES or tuple(
        sorted(evaluations)
    ) != B1_CHECKPOINT_UPDATES:
        raise B1OrchestrationError("policy replay checkpoint/evaluation coverage differs")
    admission = slot_root / "admission.json"
    result = slot_root / "result.json"
    error = slot_root / "error.json"
    request_path = slot_root / "request.json"
    run_memory_preflight(
        admission, attempt_id=attempt_id, arm=arm, seed=seed,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
    )
    request = encode_policy_replay_request(
        attempt_root=staging, attempt_id=attempt_id, seed=seed, arm=arm,
        original_slot_index=index,
        checkpoint_inventory=[checkpoints[u] for u in B1_CHECKPOINT_UPDATES],
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        literal_binding_spec_sha256=literal_binding_spec_sha256,
        source_evaluations=[evaluations[u] for u in B1_CHECKPOINT_UPDATES],
        source_active_modes=active_modes or (), admission_receipt_path=admission,
        admission_receipt_sha256=_digest(admission.read_bytes()),
        scratch_root=scratch, output_path=result, error_path=error,
        test_only=test_only,
    )
    _atomic_create_json(request_path, request)
    command = [
        str(Path(sys.executable).resolve()), "-m",
        "experiments.candidates.capability_bound_semantic_currentness.omrc_b01.b1_policy_replay_worker",
        "--request", str(request_path.resolve(strict=True)),
    ]
    return command, result, error, scratch, admission


def _execute_policy_replay_batch(
    *, staging: Path, attempt_id: str,
    groups: Sequence[Sequence[Mapping[str, Any]]], implementation_commit: str,
    source_conformance_sha256: str, test_only: bool = False,
) -> B1PolicyReplayBatchWitness:
    indices = (1, 5, 9) if test_only else tuple(range(len(ARM_SEED_ORDER)))
    literal = REPO_ROOT / LITERAL_BINDING_SPEC_RELATIVE_PATH
    literal_sha = _digest(literal.read_bytes())
    for index in indices:
        seed, arm = ARM_SEED_ORDER[index]
        command, result, _, scratch, _ = _prepare_policy_replay_invocation(
            staging=staging, attempt_id=attempt_id, index=index, seed=seed, arm=arm,
            raw_group=groups[index], implementation_commit=implementation_commit,
            source_conformance_sha256=source_conformance_sha256,
            literal_binding_spec_sha256=literal_sha, test_only=test_only,
        )
        wrapper, measurement = supervise_policy_replay_child(
            command, result_path=result, scratch_root=scratch, durable_root=staging,
            stdout_path=result.with_name("stdout.log"),
            stderr_path=result.with_name("stderr.log"), test_only=test_only,
        )
        telemetry = {
            "schema": "cbsc_omrc_b01_policy_replay_telemetry_v1",
            "attempt_id": attempt_id, "run_name": B1_RUN_NAME,
            "original_slot_index": index, "seed": seed, "arm": arm,
            "measurement": measurement, "scientific_branch": None,
        }
        _atomic_create_json(result.with_name("telemetry.json"), telemetry)
        if scratch.exists():
            shutil.rmtree(scratch)
    return make_b1_policy_replay_batch_witness(
        staging_root=staging, allowed_root=CONFINED_ROOT, attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_conformance_sha256,
        literal_binding_spec_sha256=literal_sha, test_only=test_only,
    )


def _assemble_and_publish_complete(
    *, staging: Path, final_path: Path, implementation_commit: str,
    source_receipt: Mapping[str, Any], b0_evidence: Mapping[str, Any],
    raw_slices: Sequence[Mapping[str, Any]], admissions: Sequence[Mapping[str, Any]],
    telemetry_records: Sequence[Mapping[str, Any]], laws: Mapping[str, str],
    incident_lineage_witness: B1IncidentLineageWitness,
) -> Path:
    _refuse_pending_analysis()
    groups = _validate_raw_slice_sequence(raw_slices)
    attempt_ids = {raw.get("attempt_id") for group in groups for raw in group}
    if len(attempt_ids) != 1 or not isinstance(next(iter(attempt_ids)), str):
        raise B1OrchestrationError("policy replay attempt identity differs across raw slots")
    attempt_id = next(iter(attempt_ids))
    policy_replay_witness = _execute_policy_replay_batch(
        staging=staging, attempt_id=attempt_id, groups=groups,
        implementation_commit=implementation_commit,
        source_conformance_sha256=source_receipt["source_conformance_sha256"],
    )
    authority_witness = make_b1_canonical_authority_witness(
        staging_root=staging, allowed_root=CONFINED_ROOT, attempt_id=attempt_id,
        implementation_commit=implementation_commit,
        b0_root=Path(b0_evidence["root"]),
    )
    return assemble_and_publish_b1_metrics(
        staging_root=staging,
        final_path=final_path,
        grouped_raw_slices=groups,
        authority_witness=authority_witness,
        incident_lineage_witness=incident_lineage_witness,
        policy_replay_witness=policy_replay_witness,
        allowed_root=CONFINED_ROOT,
    )


def _execute_slot(
    *, staging: Path, attempt_id: str, index: int, seed: int, arm: str,
    implementation_commit: str, source_conformance_sha256: str,
    start_update: int = 0, resume_checkpoint: Path | None = None,
) -> None:
    if resume_checkpoint is None:
        if start_update != 0:
            raise B1OrchestrationError("fresh slot execution must start at update 0")
        schedule: list[tuple[int, int, Path | None]] = [
            (0, 12, None),
            (12, 24, staging / "arm-seeds" / _slot_tag(index, seed, arm) / "checkpoint-update-12.pt"),
            (24, 48, staging / "arm-seeds" / _slot_tag(index, seed, arm) / "checkpoint-update-24.pt"),
        ]
    else:
        schedule = [(start_update, 48, resume_checkpoint)]
    for slice_start, slice_stop, checkpoint in schedule:
        command, _, result_path, _, scratch, _, _ = _prepare_worker_invocation(
            staging=staging, attempt_id=attempt_id, order_index=index,
            arm=arm, seed=seed, implementation_commit=implementation_commit,
            source_conformance_sha256=source_conformance_sha256,
            start_update=slice_start, stop_update=slice_stop,
            resume_checkpoint=checkpoint,
        )
        _, telemetry = supervise_child(
            command, scratch_root=scratch, durable_root=staging,
            result_path=result_path,
            stdout_path=result_path.with_name("stdout.log"),
            stderr_path=result_path.with_name("stderr.log"),
        )
        _atomic_create_json(result_path.with_name("telemetry.json"), telemetry)
        if scratch.exists():
            shutil.rmtree(scratch)


def _execute_fresh_attempt(
    *, final_path: Path, implementation_commit: str,
    source_receipt: Mapping[str, Any], b0_evidence: Mapping[str, Any],
) -> Path:
    attempt_id = f"b1-{uuid.uuid4().hex}"
    staging = create_b1_staging_directory(final_path, allowed_root=CONFINED_ROOT)
    (staging / "admissions").mkdir(parents=True, exist_ok=True)
    laws = _law_digests(source_receipt)
    raw_slices: list[dict[str, Any]] = []
    admissions: list[dict[str, Any]] = []
    telemetry_records: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    failed_index: int | None = None
    try:
        for index, (seed, arm) in enumerate(ARM_SEED_ORDER):
            failed_index = index
            _execute_slot(
                staging=staging, attempt_id=attempt_id, index=index,
                seed=seed, arm=arm, implementation_commit=implementation_commit,
                source_conformance_sha256=source_receipt["source_conformance_sha256"],
            )
            slot_raw, admission, telemetry, digests = _load_slot_evidence(
                staging, index, seed, arm, expected_attempt_id=attempt_id,
                expected_commit=implementation_commit,
            )
            _validate_slot_checkpoint_files(
                staging, index, seed, arm, slot_raw,
                attempt_id=attempt_id,
                implementation_commit=implementation_commit,
                source_conformance_sha256=source_receipt["source_conformance_sha256"],
            )
            raw_slices.extend(slot_raw)
            admissions.append(admission)
            telemetry_records.append(telemetry)
            completed.append({
                "slot_index": index, "arm": arm, "seed": seed, **digests,
            })
            failed_index = None
        return _assemble_and_publish_complete(
            staging=staging, final_path=final_path,
            implementation_commit=implementation_commit,
            source_receipt=source_receipt, b0_evidence=b0_evidence,
            raw_slices=raw_slices, admissions=admissions,
            telemetry_records=telemetry_records, laws=laws,
            incident_lineage_witness=make_b1_incident_lineage_witness(
                [], allowed_root=CONFINED_ROOT
            ),
        )
    except BaseException as exc:
        if staging.exists():
            _publish_attempt_incident(
                staging=staging, final_path=final_path, attempt_id=attempt_id,
                implementation_commit=implementation_commit,
                source_receipt=source_receipt, laws=laws, completed=completed,
                b0_evidence=b0_evidence, failed_index=failed_index, exc=exc,
                incident_lineage_witness=None,
            )
        raise


def _execute_resume_attempt(
    *, final_path: Path, implementation_commit: str,
    source_receipt: Mapping[str, Any], b0_evidence: Mapping[str, Any],
    validated_incident: Mapping[str, Any],
) -> Path:
    incident_root = Path(validated_incident["incident_root"])
    ledger = validated_incident["ledger"]
    attempt_id = ledger.binding.attempt_id
    staging = create_b1_staging_directory(final_path, allowed_root=CONFINED_ROOT)
    (staging / "admissions").mkdir(parents=True, exist_ok=True)
    laws = _law_digests(source_receipt)
    raw_slices: list[dict[str, Any]] = []
    admissions: list[dict[str, Any]] = []
    telemetry_records: list[dict[str, Any]] = []
    completed: list[dict[str, Any]] = []
    failed_index: int | None = None
    try:
        for index, slot in enumerate(ledger.slots):
            seed, arm = ARM_SEED_ORDER[index]
            failed_index = index
            if slot.status is B1SlotStatus.COMPLETE:
                slot_raw, admission, telemetry, digests = _copy_complete_slot(
                    incident_root=incident_root, staging=staging, slot=slot,
                    implementation_commit=implementation_commit,
                    source_conformance_sha256=source_receipt["source_conformance_sha256"],
                )
            else:
                start_update = 0
                checkpoint: Path | None = None
                if slot.status is B1SlotStatus.INCOMPLETE:
                    start_update, checkpoint = _copy_incomplete_prefix(
                        incident_root=incident_root, staging=staging, slot=slot,
                        implementation_commit=implementation_commit,
                        source_conformance_sha256=source_receipt["source_conformance_sha256"],
                    )
                _execute_slot(
                    staging=staging, attempt_id=attempt_id, index=index,
                    seed=seed, arm=arm, implementation_commit=implementation_commit,
                    source_conformance_sha256=source_receipt["source_conformance_sha256"],
                    start_update=start_update, resume_checkpoint=checkpoint,
                )
                slot_raw, admission, telemetry, digests = _load_slot_evidence(
                    staging, index, seed, arm, expected_attempt_id=attempt_id,
                    expected_commit=implementation_commit,
                )
                _validate_slot_checkpoint_files(
                    staging, index, seed, arm, slot_raw,
                    attempt_id=attempt_id,
                    implementation_commit=implementation_commit,
                    source_conformance_sha256=source_receipt["source_conformance_sha256"],
                )
            raw_slices.extend(slot_raw)
            admissions.append(admission)
            telemetry_records.append(telemetry)
            completed.append({
                "slot_index": index, "arm": arm, "seed": seed, **digests,
            })
            failed_index = None
        return _assemble_and_publish_complete(
            staging=staging, final_path=final_path,
            implementation_commit=implementation_commit,
            source_receipt=source_receipt, b0_evidence=b0_evidence,
            raw_slices=raw_slices, admissions=admissions,
            telemetry_records=telemetry_records, laws=laws,
            incident_lineage_witness=validated_incident["lineage_witness"],
        )
    except BaseException as exc:
        if staging.exists():
            _publish_attempt_incident(
                staging=staging, final_path=final_path, attempt_id=attempt_id,
                implementation_commit=implementation_commit,
                source_receipt=source_receipt, laws=laws, completed=completed,
                b0_evidence=b0_evidence, failed_index=failed_index, exc=exc,
                incident_lineage_witness=validated_incident["lineage_witness"],
            )
        raise

WINDOWS_MAX_PATH = 260
#: Bytes reserved under `scratch/<slot>/<invocation>/` for engine-written files,
#: whose names the orchestrator does not fix.
SCRATCH_NAME_RESERVE = 48


def projected_attempt_paths(final_path: Path) -> dict[str, Any]:
    """Measure the longest absolute path this attempt will write.

    Windows refuses a path over ``MAX_PATH`` (260) with ``WinError 3``, and the
    first thing an attempt writes is the bound admission receipt's raw sibling,
    the longest path in the transaction.  The 2026-09-03 attempt
    ``b1-bca815500920492da688f83a2595e34e`` died there at 279 characters with a
    message that names a missing path, so this measures the budget up front and
    refuses with the arithmetic instead.  Nothing scientific depends on the run
    root's name.
    """

    final = Path(final_path).resolve(strict=False)
    staging = final.parent / f".{final.name}.partial-{'0' * 32}"
    longest = str(staging)
    for index, (seed, arm) in enumerate(ARM_SEED_ORDER):
        tag = _slot_tag(index, seed, arm)
        for start, stop in ((0, 12), (12, 24), (24, 48), (0, 48)):
            invocation = f"slice-{start:02d}-{stop:02d}"
            receipt = staging / "admissions" / f"{tag}-{invocation}-admission.json"
            worker_root = staging / "workers" / tag / invocation
            candidates = (
                receipt,
                receipt.with_name(f".{receipt.name}.raw-{'0' * 32}.json"),
                worker_root / "supervisor-incident.json",
                staging / "arm-seeds" / tag / f"checkpoint-update-{stop}.pt",
                Path(
                    str(staging / "scratch" / tag / invocation)
                    + "\\" + "x" * SCRATCH_NAME_RESERVE
                ),
            )
            for candidate in candidates:
                text = str(candidate)
                if len(text) > len(longest):
                    longest = text
    overhead = len(longest) - len(final.name)
    return {
        "final_path": str(final),
        "longest_projected_path": longest,
        "longest_projected_length": len(longest),
        "limit": WINDOWS_MAX_PATH,
        "run_root_name": final.name,
        "maximum_run_root_name_length": WINDOWS_MAX_PATH - 1 - overhead,
        "fits": len(longest) < WINDOWS_MAX_PATH,
    }


def require_attempt_path_budget(final_path: Path) -> dict[str, Any]:
    """Refuse before creating anything when the attempt cannot fit MAX_PATH."""

    budget = projected_attempt_paths(final_path)
    if not budget["fits"]:
        raise B1OrchestrationError(
            "BLOCKED_PATH_BUDGET: the longest path this attempt writes is "
            f"{budget['longest_projected_length']} characters against the "
            f"{WINDOWS_MAX_PATH}-character limit; the run root name "
            f"{budget['run_root_name']!r} may be at most "
            f"{budget['maximum_run_root_name_length']} characters at this "
            "output directory"
        )
    return budget


def _refuse_pending_analysis() -> None:
    readiness = _readiness_result()
    if not readiness.authorized:
        raise B1OrchestrationError(
            "REPAIR_REQUIRED: " + "; ".join(readiness.blockers)
        )


def run_b1_start(*, final_path: Path, implementation_commit: str, b0_root: Path) -> Path:
    """Formal fresh-start boundary; create nothing until all authorities are bound."""

    source = verify_source_conformance(implementation_commit)
    b0_evidence = locate_b0_evidence(b0_root)
    require_attempt_path_budget(final_path)
    ensure_confined(Path(final_path), CONFINED_ROOT)
    if Path(final_path).exists():
        raise FileExistsError(f"create-only B1 final root already exists: {final_path}")
    _refuse_pending_analysis()
    return _execute_fresh_attempt(
        final_path=Path(final_path), implementation_commit=implementation_commit,
        source_receipt=source, b0_evidence=b0_evidence,
    )


def run_b1_resume(
    *, final_path: Path, implementation_commit: str, b0_root: Path,
    incident_root: Path,
) -> Path:
    """Resume one immutable whole-attempt ledger into a new transaction."""

    source = verify_source_conformance(implementation_commit)
    b0_evidence = locate_b0_evidence(b0_root)
    require_attempt_path_budget(final_path)
    ensure_confined(Path(final_path), CONFINED_ROOT)
    if Path(final_path).exists():
        raise FileExistsError(f"create-only B1 resume final root already exists: {final_path}")
    validated_incident = validate_resume_incident(
        incident_root, expected_commit=implementation_commit,
        expected_source_sha256=source["source_conformance_sha256"],
        expected_laws_sha256=_digest(
            canonical_json_bytes(_law_digests(source))
        ),
        expected_b0_evidence=b0_evidence,
    )
    _refuse_pending_analysis()
    return _execute_resume_attempt(
        final_path=Path(final_path), implementation_commit=implementation_commit,
        source_receipt=source, b0_evidence=b0_evidence,
        validated_incident=validated_incident,
    )


__all__ = [
    "ARM_SEED_ORDER", "B1OrchestrationError", "CANONICAL_ENGINE_FACTORY",
    "CANONICAL_ENGINE_MODULE", "CANONICAL_ENGINE_TYPE", "CANONICAL_SOURCE_SURFACE",
    "CANONICAL_WORKER_MODULE", "CONFINED_ROOT", "DECISION", "FORMAL_ANALYSIS_BOUND",
    "canonical_engine_identity", "locate_b0_evidence", "projected_attempt_paths",
    "readiness_document", "require_attempt_path_budget",
    "run_assess_preflight", "run_b1_resume", "run_b1_start", "supervise_child",
    "validate_resume_incident", "verify_source_conformance",
]
