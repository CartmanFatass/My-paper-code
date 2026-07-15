"""R39 fixed-primitive toy with raw centralized high-level context."""

from __future__ import annotations

from ha_ctse_process.config_r39_toy_fixed_primitives import Config as FixedConfig


class Config(FixedConfig):
    algorithm = "r39_toy_fixed_primitives_direct_state"
    network_scale_profile = "r39_toy_fixed_low_direct_state_high32"
    r39_toy_direct_state_context = True

    # The six raw centralized-state entries occupy the first slots; the final
    # two are deterministic zero padding.  No learned OPT/bridge transform is
    # used by the high policy or critic in this diagnostic.
    opt_compact_dim = 8
    team_code_dim = 1
    num_team_codes = 1
    team_bridge_type = "none"

