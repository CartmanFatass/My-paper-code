"""
运行调试测试的简单脚本
"""

import os
import sys
import traceback
from logger import main_logger

def run_probe_tests():
    """运行探针测试"""
    try:
        main_logger.info("开始运行探针测试...")
        from debug_probe_tests import main
        results = main()
        main_logger.info("探针测试完成！")
        return results
    except Exception as e:
        main_logger.error(f"探针测试失败: {e}")
        main_logger.error(f"错误详情: {traceback.format_exc()}")
        return None

def main():
    """主函数"""
    main_logger.info("=" * 80)
    main_logger.info("HMASD 调试测试套件")
    main_logger.info("基于论文 'Debugging Reinforcement Learning Systems' 的建议")
    main_logger.info("=" * 80)
    
    # 运行探针测试
    probe_results = run_probe_tests()
    
    if probe_results:
        main_logger.info("✅ 调试测试完成，请查看详细结果")
    else:
        main_logger.error("❌ 调试测试失败")
    
    main_logger.info("=" * 80)

if __name__ == "__main__":
    main()
