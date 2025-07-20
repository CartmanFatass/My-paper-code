#!/usr/bin/env python
import sys
import os
import socket
import setproctitle
import numpy as np
from pathlib import Path
import torch

from mat.config import get_config
from mat.envs.uav_communication.uav_comm_env import make_uav_comm_env
from mat.algorithms.mat.mat_trainer import MATTrainer as TrainAlgo
from mat.runner.shared.base_runner import Runner


def make_train_env(all_args):
    """创建训练环境"""
    def get_env_fn(rank):
        def init_env():
            env = make_uav_comm_env(all_args.scenario_name, all_args)
            return env
        return init_env
    
    if all_args.n_rollout_threads == 1:
        return get_env_fn(0)()
    else:
        return get_env_fn

def make_eval_env(all_args):
    """创建评估环境"""
    def get_env_fn(rank):
        def init_env():
            env = make_uav_comm_env(all_args.scenario_name, all_args)
            return env
        return init_env
    
    if all_args.n_eval_rollout_threads == 1:
        return get_env_fn(0)()
    else:
        return get_env_fn

def parse_args(args, parser):
    """解析参数"""
    parser.add_argument('--scenario_name', type=str, default='multi_role_uav',
                        help="UAV通信环境的场景名称")
    parser.add_argument('--num_uavs', type=int, default=10, 
                        help="无人机数量")
    parser.add_argument('--num_gbs', type=int, default=3, 
                        help="地面基站数量")
    parser.add_argument('--num_ues', type=int, default=50, 
                        help="用户设备数量") 
    parser.add_argument('--area_size', type=float, default=1000.0, 
                        help="区域大小（米）")
    parser.add_argument('--environment_type', type=str, default='urban', 
                        choices=['urban', 'suburban', 'rural'],
                        help="环境类型（影响信道模型）")
    parser.add_argument('--frequency', type=float, default=2.4, 
                        help="通信频率（GHz）")

    all_args = parser.parse_known_args(args)[0]

    return all_args


def main(args):
    """程序入口"""
    parser = get_config()
    all_args = parse_args(args, parser)

    # 为训练进程命名
    if all_args.algorithm_name == "mat":
        proc_name = f"MAT-UAV-{all_args.scenario_name}-{all_args.experiment_name}"
    elif all_args.algorithm_name == "mat_dec":
        proc_name = f"MAT-Dec-UAV-{all_args.scenario_name}-{all_args.experiment_name}"
    else:
        proc_name = f"{all_args.algorithm_name}-UAV-{all_args.scenario_name}-{all_args.experiment_name}"
    
    setproctitle.setproctitle(proc_name)

    # 设置随机种子
    torch.manual_seed(all_args.seed)
    torch.cuda.manual_seed_all(all_args.seed)
    np.random.seed(all_args.seed)

    # 创建环境
    env = make_train_env(all_args)
    eval_env = make_eval_env(all_args) if all_args.use_eval else None
    
    # 创建一个示例环境来获取空间信息
    if all_args.n_rollout_threads > 1:
        example_env = make_uav_comm_env(all_args.scenario_name, all_args)
        print("观测空间形状: ", example_env.observation_space)
        print("共享观测空间形状: ", example_env.share_observation_space)
        print("动作空间形状: ", example_env.action_space)
    else:
        print("观测空间形状: ", env.observation_space)
        print("共享观测空间形状: ", env.share_observation_space)
        print("动作空间形状: ", env.action_space)
    
    # 创建训练器
    config = {
        "all_args": all_args,
        "envs": env,
        "eval_envs": eval_env,
        "num_agents": all_args.num_uavs,
        "device": torch.device("cuda:0" if all_args.cuda else "cpu"),
        "run_dir": None
    }
    
    # 创建训练器和运行器
    trainer = TrainAlgo(config)
    runner = Runner(config, trainer)
    
    # 开始训练
    runner.run()
    
    # 环境清理
    env.close()
    if all_args.use_eval and eval_env is not None:
        eval_env.close()


if __name__ == "__main__":
    main(sys.argv[1:])
