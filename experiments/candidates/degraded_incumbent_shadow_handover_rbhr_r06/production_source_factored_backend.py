"""Independent phased native sidecar for DISH promotion-source fork R01.

This module owns a versioned ctypes surface distinct from the shared R06 host.
Its public TEST seam exposes the post-arrival/pre-CAS cut without accepting an
application-tick action or any caller-owned native ownership field.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from typing import Final, Mapping

import numpy as np


ABI_VERSION: Final = 1
_BATCH_WIDTH: Final = 2
_SOURCE = Path(__file__).with_name("native") / "dish_promotion_source_fork_r01.cpp"
_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/fp:strict", "/W4")


class PhasedSidecarError(RuntimeError):
    """The phased sidecar rejected an ABI or transaction invariant."""


class _UavCausalFacts(ctypes.Structure):
    _fields_ = [
        ("position", ctypes.c_double * 2),
        ("velocity", ctypes.c_double * 2),
        ("held_action", ctypes.c_double * 2),
        ("battery", ctypes.c_double),
        ("camera_present", ctypes.c_int32),
        ("camera_position", ctypes.c_double * 2),
        ("camera_missing", ctypes.c_int32),
        ("filter_position", ctypes.c_double * 2),
        ("filter_velocity", ctypes.c_double * 2),
        ("filter_covariance", ctypes.c_double * 3),
        ("radio_margin", ctypes.c_double * 3),
        ("source_present", ctypes.c_int32),
        ("source_age", ctypes.c_double),
        ("source_sequence", ctypes.c_int32),
        ("partner_present", ctypes.c_int32),
        ("partner_age", ctypes.c_double),
        ("partner_position", ctypes.c_double * 2),
        ("partner_velocity", ctypes.c_double * 2),
        ("partner_action", ctypes.c_double * 2),
        ("partner_battery", ctypes.c_double),
        ("partner_camera_missing", ctypes.c_int32),
        ("partner_owner_bit", ctypes.c_int32),
        ("partner_d", ctypes.c_int32),
        ("partner_g1", ctypes.c_int32),
        ("partner_g5", ctypes.c_int32),
        ("local_d", ctypes.c_int32),
        ("local_g1", ctypes.c_int32),
        ("local_g5", ctypes.c_int32),
        ("prepare_latch", ctypes.c_int32),
        ("warmup_ticks", ctypes.c_int32),
        ("snapshot_present", ctypes.c_int32),
        ("snapshot_age", ctypes.c_double),
        ("snapshot_owner", ctypes.c_int32),
        ("snapshot_service_epoch", ctypes.c_int32),
        ("snapshot_next_payload_sequence", ctypes.c_int32),
        ("snapshot_k_epoch", ctypes.c_int32),
        ("snapshot_common_source_sequence", ctypes.c_int32),
        ("snapshot_record_version", ctypes.c_int32),
        ("readiness_present", ctypes.c_int32),
        ("readiness_age", ctypes.c_double),
        ("readiness_owner", ctypes.c_int32),
        ("readiness_service_epoch", ctypes.c_int32),
        ("readiness_next_payload_sequence", ctypes.c_int32),
        ("readiness_k_epoch", ctypes.c_int32),
        ("readiness_common_source_sequence", ctypes.c_int32),
        ("readiness_snapshot_version", ctypes.c_int32),
    ]


class _CausalFacts(ctypes.Structure):
    _fields_ = [
        ("uav", _UavCausalFacts * 2),
        ("base_position", ctypes.c_double * 2),
        ("responder", ctypes.c_double * 4),
        ("k_active", ctypes.c_int32),
        ("countdown", ctypes.c_int32),
        ("renew", ctypes.c_int32),
        ("base_present", ctypes.c_int32),
        ("base_age", ctypes.c_double),
        ("base_position_error", ctypes.c_double),
        ("base_first_margin", ctypes.c_double),
        ("base_second_margin", ctypes.c_double),
        ("pending_switch", ctypes.c_int32),
        ("terminal", ctypes.c_int32),
    ]


class _HostState(ctypes.Structure):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("initialized", ctypes.c_int32),
        ("owner", ctypes.c_int32),
        ("application_tick", ctypes.c_int32),
        ("service_epoch", ctypes.c_int32),
        ("next_payload_sequence", ctypes.c_int32),
        ("k_epoch", ctypes.c_int32),
        ("intent_origin_tick", ctypes.c_int32),
        ("snapshot_version", ctypes.c_int32),
        ("readiness_version", ctypes.c_int32),
        ("lineage_lock", ctypes.c_int32 * 2),
        ("lineage_sequence", ctypes.c_int32 * 2),
        ("controller_hidden", ctypes.c_double * 512),
        ("causal", _CausalFacts),
    ]


class _PreparedTick(ctypes.Structure):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("phase", ctypes.c_int32),
        ("owner", ctypes.c_int32),
        ("application_tick", ctypes.c_int32),
        ("service_epoch", ctypes.c_int32),
        ("next_payload_sequence", ctypes.c_int32),
        ("k_epoch", ctypes.c_int32),
        ("intent_origin_tick", ctypes.c_int32),
        ("snapshot_version", ctypes.c_int32),
        ("readiness_version", ctypes.c_int32),
        ("snapshot_assimilation_requested", ctypes.c_int32),
        ("snapshot_recipient", ctypes.c_int32),
        ("lineage_lock", ctypes.c_int32 * 2),
        ("lineage_sequence", ctypes.c_int32 * 2),
        ("controller_hidden", ctypes.c_double * 512),
        ("causal", _CausalFacts),
    ]


class _RecurrentHandoff(ctypes.Structure):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("owner", ctypes.c_int32),
        ("service_epoch", ctypes.c_int32),
        ("next_payload_sequence", ctypes.c_int32),
        ("k_epoch", ctypes.c_int32),
        ("intent_origin_tick", ctypes.c_int32),
        ("snapshot_version", ctypes.c_int32),
        ("readiness_version", ctypes.c_int32),
        ("lineage_lock", ctypes.c_int32 * 2),
        ("lineage_sequence", ctypes.c_int32 * 2),
        ("pre_bridge_hidden", ctypes.c_double * 512),
        ("post_bridge_hidden", ctypes.c_double * 512),
    ]


class _BranchState(ctypes.Structure):
    _fields_ = [
        ("owner", ctypes.c_int32),
        ("hidden", ctypes.c_double * 512),
        ("actor", ctypes.c_double * 216),
        ("critic", ctypes.c_double * 58),
    ]


class _ForkOutput(ctypes.Structure):
    _fields_ = [
        ("abi_version", ctypes.c_uint32),
        ("struct_size", ctypes.c_uint32),
        ("phase", ctypes.c_int32),
        ("forward_count", ctypes.c_int32),
        ("prepared_input_immutable", ctypes.c_int32),
        ("handoff_input_immutable", ctypes.c_int32),
        ("linearization_valid", ctypes.c_int32),
        ("branches", _BranchState * 3),
    ]


_LOCK = threading.RLock()
_LOADED: dict[str, ctypes.CDLL] = {}


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise PhasedSidecarError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [
            str(locator),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    installation = Path(result.stdout.strip())
    if result.returncode != 0 or not installation.is_dir():
        raise PhasedSidecarError("MSVC build tools are unavailable")
    return installation


def _source_stat_key() -> str:
    stat = _SOURCE.stat()
    return f"abi{ABI_VERSION}-s{stat.st_size}-m{stat.st_mtime_ns}"


def _sidecar_cache_root() -> Path:
    return Path(tempfile.gettempdir()) / "hmasd_dish_psf_r01_sidecar"


def _artifact_path(key: str) -> Path:
    return (
        _sidecar_cache_root()
        / key
        / "dish_promotion_source_fork_r01.dll"
    )


def _compile(key: str) -> Path:
    target = _artifact_path(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        return target
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    object_path = target.parent / f"dish_promotion_source_fork_r01.{suffix}.obj"
    candidate = target.parent / f"dish_promotion_source_fork_r01.{suffix}.dll"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(_FLAGS)} "{_SOURCE}" '
        f'/Fo:"{object_path}" /link /OUT:"{candidate}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=target.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not candidate.is_file():
        raise PhasedSidecarError(
            f"native sidecar compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    try:
        os.replace(candidate, target)
    except OSError:
        if not target.is_file():
            raise
        candidate.unlink(missing_ok=True)
    finally:
        object_path.unlink(missing_ok=True)
    return target


def _configure(library: ctypes.CDLL) -> ctypes.CDLL:
    library.dish_psf_r01_abi_version.argtypes = []
    library.dish_psf_r01_abi_version.restype = ctypes.c_uint32
    size_exports = (
        ("host_state_v1", _HostState),
        ("prepared_tick_v1", _PreparedTick),
        ("recurrent_handoff_v1", _RecurrentHandoff),
        ("branch_state_v1", _BranchState),
        ("fork_output_v1", _ForkOutput),
    )
    observed = [library.dish_psf_r01_abi_version()]
    expected = [ABI_VERSION]
    for export_name, structure in size_exports:
        function = getattr(library, f"dish_psf_r01_{export_name}_size")
        function.argtypes = []
        function.restype = ctypes.c_size_t
        observed.append(function())
        expected.append(ctypes.sizeof(structure))
    if observed != expected:
        raise PhasedSidecarError(
            f"phased sidecar ABI differs: observed={observed}, expected={expected}"
        )

    library.dish_psf_r01_test_two_owner_fixture.argtypes = [
        ctypes.POINTER(_HostState),
        ctypes.c_size_t,
    ]
    library.dish_psf_r01_begin_tick_batch.argtypes = [
        ctypes.POINTER(_HostState),
        ctypes.c_size_t,
        ctypes.POINTER(_PreparedTick),
    ]
    library.dish_psf_r01_clone_prepared_batch.argtypes = [
        ctypes.POINTER(_PreparedTick),
        ctypes.POINTER(_RecurrentHandoff),
        ctypes.c_size_t,
        ctypes.POINTER(_ForkOutput),
    ]
    for export_name in (
        "dish_psf_r01_test_two_owner_fixture",
        "dish_psf_r01_begin_tick_batch",
        "dish_psf_r01_clone_prepared_batch",
    ):
        getattr(library, export_name).restype = ctypes.c_int32
    return library


def _require_sidecar() -> ctypes.CDLL:
    key = _source_stat_key()
    with _LOCK:
        if key not in _LOADED:
            _LOADED[key] = _configure(ctypes.CDLL(str(_compile(key))))
        return _LOADED[key]


def sidecar_cache_observation() -> Mapping[str, object]:
    """Return non-authoritative TEST build-cache telemetry without loading it."""

    key = _source_stat_key()
    artifact = _artifact_path(key)
    return {
        "scope": "TEST_SIDECAR_BUILD_CACHE_TELEMETRY_ONLY",
        "source_stat_key": key,
        "artifact": str(artifact.resolve()),
        "artifact_present": artifact.is_file(),
    }


def load_cached_sidecar_read_only() -> Mapping[str, object]:
    """Load the current TEST ABI only when its cache artifact already exists."""

    observation = dict(sidecar_cache_observation())
    artifact = Path(str(observation["artifact"]))
    if not artifact.is_file():
        return {
            **observation,
            "status": "CACHE_ABSENT",
            "dynamic_test_probe_available": False,
            "compile_called": False,
            "cache_write_attempted": False,
        }
    key = str(observation["source_stat_key"])
    try:
        with _LOCK:
            if key not in _LOADED:
                _LOADED[key] = _configure(ctypes.CDLL(str(artifact.resolve())))
    except (AttributeError, OSError, PhasedSidecarError) as error:
        return {
            **observation,
            "status": "CACHE_ABI_INVALID",
            "dynamic_test_probe_available": False,
            "compile_called": False,
            "cache_write_attempted": False,
            "error": str(error).encode("ascii", "backslashreplace").decode("ascii"),
        }
    return {
        **observation,
        "status": "CACHE_ACCEPTED",
        "dynamic_test_probe_available": True,
        "compile_called": False,
        "cache_write_attempted": False,
        "artifact_bytes": artifact.stat().st_size,
    }


def _structure_array_bytes(value: ctypes.Array[ctypes.Structure]) -> bytes:
    return ctypes.string_at(ctypes.addressof(value), ctypes.sizeof(value))


def _readonly(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


@dataclass(frozen=True)
class BranchBatch:
    owner: np.ndarray
    hidden: np.ndarray
    actor: np.ndarray
    critic: np.ndarray


@dataclass(frozen=True)
class ForkBatch:
    branches: dict[str, BranchBatch]
    forward_count: np.ndarray
    prepared_input_immutable: bool
    handoff_bytes_before: bytes
    handoff_bytes_after: bytes
    phase: str = "BRANCH_OBSERVATION_READY_PRE_FORWARD"


@dataclass(frozen=True)
class UavCausalFacts:
    position: tuple[float, float]
    velocity: tuple[float, float]
    held_action: tuple[float, float]
    battery: float
    camera_present: int
    camera_position: tuple[float, float]
    camera_missing: int
    filter_position: tuple[float, float]
    filter_velocity: tuple[float, float]
    filter_covariance: tuple[float, float, float]
    radio_margin: tuple[float, float, float]
    source_present: int
    source_age: float
    source_sequence: int
    partner_present: int
    partner_age: float
    partner_position: tuple[float, float]
    partner_velocity: tuple[float, float]
    partner_action: tuple[float, float]
    partner_battery: float
    partner_camera_missing: int
    partner_owner_bit: int
    partner_d: int
    partner_g1: int
    partner_g5: int
    local_d: int
    local_g1: int
    local_g5: int
    prepare_latch: int
    warmup_ticks: int
    snapshot_present: int
    snapshot_age: float
    snapshot_owner: int
    snapshot_service_epoch: int
    snapshot_next_payload_sequence: int
    snapshot_k_epoch: int
    snapshot_common_source_sequence: int
    snapshot_record_version: int
    readiness_present: int
    readiness_age: float
    readiness_owner: int
    readiness_service_epoch: int
    readiness_next_payload_sequence: int
    readiness_k_epoch: int
    readiness_common_source_sequence: int
    readiness_snapshot_version: int


@dataclass(frozen=True)
class LaneCausalFacts:
    owner: int
    service_epoch: int
    next_payload_sequence: int
    k_epoch: int
    snapshot_version: int
    lineage_sequence: tuple[int, int]
    uav: tuple[UavCausalFacts, UavCausalFacts]
    base_position: tuple[float, float]
    responder: tuple[float, float, float, float]
    k_active: int
    countdown: int
    renew: int
    base_present: int
    base_age: float
    base_position_error: float
    base_first_margin: float
    base_second_margin: float
    pending_switch: int
    terminal: int


def _tuple_floats(values: ctypes.Array[ctypes.c_double]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _uav_causal_facts(raw: _UavCausalFacts) -> UavCausalFacts:
    return UavCausalFacts(
        position=_tuple_floats(raw.position),
        velocity=_tuple_floats(raw.velocity),
        held_action=_tuple_floats(raw.held_action),
        battery=float(raw.battery),
        camera_present=int(raw.camera_present),
        camera_position=_tuple_floats(raw.camera_position),
        camera_missing=int(raw.camera_missing),
        filter_position=_tuple_floats(raw.filter_position),
        filter_velocity=_tuple_floats(raw.filter_velocity),
        filter_covariance=_tuple_floats(raw.filter_covariance),
        radio_margin=_tuple_floats(raw.radio_margin),
        source_present=int(raw.source_present),
        source_age=float(raw.source_age),
        source_sequence=int(raw.source_sequence),
        partner_present=int(raw.partner_present),
        partner_age=float(raw.partner_age),
        partner_position=_tuple_floats(raw.partner_position),
        partner_velocity=_tuple_floats(raw.partner_velocity),
        partner_action=_tuple_floats(raw.partner_action),
        partner_battery=float(raw.partner_battery),
        partner_camera_missing=int(raw.partner_camera_missing),
        partner_owner_bit=int(raw.partner_owner_bit),
        partner_d=int(raw.partner_d),
        partner_g1=int(raw.partner_g1),
        partner_g5=int(raw.partner_g5),
        local_d=int(raw.local_d),
        local_g1=int(raw.local_g1),
        local_g5=int(raw.local_g5),
        prepare_latch=int(raw.prepare_latch),
        warmup_ticks=int(raw.warmup_ticks),
        snapshot_present=int(raw.snapshot_present),
        snapshot_age=float(raw.snapshot_age),
        snapshot_owner=int(raw.snapshot_owner),
        snapshot_service_epoch=int(raw.snapshot_service_epoch),
        snapshot_next_payload_sequence=int(raw.snapshot_next_payload_sequence),
        snapshot_k_epoch=int(raw.snapshot_k_epoch),
        snapshot_common_source_sequence=int(raw.snapshot_common_source_sequence),
        snapshot_record_version=int(raw.snapshot_record_version),
        readiness_present=int(raw.readiness_present),
        readiness_age=float(raw.readiness_age),
        readiness_owner=int(raw.readiness_owner),
        readiness_service_epoch=int(raw.readiness_service_epoch),
        readiness_next_payload_sequence=int(raw.readiness_next_payload_sequence),
        readiness_k_epoch=int(raw.readiness_k_epoch),
        readiness_common_source_sequence=int(raw.readiness_common_source_sequence),
        readiness_snapshot_version=int(raw.readiness_snapshot_version),
    )


class PreparedBatch:
    public_fields = (
        "owner",
        "application_tick",
        "snapshot_assimilation_requested",
        "snapshot_recipient",
        "pre_bridge_hidden",
        "phase",
    )

    def __init__(self, rows: ctypes.Array[_PreparedTick]) -> None:
        self._rows = rows
        self._consumed = False
        self.last_handoff_bytes: bytes | None = None

    def snapshot_bytes(self) -> bytes:
        return _structure_array_bytes(self._rows)

    @property
    def pre_bridge_hidden(self) -> np.ndarray:
        hidden = np.stack(
            [np.ctypeslib.as_array(row.controller_hidden).reshape(4, 128) for row in self._rows]
        ).copy()
        return _readonly(hidden)

    @property
    def causal_facts(self) -> tuple[LaneCausalFacts, ...]:
        lanes: list[LaneCausalFacts] = []
        for row in self._rows:
            raw = row.causal
            lanes.append(
                LaneCausalFacts(
                    owner=int(row.owner),
                    service_epoch=int(row.service_epoch),
                    next_payload_sequence=int(row.next_payload_sequence),
                    k_epoch=int(row.k_epoch),
                    snapshot_version=int(row.snapshot_version),
                    lineage_sequence=tuple(int(value) for value in row.lineage_sequence),
                    uav=(_uav_causal_facts(raw.uav[0]), _uav_causal_facts(raw.uav[1])),
                    base_position=_tuple_floats(raw.base_position),
                    responder=_tuple_floats(raw.responder),
                    k_active=int(raw.k_active),
                    countdown=int(raw.countdown),
                    renew=int(raw.renew),
                    base_present=int(raw.base_present),
                    base_age=float(raw.base_age),
                    base_position_error=float(raw.base_position_error),
                    base_first_margin=float(raw.base_first_margin),
                    base_second_margin=float(raw.base_second_margin),
                    pending_switch=int(raw.pending_switch),
                    terminal=int(raw.terminal),
                )
            )
        return tuple(lanes)

    def test_only_replace_causal(
        self, *, lane: int, physical: int, field: str, value: int
    ) -> "PreparedBatch":
        allowed = {
            "source_sequence",
            "snapshot_common_source_sequence",
            "readiness_common_source_sequence",
            "snapshot_record_version",
            "readiness_snapshot_version",
        }
        if lane not in range(len(self._rows)) or physical not in (0, 1) or field not in allowed:
            raise PhasedSidecarError("TEST causal replacement coordinate differs")
        rows = (_PreparedTick * len(self._rows))()
        for index, row in enumerate(self._rows):
            rows[index] = row
        setattr(rows[lane].causal.uav[physical], field, int(value))
        return PreparedBatch(rows)

    def test_only_replace_lineage(
        self, *, lane: int, physical: int, value: int
    ) -> "PreparedBatch":
        if lane not in range(len(self._rows)) or physical not in (0, 1):
            raise PhasedSidecarError("TEST lineage replacement coordinate differs")
        rows = (_PreparedTick * len(self._rows))()
        for index, row in enumerate(self._rows):
            rows[index] = row
        rows[lane].lineage_sequence[physical] = int(value)
        return PreparedBatch(rows)

    @property
    def owner(self) -> np.ndarray:
        return _readonly(np.asarray([row.owner for row in self._rows], dtype=np.int32))

    @property
    def application_tick(self) -> np.ndarray:
        return _readonly(
            np.asarray([row.application_tick for row in self._rows], dtype=np.int32)
        )

    @property
    def snapshot_assimilation_requested(self) -> np.ndarray:
        return _readonly(
            np.asarray(
                [bool(row.snapshot_assimilation_requested) for row in self._rows],
                dtype=np.bool_,
            )
        )

    @property
    def snapshot_recipient(self) -> np.ndarray:
        return _readonly(
            np.asarray([row.snapshot_recipient for row in self._rows], dtype=np.int32)
        )

    @property
    def phase(self) -> str:
        if any(row.phase != 1 for row in self._rows):
            raise PhasedSidecarError("prepared phase differs")
        return "POST_ARRIVAL_PRE_CAS"

    def recurrent_handoff(
        self, pre_arrival: np.ndarray, post_arrival: np.ndarray
    ) -> "RecurrentHandoff":
        pre = np.asarray(pre_arrival, dtype=np.float64, order="C")
        post = np.asarray(post_arrival, dtype=np.float64, order="C")
        expected_shape = (len(self._rows), 4, 128)
        if pre.shape != expected_shape or post.shape != expected_shape:
            raise PhasedSidecarError("recurrent bridge tensors must have shape (batch,4,128)")

        handoffs = (_RecurrentHandoff * len(self._rows))()
        for lane, prepared in enumerate(self._rows):
            handoff = handoffs[lane]
            handoff.abi_version = ABI_VERSION
            handoff.struct_size = ctypes.sizeof(_RecurrentHandoff)
            handoff.owner = prepared.owner
            handoff.service_epoch = prepared.service_epoch
            handoff.next_payload_sequence = prepared.next_payload_sequence
            handoff.k_epoch = prepared.k_epoch
            handoff.intent_origin_tick = prepared.intent_origin_tick
            handoff.snapshot_version = prepared.snapshot_version
            handoff.readiness_version = prepared.readiness_version
            handoff.lineage_lock[:] = prepared.lineage_lock[:]
            handoff.lineage_sequence[:] = prepared.lineage_sequence[:]
            np.ctypeslib.as_array(handoff.pre_bridge_hidden)[:] = pre[lane].reshape(512)
            np.ctypeslib.as_array(handoff.post_bridge_hidden)[:] = post[lane].reshape(512)
        return RecurrentHandoff(handoffs)

    def clone_prepared(self, recurrent_handoff: "RecurrentHandoff") -> ForkBatch:
        if self._consumed:
            raise PhasedSidecarError("prepared batch may be cloned exactly once")
        if not isinstance(recurrent_handoff, RecurrentHandoff):
            raise PhasedSidecarError("clone_prepared requires a typed recurrent handoff")
        handoffs = recurrent_handoff._rows
        if len(handoffs) != len(self._rows):
            raise PhasedSidecarError("recurrent handoff batch width differs")

        prepared_before = self.snapshot_bytes()
        handoff_before = _structure_array_bytes(handoffs)
        outputs = (_ForkOutput * len(self._rows))()
        code = _require_sidecar().dish_psf_r01_clone_prepared_batch(
            self._rows, handoffs, len(self._rows), outputs
        )
        prepared_after = self.snapshot_bytes()
        handoff_after = _structure_array_bytes(handoffs)
        if code == 2:
            raise PhasedSidecarError("native recurrent handoff linearization differs")
        if code == 3:
            raise PhasedSidecarError("recurrent handoff must be finite and within [-1,1]")
        if code == 4:
            raise PhasedSidecarError("recurrent handoff changed a copy outside the snapshot recipient")
        if code != 0:
            raise PhasedSidecarError(f"native clone_prepared rejected batch ({code})")
        if prepared_before != prepared_after:
            raise PhasedSidecarError("native clone_prepared mutated prepared input")
        if handoff_before != handoff_after:
            raise PhasedSidecarError("native clone_prepared mutated recurrent handoff")
        if any(
            output.abi_version != ABI_VERSION
            or output.struct_size != ctypes.sizeof(_ForkOutput)
            or output.phase != 2
            or output.forward_count != 0
            or output.prepared_input_immutable != 1
            or output.handoff_input_immutable != 1
            or output.linearization_valid != 1
            for output in outputs
        ):
            raise PhasedSidecarError("native clone_prepared output contract differs")

        branch_names = ("RETAIN", "TRANSFER_COPY", "TRANSFER_SHADOW")
        branches: dict[str, BranchBatch] = {}
        for branch_index, branch_name in enumerate(branch_names):
            owners = np.asarray(
                [output.branches[branch_index].owner for output in outputs], dtype=np.int32
            )
            branch_hidden = np.stack(
                [
                    np.ctypeslib.as_array(output.branches[branch_index].hidden).reshape(4, 128)
                    for output in outputs
                ]
            ).copy()
            actor = np.stack(
                [
                    np.ctypeslib.as_array(output.branches[branch_index].actor).reshape(4, 54)
                    for output in outputs
                ]
            ).copy()
            critic = np.stack(
                [np.ctypeslib.as_array(output.branches[branch_index].critic) for output in outputs]
            ).copy()
            branches[branch_name] = BranchBatch(
                owner=_readonly(owners),
                hidden=_readonly(branch_hidden),
                actor=_readonly(actor),
                critic=_readonly(critic),
            )

        self._consumed = True
        self.last_handoff_bytes = handoff_before
        return ForkBatch(
            branches=branches,
            forward_count=_readonly(
                np.asarray([output.forward_count for output in outputs], dtype=np.int32)
            ),
            prepared_input_immutable=True,
            handoff_bytes_before=handoff_before,
            handoff_bytes_after=handoff_after,
        )


class RecurrentHandoff:
    _REPLACEABLE_FIELDS = frozenset(
        {
            "owner",
            "service_epoch",
            "next_payload_sequence",
            "k_epoch",
            "intent_origin_tick",
            "snapshot_version",
            "readiness_version",
        }
    )

    def __init__(self, rows: ctypes.Array[_RecurrentHandoff]) -> None:
        self._rows = rows

    def snapshot_bytes(self) -> bytes:
        return _structure_array_bytes(self._rows)

    def test_only_permute_lanes(self, order: tuple[int, ...]) -> "RecurrentHandoff":
        if tuple(sorted(order)) != tuple(range(len(self._rows))):
            raise PhasedSidecarError("TEST lane order must be a complete permutation")
        rows = (_RecurrentHandoff * len(self._rows))()
        for target, source in enumerate(order):
            rows[target] = self._rows[source]
        return RecurrentHandoff(rows)

    def test_only_replace(self, *, lane: int, field: str, value: int) -> "RecurrentHandoff":
        if lane < 0 or lane >= len(self._rows):
            raise PhasedSidecarError("TEST replacement lane differs")
        if field not in self._REPLACEABLE_FIELDS:
            raise PhasedSidecarError("TEST replacement field differs")
        rows = (_RecurrentHandoff * len(self._rows))()
        for index, row in enumerate(self._rows):
            rows[index] = row
        setattr(rows[lane], field, int(value))
        return RecurrentHandoff(rows)


class NativeBatch:
    def __init__(self, states: ctypes.Array[_HostState]) -> None:
        self._states = states

    def snapshot_bytes(self) -> bytes:
        return _structure_array_bytes(self._states)

    def begin_tick(self) -> PreparedBatch:
        parent_before = self.snapshot_bytes()
        prepared = (_PreparedTick * len(self._states))()
        code = _require_sidecar().dish_psf_r01_begin_tick_batch(
            self._states, len(self._states), prepared
        )
        if code != 0:
            raise PhasedSidecarError(f"native begin_tick rejected batch ({code})")
        if self.snapshot_bytes() != parent_before:
            raise PhasedSidecarError("native begin_tick mutated parent")
        return PreparedBatch(prepared)


def test_only_two_owner_batch() -> NativeBatch:
    """Return the native-owned two-owner TEST fixture for phased conformance."""

    states = (_HostState * _BATCH_WIDTH)()
    code = _require_sidecar().dish_psf_r01_test_two_owner_fixture(states, _BATCH_WIDTH)
    if code != 0:
        raise PhasedSidecarError(f"native two-owner fixture rejected batch ({code})")
    return NativeBatch(states)


test_only_two_owner_batch.__test__ = False


__all__ = [
    "BranchBatch",
    "ForkBatch",
    "NativeBatch",
    "PhasedSidecarError",
    "PreparedBatch",
    "RecurrentHandoff",
    "load_cached_sidecar_read_only",
    "sidecar_cache_observation",
    "test_only_two_owner_batch",
]
