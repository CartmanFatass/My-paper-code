"""Packed B12 attempt/completion evidence; no per-permutation target copies."""
from __future__ import annotations
import numpy as np

CANDIDATE_DTYPE = np.dtype([
    ("step", "<i4"), ("index", "<i2"), ("m", "i1"), ("columns", "i1", (6,)),
    ("energy", "<f8"), ("slacks", "<f8", (6,)),
    ("started", "?"), ("completed", "?"), ("selected", "?"),
])
assert CANDIDATE_DTYPE.itemsize == 72
EDGE_DTYPE = np.dtype([
    ("step", "<i4"), ("index", "<i2"), ("m", "i1"),
    ("row", "i1"), ("column", "i1"), ("uav", "i1"), ("target_column", "i1"),
    ("arrival_ticks", "<i4"), ("fly_wh", "<f8"), ("slack", "<f8"),
    ("started", "?"), ("completed", "?"),
])
RETURN_DTYPE = np.dtype([
    ("step", "<i4"), ("index", "i1"), ("m", "i1"), ("column", "i1"),
    ("station", "i1"), ("return_wh", "<f8"), ("started", "?"), ("completed", "?"),
])


def blank(dtype, **inputs):
    row = np.zeros((), dtype=dtype)
    for name in dtype.names:
        field = dtype.fields[name][0]
        if field.kind == "f" or field.subdtype and field.subdtype[0].kind == "f":
            row[name] = np.nan
    if "columns" in dtype.names:
        row["columns"] = -1
    if "station" in dtype.names:
        row["station"] = -1
    for name, value in inputs.items():
        row[name] = value
    return row
