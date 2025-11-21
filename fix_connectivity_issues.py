#!/usr/bin/env python3
"""
修复连接性问题的脚本
通过调整参数和位置来确保UAV网络具有基本连通性
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')

from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv

def create_fixed_config():
    """创建修复后的配置"""
    class FixedConfig:
        def __init__(self):
            # 环境基础参数
            self.n_agents = 4
            self.n_users = 10
            self.area_size = 1000
            self.height_range = (50, 200)
            self.max_speed = 30
            self.discrete_speeds = [15.0]
            self.time_step = 1.0
            self.max_steps = 100
            
            # 场景参数
            self.user_distribution = "forced_relay_cluster"
            self.n_clusters = 2
            self.cluster_std = 60
            self.central_area_ratio = 0.6
            self.n_ground_bs = 1
            self.max_hops = 4
            self.min_sinr = -5  # 大幅降低SINR阈值
            self.max_connections = 20
            
            # 增强通信参数
            self.routing_protocol = 'widest_path'
            self.k = 5
            self.carrier_frequency = 2e9
            self.tx_power = 30  # 增加UAV发射功率
            self.noise_power = -100  # 降低噪声功率
            self.use_fdma = False
            self.bandwidth = 20e6
            self.ground_bs_tx_power = 40  # 大幅增加基站发射功率
            
            # 观测参数
            self.reward_type = "health"
            self.observation_radius = 600
            self.max_observed_uavs = 8
            self.max_observed_users = 15
            self.max_observed_bs = 2
            
            # 固定配置确保可重复性
            self.randomize_bs = False
            self.randomize_users = False
            self.randomize_uav_start = False
            
    return FixedConfig()

def test_fixed_connectivity():
    """测试修复后的连接性"""
    print("=== 测试修复后的网络连接性 ===")
    
    config = create_fixed_config()
    
    # 测试不同的路由协议
    protocols = ['widest_path', 'hggr', 'geographic']
    
    for protocol in protocols:
        print(f"\n--- 测试 {protocol.upper()} 协议 ---")
        config.routing_protocol = protocol
        
        try:
            env = UAVForcedRelayEnv(config=config, render_mode=None)
            obs, infos = env.reset(seed=42)
            
            print(f"✓ 环境创建成功")
            print(f"  配置: SINR阈值={env.min_sinr}dB, UAV功率={env.tx_power}dBm, BS功率={env.ground_bs_tx_power}dBm")
            
            # 检查初始连接
            uav_bs_connections = 0
            uav_uav_connections = 0
            user_connections = 0
            
            for i in range(env.n_uavs):
                # 检查UAV到基站连接
                for j in range(env.n_ground_bs):
                    if env.uav_bs_connections[i, j]:
                        uav_bs_connections += 1
                
                # 检查UAV间连接
                for j in range(i+1, env.n_uavs):
                    if env.uav_connections[i, j]:
                        uav_uav_connections += 1
                
                # 检查用户连接
                user_connections += np.sum(env.connections[i])
            
            print(f"  初始连接: UAV-BS={uav_bs_connections}, UAV-UAV={uav_uav_connections}, 用户={user_connections}")
            
            # 运行仿真测试
            max_coverage = 0
            packets_generated = 0
            packets_delivered = 0
            
            for step in range(30):  # 运行30步测试
                # 使用随机动作
                actions = {}
                for agent in env.agents:
                    actions[agent] = np.random.randint(0, env.n_discrete_actions)
                
                obs, rewards, terminations, truncations, infos = env.step(actions)
                
                if 'uav_0' in infos and 'reward_info' in infos['uav_0']:
                    coverage = infos['uav_0']['reward_info'].get('coverage_ratio', 0)
                    max_coverage = max(max_coverage, coverage)
                
                packets_generated = env.metrics['packets_sent']
                packets_delivered = env.metrics['packets_arrived']
                
                if step % 10 == 0:
                    routes = len(env.routing_paths)
                    print(f"    步骤{step}: 路径数={routes}, 覆盖率={coverage:.1%}, 包={packets_generated}/{packets_delivered}")
            
            pdr = (packets_delivered / packets_generated * 100) if packets_generated > 0 else 0
            final_routes = len(env.routing_paths)
            
            print(f"  最终结果: 最大覆盖率={max_coverage:.1%}, 路径数={final_routes}, PDR={pdr:.1f}%")
            
            success = max_coverage > 0 or final_routes > 0 or pdr > 0
            if success:
                print(f"  ✓ {protocol.upper()} 协议连接修复成功！")
            else:
                print(f"  ✗ {protocol.upper()} 协议仍有问题")
            
            env.close()
            
        except Exception as e:
            print(f"  ✗ {protocol.upper()} 协议测试失败: {e}")

def test_manual_uav_placement():
    """测试手动放置UAV的连接性"""
    print("\n=== 测试手动UAV位置优化 ===")
    
    config = create_fixed_config()
    env = UAVForcedRelayEnv(config=config, render_mode=None)
    obs, infos = env.reset(seed=42)  # 需要先reset
    
    # 手动设置UAV位置以确保连通性
    # UAV 0: 靠近基站
    env.uav_positions[0] = np.array([100, 100, 100])  # 距离基站70m左右
    # UAV 1: 中继位置
    env.uav_positions[1] = np.array([250, 250, 120])
    # UAV 2: 另一个中继
    env.uav_positions[2] = np.array([400, 400, 100])
    # UAV 3: 靠近用户区域
    env.uav_positions[3] = np.array([350, 350, 80])
    
    print("优化UAV位置:")
    for i in range(env.n_uavs):
        pos = env.uav_positions[i]
        print(f"  UAV {i}: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f})")
    
    # 重新计算连接
    env._update_channel_state()
    env._update_uav_connections()
    env._compute_routing_paths()
    
    # 检查连接性
    uav_bs_connections = 0
    uav_uav_connections = 0
    user_connections = 0
    
    print("\n连接性检查:")
    for i in range(env.n_uavs):
        # UAV到基站
        bs_connected = []
        for j in range(env.n_ground_bs):
            if env.uav_bs_connections[i, j]:
                bs_connected.append(j)
                uav_bs_connections += 1
        if bs_connected:
            print(f"  UAV {i} -> BS {bs_connected}")
        
        # UAV间连接  
        uav_connected = []
        for j in range(env.n_uavs):
            if i != j and env.uav_connections[i, j]:
                uav_connected.append(j)
                if j > i:  # 避免重复计数
                    uav_uav_connections += 1
        if uav_connected:
            print(f"  UAV {i} -> UAV {uav_connected}")
        
        # 用户连接
        user_count = np.sum(env.connections[i])
        if user_count > 0:
            print(f"  UAV {i} -> {user_count} 用户")
            user_connections += user_count
    
    # 检查路径
    print(f"\n路径检查: {len(env.routing_paths)} 条路径")
    for uav_idx, (path, capacity) in env.routing_paths.items():
        path_str = " -> ".join([f"{node_type}_{node_idx}" for node_type, node_idx in path])
        print(f"  UAV {uav_idx}: {path_str} (容量: {capacity:.0f})")
    
    print(f"\n总结:")
    print(f"  UAV-基站连接: {uav_bs_connections}")
    print(f"  UAV间连接: {uav_uav_connections}")
    print(f"  用户连接: {user_connections}")
    print(f"  有效路径: {len(env.routing_paths)}")
    
    if len(env.routing_paths) > 0:
        print("  ✓ 网络连通性修复成功！")
        return True
    else:
        print("  ✗ 仍需进一步优化")
        return False

def main():
    """主测试函数"""
    print("=== 路由协议连接性修复测试 ===")
    
    # 首先测试参数修复
    test_fixed_connectivity()
    
    # 然后测试位置优化
    success = test_manual_uav_placement()
    
    if success:
        print("\n🎉 连接性问题已修复！")
        print("建议的修复参数:")
        print("- min_sinr: -5 dB (降低阈值)")
        print("- tx_power: 30 dBm (增加UAV功率)")
        print("- ground_bs_tx_power: 40 dBm (增加基站功率)")
        print("- noise_power: -100 dBm (降低噪声)")
        print("- 优化UAV初始位置确保基本连通性")
        
        print("\n现在可以运行完整的路由协议比较实验。")
    else:
        print("\n⚠️  仍需进一步调试连接性问题")

if __name__ == "__main__":
    main()
