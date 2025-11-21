#!/usr/bin/env python3
"""
负载均衡与覆盖率结合奖励函数的训练示例

这个脚本展示了如何使用新实施的负载均衡奖励函数进行实际的多智能体强化学习训练。
"""

import os
import sys
import time
import numpy as np
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_load_balance_example import get_config_by_training_stage
from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv


def test_load_balance_environment():
    """测试负载均衡环境的基本功能"""
    print("="*60)
    print("测试负载均衡环境")
    print("="*60)
    
    # 使用平衡配置进行测试
    config = get_config_by_training_stage('balanced')
    env = UAVForcedRelayEnv(config=config, seed=42)
    
    print(f"环境配置:")
    print(f"  奖励类型: {env.reward_type}")
    print(f"  覆盖率权重: {env.w_coverage}")
    print(f"  负载均衡权重: {env.w_load_balance}")
    print(f"  无人机数量: {env.n_uavs}")
    print(f"  用户数量: {env.n_users}")
    
    # 重置环境
    observations, infos = env.reset()
    print(f"\n环境重置成功，智能体数量: {len(env.agents)}")
    
    # 运行几步来测试奖励计算
    total_reward = 0
    episode_rewards = []
    
    print(f"\n开始测试运行...")
    for step in range(10):
        # 随机动作
        actions = {agent: env.np_random.choice(env.n_discrete_actions) for agent in env.agents}
        
        # 执行动作
        observations, rewards, terminations, truncations, infos = env.step(actions)
        
        # 记录奖励
        step_reward = list(rewards.values())[0]  # 所有智能体共享相同奖励
        total_reward += step_reward
        episode_rewards.append(step_reward)
        
        # 显示详细信息
        if step % 5 == 0:
            agent_info = infos[env.agents[0]]
            reward_info = agent_info.get('reward_info', {})
            
            print(f"\n步骤 {step}:")
            print(f"  奖励: {step_reward:.4f}")
            
            if 'load_balance_coverage_reward' in reward_info:
                print(f"  负载均衡覆盖率奖励: {reward_info['load_balance_coverage_reward']:.4f}")
                print(f"  覆盖率奖励: {reward_info.get('coverage_reward', 0):.4f}")
                print(f"  负载均衡惩罚: {reward_info.get('load_balance_penalty', 0):.4f}")
                print(f"  服务UAV数量: {reward_info.get('serving_uavs_count', 0)}")
                
                if 'serving_uav_loads' in reward_info and reward_info['serving_uav_loads']:
                    loads = reward_info['serving_uav_loads']
                    print(f"  负载分布: {loads}")
                    if len(loads) > 1:
                        load_variance = np.var(loads)
                        print(f"  负载方差: {load_variance:.4f}")
        
        if any(terminations.values()) or any(truncations.values()):
            print(f"\n环境在步骤 {step} 终止")
            break
    
    print(f"\n测试运行完成:")
    print(f"  总奖励: {total_reward:.4f}")
    print(f"  平均奖励: {np.mean(episode_rewards):.4f}")
    print(f"  奖励标准差: {np.std(episode_rewards):.4f}")
    
    env.close()
    return True


def demonstrate_different_configurations():
    """演示不同配置下的奖励行为差异"""
    print("\n" + "="*60)
    print("演示不同配置的奖励行为")
    print("="*60)
    
    configurations = [
        ('conservative', '保守配置'),
        ('balanced', '平衡配置'), 
        ('aggressive', '激进配置')
    ]
    
    results = {}
    
    for config_type, config_name in configurations:
        print(f"\n测试 {config_name} ({config_type}):")
        
        # 创建环境
        config = get_config_by_training_stage(config_type)
        env = UAVForcedRelayEnv(config=config, seed=42)
        
        print(f"  覆盖率权重: {env.w_coverage}")
        print(f"  负载均衡权重: {env.w_load_balance}")
        
        # 重置并运行
        observations, infos = env.reset()
        total_reward = 0
        
        for step in range(5):
            actions = {agent: env.np_random.choice(env.n_discrete_actions) for agent in env.agents}
            observations, rewards, terminations, truncations, infos = env.step(actions)
            total_reward += list(rewards.values())[0]
        
        # 获取最终状态信息
        agent_info = infos[env.agents[0]]
        reward_info = agent_info.get('reward_info', {})
        
        results[config_type] = {
            'total_reward': total_reward,
            'coverage_reward': reward_info.get('coverage_reward', 0),
            'load_balance_penalty': reward_info.get('load_balance_penalty', 0),
            'serving_uavs': reward_info.get('serving_uavs_count', 0)
        }
        
        print(f"  5步总奖励: {total_reward:.4f}")
        print(f"  覆盖率奖励: {results[config_type]['coverage_reward']:.4f}")
        print(f"  负载均衡惩罚: {results[config_type]['load_balance_penalty']:.4f}")
        
        env.close()
    
    print(f"\n配置比较汇总:")
    for config_type, config_name in configurations:
        result = results[config_type]
        print(f"  {config_name}: 奖励={result['total_reward']:.4f}, " +
              f"覆盖率={result['coverage_reward']:.4f}, " +
              f"惩罚={result['load_balance_penalty']:.4f}")
    
    return results


def simulate_training_progression():
    """模拟训练过程中的配置切换"""
    print("\n" + "="*60)
    print("模拟训练过程中的配置切换")
    print("="*60)
    
    # 模拟的训练阶段
    stages = [
        (0, 30, 'conservative'),   # 前30%使用保守配置
        (30, 70, 'balanced'),      # 中间40%使用平衡配置
        (70, 100, 'aggressive')    # 后30%使用激进配置
    ]
    
    print("模拟的训练进度和配置切换:")
    
    for start, end, stage in stages:
        config = get_config_by_training_stage(stage)
        
        print(f"\n训练进度 {start}%-{end}%: 使用{stage}配置")
        print(f"  奖励类型: {config.reward_type}")
        print(f"  覆盖率权重: {config.w_coverage}")
        print(f"  负载均衡权重: {config.w_load_balance}")
        
        # 简单的奖励计算示例
        coverage_reward = 0.8  # 模拟80%覆盖率
        load_balance_penalty = 0.3  # 模拟中等负载不均衡
        
        final_reward = config.w_coverage * coverage_reward - config.w_load_balance * load_balance_penalty
        
        print(f"  示例计算: {config.w_coverage}×{coverage_reward} - {config.w_load_balance}×{load_balance_penalty} = {final_reward:.4f}")
    
    print(f"\n训练建议:")
    print(f"1. 初期阶段: 专注建立基础覆盖率，负载均衡要求较低")
    print(f"2. 中期阶段: 在保持覆盖率的同时，逐步改善负载分布")
    print(f"3. 后期阶段: 精细调优负载均衡，实现更稳定的网络性能")


def create_training_script_example():
    """创建实际训练脚本的示例代码"""
    print("\n" + "="*60)
    print("实际训练脚本示例代码")
    print("="*60)
    
    example_code = '''
# 实际训练脚本示例 (使用你选择的RL库)

import torch
from config_load_balance_example import get_config_by_training_stage
from envs.pettingzoo.scenario4_discrete import UAVForcedRelayEnv

def train_with_load_balance():
    """使用负载均衡奖励函数进行训练"""
    
    # 第一阶段: 保守配置 (建立基础覆盖率)
    print("阶段1: 保守配置训练")
    config = get_config_by_training_stage('conservative')
    env = UAVForcedRelayEnv(config=config)
    
    # 在这里添加你的RL训练代码
    # 例如: PPO, MAPPO, SAC等
    # train_agent(env, episodes=1000)
    
    # 第二阶段: 平衡配置 (兼顾覆盖率和均衡)
    print("阶段2: 平衡配置训练")
    config = get_config_by_training_stage('balanced')
    env.close()
    env = UAVForcedRelayEnv(config=config)
    
    # 继续训练或微调
    # finetune_agent(env, episodes=1000)
    
    # 第三阶段: 激进配置 (精细调优负载均衡)
    print("阶段3: 激进配置训练")
    config = get_config_by_training_stage('aggressive')
    env.close()
    env = UAVForcedRelayEnv(config=config)
    
    # 最终优化
    # optimize_agent(env, episodes=500)
    
    env.close()

if __name__ == "__main__":
    train_with_load_balance()
    '''
    
    print("示例训练代码:")
    print(example_code)
    
    print("关键要点:")
    print("1. 使用 get_config_by_training_stage() 获取不同阶段的配置")
    print("2. 在训练过程中切换配置以实现渐进式优化")  
    print("3. 监控 load_balance_coverage_reward 和相关指标")
    print("4. 根据训练效果调整 w_load_balance 权重")


def main():
    """主函数"""
    print("负载均衡与覆盖率结合奖励函数 - 训练示例")
    print("="*80)
    
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 基本环境测试
        print("\n[1/4] 基本环境测试...")
        test_load_balance_environment()
        
        # 2. 不同配置演示
        print("\n[2/4] 不同配置演示...")
        demonstrate_different_configurations()
        
        # 3. 训练进程模拟
        print("\n[3/4] 训练进程模拟...")
        simulate_training_progression()
        
        # 4. 训练脚本示例
        print("\n[4/4] 训练脚本示例...")
        create_training_script_example()
        
        print("\n" + "="*80)
        print("✅ 所有示例运行成功!")
        print("\n🚀 现在你可以开始使用负载均衡奖励函数进行训练:")
        
        print("\n推荐的使用步骤:")
        print("1. 从保守配置开始，建立基础的覆盖能力")
        print("2. 切换到平衡配置，优化网络结构") 
        print("3. 使用激进配置进行最终调优")
        print("4. 根据实际训练效果调整权重参数")
        
        print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 训练示例展示完成!")
        print("\n📚 相关文件:")
        print("- envs/pettingzoo/scenario4_discrete.py  (奖励函数实现)")
        print("- config_load_balance_example.py         (配置示例)")
        print("- test_load_balance_coverage_reward.py   (测试脚本)")
        print("- train_load_balance_example.py          (训练示例)")
    else:
        print("\n❌ 运行失败，请检查错误信息")
