"""Create-only atomic FCEOV artifacts with direct structural resume equality."""

from __future__ import annotations

import base64
from dataclasses import asdict, dataclass, fields
import importlib
from io import BytesIO
import json
import os
import pickle
import platform
from pathlib import Path
import tempfile
from typing import Callable, Mapping, Sequence

import torch
from torch import Tensor, nn

from .analysis import PanelAnalysis, analyze_complete_panel
from . import contracts as _contracts
from .contracts import (
    CANDIDATE_ACTIONS, CHECKPOINT_UPDATE, Disposition, FAILURE_LABELS, FOUNDATION_UPDATES,
    FoundationGate, GRAPHS, PANEL_WIDTH, RESOURCE_MAXIMA, TAPE_COUNT, PanelCell, TerminalFact,
)
from .training import ExactAdamW, OptimizerSnapshot, TrainingContractError
from .foundation import CompetenceRecord, FoundationActorCritic, analyze_competence
from .rng import AddressRNG


CHECKPOINT_SCHEMA = "SCDMP_FCEOV_CHECKPOINT_V4"
FOUNDATION_GATE_SCHEMA = "SCDMP_FCEOV_FOUNDATION_GATE_V4"
PANEL_SCHEMA = "SCDMP_FCEOV_COMPLETE_2X3_RESULT_V4"
TERMINAL_FACT_SCHEMA = "SCDMP_FCEOV_TERMINAL_V4"
RUN_RECORD_SCHEMA = "SCDMP_FCEOV_RUN_RECORD_V4"
RESUME_WITNESS_SCHEMA = "SCDMP_FCEOV_RESUME_WITNESS_V4"
PANEL_SLICE_SCHEMA = "SCDMP_FCEOV_PANEL_SLICE_V4"
PANEL_FRONTIER_SCHEMA = "SCDMP_FCEOV_PANEL_FRONTIER_V4"
SOURCE_NATIVE_SNAPSHOT_SCHEMA = "SCDMP_FCEOV_SOURCE_NATIVE_DIRECT_BYTES_V2"
FINAL_BUNDLE_SCHEMA = "SCDMP_FCEOV_FINAL_BUNDLE_V5"


class ArtifactContractError(RuntimeError):
    pass


_atomic_scratch_observer: Callable[[Path], None] | None = None


def set_atomic_scratch_observer(observer: Callable[[Path], None] | None) -> None:
    """Bind one process-local invocation observer for every atomic temp file."""

    global _atomic_scratch_observer
    _atomic_scratch_observer = observer


def observe_atomic_scratch(path: Path) -> None:
    """Observe a fully flushed temp before any publish or cleanup operation."""

    observer = _atomic_scratch_observer
    if observer is not None:
        observer(path)


@dataclass(frozen=True, slots=True)
class SourceNativeEntry:
    kind: str
    name: str
    resolved_path: str
    direct_bytes: bytes


@dataclass(frozen=True, slots=True)
class SourceNativeSnapshot:
    schema: str
    entries: tuple[SourceNativeEntry, ...]


@dataclass(frozen=True, slots=True)
class PreparedFinalBundle:
    fact: TerminalFact
    encoded: bytes

    @property
    def encoded_size(self) -> int:
        return len(self.encoded)


def _atomic_create(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        observe_atomic_scratch(temporary)
        os.link(temporary, path)
    except FileExistsError as error:
        raise ArtifactContractError("FCEOV artifacts are create-only") from error
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    _atomic_create(path, _canonical_json_bytes(value))


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("artifact is not finite direct JSON") from error


def _json_shape(value: object) -> object:
    """Return the exact list/dict/scalar shape persisted by canonical JSON."""

    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("artifact is not finite direct JSON") from error


def _atomic_replace_json(path: Path, value: Mapping[str, object]) -> None:
    """Atomically replace one technical frontier; scientific artifacts remain create-only."""

    try:
        payload = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("artifact is not finite direct JSON") from error
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        observe_atomic_scratch(temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _live_source_native_material() -> tuple[tuple[str, str, Path], ...]:
    """Resolve the exact source files and the binary loaded by the native bridge."""

    manifest = _contracts.Manifest()
    package_root = Path(__file__).resolve().parent
    owned = tuple(
        ("owned_python", module_name, (package_root / f"{module_name}.py").resolve())
        for module_name in manifest.source_modules
    )
    sibling_package = __package__.rsplit(".", 1)[0]
    dependencies: list[tuple[str, str, Path]] = []
    for reference in manifest.allowed_dependencies:
        module_name, _ = reference.split(":", 1)
        module = importlib.import_module(f"{sibling_package}.{module_name}")
        module_file = getattr(module, "__file__", None)
        if not isinstance(module_file, str):
            raise ArtifactContractError(f"allowlisted dependency source is unavailable: {module_name}")
        source_path = Path(module_file)
        if source_path.suffix in {".pyc", ".pyo"}:
            source_path = source_path.with_suffix(".py")
        dependencies.append(("dependency_python", module_name, source_path.resolve()))

    native_module_name = "target_bound_competent_controller_order_value.native_backend"
    native_module = importlib.import_module(f"{sibling_package}.{native_module_name}")
    native_source = Path(getattr(native_module, "_SOURCE")).resolve()
    library = native_module.require_cpp_batched_backend()
    library_name = vars(library).get("_name")
    if not isinstance(library_name, (str, bytes, os.PathLike)):
        raise ArtifactContractError("loaded native binary path is unavailable")
    native_binary = Path(library_name).resolve()
    return owned + tuple(dependencies) + (
        ("native_source", "tbcc_backend.cpp", native_source),
        ("native_binary", "loaded_tbcc_backend", native_binary),
    )


def _validate_source_native_snapshot(snapshot: SourceNativeSnapshot) -> SourceNativeSnapshot:
    if not isinstance(snapshot, SourceNativeSnapshot) or snapshot.schema != SOURCE_NATIVE_SNAPSHOT_SCHEMA:
        raise ArtifactContractError("source/native snapshot typed schema differs")
    manifest = _contracts.Manifest()
    expected_keys = (
        tuple(("owned_python", name) for name in manifest.source_modules)
        + tuple(
            ("dependency_python", reference.split(":", 1)[0])
            for reference in manifest.allowed_dependencies
        )
        + (("native_source", "tbcc_backend.cpp"), ("native_binary", "loaded_tbcc_backend"))
    )
    if tuple((entry.kind, entry.name) for entry in snapshot.entries) != expected_keys:
        raise ArtifactContractError("source/native snapshot is not the exact ordered 19-entry inventory")
    names: set[tuple[str, str]] = set()
    for entry in snapshot.entries:
        if (
            not isinstance(entry, SourceNativeEntry)
            or entry.kind not in {"owned_python", "dependency_python", "native_source", "native_binary"}
            or not isinstance(entry.name, str)
            or not entry.name
            or not isinstance(entry.resolved_path, str)
            or not entry.resolved_path
            or not isinstance(entry.direct_bytes, bytes)
        ):
            raise ArtifactContractError("source/native snapshot entry differs")
        key = (entry.kind, entry.name)
        if key in names:
            raise ArtifactContractError("source/native snapshot entry is duplicated")
        names.add(key)
    return snapshot


def _source_native_snapshot_payload(snapshot: SourceNativeSnapshot) -> dict[str, object]:
    snapshot = _validate_source_native_snapshot(snapshot)
    return {
        "schema": snapshot.schema,
        "entries": [
            {
                "kind": entry.kind,
                "name": entry.name,
                "resolved_path": entry.resolved_path,
                "length_bytes": len(entry.direct_bytes),
                "direct_bytes_b64": base64.b64encode(entry.direct_bytes).decode("ascii"),
            }
            for entry in snapshot.entries
        ],
    }


def _decode_source_native_snapshot(value: object) -> SourceNativeSnapshot:
    if not isinstance(value, dict) or set(value) != {"schema", "entries"}:
        raise ArtifactContractError("source/native snapshot fields differ")
    raw_entries = value["entries"]
    if not isinstance(raw_entries, list):
        raise ArtifactContractError("source/native snapshot entry inventory differs")
    entries: list[SourceNativeEntry] = []
    try:
        for row in raw_entries:
            if not isinstance(row, dict) or set(row) != {
                "kind", "name", "resolved_path", "length_bytes", "direct_bytes_b64",
            }:
                raise ArtifactContractError("source/native snapshot entry fields differ")
            encoded = row["direct_bytes_b64"]
            if not isinstance(encoded, str):
                raise ArtifactContractError("source/native snapshot direct bytes differ")
            direct = base64.b64decode(encoded.encode("ascii"), validate=True)
            if base64.b64encode(direct).decode("ascii") != encoded:
                raise ArtifactContractError("source/native snapshot base64 is not canonical")
            if (
                isinstance(row["length_bytes"], bool)
                or not isinstance(row["length_bytes"], int)
                or row["length_bytes"] != len(direct)
            ):
                raise ArtifactContractError("source/native snapshot direct byte length differs")
            entries.append(SourceNativeEntry(
                str(row["kind"]), str(row["name"]), str(row["resolved_path"]), direct,
            ))
    except (UnicodeEncodeError, ValueError) as error:
        raise ArtifactContractError("source/native snapshot direct bytes cannot be decoded") from error
    snapshot = _validate_source_native_snapshot(SourceNativeSnapshot(str(value["schema"]), tuple(entries)))
    if value != _source_native_snapshot_payload(snapshot):
        raise ArtifactContractError("source/native snapshot typed payload differs")
    return snapshot


def capture_source_native_snapshot() -> SourceNativeSnapshot:
    entries: list[SourceNativeEntry] = []
    try:
        for kind, name, path in _live_source_native_material():
            resolved = path.resolve()
            entries.append(SourceNativeEntry(kind, name, str(resolved), resolved.read_bytes()))
    except OSError as error:
        raise ArtifactContractError("source/native direct bytes cannot be captured") from error
    return _validate_source_native_snapshot(
        SourceNativeSnapshot(SOURCE_NATIVE_SNAPSHOT_SCHEMA, tuple(entries))
    )


def encode_source_native_snapshot(snapshot: SourceNativeSnapshot) -> bytes:
    return _canonical_json_bytes(_source_native_snapshot_payload(snapshot))


def write_source_native_snapshot(path: str | Path, snapshot: SourceNativeSnapshot) -> None:
    _atomic_create(Path(path), encode_source_native_snapshot(snapshot))


def load_source_native_snapshot(path: str | Path) -> SourceNativeSnapshot:
    try:
        encoded = Path(path).read_bytes()
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("source/native snapshot cannot be loaded") from error
    snapshot = _decode_source_native_snapshot(value)
    if encoded != encode_source_native_snapshot(snapshot):
        raise ArtifactContractError("source/native snapshot is not canonical direct JSON")
    return snapshot


def compare_source_native_snapshot(
    expected: SourceNativeSnapshot, live: SourceNativeSnapshot | None = None,
) -> None:
    expected_bytes = encode_source_native_snapshot(expected)
    observed_bytes = encode_source_native_snapshot(
        capture_source_native_snapshot() if live is None else live
    )
    if observed_bytes != expected_bytes:
        raise ArtifactContractError("source/native direct bytes or ordered paths differ")


def make_checkpoint(
    model: nn.Module, optimizer: ExactAdamW, *, completed_updates: int, rng_master: bytes
) -> dict[str, object]:
    _validate_foundation_binding(model, optimizer)
    if (
        isinstance(completed_updates, bool)
        or not isinstance(completed_updates, int)
        or not 0 <= completed_updates <= 160
    ):
        raise ArtifactContractError("checkpoint update frontier differs")
    if optimizer.step_index != completed_updates * 12:
        raise ArtifactContractError("checkpoint optimizer frontier differs")
    state = optimizer.snapshot()
    value: dict[str, object] = {
        "schema": CHECKPOINT_SCHEMA,
        "completed_updates": completed_updates,
        "model_state": {name: value.detach().clone() for name, value in model.state_dict().items()},
        "optimizer": {
            "step": state.step,
            "names": state.names,
            "first": state.first,
            "second": state.second,
        },
    }
    if not isinstance(rng_master, bytes) or len(rng_master) != 32:
        raise ArtifactContractError("production checkpoint RNG master differs")
    if completed_updates != CHECKPOINT_UPDATE:
        raise ArtifactContractError("production checkpoint frontier must be update 160")
    value["rng_master"] = rng_master
    return value


def _validate_checkpoint(value: object, model: nn.Module, optimizer: ExactAdamW) -> dict[str, object]:
    _validate_foundation_binding(model, optimizer)
    required_fields = {"schema", "completed_updates", "model_state", "optimizer", "rng_master"}
    if not isinstance(value, dict) or set(value) != required_fields:
        raise ArtifactContractError("checkpoint fields differ or legacy schema was supplied")
    if value["schema"] != CHECKPOINT_SCHEMA:
        raise ArtifactContractError("checkpoint schema differs or is legacy")
    completed = value["completed_updates"]
    if isinstance(completed, bool) or not isinstance(completed, int) or not 0 <= completed <= 160:
        raise ArtifactContractError("checkpoint completed-update frontier differs")
    expected = model.state_dict()
    observed = value["model_state"]
    if not isinstance(observed, dict) or set(observed) != set(expected):
        raise ArtifactContractError("checkpoint model tensor names differ")
    for name, reference in expected.items():
        item = observed[name]
        if not isinstance(item, Tensor) or item.dtype != reference.dtype or item.shape != reference.shape or not bool(torch.isfinite(item).all()):
            raise ArtifactContractError(f"checkpoint model tensor differs: {name}")
    model_tensors = tuple(observed[name] for name in expected)
    if len({id(value) for value in model_tensors}) != len(model_tensors):
        raise ArtifactContractError("checkpoint model tensors must be direct nonaliased state")
    row = value["optimizer"]
    required = {"step", "names", "first", "second"}
    if not isinstance(row, dict) or set(row) != required:
        raise ArtifactContractError("checkpoint optimizer structure differs")
    raw_step = row["step"]
    if isinstance(raw_step, bool) or not isinstance(raw_step, int):
        raise ArtifactContractError("checkpoint optimizer step must be an integer")
    try:
        snapshot = OptimizerSnapshot(raw_step, tuple(row["names"]), tuple(row["first"]), tuple(row["second"]))
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("checkpoint optimizer structure differs") from error
    if snapshot.step != completed * 12:
        raise ArtifactContractError("checkpoint optimizer/update frontiers differ")
    try:
        optimizer.validate_snapshot(snapshot)
    except TrainingContractError as error:
        raise ArtifactContractError("checkpoint optimizer state differs") from error
    master = value["rng_master"]
    if not isinstance(master, bytes) or len(master) != 32 or completed != CHECKPOINT_UPDATE:
        raise ArtifactContractError("production checkpoint master/frontier differs")
    return value


def write_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: ExactAdamW,
    *,
    completed_updates: int,
    rng_master: bytes,
) -> None:
    stream = BytesIO()
    torch.save(make_checkpoint(model, optimizer, completed_updates=completed_updates, rng_master=rng_master), stream)
    _atomic_create(Path(path), stream.getvalue())


def load_checkpoint(path: str | Path, model: nn.Module, optimizer: ExactAdamW) -> dict[str, object]:
    try:
        value = torch.load(BytesIO(Path(path).read_bytes()), map_location="cpu", weights_only=True)
    except (OSError, RuntimeError, EOFError, pickle.UnpicklingError) as error:
        raise ArtifactContractError("checkpoint cannot be loaded") from error
    return _validate_checkpoint(value, model, optimizer)


@torch.no_grad()
def restore_checkpoint(value: Mapping[str, object], model: nn.Module, optimizer: ExactAdamW) -> None:
    row = _validate_checkpoint(dict(value), model, optimizer)
    state = row["optimizer"]
    assert isinstance(state, dict)
    incoming_optimizer = OptimizerSnapshot(
        int(state["step"]), tuple(state["names"]), tuple(state["first"]), tuple(state["second"])
    )
    before_model = {name: value.detach().clone() for name, value in model.state_dict().items()}
    before_optimizer = optimizer.snapshot()
    try:
        model.load_state_dict(row["model_state"], strict=True)  # type: ignore[arg-type]
        optimizer.restore(incoming_optimizer)
        if not direct_resume_equal(row, model, optimizer):
            raise ArtifactContractError("direct checkpoint resume equality failed")
    except Exception:
        model.load_state_dict(before_model, strict=True)
        optimizer.restore(before_optimizer)
        raise


def direct_resume_equal(value: Mapping[str, object], model: nn.Module, optimizer: ExactAdamW) -> bool:
    observed = value.get("model_state")
    state = value.get("optimizer")
    if not isinstance(observed, Mapping) or not isinstance(state, Mapping):
        return False
    if set(observed) != set(model.state_dict()):
        return False
    if any(not torch.equal(observed[name], current) for name, current in model.state_dict().items()):
        return False
    current = optimizer.snapshot()
    return (
        state.get("step") == current.step
        and tuple(state.get("names", ())) == current.names
        and len(tuple(state.get("first", ()))) == len(current.first)
        and len(tuple(state.get("second", ()))) == len(current.second)
        and all(torch.equal(left, right) for left, right in zip(tuple(state.get("first", ())), current.first))
        and all(torch.equal(left, right) for left, right in zip(tuple(state.get("second", ())), current.second))
    )


def write_rng_master(path: str | Path, master: bytes) -> None:
    if not isinstance(master, bytes) or len(master) != 32:
        raise ArtifactContractError("run RNG master must contain exactly 32 bytes")
    _atomic_create(Path(path), master)


def load_rng_master(path: str | Path) -> bytes:
    try:
        value = Path(path).read_bytes()
    except OSError as error:
        raise ArtifactContractError("run RNG master cannot be loaded") from error
    if len(value) != 32:
        raise ArtifactContractError("persisted run RNG master differs")
    return value


@dataclass(frozen=True, slots=True)
class ResumeWitness:
    schema: str
    checkpoint_update: int
    optimizer_step: int
    model_tensors_equal: bool
    optimizer_tensors_equal: bool
    counters_equal: bool
    addressed_inputs_equal: bool
    continuation_stage: str
    probe_initial_state: tuple[float, float, float]
    probe_disturbance: tuple[float, float, float]


def observe_resume_equality(
    checkpoint: Mapping[str, object],
    uninterrupted_model: FoundationActorCritic,
    uninterrupted_optimizer: ExactAdamW,
    restored_model: FoundationActorCritic,
    restored_optimizer: ExactAdamW,
    *,
    persisted_master: bytes,
) -> ResumeWitness:
    """Directly compare the final-training resume state and competence RNG inputs."""

    from .foundation import competence_disturbance, competence_initial_draws, competence_inventory

    if (
        not isinstance(persisted_master, bytes)
        or len(persisted_master) != 32
        or checkpoint.get("schema") != CHECKPOINT_SCHEMA
        or checkpoint.get("completed_updates") != CHECKPOINT_UPDATE
        or checkpoint.get("rng_master") != persisted_master
        or not direct_resume_equal(checkpoint, restored_model, restored_optimizer)
    ):
        raise ArtifactContractError("checkpoint and persisted RNG masters differ")
    model_equal = all(
        torch.equal(left, right)
        for left, right in zip(uninterrupted_model.state_dict().values(), restored_model.state_dict().values())
    )
    left_state = uninterrupted_optimizer.snapshot()
    right_state = restored_optimizer.snapshot()
    optimizer_equal = (
        left_state.names == right_state.names
        and all(torch.equal(left, right) for left, right in zip(left_state.first, right_state.first))
        and all(torch.equal(left, right) for left, right in zip(left_state.second, right_state.second))
    )
    counters_equal = left_state.step == right_state.step == CHECKPOINT_UPDATE * 12
    mission = competence_inventory()[0]
    left_rng = AddressRNG(persisted_master)
    right_rng = AddressRNG(bytes(persisted_master))
    left_probe = (
        competence_initial_draws(left_rng, mission),
        tuple(competence_disturbance(left_rng, mission, tick=0, component=name) for name in ("eta_v", "eta_y", "eta_omega")),
    )
    right_probe = (
        competence_initial_draws(right_rng, mission),
        tuple(competence_disturbance(right_rng, mission, tick=0, component=name) for name in ("eta_v", "eta_y", "eta_omega")),
    )
    addressed_equal = left_probe == right_probe
    if not (model_equal and optimizer_equal and counters_equal and addressed_equal):
        raise ArtifactContractError("nonzero checkpoint/resume continuation equality failed")
    return ResumeWitness(
        RESUME_WITNESS_SCHEMA, CHECKPOINT_UPDATE, left_state.step, model_equal, optimizer_equal,
        counters_equal, addressed_equal, "COMPETENCE", left_probe[0], left_probe[1],
    )


def write_resume_witness(path: str | Path, witness: ResumeWitness) -> None:
    if not isinstance(witness, ResumeWitness) or witness.schema != RESUME_WITNESS_SCHEMA:
        raise ArtifactContractError("resume witness differs")
    if not all((witness.model_tensors_equal, witness.optimizer_tensors_equal, witness.counters_equal, witness.addressed_inputs_equal)):
        raise ArtifactContractError("resume witness is not a direct equality observation")
    _atomic_json(Path(path), asdict(witness))


def load_resume_witness(path: str | Path) -> ResumeWitness:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("resume witness cannot be loaded") from error
    if not isinstance(value, dict) or set(value) != {field.name for field in fields(ResumeWitness)}:
        raise ArtifactContractError("resume witness fields differ")
    try:
        witness = ResumeWitness(
            str(value["schema"]), int(value["checkpoint_update"]), int(value["optimizer_step"]),
            value["model_tensors_equal"] is True, value["optimizer_tensors_equal"] is True,
            value["counters_equal"] is True, value["addressed_inputs_equal"] is True,
            str(value["continuation_stage"]), tuple(float(item) for item in value["probe_initial_state"]),
            tuple(float(item) for item in value["probe_disturbance"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ArtifactContractError("resume witness typed payload differs") from error
    if value != _json_shape(asdict(witness)) or witness.schema != RESUME_WITNESS_SCHEMA or not all((
        witness.model_tensors_equal, witness.optimizer_tensors_equal, witness.counters_equal,
        witness.addressed_inputs_equal,
    )):
        raise ArtifactContractError("resume witness differs")
    return witness


@dataclass(frozen=True, slots=True)
class RunRuntime:
    python: str
    torch: str
    device: str = "cpu"
    torch_threads: int = 1
    torch_interop_threads: int = 1
    deterministic_algorithms: bool = True
    native_batch_widths: tuple[tuple[str, int], ...] = (
        ("training", 12), ("competence", 120), ("panel_full", 144), ("panel_final", 60),
    )


@dataclass(frozen=True, slots=True)
class RunRecord:
    schema: str
    phase: str
    checkpoint_update: int
    foundation_updates: int
    episodes_per_update: int
    competence_missions: int
    panel_width: int
    actions: tuple[int, int, int]
    resources: tuple[tuple[str, int], ...]
    runtime: RunRuntime


def build_run_record() -> RunRecord:
    return RunRecord(
        RUN_RECORD_SCHEMA, "FOUNDATION_AND_2X3", CHECKPOINT_UPDATE, FOUNDATION_UPDATES,
        12, 120, PANEL_WIDTH, (0, 10, 12), tuple(RESOURCE_MAXIMA.items()),
        RunRuntime(
            platform.python_version(), str(torch.__version__), "cpu", torch.get_num_threads(),
            torch.get_num_interop_threads(), torch.are_deterministic_algorithms_enabled(),
        ),
    )


def _frozen_run_record() -> RunRecord:
    """Return the persisted contract without consulting mutable live Torch controls."""

    return RunRecord(
        RUN_RECORD_SCHEMA, "FOUNDATION_AND_2X3", CHECKPOINT_UPDATE, FOUNDATION_UPDATES,
        12, 120, PANEL_WIDTH, (0, 10, 12), tuple(RESOURCE_MAXIMA.items()),
        RunRuntime(
            platform.python_version(), str(torch.__version__), "cpu", 1, 1, True,
        ),
    )


def write_run_record(path: str | Path, value: RunRecord) -> None:
    if not isinstance(value, RunRecord) or not isinstance(value.runtime, RunRuntime):
        raise ArtifactContractError("run record must use the exact typed schema")
    if any(
        not isinstance(version, str)
        or not version.strip()
        or any(ord(character) < 32 for character in version)
        for version in (value.runtime.python, value.runtime.torch)
    ):
        raise ArtifactContractError("runtime version strings must be nonempty printable text")
    if (
        value.runtime.device != "cpu"
        or value.runtime.torch_threads != 1
        or value.runtime.torch_interop_threads != 1
        or value.runtime.deterministic_algorithms is not True
    ):
        raise ArtifactContractError("run record numerical runtime controls differ")
    expected = build_run_record()
    if value != expected:
        raise ArtifactContractError("run record fields/runtime differ from the frozen execution contract")
    payload = asdict(value)
    payload["resources"] = dict(value.resources)
    payload["runtime"]["native_batch_widths"] = dict(value.runtime.native_batch_widths)
    _atomic_json(Path(path), payload)


def load_run_record(path: str | Path) -> RunRecord:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("run record cannot be loaded") from error
    # Completed-result validation and the first half of technical resume run in
    # a fresh process whose Torch defaults need not yet be 1/1/deterministic.
    # Validate the persisted frozen record here; live controls are checked only
    # after the runner explicitly configures them.
    expected = _frozen_run_record()
    payload = json.loads(json.dumps(asdict(expected), allow_nan=False))
    payload["resources"] = dict(expected.resources)
    payload["runtime"]["native_batch_widths"] = dict(expected.runtime.native_batch_widths)
    # Compare the persisted JSON shape rather than Python's tuple-rich typed
    # shape.  ``json.dumps`` serializes tuple fields such as ``actions`` as
    # arrays, so a direct comparison would reject the record written by
    # ``write_run_record`` itself on every technical resume.
    payload = _json_shape(payload)
    if value != payload:
        raise ArtifactContractError("run record fields/runtime differ from the frozen execution contract")
    return expected


def validate_live_run_record_runtime(path: str | Path) -> RunRecord:
    """Require current Torch controls to equal the already validated record."""

    persisted = load_run_record(path)
    if build_run_record() != persisted:
        raise ArtifactContractError("live numerical runtime differs from the persisted run record")
    return persisted


def _competence_evidence(
    gate: FoundationGate, records: Sequence[CompetenceRecord]
) -> tuple[tuple[CompetenceRecord, ...], dict[str, object]]:
    rows = tuple(records)
    try:
        recomputed = analyze_competence(rows)
    except ValueError as error:
        raise ArtifactContractError("competence evidence is invalid") from error
    if not recomputed.complete or recomputed != gate:
        raise ArtifactContractError("foundation gate differs from 120 raw competence records")
    _validate_complete_gate(gate)
    counts: dict[str, object] = {
        "missions": len(rows),
        "safe_by_graph": {
            graph: sum(row.safe_dock for row in rows if row.graph == graph) for graph in GRAPHS
        },
        "pooled_safe": sum(row.safe_dock for row in rows),
        "failures": {
            label: sum(label in row.failures for row in rows) for label in FAILURE_LABELS
        },
    }
    return rows, counts


def write_foundation_gate(
    path: str | Path, gate: FoundationGate, records: Sequence[CompetenceRecord]
) -> None:
    if not gate.complete:
        raise ArtifactContractError("incomplete foundation gate cannot be published")
    rows, counts = _competence_evidence(gate, records)
    _atomic_json(Path(path), {
        "schema": FOUNDATION_GATE_SCHEMA,
        "gate": asdict(gate),
        "competence_records": [asdict(row) for row in rows],
        "counts": counts,
    })


def _decode_competence_records(value: object) -> tuple[CompetenceRecord, ...]:
    if not isinstance(value, list):
        raise ArtifactContractError("competence record inventory differs")
    expected_fields = {field.name for field in fields(CompetenceRecord)}
    rows: list[CompetenceRecord] = []
    try:
        for item in value:
            if not isinstance(item, dict) or set(item) != expected_fields:
                raise ArtifactContractError("competence record fields differ")
            if (
                isinstance(item["mission"], bool)
                or not isinstance(item["mission"], int)
                or not isinstance(item["graph"], str)
                or not isinstance(item["complete"], bool)
                or not isinstance(item["safe_dock"], bool)
                or not isinstance(item["failures"], list)
                or any(not isinstance(label, str) for label in item["failures"])
            ):
                raise ArtifactContractError("competence record typed payload differs")
            rows.append(CompetenceRecord(
                item["mission"], item["graph"], item["complete"], item["safe_dock"],
                tuple(item["failures"]),
            ))
    except KeyError as error:
        raise ArtifactContractError("competence record typed payload differs") from error
    if value != _json_shape([asdict(row) for row in rows]):
        raise ArtifactContractError("competence record direct evidence differs")
    return tuple(rows)


def _decode_foundation_gate(value: object) -> FoundationGate:
    expected_fields = {field.name for field in fields(FoundationGate)}
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ArtifactContractError("foundation gate fields differ")
    if not isinstance(value["complete"], bool) or not isinstance(value["passed"], bool):
        raise ArtifactContractError("foundation gate flags differ")
    try:
        gate = FoundationGate(
            value["complete"], value["passed"],
            tuple((str(name), float(bound)) for name, bound in value["graph_lower_bounds"]),
            float(value["pooled_lower_bound"]),
            tuple((str(name), float(bound)) for name, bound in value["failure_upper_bounds"]),
        )
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("foundation gate typed payload differs") from error
    if value != _json_shape(asdict(gate)):
        raise ArtifactContractError("foundation gate direct payload differs")
    _validate_complete_gate(gate)
    return gate


def load_foundation_gate(
    path: str | Path,
) -> tuple[FoundationGate, tuple[CompetenceRecord, ...]]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("foundation gate cannot be loaded") from error
    if not isinstance(value, dict) or set(value) != {
        "schema", "gate", "competence_records", "counts",
    } or value["schema"] != FOUNDATION_GATE_SCHEMA:
        raise ArtifactContractError("foundation gate fields/schema differ")
    raw_gate = value["gate"]
    raw_records = value["competence_records"]
    if not isinstance(raw_gate, dict) or not isinstance(raw_records, list):
        raise ArtifactContractError("foundation gate typed payload differs")
    gate = _decode_foundation_gate(raw_gate)
    records = _decode_competence_records(raw_records)
    evidence_rows, counts = _competence_evidence(gate, records)
    if list(raw_records) != _json_shape([asdict(row) for row in evidence_rows]) or value["counts"] != counts:
        raise ArtifactContractError("foundation gate raw evidence differs")
    return gate, evidence_rows


@dataclass(frozen=True, slots=True)
class PanelFrontier:
    schema: str
    completed_slices: int
    completed_cells: int
    next_slice: int


def _slice_geometry(slice_index: int) -> tuple[int, int, int]:
    full_tapes = int(getattr(_contracts, "PANEL_FULL_SLICE_TAPES", 24))
    slice_count = int(getattr(_contracts, "PANEL_SLICE_COUNT", (TAPE_COUNT + full_tapes - 1) // full_tapes))
    if isinstance(slice_index, bool) or not isinstance(slice_index, int) or not 0 <= slice_index < slice_count:
        raise ArtifactContractError("panel slice index differs")
    start = slice_index * full_tapes
    count = min(full_tapes, TAPE_COUNT - start)
    return start, count, count * len(GRAPHS) * len(CANDIDATE_ACTIONS)


def _validate_slice_cells(slice_index: int, cells: Sequence[PanelCell]) -> tuple[PanelCell, ...]:
    start, count, width = _slice_geometry(slice_index)
    rows = tuple(cells)
    expected = tuple(
        (tape, graph, action, CANDIDATE_ACTIONS[action])
        for tape in range(start, start + count)
        for graph in GRAPHS
        for action in CANDIDATE_ACTIONS
    )
    observed = tuple((row.tape, row.graph, row.action_name, row.action_index) for row in rows)
    if len(rows) != width or observed != expected or any(not row.terminal for row in rows):
        raise ArtifactContractError("panel slice is not the exact complete ordered inventory")
    try:
        from .panel import build_panel_slices, validate_panel_slice_cells
        validate_panel_slice_cells(rows, build_panel_slices()[slice_index])
    except (IndexError, TypeError, ValueError, RuntimeError) as error:
        raise ArtifactContractError("panel slice failed direct panel-contract validation") from error
    return rows


def write_panel_slice(path: str | Path, *, slice_index: int, cells: Sequence[PanelCell]) -> None:
    rows = _validate_slice_cells(slice_index, cells)
    start, count, _ = _slice_geometry(slice_index)
    _atomic_json(Path(path), {
        "schema": PANEL_SLICE_SCHEMA,
        "slice_index": slice_index,
        "start_tape": start,
        "tape_count": count,
        "cells": [asdict(row) for row in rows],
    })


def load_panel_slice(path: str | Path, *, slice_index: int) -> tuple[PanelCell, ...]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("panel slice cannot be loaded") from error
    start, count, _ = _slice_geometry(slice_index)
    if not isinstance(value, dict) or set(value) != {
        "schema", "slice_index", "start_tape", "tape_count", "cells",
    } or (
        value["schema"] != PANEL_SLICE_SCHEMA
        or value["slice_index"] != slice_index
        or value["start_tape"] != start
        or value["tape_count"] != count
        or not isinstance(value["cells"], list)
    ):
        raise ArtifactContractError("panel slice fields/schema differ")
    try:
        rows = tuple(
            PanelCell(
                int(row["tape"]), str(row["graph"]), str(row["action_name"]),
                int(row["action_index"]), row["terminal"] is True, row["safe_dock"] is True,
                None if row["dock_tick"] is None else int(row["dock_tick"]),
                tuple(str(item) for item in row.get("failures", ())),
            )
            for row in value["cells"]
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ArtifactContractError("panel slice typed payload differs") from error
    rows = _validate_slice_cells(slice_index, rows)
    if value["cells"] != _json_shape([asdict(row) for row in rows]):
        raise ArtifactContractError("panel slice raw cells differ")
    return rows


def build_panel_frontier(completed_slices: int) -> PanelFrontier:
    slice_count = int(getattr(_contracts, "PANEL_SLICE_COUNT", 24))
    if isinstance(completed_slices, bool) or not isinstance(completed_slices, int) or not 0 <= completed_slices <= slice_count:
        raise ArtifactContractError("panel frontier slice count differs")
    cells = sum(_slice_geometry(index)[2] for index in range(completed_slices))
    return PanelFrontier(PANEL_FRONTIER_SCHEMA, completed_slices, cells, completed_slices)


def write_panel_frontier(path: str | Path, frontier: PanelFrontier) -> None:
    if not isinstance(frontier, PanelFrontier) or frontier != build_panel_frontier(frontier.completed_slices):
        raise ArtifactContractError("typed panel frontier differs")
    _atomic_replace_json(Path(path), asdict(frontier))


def load_panel_frontier(path: str | Path) -> PanelFrontier:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("panel frontier cannot be loaded") from error
    if not isinstance(value, dict) or set(value) != {
        "schema", "completed_slices", "completed_cells", "next_slice",
    }:
        raise ArtifactContractError("panel frontier fields differ")
    try:
        frontier = PanelFrontier(
            str(value["schema"]), int(value["completed_slices"]),
            int(value["completed_cells"]), int(value["next_slice"]),
        )
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("panel frontier typed payload differs") from error
    if value != asdict(frontier) or frontier != build_panel_frontier(frontier.completed_slices):
        raise ArtifactContractError("typed panel frontier differs")
    return frontier


def load_contiguous_panel_slices(root: str | Path) -> tuple[tuple[PanelCell, ...], ...]:
    directory = Path(root)
    slice_count = int(getattr(_contracts, "PANEL_SLICE_COUNT", 24))
    observed = tuple(sorted(directory.glob("panel-slice-*.json")))
    completed: list[tuple[PanelCell, ...]] = []
    for index in range(slice_count):
        path = directory / f"panel-slice-{index:03d}.json"
        if not path.exists():
            if any(item.name > path.name for item in observed):
                raise ArtifactContractError("panel slice inventory is noncontiguous")
            break
        completed.append(load_panel_slice(path, slice_index=index))
    expected_names = {f"panel-slice-{index:03d}.json" for index in range(len(completed))}
    if {path.name for path in observed} != expected_names:
        raise ArtifactContractError("panel slice file inventory differs")
    return tuple(completed)


def _write_complete_panel_fixture(path: str | Path, cells: Sequence[PanelCell], analysis: PanelAnalysis) -> None:
    """Historical fixture writer; production passing publication uses one final bundle."""
    rows = tuple(cells)
    if len(rows) != PANEL_WIDTH or any(not row.terminal for row in rows) or len(analysis.tape_contrasts) != TAPE_COUNT:
        raise ArtifactContractError("partial panel cannot be published")
    try:
        recomputed = analyze_complete_panel(rows)
    except ValueError as error:
        raise ArtifactContractError("complete panel semantics are invalid") from error
    if recomputed != analysis:
        raise ArtifactContractError("panel analysis differs from direct recomputation")
    _atomic_json(Path(path), {
        "schema": PANEL_SCHEMA,
        "cells": [asdict(row) for row in rows],
        "analysis": asdict(analysis),
    })


def _complete_final_bundle(
    *, competence_records: Sequence[CompetenceRecord], panel_cells: Sequence[PanelCell],
    panel_analysis: PanelAnalysis | None = None,
) -> tuple[TerminalFact, dict[str, object]]:
    rows = tuple(competence_records)
    gate = analyze_competence(rows)
    evidence_rows, counts = _competence_evidence(gate, rows)
    if gate.passed is not True:
        raise ArtifactContractError("atomic final bundle requires a passing raw competence gate")
    cells = tuple(panel_cells)
    if len(cells) != PANEL_WIDTH or any(not cell.terminal for cell in cells):
        raise ArtifactContractError(f"atomic final bundle requires {PANEL_WIDTH} terminal panel cells")
    try:
        recomputed = analyze_complete_panel(cells)
    except ValueError as error:
        raise ArtifactContractError("atomic final bundle panel semantics are invalid") from error
    if panel_analysis is not None and panel_analysis != recomputed:
        raise ArtifactContractError("atomic final bundle analysis differs from raw-cell recomputation")
    panel_analysis = recomputed
    gap_integer_sums = tuple(
        (gap.name, gap.raw_utility_numerator_sum) for gap in panel_analysis.gaps
    )
    component_p_values = tuple((gap.name, gap.p_value_upper) for gap in panel_analysis.gaps)
    fact = TerminalFact(
        TERMINAL_FACT_SCHEMA, panel_analysis.disposition, gate, True,
        gap_integer_sums=gap_integer_sums,
        component_p_values=component_p_values,
        joint_p_value=panel_analysis.p_iut,
        l_theta=panel_analysis.l_theta,
    )
    payload: dict[str, object] = {
        "schema": FINAL_BUNDLE_SCHEMA,
        "foundation_gate": asdict(gate),
        "competence_records": [asdict(row) for row in evidence_rows],
        "competence_counts": counts,
        "panel_cells": [asdict(cell) for cell in cells],
        "panel_analysis": asdict(panel_analysis),
        "terminal_fact": asdict(fact),
    }
    return fact, payload


def _validate_result_bindings(
    *,
    resolved_result_root: str,
    rng_master: bytes,
    run_record_bytes: bytes,
    source_native_snapshot: SourceNativeSnapshot,
) -> tuple[str, bytes, bytes, SourceNativeSnapshot]:
    if (
        not isinstance(resolved_result_root, str)
        or not resolved_result_root
        or str(Path(resolved_result_root).resolve()) != resolved_result_root
    ):
        raise ArtifactContractError("final bundle requires the canonical resolved result root string")
    if not isinstance(rng_master, bytes) or len(rng_master) != 32:
        raise ArtifactContractError("final bundle RNG master must be the raw 32 bytes")
    if not isinstance(run_record_bytes, bytes) or not run_record_bytes:
        raise ArtifactContractError("final bundle run record must be nonempty exact bytes")
    return (
        resolved_result_root, rng_master, run_record_bytes,
        _validate_source_native_snapshot(source_native_snapshot),
    )


def _bound_final_payload(
    core: Mapping[str, object],
    *,
    resolved_result_root: str,
    rng_master: bytes,
    run_record_bytes: bytes,
    source_native_snapshot: SourceNativeSnapshot,
) -> dict[str, object]:
    root, master, record, snapshot = _validate_result_bindings(
        resolved_result_root=resolved_result_root,
        rng_master=rng_master,
        run_record_bytes=run_record_bytes,
        source_native_snapshot=source_native_snapshot,
    )
    value = dict(core)
    value.update({
        "resolved_result_root": root,
        "rng_master_b64": base64.b64encode(master).decode("ascii"),
        "run_record_b64": base64.b64encode(record).decode("ascii"),
        "source_native_snapshot": _source_native_snapshot_payload(snapshot),
    })
    return value


def prepare_final_bundle(
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell],
    panel_analysis: PanelAnalysis,
    resolved_result_root: str,
    rng_master: bytes,
    run_record_bytes: bytes,
    source_native_snapshot: SourceNativeSnapshot,
) -> PreparedFinalBundle:
    """Recompute all evidence and pre-encode the exact bytes before resource admission."""

    fact, core = _complete_final_bundle(
        competence_records=competence_records,
        panel_cells=panel_cells,
        panel_analysis=panel_analysis,
    )
    payload = _bound_final_payload(
        core,
        resolved_result_root=resolved_result_root,
        rng_master=rng_master,
        run_record_bytes=run_record_bytes,
        source_native_snapshot=source_native_snapshot,
    )
    return PreparedFinalBundle(fact, _canonical_json_bytes(payload))


def final_bundle_encoded_size(prepared: PreparedFinalBundle) -> int:
    if not isinstance(prepared, PreparedFinalBundle):
        raise ArtifactContractError("final bundle was not prepared by the typed pre-encoding seam")
    return prepared.encoded_size


def _decode_panel_cells(value: object) -> tuple[PanelCell, ...]:
    if not isinstance(value, list):
        raise ArtifactContractError("final bundle panel inventory differs")
    expected_fields = {field.name for field in fields(PanelCell)}
    rows: list[PanelCell] = []
    try:
        for item in value:
            if not isinstance(item, dict) or set(item) != expected_fields:
                raise ArtifactContractError("final bundle panel cell fields differ")
            if (
                isinstance(item["tape"], bool)
                or not isinstance(item["tape"], int)
                or not isinstance(item["graph"], str)
                or not isinstance(item["action_name"], str)
                or isinstance(item["action_index"], bool)
                or not isinstance(item["action_index"], int)
                or not isinstance(item["terminal"], bool)
                or not isinstance(item["safe_dock"], bool)
                or (item["dock_tick"] is not None and (
                    isinstance(item["dock_tick"], bool) or not isinstance(item["dock_tick"], int)
                ))
                or not isinstance(item["failures"], list)
                or any(not isinstance(label, str) for label in item["failures"])
            ):
                raise ArtifactContractError("final bundle panel cell typed payload differs")
            rows.append(PanelCell(
                item["tape"], item["graph"], item["action_name"], item["action_index"],
                item["terminal"], item["safe_dock"], item["dock_tick"], tuple(item["failures"]),
            ))
    except KeyError as error:
        raise ArtifactContractError("final bundle panel cell typed payload differs") from error
    if value != _json_shape([asdict(row) for row in rows]):
        raise ArtifactContractError("final bundle panel cells differ")
    return tuple(rows)


def _decode_direct_base64(value: object, *, label: str) -> bytes:
    if not isinstance(value, str):
        raise ArtifactContractError(f"final bundle {label} direct bytes differ")
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise ArtifactContractError(f"final bundle {label} direct bytes cannot be decoded") from error
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ArtifactContractError(f"final bundle {label} base64 is not canonical")
    return decoded


def _decode_terminal_fact_payload(value: object) -> TerminalFact:
    if not isinstance(value, dict) or set(value) != {field.name for field in fields(TerminalFact)}:
        raise ArtifactContractError("terminal fact fields differ")
    if (
        not isinstance(value["schema"], str)
        or not isinstance(value["disposition"], str)
        or not isinstance(value["panel_complete"], bool)
    ):
        raise ArtifactContractError("terminal fact typed payload differs")
    try:
        integer_sums = tuple((str(name), int(number)) for name, number in value["gap_integer_sums"])
        p_values = tuple((str(name), float(number)) for name, number in value["component_p_values"])
        if any(isinstance(number, bool) for _, number in value["gap_integer_sums"]):
            raise ArtifactContractError("terminal fact integer sums differ")
        fact = TerminalFact(
            value["schema"], value["disposition"],
            _decode_foundation_gate(value["foundation_gate"]), value["panel_complete"],
            integer_sums, p_values,
            None if value["joint_p_value"] is None else float(value["joint_p_value"]),
            None if value["l_theta"] is None else float(value["l_theta"]),
        )
    except (TypeError, ValueError) as error:
        raise ArtifactContractError("terminal fact typed payload differs") from error
    if value != _json_shape(asdict(fact)):
        raise ArtifactContractError("terminal fact direct payload differs")
    return fact


def _validate_prepared_final_bundle(prepared: PreparedFinalBundle) -> dict[str, object]:
    if not isinstance(prepared, PreparedFinalBundle) or not isinstance(prepared.encoded, bytes):
        raise ArtifactContractError("final bundle was not prepared by the typed pre-encoding seam")
    try:
        value = json.loads(prepared.encoded.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("prepared final bundle cannot be decoded") from error
    expected_fields = {
        "schema", "foundation_gate", "competence_records", "competence_counts",
        "panel_cells", "panel_analysis", "terminal_fact", "resolved_result_root",
        "rng_master_b64", "run_record_b64", "source_native_snapshot",
    }
    if not isinstance(value, dict) or set(value) != expected_fields or value.get("schema") != FINAL_BUNDLE_SCHEMA:
        raise ArtifactContractError("prepared final bundle fields/schema differ")
    records = _decode_competence_records(value["competence_records"])
    cells = _decode_panel_cells(value["panel_cells"])
    recomputed_analysis = analyze_complete_panel(cells)
    master = _decode_direct_base64(value["rng_master_b64"], label="RNG master")
    run_record = _decode_direct_base64(value["run_record_b64"], label="run record")
    snapshot = _decode_source_native_snapshot(value["source_native_snapshot"])
    recomputed = prepare_final_bundle(
        competence_records=records,
        panel_cells=cells,
        panel_analysis=recomputed_analysis,
        resolved_result_root=value["resolved_result_root"],
        rng_master=master,
        run_record_bytes=run_record,
        source_native_snapshot=snapshot,
    )
    if prepared.encoded != recomputed.encoded or prepared.fact != recomputed.fact:
        raise ArtifactContractError("prepared final bundle differs from full direct recomputation")
    return value


def _test_only_write_final_bundle(
    path: str | Path,
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell],
    resolved_result_root: str,
    rng_master: bytes,
    run_record_bytes: bytes,
    source_native_snapshot: SourceNativeSnapshot,
) -> TerminalFact:
    """TEST_ONLY atomic fixture; production calls the distinct guarded publisher."""

    try:
        analysis = analyze_complete_panel(tuple(panel_cells))
    except ValueError as error:
        message = str(error)
        if "terminal cells" not in message:
            message = "atomic final bundle panel semantics are invalid"
        raise ArtifactContractError(message) from error
    prepared = prepare_final_bundle(
        competence_records=competence_records,
        panel_cells=panel_cells,
        panel_analysis=analysis,
        resolved_result_root=resolved_result_root,
        rng_master=rng_master,
        run_record_bytes=run_record_bytes,
        source_native_snapshot=source_native_snapshot,
    )
    return write_prepared_final_bundle(path, prepared)


def write_prepared_final_bundle(path: str | Path, prepared: PreparedFinalBundle) -> TerminalFact:
    """Revalidate the prepared bytes immediately before their sole create-only publication."""

    _validate_prepared_final_bundle(prepared)
    _atomic_create(Path(path), prepared.encoded)
    return prepared.fact


def write_final_bundle(
    path: str | Path,
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell],
    panel_analysis: PanelAnalysis,
    resolved_result_root: str,
    rng_master: bytes,
    run_record_bytes: bytes,
    source_native_snapshot: SourceNativeSnapshot,
) -> TerminalFact:
    """Compatibility convenience around the V5 prepare/resource/publish seam."""

    prepared = prepare_final_bundle(
        competence_records=competence_records,
        panel_cells=panel_cells,
        panel_analysis=panel_analysis,
        resolved_result_root=resolved_result_root,
        rng_master=rng_master,
        run_record_bytes=run_record_bytes,
        source_native_snapshot=source_native_snapshot,
    )
    return write_prepared_final_bundle(path, prepared)


def load_final_bundle(
    path: str | Path,
    *,
    expected_result_root: str,
    expected_rng_master: bytes,
    expected_run_record_bytes: bytes,
    expected_source_native_snapshot: SourceNativeSnapshot,
) -> TerminalFact:
    """Validate a complete result by reconstructing raw records/cells and reanalyzing globally."""

    try:
        encoded = Path(path).read_bytes()
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("final bundle cannot be loaded") from error
    prepared = PreparedFinalBundle(
        _decode_terminal_fact_payload(value.get("terminal_fact")), encoded
    )
    _validate_prepared_final_bundle(prepared)
    records = _decode_competence_records(value["competence_records"])
    cells = _decode_panel_cells(value["panel_cells"])
    expected = prepare_final_bundle(
        competence_records=records,
        panel_cells=cells,
        panel_analysis=analyze_complete_panel(cells),
        resolved_result_root=expected_result_root,
        rng_master=expected_rng_master,
        run_record_bytes=expected_run_record_bytes,
        source_native_snapshot=expected_source_native_snapshot,
    )
    if encoded != expected.encoded:
        raise ArtifactContractError("final bundle root/master/record/snapshot binding differs")
    return expected.fact


def write_terminal_fact(
    path: str | Path,
    fact: TerminalFact,
    *,
    competence_records: Sequence[CompetenceRecord],
    panel_cells: Sequence[PanelCell] | None = None,
) -> None:
    if fact.schema != TERMINAL_FACT_SCHEMA or not fact.foundation_gate.complete:
        raise ArtifactContractError("terminal fact is incomplete or has a legacy schema")
    rows, counts = _competence_evidence(fact.foundation_gate, competence_records)
    if fact.foundation_gate.passed:
        raise ArtifactContractError("passing panel requires atomic final bundle")
    if (
        fact.panel_complete is not False
        or panel_cells is not None
        or getattr(fact, "gap_integer_sums", ())
        or getattr(fact, "component_p_values", ())
        or getattr(fact, "joint_p_value", None) is not None
        or getattr(fact, "l_theta", None) is not None
        or fact.disposition != Disposition.FOUNDATION_NONPASS.value
    ):
        raise ArtifactContractError("foundation nonpass terminal branch differs")
    value = asdict(fact)
    value["competence_records"] = [asdict(row) for row in rows]
    value["competence_counts"] = counts
    _atomic_json(Path(path), value)


def load_foundation_nonpass_terminal(
    path: str | Path,
) -> tuple[TerminalFact, tuple[CompetenceRecord, ...]]:
    """Recompute a typed terminal nonpass from its complete 120-record evidence."""

    try:
        encoded = Path(path).read_bytes()
        value = json.loads(encoded.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ArtifactContractError("foundation nonpass terminal fact cannot be loaded") from error
    expected_fields = {field.name for field in fields(TerminalFact)} | {
        "competence_records", "competence_counts",
    }
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ArtifactContractError("foundation nonpass terminal fact fields differ")
    raw_fact = {field.name: value[field.name] for field in fields(TerminalFact)}
    supplied = _decode_terminal_fact_payload(raw_fact)
    records = _decode_competence_records(value["competence_records"])
    gate = analyze_competence(records)
    evidence_rows, counts = _competence_evidence(gate, records)
    expected = TerminalFact(
        TERMINAL_FACT_SCHEMA, Disposition.FOUNDATION_NONPASS.value, gate, False,
    )
    expected_payload = asdict(expected)
    expected_payload["competence_records"] = [asdict(row) for row in evidence_rows]
    expected_payload["competence_counts"] = counts
    if (
        gate.passed is not False
        or supplied != expected
        or encoded != _canonical_json_bytes(expected_payload)
    ):
        raise ArtifactContractError("foundation nonpass terminal differs from 120 raw records")
    return expected, evidence_rows


def _validate_complete_gate(gate: FoundationGate) -> None:
    if (
        not isinstance(gate, FoundationGate)
        or gate.complete is not True
        or not isinstance(gate.passed, bool)
    ):
        raise ArtifactContractError("foundation gate flags differ")
    if tuple(name for name, _ in gate.graph_lower_bounds) != GRAPHS:
        raise ArtifactContractError("foundation graph-bound inventory differs")
    if tuple(name for name, _ in gate.failure_upper_bounds) != FAILURE_LABELS:
        raise ArtifactContractError("foundation failure-bound inventory differs")
    values = tuple(value for _, value in gate.graph_lower_bounds) + (gate.pooled_lower_bound,) + tuple(
        value for _, value in gate.failure_upper_bounds
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not bool(torch.isfinite(torch.tensor(value)))
        or not 0.0 <= value <= 1.0
        for value in values
    ):
        raise ArtifactContractError("foundation gate bound is invalid")
    expected = (
        all(value > 0.72 for _, value in gate.graph_lower_bounds)
        and gate.pooled_lower_bound > 0.84
        and all(value < 0.10 for _, value in gate.failure_upper_bounds)
    )
    if gate.passed != expected:
        raise ArtifactContractError("foundation gate pass flag differs from strict bounds")


def _validate_foundation_binding(model: nn.Module, optimizer: ExactAdamW) -> None:
    if not isinstance(model, FoundationActorCritic):
        raise ArtifactContractError("checkpoint requires the isolated FCEOV FoundationActorCritic")
    if sum(value.numel() for value in model.parameters()) != 24_115:
        raise ArtifactContractError("foundation checkpoint parameter schema differs")
    if not optimizer.matches_named_parameters(tuple(model.named_parameters())):
        raise ArtifactContractError("checkpoint optimizer is not bound to this foundation")


__all__ = [
    "ArtifactContractError", "CHECKPOINT_SCHEMA", "FINAL_BUNDLE_SCHEMA", "FOUNDATION_GATE_SCHEMA", "PANEL_SCHEMA",
    "PANEL_FRONTIER_SCHEMA", "PANEL_SLICE_SCHEMA", "PanelFrontier", "PreparedFinalBundle",
    "RESUME_WITNESS_SCHEMA", "RUN_RECORD_SCHEMA", "ResumeWitness", "RunRecord", "RunRuntime",
    "SOURCE_NATIVE_SNAPSHOT_SCHEMA", "SourceNativeEntry", "SourceNativeSnapshot",
    "TERMINAL_FACT_SCHEMA", "direct_resume_equal", "load_checkpoint", "make_checkpoint",
    "build_panel_frontier", "build_run_record", "capture_source_native_snapshot",
    "compare_source_native_snapshot", "encode_source_native_snapshot", "final_bundle_encoded_size",
    "load_contiguous_panel_slices", "load_final_bundle", "load_foundation_gate",
    "load_foundation_nonpass_terminal", "load_panel_frontier", "load_panel_slice", "load_resume_witness",
    "load_rng_master", "load_run_record", "observe_resume_equality", "restore_checkpoint",
    "load_source_native_snapshot", "prepare_final_bundle", "write_checkpoint", "write_final_bundle",
    "write_foundation_gate", "write_panel_frontier", "write_panel_slice",
    "write_prepared_final_bundle", "write_resume_witness", "write_rng_master", "write_run_record",
    "validate_live_run_record_runtime", "write_source_native_snapshot", "write_terminal_fact",
]
