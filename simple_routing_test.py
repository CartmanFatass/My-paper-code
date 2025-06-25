#!/usr/bin/env python3
"""
简单的路由测试脚本
"""

import sys
import os
sys.path.append(os.getcwd())

try:
    import numpy as np
    from envs.pettingzoo.scenario3 import UAVMultiHopEnv
    
    print("=== 开始路由修复测试 ===")
    
    # 创建环境
    env = UAVMultiHopEnv(
        n_uavs=3,
        n_users=10,
        area_size=1000,
        n_ground_bs=4,
        max_steps=10,
        render_mode=None,
        seed=42
    )
    
    print("环境创建成功")
    
    # 重置环境
    observations, infos = env.reset()
    print("环境重置成功")
    
    # 打印基站位置
    print("\n地面基站位置:")
    for i, pos in enumerate(env.ground_bs_positions):
        print(f"  基站 {i}: ({pos[0]:.1f}, {pos[1]:.1f})")
    
    # 打印无人机位置
    print("\n无人机位置:")
    for i, pos in enumerate(env.uav_positions):
        print(f"  无人机 {i}: ({pos[0]:.1f}, {pos[1]:.1f})")
    
    # 执行一步
    actions = {agent: 4 for agent in env.agents}  # 保持位置
    observations, rewards, terminations, truncations, infos = env.step(actions)
    
    print("\n执行一步后的路由信息:")
    if hasattr(env, 'routing_paths') and env.routing_paths:
        bs_usage = {}
        for uav_idx, path in env.routing_paths.items():
            for node_type, node_idx in path:
                if node_type == "ground_bs":
                    bs_usage[node_idx] = bs_usage.get(node_idx, 0) + 1
                    print(f"  无人机 {uav_idx} -> 基站 {node_idx}")
                    break
        
        print(f"\n基站使用统计:")
        for bs_idx in range(env.n_ground_bs):
            count = bs_usage.get(bs_idx, 0)
            print(f"  基站 {bs_idx}: {count} 个连接")
        
        if len(bs_usage) > 1:
            print("✓ 修复成功: 无人机连接到了不同的基站!")
        else:
            print("⚠️ 仍有问题: 所有无人机连接到同一个基站")
    else:
        print("  暂无路由建立")
    
    print("\n=== 测试完成 ===")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
