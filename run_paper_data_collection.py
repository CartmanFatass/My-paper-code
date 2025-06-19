#!/usr/bin/env python3
"""
运行论文数据收集的示例脚本

这个脚本展示了如何使用优化后的训练系统来收集论文数据
"""

import subprocess
import sys
import os
from datetime import datetime

def run_training_experiment(experiment_name, **kwargs):
    """运行训练实验"""
    
    # 基础命令
    cmd = [
        sys.executable, 'train_multiproc_paper_data_collection.py',
        '--mode', 'train'
    ]
    
    # 添加参数
    for key, value in kwargs.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f'--{key}')
        else:
            cmd.extend([f'--{key}', str(value)])
    
    print(f"\n{'='*60}")
    print(f"开始实验: {experiment_name}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)
    
    try:
        # 运行训练
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n实验 '{experiment_name}' 完成成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n实验 '{experiment_name}' 失败，错误码: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n实验 '{experiment_name}' 被用户中断")
        return False

def main():
    """运行一系列论文数据收集实验"""
    
    print("开始论文数据收集实验系列...")
    
    # 实验1: 32环境，默认参数
    success1 = run_training_experiment(
        "基准实验_32环境",
        num_envs=32,
        n_uavs=5,
        n_users=50,
        scenario=2,
        channel_model='3gpp-36777',
        user_distribution='uniform',
        log_level='info',
        console_log_level='warning'
    )
    
    # 实验2: 128环境，高并行度
    if success1:
        success2 = run_training_experiment(
            "高并行实验_128环境",
            num_envs=128,
            n_uavs=5,
            n_users=50,
            scenario=2,
            channel_model='3gpp-36777',
            user_distribution='uniform',
            log_level='info',
            console_log_level='warning'
        )
    
    # 实验3: 不同用户分布
    if success1:
        success3 = run_training_experiment(
            "聚类分布实验",
            num_envs=32,
            n_uavs=5,
            n_users=50,
            scenario=2,
            channel_model='3gpp-36777',
            user_distribution='cluster',
            log_level='info',
            console_log_level='warning'
        )
    
    # 实验4: 不同无人机数量
    if success1:
        success4 = run_training_experiment(
            "更多无人机实验",
            num_envs=32,
            n_uavs=8,
            n_users=80,
            scenario=2,
            channel_model='3gpp-36777',
            user_distribution='uniform',
            log_level='info',
            console_log_level='warning'
        )
    
    print("\n" + "="*60)
    print("所有实验完成！")
    print("数据文件位置:")
    print("  - TensorBoard日志: logs/paper_data_collection_*/")
    print("  - CSV数据文件: logs/paper_data_collection_*/paper_data/")
    print("  - 最终摘要: logs/paper_data_collection_*/final_summary.json")
    print("="*60)

if __name__ == "__main__":
    main()
