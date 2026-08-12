"""Immutable scientific constants for the VQFP-B1 construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

VQFP_REVISION: Final = "VQFP-B1-MATH-CLOSURE-20260812-04"
TRAINING_SEEDS: Final[tuple[int, ...]] = (
    2101, 2111, 2129, 2141, 2153, 2161,
    2179, 2203, 2213, 2237, 2251, 2267,
)
ARMS: Final[tuple[str, str]] = ("vqfp", "learned")
TRAIN_N: Final[tuple[int, int]] = (6, 10)
HELDOUT_N: Final[tuple[int, int]] = (4, 14)
REGIMES: Final[tuple[str, str]] = ("IID", "CLUSTER")
CONTROLS: Final[tuple[str, ...]] = (
    "WHOLE-TUPLE-PERMUTE", "EQUAL-VOLUME", "CONSTANT-FIELD", "IDENTITY-RESTORE",
)


@dataclass(frozen=True, slots=True)
class FrozenConfig:
    """All quantities that may not be changed after activity begins."""

    horizon: int = 32
    updates: int = 375
    episodes_per_update: int = 8
    gamma: float = 0.99
    gae_lambda: float = 0.95
    learning_rate: float = 3e-4
    adam_beta1: float = 0.9
    adam_beta2: float = 0.999
    adam_epsilon: float = 1e-8
    gradient_clip: float = 1.0
    ordinary_episodes: int = 128
    conflict_episodes: int = 128
    noisy_episodes: int = 128
    control_states: int = 128
    material_margin: float = 0.03
    mechanism_density_margin: float = 0.02
    mechanism_return_margin: float = 0.02
    mechanism_tv_margin: float = 0.05
    control_atol: float = 1e-8
    control_rtol: float = 1e-6
    nominal_parameters_per_arm: int = 40_996
    transition_state_ceiling: int = 4_098_048
    cpu_processes: int = 1
    ram_gib: int = 2
    wall_hours: int = 8

    @property
    def team_transitions_per_update(self) -> int:
        return self.horizon * self.episodes_per_update

    @property
    def train_transitions_per_arm_seed(self) -> int:
        return self.team_transitions_per_update * self.updates

    def static_accounting(self) -> dict[str, int]:
        """The registered ceiling, counting a one-step control per arm."""
        training = len(TRAINING_SEEDS) * 2 * self.train_transitions_per_arm_seed
        ordinary = len(TRAINING_SEEDS) * 2 * 4 * 2 * self.ordinary_episodes * self.horizon
        ordinary_cut = len(TRAINING_SEEDS) * 2 * 2 * 2 * self.ordinary_episodes * self.horizon
        conflict = len(TRAINING_SEEDS) * 2 * 2 * 2 * self.conflict_episodes * self.horizon
        noisy = len(TRAINING_SEEDS) * 2 * 2 * self.noisy_episodes * self.horizon
        controls = len(CONTROLS) * len(TRAINING_SEEDS) * 2 * 2 * self.control_states
        return {
            "training": training,
            "ordinary_intact": ordinary,
            "ordinary_cut": ordinary_cut,
            "conflict_intact_cut": conflict,
            "noisy": noisy,
            "controls": controls,
            "total": training + ordinary + ordinary_cut + conflict + noisy + controls,
        }

    def assert_registered_counts(self) -> None:
        if self.episodes_per_update != 8 or self.team_transitions_per_update != 256:
            raise ValueError("B1 requires eight 32-tick episodes / 256 team transitions per update")
        if self.static_accounting()["total"] != self.transition_state_ceiling:
            raise ValueError("registered transition/state accounting drift")
