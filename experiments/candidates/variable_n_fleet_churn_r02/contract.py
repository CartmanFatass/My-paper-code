"""Frozen constants and narrow interfaces for the VNFC R02 scalar law.

This module deliberately contains no runtime discovery.  Every value here is a
literal from the prospective A0 freeze.  Callers inject the four content-bound
scalar transcendental operations through :class:`ScalarTranscendentals`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class ContractViolation(ValueError):
    """The requested operation is outside the frozen finite law."""


LAW_CONFIG = "VNFC-R02-ORC-B64-Q52-U64-V1"
REVISION = "VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02"
A0_OBJECT = "VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
A0_SEED = 2026090191
A0_NAMESPACE = "temp/vnfc-r02-a0/VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0"
FUTURE_B_NAMESPACE = "temp/vnfc-bexp-r02/VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02"

RNG_RECORD_TAG = "VNFC-R02-RNG-V1"
MASS_TOTAL = 1 << 52
UINT64_LIMIT = 1 << 64
UINT256_LIMIT = 1 << 256
MAX_CANDIDATES = 8

TOKEN_ROLES = (
    "EXEC_FAILED",
    "RELAY_FAILED",
    "EXEC_INTACT",
    "RELAY_INTACT",
)
PHASE_SEEDS = {
    "DEBUG": (2026090201,),
    "PRIMARY": (2026090211, 2026090221, 2026090231),
    "OPTIONAL": (2026090241, 2026090251),
}

LR = float.fromhex("0x1.3a92a30553261p-12")
BETA1 = float.fromhex("0x1.ccccccccccccdp-1")
BETA2 = float.fromhex("0x1.ff7ced916872bp-1")
EPS = float.fromhex("0x1.5798ee2308c3ap-27")
GRADIENT_CAP = float.fromhex("0x1.0000000000000p-1")
WEIGHT_DECAY = float.fromhex("0x1.a36e2eb1c432dp-14")
LOGIT_FLOOR = -16.0


@runtime_checkable
class ScalarTranscendentals(Protocol):
    """Injected exact scalar callable surface from the byte-bound kernel.

    Implementations must invoke the exact shape-(1,) ATen default schemas.  The
    finite-law core intentionally provides no alternate approximation.
    """

    def sigmoid_R02(self, value: float) -> float: ...

    def exp_R02(self, value: float) -> float: ...

    def log_R02(self, value: float) -> float: ...

    def sqrt_R02(self, value: float) -> float: ...

