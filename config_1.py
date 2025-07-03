# HMASD算法配置参数 - 基于论文《Hierarchical Multi-Agent Skill Discovery》附录E中的超参数设置

class Config:
    # 环境参数
    # 注意：实际环境中应该获取这些值
    n_agents = None  # 无人机数量（将由训练脚本根据--n_uavs参数设置）
    state_dim = None  # 全局状态维度（将在环境初始化时获取）
    obs_dim = None    # 单个智能体观测维度（将在环境初始化时获取）
    action_dim = 3    # 每个智能体输出3D速度向量
    
    # 局部观测参数
    #observation_radius = 500  # 观测半径 (m) 使用真实通信范围代替
    max_observed_uavs = 8     # 最大观测无人机数量
    max_observed_users = 15   # 最大观测用户数量

    # HMASD参数 - 基于论文Table 3中的3m场景
    n_Z = 5           # 团队技能数量 (论文中3m场景为3)
    n_z = 5           # 个体技能数量 (论文中3m场景为3)
    k = 30            # 技能分配间隔 (论文中3m场景为25，为适应无人机场景改为10)

    # 网络参数 - 基于论文Table 1
    hidden_size = 64         # 隐藏层大小 (论文中为64)
    embedding_dim = 64       # 嵌入维度 (与hidden_size保持一致)
    n_encoder_layers = 3     # 编码器层数
    n_decoder_layers = 3     # 解码器层数
    n_heads = 8              # 多头注意力头数
    gru_hidden_size = 64     # GRU隐藏层大小 (与hidden_size保持一致)
    lr_coordinator = 1e-4    # 技能协调器学习率 (适当降低以稳定高层策略学习)
    lr_discoverer = 1e-4     # 技能发现器学习率 (降低以稳定低层策略学习)
    lr_discriminator = 1e-4  # 技能判别器学习率 (适当降低，防止其过强)

    # PPO参数 - 基于论文Table 1
    gamma = 0.99             # 折扣因子
    gae_lambda = 0.95        # GAE参数
    clip_epsilon = 0.2       # PPO裁剪参数 (更保守以稳定学习)
    ppo_epochs = 15          # PPO迭代次数 (减少以稳定学习)
    value_loss_coef = 1.0    # 价值损失系数 (论文中为1.0)
    max_grad_norm = 0.5      # 最大梯度范数 (更严格的梯度裁剪)

    # HMASD损失权重 - 基于论文Table 3中的3m场景
    # 注意：lambda_e参数已调整为0.1，以稳定训练
    lambda_e = 20.0          # 外部奖励权重 (从100降低，但保持足够强度)
    lambda_D = 0.05          # 团队技能判别器奖励权重 (适度降低团队判别器权重)
    lambda_d = 0.2           # 个体技能判别器奖励权重 (适度降低个体判别器权重)
    lambda_h = 0.001         # 高层策略熵权重 (论文中3m场景为0.001)
    lambda_l = 0.01          # 低层策略熵权重 (论文中3m场景为0.01)
    lambda_cd = 0.5          # 对比散度损失权重 (新增)

    # 训练参数 - 部分基于论文Table 1和Table 2
    buffer_size = 1024       # 经验回放缓冲区大小
    batch_size = 128         # 批处理大小
    high_level_batch_size = 128  # 高层更新的批处理大小
    num_envs = 32            # 并行环境数量 (论文中rollout threads为32)
    rollout_length = 150     # 每次rollout收集的步数 (严格on-policy)
    total_timesteps = 4e6 #4e6    # 总时间步数 (论文中SMAC为2e6)
    episode_length = 1500    # 每个episode的最大长度 (基于观察到的实际行为)
    eval_interval = episode_length*num_envs   # 评估间隔 (32并行环境 * 每环境5120步)
    eval_episodes = 4      # 评估时的episode数量 (论文中SMAC为100)
    eval_rollout_threads = 4 # 评估时的并行线程数 (论文中SMAC为4)
    
    # 其他论文中提到的参数
    use_valuenorm = True     # 使用价值标准化
    use_orthogonal = True    # 使用正交初始化
    gain = 0.01              # 增益
    optimizer_epsilon = 1e-5 # 优化器epsilon
    weight_decay = 1e-4      # 权重衰减
    num_mini_batch = 1       # mini batch数量
    use_huber_loss = True    # 使用Huber损失
    huber_delta = 10         # Huber delta
    
    # OPT (Interaction Pattern Disentangling) 参数 - 基于论文《Interaction Pattern Disentangling for Multi-Agent Reinforcement Learning》
    use_opt = True           # 是否使用OPT模块 (设为False可对比原始性能)
    opt_num_prototypes = 4   # 交互原型数量 (论文中N=4)
    opt_prototype_dim = 32   # 交互原型特征维度 (论文中d_x=32)
    opt_alpha = 0.5          # 对比散度损失权重 (论文中α=0.5)
    opt_beta = 0.1           # 条件互信息损失权重 (论文中β=0.1)
    opt_layers = 2           # OPT模块层数 (论文中K=2)
    
    # 环境奖励权重配置 - 场景3多跳环境（优化后的权重分配）
    # 注意：场景2不再需要传入奖励权重，其奖励已固化为覆盖率+归一化吞吐量
    effective_coverage_weight = 0.6     # 有效覆盖率权重（大幅增强，优先覆盖所有用户）
    throughput_weight = 0.2            # 系统吞吐量权重（降低，避免与覆盖目标冲突）
    load_balance_weight = 0.15          # 负载均衡权重（适度降低）
    proximity_penalty_weight = 0.05   # 邻近惩罚权重（降低，减少对探索的限制）
    coverage_curve_steepness = 2.0     # 覆盖率奖励曲线陡峭度（新增，增强高覆盖率区域奖励）

    # 权重退火参数 - 用于解决奖励空窗期问题
    use_reward_annealing = True         # 是否启用奖励权重退火机制
    w_intrinsic_initial = 5.0          # 内在奖励初始权重倍数（早期强调探索）
    w_intrinsic_final = 1.0            # 内在奖励最终权重倍数（后期回到正常水平）
    w_extrinsic_initial = 0.5          # 外部奖励初始权重倍数（早期弱化利用）
    w_extrinsic_final = 2.0            # 外部奖励最终权重倍数（后期强化利用）
    anneal_steps = 1000000             # 权重退火总步数（约25%的训练时间）
    anneal_schedule = 'linear'         # 退火计划（'linear' 或 'cosine'）

    # --- GNN-HMASD 参数 ---
    use_gnn_hmasd = False        # 是否启用GNN方案
    num_roles = 2                # 角色数量 (e.g., 2 for 'SERVER', 'RELAY')
    role_embedding_dim = 16      # 角色嵌入维度
    gnn_hidden_dim = 64          # GNN隐藏层维度
    node_feature_dim = 8         # 图节点特征维度 (3 pos + 1 type_specific + 4 type_onehot)
    num_user_clusters = 10       # 用户聚类数量
    graph_build_d_max = 1500     # 建图的最大通信距离 (m)

    def update_env_dims(self, state_dim, obs_dim):
        """更新环境维度"""
        self.state_dim = state_dim
        self.obs_dim = obs_dim
        print(f"环境维度已更新：state_dim={state_dim}, obs_dim={obs_dim}")
