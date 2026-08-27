"""Frozen CLOSED-R01 foundation construction constants; no activity identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


S1_SLICE: Final[str] = "SCDMP-NATIVE-FUSION-R01-S1-FOUNDATION-CONSTRUCTION-V1"
FOUNDATION_KIND: Final[str] = "NATIVE-ORDER-ERASED-DELIVERY-FOUNDATION"
OBSERVATION_WIDTH: Final[int] = 14
ACTION_COUNT: Final[int] = 27
HIDDEN_WIDTH: Final[int] = 80
ACTOR_WIDTHS: Final[tuple[int, ...]] = (14, 80, 80, 27)
CRITIC_WIDTHS: Final[tuple[int, ...]] = (14, 80, 80, 1)
ACTOR_PARAMETER_COUNT: Final[int] = 9_867
CRITIC_PARAMETER_COUNT: Final[int] = 7_761
FOUNDATION_PARAMETER_COUNT: Final[int] = 17_628
FLOAT_DTYPE: Final[str] = "float32"
REPLICATE_COUNT: Final[int] = 24
UPDATE_COUNT: Final[int] = 192
EPISODES_PER_UPDATE: Final[int] = 16
EPOCHS_PER_UPDATE: Final[int] = 4
MINIBATCHES_PER_EPOCH: Final[int] = 4
STEPS_PER_UPDATE: Final[int] = 16
STEPS_PER_FOUNDATION: Final[int] = 3_072


@dataclass(frozen=True)
class FoundationBlueprint:
    kind: str = FOUNDATION_KIND
    actor_widths: tuple[int, ...] = ACTOR_WIDTHS
    critic_widths: tuple[int, ...] = CRITIC_WIDTHS
    activation: str = "SiLU"
    dtype: str = FLOAT_DTYPE
    actor_parameters: int = ACTOR_PARAMETER_COUNT
    critic_parameters: int = CRITIC_PARAMETER_COUNT
    total_parameters: int = FOUNDATION_PARAMETER_COUNT
    ordered_input_fields: tuple[str, ...] = ()
    xavier_gain: float = 1.0
    biases: str = "ZERO"


def structural_step_count(update_count: int = UPDATE_COUNT) -> int:
    if isinstance(update_count, bool) or not 0 <= update_count <= UPDATE_COUNT:
        raise ValueError("update_count must be an integer in [0,192]")
    return update_count * STEPS_PER_UPDATE
