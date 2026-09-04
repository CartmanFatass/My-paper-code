"""Relay corridor configuration, exactly as ADR 02 "Parameters" names it.

``N, K, Z, H: positive int``, fixed within an object; first-object ``K = 2``,
registered family point ``K = 3``; ``n_z = K``; ``low_level_action_dim = K``;
``role_decode = argmax``; ``rho = 0``; ``Delta: float in (0, 1]``;
``lambda_regions: pair in [0, 1]^2``; ``D0_k_set: positive-int set``;
``renewal_law in {deterministic, geometric, lognormal}``;
``renewal_mean, lognormal_shape > 0``; ``c_probe = 0``, ``v`` inactive;
``e5_coupling_enabled = false``.  ``time_homogeneous`` is deliberately absent:
renewal age is explicit state and the service mechanics are time-homogeneous.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from envs.relay_corridor.renewal import BernoulliHazard, RenewalLaw, make_renewal_law

__all__ = [
    "RelayCorridorConfig",
    "HorizonValidationError",
    "PROPOSAL_GRID",
    "proposal_config",
    "validate_horizon",
    "rows_per_rollout",
]


class HorizonValidationError(ValueError):
    """Raised when ADR 02 invariant 6 rejects a fixed-``k`` D0 configuration."""


@dataclass(frozen=True)
class RelayCorridorConfig:
    """One frozen relay corridor object."""

    # --- entities -------------------------------------------------------
    n_agents: int = 6           # N
    n_roles: int = 2            # K, first object K = 2
    n_zones: int = 4            # Z
    n_regions: int = 2          # fixed at two by the mechanics page
    horizon: int = 400          # H

    # --- reward ---------------------------------------------------------
    delta: float = 0.4          # Delta in (0, 1]

    # --- event process --------------------------------------------------
    event_process: str = "bernoulli"        # 'bernoulli' (E3) | 'renewal' (E4)
    lambda_regions: Tuple[float, ...] = (0.005, 0.02)
    renewal_law: str = "deterministic"
    renewal_mean: float = 20.0
    lognormal_shape: float = 1.0

    # --- structure cut / D0 --------------------------------------------
    d0_k_set: Tuple[int, ...] = (1, 2, 5, 20, 40)

    # --- fixed-off / inactive knobs ------------------------------------
    rho: float = 0.0
    c_probe: float = 0.0
    e5_coupling_enabled: bool = False

    # --- adapter surface ------------------------------------------------
    role_decode: str = "argmax"

    def __post_init__(self) -> None:
        for name in ("n_agents", "n_roles", "n_zones", "n_regions", "horizon"):
            value = getattr(self, name)
            if not isinstance(value, (int, np.integer)) or int(value) < 1:
                raise ValueError(f"{name} must be a positive int, got {value!r}")
        # Invariant 3: every positive N is valid; there is no N mod K rule.
        if int(self.n_roles) < 2:
            raise ValueError("n_roles (K) must be at least 2: a switch draws a *different* theta")
        if self.n_zones < self.n_regions:
            raise ValueError("n_zones must be at least n_regions (each region owns a zone)")
        if not (0.0 < float(self.delta) <= 1.0):
            raise ValueError(f"delta must lie in (0, 1], got {self.delta!r}")
        if self.event_process not in ("bernoulli", "renewal"):
            raise ValueError(f"event_process must be bernoulli|renewal, got {self.event_process!r}")
        if self.event_process == "bernoulli":
            if len(self.lambda_regions) != self.n_regions:
                raise ValueError("lambda_regions must have one rate per region")
            for lam in self.lambda_regions:
                if not (0.0 <= float(lam) <= 1.0):
                    raise ValueError(f"lambda_regions entries must lie in [0, 1], got {lam!r}")
        if any(int(k) < 1 for k in self.d0_k_set):
            raise ValueError("d0_k_set entries must be positive ints")
        if float(self.rho) != 0.0:
            raise ValueError("E2-E4 fix the churn rate rho = 0")
        if float(self.c_probe) != 0.0:
            raise ValueError("E2-E4 fix c_probe = 0; the probe action does not exist here")
        if self.e5_coupling_enabled:
            raise NotImplementedError(
                "The E5 agent-coupling rule is deliberately deferred (review IV.8.1 decision 3); "
                "only its default-off switch and reserved zero state field are fixed."
            )
        if self.role_decode != "argmax":
            raise ValueError("role_decode is fixed to 'argmax' by ADR 02")

    # --- derived, ADR 02 "Parameters" aliases ---------------------------
    @property
    def n_z(self) -> int:
        """HMASD skill-space size; ADR 02 fixes ``n_z = K``."""
        return int(self.n_roles)

    @property
    def low_level_action_dim(self) -> int:
        return int(self.n_roles)

    @property
    def region_of_zone(self) -> np.ndarray:
        """Contiguous zone -> region map (zones are ordered along the corridor)."""
        sizes = _balanced_sizes(self.n_zones, self.n_regions)
        return np.repeat(np.arange(self.n_regions, dtype=np.int64), sizes)

    @property
    def region_of_agent(self) -> np.ndarray:
        """Agents are pinned to a region at reset and never move (invariant 4)."""
        sizes = _balanced_sizes(self.n_agents, self.n_regions)
        return np.repeat(np.arange(self.n_regions, dtype=np.int64), sizes)

    @property
    def zone_of_agent(self) -> np.ndarray:
        """Agents are pinned to a zone inside their region, round robin."""
        region_of_zone = self.region_of_zone
        region_of_agent = self.region_of_agent
        zones = np.empty(self.n_agents, dtype=np.int64)
        for region in range(self.n_regions):
            zone_ids = np.flatnonzero(region_of_zone == region)
            agent_ids = np.flatnonzero(region_of_agent == region)
            if zone_ids.size == 0 and agent_ids.size:
                raise ValueError(f"region {region} has agents but no zone")
            for slot, agent in enumerate(agent_ids):
                zones[agent] = zone_ids[slot % zone_ids.size]
        return zones

    @property
    def region_weights(self) -> np.ndarray:
        """``w_r = N_r / N`` used to combine the two per-region references."""
        counts = np.bincount(self.region_of_agent, minlength=self.n_regions)
        return counts.astype(np.float64) / float(self.n_agents)

    def region_laws(self) -> Tuple[RenewalLaw, ...]:
        """One event-process law per region."""
        if self.event_process == "bernoulli":
            return tuple(
                BernoulliHazard(name="bernoulli", lam=float(lam))
                for lam in self.lambda_regions
            )
        law = make_renewal_law(self.renewal_law, self.renewal_mean, self.lognormal_shape)
        return tuple(law for _ in range(self.n_regions))

    def parameter_record(self) -> Dict[str, object]:
        """The ADR 02 "Parameters" block, for the manifest / metrics line."""
        return {
            "N": int(self.n_agents),
            "K": int(self.n_roles),
            "Z": int(self.n_zones),
            "H": int(self.horizon),
            "n_z": self.n_z,
            "low_level_action_dim": self.low_level_action_dim,
            "role_decode": self.role_decode,
            "rho": float(self.rho),
            "Delta": float(self.delta),
            "event_process": self.event_process,
            "lambda_regions": tuple(float(x) for x in self.lambda_regions),
            "D0_k_set": tuple(int(k) for k in self.d0_k_set),
            "renewal_law": self.renewal_law,
            "renewal_mean": float(self.renewal_mean),
            "lognormal_shape": float(self.lognormal_shape),
            "c_probe": float(self.c_probe),
            "v_active": False,
            "e5_coupling_enabled": bool(self.e5_coupling_enabled),
        }


def _balanced_sizes(total: int, parts: int) -> np.ndarray:
    base, extra = divmod(int(total), int(parts))
    sizes = np.full(int(parts), base, dtype=np.int64)
    sizes[:extra] += 1
    return sizes


#: The three unchanged proposal rows of the mechanics page margin table.
#: ``level -> (lambda_1, lambda_2, Delta, m, m_dur, best fixed k)``
PROPOSAL_GRID: Dict[str, Dict[str, object]] = {
    "small": {
        "lambda_regions": (0.005, 0.02),
        "delta": 0.4,
        "m": 0.226025,
        "m_dur": 0.057037,
        "best_k": 20,
    },
    "medium": {
        "lambda_regions": (0.005, 0.10),
        "delta": 0.6,
        "m": 0.356468,
        "m_dur": 0.144358,
        "best_k": 5,
    },
    "large": {
        "lambda_regions": (0.02, 0.20),
        "delta": 1.0,
        "m": 0.580747,
        "m_dur": 0.271219,
        "best_k": 5,
    },
}


def proposal_config(level: str, **overrides) -> RelayCorridorConfig:
    """Build the E3 proposal object for ``level in {small, medium, large}``.

    Proposed grid: ``N = 6`` (three agents per region), ``K = 2``, ``Z = 4``,
    ``H = 400``, D0 ``k in {1, 2, 5, 20, 40}``.
    """
    row = PROPOSAL_GRID[level]
    kwargs = dict(
        n_agents=6,
        n_roles=2,
        n_zones=4,
        n_regions=2,
        horizon=400,
        delta=float(row["delta"]),
        event_process="bernoulli",
        lambda_regions=tuple(row["lambda_regions"]),
        d0_k_set=(1, 2, 5, 20, 40),
    )
    kwargs.update(overrides)
    return RelayCorridorConfig(**kwargs)


def validate_horizon(
    config: RelayCorridorConfig,
    *,
    mode: str = "d0_fixed_k",
    k_max: int | None = None,
) -> Dict[str, object]:
    """ADR 02 invariant 6.

    ``H >= 10 * max(D0_k_set)`` for the fixed-``k`` D0 arm.  D2's ``k_max`` is
    **exempt** from that rule (a D2 arm may hold for up to ``H``); it reports
    ``M`` rows per rollout instead, which ADR 01 revision 3 identifies as the
    binding resolution term at long holds.

    Returns the accounting record; raises :class:`HorizonValidationError` when
    the fixed-``k`` D0 arm is rejected.
    """
    if mode not in ("d0_fixed_k", "d2"):
        raise ValueError(f"mode must be d0_fixed_k|d2, got {mode!r}")
    largest_k = int(max(config.d0_k_set))
    required = 10 * largest_k
    record: Dict[str, object] = {
        "mode": mode,
        "horizon": int(config.horizon),
        "largest_d0_k": largest_k,
        "required_horizon": required,
        "segments_at_largest_k": int(config.horizon) // largest_k,
        "k_max": None if k_max is None else int(k_max),
        "k_max_exempt": mode == "d2",
        "accepted": True,
    }
    if mode == "d0_fixed_k" and int(config.horizon) < required:
        record["accepted"] = False
        raise HorizonValidationError(
            "ADR 02 invariant 6: fixed-k D0 needs H >= 10 * max(D0_k_set); "
            f"H={config.horizon} < {required} (largest k={largest_k})"
        )
    return record


def rows_per_rollout(num_envs: int, rollout_length: int, k: int) -> int:
    """``M``: coordinator rows produced by one rollout at hold length ``k``.

    ADR 01 revision 3: D0 at ``k = 10`` with 32 environments and 500 steps has
    ``M = 32 * 500 / 10 = 1600`` rows; at ``k_max = H = 500`` infinite costs give
    ``M = 32``.  Both are reproduced by ``num_envs * ceil(rollout_length / k)``.
    """
    if int(k) < 1:
        raise ValueError("k must be a positive int")
    return int(num_envs) * -(-int(rollout_length) // int(k))
