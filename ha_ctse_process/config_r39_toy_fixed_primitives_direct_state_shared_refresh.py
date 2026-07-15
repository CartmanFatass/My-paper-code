"""Full-refresh control for the R39 direct-state high-context diagnostic."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_fixed_primitives_direct_state import (
    Config as DirectStateConfig,
)


class Config(DirectStateConfig):
    algorithm = "r39_toy_fixed_primitives_direct_state_shared_refresh"
    scenario_label = "two_timescale_role_free_actions_direct_state_shared_refresh"
    r30_force_refresh_every_check = True

