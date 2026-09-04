"""Learned and fixed ACVC-B1 policies."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random
from typing import Mapping, Sequence

from .host import ACTIONS, Action, CanonicalState, Feedback


LEARN_CORRECT = "LEARN-CORRECT"
LEARN_PERM = "LEARN-PERM"
DET_BOUND = "DET-BOUND"
AUTH_PROBE = "AUTH-PROBE"
IGNORE = "IGNORE"
LEARNED_ARMS = (LEARN_CORRECT, LEARN_PERM)
FIXED_ARMS = (DET_BOUND, AUTH_PROBE, IGNORE)
ALPHA = 0.15
GAMMA = 1.0


def epsilon_for_episode(episode: int) -> float:
    if not 1 <= episode <= 7_680:
        raise ValueError("training episode must be in [1, 7680]")
    if episode >= 7_000:
        return 0.02
    return 0.30 + (0.02 - 0.30) * ((episode - 1) / (7_000 - 1))


def _counter_word(seed: int, episode: int, service_position: int,
                  local_action_index: int, purpose: str) -> int:
    payload = f"ACVC-B1\0{seed}\0{episode}\0{service_position}\0{local_action_index}\0{purpose}"
    return int.from_bytes(hashlib.sha256(payload.encode("ascii")).digest()[:8], "big")


def counter_uniform(seed: int, episode: int, service_position: int,
                    local_action_index: int, purpose: str) -> float:
    return (_counter_word(seed, episode, service_position, local_action_index, purpose) + 0.5) / 2**64


@dataclass
class TabularQLearner:
    learner_seed: int
    q: dict[tuple[int, int, str, bool, bool, bool], list[float]] = field(default_factory=dict)
    updates: int = 0

    def __post_init__(self) -> None:
        if self.learner_seed <= 0:
            raise ValueError("learner seed must be positive")

    @staticmethod
    def _key(state: CanonicalState) -> tuple[int, int, str, bool, bool, bool]:
        return state.as_tuple()

    def values(self, state: CanonicalState) -> list[float]:
        key = self._key(state)
        values = self.q.get(key)
        if values is None:
            values = [0.0] * len(ACTIONS)
            self.q[key] = values
        return values

    def training_action(self, state: CanonicalState, *, episode: int) -> Action:
        local_index = state.target_action_count + 1
        explore = counter_uniform(
            self.learner_seed, episode, state.service_position, local_index, "epsilon_coin"
        ) < epsilon_for_episode(episode)
        if explore:
            word = _counter_word(
                self.learner_seed, episode, state.service_position, local_index, "exploration_action"
            )
            return ACTIONS[word % len(ACTIONS)]
        values = self.values(state)
        best = max(values)
        ties = [index for index, value in enumerate(values) if value == best]
        tie_word = _counter_word(
            self.learner_seed, episode, state.service_position, local_index, "training_tie"
        )
        return ACTIONS[ties[tie_word % len(ties)]]

    def evaluation_action(self, state: CanonicalState, tie_rank: Sequence[Action]) -> Action:
        values = self.values(state)
        best = max(values)
        best_actions = {ACTIONS[index] for index, value in enumerate(values) if value == best}
        return next(action for action in tie_rank if action in best_actions)

    def update(self, state: CanonicalState, action: Action, reward: float,
               next_state: CanonicalState | None, scene_done: bool) -> None:
        values = self.values(state)
        bootstrap = 0.0 if scene_done or next_state is None else max(self.values(next_state))
        index = ACTIONS.index(action)
        values[index] += ALPHA * (reward + GAMMA * bootstrap - values[index])
        self.updates += 1

    def to_json(self) -> dict[str, object]:
        rows = [
            {"state": list(key), "q": list(values)}
            for key, values in sorted(self.q.items(), key=lambda item: repr(item[0]))
        ]
        return {
            "schema": "ACVC-B1-TABULAR-Q-v1",
            "learner_seed": self.learner_seed,
            "alpha": ALPHA,
            "gamma": GAMMA,
            "updates": self.updates,
            "rows": rows,
        }

    @classmethod
    def from_json(cls, payload: Mapping[str, object]) -> "TabularQLearner":
        if payload.get("schema") != "ACVC-B1-TABULAR-Q-v1":
            raise ValueError("invalid checkpoint schema")
        learner = cls(int(payload["learner_seed"]))
        for row in payload["rows"]:  # type: ignore[index,union-attr]
            state = row["state"]  # type: ignore[index]
            key = (int(state[0]), int(state[1]), str(state[2]), bool(state[3]), bool(state[4]), bool(state[5]))
            values = [float(value) for value in row["q"]]  # type: ignore[index]
            if len(values) != len(ACTIONS):
                raise ValueError("invalid Q row")
            learner.q[key] = values
        learner.updates = int(payload["updates"])
        return learner


def evaluation_tie_rank(base_seed: int) -> tuple[Action, ...]:
    rank = list(ACTIONS)
    random.Random(700_000 + base_seed).shuffle(rank)
    return tuple(rank)


def fixed_action(arm: str, state: CanonicalState) -> Action:
    feedback = Feedback(state.previous_feedback)
    if arm == IGNORE:
        return Action.COMPLETE
    if arm == DET_BOUND:
        if feedback is Feedback.CONTINUE_EPOCH_CHANGED:
            return Action.COMPLETE
        if feedback is Feedback.CONTINUE_NO_CHANGE:
            return Action.ABSTAIN
        return Action.CONTINUE if state.active_matching_negative else Action.COMPLETE
    if arm != AUTH_PROBE:
        raise ValueError(f"unknown fixed arm: {arm}")
    if not state.any_authenticated_negative or state.event_located and feedback is Feedback.NONE:
        return Action.COMPLETE
    if feedback is Feedback.PROBE_VALID:
        return Action.COMPLETE
    if feedback is Feedback.PROBE_REPAIRABLE:
        return Action.CONTINUE
    if feedback is Feedback.PROBE_TERMINAL:
        return Action.ABSTAIN
    if feedback is Feedback.CONTINUE_EPOCH_CHANGED:
        return Action.COMPLETE
    if feedback is Feedback.CONTINUE_NO_CHANGE:
        return Action.ABSTAIN
    # With an authenticated negative but no located event, the final service
    # target is inferred invalid without a probe; all earlier targets are probed.
    return Action.CONTINUE if state.service_position == 3 else Action.PROBE
