import numpy as np
import heapq
from pettingzoo import ParallelEnv
from gymnasium.spaces import Box, Dict
from scipy.spatial.distance import cdist
from envs.pettingzoo.relay.channel_geometry import RelayChannelGeometry

class UAVBeliefMapEnv(ParallelEnv, RelayChannelGeometry):
    """
    场景5: 基于信念地图的动态用户覆盖环境
    
    """
    
    from envs.pettingzoo.relay.local_view import (
        _get_local_bs,
        _get_local_uavs,
        _get_local_users,
        _update_observations_dict,
    )

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_belief_map_env_v0",
        "is_parallelizable": True,
    }

    def __init__(
        self,
        n_uavs=12,
        n_users=80,
        area_size=2500,
        height_range=(50, 200),
        max_speed=30,
        time_step=1.0,
        max_steps=1800,
        user_distribution="forced_relay_cluster",
        render_mode=None,
        seed=None,
        min_sinr=3,
        max_connections=25,
        max_hops=4,
        n_ground_bs=1,
        n_clusters=4,
        cluster_std=80,
        central_area_ratio=0.6,
        base_station_distance_factor=0.8,
        observation_radius=600,
        max_observed_uavs=15,
        max_observed_users=25,
        max_observed_bs=4,
        use_fdma=False,
        bandwidth=20e6,
        ground_bs_tx_power=30,
        uav_init_mode="start_area",
        uav_start_area_size=500,
        # Randomization control parameters
        randomize_bs=True,  # 是否随机化基站位置
        randomize_users=True,  # 是否随机化用户簇中心
        randomize_uav_start=True,  # 是否随机化无人机起始区域
        aclr_db=45,  # 邻道泄漏比 (Adjacent Channel Leakage Ratio) in dB
        test_reward_mode=False,
        # Network Health Score Weights
        w_connectivity=0.5,
        w_diversity=1.0,
        w_coverage=1.0,
        w_dispersion=0.05,
        # --- New parameters for Dynamic Environment ---
        users_dynamic=True,
        user_max_speed=20,  # m/s, high-speed scenario (72 km/h) - 车辆速度
        user_movement_model="rpgm",  # 标准参考点群体移动模型
        grid_resolution=100, # M x N grid, e.g., 100x100 for a 2500m area
        belief_decay=0.99,
        belief_diffusion_factor=0.1,
        belief_update_strength=0.2,
        discovery_reward_value=10.0,
        # --- High-Speed RPGM Parameters ---
        cluster_migration_speed=15.0,  # m/s, 高速簇中心移动速度 (54 km/h)
        cluster_pause_time_range=(0, 5),  # 簇中心暂停时间范围 (秒) - 大幅减少
        user_pause_time_range=(0, 3),  # 用户暂停时间范围 (秒) - 大幅减少
        # --- Dynamic Density Prediction Parameters ---
        density_prediction=True,  # 启用动态密度预测功能
        prediction_horizon_k=10,  # 预测未来k步的用户密度分布
        density_grid_resolution=50,  # 密度预测网格分辨率 (50x50)
        density_diffusion_rate=0.1,  # 密度扩散率
        velocity_smoothing_factor=0.8,  # 速度平滑因子
    ):
        super().__init__()

        # 环境参数
        self.n_uavs = n_uavs
        self.n_users = n_users
        self.area_size = area_size
        self.height_range = height_range
        self.max_speed = max_speed
        self.time_step = time_step
        self.max_steps = max_steps
        self.user_distribution = user_distribution
        self.render_mode = render_mode
        self.seed_val = seed
        self.np_random = np.random.RandomState(seed)

        # Track user service status to provide sparse rewards correctly
        self.user_serviced_status = np.zeros(self.n_users, dtype=bool)
        
        # 场景特定参数
        self.n_clusters = n_clusters
        self.cluster_std = cluster_std
        self.central_area_ratio = central_area_ratio
        self.base_station_distance_factor = base_station_distance_factor
        self.observation_radius = observation_radius
        self.uav_init_mode = uav_init_mode
        self.uav_start_area_size = uav_start_area_size
        self.n_ground_bs = n_ground_bs
        self.max_hops = max_hops
        self.min_sinr = min_sinr
        self.max_connections = max_connections
        
        # 随机化控制参数
        self.randomize_bs = randomize_bs
        self.randomize_users = randomize_users
        self.randomize_uav_start = randomize_uav_start
        self.test_reward_mode = test_reward_mode

        # Store reward weights
        self.w_connectivity = w_connectivity
        self.w_diversity = w_diversity
        self.w_coverage = w_coverage
        self.w_dispersion = w_dispersion

        # --- New Dynamic Environment Parameters ---
        self.users_dynamic = users_dynamic
        self.user_max_speed = user_max_speed
        self.user_movement_model = user_movement_model
        self.grid_resolution = grid_resolution
        self.belief_decay = belief_decay
        self.belief_diffusion_factor = belief_diffusion_factor
        self.belief_update_strength = belief_update_strength
        self.discovery_reward_value = discovery_reward_value

        # --- Standard RPGM Parameters ---
        self.cluster_migration_speed = cluster_migration_speed
        self.cluster_pause_time_range = cluster_pause_time_range
        self.user_pause_time_range = user_pause_time_range

        # --- Dynamic Density Prediction Parameters ---
        self.density_prediction = density_prediction
        self.prediction_horizon_k = prediction_horizon_k
        self.density_grid_resolution = density_grid_resolution
        self.density_diffusion_rate = density_diffusion_rate
        self.velocity_smoothing_factor = velocity_smoothing_factor

        # --- New State Variables ---
        self.user_velocities = np.zeros((self.n_users, 2)) # 2D velocity (x, y)
        self.user_waypoints = np.zeros((self.n_users, 2))
        self.user_cluster_assignments = np.zeros(self.n_users, dtype=int) # Track which cluster each user belongs to
        self.cluster_centers_history = np.zeros((self.n_clusters, 2)) # Store cluster centers for mobility
        self.belief_map = np.ones((grid_resolution, grid_resolution)) / (grid_resolution**2) # Initial uniform belief
        self.discovered_users_this_episode = set()

        # --- Dynamic Density Prediction State Variables ---
        if self.density_prediction:
            # 当前时刻的用户密度图 (G x G)
            self.density_map = np.zeros((self.density_grid_resolution, self.density_grid_resolution))
            # 当前时刻的平均速度图 (G x G x 2) - 每个网格的平均用户速度向量
            self.velocity_map = np.zeros((self.density_grid_resolution, self.density_grid_resolution, 2))
            # 预测的未来用户密度图 (G x G)
            self.predicted_density_map = np.zeros((self.density_grid_resolution, self.density_grid_resolution))
            # 网格单元大小 (米)
            self.density_cell_size = self.area_size / self.density_grid_resolution
        else:
            # 如果关闭密度预测，设置为None
            self.density_map = None
            self.velocity_map = None
            self.predicted_density_map = None
            self.density_cell_size = None
        
        # --- Enhanced Mobility State Variables ---
        self.cluster_velocities = np.zeros((self.n_clusters, 2))  # 簇中心移动速度
        self.cluster_waypoints = np.zeros((self.n_clusters, 2))   # 簇中心目标点
        self.enhanced_cluster_std = max(500, cluster_std * 5)  # 大幅扩展簇活动范围
        self.user_pause_times = np.zeros(self.n_users)  # 用户暂停时间
        self.user_movement_phases = np.zeros(self.n_users, dtype=int)  # 用户移动阶段 (0:正常, 1:逃离, 2:跳跃)
        
        # 通信参数
        self.carrier_frequency = 2e9
        self.tx_power = 23
        self.noise_power = -94  # 
        self.use_fdma = use_fdma
        self.bandwidth = bandwidth
        self.ground_bs_tx_power = ground_bs_tx_power
        self.aclr_db = aclr_db  # 存储ACLR值
        self.aclr_linear = 10 ** (-self.aclr_db / 10)  # 转换为线性值以便计算

        # 局部观测参数
        self.max_observed_uavs = max_observed_uavs
        self.max_observed_users = max_observed_users
        self.max_observed_bs = max_observed_bs

        # 智能体列表
        self.possible_agents = [f"uav_{i}" for i in range(n_uavs)]
        self.agents = self.possible_agents.copy()

        # 观测和动作空间
        # obs_dim: 3(自身位置) + 3(最近邻无人机) + 4(自身状态，包含跳数) + N_user*4(用户) + N_uav*4(无人机) + N_bs*4(基站) + 1(步数)
        self.obs_dim = 3 + 3 + 4 + max_observed_users * 4 + max_observed_uavs * 4 + max_observed_bs * 4 + 1
        self.observation_spaces = {
            agent: Dict({
                "obs": Box(
                    low=-float('inf'),
                    high=float('inf'),
                    shape=(self.obs_dim,),
                    dtype=np.float32,
                ),
                "action_mask": Box(
                    low=0,
                    high=1,
                    shape=(3,),
                    dtype=np.float32,
                )
            }) for agent in self.possible_agents
        }
        self.action_spaces = {
            agent: Box(low=-1, high=1, shape=(3,))
            for agent in self.possible_agents
        }

        # 初始化地面基站
        self._init_ground_bs()
        
        # 【关键修复】初始化状态变量，防止在reset()之前调用render()时出错
        self.current_step = 0
        self.uav_positions = np.zeros((self.n_uavs, 3))
        self.user_positions = np.zeros((self.n_users, 3))
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        self.routing_paths = {}
        
        # 渲染相关
        self.viewer = None
        self.fig = None
        self.ax = None
        
        # 重新计算并设置场景4的状态维度
        # 1. 无人机位置: n_uavs * 3
        uav_pos_dim = self.n_uavs * 3
        
        # 2. 用户位置: n_users * 3 (改为3维，保持一致性)
        user_pos_dim = self.n_users * 3
        
        # 3. 地面基站位置: n_ground_bs * 3
        bs_pos_dim = self.n_ground_bs * 3
        
        # 4. 用户覆盖状态: n_users
        user_covered_dim = self.n_users
        
        # 5. 无人机连接状态: n_uavs
        uav_connected_dim = self.n_uavs
        
        # 6. 系统通信质量指标: 4 (平均SINR, 连接质量, 平均跳数, 系统吞吐量)
        comm_quality_dim = 4
        
        # 7. 当前步数: 1
        step_dim = 1
        
        # 8. 动态密度预测图维度 (如果启用)
        if self.density_prediction:
            density_map_dim = self.density_grid_resolution * self.density_grid_resolution  # 预测密度图
        else:
            density_map_dim = 0
        
        # 重新设置state_dim
        self.state_dim = uav_pos_dim + user_pos_dim + bs_pos_dim + user_covered_dim + uav_connected_dim + comm_quality_dim + step_dim + density_map_dim

    def get_state_dim(self):
        """返回全局状态维度"""
        return self.state_dim
    
    def get_obs_dim(self):
        """返回观测维度"""
        return self.obs_dim

    def _init_ground_bs(self):
        """初始化地面基站位置 - 支持固定或随机边界分布"""
        self.ground_bs_positions = np.zeros((self.n_ground_bs, 3))
        
        # 如果关闭随机化，则使用原有的固定位置逻辑
        if not self.randomize_bs:
            # 计算基站到用户区域中心的距离
            user_center = self.area_size / 2
            base_distance = self.area_size * self.base_station_distance_factor
            
            if self.n_ground_bs == 1:
                # 单个基站放在远离中心的角落
                self.ground_bs_positions[0] = [
                    self.area_size * 0.05,  # 靠近边界
                    self.area_size * 0.05,
                    30
                ]
            elif self.n_ground_bs == 2:
                # 两个基站放在对角，距离用户区域中心很远
                # 基站1：左下角
                self.ground_bs_positions[0] = [
                    self.area_size * 0.05,
                    self.area_size * 0.05,
                    30
                ]
                # 基站2：右上角
                self.ground_bs_positions[1] = [
                    self.area_size * 0.95,
                    self.area_size * 0.95,
                    30
                ]
            elif self.n_ground_bs == 3:
                # 三个基站分布在三个角落
                self.ground_bs_positions[0] = [self.area_size * 0.05, self.area_size * 0.05, 30]
                self.ground_bs_positions[1] = [self.area_size * 0.95, self.area_size * 0.05, 30]
                self.ground_bs_positions[2] = [self.area_size * 0.05, self.area_size * 0.95, 30]
            elif self.n_ground_bs >= 4:
                # 四个角落
                self.ground_bs_positions[0] = [self.area_size * 0.05, self.area_size * 0.05, 30]
                self.ground_bs_positions[1] = [self.area_size * 0.95, self.area_size * 0.05, 30]
                self.ground_bs_positions[2] = [self.area_size * 0.95, self.area_size * 0.95, 30]
                self.ground_bs_positions[3] = [self.area_size * 0.05, self.area_size * 0.95, 30]
                
                # 如果有更多基站，分布在边界
                for i in range(4, self.n_ground_bs):
                    edge = i % 4
                    if edge == 0:  # 下边界
                        x = self.np_random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                        y = self.area_size * 0.05
                    elif edge == 1:  # 右边界
                        x = self.area_size * 0.95
                        y = self.np_random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                    elif edge == 2:  # 上边界
                        x = self.np_random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                        y = self.area_size * 0.95
                    else:  # 左边界
                        x = self.area_size * 0.05
                        y = self.np_random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                    
                    self.ground_bs_positions[i] = [x, y, 30]
            return
        
        # --- 新的随机化逻辑 ---
        # 将边界划分为四个区域：0:下, 1:右, 2:上, 3:左
        # 为每个基站随机选择一个边界区域，避免所有基站挤在一起
        
        # 定义边界区域的范围
        margin = self.area_size * 0.1  # 距离角落的最小距离
        
        for i in range(self.n_ground_bs):
            edge = self.np_random.randint(0, 4)  # 随机选择一个边界
            
            if edge == 0:  # 下边界
                x = self.np_random.uniform(margin, self.area_size - margin)
                y = self.np_random.uniform(0, self.area_size * 0.05)
            elif edge == 1:  # 右边界
                x = self.np_random.uniform(self.area_size * 0.95, self.area_size)
                y = self.np_random.uniform(margin, self.area_size - margin)
            elif edge == 2:  # 上边界
                x = self.np_random.uniform(margin, self.area_size - margin)
                y = self.np_random.uniform(self.area_size * 0.95, self.area_size)
            else:  # 左边界
                x = self.np_random.uniform(0, self.area_size * 0.05)
                y = self.np_random.uniform(margin, self.area_size - margin)
                
            self.ground_bs_positions[i] = [x, y, 30]  # 高度固定为30
    
    def _generate_user_positions(self):
        """
        生成用户位置
        
        返回:
            user_positions: 用户位置 [n_users, 3] (包含高度1.5米)
        """
        if self.user_distribution == "forced_relay_cluster":
            return self._generate_forced_relay_cluster_positions()
        elif self.user_distribution == "uniform":
            user_positions = np.zeros((self.n_users, 3))
            for i in range(self.n_users):
                user_positions[i] = [
                    self.np_random.uniform(0, self.area_size),
                    self.np_random.uniform(0, self.area_size),
                    1.5  # 用户高度设为1.5米
                ]
            return user_positions
        else:
            # 默认或未指定时，也使用强制中继的簇分布
            return self._generate_forced_relay_cluster_positions()
    
    def _generate_forced_relay_cluster_positions(self):
        """
        生成针对强制中继优化的用户簇分布 - 改进的最远点圆形区域策略
        
        新特点：
        - 找到距离基站最远的点作为用户区域中心
        - 在该点周围定义一个大的圆形区域用于用户生成
        - 空间利用率更高，不再局限于单一象限
        - 仍然确保强制多跳中继的效果
        
        返回:
            user_positions: 用户位置 [n_users, 3] (包含高度1.5米)
        """
        user_positions = np.zeros((self.n_users, 3))
        
        # 1. 计算所有地面基站的几何中心
        bs_center = np.mean(self.ground_bs_positions[:, :2], axis=0)
        
        # 2. 找到距离基站中心最远的点（通常在地图的某个角落）
        # 检查四个角落，找到距离基站中心最远的那个
        corners = [
            [self.area_size * 0.05, self.area_size * 0.05],  # 左下
            [self.area_size * 0.95, self.area_size * 0.05],  # 右下
            [self.area_size * 0.95, self.area_size * 0.95],  # 右上
            [self.area_size * 0.05, self.area_size * 0.95],  # 左上
        ]
        
        max_distance = 0
        farthest_corner = corners[0]
        for corner in corners:
            distance = np.linalg.norm(np.array(corner) - bs_center)
            if distance > max_distance:
                max_distance = distance
                farthest_corner = corner
        
        # 3. 以最远点为中心，定义用户生成的圆形区域
        user_region_center = np.array(farthest_corner)
        user_region_radius = self.area_size * 0.35  # 圆形区域半径，覆盖更大面积
        
        # 4. 在圆形区域内生成簇中心位置
        cluster_centers = np.zeros((self.n_clusters, 2))
        
        # --- 随机化簇中心 ---
        if self.randomize_users:
            # 在圆形区域内随机生成簇中心
            for i in range(self.n_clusters):
                max_attempts = 50
                for attempt in range(max_attempts):
                    # 在圆形区域内随机生成点
                    angle = self.np_random.uniform(0, 2 * np.pi)
                    radius = self.np_random.uniform(0, user_region_radius)
                    
                    x = user_region_center[0] + radius * np.cos(angle)
                    y = user_region_center[1] + radius * np.sin(angle)
                    
                    # 确保在地图边界内
                    x = np.clip(x, self.area_size * 0.05, self.area_size * 0.95)
                    y = np.clip(y, self.area_size * 0.05, self.area_size * 0.95)
                    
                    new_center = np.array([x, y])
                    
                    # 检查与已有簇中心的距离
                    min_distance = self.cluster_std * 2.5
                    valid = True
                    for j in range(i):
                        distance = np.linalg.norm(new_center - cluster_centers[j])
                        if distance < min_distance:
                            valid = False
                            break
                    
                    if valid:
                        cluster_centers[i] = new_center
                        break
                else:
                    # 备选方案：在圆形区域内使用极坐标网格
                    angle = 2 * np.pi * i / self.n_clusters
                    radius = user_region_radius * 0.7  # 使用70%的半径
                    x = user_region_center[0] + radius * np.cos(angle)
                    y = user_region_center[1] + radius * np.sin(angle)
                    x = np.clip(x, self.area_size * 0.05, self.area_size * 0.95)
                    y = np.clip(y, self.area_size * 0.05, self.area_size * 0.95)
                    cluster_centers[i] = [x, y]
        else:
            # --- 固定簇中心逻辑（在圆形区域内使用极坐标布局） ---
            for i in range(self.n_clusters):
                if self.n_clusters == 1:
                    # 单簇情况，放在圆心
                    cluster_centers[i] = user_region_center
                else:
                    # 多簇情况，均匀分布在圆周上
                    angle = 2 * np.pi * i / self.n_clusters
                    radius = user_region_radius * 0.6  # 使用60%的半径
                    x = user_region_center[0] + radius * np.cos(angle)
                    y = user_region_center[1] + radius * np.sin(angle)
                    x = np.clip(x, self.area_size * 0.05, self.area_size * 0.95)
                    y = np.clip(y, self.area_size * 0.05, self.area_size * 0.95)
                    cluster_centers[i] = [x, y]
        
        # 存储簇中心用于移动模型
        self.cluster_centers_history = cluster_centers.copy()
        
        # 5. 计算每个簇的用户数量
        base_users_per_cluster = self.n_users // self.n_clusters
        remaining_users = self.n_users % self.n_clusters
        
        cluster_user_counts = [base_users_per_cluster] * self.n_clusters
        for i in range(remaining_users):
            cluster_user_counts[i] += 1
        
        # 6. 为每个簇生成用户并记录簇分配
        user_idx = 0
        
        for cluster_idx in range(self.n_clusters):
            cluster_center = cluster_centers[cluster_idx]
            n_users_in_cluster = cluster_user_counts[cluster_idx]
            
            # 在簇中心周围生成用户（二维高斯分布）
            for _ in range(n_users_in_cluster):
                # 生成二维高斯分布的偏移
                offset = self.np_random.multivariate_normal(
                    mean=[0, 0],
                    cov=[[self.cluster_std**2, 0], [0, self.cluster_std**2]]
                )
                
                user_position_2d = cluster_center + offset
                
                # 确保用户位置在有效区域内
                user_position_2d[0] = np.clip(user_position_2d[0], 10, self.area_size - 10)
                user_position_2d[1] = np.clip(user_position_2d[1], 10, self.area_size - 10)
                
                # 创建三维用户位置（包含1.5米高度）
                user_position_3d = np.array([user_position_2d[0], user_position_2d[1], 1.5])
                
                user_positions[user_idx] = user_position_3d
                # 记录用户所属的簇
                self.user_cluster_assignments[user_idx] = cluster_idx
                user_idx += 1
        
        return user_positions
    
    def _calculate_link_quality_reward(self):
        """
        计算统一的"链路质量"奖励，取代之前分散的连通性、效率、中继等奖励。
        
        核心思想:
        - 直接奖励高质量的完整通信链路。
        - 链路质量由其"瓶颈容量"和"跳数"共同决定。
        - 容量高、跳数少的链路获得更高奖励。
        - 【重要修正】：只有实际服务了用户的无人机才能获得链路质量奖励。
        
        返回:
            link_quality_reward: 归一化的链路质量总奖励 [0, 1]
        """
        if not hasattr(self, 'routing_paths') or not self.routing_paths:
            return 0.0

        total_quality_score = 0
        
        # 设定一个理论上的最大容量用于归一化，例如基于30dB SINR计算
        # C = B * log2(1 + SINR_linear)
        # SINR = 30dB -> SINR_linear = 1000
        # C_max = 20e6 * log2(1001) ≈ 20e6 * 9.96 ≈ 200 Mbps
        max_theoretical_capacity = 200e6  # 200 Mbps

        for uav_idx, (path, bottleneck_capacity) in self.routing_paths.items():
            # 【核心修正】：检查这架拥有回程路径的无人机是否连接了任何用户
            # 如果没有连接用户，那么它的高质量链路是无用的，不应给予奖励
            if np.sum(self.connections[uav_idx]) == 0:
                continue  # 跳过这个无人机，不给予链路质量奖励
            
            if not path or bottleneck_capacity <= 0:
                continue

            # 1. 容量得分 (Capacity Score)
            # 将瓶颈容量归一化
            capacity_score = np.clip(bottleneck_capacity / max_theoretical_capacity, 0, 1)

            # 2. 效率得分 (Efficiency Score)
            # 跳数越少，效率得分越高
            hops = len(path) - 1
            efficiency_score = max(0, 1 - (hops - 1) / (self.max_hops * 1.5)) # 放宽分母，使惩罚更平滑

            # 3. 综合路径质量分
            # 将容量和效率结合，容量的权重更高
            path_quality_score = capacity_score * (0.7 + 0.3 * efficiency_score)
            total_quality_score += path_quality_score

        # 归一化：用总得分除以无人机数量，得到平均链路质量
        # 这样，目标就是为每个无人机都建立一条高质量链路
        if self.n_uavs > 0:
            normalized_reward = total_quality_score / self.n_uavs
        else:
            normalized_reward = 0.0
            
        return np.clip(normalized_reward, 0, 1)
    
    def _calculate_individual_distance_overlap_penalties(self):
        """
        计算每个智能体的个体距离重叠惩罚（增强版）。
        这个函数提供了一个去中心化且更直接的学习信号。

        返回:
            individual_penalties (np.ndarray): 形状为 (n_uavs,) 的数组，
                                               包含每个智能体的惩罚值。
        """
        individual_penalties = np.zeros(self.n_uavs)
        # 增加惩罚乘数，使其在奖励信号中更显著
        penalty_multiplier = getattr(self, 'proximity_penalty_multiplier', 5.0)
        
        # 定义一个安全距离，小于此距离将受到惩罚
        # 使用观测半径的1/3作为基础安全距离，例如 600/3 = 200m
        safety_radius = self.observation_radius / 3.0

        for i in range(self.n_uavs):
            min_dist_to_neighbor = float('inf')
            
            # 找到智能体i的最近邻居
            for j in range(self.n_uavs):
                if i == j:
                    continue
                # 使用2D距离进行计算，因为主要关注水平分散
                dist = np.linalg.norm(self.uav_positions[i, :2] - self.uav_positions[j, :2])
                if dist < min_dist_to_neighbor:
                    min_dist_to_neighbor = dist

            # 如果最近邻居距离过近，则施加惩罚
            if min_dist_to_neighbor < safety_radius:
                # 使用更平滑且在接近零时梯度更大的惩罚函数
                # 当距离为0时，惩罚为1；当距离为safety_radius时，惩罚为0
                # (1 - x)^2 在 x 接近1时梯度较小，(1 - x^0.5) 在 x 接近1时梯度更大
                normalized_dist = min_dist_to_neighbor / safety_radius
                penalty = (1 - np.sqrt(normalized_dist))
                
                # 应用惩罚乘数
                individual_penalties[i] = penalty * penalty_multiplier
                
        return individual_penalties
        
    def _init_uav_positions(self):
        """
        初始化无人机位置 - 支持多种初始化模式
        
        模式：
        - 'random': 在整个区域内随机分布（默认行为）
        - 'start_area': 在指定的起始区域内均匀分布
        
        返回:
            uav_positions: 无人机位置 [n_uavs, 3]
        """
        if self.uav_init_mode == "start_area":
            return self._init_uav_positions_start_area()
        elif self.uav_init_mode == "hybrid_test":
            return self._init_uav_positions_hybrid_test()
        else:
            # 'random' 模式：在整个区域内随机分布
            uav_positions = np.zeros((self.n_uavs, 3))
            for i in range(self.n_uavs):
                uav_positions[i] = [
                    self.np_random.uniform(0, self.area_size),
                    self.np_random.uniform(0, self.area_size),
                    self.height_range[0]  # 固定为最小高度（50m）
                ]
            return uav_positions
    
    def _init_uav_positions_hybrid_test(self):
        """
        混合初始化模式，用于严格测试分散行为。
        一半无人机在角落密集出生，另一半随机分布。
        """
        uav_positions = np.zeros((self.n_uavs, 3))
        
        # 计算集群中的无人机数量
        num_in_cluster = self.n_uavs // 2
        
        # --- 1. 生成集群中的无人机 ---
        # (复用 _init_uav_positions_start_area 的逻辑)
        margin = 50
        max_start_area_size = min(self.uav_start_area_size, self.area_size / 2 - margin)
        start_x_min = margin
        start_y_min = margin
        start_x_max = start_x_min + max_start_area_size
        start_y_max = start_y_min + max_start_area_size
        
        grid_size = int(np.ceil(np.sqrt(num_in_cluster)))
        
        cluster_idx = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if cluster_idx >= num_in_cluster:
                    break
                
                if grid_size == 1:
                    x = (start_x_min + start_x_max) / 2
                    y = (start_y_min + start_y_max) / 2
                else:
                    x = start_x_min + (start_x_max - start_x_min) * (i + 0.5) / grid_size
                    y = start_y_min + (start_y_max - start_y_min) * (j + 0.5) / grid_size
                
                x_offset = self.np_random.uniform(-20, 20)
                y_offset = self.np_random.uniform(-20, 20)
                
                x = np.clip(x + x_offset, 10, self.area_size - 10)
                y = np.clip(y + y_offset, 10, self.area_size - 10)
                z = self.height_range[0]
                
                uav_positions[cluster_idx] = [x, y, z]
                cluster_idx += 1
            if cluster_idx >= num_in_cluster:
                break

        # --- 2. 生成随机分布的无人机 ---
        for i in range(num_in_cluster, self.n_uavs):
            uav_positions[i] = [
                self.np_random.uniform(0, self.area_size),
                self.np_random.uniform(0, self.area_size),
                self.height_range[0]
            ]
            
        return uav_positions
    
    def _init_uav_positions_start_area(self):
        """
        在指定的起始区域内均匀分布无人机 - 支持固定或随机的起始角落
        
        特点：
        - 无人机在地图边缘的一个正方形区域内均匀分布
        - 区域大小由 uav_start_area_size 参数控制
        - 高度在指定范围内随机分布
        
        返回:
            uav_positions: 无人机位置 [n_uavs, 3]
        """
        uav_positions = np.zeros((self.n_uavs, 3))
        
        margin = 50  # 距离边界的最小距离
        
        # 确保起始区域不超出地图边界
        max_start_area_size = min(self.uav_start_area_size, self.area_size / 2 - margin)
        
        # 起始区域的位置
        start_x_min, start_y_min = 0, 0
        
        # --- 随机化起始角落 ---
        if self.randomize_uav_start:
            corner = self.np_random.randint(0, 4)  # 0:左下, 1:右下, 2:右上, 3:左上
            if corner == 0:  # 左下
                start_x_min = margin
                start_y_min = margin
            elif corner == 1:  # 右下
                start_x_min = self.area_size - max_start_area_size - margin
                start_y_min = margin
            elif corner == 2:  # 右上
                start_x_min = self.area_size - max_start_area_size - margin
                start_y_min = self.area_size - max_start_area_size - margin
            else:  # 左上
                start_x_min = margin
                start_y_min = self.area_size - max_start_area_size - margin
        else:
            # --- 保留原有的固定左下角逻辑 ---
            start_x_min = margin
            start_y_min = margin
        
        start_x_max = start_x_min + max_start_area_size
        start_y_max = start_y_min + max_start_area_size
        
        # 计算网格布局参数
        grid_size = int(np.ceil(np.sqrt(self.n_uavs)))
        
        # 在起始区域内创建网格布局
        uav_idx = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if uav_idx >= self.n_uavs:
                    break
                
                # 计算网格位置（均匀分布）
                if grid_size == 1:
                    # 如果只有一个无人机，放在起始区域中心
                    x = (start_x_min + start_x_max) / 2
                    y = (start_y_min + start_y_max) / 2
                else:
                    # 多个无人机时，在网格中均匀分布
                    x = start_x_min + (start_x_max - start_x_min) * (i + 0.5) / grid_size
                    y = start_y_min + (start_y_max - start_y_min) * (j + 0.5) / grid_size
                
                # 添加小的随机偏移以避免完全重叠
                x_offset = self.np_random.uniform(-20, 20)  # ±20米随机偏移
                y_offset = self.np_random.uniform(-20, 20)
                
                x = np.clip(x + x_offset, 10, self.area_size - 10)
                y = np.clip(y + y_offset, 10, self.area_size - 10)
                
                # 固定高度为最小高度（50m）
                z = self.height_range[0]
                
                uav_positions[uav_idx] = [x, y, z]
                uav_idx += 1
                
            if uav_idx >= self.n_uavs:
                break
        
        return uav_positions
    
    def _calculate_coverage_metrics(self):
        """
        计算并记录核心的覆盖性能指标。
        
        此函数不直接用于奖励计算，而是为更复杂的奖励函数（如calculate_network_health_reward）
        提供基础的性能数据，并填充self.reward_info字典用于日志记录。
        
        返回:
            coverage_ratio: 有效用户覆盖率
        """
        
        # 统计有效连接的用户数量
        effective_connected_users = 0
        total_connected_users = 0
        for i in range(self.n_uavs):
            uav_connected_users = np.sum(self.connections[i])
            total_connected_users += uav_connected_users
            # 只有当UAV有回程路径时，其连接的用户才算有效
            if i in self.routing_paths and self.routing_paths[i][0]:
                effective_connected_users += uav_connected_users
        
        # 计算覆盖率（线性奖励）
        coverage_ratio = effective_connected_users / self.n_users if self.n_users > 0 else 0
        
        # 纯净的线性覆盖率奖励
        shared_global_reward = coverage_ratio
        
        # 计算其他性能指标（仅用于信息记录）
        connected_uavs = len(self.routing_paths)
        avg_hops = 0
        if connected_uavs > 0:
            total_hops = sum(len(path) - 1 for path, capacity in self.routing_paths.values())
            avg_hops = total_hops / connected_uavs
        
        # 更新奖励信息字典，用于调试和可视化
        self.reward_info = {
            "coverage_reward": shared_global_reward,
            "coverage_ratio": coverage_ratio,
            "effective_connected_users": effective_connected_users,
            "total_connected_users": total_connected_users,
            "connected_uavs": connected_uavs,
            "avg_hops": avg_hops,
            "target_coverage_achieved": coverage_ratio >= 0.90,
            "pure_team_reward": shared_global_reward,  # 明确标记这是纯净团队奖励
        }
        
        return coverage_ratio

    def calculate_network_health_reward(self):
        """
        计算一个综合性的、单一的、共享的团队奖励 r_t，称为“网络健康度”。
        该奖励旨在引导算法学会构建一个包含服务和中继角色的、高效的无人机网络。
        
        经实验验证，此奖励塑造函数能有效提升覆盖率性能（从约0.5提升至0.7以上）。
        核心在于通过“服务贡献加权”的角色多样性奖励，激励无人机不仅要成为服务节点，
        还要尽可能服务更多的用户，从而打破局部最优。

        返回:
            shared_team_reward (float): 最终的 r_t 值。
            reward_components (dict): 用于日志记录的奖励组成部分。
        """
        if not hasattr(self, 'routing_paths'):
            return 0.0, {}

        # --- 奖励权重 (从配置中获取) ---
        W_CONNECTIVITY = self.w_connectivity
        W_DIVERSITY = self.w_diversity
        W_COVERAGE = self.w_coverage
        W_DISPERSION = self.w_dispersion

        # --- 1. 连接性得分 (Connectivity Score) ---
        # 衡量有多少比例的无人机成功接入了回程网络（无论是直连还是中继）。
        # 这是构建任何有效覆盖的基础。
        uavs_with_route = len(self.routing_paths)
        connectivity_score = uavs_with_route / self.n_uavs if self.n_uavs > 0 else 0

        # --- 2. 服务贡献加权的角色多样性奖励 (Service-Weighted Role Diversity) ---
        # 改进版奖励：不再简单计数服务无人机，而是计算其“服务贡献”。
        # 贡献度与其服务的用户数正相关 (log(1+x))，以激励更广的覆盖。
        weighted_serving_score = 0
        pure_relay_uavs_count = 0
        serving_uavs_count = 0 # 仍然计数用于日志

        for uav_idx in self.routing_paths: # 只考虑已连接的无人机
            num_connected_users = np.sum(self.connections[uav_idx])
            if num_connected_users > 0:
                serving_uavs_count += 1
                # 使用 log(1+x) 作为贡献值，奖励边际效用递减
                # 这强烈激励了“从无到有”的转变，并鼓励更均衡的覆盖
                weighted_serving_score += np.log1p(num_connected_users)
            else:
                # 如果一个无人机有回程路径，但没有连接任何用户，它就是一个纯粹的中继节点。
                pure_relay_uavs_count += 1
                
        # 奖励来自于两种角色的“平衡”。我们使用几何平均数来激励两种角色都存在。
        # 如果任何一种角色数量为0，则奖励为0。
        # (self.n_uavs / 2) 是一个归一化因子，假设最优情况是角色各占一半。
        # 使用加权服务分代替简单的计数
        role_diversity_bonus = np.sqrt(weighted_serving_score * pure_relay_uavs_count) / (self.n_uavs / 2.0 + 1e-8)

        # --- 3. 有效覆盖得分 (Effective Coverage Score) ---
        # 这就是您原来的奖励，即最终的任务目标。
        effective_coverage_score = self.reward_info.get("coverage_ratio", 0)

        # --- 4. 分散惩罚 (Dispersion Penalty) ---
        # 一个可选但推荐的项，用于防止无人机挤作一团。
        distance_penalties = self._calculate_individual_distance_overlap_penalties()
        dispersion_penalty = np.mean(distance_penalties) if len(distance_penalties) > 0 else 0

        # --- 组合成最终的 r_t ---
        # 这是一个加权和，反映了网络的整体健康状况。
        shared_team_reward = (W_CONNECTIVITY * connectivity_score +
                             W_DIVERSITY * role_diversity_bonus +
                             W_COVERAGE * effective_coverage_score -
                             W_DISPERSION * dispersion_penalty)
        
        # 归一化，使其保持在一个合理的范围内，有利于稳定学习。
        total_positive_weight = W_CONNECTIVITY + W_DIVERSITY + W_COVERAGE
        final_rt = shared_team_reward / total_positive_weight

        # 准备一个字典用于日志记录，这对于调试至关重要！
        reward_components = {
            "rt_final_health_score": final_rt,
            "connectivity_score": connectivity_score,
            "role_diversity_bonus": role_diversity_bonus,
            "effective_coverage_score": effective_coverage_score,
            "dispersion_penalty": dispersion_penalty,
            "serving_uavs_count": serving_uavs_count, # 日志中仍保留原始计数
            "pure_relay_uavs_count": pure_relay_uavs_count,
            "weighted_serving_score": weighted_serving_score # 添加新的加权分数
        }

        return final_rt, reward_components
    
    def render(self):
        """
        渲染环境
        
        返回:
            frame: 渲染帧
        """
        if self.render_mode is None:
            return
        
        return self._render_frame()

    def _render_frame(self):
        """渲染单帧 - 添加强制中继特定的可视化元素"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            print("渲染需要matplotlib库")
            return None
        
        if self.fig is None:
            self.fig = plt.figure(figsize=(10, 8))
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax.clear()

        # 设置坐标轴
        self.ax.set_xlim(0, self.area_size)
        self.ax.set_ylim(0, self.area_size)
        self.ax.set_zlim(0, self.height_range[1] * 1.2)
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title(f'Forced Relay UAV Environment - Step: {self.current_step}/{self.max_steps}')

        # 绘制用户
        if self.user_positions is not None:
            user_x = self.user_positions[:, 0]
            user_y = self.user_positions[:, 1]
            user_z = np.zeros(self.n_users)
            self.ax.scatter(user_x, user_y, user_z, c='blue', marker='.', label='Users')

        # 绘制无人机和连接
        if self.uav_positions is not None:
            for i in range(self.n_uavs):
                uav_pos = self.uav_positions[i]
                self.ax.scatter(uav_pos[0], uav_pos[1], uav_pos[2], c='red', marker='^', s=100, label=f'UAV {i}' if i == 0 else "")
                
                # 绘制到用户的连接
                if self.connections is not None:
                    for j in range(self.n_users):
                        if self.connections[i, j]:
                            user_pos = self.user_positions[j]
                            self.ax.plot([uav_pos[0], user_pos[0]], [uav_pos[1], user_pos[1]], [uav_pos[2], 0], 'g-', alpha=0.3)
        
        # 绘制地面基站
        if self.ground_bs_positions is not None:
            bs_x = self.ground_bs_positions[:, 0]
            bs_y = self.ground_bs_positions[:, 1]
            bs_z = self.ground_bs_positions[:, 2]
            self.ax.scatter(bs_x, bs_y, bs_z, c='black', marker='s', s=120, label='Ground BS')

        # 绘制路由路径
        if hasattr(self, 'routing_paths'):
            for uav_idx, (path, capacity) in self.routing_paths.items():
                for i in range(len(path) - 1):
                    pos1 = self._get_node_pos(path[i])
                    pos2 = self._get_node_pos(path[i+1])
                    self.ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], [pos1[2], pos2[2]], 'y--', alpha=0.7, linewidth=1.5)
        
        # 添加图例
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='upper right')
        
        # 添加强制中继统计信息
        if hasattr(self, 'reward_info'):
            reward_info = self.reward_info
            
            # 左侧显示关键指标
            self.ax.text2D(0.02, 0.85, f'Coverage: {reward_info.get("coverage_ratio", 0):.1%}', 
                          transform=self.ax.transAxes, fontsize=10, weight='bold')
            self.ax.text2D(0.02, 0.80, f'Effective Users: {reward_info.get("effective_connected_users", 0)}/{self.n_users}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.75, f'Connected UAVs: {reward_info.get("connected_uavs", 0)}/{self.n_uavs}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.70, f'Avg Hops: {reward_info.get("avg_hops", 0):.1f}', 
                          transform=self.ax.transAxes)
            
            # 右侧显示奖励组成
            self.ax.text2D(0.75, 0.85, f'Coverage Reward: {reward_info.get("coverage_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9)
            self.ax.text2D(0.75, 0.80, f'Link Quality Reward: {reward_info.get("link_quality_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9)
            self.ax.text2D(0.75, 0.70, f'Overlap Penalty: {reward_info.get("coverage_overlap_penalty", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9, color='red')
            self.ax.text2D(0.75, 0.65, f'Total Reward: {reward_info.get("final_global_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9, weight='bold')
            
            # 目标达成状态
            if reward_info.get("target_coverage_achieved", False):
                self.ax.text2D(0.02, 0.65, '✓ Target Coverage Achieved!', 
                              transform=self.ax.transAxes, color='green', weight='bold')
            else:
                self.ax.text2D(0.02, 0.65, '⚠ Target Coverage Not Achieved', 
                              transform=self.ax.transAxes, color='orange')
        
        self.fig.canvas.draw()
        
        if self.render_mode == "human":
            plt.pause(0.01)
            return None
        
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        image = np.array(canvas.renderer.buffer_rgba())
        return image
    
    def _get_cluster_centers(self):
        """
        获取用户簇的中心位置（用于可视化） - 更新为动态计算
        
        返回:
            cluster_centers: 簇中心位置列表
        """
        if not hasattr(self, 'user_positions') or self.user_positions is None:
            return []
        
        # 重新计算动态用户区域（与_generate_forced_relay_cluster_positions保持一致）
        bs_center = np.mean(self.ground_bs_positions[:, :2], axis=0)
        map_center = np.array([self.area_size / 2, self.area_size / 2])
        
        user_area_margin = self.area_size * 0.1
        user_area_size = self.area_size * 0.4
        
        # 根据基站中心位置确定用户区域的位置
        if bs_center[0] < map_center[0]:  # 基站在左侧
            user_x_min = self.area_size - user_area_size - user_area_margin
            user_x_max = self.area_size - user_area_margin
        else:  # 基站在右侧
            user_x_min = user_area_margin
            user_x_max = user_area_margin + user_area_size
            
        if bs_center[1] < map_center[1]:  # 基站在下方
            user_y_min = self.area_size - user_area_size - user_area_margin
            user_y_max = self.area_size - user_area_margin
        else:  # 基站在上方
            user_y_min = user_area_margin
            user_y_max = user_area_margin + user_area_size
        
        cluster_centers = []
        
        if self.n_clusters == 4:
            cluster_centers = [
                [user_x_min + (user_x_max - user_x_min) * 0.3, user_y_min + (user_y_max - user_y_min) * 0.3],
                [user_x_min + (user_x_max - user_x_min) * 0.7, user_y_min + (user_y_max - user_y_min) * 0.3],
                [user_x_min + (user_x_max - user_x_min) * 0.3, user_y_min + (user_y_max - user_y_min) * 0.7],
                [user_x_min + (user_x_max - user_x_min) * 0.7, user_y_min + (user_y_max - user_y_min) * 0.7]
            ]
        elif self.n_clusters == 3:
            cluster_centers = [
                [user_x_min + (user_x_max - user_x_min) * 0.5, user_y_min + (user_y_max - user_y_min) * 0.2],
                [user_x_min + (user_x_max - user_x_min) * 0.2, user_y_min + (user_y_max - user_y_min) * 0.8],
                [user_x_min + (user_x_max - user_x_min) * 0.8, user_y_min + (user_y_max - user_y_min) * 0.8]
            ]
        elif self.n_clusters == 5:
            cluster_centers = [
                [user_x_min + (user_x_max - user_x_min) * 0.5, user_y_min + (user_y_max - user_y_min) * 0.5],
                [user_x_min + (user_x_max - user_x_min) * 0.2, user_y_min + (user_y_max - user_y_min) * 0.2],
                [user_x_min + (user_x_max - user_x_min) * 0.8, user_y_min + (user_y_max - user_y_min) * 0.2],
                [user_x_min + (user_x_max - user_x_min) * 0.2, user_y_min + (user_y_max - user_y_min) * 0.8],
                [user_x_min + (user_x_max - user_x_min) * 0.8, user_y_min + (user_y_max - user_y_min) * 0.8]
            ]
        else:
            # 其他情况使用网格布局
            grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
            cluster_idx = 0
            
            for i in range(grid_size):
                for j in range(grid_size):
                    if cluster_idx >= self.n_clusters:
                        break
                    
                    grid_x = user_x_min + (user_x_max - user_x_min) * (i + 0.5) / grid_size
                    grid_y = user_y_min + (user_y_max - user_y_min) * (j + 0.5) / grid_size
                    
                    cluster_centers.append([grid_x, grid_y])
                    cluster_idx += 1
                
                if cluster_idx >= self.n_clusters:
                    break
        
        return cluster_centers
    
    def reset(self, seed=None, options=None):
        """
        重置环境，为新一轮的动态仿真做准备。
        
        返回:
            observations: 所有智能体的观测字典
            infos: 所有智能体的信息字典
        """
        # 1. 重置随机种子和基本环境状态
        if seed is not None:
            self.seed_val = seed
            self.np_random = np.random.RandomState(seed)
        
        self.current_step = 0
        self.agents = self.possible_agents.copy()
        
        # Reset belief map and user serviced status
        self.user_serviced_status.fill(False)
        # Initialize belief map to uniform distribution
        self.belief_map.fill(1.0 / (self.grid_resolution**2))
        self.discovered_users_this_episode.clear()
        
        # 2. 使用本类的方法初始化UAV和用户位置
        self.uav_positions = self._init_uav_positions()
        self.user_positions = self._generate_user_positions()
        self._initialize_user_waypoints()
        
        # 3. 初始化连接和路由信息
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        self.sinr_matrix = np.zeros((self.n_uavs, self.n_users))
        self.uav_connections = np.zeros((self.n_uavs, self.n_uavs), dtype=bool)
        self.uav_bs_connections = np.zeros((self.n_uavs, self.n_ground_bs), dtype=bool)
        self.routing_paths = {}
        
        # 4. 更新信道状态、连接和路由
        self._update_channel_state()  # 从父类继承
        self._update_uav_connections() # 从父类继承
        self._compute_routing_paths()  # 使用本类的路由计算
        
        # 4.5 初始化新增的 Reward Shaping 相关变量
        self.previous_bottleneck_capacities = np.zeros(self.n_uavs)
        
        # 4.6 初始化密度预测系统（如果启用）
        if self.density_prediction:
            # 更新初始密度图和速度图
            self._update_density_and_velocity_maps()
            # 预测未来密度分布
            self._predict_future_density_map()
        
        # 5. 获取观测值
        observations = {}
        infos = {}
        for agent in self.agents:
            # 注意：这里需要调用父类的_get_observation和_update_observations_dict
            # 为了简化，我们先获取基础观测，再在循环外统一更新
            observations[agent] = self._get_observation(agent)
            infos[agent] = {}
            
        # 6. 更新包含连接和跳数信息的观测
        observations = self._update_observations_dict(observations)
        
        # 7. Calculate initial potential and set state
        current_state = self._get_state()
        self.state = current_state
        
        # 为每个智能体的info添加正确的state
        for agent in self.agents:
            infos[agent]['state'] = current_state.copy()
            
        return observations, infos

    def _compute_sinr(self, uav_idx, user_idx):
        """
        重写父类方法，使用场景4的精确信道模型计算SINR
        """
        uav_pos = self.uav_positions[uav_idx]
        user_pos_3d = self.user_positions[user_idx]  # 现在用户位置已经是三维的
        
        # 使用精确的A2G路径损耗模型
        path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的UAV-User SINR计算
        sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
        
        return sinr_db

    def _update_density_and_velocity_maps(self):
        """
        更新密度图和速度图 - 基于当前用户位置和速度
        
        此方法会在每个step中被调用。它会遍历所有用户，根据其当前位置和速度，
        将他们'分配'到对应的网格中，从而计算出最新的self.density_map和self.velocity_map。
        
        核心思想：
        - 将连续的用户位置离散化到网格单元中
        - 计算每个网格单元的用户密度（用户数量/单元面积）
        - 计算每个网格单元的平均用户速度向量
        - 使用高斯核进行空间平滑，避免过度离散化
        """
        if not self.density_prediction:
            return
        
        # 边界检查：确保必要的属性存在
        if not hasattr(self, 'density_map') or self.density_map is None:
            return
        if not hasattr(self, 'velocity_map') or self.velocity_map is None:
            return
        if not hasattr(self, 'user_positions') or self.user_positions is None:
            return
        if not hasattr(self, 'user_velocities') or self.user_velocities is None:
            return
        
        # 重置密度图和速度图
        self.density_map.fill(0.0)
        self.velocity_map.fill(0.0)
        
        # 用于累积每个网格单元的用户数量和速度
        user_count_per_cell = np.zeros((self.density_grid_resolution, self.density_grid_resolution))
        velocity_sum_per_cell = np.zeros((self.density_grid_resolution, self.density_grid_resolution, 2))
        
        # 遍历所有用户，将其分配到对应的网格单元
        for user_idx in range(self.n_users):
            user_pos = self.user_positions[user_idx, :2]  # 只取x, y坐标
            user_vel = self.user_velocities[user_idx]  # 2D速度向量
            
            # 计算用户所在的网格坐标
            grid_x = int(np.clip(user_pos[0] / self.density_cell_size, 0, self.density_grid_resolution - 1))
            grid_y = int(np.clip(user_pos[1] / self.density_cell_size, 0, self.density_grid_resolution - 1))
            
            # 基础分配：将用户分配到其所在的网格单元
            user_count_per_cell[grid_y, grid_x] += 1.0
            velocity_sum_per_cell[grid_y, grid_x] += user_vel
            
            # 高斯平滑：将用户的影响扩散到邻近网格单元
            # 使用标准差为1个网格单元的高斯核
            sigma = 1.0  # 网格单元为单位
            gaussian_radius = 2  # 影响半径（网格单元数）
            
            for dy in range(-gaussian_radius, gaussian_radius + 1):
                for dx in range(-gaussian_radius, gaussian_radius + 1):
                    neighbor_x = grid_x + dx
                    neighbor_y = grid_y + dy
                    
                    # 检查邻居网格是否在有效范围内
                    if (0 <= neighbor_x < self.density_grid_resolution and 
                        0 <= neighbor_y < self.density_grid_resolution):
                        
                        # 计算高斯权重
                        distance_sq = dx*dx + dy*dy
                        weight = np.exp(-distance_sq / (2 * sigma*sigma))
                        
                        # 如果不是中心网格，应用高斯权重
                        if dx != 0 or dy != 0:
                            user_count_per_cell[neighbor_y, neighbor_x] += weight * 0.3  # 30%的扩散强度
                            velocity_sum_per_cell[neighbor_y, neighbor_x] += weight * 0.3 * user_vel
        
        # 计算密度图：用户数量除以网格单元面积
        cell_area = self.density_cell_size * self.density_cell_size  # 平方米
        self.density_map = user_count_per_cell / cell_area  # 用户数量/平方米
        
        # 计算平均速度图：总速度除以用户数量
        for y in range(self.density_grid_resolution):
            for x in range(self.density_grid_resolution):
                if user_count_per_cell[y, x] > 0:
                    self.velocity_map[y, x] = velocity_sum_per_cell[y, x] / user_count_per_cell[y, x]
                else:
                    self.velocity_map[y, x] = np.zeros(2)  # 无用户的网格速度为零
        
        # 应用速度平滑滤波器，减少噪声
        if self.velocity_smoothing_factor > 0:
            self._apply_velocity_smoothing()

    def _apply_velocity_smoothing(self):
        """
        对速度图应用空间平滑滤波器，减少噪声和不连续性
        
        使用简单的3x3平均滤波器进行平滑
        """
        smoothed_velocity_map = self.velocity_map.copy()
        
        for y in range(1, self.density_grid_resolution - 1):
            for x in range(1, self.density_grid_resolution - 1):
                # 计算3x3邻域的平均速度
                neighborhood_velocities = self.velocity_map[y-1:y+2, x-1:x+2]  # 3x3区域
                
                # 只考虑有用户的网格单元
                valid_mask = np.any(neighborhood_velocities != 0, axis=2)  # 检查速度向量是否非零
                
                if np.any(valid_mask):
                    # 计算有效邻居的平均速度
                    valid_velocities = neighborhood_velocities[valid_mask]
                    avg_velocity = np.mean(valid_velocities, axis=0)
                    
                    # 应用平滑因子：原始速度 * (1-α) + 平滑速度 * α
                    original_velocity = self.velocity_map[y, x]
                    smoothed_velocity_map[y, x] = (
                        (1 - self.velocity_smoothing_factor) * original_velocity + 
                        self.velocity_smoothing_factor * avg_velocity
                    )
        
        self.velocity_map = smoothed_velocity_map

    def _predict_future_density_map(self):
        """
        使用拉格朗日平流（Lagrangian Advection）预测未来k步后的用户密度分布
        
        核心算法：
        1. 基于当前密度图和速度图，使用拉格朗日平流方程预测密度演化
        2. 拉格朗日平流方程：∂ρ/∂t + ∇·(ρv) = 0
        3. 离散化实现：ρ(t+Δt) = ρ(t) - Δt * ∇·(ρv)
        4. 迭代k步得到未来密度分布
        
        这种方法的优势：
        - 不需要预先知道用户群体结构
        - 能够处理动态变化的用户分布
        - 基于物理原理，具有良好的理论基础
        """
        if not self.density_prediction:
            return
        
        # 初始化预测密度图为当前密度图
        predicted_density = self.density_map.copy()
        predicted_velocity = self.velocity_map.copy()
        
        # 时间步长（秒）
        dt = self.time_step
        
        # 迭代预测k步
        for step in range(self.prediction_horizon_k):
            # 应用拉格朗日平流方程的离散化版本
            predicted_density = self._apply_lagrangian_advection_step(
                predicted_density, predicted_velocity, dt
            )
            
            # 应用密度扩散（模拟用户的随机移动和不确定性）
            predicted_density = self._apply_density_diffusion(predicted_density)
            
            # 更新速度图（简化假设：速度在短期内保持相对稳定）
            # 在实际应用中，可以根据历史数据学习速度演化模式
            predicted_velocity = self._update_predicted_velocity(predicted_velocity)
        
        # 存储预测结果
        self.predicted_density_map = predicted_density
        
        # 确保密度图的非负性和数值稳定性
        self.predicted_density_map = np.clip(self.predicted_density_map, 0, np.inf)

    def _apply_lagrangian_advection_step(self, density, velocity, dt):
        """
        应用拉格朗日平流方程的一个时间步
        
        使用上风差分格式（Upwind Scheme）求解平流方程：
        ∂ρ/∂t + ∇·(ρv) = 0
        
        参数:
            density: 当前密度图 (G x G)
            velocity: 当前速度图 (G x G x 2)
            dt: 时间步长
            
        返回:
            new_density: 更新后的密度图 (G x G)
        """
        new_density = density.copy()
        
        # 网格间距（米）
        dx = self.density_cell_size
        dy = self.density_cell_size
        
        # 遍历所有内部网格点（避免边界问题）
        for y in range(1, self.density_grid_resolution - 1):
            for x in range(1, self.density_grid_resolution - 1):
                # 当前网格的密度和速度
                rho = density[y, x]
                vx = velocity[y, x, 0]  # x方向速度
                vy = velocity[y, x, 1]  # y方向速度
                
                # 计算密度梯度（中心差分）
                drho_dx = (density[y, x+1] - density[y, x-1]) / (2 * dx)
                drho_dy = (density[y+1, x] - density[y-1, x]) / (2 * dy)
                
                # 计算速度散度（中心差分）
                dvx_dx = (velocity[y, x+1, 0] - velocity[y, x-1, 0]) / (2 * dx)
                dvy_dy = (velocity[y+1, x, 1] - velocity[y-1, x, 1]) / (2 * dy)
                
                # 拉格朗日平流方程的离散化：
                # ∂ρ/∂t = -∇·(ρv) = -(ρ∇·v + v·∇ρ)
                advection_term = -(rho * (dvx_dx + dvy_dy) + vx * drho_dx + vy * drho_dy)
                
                # 更新密度
                new_density[y, x] = density[y, x] + dt * advection_term
        
        # 处理边界条件（使用零梯度边界条件）
        new_density[0, :] = new_density[1, :]      # 下边界
        new_density[-1, :] = new_density[-2, :]   # 上边界
        new_density[:, 0] = new_density[:, 1]     # 左边界
        new_density[:, -1] = new_density[:, -2]   # 右边界
        
        return new_density

    def _apply_density_diffusion(self, density):
        """
        应用密度扩散，模拟用户移动的随机性和不确定性
        
        使用简单的扩散方程：∂ρ/∂t = D∇²ρ
        其中D是扩散系数
        
        参数:
            density: 当前密度图 (G x G)
            
        返回:
            diffused_density: 扩散后的密度图 (G x G)
        """
        diffused_density = density.copy()
        
        # 扩散系数
        D = self.density_diffusion_rate
        
        # 网格间距
        dx = self.density_cell_size
        dy = self.density_cell_size
        
        # 时间步长
        dt = self.time_step
        
        # 遍历所有内部网格点
        for y in range(1, self.density_grid_resolution - 1):
            for x in range(1, self.density_grid_resolution - 1):
                # 计算拉普拉斯算子（二阶导数）
                d2rho_dx2 = (density[y, x+1] - 2*density[y, x] + density[y, x-1]) / (dx*dx)
                d2rho_dy2 = (density[y+1, x] - 2*density[y, x] + density[y-1, x]) / (dy*dy)
                
                # 扩散项
                diffusion_term = D * (d2rho_dx2 + d2rho_dy2)
                
                # 更新密度
                diffused_density[y, x] = density[y, x] + dt * diffusion_term
        
        return diffused_density

    def _update_predicted_velocity(self, velocity):
        """
        更新预测的速度图
        
        简化假设：速度在短期内保持相对稳定，但会逐渐衰减
        在更复杂的实现中，可以基于历史数据学习速度演化模式
        
        参数:
            velocity: 当前速度图 (G x G x 2)
            
        返回:
            updated_velocity: 更新后的速度图 (G x G x 2)
        """
        # 简单的速度衰减模型
        velocity_decay_factor = 0.95  # 速度逐渐衰减
        
        updated_velocity = velocity * velocity_decay_factor
        
        return updated_velocity

    def _calculate_belief_map_statistics(self):
        """
        计算信念地图的统计信息，用于TensorBoard记录
        
        返回:
            belief_stats: 包含各种信念地图统计信息的字典
        """
        belief_stats = {}
        
        # 1. 信念地图熵 (Shannon Entropy)
        # H = -Σ p_i * log(p_i)
        epsilon = 1e-9
        belief_flat = self.belief_map.flatten()
        belief_flat_safe = np.clip(belief_flat, epsilon, 1.0)
        entropy = -np.sum(belief_flat_safe * np.log(belief_flat_safe))
        belief_stats['belief_map_entropy'] = entropy
        
        # 2. 信念地图覆盖度 (非零信念区域的比例)
        non_zero_cells = np.sum(self.belief_map > epsilon)
        total_cells = self.grid_resolution * self.grid_resolution
        coverage = non_zero_cells / total_cells
        belief_stats['belief_map_coverage'] = coverage
        
        # 3. 信念地图最大值和最小值
        belief_stats['belief_map_max_value'] = np.max(self.belief_map)
        belief_stats['belief_map_min_value'] = np.min(self.belief_map)
        
        # 4. 信念地图标准差
        belief_stats['belief_map_std'] = np.std(self.belief_map)
        
        # 5. 发现vs预测准确性
        # 计算实际发现用户的位置与高信念区域的重叠度
        if hasattr(self, 'discovered_users_this_episode') and self.discovered_users_this_episode:
            discovered_positions = []
            for user_idx in self.discovered_users_this_episode:
                if user_idx < len(self.user_positions):
                    discovered_positions.append(self.user_positions[user_idx])
            
            if discovered_positions:
                # 计算发现位置的平均信念值
                total_belief_at_discoveries = 0
                for pos in discovered_positions:
                    gx, gy = self._get_grid_coords(pos)
                    total_belief_at_discoveries += self.belief_map[gy, gx]
                
                avg_belief_at_discoveries = total_belief_at_discoveries / len(discovered_positions)
                # 归一化为预测准确性分数 (0-1)
                max_possible_belief = np.max(self.belief_map)
                if max_possible_belief > epsilon:
                    prediction_accuracy = avg_belief_at_discoveries / max_possible_belief
                else:
                    prediction_accuracy = 0
                belief_stats['belief_prediction_accuracy'] = prediction_accuracy
                belief_stats['discovered_vs_predicted'] = avg_belief_at_discoveries
            else:
                belief_stats['belief_prediction_accuracy'] = 0
                belief_stats['discovered_vs_predicted'] = 0
        else:
            belief_stats['belief_prediction_accuracy'] = 0
            belief_stats['discovered_vs_predicted'] = 0
        
        # 6. 高信念和低信念区域计数
        # 定义阈值：高于平均值的为高信念区域，低于平均值的为低信念区域
        mean_belief = np.mean(self.belief_map)
        high_belief_regions = np.sum(self.belief_map > mean_belief)
        low_belief_regions = np.sum(self.belief_map < mean_belief)
        
        belief_stats['high_belief_regions_count'] = high_belief_regions
        belief_stats['low_belief_regions_count'] = low_belief_regions
        
        # 7. 信念集中度比率 (前10%最高信念区域包含的总信念比例)
        belief_flat_sorted = np.sort(belief_flat)[::-1]  # 降序排列
        top_10_percent_count = max(1, int(0.1 * len(belief_flat_sorted)))
        top_10_percent_belief = np.sum(belief_flat_sorted[:top_10_percent_count])
        total_belief = np.sum(belief_flat_sorted)
        
        if total_belief > epsilon:
            concentration_ratio = top_10_percent_belief / total_belief
        else:
            concentration_ratio = 0
        belief_stats['belief_concentration_ratio'] = concentration_ratio
        
        return belief_stats

    def get_current_state(self):
        """
        获取当前环境状态，用于调试和可视化
        
        返回:
            state_dict: 包含当前环境状态的字典
        """
        state_dict = {
            'uav_positions': self.uav_positions.copy() if hasattr(self, 'uav_positions') else None,
            'user_positions': self.user_positions.copy() if hasattr(self, 'user_positions') else None,
            'ground_bs_positions': self.ground_bs_positions.copy() if hasattr(self, 'ground_bs_positions') else None,
            'area_size': self.area_size,
            'current_step': getattr(self, 'current_step', 0),
            'max_steps': self.max_steps,
            'belief_map': self.belief_map.copy() if hasattr(self, 'belief_map') else None,
            'discovered_users_this_episode': list(self.discovered_users_this_episode) if hasattr(self, 'discovered_users_this_episode') else [],
            'grid_resolution': self.grid_resolution,
            'connections': self.connections.copy() if hasattr(self, 'connections') else None,
            'routing_paths': dict(self.routing_paths) if hasattr(self, 'routing_paths') else {}
        }
        
        return state_dict
    
    def _compute_interference_radius(self):
        """
        基于信道条件动态计算干扰半径（移除上限，增强干扰）
        
        核心思想：
        - 计算在给定发射功率下，能够产生有意义干扰的最大传播距离
        - "有意义干扰"定义为干扰功率高于噪声功率一定倍数（如3dB）
        - 移除上限，确保所有可能的干扰源都被考虑
        
        返回:
            interference_radius: 动态计算的干扰半径（米）
        """
        # 定义最小有意义干扰功率阈值（相对于噪声功率）
        # 例如：干扰功率至少要比噪声功率高3dB才被认为是"有意义的"
        min_interference_margin_db = 3.0
        min_interference_power_dbm = self.noise_power + min_interference_margin_db
        
        # 计算在自由空间传播下，达到最小干扰功率所需的最大距离
        # 使用自由空间路径损耗公式的逆运算：
        # PL = 20*log10(d) + 20*log10(f) - 147.55
        # d = 10^((Tx_power - Rx_power - 20*log10(f) + 147.55) / 20)
        
        path_loss_required = self.tx_power - min_interference_power_dbm
        
        # 自由空间路径损耗公式中的常数项
        fspl_constant = 20 * np.log10(self.carrier_frequency) - 147.55
        
        # 计算距离（米）
        distance_exponent = (path_loss_required - fspl_constant) / 20.0
        max_interference_distance = 10 ** distance_exponent
        
        # 移除上限，只保留最小值以确保合理性
        min_radius = 500.0  # 最小500米
        
        interference_radius = max(max_interference_distance, min_radius)
        
        return interference_radius

    def _update_channel_state(self):
        """
        重写父类方法，确保使用场景4的精确SINR计算
        同时在此函数中计算发现奖励，确保使用最新的信道状态
        """
        # 计算所有UAV-用户对的SINR
        for i in range(self.n_uavs):
            for j in range(self.n_users):
                self.sinr_matrix[i, j] = self._compute_sinr(i, j)
        
        # 更新连接（贪婪算法）
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        
        # 按SINR降序排列所有UAV-用户对
        uav_user_pairs = []
        for i in range(self.n_uavs):
            for j in range(self.n_users):
                if self.sinr_matrix[i, j] >= self.min_sinr:
                    uav_user_pairs.append((i, j, self.sinr_matrix[i, j]))
        
        # 按SINR降序排序
        uav_user_pairs.sort(key=lambda x: x[2], reverse=True)
        
        # 分配连接
        uav_connections = [0] * self.n_uavs
        user_connected = [False] * self.n_users
        
        for uav_idx, user_idx, sinr in uav_user_pairs:
            # 如果UAV未达到最大连接数且用户未连接
            if uav_connections[uav_idx] < self.max_connections and not user_connected[user_idx]:
                self.connections[uav_idx, user_idx] = True
                uav_connections[uav_idx] += 1
                user_connected[user_idx] = True
        
        # 移除这里的发现奖励计算调用 - 将在step函数中的正确位置调用
    
    def _calculate_discovery_reward_inline(self):
        """
        基于信念地图计算发现用户奖励 (Belief-Modulated Discovery Reward)
        
        核心思想：
        - 只有第一次发现的用户才能获得奖励
        - 发现奖励的大小与发现时该区域的信念值成反比
        - 在低信念区域（意外区域）发现用户获得更高奖励
        - 在高信念区域（预期区域）发现用户获得较低奖励
        
        结果存储在实例变量中，供step函数使用
        """
        total_discovery_reward = 0.0
        newly_discovered_user_count = 0
        epsilon = 1e-8  # 防止除以零的小常数
        
        # 获取当前所有被覆盖的用户位置（无论是否连接）
        all_covered_users = set()
        
        # 遍历所有UAV-用户对，找出能够覆盖的用户
        # 直接使用刚刚计算的sinr_matrix，确保数据一致性
        for uav_idx in range(self.n_uavs):
            for user_idx in range(self.n_users):
                if self.sinr_matrix[uav_idx, user_idx] >= self.min_sinr:
                    all_covered_users.add(user_idx)
        
        # 检查新发现的用户并计算基于信念的动态奖励
        for user_idx in all_covered_users:
            if user_idx not in self.discovered_users_this_episode:
                newly_discovered_user_count += 1
                self.discovered_users_this_episode.add(user_idx)
                
                # 获取用户所在栅格的信念值
                user_pos = self.user_positions[user_idx]
                gx, gy = self._get_grid_coords(user_pos)
                belief_at_discovery = self.belief_map[gy, gx]
                
                # 基于信念值计算动态奖励
                # 信念值越低（越意外），奖励越高
                base_reward = getattr(self, 'discovery_reward_value', 10.0)
                dynamic_reward = base_reward / (belief_at_discovery + epsilon)
                total_discovery_reward += dynamic_reward
        
        # 存储结果到实例变量，供step函数使用
        self.last_discovery_reward = total_discovery_reward
        self.last_newly_discovered_count = newly_discovered_user_count

    def _compute_uav_to_uav_sinr(self, sender_idx, receiver_idx):
        """
        使用场景4的精确信道模型计算UAV到UAV的SINR
        """
        sender_pos = self.uav_positions[sender_idx]
        receiver_pos = self.uav_positions[receiver_idx]
        
        # 使用精确的A2A路径损耗模型
        path_loss = self._compute_air_to_air_path_loss(sender_pos, receiver_pos)
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的链路SINR计算（考虑干扰）
        sinr_db = self._compute_link_sinr("uav", sender_idx, "uav", receiver_idx, rx_power)
        
        return sinr_db

    def _update_uav_connections(self):
        """
        重写父类方法，确保使用场景4的精确信道模型更新UAV间和UAV到基站的连接
        """
        # 更新UAV之间的连接
        for i in range(self.n_uavs):
            for j in range(i + 1, self.n_uavs):
                # 使用本类的精确SINR计算
                sinr_ij = self._compute_uav_to_uav_sinr(i, j)
                sinr_ji = self._compute_uav_to_uav_sinr(j, i)
                
                # 双向连接需要两个方向的SINR都满足阈值
                if sinr_ij >= self.min_sinr and sinr_ji >= self.min_sinr:
                    self.uav_connections[i, j] = True
                    self.uav_connections[j, i] = True
                else:
                    self.uav_connections[i, j] = False
                    self.uav_connections[j, i] = False
        
        # 更新UAV到地面基站的连接
        for i in range(self.n_uavs):
            for j in range(self.n_ground_bs):
                # 使用精确的链路容量计算，如果容量大于0，则认为可连接
                # G2A方向（下行）
                capacity_g2a = self._get_link_capacity("ground_bs", j, "uav", i)
                # A2G方向（上行）
                capacity_a2g = self._get_link_capacity("uav", i, "ground_bs", j)
                
                # 需要双向都能通信才算建立连接
                if capacity_g2a > 0 and capacity_a2g > 0:
                    self.uav_bs_connections[i, j] = True
                else:
                    self.uav_bs_connections[i, j] = False
    
    def step(self, actions):
        """
        执行环境步骤 - 确保使用场景4特定的全局状态和信道模型
        
        参数:
            actions: 所有智能体的动作字典 {agent_id: action}
            
        返回:
            observations: 所有智能体的下一个观测字典
            rewards: 所有智能体的奖励字典
            terminations: 所有智能体的终止状态字典
            truncations: 所有智能体的截断状态字典
            infos: 所有智能体的信息字典
        """
        # 2. Update agent positions based on actions
        for agent_idx, agent in enumerate(self.agents):
            if agent in actions:
                # 【关键修复】正确处理动作向量以控制速度和方向
                # The action vector from the policy is in the range [-1, 1] for each dimension.
                # We directly scale this to the maximum velocity.
                action_vec = actions[agent]
                velocity = action_vec * self.max_speed
                
                new_position = self.uav_positions[agent_idx] + velocity * self.time_step
                
                # Boundary checks
                new_position[0] = np.clip(new_position[0], 0, self.area_size)
                new_position[1] = np.clip(new_position[1], 0, self.area_size)
                new_position[2] = np.clip(new_position[2], *self.height_range)
                self.uav_positions[agent_idx] = new_position
        
        # 3. Update system state based on new positions
        self._update_user_positions()
        self._predict_belief_map()
        self._update_channel_state()
        self._update_belief_map_from_observation() # Update belief based on new observations
        self._update_uav_connections()
        self._compute_routing_paths()
        self._calculate_discovery_reward_inline() # Calculate discovery reward after all updates

        # 3.5 更新密度预测系统（如果启用）
        if self.density_prediction:
            # 更新当前密度图和速度图
            self._update_density_and_velocity_maps()
            # 预测未来密度分布
            self._predict_future_density_map()


        # 4. Check for newly serviced users and update belief map
        for user_idx in range(self.n_users):
            # Check if user is not yet serviced but is now connected by a UAV with a valid route
            is_effectively_connected = False
            if not self.user_serviced_status[user_idx]:
                for uav_idx in range(self.n_uavs):
                    if self.connections[uav_idx, user_idx] and uav_idx in self.routing_paths:
                        is_effectively_connected = True
                        break
            
            if is_effectively_connected:
                self.user_serviced_status[user_idx] = True
        
        # 7. CALCULATE REWARDS
        # 首先，计算核心覆盖指标并更新 self.reward_info，供塑形奖励函数使用
        self._calculate_coverage_metrics()

        # 然后，计算新的、综合性的“网络健康度”作为共享团队奖励 r_t
        shaped_team_reward, reward_components = self.calculate_network_health_reward()
        
        # Add the belief-modulated discovery reward
        discovery_reward = getattr(self, 'last_discovery_reward', 0.0)
        shaped_team_reward += discovery_reward
        reward_components['discovery_reward'] = discovery_reward

        # 计算信念地图统计信息
        belief_map_stats = self._calculate_belief_map_statistics()
        # 将信念地图统计信息添加到奖励组件中，供TensorBoard记录
        reward_components.update(belief_map_stats)


        # 8. 计算系统吞吐量 (在计算完路由和奖励之后)
        system_throughput_mbps, avg_throughput_per_user_mbps = self._calculate_system_throughput()
        self.reward_info['system_throughput_mbps'] = system_throughput_mbps
        self.reward_info['avg_throughput_per_user_mbps'] = avg_throughput_per_user_mbps

        # 11. 更新步数并检查终止/截断条件
        self.current_step += 1
        # 检查是否因为达到最大步数而被截断
        is_truncated = self.current_step >= self.max_steps
        # 在这个环境中，我们没有定义其他自然终止条件，所以 is_terminated 总是 False
        is_terminated = False

        # 12. 准备返回值
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        # 根据模式计算奖励
        if self.test_reward_mode:
            penalties = self._calculate_individual_distance_overlap_penalties()
            # 【修复】计算平均惩罚，并将其作为共享奖励信号
            mean_penalty = np.mean(penalties)
            shared_reward = -mean_penalty
            for agent in self.agents:
                rewards[agent] = shared_reward
        else:
            # 所有智能体接收完全相同的共享团队奖励 r_t
            for agent in self.agents:
                rewards[agent] = shaped_team_reward

        # 13. 获取新的观测并填充返回值
        for agent_idx, agent in enumerate(self.agents):
            observations[agent] = self._get_observation(agent)

            # 【核心修正】正确设置 termination 和 truncation
            terminations[agent] = is_terminated
            truncations[agent] = is_truncated
            
            # 将详细的奖励分解信息放入 info 字典，用于监控和调试
            infos[agent] = {
                "reward_info": reward_components,
                "coverage_ratio": self.reward_info.get("coverage_ratio", 0),
                "connectivity_ratio": len(self.routing_paths) / self.n_uavs if self.n_uavs > 0 else 0,
                # 【关键修复】：添加当前UAV位置到info中，避免环境重置后位置丢失
                "uav_positions": self.uav_positions.copy(),
            }
        
        # 7. 更新观测值（在循环外一次性完成）
        observations = self._update_observations_dict(observations)

        # 8. 计算并添加 next_state 到 infos
        next_state = self._get_state()
        self.state = next_state
        for agent in self.agents:
            infos[agent]['next_state'] = next_state.copy()
            
        return observations, rewards, terminations, truncations, infos

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def close(self):
        if self.fig is not None:
            import matplotlib.pyplot as plt
            plt.close(self.fig)
            self.fig = None
            self.ax = None

    def _get_node_pos(self, node):
        node_type, node_idx = node
        if node_type == "uav":
            return self.uav_positions[node_idx]
        elif node_type == "ground_bs":
            return self.ground_bs_positions[node_idx]
        return None

    def _calculate_system_throughput(self):
        """
        计算整个系统的总吞吐量和平均用户吞吐量。
        
        返回:
            total_throughput_mbps (float): 系统总吞吐量 (Mbps)
            avg_throughput_per_user_mbps (float): 平均每个有效用户的吞吐量 (Mbps)
        """
        total_throughput_bps = 0
        effective_users = set()

        # 遍历所有具有有效回程路径的UAV
        for uav_idx, (path, bottleneck_capacity) in self.routing_paths.items():
            # 找出连接到这个UAV的用户
            connected_user_indices = np.where(self.connections[uav_idx])[0]
            
            if len(connected_user_indices) == 0:
                continue

            # 计算该UAV的前端总容量
            frontend_capacity = self._compute_uav_frontend_capacity(uav_idx, connected_user_indices)
            
            # 该UAV能提供的总吞吐量受限于前端容量和回程瓶颈容量
            uav_throughput = min(frontend_capacity, bottleneck_capacity)
            
            # 将该UAV的吞吐量累加到系统总吞吐量
            total_throughput_bps += uav_throughput
            
            # 将这些用户标记为有效用户
            for user_idx in connected_user_indices:
                effective_users.add(user_idx)

        total_throughput_mbps = total_throughput_bps / 1e6  # 转换为Mbps
        
        num_effective_users = len(effective_users)
        if num_effective_users > 0:
            avg_throughput_per_user_mbps = total_throughput_mbps / num_effective_users
        else:
            avg_throughput_per_user_mbps = 0

        return total_throughput_mbps, avg_throughput_per_user_mbps


    def _get_observation(self, agent):
        """
        获取指定智能体基于通信能力的局部观测
        
        参数:
            agent: 智能体ID
            
        返回:
            observation: 智能体的观测
        """
        agent_idx = int(agent.split("_")[1])
        own_position = self.uav_positions[agent_idx]
        
        # 初始化观测向量
        obs_components = []
        
        # 1. 自身位置 (3维) - 归一化到[0,1]范围
        normalized_position = own_position.copy()
        normalized_position[:2] /= self.area_size
        normalized_position[2] = (own_position[2] - self.height_range[0]) / (self.height_range[1] - self.height_range[0])
        obs_components.append(normalized_position)

        # 1.5. 最近邻无人机信息 (3维) - 新增的关键信息
        nearest_uav_obs = np.zeros(3)
        min_dist_to_neighbor = float('inf')
        nearest_neighbor_pos = None

        for other_idx in range(self.n_uavs):
            if other_idx == agent_idx:
                continue
            dist = np.linalg.norm(own_position - self.uav_positions[other_idx])
            if dist < min_dist_to_neighbor:
                min_dist_to_neighbor = dist
                nearest_neighbor_pos = self.uav_positions[other_idx]

        if nearest_neighbor_pos is not None:
            # 归一化距离
            normalized_dist = min_dist_to_neighbor / self.area_size
            # 归一化相对位置 (x, y)
            relative_pos = (nearest_neighbor_pos[:2] - own_position[:2]) / self.area_size
            nearest_uav_obs = np.array([normalized_dist, relative_pos[0], relative_pos[1]])
        
        obs_components.append(nearest_uav_obs)
        
        # 2. 自身状态信息 (4维) - 连接状态、路由状态、连接用户数、跳数
        self_state = np.zeros(4)
        
        # 连接用户数量（归一化）
        connected_users = np.sum(self.connections[agent_idx])
        self_state[0] = connected_users / self.max_connections
        
        # 是否有回程路径
        has_backhaul = 1.0 if agent_idx in self.routing_paths else 0.0
        self_state[1] = has_backhaul
        
        # 跳数（归一化）
        if agent_idx in self.routing_paths:
            path, _ = self.routing_paths[agent_idx]
            hops = len(path) - 1
            normalized_hops = hops / self.max_hops
        else:
            normalized_hops = 1.0  # 无路径时设为最大值
        self_state[2] = normalized_hops
        
        # 到最近基站的距离（归一化）
        min_bs_dist = float('inf')
        for bs_idx in range(self.n_ground_bs):
            bs_pos = self.ground_bs_positions[bs_idx]
            dist = np.linalg.norm(own_position - bs_pos)
            min_bs_dist = min(min_bs_dist, dist)
        self_state[3] = min_bs_dist / self.area_size if min_bs_dist != float('inf') else 1.0
        
        obs_components.append(self_state)
        
        # 3. 局部用户观测 (max_observed_users * 4维)
        local_users = self._get_local_users(agent_idx)
        user_obs = np.zeros(self.max_observed_users * 4)
        
        for i, (user_idx, sinr_db) in enumerate(local_users):
            if i >= self.max_observed_users:
                break
            
            user_pos = self.user_positions[user_idx]
            # 相对位置 (x, y) - 归一化，只取前两个维度
            relative_pos = (user_pos[:2] - own_position[:2]) / self.area_size
            # 归一化SINR到[0,1]范围 (假设SINR范围为-10dB到40dB)
            normalized_sinr = np.clip((sinr_db + 10) / 50, 0, 1)
            # 连接状态 - 该用户是否被当前UAV连接
            is_connected = 1.0 if self.connections[agent_idx, user_idx] else 0.0
            
            start_idx = i * 4
            user_obs[start_idx:start_idx+4] = [relative_pos[0], relative_pos[1], normalized_sinr, is_connected]
        
        obs_components.append(user_obs)
        
        # 3. 局部无人机观测 (max_observed_uavs * 4维)
        local_uavs = self._get_local_uavs(agent_idx)
        uav_obs = np.zeros(self.max_observed_uavs * 4)
        
        for i, (uav_idx, sinr_db) in enumerate(local_uavs):
            if i >= self.max_observed_uavs:
                break
            
            other_uav_pos = self.uav_positions[uav_idx]
            # 相对位置 (x, y, z) - 归一化
            relative_pos = other_uav_pos - own_position
            relative_pos[:2] = relative_pos[:2] / self.area_size
            relative_pos[2] = (relative_pos[2] - self.height_range[0]) / (self.height_range[1] - self.height_range[0])
            # 归一化SINR到[0,1]范围
            normalized_sinr = np.clip((sinr_db + 10) / 50, 0, 1)
            
            start_idx = i * 4
            uav_obs[start_idx:start_idx+4] = [relative_pos[0], relative_pos[1], relative_pos[2], normalized_sinr]
        
        obs_components.append(uav_obs)
        
        # 4. 局部基站观测 (max_observed_bs * 4维)
        local_bs = self._get_local_bs(agent_idx)
        bs_obs = np.zeros(self.max_observed_bs * 4)
        
        for i, (bs_idx, dist) in enumerate(local_bs):
            if i >= self.max_observed_bs:
                break
            
            bs_pos = self.ground_bs_positions[bs_idx]
            # 相对位置 (x, y, z) - 归一化
            relative_pos = bs_pos - own_position
            relative_pos[:2] /= self.area_size
            relative_pos[2] /= self.height_range[1] # 与全局状态归一化保持一致
            
            # 连接状态
            connection_status = 1.0 if self.uav_bs_connections[agent_idx, bs_idx] else 0.0
            
            start_idx = i * 4
            bs_obs[start_idx:start_idx+4] = [relative_pos[0], relative_pos[1], relative_pos[2], connection_status]
        
        obs_components.append(bs_obs)

        # 5. 当前步数 (1维)
        step_normalized = np.array([self.current_step / self.max_steps])
        obs_components.append(step_normalized)
        
        # 组合所有观测
        obs_dtype = self.observation_spaces[agent].spaces["obs"].dtype
        obs = np.asarray(np.concatenate(obs_components), dtype=obs_dtype)
        
        # 动作掩码（这里我们不限制动作，所以全为1）
        action_mask_dtype = self.observation_spaces[agent].spaces["action_mask"].dtype
        action_mask = np.ones((3,), dtype=action_mask_dtype)
        
        return {"obs": obs, "action_mask": action_mask}




    def get_scenario_info(self):
        """
        获取场景特定信息
        
        返回:
            info: 场景信息字典
        """
        info = {
            "scenario_name": "forced_relay",
            "scenario_description": "强制多跳中继无人机网络环境",
            "area_size": self.area_size,
            "n_ground_bs": self.n_ground_bs,
            "ground_bs_positions": self.ground_bs_positions.tolist() if hasattr(self, 'ground_bs_positions') else [],
            "n_clusters": self.n_clusters,
            "cluster_std": self.cluster_std,
            "central_area_ratio": self.central_area_ratio,
            "max_hops": self.max_hops,
            "min_distance_to_bs": self._compute_min_distance_to_bs(),
            "target_coverage_rate": 0.90,
        }
        
        return info
    
    def _compute_min_distance_to_bs(self):
        """
        计算用户到最近地面基站的最小距离
        
        返回:
            min_distance: 最小距离（米）
        """
        if not hasattr(self, 'user_positions') or self.user_positions is None:
            return 0
        
        min_distance = float('inf')
        
        for user_pos in self.user_positions:
            for bs_pos in self.ground_bs_positions:
                # 计算2D距离（用户在地面，基站也基本在地面）
                distance = np.sqrt((user_pos[0] - bs_pos[0])**2 + (user_pos[1] - bs_pos[1])**2)
                min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 0
    
    def _get_link_capacity(self, node1_type, node1_idx, node2_type, node2_idx):
        """
        计算两个节点之间的链路容量（修正版本，符合移动通信常识）
        
        参数:
            node1_type: 发送节点类型 ("uav" 或 "ground_bs")
            node1_idx: 发送节点索引
            node2_type: 接收节点类型 ("uav" 或 "ground_bs") 
            node2_idx: 接收节点索引
            
        返回:
            capacity: 链路容量 (bps)，如果无法建立连接则返回0
        """
        # 获取节点位置
        if node1_type == "uav":
            pos1 = self.uav_positions[node1_idx]
        elif node1_type == "ground_bs":
            pos1 = self.ground_bs_positions[node1_idx]
        else:
            return 0
            
        if node2_type == "uav":
            pos2 = self.uav_positions[node2_idx]
        elif node2_type == "ground_bs":
            pos2 = self.ground_bs_positions[node2_idx]
        else:
            return 0
        
        # 计算距离
        distance = self._compute_distance(pos1, pos2)
        safe_distance = max(distance, 1e-6)
        
        # 根据链路类型选择正确的路径损耗计算和发射功率
        if node1_type == "uav" and node2_type == "uav":
            # 空对空通信：UAV到UAV - 使用精确的A2A自由空间模型
            path_loss = self._compute_air_to_air_path_loss(pos1, pos2)
            tx_power = self.tx_power  # 使用UAV发射功率
        elif node1_type == "uav" and node2_type == "ground_bs":
            # 上行链路：UAV到地面基站 - 使用A2G模型
            path_loss = self._compute_air_to_ground_path_loss(pos1, pos2)
            tx_power = self.tx_power  # 使用UAV发射功率
        elif node1_type == "ground_bs" and node2_type == "uav":
            # 下行链路：地面基站到UAV - 使用G2A模型
            path_loss = self._compute_ground_to_air_path_loss(pos1, pos2)
            tx_power = self.ground_bs_tx_power  # 使用基站发射功率
        else:
            return 0  # 不支持的连接类型
        
        # 计算接收功率 (dBm)
        rx_power = tx_power - path_loss
        
        # 计算SINR (dB) - 考虑实际干扰情况
        sinr_db = self._compute_link_sinr(node1_type, node1_idx, node2_type, node2_idx, rx_power)
        
        # 检查SINR是否满足最小阈值
        if sinr_db < self.min_sinr:
            return 0
        
        # 确定用于计算容量的带宽
        if self.use_fdma:
            # FDMA模式下，假设总带宽被平均分配给每个UAV用于其回程链路
            link_bandwidth = self.bandwidth / self.n_uavs
        else:
            # 非FDMA模式（同频干扰）下，所有链路共享全部带宽，但受到同频干扰影响
            # 这里使用全部带宽，干扰影响已经在SINR计算中体现
            link_bandwidth = self.bandwidth
            
        # 转换为线性单位并计算容量
        sinr_linear = 10 ** (sinr_db / 10)
        capacity = link_bandwidth * np.log2(1 + sinr_linear)
        
        return capacity
    
    def _compute_link_sinr(self, tx_type, tx_idx, rx_type, rx_idx, rx_power):
        """
        计算链路SINR，使用确定性的干扰模型（移除随机性，增强干扰）
        
        改进原则：
        1. 空间隔离：基于信道条件计算动态干扰半径（已移除上限）
        2. 确定性干扰：移除随机性，使用固定权重模拟MAC层协议
        3. 精确路径损耗：为每条干扰链路计算正确的路径损耗
        
        参数:
            tx_type: 发送节点类型
            tx_idx: 发送节点索引
            rx_type: 接收节点类型
            rx_idx: 接收节点索引
            rx_power: 接收功率 (dBm)
            
        返回:
            sinr_db: SINR (dB)
        """
        # 原则1: 动态干扰半径 - 基于能够产生有意义干扰的最大距离（已移除上限）
        interference_radius = self._compute_interference_radius()
        
        # 原则2: 确定性干扰权重 - 模拟MAC层协议，提高干扰强度
        # 设置为1.0，表示所有干扰源都产生100%的干扰，更接近真实同频干扰场景
        uav_interference_weight = 1.0
        
        interference_powers_linear = []
        
        # 获取接收机位置，用于计算到干扰源的距离
        if rx_type == "uav":
            rx_pos = self.uav_positions[rx_idx]
        elif rx_type == "ground_bs":
            rx_pos = self.ground_bs_positions[rx_idx]
        else:
            rx_pos = None
        
        if rx_pos is not None:
            # 计算来自其他UAV的干扰
            for i in range(self.n_uavs):
                # 排除发送方自身
                if tx_type == "uav" and i == tx_idx:
                    continue
                
                interferer_pos = self.uav_positions[i]
                
                # 原则1：检查距离 - 考虑干扰半径内的所有无人机
                dist_to_receiver = self._compute_distance(interferer_pos, rx_pos)
                if dist_to_receiver > interference_radius:
                    continue  # 干扰源太远，忽略
                
                # 原则3：为干扰链路计算正确的路径损耗
                if rx_type == "uav":
                    interferer_path_loss = self._compute_air_to_air_path_loss(interferer_pos, rx_pos)
                elif rx_type == "ground_bs":
                    interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, rx_pos)
                else:
                    continue
                
                # 计算干扰功率
                interferer_rx_power_dbm = self.tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                
                # 应用确定性干扰权重
                weighted_interference_power = interferer_rx_power_linear * uav_interference_weight
                
                if self.use_fdma:
                    # FDMA模式：邻道干扰功率 = 加权干扰功率 * ACLR
                    interference_powers_linear.append(weighted_interference_power * self.aclr_linear)
                else:
                    # 非FDMA模式：同频干扰
                    interference_powers_linear.append(weighted_interference_power)
        
        # 计算总干扰加噪声功率
        total_interference_linear = np.sum(interference_powers_linear)
        noise_power_linear = 10 ** (self.noise_power / 10)  # dBm to mW
        interference_plus_noise_linear = noise_power_linear + total_interference_linear
        interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
        
        sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db

    def _get_grid_coords(self, pos):
        """Converts a 2D position to grid coordinates."""
        x, y = pos[0], pos[1]
        gx = int(np.clip(x / self.area_size * self.grid_resolution, 0, self.grid_resolution - 1))
        gy = int(np.clip(y / self.area_size * self.grid_resolution, 0, self.grid_resolution - 1))
        return gx, gy

    def _initialize_user_waypoints(self):
        """
        初始化用户路径点 - 基于增强的动态热点迁移模型
        
        特点：
        - 初始化簇中心的移动状态
        - 为用户设置基于增强簇标准差的路径点
        - 支持动态热点迁移模式
        """
        # 初始化簇中心的移动状态
        self._initialize_cluster_migration()
        
        for i in range(self.n_users):
            # 获取用户所属的簇
            user_cluster = self.user_cluster_assignments[i]
            
            if self.user_movement_model == "dynamic_hotspot_migration":
                # 使用增强的簇标准差生成路径点
                self._generate_enhanced_cluster_waypoint(i, user_cluster)
            else:
                # 回退到原有的RPGM模型
                if self.np_random.random() < 0.8:  # 80%概率在本簇内移动
                    self._generate_intra_cluster_waypoint(i, user_cluster)
                else:  # 20%概率跨簇移动
                    self._generate_inter_cluster_waypoint(i)
            
            # 设置初始速度
            direction = self.user_waypoints[i] - self.user_positions[i, :2]
            distance = np.linalg.norm(direction)
            if distance > 1e-6:
                speed = self.np_random.uniform(self.user_max_speed * 0.5, self.user_max_speed)
                self.user_velocities[i] = (direction / distance) * speed
            else:
                self.user_velocities[i] = np.zeros(2)
    
    def _initialize_cluster_migration(self):
        """
        初始化簇中心的迁移状态
        """
        # 为每个簇中心设置初始移动目标
        for cluster_idx in range(self.n_clusters):
            # 在当前簇中心周围选择一个迁移目标
            current_center = self.cluster_centers_history[cluster_idx]
            
            # 生成迁移目标（在较大范围内）
            migration_range = self.enhanced_cluster_std * 0.8  # 迁移范围
            angle = self.np_random.uniform(0, 2 * np.pi)
            radius = self.np_random.uniform(migration_range * 0.3, migration_range)
            
            target_x = current_center[0] + radius * np.cos(angle)
            target_y = current_center[1] + radius * np.sin(angle)
            
            # 确保目标在地图边界内
            target_x = np.clip(target_x, self.area_size * 0.05, self.area_size * 0.95)
            target_y = np.clip(target_y, self.area_size * 0.05, self.area_size * 0.95)
            
            self.cluster_waypoints[cluster_idx] = [target_x, target_y]
            
            # 设置簇中心的移动速度
            direction = self.cluster_waypoints[cluster_idx] - current_center
            distance = np.linalg.norm(direction)
            if distance > 1e-6:
                self.cluster_velocities[cluster_idx] = (direction / distance) * self.cluster_migration_speed
            else:
                self.cluster_velocities[cluster_idx] = np.zeros(2)
    
    def _generate_enhanced_cluster_waypoint(self, user_idx, cluster_idx):
        """
        基于增强簇标准差为用户生成路径点
        
        参数:
            user_idx: 用户索引
            cluster_idx: 簇索引
        """
        cluster_center = self.cluster_centers_history[cluster_idx]
        
        # 使用增强的簇标准差作为活动范围
        activity_radius = self.enhanced_cluster_std
        
        # 生成极坐标形式的随机偏移
        angle = self.np_random.uniform(0, 2 * np.pi)
        radius = self.np_random.uniform(0, activity_radius)
        
        waypoint = cluster_center + radius * np.array([np.cos(angle), np.sin(angle)])
        
        # 确保路径点在地图边界内
        waypoint[0] = np.clip(waypoint[0], 10, self.area_size - 10)
        waypoint[1] = np.clip(waypoint[1], 10, self.area_size - 10)
        
        self.user_waypoints[user_idx] = waypoint
    
    def _generate_intra_cluster_waypoint(self, user_idx, cluster_idx):
        """
        在指定簇内为用户生成路径点
        
        参数:
            user_idx: 用户索引
            cluster_idx: 簇索引
        """
        cluster_center = self.cluster_centers_history[cluster_idx]
        
        # 在簇中心周围生成路径点（使用簇标准差的1.5倍作为活动范围）
        activity_radius = self.cluster_std * 1.5
        
        # 生成极坐标形式的随机偏移
        angle = self.np_random.uniform(0, 2 * np.pi)
        radius = self.np_random.uniform(0, activity_radius)
        
        waypoint = cluster_center + radius * np.array([np.cos(angle), np.sin(angle)])
        
        # 确保路径点在地图边界内
        waypoint[0] = np.clip(waypoint[0], 10, self.area_size - 10)
        waypoint[1] = np.clip(waypoint[1], 10, self.area_size - 10)
        
        self.user_waypoints[user_idx] = waypoint
    
    def _generate_inter_cluster_waypoint(self, user_idx):
        """
        为用户生成跨簇路径点
        
        参数:
            user_idx: 用户索引
        """
        # 随机选择一个不同的簇作为目标
        current_cluster = self.user_cluster_assignments[user_idx]
        available_clusters = [i for i in range(self.n_clusters) if i != current_cluster]
        
        if available_clusters:
            target_cluster = self.np_random.choice(available_clusters)
            target_cluster_center = self.cluster_centers_history[target_cluster]
            
            # 在目标簇附近生成路径点
            activity_radius = self.cluster_std * 1.2
            angle = self.np_random.uniform(0, 2 * np.pi)
            radius = self.np_random.uniform(0, activity_radius)
            
            waypoint = target_cluster_center + radius * np.array([np.cos(angle), np.sin(angle)])
            
            # 确保路径点在地图边界内
            waypoint[0] = np.clip(waypoint[0], 10, self.area_size - 10)
            waypoint[1] = np.clip(waypoint[1], 10, self.area_size - 10)
            
            self.user_waypoints[user_idx] = waypoint
            
            # 更新用户的簇分配（模拟用户迁移到新的热点区域）
            self.user_cluster_assignments[user_idx] = target_cluster
        else:
            # 如果只有一个簇，则在本簇内生成路径点
            self._generate_intra_cluster_waypoint(user_idx, current_cluster)

    def _update_user_positions(self):
        """
        更新用户位置 - 标准参考点群体移动模型 (Standard RPGM)
        
        标准RPGM特点：
        - 簇中心按照设定速度移动
        - 用户围绕其所属簇的参考点移动
        - 支持标准的暂停时间
        - 移除非标准行为（逃离、跳跃等）
        """
        if not self.users_dynamic:
            return

        # 1. 更新簇中心位置（标准RPGM的参考点移动）
        self._update_cluster_centers_standard_rpgm()

        # 2. 更新用户位置 - 标准RPGM版本
        for i in range(self.n_users):
            # 检查用户暂停状态
            if self.user_pause_times[i] > 0:
                self.user_pause_times[i] -= self.time_step
                continue  # 暂停期间不移动
            
            # 标准RPGM移动：用户跟随其参考点移动
            self.user_positions[i, :2] += self.user_velocities[i] * self.time_step
            
            # 边界检查
            self.user_positions[i, 0] = np.clip(self.user_positions[i, 0], 0, self.area_size)
            self.user_positions[i, 1] = np.clip(self.user_positions[i, 1], 0, self.area_size)

            # 检查是否到达路径点
            dist_to_waypoint = np.linalg.norm(self.user_positions[i, :2] - self.user_waypoints[i])
            if dist_to_waypoint < self.user_max_speed * self.time_step:  # 如果足够接近
                # 获取用户当前所属的簇
                user_cluster = self.user_cluster_assignments[i]
                
                # 高速RPGM：增加跨簇移动概率以模拟更大范围的快速移动
                if self.np_random.random() < 0.6:  # 60%概率在本簇内移动
                    self._generate_intra_cluster_waypoint(i, user_cluster)
                else:  # 40%概率跨簇移动 - 适合高速场景
                    self._generate_inter_cluster_waypoint(i)
                
                # 设置新的速度
                direction = self.user_waypoints[i] - self.user_positions[i, :2]
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    speed = self.np_random.uniform(self.user_max_speed * 0.5, self.user_max_speed)
                    self.user_velocities[i] = (direction / distance) * speed
                else:
                    self.user_velocities[i] = np.zeros(2)
                
                # 高速场景下减少暂停概率
                if self.np_random.random() < 0.1:  # 10%概率暂停 - 高速移动很少暂停
                    pause_time = self.np_random.uniform(*self.user_pause_time_range)
                    self.user_pause_times[i] = pause_time

    def _update_cluster_centers_standard_rpgm(self):
        """
        更新簇中心位置 - 标准RPGM参考点移动模型
        
        标准RPGM特点：
        - 簇中心（参考点）按照设定的速度移动
        - 到达目标点后选择新的迁移目标并可能暂停
        - 移动模式更加规律和可预测
        """
        for cluster_idx in range(self.n_clusters):
            # 检查簇中心是否在暂停状态
            if not hasattr(self, 'cluster_pause_times'):
                self.cluster_pause_times = np.zeros(self.n_clusters)
            
            if self.cluster_pause_times[cluster_idx] > 0:
                self.cluster_pause_times[cluster_idx] -= self.time_step
                continue  # 暂停期间不移动
            
            # 移动簇中心
            self.cluster_centers_history[cluster_idx] += self.cluster_velocities[cluster_idx] * self.time_step
            
            # 边界检查
            self.cluster_centers_history[cluster_idx, 0] = np.clip(
                self.cluster_centers_history[cluster_idx, 0], 
                self.area_size * 0.05, 
                self.area_size * 0.95
            )
            self.cluster_centers_history[cluster_idx, 1] = np.clip(
                self.cluster_centers_history[cluster_idx, 1], 
                self.area_size * 0.05, 
                self.area_size * 0.95
            )
            
            # 检查是否到达目标点
            dist_to_target = np.linalg.norm(
                self.cluster_centers_history[cluster_idx] - self.cluster_waypoints[cluster_idx]
            )
            
            if dist_to_target < self.cluster_migration_speed * self.time_step:  # 如果足够接近目标
                # 选择新的迁移目标
                self._generate_new_cluster_target_standard_rpgm(cluster_idx)
                
                # 更新簇中心的移动速度
                direction = self.cluster_waypoints[cluster_idx] - self.cluster_centers_history[cluster_idx]
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    self.cluster_velocities[cluster_idx] = (direction / distance) * self.cluster_migration_speed
                else:
                    self.cluster_velocities[cluster_idx] = np.zeros(2)
                
                # 高速场景下减少簇中心暂停概率
                if self.np_random.random() < 0.2:  # 20%概率暂停 - 高速场景下簇中心也很少暂停
                    pause_time = self.np_random.uniform(*self.cluster_pause_time_range)
                    self.cluster_pause_times[cluster_idx] = pause_time

    def _generate_new_cluster_target_standard_rpgm(self, cluster_idx):
        """
        为簇中心生成新的迁移目标 - 标准RPGM版本
        
        标准RPGM特点：
        - 移动范围更加保守，避免过度分散
        - 移动模式更加规律和可预测
        
        参数:
            cluster_idx: 簇索引
        """
        current_center = self.cluster_centers_history[cluster_idx]
        
        # 标准RPGM使用更保守的迁移范围
        migration_range = self.cluster_std * 2.0  # 使用标准簇标准差的2倍作为迁移范围
        
        # 使用极坐标生成目标
        angle = self.np_random.uniform(0, 2 * np.pi)
        radius = self.np_random.uniform(migration_range * 0.3, migration_range)
        
        target_x = current_center[0] + radius * np.cos(angle)
        target_y = current_center[1] + radius * np.sin(angle)
        
        # 确保目标在地图边界内，并避免过于接近边界
        target_x = np.clip(target_x, self.area_size * 0.1, self.area_size * 0.9)
        target_y = np.clip(target_y, self.area_size * 0.1, self.area_size * 0.9)
        
        self.cluster_waypoints[cluster_idx] = [target_x, target_y]

    def _execute_long_distance_jump(self, user_idx):
        """
        执行用户长距离跳跃行为（模拟车辆快速移动或公共交通）
        
        参数:
            user_idx: 用户索引
        """
        # 随机选择一个远距离目标位置
        jump_distance = self.np_random.uniform(self.max_jump_distance * 0.5, self.max_jump_distance)
        angle = self.np_random.uniform(0, 2 * np.pi)
        
        current_pos = self.user_positions[user_idx, :2]
        new_x = current_pos[0] + jump_distance * np.cos(angle)
        new_y = current_pos[1] + jump_distance * np.sin(angle)
        
        # 确保新位置在地图边界内
        new_x = np.clip(new_x, 10, self.area_size - 10)
        new_y = np.clip(new_y, 10, self.area_size - 10)
        
        # 立即移动到新位置
        self.user_positions[user_idx, :2] = [new_x, new_y]
        
        # 设置短暂的暂停时间（模拟到达后的停留）
        self.user_pause_times[user_idx] = self.np_random.uniform(5, 15)  # 5-15秒暂停
        
        # 更新移动阶段
        self.user_movement_phases[user_idx] = 2  # 跳跃阶段
        
        # 重新分配到最近的簇
        self._reassign_user_to_nearest_cluster(user_idx)
        
        # 生成新的路径点
        new_cluster = self.user_cluster_assignments[user_idx]
        self._generate_enhanced_cluster_waypoint(user_idx, new_cluster)

    def _execute_user_escape(self, user_idx):
        """
        执行用户逃离行为（主动逃离当前UAV覆盖）
        
        参数:
            user_idx: 用户索引
        """
        current_pos = self.user_positions[user_idx, :2]
        
        # 找到覆盖该用户的所有UAV
        covering_uavs = []
        for uav_idx in range(self.n_uavs):
            if hasattr(self, 'sinr_matrix') and self.sinr_matrix[uav_idx, user_idx] >= self.min_sinr:
                covering_uavs.append(uav_idx)
        
        if covering_uavs:
            # 计算所有覆盖UAV的平均位置
            uav_positions = self.uav_positions[covering_uavs, :2]
            avg_uav_pos = np.mean(uav_positions, axis=0)
            
            # 计算逃离方向（远离UAV的方向）
            escape_direction = current_pos - avg_uav_pos
            escape_distance = np.linalg.norm(escape_direction)
            
            if escape_distance > 1e-6:
                # 归一化逃离方向
                escape_direction = escape_direction / escape_distance
                
                # 设置逃离距离（至少逃离UAV覆盖范围）
                min_escape_distance = self.observation_radius * 1.2
                max_escape_distance = self.observation_radius * 2.0
                escape_distance = self.np_random.uniform(min_escape_distance, max_escape_distance)
                
                # 计算逃离目标位置
                escape_target = current_pos + escape_direction * escape_distance
                
                # 确保目标位置在地图边界内
                escape_target[0] = np.clip(escape_target[0], 10, self.area_size - 10)
                escape_target[1] = np.clip(escape_target[1], 10, self.area_size - 10)
                
                # 设置逃离路径点
                self.user_waypoints[user_idx] = escape_target
                
                # 设置高速逃离
                direction = escape_target - current_pos
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    escape_speed = self.user_max_speed * 1.2  # 逃离时速度提升20%
                    self.user_velocities[user_idx] = (direction / distance) * escape_speed
                
                # 更新移动阶段
                self.user_movement_phases[user_idx] = 1  # 逃离阶段
        else:
            # 如果没有被覆盖，执行随机移动
            self._generate_random_waypoint(user_idx)

    def _reassign_user_to_nearest_cluster(self, user_idx):
        """
        将用户重新分配到最近的簇
        
        参数:
            user_idx: 用户索引
        """
        user_pos = self.user_positions[user_idx, :2]
        min_distance = float('inf')
        nearest_cluster = 0
        
        for cluster_idx in range(self.n_clusters):
            cluster_center = self.cluster_centers_history[cluster_idx]
            distance = np.linalg.norm(user_pos - cluster_center)
            if distance < min_distance:
                min_distance = distance
                nearest_cluster = cluster_idx
        
        self.user_cluster_assignments[user_idx] = nearest_cluster

    def _generate_random_waypoint(self, user_idx):
        """
        为用户生成完全随机的路径点
        
        参数:
            user_idx: 用户索引
        """
        # 在整个地图范围内随机生成路径点
        waypoint = self.np_random.uniform([10, 10], [self.area_size - 10, self.area_size - 10])
        self.user_waypoints[user_idx] = waypoint
        
        # 设置随机速度
        direction = waypoint - self.user_positions[user_idx, :2]
        distance = np.linalg.norm(direction)
        if distance > 1e-6:
            speed = self.np_random.uniform(self.user_max_speed * 0.3, self.user_max_speed)
            self.user_velocities[user_idx] = (direction / distance) * speed
        else:
            self.user_velocities[user_idx] = np.zeros(2)
    
    def _update_cluster_centers(self):
        """
        更新簇中心位置 - 实现动态热点迁移
        
        特点：
        - 簇中心按照设定的速度向目标点移动
        - 到达目标点后选择新的迁移目标
        - 确保簇中心移动不会导致用户分布过于分散
        """
        for cluster_idx in range(self.n_clusters):
            # 移动簇中心
            self.cluster_centers_history[cluster_idx] += self.cluster_velocities[cluster_idx] * self.time_step
            
            # 边界检查
            self.cluster_centers_history[cluster_idx, 0] = np.clip(
                self.cluster_centers_history[cluster_idx, 0], 
                self.area_size * 0.05, 
                self.area_size * 0.95
            )
            self.cluster_centers_history[cluster_idx, 1] = np.clip(
                self.cluster_centers_history[cluster_idx, 1], 
                self.area_size * 0.05, 
                self.area_size * 0.95
            )
            
            # 检查是否到达目标点
            dist_to_target = np.linalg.norm(
                self.cluster_centers_history[cluster_idx] - self.cluster_waypoints[cluster_idx]
            )
            
            if dist_to_target < self.cluster_migration_speed * 2:  # 如果足够接近目标
                # 选择新的迁移目标
                self._generate_new_cluster_target(cluster_idx)
                
                # 更新簇中心的移动速度
                direction = self.cluster_waypoints[cluster_idx] - self.cluster_centers_history[cluster_idx]
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    self.cluster_velocities[cluster_idx] = (direction / distance) * self.cluster_migration_speed
                else:
                    self.cluster_velocities[cluster_idx] = np.zeros(2)
    
    def _generate_new_cluster_target(self, cluster_idx):
        """
        为簇中心生成新的迁移目标
        
        参数:
            cluster_idx: 簇索引
        """
        current_center = self.cluster_centers_history[cluster_idx]
        
        # 生成新的迁移目标（在更大范围内，但避免过度分散）
        migration_range = self.enhanced_cluster_std * 0.6  # 适中的迁移范围
        
        # 使用极坐标生成目标
        angle = self.np_random.uniform(0, 2 * np.pi)
        radius = self.np_random.uniform(migration_range * 0.4, migration_range)
        
        target_x = current_center[0] + radius * np.cos(angle)
        target_y = current_center[1] + radius * np.sin(angle)
        
        # 确保目标在地图边界内，并避免过于接近边界
        target_x = np.clip(target_x, self.area_size * 0.1, self.area_size * 0.9)
        target_y = np.clip(target_y, self.area_size * 0.1, self.area_size * 0.9)
        
        self.cluster_waypoints[cluster_idx] = [target_x, target_y]

    def _predict_belief_map(self):
        """
        Predicts the next state of the belief map based on a diffusion model.
        This simulates the movement of users.
        """
        if not self.users_dynamic:
            return
            
        # 1. Decay: Belief naturally decreases over time
        self.belief_map *= self.belief_decay

        # 2. Diffusion: Belief spreads to neighbors
        # Using a simple 3x3 averaging kernel for diffusion
        kernel = np.ones((3, 3)) * self.belief_diffusion_factor / 9.0
        center_val = 1 - self.belief_diffusion_factor
        kernel[1, 1] = center_val
        
        # Apply convolution. Using 'scipy.signal.convolve2d' would be better,
        # but to avoid new dependencies, we'll use a simple manual loop.
        # For simplicity and performance, we'll use a more direct neighbor sum approach.
        diffused_map = self.belief_map.copy()
        padded_map = np.pad(self.belief_map, 1, mode='edge')
        
        for r in range(self.grid_resolution):
            for c in range(self.grid_resolution):
                # Sum of 8 neighbors
                neighbor_sum = np.sum(padded_map[r:r+3, c:c+3]) - padded_map[r+1, c+1]
                # Current cell loses belief to neighbors
                loss = self.belief_map[r, c] * self.belief_diffusion_factor
                # Current cell gains belief from neighbors
                gain = neighbor_sum / 8.0 * self.belief_diffusion_factor
                diffused_map[r, c] = self.belief_map[r, c] - loss + gain
        
        self.belief_map = np.clip(diffused_map, 1e-9, 1.0)

        # 3. Normalize: Ensure the map remains a probability distribution
        total_belief = np.sum(self.belief_map)
        if total_belief > 1e-9:
            self.belief_map /= total_belief

    def _update_belief_map_from_observation(self):
        """
        Updates the belief map based on UAV observations.
        """
        if not self.users_dynamic:
            return

        # Create a map of observed cells
        observed_cells = np.zeros_like(self.belief_map, dtype=bool)
        user_found_in_cell = np.zeros_like(self.belief_map, dtype=bool)

        # Mark cells with found users
        for user_idx in range(self.n_users):
            # Check if this user is covered by any UAV
            is_covered = False
            for uav_idx in range(self.n_uavs):
                if self.sinr_matrix[uav_idx, user_idx] >= self.min_sinr:
                    is_covered = True
                    break
            
            if is_covered:
                gx, gy = self._get_grid_coords(self.user_positions[user_idx])
                user_found_in_cell[gy, gx] = True

        # Mark all observed cells (within UAVs' observation radius)
        cell_size = self.area_size / self.grid_resolution
        obs_radius_in_cells = int(self.observation_radius / cell_size)
        
        for uav_idx in range(self.n_uavs):
            uav_gx, uav_gy = self._get_grid_coords(self.uav_positions[uav_idx])
            
            # A simple square approximation for the observation circle
            min_x = max(0, uav_gx - obs_radius_in_cells)
            max_x = min(self.grid_resolution, uav_gx + obs_radius_in_cells + 1)
            min_y = max(0, uav_gy - obs_radius_in_cells)
            max_y = min(self.grid_resolution, uav_gy + obs_radius_in_cells + 1)
            
            observed_cells[min_y:max_y, min_x:max_x] = True

        # Apply Bayesian-like updates
        # P(user|obs) = P(obs|user) * P(user) / P(obs)
        
        # Increase belief where users were found
        # P(user_found | user_present) is high, let's say 0.9
        # P(user_found | user_absent) is low, let's say 0.1
        p_obs_given_user = 0.9
        p_obs_given_no_user = 0.1
        
        # Cells where a user was found
        positive_obs_mask = user_found_in_cell
        prior_belief = self.belief_map[positive_obs_mask]
        # Bayes update: P(user|+) = (P(+|user)P(user)) / (P(+|user)P(user) + P(+|no_user)P(no_user))
        numerator = p_obs_given_user * prior_belief
        denominator = numerator + p_obs_given_no_user * (1 - prior_belief)
        posterior_belief_pos = numerator / (denominator + 1e-9)
        self.belief_map[positive_obs_mask] = (1 - self.belief_update_strength) * prior_belief + self.belief_update_strength * posterior_belief_pos

        # Cells observed but no user was found
        negative_obs_mask = observed_cells & ~user_found_in_cell
        prior_belief = self.belief_map[negative_obs_mask]
        # Bayes update: P(user|-) = (P(-|user)P(user)) / (P(-|user)P(user) + P(-|no_user)P(no_user))
        # P(-|user) = 1 - P(+|user) = 0.1
        # P(-|no_user) = 1 - P(+|no_user) = 0.9
        numerator = (1 - p_obs_given_user) * prior_belief
        denominator = numerator + (1 - p_obs_given_no_user) * (1 - prior_belief)
        posterior_belief_neg = numerator / (denominator + 1e-9)
        self.belief_map[negative_obs_mask] = (1 - self.belief_update_strength) * prior_belief + self.belief_update_strength * posterior_belief_neg

        # Normalize again
        total_belief = np.sum(self.belief_map)
        if total_belief > 1e-9:
            self.belief_map /= total_belief
    
    def _compute_routing_paths(self):
        """
        修复后的路由路径计算方法 (V2)
        
        改进策略：
        1. 将所有UAV和基站视为一个图中的节点。
        2. 为每一个UAV，独立地计算其到任何一个地面基站的最宽路径。
        3. 这样可以自然地形成中继链路，因为一个UAV到基站的路径可能会经过另一个UAV。
        """
        self.routing_paths = {}
        
        # 为每一个UAV都尝试寻找一条到基站的最宽路径
        for uav_idx in range(self.n_uavs):
            # 使用最宽路径算法寻找多跳路径
            # 这个算法会考虑通过其他UAV进行中继
            path, capacity = self._find_widest_path_to_ground_bs(uav_idx)
            
            # 如果找到了有效的路径，并且满足最大跳数限制
            if path and capacity > 0 and len(path) - 1 <= self.max_hops:
                self.routing_paths[uav_idx] = (path, capacity)
    def _get_state(self):
        """
        获取针对强制中继场景优化的全局状态
        
        包含以下信息：
        1. 无人机位置 (n_uavs * 3)
        2. 用户位置 (n_users * 3) - 包含高度，保持一致性
        3. 地面基站位置 (n_ground_bs * 3) - 关键信息
        4. 用户覆盖状态 (n_users) - 每个用户是否被覆盖
        5. 无人机连接状态 (n_uavs) - 每个无人机是否有到基站的路径
        6. 系统通信质量指标 (4) - 平均SINR、连接质量、平均跳数、系统吞吐量
        7. 当前步数 (1)
        
        返回:
            state: 完整的全局状态向量
        """
        state_components = []
        
        # 1. 无人机位置 (归一化到[0,1])
        normalized_uav_positions = self.uav_positions.copy()
        normalized_uav_positions[:, :2] /= self.area_size  # x, y 归一化
        normalized_uav_positions[:, 2] = (normalized_uav_positions[:, 2] - self.height_range[0]) / (self.height_range[1] - self.height_range[0])  # z 归一化
        state_components.append(normalized_uav_positions.flatten())
        
        # 2. 用户位置 (归一化到[0,1]) - 现在包含高度
        normalized_user_positions = self.user_positions.copy()
        normalized_user_positions[:, :2] /= self.area_size  # x, y 归一化
        normalized_user_positions[:, 2] /= 10  # z 归一化 (用户高度固定为1.5m，用10m作为归一化基准)
        state_components.append(normalized_user_positions.flatten())
        
        # 3. 地面基站位置 (归一化到[0,1]) - 强制中继场景的关键信息
        normalized_bs_positions = self.ground_bs_positions.copy()
        normalized_bs_positions[:, :2] /= self.area_size  # x, y 归一化
        normalized_bs_positions[:, 2] /= 200  # z 归一化 (假设最大高度200m)
        state_components.append(normalized_bs_positions.flatten())
        
        # 4. 用户覆盖状态 (0或1)
        user_covered = np.zeros(self.n_users)
        for j in range(self.n_users):
            if np.any(self.connections[:, j]):  # 如果有任何无人机连接了该用户
                user_covered[j] = 1.0
        state_components.append(user_covered)
        
        # 5. 无人机连接状态 (0或1) - 每个无人机是否有到基站的回程路径
        uav_connected = np.zeros(self.n_uavs)
        if hasattr(self, 'routing_paths'):
            for i in range(self.n_uavs):
                if i in self.routing_paths and self.routing_paths[i][0]:
                    uav_connected[i] = 1.0
        state_components.append(uav_connected)
        
        # 6. 系统通信质量指标 (4维)
        comm_quality = np.zeros(4)
        
        # 6.1 平均SINR (归一化到[0,1]，假设SINR范围为-10dB到40dB)
        if hasattr(self, 'sinr_matrix'):
            valid_sinr_values = self.sinr_matrix[self.sinr_matrix >= self.min_sinr]
            if len(valid_sinr_values) > 0:
                avg_sinr = np.mean(valid_sinr_values)
                comm_quality[0] = np.clip((avg_sinr + 10) / 50, 0, 1)  # 归一化到[0,1]
            else:
                comm_quality[0] = 0
        else:
            comm_quality[0] = 0
        
        # 6.2 连接质量（有回程路径的UAV比例）
        if hasattr(self, 'routing_paths'):
            comm_quality[1] = len(self.routing_paths) / self.n_uavs if self.n_uavs > 0 else 0
        else:
            comm_quality[1] = 0
        
        # 6.3 平均跳数 (归一化)
        if hasattr(self, 'routing_paths') and len(self.routing_paths) > 0:
            hop_counts = [len(path) - 1 for path, _ in self.routing_paths.values() if path]
            if hop_counts:
                avg_hops = np.mean(hop_counts)
                comm_quality[2] = np.clip(avg_hops / self.max_hops, 0, 1)
            else:
                comm_quality[2] = 1.0
        else:
            comm_quality[2] = 1.0
        
        # 6.4 系统吞吐量 (归一化，假设最大1Gbps)
        if hasattr(self, 'reward_info') and self.reward_info:
            throughput_mbps = self.reward_info.get('system_throughput_mbps', 0)
            comm_quality[3] = np.clip(throughput_mbps / 1000, 0, 1)  # 归一化到[0,1]
        else:
            comm_quality[3] = 0
        
        state_components.append(comm_quality)
        
        # 7. 当前步数 (归一化到[0,1])
        step_normalized = np.array([self.current_step / self.max_steps])
        state_components.append(step_normalized)
        
        # 8. 动态密度预测图 (如果启用) - 核心创新
        if self.density_prediction and hasattr(self, 'predicted_density_map') and self.predicted_density_map is not None:
            # 将预测密度图展平并归一化
            # 使用最大密度值进行归一化，确保数值稳定性
            max_density = np.max(self.predicted_density_map)
            if max_density > 1e-9:
                normalized_predicted_density = self.predicted_density_map.flatten() / max_density
            else:
                normalized_predicted_density = self.predicted_density_map.flatten()
            
            state_components.append(normalized_predicted_density)
        
        # 组合所有状态组件
        state = np.concatenate(state_components)
        
        return state
    
    def _find_widest_path_to_ground_bs(self, start_uav):
        """
        使用改进的Dijkstra算法寻找从UAV到地面基站的最宽路径。
        
        参数:
            start_uav: 起始UAV索引
            
        返回:
            (best_path, best_capacity): 一个元组，包含最优路径列表和该路径的瓶颈容量。
                                        如果没有路径，则返回 (None, 0)。
        """
        max_bottleneck = {}
        parent = {}
        pq = []  # 优先队列: (-瓶颈容量, 节点标识符)

        start_node = ("uav", start_uav)
        max_bottleneck[start_node] = float('inf')
        parent[start_node] = None
        heapq.heappush(pq, (-float('inf'), start_node))

        best_target_path = None
        best_target_capacity = 0

        while pq:
            neg_capacity, current_node = heapq.heappop(pq)
            current_capacity = -neg_capacity

            if current_capacity < max_bottleneck.get(current_node, 0):
                continue

            current_type, current_idx = current_node

            # 探索邻居节点
            neighbors = []
            if current_type == "uav":
                # 添加其他UAV和地面基站作为邻居
                for next_uav in range(self.n_uavs):
                    if next_uav != current_idx:
                        neighbors.append(("uav", next_uav))
                for bs_idx in range(self.n_ground_bs):
                    neighbors.append(("ground_bs", bs_idx))

            for neighbor in neighbors:
                neighbor_type, neighbor_idx = neighbor
                
                # 计算链路容量
                link_capacity = self._get_link_capacity(current_type, current_idx, neighbor_type, neighbor_idx)
                if link_capacity <= 0:
                    continue

                path_bottleneck = min(current_capacity, link_capacity)

                if path_bottleneck > max_bottleneck.get(neighbor, 0):
                    max_bottleneck[neighbor] = path_bottleneck
                    parent[neighbor] = current_node
                    heapq.heappush(pq, (-path_bottleneck, neighbor))

                    # 如果邻居是基站，更新找到的最佳路径
                    if neighbor_type == "ground_bs":
                        if path_bottleneck > best_target_capacity:
                            best_target_capacity = path_bottleneck
                            # 重构路径
                            path = []
                            curr = neighbor
                            while curr is not None:
                                path.append(curr)
                                curr = parent.get(curr)
                            path.reverse()
                            best_target_path = path
        
        if best_target_path:
            return best_target_path, best_target_capacity
        else:
            return None, 0
    
    def _compute_uav_frontend_capacity(self, uav_idx, connected_users):
        """
        重写父类方法：计算UAV的前端总容量（使用精确的信道模型）
        
        参数:
            uav_idx: 无人机索引
            connected_users: 连接到该UAV的用户索引列表
            
        返回:
            frontend_capacity: 前端总容量 (bps)
        """
        if len(connected_users) == 0:
            return 0
        
        # 使用我们自定义的精确SINR计算，而不是依赖父类的sinr_matrix
        user_capacities = []
        
        for user_idx in connected_users:
            # 计算UAV到用户的精确SINR
            uav_pos = self.uav_positions[uav_idx]
            user_pos_3d = self.user_positions[user_idx]  # 现在用户位置已经是三维的
            
            # 计算路径损耗（使用我们的精确A2G模型）
            path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
            
            # 计算接收功率 (dBm)
            rx_power = self.tx_power - path_loss
            
            # 计算精确的SINR（考虑所有干扰源）
            sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
            
            # 检查SINR是否满足最小阈值
            if sinr_db >= self.min_sinr:
                # 转换为线性单位并计算单用户容量
                sinr_linear = 10 ** (sinr_db / 10)
                user_capacity = self.bandwidth * np.log2(1 + sinr_linear)
                user_capacities.append(user_capacity)
            else:
                # SINR不满足阈值，该用户无法获得服务
                user_capacities.append(0)
        
        # 在FDMA模式下，每个用户分配独立的频率资源
        if self.use_fdma:
            # FDMA模式下，假设每个UAV将其均分到的带宽(self.bandwidth / self.n_uavs)
            # 再次平均分配给其连接的所有用户。
            if len(connected_users) > 0:
                # 首先计算该UAV可用于接入的总带宽
                access_bandwidth_for_uav = self.bandwidth / self.n_uavs
                # 然后将此带宽均分给其连接的用户
                bandwidth_per_user = access_bandwidth_for_uav / len(connected_users)
                
                # 重新计算基于分配带宽的容量
                adjusted_capacities = []
                for i, user_idx in enumerate(connected_users):
                    if user_capacities[i] > 0:
                        # 使用分配的带宽重新计算容量
                        uav_pos = self.uav_positions[uav_idx]
                        user_pos_3d = self.user_positions[user_idx]  # 现在用户位置已经是三维的
                        path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
                        rx_power = self.tx_power - path_loss
                        sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
                        sinr_linear = 10 ** (sinr_db / 10)
                        adjusted_capacity = bandwidth_per_user * np.log2(1 + sinr_linear)
                        adjusted_capacities.append(adjusted_capacity)
                    else:
                        adjusted_capacities.append(0)
                
                frontend_capacity = sum(adjusted_capacities)
            else:
                frontend_capacity = 0
        else:
            # 非FDMA模式 (TDMA): 用户共享时间资源，总容量是所有用户容量之和
            if user_capacities:
                # 找出有效连接用户的容量
                valid_capacities = [cap for cap in user_capacities if cap > 0]
                if valid_capacities:
                    # 共享信道的总容量等于所有服务用户的容量之和
                    frontend_capacity = sum(valid_capacities)
                else:
                    frontend_capacity = 0
            else:
                frontend_capacity = 0
        
        return frontend_capacity
    
    def _compute_uav_to_user_sinr(self, uav_idx, user_idx, rx_power):
        """
        计算UAV到用户通信的精确SINR，使用确定性的干扰模型（移除随机性，增强干扰）
        
        改进原则：
        1. 空间隔离：基于信道条件计算动态干扰半径（已移除上限）
        2. 确定性干扰：移除随机性，使用固定权重模拟MAC层协议
        3. 精确路径损耗：为每条干扰链路计算正确的A2G路径损耗
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            rx_power: 接收功率 (dBm)
            
        返回:
            sinr_db: SINR (dB)
        """
        # 原则1: 动态干扰半径 - 基于能够产生有意义干扰的最大距离（已移除上限）
        interference_radius = self._compute_interference_radius()
        
        # 原则2: 确定性干扰权重 - 模拟MAC层协议，提高干扰强度
        # 设置为1.0，表示所有干扰源都产生100%的干扰，更接近真实同频干扰场景
        uav_interference_weight = 1.0
        
        interference_powers_linear = []
        user_pos_3d = self.user_positions[user_idx]  # 用户位置已经是三维的
        
        # 计算来自其他UAV的干扰
        for i in range(self.n_uavs):
            if i != uav_idx:  # 排除目标UAV自身
                interferer_pos = self.uav_positions[i]
                
                # 原则1：检查距离 - 考虑干扰半径内的所有无人机
                dist_to_user = self._compute_distance(interferer_pos, user_pos_3d)
                if dist_to_user > interference_radius:
                    continue  # 干扰源太远，忽略
                
                # 原则3：使用精确的A2G路径损耗模型计算干扰
                interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, user_pos_3d)
                interferer_rx_power_dbm = self.tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                
                # 应用确定性干扰权重
                weighted_interference_power = interferer_rx_power_linear * uav_interference_weight
                
                if self.use_fdma:
                    # FDMA模式：邻道干扰功率 = 加权干扰功率 * ACLR
                    interference_powers_linear.append(weighted_interference_power * self.aclr_linear)
                else:
                    # 非FDMA模式：同频干扰
                    interference_powers_linear.append(weighted_interference_power)
        
        # 计算总干扰加噪声功率
        total_interference_linear = np.sum(interference_powers_linear)
        noise_power_linear = 10 ** (self.noise_power / 10)  # dBm to mW
        interference_plus_noise_linear = noise_power_linear + total_interference_linear
        interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
        
        sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db
