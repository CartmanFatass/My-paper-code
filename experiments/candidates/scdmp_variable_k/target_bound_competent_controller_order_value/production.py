"""Fail-closed production admission and realized-path orchestration for TBCC r02.

The preflight path is identity-free.  The separate binding path is the sole
place that may request a 32-byte operating-system master; it persists only a
DPAPI seal and public commitments.  Production execution validates an exact
Root lease and all immutable inputs before unsealing that master.
"""

from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import ctypes
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from enum import Enum
import hashlib
import io
import json
import math
import os
from pathlib import Path
from typing import Callable, Final, Mapping, Protocol, Sequence

import torch

from .artifacts import (
    ADAPTER_ARMS,
    AdapterExecutionPermit,
    AdapterFinalReceipt,
    EmpiricalBindings,
    FinalPanelReceipt,
    FoundationFinalReceipt,
    FoundationGate,
    OpportunityReceipt,
    ResultCode,
    atomic_create_json,
    foundation_barrier_digest,
    issue_adapter_execution_permit,
    issue_final_evaluation_permit,
    load_canonical_json,
    load_foundation_gate,
    load_opportunity_receipt,
    publish_complete_result,
    publish_foundation_gate,
    publish_opportunity_receipt,
    require_final_panel_barrier,
    require_foundation_checkpoint_barrier,
    seal_empirical_activity_permit,
    seal_empirical_bindings,
    test_only_bindings,
    validate_adapter_execution_permit,
    validate_final_evaluation_permit,
)
from .empirical_contract import (
    CARD_REVISION,
    CARD_SHA256,
    DOMAIN_ADDRESS_SCHEMAS,
    EMPIRICAL_STAGE,
    PANEL_COUNTS,
    REPLICATE_NAMESPACE,
    REPLICATES,
    canonical_digest,
    canonical_json_bytes,
    coordinate_proposal,
    coordinate_proposal_digest,
    validate_coordinate_proposal,
)
from .lease import (
    REPAIR_LINEAGE_SCHEMA,
    ActivityPermit,
    execution_argv,
    validate_repair_lineage,
    validate_root_lease,
)
from .lifecycle import GateOutcome
from .preactivity import (
    require_direction_cpp_batched_production,
    validate_preactivity_acceptance,
)
from .source_manifest import (
    load_and_validate_source_manifest,
    manifest_digest,
    stable_native_binding,
)


RUN_IDENTITY_SCHEMA: Final[str] = (
    "SCDMP_TBCC_R02_BLINDED_RUN_IDENTITY_COORDINATE_BINDING_V1"
)
RUN_IDENTITY_NAME: Final[str] = "RUN_IDENTITY.json"
FOUNDATION_GATE_NAME: Final[str] = "FOUNDATION_GATE.json"
OPPORTUNITY_RECEIPT_NAME: Final[str] = "OPPORTUNITY_RECEIPT.json"
COMPLETION_INVENTORY_NAME: Final[str] = "COMPLETION_INVENTORY.json"
FINAL_RESULT_NAME: Final[str] = "COMPLETE_ATOMIC_RESULT.json"
_PREACTIVITY_SEAL: Final[object] = object()


class ProductionContractError(RuntimeError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_file_sha(path: Path, *, allow_final_lf: bool = False) -> tuple[dict[str, object], str]:
    try:
        raw = Path(path).read_bytes()
        decoded = json.loads(raw.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductionContractError(f"canonical JSON is unavailable: {path}") from error
    if not isinstance(decoded, dict):
        raise ProductionContractError("canonical JSON root must be an object")
    exact = canonical_json_bytes(decoded)
    if raw != exact and (not allow_final_lf or raw != exact + b"\n"):
        raise ProductionContractError("JSON bytes are not canonical")
    return decoded, _sha256_bytes(raw)


def _hex_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ProductionContractError(f"{field} is not a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise ProductionContractError(f"{field} is not a SHA-256 digest") from error
    return value.lower()


def _under(root: Path, target: Path, field: str) -> Path:
    resolved_root = Path(root).resolve()
    resolved = Path(target).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise ProductionContractError(f"{field} escapes the repository/result root") from error
    return resolved


def _validate_output_paths(repository_root: Path, paths: Mapping[str, object]) -> dict[str, Path]:
    required = {
        "result_root", "frontier_root", "source_manifest_path",
        "preactivity_acceptance_path", "run_identity_path",
        "completion_inventory_path", "final_result_path", "cm_acceptance_path",
    }
    if not isinstance(paths, Mapping) or set(paths) != required:
        raise ProductionContractError("output path inventory differs from the Root request")
    repo = Path(repository_root).resolve()
    result = _under(repo, Path(str(paths["result_root"])), "result_root")
    if not Path(str(paths["result_root"])).is_absolute():
        raise ProductionContractError("result_root must be absolute")
    resolved: dict[str, Path] = {"result_root": result}
    for field in sorted(required - {"result_root"}):
        raw = Path(str(paths[field]))
        if not raw.is_absolute():
            raise ProductionContractError(f"{field} must be absolute")
        resolved[field] = _under(result, raw, field)
        if resolved[field] == result:
            raise ProductionContractError(f"{field} cannot equal result_root")
    expected_names = {
        "frontier_root": "frontiers",
        "source_manifest_path": "empirical_source_manifest.json",
        "preactivity_acceptance_path": "CM_PREACTIVITY_ACCEPTANCE.json",
        "run_identity_path": RUN_IDENTITY_NAME,
        "completion_inventory_path": "COMPLETION_INVENTORY.json",
        "final_result_path": FINAL_RESULT_NAME,
        "cm_acceptance_path": "CM_TECHNICAL_ACCEPTANCE.json",
    }
    for field, name in expected_names.items():
        if resolved[field].name != name:
            raise ProductionContractError(f"{field} has the wrong terminal name")
    if len({str(path).casefold() for path in resolved.values()}) != len(resolved):
        raise ProductionContractError("output paths are not pairwise distinct")
    return resolved


def _stable_shared_native(value: object) -> dict[str, object]:
    """Return all native receipt semantics except observed load latency."""

    if not isinstance(value, Mapping):
        raise ProductionContractError("shared native receipt is absent")
    stable = dict(value)
    observed = stable.pop("load_seconds", None)
    if observed is not None and (
        isinstance(observed, bool)
        or not isinstance(observed, (int, float))
        or not math.isfinite(float(observed))
        or float(observed) < 0.0
    ):
        raise ProductionContractError("shared native load_seconds is malformed")
    return stable


def _validate_shared_native_semantics(
    receipts: Sequence[Mapping[str, object]], native_identity: Mapping[str, object]
) -> None:
    """Require every admitted width to match the accepted native identity."""

    expected = _stable_shared_native(native_identity)
    if not receipts:
        raise ProductionContractError("object-supported shared receipts are absent")
    for receipt in receipts:
        if _stable_shared_native(receipt.get("native")) != expected:
            raise ProductionContractError(
                "object-supported shared/native semantic binding differs"
            )


@dataclass(frozen=True, repr=False)
class PreactivityState:
    repository_root: Path
    paths: Mapping[str, Path]
    source_manifest: Mapping[str, object]
    source_manifest_sha256: str
    preactivity_acceptance: Mapping[str, object]
    preactivity_acceptance_sha256: str
    native_identity: Mapping[str, object]
    native_binding: Mapping[str, object]
    native_binding_sha256: str
    shared_receipt: Mapping[str, object]
    shared_receipt_sha256: str
    coordinate_proposal: Mapping[str, object]
    _seal: object | None = None

    def validate_seal(self) -> None:
        if self._seal is not _PREACTIVITY_SEAL:
            raise ProductionContractError("sealed preactivity validation state is required")


def preflight_only(
    *,
    repository_root: Path,
    source_manifest_path: Path,
    preactivity_acceptance_path: Path,
    output_paths: Mapping[str, object],
    native_identity_loader: Callable[[], Mapping[str, object]],
    shared_guard: Callable[..., Mapping[str, object]],
    batch_width: int = 144,
) -> PreactivityState:
    """Validate immutable inputs without writing or materializing an identity."""

    root = Path(repository_root).resolve()
    paths = _validate_output_paths(root, output_paths)
    if Path(source_manifest_path).resolve() != paths["source_manifest_path"]:
        raise ProductionContractError("source manifest path differs from the future Root path")
    if Path(preactivity_acceptance_path).resolve() != paths["preactivity_acceptance_path"]:
        raise ProductionContractError("preactivity acceptance path differs from the future Root path")
    native_identity = dict(native_identity_loader())
    source_manifest = load_and_validate_source_manifest(
        paths["source_manifest_path"], root, native_identity=native_identity
    )
    source_sha = manifest_digest(source_manifest)
    raw_manifest_sha = _sha256_bytes(paths["source_manifest_path"].read_bytes())
    if source_sha != raw_manifest_sha:
        raise ProductionContractError("source manifest byte digest differs from its canonical digest")
    acceptance, acceptance_sha = _canonical_file_sha(paths["preactivity_acceptance_path"])
    if batch_width != 144:
        raise ProductionContractError("preflight primary width must be the Root-bound width 144")
    receipts = tuple(
        dict(
            require_direction_cpp_batched_production(
                batch_width=width,
                shared_guard=shared_guard,
                candidate_identity=lambda: native_identity,
            )
        )
        for width in (12, 120, 144)
    )
    receipt = receipts[-1]
    _validate_shared_native_semantics(receipts, native_identity)
    validated_acceptance = validate_preactivity_acceptance(
        acceptance,
        repository_root=root,
        source_manifest=source_manifest,
        native_identity=native_identity,
        native_receipt=receipt,
    )
    proposal = coordinate_proposal(source_sha)
    validate_coordinate_proposal(proposal, source_manifest_sha256=source_sha)
    native_binding = stable_native_binding(native_identity)
    shared_sha = canonical_digest(receipt)
    return PreactivityState(
        repository_root=root,
        paths=paths,
        source_manifest=source_manifest,
        source_manifest_sha256=source_sha,
        preactivity_acceptance=validated_acceptance,
        preactivity_acceptance_sha256=acceptance_sha,
        native_identity=native_identity,
        native_binding=native_binding,
        native_binding_sha256=canonical_digest(native_binding),
        shared_receipt=receipt,
        shared_receipt_sha256=shared_sha,
        coordinate_proposal=proposal,
        _seal=_PREACTIVITY_SEAL,
    )


class MasterSealer(Protocol):
    def seal(self, master: bytes, *, context: bytes) -> bytes: ...
    def unseal(self, sealed: bytes, *, context: bytes) -> bytes: ...


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


class WindowsDPAPIMasterSealer:
    """Same-user Windows DPAPI seal with UI forbidden and no fallback."""

    _UI_FORBIDDEN = 0x1

    @staticmethod
    def _blob(value: bytes) -> tuple[_DataBlob, object]:
        buffer = ctypes.create_string_buffer(value)
        return (
            _DataBlob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))),
            buffer,
        )

    @staticmethod
    def _copy_free(blob: _DataBlob) -> bytes:
        value = ctypes.string_at(blob.pbData, blob.cbData)
        ctypes.windll.kernel32.LocalFree(blob.pbData)
        return value

    def seal(self, master: bytes, *, context: bytes) -> bytes:
        if os.name != "nt" or type(master) is not bytes or len(master) != 32:
            raise ProductionContractError("Windows DPAPI and one 32-byte master are required")
        source, source_buffer = self._blob(master)
        entropy, entropy_buffer = self._blob(context)
        output = _DataBlob()
        ok = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(source), None, ctypes.byref(entropy), None, None,
            self._UI_FORBIDDEN, ctypes.byref(output),
        )
        _ = source_buffer, entropy_buffer
        if not ok:
            raise ProductionContractError("DPAPI master sealing failed")
        return self._copy_free(output)

    def unseal(self, sealed: bytes, *, context: bytes) -> bytes:
        if os.name != "nt" or type(sealed) is not bytes or not sealed:
            raise ProductionContractError("Windows DPAPI sealed master is required")
        source, source_buffer = self._blob(sealed)
        entropy, entropy_buffer = self._blob(context)
        output = _DataBlob()
        ok = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(source), None, ctypes.byref(entropy), None, None,
            self._UI_FORBIDDEN, ctypes.byref(output),
        )
        _ = source_buffer, entropy_buffer
        if not ok:
            raise ProductionContractError("DPAPI master unsealing failed")
        value = self._copy_free(output)
        if len(value) != 32:
            raise ProductionContractError("unsealed master is not 32 bytes")
        return value


def _coordinate_public_binding(state: PreactivityState) -> dict[str, object]:
    state.validate_seal()
    return {
        "schema": "SCDMP_TBCC_R02_MATERIALIZED_COORDINATE_BINDING_V1",
        "stage": EMPIRICAL_STAGE,
        "card_revision": CARD_REVISION,
        "card_sha256": CARD_SHA256,
        "source_manifest_sha256": state.source_manifest_sha256,
        "preactivity_acceptance_sha256": state.preactivity_acceptance_sha256,
        "native_binding_sha256": state.native_binding_sha256,
        "shared_receipt_sha256": state.shared_receipt_sha256,
        "coordinate_proposal_digest": coordinate_proposal_digest(
            state.source_manifest_sha256
        ),
        "replicate_namespace": REPLICATE_NAMESPACE,
        "replicates": list(REPLICATES),
        "domain_address_schemas": [
            {"domain": domain, "fields": list(fields)}
            for domain, fields in DOMAIN_ADDRESS_SCHEMAS
        ],
        "counts": dict(PANEL_COUNTS),
        "rng_derivation": "HMAC-SHA256",
        "rng_words_present": False,
        "partial_inspection_permitted": False,
    }


def _seal_context(binding: Mapping[str, object]) -> bytes:
    return b"SCDMP-TBCC-R02-RUN-IDENTITY-SEAL-v1\0" + canonical_json_bytes(binding)


def _atomic_create_exact(path: Path, payload: Mapping[str, object], *, root: Path) -> str:
    target = _under(root, path, "run identity path")
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(dict(payload))
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise ProductionContractError("run identity/coordinate binding is create-only") from error
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return _sha256_bytes(encoded)


@dataclass(frozen=True)
class BoundIdentity:
    path: Path
    file_sha256: str
    empirical_identity_sha256: str
    coordinate_manifest_sha256: str
    master_commitment_sha256: str


def bind_coordinates(
    state: PreactivityState,
    *,
    master_source: Callable[[int], bytes] = os.urandom,
    master_sealer: MasterSealer | None = None,
) -> BoundIdentity:
    """Create the sole blinded identity/coordinate record after preactivity acceptance."""

    state.validate_seal()
    if state.preactivity_acceptance.get("accepted") is not True:
        raise ProductionContractError("complete preactivity acceptance is required")
    path = state.paths["run_identity_path"]
    if path.exists():
        raise ProductionContractError("run identity/coordinate binding already exists")
    master = master_source(32)
    if type(master) is not bytes or len(master) != 32:
        raise ProductionContractError("master source must return exactly 32 bytes once")
    binding = _coordinate_public_binding(state)
    coordinate_sha = canonical_digest(binding)
    master_sha = _sha256_bytes(master)
    identity_sha = canonical_digest(
        {
            "coordinate_manifest_sha256": coordinate_sha,
            "master_commitment_sha256": master_sha,
            "origin_receipt_sha256": state.preactivity_acceptance_sha256,
        }
    )
    sealer = master_sealer or WindowsDPAPIMasterSealer()
    ciphertext = sealer.seal(master, context=_seal_context(binding))
    if type(ciphertext) is not bytes or not ciphertext:
        raise ProductionContractError("master sealer returned an empty/non-byte seal")
    payload = {
        "schema": RUN_IDENTITY_SCHEMA,
        "coordinate_binding": binding,
        "coordinate_manifest_sha256": coordinate_sha,
        "empirical_identity_sha256": identity_sha,
        "master_commitment_sha256": master_sha,
        "origin_receipt_sha256": state.preactivity_acceptance_sha256,
        "sealed_master": {
            "kind": type(sealer).__name__,
            "encoding": "base64",
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        },
        "master_material_exposed": False,
        "rng_words_present": False,
        "partial_inspection_permitted": False,
    }
    file_sha = _atomic_create_exact(path, payload, root=state.paths["result_root"])
    return BoundIdentity(path, file_sha, identity_sha, coordinate_sha, master_sha)


@dataclass(frozen=True, repr=False)
class RunContext:
    permit: ActivityPermit
    bindings: EmpiricalBindings
    native_binding: Mapping[str, object]
    result_root: Path
    frontier_root: Path
    _master: bytes

    def master_for_service(self, permit: ActivityPermit) -> bytes:
        if permit is not self.permit:
            raise ProductionContractError("service requested master under a different permit")
        permit.require_active()
        return self._master


def _jsonable(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ProductionContractError(f"noncanonical analysis value: {type(value).__name__}")


def _analysis_digest(value: object) -> str:
    return canonical_digest(_jsonable(value))


def _parallel_ordered(
    workers: int, function: Callable[[object], object], values: Sequence[object]
) -> tuple[object, ...]:
    if workers == 1:
        return tuple(function(value) for value in values)
    if workers not in (2, 4):
        raise ProductionContractError("worker count must be exactly 1, 2, or 4")
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="tbcc-r02") as executor:
        futures = tuple(executor.submit(function, value) for value in values)
        return tuple(future.result() for future in futures)


def _atomic_create_binary(path: Path, payload: object, *, root: Path) -> str:
    target = _under(root, path, "checkpoint path")
    target.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    torch.save(payload, buffer)
    encoded = buffer.getvalue()
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, target)
        except FileExistsError as error:
            raise ProductionContractError("checkpoint generation is create-only") from error
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return _sha256_bytes(encoded)


def _load_checkpoint(path: Path, *, root: Path) -> tuple[Mapping[str, object], str]:
    target = _under(root, path, "checkpoint path")
    try:
        encoded = target.read_bytes()
        payload = torch.load(io.BytesIO(encoded), map_location="cpu", weights_only=True)
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        raise ProductionContractError("checkpoint is absent, corrupt, or unsafe") from error
    if not isinstance(payload, Mapping):
        raise ProductionContractError("checkpoint payload is not a mapping")
    return payload, _sha256_bytes(encoded)


class ConcreteProductionServices:
    """High-level adapter over native services, analyzers, and hash-linked frontiers."""

    def __init__(self, context: RunContext) -> None:
        if context.bindings.test_only:
            raise ProductionContractError("concrete production services reject TEST_ONLY bindings")
        from .production_services import (
            NativeProductionServices,
            issue_service_authority,
        )

        master = context.master_for_service(context.permit)
        authority = issue_service_authority(
            activity_permit=context.permit,
            bindings=context.bindings,
            native_binding=context.native_binding,
            master_sha256=_sha256_bytes(master),
        )
        self.context = context
        self.authority = authority
        self.native = NativeProductionServices(authority=authority, master=master)
        self._foundation_models: dict[int, object] = {}
        self._adapter_models: dict[tuple[int, str], object] = {}
        self._foundation_summaries: tuple[object, ...] | None = None
        self._opportunity_analysis: object | None = None

    def _slot_root(self, replicate: int, arm: str) -> Path:
        label = "foundation" if arm == "FOUNDATION" else f"adapter_{arm.lower()}"
        return self.context.frontier_root / label / f"replicate_{replicate:02d}"

    def _paths(self, replicate: int, arm: str, generation: int) -> tuple[Path, Path, Path]:
        root = self._slot_root(replicate, arm)
        return (
            root / f"generation_{generation:04d}.json",
            root / f"checkpoint_{generation:04d}.pt",
            root / f"checkpoint_{generation:04d}.receipt.json",
        )

    def _frontier_chain(self, replicate: int, arm: str):
        from .frontier import load_resume_chain

        root = self._slot_root(replicate, arm)
        if not root.exists():
            return ()
        paths = tuple(sorted(root.glob("generation_*.json")))
        if not paths:
            return ()
        expected = tuple(
            root / f"generation_{index:04d}.json" for index in range(len(paths))
        )
        if paths != expected:
            raise ProductionContractError("frontier generations are noncontiguous")
        return load_resume_chain(
            paths, artifact_root=self.context.frontier_root, bindings=self.context.bindings
        )

    def _checkpoint_receipt(
        self,
        *,
        replicate: int,
        arm: str,
        generation: int,
        checkpoint_sha256: str,
        optimizer_sha256: str,
        frontier_sha256: str,
    ) -> dict[str, object]:
        return {
            "schema": "SCDMP_TBCC_R02_BLINDED_CHECKPOINT_GENERATION_RECEIPT_V1",
            "lineage_digest": self.context.bindings.lineage_digest,
            "coordinate_manifest_sha256": self.context.bindings.coordinate_manifest_sha256,
            "replicate": replicate,
            "arm": arm,
            "generation": generation,
            "checkpoint_sha256": checkpoint_sha256,
            "optimizer_state_sha256": optimizer_sha256,
            "frontier_generation_sha256": frontier_sha256,
            "partial_inspection_permitted": False,
        }

    def _load_receipt(self, path: Path) -> dict[str, object]:
        return load_canonical_json(path, artifact_root=self.context.frontier_root)

    def _train_final(
        self,
        *,
        replicate: int,
        arm: str,
        model: object,
        adapter_permit: AdapterExecutionPermit | None = None,
    ):
        from .frontier import (
            FrontierGeneration,
            FrontierStage,
            FrontierState,
            create_frontier_generation,
            frontier_generation_digest,
        )
        from .training import DurationCorrectPPOTrainer, validate_checkpoint_payload

        stage = FrontierStage.FOUNDATION if arm == "FOUNDATION" else FrontierStage.ADAPTER
        limit = 160 if arm == "FOUNDATION" else 96
        trainer = DurationCorrectPPOTrainer(model, permit=self.authority)
        chain = self._frontier_chain(replicate, arm)
        if not chain:
            created = FrontierGeneration(
                stage=stage,
                replicate=replicate,
                arm=arm,
                lineage_digest=self.context.bindings.lineage_digest,
                coordinate_manifest_sha256=self.context.bindings.coordinate_manifest_sha256,
                generation=0,
                previous_generation_sha256=None,
                state=FrontierState.CREATED,
                update_index=0,
                optimizer_step=0,
            )
            generation_path, _, _ = self._paths(replicate, arm, 0)
            create_frontier_generation(
                generation_path,
                created,
                artifact_root=self.context.frontier_root,
                bindings=self.context.bindings,
                adapter_permit=adapter_permit,
            )
            chain = (created,)
        latest = chain[-1]
        if latest.state is FrontierState.FINAL_CHECKPOINT:
            _, checkpoint_path, receipt_path = self._paths(replicate, arm, limit)
            checkpoint, checkpoint_sha = _load_checkpoint(
                checkpoint_path, root=self.context.frontier_root
            )
            validation = trainer.restore_checkpoint(checkpoint)
            receipt = self._load_receipt(receipt_path)
            expected = self._checkpoint_receipt(
                replicate=replicate,
                arm=arm,
                generation=limit,
                checkpoint_sha256=checkpoint_sha,
                optimizer_sha256=validation.optimizer_digest,
                frontier_sha256=frontier_generation_digest(latest, self.context.bindings),
            )
            if receipt != expected:
                raise ProductionContractError("final checkpoint receipt differs on resume")
            return model, latest
        completed = latest.update_index
        if completed:
            _, checkpoint_path, receipt_path = self._paths(replicate, arm, completed)
            checkpoint, checkpoint_sha = _load_checkpoint(
                checkpoint_path, root=self.context.frontier_root
            )
            validation = trainer.restore_checkpoint(checkpoint)
            receipt = self._load_receipt(receipt_path)
            if (
                receipt.get("checkpoint_sha256") != checkpoint_sha
                or receipt.get("optimizer_state_sha256") != validation.optimizer_digest
                or receipt.get("frontier_generation_sha256")
                != frontier_generation_digest(latest, self.context.bindings)
            ):
                raise ProductionContractError("checkpoint/frontier receipt differs on resume")
        for update in range(completed + 1, limit + 1):
            output = self.native.collect_and_train_update(trainer=trainer, update=update)
            checkpoint = output.checkpoint_payload
            validation = validate_checkpoint_payload(checkpoint, trainer.model, trainer.optimizer)
            generation_path, checkpoint_path, receipt_path = self._paths(replicate, arm, update)
            if checkpoint_path.exists():
                retained, checkpoint_sha = _load_checkpoint(
                    checkpoint_path, root=self.context.frontier_root
                )
                retained_validation = validate_checkpoint_payload(
                    retained, trainer.model, trainer.optimizer
                )
                if (
                    retained_validation.parameter_digest != validation.parameter_digest
                    or retained_validation.optimizer_digest != validation.optimizer_digest
                ):
                    raise ProductionContractError("orphan checkpoint differs during resume")
            else:
                checkpoint_sha = _atomic_create_binary(
                    checkpoint_path, checkpoint, root=self.context.frontier_root
                )
            state = (
                FrontierState.FINAL_CHECKPOINT
                if update == limit
                else FrontierState.TRAINING
            )
            generation = FrontierGeneration(
                stage=stage,
                replicate=replicate,
                arm=arm,
                lineage_digest=self.context.bindings.lineage_digest,
                coordinate_manifest_sha256=self.context.bindings.coordinate_manifest_sha256,
                generation=update,
                previous_generation_sha256=frontier_generation_digest(
                    chain[-1], self.context.bindings
                ),
                state=state,
                update_index=update,
                optimizer_step=update * 12,
                checkpoint_sha256=checkpoint_sha if update == limit else None,
                optimizer_state_sha256=(
                    validation.optimizer_digest if update == limit else None
                ),
            )
            frontier_sha = frontier_generation_digest(generation, self.context.bindings)
            checkpoint_receipt = self._checkpoint_receipt(
                replicate=replicate,
                arm=arm,
                generation=update,
                checkpoint_sha256=checkpoint_sha,
                optimizer_sha256=validation.optimizer_digest,
                frontier_sha256=frontier_sha,
            )
            if receipt_path.exists():
                if self._load_receipt(receipt_path) != checkpoint_receipt:
                    raise ProductionContractError("orphan checkpoint receipt differs")
            else:
                atomic_create_json(
                    receipt_path,
                    checkpoint_receipt,
                    artifact_root=self.context.frontier_root,
                )
            if generation_path.exists():
                raise ProductionContractError("frontier generation appeared concurrently")
            create_frontier_generation(
                generation_path,
                generation,
                artifact_root=self.context.frontier_root,
                bindings=self.context.bindings,
                adapter_permit=adapter_permit,
            )
            chain = (*chain, generation)
        return model, chain[-1]

    def foundation_final(self, context: RunContext, replicate: int) -> FoundationFinalReceipt:
        from .frontier import foundation_receipt_from_final

        if context is not self.context:
            raise ProductionContractError("concrete service context differs")
        model = self.native.materialize_foundation(replicate=replicate)
        model, final = self._train_final(
            replicate=replicate, arm="FOUNDATION", model=model
        )
        self._foundation_models[replicate] = model
        return foundation_receipt_from_final(final, bindings=context.bindings)

    class _Loader:
        def __init__(self, owner: "ConcreteProductionServices", replicate: int) -> None:
            self.owner = owner
            self.replicate = replicate

        def load_accepted_controller(self, *, replicate: int, controller: str):
            from .evaluation import AcceptedControllerBinding

            if replicate != self.replicate:
                raise ProductionContractError("model loader replicate differs")
            if controller == "FOUNDATION":
                model = self.owner._foundation_models[replicate]
                source_arm = "FOUNDATION"
                _, checkpoint, _ = self.owner._paths(replicate, "FOUNDATION", 160)
            else:
                source_arm = "TREAT" if controller == "REVERSED" else controller
                model = self.owner._adapter_models[(replicate, source_arm)]
                _, checkpoint, _ = self.owner._paths(replicate, source_arm, 96)
            return AcceptedControllerBinding(
                controller=controller,
                source_arm=source_arm,
                model_digest=_sha256_bytes(checkpoint.read_bytes()),
                model=model,
                technically_accepted=True,
                frozen=True,
            )

    def foundation_competence(
        self, context: RunContext, receipts: Sequence[FoundationFinalReceipt]
    ) -> tuple[FoundationGate, str]:
        from .evaluation import collect_complete_evaluation
        from .inference import analyze_foundation_competence

        barrier = require_foundation_checkpoint_barrier(receipts, context.bindings)
        def evaluate(replicate_object: object):
            replicate = int(replicate_object)
            scenarios = self.native.evaluation_scenarios(
                replicate=replicate, stage="foundation-competence"
            )
            return collect_complete_evaluation(
                stage="foundation-competence",
                replicate=replicate,
                scenarios=scenarios,
                authority=self.authority,
                model_loader=self._Loader(self, replicate),
                native_service=self.native.evaluation_adapter(
                    stage="foundation-competence",
                    replicate=replicate,
                    scenarios=scenarios,
                ),
            )
        summaries = _parallel_ordered(
            self.context.permit.workers, evaluate, tuple(REPLICATES)
        )
        self._foundation_summaries = summaries
        analysis = analyze_foundation_competence(summaries)
        digest = _analysis_digest(analysis)
        return FoundationGate(
            outcome=analysis.gate,
            complete_panel_sha256=digest,
            barrier_sha256=foundation_barrier_digest(barrier),
        ), digest

    def opportunity(
        self, context: RunContext, foundation_gate: FoundationGate
    ) -> tuple[OpportunityReceipt, str]:
        from . import artifacts as artifact_api
        from .opportunity import aggregate_replicate, analyze_gate

        bridge = getattr(artifact_api, "issue_stage1b_opportunity_execution_permit", None)
        if not callable(bridge):
            raise ProductionContractError(
                "production opportunity permit bridge is not installed"
            )
        foundation_receipts = tuple(
            self.foundation_final(context, replicate) for replicate in REPLICATES
        )
        barrier = require_foundation_checkpoint_barrier(
            foundation_receipts, context.bindings
        )
        permit = bridge(
            receipts=foundation_receipts,
            foundation_barrier=barrier,
            foundation_gate_path=context.result_root / FOUNDATION_GATE_NAME,
            foundation_gate=foundation_gate,
            artifact_root=context.result_root,
            bindings=context.bindings,
            opportunity_receipt_path=context.result_root / OPPORTUNITY_RECEIPT_NAME,
            adapter_frontier_paths=tuple(
                self._paths(replicate, arm, 0)[0]
                for replicate in REPLICATES
                for arm in ADAPTER_ARMS
            ),
            final_result_path=context.result_root / FINAL_RESULT_NAME,
        )
        def evaluate_opportunity(replicate_object: object):
            replicate = int(replicate_object)
            foundation = self._foundation_models[replicate]
            pairs = tuple(
                self.native.run_opportunity_pair(
                    replicate=replicate,
                    k=k,
                    state_index=state,
                    permit=permit,
                    foundation=foundation,
                )
                for k in (7, 13)
                for state in range(16)
            )
            return aggregate_replicate(pairs)
        aggregates = _parallel_ordered(
            self.context.permit.workers,
            evaluate_opportunity,
            tuple(REPLICATES),
        )
        analysis = analyze_gate(aggregates)
        self._opportunity_analysis = analysis
        digest = _analysis_digest(analysis)
        return OpportunityReceipt(
            outcome=GateOutcome.PASS if analysis.passes else GateOutcome.NONPASS,
            complete_stage_sha256=digest,
            foundation_gate_sha256="0" * 64,
        ), digest

    def adapter_final(
        self,
        context: RunContext,
        replicate: int,
        arm: str,
        adapter_permit: object,
    ) -> AdapterFinalReceipt:
        from .frontier import adapter_receipt_from_final

        if not isinstance(adapter_permit, AdapterExecutionPermit):
            raise ProductionContractError("artifact-bound adapter permit is required")
        validate_adapter_execution_permit(adapter_permit, bindings=context.bindings)
        foundation = self._foundation_models[replicate]
        model = self.native.materialize_order_arm(foundation=foundation, arm=arm)
        model, final = self._train_final(
            replicate=replicate,
            arm=arm,
            model=model,
            adapter_permit=adapter_permit,
        )
        self._adapter_models[(replicate, arm)] = model
        return adapter_receipt_from_final(
            final, bindings=context.bindings, adapter_permit=adapter_permit
        )

    def final_evaluation(
        self, context: RunContext, final_permit: object, final_barrier: object
    ) -> tuple[FinalPanelReceipt, ResultCode, str]:
        from .artifacts import FinalEvaluationPermit, FinalPanelBarrier, final_panel_barrier_digest
        from .evaluation import collect_complete_evaluation
        from .inference import analyze_final_inference, analyze_foundation_competence

        if not isinstance(final_permit, FinalEvaluationPermit) or not isinstance(
            final_barrier, FinalPanelBarrier
        ):
            raise ProductionContractError("final evaluation requires exact artifact permits")
        validate_final_evaluation_permit(
            final_permit, barrier=final_barrier, bindings=context.bindings
        )
        def evaluate(replicate_object: object):
            replicate = int(replicate_object)
            scenarios = self.native.evaluation_scenarios(
                replicate=replicate, stage="final"
            )
            return collect_complete_evaluation(
                stage="final",
                replicate=replicate,
                scenarios=scenarios,
                authority=self.authority,
                model_loader=self._Loader(self, replicate),
                native_service=self.native.evaluation_adapter(
                    stage="final", replicate=replicate, scenarios=scenarios
                ),
            )
        summaries = _parallel_ordered(
            self.context.permit.workers, evaluate, tuple(REPLICATES)
        )
        if self._foundation_summaries is None:
            raise ProductionContractError("final inference lacks complete foundation summaries")
        foundation_analysis = analyze_foundation_competence(self._foundation_summaries)
        if foundation_analysis.gate is not GateOutcome.PASS:
            raise ProductionContractError("final inference foundation prerequisite differs")
        inference = analyze_final_inference(summaries)
        try:
            result_code = ResultCode(inference.branch.value)
        except ValueError as error:
            raise ProductionContractError("complete final inference branch is unregistered") from error
        digest = _analysis_digest(
            {
                "foundation_gate_sha256": _sha256_bytes(
                    (context.result_root / FOUNDATION_GATE_NAME).read_bytes()
                ),
                "opportunity_receipt_sha256": _sha256_bytes(
                    (context.result_root / OPPORTUNITY_RECEIPT_NAME).read_bytes()
                ),
                "final_inference": inference,
            }
        )
        return (
            FinalPanelReceipt(
                complete_panel_sha256=digest,
                barrier_sha256=final_panel_barrier_digest(final_barrier),
            ),
            result_code,
            digest,
        )


def _inspect_bound_identity_lineage(
    state: PreactivityState,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Validate frozen public identity/coordinate bytes without unsealing master."""

    path = state.paths["run_identity_path"]
    value, run_identity_sha = _canonical_file_sha(path)
    required = {
        "schema", "coordinate_binding", "coordinate_manifest_sha256",
        "empirical_identity_sha256", "master_commitment_sha256",
        "origin_receipt_sha256", "sealed_master", "master_material_exposed",
        "rng_words_present", "partial_inspection_permitted",
    }
    if set(value) != required or value.get("schema") != RUN_IDENTITY_SCHEMA:
        raise ProductionContractError("run identity/coordinate binding schema differs")
    binding_value = value.get("coordinate_binding")
    if not isinstance(binding_value, Mapping):
        raise ProductionContractError("run identity coordinate/source binding differs")
    binding = dict(binding_value)
    origin_source = _hex_digest(
        binding.get("source_manifest_sha256"), "origin source manifest"
    )
    origin_acceptance = _hex_digest(
        binding.get("preactivity_acceptance_sha256"), "origin preactivity acceptance"
    )
    frozen_shared = _hex_digest(
        binding.get("shared_receipt_sha256"), "bound shared receipt"
    )
    frozen_proposal = _hex_digest(
        binding.get("coordinate_proposal_digest"), "frozen coordinate proposal"
    )
    if frozen_proposal != coordinate_proposal_digest(origin_source):
        raise ProductionContractError("frozen coordinate proposal/source binding differs")
    expected_binding = _coordinate_public_binding(state)
    expected_binding.update(
        {
            "source_manifest_sha256": origin_source,
            "preactivity_acceptance_sha256": origin_acceptance,
            "shared_receipt_sha256": frozen_shared,
            "coordinate_proposal_digest": frozen_proposal,
        }
    )
    if binding != expected_binding:
        raise ProductionContractError("run identity coordinate/source binding differs")
    coordinate_sha = canonical_digest(binding)
    if value.get("coordinate_manifest_sha256") != coordinate_sha:
        raise ProductionContractError("coordinate manifest digest differs")
    master_sha = _hex_digest(value.get("master_commitment_sha256"), "master commitment")
    identity_sha = canonical_digest(
        {
            "coordinate_manifest_sha256": coordinate_sha,
            "master_commitment_sha256": master_sha,
            "origin_receipt_sha256": origin_acceptance,
        }
    )
    if (
        value.get("empirical_identity_sha256") != identity_sha
        or value.get("origin_receipt_sha256") != origin_acceptance
        or value.get("master_material_exposed") is not False
        or value.get("rng_words_present") is not False
        or value.get("partial_inspection_permitted") is not False
    ):
        raise ProductionContractError("run identity public/blinding fields differ")
    sealed = value.get("sealed_master")
    if (
        not isinstance(sealed, Mapping)
        or set(sealed) != {"kind", "encoding", "ciphertext"}
        or sealed.get("encoding") != "base64"
    ):
        raise ProductionContractError("run identity seal contract differs")
    try:
        base64.b64decode(str(sealed["ciphertext"]), validate=True)
    except (ValueError, TypeError) as error:
        raise ProductionContractError("run identity seal encoding differs") from error
    lineage = validate_repair_lineage(
        {
            "schema": REPAIR_LINEAGE_SCHEMA,
            "run_identity_sha256": run_identity_sha,
            "origin_source_manifest_sha256": origin_source,
            "origin_preactivity_acceptance_sha256": origin_acceptance,
            "frozen_shared_receipt_sha256": frozen_shared,
            "frozen_native_binding_sha256": binding["native_binding_sha256"],
            "frozen_coordinate_proposal_digest": frozen_proposal,
            "coordinate_manifest_sha256": coordinate_sha,
            "empirical_identity_sha256": identity_sha,
            "master_commitment_sha256": master_sha,
            "card_revision": binding["card_revision"],
            "card_sha256": binding["card_sha256"],
            "replicate_namespace": binding["replicate_namespace"],
            "domain_address_schemas_sha256": canonical_digest(
                binding["domain_address_schemas"]
            ),
            "counts_sha256": canonical_digest(binding["counts"]),
            "scientific_activity_started": False,
            "master_regenerated": False,
            "coordinate_domains_changed": False,
        }
    )
    return value, binding, lineage


def same_coordinate_repair_lineage(state: PreactivityState) -> dict[str, object]:
    """Return the exact public lineage for a Root successor request; no unseal."""

    state.validate_seal()
    return _inspect_bound_identity_lineage(state)[2]


def _load_bound_identity(
    state: PreactivityState,
    *,
    permit: ActivityPermit,
    lease_sha256: str,
    master_sealer: MasterSealer,
) -> RunContext:
    value, bound_binding, lineage = _inspect_bound_identity_lineage(state)
    repair_lineage = permit.same_coordinate_repair_lineage
    if repair_lineage is None:
        if (
            lineage["origin_source_manifest_sha256"] != state.source_manifest_sha256
            or lineage["origin_preactivity_acceptance_sha256"]
            != state.preactivity_acceptance_sha256
        ):
            raise ProductionContractError(
                "source-repaired identity requires an explicit successor permit"
            )
    elif validate_repair_lineage(repair_lineage) != lineage:
        raise ProductionContractError("successor permit identity lineage differs")
    if (
        permit.source_manifest_sha256 != state.source_manifest_sha256
        or permit.preactivity_acceptance_sha256
        != state.preactivity_acceptance_sha256
        or permit.native_binding_sha256 != state.native_binding_sha256
    ):
        raise ProductionContractError("activity permit current source binding differs")
    coordinate_sha = str(lineage["coordinate_manifest_sha256"])
    master_sha = str(lineage["master_commitment_sha256"])
    identity_sha = str(lineage["empirical_identity_sha256"])
    origin_acceptance = str(lineage["origin_preactivity_acceptance_sha256"])
    bound_shared_receipt_sha256 = str(lineage["frozen_shared_receipt_sha256"])
    sealed = value.get("sealed_master")
    if (
        not isinstance(sealed, Mapping)
        or set(sealed) != {"kind", "encoding", "ciphertext"}
        or sealed.get("kind") != type(master_sealer).__name__
        or sealed.get("encoding") != "base64"
    ):
        raise ProductionContractError("run identity seal contract differs")
    try:
        ciphertext = base64.b64decode(str(sealed["ciphertext"]), validate=True)
    except (ValueError, TypeError) as error:
        raise ProductionContractError("run identity seal encoding differs") from error
    # This is deliberately the first operation that opens the sealed master.
    master = master_sealer.unseal(ciphertext, context=_seal_context(bound_binding))
    if type(master) is not bytes or len(master) != 32 or _sha256_bytes(master) != master_sha:
        raise ProductionContractError("unsealed master differs from its blinded commitment")
    authorization = seal_empirical_activity_permit(authorization_sha256=lease_sha256)
    bindings = seal_empirical_bindings(
        permit=authorization,
        source_manifest_sha256=state.source_manifest_sha256,
        shared_receipt_sha256=bound_shared_receipt_sha256,
        master_commitment_sha256=master_sha,
        empirical_identity_sha256=identity_sha,
        coordinate_manifest_sha256=coordinate_sha,
        origin_receipt_sha256=origin_acceptance,
    )
    return RunContext(
        permit=permit,
        bindings=bindings,
        native_binding=state.native_binding,
        result_root=state.paths["result_root"],
        frontier_root=state.paths["frontier_root"],
        _master=master,
    )


class ProductionServices(Protocol):
    def foundation_final(self, context: RunContext, replicate: int) -> FoundationFinalReceipt: ...
    def foundation_competence(
        self, context: RunContext, receipts: Sequence[FoundationFinalReceipt]
    ) -> tuple[FoundationGate, str]: ...
    def opportunity(
        self, context: RunContext, foundation_gate: FoundationGate
    ) -> tuple[OpportunityReceipt, str]: ...
    def adapter_final(
        self, context: RunContext, replicate: int, arm: str, adapter_permit: object
    ) -> AdapterFinalReceipt: ...
    def final_evaluation(
        self, context: RunContext, final_permit: object, final_barrier: object
    ) -> tuple[FinalPanelReceipt, ResultCode, str]: ...


def _require_services_api(services: object) -> ProductionServices:
    required = (
        "foundation_final", "foundation_competence", "opportunity",
        "adapter_final", "final_evaluation",
    )
    missing = tuple(name for name in required if not callable(getattr(services, name, None)))
    if missing:
        raise ProductionContractError(
            "production_services API is incomplete: " + ", ".join(missing)
        )
    return services  # type: ignore[return-value]


def _load_completed_result_digest(context: RunContext, path: Path) -> str | None:
    if not path.exists():
        return None
    row = load_canonical_json(path, artifact_root=context.result_root)
    required_common = {
        "schema", "lineage_digest", "coordinate_manifest_sha256", "test_only",
        "foundation_gate_sha256", "realized_path", "result_code",
        "complete_inference_sha256", "complete", "partial_values_exposed",
        "interpretation_included",
    }
    if not required_common.issubset(row):
        raise ProductionContractError("existing complete-result inventory is malformed")
    if (
        row.get("schema") != "SCDMP_TBCC_R02_COMPLETE_REALIZED_PATH_RESULT_V1"
        or row.get("lineage_digest") != context.bindings.lineage_digest
        or row.get("coordinate_manifest_sha256")
        != context.bindings.coordinate_manifest_sha256
        or row.get("test_only") is not context.bindings.test_only
        or row.get("complete") is not True
        or row.get("partial_values_exposed") is not False
        or row.get("interpretation_included") is not False
    ):
        raise ProductionContractError("existing complete result differs from the same-coordinate lineage")
    realized = row.get("realized_path")
    extra = set(row) - required_common
    expected_extra = {
        "FOUNDATION_ONLY": set(),
        "FOUNDATION_AND_OPPORTUNITY": {"opportunity_receipt_sha256"},
        "FULL_FIVE_CONTROLLER_PANEL": {
            "opportunity_receipt_sha256", "final_panel_sha256",
            "final_panel_barrier_sha256",
        },
    }
    if realized not in expected_extra or extra != expected_extra[realized]:
        raise ProductionContractError("existing complete result realized-path inventory differs")
    allowed_codes = {
        value.value for value in ResultCode
    }
    if row.get("result_code") not in allowed_codes:
        raise ProductionContractError("existing complete result code differs")
    _hex_digest(
        str(row.get("complete_inference_sha256", "")).removeprefix(
            "TEST_ONLY_FAKE_SHA256:"
        ),
        "complete inference",
    )
    return _sha256_bytes(path.read_bytes())


def _publish_or_validate_completion(
    context: RunContext, *, realized_path: str, stage_digests: Mapping[str, str]
) -> str:
    payload = {
        "schema": "SCDMP_TBCC_R02_COMPLETE_REALIZED_PATH_INVENTORY_V1",
        "lineage_digest": context.bindings.lineage_digest,
        "coordinate_manifest_sha256": context.bindings.coordinate_manifest_sha256,
        "realized_path": realized_path,
        "stage_digests": dict(stage_digests),
        "foundation_final_count": 24,
        "adapter_final_count": 72 if realized_path == "FULL_FIVE_CONTROLLER_PANEL" else 0,
        "complete": True,
        "partial_values_exposed": False,
        "interpretation_included": False,
        "test_only": context.bindings.test_only,
    }
    path = context.result_root / COMPLETION_INVENTORY_NAME
    if path.exists():
        if load_canonical_json(path, artifact_root=context.result_root) != payload:
            raise ProductionContractError("completion inventory differs on resume")
        return _sha256_bytes(path.read_bytes())
    return atomic_create_json(path, payload, artifact_root=context.result_root)


def load_default_production_services(context: RunContext) -> ProductionServices:
    """Feature-detect the separately owned concrete service without fallback."""

    try:
        from . import production_services as module  # noqa: F401
    except ImportError as error:
        raise ProductionContractError("production_services module is not installed") from error
    return _require_services_api(ConcreteProductionServices(context))


def execute_realized_path(context: RunContext, *, services: object) -> str:
    """Execute exactly one prerequisite-dependent complete realized path."""

    context.permit.require_active()
    api = _require_services_api(services)
    torch.set_num_threads(1)
    result_path = context.result_root / FINAL_RESULT_NAME
    completed = _load_completed_result_digest(context, result_path)
    if completed is not None:
        return completed
    workers = int(getattr(context.permit, "workers", 1))
    foundation_receipts = _parallel_ordered(
        workers,
        lambda value: api.foundation_final(context, int(value)),
        tuple(REPLICATES),
    )
    foundation_barrier = require_foundation_checkpoint_barrier(
        foundation_receipts, context.bindings
    )
    foundation_gate, foundation_inference_sha = api.foundation_competence(
        context, foundation_receipts
    )
    foundation_path = context.result_root / FOUNDATION_GATE_NAME
    if foundation_path.exists():
        retained_foundation = load_foundation_gate(
            foundation_path,
            artifact_root=context.result_root,
            barrier=foundation_barrier,
            bindings=context.bindings,
        )
        if retained_foundation != foundation_gate:
            raise ProductionContractError("resumed foundation gate differs")
        foundation_gate = retained_foundation
    else:
        publish_foundation_gate(
            foundation_path,
            foundation_gate,
            artifact_root=context.result_root,
            barrier=foundation_barrier,
            bindings=context.bindings,
        )
    if foundation_gate.outcome is GateOutcome.NONPASS:
        _publish_or_validate_completion(
            context,
            realized_path="FOUNDATION_ONLY",
            stage_digests={
                "foundation_gate_sha256": _sha256_bytes(foundation_path.read_bytes())
            },
        )
        return publish_complete_result(
            result_path,
            artifact_root=context.result_root,
            bindings=context.bindings,
            result_code=ResultCode.FOUNDATION_NOT_ESTABLISHED,
            complete_inference_sha256=foundation_inference_sha,
            foundation_gate_path=foundation_path,
            foundation_gate=foundation_gate,
        )
    opportunity_path = context.result_root / OPPORTUNITY_RECEIPT_NAME
    if opportunity_path.exists():
        opportunity = load_opportunity_receipt(
            opportunity_path,
            artifact_root=context.result_root,
            foundation_gate_path=foundation_path,
            foundation_gate=foundation_gate,
            bindings=context.bindings,
        )
        opportunity_inference_sha = opportunity.complete_stage_sha256
    else:
        opportunity, opportunity_inference_sha = api.opportunity(context, foundation_gate)
        foundation_file_sha = _sha256_bytes(foundation_path.read_bytes())
        opportunity = OpportunityReceipt(
            outcome=opportunity.outcome,
            complete_stage_sha256=opportunity.complete_stage_sha256,
            foundation_gate_sha256=foundation_file_sha,
        )
        publish_opportunity_receipt(
            opportunity_path,
            opportunity,
            artifact_root=context.result_root,
            foundation_gate_path=foundation_path,
            foundation_gate=foundation_gate,
            bindings=context.bindings,
        )
    if opportunity.outcome is GateOutcome.NONPASS:
        _publish_or_validate_completion(
            context,
            realized_path="FOUNDATION_AND_OPPORTUNITY",
            stage_digests={
                "foundation_gate_sha256": _sha256_bytes(foundation_path.read_bytes()),
                "opportunity_receipt_sha256": _sha256_bytes(opportunity_path.read_bytes()),
            },
        )
        return publish_complete_result(
            result_path,
            artifact_root=context.result_root,
            bindings=context.bindings,
            result_code=ResultCode.OPPORTUNITY_NOT_ESTABLISHED,
            complete_inference_sha256=opportunity_inference_sha,
            foundation_gate_path=foundation_path,
            foundation_gate=foundation_gate,
            opportunity_path=opportunity_path,
            opportunity=opportunity,
        )
    adapter_permit = issue_adapter_execution_permit(
        foundation_gate_path=foundation_path,
        foundation_gate=foundation_gate,
        opportunity_path=opportunity_path,
        opportunity=opportunity,
        artifact_root=context.result_root,
        bindings=context.bindings,
    )
    adapter_slots = tuple(
        (replicate, arm) for replicate in REPLICATES for arm in ADAPTER_ARMS
    )
    adapters = _parallel_ordered(
        workers,
        lambda value: api.adapter_final(
            context, int(value[0]), str(value[1]), adapter_permit
        ),
        adapter_slots,
    )
    final_barrier = require_final_panel_barrier(
        adapters,
        foundation_barrier=foundation_barrier,
        foundation_gate_path=foundation_path,
        foundation_gate=foundation_gate,
        opportunity_path=opportunity_path,
        opportunity=opportunity,
        artifact_root=context.result_root,
        bindings=context.bindings,
    )
    final_permit = issue_final_evaluation_permit(
        final_barrier, bindings=context.bindings
    )
    final_panel, result_code, final_inference_sha = api.final_evaluation(
        context, final_permit, final_barrier
    )
    _publish_or_validate_completion(
        context,
        realized_path="FULL_FIVE_CONTROLLER_PANEL",
        stage_digests={
            "foundation_gate_sha256": _sha256_bytes(foundation_path.read_bytes()),
            "opportunity_receipt_sha256": _sha256_bytes(opportunity_path.read_bytes()),
            "final_panel_sha256": final_panel.complete_panel_sha256,
            "final_panel_barrier_sha256": final_panel.barrier_sha256,
        },
    )
    return publish_complete_result(
        result_path,
        artifact_root=context.result_root,
        bindings=context.bindings,
        result_code=result_code,
        complete_inference_sha256=final_inference_sha,
        foundation_gate_path=foundation_path,
        foundation_gate=foundation_gate,
        opportunity_path=opportunity_path,
        opportunity=opportunity,
        final_barrier=final_barrier,
        final_panel=final_panel,
    )


def run_with_root_lease(
    *,
    lease: Mapping[str, object],
    lease_path: Path,
    actual_argv: Sequence[str],
    now: datetime,
    preactivity: PreactivityState,
    shared_guard: Callable[..., Mapping[str, object]],
    services: object | None,
    master_sealer: MasterSealer | None = None,
) -> str:
    """Admit and run only after exact command/source/lease/coordinate validation."""

    preactivity.validate_seal()
    expected_argv = execution_argv(Path(lease_path))
    if list(actual_argv) != expected_argv:
        raise ProductionContractError("actual production argv differs from the Root lease")
    lease_raw = Path(lease_path).read_bytes()
    try:
        persisted = json.loads(lease_raw.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ProductionContractError("Root lease bytes are unreadable") from error
    if not isinstance(persisted, dict) or persisted != dict(lease):
        raise ProductionContractError("supplied Root lease differs from installed bytes")
    frozen_lineage = same_coordinate_repair_lineage(preactivity)
    permit = validate_root_lease(
        lease,
        now=now,
        repository_root=preactivity.repository_root,
        lease_path=Path(lease_path),
        source_manifest_sha256=preactivity.source_manifest_sha256,
        preactivity_acceptance_sha256=preactivity.preactivity_acceptance_sha256,
        native_binding=preactivity.native_binding,
        shared_guard=shared_guard,
        frozen_identity_lineage=frozen_lineage,
    )
    if Path(permit.paths["run_identity_path"]).resolve() != preactivity.paths["run_identity_path"]:
        raise ProductionContractError("lease run identity path differs after admission")
    context = _load_bound_identity(
        preactivity,
        permit=permit,
        lease_sha256=_sha256_bytes(lease_raw),
        master_sealer=master_sealer or WindowsDPAPIMasterSealer(),
    )
    selected = load_default_production_services(context) if services is None else services
    return execute_realized_path(context, services=selected)


def test_only_run_context(result_root: Path, *, token: str = "runner") -> RunContext:
    """Conspicuous mechanics-only context; never accepted by production admission."""

    class _TestPermit:
        lease_id = f"TEST_ONLY:{token}"
        def require_active(self, *, now: datetime | None = None) -> None:
            return None
    root = Path(result_root).resolve()
    return RunContext(
        permit=_TestPermit(),  # type: ignore[arg-type]
        bindings=test_only_bindings(token=token),
        native_binding={},
        result_root=root,
        frontier_root=root / "frontiers",
        _master=b"\0" * 32,
    )
