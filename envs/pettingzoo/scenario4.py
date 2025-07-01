import numpy as np
import heapq
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv

class UAVForcedRelayEnv(UAVCooperativeNetworkEnv):
    """
    场景4：强制多跳中继无人机环境
    
    特点：
    - 专为强制协作设计的拓扑结构
    - 地面基站距离用户群体很远，强制要求多跳中继
    - 优化的用户分布，便于实现90%以上覆盖率
    - 重点激励用户覆盖率，简化奖励机制
    - 所有无人机地位平等，通过算法自主选择行为
    """
    
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
        min_sinr=3,  # 降低SINR门槛便于建立连接
        max_connections=25,  # 增加连接数上限
        max_hops=4,  # 允许最多4跳
        coverage_weight=0.8,  # 覆盖率权重80%
        connectivity_weight=0.15,  # 网络连通性权重15%
        efficiency_weight=0.05,  # 路径效率权重5%
        n_ground_bs=2,  # 2个地面基站
        n_clusters=4,  # 4个用户簇
        cluster_std=80,  # 簇内用户分布标准差（米）
        central_area_ratio=0.6,  # 中心用户区域占总区域的比例
        base_station_distance_factor=0.8,  # 基站距离因子
        uav_communication_range=600,  # 无人机通信范围
        max_observed_uavs=15,  # 最大观测无人机数量
        max_observed_users=25,  # 最大观测用户数量
        use_shadowing=False,  # 是否启用阴影衰落（默认关闭）
        paper_reward=False,  # 是否使用论文中的奖励函数
        use_fdma=True,  # 是否启用FDMA频分多址
        bandwidth=20e6,  # 每个无人机的带宽 (Hz)，默认为20MHz
        ground_bs_tx_power=30,  # 地面基站发射功率 (dBm)
    ):
        """
        初始化UAV强制中继环境
        
        参数:
            n_uavs: 无人机数量（推荐12架）
            n_users: 用户数量（推荐80个）
            area_size: 区域大小 (m)（推荐2500m）
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
            coverage_weight: 覆盖率权重
            connectivity_weight: 网络连通性权重
            efficiency_weight: 路径效率权重
            n_ground_bs: 地面基站数量
            n_clusters: 用户簇数量
            cluster_std: 簇内用户分布标准差（米）
            central_area_ratio: 中心用户区域占总区域的比例
            base_station_distance_factor: 基站距离因子
            uav_communication_range: 无人机通信范围
        """
        # 保存场景4特有的参数
        self.n_clusters = n_clusters
        self.cluster_std = cluster_std
        self.central_area_ratio = central_area_ratio
        self.base_station_distance_factor = base_station_distance_factor
        self.uav_communication_range = uav_communication_range
        
        # 保存奖励权重
        self.coverage_weight = coverage_weight
        self.connectivity_weight = connectivity_weight
        self.efficiency_weight = efficiency_weight
        
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
            ground_bs_tx_power=ground_bs_tx_power,
        )
        
        # 场景名称
        self.metadata["name"] = "uav_forced_relay_env_v0"
    
    def _init_ground_bs(self):
        """初始化地面基站位置 - 强制多跳的关键设计"""
        self.ground_bs_positions = np.zeros((self.n_ground_bs, 3))
        
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
                    x = np.random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                    y = self.area_size * 0.05
                elif edge == 1:  # 右边界
                    x = self.area_size * 0.95
                    y = np.random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                elif edge == 2:  # 上边界
                    x = np.random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                    y = self.area_size * 0.95
                else:  # 左边界
                    x = self.area_size * 0.05
                    y = np.random.uniform(self.area_size * 0.1, self.area_size * 0.9)
                
                self.ground_bs_positions[i] = [x, y, 30]
    
    def _generate_user_positions(self):
        """
        生成针对强制中继优化的用户分布
        
        返回:
            user_positions: 用户位置 [n_users, 2]
        """
        if self.user_distribution == "forced_relay_cluster":
            return self._generate_forced_relay_cluster_positions()
        else:
            # 如果指定了其他分布类型，调用父类方法
            return super()._generate_user_positions()
    
    def _generate_forced_relay_cluster_positions(self):
        """
        生成针对强制中继优化的用户簇分布
        
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
        
        # 生成簇中心位置 - 采用更规整的布局
        cluster_centers = np.zeros((self.n_clusters, 2))
        
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
    
    def _compute_reward(self):
        """
        计算针对强制中继优化的奖励函数
        
        重点：
        1. 用户覆盖率奖励（权重80%）
        2. 网络连通性奖励（权重15%）
        3. 路径效率奖励（权重5%）
        
        返回:
            reward: 全局奖励 [0, 1]
        """
        
        # 1. 用户覆盖率奖励
        connected_users = 0
        effective_connected_users = 0
        
        # 统计总连接用户和有效连接用户（有回程路径的）
        for i in range(self.n_uavs):
            uav_connected_users = np.sum(self.connections[i])
            connected_users += uav_connected_users
            
            # 只有当UAV有到地面基站的路径时，其连接的用户才算有效
            if i in self.routing_paths and self.routing_paths[i]:
                effective_connected_users += uav_connected_users
        
        # 基础覆盖率
        coverage_ratio = effective_connected_users / self.n_users if self.n_users > 0 else 0
        
        # 非线性覆盖率奖励：使用幂函数激励高覆盖率
        # f(x) = x^0.5 在低覆盖率时增长较快，在高覆盖率时趋于平缓
        coverage_reward = np.power(coverage_ratio, 0.5)
        
        # 添加高覆盖率奖励阶梯
        coverage_bonus = 0
        if coverage_ratio >= 0.95:  # 95%以上覆盖率
            coverage_bonus = 0.15
        elif coverage_ratio >= 0.90:  # 90%以上覆盖率
            coverage_bonus = 0.10
        elif coverage_ratio >= 0.85:  # 85%以上覆盖率
            coverage_bonus = 0.05
        
        # 最终覆盖率奖励
        final_coverage_reward = min(1.0, coverage_reward + coverage_bonus)
        
        # 2. 网络连通性奖励
        connected_uavs = len(self.routing_paths)
        connectivity_reward = connected_uavs / self.n_uavs if self.n_uavs > 0 else 0
        
        # 3. 路径效率奖励（平均跳数的倒数）
        if len(self.routing_paths) > 0:
            total_hops = sum(len(path) - 1 for path in self.routing_paths.values())
            avg_hops = total_hops / len(self.routing_paths)
            # 将平均跳数转换为效率奖励（2-4跳的范围内）
            efficiency_reward = max(0, 1 - (avg_hops - 1) / 3)  # 1跳=1.0, 4跳=0.0
        else:
            efficiency_reward = 0
            avg_hops = 0
        
        # 4. 系统吞吐量计算（用于信息记录）
        system_throughput = 0
        
        for i in range(self.n_uavs):
            connected_users_to_uav = []
            for j in range(self.n_users):
                if self.connections[i, j]:
                    connected_users_to_uav.append(j)
            
            if len(connected_users_to_uav) == 0:
                continue
            
            # 只有有回程路径的UAV才能提供有效吞吐量
            if i in self.routing_paths:
                uav_frontend_capacity = self._compute_uav_frontend_capacity(i, connected_users_to_uav)
                system_throughput += uav_frontend_capacity
        
        # 组合最终奖励
        final_reward = (
            self.coverage_weight * final_coverage_reward +
            self.connectivity_weight * connectivity_reward +
            self.efficiency_weight * efficiency_reward
        )
        
        # 确保奖励在[0, 1]范围内
        final_reward = np.clip(final_reward, 0, 1)
        
        # 更新奖励信息用于调试和可视化
        self.reward_info = {
            "coverage_reward": final_coverage_reward,
            "base_coverage_ratio": coverage_ratio,
            "coverage_bonus": coverage_bonus,
            "connectivity_reward": connectivity_reward,
            "efficiency_reward": efficiency_reward,
            "final_reward": final_reward,
            "effective_connected_users": effective_connected_users,
            "total_connected_users": connected_users,
            "system_throughput_mbps": system_throughput / 1e6,
            "avg_throughput_per_user_mbps": (system_throughput / max(effective_connected_users, 1)) / 1e6,
            "avg_hops": avg_hops,
            "connected_uavs": connected_uavs,
            "total_uavs": self.n_uavs,
            "coverage_ratio": coverage_ratio,  # 兼容性字段
            "target_coverage_achieved": coverage_ratio >= 0.90,  # 是否达到90%目标
        }
        
        return final_reward
    
    def _render_frame(self):
        """渲染单帧 - 添加强制中继特定的可视化元素"""
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
            # 绘制用户簇的边界（半透明圆圈）
            cluster_centers = self._get_cluster_centers()
            
            for center in cluster_centers:
                # 在地面绘制簇的范围
                circle = Circle(
                    (center[0], center[1]), 
                    self.cluster_std * 2,  # 2倍标准差作为可视化半径
                    fill=False, 
                    edgecolor='lightblue', 
                    alpha=0.4, 
                    linestyle='--'
                )
                # 注意：3D绘图中需要特殊处理2D圆圈
        
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
            self.ax.text2D(0.75, 0.70, f'Total Reward: {reward_info.get("final_reward", 0):.3f}', 
                          transform=self.ax.transAxes, fontsize=9, weight='bold')
            
            # 目标达成状态
            if reward_info.get("target_coverage_achieved", False):
                self.ax.text2D(0.02, 0.65, '✓ Target Coverage Achieved!', 
                              transform=self.ax.transAxes, color='green', weight='bold')
            else:
                self.ax.text2D(0.02, 0.65, '⚠ Target Coverage Not Achieved', 
                              transform=self.ax.transAxes, color='orange')
        
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
            "connectivity_weight": self.connectivity_weight,
            "efficiency_weight": self.efficiency_weight,
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
        计算两个节点之间的链路容量
        
        参数:
            node1_type: 节点1类型 ("uav" 或 "ground_bs")
            node1_idx: 节点1索引
            node2_type: 节点2类型 ("uav" 或 "ground_bs")
            node2_idx: 节点2索引
            
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
        
        # 计算路径损耗
        if node1_type == "uav" and node2_type == "uav":
            # UAV到UAV的路径损耗
            path_loss = self._compute_uav_path_loss(pos1, pos2)
            tx_power = self.tx_power
        elif (node1_type == "uav" and node2_type == "ground_bs") or (node1_type == "ground_bs" and node2_type == "uav"):
            # UAV到地面基站的路径损耗
            if node1_type == "uav":
                path_loss = self._compute_uav_path_loss(pos1, pos2)
            else:
                path_loss = self._compute_uav_path_loss(pos2, pos1)
            tx_power = self.ground_bs_tx_power
        else:
            return 0  # 不支持的连接类型
        
        # 计算接收功率 (dBm)
        rx_power = tx_power - path_loss
        
        # 计算SINR (dB) - 在FDMA模式下简化为SNR
        if self.use_fdma:
            sinr_db = rx_power - self.noise_power
        else:
            # 非FDMA模式需要考虑干扰，这里简化处理
            sinr_db = rx_power - self.noise_power
        
        # 检查SINR是否满足最小阈值
        if sinr_db < self.min_sinr:
            return 0
        
        # 转换为线性单位并计算容量
        sinr_linear = 10 ** (sinr_db / 10)
        capacity = self.bandwidth * np.log2(1 + sinr_linear)
        
        return capacity
    
    def _compute_routing_paths(self):
        """
        使用基于瓶颈容量的智能路由算法计算每个UAV到地面基站的最优路径
        
        新算法特点：
        1. 寻找瓶颈容量最大的路径，而不是跳数最少的路径
        2. 使用类似Dijkstra的"最宽路径"算法
        3. 智能选择高质量的多跳中继路径，即使跳数更多
        """
        self.routing_paths = {}
        
        # 为每个UAV计算最优路径
        for start_uav in range(self.n_uavs):
            best_path = self._find_widest_path_to_ground_bs(start_uav)
            if best_path and len(best_path) <= self.max_hops + 1:  # +1因为路径包含起始节点
                self.routing_paths[start_uav] = best_path
    
    def _find_widest_path_to_ground_bs(self, start_uav):
        """
        使用改进的Dijkstra算法寻找从UAV到地面基站的最宽路径
        
        参数:
            start_uav: 起始UAV索引
            
        返回:
            best_path: 最优路径列表 [(node_type, node_idx), ...]，如果没有路径则返回None
        """
        # 初始化距离数组（这里存储的是瓶颈容量）
        max_bottleneck = {}
        parent = {}
        visited = set()
        
        # 优先队列：(-瓶颈容量, 节点标识符)
        # 使用负值因为heapq是最小堆，我们需要最大瓶颈容量
        pq = []
        
        # 初始化起始UAV
        start_node = ("uav", start_uav)
        max_bottleneck[start_node] = float('inf')  # 起始节点的瓶颈容量设为无穷大
        parent[start_node] = None
        heapq.heappush(pq, (0, start_node))  # 起始节点的优先级最高
        
        # 所有可能的目标节点（地面基站）
        target_nodes = [("ground_bs", bs_idx) for bs_idx in range(self.n_ground_bs)]
        best_target = None
        best_capacity = 0
        
        while pq:
            neg_capacity, current_node = heapq.heappop(pq)
            current_capacity = -neg_capacity
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            current_type, current_idx = current_node
            
            # 检查是否到达地面基站
            if current_type == "ground_bs":
                if current_capacity > best_capacity:
                    best_capacity = current_capacity
                    best_target = current_node
                continue
            
            # 探索邻居节点
            neighbors = []
            
            if current_type == "uav":
                # 添加其他UAV作为邻居
                for next_uav in range(self.n_uavs):
                    if next_uav != current_idx:
                        neighbors.append(("uav", next_uav))
                
                # 添加地面基站作为邻居
                for bs_idx in range(self.n_ground_bs):
                    neighbors.append(("ground_bs", bs_idx))
            
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                
                neighbor_type, neighbor_idx = neighbor
                
                # 计算双向链路容量，取其最小值作为有效容量
                forward_capacity = self._get_link_capacity(
                    current_type, current_idx,
                    neighbor_type, neighbor_idx
                )
                
                reverse_capacity = self._get_link_capacity(
                    neighbor_type, neighbor_idx,
                    current_type, current_idx
                )
                
                # 链路的有效容量是双向容量中的较小者
                effective_link_capacity = min(forward_capacity, reverse_capacity)
                
                if effective_link_capacity <= 0:
                    continue  # 无法建立有效的双向连接
                
                # 计算通过当前路径到达邻居节点的瓶颈容量
                path_bottleneck = min(max_bottleneck.get(current_node, 0), effective_link_capacity)
                
                # 如果找到更好的路径
                if neighbor not in max_bottleneck or path_bottleneck > max_bottleneck[neighbor]:
                    max_bottleneck[neighbor] = path_bottleneck
                    parent[neighbor] = current_node
                    heapq.heappush(pq, (-path_bottleneck, neighbor))
        
        # 重构最优路径
        if best_target and best_capacity > 0:
            path = []
            current = best_target
            
            while current is not None:
                path.append(current)
                current = parent.get(current)
            
            path.reverse()
            return path
        
        return None  # 没有找到路径
