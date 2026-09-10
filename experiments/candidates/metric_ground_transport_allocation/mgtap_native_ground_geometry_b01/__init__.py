"""Typed native ground-geometry B01 adapter over the accepted UCOPE APIs."""

from .geometry import (
    DENSE,
    REL,
    DenseResidualEncoder,
    RelationResidualEncoder,
    NativeGeometryActor,
    build_pair,
    parameter_count,
)

__all__ = [
    "DENSE",
    "REL",
    "DenseResidualEncoder",
    "RelationResidualEncoder",
    "NativeGeometryActor",
    "build_pair",
    "parameter_count",
]
