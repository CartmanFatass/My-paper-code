#!/usr/bin/env python3
"""
简化的路由协议调试脚本
用于快速识别和解决路由协议实现中的问题
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互后端

from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv

def create_debug_config():
    """创建用于调试的简化配置"""
    class DebugConfig:
        def __init__(self):
            # 环境基础参数
            self.n_agents = 4  # 减少UAV数量以便调试
            self.n_users = 10  # 减少用户数量
            self.area_size = 1000  # 减小区域大小
            self.height_range = (50, 200)
            self.max_speed = 30
            self.discrete_speeds = [15.0]
            self.time_step = 1.0
            self.max_steps = 50  # 减少步数以快速测试
            
            # 场景特定参数
            self.user_distribution = "forced_relay_cluster"
            self.n_clusters = 2
            self.cluster_std = 60
            self.central_area_ratio = 0.6
            self.n_ground_bs = 1
            self.max_hops = 3
            self.min_sinr = 3
            self.max_connections = 10
            
            # 路由和通信参数
            self.routing_protocol = 'hggr'  # 将在测试中修改
            self.k = 5  # HGGR更新间隔
            self.carrier_frequency = 2e9
            self.tx_power = 23
            self.noise_power = -94
            self.use_fdma = False
            self.bandwidth = 20e6
            self.ground_bs_tx_power = 30
            
            # 奖励和观测参数
            self.reward_type = "health"
            self.observation_radius = 400
            self.max_observed_uavs = 8
            self.max_observed_users = 10
            self.max_observed_bs = 2
            
            # 关闭随机化以便调试
            self.randomize_bs = False
            self.randomize_users = False
            self.randomize_uav_start = False
            
    return DebugConfig()

def test_single_protocol(protocol_name, max_steps=50):
    """测试单个路由协议"""
    print(f"\n=== 测试 {protocol_name.upper()} 协议 ===")
    
    # 创建配置
    config = create_debug_config()
    config.routing_protocol = protocol_name
    config.max_steps = max_steps
    
    try:
        # 创建环境
        env = UAVForcedRelayEnv(config=config, render_mode=None)
        print(f"✓ 环境创建成功")
        
        # 重置环境
        obs, infos = env.reset(seed=42)
        print(f"✓ 环境重置成功")
        print(f"  UAV数量: {env.n_uavs}")
        print(f"  用户数量: {env.n_users}")
        print(f"  基站数量: {env.n_ground_bs}")
        
        # 检查初始连接状态
        initial_connections = np.sum(env.connections)
        initial_routing_paths = len(env.routing_paths)
        print(f"  初始用户连接数: {initial_connections}")
        print(f"  初始路由路径数: {initial_routing_paths}")
        
        # 运行几个步骤
        packets_sent = 0
        packets_arrived = 0
        max_coverage = 0
        
        for step in range(max_steps):
            # 使用随机动作（对于调试已足够）
            actions = {}
            for agent in env.agents:
                actions[agent] = np.random.randint(0, env.n_discrete_actions)
            
            # 执行步骤
            obs, rewards, terminations, truncations, infos = env.step(actions)
            
            # 收集统计信息
            if 'uav_0' in infos and 'reward_info' in infos['uav_0']:
                reward_info = infos['uav_0']['reward_info']
                coverage = reward_info.get('coverage_ratio', 0)
                max_coverage = max(max_coverage, coverage)
                
            # 收集数据包统计
            packets_sent = env.metrics['packets_sent']
            packets_arrived = env.metrics['packets_arrived']
            
            # 每10步输出一次状态
            if step % 10 == 0:
                connections = np.sum(env.connections)
                routing_paths = len(env.routing_paths)
                print(f"  步骤 {step}: 连接数={connections}, 路径数={routing_paths}, 覆盖率={coverage:.2%}")
        
        # 最终统计
        final_connections = np.sum(env.connections)
        final_routing_paths = len(env.routing_paths)
        pdr = (packets_arrived / packets_sent * 100) if packets_sent > 0 else 0
        
        print(f"✓ {protocol_name.upper()} 协议测试完成")
        print(f"  最终连接数: {final_connections}")
        print(f"  最终路径数: {final_routing_paths}")
        print(f"  最大覆盖率: {max_coverage:.2%}")
        print(f"  数据包发送: {packets_sent}")
        print(f"  数据包到达: {packets_arrived}")
        print(f"  PDR: {pdr:.1f}%")
        
        # 检查路由协议开销
        if hasattr(env, 'router') and env.router:
            overhead = env.router.get_and_reset_overhead()
            print(f"  路由开销: {overhead} 数据包")
        
        env.close()
        return True, {
            'max_coverage': max_coverage,
            'final_connections': final_connections,
            'final_routing_paths': final_routing_paths,
            'packets_sent': packets_sent,
            'packets_arrived': packets_arrived,
            'pdr': pdr
        }
        
    except Exception as e:
        print(f"✗ {protocol_name.upper()} 协议测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """主测试函数"""
    print("=== 路由协议调试测试 ===")
    print("这个测试将快速验证每个路由协议的基本功能")
    
    # 要测试的协议列表
    protocols = ['widest_path', 'hggr', 'geographic', 'aodv', 'dsdv']
    results = {}
    
    for protocol in protocols:
        success, result = test_single_protocol(protocol, max_steps=30)
        results[protocol] = {'success': success, 'data': result}
    
    # 汇总结果
    print("\n=== 测试结果汇总 ===")
    print(f"{'协议':<12} {'成功':<6} {'覆盖率':<8} {'连接数':<6} {'路径数':<6} {'PDR':<8}")
    print("-" * 50)
    
    for protocol, result in results.items():
        if result['success'] and result['data']:
            data = result['data']
            print(f"{protocol.upper():<12} {'✓':<6} {data['max_coverage']:<7.1%} "
                  f"{data['final_connections']:<6} {data['final_routing_paths']:<6} "
                  f"{data['pdr']:<7.1f}%")
        else:
            print(f"{protocol.upper():<12} {'✗':<6} {'N/A':<8} {'N/A':<6} {'N/A':<6} {'N/A':<8}")
    
    # 检查问题
    successful_protocols = [p for p, r in results.items() if r['success']]
    failed_protocols = [p for p, r in results.items() if not r['success']]
    
    if failed_protocols:
        print(f"\n⚠️  失败的协议: {', '.join(failed_protocols)}")
    
    if successful_protocols:
        print(f"✓ 成功的协议: {', '.join(successful_protocols)}")
    else:
        print("⚠️  所有协议都失败了，需要检查环境配置")
    
    # 提供建议
    print("\n=== 调试建议 ===")
    if all(r['success'] for r in results.values()):
        print("✓ 所有协议测试成功！可以运行完整的比较实验。")
    else:
        print("以下是可能的问题和解决方案：")
        print("1. 检查UAV初始位置是否合理")
        print("2. 检查无人机间连接是否正常建立")
        print("3. 检查路由算法实现是否正确")
        print("4. 检查数据包生成逻辑")

if __name__ == "__main__":
    main()
