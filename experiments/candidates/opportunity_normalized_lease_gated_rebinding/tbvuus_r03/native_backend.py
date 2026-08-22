"""Fail-closed source-keyed ctypes binding for the TBVUUS r03 C++ host.

There is no Python execution fallback and no production namespace adapter.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
from typing import Iterable

from .config import MAX_STATES, MAX_TICKS, FixtureCase
from .oracle import ACTION_NAMES, EncounterResult, TickRecord

_SOURCE = Path(__file__).with_name("native") / "tbvuus_backend.cpp"
NATIVE_ABI_VERSION = 1
MSVC_COMPILE_FLAGS = (
    "/nologo",
    "/std:c++17",
    "/O2",
    "/EHsc",
    "/LD",
    "/fp:strict",
)


class NativeBackendError(RuntimeError):
    pass


class _Input(ctypes.Structure):
    _fields_ = [
        ("route_class", ctypes.c_int),
        ("direction", ctypes.c_int),
        ("lateral", ctypes.c_int),
        ("arm", ctypes.c_int),
        ("target", ctypes.c_double * MAX_STATES),
        ("wind_tx", ctypes.c_double * MAX_STATES),
        ("wind_ty", ctypes.c_double * MAX_STATES),
        ("wind_rx", ctypes.c_double * MAX_STATES),
        ("wind_ry", ctypes.c_double * MAX_STATES),
        ("sensor_x", ctypes.c_double * MAX_STATES),
        ("sensor_y", ctypes.c_double * MAX_STATES),
        ("shadow_tr", ctypes.c_double * MAX_STATES),
        ("shadow_rb", ctypes.c_double * MAX_STATES),
        ("link_tr", ctypes.c_double * MAX_TICKS),
        ("link_rb", ctypes.c_double * MAX_TICKS),
    ]


class _Tick(ctypes.Structure):
    _fields_ = [
        *[(name, ctypes.c_int) for name in (
            "tick", "scored", "scored_index", "action_code", "scheduled",
            "shell", "fit_available", "selected_template", "effective",
        )],
        ("time", ctypes.c_double),
        ("residuals", ctypes.c_double * 8),
        *[(name, ctypes.c_double) for name in (
            "fit_t1", "fit_t2", "fit_z1x", "fit_z1y", "fit_z2x", "fit_z2y",
            "eta_raw", "eta_patch", "patch_x", "patch_y", "patch_vx", "patch_vy",
            "target_x", "target_y", "tangent_x", "tangent_y", "normal_x", "normal_y",
            "zeta", "wind_tx", "wind_ty", "wind_rx", "wind_ry", "pt_x", "pt_y",
            "pr_x", "pr_y", "xpre_x", "xpre_y", "vpre_x", "vpre_y", "xhat_x",
            "xhat_y", "vhat_x", "vhat_y",
        )],
        ("sensor_visible", ctypes.c_int),
        ("sensor_x", ctypes.c_double),
        ("sensor_y", ctypes.c_double),
        ("buffer_pre", ctypes.c_int),
        ("buffer_post", ctypes.c_int),
        *[(name, ctypes.c_double) for name in (
            "wt_x", "wt_y", "wr_x", "wr_y", "tracking_error",
        )],
        ("tracking_valid", ctypes.c_int),
        ("shadow_tr", ctypes.c_double),
        ("shadow_rb", ctypes.c_double),
        ("los_tr", ctypes.c_int),
        ("los_rb", ctypes.c_int),
        *[(name, ctypes.c_double) for name in (
            "margin_tr", "margin_rb", "prob_tr", "prob_rb", "link_u_tr", "link_u_rb",
        )],
        *[(name, ctypes.c_int) for name in (
            "raw_trial_tr", "raw_trial_rb", "trial_tr", "trial_rb", "packet_valid",
            "blackout", "lockout",
        )],
        *[(name, ctypes.c_double) for name in (
            "et_before", "er_before", "et_after", "er_after", "at_x", "at_y",
            "ar_x", "ar_y", "gt_x", "gt_y", "gr_x", "gr_y",
        )],
        *[(name, ctypes.c_int) for name in (
            "it", "ir", "uit", "uir", "safety_override",
        )],
        ("min_separation", ctypes.c_double),
        ("terrain_t_after", ctypes.c_double),
        ("terrain_r_after", ctypes.c_double),
        *[(name, ctypes.c_int) for name in (
            "terrain_penetration", "geofence_exit", "separation_breach", "service",
            "hard_failure", "no_planner", "no_safe", "numerical_fault", "battery",
        )],
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        *[(name, ctypes.c_int) for name in (
            "total_ticks", "scored_valid", "scheduled", "shells", "fit_count",
            "effective_count", "overrides", "terrain_penetrations", "geofence_exits",
            "separation_breaches", "hard_failure", "no_planner", "no_safe", "numerical_fault", "battery",
        )],
        ("ticks", _Tick * MAX_TICKS),
    ]


def source_sha256() -> str:
    """Hash the current source bytes; this is intentionally never memoized."""
    return hashlib.sha256(_SOURCE.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    vswhere = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [
            str(vswhere),
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    path = Path(result.stdout.strip())
    if not path.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return path


def _compiler_path() -> Path:
    candidates = tuple(
        path
        for path in (_vs_installation() / "VC" / "Tools" / "MSVC").glob("*/bin/Hostx64/x64/cl.exe")
        if path.is_file()
    )
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    return max(candidates, key=lambda path: tuple(int(part) for part in path.parts[-5].split(".")))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@functools.lru_cache(maxsize=1)
def _native_toolchain_identity_cached() -> dict[str, object]:
    compiler = _compiler_path().resolve()
    stat = compiler.stat()
    version = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    version_text = "\n".join(
        line.strip()
        for line in (version.stdout + "\n" + version.stderr).splitlines()
        if line.strip()
    )
    if "Microsoft" not in version_text or "C/C++" not in version_text:
        raise NativeBackendError("MSVC version identity could not be read")
    return {
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256_file(compiler),
        "compiler_size": stat.st_size,
        "compiler_mtime_ns": stat.st_mtime_ns,
        "compiler_version_output": version_text,
        "compile_flags": list(MSVC_COMPILE_FLAGS),
        "abi_version": NATIVE_ABI_VERSION,
    }


def native_toolchain_identity() -> dict[str, object]:
    identity = _native_toolchain_identity_cached()
    return {**identity, "compile_flags": list(identity["compile_flags"])}  # type: ignore[arg-type]


def _build_material() -> tuple[str, str, bytes]:
    source_bytes = _SOURCE.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    toolchain = native_toolchain_identity()
    digest = hashlib.sha256()
    digest.update(b"ONLGR-TBVUUS-R03-NATIVE-BUILD-v1\0")
    digest.update(source_digest.encode("ascii"))
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        encoded = flag.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    digest.update(NATIVE_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest(), source_digest, source_bytes


def native_build_key() -> str:
    """Return a key for the source bytes visible at this exact call."""
    return _build_material()[0]


def _artifact_path(build_key: str) -> Path:
    return Path(tempfile.gettempdir()) / "hmasd_tbvuus_r03_native" / build_key / "tbvuus_backend.dll"


def _source_snapshot(cache: Path, source_bytes: bytes) -> Path:
    snapshot = cache / "tbvuus_backend.source.cpp"
    if snapshot.is_file():
        if snapshot.read_bytes() != source_bytes:
            raise NativeBackendError("build-key source snapshot mismatch")
        return snapshot
    candidate = cache / f"tbvuus_backend.source.{os.getpid()}.{threading.get_ident()}.tmp"
    with candidate.open("wb") as stream:
        stream.write(source_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(candidate, snapshot)
    finally:
        candidate.unlink(missing_ok=True)
    if snapshot.read_bytes() != source_bytes:
        raise NativeBackendError("published source snapshot mismatch")
    return snapshot


def _compiled_path(build_key: str, source_bytes: bytes) -> Path:
    cache = _artifact_path(build_key).parent
    cache.mkdir(parents=True, exist_ok=True)
    snapshot = _source_snapshot(cache, source_bytes)
    dll = _artifact_path(build_key)
    if dll.is_file():
        return dll
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    obj = cache / f"tbvuus_backend.{suffix}.obj"
    candidate = cache / f"tbvuus_backend.{suffix}.dll"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{snapshot}" /Fo:"{obj}" /link /OUT:"{candidate}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not candidate.is_file():
        raise NativeBackendError(
            f"native backend compilation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
        )
    try:
        os.replace(candidate, dll)
    except OSError:
        if not dll.is_file():
            raise
        candidate.unlink(missing_ok=True)
    finally:
        obj.unlink(missing_ok=True)
    return dll


_LIBRARY_LOCK = threading.RLock()
_LOADED_LIBRARIES: dict[str, ctypes.CDLL] = {}


def _configure_library(library: ctypes.CDLL) -> ctypes.CDLL:
    library.tbvuus_abi_version.argtypes = []
    library.tbvuus_abi_version.restype = ctypes.c_int
    for name in ("tbvuus_input_size", "tbvuus_tick_size", "tbvuus_output_size"):
        function = getattr(library, name)
        function.argtypes = []
        function.restype = ctypes.c_uint64
    if library.tbvuus_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("native backend ABI version mismatch")
    expected = (ctypes.sizeof(_Input), ctypes.sizeof(_Tick), ctypes.sizeof(_Output))
    observed = (
        library.tbvuus_input_size(),
        library.tbvuus_tick_size(),
        library.tbvuus_output_size(),
    )
    if observed != expected:
        raise NativeBackendError(f"native backend sizeof mismatch: {observed!r} != {expected!r}")
    library.tbvuus_run_batch.argtypes = [
        ctypes.POINTER(_Input),
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.POINTER(_Output),
        ctypes.c_uint64,
    ]
    library.tbvuus_run_batch.restype = ctypes.c_int
    return library


def _require_library_for_material(build_key: str, source_bytes: bytes) -> ctypes.CDLL:
    with _LIBRARY_LOCK:
        existing = _LOADED_LIBRARIES.get(build_key)
        if existing is not None:
            return existing
        library = _configure_library(ctypes.CDLL(str(_compiled_path(build_key, source_bytes))))
        _LOADED_LIBRARIES[build_key] = library
        return library


def require_cpp_batched_backend() -> ctypes.CDLL:
    """Load/reuse only the DLL for the currently visible source build key."""
    build_key, _, source_bytes = _build_material()
    return _require_library_for_material(build_key, source_bytes)


def _abi_identity(library: ctypes.CDLL) -> dict[str, int]:
    return {
        "abi_version": library.tbvuus_abi_version(),
        "input_size": library.tbvuus_input_size(),
        "tick_size": library.tbvuus_tick_size(),
        "output_size": library.tbvuus_output_size(),
    }


def native_abi_identity() -> dict[str, int]:
    return _abi_identity(require_cpp_batched_backend())


def native_artifact_identity() -> dict[str, object]:
    build_key, source_digest, source_bytes = _build_material()
    path = _artifact_path(build_key)
    present_before = path.is_file()
    started = time.perf_counter()
    library = _require_library_for_material(build_key, source_bytes)
    elapsed = time.perf_counter() - started
    if not path.is_file():
        raise NativeBackendError("native artifact disappeared after load")
    stat = path.stat()
    return {
        "path": str(path),
        "sha256": _sha256_file(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "cache_present_before": present_before,
        "load_seconds": elapsed,
        "source_sha256": source_digest,
        "build_key": build_key,
        "abi": _abi_identity(library),
    }


def _input(case: FixtureCase) -> _Input:
    case.validate_shape()
    spec, tape = case.spec, case.tape
    result = _Input()
    result.route_class = int(spec.route_class)
    result.direction = spec.direction
    result.lateral = spec.lateral_offset
    result.arm = int(case.arm)
    for index, value in enumerate(tape.target_lateral):
        result.target[index] = value
    for index, (x, y) in enumerate(tape.wind_t):
        result.wind_tx[index], result.wind_ty[index] = x, y
    for index, (x, y) in enumerate(tape.wind_r):
        result.wind_rx[index], result.wind_ry[index] = x, y
    for index, (x, y) in enumerate(tape.sensor):
        result.sensor_x[index], result.sensor_y[index] = x, y
    for index, value in enumerate(tape.shadow_tr):
        result.shadow_tr[index] = value
    for index, value in enumerate(tape.shadow_rb):
        result.shadow_rb[index] = value
    for index, value in enumerate(tape.link_tr):
        result.link_tr[index] = value
    for index, value in enumerate(tape.link_rb):
        result.link_rb[index] = value
    return result


def _tick(value: _Tick) -> TickRecord:
    observation = (value.sensor_x, value.sensor_y) if value.sensor_visible else None
    return TickRecord(
        tick=value.tick,
        time=value.time,
        scored=bool(value.scored),
        scored_index=value.scored_index,
        action=ACTION_NAMES[value.action_code],
        scheduled_t0_decision=bool(value.scheduled),
        action_shell=bool(value.shell),
        road_fit_available=bool(value.fit_available),
        selected_template=value.selected_template,
        road_residuals=tuple(value.residuals),
        fit_t1=value.fit_t1,
        fit_t2=value.fit_t2,
        fit_z1=(value.fit_z1x, value.fit_z1y),
        fit_z2=(value.fit_z2x, value.fit_z2y),
        eta_raw=value.eta_raw,
        eta_patch=value.eta_patch,
        patch_position=(value.patch_x, value.patch_y),
        patch_velocity=(value.patch_vx, value.patch_vy),
        effective_road_patch=bool(value.effective),
        target=(value.target_x, value.target_y),
        tangent=(value.tangent_x, value.tangent_y),
        normal=(value.normal_x, value.normal_y),
        zeta=value.zeta,
        wind_tracker=(value.wind_tx, value.wind_ty),
        wind_relay=(value.wind_rx, value.wind_ry),
        tracker_position=(value.pt_x, value.pt_y),
        relay_position=(value.pr_x, value.pr_y),
        estimator_position_pre=(value.xpre_x, value.xpre_y),
        estimator_velocity_pre=(value.vpre_x, value.vpre_y),
        estimator_position=(value.xhat_x, value.xhat_y),
        estimator_velocity=(value.vhat_x, value.vhat_y),
        sensor_visible=bool(value.sensor_visible),
        sensor_observation=observation,
        buffer_count_pre=value.buffer_pre,
        buffer_count_post=value.buffer_post,
        tracker_waypoint=(value.wt_x, value.wt_y),
        relay_waypoint=(value.wr_x, value.wr_y),
        tracking_error=value.tracking_error,
        tracking_valid=bool(value.tracking_valid),
        shadow_tr=value.shadow_tr,
        shadow_rb=value.shadow_rb,
        los_tr=bool(value.los_tr),
        los_rb=bool(value.los_rb),
        margin_tr=value.margin_tr,
        margin_rb=value.margin_rb,
        probability_tr=value.prob_tr,
        probability_rb=value.prob_rb,
        link_uniform_tr=value.link_u_tr,
        link_uniform_rb=value.link_u_rb,
        raw_trial_tr=bool(value.raw_trial_tr),
        raw_trial_rb=bool(value.raw_trial_rb),
        trial_tr=bool(value.trial_tr),
        trial_rb=bool(value.trial_rb),
        packet_valid=bool(value.packet_valid),
        blackout_active=bool(value.blackout),
        lockout_active=bool(value.lockout),
        tracker_energy_before=value.et_before,
        relay_energy_before=value.er_before,
        tracker_energy_after=value.et_after,
        relay_energy_after=value.er_after,
        tracker_air_velocity=(value.at_x, value.at_y),
        relay_air_velocity=(value.ar_x, value.ar_y),
        tracker_ground_velocity=(value.gt_x, value.gt_y),
        relay_ground_velocity=(value.gr_x, value.gr_y),
        tracker_control_index=value.it,
        relay_control_index=value.ir,
        unconstrained_tracker_index=value.uit,
        unconstrained_relay_index=value.uir,
        safety_override=bool(value.safety_override),
        minimum_separation=value.min_separation,
        terrain_distance_tracker_after=value.terrain_t_after,
        terrain_distance_relay_after=value.terrain_r_after,
        terrain_penetration=bool(value.terrain_penetration),
        geofence_exit=bool(value.geofence_exit),
        separation_breach=bool(value.separation_breach),
        service=value.service,
        hard_failure=bool(value.hard_failure),
        no_planner_solution=bool(value.no_planner),
        no_safe_control=bool(value.no_safe),
        numerical_fault=bool(value.numerical_fault),
        battery_exhausted=bool(value.battery),
    )


def run_native_batch(cases: Iterable[FixtureCase]) -> tuple[EncounterResult, ...]:
    materialized = tuple(cases)
    if not materialized:
        return ()
    if len(materialized) > 512:
        raise ValueError("native batch cannot exceed 512 fixture encounters")
    inputs = (_Input * len(materialized))(*(_input(case) for case in materialized))
    outputs = (_Output * len(materialized))()
    library = require_cpp_batched_backend()
    status = library.tbvuus_run_batch(
        inputs,
        len(materialized),
        ctypes.sizeof(_Input),
        outputs,
        ctypes.sizeof(_Output),
    )
    if status != 0:
        raise NativeBackendError(f"native batch execution failed with status {status}")
    results: list[EncounterResult] = []
    for case, output in zip(materialized, outputs):
        results.append(
            EncounterResult(
                spec=case.spec,
                arm=case.arm,
                logical_tag=case.logical_tag,
                ticks=tuple(_tick(output.ticks[index]) for index in range(output.total_ticks)),
                scored_valid_ticks=output.scored_valid,
                scheduled_t0_decisions=output.scheduled,
                action_shells=output.shells,
                road_fit_available_count=output.fit_count,
                effective_road_patch_count=output.effective_count,
                safety_overrides=output.overrides,
                terrain_penetrations=output.terrain_penetrations,
                geofence_exits=output.geofence_exits,
                separation_breaches=output.separation_breaches,
                hard_failure=bool(output.hard_failure),
                no_planner_solution=bool(output.no_planner),
                no_safe_control=bool(output.no_safe),
                numerical_fault=bool(output.numerical_fault),
                battery_exhausted=bool(output.battery),
            )
        )
    return tuple(results)
