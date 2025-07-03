#!/usr/bin/env python3
"""
基于流形的目标导向HMASD完整训练流水线
自动执行：数据收集 → VAE训练 → 目标导向强化学习训练
"""

import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
import time

from logger import main_logger

class ManifoldHMASDPipeline:
    """
    完整的Manifold HMASD训练流水线
    """
    
    def __init__(self, config):
        self.config = config
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 设置路径
        self.data_dir = f"data/good_states_{self.timestamp}"
        self.vae_dir = f"models/vae_{self.timestamp}"
        self.log_dir = f"logs/manifold_hmasd_{self.timestamp}"
        
        # 创建目录
        for dir_path in [self.data_dir, self.vae_dir, self.log_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 保存配置
        config_path = os.path.join(self.log_dir, 'pipeline_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        main_logger.info(f"流水线初始化完成，时间戳: {self.timestamp}")
        main_logger.info(f"数据目录: {self.data_dir}")
        main_logger.info(f"VAE模型目录: {self.vae_dir}")
        main_logger.info(f"日志目录: {self.log_dir}")
    
    def run_command(self, cmd, step_name):
        """
        执行系统命令并记录输出
        
        参数:
            cmd: 命令列表
            step_name: 步骤名称
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
                check=True
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
    
    def step1_collect_data(self):
        """
        步骤1: 收集高奖励状态数据
        """
        main_logger.info("=" * 60)
        main_logger.info("步骤1: 收集高奖励状态数据")
        main_logger.info("=" * 60)
        
        cmd = [
            "python", "scripts/collect_good_states.py",
            "--n_episodes", str(self.config['data_collection']['n_episodes']),
            "--reward_threshold", str(self.config['data_collection']['reward_threshold']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--save_dir", self.data_dir,
            "--seed", str(self.config['general']['seed'])
        ]
        
        if self.config['data_collection'].get('render', False):
            cmd.append("--render")
        
        success, output = self.run_command(cmd, "数据收集")
        
        if not success:
            raise RuntimeError("数据收集失败")
        
        # 检查生成的数据文件
        good_states_file = os.path.join(self.data_dir, 'good_states.npy')
        if not os.path.exists(good_states_file):
            raise FileNotFoundError(f"未找到数据文件: {good_states_file}")
        
        main_logger.info(f"数据收集成功，文件保存在: {self.data_dir}")
        return self.data_dir
    
    def step2_train_vae(self, data_dir):
        """
        步骤2: 训练VAE模型
        
        参数:
            data_dir: 数据目录
        """
        main_logger.info("=" * 60)
        main_logger.info("步骤2: 训练VAE模型")
        main_logger.info("=" * 60)
        
        cmd = [
            "python", "scripts/train_vae.py",
            "--data_dir", data_dir,
            "--latent_dim", str(self.config['vae']['latent_dim']),
            "--n_epochs", str(self.config['vae']['n_epochs']),
            "--batch_size", str(self.config['vae']['batch_size']),
            "--lr", str(self.config['vae']['lr']),
            "--beta_start", str(self.config['vae']['beta_start']),
            "--beta_end", str(self.config['vae']['beta_end']),
            "--beta_anneal_epochs", str(self.config['vae']['beta_anneal_epochs']),
            "--save_dir", self.vae_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'])
        ]
        
        success, output = self.run_command(cmd, "VAE训练")
        
        if not success:
            raise RuntimeError("VAE训练失败")
        
        # 查找生成的VAE模型文件
        import glob
        vae_files = glob.glob(os.path.join(self.vae_dir + "_*", 'vae_model.pth'))
        if not vae_files:
            raise FileNotFoundError("未找到训练好的VAE模型文件")
        
        vae_model_path = vae_files[0]  # 取最新的
        main_logger.info(f"VAE训练成功，模型保存在: {vae_model_path}")
        return vae_model_path
    
    def step3_train_agent(self, vae_model_path):
        """
        步骤3: 目标导向强化学习训练
        
        参数:
            vae_model_path: VAE模型路径
        """
        main_logger.info("=" * 60)
        main_logger.info("步骤3: 目标导向强化学习训练")
        main_logger.info("=" * 60)
        
        cmd = [
            "python", "train_manifold_hmasd.py",
            "--vae_model_path", vae_model_path,
            "--total_episodes", str(self.config['training']['total_episodes']),
            "--eval_interval", str(self.config['training']['eval_interval']),
            "--save_interval", str(self.config['training']['save_interval']),
            "--n_uavs", str(self.config['environment']['n_uavs']),
            "--n_users", str(self.config['environment']['n_users']),
            "--area_size", str(self.config['environment']['area_size']),
            "--log_dir", self.log_dir,
            "--device", self.config['general']['device'],
            "--seed", str(self.config['general']['seed'])
        ]
        
        if self.config['training'].get('render', False):
            cmd.append("--render")
        
        success, output = self.run_command(cmd, "目标导向训练")
        
        if not success:
            raise RuntimeError("目标导向训练失败")
        
        # 检查生成的模型文件
        final_model_path = os.path.join(self.log_dir + "_*", 'final_model.pth')
        import glob
        model_files = glob.glob(final_model_path)
        if not model_files:
            main_logger.warning("未找到最终模型文件，但训练可能仍在进行中")
        else:
            main_logger.info(f"训练完成，模型保存在: {model_files[0]}")
        
        return self.log_dir
    
    def run_pipeline(self):
        """
        运行完整流水线
        """
        main_logger.info("开始执行Manifold HMASD完整训练流水线")
        main_logger.info(f"配置: {self.config}")
        
        start_time = time.time()
        
        try:
            # 步骤1: 数据收集
            if self.config['pipeline']['skip_data_collection']:
                main_logger.info("跳过数据收集步骤")
                data_dir = self.config['pipeline']['existing_data_dir']
                if not os.path.exists(data_dir):
                    raise FileNotFoundError(f"指定的数据目录不存在: {data_dir}")
            else:
                data_dir = self.step1_collect_data()
            
            # 步骤2: VAE训练
            if self.config['pipeline']['skip_vae_training']:
                main_logger.info("跳过VAE训练步骤")
                vae_model_path = self.config['pipeline']['existing_vae_model']
                if not os.path.exists(vae_model_path):
                    raise FileNotFoundError(f"指定的VAE模型不存在: {vae_model_path}")
            else:
                vae_model_path = self.step2_train_vae(data_dir)
            
            # 步骤3: 目标导向训练
            log_dir = self.step3_train_agent(vae_model_path)
            
            # 完成
            total_time = time.time() - start_time
            main_logger.info("=" * 60)
            main_logger.info("流水线执行完成！")
            main_logger.info(f"总用时: {total_time:.1f}秒 ({total_time/60:.1f}分钟)")
            main_logger.info(f"数据目录: {data_dir}")
            main_logger.info(f"VAE模型: {vae_model_path}")
            main_logger.info(f"训练日志: {log_dir}")
            main_logger.info("=" * 60)
            
            # 生成总结报告
            self._generate_pipeline_summary(data_dir, vae_model_path, log_dir, total_time)
            
        except Exception as e:
            main_logger.error(f"流水线执行失败: {e}")
            raise
    
    def _generate_pipeline_summary(self, data_dir, vae_model_path, log_dir, total_time):
        """生成流水线执行总结"""
        summary = {
            'pipeline_info': {
                'timestamp': self.timestamp,
                'total_time_seconds': total_time,
                'total_time_minutes': total_time / 60,
                'config': self.config
            },
            'outputs': {
                'data_directory': data_dir,
                'vae_model_path': vae_model_path,
                'training_log_directory': log_dir,
                'tensorboard_command': f"tensorboard --logdir {log_dir}"
            },
            'next_steps': [
                "查看TensorBoard监控训练进度",
                "使用最佳模型进行评估",
                "根据需要调整超参数重新训练",
                "将框架扩展到其他任务"
            ]
        }
        
        summary_path = os.path.join(self.log_dir, 'pipeline_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        main_logger.info(f"流水线总结已保存: {summary_path}")

def create_default_config():
    """创建默认配置"""
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
            'reward_threshold': 0.7,
            'render': False
        },
        'vae': {
            'latent_dim': 5,
            'n_epochs': 200,
            'batch_size': 64,
            'lr': 1e-3,
            'beta_start': 0.0,
            'beta_end': 1.0,
            'beta_anneal_epochs': 50
        },
        'training': {
            'total_episodes': 1000,
            'eval_interval': 50,
            'save_interval': 100,
            'render': False
        },
        'pipeline': {
            'skip_data_collection': False,
            'existing_data_dir': None,
            'skip_vae_training': False,
            'existing_vae_model': None
        }
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Manifold HMASD完整训练流水线')
    
    # 基本参数
    parser.add_argument('--config_file', type=str, help='配置文件路径')
    parser.add_argument('--seed', type=int, default=42, help='随机种子')
    parser.add_argument('--device', type=str, default='auto', help='计算设备')
    
    # 环境参数
    parser.add_argument('--n_uavs', type=int, default=12, help='无人机数量')
    parser.add_argument('--n_users', type=int, default=80, help='用户数量')
    parser.add_argument('--area_size', type=int, default=2500, help='区域大小')
    
    # 数据收集参数
    parser.add_argument('--n_episodes', type=int, default=100, help='数据收集episodes')
    parser.add_argument('--reward_threshold', type=float, default=0.7, help='好状态奖励阈值')
    
    # VAE参数
    parser.add_argument('--latent_dim', type=int, default=5, help='VAE潜空间维度')
    parser.add_argument('--vae_epochs', type=int, default=200, help='VAE训练轮数')
    
    # 训练参数
    parser.add_argument('--total_episodes', type=int, default=1000, help='总训练episodes')
    
    # 跳过步骤（用于调试）
    parser.add_argument('--skip_data_collection', action='store_true', help='跳过数据收集')
    parser.add_argument('--existing_data_dir', type=str, help='已有数据目录')
    parser.add_argument('--skip_vae_training', action='store_true', help='跳过VAE训练')
    parser.add_argument('--existing_vae_model', type=str, help='已有VAE模型路径')
    
    # 其他
    parser.add_argument('--render', action='store_true', help='是否渲染')
    parser.add_argument('--quick_test', action='store_true', help='快速测试模式')
    
    args = parser.parse_args()
    
    # 加载或创建配置
    if args.config_file and os.path.exists(args.config_file):
        with open(args.config_file, 'r') as f:
            config = json.load(f)
        main_logger.info(f"从文件加载配置: {args.config_file}")
    else:
        config = create_default_config()
        main_logger.info("使用默认配置")
    
    # 命令行参数覆盖配置
    config['general']['seed'] = args.seed
    config['general']['device'] = args.device
    config['environment']['n_uavs'] = args.n_uavs
    config['environment']['n_users'] = args.n_users
    config['environment']['area_size'] = args.area_size
    config['data_collection']['n_episodes'] = args.n_episodes
    config['data_collection']['reward_threshold'] = args.reward_threshold
    config['data_collection']['render'] = args.render
    config['vae']['latent_dim'] = args.latent_dim
    config['vae']['n_epochs'] = args.vae_epochs
    config['training']['total_episodes'] = args.total_episodes
    config['training']['render'] = args.render
    config['pipeline']['skip_data_collection'] = args.skip_data_collection
    config['pipeline']['existing_data_dir'] = args.existing_data_dir
    config['pipeline']['skip_vae_training'] = args.skip_vae_training
    config['pipeline']['existing_vae_model'] = args.existing_vae_model
    
    # 快速测试模式
    if args.quick_test:
        main_logger.info("启用快速测试模式")
        config['data_collection']['n_episodes'] = 20
        config['vae']['n_epochs'] = 50
        config['training']['total_episodes'] = 100
        config['training']['eval_interval'] = 20
        config['training']['save_interval'] = 50
    
    # 创建并运行流水线
    pipeline = ManifoldHMASDPipeline(config)
    
    try:
        pipeline.run_pipeline()
        main_logger.info("流水线执行成功完成！")
        
        # 显示后续步骤提示
        print("\n" + "="*60)
        print("🎉 Manifold HMASD训练流水线执行完成！")
        print("="*60)
        print("下一步操作：")
        print(f"1. 查看TensorBoard: tensorboard --logdir {pipeline.log_dir}")
        print("2. 分析训练结果和模型性能")
        print("3. 根据需要调整超参数")
        print("4. 将框架应用到其他任务")
        print("="*60)
        
    except KeyboardInterrupt:
        main_logger.info("用户中断了流水线执行")
    except Exception as e:
        main_logger.error(f"流水线执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
