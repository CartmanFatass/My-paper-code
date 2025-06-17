#!/usr/bin/env python3
"""
独立的训练数据可视化脚本
用于在训练完成后生成图表，避免训练过程中的内存问题
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
import argparse
from datetime import datetime

def load_training_data(log_dir):
    """加载训练数据"""
    paper_data_dir = os.path.join(log_dir, 'paper_data')
    
    if not os.path.exists(paper_data_dir):
        print(f"错误: 找不到paper_data目录: {paper_data_dir}")
        return None
    
    data = {
        'episode_rewards': [],
        'reward_components': [],
        'skill_usage': []
    }
    
    # 加载所有CSV和JSON文件
    for filename in os.listdir(paper_data_dir):
        filepath = os.path.join(paper_data_dir, filename)
        
        if filename.startswith('episode_rewards_step_') and filename.endswith('.csv'):
            try:
                df = pd.read_csv(filepath)
                data['episode_rewards'].append(df)
                print(f"加载奖励数据: {filename} ({len(df)} 条记录)")
            except Exception as e:
                print(f"加载 {filename} 失败: {e}")
        
        elif filename.startswith('reward_components_step_') and filename.endswith('.csv'):
            try:
                df = pd.read_csv(filepath)
                data['reward_components'].append(df)
                print(f"加载奖励组件数据: {filename} ({len(df)} 条记录)")
            except Exception as e:
                print(f"加载 {filename} 失败: {e}")
        
        elif filename.startswith('skill_usage_step_') and filename.endswith('.json'):
            try:
                with open(filepath, 'r') as f:
                    skill_data = json.load(f)
                    skill_data['step'] = int(filename.split('_')[-1].split('.')[0])
                    data['skill_usage'].append(skill_data)
                print(f"加载技能使用数据: {filename}")
            except Exception as e:
                print(f"加载 {filename} 失败: {e}")
    
    # 合并数据
    if data['episode_rewards']:
        data['episode_rewards'] = pd.concat(data['episode_rewards'], ignore_index=True)
        data['episode_rewards'] = data['episode_rewards'].sort_values('episode')
    
    if data['reward_components']:
        data['reward_components'] = pd.concat(data['reward_components'], ignore_index=True)
        data['reward_components'] = data['reward_components'].sort_values('step')
    
    if data['skill_usage']:
        data['skill_usage'] = sorted(data['skill_usage'], key=lambda x: x['step'])
    
    return data

def generate_episode_reward_plots(data, output_dir):
    """生成episode奖励相关图表"""
    if data['episode_rewards'].empty:
        print("警告: 没有episode奖励数据")
        return
    
    episodes = data['episode_rewards']['episode'].values
    rewards = data['episode_rewards']['total_reward'].values
    lengths = data['episode_rewards']['episode_length'].values
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('训练过程奖励分析', fontsize=16)
    
    # 1. 原始奖励曲线
    axes[0, 0].plot(episodes, rewards, alpha=0.3, color='blue', label='Episode Rewards')
    # 滑动平均
    if len(rewards) >= 50:
        window = min(50, len(rewards) // 2)
        smoothed = pd.Series(rewards).rolling(window=window, center=True).mean()
        axes[0, 0].plot(episodes, smoothed, color='red', linewidth=2, label=f'{window}-episode 滑动平均')
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('总奖励')
    axes[0, 0].set_title('训练奖励进展')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 奖励分布直方图
    axes[0, 1].hist(rewards, bins=min(50, len(rewards)//10), alpha=0.7, color='green')
    axes[0, 1].set_xlabel('总奖励')
    axes[0, 1].set_ylabel('频次')
    axes[0, 1].set_title('奖励分布')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Episode长度趋势
    axes[1, 0].plot(episodes, lengths, alpha=0.6, color='orange', label='Episode 长度')
    if len(lengths) >= 20:
        window = min(20, len(lengths) // 2)
        smoothed_lengths = pd.Series(lengths).rolling(window=window, center=True).mean()
        axes[1, 0].plot(episodes, smoothed_lengths, color='darkred', linewidth=2, label=f'{window}-episode 滑动平均')
    axes[1, 0].set_xlabel('Episode')
    axes[1, 0].set_ylabel('Episode 长度')
    axes[1, 0].set_title('Episode 长度进展')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 奖励统计分析
    window_size = 100
    if len(rewards) >= window_size:
        rolling_mean = pd.Series(rewards).rolling(window=window_size).mean()
        rolling_std = pd.Series(rewards).rolling(window=window_size).std()
        
        axes[1, 1].plot(episodes, rolling_mean, color='purple', label=f'{window_size}-episode 滑动平均')
        axes[1, 1].fill_between(episodes, 
                               rolling_mean - rolling_std, 
                               rolling_mean + rolling_std, 
                               alpha=0.3, color='purple', label=f'± 标准差')
        axes[1, 1].set_xlabel('Episode')
        axes[1, 1].set_ylabel('奖励')
        axes[1, 1].set_title(f'奖励稳定性 ({window_size}-episode 窗口)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, '数据不足\n(需要至少100个episodes)', 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('奖励稳定性分析')
    
    plt.tight_layout()
    
    # 保存图表 - 使用较低的DPI以减少内存使用
    output_path = os.path.join(output_dir, 'training_progress_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"已保存训练进展图表: {output_path}")

def generate_reward_components_plots(data, output_dir):
    """生成奖励组件分析图表"""
    if data['reward_components'].empty:
        print("警告: 没有奖励组件数据")
        return
    
    components_data = data['reward_components']
    components = components_data['component'].unique()
    
    if len(components) == 0:
        print("警告: 没有找到奖励组件")
        return
    
    fig, axes = plt.subplots(1, len(components), figsize=(5*len(components), 5))
    if len(components) == 1:
        axes = [axes]
    
    fig.suptitle('奖励组件分析', fontsize=16)
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, component in enumerate(components):
        comp_data = components_data[components_data['component'] == component]
        steps = comp_data['step'].values
        values = comp_data['value'].values
        
        color = colors[i % len(colors)]
        axes[i].plot(steps, values, alpha=0.6, color=color, label=component)
        
        # 添加滑动平均
        if len(values) >= 20:
            window = min(50, len(values) // 4)
            smoothed = pd.Series(values).rolling(window=window, center=True).mean()
            axes[i].plot(steps, smoothed, color='black', linewidth=2, label=f'{window}-step 滑动平均')
        
        axes[i].set_xlabel('训练步数')
        axes[i].set_ylabel('奖励组件值')
        axes[i].set_title(f'{component.replace("_", " ").title()}')
        axes[i].legend()
        axes[i].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(output_dir, 'reward_components_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"已保存奖励组件图表: {output_path}")

def generate_skill_usage_plots(data, output_dir):
    """生成技能使用分析图表"""
    if not data['skill_usage']:
        print("警告: 没有技能使用数据")
        return
    
    # 提取技能使用数据
    steps = [item['step'] for item in data['skill_usage']]
    team_skills_over_time = []
    skill_switches_over_time = []
    
    all_team_skills = set()
    for item in data['skill_usage']:
        if 'team_skills' in item:
            all_team_skills.update(item['team_skills'].keys())
        team_skills_over_time.append(item.get('team_skills', {}))
        skill_switches_over_time.append(item.get('skill_switches', 0))
    
    if not all_team_skills:
        print("警告: 没有找到团队技能数据")
        return
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('技能使用分析', fontsize=16)
    
    # 1. 技能切换次数趋势
    axes[0, 0].plot(steps, skill_switches_over_time, color='red', marker='o', markersize=3)
    axes[0, 0].set_xlabel('训练步数')
    axes[0, 0].set_ylabel('累积技能切换次数')
    axes[0, 0].set_title('技能切换趋势')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 最终技能使用分布
    if team_skills_over_time:
        final_skills = team_skills_over_time[-1]
        if final_skills:
            skills = list(final_skills.keys())
            counts = list(final_skills.values())
            axes[0, 1].bar(skills, counts, alpha=0.7, color='orange')
            axes[0, 1].set_xlabel('团队技能ID')
            axes[0, 1].set_ylabel('使用次数')
            axes[0, 1].set_title('最终技能使用分布')
            axes[0, 1].grid(True, alpha=0.3)
        else:
            axes[0, 1].text(0.5, 0.5, '没有技能使用数据', ha='center', va='center', transform=axes[0, 1].transAxes)
    
    # 3. 技能使用演变热图
    if len(team_skills_over_time) > 1 and all_team_skills:
        skill_matrix = []
        sorted_skills = sorted(all_team_skills)
        
        for skills_dict in team_skills_over_time:
            row = [skills_dict.get(skill, 0) for skill in sorted_skills]
            skill_matrix.append(row)
        
        skill_matrix = np.array(skill_matrix).T
        
        if skill_matrix.size > 0:
            im = axes[1, 0].imshow(skill_matrix, aspect='auto', cmap='viridis', interpolation='nearest')
            axes[1, 0].set_xlabel('时间步骤索引')
            axes[1, 0].set_ylabel('技能ID')
            axes[1, 0].set_title('技能使用演变热图')
            axes[1, 0].set_yticks(range(len(sorted_skills)))
            axes[1, 0].set_yticklabels(sorted_skills)
            plt.colorbar(im, ax=axes[1, 0], label='使用次数')
    
    # 4. 技能多样性指标
    diversity_scores = []
    for skills_dict in team_skills_over_time:
        if skills_dict:
            total_usage = sum(skills_dict.values())
            if total_usage > 0:
                # 计算香农熵作为多样性指标
                probs = [count/total_usage for count in skills_dict.values()]
                entropy = -sum(p * np.log(p + 1e-8) for p in probs if p > 0)
                diversity_scores.append(entropy)
            else:
                diversity_scores.append(0)
        else:
            diversity_scores.append(0)
    
    if diversity_scores:
        axes[1, 1].plot(steps, diversity_scores, color='purple', marker='o', markersize=3)
        axes[1, 1].set_xlabel('训练步数')
        axes[1, 1].set_ylabel('技能多样性 (熵)')
        axes[1, 1].set_title('技能多样性演变')
        axes[1, 1].grid(True, alpha=0.3)
    else:
        axes[1, 1].text(0.5, 0.5, '无法计算多样性', ha='center', va='center', transform=axes[1, 1].transAxes)
    
    plt.tight_layout()
    
    # 保存图表
    output_path = os.path.join(output_dir, 'skill_usage_analysis.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"已保存技能使用图表: {output_path}")

def generate_summary_report(data, output_dir):
    """生成训练摘要报告"""
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("训练数据分析摘要报告")
    report_lines.append("=" * 60)
    report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Episode统计
    if not data['episode_rewards'].empty:
        rewards = data['episode_rewards']['total_reward'].values
        lengths = data['episode_rewards']['episode_length'].values
        episodes = data['episode_rewards']['episode'].values
        
        report_lines.append("Episode统计:")
        report_lines.append(f"  总episodes数: {len(episodes)}")
        report_lines.append(f"  平均奖励: {np.mean(rewards):.4f} ± {np.std(rewards):.4f}")
        report_lines.append(f"  最大奖励: {np.max(rewards):.4f}")
        report_lines.append(f"  最小奖励: {np.min(rewards):.4f}")
        report_lines.append(f"  平均episode长度: {np.mean(lengths):.2f}")
        report_lines.append("")
        
        # 最近100个episodes的统计
        if len(rewards) >= 100:
            recent_rewards = rewards[-100:]
            report_lines.append("最近100个episodes统计:")
            report_lines.append(f"  平均奖励: {np.mean(recent_rewards):.4f} ± {np.std(recent_rewards):.4f}")
            report_lines.append(f"  最大奖励: {np.max(recent_rewards):.4f}")
            report_lines.append(f"  最小奖励: {np.min(recent_rewards):.4f}")
            report_lines.append("")
    
    # 技能使用统计
    if data['skill_usage']:
        final_skill_data = data['skill_usage'][-1]
        report_lines.append("技能使用统计:")
        report_lines.append(f"  总技能切换次数: {final_skill_data.get('skill_switches', 0)}")
        
        if 'team_skills' in final_skill_data and final_skill_data['team_skills']:
            team_skills = final_skill_data['team_skills']
            total_usage = sum(team_skills.values())
            report_lines.append(f"  团队技能总使用次数: {total_usage}")
            report_lines.append("  团队技能分布:")
            for skill_id, count in sorted(team_skills.items()):
                percentage = (count / total_usage) * 100 if total_usage > 0 else 0
                report_lines.append(f"    技能 {skill_id}: {count} 次 ({percentage:.1f}%)")
        report_lines.append("")
    
    # 数据收集统计
    report_lines.append("数据收集统计:")
    report_lines.append(f"  奖励数据记录数: {len(data['episode_rewards'])}")
    report_lines.append(f"  奖励组件数据记录数: {len(data['reward_components'])}")
    report_lines.append(f"  技能使用快照数: {len(data['skill_usage'])}")
    
    # 保存报告
    report_path = os.path.join(output_dir, 'training_analysis_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"已保存分析报告: {report_path}")
    
    # 同时打印到控制台
    print("\n" + "\n".join(report_lines))

def main():
    parser = argparse.ArgumentParser(description='生成训练数据可视化图表')
    parser.add_argument('log_dir', help='训练日志目录路径')
    parser.add_argument('--output_dir', help='输出目录 (默认为log_dir/analysis)')
    parser.add_argument('--dpi', type=int, default=150, help='图像DPI (默认: 150)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.log_dir):
        print(f"错误: 日志目录不存在: {args.log_dir}")
        return
    
    # 设置输出目录
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(args.log_dir, 'analysis')
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    
    # 加载数据
    print("正在加载训练数据...")
    data = load_training_data(args.log_dir)
    
    if data is None:
        print("加载数据失败")
        return
    
    # 生成图表
    print("\n正在生成图表...")
    
    try:
        generate_episode_reward_plots(data, output_dir)
    except Exception as e:
        print(f"生成奖励图表时出错: {e}")
    
    try:
        generate_reward_components_plots(data, output_dir)
    except Exception as e:
        print(f"生成奖励组件图表时出错: {e}")
    
    try:
        generate_skill_usage_plots(data, output_dir)
    except Exception as e:
        print(f"生成技能使用图表时出错: {e}")
    
    try:
        generate_summary_report(data, output_dir)
    except Exception as e:
        print(f"生成摘要报告时出错: {e}")
    
    print(f"\n分析完成！所有文件已保存到: {output_dir}")

if __name__ == "__main__":
    main()
