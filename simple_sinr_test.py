import numpy as np
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.getcwd())

print("开始简单的SINR和吞吐量测试...")

try:
    from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
    print("成功导入UAVCooperativeNetworkEnv")
    
    # 创建环境
    print("创建环境...")
    env = UAVCooperativeNetworkEnv(
        n_uavs=5,
        n_users=50,
        area_size=1000,
        height_range=(50, 150),
        user_distribution="uniform",
        channel_model="free_space",
        seed=42
    )
    print("环境创建成功")
    
    # 打印基础参数
    print(f"\n=== 基础通信参数 ===")
    print(f"载波频率: {env.carrier_frequency/1e9:.1f} GHz")
    print(f"带宽: {env.bandwidth/1e6:.1f} MHz")
    print(f"UAV发射功率: {env.tx_power} dBm")
    print(f"地面基站发射功率: {env.ground_bs_tx_power} dBm")
    print(f"噪声功率: {env.noise_power} dBm")
    print(f"最小SINR阈值: {env.min_sinr} dB")
    print(f"每UAV最大连接数: {env.max_connections}")
    
    # 重置环境
    print("\n重置环境...")
    observations, infos = env.reset()
    print("环境重置成功")
    
    # 检查连接情况
    print(f"\n=== 连接状态 ===")
    print(f"连接矩阵形状: {env.connections.shape}")
    print(f"总连接数: {np.sum(env.connections)}")
    print(f"连接覆盖率: {np.sum(env.connections)/env.n_users:.2%}")
    
    # SINR分析
    print(f"\n=== SINR分析 ===")
    all_sinrs = env.sinr_matrix.flatten()
    connected_sinrs = env.sinr_matrix[env.connections] if np.sum(env.connections) > 0 else []
    
    print(f"所有SINR统计 (dB):")
    print(f"  均值: {np.mean(all_sinrs):.2f}")
    print(f"  最小值: {np.min(all_sinrs):.2f}")
    print(f"  最大值: {np.max(all_sinrs):.2f}")
    
    if len(connected_sinrs) > 0:
        print(f"已连接链路的SINR统计 (dB):")
        print(f"  均值: {np.mean(connected_sinrs):.2f}")
        print(f"  最小值: {np.min(connected_sinrs):.2f}")
        print(f"  最大值: {np.max(connected_sinrs):.2f}")
    
    # 吞吐量分析
    print(f"\n=== 吞吐量分析 ===")
    individual_throughputs = []
    
    for i in range(env.n_uavs):
        uav_connections = 0
        uav_total_throughput = 0
        
        for j in range(env.n_users):
            if env.connections[i, j]:
                uav_connections += 1
                throughput = env._compute_throughput(i, j)
                throughput_mbps = throughput / 1e6
                individual_throughputs.append(throughput_mbps)
                uav_total_throughput += throughput
        
        print(f"UAV {i}: {uav_connections} 个连接, 总吞吐量: {uav_total_throughput/1e6:.1f} Mbps")
    
    if individual_throughputs:
        print(f"\n单连接吞吐量统计 (Mbps):")
        print(f"  均值: {np.mean(individual_throughputs):.1f}")
        print(f"  最小值: {np.min(individual_throughputs):.1f}")
        print(f"  最大值: {np.max(individual_throughputs):.1f}")
        
        # 检查异常值
        high_throughput = [t for t in individual_throughputs if t > 200]
        if high_throughput:
            print(f"  ⚠️  检测到 {len(high_throughput)} 个高吞吐量连接 (>200Mbps):")
            print(f"      值: {high_throughput}")
    
    # 计算系统总吞吐量
    system_throughput = sum(individual_throughputs)
    print(f"\n系统总吞吐量: {system_throughput:.1f} Mbps")
    
    # 理论分析
    print(f"\n=== 理论分析 ===")
    bandwidth_mhz = env.bandwidth / 1e6
    theoretical_max_single = bandwidth_mhz * np.log2(1 + 1000)  # 30dB SINR
    print(f"理论单连接最大吞吐量 (30dB SINR): {theoretical_max_single:.1f} Mbps")
    
    if individual_throughputs:
        actual_max_single = np.max(individual_throughputs)
        print(f"实际单连接最大吞吐量: {actual_max_single:.1f} Mbps")
        
        if actual_max_single > theoretical_max_single:
            print(f"⚠️  实际值超过理论值！差值: {actual_max_single - theoretical_max_single:.1f} Mbps")
        
        if actual_max_single > 300:
            print(f"⚠️  单连接吞吐量异常高！可能存在计算错误。")
    
    if system_throughput > 1000:
        print(f"⚠️  系统总吞吐量异常高！可能存在累积计算错误。")
    
    print("\n测试完成！")

except Exception as e:
    print(f"测试过程中发生错误: {e}")
    import traceback
    traceback.print_exc()
