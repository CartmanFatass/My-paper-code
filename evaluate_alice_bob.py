"""
Alice and Bob 环境的独立评估脚本

支持：
- 加载训练好的模型进行评估
- 生成详细的可视化分析
- 交互式评估模式
- 性能基准测试
"""

import os
import time
import numpy as np
import torch
import argparse
from datetime import datetime

from config_alice_bob import Config
from hmasd.agent_discrete import HMASDAgent
from envs.alice_and_bob_env import AliceAndBobEnv
from envs.alice_and_bob_adapter import AliceAndBobAdapter
from visualizers.alice_bob_visualizer import AliceAndBobVisualizer
from logger import init_multiproc_logging, get_logger, shutdown_logging

class RandomAgent:
    """随机策略智能体，用作基线对比"""
    
    def __init__(self, config, seed=None):
        self.config = config
        if seed is not None:
            np.random.seed(seed)
        
        # 模拟技能状态
        self.current_team_skill = 0
        self.current_agent_skills = [0, 0]
        self.skill_timer = 0
        self.skill_duration = 10
        
    def step(self, state, obs, step_count, deterministic=True, env_id=0):
        # 生成随机动作
        actions = np.random.randint(0, 5, size=self.config.n_agents)
        
        # 更新技能状态（模拟）
        skill_changed = False
        if self.skill_timer >= self.skill_duration:
            self.current_team_skill = np.random.randint(0, self.config.n_Z)
            self.current_agent_skills = [
                np.random.randint(0, self.config.n_z) 
                for _ in range(self.config.n_agents)
            ]
            self.skill_timer = 0
            skill_changed = True
        else:
            self.skill_timer += 1
        
        agent_info = {
            'team_skill': self.current_team_skill,
            'agent_skills': self.current_agent_skills.copy(),
            'skill_changed': skill_changed,
            'action_logprobs': np.zeros((self.config.n_agents,)),
            'log_probs': {
                'team_logprob': 0.0,
                'agent_logprobs': [0.0] * self.config.n_agents
            }
        }
        
        return actions, agent_info
    
    def reset_env_state(self, env_id):
        self.skill_timer = 0

def create_eval_environment(seed=42):
    """创建评估环境"""
    from gymnasium import spaces
    
    raw_env = AliceAndBobEnv()
    observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32)
    action_space = spaces.Discrete(5)
    agent_names = raw_env.agents
    
    eval_env = AliceAndBobAdapter(raw_env, agent_names, observation_space, action_space, seed=seed)
    return eval_env

def run_evaluation(agent, config, args):
    """运行完整评估"""
    eval_logger = get_logger("HMASD-Evaluation")
    
    # 创建结果保存目录
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.model_path and os.path.exists(args.model_path):
        model_name = os.path.splitext(os.path.basename(args.model_path))[0]
        save_dir = f"evaluation_results/{timestamp}_{model_name}"
    else:
        save_dir = f"evaluation_results/{timestamp}_random_agent"
    
    os.makedirs(save_dir, exist_ok=True)
    eval_logger.info(f"评估结果将保存到: {save_dir}")
    
    # 创建可视化器
    visualizer = AliceAndBobVisualizer(save_path=save_dir)
    
    # 创建环境
    eval_env = create_eval_environment(seed=args.seed)
    
    # 评估指标
    episode_rewards = []
    episode_lengths = []
    success_episodes = []
    skill_usage_stats = np.zeros((config.n_Z, config.n_z))
    detailed_results = []
    
    eval_logger.info(f"开始评估，运行 {args.n_episodes} 个episodes...")
    
    for episode in range(args.n_episodes):
        eval_logger.info(f"\n=== Episode {episode + 1}/{args.n_episodes} ===")
        
        # 重置环境和可视化器
        obs, info = eval_env.reset()
        state = info.get('state', np.zeros(config.state_dim))
        visualizer.next_episode()
        
        episode_reward = 0
        episode_length = 0
        success = False
        episode_skills = []
        episode_actions = []
        
        # 记录episode开始时间
        episode_start_time = time.time()
        
        while True:
            # 智能体选择动作
            actions, agent_info = agent.step(state, obs, episode_length, 
                                           deterministic=args.deterministic, env_id=0)
            
            # 记录技能和动作
            episode_skills.append({
                'step': episode_length,
                'team_skill': agent_info['team_skill'],
                'agent_skills': agent_info['agent_skills'].copy(),
                'skill_changed': agent_info.get('skill_changed', False)
            })
            episode_actions.append(actions.copy())
            
            # 记录技能使用统计
            team_skill = agent_info['team_skill']
            agent_skills = agent_info['agent_skills']
            for agent_skill in agent_skills:
                if 0 <= team_skill < config.n_Z and 0 <= agent_skill < config.n_z:
                    skill_usage_stats[team_skill, agent_skill] += 1
            
            # 执行动作
            next_obs, reward, done, truncated, info = eval_env.step(actions)
            next_state = info.get('state', np.zeros(config.state_dim))
            
            # 记录可视化
            visualizer.record_step(obs, actions, reward, agent_info, info)
            
            # 实时渲染（如果启用）
            if args.render:
                visualizer.render_current_state(obs, agent_info, info, show_skills=True)
                if args.interactive:
                    input("按回车键继续...")
                else:
                    time.sleep(0.1)
            
            # 更新状态
            state = next_state
            obs = next_obs
            episode_reward += reward
            episode_length += 1
            
            # 检查成功条件
            if reward >= 10.0:
                success = True
                eval_logger.info(f"Episode {episode + 1} 成功! 步数: {episode_length}, 奖励: {reward}")
            
            if done or truncated:
                break
        
        episode_duration = time.time() - episode_start_time
        
        # 记录episode结果
        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)
        success_episodes.append(1 if success else 0)
        
        # 保存详细结果
        episode_result = {
            'episode': episode + 1,
            'reward': episode_reward,
            'length': episode_length,
            'success': success,
            'duration': episode_duration,
            'skills': episode_skills,
            'actions': episode_actions
        }
        detailed_results.append(episode_result)
        
        # 保存episode分析图
        visualizer.save_episode_analysis(episode_reward, success)
        
        # 重置智能体状态
        agent.reset_env_state(0)
        
        eval_logger.info(f"Episode {episode + 1} 完成: 奖励={episode_reward:.2f}, "
                        f"长度={episode_length}, 成功={success}, 用时={episode_duration:.2f}s")
    
    # 关闭环境和可视化器
    eval_env.close()
    visualizer.close()
    
    # 计算最终统计
    eval_metrics = {
        'total_episodes': args.n_episodes,
        'avg_reward': np.mean(episode_rewards),
        'std_reward': np.std(episode_rewards),
        'avg_length': np.mean(episode_lengths),
        'std_length': np.std(episode_lengths),
        'success_rate': np.mean(success_episodes),
        'max_reward': np.max(episode_rewards),
        'min_reward': np.min(episode_rewards),
        'max_length': np.max(episode_lengths),
        'min_length': np.min(episode_lengths)
    }
    
    # 计算技能多样性
    if np.sum(skill_usage_stats) > 0:
        skill_dist = skill_usage_stats / np.sum(skill_usage_stats)
        skill_entropy = -np.sum(skill_dist * np.log(skill_dist + 1e-8))
        eval_metrics['skill_diversity'] = skill_entropy
        eval_metrics['skill_usage_stats'] = skill_usage_stats.tolist()
    else:
        eval_metrics['skill_diversity'] = 0.0
        eval_metrics['skill_usage_stats'] = skill_usage_stats.tolist()
    
    # 保存评估结果
    import json
    results_file = os.path.join(save_dir, "evaluation_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'config': {
                'model_path': args.model_path,
                'n_episodes': args.n_episodes,
                'deterministic': args.deterministic,
                'seed': args.seed
            },
            'metrics': eval_metrics,
            'detailed_results': detailed_results
        }, f, indent=2, ensure_ascii=False)
    
    eval_logger.info(f"评估结果已保存: {results_file}")
    
    # 打印最终结果
    print_evaluation_summary(eval_metrics, eval_logger)
    
    return eval_metrics

def print_evaluation_summary(metrics, logger):
    """打印评估摘要"""
    logger.info("\n" + "="*50)
    logger.info("评估摘要")
    logger.info("="*50)
    logger.info(f"总Episodes: {metrics['total_episodes']}")
    logger.info(f"平均奖励: {metrics['avg_reward']:.3f} ± {metrics['std_reward']:.3f}")
    logger.info(f"成功率: {metrics['success_rate']:.1%} ({int(metrics['success_rate'] * metrics['total_episodes'])}/{metrics['total_episodes']})")
    logger.info(f"平均长度: {metrics['avg_length']:.1f} ± {metrics['std_length']:.1f}")
    logger.info(f"奖励范围: [{metrics['min_reward']:.1f}, {metrics['max_reward']:.1f}]")
    logger.info(f"长度范围: [{metrics['min_length']}, {metrics['max_length']}]")
    logger.info(f"技能多样性: {metrics['skill_diversity']:.3f}")
    logger.info("="*50)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='评估 Alice and Bob 环境中的 HMASD 智能体')
    
    # 模型参数
    parser.add_argument('--model_path', type=str, default=None,
                       help='训练好的模型路径 (如果未提供将使用随机策略)')
    parser.add_argument('--device', type=str, default='auto', 
                       choices=['auto', 'cuda', 'cpu'],
                       help='计算设备')
    
    # 评估参数
    parser.add_argument('--n_episodes', type=int, default=50,
                       help='评估的episode数量')
    parser.add_argument('--deterministic', action='store_true',
                       help='使用确定性策略')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子')
    
    # 可视化参数
    parser.add_argument('--render', action='store_true',
                       help='实时渲染评估过程')
    parser.add_argument('--interactive', action='store_true',
                       help='交互式模式（需要按键继续）')
    parser.add_argument('--save_videos', action='store_true',
                       help='保存评估视频')
    
    # 日志参数
    parser.add_argument('--log_dir', type=str, default='logs/',
                       help='日志目录')
    parser.add_argument('--verbose', action='store_true',
                       help='详细输出')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 初始化日志
    init_multiproc_logging(log_dir=args.log_dir, log_file="alice_bob_eval.log")
    logger = get_logger("HMASD-Main-Eval")
    
    # 加载配置
    config = Config()
    
    # 设置设备
    if args.device == 'auto':
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    
    logger.info(f"使用设备: {device}")
    logger.info(f"评估配置: episodes={args.n_episodes}, deterministic={args.deterministic}")
    
    # 创建临时环境获取维度
    temp_env = create_eval_environment()
    config.update_env_dims(
        state_dim=temp_env.state_space.shape[0],
        obs_dim=temp_env.observation_space.shape[0],
        n_agents=temp_env.n_agents,
        action_dim=temp_env.action_space.n
    )
    temp_env.close()
    
    # 创建智能体
    if args.model_path and os.path.exists(args.model_path):
        logger.info(f"加载训练好的模型: {args.model_path}")
        try:
            agent = HMASDAgent(config, device=device)
            agent.load_model(args.model_path)
            logger.info("模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.info("回退到随机策略")
            agent = RandomAgent(config, seed=args.seed)
    else:
        if args.model_path:
            logger.warning(f"模型文件不存在: {args.model_path}")
        logger.info("使用随机策略进行评估")
        agent = RandomAgent(config, seed=args.seed)
    
    # 运行评估
    try:
        eval_metrics = run_evaluation(agent, config, args)
        logger.info("评估完成!")
        
    except KeyboardInterrupt:
        logger.info("评估被用户中断")
    except Exception as e:
        logger.error(f"评估过程中出现错误: {e}")
        raise
    finally:
        shutdown_logging()

if __name__ == "__main__":
    main()
