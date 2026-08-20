"""Thin, file-backed observability helpers for the HMASD control plane.

The package deliberately separates read-only diagnosis from explicit repair.
It does not implement workflow transitions, retries, or scientific routing.
"""

from __future__ import annotations

DOCTOR_SCHEMA = "HMASD_CONTROL_PLANE_DOCTOR_V1"
LONG_EFFECT_SCHEMA = "HMASD_LONG_EFFECT_V1"

__all__ = ["DOCTOR_SCHEMA", "LONG_EFFECT_SCHEMA"]
