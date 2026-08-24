"""Production atomic frontier for the RCLE-TBCFV r04 empirical panel.

This module stores no scientific policy logic and materializes no random
coordinate.  It binds already-authorized production artifacts to one immutable
source/config/native/coordinate/master/origin/lease identity, provides a
parent-owned append-only mechanical resume chain for each of the twenty run
blocks, and withholds analyzer/result publication until every exact block is
sealed complete.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import threading
from typing import Any, Callable, Iterator, Mapping, Protocol, Sequence
import uuid

from .config import DIRECTION_ID, LEARNED_PACKAGES, SCIENCE_REVISION, SCRIPTED_PACKAGES
from .empirical_contract import (
    PANEL_COUNTS as CONTRACT_PANEL_COUNTS,
    SOURCE_REPAIR_REASON,
    SOURCE_REPAIR_TRANSITION_SCHEMA,
)
from .inference import (
    BRANCHES,
    DIRECT_VALUE_VARIABLES,
    HELDOUT_CELLS,
    MECHANISM_VARIABLES,
    PREREQUISITE_VARIABLES,
    TRAINING_CELLS,
)

EMPIRICAL_OBJECT = "RCLE-TBCFV-R04-FULL-EMPIRICAL-PANEL"
FRONTIER_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_FRONTIER_V1"
BINDINGS_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_BINDINGS_V1"
RESUME_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_RESUME_GENERATION_V1"
BLOCK_COMPLETE_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_BLOCK_COMPLETE_V1"
PANEL_COMPLETE_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_PANEL_COMPLETE_V1"
ANALYZER_OUTPUT_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_ANALYZER_OUTPUT_V1"
RESULT_OUTPUT_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_RESULT_OUTPUT_V1"
LEASE_AUDIT_SCHEMA = "RCLE_TBCFV_R04_EMPIRICAL_LEASE_AUDIT_V1"
LOCK_SCHEMA = "RCLE_TBCFV_R04_PARENT_COMMIT_LOCK_V1"
STAGING_SCHEMA = "RCLE_TBCFV_R04_GENERATION_STAGING_V1"
STAGE_REPAIR_AUDIT_SCHEMA = "RCLE_TBCFV_R04_STAGE_REPAIR_AUDIT_V1"

BLOCK_COUNT = 20
UPDATE_COUNT = 800
TRAIN_EPISODES_PER_UPDATE = 64
HELDOUT_EPISODES_PER_CELL = 2_048
REGISTERED_TAIL_COUNT = 72

LEARNED_ARMS = tuple(LEARNED_PACKAGES)
SCRIPTED_PANELS = tuple(SCRIPTED_PACKAGES)

REGISTERED_TAIL_NAMES = (
    tuple(f"prerequisite.{name}.lower" for name in PREREQUISITE_VARIABLES)
    + tuple(
        f"direct_value.{name}.{side}"
        for name in DIRECT_VALUE_VARIABLES
        for side in ("lower", "upper")
    )
    + tuple(
        f"mechanism.{name}.{side}"
        for name in MECHANISM_VARIABLES
        for side in ("lower", "upper")
    )
)
assert len(REGISTERED_TAIL_NAMES) == REGISTERED_TAIL_COUNT

COUNT_KEYS = (
    "training_episodes",
    "learned_heldout_episodes",
    "scripted_heldout_episodes",
    "total_episodes",
    "environment_ticks",
    "agent_ticks",
    "agent_claim_decisions",
    "candidate_pointer_scores",
)

BLOCK_COUNTS = {
    "training_episodes": 256_000,
    "learned_heldout_episodes": 81_920,
    "scripted_heldout_episodes": 49_152,
    "total_episodes": 387_072,
    "environment_ticks": 24_772_608,
    "agent_ticks": 214_958_080,
    "agent_claim_decisions": 53_739_520,
    "candidate_pointer_scores": 322_437_120,
}
PANEL_COUNTS = {name: value * BLOCK_COUNT for name, value in BLOCK_COUNTS.items()}
assert PANEL_COUNTS == {
    "training_episodes": 5_120_000,
    "learned_heldout_episodes": 1_638_400,
    "scripted_heldout_episodes": 983_040,
    "total_episodes": 7_741_440,
    "environment_ticks": 495_452_160,
    "agent_ticks": 4_299_161_600,
    "agent_claim_decisions": 1_074_790_400,
    "candidate_pointer_scores": 6_448_742_400,
}

_PHASES = (
    "TRAINING",
    "LEARNED_EVALUATION",
    "SCRIPTED_EVALUATION",
    "BLOCK_COMPLETE",
)
_HEX = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_BLOCK_NAME = re.compile(r"block_(0[0-9]|1[0-9])")
_GENERATION_NAME = re.compile(r"generation_([0-9]{6})\.json")
_STAGING_NAME = re.compile(r"generation_([0-9]{6})-([0-9a-f]{32})")
_PAYLOAD_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


class EmpiricalArtifactError(RuntimeError):
    """An empirical binding, atomic frontier, or completion object is invalid."""


@dataclass(frozen=True)
class EmpiricalBindings:
    """Immutable production identity for one same-coordinate frontier.

    ``lease_id`` is the contract's compatibility alias for the immutable
    origin lease; the renewable current permit is recorded only in lease audit
    entries.
    """

    source_manifest_sha256: str
    config_sha256: str
    native_binding_sha256: str
    coordinate_digest: str
    master_digest: str
    origin_lease_id: str
    lease_id: str
    lease_binding_sha256: str

    def validate(self) -> None:
        for name in (
            "source_manifest_sha256",
            "config_sha256",
            "native_binding_sha256",
            "coordinate_digest",
            "master_digest",
            "lease_binding_sha256",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _HEX.fullmatch(value):
                raise EmpiricalArtifactError(f"{name} must be a lowercase SHA-256 digest")
        if not isinstance(self.origin_lease_id, str) or not _IDENTIFIER.fullmatch(
            self.origin_lease_id
        ):
            raise EmpiricalArtifactError("origin_lease_id is malformed")
        if self.lease_id != self.origin_lease_id:
            raise EmpiricalArtifactError("immutable frontier lease_id must equal origin_lease_id")

    @property
    def stage_binding_sha256(self) -> str:
        return self.lease_binding_sha256


class ActiveLeasePermit(Protocol):
    """The caller-validated Root permit surface consumed by this frontier."""

    lease_id: str
    origin_lease_id: str
    predecessor_lease_id: str | None
    replacement_index: int
    lease_lineage: tuple[str, ...]
    stage_binding_sha256: str
    accepted_binding_sha256: str
    preactivity_certificate_sha256: str
    coordinate_proposal_sha256: str
    paths: Mapping[str, str]
    repair_transition_sha256: str | None

    def require_active(self, *, now: datetime) -> None: ...


@dataclass(frozen=True)
class ArtifactRef:
    """Immutable reference to one regular file below a block's data directory."""

    path: str
    sha256: str
    size_bytes: int

    @classmethod
    def capture(cls, frontier_root: str | os.PathLike[str], path: str | os.PathLike[str]) -> "ArtifactRef":
        root = Path(frontier_root).resolve()
        target = Path(path).resolve()
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise EmpiricalArtifactError("artifact escapes the empirical frontier") from exc
        payload = _read_regular_bytes(target)
        return cls(relative.as_posix(), _sha256(payload), len(payload))


@dataclass(frozen=True)
class ResumeState:
    """Complete mechanical state needed to continue one blinded run block."""

    phase: str
    updates_completed: Mapping[str, int]
    model_state: Mapping[str, ArtifactRef]
    optimizer_state: Mapping[str, ArtifactRef]
    baselines: Mapping[str, ArtifactRef]
    semantic_coordinate: ArtifactRef
    aggregates: ArtifactRef
    learned_heldout_completed: Mapping[str, Mapping[str, int]]
    scripted_heldout_completed: Mapping[str, Mapping[str, int]]
    counts: Mapping[str, int]


@dataclass(frozen=True)
class CompletePanel:
    branch: str
    analyzer_payload: bytes
    result_payload: bytes
    manifest: Mapping[str, Any]


@dataclass(frozen=True)
class StagedGeneration:
    block_index: int
    generation: int
    token: str
    refs: Mapping[str, ArtifactRef]


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, OverflowError, UnicodeEncodeError) as exc:
        raise EmpiricalArtifactError("artifact must be finite canonical JSON") from exc
    return encoded + b"\n"


def _read_regular_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise EmpiricalArtifactError(f"required regular artifact is missing: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise EmpiricalArtifactError(f"cannot read artifact: {path}") from exc


def _read_canonical_json(path: Path) -> Mapping[str, Any]:
    payload = _read_regular_bytes(path)
    return _canonical_mapping_bytes(payload, str(path))


def _canonical_mapping_bytes(payload: bytes, location: str) -> Mapping[str, Any]:
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EmpiricalArtifactError(f"malformed JSON artifact: {location}") from exc
    if not isinstance(value, Mapping) or _canonical_json(value) != payload:
        raise EmpiricalArtifactError(f"artifact is not an exact canonical mapping: {location}")
    return value


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise EmpiricalArtifactError(f"create-only artifact already exists: {path.name}")
    # Keep the temporary basename independent of the target basename.  A
    # target may already be close to the Windows legacy path ceiling; copying
    # its full name into the temporary name can make an otherwise valid atomic
    # publication impossible.  The full UUID retains collision resistance and
    # the same parent retains same-volume rename semantics.
    temporary = path.parent / f".aw-{uuid.uuid4().hex}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise EmpiricalArtifactError(f"create-only artifact already exists: {path.name}")
        os.rename(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _exact_mapping(value: object, keys: Sequence[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(keys):
        raise EmpiricalArtifactError(f"{location} inventory differs from the frozen schema")
    return value


def _owner_digest(owner_token: str) -> str:
    if not isinstance(owner_token, str) or not _IDENTIFIER.fullmatch(owner_token):
        raise EmpiricalArtifactError("parent owner token is malformed")
    return _sha256(owner_token.encode("ascii"))


def _process_is_alive(process_id: int) -> bool:
    if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id <= 0:
        return False
    if process_id == os.getpid():
        return True
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            open_process = kernel32.OpenProcess
            open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            open_process.restype = wintypes.HANDLE
            close_handle = kernel32.CloseHandle
            close_handle.argtypes = (wintypes.HANDLE,)
            close_handle.restype = wintypes.BOOL
            get_exit_code = kernel32.GetExitCodeProcess
            get_exit_code.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
            get_exit_code.restype = wintypes.BOOL
            handle = open_process(0x1000, False, process_id)
            if not handle:
                # ERROR_INVALID_PARAMETER deterministically means no such PID;
                # access denial and all other errors remain ambiguous/live.
                return ctypes.get_last_error() != 87
            try:
                code = wintypes.DWORD()
                if not get_exit_code(handle, ctypes.byref(code)):
                    return True
                return int(code.value) == 259
            finally:
                close_handle(handle)
        except Exception:
            return True
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        # Permission and platform ambiguity are treated as live.
        return True
    return True


def stage_binding_sha256_for_permit(permit: ActiveLeasePermit) -> str:
    """Return the contract-validated immutable stage binding."""

    value = getattr(permit, "stage_binding_sha256", None)
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise EmpiricalArtifactError("active permit stage_binding_sha256 is malformed")
    return value


def _validate_active_permit(
    permit: ActiveLeasePermit,
    *,
    now: datetime,
    bindings: EmpiricalBindings,
) -> str:
    try:
        permit.require_active(now=now)
    except Exception as exc:
        raise EmpiricalArtifactError("caller permit is not active and validated") from exc
    lease_id = getattr(permit, "lease_id", None)
    if not isinstance(lease_id, str) or not _IDENTIFIER.fullmatch(lease_id):
        raise EmpiricalArtifactError("active permit lease_id is malformed")
    if stage_binding_sha256_for_permit(permit) != bindings.lease_binding_sha256:
        raise EmpiricalArtifactError("replacement permit changes the invariant stage binding")
    permit_origin = getattr(permit, "origin_lease_id", None)
    if permit_origin != bindings.origin_lease_id:
        raise EmpiricalArtifactError("replacement permit changes the origin lease lineage")
    immutable = getattr(permit, "immutable_frontier_lease_binding", None)
    if callable(immutable):
        try:
            mapped = immutable()
        except Exception as exc:
            raise EmpiricalArtifactError("permit immutable frontier binding is unavailable") from exc
        if mapped != {
            "origin_lease_id": bindings.origin_lease_id,
            "lease_id": bindings.lease_id,
            "lease_binding_sha256": bindings.lease_binding_sha256,
        }:
            raise EmpiricalArtifactError("permit immutable frontier binding differs")
    return lease_id


def _block_name(index: int) -> str:
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < BLOCK_COUNT:
        raise EmpiricalArtifactError("run block index must be in [0,19]")
    return f"block_{index:02d}"


def _ref_to_mapping(value: ArtifactRef) -> Mapping[str, object]:
    if not isinstance(value, ArtifactRef):
        raise EmpiricalArtifactError("resume component must be an ArtifactRef")
    return asdict(value)


def _ref_from_mapping(value: object, location: str) -> ArtifactRef:
    mapping = _exact_mapping(value, ("path", "sha256", "size_bytes"), location)
    try:
        return ArtifactRef(
            path=mapping["path"],  # type: ignore[arg-type]
            sha256=mapping["sha256"],  # type: ignore[arg-type]
            size_bytes=mapping["size_bytes"],  # type: ignore[arg-type]
        )
    except TypeError as exc:
        raise EmpiricalArtifactError(f"{location} schema differs") from exc


def _state_to_mapping(state: ResumeState) -> Mapping[str, object]:
    return {
        "phase": state.phase,
        "updates_completed": dict(state.updates_completed),
        "model_state": {key: _ref_to_mapping(value) for key, value in state.model_state.items()},
        "optimizer_state": {
            key: _ref_to_mapping(value) for key, value in state.optimizer_state.items()
        },
        "baselines": {key: _ref_to_mapping(value) for key, value in state.baselines.items()},
        "semantic_coordinate": _ref_to_mapping(state.semantic_coordinate),
        "aggregates": _ref_to_mapping(state.aggregates),
        "learned_heldout_completed": {
            arm: dict(cells) for arm, cells in state.learned_heldout_completed.items()
        },
        "scripted_heldout_completed": {
            package: dict(cells) for package, cells in state.scripted_heldout_completed.items()
        },
        "counts": dict(state.counts),
    }


def _state_from_mapping(value: object) -> ResumeState:
    mapping = _exact_mapping(
        value,
        (
            "phase",
            "updates_completed",
            "model_state",
            "optimizer_state",
            "baselines",
            "semantic_coordinate",
            "aggregates",
            "learned_heldout_completed",
            "scripted_heldout_completed",
            "counts",
        ),
        "resume state",
    )
    models = _exact_mapping(mapping["model_state"], LEARNED_ARMS, "model_state")
    optimizers = _exact_mapping(mapping["optimizer_state"], LEARNED_ARMS, "optimizer_state")
    baselines = _exact_mapping(mapping["baselines"], LEARNED_ARMS, "baselines")
    learned = _exact_mapping(
        mapping["learned_heldout_completed"], LEARNED_ARMS, "learned heldout"
    )
    scripted = _exact_mapping(
        mapping["scripted_heldout_completed"], SCRIPTED_PANELS, "scripted heldout"
    )
    return ResumeState(
        phase=mapping["phase"],  # type: ignore[arg-type]
        updates_completed=mapping["updates_completed"],  # type: ignore[arg-type]
        model_state={arm: _ref_from_mapping(models[arm], f"model_state.{arm}") for arm in LEARNED_ARMS},
        optimizer_state={
            arm: _ref_from_mapping(optimizers[arm], f"optimizer_state.{arm}")
            for arm in LEARNED_ARMS
        },
        baselines={
            arm: _ref_from_mapping(baselines[arm], f"baselines.{arm}") for arm in LEARNED_ARMS
        },
        semantic_coordinate=_ref_from_mapping(mapping["semantic_coordinate"], "semantic_coordinate"),
        aggregates=_ref_from_mapping(mapping["aggregates"], "aggregates"),
        learned_heldout_completed={
            arm: learned[arm] for arm in LEARNED_ARMS  # type: ignore[misc]
        },
        scripted_heldout_completed={
            package: scripted[package] for package in SCRIPTED_PANELS  # type: ignore[misc]
        },
        counts=mapping["counts"],  # type: ignore[arg-type]
    )


def _validate_ref(root: Path, block_index: int, ref: ArtifactRef, location: str) -> str:
    if not isinstance(ref.path, str) or not isinstance(ref.sha256, str):
        raise EmpiricalArtifactError(f"{location} reference types differ")
    pure = PurePosixPath(ref.path)
    expected_prefix = PurePosixPath("blocks") / _block_name(block_index) / "data"
    if pure.is_absolute() or ".." in pure.parts or tuple(pure.parts[:3]) != tuple(expected_prefix.parts):
        raise EmpiricalArtifactError(f"{location} must remain below its run-block data directory")
    if not _HEX.fullmatch(ref.sha256):
        raise EmpiricalArtifactError(f"{location} digest is malformed")
    if isinstance(ref.size_bytes, bool) or not isinstance(ref.size_bytes, int) or ref.size_bytes < 0:
        raise EmpiricalArtifactError(f"{location} size is malformed")
    target = root.joinpath(*pure.parts)
    payload = _read_regular_bytes(target)
    if len(payload) != ref.size_bytes or _sha256(payload) != ref.sha256:
        raise EmpiricalArtifactError(f"{location} size or digest differs")
    return pure.as_posix()


def _validate_counts(state: ResumeState) -> None:
    counts = _exact_mapping(state.counts, COUNT_KEYS, "resume counts")
    for name in COUNT_KEYS:
        value = counts[name]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= BLOCK_COUNTS[name]:
            raise EmpiricalArtifactError(f"resume count {name} is outside the exact block envelope")
    expected_training = sum(state.updates_completed.values()) * TRAIN_EPISODES_PER_UPDATE
    expected_learned = sum(
        count for cells in state.learned_heldout_completed.values() for count in cells.values()
    )
    expected_scripted = sum(
        count for cells in state.scripted_heldout_completed.values() for count in cells.values()
    )
    if counts["training_episodes"] != expected_training:
        raise EmpiricalArtifactError("training episode count does not match completed updates")
    if counts["learned_heldout_episodes"] != expected_learned:
        raise EmpiricalArtifactError("learned heldout count does not match exact cells")
    if counts["scripted_heldout_episodes"] != expected_scripted:
        raise EmpiricalArtifactError("scripted heldout count does not match exact cells")
    if counts["total_episodes"] != expected_training + expected_learned + expected_scripted:
        raise EmpiricalArtifactError("total episode count differs")
    if counts["environment_ticks"] != counts["total_episodes"] * 64:
        raise EmpiricalArtifactError("environment tick count differs")
    if counts["candidate_pointer_scores"] != counts["agent_claim_decisions"] * 6:
        raise EmpiricalArtifactError("candidate pointer score count differs")


def _validate_state(root: Path, block_index: int, state: ResumeState) -> set[str]:
    if state.phase not in _PHASES:
        raise EmpiricalArtifactError("resume phase differs from the frozen lifecycle")
    updates = _exact_mapping(state.updates_completed, LEARNED_ARMS, "updates_completed")
    for arm in LEARNED_ARMS:
        value = updates[arm]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= UPDATE_COUNT:
            raise EmpiricalArtifactError(f"update count for {arm} is outside [0,800]")
    _exact_mapping(state.model_state, LEARNED_ARMS, "model_state")
    _exact_mapping(state.optimizer_state, LEARNED_ARMS, "optimizer_state")
    _exact_mapping(state.baselines, LEARNED_ARMS, "baselines")
    learned = _exact_mapping(
        state.learned_heldout_completed, LEARNED_ARMS, "learned_heldout_completed"
    )
    scripted = _exact_mapping(
        state.scripted_heldout_completed, SCRIPTED_PANELS, "scripted_heldout_completed"
    )
    for family, owners in (("learned", learned), ("scripted", scripted)):
        for owner, raw_cells in owners.items():
            cells = _exact_mapping(raw_cells, HELDOUT_CELLS, f"{family}.{owner}")
            for cell in HELDOUT_CELLS:
                value = cells[cell]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, int)
                    or not 0 <= value <= HELDOUT_EPISODES_PER_CELL
                ):
                    raise EmpiricalArtifactError(f"{family}.{owner}.{cell} count differs")
    if state.phase != "TRAINING" and any(value != UPDATE_COUNT for value in updates.values()):
        raise EmpiricalArtifactError("evaluation phase reached before all update-800 checkpoints")
    if state.phase == "TRAINING" and any(
        value for owner in learned.values() for value in owner.values()
    ):
        raise EmpiricalArtifactError("learned evaluation appeared during training")
    if state.phase in ("TRAINING", "LEARNED_EVALUATION") and any(
        value for owner in scripted.values() for value in owner.values()
    ):
        raise EmpiricalArtifactError("scripted evaluation appeared before its phase")
    if state.phase in ("SCRIPTED_EVALUATION", "BLOCK_COMPLETE") and any(
        value != HELDOUT_EPISODES_PER_CELL
        for owner in learned.values()
        for value in owner.values()
    ):
        raise EmpiricalArtifactError("scripted phase reached before complete learned heldout cells")
    _validate_counts(state)
    if state.phase == "BLOCK_COMPLETE" and not _is_complete_state(state):
        raise EmpiricalArtifactError("BLOCK_COMPLETE state is not the exact complete block")

    refs: list[tuple[str, ArtifactRef]] = []
    refs.extend((f"model_state.{arm}", state.model_state[arm]) for arm in LEARNED_ARMS)
    refs.extend((f"optimizer_state.{arm}", state.optimizer_state[arm]) for arm in LEARNED_ARMS)
    refs.extend((f"baselines.{arm}", state.baselines[arm]) for arm in LEARNED_ARMS)
    refs.append(("semantic_coordinate", state.semantic_coordinate))
    refs.append(("aggregates", state.aggregates))
    paths = {_validate_ref(root, block_index, ref, name) for name, ref in refs}
    if len(paths) != len(refs):
        raise EmpiricalArtifactError("mechanical resume components must have distinct immutable files")
    return paths


def _validate_monotonic(previous: ResumeState, current: ResumeState) -> None:
    if _PHASES.index(current.phase) < _PHASES.index(previous.phase):
        raise EmpiricalArtifactError("resume phase regressed")
    for arm in LEARNED_ARMS:
        if current.updates_completed[arm] < previous.updates_completed[arm]:
            raise EmpiricalArtifactError("completed update count regressed")
        for cell in HELDOUT_CELLS:
            if (
                current.learned_heldout_completed[arm][cell]
                < previous.learned_heldout_completed[arm][cell]
            ):
                raise EmpiricalArtifactError("learned heldout frontier regressed")
    for package in SCRIPTED_PANELS:
        for cell in HELDOUT_CELLS:
            if (
                current.scripted_heldout_completed[package][cell]
                < previous.scripted_heldout_completed[package][cell]
            ):
                raise EmpiricalArtifactError("scripted heldout frontier regressed")
    for name in COUNT_KEYS:
        if current.counts[name] < previous.counts[name]:
            raise EmpiricalArtifactError("mechanical count frontier regressed")


def _state_artifact_refs(state: ResumeState) -> tuple[ArtifactRef, ...]:
    return (
        tuple(state.model_state[arm] for arm in LEARNED_ARMS)
        + tuple(state.optimizer_state[arm] for arm in LEARNED_ARMS)
        + tuple(state.baselines[arm] for arm in LEARNED_ARMS)
        + (state.semantic_coordinate, state.aggregates)
    )


def _is_complete_state(state: ResumeState) -> bool:
    return (
        state.phase == "BLOCK_COMPLETE"
        and all(value == UPDATE_COUNT for value in state.updates_completed.values())
        and all(
            value == HELDOUT_EPISODES_PER_CELL
            for cells in state.learned_heldout_completed.values()
            for value in cells.values()
        )
        and all(
            value == HELDOUT_EPISODES_PER_CELL
            for cells in state.scripted_heldout_completed.values()
            for value in cells.values()
        )
        and dict(state.counts) == BLOCK_COUNTS
    )


def _validate_publication_payloads(
    analyzer_payload: bytes, result_payload: bytes, branch: str
) -> None:
    analyzer = _canonical_mapping_bytes(analyzer_payload, "analyzer payload")
    _exact_mapping(
        analyzer,
        (
            "schema",
            "science_revision",
            "empirical_object",
            "block_count",
            "registered_tail_count",
            "registered_tail_names",
            "branch",
            "payload",
        ),
        "analyzer payload",
    )
    if (
        analyzer["schema"] != ANALYZER_OUTPUT_SCHEMA
        or analyzer["science_revision"] != SCIENCE_REVISION
        or analyzer["empirical_object"] != EMPIRICAL_OBJECT
        or analyzer["block_count"] != BLOCK_COUNT
        or analyzer["registered_tail_count"] != REGISTERED_TAIL_COUNT
        or analyzer["registered_tail_names"] != list(REGISTERED_TAIL_NAMES)
        or analyzer["branch"] != branch
        or not isinstance(analyzer["payload"], Mapping)
    ):
        raise EmpiricalArtifactError("analyzer payload identity or exact tail inventory differs")

    result = _canonical_mapping_bytes(result_payload, "result payload")
    _exact_mapping(
        result,
        (
            "schema",
            "science_revision",
            "empirical_object",
            "block_count",
            "counts",
            "branch",
            "analyzer_sha256",
            "payload",
        ),
        "result payload",
    )
    if (
        result["schema"] != RESULT_OUTPUT_SCHEMA
        or result["science_revision"] != SCIENCE_REVISION
        or result["empirical_object"] != EMPIRICAL_OBJECT
        or result["block_count"] != BLOCK_COUNT
        or result["counts"] != PANEL_COUNTS
        or result["branch"] != branch
        or result["analyzer_sha256"] != _sha256(analyzer_payload)
        or not isinstance(result["payload"], Mapping)
    ):
        raise EmpiricalArtifactError("result payload identity, analyzer binding, or counts differ")


class AtomicEmpiricalFrontier:
    """Create-only, parent-owned, same-coordinate empirical frontier."""

    def __init__(
        self,
        root: Path,
        bindings: EmpiricalBindings,
        owner_sha256: str,
        current_lease_audit_sha256: str | None = None,
        effective_bindings: EmpiricalBindings | None = None,
    ):
        self.root = root
        self._original_bindings = bindings
        self.bindings = effective_bindings or bindings
        self._owner_sha256 = owner_sha256
        self._current_lease_audit_sha256 = current_lease_audit_sha256
        self._process_commit_lock = threading.Lock()

    @classmethod
    def create(
        cls,
        root: str | os.PathLike[str],
        bindings: EmpiricalBindings,
        *,
        owner_token: str,
        permit: ActiveLeasePermit,
        now: datetime,
        lease_document_sha256: str,
    ) -> "AtomicEmpiricalFrontier":
        bindings.validate()
        lease_id = _validate_active_permit(permit, now=now, bindings=bindings)
        if lease_id != bindings.origin_lease_id:
            raise EmpiricalArtifactError("originating permit must equal origin_lease_id")
        if not _HEX.fullmatch(lease_document_sha256):
            raise EmpiricalArtifactError("lease document digest is malformed")
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=False)
        (root_path / "blocks").mkdir()
        (root_path / "lease_audits").mkdir()
        manifest = {
            "schema": BINDINGS_SCHEMA,
            "empirical_object": EMPIRICAL_OBJECT,
            "science_revision": SCIENCE_REVISION,
            "bindings": asdict(bindings),
            "parent_owner_sha256": _owner_digest(owner_token),
            "block_count": BLOCK_COUNT,
            "learned_arms": list(LEARNED_ARMS),
            "scripted_panels": list(SCRIPTED_PANELS),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
            "panel_counts": dict(PANEL_COUNTS),
            "same_coordinate_resume": True,
            "scientific_values_exposed": False,
            "partial_interpretation_permitted": False,
        }
        _write_exclusive(root_path / "bindings.json", _canonical_json(manifest))
        frontier = cls(root_path, bindings, manifest["parent_owner_sha256"])
        frontier._register_active_permit(
            permit,
            now=now,
            lease_document_sha256=lease_document_sha256,
            owner_token=owner_token,
        )
        return frontier

    @classmethod
    def resume(
        cls,
        root: str | os.PathLike[str],
        expected_bindings: EmpiricalBindings,
        *,
        owner_token: str,
        permit: ActiveLeasePermit,
        now: datetime,
        lease_document_sha256: str,
        process_alive_probe: Callable[[int], bool] | None = None,
    ) -> "AtomicEmpiricalFrontier":
        root_path = Path(root)
        expected_bindings.validate()
        if not _HEX.fullmatch(lease_document_sha256):
            raise EmpiricalArtifactError("lease document digest is malformed")
        manifest = _read_canonical_json(root_path / "bindings.json")
        expected_keys = (
            "schema",
            "empirical_object",
            "science_revision",
            "bindings",
            "parent_owner_sha256",
            "block_count",
            "learned_arms",
            "scripted_panels",
            "training_cells",
            "heldout_cells",
            "panel_counts",
            "same_coordinate_resume",
            "scientific_values_exposed",
            "partial_interpretation_permitted",
        )
        _exact_mapping(manifest, expected_keys, "frontier bindings manifest")
        if (
            manifest["schema"] != BINDINGS_SCHEMA
            or manifest["empirical_object"] != EMPIRICAL_OBJECT
            or manifest["science_revision"] != SCIENCE_REVISION
            or manifest["parent_owner_sha256"] != _owner_digest(owner_token)
            or manifest["block_count"] != BLOCK_COUNT
            or manifest["learned_arms"] != list(LEARNED_ARMS)
            or manifest["scripted_panels"] != list(SCRIPTED_PANELS)
            or manifest["training_cells"] != list(TRAINING_CELLS)
            or manifest["heldout_cells"] != list(HELDOUT_CELLS)
            or manifest["panel_counts"] != PANEL_COUNTS
            or manifest["same_coordinate_resume"] is not True
            or manifest["scientific_values_exposed"] is not False
            or manifest["partial_interpretation_permitted"] is not False
        ):
            raise EmpiricalArtifactError("same-coordinate frontier binding differs")
        raw_bindings = manifest["bindings"]
        if not isinstance(raw_bindings, Mapping):
            raise EmpiricalArtifactError("frontier original binding is malformed")
        try:
            original_bindings = EmpiricalBindings(**raw_bindings)
        except TypeError as exc:
            raise EmpiricalArtifactError("frontier original binding schema differs") from exc
        original_bindings.validate()
        frontier = cls(root_path, original_bindings, manifest["parent_owner_sha256"])
        frontier._recover_stale_lock(
            owner_token,
            process_alive_probe=process_alive_probe,
        )
        frontier._validate_bindings_manifest()
        frontier._validate_stage_repair_audit()
        if expected_bindings != frontier.bindings:
            raise EmpiricalArtifactError("same-coordinate effective frontier binding differs")
        _validate_active_permit(permit, now=now, bindings=frontier.bindings)
        frontier._recover_generation_orphans(owner_token)
        frontier.validate()
        audits = frontier._validate_lease_audits()
        frontier._current_lease_audit_sha256 = audits[-1][0]
        frontier._register_active_permit(
            permit,
            now=now,
            lease_document_sha256=lease_document_sha256,
            owner_token=owner_token,
        )
        return frontier

    def _require_owner(self, owner_token: str) -> None:
        if _owner_digest(owner_token) != self._owner_sha256:
            raise EmpiricalArtifactError("only the bound parent owner may commit")

    def _recover_stale_lock(
        self,
        owner_token: str,
        *,
        process_alive_probe: Callable[[int], bool] | None,
    ) -> None:
        self._require_owner(owner_token)
        lock = self.root / "PARENT_COMMIT.lock"
        if not lock.exists():
            return
        try:
            initial_stat = lock.stat(follow_symlinks=False)
        except OSError as exc:
            raise EmpiricalArtifactError("persistent parent lock cannot be inspected") from exc
        packet = _read_canonical_json(lock)
        _exact_mapping(
            packet,
            (
                "schema",
                "parent_owner_sha256",
                "frontier_bindings_sha256",
                "process_id",
                "process_nonce",
            ),
            "parent commit lock",
        )
        if (
            packet["schema"] != LOCK_SCHEMA
            or packet["parent_owner_sha256"] != self._owner_sha256
            or packet["frontier_bindings_sha256"] != self.bindings_sha256
            or not isinstance(packet["process_id"], int)
            or isinstance(packet["process_id"], bool)
            or not isinstance(packet["process_nonce"], str)
            or not _HEX.fullmatch(packet["process_nonce"])
        ):
            raise EmpiricalArtifactError("persistent parent lock has foreign or ambiguous provenance")
        probe = process_alive_probe or _process_is_alive
        try:
            alive = probe(int(packet["process_id"]))
        except Exception as exc:
            raise EmpiricalArtifactError("parent lock liveness is unprovable") from exc
        if alive is not False:
            raise EmpiricalArtifactError("parent commit lock belongs to a live or ambiguous process")
        observed = _read_regular_bytes(lock)
        if _sha256(observed) != _sha256(_canonical_json(packet)):
            raise EmpiricalArtifactError("parent commit lock changed during stale proof")
        try:
            final_stat = lock.stat(follow_symlinks=False)
        except OSError as exc:
            raise EmpiricalArtifactError("parent commit lock changed during stale proof") from exc
        if (
            initial_stat.st_dev,
            initial_stat.st_ino,
            initial_stat.st_size,
            initial_stat.st_mtime_ns,
        ) != (
            final_stat.st_dev,
            final_stat.st_ino,
            final_stat.st_size,
            final_stat.st_mtime_ns,
        ):
            raise EmpiricalArtifactError("parent commit lock changed during stale proof")
        lock.unlink()

    @contextmanager
    def _exclusive_commit(self, owner_token: str) -> Iterator[None]:
        self._require_owner(owner_token)
        with self._process_commit_lock:
            lock = self.root / "PARENT_COMMIT.lock"
            payload = _canonical_json(
                {
                    "schema": LOCK_SCHEMA,
                    "parent_owner_sha256": self._owner_sha256,
                    "frontier_bindings_sha256": self.bindings_sha256,
                    "process_id": os.getpid(),
                    "process_nonce": _sha256(uuid.uuid4().bytes),
                }
            )
            try:
                descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError as exc:
                raise EmpiricalArtifactError("another parent commit is active") from exc
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                yield
            finally:
                try:
                    if lock.is_file() and not lock.is_symlink() and lock.read_bytes() == payload:
                        lock.unlink()
                except OSError:
                    pass

    def _validate_lease_audits(self) -> list[tuple[str, Mapping[str, Any]]]:
        audit_root = self.root / "lease_audits"
        if not audit_root.is_dir() or audit_root.is_symlink():
            raise EmpiricalArtifactError("lease audit root is missing")
        entries = sorted(audit_root.iterdir(), key=lambda item: item.name)
        if not entries:
            raise EmpiricalArtifactError("origin lease audit is missing")
        result: list[tuple[str, Mapping[str, Any]]] = []
        previous_digest: str | None = None
        previous_lease: str | None = None
        seen_leases: set[str] = set()
        repair = self._validate_stage_repair_audit()
        for index, path in enumerate(entries):
            if path.name != f"lease_{index:06d}.json":
                raise EmpiricalArtifactError("lease audit inventory is incomplete or extra")
            packet = _read_canonical_json(path)
            base_keys = {
                    "schema",
                    "index",
                    "lease_id",
                    "lease_document_sha256",
                    "origin_lease_id",
                    "stage_binding_sha256",
                    "source_manifest_sha256",
                    "config_sha256",
                    "native_binding_sha256",
                    "coordinate_digest",
                    "master_digest",
                    "predecessor_lease_id",
                    "previous_audit_sha256",
                    "validated_at",
                    "active_validated",
                    "replacement_coordinate_created",
            }
            packet_keys = set(packet)
            if packet_keys not in (base_keys, base_keys | {"repair_transition_sha256"}):
                raise EmpiricalArtifactError("lease audit field inventory differs")
            expected_bindings = (
                self._original_bindings if index == 0 else self.bindings
            )
            expected_repair_sha = None
            if repair is not None and index == 1:
                expected_repair_sha = repair["repair_transition_sha256"]
            lease_id = packet["lease_id"]
            if (
                packet["schema"] != LEASE_AUDIT_SCHEMA
                or packet["index"] != index
                or not isinstance(lease_id, str)
                or not _IDENTIFIER.fullmatch(lease_id)
                or lease_id in seen_leases
                or not isinstance(packet["lease_document_sha256"], str)
                or not _HEX.fullmatch(packet["lease_document_sha256"])
                or packet["origin_lease_id"] != expected_bindings.origin_lease_id
                or packet["stage_binding_sha256"] != expected_bindings.stage_binding_sha256
                or packet["source_manifest_sha256"] != expected_bindings.source_manifest_sha256
                or packet["config_sha256"] != expected_bindings.config_sha256
                or packet["native_binding_sha256"] != expected_bindings.native_binding_sha256
                or packet["coordinate_digest"] != expected_bindings.coordinate_digest
                or packet["master_digest"] != expected_bindings.master_digest
                or packet.get("repair_transition_sha256") != expected_repair_sha
                or packet["previous_audit_sha256"] != previous_digest
                or packet["predecessor_lease_id"] != previous_lease
                or not isinstance(packet["validated_at"], str)
                or packet["active_validated"] is not True
                or packet["replacement_coordinate_created"] is not False
            ):
                raise EmpiricalArtifactError("lease audit lineage or immutable binding differs")
            if index == 0 and lease_id != self._original_bindings.origin_lease_id:
                raise EmpiricalArtifactError("first lease audit is not the origin lease")
            if repair is not None and index == 0 and len(entries) < 2:
                raise EmpiricalArtifactError("stage repair audit lacks its replacement lease audit")
            if repair is not None and index == 1 and (
                repair["old_lease_id"] != previous_lease
                or repair["new_lease_id"] != lease_id
                or repair["old_lease_audit_sha256"] != previous_digest
                or repair["new_lease_document_sha256"]
                != packet["lease_document_sha256"]
            ):
                raise EmpiricalArtifactError("stage repair lease bridge differs")
            payload = _read_regular_bytes(path)
            digest = _sha256(payload)
            result.append((digest, packet))
            previous_digest = digest
            previous_lease = lease_id
            seen_leases.add(lease_id)
        return result

    def _register_active_permit(
        self,
        permit: ActiveLeasePermit,
        *,
        now: datetime,
        lease_document_sha256: str,
        owner_token: str,
    ) -> None:
        lease_id = _validate_active_permit(permit, now=now, bindings=self.bindings)
        if not _HEX.fullmatch(lease_document_sha256):
            raise EmpiricalArtifactError("lease document digest is malformed")
        lineage = getattr(permit, "predecessor_lease_id", None)
        replacement_index = getattr(permit, "replacement_index", None)
        lease_lineage = getattr(permit, "lease_lineage", None)
        repair_transition_sha256 = getattr(permit, "repair_transition_sha256", None)
        with self._exclusive_commit(owner_token):
            audit_root = self.root / "lease_audits"
            entries = sorted(audit_root.iterdir(), key=lambda item: item.name)
            if entries:
                audits = self._validate_lease_audits()
                previous_digest, previous_packet = audits[-1]
                previous_lease = str(previous_packet["lease_id"])
                if lease_id == previous_lease:
                    if (
                        lease_document_sha256 != previous_packet["lease_document_sha256"]
                        or lineage != previous_packet["predecessor_lease_id"]
                        or replacement_index != previous_packet["index"]
                        or tuple(lease_lineage or ())
                        != tuple(packet["lease_id"] for _, packet in audits)
                        or repair_transition_sha256
                        != previous_packet.get("repair_transition_sha256")
                    ):
                        raise EmpiricalArtifactError("same lease resume changes its document or lineage")
                    self._current_lease_audit_sha256 = previous_digest
                    return
                if any(packet["lease_id"] == lease_id for _, packet in audits):
                    raise EmpiricalArtifactError("lease audit cannot roll back to an earlier lease")
                if lineage != previous_lease:
                    raise EmpiricalArtifactError("replacement permit does not continue the current lease lineage")
                index = len(audits)
                if replacement_index != index or tuple(lease_lineage or ()) != tuple(
                    [packet["lease_id"] for _, packet in audits] + [lease_id]
                ):
                    raise EmpiricalArtifactError("replacement permit lineage index or chain differs")
            else:
                if (
                    lease_id != self.bindings.origin_lease_id
                    or lineage is not None
                    or replacement_index != 0
                    or tuple(lease_lineage or ()) != (lease_id,)
                ):
                    raise EmpiricalArtifactError("first active permit is not the origin lease")
                previous_digest = None
                previous_lease = None
                index = 0
            packet = {
                "schema": LEASE_AUDIT_SCHEMA,
                "index": index,
                "lease_id": lease_id,
                "lease_document_sha256": lease_document_sha256,
                "origin_lease_id": self.bindings.origin_lease_id,
                "stage_binding_sha256": self.bindings.stage_binding_sha256,
                "source_manifest_sha256": self.bindings.source_manifest_sha256,
                "config_sha256": self.bindings.config_sha256,
                "native_binding_sha256": self.bindings.native_binding_sha256,
                "coordinate_digest": self.bindings.coordinate_digest,
                "master_digest": self.bindings.master_digest,
                "predecessor_lease_id": previous_lease,
                "previous_audit_sha256": previous_digest,
                "validated_at": now.isoformat(),
                "active_validated": True,
                "replacement_coordinate_created": False,
                "repair_transition_sha256": repair_transition_sha256,
            }
            payload = _canonical_json(packet)
            _write_exclusive(audit_root / f"lease_{index:06d}.json", payload)
            self._current_lease_audit_sha256 = _sha256(payload)
            self._validate_lease_audits()

    @property
    def bindings_sha256(self) -> str:
        return _sha256(_read_regular_bytes(self.root / "bindings.json"))

    @property
    def effective_bindings_sha256(self) -> str:
        return _sha256(
            _canonical_json(
                {
                    "schema": BINDINGS_SCHEMA,
                    "effective_bindings": asdict(self.bindings),
                }
            )
        )

    def _validate_bindings_manifest(self) -> None:
        manifest = _read_canonical_json(self.root / "bindings.json")
        expected = {
            "schema": BINDINGS_SCHEMA,
            "empirical_object": EMPIRICAL_OBJECT,
            "science_revision": SCIENCE_REVISION,
            "bindings": asdict(self._original_bindings),
            "parent_owner_sha256": self._owner_sha256,
            "block_count": BLOCK_COUNT,
            "learned_arms": list(LEARNED_ARMS),
            "scripted_panels": list(SCRIPTED_PANELS),
            "training_cells": list(TRAINING_CELLS),
            "heldout_cells": list(HELDOUT_CELLS),
            "panel_counts": dict(PANEL_COUNTS),
            "same_coordinate_resume": True,
            "scientific_values_exposed": False,
            "partial_interpretation_permitted": False,
        }
        if dict(manifest) != expected:
            raise EmpiricalArtifactError("same-coordinate frontier binding differs")

    def _validate_stage_repair_audit(self) -> Mapping[str, Any] | None:
        repair_root = self.root / "stage_repairs"
        if not repair_root.exists():
            self.bindings = self._original_bindings
            return None
        if not repair_root.is_dir() or repair_root.is_symlink():
            raise EmpiricalArtifactError("stage repair audit root is invalid")
        entries = list(repair_root.iterdir())
        if len(entries) != 1 or entries[0].name != "repair_000001.json":
            raise EmpiricalArtifactError("stage repair audit is duplicate or incomplete")
        audit = _read_canonical_json(entries[0])
        _exact_mapping(
            audit,
            (
                "schema",
                "index",
                "parent_owner_sha256",
                "original_bindings_manifest_sha256",
                "old_source_manifest_sha256",
                "new_source_manifest_sha256",
                "old_stage_binding_sha256",
                "new_stage_binding_sha256",
                "origin_lease_id",
                "old_lease_id",
                "new_lease_id",
                "old_lease_audit_sha256",
                "new_lease_document_sha256",
                "repair_transition_sha256",
                "transition_document_sha256",
                "transition",
                "coordinate_digest",
                "master_digest",
                "config_sha256",
                "native_binding_sha256",
                "analyzer_sha256",
                "result_root",
                "result_root_sha256",
                "panel_counts_sha256",
                "effective_bindings",
                "no_committed_generation_proven",
                "no_result_proven",
                "recovered_staging_count",
                "science_change",
                "replacement_coordinate_created",
            ),
            "stage repair audit",
        )
        effective_raw = audit["effective_bindings"]
        if not isinstance(effective_raw, Mapping):
            raise EmpiricalArtifactError("stage repair effective bindings are malformed")
        try:
            effective = EmpiricalBindings(**effective_raw)
        except TypeError as exc:
            raise EmpiricalArtifactError("stage repair effective binding schema differs") from exc
        effective.validate()
        stored_transition = audit["transition"]
        if not isinstance(stored_transition, Mapping):
            raise EmpiricalArtifactError("stage repair transition evidence is malformed")
        stored_transition = self._validate_source_repair_transition_shape(stored_transition)
        stored_preserved = stored_transition["preserved"]
        if not isinstance(stored_preserved, Mapping):
            raise EmpiricalArtifactError("stage repair preserved evidence is malformed")
        expected_counts_sha = _sha256(_canonical_json(CONTRACT_PANEL_COUNTS))
        if (
            audit["schema"] != STAGE_REPAIR_AUDIT_SCHEMA
            or audit["index"] != 1
            or audit["parent_owner_sha256"] != self._owner_sha256
            or audit["original_bindings_manifest_sha256"] != self.bindings_sha256
            or audit["old_source_manifest_sha256"]
            != self._original_bindings.source_manifest_sha256
            or audit["old_stage_binding_sha256"]
            != self._original_bindings.lease_binding_sha256
            or audit["new_source_manifest_sha256"] != effective.source_manifest_sha256
            or audit["new_stage_binding_sha256"] != effective.lease_binding_sha256
            or audit["origin_lease_id"] != self._original_bindings.origin_lease_id
            or not isinstance(audit["old_lease_id"], str)
            or not _IDENTIFIER.fullmatch(audit["old_lease_id"])
            or not isinstance(audit["new_lease_id"], str)
            or not _IDENTIFIER.fullmatch(audit["new_lease_id"])
            or audit["old_lease_id"] == audit["new_lease_id"]
            or not isinstance(audit["old_lease_audit_sha256"], str)
            or not _HEX.fullmatch(audit["old_lease_audit_sha256"])
            or not isinstance(audit["new_lease_document_sha256"], str)
            or not _HEX.fullmatch(audit["new_lease_document_sha256"])
            or audit["coordinate_digest"] != self._original_bindings.coordinate_digest
            or audit["master_digest"] != self._original_bindings.master_digest
            or audit["config_sha256"] != self._original_bindings.config_sha256
            or audit["native_binding_sha256"] != self._original_bindings.native_binding_sha256
            or audit["panel_counts_sha256"] != expected_counts_sha
            or not isinstance(audit["analyzer_sha256"], str)
            or not _HEX.fullmatch(audit["analyzer_sha256"])
            or not isinstance(audit["result_root"], str)
            or audit["result_root_sha256"]
            != _sha256(str(audit["result_root"]).encode("utf-8"))
            or audit["transition_document_sha256"] != audit["repair_transition_sha256"]
            or stored_transition["repair_transition_sha256"]
            != audit["repair_transition_sha256"]
            or stored_preserved.get("analyzer_sha256") != audit["analyzer_sha256"]
            or stored_preserved.get("result_root") != audit["result_root"]
            or _sha256(_canonical_json(stored_preserved.get("counts")))
            != audit["panel_counts_sha256"]
            or not isinstance(audit["repair_transition_sha256"], str)
            or not _HEX.fullmatch(audit["repair_transition_sha256"])
            or audit["no_committed_generation_proven"] is not True
            or audit["no_result_proven"] is not True
            or audit["recovered_staging_count"] != 1
            or audit["science_change"] is not False
            or audit["replacement_coordinate_created"] is not False
        ):
            raise EmpiricalArtifactError("stage repair audit binding differs")
        for name in (
            "config_sha256",
            "native_binding_sha256",
            "coordinate_digest",
            "master_digest",
            "origin_lease_id",
            "lease_id",
        ):
            if getattr(effective, name) != getattr(self._original_bindings, name):
                raise EmpiricalArtifactError(f"stage repair changes protected binding: {name}")
        if (
            effective.source_manifest_sha256 == self._original_bindings.source_manifest_sha256
            or effective.lease_binding_sha256 == self._original_bindings.lease_binding_sha256
        ):
            raise EmpiricalArtifactError("stage repair does not establish a new source/stage")
        self.bindings = effective
        return audit

    @staticmethod
    def _validate_source_repair_transition_shape(
        transition: Mapping[str, object],
    ) -> Mapping[str, object]:
        required = {
            "schema",
            "fixture_only",
            "non_scientific",
            "reason",
            "direction_id",
            "science_revision",
            "empirical_object",
            "origin_lease_id",
            "original",
            "repaired",
            "run_identity",
            "failed_terminal",
            "source_deltas",
            "preserved",
            "science_change",
            "coordinate_materialization_authorized",
            "partial_interpretation_permitted",
            "repair_transition_sha256",
        }
        if not isinstance(transition, Mapping) or set(transition) != required:
            raise EmpiricalArtifactError("source repair transition schema differs")
        body = {key: transition[key] for key in required - {"repair_transition_sha256"}}
        if (
            transition["schema"]
            != SOURCE_REPAIR_TRANSITION_SCHEMA
            or transition["reason"] != SOURCE_REPAIR_REASON
            or transition["direction_id"] != DIRECTION_ID
            or transition["science_revision"] != SCIENCE_REVISION
            or transition["empirical_object"] != EMPIRICAL_OBJECT
            or transition["science_change"] is not False
            or transition["coordinate_materialization_authorized"] is not False
            or transition["partial_interpretation_permitted"] is not False
            or transition["repair_transition_sha256"] != _sha256(_canonical_json(body))
        ):
            raise EmpiricalArtifactError("source repair transition identity or digest differs")
        return transition

    @classmethod
    def apply_source_repair(
        cls,
        root: str | os.PathLike[str],
        original_bindings: EmpiricalBindings,
        repaired_bindings: EmpiricalBindings,
        *,
        repair_transition: Mapping[str, object],
        permit: ActiveLeasePermit,
        now: datetime,
        lease_document_sha256: str,
        owner_token: str,
        process_alive_probe: Callable[[int], bool] | None = None,
    ) -> "AtomicEmpiricalFrontier":
        """Append the sole proven pre-generation source/stage repair bridge.

        The contract owns validation of the source-bearing transition and its
        replacement permit.  This method additionally proves that the local
        frontier is still at the exact owner-bound, uncommitted generation-0
        crash point before recording the new effective source/stage binding.
        """

        original_bindings.validate()
        repaired_bindings.validate()
        transition = cls._validate_source_repair_transition_shape(repair_transition)
        transition_sha = transition["repair_transition_sha256"]
        if not isinstance(transition_sha, str) or not _HEX.fullmatch(transition_sha):
            raise EmpiricalArtifactError("source repair transition digest is malformed")
        if not _HEX.fullmatch(lease_document_sha256):
            raise EmpiricalArtifactError("lease document digest is malformed")
        for name in (
            "config_sha256",
            "native_binding_sha256",
            "coordinate_digest",
            "master_digest",
            "origin_lease_id",
            "lease_id",
        ):
            if getattr(repaired_bindings, name) != getattr(original_bindings, name):
                raise EmpiricalArtifactError(f"source repair changes protected binding: {name}")
        if (
            repaired_bindings.source_manifest_sha256
            == original_bindings.source_manifest_sha256
            or repaired_bindings.lease_binding_sha256
            == original_bindings.lease_binding_sha256
        ):
            raise EmpiricalArtifactError("source repair does not establish a new source/stage")

        root_path = Path(root)
        manifest = _read_canonical_json(root_path / "bindings.json")
        raw_original = manifest.get("bindings")
        if raw_original != asdict(original_bindings):
            raise EmpiricalArtifactError("source repair original frontier binding differs")
        owner_sha = manifest.get("parent_owner_sha256")
        if owner_sha != _owner_digest(owner_token):
            raise EmpiricalArtifactError("source repair parent owner differs")
        frontier = cls(root_path, original_bindings, str(owner_sha))
        frontier._recover_stale_lock(
            owner_token, process_alive_probe=process_alive_probe
        )
        frontier._validate_bindings_manifest()
        if (root_path / "stage_repairs").exists():
            raise EmpiricalArtifactError("source repair is duplicate")
        if {path.name for path in root_path.iterdir()} != {
            "bindings.json",
            "blocks",
            "lease_audits",
        }:
            raise EmpiricalArtifactError("source repair frontier inventory is incomplete or extra")
        audits = frontier._validate_lease_audits()
        if len(audits) != 1:
            raise EmpiricalArtifactError("source repair requires the sole origin lease audit")
        old_audit_sha, old_audit = audits[0]

        original = transition.get("original")
        repaired = transition.get("repaired")
        preserved = transition.get("preserved")
        if not all(isinstance(item, Mapping) for item in (original, repaired, preserved)):
            raise EmpiricalArtifactError("source repair transition locators are malformed")
        assert isinstance(original, Mapping)
        assert isinstance(repaired, Mapping)
        assert isinstance(preserved, Mapping)
        _exact_mapping(
            original,
            (
                "certificate_sha256",
                "binding_sha256",
                "request_sha256",
                "source_set_sha256",
                "stage_binding_sha256",
                "lease_id",
            ),
            "source repair original locator",
        )
        _exact_mapping(
            repaired,
            (
                "certificate_sha256",
                "binding_sha256",
                "request_sha256",
                "source_set_sha256",
                "stage_binding_sha256",
            ),
            "source repair repaired locator",
        )
        _exact_mapping(
            preserved,
            (
                "coordinate_binding_sha256",
                "master_digest",
                "run_block_roots",
                "result_root",
                "resource_ceiling",
                "config_sha256",
                "native_identity_sha256",
                "analyzer_sha256",
                "counts",
            ),
            "source repair preserved evidence",
        )
        if (
            transition["origin_lease_id"] != original_bindings.origin_lease_id
            or original["lease_id"] != old_audit["lease_id"]
            or original["source_set_sha256"]
            != original_bindings.source_manifest_sha256
            or original["stage_binding_sha256"]
            != original_bindings.stage_binding_sha256
            or repaired["source_set_sha256"]
            != repaired_bindings.source_manifest_sha256
            or repaired["stage_binding_sha256"]
            != repaired_bindings.stage_binding_sha256
            or preserved["coordinate_binding_sha256"]
            != original_bindings.coordinate_digest
            or preserved["master_digest"] != original_bindings.master_digest
            or preserved["config_sha256"] != original_bindings.config_sha256
            or preserved["native_identity_sha256"]
            != original_bindings.native_binding_sha256
            or preserved["counts"] != CONTRACT_PANEL_COUNTS
            or not isinstance(preserved["analyzer_sha256"], str)
            or not _HEX.fullmatch(str(preserved["analyzer_sha256"]))
            or not isinstance(preserved["result_root"], str)
        ):
            raise EmpiricalArtifactError("source repair transition changes protected evidence")
        run_block_roots = preserved["run_block_roots"]
        if (
            not isinstance(run_block_roots, list)
            or len(run_block_roots) != BLOCK_COUNT
        ):
            raise EmpiricalArtifactError("source repair run-block roots are malformed")
        root_digests: list[str] = []
        for index, row in enumerate(run_block_roots):
            if (
                not isinstance(row, Mapping)
                or set(row) != {"block_index", "root_digest"}
                or row["block_index"] != index
                or not isinstance(row["root_digest"], str)
                or not _HEX.fullmatch(row["root_digest"])
            ):
                raise EmpiricalArtifactError("source repair run-block roots are malformed")
            root_digests.append(row["root_digest"])
        if len(set(root_digests)) != BLOCK_COUNT:
            raise EmpiricalArtifactError("source repair run-block roots are not distinct")

        lease_id = _validate_active_permit(permit, now=now, bindings=repaired_bindings)
        if (
            getattr(permit, "repair_transition_sha256", None) != transition_sha
            or getattr(permit, "replacement_index", None) != 1
            or getattr(permit, "predecessor_lease_id", None) != old_audit["lease_id"]
            or tuple(getattr(permit, "lease_lineage", ()))
            != (old_audit["lease_id"], lease_id)
            or repaired.get("certificate_sha256")
            != getattr(permit, "preactivity_certificate_sha256", None)
            or repaired.get("binding_sha256")
            != getattr(permit, "accepted_binding_sha256", None)
        ):
            raise EmpiricalArtifactError("source repair replacement permit bridge differs")
        permit_paths = getattr(permit, "paths", None)
        if (
            not isinstance(permit_paths, Mapping)
            or permit_paths.get("result_root") != preserved["result_root"]
            or "frontier_root" not in permit_paths
            or Path(str(permit_paths["frontier_root"])).resolve() != root_path.resolve()
        ):
            raise EmpiricalArtifactError("source repair replacement path binding differs")

        if (root_path / "published").exists():
            raise EmpiricalArtifactError("source repair cannot migrate a published result")
        staging_rows: list[tuple[Path, Path, int]] = []
        blocks_root = root_path / "blocks"
        if not blocks_root.is_dir() or blocks_root.is_symlink():
            raise EmpiricalArtifactError("source repair blocks root is invalid")
        for block_root in blocks_root.iterdir():
            if not _BLOCK_NAME.fullmatch(block_root.name) or not block_root.is_dir() or block_root.is_symlink():
                raise EmpiricalArtifactError("source repair block inventory is ambiguous")
            block_index = int(block_root.name[-2:])
            entries = {path.name for path in block_root.iterdir()}
            if entries != {"resume", "data", ".staging"}:
                raise EmpiricalArtifactError("source repair block inventory is ambiguous")
            if (block_root / "COMPLETE.json").exists():
                raise EmpiricalArtifactError("source repair cannot migrate a committed block")
            resume_root = block_root / "resume"
            if not resume_root.is_dir() or resume_root.is_symlink() or any(resume_root.iterdir()):
                raise EmpiricalArtifactError("source repair cannot migrate a committed generation")
            data_root = block_root / "data"
            if not data_root.is_dir() or data_root.is_symlink():
                raise EmpiricalArtifactError("source repair block data root is invalid")
            staging_parent = block_root / ".staging"
            if staging_parent.exists():
                if not staging_parent.is_dir() or staging_parent.is_symlink():
                    raise EmpiricalArtifactError("source repair staging parent is ambiguous")
                roots = list(staging_parent.iterdir())
                if len(roots) != 1:
                    raise EmpiricalArtifactError("source repair staging multiplicity is ambiguous")
                staging_rows.append((staging_parent, roots[0], block_index))
        if len(staging_rows) != 1:
            raise EmpiricalArtifactError("source repair requires exactly one failed generation staging")

        staging_parent, staging_root, block_index = staging_rows[0]
        staging_manifest, refs = frontier._load_staged_generation(staging_root, block_index)
        if (
            staging_manifest["generation"] != 0
            or (staging_root / "generation.json").exists()
            or any(
                root_path.joinpath(*PurePosixPath(ref.path).parts).exists()
                for ref in refs.values()
            )
            or any((staging_parent.parent / "data").iterdir())
        ):
            raise EmpiricalArtifactError("source repair staging is committed or ambiguous")

        with frontier._exclusive_commit(owner_token):
            shutil.rmtree(staging_root)
            staging_parent.rmdir()
            shutil.rmtree(staging_parent.parent)
            repair_root = root_path / "stage_repairs"
            repair_root.mkdir()
            repair_packet = {
                "schema": STAGE_REPAIR_AUDIT_SCHEMA,
                "index": 1,
                "parent_owner_sha256": frontier._owner_sha256,
                "original_bindings_manifest_sha256": frontier.bindings_sha256,
                "old_source_manifest_sha256": original_bindings.source_manifest_sha256,
                "new_source_manifest_sha256": repaired_bindings.source_manifest_sha256,
                "old_stage_binding_sha256": original_bindings.stage_binding_sha256,
                "new_stage_binding_sha256": repaired_bindings.stage_binding_sha256,
                "origin_lease_id": original_bindings.origin_lease_id,
                "old_lease_id": old_audit["lease_id"],
                "new_lease_id": lease_id,
                "old_lease_audit_sha256": old_audit_sha,
                "new_lease_document_sha256": lease_document_sha256,
                "repair_transition_sha256": transition_sha,
                "transition_document_sha256": transition_sha,
                "transition": dict(transition),
                "coordinate_digest": original_bindings.coordinate_digest,
                "master_digest": original_bindings.master_digest,
                "config_sha256": original_bindings.config_sha256,
                "native_binding_sha256": original_bindings.native_binding_sha256,
                "analyzer_sha256": preserved["analyzer_sha256"],
                "result_root": preserved["result_root"],
                "result_root_sha256": _sha256(str(preserved["result_root"]).encode("utf-8")),
                "panel_counts_sha256": _sha256(_canonical_json(CONTRACT_PANEL_COUNTS)),
                "effective_bindings": asdict(repaired_bindings),
                "no_committed_generation_proven": True,
                "no_result_proven": True,
                "recovered_staging_count": 1,
                "science_change": False,
                "replacement_coordinate_created": False,
            }
            _write_exclusive(
                repair_root / "repair_000001.json", _canonical_json(repair_packet)
            )
            lease_packet = {
                "schema": LEASE_AUDIT_SCHEMA,
                "index": 1,
                "lease_id": lease_id,
                "lease_document_sha256": lease_document_sha256,
                "origin_lease_id": repaired_bindings.origin_lease_id,
                "stage_binding_sha256": repaired_bindings.stage_binding_sha256,
                "source_manifest_sha256": repaired_bindings.source_manifest_sha256,
                "config_sha256": repaired_bindings.config_sha256,
                "native_binding_sha256": repaired_bindings.native_binding_sha256,
                "coordinate_digest": repaired_bindings.coordinate_digest,
                "master_digest": repaired_bindings.master_digest,
                "predecessor_lease_id": old_audit["lease_id"],
                "previous_audit_sha256": old_audit_sha,
                "validated_at": now.isoformat(),
                "active_validated": True,
                "replacement_coordinate_created": False,
                "repair_transition_sha256": transition_sha,
            }
            lease_payload = _canonical_json(lease_packet)
            _write_exclusive(root_path / "lease_audits" / "lease_000001.json", lease_payload)

        frontier.bindings = repaired_bindings
        frontier._current_lease_audit_sha256 = _sha256(lease_payload)
        frontier.validate(permit_published=False)
        return frontier

    def _block_root(self, block_index: int) -> Path:
        return self.root / "blocks" / _block_name(block_index)

    def _load_staged_generation(
        self, staging_root: Path, block_index: int
    ) -> tuple[Mapping[str, Any], dict[str, ArtifactRef]]:
        match = _STAGING_NAME.fullmatch(staging_root.name)
        if not match or not staging_root.is_dir() or staging_root.is_symlink():
            raise EmpiricalArtifactError("generation staging directory provenance is malformed")
        generation = int(match.group(1))
        token = match.group(2)
        staging_entries = {path.name for path in staging_root.iterdir()}
        if staging_entries not in (
            {"payloads", "manifest.json"},
            {"payloads", "manifest.json", "generation.json"},
        ):
            raise EmpiricalArtifactError("generation staging inventory is incomplete or extra")
        payload_root = staging_root / "payloads"
        if not payload_root.is_dir() or payload_root.is_symlink():
            raise EmpiricalArtifactError("generation staging payload directory is invalid")
        manifest = _read_canonical_json(staging_root / "manifest.json")
        _exact_mapping(
            manifest,
            (
                "schema",
                "science_revision",
                "empirical_object",
                "block_index",
                "generation",
                "token",
                "parent_owner_sha256",
                "bindings_sha256",
                "lease_audit_sha256",
                "payloads",
                "publication_committed",
            ),
            "generation staging manifest",
        )
        rows = manifest["payloads"]
        if (
            manifest["schema"] != STAGING_SCHEMA
            or manifest["science_revision"] != SCIENCE_REVISION
            or manifest["empirical_object"] != EMPIRICAL_OBJECT
            or manifest["block_index"] != block_index
            or manifest["generation"] != generation
            or manifest["token"] != token
            or manifest["parent_owner_sha256"] != self._owner_sha256
            or manifest["bindings_sha256"] != self.effective_bindings_sha256
            or manifest["lease_audit_sha256"]
            not in {digest for digest, _ in self._validate_lease_audits()}
            or manifest["publication_committed"] is not False
            or not isinstance(rows, list)
            or not rows
        ):
            raise EmpiricalArtifactError("generation staging provenance differs")
        refs: dict[str, ArtifactRef] = {}
        seen_paths: set[str] = set()
        actual_staged = {path.name for path in payload_root.iterdir()}
        for row in rows:
            item = _exact_mapping(
                row,
                ("name", "staged_path", "final_path", "sha256", "size_bytes"),
                "generation staging payload",
            )
            name = item["name"]
            if not isinstance(name, str) or not _PAYLOAD_NAME.fullmatch(name) or name in refs:
                raise EmpiricalArtifactError("generation staging payload name differs")
            expected_staged = f"payloads/{name}"
            expected_final = (
                PurePosixPath("blocks")
                / _block_name(block_index)
                / "data"
                / f"g{generation:06d}.{name}"
            ).as_posix()
            if (
                item["staged_path"] != expected_staged
                or item["final_path"] != expected_final
                or not isinstance(item["sha256"], str)
                or not _HEX.fullmatch(item["sha256"])
                or isinstance(item["size_bytes"], bool)
                or not isinstance(item["size_bytes"], int)
                or item["size_bytes"] < 0
                or expected_final in seen_paths
            ):
                raise EmpiricalArtifactError("generation staging payload provenance differs")
            staged_path = staging_root / "payloads" / name
            final_path = self.root.joinpath(*PurePosixPath(expected_final).parts)
            staged_exists = staged_path.is_file() and not staged_path.is_symlink()
            final_exists = final_path.is_file() and not final_path.is_symlink()
            if staged_exists == final_exists:
                raise EmpiricalArtifactError("staged payload publication state is ambiguous")
            target = staged_path if staged_exists else final_path
            payload = _read_regular_bytes(target)
            if len(payload) != item["size_bytes"] or _sha256(payload) != item["sha256"]:
                raise EmpiricalArtifactError("staged payload digest or size differs")
            refs[name] = ArtifactRef(expected_final, str(item["sha256"]), int(item["size_bytes"]))
            seen_paths.add(expected_final)
        expected_staged_names = {
            name for name, ref in refs.items() if (staging_root / "payloads" / name).exists()
        }
        if actual_staged != expected_staged_names:
            raise EmpiricalArtifactError("generation staging contains an extra payload")
        generation_path = staging_root / "generation.json"
        if generation_path.exists():
            packet = _read_canonical_json(generation_path)
            _exact_mapping(
                packet,
                (
                    "schema",
                    "science_revision",
                    "empirical_object",
                    "block_index",
                    "generation",
                    "previous_generation_sha256",
                    "bindings_sha256",
                    "lease_audit_sha256",
                    "state",
                    "blinded",
                    "partial_interpretation_permitted",
                ),
                "staged generation packet",
            )
            state = _state_from_mapping(packet["state"])
            if (
                packet["schema"] != RESUME_SCHEMA
                or packet["science_revision"] != SCIENCE_REVISION
                or packet["empirical_object"] != EMPIRICAL_OBJECT
                or packet["block_index"] != block_index
                or packet["generation"] != generation
                or packet["bindings_sha256"] != self.effective_bindings_sha256
                or packet["lease_audit_sha256"] != manifest["lease_audit_sha256"]
                or packet["blinded"] is not True
                or packet["partial_interpretation_permitted"] is not False
                or {ref.path for ref in _state_artifact_refs(state)}
                != {ref.path for ref in refs.values()}
            ):
                raise EmpiricalArtifactError("staged generation packet provenance differs")
        return manifest, refs

    def stage_generation_payloads(
        self,
        block_index: int,
        payloads: Mapping[str, bytes],
        *,
        owner_token: str,
        failure_hook: Callable[[str], None] | None = None,
    ) -> StagedGeneration:
        """Durably stage one next generation without publishing its payloads."""

        if not isinstance(payloads, Mapping) or not payloads:
            raise EmpiricalArtifactError("generation payload inventory is empty")
        with self._exclusive_commit(owner_token):
            block_root = self._block_root(block_index)
            if (block_root / "COMPLETE.json").exists():
                raise EmpiricalArtifactError("sealed block cannot stage another generation")
            block_root.mkdir(parents=True, exist_ok=True)
            (block_root / "resume").mkdir(exist_ok=True)
            (block_root / "data").mkdir(exist_ok=True)
            staging_parent = block_root / ".staging"
            staging_parent.mkdir(exist_ok=True)
            generations, _ = self._validate_chain(block_index, require_data_exact=False)
            if any(staging_parent.iterdir()):
                raise EmpiricalArtifactError("another staged generation requires recovery")
            generation = len(generations)
            token = uuid.uuid4().hex
            staging_root = staging_parent / f"generation_{generation:06d}-{token}"
            (staging_root / "payloads").mkdir(parents=True)
            rows: list[dict[str, object]] = []
            for name in sorted(payloads):
                payload = payloads[name]
                if not isinstance(name, str) or not _PAYLOAD_NAME.fullmatch(name):
                    raise EmpiricalArtifactError("generation payload name is malformed")
                if not isinstance(payload, bytes):
                    raise EmpiricalArtifactError("generation payload must be bytes")
                _write_exclusive(staging_root / "payloads" / name, payload)
                rows.append(
                    {
                        "name": name,
                        "staged_path": f"payloads/{name}",
                        "final_path": (
                            PurePosixPath("blocks")
                            / _block_name(block_index)
                            / "data"
                            / f"g{generation:06d}.{name}"
                        ).as_posix(),
                        "sha256": _sha256(payload),
                        "size_bytes": len(payload),
                    }
                )
            manifest = {
                "schema": STAGING_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_index": block_index,
                "generation": generation,
                "token": token,
                "parent_owner_sha256": self._owner_sha256,
                "bindings_sha256": self.effective_bindings_sha256,
                "lease_audit_sha256": self._current_lease_audit_sha256,
                "payloads": rows,
                "publication_committed": False,
            }
            _write_exclusive(staging_root / "manifest.json", _canonical_json(manifest))
            _, refs = self._load_staged_generation(staging_root, block_index)
            staged = StagedGeneration(block_index, generation, token, refs)
            if failure_hook is not None:
                failure_hook("after_payload_staging")
            return staged

    def commit_staged_resume(
        self,
        staged: StagedGeneration,
        state: ResumeState,
        *,
        owner_token: str,
        failure_hook: Callable[[str], None] | None = None,
    ) -> str:
        """Atomically publish staged payloads and then append their generation."""

        if not isinstance(staged, StagedGeneration):
            raise EmpiricalArtifactError("staged generation handle is malformed")
        with self._exclusive_commit(owner_token):
            block_index = staged.block_index
            block_root = self._block_root(block_index)
            generations, _ = self._validate_chain(block_index, require_data_exact=False)
            if staged.generation != len(generations):
                raise EmpiricalArtifactError("staged generation is not the next committed generation")
            staging_root = (
                block_root
                / ".staging"
                / f"generation_{staged.generation:06d}-{staged.token}"
            )
            _, refs = self._load_staged_generation(staging_root, block_index)
            if dict(refs) != dict(staged.refs):
                raise EmpiricalArtifactError("staged generation handle differs from durable provenance")
            state_refs = {ref.path: ref for ref in _state_artifact_refs(state)}
            staged_refs = {ref.path: ref for ref in refs.values()}
            if state_refs != staged_refs:
                raise EmpiricalArtifactError("resume state does not bind every exact staged payload")
            for name, ref in refs.items():
                source = staging_root / "payloads" / name
                target = self.root.joinpath(*PurePosixPath(ref.path).parts)
                if target.exists():
                    raise EmpiricalArtifactError("staged final payload already exists")
                os.rename(source, target)
            if failure_hook is not None:
                failure_hook("after_payload_publication")
            _validate_state(self.root, block_index, state)
            if generations:
                _validate_monotonic(generations[-1][1], state)
            previous = generations[-1][0] if generations else None
            packet = {
                "schema": RESUME_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_index": block_index,
                "generation": staged.generation,
                "previous_generation_sha256": previous,
                "bindings_sha256": self.effective_bindings_sha256,
                "lease_audit_sha256": self._current_lease_audit_sha256,
                "state": _state_to_mapping(state),
                "blinded": True,
                "partial_interpretation_permitted": False,
            }
            target = block_root / "resume" / f"generation_{staged.generation:06d}.json"
            payload = _canonical_json(packet)
            staged_generation_path = staging_root / "generation.json"
            _write_exclusive(staged_generation_path, payload)
            if target.exists():
                raise EmpiricalArtifactError("generation publication target already exists")
            os.rename(staged_generation_path, target)
            if failure_hook is not None:
                failure_hook("after_generation_commit")
            shutil.rmtree(staging_root)
            staging_parent = staging_root.parent
            if not any(staging_parent.iterdir()):
                staging_parent.rmdir()
            self._validate_chain(block_index, require_data_exact=True)
            return _sha256(payload)

    def _recover_generation_orphans(self, owner_token: str) -> None:
        """Recover only owner-bound staging left by a proven interrupted commit."""

        with self._exclusive_commit(owner_token):
            blocks_root = self.root / "blocks"
            if not blocks_root.is_dir() or blocks_root.is_symlink():
                raise EmpiricalArtifactError("blocks root is invalid during recovery")
            for block_root in sorted(blocks_root.iterdir(), key=lambda item: item.name):
                match = _BLOCK_NAME.fullmatch(block_root.name)
                if not match or not block_root.is_dir() or block_root.is_symlink():
                    raise EmpiricalArtifactError("recovery found an ambiguous block entry")
                block_index = int(block_root.name[-2:])
                entries = {path.name for path in block_root.iterdir()}
                if not entries <= {"resume", "data", ".staging", "COMPLETE.json"}:
                    raise EmpiricalArtifactError("recovery found an ambiguous block artifact")
                if not {"resume", "data"} <= entries:
                    raise EmpiricalArtifactError("recovery block lacks deterministic resume/data roots")
                generations, referenced = self._validate_chain(
                    block_index, require_data_exact=False
                )
                staging_parent = block_root / ".staging"
                staging_roots: list[Path] = []
                if staging_parent.exists():
                    if not staging_parent.is_dir() or staging_parent.is_symlink():
                        raise EmpiricalArtifactError("generation staging parent is ambiguous")
                    staging_roots = list(staging_parent.iterdir())
                    if len(staging_roots) != 1:
                        raise EmpiricalArtifactError("generation staging multiplicity is ambiguous")
                if staging_roots:
                    staging_root = staging_roots[0]
                    manifest, refs = self._load_staged_generation(staging_root, block_index)
                    generation = int(manifest["generation"])
                    final_paths = {ref.path for ref in refs.values()}
                    if generation > len(generations):
                        raise EmpiricalArtifactError("staged generation skips the committed frontier")
                    if generation < len(generations):
                        if (staging_root / "generation.json").exists():
                            raise EmpiricalArtifactError(
                                "committed generation retains an ambiguous staged packet"
                            )
                        committed_paths = {
                            ref.path for ref in _state_artifact_refs(generations[generation][1])
                        }
                        if committed_paths != final_paths or not final_paths <= referenced:
                            raise EmpiricalArtifactError(
                                "staged payload overlaps a committed generation ambiguously"
                            )
                        shutil.rmtree(staging_root)
                    else:
                        staged_packet_path = staging_root / "generation.json"
                        if staged_packet_path.exists():
                            staged_packet = _read_canonical_json(staged_packet_path)
                            expected_previous = generations[-1][0] if generations else None
                            if staged_packet["previous_generation_sha256"] != expected_previous:
                                raise EmpiricalArtifactError(
                                    "staged generation predecessor digest differs"
                                )
                        if final_paths & referenced:
                            raise EmpiricalArtifactError(
                                "uncommitted staging references an earlier committed payload"
                            )
                        for ref in refs.values():
                            final_path = self.root.joinpath(*PurePosixPath(ref.path).parts)
                            if final_path.exists():
                                payload = _read_regular_bytes(final_path)
                                if len(payload) != ref.size_bytes or _sha256(payload) != ref.sha256:
                                    raise EmpiricalArtifactError(
                                        "orphan final payload changed after staging"
                                    )
                                final_path.unlink()
                        shutil.rmtree(staging_root)
                    if not any(staging_parent.iterdir()):
                        staging_parent.rmdir()

                data_root = block_root / "data"
                actual = {
                    path.relative_to(self.root).as_posix()
                    for path in data_root.rglob("*")
                    if path.is_file() and not path.is_symlink()
                }
                if any(path.is_symlink() for path in data_root.rglob("*")):
                    raise EmpiricalArtifactError("recovery refuses symlinked payloads")
                if actual != referenced:
                    raise EmpiricalArtifactError(
                        "unreferenced payload lacks exact owner-bound staging provenance"
                    )
                if not generations and not (block_root / "COMPLETE.json").exists():
                    if any(data_root.iterdir()) or any((block_root / "resume").iterdir()):
                        raise EmpiricalArtifactError("empty recovery block retains ambiguous artifacts")
                    shutil.rmtree(block_root)

    def commit_resume(
        self,
        block_index: int,
        state: ResumeState,
        *,
        owner_token: str,
    ) -> str:
        """Append one fully bound mechanical resume generation."""

        with self._exclusive_commit(owner_token):
            block_root = self._block_root(block_index)
            complete_marker = block_root / "COMPLETE.json"
            if complete_marker.exists():
                raise EmpiricalArtifactError("sealed block cannot receive another generation")
            block_root.mkdir(parents=True, exist_ok=True)
            (block_root / "resume").mkdir(exist_ok=True)
            (block_root / "data").mkdir(exist_ok=True)
            generations, referenced = self._validate_chain(block_index, require_data_exact=False)
            _validate_state(self.root, block_index, state)
            if generations:
                _validate_monotonic(generations[-1][1], state)
            generation = len(generations)
            previous = generations[-1][0] if generations else None
            packet = {
                "schema": RESUME_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_index": block_index,
                "generation": generation,
                "previous_generation_sha256": previous,
                "bindings_sha256": self.effective_bindings_sha256,
                "lease_audit_sha256": self._current_lease_audit_sha256,
                "state": _state_to_mapping(state),
                "blinded": True,
                "partial_interpretation_permitted": False,
            }
            target = block_root / "resume" / f"generation_{generation:06d}.json"
            payload = _canonical_json(packet)
            _write_exclusive(target, payload)
            self._validate_chain(block_index, require_data_exact=True)
            return _sha256(payload)

    def seal_block(self, block_index: int, *, owner_token: str) -> str:
        """Seal one block only after every exact learned/scripted component."""

        with self._exclusive_commit(owner_token):
            block_root = self._block_root(block_index)
            generations, _ = self._validate_chain(block_index, require_data_exact=True)
            if not generations or not _is_complete_state(generations[-1][1]):
                raise EmpiricalArtifactError("run block is not the exact complete r04 block")
            marker = block_root / "COMPLETE.json"
            if marker.exists():
                raise EmpiricalArtifactError("run block is already sealed")
            packet = {
                "schema": BLOCK_COMPLETE_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_index": block_index,
                "bindings_sha256": self.effective_bindings_sha256,
                "final_generation": len(generations) - 1,
                "final_generation_sha256": generations[-1][0],
                "updates_per_arm": UPDATE_COUNT,
                "learned_arms": list(LEARNED_ARMS),
                "heldout_cells": list(HELDOUT_CELLS),
                "heldout_episodes_per_cell": HELDOUT_EPISODES_PER_CELL,
                "scripted_panels": list(SCRIPTED_PANELS),
                "counts": dict(BLOCK_COUNTS),
                "complete": True,
                "partial_interpretation_permitted": False,
            }
            payload = _canonical_json(packet)
            _write_exclusive(marker, payload)
            self._validate_block(block_index)
            return _sha256(payload)

    def publish_complete_panel(
        self,
        *,
        branch: str,
        analyzer_payload: bytes,
        result_payload: bytes,
        owner_token: str,
    ) -> Path:
        """Atomically publish analyzer/result bytes after all twenty blocks."""

        if branch not in BRANCHES:
            raise EmpiricalArtifactError("result branch is not in the frozen twelve-branch map")
        if not isinstance(analyzer_payload, bytes) or not analyzer_payload:
            raise EmpiricalArtifactError("analyzer payload must be nonempty bytes")
        if not isinstance(result_payload, bytes) or not result_payload:
            raise EmpiricalArtifactError("result payload must be nonempty bytes")
        _validate_publication_payloads(analyzer_payload, result_payload, branch)
        with self._exclusive_commit(owner_token):
            self.validate(
                require_complete_blocks=True,
                permit_published=False,
                _permit_active_lock=True,
            )
            published = self.root / "published"
            if published.exists():
                raise EmpiricalArtifactError("complete panel is already published")
            staging = self.root / f".published.tmp-{uuid.uuid4().hex}"
            try:
                staging.mkdir()
                _write_exclusive(staging / "analyzer.json", analyzer_payload)
                _write_exclusive(staging / "result.json", result_payload)
                block_digests = {
                    _block_name(index): _sha256(
                        _read_regular_bytes(self._block_root(index) / "COMPLETE.json")
                    )
                    for index in range(BLOCK_COUNT)
                }
                manifest = {
                    "schema": PANEL_COMPLETE_SCHEMA,
                    "science_revision": SCIENCE_REVISION,
                    "empirical_object": EMPIRICAL_OBJECT,
                    "bindings_sha256": self.effective_bindings_sha256,
                    "lease_audit_sha256": self._current_lease_audit_sha256,
                    "block_count": BLOCK_COUNT,
                    "block_complete_sha256": block_digests,
                    "learned_arms": list(LEARNED_ARMS),
                    "scripted_panels": list(SCRIPTED_PANELS),
                    "counts": dict(PANEL_COUNTS),
                    "registered_tail_count": REGISTERED_TAIL_COUNT,
                    "registered_tail_names": list(REGISTERED_TAIL_NAMES),
                    "branch": branch,
                    "analyzer_sha256": _sha256(analyzer_payload),
                    "result_sha256": _sha256(result_payload),
                    "complete": True,
                    "partial_interpretation_permitted": False,
                }
                manifest_payload = _canonical_json(manifest)
                _write_exclusive(staging / "manifest.json", manifest_payload)
                _write_exclusive(
                    staging / "COMPLETE",
                    _canonical_json(
                        {
                            "schema": PANEL_COMPLETE_SCHEMA,
                            "manifest_sha256": _sha256(manifest_payload),
                            "complete": True,
                        }
                    ),
                )
                os.rename(staging, published)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
            self.validate(
                require_complete_blocks=True,
                permit_published=True,
                _permit_active_lock=True,
            )
            return published

    def _validate_chain(
        self, block_index: int, *, require_data_exact: bool
    ) -> tuple[list[tuple[str, ResumeState]], set[str]]:
        block_root = self._block_root(block_index)
        resume_root = block_root / "resume"
        data_root = block_root / "data"
        if not resume_root.is_dir() or resume_root.is_symlink():
            raise EmpiricalArtifactError("run block resume directory is missing")
        if not data_root.is_dir() or data_root.is_symlink():
            raise EmpiricalArtifactError("run block data directory is missing")
        entries = sorted(resume_root.iterdir(), key=lambda item: item.name)
        generations: list[tuple[str, ResumeState]] = []
        referenced: set[str] = set()
        previous: str | None = None
        previous_state: ResumeState | None = None
        for expected_generation, path in enumerate(entries):
            match = _GENERATION_NAME.fullmatch(path.name)
            if not match or int(match.group(1)) != expected_generation:
                raise EmpiricalArtifactError("resume generation inventory is incomplete or extra")
            packet = _read_canonical_json(path)
            _exact_mapping(
                packet,
                (
                    "schema",
                    "science_revision",
                    "empirical_object",
                    "block_index",
                    "generation",
                    "previous_generation_sha256",
                    "bindings_sha256",
                    "lease_audit_sha256",
                    "state",
                    "blinded",
                    "partial_interpretation_permitted",
                ),
                "resume generation",
            )
            if (
                packet["schema"] != RESUME_SCHEMA
                or packet["science_revision"] != SCIENCE_REVISION
                or packet["empirical_object"] != EMPIRICAL_OBJECT
                or packet["block_index"] != block_index
                or packet["generation"] != expected_generation
                or packet["previous_generation_sha256"] != previous
                or packet["bindings_sha256"] != self.effective_bindings_sha256
                or packet["lease_audit_sha256"]
                not in {digest for digest, _ in self._validate_lease_audits()}
                or packet["blinded"] is not True
                or packet["partial_interpretation_permitted"] is not False
            ):
                raise EmpiricalArtifactError("resume generation identity or digest chain differs")
            state = _state_from_mapping(packet["state"])
            referenced.update(_validate_state(self.root, block_index, state))
            if previous_state is not None:
                _validate_monotonic(previous_state, state)
            payload = _read_regular_bytes(path)
            previous = _sha256(payload)
            previous_state = state
            generations.append((previous, state))
        if require_data_exact:
            actual: set[str] = set()
            actual_directories: set[str] = set()
            for path in data_root.rglob("*"):
                if path.is_symlink():
                    raise EmpiricalArtifactError("symlink is forbidden in run-block data")
                if path.is_file():
                    actual.add(path.relative_to(self.root).as_posix())
                elif path.is_dir():
                    actual_directories.add(path.relative_to(self.root).as_posix())
                else:
                    raise EmpiricalArtifactError("unexpected run-block data entry")
            if actual != referenced:
                raise EmpiricalArtifactError("run-block data contains missing, unbound, or extra artifacts")
            expected_directories: set[str] = set()
            data_prefix = (PurePosixPath("blocks") / _block_name(block_index) / "data").as_posix()
            for relative in referenced:
                parent = PurePosixPath(relative).parent
                while parent.as_posix() != data_prefix:
                    expected_directories.add(parent.as_posix())
                    parent = parent.parent
            if actual_directories != expected_directories:
                raise EmpiricalArtifactError("run-block data contains an extra or missing directory")
        return generations, referenced

    def _validate_block(self, block_index: int) -> None:
        block_root = self._block_root(block_index)
        if not block_root.is_dir() or block_root.is_symlink():
            raise EmpiricalArtifactError("run block directory is missing")
        entries = {path.name for path in block_root.iterdir()}
        if not entries <= {"resume", "data", "COMPLETE.json"}:
            raise EmpiricalArtifactError("run block contains an unexpected artifact")
        generations, _ = self._validate_chain(block_index, require_data_exact=True)
        if not generations:
            raise EmpiricalArtifactError("run block has no committed resume generation")
        marker = block_root / "COMPLETE.json"
        if marker.exists():
            packet = _read_canonical_json(marker)
            expected = {
                "schema": BLOCK_COMPLETE_SCHEMA,
                "science_revision": SCIENCE_REVISION,
                "empirical_object": EMPIRICAL_OBJECT,
                "block_index": block_index,
                "bindings_sha256": self.effective_bindings_sha256,
                "final_generation": len(generations) - 1,
                "final_generation_sha256": generations[-1][0] if generations else None,
                "updates_per_arm": UPDATE_COUNT,
                "learned_arms": list(LEARNED_ARMS),
                "heldout_cells": list(HELDOUT_CELLS),
                "heldout_episodes_per_cell": HELDOUT_EPISODES_PER_CELL,
                "scripted_panels": list(SCRIPTED_PANELS),
                "counts": dict(BLOCK_COUNTS),
                "complete": True,
                "partial_interpretation_permitted": False,
            }
            if dict(packet) != expected or not generations or not _is_complete_state(
                generations[-1][1]
            ):
                raise EmpiricalArtifactError("run block COMPLETE marker differs")

    def _validate_published(self) -> CompletePanel:
        published = self.root / "published"
        if not published.is_dir() or published.is_symlink():
            raise EmpiricalArtifactError("published panel directory is missing")
        if {path.name for path in published.iterdir()} != {
            "analyzer.json",
            "result.json",
            "manifest.json",
            "COMPLETE",
        }:
            raise EmpiricalArtifactError("published panel inventory is incomplete or extra")
        analyzer = _read_regular_bytes(published / "analyzer.json")
        result = _read_regular_bytes(published / "result.json")
        manifest_payload = _read_regular_bytes(published / "manifest.json")
        manifest = _read_canonical_json(published / "manifest.json")
        marker = _read_canonical_json(published / "COMPLETE")
        if dict(marker) != {
            "schema": PANEL_COMPLETE_SCHEMA,
            "manifest_sha256": _sha256(manifest_payload),
            "complete": True,
        }:
            raise EmpiricalArtifactError("published COMPLETE marker does not bind the manifest")
        expected_keys = (
            "schema",
            "science_revision",
            "empirical_object",
            "bindings_sha256",
            "lease_audit_sha256",
            "block_count",
            "block_complete_sha256",
            "learned_arms",
            "scripted_panels",
            "counts",
            "registered_tail_count",
            "registered_tail_names",
            "branch",
            "analyzer_sha256",
            "result_sha256",
            "complete",
            "partial_interpretation_permitted",
        )
        _exact_mapping(manifest, expected_keys, "published panel manifest")
        block_digests = {
            _block_name(index): _sha256(
                _read_regular_bytes(self._block_root(index) / "COMPLETE.json")
            )
            for index in range(BLOCK_COUNT)
        }
        if (
            manifest["schema"] != PANEL_COMPLETE_SCHEMA
            or manifest["science_revision"] != SCIENCE_REVISION
            or manifest["empirical_object"] != EMPIRICAL_OBJECT
            or manifest["bindings_sha256"] != self.effective_bindings_sha256
            or manifest["lease_audit_sha256"]
            not in {digest for digest, _ in self._validate_lease_audits()}
            or manifest["block_count"] != BLOCK_COUNT
            or manifest["block_complete_sha256"] != block_digests
            or manifest["learned_arms"] != list(LEARNED_ARMS)
            or manifest["scripted_panels"] != list(SCRIPTED_PANELS)
            or manifest["counts"] != PANEL_COUNTS
            or manifest["registered_tail_count"] != REGISTERED_TAIL_COUNT
            or manifest["registered_tail_names"] != list(REGISTERED_TAIL_NAMES)
            or manifest["branch"] not in BRANCHES
            or manifest["analyzer_sha256"] != _sha256(analyzer)
            or manifest["result_sha256"] != _sha256(result)
            or manifest["complete"] is not True
            or manifest["partial_interpretation_permitted"] is not False
        ):
            raise EmpiricalArtifactError("published panel binding or exact inventory differs")
        _validate_publication_payloads(analyzer, result, str(manifest["branch"]))
        return CompletePanel(str(manifest["branch"]), analyzer, result, manifest)

    def validate(
        self,
        *,
        require_complete_blocks: bool = False,
        permit_published: bool = True,
        _permit_active_lock: bool = False,
    ) -> None:
        top = {path.name for path in self.root.iterdir()}
        allowed = {"bindings.json", "blocks", "lease_audits"}
        if "stage_repairs" in top:
            allowed.add("stage_repairs")
        if permit_published:
            allowed.add("published")
        if _permit_active_lock:
            allowed.add("PARENT_COMMIT.lock")
        if top - allowed:
            raise EmpiricalArtifactError("frontier contains an unexpected or incomplete top-level entry")
        if "PARENT_COMMIT.lock" in top:
            lock_packet = _read_canonical_json(self.root / "PARENT_COMMIT.lock")
            if (
                not _permit_active_lock
                or set(lock_packet)
                != {
                    "schema",
                    "parent_owner_sha256",
                    "frontier_bindings_sha256",
                    "process_id",
                    "process_nonce",
                }
                or lock_packet["schema"] != LOCK_SCHEMA
                or lock_packet["parent_owner_sha256"] != self._owner_sha256
                or lock_packet["frontier_bindings_sha256"] != self.bindings_sha256
                or lock_packet["process_id"] != os.getpid()
                or not isinstance(lock_packet["process_nonce"], str)
                or not _HEX.fullmatch(lock_packet["process_nonce"])
            ):
                raise EmpiricalArtifactError("frontier has an unowned or stale parent commit lock")
        if not {"bindings.json", "blocks", "lease_audits"} <= top:
            raise EmpiricalArtifactError("frontier bindings, lease audits, or blocks directory is missing")
        self._validate_bindings_manifest()
        self._validate_stage_repair_audit()
        self._validate_lease_audits()
        blocks_root = self.root / "blocks"
        if not blocks_root.is_dir() or blocks_root.is_symlink():
            raise EmpiricalArtifactError("blocks root is invalid")
        present: set[int] = set()
        for path in blocks_root.iterdir():
            match = _BLOCK_NAME.fullmatch(path.name)
            if not match:
                raise EmpiricalArtifactError("blocks root contains an unexpected entry")
            index = int(path.name[-2:])
            present.add(index)
            self._validate_block(index)
        if require_complete_blocks:
            if present != set(range(BLOCK_COUNT)):
                raise EmpiricalArtifactError("all twenty run blocks are not present")
            for index in range(BLOCK_COUNT):
                if not (self._block_root(index) / "COMPLETE.json").is_file():
                    raise EmpiricalArtifactError("all twenty run blocks are not sealed")
        if "published" in top:
            if not permit_published:
                raise EmpiricalArtifactError("analyzer/result publication already exists")
            if present != set(range(BLOCK_COUNT)):
                raise EmpiricalArtifactError("published panel exists before twenty blocks")
            self._validate_published()

    def restore_complete_panel(self) -> CompletePanel:
        self.validate(require_complete_blocks=True, permit_published=True)
        return self._validate_published()


__all__ = [
    "ArtifactRef",
    "ActiveLeasePermit",
    "ANALYZER_OUTPUT_SCHEMA",
    "AtomicEmpiricalFrontier",
    "BLOCK_COMPLETE_SCHEMA",
    "BLOCK_COUNT",
    "BLOCK_COUNTS",
    "BINDINGS_SCHEMA",
    "CompletePanel",
    "EMPIRICAL_OBJECT",
    "EmpiricalArtifactError",
    "EmpiricalBindings",
    "FRONTIER_SCHEMA",
    "HELDOUT_EPISODES_PER_CELL",
    "LEARNED_ARMS",
    "LEASE_AUDIT_SCHEMA",
    "LOCK_SCHEMA",
    "PANEL_COMPLETE_SCHEMA",
    "PANEL_COUNTS",
    "REGISTERED_TAIL_COUNT",
    "REGISTERED_TAIL_NAMES",
    "RESULT_OUTPUT_SCHEMA",
    "RESUME_SCHEMA",
    "ResumeState",
    "SCRIPTED_PANELS",
    "STAGING_SCHEMA",
    "StagedGeneration",
    "UPDATE_COUNT",
    "stage_binding_sha256_for_permit",
]
