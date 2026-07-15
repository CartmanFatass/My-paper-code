"""R37 treatment exposing only current active plate and target identity."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_identity_masked import Config as MaskedConfig


class Config(MaskedConfig):
    algorithm = "alice_bob_sparse_mappo_identity_visible"
    scenario_label = "alice_bob_asymmetric_cycles_identity_visible"
    alice_bob_actor_identity_mode = "visible"
