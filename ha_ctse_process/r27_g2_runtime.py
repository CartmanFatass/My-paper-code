"""Fail-closed runtime and evidence helpers for the frozen R27-G2 audit.

These helpers deliberately contain no rollout or intervention policy.  They
implement restoration, direct state comparison, RNG capture, and deterministic
CUDA contracts for the frozen diagnostic.
"""

from __future__ import annotations

import copy
import inspect
import os
import random
import struct
import types
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import PurePath
from typing import Any, Callable

import numpy as np
import torch


class R27G2ContractError(RuntimeError):
    """A fail-closed violation of the registered R27-G2 source contract."""


RUNTIME_ATTRIBUTE_NAMES = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "team_intent_remaining",
    "team_intent_age",
    "low_actor_hxs",
    "low_critic_hxs",
    "_last_low_context",
    "segments",
    "situation_debouncer",
    "per_agent_situation_debouncer",
    "situation_hazard_guard",
    "_last_situation_state",
    "_last_agent_situation_state",
    "_team_transition_open",
    "_team_transition_closed",
    "_team_transition_env_steps",
    "_team_intent_boundary_count",
    "_team_intent_boundary_trunc_fracs",
    "_team_intent_boundary_trunc_by_duration",
    "_team_intent_dwell_checks",
    "_team_intent_age_check_samples",
    "_situation_diag_events",
    "_agent_situation_diag_events",
    "_situation_hazard_forced_renewals",
    "_situation_hazard_events",
)

REQUIRED_CUBLAS_WORKSPACE_CONFIG = ":4096:8"


@dataclass(frozen=True)
class CanonicalEntry:
    """One typed, path-addressed value in a canonical evidence encoding."""

    path: str
    type_name: str
    payload: bytes


@dataclass(frozen=True)
class EnvironmentStateSnapshot:
    entries: tuple[CanonicalEntry, ...]


@dataclass(frozen=True)
class LegacyRandomStateSnapshot:
    algorithm: str
    keys_dtype: str
    keys_shape: tuple[int, ...]
    keys_bytes: bytes
    position: int
    has_gauss: int
    cached_gaussian_bytes: bytes


@dataclass(frozen=True)
class GeneratorStateSnapshot:
    bit_generator_type: str
    state_entries: tuple[CanonicalEntry, ...]


@dataclass(frozen=True)
class EnvironmentRNGState:
    scenario_random_state: LegacyRandomStateSnapshot
    adapter_generator_state: GeneratorStateSnapshot


@dataclass(frozen=True)
class GlobalRNGState:
    python_state_entries: tuple[CanonicalEntry, ...]
    numpy_state: LegacyRandomStateSnapshot
    torch_cpu_state: bytes
    torch_cuda_states: tuple[bytes, ...]
    cuda_captured: bool


@dataclass(frozen=True, eq=False)
class ModuleStateEntry:
    """One cloned tensor from a directly named module state entry."""

    attribute_name: str
    module_type: str
    state_name: str
    value: torch.Tensor


@dataclass(frozen=True)
class DeterministicCUDAContract:
    device: str
    cuda_was_initialized: bool
    cublas_workspace_config: str
    deterministic_algorithms: bool
    cudnn_deterministic: bool
    cudnn_benchmark: bool
    cuda_matmul_allow_tf32: bool
    cudnn_allow_tf32: bool


_MISSING = object()


def _qualified_type(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, byteorder="big", signed=False) + value


def _float_bytes(value: float) -> bytes:
    return struct.pack(">d", float(value))


def _complex_bytes(value: complex) -> bytes:
    return _float_bytes(float(value.real)) + _float_bytes(float(value.imag))


def _tensor_bytes(value: torch.Tensor) -> bytes:
    if value.layout != torch.strided or bool(value.is_quantized):
        raise R27G2ContractError(
            f"unsupported tensor layout for canonical evidence: {value.layout}"
        )
    tensor = value.detach().cpu().contiguous()
    if tensor.numel() == 0:
        return b""
    return tensor.reshape(-1).view(torch.uint8).numpy().tobytes(order="C")


def _numpy_dtype_payload(dtype: np.dtype[Any]) -> bytes:
    if dtype.hasobject:
        raise R27G2ContractError("object-dtype arrays are not canonical evidence")
    description = repr(dtype.descr) if dtype.fields is not None else dtype.str
    return description.encode("utf-8")


def _render_or_plot_handle(value: Any) -> bool:
    """Classify renderer/plot handles by their type, never by field name."""

    handle_tokens = (
        "renderer",
        "renderhandle",
        "figurecanvas",
        "plotter",
    )
    exact_names = {
        "axes",
        "figure",
        "canvas",
        "viewer",
        "surface",
        "window",
        "display",
    }
    for cls in type(value).__mro__:
        name = cls.__name__.lower()
        module = cls.__module__.lower()
        if any(token in name for token in handle_tokens) or name in exact_names:
            return True
        if module.startswith(("matplotlib.", "pygame.", "pyglet.", "opengl.")):
            if any(
                token in name
                for token in ("canvas", "figure", "axes", "render", "window", "surface")
            ):
                return True
    return False


def _gym_space_types() -> tuple[type[Any], ...]:
    result: list[type[Any]] = []
    try:
        from gymnasium.spaces import Space as GymnasiumSpace

        result.append(GymnasiumSpace)
    except ImportError:
        pass
    try:
        from gym.spaces import Space as LegacyGymSpace

        result.append(LegacyGymSpace)
    except ImportError:
        pass
    return tuple(result)


_GYM_SPACE_TYPES = _gym_space_types()


def _is_rng_object(value: Any) -> bool:
    rng_types: tuple[type[Any], ...] = (
        random.Random,
        np.random.RandomState,
        np.random.Generator,
        np.random.BitGenerator,
        torch.Generator,
    )
    return isinstance(value, rng_types)


def _is_environment_excluded(value: Any) -> bool:
    if isinstance(value, (types.ModuleType, type)):
        return True
    if inspect.isroutine(value) or callable(value):
        return True
    if _GYM_SPACE_TYPES and isinstance(value, _GYM_SPACE_TYPES):
        return True
    if _render_or_plot_handle(value):
        return True
    return _is_rng_object(value)


def _canonical_order_blob(value: Any) -> bytes:
    entries = _canonical_entries(value, root="order", exclude=None)
    payload = bytearray()
    for entry in entries:
        payload.extend(_frame(entry.path.encode("utf-8")))
        payload.extend(_frame(entry.type_name.encode("utf-8")))
        payload.extend(_frame(entry.payload))
    return bytes(payload)


def _canonical_entries(
    value: Any,
    *,
    root: str = "root",
    exclude: Callable[[Any], bool] | None = None,
    seen: dict[int, str] | None = None,
) -> tuple[CanonicalEntry, ...]:
    entries: list[CanonicalEntry] = []
    references = {} if seen is None else seen

    def visit(current: Any, path: str) -> None:
        if exclude is not None and exclude(current):
            return

        type_name = _qualified_type(current)
        if current is None:
            entries.append(CanonicalEntry(path, type_name, b""))
            return
        if isinstance(current, bool):
            entries.append(CanonicalEntry(path, type_name, b"1" if current else b"0"))
            return
        if isinstance(current, int) and not isinstance(current, bool):
            entries.append(CanonicalEntry(path, type_name, str(current).encode("ascii")))
            return
        if isinstance(current, float):
            entries.append(CanonicalEntry(path, type_name, _float_bytes(current)))
            return
        if isinstance(current, complex):
            entries.append(CanonicalEntry(path, type_name, _complex_bytes(current)))
            return
        if isinstance(current, str):
            entries.append(CanonicalEntry(path, type_name, current.encode("utf-8")))
            return
        if isinstance(current, (bytes, bytearray, memoryview)):
            entries.append(CanonicalEntry(path, type_name, bytes(current)))
            return
        if isinstance(current, PurePath):
            entries.append(CanonicalEntry(path, type_name, str(current).encode("utf-8")))
            return
        if isinstance(current, Enum):
            entries.append(
                CanonicalEntry(path, type_name, str(current.name).encode("utf-8"))
            )
            return
        if isinstance(current, np.dtype):
            entries.append(CanonicalEntry(path, type_name, _numpy_dtype_payload(current)))
            return
        if isinstance(current, np.generic):
            dtype = np.dtype(current.dtype)
            payload = _frame(_numpy_dtype_payload(dtype)) + current.tobytes()
            entries.append(CanonicalEntry(path, type_name, payload))
            return
        if isinstance(current, np.ndarray):
            dtype = np.dtype(current.dtype)
            contiguous = np.ascontiguousarray(current)
            metadata = (
                _frame(_numpy_dtype_payload(dtype))
                + _frame(repr(tuple(int(v) for v in contiguous.shape)).encode("ascii"))
            )
            entries.append(
                CanonicalEntry(path, type_name, metadata + contiguous.tobytes(order="C"))
            )
            return
        if isinstance(current, torch.dtype):
            entries.append(CanonicalEntry(path, type_name, str(current).encode("ascii")))
            return
        if isinstance(current, torch.device):
            entries.append(CanonicalEntry(path, type_name, str(current).encode("ascii")))
            return
        if isinstance(current, torch.Tensor):
            metadata = (
                _frame(str(current.dtype).encode("ascii"))
                + _frame(repr(tuple(int(v) for v in current.shape)).encode("ascii"))
                + _frame(repr(tuple(int(v) for v in current.stride())).encode("ascii"))
                + _frame(str(current.device).encode("ascii"))
                + (b"1" if bool(current.requires_grad) else b"0")
            )
            entries.append(CanonicalEntry(path, type_name, metadata + _tensor_bytes(current)))
            return

        track_identity = isinstance(
            current, (list, tuple, dict, set, frozenset, deque)
        ) or hasattr(current, "__dict__") or is_dataclass(current)
        if track_identity:
            object_id = id(current)
            if object_id in references:
                entries.append(
                    CanonicalEntry(path, "cycle-reference", references[object_id].encode("utf-8"))
                )
                return
            references[object_id] = path

        if isinstance(current, (list, tuple)):
            retained = [
                item for item in current if exclude is None or not exclude(item)
            ]
            entries.append(CanonicalEntry(path, type_name, str(len(retained)).encode("ascii")))
            for index, item in enumerate(retained):
                visit(item, f"{path}[{index}]<{_qualified_type(item)}>")
            return
        if isinstance(current, deque):
            retained = [
                item for item in current if exclude is None or not exclude(item)
            ]
            metadata = f"len={len(retained)};maxlen={current.maxlen}".encode("ascii")
            entries.append(CanonicalEntry(path, type_name, metadata))
            for index, item in enumerate(retained):
                visit(item, f"{path}[{index}]<{_qualified_type(item)}>")
            return
        if isinstance(current, (set, frozenset)):
            retained = [
                item for item in current if exclude is None or not exclude(item)
            ]
            ordered = sorted(retained, key=_canonical_order_blob)
            entries.append(CanonicalEntry(path, type_name, str(len(ordered)).encode("ascii")))
            for index, item in enumerate(ordered):
                visit(item, f"{path}{{{index}}}<{_qualified_type(item)}>")
            return
        if isinstance(current, Mapping):
            retained_items = [
                (key, item)
                for key, item in current.items()
                if exclude is None or (not exclude(key) and not exclude(item))
            ]
            ordered_items = sorted(
                retained_items, key=lambda pair: _canonical_order_blob(pair[0])
            )
            entries.append(
                CanonicalEntry(path, type_name, str(len(ordered_items)).encode("ascii"))
            )
            for index, (key, item) in enumerate(ordered_items):
                key_path = f"{path}.key[{index}]<{_qualified_type(key)}>"
                visit(key, key_path)
                visit(item, f"{path}.value[{index}]<{_qualified_type(item)}>")
            return

        if is_dataclass(current):
            dataclass_fields = sorted(
                (
                    field
                    for field in fields(current)
                    if exclude is None or not exclude(getattr(current, field.name))
                ),
                key=lambda item: item.name,
            )
            entries.append(
                CanonicalEntry(path, type_name, str(len(dataclass_fields)).encode("ascii"))
            )
            for field in dataclass_fields:
                item = getattr(current, field.name)
                visit(item, f"{path}.{field.name}<{_qualified_type(item)}>")
            return
        if hasattr(current, "__dict__"):
            attributes = vars(current)
            if not isinstance(attributes, dict):
                raise R27G2ContractError(
                    f"non-dict __dict__ for canonical evidence at {path}: {type_name}"
                )
            names = sorted(
                name
                for name, item in attributes.items()
                if exclude is None or not exclude(item)
            )
            entries.append(CanonicalEntry(path, type_name, str(len(names)).encode("ascii")))
            for name in names:
                item = attributes[name]
                visit(item, f"{path}.{name}<{_qualified_type(item)}>")
            return

        raise R27G2ContractError(
            f"unsupported canonical evidence type at {path}: {type_name}"
        )

    visit(value, root)
    return tuple(entries)


def capture_structured_evidence(value: Any) -> tuple[CanonicalEntry, ...]:
    """Capture typed evidence for direct structural equality checks."""

    return _canonical_entries(value)


def typed_evidence_equal(left: Any, right: Any) -> bool:
    """Compare arbitrary supported evidence by its typed structure and values."""

    return capture_structured_evidence(left) == capture_structured_evidence(right)


def _validate_runtime_snapshot(snapshot: Mapping[str, Any]) -> None:
    if tuple(snapshot.keys()) != RUNTIME_ATTRIBUTE_NAMES:
        missing = [name for name in RUNTIME_ATTRIBUTE_NAMES if name not in snapshot]
        extra = [name for name in snapshot if name not in RUNTIME_ATTRIBUTE_NAMES]
        raise R27G2ContractError(
            "runtime snapshot inventory mismatch: "
            f"missing={missing}, extra={extra}, order={tuple(snapshot.keys())}"
        )


def capture_runtime_snapshot(runtime: Any) -> dict[str, Any]:
    """Deep-copy exactly the registered behavior-affecting runtime inventory."""

    missing = [name for name in RUNTIME_ATTRIBUTE_NAMES if not hasattr(runtime, name)]
    if missing:
        raise R27G2ContractError(f"runtime missing registered attributes: {missing}")
    source = {name: getattr(runtime, name) for name in RUNTIME_ATTRIBUTE_NAMES}
    try:
        snapshot = copy.deepcopy(source)
    except Exception as exc:
        raise R27G2ContractError(f"runtime deep snapshot failed: {exc}") from exc
    _validate_runtime_snapshot(snapshot)
    return snapshot


def restore_runtime_snapshot(runtime: Any, snapshot: Mapping[str, Any]) -> None:
    """Restore a fresh deep copy; the canonical source is never installed directly."""

    _validate_runtime_snapshot(snapshot)
    missing = [name for name in RUNTIME_ATTRIBUTE_NAMES if not hasattr(runtime, name)]
    if missing:
        raise R27G2ContractError(f"restore target missing registered attributes: {missing}")
    try:
        working = copy.deepcopy(dict(snapshot))
    except Exception as exc:
        raise R27G2ContractError(f"runtime deep restore failed: {exc}") from exc
    for name in RUNTIME_ATTRIBUTE_NAMES:
        setattr(runtime, name, working[name])


def runtime_snapshot_differences(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> tuple[str, ...]:
    _validate_runtime_snapshot(left)
    _validate_runtime_snapshot(right)
    differences: list[str] = []
    for name in RUNTIME_ATTRIBUTE_NAMES:
        if capture_structured_evidence(left[name]) != capture_structured_evidence(
            right[name]
        ):
            differences.append(name)
    return tuple(differences)


def runtime_snapshots_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return not runtime_snapshot_differences(left, right)


def assert_runtime_snapshots_equal(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> None:
    differences = runtime_snapshot_differences(left, right)
    if differences:
        raise R27G2ContractError(f"runtime snapshot mismatch: {list(differences)}")


def assert_runtime_matches_snapshot(runtime: Any, snapshot: Mapping[str, Any]) -> None:
    assert_runtime_snapshots_equal(capture_runtime_snapshot(runtime), snapshot)


def capture_environment_state(
    adapter: Any, underlying_environment: Any = _MISSING
) -> EnvironmentStateSnapshot:
    """Capture the adapter and explicit underlying environment object graph."""

    if _is_environment_excluded(adapter):
        raise R27G2ContractError("adapter root has an excluded environment type")
    if underlying_environment is _MISSING:
        if not hasattr(adapter, "env"):
            raise R27G2ContractError(
                "environment state capture requires adapter.env or an explicit "
                "underlying environment"
            )
        underlying_environment = getattr(adapter, "env")
    seen: dict[int, str] = {}
    entries = list(
        _canonical_entries(
            adapter,
            root=f"adapter<{_qualified_type(adapter)}>",
            exclude=_is_environment_excluded,
            seen=seen,
        )
    )
    if _is_environment_excluded(underlying_environment):
        raise R27G2ContractError("underlying environment root has an excluded type")
    entries.extend(
        _canonical_entries(
            underlying_environment,
            root=f"underlying_environment<{_qualified_type(underlying_environment)}>",
            exclude=_is_environment_excluded,
            seen=seen,
        )
    )
    return EnvironmentStateSnapshot(entries=tuple(entries))


def environment_states_equal(
    left: EnvironmentStateSnapshot, right: EnvironmentStateSnapshot
) -> bool:
    return left == right


def assert_environment_states_equal(
    left: EnvironmentStateSnapshot, right: EnvironmentStateSnapshot
) -> None:
    if not environment_states_equal(left, right):
        raise R27G2ContractError("environment state mismatch")


def capture_legacy_random_state(rng: np.random.RandomState) -> LegacyRandomStateSnapshot:
    if not isinstance(rng, np.random.RandomState):
        raise R27G2ContractError(
            "scenario RNG must be numpy.random.RandomState for the registered source"
        )
    algorithm, keys, position, has_gauss, cached = rng.get_state()
    key_array = np.ascontiguousarray(np.asarray(keys))
    if key_array.dtype.hasobject:
        raise R27G2ContractError("legacy RandomState keys have object dtype")
    return LegacyRandomStateSnapshot(
        algorithm=str(algorithm),
        keys_dtype=key_array.dtype.str,
        keys_shape=tuple(int(v) for v in key_array.shape),
        keys_bytes=key_array.tobytes(order="C"),
        position=int(position),
        has_gauss=int(has_gauss),
        cached_gaussian_bytes=_float_bytes(float(cached)),
    )


def capture_generator_state(rng: np.random.Generator) -> GeneratorStateSnapshot:
    if not isinstance(rng, np.random.Generator):
        raise R27G2ContractError(
            "adapter RNG must be numpy.random.Generator for the registered source"
        )
    state = copy.deepcopy(rng.bit_generator.state)
    entries = _canonical_entries(state, root="bit_generator_state")
    return GeneratorStateSnapshot(
        bit_generator_type=_qualified_type(rng.bit_generator),
        state_entries=entries,
    )


def capture_environment_rng_state(
    scenario_rng_or_adapter: np.random.RandomState | Any,
    adapter_rng: np.random.Generator | object = _MISSING,
) -> EnvironmentRNGState:
    if adapter_rng is _MISSING:
        adapter = scenario_rng_or_adapter
        if not hasattr(adapter, "env") or not hasattr(adapter, "np_random"):
            raise R27G2ContractError(
                "registered environment RNG capture requires adapter.env and "
                "adapter.np_random"
            )
        scenario = getattr(adapter, "env")
        if not hasattr(scenario, "np_random"):
            raise R27G2ContractError(
                "registered scenario RNG capture requires adapter.env.np_random"
            )
        scenario_rng = getattr(scenario, "np_random")
        adapter_rng = getattr(adapter, "np_random")
    else:
        scenario_rng = scenario_rng_or_adapter
    scenario = capture_legacy_random_state(scenario_rng)
    adapter = capture_generator_state(adapter_rng)  # type: ignore[arg-type]
    return EnvironmentRNGState(scenario, adapter)


def environment_rng_states_equal(
    left: EnvironmentRNGState, right: EnvironmentRNGState
) -> bool:
    return left == right


def rng_states_equal(left: Any, right: Any) -> bool:
    """Exact typed equality for registered environment or global RNG snapshots."""

    if type(left) is not type(right):
        return False
    if isinstance(left, (EnvironmentRNGState, GlobalRNGState)):
        return bool(left == right)
    raise R27G2ContractError(
        "rng_states_equal requires matching EnvironmentRNGState or GlobalRNGState"
    )


def assert_environment_rng_states_equal(
    left: EnvironmentRNGState, right: EnvironmentRNGState
) -> None:
    if not environment_rng_states_equal(left, right):
        raise R27G2ContractError("environment RNG state mismatch")


def _torch_rng_bytes(state: torch.Tensor) -> bytes:
    if state.dtype != torch.uint8 or state.ndim != 1:
        raise R27G2ContractError(
            f"unexpected Torch RNG state tensor: shape={tuple(state.shape)}, dtype={state.dtype}"
        )
    return state.detach().cpu().contiguous().numpy().tobytes(order="C")


def capture_global_rng_state(
    *, require_cuda: bool = True, include_cuda: bool = True
) -> GlobalRNGState:
    """Capture Python, NumPy, CPU-Torch, and (by default) all CUDA RNG states."""

    if require_cuda and not include_cuda:
        raise R27G2ContractError("R27-G2 cannot omit CUDA RNG state when CUDA is required")
    cuda_available = bool(torch.cuda.is_available()) if include_cuda else False
    if require_cuda and not cuda_available:
        raise R27G2ContractError("CUDA unavailable; CPU fallback is forbidden for R27-G2")
    cuda_states: tuple[bytes, ...] = ()
    if include_cuda and cuda_available:
        cuda_states = tuple(_torch_rng_bytes(state) for state in torch.cuda.get_rng_state_all())

    python_entries = _canonical_entries(random.getstate(), root="python_random_state")
    numpy_state = capture_legacy_random_state(np.random.mtrand._rand)
    cpu_state = _torch_rng_bytes(torch.get_rng_state())
    return GlobalRNGState(
        python_state_entries=python_entries,
        numpy_state=numpy_state,
        torch_cpu_state=cpu_state,
        torch_cuda_states=cuda_states,
        cuda_captured=bool(include_cuda and cuda_available),
    )


def global_rng_states_equal(left: GlobalRNGState, right: GlobalRNGState) -> bool:
    return left == right


def assert_global_rng_states_equal(left: GlobalRNGState, right: GlobalRNGState) -> None:
    if not global_rng_states_equal(left, right):
        raise R27G2ContractError("global RNG state mismatch")


def capture_module_state(module_or_agent: Any) -> tuple[ModuleStateEntry, ...]:
    """Clone complete module state for one module or an agent-like owner.

    Agent-like sources are intentionally restricted to unique *direct*
    ``nn.Module`` attributes.  Attribute names qualify every state key so that
    equal tensors in distinct source modules cannot alias in the evidence.
    """

    if isinstance(module_or_agent, torch.nn.Module):
        modules = (("module", module_or_agent),)
    else:
        try:
            attributes = vars(module_or_agent)
        except TypeError as exc:
            raise R27G2ContractError(
                "capture_module_state requires nn.Module or an agent-like object"
            ) from exc
        unique_ids: set[int] = set()
        discovered: list[tuple[str, torch.nn.Module]] = []
        for name in sorted(attributes):
            value = attributes[name]
            if not isinstance(value, torch.nn.Module) or id(value) in unique_ids:
                continue
            unique_ids.add(id(value))
            discovered.append((str(name), value))
        if not discovered:
            raise R27G2ContractError(
                "agent-like source has no direct torch.nn.Module attributes"
            )
        modules = tuple(discovered)

    entries: list[ModuleStateEntry] = []
    for attribute_name, module in modules:
        state = module.state_dict()
        module_type = _qualified_type(module)
        for state_name in sorted(state):
            value = state[state_name]
            if not isinstance(state_name, str) or not isinstance(value, torch.Tensor):
                raise R27G2ContractError(
                    f"unsupported state_dict entry {state_name!r}: {_qualified_type(value)}"
                )
            if value.layout != torch.strided or bool(value.is_quantized):
                raise R27G2ContractError(
                    "unsupported state_dict tensor layout for "
                    f"{attribute_name}.{state_name}: {value.layout}"
                )
            tensor = value.detach().cpu().contiguous()
            entries.append(
                ModuleStateEntry(
                    attribute_name=str(attribute_name),
                    module_type=module_type,
                    state_name=state_name,
                    value=tensor.clone(),
                )
            )
    return tuple(entries)


def module_state_differences(
    left: tuple[ModuleStateEntry, ...], right: tuple[ModuleStateEntry, ...]
) -> tuple[str, ...]:
    """Return directly compared module-state paths that differ."""

    differences: list[str] = []
    if len(left) != len(right):
        return ("<inventory>",)
    for left_entry, right_entry in zip(left, right):
        left_path = f"{left_entry.attribute_name}.{left_entry.state_name}"
        right_path = f"{right_entry.attribute_name}.{right_entry.state_name}"
        if (
            left_path != right_path
            or left_entry.module_type != right_entry.module_type
            or left_entry.value.dtype != right_entry.value.dtype
            or tuple(left_entry.value.shape) != tuple(right_entry.value.shape)
            or not torch.equal(left_entry.value, right_entry.value)
        ):
            differences.append(
                left_path if left_path == right_path else f"{left_path}|{right_path}"
            )
    return tuple(differences)


def module_states_equal(
    left: tuple[ModuleStateEntry, ...], right: tuple[ModuleStateEntry, ...]
) -> bool:
    return not module_state_differences(left, right)


def assert_module_states_equal(
    left: tuple[ModuleStateEntry, ...], right: tuple[ModuleStateEntry, ...]
) -> None:
    differences = module_state_differences(left, right)
    if differences:
        raise R27G2ContractError(f"module state mismatch: {list(differences)}")


def capture_value_norm_payload(
    payload: Mapping[str, Any]
) -> tuple[CanonicalEntry, ...]:
    """Capture checkpoint ValueNorm payload for direct comparison after load."""

    expected = ("high_value_norm", "low_value_norm")
    missing = [name for name in expected if name not in payload]
    if missing:
        raise R27G2ContractError(
            f"checkpoint is missing registered ValueNorm state: {missing}"
        )
    return capture_structured_evidence({name: payload[name] for name in expected})


def capture_value_norm_state(agent: Any) -> tuple[CanonicalEntry, ...]:
    """Capture loaded non-module ValueNorm state for direct comparison."""

    payload: dict[str, Any] = {}
    for name in ("high_value_norm", "low_value_norm"):
        if not hasattr(agent, name):
            raise R27G2ContractError(f"agent is missing registered inference state: {name}")
        value = getattr(agent, name)
        if value is None:
            payload[name] = None
            continue
        state_dict = getattr(value, "state_dict", None)
        if not callable(state_dict):
            raise R27G2ContractError(
                f"registered inference state has no state_dict: {name}"
            )
        state = state_dict()
        if not isinstance(state, Mapping):
            raise R27G2ContractError(
                f"registered inference state_dict is not a mapping: {name}"
            )
        payload[name] = dict(state)
    return capture_structured_evidence(payload)


def value_norm_states_equal(
    left: tuple[CanonicalEntry, ...], right: tuple[CanonicalEntry, ...]
) -> bool:
    return left == right


def assert_value_norm_states_equal(
    left: tuple[CanonicalEntry, ...], right: tuple[CanonicalEntry, ...]
) -> None:
    if not value_norm_states_equal(left, right):
        raise R27G2ContractError("ValueNorm state mismatch")


def configure_deterministic_cuda(
    device: str | torch.device = "cuda",
) -> DeterministicCUDAContract:
    """Enable the registered deterministic CUDA contract or fail closed.

    This configures deterministic kernels, cuDNN, and TF32.  Callers remain
    responsible for identical inference batching and ordering for identity
    pairs; no helper can infer that property from global backend state.
    """

    requested = torch.device(device)
    if requested.type != "cuda":
        raise R27G2ContractError("R27-G2 requires CUDA; CPU fallback is forbidden")

    initialized = bool(torch.cuda.is_initialized())
    current_workspace = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
    if initialized and current_workspace != REQUIRED_CUBLAS_WORKSPACE_CONFIG:
        raise R27G2ContractError(
            "CUBLAS_WORKSPACE_CONFIG was not registered before CUDA initialization"
        )
    if current_workspace is None:
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = REQUIRED_CUBLAS_WORKSPACE_CONFIG
    elif current_workspace != REQUIRED_CUBLAS_WORKSPACE_CONFIG:
        raise R27G2ContractError(
            "unexpected CUBLAS_WORKSPACE_CONFIG: " f"{current_workspace!r}"
        )

    if not torch.cuda.is_available():
        raise R27G2ContractError("CUDA unavailable; CPU fallback is forbidden for R27-G2")
    if requested.index is not None and requested.index >= torch.cuda.device_count():
        raise R27G2ContractError(f"CUDA device index is unavailable: {requested}")

    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False

    contract = DeterministicCUDAContract(
        device=str(requested),
        cuda_was_initialized=initialized,
        cublas_workspace_config=str(os.environ["CUBLAS_WORKSPACE_CONFIG"]),
        deterministic_algorithms=bool(torch.are_deterministic_algorithms_enabled()),
        cudnn_deterministic=bool(torch.backends.cudnn.deterministic),
        cudnn_benchmark=bool(torch.backends.cudnn.benchmark),
        cuda_matmul_allow_tf32=bool(torch.backends.cuda.matmul.allow_tf32),
        cudnn_allow_tf32=bool(torch.backends.cudnn.allow_tf32),
    )
    if (
        not contract.deterministic_algorithms
        or not contract.cudnn_deterministic
        or contract.cudnn_benchmark
        or contract.cuda_matmul_allow_tf32
        or contract.cudnn_allow_tf32
    ):
        raise R27G2ContractError(f"deterministic CUDA backend verification failed: {contract}")
    return contract


__all__ = [
    "CanonicalEntry",
    "DeterministicCUDAContract",
    "EnvironmentStateSnapshot",
    "EnvironmentRNGState",
    "GeneratorStateSnapshot",
    "GlobalRNGState",
    "LegacyRandomStateSnapshot",
    "ModuleStateEntry",
    "R27G2ContractError",
    "REQUIRED_CUBLAS_WORKSPACE_CONFIG",
    "RUNTIME_ATTRIBUTE_NAMES",
    "assert_environment_states_equal",
    "assert_environment_rng_states_equal",
    "assert_global_rng_states_equal",
    "assert_module_states_equal",
    "assert_runtime_matches_snapshot",
    "assert_runtime_snapshots_equal",
    "assert_value_norm_states_equal",
    "capture_environment_state",
    "capture_environment_rng_state",
    "capture_generator_state",
    "capture_global_rng_state",
    "capture_legacy_random_state",
    "capture_module_state",
    "capture_runtime_snapshot",
    "capture_structured_evidence",
    "capture_value_norm_payload",
    "capture_value_norm_state",
    "configure_deterministic_cuda",
    "environment_states_equal",
    "environment_rng_states_equal",
    "global_rng_states_equal",
    "module_state_differences",
    "module_states_equal",
    "restore_runtime_snapshot",
    "rng_states_equal",
    "runtime_snapshot_differences",
    "runtime_snapshots_equal",
    "typed_evidence_equal",
    "value_norm_states_equal",
]
