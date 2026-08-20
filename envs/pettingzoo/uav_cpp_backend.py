"""Thin, fail-closed loader for the deterministic batched UAV C++ kernel."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import threading
from types import ModuleType
from typing import Final

import numpy as np

from envs.native.cpp_extension_cache import (
    CppExtensionLoadFailed,
    CppExtensionUnavailable,
    load_source_keyed_extension,
    resolve_build_root,
)


_SOURCE: Final[Path] = (
    Path(__file__).resolve().parent / "native" / "uav_geometry_backend.cpp"
)
_BUILD_INTERFACE_VERSION: Final[str] = "ascii_source_stage_v2"
_LOS_PARAMETERS: Final[dict[str, tuple[float, float, float, float]]] = {
    "suburban": (0.1, 7.5e-4, 1.0, 20.0),
    "urban": (0.3, 5e-4, 1.5, 25.0),
    "dense_urban": (0.5, 3e-4, 5.0, 30.0),
}
VALID_RELAY_GEOMETRY_BACKENDS: Final[frozenset[str]] = frozenset(
    {"python_reference", "cpp"}
)
# The native implementation remains explicitly selectable, but each production
# consumer defaults to the reference path until its own complete-environment
# fixed-machine median gate is positive.  The current 31-sample gate was
# semantically exact for all three consumers but slower for each one.
DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND: Final[str] = "python_reference"
DEFAULT_ENERGY_RELAY_GEOMETRY_BACKEND: Final[str] = "python_reference"
DEFAULT_FORCED_RELAY_GEOMETRY_BACKEND: Final[str] = "python_reference"
# Backward-compatible name for routed/progressive consumers.
DEFAULT_RELAY_GEOMETRY_BACKEND: Final[str] = DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND
_WINDOWS_TOOLCHAIN_LOCK: Final[threading.RLock] = threading.RLock()


class UAVCppBackendUnavailable(RuntimeError):
    """Raised when the native backend cannot be built or loaded."""


@dataclass(frozen=True)
class BatchedUAVGeometry:
    next_uav_positions: np.ndarray
    access_path_loss: np.ndarray
    air_path_loss: np.ndarray
    base_path_loss: np.ndarray


def _safe_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def _torch_version() -> str:
    try:
        import torch
    except ImportError as error:  # pragma: no cover - deployment failure path
        raise UAVCppBackendUnavailable(
            "PyTorch is required to build the UAV C++ backend"
        ) from error
    return str(torch.__version__)


def _compiler_flags() -> tuple[str, ...]:
    if os.name == "nt":
        return "/O2", "/std:c++17", "/EHsc", "/fp:precise"
    return "-O3", "-std=c++17", "-ffp-contract=off", "-fno-fast-math"


def _configure_windows_toolchain() -> None:
    if os.name != "nt":
        return
    if shutil.which("cl") is not None and shutil.which("ninja") is not None:
        return
    program_files_x86 = Path(
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    )
    installation = program_files_x86 / "Microsoft Visual Studio" / "2022" / "BuildTools"
    tool_versions = sorted(
        (installation / "VC" / "Tools" / "MSVC").glob("*"), reverse=True
    )
    cl = (
        tool_versions[0] / "bin" / "Hostx64" / "x64" / "cl.exe"
        if tool_versions
        else Path()
    )
    ninja = (
        installation
        / "Common7"
        / "IDE"
        / "CommonExtensions"
        / "Microsoft"
        / "CMake"
        / "Ninja"
        / "ninja.exe"
    )
    if not cl.is_file() or not ninja.is_file():
        raise UAVCppBackendUnavailable(
            "MSVC x64 and Ninja are required at the registered Build Tools path"
        )
    os.environ["PATH"] = os.pathsep.join(
        (str(cl.parent), str(ninja.parent), os.environ.get("PATH", ""))
    )
    if shutil.which("cl") is None or shutil.which("ninja") is None:
        raise UAVCppBackendUnavailable(
            "vcvars64 did not expose the required compiler executables"
        )


@contextmanager
def _windows_toolchain_context():
    """Expose the compiler only while one locked native load is active."""

    if os.name != "nt":
        yield
        return
    with _WINDOWS_TOOLCHAIN_LOCK:
        environment_snapshot = dict(os.environ)
        try:
            _configure_windows_toolchain()
            yield
        finally:
            # Restore PATH/Path and every activation variable, including keys a
            # future vcvars implementation may add.
            os.environ.clear()
            os.environ.update(environment_snapshot)


@lru_cache(maxsize=1)
def _compiler_signature() -> str:
    requested = os.environ.get("CXX") or ("cl" if os.name == "nt" else "c++")
    compiler = shutil.which(requested)
    if compiler is None:
        return "compiler_unavailable"
    path = Path(compiler).resolve()
    version_flag = "/Bv" if os.name == "nt" else "--version"
    try:
        completed = subprocess.run(
            [str(path), version_flag],
            capture_output=True,
            check=False,
            text=True,
            timeout=10.0,
        )
        version_text = completed.stdout + completed.stderr
    except (OSError, subprocess.SubprocessError) as error:
        version_text = f"probe_error={type(error).__name__}"
    stat = path.stat()
    material = "|".join(
        (str(path), str(stat.st_size), str(stat.st_mtime_ns), version_text)
    )
    digest = hashlib.sha256(material.encode("utf-8", errors="replace")).hexdigest()
    return f"{_safe_component(path.stem)}_{digest[:12]}"


def _build_identity() -> str:
    source_digest = hashlib.sha256(_SOURCE.read_bytes()).hexdigest()[:12]
    flags_digest = hashlib.sha256("\0".join(_compiler_flags()).encode()).hexdigest()[:8]
    return "_".join(
        (
            f"py{sys.version_info.major}{sys.version_info.minor}",
            f"torch{_safe_component(_torch_version())}",
            _safe_component(platform.machine() or "unknown_cpu"),
            _safe_component(platform.processor() or "unknown_processor"),
            _safe_component(platform.python_compiler() or "unknown_python_compiler"),
            _compiler_signature(),
            f"flags{flags_digest}",
            _BUILD_INTERFACE_VERSION,
            source_digest,
        )
    )


def load_uav_cpp_backend(
    *, build_root: str | os.PathLike[str] | None = None, verbose: bool = False
) -> ModuleType:
    """Build or reuse the ABI/source-keyed native module outside tracked files."""

    if not _SOURCE.is_file():
        raise UAVCppBackendUnavailable(f"native source is missing: {_SOURCE}")
    with _windows_toolchain_context():
        identity = _build_identity()
        root = resolve_build_root(
            build_root,
            environment_variable="HMASD_UAV_CPP_BUILD_ROOT",
            default_name="hmasd_uav_cpp_extensions",
        )
        module_digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
        try:
            return load_source_keyed_extension(
                cache_namespace="uav_geometry",
                identity=identity,
                root=root,
                build_directory_name=f"build_{module_digest}",
                source=_SOURCE,
                staged_source_name="uav_geometry_backend.cpp",
                module_name=f"hmasd_uav_geometry_{module_digest}",
                compiler_flags=_compiler_flags(),
                verbose=verbose,
            )
        except CppExtensionUnavailable as error:  # pragma: no cover - deployment path
            raise UAVCppBackendUnavailable(
                "torch.utils.cpp_extension is unavailable"
            ) from error
        except CppExtensionLoadFailed as error:
            raise UAVCppBackendUnavailable(
                "failed to build/load the UAV C++ backend; provision the registered "
                "CPU compiler toolchain and inspect the chained build error"
            ) from error


def _require_array(
    name: str,
    value: np.ndarray,
    *,
    dtype: np.dtype,
    rank: int,
    trailing: int | None = None,
) -> np.ndarray:
    if not isinstance(value, np.ndarray):
        raise TypeError(f"{name} must be a numpy.ndarray")
    if value.dtype != dtype:
        raise TypeError(f"{name} must have dtype {dtype}")
    if value.ndim != rank:
        raise ValueError(f"{name} must have rank {rank}")
    if trailing is not None and value.shape[-1] != trailing:
        raise ValueError(f"{name} must end in width {trailing}")
    if not value.flags.c_contiguous:
        raise ValueError(f"{name} must be C-contiguous")
    if np.issubdtype(dtype, np.floating) and not np.isfinite(value).all():
        raise ValueError(f"{name} must contain only finite values")
    return value


def _require_finite_scalar(name: str, value: float) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _validated_geometry_inputs(
    *,
    uav_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    prepared_velocities: np.ndarray,
    movable_mask: np.ndarray,
    time_step: float,
    area_size: float,
    height_range: tuple[float, float],
    carrier_frequency: float,
    environment_type: str,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
    float,
    float,
    float,
    float,
    tuple[float, float, float, float],
]:
    """Validate the shared reference/native geometry boundary once."""

    uavs = _require_array(
        "uav_positions", uav_positions, dtype=np.dtype(np.float64), rank=3, trailing=3
    )
    users = _require_array(
        "user_positions", user_positions, dtype=np.dtype(np.float64), rank=3, trailing=3
    )
    bases = _require_array(
        "ground_bs_positions",
        ground_bs_positions,
        dtype=np.dtype(np.float64),
        rank=3,
        trailing=3,
    )
    velocities = _require_array(
        "prepared_velocities",
        prepared_velocities,
        dtype=np.dtype(np.float32),
        rank=3,
        trailing=3,
    )
    mask = _require_array(
        "movable_mask", movable_mask, dtype=np.dtype(np.bool_), rank=2
    )
    batch, uav_count, _ = uavs.shape
    if users.shape[0] != batch or bases.shape[0] != batch:
        raise ValueError("all position arrays must share the batch dimension")
    if velocities.shape[:2] != (batch, uav_count) or mask.shape != (
        batch,
        uav_count,
    ):
        raise ValueError("velocity/mask dimensions must match the UAV batch")
    if environment_type not in _LOS_PARAMETERS:
        raise ValueError("environment_type must be suburban, urban, or dense_urban")
    if len(height_range) != 2:
        raise ValueError("height_range must contain exactly two bounds")

    dt = _require_finite_scalar("time_step", time_step)
    area = _require_finite_scalar("area_size", area_size)
    minimum_height = _require_finite_scalar("height_range[0]", height_range[0])
    maximum_height = _require_finite_scalar("height_range[1]", height_range[1])
    frequency = _require_finite_scalar("carrier_frequency", carrier_frequency)
    if dt <= 0.0 or area <= 0.0 or frequency <= 0.0:
        raise ValueError("time_step, area_size, and carrier_frequency must be positive")
    if minimum_height > maximum_height:
        raise ValueError("height_range lower bound exceeds upper bound")
    return (
        uavs,
        users,
        bases,
        velocities,
        mask,
        dt,
        area,
        minimum_height,
        maximum_height,
        frequency,
        _LOS_PARAMETERS[environment_type],
    )


def step_geometry_reference_batch(
    *,
    uav_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    prepared_velocities: np.ndarray,
    movable_mask: np.ndarray,
    time_step: float,
    area_size: float,
    height_range: tuple[float, float],
    carrier_frequency: float,
    environment_type: str,
) -> BatchedUAVGeometry:
    """Exact Python oracle for the deterministic native geometry contract."""

    (
        uavs,
        users,
        bases,
        velocities,
        mask,
        dt,
        area,
        minimum_height,
        maximum_height,
        frequency,
        los_parameters,
    ) = _validated_geometry_inputs(
        uav_positions=uav_positions,
        user_positions=user_positions,
        ground_bs_positions=ground_bs_positions,
        prepared_velocities=prepared_velocities,
        movable_mask=movable_mask,
        time_step=time_step,
        area_size=area_size,
        height_range=height_range,
        carrier_frequency=carrier_frequency,
        environment_type=environment_type,
    )
    los_a, los_b, eta_los, eta_nlos = los_parameters
    next_uavs = uavs.copy()
    time_step_f32 = np.float32(dt)
    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            if mask[batch_index, uav_index]:
                next_uavs[batch_index, uav_index] += (
                    velocities[batch_index, uav_index] * time_step_f32
                ).astype(np.float64)
            next_uavs[batch_index, uav_index, 0] = np.clip(
                next_uavs[batch_index, uav_index, 0], 0.0, area
            )
            next_uavs[batch_index, uav_index, 1] = np.clip(
                next_uavs[batch_index, uav_index, 1], 0.0, area
            )
            next_uavs[batch_index, uav_index, 2] = np.clip(
                next_uavs[batch_index, uav_index, 2], minimum_height, maximum_height
            )

    access = np.empty(
        (uavs.shape[0], uavs.shape[1], users.shape[1]), dtype=np.float64
    )
    air = np.empty(
        (uavs.shape[0], uavs.shape[1], uavs.shape[1]), dtype=np.float64
    )
    base = np.empty(
        (uavs.shape[0], uavs.shape[1], bases.shape[1]), dtype=np.float64
    )

    frequency_term = 20.0 * np.log10(frequency)

    def a2g(airborne: np.ndarray, ground: np.ndarray) -> float:
        delta = airborne - ground
        distance_3d = np.sqrt(np.sum(delta**2))
        distance_2d = np.sqrt(delta[0] ** 2 + delta[1] ** 2)
        safe_distance_3d = max(distance_3d, 1.0e-6)
        safe_distance_2d = max(distance_2d, 1.0e-6)
        elevation = np.degrees(np.arctan(abs(delta[2]) / safe_distance_2d))
        p_los = 1.0 / (1.0 + los_a * np.exp(-los_b * (elevation - los_a)))
        p_los = np.clip(p_los, 0.0, 1.0)
        fspl = 20.0 * np.log10(safe_distance_3d) + frequency_term - 147.55
        los_linear = 10.0 ** (-(fspl + eta_los) / 10.0)
        nlos_linear = 10.0 ** (-(fspl + eta_nlos) / 10.0)
        return float(-10.0 * np.log10(p_los * los_linear + (1.0 - p_los) * nlos_linear))

    def a2a(first: np.ndarray, second: np.ndarray) -> float:
        distance = np.sqrt(np.sum((first - second) ** 2))
        return float(20.0 * np.log10(max(distance, 1.0e-6)) + frequency_term - 147.55)

    for batch_index in range(uavs.shape[0]):
        for uav_index in range(uavs.shape[1]):
            airborne = next_uavs[batch_index, uav_index]
            for user_index in range(users.shape[1]):
                access[batch_index, uav_index, user_index] = a2g(
                    airborne, users[batch_index, user_index]
                )
            for peer_index in range(uavs.shape[1]):
                air[batch_index, uav_index, peer_index] = a2a(
                    airborne, next_uavs[batch_index, peer_index]
                )
            for base_index in range(bases.shape[1]):
                base[batch_index, uav_index, base_index] = a2g(
                    airborne, bases[batch_index, base_index]
                )
    return BatchedUAVGeometry(next_uavs, access, air, base)


def step_relay_geometry_batch(*, backend: str, **kwargs) -> BatchedUAVGeometry:
    """Dispatch one explicit geometry implementation without fallback."""

    selected = str(backend)
    if selected == "python_reference":
        return step_geometry_reference_batch(**kwargs)
    if selected == "cpp":
        return step_geometry_batch(**kwargs)
    raise ValueError(
        f"unknown relay geometry backend {selected!r}; expected one of "
        f"{sorted(VALID_RELAY_GEOMETRY_BACKENDS)}"
    )


def step_geometry_batch(
    *,
    uav_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    prepared_velocities: np.ndarray,
    movable_mask: np.ndarray,
    time_step: float,
    area_size: float,
    height_range: tuple[float, float],
    carrier_frequency: float,
    environment_type: str,
    build_root: str | os.PathLike[str] | None = None,
) -> BatchedUAVGeometry:
    """Execute one stateless batch geometry step without implicit conversions."""

    (
        uavs,
        users,
        bases,
        velocities,
        mask,
        dt,
        area,
        minimum_height,
        maximum_height,
        frequency,
        los_parameters,
    ) = _validated_geometry_inputs(
        uav_positions=uav_positions,
        user_positions=user_positions,
        ground_bs_positions=ground_bs_positions,
        prepared_velocities=prepared_velocities,
        movable_mask=movable_mask,
        time_step=time_step,
        area_size=area_size,
        height_range=height_range,
        carrier_frequency=carrier_frequency,
        environment_type=environment_type,
    )
    batch, uav_count, _ = uavs.shape
    los_a, los_b, eta_los, eta_nlos = los_parameters
    module = load_uav_cpp_backend(build_root=build_root)
    raw = module.step_geometry_batch(
        uavs,
        users,
        bases,
        velocities,
        mask,
        dt,
        area,
        minimum_height,
        maximum_height,
        frequency,
        los_a,
        los_b,
        eta_los,
        eta_nlos,
    )
    if not isinstance(raw, tuple) or len(raw) != 4:
        raise RuntimeError("native geometry backend returned an invalid payload")
    expected = (
        ((batch, uav_count, 3), np.dtype(np.float64)),
        ((batch, uav_count, users.shape[1]), np.dtype(np.float64)),
        ((batch, uav_count, uav_count), np.dtype(np.float64)),
        ((batch, uav_count, bases.shape[1]), np.dtype(np.float64)),
    )
    checked: list[np.ndarray] = []
    for index, (value, (shape, dtype)) in enumerate(zip(raw, expected)):
        if not isinstance(value, np.ndarray):
            raise RuntimeError(f"native output {index} is not a numpy.ndarray")
        if value.shape != shape or value.dtype != dtype or not value.flags.c_contiguous:
            raise RuntimeError(f"native output {index} violated shape/dtype/layout")
        if not np.isfinite(value).all():
            raise RuntimeError(f"native output {index} contains non-finite values")
        checked.append(value)
    return BatchedUAVGeometry(*checked)
