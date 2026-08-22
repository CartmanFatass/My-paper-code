"""Source/ABI/compiler/Python/Torch-keyed loader for the V2 native host."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
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
from torch.utils.cpp_extension import load

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


def _ensure_ninja_on_path() -> None:
    """Expose the environment-owned Ninja binary without selecting another toolchain."""

    try:
        import ninja  # type: ignore[import-not-found]
    except ImportError as error:
        raise RuntimeError("the required environment-local Ninja package is unavailable") from error
    bin_dir = str(Path(ninja.BIN_DIR).resolve(strict=True))
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    if bin_dir not in path_entries:
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")


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
    for line in completed.stdout.splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            os.environ[name] = value
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
    module_name = f"sgsp_rscf_native_v3_{build_key[:20]}"
    with _LOCK:
        module = _MODULES.get(build_key)
        identity = _IDENTITIES.get(build_key)
        if module is None:
            _ensure_ninja_on_path()
            flags = list(_expected_flags())
            module = load(
                name=module_name,
                sources=[str(source)],
                extra_cflags=flags,
                with_cuda=False,
                verbose=False,
                is_python_module=True,
            )
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
        "observations": (np.float64, (width, 12, 21, 22)),
        "messages": (np.float64, (width, 12, 21, 32)),
        "role_summaries": (np.float64, (width, 12, 21, 32)),
        "denominators": (np.float64, (width, 12, 21)),
        "incoming_hidden": (np.float64, (width, 12, 21, 64)),
        "post_gru_hidden": (np.float64, (width, 12, 21, 64)),
        "legal_probabilities": (np.float64, (width, 12, 21, 6)),
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
        "terminal_return": (np.float64, (width,)),
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
        if value.dtype == np.float64 and not np.isfinite(value).all():
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
        "role_summaries": (np.float64, (width, 12, 21, 32)),
        "denominators": (np.float64, (width, 12, 21)),
        "post_gru_hidden": (np.float64, (width, 12, 21, 64)),
        "legal_probabilities": (np.float64, (width, 12, 21, 6)),
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
        if value.dtype == np.float64 and not np.isfinite(value).all():
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
        "terminal_target": (np.float64, (batch.width,)),
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
        if value.dtype == np.float64 and not np.isfinite(value).all():
            raise RuntimeError(f"native output {name} is nonfinite")
        value.setflags(write=False)
        outputs[name] = value
    return NativeSuffixResult(
        **outputs,
        parameter_digest=parameters.digest,
        abi_version=ABI_VERSION,
    )
