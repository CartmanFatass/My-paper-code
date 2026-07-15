"""Three-epoch high-PPO treatment for the R39 direct-state toy."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_fixed_primitives_direct_state_shared_refresh import (
    Config as SharedRefreshConfig,
)


class Config(SharedRefreshConfig):
    algorithm = "r39_toy_fixed_primitives_direct_state_high3_shared_refresh"
    scenario_label = "two_timescale_role_free_actions_high3_shared_refresh"
    r30_high_ppo_epochs = 3
