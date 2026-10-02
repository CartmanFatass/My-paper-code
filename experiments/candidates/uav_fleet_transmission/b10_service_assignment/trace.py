"""Bounded typed candidate evidence, no pickle or full intermediate RF corpus."""
from __future__ import annotations
import numpy as np

CANDIDATE_DTYPE = np.dtype([
    ("step", "<i4"), ("index", "<i2"), ("pair_left", "i1"), ("pair_right", "i1"), ("alias_base", "?"),
    ("q", "i1"), ("hold_xy", "?", (8,)), ("ticks_started", "i1"), ("ticks", "i1"), ("rf_started", "i1"), ("rf_completed", "i1"),
    ("completed", "?"), ("accepted", "?"), ("selected", "?"),
    ("targets", "<f8", (8, 3)), ("xyz", "<f8", (3, 8, 3)),
    ("battery", "<f8", (3, 8)), ("margin", "<f8", (3, 8)),
    ("F", "?", (3, 8)), ("waits", "<i8", (3, 8)),
    ("cancelled", "?", (8,)), ("crossed_F", "?", (8,)),
    ("crossed_reserve", "?", (8,)), ("crossed_cutoff", "?", (8,)),
    ("forecast_travel", "<f8"), ("score", "<f8"),
    ("qos", "<f8", (3,)), ("return_cost", "<f8", (3,)),
    ("tick_digest", "u1", (32,)), ("rf_digest", "u1", (3, 32)),
])
assert CANDIDATE_DTYPE.itemsize <= 2048
# pair (-1,-1) is the ordinary base; all others are global UAV indices.

def empty_candidate(step, index, pair, layout, q, *, alias_base=False):
    row = np.zeros((), dtype=CANDIDATE_DTYPE)
    row["step"], row["index"], row["q"] = step, index, q
    row["pair_left"], row["pair_right"] = pair
    row["targets"] = layout
    row["hold_xy"] = ~np.isfinite(layout[:, :2]).all(axis=1)
    row["alias_base"] = alias_base
    row["score"] = np.nan
    return row


def digest_bytes(value):
    return np.frombuffer(bytes.fromhex(value), dtype=np.uint8).copy()


def install_forecast(row, forecast):
    for name in ("xyz", "battery", "margin", "F", "waits", "cancelled", "crossed_F",
                 "crossed_reserve", "crossed_cutoff"):
        row[name] = getattr(forecast, name)
    row["forecast_travel"] = forecast.travel_m
