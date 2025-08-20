"""
增强版简化探针测试，详细错误报告
主要功能：
1. 统一批次大小和rollout长度
2. 简化网络结构
3. 确保形状匹配
4. 详细的错误分类和报告
5. 逐步进度跟踪
6. 结构化测试结果
"""

import torch
import numpy as np
import json
import traceback
import time
from datetime import datetime
import logging
from logger import main_logger, setup_logger
from config_1 import Config
from envs.probe_environments import create_probe_environment
from probe_agent import create_probe_agent


class TestResult:
    """测试结果类，用于结构化存储测试信息"""
    def __init__(self, test_name):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.status = "RUNNING"  # RUNNING, PASSED, FAILED, ERROR
        self.error_category = None
        self.error_message = None
        self.error_traceback = None
        self.steps_completed = []
        self.steps_failed = []
        self.metrics = {}
        self.warnings = []
        self.recommendations = []
        
    def add_step(self, step_name, success=True, details=None):
        """添加测试步骤"""
        step_info = {
            'name': step_name,
            'success': success,
            'timestamp': time.time(),
            'details': details or {}
        }
        
        if success:
            self.steps_completed.append(step_info)
            main_logger.info(f"✅ [{self.test_name}] {step_name} - 成功")
        else:
            self.steps_failed.append(step_info)
            main_logger.error(f"❌ [{self.test_name}] {step_name} - 失败: {details}")
            
    def add_warning(self, warning_msg):
        """添加警告"""
        self.warnings.append({
            'message': warning_msg,
            'timestamp': time.time()
        })
        main_logger.warning(f"⚠️ [{self.test_name}] {warning_msg}")
        
    def add_metric(self, name, value, expected=None, threshold=None):
        """添加指标"""
        self.metrics[name] = {
            'value': value,
            'expected': expected,
            'threshold': threshold,
            'timestamp': time.time()
        }
        
        if expected is not None and isinstance(expected, (int, float)):
            error = abs(value - expected) if isinstance(value, (int, float)) else None
            if isinstance(value, (int, float)):
                main_logger.info(f"📊 [{self.test_name}] {name}: {value:.4f} (期望: {expected:.4f}, 误差: {error:.4f if error is not None else 'N/A'})")
            else:
                main_logger.info(f"📊 [{self.test_name}] {name}: {value} (期望: {expected:.4f})")
        else:
            if isinstance(value, (int, float)):
                main_logger.info(f"📊 [{self.test_name}] {name}: {value:.4f}")
            else:
                main_logger.info(f"📊 [{self.test_name}] {name}: {value}")
    
    def set_error(self, error_category, error_message, error_traceback=None):
        """设置错误信息"""
        self.status = "ERROR"
        self.error_category = error_category
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.end_time = time.time()
        
        main_logger.error(f"💥 [{self.test_name}] 错误类别: {error_category}")
        main_logger.error(f"💥 [{self.test_name}] 错误信息: {error_message}")
        
    def set_passed(self):
        """设置测试通过"""
        self.status = "PASSED"
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        main_logger.info(f"🎉 [{self.test_name}] 测试通过! 耗时: {duration:.2f}秒")
        
    def set_failed(self, reason):
        """设置测试失败"""
        self.status = "FAILED"
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        main_logger.error(f"❌ [{self.test_name}] 测试失败: {reason} 耗时: {duration:.2f}秒")
        
    def add_recommendation(self, recommendation):
        """添加建议"""
        self.recommendations.append(recommendation)
        main_logger.info(f"💡 [{self.test_name}] 建议: {recommendation}")
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            'test_name': self.test_name,
            'status': self.status,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.end_time - self.start_time if self.end_time else None,
            'error_category': self.error_category,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'steps_completed': self.steps_completed,
            'steps_failed': self.steps_failed,
            'metrics': self.metrics,
            'warnings': self.warnings,
            'recommendations': self.recommendations
        }


def categorize_error(exception):
    """错误分类函数"""
    error_type = type(exception).__name__
    error_msg = str(exception)
    
    if "shape" in error_msg.lower() or "size" in error_msg.lower():
        return "DIMENSION_MISMATCH", f"维度不匹配错误: {error_msg}"
    elif "cuda" in error_msg.lower() or "device" in error_msg.lower():
        return "DEVICE_ERROR", f"设备错误: {error_msg}"
    elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
        return "MEMORY_ERROR", f"内存错误: {error_msg}"
    elif "nan" in error_msg.lower() or "inf" in error_msg.lower():
        return "NUMERICAL_ERROR", f"数值错误: {error_msg}"
    elif "gradient" in error_msg.lower():
        return "GRADIENT_ERROR", f"梯度错误: {error_msg}"
    elif "network" in error_msg.lower() or "module" in error_msg.lower():
        return "NETWORK_ERROR", f"网络结构错误: {error_msg}"
    elif isinstance(exception, KeyError):
        return "CONFIG_ERROR", f"配置错误: {error_msg}"
    elif isinstance(exception, ValueError):
        return "VALUE_ERROR", f"数值错误: {error_msg}"
    elif isinstance(exception, RuntimeError):
        return "RUNTIME_ERROR", f"运行时错误: {error_msg}"
    else:
        return "UNKNOWN_ERROR", f"未知错误 ({error_type}): {error_msg}"


def get_error_recommendations(error_category):
    """根据错误类别提供建议"""
    recommendations = {
        "DIMENSION_MISMATCH": [
            "检查批次大小配置是否一致",
            "验证网络输入输出维度",
            "确认rollout_length和batch_size匹配"
        ],
        "DEVICE_ERROR": [
            "检查CUDA是否可用",
            "确认所有张量在同一设备上",
            "考虑使用CPU模式进行调试"
        ],
        "MEMORY_ERROR": [
            "减小批次大小",
            "减少网络层数或隐藏单元数",
            "使用梯度累积"
        ],
        "NUMERICAL_ERROR": [
            "检查学习率是否过大",
            "添加梯度裁剪",
            "检查损失函数计算"
        ],
        "GRADIENT_ERROR": [
            "检查网络参数是否需要梯度",
            "验证损失函数的可微性",
            "添加梯度裁剪"
        ],
        "NETWORK_ERROR": [
            "检查网络结构定义",
            "验证前向传播逻辑",
            "确认所有必需的模块都已初始化"
        ],
        "CONFIG_ERROR": [
            "检查配置文件格式",
            "验证所有必需的配置项",
            "确认配置值的类型和范围"
        ],
        "VALUE_ERROR": [
            "检查输入数据的有效性",
            "验证参数范围",
            "确认数据类型匹配"
        ],
        "RUNTIME_ERROR": [
            "检查系统资源",
            "验证依赖库版本",
            "查看详细错误日志"
        ],
        "UNKNOWN_ERROR": [
            "查看完整错误堆栈",
            "检查最近的代码更改",
            "尝试简化测试场景"
        ]
    }
    return recommendations.get(error_category, ["联系开发者获取支持"])


def test_simple_value_function():
    """增强版价值函数测试，带详细错误报告"""
    result = TestResult("价值函数测试")
    
    try:
        # 步骤1: 配置初始化
        result.add_step("配置初始化")
        config = Config()
        config.state_dim = 1
        config.obs_dim = 1
        config.action_dim = 1
        config.n_agents = 2
        config.n_Z = 2
        config.n_z = 2
        config.action_bound = 2.0
        
        # 关键修复：统一批次配置，避免广播错误
        config.num_envs = 1
        config.rollout_length = 16
        config.batch_size = 16
        config.coordinator_batch_size = 16
        config.sequence_batch_size = 8
        
        # 简化网络配置 - 确保参数兼容性
        config.hidden_size = 16
        config.gru_hidden_size = 16
        config.embedding_dim = 16  # 必须能被n_heads整除
        config.n_heads = 2         # 必须为偶数以避免PyTorch警告
        config.n_encoder_layers = 1
        config.n_decoder_layers = 1
        
        # 学习率配置 - 大幅提高价值函数学习率以促进收敛
        config.lr_coordinator = 5e-4  # 提高协调器学习率
        config.lr_discoverer = 3e-2   # 大幅提高发现器学习率，专注价值函数学习
        config.lr_discriminator = 1e-2
        
        # 其他训练参数 - 优化价值函数学习
        config.clip_epsilon = 0.2  # 减小裁剪范围，提高稳定性
        config.value_loss_coef = 2.0  # 增加价值损失权重，专注价值函数学习
        config.lambda_h = 0.1
        config.lambda_l = 0.1
        config.lambda_e = 1.0
        config.lambda_D = 0.0
        config.lambda_d = 0.0
        config.k = 8
        config.max_grad_norm = 0.5  # 减小梯度裁剪，避免梯度消失
        config.use_valuenorm = False
        config.use_obsnorm = False
        config.use_opt = False
        config.use_opt_coordinator = False
        
        config.update_env_dims(config.state_dim, config.obs_dim)
        
        # 步骤2: 环境创建
        result.add_step("环境创建")
        env = create_probe_environment('value', n_agents=config.n_agents)
        expected_value = env.get_expected_value(gamma=0.99)
        result.add_metric("期望价值", expected_value)
        
        # 步骤3: 智能体创建
        result.add_step("智能体创建")
        agent = create_probe_agent(
            config, 
            probe_mode='fixed_skills',
            log_dir='logs/simple_probe',
            device=torch.device('cpu')
        )
        agent.set_fixed_skills(team_skill=0, agent_skills=[0, 0])
        
        # 步骤4: 训练循环
        result.add_step("开始训练循环")
        obs_list, state_list = env.reset()
        done = False
        value_predictions = []
        step_count = 0
        
        for episode in range(80):  # 增加训练轮数从50到80
            try:
                if done:
                    obs_list, state_list = env.reset()
                
                episode_values = []
                
                # Rollout阶段
                for step in range(config.rollout_length):
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
                        episode_values.append(mean_value)
                    
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
                        rollout_step_idx=step
                    )
                    
                    obs_list = next_obs_list
                    state_list = next_state_list
                    step_count += 1
                
                # 网络更新
                update_results = agent.update(
                    steps_in_buffer=config.rollout_length,
                    last_next_state=next_state_list[0],
                    last_dones=dones[0],
                    last_next_obs=next_obs_list[0]
                )
                
                # 记录更新结果
                if update_results:
                    result.add_metric(f"Episode_{episode}_Discoverer_Loss", 
                                    update_results.get('discoverer_loss', 0))
                    result.add_metric(f"Episode_{episode}_Coordinator_Loss", 
                                    update_results.get('coordinator_loss', 0))
                
                # 清空缓冲区
                agent.clear_buffers()
                
                # 报告当前价值预测
                if episode_values:
                    mean_episode_value = np.mean(episode_values)
                    value_error = abs(mean_episode_value - expected_value)
                    result.add_metric(f"Episode_{episode}_Value_Prediction", 
                                    mean_episode_value, expected_value)
                    result.add_metric(f"Episode_{episode}_Value_Error", value_error)
                    
                    # 检查是否有异常值
                    if np.isnan(mean_episode_value) or np.isinf(mean_episode_value):
                        result.add_warning(f"Episode {episode}: 价值预测包含NaN或Inf")
                    elif value_error > expected_value * 2:
                        result.add_warning(f"Episode {episode}: 价值误差过大 ({value_error:.4f})")
                
            except Exception as e:
                error_category, error_message = categorize_error(e)
                result.add_step(f"Episode {episode} 训练", False, 
                              {'error': error_message, 'traceback': traceback.format_exc()})
                
                # 添加针对性建议
                recommendations = get_error_recommendations(error_category)
                for rec in recommendations:
                    result.add_recommendation(rec)
                
                # 如果是严重错误，停止测试
                if error_category in ["MEMORY_ERROR", "DEVICE_ERROR"]:
                    result.set_error(error_category, error_message, traceback.format_exc())
                    return result
        
        # 步骤5: 结果分析
        result.add_step("结果分析")
        if value_predictions:
            final_values = value_predictions[-10:]
            mean_final_value = np.mean(final_values)
            value_error = abs(mean_final_value - expected_value)
            
            result.add_metric("最终平均价值", mean_final_value, expected_value)
            result.add_metric("最终价值误差", value_error)
            result.add_metric("总训练步数", step_count)
            
            # 收敛判断
            converged = value_error < 2.0
            result.add_metric("是否收敛", converged)
            
            if converged:
                result.set_passed()
            else:
                result.set_failed(f"价值函数未收敛，误差: {value_error:.4f}")
                result.add_recommendation("尝试增加训练轮数")
                result.add_recommendation("调整学习率")
                result.add_recommendation("检查网络结构配置")
        else:
            result.set_failed("未获得任何价值预测")
            result.add_recommendation("检查价值网络的前向传播")
            result.add_recommendation("验证智能体的select_action方法")
            
    except Exception as e:
        error_category, error_message = categorize_error(e)
        result.set_error(error_category, error_message, traceback.format_exc())
        
        # 添加针对性建议
        recommendations = get_error_recommendations(error_category)
        for rec in recommendations:
            result.add_recommendation(rec)
    
    return result


def test_simple_policy_learning():
    """增强版策略学习测试，带详细错误报告"""
    result = TestResult("策略学习测试")
    
    try:
        # 步骤1: 配置初始化
        result.add_step("配置初始化")
        config = Config()
        config.state_dim = 1
        config.obs_dim = 1
        config.action_dim = 1
        config.n_agents = 1
        config.n_Z = 1
        config.n_z = 1
        config.action_bound = 2.0
        
        # 关键修复：统一批次配置
        config.num_envs = 1
        config.rollout_length = 8
        config.batch_size = 8
        config.coordinator_batch_size = 8
        config.sequence_batch_size = 4
        
        # 简化网络配置 - 确保参数兼容性
        config.hidden_size = 16    # 增加最小尺寸以提高稳定性
        config.gru_hidden_size = 16
        config.embedding_dim = 16  # 必须能被n_heads整除
        config.n_heads = 2         # 必须为偶数以避免PyTorch警告
        config.n_encoder_layers = 1
        config.n_decoder_layers = 1
        
        # 更高的学习率
        config.lr_discoverer = 1e-2
        config.lambda_l = 0.01
        
        # 在策略测试中禁用归一化
        config.use_valuenorm = False
        config.use_obsnorm = False
        
        config.update_env_dims(config.state_dim, config.obs_dim)
        
        # 步骤2: 环境创建
        result.add_step("环境创建")
        env = create_probe_environment('policy', n_agents=config.n_agents)
        
        # 步骤3: 智能体创建
        result.add_step("智能体创建")
        agent = create_probe_agent(
            config,
            probe_mode='fixed_skills',
            log_dir='logs/simple_policy',
            device=torch.device('cpu')
        )
        agent.set_fixed_skills(team_skill=0, agent_skills=[0])
        
        # 步骤4: 训练循环
        result.add_step("开始训练循环")
        obs_list, state_list = env.reset()
        done = False
        
        positive_actions = 0
        total_actions = 0
        action_history = []
        reward_history = []
        
        for episode in range(20):
            try:
                if done:
                    obs_list, state_list = env.reset()
                
                episode_actions = []
                episode_rewards = []
                
                # Rollout阶段
                for step in range(config.rollout_length):
                    current_obs = obs_list[0]
                    current_state = state_list[0]
                    
                    # 分配技能
                    team_skill, agent_skills, log_probs = agent.assign_skills(current_state, current_obs)
                    
                    # 选择动作
                    actions, action_logprobs, values = agent.select_action(
                        current_obs, agent_skills, env_id=0, state=current_state
                    )
                    
                    # 统计动作
                    action_value = actions[0, 0]
                    total_actions += 1
                    if action_value > 0:
                        positive_actions += 1
                    
                    action_history.append(action_value)
                    episode_actions.append(action_value)
                    
                    # 执行动作
                    next_obs_list, next_state_list, rewards, dones, infos = env.step([actions])
                    done = dones[0]
                    
                    reward_history.append(rewards[0])
                    episode_rewards.append(rewards[0])
                    
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
                        rollout_step_idx=step
                    )
                    
                    obs_list = next_obs_list
                    state_list = next_state_list
                
                # 网络更新
                update_results = agent.update(
                    steps_in_buffer=config.rollout_length,
                    last_next_state=next_state_list[0],
                    last_dones=dones[0],
                    last_next_obs=next_obs_list[0]
                )
                agent.clear_buffers()
                
                # 记录episode指标
                if episode_actions:
                    mean_action = np.mean(episode_actions)
                    positive_ratio_episode = sum(1 for a in episode_actions if a > 0) / len(episode_actions)
                    mean_reward = np.mean(episode_rewards)
                    
                    result.add_metric(f"Episode_{episode}_Mean_Action", mean_action)
                    result.add_metric(f"Episode_{episode}_Positive_Ratio", positive_ratio_episode)
                    result.add_metric(f"Episode_{episode}_Mean_Reward", mean_reward)
                    
                    # 检查学习进度
                    if episode >= 5:  # 从第5个episode开始检查
                        recent_positive_ratio = positive_actions / total_actions
                        if recent_positive_ratio < 0.3 and episode > 10:
                            result.add_warning(f"Episode {episode}: 正动作比例过低 ({recent_positive_ratio:.3f})")
                        elif recent_positive_ratio > 0.7:
                            result.add_step(f"Episode {episode}: 学习进展良好", True, 
                                          {'positive_ratio': recent_positive_ratio})
                
                # 记录更新结果
                if update_results:
                    result.add_metric(f"Episode_{episode}_Policy_Loss", 
                                    update_results.get('discoverer_loss', 0))
                
            except Exception as e:
                error_category, error_message = categorize_error(e)
                result.add_step(f"Episode {episode} 训练", False, 
                              {'error': error_message, 'traceback': traceback.format_exc()})
                
                # 添加针对性建议
                recommendations = get_error_recommendations(error_category)
                for rec in recommendations:
                    result.add_recommendation(rec)
                
                # 如果是严重错误，停止测试
                if error_category in ["MEMORY_ERROR", "DEVICE_ERROR"]:
                    result.set_error(error_category, error_message, traceback.format_exc())
                    return result
        
        # 步骤5: 结果分析
        result.add_step("结果分析")
        if total_actions > 0:
            final_positive_ratio = positive_actions / total_actions
            mean_final_reward = np.mean(reward_history[-20:]) if len(reward_history) >= 20 else np.mean(reward_history)
            
            result.add_metric("最终正动作比例", final_positive_ratio)
            result.add_metric("总动作数", total_actions)
            result.add_metric("最终平均奖励", mean_final_reward)
            
            # 学习判断
            learned = final_positive_ratio > 0.55
            result.add_metric("是否学会", learned)
            
            if learned:
                result.set_passed()
            else:
                result.set_failed(f"策略未学会，正动作比例: {final_positive_ratio:.3f}")
                result.add_recommendation("增加训练轮数")
                result.add_recommendation("调整学习率或熵正则化系数")
                result.add_recommendation("检查奖励函数设计")
                
                # 分析失败原因
                if final_positive_ratio < 0.3:
                    result.add_recommendation("策略可能陷入局部最优，尝试增加探索")
                elif 0.3 <= final_positive_ratio <= 0.55:
                    result.add_recommendation("学习进度缓慢，可能需要更多训练时间")
        else:
            result.set_failed("未执行任何动作")
            result.add_recommendation("检查环境和智能体的交互逻辑")
            
    except Exception as e:
        error_category, error_message = categorize_error(e)
        result.set_error(error_category, error_message, traceback.format_exc())
        
        # 添加针对性建议
        recommendations = get_error_recommendations(error_category)
        for rec in recommendations:
            result.add_recommendation(rec)
    
    return result


def save_test_results(results, filename="enhanced_probe_test_results.json"):
    """保存测试结果到JSON文件"""
    try:
        # 转换TestResult对象为字典
        results_dict = {}
        for test_name, result in results.items():
            if isinstance(result, TestResult):
                results_dict[test_name] = result.to_dict()
            else:
                results_dict[test_name] = result
        
        # 添加测试总结
        results_dict['test_summary'] = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'passed_tests': sum(1 for r in results.values() if isinstance(r, TestResult) and r.status == "PASSED"),
            'failed_tests': sum(1 for r in results.values() if isinstance(r, TestResult) and r.status == "FAILED"),
            'error_tests': sum(1 for r in results.values() if isinstance(r, TestResult) and r.status == "ERROR")
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False, default=str)
        
        main_logger.info(f"测试结果已保存到: {filename}")
        return True
    except Exception as e:
        main_logger.error(f"保存测试结果失败: {e}")
        return False


def print_detailed_summary(results):
    """打印详细的测试总结"""
    main_logger.info("=" * 80)
    main_logger.info("📋 详细测试报告")
    main_logger.info("=" * 80)
    
    total_tests = len(results)
    passed_tests = 0
    failed_tests = 0
    error_tests = 0
    
    for test_name, result in results.items():
        if isinstance(result, TestResult):
            main_logger.info(f"\n🔍 {result.test_name}")
            main_logger.info(f"   状态: {result.status}")
            main_logger.info(f"   耗时: {result.end_time - result.start_time:.2f}秒" if result.end_time else "   耗时: 未完成")
            main_logger.info(f"   完成步骤: {len(result.steps_completed)}")
            main_logger.info(f"   失败步骤: {len(result.steps_failed)}")
            main_logger.info(f"   警告数量: {len(result.warnings)}")
            main_logger.info(f"   建议数量: {len(result.recommendations)}")
            
            if result.status == "PASSED":
                passed_tests += 1
                main_logger.info("   ✅ 测试通过")
            elif result.status == "FAILED":
                failed_tests += 1
                main_logger.info("   ❌ 测试失败")
                if result.recommendations:
                    main_logger.info("   💡 建议:")
                    for rec in result.recommendations[:3]:  # 只显示前3个建议
                        main_logger.info(f"      - {rec}")
            elif result.status == "ERROR":
                error_tests += 1
                main_logger.info("   💥 测试错误")
                main_logger.info(f"   错误类别: {result.error_category}")
                main_logger.info(f"   错误信息: {result.error_message}")
                if result.recommendations:
                    main_logger.info("   💡 建议:")
                    for rec in result.recommendations[:3]:
                        main_logger.info(f"      - {rec}")
            
            # 显示关键指标
            if result.metrics:
                main_logger.info("   📊 关键指标:")
                key_metrics = ['最终平均价值', '最终价值误差', '最终正动作比例', '是否收敛', '是否学会']
                for metric_name in key_metrics:
                    if metric_name in result.metrics:
                        metric = result.metrics[metric_name]
                        value = metric['value']
                        if isinstance(value, bool):
                            main_logger.info(f"      {metric_name}: {'是' if value else '否'}")
                        elif isinstance(value, (int, float)):
                            main_logger.info(f"      {metric_name}: {value:.4f}")
                        else:
                            main_logger.info(f"      {metric_name}: {value}")
    
    # 总体统计
    main_logger.info("\n" + "=" * 80)
    main_logger.info("📊 测试统计")
    main_logger.info("=" * 80)
    main_logger.info(f"总测试数: {total_tests}")
    main_logger.info(f"通过测试: {passed_tests} ✅")
    main_logger.info(f"失败测试: {failed_tests} ❌")
    main_logger.info(f"错误测试: {error_tests} 💥")
    main_logger.info(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    # 最终结论
    main_logger.info("\n" + "=" * 80)
    main_logger.info("🎯 最终结论")
    main_logger.info("=" * 80)
    
    if passed_tests == total_tests:
        main_logger.info("🎉 所有测试通过！基础训练功能完全正常。")
        return "ALL_PASSED"
    elif passed_tests > 0:
        main_logger.warning("⚠️  部分测试通过，基础功能部分正常。")
        main_logger.info("需要关注的问题:")
        
        # 收集所有失败和错误测试的建议
        all_recommendations = set()
        for result in results.values():
            if isinstance(result, TestResult) and result.status in ["FAILED", "ERROR"]:
                all_recommendations.update(result.recommendations)
        
        for i, rec in enumerate(list(all_recommendations)[:5], 1):  # 显示前5个建议
            main_logger.info(f"  {i}. {rec}")
        
        return "PARTIAL_PASSED"
    else:
        main_logger.error("❌ 所有测试失败，需要进一步调试。")
        
        # 收集所有错误类别
        error_categories = set()
        for result in results.values():
            if isinstance(result, TestResult) and result.error_category:
                error_categories.add(result.error_category)
        
        if error_categories:
            main_logger.error(f"主要错误类别: {', '.join(error_categories)}")
        
        return "ALL_FAILED"


def main():
    """增强版主函数，提供详细的测试报告"""
    # 创建带时间戳的日志文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"probe_test_{timestamp}.log"
    
    # 设置日志，同时输出到文件和控制台
    setup_logger("HMASD", log_dir='logs', log_file=log_filename, level=logging.INFO, console_level=logging.INFO)
    main_logger.info("🚀 开始增强版简化探针测试...")
    main_logger.info(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main_logger.info(f"日志文件: logs/{log_filename}")
    
    # 存储所有测试结果
    test_results = {}
    
    try:
        # 测试1: 价值函数测试
        main_logger.info("\n" + "="*60)
        main_logger.info("🧪 执行价值函数测试...")
        main_logger.info("="*60)
        value_result = test_simple_value_function()
        test_results['value_function'] = value_result
        
        # 测试2: 策略学习测试
        main_logger.info("\n" + "="*60)
        main_logger.info("🧪 执行策略学习测试...")
        main_logger.info("="*60)
        policy_result = test_simple_policy_learning()
        test_results['policy_learning'] = policy_result
        
        # 保存测试结果
        save_test_results(test_results)
        
        # 打印详细总结
        final_status = print_detailed_summary(test_results)
        
        # 返回兼容的布尔值（为了向后兼容）
        value_passed = isinstance(value_result, TestResult) and value_result.status == "PASSED"
        policy_passed = isinstance(policy_result, TestResult) and policy_result.status == "PASSED"
        
        return value_passed, policy_passed, test_results
        
    except Exception as e:
        main_logger.error(f"测试执行过程中发生严重错误: {e}")
        main_logger.error(f"错误堆栈: {traceback.format_exc()}")
        
        # 创建错误结果
        error_result = TestResult("测试执行")
        error_category, error_message = categorize_error(e)
        error_result.set_error(error_category, error_message, traceback.format_exc())
        test_results['execution_error'] = error_result
        
        # 保存错误结果
        save_test_results(test_results)
        
        return False, False, test_results


if __name__ == "__main__":
    main()
