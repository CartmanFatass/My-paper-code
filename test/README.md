# 所有配置可视化工具

这个工具可以为 `quick_env_test.py` 生成的所有测试配置创建详细的网络拓扑可视化，特别适合观察大区域场景下的中继建立情况。

## 功能特色

✨ **全配置覆盖**: 为每个测试配置生成独立的可视化分析
🎯 **中继能力分析**: 重点关注大area_size下的多跳中继建立
📊 **多维度对比**: 提供区域大小影响、性能对比等分析图表
🔍 **详细拓扑图**: 3D网络拓扑、2D俯视图、连通性分析、性能雷达图

## 使用方法

### 1. 快速运行

```bash
# 使用默认的测试结果文件
python test/run_visualization.py

# 指定特定的CSV文件
python test/run_visualization.py --csv_path your_test_results.csv
```

### 2. 直接调用主脚本

```bash
python test/visualize_all_configs.py --csv_path quick_test_results_20250702-003613/test_results.csv
```

## 输出结构

生成的可视化结果将保存在 `./test/all_configs_visualization_TIMESTAMP/` 目录下：

```
all_configs_visualization_TIMESTAMP/
├── config_1/                           # 配置1的详细分析
│   ├── config_info.txt                 # 配置参数详情
│   └── network_topology_analysis.png   # 四合一分析图
├── config_2/                           # 配置2的详细分析
│   ├── config_info.txt
│   └── network_topology_analysis.png
├── ...                                 # 其他配置
├── config_10/                          # 配置10的详细分析
│   ├── config_info.txt
│   └── network_topology_analysis.png
└── comparison_analysis/                 # 对比分析
    ├── area_size_impact_analysis.png   # 区域大小影响分析
    ├── all_configs_overview.png        # 所有配置性能总览
    ├── relay_capability_analysis.png   # 中继能力专项分析
    └── visualization_summary_report.txt # 总结报告
```

## 生成内容说明

### 单配置分析图 (四合一)

每个配置的 `network_topology_analysis.png` 包含：

1. **3D网络拓扑图**
   - 🔺 无人机位置和类型标识
   - 🔵 用户分布和连接状态
   - ⬛ 地面基站位置
   - 🔗 中继链路和回程链路

2. **2D俯视图**
   - 网络拓扑的俯视视角
   - 用户簇边界显示
   - 连接关系清晰标注

3. **UAV类型分布饼图**
   - 服务型UAV (红色)
   - 中继型UAV (橙色)
   - 孤立型UAV (珊瑚色)
   - 空闲UAV (灰色)

4. **性能指标雷达图**
   - 服务率
   - 有效服务率
   - 吞吐量
   - 网络连通性
   - 负载均衡

### 对比分析图表

1. **区域大小影响分析**
   - 服务率 vs 区域大小
   - 网络连通性 vs 区域大小
   - 平均跳数 vs 区域大小
   - 吞吐量 vs 区域大小

2. **所有配置性能总览**
   - 气泡图：area_size vs 服务率
   - 气泡大小代表吞吐量
   - 颜色深浅代表网络连通性

3. **中继能力专项分析**
   - 不同区域大小的服务率分布
   - 各配置的平均跳数对比
   - 总服务率 vs 有效服务率对比

## 重点观察内容

🎯 **大区域配置** (area_size ≥ 2600m):
- 配置1: area_size=3000m，观察最大区域下的中继情况
- 配置5: area_size=2600m，观察中继建立的临界状态
- 配置10: area_size=2800m，观察中等大区域的表现

🔍 **中继建立指标**:
- network_connectivity: 网络连通性(应为1.0表示所有UAV可达)
- avg_hops: 平均跳数(>1.0表示存在多跳中继)
- UAV类型分布: 中继型UAV的数量和比例

📊 **性能权衡**:
- 区域增大 → 服务率下降
- 但网络连通性保持稳定
- 需要更多UAV或更好的位置优化

## 依赖要求

```bash
pip install matplotlib pandas numpy tqdm
```

## 故障排除

1. **ImportError**: 确保项目模块路径正确
2. **FileNotFoundError**: 检查CSV文件路径是否存在
3. **可视化失败**: 检查matplotlib后端设置
4. **内存不足**: 可以分批处理配置

## 进一步分析

生成的可视化结果可以帮助您：

1. **参数优化**: 找到最适合大区域的UAV数量和分布
2. **中继策略**: 观察哪些配置能有效建立多跳中继
3. **性能预测**: 预测更大区域下的网络表现
4. **算法改进**: 为智能体训练提供参考配置

---

💡 **提示**: 重点关注area_size较大的配置，这些场景更容易观察到中继网络的建立和优化效果。
