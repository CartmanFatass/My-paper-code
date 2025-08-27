#!/usr/bin/env python3
"""
快速测试当前移动性模型效果
"""

import numpy as np
from envs.pettingzoo.scenario5 import UAVBeliefMapEnv

def quick_mobility_test():
    """快速测试移动性效果"""
    print("=== 快速移动性测试 ===")
    
    # 创建环境
    env = UAVBeliefMapEnv(
        n_uavs=12,
        n_users=80,
        area_size=8000,  # 大型场景
        max_steps=300,   # 短时间测试
        n_clusters=4,
        cluster_std=80,
        users_dynamic=True,
        user_max_speed=12,  # 当前增强速度
        user_movement_model="random_waypoint",  # 当前模型
        observation_radius=600,
        seed=42
    )
    
    obs, info = env.reset()
    initial_positions = env.user_positions.copy()
    
    print(f"环境设置: {env.area_size}x{env.area_size}m, {env.n_users}用户, {env.user_max_speed}m/s速度")
    print(f"UAV覆盖半径: {env.observation_radius}m")
    
    # 运行300步
    for step in range(300):
        actions = {}
        for agent in env.agents:
            actions[agent] = env.action_space(agent).sample()
        obs, rewards, terminations, truncations, infos = env.step(actions)
        if any(terminations.values()) or any(truncations.values()):
            break
    
    final_positions = env.user_positions.copy()
    
    # 计算位移
    displacements = []
    for i in range(env.n_users):
        displacement = np.linalg.norm(final_positions[i, :2] - initial_positions[i, :2])
        displacements.append(displacement)
    
    displacements = np.array(displacements)
    
    print(f"\n300步后的移动性分析:")
    print(f"  - 平均位移: {np.mean(displacements):.1f}m")
    print(f"  - 最大位移: {np.max(displacements):.1f}m")
    print(f"  - 位移 > 300m的用户: {np.sum(displacements > 300)}/{env.n_users} ({np.sum(displacements > 300)/env.n_users:.1%})")
    print(f"  - 位移 > 600m的用户: {np.sum(displacements > 600)}/{env.n_users} ({np.sum(displacements > 600)/env.n_users:.1%})")
    
    # 理论最大移动距离
    max_theoretical = env.user_max_speed * 300
    print(f"  - 理论最大移动距离: {max_theoretical:.0f}m")
    print(f"  - 实际vs理论比例: {np.mean(displacements)/max_theoretical:.1%}")
    
    env.close()
    return np.mean(displacements)

if __name__ == "__main__":
    avg_displacement = quick_mobility_test()
