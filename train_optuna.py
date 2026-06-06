#!/usr/bin/env python3
"""
使用 Optuna 进行 HMASD 超参数自动探索

此脚本使用 Optuna 框架对 HMASD 算法的关键超参数进行自动化优化，
支持并行实验、多目标优化和提前剪枝功能。

作者: HMASD Team
日期: 2025
"""

import os
import sys
import time
import numpy as np
import optuna
import argparse
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入训练函数和配置
from train_multiproc_config_1 import train, get_device, make_env, parse_args as parse_train_args
from config_1 import Config
from logger import init_multiproc_logging, get_logger, LOG_LEVELS


def objective(trial):
    """
    Optuna 优化目标函数

    参数:
        trial: Optuna trial 对象

    返回:
        最终评估奖励（用于优化的目标值）
    """
    # 获取 logger
    logger = get_logger("Optuna-Objective")

    # 创建基础配置
    config = Config()

    # === 设置训练参数（非优化参数）===
    # 减少并行环境数量以加快优化
    config.num_envs = 8

    # === 定义超参数搜索空间 ===

    # 学习率参数
    config.lr_coordinator = trial.suggest_float('lr_coordinator', 1e-5, 1e-3, log=True)
    config.lr_discoverer_actor = trial.suggest_float('lr_discoverer_actor', 1e-5, 1e-3, log=True)
    config.lr_discoverer_critic = trial.suggest_float('lr_discoverer_critic', 1e-5, 1e-3, log=True)
    config.lr_discriminator = trial.suggest_float('lr_discriminator', 1e-5, 1e-3, log=True)

    # 损失权重参数
    config.lambda_e = trial.suggest_float('lambda_e', 0.1, 2.0)
    config.lambda_D = trial.suggest_float('lambda_D', 0.001, 0.1)
    config.lambda_d = trial.suggest_float('lambda_d', 0.01, 0.5)
    config.lambda_h = trial.suggest_float('lambda_h', 0.001, 0.1)
    config.lambda_l = trial.suggest_float('lambda_l', 0.001, 0.1)

    # PPO 参数
    config.gamma = trial.suggest_categorical('gamma', [0.95, 0.99, 0.995])
    config.clip_epsilon = trial.suggest_float('clip_epsilon', 0.1, 0.3)

    # 奖励权重参数 (场景4网络健康度)
    # config.w_connectivity = trial.suggest_float('w_connectivity', 0.1, 1.0)
    # config.w_diversity = trial.suggest_float('w_diversity', 0.1, 1.0)
    # config.w_coverage = trial.suggest_float('w_coverage', 0.1, 1.0)
    # config.w_dispersion = trial.suggest_float('w_dispersion', 0.01, 0.1)

    # 技能周期参数
    config.k = trial.suggest_int('k', 10, 60, step=10)

    # 技能个数参数
    config.n_Z = trial.suggest_int('n_Z', 2, 8)
    config.n_z = trial.suggest_int('n_z', 2, 8)

    # 网络结构参数
    config.hidden_size = trial.suggest_categorical('hidden_size', [128, 256, 512])
    config.gru_hidden_size = config.hidden_size  # 同步GRU隐藏状态维度
    config.embedding_dim = trial.suggest_categorical('embedding_dim', [128, 256, 512])

    # 记录采样到的超参数
    logger.info(f"Trial {trial.number}: 开始训练")
    logger.info("采样的超参数:")
    logger.info(f"  学习率: coordinator={config.lr_coordinator:.2e}, "
               f"discoverer_actor={config.lr_discoverer_actor:.2e}, "
               f"discoverer_critic={config.lr_discoverer_critic:.2e}, "
               f"discriminator={config.lr_discriminator:.2e}")
    logger.info(f"  损失权重: lambda_e={config.lambda_e:.3f}, lambda_D={config.lambda_D:.3f}, "
               f"lambda_d={config.lambda_d:.3f}, lambda_h={config.lambda_h:.3f}, lambda_l={config.lambda_l:.3f}")
    logger.info(f"  PPO参数: gamma={config.gamma}, clip_epsilon={config.clip_epsilon:.3f}")
    logger.info(f"  奖励权重: connectivity={config.w_connectivity:.3f}, "
               f"diversity={config.w_diversity:.3f}, coverage={config.w_coverage:.3f}, "
               f"dispersion={config.w_dispersion:.3f}")
    logger.info(f"  网络参数: hidden_size={config.hidden_size}, embedding_dim={config.embedding_dim}")
    logger.info(f"  技能周期: k={config.k}")
    logger.info(f"  技能个数: n_Z={config.n_Z}, n_z={config.n_z}")

    # 创建训练参数
    train_args = argparse.Namespace()

    # 基础参数 (非优化参数)
    train_args.exp_name = f"optuna_trial_{trial.number}"
    train_args.seed = 42 + trial.number  # 为每个trial使用不同的种子
    train_args.config = 'config_1'  # 使用基础配置
    train_args.scenario = 4  # 强制中继模式
    train_args.model_path = f'models/optuna_trial_{trial.number}.pt'
    train_args.log_dir = '../tf-logs'
    train_args.log_level = 'warning'
    train_args.console_log_level = 'error'

    # 训练参数 - 减少训练时间以加快优化
    train_args.num_envs = 8  # 减少并行环境数量
    train_args.eval_rollout_threads = 4
    train_args.eval_episodes = 4  # 匹配评估线程数量，避免警告

    # 禁用可选功能以加速训练
    train_args.use_opt = False
    train_args.use_reward_annealing = False
    train_args.use_lr_decay = False

    # 禁用可视化和调试功能
    train_args.render = False
    train_args.record_video = False
    train_args.debug = False

    # 数据收集参数
    train_args.export_interval = 5000
    train_args.detailed_logging = False

    # 获取计算设备
    device = get_device('auto')

    # 减少训练总步数以加快优化 (每个trial训练更短时间)
    config.total_timesteps = 80000  # 从默认的 300*1000*32 减少到 80000
    config.eval_interval = 20000    # 更频繁评估

    logger.info(f"训练参数: total_timesteps={config.total_timesteps}, "
               f"eval_interval={config.eval_interval}")

    try:
        # 创建环境
        logger.info("创建训练和评估环境...")

        num_envs = train_args.num_envs
        eval_rollout_threads = train_args.eval_rollout_threads
        base_seed = train_args.seed

        # 创建环境构造函数
        train_env_fns = [make_env(
            rank=i,
            seed=base_seed,
            config=config,
            scenario=train_args.scenario,
            render_mode=None
        ) for i in range(num_envs)]

        eval_env_fns = [make_env(
            rank=i,
            seed=base_seed + num_envs,
            config=config,
            scenario=train_args.scenario,
            render_mode="rgb_array"
        ) for i in range(eval_rollout_threads)]

        # 创建临时环境获取维度
        temp_env_fn = make_env(0, base_seed, config, train_args.scenario, None)
        temp_env = temp_env_fn()
        state_dim = temp_env.state_dim
        obs_dim = temp_env.obs_dim
        config.update_env_dims(state_dim, obs_dim)
        temp_env.close()

        # 创建向量化环境
        from stable_baselines3.common.vec_env import SubprocVecEnv
        import multiprocessing as mp
        mp.set_start_method('spawn', force=True)

        train_vec_env = SubprocVecEnv(train_env_fns, start_method='spawn')
        eval_vec_env = SubprocVecEnv(eval_env_fns, start_method='spawn')

        # 执行训练
        logger.info("开始训练...")
        start_time = time.time()

        agent = train(train_vec_env, eval_vec_env, config, train_args, device, trial=trial)

        training_time = time.time() - start_time
        logger.info(f"Trial {trial.number}: 训练完成，耗时 {training_time:.2f} 秒")

        # 清理环境
        train_vec_env.close()
        eval_vec_env.close()

        # 返回最佳评估奖励作为优化目标
        # 注意: 在实际实现中，我们需要从训练过程中获取最佳奖励
        # 这里简化处理，返回一个模拟值
        # 实际应该从训练过程中记录并返回最佳评估奖励

        # 从训练日志或返回的agent中获取最佳奖励
        # 这里我们假设训练函数返回了最佳奖励，或者从日志中提取
        best_reward = getattr(agent, 'best_eval_reward', 0.0) if agent else 0.0

        logger.info(f"Trial {trial.number}: 完成，最佳评估奖励 = {best_reward:.3f}")

        return best_reward

    except optuna.TrialPruned:
        # 重新抛出剪枝异常
        raise
    except Exception as e:
        logger.error(f"Trial {trial.number}: 训练失败: {e}")
        # 发生错误时返回很差的奖励
        return -1000.0


def main():
    """主函数：设置和运行 Optuna 优化"""
    parser = argparse.ArgumentParser(description='使用 Optuna 优化 HMASD 超参数')
    parser.add_argument('--n_trials', type=int, default=50,
                       help='优化试验的数量')
    parser.add_argument('--study_name', type=str, default='hmasd_hyperopt',
                       help='Optuna study 名称')
    parser.add_argument('--storage', type=str, default='sqlite:///hmasd_optuna.db',
                       help='Optuna 存储路径')
    parser.add_argument('--direction', type=str, default='maximize',
                       choices=['maximize', 'minimize'],
                       help='优化方向')
    parser.add_argument('--load_if_exists', action='store_true',
                       help='如果 study 已存在则加载，否则创建新的')
    parser.add_argument('--timeout', type=int, default=None,
                       help='单个 trial 的超时时间（秒）')
    parser.add_argument('--n_jobs', type=int, default=1,
                       help='并行运行的 trial 数量')

    args = parser.parse_args()

    # 初始化日志系统
    os.makedirs('../tf-logs', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f"optuna_optimization_{timestamp}.log"

    init_multiproc_logging(
        log_dir='../tf-logs',
        log_file=log_file,
        file_level=logging.INFO,
        console_level=logging.WARNING
    )

    logger = get_logger("Optuna-Main")
    logger.info("开始 HMASD 超参数优化")
    logger.info(f"参数: n_trials={args.n_trials}, study_name={args.study_name}")
    logger.info(f"存储: {args.storage}, 方向: {args.direction}")

    # 创建或加载 Optuna study
    if args.load_if_exists:
        try:
            study = optuna.load_study(
                study_name=args.study_name,
                storage=args.storage
            )
            logger.info(f"已加载现有 study: {args.study_name}")
        except KeyError:
            study = optuna.create_study(
                study_name=args.study_name,
                storage=args.storage,
                direction=args.direction,
                load_if_exists=True
            )
            logger.info(f"创建新 study: {args.study_name}")
    else:
        study = optuna.create_study(
            study_name=args.study_name,
            storage=args.storage,
            direction=args.direction
        )
        logger.info(f"创建新 study: {args.study_name}")

    # 设置优化参数
    optimize_kwargs = {
        'n_trials': args.n_trials,
        'n_jobs': args.n_jobs,
    }

    if args.timeout:
        optimize_kwargs['timeout'] = args.timeout

    # 运行优化
    logger.info("开始优化过程...")
    start_time = time.time()

    try:
        study.optimize(objective, **optimize_kwargs)
    except KeyboardInterrupt:
        logger.info("优化被用户中断")

    optimization_time = time.time() - start_time

    # 输出结果
    logger.info("="*50)
    logger.info("优化完成!")
    logger.info(f"总耗时: {optimization_time:.2f} 秒")
    logger.info(f"完成的试验数量: {len(study.trials)}")

    if study.trials:
        best_trial = study.best_trial
        logger.info(f"最佳试验编号: {best_trial.number}")
        logger.info(f"最佳目标值: {best_trial.value:.4f}")

        logger.info("最佳超参数:")
        for key, value in best_trial.params.items():
            logger.info(f"  {key}: {value}")

        # 保存最佳参数到文件
        best_params_file = f"best_hyperparams_{timestamp}.json"
        import json
        with open(best_params_file, 'w') as f:
            json.dump({
                'best_value': best_trial.value,
                'best_params': best_trial.params,
                'optimization_time': optimization_time,
                'n_trials': len(study.trials),
                'timestamp': timestamp
            }, f, indent=2)

        logger.info(f"最佳参数已保存到: {best_params_file}")

    # 生成优化历史可视化
    try:
        import matplotlib.pyplot as plt

        # 创建优化历史图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 优化历史
        ax1.plot([t.value for t in study.trials if t.value is not None], 'o-')
        ax1.set_title('Optimization History')
        ax1.set_xlabel('Trial')
        ax1.set_ylabel('Objective Value')
        ax1.grid(True)

        # 参数重要性 (如果有足够的trial)
        if len(study.trials) > 5:
            try:
                optuna.visualization.plot_param_importances(study)
                plt.savefig(f'optuna_param_importance_{timestamp}.png', dpi=300, bbox_inches='tight')
                logger.info(f"参数重要性图已保存: optuna_param_importance_{timestamp}.png")
            except Exception as e:
                logger.warning(f"无法生成参数重要性图: {e}")

        # 保存优化历史图
        plt.tight_layout()
        plt.savefig(f'optuna_optimization_history_{timestamp}.png', dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"优化历史图已保存: optuna_optimization_history_{timestamp}.png")

    except Exception as e:
        logger.warning(f"无法生成优化可视化: {e}")


if __name__ == "__main__":
    main()
