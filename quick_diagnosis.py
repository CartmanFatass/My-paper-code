#!/usr/bin/env python3
"""
HMASD 策略坍塌快速诊断脚本
检查网络输出、数值稳定性和关键指标
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
import os
import time

def create_test_environment():
    """创建测试环境"""
    print("=" * 60)
    print("创建测试环境...")
    
    config = Config()
    
    # 创建原始环境
    raw_env = UAVForcedRelayEnv(
        n_uavs=config.n_agents,
        n_users=config.n_users,
        area_size=config.area_size,
        max_hops=config.max_hops,
        user_distribution=config.user_distribution,
        use_fdma=config.use_fdma,
        bandwidth=config.bandwidth,
        n_clusters=config.n_clusters,
        cluster_std=config.cluster_std,
        central_area_ratio=config.central_area_ratio,
        observation_radius=config.observation_radius,
        max_observed_uavs=config.max_observed_uavs,
        max_observed_users=config.max_observed_users,
        max_observed_bs=config.max_observed_bs,
        min_sinr=config.min_sinr,
        max_connections=config.max_connections,
        uav_init_mode=config.uav_init_mode,
        uav_start_area_size=config.uav_start_area_size
    )
    
    # 使用适配器包装环境
    env = ParallelToArrayAdapter(raw_env)
    
    # 重置环境获取维度信息
    observations, info = env.reset()
    state = info['state']  # 从info中获取state
    
    # 更新配置
    config.update_env_dims(
        state_dim=len(state),
        obs_dim=observations.shape[1],  # observations是numpy数组
        n_agents=observations.shape[0]
    )
    
    print(f"环境维度: state_dim={config.state_dim}, obs_dim={config.obs_dim}, n_agents={config.n_agents}")
    print("环境创建完成 ✓")
    
    return env, config

def test_network_initialization(config):
    """测试网络初始化"""
    print("\n" + "=" * 60)
    print("测试网络初始化...")
    
    try:
        agent = HMASDAgent(config, debug=True)
        print("网络初始化成功 ✓")
        
        # 检查网络参数
        coord_params = sum(p.numel() for p in agent.skill_coordinator.parameters())
        disc_params = sum(p.numel() for p in agent.skill_discoverer.parameters())
        team_disc_params = sum(p.numel() for p in agent.team_discriminator.parameters())
        ind_disc_params = sum(p.numel() for p in agent.individual_discriminator.parameters())
        
        print(f"网络参数统计:")
        print(f"  SkillCoordinator: {coord_params:,} 参数")
        print(f"  SkillDiscoverer: {disc_params:,} 参数")
        print(f"  TeamDiscriminator: {team_disc_params:,} 参数")
        print(f"  IndividualDiscriminator: {ind_disc_params:,} 参数")
        print(f"  总计: {coord_params + disc_params + team_disc_params + ind_disc_params:,} 参数")
        
        return agent
        
    except Exception as e:
        print(f"网络初始化失败 ✗: {e}")
        return None

def test_skill_assignment(agent, env, config, num_tests=10):
    """测试技能分配"""
    print("\n" + "=" * 60)
    print("测试技能分配...")
    
    results = {
        'team_skills': [],
        'agent_skills': [],
        'logits_ranges': [],
        'nan_inf_count': 0,
        'identical_outputs': 0
    }
    
    for i in range(num_tests):
        try:
            # 重置环境
            observations, info = env.reset()
            state = info['state']
            
            # 分配技能
            team_skill, agent_skills, log_probs = agent.assign_skills(
                state, observations, deterministic=False
            )
            
            results['team_skills'].append(team_skill)
            results['agent_skills'].append(agent_skills.copy())
            
            # 检查网络内部输出
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
            obs_tensor = torch.FloatTensor(observations).unsqueeze(0).to(agent.device)
            
            with torch.no_grad():
                _, _, Z_logits, z_logits, _, _ = agent.skill_coordinator(state_tensor, obs_tensor)
                
                # 检查logits范围
                if z_logits and len(z_logits) > 0:
                    # z_logits是一个列表，需要处理每个元素
                    z_min_vals = [z_logit.min().item() for z_logit in z_logits]
                    z_max_vals = [z_logit.max().item() for z_logit in z_logits]
                    z_logits_range = [min(z_min_vals), max(z_max_vals)]
                else:
                    z_logits_range = [0, 0]
                Z_logits_range = [Z_logits.min().item(), Z_logits.max().item()]
                
                results['logits_ranges'].append({
                    'Z_logits': Z_logits_range,
                    'z_logits': z_logits_range
                })
                
                # 检查NaN/Inf
                if torch.isnan(Z_logits).any() or torch.isinf(Z_logits).any():
                    results['nan_inf_count'] += 1
                    print(f"  警告: 测试 {i+1} 发现NaN/Inf值")
                
        except Exception as e:
            print(f"  错误: 测试 {i+1} 失败: {e}")
            results['nan_inf_count'] += 1
    
    # 分析结果
    print(f"技能分配测试完成 ({num_tests}次测试)")
    
    # 检查技能多样性
    unique_team_skills = len(set(results['team_skills']))
    print(f"团队技能多样性: {unique_team_skills}/{config.n_Z} ({unique_team_skills/config.n_Z*100:.1f}%)")
    
    # 检查个体技能多样性
    all_agent_skills = []
    for agent_skills in results['agent_skills']:
        all_agent_skills.extend(agent_skills)
    unique_agent_skills = len(set(all_agent_skills))
    print(f"个体技能多样性: {unique_agent_skills}/{config.n_z} ({unique_agent_skills/config.n_z*100:.1f}%)")
    
    # 检查是否所有输出都相同
    if len(set(results['team_skills'])) == 1:
        print("⚠️  警告: 所有团队技能输出都相同!")
        results['identical_outputs'] += 1
    
    # 检查logits范围
    if results['logits_ranges']:
        avg_Z_range = np.mean([r['Z_logits'][1] - r['Z_logits'][0] for r in results['logits_ranges']])
        avg_z_range = np.mean([r['z_logits'][1] - r['z_logits'][0] for r in results['logits_ranges']])
        print(f"平均logits范围: Z_logits={avg_Z_range:.2f}, z_logits={avg_z_range:.2f}")
    
    if results['nan_inf_count'] == 0:
        print("数值稳定性检查通过 ✓")
    else:
        print(f"⚠️  发现 {results['nan_inf_count']} 次数值异常")
    
    return results

def test_action_generation(agent, env, config, num_tests=10):
    """测试动作生成"""
    print("\n" + "=" * 60)
    print("测试动作生成...")
    
    results = {
        'actions': [],
        'values': [],
        'action_ranges': [],
        'nan_inf_count': 0,
        'identical_actions': 0
    }
    
    for i in range(num_tests):
        try:
            # 重置环境
            observations, info = env.reset()
            state = info['state']
            
            # 分配技能
            team_skill, agent_skills, _ = agent.assign_skills(state, observations)
            
            # 【修复】手动设置智能体的内部状态，以确保select_action能获取到正确的技能
            agent.env_team_skills[0] = team_skill
            
            # 生成动作
            actions, action_logprobs, values = agent.select_action(
                observations, agent_skills, deterministic=False, env_id=0, state=state
            )
            
            results['actions'].append(actions.copy())
            results['values'].append(values.copy())
            
            # 检查动作范围
            action_range = [actions.min(), actions.max()]
            results['action_ranges'].append(action_range)
            
            # 检查NaN/Inf
            if np.isnan(actions).any() or np.isinf(actions).any():
                results['nan_inf_count'] += 1
                print(f"  警告: 测试 {i+1} 动作包含NaN/Inf")
            
            if np.isnan(values).any() or np.isinf(values).any():
                results['nan_inf_count'] += 1
                print(f"  警告: 测试 {i+1} 价值包含NaN/Inf")
                
        except Exception as e:
            print(f"  错误: 测试 {i+1} 失败: {e}")
            results['nan_inf_count'] += 1
    
    # 分析结果
    print(f"动作生成测试完成 ({num_tests}次测试)")
    
    # 检查动作多样性
    if len(results['actions']) > 1:
        action_std = np.std([np.mean(np.abs(actions)) for actions in results['actions']])
        print(f"动作多样性 (标准差): {action_std:.4f}")
        
        if action_std < 0.001:
            print("⚠️  警告: 动作输出几乎相同!")
            results['identical_actions'] = 1
    
    # 检查价值估计
    if len(results['values']) > 0:
        all_values = np.concatenate(results['values'])
        value_mean = np.mean(all_values)
        value_std = np.std(all_values)
        print(f"价值估计统计: 均值={value_mean:.4f}, 标准差={value_std:.4f}")
        
        if abs(value_mean) < 1e-6 and value_std < 1e-6:
            print("⚠️  警告: 价值估计始终为0!")
    
    # 检查动作范围
    if results['action_ranges']:
        avg_range = np.mean([r[1] - r[0] for r in results['action_ranges']])
        print(f"平均动作范围: {avg_range:.4f}")
        
        if avg_range > config.action_bound * 2:
            print(f"⚠️  警告: 动作超出预期范围 (>{config.action_bound * 2})")
    
    if results['nan_inf_count'] == 0:
        print("数值稳定性检查通过 ✓")
    else:
        print(f"⚠️  发现 {results['nan_inf_count']} 次数值异常")
    
    return results

def test_reward_computation(agent, env, config, num_tests=5):
    """测试奖励计算"""
    print("\n" + "=" * 60)
    print("测试奖励计算...")
    
    results = {
        'env_rewards': [],
        'intrinsic_rewards': [],
        'reward_components': [],
        'nan_inf_count': 0
    }
    
    for i in range(num_tests):
        try:
            # 重置环境
            observations, info = env.reset()
            state = info['state']
            
            # 分配技能并执行动作
            team_skill, agent_skills, _ = agent.assign_skills(state, observations)
            actions, _, _ = agent.select_action(observations, agent_skills, env_id=0, state=state)
            
            # 执行环境步骤
            next_observations, env_rewards, dones, truncated, infos = env.step(actions)
            next_state = infos['next_state']
            
            # 计算内在奖励
            intrinsic_rewards = []
            reward_components = []
            
            for j in range(config.n_agents):
                intrinsic_reward, env_comp, team_disc_comp, ind_disc_comp = agent._compute_intrinsic_reward(
                    next_state, env_rewards, next_observations[j], team_skill, agent_skills[j]
                )
                
                intrinsic_rewards.append(intrinsic_reward)
                reward_components.append({
                    'env': env_comp,
                    'team_disc': team_disc_comp,
                    'ind_disc': ind_disc_comp
                })
                
                # 检查NaN/Inf
                if np.isnan(intrinsic_reward) or np.isinf(intrinsic_reward):
                    results['nan_inf_count'] += 1
                    print(f"  警告: 测试 {i+1} 智能体 {j} 内在奖励异常")
            
            results['env_rewards'].append(env_rewards)
            results['intrinsic_rewards'].append(intrinsic_rewards)
            results['reward_components'].append(reward_components)
            
        except Exception as e:
            print(f"  错误: 测试 {i+1} 失败: {e}")
            results['nan_inf_count'] += 1
    
    # 分析结果
    print(f"奖励计算测试完成 ({num_tests}次测试)")
    
    if len(results['env_rewards']) > 0:
        env_reward_mean = np.mean(results['env_rewards'])
        print(f"环境奖励均值: {env_reward_mean:.4f}")
        
        if len(results['intrinsic_rewards']) > 0:
            intrinsic_reward_mean = np.mean(results['intrinsic_rewards'])
            print(f"内在奖励均值: {intrinsic_reward_mean:.4f}")
            
            # 分析奖励组成
            if results['reward_components']:
                env_comp_mean = np.mean([np.mean([comp['env'] for comp in comps]) for comps in results['reward_components']])
                team_disc_mean = np.mean([np.mean([comp['team_disc'] for comp in comps]) for comps in results['reward_components']])
                ind_disc_mean = np.mean([np.mean([comp['ind_disc'] for comp in comps]) for comps in results['reward_components']])
                
                print(f"奖励组成均值:")
                print(f"  环境组件: {env_comp_mean:.4f}")
                print(f"  团队判别器: {team_disc_mean:.4f}")
                print(f"  个体判别器: {ind_disc_mean:.4f}")
    
    if results['nan_inf_count'] == 0:
        print("奖励计算检查通过 ✓")
    else:
        print(f"⚠️  发现 {results['nan_inf_count']} 次奖励异常")
    
    return results

def test_buffer_operations(agent, env, config, num_steps=50):
    """测试缓冲区操作"""
    print("\n" + "=" * 60)
    print("测试缓冲区操作...")
    
    try:
        # 重置缓冲区
        agent.rollout_buffer.reset()
        
        # 模拟数据收集
        observations, info = env.reset()
        state = info['state']
        
        success_count = 0
        error_count = 0
        
        for step in range(num_steps):
            try:
                # 分配技能
                team_skill, agent_skills, log_probs = agent.assign_skills(state, observations)
                
                # 生成动作
                actions, action_logprobs, values = agent.select_action(
                    observations, agent_skills, env_id=0, state=state
                )
                
                # 执行环境步骤
                next_observations, env_rewards, dones, truncated, infos = env.step(actions)
                next_state = infos['next_state']
                
                # 存储经验
                # 确保dones是数组格式而不是单个布尔值
                if isinstance(dones, bool):
                    dones_array = np.array([dones] * config.n_agents)
                elif hasattr(dones, '__iter__'):
                    dones_array = np.array(dones)
                else:
                    dones_array = np.array([dones] * config.n_agents)
                
                reward_components = agent.store_transition(
                    state, next_state, observations, next_observations,
                    actions, env_rewards, dones_array, team_skill, agent_skills,
                    action_logprobs, log_probs, step % config.k, env_id=0,
                    values=values, rollout_step_idx=step
                )
                
                if reward_components is not None:
                    success_count += 1
                
                # 更新状态
                state = next_state
                observations = next_observations
                
                # 如果环境结束，重置
                if np.any(dones_array):
                    observations, info = env.reset()
                    state = info['state']
                    agent.reset_env_state(0)
                
            except Exception as e:
                error_count += 1
                print(f"  错误: 步骤 {step} 失败: {e}")
        
        # 检查缓冲区状态
        buffer_stats = agent.rollout_buffer.get_storage_stats()
        print(f"缓冲区操作测试完成 ({num_steps}步)")
        print(f"成功存储: {success_count}/{num_steps} ({success_count/num_steps*100:.1f}%)")
        print(f"错误次数: {error_count}")
        
        print(f"缓冲区统计:")
        print(f"  低层成功率: {buffer_stats['low_level_success_rate']*100:.1f}%")
        print(f"  高层成功率: {buffer_stats['high_level_success_rate']*100:.1f}%")
        print(f"  低层重复率: {buffer_stats['low_level_duplicate_rate']*100:.1f}%")
        print(f"  高层重复率: {buffer_stats['high_level_duplicate_rate']*100:.1f}%")
        
        # 诊断缓冲区
        diagnosis = agent.rollout_buffer.diagnose_buffer_state(num_steps)
        
        if diagnosis['has_nan'] or diagnosis['has_inf']:
            print("⚠️  缓冲区包含异常数值")
        else:
            print("缓冲区数值检查通过 ✓")
        
        return buffer_stats, diagnosis
        
    except Exception as e:
        print(f"缓冲区测试失败: {e}")
        return None, None

def generate_diagnosis_report(skill_results, action_results, reward_results, buffer_stats, buffer_diagnosis):
    """生成诊断报告"""
    print("\n" + "=" * 60)
    print("诊断报告总结")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # 检查技能分配问题
    if skill_results:
        if skill_results['identical_outputs'] > 0:
            issues.append("❌ 技能分配输出完全相同 - 可能的策略坍塌")
        if skill_results['nan_inf_count'] > 0:
            issues.append(f"❌ 技能分配存在 {skill_results['nan_inf_count']} 次数值异常")
    
    # 检查动作生成问题
    if action_results:
        if action_results['identical_actions'] > 0:
            issues.append("❌ 动作输出几乎相同 - 可能的策略坍塌")
        if action_results['nan_inf_count'] > 0:
            issues.append(f"❌ 动作生成存在 {action_results['nan_inf_count']} 次数值异常")
        # 检查价值估计是否恒为零
        if len(action_results['values']) > 0:
            all_values = np.concatenate(action_results['values'])
            if np.allclose(all_values, 0):
                issues.append("❌ 价值估计始终为0 - Critic网络可能未正确学习")
    
    # 检查奖励计算问题
    if reward_results:
        if reward_results['nan_inf_count'] > 0:
            issues.append(f"❌ 奖励计算存在 {reward_results['nan_inf_count']} 次数值异常")
    
    # 检查缓冲区问题
    if buffer_stats:
        if buffer_stats['low_level_success_rate'] < 0.9:
            warnings.append(f"⚠️  低层数据存储成功率较低: {buffer_stats['low_level_success_rate']*100:.1f}%")
        if buffer_stats['high_level_success_rate'] < 0.9:
            warnings.append(f"⚠️  高层数据存储成功率较低: {buffer_stats['high_level_success_rate']*100:.1f}%")
    
    if buffer_diagnosis:
        if buffer_diagnosis['has_nan'] or buffer_diagnosis['has_inf']:
            issues.append("❌ 缓冲区包含NaN/Inf数值")
    
    # 输出结果
    if not issues and not warnings:
        print("🎉 所有检查都通过！网络运行正常。")
        print("\n建议:")
        print("- 检查超参数设置（学习率、熵权重等）")
        print("- 增加训练时间或调整探索策略")
        print("- 检查环境奖励信号的有效性")
    else:
        if issues:
            print("🚨 发现严重问题:")
            for issue in issues:
                print(f"  {issue}")
        
        if warnings:
            print("\n⚠️  发现警告:")
            for warning in warnings:
                print(f"  {warning}")
        
        print("\n建议的修复措施:")
        if any("策略坍塌" in issue for issue in issues):
            print("- 增加熵权重 (lambda_h, lambda_l)")
            print("- 减小学习率")
            print("- 增加技能空间大小 (n_Z, n_z)")
            print("- 检查网络初始化")
        
        if any("数值异常" in issue for issue in issues):
            print("- 检查梯度裁剪设置")
            print("- 添加更严格的数值稳定性检查")
            print("- 检查网络架构中的激活函数")
        
        if any("存储成功率" in warning for warning in warnings):
            print("- 检查缓冲区大小设置")
            print("- 验证数据存储逻辑")

def main():
    """主函数"""
    print("HMASD 策略坍塌快速诊断")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 1. 创建环境和配置
        env, config = create_test_environment()
        
        # 2. 测试网络初始化
        agent = test_network_initialization(config)
        if agent is None:
            print("❌ 网络初始化失败，无法继续测试")
            return
        
        # 3. 测试技能分配
        skill_results = test_skill_assignment(agent, env, config)
        
        # 4. 测试动作生成
        action_results = test_action_generation(agent, env, config)
        
        # 5. 测试奖励计算
        reward_results = test_reward_computation(agent, env, config)
        
        # 6. 测试缓冲区操作
        buffer_stats, buffer_diagnosis = test_buffer_operations(agent, env, config)
        
        # 7. 生成诊断报告
        generate_diagnosis_report(skill_results, action_results, reward_results, buffer_stats, buffer_diagnosis)
        
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        elapsed_time = time.time() - start_time
        print(f"\n诊断完成，耗时: {elapsed_time:.2f}秒")

if __name__ == "__main__":
    main()
