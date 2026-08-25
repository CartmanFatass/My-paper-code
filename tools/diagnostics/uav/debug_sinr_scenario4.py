#!/usr/bin/env python3
"""
调试relay.forced_relay中的SINR计算
验证覆盖率为0的问题是否由SINR计算错误引起
"""

import numpy as np

from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv

def debug_sinr_calculation():
    """调试SINR计算的各个环节"""
    print("=" * 60)
    print("调试relay.forced_relay中的SINR计算")
    print("=" * 60)
    
    # 创建环境实例
    env = UAVForcedRelayEnv(
        n_uavs=3,  # 减少无人机数量便于调试
        n_users=10,  # 减少用户数量便于调试
        area_size=1000,  # 减小区域便于调试
        seed=42,
        randomize_bs=False,  # 固定基站位置
        randomize_users=False,  # 固定用户位置
        randomize_uav_start=False,  # 固定无人机起始位置
    )
    
    # 重置环境
    obs, info = env.reset(seed=42)
    
    print(f"环境参数:")
    print(f"  - 无人机数量: {env.n_uavs}")
    print(f"  - 用户数量: {env.n_users}")
    print(f"  - 区域大小: {env.area_size}m x {env.area_size}m")
    print(f"  - 最小SINR阈值: {env.min_sinr} dB")
    print(f"  - 发射功率: {env.tx_power} dBm")
    print(f"  - 噪声功率: {env.noise_power} dBm")
    print(f"  - 载波频率: {env.carrier_frequency/1e9:.1f} GHz")
    print()
    
    # 打印位置信息
    print("位置信息:")
    print("无人机位置:")
    for i, pos in enumerate(env.uav_positions):
        print(f"  UAV {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    print("\n用户位置:")
    for i, pos in enumerate(env.user_positions):
        print(f"  User {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    print("\n基站位置:")
    for i, pos in enumerate(env.ground_bs_positions):
        print(f"  BS {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    print()
    
    # 详细分析第一个UAV到第一个用户的SINR计算
    uav_idx = 0
    user_idx = 0
    
    print(f"详细分析 UAV {uav_idx} 到 User {user_idx} 的SINR计算:")
    print("-" * 50)
    
    uav_pos = env.uav_positions[uav_idx]
    user_pos = env.user_positions[user_idx]
    
    # 1. 计算距离
    distance_3d = np.sqrt(np.sum((uav_pos - user_pos) ** 2))
    distance_2d = np.sqrt((uav_pos[0] - user_pos[0])**2 + (uav_pos[1] - user_pos[1])**2)
    height_diff = abs(uav_pos[2] - user_pos[2])
    
    print(f"1. 距离计算:")
    print(f"   3D距离: {distance_3d:.2f} m")
    print(f"   2D距离: {distance_2d:.2f} m")
    print(f"   高度差: {height_diff:.2f} m")
    
    # 2. 计算路径损耗
    path_loss = env._compute_air_to_ground_path_loss(uav_pos, user_pos)
    print(f"2. 路径损耗: {path_loss:.2f} dB")
    
    # 3. 计算接收功率
    rx_power = env.tx_power - path_loss
    print(f"3. 接收功率: {env.tx_power} - {path_loss:.2f} = {rx_power:.2f} dBm")
    
    # 4. 计算SINR
    sinr_db = env._compute_uav_to_user_sinr(uav_idx, user_idx, rx_power)
    print(f"4. SINR: {sinr_db:.2f} dB")
    
    # 5. 检查是否满足阈值
    meets_threshold = sinr_db >= env.min_sinr
    print(f"5. 满足阈值({env.min_sinr} dB): {meets_threshold}")
    print()
    
    # 计算所有UAV-用户对的SINR矩阵
    print("SINR矩阵 (dB):")
    print("UAV\\User", end="")
    for j in range(env.n_users):
        print(f"{j:8}", end="")
    print()
    
    valid_connections = 0
    total_pairs = 0
    
    for i in range(env.n_uavs):
        print(f"UAV {i:2}  ", end="")
        for j in range(env.n_users):
            sinr = env.sinr_matrix[i, j]
            print(f"{sinr:8.2f}", end="")
            total_pairs += 1
            if sinr >= env.min_sinr:
                valid_connections += 1
        print()
    
    print(f"\n满足SINR阈值的连接数: {valid_connections}/{total_pairs}")
    print(f"连接比例: {valid_connections/total_pairs*100:.1f}%")
    print()
    
    # 检查连接分配结果
    print("连接分配结果:")
    total_connections = 0
    for i in range(env.n_uavs):
        connected_users = np.where(env.connections[i])[0]
        total_connections += len(connected_users)
        print(f"UAV {i}: 连接用户 {list(connected_users)}")
    
    print(f"总连接数: {total_connections}")
    print()
    
    # 检查路由路径
    print("路由路径:")
    if hasattr(env, 'routing_paths') and env.routing_paths:
        for uav_idx, (path, capacity) in env.routing_paths.items():
            path_str = " -> ".join([f"{node[0]}_{node[1]}" for node in path])
            print(f"UAV {uav_idx}: {path_str} (容量: {capacity/1e6:.2f} Mbps)")
    else:
        print("没有找到有效的路由路径")
    print()
    
    # 计算覆盖率
    effective_connected_users = 0
    for i in range(env.n_uavs):
        if i in env.routing_paths and env.routing_paths[i][0]:
            effective_connected_users += np.sum(env.connections[i])
    
    coverage_ratio = effective_connected_users / env.n_users
    print(f"有效覆盖用户数: {effective_connected_users}/{env.n_users}")
    print(f"覆盖率: {coverage_ratio*100:.1f}%")
    print()
    
    # 分析可能的问题
    print("问题分析:")
    print("-" * 30)
    
    if valid_connections == 0:
        print("❌ 问题1: 没有任何UAV-用户对满足SINR阈值")
        print("   可能原因:")
        print("   - SINR阈值设置过高")
        print("   - 路径损耗计算过大")
        print("   - 干扰计算过强")
        print("   - 噪声功率设置不合理")
    elif total_connections == 0:
        print("❌ 问题2: SINR满足阈值但连接分配失败")
        print("   可能原因:")
        print("   - 连接分配算法有问题")
        print("   - 最大连接数限制过严")
    elif len(env.routing_paths) == 0:
        print("❌ 问题3: 有连接但没有路由路径")
        print("   可能原因:")
        print("   - UAV到基站的连接失败")
        print("   - 路由算法有问题")
        print("   - 链路容量计算有问题")
    elif coverage_ratio == 0:
        print("❌ 问题4: 有路由路径但覆盖率为0")
        print("   可能原因:")
        print("   - 奖励计算逻辑有问题")
    else:
        print("✅ SINR计算看起来正常")
    
    return env

def test_sinr_components():
    """测试SINR计算的各个组件"""
    print("\n" + "=" * 60)
    print("测试SINR计算组件")
    print("=" * 60)
    
    env = UAVForcedRelayEnv(seed=42)
    env.reset(seed=42)
    
    # 测试路径损耗计算
    uav_pos = np.array([500, 500, 100])  # 中心位置，100米高度
    user_pos = np.array([600, 600, 1.5])  # 距离约141米
    
    print("测试路径损耗计算:")
    print(f"UAV位置: {uav_pos}")
    print(f"用户位置: {user_pos}")
    
    distance_3d = np.sqrt(np.sum((uav_pos - user_pos) ** 2))
    print(f"3D距离: {distance_3d:.2f} m")
    
    # 计算理论自由空间路径损耗
    fspl_theoretical = 20 * np.log10(distance_3d) + 20 * np.log10(env.carrier_frequency) - 147.55
    print(f"理论FSPL: {fspl_theoretical:.2f} dB")
    
    # 计算实际路径损耗
    path_loss_actual = env._compute_air_to_ground_path_loss(uav_pos, user_pos)
    print(f"实际A2G路径损耗: {path_loss_actual:.2f} dB")
    print(f"附加损耗: {path_loss_actual - fspl_theoretical:.2f} dB")
    
    # 测试干扰计算
    print("\n测试干扰计算:")
    rx_power = env.tx_power - path_loss_actual
    print(f"接收功率: {rx_power:.2f} dBm")
    
    # 手动计算噪声限制的SINR
    noise_power_linear = 10 ** (env.noise_power / 10)
    rx_power_linear = 10 ** (rx_power / 10)
    sinr_no_interference = 10 * np.log10(rx_power_linear / noise_power_linear)
    print(f"无干扰SINR: {sinr_no_interference:.2f} dB")
    
    # 计算实际SINR（包含干扰）
    sinr_with_interference = env._compute_uav_to_user_sinr(0, 0, rx_power)
    print(f"含干扰SINR: {sinr_with_interference:.2f} dB")
    print(f"干扰影响: {sinr_no_interference - sinr_with_interference:.2f} dB")

def test_parameter_sensitivity():
    """测试参数敏感性"""
    print("\n" + "=" * 60)
    print("测试参数敏感性")
    print("=" * 60)
    
    # 测试不同的SINR阈值
    print("测试不同SINR阈值的影响:")
    thresholds = [-5, 0, 3, 5, 10]
    
    for threshold in thresholds:
        env = UAVForcedRelayEnv(
            n_uavs=3, n_users=10, area_size=1000,
            min_sinr=threshold, seed=42,
            randomize_bs=False, randomize_users=False, randomize_uav_start=False
        )
        env.reset(seed=42)
        
        # 统计满足阈值的连接数
        valid_connections = 0
        for i in range(env.n_uavs):
            for j in range(env.n_users):
                if env.sinr_matrix[i, j] >= threshold:
                    valid_connections += 1
        
        total_connections = np.sum(env.connections)
        coverage_ratio = 0
        if hasattr(env, 'routing_paths'):
            effective_users = 0
            for i in range(env.n_uavs):
                if i in env.routing_paths and env.routing_paths[i][0]:
                    effective_users += np.sum(env.connections[i])
            coverage_ratio = effective_users / env.n_users
        
        print(f"  阈值 {threshold:2d} dB: 有效SINR {valid_connections:2d}, 实际连接 {total_connections:2d}, 覆盖率 {coverage_ratio*100:5.1f}%")

if __name__ == "__main__":
    # 运行调试
    env = debug_sinr_calculation()
    test_sinr_components()
    test_parameter_sensitivity()
    
    print("\n" + "=" * 60)
    print("调试总结")
    print("=" * 60)
    print("如果覆盖率为0，可能的解决方案:")
    print("1. 降低min_sinr阈值（当前为3dB，可尝试0dB或-5dB）")
    print("2. 增加UAV发射功率（当前为23dBm）")
    print("3. 降低噪声功率（当前为-95dBm）")
    print("4. 减小区域大小或增加UAV数量")
    print("5. 检查路由算法是否正确建立回程链路")
    print("6. 验证干扰计算是否过于保守")
