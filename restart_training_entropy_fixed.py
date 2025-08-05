#!/usr/bin/env python3
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
        print("\n训练被用户中断")
    except subprocess.CalledProcessError as e:
        print(f"\n训练失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
