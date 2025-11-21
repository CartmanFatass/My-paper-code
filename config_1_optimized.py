# HMASD算法配置参数 - 优化版
# 专用于解决场景4覆盖率低的问题

class Config:
    # 调试参数
    test_reward_mode = False
    # 环境参数
    n_agents = 6
    state_dim = None
    obs_dim = None
    action_dim = 3
    action_bound = 3.0
    action_space_type = 'discrete'
    
    # 通用环境参数 - 优化
    n_users = 30
    area_size = 8000               # [优化] 减小区域，增加密度
    height_range = (50, 200)
    max_speed = 30
    time_step = 1.0
    max_steps = 1500                # [优化] 匹配 episode_length
    max_hops = 5
    user_distribution = 'forced_relay_cluster'  # [优化] 使用簇分布
    use_fdma = True
    bandwidth = 20e6
    reward_type = "health"         # [优化] 使用网络健康度奖励
    
    # 用户移动参数
    user_max_speed = 15.0
    user_movement_model = "rpgm"
    
    # RPGM参数
    cluster_migration_speed = 15.0
    cluster_pause_time_range = (0, 5)
    user_pause_time_range = (0, 3)
    
    # 场景4参数
    n_clusters = 5
    cluster_std = 80
    central_area_ratio = 0.5
    base_station_distance_factor = 0.8
    n_ground_bs = 1
    
    # 通信参数
    min_sinr = 3
    max_connections = 25
    carrier_frequency = 2e9
    tx_power = 23
    noise_power = -94
    ground_bs_tx_power = 30
    aclr_db = 45
    
    # 无人机初始化参数
    uav_init_mode = "random"
    uav_start_area_size = 500
    
    # 随机化控制参数
    randomize_bs = True
    randomize_users = True
    randomize_uav_start = True
    
    # 预测状态参数False
    enable_predictive_state = False
    prediction_horizon = 10

    # 软切换和动态簇管理参数
    enable_soft_handover = True
    serving_set_size = 3
    handover_hysteresis_db = 3.0
    w_serving_set_cost = 0.01
    
    # 状态增强参数
    enhanced_state = False    # 是否启用增强状态模式（多头嵌入）
    state_component_dims = None  # 状态组件维度（增强状态模式需要）
    w_entropy = 0.0          # 熵权重（用于增强状态模式）
    
    # 局部观测参数
    observation_radius = 1000  # [优化] 调整观测半径
    max_observed_uavs = 6
    max_observed_users = 30
    max_observed_bs = 2

    # HMASD参数
    n_Z = 3
    n_z = 3
    k = 10

    # 网络参数 - 【弱判别器修复】增强配置
    hidden_size = 128                    # [增强] 从128提升到256，配合残差网络
    embedding_dim = 128
    n_encoder_layers = 2
    n_decoder_layers = 2
    n_heads = 8
    gru_hidden_size = 128
    lr_coordinator = 1e-4
    lr_discoverer_actor  = 1e-4     # 技能发现器学习率 (离散动作空间下提高学习率以确保有效更新)
    lr_discoverer_critic = 1e-3
    lr_discriminator = 3e-4              # [关键修复] 提高Discriminator学习率，加快学习速度
    lr_prototype_discriminator = 3e-4    # [关键修复] 同步提高学习率

    # PPO参数
    gamma = 0.99
    gae_lambda = 0.95
    clip_epsilon = 0.2
    ppo_epochs = 10
    value_loss_coef = 1.0
    max_grad_norm = 0.5
    value_clip = 10.0

    # HMASD损失权重
    lambda_e = 1.0
    lambda_D = 0.1
    lambda_d = 0.5
    lambda_h = 0.001
    lambda_l = 0.01
    lambda_cd = 0.0
    lambda_mi = 0.1

    # 训练参数
    low_level_buffer_size = None
    batch_size = None
    discriminator_buffer_size = 500000
    buffer_size = None
    high_level_buffer_size = None
    high_level_batch_size = None
    num_envs = 32
    rollout_length = 1500
    total_timesteps = num_envs * rollout_length * 400
    
    episode_length = 1500
    eval_interval = episode_length * num_envs * 10
    eval_episodes = 4
    eval_rollout_threads = 4
    
    use_valuenorm = True
    use_obsnorm = True
    use_orthogonal = True
    gain = 0.01
    optimizer_epsilon = 1e-5
    weight_decay = 0.0
    num_mini_batch = 4

    use_lr_decay = False
    
    # OPT (Interaction Pattern Disentangling) 参数 - 基于论文《Interaction Pattern Disentangling for Multi-Agent Reinforcement Learning》
    use_opt = False                    # 总开关：是否使用OPT模块
    use_opt_coordinator = False        # 禁用额外模块
    use_opt_discoverer_actor = False   # 禁用额外模块
    use_opt_discoverer_critic = False  # 禁用额外模块
    opt_num_prototypes = 4   # 交互原型数量 (论文中N=4)
    opt_prototype_dim = 32   # 交互原型特征维度 (论文中d_x=32)
    opt_alpha = 0.5          # 对比散度损失权重 (论文中α=0.5)
    opt_beta = 0.1           # 条件互信息损失权重 (论文中β=0.1)
    opt_layers = 2           # OPT模块层数 (论文中K=2)
    
    # --- 场景4: 网络健康度奖励权重 (Network Health Score) ---
    w_connectivity = 0.5
    w_diversity = 1.0
    w_coverage = 1.0
    w_dispersion = 0.05
    
    # 强制收集参数 - 解决环境样本贡献不均问题
    force_collection_threshold = 500    # 环境距离上次贡献超过此步数时强制收集高层样本

    def calculate_and_set_buffer_sizes(self):
        if self.n_agents is None:
            print("警告: n_agents 未设置，无法动态计算buffer大小。")
            return
        buffer_size = self.num_envs * self.rollout_length
        minibatch_size = buffer_size // self.num_mini_batch
        self.low_level_buffer_size = buffer_size * self.n_agents
        self.batch_size = minibatch_size * self.n_agents
        self.buffer_size = self.low_level_buffer_size
        total_high_level_samples = self.num_envs * (self.rollout_length // self.k)
        self.high_level_buffer_size = total_high_level_samples
        self.high_level_batch_size = min(total_high_level_samples, 128)

    def validate_config(self):
        if self.n_heads % 2 != 0:
            self.n_heads = self.n_heads + 1 if self.n_heads > 1 else 2
        if self.embedding_dim % self.n_heads != 0:
            self.embedding_dim = ((self.embedding_dim // self.n_heads) + 1) * self.n_heads

    def update_env_dims(self, state_dim, obs_dim, n_agents=None):
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        if n_agents is not None:
            self.n_agents = n_agents
        self.validate_config()
        self.calculate_and_set_buffer_sizes()
