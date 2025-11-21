import subprocess
import time
import os

# --- 实验配置 ---
EXP_NAME = "scenario4_final_results_by_config"
CONFIGS = ["config_1", "config_1_optimized"]  # 在这里列出您要运行的所有配置文件名
SEED = 42  # 为所有配置使用固定的种子
LOG_DIR = "../tf-logs"
SCENARIO = 4
MAX_CONCURRENT_RUNS = 3  # 根据您的机器CPU核心数和内存来设置

# --- 算法参数 ---
# 这个字典可以保留，以防您想对某些配置应用额外的、覆盖性的命令行参数
EXPERIMENTS = {
    "hmasd": [
        # No extra arguments are passed to use the default parameters from the training script.
    ],
}

def run_parallel_experiments():
    processes = []
    for alg_name, alg_args in EXPERIMENTS.items():
        for config_name in CONFIGS:
            # 等待直到有可用的进程槽位
            while len(processes) >= MAX_CONCURRENT_RUNS:
                # 检查已完成的进程并移除
                processes = [p for p in processes if p.poll() is None]
                time.sleep(5)

            command = [
                'python',
                'train_multiproc_config_1.py',
                '--scenario', str(SCENARIO),
                '--log_dir', LOG_DIR,
                '--exp_name', f"{EXP_NAME}/{config_name}", # 使用config名来区分实验
                '--seed', str(SEED),
                '--config', config_name  # 传入配置文件名
            ] + alg_args
            
            print(f"\n>>> Starting: {alg_name.upper()} with Config '{config_name}'")
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
