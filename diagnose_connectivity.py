#!/usr/bin/env python3
"""
连接性诊断脚本
详细检查UAV间连接、UAV到基站连接以及路径计算问题
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')

from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv

def create_debug_config():
    """创建用于调试的配置"""
    class DebugConfig:
        def __init__(self):
            self.n_agents = 4
            self.n_users = 10
            self.area_size = 1000
            self.height_range = (50, 200)
            self.max_speed = 30
            self.discrete_speeds = [15.0]
            self.time_step = 1.0
            self.max_steps = 50
            
            # 场景参数
            self.user_distribution = "forced_relay_cluster"
            self.n_clusters = 2
            self.cluster_std = 60
            self.central_area_ratio = 0.6
            self.n_ground_bs = 1
            self.max_hops = 3
            self.min_sinr = 3  # 降低SINR阈值
            self.max_connections = 10
            
            # 通信参数
            self.routing_protocol = 'widest_path'
            self.k = 5
            self.carrier_frequency = 2e9
            self.tx_power = 23
            self.noise_power = -94
            self.use_fdma = False
            self.bandwidth = 20e6
            self.ground_bs_tx_power = 30
            
            # 观测参数
            self.reward_type = "health"
            self.observation_radius = 400
            self.max_observed_uavs = 8
            self.max_observed_users = 10
            self.max_observed_bs = 2
            
            # 固定配置以便调试
            self.randomize_bs = False
            self.randomize_users = False
            self.randomize_uav_start = False
            
    return DebugConfig()

def diagnose_environment():
    """诊断环境连接性问题"""
    print("=== UAV网络连接性诊断 ===")
    
    config = create_debug_config()
    env = UAVForcedRelayEnv(config=config, render_mode=None)
    obs, infos = env.reset(seed=42)
    
    print(f"环境配置：")
    print(f"  区域大小: {env.area_size}m x {env.area_size}m")
    print(f"  UAV数量: {env.n_uavs}")
    print(f"  用户数量: {env.n_users}")
    print(f"  基站数量: {env.n_ground_bs}")
    print(f"  最小SINR阈值: {env.min_sinr} dB")
    print(f"  最大跳数: {env.max_hops}")
    
    # 1. 检查UAV位置
    print("\n=== UAV位置检查 ===")
    for i in range(env.n_uavs):
        pos = env.uav_positions[i]
        print(f"  UAV {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    # 2. 检查基站位置
    print("\n=== 基站位置检查 ===")
    for i in range(env.n_ground_bs):
        pos = env.ground_bs_positions[i]
        print(f"  BS {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    # 3. 检查用户位置（只显示前5个）
    print("\n=== 用户位置检查（前5个）===")
    for i in range(min(5, env.n_users)):
        pos = env.user_positions[i]
        print(f"  User {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    # 4. 检查UAV到基站的连接
    print("\n=== UAV到基站连接检查 ===")
    uav_bs_connected = []
    for i in range(env.n_uavs):
        connected_bs = []
        for j in range(env.n_ground_bs):
            if env.uav_bs_connections[i, j]:
                connected_bs.append(j)
                uav_bs_connected.append(i)
        if connected_bs:
            print(f"  UAV {i} 连接到 BS {connected_bs}")
        else:
            # 检查为什么不能连接
            uav_pos = env.uav_positions[i]
            bs_pos = env.ground_bs_positions[0]  # 假设只有一个基站
            distance = np.linalg.norm(uav_pos - bs_pos)
            # 计算链路容量
            capacity_to_bs = env._get_link_capacity("uav", i, "ground_bs", 0)
            capacity_from_bs = env._get_link_capacity("ground_bs", 0, "uav", i)
            print(f"  UAV {i} 未连接到BS - 距离: {distance:.1f}m, 到BS容量: {capacity_to_bs:.0f}, 从BS容量: {capacity_from_bs:.0f}")
    
    print(f"  总计 {len(set(uav_bs_connected))}/{env.n_uavs} 个UAV直连基站")
    
    # 5. 检查UAV间连接
    print("\n=== UAV间连接检查 ===")
    uav_connections_count = 0
    for i in range(env.n_uavs):
        connected_uavs = []
        for j in range(env.n_uavs):
            if i != j and env.uav_connections[i, j]:
                connected_uavs.append(j)
                uav_connections_count += 1
        if connected_uavs:
            print(f"  UAV {i} 连接到 UAV {connected_uavs}")
        else:
            print(f"  UAV {i} 未连接任何其他UAV")
    
    print(f"  总计 {uav_connections_count//2} 个UAV间连接")
    
    # 6. 检查用户连接
    print("\n=== 用户连接检查 ===")
    total_user_connections = 0
    for i in range(env.n_uavs):
        connected_users = np.where(env.connections[i])[0]
        if len(connected_users) > 0:
            print(f"  UAV {i} 连接 {len(connected_users)} 个用户: {connected_users.tolist()}")
            total_user_connections += len(connected_users)
        else:
            print(f"  UAV {i} 未连接任何用户")
    
    print(f"  总计 {total_user_connections} 个用户连接")
    
    # 7. 检查路径计算
    print("\n=== 路径计算检查 ===")
    print(f"  当前路由路径数: {len(env.routing_paths)}")
    
    if env.routing_paths:
        for uav_idx, (path, capacity) in env.routing_paths.items():
            path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
            print(f"  UAV {uav_idx}: {path_str} (容量: {capacity:.0f})")
    else:
        print("  没有找到任何有效路径")
        
        # 手动测试路径计算
        print("\n  手动路径查找测试:")
        for uav_idx in range(env.n_uavs):
            path, capacity = env._find_widest_path_to_ground_bs(uav_idx)
            if path:
                path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
                print(f"    UAV {uav_idx}: {path_str} (容量: {capacity:.0f})")
            else:
                print(f"    UAV {uav_idx}: 无路径")
    
    # 8. 连接性分析建议
    print("\n=== 连接性分析 ===")
    
    # 检查是否有UAV直连基站
    direct_bs_connections = len(set(uav_bs_connected))
    if direct_bs_connections == 0:
        print("⚠️  警告：没有UAV能直接连接基站！")
        print("   可能原因：")
        print("   - UAV距离基站太远")
        print("   - SINR阈值太高")
        print("   - 发射功率不足")
        
        # 建议解决方案
        print("   建议解决方案：")
        print("   1. 降低min_sinr阈值（当前: %d dB）" % env.min_sinr)
        print("   2. 增加基站发射功率（当前: %d dBm）" % env.ground_bs_tx_power)
        print("   3. 将UAV初始位置设置得更靠近基站")
    else:
        print(f"✓ 有 {direct_bs_connections} 个UAV可以直连基站")
    
    # 检查UAV间连接
    if uav_connections_count == 0:
        print("⚠️  警告：UAV间没有任何连接！")
        print("   这意味着无法形成中继网络")
    else:
        print(f"✓ UAV间有 {uav_connections_count//2} 个连接")
    
    # 检查网络连通性
    if direct_bs_connections > 0 and uav_connections_count > 0:
        print("✓ 网络具备基本连通性，应该能够计算路径")
    elif direct_bs_connections > 0:
        print("⚠️  只有直连基站的UAV能提供服务，无中继能力")
    else:
        print("✗ 网络缺乏基本连通性，无法提供服务")
    
    env.close()

if __name__ == "__main__":
    diagnose_environment()
