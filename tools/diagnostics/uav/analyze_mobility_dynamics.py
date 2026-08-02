import numpy as np
import matplotlib.pyplot as plt

def analyze_current_mobility():
    """分析当前移动模型的动态性"""
    
    # 当前参数
    area_size = 8000  # 用户提到的8000x8000场景
    max_steps = 1800
    time_step = 1.0
    user_max_speed = 5  # m/s
    cluster_std = 80
    
    # 计算最大可能移动距离
    max_distance_per_step = user_max_speed * time_step  # 5m per step
    max_total_distance = max_distance_per_step * max_steps  # 9000m total
    
    # 计算相对于地图大小的移动范围
    movement_ratio = max_total_distance / area_size  # 1.125 (112.5% of map size)
    
    # 分析簇内活动范围
    intra_cluster_radius = cluster_std * 1.5  # 120m
    intra_cluster_diameter = intra_cluster_radius * 2  # 240m
    
    print("=== 当前移动模型分析 ===")
    print(f"地图大小: {area_size}x{area_size}m")
    print(f"仿真时长: {max_steps}步 ({max_steps}秒)")
    print(f"用户最大速度: {user_max_speed} m/s")
    print(f"每步最大移动距离: {max_distance_per_step}m")
    print(f"理论最大总移动距离: {max_total_distance}m")
    print(f"移动距离/地图大小比例: {movement_ratio:.1%}")
    print(f"簇内活动半径: {intra_cluster_radius}m")
    print(f"簇内活动直径: {intra_cluster_diameter}m")
    print(f"簇活动范围/地图大小比例: {intra_cluster_diameter/area_size:.1%}")
    
    # 分析问题
    print("\n=== 问题分析 ===")
    if intra_cluster_diameter / area_size < 0.1:
        print("❌ 簇内活动范围过小，仅占地图的{:.1%}".format(intra_cluster_diameter/area_size))
    
    # UAV覆盖范围分析（假设观测半径600m）
    uav_observation_radius = 600
    uav_coverage_diameter = uav_observation_radius * 2
    coverage_ratio = uav_coverage_diameter / area_size
    
    print(f"UAV观测半径: {uav_observation_radius}m")
    print(f"UAV覆盖直径: {uav_coverage_diameter}m") 
    print(f"UAV覆盖范围/地图大小比例: {coverage_ratio:.1%}")
    
    if intra_cluster_diameter < uav_coverage_diameter:
        print("❌ 用户簇活动范围小于UAV覆盖范围，移动性不足以逃脱覆盖")
    
    return {
        'max_total_distance': max_total_distance,
        'movement_ratio': movement_ratio,
        'intra_cluster_diameter': intra_cluster_diameter,
        'cluster_coverage_ratio': intra_cluster_diameter/area_size,
        'uav_coverage_ratio': coverage_ratio
    }

def propose_enhanced_mobility_models():
    """提出增强的移动模型"""
    
    print("\n=== 增强移动模型建议 ===")
    
    print("\n1. 【高速移动模型】- 适用于车载用户场景")
    print("   - user_max_speed: 15-25 m/s (54-90 km/h)")
    print("   - 适合模拟车载通信场景")
    print("   - 能在1800s内横穿整个8000m地图")
    
    print("\n2. 【扩展簇活动模型】- 保持簇特性但增加活动范围")
    print("   - cluster_std: 200-400 (原80)")
    print("   - intra_cluster_activity_radius: cluster_std * 3-5")
    print("   - 簇内活动范围扩大到600-2000m直径")
    
    print("\n3. 【动态热点迁移模型】- 簇中心随时间变化")
    print("   - 簇中心以较慢速度移动 (1-2 m/s)")
    print("   - 用户跟随簇中心移动")
    print("   - 模拟热点区域的时空变化")
    
    print("\n4. 【混合移动模型】- 不同类型用户混合")
    print("   - 70%低速用户 (2-5 m/s) - 行人")
    print("   - 30%高速用户 (10-20 m/s) - 车辆")
    print("   - 更真实的异构移动场景")
    
    print("\n5. 【潮汐移动模型】- 基于时间的定向移动")
    print("   - 早期: 向中心聚集")
    print("   - 中期: 随机移动")
    print("   - 后期: 向边缘扩散")
    print("   - 模拟真实的人群流动模式")

if __name__ == "__main__":
    current_stats = analyze_current_mobility()
    propose_enhanced_mobility_models()
    
    # 可视化移动范围对比
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 当前模型
    ax1.set_xlim(0, 8000)
    ax1.set_ylim(0, 8000)
    ax1.set_title("当前移动模型")
    ax1.set_aspect('equal')
    
    # 模拟簇位置
    cluster_centers = [[2000, 2000], [6000, 2000], [2000, 6000], [6000, 6000]]
    for center in cluster_centers:
        circle = plt.Circle(center, 120, fill=False, color='blue', linestyle='--')
        ax1.add_patch(circle)
        ax1.plot(center[0], center[1], 'bo', markersize=8)
    
    ax1.text(4000, 500, f"簇活动直径: {current_stats['intra_cluster_diameter']:.0f}m\n占地图比例: {current_stats['cluster_coverage_ratio']:.1%}", 
             ha='center', fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue"))
    
    # 增强模型
    ax2.set_xlim(0, 8000)
    ax2.set_ylim(0, 8000)
    ax2.set_title("增强移动模型")
    ax2.set_aspect('equal')
    
    # 更大的活动范围
    enhanced_radius = 400  # 扩展后的活动半径
    for center in cluster_centers:
        circle = plt.Circle(center, enhanced_radius, fill=False, color='red', linestyle='--')
        ax2.add_patch(circle)
        ax2.plot(center[0], center[1], 'ro', markersize=8)
    
    enhanced_diameter = enhanced_radius * 2
    enhanced_ratio = enhanced_diameter / 8000
    ax2.text(4000, 500, f"簇活动直径: {enhanced_diameter:.0f}m\n占地图比例: {enhanced_ratio:.1%}", 
             ha='center', fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral"))
    
    plt.tight_layout()
    plt.savefig('mobility_comparison.png', dpi=150, bbox_inches='tight')
    plt.show()
