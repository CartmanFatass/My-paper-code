"""
手动分析UAV环境中的SINR和吞吐量计算
直接分析数学公式，验证是否存在1100Mbps的异常情况
"""

import numpy as np

def analyze_throughput_calculation():
    """
    手动分析吞吐量计算，验证是否存在异常
    """
    print("=" * 60)
    print("手动SINR和吞吐量计算分析")
    print("=" * 60)
    
    # 基础参数（从uav_env.py中获取）
    carrier_frequency = 2.4e9  # Hz
    bandwidth = 20e6  # Hz = 20MHz
    tx_power = 20  # dBm
    ground_bs_tx_power = 30  # dBm
    noise_power = -104  # dBm
    min_sinr = 0  # dB
    
    print(f"基础通信参数:")
    print(f"  载波频率: {carrier_frequency/1e9:.1f} GHz")
    print(f"  带宽: {bandwidth/1e6:.1f} MHz")
    print(f"  UAV发射功率: {tx_power} dBm")
    print(f"  地面基站发射功率: {ground_bs_tx_power} dBm")
    print(f"  噪声功率: {noise_power} dBm")
    
    # 测试不同距离下的SINR和吞吐量
    distances = [50, 100, 200, 500, 1000, 2000]  # 米
    
    print(f"\n=== 不同距离下的SINR和吞吐量分析 ===")
    print(f"{'距离(m)':<8} {'路径损耗(dB)':<12} {'接收功率(dBm)':<14} {'SINR(dB)':<10} {'吞吐量(Mbps)':<12}")
    print("-" * 70)
    
    max_throughput = 0
    max_sinr = 0
    
    for distance in distances:
        # 计算自由空间路径损耗
        # 公式: PL = 20*log10(d) + 20*log10(4*pi*f/c)
        wavelength = 3e8 / carrier_frequency
        path_loss = 20 * np.log10(distance) + 20 * np.log10(4 * np.pi / wavelength)
        
        # 计算接收功率
        rx_power = tx_power - path_loss
        
        # 计算SINR (假设没有干扰，只有噪声)
        sinr_db = rx_power - noise_power
        
        # 转换为线性单位
        sinr_linear = 10 ** (sinr_db / 10)
        
        # 香农公式计算吞吐量
        throughput_bps = bandwidth * np.log2(1 + sinr_linear)
        throughput_mbps = throughput_bps / 1e6
        
        print(f"{distance:<8} {path_loss:<12.1f} {rx_power:<14.1f} {sinr_db:<10.1f} {throughput_mbps:<12.1f}")
        
        max_throughput = max(max_throughput, throughput_mbps)
        max_sinr = max(max_sinr, sinr_db)
    
    print(f"\n发现的最大单连接吞吐量: {max_throughput:.1f} Mbps")
    print(f"发现的最大SINR: {max_sinr:.1f} dB")
    
    # 分析极端情况
    print(f"\n=== 极端情况分析 ===")
    
    # 极近距离 (10米)
    extreme_distance = 10
    wavelength = 3e8 / carrier_frequency
    extreme_path_loss = 20 * np.log10(extreme_distance) + 20 * np.log10(4 * np.pi / wavelength)
    extreme_rx_power = tx_power - extreme_path_loss
    extreme_sinr_db = extreme_rx_power - noise_power
    extreme_sinr_linear = 10 ** (extreme_sinr_db / 10)
    extreme_throughput = bandwidth * np.log2(1 + extreme_sinr_linear) / 1e6
    
    print(f"极近距离 ({extreme_distance}m):")
    print(f"  路径损耗: {extreme_path_loss:.1f} dB")
    print(f"  接收功率: {extreme_rx_power:.1f} dBm")
    print(f"  SINR: {extreme_sinr_db:.1f} dB")
    print(f"  单连接吞吐量: {extreme_throughput:.1f} Mbps")
    
    # 理论最大值 (SINR = 30dB)
    theoretical_sinr_linear = 10 ** (30 / 10)  # 30dB = 1000倍
    theoretical_max_throughput = bandwidth * np.log2(1 + theoretical_sinr_linear) / 1e6
    print(f"\n理论最大值 (30dB SINR):")
    print(f"  单连接最大吞吐量: {theoretical_max_throughput:.1f} Mbps")
    
    # 系统级别分析
    print(f"\n=== 系统级别分析 ===")
    n_uavs = 5
    max_connections_per_uav = 10
    
    # 情况1: 每个UAV都达到最大连接数，每个连接都是极端高吞吐量
    system_throughput_scenario1 = n_uavs * max_connections_per_uav * extreme_throughput
    print(f"情况1 - 所有连接都在极近距离:")
    print(f"  {n_uavs} UAVs × {max_connections_per_uav} 连接/UAV × {extreme_throughput:.1f} Mbps/连接")
    print(f"  = {system_throughput_scenario1:.1f} Mbps (这是不现实的)")
    
    # 情况2: 更现实的情况 - 平均距离500米
    avg_distance = 500
    avg_path_loss = 20 * np.log10(avg_distance) + 20 * np.log10(4 * np.pi / wavelength)
    avg_rx_power = tx_power - avg_path_loss
    avg_sinr_db = avg_rx_power - noise_power
    avg_sinr_linear = 10 ** (avg_sinr_db / 10)
    avg_throughput = bandwidth * np.log2(1 + avg_sinr_linear) / 1e6
    
    print(f"\n情况2 - 平均距离 ({avg_distance}m):")
    print(f"  平均单连接吞吐量: {avg_throughput:.1f} Mbps")
    
    # 假设每个UAV平均连接5个用户
    avg_connections_per_uav = 5
    system_throughput_scenario2 = n_uavs * avg_connections_per_uav * avg_throughput
    print(f"  {n_uavs} UAVs × {avg_connections_per_uav} 连接/UAV × {avg_throughput:.1f} Mbps/连接")
    print(f"  = {system_throughput_scenario2:.1f} Mbps (更现实)")
    
    # 问题诊断
    print(f"\n=== 问题诊断 ===")
    
    if extreme_throughput > 300:
        print(f"⚠️  极近距离单连接吞吐量 ({extreme_throughput:.1f} Mbps) 确实可能超过300Mbps")
        print(f"   这在物理上是可能的，但在实际部署中很少见")
    
    if system_throughput_scenario1 > 1000:
        print(f"⚠️  如果所有连接都在极近距离，系统总吞吐量 ({system_throughput_scenario1:.1f} Mbps) 会超过1000Mbps")
        print(f"   这表明代码中可能存在以下问题:")
        print(f"   1. 没有考虑带宽共享 - 每个连接都假设独享全部20MHz")
        print(f"   2. 没有考虑回程瓶颈的有效限制")
        print(f"   3. 没有考虑干扰的影响")
    
    # 带宽共享分析
    print(f"\n=== 带宽共享修正分析 ===")
    
    # 如果UAV内部需要共享带宽
    shared_bandwidth_per_connection = bandwidth / max_connections_per_uav  # 每连接分配的带宽
    shared_throughput_extreme = shared_bandwidth_per_connection * np.log2(1 + extreme_sinr_linear) / 1e6
    
    print(f"考虑带宽共享的情况:")
    print(f"  每连接分配带宽: {shared_bandwidth_per_connection/1e6:.1f} MHz")
    print(f"  极近距离单连接吞吐量: {shared_throughput_extreme:.1f} Mbps")
    
    system_throughput_shared = n_uavs * max_connections_per_uav * shared_throughput_extreme
    print(f"  修正后的系统总吞吐量: {system_throughput_shared:.1f} Mbps")
    
    if system_throughput_shared < 1000:
        print(f"✅ 考虑带宽共享后，系统吞吐量变得更合理")
    
    # 总结
    print(f"\n=== 总结 ===")
    print(f"1. 单连接最大理论吞吐量: {theoretical_max_throughput:.1f} Mbps (20MHz, 30dB SINR)")
    print(f"2. 极近距离实际吞吐量: {extreme_throughput:.1f} Mbps")
    print(f"3. 如果不考虑带宽共享，系统总吞吐量可能达到: {system_throughput_scenario1:.1f} Mbps")
    print(f"4. 考虑带宽共享后，系统总吞吐量: {system_throughput_shared:.1f} Mbps")
    
    print(f"\n结论:")
    if extreme_throughput > 200:
        print(f"- 单连接1100Mbps在当前参数下是不可能的（最大约{extreme_throughput:.0f}Mbps）")
        print(f"- 但系统总吞吐量1100Mbps是可能的，特别是在不考虑带宽共享的情况下")
        print(f"- 建议修改代码以考虑UAV内部的带宽共享")
    
    return {
        'max_single_throughput': extreme_throughput,
        'max_system_throughput_no_sharing': system_throughput_scenario1,
        'max_system_throughput_with_sharing': system_throughput_shared,
        'theoretical_max': theoretical_max_throughput
    }

if __name__ == "__main__":
    results = analyze_throughput_calculation()
    print(f"\n测试完成！")
