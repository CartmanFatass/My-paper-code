"""
政策rollout和数据增强脚本
从训练好的RL智能体中运行rollout，收集高质量状态用于数据增强
"""

import numpy as np
import torch
import os
import sys
import argparse
from datetime import datetime
import json
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_1 import Config
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from manifold_hmasd.agent import ManifoldHMASDAgent
from hmasd.logging import main_logger

class PolicyRolloutCollector:
    """
    从训练好的策略中进行rollout并收集高质量状态
    """
    
    def __init__(self, agent_path, vae_path, env_config, quality_threshold=0.6):
        """
        初始化收集器
        
        参数:
            agent_path: 训练好的智能体模型路径
            vae_path: VAE模型路径
            env_config: 环境配置
            quality_threshold: 质量阈值（episode平均奖励）
        """
        self.agent_path = agent_path
        self.vae_path = vae_path
        self.env_config = env_config
        self.quality_threshold = quality_threshold
        
        # 收集的数据
        self.collected_states = []
        self.collected_rewards = []
        self.episode_rewards = []
        self.quality_episodes = 0
        
        main_logger.info(f"PolicyRolloutCollector初始化，质量阈值: {quality_threshold}")
    
    def setup_environment(self):
        """设置环境"""
        self.env = UAVForcedRelayEnv(
            n_uavs=self.env_config['n_uavs'],
            n_users=self.env_config['n_users'],
            area_size=self.env_config['area_size'],
            max_steps=1500,
            render_mode=None,
            seed=self.env_config.get('seed', 42)
        )
        
        # 初始化环境以获取维度信息
        observations, infos = self.env.reset()
        global_state = self.env.get_global_state()
        
        # 创建配置
        config = Config()
        config.update_env_dims(
            state_dim=global_state.shape[0],
            obs_dim=observations[list(observations.keys())[0]].shape[0] if isinstance(observations, dict) else observations[0].shape[0]
        )
        
        return config
    
    def load_agent(self, config):
        """加载训练好的智能体"""
        main_logger.info(f"加载智能体: {self.agent_path}")
        
        # 创建智能体
        self.agent = ManifoldHMASDAgent(
            config=config,
            vae_model_path=self.vae_path,
            log_dir='temp_rollout_log',  # 临时日志目录
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        )
        
        # 为了兼容新版PyTorch的安全加载机制，添加Config类到安全全局列表
        import torch.serialization
        torch.serialization.add_safe_globals([Config])
        main_logger.debug("已将Config类添加到PyTorch安全全局列表")
        
        # 直接尝试加载模型，不进行类型检测
        try:
            model_state = torch.load(self.agent_path)
            self.agent.policy.load_state_dict(model_state)
            main_logger.info("模型权重加载成功")
        except Exception as e:
            main_logger.error(f"加载模型权重时发生错误: {e}")
            raise
        
        # 设置为评估模式
        self.agent.policy.eval()
        
        main_logger.info("智能体加载成功")
    
    def rollout_episode(self, episode_id, deterministic=True):
        """
        运行一个episode
        
        参数:
            episode_id: episode ID
            deterministic: 是否使用确定性策略
            
        返回:
            episode_states: episode中的所有状态
            episode_rewards: episode中的所有奖励
            episode_total_reward: episode总奖励
        """
        observations, infos = self.env.reset()
        
        episode_states = []
        episode_rewards = []
        episode_total_reward = 0
        
        for step in range(1500):  # 最大步数
            # 获取全局状态
            global_state = self.env.get_global_state()
            episode_states.append(global_state.copy())
            
            # 智能体选择动作
            actions, action_info = self.agent.step(
                observations=observations,
                global_state=global_state,
                env_id=episode_id,
                episode_step=step
            )
            
            # 如果需要确定性策略，重新选择动作
            if deterministic:
                current_goal = self.agent.current_goals.get(episode_id)
                if current_goal is not None:
                    actions, _ = self.agent._select_actions(observations, current_goal, deterministic=True)
            
            # 执行动作
            next_observations, rewards, dones, truncated, infos = self.env.step(actions)
            
            # 获取奖励
            step_reward = rewards[list(rewards.keys())[0]] if isinstance(rewards, dict) else rewards
            episode_rewards.append(step_reward)
            episode_total_reward += step_reward
            
            # 更新观测
            observations = next_observations
            
            # 检查是否结束
            if any(dones.values()) if isinstance(dones, dict) else dones:
                break
        
        # 清理智能体的episode状态
        if episode_id in self.agent.current_goals:
            del self.agent.current_goals[episode_id]
        if episode_id in self.agent.episode_starts:
            del self.agent.episode_starts[episode_id]
        
        return episode_states, episode_rewards, episode_total_reward
    
    def collect_data(self, n_episodes=50, save_all_states=False):
        """
        收集多个episode的数据
        
        参数:
            n_episodes: rollout的episode数量
            save_all_states: 是否保存所有状态（默认只保存高质量episode的状态）
            
        返回:
            summary: 收集统计信息
        """
        main_logger.info(f"开始数据收集，共{n_episodes}个episodes")
        
        for episode in tqdm(range(n_episodes), desc="Rollout Episodes"):
            try:
                episode_states, episode_rewards, episode_total_reward = self.rollout_episode(episode)
                
                # 计算episode平均奖励
                avg_reward = episode_total_reward / len(episode_rewards) if episode_rewards else 0
                self.episode_rewards.append(episode_total_reward)
                
                # 判断是否为高质量episode
                is_quality_episode = avg_reward >= self.quality_threshold
                
                if is_quality_episode or save_all_states:
                    # 保存高质量状态
                    for i, (state, reward) in enumerate(zip(episode_states, episode_rewards)):
                        # 可以添加额外的状态级别过滤条件
                        if reward >= self.quality_threshold * 0.8:  # 状态级别的阈值稍低一些
                            self.collected_states.append(state)
                            self.collected_rewards.append(reward)
                    
                    if is_quality_episode:
                        self.quality_episodes += 1
                
                # 记录进度
                if (episode + 1) % 10 == 0:
                    recent_avg_reward = np.mean(self.episode_rewards[-10:])
                    main_logger.info(f"Episode {episode + 1}/{n_episodes}: "
                                   f"平均奖励={recent_avg_reward:.3f}, "
                                   f"质量episodes={self.quality_episodes}, "
                                   f"收集状态数={len(self.collected_states)}")
            
            except Exception as e:
                main_logger.warning(f"Episode {episode}执行失败: {e}")
                continue
        
        # 计算统计信息
        summary = {
            'total_episodes': n_episodes,
            'quality_episodes': self.quality_episodes,
            'quality_rate': self.quality_episodes / n_episodes,
            'total_states_collected': len(self.collected_states),
            'avg_states_per_quality_episode': len(self.collected_states) / max(self.quality_episodes, 1),
            'avg_episode_reward': np.mean(self.episode_rewards),
            'std_episode_reward': np.std(self.episode_rewards),
            'quality_threshold': self.quality_threshold
        }
        
        main_logger.info(f"数据收集完成: {summary}")
        return summary
    
    def save_collected_data(self, save_dir):
        """
        保存收集的数据
        
        参数:
            save_dir: 保存目录
            
        返回:
            save_info: 保存信息
        """
        os.makedirs(save_dir, exist_ok=True)
        
        if len(self.collected_states) == 0:
            main_logger.warning("没有收集到任何状态数据")
            return None
        
        # 保存新收集的好状态
        new_states_array = np.array(self.collected_states)
        new_states_path = os.path.join(save_dir, 'new_good_states.npy')
        np.save(new_states_path, new_states_array)
        
        # 保存对应的奖励
        new_rewards_array = np.array(self.collected_rewards)
        new_rewards_path = os.path.join(save_dir, 'new_good_states_rewards.npy')
        np.save(new_rewards_path, new_rewards_array)
        
        # 保存episode奖励
        episode_rewards_array = np.array(self.episode_rewards)
        episode_rewards_path = os.path.join(save_dir, 'rollout_episode_rewards.npy')
        np.save(episode_rewards_path, episode_rewards_array)
        
        main_logger.info(f"新数据已保存到 {save_dir}")
        main_logger.info(f"新状态数据形状: {new_states_array.shape}")
        main_logger.info(f"新状态奖励范围: [{new_rewards_array.min():.3f}, {new_rewards_array.max():.3f}]")
        
        save_info = {
            'new_states_path': new_states_path,
            'new_rewards_path': new_rewards_path,
            'episode_rewards_path': episode_rewards_path,
            'n_new_states': len(new_states_array),
            'state_dim': new_states_array.shape[1] if len(new_states_array) > 0 else 0
        }
        
        return save_info
    
    def run(self, n_episodes=50, save_dir=None, save_all_states=False):
        """
        运行完整的rollout和收集流程
        
        参数:
            n_episodes: rollout的episode数量
            save_dir: 保存目录
            save_all_states: 是否保存所有状态
            
        返回:
            save_info: 保存信息
            summary: 收集统计信息
        """
        # 设置环境
        config = self.setup_environment()
        
        # 加载智能体
        self.load_agent(config)
        
        # 收集数据
        summary = self.collect_data(n_episodes, save_all_states)
        
        # 保存数据
        save_info = None
        if save_dir:
            save_info = self.save_collected_data(save_dir)
        
        # 清理
        self.env.close()
        
        return save_info, summary

def merge_datasets(original_data_dir, new_data_dir, output_dir):
    """
    合并原始数据集和新收集的数据集
    
    参数:
        original_data_dir: 原始数据目录
        new_data_dir: 新数据目录
        output_dir: 输出目录
        
    返回:
        merged_info: 合并信息
    """
    main_logger.info(f"合并数据集: {original_data_dir} + {new_data_dir} -> {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载原始数据
    original_states_path = os.path.join(original_data_dir, 'good_states.npy')
    original_rewards_path = os.path.join(original_data_dir, 'good_states_rewards.npy')
    
    if not os.path.exists(original_states_path):
        raise FileNotFoundError(f"原始状态文件不存在: {original_states_path}")
    
    original_states = np.load(original_states_path)
    original_rewards = np.load(original_rewards_path) if os.path.exists(original_rewards_path) else np.zeros(len(original_states))
    
    # 加载新数据
    new_states_path = os.path.join(new_data_dir, 'new_good_states.npy')
    new_rewards_path = os.path.join(new_data_dir, 'new_good_states_rewards.npy')
    
    if not os.path.exists(new_states_path):
        main_logger.warning(f"新状态文件不存在: {new_states_path}，跳过合并")
        # 直接复制原始数据
        merged_states = original_states
        merged_rewards = original_rewards
    else:
        new_states = np.load(new_states_path)
        new_rewards = np.load(new_rewards_path) if os.path.exists(new_rewards_path) else np.zeros(len(new_states))
        
        # 合并数据
        merged_states = np.concatenate([original_states, new_states], axis=0)
        merged_rewards = np.concatenate([original_rewards, new_rewards], axis=0)
    
    # 保存合并后的数据
    merged_states_path = os.path.join(output_dir, 'good_states.npy')
    merged_rewards_path = os.path.join(output_dir, 'good_states_rewards.npy')
    
    np.save(merged_states_path, merged_states)
    np.save(merged_rewards_path, merged_rewards)
    
    # 保存合并信息
    merge_info = {
        'original_data_dir': original_data_dir,
        'new_data_dir': new_data_dir,
        'output_dir': output_dir,
        'original_size': len(original_states),
        'new_size': len(new_states) if 'new_states' in locals() else 0,
        'merged_size': len(merged_states),
        'expansion_ratio': len(merged_states) / len(original_states)
    }
    
    merge_info_path = os.path.join(output_dir, 'merge_info.json')
    with open(merge_info_path, 'w') as f:
        json.dump(merge_info, f, indent=2)
    
    main_logger.info(f"数据集合并完成: {merge_info}")
    main_logger.info(f"原始: {merge_info['original_size']} -> 新增: {merge_info['new_size']} -> 合并: {merge_info['merged_size']}")
    
    return merge_info

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='从训练好的策略中rollout并收集高质量状态')
    parser.add_argument('--agent_path', type=str, required=True, help='训练好的智能体模型路径')
    parser.add_argument('--vae_path', type=str, required=True, help='VAE模型路径')
    parser.add_argument('--n_episodes', type=int, default=50, help='rollout的episode数量')
    parser.add_argument('--quality_threshold', type=float, default=0.6, help='质量阈值（episode平均奖励）')
    parser.add_argument('--n_uavs', type=int, default=10, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2000, help='区域大小 (默认值与train_multiproc_config_1.py一致，可通过命令行参数覆盖)')
    parser.add_argument('--save_dir', type=str, required=True, help='保存目录')
    parser.add_argument('--save_all_states', action='store_true', help='是否保存所有状态')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    
    # 数据合并选项
    parser.add_argument('--merge_with', type=str, help='要合并的原始数据目录')
    parser.add_argument('--merge_output', type=str, help='合并后的输出目录')
    
    args = parser.parse_args()
    
    # 设置随机种子
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 环境配置
    env_config = {
        'n_uavs': args.n_uavs,
        'n_users': args.n_users,
        'area_size': args.area_size,
        'seed': args.seed
    }
    
    # 创建收集器
    collector = PolicyRolloutCollector(
        agent_path=args.agent_path,
        vae_path=args.vae_path,
        env_config=env_config,
        quality_threshold=args.quality_threshold
    )
    
    # 运行收集
    main_logger.info("开始rollout和数据收集...")
    save_info, summary = collector.run(
        n_episodes=args.n_episodes,
        save_dir=args.save_dir,
        save_all_states=args.save_all_states
    )
    
    # 数据合并（如果指定）
    if args.merge_with and args.merge_output and save_info:
        main_logger.info("开始数据集合并...")
        merge_info = merge_datasets(args.merge_with, args.save_dir, args.merge_output)
        
        # 保存完整的运行信息
        run_info = {
            'args': vars(args),
            'save_info': save_info,
            'summary': summary,
            'merge_info': merge_info,
            'timestamp': datetime.now().isoformat()
        }
    else:
        run_info = {
            'args': vars(args),
            'save_info': save_info,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    # 保存运行信息
    if args.save_dir:
        run_info_path = os.path.join(args.save_dir, 'rollout_info.json')
        with open(run_info_path, 'w') as f:
            json.dump(run_info, f, indent=2)
    
    # 输出结果
    main_logger.info("=" * 60)
    main_logger.info("Rollout和数据收集完成!")
    if save_info:
        main_logger.info(f"收集到 {save_info['n_new_states']} 个新的高质量状态")
        main_logger.info(f"质量episode比例: {summary['quality_rate']:.2%}")
        main_logger.info(f"平均episode奖励: {summary['avg_episode_reward']:.3f}")
    main_logger.info("=" * 60)

if __name__ == "__main__":
    main()
