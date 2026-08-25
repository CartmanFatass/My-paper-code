"""Source-keyed ctypes binding for the batched C++ HEADLAND-90 backend.

There is intentionally no Python fallback in this module.  Compilation,
loading, ABI, or execution failures are surfaced to the caller.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Iterable

from .config import (
    FIXTURE_NAMESPACE,
    MAX_STATES,
    MAX_TICKS,
    ControllerSpec,
    EncounterSpec,
    FixtureTape,
    RouteClass,
)
from .coordinates import production_activity_permitted
from .host import EncounterResult, TickRecord

_SOURCE = Path(__file__).with_name("native") / "headland90_backend.cpp"
_EVENT_HEADER = _SOURCE.with_name("event_transform_table.h")
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
        ("route_class", ctypes.c_int), ("direction", ctypes.c_int),
        ("lateral", ctypes.c_int), ("policy_kind", ctypes.c_int),
        ("alpha_s", ctypes.c_int), ("alpha_l", ctypes.c_int),
        ("beta_s", ctypes.c_int), ("beta_l", ctypes.c_int),
        ("gamma_s", ctypes.c_int), ("gamma_l", ctypes.c_int),
        ("explicit_num", ctypes.c_int64 * 128),
        ("explicit_den", ctypes.c_int64 * 128),
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
        ("action", ctypes.c_double * MAX_TICKS),
    ]


class _Tick(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_int) for name in (
            "tick", "scored", "scored_index", "action_code",
            "legal_opportunity", "action_consumed",
        )
    ] + [
        ("rate_num", ctypes.c_int64), ("rate_den", ctypes.c_int64),
    ] + [
        (name, ctypes.c_double) for name in (
            "time", "action_uniform", "rate_q", "event_lambda",
            "event_probability", "eligible_time", "target_x", "target_y",
            "tangent_x", "tangent_y", "normal_x", "normal_y", "zeta",
            "wind_t_x", "wind_t_y", "wind_r_x", "wind_r_y",
            "pt_x", "pt_y", "pr_x", "pr_y", "xhat_x", "xhat_y",
            "vhat_x", "vhat_y",
        )
    ] + [
        ("sensor_visible", ctypes.c_int),
        ("sensor_x", ctypes.c_double), ("sensor_y", ctypes.c_double),
        ("buffer_count", ctypes.c_int),
    ] + [
        (name, ctypes.c_double) for name in (
            "wt_x", "wt_y", "wr_x", "wr_y", "tracking_error",
        )
    ] + [
        ("tracking_valid", ctypes.c_int),
        ("shadow_tr", ctypes.c_double), ("shadow_rb", ctypes.c_double),
        ("los_tr", ctypes.c_int), ("los_rb", ctypes.c_int),
    ] + [
        (name, ctypes.c_double) for name in (
            "margin_tr", "margin_rb", "prob_tr", "prob_rb", "link_u_tr", "link_u_rb",
        )
    ] + [
        (name, ctypes.c_int) for name in (
            "raw_trial_tr", "raw_trial_rb", "trial_tr", "trial_rb",
            "packet_valid", "blackout", "lockout",
        )
    ] + [
        (name, ctypes.c_double) for name in (
            "et_before", "er_before", "et_after", "er_after", "at_x", "at_y",
            "ar_x", "ar_y", "gt_x", "gt_y", "gr_x", "gr_y",
        )
    ] + [
        (name, ctypes.c_int) for name in (
            "it", "ir", "uit", "uir", "safety_override",
        )
    ] + [
        ("min_separation", ctypes.c_double),
        ("terrain_t_after", ctypes.c_double), ("terrain_r_after", ctypes.c_double),
    ] + [
        (name, ctypes.c_int) for name in (
            "terrain_penetration", "geofence_exit", "separation_breach",
            "service", "hard_failure", "no_planner", "no_safe", "battery",
        )
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_int) for name in (
            "total_ticks", "scored_valid", "updates", "keeps", "opportunities",
            "overrides", "hard_failure", "no_planner", "no_safe", "battery",
        )
    ] + [("ticks", _Tick * MAX_TICKS)]


def source_sha256() -> str:
    digest = hashlib.sha256()
    for path in (_SOURCE, _EVENT_HEADER):
        encoded_name = path.name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(4, "big"))
        digest.update(encoded_name)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _vs_installation() -> Path:
    vswhere = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [str(vswhere), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        check=True,
        capture_output=True,
        text=True,
    )
    path = Path(result.stdout.strip())
    if not path.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return path


def _compiler_path() -> Path:
    tools_root = _vs_installation() / "VC" / "Tools" / "MSVC"
    candidates = tuple(
        path for path in tools_root.glob("*/bin/Hostx64/x64/cl.exe") if path.is_file()
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
    version = subprocess.run(
        [str(compiler)], capture_output=True, text=True, check=False
    )
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
    return {
        **identity,
        "compile_flags": list(identity["compile_flags"]),  # type: ignore[arg-type]
    }


@functools.lru_cache(maxsize=1)
def native_build_key() -> str:
    toolchain = native_toolchain_identity()
    digest = hashlib.sha256()
    digest.update(b"ONLGR-HEADLAND90-NATIVE-BUILD-v1\0")
    digest.update(source_sha256().encode("ascii"))
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        encoded = flag.encode("ascii")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
    digest.update(NATIVE_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest()


def _compiled_path() -> Path:
    digest = native_build_key()
    cache = Path(tempfile.gettempdir()) / "hmasd_headland90_native" / digest
    dll = cache / "headland90_backend.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    obj = cache / "headland90_backend.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'"{_SOURCE}" /Fo:"{obj}" /link /OUT:"{dll}"'
    )
    result = subprocess.run(
        command,
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=cache,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not dll.is_file():
        raise NativeBackendError(
            f"native backend compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return dll


@functools.lru_cache(maxsize=1)
def require_cpp_batched_backend() -> ctypes.CDLL:
    """Compile/load the exact source-keyed backend or raise; never fall back."""
    library = ctypes.CDLL(str(_compiled_path()))
    library.headland90_abi_version.argtypes = []
    library.headland90_abi_version.restype = ctypes.c_int
    if library.headland90_abi_version() != NATIVE_ABI_VERSION:
        raise NativeBackendError("native backend ABI mismatch")
    library.headland90_run_batch.argtypes = [
        ctypes.POINTER(_Input), ctypes.c_int, ctypes.POINTER(_Output)
    ]
    library.headland90_run_batch.restype = ctypes.c_int
    library.headland90_event_transform.argtypes = [
        ctypes.c_int64, ctypes.c_int64,
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
    ]
    library.headland90_event_transform.restype = ctypes.c_int
    return library


def native_artifact_identity() -> dict[str, object]:
    """Build/load preactivity identity without executing a host transition."""
    path = (
        Path(tempfile.gettempdir())
        / "hmasd_headland90_native"
        / native_build_key()
        / "headland90_backend.dll"
    )
    cache_present_before = path.is_file()
    started = time.perf_counter()
    library = require_cpp_batched_backend()
    elapsed = time.perf_counter() - started
    if library.headland90_abi_version() != NATIVE_ABI_VERSION or not path.is_file():
        raise NativeBackendError("native artifact identity failed ABI/path verification")
    stat = path.stat()
    return {
        "artifact_path": str(path.resolve()),
        "artifact_sha256": _sha256_file(path),
        "artifact_size": stat.st_size,
        "artifact_mtime_ns": stat.st_mtime_ns,
        "build_key": native_build_key(),
        "abi_version": NATIVE_ABI_VERSION,
        "python_fallback": False,
        "first_compile_seconds": None if cache_present_before else elapsed,
        "compile_time_status": "cache_present_unknown" if cache_present_before else "measured_first_compile",
    }


def production_preflight() -> ctypes.CDLL:
    """Future production-facing loader; activity is fenced in this stage."""
    library = require_cpp_batched_backend()
    if not production_activity_permitted():
        raise PermissionError("HEADLAND-90 production activity is not authorized")
    return library


def native_event_transform_bits(q) -> tuple[int, int]:
    """Return the exact native table bits for one frozen rational rate."""
    from fractions import Fraction

    exact = Fraction(q)
    lambda_bits, event_bits = ctypes.c_uint64(), ctypes.c_uint64()
    status = require_cpp_batched_backend().headland90_event_transform(
        exact.numerator, exact.denominator,
        ctypes.byref(lambda_bits), ctypes.byref(event_bits),
    )
    if status != 0:
        raise NativeBackendError(f"native event transform failed with status {status}")
    return lambda_bits.value, event_bits.value


def _input(spec: EncounterSpec, tape: FixtureTape, controller: ControllerSpec) -> _Input:
    if spec.namespace != FIXTURE_NAMESPACE:
        raise PermissionError("native conformance execution requires the fixture namespace")
    item = _Input()
    item.route_class = 0 if spec.route_class is RouteClass.SHORT else 1
    item.direction, item.lateral = spec.direction, spec.lateral_offset
    item.policy_kind = int(controller.explicit is not None)
    item.alpha_s, item.alpha_l = controller.alpha_short, controller.alpha_long
    item.beta_s, item.beta_l = controller.beta_short, controller.beta_long
    item.gamma_s, item.gamma_l = controller.gamma_short, controller.gamma_long
    if controller.explicit is not None:
        if len(controller.explicit) != spec.route_class.scored_ticks:
            raise ValueError("explicit rate tape length does not match route")
        for index, rate in enumerate(controller.explicit):
            item.explicit_num[index], item.explicit_den[index] = rate.numerator, rate.denominator
    for index in range(spec.total_ticks + 1):
        item.target[index] = tape.target_lateral[index]
        item.wind_tx[index], item.wind_ty[index] = tape.wind_t[index]
        item.wind_rx[index], item.wind_ry[index] = tape.wind_r[index]
        item.sensor_x[index], item.sensor_y[index] = tape.sensor[index]
        item.shadow_tr[index], item.shadow_rb[index] = tape.shadow_tr[index], tape.shadow_rb[index]
    for index in range(spec.total_ticks):
        item.link_tr[index], item.link_rb[index] = tape.link_tr[index], tape.link_rb[index]
        item.action[index] = tape.action[index]
    return item


def _record(tick: _Tick) -> TickRecord:
    actions = ("KEEP", "BOOT", "JOINT-UPDATE")
    observation = (tick.sensor_x, tick.sensor_y) if tick.sensor_visible else None
    return TickRecord(
        tick=tick.tick, time=tick.time, scored=bool(tick.scored), scored_index=tick.scored_index,
        action=actions[tick.action_code], legal_opportunity=bool(tick.legal_opportunity),
        action_uniform_consumed=bool(tick.action_consumed), action_uniform=tick.action_uniform,
        rate_numerator=tick.rate_num, rate_denominator=tick.rate_den, rate_q=tick.rate_q,
        event_lambda=tick.event_lambda, event_probability=tick.event_probability,
        eligible_time=tick.eligible_time, target=(tick.target_x, tick.target_y),
        tangent=(tick.tangent_x, tick.tangent_y), normal=(tick.normal_x, tick.normal_y),
        zeta=tick.zeta, wind_tracker=(tick.wind_t_x, tick.wind_t_y),
        wind_relay=(tick.wind_r_x, tick.wind_r_y),
        tracker_position=(tick.pt_x, tick.pt_y), relay_position=(tick.pr_x, tick.pr_y),
        estimator_position=(tick.xhat_x, tick.xhat_y), estimator_velocity=(tick.vhat_x, tick.vhat_y),
        sensor_visible=bool(tick.sensor_visible), sensor_observation=observation,
        buffer_count=tick.buffer_count, tracker_waypoint=(tick.wt_x, tick.wt_y),
        relay_waypoint=(tick.wr_x, tick.wr_y), tracking_error=tick.tracking_error,
        tracking_valid=bool(tick.tracking_valid), shadow_tr=tick.shadow_tr, shadow_rb=tick.shadow_rb,
        los_tr=bool(tick.los_tr), los_rb=bool(tick.los_rb), margin_tr=tick.margin_tr,
        margin_rb=tick.margin_rb, probability_tr=tick.prob_tr, probability_rb=tick.prob_rb,
        link_uniform_tr=tick.link_u_tr, link_uniform_rb=tick.link_u_rb,
        raw_trial_tr=bool(tick.raw_trial_tr), raw_trial_rb=bool(tick.raw_trial_rb),
        trial_tr=bool(tick.trial_tr), trial_rb=bool(tick.trial_rb), packet_valid=bool(tick.packet_valid),
        blackout_active=bool(tick.blackout), lockout_active=bool(tick.lockout),
        tracker_energy_before=tick.et_before, relay_energy_before=tick.er_before,
        tracker_energy_after=tick.et_after, relay_energy_after=tick.er_after,
        tracker_air_velocity=(tick.at_x, tick.at_y), relay_air_velocity=(tick.ar_x, tick.ar_y),
        tracker_ground_velocity=(tick.gt_x, tick.gt_y), relay_ground_velocity=(tick.gr_x, tick.gr_y),
        tracker_control_index=tick.it, relay_control_index=tick.ir,
        unconstrained_tracker_index=tick.uit, unconstrained_relay_index=tick.uir,
        safety_override=bool(tick.safety_override), minimum_separation=tick.min_separation,
        terrain_distance_tracker_after=tick.terrain_t_after,
        terrain_distance_relay_after=tick.terrain_r_after, service=tick.service,
        terrain_penetration=bool(tick.terrain_penetration),
        geofence_exit=bool(tick.geofence_exit), separation_breach=bool(tick.separation_breach),
        hard_failure=bool(tick.hard_failure), no_planner_solution=bool(tick.no_planner),
        no_safe_control=bool(tick.no_safe), battery_exhausted=bool(tick.battery),
    )


def run_native_batch(
    fixtures: Iterable[tuple[EncounterSpec, FixtureTape, ControllerSpec, str]],
) -> tuple[EncounterResult, ...]:
    """Run explicit fixtures through the C++ reset-to-terminal batch kernel."""
    materialized = tuple(fixtures)
    if not materialized:
        return ()
    inputs = (_Input * len(materialized))(
        *(_input(spec, tape, controller) for spec, tape, controller, _ in materialized)
    )
    outputs = (_Output * len(materialized))()
    library = require_cpp_batched_backend()
    status = library.headland90_run_batch(inputs, len(materialized), outputs)
    if status != 0:
        raise NativeBackendError(f"native batch execution failed with status {status}")
    results: list[EncounterResult] = []
    for (spec, _, _, tag), output in zip(materialized, outputs):
        results.append(
            EncounterResult(
                spec=spec, logical_tag=tag,
                ticks=tuple(_record(output.ticks[index]) for index in range(output.total_ticks)),
                scored_valid_ticks=output.scored_valid, voluntary_updates=output.updates,
                voluntary_keeps=output.keeps, opportunity_rows=output.opportunities,
                safety_overrides=output.overrides, hard_failure=bool(output.hard_failure),
                no_planner_solution=bool(output.no_planner), no_safe_control=bool(output.no_safe),
                battery_exhausted=bool(output.battery),
            )
        )
    return tuple(results)
