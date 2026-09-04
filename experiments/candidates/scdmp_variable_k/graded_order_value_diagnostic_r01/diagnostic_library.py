"""Build and load the diagnostic translation unit for the R01 host diagnostic.

The frozen host `mf_rs_native.cpp` is never edited.  This module *derives* a
diagnostic source from it by four exact, unique string substitutions that turn
the two constants the `cable_overload` constraint reads into runtime globals,
then compiles that derived source into a separate DLL.  The substitution table
is the whole difference between the two translation units and is recorded with
every measurement.

Frozen sites (as of the base run, `mf_rs_native.cpp`):

  :173  output[6 + i] = state.z[i] / 0.25;                    -- observation scale
  :298  state.z[i] = 0.84 * state.z[i] + max(0.0, tau[i] - 0.88);
  :307  state.cable_overload = max(z) > 0.25 ? 1 : 0;
  :315  && *std::max_element(state.z, state.z + 4) <= 0.25    -- safe_dock clause

Note that `Z_LIMIT` is read by the failure predicate, the dock predicate and the
observation normaliser, so a row with `Z_LIMIT != 0.25` is a different host, not
the frozen one.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Final

from experiments.candidates.scdmp_variable_k.multifoundation_reachable_order_value import (
    native_backend,
)


class DiagnosticLibraryError(RuntimeError):
    pass


FROZEN_TAU_LEAK: Final[float] = 0.88
FROZEN_Z_LIMIT: Final[float] = 0.25

_FROZEN_SOURCE: Final[Path] = (
    Path(native_backend.__file__).with_name("native") / "mf_rs_native.cpp"
)

# (frozen text, diagnostic text, the frozen line it occupies).  Each must occur
# exactly once in the frozen source or the build refuses.
SUBSTITUTIONS: Final[tuple[tuple[str, str, int], ...]] = (
    (
        "output[6 + i] = state.z[i] / 0.25;",
        "output[6 + i] = state.z[i] / mf_diag_z_limit;",
        173,
    ),
    (
        "state.z[i] = 0.84 * state.z[i] + std::max(0.0, tau[i] - 0.88);",
        "state.z[i] = 0.84 * state.z[i] + std::max(0.0, tau[i] - mf_diag_tau_leak);",
        298,
    ),
    (
        "state.cable_overload = *std::max_element(state.z, state.z + 4) > 0.25 ? 1 : 0;",
        "state.cable_overload = *std::max_element(state.z, state.z + 4) > mf_diag_z_limit ? 1 : 0;",
        307,
    ),
    (
        "&& *std::max_element(state.z, state.z + 4) <= 0.25",
        "&& *std::max_element(state.z, state.z + 4) <= mf_diag_z_limit",
        315,
    ),
)

_GLOBALS_ANCHOR: Final[str] = "namespace {\n"
_GLOBALS_TEXT: Final[str] = (
    "namespace {\n"
    "\n"
    "// SCDMP-A-GRADED-ORDER-VALUE-DIAGNOSTIC-R01: the two constants the\n"
    "// cable_overload constraint reads, as runtime globals.  Initialised to the\n"
    "// frozen host values, so an unset library is bit-identical to the frozen one.\n"
    "double mf_diag_tau_leak = 0.88;\n"
    "double mf_diag_z_limit = 0.25;\n"
)
_SETTER_TEXT: Final[str] = (
    "\n"
    "MF_EXPORT std::int32_t mf_diag_set_cable_parameters(double tau_leak, double z_limit) {\n"
    "    if (!(tau_leak > 0.0) || !(z_limit > 0.0)) return -1;\n"
    "    mf_diag_tau_leak = tau_leak;\n"
    "    mf_diag_z_limit = z_limit;\n"
    "    return 0;\n"
    "}\n"
    "\n"
    "MF_EXPORT double mf_diag_tau_leak_value() { return mf_diag_tau_leak; }\n"
    "MF_EXPORT double mf_diag_z_limit_value() { return mf_diag_z_limit; }\n"
)

_COMPILE_FLAGS: Final[tuple[str, ...]] = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/W4")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def derive_diagnostic_source() -> tuple[str, dict[str, object]]:
    """Return the derived source text and a record of exactly how it differs."""

    frozen_bytes = _FROZEN_SOURCE.read_bytes()
    text = frozen_bytes.decode("utf-8")
    applied = []
    for old, new, line in SUBSTITUTIONS:
        occurrences = text.count(old)
        if occurrences != 1:
            raise DiagnosticLibraryError(
                f"frozen substitution site is not unique ({occurrences}) at line {line}: {old}"
            )
        text = text.replace(old, new, 1)
        applied.append({"frozen_line": line, "frozen_text": old, "diagnostic_text": new})
    if text.count(_GLOBALS_ANCHOR) != 1:
        raise DiagnosticLibraryError("anonymous-namespace anchor is not unique")
    text = text.replace(_GLOBALS_ANCHOR, _GLOBALS_TEXT, 1)
    text = text + _SETTER_TEXT
    derived = text.encode("utf-8")
    record = {
        "frozen_source_path": str(_FROZEN_SOURCE),
        "frozen_source_byte_size": len(frozen_bytes),
        "frozen_source_sha256": _sha256(frozen_bytes),
        "diagnostic_source_byte_size": len(derived),
        "diagnostic_source_sha256": _sha256(derived),
        "substitutions": applied,
        "inserted_globals": _GLOBALS_TEXT[len(_GLOBALS_ANCHOR):],
        "appended_exports": _SETTER_TEXT,
        "frozen_tau_leak": FROZEN_TAU_LEAK,
        "frozen_z_limit": FROZEN_Z_LIMIT,
    }
    return text, record


def _compile(source_path: Path, staging: Path) -> Path:
    installation = native_backend._vs_installation()
    compiler = native_backend._compiler_path()
    vcvars = installation / "VC/Auxiliary/Build/vcvars64.bat"
    obj = staging / "mf_rs_diagnostic.obj"
    dll = staging / "mf_rs_diagnostic.dll"
    command = (
        f'call "{vcvars}" >nul && "{compiler}" {" ".join(_COMPILE_FLAGS)} '
        f'"{source_path}" /Fo:"{obj}" /Fe:"{dll}"'
    )
    completed = subprocess.run(
        command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"),
        cwd=staging, capture_output=True, text=True,
    )
    if completed.returncode != 0 or not dll.is_file():
        raise DiagnosticLibraryError(
            f"diagnostic compilation failed ({completed.returncode}):\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    obj.unlink(missing_ok=True)
    return dll


def build_diagnostic_library(output_root: str | Path) -> tuple[ctypes.CDLL, dict[str, object]]:
    """Derive, compile, load and configure the diagnostic library."""

    root = Path(output_root).resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    text, record = derive_diagnostic_source()
    source_path = root / "mf_rs_diagnostic.cpp"
    source_path.write_bytes(text.encode("utf-8"))
    staging = Path(tempfile.mkdtemp(prefix=".build-", dir=root))
    dll = _compile(source_path, staging)
    dll_bytes = dll.read_bytes()
    library = native_backend._configure(ctypes.CDLL(str(dll)))
    library.mf_diag_set_cable_parameters.argtypes = [ctypes.c_double, ctypes.c_double]
    library.mf_diag_set_cable_parameters.restype = ctypes.c_int32
    library.mf_diag_tau_leak_value.argtypes = []
    library.mf_diag_tau_leak_value.restype = ctypes.c_double
    library.mf_diag_z_limit_value.argtypes = []
    library.mf_diag_z_limit_value.restype = ctypes.c_double
    record.update({
        "diagnostic_source_resolved_path": str(source_path),
        "compiled_diagnostic_library_resolved_path": str(dll),
        "compiled_diagnostic_library_byte_size": len(dll_bytes),
        "compiled_diagnostic_library_sha256": _sha256(dll_bytes),
        "compile_flags": list(_COMPILE_FLAGS),
        "compiler_resolved_executable": str(native_backend._compiler_path()),
        "abi_version": int(library.mf_rs_abi_version()),
        "magic": int(library.mf_rs_magic()),
        "max_width": int(library.mf_rs_max_width()),
        "initial_tau_leak": float(library.mf_diag_tau_leak_value()),
        "initial_z_limit": float(library.mf_diag_z_limit_value()),
    })
    if record["initial_tau_leak"] != FROZEN_TAU_LEAK or record["initial_z_limit"] != FROZEN_Z_LIMIT:
        raise DiagnosticLibraryError("diagnostic library did not initialise at the frozen row")
    return library, record


def set_cable_parameters(library: ctypes.CDLL, *, tau_leak: float, z_limit: float) -> None:
    if int(library.mf_diag_set_cable_parameters(float(tau_leak), float(z_limit))) != 0:
        raise DiagnosticLibraryError("diagnostic library rejected the cable parameters")
    if (
        float(library.mf_diag_tau_leak_value()) != float(tau_leak)
        or float(library.mf_diag_z_limit_value()) != float(z_limit)
    ):
        raise DiagnosticLibraryError("diagnostic library did not adopt the cable parameters")


class use_library:
    """Point `NativeSession` at a chosen library for the duration of a block.

    Diagnostic-only.  No production file is modified; the module attribute is
    restored on exit, and the frozen library is what every other caller sees.
    """

    def __init__(self, library: ctypes.CDLL) -> None:
        self._library = library
        self._previous = None

    def __enter__(self) -> ctypes.CDLL:
        self._previous = native_backend.require_native_backend
        native_backend.require_native_backend = lambda: self._library
        return self._library

    def __exit__(self, *_args: object) -> None:
        native_backend.require_native_backend = self._previous


__all__ = [
    "DiagnosticLibraryError", "FROZEN_TAU_LEAK", "FROZEN_Z_LIMIT", "SUBSTITUTIONS",
    "build_diagnostic_library", "derive_diagnostic_source", "set_cable_parameters",
    "use_library",
]
