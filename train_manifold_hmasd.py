"""
基于流形的目标导向HMASD训练脚本
使用VAE学习的状态流形和HER进行目标导向强化学习
"""

import numpy as np
import torch
import os
import sys
import argparse
from datetime import datetime
import time
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_1 import Config
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from manifold_hmasd.agent import ManifoldHMASDAgent
from logger import main_logger

class ManifoldHMASDTrainer:
    """
    基于流形的HMASD训练器
    """
    def __init__(self, config, env, agent, log_dir):
        self.config = config
        self.env = env
        self.agent = agent
        self.log_dir = log_dir
        
        # 训练统计
        self.episode_rewards = []
        self.episode_success_rates = []
        self.episode_lengths = []
        self.evaluation_results = []
        
        # 最佳性能记录
        self.best_success_rate = 0.0
        self.best_avg_reward = -float('inf')
        
        main_logger.info("ManifoldHMASD训练器初始化完成")
    
    def train(self, total_episodes=1000, eval_interval=50, save_interval=100):
        """
        主训练循环
        
        参数:
            total_episodes: 总训练episode数
            eval_interval: 评估间隔
            save_interval: 模型保存间隔
        """
        main_logger.info(f"开始训练，总episodes: {total_episodes}")
        
        start_time = time.time()
        
        for episode in range(total_episodes):
            # 训练一个episode
            episode_reward, episode_length, episode_success = self._train_episode(episode)
            
            # 记录统计信息
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            self.episode_success_rates.append(episode_success)
            
            # 更新目标难度
            recent_success_rate = np.mean(self.episode_success_rates[-10:])
            self.agent.goal_generator.update_difficulty(recent_success_rate, episode)
            
            # 记录训练进度
            if (episode + 1) % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_success_rate = np.mean(self.episode_success_rates[-10:])
                avg_length = np.mean(self.episode_lengths[-10:])
                
                main_logger.info(f"Episode {episode + 1}/{total_episodes}: "
                               f"平均奖励={avg_reward:.3f}, "
                               f"成功率={avg_success_rate:.3f}, "
                               f"平均长度={avg_length:.1f}")
            
            # 定期评估
            if (episode + 1) % eval_interval == 0:
                eval_results = self._evaluate(n_episodes=5)
                self.evaluation_results.append({
                    'episode': episode + 1,
                    'results': eval_results
                })
                
                # 检查是否为最佳性能
                if eval_results['success_rate'] > self.best_success_rate:
                    self.best_success_rate = eval_results['success_rate']
                    self._save_best_model('best_success_rate')
                
                if eval_results['avg_reward'] > self.best_avg_reward:
                    self.best_avg_reward = eval_results['avg_reward']
                    self._save_best_model('best_reward')
            
            # 定期保存模型
            if (episode + 1) % save_interval == 0:
                self._save_checkpoint(episode + 1)
            
            # 更新智能体
            if len(self.agent.replay_buffer) >= self.config.batch_size:
                update_info = self.agent.update()
                
                # 记录更新信息到TensorBoard
                if update_info:
                    self.agent.writer.add_scalar('Training/EpisodeReward', episode_reward, episode)
                    self.agent.writer.add_scalar('Training/EpisodeLength', episode_length, episode)
                    self.agent.writer.add_scalar('Training/EpisodeSuccess', episode_success, episode)
        
        # 训练完成
        total_time = time.time() - start_time
        main_logger.info(f"训练完成！总用时: {total_time:.1f}秒")
        
        # 保存最终模型和训练记录
        self._save_final_results()
    
    def _train_episode(self, episode):
        """
        训练一个episode
        
        参数:
            episode: episode编号
            
        返回:
            episode_reward: episode总奖励
            episode_length: episode长度
            episode_success: 是否成功
        """
        observations, infos = self.env.reset()
        
        episode_reward = 0
        episode_length = 0
        episode_success = False
        
        for step in range(self.config.episode_length):
            # 获取全局状态
            global_state = self.env.get_global_state()
            
            # 智能体选择动作
            actions, action_info = self.agent.step(
                observations=observations,
                global_state=global_state,
                env_id=0,  # 单环境训练
                episode_step=step
            )
            
            # 环境执行动作
            next_observations, rewards, dones, truncated, infos = self.env.step(actions)
            
            # 获取奖励
            env_reward = rewards[list(rewards.keys())[0]] if isinstance(rewards, dict) else rewards
            episode_reward += env_reward
            
            # 存储经验
            next_global_state = self.env.get_global_state()
            self.agent.store_transition(
                state=global_state,
                next_state=next_global_state,
                observations=observations,
                actions=actions,
                reward=env_reward,
                done=any(dones.values()) if isinstance(dones, dict) else dones,
                info=action_info,
                env_id=0
            )
            
            # 更新状态
            observations = next_observations
            episode_length = step + 1
            
            # 检查是否结束
            if any(dones.values()) if isinstance(dones, dict) else dones:
                break
        
        # 判断是否成功（基于环境奖励）
        # 这里使用简化的成功标准
        if hasattr(self.env, 'reward_info'):
            episode_success = self.env.reward_info.get('target_coverage_achieved', False)
        else:
            # 如果没有明确的成功标准，使用奖励阈值
            episode_success = episode_reward > self.config.episode_length * 0.5
        
        return episode_reward, episode_length, episode_success
    
    def _evaluate(self, n_episodes=5, deterministic=True):
        """
        评估当前策略
        
        参数:
            n_episodes: 评估episode数
            deterministic: 是否使用确定性策略
            
        返回:
            eval_results: 评估结果字典
        """
        main_logger.info(f"开始评估，共{n_episodes}个episodes")
        
        eval_rewards = []
        eval_success_rates = []
        eval_lengths = []
        
        for eval_ep in range(n_episodes):
            observations, infos = self.env.reset()
            
            eval_reward = 0
            eval_length = 0
            eval_success = False
            
            for step in range(self.config.episode_length):
                # 获取全局状态
                global_state = self.env.get_global_state()
                
                # 智能体选择动作（确定性）
                actions, _ = self.agent.step(
                    observations=observations,
                    global_state=global_state,
                    env_id=eval_ep,  # 使用不同的环境ID避免冲突
                    episode_step=step
                )
                
                # 如果需要确定性策略，重新选择动作
                if deterministic:
                    current_goal = self.agent.current_goals.get(eval_ep)
                    if current_goal is not None:
                        actions, _ = self.agent._select_actions(observations, current_goal, deterministic=True)
                
                # 环境执行动作
                next_observations, rewards, dones, truncated, infos = self.env.step(actions)
                
                # 累计奖励
                env_reward = rewards[list(rewards.keys())[0]] if isinstance(rewards, dict) else rewards
                eval_reward += env_reward
                
                # 更新状态
                observations = next_observations
                eval_length = step + 1
                
                # 检查是否结束
                if any(dones.values()) if isinstance(dones, dict) else dones:
                    break
            
            # 判断是否成功
            if hasattr(self.env, 'reward_info'):
                eval_success = self.env.reward_info.get('target_coverage_achieved', False)
            else:
                eval_success = eval_reward > self.config.episode_length * 0.5
            
            eval_rewards.append(eval_reward)
            eval_success_rates.append(eval_success)
            eval_lengths.append(eval_length)
            
            # 清理评估环境的目标
            if eval_ep in self.agent.current_goals:
                del self.agent.current_goals[eval_ep]
            if eval_ep in self.agent.episode_starts:
                del self.agent.episode_starts[eval_ep]
        
        # 计算评估结果
        eval_results = {
            'avg_reward': np.mean(eval_rewards),
            'std_reward': np.std(eval_rewards),
            'success_rate': np.mean(eval_success_rates),
            'avg_length': np.mean(eval_lengths),
            'all_rewards': eval_rewards,
            'all_success': eval_success_rates
        }
        
        main_logger.info(f"评估完成: 平均奖励={eval_results['avg_reward']:.3f}, "
                        f"成功率={eval_results['success_rate']:.3f}")
        
        # 记录到TensorBoard
        step = len(self.episode_rewards)
        self.agent.writer.add_scalar('Evaluation/AvgReward', eval_results['avg_reward'], step)
        self.agent.writer.add_scalar('Evaluation/SuccessRate', eval_results['success_rate'], step)
        self.agent.writer.add_scalar('Evaluation/AvgLength', eval_results['avg_length'], step)
        
        return eval_results
    
    def _save_best_model(self, criteria):
        """保存最佳模型"""
        model_path = os.path.join(self.log_dir, f'best_model_{criteria}.pth')
        self.agent.save_model(model_path)
        main_logger.info(f"最佳模型已保存: {model_path} (标准: {criteria})")
    
    def _save_checkpoint(self, episode):
        """保存检查点"""
        checkpoint_dir = os.path.join(self.log_dir, 'checkpoints')
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        model_path = os.path.join(checkpoint_dir, f'checkpoint_episode_{episode}.pth')
        self.agent.save_model(model_path)
        
        # 保存训练统计
        stats_path = os.path.join(checkpoint_dir, f'training_stats_episode_{episode}.json')
        training_stats = {
            'episode': episode,
            'episode_rewards': self.episode_rewards,
            'episode_success_rates': self.episode_success_rates,
            'episode_lengths': self.episode_lengths,
            'evaluation_results': self.evaluation_results,
            'agent_stats': self.agent.get_statistics()
        }
        
        with open(stats_path, 'w') as f:
            json.dump(training_stats, f, indent=2)
        
        main_logger.info(f"检查点已保存: episode {episode}")
    
    def _save_final_results(self):
        """保存最终训练结果"""
        # 保存最终模型
        final_model_path = os.path.join(self.log_dir, 'final_model.pth')
        self.agent.save_model(final_model_path)
        
        # 保存完整训练记录
        final_stats = {
            'total_episodes': len(self.episode_rewards),
            'episode_rewards': self.episode_rewards,
            'episode_success_rates': self.episode_success_rates,
            'episode_lengths': self.episode_lengths,
            'evaluation_results': self.evaluation_results,
            'best_success_rate': self.best_success_rate,
            'best_avg_reward': self.best_avg_reward,
            'final_agent_stats': self.agent.get_statistics()
        }
        
        results_path = os.path.join(self.log_dir, 'final_training_results.json')
        with open(results_path, 'w') as f:
            json.dump(final_stats, f, indent=2)
        
        main_logger.info(f"最终训练结果已保存: {results_path}")
        
        # 生成训练总结
        self._generate_training_summary()
    
    def _generate_training_summary(self):
        """生成训练总结"""
        summary = {
            'training_config': {
                'total_episodes': len(self.episode_rewards),
                'environment': 'UAVForcedRelayEnv',
                'algorithm': 'ManifoldHMASD'
            },
            'performance_metrics': {
                'final_avg_reward': np.mean(self.episode_rewards[-50:]) if len(self.episode_rewards) >= 50 else np.mean(self.episode_rewards),
                'final_success_rate': np.mean(self.episode_success_rates[-50:]) if len(self.episode_success_rates) >= 50 else np.mean(self.episode_success_rates),
                'best_success_rate': self.best_success_rate,
                'best_avg_reward': self.best_avg_reward
            },
            'training_stability': {
                'reward_std': np.std(self.episode_rewards),
                'success_rate_std': np.std(self.episode_success_rates)
            }
        }
        
        summary_path = os.path.join(self.log_dir, 'training_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # 打印训练总结
        main_logger.info("=" * 60)
        main_logger.info("训练总结")
        main_logger.info("=" * 60)
        main_logger.info(f"总episodes: {summary['training_config']['total_episodes']}")
        main_logger.info(f"最终平均奖励: {summary['performance_metrics']['final_avg_reward']:.3f}")
        main_logger.info(f"最终成功率: {summary['performance_metrics']['final_success_rate']:.3f}")
        main_logger.info(f"最佳成功率: {summary['performance_metrics']['best_success_rate']:.3f}")
        main_logger.info(f"最佳平均奖励: {summary['performance_metrics']['best_avg_reward']:.3f}")
        main_logger.info("=" * 60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='基于流形的目标导向HMASD训练')
    parser.add_argument('--vae_model_path', type=str, required=True, help='VAE模型路径')
    parser.add_argument('--total_episodes', type=int, default=1000, help='总训练episodes')
    parser.add_argument('--eval_interval', type=int, default=50, help='评估间隔')
    parser.add_argument('--save_interval', type=int, default=100, help='保存间隔')
    parser.add_argument('--n_uavs', type=int, default=12, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=80, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2500, help='区域大小')
    parser.add_argument('--log_dir', type=str, default='logs/manifold_hmasd', help='日志目录')
    parser.add_argument('--device', type=str, default='auto', help='设备 (auto/cpu/cuda)')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--render', action='store_true', help='是否渲染')
    
    args = parser.parse_args()
    
    # 设置随机种子
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 设置设备
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    main_logger.info(f"使用设备: {device}")
    
    # 创建时间戳日志目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = f"{args.log_dir}_{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    
    # 保存运行参数
    with open(os.path.join(log_dir, 'run_args.json'), 'w') as f:
        json.dump(vars(args), f, indent=2)
    
    # 创建环境
    main_logger.info("创建环境...")
    env = UAVForcedRelayEnv(
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        area_size=args.area_size,
        max_steps=1500,
        render_mode='human' if args.render else None,
        seed=args.seed
    )
    
    # 初始化环境获取维度信息
    observations, infos = env.reset()
    global_state = env.get_global_state()
    
    # 创建配置
    config = Config()
    config.update_env_dims(
        state_dim=global_state.shape[0],
        obs_dim=observations[list(observations.keys())[0]].shape[0] if isinstance(observations, dict) else observations[0].shape[0]
    )
    
    main_logger.info(f"环境维度: state_dim={config.state_dim}, obs_dim={config.obs_dim}")
    
    # 创建智能体
    main_logger.info("创建ManifoldHMASD智能体...")
    agent = ManifoldHMASDAgent(
        config=config,
        vae_model_path=args.vae_model_path,
        log_dir=log_dir,
        device=device
    )
    
    # 创建训练器
    trainer = ManifoldHMASDTrainer(
        config=config,
        env=env,
        agent=agent,
        log_dir=log_dir
    )
    
    # 开始训练
    main_logger.info("开始训练...")
    trainer.train(
        total_episodes=args.total_episodes,
        eval_interval=args.eval_interval,
        save_interval=args.save_interval
    )
    
    # 关闭环境
    env.close()
    
    main_logger.info("训练完成！")

if __name__ == "__main__":
    main()
