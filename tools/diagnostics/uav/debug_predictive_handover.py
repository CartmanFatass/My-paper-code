#!/usr/bin/env python3
"""
预测性切换功能调试脚本

专门用于调试为什么在测试中无人机无法建立有效连接
"""

import numpy as np

from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv

def debug_connectivity_issue():
    """调试连接问题"""
    print("=" * 60)
    print("调试: 连接问题分析")
    print("=" * 60)
    
    # 创建一个小规模环境便于调试
    env = UAVForcedRelayEnv(
        n_uavs=3,
        n_users=5,
        area_size=800,  # 较小的区域
        max_steps=50,
        predictive_handover=True,
        user_max_speed=5.0,
        min_sinr=0,  # 降低SINR阈值
        seed=42
    )
    
    obs, infos = env.reset()
    
    print("环境初始化后的状态:")
    print(f"  区域大小: {env.area_size}m x {env.area_size}m")
    print(f"  最小SINR阈值: {env.min_sinr} dB")
    
    # 分析初始位置
    print(f"\n无人机位置:")
    for i in range(env.n_uavs):
        pos = env.uav_positions[i]
        print(f"  UAV {i}: [{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}]")
    
    print(f"\n用户位置:")
    for i in range(min(5, env.n_users)):
        pos = env.user_positions[i]
        print(f"  用户 {i}: [{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}]")
    
    print(f"\n基站位置:")
    for i in range(env.n_ground_bs):
        pos = env.ground_bs_positions[i]
        print(f"  基站 {i}: [{pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}]")
    
    # 分析距离
    print(f"\n距离分析:")
    
    # UAV到用户的距离
    min_uav_user_dist = float('inf')
    max_uav_user_dist = 0
    for i in range(env.n_uavs):
        for j in range(env.n_users):
            dist = np.linalg.norm(env.uav_positions[i] - env.user_positions[j])
            min_uav_user_dist = min(min_uav_user_dist, dist)
            max_uav_user_dist = max(max_uav_user_dist, dist)
    
    print(f"  UAV到用户距离范围: {min_uav_user_dist:.1f}m - {max_uav_user_dist:.1f}m")
    
    # UAV到基站的距离
    min_uav_bs_dist = float('inf')
    max_uav_bs_dist = 0
    for i in range(env.n_uavs):
        for j in range(env.n_ground_bs):
            dist = np.linalg.norm(env.uav_positions[i] - env.ground_bs_positions[j])
            min_uav_bs_dist = min(min_uav_bs_dist, dist)
            max_uav_bs_dist = max(max_uav_bs_dist, dist)
    
    print(f"  UAV到基站距离范围: {min_uav_bs_dist:.1f}m - {max_uav_bs_dist:.1f}m")
    
    # 分析SINR矩阵
    print(f"\nSINR分析:")
    print(f"  SINR矩阵形状: {env.sinr_matrix.shape}")
    
    # 找出最好的SINR值
    max_sinr = np.max(env.sinr_matrix)
    min_sinr = np.min(env.sinr_matrix)
    valid_sinr_count = np.sum(env.sinr_matrix >= env.min_sinr)
    
    print(f"  SINR范围: {min_sinr:.2f} dB - {max_sinr:.2f} dB")
    print(f"  满足阈值的连接数: {valid_sinr_count}")
    
    # 显示前几个最好的SINR值
    flat_sinr = env.sinr_matrix.flatten()
    sorted_indices = np.argsort(flat_sinr)[::-1]  # 降序排列
    
    print(f"  前5个最佳SINR值:")
    for i in range(min(5, len(sorted_indices))):
        idx = sorted_indices[i]
        uav_idx = idx // env.n_users
        user_idx = idx % env.n_users
        sinr_val = flat_sinr[idx]
        dist = np.linalg.norm(env.uav_positions[uav_idx] - env.user_positions[user_idx])
        print(f"    UAV{uav_idx}->用户{user_idx}: {sinr_val:.2f} dB (距离: {dist:.1f}m)")
    
    # 分析连接状态
    print(f"\n连接分析:")
    total_connections = np.sum(env.connections)
    print(f"  总连接数: {total_connections}")
    
    for i in range(env.n_uavs):
        connected_users = np.sum(env.connections[i])
        print(f"  UAV {i}: 连接 {connected_users} 个用户")
    
    # 分析路由路径
    print(f"\n路由分析:")
    print(f"  有路径的UAV数量: {len(env.routing_paths)}")
    
    for uav_idx, (path, capacity) in env.routing_paths.items():
        print(f"  UAV {uav_idx}: 路径长度={len(path)}, 容量={capacity/1e6:.2f} Mbps")
        path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
        print(f"    路径: {path_str}")
    
    env.close()
    return True

def test_optimized_environment():
    """测试优化后的环境配置"""
    print("\n" + "=" * 60)
    print("测试: 优化环境配置")
    print("=" * 60)
    
    # 创建一个更容易建立连接的环境
    env = UAVForcedRelayEnv(
        n_uavs=4,
        n_users=6,
        area_size=600,  # 更小的区域
        max_steps=50,
        predictive_handover=True,
        user_max_speed=8.0,
        min_sinr=-5,  # 更低的SINR阈值
        max_connections=10,  # 更多连接
        height_range=(30, 80),  # 更低的飞行高度
        tx_power=30,  # 更高的发射功率
        seed=42
    )
    
    obs, infos = env.reset()
    
    print("优化环境初始状态:")
    print(f"  区域大小: {env.area_size}m")
    print(f"  最小SINR: {env.min_sinr} dB")
    print(f"  发射功率: {env.tx_power} dBm")
    print(f"  高度范围: {env.height_range}")
    
    # 让无人机移动到更好的位置
    for step in range(10):
        actions = {}
        for i in range(env.n_uavs):
            # 计算到用户中心的方向
            uav_pos = env.uav_positions[i]
            user_center = np.mean(env.user_positions[:, :2], axis=0)
            direction = user_center - uav_pos[:2]
            direction_norm = np.linalg.norm(direction)
            
            if direction_norm > 0:
                direction = direction / direction_norm
                # 强制向用户中心移动
                action = np.array([direction[0] * 0.8, direction[1] * 0.8, -0.3])  # 降低高度
            else:
                action = np.array([0, 0, -0.3])
            
            actions[f"uav_{i}"] = action
        
        obs, rewards, terminations, truncations, infos = env.step(actions)
        
        if step % 3 == 0:
            reward_info = infos["uav_0"]["reward_info"]
            print(f"\n步骤 {step + 1}:")
            print(f"  覆盖率: {reward_info.get('coverage_ratio', 0):.1%}")
            print(f"  系统吞吐量: {reward_info.get('system_throughput_mbps', 0):.2f} Mbps")
            print(f"  连接UAV: {len(env.routing_paths)}/{env.n_uavs}")
            print(f"  切换次数: {env.handover_count}")
            print(f"  切换奖励: {reward_info.get('handover_reward', 0):.4f}")
            
            # 显示最佳SINR
            max_sinr = np.max(env.sinr_matrix)
            valid_connections = np.sum(env.sinr_matrix >= env.min_sinr)
            print(f"  最佳SINR: {max_sinr:.2f} dB")
            print(f"  有效连接: {valid_connections}")
    
    final_reward_info = infos["uav_0"]["reward_info"]
    final_coverage = final_reward_info.get("coverage_ratio", 0)
    final_throughput = final_reward_info.get("system_throughput_mbps", 0)
    
    print(f"\n最终结果:")
    print(f"  最终覆盖率: {final_coverage:.1%}")
    print(f"  最终吞吐量: {final_throughput:.2f} Mbps")
    print(f"  总切换次数: {env.handover_count}")
    
    success = final_coverage > 0 or final_throughput > 0
    
    env.close()
    print("✓ 优化环境测试通过" if success else "✗ 优化环境测试失败")
    return success

def test_manual_positioning():
    """测试手动定位以确保连接"""
    print("\n" + "=" * 60)
    print("测试: 手动定位验证功能")
    print("=" * 60)
    
    env = UAVForcedRelayEnv(
        n_uavs=2,
        n_users=3,
        area_size=500,
        max_steps=20,
        predictive_handover=True,
        min_sinr=-10,  # 非常低的阈值
        seed=42
    )
    
    obs, infos = env.reset()
    
    # 手动设置无人机位置，确保能够建立连接
    # UAV 0 靠近用户
    env.uav_positions[0] = [env.user_positions[0, 0] + 50, env.user_positions[0, 1] + 50, 50]
    # UAV 1 在UAV 0和基站之间
    bs_pos = env.ground_bs_positions[0]
    uav0_pos = env.uav_positions[0]
    mid_pos = (bs_pos + uav0_pos) / 2
    env.uav_positions[1] = [mid_pos[0], mid_pos[1], 60]
    
    print("手动设置位置:")
    print(f"  UAV 0: {env.uav_positions[0]}")
    print(f"  UAV 1: {env.uav_positions[1]}")
    print(f"  用户 0: {env.user_positions[0]}")
    print(f"  基站 0: {env.ground_bs_positions[0]}")
    
    # 重新计算连接
    env._update_channel_state()
    env._update_uav_connections()
    env._compute_routing_paths()
    
    # 分析结果
    print(f"\n连接分析:")
    total_connections = np.sum(env.connections)
    print(f"  总连接数: {total_connections}")
    
    # 显示SINR矩阵
    print(f"\nSINR矩阵:")
    for i in range(env.n_uavs):
        for j in range(env.n_users):
            sinr = env.sinr_matrix[i, j]
            connected = "✓" if env.connections[i, j] else "✗"
            print(f"  UAV{i}->用户{j}: {sinr:.2f} dB {connected}")
    
    # 显示UAV间连接
    print(f"\nUAV间连接:")
    for i in range(env.n_uavs):
        for j in range(i+1, env.n_uavs):
            connected = "✓" if env.uav_connections[i, j] else "✗"
            dist = np.linalg.norm(env.uav_positions[i] - env.uav_positions[j])
            print(f"  UAV{i}<->UAV{j}: {dist:.1f}m {connected}")
    
    # 显示UAV到基站连接
    print(f"\nUAV到基站连接:")
    for i in range(env.n_uavs):
        for j in range(env.n_ground_bs):
            connected = "✓" if env.uav_bs_connections[i, j] else "✗"
            dist = np.linalg.norm(env.uav_positions[i] - env.ground_bs_positions[j])
            print(f"  UAV{i}->基站{j}: {dist:.1f}m {connected}")
    
    # 显示路由路径
    print(f"\n路由路径:")
    if env.routing_paths:
        for uav_idx, (path, capacity) in env.routing_paths.items():
            path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
            print(f"  UAV {uav_idx}: {path_str} (容量: {capacity/1e6:.2f} Mbps)")
    else:
        print("  无有效路径")
    
    # 执行一步，测试奖励计算
    actions = {f"uav_{i}": np.array([0, 0, 0]) for i in range(env.n_uavs)}  # 静止
    obs, rewards, terminations, truncations, infos = env.step(actions)
    
    reward_info = infos["uav_0"]["reward_info"]
    print(f"\n奖励分析:")
    print(f"  覆盖率: {reward_info.get('coverage_ratio', 0):.1%}")
    print(f"  系统吞吐量: {reward_info.get('system_throughput_mbps', 0):.2f} Mbps")
    print(f"  切换奖励: {reward_info.get('handover_reward', 0):.4f}")
    print(f"  中断用户: {reward_info.get('outage_users', 0)}/{env.n_users}")
    
    env.close()
    return True

def test_step_by_step_prediction():
    """逐步测试预测功能"""
    print("\n" + "=" * 60)
    print("测试: 逐步预测功能验证")
    print("=" * 60)
    
    env = UAVForcedRelayEnv(
        n_uavs=2,
        n_users=2,
        area_size=400,
        max_steps=10,
        predictive_handover=True,
        user_max_speed=15.0,  # 高移动性
        min_sinr=-10,
        seed=42
    )
    
    obs, infos = env.reset()
    
    # 手动设置一个良好的初始配置
    env.uav_positions[0] = [200, 200, 50]  # 中心位置
    env.uav_positions[1] = [100, 100, 60]  # 靠近基站
    
    # 重新计算状态
    env._update_channel_state()
    env._update_uav_connections()
    env._compute_routing_paths()
    
    print("初始配置:")
    print(f"  UAV 0: {env.uav_positions[0]}")
    print(f"  UAV 1: {env.uav_positions[1]}")
    
    for step in range(5):
        print(f"\n=== 步骤 {step + 1} ===")
        
        # 显示用户当前和预测位置
        for user_idx in range(env.n_users):
            current_pos = env.user_positions[user_idx, :2]
            kf = env.kalman_filters[user_idx]
            predicted_state = kf.x
            predicted_pos = predicted_state[:2]
            predicted_vel = predicted_state[2:4]
            
            print(f"用户 {user_idx}:")
            print(f"  当前位置: [{current_pos[0]:.1f}, {current_pos[1]:.1f}]")
            print(f"  预测位置: [{predicted_pos[0]:.1f}, {predicted_pos[1]:.1f}]")
            print(f"  预测速度: [{predicted_vel[0]:.1f}, {predicted_vel[1]:.1f}] m/s")
            
            # 计算当前和预测SINR
            for uav_idx in range(env.n_uavs):
                current_sinr = env.sinr_matrix[uav_idx, user_idx]
                predicted_pos_3d = np.array([predicted_pos[0], predicted_pos[1], 1.5])
                predicted_sinr = env._compute_sinr_at_pos(uav_idx, predicted_pos_3d)
                
                print(f"    UAV{uav_idx}: 当前SINR={current_sinr:.2f}dB, 预测SINR={predicted_sinr:.2f}dB")
        
        # 执行步骤
        actions = {f"uav_{i}": np.random.uniform(-0.3, 0.3, 3) for i in range(env.n_uavs)}
        obs, rewards, terminations, truncations, infos = env.step(actions)
        
        # 显示奖励信息
        reward_info = infos["uav_0"]["reward_info"]
        print(f"奖励: {reward_info.get('handover_reward', 0):.4f}")
        print(f"切换: {env.handover_count}, 乒乓: {env.ping_pong_count}")
    
    env.close()
    print("✓ 逐步预测测试完成")
    return True

def main():
    """主调试函数"""
    print("开始预测性切换功能调试")
    print("=" * 80)
    
    debug_functions = [
        ("连接问题分析", debug_connectivity_issue),
        ("优化环境测试", test_optimized_environment),
        ("逐步预测验证", test_step_by_step_prediction)
    ]
    
    for test_name, test_func in debug_functions:
        try:
            print(f"\n执行: {test_name}")
            result = test_func()
            print(f"✓ {test_name} 完成")
        except Exception as e:
            print(f"✗ {test_name} 出现异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
