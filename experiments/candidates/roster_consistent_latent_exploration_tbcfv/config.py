"""Frozen construction constants for RCLE-TBCFV revision 04.

This module contains no coordinates, seeds, learned state, or runtime authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

DIRECTION_ID = "roster_consistent_latent_exploration"
SCIENCE_REVISION = "RCLE-TBCFV-SCIENCE-20260821-04"

C1P1 = "C1P1-COMMON-PERSISTENT"
FLEX = "FLEX-REKEY"
C1P0 = "C1P0-COMMON-REFRESH"
C0P1 = "C0P1-PRIVATE-PERSISTENT"
C0P0 = "C0P0-PRIVATE-REFRESH"
LEARNED_PACKAGES = (C1P1, FLEX, C1P0, C0P1, C0P0)

COHERENT_SCAFFOLD = "COHERENT-SCAFFOLD"
FRAGMENTED_SCAFFOLD = "FRAGMENTED-SCAFFOLD"
INDEPENDENT_NEAREST = "INDEPENDENT-NEAREST"
SCRIPTED_PACKAGES = (COHERENT_SCAFFOLD, FRAGMENTED_SCAFFOLD, INDEPENDENT_NEAREST)

ACTIVE_CONTINUATION = "ACTIVE_CONTINUATION"
NEW_EPOCH = "NEW_EPOCH"

TRAIN_EPISODES_PER_BLOCK = 64
TRAIN_CELLS = 8
EPISODES_PER_CELL = 8
BASELINE_DECAY = 0.95
GRADIENT_DIRECTION_SCALE = 0.05
LEARNING_RATE = 0.01
NONZERO_UPDATE_NORM = GRADIENT_DIRECTION_SCALE * LEARNING_RATE


@dataclass(frozen=True)
class ConformanceConfig:
    dtype: str = "float64"
    max_agents: int = 12
    sectors: int = 120
    beacons: int = 6
    horizon: int = 64
    event_tick: int = 24
    claim_period: int = 4
    plan_dim: int = 4
    element_input: int = 3
    element_hidden: int = 32
    public_summary_dim: int = 68
    pooled_summary_dim: int = 64
    manager_hidden: int = 64
    pointer_input: int = 81
    pointer_hidden: int = 64
    common_update_input: int = 72
    agent_update_input: int = 81
    update_hidden: int = 32
    parameters_per_arm: int = 26_161
    train_episodes_per_block: int = TRAIN_EPISODES_PER_BLOCK
    train_cells: int = TRAIN_CELLS
    episodes_per_cell: int = EPISODES_PER_CELL
    baseline_decay: float = BASELINE_DECAY
    gradient_direction_scale: float = GRADIENT_DIRECTION_SCALE
    learning_rate: float = LEARNING_RATE
    nonzero_update_norm: float = NONZERO_UPDATE_NORM

    def manifest(self) -> dict[str, object]:
        result: dict[str, object] = asdict(self)
        result.update(
            direction_id=DIRECTION_ID,
            science_revision=SCIENCE_REVISION,
            learned_packages=list(LEARNED_PACKAGES),
            scripted_packages=list(SCRIPTED_PACKAGES),
            architecture=(
                "two 3-32-32 mean-pooled set encoders; 68-64-64 manager; "
                "two 64-4 Normal heads; 81-64-64-1 pointer; "
                "72-32-4 common and 81-32-4 agent FLEX heads"
            ),
        )
        return result


REGISTERED = ConformanceConfig()
