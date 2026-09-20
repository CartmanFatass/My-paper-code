"""Fixed A02 behavior-law wrapper around the A01 Retrace artifact producer."""

from __future__ import annotations

from pathlib import Path
import time
from typing import Mapping

from ..off_termination_a01.study import Config, run_study as _produce_study


OBJECT = "termination_reuse_behavior_clock_a02"
SEEDS = (91031, 91032, 91033)
BEHAVIOR_ZETA = {
    "long_behavior": .125,
    "matched_termination": .5,
}
LIMITS = (
    "exploratory independent host; no UAV or novelty claim",
    "fixed teammate law and fixed target beta; behavior termination differs by arm",
    "same addressed exogenous draws and row exposure; observed behavior trajectories differ",
    "same ordinary Retrace learner; collection-law package comparison, not causal mediation",
    "constant step size and finite exposure; no convergence claim",
)


def make_config(arm: str, seed: int) -> Config:
    """Map a declared artifact arm to its fixed A02 Retrace configuration."""
    if arm not in BEHAVIOR_ZETA or seed not in SEEDS:
        raise ValueError("invalid A02 arm/seed")
    return Config(arm="retrace", seed=seed, zeta=BEHAVIOR_ZETA[arm])


def run_study(arm: str, seed: int, out: Path, admission: Mapping,
              start: float | None = None):
    """Produce one A02 artifact without exposing scientific CLI overrides."""
    config = make_config(arm, seed)
    return _produce_study(
        config, out, admission, start,
        object_id=OBJECT, run_label=arm, limits=LIMITS,
    )
