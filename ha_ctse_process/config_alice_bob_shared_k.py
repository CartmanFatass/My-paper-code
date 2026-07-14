"""Mechanism-matched shared fixed-k control for Alice--Bob."""

from __future__ import annotations

from ha_ctse_process.config_alice_bob_asymmetric import Config as AdaptiveConfig


class Config(AdaptiveConfig):
    scenario_label = "alice_bob_asymmetric_cycles_shared_k_control"
    r30_force_refresh_every_check = True
