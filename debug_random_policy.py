#!/usr/bin/env python3
"""
Debug Random Policy - 深度分析随机策略行为
分析为什么"随机"策略导致UAV直线移动而非随机散布
"""

import numpy as np
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from config_1 import Config
from hmasd.agent import HMASDAgent
from envs.pettingzoo.scenario4 import UAVForcedRelayEnv
from logger import main_logger
import json
from datetime import datetime
import os

class RandomPolicyDebugger:
    def __init__(self):
        self.config = Config()
        self.debug_data = {
            'actions': [],
            'velocities': [],
            'positions': [],
            'observations': [],
            'hidden_states': [],
            'skill_assignments': [],
            'action_magnitudes': [],
            'movement_directions': [],
            'step_distances': []
        }
        
    def create_true_random_policy(self, n_agents, action_dim, max_speed=30):
        """创建真正的随机策略，完全绕过神经网络"""
        def random_policy():
            # 生成真正随机的3D动作向量
            actions = []
            for _ in range(n_agents):
                # 方法1: 均匀随机方向 + 随机速度
                direction = np.random.uniform(-1, 1, 3)  # 随机方向
                direction = direction / (np.linalg.norm(direction) + 1e-8)  # 归一化
                speed = np.random.uniform(0, 1)  # 随机速度比例
                action = direction * speed
                actions.append(action)
            return np.array(actions)
        return random_policy
    
    def analyze_action_patterns(self, actions_history):
        """分析动作模式，检测是否存在隐藏的规律性"""
        actions_array = np.array(actions_history)
        
        analysis = {
            'mean_action': np.mean(actions_array, axis=0),
            'std_action': np.std(actions_array, axis=0),
            'action_range': {
                'min': np.min(actions_array, axis=0),
                'max': np.max(actions_array, axis=0)
            },
            'correlation_matrix': np.corrcoef(actions_array.reshape(-1, actions_array.shape[-1]).T),
            'temporal_consistency': []
        }
        
        # 检查时间一致性（连续动作的相似性）
        for i in range(len(actions_history) - 1):
            similarity = np.mean([
                np.dot(actions_history[i][j], actions_history[i+1][j]) / 
                (np.linalg.norm(actions_history[i][j]) * np.linalg.norm(actions_history[i+1][j]) + 1e-8)
                for j in range(len(actions_history[i]))
            ])
            analysis['temporal_consistency'].append(similarity)
        
        return analysis
    
    def detect_straight_line_movement(self, trajectories, threshold=0.9):
        """检测直线移动模式"""
        straight_line_agents = []
        
        for i, trajectory in enumerate(trajectories):
            if len(trajectory) < 3:
                continue
                
            trajectory = np.array(trajectory)
            
            # 计算路径的线性度
            start_pos = trajectory[0]
            end_pos = trajectory[-1]
            direct_distance = np.linalg.norm(end_pos - start_pos)
            
            if direct_distance < 1e-6:  # 没有移动
                continue
                
            # 计算实际路径长度
            path_distances = np.linalg.norm(np.diff(trajectory, axis=0), axis=1)
            total_path_length = np.sum(path_distances)
            
            # 线性度 = 直线距离 / 实际路径长度
            linearity = direct_distance / (total_path_length + 1e-8)
            
            if linearity > threshold:
                straight_line_agents.append({
                    'agent_id': i,
                    'linearity': linearity,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'total_distance': total_path_length
                })
        
        return straight_line_agents
    
    def run_comparison_test(self, episode_length=200):
        """运行对比测试：HMASD随机策略 vs 真正随机策略"""
        
        print("="*60)
        print("开始随机策略对比测试")
        print("="*60)
        
        # 创建环境
        env = UAVForcedRelayEnv()
        observations, infos = env.reset()
        
        # 获取环境信息
        state = infos[list(infos.keys())[0]]['state']
        first_agent = list(observations.keys())[0]
        obs_dim = len(observations[first_agent]['obs'])
        n_agents = len(observations)
        
        self.config.update_env_dims(
            state_dim=len(state),
            obs_dim=obs_dim,
            n_agents=n_agents
        )
        
        print(f"环境配置:")
        print(f"  智能体数量: {n_agents}")
        print(f"  观测维度: {obs_dim}")
        print(f"  动作维度: {self.config.action_dim}")
        print(f"  区域大小: {self.config.area_size}")
        
        # 测试1: HMASD "随机"策略
        print("\n--- 测试1: HMASD未训练策略 ---")
        hmasd_results = self._run_single_test(env, "hmasd", episode_length)
        
        # 重置环境
        env.close()
        env = UAVForcedRelayEnv()
        observations, infos = env.reset()
        
        # 测试2: 真正随机策略
        print("\n--- 测试2: 真正随机策略 ---")
        true_random_results = self._run_single_test(env, "true_random", episode_length)
        
        # 对比分析
        self._compare_results(hmasd_results, true_random_results)
        
        # 生成可视化
        self._generate_visualizations(hmasd_results, true_random_results)
        
        # 保存调试数据
        self._save_debug_data(hmasd_results, true_random_results)
        
        env.close()
        
    def _run_single_test(self, env, policy_type, episode_length):
        """运行单个策略测试"""
        
        # 初始化记录
        trajectories = [[] for _ in range(self.config.n_agents)]
        actions_history = []
        velocities_history = []
        observations_history = []
        hidden_states_history = []
        
        # 创建策略
        if policy_type == "hmasd":
            agent = HMASDAgent(self.config, device=torch.device('cpu'))
            print(f"HMASD智能体创建完成，观测归一化: {'启用' if self.config.use_obsnorm else '禁用'}")
        else:
            true_random_policy = self.create_true_random_policy(
                self.config.n_agents, 
                self.config.action_dim
            )
            print("真正随机策略创建完成")
        
        # 获取初始观测
        observations, infos = env.reset()
        state = infos[list(infos.keys())[0]]['state']
        
        print(f"开始{episode_length}步模拟...")
        
        for step in range(episode_length):
            # 记录当前位置
            for i in range(self.config.n_agents):
                trajectories[i].append([env.uav_positions[i][0], env.uav_positions[i][1]])
            
            # 选择动作
            if policy_type == "hmasd":
                # 准备观测数据
                obs_array = []
                for agent_id in sorted(observations.keys()):
                    obs_array.append(observations[agent_id]['obs'])
                obs_array = np.array(obs_array)
                
                # 使用HMASD智能体
                actions, agent_infos = agent.step(
                    states_batch=np.array([state]),
                    observations_batch=np.array([obs_array]),
                    env_steps_batch=np.array([step]),
                    dones_batch=np.array([False]),
                    deterministic=False
                )
                actions = actions[0]  # 取第一个batch
                
                # 记录隐藏状态信息
                if hasattr(agent, 'skill_discoverer') and hasattr(agent.skill_discoverer, 'rnn_hidden'):
                    hidden_states_history.append({
                        'step': step,
                        'hidden_norm': torch.norm(agent.skill_discoverer.rnn_hidden).item()
                    })
                
                observations_history.append(obs_array.copy())
                
            else:
                # 使用真正随机策略
                actions = true_random_policy()
            
            # 记录动作信息
            actions_history.append(actions.copy())
            
            # 计算速度（动作 * 最大速度）
            velocities = actions * env.max_speed
            velocities_history.append(velocities.copy())
            
            # 准备环境动作
            env_actions = {}
            for i, agent_id in enumerate(sorted(observations.keys())):
                env_actions[agent_id] = actions[i]
            
            # 执行动作
            next_observations, rewards, terminations, truncations, env_infos = env.step(env_actions)
            
            # 更新状态
            state = env_infos[list(env_infos.keys())[0]]['next_state']
            observations = next_observations
            
            # 打印进度
            if step % 50 == 0:
                action_magnitudes = [np.linalg.norm(a) for a in actions]
                print(f"  步骤 {step}: 动作幅度范围 [{np.min(action_magnitudes):.3f}, {np.max(action_magnitudes):.3f}]")
            
            if np.any(list(terminations.values())):
                print(f"  Episode在第{step}步结束")
                break
        
        # 分析结果
        results = {
            'policy_type': policy_type,
            'trajectories': trajectories,
            'actions_history': actions_history,
            'velocities_history': velocities_history,
            'observations_history': observations_history,
            'hidden_states_history': hidden_states_history,
            'action_analysis': self.analyze_action_patterns(actions_history),
            'straight_line_agents': self.detect_straight_line_movement(trajectories),
            'final_positions': [traj[-1] if traj else [0, 0] for traj in trajectories],
            'total_distances': [
                np.sum([np.linalg.norm(np.array(traj[i+1]) - np.array(traj[i])) 
                       for i in range(len(traj)-1)]) if len(traj) > 1 else 0
                for traj in trajectories
            ]
        }
        
        return results
    
    def _compare_results(self, hmasd_results, true_random_results):
        """对比两种策略的结果"""
        
        print("\n" + "="*60)
        print("策略对比分析")
        print("="*60)
        
        # 1. 轨迹线性度对比
        hmasd_straight = len(hmasd_results['straight_line_agents'])
        random_straight = len(true_random_results['straight_line_agents'])
        
        print(f"\n1. 直线移动检测:")
        print(f"   HMASD策略: {hmasd_straight}/{self.config.n_agents} 个智能体呈直线移动")
        print(f"   真随机策略: {random_straight}/{self.config.n_agents} 个智能体呈直线移动")
        
        if hmasd_straight > 0:
            print("   HMASD直线移动详情:")
            for agent_info in hmasd_results['straight_line_agents']:
                print(f"     UAV {agent_info['agent_id']}: 线性度={agent_info['linearity']:.3f}")
        
        # 2. 动作分布对比
        print(f"\n2. 动作统计对比:")
        hmasd_actions = np.array(hmasd_results['actions_history'])
        random_actions = np.array(true_random_results['actions_history'])
        
        print(f"   HMASD动作:")
        print(f"     均值: {np.mean(hmasd_actions, axis=(0,1))}")
        print(f"     标准差: {np.std(hmasd_actions, axis=(0,1))}")
        print(f"     范围: [{np.min(hmasd_actions):.3f}, {np.max(hmasd_actions):.3f}]")
        
        print(f"   真随机动作:")
        print(f"     均值: {np.mean(random_actions, axis=(0,1))}")
        print(f"     标准差: {np.std(random_actions, axis=(0,1))}")
        print(f"     范围: [{np.min(random_actions):.3f}, {np.max(random_actions):.3f}]")
        
        # 3. 移动距离对比
        print(f"\n3. 移动距离对比:")
        hmasd_distances = hmasd_results['total_distances']
        random_distances = true_random_results['total_distances']
        
        print(f"   HMASD总移动距离: 均值={np.mean(hmasd_distances):.1f}m, 标准差={np.std(hmasd_distances):.1f}m")
        print(f"   真随机总移动距离: 均值={np.mean(random_distances):.1f}m, 标准差={np.std(random_distances):.1f}m")
        
        # 4. 时间一致性分析
        if hmasd_results['action_analysis']['temporal_consistency']:
            hmasd_consistency = np.mean(hmasd_results['action_analysis']['temporal_consistency'])
            random_consistency = np.mean(true_random_results['action_analysis']['temporal_consistency'])
            
            print(f"\n4. 时间一致性分析:")
            print(f"   HMASD动作时间一致性: {hmasd_consistency:.3f}")
            print(f"   真随机动作时间一致性: {random_consistency:.3f}")
            print(f"   (值越高表示连续动作越相似，随机策略应该接近0)")
        
        # 5. 问题诊断
        print(f"\n5. 问题诊断:")
        if hmasd_straight > random_straight:
            print("   ❌ HMASD策略确实存在直线移动问题")
            print("   可能原因:")
            print("     - 未训练的神经网络存在初始化偏置")
            print("     - GRU隐藏状态导致时间一致性")
            print("     - 观测归一化影响动作选择")
            print("     - 技能分配机制产生确定性行为")
        else:
            print("   ✅ HMASD策略的随机性与真随机策略相当")
    
    def _generate_visualizations(self, hmasd_results, true_random_results):
        """生成可视化图表"""
        
        print("\n生成可视化图表...")
        
        # 创建子图
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('随机策略对比分析', fontsize=16)
        
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
        
        # 1. 轨迹对比
        for i, (results, title) in enumerate([(hmasd_results, 'HMASD策略'), 
                                             (true_random_results, '真随机策略')]):
            ax = axes[i, 0]
            
            for j, trajectory in enumerate(results['trajectories']):
                if len(trajectory) > 0:
                    trajectory = np.array(trajectory)
                    ax.plot(trajectory[:, 0], trajectory[:, 1], 
                           color=colors[j % len(colors)], 
                           label=f'UAV {j}', alpha=0.7, linewidth=2)
                    # 起始点
                    ax.scatter(trajectory[0, 0], trajectory[0, 1], 
                              color=colors[j % len(colors)], s=100, marker='o')
                    # 结束点
                    ax.scatter(trajectory[-1, 0], trajectory[-1, 1], 
                              color=colors[j % len(colors)], s=100, marker='x')
            
            ax.set_xlim(0, self.config.area_size)
            ax.set_ylim(0, self.config.area_size)
            ax.set_title(f'{title} - 轨迹')
            ax.set_xlabel('X (米)')
            ax.set_ylabel('Y (米)')
            ax.grid(True, alpha=0.3)
            if i == 0:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 2. 动作分布直方图
        for i, (results, title) in enumerate([(hmasd_results, 'HMASD'), 
                                             (true_random_results, '真随机')]):
            ax = axes[i, 1]
            
            actions = np.array(results['actions_history'])
            actions_flat = actions.reshape(-1, actions.shape[-1])
            
            for dim in range(3):
                ax.hist(actions_flat[:, dim], bins=30, alpha=0.5, 
                       label=f'维度 {dim}', density=True)
            
            ax.set_title(f'{title} - 动作分布')
            ax.set_xlabel('动作值')
            ax.set_ylabel('密度')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # 3. 动作幅度时间序列
        for i, (results, title) in enumerate([(hmasd_results, 'HMASD'), 
                                             (true_random_results, '真随机')]):
            ax = axes[i, 2]
            
            actions = np.array(results['actions_history'])
            action_magnitudes = np.linalg.norm(actions, axis=2)  # (time, agents)
            
            for j in range(min(self.config.n_agents, 6)):  # 最多显示6个智能体
                ax.plot(action_magnitudes[:, j], 
                       color=colors[j % len(colors)], 
                       label=f'UAV {j}', alpha=0.7)
            
            ax.set_title(f'{title} - 动作幅度时间序列')
            ax.set_xlabel('时间步')
            ax.set_ylabel('动作幅度')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('debug_random_policy_comparison.png', dpi=150, bbox_inches='tight')
        print("对比图表已保存为: debug_random_policy_comparison.png")
        
        # 生成详细的动作分析图
        self._generate_action_analysis_plots(hmasd_results, true_random_results)
    
    def _generate_action_analysis_plots(self, hmasd_results, true_random_results):
        """生成详细的动作分析图表"""
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('动作模式深度分析', fontsize=16)
        
        # 1. 动作相关性矩阵
        hmasd_actions = np.array(hmasd_results['actions_history'])
        random_actions = np.array(true_random_results['actions_history'])
        
        # HMASD相关性
        hmasd_flat = hmasd_actions.reshape(-1, hmasd_actions.shape[-1])
        hmasd_corr = np.corrcoef(hmasd_flat.T)
        
        im1 = axes[0, 0].imshow(hmasd_corr, cmap='coolwarm', vmin=-1, vmax=1)
        axes[0, 0].set_title('HMASD动作维度相关性')
        axes[0, 0].set_xlabel('动作维度')
        axes[0, 0].set_ylabel('动作维度')
        plt.colorbar(im1, ax=axes[0, 0])
        
        # 真随机相关性
        random_flat = random_actions.reshape(-1, random_actions.shape[-1])
        random_corr = np.corrcoef(random_flat.T)
        
        im2 = axes[0, 1].imshow(random_corr, cmap='coolwarm', vmin=-1, vmax=1)
        axes[0, 1].set_title('真随机动作维度相关性')
        axes[0, 1].set_xlabel('动作维度')
        axes[0, 1].set_ylabel('动作维度')
        plt.colorbar(im2, ax=axes[0, 1])
        
        # 2. 时间一致性分析
        if hmasd_results['action_analysis']['temporal_consistency']:
            axes[1, 0].plot(hmasd_results['action_analysis']['temporal_consistency'], 
                           label='HMASD', color='blue', alpha=0.7)
            axes[1, 0].plot(true_random_results['action_analysis']['temporal_consistency'], 
                           label='真随机', color='red', alpha=0.7)
            axes[1, 0].set_title('动作时间一致性')
            axes[1, 0].set_xlabel('时间步')
            axes[1, 0].set_ylabel('连续动作相似度')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # 3. 动作方向分布（极坐标）
        ax_polar = plt.subplot(2, 2, 4, projection='polar')
        
        # 计算HMASD动作的方向角
        hmasd_directions = []
        for actions in hmasd_results['actions_history']:
            for action in actions:
                if np.linalg.norm(action[:2]) > 1e-6:  # 只考虑有意义的移动
                    angle = np.arctan2(action[1], action[0])
                    hmasd_directions.append(angle)
        
        # 计算真随机动作的方向角
        random_directions = []
        for actions in true_random_results['actions_history']:
            for action in actions:
                if np.linalg.norm(action[:2]) > 1e-6:
                    angle = np.arctan2(action[1], action[0])
                    random_directions.append(angle)
        
        # 绘制方向分布
        bins = np.linspace(-np.pi, np.pi, 36)
        hmasd_hist, _ = np.histogram(hmasd_directions, bins=bins)
        random_hist, _ = np.histogram(random_directions, bins=bins)
        
        bin_centers = (bins[:-1] + bins[1:]) / 2
        ax_polar.bar(bin_centers, hmasd_hist, width=2*np.pi/35, alpha=0.5, label='HMASD')
        ax_polar.bar(bin_centers, random_hist, width=2*np.pi/35, alpha=0.5, label='真随机')
        ax_polar.set_title('动作方向分布')
        ax_polar.legend()
        
        plt.tight_layout()
        plt.savefig('debug_action_analysis.png', dpi=150, bbox_inches='tight')
        print("动作分析图表已保存为: debug_action_analysis.png")
    
    def _save_debug_data(self, hmasd_results, true_random_results):
        """保存调试数据到JSON文件"""
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, (np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            else:
                return obj
        
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'n_agents': self.config.n_agents,
                'obs_dim': self.config.obs_dim,
                'action_dim': self.config.action_dim,
                'area_size': self.config.area_size,
                'use_obsnorm': self.config.use_obsnorm
            },
            'hmasd_results': {
                'straight_line_count': len(hmasd_results['straight_line_agents']),
                'straight_line_agents': convert_numpy_types(hmasd_results['straight_line_agents']),
                'action_stats': {
                    'mean': convert_numpy_types(np.mean(hmasd_results['actions_history'], axis=(0,1))),
                    'std': convert_numpy_types(np.std(hmasd_results['actions_history'], axis=(0,1))),
                    'min': convert_numpy_types(np.min(hmasd_results['actions_history'])),
                    'max': convert_numpy_types(np.max(hmasd_results['actions_history']))
                },
                'total_distances': convert_numpy_types(hmasd_results['total_distances']),
                'temporal_consistency': convert_numpy_types(hmasd_results['action_analysis']['temporal_consistency'])
            },
            'true_random_results': {
                'straight_line_count': len(true_random_results['straight_line_agents']),
                'straight_line_agents': convert_numpy_types(true_random_results['straight_line_agents']),
                'action_stats': {
                    'mean': convert_numpy_types(np.mean(true_random_results['actions_history'], axis=(0,1))),
                    'std': convert_numpy_types(np.std(true_random_results['actions_history'], axis=(0,1))),
                    'min': convert_numpy_types(np.min(true_random_results['actions_history'])),
                    'max': convert_numpy_types(np.max(true_random_results['actions_history']))
                },
                'total_distances': convert_numpy_types(true_random_results['total_distances']),
                'temporal_consistency': convert_numpy_types(true_random_results['action_analysis']['temporal_consistency'])
            }
        }
        
        with open('debug_random_policy_data.json', 'w') as f:
            json.dump(debug_data, f, indent=2)
        
        print("调试数据已保存为: debug_random_policy_data.json")
    
    def generate_recommendations(self):
        """基于分析结果生成修复建议"""
        
        print("\n" + "="*60)
        print("修复建议")
        print("="*60)
        
        print("\n如果HMASD策略存在直线移动问题，可以尝试以下修复方案:")
        
        print("\n1. 强制随机化修复:")
        print("   - 在HMASDAgent.step()中添加噪声注入")
        print("   - 重置GRU隐藏状态的频率")
        print("   - 使用更强的动作噪声")
        
        print("\n2. 网络初始化修复:")
        print("   - 使用Xavier或He初始化")
        print("   - 添加网络权重的随机扰动")
        print("   - 调整网络架构减少确定性")
        
        print("\n3. 观测处理修复:")
        print("   - 检查观测归一化是否过度平滑")
        print("   - 添加观测噪声增强随机性")
        print("   - 调整观测特征的权重")
        
        print("\n4. 技能机制修复:")
        print("   - 增加技能切换频率")
        print("   - 使用更随机的技能分配")
        print("   - 在未训练阶段禁用技能机制")

def main():
    """主函数"""
    print("开始随机策略调试分析...")
    
    debugger = RandomPolicyDebugger()
    
    try:
        # 运行对比测试
        debugger.run_comparison_test(episode_length=150)
        
        # 生成修复建议
        debugger.generate_recommendations()
        
        print("\n" + "="*60)
        print("调试分析完成!")
        print("生成的文件:")
        print("  - debug_random_policy_comparison.png (轨迹和动作对比)")
        print("  - debug_action_analysis.png (详细动作分析)")
        print("  - debug_random_policy_data.json (原始调试数据)")
        print("="*60)
        
    except Exception as e:
        print(f"调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
