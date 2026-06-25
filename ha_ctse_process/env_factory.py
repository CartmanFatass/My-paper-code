"""Environment construction for the standalone process-core trainer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from envs.pettingzoo.scenario5 import UAVBeliefMapEnv
from envs.pettingzoo.scenario6_progressive import UAVProgressiveRelayEnv
from envs.pettingzoo.scenario7_energy_aware import UAVEnergyAwareRelayEnv


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
}


def normalize_scenario(scenario: str) -> str:
    key = str(scenario or "base").strip().lower()
    if key not in SCENARIO_ALIASES:
        raise ValueError(
            "Unknown scenario "
            f"{scenario!r}. Expected one of: {', '.join(sorted(SCENARIO_ALIASES))}"
        )
    return SCENARIO_ALIASES[key]


@dataclass(frozen=True)
class EnvSpec:
    scenario: str
    seed: int
    rank: int = 0
    render_mode: str | None = None
    scale_mode: str | None = None


def make_env(config, spec: EnvSpec) -> Callable[[], ParallelToArrayAdapter]:
    """Return a thunk compatible with SB3-style vector env constructors."""

    scenario = normalize_scenario(spec.scenario)

    def _init() -> ParallelToArrayAdapter:
        env_seed = int(spec.seed) + int(spec.rank)
        kwargs = {
            "config": config,
            "render_mode": spec.render_mode,
            "seed": env_seed,
        }

        if scenario == "base":
            raw_env = UAVForcedRelayEnv(**kwargs)
        elif scenario == "belief_map":
            raw_env = UAVBeliefMapEnv(**kwargs)
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
        else:
            raise AssertionError(f"Unhandled normalized scenario: {scenario}")

        return ParallelToArrayAdapter(raw_env, seed=env_seed)

    return _init

