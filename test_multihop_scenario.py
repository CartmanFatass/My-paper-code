import numpy as np
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv

def test_multihop_scenario():
    """
    测试多跳回程场景
    通过调整环境参数强制无人机使用多跳路径连接到地面基站
    """
    print("=== 多跳回程场景测试 ===")
    
    # 环境配置
    env_config = {
        "n_uavs": 6,  # 增加无人机数量，提供更多中继选择
        "n_users": 30,  # 减少用户数量，更容易观察
        "area_size": 8000,  # 大区域，更容易产生远距离分布
        "height_range": (100, 200),
        "max_speed": 30,
        "time_step": 1.0,
        "max_steps": 1000,
        "user_distribution": "cluster",  # 聚集分布，易产生远离基站的簇
        "channel_model": "free_space",
        "render_mode": None,
        "seed": 42,  # 固定种子确保可复现
        "min_sinr": 0,  # 先用默认值，后面会调整
        "max_connections": 8,
        "max_hops": 4,  # 允许最多4跳
        "coverage_weight": 0.3,
        "quality_weight": 0.2,
        "connectivity_weight": 0.3,
        "throughput_weight": 0.2,
        "n_ground_bs": 1,  # 单个地面基站
    }
    
    print(f"环境配置:")
    for key, value in env_config.items():
        print(f"  {key}: {value}")
    
    # 创建环境
    env = UAVCooperativeNetworkEnv(**env_config)
    
    # 关键：调整通信参数以缩短有效通信距离
    original_tx_power = env.tx_power
    original_min_sinr = env.min_sinr
    original_ground_bs_tx_power = env.ground_bs_tx_power
    
    # 大幅降低发射功率和提高SINR门槛
    env.tx_power = 5  # 从20 dBm降低到5 dBm
    env.min_sinr = 8  # 从0 dB提高到8 dB
    env.ground_bs_tx_power = 15  # 从30 dBm降低到15 dBm
    
    print(f"\n通信参数调整:")
    print(f"  无人机发射功率: {original_tx_power} dBm -> {env.tx_power} dBm")
    print(f"  最小SINR阈值: {original_min_sinr} dB -> {env.min_sinr} dB")
    print(f"  地面基站发射功率: {original_ground_bs_tx_power} dBm -> {env.ground_bs_tx_power} dBm")
    
    # 计算调整后的理论通信距离
    wavelength = 3e8 / env.carrier_frequency
    constant_term = 20 * np.log10(4 * np.pi / wavelength)
    
    # UAV间通信距离
    max_path_loss_uav = env.tx_power - env.noise_power - env.min_sinr
    max_distance_uav = 10 ** ((max_path_loss_uav - constant_term) / 20)
    
    # 地面基站到UAV通信距离  
    max_path_loss_bs = env.ground_bs_tx_power - env.noise_power - env.min_sinr
    max_distance_bs = 10 ** ((max_path_loss_bs - constant_term) / 20)
    
    print(f"\n调整后理论最大通信距离:")
    print(f"  UAV间通信: {max_distance_uav:.0f} 米")
    print(f"  地面基站到UAV: {max_distance_bs:.0f} 米")
    
    # 寻找合适的场景布局
    print("\n正在寻找合适的多跳场景布局...")
    max_attempts = 50
    suitable_scenario_found = False
    
    for attempt in range(max_attempts):
        observations, infos = env.reset(seed=42+attempt)
        
        # 检查用户簇中心与地面基站的距离
        if hasattr(env, 'user_positions') and hasattr(env, 'ground_bs_positions'):
            # 计算用户质心
            user_centroid = np.mean(env.user_positions, axis=0)
            
            # 计算到地面基站的距离
            bs_pos = env.ground_bs_positions[0]
            distance_to_bs = np.sqrt(np.sum((user_centroid - bs_pos[:2])**2))
            
            print(f"  尝试 {attempt+1}: 用户簇中心距离地面基站 {distance_to_bs:.0f} 米")
            
            # 如果距离足够远，可能需要多跳
            if distance_to_bs > max_distance_bs * 0.7:  # 70%的最大距离作为阈值
                print(f"  -> 发现合适的布局！用户簇距离基站较远，可能需要多跳回程")
                suitable_scenario_found = True
                break
    
    if not suitable_scenario_found:
        print(f"  警告: {max_attempts}次尝试后未找到理想布局，使用最后一次布局")
    
    # 打印初始状态
    print(f"\n=== 初始状态 ===")
    print(f"地面基站位置: {env.ground_bs_positions[0]}")
    print(f"用户分布范围: X[{env.user_positions[:, 0].min():.0f}, {env.user_positions[:, 0].max():.0f}], "
          f"Y[{env.user_positions[:, 1].min():.0f}, {env.user_positions[:, 1].max():.0f}]")
    print(f"无人机初始位置:")
    for i, pos in enumerate(env.uav_positions):
        print(f"  UAV {i}: [{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}]")
    
    # 运行几个步骤，观察路由路径的建立
    print(f"\n=== 运行步骤并观察路由路径 ===")
    
    for step in range(5):
        print(f"\n--- 步骤 {step+1} ---")
        
        # 随机动作（这里主要关注路由，不关注具体的移动策略）
        actions = {}
        for agent in env.agents:
            actions[agent] = env.action_space(agent).sample()
        
        # 执行步骤
        observations, rewards, terminations, truncations, infos = env.step(actions)
        
        # 分析路由路径
        print(f"UAV角色分配:")
        role_names = ["未分配", "基站", "中继"]
        for i, role in enumerate(env.uav_roles):
            print(f"  UAV {i}: {role_names[role]} (连接用户数: {np.sum(env.connections[i])})")
        
        print(f"路由路径:")
        multihop_found = False
        for uav_idx, path in env.routing_paths.items():
            hops = len(path)
            if hops > 1:
                multihop_found = True
                print(f"  UAV {uav_idx}: {path} ({hops}跳) <- 多跳路径!")
            else:
                print(f"  UAV {uav_idx}: {path} ({hops}跳)")
        
        # 连通性统计
        connectivity_ratio = env._compute_connectivity_ratio()
        connected_users = np.sum(env.connections)
        
        print(f"网络统计:")
        print(f"  连通UAV比例: {connectivity_ratio:.2%}")
        print(f"  已连接用户: {connected_users}/{env.n_users}")
        print(f"  全局奖励: {rewards[env.agents[0]] * env.n_uavs:.4f}")
        
        if multihop_found:
            print("  ✅ 检测到多跳回程路径!")
        else:
            print("  ❌ 未检测到多跳回程路径")
        
        # 如果检测到多跳路径，提供详细分析
        if multihop_found:
            print(f"\n多跳路径详细分析:")
            for uav_idx, path in env.routing_paths.items():
                if len(path) > 1:
                    print(f"  UAV {uav_idx} 的路径:")
                    for i, (node_type, node_idx) in enumerate(path):
                        if node_type == "uav":
                            pos = env.uav_positions[node_idx]
                            print(f"    跳 {i+1}: UAV {node_idx} at [{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}]")
                        elif node_type == "ground_bs":
                            pos = env.ground_bs_positions[node_idx]
                            print(f"    跳 {i+1}: 地面基站 {node_idx} at [{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}]")
    
    print(f"\n=== 测试完成 ===")
    
    # 最终统计
    final_multihop_paths = sum(1 for path in env.routing_paths.values() if len(path) > 1)
    total_paths = len(env.routing_paths)
    
    print(f"最终结果:")
    print(f"  总路由路径数: {total_paths}")
    print(f"  多跳路径数: {final_multihop_paths}")
    print(f"  多跳比例: {final_multihop_paths/max(total_paths, 1):.2%}")
    
    if final_multihop_paths > 0:
        print("  ✅ 成功创建了需要多跳回程的场景!")
    else:
        print("  ❌ 未能创建多跳场景，可能需要进一步调整参数")
        print("     建议: 进一步降低发射功率或增大区域范围")
    
    return final_multihop_paths > 0

if __name__ == "__main__":
    success = test_multihop_scenario()
    if success:
        print("\n🎉 多跳回程场景测试成功!")
    else:
        print("\n⚠️  多跳回程场景测试未达到预期，需要调整参数")
