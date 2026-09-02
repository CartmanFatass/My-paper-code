import numpy as np
import gymnasium as gym
from gymnasium.spaces import Box, Dict
from pettingzoo import ParallelEnv
from pettingzoo.utils import wrappers

class MultiUAVEnv(ParallelEnv):
    """
    多无人机基站环境的基类
    
    实现了PettingZoo的Parallel接口，提供了基本的无人机和用户模型
    """
    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "multi_uav_env_v0",
        "is_parallelizable": True,
    }

    #: 信道模型的两条求值路径，见 __init__ 的 channel_backend 参数。
    CHANNEL_BACKENDS = ("vectorized", "reference")

    def __init__(
        self,
        n_uavs=5,
        n_users=50,
        area_size=1000,  # 区域大小 (m)
        height_range=(50, 150),  # 无人机高度范围 (m)
        max_speed=30,  # 最大速度 (m/s)
        time_step=1.0,  # 时间步长 (s)
        max_steps=5000,  # 最大步数
        user_distribution="uniform",  # 用户分布类型
        channel_model="free_space",  # 信道模型
        render_mode=None,
        seed=None,
        max_observed_uavs=10,  # 最大观测无人机数量
        max_observed_users=20,  # 最大观测用户数量
        use_shadowing=False,  # 是否启用阴影衰落（默认关闭）
        paper_reward=False,  # 是否使用论文中的奖励函数
        use_fdma=False,  # 是否启用FDMA频分多址（无干扰模式）
        bandwidth=20e6,  # 每个无人机的带宽 (Hz)，默认为20MHz
        ground_bs_tx_power=30,  # 地面基站发射功率 (dBm)
        step_path_loss_cache=True,  # 每步复用完全相同链路的路径损耗
        channel_backend="vectorized",  # 信道模型求值路径: "vectorized" 或 "reference"
    ):
        """
        初始化多无人机基站环境
        
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
        """
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
        if not isinstance(step_path_loss_cache, (bool, np.bool_)):
            raise TypeError("step_path_loss_cache must be a bool")
        self.step_path_loss_cache = bool(step_path_loss_cache)
        # 信道模型求值路径。"reference" 是逐链路的标量实现（原始代码，未修改）；
        # "vectorized" 用数组运算一次性求出同样的公式。两者在 1e-9 绝对容差内等价，
        # 由 tests/uav_env_channel_equivalence_test.py 判定。
        if channel_backend not in self.CHANNEL_BACKENDS:
            raise ValueError(
                f"channel_backend must be one of {self.CHANNEL_BACKENDS}, got {channel_backend!r}"
            )
        self.channel_backend = channel_backend
        
        # 局部观测参数
        self.max_observed_uavs = max_observed_uavs
        self.max_observed_users = max_observed_users
        
        # 阴影衰落参数
        self.use_shadowing = use_shadowing
        
        # FDMA参数
        self.use_fdma = use_fdma
        
        # 初始化随机数生成器
        self.np_random = np.random.RandomState(seed)

        # 路径损耗缓存只在一个物理状态代内有效。3GPP 链路即使关闭性能
        # 缓存也必须保留一次抽样，保证同一步内所有消费者看到同一信道实现。
        self._path_loss_cache = {}
        self._path_loss_cache_context = None
        self._path_loss_cache_generation = 0
        self._path_loss_cache_hits = 0
        self._path_loss_cache_misses = 0
        self._uav_user_path_loss_matrix = None
        self._uav_uav_path_loss_matrix = None
        self._path_loss_matrix_context = None
        self._path_loss_uav_position_bytes = None
        self._path_loss_user_position_bytes = None
        # 向量化路径每步一次性求出的无人机-无人机 SINR 矩阵，以及它对应的物理状态代。
        self.uav_sinr_matrix = None
        self._channel_state_generation = None

        # 通信参数 - 基于论文模型
        self.carrier_frequency = 2e9  # 载波频率 (Hz) - 论文中为2 GHz
        self.bandwidth = bandwidth  # 子信道带宽 (Hz) - 可配置参数
        self.tx_power = 23  # 发射功率 (dBm) - 论文中最大发射功率
        self.noise_power = -80  # 噪声功率 (dBm) - 论文中的σ²
        self.min_sinr = 3  # 最小SINR阈值 (dB) - 论文中的γ̄
        self.max_connections = 10  # 每个无人机最大连接数
        
        # 论文中的概率信道模型参数
        self.prob_channel_a = 9.61  # 环境常数a
        self.prob_channel_b = 0.16  # 环境常数b
        self.eta_los = 1.0  # LoS额外损耗 (dB)
        self.eta_nlos = 20.0  # NLoS额外损耗 (dB)
        #self.uav_height = 100  # 无人机飞行高度 (m) - 论文中的H
        
        # 论文中的信号与性能模型参数
        self.sinr_threshold_db = 3  # 最低SINR阈值γ̄ (dB)
        self.power_cost_weight = 100  # 单位功率成本w_m
        
        # 奖励函数选择
        self.paper_reward = paper_reward  # 是否使用论文中的奖励函数
        
        # 地面基站参数 (用于场景2)
        # 默认地面基站数量，可以被子类覆盖
        if not hasattr(self, 'n_ground_bs'):
            self.n_ground_bs = 1
        
        # 默认地面基站位置，可以被子类覆盖
        if not hasattr(self, 'ground_bs_positions'):
            self.ground_bs_positions = np.array([[area_size/2, area_size/2, 30]])  # 中心位置
        
        self.ground_bs_tx_power = ground_bs_tx_power  # 地面基站发射功率 (dBm)
        
        # 状态和观测维度
        self.state_dim = 3 * n_uavs + 2 * n_users + 1  # UAV位置 + 用户位置 + 当前步数
        # 新的观测维度：自身位置(3) + 局部用户相对位置(max_observed_users*3) + 局部无人机相对位置(max_observed_uavs*4) + 当前步数(1)
        # 注意：用户使用3维是因为包含相对位置(x,y)和距离(1)；无人机使用4维是因为包含相对位置(x,y,z)和距离(1)
        self.obs_dim = 3 + max_observed_users * 3 + max_observed_uavs * 4 + 1
        
        # 创建智能体列表
        self.possible_agents = [f"uav_{i}" for i in range(n_uavs)]
        self.agents = self.possible_agents.copy()
        
        # 定义观测和动作空间
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
            agent: Box(low=-1, high=1, shape=(3,), dtype=np.float32)
            for agent in self.possible_agents
        }
        
        # 环境状态
        self.uav_positions = None  # 无人机位置 [n_uavs, 3]
        self.user_positions = None  # 用户位置 [n_users, 2]
        self.connections = None  # 连接矩阵 [n_uavs, n_users]
        self.sinr_matrix = None  # SINR矩阵 [n_uavs, n_users]
        self.current_step = 0
        
        # 渲染相关
        self.viewer = None
        self.fig = None
        self.ax = None
        # 重置环境
        self.reset(seed=seed)

    # PettingZoo API methods for spaces
    def observation_space(self, agent):
        """返回指定智能体的观测空间"""
        return self.observation_spaces[agent]

    def action_space(self, agent):
        """返回指定智能体的动作空间"""
        return self.action_spaces[agent]

    def get_state_dim(self):
        """返回全局状态维度"""
        return self.state_dim
    
    def get_obs_dim(self):
        """返回观测维度"""
        return self.obs_dim
    
    def reset(self, seed=None, options=None):
        """
        重置环境
        
        返回:
            observations: 所有智能体的观测字典
            infos: 所有智能体的信息字典
        """
        if seed is not None:
            self.seed_val = seed
            self.np_random = np.random.RandomState(seed)
        
        # 重置环境状态
        self.current_step = 0
        self.agents = self.possible_agents.copy()
        
        # 初始化无人机位置
        self.uav_positions = np.zeros((self.n_uavs, 3))
        for i in range(self.n_uavs):
            self.uav_positions[i] = [
                self.np_random.uniform(0, self.area_size),
                self.np_random.uniform(0, self.area_size),
                self.np_random.uniform(*self.height_range)
            ]
        
        
        # 初始化用户位置
        self.user_positions = self._generate_user_positions()
        
        # 初始化连接矩阵和SINR矩阵
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        self.sinr_matrix = np.zeros((self.n_uavs, self.n_users))

        self._begin_path_loss_step()
        
        # 计算初始SINR和连接
        self._update_channel_state()
        
        # 获取所有智能体的观测
        observations = {}
        infos = {}
        
        for agent_idx, agent in enumerate(self.agents):
            observations[agent] = self._get_observation(agent)
            infos[agent] = {}
        
        # 如果在渲染模式下，初始化渲染
        if self.render_mode == "human":
            self._render_frame()
        
        return observations, infos
    
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
        # 更新所有无人机位置
        for agent_idx, agent in enumerate(self.agents):
            if agent in actions:
                # 将归一化动作转换为实际速度
                velocity = actions[agent] * self.max_speed
                
                # 更新位置
                new_position = self.uav_positions[agent_idx] + velocity * self.time_step
                
                # 边界检查
                new_position[0] = np.clip(new_position[0], 0, self.area_size)
                new_position[1] = np.clip(new_position[1], 0, self.area_size)
                new_position[2] = np.clip(new_position[2], *self.height_range)
                
                # 更新位置
                self.uav_positions[agent_idx] = new_position
        
        # UAV 位置已经更新，旧物理状态的缓存不得继续使用。
        self._begin_path_loss_step()

        # 更新信道状态和连接
        self._update_channel_state()
        
        # 计算奖励
        global_reward = self._compute_reward()
        
        # 更新步数
        self.current_step += 1
        
        # 检查是否达到最大步数
        done = self.current_step >= self.max_steps
        
        # 准备返回值
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        # 为每个智能体填充返回值
        for agent_idx, agent in enumerate(self.agents):
            observations[agent] = self._get_observation(agent)
            rewards[agent] = global_reward / self.n_uavs  # 平均分配奖励
            terminations[agent] = done
            truncations[agent] = False
            infos[agent] = {
                "connections": self.connections[agent_idx],
                "sinr_matrix": self.sinr_matrix[agent_idx],
                "served_users": np.sum(self.connections[agent_idx])
            }
        
        # 添加全局信息
        global_info = {
            "connections": self.connections,
            "sinr_matrix": self.sinr_matrix,
            "served_users": np.sum(self.connections)
        }
        
        for agent in self.agents:
            infos[agent].update({"global": global_info})
            # 添加实体位置信息，供GNN Agent使用
            entity_positions = {
                'uav_positions': self.uav_positions,
                'user_positions': self.user_positions,
                'ground_bs_positions': self.ground_bs_positions
            }
            infos[agent].update({'entity_positions': entity_positions})
        
        # 如果在渲染模式下，更新渲染
        if self.render_mode == "human":
            self._render_frame()
        
        return observations, rewards, terminations, truncations, infos
    
    def _get_state(self):
        """
        获取全局状态
        
        返回:
            state: 全局状态向量
        """
        # 全局状态包括所有无人机位置、所有用户位置和当前步数
        uav_positions_flat = self.uav_positions.flatten()
        user_positions_flat = self.user_positions.flatten()
        step_normalized = np.array([self.current_step / self.max_steps])
        
        state = np.concatenate([uav_positions_flat, user_positions_flat, step_normalized])
        return state
    
    def _get_observation(self, agent):
        """
        获取指定智能体基于通信能力的局部观测

        参数:
            agent: 智能体ID

        返回:
            observation: 智能体的观测
        """
        if self.channel_backend == "reference" or not self._vector_channel_state_is_current():
            return self._get_observation_reference(agent)
        return self._get_observation_vectorized(agent)

    def _get_observation_vectorized(self, agent):
        """Same layout and ordering, assembled from the precomputed SINR matrices."""
        agent_idx = int(agent.split("_")[1])
        own_position = self.uav_positions[agent_idx]

        # 1. 自身位置 (3维)
        normalized_position = own_position / self.area_size
        normalized_position[2] = (own_position[2] - self.height_range[0]) / (
            self.height_range[1] - self.height_range[0]
        )

        # 2. 局部用户观测 (max_observed_users * 3维)
        user_obs = np.zeros(self.max_observed_users * 3)
        user_indices, user_sinr = self._local_user_entries(agent_idx)
        observed_users = min(int(user_indices.size), self.max_observed_users)
        if observed_users:
            selected = user_indices[:observed_users]
            relative_positions = (
                self.user_positions[selected] - own_position[:2]
            ) / self.area_size
            normalized_sinr = np.clip((user_sinr[:observed_users] + 10) / 50, 0, 1)
            block = user_obs[: observed_users * 3].reshape(observed_users, 3)
            block[:, 0] = relative_positions[:, 0]
            block[:, 1] = relative_positions[:, 1]
            block[:, 2] = normalized_sinr

        # 3. 局部无人机观测 (max_observed_uavs * 4维)
        uav_obs = np.zeros(self.max_observed_uavs * 4)
        uav_indices, uav_sinr = self._local_uav_entries(agent_idx)
        observed_uavs = min(int(uav_indices.size), self.max_observed_uavs)
        if observed_uavs:
            selected = uav_indices[:observed_uavs]
            relative_positions = self.uav_positions[selected] - own_position
            relative_xy = relative_positions[:, :2] / self.area_size
            relative_z = relative_positions[:, 2] / (
                self.height_range[1] - self.height_range[0]
            )
            normalized_sinr = np.clip((uav_sinr[:observed_uavs] + 10) / 50, 0, 1)
            block = uav_obs[: observed_uavs * 4].reshape(observed_uavs, 4)
            block[:, 0] = relative_xy[:, 0]
            block[:, 1] = relative_xy[:, 1]
            block[:, 2] = relative_z
            block[:, 3] = normalized_sinr

        # 4. 当前步数 (1维)
        step_normalized = np.array([self.current_step / self.max_steps])

        obs = np.concatenate(
            [normalized_position, user_obs, uav_obs, step_normalized]
        ).astype(np.float32, copy=False)
        action_mask = np.ones(3, dtype=np.float32)
        return {"obs": obs, "action_mask": action_mask}

    def _get_observation_reference(self, agent):
        """Scalar reference path: local lists rebuilt per agent from `_compute_sinr`."""
        agent_idx = int(agent.split("_")[1])
        own_position = self.uav_positions[agent_idx]
        
        # 初始化观测向量
        obs_components = []
        
        # 1. 自身位置 (3维) - 归一化到[0,1]范围
        normalized_position = own_position / self.area_size
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
            relative_pos[2] = relative_pos[2] / (self.height_range[1] - self.height_range[0])
            # 归一化SINR到[0,1]范围
            normalized_sinr = np.clip((sinr_db + 10) / 50, 0, 1)
            
            start_idx = i * 4
            uav_obs[start_idx:start_idx+4] = [relative_pos[0], relative_pos[1], relative_pos[2], normalized_sinr]
        
        obs_components.append(uav_obs)
        
        # 4. 当前步数 (1维)
        step_normalized = np.array([self.current_step / self.max_steps])
        obs_components.append(step_normalized)
        
        # 组合所有观测
        obs = np.concatenate(obs_components).astype(np.float32, copy=False)
        
        # 动作掩码（这里我们不限制动作，所以全为1）
        action_mask = np.ones(3, dtype=np.float32)
        
        return {"obs": obs, "action_mask": action_mask}
    
    def _generate_user_positions(self):
        """
        生成用户位置
        
        返回:
            user_positions: 用户位置 [n_users, 2]
        """
        if self.user_distribution == "uniform":
            # 均匀分布
            user_positions = np.zeros((self.n_users, 2))
            for i in range(self.n_users):
                user_positions[i] = [
                    self.np_random.uniform(0, self.area_size),
                    self.np_random.uniform(0, self.area_size)
                ]
        
        elif self.user_distribution == "cluster":
            # 聚类分布
            n_clusters = min(5, self.n_users // 10 + 1)
            cluster_centers = self.np_random.uniform(0, self.area_size, (n_clusters, 2))
            cluster_std = self.area_size / 10
            
            user_positions = np.zeros((self.n_users, 2))
            users_per_cluster = self.n_users // n_clusters
            
            for i in range(n_clusters):
                start_idx = i * users_per_cluster
                end_idx = (i + 1) * users_per_cluster if i < n_clusters - 1 else self.n_users
                
                for j in range(start_idx, end_idx):
                    user_positions[j] = cluster_centers[i] + self.np_random.normal(0, cluster_std, 2)
                    # 确保在区域内
                    user_positions[j] = np.clip(user_positions[j], 0, self.area_size)
        
        elif self.user_distribution == "hotspot":
            # 热点分布
            hotspot_center = np.array([self.area_size/2, self.area_size/2])
            hotspot_radius = self.area_size / 3
            
            user_positions = np.zeros((self.n_users, 2))
            n_hotspot_users = int(self.n_users * 0.7)  # 70%的用户在热点区域
            
            # 热点区域的用户
            for i in range(n_hotspot_users):
                distance = self.np_random.uniform(0, hotspot_radius)
                angle = self.np_random.uniform(0, 2 * np.pi)
                user_positions[i] = hotspot_center + distance * np.array([np.cos(angle), np.sin(angle)])
            
            # 其余用户均匀分布
            for i in range(n_hotspot_users, self.n_users):
                user_positions[i] = [
                    self.np_random.uniform(0, self.area_size),
                    self.np_random.uniform(0, self.area_size)
                ]
        
        else:
            raise ValueError(f"未知的用户分布类型: {self.user_distribution}")
        
        return user_positions
    
    def _get_local_users(self, agent_idx):
        """
        获取指定无人机可通信的用户列表（基于SINR阈值）

        参数:
            agent_idx: 无人机索引

        返回:
            local_users: 按SINR降序排序的(用户索引, SINR)元组列表
        """
        if self.channel_backend == "reference" or not self._vector_channel_state_is_current():
            return self._get_local_users_reference(agent_idx)
        indices, values = self._local_user_entries(agent_idx)
        return list(zip(indices.tolist(), values.tolist()))

    def _local_user_entries(self, agent_idx):
        """(indices, SINR) above the threshold, SINR descending, from `sinr_matrix`."""
        row = self.sinr_matrix[agent_idx]
        eligible = np.flatnonzero(row >= self.min_sinr)
        # 降序，等值保持用户索引升序 —— 与 list.sort(reverse=True) 的稳定性一致。
        order = eligible[np.argsort(-row[eligible], kind="stable")]
        return order, row[order]

    def _local_uav_entries(self, agent_idx):
        """(indices, SINR) above the threshold, SINR descending, from `uav_sinr_matrix`."""
        row = self.uav_sinr_matrix[agent_idx]
        eligible = np.flatnonzero(row >= self.min_sinr)
        eligible = eligible[eligible != agent_idx]  # 跳过自己
        order = eligible[np.argsort(-row[eligible], kind="stable")]
        return order, row[order]

    def _get_local_users_reference(self, agent_idx):
        """Scalar reference path: one `_compute_sinr` call per user."""
        local_users = []
        
        for user_idx in range(self.n_users):
            # 计算SINR
            sinr_db = self._compute_sinr(agent_idx, user_idx)
            
            # 只有SINR大于等于最小阈值的用户才能被观测
            if sinr_db >= self.min_sinr:
                local_users.append((user_idx, sinr_db))
        
        # 按SINR降序排序（SINR最高的在前）
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
        if self.channel_backend == "reference" or not self._vector_channel_state_is_current():
            return self._get_local_uavs_reference(agent_idx)
        indices, values = self._local_uav_entries(agent_idx)
        return list(zip(indices.tolist(), values.tolist()))

    def _get_local_uavs_reference(self, agent_idx):
        """Scalar reference path: one `_compute_uav_to_uav_sinr` call per other UAV."""
        local_uavs = []
        
        for other_idx in range(self.n_uavs):
            if other_idx == agent_idx:
                continue  # 跳过自己
            
            # 计算无人机间的SINR
            sinr_db = self._compute_uav_to_uav_sinr(agent_idx, other_idx)
            
            # 只有SINR大于等于最小阈值的无人机才能被观测
            if sinr_db >= self.min_sinr:
                local_uavs.append((other_idx, sinr_db))
        
        # 按SINR降序排序（SINR最高的在前）
        local_uavs.sort(key=lambda x: x[1], reverse=True)
        return local_uavs

    def _compute_distance(self, pos1, pos2):
        """
        计算两点之间的欧几里得距离
        
        参数:
            pos1: 位置1
            pos2: 位置2
            
        返回:
            distance: 距离
        """
        return np.sqrt(np.sum((pos1 - pos2) ** 2))
    
    def _begin_path_loss_step(self):
        """Start a new physical-state generation for link-level channel values."""
        self._path_loss_cache_generation += 1
        self._path_loss_cache.clear()
        self._path_loss_cache_context = self._path_loss_context()
        self._path_loss_cache_hits = 0
        self._path_loss_cache_misses = 0
        self._uav_user_path_loss_matrix = None
        self._uav_uav_path_loss_matrix = None
        self._path_loss_matrix_context = None
        self._path_loss_uav_position_bytes = None
        self._path_loss_user_position_bytes = None

    def _path_loss_context(self):
        """Return every mutable non-position input used by path-loss formulas."""
        return (
            str(self.channel_model),
            float(self.carrier_frequency),
            bool(self.use_shadowing),
            float(self.prob_channel_a),
            float(self.prob_channel_b),
            float(self.eta_los),
            float(self.eta_nlos),
            tuple(self.agents),
        )

    def _ensure_path_loss_context(self):
        context = self._path_loss_context()
        if context != self._path_loss_cache_context:
            self._path_loss_cache.clear()
            self._path_loss_cache_context = context
        return context

    def _prime_path_loss_matrices(self):
        """Materialize each base-environment link once for the current state."""
        if self.channel_backend == "reference":
            self._prime_path_loss_matrices_reference()
        else:
            self._prime_path_loss_matrices_vectorized()

    def _prime_path_loss_matrices_reference(self):
        """Scalar reference path: one `_compute_path_loss_reference` call per link."""
        if not (self.step_path_loss_cache or self.channel_model == "3gpp-36777"):
            return

        context = self._ensure_path_loss_context()
        self._path_loss_matrix_context = context
        self._path_loss_uav_position_bytes = tuple(
            row.tobytes() for row in self.uav_positions
        )
        self._path_loss_user_position_bytes = tuple(
            row.tobytes() for row in self.user_positions
        )
        self._uav_user_path_loss_matrix = np.empty((self.n_uavs, self.n_users), dtype=float)
        self._uav_uav_path_loss_matrix = np.empty((self.n_uavs, self.n_uavs), dtype=float)

        for uav_idx in range(self.n_uavs):
            uav_pos = self.uav_positions[uav_idx]
            for user_idx in range(self.n_users):
                user_pos = self.user_positions[user_idx]
                value = float(self._compute_path_loss_reference(uav_pos, user_pos))
                if not np.isfinite(value):
                    raise FloatingPointError("path-loss computation produced a non-finite value")
                self._uav_user_path_loss_matrix[uav_idx, user_idx] = value
                key = self._path_loss_key("uav_user", uav_pos, user_pos, context)
                self._path_loss_cache[key] = value
                self._path_loss_cache_misses += 1

        for first_idx in range(self.n_uavs):
            self._uav_uav_path_loss_matrix[first_idx, first_idx] = 0.0
            for second_idx in range(first_idx + 1, self.n_uavs):
                first_pos = self.uav_positions[first_idx]
                second_pos = self.uav_positions[second_idx]
                value = float(self._compute_uav_path_loss_reference(first_pos, second_pos))
                if not np.isfinite(value):
                    raise FloatingPointError("path-loss computation produced a non-finite value")
                self._uav_uav_path_loss_matrix[first_idx, second_idx] = value
                self._uav_uav_path_loss_matrix[second_idx, first_idx] = value
                key = self._path_loss_key("uav_uav", first_pos, second_pos, context)
                self._path_loss_cache[key] = value
                self._path_loss_cache_misses += 1

    # ------------------------------------------------------------------
    # 向量化信道后端（吞吐重构 P1/P2）。
    #
    # 公式与上面的标量参考路径逐字相同，只是改用广播求值。浮点求和次序因此改变，
    # 两条路径是 1e-9 绝对容差内等价而不是逐位相同；连接矩阵完全相等。
    # 判定工具是 tests/uav_env_channel_equivalence_test.py。
    # ------------------------------------------------------------------

    def _channel_realization_is_stochastic(self):
        """True when a link's path loss consumes RNG (one draw per link per step)."""
        return self.channel_model == "3gpp-36777"

    def _user_position_components(self):
        """User x, y and z columns, with the scalar path's 2-D convention (z = 0)."""
        users = np.asarray(self.user_positions, dtype=float)
        if users.ndim != 2 or users.shape[1] < 2:
            raise ValueError("user_positions must be a [n_users, >=2] array")
        if users.shape[1] == 2:
            return users[:, 0], users[:, 1], np.zeros(users.shape[0], dtype=float)
        if users.shape[1] == 3:
            return users[:, 0], users[:, 1], users[:, 2]
        raise ValueError("user positions with more than three components are unsupported")

    def _uav_user_geometry(self):
        """3-D distance, 2-D distance, elevation angle and height for every (UAV, user)."""
        uav = np.asarray(self.uav_positions, dtype=float)
        user_x, user_y, user_z = self._user_position_components()
        height = uav[:, 2][:, None]
        delta_x = uav[:, 0][:, None] - user_x[None, :]
        delta_y = uav[:, 1][:, None] - user_y[None, :]
        delta_z = height - user_z[None, :]
        distance_3d = np.sqrt(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z)
        distance_2d = np.sqrt(delta_x * delta_x + delta_y * delta_y)
        elevation_angle = np.degrees(np.arctan2(height, distance_2d))
        return distance_3d, distance_2d, elevation_angle, height

    def _compute_path_loss_matrix(self):
        """[n_uavs, n_users] path loss in dB — `_compute_path_loss_reference`, broadcast."""
        distance_3d, _distance_2d, elevation_angle, height = self._uav_user_geometry()
        safe_distance = np.maximum(distance_3d, 1e-6)

        if self.channel_model == "free_space":
            wavelength = 3e8 / self.carrier_frequency
            return 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)

        if self.channel_model == "urban":
            return 128.1 + 37.6 * np.log10(safe_distance / 1000)

        if self.channel_model == "suburban":
            return 120 + 35 * np.log10(safe_distance / 1000)

        if self.channel_model == "3gpp-36777":
            f_c = self.carrier_frequency / 1e9
            p_los = 1 / (1 + 5 * np.exp(-0.6 * (elevation_angle - 5)))
            pl_los = 28.0 + 22 * np.log10(safe_distance) + 20 * np.log10(f_c)
            pl_nlos = 22.7 + 41 * np.log10(safe_distance) + 20 * np.log10(f_c)
            # 与标量路径同序、同数量地消耗 RNG：每条链路一次 uniform，行优先，
            # 这与 n_uavs * n_users 次标量 uniform(0, 1) 逐位相同。
            is_los = self.np_random.uniform(0, 1, size=p_los.shape) < p_los
            return np.where(is_los, pl_los, pl_nlos)

        if self.channel_model == "probabilistic":
            theta_deg = np.degrees(np.arcsin(height / safe_distance))
            p_los = 1 / (
                1
                + self.prob_channel_a
                * np.exp(-self.prob_channel_b * (theta_deg - self.prob_channel_a))
            )
            p_nlos = 1 - p_los
            wavelength = 3e8 / self.carrier_frequency
            l_fs = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
            return p_los * (l_fs + self.eta_los) + p_nlos * (l_fs + self.eta_nlos)

        raise ValueError(f"未知的信道模型: {self.channel_model}")

    def _compute_uav_path_loss_matrix(self):
        """[n_uavs, n_uavs] path loss in dB — `_compute_uav_path_loss_reference`, broadcast."""
        uav = np.asarray(self.uav_positions, dtype=float)
        difference = uav[:, None, :] - uav[None, :, :]
        distance_3d = np.sqrt(
            difference[:, :, 0] * difference[:, :, 0]
            + difference[:, :, 1] * difference[:, :, 1]
            + difference[:, :, 2] * difference[:, :, 2]
        )
        safe_distance = np.maximum(distance_3d, 1e-6)

        if self.channel_model in ("free_space", "3gpp-36777"):
            wavelength = 3e8 / self.carrier_frequency
            matrix = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
        elif self.channel_model == "urban":
            matrix = 128.1 + 37.6 * np.log10(safe_distance / 1000)
        elif self.channel_model == "suburban":
            matrix = 120 + 35 * np.log10(safe_distance / 1000)
        elif self.channel_model == "probabilistic":
            wavelength = 3e8 / self.carrier_frequency
            l_fs = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
            matrix = 0.9 * (l_fs + self.eta_los) + 0.1 * (l_fs + self.eta_nlos)
        else:
            raise ValueError(f"未知的信道模型: {self.channel_model}")

        # 标量路径把对角线显式写成 0.0（不走公式），这里照做。
        np.fill_diagonal(matrix, 0.0)
        return matrix

    def _prime_path_loss_matrices_vectorized(self):
        """Array path: both link matrices for the current physical state in one pass."""
        if self._channel_realization_is_stochastic() and self.use_shadowing:
            # 阴影衰落把 uniform 与 normal 抽样按链路交错，向量化会改变 RNG 消费顺序，
            # 所以这一组合的矩阵仍由标量路径求出（SINR 仍然向量化）。
            self._prime_path_loss_matrices_reference()
            return

        context = self._ensure_path_loss_context()
        self._path_loss_matrix_context = context
        self._path_loss_uav_position_bytes = tuple(
            row.tobytes() for row in self.uav_positions
        )
        self._path_loss_user_position_bytes = tuple(
            row.tobytes() for row in self.user_positions
        )

        uav_user = np.ascontiguousarray(self._compute_path_loss_matrix(), dtype=float)
        uav_uav = np.ascontiguousarray(self._compute_uav_path_loss_matrix(), dtype=float)
        if not (np.all(np.isfinite(uav_user)) and np.all(np.isfinite(uav_uav))):
            raise FloatingPointError("path-loss computation produced a non-finite value")
        self._uav_user_path_loss_matrix = uav_user
        self._uav_uav_path_loss_matrix = uav_uav
        self._path_loss_cache_misses += (
            self.n_uavs * self.n_users + (self.n_uavs * (self.n_uavs - 1)) // 2
        )

        if self._channel_realization_is_stochastic():
            # 一条链路在一个物理状态代内只有一次抽样：按链路调用的外部消费者
            # （场景 2/3、诊断工具）必须看到同一个实现值，所以字典照样填满。
            for uav_idx in range(self.n_uavs):
                uav_position = self.uav_positions[uav_idx]
                for user_idx in range(self.n_users):
                    key = self._path_loss_key(
                        "uav_user", uav_position, self.user_positions[user_idx], context
                    )
                    self._path_loss_cache[key] = float(uav_user[uav_idx, user_idx])
            for first_idx in range(self.n_uavs):
                for second_idx in range(first_idx + 1, self.n_uavs):
                    key = self._path_loss_key(
                        "uav_uav",
                        self.uav_positions[first_idx],
                        self.uav_positions[second_idx],
                        context,
                    )
                    self._path_loss_cache[key] = float(uav_uav[first_idx, second_idx])

    @staticmethod
    def _sum_excluding_own_row(values):
        """out[s, c] = sum over k != s of values[k, c], accumulated in ascending k."""
        rows = values.shape[0]
        result = np.zeros_like(values)
        for source in range(rows):
            accumulator = np.zeros(values.shape[1], dtype=values.dtype)
            for other in range(rows):
                if other == source:
                    continue
                accumulator += values[other]
            result[source] = accumulator
        return result

    def _sinr_from_path_loss(self, path_loss, interference_linear):
        """`_compute_sinr`'s dB arithmetic, including its zero-interference branch."""
        rx_power = self.tx_power - path_loss
        if self.use_fdma:
            return rx_power - self.noise_power

        noise_linear = 10 ** (self.noise_power / 10)
        positive = interference_linear > 0
        safe_interference = np.where(positive, interference_linear, 1.0)
        # 标量路径经过 dBm 往返（10*log10 再 10**(x/10)），这里保留同样的往返。
        total_interference_dbm = 10 * np.log10(safe_interference)
        interference_plus_noise_dbm = np.where(
            positive,
            10 * np.log10(noise_linear + 10 ** (total_interference_dbm / 10)),
            float(self.noise_power),
        )
        return rx_power - interference_plus_noise_dbm

    def _compute_uav_user_sinr_matrix(self):
        """[n_uavs, n_users] SINR in dB from the primed path-loss matrix."""
        path_loss = self._uav_user_path_loss_matrix
        if path_loss is None:
            raise RuntimeError("path-loss matrices were not primed for this step")
        if self.use_fdma:
            interference = np.zeros_like(path_loss)
        else:
            interference = self._sum_excluding_own_row(
                10 ** ((self.tx_power - path_loss) / 10)
            )
        return self._sinr_from_path_loss(path_loss, interference)

    def _compute_uav_uav_sinr_matrix(self):
        """[sender, receiver] SINR in dB, matching `_compute_uav_to_uav_sinr`."""
        path_loss = self._uav_uav_path_loss_matrix
        if path_loss is None:
            raise RuntimeError("path-loss matrices were not primed for this step")
        if self.use_fdma:
            interference = np.zeros_like(path_loss)
        else:
            linear = 10 ** ((self.tx_power - path_loss) / 10)
            # 接收方自己不是干扰源。把对角线置零后按 k 升序累加，与标量路径的
            # "跳过 k == receiver" 同序（加 0.0 是精确运算）。
            np.fill_diagonal(linear, 0.0)
            interference = self._sum_excluding_own_row(linear)
        return self._sinr_from_path_loss(path_loss, interference)

    def _greedy_connection_assignment(self):
        """The scalar path's greedy rule, with its exact descending/tie order."""
        sinr = self.sinr_matrix
        n_uavs, n_users = sinr.shape
        connections = np.zeros((n_uavs, n_users), dtype=bool)
        flat = np.asarray(sinr).reshape(-1)
        eligible = np.flatnonzero(flat >= self.min_sinr)
        if eligible.size == 0:
            return connections

        # 降序，等值保持 (uav, user) 升序 —— 与 list.sort(key=sinr, reverse=True)
        # 的稳定性完全一致。
        order = eligible[np.argsort(-flat[eligible], kind="stable")]

        uav_connections = [0] * n_uavs
        user_connected = [False] * n_users
        connected_total = 0
        full_uavs = 0
        for position in order.tolist():
            uav_idx = position // n_users
            user_idx = position - uav_idx * n_users
            if user_connected[user_idx] or uav_connections[uav_idx] >= self.max_connections:
                continue
            connections[uav_idx, user_idx] = True
            uav_connections[uav_idx] += 1
            if uav_connections[uav_idx] >= self.max_connections:
                full_uavs += 1
            user_connected[user_idx] = True
            connected_total += 1
            if connected_total == n_users or full_uavs == n_uavs:
                break
        return connections

    def _update_channel_state_vectorized(self):
        """SINR for every pair by matrix operations, then the same greedy assignment."""
        self._prime_path_loss_matrices()

        sinr = self._compute_uav_user_sinr_matrix()
        if (
            not isinstance(self.sinr_matrix, np.ndarray)
            or self.sinr_matrix.shape != sinr.shape
            or self.sinr_matrix.dtype != sinr.dtype
        ):
            self.sinr_matrix = np.array(sinr, dtype=float)
        else:
            # 原地写入，保留 info 字典里既有视图的语义。
            self.sinr_matrix[...] = sinr
        self.uav_sinr_matrix = self._compute_uav_uav_sinr_matrix()
        self._channel_state_generation = self._path_loss_cache_generation

        self.connections = self._greedy_connection_assignment()

    def _vector_channel_state_is_current(self):
        """True when the cached SINR matrices belong to the current physical state."""
        return (
            self.channel_backend != "reference"
            and self.uav_sinr_matrix is not None
            and self._channel_state_generation == self._path_loss_cache_generation
            and self._path_loss_matrix_context == self._path_loss_context()
        )

    def _cached_uav_user_path_loss(self, uav_idx, user_idx):
        if self._uav_user_path_loss_matrix is not None:
            if (
                self._path_loss_context() == self._path_loss_matrix_context
                and self.uav_positions[uav_idx].tobytes()
                == self._path_loss_uav_position_bytes[uav_idx]
                and self.user_positions[user_idx].tobytes()
                == self._path_loss_user_position_bytes[user_idx]
            ):
                self._path_loss_cache_hits += 1
                return self._uav_user_path_loss_matrix[uav_idx, user_idx]
        return self._compute_path_loss(self.uav_positions[uav_idx], self.user_positions[user_idx])

    def _cached_uav_uav_path_loss(self, first_idx, second_idx):
        if self._uav_uav_path_loss_matrix is not None:
            if (
                self._path_loss_context() == self._path_loss_matrix_context
                and self.uav_positions[first_idx].tobytes()
                == self._path_loss_uav_position_bytes[first_idx]
                and self.uav_positions[second_idx].tobytes()
                == self._path_loss_uav_position_bytes[second_idx]
            ):
                self._path_loss_cache_hits += 1
                return self._uav_uav_path_loss_matrix[first_idx, second_idx]
        return self._compute_uav_path_loss(self.uav_positions[first_idx], self.uav_positions[second_idx])

    @staticmethod
    def _position_cache_key(position):
        array = np.asarray(position)
        if array.ndim != 1 or array.dtype.kind not in "fiu":
            raise ValueError("path-loss positions must be finite one-dimensional numeric arrays")
        contiguous = np.ascontiguousarray(array)
        return (contiguous.dtype.str, contiguous.shape, contiguous.tobytes())

    def _path_loss_key(self, link_kind, first_pos, second_pos, context):
        first_key = self._position_cache_key(first_pos)
        second_key = self._position_cache_key(second_pos)
        if link_kind == "uav_uav" and second_key < first_key:
            first_key, second_key = second_key, first_key
        return (
            self._path_loss_cache_generation,
            context,
            link_kind,
            first_key,
            second_key,
        )

    def _cache_path_loss(self, link_kind, first_pos, second_pos, compute):
        # 3GPP is always cached because a link has exactly one stochastic channel
        # realization per physical step. Other models honor the performance switch.
        should_cache = self.step_path_loss_cache or self.channel_model == "3gpp-36777"
        if not should_cache:
            self._path_loss_cache_misses += 1
            return compute()

        context = self._ensure_path_loss_context()
        key = self._path_loss_key(link_kind, first_pos, second_pos, context)
        if key in self._path_loss_cache:
            self._path_loss_cache_hits += 1
            return self._path_loss_cache[key]

        value = float(compute())
        if not np.isfinite(value):
            raise FloatingPointError("path-loss computation produced a non-finite value")
        self._path_loss_cache[key] = value
        self._path_loss_cache_misses += 1
        return value

    def _compute_path_loss(self, uav_pos, user_pos):
        """
        计算路径损耗
        
        参数:
            uav_pos: 无人机位置 [3]
            user_pos: 用户位置 [2]
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        # 检查 user_pos 是否为整数索引，如果是则获取对应的用户位置
        if isinstance(user_pos, (int, np.integer)):
            user_pos = self.user_positions[user_pos]

        return self._cache_path_loss(
            "uav_user",
            uav_pos,
            user_pos,
            lambda: self._compute_path_loss_reference(uav_pos, user_pos),
        )

    def _compute_path_loss_reference(self, uav_pos, user_pos):
        """Uncached scalar reference formula used by the equivalence harness."""
            
        # 计算3D距离和2D距离
        # 确保 user_pos 是二维的 (x, y)
        if len(user_pos) > 2:
            user_pos_2d = user_pos[:2]  # 如果是三维的，取前两个元素
            user_pos_3d = user_pos  # 已经是三维的
        else:
            user_pos_2d = user_pos  # 已经是二维的
            user_pos_3d = np.append(user_pos, 0)  # 假设用户在地面
            
        distance_3d = self._compute_distance(uav_pos, user_pos_3d)
        distance_2d = np.sqrt(np.sum((uav_pos[:2] - user_pos_2d) ** 2))
        height = uav_pos[2]
        
        # 计算仰角 (度)
        elevation_angle = np.degrees(np.arctan2(height, distance_2d))
        
        # 确保距离不为零，避免log10(0)错误
        safe_distance = max(distance_3d, 1e-6)  # 使用一个很小的正数代替零
        
        # 根据不同信道模型计算路径损耗
        
        # 自由空间路径损耗模型
        if self.channel_model == "free_space":
            # 自由空间路径损耗 (dB)
            wavelength = 3e8 / self.carrier_frequency
            path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
        
        # 城市环境路径损耗模型
        elif self.channel_model == "urban":
            # 简化的城市环境路径损耗模型
            path_loss = 128.1 + 37.6 * np.log10(safe_distance / 1000)
        
        # 郊区环境路径损耗模型
        elif self.channel_model == "suburban":
            # 简化的郊区环境路径损耗模型
            path_loss = 120 + 35 * np.log10(safe_distance / 1000)
            
        # 3GPP 36.777标准的UAV信道模型 (TR 36.777)
        elif self.channel_model == "3gpp-36777":
            # 频率转换为GHz
            f_c = self.carrier_frequency / 1e9
            
            # 基于3GPP 36.777的路径损耗计算
            # 视距概率 (LoS probability)
            p_los = 1 / (1 + 5 * np.exp(-0.6 * (elevation_angle - 5)))
            
            # 视距路径损耗 (LoS path loss)
            pl_los = 28.0 + 22 * np.log10(safe_distance) + 20 * np.log10(f_c)
            
            # 非视距路径损耗 (NLoS path loss)
            pl_nlos = 22.7 + 41 * np.log10(safe_distance) + 20 * np.log10(f_c)
            
            # 模拟信道状态：根据LoS概率决定是LoS还是NLoS
            # 这是一个更符合实际仿真的蒙特卡洛方法，而不是计算期望值
            is_los = self.np_random.uniform(0, 1) < p_los
            
            if is_los:
                # 视距 (LoS) 链路
                path_loss = pl_los
                if self.use_shadowing:
                    sigma_los = 4.0
                    shadowing = self.np_random.normal(0, sigma_los)
                    path_loss += shadowing
            else:
                # 非视距 (NLoS) 链路
                path_loss = pl_nlos
                if self.use_shadowing:
                    sigma_nlos = 8.0
                    shadowing = self.np_random.normal(0, sigma_nlos)
                    path_loss += shadowing
        
        # 论文中的概率信道模型 (Probabilistic Channel Model)
        elif self.channel_model == "probabilistic":
            # 步骤1: 计算LoS概率 (Eq. 1)
            # θ = arcsin(H / d_m,l(t))，其中H是无人机高度，d_m,l是3D距离
            theta_rad = np.arcsin(height / safe_distance)  # 仰角 (弧度)
            theta_deg = np.degrees(theta_rad)  # 仰角 (度)
            
            # P_LoS = 1 / (1 + a * exp(-b * (θ - a)))
            p_los = 1 / (1 + self.prob_channel_a * np.exp(-self.prob_channel_b * (theta_deg - self.prob_channel_a)))
            p_nlos = 1 - p_los
            
            # 步骤2: 计算自由空间路径损耗 (Free Space Path Loss)
            # L_FS = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
            wavelength = 3e8 / self.carrier_frequency
            l_fs = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
            
            # 步骤3: 计算LoS和NLoS路径损耗 (Eq. 2a, 2b)
            pl_los = l_fs + self.eta_los   # LoS路径损耗
            pl_nlos = l_fs + self.eta_nlos # NLoS路径损耗
            
            # 步骤4: 计算平均路径损耗 (Eq. 3)
            # L(t) = P_LoS * PL_LoS + P_NLoS * PL_NLoS
            path_loss = p_los * pl_los + p_nlos * pl_nlos
        
        else:
            raise ValueError(f"未知的信道模型: {self.channel_model}")
            
        # 添加调试打印，用于验证路径损耗计算
        # print(f"Debug: 3D距离={distance_3d:.2f}m, 高度={height:.2f}m, 路径损耗={path_loss:.2f}dB, 信道模型={self.channel_model}")
        
        return path_loss
    
    def _compute_sinr(self, uav_idx, user_idx):
        """
        计算SINR (Signal to Interference plus Noise Ratio)
        
        参数:
            uav_idx: 无人机索引
            user_idx: 用户索引
            
        返回:
            sinr: SINR值 (dB)
        """
        # 检查索引并获取位置
        uav_is_index = isinstance(uav_idx, (int, np.integer))
        if uav_is_index:
            uav_pos = self.uav_positions[uav_idx]
        else:
            uav_pos = uav_idx  # 假设已经是位置
            
        user_is_index = isinstance(user_idx, (int, np.integer))
        if user_is_index:
            user_pos = self.user_positions[user_idx]
        else:
            user_pos = user_idx  # 假设已经是位置
        
        # 计算路径损耗
        if uav_is_index and user_is_index:
            path_loss = self._cached_uav_user_path_loss(int(uav_idx), int(user_idx))
        else:
            path_loss = self._compute_path_loss(uav_pos, user_pos)
        
        # 计算接收功率 (dBm)
        rx_power = self.tx_power - path_loss
        
        # 如果启用FDMA，无人机间无干扰，SINR = SNR
        if self.use_fdma:
            # FDMA模式：无干扰，SINR = 接收功率 - 噪声功率
            sinr = rx_power - self.noise_power
        else:
            # 原始模式：计算干扰功率
            interference_power = []
            for i in range(self.n_uavs):
                if i != uav_idx:
                    interferer_pos = self.uav_positions[i]
                    if user_is_index:
                        interferer_path_loss = self._cached_uav_user_path_loss(i, int(user_idx))
                    else:
                        interferer_path_loss = self._compute_path_loss(interferer_pos, user_pos)
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
    
    def _compute_uav_to_uav_sinr(self, sender_idx, receiver_idx):
        """
        计算无人机间通信的SINR (Signal to Interference plus Noise Ratio)
        
        参数:
            sender_idx: 发送方无人机索引
            receiver_idx: 接收方无人机索引
            
        返回:
            sinr: SINR值 (dB)
        """
        sender_pos = self.uav_positions[sender_idx]
        receiver_pos = self.uav_positions[receiver_idx]
        
        # 计算路径损耗（使用无人机到无人机的路径损耗计算）
        path_loss = self._cached_uav_uav_path_loss(sender_idx, receiver_idx)
        
        # 计算接收功率 (dBm)
        rx_power = self.tx_power - path_loss
        
        # 如果启用FDMA，无人机间无干扰，SINR = SNR
        if self.use_fdma:
            # FDMA模式：无干扰，SINR = 接收功率 - 噪声功率
            sinr = rx_power - self.noise_power
        else:
            # 原始模式：计算干扰功率
            interference_power = []
            for i in range(self.n_uavs):
                if i != sender_idx and i != receiver_idx:  # 排除发送方和接收方
                    interferer_pos = self.uav_positions[i]
                    interferer_path_loss = self._cached_uav_uav_path_loss(i, receiver_idx)
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
    
    def _compute_uav_path_loss(self, uav_pos1, uav_pos2):
        """
        计算无人机间的路径损耗
        
        参数:
            uav_pos1: 无人机1位置 [3]
            uav_pos2: 无人机2位置 [3]
            
        返回:
            path_loss: 路径损耗 (dB)
        """
        return self._cache_path_loss(
            "uav_uav",
            uav_pos1,
            uav_pos2,
            lambda: self._compute_uav_path_loss_reference(uav_pos1, uav_pos2),
        )

    def _compute_uav_path_loss_reference(self, uav_pos1, uav_pos2):
        """Uncached scalar reference formula for an air-to-air link."""
        # 计算3D距离
        distance_3d = self._compute_distance(uav_pos1, uav_pos2)
        
        # 确保距离不为零，避免log10(0)错误
        safe_distance = max(distance_3d, 1e-6)
        
        # 根据不同信道模型计算路径损耗
        if self.channel_model == "free_space":
            # 自由空间路径损耗 (dB)
            wavelength = 3e8 / self.carrier_frequency
            path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
        
        elif self.channel_model == "urban":
            # 简化的城市环境路径损耗模型
            path_loss = 128.1 + 37.6 * np.log10(safe_distance / 1000)
        
        elif self.channel_model == "suburban":
            # 简化的郊区环境路径损耗模型
            path_loss = 120 + 35 * np.log10(safe_distance / 1000)
            
        elif self.channel_model == "3gpp-36777":
            # 对于无人机间通信，简化为自由空间模型
            wavelength = 3e8 / self.carrier_frequency
            path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
        
        elif self.channel_model == "probabilistic":
            # 对于无人机间通信，使用简化的概率信道模型
            # 由于两个无人机都在空中，LoS概率较高，简化为主要考虑自由空间损耗
            wavelength = 3e8 / self.carrier_frequency
            l_fs = 20 * np.log10(safe_distance) + 20 * np.log10(4 * np.pi / wavelength)
            
            # 对于无人机间通信，假设LoS概率较高（0.9），NLoS概率较低（0.1）
            p_los = 0.9
            p_nlos = 0.1
            
            # LoS和NLoS路径损耗
            pl_los = l_fs + self.eta_los
            pl_nlos = l_fs + self.eta_nlos
            
            # 加权平均路径损耗
            path_loss = p_los * pl_los + p_nlos * pl_nlos
        
        else:
            raise ValueError(f"未知的信道模型: {self.channel_model}")
            
        return path_loss
    
    def _update_channel_state(self):
        """
        更新信道状态和连接
        """
        if self.channel_backend == "reference":
            self._update_channel_state_reference()
        else:
            self._update_channel_state_vectorized()

    def _update_channel_state_reference(self):
        """Scalar reference path: one `_compute_sinr` call per (UAV, user) pair."""
        self._prime_path_loss_matrices()

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
        uav_connections = [0] * self.n_uavs  # 每个UAV的连接数
        user_connected = [False] * self.n_users  # 每个用户是否已连接
        
        for uav_idx, user_idx, sinr in uav_user_pairs:
            # 如果UAV未达到最大连接数且用户未连接
            if uav_connections[uav_idx] < self.max_connections and not user_connected[user_idx]:
                self.connections[uav_idx, user_idx] = True
                uav_connections[uav_idx] += 1
                user_connected[user_idx] = True
    
    def _compute_reward(self):
        """
        计算奖励 - 支持原始奖励和论文奖励两种模式
        
        返回:
            reward: 全局奖励
        """
        if self.paper_reward:
            # 论文中的奖励函数 (Eq. 13)
            total_reward = 0.0
            
            for i in range(self.n_uavs):
                uav_reward = 0.0
                
                # 计算该无人机服务的所有用户的奖励
                for j in range(self.n_users):
                    if self.connections[i, j]:
                        sinr_db = self.sinr_matrix[i, j]
                        
                        # 检查SINR是否达到阈值
                        if sinr_db >= self.sinr_threshold_db:
                            # 将SINR从dB转换为线性值
                            sinr_linear = 10 ** (sinr_db / 10)
                            
                            # 根据香农公式计算吞吐量 (bps)
                            # R = (W/K) * log2(1 + γ)
                            throughput = self.bandwidth * np.log2(1 + sinr_linear)
                            
                            # 计算功率成本
                            # 将发射功率从dBm转换为瓦特
                            tx_power_watts = 10 ** ((self.tx_power - 30) / 10)
                            power_cost = self.power_cost_weight * tx_power_watts
                            
                            # 计算该连接的奖励
                            connection_reward = throughput - power_cost
                            uav_reward += connection_reward
                        # 如果SINR未达到阈值，该连接的奖励为0（已经是默认值）
                
                total_reward += uav_reward
            
            return total_reward
        
        else:
            # 原始奖励函数
            # 基本奖励：已连接用户数
            connected_users = np.sum(self.connections)
            reward = connected_users / self.n_users
            
            # 额外奖励：SINR质量
            total_sinr = 0
            for i in range(self.n_uavs):
                for j in range(self.n_users):
                    if self.connections[i, j]:
                        # 归一化SINR到[0,1]范围
                        normalized_sinr = np.clip((self.sinr_matrix[i, j] - self.min_sinr) / 30, 0, 1)
                        total_sinr += normalized_sinr
            
            # 平均SINR质量
            avg_sinr_quality = total_sinr / max(connected_users, 1)
            
            # 组合奖励
            reward = 0.7 * reward + 0.3 * avg_sinr_quality
            
            return reward
    
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
        """
        渲染单帧
        
        返回:
            frame: 渲染帧
        """
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
        self.ax.set_title(f'Multi-UAV Base Station Environment - Step: {self.current_step}/{self.max_steps}')
        
        # 绘制用户
        user_x = self.user_positions[:, 0]
        user_y = self.user_positions[:, 1]
        user_z = np.zeros(self.n_users)  # 用户在地面
        self.ax.scatter(user_x, user_y, user_z, c='blue', marker='.', label='Users')
        
        # 绘制无人机
        for i in range(self.n_uavs):
            uav_pos = self.uav_positions[i]
            self.ax.scatter(uav_pos[0], uav_pos[1], uav_pos[2], c='red', marker='^', s=100, label=f'UAV {i}' if i == 0 else "")
            
            # 绘制连接线
            for j in range(self.n_users):
                if self.connections[i, j]:
                    user_pos = self.user_positions[j]
                    self.ax.plot([uav_pos[0], user_pos[0]], [uav_pos[1], user_pos[1]], [uav_pos[2], 0], 'g-', alpha=0.3)
        
        # 绘制地面基站（如果有）
        if hasattr(self, 'ground_bs_positions') and len(self.ground_bs_positions) > 0:
            bs_x = self.ground_bs_positions[:, 0]
            bs_y = self.ground_bs_positions[:, 1]
            bs_z = self.ground_bs_positions[:, 2]
            self.ax.scatter(bs_x, bs_y, bs_z, c='black', marker='s', s=100, label='Ground BS')
        
        # 添加图例
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='upper right')
        
        # 添加统计信息
        connected_users = np.sum(self.connections)
        coverage_ratio = connected_users / self.n_users
        self.ax.text2D(0.02, 0.95, f'Connected Users: {connected_users}/{self.n_users} ({coverage_ratio:.2%})', transform=self.ax.transAxes)
        
        self.fig.canvas.draw()
        
        if self.render_mode == "human":
            plt.pause(0.01)
            return None
        
        # 返回RGB数组
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        canvas = FigureCanvasAgg(self.fig)
        canvas.draw()
        image = np.array(canvas.renderer.buffer_rgba())
        return image
    
    def close(self):
        """关闭环境"""
        if self.fig is not None:
            import matplotlib.pyplot as plt
            plt.close(self.fig)
            self.fig = None
            self.ax = None
