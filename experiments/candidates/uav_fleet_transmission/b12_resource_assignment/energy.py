"""Pure public S7/S2 uninterrupted-arrival energy; no environment or import work.

Distances are lawful decoded coordinates. Arrival slack is an intent estimate,
not a simultaneous fleet forecast. Scalar evaluation counts include failures.
"""
from __future__ import annotations
import math
import numpy as np

PUBLIC_PARAMETERS = dict(P0=79.86, Pi=88.63, v0=4.03, k1=3 / 120**2,
    k2=1 / (2 * 4.03**2), k3=.5 * .6 * 1.225 * .05 * .503,
    P_z_coeff=15.0, battery_capacity_wh=160.0, return_reserve_ratio=.10,
    limp_home_speed_mps=3.0, horizontal_speed_mps=30.0,
    vertical_speed_mps=5.0, time_step=1.0)


def bump(counts, name):
    if counts is not None:
        counts[name] = counts.get(name, 0) + 1


def power(v, w=0.0, *, counters=None, constant=False):
    """Frozen routed_core scalar arithmetic, Watts; one scalar argument row."""
    key = "constant_power_evaluations" if constant else "power_evaluations"
    bump(counters, key)
    v, w = float(v), float(w)
    if not math.isfinite(v) or not math.isfinite(w) or v < 0.0:
        raise ValueError("power requires finite nonnegative horizontal speed")
    p_profile = 79.86 * (1 + PUBLIC_PARAMETERS["k1"] * v**2)
    term1 = 1 + v**4 / (4 * 4.03**4)
    term2 = v**2 * PUBLIC_PARAMETERS["k2"]
    p_induced = 88.63 * math.sqrt(max(0.0, math.sqrt(term1) - term2))
    p_parasitic = PUBLIC_PARAMETERS["k3"] * v**3
    p_vertical = 15.0 * abs(w)
    result = p_profile + p_induced + p_parasitic + p_vertical
    if not math.isfinite(result):
        raise FloatingPointError("non-finite public power")
    bump(counters, key + "_completed")
    return result


class PublicLaw:
    """One lazy constant-power bundle, retained across controller resets."""
    def __init__(self, cold_counts=None):
        self.cold_counts = {} if cold_counts is None else cold_counts
        self._constants = None
        bump(self.cold_counts, "law_constructions")

    def constants(self):
        if self._constants is None:
            self._constants = tuple(power(v, counters=self.cold_counts, constant=True)
                                    for v in (0.0, 30.0, 3.0))
        return self._constants


def _xyz(value, label):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ValueError(label + " must be finite xyz")
    return result


def _steps(distance, cap_distance):
    full, remainder = divmod(float(distance), float(cap_distance))
    if not (full >= 0.0 and 0.0 <= remainder < cap_distance):
        raise FloatingPointError("invalid divmod flight partition")
    return int(full), remainder, int(remainder > 0.0)


def flight_edge(xyz, target, battery, return_wh, law, *, counters=None):
    """One row/column edge: (arrival ticks, flight Wh, dimensionless slack)."""
    bump(counters, "flight_edges")
    start, target = _xyz(xyz, "start"), _xyz(target, "target")
    battery, return_wh = float(battery), float(return_wh)
    if not math.isfinite(battery) or not math.isfinite(return_wh) or return_wh < 0.0:
        raise ValueError("battery/return cost must be finite")
    dx = float(np.linalg.norm(target[:2] - start[:2]))
    dz = abs(float(target[2] - start[2]))
    if not math.isfinite(dx):
        raise FloatingPointError("non-finite flight distance")
    qx, rx, hx = _steps(dx, 30.0)
    qz, _, hz = _steps(dz, 5.0)
    nx, nz = qx + hx, qz + hz
    ticks = max(nx, nz)
    hover, cruise, _ = law.constants()
    partial = power(rx, counters=counters) if hx else 0.0  # dt is 1s.
    fly_wh = (qx * cruise + partial + (ticks - nx) * hover + 15.0 * dz) / 3600.0
    slack = battery - (fly_wh + return_wh) / 160.0 - .10
    if not math.isfinite(fly_wh) or not math.isfinite(slack) or ticks > np.iinfo(np.int32).max:
        raise FloatingPointError("non-finite or unrecordable flight edge")
    bump(counters, "flight_edges_completed")
    return ticks, float(fly_wh), float(slack)


def target_return(target, stations, law, *, counters=None):
    """Nearest observed 3D station; station0 wins a literal distance tie."""
    bump(counters, "return_evaluations")
    target = _xyz(target, "target")
    stations = np.asarray(stations, dtype=np.float64)
    if stations.shape != (2, 3) or not np.isfinite(stations).all():
        raise ValueError("return requires two finite observed station xyz rows")
    distance = np.linalg.norm(stations - target, axis=1)
    station = int(np.argmin(distance))
    _, _, limp = law.constants()
    wh = float(distance[station]) / 3.0 * limp / 3600.0
    if not math.isfinite(wh):
        raise FloatingPointError("non-finite target return")
    bump(counters, "return_evaluations_completed")
    return station, wh


def permutation_criterion(fly_wh, slack, local_columns, *, counters=None):
    """One complete finite criterion, in increasing eligible-member row order."""
    bump(counters, "permutation_evaluations")
    m = len(local_columns)
    if np.shape(fly_wh) != (m, m) or np.shape(slack) != (m, m):
        raise ValueError("criterion requires square edge arrays")
    if sorted(local_columns) != list(range(m)):
        raise ValueError("criterion requires every local column exactly once")
    energy = math.fsum(float(fly_wh[row, col]) for row, col in enumerate(local_columns))
    slacks = tuple(sorted(float(slack[row, col]) for row, col in enumerate(local_columns)))
    if not math.isfinite(energy) or not all(math.isfinite(x) for x in slacks):
        raise FloatingPointError("non-finite permutation criterion")
    bump(counters, "permutation_evaluations_completed")
    return energy, slacks
