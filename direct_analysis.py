import numpy as np

# 基础参数（从uav_env.py中获取）
carrier_frequency = 2.4e9  # Hz
bandwidth = 20e6  # Hz = 20MHz
tx_power = 20  # dBm
noise_power = -104  # dBm

print("=" * 50)
print("SINR和吞吐量计算验证")
print("=" * 50)

print(f"基础参数:")
print(f"  载波频率: {carrier_frequency/1e9:.1f} GHz")
print(f"  带宽: {bandwidth/1e6:.1f} MHz")
print(f"  UAV发射功率: {tx_power} dBm")
print(f"  噪声功率: {noise_power} dBm")

# 测试极近距离的情况
distance = 10  # 10米
wavelength = 3e8 / carrier_frequency
path_loss = 20 * np.log10(distance) + 20 * np.log10(4 * np.pi / wavelength)
rx_power = tx_power - path_loss
sinr_db = rx_power - noise_power
sinr_linear = 10 ** (sinr_db / 10)
throughput_bps = bandwidth * np.log2(1 + sinr_linear)
throughput_mbps = throughput_bps / 1e6

print(f"\n极近距离 ({distance}m) 分析:")
print(f"  路径损耗: {path_loss:.1f} dB")
print(f"  接收功率: {rx_power:.1f} dBm")
print(f"  SINR: {sinr_db:.1f} dB")
print(f"  单连接吞吐量: {throughput_mbps:.1f} Mbps")

# 理论最大值 (30dB SINR)
theoretical_sinr_linear = 10 ** (30 / 10)
theoretical_max = bandwidth * np.log2(1 + theoretical_sinr_linear) / 1e6
print(f"\n理论最大值 (30dB SINR): {theoretical_max:.1f} Mbps")

# 系统级分析
n_uavs = 5
max_connections = 10

system_throughput_no_sharing = n_uavs * max_connections * throughput_mbps
print(f"\n系统级分析:")
print(f"  {n_uavs} UAVs × {max_connections} 连接 × {throughput_mbps:.1f} Mbps")
print(f"  = {system_throughput_no_sharing:.1f} Mbps (不考虑带宽共享)")

# 考虑带宽共享
shared_bandwidth = bandwidth / max_connections
shared_throughput = shared_bandwidth * np.log2(1 + sinr_linear) / 1e6
system_throughput_shared = n_uavs * max_connections * shared_throughput

print(f"\n考虑带宽共享:")
print(f"  每连接带宽: {shared_bandwidth/1e6:.1f} MHz")
print(f"  单连接吞吐量: {shared_throughput:.1f} Mbps")
print(f"  系统总吞吐量: {system_throughput_shared:.1f} Mbps")

print(f"\n结论:")
if throughput_mbps > 200:
    print(f"✓ 单连接可能达到 {throughput_mbps:.0f} Mbps (极近距离)")
else:
    print(f"✓ 单连接最大约 {throughput_mbps:.0f} Mbps")

if system_throughput_no_sharing > 1000:
    print(f"⚠️  不考虑带宽共享时，系统可达 {system_throughput_no_sharing:.0f} Mbps")
    print(f"   这解释了为什么会看到1100Mbps的情况")
else:
    print(f"✓ 系统吞吐量约 {system_throughput_no_sharing:.0f} Mbps")

print(f"✓ 考虑带宽共享后，更合理的系统吞吐量: {system_throughput_shared:.0f} Mbps")

print("\n" + "=" * 50)
print("分析完成")
print("=" * 50)
