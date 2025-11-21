#!/usr/bin/env python3
"""
负载均衡与覆盖率结合奖励函数的使用示例配置

这个配置文件展示了如何配置和使用新实施的负载均衡奖励函数，
该函数旨在在最大化用户覆盖率的同时，避免负载过度集中到少数无人机上。
"""


class LoadBalanceConfig:
    """
    负载均衡奖励函数配置示例
    
    核心思想：
    - 最大化用户覆盖率（w_coverage * coverage_reward）
    - 最小化负载不均衡（w_load_balance * load_balance_penalty）
    - 最终奖励 = w_coverage * coverage_reward - w_load_balance * load_balance_penalty
    """
    
    def __init__(self):
        # ============================================================
        # 基本环境参数
        # ============================================================
        self.n_agents = 12  # 无人机数量
        self.n_users = 60   # 用户数量
        self.area_size = 2000  # 区域大小（米）
        self.height_range = (50, 150)  # 无人机高度范围
        self.max_speed = 25  # 最大速度
        self.discrete_speeds = [20.0]  # 离散速度
        self.time_step = 1.0
        self.max_steps = 3000
        
        # ============================================================
        # 场景特定参数
        # ============================================================
        self.user_distribution = "forced_relay_cluster"  # 强制中继簇分布
        self.n_clusters = 4  # 用户簇数量
        self.cluster_std = 100  # 簇标准差
        self.central_area_ratio = 0.7  # 中心区域比例
        
        # 地面基站配置
        self.n_ground_bs = 1
        self.base_station_distance_factor = 0.9  # 基站距离因子，越大越远离用户
        
        # 网络参数
        self.max_hops = 4  # 最大跳数
        self.min_sinr = 3  # 最小SINR阈值（dB）
        self.max_connections = 20  # 每个UAV最大连接用户数
        
        # ============================================================
        # 新奖励函数配置 - 关键设置！
        # ============================================================
        self.reward_type = "load_balance_coverage"  # 使用负载均衡与覆盖率结合的奖励
        
        # 权重配置（可根据训练效果调整）
        self.w_coverage = 1.0      # 覆盖率权重（基础奖励）
        self.w_load_balance = 0.5  # 负载均衡权重（惩罚不均衡）
        
        # 权重调整指导：
        # - w_load_balance 较小 (0.1-0.3): 轻微鼓励负载均衡，主要关注覆盖率
        # - w_load_balance 中等 (0.4-0.7): 平衡覆盖率和负载均衡
        # - w_load_balance 较大 (0.8-1.2): 强烈要求负载均衡，可能牺牲部分覆盖率
        
        # ============================================================
        # 其他奖励权重（保持默认或根据需要调整）
        # ============================================================
        self.w_connectivity = 0.5   # 连接性权重（仅在health奖励中使用）
        self.w_diversity = 1.0      # 角色多样性权重
        self.w_dispersion = 0.05    # 分散惩罚权重
        
        # ============================================================
        # 通信参数
        # ============================================================
        self.carrier_frequency = 2e9  # 载波频率
        self.tx_power = 23            # 发射功率（dBm）
        self.noise_power = -94        # 噪声功率（dBm）
        self.bandwidth = 20e6         # 带宽
        self.use_fdma = False         # 是否使用FDMA
        
        # ============================================================
        # 用户移动模型
        # ============================================================
        self.user_movement_model = "random_walk"  # 或 "rpgm"
        self.user_max_speed = 3.0  # 用户最大移动速度
        
        # ============================================================
        # 随机化控制（用于增加训练多样性）
        # ============================================================
        self.randomize_bs = True      # 随机化基站位置
        self.randomize_users = True   # 随机化用户分布
        self.randomize_uav_start = True  # 随机化UAV起始位置
        
        # ============================================================
        # 路由协议
        # ============================================================
        self.routing_protocol = "widest_path"  # "widest_path", "hggr", "geographic"
        
        # ============================================================
        # 观测参数
        # ============================================================
        self.observation_radius = 600  # 观测半径
        self.max_observed_uavs = 15
        self.max_observed_users = 25
        self.max_observed_bs = 4


class ConservativeLoadBalanceConfig(LoadBalanceConfig):
    """
    保守的负载均衡配置 - 主要关注覆盖率，轻微鼓励负载均衡
    适用于初期训练阶段
    """
    
    def __init__(self):
        super().__init__()
        self.w_coverage = 1.0        # 保持覆盖率为主要目标
        self.w_load_balance = 0.2    # 较小的负载均衡权重
        print("使用保守的负载均衡配置：主要关注覆盖率，轻微鼓励负载均衡")


class BalancedLoadBalanceConfig(LoadBalanceConfig):
    """
    平衡的负载均衡配置 - 平衡覆盖率和负载均衡
    适用于中期训练阶段
    """
    
    def __init__(self):
        super().__init__()
        self.w_coverage = 1.0        # 保持覆盖率重要性
        self.w_load_balance = 0.6    # 中等的负载均衡权重
        print("使用平衡的负载均衡配置：平衡覆盖率和负载均衡")


class AggressiveLoadBalanceConfig(LoadBalanceConfig):
    """
    激进的负载均衡配置 - 强烈要求负载均衡
    适用于后期优化阶段，当覆盖率已经达到较高水平时
    """
    
    def __init__(self):
        super().__init__()
        self.w_coverage = 1.0        # 保持覆盖率基础奖励
        self.w_load_balance = 1.0    # 高负载均衡权重
        print("使用激进的负载均衡配置：强烈要求负载均衡")


# ============================================================
# 使用示例
# ============================================================

def get_config_by_training_stage(stage="balanced"):
    """
    根据训练阶段获取合适的配置
    
    参数:
        stage: 训练阶段
            - "conservative": 保守配置，主要关注覆盖率
            - "balanced": 平衡配置，兼顾覆盖率和负载均衡
            - "aggressive": 激进配置，强烈要求负载均衡
            
    返回:
        config: 相应的配置对象
    """
    if stage == "conservative":
        return ConservativeLoadBalanceConfig()
    elif stage == "balanced":
        return BalancedLoadBalanceConfig()
    elif stage == "aggressive":
        return AggressiveLoadBalanceConfig()
    else:
        print(f"未知的训练阶段: {stage}，使用默认平衡配置")
        return BalancedLoadBalanceConfig()


if __name__ == "__main__":
    print("负载均衡与覆盖率结合奖励函数 - 配置示例")
    print("="*60)
    
    print("\n可用的配置类型：")
    
    # 保守配置
    print("\n1. 保守配置 (适用于初期训练)：")
    conservative_config = ConservativeLoadBalanceConfig()
    print(f"   覆盖率权重: {conservative_config.w_coverage}")
    print(f"   负载均衡权重: {conservative_config.w_load_balance}")
    print(f"   特点: 主要关注覆盖率，轻微鼓励负载均衡")
    
    # 平衡配置
    print("\n2. 平衡配置 (适用于中期训练)：")
    balanced_config = BalancedLoadBalanceConfig()
    print(f"   覆盖率权重: {balanced_config.w_coverage}")
    print(f"   负载均衡权重: {balanced_config.w_load_balance}")
    print(f"   特点: 平衡覆盖率和负载均衡")
    
    # 激进配置
    print("\n3. 激进配置 (适用于后期优化)：")
    aggressive_config = AggressiveLoadBalanceConfig()
    print(f"   覆盖率权重: {aggressive_config.w_coverage}")
    print(f"   负载均衡权重: {aggressive_config.w_load_balance}")
    print(f"   特点: 强烈要求负载均衡")
    
    print("\n使用方法：")
    print("```python")
    print("from config_load_balance_example import get_config_by_training_stage")
    print("from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv")
    print("")
    print("# 获取配置")
    print("config = get_config_by_training_stage('balanced')")
    print("")
    print("# 创建环境")
    print("env = UAVForcedRelayEnv(config=config)")
    print("```")
    
    print(f"\n建议的训练流程：")
    print(f"1. 初期训练 (前30%): 使用保守配置，专注建立基础覆盖率")
    print(f"2. 中期训练 (中间40%): 使用平衡配置，兼顾覆盖率和均衡")
    print(f"3. 后期优化 (后30%): 使用激进配置，精细调优负载分布")
