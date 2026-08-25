"""Source/runtime-ABI/build-root keyed loader for the UCOPE r03 C++ S1 host.

Python validates and marshals contiguous arrays and owns TEST lifecycle calls.
Every environment transition, counter draw, component, and terminal value is
computed by the native library; there is deliberately no Python fallback.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Final

import numpy as np

from .contract import (
    BASELINE_FEATURES,
    NATIVE_ABI_VERSION,
    NATIVE_HOST_KIND,
    ROOT_ACTION_COUNT,
    SCORER_FEATURES,
    SUPPORTED_BATCH_WIDTHS,
    TAIL_ACTION_COUNT,
    require_supported_width,
)


_SOURCE: Final[Path] = Path(__file__).with_name("native") / "ucope_r01_r03_backend.cpp"
_DEFAULT_BUILD_ROOT: Final[Path] = Path(tempfile.gettempdir()) / "hmasd_ucope_r01_r03_native"
_LOCK = threading.Lock()
_LIBRARIES: dict[tuple[str, str], ctypes.CDLL] = {}
_IDENTITIES: dict[tuple[str, str], dict[str, object]] = {}


class NativeBackendError(RuntimeError):
    """The source-bound UCOPE native boundary rejected an input or lifecycle."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _merge_environment(output: str) -> None:
    existing = {name.casefold(): name for name in os.environ}
    imported: set[str] = set()
    for line in output.splitlines():
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        folded = name.casefold()
        if not name or folded in imported:
            continue
        imported.add(folded)
        os.environ[existing.get(folded, name)] = value


@functools.lru_cache(maxsize=1)
def _compiler() -> Path:
    candidate = shutil.which("cl" if os.name == "nt" else "c++")
    if candidate:
        return Path(candidate).resolve(strict=True)
    if os.name != "nt":
        raise NativeBackendError("a C++ compiler is unavailable")
    scripts = (
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"),
    )
    script = next((item for item in scripts if item.is_file()), None)
    if script is None:
        raise NativeBackendError("the MSVC x64 environment script is unavailable")
    completed = subprocess.run(
        f'call "{script}" >nul && set',
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        shell=True,
        executable=os.environ.get("COMSPEC", "cmd.exe"),
    )
    _merge_environment(completed.stdout)
    candidate = shutil.which("cl")
    if candidate is None:
        raise NativeBackendError("the MSVC environment did not expose cl.exe")
    return Path(candidate).resolve(strict=True)


def _compiler_flags() -> tuple[str, ...]:
    if os.name == "nt":
        return ("/O2", "/std:c++17", "/EHsc", "/fp:precise", "/LD")
    return ("-O3", "-std=c++17", "-ffp-contract=off", "-fno-fast-math", "-shared", "-fPIC")


def _runtime_abi() -> dict[str, object]:
    return {
        "abi_version": NATIVE_ABI_VERSION,
        "host_kind": NATIVE_HOST_KIND,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "machine": platform.machine(),
        "pointer_bytes": ctypes.sizeof(ctypes.c_void_p),
        "numpy_version": np.__version__,
        "supported_widths": list(SUPPORTED_BATCH_WIDTHS),
    }


@functools.lru_cache(maxsize=1)
def _build_key() -> str:
    compiler = _compiler()
    payload = {
        "schema": "UCOPE_R01_R03_NATIVE_BUILD_KEY_V1",
        "source_sha256": _sha256(_SOURCE),
        "compiler_path": str(compiler),
        "compiler_sha256": _sha256(compiler),
        "compiler_flags": list(_compiler_flags()),
        "runtime_abi": _runtime_abi(),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _compile(build_root: Path, build_key: str) -> Path:
    directory = build_root / build_key
    suffix = ".dll" if os.name == "nt" else ".so"
    artifact = directory / f"ucope_r01_r03_backend{suffix}"
    if artifact.is_file():
        return artifact
    directory.mkdir(parents=True, exist_ok=True)
    unique = f"{os.getpid()}_{time.time_ns()}"
    staged = directory / f"ucope_r01_r03_backend_{unique}{suffix}"
    compiler = _compiler()
    if os.name == "nt":
        object_path = directory / f"ucope_r01_r03_backend_{unique}.obj"
        command = [
            str(compiler),
            *_compiler_flags(),
            str(_SOURCE),
            f"/Fo:{object_path}",
            f"/Fe:{staged}",
        ]
    else:
        object_path = None
        command = [str(compiler), *_compiler_flags(), str(_SOURCE), "-o", str(staged)]
    completed = subprocess.run(
        command,
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        if completed.returncode != 0 or not staged.is_file():
            raise NativeBackendError(
                "UCOPE native compilation failed "
                f"({completed.returncode}):\n{completed.stdout}\n{completed.stderr}"
            )
        try:
            os.replace(staged, artifact)
        except OSError:
            if not artifact.is_file():
                raise
    finally:
        staged.unlink(missing_ok=True)
        if object_path is not None:
            object_path.unlink(missing_ok=True)
    return artifact


def _pointer(array: np.ndarray, ctype: type[ctypes._SimpleCData]) -> object:
    return array.ctypes.data_as(ctypes.POINTER(ctype))


def _configure(library: ctypes.CDLL) -> ctypes.CDLL:
    library.ucope_r01_r03_abi_version.argtypes = []
    library.ucope_r01_r03_abi_version.restype = ctypes.c_int32
    library.ucope_r01_r03_max_width.argtypes = []
    library.ucope_r01_r03_max_width.restype = ctypes.c_int32
    library.ucope_r01_r03_supported_width.argtypes = [ctypes.c_int32]
    library.ucope_r01_r03_supported_width.restype = ctypes.c_int32
    library.ucope_r01_r03_philox_word0.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32,
    ]
    library.ucope_r01_r03_philox_word0.restype = ctypes.c_uint32
    library.ucope_r01_r03_init_uniforms.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_float),
    ]
    library.ucope_r01_r03_init_uniforms.restype = ctypes.c_int32
    library.ucope_r01_r03_reset_batch.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint64),
        ctypes.POINTER(ctypes.c_int64), ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
    ]
    library.ucope_r01_r03_reset_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_sample_actions.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_float), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32),
    ]
    library.ucope_r01_r03_sample_actions.restype = ctypes.c_int32
    library.ucope_r01_r03_root_step_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_float),
    ]
    library.ucope_r01_r03_root_step_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_tail_step_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_int32), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_float),
    ]
    library.ucope_r01_r03_tail_step_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_terminal_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int32,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
    ]
    library.ucope_r01_r03_terminal_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_close_batch.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int32,
    ]
    library.ucope_r01_r03_close_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_counter_fill.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_uint64),
    ]
    library.ucope_r01_r03_counter_fill.restype = ctypes.c_int32
    library.ucope_r01_r03_population_batch.argtypes = [
        ctypes.c_uint64, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32),
        ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_int32),
    ]
    library.ucope_r01_r03_population_batch.restype = ctypes.c_int32
    library.ucope_r01_r03_nonlearned_actions.argtypes = [
        ctypes.c_int32, ctypes.c_int32, ctypes.POINTER(ctypes.c_int32),
        ctypes.c_int32, ctypes.POINTER(ctypes.c_int32),
    ]
    library.ucope_r01_r03_nonlearned_actions.restype = ctypes.c_int32
    if int(library.ucope_r01_r03_abi_version()) != NATIVE_ABI_VERSION:
        raise NativeBackendError("native ABI version mismatch")
    if int(library.ucope_r01_r03_max_width()) != max(SUPPORTED_BATCH_WIDTHS):
        raise NativeBackendError("native maximum width mismatch")
    if tuple(
        width
        for width in range(1, max(SUPPORTED_BATCH_WIDTHS) + 1)
        if int(library.ucope_r01_r03_supported_width(width)) == 1
    ) != SUPPORTED_BATCH_WIDTHS:
        raise NativeBackendError("native supported-width set mismatch")
    return library


def require_cpp_batched_backend(*, build_root: str | Path | None = None) -> ctypes.CDLL:
    root = (_DEFAULT_BUILD_ROOT if build_root is None else Path(build_root)).expanduser().resolve()
    build_key = _build_key()
    cache_key = str(root), build_key
    with _LOCK:
        cached = _LIBRARIES.get(cache_key)
        if cached is not None:
            return cached
        artifact = _compile(root, build_key).resolve(strict=True)
        library = _configure(ctypes.CDLL(str(artifact)))
        _LIBRARIES[cache_key] = library
        _IDENTITIES[cache_key] = {
            "schema": "UCOPE_R01_R03_NATIVE_IDENTITY_V1",
            "abi_version": NATIVE_ABI_VERSION,
            "host_kind": NATIVE_HOST_KIND,
            "source_path": str(_SOURCE.resolve(strict=True)),
            "source_sha256": _sha256(_SOURCE),
            "build_root": str(root),
            "build_key": build_key,
            "artifact": str(artifact),
            "artifact_sha256": _sha256(artifact),
            "artifact_size_bytes": artifact.stat().st_size,
            "compiler": str(_compiler()),
            "compiler_flags": list(_compiler_flags()),
            "runtime_abi": _runtime_abi(),
        }
        return library


def clear_process_local_cache_for_tests() -> None:
    with _LOCK:
        _LIBRARIES.clear()
        _IDENTITIES.clear()
        _build_key.cache_clear()


def native_artifact_identity(*, build_root: str | Path | None = None) -> dict[str, object]:
    root = (_DEFAULT_BUILD_ROOT if build_root is None else Path(build_root)).expanduser().resolve()
    build_key = _build_key()
    require_cpp_batched_backend(build_root=root)
    return dict(_IDENTITIES[(str(root), build_key)])


def philox_word0(
    seed: int, tag: int, panel: int, arm: int, network: int, word0: int, word1: int,
    *, build_root: str | Path | None = None,
) -> int:
    library = require_cpp_batched_backend(build_root=build_root)
    return int(library.ucope_r01_r03_philox_word0(seed, tag, panel, arm, network, word0, word1))


def init_uniforms(
    *, seed: int, panel: int, network: int, count: int,
    build_root: str | Path | None = None,
) -> np.ndarray:
    if panel not in (0, 1, 2) or network not in (0, 1) or count < 0:
        raise ValueError("invalid INIT counter coordinate")
    output = np.empty(count, dtype=np.float32)
    library = require_cpp_batched_backend(build_root=build_root)
    code = library.ucope_r01_r03_init_uniforms(
        seed, panel, network, count, _pointer(output, ctypes.c_float)
    )
    _raise(int(code), "INIT uniform fill")
    return output


def _check_array(name: str, value: np.ndarray, dtype: np.dtype, shape: tuple[int, ...]) -> np.ndarray:
    if not isinstance(value, np.ndarray) or value.dtype != dtype or value.shape != shape or not value.flags.c_contiguous:
        raise TypeError(f"{name} must be a C-contiguous {dtype} array with shape {shape}")
    return value


def _raise(code: int, action: str) -> None:
    if code != 0:
        raise NativeBackendError(f"native {action} failed with status {code}")


@dataclass
class NativeBatch:
    library: ctypes.CDLL
    handles: np.ndarray
    episodes: np.ndarray
    regimes: np.ndarray
    root_features: np.ndarray
    root_baselines: np.ndarray
    arms: np.ndarray
    panel: int
    seed: int
    batch_index: int
    closed: bool = False

    @property
    def width(self) -> int:
        return int(self.handles.shape[0])

    def root_step(self, actions: np.ndarray) -> dict[str, np.ndarray]:
        if self.closed:
            raise NativeBackendError("native batch is closed")
        _check_array("actions", actions, np.dtype(np.int32), (self.width,))
        actual = np.empty((self.width, 6), dtype=np.int32)
        displayed = np.empty((self.width, 6), dtype=np.int32)
        probe = np.empty((self.width, 3), dtype=np.float32)
        tail_features = np.zeros((self.width, TAIL_ACTION_COUNT, SCORER_FEATURES), dtype=np.float32)
        tail_baselines = np.zeros((self.width, BASELINE_FEATURES), dtype=np.float32)
        terminal = np.empty(self.width, dtype=np.int32)
        immediate = np.empty((self.width, 3), dtype=np.float32)
        code = self.library.ucope_r01_r03_root_step_batch(
            _pointer(self.handles, ctypes.c_uint64), _pointer(actions, ctypes.c_int32), self.width,
            _pointer(actual, ctypes.c_int32), _pointer(displayed, ctypes.c_int32),
            _pointer(probe, ctypes.c_float), _pointer(tail_features, ctypes.c_float),
            _pointer(tail_baselines, ctypes.c_float), _pointer(terminal, ctypes.c_int32),
            _pointer(immediate, ctypes.c_float),
        )
        _raise(int(code), "root step")
        return {
            "actual_marks": actual,
            "displayed_marks": displayed,
            "probe_components": probe,
            "tail_features": tail_features,
            "tail_baselines": tail_baselines,
            "terminal": terminal,
            "immediate_tail_components": immediate,
        }

    def tail_step(self, actions: np.ndarray) -> np.ndarray:
        if self.closed:
            raise NativeBackendError("native batch is closed")
        _check_array("actions", actions, np.dtype(np.int32), (self.width,))
        output = np.empty((self.width, 3), dtype=np.float32)
        code = self.library.ucope_r01_r03_tail_step_batch(
            _pointer(self.handles, ctypes.c_uint64), _pointer(actions, ctypes.c_int32), self.width,
            _pointer(output, ctypes.c_float),
        )
        _raise(int(code), "tail step")
        return output

    def terminal(self) -> dict[str, np.ndarray]:
        if self.closed:
            raise NativeBackendError("native batch is closed")
        components = np.empty((self.width, 6), dtype=np.float32)
        totals = np.empty(self.width, dtype=np.float32)
        code = self.library.ucope_r01_r03_terminal_batch(
            _pointer(self.handles, ctypes.c_uint64), self.width,
            _pointer(components, ctypes.c_float), _pointer(totals, ctypes.c_float),
        )
        _raise(int(code), "terminal")
        return {"components": components, "totals": totals}

    def close(self) -> None:
        if self.closed:
            raise NativeBackendError("native batch is already closed")
        code = self.library.ucope_r01_r03_close_batch(
            _pointer(self.handles, ctypes.c_uint64), self.width,
        )
        _raise(int(code), "close")
        self.closed = True


def reset_batch(
    *, seed: int, panel: int, batch_index: int, arms: np.ndarray,
    build_root: str | Path | None = None,
) -> NativeBatch:
    if not isinstance(arms, np.ndarray) or arms.dtype != np.int32 or arms.ndim != 1 or not arms.flags.c_contiguous:
        raise TypeError("arms must be a C-contiguous int32 vector")
    width = int(arms.shape[0])
    require_supported_width(width)
    if panel not in (0, 1, 2) or batch_index < 0:
        raise ValueError("panel must be 0..2 and batch_index must be nonnegative")
    library = require_cpp_batched_backend(build_root=build_root)
    handles = np.empty(width, dtype=np.uint64)
    episodes = np.empty(width, dtype=np.int64)
    regimes = np.empty((width, 3), dtype=np.int32)
    root_features = np.empty((width, ROOT_ACTION_COUNT, SCORER_FEATURES), dtype=np.float32)
    root_baselines = np.empty((width, BASELINE_FEATURES), dtype=np.float32)
    code = library.ucope_r01_r03_reset_batch(
        seed, panel, batch_index, width, _pointer(arms, ctypes.c_int32),
        _pointer(handles, ctypes.c_uint64), _pointer(episodes, ctypes.c_int64),
        _pointer(regimes, ctypes.c_int32), _pointer(root_features, ctypes.c_float),
        _pointer(root_baselines, ctypes.c_float),
    )
    _raise(int(code), "reset")
    return NativeBatch(
        library, handles, episodes, regimes, root_features, root_baselines,
        arms.copy(), panel, seed, batch_index,
    )


def sample_actions(
    probabilities: np.ndarray, *, seed: int, panel: int, batch_index: int,
    arms: np.ndarray, decision_code: int, legal_counts: np.ndarray,
    build_root: str | Path | None = None,
) -> np.ndarray:
    if not isinstance(probabilities, np.ndarray) or probabilities.dtype != np.float32 or probabilities.ndim != 2 or not probabilities.flags.c_contiguous:
        raise TypeError("probabilities must be a C-contiguous FP32 matrix")
    width, maximum_actions = probabilities.shape
    require_supported_width(width)
    _check_array("arms", arms, np.dtype(np.int32), (width,))
    _check_array("legal_counts", legal_counts, np.dtype(np.int32), (width,))
    output = np.empty(width, dtype=np.int32)
    library = require_cpp_batched_backend(build_root=build_root)
    code = library.ucope_r01_r03_sample_actions(
        seed, panel, batch_index, width, _pointer(arms, ctypes.c_int32), decision_code,
        _pointer(probabilities, ctypes.c_float), maximum_actions,
        _pointer(legal_counts, ctypes.c_int32), _pointer(output, ctypes.c_int32),
    )
    _raise(int(code), "action sample")
    return output


def counter_fill(
    *, seed: int, width: int, iterations: int,
    build_root: str | Path | None = None,
) -> np.ndarray:
    require_supported_width(width)
    output = np.empty(width, dtype=np.uint64)
    library = require_cpp_batched_backend(build_root=build_root)
    code = library.ucope_r01_r03_counter_fill(
        seed, width, iterations, _pointer(output, ctypes.c_uint64),
    )
    _raise(int(code), "counter fill")
    return output


def counter_population(
    *, seed: int, panel: int, batch_index: int, width: int,
    build_root: str | Path | None = None,
) -> dict[str, np.ndarray]:
    """Materialize the complete addressed environment tape for one TEST batch."""

    require_supported_width(width)
    if panel not in (0, 1, 2) or batch_index < 0:
        raise ValueError("panel must be 0..2 and batch_index must be nonnegative")
    regimes = np.empty((width, 3), dtype=np.int32)
    actual = np.empty((width, 6), dtype=np.int32)
    displayed = np.empty((width, 6), dtype=np.int32)
    potential_tail = np.empty((width, 5), dtype=np.int32)
    library = require_cpp_batched_backend(build_root=build_root)
    code = library.ucope_r01_r03_population_batch(
        seed, panel, batch_index, width, _pointer(regimes, ctypes.c_int32),
        _pointer(actual, ctypes.c_int32), _pointer(displayed, ctypes.c_int32),
        _pointer(potential_tail, ctypes.c_int32),
    )
    _raise(int(code), "counter population")
    return {
        "regimes": regimes,
        "actual_marks": actual,
        "displayed_marks": displayed,
        "potential_tail": potential_tail,
    }


def nonlearned_actions(
    *, panel: int, displayed_count: int, periods: np.ndarray,
    build_root: str | Path | None = None,
) -> dict[str, int]:
    """Return the three frozen nonlearned-arm action codes without values."""

    if not isinstance(periods, np.ndarray) or periods.dtype != np.int32 or periods.ndim != 1 or not periods.flags.c_contiguous:
        raise TypeError("periods must be a C-contiguous int32 vector")
    output = np.empty(5, dtype=np.int32)
    library = require_cpp_batched_backend(build_root=build_root)
    code = library.ucope_r01_r03_nonlearned_actions(
        panel, displayed_count, _pointer(periods, ctypes.c_int32), periods.size,
        _pointer(output, ctypes.c_int32),
    )
    _raise(int(code), "nonlearned action primitive")
    return {
        "belief_dp_root": int(output[0]),
        "belief_dp_tail": int(output[1]),
        "immediate_dp_root": int(output[2]),
        "forced_probe_blind_dp_root": int(output[3]),
        "forced_probe_blind_dp_tail": int(output[4]),
    }
