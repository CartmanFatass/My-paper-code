"""Small, failure-only traceback evidence for an incomplete B01 fit."""

from __future__ import annotations

import math
import sys
from collections import deque
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import torch


MAX_FRAMES = 32
MAX_PATH = 512


def _type_name(value: object) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"[:128]


def _scalar(value: object) -> dict[str, Any]:
    """Never stringify an arbitrary object or traverse an array/tensor."""
    result: dict[str, Any] = {"type": _type_name(value)}
    if type(value) in (bool, int, float):
        scalar = value
    elif isinstance(value, np.generic) and type(value).__module__.startswith("numpy") \
            and value.dtype.kind in "biuf":
        scalar = value.item()
    elif type(value) is np.ndarray and value.ndim == 0 and value.dtype.kind in "biuf":
        scalar = value.item()
    else:
        return result
    if type(scalar) is bool:
        result["value"] = scalar
    elif type(scalar) is int:
        if scalar.bit_length() <= 128:
            result["value"] = scalar
        else:
            result["value_omitted"] = "integer exceeds 128 bits"
    elif type(scalar) is float:
        result["value"] = scalar if math.isfinite(scalar) else (
            "nan" if math.isnan(scalar) else "+inf" if scalar > 0 else "-inf")
    return result


def _count_fields(value: object) -> dict[str, int]:
    if type(value) is not dict:
        return {}
    return {key: value[key] for key in ("transitions", "rollouts", "native_episodes", "checkpoints")
            if type(value.get(key)) is int and 0 <= value[key] <= 10**15}


def _native_modules() -> dict[str, str]:
    names = ("numpy.core._multiarray_umath", "numpy._core._multiarray_umath", "torch._C")
    paths = {}
    def record(module: object) -> None:
        if type(module) is not ModuleType:
            return
        name = module.__dict__.get("__name__")
        origin = module.__dict__.get("__file__")
        if type(name) is str and type(origin) is str and origin.endswith((".so", ".pyd")):
            paths[name[:128]] = origin[:MAX_PATH]

    # Torch's extension loader can return a module without registering it in sys.modules.
    # Read only caches belonging to modules already present in this process.
    for module_name, cache_name in (
        ("envs.native.cpp_extension_cache", "_LOADED_MODULES"),
        ("envs.pettingzoo.uav_cpp_backend", "_LOADED_BACKENDS"),
    ):
        holder = sys.modules.get(module_name)
        cache = holder.__dict__.get(cache_name) if type(holder) is ModuleType else None
        if type(cache) is dict:
            for module in list(cache.values())[:16]:
                record(module)
                if len(paths) >= 16:
                    return paths
    for name, module in list(sys.modules.items()):
        if name in names or name.startswith("envs."):
            record(module)
            if len(paths) >= 16:
                break
    return paths


def failure_context(error: Exception, completed_counts: dict[str, Any]) -> dict[str, Any]:
    frames = deque(maxlen=MAX_FRAMES)
    frame_count = 0
    traceback = error.__traceback__
    while traceback is not None:
        frames.append((traceback, traceback.tb_frame))
        frame_count += 1
        traceback = traceback.tb_next
    locations = []
    collector = None
    scalar_frames = []
    for trace, frame in frames:
        name = frame.f_code.co_name
        locations.append({"file": frame.f_code.co_filename[:MAX_PATH],
                          "line": trace.tb_lineno, "function": name[:128]})
        if name == "collect_and_train":
            local = frame.f_locals
            position = {key: local[key] for key in ("rollout", "step", "lane")
                        if type(local.get(key)) is int and 0 <= local[key] <= 10**9}
            result = local.get("result")
            if type(result) is dict:
                position["partial_observed_counts"] = _count_fields(result.get("counts"))
            collector = position
        fields = {"_get_observation_cached_body": ("sinr_db",),
                  "clip": ("a", "a_min", "a_max"),
                  "_wrapfunc": ("obj",), "_wrapit": ("obj",)}.get(name)
        if fields:
            local = frame.f_locals
            captured = {key: _scalar(local[key]) for key in fields if key in local}
            if captured:
                scalar_frames.append({"function": name, "values": captured})
    return {
        "schema_version": 1,
        "exception_type": _type_name(error),
        "traceback": {"locations": locations, "omitted_earlier_frames": max(0, frame_count - MAX_FRAMES)},
        "completed_stored_counts": _count_fields(completed_counts),
        "collector": collector,
        "scalar_frames": scalar_frames,
        "runtime": {"python": sys.version[:256], "executable": sys.executable[:MAX_PATH],
                    "numpy_version": np.__version__, "numpy_file": str(Path(np.__file__))[:MAX_PATH],
                    "torch_version": torch.__version__, "torch_file": str(Path(torch.__file__))[:MAX_PATH],
                    "loaded_native_modules": _native_modules()},
    }
