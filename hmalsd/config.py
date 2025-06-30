# HMASD算法配置参数

class Config:
    # 环境参数
    # 注意：实际环境中应该获取这些值
    n_agents = 10  # 无人机数量上限
    state_dim = None  # 全局状态维度（将在环境初始化时获取）
    obs_dim = None    # 单个智能体观测维度（将在环境初始化时获取）
    action_dim = 3    # 每个智能体输出3D速度向量

    # HMASD参数
    n_Z = 10          # 团队技能数量 (在HMALS中被分层技能替代)
    n_z = 10          # 个体技能数量
    k = 50            # 技能分配间隔

    # HMALS & Louvain 技能发现参数
    n_louvain_skills = 32      # 假设的Louvain技能最大数量 (用于网络输出维度)
    louvain_resolution = 0.05  # Louvain算法的分辨率参数
    louvain_min_cluster_size = 4 # 最小有效社区大小
    louvain_update_interval = 10000 # 更新Louvain技能树的频率（以时间步为单位）

    # 网络参数
    hidden_size = 256        # 隐藏层大小
    embedding_dim = 128      # 嵌入维度
    n_encoder_layers = 3     # 编码器层数
    n_decoder_layers = 3     # 解码器层数
    n_heads = 8             # 多头注意力头数
    gru_hidden_size = 256    # GRU隐藏层大小
    lr_coordinator = 3e-4    # 技能协调器学习率
    lr_discoverer = 3e-4     # 技能发现器学习率
    lr_discriminator = 3e-4  # 技能判别器学习率

    # OPT模块参数 (可选)
    use_opt = False          # 是否使用OPT模块
    opt_num_prototypes = 8   # OPT原型数量
    opt_prototype_dim = 128  # OPT原型维度
    opt_layers = 2           # OPT层数

    # PPO参数
    use_valuenorm = True     # 是否使用Value Normalization
    gamma = 0.99             # 折扣因子
    gae_lambda = 0.95        # GAE参数
    clip_epsilon = 0.2       # PPO裁剪参数
    ppo_epochs = 15          # PPO迭代次数
    value_loss_coef = 0.5    # 价值损失系数
    entropy_coef = 0.01      # 熵损失系数
    max_grad_norm = 0.5      # 最大梯度范数

    # HMALS损失权重
    lambda_e = 1.0           # 外部奖励权重
    # lambda_D is removed for HMALS
    lambda_d = 0.1           # 个体技能判别器奖励权重
    lambda_h = 0.01          # 高层策略熵权重
    lambda_l = 0.01          # 低层策略熵权重
    lambda_cd = 0.1          # 对比散度损失权重 (用于OPT)

    # 训练参数
    trajectory_buffer_size = 50000 # 用于构建Louvain图的轨迹缓冲区大小
    buffer_size = 1024       # 经验回放缓冲区大小
    batch_size = 128         # 批处理大小
    high_level_batch_size = 16  # 高层更新的批处理大小（较小值使高层网络能在早期开始更新）
    num_envs = 16            # 并行环境数量
    total_timesteps = 5e6    # 总时间步数
    eval_interval = 1000     # 评估间隔

    def update_env_dims(self, state_dim, obs_dim):
        """更新环境维度"""
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        print(f"环境维度已更新：state_dim={state_dim}, obs_dim={obs_dim}")
