"""Prospective constants; importing this module creates no scientific exposure."""

from __future__ import annotations

from itertools import product

DIRECTION = "uav_radio_uncertainty"
TAG = "b01_correlated_shadow_a01"
LEAD = "Codex DM (native child)"
N_UAVS = 5
N_USERS = 50
HORIZON = 256
HOLD = 4
DELIVERY = 3
COMPUTE_SECONDS = 1.336
REPORT_BYTES = 75
COMMAND_BYTES = 16
ROUND_BYTES = 391
MAP_BYTES = 400
BITRATE = 2000
PILOT_SLOTS = 50
PILOT_SECONDS = 0.1
PAYLOAD_REPORT_WEIGHT = 0.9
SIGMA_DB = 4.14
CORRELATION_METRES = 17.62
CARRIER_HZ = 2.0e9
TRANSMIT_DBM = 23.0
NOISE_DBM = -80.0
MIN_SINR_DB = 3.0
CAPACITY = 10
COMPONENT_METRES = 30.0
AREA_METRES = 1000.0
MIN_HEIGHT = 50.0
MAX_HEIGHT = 150.0
PARTICLES = 32
BASE_PARTICLES = 16
MODEL_STEPS = 7
NUMPY_VERSION = "1.26.3"
PHYSICAL_NAMESPACE = 0x52465048
MODEL_NAMESPACE = 0x52464D43
PHYSICAL_ROOT = 29640001
MODEL_ROOT = 29640002
WORLD_SEEDS = tuple(range(29641000, 29641032))
CONSTRUCTOR_SEED = 29641999
FIXTURE_SEED = 29641900
FIXTURE_CONSTRUCTOR_SEEDS = (29641996, 29641997, 29641998)
ARMS = ("P", "U32")
COMMAND_GRID = tuple(sorted(product((-1, 0, 1), repeat=3),
                            key=lambda q: (sum(x * x for x in q), q)))


def payload_weight(tick: int) -> float:
    """Weight the transition departing report-boundary state ``tick``."""
    return PAYLOAD_REPORT_WEIGHT if tick % HOLD == 0 else 1.0


def arm_order(world: int) -> tuple[str, str]:
    if world not in WORLD_SEEDS:
        raise ValueError("world outside the fixed scientific panel")
    return ARMS if (world - WORLD_SEEDS[0]) % 2 == 0 else ARMS[::-1]
