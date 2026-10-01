"""Bounded typed candidate evidence, no pickle or full intermediate RF corpus."""
from __future__ import annotations
import numpy as np

CANDIDATE_DTYPE = np.dtype([
    ("step", "<i4"), ("index", "<i2"), ("kind", "i1"),
    ("sweep", "i1"), ("member", "i1"), ("axis", "i1"), ("sign", "i1"),
    ("q", "i1"), ("ticks", "i1"), ("rf_started", "i1"), ("rf_completed", "i1"),
    ("completed", "?"), ("accepted", "?"), ("selected", "?"),
    ("targets", "<f8", (8, 3)), ("xyz", "<f8", (3, 8, 3)),
    ("battery", "<f8", (3, 8)), ("margin", "<f8", (3, 8)),
    ("F", "?", (3, 8)), ("waits", "<i8", (3, 8)),
    ("cancelled", "?", (8,)), ("crossed_F", "?", (8,)),
    ("crossed_reserve", "?", (8,)), ("crossed_cutoff", "?", (8,)),
    ("forecast_travel", "<f8"), ("score", "<f8"), ("target_travel", "<f8"),
    ("qos", "<f8", (3,)), ("return_cost", "<f8", (3,)),
    ("tick_digest", "u1", (32,)), ("rf_digest", "u1", (3, 32)),
])
assert CANDIDATE_DTYPE.itemsize <= 2048
KINDS = ("H1", "G", "carried", "current", "pattern")


def empty_candidate(step, index, kind, layout, q, *, sweep=-1, member=-1, axis=-1, sign=0):
    row = np.zeros((), dtype=CANDIDATE_DTYPE)
    for name, value in (("step", step), ("index", index), ("kind", kind),
                        ("q", q), ("sweep", sweep), ("member", member),
                        ("axis", axis), ("sign", sign), ("targets", layout)):
        row[name] = value
    row["score"] = np.nan
    row["target_travel"] = np.nan
    return row


def digest_bytes(value):
    return np.frombuffer(bytes.fromhex(value), dtype=np.uint8).copy()


def install_forecast(row, forecast):
    for name in ("xyz", "battery", "margin", "F", "waits", "cancelled", "crossed_F",
                 "crossed_reserve", "crossed_cutoff"):
        row[name] = getattr(forecast, name)
    row["forecast_travel"] = forecast.travel_m
