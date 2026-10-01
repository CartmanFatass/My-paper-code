"""Frozen P_FULL/P_PRIOR package contract; importing creates no scientific exposure."""
from itertools import product
DIRECTION = "uav_radio_information_cost"
TAG = "b01_pilot_package_a01"
LEAD = "Codex DM (native child)"
N_UAVS, N_USERS, HORIZON, HOLD = 5, 50, 256, 4
ARMS = ("P_FULL", "P_PRIOR")
WORLD_SEEDS = tuple(range(29651000, 29651032))
CONSTRUCTOR_SEED = 29651999
FIXTURE_SEED = 29651900
FIXTURE_CONSTRUCTOR_SEED = 29651998
SIGMA_DB, CORRELATION_METRES = 4.14, 17.62
PRIOR_VARIANCE = SIGMA_DB ** 2
CARRIER_HZ, TRANSMIT_DBM, NOISE_DBM = 2.0e9, 23.0, -80.0
MIN_SINR_DB, CAPACITY, COMPONENT_METRES = 3.0, 10, 30.0
AREA_METRES, MIN_HEIGHT, MAX_HEIGHT = 1000.0, 50.0, 150.0
COMMAND_BYTES, MAP_BYTES, BITRATE = 16, 400, 2000
NUMPY_VERSION = "1.26.3"
PHYSICAL_NAMESPACE, PHYSICAL_ROOT = 0x52465048, 29640001
DEPENDENCY_COMMIT = "9b6f493b343c2939b374a1ce21384266d3257456"
COMMAND_GRID = tuple(sorted(product((-1,0,1), repeat=3), key=lambda q:(sum(x*x for x in q),q)))
VERSION = 6

def arm_settings(arm):
    if arm == "P_FULL":
        return dict(delivery=3,compute_seconds=1.336,report_bytes=75,round_bytes=391,
                    pilot_slots=50,pilot_seconds=.1,payload_report_weight=.9)
    if arm == "P_PRIOR":
        return dict(delivery=2,compute_seconds=1.436,report_bytes=25,round_bytes=141,
                    pilot_slots=0,pilot_seconds=0.,payload_report_weight=1.)
    raise ValueError("unknown package arm")

def payload_weight(arm,tick):
    return arm_settings(arm)["payload_report_weight"] if tick % HOLD == 0 else 1.

def arm_order(world):
    if world not in WORLD_SEEDS:
        raise ValueError("world outside fixed panel")
    return ARMS if (world-WORLD_SEEDS[0]) % 2 == 0 else ARMS[::-1]
