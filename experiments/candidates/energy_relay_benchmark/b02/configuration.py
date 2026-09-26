"""B02 Stage 1 programme "SET-shield-on-1.2M": fixed S7 native recipe with the SET actor.

The native base is B09's ``make_b09_config`` (``uav_service_auxiliary/b09/native.py``): the S7-S2
preset built by ``uav_service_auxiliary/b01/native.py::make_config`` with 2 lanes x rollout 3000,
episode 3000, k 10, lambda_return 2.0, lambda_e 1.0 and the observation/state normalizers off.
The SET switch is the one ``agent_count_generalization/configuration.py::make_config`` applies:
``apply_algorithm_config(config, "mappo")``, ``k = 10`` restored,
``use_central_snapshot_in_flat_actor = True``, ``calculate_and_set_buffer_sizes()``,
``validate_config()``.

Two forced differences from B09's config (see ``RECIPE_NOTES``): ``ordinary_completed_segments``
is False because ``HMASDAgent`` refuses it together with ``disable_high_level_training`` (the
mappo switch), and exposure is 200 rollouts (1.2 M transitions) instead of 30.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from experiments.candidates.uav_service_auxiliary.b01.native import NativeSpec, make_config
from hmasd.baselines import apply_algorithm_config

OBJECT_ID = "ENERGY-RELAY-BENCHMARK-B02"
DIRECTION = "energy_relay_benchmark"
PROGRAMME = "SET-shield-on-1.2M"
# DM decision 2026-09-26: 925031, B09's own TRAINING_SEED (the L0 named 915031, which is B08's), so the
# learner's recorded policy seed and the evaluator's sample_seed rule match N's.
TRAINING_SEED = 925031
TRAINING_SEEDS = (TRAINING_SEED,)
TOTAL_TRANSITIONS = 1_200_000
CHECKPOINT_EVERY_TRANSITIONS = 200_000
CHECKPOINT_RULE = ("c00 = the initialisation (0 transitions, saved before any collection); "
                   "c01.. = after the update of the first rollout whose cumulative transitions "
                   "reach each multiple of checkpoint_every_transitions (200,000 / 6,000 per "
                   "rollout is not an integer: rollouts 34, 67, 100, 134, 167, 200 = 204k, 402k, "
                   "600k, 804k, 1,002k, 1.2M); record.json holds the exact count")
RECIPE_NOTES = {
    "native_base": "uav_service_auxiliary/b09/native.py::make_b09_config (S7-S2 preset)",
    "set_switch": ("agent_count_generalization/configuration.py::make_config: "
                   "apply_algorithm_config(config, 'mappo'); k = 10 restored; "
                   "use_central_snapshot_in_flat_actor = True; calculate_and_set_buffer_sizes(); "
                   "validate_config()"),
    "ordinary_completed_segments": (
        "False (B09: True).  hmasd/agent.py refuses ordinary_completed_segments with "
        "disable_high_level_training, which the mappo switch sets; clear_buffers therefore takes "
        "the legacy path (env_timers and pending high-level records emptied at each update).  "
        "The team decision, and with it the central-snapshot refresh, stays on the episode step "
        "(_batched_assign_skills: env_steps % k == 0 | dones), so a lane live at a rollout "
        "boundary keeps its k = 10 cadence; only its skill-timer count restarts (none are live "
        "at production sizes when every episode is truncated at 3000 = rollout length; counted "
        "per rollout)"),
    "discriminator_batch_size": (
        "not set (ACG sets it to batch_size); hmasd/agent.py reads it only in "
        "update_discriminators, which the mappo switch disables, with default batch_size"),
    "training_shield": "B06 apply_feedback at the production layout (enter 0.0, exit 0.05)",
}


@dataclass(frozen=True)
class B02Spec(NativeSpec):
    seed: int = TRAINING_SEED
    lanes: int = 2
    rollouts: int = 200
    rollout_length: int = 3000
    episode_length: int = 3000
    eval_seeds: tuple[int, ...] = ()
    fact_seeds: tuple[int, ...] = ()
    checkpoint_every_transitions: int = CHECKPOINT_EVERY_TRANSITIONS

    @property
    def transitions_per_rollout(self) -> int:
        return self.lanes * self.rollout_length


def production_spec(seed: int) -> B02Spec:
    if int(seed) not in TRAINING_SEEDS:
        raise ValueError(f"unplanned B02 training seed {seed}; declared {TRAINING_SEEDS}")
    spec = B02Spec(seed=int(seed))
    assert_production(spec)
    return spec


def assert_production(spec: B02Spec) -> None:
    """The fixed exposure: 200 rollouts of 2 x 3000 = 1.2 M transitions, 6 checkpoints after c00."""
    if (spec.lanes, spec.rollout_length, spec.episode_length, spec.rollouts) != (2, 3000, 3000, 200):
        raise ValueError("B02 production is 2 lanes x rollout 3000 (episode 3000) x 200 rollouts")
    if spec.transitions != TOTAL_TRANSITIONS or spec.transitions != 200 * 2 * 3000:
        raise ValueError("B02 production exposure must be 1,200,000 transitions")
    if spec.checkpoint_every_transitions != CHECKPOINT_EVERY_TRANSITIONS:
        raise ValueError("B02 production checkpoints every 200,000 transitions")
    if (spec.ppo_epochs, spec.hidden_size, spec.gru_hidden_size) != (None, None, None):
        raise ValueError("B02 production keeps the S7 preset network and PPO settings")
    if len(checkpoint_rollouts(spec)) != 6 or checkpoint_rollouts(spec)[-1] != spec.rollouts:
        raise ValueError("B02 production saves six checkpoints after c00, the last at the endpoint")


def checkpoint_rollouts(spec: B02Spec) -> tuple[int, ...]:
    """Rollout indices (1-based, after their update) that save c01, c02, ... (``CHECKPOINT_RULE``)."""
    per_rollout = spec.transitions_per_rollout
    every = int(spec.checkpoint_every_transitions)
    if every <= 0:
        raise ValueError("checkpoint_every_transitions must be positive")
    marks = range(every, spec.transitions + 1, every)
    rollouts = sorted({math.ceil(mark / per_rollout) for mark in marks})
    if not rollouts or rollouts[-1] != spec.rollouts:
        rollouts.append(spec.rollouts)   # the endpoint is always saved
    return tuple(rollouts)


def apply_set_switch(config):
    """The ACG SET switch on an existing S7 config (same order as ACG ``make_config``)."""
    config = apply_algorithm_config(config, "mappo")
    # MAPPO's switch sets k = rollout_length + 1; restore the ten-step snapshot clock.
    config.k = 10
    config.use_central_snapshot_in_flat_actor = True
    config.calculate_and_set_buffer_sizes()
    config.validate_config()
    return config


def make_b02_config(spec: B02Spec):
    """B09's native config for ``spec`` + ``ordinary_completed_segments = False`` + SET switch."""
    config = make_config(spec)
    config.ordinary_completed_segments = False
    expected = {"seed": spec.seed, "num_envs": spec.lanes, "rollout_length": spec.rollout_length,
                "episode_length": spec.episode_length, "max_steps": spec.episode_length,
                "total_timesteps": spec.transitions, "n_agents": 8, "k": 10}
    mismatches = {key: (value, getattr(config, key, None)) for key, value in expected.items()
                  if getattr(config, key, None) != value}
    if mismatches:
        raise ValueError(f"B02 native configuration mismatch: {mismatches}")
    if config.lambda_return != 2.0 or config.lambda_e != 1.0:
        raise ValueError("B02 native reward coefficients changed")
    if config.use_obsnorm or config.use_statenorm:
        raise ValueError("B02 expects disabled observation/state normalizers")
    config = apply_set_switch(config)
    if (
        config.algorithm != "mappo" or config.k != 10 or config.n_Z != 1 or config.n_z != 1
        or not config.use_central_snapshot_in_flat_actor
        or not config.disable_high_level_training or not config.disable_discriminator_training
        or config.total_timesteps != spec.transitions
    ):
        raise ValueError("B02 SET switch did not produce the declared configuration")
    return config


# ``agent_count_generalization/configuration.py::config_dict`` fields, plus B02 additions.
ACG_FIELDS = """count_arm algorithm n_agents n_uavs n_users num_envs rollout_length
    episode_length k n_Z n_z state_dim obs_dim action_dim action_space_type
    gamma gae_lambda ppo_epochs num_mini_batch sequence_batch_size coordinator_batch_size
    high_level_batch_size high_level_buffer_size batch_size discriminator_batch_size
    lambda_e lambda_D lambda_d lambda_h lambda_l lambda_cd lambda_mi
    lr_coordinator lr_discoverer_actor lr_discoverer_critic lr_discriminator
    weight_decay clip_epsilon value_loss_coef max_grad_norm hidden_size embedding_dim
    n_heads n_encoder_layers n_decoder_layers gru_hidden_size use_valuenorm use_obsnorm
    use_statenorm use_lr_decay total_timesteps seed policy_interruption_mode
    use_central_snapshot_in_flat_actor disable_high_level_training
    disable_discriminator_training disable_discriminator_rewards collects_high_level_samples
    use_process_exploration use_horizon_window use_opt_compact""".split()
EXTRA_FIELDS = ("lambda_return", "max_steps", "ordinary_completed_segments", "baseline_algorithm",
                "scenario", "energy_stage", "use_entropy_annealing", "use_reward_annealing",
                "continuous_action_distribution", "central_snapshot_state_affine")


def _plain(value):
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)   # JSON has no inf/nan; the evaluator compares the same repr
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


def config_dict(config) -> dict[str, Any]:
    return {name: _plain(getattr(config, name, None)) for name in (*ACG_FIELDS, *EXTRA_FIELDS)}


def actor_input_width(config) -> int:
    """Flag-on actor input: own observation + central state + 8 observations + ego one-hot."""
    return (int(config.obs_dim) + int(config.state_dim)
            + int(config.n_agents) * int(config.obs_dim) + int(config.n_agents))


def spec_record(spec: B02Spec) -> dict[str, Any]:
    record = asdict(spec)
    record.update(transitions=spec.transitions, transitions_per_rollout=spec.transitions_per_rollout,
                  checkpoint_rollouts=list(checkpoint_rollouts(spec)))
    return record
