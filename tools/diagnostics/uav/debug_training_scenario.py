#!/usr/bin/env python3
"""
使用训练时的实际参数测试relay.forced_relay
验证在真实训练参数下的SINR和覆盖率表现
"""

import numpy as np

from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv

def test_training_parameters():
    """使用训练时的实际参数进行测试"""
    print("=" * 60)
    print("使用训练参数测试relay.forced_relay")
    print("=" * 60)
    
    # 使用训练时的实际参数
    env = UAVForcedRelayEnv(
        n_uavs=12,  # 训练时的UAV数量
        n_users=80,  # 训练时的用户数量
        area_size=2500,  # 训练时的区域大小
        seed=42,
        randomize_bs=True,  # 训练时的随机化设置
        randomize_users=True,
        randomize_uav_start=True,
    )
    
    print(f"训练参数:")
    print(f"  - 无人机数量: {env.n_uavs}")
    print(f"  - 用户数量: {env.n_users}")
    print(f"  - 区域大小: {env.area_size}m x {env.area_size}m")
    print(f"  - 最小SINR阈值: {env.min_sinr} dB")
    print(f"  - 发射功率: {env.tx_power} dBm")
    print(f"  - 噪声功率: {env.noise_power} dBm")
    print()
    
    # 测试多个随机种子
    seeds = [42, 123, 456, 789, 999]
    results = []
    
    for seed in seeds:
        env_test = UAVForcedRelayEnv(
            n_uavs=12, n_users=80, area_size=2500,
            seed=seed,
            randomize_bs=True,
            randomize_users=True, 
            randomize_uav_start=True,
        )
        
        obs, info = env_test.reset(seed=seed)
        
        # 统计SINR满足阈值的连接数
        valid_sinr_count = 0
        total_pairs = env_test.n_uavs * env_test.n_users
        
        for i in range(env_test.n_uavs):
            for j in range(env_test.n_users):
                if env_test.sinr_matrix[i, j] >= env_test.min_sinr:
                    valid_sinr_count += 1
        
        # 统计实际连接数
        total_connections = np.sum(env_test.connections)
        
        # 统计有路由路径的UAV数量
        connected_uavs = len(env_test.routing_paths) if hasattr(env_test, 'routing_paths') else 0
        
        # 计算覆盖率
        effective_users = 0
        if hasattr(env_test, 'routing_paths'):
            for i in range(env_test.n_uavs):
                if i in env_test.routing_paths and env_test.routing_paths[i][0]:
                    effective_users += np.sum(env_test.connections[i])
        
        coverage_ratio = effective_users / env_test.n_users
        
        results.append({
            'seed': seed,
            'valid_sinr': valid_sinr_count,
            'total_pairs': total_pairs,
            'sinr_ratio': valid_sinr_count / total_pairs,
            'connections': total_connections,
            'connected_uavs': connected_uavs,
            'coverage_ratio': coverage_ratio,
            'effective_users': effective_users
        })
        
        print(f"种子 {seed:3d}: SINR满足 {valid_sinr_count:3d}/{total_pairs:3d} ({valid_sinr_count/total_pairs*100:5.1f}%), "
              f"连接 {total_connections:2d}, 有路径UAV {connected_uavs:2d}, 覆盖率 {coverage_ratio*100:5.1f}%")
    
    # 计算统计信息
    avg_sinr_ratio = np.mean([r['sinr_ratio'] for r in results])
    avg_connections = np.mean([r['connections'] for r in results])
    avg_connected_uavs = np.mean([r['connected_uavs'] for r in results])
    avg_coverage = np.mean([r['coverage_ratio'] for r in results])
    
    print(f"\n平均统计:")
    print(f"  - 平均SINR满足率: {avg_sinr_ratio*100:.1f}%")
    print(f"  - 平均连接数: {avg_connections:.1f}")
    print(f"  - 平均有路径UAV数: {avg_connected_uavs:.1f}")
    print(f"  - 平均覆盖率: {avg_coverage*100:.1f}%")
    
    return results

def analyze_distance_impact():
    """分析距离对SINR的影响"""
    print("\n" + "=" * 60)
    print("分析距离对SINR的影响")
    print("=" * 60)
    
    env = UAVForcedRelayEnv(n_uavs=1, n_users=1, area_size=2500, seed=42)
    
    # 测试不同距离下的SINR
    distances = [100, 200, 500, 1000, 1500, 2000, 2500]
    
    print("距离(m)  路径损耗(dB)  接收功率(dBm)  SINR(dB)  满足阈值")
    print("-" * 55)
    
    for dist in distances:
        # 设置UAV和用户位置
        uav_pos = np.array([1000, 1000, 100])  # 中心位置，100米高度
        user_pos = np.array([1000 + dist, 1000, 1.5])  # 水平距离为dist
        
        # 计算路径损耗
        path_loss = env._compute_air_to_ground_path_loss(uav_pos, user_pos)
        
        # 计算接收功率
        rx_power = env.tx_power - path_loss
        
        # 计算SINR（假设无干扰）
        noise_power_linear = 10 ** (env.noise_power / 10)
        rx_power_linear = 10 ** (rx_power / 10)
        sinr_db = 10 * np.log10(rx_power_linear / noise_power_linear)
        
        meets_threshold = sinr_db >= env.min_sinr
        
        print(f"{dist:6d}   {path_loss:8.2f}      {rx_power:8.2f}     {sinr_db:6.2f}    {'✓' if meets_threshold else '✗'}")

def analyze_backhaul_problem():
    """分析回程链路问题"""
    print("\n" + "=" * 60)
    print("分析回程链路问题")
    print("=" * 60)
    
    env = UAVForcedRelayEnv(
        n_uavs=12, n_users=80, area_size=2500, seed=42,
        randomize_bs=True, randomize_users=True, randomize_uav_start=True
    )
    
    obs, info = env.reset(seed=42)
    
    print("回程链路分析:")
    print(f"基站位置: {env.ground_bs_positions[0]}")
    print()
    
    # 分析每个UAV到基站的连接能力
    print("UAV到基站的连接分析:")
    print("UAV  位置                    距离(m)  路径损耗(dB)  链路容量(Mbps)  能连接")
    print("-" * 75)
    
    uav_bs_capacities = []
    
    for i in range(env.n_uavs):
        uav_pos = env.uav_positions[i]
        bs_pos = env.ground_bs_positions[0]
        
        # 计算距离
        distance = np.linalg.norm(uav_pos - bs_pos)
        
        # 计算链路容量
        capacity = env._get_link_capacity("uav", i, "ground_bs", 0)
        uav_bs_capacities.append(capacity)
        
        # 计算路径损耗
        path_loss = env._compute_air_to_ground_path_loss(uav_pos, bs_pos)
        
        can_connect = capacity > 0
        
        print(f"{i:2d}   ({uav_pos[0]:6.1f},{uav_pos[1]:6.1f},{uav_pos[2]:4.1f})  "
              f"{distance:7.1f}    {path_loss:8.2f}      {capacity/1e6:8.2f}     {'✓' if can_connect else '✗'}")
    
    # 分析UAV间连接
    print(f"\nUAV间连接分析:")
    uav_connections_count = np.sum(env.uav_connections, axis=1)
    print("UAV  连接的其他UAV数量  连接列表")
    print("-" * 40)
    
    for i in range(env.n_uavs):
        connected_uavs = np.where(env.uav_connections[i])[0]
        print(f"{i:2d}        {len(connected_uavs):2d}           {list(connected_uavs)}")
    
    # 分析路由路径
    print(f"\n路由路径分析:")
    if hasattr(env, 'routing_paths') and env.routing_paths:
        for uav_idx, (path, capacity) in env.routing_paths.items():
            path_str = " -> ".join([f"{node[0]}_{node[1]}" for node in path])
            print(f"UAV {uav_idx}: {path_str} (容量: {capacity/1e6:.2f} Mbps)")
    else:
        print("没有找到有效的路由路径")
    
    # 统计分析
    direct_connections = sum(1 for cap in uav_bs_capacities if cap > 0)
    total_with_routes = len(env.routing_paths) if hasattr(env, 'routing_paths') else 0
    
    print(f"\n统计:")
    print(f"  - 能直连基站的UAV: {direct_connections}/{env.n_uavs}")
    print(f"  - 有路由路径的UAV: {total_with_routes}/{env.n_uavs}")
    print(f"  - 平均UAV间连接数: {np.mean(uav_connections_count):.1f}")
    
    return env

if __name__ == "__main__":
    # 运行测试
    results = test_training_parameters()
    analyze_distance_impact()
    analyze_backhaul_problem()
    
    print("\n" + "=" * 60)
    print("结论")
    print("=" * 60)
    
    avg_coverage = np.mean([r['coverage_ratio'] for r in results])
    
    if avg_coverage < 0.1:
        print("❌ 发现问题：在训练参数下覆盖率很低")
        print("可能的原因:")
        print("1. 区域太大(2500m)，UAV数量相对不足")
        print("2. 用户分布过于分散")
        print("3. UAV起始位置不合理")
        print("4. 路由算法在大规模场景下效果不佳")
        print("\n建议的解决方案:")
        print("1. 减小区域大小到1500-2000m")
        print("2. 增加UAV数量到15-20个")
        print("3. 优化用户簇分布，使其更集中")
        print("4. 改进UAV初始位置分布策略")
    else:
        print("✅ 训练参数下的覆盖率表现正常")
        print(f"平均覆盖率: {avg_coverage*100:.1f}%")
