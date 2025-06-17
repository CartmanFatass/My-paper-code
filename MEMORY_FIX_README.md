# 内存问题修复说明

## 问题描述

原始训练脚本在运行过程中出现 `MemoryError: bad allocation` 错误，具体发生在 matplotlib 保存图片时（第359行）。这是由于在训练过程中频繁生成高分辨率图表导致的内存消耗过大。

## 解决方案

### 1. 训练过程优化

我们修改了 `train_multiproc_config_1.py` 文件，**禁用了训练过程中的图表生成**，但保留了所有数据收集功能：

- ✅ **保留数据收集**: 所有训练数据（奖励、技能使用、性能指标）仍然被收集和保存
- ✅ **保留TensorBoard日志**: 可以使用TensorBoard实时监控训练进展
- ❌ **跳过matplotlib绘图**: 避免内存问题，提高训练效率

### 2. 独立可视化工具

创建了新的脚本 `generate_training_plots.py`，用于在训练完成后生成图表：

- 📊 **完整的可视化分析**: 生成训练进展、奖励组件、技能使用等图表
- 💾 **内存友好**: 使用较低DPI，优化内存使用
- 📈 **详细报告**: 自动生成训练摘要统计报告

## 使用方法

### 运行训练（无内存问题）

```bash
# 正常训练，不会再有内存错误
python train_multiproc_config_1.py --scenario 2 --n_uavs 5 --n_users 50

# 可以使用详细日志记录更多数据
python train_multiproc_config_1.py --scenario 2 --detailed_logging

# 调整数据导出频率（默认每1000步导出一次）
python train_multiproc_config_1.py --scenario 2 --export_interval 2000
```

### 实时监控训练

使用TensorBoard查看训练进展：

```bash
# 在另一个终端运行
tensorboard --logdir logs/sb3_multiproc_paper_config_YYYYMMDD-HHMMSS
```

### 生成可视化图表

训练完成后（或训练过程中），运行可视化脚本：

```bash
# 基本用法 - 分析指定的训练日志
python generate_training_plots.py logs/sb3_multiproc_paper_config_20250617-103500

# 指定输出目录
python generate_training_plots.py logs/sb3_multiproc_paper_config_20250617-103500 --output_dir results/analysis

# 调整图像质量（DPI）
python generate_training_plots.py logs/sb3_multiproc_paper_config_20250617-103500 --dpi 200
```

## 生成的文件

### 训练过程中保存的数据

在 `logs/训练会话目录/paper_data/` 下：

- `episode_rewards_step_XXXX.csv` - Episode奖励数据
- `reward_components_step_XXXX.csv` - 奖励组件分析数据
- `skill_usage_step_XXXX.json` - 技能使用统计数据
- `final_training_summary.json` - 最终训练摘要

### 可视化分析结果

在 `输出目录/analysis/` 下：

- `training_progress_analysis.png` - 训练进展分析（4个子图）
- `reward_components_analysis.png` - 奖励组件趋势分析
- `skill_usage_analysis.png` - 技能使用分析（4个子图）
- `training_analysis_report.txt` - 详细的文本统计报告

## 图表内容说明

### 1. 训练进展分析 (`training_progress_analysis.png`)

- **左上**: Episode奖励趋势，包含原始数据和滑动平均
- **右上**: 奖励分布直方图，显示奖励的统计分布
- **左下**: Episode长度趋势，显示每个episode的持续时间
- **右下**: 奖励稳定性分析，显示100-episode滑动窗口的均值和标准差

### 2. 奖励组件分析 (`reward_components_analysis.png`)

- 分别显示环境奖励、团队判别器奖励、个体判别器奖励的变化趋势
- 每个组件都包含原始数据和滑动平均线

### 3. 技能使用分析 (`skill_usage_analysis.png`)

- **左上**: 技能切换次数的累积趋势
- **右上**: 最终的团队技能使用分布柱状图
- **左下**: 技能使用演变热图，显示各技能随时间的使用变化
- **右下**: 技能多样性指标（熵）的演变

## 优势对比

| 特性 | 原版本 | 修复版本 |
|------|--------|----------|
| 内存使用 | ❌ 容易溢出 | ✅ 稳定低耗 |
| 训练效率 | ❌ 被绘图拖慢 | ✅ 专注训练 |
| 数据完整性 | ❌ 可能因崩溃丢失 | ✅ 持续保存 |
| 可视化质量 | ⚠️ 受内存限制 | ✅ 高质量输出 |
| 灵活性 | ❌ 固定绘图 | ✅ 按需生成 |

## 故障排除

### 如果可视化脚本出错

1. **检查数据文件**: 确保 `paper_data` 目录存在且包含数据文件
2. **检查依赖**: 确保安装了 pandas, matplotlib, numpy
3. **降低DPI**: 如果仍有内存问题，使用 `--dpi 100`

```bash
# 检查可用的数据文件
ls logs/你的训练会话/paper_data/

# 降低内存使用
python generate_training_plots.py logs/训练会话 --dpi 100
```

### 如果没有数据文件

- 确保训练时启用了数据导出（默认启用）
- 检查 `--export_interval` 设置，确保训练运行时间足够长
- 使用 `--detailed_logging` 获得更多数据

## 总结

这个修复方案：
1. **完全解决了内存问题** - 训练过程不再生成图表
2. **保持了数据完整性** - 所有数据仍被收集和保存
3. **提供了更好的可视化** - 独立脚本可以生成更高质量的图表
4. **提高了训练效率** - 专注于训练任务，减少I/O开销

现在您可以安全地运行长时间训练，而不用担心内存溢出问题！
