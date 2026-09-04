"""B0-only orchestration seam for CBSC-OMRC-B01.

This module intentionally does not construct the dynamic host or PPO learner
in the parent.  The formal path starts only the frozen canonical worker and
recomputes its claims from raw actions, tapes, laws, and checkpoints.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence
import uuid

from .artifact import (
    ArtifactError,
    B0_RUN_NAME,
    CLARIFICATION_ID,
    NO_SCIENCE_CLAIM,
    OBJECT_ID,
    PINNED_EVIDENCE_REF,
    RESULT_SCHEMA,
    create_staging_directory,
    directory_size,
    publish_complete,
    publish_incident,
    publish_incident_bundle,
    sha256_json,
)
from .telemetry import (
    DURABLE_CAP_BYTES,
    ProcessTreeMonitor,
    ResourceCaps,
    TelemetryError,
    validate_telemetry,
)


DIRECTION_ID = "capability_bound_semantic_currentness"
B0_SEED = 21001
ARMS = (
    "STRUCT-CURRENTNESS-GRU",
    "RAW-GRU",
    "PI-GRU",
    "DERANGED-CURRENTNESS-GRU",
)
TRAIN_EPISODE_IDS = tuple(range(8))
EVAL_STOCHASTIC_IDS = (0, 1, 2, 3)
EVAL_MOTIF_IDS = (0, 12, 20, 28)
CHECKPOINT_IDENTITIES = ("update-0", "update-1")
EXPECTED_COUNTS = {
    "train_episodes": 8,
    "train_transitions": 8 * 152,
    "train_decisions": 8 * 24,
    "rollout_updates": 1,
    "ppo_epochs": 4,
    "minibatches_per_epoch": 4,
    "optimizer_steps": 16,
    "evaluation_episodes": 8,
    "evaluation_transitions": 8 * 152,
    "evaluation_decisions": 8 * 24,
}
COMMON_DIGESTS = (
    "configuration",
    "environment_law",
    "token_law",
    "environment_train_tapes",
    "primitive_train_histories",
    "action_uniforms",
    "parameter_initialization",
    "minibatch_order",
    "evaluation_tapes",
)
REQUIRED_AUDITS = (
    "event_order_causality",
    "ledger_oracle_arithmetic",
    "action_masks",
    "adapter_replay",
    "primitive_history_parity",
    "heldout_separation",
    "rng_address_independence",
    "update_evaluation_counters",
    "checkpoint_roundtrip",
    "parameter_update_parity",
    "evaluation_parity",
)
MIN_AVAILABLE_BYTES = 4 * 1024**3
REPO_ROOT = Path(__file__).resolve().parents[4]
CONFINED_ROOT = (
    REPO_ROOT / "temp" / "directions" / DIRECTION_ID
).resolve(strict=False)
CANONICAL_PREFLIGHT = (REPO_ROOT / "scripts" / "hmasd_resource_preflight.py").resolve()
CANONICAL_ENGINE_MODULE = (
    "experiments.candidates.capability_bound_semantic_currentness.omrc_b01.engine"
)
CANONICAL_ENGINE_FACTORY = "b0_engine"
CANONICAL_ENGINE_TYPE = "LiteralB0Engine"
CANONICAL_WORKER_MODULE = (
    "experiments.candidates.capability_bound_semantic_currentness.omrc_b01.worker"
)
CANONICAL_SOURCE_SURFACE = (
    "docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md",
    "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md",
    "docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/__init__.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/addressing.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/adapters.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/artifact.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b0.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/checkpoint.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/contract.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/engine.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/evaluator.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/host.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ledger.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/model.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/state.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/tapes.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/telemetry.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/token.py",
    "experiments/candidates/capability_bound_semantic_currentness/omrc_b01/worker.py",
    "scripts/hmasd_resource_preflight.py",
    "scripts/run_cbsc_omrc_b01.py",
)
BOUND_ADMISSION_SCHEMA = "cbsc_omrc_b01_b0_bound_admission_v1"


class B0ContractError(RuntimeError):
    """The B0 shell or connected engine violated the frozen observable."""


@dataclass(frozen=True)
class B0Plan:
    run_name: str = B0_RUN_NAME
    seed: int = B0_SEED
    arms: tuple[str, ...] = ARMS
    train_episode_ids: tuple[int, ...] = TRAIN_EPISODE_IDS
    eval_stochastic_ids: tuple[int, ...] = EVAL_STOCHASTIC_IDS
    eval_motif_ids: tuple[int, ...] = EVAL_MOTIF_IDS
    rollout_updates: int = 1
    ppo_epochs: int = 4
    minibatches_per_epoch: int = 4
    optimizer_steps_per_arm: int = 16
    checkpoints: tuple[str, ...] = CHECKPOINT_IDENTITIES
    scientific_branch: None = None

    def validate(self) -> None:
        if self != B0Plan():
            raise B0ContractError("B0 plan differs from the literal clarification")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class B0ArmRequest:
    plan: B0Plan
    arm: str
    seed: int
    train_episode_ids: tuple[int, ...]
    eval_stochastic_ids: tuple[int, ...]
    eval_motif_ids: tuple[int, ...]
    scratch_root: Path
    durable_root: Path
    admission_receipt_path: Path
    admission_receipt: Mapping[str, Any]
    resource_caps: ResourceCaps


def frozen_configuration() -> dict[str, Any]:
    plan = B0Plan()
    return {
        "object_id": OBJECT_ID,
        "clarification_id": CLARIFICATION_ID,
        "plan": plan.as_dict(),
        "counts_per_arm": dict(EXPECTED_COUNTS),
        "resource_caps": ResourceCaps().as_dict(),
        "result_schema": RESULT_SCHEMA,
        "claim_ceiling": NO_SCIENCE_CLAIM,
    }


def refuse_non_b0(run_name: str) -> None:
    if run_name != B0_RUN_NAME:
        raise B0ContractError("this entry point is B0-only and refuses B1/B2")


def validate_memory_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    receipt = dict(value)
    required = {
        "passed",
        "physical_floor_pass",
        "effective_floor_pass",
        "available_physical_bytes",
        "effective_available_bytes",
    }
    missing = required - set(receipt)
    if missing:
        raise B0ContractError(f"memory admission fields are missing: {sorted(missing)}")
    if (
        receipt["passed"] is not True
        or receipt["physical_floor_pass"] is not True
        or receipt["effective_floor_pass"] is not True
    ):
        raise B0ContractError("memory admission did not pass both 4-GiB floors")
    for name in ("available_physical_bytes", "effective_available_bytes"):
        if type(receipt[name]) is not int or receipt[name] < MIN_AVAILABLE_BYTES:
            raise B0ContractError(f"memory admission {name} is below 4 GiB")
    return receipt


def run_memory_preflight(
    receipt_path: Path,
    arm: str,
    *,
    attempt_id: str,
    implementation_commit: str,
    source_conformance_sha256: str,
) -> Mapping[str, Any]:
    """Run and bind the one canonical shared admission command."""

    if arm not in ARMS or not attempt_id:
        raise B0ContractError("admission attempt/arm identity differs")
    executable = Path(sys.executable).resolve()
    script = CANONICAL_PREFLIGHT
    raw_path = receipt_path.with_name(f".{receipt_path.name}.raw-{uuid.uuid4().hex}.json")
    command = [str(executable), str(script), "admit-memory", "--out", str(raw_path)]
    completed = subprocess.run(command, capture_output=True, text=True, shell=False, timeout=120)
    if completed.returncode != 0:
        raise B0ContractError(
            f"memory admission failed with exit {completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        receipt = json.loads(raw_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B0ContractError("memory admission receipt is unreadable") from exc
    bound = {
        "schema": BOUND_ADMISSION_SCHEMA,
        "attempt_id": attempt_id,
        "arm": arm,
        "implementation_commit": implementation_commit,
        "source_conformance_sha256": source_conformance_sha256,
        "bound_receipt_path": str(receipt_path.resolve()),
        "raw_output_path": str(raw_path.resolve()),
        "python_executable": str(executable),
        "python_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
        "preflight_script": str(script),
        "preflight_script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "exact_command": command,
        "raw_receipt_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "receipt": validate_memory_receipt(receipt),
    }
    if receipt_path.exists():
        raise FileExistsError("create-only bound admission receipt exists")
    _atomic_create_json(receipt_path, bound)
    return validate_bound_admission(
        bound,
        expected_attempt_id=attempt_id,
        expected_arm=arm,
        expected_commit=implementation_commit,
    )


def validate_bound_admission(
    value: Mapping[str, Any], *, expected_attempt_id: str, expected_arm: str,
    expected_commit: str, expected_receipt_path: Path | None = None,
) -> dict[str, Any]:
    bound = dict(value)
    required = {
        "schema", "attempt_id", "arm", "implementation_commit",
        "bound_receipt_path", "raw_output_path",
        "source_conformance_sha256", "python_executable", "python_sha256",
        "preflight_script", "preflight_script_sha256", "exact_command",
        "raw_receipt_sha256", "receipt",
    }
    if set(bound) != required or bound["schema"] != BOUND_ADMISSION_SCHEMA:
        raise B0ContractError("bound admission schema differs")
    if (
        bound["attempt_id"] != expected_attempt_id
        or bound["arm"] != expected_arm
        or bound["implementation_commit"] != expected_commit
    ):
        raise B0ContractError("bound admission identity differs")
    executable = Path(sys.executable).resolve()
    if (
        bound["python_executable"] != str(executable)
        or bound["python_sha256"] != hashlib.sha256(executable.read_bytes()).hexdigest()
        or bound["preflight_script"] != str(CANONICAL_PREFLIGHT)
        or bound["preflight_script_sha256"]
        != hashlib.sha256(CANONICAL_PREFLIGHT.read_bytes()).hexdigest()
    ):
        raise B0ContractError("bound admission canonical executable/script differs")
    command = bound["exact_command"]
    if (
        not isinstance(command, list)
        or command[:3] != [str(executable), str(CANONICAL_PREFLIGHT), "admit-memory"]
        or len(command) != 5
        or command[3] != "--out"
        or command[4] != bound["raw_output_path"]
    ):
        raise B0ContractError("bound admission exact command differs")
    bound_path = Path(bound["bound_receipt_path"]).resolve(strict=False)
    raw_path = Path(bound["raw_output_path"]).resolve(strict=False)
    if raw_path.parent != bound_path.parent or not raw_path.name.startswith(f".{bound_path.name}.raw-"):
        raise B0ContractError("bound admission raw output path differs")
    if expected_receipt_path is not None and bound_path != expected_receipt_path.resolve(strict=False):
        raise B0ContractError("bound admission persisted path differs")
    _validate_digest(bound["source_conformance_sha256"], "source_conformance_sha256")
    _validate_digest(bound["raw_receipt_sha256"], "raw_receipt_sha256")
    bound["receipt"] = validate_memory_receipt(bound["receipt"])
    if expected_receipt_path is not None:
        if not raw_path.is_file():
            raise B0ContractError("bound admission raw receipt is absent")
        raw_bytes = raw_path.read_bytes()
        if hashlib.sha256(raw_bytes).hexdigest() != bound["raw_receipt_sha256"]:
            raise B0ContractError("bound admission raw receipt bytes differ")
        try:
            raw_receipt = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise B0ContractError("bound admission raw receipt is unreadable") from exc
        if validate_memory_receipt(raw_receipt) != bound["receipt"]:
            raise B0ContractError("bound admission parsed receipt differs from raw bytes")
    return bound


def run_assess_preflight(
    receipt_path: Path,
    *,
    workers: int,
    threads_per_worker: int,
) -> dict[str, Any]:
    """Run the shared result-blind B0 resource assessment; this is not B0."""

    executable = Path(sys.executable).resolve()
    script = CANONICAL_PREFLIGHT
    command = [
        str(executable),
        str(script),
        "assess-run",
        "--direction",
        DIRECTION_ID,
        "--run-id",
        "cbsc_omrc_b0_instrument",
        "--workers",
        str(workers),
        "--threads-per-worker",
        str(threads_per_worker),
        "--estimated-wall-seconds",
        "1800",
        "--estimated-peak-gib",
        "4",
        "--basis",
        "frozen B0 per-arm cap; result-blind readiness only",
        "--out",
        str(receipt_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, shell=False, timeout=120)
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B0ContractError("assess-run receipt is unreadable") from exc
    receipt["command_returncode"] = completed.returncode
    receipt["performance_disposition"] = "PILOT_ONLY"
    receipt["scientific_branch"] = None
    return receipt


def _canonical_engine_identity() -> dict[str, str]:
    module = importlib.import_module(CANONICAL_ENGINE_MODULE)
    factory = getattr(module, CANONICAL_ENGINE_FACTORY, None)
    engine_type = getattr(module, CANONICAL_ENGINE_TYPE, None)
    if not callable(factory) or not inspect.isclass(engine_type):
        raise B0ContractError("canonical engine factory/type is absent")
    factory_file = Path(inspect.getsourcefile(factory) or "").resolve()
    type_file = Path(inspect.getsourcefile(engine_type) or "").resolve()
    expected = (REPO_ROOT / CANONICAL_SOURCE_SURFACE[10]).resolve()
    if (
        factory.__module__ != CANONICAL_ENGINE_MODULE
        or engine_type.__module__ != CANONICAL_ENGINE_MODULE
        or factory_file != expected
        or type_file != expected
    ):
        raise B0ContractError("canonical engine factory/type module identity differs")
    return {
        "module": CANONICAL_ENGINE_MODULE,
        "factory": CANONICAL_ENGINE_FACTORY,
        "type": CANONICAL_ENGINE_TYPE,
        "factory_file": factory_file.relative_to(REPO_ROOT).as_posix(),
        "type_file": type_file.relative_to(REPO_ROOT).as_posix(),
    }


def verify_source_conformance(implementation_commit: str) -> dict[str, Any]:
    """Verify the frozen canonical source surface without engine declarations."""

    try:
        decoded = bytes.fromhex(implementation_commit)
    except ValueError as exc:
        raise B0ContractError("implementation_commit must be lowercase Git hex") from exc
    if len(decoded) != 20 or decoded.hex() != implementation_commit:
        raise B0ContractError("implementation_commit must be lowercase Git hex")
    engine_identity = _canonical_engine_identity()
    relative_paths = list(CANONICAL_SOURCE_SURFACE)
    resolved_paths = [(REPO_ROOT / relative).resolve() for relative in relative_paths]
    if any(not path.is_file() for path in resolved_paths):
        raise B0ContractError("BLOCKED_UNCOMMITTED: canonical source surface is incomplete")

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, shell=False, timeout=60
        )

    head = git("rev-parse", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != implementation_commit:
        raise B0ContractError("BLOCKED_UNCOMMITTED: implementation_commit is not current HEAD")
    for relative in relative_paths:
        tracked = git("ls-files", "--error-unmatch", "--", relative)
        if tracked.returncode != 0:
            raise B0ContractError(f"BLOCKED_UNCOMMITTED: source is not tracked: {relative}")
    status = git("status", "--porcelain", "--untracked-files=all", "--", *relative_paths)
    if status.returncode != 0 or status.stdout.strip():
        raise B0ContractError("BLOCKED_UNCOMMITTED: implementation source differs from HEAD")
    diff = git("diff", "--quiet", implementation_commit, "--", *relative_paths)
    if diff.returncode != 0:
        raise B0ContractError("BLOCKED_UNCOMMITTED: implementation bytes differ from commit")
    files = [
        {"path": relative, "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest()}
        for relative, path in zip(relative_paths, resolved_paths)
    ]
    receipt = {
        "status": "COMMIT_CONFORMANT",
        "commit": implementation_commit,
        "canonical_engine": engine_identity,
        "files": files,
    }
    receipt["source_conformance_sha256"] = sha256_json(receipt)
    return receipt


def _validate_digest(value: Any, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise B0ContractError(f"{name} must be a SHA-256 hex digest")
    try:
        decoded = bytes.fromhex(value)
    except ValueError as exc:
        raise B0ContractError(f"{name} must be a SHA-256 hex digest") from exc
    if len(decoded) != 32 or decoded.hex() != value:
        raise B0ContractError(f"{name} must be lowercase SHA-256 hex")
    return value


def validate_arm_result(value: Mapping[str, Any], *, expected_arm: str) -> dict[str, Any]:
    result = dict(value)
    required = {
        "arm",
        "seed",
        "run_name",
        "counts",
        "checkpoint_identities",
        "digests",
        "audits",
        "numerical_finite",
        "scientific_branch",
        "stage_measurements",
        "worker_count",
        "threads_per_worker",
        "records",
    }
    missing = required - set(result)
    if missing:
        raise B0ContractError(f"{expected_arm} result fields are missing: {sorted(missing)}")
    if (
        result["arm"] != expected_arm
        or result["seed"] != B0_SEED
        or result["run_name"] != B0_RUN_NAME
    ):
        raise B0ContractError(f"{expected_arm} result identity differs")
    if result["counts"] != EXPECTED_COUNTS:
        raise B0ContractError(f"{expected_arm} B0 counts differ")
    if result["checkpoint_identities"] != list(CHECKPOINT_IDENTITIES):
        raise B0ContractError(f"{expected_arm} checkpoint identities differ")
    if result["scientific_branch"] is not None:
        raise B0ContractError("B0 engine returned a prohibited scientific branch")
    if result["numerical_finite"] is not True:
        raise B0ContractError(f"{expected_arm} reported nonfinite values")
    if type(result["worker_count"]) is not int or result["worker_count"] < 1:
        raise B0ContractError("worker_count must be positive")
    if type(result["threads_per_worker"]) is not int or result["threads_per_worker"] < 1:
        raise B0ContractError("threads_per_worker must be positive")
    digests = result["digests"]
    if not isinstance(digests, Mapping):
        raise B0ContractError(f"{expected_arm} digests are absent")
    for name in (*COMMON_DIGESTS, "adapter_law", "checkpoint_bytes", "adapter_work"):
        _validate_digest(digests.get(name), f"{expected_arm}.{name}")
    audits = result["audits"]
    if not isinstance(audits, Mapping):
        raise B0ContractError(f"{expected_arm} audits are absent")
    for name in REQUIRED_AUDITS:
        if audits.get(name) is not True:
            raise B0ContractError(f"{expected_arm} audit failed: {name}")
    stages = result["stage_measurements"]
    if not isinstance(stages, list) or not stages:
        raise B0ContractError(f"{expected_arm} stage measurements are absent")
    if not isinstance(result["records"], Mapping):
        raise B0ContractError(f"{expected_arm} records must be an object")
    records = result["records"]
    record_fields = {
        "train_episode_ids",
        "evaluation_roots",
        "update_zero_checks",
        "post_update_checks",
        "checkpoints",
        "diagnostics",
    }
    missing_records = record_fields - set(records)
    if missing_records:
        raise B0ContractError(
            f"{expected_arm} B0 records are missing: {sorted(missing_records)}"
        )
    if records["train_episode_ids"] != list(TRAIN_EPISODE_IDS):
        raise B0ContractError(f"{expected_arm} training roots differ")
    if records["evaluation_roots"] != {
        "EVAL_STOCHASTIC": list(EVAL_STOCHASTIC_IDS),
        "EVAL_MOTIF": list(EVAL_MOTIF_IDS),
    }:
        raise B0ContractError(f"{expected_arm} held-out roots differ")
    if not isinstance(records["checkpoints"], Mapping) or set(records["checkpoints"]) != set(
        CHECKPOINT_IDENTITIES
    ):
        raise B0ContractError(f"{expected_arm} checkpoint records differ")
    for name in ("update_zero_checks", "post_update_checks", "diagnostics"):
        if not isinstance(records[name], Mapping) or not records[name]:
            raise B0ContractError(f"{expected_arm} {name} records are absent")
    return result


def validate_cross_arm_parity(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if [result["arm"] for result in results] != list(ARMS):
        raise B0ContractError("B0 arms are absent or out of frozen order")
    baseline = results[0]["digests"]
    for result in results[1:]:
        for name in COMMON_DIGESTS:
            if result["digests"][name] != baseline[name]:
                raise B0ContractError(f"cross-arm parity failed: {name}")
    struct = results[0]["digests"]["adapter_work"]
    deranged = results[3]["digests"]["adapter_work"]
    if struct != deranged:
        raise B0ContractError("STRUCT/DERANGED adapter-work parity failed")
    return {
        "primitive_history_parity": True,
        "parameter_initialization_parity": True,
        "action_uniform_parity": True,
        "minibatch_order_parity": True,
        "evaluation_tape_parity": True,
        "struct_deranged_adapter_work_parity": True,
    }


def _finite_tree(value: Any) -> bool:
    import math

    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_finite_tree(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(item) for item in value)
    return True


def _file_law_digest(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        payload = path.read_bytes()
        digest.update(path.name.encode("utf-8"))
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _panel_digest(tapes: Sequence[Any], *, environment: bool) -> str:
    if environment:
        rows = [
            {
                "identity": vars(tape.identity),
                "draw_digest": tape.generation_audit.draw_digest,
                "draw_count": tape.generation_audit.draw_count,
                "owner_tokens_consumed": tape.generation_audit.owner_tokens_consumed,
                "epoch_tokens_consumed": tape.generation_audit.epoch_tokens_consumed,
            }
            for tape in tapes
        ]
    else:
        rows = [
            {"identity": vars(tape.identity), "primitive_digest": tape.primitive_digest}
            for tape in tapes
        ]
    return sha256_json(rows)


def _validate_action_matrix(
    value: Any, *, name: str, expected_identities: Sequence[Mapping[str, Any]]
) -> list[list[str]]:
    legal = {"SERVE", "REFRESH", "SAFE_FALLBACK"}
    if (
        not isinstance(value, list)
        or len(value) != 8
        or any(not isinstance(row, Mapping) for row in value)
    ):
        raise B0ContractError(f"{name} must contain exact 8x24 identified action traces")
    actions: list[list[str]] = []
    for index, row in enumerate(value):
        if row.get("identity") != dict(expected_identities[index]):
            raise B0ContractError(f"{name} tape identity differs")
        decision_actions = row.get("decision_actions")
        if (
            not isinstance(decision_actions, list)
            or len(decision_actions) != 24
            or any(action not in legal for action in decision_actions)
        ):
            raise B0ContractError(f"{name} must contain exact 8x24 legal decision actions")
        actions.append(decision_actions)
    return actions


def recompute_arm_evidence(
    raw_result: Mapping[str, Any], *, expected_arm: str, arm_root: Path
) -> dict[str, Any]:
    """Rebuild formal digests/audits from canonical laws and raw evidence."""

    from dataclasses import asdict as dataclass_asdict

    from . import addressing
    from .adapters import (
        DerangedCurrentnessAdapter,
        PredictiveIndexAdapter,
        RawHistoryAdapter,
        StructCurrentnessAdapter,
    )
    from .checkpoint import load_checkpoint
    from .host import DynamicHost
    from .tapes import build_b0_panel

    result = dict(raw_result)
    if (
        result.get("engine_evidence_schema")
        != "cbsc_omrc_b01_engine_raw_evidence_v1"
        or result.get("arm") != expected_arm
        or result.get("seed") != B0_SEED
        or result.get("run_name") != B0_RUN_NAME
        or result.get("scientific_branch") is not None
        or result.get("worker_count") != 1
        or result.get("threads_per_worker") != 1
        or result.get("counts") != EXPECTED_COUNTS
    ):
        raise B0ContractError("raw worker identity, topology, or observed counts differ")
    records = result.get("records")
    if not isinstance(records, Mapping):
        raise B0ContractError("raw worker records are absent")
    panel = build_b0_panel(DynamicHost(B0_RUN_NAME, B0_SEED))
    heldout = (*panel.eval_stochastic, *panel.eval_motif)
    all_tapes = (*panel.train, *heldout)
    training_actions = _validate_action_matrix(
        records.get("training_actions"), name="training_actions",
        expected_identities=[vars(tape.identity) for tape in panel.train],
    )
    evaluation_actions = _validate_action_matrix(
        records.get("evaluation_actions"), name="evaluation_actions",
        expected_identities=[vars(tape.identity) for tape in heldout],
    )
    trainer_observations = records.get("trainer_observations")
    if not isinstance(trainer_observations, Mapping):
        raise B0ContractError("raw trainer observations are absent")
    counters = trainer_observations.get("counters")
    if not isinstance(counters, Mapping) or (
        counters.get("train_episodes") != 8
        or counters.get("train_transitions") != 1216
        or counters.get("train_decisions") != 192
        or counters.get("rollout_updates") != 1
        or counters.get("adam_steps") != 16
    ):
        raise B0ContractError("independent trainer counter audit failed")
    if any(tape.transition_count != 152 or tape.decision_count != 24 for tape in all_tapes):
        raise B0ContractError("independent tape count audit failed")
    clock_valid = True
    for tape in all_tapes:
        positions = [int(token.event_order_position) for token in tape.public_tokens]
        clock_valid = clock_valid and positions[:8] == list(range(8))
        clock_valid = clock_valid and all(
            positions[8 + 6 * opportunity : 14 + 6 * opportunity] == list(range(6))
            for opportunity in range(24)
        )
    if not clock_valid:
        raise B0ContractError("independent event-order clock audit failed")
    address_rows = []
    for tape in panel.train:
        for opportunity in range(24):
            address = addressing.action_address(
                B0_RUN_NAME, B0_SEED, tape.identity.episode_id, opportunity
            )
            address_rows.append(
                {
                    "episode_id": tape.identity.episode_id,
                    "opportunity_index": opportunity,
                    "address": list(address),
                    "u64": addressing.u64(address),
                }
            )
            if expected_arm in json.dumps(address):
                raise B0ContractError("arm name entered a common action address")
    rollout_observations = records.get("rollout_observations")
    decision_rows = [12 + 6 * opportunity for opportunity in range(24)]
    forced_wait_rows = [row for row in range(152) if row not in decision_rows]
    if (
        not isinstance(rollout_observations, Mapping)
        or rollout_observations.get("observation_shape") != [8, 152, 168]
        or rollout_observations.get("uniforms") != address_rows
        or rollout_observations.get("uniforms_consumed_rows")
        != [decision_rows for _ in range(8)]
        or rollout_observations.get("forced_wait_rows")
        != [forced_wait_rows for _ in range(8)]
        or rollout_observations.get("terminated_rows") != [[151] for _ in range(8)]
    ):
        raise B0ContractError("independent action-mask, uniform, or terminal audit failed")

    adapter_types = {
        ARMS[0]: StructCurrentnessAdapter,
        ARMS[1]: RawHistoryAdapter,
        ARMS[2]: PredictiveIndexAdapter,
        ARMS[3]: DerangedCurrentnessAdapter,
    }
    adapter_type = adapter_types[expected_arm]
    total_work = None
    for tape in all_tapes:
        first = adapter_type()
        second = adapter_type()
        emitted_first = first.replay(tape.public_tokens)
        emitted_second = second.replay(tape.public_tokens)
        if emitted_first != emitted_second or first.total_work != second.total_work:
            raise B0ContractError("independent adapter replay audit failed")
        total_work = first.total_work if total_work is None else total_work + first.total_work
    if total_work is None:
        raise B0ContractError("independent adapter work audit observed no tapes")

    observed_train_tapes = records.get("train_tapes")
    observed_eval_tapes = records.get("evaluation_tapes")
    expected_train_tapes = [
        {
            "identity": vars(tape.identity),
            "primitive_digest_observed": tape.primitive_digest,
            "draw_digest_observed": tape.generation_audit.draw_digest,
            "draw_count_observed": tape.generation_audit.draw_count,
        }
        for tape in panel.train
    ]
    expected_eval_tapes = [
        {
            "identity": vars(tape.identity),
            "primitive_digest_observed": tape.primitive_digest,
            "draw_digest_observed": tape.generation_audit.draw_digest,
            "draw_count_observed": tape.generation_audit.draw_count,
        }
        for tape in heldout
    ]
    if observed_train_tapes != expected_train_tapes or observed_eval_tapes != expected_eval_tapes:
        raise B0ContractError("raw tape evidence differs from independently rebuilt tapes")
    address_sets = [
        {address for tape in group for address in tape.generation_audit.draw_addresses}
        for group in (panel.train, panel.eval_stochastic, panel.eval_motif)
    ]
    heldout_separated = not any(
        address_sets[left] & address_sets[right]
        for left in range(3)
        for right in range(left + 1, 3)
    )
    if not heldout_separated:
        raise B0ContractError("independent held-out address separation audit failed")

    import struct
    from .contract import Action

    rewards = records.get("rollout_observations", {}).get("rewards")
    if not isinstance(rewards, list) or len(rewards) != 8:
        raise B0ContractError("raw reward-row evidence is absent")
    for tape, names, reward_record in zip(panel.train, training_actions, rewards, strict=True):
        if reward_record.get("identity") != vars(tape.identity):
            raise B0ContractError("raw reward identity differs")
        expected_decision = []
        expected_settlement = []
        evaluator = tape.evaluator()
        for opportunity, name in enumerate(names):
            ledger = evaluator.ledger(opportunity, Action[name])
            expected_decision.append(struct.unpack("f", struct.pack("f", float(ledger.decision_reward)))[0])
            expected_settlement.append(struct.unpack("f", struct.pack("f", float(ledger.settlement_reward)))[0])
        if (
            reward_record.get("decision_rewards") != expected_decision
            or reward_record.get("settlement_rewards") != expected_settlement
            or reward_record.get("nonzero_outside_ledger_rows") != []
        ):
            raise B0ContractError("independent native ledger audit failed")

    oracle_unique = True
    for tape in all_tapes:
        evaluator = tape.evaluator()
        for opportunity in range(24):
            truth = evaluator.truth(opportunity)
            totals = {
                action: truth.ledger(action).undiscounted_total
                for action in (Action.SERVE, Action.REFRESH, Action.SAFE_FALLBACK)
            }
            best = max(totals.values())
            oracle_unique = oracle_unique and sum(value == best for value in totals.values()) == 1
            oracle_unique = oracle_unique and totals[truth.oracle_action] == best
    if not oracle_unique:
        raise B0ContractError("independent ledger oracle uniqueness audit failed")

    checkpoint_records: dict[str, Any] = {}
    checkpoint_aggregate = hashlib.sha256()
    checkpoint_payloads: dict[str, Mapping[str, Any]] = {}
    observed_checkpoint_records = records.get("checkpoints")
    if not isinstance(observed_checkpoint_records, Mapping):
        raise B0ContractError("raw checkpoint observations are absent")
    checkpoint_roundtrip_observed = True
    from .checkpoint import model_parameter_digest_from_state
    for checkpoint_id in CHECKPOINT_IDENTITIES:
        path = arm_root / f"{checkpoint_id}.pt"
        payload_bytes = path.read_bytes()
        payload = load_checkpoint(path)
        identity = payload["identity"]
        if (
            identity["run_name"] != B0_RUN_NAME
            or identity["arm"] != expected_arm
            or identity["seed"] != B0_SEED
            or checkpoint_id != f"update-{identity['completed_rollout_updates']}"
        ):
            raise B0ContractError("independent checkpoint identity audit failed")
        checkpoint_payloads[checkpoint_id] = payload
        model_digest = model_parameter_digest_from_state(payload["model_state"])
        observed_checkpoint = observed_checkpoint_records.get(checkpoint_id)
        checkpoint_roundtrip_observed = checkpoint_roundtrip_observed and bool(
            isinstance(observed_checkpoint, Mapping)
            and observed_checkpoint.get("relative_path") == path.name
            and observed_checkpoint.get("byte_count") == len(payload_bytes)
            and observed_checkpoint.get("loaded_identity") == identity
            and observed_checkpoint.get("loaded_counters") == payload["counters"]
            and observed_checkpoint.get("loaded_digests") == payload["digests"]
            and observed_checkpoint.get("loaded_model_parameter_digest") == model_digest
            and observed_checkpoint.get("restored_model_parameter_digest") == model_digest
        )
        checkpoint_aggregate.update(checkpoint_id.encode("ascii"))
        checkpoint_aggregate.update(len(payload_bytes).to_bytes(8, "big"))
        checkpoint_aggregate.update(payload_bytes)
        checkpoint_records[checkpoint_id] = {
            "path": path.name,
            "sha256": hashlib.sha256(payload_bytes).hexdigest(),
            "bytes": len(payload_bytes),
            "identity": dict(identity),
        }
    zero_digests = checkpoint_payloads["update-0"]["digests"]
    one_digests = checkpoint_payloads["update-1"]["digests"]
    if zero_digests["parameter_initialization"] == "" or (
        zero_digests["training_tape"] != _panel_digest(panel.train, environment=False)
        or zero_digests["action_uniform"] != sha256_json(address_rows)
        or one_digests["training_tape"] != zero_digests["training_tape"]
        or one_digests["action_uniform"] != zero_digests["action_uniform"]
    ):
        raise B0ContractError("independent checkpoint digest binding audit failed")
    if not checkpoint_roundtrip_observed:
        raise B0ContractError("independent checkpoint roundtrip evidence audit failed")
    if (
        model_parameter_digest_from_state(checkpoint_payloads["update-0"]["model_state"])
        == model_parameter_digest_from_state(checkpoint_payloads["update-1"]["model_state"])
    ):
        raise B0ContractError("independent parameter-update audit found unchanged bytes")

    heldout_state = records.get("heldout_state_observations")
    heldout_unchanged = bool(
        isinstance(heldout_state, Mapping)
        and heldout_state.get("model_digest_before")
        == heldout_state.get("model_digest_after")
        and heldout_state.get("optimizer_digest_before")
        == heldout_state.get("optimizer_digest_after")
        and heldout_state.get("training_mode_before")
        == heldout_state.get("training_mode_after")
        and heldout_state.get("consumed_uniform_rows") == []
    )
    if not heldout_unchanged:
        raise B0ContractError("independent held-out adaptation audit failed")

    from .evaluator import aggregate_evaluations, evaluate_episode

    evaluation_records = [
        evaluate_episode(
            tape,
            [Action[name] for name in action_names],
        )
        for tape, action_names in zip(heldout, evaluation_actions, strict=True)
    ]
    evaluation_diagnostics = aggregate_evaluations(evaluation_records)

    module_root = Path(__file__).resolve().parent
    recomputed_digests = {
        "configuration": sha256_json(frozen_configuration()),
        "environment_law": _file_law_digest(
            (module_root / "host.py", module_root / "state.py", module_root / "ledger.py")
        ),
        "token_law": _file_law_digest((module_root / "contract.py", module_root / "token.py")),
        "environment_train_tapes": _panel_digest(panel.train, environment=True),
        "primitive_train_histories": _panel_digest(panel.train, environment=False),
        "action_uniforms": sha256_json(address_rows),
        "parameter_initialization": zero_digests["parameter_initialization"],
        "minibatch_order": one_digests["minibatch_order"],
        "evaluation_tapes": _panel_digest(heldout, environment=False),
        "adapter_law": sha256_json(
            {"arm": expected_arm, "adapter": adapter_type.__name__}
        ),
        "checkpoint_bytes": checkpoint_aggregate.hexdigest(),
        "adapter_work": sha256_json(dataclass_asdict(total_work)),
    }
    recomputed_audits = {
        "event_order_causality": clock_valid,
        "ledger_oracle_arithmetic": oracle_unique,
        "action_masks": rollout_observations.get("uniforms_consumed_rows")
        == [decision_rows for _ in range(8)],
        "adapter_replay": total_work is not None,
        "primitive_history_parity": observed_train_tapes == expected_train_tapes,
        "heldout_separation": heldout_separated,
        "rng_address_independence": all(
            expected_arm not in json.dumps(row["address"]) for row in address_rows
        ),
        "update_evaluation_counters": (
            counters.get("train_transitions") == 1216
            and evaluation_diagnostics["decision_count"] == 192
        ),
        "checkpoint_roundtrip": checkpoint_roundtrip_observed,
        "parameter_update_parity": (
            checkpoint_payloads["update-0"]["counters"]["adam_steps"] == 0
            and checkpoint_payloads["update-1"]["counters"]["adam_steps"] == 16
        ),
        "evaluation_parity": heldout_unchanged
        and evaluation_diagnostics["episode_count"] == 8,
    }
    result["digests"] = recomputed_digests
    result["audits"] = recomputed_audits
    result["counts"] = dict(EXPECTED_COUNTS)
    result["checkpoint_identities"] = list(CHECKPOINT_IDENTITIES)
    result["numerical_finite"] = _finite_tree(
        {"records": records, "stage_measurements": result.get("stage_measurements")}
    )
    result["records"] = {
        **dict(records),
        "train_episode_ids": list(TRAIN_EPISODE_IDS),
        "evaluation_roots": {
            "EVAL_STOCHASTIC": list(EVAL_STOCHASTIC_IDS),
            "EVAL_MOTIF": list(EVAL_MOTIF_IDS),
        },
        "update_zero_checks": dict(records.get("rollout_observations", {})),
        "post_update_checks": dict(records.get("trainer_observations", {})),
        "diagnostics": {
            "heldout_state": dict(records.get("heldout_state_observations", {})),
            "evaluation": evaluation_diagnostics,
            "training_action_trace_count": len(training_actions),
            "evaluation_action_trace_count": len(evaluation_actions),
        },
        "checkpoints": checkpoint_records,
        "audit_provenance": "PARENT_RECOMPUTED_FROM_CANONICAL_LAWS_RAW_ACTIONS_AND_CHECKPOINTS",
    }
    return validate_arm_result(result, expected_arm=expected_arm)


def _incident_category(exc: BaseException) -> str:
    if isinstance(exc, FileExistsError):
        return "PUBLICATION_COLLISION"
    if isinstance(exc, TelemetryError):
        return "RESOURCE_OR_TELEMETRY_FAILURE"
    if "nonfinite" in str(exc).lower():
        return "NONFINITE_FAILURE"
    if "parity" in str(exc).lower():
        return "PARITY_FAILURE"
    return "PARTIAL_OR_CONFORMANCE_FAILURE"


def _atomic_create_json(path: Path, value: Mapping[str, Any]) -> None:
    from .artifact import canonical_json_bytes

    if path.exists():
        raise FileExistsError(f"create-only control record exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json_bytes(value) + b"\n")
        stream.flush()
        import os

        os.fsync(stream.fileno())


def _kill_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, shell=False, timeout=10,
        )
    else:  # pragma: no cover - declared runtime is Windows
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def supervise_child(
    command: Sequence[str], *, scratch_root: Path, durable_root: Path,
    result_path: Path, stdout_path: Path, stderr_path: Path,
    caps: ResourceCaps = ResourceCaps(), interval_seconds: float = 0.05,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one child and enforce live hard caps from the parent process."""

    supervisor_incident_path = result_path.with_name("supervisor-incident.json")
    if result_path.exists() or supervisor_incident_path.exists():
        raise FileExistsError("create-only worker result already exists")
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(command), stdout=stdout, stderr=stderr, shell=False, cwd=REPO_ROOT
        )
        monitor = ProcessTreeMonitor(
            scratch_root,
            durable_root,
            worker_count=1,
            threads_per_worker=1,
            interval_seconds=interval_seconds,
            root_pid=process.pid,
        )
        try:
            monitor.begin()
        except BaseException:
            _kill_process_tree(process)
            raise
        cap_failures: tuple[str, ...] = ()
        try:
            while process.poll() is None:
                cap_failures = monitor.poll_caps(caps=caps)
                if cap_failures:
                    _kill_process_tree(process)
                    break
                time.sleep(interval_seconds)
        finally:
            if process.poll() is None:
                _kill_process_tree(process)
        if cap_failures:
            _atomic_create_json(
                supervisor_incident_path,
                monitor.incident_snapshot(
                    reason="LIVE_RESOURCE_CAP_TERMINATION",
                    cap_failures=cap_failures,
                ),
            )
            raise TelemetryError(f"live resource cap exceeded: {','.join(cap_failures)}")
        if process.returncode != 0:
            _atomic_create_json(
                supervisor_incident_path,
                monitor.incident_snapshot(
                    reason=f"WORKER_EXIT_{process.returncode}",
                ),
            )
            raise B0ContractError(f"canonical B0 worker exited {process.returncode}")
        if not result_path.is_file():
            _atomic_create_json(
                supervisor_incident_path,
                monitor.incident_snapshot(reason="WORKER_RESULT_ABSENT"),
            )
            raise B0ContractError("canonical worker produced no create-only result")
        try:
            raw_result = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _atomic_create_json(
                supervisor_incident_path,
                monitor.incident_snapshot(reason="WORKER_RESULT_UNREADABLE"),
            )
            raise B0ContractError("canonical worker result is unreadable") from exc
        telemetry = monitor.finish(
            scientific_work_transitions=(
                EXPECTED_COUNTS["train_transitions"]
                + EXPECTED_COUNTS["evaluation_transitions"]
            ),
            stage_measurements=raw_result.get("stage_measurements", []),
        )
    return raw_result, validate_telemetry(telemetry, caps=caps)


def _worker_request(
    *, staging: Path, attempt_id: str, arm: str, arm_index: int,
    receipt_path: Path, implementation_commit: str,
) -> tuple[dict[str, Any], Path, Path, Path, Path, Path]:
    scratch = staging / "scratch" / f"arm-{arm_index:02d}"
    durable = staging / "arms" / f"{arm_index:02d}-{arm}"
    scratch.mkdir(parents=True)
    durable.mkdir(parents=True)
    worker_root = staging / "workers" / f"{arm_index:02d}-{arm}"
    worker_root.mkdir(parents=True)
    request_path = worker_root / "request.json"
    result_path = worker_root / "result.json"
    error_path = worker_root / "error.json"
    payload = {
        "schema": "cbsc_omrc_b01_b0_worker_request_v1",
        "attempt_id": attempt_id,
        "attempt_root": str(staging),
        "implementation_commit": implementation_commit,
        "arm": arm,
        "seed": B0_SEED,
        "train_episode_ids": list(TRAIN_EPISODE_IDS),
        "eval_stochastic_ids": list(EVAL_STOCHASTIC_IDS),
        "eval_motif_ids": list(EVAL_MOTIF_IDS),
        "scratch_root": str(scratch),
        "durable_root": str(durable),
        "admission_receipt_path": str(receipt_path),
        "resource_caps": ResourceCaps().as_dict(),
    }
    _atomic_create_json(request_path, payload)
    return payload, request_path, result_path, error_path, scratch, durable


def run_b0(
    *, final_path: Path, implementation_commit: str, run_name: str = B0_RUN_NAME
) -> Path:
    """Formal canonical B0 path; no engine, preflight, monitor, or publisher injection."""

    refuse_non_b0(run_name)
    source_receipt = verify_source_conformance(implementation_commit)
    final_path = Path(final_path)
    from .artifact import ensure_confined

    ensure_confined(final_path, CONFINED_ROOT)
    attempt_id = f"b0-{B0_SEED}-{uuid.uuid4().hex}"
    incident_root = final_path.parent / "incidents"
    staging: Path | None = None
    completed: list[str] = []
    try:
        staging = create_staging_directory(final_path, allowed_root=CONFINED_ROOT)
        (staging / "scratch").mkdir()
        arm_results: list[dict[str, Any]] = []
        telemetry_records: list[dict[str, Any]] = []
        admissions: list[dict[str, Any]] = []
        for arm_index, arm in enumerate(ARMS):
            receipt_path = staging / "admissions" / f"{arm_index:02d}-{arm}-admission.json"
            receipt_path.parent.mkdir(exist_ok=True)
            receipt = run_memory_preflight(
                receipt_path,
                arm,
                attempt_id=attempt_id,
                implementation_commit=implementation_commit,
                source_conformance_sha256=source_receipt["source_conformance_sha256"],
            )
            _, request_path, result_path, error_path, scratch, durable = _worker_request(
                staging=staging,
                attempt_id=attempt_id,
                arm=arm,
                arm_index=arm_index,
                receipt_path=receipt_path,
                implementation_commit=implementation_commit,
            )
            command = [
                str(Path(sys.executable).resolve()), "-m", CANONICAL_WORKER_MODULE,
                "--request", str(request_path), "--result", str(result_path),
                "--error", str(error_path),
            ]
            raw_result, telemetry = supervise_child(
                command,
                scratch_root=scratch,
                durable_root=staging,
                result_path=result_path,
                stdout_path=result_path.with_name("stdout.log"),
                stderr_path=result_path.with_name("stderr.log"),
            )
            result = recompute_arm_evidence(raw_result, expected_arm=arm, arm_root=durable)
            if telemetry["worker_count"] != 1 or telemetry["threads_per_worker"] != 1:
                raise B0ContractError("measured canonical worker topology differs")
            admissions.append(
                {
                    "arm": arm,
                    "receipt_path": str(receipt_path.relative_to(staging)),
                    "receipt": receipt,
                }
            )
            arm_results.append(result)
            telemetry_records.append(telemetry)
            completed.append(arm)
            if scratch.exists():
                shutil.rmtree(scratch)
        parity = validate_cross_arm_parity(arm_results)
        scratch_root = staging / "scratch"
        if scratch_root.exists():
            shutil.rmtree(scratch_root)
        if directory_size(staging) > DURABLE_CAP_BYTES:
            raise TelemetryError("resource cap exceeded: durable_high_water_bytes")
        manifest = {
            "schema": RESULT_SCHEMA,
            "object_id": OBJECT_ID,
            "clarification_id": CLARIFICATION_ID,
            "run_name": B0_RUN_NAME,
            "implementation_commit": implementation_commit,
            "source_conformance": source_receipt,
            "pinned_evidence_ref": PINNED_EVIDENCE_REF,
            "configuration_sha256": sha256_json(frozen_configuration()),
            "arms": list(ARMS),
            "seeds": [B0_SEED],
            "checkpoint_identities": list(CHECKPOINT_IDENTITIES),
            "counts": {"per_arm": dict(EXPECTED_COUNTS), "arm_count": 4},
            "arm_records": arm_results,
            "parity_audits": parity,
            "resource_caps": ResourceCaps().as_dict(),
            "resource_admissions": admissions,
            "telemetry": telemetry_records,
            "numerical_finiteness_audit": True,
            "incident_references": [],
            "scientific_branch": None,
            "claim_ceiling": NO_SCIENCE_CLAIM,
            "performance_disposition": "PILOT_ONLY",
        }
        return publish_complete(staging, final_path, manifest, allowed_root=CONFINED_ROOT)
    except BaseException as exc:
        if staging is not None and staging.exists():
            publish_incident_bundle(
                staging=staging,
                incident_root=incident_root,
                allowed_root=CONFINED_ROOT,
                attempt_id=attempt_id,
                run_name=run_name,
                category=_incident_category(exc),
                detail=f"{type(exc).__name__}: {exc}",
                completed_arms=completed,
            )
        else:
            publish_incident(
                incident_root=incident_root,
                allowed_root=CONFINED_ROOT,
                attempt_id=attempt_id,
                run_name=run_name,
                category=_incident_category(exc),
                detail=f"{type(exc).__name__}: {exc}",
                completed_arms=completed,
            )
        raise


__all__ = [
    "ARMS",
    "B0ArmRequest",
    "B0ContractError",
    "B0Plan",
    "B0_RUN_NAME",
    "B0_SEED",
    "CHECKPOINT_IDENTITIES",
    "EVAL_MOTIF_IDS",
    "EVAL_STOCHASTIC_IDS",
    "EXPECTED_COUNTS",
    "TRAIN_EPISODE_IDS",
    "frozen_configuration",
    "refuse_non_b0",
    "run_assess_preflight",
    "run_b0",
    "run_memory_preflight",
    "validate_arm_result",
    "validate_cross_arm_parity",
    "validate_memory_receipt",
    "verify_source_conformance",
]
