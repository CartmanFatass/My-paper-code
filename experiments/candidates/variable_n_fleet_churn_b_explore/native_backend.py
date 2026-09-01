"""Thin B-only ctypes sidecar over the frozen revision-09 public-law header.

Tick telemetry is a direct observation of a fresh shadow session.  Its
applicability to a primary R09 rollout requires exact input/action identity,
exact boundary-output equivalence, and unchanged included-source identity.
The sidecar never supplies a primary action or return.
"""

from __future__ import annotations

import ctypes
import copy
import functools
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from time import perf_counter
from typing import Mapping, Sequence

from experiments.candidates.variable_n_fleet_churn_bpcr_r09 import native_backend as _r09
from experiments.candidates.variable_n_fleet_churn_bpcr_r09.contracts import MSVC_COMPILE_FLAGS


B_ABI_VERSION = 1
B_BUILD_MAGIC = 0x564E46434254454C
MINIMUM_BATCH_WIDTH = 8
TICKS_PER_STEP = 20
PERFORMANCE_DISPOSITION = "PILOT_ONLY"
CALL_LEDGER_SCHEMA = "VNFC-BEXP-PAIRED-HOST-CALL-LEDGER-v1"
_LOAD_ONLY_BINDING: dict[str, object] | None = None

_PACKAGE = Path(__file__).resolve().parent
_SOURCE = _PACKAGE / "native" / "telemetry_backend.cpp"
_R09_NATIVE = _PACKAGE.parent / "variable_n_fleet_churn_bpcr_r09" / "native"
_R09_HEADER = _R09_NATIVE / "bpcr_general.hpp"
_R09_CHECKER = _R09_NATIVE / "bpcr_checker.hpp"
_R09_SOURCE = _R09_NATIVE / "bpcr_backend.cpp"


class NativeTelemetryError(RuntimeError):
    """The B-only native telemetry boundary is unavailable or rejected input."""


def expected_host_call_inventory(
    *,
    paired_steps: int,
    primary_sensitivity_calls: int = 0,
    primary_bcrh_calls: int = 0,
) -> dict[str, object]:
    """Canonical inventory for a fully successful paired construction path."""
    values = (paired_steps, primary_sensitivity_calls, primary_bcrh_calls)
    if any(not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("expected host-call counts must be nonnegative integers")
    return {
        "schema": CALL_LEDGER_SCHEMA,
        "primary": {
            "reset": 1,
            "step": paired_steps,
            "sensitivity": primary_sensitivity_calls,
            "bcrh": primary_bcrh_calls,
        },
        "shadow": {
            "reset": 1,
            "step": paired_steps,
            "sensitivity": 0,
            "bcrh": 0,
        },
        "paired": {"step": paired_steps},
        "close_accounting": "excluded_non_scientific_lifecycle",
    }


class _TickRow(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_int32)
        for name in (
            "post_loss_second",
            "tick_end_second",
            "integrated_ticks",
            "zone1_delivery",
            "zone2_delivery",
            "failed_zone_delivery",
            "failed_executor_state_before",
            "failed_executor_rank_before",
            "failed_executor_acquisition_elapsed_before",
            "failed_executor_state_after",
            "failed_executor_rank_after",
            "failed_executor_acquisition_elapsed_after",
            "acquisition_transition",
        )
    ]


class _StepOutput(ctypes.Structure):
    _fields_ = [
        ("interactive", _r09._InteractiveOutput),
        ("tick_count", ctypes.c_int32),
        ("ticks", _TickRow * TICKS_PER_STEP),
    ]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_identity() -> dict[str, str]:
    return {
        "b_adapter_source_sha256": _sha256(_SOURCE),
        "included_r09_header_sha256": _sha256(_R09_HEADER),
        "transitive_r09_checker_sha256": _sha256(_R09_CHECKER),
        "registered_r09_source_sha256": _sha256(_R09_SOURCE),
    }


def native_build_key(source_identity: Mapping[str, str] | None = None) -> str:
    """Return the current content key; source-derived values are never cached."""
    toolchain = _r09.native_toolchain_identity()
    digest = hashlib.sha256(b"VNFC-BPCR-BEXP-TICK-TELEMETRY-BUILD-v1\0")
    identity = dict(_source_identity() if source_identity is None else source_identity)
    for name, value in sorted(identity.items()):
        digest.update(name.encode("ascii"))
        digest.update(value.encode("ascii"))
    digest.update(str(toolchain["compiler_sha256"]).encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        digest.update(flag.encode("ascii"))
    digest.update(B_ABI_VERSION.to_bytes(4, "big"))
    return digest.hexdigest()


def _pure_filesystem_compiler_candidates(program_files_roots: Sequence[Path] | None = None) -> tuple[Path, ...]:
    roots = tuple(program_files_roots) if program_files_roots is not None else tuple(Path(value) for key in ("ProgramFiles", "ProgramFiles(x86)") if (value := os.environ.get(key)))
    found = set()
    for root in roots:
        base = Path(root) / "Microsoft Visual Studio"
        if base.is_dir(): found.update(path.resolve() for path in base.glob("**/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe") if path.is_file())
    return tuple(sorted(found, key=lambda path: str(path).casefold()))


def _r09_key_for_compiler_sha(compiler_sha256: str) -> str:
    frozen = _r09.verify_immutable_inputs(_r09._REPOSITORY_ROOT); digest = hashlib.sha256(b"VNFC-BPCR-R09-NATIVE-BUILD-v1\0")
    for item in (_r09.native_source_sha256(), _r09.contract_sha256(), str(frozen["science_card_sha256"]), str(frozen["public_law_sha256"]), compiler_sha256): digest.update(item.encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS:
        encoded = flag.encode("ascii"); digest.update(len(encoded).to_bytes(4, "big")); digest.update(encoded)
    digest.update(_r09.NATIVE_ABI_VERSION.to_bytes(4, "big")); return digest.hexdigest()


def _shadow_key_for_compiler_sha(source_identity: Mapping[str, str], compiler_sha256: str) -> str:
    digest = hashlib.sha256(b"VNFC-BPCR-BEXP-TICK-TELEMETRY-BUILD-v1\0")
    for name, value in sorted(source_identity.items()): digest.update(name.encode("ascii")); digest.update(value.encode("ascii"))
    digest.update(compiler_sha256.encode("ascii"))
    for flag in MSVC_COMPILE_FLAGS: digest.update(flag.encode("ascii"))
    digest.update(B_ABI_VERSION.to_bytes(4, "big")); return digest.hexdigest()


def resolve_prebuilt_load_only_binding(*, program_files_roots: Sequence[Path] | None = None, cache_root: Path | None = None) -> dict[str, object]:
    compilers = _pure_filesystem_compiler_candidates(program_files_roots); by_sha: dict[str, list[Path]] = {}
    for path in compilers: by_sha.setdefault(_sha256(path), []).append(path)
    cache = Path(tempfile.gettempdir()) if cache_root is None else Path(cache_root); source = _source_identity(); matches = []
    for compiler_sha, paths in sorted(by_sha.items()):
        r09_key = _r09_key_for_compiler_sha(compiler_sha); shadow_key = _shadow_key_for_compiler_sha(source, compiler_sha)
        primary = cache / "hmasd_vnfc_bpcr_r09_native" / r09_key / "bpcr_backend.dll"; shadow = cache / "hmasd_vnfc_b_tick_native" / shadow_key / "vnfc_b_tick_telemetry.dll"
        if primary.is_file() and shadow.is_file(): matches.append((compiler_sha, paths[0], r09_key, shadow_key, primary.resolve(), shadow.resolve()))
    if len(matches) != 1: raise NativeTelemetryError(f"REPAIR_REQUIRED: expected exactly one prebuilt load-only native key pair, found {len(matches)}")
    compiler_sha, compiler, r09_key, shadow_key, primary, shadow = matches[0]
    return {"schema": "VNFC_BPCR_BEXP_R01_PREBUILT_LOAD_ONLY_BINDING_V1", "compiler_path": str(compiler), "compiler_sha256": compiler_sha, "source_identity": source, "r09_build_key": r09_key, "shadow_build_key": shadow_key, "primary_artifact_path": str(primary), "primary_artifact_sha256": _sha256(primary), "primary_artifact_size": primary.stat().st_size, "shadow_artifact_path": str(shadow), "shadow_artifact_sha256": _sha256(shadow), "shadow_artifact_size": shadow.stat().st_size}


def _install_prebuilt_load_only_binding(binding: Mapping[str, object]) -> dict[str, object]:
    """Privately install only a fully rederived live filesystem binding."""
    global _LOAD_ONLY_BINDING, native_build_key, _compiled_path
    required = {"schema", "compiler_path", "compiler_sha256", "source_identity", "r09_build_key", "shadow_build_key", "primary_artifact_path", "primary_artifact_sha256", "primary_artifact_size", "shadow_artifact_path", "shadow_artifact_sha256", "shadow_artifact_size"}
    live_source = _source_identity()
    if set(binding) != required or binding.get("schema") != "VNFC_BPCR_BEXP_R01_PREBUILT_LOAD_ONLY_BINDING_V1" or binding.get("source_identity") != live_source: raise NativeTelemetryError("load-only binding schema/source differs")
    compiler = Path(str(binding["compiler_path"])).resolve()
    reparse_flag = getattr(compiler.stat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0) if compiler.exists() else 0
    if not compiler.is_file() or reparse_flag or compiler.name.casefold() != "cl.exe" or compiler not in _pure_filesystem_compiler_candidates(): raise NativeTelemetryError("load-only compiler path is not a live enumerated regular cl.exe")
    compiler_sha = _sha256(compiler)
    if binding.get("compiler_sha256") != compiler_sha: raise NativeTelemetryError("load-only compiler hash differs")
    expected_r09_key = _r09_key_for_compiler_sha(compiler_sha); expected_shadow_key = _shadow_key_for_compiler_sha(live_source, compiler_sha)
    if binding.get("r09_build_key") != expected_r09_key or binding.get("shadow_build_key") != expected_shadow_key: raise NativeTelemetryError("load-only binding keys do not rederive from live bytes")
    primary_raw, shadow_raw = Path(str(binding["primary_artifact_path"])), Path(str(binding["shadow_artifact_path"]))
    if not primary_raw.is_absolute() or not shadow_raw.is_absolute(): raise NativeTelemetryError("load-only artifact paths are not absolute")
    primary, shadow = primary_raw.resolve(), shadow_raw.resolve()
    if primary.name != "bpcr_backend.dll" or primary.parent.name != expected_r09_key or shadow.name != "vnfc_b_tick_telemetry.dll" or shadow.parent.name != expected_shadow_key: raise NativeTelemetryError("load-only artifact cache key/path differs")
    for path, sha, size in ((primary, binding["primary_artifact_sha256"], binding["primary_artifact_size"]), (shadow, binding["shadow_artifact_sha256"], binding["shadow_artifact_size"])):
        attributes = getattr(path.stat(), "st_file_attributes", 0) if path.exists() else 0
        if not path.is_file() or path.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0) or path.stat().st_size != size or _sha256(path) != sha: raise NativeTelemetryError("load-only bound artifact drifted")
    source = dict(binding["source_identity"]); r09_key, shadow_key = str(binding["r09_build_key"]), str(binding["shadow_build_key"])
    def bound_r09_key() -> str: return r09_key
    def bound_toolchain() -> dict[str, object]: return {"compiler_path": str(binding["compiler_path"]), "compiler_sha256": str(binding["compiler_sha256"]), "compile_flags": list(MSVC_COMPILE_FLAGS), "abi_version": _r09.NATIVE_ABI_VERSION, "load_only": True}
    def bound_r09_path() -> Path:
        if not primary.is_file() or _sha256(primary) != binding["primary_artifact_sha256"]: raise NativeTelemetryError("bound primary artifact drifted")
        return primary
    def bound_shadow_key(identity: Mapping[str, str] | None = None) -> str:
        if dict(source if identity is None else identity) != source: raise NativeTelemetryError("bound shadow source identity differs")
        return shadow_key
    def bound_shadow_path(key: str) -> Path:
        if key != shadow_key or not shadow.is_file() or _sha256(shadow) != binding["shadow_artifact_sha256"]: raise NativeTelemetryError("bound shadow artifact drifted")
        return shadow
    _r09.native_build_key = bound_r09_key; _r09.native_toolchain_identity = bound_toolchain; _r09._compiled_path = bound_r09_path; _r09.require_cpp_batched_backend.cache_clear()
    native_build_key = bound_shadow_key; _compiled_path = bound_shadow_path; _load_b_native_telemetry.cache_clear(); _LOAD_ONLY_BINDING = dict(binding); return dict(binding)


def active_prebuilt_load_only_binding() -> dict[str, object] | None:
    return None if _LOAD_ONLY_BINDING is None else dict(_LOAD_ONLY_BINDING)


def _compiled_path(build_key: str) -> Path:
    cache = Path(tempfile.gettempdir()) / "hmasd_vnfc_b_tick_native" / build_key
    dll = cache / "vnfc_b_tick_telemetry.dll"
    if dll.is_file():
        return dll
    cache.mkdir(parents=True, exist_ok=True)
    vcvars = _r09._vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = cache / "vnfc_b_tick_telemetry.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(MSVC_COMPILE_FLAGS)} '
        f'/D"VNFC_B_BUILD_FINGERPRINT=\\\"{build_key}\\\"" '
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
        raise NativeTelemetryError(
            f"B tick telemetry compilation failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return dll


@functools.lru_cache(maxsize=8)
def _load_b_native_telemetry(build_key: str) -> ctypes.CDLL:
    library = ctypes.CDLL(str(_compiled_path(build_key)))
    library.vnfc_b_tick_abi_version.argtypes = []
    library.vnfc_b_tick_abi_version.restype = ctypes.c_int32
    library.vnfc_b_tick_build_magic.argtypes = []
    library.vnfc_b_tick_build_magic.restype = ctypes.c_uint64
    library.vnfc_b_tick_build_fingerprint.argtypes = []
    library.vnfc_b_tick_build_fingerprint.restype = ctypes.c_char_p
    if int(library.vnfc_b_tick_abi_version()) != B_ABI_VERSION:
        raise NativeTelemetryError("B tick telemetry ABI version mismatch")
    if int(library.vnfc_b_tick_build_magic()) != B_BUILD_MAGIC:
        raise NativeTelemetryError("B tick telemetry build magic mismatch")
    sizes = {
        "vnfc_b_tick_sizeof_episode_input": _r09._EpisodeInput,
        "vnfc_b_tick_sizeof_interactive_output": _r09._InteractiveOutput,
        "vnfc_b_tick_sizeof_tick_row": _TickRow,
        "vnfc_b_tick_sizeof_step_output": _StepOutput,
    }
    for symbol, structure in sizes.items():
        function = getattr(library, symbol)
        function.argtypes = []
        function.restype = ctypes.c_size_t
        if int(function()) != ctypes.sizeof(structure):
            raise NativeTelemetryError(f"B tick telemetry ABI size mismatch for {symbol}")
    library.vnfc_b_tick_reset_batch.argtypes = [
        ctypes.POINTER(_r09._EpisodeInput),
        ctypes.c_int32,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(_r09._InteractiveOutput),
    ]
    library.vnfc_b_tick_reset_batch.restype = ctypes.c_int32
    library.vnfc_b_tick_step_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_int32),
        ctypes.c_int32,
        ctypes.POINTER(_StepOutput),
    ]
    library.vnfc_b_tick_step_batch.restype = ctypes.c_int32
    library.vnfc_b_tick_close_batch.argtypes = [
        ctypes.POINTER(ctypes.c_void_p), ctypes.c_int32
    ]
    library.vnfc_b_tick_close_batch.restype = ctypes.c_int32
    return library


def require_b_native_telemetry(
    *, expected_source_identity: Mapping[str, str] | None = None
) -> ctypes.CDLL:
    """Load the current content-addressed DLL and verify its embedded key."""
    before = _source_identity()
    if expected_source_identity is not None and before != dict(expected_source_identity):
        raise NativeTelemetryError("INCOMPLETE: B shadow source changed before load")
    build_key = native_build_key(before)
    library = _load_b_native_telemetry(build_key)
    embedded = library.vnfc_b_tick_build_fingerprint()
    embedded_key = embedded.decode("ascii") if embedded is not None else ""
    after = _source_identity()
    if after != before:
        raise NativeTelemetryError("INCOMPLETE: B shadow source changed during load")
    if embedded_key != build_key:
        raise NativeTelemetryError(
            "INCOMPLETE: loaded B artifact fingerprint differs from current build key"
        )
    library._vnfc_b_embedded_build_key = embedded_key
    library._vnfc_b_source_identity = before
    return library


def _tick_dict(row: _TickRow) -> dict[str, int | bool | None]:
    def rank(value: int) -> int | None:
        return None if value == 255 else value

    return {
        "post_loss_second": int(row.post_loss_second),
        "tick_end_second": int(row.tick_end_second),
        "integrated_ticks": int(row.integrated_ticks),
        "zone1_delivery": int(row.zone1_delivery),
        "zone2_delivery": int(row.zone2_delivery),
        "failed_zone_delivery": int(row.failed_zone_delivery),
        "failed_zone_executor_state_before": int(row.failed_executor_state_before),
        "failed_zone_executor_rank_before": rank(int(row.failed_executor_rank_before)),
        "failed_zone_executor_acquisition_elapsed_before": int(
            row.failed_executor_acquisition_elapsed_before
        ),
        "failed_zone_executor_state_after": int(row.failed_executor_state_after),
        "failed_zone_executor_rank_after": rank(int(row.failed_executor_rank_after)),
        "failed_zone_executor_acquisition_elapsed_after": int(
            row.failed_executor_acquisition_elapsed_after
        ),
        "acquisition_transition": bool(row.acquisition_transition),
    }


def derive_recovery_telemetry(
    tick_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Derive latency/count observables without replacing the retained raw rows."""
    rows = tuple(dict(row) for row in tick_rows)
    first_service = next(
        (
            int(row["post_loss_second"])
            for row in rows
            if int(row["failed_zone_delivery"]) > 0
        ),
        None,
    )
    reacquisition = next(
        (
            int(row["tick_end_second"])
            for row in rows
            if bool(row["acquisition_transition"])
        ),
        None,
    )
    early = tuple(row for row in rows if 0 <= int(row["post_loss_second"]) < 60)
    zero_service = sum(int(row["failed_zone_delivery"]) == 0 for row in early)
    return {
        "observation_scope": "fresh_b_shadow_direct",
        "primary_rollout_applicability": (
            "inference_only_after_exact_same-input/action boundary equivalence"
        ),
        "first_failed_zone_service_time_seconds": first_service,
        "failed_zone_executor_reacquisition_time_seconds": reacquisition,
        "failed_zone_zero_service_seconds_0_60": zero_service,
        "observed_failed_zone_seconds_0_60": len(early),
        "complete_0_60": len(early) == 60,
        "raw_tick_rows": rows,
    }


def require_boundary_equivalence(
    primary_rows: Sequence[Mapping[str, object]],
    shadow_rows: Sequence[Mapping[str, object]],
) -> None:
    """Fail incomplete unless every old-host and B-shadow boundary is exact."""
    primary = tuple(dict(row) for row in primary_rows)
    shadow = tuple(dict(row["interactive"]) for row in shadow_rows)
    if primary != shadow:
        raise NativeTelemetryError(
            "INCOMPLETE: B shadow and primary R09 boundary outputs differ"
        )


def _canonical_digest(value: object, schema: bytes) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(schema + b"\0" + payload).hexdigest()


def _native_input_digest(fixtures: Sequence[object]) -> str:
    digest = hashlib.sha256(b"VNFC-BEXP-PAIRED-NATIVE-INPUT-v1\0")
    digest.update(len(fixtures).to_bytes(4, "big"))
    for fixture in fixtures:
        packed = _r09._episode_input(fixture)
        payload = ctypes.string_at(ctypes.byref(packed), ctypes.sizeof(packed))
        digest.update(len(payload).to_bytes(4, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _commands_value(commands: Sequence[Sequence[object]]) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(255 if value is None else int(value) for value in row)
        for row in commands
    )


def _paired_source_snapshot(
    primary: _r09.NativeInteractiveBatch,
    shadow: "BNativeTelemetryBatch",
) -> dict[str, object]:
    primary_path = Path(vars(primary._library)["_name"]).resolve()
    shadow_path = Path(vars(shadow._library)["_name"]).resolve()
    return {
        "included_source_identity": _source_identity(),
        "shadow_build_key": native_build_key(_source_identity()),
        "shadow_embedded_build_key": shadow._library.vnfc_b_tick_build_fingerprint().decode(
            "ascii"
        ),
        "shadow_artifact_path": str(shadow_path),
        "shadow_artifact_sha256": _sha256(shadow_path),
        "primary_artifact_path": str(primary_path),
        "primary_artifact_sha256": _sha256(primary_path),
        "primary_registered_build_key": _r09.native_build_key(),
    }


class BNativeTelemetryBatch:
    """B>=8 C++-owned shadow sessions with exact per-physics-tick telemetry."""

    def __init__(
        self,
        fixtures: object,
        *,
        expected_source_identity: Mapping[str, str] | None = None,
    ):
        materialized = tuple(fixtures)  # type: ignore[arg-type]
        if len(materialized) < MINIMUM_BATCH_WIDTH:
            raise ValueError("B tick telemetry requires native batch width B>=8")
        self._width = len(materialized)
        self._source_fence = _source_identity()
        if (
            expected_source_identity is not None
            and self._source_fence != dict(expected_source_identity)
        ):
            raise NativeTelemetryError(
                "INCOMPLETE: B shadow source differs from the caller's frozen fence"
            )
        self._build_key = native_build_key(self._source_fence)
        self._library = require_b_native_telemetry(
            expected_source_identity=self._source_fence
        )
        if self._library._vnfc_b_embedded_build_key != self._build_key:
            raise NativeTelemetryError(
                "INCOMPLETE: B shadow constructor loaded a stale native artifact"
            )
        inputs = (_r09._EpisodeInput * self._width)(
            *(_r09._episode_input(fixture) for fixture in materialized)
        )
        self._handles = (ctypes.c_void_p * self._width)()
        outputs = (_r09._InteractiveOutput * self._width)()
        if _source_identity() != self._source_fence:
            raise NativeTelemetryError("INCOMPLETE: B shadow source drifted before reset")
        embedded = self._library.vnfc_b_tick_build_fingerprint()
        if embedded is None or embedded.decode("ascii") != self._build_key:
            raise NativeTelemetryError(
                "INCOMPLETE: B shadow artifact fingerprint drifted before reset"
            )
        status = self._library.vnfc_b_tick_reset_batch(
            inputs, self._width, self._handles, outputs
        )
        if status != 0:
            raise NativeTelemetryError(f"B tick telemetry reset failed with status {status}")
        try:
            if _source_identity() != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: B shadow source drifted across native reset"
                )
            embedded = self._library.vnfc_b_tick_build_fingerprint()
            if embedded is None or embedded.decode("ascii") != self._build_key:
                raise NativeTelemetryError(
                    "INCOMPLETE: B shadow artifact fingerprint drifted across reset"
                )
        except Exception:
            close_status = self._library.vnfc_b_tick_close_batch(
                self._handles, self._width
            )
            if close_status != 0:
                raise NativeTelemetryError(
                    "INCOMPLETE: B shadow reset fence failed and handles did not close"
                )
            raise
        self._open = True
        self._tick_rows: list[list[dict[str, object]]] = [
            [] for _ in range(self._width)
        ]
        self.initial = tuple(_r09._interactive_dict(output) for output in outputs)

    @property
    def width(self) -> int:
        return self._width

    def step(self, commands: object) -> tuple[dict[str, object], ...]:
        if not self._open:
            raise NativeTelemetryError("B tick telemetry batch is closed")
        if _source_identity() != self._source_fence:
            raise NativeTelemetryError("INCOMPLETE: B shadow included-source identity drifted")
        embedded = self._library.vnfc_b_tick_build_fingerprint()
        if embedded is None or embedded.decode("ascii") != self._build_key:
            raise NativeTelemetryError("INCOMPLETE: B shadow artifact fingerprint drifted")
        rows = tuple(tuple(row) for row in commands)  # type: ignore[arg-type]
        if len(rows) != self._width or any(len(row) != 4 for row in rows):
            raise ValueError("one width-four command is required per B shadow session")
        packed = (ctypes.c_int32 * (4 * self._width))()
        for index, row in enumerate(rows):
            for token, value in enumerate(row):
                packed[4 * index + token] = 255 if value is None else int(value)
        outputs = (_StepOutput * self._width)()
        status = self._library.vnfc_b_tick_step_batch(
            self._handles, packed, self._width, outputs
        )
        if status != 0:
            raise NativeTelemetryError(f"B tick telemetry step failed with status {status}")
        if _source_identity() != self._source_fence:
            raise NativeTelemetryError("INCOMPLETE: B shadow included-source identity drifted")
        converted = []
        for index, output in enumerate(outputs):
            if int(output.tick_count) != TICKS_PER_STEP:
                raise NativeTelemetryError("B tick telemetry returned an incomplete step")
            tick_rows = tuple(_tick_dict(row) for row in output.ticks)
            self._tick_rows[index].extend(tick_rows)
            converted.append(
                {
                    "interactive": _r09._interactive_dict(output.interactive),
                    "tick_rows": tick_rows,
                    "receipt": derive_recovery_telemetry(self._tick_rows[index]),
                }
            )
        return tuple(converted)

    def close(self) -> None:
        if not self._open:
            return
        status = self._library.vnfc_b_tick_close_batch(self._handles, self._width)
        if status != 0:
            raise NativeTelemetryError(f"B tick telemetry close failed with status {status}")
        self._open = False

    def __enter__(self) -> "BNativeTelemetryBatch":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class PairedPrimaryShadowBatch:
    """One-input/one-action seam for the R09 primary and B telemetry shadow."""

    def __init__(self, fixtures: object):
        materialized = tuple(fixtures)  # type: ignore[arg-type]
        if len(materialized) < MINIMUM_BATCH_WIDTH:
            raise ValueError("paired primary/shadow batch requires B>=8")
        self._width = len(materialized)
        self._source_fence = _source_identity()
        self._primary: _r09.NativeInteractiveBatch | None = None
        self._shadow: BNativeTelemetryBatch | None = None
        self._open = False
        try:
            self._primary = _r09.NativeInteractiveBatch(materialized)
            if _source_identity() != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: included source drifted across primary reset"
                )
            if _source_identity() != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: included source drifted before shadow reset"
                )
            self._shadow = BNativeTelemetryBatch(
                materialized, expected_source_identity=self._source_fence
            )
            if _source_identity() != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: included source drifted across shadow reset"
                )
            if self._primary.initial != self._shadow.initial:
                raise NativeTelemetryError(
                    "INCOMPLETE: primary and shadow reset boundaries differ"
                )
            self._input_digest = _native_input_digest(materialized)
            self._action_hasher = hashlib.sha256(
                b"VNFC-BEXP-PAIRED-ACTIONS-v1\0" + self._width.to_bytes(4, "big")
            )
            source = _paired_source_snapshot(self._primary, self._shadow)
            if source["included_source_identity"] != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source changed during construction"
                )
            self._receipt: dict[str, object] = {
                "schema": "VNFC-BEXP-PAIRED-PRIMARY-SHADOW-RECEIPT-v1",
                "input_digest": self._input_digest,
                "action_digest": self._action_hasher.hexdigest(),
                "width": self._width,
                "main_return_source": "registered_r09_native_interactive_primary",
                "shadow_role": "telemetry_only_no_action_or_return_authority",
                "authority": {
                    "scientific_trajectory_source": "registered_r09_native_interactive_primary",
                    "action_source": "single_paired_caller_command_forwarded_unchanged",
                    "scientific_return_source": "registered_r09_native_interactive_primary",
                    "shadow_effect": "read_only_deterministic_replay_telemetry",
                },
                "host_call_ledger": expected_host_call_inventory(paired_steps=0),
                "initial": {
                    "primary_full_output_digest": _canonical_digest(
                        self._primary.initial, b"VNFC-BEXP-INITIAL-OUTPUT-v1"
                    ),
                    "shadow_full_output_digest": _canonical_digest(
                        self._shadow.initial, b"VNFC-BEXP-INITIAL-OUTPUT-v1"
                    ),
                    "exact": True,
                },
                "source_pre": source,
                "source_post": source,
                "boundaries": [],
                "incomplete": False,
                "last_failure": None,
            }
            self._open = True
        except Exception as error:
            self._close_safely()
            if isinstance(error, NativeTelemetryError):
                raise
            raise NativeTelemetryError(
                f"INCOMPLETE: paired primary/shadow construction failed: {error}"
            ) from error

    @property
    def initial(self) -> tuple[dict[str, object], ...]:
        if self._primary is None:
            raise NativeTelemetryError("paired primary/shadow batch is unavailable")
        return self._primary.initial

    @property
    def receipt(self) -> dict[str, object]:
        return copy.deepcopy(self._receipt)

    def _require_open(self) -> tuple[_r09.NativeInteractiveBatch, BNativeTelemetryBatch]:
        if not self._open or self._primary is None or self._shadow is None:
            raise NativeTelemetryError("paired primary/shadow batch is closed")
        if _source_identity() != self._source_fence:
            self._mark_incomplete(
                "INCOMPLETE: paired primary/shadow included-source identity drifted"
            )
            self._close_safely()
            raise NativeTelemetryError(
                "INCOMPLETE: paired primary/shadow included-source identity drifted"
            )
        return self._primary, self._shadow

    def _increment_host_call(self, owner: str, operation: str) -> None:
        ledger = self._receipt["host_call_ledger"]
        row = ledger[owner]  # type: ignore[index]
        row[operation] = int(row[operation]) + 1  # type: ignore[index]

    def _mark_incomplete(self, error: object) -> None:
        if hasattr(self, "_receipt"):
            self._receipt["incomplete"] = True
            self._receipt["last_failure"] = str(error)

    def _close_safely(self) -> None:
        shadow, primary = self._shadow, self._primary
        self._open = False
        if shadow is not None:
            try:
                shadow.close()
            except Exception:
                pass
        if primary is not None:
            try:
                primary.close()
            except Exception:
                pass

    def step(self, commands: object) -> dict[str, object]:
        primary, shadow = self._require_open()
        supplied = tuple(tuple(row) for row in commands)  # type: ignore[arg-type]
        if len(supplied) != self._width or any(len(row) != 4 for row in supplied):
            raise ValueError("one width-four command is required by the paired seam")
        command_value = _commands_value(supplied)
        immutable = tuple(
            tuple(None if value == 255 else value for value in row)
            for row in command_value
        )
        boundary_index = len(self._receipt["boundaries"])  # type: ignore[arg-type]
        if boundary_index >= 6:
            raise NativeTelemetryError("paired primary/shadow batch is terminal")
        try:
            source_pre = _paired_source_snapshot(primary, shadow)
            if source_pre != self._receipt["source_post"]:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact changed between boundaries"
                )
            if source_pre["included_source_identity"] != self._source_fence:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source drifted before boundary"
                )
            # Scientific outputs originate here, before the observational shadow.
            primary_rows = primary.step(immutable)
            self._increment_host_call("primary", "step")
            shadow_rows = shadow.step(immutable)
            self._increment_host_call("shadow", "step")
            require_boundary_equivalence(primary_rows, shadow_rows)
            source_post = _paired_source_snapshot(primary, shadow)
            if source_post != source_pre:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact identity drifted across boundary"
                )
        except Exception as error:
            self._mark_incomplete(error)
            self._close_safely()
            if isinstance(error, NativeTelemetryError) and "INCOMPLETE" in str(error):
                raise
            raise NativeTelemetryError(
                f"INCOMPLETE: paired primary/shadow boundary failed: {error}"
            ) from error

        command_digest = _canonical_digest(
            command_value, b"VNFC-BEXP-PAIRED-BOUNDARY-ACTIONS-v1"
        )
        self._action_hasher.update(boundary_index.to_bytes(4, "big"))
        self._action_hasher.update(bytes.fromhex(command_digest))
        primary_digest = _canonical_digest(
            primary_rows, b"VNFC-BEXP-BOUNDARY-OUTPUT-v1"
        )
        shadow_interactive = tuple(row["interactive"] for row in shadow_rows)
        shadow_digest = _canonical_digest(
            shadow_interactive, b"VNFC-BEXP-BOUNDARY-OUTPUT-v1"
        )
        boundary = {
            "boundary_index": boundary_index,
            "command_digest": command_digest,
            "cumulative_action_digest": self._action_hasher.hexdigest(),
            "primary_full_output_digest": primary_digest,
            "shadow_full_output_digest": shadow_digest,
            "exact": primary_rows == shadow_interactive,
            "primary_integrated_ticks": tuple(
                int(row["integrated_ticks"]) for row in primary_rows
            ),
            "shadow_integrated_ticks": tuple(
                int(row["interactive"]["integrated_ticks"]) for row in shadow_rows
            ),
            "shadow_ticks_per_session": tuple(
                len(row["tick_rows"]) for row in shadow_rows
            ),
            "shadow_tick_rows_digest": _canonical_digest(
                tuple(row["tick_rows"] for row in shadow_rows),
                b"VNFC-BEXP-SHADOW-TICKS-v1",
            ),
            "source_exact_pre_post": True,
        }
        self._receipt["action_digest"] = self._action_hasher.hexdigest()
        self._receipt["source_post"] = source_post
        self._receipt["boundaries"].append(boundary)  # type: ignore[union-attr]
        self._increment_host_call("paired", "step")
        return {
            "primary_rows": primary_rows,
            "shadow_rows": shadow_rows,
            "receipt": self.receipt,
        }

    def bcrh(self, *, include_candidate_records: bool = False) -> tuple[dict[str, object], ...]:
        if include_candidate_records:
            raise ValueError("paired BCRH seam forbids candidate-record serialization")
        primary, shadow = self._require_open()
        try:
            source_pre = _paired_source_snapshot(primary, shadow)
            if source_pre != self._receipt["source_post"]:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact changed before BCRH"
                )
            rows = primary.bcrh(include_candidate_records=False)
            self._increment_host_call("primary", "bcrh")
            source_post = _paired_source_snapshot(primary, shadow)
            if source_post != source_pre:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact identity drifted across BCRH"
                )
            return rows
        except Exception as error:
            self._mark_incomplete(error)
            self._close_safely()
            if isinstance(error, NativeTelemetryError) and "INCOMPLETE" in str(error):
                raise
            raise NativeTelemetryError(
                f"INCOMPLETE: primary-only BCRH command query failed: {error}"
            ) from error

    def sensitivity(self) -> tuple[dict[str, object], ...]:
        """Read treatment-blind N7 diagnostics from the primary R09 host only."""
        primary, shadow = self._require_open()
        try:
            source_pre = _paired_source_snapshot(primary, shadow)
            if source_pre != self._receipt["source_post"]:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact changed before sensitivity"
                )
            rows = primary.sensitivity()
            self._increment_host_call("primary", "sensitivity")
            source_post = _paired_source_snapshot(primary, shadow)
            if source_post != source_pre:
                raise NativeTelemetryError(
                    "INCOMPLETE: paired source/artifact identity drifted across sensitivity"
                )
            if len(rows) != self._width:
                raise NativeTelemetryError(
                    "INCOMPLETE: primary sensitivity row count differs from batch width"
                )
            return rows
        except Exception as error:
            self._mark_incomplete(error)
            self._close_safely()
            if isinstance(error, NativeTelemetryError) and "INCOMPLETE" in str(error):
                raise
            raise NativeTelemetryError(
                f"INCOMPLETE: primary-only sensitivity query failed: {error}"
            ) from error

    def close(self) -> None:
        if not self._open:
            return
        primary, shadow = self._primary, self._shadow
        self._open = False
        errors: list[Exception] = []
        for batch in (shadow, primary):
            if batch is not None:
                try:
                    batch.close()
                except Exception as error:
                    errors.append(error)
        if errors:
            raise NativeTelemetryError(
                f"paired primary/shadow close failed: {errors[0]}"
            ) from errors[0]

    def __enter__(self) -> "PairedPrimaryShadowBatch":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def native_artifact_identity() -> dict[str, object]:
    started = perf_counter()
    library = require_b_native_telemetry()
    source_identity = _source_identity()
    build_key = native_build_key(source_identity)
    embedded_build_key = library.vnfc_b_tick_build_fingerprint().decode("ascii")
    if embedded_build_key != build_key:
        raise NativeTelemetryError(
            "INCOMPLETE: identity read observed a stale B native artifact"
        )
    b_path = Path(vars(library)["_name"]).resolve()
    loaded = perf_counter()
    r09_library = _r09.require_cpp_batched_backend()
    r09_path = Path(vars(r09_library)["_name"]).resolve()
    old_symbol_visible = True
    try:
        getattr(library, "vnfc_bpcr_r09_abi_version")
    except AttributeError:
        old_symbol_visible = False
    return {
        "schema": "VNFC-BPCR-BEXP-TICK-TELEMETRY-IDENTITY-v1",
        "abi_version": B_ABI_VERSION,
        "build_magic": B_BUILD_MAGIC,
        "build_key": build_key,
        "embedded_build_fingerprint": embedded_build_key,
        "artifact_path": str(b_path),
        "artifact_sha256": _sha256(b_path),
        "artifact_size": b_path.stat().st_size,
        "source_identity": source_identity,
        "included_r09_header": True,
        "copied_routing_delivery_acquisition_energy_laws": False,
        "registered_production_component": False,
        "python_fallback": False,
        "minimum_batch_width": MINIMUM_BATCH_WIDTH,
        "exports": (
            "vnfc_b_tick_abi_version",
            "vnfc_b_tick_build_magic",
            "vnfc_b_tick_build_fingerprint",
            "vnfc_b_tick_sizeof_episode_input",
            "vnfc_b_tick_sizeof_interactive_output",
            "vnfc_b_tick_sizeof_tick_row",
            "vnfc_b_tick_sizeof_step_output",
            "vnfc_b_tick_reset_batch",
            "vnfc_b_tick_step_batch",
            "vnfc_b_tick_close_batch",
        ),
        "old_r09_exports_visible_from_b_artifact": old_symbol_visible,
        "registered_r09_artifact_path": str(r09_path),
        "registered_r09_artifact_sha256": _sha256(r09_path),
        "registered_r09_build_key": _r09.native_build_key(),
        "artifact_path_distinct_from_registered_r09": b_path != r09_path,
        "load_wall_seconds": loaded - started,
    }


def performance_readiness() -> dict[str, object]:
    return {
        "disposition": PERFORMANCE_DISPOSITION,
        "reason": (
            "construction/equivalence sidecar only; no result-bearing end-to-end "
            "throughput, process-tree RSS, occupancy, scratch, durable, or I/O proof"
        ),
        "b8_construction_wall_seconds": None,
        "b32_construction_wall_seconds": None,
        "process_tree_peak_rss_bytes": None,
        "cpu_worker_occupancy": None,
        "scratch_high_water_bytes": None,
        "durable_high_water_bytes": None,
        "io_bytes_written": None,
        "shadow_overhead_included_in_primary_performance": False,
    }


__all__ = [
    "B_ABI_VERSION",
    "B_BUILD_MAGIC",
    "BNativeTelemetryBatch",
    "MINIMUM_BATCH_WIDTH",
    "NativeTelemetryError",
    "PairedPrimaryShadowBatch",
    "active_prebuilt_load_only_binding",
    "expected_host_call_inventory",
    "derive_recovery_telemetry",
    "native_artifact_identity",
    "native_build_key",
    "performance_readiness",
    "resolve_prebuilt_load_only_binding",
    "require_boundary_equivalence",
    "require_b_native_telemetry",
]
