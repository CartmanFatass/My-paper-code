import numpy as np
import heapq
import matplotlib
matplotlib.use('Agg')
from pettingzoo import ParallelEnv
from gymnasium.spaces import Box, Dict, Discrete
from scipy.spatial.distance import cdist
from envs.pettingzoo.relay.channel_geometry import RelayChannelGeometry
from envs.pettingzoo.uav_cpp_backend import (
    DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND,
    VALID_RELAY_GEOMETRY_BACKENDS,
    compute_relay_radio_batch,
    step_relay_geometry_batch,
)

_STEP_CACHE_UNSET = object()

# 尝试导入路由协议
try:
    from envs.pettingzoo.relay.routing import (
        BaseRoutingProtocol, HGGRProtocol, AODVProtocol, 
        DSDVProtocol, GPSRProtocol, WidestPathProtocol
    )
    ROUTING_PROTOCOLS_AVAILABLE = True
except ImportError as e:
    print(f"路由协议导入失败: {e}")
    ROUTING_PROTOCOLS_AVAILABLE = False

try:
    from stable_baselines3.common.running_mean_std import RunningMeanStd
    SB3_RUNNING_MEAN_STD_AVAILABLE = True
except ImportError as e:
    print(f"stable_baselines3.common.running_mean_std 导入失败: {e}")
    SB3_RUNNING_MEAN_STD_AVAILABLE = False


class UAVRoutedRelayEnv(ParallelEnv, RelayChannelGeometry):
    """
    场景4：强制多跳中继无人机环境
    
    """
    
    from envs.pettingzoo.relay.local_view import (
        _get_local_bs,
        _get_local_uavs,
        _get_local_users,
        _update_observations_dict,
    )

    metadata = {
        "render_modes": ["human", "rgb_array"],
        "name": "uav_forced_relay_env_v0",
        "is_parallelizable": True,
    }

    def __init__(self, config=None, **kwargs):
        super().__init__()
        
        n_uavs_for_hop_map = kwargs.get('n_uavs', 12) if config is None else getattr(config, 'n_agents', 12)
        self.hop_map = {i: float('inf') for i in range(n_uavs_for_hop_map)}

        # 如果没有传入config对象，则使用默认值或kwargs中的值
        if config is None:
            # 为了向后兼容，如果没有config对象，使用kwargs中的参数
            # 基本环境参数
            self.n_uavs = kwargs.get('n_uavs', 12)
            self.n_users = kwargs.get('n_users', 80)
            self.area_size = kwargs.get('area_size', 2500)
            self.height_range = kwargs.get('height_range', (50, 200))
            self.max_speed = kwargs.get('max_speed', 30)
            self.discrete_speeds = kwargs.get('discrete_speeds', [kwargs.get('discrete_speed', 15.0)]) # 支持多级速度
            self.time_step = kwargs.get('time_step', 1.0)
            self.max_steps = kwargs.get('max_steps', 5000)
            self.user_distribution = kwargs.get('user_distribution', "forced_relay_cluster")
            self.user_max_speed = kwargs.get('user_max_speed', 5.0)
            self.user_movement_model = kwargs.get('user_movement_model', "random_walk")
            self.cluster_migration_speed = kwargs.get('cluster_migration_speed', 15.0)
            self.cluster_pause_time_range = kwargs.get('cluster_pause_time_range', (0, 5))
            self.user_pause_time_range = kwargs.get('user_pause_time_range', (0, 3))
            self.render_mode = kwargs.get('render_mode', None)
            self.seed_val = kwargs.get('seed', None)
            
            # 场景特定参数
            self.n_clusters = kwargs.get('n_clusters', 4)
            self.cluster_std = kwargs.get('cluster_std', 80)
            self.n_remote_clusters = kwargs.get('n_remote_clusters', 0) # 新增：远程用户群数量
            self.remote_cluster_std = kwargs.get('remote_cluster_std', 120) # 新增：远程用户群标准差
            self.central_area_ratio = kwargs.get('central_area_ratio', 0.6)
            self.base_station_distance_factor = kwargs.get('base_station_distance_factor', 0.8)
            self.observation_radius = kwargs.get('observation_radius', 600)
            self.uav_init_mode = kwargs.get('uav_init_mode', "start_area")
            self.uav_start_area_size = kwargs.get('uav_start_area_size', 500)
            self.n_ground_bs = kwargs.get('n_ground_bs', 1)
            self.max_hops = kwargs.get('max_hops', 4)
            self.min_sinr = kwargs.get('min_sinr', 3)
            self.max_connections = kwargs.get('max_connections', 25)
            
            # 随机化控制参数
            self.randomize_bs = kwargs.get('randomize_bs', True)
            self.randomize_users = kwargs.get('randomize_users', True)
            self.randomize_uav_start = kwargs.get('randomize_uav_start', True)
            self.test_reward_mode = kwargs.get('test_reward_mode', False)
            
            # 奖励类型和权重 - 简化版：仅保留必要的权重参数
            self.reward_type = kwargs.get('reward_type', "naive")  # 默认为naive模式
            self.w_load_balance = kwargs.get('w_load_balance', 0.35)  # load_balance模式需要
            self.w_freshness_penalty = kwargs.get('w_freshness_penalty', 0.5)  # awareness模式需要
            self.w_first_contact = kwargs.get('w_first_contact', 0.1)  # load_balance模式的催化剂奖励
            self.w_repulsion = kwargs.get('w_repulsion', 0.0)  # 斥力场惩罚权重
            self.w_backhaul_outage = kwargs.get('w_backhaul_outage', 0.8)  # load_balance模式：回传断联惩罚
            self.w_full_disconnect = kwargs.get('w_full_disconnect', 1.0)  # load_balance模式：整网断联惩罚
            self.w_coverage_drop = kwargs.get('w_coverage_drop', 0.5)  # load_balance模式：覆盖率骤降惩罚
            self.w_outage_memory = kwargs.get('w_outage_memory', 0.25)  # load_balance模式：短期断联记忆惩罚
            self.w_relay_break = kwargs.get('w_relay_break', 1.2)  # load_balance模式：承载用户的回程路径断裂惩罚
            self.w_backhaul_margin = kwargs.get('w_backhaul_margin', 0.6)  # load_balance模式：回程瓶颈容量余量惩罚
            self.backhaul_margin_target_mbps = kwargs.get('backhaul_margin_target_mbps', 10.0)
            self.outage_memory_decay = kwargs.get('outage_memory_decay', 0.90)
            self.enable_backhaul_action_guard = kwargs.get('enable_backhaul_action_guard', True)
            self.backhaul_guard_min_capacity_mbps = kwargs.get('backhaul_guard_min_capacity_mbps', 5.0)
            self.backhaul_guard_reject_speed_scale = kwargs.get('backhaul_guard_reject_speed_scale', 0.0)
            
            # === test_reward 模式参数：基于物理动力学的审慎奖励设计 ===
            # 基于大疆(DJI)等典型四旋翼参数估算
            # 假设 max_speed = 30 m/s
            # 最大水平能耗因子: 1.0
            # 最大垂直能耗因子: 2.5 (垂直机动代价远高于水平)
            self.energy_weight_xy = kwargs.get('energy_weight_xy', 1.0)
            self.energy_weight_z = kwargs.get('energy_weight_z', 2.5)
            
            # 计算理论最大单步能耗代价 (用于归一化)
            # Max cost = (weight_xy * max_speed) + (weight_z * max_speed)
            # 注意：实际上无人机很难同时在水平和垂直方向都达到最大速度，但作为归一化分母足够安全
            self.max_step_energy_cost = (self.energy_weight_xy * self.max_speed + 
                                         self.energy_weight_z * self.max_speed) * self.time_step

            self.outage_sinr_threshold_db = kwargs.get('outage_sinr_threshold_db', -5)
            self.predictive_handover = kwargs.get('predictive_handover', False)

            # 软切换和动态簇管理参数
            self.enable_soft_handover = kwargs.get('enable_soft_handover', False)
            self.serving_set_size = kwargs.get('serving_set_size', 3)
            self.handover_hysteresis_db = kwargs.get('handover_hysteresis_db', 3.0)
            self.w_serving_set_cost = kwargs.get('w_serving_set_cost', 0.01)
            
            # 预测状态相关参数
            self.enable_predictive_state = kwargs.get('enable_predictive_state', False)
            self.prediction_horizon = kwargs.get('prediction_horizon', 3)
            
            # 卡尔曼滤波控制参数 (已停用)
            self.enable_cluster_kalman_filter = False
            
            # 通信参数
            self.carrier_frequency = kwargs.get('carrier_frequency', 2e9)
            self.tx_power = kwargs.get('tx_power', 23)
            self.noise_power = kwargs.get('noise_power', -94)
            self.use_fdma = kwargs.get('use_fdma', False)
            self.bandwidth = kwargs.get('bandwidth', 20e6)
            self.ground_bs_tx_power = kwargs.get('ground_bs_tx_power', 30)
            self.aclr_db = kwargs.get('aclr_db', 45)
            
            # 局部观测参数
            self.max_observed_uavs = kwargs.get('max_observed_uavs', 15)
            self.max_observed_users = kwargs.get('max_observed_users', 25)
            self.max_observed_bs = kwargs.get('max_observed_bs', 4)
            self.max_observed_overloaded_uavs = kwargs.get('max_observed_overloaded_uavs', 3) # 新增：观测过载无人机的数量
            self.routing_protocol = kwargs.get('routing_protocol', 'widest_path') # 'hggr', 'widest_path', 'geographic'
            self.action_space_type = kwargs.get('action_space_type', 'discrete')
            self.relay_geometry_backend = kwargs.get(
                'relay_geometry_backend', DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND
            )
        else:
            # 使用config对象通过getattr获取参数
            # 基本环境参数
            self.n_uavs = getattr(config, 'n_agents', 12)  # n_agents对应n_uavs
            self.n_users = getattr(config, 'n_users', 80)
            self.area_size = getattr(config, 'area_size', 2500)
            self.height_range = getattr(config, 'height_range', (50, 200))
            self.max_speed = getattr(config, 'max_speed', 30)
            self.discrete_speeds = getattr(config, 'discrete_speeds', [getattr(config, 'discrete_speed', 15.0)]) # 支持多级速度
            self.time_step = getattr(config, 'time_step', 1.0)
            self.max_steps = getattr(config, 'max_steps', 5000)
            self.user_distribution = getattr(config, 'user_distribution', "forced_relay_cluster")
            self.user_max_speed = getattr(config, 'user_max_speed', 5.0)
            self.user_movement_model = getattr(config, 'user_movement_model', "random_walk")
            self.cluster_migration_speed = getattr(config, 'cluster_migration_speed', 15.0)
            self.cluster_pause_time_range = getattr(config, 'cluster_pause_time_range', (0, 5))
            self.user_pause_time_range = getattr(config, 'user_pause_time_range', (0, 3))
            self.render_mode = kwargs.get('render_mode', None)  # 渲染模式仍从kwargs获取
            self.seed_val = kwargs.get('seed', None)  # 种子仍从kwargs获取
            
            # 场景特定参数
            self.n_clusters = getattr(config, 'n_clusters', 4)
            self.cluster_std = getattr(config, 'cluster_std', 80)
            self.n_remote_clusters = getattr(config, 'n_remote_clusters', 0) # 新增：远程用户群数量
            self.remote_cluster_std = getattr(config, 'remote_cluster_std', 120) # 新增：远程用户群标准差
            self.central_area_ratio = getattr(config, 'central_area_ratio', 0.6)
            self.base_station_distance_factor = getattr(config, 'base_station_distance_factor', 0.8)
            self.observation_radius = getattr(config, 'observation_radius', 600)
            self.uav_init_mode = getattr(config, 'uav_init_mode', "start_area")
            self.uav_start_area_size = getattr(config, 'uav_start_area_size', 500)
            self.n_ground_bs = getattr(config, 'n_ground_bs', 1)
            self.max_hops = getattr(config, 'max_hops', 4)
            self.min_sinr = getattr(config, 'min_sinr', 3)
            self.max_connections = getattr(config, 'max_connections', 25)
            
            # 随机化控制参数
            self.randomize_bs = getattr(config, 'randomize_bs', True)
            self.randomize_users = getattr(config, 'randomize_users', True)
            self.randomize_uav_start = getattr(config, 'randomize_uav_start', True)
            self.test_reward_mode = getattr(config, 'test_reward_mode', False)
            
            # 奖励类型和权重 - 简化版：仅保留必要的权重参数
            self.reward_type = getattr(config, 'reward_type', "naive")  # 默认为naive模式
            self.w_load_balance = getattr(config, 'w_load_balance', 0.35)  # load_balance模式需要
            self.w_freshness_penalty = getattr(config, 'w_freshness_penalty', 0.5)  # awareness模式需要
            self.w_first_contact = getattr(config, 'w_first_contact', 0.1)  # load_balance模式的催化剂奖励
            self.w_repulsion = getattr(config, 'w_repulsion', 0.0)  # 斥力场惩罚权重
            self.w_backhaul_outage = getattr(config, 'w_backhaul_outage', 0.8)  # load_balance模式：回传断联惩罚
            self.w_full_disconnect = getattr(config, 'w_full_disconnect', 1.0)  # load_balance模式：整网断联惩罚
            self.w_coverage_drop = getattr(config, 'w_coverage_drop', 0.5)  # load_balance模式：覆盖率骤降惩罚
            self.w_outage_memory = getattr(config, 'w_outage_memory', 0.25)  # load_balance模式：短期断联记忆惩罚
            self.w_relay_break = getattr(config, 'w_relay_break', 1.2)  # load_balance模式：承载用户的回程路径断裂惩罚
            self.w_backhaul_margin = getattr(config, 'w_backhaul_margin', 0.6)  # load_balance模式：回程瓶颈容量余量惩罚
            self.backhaul_margin_target_mbps = getattr(config, 'backhaul_margin_target_mbps', 10.0)
            self.outage_memory_decay = getattr(config, 'outage_memory_decay', 0.90)
            self.enable_backhaul_action_guard = getattr(config, 'enable_backhaul_action_guard', True)
            self.backhaul_guard_min_capacity_mbps = getattr(config, 'backhaul_guard_min_capacity_mbps', 5.0)
            self.backhaul_guard_reject_speed_scale = getattr(config, 'backhaul_guard_reject_speed_scale', 0.0)
            
            # === test_reward 模式参数：基于物理动力学的审慎奖励设计 ===
            # 基于大疆(DJI)等典型四旋翼参数估算
            self.energy_weight_xy = getattr(config, 'energy_weight_xy', 1.0)
            self.energy_weight_z = getattr(config, 'energy_weight_z', 2.5)
            
            # 计算理论最大单步能耗代价 (用于归一化)
            self.max_step_energy_cost = (self.energy_weight_xy * self.max_speed + 
                                         self.energy_weight_z * self.max_speed) * self.time_step
            
            self.outage_sinr_threshold_db = getattr(config, 'outage_sinr_threshold_db', -5)
            self.predictive_handover = getattr(config, 'predictive_handover', False)

            # 软切换和动态簇管理参数
            self.enable_soft_handover = getattr(config, 'enable_soft_handover', False)
            self.serving_set_size = getattr(config, 'serving_set_size', 3)
            self.handover_hysteresis_db = getattr(config, 'handover_hysteresis_db', 3.0)
            self.w_serving_set_cost = getattr(config, 'w_serving_set_cost', 0.01)
            
            # 预测状态相关参数
            self.enable_predictive_state = getattr(config, 'enable_predictive_state', False)
            self.prediction_horizon = getattr(config, 'prediction_horizon', 3)
            
            # 卡尔曼滤波控制参数 (已停用)
            self.enable_cluster_kalman_filter = False
            
            # 通信参数
            self.carrier_frequency = getattr(config, 'carrier_frequency', 2e9)
            self.tx_power = getattr(config, 'tx_power', 23)
            self.noise_power = getattr(config, 'noise_power', -94)
            self.use_fdma = getattr(config, 'use_fdma', False)
            self.bandwidth = getattr(config, 'bandwidth', 20e6)
            self.ground_bs_tx_power = getattr(config, 'ground_bs_tx_power', 30)
            self.aclr_db = getattr(config, 'aclr_db', 45)
            
            # 局部观测参数
            self.max_observed_uavs = getattr(config, 'max_observed_uavs', 15)
            self.max_observed_users = getattr(config, 'max_observed_users', 25)
            self.max_observed_bs = getattr(config, 'max_observed_bs', 4)
            self.max_observed_overloaded_uavs = getattr(config, 'max_observed_overloaded_uavs', 3) # 新增：观测过载无人机的数量
            self.routing_protocol = getattr(config, 'routing_protocol', 'widest_path') # 'hggr', 'widest_path', 'geographic'
            self.action_space_type = getattr(config, 'action_space_type', 'discrete')
            self.relay_geometry_backend = getattr(
                config,
                'relay_geometry_backend',
                kwargs.get(
                    'relay_geometry_backend',
                    DEFAULT_ROUTED_RELAY_GEOMETRY_BACKEND,
                ),
            )

        self.relay_geometry_backend = str(self.relay_geometry_backend)
        if self.relay_geometry_backend not in VALID_RELAY_GEOMETRY_BACKENDS:
            raise ValueError(
                f"Unknown relay_geometry_backend {self.relay_geometry_backend!r}; "
                f"expected one of {sorted(VALID_RELAY_GEOMETRY_BACKENDS)}"
            )
        self._relay_geometry_state = None

        # === 无人机动力学参数 (基于 IEEE TWC 论文: Zeng et al. 2019) ===
        # 参考型号: 类似 DJI Phantom 4 的小型旋翼机
        self.P0 = 79.86  # 悬停叶片轮廓功率 (W)
        self.Pi = 88.63  # 悬停诱导功率 (W)
        self.U_tip = 120 # 叶尖速度 (m/s)
        self.v0 = 4.03   # 平均诱导速度 (m/s)
        self.d0 = 0.6    # 机身阻力系数
        self.rho = 1.225 # 空气密度 (kg/m^3)
        self.s = 0.05    # 旋翼实度
        self.A = 0.503   # 桨盘面积 (m^2)
        
        # 预计算常数项，减少step中的计算量
        self.k1 = 3 / (self.U_tip ** 2)
        self.k2 = 1 / (2 * self.v0 ** 2) # 用于 1/(2v0^2)
        self.k3 = 0.5 * self.d0 * self.rho * self.s * self.A
        
        # 垂直飞行能耗权重 (近似处理: 爬升功率 = mg * Vz)
        # 假设无人机质量 m=1.5kg, g=9.8 => mg ≈ 15N
        # 垂直功率 P_z ≈ 15 * Vz (Watts)
        self.P_z_coeff = 15.0 
        
        # 归一化基准：计算最大速度下的功率，用于将惩罚缩放到 [0,1]
        # 假设最大水平速度和垂直速度
        # 这里的 max_speed 来自 config
        self.max_power_consumption = self._calculate_power_consumption(self.max_speed, self.max_speed) if hasattr(self, 'max_speed') else 300.0 # 默认给个值
        
        # 惩罚系数：决定能耗在总奖励中的占比
        # 如果设为 0.05，意味着满功率飞行的惩罚相当于损失了 5% 的覆盖率
        self.w_energy = 0.05
            
        # HGGR 分层路由参数
        self.hggr_update_interval = getattr(config, 'k', 10) if config else 10 # 默认为10

        # In __init__ method
        grid_resolution = 50  # 保持50x50网格
        self.grid_map_size = (grid_resolution, grid_resolution)
        self.last_visit_time_map = np.zeros(self.grid_map_size, dtype=np.int32)
        self.grid_cell_size = self.area_size / grid_resolution

        # 新增: Reward Shaping 相关变量
        self.previous_bottleneck_capacities = np.zeros(self.n_uavs)

        # 新增: stability_aware 奖励所需的状态追踪变量
        self.previous_coverage_ratio = 0.0
        self.previous_serving_uavs = set()
        self.prev_effective_user_service_status = np.zeros(self.n_users, dtype=bool)
        self.prev_load_balance_coverage_ratio = 0.0
        self.backhaul_outage_ema = 0.0
        self.full_disconnect_streak = 0
        self.previous_routing_paths_snapshot = {}
        self.previous_connections_snapshot = np.zeros((self.n_uavs, self.n_users), dtype=bool)

        # 新增: 层次强化学习中的全局基站信息缓存机制
        self.global_bs_cache = {}  # 存储全局同步的基站信息 {bs_idx: (normalized_pos, visibility_flag)}
        self.last_global_sync_step = -1  # 记录上次全局同步的步数

        # 新增: 基于3GPP标准的AMC (自适应调制与编码) 查找表
        # (SINR dB, Spectral Efficiency in bits/s/Hz)
        self.mcs_table = [
            (-5.0, 0.0),   # 传输失败
            (-2.5, 0.4),   # QPSK, ~1/5
            (0.0, 0.6),    # QPSK, ~1/3
            (2.5, 1.0),    # QPSK, ~1/2
            (5.0, 2.0),    # 16-QAM, ~1/2
            (7.5, 2.6),    # 16-QAM, ~2/3
            (10.0, 3.0),   # 16-QAM, ~3/4
            (12.5, 4.0),   # 64-QAM, ~2/3
            (15.0, 4.5),   # 64-QAM, ~3/4
            (17.5, 5.0),   # 64-QAM, ~5/6
            (float('inf'), 6.6) # 256-QAM, ~5/6
        ]

        # 初始化随机数生成器
        self.np_random = np.random.RandomState(self.seed_val)
        
        # 【关键修复】初始化状态变量，防止在reset()之前调用render()时出错
        self.current_step = 0
        self.uav_positions = np.zeros((self.n_uavs, 3))
        self.user_positions = np.zeros((self.n_users, 3))
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        self.routing_paths = {}

        # 新增: 探索发现相关的状态变量
        self.discovered_users_this_episode = set()
        self.discovered_bs_this_episode = set()

        # Track user service status to provide sparse rewards correctly
        self.user_serviced_status = np.zeros(self.n_users, dtype=bool)
        self.prev_user_serviced_status = np.zeros(self.n_users, dtype=bool)
        
        # 切换和预测相关
        # 卡尔曼滤波器已被移除
        self.kalman_filters = None
        self.cluster_kalman_filters = None
            
        self.user_velocities = np.zeros((self.n_users, 3))
        self.user_serving_uav = -np.ones(self.n_users, dtype=int) # 硬切换模式下使用
        self.user_serving_sets = [[] for _ in range(self.n_users)] # 软切换模式下使用
        self.user_handover_history = [[] for _ in range(self.n_users)]
        self.handover_count = 0
        self.ping_pong_count = 0
        # 软切换性能指标
        self.serving_set_changes = 0 # 服务簇成员变化次数 (加入或离开)
        self.uav_joins_count = 0
        self.uav_leaves_count = 0
        self.ping_pong_window = getattr(config, 'ping_pong_window', 5) if config else 5 # 5个时间步内发生A->B->A切换算作乒乓切换
        
        # RPGM 移动模型状态变量 (仅在 user_movement_model="rpgm" 时使用)
        self.user_waypoints = np.zeros((self.n_users, 2))  # 用户路径点 (2D)
        self.user_cluster_assignments = np.zeros(self.n_users, dtype=int)  # 用户簇分配
        self.cluster_centers_history = np.zeros((self.n_clusters, 2))  # 簇中心历史位置
        self.cluster_velocities = np.zeros((self.n_clusters, 2))  # 簇中心移动速度
        self.cluster_waypoints = np.zeros((self.n_clusters, 2))  # 簇中心目标点
        self.user_pause_times = np.zeros(self.n_users)  # 用户暂停时间
        self.cluster_pause_times = np.zeros(self.n_clusters)  # 簇中心暂停时间
        
        # 计算ACLR线性值
        self.aclr_linear = 10 ** (-self.aclr_db / 10)  # 转换为线性值以便计算

        # 创建从离散动作ID到速度向量 [vx, vy, vz] 的映射
        self.action_to_velocity = {0: np.array([0, 0, 0])}  # 0: 悬停 (Hover)
        action_id = 1
        
        # 定义基本方向向量
        base_directions = [
            np.array([1, 0, 0]),       # E
            np.array([-1, 0, 0]),      # W
            np.array([0, 1, 0]),       # N
            np.array([0, -1, 0]),      # S
            np.array([1, 1, 0]) / np.sqrt(2),   # NE
            np.array([1, -1, 0]) / np.sqrt(2),  # SE
            np.array([-1, 1, 0]) / np.sqrt(2),  # NW
            np.array([-1, -1, 0]) / np.sqrt(2), # SW
            np.array([0, 0, 1]),       # Up
            np.array([0, 0, -1]),     # Down
        ]

        # 为每个速度等级生成方向动作
        for speed in self.discrete_speeds:
            for direction_vector in base_directions:
                self.action_to_velocity[action_id] = direction_vector * speed
                action_id += 1

        self.n_discrete_actions = len(self.action_to_velocity)

        # 智能体列表
        self.possible_agents = [f"uav_{i}" for i in range(self.n_uavs)]
        self.agents = self.possible_agents.copy()

        # 观测和动作空间
        self_state_dim = 5
        overloaded_uav_obs_dim = self.max_observed_overloaded_uavs * 3  # 每个过载UAV观察3个维度 (x,y,load)

        base_obs_dim = 3 + 3 + self_state_dim + self.max_observed_uavs * 4 + self.max_observed_bs * 4 + overloaded_uav_obs_dim + 1

        if self.predictive_handover:
            self.obs_dim = base_obs_dim + self.max_observed_users * 7 # 6 -> 7
            if self.reward_type != "handover":
                print("Warning: predictive_handover is True, forcing reward_type to 'handover'.")
                self.reward_type = "handover"
        elif self.enable_soft_handover:
            self.obs_dim = base_obs_dim + self.max_observed_users * 6 # 5 -> 6
        else:
            self.obs_dim = base_obs_dim + self.max_observed_users * 5 # 4 -> 5
        
        action_mask_dim = self.n_discrete_actions if self.action_space_type == 'discrete' else 3
        self.observation_spaces = {
            agent: Dict({
                "obs": Box(low=-float('inf'), high=float('inf'), shape=(self.obs_dim,)),
                "action_mask": Box(low=0, high=1, shape=(action_mask_dim,))
            }) for agent in self.possible_agents
        }
        if self.action_space_type == 'discrete':
            self.action_spaces = {
                agent: Discrete(self.n_discrete_actions)
                for agent in self.possible_agents
            }
        elif self.action_space_type == 'continuous':
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
        
        # 重新计算并设置场景4的状态维度（简化版：仅包含物理实体状态）
        # 1. 无人机位置: n_uavs * 3
        uav_pos_dim = self.n_uavs * 3
        
        # 2. 用户详细信息: n_users * 6 (位置x, 位置y, 速度x, 速度y, 连接状态, SINR)
        user_info_dim = self.n_users * 6
        
        # 3. 地面基站位置: n_ground_bs * 3
        bs_pos_dim = self.n_ground_bs * 3

        # 4. 无人机负载: n_uavs * 1 (新增)
        uav_load_dim = self.n_uavs

        # 5. 当前步数: 1
        step_dim = 1
        
        # 重新设置state_dim 
        self.state_dim = uav_pos_dim + user_info_dim + bs_pos_dim + uav_load_dim + step_dim

        # 添加数据包级别仿真相关的变量
        self.metrics = {
            "packets_sent": 0,
            "packets_arrived": 0,
            "total_end_to_end_delay": 0.0,
            "total_hop_count": 0,
            "route_disconnections": 0,  # 数据包由于路由中断而丢失的数量
            "total_energy_consumed_mj": 0.0,  # 总能耗（毫焦耳）
        }
        
        # 当前网络中传输的活跃数据包列表
        self.active_packets = []
        self.packet_id_counter = 0
        
        # 简化的能耗模型（示例值）
        self.ENERGY_TX_MJ = 0.06  # 传输一个数据包的能耗（毫焦耳）
        self.ENERGY_RX_MJ = 0.02  # 接收一个数据包的能耗（毫焦耳）
        
        # 初始化路由协议实例（策略模式）
        self.router = None
        if ROUTING_PROTOCOLS_AVAILABLE:
            try:
                if self.routing_protocol == 'hggr':
                    self.router = HGGRProtocol(self)
                elif self.routing_protocol == 'aodv':
                    self.router = AODVProtocol(self)
                elif self.routing_protocol == 'dsdv':
                    self.router = DSDVProtocol(self)
                elif self.routing_protocol == 'geographic':
                    self.router = GPSRProtocol(self)
                elif self.routing_protocol == 'widest_path':
                    self.router = WidestPathProtocol(self)
                else:
                    # 默认使用widest_path协议
                    self.router = WidestPathProtocol(self)
            except Exception as e:
                print(f"路由协议初始化失败: {e}")
                self.router = None

    def _calculate_power_consumption(self, v_xy, v_z):
        """
        基于物理模型的功率计算 (Zeng et al. 2019)
        返回单位: Watts
        """
        # 1. 叶片轮廓功率 (Profile Power)
        # P_profile = P0 * (1 + 3 * V_xy^2 / U_tip^2)
        p_profile = self.P0 * (1 + self.k1 * (v_xy ** 2))
        
        # 2. 诱导功率 (Induced Power)
        # P_induced = Pi * sqrt( sqrt(1 + V_xy^4 / (4*v0^4)) - V_xy^2 / (2*v0^2) )
        # 注意数值稳定性
        term1 = 1 + (v_xy ** 4) / (4 * self.v0 ** 4)
        term2 = (v_xy ** 2) * self.k2
        # 【关键修复】增加 np.maximum(0, ...) 以防止浮点误差导致负数
        p_induced = self.Pi * np.sqrt(np.maximum(0, np.sqrt(term1) - term2))
        
        # 3. 寄生功率 (Parasitic Power) - 仅在高速时显著
        # P_parasitic = 0.5 * d0 * rho * s * A * V_xy^3
        p_parasitic = self.k3 * (v_xy ** 3)
        
        # 4. 垂直功率 (Vertical Power)
        # 简化模型：主要惩罚爬升，对下降也给予一定惩罚以防震荡
        p_vertical = self.P_z_coeff * abs(v_z)
        
        return p_profile + p_induced + p_parasitic + p_vertical

    def get_state_dim(self):
        """返回全局状态维度"""
        return self.state_dim
    
    def get_obs_dim(self):
        """返回观测维度"""
        return self.obs_dim

    def get_global_info(self):
        """返回计算跳数地图所需的全局信息 (用于HGGR算法)"""
        return {
            "n_uavs": self.n_uavs,
            "n_ground_bs": self.n_ground_bs,
            "uav_positions": self.uav_positions,
            "ground_bs_positions": self.ground_bs_positions,
            "get_link_capacity_func": self._get_link_capacity
        }

    def set_hop_map(self, hop_map):
        """从外部设置计算好的跳数地图 (用于HGGR算法)"""
        if isinstance(hop_map, dict):
            self.hop_map = hop_map
        else:
            self.hop_map = {i: hop_map[i] for i in range(len(hop_map))}

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
        elif self.user_distribution == "coverage_hole":
            return self._generate_coverage_hole_positions()
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
        生成强制中继优化的用户簇分布 - 支持中心区域和远离基站的远程区域混合部署。

        特点：
        - 可以在中心区域生成用户群，便于覆盖。
        - 可以在远离基站的角落生成远程用户群，强制多跳中继。
        - 通过 n_remote_clusters 参数控制远程用户群的数量。
        
        返回:
            user_positions: 用户位置 [n_users, 3] (包含高度1.5米)
        """
        user_positions = np.zeros((self.n_users, 3))
        
        # --- 1. 确定远程用户群和中心用户群的数量 ---
        n_remote = min(self.n_remote_clusters, self.n_clusters)
        n_central = self.n_clusters - n_remote
        
        all_cluster_centers = []
        all_cluster_stds = []

        # --- 2. 生成远程用户群 (如果 n_remote > 0) ---
        if n_remote > 0:
            # 计算所有基站的平均位置
            if self.n_ground_bs > 0:
                bs_center = np.mean(self.ground_bs_positions[:, :2], axis=0)
            else:
                bs_center = np.array([self.area_size * 0.05, self.area_size * 0.05])

            # 确定与基站群相对的、最远的角落
            area_center = self.area_size / 2
            if bs_center[0] < area_center and bs_center[1] < area_center: # 左下 -> 右上
                remote_corner = (self.area_size * 0.95, self.area_size * 0.95)
            elif bs_center[0] > area_center and bs_center[1] < area_center: # 右下 -> 左上
                remote_corner = (self.area_size * 0.05, self.area_size * 0.95)
            elif bs_center[0] < area_center and bs_center[1] > area_center: # 左上 -> 右下
                remote_corner = (self.area_size * 0.95, self.area_size * 0.05)
            else: # 右上 -> 左下
                remote_corner = (self.area_size * 0.05, self.area_size * 0.05)

            # 在最远的角落附近生成远程用户群
            for i in range(n_remote):
                offset = self.np_random.uniform(-self.area_size * 0.1, self.area_size * 0.1, 2)
                center_x = np.clip(remote_corner[0] + offset[0], self.area_size * 0.05, self.area_size * 0.95)
                center_y = np.clip(remote_corner[1] + offset[1], self.area_size * 0.05, self.area_size * 0.95)
                all_cluster_centers.append([center_x, center_y])
                all_cluster_stds.append(self.remote_cluster_std)

        # --- 3. 生成中心用户群 (如果 n_central > 0) ---
        if n_central > 0:
            central_size = self.area_size * self.central_area_ratio
            central_margin = (self.area_size - central_size) / 2
            
            # 在中心区域生成簇
            for i in range(n_central):
                x = self.np_random.uniform(central_margin, central_margin + central_size)
                y = self.np_random.uniform(central_margin, central_margin + central_size)
                all_cluster_centers.append([x, y])
                all_cluster_stds.append(self.cluster_std)

        # --- 4. 将用户均匀分配到所有簇中 ---
        cluster_centers = np.array(all_cluster_centers)
        
        if self.n_clusters == 0:
             return user_positions

        base_users_per_cluster = self.n_users // self.n_clusters
        remaining_users = self.n_users % self.n_clusters
        
        cluster_user_counts = [base_users_per_cluster] * self.n_clusters
        for i in range(remaining_users):
            cluster_user_counts[i] += 1
            
        # --- 5. 为每个簇生成用户 ---
        user_idx = 0
        for cluster_idx in range(self.n_clusters):
            cluster_center = cluster_centers[cluster_idx]
            cluster_std = all_cluster_stds[cluster_idx]
            n_users_in_cluster = cluster_user_counts[cluster_idx]
            
            for _ in range(n_users_in_cluster):
                offset = self.np_random.multivariate_normal(
                    mean=[0, 0],
                    cov=[[cluster_std**2, 0], [0, cluster_std**2]]
                )
                user_pos_2d = cluster_center + offset
                
                # 确保用户在地图边界内
                user_pos_2d[0] = np.clip(user_pos_2d[0], 10, self.area_size - 10)
                user_pos_2d[1] = np.clip(user_pos_2d[1], 10, self.area_size - 10)

                user_positions[user_idx] = np.array([user_pos_2d[0], user_pos_2d[1], 1.5])
                
                if hasattr(self, 'user_cluster_assignments'):
                    self.user_cluster_assignments[user_idx] = cluster_idx
                
                user_idx += 1
        
        # 初始化簇中心历史位置 (用于RPGM移动模型)
        if hasattr(self, 'cluster_centers_history'):
             if cluster_centers.shape[0] == self.cluster_centers_history.shape[0]:
                self.cluster_centers_history = cluster_centers.copy()

        return user_positions
    
    def _generate_coverage_hole_positions(self):
        """
        生成覆盖空洞场景的用户分布 - 专门用于中继场景研究
        
        特点：
        - 所有用户都位于远离基站的区域，形成明显的覆盖空洞
        - 用户无法直接与基站建立有效通信，强制需要无人机中继
        - 符合无线通信研究中的标准覆盖空洞场景设置
        
        返回:
            user_positions: 用户位置 [n_users, 3] (包含高度1.5米)
        """
        user_positions = np.zeros((self.n_users, 3))
        
        # 获取基站位置（假设单基站场景）
        if self.n_ground_bs > 0:
            bs_pos = self.ground_bs_positions[0]  # 使用第一个基站
        else:
            # 如果没有基站，默认基站在左下角
            bs_pos = np.array([self.area_size * 0.05, self.area_size * 0.05, 30])
        
        # 确定覆盖空洞区域（与基站对角线相对的区域）
        # 基站在左下角 -> 用户在右上角
        # 基站在右上角 -> 用户在左下角
        # 基站在左上角 -> 用户在右下角
        # 基站在右下角 -> 用户在左上角
        
        area_center = self.area_size / 2
        
        # 判断基站在哪个象限
        if bs_pos[0] < area_center and bs_pos[1] < area_center:
            # 基站在左下角，用户区域在右上角
            hole_x_min = self.area_size * 0.6
            hole_x_max = self.area_size * 0.95
            hole_y_min = self.area_size * 0.6
            hole_y_max = self.area_size * 0.95
        elif bs_pos[0] > area_center and bs_pos[1] > area_center:
            # 基站在右上角，用户区域在左下角
            hole_x_min = self.area_size * 0.05
            hole_x_max = self.area_size * 0.4
            hole_y_min = self.area_size * 0.05
            hole_y_max = self.area_size * 0.4
        elif bs_pos[0] < area_center and bs_pos[1] > area_center:
            # 基站在左上角，用户区域在右下角
            hole_x_min = self.area_size * 0.6
            hole_x_max = self.area_size * 0.95
            hole_y_min = self.area_size * 0.05
            hole_y_max = self.area_size * 0.4
        else:
            # 基站在右下角，用户区域在左上角
            hole_x_min = self.area_size * 0.05
            hole_x_max = self.area_size * 0.4
            hole_y_min = self.area_size * 0.6
            hole_y_max = self.area_size * 0.95
        
        # 在覆盖空洞区域内生成用户簇
        hole_width = hole_x_max - hole_x_min
        hole_height = hole_y_max - hole_y_min
        
        # 生成簇中心位置
        cluster_centers = np.zeros((self.n_clusters, 2))
        
        if self.randomize_users:
            # 随机在覆盖空洞区域内生成簇中心
            for i in range(self.n_clusters):
                # 确保簇中心之间有足够的距离，避免重叠
                max_attempts = 50
                for attempt in range(max_attempts):
                    x = self.np_random.uniform(hole_x_min, hole_x_max)
                    y = self.np_random.uniform(hole_y_min, hole_y_max)
                    new_center = np.array([x, y])
                    
                    # 检查与已有簇中心的距离
                    min_distance = self.cluster_std * 2.5  # 簇中心之间的最小距离
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
                    x = hole_x_min + hole_width * (grid_i + 0.5) / grid_size
                    y = hole_y_min + hole_height * (grid_j + 0.5) / grid_size
                    cluster_centers[i] = [x, y]
        else:
            # 固定簇中心布局
            if self.n_clusters == 1:
                # 单个簇在覆盖空洞中心
                cluster_centers[0] = [(hole_x_min + hole_x_max) / 2, (hole_y_min + hole_y_max) / 2]
            elif self.n_clusters == 2:
                # 两个簇对角分布
                cluster_centers[0] = [hole_x_min + hole_width * 0.3, hole_y_min + hole_height * 0.3]
                cluster_centers[1] = [hole_x_min + hole_width * 0.7, hole_y_min + hole_height * 0.7]
            elif self.n_clusters == 3:
                # 三个簇形成三角形
                cluster_centers[0] = [hole_x_min + hole_width * 0.5, hole_y_min + hole_height * 0.2]
                cluster_centers[1] = [hole_x_min + hole_width * 0.2, hole_y_min + hole_height * 0.8]
                cluster_centers[2] = [hole_x_min + hole_width * 0.8, hole_y_min + hole_height * 0.8]
            elif self.n_clusters == 4:
                # 四个簇形成2x2网格
                cluster_centers[0] = [hole_x_min + hole_width * 0.3, hole_y_min + hole_height * 0.3]
                cluster_centers[1] = [hole_x_min + hole_width * 0.7, hole_y_min + hole_height * 0.3]
                cluster_centers[2] = [hole_x_min + hole_width * 0.3, hole_y_min + hole_height * 0.7]
                cluster_centers[3] = [hole_x_min + hole_width * 0.7, hole_y_min + hole_height * 0.7]
            else:
                # 其他情况使用网格布局
                grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
                cluster_idx = 0
                
                for i in range(grid_size):
                    for j in range(grid_size):
                        if cluster_idx >= self.n_clusters:
                            break
                        
                        x = hole_x_min + hole_width * (i + 0.5) / grid_size
                        y = hole_y_min + hole_height * (j + 0.5) / grid_size
                        
                        cluster_centers[cluster_idx] = [x, y]
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
                
                user_position_2d = cluster_center + offset
                
                # 确保用户位置在覆盖空洞区域内
                user_position_2d[0] = np.clip(user_position_2d[0], hole_x_min + 10, hole_x_max - 10)
                user_position_2d[1] = np.clip(user_position_2d[1], hole_y_min + 10, hole_y_max - 10)
                
                # 创建三维用户位置（包含1.5米高度）
                user_position_3d = np.array([user_position_2d[0], user_position_2d[1], 1.5])
                
                user_positions[user_idx] = user_position_3d
                user_idx += 1
        
        return user_positions
    
    
    def _calculate_individual_distance_overlap_penalties(self):
        """
        计算每个智能体的个体距离重叠惩罚（智能版）。
        惩罚力度与无人机的网络贡献角色相关。

        返回:
            individual_penalties (np.ndarray): 每个智能体的惩罚值数组。
        """
        individual_penalties = np.zeros(self.n_uavs)
        
        # 定义不同角色的惩罚乘数
        idle_penalty_multiplier = 10.0  # 对空闲无人机施加高额惩罚
        active_penalty_multiplier = 0.5   # 对有贡献的无人机施加非常低的惩罚
        
        # 定义安全距离
        safety_radius = self.observation_radius / 3.0

        # --- 识别有贡献的无人机 ---
        contributing_uavs = set()
        # 1. 服务用户的无人机是有贡献的
        for uav_idx in range(self.n_uavs):
            if np.sum(self.connections[uav_idx]) > 0:
                contributing_uavs.add(uav_idx)
        
        # 2. 作为中继节点的无人机也是有贡献的
        for path, _ in self.routing_paths.values():
            # 路径上的所有无人机（除了终点基站）都是有贡献的中继节点
            for node_type, node_idx in path:
                if node_type == 'uav':
                    contributing_uavs.add(node_idx)

        # --- 计算每个无人机的惩罚 ---
        for i in range(self.n_uavs):
            min_dist_to_neighbor = float('inf')
            
            for j in range(self.n_uavs):
                if i == j:
                    continue
                dist = np.linalg.norm(self.uav_positions[i, :2] - self.uav_positions[j, :2])
                if dist < min_dist_to_neighbor:
                    min_dist_to_neighbor = dist

            if min_dist_to_neighbor < safety_radius:
                normalized_dist = min_dist_to_neighbor / safety_radius
                penalty_base = (1 - np.sqrt(normalized_dist))
                
                # 根据角色应用不同的惩罚力度
                if i in contributing_uavs:
                    # 对于有贡献的无人机，施加较低惩罚
                    penalty = penalty_base * active_penalty_multiplier
                else:
                    # 对于空闲无人机，施加较高惩罚
                    penalty = penalty_base * idle_penalty_multiplier
                
                individual_penalties[i] = penalty
                
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
        # 遍历每一个用户，确保每个用户只被计算一次
        for user_idx in range(self.n_users):
            is_effectively_covered = False
            # 查找连接到该用户的所有无人机
            connected_uavs_indices = np.where(self.connections[:, user_idx])[0]
            
            for uav_idx in connected_uavs_indices:
                # 只要其中任意一个无人机有回程路径，该用户就算作有效覆盖
                if uav_idx in self.routing_paths and self.routing_paths[uav_idx][0]:
                    is_effectively_covered = True
                    break  # 找到一个即可，无需继续检查
            
            if is_effectively_covered:
                effective_connected_users += 1

        # total_connected_users 的计算也需要修正，以避免重复计数
        total_connected_users = 0
        for user_idx in range(self.n_users):
            if np.any(self.connections[:, user_idx]):
                total_connected_users += 1
        
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
            # 【新增】确保包含所有关键性能指标，供可视化工具使用
            "served_users": effective_connected_users,  # 为兼容性添加别名
            "service_rate": coverage_ratio,  # 服务率等同于覆盖率
            # 【关键修复】添加当前用户位置，用于可视化用户移动轨迹
            "user_positions": self.user_positions.copy() if hasattr(self, 'user_positions') and self.user_positions is not None else None,
        }
        
        return coverage_ratio

    def _calculate_backhaul_outage_metrics(self):
        """
        统计由回传/路由断联导致的服务中断。

        access_connected 表示用户至少被某个UAV接入；effective_service 表示该接入UAV
        至少有一条有效回传路径。两者的差值用于区分“接入覆盖不足”和“网络断联”。
        """
        access_connected_status = np.any(self.connections, axis=0) if self.n_users > 0 else np.array([], dtype=bool)
        effective_service_status = np.zeros(self.n_users, dtype=bool)

        for user_idx in range(self.n_users):
            connected_uavs = np.where(self.connections[:, user_idx])[0]
            for uav_idx in connected_uavs:
                if uav_idx in self.routing_paths and self.routing_paths[uav_idx][0]:
                    effective_service_status[user_idx] = True
                    break

        access_connected_users = int(np.sum(access_connected_status))
        access_no_backhaul_status = access_connected_status & ~effective_service_status
        access_no_backhaul_users = int(np.sum(access_no_backhaul_status))
        access_no_backhaul_ratio = access_no_backhaul_users / self.n_users if self.n_users > 0 else 0.0

        prev_effective_status = getattr(
            self,
            'prev_effective_user_service_status',
            np.zeros(self.n_users, dtype=bool)
        )
        dropped_service_status = prev_effective_status & ~effective_service_status
        backhaul_drop_status = dropped_service_status & access_connected_status
        dropped_service_users = int(np.sum(dropped_service_status))
        backhaul_drop_users = int(np.sum(backhaul_drop_status))
        prev_effective_users = int(np.sum(prev_effective_status))
        service_drop_ratio = dropped_service_users / prev_effective_users if prev_effective_users > 0 else 0.0
        backhaul_drop_ratio = backhaul_drop_users / prev_effective_users if prev_effective_users > 0 else 0.0

        serving_uav_status = np.any(self.connections, axis=1) if self.n_uavs > 0 else np.array([], dtype=bool)
        serving_uavs = int(np.sum(serving_uav_status))
        isolated_serving_uavs = int(sum(
            1 for uav_idx, has_users in enumerate(serving_uav_status)
            if has_users and uav_idx not in self.routing_paths
        ))
        isolated_serving_uav_ratio = isolated_serving_uavs / serving_uavs if serving_uavs > 0 else 0.0

        coverage_ratio = self.reward_info.get("coverage_ratio", 0.0)
        prev_coverage = getattr(self, 'prev_load_balance_coverage_ratio', 0.0)
        coverage_drop_ratio = max(0.0, prev_coverage - coverage_ratio)

        has_any_backhaul = len(self.routing_paths) > 0
        full_network_disconnect = bool(access_connected_users > 0 and not has_any_backhaul)
        coverage_collapse = bool(prev_coverage > 0.0 and coverage_ratio <= 1e-6)

        instant_outage_intensity = max(
            access_no_backhaul_ratio,
            backhaul_drop_ratio,
            coverage_drop_ratio
        )
        if full_network_disconnect or coverage_collapse:
            instant_outage_intensity = 1.0

        decay = float(np.clip(getattr(self, 'outage_memory_decay', 0.85), 0.0, 0.99))
        self.backhaul_outage_ema = max(
            instant_outage_intensity,
            decay * getattr(self, 'backhaul_outage_ema', 0.0) + (1.0 - decay) * instant_outage_intensity
        )

        if full_network_disconnect:
            self.full_disconnect_streak = getattr(self, 'full_disconnect_streak', 0) + 1
        else:
            self.full_disconnect_streak = 0

        metrics = {
            "access_connected_users": access_connected_users,
            "backhaul_outage_users": access_no_backhaul_users,
            "backhaul_outage_ratio": access_no_backhaul_ratio,
            "service_drop_users": dropped_service_users,
            "service_drop_ratio": service_drop_ratio,
            "backhaul_drop_users": backhaul_drop_users,
            "backhaul_drop_ratio": backhaul_drop_ratio,
            "isolated_serving_uavs": isolated_serving_uavs,
            "isolated_serving_uav_ratio": isolated_serving_uav_ratio,
            "full_network_disconnect": int(full_network_disconnect),
            "full_disconnect_streak": self.full_disconnect_streak,
            "coverage_drop_ratio": coverage_drop_ratio,
            "backhaul_outage_ema": self.backhaul_outage_ema,
            "instant_outage_intensity": instant_outage_intensity,
        }

        self.reward_info.update(metrics)
        self.user_serviced_status = effective_service_status.copy()
        self.prev_effective_user_service_status = effective_service_status.copy()
        self.prev_load_balance_coverage_ratio = coverage_ratio

        return metrics

    def _calculate_relay_backhaul_metrics(self):
        """
        统计中继骨干断裂和回程容量余量。

        重点不是覆盖率结果，而是上一时刻正在承载用户的源UAV是否丢失回程路径，
        以及当前仍在服务用户的回程路径瓶颈容量是否低于安全余量。
        """
        prev_routing_paths = getattr(self, 'previous_routing_paths_snapshot', {})
        prev_connections = getattr(
            self,
            'previous_connections_snapshot',
            np.zeros((self.n_uavs, self.n_users), dtype=bool)
        )

        relay_route_lost_uavs = 0
        relay_route_lost_users = 0
        prev_backhaul_served_users = 0

        for uav_idx, (prev_path, _) in prev_routing_paths.items():
            prev_user_count = int(np.sum(prev_connections[uav_idx])) if uav_idx < prev_connections.shape[0] else 0
            if prev_user_count <= 0:
                continue

            prev_backhaul_served_users += prev_user_count
            if uav_idx not in self.routing_paths:
                relay_route_lost_uavs += 1
                relay_route_lost_users += prev_user_count

        relay_route_loss_ratio = relay_route_lost_users / self.n_users if self.n_users > 0 else 0.0
        relay_route_loss_prev_served_ratio = (
            relay_route_lost_users / prev_backhaul_served_users
            if prev_backhaul_served_users > 0 else 0.0
        )

        target_mbps = max(1e-6, float(getattr(self, 'backhaul_margin_target_mbps', 10.0)))
        serving_bottlenecks_mbps = []
        weighted_margin_deficit = 0.0
        current_backhaul_served_users = 0

        for uav_idx, (path, bottleneck_capacity_bps) in self.routing_paths.items():
            current_user_count = int(np.sum(self.connections[uav_idx]))
            if current_user_count <= 0:
                continue

            bottleneck_mbps = bottleneck_capacity_bps / 1e6
            serving_bottlenecks_mbps.append(bottleneck_mbps)
            current_backhaul_served_users += current_user_count

            margin_deficit = max(0.0, 1.0 - bottleneck_mbps / target_mbps)
            weighted_margin_deficit += current_user_count * margin_deficit

        backhaul_margin_penalty_raw = (
            weighted_margin_deficit / current_backhaul_served_users
            if current_backhaul_served_users > 0 else 0.0
        )

        if serving_bottlenecks_mbps:
            min_serving_backhaul_bottleneck_mbps = float(np.min(serving_bottlenecks_mbps))
            avg_serving_backhaul_bottleneck_mbps = float(np.mean(serving_bottlenecks_mbps))
        else:
            min_serving_backhaul_bottleneck_mbps = 0.0
            avg_serving_backhaul_bottleneck_mbps = 0.0

        metrics = {
            "relay_route_lost_uavs": relay_route_lost_uavs,
            "relay_route_lost_users": relay_route_lost_users,
            "relay_route_loss_ratio": relay_route_loss_ratio,
            "relay_route_loss_prev_served_ratio": relay_route_loss_prev_served_ratio,
            "prev_backhaul_served_users": prev_backhaul_served_users,
            "current_backhaul_served_users": current_backhaul_served_users,
            "backhaul_margin_penalty_raw": backhaul_margin_penalty_raw,
            "min_serving_backhaul_bottleneck_mbps": min_serving_backhaul_bottleneck_mbps,
            "avg_serving_backhaul_bottleneck_mbps": avg_serving_backhaul_bottleneck_mbps,
        }

        self.reward_info.update(metrics)
        return metrics

    def _get_spectral_efficiency_from_sinr(self, sinr_db):
        """根据SINR值从MCS查找表中获取频谱效率"""
        for sinr_threshold, se in self.mcs_table:
            if sinr_db < sinr_threshold:
                return se
        return self.mcs_table[-1][1]


    def _calculate_repulsion_penalty(self):
        """
        计算斥力场惩罚（方案二：物理层面的"社交距离"）
        
        核心思想：
        - 计算所有无人机对之间的距离
        - 对于距离小于安全距离（200m）的无人机对，施加累积惩罚
        - 惩罚强度与距离成反比，距离越近惩罚越大
        - 设置总惩罚上限，防止训练崩溃
        
        返回:
            repulsion_penalty (float): 斥力场惩罚值 [0, 1]
        """
        if self.n_uavs <= 1:
            return 0.0
        
        safe_margin = 200.0  # 安全距离 200米
        max_penalty_per_pair = 1.0  # 单对的最大惩罚
        total_penalty_limit = 2.0  # 总惩罚上限
        
        total_penalty = 0.0
        violation_count = 0
        
        # 计算所有无人机对之间的距离和惩罚
        for i in range(self.n_uavs):
            for j in range(i + 1, self.n_uavs):
                # 计算无人机i和j之间的2D距离
                pos_i = self.uav_positions[i, :2]
                pos_j = self.uav_positions[j, :2]
                distance = np.linalg.norm(pos_i - pos_j)
                
                # 如果距离小于安全距离，计算惩罚
                if distance < safe_margin:
                    # 距离越近，惩罚越大 (使用平方反比关系)
                    normalized_distance = distance / safe_margin
                    pair_penalty = max_penalty_per_pair * (1 - normalized_distance)
                    total_penalty += pair_penalty
                    violation_count += 1
        
        # 应用总惩罚上限，防止极端情况下训练崩溃
        clamped_penalty = min(total_penalty, total_penalty_limit)
        
        # 归一化到[0,1]范围
        normalized_penalty = clamped_penalty / total_penalty_limit
        
        return np.clip(normalized_penalty, 0.0, 1.0)

    def _calculate_load_balancing_penalty(self):
        """
        计算负载均衡惩罚函数（方案B，修正版）
        
        核心思想：
        - 考虑**所有**无人机，无论其是否有回程路径。
        - 计算所有无人机负载（连接的用户数）的方差。
        - 方差越大，说明负载越不均衡，惩罚值越高。
        - 使用理论最大方差进行归一化，确保惩罚值在[0,1]范围内，避免惩罚爆炸。
        
        返回:
            load_balance_penalty (float): 归一化的负载均衡惩罚值 [0, 1]
        """
        if self.n_uavs <= 1:
            return 0.0
        
        # 收集所有无人机的负载
        all_uav_loads = []
        for uav_idx in range(self.n_uavs):
            num_connected_users = np.sum(self.connections[uav_idx])
            all_uav_loads.append(num_connected_users)
        
        # 计算负载方差
        loads_array = np.array(all_uav_loads)
        load_variance = np.var(loads_array)
        
        # 计算理论最大方差用于归一化
        # 最不均衡的情况：一个无人机连接所有已服务的用户，其他无人机连接0个
        # 注意：这里我们应该计算所有被覆盖用户的总数
        total_served_users = self.reward_info.get("effective_connected_users", 0)

        if self.n_uavs > 0 and total_served_users > 0:
            # 构造最不均衡的负载分布：一个UAV承担所有负载，其余为0
            max_uneven_loads = [total_served_users] + [0] * (self.n_uavs - 1)
            max_variance = np.var(max_uneven_loads)
        else:
            max_variance = 0.0 # 如果没有服务用户，则没有不均衡

        # 归一化惩罚值到[0,1]
        if max_variance > 0:
            # 使用平方根来调整惩罚曲线，使得初始阶段的惩罚更敏感
            normalized_penalty = np.sqrt(load_variance / max_variance)
        else:
            normalized_penalty = 0.0
        
        return np.clip(normalized_penalty, 0, 1)

    def _calculate_potential_service_reward(self):
        """
        计算“潜在服务价值”或“区域探索”奖励。
        新逻辑：奖励无人机飞向未被服务的用户所在区域，以此激励探索和扩大覆盖范围。
        此奖励适用于所有无人机，形成一个全局的“引力场”。

        返回:
            potential_service_reward (float): 归一化的潜在服务价值奖励 [0, 1]
        """
        # --- 1. 识别所有未被有效服务的用户 ---
        unserved_user_indices = []
        for user_idx in range(self.n_users):
            # 使用 self.user_serviced_status 来判断，该状态在 step 函数中被更新
            if not self.user_serviced_status[user_idx]:
                unserved_user_indices.append(user_idx)

        # 如果所有用户都已被服务，则没有探索的必要，奖励为0
        if not unserved_user_indices:
            return 0.0

        unserved_user_positions = self.user_positions[unserved_user_indices, :2]

        # --- 2. 为每个无人机计算飞向最近未服务用户的奖励 ---
        total_potential_reward = 0
        for uav_idx in range(self.n_uavs):
            uav_pos = self.uav_positions[uav_idx, :2]
            
            # 计算到所有未服务用户的距离，并找到最小值
            distances = np.linalg.norm(uav_pos - unserved_user_positions, axis=1)
            min_dist_to_unserved = np.min(distances)
            
            # 奖励函数：与到最近未服务用户的距离成反比
            # 使用平方反比关系来强化近距离的奖励，同时避免距离为0时除零
            # 将距离归一化，使其与区域大小无关
            normalized_dist = min_dist_to_unserved / self.area_size
            
            # 设计一个更平滑的奖励函数，避免在远距离时梯度过小
            # 使用 1 / (1 + k*d) 的形式
            reward = 1.0 / (1.0 + normalized_dist * 10) # 乘以10使距离衰减更敏感
            
            total_potential_reward += reward
        
        # --- 3. 归一化 ---
        # 用无人机总数进行归一化，得到一个平均的团队探索奖励
        if self.n_uavs > 0:
            return total_potential_reward / self.n_uavs
        else:
            return 0.0

    def _calculate_map_freshness_penalty(self):
        """
        计算地图新鲜度惩罚。
        惩罚的是整个团队对环境态势感知的衰退。
        
        返回:
            penalty (float): [0, 1] 范围内的惩罚值。
        """
        # 1. 计算地图上所有格子的平均年龄
        # 这里的“年龄”就是自上次访问以来的时间步数
        average_age = np.mean(self.last_visit_time_map)
        
        # 2. 归一化惩罚
        # 一个合理的归一化上限是当一半时间过去后，地图还完全没被探索
        # 当然，也可以使用 max_steps 作为理论最大年龄
        normalization_factor = self.max_steps / 2 
        
        penalty = average_age / normalization_factor
        
        return np.clip(penalty, 0.0, 1.0)

    def _get_grid_coords(self, position_2d):
        """将物理2D坐标转换为访问地图的网格坐标"""
        x, y = position_2d
        gx = int(np.clip(x / self.grid_cell_size, 0, self.grid_map_size[0] - 1))
        gy = int(np.clip(y / self.grid_cell_size, 0, self.grid_map_size[1] - 1))
        return gx, gy

    def _update_visit_map(self):
        """在每个时间步更新所有无人机的访问地图"""
        # 首先，将整个地图的访问时间增加1
        self.last_visit_time_map += 1
        
        # 然后，将当前所有无人机所在的网格的访问时间重置为0
        for uav_pos in self.uav_positions:
            gx, gy = self._get_grid_coords(uav_pos[:2])
            self.last_visit_time_map[gx, gy] = 0

    def _calculate_area_exploration_reward(self):
        """
        计算基于区域新颖度的探索奖励。
        奖励智能体访问那些“长时间未被访问过”的区域。
        """
        total_novelty_score = 0
        
        for uav_pos in self.uav_positions:
            gx, gy = self._get_grid_coords(uav_pos[:2])
            time_since_last_visit = self.last_visit_time_map[gx, gy]
            
            # 使用log函数来平滑奖励，避免时间过长导致奖励爆炸
            # time_since_last_visit为0意味着当前正在访问，新颖度为0
            novelty = np.log1p(time_since_last_visit)
            total_novelty_score += novelty
            
        # 归一化：除以无人机数量和最大可能log(T)
        # 假设最大探索价值在 T=500 步左右达到
        max_novelty = np.log1p(500) * self.n_uavs 
        if max_novelty > 0:
            return np.clip(total_novelty_score / max_novelty, 0, 1)
        return 0.0

    def _calculate_enhanced_qos_reward(self):
        """
        计算增强的QoS奖励 (enhanced_qos)，旨在实现鲁棒的高覆盖率。
        
        结合了:
        1. 骨干网健康度 (Backbone Health): 基于链路质量和角色多样性。
        2. 服务稳定性 (Service Stability): 惩罚中断和服务切换。
        3. 区域新颖度探索 (Area Novelty Exploration): 鼓励探索以避免作弊和局部最优。
        """
        # --- 权重 (可从config中获取，这里使用默认值) ---
        w_backbone_health = 1.0
        w_stability = 0.5
        w_exploration = 0.1
        W_CONNECTIVITY = self.w_connectivity
        W_DIVERSITY = self.w_diversity
        W_COVERAGE = self.w_coverage
        W_DISPERSION = self.w_dispersion
        
        # --- 1. 计算骨干网健康度 ---
        # 复用 network_health_reward 的核心逻辑
        _, health_components = self.calculate_network_health_reward()
        connectivity_score = health_components.get("connectivity_score", 0)
        role_diversity_bonus = health_components.get("role_diversity_bonus", 0)
        effective_coverage_score = health_components.get("effective_coverage_score", 0)
        dispersion_penalty = health_components.get("dispersion_penalty", 0)
        
        backbone_health_reward = (W_CONNECTIVITY * connectivity_score +
                                  W_DIVERSITY * role_diversity_bonus +
                                  W_COVERAGE * effective_coverage_score -
                                  W_DISPERSION * dispersion_penalty)

        # --- 2. 计算服务稳定性惩罚 ---
        qos_metrics = self._calculate_handover_metrics()
        handover_penalty = qos_metrics.get('handover_penalty', 0)
        ping_pong_penalty = qos_metrics.get('ping_pong_penalty', 0)
        outage_penalty = qos_metrics.get('outage_penalty', 0)
        
        stability_penalty = handover_penalty + ping_pong_penalty + outage_penalty
        
        # --- 3. 计算区域探索奖励 ---
        exploration_reward = self._calculate_area_exploration_reward()
        
        # --- 4. 组合最终奖励 ---
        combined_reward = (w_backbone_health * backbone_health_reward -
                           w_stability * stability_penalty +
                           w_exploration * exploration_reward)

        # --- 5. 准备日志 ---
        reward_components = {
            "enhanced_qos_reward": combined_reward,
            "backbone_health_reward": backbone_health_reward,
            "stability_penalty": stability_penalty,
            "exploration_reward": exploration_reward,
            "handover_penalty_applied": handover_penalty,
            "ping_pong_penalty_applied": ping_pong_penalty,
            "outage_penalty_applied": outage_penalty,
        }
        
        return combined_reward, reward_components

    def _calculate_qos_test_reward(self):
        """
        计算QoS测试奖励（qos_test），其特点是区分了部分覆盖和完全覆盖。
        - 完全覆盖：用户通过UAV成功连接到地面基站，获得全额奖励。
        - 部分覆盖：用户仅连接到UAV（UAV无回程），获得较低奖励。
        - 惩罚项：对由于回程链路丢失导致的服务中断进行惩罚。
        """
        full_coverage_score = 0
        partial_coverage_score = 0
        
        for user_idx in range(self.n_users):
            is_partially_covered = False
            is_fully_covered = False
            
            # 检查连接到该用户的所有UAV
            connected_uavs = np.where(self.connections[:, user_idx])[0]
            if len(connected_uavs) > 0:
                is_partially_covered = True # 只要连上UAV就算部分覆盖
                
                # 检查这些UAV中是否至少有一个具有回程路径
                for uav_idx in connected_uavs:
                    if uav_idx in self.routing_paths and self.routing_paths[uav_idx][0]:
                        is_fully_covered = True
                        break # 找到一个即可
            
            if is_fully_covered:
                full_coverage_score += 1
            elif is_partially_covered:
                partial_coverage_score += 1
        
        # 归一化得分
        normalized_full_coverage = full_coverage_score / self.n_users if self.n_users > 0 else 0
        normalized_partial_coverage = partial_coverage_score / self.n_users if self.n_users > 0 else 0
        
        # 获取中断惩罚
        metrics = self._calculate_handover_metrics()
        outage_penalty = metrics['outage_ratio'] * self.w_qos_test_outage
        
        # 组合最终奖励
        qos_test_reward = (self.w_qos_test_coverage_full * normalized_full_coverage +
                           self.w_qos_test_coverage_partial * normalized_partial_coverage -
                           outage_penalty)

        # 记录到日志
        self.reward_info['qos_test_reward'] = qos_test_reward
        self.reward_info['qos_test_full_coverage'] = normalized_full_coverage
        self.reward_info['qos_test_partial_coverage'] = normalized_partial_coverage
        self.reward_info['qos_test_outage_penalty'] = outage_penalty
        
        return qos_test_reward

    def _calculate_stability_aware_reward(self):
        """
        计算稳定性感知奖励 (stability_aware)。
        该奖励函数基于势能奖励塑造 (PBRS) 和运行归一化，以提供稠密且稳定的奖励信号。
        """
        current_coverage = self.reward_info.get('coverage_ratio', 0)
        
        # --- 1. 核心覆盖奖励 (稠密, 基于PBRS) ---
        # r_cov(t) = γ * CoverageRatio(t) - CoverageRatio(t-1)
        dense_coverage_reward_raw = self.gamma * current_coverage - self.previous_coverage_ratio
        
        # --- 2. 关键链路断开惩罚 (事件驱动) ---
        current_serving_uavs = {uav_idx for uav_idx in self.routing_paths if np.sum(self.connections[uav_idx]) > 0}
        lost_service_uavs = self.previous_serving_uavs - current_serving_uavs
        link_loss_penalty_raw = -float(len(lost_service_uavs)) # 原始惩罚值为负数

        # --- 3. 归一化处理 (如果可用) ---
        if self.reward_normalizers:
            # 更新并归一化覆盖奖励
            self.reward_normalizers['coverage'].update(np.array([dense_coverage_reward_raw]))
            mean_cov = self.reward_normalizers['coverage'].mean
            std_cov = np.sqrt(self.reward_normalizers['coverage'].var + 1e-8)
            dense_coverage_reward_norm = (dense_coverage_reward_raw - mean_cov) / std_cov
            
            # 更新并归一化链路丢失惩罚
            self.reward_normalizers['link_loss'].update(np.array([link_loss_penalty_raw]))
            mean_link = self.reward_normalizers['link_loss'].mean
            std_link = np.sqrt(self.reward_normalizers['link_loss'].var + 1e-8)
            link_loss_penalty_norm = (link_loss_penalty_raw - mean_link) / std_link
        else:
            # 如果归一化工具不可用，则使用原始值
            dense_coverage_reward_norm = dense_coverage_reward_raw
            link_loss_penalty_norm = link_loss_penalty_raw

        # --- 4. 组合最终奖励 ---
        # R_final(t) = w_cov * r_cov_norm + w_link * p_link_norm
        final_reward = (self.w_dense_coverage * dense_coverage_reward_norm +
                        self.w_link_loss * link_loss_penalty_norm)
        
        # 更新状态以供下一时间步使用
        self.previous_coverage_ratio = current_coverage
        self.previous_serving_uavs = current_serving_uavs
        
        # 记录到日志
        self.reward_info['stability_aware_reward'] = final_reward
        self.reward_info['stability_dense_coverage_norm'] = dense_coverage_reward_norm
        self.reward_info['stability_link_loss_norm'] = link_loss_penalty_norm
        self.reward_info['stability_lost_service_uavs'] = len(lost_service_uavs)
        
        return final_reward

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
        渲染单帧 - 3D 视图 (优化版)
        【多进程修复版v2】: 在每次渲染前确保matplotlib后端正确配置
        """
        import os
        import threading
        import traceback

        # 多进程安全性保护 - 使用线程锁确保渲染操作的线程安全
        if not hasattr(self, '_render_lock'):
            self._render_lock = threading.Lock()

        with self._render_lock:
            try:
                import matplotlib
                pid = os.getpid()
                current_backend = matplotlib.get_backend()
                
                # 【关键修复】在子进程中，每次渲染前都确保使用Agg后端
                if current_backend.lower() != 'agg':
                    # print(f"[PID: {pid}] 检测到非Agg后端 ({current_backend})，正在切换...")
                    matplotlib.use('Agg', force=True)
                    # print(f"[PID: {pid}] 已切换到Agg后端")
                    import importlib
                    import matplotlib.pyplot
                    importlib.reload(matplotlib.pyplot)
                
                import matplotlib.pyplot as plt
                from matplotlib.patches import Circle
                from mpl_toolkits.mplot3d import Axes3D
                import mpl_toolkits.mplot3d.art3d as art3d
                
            except ImportError as e:
                print(f"[PID: {os.getpid()}] 渲染需要matplotlib库: {e}")
                return self._fallback_render_strategy()
            except Exception as e:
                print(f"[PID: {os.getpid()}] 导入matplotlib时出错: {e}")
                return self._fallback_render_strategy()
        
        if self.fig is None:
            self.fig = plt.figure(figsize=(14, 10)) # 稍微加宽一点
            self.ax = self.fig.add_subplot(111, projection='3d')
        else:
            self.ax.clear()

        # 设置坐标轴 (3D)
        self.ax.set_xlim(0, self.area_size)
        self.ax.set_ylim(0, self.area_size)
        self.ax.set_zlim(0, 300) # Z轴限制：假设最大高度300米
        
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Height (m)')
        
        # 标题只显示当前步数
        self.ax.set_title(f'UAV Relay Network (3D) - Step: {self.current_step}')
        
        # 调整视角 (仰角 30 度，方位角 45 度)
        self.ax.view_init(elev=30, azim=45)

        # 绘制用户簇范围 (投射在 z=0 平面)
        if self.user_movement_model == "rpgm" and hasattr(self, 'cluster_centers_history'):
            try:
                import matplotlib as mpl
                cluster_colors = mpl.colormaps['tab10'].resampled(self.n_clusters)
            except AttributeError:
                cluster_colors = plt.cm.get_cmap('tab10', self.n_clusters)
            
            for i in range(self.n_clusters):
                center = self.cluster_centers_history[i]
                radius = self.cluster_std * 2
                circle = Circle(center, radius, color=cluster_colors(i), alpha=0.1)
                self.ax.add_patch(circle)
                art3d.pathpatch_2d_to_3d(circle, z=0, zdir="z")

        # 绘制用户 (位于地面 z=0)
        if self.user_positions is not None:
            user_x = self.user_positions[:, 0]
            user_y = self.user_positions[:, 1]
            user_z = np.zeros_like(user_x)
            
            if self.user_movement_model == "rpgm" and hasattr(self, 'user_cluster_assignments'):
                colors = [cluster_colors(c) for c in self.user_cluster_assignments]
                self.ax.scatter(user_x, user_y, user_z, c=colors, marker='.', label='Users', alpha=0.6)
            else:
                self.ax.scatter(user_x, user_y, user_z, c='blue', marker='.', label='Users', alpha=0.6)

        # 绘制无人机和连接 (3D)
        if self.uav_positions is not None:
            # 绘制无人机主体
            uav_xs = self.uav_positions[:, 0]
            uav_ys = self.uav_positions[:, 1]
            uav_zs = self.uav_positions[:, 2]
            
            self.ax.scatter(uav_xs, uav_ys, uav_zs, c='red', marker='^', s=100, label='UAVs')
            
            # 为每个无人机绘制投影线和连接
            for i in range(self.n_uavs):
                uav_pos = self.uav_positions[i]
                
                # 投影线 (Ground Projection)
                self.ax.plot([uav_pos[0], uav_pos[0]], [uav_pos[1], uav_pos[1]], [0, uav_pos[2]], 
                             'k--', alpha=0.1, linewidth=0.5)
                
                # 绘制连接线 (UAV -> User)
                if self.connections is not None:
                    # 找出连接的用户
                    connected_users = np.where(self.connections[i])[0]
                    if len(connected_users) > 0:
                        # 批量绘制线段以提高性能
                        for user_idx in connected_users:
                            user_pos = self.user_positions[user_idx]
                            # 线段: UAV(x,y,z) -> User(x,y,0)
                            self.ax.plot([uav_pos[0], user_pos[0]], 
                                         [uav_pos[1], user_pos[1]], 
                                         [uav_pos[2], 0], 
                                         'g-', alpha=0.15, linewidth=0.5)

        # 绘制地面基站 (3D)
        if self.ground_bs_positions is not None:
            bs_x = self.ground_bs_positions[:, 0]
            bs_y = self.ground_bs_positions[:, 1]
            bs_z = self.ground_bs_positions[:, 2]
            self.ax.scatter(bs_x, bs_y, bs_z, c='black', marker='s', s=150, label='Ground BS')

        # 绘制路由路径 (回程链路, 3D)
        if hasattr(self, 'routing_paths'):
            for uav_idx, (path, capacity) in self.routing_paths.items():
                for i in range(len(path) - 1):
                    pos1 = self._get_node_pos(path[i])
                    pos2 = self._get_node_pos(path[i+1])
                    
                    if pos1 is not None and pos2 is not None:
                        # 确保 z 坐标存在 (如果是用户位置可能需要处理，但路由节点通常是 UAV 或 BS)
                        z1 = pos1[2] if len(pos1) > 2 else 0
                        z2 = pos2[2] if len(pos2) > 2 else 0
                        
                        self.ax.plot([pos1[0], pos2[0]], 
                                     [pos1[1], pos2[1]], 
                                     [z1, z2], 
                                     'y--', alpha=0.8, linewidth=2.0)
        
        # 添加图例 (去重)
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize='small')
        
        # 添加统计信息 (在 2D 坐标系中显示)
        if hasattr(self, 'reward_info'):
            reward_info = self.reward_info
            
            info_text = (
                f'Coverage: {reward_info.get("coverage_ratio", 0):.2%}\n'
                f'Eff. Users: {reward_info.get("effective_connected_users", 0)} / {self.n_users}\n'
                f'Conn. UAVs: {reward_info.get("connected_uavs", 0)} / {self.n_uavs}\n'
                f'Avg Hops: {reward_info.get("avg_hops", 0):.2f}\n'
                f'Sys T-put: {reward_info.get("system_throughput_mbps", 0):.2f} Mbps'
            )
            
            # 使用 text2D 在固定的 2D 屏幕坐标上绘制
            self.ax.text2D(0.02, 0.02, info_text, transform=self.ax.transAxes, fontsize=9,
                           verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7))
            
            if reward_info.get("target_coverage_achieved", False):
                self.ax.text2D(0.5, 0.95, '✓ Target Coverage Achieved!', transform=self.ax.transAxes, 
                             color='green', weight='bold', ha='center')
        
        try:
            self.fig.canvas.draw()
        except Exception as e:
            print(f"绘制图形时出错: {e}")
            return np.zeros((600, 800, 3), dtype=np.uint8)
        
        if self.render_mode == "human":
            try:
                plt.pause(0.01)
                return None
            except Exception as e:
                # print(f"人类模式渲染时出错: {e}")
                return None
        elif self.render_mode == "rgb_array":
            try:
                from matplotlib.backends.backend_agg import FigureCanvasAgg
                canvas = FigureCanvasAgg(self.fig)
                canvas.draw()
                image_rgba = np.array(canvas.renderer.buffer_rgba())
                image_rgb = image_rgba[:, :, :3]
                return image_rgb
            except Exception as e:
                print(f"渲染 rgb_array 时出错: {e}")
                return np.zeros((600, 800, 3), dtype=np.uint8)
        else:
            return None
    
    def _fallback_render_strategy(self):
        """
        备用渲染策略：当matplotlib不可用时，生成一个包含文本信息的图像帧。
        这确保了在无GUI服务器上即使渲染失败，也能生成有意义的视频用于调试。
        
        返回:
            frame: 包含调试信息的图像帧 (numpy array)
        """
        try:
            import cv2
        except ImportError:
            # 如果连cv2都没有，返回一个纯黑色的图像
            print("备用渲染策略需要OpenCV (cv2)。请安装：pip install opencv-python")
            return np.zeros((600, 800, 3), dtype=np.uint8)

        # 创建一个黑色背景的图像
        frame = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # 定义文本样式
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)  # 白色
        thickness = 1
        line_type = cv2.LINE_AA

        # 准备要显示的文本信息
        info_lines = [
            "--- Fallback Rendering Mode ---",
            "Matplotlib rendering failed. Switched to data-only view.",
            "",
            f"Step: {self.current_step} / {self.max_steps}"
        ]
        
        # 添加reward_info中的关键指标
        if hasattr(self, 'reward_info') and self.reward_info:
            info_lines.extend([
                "",
                "--- Performance Metrics ---",
                f"Coverage Ratio: {self.reward_info.get('coverage_ratio', 0):.2%}",
                f"Effective Users: {self.reward_info.get('effective_connected_users', 0)} / {self.n_users}",
                f"Connected UAVs: {self.reward_info.get('connected_uavs', 0)} / {self.n_uavs}",
                f"Avg Hops: {self.reward_info.get('avg_hops', 0):.2f}",
                f"Sys Throughput: {self.reward_info.get('system_throughput_mbps', 0):.2f} Mbps",
                f"Health Score: {self.reward_info.get('rt_final_health_score', 0):.3f}"
            ])
        
        # 添加UAV和用户位置信息（简化版）
        if hasattr(self, 'uav_positions') and self.uav_positions is not None:
            info_lines.extend([
                "",
                "--- UAV Positions (x, y, z) ---"
            ])
            for i in range(min(5, self.n_uavs)):  # 只显示前5个UAV
                pos = self.uav_positions[i]
                info_lines.append(f"UAV {i}: ({pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f})")
            if self.n_uavs > 5:
                info_lines.append(f"... and {self.n_uavs - 5} more UAVs")

        # 将文本逐行绘制到图像上
        y_pos = 40
        for line in info_lines:
            if y_pos > 550:  # 防止文本超出图像边界
                break
            cv2.putText(frame, line, (30, y_pos), font, font_scale, color, thickness, line_type)
            y_pos += 30
            
        print(f"备用渲染策略生成了 {frame.shape} 的调试帧")
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
        # 1. 重置随机种子和基本环境状态
        if seed is not None:
            self.seed_val = seed
            self.np_random = np.random.RandomState(seed)
        
        self.current_step = 0
        self.agents = self.possible_agents.copy()
        self.global_bs_cache = {}
        self.last_global_sync_step = -1
        self.hop_map = {i: float('inf') for i in range(self.n_uavs)}
        self._step_communication_cache = None
        self._relay_geometry_state = None

        # Init visit map for exploration reward
        self.last_visit_time_map.fill(0)
        
        # Reset belief map and user serviced status
        self.user_serviced_status.fill(False)
        self.prev_user_serviced_status.fill(False)
        self.discovered_users_this_episode.clear()
        self.discovered_bs_this_episode.clear()
        
        # 2. 使用本类的方法初始化UAV和用户位置
        self.uav_positions = self._init_uav_positions()
        self.user_positions = self._generate_user_positions()
        self._init_user_velocities()
        
        # 3. 初始化移动模型特定的状态
        if self.user_movement_model == "rpgm":
            self._initialize_user_waypoints_rpgm()
        
        # 卡尔曼滤波器已被移除，无需初始化

        # 3. 初始化连接和路由信息
        self.connections = np.zeros((self.n_uavs, self.n_users), dtype=bool)
        self.sinr_matrix = np.zeros((self.n_uavs, self.n_users))
        self.uav_connections = np.zeros((self.n_uavs, self.n_uavs), dtype=bool)
        self.uav_bs_connections = np.zeros((self.n_uavs, self.n_ground_bs), dtype=bool)
        self.routing_paths = {}
        self.handover_count = 0
        self.ping_pong_count = 0
        self.user_serving_uav.fill(-1)
        self.user_serving_sets = [[] for _ in range(self.n_users)]
        self.serving_set_changes = 0
        self.uav_joins_count = 0
        self.uav_leaves_count = 0
        self.user_handover_history = [[] for _ in range(self.n_users)]
        
        # 重置数据包仿真指标
        self.metrics = {k: 0 if k != "total_end_to_end_delay" and k != "total_energy_consumed_mj" else 0.0 for k in self.metrics}
        self.active_packets = []
        self.packet_id_counter = 0

        # 重置稳定性奖励的状态变量
        self.previous_coverage_ratio = 0.0
        self.previous_serving_uavs = set()
        self.prev_effective_user_service_status = np.zeros(self.n_users, dtype=bool)
        self.prev_load_balance_coverage_ratio = 0.0
        self.backhaul_outage_ema = 0.0
        self.full_disconnect_streak = 0

        # 重置路由协议状态
        if ROUTING_PROTOCOLS_AVAILABLE and hasattr(self, 'router') and self.router is not None:
            self.router.reset()
        
        # 4. 更新信道状态、连接和路由。Scenario 7 must first sample its
        # episode-owned energy/failure state, so it performs this materialization
        # once in its reset override instead of exposing a stale preliminary pass.
        defer_topology = bool(
            getattr(self, "_defer_base_topology_materialization", False)
        )
        if not defer_topology:
            self._update_channel_state()
            self._update_uav_connections()
            if self.routing_protocol == 'hggr':
                self.hop_map = self._calculate_hop_map()
            self._compute_routing_paths()  # 使用本类的路由计算
        
        # 4.5 初始化新增的 Reward Shaping 相关变量
        self.previous_bottleneck_capacities.fill(0)
        
        # 5. 获取观测值
        observations = {}
        infos = {}
        defer_base_views = bool(
            getattr(self, "_defer_base_view_materialization", False)
        )
        for agent in self.agents:
            # 注意：这里需要调用父类的_get_observation和_update_observations_dict
            # 为了简化，我们先获取基础观测，再在循环外统一更新
            if not defer_base_views:
                observations[agent] = self._get_observation(agent)
            infos[agent] = {}

        # 6. 更新包含连接和跳数信息的观测
        if not defer_base_views:
            observations = self._update_observations_dict(observations)
            current_state = self._get_state()
            self.state = current_state
        
        # 为每个智能体的info添加正确的state
        for agent in self.agents:
            if not defer_base_views:
                infos[agent]['state'] = current_state.copy()
            else:
                # The wrapping environment replaces this value before return;
                # retain the public insertion order of the info mapping.
                infos[agent]['state'] = None
            infos[agent]['handover_count'] = self.handover_count
            infos[agent]['ping_pong_count'] = self.ping_pong_count
            
        return observations, infos

    def _init_user_velocities(self):
        """初始化用户的速度"""
        for i in range(self.n_users):
            speed = self.np_random.uniform(0, self.user_max_speed)
            angle = self.np_random.uniform(0, 2 * np.pi)
            self.user_velocities[i, 0] = speed * np.cos(angle)  # vx
            self.user_velocities[i, 1] = speed * np.sin(angle)  # vy
            self.user_velocities[i, 2] = 0  # vz, 用户在地面移动

    def _move_users(self):
        """根据选择的移动模型更新用户位置"""
        if self.user_movement_model == "stationary":
            pass  # 用户静止
        elif self.user_movement_model == "rpgm":
            self._update_user_positions_rpgm()
        else:
            # 默认使用随机游走模型
            self._move_users_random_walk()

    def _move_users_random_walk(self):
        """随机游走移动模型：更新用户位置，并处理边界反弹"""
        for i in range(self.n_users):
            self.user_positions[i] += self.user_velocities[i] * self.time_step

            # 边界检测和反弹
            if not (0 <= self.user_positions[i, 0] <= self.area_size):
                self.user_velocities[i, 0] *= -1
                self.user_positions[i, 0] = np.clip(self.user_positions[i, 0], 0, self.area_size)
            
            if not (0 <= self.user_positions[i, 1] <= self.area_size):
                self.user_velocities[i, 1] *= -1
                self.user_positions[i, 1] = np.clip(self.user_positions[i, 1], 0, self.area_size)

    def _update_user_positions_rpgm(self):
        """
        RPGM 移动模型：更新用户位置 - 标准参考点群体移动模型
        
        标准RPGM特点：
        - 簇中心按照设定速度移动
        - 用户围绕其所属簇的参考点移动
        - 支持标准的暂停时间
        """
        # 1. 更新簇中心位置（标准RPGM的参考点移动）
        self._update_cluster_centers_rpgm()

        # 2. 更新用户位置 - 标准RPGM版本
        for i in range(self.n_users):
            # 检查用户暂停状态
            if self.user_pause_times[i] > 0:
                self.user_pause_times[i] -= self.time_step
                continue  # 暂停期间不移动
            
            # 标准RPGM移动：用户跟随其参考点移动
            self.user_positions[i, :2] += self.user_velocities[i, :2] * self.time_step
            
            # 边界检查
            self.user_positions[i, 0] = np.clip(self.user_positions[i, 0], 0, self.area_size)
            self.user_positions[i, 1] = np.clip(self.user_positions[i, 1], 0, self.area_size)

            # 检查是否到达路径点
            dist_to_waypoint = np.linalg.norm(self.user_positions[i, :2] - self.user_waypoints[i])
            if dist_to_waypoint < self.user_max_speed * self.time_step:  # 如果足够接近
                # 获取用户当前所属的簇
                user_cluster = self.user_cluster_assignments[i]
                
                # RPGM：增加跨簇移动概率以模拟更大范围的移动
                if self.np_random.random() < 0.6:  # 60%概率在本簇内移动
                    self._generate_intra_cluster_waypoint(i, user_cluster)
                else:  # 40%概率跨簇移动
                    self._generate_inter_cluster_waypoint(i)
                
                # 设置新的速度
                direction = self.user_waypoints[i] - self.user_positions[i, :2]
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    speed = self.np_random.uniform(self.user_max_speed * 0.5, self.user_max_speed)
                    self.user_velocities[i, :2] = (direction / distance) * speed
                else:
                    self.user_velocities[i, :2] = np.zeros(2)
                
                # 设置暂停时间
                if self.np_random.random() < 0.1:  # 10%概率暂停
                    pause_time = self.np_random.uniform(*self.user_pause_time_range)
                    self.user_pause_times[i] = pause_time

    def _update_cluster_centers_rpgm(self):
        """
        更新簇中心位置 - 标准RPGM参考点移动模型
        
        标准RPGM特点：
        - 簇中心（参考点）按照设定的速度移动
        - 到达目标点后选择新的迁移目标并可能暂停
        - 移动模式更加规律和可预测
        """
        for cluster_idx in range(self.n_clusters):
            # 检查簇中心是否在暂停状态
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
                self._generate_new_cluster_target_rpgm(cluster_idx)
                
                # 更新簇中心的移动速度
                direction = self.cluster_waypoints[cluster_idx] - self.cluster_centers_history[cluster_idx]
                distance = np.linalg.norm(direction)
                if distance > 1e-6:
                    self.cluster_velocities[cluster_idx] = (direction / distance) * self.cluster_migration_speed
                else:
                    self.cluster_velocities[cluster_idx] = np.zeros(2)
                
                # 设置簇中心暂停概率
                if self.np_random.random() < 0.2:  # 20%概率暂停
                    pause_time = self.np_random.uniform(*self.cluster_pause_time_range)
                    self.cluster_pause_times[cluster_idx] = pause_time

    def _generate_new_cluster_target_rpgm(self, cluster_idx):
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

    def _initialize_user_waypoints_rpgm(self):
        """
        初始化用户路径点 - RPGM 模型
        
        特点：
        - 初始化簇中心的移动状态
        - 为用户设置基于簇的路径点
        - 支持簇迁移模式
        """
        # 初始化簇中心的移动状态
        self._initialize_cluster_migration_rpgm()
        
        for i in range(self.n_users):
            # 获取用户所属的簇
            user_cluster = self.user_cluster_assignments[i]
            
            # 80%概率在本簇内移动
            if self.np_random.random() < 0.8:
                self._generate_intra_cluster_waypoint(i, user_cluster)
            else:  # 20%概率跨簇移动
                self._generate_inter_cluster_waypoint(i)
            
            # 设置初始速度
            direction = self.user_waypoints[i] - self.user_positions[i, :2]
            distance = np.linalg.norm(direction)
            if distance > 1e-6:
                speed = self.np_random.uniform(self.user_max_speed * 0.5, self.user_max_speed)
                self.user_velocities[i, :2] = (direction / distance) * speed
            else:
                self.user_velocities[i, :2] = np.zeros(2)
    
    def _initialize_cluster_migration_rpgm(self):
        """
        初始化簇中心的迁移状态 - RPGM 模型
        """
        # 为每个簇中心设置初始移动目标
        for cluster_idx in range(self.n_clusters):
            # 在当前簇中心周围选择一个迁移目标
            current_center = self.cluster_centers_history[cluster_idx]
            
            # 生成迁移目标（在较大范围内）
            migration_range = self.cluster_std * 2.0  # 迁移范围
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

    def _compute_sinr(self, uav_idx, user_idx):
        """
        重写父类方法，使用场景4的精确信道模型计算SINR
        """
        # 使用精确的A2G路径损耗模型
        step_cache = self._current_step_communication_cache()
        if step_cache is not None and "radio" in step_cache:
            return float(step_cache["radio"].access_sinr[0, uav_idx, user_idx])
        path_loss = self._cached_user_path_loss(
            uav_idx, user_idx, step_cache=step_cache
        )
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的UAV-User SINR计算
        sinr_db = self._compute_uav_to_user_sinr(
            uav_idx, user_idx, rx_power, step_cache=step_cache
        )
        
        return sinr_db

    def _calculate_handover_metrics(self):
        """
        计算并返回所有与切换相关的性能指标。
        此函数不计算最终奖励，只负责数据收集。
        
        返回:
            metrics (dict): 包含所有切换指标的字典。
        """
        # 在计算新指标前，首先确定当前时间步的真实服务状态
        current_serviced_status = np.zeros(self.n_users, dtype=bool)
        for user_idx in range(self.n_users):
            user_has_service = False
            for uav_idx in range(self.n_uavs):
                if self.connections[uav_idx, user_idx] and uav_idx in self.routing_paths:
                    if self.sinr_matrix[uav_idx, user_idx] >= self.outage_sinr_threshold_db:
                        user_has_service = True
                        break
            current_serviced_status[user_idx] = user_has_service
        # 1. 计算切换成本
        if not hasattr(self, 'prev_handover_count'):
            self.prev_handover_count = 0
        handover_increment = self.handover_count - self.prev_handover_count
        self.prev_handover_count = self.handover_count
        
        # 2. 计算乒乓切换
        if not hasattr(self, 'prev_ping_pong_count'):
            self.prev_ping_pong_count = 0
        ping_pong_increment = self.ping_pong_count - self.prev_ping_pong_count
        self.prev_ping_pong_count = self.ping_pong_count
        
        # 3. 计算服务中断 (新定义)
        # 中断 = 之前被服务，但现在未被服务的用户
        outage_users = np.sum(self.prev_user_serviced_status & ~current_serviced_status)
        
        # 分母 = 上一时刻被服务的用户总数
        num_previously_served = np.sum(self.prev_user_serviced_status)
        
        outage_ratio = outage_users / num_previously_served if num_previously_served > 0 else 0
        
        # 更新上一时刻的状态
        self.prev_user_serviced_status = current_serviced_status.copy()
        
        # 计算惩罚值
        handover_penalty = handover_increment * self.w_handover
        ping_pong_penalty = ping_pong_increment * self.w_pingpong
        outage_penalty = outage_ratio * self.w_outage
        
        # 4. 将所有指标打包到字典中返回
        metrics = {
            'handover_increment': handover_increment,
            'ping_pong_increment': ping_pong_increment,
            'outage_users': outage_users,
            'outage_ratio': outage_ratio,
            'handover_penalty': handover_penalty,
            'ping_pong_penalty': ping_pong_penalty,
            'outage_penalty': outage_penalty,
        }
        return metrics

    def _get_handover_reward_from_metrics(self, metrics):
        """
        根据已计算的指标计算最终的切换奖励值。
        
        参数:
            metrics (dict): 包含切换指标的字典。
        
        返回:
            handover_reward (float): 最终的切换奖励值。
        """
        coverage_reward = self.reward_info.get('coverage_ratio', 0)
        handover_penalty = metrics['handover_penalty']
        ping_pong_penalty = metrics['ping_pong_penalty']
        outage_penalty = metrics['outage_penalty']
        
        handover_reward = (self.w_throughput * coverage_reward - 
                          handover_penalty - 
                          ping_pong_penalty - 
                          outage_penalty)
        return handover_reward
    
    def _communication_config_signature(self):
        """Return the exact configuration fields used by cached radio calculations."""
        return (
            float(self.tx_power),
            float(self.ground_bs_tx_power),
            float(self.noise_power),
            float(self.carrier_frequency),
            bool(self.use_fdma),
            float(self.bandwidth),
            float(self.aclr_linear),
            float(self.min_sinr),
            int(self.n_uavs),
            int(self.n_users),
            int(self.n_ground_bs),
            str(getattr(self, "environment_type", "urban")),
            tuple(
                (float(threshold), float(efficiency))
                for threshold, efficiency in self.mcs_table
            ),
        )

    def _communication_unavailable_mask(self):
        unavailable = getattr(self, "_is_uav_unavailable", None)
        if unavailable is None:
            return np.zeros(self.n_uavs, dtype=bool)
        return np.asarray(
            [unavailable(index) for index in range(self.n_uavs)], dtype=bool
        )

    def _relay_geometry_signature(self):
        return (
            float(self.carrier_frequency),
            str(getattr(self, "environment_type", "urban")),
        )

    def _run_relay_geometry(self, prepared_velocities, movable_mask):
        """Run the configured deterministic geometry implementation explicitly."""

        result = step_relay_geometry_batch(
            backend=self.relay_geometry_backend,
            uav_positions=np.ascontiguousarray(
                np.asarray(self.uav_positions, dtype=np.float64)[None, ...]
            ),
            user_positions=np.ascontiguousarray(
                np.asarray(self.user_positions, dtype=np.float64)[None, ...]
            ),
            ground_bs_positions=np.ascontiguousarray(
                np.asarray(self.ground_bs_positions, dtype=np.float64)[None, ...]
            ),
            prepared_velocities=np.ascontiguousarray(
                np.asarray(prepared_velocities, dtype=np.float32)[None, ...]
            ),
            movable_mask=np.ascontiguousarray(
                np.asarray(movable_mask, dtype=np.bool_)[None, ...]
            ),
            time_step=float(self.time_step),
            area_size=float(self.area_size),
            height_range=(float(self.height_range[0]), float(self.height_range[1])),
            carrier_frequency=float(self.carrier_frequency),
            environment_type=str(getattr(self, "environment_type", "urban")),
        )
        return result

    def _retain_relay_geometry(self, result):
        next_positions = np.ascontiguousarray(result.next_uav_positions[0])
        self._relay_geometry_state = {
            "uav_positions": next_positions.copy(),
            "user_positions": np.asarray(self.user_positions).copy(),
            "ground_bs_positions": np.asarray(self.ground_bs_positions).copy(),
            "config": self._relay_geometry_signature(),
            "access_path_loss": np.ascontiguousarray(result.access_path_loss[0]),
            "air_path_loss": np.ascontiguousarray(result.air_path_loss[0]),
            "base_path_loss": np.ascontiguousarray(result.base_path_loss[0]),
        }
        return next_positions

    def _relay_geometry_for_current_state(self):
        retained = getattr(self, "_relay_geometry_state", None)
        if (
            retained is not None
            and retained["config"] == self._relay_geometry_signature()
            and np.array_equal(retained["uav_positions"], self.uav_positions)
            and np.array_equal(retained["user_positions"], self.user_positions)
            and np.array_equal(retained["ground_bs_positions"], self.ground_bs_positions)
        ):
            return retained
        result = self._run_relay_geometry(
            np.zeros((self.n_uavs, 3), dtype=np.float32),
            np.zeros(self.n_uavs, dtype=np.bool_),
        )
        self._retain_relay_geometry(result)
        return self._relay_geometry_state

    def _refresh_step_communication_cache(self):
        """Start an exact-state cache for deterministic communication calculations."""
        if bool(getattr(self, "_disable_step_communication_cache", False)):
            self._step_communication_cache = None
            return None
        geometry = self._relay_geometry_for_current_state()
        radio = compute_relay_radio_batch(
            backend=self.relay_geometry_backend,
            uav_positions=np.ascontiguousarray(
                np.asarray(self.uav_positions, dtype=np.float64)[None, ...]
            ),
            user_positions=np.ascontiguousarray(
                np.asarray(self.user_positions, dtype=np.float64)[None, ...]
            ),
            ground_bs_positions=np.ascontiguousarray(
                np.asarray(self.ground_bs_positions, dtype=np.float64)[None, ...]
            ),
            access_path_loss=np.ascontiguousarray(
                geometry["access_path_loss"][None, ...]
            ),
            air_path_loss=np.ascontiguousarray(
                geometry["air_path_loss"][None, ...]
            ),
            base_path_loss=np.ascontiguousarray(
                geometry["base_path_loss"][None, ...]
            ),
            uav_tx_power_dbm=float(self.tx_power),
            ground_bs_tx_power_dbm=float(self.ground_bs_tx_power),
            noise_power_dbm=float(self.noise_power),
            interference_radius=float(self._compute_interference_radius()),
            use_fdma=bool(self.use_fdma),
            aclr_linear=float(self.aclr_linear),
            exclude_receiver_uav=True,
        )
        cache = {
            "uav_positions": np.asarray(self.uav_positions).copy(),
            "user_positions": np.asarray(self.user_positions).copy(),
            "ground_bs_positions": np.asarray(self.ground_bs_positions).copy(),
            "unavailable": self._communication_unavailable_mask(),
            "config": self._communication_config_signature(),
            "radio": radio,
            "user_path_loss": {
                (uav_idx, user_idx): float(
                    geometry["access_path_loss"][uav_idx, user_idx]
                )
                for uav_idx in range(self.n_uavs)
                for user_idx in range(self.n_users)
            },
            "link_path_loss": {},
            "link_sinr": {},
            "link_capacity": {},
        }
        for uav_idx in range(self.n_uavs):
            for peer_idx in range(self.n_uavs):
                path_loss = float(geometry["air_path_loss"][uav_idx, peer_idx])
                cache["link_path_loss"][("uav", uav_idx, "uav", peer_idx)] = path_loss
                cache["link_sinr"][
                    (
                        "uav",
                        uav_idx,
                        "uav",
                        peer_idx,
                        float(self.tx_power - path_loss),
                    )
                ] = float(radio.air_sinr[0, uav_idx, peer_idx])
            for bs_idx in range(self.n_ground_bs):
                path_loss = float(geometry["base_path_loss"][uav_idx, bs_idx])
                cache["link_path_loss"][("uav", uav_idx, "ground_bs", bs_idx)] = path_loss
                cache["link_path_loss"][("ground_bs", bs_idx, "uav", uav_idx)] = path_loss
                cache["link_sinr"][
                    (
                        "uav",
                        uav_idx,
                        "ground_bs",
                        bs_idx,
                        float(self.tx_power - path_loss),
                    )
                ] = float(radio.uav_to_base_sinr[0, uav_idx, bs_idx])
                cache["link_sinr"][
                    (
                        "ground_bs",
                        bs_idx,
                        "uav",
                        uav_idx,
                        float(self.ground_bs_tx_power - path_loss),
                    )
                ] = float(radio.base_to_uav_sinr[0, uav_idx, bs_idx])
        self._step_communication_cache = cache
        return cache

    def _current_step_communication_cache(self):
        """Return the cache only when every result-bearing input is unchanged."""
        if bool(getattr(self, "_disable_step_communication_cache", False)):
            return None
        cache = getattr(self, "_step_communication_cache", None)
        if cache is None:
            return None
        if bool(getattr(self, "_channel_update_cache_active", False)):
            return cache
        if cache["config"] != self._communication_config_signature():
            return None
        if not np.array_equal(cache["uav_positions"], self.uav_positions):
            return None
        if not np.array_equal(cache["user_positions"], self.user_positions):
            return None
        if not np.array_equal(cache["ground_bs_positions"], self.ground_bs_positions):
            return None
        if not np.array_equal(cache["unavailable"], self._communication_unavailable_mask()):
            return None
        return cache

    def _cached_user_path_loss(
        self, uav_idx, user_idx, step_cache=_STEP_CACHE_UNSET
    ):
        cache = (
            self._current_step_communication_cache()
            if step_cache is _STEP_CACHE_UNSET
            else step_cache
        )
        key = (int(uav_idx), int(user_idx))
        if cache is not None and key in cache["user_path_loss"]:
            return cache["user_path_loss"][key]
        path_loss = self._compute_air_to_ground_path_loss(
            self.uav_positions[uav_idx], self.user_positions[user_idx]
        )
        if cache is not None:
            cache["user_path_loss"][key] = path_loss
        return path_loss

    def _cached_directional_path_loss(
        self,
        tx_type,
        tx_idx,
        rx_type,
        rx_idx,
        step_cache=_STEP_CACHE_UNSET,
    ):
        cache = (
            self._current_step_communication_cache()
            if step_cache is _STEP_CACHE_UNSET
            else step_cache
        )
        if bool(getattr(self, "_disable_directional_path_loss_cache", False)):
            cache = None
        key = (str(tx_type), int(tx_idx), str(rx_type), int(rx_idx))
        if cache is not None and key in cache["link_path_loss"]:
            return cache["link_path_loss"][key]
        if tx_type == "uav":
            tx_position = self.uav_positions[tx_idx]
        elif tx_type == "ground_bs":
            tx_position = self.ground_bs_positions[tx_idx]
        else:
            raise ValueError(f"unsupported path-loss transmitter: {tx_type}")
        if rx_type == "uav":
            rx_position = self.uav_positions[rx_idx]
        elif rx_type == "ground_bs":
            rx_position = self.ground_bs_positions[rx_idx]
        else:
            raise ValueError(f"unsupported path-loss receiver: {rx_type}")
        if tx_type == "uav" and rx_type == "uav":
            path_loss = self._compute_air_to_air_path_loss(
                tx_position, rx_position
            )
        elif tx_type == "uav" and rx_type == "ground_bs":
            path_loss = self._compute_air_to_ground_path_loss(
                tx_position, rx_position
            )
        elif tx_type == "ground_bs" and rx_type == "uav":
            path_loss = self._compute_ground_to_air_path_loss(
                tx_position, rx_position
            )
        else:
            raise ValueError(
                f"unsupported path-loss direction: {tx_type}->{rx_type}"
            )
        if cache is not None:
            cache["link_path_loss"][key] = path_loss
        return path_loss

    def _cached_link_sinr(self, tx_type, tx_idx, rx_type, rx_idx, rx_power):
        cache = self._current_step_communication_cache()
        key = (
            str(tx_type),
            int(tx_idx),
            str(rx_type),
            int(rx_idx),
            float(rx_power),
        )
        if cache is not None and key in cache["link_sinr"]:
            return cache["link_sinr"][key]
        sinr = self._compute_link_sinr(tx_type, tx_idx, rx_type, rx_idx, rx_power)
        if cache is not None:
            cache["link_sinr"][key] = sinr
        return sinr

    def _noise_power_linear_mw(self):
        signature = float(self.noise_power)
        cached = getattr(self, "_noise_power_linear_cache", None)
        if cached is None or cached[0] != signature:
            cached = (signature, 10 ** (self.noise_power / 10))
            self._noise_power_linear_cache = cached
        return cached[1]

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
        signature = (
            float(self.tx_power),
            float(self.noise_power),
            float(self.carrier_frequency),
        )
        cached = getattr(self, "_interference_radius_cache", None)
        if cached is not None and cached[0] == signature:
            return cached[1]

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
        
        self._interference_radius_cache = (signature, interference_radius)
        return interference_radius

    def _update_channel_state(self):
        """
        重写父类方法，确保使用场景4的精确SINR计算
        同时在此函数中计算发现奖励，确保使用最新的信道状态
        """
        # 计算所有UAV-用户对的SINR
        cache = self._refresh_step_communication_cache()
        self._channel_update_cache_active = True
        try:
            if cache is None:
                for i in range(self.n_uavs):
                    for j in range(self.n_users):
                        self.sinr_matrix[i, j] = self._compute_sinr(i, j)
            else:
                self.sinr_matrix[...] = cache["radio"].access_sinr[0]
                unavailable = cache["unavailable"]
                if np.any(unavailable):
                    self.sinr_matrix[unavailable, :] = -np.inf
        finally:
            self._channel_update_cache_active = False

        # 记录旧的连接状态，用于切换统计
        old_connections = self.connections.copy()
        old_serving_uav = self.user_serving_uav.copy()

        # 根据模式选择连接更新逻辑
        if self.enable_soft_handover:
            self._update_serving_sets()
            self._update_soft_handover_stats(old_connections)
        else:
            # 传统硬切换逻辑
            self._update_hard_connections()
            self._update_hard_handover_stats(old_serving_uav)

    def _update_hard_connections(self):
        """
        两阶段硬连接分配逻辑：优先保护中继骨干网，再进行用户接入
        
        阶段一：识别潜在的关键中继节点
        阶段二：带保护机制的用户接入分配
        """
        self.connections.fill(False)
        
        # 阶段一：识别潜在的关键中继节点
        critical_relay_nodes = self._identify_critical_relay_nodes()
        
        # 阶段二：以用户为中心的连接分配，带中继节点保护机制
        uav_connections = np.zeros(self.n_uavs, dtype=int)
        user_connected = np.zeros(self.n_users, dtype=bool)
        
        # 为每个用户寻找最佳的服务无人机
        for user_idx in range(self.n_users):
            if user_connected[user_idx]:
                continue
                
            # 找出所有能为该用户提供服务的无人机候选
            candidates = []
            for uav_idx in range(self.n_uavs):
                if (self.sinr_matrix[uav_idx, user_idx] >= self.min_sinr and 
                    uav_connections[uav_idx] < self.max_connections):
                    candidates.append((uav_idx, self.sinr_matrix[uav_idx, user_idx]))
            
            if not candidates:
                continue  # 该用户无法被任何无人机服务
            
            # 按信号质量排序
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            # 应用中继节点保护机制
            selected_uav = self._select_uav_with_relay_protection(
                user_idx, candidates, critical_relay_nodes
            )
            
            if selected_uav is not None:
                self.connections[selected_uav, user_idx] = True
                uav_connections[selected_uav] += 1
                user_connected[user_idx] = True

    def _update_serving_sets(self):
        """动态更新每个用户的服务集，实现软切换"""
        self.connections.fill(False)
        
        for user_idx in range(self.n_users):
            # 1. 识别并排序候选UAV
            candidates = []
            for uav_idx in range(self.n_uavs):
                sinr = self.sinr_matrix[uav_idx, user_idx]
                if sinr >= self.min_sinr:
                    candidates.append({'uav_idx': uav_idx, 'sinr': sinr})
            
            candidates.sort(key=lambda x: x['sinr'], reverse=True)
            
            # 2. 获取当前服务集
            current_set = self.user_serving_sets[user_idx]
            new_set = []

            # 3. 应用迟滞规则构建新的服务集
            if not candidates:
                self.user_serving_sets[user_idx] = []
                continue

            # 将当前服务集中的有效成员加入新集
            current_set_sinrs = {uav_idx: self.sinr_matrix[uav_idx, user_idx] for uav_idx in current_set}
            
            # 过滤掉当前服务集中信号不再满足条件的成员
            valid_current_set = [uav for uav in current_set if current_set_sinrs.get(uav, -np.inf) >= self.min_sinr]
            
            # 合并候选者和当前有效服务者，去重并排序
            all_possible = {c['uav_idx']: c['sinr'] for c in candidates}
            for uav in valid_current_set:
                if uav not in all_possible:
                    all_possible[uav] = current_set_sinrs[uav]
            
            sorted_all = sorted(all_possible.items(), key=lambda item: item[1], reverse=True)

            # 填充新的服务集
            final_set = []
            if sorted_all:
                # 始终保留最好的一个
                best_uav_idx, best_sinr = sorted_all[0]
                final_set.append(best_uav_idx)

                # 从次优的开始，应用迟滞规则
                for uav_idx, sinr in sorted_all[1:]:
                    if len(final_set) >= self.serving_set_size:
                        break
                    
                    # 检查是否在旧的服务集中
                    is_in_old_set = uav_idx in valid_current_set
                    
                    # 检查是否满足迟滞条件
                    can_add = True
                    if not is_in_old_set:
                        # 如果是新成员，需要比当前最差的好一个阈值
                        if final_set:
                            worst_in_set_sinr = self.sinr_matrix[final_set[-1], user_idx]
                            if sinr < worst_in_set_sinr + self.handover_hysteresis_db:
                                can_add = False
                    
                    if can_add:
                        final_set.append(uav_idx)

            self.user_serving_sets[user_idx] = final_set
            
            # 4. 更新connections矩阵
            for uav_idx in final_set:
                self.connections[uav_idx, user_idx] = True

    def _update_hard_handover_stats(self, old_serving_uav):
        """(原_update_handover_stats)根据连接变化，更新硬切换和乒乓切换计数"""
        # 首先，确定当前每个用户的服务UAV
        current_serving_uav = -np.ones(self.n_users, dtype=int)
        for user_idx in range(self.n_users):
            connected_uavs = np.where(self.connections[:, user_idx])[0]
            if len(connected_uavs) > 0:
                # 如果有多个UAV连接，选择SINR最高的那个作为服务UAV
                best_uav = -1
                max_sinr = -np.inf
                for uav_idx in connected_uavs:
                    if self.sinr_matrix[uav_idx, user_idx] > max_sinr:
                        max_sinr = self.sinr_matrix[uav_idx, user_idx]
                        best_uav = uav_idx
                current_serving_uav[user_idx] = best_uav
        
        # 比较新旧服务UAV，统计切换
        for user_idx in range(self.n_users):
            old_uav = old_serving_uav[user_idx]
            new_uav = current_serving_uav[user_idx]

            if old_uav != new_uav and old_uav != -1 and new_uav != -1:
                self.handover_count += 1
                
                # --- 乒乓切换检测 ---
                history = self.user_handover_history[user_idx]
                # 记录格式: (timestamp, from_uav, to_uav)
                history.append((self.current_step, old_uav, new_uav))
                
                # 移除超出时间窗口的历史记录
                while history and history[0][0] < self.current_step - self.ping_pong_window:
                    history.pop(0)
                
                # 检查是否存在 A -> B -> A 模式
                if len(history) >= 2:
                    last_ho = history[-1]
                    second_last_ho = history[-2]
                    # 如果最近两次切换是: (t1, X, A) 和 (t2, A, B)，且 B == X
                    if last_ho[1] == second_last_ho[2] and last_ho[2] == second_last_ho[1]:
                        self.ping_pong_count += 1
                        # 清空历史，避免重复计数
                        self.user_handover_history[user_idx] = []

        self.user_serving_uav = current_serving_uav

    def _update_soft_handover_stats(self, old_connections):
        """根据服务集的变化，更新软切换相关的统计数据"""
        current_connections = self.connections
        
        # 遍历每个用户，比较新旧服务集
        for user_idx in range(self.n_users):
            old_set = set(np.where(old_connections[:, user_idx])[0])
            current_set = set(np.where(current_connections[:, user_idx])[0])
            
            if old_set != current_set:
                # 服务集发生了变化
                self.serving_set_changes += 1
                
                # 计算加入和离开的UAV数量
                joins = len(current_set - old_set)
                leaves = len(old_set - current_set)
                
                self.uav_joins_count += joins
                self.uav_leaves_count += leaves
                
                # 【可选】更精细的乒乓切换检测
                # 可以在这里实现基于服务集变化的乒乓检测逻辑
                # 例如，检测 A 加入 -> A 离开 -> A 再次加入的模式

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
        step_cache = self._current_step_communication_cache()
        path_loss = self._cached_directional_path_loss(
            "uav",
            sender_idx,
            "uav",
            receiver_idx,
            step_cache=step_cache,
        )
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的链路SINR计算（考虑干扰）
        sinr_db = self._cached_link_sinr(
            "uav", sender_idx, "uav", receiver_idx, rx_power
        )
        
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

    def _apply_backhaul_action_guard(self, uav_idx, velocity):
        """
        对关键回程/服务节点应用动作安全层，避免单步动作直接切断已有回程路径。

        该保护只在 load_balance 模式默认启用。它不改变奖励函数，而是在关键 UAV 的
        候选移动会让当前依赖它的回程路径任一链路低于阈值时，将速度缩放到悬停或近悬停。
        """
        if not getattr(self, 'enable_backhaul_action_guard', False):
            return velocity
        if self.reward_type != "load_balance":
            return velocity
        if not hasattr(self, 'routing_paths') or not self.routing_paths:
            return velocity
        if not self._is_backhaul_guarded_uav(uav_idx):
            return velocity

        self.backhaul_guard_checked_actions += 1

        current_position = self.uav_positions[uav_idx].copy()
        proposed_position = current_position + velocity * self.time_step
        proposed_position[0] = np.clip(proposed_position[0], 0, self.area_size)
        proposed_position[1] = np.clip(proposed_position[1], 0, self.area_size)
        proposed_position[2] = np.clip(proposed_position[2], *self.height_range)

        if self._would_preserve_dependent_backhaul_paths(uav_idx, proposed_position):
            return velocity

        self.backhaul_guard_blocked_actions += 1
        reject_scale = float(np.clip(getattr(self, 'backhaul_guard_reject_speed_scale', 0.0), 0.0, 1.0))
        return velocity * reject_scale

    def _is_backhaul_guarded_uav(self, uav_idx):
        """判断该 UAV 是否正在服务用户或作为其他 UAV 的中继骨干。"""
        if uav_idx not in self.routing_paths:
            return False
        if np.sum(self.connections[uav_idx]) > 0:
            return True

        node = ("uav", uav_idx)
        for source_uav, (path, _) in self.routing_paths.items():
            if source_uav == uav_idx:
                continue
            if node in path[1:-1]:
                return True
        return False

    def _would_preserve_dependent_backhaul_paths(self, uav_idx, proposed_position):
        """检查移动后所有依赖该 UAV 的已有回程路径是否仍有链路容量余量。"""
        node = ("uav", uav_idx)
        dependent_paths = [
            path for path, _ in self.routing_paths.values()
            if node in path
        ]
        if not dependent_paths:
            return True

        min_capacity_bps = max(0.0, getattr(self, 'backhaul_guard_min_capacity_mbps', 1.0)) * 1e6
        original_position = self.uav_positions[uav_idx].copy()

        try:
            self.uav_positions[uav_idx] = proposed_position
            for path in dependent_paths:
                for edge_idx in range(len(path) - 1):
                    src_type, src_idx = path[edge_idx]
                    dst_type, dst_idx = path[edge_idx + 1]
                    if (src_type, src_idx) != node and (dst_type, dst_idx) != node:
                        continue

                    forward_capacity = self._get_link_capacity(src_type, src_idx, dst_type, dst_idx)
                    reverse_capacity = self._get_link_capacity(dst_type, dst_idx, src_type, src_idx)

                    if forward_capacity < min_capacity_bps or reverse_capacity < min_capacity_bps:
                        return False
            return True
        finally:
            self.uav_positions[uav_idx] = original_position
    
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
        # 1. Move users and update their state predictions
        # Routing builders replace the outer dict and path records; they do not
        # mutate records retained from the previous authoritative topology.
        self.previous_routing_paths_snapshot = dict(self.routing_paths)
        self.previous_connections_snapshot = self.connections.copy()
        self._move_users()
        
        # 卡尔曼滤波器已被移除，无需更新
        self.backhaul_guard_checked_actions = 0
        self.backhaul_guard_blocked_actions = 0

        # 2. Preserve the existing per-action dtype/order for movement.  The
        # deterministic geometry backend is then evaluated once at the exact
        # resulting positions, avoiding any float32 narrowing of discrete moves.
        next_uav_positions = self.uav_positions.copy()
        for agent_idx, agent in enumerate(self.agents):
            if agent in actions:
                if self.action_space_type == 'discrete':
                    # 【离散动作处理】接收离散的整数动作并使用映射查找对应的速度向量
                    discrete_action = actions[agent]
                    
                    # 检查动作是否有效，以防万一
                    if discrete_action not in self.action_to_velocity:
                        print(f"警告：接收到无效的离散动作 {discrete_action}，将执行悬停。")
                        discrete_action = 0  # 默认为悬停
                        
                    # 从映射中查找对应的速度向量
                    velocity = self.action_to_velocity[discrete_action]
                
                elif self.action_space_type == 'continuous':
                    action_vec = np.asarray(actions[agent], dtype=np.float32)
                    velocity = action_vec * self.max_speed

                velocity = self._apply_backhaul_action_guard(agent_idx, velocity)
                new_position = self.uav_positions[agent_idx] + velocity * self.time_step
                new_position[0] = np.clip(new_position[0], 0, self.area_size)
                new_position[1] = np.clip(new_position[1], 0, self.area_size)
                new_position[2] = np.clip(new_position[2], *self.height_range)
                next_uav_positions[agent_idx] = new_position

        self.uav_positions = next_uav_positions
        self._relay_geometry_state = None
        
        # 3.5. 更新无人机访问地图 (用于探索奖励)
        self._update_visit_map()

        # 3. Update system state based on new positions
        self._update_channel_state()
        self._update_uav_connections()
        
        # 【核心修改】实现分层的路由计算
        # 高层决策：周期性更新全局 hop_map
        if self.routing_protocol == 'hggr' and self.current_step % self.hggr_update_interval == 0:
            self.hop_map = self._calculate_hop_map()
            
        # 【新增】分层可见性：在K step同步时更新全局基站缓存
        if self.current_step % self.hggr_update_interval == 0:
            self._update_global_bs_cache()
        
        # 低层决策：每一步都基于当前（可能过时的）信息计算路径
        self._compute_routing_paths()

        # >>> 插入数据包仿真调用 <<<
        self._simulate_packet_flow()
        
        # 计算路由开销（简化版本 - 基于协议类型）
        if ROUTING_PROTOCOLS_AVAILABLE and hasattr(self, 'router'):
            routing_overhead_this_step = self.router.get_and_reset_overhead()
        else:
            # 使用默认的简化开销模型
            if self.routing_protocol == 'hggr' and self.current_step % self.hggr_update_interval == 0:
                routing_overhead_this_step = self.n_uavs  # HGGR的全局更新开销
            elif self.routing_protocol == 'geographic':
                routing_overhead_this_step = self.n_uavs  # 地理路由的hello消息开销
            else:
                routing_overhead_this_step = 0  # 其他协议的默认开销

        # 7. CALCULATE REWARDS
        # 首先，计算核心覆盖指标并更新 self.reward_info，供塑形奖励函数使用
        self._calculate_coverage_metrics()
        backhaul_outage_metrics = self._calculate_backhaul_outage_metrics()
        relay_backhaul_metrics = self._calculate_relay_backhaul_metrics()
        reward_components = {}
        # 始终计算切换指标以用于日志记录
        #handover_metrics = self._calculate_handover_metrics()

        # 8. 计算系统吞吐量 (在计算完路由和奖励之后)
        system_throughput_mbps, avg_throughput_per_user_mbps = self._calculate_system_throughput()
        self.reward_info['system_throughput_mbps'] = system_throughput_mbps
        self.reward_info['avg_throughput_per_user_mbps'] = avg_throughput_per_user_mbps

        # 11. 更新步数并检查终止/截断条件
        self.current_step += 1
        # 检查是否因为达到最大步数而被截断
        is_truncated = self.current_step >= self.max_steps
        # 【方案A修改】不再因为100%覆盖而提前终止，让episode自然运行到max_steps
        # 这样可以解决GAE问题，并鼓励智能体学会维持最优状态
        # coverage_ratio = self.reward_info.get("coverage_ratio", 0)
        # is_terminated = coverage_ratio >= 1.0
        is_terminated = False  # 永不提前终止

        # 12. 准备返回值
        observations = {}
        rewards = {}
        terminations = {}
        truncations = {}
        infos = {}
        
        # 根据模式计算奖励 - 简化版：只保留三种模式
        # 根据reward_type参数选择奖励类型
        if self.reward_type == "naive":
            # naive模式：直接使用覆盖率作为奖励
            coverage_ratio = self.reward_info.get("coverage_ratio", 0)
            shared_reward = coverage_ratio
        elif self.reward_type == "load_balance":
            # load_balance 模式: 使用门控奖励机制 + 斥力场惩罚
            coverage_ratio = self.reward_info.get("coverage_ratio", 0)
            load_balance_penalty = self._calculate_load_balancing_penalty()
            repulsion_penalty = self._calculate_repulsion_penalty()
            backhaul_outage_ratio = backhaul_outage_metrics.get("backhaul_outage_ratio", 0.0)
            backhaul_drop_ratio = backhaul_outage_metrics.get("backhaul_drop_ratio", 0.0)
            coverage_drop_ratio = backhaul_outage_metrics.get("coverage_drop_ratio", 0.0)
            outage_memory_penalty = backhaul_outage_metrics.get("backhaul_outage_ema", 0.0)
            full_disconnect_penalty = float(backhaul_outage_metrics.get("full_network_disconnect", 0))
            relay_route_loss_ratio = relay_backhaul_metrics.get("relay_route_loss_ratio", 0.0)
            relay_margin_penalty = relay_backhaul_metrics.get("backhaul_margin_penalty_raw", 0.0)
            
            # 组合惩罚项：负载均衡 + 斥力场
            # 使用权重参数来平衡两种惩罚的影响
            w_repulsion = getattr(self, 'w_repulsion', 0.3)  # 默认斥力场权重为0.3
            combined_penalty = self.w_load_balance * load_balance_penalty + w_repulsion * repulsion_penalty
            
            shared_reward = coverage_ratio * (1 - combined_penalty)

            # 回传断联惩罚不乘覆盖率。即使瞬时覆盖率已经掉到0，也保留负梯度，
            # 避免策略把短时断联当作普通低覆盖状态处理。
            robustness_penalty = (
                self.w_backhaul_outage * max(backhaul_outage_ratio, backhaul_drop_ratio) +
                self.w_full_disconnect * full_disconnect_penalty +
                self.w_coverage_drop * coverage_drop_ratio +
                self.w_outage_memory * outage_memory_penalty +
                self.w_relay_break * relay_route_loss_ratio +
                self.w_backhaul_margin * relay_margin_penalty
            )
            shared_reward -= robustness_penalty

            # === 灯塔导航奖励 (Lighthouse/Navigation Reward) ===
            # 替代原有的 catalyst_reward，解决极端位置导致的稀疏性问题
            
            # 1. 检查整个团队是否有任何连接
            team_connected = np.any(self.uav_bs_connections)
            
            nav_reward = 0.0
            
            if not team_connected:
                # === 阶段 A: 求生模式 (Survival Mode) ===
                # 全员未连接，给予基于距离的负奖励（引导向基站移动）
                
                # 计算每个UAV到最近基站的距离
                dists = []
                for uav_pos in self.uav_positions:
                    d = np.linalg.norm(self.ground_bs_positions - uav_pos, axis=1)
                    dists.append(np.min(d))  # 找到离该UAV最近的基站距离
                
                avg_min_dist = np.mean(dists)
                
                # 归一化距离 (使用地图对角线长度)
                map_scale = self.area_size * np.sqrt(2)
                normalized_dist = avg_min_dist / map_scale
                
                # 复用 w_first_contact 作为导航权重
                w_nav = self.w_first_contact
                
                # 给予负奖励：距离越远，惩罚越大
                # 这样梯度下降的方向就是让距离变小
                nav_reward = -1.0 * w_nav * normalized_dist
            else:
                # === 阶段 B: 覆盖模式 (Coverage Mode) ===
                # 已经连接，关闭导航奖励，专注于覆盖
                nav_reward = 0.0
                
            shared_reward += nav_reward

            reward_components.update({
                "gated_reward": shared_reward,
                "load_balance_reward": shared_reward,
                "rt_final_health_score": shared_reward,
                "load_balance_penalty": load_balance_penalty,
                "repulsion_penalty": repulsion_penalty,
                "combined_penalty": combined_penalty,
                "robustness_penalty": robustness_penalty,
                "backhaul_outage_penalty": self.w_backhaul_outage * max(backhaul_outage_ratio, backhaul_drop_ratio),
                "full_disconnect_penalty": self.w_full_disconnect * full_disconnect_penalty,
                "coverage_drop_penalty": self.w_coverage_drop * coverage_drop_ratio,
                "outage_memory_penalty": self.w_outage_memory * outage_memory_penalty,
                "relay_break_penalty": self.w_relay_break * relay_route_loss_ratio,
                "backhaul_margin_penalty": self.w_backhaul_margin * relay_margin_penalty,
                "backhaul_guard_checked_actions": getattr(self, 'backhaul_guard_checked_actions', 0),
                "backhaul_guard_blocked_actions": getattr(self, 'backhaul_guard_blocked_actions', 0),
                "nav_reward": nav_reward  # 记录导航奖励以便观察
            })
        elif self.reward_type == "awareness":
            # awareness模式：覆盖率 + 地图新鲜度 + 负载均衡的综合惩罚
            coverage_ratio = self.reward_info.get("coverage_ratio", 0)
            
            # 计算两种惩罚
            freshness_penalty = self._calculate_map_freshness_penalty()
            balance_penalty = self._calculate_load_balancing_penalty()
            
            # 组合成综合惩罚项
            comprehensive_penalty = (self.w_freshness_penalty * freshness_penalty +
                                     self.w_load_balance * balance_penalty)
            
            # 应用乘法结构
            shared_reward = coverage_ratio * (1 - np.clip(comprehensive_penalty, 0, 1))
            
            # 更新日志
            reward_components["freshness_penalty"] = freshness_penalty
            reward_components["awareness_reward"] = shared_reward
        elif self.reward_type == "test_reward":
            # ===== test_reward Ver2.0: 基于真实物理能耗模型 =====
            
            # --- Part 1: 基于 IEEE TWC (Zeng et al. 2019) 的物理能耗惩罚 ---
            total_power_watts = 0.0
            
            for i, agent in enumerate(self.agents):
                if agent in actions:
                    # 获取速度 (增加安全检查)
                    if self.action_space_type == 'discrete':
                        action = actions[agent]
                        if action in self.action_to_velocity:
                            vel = self.action_to_velocity[action]
                        else:
                            # 默认悬停
                            vel = self.action_to_velocity[0]
                    else:
                        vel = actions[agent] * self.max_speed
                    
                    v_xy = np.linalg.norm(vel[:2])
                    v_z = vel[2] # 保留符号，虽然我们在计算功率时用了abs
                    
                    # 计算该无人机的瞬时功率 (W)
                    power = self._calculate_power_consumption(v_xy, v_z)
                    
                    # 我们主要惩罚 "额外的运动能耗"，而不是悬停能耗
                    # 因此减去悬停功率 (v=0时的功率)
                    # P_hover = P0 + Pi ≈ 168W
                    # 这样静止时的惩罚为 0
                    p_hover = self.P0 + self.Pi
                    extra_power = max(0, power - p_hover)
                    
                    total_power_watts += extra_power

            # 归一化处理
            # 这里的 max_power_consumption 也是减去悬停功率后的值
            max_extra_power = self.max_power_consumption - (self.P0 + self.Pi)
            # 防止除以零或过小
            if max_extra_power <= 1e-3:
                max_extra_power = 1.0
            
            normalized_energy_penalty = total_power_watts / (self.n_uavs * max_extra_power)
            
            # 【安全保护】防止惩罚值爆炸
            if normalized_energy_penalty > 2.0:
                # print(f"Warning: Energy penalty exploded ({normalized_energy_penalty:.2f}). Total Watts: {total_power_watts:.2f}, Max Extra/UAV: {max_extra_power:.2f}")
                normalized_energy_penalty = 2.0 # 软截断
            
            # --- Part 2: 稳定性迟滞惩罚 (Hysteresis) ---
            # 比较当前连接状态与上一步连接状态
            current_connected = set()
            prev_connected = getattr(self, '_prev_connected_ues', set())
            
            for user_idx in range(self.n_users):
                for uav_idx in range(self.n_uavs):
                    if self.sinr_matrix[uav_idx, user_idx] >= self.min_sinr:
                        current_connected.add(user_idx)
                        break
            
            # 计算新上线和掉线的用户数量
            new_connected = current_connected - prev_connected  # 新上线
            disconnected = prev_connected - current_connected   # 掉线
            
            # 迟滞系数：掉线惩罚是上线收益的2.5倍
            hysteresis_ratio = 2.5
            connection_gain = len(new_connected) * 1.0
            disconnection_loss = len(disconnected) * hysteresis_ratio
            
            # 归一化迟滞惩罚到 [-1, 1]
            # 正值表示净收益，负值表示净损失
            if self.n_users > 0:
                hysteresis_score = (connection_gain - disconnection_loss) / self.n_users
            else:
                hysteresis_score = 0.0
            hysteresis_score = np.clip(hysteresis_score, -1.0, 1.0)
            
            # 保存当前状态用于下一步
            self._prev_connected_ues = current_connected.copy()
            
            # --- Part 3: 组合最终奖励 ---
            # 基础覆盖率奖励 (使用已计算的覆盖率)
            coverage_reward = self.reward_info.get("coverage_ratio", 0)
            
            # 组合公式：
            # R = w_cov * coverage - w_energy * energy_penalty + w_hysteresis * hysteresis_score
            w_coverage = 0.5
            # w_energy 建议 0.05 ~ 0.1, 使用初始化时设定的值
            w_energy = self.w_energy 
            w_hysteresis = 0.3
            
            shared_reward = (w_coverage * coverage_reward - 
                            w_energy * normalized_energy_penalty + 
                            w_hysteresis * hysteresis_score)
            
            # 更新日志
            reward_components["test_reward"] = shared_reward
            reward_components["energy_penalty"] = normalized_energy_penalty
            reward_components["hysteresis_score"] = hysteresis_score
            reward_components["coverage_component"] = coverage_reward
            reward_components["total_power_watts"] = total_power_watts # 记录总功率以便调试
        else:
            # 默认使用naive模式
            coverage_ratio = self.reward_info.get("coverage_ratio", 0)
            shared_reward = coverage_ratio
        
        # 所有智能体接收完全相同的共享团队奖励
        for agent in self.agents:
            rewards[agent] = shared_reward

        # Visualization consumes these snapshots from every agent's reward_info.
        # Build them once per step and share the same read-only-by-contract values
        # instead of copying the full topology once for every agent.
        connections_snapshot = self.connections.copy()
        routing_paths_snapshot = dict(self.routing_paths)
        defer_base_views = bool(
            getattr(self, "_defer_base_view_materialization", False)
        )

        # 13. 获取新的观测并填充返回值
        for agent_idx, agent in enumerate(self.agents):
            if not defer_base_views:
                observations[agent] = self._get_observation(agent)

            # 【核心修正】正确设置 termination 和 truncation
            terminations[agent] = is_terminated
            truncations[agent] = is_truncated
            
            # 【关键修复】创建统一的 reward_info 字典，包含所有性能指标
            # 合并基础覆盖指标和网络健康度组件
            unified_reward_info = self.reward_info.copy()  # 包含基础覆盖指标
            unified_reward_info.update(reward_components)  # 添加网络健康度组件
            
            # 添加额外的性能指标
            unified_reward_info.update({
                "connectivity_ratio": len(self.routing_paths) / self.n_uavs if self.n_uavs > 0 else 0,
                "total_connected_users": sum(np.sum(self.connections[i]) for i in range(self.n_uavs)),
                "uavs_with_backhaul": len(self.routing_paths),
                "system_throughput_mbps": system_throughput_mbps,
                "avg_throughput_per_user_mbps": avg_throughput_per_user_mbps,
                "connections": connections_snapshot,
                "routing_paths": routing_paths_snapshot,
            })
            
            # 将统一的奖励信息放入 info 字典，用于监控、调试和可视化
            infos[agent] = {
                "reward_info": unified_reward_info,
                "coverage_ratio": unified_reward_info.get("coverage_ratio", 0),
                "connectivity_ratio": unified_reward_info.get("connectivity_ratio", 0),
            # 【关键修复】：添加当前UAV位置到info中，避免环境重置后位置丢失
            "uav_positions": self.uav_positions.copy(),
            # 添加路由开销信息
                "routing_overhead": routing_overhead_this_step,
                "routing_protocol": self.routing_protocol,
            }
        
        # 7. 更新观测值（在循环外一次性完成）
        if not defer_base_views:
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

    def _calculate_entity_discovery_reward(self, current_observations):
        """
        Calculates a one-time bonus for discovering new users or base stations.
        This is based on the collective observations of all UAVs.
        """
        newly_discovered_users = 0
        newly_discovered_bs = 0
        
        # This approach is slightly inefficient as it re-calculates local entities,
        # but it ensures that the discovery is based purely on what agents can *see*.
        
        # Check for newly discovered users
        currently_visible_users = set()
        for agent_idx in range(self.n_uavs):
            local_users = self._get_local_users(agent_idx)
            for user_idx, _ in local_users:
                currently_visible_users.add(user_idx)
        
        new_users = currently_visible_users - self.discovered_users_this_episode
        if new_users:
            newly_discovered_users = len(new_users)
            self.discovered_users_this_episode.update(new_users)

        # Check for newly discovered base stations
        currently_visible_bs = set()
        for agent_idx in range(self.n_uavs):
            local_bs = self._get_local_bs(agent_idx)
            for bs_idx, _ in local_bs:
                currently_visible_bs.add(bs_idx)

        new_bs = currently_visible_bs - self.discovered_bs_this_episode
        if new_bs:
            newly_discovered_bs = len(new_bs)
            self.discovered_bs_this_episode.update(new_bs)
            
        # The reward is normalized by the total number of entities to be discovered
        user_discovery_reward = newly_discovered_users / self.n_users if self.n_users > 0 else 0
        bs_discovery_reward = newly_discovered_bs / self.n_ground_bs if self.n_ground_bs > 0 else 0
        
        total_discovery_reward = user_discovery_reward + bs_discovery_reward

        return total_discovery_reward

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

    def _compute_sinr_at_pos(self, uav_idx, user_pos_3d):
        """
        计算无人机到指定3D位置的SINR
        
        参数:
            uav_idx: 无人机索引
            user_pos_3d: 目标位置的3D坐标 [x, y, z]
            
        返回:
            sinr_db: SINR值 (dB)
        """
        uav_pos = self.uav_positions[uav_idx]
        
        # 使用精确的A2G路径损耗模型
        path_loss = self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)
        
        # 计算接收功率
        rx_power = self.tx_power - path_loss
        
        # 使用精确的UAV-User SINR计算
        sinr_db = self._compute_uav_to_user_sinr_at_pos(uav_idx, user_pos_3d, rx_power)
        
        return sinr_db

    def _compute_uav_to_user_sinr_at_pos(self, uav_idx, user_pos_3d, rx_power):
        """计算UAV到指定位置通信的精确SINR"""
        interference_radius = self._compute_interference_radius()
        uav_interference_weight = 1.0
        
        interference_powers_linear = []
        
        # 计算来自其他UAV的干扰
        for i in range(self.n_uavs):
            if i != uav_idx:
                interferer_pos = self.uav_positions[i]
                dist_to_user = self._compute_distance(interferer_pos, user_pos_3d)
                if dist_to_user > interference_radius:
                    continue
                
                interferer_path_loss = self._compute_air_to_ground_path_loss(interferer_pos, user_pos_3d)
                interferer_rx_power_dbm = self.tx_power - interferer_path_loss
                interferer_rx_power_linear = 10**(interferer_rx_power_dbm / 10)
                
                weighted_interference_power = interferer_rx_power_linear * uav_interference_weight
                
                if self.use_fdma:
                    interference_powers_linear.append(weighted_interference_power * self.aclr_linear)
                else:
                    interference_powers_linear.append(weighted_interference_power)
        
        total_interference_linear = np.sum(interference_powers_linear)
        noise_power_linear = 10 ** (self.noise_power / 10)
        interference_plus_noise_linear = noise_power_linear + total_interference_linear
        interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
        
        sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db


    def _get_observation(self, agent):
        """Materialize one view under one exact cache validation."""
        cache = self._current_step_communication_cache()
        if cache is None:
            return self._get_observation_cached_body(agent)
        previous = bool(getattr(self, "_channel_update_cache_active", False))
        self._channel_update_cache_active = True
        try:
            return self._get_observation_cached_body(agent)
        finally:
            self._channel_update_cache_active = previous

    def _get_observation_cached_body(self, agent):
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

        if (
            nearest_neighbor_pos is not None
            and min_dist_to_neighbor <= self.observation_radius
        ):
            # 归一化距离
            normalized_dist = min_dist_to_neighbor / self.area_size
            # 归一化相对位置 (x, y)
            relative_pos = (nearest_neighbor_pos[:2] - own_position[:2]) / self.area_size
            nearest_uav_obs = np.array([normalized_dist, relative_pos[0], relative_pos[1]])
        
        obs_components.append(nearest_uav_obs)
        
        # 2. 自身状态信息 (5维) - 连接状态、路由状态、连接用户数、跳数、到最近基站的相对位置
        self_state = np.zeros(5)
        
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
        
        # 到最近基站的归一化相对位置向量 (包含距离和方向信息)
        min_bs_dist_sq = float('inf')
        relative_pos_to_bs = np.zeros(2)

        max_bs_dist_sq = float(self.observation_radius) ** 2
        for bs_idx in range(self.n_ground_bs):
            bs_pos = self.ground_bs_positions[bs_idx]
            # Use the same 3-D radius contract as all other local entity views.
            dist_sq = np.sum(np.square(own_position - bs_pos))
            if dist_sq <= max_bs_dist_sq and dist_sq < min_bs_dist_sq:
                min_bs_dist_sq = dist_sq
                # 计算归一化的相对位置向量
                relative_pos = (bs_pos[:2] - own_position[:2]) / self.area_size
                relative_pos_to_bs = relative_pos
        
        self_state[3] = relative_pos_to_bs[0]  # Rel Pos X
        self_state[4] = relative_pos_to_bs[1]  # Rel Pos Y
        
        obs_components.append(self_state)
        
        # 3. 局部用户观测
        local_users = self._get_local_users(agent_idx)
        
        if self.predictive_handover:
            user_obs = np.zeros(self.max_observed_users * 7)
            obs_dim_per_user = 7
        elif self.enable_soft_handover:
            user_obs = np.zeros(self.max_observed_users * 6)
            obs_dim_per_user = 6
        else:
            user_obs = np.zeros(self.max_observed_users * 5)
            obs_dim_per_user = 5

        for i, (user_idx, sinr_db) in enumerate(local_users):
            if i >= self.max_observed_users:
                break
            
            user_pos = self.user_positions[user_idx]
            relative_pos = (user_pos[:2] - own_position[:2]) / self.area_size
            normalized_sinr = np.clip((sinr_db + 10) / 50, 0, 1)
            is_connected_to_self = 1.0 if self.connections[agent_idx, user_idx] else 0.0
            is_serviced_by_any = 1.0 if self.user_serviced_status[user_idx] else 0.0 # 新增状态
            
            start_idx = i * obs_dim_per_user
            
            base_obs = [relative_pos[0], relative_pos[1], normalized_sinr, is_connected_to_self, is_serviced_by_any]
            
            if self.enable_soft_handover:
                # 添加服务簇大小作为观测维度
                serving_set_size = len(self.user_serving_sets[user_idx])
                normalized_set_size = serving_set_size / self.serving_set_size
                base_obs.append(normalized_set_size)

            user_obs[start_idx : start_idx + len(base_obs)] = base_obs

            if self.predictive_handover:
                # 卡尔曼滤波器已移除，使用零值填充预测状态
                # 以保持观测空间维度不变
                normalized_predicted_sinr_self = 0.0
                normalized_predicted_sinr_neighbor = 0.0
                user_obs[start_idx+4:start_idx+6] = [normalized_predicted_sinr_self, normalized_predicted_sinr_neighbor]

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
        
        # 4. 分层基站观测 (max_observed_bs * 4维) - 结合局部观测和全局缓存
        bs_obs = np.zeros(self.max_observed_bs * 4)
        filled_slots = 0
        
        # 4.1 首先填充当前直接观测到的基站
        local_bs = self._get_local_bs(agent_idx)
        for bs_idx, dist in local_bs:
            if filled_slots >= self.max_observed_bs:
                break
                
            bs_pos = self.ground_bs_positions[bs_idx]
            # 相对位置 (x, y, z) - 归一化
            relative_pos = bs_pos - own_position
            relative_pos[:2] /= self.area_size
            relative_pos[2] /= self.height_range[1] # 与全局状态归一化保持一致
            
            # 【语义修复】对于直接观测到的基站，第4维始终为1.0（可见性标志位）
            # 这确保了与可见性标志位定义的一致性：1.0表示位置信息有效，0.0表示无效填充
            visibility_flag = 1.0  # 直接观测到的基站始终标记为可见
            
            start_idx = filled_slots * 4
            bs_obs[start_idx:start_idx+4] = [relative_pos[0], relative_pos[1], relative_pos[2], visibility_flag]
            filled_slots += 1
        
        # 4.2 如果还有剩余观测位，从全局缓存中补充
        if filled_slots < self.max_observed_bs and len(self.global_bs_cache) > 0:
            # 获取当前已观测到的基站集合
            observed_bs_set = {bs_idx for bs_idx, _ in local_bs}
            
            # 从全局缓存中添加未直接观测到的基站
            for bs_idx, (normalized_pos, visibility_flag) in self.global_bs_cache.items():
                if filled_slots >= self.max_observed_bs:
                    break
                if bs_idx in observed_bs_set:
                    continue  # 跳过已经直接观测到的基站
                
                # 从缓存中获取归一化位置（相对于地图中心）
                # 需要转换为相对于当前UAV的位置
                map_center_pos = np.array([0.5, 0.5, 0])  # 地图中心的归一化坐标
                own_normalized_pos = np.array([
                    own_position[0] / self.area_size,
                    own_position[1] / self.area_size, 
                    own_position[2] / self.height_range[1]
                ])
                
                # 计算相对位置：缓存位置 - 当前UAV位置
                relative_pos_cached = normalized_pos - own_normalized_pos + map_center_pos
                
                # 连接状态：从全局缓存获取的基站标记为不可连接（距离太远）
                connection_status = 0.0
                
                # 可见性标志：使用缓存中的可见性标志
                # 注意：第4维现在存储的是可见性标志而不是连接状态
                start_idx = filled_slots * 4
                bs_obs[start_idx:start_idx+4] = [
                    relative_pos_cached[0], 
                    relative_pos_cached[1], 
                    relative_pos_cached[2], 
                    visibility_flag  # 全局同步的可见性标志
                ]
                filled_slots += 1
        
        obs_components.append(bs_obs)

        # 5. 局部过载无人机观测
        overloaded_obs = self._get_local_overloaded_uavs(agent_idx)
        obs_components.append(overloaded_obs)

        # 6. 当前步数 (1维)
        step_normalized = np.array([self.current_step / self.max_steps])
        obs_components.append(step_normalized)
        
        # 组合所有观测
        obs = np.concatenate(obs_components)
        
        # 动作掩码（这里我们不限制动作，所以全为1）
        action_mask_dim = self.n_discrete_actions if self.action_space_type == 'discrete' else 3
        action_mask = np.ones(action_mask_dim)
        
        return {
            "obs": obs.astype(np.float32, copy=False),
            "action_mask": action_mask.astype(np.float32, copy=False),
        }




    def _get_local_overloaded_uavs(self, agent_idx):
        """
        获取指定无人机侦测范围内的过载无人机列表。
        """
        overloaded_uavs = []
        own_pos = self.uav_positions[agent_idx]
        
        # 定义过载阈值
        ideal_avg_load = self.n_users / self.n_uavs
        overload_threshold = ideal_avg_load * 1.5

        for other_idx in range(self.n_uavs):
            if other_idx == agent_idx:
                continue

            # 检查是否过载
            load = np.sum(self.connections[other_idx])
            if load > overload_threshold:
                # 检查是否在观测范围内
                other_pos = self.uav_positions[other_idx]
                dist = np.linalg.norm(own_pos - other_pos)
                if dist <= self.observation_radius:
                    overloaded_uavs.append({
                        'idx': other_idx,
                        'pos': other_pos,
                        'load': load,
                        'dist': dist
                    })
        
        # 按距离排序
        overloaded_uavs.sort(key=lambda x: x['dist'])

        # 填充观测向量
        obs = np.zeros(self.max_observed_overloaded_uavs * 3)
        for i, uav_info in enumerate(overloaded_uavs):
            if i >= self.max_observed_overloaded_uavs:
                break
            
            relative_pos = (uav_info['pos'][:2] - own_pos[:2]) / self.area_size
            normalized_load = uav_info['load'] / self.max_connections

            start_idx = i * 3
            obs[start_idx : start_idx + 3] = [relative_pos[0], relative_pos[1], normalized_load]
            
        return obs

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

    def _simulate_packet_flow(self):
        """
        模拟数据包的生成、转发、到达和丢失，用于一个时间步。
        这个方法负责填充self.metrics字典中的性能指标。
        """
        # --- 1. 生成新数据包 ---
        # 假设每个服务用户且有有效回程路径的UAV在每个时间步生成一个数据包
        for uav_idx in range(self.n_uavs):
            # UAV是数据源当且仅当它有路由路径且连接了至少一个用户
            is_serving_users = np.sum(self.connections[uav_idx]) > 0
            if uav_idx in self.routing_paths and is_serving_users:
                path, _ = self.routing_paths[uav_idx]
                
                new_packet = {
                    'id': self.packet_id_counter,
                    'source_uav': uav_idx,
                    'path': path,  # 路由在创建时就固定
                    'path_idx': 0,  # 在路径列表中的当前位置
                    'creation_time': self.current_step,
                    'hop_count': 0
                }
                
                self.active_packets.append(new_packet)
                self.metrics["packets_sent"] += 1
                self.packet_id_counter += 1
                
                # 源UAV发送新数据包的能耗成本
                self.metrics["total_energy_consumed_mj"] += self.ENERGY_TX_MJ

        # --- 2. 推进、交付或丢弃现有数据包 ---
        packets_to_remove = []
        for packet in self.active_packets:
            current_node_type, current_node_idx = packet['path'][packet['path_idx']]
            next_path_idx = packet['path_idx'] + 1

            # 防护：如果路径已经到达末尾
            if next_path_idx >= len(packet['path']):
                packets_to_remove.append(packet)
                continue
            
            next_hop_type, next_hop_idx = packet['path'][next_path_idx]

            # === 关键检查：路由断开 (修正版：基于动态单向链路容量) ===
            # 验证数据包在当前时刻，从当前节点到下一跳的链路是否仍然有效
            # 这应该使用与路由算法相同的标准，即检查单向链路容量
            link_capacity = self._get_link_capacity(current_node_type, current_node_idx, next_hop_type, next_hop_idx)

            if link_capacity <= 0:
                # 路径断开！数据包被丢弃
                self.metrics["route_disconnections"] += 1
                packets_to_remove.append(packet)
                continue  # 移动到下一个数据包

            # 如果链路存在，数据包成功转发
            # 能耗成本：当前节点接收 + 向下一跳发送
            self.metrics["total_energy_consumed_mj"] += self.ENERGY_RX_MJ + self.ENERGY_TX_MJ
            
            # === 检查到达 ===
            if next_hop_type == 'ground_bs':
                # 数据包已成功到达目的地！
                self.metrics["packets_arrived"] += 1
                
                # 基于这次成功传输更新指标
                delay = (self.current_step + 1) - packet['creation_time']
                self.metrics["total_end_to_end_delay"] += delay
                self.metrics["total_hop_count"] += packet['hop_count'] + 1  # +1为最后一跳
                
                # 标记为从活跃列表中移除
                packets_to_remove.append(packet)
                
                # 最终能耗成本：只在BS接收（无需再发送）
                self.metrics["total_energy_consumed_mj"] -= self.ENERGY_TX_MJ  # 修正无需再发送的情况
            else:
                # === 数据包被中继 ===
                # 数据包还没到达BS，所以我们只是推进它
                packet['path_idx'] = next_path_idx
                packet['hop_count'] += 1

        # --- 3. 清理 ---
        # 从活跃列表中移除已交付或丢弃的数据包
        if packets_to_remove:
            self.active_packets = [p for p in self.active_packets if p not in packets_to_remove]
    
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
        cache_key = (node1_type, int(node1_idx), node2_type, int(node2_idx))
        step_cache = self._current_step_communication_cache()
        if step_cache is not None and cache_key in step_cache["link_capacity"]:
            return step_cache["link_capacity"][cache_key]
        cache = getattr(self, "_routing_link_capacity_cache", None)
        if cache is not None and cache_key in cache:
            return cache[cache_key]

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
        
        # 根据链路类型选择正确的路径损耗计算和发射功率
        if node1_type == "uav" and node2_type == "uav":
            # 空对空通信：UAV到UAV - 使用精确的A2A自由空间模型
            tx_power = self.tx_power  # 使用UAV发射功率
        elif node1_type == "uav" and node2_type == "ground_bs":
            # 上行链路：UAV到地面基站 - 使用A2G模型
            tx_power = self.tx_power  # 使用UAV发射功率
        elif node1_type == "ground_bs" and node2_type == "uav":
            # 下行链路：地面基站到UAV - 使用G2A模型
            tx_power = self.ground_bs_tx_power  # 使用基站发射功率
        else:
            return 0  # 不支持的连接类型
        path_loss = self._cached_directional_path_loss(
            node1_type,
            node1_idx,
            node2_type,
            node2_idx,
            step_cache=step_cache,
        )
        
        # 计算接收功率 (dBm)
        rx_power = tx_power - path_loss
        
        # 计算SINR (dB) - 考虑实际干扰情况
        sinr_db = self._cached_link_sinr(
            node1_type, node1_idx, node2_type, node2_idx, rx_power
        )
        
        # 检查SINR是否满足最小阈值
        if sinr_db < self.min_sinr:
            capacity = 0
            if step_cache is not None:
                step_cache["link_capacity"][cache_key] = capacity
            if cache is not None:
                cache[cache_key] = capacity
            return capacity
        
        # 确定用于计算容量的带宽
        if self.use_fdma:
            # FDMA模式下，假设总带宽被平均分配给每个UAV用于其回程链路
            link_bandwidth = self.bandwidth / self.n_uavs
        else:
            # 非FDMA模式（同频干扰）下，所有链路共享全部带宽，但受到同频干扰影响
            # 这里使用全部带宽，干扰影响已经在SINR计算中体现
            link_bandwidth = self.bandwidth
            
        # 使用AMC模型计算容量
        spectral_efficiency = self._get_spectral_efficiency_from_sinr(sinr_db)
        capacity = link_bandwidth * spectral_efficiency

        if step_cache is not None:
            step_cache["link_capacity"][cache_key] = capacity
        if cache is not None:
            cache[cache_key] = capacity
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
            step_cache = self._current_step_communication_cache()
            # 计算来自其他UAV的干扰
            for i in range(self.n_uavs):
                # 排除发送方和接收方自身
                if (tx_type == "uav" and i == tx_idx) or \
                   (rx_type == "uav" and i == rx_idx):
                    continue
                
                interferer_pos = self.uav_positions[i]
                
                # 原则1：检查距离 - 考虑干扰半径内的所有无人机
                dist_to_receiver = self._compute_distance(interferer_pos, rx_pos)
                if dist_to_receiver > interference_radius:
                    continue  # 干扰源太远，忽略
                
                # 原则3：为干扰链路计算正确的路径损耗
                if rx_type == "uav":
                    interferer_path_loss = self._cached_directional_path_loss(
                        "uav", i, "uav", rx_idx, step_cache=step_cache
                    )
                elif rx_type == "ground_bs":
                    interferer_path_loss = self._cached_directional_path_loss(
                        "uav",
                        i,
                        "ground_bs",
                        rx_idx,
                        step_cache=step_cache,
                    )
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
        noise_power_linear = self._noise_power_linear_mw()
        interference_plus_noise_linear = noise_power_linear + total_interference_linear
        interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
        
        sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db
    
    def _compute_routing_paths(self):
        """Build routes under one exact communication-cache validation."""
        cache = self._current_step_communication_cache()
        if cache is None:
            return self._compute_routing_paths_cached_body()
        previous = bool(getattr(self, "_channel_update_cache_active", False))
        self._channel_update_cache_active = True
        try:
            return self._compute_routing_paths_cached_body()
        finally:
            self._channel_update_cache_active = previous

    def _compute_routing_paths_cached_body(self):
        """
        根据指定的路由协议计算路由路径。
        这是一个调度器方法，会调用具体的路由算法实现。
        """
        if self.routing_protocol == 'hggr':
            self._compute_routing_paths_hggr()
        elif self.routing_protocol == 'geographic':
            self._compute_routing_paths_geo()
        else:  # 默认使用 'widest_path'
            self._compute_routing_paths_widest()

    def _compute_routing_paths_hggr(self):
        """
        【优化版】使用 HGGR 算法计算路由路径，并重建完整路径。
        """
        self.routing_paths = {}
        for uav_idx in range(self.n_uavs):
            # 对于每个无人机，尝试重建其到基站的完整路径
            path, bottleneck_capacity = self._reconstruct_hggr_path(uav_idx)
            if path and bottleneck_capacity > 0:
                self.routing_paths[uav_idx] = (path, bottleneck_capacity)

    def _reconstruct_hggr_path(self, start_uav_idx):
        """
        从指定的无人机开始，沿着跳数梯度重建到基站的完整路径。
        """
        path = [("uav", start_uav_idx)]
        bottleneck_capacity = float('inf')
        
        current_node_idx = start_uav_idx
        
        # 循环构建路径，直到到达基站或无法继续
        for _ in range(self.max_hops + 1):
            current_hop = self.hop_map.get(current_node_idx, float('inf'))
            if current_hop == float('inf'):
                return None, 0 # 当前节点不可达

            # --- 寻找最优的下一跳 ---
            best_next_hop_node = None
            max_link_capacity = 0.0

            # 候选1：其他无人机
            for neighbor_idx in range(self.n_uavs):
                if current_node_idx == neighbor_idx:
                    continue
                
                neighbor_hop = self.hop_map.get(neighbor_idx, float('inf'))
                if neighbor_hop < current_hop:
                    capacity = self._get_link_capacity("uav", current_node_idx, "uav", neighbor_idx)
                    if capacity > max_link_capacity:
                        max_link_capacity = capacity
                        best_next_hop_node = ("uav", neighbor_idx)
            
            # 候选2：地面基站 (跳数为0)
            for bs_idx in range(self.n_ground_bs):
                if self.uav_bs_connections[current_node_idx, bs_idx]:
                    if 0 < current_hop:
                        capacity = self._get_link_capacity("uav", current_node_idx, "ground_bs", bs_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("ground_bs", bs_idx)

            # --- 更新路径和瓶颈 ---
            if best_next_hop_node:
                path.append(best_next_hop_node)
                bottleneck_capacity = min(bottleneck_capacity, max_link_capacity)
                
                # 如果下一跳是基站，路径构建完成
                if best_next_hop_node[0] == "ground_bs":
                    return path, bottleneck_capacity
                
                # 更新当前节点以继续构建路径
                current_node_idx = best_next_hop_node[1]
            else:
                # 找不到下一跳，路径中断
                return None, 0
        
        # 如果超出最大跳数仍未到达基站，则路径无效
        return None, 0

    def _calculate_hop_map(self):
        """
        为 HGGR 协议动态计算跳数地图（全局BFS）。
        在分层模型中，这个函数相当于高层策略的一部分。
        """
        import collections
        q = collections.deque()
        hop_map = {i: float('inf') for i in range(self.n_uavs)}

        # 1. 将所有直连到基站的无人机作为第一层（跳数为1）
        for uav_idx in range(self.n_uavs):
            for bs_idx in range(self.n_ground_bs):
                if self.uav_bs_connections[uav_idx, bs_idx]:
                    if hop_map[uav_idx] == float('inf'):
                        hop_map[uav_idx] = 1
                        q.append(uav_idx)
                    break

        # 2. 从第一层开始，通过BFS计算其他无人机的跳数 (修正版：基于单向链路)
        while q:
            current_uav = q.popleft()
            current_hop = hop_map[current_uav]
            
            # 遍历所有无人机，寻找可以通过 current_uav 进行中继的节点
            for upstream_neighbor_idx in range(self.n_uavs):
                # 只关心尚未分配跳数的节点
                if hop_map[upstream_neighbor_idx] == float('inf'):
                    # 检查是否存在一个有效的单向链路从 "上游" 邻居到当前节点
                    # 这是数据回程的方向: upstream_neighbor -> current_uav
                    capacity = self._get_link_capacity("uav", upstream_neighbor_idx, "uav", current_uav)
                    
                    if capacity > 0:
                        # 如果存在有效链路，说明 upstream_neighbor 可以通过 current_uav 中继
                        # 因此它的跳数是 current_uav 的跳数 + 1
                        hop_map[upstream_neighbor_idx] = current_hop + 1
                        q.append(upstream_neighbor_idx)
        
        return hop_map
                
    def _compute_routing_paths_geo(self):
        """
        【优化版】使用简化的地理路由算法计算路由路径，并重建完整路径。
        无人机总是选择物理距离上最接近任何一个基站的邻居作为下一跳。
        """
        self.routing_paths = {}

        # 预先计算所有无人机到最近基站的物理距离
        uav_dist_to_bs = {i: min(np.linalg.norm(self.uav_positions[i] - bs_pos) for bs_pos in self.ground_bs_positions) for i in range(self.n_uavs)}

        for uav_idx in range(self.n_uavs):
            path = [("uav", uav_idx)]
            bottleneck_capacity = float('inf')
            current_node_idx = uav_idx
            
            # 迭代构建路径
            for _ in range(self.max_hops + 1):
                own_dist = uav_dist_to_bs.get(current_node_idx, float('inf'))
                if own_dist == float('inf'): # Should not happen if start is a uav
                    break

                best_next_hop_node = None
                max_link_capacity = 0.0

                # 候选1：寻找距离基站更近的无人机邻居
                for neighbor_idx in range(self.n_uavs):
                    if current_node_idx == neighbor_idx or not self.uav_connections[current_node_idx, neighbor_idx]:
                        continue
                    
                    neighbor_dist = uav_dist_to_bs.get(neighbor_idx, float('inf'))
                    if neighbor_dist < own_dist:
                        capacity = self._get_link_capacity("uav", current_node_idx, "uav", neighbor_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("uav", neighbor_idx)

                # 候选2：检查到基站的直连
                for bs_idx in range(self.n_ground_bs):
                    if self.uav_bs_connections[current_node_idx, bs_idx]:
                        capacity = self._get_link_capacity("uav", current_node_idx, "ground_bs", bs_idx)
                        if capacity > max_link_capacity:
                            max_link_capacity = capacity
                            best_next_hop_node = ("ground_bs", bs_idx)

                # 更新路径
                if best_next_hop_node:
                    path.append(best_next_hop_node)
                    bottleneck_capacity = min(bottleneck_capacity, max_link_capacity)
                    
                    if best_next_hop_node[0] == "ground_bs":
                        # 成功到达基站
                        self.routing_paths[uav_idx] = (path, bottleneck_capacity)
                        break
                    
                    current_node_idx = best_next_hop_node[1]
                else:
                    # 路径中断
                    break
            # 如果循环结束仍未设置路径，则说明失败

    def _compute_routing_paths_widest(self):
        """
        原始的最宽路径路由算法。
        为每一个UAV独立计算其到任何一个基站的最宽路径。
        """
        self.routing_paths = {}
        use_cache = not bool(
            getattr(self, "_disable_routing_link_capacity_cache", False)
        )
        if use_cache:
            self._routing_link_capacity_cache = {}
        try:
            for uav_idx in range(self.n_uavs):
                path, capacity = self._find_widest_path_to_ground_bs(uav_idx)
                if path and capacity > 0 and len(path) - 1 <= self.max_hops:
                    self.routing_paths[uav_idx] = (path, capacity)
        finally:
            if use_cache:
                del self._routing_link_capacity_cache

    def _kmeans_clustering(self, data, n_clusters, max_iters=100, tol=1e-4):
        """
        纯NumPy实现的K-means聚类算法。
        
        参数:
            data (np.ndarray): 要聚类的数据，形状为 (n_samples, n_features)。
            n_clusters (int): 簇的数量 (k)。
            max_iters (int): 最大迭代次数。
            tol (float): 中心点变化的容忍度，用于判断收敛。
            
        返回:
            tuple: (centroids, labels)
                - centroids (np.ndarray): 簇中心点，形状为 (n_clusters, n_features)。
                - labels (np.ndarray): 每个样本的簇标签，形状为 (n_samples,)。
        """
        # 1. 初始化中心点：随机选择k个数据点作为初始中心
        initial_indices = self.np_random.choice(data.shape[0], n_clusters, replace=False)
        centroids = data[initial_indices]

        for i in range(max_iters):
            # 2. 分配步骤：将每个点分配到最近的中心点
            distances = cdist(data, centroids, 'euclidean')
            labels = np.argmin(distances, axis=1)

            # 3. 更新步骤：重新计算每个簇的中心点
            new_centroids = np.array([data[labels == j].mean(axis=0) for j in range(n_clusters)])

            # 检查收敛性
            if np.all(np.abs(new_centroids - centroids) <= tol):
                break
            
            centroids = new_centroids

        return centroids, labels

    def _perform_dynamic_clustering(self):
        """
        对当前用户位置进行动态K-means聚类（使用内置实现）。
        
        返回:
            cluster_centers: 簇中心位置 [n_clusters, 2]
            cluster_assignments: 用户簇分配 [n_users]
            cluster_info: 簇信息 [n_clusters, 4] (中心x, 中心y, 用户数, 覆盖率)
        """
        # 获取用户的2D位置
        user_positions_2d = self.user_positions[:, :2]
        
        # 执行内置的K-means聚类
        cluster_centers, cluster_assignments = self._kmeans_clustering(user_positions_2d, self.n_clusters)
        
        # 计算每个簇的详细信息
        cluster_info = np.zeros((self.n_clusters, 4))
        
        for i in range(self.n_clusters):
            # 找到属于该簇的用户
            user_indices_in_cluster = np.where(cluster_assignments == i)[0]
            num_users_in_cluster = len(user_indices_in_cluster)
            
            if num_users_in_cluster > 0:
                # 簇中心位置 (归一化)
                cluster_info[i, 0] = cluster_centers[i, 0] / self.area_size
                cluster_info[i, 1] = cluster_centers[i, 1] / self.area_size
                
                # 簇内用户数 (归一化)
                cluster_info[i, 2] = num_users_in_cluster / self.n_users
                
                # 簇内覆盖率
                covered_users_in_cluster = 0
                for user_idx in user_indices_in_cluster:
                    # 检查用户是否被有效覆盖 (连接到有回程的UAV)
                    for uav_idx in range(self.n_uavs):
                        if self.connections[uav_idx, user_idx] and uav_idx in self.routing_paths:
                            covered_users_in_cluster += 1
                            break  # 每个用户只计数一次
                
                cluster_info[i, 3] = covered_users_in_cluster / num_users_in_cluster
            # 如果簇内没有用户，则信息为0
        
        return cluster_centers, cluster_assignments, cluster_info

    def _get_state(self):
        """
        获取针对强制中继场景优化的全局状态（详细版：包含每个用户的完整信息）
        
        包含以下信息：
        1. 无人机位置 (n_uavs * 3)
        2. 用户详细信息 (n_users * 6) - 位置(x,y), 速度(x,y), 连接状态, 最佳SINR
        3. 地面基站位置 (n_ground_bs * 3)
        4. 当前步数 (1)
        
        返回:
            state: 简化的全局状态向量
        """
        state_components = []
        
        # 1. 无人机位置 (归一化到[0,1])
        normalized_uav_positions = self.uav_positions.copy()
        normalized_uav_positions[:, :2] /= self.area_size
        normalized_uav_positions[:, 2] = (normalized_uav_positions[:, 2] - self.height_range[0]) / (self.height_range[1] - self.height_range[0])
        state_components.append(normalized_uav_positions.flatten())
        
        # 1.5. 无人机负载 (归一化)
        uav_loads = np.sum(self.connections, axis=1) / self.max_connections
        state_components.append(uav_loads.flatten())

        # 2. 用户详细信息 (每个用户6维信息)
        user_info = np.zeros((self.n_users, 6))
        
        for user_idx in range(self.n_users):
            # 2.1 用户位置 (归一化)
            user_pos = self.user_positions[user_idx]
            user_info[user_idx, 0] = user_pos[0] / self.area_size  # x位置
            user_info[user_idx, 1] = user_pos[1] / self.area_size  # y位置
            
            # 2.2 用户速度 (归一化)
            user_vel = self.user_velocities[user_idx]
            user_info[user_idx, 2] = user_vel[0] / self.user_max_speed  # x速度
            user_info[user_idx, 3] = user_vel[1] / self.user_max_speed  # y速度
            
            # 2.3 连接状态 (是否被有效覆盖)
            is_effectively_connected = False
            best_sinr = -np.inf
            
            # 检查是否有UAV连接到该用户且该UAV有回程路径
            for uav_idx in range(self.n_uavs):
                if self.connections[uav_idx, user_idx]:
                    sinr = self.sinr_matrix[uav_idx, user_idx]
                    best_sinr = max(best_sinr, sinr)
                    
                    if uav_idx in self.routing_paths and self.routing_paths[uav_idx][0]:
                        is_effectively_connected = True
            
            user_info[user_idx, 4] = 1.0 if is_effectively_connected else 0.0  # 连接状态
            
            # 2.4 最佳SINR (归一化到[0,1])
            if best_sinr > -np.inf:
                # 将SINR从[-10, 40]dB范围归一化到[0,1]
                normalized_sinr = np.clip((best_sinr + 10) / 50, 0, 1)
            else:
                normalized_sinr = 0.0
            user_info[user_idx, 5] = normalized_sinr
        
        state_components.append(user_info.flatten())
        
        # 3. 地面基站位置 (归一化)
        normalized_bs_positions = self.ground_bs_positions.copy()
        normalized_bs_positions[:, :2] /= self.area_size
        normalized_bs_positions[:, 2] /= self.height_range[1]
        state_components.append(normalized_bs_positions.flatten())
        
        # 4. 当前步数 (归一化)
        step_normalized = np.array([self.current_step / self.max_steps])
        state_components.append(step_normalized)
        
        # 组合所有状态组件
        state = np.concatenate(state_components)
        
        return state

    def _perform_grid_clustering(self):
        """
        简化的网格聚类方法（当sklearn不可用时的备选方案）
        
        返回:
            cluster_info: 簇信息 [n_clusters, 4]
        """
        # 将区域划分为网格
        grid_size = int(np.ceil(np.sqrt(self.n_clusters)))
        cell_width = self.area_size / grid_size
        cell_height = self.area_size / grid_size
        
        cluster_info = np.zeros((self.n_clusters, 4))
        
        cluster_idx = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if cluster_idx >= self.n_clusters:
                    break
                
                # 定义网格单元边界
                x_min = i * cell_width
                x_max = (i + 1) * cell_width
                y_min = j * cell_height
                y_max = (j + 1) * cell_height
                
                # 找到在该网格单元内的用户
                users_in_cell = []
                for user_idx in range(self.n_users):
                    user_pos = self.user_positions[user_idx]
                    if x_min <= user_pos[0] < x_max and y_min <= user_pos[1] < y_max:
                        users_in_cell.append(user_idx)
                
                num_users_in_cell = len(users_in_cell)
                
                if num_users_in_cell > 0:
                    # 计算网格中心 (归一化)
                    center_x = (x_min + x_max) / 2
                    center_y = (y_min + y_max) / 2
                    cluster_info[cluster_idx, 0] = center_x / self.area_size
                    cluster_info[cluster_idx, 1] = center_y / self.area_size
                    
                    # 用户数 (归一化)
                    cluster_info[cluster_idx, 2] = num_users_in_cell / self.n_users
                    
                    # 覆盖率
                    covered_users = 0
                    for user_idx in users_in_cell:
                        for uav_idx in range(self.n_uavs):
                            if self.connections[uav_idx, user_idx] and uav_idx in self.routing_paths:
                                covered_users += 1
                                break
                    
                    cluster_info[cluster_idx, 3] = covered_users / num_users_in_cell
                
                cluster_idx += 1
                
            if cluster_idx >= self.n_clusters:
                break
        
        return cluster_info
    
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
        user_spectral_efficiencies = []
        
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
                # 使用AMC模型计算单用户容量
                spectral_efficiency = self._get_spectral_efficiency_from_sinr(sinr_db)
                user_capacity = self.bandwidth * spectral_efficiency
                user_capacities.append(user_capacity)
                user_spectral_efficiencies.append(spectral_efficiency)
            else:
                # SINR不满足阈值，该用户无法获得服务
                user_capacities.append(0)
                user_spectral_efficiencies.append(0)
        
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
                for i, _user_idx in enumerate(connected_users):
                    if user_capacities[i] > 0:
                        adjusted_capacity = (
                            bandwidth_per_user * user_spectral_efficiencies[i]
                        )
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
    
    def _compute_uav_to_user_sinr(
        self, uav_idx, user_idx, rx_power, step_cache=_STEP_CACHE_UNSET
    ):
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
        if step_cache is _STEP_CACHE_UNSET:
            step_cache = self._current_step_communication_cache()
        
        # 计算来自其他UAV的干扰
        for i in range(self.n_uavs):
            if i != uav_idx:  # 排除目标UAV自身
                interferer_pos = self.uav_positions[i]
                
                # 原则1：检查距离 - 考虑干扰半径内的所有无人机
                dist_to_user = self._compute_distance(interferer_pos, user_pos_3d)
                if dist_to_user > interference_radius:
                    continue  # 干扰源太远，忽略
                
                # 原则3：使用精确的A2G路径损耗模型计算干扰
                interferer_path_loss = self._cached_user_path_loss(
                    i, user_idx, step_cache=step_cache
                )
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
        noise_power_linear = self._noise_power_linear_mw()
        interference_plus_noise_linear = noise_power_linear + total_interference_linear
        interference_plus_noise_dbm = 10 * np.log10(interference_plus_noise_linear)
        
        sinr_db = rx_power - interference_plus_noise_dbm
        
        return sinr_db

    def _identify_critical_relay_nodes(self):
        """
        阶段一：识别潜在的关键中继节点
        
        通过在"干净"环境下（忽略用户）计算无人机间的连接质量，
        识别出那些在网络拓扑中处于关键"桥梁"位置的无人机。
        
        返回:
            critical_relay_nodes: 关键中继节点的集合
        """
        critical_relay_nodes = set()
        
        # 临时保存当前的连接状态
        temp_connections = self.connections.copy()
        
        # 创建一个"干净"的环境：暂时清空用户连接，只考虑UAV间连接
        self.connections.fill(False)
        
        # 计算所有UAV之间的潜在连接质量
        uav_link_qualities = {}
        for i in range(self.n_uavs):
            for j in range(i + 1, self.n_uavs):
                # 计算UAV间的链路容量
                capacity_ij = self._get_link_capacity("uav", i, "uav", j)
                capacity_ji = self._get_link_capacity("uav", j, "uav", i)
                
                # 双向链路的容量取较小值
                bidirectional_capacity = min(capacity_ij, capacity_ji)
                
                if bidirectional_capacity > 0:
                    uav_link_qualities[(i, j)] = bidirectional_capacity
        
        # 计算每个UAV到地面基站的直连质量
        uav_bs_qualities = {}
        for i in range(self.n_uavs):
            max_bs_capacity = 0
            for bs_idx in range(self.n_ground_bs):
                # 计算UAV到基站的链路容量
                capacity_to_bs = self._get_link_capacity("uav", i, "ground_bs", bs_idx)
                capacity_from_bs = self._get_link_capacity("ground_bs", bs_idx, "uav", i)
                
                # 双向链路的容量取较小值
                bidirectional_capacity = min(capacity_to_bs, capacity_from_bs)
                max_bs_capacity = max(max_bs_capacity, bidirectional_capacity)
            
            uav_bs_qualities[i] = max_bs_capacity
        
        # 使用简化的中心性分析识别关键节点
        # 计算每个UAV的"桥梁重要性"
        for uav_idx in range(self.n_uavs):
            importance_score = 0
            
            # 1. 连接度重要性：连接到多少其他UAV
            connected_uavs = 0
            for i, j in uav_link_qualities.keys():
                if i == uav_idx or j == uav_idx:
                    connected_uavs += 1
            
            # 2. 位置重要性：是否处于网络的"中间"位置
            # 通过计算到其他所有UAV的平均距离来衡量
            total_distance = 0
            for other_idx in range(self.n_uavs):
                if other_idx != uav_idx:
                    dist = self._compute_distance(
                        self.uav_positions[uav_idx], 
                        self.uav_positions[other_idx]
                    )
                    total_distance += dist
            
            avg_distance = total_distance / (self.n_uavs - 1) if self.n_uavs > 1 else 0
            
            # 3. 基站连接质量：到基站的直连能力
            bs_connection_quality = uav_bs_qualities.get(uav_idx, 0)
            
            # 综合评分：连接度高、位置居中、但基站连接不是最强的UAV
            # 更可能是好的中继节点
            if connected_uavs > 0:
                # 归一化各项指标
                normalized_connectivity = connected_uavs / self.n_uavs
                normalized_centrality = 1.0 / (1.0 + avg_distance / self.area_size)  # 距离越小，中心性越高
                
                # 基站连接质量归一化（这里我们希望中继节点的基站连接不要太强）
                max_bs_quality = max(uav_bs_qualities.values()) if uav_bs_qualities.values() else 1
                normalized_bs_quality = bs_connection_quality / max_bs_quality if max_bs_quality > 0 else 0
                
                # 综合评分：连接度和中心性高，但基站连接适中的节点
                importance_score = (
                    0.4 * normalized_connectivity +
                    0.4 * normalized_centrality +
                    0.2 * (1.0 - normalized_bs_quality)  # 基站连接不要太强
                )
                
                # 如果重要性评分超过阈值，标记为关键中继节点
                if importance_score > 0.5:  # 可调整的阈值
                    critical_relay_nodes.add(uav_idx)
        
        # 恢复原始的连接状态
        self.connections = temp_connections
        
        return critical_relay_nodes

    def _select_uav_with_relay_protection(self, user_idx, candidates, critical_relay_nodes):
        """
        阶段二：带保护机制的无人机选择
        
        为指定用户从候选无人机中选择最佳的服务无人机，
        同时保护关键中继节点不被轻易占用。
        
        参数:
            user_idx: 用户索引
            candidates: 候选无人机列表 [(uav_idx, sinr), ...] (已按SINR降序排序)
            critical_relay_nodes: 关键中继节点集合
            
        返回:
            selected_uav: 选中的无人机索引，如果没有合适的则返回None
        """
        if not candidates:
            return None
        
        # 保护阈值：关键中继节点需要比非关键节点强多少dB才会被选中
        protection_threshold_db = 10.0  # 可调整的保护阈值
        
        # 首先尝试从非关键节点中选择
        non_critical_candidates = [
            (uav_idx, sinr) for uav_idx, sinr in candidates 
            if uav_idx not in critical_relay_nodes
        ]
        
        if non_critical_candidates:
            # 如果有非关键节点可用，直接选择信号最好的
            return non_critical_candidates[0][0]
        
        # 如果只有关键节点可用，应用保护机制
        critical_candidates = [
            (uav_idx, sinr) for uav_idx, sinr in candidates 
            if uav_idx in critical_relay_nodes
        ]
        
        if not critical_candidates:
            return None
        
        # 选择信号最强的关键节点，但需要满足保护条件
        best_critical_uav, best_critical_sinr = critical_candidates[0]
        
        # 检查是否有其他用户已经"预订"了更好的非关键节点
        # 这里简化处理：如果关键节点的信号足够强（超过最小阈值+保护阈值），
        # 则允许使用
        if best_critical_sinr >= self.min_sinr + protection_threshold_db:
            return best_critical_uav
        
        # 否则，不分配任何无人机给这个用户（保护中继节点）
        return None

    def _update_global_bs_cache(self):
        """
        在K step同步时更新全局基站信息缓存
        
        此方法在每K个时间步执行一次，收集所有UAV观测到的基站信息，
        并更新全局缓存，供那些没有直接观测到基站的UAV使用。
        """
        # 记录本次同步的步数
        self.last_global_sync_step = self.current_step
        
        # 临时存储本次同步收集到的基站信息
        sync_bs_info = {}
        
        # 遍历所有UAV，收集它们观测到的基站信息
        for uav_idx in range(self.n_uavs):
            local_bs = self._get_local_bs(uav_idx)  # 获取该UAV观测到的基站列表
            own_position = self.uav_positions[uav_idx]
            
            for bs_idx, dist in local_bs:
                if bs_idx not in sync_bs_info:
                    # 首次发现这个基站，记录其归一化位置信息
                    bs_pos = self.ground_bs_positions[bs_idx]
                    # 计算归一化的相对位置（相对于某个参考点，这里使用地图中心）
                    map_center = np.array([self.area_size / 2, self.area_size / 2, 0])
                    relative_pos = bs_pos - map_center
                    
                    # 归一化位置信息
                    normalized_pos = np.array([
                        relative_pos[0] / self.area_size,  # x
                        relative_pos[1] / self.area_size,  # y  
                        relative_pos[2] / self.height_range[1]  # z
                    ])
                    
                    sync_bs_info[bs_idx] = {
                        'normalized_pos': normalized_pos,
                        'visibility_flag': 1.0,  # 在全局同步中发现的基站标记为可见
                        'observers': [uav_idx]  # 记录观测到该基站的UAV
                    }
                else:
                    # 已有其他UAV观测到此基站，添加到观测者列表
                    sync_bs_info[bs_idx]['observers'].append(uav_idx)
        
        # 更新全局缓存
        self.global_bs_cache = {}
        for bs_idx, info in sync_bs_info.items():
            self.global_bs_cache[bs_idx] = (info['normalized_pos'], info['visibility_flag'])
        
        # 可选：打印调试信息
        #if len(self.global_bs_cache) > 0:
        #    print(f"[Step {self.current_step}] 全局基站缓存更新: 发现 {len(self.global_bs_cache)} 个基站")
