"""Direct runtime observations for the OMRC B1 mechanical C evidence surface."""

from __future__ import annotations

from contextlib import AbstractContextManager
import hashlib
from pathlib import Path
from types import MethodType
from typing import Any, Mapping, Sequence

import torch
from torch import nn

from .contract import EPISODE_TRANSITIONS
from .model import INPUT_DIM


MECHANICAL_DIRECT_FIELDS = frozenset(
    {"active_modes", "reset_records", "checkpoint_records", "learner_visibility_records"}
)
ALLOWED_LEARNER_FIELDS = ("primitive_token", "adapter_emission")


class B1RuntimeAuditError(ValueError):
    """A direct mechanical observation differs from the frozen CPU/FP32 path."""


def _autocast_enabled(device_type: str) -> bool:
    try:
        return bool(torch.is_autocast_enabled(device_type))
    except TypeError:  # pragma: no cover - compatibility with older PyTorch
        if device_type == "cpu" and hasattr(torch, "is_autocast_cpu_enabled"):
            return bool(torch.is_autocast_cpu_enabled())
        return bool(torch.is_autocast_enabled()) if device_type == "cuda" else False


def observe_active_modes(model: nn.Module) -> list[str]:
    """Observe every execution mode that would violate frozen FP32 CPU execution."""

    if not isinstance(model, nn.Module):
        raise B1RuntimeAuditError("execution mode observation requires a torch module")
    parameters = tuple(model.parameters())
    if not parameters:
        raise B1RuntimeAuditError("execution mode observation requires active parameters")
    modes: list[str] = []
    devices = sorted({parameter.device.type for parameter in parameters})
    dtypes = sorted({str(parameter.dtype) for parameter in parameters})
    if devices != ["cpu"]:
        modes.extend(f"parameter-device:{device}" for device in devices if device != "cpu")
    if dtypes != ["torch.float32"]:
        modes.extend(f"parameter-dtype:{dtype}" for dtype in dtypes if dtype != "torch.float32")
    if torch.get_default_dtype() is not torch.float32:
        modes.append(f"default-dtype:{torch.get_default_dtype()}")
    for device_type in ("cpu", "cuda"):
        if _autocast_enabled(device_type):
            modes.append(f"autocast:{device_type}")
    precision = torch.get_float32_matmul_precision()
    if precision != "highest":
        modes.append(f"float32-matmul-precision:{precision}")
    if "cuda" in devices:
        if bool(torch.backends.cuda.matmul.allow_tf32):
            modes.append("tf32:cuda-matmul")
        if bool(torch.backends.cudnn.allow_tf32):
            modes.append("tf32:cudnn")
    return sorted(set(modes))


def require_frozen_execution_modes(model: nn.Module) -> list[str]:
    modes = observe_active_modes(model)
    if modes:
        raise B1RuntimeAuditError(
            "prohibited active execution modes: " + ",".join(modes)
        )
    return modes


def _fp32_bits(tensor: torch.Tensor) -> list[str]:
    if not isinstance(tensor, torch.Tensor) or tensor.dtype is not torch.float32:
        raise B1RuntimeAuditError("recurrent reset observation must be an FP32 tensor")
    words = tensor.detach().cpu().contiguous().view(torch.int32).reshape(-1).tolist()
    return [f"{int(word) & 0xFFFFFFFF:08x}" for word in words]


class ModelResetObserver(AbstractContextManager["ModelResetObserver"]):
    """Record the actual h0 returned at every model episode-batch boundary."""

    def __init__(
        self,
        model: nn.Module,
        *,
        name: str,
        records: list[dict[str, Any]],
    ) -> None:
        if not isinstance(model, nn.Module) or not name or not isinstance(records, list):
            raise B1RuntimeAuditError("reset observer identity differs")
        if not callable(getattr(model, "initial_hidden", None)):
            raise B1RuntimeAuditError("model has no recurrent reset boundary")
        self.model = model
        self.name = name
        self.records = records
        self._original: Any = None
        self._had_instance_override = False
        self._call_index = 0

    def __enter__(self) -> "ModelResetObserver":
        self._had_instance_override = "initial_hidden" in self.model.__dict__
        self._original = self.model.initial_hidden
        observer = self

        def observed_initial_hidden(
            model_self: nn.Module,
            batch_size: int,
            *,
            device: torch.device | str | None = None,
        ) -> torch.Tensor:
            hidden = observer._original(batch_size, device=device)
            observed = _fp32_bits(hidden)
            expected = ["00000000"] * len(observed)
            observer.records.append(
                {
                    "name": f"{observer.name}:batch-{observer._call_index}",
                    "expected_fp32_bits": expected,
                    "observed_fp32_bits": observed,
                }
            )
            observer._call_index += 1
            if not observed or observed != expected:
                raise B1RuntimeAuditError("nonzero recurrent reset/carry was observed")
            return hidden

        self.model.initial_hidden = MethodType(observed_initial_hidden, self.model)  # type: ignore[method-assign]
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._had_instance_override:
            self.model.initial_hidden = self._original  # type: ignore[method-assign]
        else:
            del self.model.__dict__["initial_hidden"]
        return None


def observe_learner_visibility(
    name: str,
    observations: torch.Tensor,
    *,
    episode_count: int,
    visible_fields: Sequence[str],
) -> dict[str, Any]:
    """Validate and record the actual public learner-input tensor boundary."""

    if not name or type(episode_count) is not int or episode_count <= 0:
        raise B1RuntimeAuditError("learner visibility observation identity differs")
    if (
        not isinstance(observations, torch.Tensor)
        or observations.shape != (episode_count, EPISODE_TRANSITIONS, INPUT_DIM)
        or observations.dtype is not torch.float32
        or observations.device.type != "cpu"
        or not torch.isfinite(observations).all().item()
    ):
        raise B1RuntimeAuditError("learner visibility tensor boundary differs")
    visible = list(visible_fields)
    allowed = list(ALLOWED_LEARNER_FIELDS)
    if visible != allowed or len(visible) != len(set(visible)):
        raise B1RuntimeAuditError("learner visibility contains an extension or omission")
    return {"name": name, "visible_fields": visible, "allowed_fields": allowed}


def checkpoint_roundtrip_record(
    name: str,
    *,
    saved_bytes: bytes,
    loaded_bytes: bytes,
    expected_parameter_sha256: str,
    restored_parameter_sha256: str,
) -> dict[str, str]:
    """Form one exact C-schema row from directly observed checkpoint bytes/state."""

    if not name or not isinstance(saved_bytes, bytes) or not isinstance(loaded_bytes, bytes):
        raise B1RuntimeAuditError("checkpoint byte observation is absent")
    saved_sha = hashlib.sha256(saved_bytes).hexdigest()
    loaded_sha = hashlib.sha256(loaded_bytes).hexdigest()
    for label, digest in (
        ("expected parameter", expected_parameter_sha256),
        ("restored parameter", restored_parameter_sha256),
    ):
        if (
            type(digest) is not str
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise B1RuntimeAuditError(f"checkpoint {label} digest differs")
    if saved_sha != loaded_sha:
        raise B1RuntimeAuditError("checkpoint saved/loaded byte digest differs")
    if expected_parameter_sha256 != restored_parameter_sha256:
        raise B1RuntimeAuditError("checkpoint restored parameter digest differs")
    return {
        "name": name,
        "saved_sha256": saved_sha,
        "loaded_sha256": loaded_sha,
        "expected_parameter_sha256": expected_parameter_sha256,
        "restored_parameter_sha256": restored_parameter_sha256,
    }


def build_mechanical_direct(
    *,
    active_modes: list[str],
    reset_records: list[Mapping[str, Any]],
    checkpoint_records: list[Mapping[str, Any]],
    learner_visibility_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate and form the exact upstream C mechanical surface."""

    if not isinstance(active_modes, list) or active_modes:
        raise B1RuntimeAuditError("prohibited active execution modes were recorded")
    reset_keys = {"name", "expected_fp32_bits", "observed_fp32_bits"}
    checkpoint_keys = {
        "name",
        "saved_sha256",
        "loaded_sha256",
        "expected_parameter_sha256",
        "restored_parameter_sha256",
    }
    visibility_keys = {"name", "visible_fields", "allowed_fields"}
    for label, records, keys in (
        ("reset", reset_records, reset_keys),
        ("checkpoint", checkpoint_records, checkpoint_keys),
        ("learner visibility", learner_visibility_records, visibility_keys),
    ):
        if not isinstance(records, list) or not records:
            raise B1RuntimeAuditError(f"mechanical {label} records are absent")
        if any(not isinstance(record, Mapping) or set(record) != keys for record in records):
            raise B1RuntimeAuditError(f"mechanical {label} record schema differs")
    for record in reset_records:
        expected = record["expected_fp32_bits"]
        observed = record["observed_fp32_bits"]
        if (
            not isinstance(expected, list)
            or not expected
            or expected != observed
            or any(word != "00000000" for word in expected)
        ):
            raise B1RuntimeAuditError("mechanical recurrent reset record differs")
    for record in checkpoint_records:
        if (
            record["saved_sha256"] != record["loaded_sha256"]
            or record["expected_parameter_sha256"]
            != record["restored_parameter_sha256"]
        ):
            raise B1RuntimeAuditError("mechanical checkpoint record differs")
    for record in learner_visibility_records:
        if (
            record["visible_fields"] != list(ALLOWED_LEARNER_FIELDS)
            or record["allowed_fields"] != list(ALLOWED_LEARNER_FIELDS)
        ):
            raise B1RuntimeAuditError("mechanical learner visibility record differs")
    direct = {
        "active_modes": list(active_modes),
        "reset_records": [dict(record) for record in reset_records],
        "checkpoint_records": [dict(record) for record in checkpoint_records],
        "learner_visibility_records": [
            dict(record) for record in learner_visibility_records
        ],
    }
    if frozenset(direct) != MECHANICAL_DIRECT_FIELDS:
        raise AssertionError("mechanical direct schema construction differs")
    return direct


__all__ = [
    "ALLOWED_LEARNER_FIELDS",
    "B1RuntimeAuditError",
    "MECHANICAL_DIRECT_FIELDS",
    "ModelResetObserver",
    "checkpoint_roundtrip_record",
    "build_mechanical_direct",
    "observe_active_modes",
    "observe_learner_visibility",
    "require_frozen_execution_modes",
]
