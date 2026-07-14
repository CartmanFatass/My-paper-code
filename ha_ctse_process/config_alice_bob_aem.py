"""R36 episodic joint-position novelty on constant-code recurrent MAPPO."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_sparse_mappo import Config as SparseMAPPOConfig


class Config(SparseMAPPOConfig):
    algorithm = "alice_bob_sparse_mappo_aem_joint_novelty"
    scenario_label = "alice_bob_asymmetric_cycles_aem_joint_novelty"
    aem_joint_novelty_enabled = True
