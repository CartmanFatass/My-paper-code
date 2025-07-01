#!/usr/bin/env python3
"""
快速运行所有配置可视化的脚本
"""

import os
import sys
import argparse

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualize_all_configs import AllConfigsVisualizer

def main():
    parser = argparse.ArgumentParser(description='快速运行所有配置的网络拓扑可视化')
    parser.add_argument('--csv_path', type=str, 
                       default='quick_test_results_20250702-003613/test_results.csv',
                       help='测试结果CSV文件路径')
    
    args = parser.parse_args()
    
    print("🚀 启动所有配置可视化生成器...")
    print("=" * 60)
    
    # 检查CSV文件是否存在
    if not os.path.exists(args.csv_path):
        print(f"❌ 错误: CSV文件 {args.csv_path} 不存在")
        print("\n💡 请先运行以下命令生成测试结果:")
        print("   python quick_env_test.py --mode focused")
        print("   或")
        print("   python run_quick_test.py")
        return
    
    print(f"📊 输入文件: {args.csv_path}")
    print(f"💾 输出目录: ./test/")
    print()
    
    try:
        # 创建可视化器
        visualizer = AllConfigsVisualizer(save_base_path="./test")
        
        # 生成所有可视化
        result_path = visualizer.visualize_all_configs_from_csv(args.csv_path)
        
        print("\n" + "=" * 60)
        print("🎉 所有配置的可视化已完成!")
        print(f"📁 结果保存在: {result_path}")
        print("\n📊 生成的内容包括:")
        print("   ✅ 每个配置的详细网络拓扑分析图")
        print("   ✅ 配置对比分析图表")
        print("   ✅ 区域大小影响分析")
        print("   ✅ 中继能力专项分析")
        print("   ✅ 可视化总结报告")
        print("\n🎯 重点关注:")
        print("   - area_size较大的配置 (≥2600m) 的中继建立情况")
        print("   - 不同区域大小下的网络连通性变化")
        print("   - UAV类型分布和中继路径可视化")
        
    except Exception as e:
        print(f"❌ 可视化生成过程中出现错误: {e}")
        print("\n🔧 可能的解决方案:")
        print("   1. 检查依赖包是否安装: matplotlib, pandas, numpy, tqdm")
        print("   2. 确保环境模块路径正确")
        print("   3. 检查CSV文件格式是否正确")
        return

if __name__ == "__main__":
    main()
