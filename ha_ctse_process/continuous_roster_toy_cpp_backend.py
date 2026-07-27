"""Batched CPU C++ slice for the continuous-roster toy environment.

Python retains ledger generation, lifecycle preparation, mutable environment
state, trajectory assembly, and all fail-closed boundary checks.  The native
module performs only the deterministic six-coordinate observation and immediate
reward arithmetic for a synchronous batch.
"""

from __future__ import annotations

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
from typing import Final, Sequence

import numpy as np

from ha_ctse_process import runtime_capacity_continuous_roster_g32 as g32


_SOURCE: Final[Path] = (
    Path(__file__).resolve().parent
    / "native"
    / "continuous_roster_toy_backend.cpp"
)
_BUILD_INTERFACE_VERSION: Final[str] = "continuous_roster_toy_v1"
_LOADED_MODULES: dict[tuple[str, str], ModuleType] = {}


class ContinuousRosterToyCppUnavailable(RuntimeError):
    """Raised when the registered CPU native toolchain cannot load the slice."""


def _safe_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


def _compiler_flags() -> tuple[str, ...]:
    if os.name == "nt":
        return "/O2", "/std:c++17", "/EHsc", "/fp:precise"
    return "-O3", "-std=c++17", "-ffp-contract=off", "-fno-fast-math"


@lru_cache(maxsize=1)
def _configure_windows_toolchain() -> None:
    if os.name != "nt":
        return
    if (
        shutil.which("cl") is not None
        and shutil.which("ninja") is not None
        and os.environ.get("VSCMD_ARG_TGT_ARCH")
    ):
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
    vcvars = installation / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not cl.is_file() or not ninja.is_file() or not vcvars.is_file():
        raise ContinuousRosterToyCppUnavailable(
            "MSVC x64, vcvars64, and Ninja are required at the registered Build Tools path"
        )
    try:
        command_processor = os.environ.get("COMSPEC", "cmd.exe")
        completed = subprocess.run(
            f'"{command_processor}" /d /s /c ""{vcvars}" >nul && set"',
            capture_output=True,
            check=True,
            text=True,
            timeout=30.0,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ContinuousRosterToyCppUnavailable(
            "failed to activate the registered MSVC x64 environment"
        ) from error
    activated: dict[str, str] = {}
    for row in completed.stdout.splitlines():
        if "=" in row:
            name, value = row.split("=", 1)
            if name == name.upper():
                activated[name] = value
    for name, value in activated.items():
        os.environ[name] = value
    tool_path = os.pathsep.join((str(ninja.parent), activated.get("PATH", "")))
    # The desktop host can expose both PATH and Path.  Keep them identical so
    # child-process environment serialization cannot select the stale spelling.
    os.environ["PATH"] = tool_path
    os.environ["Path"] = tool_path
    if shutil.which("cl") is None or shutil.which("ninja") is None:
        raise ContinuousRosterToyCppUnavailable(
            "the activated MSVC environment did not expose cl and Ninja"
        )


@lru_cache(maxsize=1)
def _build_identity() -> str:
    try:
        import torch
    except ImportError as error:  # pragma: no cover - deployment failure path
        raise ContinuousRosterToyCppUnavailable(
            "PyTorch is required to build the toy C++ backend"
        ) from error
    _configure_windows_toolchain()
    compiler_name = os.environ.get("CXX") or ("cl" if os.name == "nt" else "c++")
    compiler = shutil.which(compiler_name)
    if compiler is None:
        raise ContinuousRosterToyCppUnavailable(
            "the registered CPU C++ compiler is unavailable"
        )
    compiler_path = Path(compiler).resolve()
    compiler_stat = compiler_path.stat()
    material = "|".join(
        (
            hashlib.sha256(_SOURCE.read_bytes()).hexdigest(),
            "\0".join(_compiler_flags()),
            str(compiler_path),
            str(compiler_stat.st_size),
            str(compiler_stat.st_mtime_ns),
            str(torch.__version__),
            sys.implementation.cache_tag or "unknown_python",
            platform.machine() or "unknown_cpu",
            _BUILD_INTERFACE_VERSION,
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def _default_build_root() -> Path:
    configured = os.environ.get("HMASD_TOY_CPP_BUILD_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / "hmasd_toy_cpp_extensions"


def load_continuous_roster_toy_cpp_backend(
    *, build_root: str | os.PathLike[str] | None = None, verbose: bool = False
) -> ModuleType:
    """Build or reuse the ABI/source-keyed CPU module outside tracked files."""

    if not _SOURCE.is_file():
        raise ContinuousRosterToyCppUnavailable(f"native source is missing: {_SOURCE}")
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
        raise ContinuousRosterToyCppUnavailable(
            "torch.utils.cpp_extension is unavailable"
        ) from error

    build_directory = root / f"build_{identity}"
    build_directory.mkdir(parents=True, exist_ok=True)
    staged_source = build_directory / "continuous_roster_toy_backend.cpp"
    source_bytes = _SOURCE.read_bytes()
    if not staged_source.exists() or staged_source.read_bytes() != source_bytes:
        staged_source.write_bytes(source_bytes)
    module_name = f"hmasd_continuous_roster_toy_{identity}"
    try:
        module = load(
            name=module_name,
            sources=[str(staged_source)],
            extra_cflags=list(_compiler_flags()),
            build_directory=str(build_directory),
            with_cuda=False,
            is_python_module=True,
            verbose=verbose,
        )
    except Exception as error:  # cpp_extension exposes toolchain-specific errors
        raise ContinuousRosterToyCppUnavailable(
            "failed to build/load the continuous-roster toy C++ backend"
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


def observe_six_batch(
    *,
    capabilities: np.ndarray,
    priorities: np.ndarray,
    loads: np.ndarray,
    target_mixes: np.ndarray,
    active_mask: np.ndarray,
    log_counts: np.ndarray,
    time_fraction: np.float32,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the stateless six-coordinate observation slice."""

    capability_rows = _require_array(
        "capabilities", capabilities, dtype=np.dtype(np.float32), rank=3, trailing=2
    )
    priority_rows = _require_array(
        "priorities", priorities, dtype=np.dtype(np.float32), rank=2
    )
    load_rows = _require_array("loads", loads, dtype=np.dtype(np.float32), rank=1)
    mix_rows = _require_array(
        "target_mixes", target_mixes, dtype=np.dtype(np.float32), rank=1
    )
    active_rows = _require_array(
        "active_mask", active_mask, dtype=np.dtype(np.bool_), rank=2
    )
    log_rows = _require_array(
        "log_counts", log_counts, dtype=np.dtype(np.float32), rank=1
    )
    batch, capacity, _ = capability_rows.shape
    if (
        priority_rows.shape != (batch, capacity)
        or active_rows.shape != (batch, capacity)
        or load_rows.shape != (batch,)
        or mix_rows.shape != (batch,)
        or log_rows.shape != (batch,)
    ):
        raise ValueError("toy observation batch shapes do not match")
    fraction = np.float32(time_fraction)
    if not np.isfinite(fraction):
        raise ValueError("time_fraction must be finite")
    raw = load_continuous_roster_toy_cpp_backend().observe_six_batch(
        capability_rows,
        priority_rows,
        load_rows,
        mix_rows,
        active_rows,
        log_rows,
        fraction,
    )
    return _checked_observation_payload(
        raw, batch=batch, capacity=capacity, active_mask=active_rows
    )


def _checked_observation_payload(
    raw: object, *, batch: int, capacity: int, active_mask: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    if not isinstance(raw, tuple) or len(raw) != 2:
        raise RuntimeError("native toy observation returned an invalid payload")
    expected = (
        ((batch, capacity, 6), np.dtype(np.float32)),
        ((batch, g32.CRITIC_STATE_DIM), np.dtype(np.float32)),
    )
    checked: list[np.ndarray] = []
    for index, (value, (shape, dtype)) in enumerate(zip(raw, expected)):
        if not isinstance(value, np.ndarray):
            raise RuntimeError(f"native toy observation output {index} is not an array")
        if value.shape != shape or value.dtype != dtype or not value.flags.c_contiguous:
            raise RuntimeError(
                f"native toy observation output {index} violated shape/dtype/layout"
            )
        if not np.isfinite(value).all():
            raise RuntimeError(f"native toy observation output {index} is non-finite")
        checked.append(value)
    if np.count_nonzero(checked[0][~active_mask]):
        raise RuntimeError("native toy observation populated an inactive member")
    return checked[0], checked[1]


def reward_batch(
    *,
    capabilities: np.ndarray,
    active_mask: np.ndarray,
    actions: np.ndarray,
    loads: np.ndarray,
    target_mixes: np.ndarray,
) -> np.ndarray:
    """Run the stateless immediate-reward slice without implicit conversions."""

    capability_rows = _require_array(
        "capabilities", capabilities, dtype=np.dtype(np.float32), rank=3, trailing=2
    )
    active_rows = _require_array(
        "active_mask", active_mask, dtype=np.dtype(np.bool_), rank=2
    )
    action_rows = _require_array(
        "actions", actions, dtype=np.dtype(np.float32), rank=3, trailing=2
    )
    load_rows = _require_array("loads", loads, dtype=np.dtype(np.float32), rank=1)
    mix_rows = _require_array(
        "target_mixes", target_mixes, dtype=np.dtype(np.float32), rank=1
    )
    batch, capacity, _ = capability_rows.shape
    if (
        active_rows.shape != (batch, capacity)
        or action_rows.shape != (batch, capacity, g32.ACTION_DIM)
        or load_rows.shape != (batch,)
        or mix_rows.shape != (batch,)
    ):
        raise ValueError("toy reward batch shapes do not match")
    if np.any(np.abs(action_rows) > 1.0):
        raise ValueError("toy actions exceed registered support")
    if np.count_nonzero(action_rows[~active_rows]):
        raise ValueError("toy inactive actions must be exactly zero")
    raw = load_continuous_roster_toy_cpp_backend().reward_batch(
        capability_rows, active_rows, action_rows, load_rows, mix_rows
    )
    return _checked_reward_payload(raw, batch=batch)


def _checked_reward_payload(raw: object, *, batch: int) -> np.ndarray:
    if (
        not isinstance(raw, np.ndarray)
        or raw.shape != (batch,)
        or raw.dtype != np.dtype(np.float64)
        or not raw.flags.c_contiguous
        or not np.isfinite(raw).all()
        or np.any(raw < 0.0)
        or np.any(raw > 1.0)
    ):
        raise RuntimeError("native toy reward violated payload constraints")
    return raw


class ContinuousRosterToyBatch:
    """Python-owned synchronous environment batch with two native arithmetic slices."""

    def __init__(self, envs: Sequence[g32.RuntimeCapacityRosterEnv]):
        rows = tuple(envs)
        if not rows:
            raise ValueError("toy batch requires at least one environment")
        capacity = rows[0].ledger.member_capacity
        if any(
            not isinstance(env, g32.RuntimeCapacityRosterEnv)
            or env.ledger.member_capacity != capacity
            or env.time != rows[0].time
            or env._terminated
            or env._prepared_time is not None
            for env in rows
        ):
            raise ValueError("toy batch environments are not synchronously compatible")
        self.envs = rows
        self.batch_size = len(rows)
        self.member_capacity = capacity
        self._capabilities = np.ascontiguousarray(
            np.stack([env.ledger.capabilities for env in rows]), dtype=np.float32
        )
        self._priorities = np.ascontiguousarray(
            np.stack([env.ledger.presentation_priority for env in rows], axis=1),
            dtype=np.float32,
        )
        self._loads = np.ascontiguousarray(
            np.stack([env.ledger.load for env in rows], axis=1), dtype=np.float32
        )
        self._target_mixes = np.ascontiguousarray(
            np.stack([env.ledger.target_mix for env in rows], axis=1), dtype=np.float32
        )
        self._active = np.ascontiguousarray(
            np.stack([env.active for env in rows]), dtype=np.bool_
        )
        self._ages = np.ascontiguousarray(
            np.stack([env.age for env in rows]), dtype=np.int64
        )
        self._previous_actions = np.ascontiguousarray(
            np.stack([env.previous_actions for env in rows]), dtype=np.float32
        )
        _require_array(
            "batched capabilities",
            self._capabilities,
            dtype=np.dtype(np.float32),
            rank=3,
            trailing=2,
        )
        _require_array(
            "batched priorities",
            self._priorities,
            dtype=np.dtype(np.float32),
            rank=3,
        )
        _require_array(
            "batched loads", self._loads, dtype=np.dtype(np.float32), rank=2
        )
        _require_array(
            "batched target mixes",
            self._target_mixes,
            dtype=np.dtype(np.float32),
            rank=2,
        )
        self._active_rows = tuple(self._active[index] for index in range(self.batch_size))
        self._age_rows = tuple(self._ages[index] for index in range(self.batch_size))
        self._previous_rows = tuple(
            self._previous_actions[index] for index in range(self.batch_size)
        )
        for index, env in enumerate(rows):
            env.active = self._active_rows[index]
            env.age = self._age_rows[index]
            env.previous_actions = self._previous_rows[index]
        self._module = load_continuous_roster_toy_cpp_backend()
        self._last_views: tuple[g32.CapacityRosterView, ...] | None = None

    def _validate_state_binding(self) -> None:
        for index, env in enumerate(self.envs):
            if (
                env.active is not self._active_rows[index]
                or env.age is not self._age_rows[index]
                or env.previous_actions is not self._previous_rows[index]
            ):
                raise RuntimeError("toy batch environment state binding changed")

    def observe_six(self) -> tuple[g32.CapacityRosterView, ...]:
        """Prepare Python lifecycle state, then construct one native observation batch."""

        self._validate_state_binding()
        times = {env.time for env in self.envs}
        if len(times) != 1 or any(env._terminated for env in self.envs):
            raise RuntimeError("toy batch observation clock mismatch")
        time = times.pop()
        for env in self.envs:
            env._prepare_membership()
        counts = self._active.sum(axis=1, dtype=np.int64)
        if np.any(counts <= 0):
            raise RuntimeError("toy source produced an empty roster")
        log_counts = np.ascontiguousarray(np.log1p(counts), dtype=np.float32)
        loads = self._loads[time]
        target_mixes = self._target_mixes[time]
        raw = self._module.observe_six_batch(
            self._capabilities,
            self._priorities[time],
            loads,
            target_mixes,
            self._active,
            log_counts,
            np.float32(time / (g32.HORIZON - 1)),
        )
        observations, critic_states = _checked_observation_payload(
            raw,
            batch=self.batch_size,
            capacity=self.member_capacity,
            active_mask=self._active,
        )
        views = tuple(
            g32.CapacityRosterView(
                time,
                observations[index],
                self._active_rows[index].copy(),
                critic_states[index],
                env._change,
                float(loads[index]),
                float(target_mixes[index]),
            )
            for index, env in enumerate(self.envs)
        )
        self._last_views = views
        return views

    def advance(
        self,
        views: tuple[g32.CapacityRosterView, ...],
        actions: np.ndarray,
    ) -> np.ndarray:
        """Compute rewards natively and apply all state transitions in Python."""

        self._validate_state_binding()
        if views is not self._last_views:
            raise RuntimeError("toy batch advance requires its latest observation tuple")
        time = self.envs[0].time
        if any(
            env.time != time
            or env._terminated
            or view.time != time
            or not np.array_equal(view.active_mask, self._active_rows[index])
            for index, (env, view) in enumerate(zip(self.envs, views))
        ):
            raise RuntimeError("toy batch environment/view clock mismatch")
        values = _require_array(
            "actions", actions, dtype=np.dtype(np.float32), rank=3, trailing=2
        )
        if values.shape != (
            self.batch_size,
            self.member_capacity,
            g32.ACTION_DIM,
        ):
            raise ValueError("toy batch action shape mismatch")
        if np.any(np.abs(values) > 1.0):
            raise ValueError("toy actions exceed registered support")
        if np.count_nonzero(values[~self._active]):
            raise ValueError("toy inactive actions must be exactly zero")
        raw = self._module.reward_batch(
            self._capabilities,
            self._active,
            values,
            self._loads[time],
            self._target_mixes[time],
        )
        rewards = _checked_reward_payload(raw, batch=self.batch_size)
        counts = self._active.sum(axis=1, dtype=np.int64)
        self._previous_actions[self._active] = values[self._active]
        self._ages[self._active] += 1
        for index, env in enumerate(self.envs):
            reward = float(rewards[index])
            env.reward_trace.append(reward)
            env.roster_sizes.append(int(counts[index]))
            env.time += 1
            env._prepared_time = None
            env._change = g32.MembershipChange()
            env._terminated = env.time == g32.HORIZON
        self._last_views = None
        return rewards
