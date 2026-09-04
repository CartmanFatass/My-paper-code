"""Fail-closed orchestration for a future exact revision-02 empirical lease.

There is no CLI entry point.  The function below is deliberately unusable
without an exact active Root lease, the accepted ABI-v2 native guard, and all
future materialization services.  It performs no retry, fallback, search,
coordinate repair, or partial publication.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path
from typing import Protocol

from .frontier import (
    CheckpointCompletion,
    CheckpointReceipt,
    FrontierContractError,
    GlobalCheckpointBarrier,
    LEARNED_ARMS,
    load_cm_technical_acceptance,
    load_completion_inventory,
    publish_completion_inventory,
    require_global_checkpoint_barrier,
)
from .inference import complete_inference
from .lease import (
    ActivityPermit,
    COORDINATE_PLAN_DIGEST,
    EVALUATE_PHASE,
    TRAIN_PHASE,
    canonical_digest,
    canonical_absolute_path_key,
    coordinate_proposal,
    validate_coordinate_proposal,
    validate_lease,
    validate_lease_envelope,
)
from .preactivity import require_direction_cpp_batched_production
from .rng import (
    DOMAIN_LABELS,
    EmpiricalRNG,
    domain_key,
    identity_digest_set,
    replicate_key,
    sample_fresh_master,
    sha256_hex,
)


class RunnerContractError(RuntimeError):
    pass


@dataclass(frozen=True)
class BlindedFrontierHandle:
    replicate: int
    arm: str
    coordinate_digest: str
    frontier_digest: str
    partial_inspection_permitted: bool = False

    def validate(self) -> None:
        if (self.replicate, self.arm) not in {
            (replicate, arm) for replicate in range(18) for arm in LEARNED_ARMS
        }:
            raise RunnerContractError("frontier handle slot is unregistered")
        if self.coordinate_digest != COORDINATE_PLAN_DIGEST:
            raise RunnerContractError("frontier handle coordinate differs")
        if self.partial_inspection_permitted is not False:
            raise RunnerContractError("frontier handle is not blinded")
        if len(self.frontier_digest) != 64:
            raise RunnerContractError("frontier handle digest is invalid")
        try:
            int(self.frontier_digest, 16)
        except ValueError as error:
            raise RunnerContractError("frontier handle digest is invalid") from error


class FrontierFactory(Protocol):
    def __call__(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
    ) -> BlindedFrontierHandle: ...


class SlotTrainer(Protocol):
    def __call__(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        frontier: BlindedFrontierHandle,
    ) -> CheckpointReceipt: ...


class EvaluationPanel(Protocol):
    def __call__(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
        checkpoints: Sequence[CheckpointReceipt],
    ) -> Sequence[Mapping[str, object]]: ...


class SupportPanel(Protocol):
    def __call__(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
    ) -> Sequence[Mapping[str, object]]: ...


class AtomicPublisher(Protocol):
    def __call__(self, permit: ActivityPermit, complete_result: Mapping[str, object]) -> object: ...


@dataclass(frozen=True)
class RunnerServices:
    create_frontier: FrontierFactory
    train_slot: SlotTrainer
    evaluate_panel: EvaluationPanel
    support_panel: SupportPanel
    publish_atomic: AtomicPublisher


class MasterSealer(Protocol):
    def seal(self, master: bytes, *, context: bytes) -> bytes: ...

    def unseal(self, sealed: bytes, *, context: bytes) -> bytes: ...


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


class WindowsDPAPIMasterSealer:
    """Same-user Windows DPAPI seal; no portable or plaintext fallback."""

    _UI_FORBIDDEN = 0x1

    @staticmethod
    def _blob(value: bytes) -> tuple[_DATA_BLOB, object]:
        buffer = ctypes.create_string_buffer(value)
        blob = _DATA_BLOB(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
        return blob, buffer

    @staticmethod
    def _copy_and_free(blob: _DATA_BLOB) -> bytes:
        value = ctypes.string_at(blob.pbData, blob.cbData)
        ctypes.windll.kernel32.LocalFree(blob.pbData)
        return value

    def seal(self, master: bytes, *, context: bytes) -> bytes:
        if os.name != "nt" or len(master) != 32:
            raise RunnerContractError("Windows DPAPI and a 256-bit master are required")
        source, source_buffer = self._blob(master)
        entropy, entropy_buffer = self._blob(context)
        output = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(source), None, ctypes.byref(entropy), None, None,
            self._UI_FORBIDDEN, ctypes.byref(output),
        )
        _ = (source_buffer, entropy_buffer)
        if not ok:
            raise RunnerContractError("DPAPI master sealing failed")
        return self._copy_and_free(output)

    def unseal(self, sealed: bytes, *, context: bytes) -> bytes:
        if os.name != "nt" or not sealed:
            raise RunnerContractError("Windows DPAPI sealed master is required")
        source, source_buffer = self._blob(sealed)
        entropy, entropy_buffer = self._blob(context)
        output = _DATA_BLOB()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source), None, ctypes.byref(entropy), None, None,
            self._UI_FORBIDDEN, ctypes.byref(output),
        )
        _ = (source_buffer, entropy_buffer)
        if not ok:
            raise RunnerContractError("DPAPI master unsealing failed")
        value = self._copy_and_free(output)
        if len(value) != 32:
            raise RunnerContractError("unsealed master is not 256 bits")
        return value


@dataclass(frozen=True, repr=False)
class RunIdentitySession:
    record_digest: str
    master_digest: str
    replicate_key_digests: tuple[str, ...]
    domain_key_digests: tuple[tuple[str, ...], ...]
    origin_lease_id: str
    resumed_under_lease_id: str
    _master: bytes

    def empirical_rng(self, permit: ActivityPermit) -> EmpiricalRNG:
        permit.require_active()
        return EmpiricalRNG(self._master, permit)


class TrainingPhaseServices(Protocol):
    def create_or_resume_frontier(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        replicate: int,
        arm: str,
        run_identity_digest: str,
    ) -> BlindedFrontierHandle: ...

    def train_slot(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        frontier: BlindedFrontierHandle,
        run_identity_digest: str,
    ) -> CheckpointCompletion: ...


class EvaluationPhaseServices(Protocol):
    def evaluate_panel(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
        checkpoints: Sequence[CheckpointReceipt],
    ) -> Sequence[Mapping[str, object]]: ...

    def support_panel(
        self,
        permit: ActivityPermit,
        rng: EmpiricalRNG,
        barrier: GlobalCheckpointBarrier,
    ) -> Sequence[Mapping[str, object]]: ...

    def publish_atomic(
        self, permit: ActivityPermit, complete_result: Mapping[str, object]
    ) -> object: ...


@dataclass(frozen=True)
class TrainingPhaseResult:
    run_identity_digest: str
    completion_inventory_sha256: str
    completion_count: int
    resumed_run_identity: bool
    technically_accepted: bool = False


@dataclass(frozen=True)
class EvaluationPhaseResult:
    run_identity_digest: str
    cm_acceptance_sha256: str
    publication: object


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _atomic_create_json(path: Path, value: Mapping[str, object]) -> str:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = _canonical_bytes(value)
    temporary = Path(str(target) + f".{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise RunnerContractError("create-only lifecycle record already exists") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(encoded).hexdigest()


def _require_bound_path(permit: ActivityPermit, field: str, supplied: Path) -> Path:
    permit.require_active()
    if not isinstance(permit.paths, Mapping) or field not in permit.paths:
        raise RunnerContractError("activity permit lacks bound lifecycle paths")
    expected = Path(str(permit.paths[field])).resolve()
    actual = supplied.resolve()
    if canonical_absolute_path_key(actual) != canonical_absolute_path_key(expected):
        raise RunnerContractError(f"supplied {field} differs from the exact lease")
    return actual


def _run_binding(permit: ActivityPermit, lease: Mapping[str, object]) -> dict[str, object]:
    permit.require_active()
    registry = lease.get("occupied_digest_registry")
    return {
        "stage": lease.get("stage"),
        "coordinate_plan_digest": permit.coordinate_plan_digest,
        "source_manifest_sha256": permit.source_manifest_sha256,
        "card_sha256": permit.card_sha256,
        "native_binding_digest": permit.native_binding_digest,
        "paths": dict(permit.paths or {}),
        "occupied_digest_registry": None if registry is None else dict(registry),
        "cpu_only": True,
        "gpu_count": 0,
        "torch_threads": 1,
    }


def _identity_public_payload(master: bytes) -> tuple[str, tuple[str, ...], tuple[tuple[str, ...], ...]]:
    master_digest = sha256_hex(master)
    replicate_digests = tuple(
        sha256_hex(replicate_key(master, replicate)) for replicate in range(18)
    )
    domain_digests = tuple(
        tuple(
            sha256_hex(domain_key(master, replicate, domain))
            for domain in DOMAIN_LABELS
        )
        for replicate in range(18)
    )
    return master_digest, replicate_digests, domain_digests


def _run_identity_context(binding: Mapping[str, object]) -> bytes:
    return b"SCDMP-UAV-SP-R02-RUN-IDENTITY-SEAL-v1\0" + _canonical_bytes(binding)


def _run_identity_payload(
    *,
    binding: Mapping[str, object],
    origin_lease: Mapping[str, object],
    master: bytes,
    sealer: MasterSealer,
) -> dict[str, object]:
    master_digest, replicate_digests, domain_digests = _identity_public_payload(master)
    context = _run_identity_context(binding)
    sealed = sealer.seal(master, context=context)
    if not isinstance(sealed, bytes) or not sealed:
        raise RunnerContractError("master sealer returned an empty/non-byte seal")
    return {
        "schema": "SCDMP_UAV_SP_R02_BLINDED_RUN_IDENTITY_V1",
        "binding": dict(binding),
        "origin_lease": {
            "lease_id": origin_lease.get("lease_id"),
            "issued_at": origin_lease.get("issued_at"),
            "expires_at": origin_lease.get("expires_at"),
            "phase": origin_lease.get("phase"),
        },
        "master_digest": master_digest,
        "replicate_key_digests": list(replicate_digests),
        "domain_labels": list(DOMAIN_LABELS),
        "domain_key_digests": [list(row) for row in domain_digests],
        "sealed_master": {
            "kind": type(sealer).__name__,
            "encoding": "base64",
            "ciphertext": base64.b64encode(sealed).decode("ascii"),
        },
        "partial_inspection_permitted": False,
    }


def _load_run_identity(
    *,
    path: Path,
    binding: Mapping[str, object],
    current_lease_id: str,
    sealer: MasterSealer,
) -> RunIdentitySession:
    raw = path.resolve().read_bytes()
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RunnerContractError("run identity record is unreadable") from error
    if not isinstance(value, Mapping) or value.get("schema") != "SCDMP_UAV_SP_R02_BLINDED_RUN_IDENTITY_V1":
        raise RunnerContractError("run identity record schema differs")
    if value.get("binding") != dict(binding):
        raise RunnerContractError("run identity scientific/source/path binding differs")
    origin = value.get("origin_lease")
    sealed = value.get("sealed_master")
    if not isinstance(origin, Mapping) or not isinstance(sealed, Mapping):
        raise RunnerContractError("run identity provenance or master seal is absent")
    if set(sealed) != {"kind", "encoding", "ciphertext"} or sealed.get("kind") != type(sealer).__name__ or sealed.get("encoding") != "base64":
        raise RunnerContractError("run identity master seal contract differs")
    try:
        ciphertext = base64.b64decode(str(sealed["ciphertext"]), validate=True)
    except (ValueError, TypeError) as error:
        raise RunnerContractError("run identity master seal encoding differs") from error
    master = sealer.unseal(ciphertext, context=_run_identity_context(binding))
    if len(master) != 32:
        raise RunnerContractError("unsealed run identity master is not 256 bits")
    master_digest, replicate_digests, domain_digests = _identity_public_payload(master)
    if value.get("master_digest") != master_digest:
        raise RunnerContractError("run identity master digest changed")
    if value.get("replicate_key_digests") != list(replicate_digests):
        raise RunnerContractError("run identity replicate digests changed")
    if value.get("domain_labels") != list(DOMAIN_LABELS) or value.get("domain_key_digests") != [list(row) for row in domain_digests]:
        raise RunnerContractError("run identity domain digests changed")
    return RunIdentitySession(
        record_digest=hashlib.sha256(raw).hexdigest(),
        master_digest=master_digest,
        replicate_key_digests=replicate_digests,
        domain_key_digests=domain_digests,
        origin_lease_id=str(origin.get("lease_id")),
        resumed_under_lease_id=current_lease_id,
        _master=master,
    )


def prepare_or_resume_run_identity(
    *,
    permit: ActivityPermit,
    lease: Mapping[str, object],
    run_identity_path: Path,
    occupied_identity_digests: Iterable[str],
    master_source: Callable[[int], bytes],
    master_sealer: MasterSealer,
) -> tuple[RunIdentitySession, bool]:
    target = _require_bound_path(permit, "run_identity_path", run_identity_path)
    binding = _run_binding(permit, lease)
    if target.is_file():
        return (
            _load_run_identity(
                path=target,
                binding=binding,
                current_lease_id=permit.lease_id,
                sealer=master_sealer,
            ),
            True,
        )
    permit.require_phase(TRAIN_PHASE)
    if not 1 <= permit.workers <= 4:
        raise RunnerContractError("TRAIN worker count must remain in [1,4]")
    master = sample_fresh_master(
        permit,
        occupied_digests=occupied_identity_digests,
        source=master_source,
    )
    payload = _run_identity_payload(
        binding=binding,
        origin_lease=lease,
        master=master,
        sealer=master_sealer,
    )
    digest = _atomic_create_json(target, payload)
    session = _load_run_identity(
        path=target,
        binding=binding,
        current_lease_id=permit.lease_id,
        sealer=master_sealer,
    )
    if session.record_digest != digest:
        raise RunnerContractError("persisted run identity digest changed after create")
    return session, False


def _merge_complete_packets(
    evaluation: Sequence[Mapping[str, object]],
    support: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if len(evaluation) != 18 or len(support) != 18:
        raise RunnerContractError("evaluation and support must each return all 18 replicates")
    evaluation_map = {int(row["replicate"]): row for row in evaluation}
    support_map = {int(row["replicate"]): row for row in support}
    if set(evaluation_map) != set(range(18)) or set(support_map) != set(range(18)):
        raise RunnerContractError("evaluation/support replicate inventory differs")
    if len(evaluation_map) != 18 or len(support_map) != 18:
        raise RunnerContractError("evaluation/support replicate identity is duplicated")
    return [
        {
            "replicate": replicate,
            "controllers": evaluation_map[replicate]["controllers"],
            "support": support_map[replicate]["support"],
        }
        for replicate in range(18)
    ]


def _default_native_guard(*, batch_width: int) -> Mapping[str, object]:
    return require_direction_cpp_batched_production(batch_width=batch_width)


def _create_or_validate_terminal(path: Path, payload: Mapping[str, object]) -> str:
    encoded = _canonical_bytes(payload)
    expected_digest = hashlib.sha256(encoded).hexdigest()
    if path.is_file():
        if path.read_bytes() != encoded:
            raise RunnerContractError("phase terminal record differs on resume")
        return expected_digest
    return _atomic_create_json(path, payload)


def _run_training_with_permit(
    *,
    permit: ActivityPermit,
    lease: Mapping[str, object],
    services: TrainingPhaseServices,
    run_identity_path: Path,
    completion_inventory_path: Path,
    train_terminal_path: Path,
    occupied_identity_digests: Iterable[str],
    master_source: Callable[[int], bytes],
    master_sealer: MasterSealer,
) -> TrainingPhaseResult:
    permit.require_phase(TRAIN_PHASE)
    identity_path = _require_bound_path(permit, "run_identity_path", run_identity_path)
    completion_path = _require_bound_path(
        permit, "completion_inventory_path", completion_inventory_path
    )
    terminal_path = _require_bound_path(permit, "train_terminal_path", train_terminal_path)
    session, resumed = prepare_or_resume_run_identity(
        permit=permit,
        lease=lease,
        run_identity_path=identity_path,
        occupied_identity_digests=occupied_identity_digests,
        master_source=master_source,
        master_sealer=master_sealer,
    )
    source_sha = str(permit.source_manifest_sha256)
    result_root = Path(str((permit.paths or {})["result_root"]))
    if completion_path.is_file():
        completions = load_completion_inventory(
            completion_path,
            result_root=result_root,
            run_identity_digest=session.record_digest,
            source_manifest_sha256=source_sha,
        )
        completion_sha = hashlib.sha256(completion_path.read_bytes()).hexdigest()
    else:
        rng = session.empirical_rng(permit)
        frontiers: list[BlindedFrontierHandle] = []
        for replicate in range(18):
            for arm in LEARNED_ARMS:
                handle = services.create_or_resume_frontier(
                    permit, rng, replicate, arm, session.record_digest
                )
                handle.validate()
                if (handle.replicate, handle.arm) != (replicate, arm):
                    raise RunnerContractError("frontier service changed the frozen slot")
                frontiers.append(handle)

        def train(handle: BlindedFrontierHandle) -> CheckpointCompletion:
            completion = services.train_slot(
                permit, rng, handle, session.record_digest
            )
            if not isinstance(completion, CheckpointCompletion):
                raise RunnerContractError("training service did not return a checkpoint completion")
            completion.validate(result_root=result_root, verify_checkpoint=True)
            if (completion.replicate, completion.arm) != (handle.replicate, handle.arm):
                raise RunnerContractError("training service changed the frozen slot")
            if completion.run_identity_digest != session.record_digest:
                raise RunnerContractError("training completion changed run identity")
            return completion

        with ThreadPoolExecutor(max_workers=permit.workers) as executor:
            futures = [executor.submit(train, handle) for handle in frontiers]
            completions = tuple(future.result() for future in futures)
        completions = tuple(
            sorted(completions, key=lambda item: (item.replicate, LEARNED_ARMS.index(item.arm)))
        )
        completion_sha = publish_completion_inventory(
            completion_path,
            completions,
            run_identity_digest=session.record_digest,
            source_manifest_sha256=source_sha,
        )
    terminal_payload = {
        "schema": "SCDMP_UAV_SP_R02_TRAIN_TERMINAL_V1",
        "phase": TRAIN_PHASE,
        "origin_lease_id": session.origin_lease_id,
        "run_identity_digest": session.record_digest,
        "completion_inventory_sha256": completion_sha,
        "completion_count": len(completions),
        "technically_accepted": False,
        "evaluation_started": False,
    }
    _create_or_validate_terminal(terminal_path, terminal_payload)
    return TrainingPhaseResult(
        run_identity_digest=session.record_digest,
        completion_inventory_sha256=completion_sha,
        completion_count=len(completions),
        resumed_run_identity=resumed,
        technically_accepted=False,
    )


def run_training_phase(
    *,
    lease: Mapping[str, object],
    now: datetime,
    services: TrainingPhaseServices,
    run_identity_path: Path,
    completion_inventory_path: Path,
    train_terminal_path: Path,
    cached_native_guard: Callable[..., Mapping[str, object]],
    occupied_identity_digests: Iterable[str],
    master_source: Callable[[int], bytes] = os.urandom,
    master_sealer: MasterSealer | None = None,
    source_manifest_path: Path | None = None,
) -> TrainingPhaseResult:
    permit = validate_lease(
        lease,
        now=now,
        package_root=Path(__file__).resolve().parent,
        native_guard=cached_native_guard,
        manifest_path=source_manifest_path,
    )
    return _run_training_with_permit(
        permit=permit,
        lease=lease,
        services=services,
        run_identity_path=run_identity_path,
        completion_inventory_path=completion_inventory_path,
        train_terminal_path=train_terminal_path,
        occupied_identity_digests=occupied_identity_digests,
        master_source=master_source,
        master_sealer=master_sealer or WindowsDPAPIMasterSealer(),
    )


def _run_evaluation_with_permit(
    *,
    permit: ActivityPermit,
    lease: Mapping[str, object],
    services: EvaluationPhaseServices,
    run_identity_path: Path,
    completion_inventory_path: Path,
    cm_acceptance_path: Path,
    result_path: Path,
    evaluation_terminal_path: Path,
    validity: Mapping[str, bool],
    master_sealer: MasterSealer,
) -> EvaluationPhaseResult:
    permit.require_phase(EVALUATE_PHASE)
    identity_path = _require_bound_path(permit, "run_identity_path", run_identity_path)
    completion_path = _require_bound_path(
        permit, "completion_inventory_path", completion_inventory_path
    )
    acceptance_path = _require_bound_path(permit, "cm_acceptance_path", cm_acceptance_path)
    _require_bound_path(permit, "result_path", result_path)
    terminal_path = _require_bound_path(
        permit, "evaluation_terminal_path", evaluation_terminal_path
    )
    if not identity_path.is_file():
        raise RunnerContractError("EVALUATE requires the existing blinded run identity")
    binding = _run_binding(permit, lease)
    session = _load_run_identity(
        path=identity_path,
        binding=binding,
        current_lease_id=permit.lease_id,
        sealer=master_sealer,
    )
    source_sha = str(permit.source_manifest_sha256)
    result_root = Path(str((permit.paths or {})["result_root"]))
    # Completion and independent CM acceptance both close before RNG/model loading.
    load_completion_inventory(
        completion_path,
        result_root=result_root,
        run_identity_digest=session.record_digest,
        source_manifest_sha256=source_sha,
    )
    receipts, barrier = load_cm_technical_acceptance(
        acceptance_path,
        completion_inventory_path=completion_path,
        run_identity_digest=session.record_digest,
        source_manifest_sha256=source_sha,
    )
    rng = session.empirical_rng(permit)
    evaluation = services.evaluate_panel(permit, rng, barrier, receipts)
    support = services.support_panel(permit, rng, barrier)
    packets = _merge_complete_packets(evaluation, support)
    inference = complete_inference(packets, validity=validity)
    acceptance_sha = hashlib.sha256(acceptance_path.read_bytes()).hexdigest()
    complete_result = {
        "schema": "SCDMP_UAV_SP_R02_ATOMIC_RESULT_V2",
        "coordinate_plan_digest": permit.coordinate_plan_digest,
        "source_manifest_sha256": source_sha,
        "run_identity_digest": session.record_digest,
        "cm_acceptance_sha256": acceptance_sha,
        "replicate_packets": packets,
        "inference": inference,
        "complete_atomic_panel": True,
        "partial_inspection_permitted": False,
    }
    publication = services.publish_atomic(permit, complete_result)
    terminal_payload = {
        "schema": "SCDMP_UAV_SP_R02_EVALUATE_TERMINAL_V1",
        "phase": EVALUATE_PHASE,
        "origin_lease_id": session.origin_lease_id,
        "run_identity_digest": session.record_digest,
        "cm_acceptance_sha256": acceptance_sha,
        "complete_atomic_panel": True,
    }
    _create_or_validate_terminal(terminal_path, terminal_payload)
    return EvaluationPhaseResult(
        run_identity_digest=session.record_digest,
        cm_acceptance_sha256=acceptance_sha,
        publication=publication,
    )


def run_evaluation_phase(
    *,
    lease: Mapping[str, object],
    now: datetime,
    services: EvaluationPhaseServices,
    run_identity_path: Path,
    completion_inventory_path: Path,
    cm_acceptance_path: Path,
    result_path: Path,
    evaluation_terminal_path: Path,
    cached_native_guard: Callable[..., Mapping[str, object]],
    validity: Mapping[str, bool],
    master_sealer: MasterSealer | None = None,
    source_manifest_path: Path | None = None,
) -> EvaluationPhaseResult:
    permit = validate_lease(
        lease,
        now=now,
        package_root=Path(__file__).resolve().parent,
        native_guard=cached_native_guard,
        manifest_path=source_manifest_path,
    )
    return _run_evaluation_with_permit(
        permit=permit,
        lease=lease,
        services=services,
        run_identity_path=run_identity_path,
        completion_inventory_path=completion_inventory_path,
        cm_acceptance_path=cm_acceptance_path,
        result_path=result_path,
        evaluation_terminal_path=evaluation_terminal_path,
        validity=validity,
        master_sealer=master_sealer or WindowsDPAPIMasterSealer(),
    )


def run_empirical_panel(
    *,
    lease: Mapping[str, object] | None,
    now: datetime,
    services: RunnerServices,
    validity: Mapping[str, bool],
    occupied_identity_digests: Iterable[str],
    proposal: Mapping[str, object] | None = None,
    native_guard: Callable[..., Mapping[str, object]] = _default_native_guard,
    master_source: Callable[[int], bytes] = os.urandom,
    source_manifest_path: Path | None = None,
) -> object:
    """Run the sole frozen sequence after all preactivity gates succeed."""

    raise RunnerContractError(
        "legacy monolithic run_empirical_panel is disabled; use TRAIN then CM acceptance then EVALUATE"
    )

    frozen_proposal = coordinate_proposal() if proposal is None else dict(proposal)
    validate_coordinate_proposal(frozen_proposal)
    # This check intentionally precedes native loading and master generation.
    if lease is None:
        raise RunnerContractError("future exact Root empirical lease is required")
    validate_lease_envelope(lease, now=now)

    package_root = Path(__file__).resolve().parent
    permit = validate_lease(
        lease,
        now=now,
        package_root=package_root,
        native_guard=native_guard,
        manifest_path=source_manifest_path,
    )

    # First scientific identity operation: exactly one OS-source call.
    master = sample_fresh_master(
        permit,
        occupied_digests=occupied_identity_digests,
        source=master_source,
    )
    rng = EmpiricalRNG(master, permit)

    frontiers: list[BlindedFrontierHandle] = []
    for replicate in range(18):
        for arm in LEARNED_ARMS:
            handle = services.create_frontier(permit, rng, replicate, arm)
            handle.validate()
            if (handle.replicate, handle.arm) != (replicate, arm):
                raise RunnerContractError("frontier factory changed the frozen slot")
            frontiers.append(handle)

    checkpoints: list[CheckpointReceipt] = []
    for frontier in frontiers:
        receipt = services.train_slot(permit, rng, frontier)
        receipt.validate()
        if (receipt.replicate, receipt.arm) != (frontier.replicate, frontier.arm):
            raise RunnerContractError("trainer changed the frozen frontier slot")
        checkpoints.append(receipt)

    # The one global technical barrier precedes both evaluation surfaces.
    barrier = require_global_checkpoint_barrier(checkpoints)
    evaluation = services.evaluate_panel(permit, rng, barrier, tuple(checkpoints))
    support = services.support_panel(permit, rng, barrier)
    packets = _merge_complete_packets(evaluation, support)
    inference = complete_inference(packets, validity=validity)

    identities = identity_digest_set(master)
    complete_result = {
        "schema": "SCDMP_UAV_SP_R02_ATOMIC_RESULT_V1",
        "coordinate_plan_digest": COORDINATE_PLAN_DIGEST,
        "lease_id": permit.lease_id,
        "master_digest": sha256_hex(master),
        "replicate_key_digests": [
            sha256_hex(replicate_key(master, replicate)) for replicate in range(18)
        ],
        "identity_digest_count": len(identities),
        "checkpoint_barrier": asdict(barrier),
        "replicate_packets": packets,
        "inference": inference,
        "complete_atomic_panel": True,
        "partial_inspection_permitted": False,
    }
    # Exactly one publication callback, after complete inference, receives no master key.
    return services.publish_atomic(permit, complete_result)


def atomic_json_publisher(path: Path) -> AtomicPublisher:
    """Return a create-only atomic publisher for a future lease-bound result."""

    target = path.resolve()

    def publish(permit: ActivityPermit, complete_result: Mapping[str, object]) -> dict[str, object]:
        permit.require_active()
        if complete_result.get("complete_atomic_panel") is not True:
            raise RunnerContractError("partial result publication is forbidden")
        encoded = json.dumps(
            dict(complete_result), sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        if target.exists():
            raise RunnerContractError("result publication is create-only")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(str(target) + f".{os.getpid()}.tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Publish the fully fsynced inode only if the target name is
                # absent.  A racing creator's target can never be replaced.
                os.link(temporary, target)
            except FileExistsError as error:
                raise RunnerContractError(
                    "result target appeared during create-only atomic publication"
                ) from error
        finally:
            if temporary.exists():
                temporary.unlink()
        return {
            "path": str(target),
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "size": len(encoded),
            "complete_atomic_panel": True,
        }

    return publish
