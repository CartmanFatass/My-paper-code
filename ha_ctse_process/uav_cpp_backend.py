"""Thin, fail-closed loader for the deterministic batched UAV C++ kernel."""

from __future__ import annotations

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
import tempfile
from types import ModuleType
from typing import Final

import numpy as np


_SOURCE: Final[Path] = (
    Path(__file__).resolve().parent / "native" / "uav_geometry_backend.cpp"
)
_BUILD_INTERFACE_VERSION: Final[str] = "communication_kernel_v1"
_LOS_PARAMETERS: Final[dict[str, tuple[float, float, float, float]]] = {
    "suburban": (0.1, 7.5e-4, 1.0, 20.0),
    "urban": (0.3, 5e-4, 1.5, 25.0),
    "dense_urban": (0.5, 3e-4, 5.0, 30.0),
}
_LOADED_MODULES: dict[tuple[str, str], ModuleType] = {}


class UAVCppBackendUnavailable(RuntimeError):
    """Raised when the native backend cannot be built or loaded."""


@dataclass(frozen=True)
class UAVCommunicationBatch:
    access_path_loss: np.ndarray
    air_path_loss: np.ndarray
    base_path_loss: np.ndarray
    user_ipn_dbm: np.ndarray
    uav_uav_ipn_dbm: np.ndarray
    uav_bs_ipn_dbm: np.ndarray
    bs_uav_ipn_dbm: np.ndarray
    cap_uav_uav: np.ndarray
    cap_uav_bs: np.ndarray
    cap_bs_uav: np.ndarray


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


@lru_cache(maxsize=1)
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
        (str(cl.parent), str(ninja.parent), os.environ["PATH"])
    )
    if shutil.which("cl") is None or shutil.which("ninja") is None:
        raise UAVCppBackendUnavailable(
            "vcvars64 did not expose the required compiler executables"
        )


@lru_cache(maxsize=1)
def _compiler_signature() -> str:
    _configure_windows_toolchain()
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


@lru_cache(maxsize=1)
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


def _default_build_root() -> Path:
    configured = os.environ.get("HMASD_UAV_CPP_BUILD_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / "hmasd_uav_cpp_extensions"


def load_uav_cpp_backend(
    *, build_root: str | os.PathLike[str] | None = None, verbose: bool = False
) -> ModuleType:
    """Build or reuse the ABI/source-keyed native module outside tracked files."""

    if not _SOURCE.is_file():
        raise UAVCppBackendUnavailable(f"native source is missing: {_SOURCE}")
    _configure_windows_toolchain()
    identity = _build_identity()
    root = (
        Path(build_root).expanduser().resolve()
        if build_root is not None
        else _default_build_root()
    )
    cache_key = identity, str(root)
    cached = _LOADED_MODULES.get(cache_key)
    if cached is not None:
        return cached

    try:
        from torch.utils.cpp_extension import load
    except (ImportError, OSError) as error:  # pragma: no cover - deployment path
        raise UAVCppBackendUnavailable(
            "torch.utils.cpp_extension is unavailable"
        ) from error

    module_digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    build_directory = root / f"build_{module_digest}"
    build_directory.mkdir(parents=True, exist_ok=True)
    staged_source = build_directory / "uav_geometry_backend.cpp"
    source_bytes = _SOURCE.read_bytes()
    if not staged_source.exists() or staged_source.read_bytes() != source_bytes:
        staged_source.write_bytes(source_bytes)
    module_name = f"hmasd_uav_geometry_{module_digest}"
    compiler_flags = list(_compiler_flags())
    try:
        module = load(
            name=module_name,
            sources=[str(staged_source)],
            extra_cflags=compiler_flags,
            build_directory=str(build_directory),
            with_cuda=False,
            is_python_module=True,
            verbose=verbose,
        )
    except Exception as error:  # cpp_extension exposes several toolchain errors
        raise UAVCppBackendUnavailable(
            "failed to build/load the UAV C++ backend; provision the registered "
            "CPU compiler toolchain and inspect the chained build error"
        ) from error
    _LOADED_MODULES[cache_key] = module
    return module


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


def _require_mcs_array(name: str, value: np.ndarray, *, rank: int) -> np.ndarray:
    """Like `_require_array`, except +infinity is legal, not just finite.

    `env.mcs_table`'s last row is `(float('inf'), se)` by design -- it is the
    catch-all bucket the first-match scan falls into for every SINR that
    cleared every real threshold. Rejecting it here would make the one
    threshold array this kernel is required to accept (per the frozen spec,
    split "in table order" straight out of `env.mcs_table`) permanently
    un-passable, which would make `step_communication_batch` uncallable
    rather than merely declining. NaN and -infinity remain rejected: neither
    is a value this table ever legitimately carries.
    """

    if not isinstance(value, np.ndarray):
        raise TypeError(f"{name} must be a numpy.ndarray")
    if value.dtype != np.dtype(np.float64):
        raise TypeError(f"{name} must have dtype float64")
    if value.ndim != rank:
        raise ValueError(f"{name} must have rank {rank}")
    if not value.flags.c_contiguous:
        raise ValueError(f"{name} must be C-contiguous")
    legal = np.isfinite(value) | (value == np.inf)
    if not legal.all():
        raise ValueError(f"{name} must contain only finite values or +inf")
    return value


def _require_finite_scalar(name: str, value: float) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def step_communication_batch(
    *,
    uav_positions: np.ndarray,
    user_positions: np.ndarray,
    ground_bs_positions: np.ndarray,
    carrier_frequency: float,
    environment_type: str,
    tx_power: float,
    ground_bs_tx_power: float,
    noise_power_linear_mw: float,
    interference_radius: float,
    use_fdma: bool,
    aclr_linear: float,
    bandwidth: float,
    min_sinr: float,
    mcs_thresholds: np.ndarray,
    mcs_efficiencies: np.ndarray,
    build_root: str | os.PathLike[str] | None = None,
) -> UAVCommunicationBatch:
    """Execute one stateless batch communication step without implicit conversions."""

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
    thresholds = _require_mcs_array("mcs_thresholds", mcs_thresholds, rank=1)
    efficiencies = _require_array(
        "mcs_efficiencies", mcs_efficiencies, dtype=np.dtype(np.float64), rank=1
    )
    batch, uav_count, _ = uavs.shape
    if users.shape[0] != batch or bases.shape[0] != batch:
        raise ValueError("all position arrays must share the batch dimension")
    if environment_type not in _LOS_PARAMETERS:
        raise ValueError(
            "environment_type must be suburban, urban, or dense_urban"
        )
    if thresholds.shape[0] < 1 or thresholds.shape != efficiencies.shape:
        raise ValueError(
            "mcs_thresholds and mcs_efficiencies must share one non-empty length"
        )

    frequency = _require_finite_scalar("carrier_frequency", carrier_frequency)
    tx = _require_finite_scalar("tx_power", tx_power)
    ground_bs_tx = _require_finite_scalar("ground_bs_tx_power", ground_bs_tx_power)
    noise_linear = _require_finite_scalar(
        "noise_power_linear_mw", noise_power_linear_mw
    )
    radius = _require_finite_scalar("interference_radius", interference_radius)
    aclr = _require_finite_scalar("aclr_linear", aclr_linear)
    band = _require_finite_scalar("bandwidth", bandwidth)
    min_sinr_value = _require_finite_scalar("min_sinr", min_sinr)
    if frequency <= 0.0:
        raise ValueError("carrier_frequency must be positive")

    los_a, los_b, eta_los, eta_nlos = _LOS_PARAMETERS[environment_type]
    module = load_uav_cpp_backend(build_root=build_root)
    raw = module.step_communication_batch(
        uavs,
        users,
        bases,
        frequency,
        los_a,
        los_b,
        eta_los,
        eta_nlos,
        tx,
        ground_bs_tx,
        noise_linear,
        radius,
        bool(use_fdma),
        aclr,
        band,
        min_sinr_value,
        thresholds,
        efficiencies,
    )
    if not isinstance(raw, tuple) or len(raw) != 10:
        raise RuntimeError("native communication backend returned an invalid payload")
    expected = (
        ((batch, uav_count, users.shape[1]), np.dtype(np.float64)),
        ((batch, uav_count, uav_count), np.dtype(np.float64)),
        ((batch, uav_count, bases.shape[1]), np.dtype(np.float64)),
        ((batch, uav_count, users.shape[1]), np.dtype(np.float64)),
        ((batch, uav_count, uav_count), np.dtype(np.float64)),
        ((batch, uav_count, bases.shape[1]), np.dtype(np.float64)),
        ((batch, uav_count), np.dtype(np.float64)),
        ((batch, uav_count, uav_count), np.dtype(np.float64)),
        ((batch, uav_count, bases.shape[1]), np.dtype(np.float64)),
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
    return UAVCommunicationBatch(*checked)
