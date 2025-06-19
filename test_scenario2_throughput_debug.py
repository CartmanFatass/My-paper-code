import numpy as np
import matplotlib.pyplot as plt
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
import warnings
warnings.filterwarnings('ignore')

class ThroughputDebugger:
    """
    专门用于调试Scenario2中throughput计算问题的调试器
    """
    
    def __init__(self, env_config=None):
        """
        初始化调试器
        
        参数:
            env_config: 环境配置字典
        """
        # 默认配置
        default_config = {
            'n_uavs': 5,
            'n_users': 50,
            'area_size': 1000,
            'height_range': (50, 150),
            'max_speed': 30,
            'time_step': 1.0,
            'max_steps': 100,  # 减少步数用于调试
            'user_distribution': "uniform",
            'channel_model': "free_space",
            'render_mode': None,
            'seed': 42,  # 固定种子确保可重现
            'min_sinr': 0,
            'max_connections': 10,
            'max_hops': 3,
            'coverage_weight': 0.4,
            'quality_weight': 0.2,
            'connectivity_weight': 0.2,
            'throughput_weight': 0.2,
            'n_ground_bs': 1,
        }
        
        if env_config:
            default_config.update(env_config)
        
        self.config = default_config
        self.env = None
        self.debug_info = {}
        
    def create_env(self):
        """创建测试环境"""
        print("=== 创建测试环境 ===")
        self.env = UAVCooperativeNetworkEnv(**self.config)
        
        # 打印基础参数
        print(f"UAV数量: {self.env.n_uavs}")
        print(f"用户数量: {self.env.n_users}")
        print(f"区域大小: {self.env.area_size}m")
        print(f"带宽: {self.env.bandwidth/1e6:.1f} MHz")
        print(f"UAV发射功率: {self.env.tx_power} dBm")
        print(f"地面基站发射功率: {self.env.ground_bs_tx_power} dBm")
        print(f"噪声功率: {self.env.noise_power} dBm")
        print(f"最小SINR: {self.env.min_sinr} dB")
        print()
        
    def test_basic_parameters(self):
        """测试基础参数的合理性"""
        print("=== 测试基础参数 ===")
        
        # 计算理论最大单链路throughput
        max_sinr_db = 30  # 假设最优SINR为30dB
        max_sinr_linear = 10 ** (max_sinr_db / 10)
        max_single_link_throughput = self.env.bandwidth * np.log2(1 + max_sinr_linear)
        
        print(f"最优SINR (30dB) 下单链路理论最大throughput: {max_single_link_throughput/1e6:.2f} Mbps")
        print(f"5个UAV理论最大总throughput (无干扰): {5 * max_single_link_throughput/1e6:.2f} Mbps")
        print(f"5个UAV理论最大总throughput (TDMA): {max_single_link_throughput/1e6:.2f} Mbps")
        print()
        
        return max_single_link_throughput
        
    def test_single_link_throughput(self):
        """测试单链路throughput计算"""
        print("=== 测试单链路Throughput计算 ===")
        
        # 重置环境
        obs, info = self.env.reset()
        
        # 检查几个UAV-用户连接的throughput
        for uav_idx in range(min(3, self.env.n_uavs)):
            connected_users = np.where(self.env.connections[uav_idx])[0]
            
            print(f"\nUAV {uav_idx}:")
            print(f"  连接用户数: {len(connected_users)}")
            
            for user_idx in connected_users[:3]:  # 只检查前3个用户
                sinr_db = self.env.sinr_matrix[uav_idx, user_idx]
                throughput = self.env._compute_throughput(uav_idx, user_idx)
                
                print(f"  用户 {user_idx}: SINR={sinr_db:.2f}dB, Throughput={throughput/1e6:.2f}Mbps")
                
                # 检查是否有异常高的throughput
                if throughput > 300e6:  # 超过300Mbps就是异常
                    print(f"    ⚠️  异常高的throughput值!")
                    
                # 验证香农定理计算
                sinr_linear = 10 ** (sinr_db / 10)
                expected_throughput = self.env.bandwidth * np.log2(1 + sinr_linear)
                if abs(throughput - expected_throughput) > 1e3:  # 1kbps误差容忍
                    print(f"    ❌ 香农定理计算错误! 期望={expected_throughput/1e6:.2f}Mbps")
                else:
                    print(f"    ✅ 香农定理计算正确")
        print()
        
    def test_backhaul_capacity(self):
        """测试回程容量计算"""
        print("=== 测试回程容量计算 ===")
        
        for uav_idx in range(self.env.n_uavs):
            backhaul_capacity = self.env._compute_backhaul_capacity(uav_idx)
            
            print(f"\nUAV {uav_idx}:")
            print(f"  回程容量: {backhaul_capacity/1e6:.2f} Mbps")
            
            # 检查是否有异常大的值
            if backhaul_capacity > 1000e6:  # 超过1000Mbps就是异常
                print(f"  ⚠️  异常高的回程容量!")
                
            if np.isinf(backhaul_capacity) or np.isnan(backhaul_capacity):
                print(f"  ❌ 回程容量计算出现inf或nan!")
                
            # 检查路径信息
            if uav_idx in self.env.routing_paths:
                path = self.env.routing_paths[uav_idx]
                print(f"  路径: {path}")
                print(f"  跳数: {len(path)}")
            else:
                print(f"  无路径到地面基站")
        print()
        
    def debug_routing_paths(self):
        """调试路由路径计算"""
        print("=== 调试路由路径 ===")
        
        print("UAV连接矩阵 (UAV之间):")
        print(self.env.uav_connections.astype(int))
        
        print("\nUAV到地面基站连接矩阵:")
        print(self.env.uav_bs_connections.astype(int))
        
        print("\n各UAV的路由路径:")
        for uav_idx in range(self.env.n_uavs):
            if uav_idx in self.env.routing_paths:
                path = self.env.routing_paths[uav_idx]
                print(f"  UAV {uav_idx}: {path} (跳数: {len(path)})")
            else:
                print(f"  UAV {uav_idx}: 无路径")
        print()
        
    def debug_system_throughput_calculation(self):
        """详细调试系统总throughput计算过程"""
        print("=== 调试系统总Throughput计算 ===")
        
        system_throughput = 0
        uav_details = []
        
        for i in range(self.env.n_uavs):
            print(f"\n--- UAV {i} ---")
            
            # 计算该UAV服务的所有用户的总需求吞吐量
            uav_user_throughput = 0
            connected_users = np.where(self.env.connections[i])[0]
            
            print(f"连接用户: {connected_users}")
            
            for j in connected_users:
                user_throughput = self.env._compute_throughput(i, j)
                uav_user_throughput += user_throughput
                print(f"  用户{j}: {user_throughput/1e6:.2f} Mbps")
            
            print(f"前端总需求: {uav_user_throughput/1e6:.2f} Mbps")
            
            # 获取该UAV的回程容量限制
            if i in self.env.routing_paths:
                backhaul_capacity = self.env._compute_backhaul_capacity(i)
                
                # 考虑多跳效率损失
                path = self.env.routing_paths[i]
                hop_count = len(path)
                hop_efficiency = 1.0 / hop_count if hop_count > 0 else 0
                
                print(f"回程容量: {backhaul_capacity/1e6:.2f} Mbps")
                print(f"跳数: {hop_count}")
                print(f"跳数效率: {hop_efficiency:.3f}")
                
                # 检查异常值
                if hop_count <= 0:
                    print(f"  ❌ 异常的跳数: {hop_count}")
                if hop_efficiency > 1.0:
                    print(f"  ❌ 异常的跳数效率: {hop_efficiency}")
                if backhaul_capacity > 1000e6:
                    print(f"  ⚠️  异常高的回程容量: {backhaul_capacity/1e6:.2f} Mbps")
                
                # 有效回程容量
                effective_backhaul = backhaul_capacity * hop_efficiency
                print(f"有效回程容量: {effective_backhaul/1e6:.2f} Mbps")
                
                # 实际有效吞吐量 = min(前端总需求, 有效回程容量)
                uav_effective_throughput = min(uav_user_throughput, effective_backhaul)
                print(f"UAV有效吞吐量: {uav_effective_throughput/1e6:.2f} Mbps")
            else:
                print("无回程路径，吞吐量为0")
                uav_effective_throughput = 0
            
            # 累加到系统总吞吐量
            system_throughput += uav_effective_throughput
            
            uav_details.append({
                'uav_idx': i,
                'connected_users': len(connected_users),
                'frontend_demand': uav_user_throughput,
                'backhaul_capacity': backhaul_capacity if i in self.env.routing_paths else 0,
                'hop_count': len(self.env.routing_paths[i]) if i in self.env.routing_paths else 0,
                'effective_throughput': uav_effective_throughput
            })
        
        print(f"\n=== 系统总throughput: {system_throughput/1e6:.2f} Mbps ===")
        
        # 检查是否超过理论上限
        max_theoretical = 5 * 200e6  # 5个UAV * 200Mbps per UAV (粗略估计)
        if system_throughput > max_theoretical:
            print(f"⚠️  系统throughput超过粗略理论上限 ({max_theoretical/1e6:.0f} Mbps)")
            
        if system_throughput > 1100e6:
            print(f"🚨 发现异常高的系统throughput (>1100Mbps)!")
            
        return system_throughput, uav_details
        
    def test_reward_calculation(self):
        """测试完整的reward计算过程"""
        print("=== 测试Reward计算 ===")
        
        # 调用环境的reward计算
        reward = self.env._compute_reward()
        
        if hasattr(self.env, 'reward_info'):
            info = self.env.reward_info
            print(f"原始奖励: {info.get('raw_reward', 'N/A'):.4f}")
            print(f"归一化奖励: {info.get('normalized_reward', 'N/A'):.4f}")
            print(f"系统throughput: {info.get('system_throughput_mbps', 'N/A'):.2f} Mbps")
            print(f"理论最大throughput: {info.get('max_realistic_throughput_mbps', 'N/A'):.2f} Mbps")
            print(f"平均用户throughput: {info.get('avg_throughput_per_user_mbps', 'N/A'):.2f} Mbps")
            print(f"连接用户数: {info.get('connected_users', 'N/A')}")
            print(f"连通性比率: {info.get('connectivity_ratio', 'N/A'):.2%}")
            print(f"平均跳数: {info.get('avg_hops', 'N/A'):.2f}")
            
            # 检查异常值
            system_throughput_mbps = info.get('system_throughput_mbps', 0)
            if system_throughput_mbps > 1100:
                print(f"🚨 发现异常高的系统throughput: {system_throughput_mbps:.2f} Mbps!")
                return True  # 返回True表示发现异常
        else:
            print("reward_info不存在")
            
        print()
        return False
        
    def run_multiple_steps_test(self, n_steps=10):
        """运行多步测试，寻找异常情况"""
        print(f"=== 运行{n_steps}步测试 ===")
        
        anomaly_found = False
        anomaly_steps = []
        
        obs, info = self.env.reset()
        
        for step in range(n_steps):
            print(f"\n--- 步骤 {step+1} ---")
            
            # 执行随机动作
            actions = {}
            for agent in self.env.agents:
                actions[agent] = self.env.action_space(agent).sample()
            
            obs, rewards, terminations, truncations, infos = self.env.step(actions)
            
            # 检查是否有异常throughput
            if self.test_reward_calculation():
                anomaly_found = True
                anomaly_steps.append(step + 1)
                
                print("🔍 发现异常，进行详细分析...")
                self.debug_system_throughput_calculation()
                self.debug_routing_paths()
                
                # 如果发现异常，可以选择停止或继续
                break
        
        if anomaly_found:
            print(f"\n🚨 在步骤 {anomaly_steps} 发现throughput异常!")
        else:
            print(f"\n✅ {n_steps}步测试中未发现异常")
            
        return anomaly_found, anomaly_steps
        
    def run_comprehensive_test(self):
        """运行完整的测试套件"""
        print("🔬 开始Scenario2 Throughput调试测试")
        print("="*50)
        
        # 1. 创建环境
        self.create_env()
        
        # 2. 测试基础参数
        max_theoretical = self.test_basic_parameters()
        
        # 3. 重置环境并开始详细测试
        obs, info = self.env.reset()
        
        # 4. 测试单链路throughput
        self.test_single_link_throughput()
        
        # 5. 测试回程容量
        self.test_backhaul_capacity()
        
        # 6. 调试路由路径
        self.debug_routing_paths()
        
        # 7. 详细调试系统throughput计算
        system_throughput, uav_details = self.debug_system_throughput_calculation()
        
        # 8. 测试reward计算
        anomaly_in_reward = self.test_reward_calculation()
        
        # 9. 运行多步测试
        anomaly_found, anomaly_steps = self.run_multiple_steps_test(5)
        
        # 10. 总结
        print("\n" + "="*50)
        print("🎯 测试总结")
        print("="*50)
        
        if anomaly_found or anomaly_in_reward:
            print("🚨 发现异常情况:")
            if system_throughput > 1100e6:
                print(f"  - 系统throughput过高: {system_throughput/1e6:.2f} Mbps")
            print("  - 建议检查以下方面:")
            print("    1. 回程容量计算中的inf值处理")
            print("    2. 跳数效率计算的边界条件")
            print("    3. 路径计算的正确性")
            print("    4. 系统throughput累加逻辑")
        else:
            print("✅ 未发现明显异常，系统计算逻辑基本正确")
            
        return {
            'anomaly_found': anomaly_found,
            'system_throughput_mbps': system_throughput / 1e6,
            'max_theoretical_mbps': max_theoretical / 1e6,
            'uav_details': uav_details
        }

def main():
    """主函数"""
    # 创建调试器并运行测试
    debugger = ThroughputDebugger()
    
    # 运行完整测试
    results = debugger.run_comprehensive_test()
    
    # 可以尝试不同的配置
    print("\n" + "="*50)
    print("🔄 测试不同配置")
    print("="*50)
    
    # 测试更多UAV的情况
    config_more_uavs = {'n_uavs': 8, 'n_users': 80}
    debugger2 = ThroughputDebugger(config_more_uavs)
    results2 = debugger2.run_comprehensive_test()
    
    return results, results2

if __name__ == "__main__":
    results = main()
