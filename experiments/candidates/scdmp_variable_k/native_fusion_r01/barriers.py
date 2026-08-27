"""Fail-closed S0 stage skeleton and no-partial-value firewall."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final


_FORBIDDEN_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "master",
        "master_id",
        "model",
        "model_path",
        "checkpoint",
        "checkpoint_path",
        "checkpoint_sha256",
        "competence",
        "competence_gate",
        "opportunity",
        "opportunity_assay",
        "adapter",
        "adapter_identity",
        "training",
        "training_command",
        "evaluation",
        "evaluation_output",
        "result_bearing_command",
        "scientific_output",
        "scientific_result",
        "partial_value",
    }
)


class S0FirewallError(ValueError):
    pass


def _walk_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise S0FirewallError("S0 payload keys must be strings")
            if key.casefold() in _FORBIDDEN_FIELDS:
                raise S0FirewallError(f"forbidden S0 field: {key}")
            _walk_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _walk_keys(item)


@dataclass(frozen=True)
class StageBarrier:
    stage: str
    materialized: frozenset[str]
    next_conditional_stage: str
    prerequisite_order: tuple[str, ...]
    effect_refs: tuple[object, ...]

    @classmethod
    def s0(cls) -> "StageBarrier":
        return cls(
            stage="S0_SOURCE_CONFORMANCE",
            materialized=frozenset({"source_manifest", "technical_acceptance"}),
            next_conditional_stage="FOUNDATION_CONSTRUCTION",
            prerequisite_order=("I_native", "C_native", "O_native"),
            effect_refs=(),
        )

    def validate_payload(self, value: Mapping[str, object]) -> None:
        if not isinstance(value, Mapping):
            raise S0FirewallError("S0 payload must be a mapping")
        _walk_keys(value)
