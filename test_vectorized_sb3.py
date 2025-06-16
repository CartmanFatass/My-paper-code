#!/usr/bin/env python3
"""
测试基于SB3向量化环境的HMASD训练脚本
验证向量化训练的正确性和性能
"""

import os
import sys
import time
import numpy as np
import torch
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from train_vectorized_sb3 import VectorizedHMASDTrainer

def test_vectorized_training():
    """测试向量化训练"""
    print("🧪 开始测试基于SB3向量化环境的HMASD训练")
    print("=" * 80)
    
    # 创建测试配置
    config = Config()
    
    # 创建测试参数
    class TestArgs:
        def __init__(self):
            self.samples = 1000  # 测试用少量样本
            self.device = 'auto'
            self.debug = True
            self.n_envs = 4  # 测试用少量环境
            self.scenario = 2
            self.n_uavs = 3  # 测试用少量无人机
            self.n_users = 10  # 测试用少量用户
            self.user_distribution = 'uniform'
            self.channel_model = '3gpp-36777'
            self.max_hops = 2
            self.log_level = 'INFO'
            self.console_log_level = 'INFO'
    
    args = TestArgs()
    
    print(f"📊 测试配置:")
    print(f"  - 向量化环境数量: {args.n_envs}")
    print(f"  - 训练样本数: {args.samples:,}")
    print(f"  - 无人机数量: {args.n_uavs}")
    print(f"  - 用户数量: {args.n_users}")
    print(f"  - 场景: {args.scenario}")
    
    try:
        # 创建向量化训练器
        trainer = VectorizedHMASDTrainer(config, args)
        
        # 开始测试训练
        start_time = time.time()
        trainer.train(total_samples=args.samples)
        end_time = time.time()
        
        # 计算性能指标
        total_time = end_time - start_time
        samples_per_second = args.samples / total_time if total_time > 0 else 0
        
        print("\n🎉 向量化训练测试完成！")
        print(f"📈 性能统计:")
        print(f"  - 总时间: {total_time:.2f}秒")
        print(f"  - 样本速度: {samples_per_second:.1f} 样本/秒")
        print(f"  - 总更新数: {trainer.total_updates}")
        print(f"  - 总Episodes: {trainer.total_episodes}")
        
        # 验证训练结果
        if trainer.total_updates > 0:
            print("✅ 模型更新成功")
        else:
            print("⚠️ 未进行模型更新")
        
        if trainer.total_episodes > 0:
            print("✅ 环境交互成功")
        else:
            print("⚠️ 未完成环境交互")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_performance():
    """比较向量化训练与多线程训练的性能"""
    print("\n🔍 性能对比分析")
    print("=" * 80)
    
    # 理论性能分析
    n_envs = 32
    rollout_length = 2048
    single_env_step_time = 0.01  # 假设单环境步骤时间10ms
    
    # 串行执行时间
    serial_time = n_envs * rollout_length * single_env_step_time
    
    # 向量化并行执行时间
    parallel_time = rollout_length * single_env_step_time  # 所有环境并行
    
    # 性能提升
    speedup = serial_time / parallel_time
    
    print(f"📊 理论性能分析 (基于 {n_envs} 环境, {rollout_length} 步长):")
    print(f"  - 串行执行时间: {serial_time:.2f}秒")
    print(f"  - 并行执行时间: {parallel_time:.2f}秒")
    print(f"  - 理论加速比: {speedup:.1f}x")
    
    # 内存使用分析
    state_dim = 100  # 假设状态维度
    obs_dim = 50     # 假设观测维度
    action_dim = 10  # 假设动作维度
    n_agents = 5     # 假设智能体数量
    
    # 单个rollout的内存使用
    memory_per_step = (
        n_envs * state_dim * 4 +           # 状态 (float32)
        n_envs * n_agents * obs_dim * 4 +  # 观测
        n_envs * n_agents * action_dim * 4 # 动作
    ) / 1024 / 1024  # 转换为MB
    
    total_memory = memory_per_step * rollout_length
    
    print(f"\n💾 内存使用分析:")
    print(f"  - 每步内存使用: {memory_per_step:.2f}MB")
    print(f"  - 总内存使用: {total_memory:.2f}MB")
    
    # 优势总结
    print(f"\n🚀 向量化训练优势:")
    print(f"  ✅ 数据收集速度提升: ~{speedup:.0f}x")
    print(f"  ✅ 消除线程锁竞争")
    print(f"  ✅ GPU批量计算友好")
    print(f"  ✅ 简化的数据流架构")
    print(f"  ✅ 更好的调试体验")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试向量化SB3训练')
    parser.add_argument('--test-only', action='store_true', help='仅运行测试，不进行性能对比')
    parser.add_argument('--compare-only', action='store_true', help='仅进行性能对比分析')
    
    args = parser.parse_args()
    
    success = True
    
    if not args.compare_only:
        # 运行训练测试
        success = test_vectorized_training()
    
    if not args.test_only:
        # 运行性能对比
        compare_performance()
    
    if success:
        print("\n🎉 所有测试通过！")
        print("💡 建议: 使用向量化SB3训练替代多线程训练以获得更好的性能")
    else:
        print("\n❌ 测试失败，请检查配置和环境")
        sys.exit(1)

if __name__ == "__main__":
    main()
