#!/usr/bin/env python3
"""
详细调试数据流，追踪随机策略为什么会变成直线运动
"""

import numpy as np
import torch
import matplotlib.pyplot as plt
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from logger import main_logger
import json

def debug_data_flow():
    """详细调试整个数据流程"""
    
    # 初始化配置
    config = Config()
    
    # 创建环境
    env = UAVForcedRelayEnv()
    
    # 获取环境信息并更新配置
    observations, infos = env.reset()
    
    # 从环境获取状态
    state = infos[list(infos.keys())[0]]['state']
    
    # 获取观测维度
    first_agent = list(observations.keys())[0]
    obs_dim = len(observations[first_agent]['obs'])
    
    config.update_env_dims(
        state_dim=len(state),
        obs_dim=obs_dim,
        n_agents=len(observations)
    )
    
    print(f"=== 环境初始化信息 ===")
    print(f"状态维度: {config.state_dim}")
    print(f"观测维度: {config.obs_dim}")
    print(f"智能体数量: {config.n_agents}")
    print(f"动作维度: {config.action_dim}")
    
    # 创建HMASD智能体（未训练）
    agent = HMASDAgent(config, device=torch.device('cpu'))
    
    # 记录详细数据
    debug_data = {
        'positions': [],
        'actions': [],
        'observations': [],
        'team_skills': [],
        'agent_skills': [],
        'action_logprobs': [],
        'values': [],
        'step_info': []
    }
    
    # 运行episode并详细记录
    episode_length = 50  # 减少步数以便详细分析
    
    print(f"\n=== 开始详细调试 ===")
    
    for step in range(episode_length):
        print(f"\n--- 步骤 {step} ---")
        
        # 记录当前位置
        current_positions = []
        for i in range(config.n_agents):
            pos = [env.uav_positions[i][0], env.uav_positions[i][1]]
            current_positions.append(pos)
        debug_data['positions'].append(current_positions)
        
        print(f"当前位置范围: X[{min(p[0] for p in current_positions):.1f}, {max(p[0] for p in current_positions):.1f}], "
              f"Y[{min(p[1] for p in current_positions):.1f}, {max(p[1] for p in current_positions):.1f}]")
        
        # 准备观测数据
        obs_array = []
        for agent_id in sorted(observations.keys()):
            obs_array.append(observations[agent_id]['obs'])
        obs_array = np.array(obs_array)
        
        print(f"观测统计: 均值={np.mean(obs_array):.4f}, 标准差={np.std(obs_array):.4f}, "
              f"范围[{np.min(obs_array):.4f}, {np.max(obs_array):.4f}]")
        
        # 记录观测
        debug_data['observations'].append(obs_array.tolist())
        
        # 使用HMASD智能体选择动作
        actions, infos_list = agent.step(
            states_batch=np.array([state]),
            observations_batch=np.array([obs_array]),
            env_steps_batch=np.array([step]),
            dones_batch=np.array([False]),
            deterministic=False
        )
        
        # 提取详细信息
        step_info = infos_list[0]  # 第一个环境的信息
        team_skill = step_info['team_skill']
        agent_skills = step_info['agent_skills']
        action_logprobs = step_info['action_logprobs']
        values = step_info['values']
        skill_changed = step_info['skill_changed']
        
        print(f"技能分配: 团队技能={team_skill}, 个体技能={agent_skills}")
        print(f"技能是否改变: {skill_changed}")
        print(f"动作统计: 均值={np.mean(actions):.4f}, 标准差={np.std(actions):.4f}, "
              f"范围[{np.min(actions):.4f}, {np.max(actions):.4f}]")
        print(f"动作对数概率: 均值={np.mean(action_logprobs):.4f}, 范围[{np.min(action_logprobs):.4f}, {np.max(action_logprobs):.4f}]")
        print(f"价值估计: 均值={np.mean(values):.4f}, 范围[{np.min(values):.4f}, {np.max(values):.4f}]")
        
        # 记录详细数据
        debug_data['actions'].append(actions[0].tolist())
        debug_data['team_skills'].append(int(team_skill))
        debug_data['agent_skills'].append(agent_skills.tolist())
        debug_data['action_logprobs'].append(action_logprobs.tolist())
        debug_data['values'].append(values.tolist())
        debug_data['step_info'].append({
            'skill_changed': bool(skill_changed),
            'skill_timer': int(step_info['skill_timer']),
            'env_id': int(step_info['env_id'])
        })
        
        # 检查是否有异常的动作模式
        action_magnitudes = np.linalg.norm(actions[0], axis=1)
        print(f"动作幅度: 均值={np.mean(action_magnitudes):.4f}, 最大={np.max(action_magnitudes):.4f}")
        
        # 检查动作方向的一致性
        if len(actions[0]) > 1:
            action_directions = actions[0] / (np.linalg.norm(actions[0], axis=1, keepdims=True) + 1e-8)
            direction_similarity = np.mean(np.dot(action_directions, action_directions.T))
            print(f"动作方向相似度: {direction_similarity:.4f} (1.0表示完全一致)")
        
        # 准备环境动作字典
        env_actions = {}
        for i, agent_id in enumerate(sorted(observations.keys())):
            env_actions[agent_id] = actions[0][i]
        
        # 执行动作
        next_observations, rewards, terminations, truncations, env_infos = env.step(env_actions)
        
        # 计算位置变化
        new_positions = []
        for i in range(config.n_agents):
            pos = [env.uav_positions[i][0], env.uav_positions[i][1]]
            new_positions.append(pos)
        
        position_changes = []
        for i in range(config.n_agents):
            change = np.linalg.norm(np.array(new_positions[i]) - np.array(current_positions[i]))
            position_changes.append(change)
        
        print(f"位置变化: 均值={np.mean(position_changes):.2f}m, 最大={np.max(position_changes):.2f}m")
        
        # 检查是否所有智能体都在朝同一方向移动
        if step > 0:
            movement_vectors = []
            for i in range(config.n_agents):
                movement = np.array(new_positions[i]) - np.array(current_positions[i])
                if np.linalg.norm(movement) > 1e-6:  # 避免零向量
                    movement_vectors.append(movement / np.linalg.norm(movement))
            
            if len(movement_vectors) > 1:
                movement_vectors = np.array(movement_vectors)
                movement_similarity = np.mean(np.dot(movement_vectors, movement_vectors.T))
                print(f"移动方向相似度: {movement_similarity:.4f} (1.0表示完全一致)")
                
                if movement_similarity > 0.8:
                    print("⚠️  警告: 检测到高度一致的移动方向!")
        
        # 更新状态
        next_state = env_infos[list(env_infos.keys())[0]]['next_state']
        state = next_state
        observations = next_observations
        
        # 检查终止条件
        dones = list(terminations.values())
        if np.any(dones):
            print(f"Episode在第{step}步结束")
            break
        
        # 每10步输出一次总结
        if step > 0 and step % 10 == 0:
            print(f"\n=== 步骤 {step} 总结 ===")
            recent_actions = debug_data['actions'][-10:]
            recent_skills = debug_data['team_skills'][-10:]
            
            action_variance = np.var([np.var(a) for a in recent_actions])
            skill_changes = sum(1 for i in range(1, len(recent_skills)) if recent_skills[i] != recent_skills[i-1])
            
            print(f"最近10步动作方差的方差: {action_variance:.6f}")
            print(f"最近10步技能变化次数: {skill_changes}")
            
            if action_variance < 0.001:
                print("⚠️  警告: 动作方差过低，可能存在策略退化!")
            
            if skill_changes == 0:
                print("⚠️  警告: 技能长时间未变化!")
    
    # 保存调试数据
    with open('debug_data_flow.json', 'w') as f:
        json.dump(debug_data, f, indent=2)
    
    print(f"\n=== 调试数据已保存到 debug_data_flow.json ===")
    
    # 分析数据趋势
    print(f"\n=== 数据趋势分析 ===")
    
    # 分析动作方差随时间的变化
    action_variances = []
    for actions_step in debug_data['actions']:
        action_variances.append(np.var(actions_step))
    
    print(f"动作方差趋势:")
    print(f"  前10步平均: {np.mean(action_variances[:10]):.6f}")
    if len(action_variances) > 20:
        print(f"  中10步平均: {np.mean(action_variances[10:20]):.6f}")
    if len(action_variances) > 30:
        print(f"  后10步平均: {np.mean(action_variances[-10:]):.6f}")
    
    # 分析技能变化频率
    team_skills = debug_data['team_skills']
    skill_changes = [i for i in range(1, len(team_skills)) if team_skills[i] != team_skills[i-1]]
    print(f"技能变化发生在步骤: {skill_changes}")
    
    # 绘制关键指标
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # 动作方差
    axes[0, 0].plot(action_variances)
    axes[0, 0].set_title('动作方差随时间变化')
    axes[0, 0].set_xlabel('步骤')
    axes[0, 0].set_ylabel('方差')
    
    # 团队技能
    axes[0, 1].plot(debug_data['team_skills'])
    axes[0, 1].set_title('团队技能随时间变化')
    axes[0, 1].set_xlabel('步骤')
    axes[0, 1].set_ylabel('技能ID')
    
    # 动作幅度
    action_magnitudes = []
    for actions_step in debug_data['actions']:
        magnitudes = [np.linalg.norm(action) for action in actions_step]
        action_magnitudes.append(np.mean(magnitudes))
    
    axes[1, 0].plot(action_magnitudes)
    axes[1, 0].set_title('平均动作幅度随时间变化')
    axes[1, 0].set_xlabel('步骤')
    axes[1, 0].set_ylabel('幅度')
    
    # 价值估计
    value_means = []
    for values_step in debug_data['values']:
        value_means.append(np.mean(values_step))
    
    axes[1, 1].plot(value_means)
    axes[1, 1].set_title('平均价值估计随时间变化')
    axes[1, 1].set_xlabel('步骤')
    axes[1, 1].set_ylabel('价值')
    
    plt.tight_layout()
    plt.savefig('debug_data_flow_analysis.png', dpi=150, bbox_inches='tight')
    print(f"分析图表已保存为 debug_data_flow_analysis.png")
    
    return debug_data

if __name__ == "__main__":
    debug_data = debug_data_flow()
