#!/usr/bin/env python3
"""
测试 train_multiproc_config_1.py 中的rollout训练流程

这个测试文件验证：
1. Rollout-based数据收集机制
2. Agent更新和缓冲区清空
3. 并行环境同步执行
4. On-policy训练流程的正确性
"""

import os
import sys
import time
import numpy as np
import torch
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
from logger import init_multiproc_logging, get_logger, shutdown_logging
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario2 import UAVCooperativeNetworkEnv
from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from stable_baselines3.common.vec_env import SubprocVecEnv

# 全局logger
main_logger = None

class TestConfig(Config):
    """测试专用配置 - 使用较小的参数进行快速测试"""
    
    # 减小训练参数以便快速测试
    num_envs = 4             # 使用4个并行环境
    rollout_length = 8       # 每个rollout只收集8步
    total_timesteps = 320    # 总共320步 (4envs * 8rollout * 10rollouts)
    eval_interval = 160      # 每160步评估一次
    eval_episodes = 2        # 评估2个episodes
    eval_rollout_threads = 2 # 评估使用2个线程
    
    # 缓冲区和批次大小
    buffer_size = 64         # 较小的缓冲区
    batch_size = 32          # 较小的批次大小
    high_level_batch_size = 32
    
    # 网络参数
    hidden_size = 32         # 较小的网络
    embedding_dim = 32
    
    # HMASD参数
    k = 4                    # 较短的技能间隔
    
    # 其他参数
    episode_length = 100     # 较短的episode长度

def make_test_env(rank=0, seed=0):
    """创建测试环境"""
    def _init():
        env_seed = seed + rank
        raw_env = UAVCooperativeNetworkEnv(
            n_uavs=3,           # 使用3个无人机
            n_users=10,         # 10个用户
            max_hops=2,         # 最大跳数2
            user_distribution='uniform',
            channel_model='free_space',  # 使用简单的信道模型
            render_mode=None,
            seed=env_seed
        )
        # 使用适配器包装环境
        env = ParallelToArrayAdapter(raw_env, seed=env_seed)
        return env
    return _init

class TrainingFlowMonitor:
    """训练流程监控器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置监控数据"""
        self.rollout_count = 0
        self.update_count = 0
        self.buffer_states = []  # 记录每次更新前后的缓冲区状态
        self.rollout_data = []   # 记录每个rollout的数据收集情况
        self.step_counts = []    # 记录每个rollout收集的步数
        self.env_sync_data = []  # 记录环境同步执行的数据
        
    def start_rollout(self, rollout_id):
        """开始一个新的rollout"""
        self.current_rollout = {
            'id': rollout_id,
            'start_time': time.time(),
            'steps_collected': 0,
            'env_steps': {},  # 每个环境的步数
            'env_rewards': {}, # 每个环境的奖励
        }
        
    def record_step(self, env_id, step_count, reward):
        """记录环境步数和奖励"""
        if 'env_steps' not in self.current_rollout:
            self.current_rollout['env_steps'] = {}
        if 'env_rewards' not in self.current_rollout:
            self.current_rollout['env_rewards'] = {}
            
        self.current_rollout['env_steps'][env_id] = step_count
        self.current_rollout['env_rewards'][env_id] = reward
        
    def end_rollout(self, buffer_size_before):
        """结束当前rollout"""
        self.current_rollout['end_time'] = time.time()
        self.current_rollout['duration'] = self.current_rollout['end_time'] - self.current_rollout['start_time']
        self.current_rollout['buffer_size_before'] = buffer_size_before
        
        self.rollout_data.append(self.current_rollout.copy())
        self.rollout_count += 1
        
    def record_update(self, buffer_size_before, buffer_size_after, update_info):
        """记录模型更新"""
        update_record = {
            'update_id': self.update_count,
            'buffer_size_before': buffer_size_before,
            'buffer_size_after': buffer_size_after,
            'buffer_cleared': buffer_size_after == 0,
            'update_info': update_info,
            'timestamp': time.time()
        }
        self.buffer_states.append(update_record)
        self.update_count += 1
        
    def check_env_synchronization(self):
        """检查环境是否同步执行"""
        if not self.rollout_data:
            return True, "没有rollout数据"
            
        sync_issues = []
        for rollout in self.rollout_data:
            if 'env_steps' in rollout:
                step_counts = list(rollout['env_steps'].values())
                if step_counts and len(set(step_counts)) > 1:
                    sync_issues.append(f"Rollout {rollout['id']}: 环境步数不同步 {step_counts}")
                    
        if sync_issues:
            return False, "; ".join(sync_issues)
        return True, "所有环境同步执行"
        
    def check_buffer_clearing(self):
        """检查缓冲区是否正确清空"""
        clearing_issues = []
        for update in self.buffer_states:
            if not update['buffer_cleared']:
                clearing_issues.append(f"更新 {update['update_id']}: 缓冲区未清空 (大小: {update['buffer_size_after']})")
                
        if clearing_issues:
            return False, "; ".join(clearing_issues)
        return True, "所有更新后缓冲区都正确清空"
        
    def generate_report(self):
        """生成测试报告"""
        report = []
        report.append("=== 训练流程测试报告 ===")
        report.append(f"总rollout数: {self.rollout_count}")
        report.append(f"总更新次数: {self.update_count}")
        
        # 检查环境同步
        sync_ok, sync_msg = self.check_env_synchronization()
        report.append(f"环境同步检查: {'✅ 通过' if sync_ok else '❌ 失败'} - {sync_msg}")
        
        # 检查缓冲区清空
        clear_ok, clear_msg = self.check_buffer_clearing()
        report.append(f"缓冲区清空检查: {'✅ 通过' if clear_ok else '❌ 失败'} - {clear_msg}")
        
        # Rollout详情
        if self.rollout_data:
            report.append("\n--- Rollout详情 ---")
            for rollout in self.rollout_data[:5]:  # 只显示前5个
                steps = rollout.get('env_steps', {})
                report.append(f"Rollout {rollout['id']}: 耗时 {rollout.get('duration', 0):.3f}s, "
                            f"环境步数 {list(steps.values()) if steps else '无数据'}")
                            
        # 更新详情
        if self.buffer_states:
            report.append("\n--- 更新详情 ---")
            for update in self.buffer_states[:5]:  # 只显示前5个
                report.append(f"更新 {update['update_id']}: 更新前缓冲区大小 {update['buffer_size_before']}, "
                            f"更新后大小 {update['buffer_size_after']}, "
                            f"清空状态 {'✅' if update['buffer_cleared'] else '❌'}")
                            
        return "\n".join(report)

def modified_train_function(vec_env, eval_vec_env, config, device, monitor):
    """修改后的训练函数，加入监控功能"""
    num_envs = vec_env.num_envs
    main_logger.info(f"开始测试训练流程，使用 {num_envs} 个并行环境...")
    
    # 获取环境维度
    state_dim = vec_env.get_attr('state_dim')[0]
    obs_shape = vec_env.observation_space.shape
    if len(obs_shape) == 3:
        obs_dim = obs_shape[2]
    else:
        obs_dim = vec_env.get_attr('obs_dim')[0]
    
    config.update_env_dims(state_dim, obs_dim)
    main_logger.info(f"环境维度: state_dim={state_dim}, obs_dim={obs_dim}")
    
    # 创建测试日志目录
    log_dir = f"test_logs/rollout_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建HMASD代理
    agent = HMASDAgent(config, log_dir=log_dir, device=device)
    
    # 训练变量
    total_steps = 0
    rollout_id = 0
    
    # 重置所有环境
    main_logger.info("重置并行环境...")
    results = vec_env.env_method('reset')
    observations = np.array([res[0] for res in results])
    initial_infos = [res[1] for res in results]
    states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in initial_infos])
    
    # 环境状态跟踪
    env_steps = np.zeros(num_envs, dtype=int)
    env_rewards = np.zeros(num_envs)
    env_skill_durations = np.zeros(num_envs, dtype=int)
    
    main_logger.info("开始训练循环...")
    
    # 主训练循环
    while total_steps < config.total_timesteps:
        # 开始新的rollout
        monitor.start_rollout(rollout_id)
        main_logger.info(f"\n--- 开始 Rollout {rollout_id} ---")
        
        # 记录更新前的缓冲区大小
        buffer_size_before = len(agent.low_level_buffer)
        main_logger.info(f"Rollout开始前缓冲区大小: {buffer_size_before}")
        
        # 收集rollout数据
        rollout_steps = 0
        for rollout_step in range(config.rollout_length):
            # 代理为所有环境选择动作
            all_actions_list = []
            all_agent_infos_list = []
            
            for i in range(num_envs):
                actions, agent_info = agent.step(states[i], observations[i], env_steps[i], deterministic=False, env_id=i)
                all_actions_list.append(actions)
                all_agent_infos_list.append(agent_info)
            
            actions_array = np.array(all_actions_list)
            
            # 执行动作
            next_observations, rewards, dones, infos = vec_env.step(actions_array)
            next_states = np.array([info.get('next_state', np.zeros(state_dim)) for info in infos])
            
            # 存储经验到缓冲区
            for i in range(num_envs):
                current_agent_info = all_agent_infos_list[i]
                skill_timer_value = env_skill_durations[i]
                
                agent.store_transition(
                    states[i], next_states[i], observations[i], next_observations[i],
                    actions_array[i], rewards[i], dones[i], current_agent_info['team_skill'],
                    current_agent_info['agent_skills'], current_agent_info['action_logprobs'],
                    log_probs=current_agent_info['log_probs'],
                    skill_timer_for_env=skill_timer_value,
                    env_id=i
                )
                
                # 更新状态跟踪
                env_steps[i] += 1
                env_rewards[i] += rewards[i]
                
                # 记录到监控器
                monitor.record_step(i, env_steps[i], env_rewards[i])
                
                # 更新技能持续时间
                if dones[i]:
                    env_skill_durations[i] = 0
                    main_logger.info(f"环境 {i} 完成episode，步数: {env_steps[i]}, 奖励: {env_rewards[i]:.2f}")
                    env_steps[i] = 0
                    env_rewards[i] = 0
                elif skill_timer_value == config.k - 1:
                    env_skill_durations[i] = 0
                elif current_agent_info['skill_changed']:
                    env_skill_durations[i] = 0
                else:
                    env_skill_durations[i] += 1
            
            # 更新状态和观测
            states = next_states
            observations = next_observations
            total_steps += num_envs
            rollout_steps += 1
            
            # 如果达到总步数限制，跳出rollout收集循环
            if total_steps >= config.total_timesteps:
                break
        
        # 结束rollout
        buffer_size_after_collection = len(agent.low_level_buffer)
        monitor.end_rollout(buffer_size_before)
        
        main_logger.info(f"Rollout {rollout_id} 完成: 收集了 {rollout_steps} 步, "
                        f"缓冲区大小: {buffer_size_before} -> {buffer_size_after_collection}")
        
        # 进行模型更新
        if len(agent.low_level_buffer) >= agent.config.batch_size:
            try:
                main_logger.info(f"开始模型更新，缓冲区大小: {len(agent.low_level_buffer)}")
                update_info = agent.update()
                buffer_size_after_update = len(agent.low_level_buffer)
                
                main_logger.info(f"模型更新前缓冲区大小: {buffer_size_after_collection}")
                
                # 清空缓冲区 (严格on-policy)
                agent.clear_buffers()
                buffer_size_after_clear = len(agent.low_level_buffer)
                
                main_logger.info(f"缓冲区清空后大小: {buffer_size_after_clear}")
                
                # 记录到监控器
                monitor.record_update(buffer_size_after_collection, buffer_size_after_clear, update_info)
                
                main_logger.info(f"✅ 更新完成: 高层损失 {update_info['coordinator_loss']:.4f}, "
                                f"低层损失 {update_info['discoverer_loss']:.4f}, "
                                f"判别器损失 {update_info['discriminator_loss']:.4f}")
                
            except Exception as e:
                main_logger.error(f"❌ 更新错误: {e}")
        else:
            main_logger.warning(f"⚠️ 缓冲区数据不足，跳过更新。当前大小: {len(agent.low_level_buffer)}, 需要: {agent.config.batch_size}")
        
        rollout_id += 1
        
        # 简化的评估逻辑
        if total_steps >= config.eval_interval and rollout_id % 2 == 0:  # 每2个rollout评估一次
            main_logger.info(f"执行简化评估...")
            try:
                # 简单运行几步评估
                eval_results = vec_env.env_method('reset')
                eval_obs = np.array([res[0] for res in eval_results])
                eval_infos = [res[1] for res in eval_results]
                eval_states = np.array([info.get('state', np.zeros(agent.config.state_dim)) for info in eval_infos])
                
                # 运行几步评估
                for _ in range(5):
                    eval_actions = []
                    for i in range(num_envs):
                        actions, _ = agent.step(eval_states[i], eval_obs[i], 0, deterministic=True, env_id=i)
                        eval_actions.append(actions)
                    
                    eval_actions_array = np.array(eval_actions)
                    eval_obs, eval_rewards, eval_dones, eval_infos = vec_env.step(eval_actions_array)
                    eval_states = np.array([info.get('next_state', np.zeros(state_dim)) for info in eval_infos])
                    
                    if np.any(eval_dones):
                        break
                
                main_logger.info("✅ 评估完成")
            except Exception as e:
                main_logger.error(f"❌ 评估错误: {e}")
    
    main_logger.info(f"训练测试完成! 总步数: {total_steps}, 总rollouts: {rollout_id}")
    return agent, monitor

def run_test():
    """运行测试"""
    global main_logger
    
    # 初始化日志系统
    os.makedirs('test_logs', exist_ok=True)
    init_multiproc_logging(
        log_dir='test_logs', 
        log_file=f'rollout_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        file_level=logging.INFO,
        console_level=logging.INFO
    )
    main_logger = get_logger("RolloutTest")
    
    try:
        main_logger.info("=== 开始Rollout训练流程测试 ===")
        
        # 创建测试配置
        config = TestConfig()
        device = torch.device('cpu')  # 测试时使用CPU
        
        # 创建监控器
        monitor = TrainingFlowMonitor()
        
        # 创建测试环境
        base_seed = int(time.time()) % 10000
        main_logger.info(f"使用种子: {base_seed}")
        
        train_env_fns = [make_test_env(rank=i, seed=base_seed) for i in range(config.num_envs)]
        eval_env_fns = [make_test_env(rank=i, seed=base_seed + config.num_envs) for i in range(config.eval_rollout_threads)]
        
        # 创建向量化环境
        main_logger.info("创建测试环境...")
        train_vec_env = SubprocVecEnv(train_env_fns, start_method='spawn')
        eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')
        
        # 更新配置中的智能体数量
        try:
            n_agents_from_env = train_vec_env.get_attr('n_uavs')[0]
            config.n_agents = n_agents_from_env
            main_logger.info(f"从环境获取智能体数量: {config.n_agents}")
        except Exception as e:
            main_logger.warning(f"无法从环境获取n_uavs: {e}, 使用默认值: {config.n_agents}")
        
        # 运行测试训练
        agent, monitor = modified_train_function(train_vec_env, eval_vec_env, config, device, monitor)
        
        # 生成测试报告
        report = monitor.generate_report()
        main_logger.info(f"\n{report}")
        
        # 保存报告到文件
        report_file = f"test_logs/rollout_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        main_logger.info(f"测试报告已保存到: {report_file}")
        
        # 验证测试结果
        sync_ok, _ = monitor.check_env_synchronization()
        clear_ok, _ = monitor.check_buffer_clearing()
        
        if sync_ok and clear_ok and monitor.update_count > 0:
            main_logger.info("🎉 所有测试通过！训练流程工作正常。")
            return True
        else:
            main_logger.error("❌ 测试失败！存在问题需要修复。")
            return False
            
    except Exception as e:
        main_logger.error(f"测试执行错误: {e}", exc_info=True)
        return False
    finally:
        try:
            train_vec_env.close()
            eval_vec_env.close()
        except:
            pass
        shutdown_logging()

if __name__ == "__main__":
    import multiprocessing as mp
    mp.set_start_method('spawn', force=True)
    
    print("开始Rollout训练流程测试...")
    success = run_test()
    
    if success:
        print("✅ 测试成功完成")
        sys.exit(0)
    else:
        print("❌ 测试失败")
        sys.exit(1)
