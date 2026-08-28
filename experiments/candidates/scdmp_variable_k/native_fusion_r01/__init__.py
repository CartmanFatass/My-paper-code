"""Result-blind S0 source-conformance surface for CLOSED native fusion R01."""

from .contract import EventOrder, Regime, deterministic_fixture
from .native import native_run_fixture
from .oracle import oracle_run_fixture
from .validation import recompute_endpoint
from .taint import Consumer, token_view
from .barriers import S0FirewallError, StageBarrier

__all__ = [
    "EventOrder",
    "Consumer",
    "Regime",
    "S0FirewallError",
    "StageBarrier",
    "deterministic_fixture",
    "native_run_fixture",
    "oracle_run_fixture",
    "recompute_endpoint",
    "token_view",
]
