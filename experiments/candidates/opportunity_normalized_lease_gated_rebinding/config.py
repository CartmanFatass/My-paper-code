"""Frozen registration for ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1."""

from __future__ import annotations

from dataclasses import dataclass

TREATMENT = "ONLGR-B1-MARKED-LEASE-CENSORED-RATE-v1"
ARTIFACT_KIND = "ONLGR_B1_MARKED_LEASE_CENSORED_RATE_RESULT"
HORIZON = 256
LEASE_TICKS = 12
ROLES = ("T", "R")
ACTIONS = ("KEEP", "REFRESH-SAME", "REBIND")
LEARNED_ARMS = ("ONLGR", "RAW-BOUNDARY-LEASE", "TIMING-ONLY-ONLGR")
TRAIN_SCHEDULES = ("CONST-8", "CONST-24", "MID-8-TO-24", "MID-24-TO-8")
HELDOUT_SCHEDULES = (
    "CONST-4", "CONST-16", "CONST-32", "MID-4-TO-32", "MID-32-TO-4",
    "ALT-4-32-4-32", "ALT-32-4-32-4",
)
IID_SCHEDULE = "RAND-IID-4-16-32"
SEEDS = (17, 31, 47, 61, 79, 97, 109, 127)
VALIDATION_ROOTS = (1009, 1013)
FIXED_RATES = (1 / 64, 1 / 32, 1 / 16, 1 / 8)
FIXED_MARKS = (0.25, 0.50, 0.75)
DIAGNOSTIC_ARMS = (
    "ALWAYS-KEEP", "ALWAYS-REFRESH-WHEN-LEGAL",
    "ALWAYS-REBIND-WHEN-LEGAL", "STATE-ORACLE",
)

GAMMA_TICK = 0.99 ** (1 / 8)
LAMBDA_TICK = 0.95 ** (1 / 8)
PPO = {
    "clip": 0.20,
    "learning_rate": 3e-4,
    "value_coefficient": 0.5,
    "entropy_coefficient": 0.0,
    "gradient_norm_cap": 1.0,
    "epochs": 4,
    "episodes_per_update": 32,
}


@dataclass(frozen=True)
class RunConfig:
    horizon: int = HORIZON
    seeds: tuple[int, ...] = SEEDS
    training_episodes: int = 256
    native_episodes: int = 32
    diagnostic_episodes: int = 16
    safety_episodes: int = 16
    fixed_selection_episodes: int = 16
    ppo_epochs: int = 4
    episodes_per_update: int = 32
    cpu_workers: int = 1
    wall_seconds: int = 45 * 60
    peak_rss_bytes: int = 2 * 1024**3
    total_tick_cap: int = 7_000_000

    @property
    def registered(self) -> bool:
        return self == PRODUCTION_CONFIG


PRODUCTION_CONFIG = RunConfig()


def registered_budget(config: RunConfig) -> dict[str, int]:
    n = len(config.seeds)
    schedules = len(HELDOUT_SCHEDULES)
    training = len(LEARNED_ARMS) * n * config.training_episodes * config.horizon
    native = len(LEARNED_ARMS) * n * schedules * config.native_episodes * config.horizon
    iid = len(LEARNED_ARMS) * n * config.native_episodes * config.horizon
    safety = len(LEARNED_ARMS) * n * schedules * config.safety_episodes * config.horizon
    clamp = len(LEARNED_ARMS) * n * schedules * config.diagnostic_episodes * config.horizon
    diagnostic = len(DIAGNOSTIC_ARMS) * n * schedules * config.diagnostic_episodes * config.horizon
    fixed_select = (
        len(FIXED_RATES) * len(FIXED_MARKS) * len(VALIDATION_ROOTS)
        * len(TRAIN_SCHEDULES) * config.fixed_selection_episodes * config.horizon
    )
    fixed_eval = n * schedules * config.diagnostic_episodes * config.horizon
    yoke_max = 2 * n * schedules * config.diagnostic_episodes * config.horizon
    keep_probe = n * schedules * config.diagnostic_episodes * config.horizon
    values = {
        "training_team_ticks": training,
        "native_team_ticks": native,
        "iid_future_k_team_ticks": iid,
        "safety_team_ticks": safety,
        "exposure_clamp_team_ticks": clamp,
        "degenerate_oracle_team_ticks": diagnostic,
        "fixed_selection_team_ticks": fixed_select,
        "fixed_evaluation_team_ticks": fixed_eval,
        "preselected_yoke_max_team_ticks": yoke_max,
        "keep_grid_probe_team_ticks": keep_probe,
    }
    values["maximum_total_team_ticks"] = sum(values.values())
    return values
