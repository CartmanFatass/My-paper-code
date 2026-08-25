"""Frozen scientific configuration for VNFC-B2."""

from __future__ import annotations

from dataclasses import dataclass


TYPED = "TYPED-SELECTIVE-CARRIER"
RESET = "RESET-ALL-MASKED-RECURRENT"
RAW = "RAW-HISTORY-MASKED-RECURRENT"
LEARNED_ARMS = (TYPED, RESET, RAW)
ORACLE = "FRESH-FACT-ORACLE"

C0 = "C0_NO_CHURN"
C1 = "C1_SAME_ENTITY_SAME_ROLE"
C2 = "C2_SAME_ENTITY_NEW_ROLE"
C3 = "C3_REPLACEMENT_SAME_SLOT"
EVENT_CELLS = (C0, C1, C2, C3)

SEEN_SCHEDULES = {"S1": (4, 5), "S2": (6, 8)}
HELD_OUT_SCHEDULES = {"S*": (5, 8)}
BASE_SEEDS = (1301, 1321, 1361, 1381, 1423, 1451, 1481, 1511)


@dataclass(frozen=True)
class Config:
    updates: int = 32
    episodes_per_update: int = 128
    episode_ticks: int = 12
    ppo_epochs: int = 4
    minibatch_agent_rows: int = 256
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ppo_clip: float = 0.20
    value_coefficient: float = 0.5
    entropy_coefficient: float = 0.01
    gradient_clip: float = 0.5
    training_sizes: tuple[int, ...] = (3, 4)
    held_out_size: int = 5
    train_worlds_per_cell: int = 32
    joint_holdout_worlds_per_cell: int = 64
    row_order_replicas: int = 4
    wall_cap_seconds: int = 3 * 60 * 60
    peak_rss_bytes: int = 4 * 1024**3
    ordinary_rtol: float = 1e-5
    ordinary_atol: float = 1e-6


PRODUCTION_CONFIG = Config()

