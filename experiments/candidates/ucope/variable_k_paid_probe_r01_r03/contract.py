"""Frozen technical contract for the result-blind UCOPE R01 r03 S0/S1 core."""

from __future__ import annotations

from enum import IntEnum
from typing import Final


OBJECT_REVISION: Final[str] = (
    "UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03"
)
COMPONENT: Final[str] = "ucope.variable_k_paid_probe.r01_r03.full_host"
NATIVE_ABI_VERSION: Final[int] = 1
NATIVE_HOST_KIND: Final[str] = "UCOPE_R01_R03_CPP_BATCHED_SEMANTIC_CORE_S1"
SUPPORTED_BATCH_WIDTHS: Final[tuple[int, ...]] = (8, 32, 256, 768)
K_TRAIN: Final[tuple[int, ...]] = (1, 3, 5, 7, 9)
K_TEST: Final[tuple[int, ...]] = (2, 4, 6, 8)
ROOT_ACTION_COUNT: Final[int] = 6
TAIL_ACTION_COUNT: Final[int] = 5
SCORER_FEATURES: Final[int] = 13
BASELINE_FEATURES: Final[int] = 9
EPISODES_PER_BATCH: Final[int] = 256
TRAINING_BATCHES: Final[int] = 320
REGISTERED_MASTER_SEEDS: Final[frozenset[int]] = frozenset(
    (101, 211, 307, 401, 503, 601, 701, 809, 907, 1009)
)
TEST_NAMESPACE: Final[str] = "TEST_ONLY_UCOPE_R01_R03_S0"
TEST_SEEDS: Final[tuple[int, ...]] = (0x13579BDF2468ACE0, 0x0F1E2D3C4B5A6978)
S1_TEST_NAMESPACE: Final[str] = "TEST_ONLY_UCOPE_R01_R03_S1"
S1_TEST_SEEDS: Final[tuple[int, ...]] = tuple(
    0xA104000000000000 + index for index in range(10)
)
S1_TEST_REQUEST: Final[str] = "SEMANTIC_CORE_TEST"
COUNTER_LAYOUT_ID: Final[str] = "UCOPE_R01_R03_PHILOX4X32_10_COUNTER_LAYOUT_V1"
LEARNED_ARM_COUNT: Final[int] = 3
ALL_ARM_COUNT: Final[int] = 6
FINAL_CHECKPOINT_SLOT_COUNT: Final[int] = 90


class Panel(IntEnum):
    PERSISTENT = 0
    REDRAW = 1
    SEVERED = 2


class LearnedArm(IntEnum):
    COUNT = 0
    RAW = 1
    BELIEF_FEATURE = 2


class NonlearnedArm(IntEnum):
    BELIEF_DP = 3
    IMMEDIATE_DP = 4
    FORCED_PROBE_BLIND_DP = 5


class CounterNamespace(IntEnum):
    REGIME = 1
    PROBE_ACTUAL = 2
    PROBE_DISPLAY = 3
    TAIL_Z = 4
    ACTION = 5
    INIT = 6


def require_test_namespace(namespace: str, master_seed: int) -> None:
    """Fail closed before S0 can touch a registered seed or non-TEST namespace."""

    if namespace != TEST_NAMESPACE:
        raise PermissionError("the retained S0 coupon accepts only its TEST namespace")
    if isinstance(master_seed, bool) or not isinstance(master_seed, int):
        raise TypeError("master_seed must be an integer")
    if master_seed < 0 or master_seed >= 1 << 64:
        raise ValueError("master_seed must fit unsigned 64 bits")
    if master_seed in REGISTERED_MASTER_SEEDS:
        raise PermissionError("registered UCOPE master seeds are forbidden in S0")


def require_s1_test_request(namespace: str, test_seed: int, request: str) -> None:
    """Admit only one result-blind S1 semantic-core request before native work."""

    if namespace != S1_TEST_NAMESPACE:
        raise PermissionError("S1 accepts only its exact TEST namespace")
    if request != S1_TEST_REQUEST:
        raise PermissionError("partial, complete-result, output, and package requests are forbidden in S1")
    if isinstance(test_seed, bool) or not isinstance(test_seed, int):
        raise TypeError("S1 TEST seed must be an integer")
    if test_seed not in S1_TEST_SEEDS:
        raise PermissionError("S1 accepts only its ten nonregistered structural TEST seed slots")
    if test_seed in REGISTERED_MASTER_SEEDS:
        raise PermissionError("registered UCOPE master seeds are forbidden in S1")


def require_supported_width(width: int) -> None:
    if isinstance(width, bool) or not isinstance(width, int):
        raise TypeError("batch width must be an integer")
    if width not in SUPPORTED_BATCH_WIDTHS:
        raise ValueError(f"batch width must be one of {SUPPORTED_BATCH_WIDTHS}")
