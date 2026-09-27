"""B03 anchor set A(s): deployment anchors computed from the raw S7-S2 central state.

State layout (306 fields; ``envs/pettingzoo/relay/routed_core.py::UAVRoutedRelayEnv._get_state``
followed by ``envs/pettingzoo/relay/energy_aware.py::UAVEnergyAwareRelayEnv._get_state``; verified
against a live ``Config("S7-S2")`` environment by test): UAV xyz 8 x 3 at [0:24] (x/area, y/area,
(z-hmin)/hspan) | UAV loads 8 at [24:32] | users 30 x 6 at [32:212] (x/area, y/area, vx, vy,
connected, sinr) | BS xyz at [212:215] (x/area, y/area, z/hmax) | step/max_steps at [215] |
energy block 90 at [216:306].  The observation/state normalizers are off on this host, so the
state the coordinator decides on carries these raw values.

Anchors (area-normalised xy, shape (9, 2)), the H1 reference's own generator
(``b01/heuristic.py::LayoutHeuristic.plan``, central mode):
- six service centroids = ``estimator_kmeans(users_m, 6, iterations=30)`` on the 30 user xy in
  metres (state xy x area), seeded at ``np.linspace(0, 29, 6, dtype=int)`` over the env's user
  index order; ordered by descending assigned user count, ties by centroid index
  (``np.argsort(-counts, kind="stable")``, copied from ``LayoutHeuristic.plan``);
- two relay points at 1/3 and 2/3 of the segment from the BS xy to the mean of the six
  centroids (``bs + (i + 1) / 3 * (centre - bs)``, i = 0, 1), labels 0 and 1 in that order
  (ascending distance from the BS);
- labels 2..7 = the ordered centroids; label 8 = FREE (no anchor, row of zeros).
Deterministic: no random draw; the same state gives the same anchors (the index-seeded k-means
is not permutation-invariant over users, and the anchors inherit that, as H1 does).
"""

from __future__ import annotations

import numpy as np

from ..b01.heuristic import estimator_kmeans

AREA_M = 8000.0
STATE_DIM = 306
N_UAVS = 8
N_USERS = 30
USER_FIELDS = 6
STATE_UAV_XYZ = slice(0, 24)
STATE_UAV_LOADS = slice(24, 32)
STATE_USERS = slice(32, 32 + N_USERS * USER_FIELDS)        # [32:212]
STATE_BS_XYZ = slice(212, 215)
STATE_STEP = 215
STATE_ENERGY = slice(216, 306)

N_RELAY = 2
N_SERVICE = 6
KMEANS_ITERATIONS = 30
RELAY_FRACTIONS = tuple((index + 1) / (N_RELAY + 1) for index in range(N_RELAY))
RELAY_LABELS = tuple(range(N_RELAY))                        # 0, 1
SERVICE_LABELS = tuple(range(N_RELAY, N_RELAY + N_SERVICE))  # 2..7
FREE_LABEL = N_RELAY + N_SERVICE                            # 8
N_LABELS = FREE_LABEL + 1                                   # 9
ANCHOR_DIM = 2 * N_LABELS                                   # 18 numbers per anchor set


def _state(state) -> np.ndarray:
    state = np.asarray(state, dtype=np.float64)
    if state.shape != (STATE_DIM,):
        raise ValueError(f"S7-S2 central state must have shape ({STATE_DIM},), got {state.shape}")
    if not np.all(np.isfinite(state)):
        raise ValueError("S7-S2 central state has a non-finite entry")
    return state


def users_xy_m(state, area_m: float = AREA_M) -> np.ndarray:
    """(30, 2) user xy in metres, in the env's user index order."""
    users = _state(state)[STATE_USERS].reshape(N_USERS, USER_FIELDS)
    return users[:, :2] * float(area_m)


def bs_xy_m(state, area_m: float = AREA_M) -> np.ndarray:
    return _state(state)[STATE_BS_XYZ][:2] * float(area_m)


def anchor_set(state, area_m: float = AREA_M) -> dict:
    """Anchors and their parts: ``anchors`` (9, 2) area-normalised, plus the metre-valued pieces."""
    users = users_xy_m(state, area_m)
    bs = bs_xy_m(state, area_m)
    centroids, counts = estimator_kmeans(users, N_SERVICE, KMEANS_ITERATIONS)
    order = np.argsort(-counts, kind="stable")
    centre = centroids.mean(axis=0)
    relays = np.asarray([bs + fraction * (centre - bs) for fraction in RELAY_FRACTIONS],
                        dtype=np.float64).reshape(N_RELAY, 2)
    anchors_m = np.concatenate((relays, centroids[order], np.zeros((1, 2))), axis=0)
    anchors = anchors_m / float(area_m)
    anchors[FREE_LABEL] = 0.0
    return {"anchors": anchors, "anchors_m": anchors_m, "centroids_m": centroids,
            "counts": counts, "order": order, "relays_m": relays, "bs_m": bs, "users_m": users}


def anchors_from_state(state, area_m: float = AREA_M) -> np.ndarray:
    """(9, 2) float64 anchors, area-normalised; row 8 (FREE) is zeros."""
    return anchor_set(state, area_m)["anchors"]
