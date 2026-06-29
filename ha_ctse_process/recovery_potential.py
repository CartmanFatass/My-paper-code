"""P2-lite recovery-window contribution credit.

This module implements a SOFT, position-based per-agent recovery potential
``phi_i_recovery(s)`` and the signed high-level shaping it induces.  It is the
active P2 mechanism (see ``ALGORITHM_PRINCIPLES.md`` -> ``P2-lite: Recovery-Window
Contribution Credit``).

Design contract (do not silently break):

1. The potential is computed from positions / distances / soft edge weights, NOT
   from binary connectivity.  It must change while a UAV is still disconnected but
   approaching a bridging position, otherwise the reward is as sparse as the env
   reward in exactly the regime that matters.
2. Compute-gating != reward-gating.  Exact leave-one-out counterfactuals (CF) are
   a diagnostic/audit only; the main reward is the cheap soft potential.
3. High-level shaping is SIGNED and telescopes (``gamma^dt Phi(s') - Phi(s)``).
   ``positive_only`` is allowed only as a low-level ablation.
4. ``W_recovery(s)`` is a smooth STATE weight folded into the potential, never an
   external ``if not window: reward = 0`` gate.

Everything here is pure NumPy and side-effect free so it can be unit-smoke-tested
and run cheaply inside the training update.  All behaviour is OFF by default; the
caller decides whether to compute and whether to inject reward.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecoveryPotentialConfig:
    """Parameters for the soft recovery potential.

    Ranges are expressed as a fraction of the environment ``area_size`` so the
    potential is scale-aware without hard-coding meters.
    """

    comm_range_frac: float = 0.25      # UAV-UAV soft link range / area_size
    bs_range_frac: float = 0.30        # UAV-BS soft link range / area_size
    soft_temp_frac: float = 0.08       # sigmoid temperature / area_size (connectivity)
    approach_scale_frac: float = 0.5   # exp closeness scale / area_size (gradient)
    w_bs_approach: float = 0.34        # weight on proximity to connected frontier
    w_bridge: float = 0.5              # weight on bridging two components
    w_disc_approach: float = 0.16      # weight on proximity to a needy node
    lambda_rec: float = 1.0            # weight of recovery term inside Phi_total
    bh_threshold: float = 0.6          # W_recovery centre (credit_bh_frac)
    w_recovery_temp: float = 0.15      # W_recovery sigmoid temperature
    gamma: float = 0.99               # discount used in F = gamma^dt Phi' - Phi
    default_area_size: float = 1000.0  # fallback when area_size missing

    @classmethod
    def from_config(cls, config: Any) -> "RecoveryPotentialConfig":
        def g(name: str, default: float) -> float:
            return float(getattr(config, name, default))

        return cls(
            comm_range_frac=g("p2_comm_range_frac", cls.comm_range_frac),
            bs_range_frac=g("p2_bs_range_frac", cls.bs_range_frac),
            soft_temp_frac=g("p2_soft_temp_frac", cls.soft_temp_frac),
            approach_scale_frac=g("p2_approach_scale_frac", cls.approach_scale_frac),
            w_bs_approach=g("p2_w_bs_approach", cls.w_bs_approach),
            w_bridge=g("p2_w_bridge", cls.w_bridge),
            w_disc_approach=g("p2_w_disc_approach", cls.w_disc_approach),
            lambda_rec=g("p2_lambda_rec", cls.lambda_rec),
            bh_threshold=g("p2_bh_threshold", cls.bh_threshold),
            w_recovery_temp=g("p2_w_recovery_temp", cls.w_recovery_temp),
            gamma=g("gamma", cls.gamma),
            default_area_size=g("p2_default_area_size", cls.default_area_size),
        )


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -40.0, 40.0)))


def _as_xy(value) -> np.ndarray | None:
    """Return an (N, d>=2) float array of positions, or None."""
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] < 2:
        return None
    return arr[:, :2]  # planar distance is sufficient for the soft potential


def _pairwise_dist(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Euclidean distances between rows of a (M,2) and b (N,2) -> (M,N)."""
    if a.size == 0 or b.size == 0:
        return np.zeros((a.shape[0], b.shape[0]), dtype=np.float64)
    diff = a[:, None, :] - b[None, :, :]
    return np.sqrt(np.maximum(np.sum(diff * diff, axis=-1), 0.0))


# ---------------------------------------------------------------------------
# Core computer
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PotentialResult:
    available: bool
    phi_i: np.ndarray            # (n_agents,) per-agent soft recovery potential
    phi_sum: float               # sum_i phi_i
    w_recovery: float            # smooth state window weight in [0, 1]
    connected_frac: float        # fraction of UAVs reachable from a BS
    bh_frac: float               # backhaul fraction used by W_recovery


class RecoveryPotentialComputer:
    """Compute soft per-agent recovery potential from a ``state_info`` dict."""

    def __init__(self, n_agents: int, cfg: RecoveryPotentialConfig):
        self.n_agents = int(max(n_agents, 1))
        self.cfg = cfg

    # -- helpers ----------------------------------------------------------

    def _ranges(self, area_size: float) -> tuple[float, float, float, float]:
        area = float(area_size) if area_size and area_size > 0 else self.cfg.default_area_size
        r_comm = self.cfg.comm_range_frac * area
        r_bs = self.cfg.bs_range_frac * area
        temp = max(self.cfg.soft_temp_frac * area, 1e-6)
        approach_scale = max(self.cfg.approach_scale_frac * area, 1e-6)
        return r_comm, r_bs, temp, approach_scale

    def _connected_set(
        self,
        uav_xy: np.ndarray,
        bs_xy: np.ndarray,
        state_info: dict,
        r_comm: float,
        r_bs: float,
    ) -> np.ndarray:
        """Boolean mask of UAVs reachable from any BS.

        Prefer the env's connection matrices; fall back to a hard threshold on the
        soft edges when they are absent.
        """
        n = uav_xy.shape[0]
        uav_conn = state_info.get("uav_connections")
        uav_bs_conn = state_info.get("uav_bs_connections")
        try:
            uav_adj = np.asarray(uav_conn, dtype=bool)
            bs_adj = np.asarray(uav_bs_conn, dtype=bool)
            ok = uav_adj.ndim == 2 and bs_adj.ndim == 2 and uav_adj.shape[0] >= n
        except (TypeError, ValueError):
            ok = False
        if not ok:
            # Derive binary edges from geometry.
            uav_adj = _pairwise_dist(uav_xy, uav_xy) <= r_comm
            if bs_xy.shape[0] > 0:
                bs_adj = _pairwise_dist(uav_xy, bs_xy) <= r_bs
            else:
                bs_adj = np.zeros((n, 0), dtype=bool)
        uav_adj = np.asarray(uav_adj)[:n, :n].astype(bool)
        bs_adj = np.asarray(bs_adj)
        if bs_adj.ndim != 2 or bs_adj.shape[0] < n:
            bs_adj = np.zeros((n, max(bs_adj.shape[1] if bs_adj.ndim == 2 else 1, 1)), dtype=bool)
        bs_adj = bs_adj[:n]

        connected = bs_adj.any(axis=1)  # directly linked to a BS
        # BFS over UAV-UAV edges from the directly-connected seed set.
        frontier = list(np.flatnonzero(connected))
        seen = set(frontier)
        while frontier:
            node = frontier.pop()
            for nb in np.flatnonzero(uav_adj[node]):
                nb = int(nb)
                if nb not in seen:
                    seen.add(nb)
                    connected[nb] = True
                    frontier.append(nb)
        return connected

    # -- main -------------------------------------------------------------

    def phi(self, state_info: dict | None) -> PotentialResult:
        zero = np.zeros(self.n_agents, dtype=np.float64)
        if not isinstance(state_info, dict) or not state_info:
            return PotentialResult(False, zero, 0.0, 0.0, 0.0, 0.0)
        uav_xy = _as_xy(state_info.get("uav_positions"))
        if uav_xy is None:
            return PotentialResult(False, zero, 0.0, 0.0, 0.0, 0.0)
        n = min(uav_xy.shape[0], self.n_agents)
        uav_xy = uav_xy[:n]
        bs_xy = _as_xy(state_info.get("ground_bs_positions"))
        if bs_xy is None:
            bs_xy = np.zeros((0, 2), dtype=np.float64)
        user_xy = _as_xy(state_info.get("user_positions"))

        area_size = state_info.get("area_size")
        if isinstance(area_size, (list, tuple, np.ndarray)):
            area_size = float(np.asarray(area_size, dtype=np.float64).reshape(-1)[0])
        r_comm, r_bs, temp, scale = self._ranges(area_size)

        connected = self._connected_set(uav_xy, bs_xy, state_info, r_comm, r_bs)
        connected_frac = float(connected.mean()) if n > 0 else 0.0

        # Smooth closeness in (0, 1]: exp(-d / scale).  Unlike a saturating
        # sigmoid soft-edge this has a non-zero gradient across the WHOLE area, so
        # a bridge UAV in a gap larger than the comm range still gets signal.
        def closeness(d: np.ndarray) -> np.ndarray:
            return np.exp(-np.maximum(d, 0.0) / scale)

        d_uav = _pairwise_dist(uav_xy, uav_xy)
        np.fill_diagonal(d_uav, np.inf)  # exclude self
        c_uav = closeness(d_uav)          # (n, n)
        d_bs = _pairwise_dist(uav_xy, bs_xy) if bs_xy.shape[0] > 0 else None
        c_bs = closeness(d_bs) if d_bs is not None else None

        # bs_approach_i: closeness to the nearest BS-connected anchor (a BS node or
        # another already-connected UAV).  Connected agents sit at the anchor -> ~1.
        anchor_close = np.zeros((n, 0), dtype=np.float64)
        if c_bs is not None:
            anchor_close = np.concatenate([anchor_close, c_bs], axis=1)
        if connected.any():
            conn_cols = c_uav[:, connected]  # closeness to connected UAVs (self=inf)
            anchor_close = np.concatenate([anchor_close, conn_cols], axis=1)
        bs_approach = anchor_close.max(axis=1) if anchor_close.shape[1] else np.zeros(n)

        # disc_approach_i: closeness to the nearest needy node (disconnected UAV or
        # an unserved user cluster).
        needy_close = np.zeros((n, 0), dtype=np.float64)
        if (~connected).any():
            needy_close = np.concatenate([needy_close, c_uav[:, ~connected]], axis=1)
        if user_xy is not None and user_xy.shape[0] > 0:
            needy_close = np.concatenate([needy_close, closeness(_pairwise_dist(uav_xy, user_xy))], axis=1)
        disc_approach = needy_close.max(axis=1) if needy_close.shape[1] else np.zeros(n)

        # Bridge potential: high only when near BOTH sides (product = soft AND).
        bridge = bs_approach * disc_approach

        phi_i = (
            self.cfg.w_bs_approach * bs_approach
            + self.cfg.w_bridge * bridge
            + self.cfg.w_disc_approach * disc_approach
        )
        phi_full = np.zeros(self.n_agents, dtype=np.float64)
        phi_full[:n] = phi_i

        bh_frac = self._backhaul_fraction(state_info, connected_frac)
        w_rec = float(_sigmoid(np.array((self.cfg.bh_threshold - bh_frac) / max(self.cfg.w_recovery_temp, 1e-6))))
        return PotentialResult(
            available=True,
            phi_i=phi_full,
            phi_sum=float(phi_full.sum()),
            w_recovery=w_rec,
            connected_frac=connected_frac,
            bh_frac=float(bh_frac),
        )

    @staticmethod
    def _backhaul_fraction(state_info: dict, connected_frac: float) -> float:
        for key in ("credit_bh_frac", "backhaul_connected_step_fraction", "bh_frac"):
            val = state_info.get(key)
            if val is not None:
                try:
                    return float(np.asarray(val, dtype=np.float64).reshape(-1)[0])
                except (TypeError, ValueError):
                    pass
        return float(connected_frac)


# ---------------------------------------------------------------------------
# Segment-level signed shaping
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SegmentShaping:
    available: bool
    f_team: float                 # signed team shaping gamma^dt Phi_total' - Phi_total
    f_i: np.ndarray               # (n_agents,) per-agent signed shaping
    phi_start: PotentialResult
    phi_end: PotentialResult
    base_start: float
    base_end: float
    delta_phi_sum: float          # phi_sum_end - phi_sum_start (unweighted, raw)
    full_disconnect_start: bool
    near_disconnect: bool


def _base_potential(state_info: dict | None, reward_info: dict | None) -> float:
    """P1-style global service/topology potential, from populated fields.

    Bounded combination of backhaul fraction / served users / coverage minus
    disconnect penalty.  Missing fields contribute zero.
    """
    if not isinstance(reward_info, dict):
        reward_info = {}
    si = state_info if isinstance(state_info, dict) else {}

    def pick(*keys, default=0.0):
        for src in (reward_info, si):
            for k in keys:
                if k in src:
                    try:
                        return float(np.asarray(src[k], dtype=np.float64).reshape(-1)[0])
                    except (TypeError, ValueError):
                        continue
        return float(default)

    bh_frac = pick("credit_bh_frac", "backhaul_connected_step_fraction", "bh_frac")
    coverage = pick("coverage_ratio")
    qos = pick("qos_satisfaction_ratio", "qos_met_fraction")
    full_disc = pick("full_network_disconnect", "full_disconnect", "network_disconnected")
    return 0.5 * bh_frac + 0.25 * coverage + 0.25 * qos - 0.5 * full_disc


def compute_segment_shaping(
    segment: Any,
    computer: RecoveryPotentialComputer,
    cfg: RecoveryPotentialConfig,
    *,
    near_disconnect_bh_frac: float = 0.4,
) -> SegmentShaping:
    """Signed potential shaping between the segment's first and last states."""
    n_agents = computer.n_agents
    zero_i = np.zeros(n_agents, dtype=np.float64)
    states = [s for s in getattr(segment, "state_info_seq", []) if isinstance(s, dict) and s]
    rewards_info = [r for r in getattr(segment, "reward_info_seq", []) if isinstance(r, dict)]
    # Prefer the true segment-start state (captured before the first action) over the
    # post-first-step state so the recovery shaping spans the real window.
    start_si = getattr(segment, "start_state_info", None)
    if isinstance(start_si, dict) and start_si:
        start_ri = getattr(segment, "start_reward_info", None)
        states = [start_si] + states
        rewards_info = [start_ri if isinstance(start_ri, dict) else {}] + rewards_info
    if len(states) < 2:
        empty = PotentialResult(False, zero_i, 0.0, 0.0, 0.0, 0.0)
        return SegmentShaping(False, 0.0, zero_i, empty, empty, 0.0, 0.0, 0.0, False, False)

    s0, s1 = states[0], states[-1]
    r0 = rewards_info[0] if rewards_info else {}
    r1 = rewards_info[-1] if rewards_info else {}

    p0 = computer.phi(s0)
    p1 = computer.phi(s1)
    base0 = _base_potential(s0, r0)
    base1 = _base_potential(s1, r1)

    lam = cfg.lambda_rec
    phi_total0 = base0 + lam * p0.w_recovery * p0.phi_sum
    phi_total1 = base1 + lam * p1.w_recovery * p1.phi_sum

    dt = max(float(getattr(segment, "length", 1)), 1.0)
    disc = float(cfg.gamma) ** dt
    f_team = disc * phi_total1 - phi_total0

    # Per-agent signed shaping on the windowed per-agent potential.
    wphi0 = lam * p0.w_recovery * p0.phi_i
    wphi1 = lam * p1.w_recovery * p1.phi_i
    f_i = disc * wphi1 - wphi0

    full_disc_start = p0.bh_frac <= 1e-6
    near_disc = p0.bh_frac < float(near_disconnect_bh_frac)

    return SegmentShaping(
        available=bool(p0.available and p1.available),
        f_team=float(f_team),
        f_i=f_i.astype(np.float64),
        phi_start=p0,
        phi_end=p1,
        base_start=float(base0),
        base_end=float(base1),
        delta_phi_sum=float(p1.phi_sum - p0.phi_sum),
        full_disconnect_start=bool(full_disc_start),
        near_disconnect=bool(near_disc),
    )


# ---------------------------------------------------------------------------
# Diagnostics (Pre-check 2 + CF audit)
# ---------------------------------------------------------------------------


def empty_p2_metrics() -> dict[str, float]:
    keys = (
        "p2_available_frac",
        "p2_window_frac",
        "p2_phi_sum_mean",
        "p2_f_team_mean",
        "p2_f_team_std",
        "p2_f_team_p95",
        "p2_w_recovery_mean",
        "p2_connected_frac_mean",
        "p2_credit_mean",
        "p2_credit_std",
        "p2_credit_p95",
        "p2_credit_by_disconnect_state",
        "p2_credit_by_recovery_event",
        "delta_phi_soft_nonzero_rate_when_full_disconnect",
        "delta_phi_soft_nonzero_rate_when_near_disconnect",
        "p2_corr_phi_recovery_event",
        # Continuous / partial-recovery diagnostics: full reconnection within one
        # short segment is too sparse for a correlation, so also track whether the
        # credit tracks the CONTINUOUS backhaul improvement (delta_bh_frac).  These
        # are informational (not a hard gate); thresholds are fixed a priori.
        "p2_delta_bh_frac_mean",
        "p2_partial_recovery_frac",
        "p2_corr_credit_delta_bh_frac",
        "p2_credit_by_partial_recovery_event",
        "p2_cf_corr",
        "p2_cf_nonzero_rate",
        "p2_segments",
    )
    return {k: 0.0 for k in keys}


def aggregate_p2_metrics(
    shapings: list[SegmentShaping],
    *,
    owner_credit: list[float] | None = None,
    recovery_flags: list[float] | None = None,
    cf_backhaul: list[float] | None = None,
    nonzero_eps: float = 1e-6,
    partial_start_bh: float = 0.4,
    partial_delta_bh: float = 0.1,
) -> dict[str, float]:
    """Aggregate per-segment shapings into Pre-check 2 / audit diagnostics.

    ``recovery_flags[k]`` should be 1.0 if segment k ended in a backhaul recovery
    (started disconnected, ended connected); ``cf_backhaul[k]`` is the exact
    leave-one-out backhaul contribution of the segment's agent, used only to audit
    whether the soft potential tracks real contribution.

    A *partial* recovery event (``start_bh_frac < partial_start_bh`` and
    ``delta_bh_frac >= partial_delta_bh``) is the continuous counterpart of the
    sparse full-reconnection flag: it fires far more often, so the correlation
    between credit and backhaul improvement (``p2_corr_credit_delta_bh_frac``) is
    observable rather than event-starved.  Thresholds are fixed a priori.
    """
    metrics = empty_p2_metrics()
    valid = [s for s in shapings if s.available]
    metrics["p2_segments"] = float(len(shapings))
    if not valid:
        return metrics

    f_team = np.array([s.f_team for s in valid], dtype=np.float64)
    phi_sum = np.array([s.phi_start.phi_sum for s in valid], dtype=np.float64)
    w_rec = np.array([s.phi_start.w_recovery for s in valid], dtype=np.float64)
    conn = np.array([s.phi_start.connected_frac for s in valid], dtype=np.float64)
    # Segment credit signal: the owning-agent per-agent shaping if the caller
    # supplied owner_credit, else the team signal.  (The aggregator has no segment
    # handle, so per-owner attribution is the caller's responsibility.)
    if owner_credit is not None and len(owner_credit) == len(valid):
        credit = np.array(owner_credit, dtype=np.float64)
    else:
        credit = f_team

    metrics["p2_available_frac"] = float(len(valid) / max(len(shapings), 1))
    metrics["p2_window_frac"] = float(np.mean([s.near_disconnect for s in valid]))
    metrics["p2_phi_sum_mean"] = float(phi_sum.mean())
    metrics["p2_f_team_mean"] = float(f_team.mean())
    metrics["p2_f_team_std"] = float(f_team.std())
    metrics["p2_f_team_p95"] = float(np.percentile(f_team, 95))
    metrics["p2_w_recovery_mean"] = float(w_rec.mean())
    metrics["p2_connected_frac_mean"] = float(conn.mean())
    metrics["p2_credit_mean"] = float(credit.mean())
    metrics["p2_credit_std"] = float(credit.std())
    metrics["p2_credit_p95"] = float(np.percentile(credit, 95))

    full_mask = np.array([s.full_disconnect_start for s in valid], dtype=bool)
    near_mask = np.array([s.near_disconnect for s in valid], dtype=bool)
    dphi = np.array([abs(s.delta_phi_sum) for s in valid], dtype=np.float64)
    if full_mask.any():
        metrics["delta_phi_soft_nonzero_rate_when_full_disconnect"] = float(
            (dphi[full_mask] > nonzero_eps).mean()
        )
    if near_mask.any():
        metrics["delta_phi_soft_nonzero_rate_when_near_disconnect"] = float(
            (dphi[near_mask] > nonzero_eps).mean()
        )

    disc_state = np.array([1.0 if s.full_disconnect_start else 0.0 for s in valid])
    metrics["p2_credit_by_disconnect_state"] = float(credit[disc_state > 0].mean()) if (disc_state > 0).any() else 0.0

    # Continuous / partial-recovery diagnostics (not event-starved): does the
    # assigned credit move together with the actual backhaul improvement?
    bh0 = np.array([s.phi_start.bh_frac for s in valid], dtype=np.float64)
    bh1 = np.array([s.phi_end.bh_frac for s in valid], dtype=np.float64)
    delta_bh = bh1 - bh0
    metrics["p2_delta_bh_frac_mean"] = float(delta_bh.mean())
    partial_mask = (bh0 < partial_start_bh) & (delta_bh >= partial_delta_bh)
    metrics["p2_partial_recovery_frac"] = float(partial_mask.mean())
    metrics["p2_corr_credit_delta_bh_frac"] = _safe_corr(credit, delta_bh)
    metrics["p2_credit_by_partial_recovery_event"] = (
        float(credit[partial_mask].mean()) if partial_mask.any() else 0.0
    )

    if recovery_flags is not None and len(recovery_flags) == len(valid):
        rec = np.array(recovery_flags, dtype=np.float64)
        metrics["p2_credit_by_recovery_event"] = float(credit[rec > 0].mean()) if (rec > 0).any() else 0.0
        metrics["p2_corr_phi_recovery_event"] = _safe_corr(phi_sum, rec)
    if cf_backhaul is not None and len(cf_backhaul) == len(valid):
        cf = np.array(cf_backhaul, dtype=np.float64)
        metrics["p2_cf_corr"] = _safe_corr(credit, cf)
        metrics["p2_cf_nonzero_rate"] = float((np.abs(cf) > nonzero_eps).mean())
    return metrics


def _safe_corr(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size < 3 or y.size < 3 or x.std() < 1e-9 or y.std() < 1e-9:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])
