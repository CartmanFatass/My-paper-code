"""Direct, non-authorizing lifecycle facts for the realized FCEOV path."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import FoundationGate


class Stage(str, Enum):
    PREFLIGHT = "PREFLIGHT"
    FOUNDATION = "FOUNDATION"
    ASSAY = "ASSAY"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True, slots=True)
class Lifecycle:
    stage: Stage
    foundation_gate: FoundationGate | None = None
    panel_complete: bool = False

    def advance_foundation(self, gate: FoundationGate) -> "Lifecycle":
        if (
            self.stage is not Stage.FOUNDATION
            or not isinstance(gate, FoundationGate)
            or gate.complete is not True
            or not isinstance(gate.passed, bool)
        ):
            raise ValueError("only a complete foundation gate can advance FOUNDATION")
        return Lifecycle(Stage.ASSAY if gate.passed else Stage.TERMINAL, gate, False)

    def advance_panel(self, *, complete: bool) -> "Lifecycle":
        if (
            self.stage is not Stage.ASSAY
            or self.foundation_gate is None
            or self.foundation_gate.passed is not True
            or complete is not True
        ):
            raise ValueError("only the complete assay can advance a passing foundation")
        return Lifecycle(Stage.TERMINAL, self.foundation_gate, True)


def preflight_complete() -> Lifecycle:
    return Lifecycle(Stage.FOUNDATION)


__all__ = ["Lifecycle", "Stage", "preflight_complete"]
