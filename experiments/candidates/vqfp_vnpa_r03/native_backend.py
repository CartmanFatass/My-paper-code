"""Source/ABI-keyed C++20 loader for the exact r03 full-chain component.

Python owns build/load and fixture marshalling only.  There is deliberately no
Python production implementation and no fallback after admission failure.
"""

from __future__ import annotations

import ctypes
import functools
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

from .contract import (
    EXACT_REVISION, NATIVE_ABI_VERSION, SCIENCE_CARD_SHA256,
    SUPPORTED_BATCH_WIDTHS, validate_cost_collapse_limits,
    validate_synthetic_limits,
)

_SOURCE = Path(__file__).with_name("native") / "vqfp_vnpa_r03.cpp"
_FLAGS = ("/nologo", "/std:c++20", "/O2", "/EHsc", "/LD")


class NativeBackendError(RuntimeError):
    """The exact native source/toolchain/runtime boundary failed closed."""


def source_sha256() -> str:
    return hashlib.sha256(_SOURCE.read_bytes()).hexdigest()


def _vs_installation() -> Path:
    locator = Path("C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe")
    if not locator.is_file():
        raise NativeBackendError("Visual Studio locator is unavailable")
    try:
        result = subprocess.run(
            [str(locator), "-latest", "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property",
             "installationPath"],
            check=True, capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise NativeBackendError("Visual Studio discovery failed") from exc
    installation = Path(result.stdout.strip())
    if not installation.is_dir():
        raise NativeBackendError("MSVC build tools are unavailable")
    return installation


def _compiler_path() -> Path:
    files = tuple(
        path for path in (_vs_installation() / "VC/Tools/MSVC").glob(
            "*/bin/Hostx64/x64/cl.exe"
        ) if path.is_file()
    )
    if not files:
        raise NativeBackendError("the x64 MSVC compiler is unavailable")
    return max(files, key=lambda path: path.stat().st_mtime_ns).resolve()


def _runtime_identity() -> dict[str, object]:
    compiler = _compiler_path()
    return {
        "abi": NATIVE_ABI_VERSION,
        "revision": EXACT_REVISION,
        "science_card_sha256": SCIENCE_CARD_SHA256,
        "source_sha256": source_sha256(),
        "compiler": str(compiler),
        "compiler_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
        "flags": _FLAGS,
        "platform": platform.platform(),
        "pointer_bits": ctypes.sizeof(ctypes.c_void_p) * 8,
        "python_cache_tag": sys.implementation.cache_tag,
    }


def _artifact_path(build_root: str | Path | None = None) -> tuple[Path, dict[str, object]]:
    identity = _runtime_identity()
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    root = Path(build_root).resolve() if build_root else Path(tempfile.gettempdir()).resolve() / "hmasd_vqfp_vnpa_r03"
    return root / key / "vqfp_vnpa_r03.dll", identity


def _build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = path.parent / "vqfp_vnpa_r03.source.cpp"
    source = _SOURCE.read_bytes()
    if not snapshot.exists() or snapshot.read_bytes() != source:
        snapshot.write_bytes(source)
    candidate = path.parent / "vqfp_vnpa_r03.candidate.dll"
    vcvars = _vs_installation() / "VC/Auxiliary/Build/vcvars64.bat"
    obj = path.parent / "vqfp_vnpa_r03.obj"
    command = (
        f'call "{vcvars}" >nul && cl {" ".join(_FLAGS)} "{snapshot}" '
        f'/Fo:"{obj}" /link /OUT:"{candidate}"'
    )
    try:
        result = subprocess.run(command, shell=True, executable=os.environ.get("COMSPEC", "cmd.exe"),
                                cwd=path.parent, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NativeBackendError("native C++20 compilation did not complete") from exc
    if result.returncode or not candidate.is_file():
        raise NativeBackendError(
            "native C++20 compilation failed:\n" + (result.stdout + result.stderr)[-8000:]
        )
    candidate.replace(path)


def _bind(lib: ctypes.CDLL) -> ctypes.CDLL:
    lib.vqfp_vnpa_r03_abi.argtypes = []; lib.vqfp_vnpa_r03_abi.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_revision.argtypes = []; lib.vqfp_vnpa_r03_revision.restype = ctypes.c_char_p
    lib.vqfp_vnpa_r03_science_card_sha256.argtypes = []; lib.vqfp_vnpa_r03_science_card_sha256.restype = ctypes.c_char_p
    lib.vqfp_vnpa_r03_philox.argtypes = [ctypes.c_uint64, *([ctypes.c_uint32] * 4), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_philox.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_uniform.argtypes = [ctypes.c_uint64, *([ctypes.c_uint32] * 4), ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint64)]; lib.vqfp_vnpa_r03_uniform.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_uniform_full.argtypes = [ctypes.c_uint64, *([ctypes.c_uint32] * 4), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint64)]; lib.vqfp_vnpa_r03_uniform_full.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_encode_address.argtypes = [*([ctypes.c_uint32] * 6), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_encode_address.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_markov_next.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_markov_next.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_resample_position.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_resample_position.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_u32_little_endian.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint8)]; lib.vqfp_vnpa_r03_u32_little_endian.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_test_rejection_injected.argtypes = [ctypes.c_uint32, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_test_rejection_injected.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_geometry.argtypes = [*([ctypes.c_uint32] * 6), ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_geometry.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_geometry_full.argtypes = [*([ctypes.c_uint32] * 4), ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_uint32)]; lib.vqfp_vnpa_r03_geometry_full.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_exact_rational_binary.argtypes = [*([ctypes.c_char_p] * 4), ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint64]; lib.vqfp_vnpa_r03_exact_rational_binary.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_fixture_audit.argtypes = [ctypes.c_char_p, ctypes.c_uint64]; lib.vqfp_vnpa_r03_fixture_audit.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_chain_benchmark.argtypes = [*([ctypes.c_uint32] * 4), ctypes.POINTER(ctypes.c_uint64)]; lib.vqfp_vnpa_r03_chain_benchmark.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_stage_slice.argtypes = [*([ctypes.c_uint32] * 5), ctypes.POINTER(ctypes.c_uint64), ctypes.c_char_p, ctypes.c_uint64]; lib.vqfp_vnpa_r03_stage_slice.restype = ctypes.c_int
    lib.vqfp_vnpa_r03_production_execute_guard.argtypes = []; lib.vqfp_vnpa_r03_production_execute_guard.restype = ctypes.c_int
    return lib


@functools.lru_cache(maxsize=8)
def _load_cached(path_text: str) -> ctypes.CDLL:
    path = Path(path_text)
    if not path.is_file():
        _build(path)
    try:
        return _bind(ctypes.CDLL(str(path)))
    except OSError as exc:
        raise NativeBackendError("native artifact load failed") from exc


def require_cpp_batched_backend(*, build_root: str | Path | None = None) -> ctypes.CDLL:
    path, _ = _artifact_path(build_root)
    lib = _load_cached(str(path))
    if lib.vqfp_vnpa_r03_abi() != NATIVE_ABI_VERSION:
        raise NativeBackendError("native ABI mismatch")
    if lib.vqfp_vnpa_r03_revision().decode("ascii") != EXACT_REVISION:
        raise NativeBackendError("native exact-revision mismatch")
    if lib.vqfp_vnpa_r03_science_card_sha256().decode("ascii") != SCIENCE_CARD_SHA256:
        raise NativeBackendError("native science-card identity mismatch")
    return lib


def artifact_identity(*, build_root: str | Path | None = None) -> dict[str, object]:
    started = time.perf_counter(); path, identity = _artifact_path(build_root)
    existed = path.is_file(); require_cpp_batched_backend(build_root=build_root)
    return {
        **identity, "artifact": str(path), "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "warm_reuse": existed, "load_seconds": time.perf_counter() - started,
        "python_fallback": False, "supported_batch_widths": SUPPORTED_BATCH_WIDTHS,
    }


def philox_words(root: int, counter: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    if not 0 <= root < 1 << 64 or len(counter) != 4 or any(not 0 <= x < 1 << 32 for x in counter):
        raise ValueError("root/counter outside unsigned width")
    out = (ctypes.c_uint32 * 4)()
    code = require_cpp_batched_backend().vqfp_vnpa_r03_philox(root, *counter, out)
    if code: raise NativeBackendError(f"native Philox failed closed ({code})")
    return tuple(int(x) for x in out)


def addressed_uniform(root: int, c1: int, c2: int, c3: int, m: int, *, max_rho: int = 1 << 20) -> tuple[int, int]:
    if not 0 <= root < 1 << 64:
        raise ValueError("root outside unsigned 64-bit width")
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 1 << 32
           for value in (c1, c2, c3)):
        raise ValueError("counter word outside unsigned 32-bit width")
    if isinstance(m, bool) or not isinstance(m, int) or not 0 < m < 1 << 32:
        raise ValueError("target size outside [1,2^32)")
    if isinstance(max_rho, bool) or not isinstance(max_rho, int) or not 0 <= max_rho < 1 << 34:
        raise ValueError("rejection ordinal would wrap c0")
    value, rho = ctypes.c_uint32(), ctypes.c_uint64()
    code = require_cpp_batched_backend().vqfp_vnpa_r03_uniform(root, c1, c2, c3, m, max_rho, ctypes.byref(value), ctypes.byref(rho))
    if code == 3: raise NativeBackendError("RNG_ADDRESS_EXHAUSTED")
    if code: raise NativeBackendError(f"native uniform failed closed ({code})")
    return int(value.value), int(rho.value)


_FAMILIES = {name:index for index,name in enumerate((
    "treatment", "free", "development_geometry", "development_markov",
    "validation_geometry", "validation_markov", "evaluation_geometry",
    "evaluation_markov", "bootstrap_block", "bootstrap_episode",
))}


def encode_address(family: str, *parameters: int) -> tuple[int, int, int, int, int]:
    if family not in _FAMILIES or len(parameters) > 5:
        raise ValueError("unregistered address family or arity")
    values = (*parameters, *((0,) * (5-len(parameters))))
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 1 << 32 for value in values):
        raise ValueError("address parameter outside unsigned 32-bit width")
    root, words = ctypes.c_uint64(), (ctypes.c_uint32 * 4)()
    code = require_cpp_batched_backend().vqfp_vnpa_r03_encode_address(
        _FAMILIES[family], *values, ctypes.byref(root), words,
    )
    if code:
        raise ValueError("invalid parameters for frozen address family")
    return int(root.value), *(int(word) for word in words)


def markov_next(current: int, draw: int) -> int:
    out=ctypes.c_uint32()
    code=require_cpp_batched_backend().vqfp_vnpa_r03_markov_next(current,draw,ctypes.byref(out))
    if code: raise ValueError("invalid Markov state/draw")
    return int(out.value)


def canonical_resample_position(p: int, h: int, counts: tuple[int, ...]) -> int:
    if len(counts)!=6: raise ValueError("six state counts required")
    packed=(ctypes.c_uint32*6)(*counts);out=ctypes.c_uint32()
    code=require_cpp_batched_backend().vqfp_vnpa_r03_resample_position(p,h,packed,ctypes.byref(out))
    if code: raise ValueError("invalid resample position")
    return int(out.value)


def little_endian_u32(word: int) -> bytes:
    if not 0<=word<1<<32: raise ValueError("word outside unsigned width")
    out=(ctypes.c_uint8*4)();code=require_cpp_batched_backend().vqfp_vnpa_r03_u32_little_endian(word,out)
    if code: raise NativeBackendError("native little-endian encoder failed")
    return bytes(out)


def injected_rejection(*, m: int, max_rho: int, forced_rejections: int, accepted_word: int) -> tuple[int,int,int]:
    rho,c0,lane=ctypes.c_uint64(),ctypes.c_uint32(),ctypes.c_uint32()
    code=require_cpp_batched_backend().vqfp_vnpa_r03_test_rejection_injected(m,max_rho,forced_rejections,accepted_word,ctypes.byref(rho),ctypes.byref(c0),ctypes.byref(lane))
    if code==3: raise NativeBackendError("RNG_ADDRESS_EXHAUSTED")
    if code: raise ValueError("invalid injected rejection fixture")
    return int(rho.value),int(c0.value),int(lane.value)


def geometry_offsets(purpose: str, block: int, roster: int, episode: int, *, test_max_g: int | None = None, test_flags: int = 0) -> tuple[tuple[int,...],int]:
    purposes={"development":0,"validation":1,"evaluation":2}
    if purpose not in purposes: raise ValueError("unregistered geometry purpose")
    out=(ctypes.c_int32*roster)();accepted_g=ctypes.c_uint32();lib=require_cpp_batched_backend()
    if test_max_g is None:
        code=lib.vqfp_vnpa_r03_geometry_full(purposes[purpose],block,roster,episode,out,ctypes.byref(accepted_g))
    else:
        code=lib.vqfp_vnpa_r03_geometry(purposes[purpose],block,roster,episode,test_max_g,test_flags,out,ctypes.byref(accepted_g))
    if code==3: raise NativeBackendError("RNG_ADDRESS_EXHAUSTED")
    if code: raise ValueError("invalid frozen geometry cell")
    return tuple(map(int,out)),int(accepted_g.value)


def exact_rational_binary(a: tuple[int, int], b: tuple[int, int], operation: str) -> str | bool:
    """Exercise the native arbitrary-width rational boundary on fixture data."""
    operation_code = {"add": 0, "sub": 1, "mul": 2, "div": 3, "lt": 4, "eq": 5}
    if operation not in operation_code:
        raise ValueError("unregistered exact-rational operation")
    parts = tuple(str(value).encode("ascii") for value in (*a, *b))
    lib = require_cpp_batched_backend()
    probe = ctypes.create_string_buffer(1)
    need = lib.vqfp_vnpa_r03_exact_rational_binary(*parts, operation_code[operation], probe, 1)
    if need >= 0 or need == -1:
        raise NativeBackendError("exact-rational size probe failed closed")
    out = ctypes.create_string_buffer(-need)
    size = lib.vqfp_vnpa_r03_exact_rational_binary(*parts, operation_code[operation], out, len(out))
    if size < 0:
        raise NativeBackendError("native exact-rational operation failed closed")
    value = bytes(out.raw[:size]).decode("ascii")
    return value == "1" if operation in {"lt", "eq"} else value


def fixture_audit() -> bytes:
    lib = require_cpp_batched_backend(); probe = ctypes.create_string_buffer(1)
    need = lib.vqfp_vnpa_r03_fixture_audit(probe, 1)
    if need >= 0: raise NativeBackendError("fixture size probe did not fail closed")
    out = ctypes.create_string_buffer(-need)
    size = lib.vqfp_vnpa_r03_fixture_audit(out, len(out))
    if size < 0: raise NativeBackendError("fixture audit failed")
    return bytes(out.raw[:size])


def synthetic_benchmark(*, width: int, candidates: int, episodes: int, draws: int) -> dict[str, int]:
    validate_synthetic_limits(candidates=candidates, episodes=episodes, draws=draws)
    if width not in SUPPORTED_BATCH_WIDTHS: raise ValueError("unsupported batch width")
    out = (ctypes.c_uint64 * 5)()
    code = require_cpp_batched_backend().vqfp_vnpa_r03_chain_benchmark(width, candidates, episodes, draws, out)
    if code: raise NativeBackendError(f"synthetic native benchmark failed ({code})")
    return dict(zip(("checksum", "philox_words", "policy_cell_states", "resample_blocks", "width"), map(int, out)))


def cost_collapse_slice(
    *, width: int, workers: int, candidates: int, host_episodes: int, draws: int
) -> tuple[bytes, dict[str, int]]:
    """Run one bounded native stage-R01 slice and return canonical opaque bytes."""
    validate_cost_collapse_limits(
        width=width, workers=workers, candidates=candidates,
        host_episodes=host_episodes, draws=draws,
    )
    lib = require_cpp_batched_backend()
    metrics = (ctypes.c_uint64 * 56)()
    # The frozen caps bound canonical output below 16 MiB.  A single native
    # pass avoids recomputing exact host/control/reducer work for a size probe.
    out = ctypes.create_string_buffer(16 * 1024 * 1024)
    size = lib.vqfp_vnpa_r03_stage_slice(
        width, host_episodes, candidates, draws, workers, metrics, out, len(out),
    )
    if size < 0:
        raise NativeBackendError("native cost-collapse slice failed closed")
    names = (
        "host_episodes", "tape_states", "score_rows", "paired_selections",
        "exact_operations", "fixed_width_hits", "arbitrary_width_slow_paths",
        "max_operand_bits", "candidate_aggregates", "candidate_ties",
        "j_reductions", "r_reductions", "canonical_bytes", "workers",
        "tile_width", "rank_values",
    )
    flat = dict(zip(names, map(int, metrics[:16])))
    kernel_names = (
        "host_materialization",
        "controls_u_z_treatment_free_lr_oracle_order",
        "candidate_aggregate_merge",
        "paired_j_r_composite_rank_reducer",
    )
    kernel_metrics: dict[str, dict[str, object]] = {}
    for index, name in enumerate(kernel_names):
        base = 16 + 10 * index
        values = list(map(int, metrics[base:base + 10]))
        kernel_metrics[name] = {
            "operations": values[0], "operands": values[1],
            "fixed_width_hits": values[2], "arbitrary_width_slow_paths": values[3],
            "max_operand_bits": values[4],
            "operand_bit_length_bands": {
                "0_32": values[5], "33_64": values[6], "65_128": values[7],
                "129_256": values[8], "257_plus": values[9],
            },
        }
    flat["kernel_instrumentation"] = kernel_metrics
    flat["instrumentation_semantics"] = (
        "one operation per exact rational/integer add, subtract, multiply, divide, "
        "comparison, reducer accumulation, mean construction, or rank comparison; "
        "each operation records both logical operands before execution"
    )
    return bytes(out.raw[:size]), flat


def production_execute_guard() -> None:
    code = require_cpp_batched_backend().vqfp_vnpa_r03_production_execute_guard()
    if code != 77: raise NativeBackendError("production activity guard contract changed")
    raise NativeBackendError("ACTIVITY_AUTHORITY_REQUIRED: construction cannot execute frozen science")
