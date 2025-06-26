import numpy as np
from envs.pettingzoo.uav_env import MultiUAVEnv

class UAVCooperativeNetworkEnv(MultiUAVEnv):
    """
    场景2：无人机协作组网环境
    
    特点：
    - 无人机可根据情况合作组网，分别担任基站以及中继
    - 需要回程到地面基站
    - 跳数最多为3-5可调
    - 优化目标是最大化用户覆盖率和系统吞吐量
    - 多跳路径的容量损失直接体现在吞吐量计算中，无显式惩罚项
    - 奖励函数简化为：覆盖率 + 归一化吞吐量
    """
    
    def __init__(
        self,
        n_uavs=5,
        n_users=50,
        area_size=1000,
        height_range=(50, 150),
        max_speed=30,
        time_step=1.0,
        max_steps=5000,
        user_distribution="uniform",
        channel_model="free_space",
        render_mode=None,
        seed=None,
        min_sinr=0,  # 最小SINR阈值 (dB)
        max_connections=10,  # 每个无人机最大连接数
        max_hops=3,  # 最大跳数 (3-5可调)
        n_ground_bs=1,  # 地面基站数量
        max_observed_uavs=10,  # 最大观测无人机数量
        max_observed_users=20,  # 最大观测用户数量
        use_shadowing=False,  # 是否启用阴影衰落（默认关闭）
        paper_reward=False,  # 是否使用论文中的奖励函数
        use_fdma=True,  # 是否启用FDMA频分多址
        bandwidth=20e6 / 5,  # 每个无人机的带宽 (Hz)，默认为20MHz/5个UAV
    ):
        """
        初始化UAV协作组网环境
        
        特点：
        - 无人机可根据情况合作组网，分别担任基站以及中继
        - 需要回程到地面基站
        - 跳数最多为3-5可调
        - 优化目标是最大化用户覆盖率和系统吞吐量
        - 多跳路径的容量损失直接体现在吞吐量计算中
        
        参数:
            n_uavs: 无人机数量
            n_users: 用户数量
            area_size: 区域大小 (m)
            height_range: 无人机高度范围 (m)
            max_speed: 最大速度 (m/s)
            time_step: 时间步长 (s)
            max_steps: 最大步数
            user_distribution: 用户分布类型 ("uniform", "cluster", "hotspot")
            channel_model: 信道模型 ("free_space", "urban", "suburban")
            render_mode: 渲染模式
            seed: 随机种子
            min_sinr: 最小SINR阈值 (dB)
            max_connections: 每个无人机最大连接数
            max_hops: 最大跳数 (3-5可调)
            n_ground_bs: 地面基站数量
        """
        # 先保存关键参数，防止在父类初始化时就需要使用
        self.n_ground_bs = n_ground_bs
        self.max_hops = max_hops
        self.min_sinr = min_sinr
        self.max_connections = max_connections
        self.area_size = area_size  # 需要在初始化地面基站之前设置
        
        # 初始化地面基站位置（在调用父类初始化之前）
        self._init_ground_bs()
        
        # 调用父类初始化
        super().__init__(
            n_uavs=n_uavs,
            n_users=n_users,
            area_size=area_size,
            height_range=height_range,
            max_speed=max_speed,
            time_step=time_step,
            max_steps=max_steps,
            user_distribution=user_distribution,
            channel_model=channel_model,
            render_mode=render_mode,
            seed=seed,
            max_observed_uavs=max_observed_uavs,
            max_observed_users=max_observed_users,
            use_shadowing=use_shadowing,
            paper_reward=paper_reward,
            use_fdma=use_fdma,
            bandwidth=bandwidth,
        )
        
        # 场景名称
        self.metadata["name"] = "uav_cooperative_network_v0"
        
        # 初始化UAV连接矩阵
        self.uav_connections = np.zeros((self.n_uavs, self.n_uavs), dtype=bool)  # UAV之间的连接
        self.uav_bs_connections = np.zeros((self.n_uavs, self.n_ground_bs), dtype=bool)  # UAV到地面基站的连接
        self.routing_paths = {}  # 路由路径 {uav_idx: [path_to_ground_bs]}
        
        # 扩展观测空间
        self.obs_dim += self.n_ground_bs + 1  # 添加到地面基站的连接(n_ground_bs)和跳数信息(1)
    
    def _init_ground_bs(self):
        """初始化地面基站位置"""
        # 确保总是创建正确数量的地面基站
        self.ground_bs_positions = np.zeros((self.n_ground_bs, 3))
        
        if self.n_ground_bs == 1:
            # 单个地面基站放在中心
            self.ground_bs_positions[0] = [self.area_size/2, self.area_size/2, 30]
        elif self.n_ground_bs == 2:
            # 两个基站分布在对角
            self.ground_bs_positions[0] = [self.area_size * 0.25, self.area_size * 0.25, 30]
            self.ground_bs_positions[1] = [self.area_size * 0.75, self.area_size * 0.75, 30]
        elif self.n_ground_bs == 3:
            # 三个基站三角分布
            self.ground_bs_positions[0] = [self.area_size * 0.5, self.area_size * 0.2, 30]
            self.ground_bs_positions[1] = [self.area_size * 0.2, self.area_size * 0.8, 30]
            self.ground_bs_positions[2] = [self.area_size * 0.8, self.area_size * 0.8, 30]
        elif self.n_ground_bs == 4:
            # 四个角落
            self.ground_bs_positions[0] = [self.area_size * 0.2, self.area_size * 0.2, 30]
            self.ground_bs_positions[1] = [self.area_size * 0.2, self.area_size * 0.8, 30]
            self.ground_bs_positions[2] = [self.area_size * 0.8, self.area_size * 0.2, 30]
            self.ground_bs_positions[3] = [self.area_size * 0.8, self.area_size * 0.8, 30]
        else:
            # 更多地面基站时使用网格或随机分布
            if self.n_ground_bs <= 9:
                # 使用网格分布（最多3x3）
                grid_size = int(np.ceil(np.sqrt(self.n_ground_bs)))
                positions_generated = 0
                
                for i in range(grid_size):
                    for j in range(grid_size):
                        if positions_generated >= self.n_ground_bs:
                            break
                        
                        x = self.area_size * (0.2 + 0.6 * i / max(1, grid_size - 1))
                        y = self.area_size * (0.2 + 0.6 * j / max(1, grid_size - 1))
                        self.ground_bs_positions[positions_generated] = [x, y, 30]
                        positions_generated += 1
                    
                    if positions_generated >= self.n_ground_bs:
                        break
            else:
                # 随机分布
                for i in range(self.n_ground_bs):
                    self.ground_bs_positions[i] = [
                        np.random.uniform(self.area_size * 0.1, self.area_size * 0.9),
                        np.random.uniform(self.area_size * 0.1, self.area_size * 0.9),
                        30  # 固定高度
                    ]
    
    def reset(self, seed=None, options=None):
        """
        重置环境
        
        返回:
            observations: 所有智能体的观测字典
            infos: 所有智能体的信息字典
        """
        # 由于在父类的reset中会用到self.n_ground_bs，我们需要先确保它被正确设置
        # 确保地面基站位置被初始化
        if not hasattr(self, 'ground_bs_positions') or self.ground_bs_positions is None:
            self._init_ground_bs()
            
        # 调用父类的reset
        observations, infos = super().reset(seed, options)
        
        # 重置UAV连接矩阵
        self.uav_connections = np.zeros((self.n_uavs, self.n_uavs), dtype=bool)
        self.uav_bs_connections = np.zeros((self.n_uavs, self.n_ground_bs), dtype=bool)
        self.routing_paths = {}
        
        # 更新UAV连接
        self._update_uav_connections()
        self._compute_routing_paths()
        
        # 更新观测 (使用字典版本)
        observations = self._update_observations_dict(observations)
        
        return observations, infos
    
    
    def _update_observations_dict(self, observations_dict):
        """
        更新观测，添加连接信息（用于字典格式的观测）
        
        参数:
            observations_dict: 原始观测字典
            
        返回:
            updated_observations_dict: 更新后的观测字典
        """
        updated_observations_dict = {}
        
        for i, agent in enumerate(self.agents):
            # 获取原始观测
            obs_dict = observations_dict[agent]
            obs = obs_dict["obs"]
            
            # 添加到地面基站的连接信息
            bs_connections = self.uav_bs_connections[i]
            
            # 添加跳数信息（归一化）
            if i in self.routing_paths:
                hop_count = len(self.routing_paths[i])
                normalized_hop = min(hop_count / self.max_hops, 1.0)
            else:
                normalized_hop = 1.0  # 无路径时设为最大值
            
            # 组合新的观测（不包括角色信息）
            new_obs = np.concatenate([obs, bs_connections, [normalized_hop]])
            
            # 更新观测字典
            updated_obs_dict = {
                "obs": new_obs,
                "action_mask": obs_dict["action_mask"]
            }
            updated_observations_dict[agent] = updated_obs_dict
        
        return updated_observations_dict
    
    def step(self, actions):
        """
        执行环境步骤
        
        参数:
            actions: 所有智能体的动作字典 {agent_id: action}
            
        返回:
            observations: 所有智能体的下一个观测字典
            rewards: 所有智能体的奖励字典
            terminations: 所有智能体的终止状态字典
            truncations: 所有智能体的截断状态字典
            infos: 所有智能体的信息字典
        """
        # 执行父类的step
        observations, rewards, terminations, truncations, infos = super().step(actions)
        
        # 更新UAV连接
        self._update_uav_connections()
        self._compute_routing_paths()
        
        # 更新观测
        observations = self._update_observations_dict(observations)
        
        # 计算新的奖励
        global_reward = self._compute_reward()
        
        # 更新每个智能体的奖励
        for agent in self.agents:
            rewards[agent] = global_reward / self.n_uavs
        
        # 添加场景特定信息到每个智能体的info中
        scenario_info = {
            "scenario": "cooperative_network",
            "reward_info": self.reward_info if hasattr(self, "reward_info") else {},
            "coverage_ratio": np.sum(self.connections) / self.n_users if self.n_users > 0 else 0,  # 避免除零错误
            "connectivity_ratio": self._compute_connectivity_ratio(),
            "routing_paths": {k: v.copy() for k, v in self.routing_paths.items()},
        }
        
        for agent in self.agents:
            infos[agent].update(scenario_info)
        
        return observations, rewards, terminations, truncations, infos
    
    def _update_uav_connections(self):
        """更新UAV之间的连接和UAV到地面基站的连接"""
        # 更新UAV之间的连接
        for i in range(self.n_uavs):
            for j in range(i+1, self.n_uavs):
                # 使用精确的SINR计算（考虑所有其他无人机的干扰）
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
                # 使用精确的SINR计算（考虑所有其他无人机的干扰）
                sinr = self._compute_uav_to_bs_sinr(i, j)
                
                # 如果SINR大于阈值，则建立连接
                if sinr >= self.min_sinr:
                    self.uav_bs_connections[i, j] = True
                else:
                    self.uav_bs_connections[i, j] = False
    
    
    def _find_best_bs_connection(self, uav_idx):
        """
        为给定的UAV找到最佳的地面基站连接（基于距离）
        
        参数:
            uav_idx: 无人机索引
            
        返回:
            best_bs_idx: 最佳基站索引，如果没有可连接的基站则返回None
        """
        available_bs = []
        for bs_idx in range(self.n_ground_bs):
            if self.uav_bs_connections[uav_idx, bs_idx]:
                available_bs.append(bs_idx)
        
        if not available_bs:
            return None
        
        # 如果只有一个可用基站，直接返回
        if len(available_bs) == 1:
            return available_bs[0]
        
        # 计算到每个可用基站的距离，选择最近的
        min_distance = float('inf')
        best_bs_idx = available_bs[0]
        
        uav_pos = self.uav_positions[uav_idx]
        for bs_idx in available_bs:
            bs_pos = self.ground_bs_positions[bs_idx]
            distance = self._compute_distance(uav_pos, bs_pos)
            
            if distance < min_distance:
                min_distance = distance
                best_bs_idx = bs_idx
        
        return best_bs_idx

    def _compute_routing_paths(self):
        """
        计算每个UAV到地面基站的路由路径
        
        使用广度优先搜索找到最短路径，优先选择距离最近的基站
        """
        self.routing_paths = {}
        
        # 对每个UAV计算到地面基站的路径
        for i in range(self.n_uavs):
            # 如果UAV直接连接到地面基站
            if np.any(self.uav_bs_connections[i]):
                # 找到最佳的地面基站连接（距离最近的）
                best_bs_idx = self._find_best_bs_connection(i)
                if best_bs_idx is not None:
                    # 确保路径包含起始UAV节点
                    self.routing_paths[i] = [("uav", i), ("ground_bs", best_bs_idx)]
                continue
            
            # 否则，使用BFS寻找到地面基站的路径
            path = self._bfs_shortest_path(i)
            if path:
                self.routing_paths[i] = path
    
    def _bfs_shortest_path(self, start_uav):
        """
        使用BFS寻找从UAV到地面基站的最短路径，优先选择距离最近的基站
        
        参数:
            start_uav: 起始UAV索引
            
        返回:
            path: 路径列表 [(node_type, node_idx), ...]，如果没有路径则返回None
        """
        # 初始化队列和访问标记
        queue = [(start_uav, [])]  # (当前节点, 路径)
        visited = set([start_uav])
        
        while queue:
            current, path = queue.pop(0)
            
            # 检查是否直接连接到地面基站
            available_bs = []
            for bs_idx in range(self.n_ground_bs):
                if self.uav_bs_connections[current, bs_idx]:
                    available_bs.append(bs_idx)
            
            # 如果找到可连接的基站，选择距离最近的那个
            if available_bs:
                if len(available_bs) == 1:
                    # 只有一个可用基站，直接返回
                    best_bs_idx = available_bs[0]
                else:
                    # 多个可用基站，选择距离最近的
                    min_distance = float('inf')
                    best_bs_idx = available_bs[0]
                    
                    current_uav_pos = self.uav_positions[current]
                    for bs_idx in available_bs:
                        bs_pos = self.ground_bs_positions[bs_idx]
                        distance = self._compute_distance(current_uav_pos, bs_pos)
                        
                        if distance < min_distance:
                            min_distance = distance
                            best_bs_idx = bs_idx
                
                return path + [("uav", current), ("ground_bs", best_bs_idx)]
            
            # 检查连接到的其他UAV
            for next_uav in range(self.n_uavs):
                if self.uav_connections[current, next_uav] and next_uav not in visited:
                    if len(path) >= self.max_hops:
                        continue  # 超过最大跳数限制
                    
                    visited.add(next_uav)
                    queue.append((next_uav, path + [("uav", current)]))
        
        return None  # 没有找到路径
    
    def _compute_uav_to_bs_sinr(self, uav_idx, bs_idx):
        """
        计算无人机到地面基站通信的SINR (Signal to Interference plus Noise Ratio)
        
        参数:
            uav_idx: 无人机索引
            bs_idx: 地面基站索引
            
        返回:
            sinr: SINR值 (dB)
        """
        uav_pos = self.uav_positions[uav_idx]
        bs_pos = self.ground_bs_positions[bs_idx]
        
        # 计算路径损耗（使用无人机到地面基站的路径损耗计算）
        path_loss = self._compute_uav_path_loss(uav_pos, bs_pos)
        
        # 计算接收功率 (dBm) - 地面基站发射功率更高
        rx_power = self.ground_bs_tx_power - path_loss
        
        # 如果启用理想的FDMA，则SINR = SNR（无干扰）
        if self.use_fdma:
            # FDMA模式：无干扰，SINR = 接收功率 - 噪声功率
            sinr = rx_power - self.noise_power
        else:
            # 原始模式：计算干扰功率：来自所有其他无人机的干扰
            interference_power = []
            for i in range(self.n_uavs):
                if i != uav_idx:  # 排除目标无人机
                    interferer_pos = self.uav_positions[i]
                    interferer_path_loss = self._compute_uav_path_loss(interferer_pos, bs_pos)
                    interferer_power = self.tx_power - interferer_path_loss
                    interference_power.append(10 ** (interferer_power / 10))  # 转换为线性单位
            
            # 总干扰功率 (dBm)
            total_interference = np.sum(interference_power) if interference_power else 0
            total_interference_dbm = 10 * np.log10(total_interference) if total_interference > 0 else -float('inf')
            
            # 计算SINR (dB)
            noise_power_dbm = self.noise_power
            interference_plus_noise_dbm = 10 * np.log10(10 ** (noise_power_dbm / 10) + 10 ** (total_interference_dbm / 10)) if total_interference_dbm != -float('inf') else noise_power_dbm
            
            sinr = rx_power - interference_plus_noise_dbm
        
        return sinr
    
    def _compute_connectivity_ratio(self):
        """
        计算网络连通性比率
        
        返回:
            connectivity_ratio: 连通性比率 [0,1]
        """
        # 计算有效路由的UAV数量
        if hasattr(self, 'routing_paths'):
            connected_uavs = len(self.routing_paths)
        else:
            connected_uavs = 0
        
        # 计算连通性比率
        connectivity_ratio = connected_uavs / self.n_uavs
        
        return connectivity_ratio
    
    def _compute_throughput(self, uav_idx, user_idx):
        """
        计算UAV-用户连接的吞吐量 (bps) - 【已弃用，仅用于兼容性】
        
        注意：此函数假设用户独占全部带宽，不适合多用户场景
        仅用于兼容性，实际计算应使用 _compute_user_throughput_with_sharing
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            
        返回:
            throughput: 吞吐量 (bps)
        """
        if not self.connections[uav_idx, user_idx]:
            return 0
        
        # 获取SINR (dB)
        sinr_db = self.sinr_matrix[uav_idx, user_idx]
        
        # 转换为线性单位
        sinr_linear = 10 ** (sinr_db / 10)
        
        # 香农定理计算吞吐量: C = B * log2(1 + SINR_linear)
        throughput = self.bandwidth * np.log2(1 + sinr_linear)
        
        return throughput  # 单位：bps
    
    def _compute_user_throughput_with_sharing(self, uav_idx, user_idx):
        """
        计算考虑带宽共享的单用户吞吐量 (bps)
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            
        返回:
            user_throughput: 该用户的实际吞吐量 (bps)
        """
        if not self.connections[uav_idx, user_idx]:
            return 0
        
        # 获取连接到该UAV的所有用户
        connected_users = []
        for j in range(self.n_users):
            if self.connections[uav_idx, j]:
                connected_users.append(j)
        
        if len(connected_users) == 0:
            return 0
        
        # 计算UAV的前端总容量
        total_frontend_capacity = self._compute_uav_frontend_capacity(uav_idx, connected_users)
        
        # 方法1: 按SINR比例分配带宽
        # 计算所有连接用户的SINR权重
        sinr_weights = []
        total_sinr_weight = 0
        
        for user in connected_users:
            sinr_db = self.sinr_matrix[uav_idx, user]
            sinr_linear = 10 ** (sinr_db / 10)
            sinr_weights.append(sinr_linear)
            total_sinr_weight += sinr_linear
        
        # 找到目标用户在列表中的位置
        try:
            user_position = connected_users.index(user_idx)
            user_sinr_weight = sinr_weights[user_position]
        except ValueError:
            return 0  # 用户不在连接列表中
        
        if total_sinr_weight == 0:
            return 0
        
        # 按SINR权重分配总容量
        user_throughput = total_frontend_capacity * (user_sinr_weight / total_sinr_weight)
        
        return user_throughput
    
    def _compute_backhaul_capacity(self, uav_idx):
        """
        计算UAV的回程容量
        
        参数:
            uav_idx: 无人机索引
            
        返回:
            backhaul_capacity: 回程容量 (bps)
        """
        if uav_idx not in self.routing_paths:
            return 0
        
        path = self.routing_paths[uav_idx]
        if not path:
            return 0
        
        # 如果直接连接到地面基站
        if len(path) == 1 and path[0][0] == "ground_bs":
            # 使用UAV到地面基站的链路容量
            bs_idx = path[0][1]
            distance = self._compute_distance(self.uav_positions[uav_idx], self.ground_bs_positions[bs_idx])
            safe_distance = max(distance, 1e-6)
            path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi * self.carrier_frequency / 3e8)
            rx_power = self.ground_bs_tx_power - path_loss
            sinr_db = rx_power - self.noise_power
            sinr_linear = 10 ** (sinr_db / 10)
            backhaul_capacity = self.bandwidth * np.log2(1 + sinr_linear)
        else:
            # 多跳路径，需要找到瓶颈链路
            min_capacity = float('inf')
            
            # 计算路径上每一跳的容量
            for i in range(len(path) - 1):
                current_node = path[i]
                next_node = path[i + 1]
                
                if current_node[0] == "uav" and next_node[0] == "uav":
                    # UAV到UAV的链路
                    uav1_idx = current_node[1]
                    uav2_idx = next_node[1]
                    
                    distance = self._compute_distance(self.uav_positions[uav1_idx], self.uav_positions[uav2_idx])
                    safe_distance = max(distance, 1e-6)
                    path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi * self.carrier_frequency / 3e8)
                    rx_power = self.tx_power - path_loss
                    sinr_db = rx_power - self.noise_power
                    sinr_linear = 10 ** (sinr_db / 10)
                    link_capacity = self.bandwidth * np.log2(1 + sinr_linear)
                    
                elif current_node[0] == "uav" and next_node[0] == "ground_bs":
                    # UAV到地面基站的链路
                    uav_idx_link = current_node[1]
                    bs_idx = next_node[1]
                    
                    distance = self._compute_distance(self.uav_positions[uav_idx_link], self.ground_bs_positions[bs_idx])
                    safe_distance = max(distance, 1e-6)
                    path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi * self.carrier_frequency / 3e8)
                    rx_power = self.ground_bs_tx_power - path_loss
                    sinr_db = rx_power - self.noise_power
                    sinr_linear = 10 ** (sinr_db / 10)
                    link_capacity = self.bandwidth * np.log2(1 + sinr_linear)
                else:
                    link_capacity = self.bandwidth  # 默认值
                
                min_capacity = min(min_capacity, link_capacity)
            
            backhaul_capacity = min_capacity if min_capacity != float('inf') else 0
        
        return backhaul_capacity
    
    def _compute_effective_throughput(self, uav_idx, user_idx):
        """
        计算考虑多跳路径的有效吞吐量（使用带宽共享的新方法）
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            
        返回:
            effective_throughput: 有效吞吐量 (bps)
        """
        if not self.connections[uav_idx, user_idx]:
            return 0
        
        # 使用新的带宽共享方法计算基础吞吐量
        base_throughput = self._compute_user_throughput_with_sharing(uav_idx, user_idx)
        
        # 如果UAV有到地面基站的路径，考虑回程瓶颈
        if uav_idx in self.routing_paths:
            path = self.routing_paths[uav_idx]
            hop_count = len(path)
            
            # 多跳效率损失：每一跳都会降低有效吞吐量
            hop_efficiency = 1.0 / hop_count if hop_count > 0 else 0
            
            # 考虑回程链路容量限制
            backhaul_capacity = self._compute_backhaul_capacity(uav_idx)
            
            # 有效吞吐量取最小值（瓶颈原则）
            adjusted_throughput = base_throughput * hop_efficiency
            effective_throughput = min(adjusted_throughput, backhaul_capacity)
        else:
            # 无路径到地面基站，吞吐量为0
            effective_throughput = 0
        
        return effective_throughput
    
    def _compute_uav_frontend_capacity(self, uav_idx, connected_users):
        """
        计算UAV的前端总容量（考虑带宽共享）
        
        参数:
            uav_idx: 无人机索引
            connected_users: 连接到该UAV的用户索引列表
            
        返回:
            frontend_capacity: 前端总容量 (bps)
        """
        if len(connected_users) == 0:
            return 0
        
        # 方法1：基于最差用户的SINR来计算总容量
        # 这假设UAV使用相同的功率向所有用户广播
        min_sinr_db = float('inf')
        for user_idx in connected_users:
            sinr_db = self.sinr_matrix[uav_idx, user_idx]
            min_sinr_db = min(min_sinr_db, sinr_db)
        
        if min_sinr_db == float('inf'):
            return 0
        
        # 使用最差SINR和全部带宽计算总容量
        min_sinr_linear = 10 ** (min_sinr_db / 10)
        total_capacity = self.bandwidth * np.log2(1 + min_sinr_linear)
        
        return total_capacity
    
    def _compute_realistic_max_throughput(self):
        """
        计算考虑系统瓶颈的现实最大吞吐量
        
        返回:
            max_realistic_throughput: 现实最大系统吞吐量 (bps)
        """
        max_system_throughput = 0
        
        for i in range(self.n_uavs):
            # 计算UAV的理论最大前端容量（单UAV在最优SINR下的总容量）
            max_sinr_linear = 10 ** (30 / 10)  # 30dB转换为线性
            max_frontend_capacity = self.bandwidth * np.log2(1 + max_sinr_linear)
            
            # 计算UAV的理论最大回程容量（直连最近地面基站的情况）
            if len(self.ground_bs_positions) > 0:
                min_distance_to_bs = min([
                    self._compute_distance(self.uav_positions[i], bs_pos) 
                    for bs_pos in self.ground_bs_positions
                ])
                safe_distance = max(min_distance_to_bs, 1e-6)
                path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi * self.carrier_frequency / 3e8)
                rx_power = self.ground_bs_tx_power - path_loss
                sinr_db = rx_power - self.noise_power
                sinr_linear = 10 ** (sinr_db / 10)
                max_backhaul_capacity = self.bandwidth * np.log2(1 + sinr_linear)
            else:
                max_backhaul_capacity = max_frontend_capacity  # 没有地面基站时使用前端容量
            
            # UAV的实际最大吞吐量 = min(前端容量, 回程容量)
            uav_max_throughput = min(max_frontend_capacity, max_backhaul_capacity)
            max_system_throughput += uav_max_throughput
        
        return max_system_throughput
    
    def _compute_reward(self):
        """
        计算简化的覆盖率+吞吐量奖励
        
        在理想FDMA模型下，前端和回程使用不同频率，因此系统吞吐量只由前端容量决定
        
        返回:
            reward: 全局奖励
        """
        # 覆盖率奖励：已连接用户数比例
        connected_users = np.sum(self.connections)
        coverage_reward = connected_users / self.n_users
        
        # 系统吞吐量计算（理想FDMA下只考虑前端容量）
        system_throughput = 0
        
        # 按UAV计算有效吞吐量
        for i in range(self.n_uavs):
            # 获取连接到该UAV的用户列表
            connected_users_to_uav = []
            for j in range(self.n_users):
                if self.connections[i, j]:
                    connected_users_to_uav.append(j)
            
            if len(connected_users_to_uav) == 0:
                continue  # 该UAV没有连接用户
            
            # 在理想FDMA模型下，只有当UAV有回程路径时，其前端容量才有效
            if i in self.routing_paths:
                # 计算该UAV的前端总容量（考虑带宽共享）
                uav_frontend_capacity = self._compute_uav_frontend_capacity(i, connected_users_to_uav)
                
                # 在理想FDMA下，前端和回程使用不同频率，因此系统吞吐量 = 前端容量
                uav_effective_throughput = uav_frontend_capacity
            else:
                # 无回程路径，吞吐量为0（无法将数据传输到核心网络）
                uav_effective_throughput = 0
            
            # 累加到系统总吞吐量
            system_throughput += uav_effective_throughput
        
        # 归一化吞吐量奖励
        max_realistic_throughput = self._compute_realistic_max_throughput()
        throughput_reward = system_throughput / max_realistic_throughput if max_realistic_throughput > 0 else 0
        
        # 简化的奖励组合：覆盖率 + 吞吐量
        raw_reward = coverage_reward + throughput_reward
        
        # 将奖励映射到[0, 1]范围
        # 理论最大值: 1.0 (覆盖率) + 1.0 (吞吐量) = 2.0
        # 因此将[0, 2.0]映射到[0, 1]
        normalized_reward = np.clip(raw_reward / 2.0, 0, 1)
        
        # 记录奖励组成信息
        self.reward_info = {
            "coverage_reward": coverage_reward,
            "throughput_reward": throughput_reward,
            "raw_reward": raw_reward,
            "normalized_reward": normalized_reward,
            "system_throughput_mbps": system_throughput / 1e6,
            "avg_throughput_per_user_mbps": (system_throughput / max(connected_users, 1)) / 1e6,
            "max_realistic_throughput_mbps": max_realistic_throughput / 1e6,
            "connected_users": connected_users,
            "coverage_ratio": coverage_reward,
            "avg_hops": sum(len(path) - 1 for path in self.routing_paths.values()) / max(len(self.routing_paths), 1)
        }
        
        return normalized_reward
    
    def _render_frame(self):
        """渲染单帧"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            print("渲染需要matplotlib库")
            return None
        
        # 调用父类的渲染方法
        frame = super()._render_frame()
        
        # 添加UAV之间的连接和UAV到地面基站的连接
        if hasattr(self, 'uav_connections') and hasattr(self, 'uav_bs_connections'):
            for i in range(self.n_uavs):
                uav_pos_i = self.uav_positions[i]
                
                # 绘制UAV之间的连接
                for j in range(i+1, self.n_uavs):
                    if self.uav_connections[i, j]:
                        uav_pos_j = self.uav_positions[j]
                        self.ax.plot([uav_pos_i[0], uav_pos_j[0]], 
                                    [uav_pos_i[1], uav_pos_j[1]], 
                                    [uav_pos_i[2], uav_pos_j[2]], 
                                    'y-', alpha=0.5, linewidth=1.5)
                
                # 绘制UAV到地面基站的连接
                for j in range(self.n_ground_bs):
                    if self.uav_bs_connections[i, j]:
                        bs_pos = self.ground_bs_positions[j]
                        self.ax.plot([uav_pos_i[0], bs_pos[0]], 
                                    [uav_pos_i[1], bs_pos[1]], 
                                    [uav_pos_i[2], bs_pos[2]], 
                                    'c-', alpha=0.7, linewidth=2.0)
        
        # 添加连通性信息
        connectivity_ratio = self._compute_connectivity_ratio()
        self.ax.text2D(0.02, 0.90, f'网络连通性: {connectivity_ratio:.2%}', transform=self.ax.transAxes)
        
        # 添加吞吐量信息
        if hasattr(self, 'reward_info') and 'total_throughput_mbps' in self.reward_info:
            total_throughput_mbps = self.reward_info['total_throughput_mbps']
            avg_throughput_mbps = self.reward_info['avg_throughput_per_user_mbps']
            self.ax.text2D(0.02, 0.80, f'总吞吐量: {total_throughput_mbps:.1f} Mbps', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.75, f'平均用户吞吐量: {avg_throughput_mbps:.1f} Mbps', 
                          transform=self.ax.transAxes)
        
        self.fig.canvas.draw()
        
        return frame
