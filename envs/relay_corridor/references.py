"""Exact reference returns and both registered margins.

Mechanics page, "Reference policies and margins" and "Enumeration recipe":

    Enumerate a latent-aware switching oracle, one latent-aware oracle per fixed
    ``k``, all open-loop zone-role maps / fixed periods, and greedy. ...
    E3's per-region dynamic-program state is ``(theta, freshness, fixed-phase)``;
    E4 adds renewal age ``0:H``.  Open-loop enumeration is ``K^Z`` zone-role maps
    times the fixed periods plus ``never-renew``.  The two regions combine by
    agent weights.  Finite states and known transition probabilities make the
    expected returns exact -- up to declared floating arithmetic -- without
    training or Monte Carlo.

ADR 02 registers

    m      = J*_switch - J*_open
    m_dur  = J*_switch - max_k J*_k

with ``m_dur`` the E3/E4 acceptance scale and ``m`` reported only.

Implementation note.  The dynamic programme carries
``(theta, lease-fresh, plan-match, dwell age, pending-cue)`` per region and runs
the fixed phase as the explicit step index ``t`` rather than as a state
coordinate, which is exact because the phase is a deterministic function of
``t``.  ``plan-match`` records whether the offset the currently held plan
assumes equals the latent that was current when the plan was stamped; it is the
coordinate that lets the *same* programme evaluate latent-aware oracles (always
matched), open-loop maps (matched with the zone offset), and the delayed-cue
greedy policy at ``K >= 3`` (matched only when no event landed on the renewal
step).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from envs.relay_corridor.config import RelayCorridorConfig
from envs.relay_corridor.renewal import RenewalLaw

__all__ = [
    "ReferenceReport",
    "dp_service_profile",
    "enumerate_references",
    "SwitchingOracle",
    "FixedKOracle",
    "OpenLoopPlan",
    "GreedyOnPublicState",
    "rollout_reference",
]

# Stamp rules: how the plan-match coordinate is set when a lease is (re)stamped.
STAMP_ORACLE = "oracle"   # latent aware: always matched
STAMP_CUE = "cue"         # greedy at K >= 3: matched iff no event landed on this step
STAMP_OPEN = "open"       # open loop: matched iff theta equals the fixed zone offset


def dp_service_profile(
    hazard: np.ndarray,
    horizon: int,
    n_roles: int,
    *,
    boundaries: Sequence[int] = (),
    renew_on_flag: bool = False,
    renew_on_pending: bool = False,
    stamp: str = STAMP_ORACLE,
    offset: int = 0,
) -> np.ndarray:
    """Exact per-step service probability of one policy in one region.

    ``hazard[a]`` is ``P(D = a + 1 | D > a)``; the last entry is the absorbing
    age used for every larger age, which is exact whenever the hazard is
    constant from there on.

    ``boundaries`` are the *positive* fixed-``k`` renewal steps (``t = 0`` is the
    free lease installed at reset).  ``renew_on_flag`` renews on the immediate
    change flag (switching oracle, and greedy at ``K = 2``); ``renew_on_pending``
    renews one step after a flag, when the cue reveals the new latent (greedy at
    ``K >= 3``).

    Returns ``service[t]``, ``t = 0 .. H - 1``, the probability that the agent is
    ``KEEP``, fresh, and holding the right role at step ``t``.
    """
    hazard = np.asarray(hazard, dtype=np.float64)
    a_max = hazard.size - 1
    k = int(n_roles)
    horizon = int(horizon)
    boundary_set = {int(b) for b in boundaries if int(b) > 0}

    shape = (k, 2, 2, a_max + 1, 2)  # theta, fresh, match, age, pending
    flag0 = np.zeros(shape, dtype=np.float64)
    flag1 = np.zeros(shape, dtype=np.float64)
    for theta in range(k):
        match = 1 if stamp != STAMP_OPEN else int(theta == int(offset))
        flag0[theta, 1, match, 0, 0] = 1.0 / k

    service = np.zeros(horizon, dtype=np.float64)
    hazard_b = hazard[None, None, None, :, None]

    for t in range(horizon):
        post = np.zeros(shape, dtype=np.float64)
        scheduled = t in boundary_set
        for flag, incoming in ((0, flag0), (1, flag1)):
            if not incoming.any():
                continue
            for pending in (0, 1):
                block = incoming[:, :, :, :, pending]
                if not block.any():
                    continue
                renew = (
                    scheduled
                    or (renew_on_flag and flag == 1)
                    or (renew_on_pending and pending == 1)
                )
                if renew:
                    # A RENEW at t is one zero-service step; the dwell age is
                    # untouched (renewing the lease does not reset the region).
                    mass = block.sum(axis=(1, 2))  # [theta, age]
                    for theta in range(k):
                        if stamp == STAMP_ORACLE:
                            match = 1
                        elif stamp == STAMP_CUE:
                            match = 1 - flag
                        else:
                            match = int(theta == int(offset))
                        post[theta, 1, match, :, flag] += mass[theta]
                else:
                    service[t] += float(block[:, 1, 1, :].sum())
                    post[:, :, :, :, flag] += block
        if t + 1 >= horizon:
            break  # H scored steps, H - 1 transitions

        stay = post * (1.0 - hazard_b)
        go = post * hazard_b

        flag0 = np.zeros(shape, dtype=np.float64)
        flag0[:, :, :, 1:, :] += stay[:, :, :, :-1, :]
        flag0[:, :, :, a_max, :] += stay[:, :, :, a_max, :]

        flag1 = np.zeros(shape, dtype=np.float64)
        if k > 1:
            collapsed = go.sum(axis=3).sum(axis=1)  # [theta, match, pending]
            total = collapsed.sum(axis=0)           # [match, pending]
            for theta in range(k):
                flag1[theta, 0, :, 0, :] += (total - collapsed[theta]) / (k - 1)
    return service


def _policy_return(service: np.ndarray, horizon: int) -> float:
    """Undiscounted mean per-step service fraction over the episode."""
    return float(service.sum() / float(horizon))


@dataclass
class ReferenceReport:
    """Every reference return and both margins for one frozen object."""

    config: RelayCorridorConfig
    j_switch: float
    j_greedy: float
    j_fixed_k: Dict[int, float]
    best_fixed_k: int
    j_best_fixed_k: float
    j_open_best: float
    best_open_candidate: Tuple[Tuple[int, ...], Optional[int]]
    open_candidates: List[Tuple[Tuple[int, ...], Optional[int], float]] = field(repr=False, default_factory=list)
    per_region_switch: Tuple[float, ...] = ()
    per_region_fixed_k: Dict[int, Tuple[float, ...]] = field(default_factory=dict)

    @property
    def m(self) -> float:
        """``m = J*_switch - J*_open`` (registered and reported, not an E2-E4 gate)."""
        return self.j_switch - self.j_open_best

    @property
    def m_dur(self) -> float:
        """``m_dur = J*_switch - max_k J*_k`` (the E3/E4 acceptance scale)."""
        return self.j_switch - self.j_best_fixed_k

    def resolution_ok(self, sigma_delta: float, episodes: int = 4096) -> bool:
        """ADR 02 invariant 5: ``m_dur >= 3 * sigma_Delta / sqrt(E_eval)``."""
        return self.m_dur >= 3.0 * float(sigma_delta) / float(np.sqrt(episodes))

    def as_dict(self) -> Dict[str, object]:
        return {
            "J_switch": self.j_switch,
            "J_greedy": self.j_greedy,
            "J_fixed_k": dict(self.j_fixed_k),
            "best_fixed_k": self.best_fixed_k,
            "J_best_fixed_k": self.j_best_fixed_k,
            "J_open_best": self.j_open_best,
            "best_open_candidate": self.best_open_candidate,
            "open_candidate_count": len(self.open_candidates),
            "m": self.m,
            "m_dur": self.m_dur,
        }


def enumerate_references(config: RelayCorridorConfig) -> ReferenceReport:
    """Enumerate the four reference families exactly and register both margins.

    The open-loop census is ``K^Z`` zone-role maps times ``len(D0_k_set) + 1``
    periods (the fixed periods plus ``never-renew``).  For the registered
    proposal that is ``2^4 * 6 = 96`` candidates.
    """
    horizon = int(config.horizon)
    k_roles = int(config.n_roles)
    laws: Tuple[RenewalLaw, ...] = config.region_laws()
    weights = config.region_weights
    delta = float(config.delta)

    hazards = [
        law.hazard_table(min(law.dp_age_cap(horizon), horizon)) for law in laws
    ]

    # --- switching oracle ------------------------------------------------
    per_region_switch = tuple(
        _policy_return(
            dp_service_profile(
                hazards[r], horizon, k_roles, renew_on_flag=True, stamp=STAMP_ORACLE
            ),
            horizon,
        )
        for r in range(config.n_regions)
    )
    j_switch = delta * float(np.dot(weights, per_region_switch))

    # --- greedy on public state -----------------------------------------
    # At K = 2 the immediate change flag plus the old cue identify the only
    # possible new latent, so greedy renews on the flag with the right role and
    # equals the switching oracle by construction.  At K >= 3 the flag does not
    # select among the K - 1 alternatives; the next cue does, so greedy renews
    # one step later and mismatches whenever a further event lands on that step.
    if k_roles == 2:
        per_region_greedy = per_region_switch
    else:
        per_region_greedy = tuple(
            _policy_return(
                dp_service_profile(
                    hazards[r],
                    horizon,
                    k_roles,
                    renew_on_pending=True,
                    stamp=STAMP_CUE,
                ),
                horizon,
            )
            for r in range(config.n_regions)
        )
    j_greedy = delta * float(np.dot(weights, per_region_greedy))

    # --- latent-aware fixed-k oracles (the D0 arm) ------------------------
    per_region_fixed: Dict[int, Tuple[float, ...]] = {}
    j_fixed: Dict[int, float] = {}
    for k in sorted({int(x) for x in config.d0_k_set}):
        boundaries = range(k, horizon, k)
        values = tuple(
            _policy_return(
                dp_service_profile(
                    hazards[r],
                    horizon,
                    k_roles,
                    boundaries=boundaries,
                    stamp=STAMP_ORACLE,
                ),
                horizon,
            )
            for r in range(config.n_regions)
        )
        per_region_fixed[k] = values
        j_fixed[k] = delta * float(np.dot(weights, values))
    best_fixed_k = max(j_fixed, key=lambda k: j_fixed[k])

    # --- open-loop zone-role maps x fixed periods (+ never-renew) --------
    periods: List[Optional[int]] = [int(k) for k in sorted({int(x) for x in config.d0_k_set})]
    periods.append(None)  # never-renew
    open_service: Dict[Tuple[int, int, Optional[int]], float] = {}
    for region in range(config.n_regions):
        for offset in range(k_roles):
            for period in periods:
                boundaries = () if period is None else range(period, horizon, period)
                open_service[(region, offset, period)] = _policy_return(
                    dp_service_profile(
                        hazards[region],
                        horizon,
                        k_roles,
                        boundaries=boundaries,
                        stamp=STAMP_OPEN,
                        offset=offset,
                    ),
                    horizon,
                )

    region_of_agent = config.region_of_agent
    zone_of_agent = config.zone_of_agent
    candidates: List[Tuple[Tuple[int, ...], Optional[int], float]] = []
    for zone_map in product(range(k_roles), repeat=int(config.n_zones)):
        # zone q holds role zone_map[q]; it is right exactly when
        # theta_r == (zone_map[q] - q) mod K.
        offsets = [(zone_map[q] - q) % k_roles for q in range(int(config.n_zones))]
        for period in periods:
            total = 0.0
            for agent in range(int(config.n_agents)):
                region = int(region_of_agent[agent])
                offset = offsets[int(zone_of_agent[agent])]
                total += open_service[(region, offset, period)]
            candidates.append((zone_map, period, delta * total / float(config.n_agents)))
    best_map, best_period, j_open_best = max(candidates, key=lambda row: row[2])

    return ReferenceReport(
        config=config,
        j_switch=j_switch,
        j_greedy=j_greedy,
        j_fixed_k=j_fixed,
        best_fixed_k=best_fixed_k,
        j_best_fixed_k=j_fixed[best_fixed_k],
        j_open_best=j_open_best,
        best_open_candidate=(best_map, best_period),
        open_candidates=candidates,
        per_region_switch=per_region_switch,
        per_region_fixed_k=per_region_fixed,
    )


# ----------------------------------------------------------------------
# closed forms from the mechanics page (check values, never the source)
# ----------------------------------------------------------------------
def commitment_fraction(k: int, lam: float) -> float:
    """``C(k, lambda) = (1 - (1 - lambda)^k) / (k * lambda)``."""
    if lam == 0.0:
        return 1.0
    return (1.0 - (1.0 - lam) ** int(k)) / (int(k) * lam)


def closed_form_j_switch(config: RelayCorridorConfig) -> float:
    """``J_sw = Delta * sum_r w_r * (1 + (H - 1)(1 - lambda_r)) / H``."""
    h = float(config.horizon)
    weights = config.region_weights
    terms = [
        (1.0 + (h - 1.0) * (1.0 - float(lam))) / h for lam in config.lambda_regions
    ]
    return float(config.delta) * float(np.dot(weights, terms))


def closed_form_j_fixed_k(config: RelayCorridorConfig, k: int) -> float:
    """``J_k = Delta * sum_r w_r * [C(k, lambda_r) - 1/k + 1/H]``."""
    h = float(config.horizon)
    weights = config.region_weights
    terms = [
        commitment_fraction(k, float(lam)) - 1.0 / float(k) + 1.0 / h
        for lam in config.lambda_regions
    ]
    return float(config.delta) * float(np.dot(weights, terms))


# ----------------------------------------------------------------------
# scripted reference policies, run against the host itself
# ----------------------------------------------------------------------
# These make the enumeration falsifiable: the same four reference families are
# driven through the vectorized host, and their realised returns must agree with
# the dynamic programme.  With the deterministic dwell law and a latent-aware
# policy the realised return carries no randomness at all, so the agreement is
# exact rather than statistical.  They also produce the matched reference tapes
# from which sigma_Delta is measured (ADR 02 invariant 5).


class _ScriptedPolicy:
    """Common shape: ``act(host, t) -> (roles [B, N], renew [B, N])``."""

    name = "policy"
    latent_aware = False

    def reset(self, host) -> None:
        self.plan = host.target_roles() if self.latent_aware else None

    def act(self, host, t: int):  # pragma: no cover - overridden
        raise NotImplementedError


class SwitchingOracle(_ScriptedPolicy):
    """Latent aware; renews on the immediate change flag with the right role."""

    name = "switching_oracle"
    latent_aware = True

    def act(self, host, t: int):
        flag = host.change_flag[:, host.region_of_agent].astype(bool)
        target = host.target_roles()
        if t == 0:
            self.plan = target
            return self.plan, np.zeros_like(flag)
        self.plan = np.where(flag, target, self.plan)
        return self.plan, flag


class FixedKOracle(_ScriptedPolicy):
    """Latent aware at fixed boundaries only: the D0 arm (``c = c_Z = inf``)."""

    latent_aware = True

    def __init__(self, k: int) -> None:
        self.k = int(k)
        self.name = f"fixed_k_{self.k}"

    def act(self, host, t: int):
        boundary = t > 0 and (t % self.k == 0)
        renew = np.full((host.batch_size, host.n_agents), bool(boundary))
        if t == 0 or boundary:
            self.plan = host.target_roles()
        return self.plan, renew


class OpenLoopPlan(_ScriptedPolicy):
    """A fixed zone-role map renewed on a fixed period (or never renewed)."""

    latent_aware = False

    def __init__(self, zone_map: Sequence[int], period: Optional[int]) -> None:
        self.zone_map = tuple(int(x) for x in zone_map)
        self.period = None if period is None else int(period)
        self.name = f"open_loop_{self.zone_map}_{self.period}"

    def reset(self, host) -> None:
        roles = np.asarray([self.zone_map[z] for z in host.zone_of_agent], dtype=np.int64)
        self.plan = np.broadcast_to(roles, (host.batch_size, host.n_agents)).copy()

    def act(self, host, t: int):
        boundary = self.period is not None and t > 0 and (t % self.period == 0)
        renew = np.full((host.batch_size, host.n_agents), bool(boundary))
        return self.plan, renew


class GreedyOnPublicState(_ScriptedPolicy):
    """Greedy on the public state only: change flag, lagged cue, identities.

    At ``K = 2`` a switch must choose the only different latent, so the flag plus
    ``y_{r,t}`` identifies the new latent and this policy renews at the same step
    as the switching oracle with the same role; ADR 02 invariant 8 asserts the
    resulting ``J_greedy = J_sw`` equality.  At ``K >= 3`` the flag does not
    select among the ``K - 1`` alternatives, so this policy waits one step for
    the cue to carry the new latent.
    """

    name = "greedy"
    latent_aware = False

    def reset(self, host) -> None:
        self.plan = (
            host.zone_of_agent[None, :] + host.cue[:, host.region_of_agent]
        ) % host.n_roles
        self.pending = np.zeros((host.batch_size, host.n_agents), dtype=bool)

    def act(self, host, t: int):
        flag = host.change_flag[:, host.region_of_agent].astype(bool)
        cue = host.cue[:, host.region_of_agent]
        if host.n_roles == 2:
            renew = flag if t > 0 else np.zeros_like(flag)
            inferred = (1 - cue) % host.n_roles  # the only different latent
        else:
            renew = self.pending.copy()
            inferred = cue  # the cue now carries theta_{t-1}
        candidate = (host.zone_of_agent[None, :] + inferred) % host.n_roles
        self.plan = np.where(renew, candidate, self.plan)
        self.pending = flag
        return self.plan, renew


def rollout_reference(host, policy: _ScriptedPolicy) -> Dict[str, object]:
    """Run one reference policy over a full episode of the vectorized host.

    Returns per-lane mean returns plus the per-step tapes ADR 02's metrics list
    requires (renew masks, per-agent service indicators, cue and change timing).
    """
    host.reset()
    policy.reset(host)
    horizon = host.horizon
    rewards = np.zeros((horizon, host.batch_size), dtype=np.float64)
    service = np.zeros((horizon, host.batch_size, host.n_agents), dtype=bool)
    renews = np.zeros((horizon, host.batch_size, host.n_agents), dtype=bool)
    flags = np.zeros((horizon, host.batch_size, host.n_regions), dtype=np.int64)
    cues = np.zeros((horizon, host.batch_size, host.n_regions), dtype=np.int64)
    for t in range(horizon):
        roles, renew = policy.act(host, t)
        _obs, reward, _terminated, info = host.step(roles, renew, build_obs=False)
        rewards[t] = reward
        service[t] = info["service_indicators"]
        renews[t] = info["renew_mask"]
        flags[t] = info["change_flag"]
        cues[t] = info["cue"]
    return {
        "policy": policy.name,
        "mean_return": rewards.mean(axis=0),
        "rewards": rewards,
        "service_indicators": service,
        "renew_masks": renews,
        "change_flags": flags,
        "cues": cues,
    }
