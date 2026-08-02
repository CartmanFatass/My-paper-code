"""Launch the scenario-4 experiment matrix from any working directory.

Run as ``python -m experiments.launchers.run_experiment_parallel``.
"""

import subprocess
import time
import os
from pathlib import Path

# --- 实验配置 ---
EXP_NAME = "scenario4_final_results"
SEEDS = [10, 20, 30, 40, 50]
LOG_DIR = "../tf-logs"
SCENARIO = 4
MAX_CONCURRENT_RUNS = 3  # 根据您的机器CPU核心数和内存来设置

# --- 算法参数 ---
# 将所有算法的配置放入一个字典中，方便扩展
EXPERIMENTS = {
    "hmasd": [
        # No extra arguments are passed to use the default parameters from the training script.
    ],
    # "mappo_baseline": [
    #     '--disable_hmasd_features' # 假设有这样一个参数
    # ]
}

TRAIN_ENTRYPOINT = Path(__file__).resolve().parents[2] / "train_multiproc_config_1.py"


def build_command(alg_name, alg_args, seed):
    return [
        'python',
        str(TRAIN_ENTRYPOINT),
        '--scenario', str(SCENARIO),
        '--log_dir', LOG_DIR,
        '--exp_name', f"{EXP_NAME}/{alg_name}",
        '--seed', str(seed)
    ] + alg_args

def run_parallel_experiments():
    processes = []
    for alg_name, alg_args in EXPERIMENTS.items():
        for seed in SEEDS:
            # 等待直到有可用的进程槽位
            while len(processes) >= MAX_CONCURRENT_RUNS:
                # 检查已完成的进程并移除
                processes = [p for p in processes if p.poll() is None]
                time.sleep(5)

            command = build_command(alg_name, alg_args, seed)
            
            print(f"\n>>> Starting: {alg_name.upper()} with Seed {seed}")
            print(f"    Command: {' '.join(command)}")
            
            # 启动子进程，不阻塞
            process = subprocess.Popen(command)
            processes.append(process)
            time.sleep(1) # 短暂间隔以避免同时启动过多进程导致资源竞争

    # 等待所有剩余的进程完成
    print("\nAll experiments launched. Waiting for completion...")
    for p in processes:
        p.wait()

    print("\nAll experiments have completed!")
    print(f"Data is available in: {os.path.join(LOG_DIR, EXP_NAME)}")

if __name__ == "__main__":
    run_parallel_experiments()
