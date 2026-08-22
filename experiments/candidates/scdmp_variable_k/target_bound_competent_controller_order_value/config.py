"""Frozen engineering constants for the TBCC revision-02 native host."""

from __future__ import annotations

COMPONENT = "scdmp.tbcc_order_value.r02.full_host"
LOADER_KEY = "scdmp_tbcc_order_value_r02_full_host"
HOST = "QUAD-UAV-PALLET-GANTRY-24P5M-v1"

NATIVE_ABI_VERSION = 2
FIXTURE_MAGIC = 0x5442434352303241  # ASCII-ish: TBCCR02A
MAX_BATCH_WIDTH = 144
FUNCTIONAL_BATCH_WIDTHS = (1, 8, 12, 32, 120, 144)
HORIZON_TICKS = 364
MAX_HOLD_TICKS = 13
OBSERVATION_WIDTH = 18

HOOK_HANDOFF = 1
FORMATION_ROTATE = 2

LOAD_SHARE_ACTIONS = (
    (0, 0, 0, 0),
    (1, -1, 0, 0),
    (-1, 1, 0, 0),
    (0, 0, 1, -1),
    (0, 0, -1, 1),
    (1, 0, -1, 0),
    (-1, 0, 1, 0),
    (0, 1, 0, -1),
    (0, -1, 0, 1),
)
ACTIONS = tuple((forward, *share) for forward in (1, 2) for share in LOAD_SHARE_ACTIONS)
ACTION_COUNT = len(ACTIONS)

ALLOWED_K = frozenset((5, 7, 11, 13))
TARGET_SWITCH_TICKS = frozenset((91, 273))

MSVC_COMPILE_FLAGS = (
    "/nologo",
    "/std:c++20",
    "/O2",
    "/EHsc",
    "/LD",
    "/W4",
)
