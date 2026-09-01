"""B/EXPLORE-only native shadow telemetry for VNFC post-churn recovery."""

from .native_backend import (
    BNativeTelemetryBatch,
    NativeTelemetryError,
    PairedPrimaryShadowBatch,
    require_boundary_equivalence,
    derive_recovery_telemetry,
    native_artifact_identity,
    performance_readiness,
)

__all__ = [
    "BNativeTelemetryBatch",
    "NativeTelemetryError",
    "PairedPrimaryShadowBatch",
    "require_boundary_equivalence",
    "derive_recovery_telemetry",
    "native_artifact_identity",
    "performance_readiness",
]
