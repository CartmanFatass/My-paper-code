"""Frozen engineering binding for the Pro-closed VQFP VNPA r03 card.

This module contains identities and cardinalities only.  It does not generate
or score the frozen panel, and importing it cannot begin scientific activity.
"""

from __future__ import annotations

from typing import Final

COMPONENT: Final[str] = "vqfp.vnpa.r03.full_chain"
EXACT_REVISION: Final[str] = (
    "VQFP-VARIABLE-N-PHYSICAL-ASSOCIATION-VALUE-R01-SCIENCE-20260823-03"
)
HOST: Final[str] = "VQFP-MARKOV-FIELD-COVERAGE-1D-VN-v2"
NATIVE_ABI_VERSION: Final[int] = 3
SCIENCE_CARD_SHA256: Final[str] = "df9bd52df6c873e79c315b1d134019df8721d5ec73b4b6a5566be1663305626e"
ARMS: Final[tuple[str, ...]] = (
    "T", "FREE", "T-P", "F-P", "EQ", "DENS", "MASS", "MARG0",
    "ORACLE", "FREE-EMBED",
)
ROSTERS: Final[tuple[int, ...]] = (4, 6, 8, 12)
TRAIN_ROSTERS: Final[tuple[int, ...]] = (4, 8)
HELDOUT_ROSTERS: Final[tuple[int, ...]] = (6, 12)
SUPPORTED_BATCH_WIDTHS: Final[tuple[int, ...]] = (1, 8, 32, 64)
STAGE_TILE_WIDTHS: Final[tuple[int, ...]] = (8, 32, 64)
STAGE_WORKERS: Final[tuple[int, ...]] = (1, 2, 4, 8)

FROZEN_COUNTS: Final[dict[str, int]] = {
    "treatment_candidates": 2048,
    "free_candidates": 2048,
    "finalists_each": 32,
    "development_episodes": 768,
    "validation_episodes": 3072,
    "evaluation_episodes": 24576,
    "evaluation_arms": 10,
    "bootstrap_draws": 20000,
    "bootstrap_block_occurrences": 12,
    "bootstrap_episode_selections": 491_520_000,
}

QUESTION_RELEVANT_ACTIVITY = (
    "first accepted candidate score on any frozen development host episode"
)


def validate_synthetic_limits(*, candidates: int, episodes: int, draws: int) -> None:
    for name, value, upper in (
        ("candidates", candidates, 64),
        ("episodes", episodes, 128),
        ("draws", draws, 256),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if not 0 < value <= upper:
            raise ValueError(f"{name} must be in [1,{upper}] for result-blind TEST")


def validate_cost_collapse_limits(
    *, width: int, workers: int, candidates: int, host_episodes: int, draws: int
) -> None:
    """Fail closed at the exact non-frozen stage-R01 measurement envelope."""
    for name, value in (
        ("width", width), ("workers", workers), ("candidates", candidates),
        ("host_episodes", host_episodes), ("draws", draws),
    ):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
    if width not in STAGE_TILE_WIDTHS:
        raise ValueError("width must be one of 8, 32, 64")
    if workers not in STAGE_WORKERS:
        raise ValueError("workers must be one of 1, 2, 4, 8")
    if not 0 < candidates <= 512:
        raise ValueError("candidates must be in [1,512]")
    if not 0 < host_episodes <= 4096:
        raise ValueError("host_episodes must be in [1,4096]")
    if not 0 < draws <= 4096:
        raise ValueError("draws must be in [1,4096]")
    if candidates * host_episodes > 245_760:
        raise ValueError("synthetic score rows exceed 245760")
