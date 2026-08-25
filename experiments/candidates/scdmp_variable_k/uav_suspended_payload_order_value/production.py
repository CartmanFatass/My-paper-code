"""Two-phase foreground production adapter for SCDMP UAV revision 02.

``train`` may create or resume one blinded run identity and may only train the
54 checkpoint slots plus publish their factual completion inventory.
``evaluate`` requires that inventory and a separately created CM acceptance
bound to the same run identity before it can evaluate, infer, or publish the
atomic result.  The adapter contains no acceptance writer, scheduler, retry,
detach, fallback, or legacy one-shot route.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Final, Protocol, runtime_checkable

from . import runner as runner_module
from .inference import VALIDITY_FLAGS
from .lease import (
    EVALUATE_PHASE,
    EMPIRICAL_SOURCE_MANIFEST_NAME,
    TRAIN_PHASE,
    empirical_source_manifest_identity,
    validate_lease,
    validate_lease_envelope,
)
from .preactivity import require_direction_cpp_batched_production
from .runner import atomic_json_publisher


OCCUPIED_REGISTRY_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_OCCUPIED_IDENTITY_DIGESTS_V1"
TRAIN_TERMINAL_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_TRAIN_TERMINAL_V1"
EVALUATE_TERMINAL_SCHEMA: Final[str] = "SCDMP_UAV_SP_R02_EVALUATE_TERMINAL_V1"
PREFLIGHT_PHASE: Final[str] = "PREFLIGHT"
PHASES: Final[tuple[str, ...]] = (PREFLIGHT_PHASE, TRAIN_PHASE, EVALUATE_PHASE)

REQUIRED_PRODUCTION_SOURCE_PATHS: Final[tuple[str, ...]] = (
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/runner.py",
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/production_training.py",
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/production_evaluation.py",
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/production.py",
    "experiments/candidates/scdmp_variable_k/uav_suspended_payload_order_value/__main__.py",
)

class ProductionCLIError(RuntimeError):
    """A command, binding, source, lifecycle, or phase API fence failed."""


@runtime_checkable
class TrainingPhaseRunner(Protocol):
    def __call__(self, **kwargs: object) -> Mapping[str, object]: ...


@runtime_checkable
class EvaluationPhaseRunner(Protocol):
    def __call__(self, **kwargs: object) -> object: ...


@dataclass(frozen=True)
class TwoPhaseRunnerAPI:
    train: TrainingPhaseRunner
    evaluate: EvaluationPhaseRunner


@dataclass(frozen=True)
class CLIPaths:
    lease: Path
    result_root: Path
    result_path: Path
    run_identity_path: Path
    checkpoint_completion_path: Path
    cm_acceptance_path: Path
    train_terminal_record: Path
    evaluate_terminal_record: Path
    occupied_digest_registry: Path | None


@dataclass(frozen=True)
class PreparedExecution:
    phase: str
    paths: CLIPaths
    lease: Mapping[str, object]
    core_lease: Mapping[str, object]
    validity: Mapping[str, bool]
    occupied_identity_digests: tuple[str, ...]
    workers: int


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii") + b"\n"


def _require_absolute(path: str | Path, label: str) -> Path:
    supplied = Path(path).expanduser()
    if not supplied.is_absolute():
        raise ProductionCLIError(f"{label} must be an explicit absolute path")
    return supplied.resolve()


def _require_under_root(path: Path, root: Path, label: str) -> None:
    if path == root:
        raise ProductionCLIError(f"{label} must name a file below result_root")
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ProductionCLIError(f"{label} escapes the exact lease-bound result_root") from error


def _path_identity(path: str | Path) -> str:
    """Canonical identity matching Windows extended/non-extended path spellings."""

    resolved = str(Path(path).resolve())
    if os.name == "nt":
        if resolved.startswith("\\\\?\\UNC\\"):
            resolved = "\\\\" + resolved[8:]
        elif resolved.startswith("\\\\?\\"):
            resolved = resolved[4:]
        return os.path.normcase(os.path.normpath(resolved))
    return os.path.normpath(resolved)


def _read_json_mapping(path: Path, label: str) -> dict[str, object]:
    if not path.is_file():
        raise ProductionCLIError(f"{label} is missing or not a regular file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProductionCLIError(f"{label} is not readable JSON") from error
    if not isinstance(value, Mapping):
        raise ProductionCLIError(f"{label} must contain one JSON object")
    return dict(value)


def _resolve_cli_paths(
    *, lease_path: str | Path, result_root: str | Path, result_path: str | Path,
    run_identity_path: str | Path, checkpoint_completion_path: str | Path,
    cm_acceptance_path: str | Path, train_terminal_record: str | Path,
    evaluate_terminal_record: str | Path,
    occupied_digest_registry: str | Path | None,
) -> CLIPaths:
    root = _require_absolute(result_root, "result_root")
    output_values = {
        "result_path": _require_absolute(result_path, "result_path"),
        "run_identity_path": _require_absolute(run_identity_path, "run_identity_path"),
        "checkpoint_completion_path": _require_absolute(
            checkpoint_completion_path, "checkpoint_completion_path"
        ),
        "cm_acceptance_path": _require_absolute(cm_acceptance_path, "cm_acceptance_path"),
        "train_terminal_record": _require_absolute(train_terminal_record, "train_terminal_record"),
        "evaluate_terminal_record": _require_absolute(
            evaluate_terminal_record, "evaluate_terminal_record"
        ),
    }
    for label, path in output_values.items():
        _require_under_root(path, root, label)
    if len(set(output_values.values())) != len(output_values):
        raise ProductionCLIError("all lease-bound lifecycle/output paths must be distinct")
    registry = None if occupied_digest_registry is None else _require_absolute(
        occupied_digest_registry, "occupied_digest_registry"
    )
    return CLIPaths(
        lease=_require_absolute(lease_path, "lease"), result_root=root,
        occupied_digest_registry=registry, **output_values,
    )


def _validate_execution_binding(
    lease: Mapping[str, object], paths: CLIPaths, *, phase: str
) -> dict[str, bool]:
    if phase not in PHASES:
        raise ProductionCLIError("phase differs from PREFLIGHT/TRAIN/EVALUATE")
    lease_phase = lease.get("phase")
    if lease_phase not in (TRAIN_PHASE, EVALUATE_PHASE):
        raise ProductionCLIError("lease phase differs from TRAIN/EVALUATE")
    if phase != PREFLIGHT_PHASE and phase != lease_phase:
        raise ProductionCLIError("command phase differs from the exact lease phase")
    expected_paths = {
        "result_root": _path_identity(paths.result_root),
        "result_path": _path_identity(paths.result_path),
        "run_identity_path": _path_identity(paths.run_identity_path),
        "completion_inventory_path": _path_identity(paths.checkpoint_completion_path),
        "cm_acceptance_path": _path_identity(paths.cm_acceptance_path),
        "train_terminal_path": _path_identity(paths.train_terminal_record),
        "evaluation_terminal_path": _path_identity(paths.evaluate_terminal_record),
    }
    raw_paths = lease.get("paths")
    if not isinstance(raw_paths, Mapping) or set(raw_paths) != set(expected_paths):
        raise ProductionCLIError("lease lifecycle/output path inventory differs")
    canonical_paths: dict[str, str] = {}
    for field in expected_paths:
        raw = raw_paths.get(field)
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            raise ProductionCLIError(f"lease path {field!r} must be absolute")
        canonical_paths[field] = _path_identity(raw)
    if canonical_paths != expected_paths:
        raise ProductionCLIError("CLI lifecycle/output paths differ from the exact lease")
    resources = lease.get("resources")
    if (
        not isinstance(resources, Mapping)
        or resources.get("cpu_only") is not True
        or resources.get("gpu_count") != 0
        or resources.get("torch_threads") != 1
    ):
        raise ProductionCLIError("lease is not CPU-only with one Torch thread")
    registry = lease.get("occupied_digest_registry")
    if registry is None:
        if paths.occupied_digest_registry is not None:
            raise ProductionCLIError("occupied registry argument is not lease-bound")
    else:
        if not isinstance(registry, Mapping) or set(registry) != {"path", "sha256"}:
            raise ProductionCLIError("occupied registry lease binding differs")
        if paths.occupied_digest_registry is None:
            raise ProductionCLIError("lease-bound occupied registry argument is required")
        if registry.get("path") != str(paths.occupied_digest_registry):
            raise ProductionCLIError("occupied registry path differs from the lease")
        digest = registry.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64 or digest != digest.lower():
            raise ProductionCLIError("occupied registry SHA-256 is invalid")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ProductionCLIError("occupied registry SHA-256 is invalid") from error
    return {flag: True for flag in VALIDITY_FLAGS}


def _load_occupied_digests(
    paths: CLIPaths, lease: Mapping[str, object]
) -> tuple[str, ...]:
    binding = lease.get("occupied_digest_registry")
    if binding is None:
        return ()
    assert isinstance(binding, Mapping) and paths.occupied_digest_registry is not None
    raw = paths.occupied_digest_registry.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise ProductionCLIError("occupied registry bytes differ from the lease")
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProductionCLIError("occupied registry is not ASCII JSON") from error
    if (
        not isinstance(value, Mapping) or set(value) != {"schema", "digests"}
        or value.get("schema") != OCCUPIED_REGISTRY_SCHEMA
        or raw != _canonical_json_bytes(dict(value))
    ):
        raise ProductionCLIError("occupied registry schema/bytes differ")
    digests = value.get("digests")
    if not isinstance(digests, list):
        raise ProductionCLIError("occupied registry inventory is invalid")
    observed: list[str] = []
    for digest in digests:
        if not isinstance(digest, str) or len(digest) != 64 or digest != digest.lower():
            raise ProductionCLIError("occupied identity digest is invalid")
        try:
            int(digest, 16)
        except ValueError as error:
            raise ProductionCLIError("occupied identity digest is invalid") from error
        if digest in observed:
            raise ProductionCLIError("occupied identity digest is duplicated")
        observed.append(digest)
    if observed != sorted(observed):
        raise ProductionCLIError("occupied identity digests must be sorted")
    return tuple(observed)


def _validate_source_binding(core_lease: Mapping[str, object]) -> None:
    package_root = Path(__file__).resolve().parent
    identity = empirical_source_manifest_identity(package_root, require_final=True)
    if identity["sha256"] != core_lease.get("empirical_source_manifest_sha256"):
        raise ProductionCLIError("final empirical source manifest differs from the lease")
    value = _read_json_mapping(
        package_root / EMPIRICAL_SOURCE_MANIFEST_NAME, "empirical source manifest"
    )
    rows = value.get("files")
    if not isinstance(rows, list):
        raise ProductionCLIError("empirical source manifest inventory is absent")
    bound = {
        str(row.get("path")) for row in rows
        if isinstance(row, Mapping) and isinstance(row.get("path"), str)
    }
    if any(path not in bound for path in REQUIRED_PRODUCTION_SOURCE_PATHS):
        raise ProductionCLIError("final manifest omits a production phase source")


def _validate_path_kind(path: Path, label: str) -> None:
    if path.exists() and not path.is_file():
        raise ProductionCLIError(f"{label} exists and is not a regular file")


def _validate_output_state(paths: CLIPaths, *, phase: str) -> None:
    if paths.result_root.exists() and not paths.result_root.is_dir():
        raise ProductionCLIError("result_root exists and is not a directory")
    for label in (
        "result_path", "run_identity_path", "checkpoint_completion_path",
        "cm_acceptance_path", "train_terminal_record", "evaluate_terminal_record",
    ):
        _validate_path_kind(getattr(paths, label), label)
    if phase == TRAIN_PHASE:
        for label in (
            "result_path", "cm_acceptance_path", "evaluate_terminal_record",
        ):
            if getattr(paths, label).exists():
                raise ProductionCLIError(f"train phase requires absent create-only {label}")
    elif phase == EVALUATE_PHASE:
        for label in (
            "run_identity_path", "checkpoint_completion_path", "cm_acceptance_path",
            "train_terminal_record",
        ):
            if not getattr(paths, label).is_file():
                raise ProductionCLIError(f"evaluate phase requires existing {label}")
        for label in ("result_path", "evaluate_terminal_record"):
            if getattr(paths, label).exists():
                raise ProductionCLIError(f"evaluate phase requires absent create-only {label}")


def prepare_execution(
    *, phase: str, lease_path: str | Path, result_root: str | Path,
    result_path: str | Path, run_identity_path: str | Path,
    checkpoint_completion_path: str | Path, cm_acceptance_path: str | Path,
    train_terminal_record: str | Path, evaluate_terminal_record: str | Path,
    occupied_digest_registry: str | Path | None = None,
    now: datetime | None = None,
) -> PreparedExecution:
    """Validate all read-only command, lease, source, and phase path bindings."""
    checked_at = now or datetime.now(timezone.utc)
    paths = _resolve_cli_paths(
        lease_path=lease_path, result_root=result_root, result_path=result_path,
        run_identity_path=run_identity_path,
        checkpoint_completion_path=checkpoint_completion_path,
        cm_acceptance_path=cm_acceptance_path,
        train_terminal_record=train_terminal_record,
        evaluate_terminal_record=evaluate_terminal_record,
        occupied_digest_registry=occupied_digest_registry,
    )
    lease = _read_json_mapping(paths.lease, "lease")
    validity = _validate_execution_binding(lease, paths, phase=phase)
    validate_lease_envelope(lease, now=checked_at)
    _validate_source_binding(lease)
    occupied = _load_occupied_digests(paths, lease)
    _validate_output_state(paths, phase=phase)
    resources = lease.get("resources")
    assert isinstance(resources, Mapping)
    return PreparedExecution(
        phase=phase, paths=paths, lease=lease, core_lease=lease, validity=validity,
        occupied_identity_digests=occupied,
        workers=int(resources["independent_workers"]),
    )


def _configure_cpu_runtime() -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    import torch
    torch.set_num_threads(1)
    if torch.get_num_threads() != 1:
        raise ProductionCLIError("Torch did not retain one CPU thread per worker")


class _TrainingServiceAdapter:
    """Bind the persisted public run identity to the concrete trainer lazily."""

    def __init__(self, *, result_root: Path, run_identity_path: Path, lease: Mapping[str, object]):
        from .production_training import ProductionTrainingService, TrainingSourceBindings

        self._root = result_root
        self._identity_path = run_identity_path
        self._bindings = TrainingSourceBindings.from_lease(lease)
        self._service = ProductionTrainingService(result_root, bindings=self._bindings)
        self._runner_identity_digest: str | None = None

    @property
    def result_root(self) -> Path:
        return self._root

    def _bind(self, run_identity_digest: str) -> None:
        from .production_training import TrainingRunIdentity

        raw = self._identity_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != run_identity_digest:
            raise ProductionCLIError("training adapter run identity digest differs")
        try:
            value = json.loads(raw.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProductionCLIError("training adapter run identity is unreadable") from error
        if not isinstance(value, Mapping) or not isinstance(value.get("master_digest"), str):
            raise ProductionCLIError("training adapter run identity lacks public master digest")
        identity = TrainingRunIdentity.create(
            master_digest=str(value["master_digest"]), bindings=self._bindings
        )
        self._service.bind_run_identity(identity)
        if self._runner_identity_digest not in (None, run_identity_digest):
            raise ProductionCLIError("training adapter run identity changed")
        self._runner_identity_digest = run_identity_digest

    def create_or_resume_frontier(
        self, permit: object, rng: object, replicate: int, arm: str,
        run_identity_digest: str,
    ) -> object:
        self._bind(run_identity_digest)
        return self._service.create_frontier(permit, rng, replicate, arm)

    def train_slot(
        self, permit: object, rng: object, frontier: object,
        run_identity_digest: str,
    ) -> object:
        from .frontier import CheckpointCompletion

        self._bind(run_identity_digest)
        receipt = self._service.train_slot(permit, rng, frontier)
        receipt.validate_completion()
        completion_path = (
            self._root / "checkpoint-completions"
            / f"replicate-{int(receipt.replicate):02d}-{str(receipt.arm)}.json"
        ).resolve()
        payload = {
            "schema": "SCDMP_UAV_SP_R02_CHECKPOINT_COMPLETION_V1",
            "replicate": receipt.replicate,
            "arm": receipt.arm,
            "coordinate_digest": receipt.coordinate_digest,
            "run_identity_digest": run_identity_digest,
            "checkpoint_path": receipt.checkpoint_path,
            "checkpoint_digest": receipt.checkpoint_digest,
            "optimizer_step": receipt.optimizer_step,
            "origin_lease_id": receipt.origin_lease_id,
            "empirical_source_manifest_sha256": receipt.empirical_source_manifest_sha256,
            "card_revision": receipt.card_revision,
            "card_sha256": receipt.card_sha256,
            "native_binding_digest": receipt.native_binding_digest,
            "technically_accepted": False,
            "evaluation_observed": False,
        }
        payload_digest = _atomic_create_or_validate_json(completion_path, payload)
        completion = CheckpointCompletion(
            replicate=receipt.replicate,
            arm=receipt.arm,
            coordinate_digest=receipt.coordinate_digest,
            run_identity_digest=run_identity_digest,
            checkpoint_path=receipt.checkpoint_path,
            checkpoint_digest=receipt.checkpoint_digest,
            completion_payload_path=str(completion_path),
            completion_payload_digest=payload_digest,
            optimizer_step=receipt.optimizer_step,
            technically_accepted=False,
            evaluation_observed=False,
        )
        completion.validate(result_root=self._root, verify_checkpoint=True)
        return completion


class _RunBoundModelLoader:
    def __init__(self, *, service: object, bindings: object, run_identity_path: Path):
        self._service = service
        self._bindings = bindings
        self._identity_path = run_identity_path
        self._bound = False

    def _bind(self) -> None:
        if self._bound:
            return
        from .production_training import TrainingRunIdentity

        value = _read_json_mapping(self._identity_path, "run identity")
        master_digest = value.get("master_digest")
        if not isinstance(master_digest, str):
            raise ProductionCLIError("run identity lacks public master digest")
        self._service.bind_run_identity(
            TrainingRunIdentity.create(master_digest=master_digest, bindings=self._bindings)
        )
        self._bound = True

    def load_final_model(self, **kwargs: object) -> object:
        self._bind()
        return self._service.load_final_model(**kwargs)


class _EvaluationServiceAdapter:
    def __init__(self, evaluation: object, publisher: Callable[..., object], root: Path):
        self._evaluation = evaluation
        self._publisher = publisher
        self.result_root = root

    def evaluate_panel(self, *args: object, **kwargs: object) -> object:
        return self._evaluation.evaluate_panel(*args, **kwargs)

    def support_panel(self, *args: object, **kwargs: object) -> object:
        return self._evaluation.support_panel(*args, **kwargs)

    def publish_atomic(self, *args: object, **kwargs: object) -> object:
        return self._publisher(*args, **kwargs)


def build_training_services(
    *, result_root: Path, run_identity_path: Path, lease: Mapping[str, object]
) -> object:
    """Expose only frontier creation and training to the train-phase runner."""
    training = _TrainingServiceAdapter(
        result_root=result_root, run_identity_path=run_identity_path, lease=lease
    )
    if training.result_root != result_root:
        raise ProductionCLIError("training service changed the exact result_root")
    return training


def build_evaluation_services(
    *, result_root: Path, result_path: Path, run_identity_path: Path,
    lease: Mapping[str, object]
) -> object:
    """Expose only accepted-checkpoint loading, evaluation, and publication."""
    from .production_evaluation import ProductionEvaluationService
    from .production_training import ProductionTrainingService, TrainingSourceBindings
    bindings = TrainingSourceBindings.from_lease(lease)
    training = ProductionTrainingService(result_root, bindings=bindings)
    loader = _RunBoundModelLoader(
        service=training, bindings=bindings, run_identity_path=run_identity_path
    )
    evaluation = ProductionEvaluationService(result_root=result_root, model_loader=loader)
    if training.result_root != result_root or evaluation.result_root != result_root:
        raise ProductionCLIError("evaluation services changed the exact result_root")
    return _EvaluationServiceAdapter(
        evaluation, atomic_json_publisher(result_path), result_root
    )


def resolve_two_phase_runner_api(module: object = runner_module) -> TwoPhaseRunnerAPI:
    """Feature-detect the runner split; the legacy one-shot API is never used."""
    train = getattr(module, "run_training_phase", None)
    evaluate = getattr(module, "run_evaluation_phase", None)
    if not callable(train) or not callable(evaluate):
        raise ProductionCLIError(
            "runner lacks required run_training_phase/run_evaluation_phase APIs; "
            "legacy run_empirical_panel is forbidden"
        )
    return TwoPhaseRunnerAPI(train=train, evaluate=evaluate)


def _prevalidate_native(
    prepared: PreparedExecution, *, now: datetime
) -> Callable[..., Mapping[str, object]]:
    receipt_box: dict[str, Mapping[str, object]] = {}
    def capture(*, batch_width: int) -> Mapping[str, object]:
        if batch_width != prepared.workers:
            raise ProductionCLIError("native guard batch width differs from the lease")
        receipt = require_direction_cpp_batched_production(batch_width=batch_width)
        receipt_box["receipt"] = receipt
        return receipt
    validate_lease(
        prepared.core_lease, now=now, package_root=Path(__file__).resolve().parent,
        native_guard=capture,
    )
    receipt = receipt_box.get("receipt")
    if receipt is None:
        raise ProductionCLIError("native prevalidation returned no exact receipt")
    def cached(*, batch_width: int) -> Mapping[str, object]:
        if batch_width != prepared.workers:
            raise ProductionCLIError("cached native guard width differs from the lease")
        return receipt
    return cached


def _runner_kwargs(function: Callable[..., object], available: Mapping[str, object]) -> dict[str, object]:
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError) as error:
        raise ProductionCLIError("runner phase API has no inspectable signature") from error
    bound: dict[str, object] = {}
    for name, parameter in signature.parameters.items():
        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            raise ProductionCLIError("runner phase API contains a positional-only parameter")
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if name in available:
            bound[name] = available[name]
        elif parameter.default is inspect.Parameter.empty:
            raise ProductionCLIError(f"runner phase API requires unsupported parameter {name!r}")
    return bound


def _require_parameter_group(
    function: Callable[..., object], alternatives: tuple[str, ...], label: str
) -> None:
    if not any(name in inspect.signature(function).parameters for name in alternatives):
        raise ProductionCLIError(f"runner phase API omits required {label} binding")


def _invoke_training_runner(
    function: Callable[..., object], *, prepared: PreparedExecution,
    services: object, now: datetime,
    native_guard: Callable[..., Mapping[str, object]],
    master_source: Callable[[int], bytes],
) -> object:
    for alternatives, label in (
        (("services", "training_services", "create_frontier"), "training service"),
        (("run_identity_path",), "run identity"),
        (("checkpoint_completion_path", "completion_inventory_path"), "completion inventory"),
        (("occupied_identity_digests",), "occupied identity registry"),
        (("train_terminal_path",), "train terminal"),
        (("master_source",), "master source"),
        (("cached_native_guard",), "cached native guard"),
    ):
        _require_parameter_group(function, alternatives, label)
    available: dict[str, object] = {
        "lease": prepared.core_lease, "now": now, "services": services,
        "training_services": services,
        "run_identity_path": prepared.paths.run_identity_path,
        "checkpoint_completion_path": prepared.paths.checkpoint_completion_path,
        "completion_inventory_path": prepared.paths.checkpoint_completion_path,
        "occupied_identity_digests": prepared.occupied_identity_digests,
        "train_terminal_path": prepared.paths.train_terminal_record,
        "cached_native_guard": native_guard, "master_source": master_source,
        "source_manifest_path": None,
    }
    return function(**_runner_kwargs(function, available))


def _invoke_evaluation_runner(
    function: Callable[..., object], *, prepared: PreparedExecution,
    services: object, now: datetime,
    native_guard: Callable[..., Mapping[str, object]],
) -> object:
    for alternatives, label in (
        (("services", "evaluation_services", "evaluate_panel"), "evaluation service"),
        (("run_identity_path",), "run identity"),
        (("checkpoint_completion_path", "completion_inventory_path"), "completion inventory"),
        (("cm_acceptance_path", "acceptance_path"), "CM acceptance"),
        (("result_path",), "result path"),
        (("evaluation_terminal_path",), "evaluation terminal"),
        (("validity",), "validity"),
        (("cached_native_guard",), "cached native guard"),
    ):
        _require_parameter_group(function, alternatives, label)
    available: dict[str, object] = {
        "lease": prepared.core_lease, "now": now, "services": services,
        "evaluation_services": services,
        "run_identity_path": prepared.paths.run_identity_path,
        "checkpoint_completion_path": prepared.paths.checkpoint_completion_path,
        "completion_inventory_path": prepared.paths.checkpoint_completion_path,
        "cm_acceptance_path": prepared.paths.cm_acceptance_path,
        "acceptance_path": prepared.paths.cm_acceptance_path,
        "result_path": prepared.paths.result_path,
        "evaluation_terminal_path": prepared.paths.evaluate_terminal_record,
        "validity": prepared.validity, "cached_native_guard": native_guard,
        "source_manifest_path": None,
    }
    return function(**_runner_kwargs(function, available))


def _atomic_create_or_validate_json(path: Path, value: Mapping[str, object]) -> str:
    encoded = _canonical_json_bytes(dict(value))
    if path.exists():
        if not path.is_file() or path.read_bytes() != encoded:
            raise ProductionCLIError("create-only factual record differs")
        return hashlib.sha256(encoded).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + f".{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise ProductionCLIError("factual record appeared during create-only publication") from error
    finally:
        if temporary.exists():
            temporary.unlink()
    return hashlib.sha256(encoded).hexdigest()


def _validate_training_completion(prepared: PreparedExecution, receipt: object) -> None:
    if getattr(receipt, "completion_count", None) != 54:
        raise ProductionCLIError("training runner did not report all 54 checkpoint slots")
    if getattr(receipt, "technically_accepted", None) is not False:
        raise ProductionCLIError("training runner self-asserted technical acceptance")
    if not prepared.paths.run_identity_path.is_file():
        raise ProductionCLIError("training runner did not persist the run identity")
    if not prepared.paths.checkpoint_completion_path.is_file():
        raise ProductionCLIError("training runner did not publish completion inventory")
    if prepared.paths.cm_acceptance_path.exists():
        raise ProductionCLIError("Operator training path created or raced with CM acceptance")
    if prepared.paths.result_path.exists():
        raise ProductionCLIError("training runner published a forbidden result")
    if not prepared.paths.train_terminal_record.is_file():
        raise ProductionCLIError("training runner wrote no train terminal")


def _validate_evaluation_completion(
    prepared: PreparedExecution, receipt: object
) -> Mapping[str, object]:
    publication = getattr(receipt, "publication", None)
    if not isinstance(publication, Mapping):
        raise ProductionCLIError("evaluation runner returned no atomic publication receipt")
    if publication.get("path") != str(prepared.paths.result_path):
        raise ProductionCLIError("evaluation result receipt changed the bound result path")
    if publication.get("complete_atomic_panel") is not True:
        raise ProductionCLIError("evaluation runner did not publish a complete atomic panel")
    if not prepared.paths.result_path.is_file():
        raise ProductionCLIError("evaluation result receipt names no result file")
    if not prepared.paths.evaluate_terminal_record.is_file():
        raise ProductionCLIError("evaluation runner wrote no evaluation terminal")
    return publication


def execute(
    *, phase: str, lease_path: str | Path, result_root: str | Path,
    result_path: str | Path, run_identity_path: str | Path,
    checkpoint_completion_path: str | Path, cm_acceptance_path: str | Path,
    train_terminal_record: str | Path, evaluate_terminal_record: str | Path,
    occupied_digest_registry: str | Path | None = None,
    now: datetime | None = None,
) -> Mapping[str, object]:
    checked_at = now or datetime.now(timezone.utc)
    prepared = prepare_execution(
        phase=phase, lease_path=lease_path, result_root=result_root,
        result_path=result_path, run_identity_path=run_identity_path,
        checkpoint_completion_path=checkpoint_completion_path,
        cm_acceptance_path=cm_acceptance_path,
        train_terminal_record=train_terminal_record,
        evaluate_terminal_record=evaluate_terminal_record,
        occupied_digest_registry=occupied_digest_registry, now=checked_at,
    )
    _configure_cpu_runtime()
    api = resolve_two_phase_runner_api()
    if phase == PREFLIGHT_PHASE:
        train_services = build_training_services(
            result_root=prepared.paths.result_root,
            run_identity_path=prepared.paths.run_identity_path,
            lease=prepared.core_lease,
        )
        evaluation_services = build_evaluation_services(
            result_root=prepared.paths.result_root,
            result_path=prepared.paths.result_path,
            run_identity_path=prepared.paths.run_identity_path,
            lease=prepared.core_lease,
        )
        del train_services, evaluation_services, api
        return {
            "phase": PREFLIGHT_PHASE, "lease_valid": True, "source_binding_valid": True,
            "two_phase_runner_available": True, "service_interfaces_available": True,
            "native_guard_called": False, "activity_started": False, "materialized": False,
        }
    cached_native_guard = _prevalidate_native(prepared, now=checked_at)
    def activity_source(length: int) -> bytes:
        return os.urandom(length)
    if phase == TRAIN_PHASE:
            services = build_training_services(
                result_root=prepared.paths.result_root,
                run_identity_path=prepared.paths.run_identity_path,
                lease=prepared.core_lease,
            )
            receipt = _invoke_training_runner(
                api.train, prepared=prepared, services=services, now=checked_at,
                native_guard=cached_native_guard, master_source=activity_source,
            )
            _validate_training_completion(prepared, receipt)
            public_receipt: Mapping[str, object] = {
                "phase": TRAIN_PHASE, "checkpoint_count": 54,
                "evaluation_started": False, "result_published": False,
                "cm_acceptance_created_by_operator": False,
            }
    else:
        services = build_evaluation_services(
            result_root=prepared.paths.result_root,
            result_path=prepared.paths.result_path,
            run_identity_path=prepared.paths.run_identity_path,
            lease=prepared.core_lease,
        )
        receipt = _invoke_evaluation_runner(
            api.evaluate, prepared=prepared, services=services, now=checked_at,
            native_guard=cached_native_guard,
        )
        public_receipt = _validate_evaluation_completion(prepared, receipt)
    return public_receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scdmp-uav-sp-r02-production",
        description="Two-phase foreground CPU production; no self-acceptance or fallback.",
    )
    parser.add_argument("--phase", choices=PHASES, required=True)
    parser.add_argument("--lease", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--result-path", type=Path, required=True)
    parser.add_argument("--run-identity-path", type=Path, required=True)
    parser.add_argument("--checkpoint-completion-path", type=Path, required=True)
    parser.add_argument("--cm-acceptance-path", type=Path, required=True)
    parser.add_argument("--train-terminal-record", type=Path, required=True)
    parser.add_argument("--evaluate-terminal-record", type=Path, required=True)
    parser.add_argument("--occupied-digest-registry", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt = execute(
            phase=args.phase, lease_path=args.lease, result_root=args.result_root,
            result_path=args.result_path, run_identity_path=args.run_identity_path,
            checkpoint_completion_path=args.checkpoint_completion_path,
            cm_acceptance_path=args.cm_acceptance_path,
            train_terminal_record=args.train_terminal_record,
            evaluate_terminal_record=args.evaluate_terminal_record,
            occupied_digest_registry=args.occupied_digest_registry,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"FAIL_CLOSED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(dict(receipt), sort_keys=True, separators=(",", ":")))
    return 0


__all__ = [
    "CLIPaths", "EVALUATE_TERMINAL_SCHEMA", "OCCUPIED_REGISTRY_SCHEMA", "PHASES",
    "PREFLIGHT_PHASE",
    "PreparedExecution", "ProductionCLIError", "REQUIRED_PRODUCTION_SOURCE_PATHS",
    "TRAIN_TERMINAL_SCHEMA", "TwoPhaseRunnerAPI", "build_evaluation_services",
    "build_parser", "build_training_services", "execute", "main",
    "prepare_execution", "resolve_two_phase_runner_api",
]
