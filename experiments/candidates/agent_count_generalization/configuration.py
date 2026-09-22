"""Prospective six-fit S1 count-transfer exploration; no CLI tuning grid."""
from dataclasses import dataclass

from configs.config_1 import Config
from hmasd.baselines import apply_algorithm_config

DIRECTION = "agent_count_generalization"
SEEDS = {"H6": (914201, 914307, 914413), "SET": (915201, 915307, 915413)}


@dataclass(frozen=True)
class FitSpec:
    train_n: int = 6
    test_ns: tuple = (4, 6, 8)
    horizon: int = 500
    train_lanes: int = 16
    eval_lanes: int = 16
    rollouts: int = 45
    panels: tuple = (0, 15, 30, 45)
    hidden_size: int = 256
    n_heads: int = 8
    n_layers: int = 2
    ppo_epochs: int = 15
    sequence_batch_size: int = 32
    coordinator_batch_size: int = 1280
    torch_threads: int = 4


DEFAULT_SPEC = FitSpec()


def make_config(arm, envs, seed, spec=DEFAULT_SPEC):
    if arm not in SEEDS:
        raise ValueError(f"unknown arm {arm}")
    config = Config()
    config.n_uavs = envs[0].n_uavs
    config.n_users = 50
    config.num_envs = len(envs)
    config.rollout_length = config.episode_length = spec.horizon
    config.k = 10
    config.seed = int(seed)
    config.hidden_size = config.embedding_dim = config.gru_hidden_size = spec.hidden_size
    config.n_heads = spec.n_heads
    config.n_encoder_layers = config.n_decoder_layers = spec.n_layers
    config.policy_interruption_mode = "off"
    config.use_obsnorm = config.use_statenorm = False
    config.use_lr_decay = False
    config.n_Z = config.n_z = 6
    config.ppo_epochs = spec.ppo_epochs
    config.sequence_batch_size = spec.sequence_batch_size
    config.coordinator_batch_size = spec.coordinator_batch_size
    config.total_timesteps = spec.train_lanes * spec.horizon * spec.rollouts
    config.update_env_dims(state_dim=envs[0].state_dim, obs_dim=envs[0].obs_dim,
                           n_agents=envs[0].n_uavs)
    config = apply_algorithm_config(config, "hmasd" if arm == "H6" else "mappo")
    # MAPPO's algorithm switch also changes the recurrent chunk length. Restore
    # the declared ten-step information clock and truncated-BPTT length.
    config.k = 10
    config.use_central_snapshot_in_flat_actor = arm == "SET"
    config.count_arm = arm
    config.calculate_and_set_buffer_sizes()
    config.discriminator_batch_size = config.batch_size
    config.validate_config()
    if config.state_dim != 133 or config.obs_dim != 104:
        raise ValueError("unexpected native S1 observation/state contract")
    return config


def config_dict(config):
    fields = """count_arm algorithm n_agents n_uavs n_users num_envs rollout_length
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
    return {name: getattr(config, name, None) for name in fields}
