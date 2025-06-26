import numpy as np
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv

class UAVMultiHopEnv(UAVCooperativeNetworkEnv):
    """
    场景3：无人机强制多跳环境
    
    特点：
    - 地面基站放置在区域四个角落，距离用户群体很远
    - 用户采用多个cluster分布，cluster中心远离地面基站
    - 强制需要无人机多跳中继才能连接到地面基站
    - 测试复杂的多跳路由和协作策略
    """
    
    def __init__(
        self,
        n_uavs=20,
        n_users=150,
        area_size=3000,
        height_range=(50, 200),
        max_speed=30,
        time_step=1.0,
        max_steps=5000,
        user_distribution="multi_cluster",
        channel_model="free_space",
        render_mode=None,
        seed=None,
        min_sinr=0,  # 最小SINR阈值 (dB)
        max_connections=15,  # 每个无人机最大连接数（增加以支持更多用户）
        max_hops=5,  # 最大跳数
        effective_coverage_weight=0.45,  # 有效覆盖率权重（增强）
        throughput_weight=0.25,  # 系统吞吐量权重
        load_balance_weight=0.2,  # 负载均衡权重
        network_connectivity_weight=0.0,  # 网络连通性权重（移除）
        proximity_penalty_weight=0.1,  # 邻近惩罚权重 (新增)
        n_ground_bs=4,  # 地面基站数量（四个角落）
        n_clusters=7,  # 用户簇数量
        cluster_std=150,  # 簇内用户分布标准差（米）
        central_area_ratio=0.5,  # 中心用户区域占总区域的比例
        max_observed_uavs=10,  # 最大观测无人机数量
        max_observed_users=20,  # 最大观测用户数量
        use_shadowing=False,  # 是否启用阴影衰落（默认关闭）
        paper_reward=False,  # 是否使用论文中的奖励函数
        use_fdma=True,  # 是否启用FDMA频分多址
        bandwidth=20e6 / 5,  # 每个无人机的带宽 (Hz)，默认为20MHz/5个UAV
    ):
        """
        初始化UAV强制多跳环境
        
        参数:
            n_uavs: 无人机数量
            n_users: 用户数量
            area_size: 区域大小 (m)
            height_range: 无人机高度范围 (m)
            max_speed: 最大速度 (m/s)
            time_step: 时间步长 (s)
            max_steps: 最大步数
            user_distribution: 用户分布类型
            channel_model: 信道模型
            render_mode: 渲染模式
            seed: 随机种子
            min_sinr: 最小SINR阈值 (dB)
            max_connections: 每个无人机最大连接数
            max_hops: 最大跳数
            effective_coverage_weight: 有效覆盖率权重
            throughput_weight: 系统吞吐量权重
            load_balance_weight: 负载均衡权重
            network_connectivity_weight: 网络连通性权重
            n_ground_bs: 地面基站数量
            n_clusters: 用户簇数量
            cluster_std: 簇内用户分布标准差（米）
            central_area_ratio: 中心用户区域占总区域的比例
        """
        # 保存多跳环境特有的参数
        self.n_clusters = n_clusters
        self.cluster_std = cluster_std
        self.central_area_ratio = central_area_ratio
        
        # 保存新的奖励权重
        self.effective_coverage_weight = effective_coverage_weight
        self.throughput_weight = throughput_weight
        self.load_balance_weight = load_balance_weight
        self.network_connectivity_weight = network_connectivity_weight
        self.proximity_penalty_weight = proximity_penalty_weight
        
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
            min_sinr=min_sinr,
            max_connections=max_connections,
            max_hops=max_hops,
            n_ground_bs=n_ground_bs,
            max_observed_uavs=max_observed_uavs,
            max_observed_users=max_observed_users,
            use_shadowing=use_shadowing,
            paper_reward=paper_reward,
            use_fdma=use_fdma,
            bandwidth=bandwidth,
        )
        
        # 场景名称
        self.metadata["name"] = "uav_multihop_env_v0"
    
    def _init_ground_bs(self):
        """初始化地面基站位置 - 放置在四个角落"""
        self.ground_bs_positions = np.zeros((self.n_ground_bs, 3))
        
        # 距离边界的偏移量
        offset = self.area_size * 0.05  # 距离边界5%的距离
        
        if self.n_ground_bs >= 1:
            # 左下角
            self.ground_bs_positions[0] = [offset, offset, 30]
        
        if self.n_ground_bs >= 2:
            # 右下角
            self.ground_bs_positions[1] = [self.area_size - offset, offset, 30]
        
        if self.n_ground_bs >= 3:
            # 左上角
            self.ground_bs_positions[2] = [offset, self.area_size - offset, 30]
        
        if self.n_ground_bs >= 4:
            # 右上角
            self.ground_bs_positions[3] = [self.area_size - offset, self.area_size - offset, 30]
        
        # 如果有更多基站，随机分布在边界附近
        for i in range(4, self.n_ground_bs):
            # 随机选择一个边界
            edge = np.random.randint(0, 4)
            
            if edge == 0:  # 下边界
                x = np.random.uniform(offset, self.area_size - offset)
                y = offset
            elif edge == 1:  # 右边界
                x = self.area_size - offset
                y = np.random.uniform(offset, self.area_size - offset)
            elif edge == 2:  # 上边界
                x = np.random.uniform(offset, self.area_size - offset)
                y = self.area_size - offset
            else:  # 左边界
                x = offset
                y = np.random.uniform(offset, self.area_size - offset)
            
            self.ground_bs_positions[i] = [x, y, 30]
    
    def _generate_user_positions(self):
        """
        生成多簇用户分布 - 符合移动通信默认分布
        
        返回:
            user_positions: 用户位置 [n_users, 2]
        """
        if self.user_distribution == "multi_cluster":
            return self._generate_multi_cluster_positions()
        else:
            # 如果指定了其他分布类型，调用父类方法
            return super()._generate_user_positions()
    
    def _generate_multi_cluster_positions(self):
        """
        生成多簇用户分布
        
        基于泊松簇过程的思想，在中心区域生成多个用户簇
        
        返回:
            user_positions: 用户位置 [n_users, 2]
        """
        user_positions = np.zeros((self.n_users, 2))
        
        # 定义中心区域的边界
        central_size = self.area_size * self.central_area_ratio
        central_margin = (self.area_size - central_size) / 2
        
        # 生成簇中心位置
        cluster_centers = np.zeros((self.n_clusters, 2))
        
        # 使用网格+随机扰动的方式生成簇中心，确保分布相对均匀
        grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
        cluster_idx = 0
        
        for i in range(grid_size):
            for j in range(grid_size):
                if cluster_idx >= self.n_clusters:
                    break
                
                # 网格位置
                grid_x = central_margin + central_size * (i + 0.5) / grid_size
                grid_y = central_margin + central_size * (j + 0.5) / grid_size
                
                # 添加随机扰动
                jitter_range = central_size / (grid_size * 3)  # 扰动范围
                jitter_x = self.np_random.uniform(-jitter_range, jitter_range)
                jitter_y = self.np_random.uniform(-jitter_range, jitter_range)
                
                cluster_centers[cluster_idx] = [
                    np.clip(grid_x + jitter_x, central_margin, central_margin + central_size),
                    np.clip(grid_y + jitter_y, central_margin, central_margin + central_size)
                ]
                
                cluster_idx += 1
            
            if cluster_idx >= self.n_clusters:
                break
        
        # 计算每个簇的用户数量
        users_per_cluster = self.n_users // self.n_clusters
        remaining_users = self.n_users % self.n_clusters
        
        cluster_user_counts = [users_per_cluster] * self.n_clusters
        # 将剩余用户随机分配给一些簇
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
                user_position[0] = np.clip(user_position[0], 0, self.area_size)
                user_position[1] = np.clip(user_position[1], 0, self.area_size)
                
                user_positions[user_idx] = user_position
                user_idx += 1
        
        return user_positions
    
    def _compute_reward(self):
        """
        计算专为多跳场景设计的奖励函数
        
        奖励由四个部分组成：
        1. 有效覆盖率奖励：只计算连接到有回程路径的UAV的用户（权重增强）
        2. 系统吞吐量奖励：使用scenario2中成熟的吞吐量计算
        3. 负载均衡奖励：衡量UAV负载分布的均衡性
        4. 邻近惩罚项：防止UAV过于靠近导致信号干扰
        
        返回:
            reward: 全局奖励 [0, 1]
        """
        
        # 1. 有效覆盖率奖励：只计算连接到有有效回程路径的UAV的用户
        effective_connected_users = 0
        
        for i in range(self.n_uavs):
            # 只有当UAV有到地面基站的路径时，其连接的用户才算有效
            if i in self.routing_paths and self.routing_paths[i]:
                effective_connected_users += np.sum(self.connections[i])
        
        effective_coverage_reward = effective_connected_users / self.n_users if self.n_users > 0 else 0
        
        # 2. 系统吞吐量奖励：在理想FDMA模型下只考虑前端容量
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
        
        # 3. 负载均衡奖励：衡量UAV负载分布的均衡性
        uav_loads = []
        
        for i in range(self.n_uavs):
            # 计算每个UAV的负载（直接服务的用户数 + 中继的数据量）
            direct_load = np.sum(self.connections[i])  # 直接连接的用户数
            
            # 计算作为中继的负载
            relay_load = 0
            for j in range(self.n_uavs):
                if j != i and j in self.routing_paths:
                    path = self.routing_paths[j]
                    # 检查当前UAV是否在其他UAV的路径中作为中继
                    for node_type, node_idx in path:
                        if node_type == "uav" and node_idx == i:
                            # 中继负载 = 该路径对应的UAV服务的用户数
                            relay_load += np.sum(self.connections[j])
                            break
            
            # 总负载 = 直接负载 + 中继负载 * 权重
            total_load = direct_load + relay_load * 0.3  # 中继负载权重较小
            uav_loads.append(total_load)
        
        # 计算负载均衡度：使用基尼系数的逆来衡量均衡性
        if len(uav_loads) > 1 and sum(uav_loads) > 0:
            # 计算基尼系数
            sorted_loads = sorted(uav_loads)
            n = len(sorted_loads)
            cumsum = np.cumsum(sorted_loads)
            total_load = cumsum[-1]
            
            if total_load > 0:
                gini = (2 * sum((i + 1) * load for i, load in enumerate(sorted_loads))) / (n * total_load) - (n + 1) / n
                load_balance_reward = max(0, 1 - gini)  # 基尼系数越小，均衡性越好
            else:
                load_balance_reward = 1  # 无负载时认为完全均衡
        else:
            load_balance_reward = 1  # 只有一个UAV或无负载时认为完全均衡
        
        # 4. 网络连通性奖励：拥有有效回程路径的UAV比例
        connected_uavs = len(self.routing_paths)
        network_connectivity_reward = connected_uavs / self.n_uavs if self.n_uavs > 0 else 0
        
        # 5. 邻近惩罚项：防止UAV过于靠近导致信号干扰
        proximity_penalty = 0
        min_safe_distance = 150  # 无人机之间的最小安全距离 (米)，可根据场景调整
        num_pairs = 0
        
        for i in range(self.n_uavs):
            for j in range(i + 1, self.n_uavs):
                distance = self._compute_distance(self.uav_positions[i], self.uav_positions[j])
                if distance < min_safe_distance:
                    # 距离越近，惩罚越大（线性递减）
                    proximity_penalty += (1 - (distance / min_safe_distance))
                num_pairs += 1
        
        # 归一化邻近惩罚（除以总的UAV对数）
        normalized_proximity_penalty = proximity_penalty / num_pairs if num_pairs > 0 else 0
        
        # 组合最终奖励 (减去惩罚项，移除连通性奖励)
        final_reward = (
            self.effective_coverage_weight * effective_coverage_reward +
            self.throughput_weight * throughput_reward +
            self.load_balance_weight * load_balance_reward -
            self.proximity_penalty_weight * normalized_proximity_penalty  # 减去惩罚
        )
        
        # 确保奖励在[0, 1]范围内
        final_reward = np.clip(final_reward, 0, 1)
        
        # 计算一些统计信息
        total_hops = sum(len(path) - 1 for path in self.routing_paths.values())
        avg_hops = total_hops / max(len(self.routing_paths), 1)
        
        # 更新奖励信息用于调试和可视化
        self.reward_info = {
            "effective_coverage_reward": effective_coverage_reward,
            "throughput_reward": throughput_reward,
            "load_balance_reward": load_balance_reward,
            "network_connectivity_reward": network_connectivity_reward,
            "proximity_penalty": normalized_proximity_penalty,  # 新增：邻近惩罚值
            "final_reward": final_reward,
            "effective_connected_users": effective_connected_users,
            "total_connected_users": np.sum(self.connections),
            "system_throughput_mbps": system_throughput / 1e6,
            "max_realistic_throughput_mbps": max_realistic_throughput / 1e6,
            "avg_hops": avg_hops,
            "connected_uavs": connected_uavs,
            "total_uavs": self.n_uavs,
            "coverage_efficiency": effective_coverage_reward / max(np.sum(self.connections) / self.n_users, 1e-6),
        }
        
        return final_reward
    
    def _render_frame(self):
        """渲染单帧 - 添加多跳特定的可视化元素"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.patches import Circle
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            print("渲染需要matplotlib库")
            return None
        
        # 调用父类的渲染方法
        frame = super()._render_frame()
        
        # 添加用户簇的可视化
        if hasattr(self, 'user_positions'):
            # 绘制簇的边界（半透明圆圈）
            cluster_centers = self._get_cluster_centers()
            
            for center in cluster_centers:
                # 在地面绘制簇的范围
                circle = Circle(
                    (center[0], center[1]), 
                    self.cluster_std * 2,  # 2倍标准差作为可视化半径
                    fill=False, 
                    edgecolor='cyan', 
                    alpha=0.3, 
                    linestyle='--'
                )
                # 注意：3D绘图中需要特殊处理2D圆圈
                # 这里简化处理，仅在文本中显示簇信息
        
        # 添加多跳统计信息
        if hasattr(self, 'reward_info'):
            reward_info = self.reward_info
            self.ax.text2D(0.02, 0.80, f'有效覆盖率: {reward_info.get("effective_coverage_reward", 0):.3f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.75, f'吞吐量奖励: {reward_info.get("throughput_reward", 0):.3f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.70, f'负载均衡: {reward_info.get("load_balance_reward", 0):.3f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.65, f'网络连通性: {reward_info.get("network_connectivity_reward", 0):.3f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.60, f'邻近惩罚: {reward_info.get("proximity_penalty", 0):.3f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.55, f'平均跳数: {reward_info.get("avg_hops", 0):.1f}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.50, f'有效用户: {reward_info.get("effective_connected_users", 0)}/{self.n_users}', 
                          transform=self.ax.transAxes)
            self.ax.text2D(0.02, 0.45, f'连通UAV: {reward_info.get("connected_uavs", 0)}/{self.n_uavs}', 
                          transform=self.ax.transAxes)
        
        self.fig.canvas.draw()
        
        return frame
    
    def _get_cluster_centers(self):
        """
        获取用户簇的中心位置（用于可视化）
        
        返回:
            cluster_centers: 簇中心位置列表
        """
        if not hasattr(self, 'user_positions') or self.user_positions is None:
            return []
        
        # 使用K-means聚类来识别用户簇的中心
        try:
            from sklearn.cluster import KMeans
            
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            kmeans.fit(self.user_positions)
            return kmeans.cluster_centers_
            
        except ImportError:
            # 如果没有sklearn，使用简单的网格估计
            central_size = self.area_size * self.central_area_ratio
            central_margin = (self.area_size - central_size) / 2
            
            grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
            cluster_centers = []
            
            cluster_idx = 0
            for i in range(grid_size):
                for j in range(grid_size):
                    if cluster_idx >= self.n_clusters:
                        break
                    
                    grid_x = central_margin + central_size * (i + 0.5) / grid_size
                    grid_y = central_margin + central_size * (j + 0.5) / grid_size
                    
                    cluster_centers.append([grid_x, grid_y])
                    cluster_idx += 1
                
                if cluster_idx >= self.n_clusters:
                    break
            
            return cluster_centers
    
    def get_scenario_info(self):
        """
        获取场景特定信息
        
        返回:
            info: 场景信息字典
        """
        info = {
            "scenario_name": "multi_hop",
            "scenario_description": "强制多跳无人机网络环境",
            "area_size": self.area_size,
            "n_ground_bs": self.n_ground_bs,
            "ground_bs_positions": self.ground_bs_positions.tolist() if hasattr(self, 'ground_bs_positions') else [],
            "n_clusters": self.n_clusters,
            "cluster_std": self.cluster_std,
            "central_area_ratio": self.central_area_ratio,
            "max_hops": self.max_hops,
            "min_distance_to_bs": self._compute_min_distance_to_bs(),
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
