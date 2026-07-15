"""Mechanism-matched full-refresh control for the lightweight R39 toy."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_native_categorical import Config as AdaptiveConfig


class Config(AdaptiveConfig):
    algorithm = "r39_toy_native_categorical_shared_refresh"
    scenario_label = "two_timescale_role_free_actions_shared_refresh"
    r30_force_refresh_every_check = True

