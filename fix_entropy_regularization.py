#!/usr/bin/env python3
"""
修复HMASD训练中的熵正则化问题

问题诊断：
1. 动作熵从正常的0.8-1.2逐渐上升到异常的4.2+
2. 这导致智能体行为完全随机化，无法学习有效策略
3. 根本原因：低级熵正则化系数lambda_l设置过高

解决方案：
1. 降低lambda_l从0.01到0.001
2. 调整其他熵相关参数以保持平衡
3. 根据论文Table 3的Alice_and_Bob设置进行优化
"""

import os
import shutil
from datetime import datetime

def fix_entropy_config():
    """修复配置文件中的熵正则化参数"""
    
    config_file = "config_continuous_alice_bob.py"
    backup_file = f"config_continuous_alice_bob_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    # 备份原配置文件
    shutil.copy(config_file, backup_file)
    print(f"已备份原配置文件到: {backup_file}")
    
    # 读取原配置
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复熵正则化参数
    fixes = [
        # 主要修复：大幅降低低级熵正则化
        ("lambda_l = 0.01", "lambda_l = 0.001"),
        
        # 微调高级熵正则化
        ("lambda_h = 0.1", "lambda_h = 0.05"),
        
        # 调整PPO参数以配合熵修复
        ("ppo_epochs = 10", "ppo_epochs = 4"),
        ("clip_epsilon = 0.2", "clip_epsilon = 0.1"),
    ]
    
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"修复: {old} -> {new}")
        else:
            print(f"警告: 未找到 '{old}'")
    
    # 写入修复后的配置
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n配置文件已修复: {config_file}")
    print("\n修复说明:")
    print("1. lambda_l: 0.01 -> 0.001 (降低10倍，防止过度随机化)")
    print("2. lambda_h: 0.1 -> 0.05 (微调高级熵)")
    print("3. ppo_epochs: 10 -> 4 (减少过拟合)")
    print("4. clip_epsilon: 0.2 -> 0.1 (更保守的策略更新)")

def create_restart_script():
    """创建重启训练脚本"""
    
    script_content = '''#!/usr/bin/env python3
"""
重启HMASD训练 - 使用修复后的熵正则化参数
"""

import os
import subprocess
import sys
from datetime import datetime

def main():
    print("=== HMASD训练重启 (熵正则化修复版) ===")
    print(f"时间: {datetime.now()}")
    
    # 清理旧的日志和模型
    cleanup_dirs = [
        "logs/alice_bob_entropy_fixed",
        "models/alice_bob_entropy_fixed"
    ]
    
    for dir_path in cleanup_dirs:
        if os.path.exists(dir_path):
            import shutil
            shutil.rmtree(dir_path)
            print(f"已清理: {dir_path}")
    
    # 启动训练
    cmd = [
        sys.executable, "train_continuous_alice_bob.py",
        "--config", "config_continuous_alice_bob.py",
        "--exp_name", "alice_bob_entropy_fixed",
        "--seed", "42"
    ]
    
    print(f"启动命令: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\\n训练被用户中断")
    except subprocess.CalledProcessError as e:
        print(f"\\n训练失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
'''
    
    with open("restart_training_entropy_fixed.py", 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 设置执行权限
    os.chmod("restart_training_entropy_fixed.py", 0o755)
    print("已创建重启脚本: restart_training_entropy_fixed.py")

def main():
    print("=== HMASD熵正则化修复工具 ===")
    print("\n问题诊断:")
    print("- 动作熵异常高 (4.2+)，导致完全随机行为")
    print("- 智能体无法学习有效策略")
    print("- 轨迹图显示混乱的随机移动")
    
    print("\n开始修复...")
    
    # 修复配置文件
    fix_entropy_config()
    
    # 创建重启脚本
    create_restart_script()
    
    print("\n=== 修复完成 ===")
    print("\n下一步操作:")
    print("1. 运行: python restart_training_entropy_fixed.py")
    print("2. 监控动作熵是否降到正常范围 (0.5-1.5)")
    print("3. 观察智能体是否开始学习有意义的行为")
    
    print("\n预期效果:")
    print("- 动作熵稳定在0.5-1.5之间")
    print("- 智能体开始学习目标导向的移动")
    print("- 轨迹图显示更有结构的行为模式")

if __name__ == "__main__":
    main()
