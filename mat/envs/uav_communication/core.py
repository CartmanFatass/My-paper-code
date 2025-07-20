import numpy as np

# 基本实体状态
class EntityState(object):
    def __init__(self):
        # 3D位置
        self.p_pos = None  # [x, y, z]
        # 3D速度
        self.p_vel = None  # [vx, vy, vz]

# UAV的状态（包括通信状态）
class UAVState(EntityState):
    def __init__(self):
        super(UAVState, self).__init__()
        # 是否在服务用户
        self.is_serving = False
        # 是否在中继
        self.is_relaying = False
        # 连接的用户设备
        self.connected_ues = []
        # 回程链路质量
        self.backhaul_link_quality = 0.0
        # 剩余电量 (0-1)
        self.battery = 1.0

# UAV的动作
class UAVAction(object):
    def __init__(self):
        # 物理动作（速度调整）
        self.u = None  # [delta_vx, delta_vy, delta_vz]

# 通信链路类
class CommunicationLink(object):
    def __init__(self, entity1, entity2, link_type=None):
        # 链路两端的实体
        self.entity1 = entity1
        self.entity2 = entity2
        # 链路类型：'UAV-UE', 'UAV-UAV', 'UAV-GBS'
        self.link_type = link_type
        # 路径损耗 (dB)
        self.path_loss = 0.0
        # 信噪比 (dB)
        self.sinr = 0.0
        # 数据速率 (bps)
        self.data_rate = 0.0
        # 是否是视距连接 (Line of Sight)
        self.is_los = True

# 物理世界中实体的属性和状态
class Entity(object):
    def __init__(self):
        # 索引（用于缓存距离计算）
        self.i = 0
        # 名称
        self.name = ''
        # 属性
        self.size = 0.1
        # 是否可移动
        self.movable = False
        # 是否会碰撞
        self.collide = False
        # 颜色
        self.color = None
        # 最大速度
        self.max_speed = None
        # 加速度
        self.accel = None
        # 状态
        self.state = EntityState()
        # 质量
        self.mass = 1.0
        # 观测范围
        self.observation_range = 1.0

# 地面基站
class GroundBaseStation(Entity):
    def __init__(self):
        super(GroundBaseStation, self).__init__()
        # 基站是固定的
        self.movable = False
        # 发射功率 (dBm)
        self.tx_power = 43.0  # 20W
        # 覆盖范围 (m)
        self.coverage_radius = 500.0
        # 颜色（蓝色）
        self.color = np.array([0.0, 0.0, 0.8])

# 用户设备
class UserEquipment(Entity):
    def __init__(self):
        super(UserEquipment, self).__init__()
        # 用户设备可以移动（可选）
        self.movable = True
        # 服务请求状态
        self.service_requested = False
        # 请求的数据速率 (bps)
        self.requested_data_rate = 1e6  # 1 Mbps
        # 颜色（绿色）
        self.color = np.array([0.0, 0.8, 0.0])

# 无人机
class UAV(Entity):
    def __init__(self):
        super(UAV, self).__init__()
        # 无人机可以移动
        self.movable = True
        # 发射功率 (dBm)
        self.tx_power = 30.0  # 1W
        # 覆盖范围 (m)
        self.coverage_radius = 200.0
        # 观测范围 (m)
        self.observation_range = 300.0
        # 最大速度 (m/s)
        self.max_speed = 10.0
        # 能量消耗率 (每单位移动距离)
        self.energy_consumption_rate = 0.01
        # 能量消耗率 (每单位通信数据量)
        self.energy_consumption_rate_comm = 0.001
        # 状态
        self.state = UAVState()
        # 动作
        self.action = UAVAction()
        # 颜色（红色）
        self.color = np.array([0.8, 0.0, 0.0])

# 多智能体世界
class World(object):
    def __init__(self):
        # 实体列表
        self.uavs = []  # UAV列表
        self.ground_base_stations = []  # 地面基站列表
        self.user_equipments = []  # 用户设备列表
        self.communication_links = []  # 通信链路列表
        # 位置维度（3D空间）
        self.dim_p = 3
        # 仿真时间步长
        self.dt = 0.1
        # 阻尼（空气阻力，减速）
        self.damping = 0.25
        # 仿真步数
        self.world_step = 0
        # 仿真最大步数
        self.world_length = 500
        # 区域范围 (m)
        self.area_size = 1000.0  # 1km x 1km x 0.3km
        # 环境特性（城市/郊区/农村）
        self.environment_type = 'urban'
        # 频率 (GHz)
        self.frequency = 2.4  # 2.4 GHz

    # 返回所有实体
    @property
    def entities(self):
        return self.uavs + self.ground_base_stations + self.user_equipments

    # 返回所有作为智能体的UAV
    @property
    def policy_agents(self):
        return self.uavs

    # 更新所有通信链路的质量
    def update_communication_links(self, channel_model):
        self.communication_links = []
        # 创建UAV-UE链路
        for uav in self.uavs:
            for ue in self.user_equipments:
                # 如果UE在UAV的覆盖范围内
                if np.linalg.norm(uav.state.p_pos - ue.state.p_pos) <= uav.coverage_radius:
                    link = CommunicationLink(uav, ue, 'UAV-UE')
                    channel_model.calculate_link_quality(link, self)
                    self.communication_links.append(link)

        # 创建UAV-UAV链路（用于中继）
        for i, uav1 in enumerate(self.uavs):
            for uav2 in self.uavs[i+1:]:
                # 如果UAV之间在彼此的观测范围内
                if np.linalg.norm(uav1.state.p_pos - uav2.state.p_pos) <= min(uav1.observation_range, uav2.observation_range):
                    link = CommunicationLink(uav1, uav2, 'UAV-UAV')
                    channel_model.calculate_link_quality(link, self)
                    self.communication_links.append(link)

        # 创建UAV-GBS链路（回程）
        for uav in self.uavs:
            for gbs in self.ground_base_stations:
                # 如果UAV在GBS的覆盖范围内
                if np.linalg.norm(uav.state.p_pos - gbs.state.p_pos) <= gbs.coverage_radius:
                    link = CommunicationLink(uav, gbs, 'UAV-GBS')
                    channel_model.calculate_link_quality(link, self)
                    self.communication_links.append(link)
                    # 更新UAV的回程链路质量
                    uav.state.backhaul_link_quality = link.sinr

    # 计算服务情况（UAV服务哪些UE）
    def calculate_service_allocation(self):
        # 重置所有UAV的服务/中继状态
        for uav in self.uavs:
            uav.state.is_serving = False
            uav.state.is_relaying = False
            uav.state.connected_ues = []

        # 为每个UE分配最佳服务UAV（基于SINR）
        for ue in self.user_equipments:
            best_uav = None
            best_sinr = -float('inf')
            
            for link in self.communication_links:
                if link.link_type == 'UAV-UE' and link.entity2 == ue:
                    if link.sinr > best_sinr:
                        best_sinr = link.sinr
                        best_uav = link.entity1

            if best_uav is not None and best_sinr > 0:  # 假设SINR需要大于0才能服务
                best_uav.state.is_serving = True
                best_uav.state.connected_ues.append(ue)

        # 计算哪些UAV充当中继
        for uav in self.uavs:
            if uav.state.is_serving:
                # 检查该UAV是否有到GBS的直接链路
                has_direct_backhaul = False
                for link in self.communication_links:
                    if link.link_type == 'UAV-GBS' and link.entity1 == uav:
                        has_direct_backhaul = True
                        break
                
                if not has_direct_backhaul:
                    # 需要其他UAV作为中继
                    for link in self.communication_links:
                        if link.link_type == 'UAV-UAV' and link.entity1 == uav:
                            relay_uav = link.entity2
                            # 检查中继UAV是否有到GBS的链路
                            for relay_link in self.communication_links:
                                if relay_link.link_type == 'UAV-GBS' and relay_link.entity1 == relay_uav:
                                    relay_uav.state.is_relaying = True
                                    break

    # 更新世界状态
    def step(self, channel_model):
        self.world_step += 1
        
        # 应用UAV物理控制（速度变化）
        for uav in self.uavs:
            uav.state.p_vel = uav.state.p_vel * (1 - self.damping) + uav.action.u
            
            # 检查速度是否超过最大速度
            speed = np.linalg.norm(uav.state.p_vel)
            if speed > uav.max_speed:
                uav.state.p_vel = uav.state.p_vel / speed * uav.max_speed
            
            # 更新位置
            uav.state.p_pos += uav.state.p_vel * self.dt
            
            # 确保UAV在区域范围内
            uav.state.p_pos = np.clip(uav.state.p_pos, 
                                      [-self.area_size/2, -self.area_size/2, 0], 
                                      [self.area_size/2, self.area_size/2, 300])  # 假设最大高度为300m
            
            # 更新电池电量（基于移动和通信）
            energy_consumed_movement = np.linalg.norm(uav.state.p_vel) * self.dt * uav.energy_consumption_rate
            uav.state.battery -= energy_consumed_movement
            
            # 确保电池电量不为负
            uav.state.battery = max(0.0, uav.state.battery)
        
        # 更新通信链路并计算服务分配
        self.update_communication_links(channel_model)
        self.calculate_service_allocation()
        
        # 更新UE的服务请求（这里简化为随机请求）
        for ue in self.user_equipments:
            if np.random.random() < 0.01:  # 1%概率改变请求状态
                ue.service_requested = not ue.service_requested
