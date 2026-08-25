"""Source/ABI/compiler/Python/Torch-keyed loader for the V2 native host."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from collections.abc import MutableMapping
import hashlib
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading
from types import ModuleType

import numpy as np
import torch

from .native_contract import (
    ABI_VERSION,
    HOST_KIND,
    LANGUAGE_STANDARD,
    MODE_FULL_ROTATED,
    MODE_INTACT,
    NATIVE_THREADS,
    ActorParameters,
    FactualEpisodeBatch,
    FactualTrajectory,
    NativeSuffixResult,
    ShadowTrajectory,
    SuffixBatch,
    validate_actor_parameters,
    validate_factual_episode_batch,
    validate_suffix_batch,
)


_SOURCE = Path(__file__).with_name("native") / "rscf_r01_full_suffix_host.cpp"
_LOCK = threading.Lock()
_MODULES: dict[str, ModuleType] = {}
_IDENTITIES: dict[str, "NativeHostIdentity"] = {}
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_ACCEPTED_BUILD_KEY_SHA256 = "0c14c2f7b3fa5840fe53a01ca7c9e219ba9309907533af2f971fa66f590cd5c9"
_ACCEPTED_ARTIFACT_SHA256 = "4a09f6e71eff77333e00aa30f0adcafc162485279a41a7fa79e9dec851d53962"
_ACCEPTED_ARTIFACT_SIZE_BYTES = 249_344


def _merge_case_insensitive_environment(
    output: str, target: MutableMapping[str, str]
) -> None:
    """Import `cmd set` output with Windows first-wins name semantics.

    Some managed shells expose both a vcvars-produced ``PATH=`` and a later
    stale inherited ``Path=``.  Windows treats those names as identical, so a
    sequential merge would silently discard the compiler path.  Collapse all
    incoming names case-insensitively before mutating the target; the first
    vcvars value remains authoritative and the later alias cannot overwrite it.
    """

    existing_names = {name.casefold(): name for name in target}
    imported: set[str] = set()
    for line in output.splitlines():
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        folded = name.casefold()
        if not name or folded in imported:
            continue
        imported.add(folded)
        target[existing_names.get(folded, name)] = value


def _ensure_compiler_environment() -> str:
    """Load the installed x64 MSVC environment and return the exact compiler path."""

    compiler = shutil.which("cl" if os.name == "nt" else "c++")
    if compiler is not None:
        return str(Path(compiler).resolve(strict=True))
    if os.name != "nt":
        raise RuntimeError("C++ compiler is unavailable")
    candidates = (
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"),
    )
    script = next((candidate for candidate in candidates if candidate.is_file()), None)
    if script is None:
        raise RuntimeError("MSVC x64 environment script is unavailable")
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
    _merge_case_insensitive_environment(completed.stdout, os.environ)
    compiler = shutil.which("cl")
    if compiler is None:
        raise RuntimeError("MSVC x64 environment did not expose cl.exe")
    return str(Path(compiler).resolve(strict=True))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _retained_prebuilt_artifact_path(module_name: str) -> Path:
    return (
        Path(__file__).with_name("native")
        / "accepted"
        / _ACCEPTED_ARTIFACT_SHA256
        / f"{module_name}.pyd"
    ).resolve(strict=False)


def _verify_prebuilt_artifact_bytes(path: Path) -> Path:
    artifact = path.resolve(strict=True)
    if artifact.stat().st_size != _ACCEPTED_ARTIFACT_SIZE_BYTES:
        raise RuntimeError("retained native artifact size differs from the accepted tuple")
    if _sha256(artifact) != _ACCEPTED_ARTIFACT_SHA256:
        raise RuntimeError("retained native artifact hash differs from the accepted tuple")
    return artifact


def _load_authenticated_prebuilt_module(module_name: str) -> ModuleType:
    """Import the exact retained extension without Torch cache/build activity."""

    expected_name = f"sgsp_rscf_native_v4_{_ACCEPTED_BUILD_KEY_SHA256[:20]}"
    if module_name != expected_name:
        raise RuntimeError("prebuilt native module name differs from the accepted build identity")
    artifact = _verify_prebuilt_artifact_bytes(
        _retained_prebuilt_artifact_path(module_name)
    )
    existing = sys.modules.get(module_name)
    if existing is not None:
        existing_path = Path(str(getattr(existing, "__file__", ""))).resolve(strict=True)
        if existing_path != artifact:
            raise RuntimeError("native module name is already bound to a non-retained path")
        return existing
    spec = importlib.util.spec_from_file_location(module_name, artifact)
    if spec is None or spec.loader is None:
        raise RuntimeError("retained native artifact has no Python extension loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    if Path(str(module.__file__)).resolve(strict=True) != artifact:
        raise RuntimeError("retained native module loaded from a different path")
    _verify_prebuilt_artifact_bytes(artifact)
    return module


def _expected_flags() -> tuple[str, ...]:
    if os.name == "nt":
        return ("/O2", "/std:c++17", "/EHsc", "/fp:precise")
    return ("-O3", "-std=c++17", "-ffp-contract=off", "-fno-fast-math")


@dataclass(frozen=True)
class NativeHostIdentity:
    abi_version: str
    host_kind: str
    source_path: str
    source_sha256: str
    source_key: str
    build_key_sha256: str
    module_name: str
    artifact_path: str
    artifact_sha256: str
    artifact_size_bytes: int
    compiler_id: str
    compiler_flags: tuple[str, ...]
    language_standard: str
    python_version: str
    python_cache_tag: str
    torch_version: str
    platform_tag: str
    native_threads: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _build_descriptor(source_sha256: str, compiler_path: str) -> tuple[str, dict[str, object]]:
    descriptor: dict[str, object] = {
        "abi_version": ABI_VERSION,
        "host_kind": HOST_KIND,
        "source_sha256": source_sha256,
        "compiler_family": "MSVC" if os.name == "nt" else "POSIX-CXX",
        "compiler_path": compiler_path,
        "compiler_sha256": _sha256(Path(compiler_path)),
        "compiler_flags": _expected_flags(),
        "language_standard": LANGUAGE_STANDARD,
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "torch_version": torch.__version__,
        "platform_tag": platform.platform(),
        "machine": platform.machine(),
        "native_threads": NATIVE_THREADS,
    }
    encoded = repr(tuple(sorted(descriptor.items()))).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), descriptor


def _verify_module(module: ModuleType, module_name: str) -> tuple[Path, str, tuple[str, ...]]:
    if module.__name__ != module_name:
        raise RuntimeError(f"native module-name mismatch: {module.__name__!r} != {module_name!r}")
    if module.abi_version() != ABI_VERSION:
        raise RuntimeError("native ABI mismatch")
    if module.host_kind() != HOST_KIND:
        raise RuntimeError("native host-kind mismatch")
    if module.language_standard() != LANGUAGE_STANDARD:
        raise RuntimeError("native language-standard mismatch")
    if int(module.native_threads()) != NATIVE_THREADS:
        raise RuntimeError("native thread-count mismatch")
    flags = tuple(str(module.compiler_flags()).split("|"))
    if flags != _expected_flags():
        raise RuntimeError(f"native compiler-flag mismatch: {flags!r}")
    artifact = Path(module.__file__).resolve(strict=True)
    if module_name not in artifact.name:
        raise RuntimeError("native artifact basename does not carry keyed module identity")
    return artifact, str(module.compiler_id()), flags


def _verify_identity(identity: NativeHostIdentity) -> None:
    if identity.abi_version != ABI_VERSION or identity.host_kind != HOST_KIND:
        raise RuntimeError("alternate ABI/host identity rejected")
    source = Path(identity.source_path).resolve(strict=True)
    if source != _SOURCE.resolve(strict=True) or _sha256(source) != identity.source_sha256:
        raise RuntimeError("native source identity changed after load")
    artifact = Path(identity.artifact_path).resolve(strict=True)
    if _sha256(artifact) != identity.artifact_sha256:
        raise RuntimeError("native artifact hash changed after load")
    if artifact.stat().st_size != identity.artifact_size_bytes:
        raise RuntimeError("native artifact size changed after load")
    if identity.compiler_flags != _expected_flags() or identity.native_threads != 1:
        raise RuntimeError("stale compiler/thread identity rejected")


def load_native_host(expected_identity: NativeHostIdentity | None = None) -> NativeHostIdentity:
    """Build/load the exact keyed host and return its verified immutable identity."""

    source = _SOURCE.resolve(strict=True)
    source_sha256 = _sha256(source)
    compiler_path = _ensure_compiler_environment()
    build_key, descriptor = _build_descriptor(source_sha256, compiler_path)
    if build_key != _ACCEPTED_BUILD_KEY_SHA256:
        raise RuntimeError("current compiler/runtime binding differs from the accepted native build")
    module_name = f"sgsp_rscf_native_v4_{build_key[:20]}"
    with _LOCK:
        module = _MODULES.get(build_key)
        identity = _IDENTITIES.get(build_key)
        if module is None:
            module = _load_authenticated_prebuilt_module(module_name)
            artifact, compiler_id, verified_flags = _verify_module(module, module_name)
            identity = NativeHostIdentity(
                abi_version=ABI_VERSION,
                host_kind=HOST_KIND,
                source_path=str(source),
                source_sha256=source_sha256,
                source_key=source_sha256[:16],
                build_key_sha256=build_key,
                module_name=module_name,
                artifact_path=str(artifact),
                artifact_sha256=_sha256(artifact),
                artifact_size_bytes=artifact.stat().st_size,
                compiler_id=compiler_id,
                compiler_flags=verified_flags,
                language_standard=LANGUAGE_STANDARD,
                python_version=str(descriptor["python_version"]),
                python_cache_tag=str(descriptor["python_cache_tag"]),
                torch_version=str(descriptor["torch_version"]),
                platform_tag=str(descriptor["platform_tag"]),
                native_threads=NATIVE_THREADS,
            )
            _MODULES[build_key] = module
            _IDENTITIES[build_key] = identity
        assert identity is not None
        _verify_module(module, module_name)
        _verify_identity(identity)
        if expected_identity is not None and identity != expected_identity:
            raise RuntimeError("loaded native identity differs from exact expected identity")
        return identity


def require_cpp_batched_backend(*, build_root: str | Path | None = None) -> ModuleType:
    """Return the authenticated full reset-to-terminal extension for the shared guard."""

    if build_root is not None:
        raise ValueError("the retained source-keyed SGSP host rejects build_root overrides")
    identity = load_native_host()
    return _MODULES[identity.build_key_sha256]


def native_factual_trajectory(
    episode: FactualEpisodeBatch,
    parameters: ActorParameters,
    *,
    mode: str = MODE_INTACT,
    identity: NativeHostIdentity | None = None,
) -> FactualTrajectory:
    """Execute the native reset-to-terminal factual path with no fallback."""

    validate_factual_episode_batch(episode)
    validate_actor_parameters(parameters)
    if mode not in (MODE_INTACT, MODE_FULL_ROTATED):
        raise ValueError(f"unsupported factual mode {mode}")
    loaded_identity = load_native_host(expected_identity=identity)
    module = _MODULES[loaded_identity.build_key_sha256]
    raw = module.run_factual_trajectory(
        episode.as_native_dict(), parameters.as_native_dict(), mode
    )
    width = episode.width
    required = {
        "observations": (np.float32, (width, 12, 21, 22)),
        "messages": (np.float32, (width, 12, 21, 32)),
        "role_summaries": (np.float32, (width, 12, 21, 32)),
        "denominators": (np.float32, (width, 12, 21)),
        "incoming_hidden": (np.float32, (width, 12, 21, 64)),
        "post_gru_hidden": (np.float32, (width, 12, 21, 64)),
        "legal_probabilities": (np.float32, (width, 12, 21, 6)),
        "factual_actions": (np.int64, (width, 12, 21)),
        "fifo_basin": (np.int64, (width, 12, 21, 4)),
        "fifo_ordinal": (np.int64, (width, 12, 21, 4)),
        "fifo_birth": (np.int64, (width, 12, 21, 4)),
        "scheduled_count": (np.int64, (width, 12)),
        "delivered": (np.int64, (width, 12, 2, 3)),
        "metrics": (np.int64, (width, 12, 8)),
        "previous_action": (np.int64, (width, 12, 21)),
        "previous_success": (np.int64, (width, 12, 21)),
        "snapshot_digest": (np.uint64, (width, 12)),
        "origin_slot": (np.int64, (width, 3)),
        "origin_agent": (np.int64, (width, 3)),
        "origin_snapshot_digest": (np.uint64, (width, 3)),
        "terminal_return": (np.float32, (width,)),
        "final_delivered": (np.int64, (width, 2)),
        "final_metrics": (np.int64, (width, 8)),
        "common_tape_digest": (np.uint64, (width,)),
        "trajectory_digest": (np.uint64, (width,)),
        "active": (np.bool_, (width,)),
    }
    if set(raw) != set(required):
        raise RuntimeError("native factual trajectory output schema mismatch")
    outputs: dict[str, np.ndarray] = {}
    for name, (dtype, shape) in required.items():
        value = np.asarray(raw[name])
        if value.dtype != np.dtype(dtype) or value.shape != shape or not value.flags.c_contiguous:
            raise RuntimeError(f"native factual output {name} violates ABI")
        if value.dtype == np.float32 and not np.isfinite(value).all():
            raise RuntimeError(f"native factual output {name} is nonfinite")
        value.setflags(write=False)
        outputs[name] = value
    for lane in np.flatnonzero(outputs["active"]):
        for role in range(3):
            slot = int(outputs["origin_slot"][lane, role])
            if outputs["origin_snapshot_digest"][lane, role] != outputs["snapshot_digest"][lane, slot]:
                raise RuntimeError("native selector origin is not bound to its exact slot snapshot")
    return FactualTrajectory(
        **outputs,
        parameter_digest=parameters.digest,
        mode=mode,
        abi_version=ABI_VERSION,
    )


def native_shadow_trajectory(
    episode: FactualEpisodeBatch,
    intact: FactualTrajectory,
    parameters: ActorParameters,
    *,
    identity: NativeHostIdentity | None = None,
) -> ShadowTrajectory:
    """Run native one-step rotated summaries on fixed intact trace inputs."""

    if intact.mode != MODE_INTACT:
        raise ValueError("shadow input must be INTACT")
    validate_factual_episode_batch(episode)
    validate_actor_parameters(parameters)
    loaded_identity = load_native_host(expected_identity=identity)
    module = _MODULES[loaded_identity.build_key_sha256]
    trace_input = {
        "observations": intact.observations,
        "messages": intact.messages,
        "incoming_hidden": intact.incoming_hidden,
        "snapshot_digest": intact.snapshot_digest,
        "active": intact.active,
    }
    raw = module.run_shadow_trajectory(
        episode.as_native_dict(), trace_input, parameters.as_native_dict()
    )
    width = episode.width
    required = {
        "role_summaries": (np.float32, (width, 12, 21, 32)),
        "denominators": (np.float32, (width, 12, 21)),
        "post_gru_hidden": (np.float32, (width, 12, 21, 64)),
        "legal_probabilities": (np.float32, (width, 12, 21, 6)),
        "snapshot_digest": (np.uint64, (width, 12)),
        "active": (np.bool_, (width,)),
    }
    if set(raw) != set(required):
        raise RuntimeError("native shadow output schema mismatch")
    outputs: dict[str, np.ndarray] = {}
    for name, (dtype, shape) in required.items():
        value = np.asarray(raw[name])
        if value.dtype != np.dtype(dtype) or value.shape != shape or not value.flags.c_contiguous:
            raise RuntimeError(f"native shadow output {name} violates ABI")
        if value.dtype == np.float32 and not np.isfinite(value).all():
            raise RuntimeError(f"native shadow output {name} is nonfinite")
        value.setflags(write=False)
        outputs[name] = value
    return ShadowTrajectory(
        **outputs,
        parameter_digest=parameters.digest,
        abi_version=ABI_VERSION,
    )


def native_full_suffix(
    batch: SuffixBatch,
    parameters: ActorParameters,
    *,
    identity: NativeHostIdentity | None = None,
) -> NativeSuffixResult:
    """Execute only the verified native host; there is no Python fallback."""

    validate_suffix_batch(batch)
    validate_actor_parameters(parameters)
    loaded_identity = load_native_host(expected_identity=identity)
    _verify_identity(loaded_identity)
    module = _MODULES[loaded_identity.build_key_sha256]
    raw = module.run_suffix(batch.as_native_dict(), parameters.as_native_dict())
    required = {
        "terminal_target": (np.float32, (batch.width,)),
        "final_delivered": (np.int64, (batch.width, 2)),
        "final_metrics": (np.int64, (batch.width, 8)),
        "counters": (np.int64, (batch.width, 4)),
        "common_tape_digest": (np.uint64, (batch.width,)),
        "audit_digest": (np.uint64, (batch.width,)),
        "factual_suffix_candidate": (np.bool_, (batch.width,)),
        "factual_suffix_identity": (np.bool_, (batch.width,)),
        "active": (np.bool_, (batch.width,)),
    }
    outputs: dict[str, np.ndarray] = {}
    if set(raw) != set(required):
        raise RuntimeError(f"native output schema mismatch: {set(raw)!r}")
    for name, (dtype, shape) in required.items():
        value = np.asarray(raw[name])
        if value.dtype != np.dtype(dtype) or value.shape != shape or not value.flags.c_contiguous:
            raise RuntimeError(f"native output {name} violates ABI")
        if value.dtype == np.float32 and not np.isfinite(value).all():
            raise RuntimeError(f"native output {name} is nonfinite")
        value.setflags(write=False)
        outputs[name] = value
    return NativeSuffixResult(
        **outputs,
        parameter_digest=parameters.digest,
        abi_version=ABI_VERSION,
    )
