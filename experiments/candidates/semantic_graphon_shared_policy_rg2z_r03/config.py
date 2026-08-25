"""Frozen constants for the SGSP RIDGEGATE-2Z revision-03 panel."""

from __future__ import annotations

from enum import IntEnum
from typing import Final

import torch

torch.set_num_threads(1)


PACKAGE_ID: Final = "semantic_graphon_shared_policy_rg2z_r03"
DIRECTION: Final = "semantic_graphon_shared_policy"
REVISION: Final = "SGSP-RG2Z-SCIENCE-20260815-03"
TASK_NAME: Final = "RIDGEGATE-2Z"
COUNTER_ROOT: Final = (
    "semantic_graphon_shared_policy|SGSP-RG2Z-SCIENCE-20260815-03|"
    "RIDGEGATE-2Z|blake2b-counter-v1"
)

SEEDS: Final = (
    830003, 830111, 830233, 830309, 830411, 830503,
    830617, 830719, 830801, 830911, 831023, 831109,
    831217, 831301, 831407, 831503, 831617, 831707,
    831811, 831911, 832003, 832103, 832211, 832309,
)

TRAIN_ROSTERS: Final = (9, 15)
HELDOUT_ROSTERS: Final = (6, 21)
REGISTERED_ROSTERS: Final = (6, 9, 15, 21)
ROLE_MULTIPLICITIES: Final = (2, 3, 5, 7)

HORIZON: Final = 12
EVENT_TIME_SUPPORT: Final = tuple(range(8))
EVENTS_PER_BASIN: Final = 3
DETECTION_PROBABILITY: Final = 0.75
REPORT_LIFETIME: Final = 4
SURVEYOR_FIFO_CAPACITY: Final = 2
RELAY_FIFO_CAPACITY: Final = 4


class Role(IntEnum):
    WEST_SURVEYOR = 0
    EAST_SURVEYOR = 1
    RIDGE_RELAY = 2


class Basin(IntEnum):
    WEST = 0
    EAST = 1


class Action(IntEnum):
    SCAN = 0
    UPLINK = 1
    LISTEN_WEST = 2
    LISTEN_EAST = 3
    FORWARD_BASE = 4
    HOLD = 5


ROLE_NAMES: Final = ("WEST-SURVEYOR", "EAST-SURVEYOR", "RIDGE-RELAY")
BASIN_NAMES: Final = ("WEST", "EAST")
ACTION_NAMES: Final = (
    "SCAN", "UPLINK", "LISTEN_WEST", "LISTEN_EAST", "FORWARD_BASE", "HOLD"
)
LEGAL_ACTIONS: Final = {
    Role.WEST_SURVEYOR: (Action.SCAN, Action.UPLINK, Action.HOLD),
    Role.EAST_SURVEYOR: (Action.SCAN, Action.UPLINK, Action.HOLD),
    Role.RIDGE_RELAY: (
        Action.LISTEN_WEST, Action.LISTEN_EAST, Action.FORWARD_BASE, Action.HOLD
    ),
}

OBSERVATION_DIM: Final = 22
MESSAGE_HIDDEN_DIM: Final = 64
MESSAGE_DIM: Final = 32
ACTOR_INPUT_DIM: Final = 55
ACTOR_HIDDEN_DIM: Final = 64
ACTION_DIM: Final = 6
CRITIC_INPUT_DIM: Final = 66
CRITIC_HIDDEN_DIM: Final = 64

P0: Final = (
    (0.92, 0.48, 0.88),
    (0.48, 0.92, 0.82),
    (0.86, 0.78, 0.90),
)
LATENCY: Final = (
    (1.0, 2.0, 1.0),
    (2.0, 1.0, 1.0),
    (1.0, 1.0, 1.0),
)
LOAD_LOGIT_SLOPE: Final = 0.22
BASE_P0: Final = 0.90
KERNEL_EPSILON: Final = 1.0e-12
ROTATED_PHYSICAL_COLUMN_SOURCE: Final = (2, 0, 1)

POLICY_SOFTMAX_WEIGHT: Final = 0.96
POLICY_UNIFORM_WEIGHT: Final = 0.04
PHY_BETA_BOUND: Final = 0.15
EDGE_BETA_BOUND: Final = 1.50

TRAINING_UPDATES: Final = 512
EPISODES_PER_UPDATE: Final = 64
EPISODES_PER_TRAIN_ROSTER: Final = 32
EVALUATION_EPISODES: Final = 256
LEARNING_RATE: Final = 3.0e-4
ADAM_BETAS: Final = (0.9, 0.999)
ADAM_EPSILON: Final = 1.0e-8
GRADIENT_NORM_CLIP: Final = 0.5
ENTROPY_COEFFICIENT: Final = 0.01
CRITIC_COEFFICIENT: Final = 0.5
TRAINING_DTYPE: Final = torch.float32
REDUCTION_DTYPE: Final = torch.float64
DEVICE: Final = torch.device("cpu")


def validate_roster(n_agents: int) -> int:
    """Return the balanced role multiplicity for a registered roster."""
    if n_agents not in REGISTERED_ROSTERS:
        raise ValueError(f"unregistered RIDGEGATE-2Z roster: {n_agents}")
    if n_agents % 3:
        raise ValueError("RIDGEGATE-2Z rosters must be exactly role-balanced")
    return n_agents // 3


def legal_action_indices(role: Role | int) -> tuple[int, ...]:
    return tuple(int(action) for action in LEGAL_ACTIONS[Role(int(role))])
