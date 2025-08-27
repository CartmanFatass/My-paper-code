# HMASD算法配置参数 - 基于论文《Hierarchical Multi-Agent Skill Discovery》附录E中的超参数设置
# 专用于场景4和场景5

class Config:
    # 调试参数
    test_reward_mode = False#True  # 是否测试奖励函数
    # 环境参数
    # 注意：实际环境中应该获取这些值
    n_agents = 6     # 无人机数量 (默认值，可通过代码设置)
    state_dim = None  # 全局状态维度（将在环境初始化时获取）
    obs_dim = None    # 单个智能体观测维度（将在环境初始化时获取）
    action_dim = 3    # 每个智能体输出3D速度向量
    action_bound = 3.0 # 动作输出的最大值（用于tanh缩放）
    
    # 通用环境参数
    n_users = 30                    # 用户数量
    area_size = 8000               # 区域大小 (米)
    max_hops = 5                   # 最大跳数
    user_distribution = 'coverage_hole'  # 用户分布类型
    channel_model = 'probabilistic'      # 信道模型
    use_fdma = True                      # FDMA
    bandwidth = 20e6                     # 每个无人机的带宽 (Hz)
    reward_type = "health"               # 奖励类型: "naive" (仅覆盖率) 或 "health" (网络健康度)
    
    # 场景4参数
    n_clusters = 5                 # 用户簇数量
    cluster_std = 80              # 簇内用户分布标准差 (米)
    central_area_ratio = 0.5      # 中心用户区域占总区域的比例
    
    # 局部观测参数
    observation_radius = 1500  # [新增] 固定的侦测范围 (米)
    max_observed_uavs = 6     # 原为6，可以适当增大以容纳更多邻居
    max_observed_users = 30   # 原为30
    max_observed_bs = 2       # [新增] 最大观测基站数量

    # HMASD参数 - 优化技能探索参数
    n_Z = 3           # [关键] 降低团队技能数量
    n_z = 3          # [关键] 降低个体技能数量
    k = 50           # [紧急修复] 增加技能分配间隔，从20增加到100，让智能体充分探索每个技能

    # 网络参数 - 基于论文Table 1
    hidden_size = 128         # 隐藏层大小 (论文中为64)
    embedding_dim = 128       # 嵌入维度 (与hidden_size保持一致)
    n_encoder_layers = 2     # 编码器层数
    n_decoder_layers = 2     # 解码器层数
    n_heads = 8              # 多头注意力头数 (必须为偶数以支持nested tensor优化)
    gru_hidden_size = 128     # GRU隐藏层大小 (与hidden_size保持一致)
    lr_coordinator = 1e-4    # 技能协调器学习率 参考原论文
    lr_discoverer = 1e-4     # 技能发现器学习率 参考原论文
    lr_discriminator = 1e-4  # 参考原论文
    lr_prototype_discriminator = 1e-4 # 原型判别器学习率 (新增)

    # PPO参数 - 基于论文Table 1
    gamma = 0.99             # 折扣因子
    gae_lambda = 0.95        # GAE参数
    clip_epsilon = 0.2       # PPO裁剪参数 (更保守以稳定学习)
    ppo_epochs = 10          # [关键] 减少PPO迭代，防止过拟合
    value_loss_coef = 1.0    # MAPPO标准价值损失系数
    max_grad_norm = 0.5      # MAPPO标准梯度裁剪
    value_clip = 10.0        # [新增] 价值函数裁剪范围，用于Value Normalization

    # HMASD损失权重 - 根据代码审查建议调整
    # 优先保证外在奖励，以确保智能体首先学习解决任务
    lambda_e = 1.0           # 外在奖励权重
    lambda_D = 0.1          # 团队技能判别器奖励权重
    lambda_d = 0.5          # 个体技能判别器奖励权重
    lambda_h = 0.001          # [优化] 提高高层策略熵权重，从0.001提高到0.01，鼓励技能多样性
    lambda_l = 0.01           # [优化] 提高低层策略熵权重，从0.01提高到0.1，鼓励动作探索
    lambda_cd = 0.0          # 对比散度损失权重 (禁用)
    lambda_mi = 0.1          # 互信息奖励权重 (新增)

    # 训练参数 - 部分基于论文Table 1和Table 2
    # buffer和batch大小将根据环境参数动态计算
    low_level_buffer_size = None   # 低层经验回放缓冲区大小 (动态计算)
    batch_size = None              # 低层批处理大小 (动态计算, 兼容旧代码)
    discriminator_buffer_size = 500000 # 判别器off-policy经验缓冲区大小
    buffer_size = None             # 兼容性别名，指向low_level_buffer_size
    high_level_buffer_size = None  # 高层经验缓冲区大小 (动态计算)
    high_level_batch_size = None   # 高层更新的批处理大小 (动态计算)
    num_envs = 32            # 并行环境数量 (论文中rollout threads为32)
    rollout_length = 400    # [调整] 增加rollout长度，从2500增加到5000，确保容纳足够的技能周期
    total_timesteps = num_envs*rollout_length*400 #4e6    # 总时间步数 (论文中SMAC为2e6)
    
    def set_short_test_mode(self):
        """设置短时间测试模式"""
        self.total_timesteps = 5000  # 短时间测试
        self.eval_interval = 1000    # 更频繁的评估
        self.rollout_length = 50     # 更短的rollout
        self.buffer_size = 1000      # 更小的缓冲区
        self.batch_size = 500        # 更小的批次
        self.high_level_batch_size = 32  # 更小的高层批次
    episode_length = 400    # 每个episode的最大长度 (基于观察到的实际行为)
    eval_interval = episode_length*num_envs*10   # 评估间隔 
    eval_episodes = 4      # 评估时的episode数量 (论文中SMAC为100)
    eval_rollout_threads = 4 # 评估时的并行线程数 (论文中SMAC为4)
    
    # 其他论文中提到的参数
    use_valuenorm = True     # 使用价值标准化
    use_obsnorm = True       # 使用观测标准化 (新增，解决输入尺度问题)
    use_orthogonal = True    # 使用正交初始化
    gain = 0.01              # 增益
    optimizer_epsilon = 1e-5 # 优化器epsilon
    weight_decay = 0.0       # 权重衰减 (根据建议移除)
    num_mini_batch = 4    # mini batch数量 (基于PPO标准框架)

    # 学习率衰减参数False
    use_lr_decay = False                    # 是否启用学习率衰减
    lr_decay_schedule = 'linear'           # 衰减计划 ('linear', 'cosine', 'exponential')
    lr_decay_steps = 2000000               # 学习率衰减总步数 (约50%的训练时间)
    coordinator_lr_decay_factor = 0.2      # 协调器最终学习率为初始的20%
    discoverer_lr_decay_factor = 0.2       # 发现器最终学习率为初始的20%
    discriminator_lr_decay_factor = 0.3    # 判别器衰减得慢一些，保持判别能力
    use_huber_loss = True    # 使用Huber损失
    huber_delta = 10         # Huber delta
    
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
    w_connectivity = 0.5  # 奖励网络骨干的形成
    w_diversity = 1.0     # 大力奖励角色分工
    w_coverage = 1.0      # 奖励最终的任务目标
    w_dispersion = 0.05   # 轻微惩罚聚集，鼓励分散
    
    # 权重退火参数 - 用于解决奖励空窗期问题
    use_reward_annealing = False         # 禁用额外模块
    w_intrinsic_initial = 5.0          # 内在奖励初始权重倍数（早期强调探索）
    w_intrinsic_final = 0.1            # 内在奖励最终权重倍数（后期回到正常水平）
    w_extrinsic_initial = 0.05          # 外部奖励初始权重倍数（早期弱化利用）
    w_extrinsic_final = 2.0            # 外部奖励最终权重倍数（后期强化利用）
    anneal_steps = 2000000             # 权重退火总步数（约25%的训练时间）
    anneal_schedule = 'linear'         # 退火计划（'linear' 或 'cosine'）

    # --- 场景4: 信念地图与势函数参数 ---
    belief_decay_factor = 0.1                # 信念衰减因子
    recon_interval = 100                     # 信念重构间隔
    recon_strength = 0.1                     # 信念重构强度

    # --- 场景4: 环境和空间参数 ---
    min_sinr = 3.0                          # 最小信噪比
    max_connections = 25                     # 最大连接数
    uav_init_mode = 'random'#'start_area'            # 无人机初始化模式
    uav_start_area_size = 100               # 起始区域大小（米）
    grid_resolution = 100                    # 栅格分辨率 (场景5使用100, 场景4使用50)


    # --- 场景5: 动态环境与信念地图参数 ---
    users_dynamic = True         # 用户是否动态移动
    user_max_speed = 5           # 用户最大移动速度 (m/s)
    belief_decay = 0.99          # 信念地图衰减因子


    # --- 可视化和绘图参数 ---
    trajectory_record_interval = 1      # 轨迹记录间隔（每N步记录一次位置，1=每步记录）
    max_trajectory_points = 10000       # 最大轨迹点数（增大以支持完整记录）
    enable_trajectory_points = True     # 是否在轨迹上显示路径点标记
    trajectory_point_size = 3           # 路径点标记大小（减小以避免图像过于密集）
    record_skill_change_points = True   # 是否在技能切换时强制记录
    record_episode_end = True           # 是否强制记录episode结束位置
    adaptive_interval = False           # 是否使用自适应间隔（暂时禁用）
    min_trajectory_interval = 1         # 最小记录间隔
    max_trajectory_interval = 50        # 最大记录间隔
    
    # --- 轨迹记录优化参数 ---
    full_trajectory_recording = True    # 启用完整轨迹记录模式（记录每一步）
    enable_trajectory_smoothing = True  # 启用轨迹平滑（减少噪声）

    # --- Paper Data存储空间优化参数 ---
    # 数据收集级别控制
    paper_data_level = 'standard'       # 数据收集级别: 'minimal', 'standard', 'detailed'
    enable_data_sampling = True         # 启用数据采样（减少存储频率）
    data_sampling_interval = 50         # 数据采样间隔（每N步采样一次，增加间隔减少数据量）
    enable_data_aggregation = True      # 启用数据聚合（将步级数据聚合为episode级）
    enable_incremental_export = True    # 启用增量导出（只导出新数据）
    enable_data_compression = True      # 启用数据压缩
    max_export_files = 10               # 最大保留导出文件数量（实现数据轮转）
    
    # 导出间隔控制
    export_interval_multiplier = 5      # 导出间隔倍数（相对于原始1000步）
    
    # 内存优化
    max_step_data_buffer = 500          # 最大步级数据缓冲区大小（减少内存占用）
    auto_clear_old_data = True          # 自动清理旧数据
    
    # 选择性数据收集
    collect_step_rewards = False        # 是否收集每步的奖励数据（减少存储）
    collect_skill_diversity = True      # 是否收集技能多样性数据  
    collect_performance_metrics = True  # 是否收集性能指标
    collect_reward_components = False   # 是否收集详细的奖励组成（减少存储）
    
    # 强制收集参数 - 解决环境样本贡献不均问题
    force_collection_threshold = 500    # 环境距离上次贡献超过此步数时强制收集高层样本

    def calculate_and_set_buffer_sizes(self):
        """根据标准PPO框架计算buffer和batch大小"""
        if self.n_agents is None:
            print("警告: n_agents 未设置，无法动态计算buffer大小。")
            return

        # === 标准PPO计算（基于您的框架） ===
        buffer_size = self.num_envs * self.rollout_length           # 80,000
        minibatch_size = buffer_size // self.num_mini_batch         # 4,000
        
        # === 多智能体适配 ===
        # 低层buffer：考虑所有智能体的总经验
        self.low_level_buffer_size = buffer_size * self.n_agents
        # 低层batch：每次训练使用的样本数（考虑所有智能体）
        self.batch_size = minibatch_size * self.n_agents
        # 兼容性别名
        self.buffer_size = self.low_level_buffer_size
        
        # === 高层计算保持不变 ===
        total_high_level_samples = self.num_envs * (self.rollout_length // self.k)
        self.high_level_buffer_size = total_high_level_samples
        self.high_level_batch_size = min(total_high_level_samples, 128)

        print("="*60)
        print("PPO标准参数关系:")
        print(f"  num_envs × rollout_length = buffer_size")
        print(f"  {self.num_envs} × {self.rollout_length} = {buffer_size:,}")
        print(f"  buffer_size ÷ num_mini_batch = minibatch_size") 
        print(f"  {buffer_size:,} ÷ {self.num_mini_batch} = {minibatch_size:,}")
        print("="*20)
        print("多智能体最终值:")
        print(f"  low_level_buffer_size: {self.low_level_buffer_size:,}")
        print(f"  batch_size: {self.batch_size:,}")
        print("="*60)

    def validate_config(self):
        """验证配置参数的有效性"""
        # 确保注意力头数为偶数，避免PyTorch nested tensor警告
        if self.n_heads % 2 != 0:
            print(f"警告: n_heads={self.n_heads} 为奇数，PyTorch nested tensor优化将被禁用")
            print(f"建议使用偶数个注意力头以获得更好的性能")
            # 自动调整为最近的偶数
            self.n_heads = self.n_heads + 1 if self.n_heads > 1 else 2
            print(f"已自动调整 n_heads 为 {self.n_heads}")
        
        # 确保embedding_dim能被n_heads整除
        if self.embedding_dim % self.n_heads != 0:
            print(f"警告: embedding_dim={self.embedding_dim} 不能被 n_heads={self.n_heads} 整除")
            # 调整embedding_dim为n_heads的倍数
            self.embedding_dim = ((self.embedding_dim // self.n_heads) + 1) * self.n_heads
            print(f"已自动调整 embedding_dim 为 {self.embedding_dim}")
        
        # 确保最小网络尺寸
        min_hidden_size = 8
        if self.hidden_size < min_hidden_size:
            print(f"警告: hidden_size={self.hidden_size} 过小，可能导致训练不稳定")
            self.hidden_size = max(self.hidden_size, min_hidden_size)
            print(f"已调整 hidden_size 为 {self.hidden_size}")
        
        # 确保GRU隐藏层大小合理
        if self.gru_hidden_size < min_hidden_size:
            self.gru_hidden_size = max(self.gru_hidden_size, min_hidden_size)
            print(f"已调整 gru_hidden_size 为 {self.gru_hidden_size}")

    def update_env_dims(self, state_dim, obs_dim, n_agents=None):
        """更新环境维度并动态计算buffer大小"""
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        if n_agents is not None:
            self.n_agents = n_agents
        
        print(f"环境维度已更新：state_dim={state_dim}, obs_dim={obs_dim}, n_agents={self.n_agents}")
        
        # 验证配置参数
        self.validate_config()
        
        # 动态计算并设置buffer大小
        self.calculate_and_set_buffer_sizes()
