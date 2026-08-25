"""Fixture-only native conformance boundary for ONLGR-TBVUUS revision 03."""

from .config import Arm, EncounterSpec, FixtureCase, FixtureTape, ROAD_TEMPLATES, RouteClass
from .native_backend import (
    NativeBackendError,
    native_abi_identity,
    native_artifact_identity,
    native_build_key,
    native_toolchain_identity,
    require_cpp_batched_backend,
    run_native_batch,
    source_sha256,
)
from .oracle import EncounterResult, TickRecord, run_reference_batch

__all__ = [
    "Arm",
    "EncounterResult",
    "EncounterSpec",
    "FixtureCase",
    "FixtureTape",
    "NativeBackendError",
    "RouteClass",
    "ROAD_TEMPLATES",
    "TickRecord",
    "native_abi_identity",
    "native_artifact_identity",
    "native_build_key",
    "native_toolchain_identity",
    "require_cpp_batched_backend",
    "run_native_batch",
    "run_reference_batch",
    "source_sha256",
]
