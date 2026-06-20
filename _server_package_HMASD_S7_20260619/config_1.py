# HMASD算法配置参数 - 优化版
# 专用于解决场景4覆盖率低的问题

class Config:
    # Unified configuration revision. Generic class defaults below serve the
    # base/progressive scenarios; Scenario 7 values are applied by S7-S* presets.
    config_revision = "unified-scenario7-energy-v2-k25-20260619"
    scenario7_config_revision = "scenario7-energy-interface-v2"
    scenario = "base"
    scenario_label = ""
    experiment_preset = ""
    paper_data_level = "standard"
    collect_step_rewards = True
    collect_reward_components = True
    collect_performance_metrics = True
    enable_data_sampling = True
    data_sampling_interval = 10
    enable_data_compression = False
    paper_data_dir = None

    # 调试参数
    test_reward_mode = False
    # 环境参数
    n_agents = 6
    state_dim = None
    obs_dim = None
    action_dim = 3
    action_bound = 3.0
    action_space_type = 'continuous'

    use_worst_case_optimization = False
    # 通用环境参数 - 优化
    n_users = 30
    area_size = 8000               # [优化] 减小区域，增加密度
    height_range = (50, 200)
    max_speed = 30
    time_step = 1.0
    episode_length = 500            # [新增] 基础 episode 长度参数
    max_steps = episode_length       # [修复] 直接引用 episode_length，确保一致性
    max_hops = 5
    user_distribution = 'forced_relay_cluster'  # [优化] 使用簇分布
    use_fdma = True
    bandwidth = 20e6
    reward_type = 'load_balance'#"load_balance"         # [优化] 使用网络健康度奖励 _health
    w_load_balance = 0.35
    w_first_contact = 0#0.2
    w_repulsion = 0.0#0.3
    # load_balance模式下的网络健壮性惩罚：统计并惩罚回传/路由断联导致的QoS中断
    w_backhaul_outage = 0.8
    w_full_disconnect = 1.0
    w_coverage_drop = 0.2
    w_outage_memory = 0.25
    w_relay_break = 1.2
    w_backhaul_margin = 0.6
    backhaul_margin_target_mbps = 10.0
    outage_memory_decay = 0.90
    enable_backhaul_action_guard = True
    backhaul_guard_min_capacity_mbps = 5.0
    backhaul_guard_reject_speed_scale = 0.0
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
    n_remote_clusters = 1
    
    # 通信参数
    min_sinr = 3
    max_connections = 25
    carrier_frequency = 2e9
    tx_power = 23
    noise_power = -94
    ground_bs_tx_power = 30
    aclr_db = 45
    
    # 无人机初始化参数
    uav_init_mode = "start_area"
    uav_start_area_size = 500
    
    # 随机化控制参数
    randomize_bs = True
    randomize_users = True
    randomize_uav_start = True
    
    # 预测状态参数False
    enable_predictive_state = False
    prediction_horizon = 10
    
    # 卡尔曼滤波控制参数
    enable_cluster_kalman_filter = False

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
    observation_radius = 1500  # [优化] 调整观测半径
    max_observed_uavs = 6
    max_observed_users = 30
    max_observed_bs = 3

    # Scenario6 progressive presets. These fields are plain scalar/list config
    # entries so the same shape can be loaded from JSON/YAML later.
    progressive_stage = "S0"
    progressive_scale_mode = "train"
    scenario6_reward_type = None
    progressive_max_agents = 6
    progressive_max_users = 30
    progressive_max_ground_bs = 3
    progressive_fixed_agent_count = True
    progressive_s7_agents = 6

    # HMASD参数
    n_Z = 6
    n_z = 6
    k = 10
    discriminator_noise_std = 0#0.05
    # 网络参数 - 【弱判别器修复】增强配置
    hidden_size = 256                  # [增强] 从128提升到256，配合残差网络
    embedding_dim = 256
    n_encoder_layers = 2
    n_decoder_layers = 2
    n_heads = 8
    gru_hidden_size = 256
    lr_coordinator = 1e-4
    lr_discoverer_actor  = 1e-4     # 技能发现器学习率 (离散动作空间下提高学习率以确保有效更新)
    lr_discoverer_critic = 1e-4
    lr_discriminator = 1e-4             # [关键修复] 提高Discriminator学习率，加快学习速度
    #lr_prototype_discriminator = 3e-4    # [关键修复] 同步提高学习率

    # PPO参数
    gamma = 0.99
    gae_lambda = 0.95
    clip_epsilon = 0.2
    ppo_epochs = 15
    value_loss_coef = 1.0
    max_grad_norm = 0.5
    value_clip = 10.0

    # HMASD损失权重
    lambda_e = 1.0
    lambda_D = 0.05
    lambda_d = 0.02
    lambda_h = 0.07
    lambda_l = 0.05
    lambda_cd = 0.0
    lambda_mi = 0.0



    # 训练参数
    low_level_buffer_size = None
    batch_size = None
    discriminator_buffer_size = 1000000
    buffer_size = None
    high_level_buffer_size = None
    high_level_batch_size = None
    num_envs = 32
    rollout_length = 500
    total_timesteps = num_envs * rollout_length * 200

    # 严格对齐HMASD论文/标准实现：高层样本只在技能周期边界闭合。
    strict_hmasd_alignment = True

    # 非论文机制默认关闭；如需工程增强，可显式改回 True。
    use_entropy_annealing = False
    lambda_h_initial = 0.07   # 高层初始熵系数 (较高以鼓励探索)
    lambda_h_final = 0.01    # 高层最终熵系数
    lambda_l_initial = 0.05   # 低层初始熵系数
    lambda_l_final = 0.01    # 低层最终熵系数
    entropy_anneal_steps = 15e5 # 退火持续
    entropy_anneal_schedule = 'linear'

    eval_interval = episode_length * num_envs * 10
    eval_episodes = 8
    eval_rollout_threads = 8
    
    use_valuenorm = True
    use_obsnorm = False
    use_statenorm = False
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

    def __init__(self, preset=None):
        if preset:
            self.apply_preset(preset)

    def apply_preset(self, preset):
        preset = str(preset).upper()
        self.experiment_preset = preset

        if preset.startswith("S6-S"):
            self._apply_scenario6_progressive_preset(preset)
        elif preset.startswith("S4-R"):
            self._apply_scenario4_reward_preset(preset)
        elif preset.startswith("S7-S"):
            self._apply_scenario7_energy_preset(preset)
        else:
            raise ValueError(
                f"Unknown preset '{preset}'. Expected S4-R0/R1/R2/R3, "
                f"S6-S0/S1/S2/S3/S4/S5/S6/S7/S8/S9/S10, or S7-S1/S2/S3/S4."
            )

    def _disable_backhaul_robustness(self):
        self.w_backhaul_outage = 0.0
        self.w_full_disconnect = 0.0
        self.w_coverage_drop = 0.0
        self.w_outage_memory = 0.0
        self.w_relay_break = 0.0
        self.w_backhaul_margin = 0.0
        self.enable_backhaul_action_guard = False

    def _restore_backhaul_robustness(self):
        self.w_backhaul_outage = 0.8
        self.w_full_disconnect = 1.0
        self.w_coverage_drop = 0.2
        self.w_outage_memory = 0.25
        self.w_relay_break = 1.2
        self.w_backhaul_margin = 0.6

    def _apply_scenario4_reward_preset(self, preset):
        self.scenario = 4
        self.scenario_label = preset
        self.scenario6_reward_type = None
        self.progressive_stage = "S0"

        if preset == "S4-R0":
            self.reward_type = "naive"
            self.w_load_balance = 0.0
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._disable_backhaul_robustness()
        elif preset == "S4-R1":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._disable_backhaul_robustness()
        elif preset == "S4-R2":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._restore_backhaul_robustness()
            self.enable_backhaul_action_guard = False
        elif preset == "S4-R3":
            self.reward_type = "load_balance"
            self.w_load_balance = 0.35
            self.w_first_contact = 0.0
            self.w_repulsion = 0.0
            self._restore_backhaul_robustness()
            self.enable_backhaul_action_guard = True
        else:
            raise ValueError(f"Unknown scenario4 reward preset '{preset}'.")

    def _apply_scenario6_progressive_preset(self, preset):
        stage = preset.split("-", 1)[1]
        valid_stages = {f"S{i}" for i in range(11)}
        if stage not in valid_stages:
            raise ValueError(f"Unknown scenario6 stage preset '{preset}'.")

        self.scenario = 6
        self.scenario_label = preset
        self.progressive_stage = stage
        self.progressive_scale_mode = "train"
        self.scenario6_reward_type = "progressive_coverage_balance"
        self.reward_type = "load_balance"

        # Fixed maxima keep scenario6 state shape stable across staged profiles.
        self.progressive_max_agents = 6
        self.progressive_max_users = 30
        self.progressive_max_ground_bs = 3
        self.max_observed_bs = 3
        self.max_observed_uavs = max(getattr(self, "max_observed_uavs", 6), 6)
        self.max_observed_users = max(getattr(self, "max_observed_users", 30), 30)

        self._restore_backhaul_robustness()
        self.enable_backhaul_action_guard = stage in {"S6", "S7", "S8", "S9", "S10"}

    def _apply_scenario7_energy_preset(self, preset):
        stage = preset.split("-", 1)[1]
        if stage not in {"S1", "S2", "S3", "S4"}:
            raise ValueError(f"Unknown scenario7 energy stage preset '{preset}'.")

        self.scenario = 7
        self.active_config_revision = self.scenario7_config_revision
        self.scenario_label = preset
        self.energy_stage = stage
        self.energy_scale_mode = "train"
        self.energy_reward_type = "load_balance"
        self.reward_type = "load_balance"
        self.progressive_stage = "S0"
        self.scenario6_reward_type = None

        self.n_agents = 8
        self.n_users = 30
        self.n_ground_bs = 1
        self.max_observed_uavs = 8
        self.max_observed_users = max(getattr(self, "max_observed_users", 30), 30)
        self.action_dim = 4
        self.action_bound = 1.0
        self.scenario7_interface_version = 2
        self.continuous_action_distribution = "tanh_gaussian"
        self.continuous_logstd_init = -1.0
        self.continuous_logstd_min = -5.0
        self.continuous_logstd_max = 0.0
        self.lambda_l = 0.005
        self.lambda_l_initial = self.lambda_l
        self.lambda_l_final = self.lambda_l
        self.use_entropy_annealing = False
        self.k = 25 if stage == "S3" else 10
        self.scenario7_skill_interval_candidates = (10, 25, 50)
        self.scenario7_comparison_gate_enabled = stage == "S3"
        self.scenario7_comparison_gate_step = 2_400_000
        self.scenario7_gate_median_coverage_min = 0.45
        self.scenario7_gate_max_zero_coverage_episodes = 2

        self.episode_length = 500 if stage == "S1" else 1500
        self.max_steps = self.episode_length
        self.eval_interval = self.episode_length * self.num_envs * 10
        self.total_timesteps = (
            self.num_envs * self.rollout_length * 200
            if stage == "S1"
            else self.num_envs * self.episode_length * 200
        )

        self.max_energy_charging_stations = 2
        self.n_charging_stations = 2
        self.battery_capacity_wh = 200.0
        self.initial_battery_ratio_range = (0.75, 1.0)
        self.return_reserve_ratio = 0.10
        self.return_threshold_min = 0.25
        self.return_threshold_max = 0.60
        self.emergency_return_threshold = 0.05
        self.service_cutoff_threshold = 0.02
        self.charging_radius_m = 160.0
        self.charging_capture_radius_m = 20.0
        self.charging_power_w = 1000.0
        self.charging_hover_speed_threshold = 1.0
        self.docking_horizontal_speed_mps = 3.0
        self.docking_vertical_speed_mps = 1.0
        self.max_vertical_speed_mps = 5.0
        self.dock_request_threshold = 0.5
        self.limp_home_speed_mps = 3.0
        self.energy_reward_delta_min = -0.5
        self.energy_reward_delta_max = 0.25
        self.randomize_charging_stations = True
        self.charging_station_layout = "service_anchored"
        self.charging_station_margin_ratio = 0.08
        self.charging_station_min_separation_m = max(2 * self.charging_radius_m, self.area_size * 0.12)
        self.charging_station_jitter_m = self.area_size * 0.12

        self.user_distribution = "forced_relay_cluster"
        self.randomize_bs = True
        self._restore_backhaul_robustness()
        self.enable_backhaul_action_guard = True

        self.battery_enabled = stage in {"S2", "S3", "S4"}
        self.charging_enabled = self.battery_enabled
        self.charging_station_capacity = [1, 1]
        self.uav_failure_enabled = stage == "S4"
        self.uav_failure_probability = 0.001 if stage == "S4" else 0.0
        self.uav_failure_duration_range = (20, 60)
        self.uav_failure_min_active = 6

        self.w_first_contact = 0.0
        self.w_energy_backhaul_potential = 0.20
        self.w_energy_motion = 0.02
        self.w_energy_efficiency = 0.0
        self.w_low_battery = 0.10
        self.w_depleted_battery = 0.30
        self.w_charge_progress = 0.20
        self.w_charging_queue = 0.02
        self.w_station_approach = 0.10
        self.w_charging_arrival = 0.10
        self.w_energy_failure = 0.20
        self.w_energy_failure_event = 0.0

        self.user_movement_model = "rpgm"
        stage_speeds = {
            "S1": (2.0, 2.0),
            "S2": (3.0, 3.0),
            "S3": (5.0, 5.0),
            "S4": (8.0, 10.0),
        }
        self.user_max_speed, self.cluster_migration_speed = stage_speeds[stage]
        self.cluster_pause_time_range = (0, 3) if stage == "S4" else (1, 4)
        self.user_pause_time_range = (0, 2)

        self._validate_scenario7_preset()

    def _validate_scenario7_preset(self):
        """Validate the complete Scenario 7 contract immediately after preset application."""
        expected = {
            "n_agents": 8,
            "action_dim": 4,
            "action_bound": 1.0,
            "charging_power_w": 1000.0,
            "max_observed_uavs": 8,
            "continuous_action_distribution": "tanh_gaussian",
            "scenario7_interface_version": 2,
            "lambda_l": 0.005,
            "use_entropy_annealing": False,
        }
        errors = [
            f"{name}={getattr(self, name, None)!r}, expected {value!r}"
            for name, value in expected.items()
            if getattr(self, name, None) != value
        ]
        if self.energy_stage == "S3" and self.k != 25:
            errors.append(f"S7-S3 k={self.k!r}, expected 25")
        if self.episode_length % self.k != 0:
            errors.append(
                f"episode_length={self.episode_length} must be divisible by k={self.k}"
            )
        capacities = tuple(self.charging_station_capacity)
        if capacities != (1, 1):
            errors.append(
                f"charging_station_capacity={capacities!r}, expected (1, 1)"
            )
        if errors:
            raise ValueError(
                "Invalid Scenario 7 preset configuration:\n- " + "\n- ".join(errors)
            )

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
