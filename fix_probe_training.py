"""
修复探针测试的训练问题
主要问题：网络没有正确学习，输出都是0或随机值
"""

import torch
import numpy as np
from logger import main_logger
from config_1 import Config
from probe_agent import create_probe_agent
from envs.probe_environments import create_probe_environment


def diagnose_network_training():
    """诊断网络训练问题"""
    main_logger.info("开始诊断网络训练问题...")
    
    # 创建简单配置
    config = Config()
    config.state_dim = 1
    config.obs_dim = 1
    config.action_dim = 1
    config.n_agents = 2
    config.n_Z = 2
    config.n_z = 2
    config.action_bound = 2.0
    config.num_envs = 1
    config.rollout_length = 32
    config.batch_size = 16
    
    # 关键修复：调整学习率
    config.lr_coordinator = 1e-3  # 提高学习率
    config.lr_discoverer = 1e-3   # 提高学习率
    config.lr_discriminator = 1e-3 # 提高学习率
    
    # 关键修复：调整网络大小
    config.hidden_size = 32       # 减小网络，更容易训练
    config.gru_hidden_size = 32
    config.embedding_dim = 16
    
    # 关键修复：调整训练参数
    config.clip_epsilon = 0.3     # 增大裁剪范围
    config.value_loss_coef = 1.0  # 增大价值损失权重
    config.lambda_h = 0.1         # 增大熵系数
    config.lambda_l = 0.1
    
    # 关键修复：调整内在奖励权重
    config.lambda_e = 1.0
    config.lambda_D = 0.1         # 降低判别器权重，避免过度复杂
    config.lambda_d = 0.1
    
    config.update_env_dims(config.state_dim, config.obs_dim)
    
    # 创建价值函数测试环境
    env = create_probe_environment('value', n_agents=config.n_agents)
    expected_value = env.get_expected_value(gamma=0.99)
    
    # 创建探针智能体
    agent = create_probe_agent(config, probe_mode='fixed_skills', device=torch.device('cpu'))
    agent.set_fixed_skills(team_skill=0, agent_skills=[0, 0])
    
    main_logger.info(f"期望价值: {expected_value:.4f}")
    main_logger.info("开始简化训练测试...")
    
    # 简化的训练循环
    obs_list, state_list = env.reset()
    done = False
    
    value_predictions = []
    rewards_collected = []
    
    for step in range(100):  # 只训练100步
        if done:
            obs_list, state_list = env.reset()
        
        current_obs = obs_list[0]
        current_state = state_list[0]
        
        # 分配技能
        team_skill, agent_skills, log_probs = agent.assign_skills(current_state, current_obs)
        
        # 选择动作
        actions, action_logprobs, values = agent.select_action(
            current_obs, agent_skills, env_id=0, state=current_state
        )
        
        # 记录价值预测
        if values is not None:
            mean_value = np.mean(values)
            value_predictions.append(mean_value)
            main_logger.info(f"步骤 {step}: 价值预测 = {mean_value:.4f}")
        
        # 执行动作
        next_obs_list, next_state_list, rewards, dones, infos = env.step([actions])
        done = dones[0]
        rewards_collected.append(rewards[0])
        
        # 存储经验
        agent.store_transition(
            state=current_state,
            next_state=next_state_list[0],
            observations=current_obs,
            next_observations=next_obs_list[0],
            actions=actions,
            rewards=rewards[0],
            dones=dones[0],
            team_skill=team_skill,
            agent_skills=agent_skills,
            action_logprobs=action_logprobs,
            log_probs=log_probs,
            env_id=0,
            values=values,
            rollout_step_idx=step % config.rollout_length
        )
        
        # 每32步更新一次
        if (step + 1) % config.rollout_length == 0:
            main_logger.info(f"执行网络更新 (步骤 {step + 1})...")
            
            # 手动检查网络参数是否在变化
            old_params = {}
            for name, param in agent.skill_discoverer.named_parameters():
                old_params[name] = param.data.clone()
            
            # 执行更新
            update_results = agent.update(
                steps_in_buffer=config.rollout_length,
                last_next_state=next_state_list[0],
                last_dones=dones[0],
                last_next_obs=next_obs_list[0]
            )
            
            # 检查参数是否变化
            param_changed = False
            for name, param in agent.skill_discoverer.named_parameters():
                if not torch.equal(old_params[name], param.data):
                    param_changed = True
                    break
            
            main_logger.info(f"网络参数是否变化: {param_changed}")
            main_logger.info(f"更新结果: {update_results}")
            
            # 清空缓冲区
            agent.clear_buffers()
        
        # 更新状态
        obs_list = next_obs_list
        state_list = next_state_list
    
    # 分析结果
    if value_predictions:
        final_values = value_predictions[-10:]
        mean_final_value = np.mean(final_values)
        value_error = abs(mean_final_value - expected_value)
        
        main_logger.info(f"诊断结果:")
        main_logger.info(f"  期望价值: {expected_value:.4f}")
        main_logger.info(f"  最终平均价值: {mean_final_value:.4f}")
        main_logger.info(f"  价值误差: {value_error:.4f}")
        main_logger.info(f"  平均奖励: {np.mean(rewards_collected):.4f}")
        
        # 检查网络输出
        with torch.no_grad():
            test_state = torch.FloatTensor([1.0]).unsqueeze(0)
            test_value, _ = agent.skill_discoverer.get_value(test_state, torch.tensor([0]))
            main_logger.info(f"  测试状态价值输出: {test_value.item():.4f}")
        
        return mean_final_value, value_error
    
    return 0.0, float('inf')


def test_simple_policy_learning():
    """测试简单的策略学习"""
    main_logger.info("测试简单策略学习...")
    
    config = Config()
    config.state_dim = 1
    config.obs_dim = 1
    config.action_dim = 1
    config.n_agents = 1  # 只用一个智能体简化问题
    config.n_Z = 1
    config.n_z = 1
    config.action_bound = 2.0
    config.num_envs = 1
    config.rollout_length = 16
    config.batch_size = 8
    
    # 更激进的学习率
    config.lr_discoverer = 5e-3
    config.hidden_size = 16
    config.gru_hidden_size = 16
    
    config.update_env_dims(config.state_dim, config.obs_dim)
    
    # 创建策略环境
    env = create_probe_environment('policy', n_agents=config.n_agents)
    agent = create_probe_agent(config, probe_mode='fixed_skills', device=torch.device('cpu'))
    agent.set_fixed_skills(team_skill=0, agent_skills=[0])
    
    obs_list, state_list = env.reset()
    done = False
    
    positive_actions = 0
    total_actions = 0
    
    for step in range(200):
        if done:
            obs_list, state_list = env.reset()
        
        current_obs = obs_list[0]
        current_state = state_list[0]
        
        # 分配技能
        team_skill, agent_skills, log_probs = agent.assign_skills(current_state, current_obs)
        
        # 选择动作
        actions, action_logprobs, values = agent.select_action(
            current_obs, agent_skills, env_id=0, state=current_state
        )
        
        # 统计正动作
        action_value = actions[0, 0]
        total_actions += 1
        if action_value > 0:
            positive_actions += 1
        
        if step % 50 == 0:
            positive_ratio = positive_actions / total_actions if total_actions > 0 else 0
            main_logger.info(f"步骤 {step}: 动作 = {action_value:.4f}, 正动作比例 = {positive_ratio:.3f}")
        
        # 执行动作
        next_obs_list, next_state_list, rewards, dones, infos = env.step([actions])
        done = dones[0]
        
        # 存储经验
        agent.store_transition(
            state=current_state,
            next_state=next_state_list[0],
            observations=current_obs,
            next_observations=next_obs_list[0],
            actions=actions,
            rewards=rewards[0],
            dones=dones[0],
            team_skill=team_skill,
            agent_skills=agent_skills,
            action_logprobs=action_logprobs,
            log_probs=log_probs,
            env_id=0,
            values=values,
            rollout_step_idx=step % config.rollout_length
        )
        
        # 更新网络
        if (step + 1) % config.rollout_length == 0:
            agent.update(
                steps_in_buffer=config.rollout_length,
                last_next_state=next_state_list[0],
                last_dones=dones[0],
                last_next_obs=next_obs_list[0]
            )
            agent.clear_buffers()
        
        obs_list = next_obs_list
        state_list = next_state_list
    
    final_positive_ratio = positive_actions / total_actions
    main_logger.info(f"最终正动作比例: {final_positive_ratio:.3f}")
    
    return final_positive_ratio


if __name__ == "__main__":
    main_logger.info("开始修复探针测试...")
    
    # 诊断价值函数训练
    final_value, error = diagnose_network_training()
    
    # 测试策略学习
    positive_ratio = test_simple_policy_learning()
    
    main_logger.info("修复测试完成!")
    main_logger.info(f"价值函数误差: {error:.4f}")
    main_logger.info(f"策略正动作比例: {positive_ratio:.3f}")
