"""Matched native Scenario 1 worlds and read-only load diagnostics."""

from .scenes import (
    MAX_UAVS,
    N_USERS,
    WORLD_IDS,
    MatchedWorld,
    MatchedWorldS1,
    make_native_scene,
    matched_world,
    refresh_native_scene,
    service_diagnostics,
)

# The evaluator is intentionally not imported here.  Its Torch/model import is
# deferred until after native admission by the production entry point.

__all__ = [
    "MAX_UAVS",
    "N_USERS",
    "WORLD_IDS",
    "MatchedWorld",
    "MatchedWorldS1",
    "make_native_scene",
    "matched_world",
    "refresh_native_scene",
    "service_diagnostics",
]
