import numpy as np

class SimplifiedChannelModel:
    """
    简化的无人机通信信道模型，参考3GPP TR 36.777
    实现了简单的路径损耗计算，包括视距(LoS)/非视距(NLoS)场景
    """
    
    def __init__(self):
        # 环境参数
        self.noise_power_dbm = -104.0  # 噪声功率 (dBm)
        self.carrier_frequency_ghz = 2.4  # 载波频率 (GHz)
        
        # 环境类型参数
        self.environment_params = {
            'urban': {
                # 城市环境LoS概率参数
                'a': 9.61,
                'b': 0.16,
                # 路径损耗参数
                'los_alpha': 2.0,
                'los_beta': 32.0,
                'nlos_alpha': 3.5,
                'nlos_beta': 45.0
            },
            'suburban': {
                # 郊区环境参数
                'a': 4.88,
                'b': 0.43,
                'los_alpha': 1.8,
                'los_beta': 30.0,
                'nlos_alpha': 3.0,
                'nlos_beta': 42.0
            },
            'rural': {
                # 农村环境参数
                'a': 3.0,
                'b': 0.1,
                'los_alpha': 1.6,
                'los_beta': 28.0,
                'nlos_alpha': 2.5,
                'nlos_beta': 36.0
            }
        }
    
    def calculate_link_quality(self, link, world):
        """
        计算链路质量
        
        Args:
            link: 要计算的通信链路
            world: 包含环境参数的世界对象
        """
        # 获取收发两端的实体
        tx_entity = link.entity1
        rx_entity = link.entity2
        
        # 计算距离 (3D)
        distance_3d = np.linalg.norm(tx_entity.state.p_pos - rx_entity.state.p_pos)
        
        # 计算视距概率 (LoS概率)
        link.is_los = self._is_line_of_sight(tx_entity, rx_entity, distance_3d, world.environment_type)
        
        # 计算路径损耗
        link.path_loss = self._calculate_path_loss(tx_entity, rx_entity, distance_3d, link.is_los, world.environment_type, world.frequency)
        
        # 计算接收功率 (dBm)
        rx_power_dbm = tx_entity.tx_power - link.path_loss
        
        # 简化的干扰计算 (假设干扰为固定值，实际应根据其他链路进行计算)
        interference_dbm = -110.0
        
        # 计算SINR (dB)
        link.sinr = rx_power_dbm - 10 * np.log10(10**(interference_dbm/10) + 10**(self.noise_power_dbm/10))
        
        # 计算数据速率 (Shannon公式的简化版本，单位：bps)
        bandwidth_hz = 10e6  # 10 MHz
        link.data_rate = bandwidth_hz * np.log2(1 + 10**(link.sinr/10))
    
    def _is_line_of_sight(self, tx_entity, rx_entity, distance_3d, environment_type):
        """
        确定链接是否为视距(LoS)
        使用3GPP提出的概率模型
        """
        # 获取环境参数
        params = self.environment_params.get(environment_type, self.environment_params['urban'])
        
        # 提取发射端和接收端的高度 (假设Z轴为高度)
        h_tx = tx_entity.state.p_pos[2]
        h_rx = rx_entity.state.p_pos[2]
        
        # 计算水平距离
        distance_2d = np.linalg.norm(tx_entity.state.p_pos[:2] - rx_entity.state.p_pos[:2])
        
        # 计算仰角 (弧度)
        if distance_2d > 0:
            elevation_angle = np.arctan((h_tx - h_rx) / distance_2d)
            elevation_angle_deg = elevation_angle * 180.0 / np.pi  # 转换为角度
        else:
            elevation_angle_deg = 90.0 if h_tx > h_rx else -90.0
        
        # 计算LoS概率
        p_los = 1.0 / (1.0 + params['a'] * np.exp(-params['b'] * (elevation_angle_deg - params['a'])))
        
        # 随机决定是否为LoS
        return np.random.random() < p_los
    
    def _calculate_path_loss(self, tx_entity, rx_entity, distance_3d, is_los, environment_type, frequency_ghz):
        """
        计算路径损耗 (dB)
        
        Args:
            tx_entity: 发射实体
            rx_entity: 接收实体
            distance_3d: 3D距离 (m)
            is_los: 是否为视距链路
            environment_type: 环境类型 ('urban', 'suburban', 'rural')
            frequency_ghz: 频率 (GHz)
        
        Returns:
            path_loss: 路径损耗 (dB)
        """
        # 获取环境参数
        params = self.environment_params.get(environment_type, self.environment_params['urban'])
        
        # 自由空间路径损耗
        fspl = 20 * np.log10(distance_3d) + 20 * np.log10(frequency_ghz) + 92.45
        
        if is_los:
            # 视距路径损耗
            path_loss = params['los_alpha'] * 10 * np.log10(distance_3d) + params['los_beta'] + 20 * np.log10(frequency_ghz/2.0)
        else:
            # 非视距路径损耗
            path_loss = params['nlos_alpha'] * 10 * np.log10(distance_3d) + params['nlos_beta'] + 20 * np.log10(frequency_ghz/2.0)
        
        return path_loss
