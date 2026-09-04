"""Fail-closed source-keyed ctypes loader for the DISH r05 Gate-A host.

This candidate-local loader proves a TEST-only engineering boundary.  It has
no production namespace adapter and no Python execution fallback.
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

from .contracts import ABI_VERSION, Arm, GateAFixture, GateAResult


_SOURCE = Path(__file__).with_name("native") / "rbhr_backend.cpp"
_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD", "/fp:strict", "/W4")


class NativeBackendError(RuntimeError):
    pass


class _Input(ctypes.Structure):
    _fields_ = [
        ("fixture_key", ctypes.c_uint64),
        *[(name, ctypes.c_int32) for name in (
            "arm", "package", "reflection", "initial_owner", "k_initial", "k_new",
            "switch_tick", "tau_d_tick", "phase", "route_speed",
            "turn_magnitude_deg", "turn_sign", "initial_ux", "initial_uy",
        )],
    ]


class _Output(ctypes.Structure):
    _fields_ = [
        *[(name, ctypes.c_int32) for name in (
            "service_ticks", "owner", "service_epoch", "next_payload_sequence",
            "handover_used", "noop_count", "transaction_shell_bytes", "invalid_commit", "token_gap",
            "dual_owner", "dual_payload", "buffer_clear", "separation_breach",
            "protocol_bytes", "terminal_tick",
        )],
        ("final_separation", ctypes.c_double),
        ("total_energy", ctypes.c_double),
        ("state_digest", ctypes.c_uint64),
    ]


class _GeneratorInput(ctypes.Structure):
    _fields_ = [
        ("fixture_key", ctypes.c_uint64),
        ("start", ctypes.c_uint32),
        ("count", ctypes.c_uint32),
        ("stratum", ctypes.c_int32),
    ]


class _GeneratorOutput(ctypes.Structure):
    _fields_ = [("winning_ordinal", ctypes.c_int64), ("winning_word", ctypes.c_uint64)]


class _ProtocolInput(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in (
        "integrity", "request_transfer", "origin_pass", "handover_unused",
        "application_tick", "origin_tick", "readiness_tick", "bound_readiness_tick",
        "snapshot_tick", "current_owner", "old_owner", "new_owner", "current_epoch",
        "intent_epoch", "current_next_sequence", "intent_next_sequence",
        "source0_sequence", "source1_sequence", "intent_source_sequence",
        "current_k_epoch", "intent_k_epoch", "terminal", "batteries_positive",
        "buffers_present", "separation_current", "separation_next", "slew_ok",
        "sham", "never_arm",
    )]


class _ProtocolOutput(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int32) for name in (
        "success", "reason_code", "invalid_commit", "noop_count", "owner",
        "service_epoch", "next_sequence", "handover_used", "source_buffers_preserved",
        "base_buffer_preserved", "transaction_shell_bytes", "forbidden_leak_count",
    )]


class _FilterInput(ctypes.Structure):
    _fields_ = [("mean", ctypes.c_double * 4), ("covariance", ctypes.c_double * 16), ("camera_present", ctypes.c_int32), ("z", ctypes.c_double * 2)]


class _FilterOutput(ctypes.Structure):
    _fields_ = [("mean", ctypes.c_double * 4), ("covariance", ctypes.c_double * 16), ("finite", ctypes.c_int32)]


class _CertificateInput(ctypes.Structure):
    _fields_ = [
        *[(name, ctypes.c_int32) for name in ("renew", "unused", "match", "age", "warm", "maintain", "separation", "slew", "g_latch")],
        ("mahalanobis_squared", ctypes.c_double), ("q95", ctypes.c_double),
    ]


def source_sha256() -> str:
    return hashlib.sha256(_SOURCE.read_bytes()).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    vswhere = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not vswhere.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    result = subprocess.run(
        [str(vswhere), "-latest", "-products", "*", "-requires",
         "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
        check=True, capture_output=True, text=True,
    )
    path = Path(result.stdout.strip())
    if not path.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return path


@functools.lru_cache(maxsize=1)
def _toolchain() -> dict[str, object]:
    candidates = tuple(
        path for path in (_vs_installation() / "VC" / "Tools" / "MSVC").glob("*/bin/Hostx64/x64/cl.exe")
        if path.is_file()
    )
    if not candidates:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    compiler = max(candidates, key=lambda path: tuple(int(part) for part in path.parts[-5].split(".")))
    result = subprocess.run([str(compiler)], capture_output=True, text=True, check=False)
    version = "\n".join(line.strip() for line in (result.stdout + "\n" + result.stderr).splitlines() if line.strip())
    if "Microsoft" not in version or "C/C++" not in version:
        raise NativeBackendError("MSVC identity could not be read")
    return {
        "compiler": str(compiler.resolve()),
        "compiler_sha256": _sha256_file(compiler),
        "version": version,
        "flags": list(_FLAGS),
    }


def _build_material() -> tuple[str, str, bytes]:
    source = _SOURCE.read_bytes()
    source_digest = hashlib.sha256(source).hexdigest()
    toolchain = _toolchain()
    digest = hashlib.sha256()
    digest.update(b"DISH-RBHR-R05-GATE-A-NATIVE-BUILD-v1\0")
    digest.update(source_digest.encode("ascii"))
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    digest.update(ABI_VERSION.to_bytes(4, "big"))
    for flag in _FLAGS:
        digest.update(flag.encode("ascii") + b"\0")
    return digest.hexdigest(), source_digest, source


def native_build_key() -> str:
    return _build_material()[0]


def _artifact_path(key: str) -> Path:
    return Path(tempfile.gettempdir()) / "hmasd_dish_rbhr_r05_gate_a" / key / "rbhr_backend.dll"


def _source_snapshot(root: Path, source: bytes) -> Path:
    path = root / "rbhr_backend.source.cpp"
    if path.is_file():
        if path.read_bytes() != source:
            raise NativeBackendError("source-key snapshot mismatch")
        return path
    temporary = root / f"rbhr_backend.{os.getpid()}.{threading.get_ident()}.tmp"
    with temporary.open("wb") as stream:
        stream.write(source)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    if path.read_bytes() != source:
        raise NativeBackendError("published source snapshot mismatch")
    return path


def _compile(key: str, source: bytes) -> Path:
    dll = _artifact_path(key)
    root = dll.parent
    root.mkdir(parents=True, exist_ok=True)
    snapshot = _source_snapshot(root, source)
    if dll.is_file():
        return dll
    vcvars = _vs_installation() / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    suffix = f"{os.getpid()}.{threading.get_ident()}"
    obj = root / f"rbhr_backend.{suffix}.obj"
    candidate = root / f"rbhr_backend.{suffix}.dll"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(_FLAGS)} "{snapshot}" '
        f'/Fo:"{obj}" /link /OUT:"{candidate}"'
    )
    result = subprocess.run(
        command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"), cwd=root,
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not candidate.is_file():
        raise NativeBackendError(
            f"native compilation failed ({result.returncode}):\n{result.stdout}\n{result.stderr}"
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


def _configure(library: ctypes.CDLL) -> ctypes.CDLL:
    for name in ("dish_rbhr_abi_version",):
        function = getattr(library, name); function.argtypes = []; function.restype = ctypes.c_int
    for name in (
        "dish_rbhr_input_size", "dish_rbhr_output_size",
        "dish_rbhr_generator_input_size", "dish_rbhr_generator_output_size",
        "dish_rbhr_protocol_input_size", "dish_rbhr_protocol_output_size",
        "dish_rbhr_filter_input_size", "dish_rbhr_filter_output_size",
    ):
        function = getattr(library, name); function.argtypes = []; function.restype = ctypes.c_uint64
    observed = (
        library.dish_rbhr_abi_version(), library.dish_rbhr_input_size(), library.dish_rbhr_output_size(),
        library.dish_rbhr_generator_input_size(), library.dish_rbhr_generator_output_size(),
        library.dish_rbhr_protocol_input_size(), library.dish_rbhr_protocol_output_size(),
        library.dish_rbhr_filter_input_size(), library.dish_rbhr_filter_output_size(),
    )
    expected = (
        ABI_VERSION, ctypes.sizeof(_Input), ctypes.sizeof(_Output),
        ctypes.sizeof(_GeneratorInput), ctypes.sizeof(_GeneratorOutput),
        ctypes.sizeof(_ProtocolInput), ctypes.sizeof(_ProtocolOutput),
        ctypes.sizeof(_FilterInput), ctypes.sizeof(_FilterOutput),
    )
    if observed != expected:
        raise NativeBackendError(f"native ABI mismatch: {observed!r} != {expected!r}")
    library.dish_rbhr_run_batch.argtypes = [ctypes.POINTER(_Input), ctypes.c_uint64, ctypes.POINTER(_Output)]
    library.dish_rbhr_run_batch.restype = ctypes.c_int
    library.dish_rbhr_generator_scan_batch.argtypes = [
        ctypes.POINTER(_GeneratorInput), ctypes.c_uint64, ctypes.POINTER(_GeneratorOutput)
    ]
    library.dish_rbhr_generator_scan_batch.restype = ctypes.c_int
    library.dish_rbhr_rng_word.argtypes = [ctypes.c_uint64, ctypes.c_char_p, ctypes.c_uint64]
    library.dish_rbhr_rng_word.restype = ctypes.c_uint64
    library.dish_rbhr_protocol_apply_batch.argtypes = [
        ctypes.POINTER(_ProtocolInput), ctypes.c_uint64, ctypes.POINTER(_ProtocolOutput)
    ]
    library.dish_rbhr_protocol_apply_batch.restype = ctypes.c_int
    library.dish_rbhr_redact_observation_batch.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_double),
    ]
    library.dish_rbhr_redact_observation_batch.restype = ctypes.c_int
    library.dish_rbhr_filter_step_batch.argtypes = [ctypes.POINTER(_FilterInput), ctypes.c_uint64, ctypes.POINTER(_FilterOutput)]
    library.dish_rbhr_filter_step_batch.restype = ctypes.c_int
    library.dish_rbhr_certificate_batch.argtypes = [ctypes.POINTER(_CertificateInput), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32)]
    library.dish_rbhr_certificate_batch.restype = ctypes.c_int
    library.dish_rbhr_wire_size.argtypes = [ctypes.c_int32]
    library.dish_rbhr_wire_size.restype = ctypes.c_int
    return library


_LOCK = threading.RLock()
_LOADED: dict[str, ctypes.CDLL] = {}


def require_cpp_batched_backend() -> ctypes.CDLL:
    key, _, source = _build_material()
    with _LOCK:
        library = _LOADED.get(key)
        if library is None:
            library = _configure(ctypes.CDLL(str(_compile(key, source))))
            _LOADED[key] = library
        return library


def artifact_identity() -> dict[str, object]:
    key, source_digest, source = _build_material()
    path = _artifact_path(key)
    existed = path.is_file()
    started = time.perf_counter()
    library = require_cpp_batched_backend()
    elapsed = time.perf_counter() - started
    return {
        "component": "dish_rbhr_r05_gate_a_test_host",
        "path": str(path),
        "sha256": _sha256_file(path),
        "size": path.stat().st_size,
        "source_sha256": source_digest,
        "build_key": key,
        "cache_present_before": existed,
        "load_seconds": elapsed,
        "abi": {
            "version": library.dish_rbhr_abi_version(),
            "input_size": library.dish_rbhr_input_size(),
            "output_size": library.dish_rbhr_output_size(),
            "generator_input_size": library.dish_rbhr_generator_input_size(),
            "generator_output_size": library.dish_rbhr_generator_output_size(),
            "protocol_input_size": library.dish_rbhr_protocol_input_size(),
            "protocol_output_size": library.dish_rbhr_protocol_output_size(),
            "filter_input_size": library.dish_rbhr_filter_input_size(),
            "filter_output_size": library.dish_rbhr_filter_output_size(),
        },
        "toolchain": _toolchain(),
        "python_fallback": False,
        "test_only": True,
    }


def _input(fixture: GateAFixture) -> _Input:
    return _Input(
        fixture_key=fixture.fixture_key, arm=int(fixture.arm), package=fixture.package,
        reflection=fixture.reflection, initial_owner=fixture.initial_owner,
        k_initial=fixture.k_initial, k_new=fixture.k_new, switch_tick=fixture.switch_tick,
        tau_d_tick=fixture.tau_d_tick, phase=fixture.phase, route_speed=fixture.route_speed,
        turn_magnitude_deg=fixture.turn_magnitude_deg, turn_sign=fixture.turn_sign,
        initial_ux=fixture.initial_ux, initial_uy=fixture.initial_uy,
    )


def _result(value: _Output) -> GateAResult:
    return GateAResult(**{name: getattr(value, name) for name, _ in _Output._fields_})


def run_native_batch(fixtures: Iterable[GateAFixture]) -> tuple[GateAResult, ...]:
    values = tuple(fixtures)
    if not values:
        return ()
    inputs = (_Input * len(values))(*(_input(value) for value in values))
    outputs = (_Output * len(values))()
    code = require_cpp_batched_backend().dish_rbhr_run_batch(inputs, len(values), outputs)
    if code != 0:
        raise NativeBackendError(f"native host rejected the fixture batch with code {code}")
    return tuple(_result(value) for value in outputs)


def generator_scan_native(
    requests: Iterable[tuple[int, int, int, int]],
) -> tuple[tuple[int | None, int], ...]:
    values = tuple(requests)
    if not values:
        return ()
    inputs = (_GeneratorInput * len(values))(
        *(_GeneratorInput(fixture_key=key, start=start, count=count, stratum=stratum)
          for key, start, count, stratum in values)
    )
    outputs = (_GeneratorOutput * len(values))()
    code = require_cpp_batched_backend().dish_rbhr_generator_scan_batch(inputs, len(values), outputs)
    if code != 0:
        raise NativeBackendError(f"native generator rejected the request batch with code {code}")
    return tuple((None if value.winning_ordinal < 0 else int(value.winning_ordinal), int(value.winning_word)) for value in outputs)


def rng_word_native(fixture_key: int, address: str) -> int:
    encoded = address.encode("utf-8")
    return int(require_cpp_batched_backend().dish_rbhr_rng_word(fixture_key, encoded, len(encoded)))


def protocol_apply_native(rows: Iterable[dict[str, int]]) -> tuple[dict[str, int], ...]:
    values = tuple(rows)
    if not values:
        return ()
    required = tuple(name for name, _ in _ProtocolInput._fields_)
    inputs = (_ProtocolInput * len(values))(
        *(_ProtocolInput(**{name: int(value[name]) for name in required}) for value in values)
    )
    outputs = (_ProtocolOutput * len(values))()
    code = require_cpp_batched_backend().dish_rbhr_protocol_apply_batch(inputs, len(values), outputs)
    if code != 0:
        raise NativeBackendError(f"native protocol canary rejected the batch with code {code}")
    return tuple({name: int(getattr(value, name)) for name, _ in _ProtocolOutput._fields_} for value in outputs)


def redact_observation_native(causal_rows: Iterable[Iterable[float]], forbidden_rows: Iterable[Iterable[float]]) -> tuple[tuple[float, ...], ...]:
    causal = tuple(tuple(float(item) for item in row) for row in causal_rows)
    forbidden = tuple(tuple(float(item) for item in row) for row in forbidden_rows)
    if len(causal) != len(forbidden) or any(len(row) != 54 for row in causal) or any(len(row) != 8 for row in forbidden):
        raise ValueError("observation redaction requires matched [B,54] causal and [B,8] forbidden rows")
    if not causal:
        return ()
    causal_flat = (ctypes.c_double * (len(causal)*54))(*(item for row in causal for item in row))
    forbidden_flat = (ctypes.c_double * (len(causal)*8))(*(item for row in forbidden for item in row))
    output = (ctypes.c_double * (len(causal)*54))()
    code = require_cpp_batched_backend().dish_rbhr_redact_observation_batch(causal_flat, forbidden_flat, len(causal), output)
    if code != 0:
        raise NativeBackendError(f"native observation redaction rejected the batch with code {code}")
    return tuple(tuple(float(output[row*54+column]) for column in range(54)) for row in range(len(causal)))


def filter_step_native(rows: Iterable[dict[str, object]]) -> tuple[dict[str, object], ...]:
    values = tuple(rows)
    if not values:
        return ()
    inputs = (_FilterInput * len(values))()
    for index, row in enumerate(values):
        mean = tuple(float(value) for value in row["mean"])
        covariance = tuple(float(value) for value in row["covariance"])
        z = tuple(float(value) for value in row["z"])
        if len(mean) != 4 or len(covariance) != 16 or len(z) != 2:
            raise ValueError("filter input shape mismatch")
        inputs[index] = _FilterInput((ctypes.c_double*4)(*mean), (ctypes.c_double*16)(*covariance), int(row["camera_present"]), (ctypes.c_double*2)(*z))
    outputs = (_FilterOutput * len(values))()
    code = require_cpp_batched_backend().dish_rbhr_filter_step_batch(inputs, len(values), outputs)
    if code != 0:
        raise NativeBackendError(f"native filter rejected the batch with code {code}")
    return tuple({"mean": tuple(value.mean), "covariance": tuple(value.covariance), "finite": bool(value.finite)} for value in outputs)


def certificate_native(rows: Iterable[dict[str, object]]) -> tuple[bool, ...]:
    values = tuple(rows)
    if not values:
        return ()
    fields = tuple(name for name, _ in _CertificateInput._fields_)
    inputs = (_CertificateInput * len(values))(*(_CertificateInput(**{name: row[name] for name in fields}) for row in values))
    outputs = (ctypes.c_int32 * len(values))()
    code = require_cpp_batched_backend().dish_rbhr_certificate_batch(inputs, len(values), outputs)
    if code != 0:
        raise NativeBackendError(f"native certificate rejected the batch with code {code}")
    return tuple(bool(value) for value in outputs)


def wire_sizes_native() -> dict[str, int]:
    names = ("SOURCE", "SERVICE_RELAY", "STATE", "SNAPSHOT", "READINESS", "COMMIT_INTENT", "NOOP_INTENT", "COMMIT_RESULT")
    library = require_cpp_batched_backend()
    return {name: int(library.dish_rbhr_wire_size(index)) for index, name in enumerate(names)}
