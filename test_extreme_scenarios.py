import numpy as np
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
import warnings
warnings.filterwarnings('ignore')

def test_extreme_sinr_scenario():
    """测试极端SINR情况下的throughput"""
    print("=== 测试极端SINR场景 ===")
    
    # 创建一个小区域，UAV都靠近地面基站的配置
    env = UAVCooperativeNetworkEnv(
        n_uavs=5,
        n_users=50,
        area_size=100,  # 小区域，容易产生高SINR
        height_range=(50, 60),  # 较低高度
        seed=123
    )
    
    obs, info = env.reset()
    
    # 手动设置UAV位置都非常靠近地面基站
    center_x, center_y = env.area_size/2, env.area_size/2
    for i in range(env.n_uavs):
        # 所有UAV都聚集在中心附近
        env.uav_positions[i] = [
            center_x + np.random.uniform(-10, 10),
            center_y + np.random.uniform(-10, 10),
            55  # 低高度
        ]
    
    # 更新连接状态
    env._update_channel_state()
    env._update_uav_connections()
    env._assign_uav_roles()
    env._compute_routing_paths()
    
    # 计算系统throughput
    reward = env._compute_reward()
    
    if hasattr(env, 'reward_info'):
        info = env.reward_info
        print(f"系统throughput: {info.get('system_throughput_mbps', 'N/A'):.2f} Mbps")
        print(f"连接用户数: {info.get('connected_users', 'N/A')}")
        
        # 检查个别UAV的高throughput
        for i in range(env.n_uavs):
            connected_users = np.where(env.connections[i])[0]
            if len(connected_users) > 0:
                uav_total = sum([env._compute_throughput(i, j) for j in connected_users])
                print(f"UAV {i}: {len(connected_users)}用户, 总需求={uav_total/1e6:.2f}Mbps")
                
                # 检查是否有单UAV超高throughput
                if uav_total > 400e6:
                    print(f"  ⚠️ UAV {i} 异常高throughput!")
                    for j in connected_users:
                        sinr = env.sinr_matrix[i, j]
                        tput = env._compute_throughput(i, j)
                        print(f"    用户{j}: SINR={sinr:.2f}dB, {tput/1e6:.2f}Mbps")

def test_forced_high_sinr():
    """通过修改环境参数强制产生高SINR"""
    print("\n=== 测试强制高SINR场景 ===")
    
    env = UAVCooperativeNetworkEnv(
        n_uavs=5,
        n_users=50,
        area_size=1000,
        seed=456
    )
    
    obs, info = env.reset()
    
    # 人为设置一些极高的SINR值来测试throughput计算
    test_sinr_values = [40, 50, 60]  # 极高的SINR值
    
    print("测试不同SINR下的单链路throughput:")
    for sinr_db in test_sinr_values:
        sinr_linear = 10 ** (sinr_db / 10)
        throughput = env.bandwidth * np.log2(1 + sinr_linear)
        print(f"SINR={sinr_db}dB -> Throughput={throughput/1e6:.2f}Mbps")
        
        if throughput > 300e6:
            print(f"  ⚠️ 单链路throughput超过300Mbps!")

def test_multi_hop_scenarios():
    """测试多跳场景"""
    print("\n=== 测试多跳场景 ===")
    
    # 创建一个配置，强制产生多跳路径
    env = UAVCooperativeNetworkEnv(
        n_uavs=6,
        n_users=30,
        area_size=1500,  # 大区域
        height_range=(100, 150),  # 较高高度，降低与地面基站的连接概率
        min_sinr=10,  # 提高SINR阈值，减少连接
        seed=789
    )
    
    obs, info = env.reset()
    
    # 手动设置UAV位置，创建链式连接
    positions = [
        [200, 200, 120],   # UAV0 - 远离基站
        [400, 400, 120],   # UAV1 - 中继
        [600, 600, 120],   # UAV2 - 中继
        [750, 750, 120],   # UAV3 - 接近基站
        [100, 900, 120],   # UAV4 - 远离基站
        [300, 700, 120],   # UAV5 - 中继
    ]
    
    for i, pos in enumerate(positions):
        if i < env.n_uavs:
            env.uav_positions[i] = pos
    
    # 更新连接状态
    env._update_channel_state()
    env._update_uav_connections()
    env._assign_uav_roles()
    env._compute_routing_paths()
    
    print("路由路径:")
    for i in range(env.n_uavs):
        if i in env.routing_paths:
            path = env.routing_paths[i]
            print(f"  UAV {i}: {path} (跳数: {len(path)})")
            
            # 检查多跳效率计算
            if len(path) > 1:
                hop_count = len(path)
                hop_efficiency = 1.0 / hop_count if hop_count > 0 else 0
                print(f"    跳数效率: {hop_efficiency:.3f}")
                
                if hop_efficiency > 1.0:
                    print(f"    ❌ 异常的跳数效率!")
    
    # 计算系统throughput
    reward = env._compute_reward()
    
    if hasattr(env, 'reward_info'):
        info = env.reward_info
        print(f"\n多跳场景系统throughput: {info.get('system_throughput_mbps', 'N/A'):.2f} Mbps")

def test_boundary_conditions():
    """测试边界条件"""
    print("\n=== 测试边界条件 ===")
    
    env = UAVCooperativeNetworkEnv(
        n_uavs=3,
        n_users=20,
        area_size=1000,
        seed=101112
    )
    
    obs, info = env.reset()
    
    # 测试1: 零距离情况
    print("测试1: 极小距离")
    test_distance = 1e-6  # 极小距离
    path_loss = 20 * np.log10(test_distance) + 20 * np.log10(4 * np.pi * env.carrier_frequency / 3e8)
    print(f"极小距离({test_distance}m)的路径损耗: {path_loss:.2f}dB")
    
    # 测试2: 空路径情况
    print("\n测试2: 空路径处理")
    empty_path = []
    hop_count = len(empty_path)
    hop_efficiency = 1.0 / hop_count if hop_count > 0 else 0
    print(f"空路径的跳数效率: {hop_efficiency}")
    
    # 测试3: 异常大的SINR
    print("\n测试3: 异常大SINR")
    extreme_sinr = 100  # 100dB SINR
    sinr_linear = 10 ** (extreme_sinr / 10)
    throughput = env.bandwidth * np.log2(1 + sinr_linear)
    print(f"100dB SINR -> Throughput={throughput/1e6:.2f}Mbps")
    
    if throughput > 1000e6:
        print(f"  🚨 发现可能导致系统throughput异常高的单链路!")

def main():
    """运行所有极端场景测试"""
    print("🔍 搜索可能导致异常高throughput的场景")
    print("="*60)
    
    test_extreme_sinr_scenario()
    test_forced_high_sinr()
    test_multi_hop_scenarios()
    test_boundary_conditions()
    
    print("\n" + "="*60)
    print("🎯 极端场景测试完成")
    print("如果仍未重现>1100Mbps的问题，可能需要:")
    print("1. 检查实际训练时的具体环境参数")
    print("2. 查看导致异常的具体UAV位置和连接状态")
    print("3. 确认是否在reward计算之外还有其他throughput计算")

if __name__ == "__main__":
    main()
