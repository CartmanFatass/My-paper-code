"""Frozen constants for RCLE-PCPV-SCIENCE-20260829-02."""

from __future__ import annotations

SCIENCE_REVISION = "RCLE-PCPV-SCIENCE-20260829-02"
RNG_DOMAIN = "RCLE-PCPV-R02-20260829"
ROOT_LABELS = tuple(f"RCLE-PCPV-R02-ROOT-{i:02d}" for i in range(16))

SECTORS = 80
BEACONS = 4
HORIZON = 56
EVENT_TICK = 20
CLAIM_PERIOD = 4
SERVICE_RADIUS = 2
MAX_SPEED = 3

TRAIN_CELLS = ((6, 6), (9, 9), (6, 9), (9, 6))
EVAL_CELLS = ((5, 5), (10, 10), (5, 10), (10, 5))
CHURN_CELLS = ((5, 10), (10, 5))
SCRIPTED_PACKAGES = ("CARRY", "REPLAN", "FRAGMENTED", "NEAREST")
LEARNED_ARMS = ("KEEP", "FLEX")

SCRIPTED_EPISODES = 4 * 16 * 4 * 512
TRAIN_EPISODES = 2 * 16 * 256 * 32
NATURAL_EVAL_EPISODES = 2 * 16 * 4 * 512
CLAMP_EPISODES = 16 * 2 * 512
MAX_EPISODES = 475_136
MAX_TICKS = 26_607_616
REGISTERED_TAILS = 70
T_CRITICAL = 3.89747369134303
GAMMA_GLOBAL = 0.9992857142857143

CYCLE = "2026-08-28.10-clean-01a04a02-rcle-public-plan-01"
RESULT_ROOT_PARTS = (
    "temp", "directions", "roster_consistent_latent_exploration", "exp", CYCLE
)


def cell_name(cell: tuple[int, int]) -> str:
    return f"{cell[0]}->{cell[1]}"


def beacon_positions(tick: int) -> tuple[int, int, int, int]:
    phase = tick // CLAIM_PERIOD
    return tuple((20 * j + phase) % SECTORS for j in range(BEACONS))


def demands(n: int, tick: int) -> tuple[int, int, int, int]:
    base, remainder = divmod(n, BEACONS)
    edge = (tick // 8) % BEACONS
    extra = {(edge + m) % BEACONS for m in range(remainder)}
    out = tuple(base + int(j in extra) for j in range(BEACONS))
    if sum(out) != n or min(out) < 1:
        raise AssertionError("frozen demand law violated")
    return out
