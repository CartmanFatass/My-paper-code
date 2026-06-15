from config_1 import Config as BaseConfig


class Config(BaseConfig):
    """Small smoke-test configuration for HMASD scenario 4."""

    # Environment size
    n_agents = 3
    n_uavs = n_agents
    n_users = 8
    area_size = 2500
    episode_length = 16
    max_steps = episode_length
    n_clusters = 2
    n_remote_clusters = 0
    max_connections = 8
    observation_radius = 1200
    max_observed_uavs = 3
    max_observed_users = 8
    max_observed_bs = 1

    # Use the actual scenario_base training path.
    action_space_type = 'discrete'
    action_dim = 3

    # Smaller networks for fast CPU smoke tests.
    n_Z = 3
    n_z = 3
    k = 4
    hidden_size = 64
    embedding_dim = 64
    n_encoder_layers = 1
    n_decoder_layers = 1
    n_heads = 4
    gru_hidden_size = 64

    # Short PPO/update settings.
    ppo_epochs = 1
    num_mini_batch = 1
    coordinator_batch_size = 8
    sequence_batch_size = 8
    discriminator_batch_size = 16
    discriminator_buffer_size = 512

    # Minimal rollout.
    num_envs = 1
    rollout_length = 16
    total_timesteps = num_envs * rollout_length
    eval_interval = total_timesteps + 1
    eval_episodes = 1
    eval_rollout_threads = 1

    # Keep correctness checks active, avoid optional schedules.
    use_valuenorm = True
    strict_hmasd_alignment = True
    use_obsnorm = False
    use_statenorm = False
    use_entropy_annealing = False
    use_lr_decay = False
    use_worst_case_optimization = False
    use_opt = False
    use_opt_coordinator = False
    use_opt_discoverer_actor = False
    use_opt_discoverer_critic = False

    # Keep forced high-level collection responsive in tiny rollouts.
    force_collection_threshold = 16
