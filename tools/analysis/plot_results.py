import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse
import glob

def plot_results(exp_dir, title='Learning Curves', save_path='learning_curve.png'):
    """
    加载、聚合和绘制多个随机种子的实验结果。
    
    参数:
        exp_dir: 包含多个算法结果的实验目录 (e.g., '../tf-logs/scenario4_vs_mappo')
        title: 图表标题
        save_path: 图像保存路径
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 获取实验目录下的所有算法子目录
    alg_dirs = [d for d in os.listdir(exp_dir) if os.path.isdir(os.path.join(exp_dir, d))]
    
    for alg_name in alg_dirs:
        alg_path = os.path.join(exp_dir, alg_name)
        
        # 查找该算法所有种子的评估数据文件
        csv_files = glob.glob(os.path.join(alg_path, 'seed_*', 'evaluation_performance_data.csv'))
        
        if not csv_files:
            print(f"警告: 在 {alg_path} 中未找到 'evaluation_performance_data.csv' 文件")
            continue
            
        all_data = []
        for f in csv_files:
            try:
                df = pd.read_csv(f)
                # 添加种子信息用于调试
                seed = os.path.basename(os.path.dirname(f))
                df['seed'] = seed
                all_data.append(df)
            except pd.errors.EmptyDataError:
                print(f"警告: 文件为空，跳过: {f}")

        if not all_data:
            continue

        # 合并所有种子数据
        full_df = pd.concat(all_data, ignore_index=True)
        
        # 使用seaborn自动计算均值和95%置信区间并绘图
        sns.lineplot(
            data=full_df,
            x='steps',
            y='mean_reward',
            label=alg_name.upper(), # 算法名称作为图例
            ax=ax,
            linewidth=2.5
        )
        
    # --- 格式化图表 ---
    ax.set_title(title, fontsize=20, fontweight='bold')
    ax.set_xlabel('Training Timesteps', fontsize=16)
    ax.set_ylabel('Mean Evaluation Reward', fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.legend(fontsize=14)
    
    # 格式化x轴为科学计数法
    ax.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"图表已保存至: {save_path}")
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_dir', type=str, required=True, help='实验目录路径')
    args = parser.parse_args()
    
    # 生成图表标题和保存路径
    exp_name = os.path.basename(args.exp_dir)
    plot_title = f"Performance on {exp_name.replace('_', ' ').title()}"
    save_file = os.path.join(args.exp_dir, f"{exp_name}_learning_curve.png")
    
    plot_results(args.exp_dir, title=plot_title, save_path=save_file)
