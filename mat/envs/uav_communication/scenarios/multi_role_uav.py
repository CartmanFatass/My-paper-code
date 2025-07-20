import numpy as np
from mat.envs.uav_communication.core import World, UAV, GroundBaseStation, UserEquipment

class Scenario:
    def make_world(self, args):
        """
        创建世界对象并初始化无人机、地面基站和用户设备
        
        Args:
            args: 参数字典，包含num_uavs, num_gbs, num_ues等
            
        Returns:
            world: 创建好的世界对象
        """
        world = World()
        
        # 设置世界属性
        world.world_length = args.episode_length if hasattr(args, 'episode_length') else 500
        world.area_size = args.area_size if hasattr(args, 'area_size') else 1000.0
        world.environment_type = args.environment_type if hasattr(args, 'environment_type') else 'urban'
        world.frequency = args.frequency if hasattr(args, 'frequency') else 2.4
        
        # 获取实体数量
        num_uavs = args.num_uavs if hasattr(args, 'num_uavs') else 10
        num_gbs = args.num_gbs if hasattr(args, 'num_gbs') else 3
        num_ues = args.num_ues if hasattr(args, 'num_ues') else 50
        
        # 添加无人机
        world.uavs = [UAV() for _ in range(num_uavs)]
        for i, uav in enumerate(world.uavs):
            uav.name = 'uav %d' % i
            uav.i = i
            
            # 初始化状态
            uav.state.p_pos = np.zeros(world.dim_p)
            uav.state.p_vel = np.zeros(world.dim_p)
            uav.state.battery = 1.0
            uav.state.is_serving = False
            uav.state.is_relaying = False
            uav.state.connected_ues = []
            uav.state.backhaul_link_quality = 0.0
            
            # 初始化动作
            uav.action.u = np.zeros(world.dim_p)
        
        # 添加地面基站
        world.ground_base_stations = [GroundBaseStation() for _ in range(num_gbs)]
        for i, gbs in enumerate(world.ground_base_stations):
            gbs.name = 'gbs %d' % i
            gbs.i = i + num_uavs
            
            # 初始化状态
            gbs.state.p_pos = np.zeros(world.dim_p)
            gbs.state.p_vel = np.zeros(world.dim_p)
        
        # 添加用户设备
        world.user_equipments = [UserEquipment() for _ in range(num_ues)]
        for i, ue in enumerate(world.user_equipments):
            ue.name = 'ue %d' % i
            ue.i = i + num_uavs + num_gbs
            
            # 初始化状态
            ue.state.p_pos = np.zeros(world.dim_p)
            ue.state.p_vel = np.zeros(world.dim_p)
            ue.service_requested = False
        
        # 初始化世界
        self.reset_world(world)
        return world

    def reset_world(self, world):
        """
        重置世界状态，包括所有实体的位置和状态
        
        Args:
            world: 世界对象
        """
        # 重置无人机位置和状态
        for uav in world.uavs:
            # 随机位置，在区域内均匀分布
            uav.state.p_pos = np.random.uniform(
                low=[-world.area_size/2, -world.area_size/2, 50], 
                high=[world.area_size/2, world.area_size/2, 300],  # 高度范围：50-300米
                size=world.dim_p
            )
            # 初始速度为零
            uav.state.p_vel = np.zeros(world.dim_p)
            # 满电
            uav.state.battery = 1.0
            # 重置服务状态
            uav.state.is_serving = False
            uav.state.is_relaying = False
            uav.state.connected_ues = []
            uav.state.backhaul_link_quality = 0.0
        
        # 重置地面基站位置
        # 通常基站是固定的，这里将其分布在区域的特定位置
        n_gbs = len(world.ground_base_stations)
        if n_gbs >= 1:
            # 以特定模式分布基站，例如三角形或网格
            for i, gbs in enumerate(world.ground_base_stations):
                if n_gbs == 1:
                    # 单基站位于中心
                    gbs.state.p_pos = np.array([0.0, 0.0, 0.0])
                else:
                    # 多基站分布
                    # 计算在圆形或网格上的位置
                    radius = world.area_size * 0.4  # 位于区域的40%半径处
                    angle = 2 * np.pi * i / n_gbs
                    gbs.state.p_pos = np.array([
                        radius * np.cos(angle),
                        radius * np.sin(angle),
                        0.0  # 地面高度为0
                    ])
                gbs.state.p_vel = np.zeros(world.dim_p)
        
        # 重置用户设备位置和状态
        for ue in world.user_equipments:
            # 用户设备随机分布在地面（z=0）
            ue.state.p_pos = np.array([
                np.random.uniform(-world.area_size/2, world.area_size/2),
                np.random.uniform(-world.area_size/2, world.area_size/2),
                0.0  # 地面高度为0
            ])
            # 用户设备静止或微小速度
            ue.state.p_vel = np.zeros(world.dim_p)
            # 随机服务请求状态（有30%的概率需要服务）
            ue.service_requested = np.random.random() < 0.3

    def reward(self, uav, world):
        """
        计算单个无人机的奖励
        
        Args:
            uav: 要计算奖励的无人机
            world: 世界对象
            
        Returns:
            reward: 无人机获得的奖励
        """
        reward = 0.0
        
        # 奖励1：服务用户的奖励
        # 如果无人机正在服务用户，奖励与服务的用户数量和链路质量成正比
        if uav.state.is_serving:
            serving_ue_count = len(uav.state.connected_ues)
            serving_reward = 0.0
            
            # 遍历所有连接到该UAV的UE
            for ue in uav.state.connected_ues:
                # 寻找UAV-UE链路
                for link in world.communication_links:
                    if (link.link_type == 'UAV-UE' and 
                        link.entity1 == uav and 
                        link.entity2 == ue):
                        # 奖励与SINR相关
                        # 将SINR限制在合理范围(0-30dB)，并归一化
                        normalized_sinr = np.clip(link.sinr, 0, 30) / 30.0
                        data_rate_mbps = link.data_rate / 1e6  # 转换为Mbps
                        serving_reward += normalized_sinr * data_rate_mbps * 0.02  # 缩放系数
                        break
            
            reward += serving_reward
        
        # 奖励2：中继贡献的奖励
        if uav.state.is_relaying:
            relay_reward = 0.0
            
            # 寻找与这个UAV相关的UAV-UAV链路
            for link in world.communication_links:
                if (link.link_type == 'UAV-UAV' and 
                    (link.entity1 == uav or link.entity2 == uav)):
                    other_uav = link.entity2 if link.entity1 == uav else link.entity1
                    
                    # 如果另一个UAV在服务用户，且这个UAV作为中继
                    if other_uav.state.is_serving and not other_uav.state.backhaul_link_quality > 0:
                        # 奖励与链路质量相关
                        normalized_sinr = np.clip(link.sinr, 0, 30) / 30.0
                        relay_reward += normalized_sinr * len(other_uav.state.connected_ues) * 0.01  # 缩放系数
            
            reward += relay_reward
        
        # 奖励3：回程链路质量奖励
        if uav.state.is_serving:
            # 检查是否有回程链路
            has_backhaul = uav.state.backhaul_link_quality > 0
            
            # 如果无回程链路但在服务用户，这是不好的
            if not has_backhaul:
                # 查找是否有中继
                has_relay = False
                for link in world.communication_links:
                    if (link.link_type == 'UAV-UAV' and 
                        (link.entity1 == uav or link.entity2 == uav)):
                        other_uav = link.entity2 if link.entity1 == uav else link.entity1
                        for relay_link in world.communication_links:
                            if (relay_link.link_type == 'UAV-GBS' and 
                                relay_link.entity1 == other_uav):
                                has_relay = True
                                break
                    if has_relay:
                        break
                
                # 没有回程也没有中继，但在服务用户，给予惩罚
                if not has_relay:
                    reward -= 0.3 * len(uav.state.connected_ues)
            else:
                # 有直接回程，给予奖励
                normalized_backhaul_quality = np.clip(uav.state.backhaul_link_quality, 0, 30) / 30.0
                reward += 0.1 * normalized_backhaul_quality * len(uav.state.connected_ues)
        
        # 奖励4：能耗惩罚
        # 移动和高度会消耗能量
        velocity_penalty = -0.01 * np.linalg.norm(uav.state.p_vel) / uav.max_speed
        height_penalty = -0.005 * (uav.state.p_pos[2] / 300.0)  # 高度越高能耗越大
        reward += velocity_penalty + height_penalty
        
        # 奖励5：电池电量过低时的惩罚
        if uav.state.battery < 0.2:
            reward -= 0.3 * (0.2 - uav.state.battery) / 0.2  # 随着电量降低，惩罚增加
        
        # 奖励6：与其他无人机保持适当距离（避免聚集）
        for other in world.uavs:
            if other is uav:
                continue
                
            dist = np.linalg.norm(uav.state.p_pos - other.state.p_pos)
            if dist < 50:  # 小于50米被视为过近
                reward -= 0.05 * (1.0 - dist / 50.0)  # 距离越近惩罚越大
        
        return reward

    def observation(self, uav, world):
        """
        生成单个无人机的观测
        
        Args:
            uav: 无人机对象
            world: 世界对象
            
        Returns:
            obs: 无人机的观测向量
        """
        # 自身状态观测
        # 归一化位置
        normalized_pos = uav.state.p_pos.copy()
        normalized_pos[:2] /= (world.area_size / 2)  # x,y归一化到[-1,1]
        normalized_pos[2] /= 300.0  # z归一化到[0,1]（假设高度上限为300米）
        
        # 归一化速度
        normalized_vel = uav.state.p_vel.copy() / uav.max_speed  # 归一化到[-1,1]
        
        # 其他自身属性
        is_serving = 1.0 if uav.state.is_serving else 0.0
        is_relaying = 1.0 if uav.state.is_relaying else 0.0
        norm_backhaul_quality = np.clip(uav.state.backhaul_link_quality, 0, 30) / 30.0
        
        # 合并自身观测
        own_state = np.concatenate([
            [uav.state.battery],         # 电池电量
            normalized_pos,              # 归一化位置
            normalized_vel,              # 归一化速度
            [is_serving],                # 是否服务用户
            [is_relaying],               # 是否作为中继
            [norm_backhaul_quality]      # 归一化回程链路质量
        ])
        
        # 观测其他实体
        uav_obs = []
        gbs_obs = []
        ue_obs = []
        
        # 观测其他无人机
        for other in world.uavs:
            if other is uav:  # 跳过自己
                continue
                
            # 计算相对位置
            rel_pos = other.state.p_pos - uav.state.p_pos
            dist = np.linalg.norm(rel_pos)
            
            # 检查是否在观测范围内
            if dist <= uav.observation_range:
                # 相对位置
                norm_rel_pos = rel_pos.copy()
                norm_rel_pos[:2] /= uav.observation_range
                norm_rel_pos[2] /= 300.0
                
                # 相对速度
                rel_vel = other.state.p_vel - uav.state.p_vel
                norm_rel_vel = rel_vel / uav.max_speed
                
                # 其他UAV属性
                other_is_serving = 1.0 if other.state.is_serving else 0.0
                other_is_relaying = 1.0 if other.state.is_relaying else 0.0
                
                # 合并这个UAV的观测
                uav_obs.append(np.concatenate([
                    norm_rel_pos,         # 归一化相对位置
                    norm_rel_vel,         # 归一化相对速度
                    [other_is_serving],   # 是否服务用户
                    [other_is_relaying]   # 是否作为中继
                ]))
            else:
                # 如果不在观测范围内，填充零向量
                uav_obs.append(np.zeros(8))  # 8是UAV观测的维度
        
        # 观测地面基站
        for gbs in world.ground_base_stations:
            # 计算相对位置
            rel_pos = gbs.state.p_pos - uav.state.p_pos
            dist = np.linalg.norm(rel_pos)
            
            # 检查是否在观测范围内
            if dist <= uav.observation_range:
                # 相对位置
                norm_rel_pos = rel_pos.copy()
                norm_rel_pos[:2] /= uav.observation_range
                norm_rel_pos[2] /= 300.0
                
                # 合并这个GBS的观测
                gbs_obs.append(norm_rel_pos)  # 只观测相对位置
            else:
                # 如果不在观测范围内，填充零向量
                gbs_obs.append(np.zeros(3))  # 3是GBS观测的维度
        
        # 观测用户设备
        for ue in world.user_equipments:
            # 计算相对位置
            rel_pos = ue.state.p_pos - uav.state.p_pos
            dist = np.linalg.norm(rel_pos)
            
            # 检查是否在观测范围内
            if dist <= uav.observation_range:
                # 相对位置
                norm_rel_pos = rel_pos.copy()
                norm_rel_pos[:2] /= uav.observation_range
                norm_rel_pos[2] /= 300.0
                
                # 服务请求状态
                service_req = 1.0 if ue.service_requested else 0.0
                
                # 合并这个UE的观测
                ue_obs.append(np.concatenate([
                    norm_rel_pos,    # 归一化相对位置
                    [service_req]    # 服务请求状态
                ]))
            else:
                # 如果不在观测范围内，填充零向量
                ue_obs.append(np.zeros(4))  # 4是UE观测的维度
        
        # 确保观测向量长度一致，如果实体数量少于预期，用零填充
        n_uav = len(world.uavs) - 1  # 除自己外的UAV数量
        n_gbs = len(world.ground_base_stations)
        n_ue = len(world.user_equipments)
        
        # 确保UAV观测向量的长度
        if len(uav_obs) < n_uav:
            for _ in range(n_uav - len(uav_obs)):
                uav_obs.append(np.zeros(8))
        elif len(uav_obs) > n_uav:
            uav_obs = uav_obs[:n_uav]
            
        # 确保GBS观测向量的长度
        if len(gbs_obs) < n_gbs:
            for _ in range(n_gbs - len(gbs_obs)):
                gbs_obs.append(np.zeros(3))
        elif len(gbs_obs) > n_gbs:
            gbs_obs = gbs_obs[:n_gbs]
            
        # 确保UE观测向量的长度
        if len(ue_obs) < n_ue:
            for _ in range(n_ue - len(ue_obs)):
                ue_obs.append(np.zeros(4))
        elif len(ue_obs) > n_ue:
            ue_obs = ue_obs[:n_ue]
        
        # 将所有观测向量扁平化并连接
        uav_obs_flat = np.concatenate(uav_obs) if uav_obs else np.array([])
        gbs_obs_flat = np.concatenate(gbs_obs) if gbs_obs else np.array([])
        ue_obs_flat = np.concatenate(ue_obs) if ue_obs else np.array([])
        
        # 合并所有观测
        return np.concatenate([own_state, uav_obs_flat, gbs_obs_flat, ue_obs_flat])

    def info(self, uav, world):
        """
        为单个无人机提供附加信息，用于记录和调试
        
        Args:
            uav: 无人机对象
            world: 世界对象
            
        Returns:
            info: 信息字典
        """
        return {
            'battery': uav.state.battery,
            'is_serving': uav.state.is_serving,
            'is_relaying': uav.state.is_relaying,
            'num_connected_ues': len(uav.state.connected_ues) if uav.state.connected_ues else 0,
            'backhaul_quality': uav.state.backhaul_link_quality
        }

    def done(self, uav, world):
        """
        判断单个无人机是否结束
        
        Args:
            uav: 无人机对象
            world: 世界对象
            
        Returns:
            done: 是否结束
        """
        # 如果电池耗尽，认为该UAV结束
        if uav.state.battery <= 0:
            return True
            
        # 如果达到最大步数，结束
        if world.world_step >= world.world_length:
            return True
            
        # 其他条件
        return False
