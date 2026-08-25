"""Streaming update-512 evaluation for the frozen RIDGEGATE-2Z panel."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .authorization import ProductionPermit, require_active_permit
from .config import (
    EVENTS_PER_BASIN,
    EVALUATION_EPISODES,
    HELDOUT_ROSTERS,
    REGISTERED_ROSTERS,
    TRAIN_ROSTERS,
)
from .policies import ArmModel
from .rng import Coordinate, CounterRNG
from .training import EpisodeResult, rollout_model_episode, rollout_uniform_episode


LEARNED_ARMS = ("PHY-TRUST", "EDGE-FLEX")


@dataclass
class StreamingPanelMean:
    """Constant-memory reducer; episode rows never become inferential samples."""

    count: int = 0
    return_sum: float = 0.0
    west_sum: float = 0.0
    east_sum: float = 0.0
    radio_actions: int = 0
    waste_actions: int = 0
    duplicate_arrivals: int = 0
    expired_arrivals: int = 0
    collision_losses: int = 0
    empty_actions: int = 0
    new_timely_deliveries: int = 0

    def add(self, result: EpisodeResult) -> None:
        west, east = result.basin_delivery_rates
        metrics = result.metrics
        self.count += 1
        self.return_sum += float(result.return_value)
        self.west_sum += float(west)
        self.east_sum += float(east)
        self.radio_actions += int(metrics.radio_actions)
        self.waste_actions += int(metrics.waste_actions)
        self.duplicate_arrivals += int(metrics.duplicate_arrivals)
        self.expired_arrivals += int(metrics.expired_arrivals)
        self.collision_losses += int(metrics.collision_losses)
        self.empty_actions += int(metrics.empty_actions)
        self.new_timely_deliveries += int(metrics.new_timely_deliveries)

    def finish(self) -> dict[str, Any]:
        if self.count != EVALUATION_EPISODES:
            raise RuntimeError("a registered evaluation panel must contain exactly 256 worlds")
        return {
            "mean_return": self.return_sum / self.count,
            "mean_timely_delivery_by_basin": {
                "WEST": self.west_sum / self.count,
                "EAST": self.east_sum / self.count,
            },
            "world_count": self.count,
            "task_diagnostics": {
                "radio_actions": self.radio_actions,
                "waste_actions": self.waste_actions,
                "duplicate_arrivals": self.duplicate_arrivals,
                "expired_arrivals": self.expired_arrivals,
                "collision_losses": self.collision_losses,
                "empty_actions": self.empty_actions,
                "new_timely_deliveries": self.new_timely_deliveries,
            },
        }


@dataclass
class StreamingShadowMean:
    history_count: int = 0
    tv_sum: float = 0.0
    support_sum: float = 0.0
    finite: bool = True

    def add(self, result: EpisodeResult, histories: int) -> None:
        if result.shadow_tv_mean is None or result.tv_support_mean is None:
            raise RuntimeError("intact PHY rollout omitted registered shadow/support means")
        self.finite = self.finite and all(
            value == value and abs(value) != float("inf")
            for value in (result.shadow_tv_mean, result.tv_support_mean)
        )
        self.tv_sum += float(result.shadow_tv_mean) * histories
        self.support_sum += float(result.tv_support_mean) * histories
        self.history_count += histories

    def finish(self, expected_histories: int) -> dict[str, Any]:
        if self.history_count != expected_histories or not self.finite:
            raise RuntimeError("the registered shadow-cut history panel is incomplete or nonfinite")
        return {
            "mean_legal_action_tv": self.tv_sum / self.history_count,
            "mean_tv_support": self.support_sum / self.history_count,
            "history_count": self.history_count,
            "shadow_state_propagated": False,
            "intact_observations_and_incoming_hidden_fixed": True,
        }

def evaluate_seed(
    permit: ProductionPermit,
    seed: int,
    models: Mapping[str, ArmModel],
    progress_guard=None,
) -> dict[str, Any]:
    """Evaluate one complete seed block from the sole update-512 checkpoint."""
    require_active_permit(permit)
    permit.require_seed(seed)
    if set(models) != set(LEARNED_ARMS):
        raise ValueError("evaluation requires exactly PHY-TRUST and EDGE-FLEX")
    for arm, model in models.items():
        if model.arm_name != arm:
            raise ValueError("model arm identity mismatch")
        model.eval()

    rng = CounterRNG(permit)
    cells: dict[str, Any] = {}
    for n in REGISTERED_ROSTERS:
        intact = {arm: StreamingPanelMean() for arm in LEARNED_ARMS}
        rotated = {arm: StreamingPanelMean() for arm in LEARNED_ARMS}
        uniform = StreamingPanelMean()
        shadow = StreamingShadowMean()
        for episode in range(EVALUATION_EPISODES):
            if progress_guard is not None:
                progress_guard()
            coordinate = Coordinate(
                phase="evaluation", seed=seed, roster=n, episode=episode, update=None
            )
            for arm in LEARNED_ARMS:
                capture_shadow = arm == "PHY-TRUST" and n in HELDOUT_ROSTERS
                intact_result = rollout_model_episode(
                    permit, models[arm], coordinate, rng=rng, condition="intact",
                    require_loss=False, capture_shadow_cut=capture_shadow,
                )
                intact[arm].add(intact_result)
                if capture_shadow:
                    shadow.add(intact_result, histories=12 * n)
                if n in HELDOUT_ROSTERS:
                    rotated[arm].add(rollout_model_episode(
                        permit, models[arm], coordinate, rng=rng, condition="rotated",
                        require_loss=False, capture_shadow_cut=False,
                    ))
            if n in TRAIN_ROSTERS:
                uniform.add(rollout_uniform_episode(permit, coordinate, rng=rng))

        cell: dict[str, Any] = {
            "n": n,
            "world_count": EVALUATION_EPISODES,
            "intact": {arm: reducer.finish() for arm, reducer in intact.items()},
            "uniform": (
                {"UNIFORM-LEGAL": uniform.finish()} if n in TRAIN_ROSTERS else {}
            ),
            "rotated": {},
            "shadow": {},
            "registered_support": {
                "basin_count": 2,
                "events_per_basin": EVENTS_PER_BASIN,
                "public_role_count": 3,
                "agents_per_role": n // 3,
                "balanced_positive_role_support": n // 3 > 0,
                "fixed_legal_masks": True,
            },
        }
        if n in HELDOUT_ROSTERS:
            cell["rotated"] = {arm: reducer.finish() for arm, reducer in rotated.items()}
            cell["shadow"] = {"PHY-TRUST": shadow.finish(EVALUATION_EPISODES * 12 * n)}
        cells[str(n)] = cell

    return {
        "seed": seed,
        "cells": cells,
        "registered_rosters": list(REGISTERED_ROSTERS),
        "worlds_per_roster": EVALUATION_EPISODES,
        "frozen_checkpoint": "immediately_after_update_512",
        "evaluation_updates": 0,
        "heldout_training_or_adaptation": False,
        "greedy_evaluation": False,
        "stochastic_policy_including_uniform_mixture": True,
        "episode_rows_retained": False,
        "seed_is_inferential_unit": True,
        "arm_independent_world_and_action_coordinates": True,
        "rotated_panels_only_at_heldout_rosters": True,
        "shadow_cut_only_at_heldout_rosters": True,
        "uniform_legal_only_at_training_rosters": True,
    }
