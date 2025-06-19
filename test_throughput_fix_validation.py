#!/usr/bin/env python3
"""
测试吞吐量修正的验证脚本

用于验证修正后的吞吐量计算是否解决了之前1100Mbps过高的问题
"""

import numpy as np
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv

def test_throughput_calculation():
    """测试吞吐量计算的理论上限"""
    
    print("=== 吞吐量计算修正验证 ===\n")
    
    # 创建环境
    env = UAVCooperativeNetworkEnv(
        n_uavs=5,
        n_users=20,  # 减少用户数以便观察
        area_size=1000,
        max_steps=100,
        seed=42
    )
    
    # 重置环境
    observations, infos = env.reset()
    
    print("环境参数:")
    print(f"- 无人机数量: {env.n_uavs}")
    print(f"- 用户数量: {env.n_users}")
    print(f"- 带宽: {env.bandwidth / 1e6:.1f} MHz")
    print(f"- UAV发射功率: {env.tx_power} dBm")
    print(f"- 地面基站发射功率: {env.ground_bs_tx_power} dBm")
    print(f"- 噪声功率: {env.noise_power} dBm")
    print()
    
    # 理论计算
    print("理论上限分析:")
    
    # 单链路最优SINR下的理论吞吐量
    optimal_sinr_db = 30  # 假设最优SINR为30dB
    optimal_sinr_linear = 10 ** (optimal_sinr_db / 10)
    single_link_max = env.bandwidth * np.log2(1 + optimal_sinr_linear)
    print(f"- 单链路理论最大吞吐量(30dB SINR): {single_link_max / 1e6:.1f} Mbps")
    
    # 系统理论最大吞吐量（所有UAV都在最优条件下）
    system_theoretical_max = env.n_uavs * single_link_max
    print(f"- 系统理论最大吞吐量: {system_theoretical_max / 1e6:.1f} Mbps")
    print()
    
    # 运行几步并监控实际吞吐量
    print("实际运行测试:")
    max_observed_throughput = 0
    
    for step in range(50):
        # 随机动作
        actions = {}
        for agent in env.agents:
            actions[agent] = env.action_spaces[agent].sample()
        
        # 执行步骤
        observations, rewards, terminations, truncations, infos = env.step(actions)
        
        # 获取奖励信息
        if "uav_0" in infos and "reward_info" in infos["uav_0"]:
            reward_info = infos["uav_0"]["reward_info"]
            system_throughput_mbps = reward_info.get("system_throughput_mbps", 0)
            max_observed_throughput = max(max_observed_throughput, system_throughput_mbps)
            
            if step % 10 == 0:
                print(f"步骤 {step:2d}: 系统吞吐量 = {system_throughput_mbps:.1f} Mbps, "
                      f"连接用户 = {reward_info.get('connected_users', 0)}, "
                      f"连通性 = {reward_info.get('connectivity_ratio', 0):.2%}")
    
    print(f"\n最大观察到的系统吞吐量: {max_observed_throughput:.1f} Mbps")
    print(f"系统理论最大吞吐量: {system_theoretical_max / 1e6:.1f} Mbps")
    print(f"观察到的/理论的比值: {max_observed_throughput / (system_theoretical_max / 1e6):.3f}")
    
    # 分析修正效果
    print("\n=== 修正效果分析 ===")
    if max_observed_throughput > system_theoretical_max / 1e6:
        print("❌ 警告: 观察到的吞吐量仍然超过理论上限！")
    elif max_observed_throughput > 500:  # 设置一个合理的阈值
        print("⚠️  注意: 吞吐量仍然较高，可能需要进一步检查")
    else:
        print("✅ 修正成功: 吞吐量在合理范围内")
    
    return max_observed_throughput, system_theoretical_max / 1e6

def test_specific_scenario():
    """测试特定场景：一个UAV连接多个用户的情况"""
    
    print("\n=== 特定场景测试：单UAV多用户 ===")
    
    env = UAVCooperativeNetworkEnv(
        n_uavs=1,
        n_users=5,
        area_size=500,
        max_steps=10,
        seed=42
    )
    
    observations, infos = env.reset()
    
    # 检查连接情况
    connected_users = np.sum(env.connections)
    if connected_users > 0:
        print(f"UAV连接了 {connected_users} 个用户")
        
        # 获取连接的用户索引
        uav_idx = 0
        connected_user_indices = []
        for j in range(env.n_users):
            if env.connections[uav_idx, j]:
                connected_user_indices.append(j)
        
        print(f"连接的用户索引: {connected_user_indices}")
        
        # 计算每个连接的SINR和不同方法下的吞吐量
        total_individual_throughput = 0
        total_shared_throughput = 0
        print("\n各用户链路分析:")
        for user_idx in connected_user_indices:
            sinr_db = env.sinr_matrix[uav_idx, user_idx]
            
            # 旧方法：假设独占全部带宽
            individual_throughput = env._compute_throughput(uav_idx, user_idx)
            total_individual_throughput += individual_throughput
            
            # 新方法：考虑带宽共享
            shared_throughput = env._compute_user_throughput_with_sharing(uav_idx, user_idx)
            total_shared_throughput += shared_throughput
            
            print(f"  用户 {user_idx}: SINR = {sinr_db:.1f} dB, "
                  f"旧方法 = {individual_throughput / 1e6:.1f} Mbps, "
                  f"新方法 = {shared_throughput / 1e6:.1f} Mbps")
        
        print(f"\n对比总吞吐量:")
        print(f"- 旧方法(简单求和): {total_individual_throughput / 1e6:.1f} Mbps")
        print(f"- 新方法(带宽共享): {total_shared_throughput / 1e6:.1f} Mbps")
        
        # 使用修正后的前端容量计算
        frontend_capacity = env._compute_uav_frontend_capacity(uav_idx, connected_user_indices)
        print(f"- 前端总容量: {frontend_capacity / 1e6:.1f} Mbps")
        
        # 理论单UAV最大容量
        optimal_sinr_linear = 10 ** (30 / 10)
        theoretical_max = env.bandwidth * np.log2(1 + optimal_sinr_linear)
        print(f"- 理论单UAV最大容量: {theoretical_max / 1e6:.1f} Mbps")
        
        print(f"\n修正效果:")
        print(f"- 修正前(简单求和): {total_individual_throughput / 1e6:.1f} Mbps")
        print(f"- 修正后(带宽共享): {total_shared_throughput / 1e6:.1f} Mbps")
        print(f"- 减少了: {(total_individual_throughput - total_shared_throughput) / 1e6:.1f} Mbps")
        if total_individual_throughput > 0:
            print(f"- 减少比例: {(1 - total_shared_throughput / total_individual_throughput) * 100:.1f}%")
        
        # 验证：新方法的总吞吐量应该等于前端容量
        print(f"\n验证一致性:")
        print(f"- 新方法总吞吐量: {total_shared_throughput / 1e6:.1f} Mbps")
        print(f"- 前端总容量: {frontend_capacity / 1e6:.1f} Mbps")
        print(f"- 差异: {abs(total_shared_throughput - frontend_capacity) / 1e6:.3f} Mbps")
    
    else:
        print("当前配置下UAV未连接任何用户，请尝试不同的种子值")

if __name__ == "__main__":
    # 测试修正后的吞吐量计算
    max_throughput, theoretical_max = test_throughput_calculation()
    
    # 测试特定场景
    test_specific_scenario()
    
    print(f"\n=== 总结 ===")
    print(f"修正前您观察到的最高吞吐量: 1100 Mbps")
    print(f"修正后观察到的最高吞吐量: {max_throughput:.1f} Mbps")
    print(f"理论最大吞吐量: {theoretical_max:.1f} Mbps")
    
    if max_throughput < 1100 and max_throughput <= theoretical_max:
        print("✅ 修正成功：吞吐量计算现在更加合理")
    else:
        print("⚠️  可能需要进一步调整")
