"""Strictly local own-grant rules; evaluator history never enters selection."""

import numpy as np

from . import protocol as p


def _local(ids, sinr, tick):
    ids, sinr = np.asarray(ids), np.asarray(sinr)
    p.require(ids.ndim == 1 and ids.dtype.kind in 'iu' and sinr.shape == ids.shape,
              'local eligible IDs/SINRs must be paired vectors')
    p.require(np.all((ids >= 0) & (ids < p.U)) and len(np.unique(ids)) == len(ids), 'invalid registered local IDs')
    # The producer supplies IDs from its single shared eligibility scan. Do not
    # repurchase that threshold scan in each local rule.
    p.require(np.isfinite(sinr).all(), 'local interface contains nonfinite SINR')
    p.require(type(tick) is int and 0 <= tick < p.HORIZON, 'invalid scored tick')
    return ids.astype(np.int64, copy=False), sinr


class RoundRobin:
    def __init__(self):
        self.cursor = 0

    def grant(self, ids, sinr, tick):
        ids, sinr = _local(ids, sinr, tick)
        needed = min(p.CAPACITY, len(ids))
        if not needed:
            return np.empty(0, np.int64)
        # Registered-ID cyclic distance, independent of input order/current quality.
        order = np.argsort((ids - self.cursor) % p.U, kind='stable')
        chosen = ids[order[:needed]].copy()
        self.cursor = (int(chosen[-1]) + 1) % p.U
        return chosen


class LeastRecentlyServed:
    def __init__(self):
        self.last_grant = np.full(p.U, -1, np.int64)

    def grant(self, ids, sinr, tick):
        ids, sinr = _local(ids, sinr, tick)
        order = np.lexsort((ids, -sinr, self.last_grant[ids]))
        chosen = ids[order[:min(p.CAPACITY, len(ids))]].copy()
        self.last_grant[chosen] = tick
        return chosen
