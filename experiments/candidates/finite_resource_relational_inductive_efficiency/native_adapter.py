"""Package-owned external-action native adapter and admission boundary.

Only the batched environment ABI is exposed here.  Policy inference,
training, evaluation orchestration, checkpoint orchestration, action coding,
and RNG construction remain outside this module.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .contracts.core import (
    HOST_ID, NATIVE_ABI, NATIVE_BINDING_KIND, NATIVE_COMPONENT, SOURCE_ID,
)
from .host import NativeBackendUnavailable, NativeContract
from .native.native_abi import (
    ABI_SYMBOLS,
    ABI_VERSION,
    NATIVE_ABI_DESCRIPTOR_SCHEMA,
    NATIVE_STEP_ABI,
    STATE_SIZE,
    STATE_VERSION,
    BoundNativeABI,
    NativeStateV1,
    ObservationOutputV1,
    ResetInputV1,
    StepInputV1,
    StepOutputV1,
    bind_native_abi,
)

REQUIRED_NATIVE_STEP_ABI = NATIVE_STEP_ABI
REQUIRED_NATIVE_CAPABILITIES = tuple(ABI_SYMBOLS)

_PACKAGE_DIR = Path(__file__).resolve().parent
_NATIVE_SOURCE = _PACKAGE_DIR / "native" / "frrie_ridgegate2z_external.cpp"
_NATIVE_DIR = _PACKAGE_DIR / "_native"
_ARTIFACT_BASENAME = {
    "win32": "frrie_ridgegate2z_external.dll",
    "darwin": "libfrrie_ridgegate2z_external.dylib",
}.get(sys.platform, "libfrrie_ridgegate2z_external.so")
_CONSTRUCTION_TOKEN = object()
_FRESH_ARTIFACT_PATH: Path | None = None
_FRESH_ARTIFACT_BYTES: bytes | None = None
_LIVE_ADAPTER: PackageNativeAdapter | None = None  # type: ignore[name-defined]


class NativeCallFailed(RuntimeError):
    """A direct package-native batched ABI call returned a nonzero status."""


@dataclass(frozen=True, slots=True)
class NativeABIDescriptor:
    schema: str
    protocol: str
    artifact_path: str
    abi_version: int
    state_version: int
    state_size: int
    symbols: tuple[str, ...]
    contract: NativeContract


def package_native_artifact_path() -> Path:
    """Return the one package-internal compiled artifact location."""
    return _NATIVE_DIR / _ARTIFACT_BASENAME


def package_native_artifact_is_fresh_in_process() -> bool:
    artifact = package_native_artifact_path()
    if not artifact.is_file():
        return False
    resolved = artifact.resolve(strict=True)
    if _LIVE_ADAPTER is not None:
        return True
    return (
        _FRESH_ARTIFACT_PATH == resolved
        and _FRESH_ARTIFACT_BYTES is not None
        and artifact.read_bytes() == _FRESH_ARTIFACT_BYTES
    )


def _run_build(
    command: list[str], *, cwd: Path, environment: Mapping[str, str] | None = None,
) -> None:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
            env=dict(environment) if environment is not None else None,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeBackendUnavailable("bounded package native build could not run") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        raise NativeBackendUnavailable(f"bounded package native build failed: {detail}")


def _windows_vcvars64() -> Path:
    vswhere = Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    if not vswhere.is_file():
        raise NativeBackendUnavailable("MSVC vswhere compiler locator is unavailable")
    try:
        completed = subprocess.run(
            [
                str(vswhere), "-latest", "-products", "*", "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                "-property", "installationPath",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeBackendUnavailable("MSVC compiler discovery could not run") from exc
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not lines:
        raise NativeBackendUnavailable("MSVC x64 compiler installation is unavailable")
    vcvars = Path(lines[-1]) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not vcvars.is_file():
        raise NativeBackendUnavailable("MSVC vcvars64 environment is unavailable")
    return vcvars


def _windows_build_environment(vcvars: Path) -> tuple[str, dict[str, str]]:
    try:
        required = ctypes.windll.kernel32.GetShortPathNameW(str(vcvars), None, 0)
        short_buffer = ctypes.create_unicode_buffer(required)
        written = ctypes.windll.kernel32.GetShortPathNameW(
            str(vcvars), short_buffer, required,
        )
    except (AttributeError, OSError, ValueError) as exc:
        raise NativeBackendUnavailable("MSVC vcvars64 short-path resolution failed") from exc
    if required == 0 or written == 0:
        raise NativeBackendUnavailable("MSVC vcvars64 short-path resolution failed")
    try:
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", f"call {short_buffer.value} >nul && set"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeBackendUnavailable("MSVC vcvars64 environment could not run") from exc
    if completed.returncode != 0:
        raise NativeBackendUnavailable("MSVC vcvars64 environment initialization failed")
    environment = dict(os.environ)
    for line in completed.stdout.splitlines():
        if "=" in line and not line.startswith("="):
            name, value = line.split("=", 1)
            for existing in tuple(environment):
                if existing.casefold() == name.casefold() and existing != name:
                    environment.pop(existing)
            environment[name] = value
    path_value = next(
        (value for name, value in environment.items() if name.casefold() == "path"),
        None,
    )
    compiler = shutil.which("cl.exe", path=path_value)
    if compiler is None:
        raise NativeBackendUnavailable("MSVC vcvars64 did not expose cl.exe")
    return compiler, environment


def build_package_native_artifact() -> Path:
    """Boundedly compile the exact package source into the sole artifact path.

    There is no caller source, output, compiler, or flag override.  An existing
    artifact is retained and merely returned; this function never rebuilds it
    in place.
    """
    global _FRESH_ARTIFACT_BYTES, _FRESH_ARTIFACT_PATH
    artifact = package_native_artifact_path()
    if artifact.exists():
        if _LIVE_ADAPTER is not None:
            return _validate_package_artifact_path(artifact)
        if (
            _FRESH_ARTIFACT_PATH == artifact.resolve(strict=True)
            and _FRESH_ARTIFACT_BYTES is not None
            and artifact.read_bytes() == _FRESH_ARTIFACT_BYTES
        ):
            return _validate_package_artifact_path(artifact)
        raise NativeBackendUnavailable(
            "package native artifact already exists outside this fresh build transaction"
        )
    if not _NATIVE_SOURCE.is_file():
        raise NativeBackendUnavailable("package native source is absent")
    _NATIVE_DIR.mkdir(exist_ok=True)
    temporary = _NATIVE_DIR / f"{artifact.stem}.building-{os.getpid()}{artifact.suffix}"
    sidecars = tuple(temporary.with_suffix(suffix) for suffix in (".obj", ".pdb", ".lib", ".exp"))
    if temporary.exists() or any(path.exists() for path in sidecars):
        raise NativeBackendUnavailable("bounded package native build staging path already exists")
    try:
        if sys.platform == "win32":
            vcvars = _windows_vcvars64()
            compiler, environment = _windows_build_environment(vcvars)
            _run_build([
                compiler, "/nologo", "/std:c++17", "/O2", "/EHsc", "/LD", "/fp:strict",
                f'/Fo:{temporary.with_suffix(".obj")}',
                f'/Fd:{temporary.with_suffix(".pdb")}',
                f'/Fe:{temporary}', str(_NATIVE_SOURCE), "/link", "/NOIMPLIB",
            ], cwd=_NATIVE_DIR, environment=environment)
        else:
            compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
            if compiler is None:
                raise NativeBackendUnavailable("C++17 compiler is unavailable")
            _run_build([
                compiler, "-O3", "-std=c++17", "-shared", "-fPIC",
                "-fno-fast-math", "-ffp-contract=off",
                str(_NATIVE_SOURCE), "-o", str(temporary),
            ], cwd=_NATIVE_DIR)
        if not temporary.is_file():
            raise NativeBackendUnavailable("bounded package native build produced no artifact")
        try:
            os.link(temporary, artifact)
        except FileExistsError as exc:
            raise NativeBackendUnavailable(
                "package native artifact appeared during create-only publication"
            ) from exc
        _FRESH_ARTIFACT_PATH = artifact.resolve(strict=True)
        _FRESH_ARTIFACT_BYTES = artifact.read_bytes()
    finally:
        for path in (temporary, *sidecars):
            if path.exists():
                path.unlink()
    return _validate_package_artifact_path(artifact)


def _validate_package_artifact_path(path: Path) -> Path:
    expected = package_native_artifact_path()
    if not expected.is_absolute():
        raise NativeBackendUnavailable("package native artifact location is not absolute")
    if not path.exists() or not path.is_file():
        raise NativeBackendUnavailable("package native artifact is absent")
    try:
        resolved = path.resolve(strict=True)
        native_dir = _NATIVE_DIR.resolve(strict=True)
        expected_resolved = expected.resolve(strict=True)
    except OSError as exc:
        raise NativeBackendUnavailable("package native artifact is unavailable") from exc
    if resolved.parent != native_dir or resolved != expected_resolved:
        raise NativeBackendUnavailable("native artifact is not package-internal")
    return resolved


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NativeBackendUnavailable(f"native runtime binding {field} must be positive")
    return value


def expected_native_contract(compute: Mapping[str, Any]) -> NativeContract:
    """Build the manifest-side runtime contract without loading native code."""
    if NATIVE_ABI != REQUIRED_NATIVE_STEP_ABI:
        raise NativeBackendUnavailable("legacy autonomous native ABI is production-inadmissible")
    return NativeContract(
        HOST_ID, SOURCE_ID, NATIVE_COMPONENT, REQUIRED_NATIVE_STEP_ABI,
        NATIVE_BINDING_KIND,
        _positive_int(compute.get("native_width"), "native_width"),
        _positive_int(compute.get("workers"), "workers"),
        _positive_int(compute.get("threads"), "threads"),
        dtype=compute.get("model_dtype"),
        reduction_dtype=compute.get("reduction_dtype"),
        device=compute.get("device"),
        python_fallback=False,
        test_only=False,
    ).validate(production=True)


class PackageNativeAdapter:
    """Exact package loader product with direct batched ABI methods."""

    __slots__ = ("_bound", "_token", "descriptor", "contract")

    def __init__(
        self,
        token: object,
        bound: BoundNativeABI,
        descriptor: NativeABIDescriptor,
    ) -> None:
        if token is not _CONSTRUCTION_TOKEN:
            raise NativeBackendUnavailable(
                "package-owned native adapters must be created by the package loader"
            )
        self._token = token
        self._bound = bound
        self.descriptor = descriptor
        self.contract = descriptor.contract

    def assert_live_contract(self) -> NativeABIDescriptor:
        if self._token is not _CONSTRUCTION_TOKEN or type(self._bound.library) is not ctypes.CDLL:
            raise NativeBackendUnavailable("package-owned native adapter construction is invalid")
        _validate_package_artifact_path(Path(self.descriptor.artifact_path))
        self.contract.validate(production=True)
        if (
            self.descriptor.schema != NATIVE_ABI_DESCRIPTOR_SCHEMA
            or self.descriptor.protocol != REQUIRED_NATIVE_STEP_ABI
            or self.descriptor.abi_version != ABI_VERSION
            or self.descriptor.state_version != STATE_VERSION
            or self.descriptor.state_size != STATE_SIZE
            or self.descriptor.symbols != tuple(ABI_SYMBOLS)
        ):
            raise NativeBackendUnavailable("package native external-action ABI descriptor mismatch")
        return self.descriptor

    def _batch_count(self, value: int) -> int:
        if type(value) is not int or not 1 <= value <= self._bound.native_width:
            raise NativeCallFailed("batch_count must be a literal integer within native_width")
        return value

    @staticmethod
    def _array(
        value: object,
        element_type: type[ctypes.Structure],
        field: str,
        count: int,
    ) -> object:
        if (
            not isinstance(value, ctypes.Array)
            or getattr(type(value), "_type_", None) is not element_type
            or len(value) < count
        ):
            raise NativeCallFailed(
                f"{field} must be a direct packed native ABI array covering batch_count"
            )
        return value

    @staticmethod
    def _check(status: int, operation: str) -> None:
        if status != 0:
            raise NativeCallFailed(f"native {operation} failed with status {status}")

    def reset_batch(self, states: object, inputs: object, *, batch_count: int) -> None:
        count = self._batch_count(batch_count)
        self._array(states, NativeStateV1, "states", count)
        self._array(inputs, ResetInputV1, "inputs", count)
        self._check(
            self._bound.library.frrie_reset_batch_v1(states, inputs, count, self._bound.native_width),
            "reset_batch",
        )

    def observe_batch(self, states: object, outputs: object, *, batch_count: int) -> None:
        count = self._batch_count(batch_count)
        self._array(states, NativeStateV1, "states", count)
        self._array(outputs, ObservationOutputV1, "outputs", count)
        self._check(
            self._bound.library.frrie_observe_batch_v1(states, outputs, count, self._bound.native_width),
            "observe_batch",
        )

    def step_batch(
        self,
        states: object,
        inputs: object,
        outputs: object,
        *,
        batch_count: int,
    ) -> None:
        count = self._batch_count(batch_count)
        self._array(states, NativeStateV1, "states", count)
        self._array(inputs, StepInputV1, "inputs", count)
        self._array(outputs, StepOutputV1, "outputs", count)
        self._check(
            self._bound.library.frrie_step_batch_v1(
                states, inputs, outputs, count, self._bound.native_width,
            ),
            "step_batch",
        )

    def snapshot_batch(self, states: object, *, batch_count: int) -> bytes:
        count = self._batch_count(batch_count)
        self._array(states, NativeStateV1, "states", count)
        byte_count = STATE_SIZE * count
        buffer = ctypes.create_string_buffer(byte_count)
        self._check(
            self._bound.library.frrie_snapshot_batch_v1(
                states, buffer, byte_count, count, self._bound.native_width,
            ),
            "snapshot_batch",
        )
        return bytes(buffer.raw)

    def restore_batch(self, states: object, snapshot: bytes, *, batch_count: int) -> None:
        count = self._batch_count(batch_count)
        self._array(states, NativeStateV1, "states", count)
        if type(snapshot) is not bytes or len(snapshot) != STATE_SIZE * count:
            raise NativeCallFailed("snapshot must contain the exact direct native state bytes")
        buffer = ctypes.create_string_buffer(snapshot, len(snapshot))
        self._check(
            self._bound.library.frrie_restore_batch_v1(
                states, buffer, len(snapshot), count, self._bound.native_width,
            ),
            "restore_batch",
        )


def load_package_native_adapter(compute: Mapping[str, Any] | None = None) -> PackageNativeAdapter:
    """Load and bind the sole package-internal external-action artifact."""
    global _LIVE_ADAPTER
    if _LIVE_ADAPTER is not None:
        if compute is None or _LIVE_ADAPTER.contract != expected_native_contract(compute):
            raise NativeBackendUnavailable("live package adapter runtime compute binding mismatch")
        return admit_package_native_adapter(_LIVE_ADAPTER)
    artifact_path = _validate_package_artifact_path(package_native_artifact_path())
    if (
        _FRESH_ARTIFACT_PATH != artifact_path
        or _FRESH_ARTIFACT_BYTES is None
        or artifact_path.read_bytes() != _FRESH_ARTIFACT_BYTES
    ):
        raise NativeBackendUnavailable(
            "package native artifact requires a fresh in-process build transaction"
        )
    if compute is None:
        raise NativeBackendUnavailable("native runtime compute binding is required")
    contract = expected_native_contract(compute)
    try:
        library = ctypes.CDLL(str(artifact_path))
        bound = bind_native_abi(library, native_width=contract.native_width)
    except (AttributeError, OSError, TypeError, ValueError, RuntimeError) as exc:
        raise NativeBackendUnavailable("package native external-action ABI load failed") from exc
    descriptor = NativeABIDescriptor(
        schema=NATIVE_ABI_DESCRIPTOR_SCHEMA,
        protocol=REQUIRED_NATIVE_STEP_ABI,
        artifact_path=str(artifact_path),
        abi_version=ABI_VERSION,
        state_version=STATE_VERSION,
        state_size=STATE_SIZE,
        symbols=tuple(ABI_SYMBOLS),
        contract=contract,
    )
    _LIVE_ADAPTER = PackageNativeAdapter(_CONSTRUCTION_TOKEN, bound, descriptor)
    return _LIVE_ADAPTER


def admit_package_native_adapter(adapter: object) -> PackageNativeAdapter:
    """Admit only the exact concrete adapter loaded from this package."""
    if type(adapter) is not PackageNativeAdapter:
        raise NativeBackendUnavailable(
            "production requires the exact package-owned native adapter; caller fakes and callbacks are forbidden"
        )
    adapter.assert_live_contract()
    return adapter


def test_only_package_native_preflight(
    compute: Mapping[str, Any], *, build_if_absent: bool = False,
) -> dict[str, Any]:
    """Exercise only ABI/state-copy facts on one fixed TEST_ONLY native lane.

    This is not production admission and emits no endpoint, reward, policy,
    training, evaluation, or result value.  Building is explicit and never
    reached from :func:`preflight.prospective_preflight`.
    """
    if build_if_absent and not package_native_artifact_path().exists():
        build_package_native_artifact()
    adapter = load_package_native_adapter(compute)
    states = (NativeStateV1 * 1)()
    resets = (ResetInputV1 * 1)()
    resets[0].abi_version = ABI_VERSION
    resets[0].state_version = STATE_VERSION
    resets[0].roster = 6
    for basin, row in enumerate(((0, 3, 6), (1, 4, 7))):
        for ordinal, event_time in enumerate(row):
            resets[0].event_times[basin][ordinal] = event_time
    adapter.reset_batch(states, resets, batch_count=1)
    observations = (ObservationOutputV1 * 1)()
    adapter.observe_batch(states, observations, batch_count=1)
    snapshot = adapter.snapshot_batch(states, batch_count=1)
    steps = (StepInputV1 * 1)()
    step_outputs = (StepOutputV1 * 1)()
    steps[0].abi_version = ABI_VERSION
    for agent in range(6):
        steps[0].actions[agent] = 5  # HOLD is legal for every public role.
    adapter.step_batch(states, steps, step_outputs, batch_count=1)
    stepped_snapshot = adapter.snapshot_batch(states, batch_count=1)
    if stepped_snapshot == snapshot:
        raise NativeCallFailed("TEST_ONLY external step did not change native state bytes")
    restored = (NativeStateV1 * 1)()
    adapter.restore_batch(restored, snapshot, batch_count=1)
    if adapter.snapshot_batch(restored, batch_count=1) != snapshot:
        raise NativeCallFailed("TEST_ONLY snapshot/restore bytes differ")
    return {
        "schema": "FRRIE_PACKAGE_NATIVE_TEST_ONLY_PREFLIGHT_V2",
        "test_only": True,
        "bounded_batch_count": 1,
        "abi_descriptor": {
            "schema": adapter.descriptor.schema,
            "protocol": adapter.descriptor.protocol,
            "abi_version": adapter.descriptor.abi_version,
            "state_version": adapter.descriptor.state_version,
            "state_size": adapter.descriptor.state_size,
            "symbols": list(adapter.descriptor.symbols),
        },
        "native_contract": asdict(adapter.contract),
        "reset_observe_legal_step_snapshot_restore": True,
        "snapshot_restore_branch_isolation": True,
        "endpoint_values_read": False,
        "scientific_activity_started": False,
    }


__all__ = [
    "NATIVE_ABI_DESCRIPTOR_SCHEMA", "REQUIRED_NATIVE_STEP_ABI",
    "REQUIRED_NATIVE_CAPABILITIES", "NativeCallFailed", "NativeABIDescriptor",
    "PackageNativeAdapter", "package_native_artifact_path",
    "package_native_artifact_is_fresh_in_process",
    "build_package_native_artifact", "test_only_package_native_preflight",
    "load_package_native_adapter", "admit_package_native_adapter",
    "expected_native_contract",
]
