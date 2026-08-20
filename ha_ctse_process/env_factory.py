"""Environment construction for the standalone process-core trainer."""

from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any, Callable

from pettingzoo.mpe import simple_spread_v3

from envs.pettingzoo.alice_bob_asymmetric_cycles import (
    AliceBobAsymmetricCyclesEnv,
)
from envs.pettingzoo.cooperative_two_timescale_sparse import (
    CooperativeTwoTimescaleSparseEnv,
)
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv
from envs.pettingzoo.relay.belief_map import UAVBeliefMapEnv
from envs.pettingzoo.relay.progressive import UAVProgressiveRelayEnv
from envs.pettingzoo.relay.energy_aware import UAVEnergyAwareRelayEnv
from envs.pettingzoo.two_timescale_role_free_actions import (
    TwoTimescaleRoleFreeActionsEnv,
)
from ha_ctse_process.dynamic_roster_testbed import DynamicRosterEventEnv


SCENARIO_ALIASES = {
    "base": "base",
    "4": "base",
    "s4": "base",
    "progress": "progress",
    "6": "progress",
    "s6": "progress",
    "belief_map": "belief_map",
    "belief-map": "belief_map",
    "5": "belief_map",
    "s5": "belief_map",
    "energy": "energy",
    "energy_aware": "energy",
    "energy-aware": "energy",
    "7": "energy",
    "s7": "energy",
    "scenario7": "energy",
    "alice_bob_asymmetric_cycles": "alice_bob_asymmetric_cycles",
    "alice-bob-asymmetric-cycles": "alice_bob_asymmetric_cycles",
    "alice_bob_multiscale": "alice_bob_asymmetric_cycles",
    "alice-bob-multiscale": "alice_bob_asymmetric_cycles",
    "two_timescale_role_free_actions": "two_timescale_role_free_actions",
    "two-timescale-role-free-actions": "two_timescale_role_free_actions",
    "role_free_two_timescale_actions": "two_timescale_role_free_actions",
    "role-free-two-timescale-actions": "two_timescale_role_free_actions",
    "r39_toy": "two_timescale_role_free_actions",
    "r39-toy": "two_timescale_role_free_actions",
    "simple_spread": "simple_spread",
    "simple-spread": "simple_spread",
    "simple_spread_v3": "simple_spread",
    "r40_simple_spread": "simple_spread",
    "generic_short_dynamic_roster": "generic_short_dynamic_roster",
    "generic-short-dynamic-roster": "generic_short_dynamic_roster",
    "dynamic_roster_generic_short": "generic_short_dynamic_roster",
}

SCENARIO_ALIASES.update(
    {
        "cooperative_two_timescale_sparse": "cooperative_two_timescale_sparse",
        "cooperative-two-timescale-sparse": "cooperative_two_timescale_sparse",
        "r38_cts": "cooperative_two_timescale_sparse",
        "cts": "cooperative_two_timescale_sparse",
    }
)


def normalize_scenario(scenario: str) -> str:
    key = str(scenario or "base").strip().lower()
    if key not in SCENARIO_ALIASES:
        raise ValueError(
            "Unknown scenario "
            f"{scenario!r}. Expected one of: {', '.join(sorted(SCENARIO_ALIASES))}"
        )
    return SCENARIO_ALIASES[key]


def _accepted_config_kwargs(constructor, config, **overrides) -> dict[str, Any]:
    """Bind only constructor-declared config fields, preserving its defaults."""

    parameters = inspect.signature(constructor).parameters
    kwargs = {
        name: getattr(config, name)
        for name, parameter in parameters.items()
        if name != "self"
        and parameter.kind
        not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and hasattr(config, name)
    }
    kwargs.update({name: value for name, value in overrides.items() if name in parameters})
    return kwargs


@dataclass(frozen=True)
class EnvSpec:
    scenario: str
    seed: int
    rank: int = 0
    render_mode: str | None = None
    scale_mode: str | None = None


def make_env(config, spec: EnvSpec) -> Callable[[], Any]:
    """Return a thunk compatible with SB3-style vector env constructors."""

    scenario = normalize_scenario(spec.scenario)

    def _init() -> Any:
        env_seed = int(spec.seed) + int(spec.rank)
        kwargs = {
            "config": config,
            "render_mode": spec.render_mode,
            "seed": env_seed,
        }

        if scenario == "generic_short_dynamic_roster":
            # The factory seed contract is the same for every scenario: rank is
            # part of the environment identity.  Formal event runners that use
            # the frozen 67_057/97_057 ledgers construct DynamicRosterEventEnv
            # directly and therefore remain unchanged.
            return DynamicRosterEventEnv(task_master_seed=env_seed)
        if scenario == "base":
            raw_env = UAVForcedRelayEnv(**kwargs)
        elif scenario == "belief_map":
            belief_kwargs = _accepted_config_kwargs(
                UAVBeliefMapEnv,
                config,
                render_mode=spec.render_mode,
                seed=env_seed,
            )
            # The shared config names roster size ``n_agents`` while the legacy
            # belief-map constructor names the same dimension ``n_uavs``.
            belief_kwargs["n_uavs"] = int(
                getattr(config, "n_uavs", getattr(config, "n_agents", 12))
            )
            raw_env = UAVBeliefMapEnv(**belief_kwargs)
        elif scenario == "progress":
            raw_env = UAVProgressiveRelayEnv(
                **kwargs,
                scale_mode=spec.scale_mode or "train",
            )
        elif scenario == "energy":
            raw_env = UAVEnergyAwareRelayEnv(
                **kwargs,
                scale_mode=spec.scale_mode or "train",
            )
        elif scenario == "alice_bob_asymmetric_cycles":
            raw_env = AliceBobAsymmetricCyclesEnv(**kwargs)
        elif scenario == "cooperative_two_timescale_sparse":
            raw_env = CooperativeTwoTimescaleSparseEnv(**kwargs)
        elif scenario == "two_timescale_role_free_actions":
            raw_env = TwoTimescaleRoleFreeActionsEnv(**kwargs)
        elif scenario == "simple_spread":
            raw_env = simple_spread_v3.parallel_env(
                N=int(getattr(config, "n_agents", 3)),
                local_ratio=float(getattr(config, "simple_spread_local_ratio", 0.0)),
                max_cycles=int(getattr(config, "episode_length", 25)),
                continuous_actions=bool(
                    getattr(config, "simple_spread_continuous_actions", False)
                ),
                render_mode=spec.render_mode,
            )
        else:
            raise AssertionError(f"Unhandled normalized scenario: {scenario}")

        return ParallelToArrayAdapter(raw_env, seed=env_seed)

    return _init
