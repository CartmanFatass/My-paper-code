import numpy as np
import heapq
from pettingzoo import ParallelEnv
from gymnasium.spaces import Box, Dict
from scipy.spatial.distance import cdist

class UAVForcedRelayEnv(ParallelEnv):
    """
    场景4：强制多跳中继无人机环境
    
    特点：
    - 专为强制协作设计的拓扑结构
    - 地面基站距离用户群体很远，强制要求多跳中继
    - 优化的用户分布，便于实现90%以上覆盖率
    - 重点激励用户覆盖率，简化奖励机制
    - 所有无人机地位平等，通过算法自主选择行为
    """
    
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_forced_relay_env_v0",
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
        max_steps=5000,
        user_distribution="forced_relay_cluster",
        channel_model="probabilistic",
        render_mode=None,
        seed=None,
        min_sinr=3,
        max_connections=25,
        max_hops=4,
        coverage_weight=0.8,
        link_quality_weight=0.2,  # 统一的链路质量权重，替代原来的connectivity_weight和efficiency_weight
        n_ground_bs=1,
        n_clusters=4,
        cluster_std=80,
        central_area_ratio=0.6,
        base_station_distance_factor=0.8,
        uav_communication_range=600,
        max_observed_uavs=15,
        max_observed_users=25,
        use_shadowing=False,
        paper_reward=False,
        use_fdma=True,
        bandwidth=20e6,
        ground_bs_tx_power=30,
        uav_init_mode="start_area",
        uav_start_area_size=500,
        grid_resolution=100,
        # Belief-based potential function parameters
        gamma=0.99,  # Discount factor for RL
        potential_reward_weight=0.2,
        belief_decay_factor=0.1,
        recon_interval=100,  # Steps between reconnaissance updates
        recon_strength=0.1,  # How much belief is added by recon
        # Distance overlap penalty parameters
        distance_overlap_penalty_weight=0.05,
        # Randomization control parameters
        randomize_bs=True,  # 是否随机化基站位置
        randomize_users=True,  # 是否随机化用户簇中心
        randomize_uav_start=True,  # 是否随机化无人机起始区域
        aclr_db=45,  # 邻道泄漏比 (Adjacent Channel Leakage Ratio) in dB
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
        self.channel_model = channel_model
        self.render_mode = render_mode
        self.seed_val = seed
        self.np_random = np.random.RandomState(seed)

        # 探索奖励参数
        self.grid_resolution = grid_resolution
        
        # Belief Map and Grid setup
        self.grid_size = int(np.ceil(self.area_size / self.grid_resolution))
        self.belief_map = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)
        
        # Store grid cell center coordinates for efficient distance calculation
        y, x = np.indices((self.grid_size, self.grid_size))
        self.cell_centers = np.stack([
            (x + 0.5) * self.grid_resolution, 
            (y + 0.5) * self.grid_resolution
        ], axis=-1).reshape(-1, 2)

        # For storing the potential value between steps
        self.current_potential = 0.0
        
        # Belief-based potential function parameters
        self.gamma = gamma
        self.potential_reward_weight = potential_reward_weight
        self.belief_decay_factor = belief_decay_factor
        self.recon_interval = recon_interval
        self.recon_strength = recon_strength

        # Track user service status to provide sparse rewards correctly
        self.user_serviced_status = np.zeros(self.n_users, dtype=bool)
        
        # 场景特定参数
        self.n_clusters = n_clusters
        self.cluster_std = cluster_std
        self.central_area_ratio = central_area_ratio
        self.base_station_distance_factor = base_station_distance_factor
        self.uav_communication_range = uav_communication_range
        self.uav_init_mode = uav_init_mode
        self.uav_start_area_size = uav_start_area_size
        self.coverage_weight = coverage_weight
        self.link_quality_weight = link_quality_weight  # 存储独立的链路质量权重
        self.n_ground_bs = n_ground_bs
        self.max_hops = max_hops
        self.min_sinr = min_sinr
        self.max_connections = max_connections
        
        # 随机化控制参数
        self.randomize_bs = randomize_bs
        self.randomize_users = randomize_users
        self.randomize_uav_start = randomize_uav_start
        
        # 距离重叠惩罚参数
        self.distance_overlap_penalty_weight = distance_overlap_penalty_weight
        
        # 通信参数
        self.carrier_frequency = 2e9
        self.tx_power = 23
        self.noise_power = -80
        self.use_shadowing = use_shadowing
        self.paper_reward = paper_reward
        self.use_fdma = use_fdma
        self.bandwidth = bandwidth
        self.ground_bs_tx_power = ground_bs_tx_power
        self.aclr_db = aclr_db  # 存储ACLR值
        self.aclr_linear = 10 ** (-self.aclr_db / 10)  # 转换为线性值以便计算

        # 局部观测参数
        self.max_observed_uavs = max_observed_uavs
        self.max_observed_users = max_observed_users

        # 智能体列表
        self.possible_agents = [f"uav_{i}" for i in range(n_uavs)]
        self.agents = self.possible_agents.copy()

        # 观测和动作空间
        self.obs_dim = 3 + max_observed_users * 3 + max_observed_uavs * 4 + 1 + self.n_ground_bs + 1
        self.observation_spaces = {
            agent: Dict({
                "obs": Box(low=-float('inf'), high=float('inf'), shape=(self.obs_dim,)),
                "action_mask": Box(low=0, high=1, shape=(3,))
            }) for agent in self.possible_agents
        }
        self.action_spaces = {
            agent: Box(low=-1, high=1, shape=(3,))
            for agent in self.possible_agents
        }

        # 初始化地面基站
        self._init_ground_bs()
        
        # 渲染相关
        self.viewer = None
        self.fig = None
        self.ax = None
        
        # 重新计算并设置场景4的状态维度
        # 1. 无人机位置: n_uavs * 3
        uav_pos_dim = self.n_uavs * 3
        
        # 2. 用户位置: n_users * 2
        user_pos_dim = self.n_users * 2
        
        # 3. 地面基站位置: n_ground_bs * 3
        bs_pos_dim = self.n_ground_bs * 3
        
        # 4. 用户覆盖状态: n_users
        user_covered_dim = self.n_users
        
        # 5. 无人机连接状态: n_uavs
        uav_connected_dim = self.n_uavs
        
        # 6. 当前步数: 1
        step_dim = 1
        
        # 重新设置state_dim
        self.state_dim = uav_pos_dim + user_pos_dim + bs_pos_dim + user_covered_dim + uav_connected_dim + step_dim

    def get_state_dim(self):
        """返回全局状态维度"""
        return self.state_dim
    
    def get_obs_dim(self):
        """返回观测维度"""
        return self.obs_dim

    def _compute_path_loss(self, uav_pos, user_pos):
        """
        重写父类的路径损耗计算方法，使用精确的A2G模型
        
        参数:
            uav_pos: 无人机位置 [3]
            user_pos: 用户位置 [2] 或索引
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        # 检查 user_pos 是否为整数索引，如果是则获取对应的用户位置
        if isinstance(user_pos, (int, np.integer)):
            user_pos = self.user_positions[user_pos]
            
        # 确保 user_pos 是二维的 (x, y)，假设用户在地面
        if len(user_pos) > 2:
            user_pos_2d = user_pos[:2]
            user_pos_3d = user_pos
        else:
            user_pos_2d = user_pos
            user_pos_3d = np.append(user_pos, 0)  # 用户在地面，z=0
        
        # 使用scenario4中的精确A2G路径损耗模型
        return self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
    
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
            user_positions: 用户位置 [n_users, 2]
        """
        if self.user_distribution == "forced_relay_cluster":
            return self._generate_forced_relay_cluster_positions()
        elif self.user_distribution == "uniform":
            user_positions = np.zeros((self.n_users, 2))
            for i in range(self.n_users):
                user_positions[i] = [
                    self.np_random.uniform(0, self.area_size),
                    self.np_random.uniform(0, self.area_size)
                ]
            return user_positions
        else:
            # 默认或未指定时，也使用强制中继的簇分布
            return self._generate_forced_relay_cluster_positions()
    
    def _generate_forced_relay_cluster_positions(self):
        """
        生成针对强制中继优化的用户簇分布 - 支持固定或随机的簇中心
        
        特点：
        - 用户集中在中心区域，便于覆盖
        - 形成紧密的簇，减少覆盖难度
        - 距离地面基站较远，强制多跳
        
        返回:
            user_positions: 用户位置 [n_users, 2]
        """
        user_positions = np.zeros((self.n_users, 2))
        
        # 定义中心区域的边界（用户集中在这里）
        central_size = self.area_size * self.central_area_ratio
        central_margin = (self.area_size - central_size) / 2
        
        # 生成簇中心位置
        cluster_centers = np.zeros((self.n_clusters, 2))
        
        # --- 随机化簇中心 ---
        if self.randomize_users:
            # 随机在中心区域内生成簇中心
            for i in range(self.n_clusters):
                # 确保簇中心之间有足够的距离，避免重叠
                max_attempts = 50
                for attempt in range(max_attempts):
                    x = self.np_random.uniform(central_margin, central_margin + central_size)
                    y = self.np_random.uniform(central_margin, central_margin + central_size)
                    new_center = np.array([x, y])
                    
                    # 检查与已有簇中心的距离
                    min_distance = self.cluster_std * 3  # 簇中心之间的最小距离
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
                    # 如果找不到合适的位置，使用网格布局作为备选
                    grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
                    grid_i = i // grid_size
                    grid_j = i % grid_size
                    x = central_margin + central_size * (grid_i + 0.5) / grid_size
                    y = central_margin + central_size * (grid_j + 0.5) / grid_size
                    cluster_centers[i] = [x, y]
        else:
            # --- 保留原有的固定簇中心逻辑 ---
            if self.n_clusters == 4:
                # 4个簇形成2x2网格
                cluster_centers[0] = [central_margin + central_size * 0.3, central_margin + central_size * 0.3]
                cluster_centers[1] = [central_margin + central_size * 0.7, central_margin + central_size * 0.3]
                cluster_centers[2] = [central_margin + central_size * 0.3, central_margin + central_size * 0.7]
                cluster_centers[3] = [central_margin + central_size * 0.7, central_margin + central_size * 0.7]
            elif self.n_clusters == 3:
                # 3个簇形成三角形
                cluster_centers[0] = [central_margin + central_size * 0.5, central_margin + central_size * 0.2]
                cluster_centers[1] = [central_margin + central_size * 0.2, central_margin + central_size * 0.8]
                cluster_centers[2] = [central_margin + central_size * 0.8, central_margin + central_size * 0.8]
            elif self.n_clusters == 5:
                # 5个簇：中心1个 + 四周4个
                cluster_centers[0] = [central_margin + central_size * 0.5, central_margin + central_size * 0.5]
                cluster_centers[1] = [central_margin + central_size * 0.2, central_margin + central_size * 0.2]
                cluster_centers[2] = [central_margin + central_size * 0.8, central_margin + central_size * 0.2]
                cluster_centers[3] = [central_margin + central_size * 0.2, central_margin + central_size * 0.8]
                cluster_centers[4] = [central_margin + central_size * 0.8, central_margin + central_size * 0.8]
            else:
                # 其他情况使用网格布局
                grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
                cluster_idx = 0
                
                for i in range(grid_size):
                    for j in range(grid_size):
                        if cluster_idx >= self.n_clusters:
                            break
                        
                        # 网格位置
                        grid_x = central_margin + central_size * (i + 0.5) / grid_size
                        grid_y = central_margin + central_size * (j + 0.5) / grid_size
                        
                        cluster_centers[cluster_idx] = [grid_x, grid_y]
                        cluster_idx += 1
                    
                    if cluster_idx >= self.n_clusters:
                        break
        
        # 计算每个簇的用户数量 - 确保总数正确
        base_users_per_cluster = self.n_users // self.n_clusters
        remaining_users = self.n_users % self.n_clusters
        
        cluster_user_counts = [base_users_per_cluster] * self.n_clusters
        # 将剩余用户分配给前几个簇
        for i in range(remaining_users):
            cluster_user_counts[i] += 1
        
        # 为每个簇生成用户
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
                
                user_position = cluster_center + offset
                
                # 确保用户位置在有效区域内
                user_position[0] = np.clip(user_position[0], 10, self.area_size - 10)
                user_position[1] = np.clip(user_position[1], 10, self.area_size - 10)
                
                user_positions[user_idx] = user_position
                user_idx += 1
        
        return user_positions
    
    def _get_grid_coords(self, position):
        """
        将连续坐标转换为离散的栅格坐标
        
        参数:
            position: 位置坐标 [x, y] 或 [x, y, z]
            
        返回:
            grid_coords: 栅格坐标 (grid_x, grid_y)
        """
        x, y = position[0], position[1]
        
        # 将坐标转换为栅格索引
        grid_x = int(np.clip(x / self.grid_resolution, 0, self.grid_size - 1))
        grid_y = int(np.clip(y / self.grid_resolution, 0, self.grid_size - 1))
        
        return (grid_x, grid_y)
    
    def _initialize_belief(self):
        """Initialize or reset the belief map to a uniform prior."""
        if self.belief_map.size > 0:
            self.belief_map.fill(1.0 / self.belief_map.size)

    def _update_belief_map(self):
        """
        Updates the belief map based on agent actions and observations.
        This method is called within step().
        """
        # 1. Decay belief for observed cells based on a more precise observation model.
        # A cell's belief is decayed only if it's observed by a UAV and found to be empty of unserviced users.
        
        # Create a set of grid cells that contain unserviced users for efficient lookup
        unserviced_user_cells = set()
        for user_idx, is_serviced in enumerate(self.user_serviced_status):
            if not is_serviced:
                user_pos = self.user_positions[user_idx]
                user_gx, user_gy = self._get_grid_coords(user_pos)
                unserviced_user_cells.add((user_gx, user_gy))

        # Identify all cells observed by any UAV in this step
        all_observed_cells = set()
        for uav_pos in self.uav_positions:
            # Assume a UAV observes its current grid cell and immediate neighbors (3x3 area)
            gx, gy = self._get_grid_coords(uav_pos)
            for y_offset in range(-1, 2):
                for x_offset in range(-1, 2):
                    cell_y, cell_x = gy + y_offset, gx + x_offset
                    if 0 <= cell_y < self.grid_size and 0 <= cell_x < self.grid_size:
                        all_observed_cells.add((cell_x, cell_y))
        
        # Decay belief only for cells that are observed but contain no unserviced users
        for gx, gy in all_observed_cells:
            if (gx, gy) not in unserviced_user_cells:
                self.belief_map[gy, gx] *= self.belief_decay_factor

        # 2. Simulate reconnaissance hint (e.g., every recon_interval steps)
        # This simulates receiving noisy, delayed AOI (Area of Interest) data.
        if self.current_step > 0 and self.current_step % self.recon_interval == 0:
            for user_pos in self.user_positions:
                # Check if this user is still a target (not yet serviced)
                # This requires tracking serviced users. We'll assume for now
                # that `self.user_serviced_status` exists.
                user_grid_x, user_grid_y = self._get_grid_coords(user_pos)
                
                # Increase belief in a small 3x3 area around the user
                # We use clipping to handle boundaries gracefully.
                y_min, y_max = max(0, user_grid_y - 1), min(self.grid_size, user_grid_y + 2)
                x_min, x_max = max(0, user_grid_x - 1), min(self.grid_size, user_grid_x + 2)
                self.belief_map[y_min:y_max, x_min:x_max] += self.recon_strength

        # 3. Handle serviced users (This is done in the step method logic)
        # When a user is serviced, the belief at that location is set to 0.

        # 4. Normalize the belief map
        # Ensure the sum of probabilities is 1.
        map_sum = self.belief_map.sum()
        if map_sum > 0:
            self.belief_map /= map_sum
        else:
            # If all belief is zero, re-initialize to uniform to avoid getting stuck
            self._initialize_belief()

    def _calculate_potential(self):
        """
        Calculates the global potential Φ(s) based on the current belief_map.
        Formula: Φ(s) = Σ [ belief(y,x) * (-min_dist_to_drone(y,x)) ]
        """
        if self.n_uavs == 0:
            return 0.0

        # Get drone positions in 2D for distance calculation
        drone_positions_2d = self.uav_positions[:, :2]

        # Calculate distances from all cell centers to all drones efficiently
        # distances shape: (num_cells, num_agents)
        distances = cdist(self.cell_centers, drone_positions_2d)
        
        # Find the distance to the *nearest* drone for each cell
        # min_distances shape: (num_cells,)
        min_distances = distances.min(axis=1)
        
        # Get belief probabilities for all cells as a flat array
        belief_flat = self.belief_map.flatten()
        
        # Calculate potential: dot product of beliefs and negative distances
        potential = np.dot(belief_flat, -min_distances)
        return potential
    
    def _compute_coverage_overlap_penalty(self):
        """
        计算基于潜在覆盖能力的重叠惩罚
        
        重叠定义：一个用户同时被多个无人机以高于SINR阈值的信号覆盖
        这能惩罚"扎堆"行为，即使最终只有一个无人机提供服务
        
        返回:
            overlap_penalty: 重叠惩罚值 [0, 1]
        """
        if not hasattr(self, 'sinr_matrix') or self.sinr_matrix is None:
            return 0.0
        
        total_redundant_coverage = 0
        
        # 遍历每个用户，统计能够覆盖它的无人机数量
        for user_idx in range(self.n_users):
            # 统计能够覆盖该用户的无人机数量（SINR达标）
            potential_servers = np.sum(self.sinr_matrix[:, user_idx] >= self.min_sinr)
            
            # 如果有多个无人机可以覆盖同一用户，产生冗余
            if potential_servers > 1:
                redundant_count = potential_servers - 1  # 冗余覆盖数 = 总覆盖数 - 1
                total_redundant_coverage += redundant_count
        
        # 归一化惩罚值：用总冗余覆盖数除以用户总数
        # 这可以理解为"平均每个用户的冗余覆盖度"
        if self.n_users > 0:
            # 将惩罚归一化到[0,1]范围，假设平均冗余不超过5
            normalized_penalty = total_redundant_coverage / (self.n_users * 5)
        else:
            normalized_penalty = 0.0
        
        # 确保惩罚值在合理范围内
        overlap_penalty = np.clip(normalized_penalty, 0.0, 1.0)
        
        return overlap_penalty
    
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
    
    def _calculate_distance_overlap_penalty(self):
        """
        计算基于距离的重叠惩罚 - 使用平滑的距离函数替代SINR重叠惩罚
        
        核心思想：
        - 当无人机距离过近时施加惩罚
        - 使用平滑的距离函数，避免突变
        - 服务半径内的距离产生较大惩罚，两倍服务半径外无惩罚
        
        返回:
            overlap_penalty: 距离重叠惩罚值 [0, 1]
        """
        overlap_penalty = 0.0
        # 一个预估的服务半径，例如150米（通信范围的1/4）
        service_radius = self.uav_communication_range / 4 
        
        for i in range(self.n_uavs):
            for j in range(i + 1, self.n_uavs):
                # 计算两个无人机之间的2D距离（忽略高度差异）
                dist = np.linalg.norm(self.uav_positions[i, :2] - self.uav_positions[j, :2])
                
                # 如果距离小于两倍服务半径，施加惩罚
                if dist < 2 * service_radius:
                    # 使用平滑的二次函数：(1 - dist / (2 * service_radius))^2
                    penalty = (1 - dist / (2 * service_radius)) ** 2
                    overlap_penalty += penalty
        
        # 归一化，最大惩罚发生在所有无人机都在一点，为 n_uavs * (n_uavs-1) / 2
        max_penalty = self.n_uavs * (self.n_uavs - 1) / 2
        return overlap_penalty / max_penalty if max_penalty > 0 else 0.0
    
    
    def _compute_belief_stats(self):
        """
        计算信念地图的统计信息，用于TensorBoard记录
        
        返回:
            belief_stats: 信念统计字典，包含熵、最大值、最小值等
        """
        if not hasattr(self, 'belief_map') or self.belief_map.size == 0:
            return {
                'belief_entropy': 0.0,
                'max_belief_value': 0.0,
                'min_belief_value': 0.0,
                'mean_belief_value': 0.0,
                'belief_concentration': 0.0,
                'high_belief_cells': 0
            }
        
        # 获取信念地图的扁平化数组
        belief_flat = self.belief_map.flatten()
        
        # 1. 计算信念熵
        # 熵 = -Σ(p * log(p))，其中p是每个栅格的信念概率
        # 高熵表示信念分散（高不确定性），低熵表示信念集中
        epsilon = 1e-10  # 避免log(0)
        belief_probs = belief_flat + epsilon
        belief_entropy = -np.sum(belief_probs * np.log(belief_probs + epsilon))
        
        # 归一化熵到[0,1]范围 (最大熵为log(N)，其中N是栅格总数)
        max_entropy = np.log(self.belief_map.size)
        normalized_entropy = belief_entropy / max_entropy if max_entropy > 0 else 0.0
        
        # 2. 计算基本统计量
        max_belief = np.max(belief_flat)
        min_belief = np.min(belief_flat)
        mean_belief = np.mean(belief_flat)
        
        # 3. 计算信念集中度
        # 集中度定义为：顶部10%栅格的信念总和
        top_10_percent_count = max(1, int(0.1 * self.belief_map.size))
        sorted_beliefs = np.sort(belief_flat)[::-1]  # 降序排列
        top_10_percent_sum = np.sum(sorted_beliefs[:top_10_percent_count])
        belief_concentration = top_10_percent_sum
        
        # 4. 计算高信念栅格数量
        # 定义"高信念"为超过平均值2倍的栅格
        high_belief_threshold = mean_belief * 2
        high_belief_cells = np.sum(belief_flat > high_belief_threshold)
        
        # 5. 计算信念方差
        belief_variance = np.var(belief_flat)
        
        # 6. 计算信念分布的偏度（衡量分布的非对称性）
        # 正偏度表示信念主要集中在低值区域，负偏度表示集中在高值区域
        if belief_variance > 0:
            belief_skewness = np.mean(((belief_flat - mean_belief) / np.sqrt(belief_variance)) ** 3)
        else:
            belief_skewness = 0.0
        
        return {
            'belief_entropy': float(normalized_entropy),
            'max_belief_value': float(max_belief),
            'min_belief_value': float(min_belief),
            'mean_belief_value': float(mean_belief),
            'belief_concentration': float(belief_concentration),
            'high_belief_cells': int(high_belief_cells),
            'belief_variance': float(belief_variance),
            'belief_skewness': float(belief_skewness),
            'total_belief_mass': float(np.sum(belief_flat))
        }
    
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
    
    def _compute_reward(self, potential_reward, potential_reward_raw=None):
        """
        计算并组合所有奖励分量，以生成最终的全局奖励。
        
        再次重构后的逻辑：
        - 核心目标奖励：用户覆盖率。
        - 统一链路塑造奖励：一个综合指标，评估整个网络骨干的质量（容量+效率）。
        - 其他塑造奖励：探索奖励。
        - 惩罚项：重叠惩罚。
        
        参数:
            potential_reward: 从step函数传入的归一化后的基于势函数的塑形奖励
            potential_reward_raw: 原始未归一化的势函数奖励（用于调试和记录）
            
        返回:
            global_reward: 最终组合的全局奖励
        """
        
        # 1. 核心目标奖励 (Primary Goal Reward) - 用户覆盖率
        effective_connected_users = 0
        total_connected_users = 0
        for i in range(self.n_uavs):
            uav_connected_users = np.sum(self.connections[i])
            total_connected_users += uav_connected_users
            # 检查 self.routing_paths[i] 是否存在且非空
            if i in self.routing_paths and self.routing_paths[i][0]:
                effective_connected_users += uav_connected_users
        
        coverage_ratio = effective_connected_users / self.n_users if self.n_users > 0 else 0
        coverage_reward_raw = np.power(coverage_ratio, 0.5)
        coverage_bonus = 0
        if coverage_ratio >= 0.95: coverage_bonus = 0.15
        elif coverage_ratio >= 0.90: coverage_bonus = 0.10
        elif coverage_ratio >= 0.85: coverage_bonus = 0.05
        final_coverage_reward = min(1.0, coverage_reward_raw + coverage_bonus)

        # 2. 行为塑造奖励 (Shaping Rewards)
        # 2.1 统一的链路质量奖励 (Unified Link Quality Reward)
        link_quality_reward = self._calculate_link_quality_reward()
        
        # 2.2 探索奖励 (从step函数传入)
        # potential_reward is already calculated
        
        # 3. 惩罚项 (Penalties)
        # 使用基于SINR的重叠惩罚，因为它与信道模型更一致
        coverage_overlap_penalty = self._compute_coverage_overlap_penalty()
        
        # 4. 组合所有奖励分量
        # 获取各分量权重
        coverage_weight = self.coverage_weight # 核心目标权重
        link_quality_weight = self.link_quality_weight # 使用独立定义的链路质量权重
        potential_reward_weight = self.potential_reward_weight
        # 注意：这里我们复用 distance_overlap_penalty_weight 作为覆盖重叠惩罚的权重
        overlap_penalty_weight = self.distance_overlap_penalty_weight
        
        # 计算最终全局奖励
        global_reward = (
            coverage_weight * final_coverage_reward +
            link_quality_weight * link_quality_reward +
            potential_reward_weight * potential_reward -
            overlap_penalty_weight * coverage_overlap_penalty
        )
        
        # 5. 计算系统吞吐量和性能指标（用于信息记录）
        system_throughput = 0
        avg_hops = 0
        connected_uavs = len(self.routing_paths)
        if connected_uavs > 0:
            total_hops = sum(len(path) - 1 for path, capacity in self.routing_paths.values())
            avg_hops = total_hops / connected_uavs

        for i in range(self.n_uavs):
            if i in self.routing_paths:
                connected_users_to_uav = [j for j, connected in enumerate(self.connections[i]) if connected]
                if connected_users_to_uav:
                    system_throughput += self._compute_uav_frontend_capacity(i, connected_users_to_uav)

        # 6. 更新奖励信息字典，用于调试和可视化
        self.reward_info = {
            # 核心目标
            "coverage_reward": final_coverage_reward,
            
            # 塑造奖励 & 惩罚
            "link_quality_reward": link_quality_reward,
            "potential_reward": potential_reward,
            "potential_reward_raw": potential_reward_raw if potential_reward_raw is not None else 0.0,
            "coverage_overlap_penalty": coverage_overlap_penalty,
            
            # 加权后的各分量贡献
            "weighted_coverage": coverage_weight * final_coverage_reward,
            "weighted_link_quality": link_quality_weight * link_quality_reward,
            "weighted_potential": potential_reward_weight * potential_reward,
            "weighted_overlap_penalty": -overlap_penalty_weight * coverage_overlap_penalty,
            
            # 最终奖励
            "final_global_reward": global_reward,
            
            # 性能指标
            "coverage_ratio": coverage_ratio,
            "effective_connected_users": effective_connected_users,
            "total_connected_users": total_connected_users,
            "connected_uavs": connected_uavs,
            "avg_hops": avg_hops,
            "system_throughput_mbps": system_throughput / 1e6,
            "avg_throughput_per_user_mbps": (system_throughput / max(effective_connected_users, 1)) / 1e6,
            "target_coverage_achieved": coverage_ratio >= 0.90,
        }
        
        return global_reward
    
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
            for uav_idx, path in self.routing_paths.items():
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
            self.ax.text2D(0.02, 0.85, f'Coverage: {reward_info.get("base_coverage_ratio", 0):.1%}', 
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
            self.ax.text2D(0.75, 0.80, f'Connectivity Reward: {reward_info.get("connectivity_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9)
            self.ax.text2D(0.75, 0.75, f'Efficiency Reward: {reward_info.get("efficiency_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9)
            self.ax.text2D(0.75, 0.70, f'Overlap Penalty: {reward_info.get("overlap_penalty", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9, color='red')
            self.ax.text2D(0.75, 0.65, f'Total Reward: {reward_info.get("final_reward", 0):.3f}', 
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
        获取用户簇的中心位置（用于可视化）
        
        返回:
            cluster_centers: 簇中心位置列表
        """
        if not hasattr(self, 'user_positions') or self.user_positions is None:
            return []
        
        # 使用预定义的簇中心（因为我们用的是规整布局）
        central_size = self.area_size * self.central_area_ratio
        central_margin = (self.area_size - central_size) / 2
        
        cluster_centers = []
        
        if self.n_clusters == 4:
            cluster_centers = [
                [central_margin + central_size * 0.3, central_margin + central_size * 0.3],
                [central_margin + central_size * 0.7, central_margin + central_size * 0.3],
                [central_margin + central_size * 0.3, central_margin + central_size * 0.7],
                [central_margin + central_size * 0.7, central_margin + central_size * 0.7]
            ]
        elif self.n_clusters == 3:
            cluster_centers = [
                [central_margin + central_size * 0.5, central_margin + central_size * 0.2],
                [central_margin + central_size * 0.2, central_margin + central_size * 0.8],
                [central_margin + central_size * 0.8, central_margin + central_size * 0.8]
            ]
        # 可以根据需要添加更多预定义布局
        
        return cluster_centers
    
    def reset(self, seed=None, options=None):
        """
        重置环境 - 确保使用场景4特定的全局状态
        
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
        self._initialize_belief()
        self.user_serviced_status.fill(False)
        
        # 2. 使用本类的方法初始化UAV和用户位置
        self.uav_positions = self._init_uav_positions()
        self.user_positions = self._generate_user_positions()
        
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
        self.current_potential = self._calculate_potential()
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
        user_pos_3d = np.append(self.user_positions[user_idx], 0)
        
        # 使用精确的A2G路径损耗模型
        path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的UAV-User SINR计算
        sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
        
        return sinr_db

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
        # 1. Store potential from the previous step
        potential_t = self.current_potential

        # 2. Update agent positions based on actions
        for agent_idx, agent in enumerate(self.agents):
            if agent in actions:
                # 计算原始速度向量
                raw_velocity = actions[agent] * self.max_speed
                
                # 计算速度向量的模长（3D速度）
                speed = np.linalg.norm(raw_velocity)
                
                # 确保3D速度不超过最大限制
                if speed > self.max_speed:
                    # 如果速度超过了最大限制，则将速度向量归一化，然后乘以最大速度
                    velocity = raw_velocity / speed * self.max_speed
                else:
                    # 如果速度未超过限制，则直接使用
                    velocity = raw_velocity
                
                new_position = self.uav_positions[agent_idx] + velocity * self.time_step
                
                # Boundary checks
                new_position[0] = np.clip(new_position[0], 0, self.area_size)
                new_position[1] = np.clip(new_position[1], 0, self.area_size)
                new_position[2] = np.clip(new_position[2], *self.height_range)
                self.uav_positions[agent_idx] = new_position
        
        # 3. Update system state based on new positions
        self._update_channel_state()
        self._update_uav_connections()
        self._compute_routing_paths()


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
                
                # Set belief at the user's location to zero as they are found
                user_grid_x, user_grid_y = self._get_grid_coords(self.user_positions[user_idx])
                self.belief_map[user_grid_y, user_grid_x] = 0.0

        # 5. Update belief map (decay, recon, normalization)
        self._update_belief_map()

        # 6. Calculate new potential and the potential-based shaping reward
        potential_t1 = self._calculate_potential()
        potential_reward_raw = self.gamma * potential_t1 - potential_t
        self.current_potential = potential_t1

        # 6.1 归一化 potential_reward
        # 估算单步内无人机可能产生的最大势能变化量
        max_potential_change = self.max_speed * self.time_step * self.n_uavs
        potential_reward = np.clip(potential_reward_raw / max_potential_change, -1.0, 1.0)
        
        # 7. 计算全局奖励（所有奖励计算已集中到 _compute_reward 中）
        global_reward = self._compute_reward(potential_reward, potential_reward_raw)

        # 8. 更新 info 字典中需要额外计算的统计数据
        # 8.1 计算并更新信念地图统计信息
        belief_stats = self._compute_belief_stats()
        self.reward_info.update(belief_stats)
        
        # 8.2 存储当前和上一时刻的势函数值
        self.reward_info["current_potential"] = potential_t1
        self.reward_info["previous_potential"] = potential_t
        
        # 9. 更新步数并检查终止条件
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # 10. 准备返回值
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        # 11. 获取新的观测并填充返回值
        for agent_idx, agent in enumerate(self.agents):
            observations[agent] = self._get_observation(agent)
            rewards[agent] = global_reward / self.n_uavs  # 平均分配全局奖励
            terminations[agent] = done
            truncations[agent] = False
            infos[agent] = {
                "reward_info": self.reward_info.copy(),
                "coverage_ratio": self.reward_info.get("coverage_ratio", 0),
                "connectivity_ratio": len(self.routing_paths) / self.n_uavs if self.n_uavs > 0 else 0,
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

    def _compute_distance(self, pos1, pos2):
        return np.sqrt(np.sum((pos1 - pos2) ** 2))

    def _update_observations_dict(self, observations_dict):
        updated_observations_dict = {}
        for i, agent in enumerate(self.agents):
            obs_dict = observations_dict[agent]
            obs = obs_dict["obs"]
            
            bs_connections = self.uav_bs_connections[i]
            
            if i in self.routing_paths:
                hop_count = len(self.routing_paths[i])
                normalized_hop = min(hop_count / self.max_hops, 1.0)
            else:
                normalized_hop = 1.0
            
            new_obs = np.concatenate([obs, bs_connections, [normalized_hop]])
            
            updated_obs_dict = {
                "obs": new_obs,
                "action_mask": obs_dict["action_mask"]
            }
            updated_observations_dict[agent] = updated_obs_dict
        
        return updated_observations_dict

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
        
        # 2. 局部用户观测 (max_observed_users * 3维)
        local_users = self._get_local_users(agent_idx)
        user_obs = np.zeros(self.max_observed_users * 3)
        
        for i, (user_idx, sinr_db) in enumerate(local_users):
            if i >= self.max_observed_users:
                break
            
            user_pos = self.user_positions[user_idx]
            # 相对位置 (x, y) - 归一化
            relative_pos = (user_pos - own_position[:2]) / self.area_size
            # 归一化SINR到[0,1]范围 (假设SINR范围为-10dB到40dB)
            normalized_sinr = np.clip((sinr_db + 10) / 50, 0, 1)
            
            start_idx = i * 3
            user_obs[start_idx:start_idx+3] = [relative_pos[0], relative_pos[1], normalized_sinr]
        
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
        
        # 4. 当前步数 (1维)
        step_normalized = np.array([self.current_step / self.max_steps])
        obs_components.append(step_normalized)
        
        # 组合所有观测
        obs = np.concatenate(obs_components)
        
        # 动作掩码（这里我们不限制动作，所以全为1）
        action_mask = np.ones(3)
        
        return {"obs": obs, "action_mask": action_mask}

    def _get_local_users(self, agent_idx):
        """
        获取指定无人机可通信的用户列表（基于SINR阈值）
        
        参数:
            agent_idx: 无人机索引
            
        返回:
            local_users: 按SINR降序排序的(用户索引, SINR)元组列表
        """
        local_users = []
        
        for user_idx in range(self.n_users):
            # 使用本类重写的_compute_sinr
            sinr_db = self._compute_sinr(agent_idx, user_idx)
            
            if sinr_db >= self.min_sinr:
                local_users.append((user_idx, sinr_db))
        
        local_users.sort(key=lambda x: x[1], reverse=True)
        return local_users

    def _get_local_uavs(self, agent_idx):
        """
        获取指定无人机可通信的其他无人机列表（基于SINR阈值）
        
        参数:
            agent_idx: 无人机索引
            
        返回:
            local_uavs: 按SINR降序排序的(无人机索引, SINR)元组列表
        """
        local_uavs = []
        
        for other_idx in range(self.n_uavs):
            if other_idx == agent_idx:
                continue
            
            # 使用本类重写的_compute_uav_to_uav_sinr
            sinr_db = self._compute_uav_to_uav_sinr(agent_idx, other_idx)
            
            if sinr_db >= self.min_sinr:
                local_uavs.append((other_idx, sinr_db))
        
        local_uavs.sort(key=lambda x: x[1], reverse=True)
        return local_uavs

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
            "coverage_weight": self.coverage_weight,
            "link_quality_weight": self.link_quality_weight,
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
            # 非FDMA模式下，链路独占全部带宽
            link_bandwidth = self.bandwidth
            
        # 转换为线性单位并计算容量
        sinr_linear = 10 ** (sinr_db / 10)
        capacity = link_bandwidth * np.log2(1 + sinr_linear)
        
        return capacity
    
    def _compute_air_to_ground_path_loss(self, uav_pos, ground_pos):
        """
        计算空对地路径损耗（A2G）- 使用精确的概率性LoS/NLoS模型
        
        参数:
            uav_pos: UAV位置 [3] (x, y, z)
            ground_pos: 地面位置 [3] (x, y, z)
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        # 计算3D距离和水平距离
        distance_3d = self._compute_distance(uav_pos, ground_pos)
        distance_2d = np.sqrt((uav_pos[0] - ground_pos[0])**2 + (uav_pos[1] - ground_pos[1])**2)
        height = abs(uav_pos[2] - ground_pos[2])
        
        # 确保距离不为零
        safe_distance_3d = max(distance_3d, 1e-6)
        safe_distance_2d = max(distance_2d, 1e-6)
        
        # 计算仰角 (度)
        elevation_angle = np.degrees(np.arctan(height / safe_distance_2d))
        
        # 环境参数设置 (基于您提供的模型参数)
        if hasattr(self, 'environment_type'):
            env_type = self.environment_type
        else:
            env_type = "suburban"  # 默认郊区环境
        
        # LoS概率参数
        if env_type == "suburban":
            a, b, phi_0 = 0.77, 0.05, 15.0
            eta_los, eta_nlos = 0.1, 21.0
        elif env_type == "urban":
            a, b, phi_0 = 0.63, 0.09, 15.0
            eta_los, eta_nlos = 1.0, 20.0
        elif env_type == "dense_urban":
            a, b, phi_0 = 0.37, 0.21, 15.0
            eta_los, eta_nlos = 1.6, 23.0
        else:
            # 默认郊区参数
            a, b, phi_0 = 0.77, 0.05, 15.0
            eta_los, eta_nlos = 0.1, 21.0
        
        # 计算LoS概率
        if elevation_angle >= phi_0:
            p_los = a * ((elevation_angle - phi_0) ** b)
        else:
            p_los = 0.1  # 低仰角时给一个最小LoS概率
        
        p_los = np.clip(p_los, 0.0, 1.0)
        
        # 基础自由空间路径损耗
        wavelength = 3e8 / self.carrier_frequency
        fspl = 20 * np.log10(safe_distance_3d) + 20 * np.log10(4 * np.pi / wavelength)
        
        # 计算LoS和NLoS路径损耗
        pl_los = fspl + eta_los
        pl_nlos = fspl + eta_nlos
        
        # 使用期望值模型：使用平均路径损耗（在线性域加权，然后转回dB）
        pl_los_linear = 10 ** (-pl_los / 10)
        pl_nlos_linear = 10 ** (-pl_nlos / 10)
        pl_avg_linear = p_los * pl_los_linear + (1 - p_los) * pl_nlos_linear
        path_loss = -10 * np.log10(pl_avg_linear)
        
        return path_loss
    
    def _compute_ground_to_air_path_loss(self, ground_pos, uav_pos):
        """
        计算地对空路径损耗（G2A）- 与A2G使用相同模型
        
        参数:
            ground_pos: 地面位置 [3] (x, y, z)
            uav_pos: UAV位置 [3] (x, y, z)
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        # G2A与A2G使用相同的物理传播模型
        return self._compute_air_to_ground_path_loss(uav_pos, ground_pos)
    
    def _compute_air_to_air_path_loss(self, uav_pos1, uav_pos2):
        """
        计算空对空路径损耗（A2A）- 使用自由空间模型
        
        参数:
            uav_pos1: UAV1位置 [3] (x, y, z)
            uav_pos2: UAV2位置 [3] (x, y, z)
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        # 计算3D距离
        distance_3d = self._compute_distance(uav_pos1, uav_pos2)
        safe_distance = max(distance_3d, 1e-6)
        
        # A2A使用纯自由空间路径损耗模型
        # 路径损耗指数 α = 2.0
        wavelength = 3e8 / self.carrier_frequency
        path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
        
        return path_loss
    
    def _compute_link_sinr(self, tx_type, tx_idx, rx_type, rx_idx, rx_power):
        """
        计算链路SINR，考虑实际干扰情况
        
        参数:
            tx_type: 发送节点类型
            tx_idx: 发送节点索引
            rx_type: 接收节点类型
            rx_idx: 接收节点索引
            rx_power: 接收功率 (dBm)
            
        返回:
            sinr_db: SINR (dB)
        """
        if self.use_fdma:
            # FDMA模式：计算来自其他所有活动链路的邻道干扰 (ACI)
            # 简化模型：干扰功率 = 发射功率 * 路径损耗 * ACLR
            # 我们进一步简化，假设所有干扰源的路径损耗对接收机的影响相似，
            # 直接使用 发射功率 * ACLR 作为干扰项。
            interference_powers_linear = []
            
            # 1. 来自其他UAV的干扰
            for i in range(self.n_uavs):
                # 排除发送方自身
                if tx_type == "uav" and i == tx_idx:
                    continue
                
                # 计算干扰源到接收机的路径损耗
                interferer_pos = self.uav_positions[i]
                if rx_type == "uav":
                    rx_pos = self.uav_positions[rx_idx]
                    interferer_path_loss = self._compute_air_to_air_path_loss(interferer_pos, rx_pos)
                elif rx_type == "ground_bs":
                    rx_pos = self.ground_bs_positions[rx_idx]
                    interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, rx_pos)
                else:
                    continue
                
                # 计算干扰功率：发射功率 - 路径损耗，然后转为线性值，再乘以ACLR
                interferer_rx_power_dbm = self.tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                # 邻道干扰功率 = 接收功率 * ACLR
                interference_powers_linear.append(interferer_rx_power_linear * self.aclr_linear)

            # 2. 来自其他BS的干扰
            for i in range(self.n_ground_bs):
                if tx_type == "ground_bs" and i == tx_idx:
                    continue
                
                # 计算干扰源到接收机的路径损耗
                interferer_pos = self.ground_bs_positions[i]
                if rx_type == "uav":
                    rx_pos = self.uav_positions[rx_idx]
                    interferer_path_loss = self._compute_ground_to_air_path_loss(interferer_pos, rx_pos)
                elif rx_type == "ground_bs":
                    # BS到BS的干扰（通常在实际中很少，但为完整性保留）
                    rx_pos = self.ground_bs_positions[rx_idx]
                    interferer_path_loss = self._compute_air_to_air_path_loss(interferer_pos, rx_pos)  # 使用A2A作为近似
                else:
                    continue
                
                # 计算干扰功率：发射功率 - 路径损耗，然后转为线性值，再乘以ACLR
                interferer_rx_power_dbm = self.ground_bs_tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                # 邻道干扰功率 = 接收功率 * ACLR
                interference_powers_linear.append(interferer_rx_power_linear * self.aclr_linear)

            total_interference_linear = np.sum(interference_powers_linear)
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            interference_plus_noise_linear = noise_power_linear + total_interference_linear
            interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
            
            sinr_db = rx_power - interference_plus_noise_dbm
        else:
            # 非FDMA模式：计算同频干扰
            interference_powers = []
            
            if rx_type == "uav":
                # 计算其他UAV对该接收UAV的干扰
                for i in range(self.n_uavs):
                    if i != tx_idx and i != rx_idx:  # 排除发送方和接收方
                        interferer_pos = self.uav_positions[i]
                        rx_pos = self.uav_positions[rx_idx]
                        interferer_path_loss = self._compute_air_to_air_path_loss(interferer_pos, rx_pos)
                        interferer_power = self.tx_power - interferer_path_loss
                        interference_powers.append(10 ** (interferer_power / 10))
            elif rx_type == "ground_bs":
                # 计算其他UAV对该接收基站的干扰
                for i in range(self.n_uavs):
                    if i != tx_idx:  # 排除发送UAV
                        interferer_pos = self.uav_positions[i]
                        rx_pos = self.ground_bs_positions[rx_idx]
                        interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, rx_pos)
                        interferer_power = self.tx_power - interferer_path_loss
                        interference_powers.append(10 ** (interferer_power / 10))
            
            # 总干扰功率 (所有干扰源的线性叠加)
            total_interference = np.sum(interference_powers) if interference_powers else 0
            total_interference_dbm = 10 * np.log10(total_interference) if total_interference > 0 else -float('inf')
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            if total_interference_dbm != -float('inf'):
                interference_plus_noise = noise_power_linear + total_interference
                interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise)
            else:
                interference_plus_noise_dbm = self.noise_power
            
            sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db
    
    def _compute_routing_paths(self):
        """
        使用基于瓶颈容量的智能路由算法计算每个UAV到地面基站的最优路径。
        
        新算法特点：
        1. 寻找瓶颈容量最大的路径，而不是跳数最少的路径。
        2. 使用类似Dijkstra的"最宽路径"算法。
        3. 智能选择高质量的多跳中继路径，即使跳数更多。
        4. 修改：现在存储路径和其对应的瓶颈容量。
        """
        self.routing_paths = {}
        
        # 为每个UAV计算最优路径
        for start_uav in range(self.n_uavs):
            path, capacity = self._find_widest_path_to_ground_bs(start_uav)
            # 确保路径有效且不超过最大跳数限制
            if path and capacity > 0 and len(path) <= self.max_hops + 1:
                self.routing_paths[start_uav] = (path, capacity)
    
    def _get_state(self):
        """
        获取针对强制中继场景优化的全局状态
        
        包含以下信息：
        1. 无人机位置 (n_uavs * 3)
        2. 用户位置 (n_users * 2) 
        3. 地面基站位置 (n_ground_bs * 3) - 关键信息
        4. 用户覆盖状态 (n_users) - 每个用户是否被覆盖
        5. 无人机连接状态 (n_uavs) - 每个无人机是否有到基站的路径
        6. 当前步数 (1)
        
        返回:
            state: 完整的全局状态向量
        """
        state_components = []
        
        # 1. 无人机位置 (归一化到[0,1])
        normalized_uav_positions = self.uav_positions.copy()
        normalized_uav_positions[:, :2] /= self.area_size  # x, y 归一化
        normalized_uav_positions[:, 2] = (normalized_uav_positions[:, 2] - self.height_range[0]) / (self.height_range[1] - self.height_range[0])  # z 归一化
        state_components.append(normalized_uav_positions.flatten())
        
        # 2. 用户位置 (归一化到[0,1])
        normalized_user_positions = self.user_positions / self.area_size
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
        
        # 6. 当前步数 (归一化到[0,1])
        step_normalized = np.array([self.current_step / self.max_steps])
        state_components.append(step_normalized)
        
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
            user_pos_3d = np.append(self.user_positions[user_idx], 0)  # 用户在地面，z=0
            
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
                        user_pos_3d = np.append(self.user_positions[user_idx], 0)
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
            # 非FDMA模式：用户共享频谱，总容量由瓶颈（最小）用户容量决定
            if user_capacities:
                # 找出有效连接用户的最小容量
                valid_capacities = [cap for cap in user_capacities if cap > 0]
                if valid_capacities:
                    # 共享信道的总容量等于瓶颈用户的容量
                    frontend_capacity = min(valid_capacities)
                else:
                    frontend_capacity = 0
            else:
                frontend_capacity = 0
        
        return frontend_capacity
    
    def _compute_uav_to_user_sinr(self, uav_idx, user_idx, rx_power):
        """
        计算UAV到用户通信的精确SINR（使用我们的信道模型）
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            rx_power: 接收功率 (dBm)
            
        返回:
            sinr_db: SINR (dB)
        """
        if self.use_fdma:
            # FDMA模式：计算来自其他所有UAV的邻道干扰 (ACI)
            # 简化模型：干扰功率 = 发射功率 * 路径损耗 * ACLR
            # 我们进一步简化，假设所有干扰源的路径损耗对接收机的影响相似，
            # 直接使用 发射功率 * ACLR 作为干扰项。
            interference_powers_linear = []
            
            # 遍历所有其他UAV作为干扰源
            for i in range(self.n_uavs):
                # 排除发送方自身
                if i == uav_idx:
                    continue
                
                # 计算干扰源到用户的路径损耗
                interferer_pos = self.uav_positions[i]
                user_pos_3d = np.append(self.user_positions[user_idx], 0)  # 用户在地面
                interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, user_pos_3d)
                
                # 计算干扰功率：发射功率 - 路径损耗，然后转为线性值，再乘以ACLR
                interferer_rx_power_dbm = self.tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                # 邻道干扰功率 = 接收功率 * ACLR
                interference_powers_linear.append(interferer_rx_power_linear * self.aclr_linear)

            total_interference_linear = np.sum(interference_powers_linear)
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            interference_plus_noise_linear = noise_power_linear + total_interference_linear
            interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
            
            sinr_db = rx_power - interference_plus_noise_dbm
        else:
            # 非FDMA模式：计算来自其他UAV的同频干扰
            interference_powers = []
            user_pos_3d = np.append(self.user_positions[user_idx], 0)  # 用户在地面
            
            for i in range(self.n_uavs):
                if i != uav_idx:  # 排除目标UAV
                    interferer_pos = self.uav_positions[i]
                    # 使用精确的A2G路径损耗模型计算干扰
                    interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, user_pos_3d)
                    interferer_power = self.tx_power - interferer_path_loss
                    interference_powers.append(10 ** (interferer_power / 10))
            
            # 总干扰功率 (所有干扰源的线性叠加)
            total_interference = np.sum(interference_powers) if interference_powers else 0
            total_interference_dbm = 10 * np.log10(total_interference) if total_interference > 0 else -float('inf')
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            if total_interference_dbm != -float('inf'):
                interference_plus_noise = noise_power_linear + total_interference
                interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise)
            else:
                interference_plus_noise_dbm = self.noise_power
            
            sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db
