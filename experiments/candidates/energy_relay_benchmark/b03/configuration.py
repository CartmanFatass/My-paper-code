"""B03 Stage 2 programme "GAS-shield-on-1.2M": grounded assignment skills on HMASD's coordinator.

Declared in ``docs/research/candidates/energy_relay_benchmark/NOTES.md`` section "2026-09-27 --
Stage 2 declaration (B03)".  The native base is the one B02 uses (``uav_service_auxiliary/b01/
native.py::make_config``, the S7-S2 preset of B09: 2 lanes x rollout 3000, episode 3000, k 10,
lambda_return 2.0, lambda_e 1.0, normalizers off) **without** the mappo switch, then the
declared GAS settings (``make_b03_config``).  Exposure, lanes, checkpoints and the ``B02Spec``
production sizes are B02's.
"""

from __future__ import annotations

from typing import Any

from experiments.candidates.uav_service_auxiliary.b01.native import make_config

from ..b02.configuration import (
    CHECKPOINT_EVERY_TRANSITIONS, CHECKPOINT_RULE, TOTAL_TRANSITIONS, B02Spec, assert_production,
    checkpoint_rollouts, spec_record,
)
from ..b02.configuration import config_dict as b02_config_dict
from .anchors import (
    ANCHOR_DIM, AREA_M, FREE_LABEL, KMEANS_ITERATIONS, N_LABELS, N_RELAY, N_SERVICE,
    RELAY_FRACTIONS, RELAY_LABELS, SERVICE_LABELS,
)

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B03"
DIRECTION = "energy_relay_benchmark"
PROGRAMME = "GAS-shield-on-1.2M"
ARM = "gas"
# 26092711 / 26092731: DM1's clean SET seeds (paired); 925031: Stage 2b only (NOTES B03 entry).
TRAINING_SEEDS = (26092711, 26092731, 925031)
LAMBDA_H = 0.01
BLOCK_FIELDS = ("anchor_x/area", "anchor_y/area", "rel_x/area", "rel_y/area", "dist/area",
                "is_free")
ANCHOR_BLOCK_WIDTH = len(BLOCK_FIELDS)

__all__ = ["OBJECT_ID", "DIRECTION", "PROGRAMME", "ARM", "TRAINING_SEEDS", "B02Spec",
           "CHECKPOINT_EVERY_TRANSITIONS", "CHECKPOINT_RULE", "TOTAL_TRANSITIONS",
           "checkpoint_rollouts", "spec_record", "production_spec", "make_b03_config",
           "config_dict", "actor_input_width", "central_input_width", "snapshot_width",
           "GAS_RECORD", "RECIPE_NOTES"]

GAS_RECORD = {
    "labels": {"relay": list(RELAY_LABELS), "service": list(SERVICE_LABELS), "free": FREE_LABEL},
    "n_labels": N_LABELS, "n_relay": N_RELAY, "n_service": N_SERVICE,
    "anchor_units": f"area-normalised xy (metres / {AREA_M:g})",
    "service": ("b01/heuristic.py::estimator_kmeans(users_m, 6, iterations=30) on the 30 user xy "
                "of the raw state in metres (state[32:212] x/y columns x area), seeds "
                "np.linspace(0, 29, 6, dtype=int) over the env user index order; ordered by "
                "descending assigned user count, ties by centroid index "
                "(np.argsort(-counts, kind='stable'), LayoutHeuristic.plan's rule)"),
    "kmeans_iterations": KMEANS_ITERATIONS,
    "relay": ("bs_xy + f * (mean(centroids) - bs_xy), BS xy = state[212:214] x area; labels 0, 1 "
              "in ascending distance from the BS"),
    "relay_fractions": list(RELAY_FRACTIONS),
    "free": "label 8: anchor row of zeros, block zeros with is_free = 1",
    "decision_cadence": ("anchors computed once per team decision (env_timers == 0 after "
                         "_batched_assign_skills: episode step % k == 0 or lane reset) from the "
                         "state the coordinator decided on; stored with the held snapshot"),
    "snapshot_row": "state 306 | anchors 18 (9 x 2, label-major) | labels 8 (float) = 332",
    "central_input": "state 306 | anchors 18 | own label 1 | 8 x obs 365 | ego one-hot 8 = 3253",
    "actor_block": list(BLOCK_FIELDS),
    "actor_block_source": ("assigned anchor = anchors[label]; own xy = the current observation's "
                           "obs[0:2]; rel = anchor - own; dist = sqrt(rel_x^2 + rel_y^2); FREE -> "
                           "zeros with is_free = 1"),
    "actor_input": "obs 365 | state 306 | 8 x obs 2920 | ego 8 | block 6 = 3605",
    "film": "R_Actor FiLM on the label one-hot (9 wide)",
}

RECIPE_NOTES = {
    "native_base": ("uav_service_auxiliary/b01/native.py::make_config (S7-S2 preset, B09 recipe) "
                    "without the mappo switch"),
    "gas_switch": ("ordinary_completed_segments = True (B09's native value); n_Z = 1; n_z = 9; "
                   "k = 10; lambda_h = 0.01; lambda_D = lambda_d = 0; "
                   "disable_high_level_training = False; disable_discriminator_training = True; "
                   "disable_discriminator_rewards = True; use_central_snapshot_in_flat_actor = "
                   "True; calculate_and_set_buffer_sizes(); validate_config()"),
    "low_level_reward": ("disable_discriminator_rewards: the low-level reward is lambda_e * "
                         "native reward (hmasd/agent.py _compute_intrinsic_rewards_batch -> "
                         "_empty_intrinsic_batch_result)"),
    "collects_high_level_samples": ("an HMASDAgent attribute (not disable_high_level_training); "
                                    "the hmasd switch never sets the config field, so config "
                                    "records it as null; the agent value is asserted True"),
    "anchor_storage": ("labels ride with the held snapshot: hmasd/agent.py "
                       "update_discoverer_from_rollout calls skill_discoverer._apply_central_input "
                       "without the labels, so the snapshot row stores the labels decided at the "
                       "same step and the replay builder selects the agent's own label"),
    "training_shield": "B06 apply_feedback at the production layout (enter 0.0, exit 0.05)",
    "decision_log": ("decisions.jsonl (raw, gitignored bulk) + a per-rollout summary in the "
                     "rollout record (progress.jsonl / summary.json)"),
}


def production_spec(seed: int) -> B02Spec:
    if int(seed) not in TRAINING_SEEDS:
        raise ValueError(f"unplanned B03 training seed {seed}; declared {TRAINING_SEEDS}")
    spec = B02Spec(seed=int(seed))
    assert_production(spec)
    return spec


def make_b03_config(spec: B02Spec):
    """B02's native base for ``spec`` without the mappo switch, then the declared GAS settings."""
    config = make_config(spec)
    expected = {"seed": spec.seed, "num_envs": spec.lanes, "rollout_length": spec.rollout_length,
                "episode_length": spec.episode_length, "max_steps": spec.episode_length,
                "total_timesteps": spec.transitions, "n_agents": 8, "k": 10}
    mismatches = {key: (value, getattr(config, key, None)) for key, value in expected.items()
                  if getattr(config, key, None) != value}
    if mismatches:
        raise ValueError(f"B03 native configuration mismatch: {mismatches}")
    if config.lambda_return != 2.0 or config.lambda_e != 1.0:
        raise ValueError("B03 native reward coefficients changed")
    if config.use_obsnorm or config.use_statenorm:
        raise ValueError("B03 expects disabled observation/state normalizers")
    config.ordinary_completed_segments = True
    config.n_Z = 1
    config.n_z = N_LABELS
    config.k = 10
    config.lambda_h = LAMBDA_H
    config.lambda_D = 0.0
    config.lambda_d = 0.0
    config.disable_high_level_training = False
    config.disable_discriminator_training = True
    config.disable_discriminator_rewards = True
    config.use_central_snapshot_in_flat_actor = True
    config.calculate_and_set_buffer_sizes()
    config.validate_config()
    if (
        config.algorithm != "hmasd" or getattr(config, "baseline_algorithm", None) != "hmasd"
        or config.k != 10 or config.n_Z != 1 or config.n_z != N_LABELS
        or config.lambda_h != LAMBDA_H or config.lambda_D != 0.0 or config.lambda_d != 0.0
        or not config.ordinary_completed_segments or not config.use_central_snapshot_in_flat_actor
        or config.disable_high_level_training or not config.disable_discriminator_training
        or not config.disable_discriminator_rewards
        or config.high_level_buffer_size != spec.lanes * (spec.rollout_length // config.k)
        or config.lambda_return != 2.0 or config.lambda_e != 1.0
        or config.use_obsnorm or config.use_statenorm
        or config.total_timesteps != spec.transitions
        or str(getattr(config, "policy_interruption_mode", "off")) != "off"
        or bool(getattr(config, "use_horizon_window", False))
        or getattr(config, "central_snapshot_state_affine", None) is not None
        or bool(getattr(config, "use_compact_in_low_level_actor", False))
        or int(config.state_dim) != 306 or int(config.obs_dim) != 365
    ):
        raise ValueError("B03 GAS settings did not produce the declared configuration")
    return config


def config_dict(config) -> dict[str, Any]:
    """B02's recorded fields (``n_Z``/``n_z`` included) plus the anchor rule."""
    return b02_config_dict(config) | {"gas": GAS_RECORD}


def snapshot_width(config) -> int:
    """Held snapshot row: state | anchors 18 | labels n_agents."""
    return int(config.state_dim) + ANCHOR_DIM + int(config.n_agents)


def central_input_width(config) -> int:
    """Per-agent central input: state | anchors 18 | own label 1 | n_agents x obs | ego."""
    return (int(config.state_dim) + ANCHOR_DIM + 1 + int(config.n_agents) * int(config.obs_dim)
            + int(config.n_agents))


def actor_input_width(config) -> int:
    """Actor input: own obs | state | n_agents x obs | ego | anchor block 6."""
    return (int(config.obs_dim) + int(config.state_dim)
            + int(config.n_agents) * int(config.obs_dim) + int(config.n_agents)
            + ANCHOR_BLOCK_WIDTH)
