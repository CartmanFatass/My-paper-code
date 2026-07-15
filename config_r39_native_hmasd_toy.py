"""Exact fixed-N native-HMASD toy anchor configuration."""

from config_1 import Config as BaseConfig


class Config(BaseConfig):
    """Small native coordinator profile for the existing role-free toy."""

    algorithm = "hmasd_original"
    scenario = "two_timescale_role_free_actions"
    scenario_label = "r39_native_hmasd_toy"

    n_agents = 2
    n_uavs = 2
    max_observed_uavs = 2
    state_dim = 6
    obs_dim = 4
    action_dim = 2
    action_bound = 1.0
    action_space_type = "continuous"
    episode_length = 40
    max_steps = 40
    k = 5
    r39_toy_k0 = 5
    r39_toy_slow_period_blocks = 6

    n_Z = 4
    n_z = 4

    hidden_size = 32
    embedding_dim = 32
    n_encoder_layers = 1
    n_decoder_layers = 1
    n_heads = 4
    coordinator_dropout = 0.0
    gru_hidden_size = 32

    ppo_epochs = 3
    num_mini_batch = 4
    coordinator_batch_size = 128
    sequence_batch_size = 32
    discriminator_batch_size = 128

    num_envs = 16
    rollout_length = 40
    total_timesteps = 12_800
    eval_episodes = 32
    eval_rollout_threads = 16
    eval_interval = total_timesteps

    strict_hmasd_alignment = True
    use_valuenorm = True
    use_obsnorm = False
    use_statenorm = False
    use_entropy_annealing = False
    use_reward_annealing = False
    use_lr_decay = False

    use_opt = False
    use_opt_coordinator = False
    use_opt_discoverer_actor = False
    use_opt_discoverer_critic = False
    use_opt_compact = False
    use_team_bridge = False
    use_horizon_window = False
    use_process_exploration = False
    use_discrete_skill_lifetimes = False
    use_process_reward_for_discoverer = False

    disable_discriminator_training = True
    disable_discriminator_rewards = True
    lambda_D = 0.0
    lambda_d = 0.0
    use_team_code_discriminator = False
    use_individual_skill_discriminator = False
    discriminator_condition_on_compact = False
    discriminator_condition_on_team_code = False

    r39_native_hmasd_toy = True
    r39_native_toy_full_refresh = True
    r39_native_toy_fixed_primitives = True
    r39_native_toy_fixed_skill_action_schema = "axis4_xy_v1"
    scenario7_comparison_gate_enabled = False
