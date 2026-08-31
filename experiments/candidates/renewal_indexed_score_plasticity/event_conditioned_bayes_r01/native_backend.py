"""Fresh native/reference seam for bounded RISP-ECR-R01 exact evaluation.

The C++ backend is used when a C++17 compiler is available.  Otherwise the
explicit fallback remains exact, isolated, and bounded to the frozen duration
set and at most ``MAX_HISTORY_EVENTS`` completed events.
"""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Mapping

from .contract import ACTIONS, ALLOWED_DURATIONS, MAX_EVENTS_PER_HISTORY, NATIVE_REGISTRY_KEY
from .exact_probability import ack_is_positive
from .reference_host import (
    choose_action,
    history_path_mass,
    q_values,
    replay_full_bayes,
    validate_clocks,
)


REFERENCE_FALLBACK_KEY = "RISP-ECR-R01-EXACT-REFERENCE-FALLBACK-V1"
MAX_HISTORY_EVENTS = MAX_EVENTS_PER_HISTORY
SOURCE = Path(__file__).with_name("native_backend.cpp")
_PROCESS_BUILD_TOKEN = f"{os.getpid()}-{time.monotonic_ns()}"


class NativeBackendError(RuntimeError):
    """Raised when native compilation/loading or exact evaluation fails."""


@dataclass(frozen=True)
class ExactEvaluation:
    backend: str
    history_mass: Fraction
    posterior: tuple[Fraction, Fraction, Fraction]
    q: tuple[Fraction, Fraction, Fraction]
    action: str
    value: Fraction

    def q_values(self) -> dict[str, Fraction]:
        return dict(zip(ACTIONS, self.q, strict=True))


_NATIVE_LIBRARY: ctypes.CDLL | None = None
_NATIVE_FAILURE: str | None = None
_NATIVE_COMPILER_FAMILY: str | None = None
_DLL_DIRECTORY_HANDLE: object | None = None


@dataclass(frozen=True)
class _Compiler:
    executable: str
    family: str
    environment: Mapping[str, str]


def _bounded_history(history: Mapping[str, object]) -> tuple[tuple[Mapping[str, object], ...], int]:
    events_value = history.get("events")
    if not isinstance(events_value, (list, tuple)):
        raise NativeBackendError("history events must be a sequence")
    if len(events_value) > MAX_HISTORY_EVENTS:
        raise NativeBackendError(
            f"exact backend is bounded to {MAX_HISTORY_EVENTS} completed events"
        )
    clocks = validate_clocks(history)
    events = tuple(events_value)
    next_duration = clocks["next_duration"]
    assert isinstance(next_duration, int) and next_duration in ALLOWED_DURATIONS
    return events, next_duration  # type: ignore[return-value]


def _reference_evaluate(history: Mapping[str, object]) -> ExactEvaluation:
    _, next_duration = _bounded_history(history)
    posterior = replay_full_bayes(history)
    values = q_values(posterior, next_duration)
    action, value = choose_action(values)
    return ExactEvaluation(
        backend=REFERENCE_FALLBACK_KEY,
        history_mass=history_path_mass(history),
        posterior=posterior,
        q=tuple(values[action_name] for action_name in ACTIONS),  # type: ignore[arg-type]
        action=action,
        value=value,
    )


def _gmp_root() -> Path | None:
    candidates: list[Path] = []
    configured = os.environ.get("RISP_ECR_R01_GMP_ROOT")
    if configured:
        candidates.append(Path(configured))
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        candidates.append(Path(conda_prefix) / "Library")
    candidates.extend(
        (
            Path(sys.prefix) / "Library",
            Path.home() / ".conda/envs/hmasd-science-tools/Library",
            Path.home() / "miniconda3/envs/hmasd-science-tools/Library",
        )
    )
    for candidate in candidates:
        if (
            (candidate / "include/gmp.h").is_file()
            and (candidate / "include/gmpxx.h").is_file()
            and (candidate / "lib/gmp.lib").is_file()
            and (candidate / "lib/gmpxx.lib").is_file()
            and (candidate / "bin/gmp.dll").is_file()
            and (candidate / "bin/gmpxx.dll").is_file()
        ):
            return candidate
    return None


def _visual_studio_dev_cmd() -> Path | None:
    candidates: list[Path] = []
    configured = os.environ.get("VSDEVCMD")
    if configured:
        candidates.append(Path(configured))
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        visual_studio = Path(program_files_x86) / "Microsoft Visual Studio/2022"
        candidates.extend(
            visual_studio / edition / "Common7/Tools/VsDevCmd.bat"
            for edition in ("BuildTools", "Community", "Professional", "Enterprise")
        )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _msvc_compiler() -> _Compiler | None:
    if os.name != "nt":
        return None
    dev_cmd = _visual_studio_dev_cmd()
    if dev_cmd is None:
        return None
    command = (
        f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c '
        f'""{dev_cmd}" -no_logo -arch=x64 -host_arch=x64 >nul && set"'
    )
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise NativeBackendError(f"VsDevCmd environment failed: {detail[-2000:]}")
    environment = dict(os.environ)
    for line in completed.stdout.splitlines():
        if not line or line.startswith("=") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        environment[key] = value
    path_value = environment.get("Path") or environment.get("PATH")
    compiler = shutil.which("cl.exe", path=path_value)
    if compiler is None:
        raise NativeBackendError("VsDevCmd did not expose cl.exe")
    return _Compiler(compiler, "msvc", environment)


def _compiler() -> _Compiler | None:
    configured = os.environ.get("CXX")
    if configured:
        located = shutil.which(configured) or (configured if Path(configured).is_file() else None)
        if located:
            family = "msvc" if Path(located).name.casefold() == "cl.exe" else "gnu"
            return _Compiler(str(located), family, dict(os.environ))
    for candidate in ("c++", "g++", "clang++"):
        located = shutil.which(candidate)
        if located:
            return _Compiler(located, "gnu", dict(os.environ))
    return _msvc_compiler()


def _library_path() -> Path:
    suffix = ".dll" if sys.platform == "win32" else ".dylib" if sys.platform == "darwin" else ".so"
    build_root = (
        Path(tempfile.gettempdir())
        / f"hmasd-risp-ecr-r01-native-{_PROCESS_BUILD_TOKEN}"
    )
    build_root.mkdir(parents=True, exist_ok=False)
    return build_root / f"risp_ecr_r01{suffix}"


def _compile(compiler: _Compiler, gmp_root: Path, destination: Path) -> None:
    temporary = destination.with_name(
        f"{destination.stem}.partial{destination.suffix}"
    )
    if compiler.family == "msvc":
        object_path = destination.with_name("risp_ecr_r01_native.obj")
        command = [
            compiler.executable,
            "/nologo",
            "/std:c++17",
            "/O2",
            "/EHsc",
            "/LD",
            f"/I{gmp_root / 'include'}",
            str(SOURCE),
            f"/Fo{object_path}",
            f"/Fe{temporary}",
            "/link",
            f"/LIBPATH:{gmp_root / 'lib'}",
            "gmpxx.lib",
            "gmp.lib",
        ]
    else:
        command = [
            compiler.executable,
            "-std=c++17",
            "-O2",
            "-shared",
            "-fPIC",
            f"-I{gmp_root / 'include'}",
            str(SOURCE),
            f"-L{gmp_root / 'lib'}",
            "-lgmpxx",
            "-lgmp",
            "-o",
            str(temporary),
        ]
        if sys.platform == "win32":
            command.remove("-fPIC")
    completed = subprocess.run(
        command,
        cwd=destination.parent,
        env=dict(compiler.environment),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        temporary.unlink(missing_ok=True)
        detail = (completed.stderr or completed.stdout).strip()
        raise NativeBackendError(f"native compile failed: {detail[-2000:]}")
    os.replace(temporary, destination)


def _load_native() -> ctypes.CDLL | None:
    global _DLL_DIRECTORY_HANDLE, _NATIVE_COMPILER_FAMILY, _NATIVE_LIBRARY, _NATIVE_FAILURE
    if _NATIVE_LIBRARY is not None:
        return _NATIVE_LIBRARY
    if _NATIVE_FAILURE is not None:
        return None
    try:
        gmp_root = _gmp_root()
        if gmp_root is None:
            raise NativeBackendError("local GMP exact-integer development runtime is unavailable")
        compiler = _compiler()
        if compiler is None:
            raise NativeBackendError("no C++17 compiler available")
        _NATIVE_COMPILER_FAMILY = compiler.family
        library_path = _library_path()
        _compile(compiler, gmp_root, library_path)
        if os.name == "nt":
            _DLL_DIRECTORY_HANDLE = os.add_dll_directory(str(gmp_root / "bin"))
        library = ctypes.CDLL(str(library_path))
        library.risp_ecr_r01_registry_key.argtypes = []
        library.risp_ecr_r01_registry_key.restype = ctypes.c_char_p
        library.risp_ecr_r01_evaluate.argtypes = [ctypes.c_char_p]
        library.risp_ecr_r01_evaluate.restype = ctypes.c_char_p
        key = library.risp_ecr_r01_registry_key().decode("ascii")
        if key != NATIVE_REGISTRY_KEY:
            raise NativeBackendError(f"unexpected native registry key {key!r}")
        _NATIVE_LIBRARY = library
        return library
    except (OSError, subprocess.SubprocessError, NativeBackendError) as error:
        _NATIVE_FAILURE = str(error)
        return None


def native_status() -> dict[str, str | bool | None]:
    """Report availability without changing scientific state or using RNG."""

    library = _load_native()
    return {
        "available": library is not None,
        "registry_key": NATIVE_REGISTRY_KEY if library is not None else None,
        "fallback_key": REFERENCE_FALLBACK_KEY,
        "compiler_family": _NATIVE_COMPILER_FAMILY,
        "exact_integer_backend": "GMP",
        "failure": _NATIVE_FAILURE,
    }


def _encode(history: Mapping[str, object]) -> bytes:
    events, next_duration = _bounded_history(history)
    encoded_events: list[str] = []
    for event in events:
        action = event["action"]
        assert isinstance(action, str)
        action_index = ACTIONS.index(action)
        positive = 1 if ack_is_positive(event["ack"]) else 0
        duration = event["completed_duration"]
        assert isinstance(duration, int)
        encoded_events.append(f"{action_index},{positive},{duration}")
    return (";".join(encoded_events) + f"|{next_duration}").encode("ascii")


def _parse_fraction(value: str) -> Fraction:
    fields = value.split("/")
    if len(fields) != 2:
        raise NativeBackendError("native rational is malformed")
    try:
        numerator, denominator = (int(field) for field in fields)
    except ValueError as error:
        raise NativeBackendError("native rational is malformed") from error
    result = Fraction(numerator, denominator)
    if denominator <= 0 or result.numerator != numerator or result.denominator != denominator:
        raise NativeBackendError("native rational is not canonical")
    return result


def _native_evaluate(history: Mapping[str, object], library: ctypes.CDLL) -> ExactEvaluation:
    raw = library.risp_ecr_r01_evaluate(_encode(history))
    if raw is None:
        raise NativeBackendError("native backend returned null")
    text = raw.decode("ascii")
    if text.startswith("ERROR:"):
        raise NativeBackendError(text[6:])
    fields = text.split(";")
    if len(fields) != 9:
        raise NativeBackendError("native backend returned malformed field count")
    history_mass = _parse_fraction(fields[0])
    posterior = tuple(_parse_fraction(value) for value in fields[1:4])
    q = tuple(_parse_fraction(value) for value in fields[4:7])
    try:
        action_index = int(fields[7])
    except ValueError as error:
        raise NativeBackendError("native action index is malformed") from error
    if action_index not in range(3):
        raise NativeBackendError("native action index is outside the action space")
    return ExactEvaluation(
        backend=NATIVE_REGISTRY_KEY,
        history_mass=history_mass,
        posterior=posterior,  # type: ignore[arg-type]
        q=q,  # type: ignore[arg-type]
        action=ACTIONS[action_index],
        value=_parse_fraction(fields[8]),
    )


def evaluate_history(
    history: Mapping[str, object], *, require_native: bool = False
) -> ExactEvaluation:
    """Evaluate one bounded history, with an explicit exact fallback.

    ``require_native`` is intended for backend verification only.  It does not
    change the mathematical observable or permit broader K/history inputs.
    """

    _bounded_history(history)
    library = _load_native()
    if library is None:
        if require_native:
            raise NativeBackendError(_NATIVE_FAILURE or "native backend unavailable")
        return _reference_evaluate(history)
    return _native_evaluate(history, library)


def assert_native_reference_equivalent(history: Mapping[str, object]) -> None:
    """Raise unless every exact native output equals the isolated reference."""

    reference = _reference_evaluate(history)
    native = evaluate_history(history, require_native=True)
    if (
        native.history_mass,
        native.posterior,
        native.q,
        native.action,
        native.value,
    ) != (
        reference.history_mass,
        reference.posterior,
        reference.q,
        reference.action,
        reference.value,
    ):
        raise NativeBackendError("native/reference exact mismatch")


__all__ = [
    "ExactEvaluation",
    "MAX_HISTORY_EVENTS",
    "NATIVE_REGISTRY_KEY",
    "NativeBackendError",
    "REFERENCE_FALLBACK_KEY",
    "assert_native_reference_equivalent",
    "evaluate_history",
    "native_status",
]
