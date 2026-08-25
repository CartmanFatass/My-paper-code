from __future__ import annotations

from dataclasses import dataclass

HORIZON = 128
K_MIN = 4
K_MAX = 32
ORDINARY_CAP = 31
TOTAL_CAP = 32
PENDING_WINDOW = 2
BASE_SEEDS = (17, 31, 47, 61, 79, 97)
SELECTION_SEEDS = (1009, 1013)
FIXED_KS = (4, 8, 16, 32)
TRAIN_DURATIONS = (12, 20, 28)
VALIDATION_DURATIONS = (10, 16, 24, 40)
CONCLUSION_CELLS = {
    "ID": ((12, 20, 28), 0.05),
    "SHORT": ((6, 8, 10), 0.10),
    "LONG": ((36, 44, 52), 0.10),
    "MIXED_NOISY": ((6, 16, 32, 52), 0.20),
}


@dataclass(frozen=True)
class RunConfig:
    horizon: int = HORIZON
    base_seeds: tuple[int, ...] = BASE_SEEDS
    training_episodes: int = 512
    primary_episodes_per_cell: int = 64
    safety_episodes_per_cell: int = 4
    selection_episodes_per_cell: int = 32
    ppo_epochs: int = 4
    minibatch_ticks: int = 1024
    wall_seconds: int = 1800
    peak_rss_bytes: int = 2 * 1024**3
    cpu_workers: int = 1
    evaluation_tick_cap: int = 5_000_000
    total_tick_cap: int = 6_000_000

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()

LEARNED_ARMS = ("LOCAL", "COORD")
FIXED_ARMS = tuple(f"FIXED-{k}" for k in FIXED_KS)
CONTROL_ARMS = ("COORD-SHUFFLE", "COORD-YOKED")
ORACLE_ARM = "STAGE-ORACLE"
UNIQUE_EVALUATION_ARMS = (*FIXED_ARMS, *LEARNED_ARMS, *CONTROL_ARMS, ORACLE_ARM)

PPO = {
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip": 0.20,
    "learning_rate": 3e-4,
    "value_coefficient": 0.5,
    "entropy_coefficient": 0.01,
    "gradient_norm_cap": 1.0,
    "epochs": 4,
    "minibatch_ticks": 1024,
}

DECLARED_BUDGETS = {
    "training_team_ticks": 786_432,
    "evaluation_team_tick_cap": 5_000_000,
    "total_team_tick_cap": 6_000_000,
    "cpu_workers": 1,
    "wall_seconds": 1800,
    "peak_rss_bytes": 2 * 1024**3,
}
