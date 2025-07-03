"""
收集高奖励状态用于训练VAE
该脚本运行环境并使用启发式策略或现有模型收集表现良好的状态
"""

import numpy as np
import torch
import os
import sys
import argparse
import logging
from datetime import datetime
import matplotlib.pyplot as plt

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from logger import main_logger, init_multiproc_logging
from config_1 import Config
from hmasd.agent import HMASDAgent

# 导入强化学习模型相关库
try:
    from stable_baselines3 import PPO, SAC, A2C
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    main_logger.warning("Stable Baselines3 not available. Will use heuristic controller only.")

class HeuristicController:
    """
    启发式控制器：用于生成基线策略来收集好状态
    """
    def __init__(self, n_uavs, area_size, user_positions, ground_bs_positions):
        self.n_uavs = n_uavs
        self.area_size = area_size
        self.user_positions = user_positions
        self.ground_bs_positions = ground_bs_positions
        
        # 计算用户中心和基站中心
        self.user_center = np.mean(user_positions, axis=0)
        self.bs_center = np.mean(ground_bs_positions[:, :2], axis=0)  # 只取x,y坐标
        
        # 策略参数
        self.relay_height = 120  # 中继无人机高度
        self.coverage_height = 80  # 覆盖无人机高度
        self.speed_factor = 0.3  # 移动速度因子
        
        main_logger.info(f"启发式控制器初始化: 用户中心={self.user_center}, 基站中心={self.bs_center}")
    
    def get_target_positions(self, current_positions):
        """
        计算无人机的目标位置
        
        策略：
        1. 一部分无人机（40%）负责覆盖用户簇
        2. 另一部分无人机（60%）形成从用户到基站的中继链
        
        参数:
            current_positions: 当前无人机位置 [n_uavs, 3]
            
        返回:
            target_positions: 目标位置 [n_uavs, 3]
        """
        target_positions = np.zeros_like(current_positions)
        
        # 分配角色
        n_coverage_uavs = max(1, int(self.n_uavs * 0.4))  # 40%负责覆盖
        n_relay_uavs = self.n_uavs - n_coverage_uavs      # 60%负责中继
        
        # 1. 覆盖无人机：分布在用户簇周围
        for i in range(n_coverage_uavs):
            # 在用户中心周围形成环形分布
            angle = 2 * np.pi * i / n_coverage_uavs
            radius = 300  # 覆盖半径
            
            target_x = self.user_center[0] + radius * np.cos(angle)
            target_y = self.user_center[1] + radius * np.sin(angle)
            target_z = self.coverage_height
            
            # 确保在边界内
            target_x = np.clip(target_x, 50, self.area_size - 50)
            target_y = np.clip(target_y, 50, self.area_size - 50)
            
            target_positions[i] = [target_x, target_y, target_z]
        
        # 2. 中继无人机：形成从用户中心到基站的链
        for i in range(n_coverage_uavs, self.n_uavs):
            relay_idx = i - n_coverage_uavs
            
            # 在用户中心和基站中心之间线性插值
            if n_relay_uavs == 1:
                t = 0.5  # 单个中继无人机放在中间
            else:
                t = (relay_idx + 1) / (n_relay_uavs + 1)  # 均匀分布
            
            target_x = self.user_center[0] + t * (self.bs_center[0] - self.user_center[0])
            target_y = self.user_center[1] + t * (self.bs_center[1] - self.user_center[1])
            target_z = self.relay_height
            
            # 添加一些随机扰动以避免重叠
            noise_scale = 100
            target_x += np.random.normal(0, noise_scale)
            target_y += np.random.normal(0, noise_scale)
            
            # 确保在边界内
            target_x = np.clip(target_x, 50, self.area_size - 50)
            target_y = np.clip(target_y, 50, self.area_size - 50)
            
            target_positions[i] = [target_x, target_y, target_z]
        
        return target_positions
    
    def get_actions(self, current_positions):
        """
        根据当前位置计算动作
        
        参数:
            current_positions: 当前位置 [n_uavs, 3]
            
        返回:
            actions: 动作（速度向量）[n_uavs, 3]
        """
        target_positions = self.get_target_positions(current_positions)
        
        # 计算目标方向
        directions = target_positions - current_positions
        distances = np.linalg.norm(directions, axis=1, keepdims=True)
        
        # 避免除零
        distances = np.maximum(distances, 1e-6)
        
        # 归一化方向向量
        unit_directions = directions / distances
        
        # 根据距离调整速度
        speeds = np.minimum(distances.flatten() * self.speed_factor, 20.0)  # 最大速度20m/s
        
        # 计算动作
        actions = unit_directions * speeds.reshape(-1, 1)
        
        return actions

class StateCollector:
    """
    状态收集器：运行环境并收集高奖励状态
    支持混合策略：预训练模型 + 启发式控制器 + 随机探索
    """
    def __init__(self, env, controller, reward_threshold=0.8, model=None, exploration_ratio=0.3, model_ratio=0.4):
        self.env = env
        self.controller = controller
        self.reward_threshold = reward_threshold
        self.model = model
        self.exploration_ratio = exploration_ratio  # 随机探索比例
        self.model_ratio = model_ratio  # 模型策略比例
        self.heuristic_ratio = 1.0 - exploration_ratio - model_ratio  # 启发式策略比例
        
        # 确保比例合理
        if self.heuristic_ratio < 0:
            main_logger.warning(f"策略比例不合理，调整为：模型={model_ratio:.2f}, 随机={exploration_ratio:.2f}, 启发式={1.0-model_ratio-exploration_ratio:.2f}")
            self.heuristic_ratio = max(0.1, 1.0 - exploration_ratio - model_ratio)
            total = self.model_ratio + self.exploration_ratio + self.heuristic_ratio
            self.model_ratio /= total
            self.exploration_ratio /= total
            self.heuristic_ratio /= total
        
        # 收集的数据
        self.good_states = []
        self.rewards = []
        self.episode_rewards = []
        
        # 统计使用的策略类型
        self.strategy_stats = {
            'model': 0,
            'heuristic': 0, 
            'random': 0
        }
        
        main_logger.info(f"StateCollector初始化 - 策略比例: 模型={self.model_ratio:.2f}, 启发式={self.heuristic_ratio:.2f}, 随机={self.exploration_ratio:.2f}")
        if model is not None:
            main_logger.info("已加载预训练模型用于数据收集")
        else:
            main_logger.info("未加载预训练模型，将使用启发式+随机策略")
        
    def _get_mixed_actions(self, observations, current_positions, episode_step=0):
        """
        使用混合策略生成动作
        
        参数:
            observations: 环境观测
            current_positions: 当前无人机位置
            episode_step: 当前episode中的步数
            
        返回:
            actions: 动作数组
            strategy_used: 使用的策略类型
        """
        # 随机选择策略
        rand = np.random.random()
        
        if self.model is not None and rand < self.model_ratio:
            # 使用预训练模型
            try:
                # 获取全局状态
                global_state = self.env._get_state()
                
                # 将观测转换为模型需要的格式
                if isinstance(observations, dict):
                    # 从字典中提取观测数组
                    obs_list = []
                    for agent_id in sorted(observations.keys()):
                        if "obs" in observations[agent_id]:
                            obs_list.append(observations[agent_id]["obs"])
                        else:
                            obs_list.append(observations[agent_id])
                    obs = np.array(obs_list)
                else:
                    obs = observations
                
                # 使用HMASD模型的step方法
                # 参数: state, observations, ep_t, deterministic, env_id
                # 设置deterministic=True来实现评估模式的效果
                actions, _ = self.model.step(
                    state=global_state,
                    observations=obs,
                    ep_t=episode_step,
                    deterministic=True,  # 使用确定性策略进行数据收集
                    env_id=0  # 使用默认环境ID
                )
                
                self.strategy_stats['model'] += 1
                return actions, 'model'
                
            except Exception as e:
                main_logger.warning(f"模型预测失败: {e}，回退到启发式策略")
                # 回退到启发式策略
                actions = self.controller.get_actions(current_positions)
                self.strategy_stats['heuristic'] += 1
                return actions, 'heuristic'
        
        elif rand < self.model_ratio + self.exploration_ratio:
            # 随机探索
            actions = np.random.uniform(-1, 1, (self.env.n_uavs, 3)) * 30  # 随机速度 [-30, 30] m/s
            self.strategy_stats['random'] += 1
            return actions, 'random'
        
        else:
            # 启发式策略
            actions = self.controller.get_actions(current_positions)
            self.strategy_stats['heuristic'] += 1
            return actions, 'heuristic'

    def collect_episode(self, max_steps=1500, render=False):
        """
        收集一个episode的数据
        
        参数:
            max_steps: 最大步数
            render: 是否渲染
            
        返回:
            episode_reward: episode总奖励
            good_states_count: 收集到的好状态数量
        """
        observations, infos = self.env.reset()
        episode_reward = 0
        good_states_count = 0
        
        for step in range(max_steps):
            # 获取当前全局状态
            current_state = self.env._get_state()
            
            # 获取当前无人机位置
            current_positions = self.env.uav_positions.copy()
            
            # 使用混合策略生成动作
            actions, strategy_used = self._get_mixed_actions(observations, current_positions, step)
            
            # 执行动作
            observations, rewards, dones, truncated, infos = self.env.step(actions)
            
            # 获取奖励（假设所有智能体共享相同的奖励）
            step_reward = rewards[list(rewards.keys())[0]] if isinstance(rewards, dict) else rewards
            episode_reward += step_reward
            
            # 如果当前状态奖励较高，收集它
            if step_reward >= self.reward_threshold:
                self.good_states.append(current_state.copy())
                self.rewards.append(step_reward)
                good_states_count += 1
            
            # 渲染（如果需要）
            if render and step % 50 == 0:
                self.env.render()
            
            # 检查是否结束
            done_any = any(dones.values()) if isinstance(dones, dict) else dones
            if done_any:
                break
        
        self.episode_rewards.append(episode_reward)
        return episode_reward, good_states_count
    
    def collect_data(self, n_episodes=50, render=False):
        """
        收集多个episode的数据
        
        参数:
            n_episodes: episode数量
            render: 是否渲染
            
        返回:
            summary: 收集统计信息
        """
        main_logger.info(f"开始收集数据，共{n_episodes}个episodes，奖励阈值={self.reward_threshold}")
        
        total_good_states = 0
        successful_episodes = 0
        
        for episode in range(n_episodes):
            try:
                episode_reward, good_states_count = self.collect_episode(render=render)
                total_good_states += good_states_count
                
                # 定义成功episode（平均奖励较高）
                if episode_reward / 1500 >= 0.5:  # 假设平均奖励0.5以上为成功
                    successful_episodes += 1
                
                # 记录进度
                if (episode + 1) % 10 == 0:
                    main_logger.info(f"Episode {episode + 1}/{n_episodes}: "
                                   f"本episode奖励={episode_reward:.3f}, "
                                   f"收集好状态数={good_states_count}, "
                                   f"累计好状态数={total_good_states}")
            except Exception as e:
                main_logger.warning(f"Episode {episode}执行失败: {e}")
                continue
        
        # 统计信息
        total_strategy_calls = sum(self.strategy_stats.values())
        strategy_percentages = {k: (v / max(total_strategy_calls, 1)) * 100 for k, v in self.strategy_stats.items()}
        
        summary = {
            'total_episodes': n_episodes,
            'successful_episodes': successful_episodes,
            'success_rate': successful_episodes / n_episodes,
            'total_good_states': total_good_states,
            'avg_good_states_per_episode': total_good_states / n_episodes,
            'avg_episode_reward': np.mean(self.episode_rewards),
            'std_episode_reward': np.std(self.episode_rewards),
            'reward_threshold': self.reward_threshold,
            'strategy_stats': self.strategy_stats,
            'strategy_percentages': strategy_percentages
        }
        
        main_logger.info(f"数据收集完成: {summary}")
        main_logger.info(f"策略使用统计: 模型={strategy_percentages['model']:.1f}%, "
                        f"启发式={strategy_percentages['heuristic']:.1f}%, "
                        f"随机={strategy_percentages['random']:.1f}%")
        return summary
    
    def save_data(self, save_dir):
        """
        保存收集的数据
        
        参数:
            save_dir: 保存目录
        """
        os.makedirs(save_dir, exist_ok=True)
        
        # 保存好状态
        good_states_array = np.array(self.good_states)
        good_states_path = os.path.join(save_dir, 'good_states.npy')
        np.save(good_states_path, good_states_array)
        
        # 保存对应的奖励
        rewards_array = np.array(self.rewards)
        rewards_path = os.path.join(save_dir, 'good_states_rewards.npy')
        np.save(rewards_path, rewards_array)
        
        # 保存episode奖励
        episode_rewards_array = np.array(self.episode_rewards)
        episode_rewards_path = os.path.join(save_dir, 'episode_rewards.npy')
        np.save(episode_rewards_path, episode_rewards_array)
        
        main_logger.info(f"数据已保存到 {save_dir}")
        main_logger.info(f"好状态数据形状: {good_states_array.shape}")
        main_logger.info(f"好状态奖励范围: [{rewards_array.min():.3f}, {rewards_array.max():.3f}]")
        
        return {
            'good_states_path': good_states_path,
            'rewards_path': rewards_path,
            'episode_rewards_path': episode_rewards_path,
            'n_good_states': len(good_states_array),
            'state_dim': good_states_array.shape[1] if len(good_states_array) > 0 else 0
        }
    
    def visualize_collection_stats(self, save_dir):
        """
        可视化收集统计信息
        
        参数:
            save_dir: 保存目录
        """
        if len(self.episode_rewards) == 0:
            main_logger.warning("没有数据用于可视化")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. Episode奖励趋势
        ax1.plot(self.episode_rewards)
        ax1.set_title('Episode奖励趋势')
        ax1.set_xlabel('Episode')
        ax1.set_ylabel('总奖励')
        ax1.grid(True)
        
        # 2. 奖励分布直方图
        ax2.hist(self.episode_rewards, bins=20, alpha=0.7)
        ax2.set_title('Episode奖励分布')
        ax2.set_xlabel('总奖励')
        ax2.set_ylabel('频次')
        ax2.grid(True)
        
        # 3. 好状态奖励分布
        if len(self.rewards) > 0:
            ax3.hist(self.rewards, bins=30, alpha=0.7, color='green')
            ax3.axvline(self.reward_threshold, color='red', linestyle='--', 
                       label=f'阈值={self.reward_threshold}')
            ax3.set_title('好状态奖励分布')
            ax3.set_xlabel('步奖励')
            ax3.set_ylabel('频次')
            ax3.legend()
            ax3.grid(True)
        
        # 4. 累积好状态数量
        cumulative_good_states = np.cumsum([len([r for r in self.rewards if r >= self.reward_threshold])])
        if len(cumulative_good_states) > 0:
            ax4.plot(cumulative_good_states)
            ax4.set_title('累积好状态数量')
            ax4.set_xlabel('Episode')
            ax4.set_ylabel('累积好状态数')
            ax4.grid(True)
        
        plt.tight_layout()
        
        # 保存图像
        plot_path = os.path.join(save_dir, 'collection_stats.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        main_logger.info(f"统计图表已保存到 {plot_path}")

def load_pretrained_model(model_path, current_config):
    """
    加载预训练的HMASD模型
    
    参数:
        model_path: 模型文件路径
        current_config: 当前环境的配置对象
        
    返回:
        agent: HMASDAgent实例，如果失败则返回None
    """
    if not os.path.exists(model_path):
        main_logger.warning(f"模型文件不存在: {model_path}")
        return None
    
    try:
        # 为了兼容新版PyTorch的安全加载机制，添加Config类到安全全局列表
        import torch.serialization
        torch.serialization.add_safe_globals([Config])
        main_logger.debug("已将Config类添加到PyTorch安全全局列表")
        
        # 首先加载检查点以获取原始配置
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        checkpoint = torch.load(model_path, map_location=device)
        
        if 'config' not in checkpoint:
            main_logger.error("检查点文件中未找到配置信息")
            return None
        
        # 获取原始训练时的配置
        original_config = checkpoint['config']
        main_logger.info(f"从检查点加载原始配置: use_opt={getattr(original_config, 'use_opt', False)}")
        
        # 创建一个混合配置：使用原始的网络架构配置，但更新环境维度
        # 这确保网络结构与预训练模型完全匹配
        hybrid_config = original_config
        
        # 更新当前环境的维度信息
        hybrid_config.state_dim = current_config.state_dim
        hybrid_config.obs_dim = current_config.obs_dim
        hybrid_config.n_agents = current_config.n_agents
        
        main_logger.info(f"使用混合配置创建模型: "
                        f"state_dim={hybrid_config.state_dim}, "
                        f"obs_dim={hybrid_config.obs_dim}, "
                        f"n_agents={hybrid_config.n_agents}, "
                        f"use_opt={getattr(hybrid_config, 'use_opt', False)}")
        
        # 使用混合配置创建HMASD智能体实例
        agent = HMASDAgent(
            config=hybrid_config,
            log_dir='temp_collection_log',  # 临时日志目录
            device=device
        )
        
        # 加载模型权重（现在应该完全匹配）
        agent.load_model(model_path)
        
        # 注意：HMASD模型通过在step方法中设置deterministic=True来实现评估模式
        # 不需要显式调用eval()方法，因为HMASDAgent类没有该方法
        main_logger.info(f"成功加载HMASD模型: {model_path}")
        main_logger.info("模型将在数据收集时使用确定性策略（deterministic=True）")
        return agent
        
    except Exception as e:
        main_logger.error(f"加载模型时发生错误: {e}")
        import traceback
        main_logger.error(f"详细错误信息: {traceback.format_exc()}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='收集高奖励状态用于VAE训练')
    parser.add_argument('--n_episodes', type=int, default=100, help='收集的episode数量')
    parser.add_argument('--reward_threshold', type=float, default=0.7, help='好状态的奖励阈值')
    parser.add_argument('--n_uavs', type=int, default=10, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=50, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2000, help='区域大小 (默认值与train_multiproc_config_1.py一致，可通过命令行参数覆盖)')
    parser.add_argument('--save_dir', type=str, default='data/good_states', help='保存目录')
    parser.add_argument('--render', action='store_true', help='是否渲染')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    
    # 混合策略相关参数
    parser.add_argument('--model_path', type=str, default='scripts/hmasd_multiproc_paper_config.pt', 
                       help='预训练模型路径')
    parser.add_argument('--exploration_ratio', type=float, default=0.3, 
                       help='随机探索比例 (0.0-1.0)')
    parser.add_argument('--model_ratio', type=float, default=0.4, 
                       help='模型策略比例 (0.0-1.0)')
    parser.add_argument('--use_model', action='store_true', 
                       help='是否使用预训练模型（如果不指定，仅使用启发式+随机策略）')
    
    args = parser.parse_args()
    
    # 初始化日志记录器，生成带时间戳的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"collect_good_states_{timestamp}.log"
    init_multiproc_logging(
        log_dir='logs',
        log_file=log_filename,
        file_level=logging.INFO,
        console_level=logging.INFO
    )
    
    main_logger.info("=" * 60)
    main_logger.info("开始运行状态收集脚本")
    main_logger.info(f"日志文件: logs/{log_filename}")
    main_logger.info(f"运行参数: {vars(args)}")
    main_logger.info("=" * 60)
    
    # 验证参数
    if args.exploration_ratio + args.model_ratio > 1.0:
        main_logger.error("探索比例和模型比例之和不能超过1.0")
        sys.exit(1)
    
    # 设置随机种子
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 创建时间戳保存目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = f"{args.save_dir}_{timestamp}"
    
    # 创建环境 - 使用与train_multiproc_config_1.py完全一致的参数
    # 根据train_multiproc_config_1.py中make_env函数的场景4配置
    env = UAVForcedRelayEnv(
        n_uavs=args.n_uavs,
        n_users=args.n_users,
        user_distribution='forced_relay_cluster',  # 场景4强制使用此分布
        channel_model='probabilistic',  # 使用默认信道模型
        render_mode='human' if args.render else None,
        seed=args.seed,
        use_fdma=True,  # 默认启用FDMA
        bandwidth=20e6,  # 默认带宽
        # 场景4特有参数 - 使用train_multiproc_config_1.py中的默认值
        max_hops=4,
        area_size=2500,
        n_clusters=4,
        cluster_std=80,
        central_area_ratio=0.6,
        min_sinr=3,
        max_connections=25,
        coverage_weight=0.8,
        connectivity_weight=0.15,
        efficiency_weight=0.05,
        max_steps=1500
    )
    
    # 初始化环境以获取位置信息和维度
    observations, infos = env.reset()
    
    # 创建配置对象并设置环境维度
    config = Config()
    config.n_agents = args.n_uavs
    
    # 在环境reset后获取真实的维度
    # state_dim 通过调用内部方法获取
    state_dim = env._get_state().shape[0]
    
    # obs_dim 从返回的Dict观测空间中获取
    first_agent = env.possible_agents[0]
    obs_dim = env.get_obs_dim()
    
    # 更新配置
    config.update_env_dims(state_dim, obs_dim)
    
    # 加载预训练模型（如果指定）
    model = None
    if args.use_model:
        model = load_pretrained_model(args.model_path, config)
        if model is None:
            main_logger.warning("模型加载失败，将仅使用启发式+随机策略")
            args.model_ratio = 0.0  # 设置模型比例为0
    else:
        main_logger.info("未启用模型策略，将仅使用启发式+随机策略")
        args.model_ratio = 0.0  # 设置模型比例为0
    
    # 创建启发式控制器
    controller = HeuristicController(
        n_uavs=args.n_uavs,
        area_size=2500,  # 使用与环境一致的area_size
        user_positions=env.user_positions,
        ground_bs_positions=env.ground_bs_positions
    )
    
    # 创建状态收集器
    collector = StateCollector(
        env=env,
        controller=controller,
        reward_threshold=args.reward_threshold,
        model=model,
        exploration_ratio=args.exploration_ratio,
        model_ratio=args.model_ratio
    )
    
    # 收集数据
    main_logger.info("开始数据收集...")
    summary = collector.collect_data(n_episodes=args.n_episodes, render=args.render)
    
    # 保存数据
    main_logger.info("保存数据...")
    save_info = collector.save_data(save_dir)
    
    # 可视化统计信息
    main_logger.info("生成可视化...")
    collector.visualize_collection_stats(save_dir)
    
    # 保存运行参数和统计信息
    config_info = {
        'args': vars(args),
        'summary': summary,
        'save_info': save_info,
        'env_info': {
            'state_dim': state_dim,
            'obs_dim': obs_dim,
            'action_dim': 3,
            'n_uavs': args.n_uavs,
            'n_users': args.n_users,
            'area_size': args.area_size
        }
    }
    
    import json
    config_path = os.path.join(save_dir, 'collection_config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_info, f, indent=2, ensure_ascii=False)
    
    # 输出最终统计
    main_logger.info("=" * 60)
    main_logger.info("数据收集完成!")
    main_logger.info(f"保存目录: {save_dir}")
    main_logger.info(f"收集到 {save_info['n_good_states']} 个好状态")
    main_logger.info(f"状态维度: {save_info['state_dim']}")
    main_logger.info(f"成功率: {summary['success_rate']:.2%}")
    main_logger.info(f"平均episode奖励: {summary['avg_episode_reward']:.3f}")
    main_logger.info("=" * 60)
    
    env.close()

if __name__ == "__main__":
    main()
