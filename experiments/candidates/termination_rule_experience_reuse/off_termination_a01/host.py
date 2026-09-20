"""Fully observed service-line dynamics with one fixed, committed teammate.

This is an independent small host, not the HMASD UAV environment. All random
numbers are supplied explicitly; a skill always reacts to the current position.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


STATE_COUNT = 400
OPTION_COUNT = 2
TEAMMATE_DURATION = 4


@dataclass(frozen=True)
class State:
    focal_position: int
    teammate_position: int
    demand: int
    teammate_skill: int
    teammate_remaining: int

    def encode(self) -> int:
        if not (0 <= self.focal_position < 5 and 0 <= self.teammate_position < 5):
            raise ValueError("positions must be in 0..4")
        if self.demand not in (0, 1) or self.teammate_skill not in (0, 1):
            raise ValueError("demand and skill must be 0 or 1")
        if not 1 <= self.teammate_remaining <= TEAMMATE_DURATION:
            raise ValueError("remaining commitment must be in 1..4")
        return (
            (((self.focal_position * 5 + self.teammate_position) * 2 + self.demand)
             * 2 + self.teammate_skill) * 4 + self.teammate_remaining - 1
        )

    @classmethod
    def decode(cls, index: int) -> "State":
        if not 0 <= index < STATE_COUNT:
            raise ValueError("invalid state index")
        rest, remaining = divmod(int(index), 4)
        rest, skill = divmod(rest, 2)
        rest, demand = divmod(rest, 2)
        focal, teammate = divmod(rest, 5)
        return cls(focal, teammate, demand, skill, remaining + 1)


def closed_loop_move(position: int, skill: int) -> int:
    """Move toward the named endpoint; retaining a skill recomputes feedback."""
    if skill not in (0, 1) or not 0 <= position < 5:
        raise ValueError("invalid position/skill")
    target = 4 * skill
    return position + int(target > position) - int(target < position)


def step(state: State, focal_skill: int, demand_u: float, teammate_u: float):
    """Reward precedes demand/teammate renewal; the returned state is predecision."""
    state.encode()  # Validate externally constructed fixture states too.
    focal = closed_loop_move(state.focal_position, focal_skill)
    teammate = closed_loop_move(state.teammate_position, state.teammate_skill)
    high, low = 4 * state.demand, 4 * (1 - state.demand)
    reward = .7 * int(high in (focal, teammate)) + .3 * int(low in (focal, teammate))
    demand = 1 - state.demand if demand_u < .12 else state.demand
    renewed = state.teammate_remaining == 1
    if renewed:
        skill = demand if teammate_u < .85 else 1 - demand
        remaining = TEAMMATE_DURATION
    else:
        skill = state.teammate_skill
        remaining = state.teammate_remaining - 1
    return State(focal, teammate, demand, skill, remaining), float(reward), renewed


def addressed_randomness(seed: int, phase: int, episode: int, horizon: int):
    """Columns address demand, teammate, focal termination and focal selection.

    Fixed-width draws avoid policy-dependent RNG consumption. Training and
    evaluation have separate phase addresses, and panels may reuse eval worlds.
    """
    rng = np.random.default_rng(np.random.SeedSequence([seed, phase, episode]))
    initial_state = State.decode(int(rng.integers(STATE_COUNT)))
    initial_option_u = float(rng.random())
    return initial_state, initial_option_u, rng.random((horizon, 4))


@dataclass(frozen=True)
class Episode:
    states: np.ndarray
    options: np.ndarray
    rewards: np.ndarray
    renewed: np.ndarray
    teammate_renewed: np.ndarray
    next_option_probability: np.ndarray

    def validate(self):
        n = len(self.rewards)
        if n == 0 or self.states.shape != (n + 1,) or self.options.shape != (n + 1,):
            raise ValueError("episode requires one successor state/option per row")
        for array in (self.renewed, self.teammate_renewed, self.next_option_probability):
            if array.shape != (n,):
                raise ValueError("misaligned transition fields")
        if np.any((self.states < 0) | (self.states >= STATE_COUNT)):
            raise ValueError("invalid encoded state")
        if np.any((self.options < 0) | (self.options >= OPTION_COUNT)):
            raise ValueError("invalid option")
        if not np.isfinite(self.rewards).all():
            raise ValueError("nonfinite reward")
        if np.any((self.next_option_probability <= 0) | (self.next_option_probability > 1)):
            raise ValueError("observed transition lacks behavior support")
        if np.any((self.options[1:] != self.options[:-1]) & ~self.renewed):
            raise ValueError("option changed without a behavior termination")


def behavior_episode(seed: int, episode: int, horizon: int, zeta: float) -> Episode:
    if not 0 < zeta <= 1:
        raise ValueError("positive termination probability is required for support")
    state, initial_option_u, draws = addressed_randomness(seed, 0, episode, horizon)
    option = int(initial_option_u >= .5)
    states = np.empty(horizon + 1, dtype=np.int16)
    options = np.empty(horizon + 1, dtype=np.int8)
    rewards = np.empty(horizon, dtype=np.float64)
    renewed = np.empty(horizon, dtype=np.bool_)
    teammate_renewed = np.empty(horizon, dtype=np.bool_)
    probabilities = np.empty(horizon, dtype=np.float64)
    states[0], options[0] = state.encode(), option
    for t, (demand_u, teammate_u, renewal_u, selection_u) in enumerate(draws):
        state, rewards[t], teammate_renewed[t] = step(state, option, demand_u, teammate_u)
        renewed[t] = renewal_u < zeta
        next_option = int(selection_u >= .5) if renewed[t] else option
        probabilities[t] = (1 - zeta) * int(next_option == option) + zeta / 2
        states[t + 1], options[t + 1] = state.encode(), next_option
        option = next_option
    result = Episode(states, options, rewards, renewed, teammate_renewed, probabilities)
    result.validate()
    return result
