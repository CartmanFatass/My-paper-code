"""R37 capacity-matched control with zeroed task-identity slots."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_sparse_mappo import Config as SparseMAPPOConfig


class Config(SparseMAPPOConfig):
    algorithm = "alice_bob_sparse_mappo_identity_masked"
    scenario_label = "alice_bob_asymmetric_cycles_identity_masked"

    obs_dim = 16
    r37_identity_gate_enabled = True
    alice_bob_actor_identity_mode = "masked"
    alice_bob_actor_identity_slots = 4
    alice_bob_actor_identity_schema = "active_plate_target_onehot_v1"
