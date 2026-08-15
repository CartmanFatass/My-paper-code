"""Literal constants and schemas for CCIC-B1-SCIENCE-20260813-06."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import Final

REVISION: Final = "CCIC-B1-SCIENCE-20260813-06"
HORIZON: Final = 30
FLIP_HAZARD: Final = 0.04
MU: Final = 0.75
EPSILON_SUPPORT: Final = 0.02
TRAIN_N: Final = (2, 5)
TRAIN_K: Final = (1, 3)
EVAL_N: Final = (2, 5, 8)
EVAL_K: Final = (1, 3, 5)
REGIMES: Final = ("DUP", "CORR", "IND")
RHO: Final = {"DUP": 1.0, "CORR": 0.5, "IND": 0.0}
OVERLAP: Final = {"DUP": 1.0, "CORR": 0.5, "IND": 0.0}
QUALITY: Final = 1.0
ACTIONS: Final = ("SENSE", "RELAY", "COMMIT_MINUS", "COMMIT_PLUS")
TIE_PRIORITY: Final = ("SENSE", "RELAY", "COMMIT_PLUS", "COMMIT_MINUS")
ROLLOUT_ARMS: Final = (
    "CCIC",
    "ESS-SCALAR",
    "RI-STRONG-v2",
    "INFO-FLEX",
    "ORIGIN-COUNT",
    "NUMERICAL-REFERENCE",
    "J-SHUFFLE",
    "J-CLAMP",
)
SHADOW_ONLY: Final = ("RECEIVED-COUNT", "MEAN-RI")
SEED_BLOCKS: Final = 32
EPISODES_PER_CELL: Final = 256
MASTER_SEED_BASE: Final = 1009
MASTER_SEED_STEP: Final = 7919
INFERENCE_SEED: Final = 8675309
FUSION_UPDATES: Final = 1500
ACTOR_UPDATES: Final = 1500
FUSION_BATCH: Final = 64
ACTOR_BATCH: Final = 128
SNAPSHOTS_PER_CELL: Final = 768
TRAIN_CELL_COUNT: Final = 12
TRAIN_ROWS: Final = 9216
BOOTSTRAP_DRAWS: Final = 100_000
PACKET_REAL_SYMBOLS: Final = 1
PACKET_METADATA_BITS: Final = 64
MAX_THREADS: Final = 8
MAX_RSS_BYTES: Final = 4 * 1024**3
MAX_WALL_MINUTES: Final = 90
MAX_OPTIMIZER_UPDATES: Final = 240_000
MAX_PRIMITIVE_TICKS: Final = 60_000_000
ROLLOUT_TICK_BOUND: Final = 53_084_160
SNAPSHOT_DRAW_BOUND: Final = 294_912


class Phase(IntEnum):
    TRAIN_SNAPSHOT = 1
    TRAIN_OPT = 2
    EVAL = 3
    INFERENCE = 4


STREAMS: Final = {
    "TRAIN_SNAPSHOT_COMMON": 11,
    "TRAIN_SNAPSHOT_IDIO": 12,
    "TRAIN_OPT_MINIBATCH": 23,
    "TRAIN_OPT_INIT": 29,
    "EVAL_Y0": 1,
    "EVAL_FLIP": 11,
    "EVAL_COMMON": 13,
    "EVAL_IDIO": 17,
    "EVAL_ACTION": 19,
    "INFERENCE_BOOTSTRAP": 31,
}
MODULE_IDS: Final = {
    "CCIC": 0,
    "ESS-SCALAR": 1,
    "RI-STRONG-v2": 2,
    "INFO-FLEX": 3,
    "actor": 4,
}


@dataclass(frozen=True)
class ReferenceGrid:
    lower: float
    upper: float
    spacing: float
    quadrature_nodes: int


FINE_GRID: Final = ReferenceGrid(-24.0, 24.0, 0.005, 128)
COARSE_GRID: Final = ReferenceGrid(-16.0, 16.0, 0.01, 64)


@dataclass(frozen=True)
class ExperimentConfig:
    revision: str = REVISION
    seed_blocks: int = SEED_BLOCKS
    episodes_per_cell: int = EPISODES_PER_CELL
    max_workers: int = MAX_THREADS

    def validate(self) -> None:
        if self.revision != REVISION:
            raise ValueError("only exact revision 06 is executable")
        if self.seed_blocks != SEED_BLOCKS:
            raise ValueError("all 32 seed blocks are required")
        if self.episodes_per_cell != EPISODES_PER_CELL:
            raise ValueError("exactly 256 episodes per cell are required")
        if not 1 <= self.max_workers <= MAX_THREADS:
            raise ValueError("max_workers must be in [1,8]")

    def machine_record(self) -> dict:
        self.validate()
        out = asdict(self)
        out.update(
            horizon=HORIZON,
            flip_hazard=FLIP_HAZARD,
            mu=MU,
            train_n=TRAIN_N,
            train_k=TRAIN_K,
            eval_n=EVAL_N,
            eval_k=EVAL_K,
            regimes=REGIMES,
            rollout_arms=ROLLOUT_ARMS,
            master_seeds=[MASTER_SEED_BASE + MASTER_SEED_STEP * b for b in range(SEED_BLOCKS)],
        )
        return out


def legal_actions(t: int, k: int) -> tuple[str, ...]:
    if t == HORIZON or HORIZON - t < k:
        return ("COMMIT_MINUS", "COMMIT_PLUS")
    return ACTIONS


def analytic_information(n: int, regime: str) -> float:
    m = 1 if regime == "DUP" else n
    rho = RHO[regime]
    return MU * MU * m / (1.0 + (m - 1) * rho)


J_SHUFFLE_CLASSES: Final = tuple((n, regime) for n in EVAL_N for regime in REGIMES)


def shuffled_class(n: int, regime: str) -> tuple[int, str]:
    index = J_SHUFFLE_CLASSES.index((n, regime))
    return J_SHUFFLE_CLASSES[(index + 1) % len(J_SHUFFLE_CLASSES)]
