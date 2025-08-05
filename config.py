# HMASD算法配置参数

class Config:
    # 环境参数
    # 注意：实际环境中应该获取这些值
    n_agents = 10  # 无人机数量上限
    state_dim = None  # 全局状态维度（将在环境初始化时获取）
    obs_dim = None    # 单个智能体观测维度（将在环境初始化时获取）
    action_dim = 3    # 每个智能体输出3D速度向量

    # HMASD参数
    n_Z = 6          # 团队技能数量
    n_z = 6          # 个体技能数量
    k = 40            # 技能分配间隔

    # 网络参数
    hidden_size = 256        # 隐藏层大小
    embedding_dim = 128      # 嵌入维度
    n_encoder_layers = 3     # 编码器层数
    n_decoder_layers = 3     # 解码器层数
    n_heads = 8             # 多头注意力头数
    gru_hidden_size = 256    # GRU隐藏层大小
    lr_coordinator = 1e-4    # 技能协调器学习率
    lr_discoverer = 1e-4     # 技能发现器学习率
    lr_discriminator = 1e-4  # 技能判别器学习率

    # PPO参数
    gamma = 0.99             # 折扣因子
    gae_lambda = 0.95        # GAE参数
    clip_epsilon = 0.2       # PPO裁剪参数
    ppo_epochs = 15          # PPO迭代次数
    value_loss_coef = 0.5    # 价值损失系数
    entropy_coef = 0.01      # 熵损失系数
    max_grad_norm = 0.5      # 最大梯度范数

    # HMASD损失权重
    lambda_e = 10.0          # [退火优化] 设置一个中性的基础外部奖励权重，由退火机制动态调整
    lambda_D = 1.0           # [退火优化] 提高基础团队判别器奖励权重
    lambda_d = 2.0           # [退火优化] 提高基础个体判别器奖励权重
    lambda_h = 0.01          # 高层策略熵权重
    lambda_l = 0.1           # [优化] 提高低层策略熵权重，鼓励动作探索

    # 权重退火参数 - 用于解决奖励空窗期问题
    use_reward_annealing = True         # [启用] 启用权重退火机制
    w_intrinsic_initial = 5.0          # 内在奖励初始权重倍数（早期强调探索）
    w_intrinsic_final = 1.0            # 内在奖励最终权重倍数（后期回到正常水平）
    w_extrinsic_initial = 0.5          # 外部奖励初始权重倍数（早期弱化利用）
    w_extrinsic_final = 2.0            # 外部奖励最终权重倍数（后期强化利用）
    anneal_steps = 1000000             # 权重退火总步数（约25%的训练时间）
    anneal_schedule = 'linear'         # 退火计划（'linear' 或 'cosine'）

    # 训练参数
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
