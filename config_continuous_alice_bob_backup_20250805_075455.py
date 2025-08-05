# HMASD config for the Continuous Alice and Bob litmus test
# Based on hyperparameters from the HMASD paper, Tables 1, 2, and 3.

class Config:
    # Environment parameters
    n_agents = 2
    state_dim = 16  # agent_pos (4) + button_pos (4) + diamond_pos (4) + button_pressed (2) + diamond_collected (2)
    obs_dim = 20    # Local observation: my_pos(2) + visible_items(6*3=18) = 20
    action_dim = 2  # 2D velocity vector
    action_bound = 1.0

    # HMASD parameters from paper
    n_Z = 2
    n_z = 4
    k = 50

    # Network parameters from paper (Table 1)
    hidden_size = 64
    embedding_dim = 64
    n_encoder_layers = 2
    n_decoder_layers = 2
    n_heads = 4  # Halved from 8 due to smaller hidden size
    gru_hidden_size = 64
    lr_coordinator = 5e-4
    lr_discoverer = 5e-4
    lr_discriminator = 5e-4

    # PPO parameters from paper (Table 1)
    gamma = 0.99
    gae_lambda = 0.95
    clip_epsilon = 0.1
    ppo_epochs = 4
    value_loss_coef = 1.0
    max_grad_norm = 0.5
    value_clip = 10.0
    batch_size = 64  # Standard batch size for discriminator training

    # HMASD loss weights from paper (Table 3, Alice and Bob)
    lambda_e = 0.0      # CRITICAL: Low-level policy is purely intrinsic
    lambda_D = 0.1
    lambda_d = 0.2
    lambda_h = 0.05      # High-level entropy
    lambda_l = 0.001     # Low-level entropy
    lambda_cd = 0.0
    lambda_mi = 0.0

    # Training parameters from paper (Table 2) - 修改为单环境测试
    num_envs = 1  # 修复：与训练脚本的单环境设置匹配
    rollout_length = 200  # 修复：与episode_length匹配，避免缓冲区溢出
    total_timesteps = 3e6
    episode_length = 200 # From environment definition
    eval_interval = 25000
    eval_episodes = 20
    
    # Other standard parameters
    use_valuenorm = True
    use_orthogonal = True
    gain = 0.01
    optimizer_epsilon = 1e-5
    weight_decay = 0.0
    num_mini_batch = 1 # From paper, 1 mini-batch per epoch

    # Learning rate decay (disabled to match paper)
    use_lr_decay = False

    # OPT module (disabled to match paper)
    use_opt = False
    
    # Unused parameters, set to default
    force_collection_threshold = 500
    use_reward_annealing = False

    def calculate_and_set_buffer_sizes(self):
        pass # Not needed for this simple config

    def update_env_dims(self, state_dim, obs_dim, n_agents=None):
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        if n_agents is not None:
            self.n_agents = n_agents
