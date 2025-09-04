#!/usr/bin/env python3
"""
簇级别卡尔曼滤波器配置示例

该配置展示了如何在RPGM移动模式中启用簇级别卡尔曼滤波器功能。
"""

# 启用簇级别卡尔曼滤波器的配置示例
cluster_kalman_config = {
    # 基本环境参数
    'n_uavs': 12,
    'n_users': 80,
    'n_clusters': 4,
    'area_size': 2500,
    'max_steps': 5000,
    
    # 移动模型配置
    'user_movement_model': 'rpgm',  # 必须使用RPGM模式
    'cluster_migration_speed': 15.0,  # 簇中心移动速度 (m/s)
    'user_max_speed': 5.0,  # 用户最大移动速度 (m/s)
    'cluster_std': 80,  # 簇内用户分布标准差 (m)
    
    # 卡尔曼滤波器控制参数
    'enable_cluster_kalman_filter': True,  # 启用簇级别卡尔曼滤波器
    
    # 时间步长
    'time_step': 1.0,  # 时间步长 (s)
    
    # 其他参数
    'randomize_users': True,
    'randomize_bs': True,
    'randomize_uav_start': True,
}

# 禁用簇级别卡尔曼滤波器的对比配置
traditional_config = {
    # 基本环境参数
    'n_uavs': 12,
    'n_users': 80,
    'n_clusters': 4,
    'area_size': 2500,
    'max_steps': 5000,
    
    # 移动模型配置
    'user_movement_model': 'rpgm',  # 使用RPGM模式
    'cluster_migration_speed': 15.0,
    'user_max_speed': 5.0,
    'cluster_std': 80,
    
    # 卡尔曼滤波器控制参数
    'enable_cluster_kalman_filter': False,  # 禁用簇级别卡尔曼滤波器，使用传统的用户级别滤波器
    
    # 时间步长
    'time_step': 1.0,
    
    # 其他参数
    'randomize_users': True,
    'randomize_bs': True,
    'randomize_uav_start': True,
}

# 非RPGM模式配置（自动使用用户级别卡尔曼滤波器）
random_walk_config = {
    # 基本环境参数
    'n_uavs': 12,
    'n_users': 80,
    'area_size': 2500,
    'max_steps': 5000,
    
    # 移动模型配置
    'user_movement_model': 'random_walk',  # 使用随机游走模式
    'user_max_speed': 5.0,
    
    # 卡尔曼滤波器控制参数
    'enable_cluster_kalman_filter': True,  # 即使设置为True，非RPGM模式下也会自动使用用户级别滤波器
    
    # 时间步长
    'time_step': 1.0,
    
    # 其他参数
    'randomize_users': True,
    'randomize_bs': True,
    'randomize_uav_start': True,
}

def demo_cluster_kalman_filter():
    """演示簇级别卡尔曼滤波器的使用"""
    from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
    
    print("=" * 60)
    print("簇级别卡尔曼滤波器使用演示")
    print("=" * 60)
    
    # 1. 创建启用簇级别卡尔曼滤波器的环境
    print("\n1. 创建启用簇级别卡尔曼滤波器的环境...")
    env_cluster = UAVForcedRelayEnv(**cluster_kalman_config)
    
    print(f"   - 移动模型: {env_cluster.user_movement_model}")
    print(f"   - 簇级别卡尔曼滤波器: {'启用' if env_cluster.enable_cluster_kalman_filter else '禁用'}")
    print(f"   - 簇数量: {env_cluster.n_clusters}")
    print(f"   - 卡尔曼滤波器数量: {len(env_cluster.cluster_kalman_filters) if env_cluster.cluster_kalman_filters else 0} (簇级别)")
    
    # 2. 创建传统用户级别卡尔曼滤波器的环境
    print("\n2. 创建传统用户级别卡尔曼滤波器的环境...")
    env_traditional = UAVForcedRelayEnv(**traditional_config)
    
    print(f"   - 移动模型: {env_traditional.user_movement_model}")
    print(f"   - 簇级别卡尔曼滤波器: {'启用' if env_traditional.enable_cluster_kalman_filter else '禁用'}")
    print(f"   - 用户数量: {env_traditional.n_users}")
    print(f"   - 卡尔曼滤波器数量: {len(env_traditional.kalman_filters) if env_traditional.kalman_filters else 0} (用户级别)")
    
    # 3. 运行简单的对比测试
    print("\n3. 运行简单的对比测试...")
    
    # 重置环境
    obs_cluster, _ = env_cluster.reset(seed=42)
    obs_traditional, _ = env_traditional.reset(seed=42)
    
    # 运行几个步骤
    for step in range(5):
        # 生成随机动作
        actions_cluster = {agent: env_cluster.action_space(agent).sample() for agent in env_cluster.agents}
        actions_traditional = {agent: env_traditional.action_space(agent).sample() for agent in env_traditional.agents}
        
        # 执行步骤
        obs_cluster, rewards_cluster, _, _, _ = env_cluster.step(actions_cluster)
        obs_traditional, rewards_traditional, _, _, _ = env_traditional.step(actions_traditional)
        
        print(f"   步骤 {step+1}: 簇级别环境奖励 {rewards_cluster['uav_0']:.3f}, 传统环境奖励 {rewards_traditional['uav_0']:.3f}")
    
    print("\n✓ 演示完成！两种配置都能正常工作。")

if __name__ == "__main__":
    demo_cluster_kalman_filter()
