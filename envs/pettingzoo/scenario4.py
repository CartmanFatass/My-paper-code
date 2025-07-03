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
        max_steps=1500,
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
    
    def reset(self, seed=None, options=None):
        """
        重置环境 - 确保使用场景4特定的全局状态
        
        返回:
            observations: 所有智能体的观测字典
            infos: 所有智能体的信息字典
        """
        # 调用父类的 reset 来完成大部分初始化工作
        observations, infos = super().reset(seed=seed, options=options)
        
        # 关键：用当前类的方法重新计算 state，并更新 infos 字典
        # 父类的 reset 可能没有设置 state，我们在这里设置正确的 state
        current_state = self._get_state()
        self.state = current_state  # 更新内部状态
        
        # 为每个智能体的 info 添加正确的 state
        for agent in self.agents:
            infos[agent]['state'] = current_state.copy()
        
        return observations, infos
    
    def step(self, actions):
        """
        执行环境步骤 - 确保使用场景4特定的全局状态
        
        参数:
            actions: 所有智能体的动作字典 {agent_id: action}
            
        返回:
            observations: 所有智能体的下一个观测字典
            rewards: 所有智能体的奖励字典
            terminations: 所有智能体的终止状态字典
            truncations: 所有智能体的截断状态字典
            infos: 所有智能体的信息字典
        """
        # 调用父类的 step 来执行动作并获取基本返回
        observations, rewards, terminations, truncations, infos = super().step(actions)
        
        # 关键：用当前类的方法重新计算 next_state，并更新 info 字典
        next_state = self._get_state()
        self.state = next_state  # 更新内部状态以备下一步使用
        
        # 为每个智能体的 info 添加正确的 next_state
        for agent in self.agents:
            infos[agent]['next_state'] = next_state.copy()
        
        return observations, rewards, terminations, truncations, infos

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
        
        # 转换为线性单位并计算容量
        sinr_linear = 10 ** (sinr_db / 10)
        capacity = self.bandwidth * np.log2(1 + sinr_linear)
        
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
        
        # 根据设置决定使用确定性还是随机性模型
        if hasattr(self, 'use_deterministic_channel') and self.use_deterministic_channel:
            # 确定性模型：使用平均路径损耗（在线性域加权，然后转回dB）
            pl_los_linear = 10 ** (-pl_los / 10)
            pl_nlos_linear = 10 ** (-pl_nlos / 10)
            pl_avg_linear = p_los * pl_los_linear + (1 - p_los) * pl_nlos_linear
            path_loss = -10 * np.log10(pl_avg_linear)
        else:
            # 随机性模型：根据概率随机选择LoS或NLoS
            if hasattr(self, 'np_random'):
                random_val = self.np_random.uniform(0, 1)
            else:
                random_val = np.random.uniform(0, 1)
            
            if random_val < p_los:
                path_loss = pl_los
            else:
                path_loss = pl_nlos
        
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
            # FDMA模式：考虑邻频干扰和其他实际干扰源
            # 简化模型：假设邻频干扰为主要接收功率的10%
            adjacent_interference_ratio = 0.1
            interference_power_linear = (10 ** (rx_power / 10)) * adjacent_interference_ratio
            interference_power_dbm = 10 * np.log10(interference_power_linear) if interference_power_linear > 0 else -float('inf')
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            total_interference_noise = noise_power_linear + interference_power_linear
            total_interference_noise_dbm = 10 * np.log10(total_interference_noise)
            
            sinr_db = rx_power - total_interference_noise_dbm
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
            
            # 总干扰功率
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
                if i in self.routing_paths and self.routing_paths[i]:
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
                
                # 修正：根据数据流方向计算链路容量
                # 回程链路主要承载下行数据流（从基站到用户方向）
                if current_type == "uav" and neighbor_type == "ground_bs":
                    # UAV直连基站：考虑下行容量（基站到UAV）
                    effective_link_capacity = self._get_link_capacity(
                        neighbor_type, neighbor_idx,  # 基站作为发送方
                        current_type, current_idx     # UAV作为接收方
                    )
                elif current_type == "uav" and neighbor_type == "uav":
                    # UAV间中继：考虑中继转发能力
                    # 取上行和下行容量的较小值作为中继瓶颈
                    forward_capacity = self._get_link_capacity(
                        current_type, current_idx,
                        neighbor_type, neighbor_idx
                    )
                    reverse_capacity = self._get_link_capacity(
                        neighbor_type, neighbor_idx,
                        current_type, current_idx
                    )
                    # 对于中继节点，确实需要考虑双向转发能力
                    effective_link_capacity = min(forward_capacity, reverse_capacity)
                else:
                    # 其他情况：使用前向链路容量
                    effective_link_capacity = self._get_link_capacity(
                        current_type, current_idx,
                        neighbor_type, neighbor_idx
                    )
                
                if effective_link_capacity <= 0:
                    continue  # 无法建立有效连接
                
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
            # FDMA：用户间无干扰，总容量为各用户容量之和
            # 但受限于UAV的总带宽
            total_user_capacity = sum(user_capacities)
            
            # 计算每个用户分配的带宽比例
            if len(connected_users) > 0:
                bandwidth_per_user = self.bandwidth / len(connected_users)
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
            # 非FDMA模式：用户共享频谱，使用最差用户的SINR
            if len(user_capacities) > 0 and max(user_capacities) > 0:
                # 找到有效用户中SINR最差的
                valid_sinrs = []
                for i, user_idx in enumerate(connected_users):
                    if user_capacities[i] > 0:
                        uav_pos = self.uav_positions[uav_idx]
                        user_pos_3d = np.append(self.user_positions[user_idx], 0)
                        path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
                        rx_power = self.tx_power - path_loss
                        sinr_db = self._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
                        valid_sinrs.append(sinr_db)
                
                if valid_sinrs:
                    min_sinr_db = min(valid_sinrs)
                    min_sinr_linear = 10 ** (min_sinr_db / 10)
                    frontend_capacity = self.bandwidth * np.log2(1 + min_sinr_linear)
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
            # FDMA模式：考虑邻频干扰
            adjacent_interference_ratio = 0.1
            interference_power_linear = (10 ** (rx_power / 10)) * adjacent_interference_ratio
            interference_power_dbm = 10 * np.log10(interference_power_linear) if interference_power_linear > 0 else -float('inf')
            
            # 噪声加干扰功率
            noise_power_linear = 10 ** (self.noise_power / 10)
            total_interference_noise = noise_power_linear + interference_power_linear
            total_interference_noise_dbm = 10 * np.log10(total_interference_noise)
            
            sinr_db = rx_power - total_interference_noise_dbm
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
            
            # 总干扰功率
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
