"""Four-agent, three-transition censored-substitution host."""

from __future__ import annotations

from dataclasses import dataclass

from . import config as C
from .rng import categorical, uniform01


@dataclass(frozen=True)
class Transition:
    step: int
    event: str
    carrier: int | None
    provenance_relation: int
    utility: int


@dataclass(frozen=True)
class Episode:
    source: int
    content: int
    action: int
    mode: str
    clockwise_waiter: int
    counterclockwise_waiter: int
    selected_waiter: int
    replacement_carrier: int
    final_carrier: int | None
    utility: int
    transitions: tuple[Transition, Transition, Transition]

    @property
    def ordered_edge_keys(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return (
            (self.source, self.clockwise_waiter),
            (self.source, self.counterclockwise_waiter),
        )


@dataclass(frozen=True)
class EvaluationOpportunity:
    source: int
    content: int
    mode: str
    action_uniform: float


def exact_q(source: int, content: int, action: int) -> float:
    del source
    return 2.0 / 3.0 if action == content else 0.0


def make_episode(source: int, content: int, action: int, mode: str) -> Episode:
    clockwise = (source + 1) % 4
    counterclockwise = (source - 1) % 4
    selected = clockwise if action == 1 else counterclockwise
    replacement = (source + 2) % 4
    final_carrier = None if mode == "EXPIRE" else replacement if mode == "REPLACE" else selected
    utility = int(mode != "EXPIRE" and action == content)
    transitions = (
        Transition(1, "SELECT", selected, action, 0),
        Transition(2, mode, final_carrier, action, 0),
        Transition(3, "SERVE" if final_carrier is not None else "CENSORED", final_carrier, action, utility),
    )
    return Episode(
        source=source,
        content=content,
        action=action,
        mode=mode,
        clockwise_waiter=clockwise,
        counterclockwise_waiter=counterclockwise,
        selected_waiter=selected,
        replacement_carrier=replacement,
        final_carrier=final_carrier,
        utility=utility,
        transitions=transitions,
    )


def generate_training(seed: int, episodes: int = C.TRAIN_EPISODES) -> list[Episode]:
    rows: list[Episode] = []
    for index in range(episodes):
        source = C.SOURCES[categorical(seed, C.RNG_NAMESPACES["training_source"], 4, index)]
        content = C.CONTENTS[categorical(seed, C.RNG_NAMESPACES["training_content"], 2, index)]
        action = C.ACTIONS[categorical(seed, C.RNG_NAMESPACES["training_action"], 2, index)]
        mode = C.MODES[categorical(seed, C.RNG_NAMESPACES["training_mode"], 3, index)]
        rows.append(make_episode(source, content, action, mode))
    return rows


def generate_evaluation(
    seed: int,
    episodes: int = C.EVALUATION_EPISODES,
) -> list[EvaluationOpportunity]:
    rows: list[EvaluationOpportunity] = []
    for index in range(episodes):
        rows.append(
            EvaluationOpportunity(
                source=C.SOURCES[
                    categorical(seed, C.RNG_NAMESPACES["evaluation_source"], 4, index)
                ],
                content=C.CONTENTS[
                    categorical(seed, C.RNG_NAMESPACES["evaluation_content"], 2, index)
                ],
                mode=C.MODES[
                    categorical(seed, C.RNG_NAMESPACES["evaluation_mode"], 3, index)
                ],
                action_uniform=uniform01(
                    seed,
                    C.RNG_NAMESPACES["evaluation_action_uniform"],
                    index,
                ),
            )
        )
    return rows
