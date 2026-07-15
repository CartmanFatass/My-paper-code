"""R39 toy positive control with zero-parameter skill action primitives."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_native_categorical import Config as LearnedLowConfig


class Config(LearnedLowConfig):
    algorithm = "r39_toy_fixed_primitives"
    network_scale_profile = "r39_toy_fixed_low_high32"
    r39_toy_fixed_skill_primitives = True
    r39_toy_fixed_skill_action_schema = "axis4_xy_v1"
