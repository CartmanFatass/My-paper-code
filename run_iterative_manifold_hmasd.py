#!/usr/bin/env python3
"""
迭代式基于流形的目标导向HMASD训练流水线
实现"探索-利用-再学习"的自改进循环
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
import time
import glob

from logger import main_logger

class IterativeManifoldPipeline:
    """
    迭代式Manifold HMASD训练流水线
    实现VAE和RL智能体的相互促进学习
    """
    
    def __init__(self, config):
        self.config = config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 设置基础路径
        self.base_data_dir = f"data/iterative_manifold_{self.timestamp}"
        self.base_vae_dir = f"models/iterative_vae_{self.timestamp}"
        self.base_log_dir = f"logs/iterative_manifold_{self.timestamp}"
        
        # 创建基础目录
        for dir_path in [self.base_data_dir, self.base_vae_dir, self.base_log_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 当前循环状态
        self.current_cycle = 0
        self.current_data_dir = None
        self.current_vae_path = None
        self.current_agent_path = None
        
        # 循环历史记录
        self.cycle_history = []
        
        # 保存配置
        config_path = os.path.join(self.base_log_dir, 'iterative_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        main_logger.info(f"迭代式流水线初始化完成，时间戳: {self.timestamp}")
        main_logger.info(f"基础数据目录: {self.base_data_dir}")
        main_logger.info(f"基础VAE目录: {self.base_vae_dir}")
        main_logger.info(f"基础日志目录: {self.base_log_dir}")
    
    def run_command(self, cmd, step_name, timeout=None):
        """
        执行系统命令并记录输出
        
        参数:
            cmd: 命令列表
            step_name: 步骤名称
            timeout: 超时时间（秒）
        """
        main_logger.info(f"开始执行: {step_name}")
        main_logger.info(f"命令: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=timeout
            )
            
            # 记录输出
            if result.stdout:
                main_logger.info(f"{step_name} 输出:\n{result.stdout}")
            
            elapsed_time = time.time() - start_time
            main_logger.info(f"{step_name} 完成，用时: {elapsed_time:.1f}秒")
            
            return True, result.stdout
            
        except subprocess.CalledProcessError as e:
            main_logger.error(f"{step_name} 失败:")
            main_logger.error(f"返回码: {e.returncode}")
            main_logger.error(f"错误输出: {e.stderr}")
            return False, e.stderr
        except subprocess.TimeoutExpired as e:
            main_logger.error(f"{step_name} 超时 ({timeout}秒)")
            return False, "Timeout"
    
    def cycle_0_cold_start(self):
        """
        循环0：冷启动阶段
        """
        main_logger.info("=" * 80)
        main_logger.info("循环 0: 冷启动阶段")
        main_logger.info("=" * 80)
        
        cycle_start_time = time.time()
        
        # 步骤1: 收集初始数据
        main_logger.info("步骤 1/3: 收集初始高奖励状态数据")
        initial_data_dir = os.path.join(self.base_data_dir, 'cycle_0_initial')
        
        cmd = [
            "python", "scripts/collect_good_states.py",
            "--n_episodes", str(self.config['data_collection']['n_episodes']),
            "--reward_threshold", str(self.config['data_collection']['reward_threshold']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--save_dir", initial_data_dir,
            "--seed", str(self.config['general']['seed'])
        ]
        
        success, output = self.run_command(cmd, "冷启动数据收集")
        if not success:
            raise RuntimeError("冷启动数据收集失败")
        
        self.current_data_dir = initial_data_dir
        
        # 步骤2: 训练初始VAE
        main_logger.info("步骤 2/3: 训练初始VAE模型")
        initial_vae_dir = os.path.join(self.base_vae_dir, 'cycle_0_initial')
        
        cmd = [
            "python", "scripts/train_vae.py",
            "--data_dir", self.current_data_dir,
            "--latent_dim", str(self.config['vae']['latent_dim']),
            "--n_epochs", str(self.config['vae']['n_epochs']),
            "--batch_size", str(self.config['vae']['batch_size']),
            "--lr", str(self.config['vae']['lr']),
            "--save_dir", initial_vae_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'])
        ]
        
        success, output = self.run_command(cmd, "初始VAE训练")
        if not success:
            raise RuntimeError("初始VAE训练失败")
        
        # 查找VAE模型文件
        vae_files = glob.glob(os.path.join(initial_vae_dir + "_*", 'vae_model.pth'))
        if not vae_files:
            raise FileNotFoundError("未找到训练好的VAE模型文件")
        self.current_vae_path = vae_files[0]
        
        # 步骤3: 训练初始RL智能体
        main_logger.info("步骤 3/3: 训练初始RL智能体")
        initial_log_dir = os.path.join(self.base_log_dir, 'cycle_0_initial')
        
        cmd = [
            "python", "train_manifold_hmasd.py",
            "--vae_model_path", self.current_vae_path,
            "--total_episodes", str(self.config['training']['total_episodes']),
            "--eval_interval", str(self.config['training']['eval_interval']),
            "--save_interval", str(self.config['training']['save_interval']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--log_dir", initial_log_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'])
        ]
        
        success, output = self.run_command(cmd, "初始RL训练", timeout=self.config.get('training_timeout', 3600))
        if not success:
            raise RuntimeError("初始RL训练失败")
        
        # 查找智能体模型文件
        agent_files = glob.glob(os.path.join(initial_log_dir + "_*", 'best_model_*.pth'))
        if not agent_files:
            # 如果没有最佳模型，尝试寻找最终模型
            agent_files = glob.glob(os.path.join(initial_log_dir + "_*", 'final_model.pth'))
        if not agent_files:
            raise FileNotFoundError("未找到训练好的智能体模型文件")
        self.current_agent_path = agent_files[0]
        
        # 记录循环0结果
        cycle_time = time.time() - cycle_start_time
        cycle_info = {
            'cycle': 0,
            'type': 'cold_start',
            'data_dir': self.current_data_dir,
            'vae_path': self.current_vae_path,
            'agent_path': self.current_agent_path,
            'duration': cycle_time,
            'timestamp': datetime.now().isoformat()
        }
        self.cycle_history.append(cycle_info)
        
        main_logger.info(f"循环 0 完成，用时: {cycle_time:.1f}秒")
        main_logger.info(f"VAE模型: {self.current_vae_path}")
        main_logger.info(f"智能体模型: {self.current_agent_path}")
        
        return cycle_info
    
    def cycle_n_self_improvement(self, cycle_num):
        """
        循环N (N>=1)：自改进阶段
        
        参数:
            cycle_num: 循环编号
        """
        main_logger.info("=" * 80)
        main_logger.info(f"循环 {cycle_num}: 自改进阶段")
        main_logger.info("=" * 80)
        
        cycle_start_time = time.time()
        
        # 步骤1: 使用当前智能体收集新数据
        main_logger.info(f"步骤 1/4: 使用智能体 π_{cycle_num-1} 收集新数据")
        rollout_data_dir = os.path.join(self.base_data_dir, f'cycle_{cycle_num}_rollout')
        
        cmd = [
            "python", "scripts/rollout_and_collect.py",
            "--agent_path", self.current_agent_path,
            "--vae_path", self.current_vae_path,
            "--n_episodes", str(self.config['rollout']['n_episodes']),
            "--quality_threshold", str(self.config['rollout']['quality_threshold']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--save_dir", rollout_data_dir,
            "--seed", str(self.config['general']['seed'] + cycle_num)  # 不同的种子
        ]
        
        success, output = self.run_command(cmd, f"循环{cycle_num}数据收集")
        if not success:
            main_logger.warning(f"循环{cycle_num}数据收集失败，跳过本循环")
            return None
        
        # 步骤2: 合并数据集
        main_logger.info(f"步骤 2/4: 合并数据集 D_{cycle_num} = D_{cycle_num-1} ∪ 新数据")
        merged_data_dir = os.path.join(self.base_data_dir, f'cycle_{cycle_num}_merged')
        
        cmd = [
            "python", "scripts/rollout_and_collect.py",
            "--agent_path", self.current_agent_path,  # 虽然不会用到，但是必需参数
            "--vae_path", self.current_vae_path,      # 虽然不会用到，但是必需参数
            "--n_episodes", "0",  # 不进行rollout
            "--save_dir", rollout_data_dir,
            "--merge_with", self.current_data_dir,
            "--merge_output", merged_data_dir
        ]
        
        success, output = self.run_command(cmd, f"循环{cycle_num}数据合并")
        if not success:
            main_logger.warning(f"循环{cycle_num}数据合并失败，使用原数据集")
            merged_data_dir = self.current_data_dir
        
        self.current_data_dir = merged_data_dir
        
        # 步骤3: 微调/重训练VAE
        main_logger.info(f"步骤 3/4: 微调VAE模型 VAE_{cycle_num}")
        new_vae_dir = os.path.join(self.base_vae_dir, f'cycle_{cycle_num}')
        
        cmd = [
            "python", "scripts/train_vae.py",
            "--data_dir", self.current_data_dir,
            "--latent_dim", str(self.config['vae']['latent_dim']),
            "--n_epochs", str(self.config['vae'].get('finetune_epochs', 100)),  # 微调时使用较少epochs
            "--batch_size", str(self.config['vae']['batch_size']),
            "--lr", str(self.config['vae']['lr']),
            "--save_dir", new_vae_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'] + cycle_num),
            "--finetune_from", self.current_vae_path,
            "--finetune_lr_scale", str(self.config['vae'].get('finetune_lr_scale', 0.1))
        ]
        
        success, output = self.run_command(cmd, f"循环{cycle_num}VAE微调")
        if not success:
            main_logger.warning(f"循环{cycle_num}VAE微调失败，使用原VAE")
            # 保持原VAE
        else:
            # 查找新VAE模型文件
            vae_files = glob.glob(os.path.join(new_vae_dir + "_*", 'vae_model.pth'))
            if vae_files:
                self.current_vae_path = vae_files[0]
            else:
                main_logger.warning("未找到新VAE模型，使用原VAE")
        
        # 步骤4: 微调/重训练RL智能体
        main_logger.info(f"步骤 4/4: 微调RL智能体 π_{cycle_num}")
        new_log_dir = os.path.join(self.base_log_dir, f'cycle_{cycle_num}')
        
        cmd = [
            "python", "train_manifold_hmasd.py",
            "--vae_model_path", self.current_vae_path,
            "--total_episodes", str(self.config['training'].get('finetune_episodes', 500)),  # 微调时使用较少episodes
            "--eval_interval", str(self.config['training']['eval_interval']),
            "--save_interval", str(self.config['training']['save_interval']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--log_dir", new_log_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'] + cycle_num),
            "--finetune_from", self.current_agent_path,
            "--finetune_lr_scale", str(self.config['training'].get('finetune_lr_scale', 0.5))
        ]
        
        success, output = self.run_command(cmd, f"循环{cycle_num}RL微调", timeout=self.config.get('training_timeout', 3600))
        if not success:
            main_logger.warning(f"循环{cycle_num}RL微调失败，使用原智能体")
            # 保持原智能体
        else:
            # 查找新智能体模型文件
            agent_files = glob.glob(os.path.join(new_log_dir + "_*", 'best_model_*.pth'))
            if not agent_files:
                agent_files = glob.glob(os.path.join(new_log_dir + "_*", 'final_model.pth'))
            if agent_files:
                self.current_agent_path = agent_files[0]
            else:
                main_logger.warning("未找到新智能体模型，使用原智能体")
        
        # 记录循环N结果
        cycle_time = time.time() - cycle_start_time
        cycle_info = {
            'cycle': cycle_num,
            'type': 'self_improvement',
            'data_dir': self.current_data_dir,
            'vae_path': self.current_vae_path,
            'agent_path': self.current_agent_path,
            'duration': cycle_time,
            'timestamp': datetime.now().isoformat()
        }
        self.cycle_history.append(cycle_info)
        
        main_logger.info(f"循环 {cycle_num} 完成，用时: {cycle_time:.1f}秒")
        main_logger.info(f"VAE模型: {self.current_vae_path}")
        main_logger.info(f"智能体模型: {self.current_agent_path}")
        
        return cycle_info
    
    def run_iterative_training(self, max_cycles=5):
        """
        运行完整的迭代训练流程
        
        参数:
            max_cycles: 最大循环数（不包括冷启动）
        """
        main_logger.info("开始迭代式Manifold HMASD训练")
        main_logger.info(f"配置: {self.config}")
        main_logger.info(f"最大循环数: {max_cycles + 1} (包括冷启动)")
        
        pipeline_start_time = time.time()
        
        try:
            # 循环0: 冷启动
            cycle_0_info = self.cycle_0_cold_start()
            
            # 循环1到N: 自改进
            for cycle in range(1, max_cycles + 1):
                try:
                    cycle_info = self.cycle_n_self_improvement(cycle)
                    if cycle_info is None:
                        main_logger.warning(f"循环 {cycle} 失败，终止迭代")
                        break
                except Exception as e:
                    main_logger.error(f"循环 {cycle} 执行失败: {e}")
                    main_logger.info("继续下一个循环...")
                    continue
            
            # 完成
            total_time = time.time() - pipeline_start_time
            main_logger.info("=" * 80)
            main_logger.info("迭代训练完成！")
            main_logger.info(f"总用时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
            main_logger.info(f"完成循环数: {len(self.cycle_history)}")
            main_logger.info(f"最终VAE模型: {self.current_vae_path}")
            main_logger.info(f"最终智能体模型: {self.current_agent_path}")
            main_logger.info("=" * 80)
            
            # 生成总结报告
            self._generate_final_summary(total_time)
            
        except Exception as e:
            main_logger.error(f"迭代训练失败: {e}")
            raise
    
    def _generate_final_summary(self, total_time):
        """生成最终总结报告"""
        summary = {
            'pipeline_info': {
                'timestamp': self.timestamp,
                'total_time_seconds': total_time,
                'total_time_minutes': total_time / 60,
                'config': self.config,
                'completed_cycles': len(self.cycle_history)
            },
            'cycle_history': self.cycle_history,
            'final_outputs': {
                'data_directory': self.current_data_dir,
                'vae_model_path': self.current_vae_path,
                'agent_model_path': self.current_agent_path,
                'base_log_directory': self.base_log_dir
            },
            'performance_evolution': self._analyze_performance_evolution()
        }
        
        summary_path = os.path.join(self.base_log_dir, 'iterative_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        main_logger.info(f"迭代训练总结已保存: {summary_path}")
    
    def _analyze_performance_evolution(self):
        """分析性能演化趋势"""
        # 这里可以添加更复杂的性能分析
        # 比如读取各个循环的训练日志，分析成功率、奖励等指标的变化
        evolution = {
            'cycle_durations': [cycle['duration'] for cycle in self.cycle_history],
            'data_expansion': "To be implemented",  # 可以添加数据集大小变化
            'model_complexity': "To be implemented"  # 可以添加模型复杂度变化
        }
        
        return evolution

def create_default_iterative_config():
    """创建默认的迭代训练配置"""
    return {
        'general': {
            'seed': 42,
            'device': 'auto'
        },
        'environment': {
            'n_uavs': 12,
            'n_users': 80,
            'area_size': 2500
        },
        'data_collection': {
            'n_episodes': 100,
            'reward_threshold': 0.7
        },
        'rollout': {
            'n_episodes': 50,
            'quality_threshold': 0.6
        },
        'vae': {
            'latent_dim': 5,
            'n_epochs': 200,
            'finetune_epochs': 100,
            'batch_size': 64,
            'lr': 1e-3,
            'finetune_lr_scale': 0.1
        },
        'training': {
            'total_episodes': 1000,
            'finetune_episodes': 500,
            'eval_interval': 50,
            'save_interval': 100,
            'finetune_lr_scale': 0.5
        },
        'training_timeout': 3600  # 1小时超时
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='迭代式Manifold HMASD训练流水线')
    
    # 基本参数
    parser.add_argument('--config_file', type=str, help='配置文件路径')
    parser.add_argument('--max_cycles', type=int, default=3, help='最大循环数（不包括冷启动）')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--device', type=str, default='auto', help='计算设备')
    
    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=12, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=80, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2500, help='区域大小')
    
    # 训练参数
    parser.add_argument('--initial_episodes', type=int, default=1000, help='冷启动训练episodes')
    parser.add_argument('--finetune_episodes', type=int, default=500, help='微调训练episodes')
    parser.add_argument('--rollout_episodes', type=int, default=50, help='rollout episodes')
    
    # 其他
    parser.add_argument('--quick_test', action='store_true', help='快速测试模式')
    
    args = parser.parse_args()
    
    # 加载或创建配置
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            config = json.load(f)
        main_logger.info(f"从文件加载配置: {args.config_file}")
    else:
        config = create_default_iterative_config()
        main_logger.info("使用默认配置")
    
    # 命令行参数覆盖配置
    config['general']['seed'] = args.seed
    config['general']['device'] = args.device
    config['environment']['n_uavs'] = args.n_uavs
    config['environment']['n_users'] = args.n_users
    config['environment']['area_size'] = args.area_size
    config['training']['total_episodes'] = args.initial_episodes
    config['training']['finetune_episodes'] = args.finetune_episodes
    config['rollout']['n_episodes'] = args.rollout_episodes
    
    # 快速测试模式
    if args.quick_test:
        main_logger.info("启用快速测试模式")
        config['data_collection']['n_episodes'] = 20
        config['rollout']['n_episodes'] = 10
        config['vae']['n_epochs'] = 50
        config['vae']['finetune_epochs'] = 25
        config['training']['total_episodes'] = 100
        config['training']['finetune_episodes'] = 50
        config['training']['eval_interval'] = 20
        config['training']['save_interval'] = 30
        args.max_cycles = min(args.max_cycles, 2)  # 最多2个自改进循环
    
    # 创建并运行迭代流水线
    pipeline = IterativeManifoldPipeline(config)
    
    try:
        pipeline.run_iterative_training(max_cycles=args.max_cycles)
        main_logger.info("迭代流水线执行成功完成！")
        
        # 显示后续步骤提示
        print("\n" + "="*80)
        print("🎉 迭代式Manifold HMASD训练流水线执行完成！")
        print("="*80)
        print("训练结果：")
        print(f"📊 完成 {len(pipeline.cycle_history)} 个训练循环")
        print(f"📁 最终VAE模型: {pipeline.current_vae_path}")
        print(f"🤖 最终智能体模型: {pipeline.current_agent_path}")
        print(f"📈 查看训练历史: {pipeline.base_log_dir}")
        print("\n下一步操作：")
        print("1. 分析各循环的性能演化趋势")
        print("2. 使用最终模型进行评估测试")
        print("3. 根据需要继续更多循环")
        print("4. 将框架应用到其他任务")
        print("="*80)
        
    except KeyboardInterrupt:
        main_logger.info("用户中断了迭代流水线执行")
    except Exception as e:
        main_logger.error(f"迭代流水线执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
