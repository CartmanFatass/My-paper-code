"""Full-refresh control for the R39 fixed-primitive toy gate."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_fixed_primitives import Config as AdaptiveConfig


class Config(AdaptiveConfig):
    algorithm = "r39_toy_fixed_primitives_shared_refresh"
    scenario_label = "two_timescale_role_free_actions_fixed_shared_refresh"
    r30_force_refresh_every_check = True

