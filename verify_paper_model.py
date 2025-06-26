#!/usr/bin/env python3
"""
验证论文中的通信模型实现
"""

import numpy as np
from envs.pettingzoo.uav_env import MultiUAVEnv
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.scenario3 import UAVMultiHopEnv

def verify_probabilistic_channel_model():
    """验证概率信道模型的具体实现"""
    
    print("=== 验证概率信道模型实现 ===\n")
    
    # 创建测试环境
    env = MultiUAVEnv(
        n_uavs=2,
        n_users=5,
        area_size=1000,
        channel_model="probabilistic",
        paper_reward=True,
        max_steps=10
    )
    
    obs, info = env.reset()
    
    # 验证概率信道模型参数
    print("1. 概率信道模型参数:")
    print(f"   - 环境常数 a: {env.prob_channel_a}")
    print(f"   - 环境常数 b: {env.prob_channel_b}")
    print(f"   - LoS额外损耗: {env.eta_los} dB")
    print(f"   - NLoS额外损耗: {env.eta_nlos} dB")
    print(f"   - 载波频率: {env.carrier_frequency/1e9:.1f} GHz")
    
    # 验证信号与性能模型参数
    print("\n2. 信号与性能模型参数:")
    print(f"   - 子信道带宽: {env.bandwidth/1e3:.0f} KHz")
    print(f"   - 发射功率: {env.tx_power} dBm")
    print(f"   - 噪声功率: {env.noise_power} dBm")
    print(f"   - SINR阈值: {env.sinr_threshold_db} dB")
    print(f"   - 功率成本权重: {env.power_cost_weight}")
    
    # 测试路径损耗计算
    print("\n3. 测试路径损耗计算:")
    uav_pos = np.array([500, 500, 100])  # 无人机位置
    user_pos = np.array([600, 600])      # 用户位置
    
    path_loss = env._compute_path_loss(uav_pos, user_pos)
    print(f"   - UAV位置: {uav_pos}")
    print(f"   - 用户位置: {user_pos}")
    print(f"   - 计算的路径损耗: {path_loss:.2f} dB")
    
    # 测试SINR计算
    print("\n4. 测试SINR计算:")
    sinr = env._compute_sinr(0, 0)  # 第一个UAV到第一个用户
    print(f"   - UAV 0 到用户 0 的SINR: {sinr:.2f} dB")
    
    # 测试论文奖励函数
    print("\n5. 测试论文奖励函数:")
    reward = env._compute_reward()
    print(f"   - 当前奖励: {reward:.6f}")
    
    env.close()
    print("\n✓ 概率信道模型验证完成")

def verify_all_environments():
    """验证所有环境都支持论文模型"""
    
    print("\n=== 验证所有环境支持论文模型 ===\n")
    
    environments = [
        ("基础环境", MultiUAVEnv),
        ("协作网络环境", UAVCooperativeNetworkEnv),
        ("多跳环境", UAVMultiHopEnv)
    ]
    
    for env_name, env_class in environments:
        print(f"测试 {env_name}:")
        try:
            # 创建环境
            env = env_class(
                n_uavs=3,
                n_users=10,
                channel_model="probabilistic",
                paper_reward=True,
                max_steps=10
            )
            
            # 重置环境
            obs, info = env.reset()
            
            # 执行一步
            actions = {}
            for agent in env.agents:
                actions[agent] = np.random.uniform(-1, 1, 3)
            
            obs, rewards, terms, truncs, infos = env.step(actions)
            
            # 检查奖励是否为数值
            total_reward = sum(rewards.values())
            print(f"   ✓ 成功运行，总奖励: {total_reward:.6f}")
            
            env.close()
            
        except Exception as e:
            print(f"   ✗ 错误: {e}")

def main():
    """主函数"""
    verify_probabilistic_channel_model()
    verify_all_environments()
    print("\n=== 验证完成 ===")

if __name__ == "__main__":
    main()
