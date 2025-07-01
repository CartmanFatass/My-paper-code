#!/usr/bin/env python3
"""
多种子分析快速测试脚本
提供一些预设的测试场景，方便快速验证参数配置的稳定性
"""

import os
import sys
import argparse

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_seed_analysis import MultiSeedAnalyzer

def run_large_area_test():
    """测试大区域场景的稳定性"""
    print("🎯 测试场景: 大区域场景 (area_size=3000m)")
    
    config_params = {
        'n_uavs': 10,
        'n_users': 50,
        'area_size': 3000,
        'n_clusters': 5,
        'max_hops': 5,
        'user_distribution': 'multi_cluster',
        'channel_model': 'probabilistic',
        'cluster_std': 120,
        'central_area_ratio': 0.6,
        'use_fdma': True,
        'bandwidth': 20e6,
    }
    
    seeds = [42, 123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627]
    
    analyzer = MultiSeedAnalyzer(max_steps=150)
    results_df, stats = analyzer.analyze_config_multi_seed(
        config_params, seeds, 
        save_path="./test/multi_seed_large_area_test"
    )
    
    return results_df, stats

def run_medium_area_test():
    """测试中等区域场景的稳定性"""
    print("🎯 测试场景: 中等区域场景 (area_size=2400m)")
    
    config_params = {
        'n_uavs': 10,
        'n_users': 50,
        'area_size': 2400,
        'n_clusters': 4,
        'max_hops': 5,
        'user_distribution': 'multi_cluster',
        'channel_model': 'probabilistic',
        'cluster_std': 120,
        'central_area_ratio': 0.6,
        'use_fdma': True,
        'bandwidth': 20e6,
    }
    
    seeds = [42, 123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627]
    
    analyzer = MultiSeedAnalyzer(max_steps=150)
    results_df, stats = analyzer.analyze_config_multi_seed(
        config_params, seeds, 
        save_path="./test/multi_seed_medium_area_test"
    )
    
    return results_df, stats

def run_high_density_test():
    """测试高密度用户场景的稳定性"""
    print("🎯 测试场景: 高密度用户场景 (75用户)")
    
    config_params = {
        'n_uavs': 12,
        'n_users': 75,
        'area_size': 2600,
        'n_clusters': 5,
        'max_hops': 5,
        'user_distribution': 'multi_cluster',
        'channel_model': 'probabilistic',
        'cluster_std': 120,
        'central_area_ratio': 0.6,
        'use_fdma': True,
        'bandwidth': 20e6,
    }
    
    seeds = [42, 123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627]
    
    analyzer = MultiSeedAnalyzer(max_steps=150)
    results_df, stats = analyzer.analyze_config_multi_seed(
        config_params, seeds, 
        save_path="./test/multi_seed_high_density_test"
    )
    
    return results_df, stats

def compare_scenarios():
    """对比不同场景的稳定性"""
    print("\n" + "="*80)
    print("📊 对比分析: 不同场景的稳定性")
    print("="*80)
    
    scenarios = [
        ("大区域场景", run_large_area_test),
        ("中等区域场景", run_medium_area_test),
        ("高密度场景", run_high_density_test),
    ]
    
    comparison_results = []
    
    for name, test_func in scenarios:
        print(f"\n🔬 运行 {name}...")
        try:
            results_df, stats = test_func()
            if stats:
                comparison_results.append({
                    'scenario': name,
                    'service_rate_mean': stats['service_rate']['mean'],
                    'service_rate_cv': stats['service_rate']['cv'],
                    'connectivity_mean': stats['network_connectivity']['mean'],
                    'connectivity_cv': stats['network_connectivity']['cv'],
                    'throughput_mean': stats['throughput_mbps']['mean'],
                    'stable': stats['service_rate']['cv'] < 0.2 and stats['network_connectivity']['cv'] < 0.2
                })
        except Exception as e:
            print(f"❌ {name} 测试失败: {e}")
    
    # 打印对比结果
    if comparison_results:
        print("\n" + "="*80)
        print("📈 场景对比总结")
        print("="*80)
        
        print(f"{'场景':<15} {'服务率':<12} {'服务率CV':<12} {'连通性':<12} {'连通性CV':<12} {'稳定性':<8}")
        print("-" * 80)
        
        for result in comparison_results:
            stability_symbol = "✅" if result['stable'] else "⚠️"
            print(f"{result['scenario']:<15} "
                  f"{result['service_rate_mean']:<12.3f} "
                  f"{result['service_rate_cv']:<12.4f} "
                  f"{result['connectivity_mean']:<12.3f} "
                  f"{result['connectivity_cv']:<12.4f} "
                  f"{stability_symbol:<8}")
        
        # 推荐最稳定的配置
        stable_configs = [r for r in comparison_results if r['stable']]
        if stable_configs:
            best_config = max(stable_configs, key=lambda x: x['service_rate_mean'])
            print(f"\n🏆 推荐配置: {best_config['scenario']}")
            print(f"   理由: 稳定性好且服务率最高 ({best_config['service_rate_mean']:.3f})")

def main():
    parser = argparse.ArgumentParser(description='多种子分析快速测试')
    parser.add_argument('--test', type=str, 
                       choices=['large', 'medium', 'high_density', 'compare'],
                       default='compare',
                       help='选择测试场景')
    
    args = parser.parse_args()
    
    print("🔬 多种子环境参数验证 - 快速测试")
    print("="*60)
    
    if args.test == 'large':
        run_large_area_test()
    elif args.test == 'medium':
        run_medium_area_test()
    elif args.test == 'high_density':
        run_high_density_test()
    elif args.test == 'compare':
        compare_scenarios()
    
    print("\n✅ 测试完成!")
    print("💡 使用自定义参数测试:")
    print("   python test/multi_seed_analysis.py --n_uavs 12 --area_size 3000 --num_seeds 5")

if __name__ == "__main__":
    main()
