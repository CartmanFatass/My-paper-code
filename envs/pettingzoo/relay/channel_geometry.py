import numpy as np


class RelayChannelGeometry:
    def _compute_distance(self, pos1, pos2):
        return np.sqrt(np.sum((pos1 - pos2) ** 2))

    def _compute_path_loss(self, uav_pos, user_pos):
        """
        重写父类的路径损耗计算方法，使用精确的A2G模型

        参数:
            uav_pos: 无人机位置 [3]
            user_pos: 用户位置 [3] 或索引

        返回:
            path_loss: 路径损耗 (dB)
        """
        # 检查 user_pos 是否为整数索引，如果是则获取对应的用户位置
        if isinstance(user_pos, (int, np.integer)):
            user_pos = self.user_positions[user_pos]

        # 确保 user_pos 是三维的 (x, y, z)
        if len(user_pos) >= 3:
            user_pos_3d = user_pos[:3]
        else:
            # 兼容性处理：如果传入的是二维位置，则添加1.5米高度
            user_pos_3d = np.append(user_pos, 1.5)

        # 使用scenario4中的精确A2G路径损耗模型
        return self._compute_air_to_ground_path_loss(uav_pos, user_pos_3d)

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
            env_type = "urban"  # 默认城市环境

        # Use the standard ITU-R P.1411 / Al-Hourani LoS Probability Model
        if env_type == "suburban":
            a = 0.1
            b = 7.5e-4
        elif env_type == "urban":
            a = 0.3
            b = 5e-4
        elif env_type == "dense_urban":
            a = 0.5
            b = 3e-4
        else: # Default to suburban
            a = 0.1
            b = 7.5e-4

        p_los = 1 / (1 + a * np.exp(-b * (elevation_angle - a)))

        # 环境附加损耗参数
        if env_type == "suburban":
            eta_los, eta_nlos = 1.0, 20.0
        elif env_type == "urban":
            eta_los, eta_nlos = 1.5, 25.0
        elif env_type == "dense_urban":
            eta_los, eta_nlos = 5.0, 30.0
        else:
            eta_los, eta_nlos = 1.0, 20.0

        p_los = np.clip(p_los, 0.0, 1.0)

        # Standard FSPL formula: PL(dB) = 20*log10(d) + 20*log10(f) - 147.55
        fspl = 20 * np.log10(safe_distance_3d) + 20 * np.log10(self.carrier_frequency) - 147.55

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

        # Standard FSPL formula: PL(dB) = 20*log10(d) + 20*log10(f) - 147.55
        path_loss = 20 * np.log10(safe_distance) + 20 * np.log10(self.carrier_frequency) - 147.55

        return path_loss
