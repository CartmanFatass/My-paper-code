# 严格 On-Policy Rollout 训练模式说明

本文档说明了对 `train_multiproc_config_1.py` 和 `config_1.py` 的修改，以实现严格的 on-policy 训练原则。

## 主要修改

### 1. 配置文件修改 (config_1.py)

添加了新的参数：
```python
rollout_length = 128     # 每次rollout收集的步数 (严格on-policy)
```

### 2. 训练循环重构 (train_multiproc_config_1.py)

#### 原始训练模式问题
- 基于缓冲区大小或固定步数间隔进行更新
- 来自不同episode的数据混合在一起
- 缓冲区没有在更新后清空，导致新旧数据混合

#### 新的严格 On-Policy 训练模式

**核心设计原则：**
- **固定长度rollout**: 每次收集固定的 `rollout_length` 步数据
- **严格更新-清空循环**: 收集数据 → 更新agent → 清空buffer → 重复
- **Episode边界处理**: 当episode结束时，继续在新episode中收集剩余步数

**训练流程：**
```
while total_steps < config.total_timesteps:
    # 1. 收集 rollout_length 步的数据
    for rollout_step in range(config.rollout_length):
        # 选择动作、执行动作、存储经验
        # 处理episode完成但继续收集数据
    
    # 2. 使用收集的数据更新网络
    if 缓冲区数据足够:
        agent.update()
        agent.clear_buffers()  # 严格清空缓冲区
    
    # 3. 重复下一个rollout
```

## 关键特性

### 1. 严格的数据隔离
- 每个rollout的数据完全独立
- 更新后立即清空缓冲区
- 避免新旧数据混合

### 2. 可调节的rollout长度
- `rollout_length = 128` (可调节)
- 平衡数据效率和训练稳定性
- 可以根据环境特性调整

### 3. Episode边界处理
- Episode结束不影响rollout完整性
- 自动在新episode中继续收集数据
- 保持rollout长度的一致性

### 4. 详细的日志记录
```
Rollout更新 X (收集了 Y 步), 总步数 Z, 
高层损失 A, 低层损失 B, 判别器损失 C, 已用时间 D
已清空缓冲区，开始新的rollout
```

## 与原版本的区别

| 特性 | 原版本 | 新版本 (On-Policy) |
|------|--------|-------------------|
| 更新时机 | 基于缓冲区大小/固定步数 | 基于rollout长度 |
| 数据管理 | 缓冲区累积，可能混合 | 严格rollout隔离 |
| Episode处理 | 可能中断数据收集 | 跨episode连续收集 |
| 缓冲区清理 | 不定期清理 | 每次更新后立即清空 |
| On-Policy程度 | 部分on-policy | 严格on-policy |

## 参数调优建议

### rollout_length 选择
- **小值 (64-128)**: 更严格的on-policy，但可能训练不稳定
- **中值 (128-256)**: 平衡效率和稳定性 (推荐)
- **大值 (256-512)**: 更稳定但less on-policy

### 与其他参数的关系
- `rollout_length` 应该 <= `buffer_size`
- 考虑 `rollout_length * num_envs` 的总数据量
- 确保 `batch_size` <= rollout收集的总数据量

## 使用方法

### 训练命令
```bash
python train_multiproc_config_1.py --mode train --scenario 2
```

### 关键参数
- `--num_envs`: 并行环境数量 (默认使用config中的32)
- `--scenario`: 场景选择 (1=基站模式, 2=协作组网模式)
- `--log_level`: 日志级别 (info推荐，可看到rollout信息)

## 预期效果

### 优势
1. **更严格的on-policy学习**: 避免过时数据影响
2. **更稳定的训练**: 固定数据量，预测性更好
3. **更好的sample efficiency**: 每个样本都是最新策略生成
4. **清晰的训练节奏**: 明确的收集-更新-清空周期

### 可能的挑战
1. **初期可能不稳定**: 严格on-policy可能导致初期波动
2. **需要调参**: rollout_length需要根据环境调整
3. **内存使用**: 需要确保agent有clear_buffers方法

## 需要的Agent方法

确保 HMASDAgent 类包含以下方法：
```python
def clear_buffers(self):
    """清空所有缓冲区，用于严格on-policy训练"""
    self.low_level_buffer.clear()
    self.high_level_buffer.clear()
    # 清空其他相关缓冲区
```

如果该方法不存在，需要在 `hmasd/agent.py` 中添加。

## 监控指标

关注以下日志信息：
- Rollout更新频率和步数
- 缓冲区清空确认
- Episode完成与rollout边界的关系
- 训练损失的变化趋势

## 故障排除

1. **如果出现 `agent.clear_buffers()` 方法不存在错误**:
   - 需要在HMASDAgent中添加该方法
   - 或者注释掉该调用行（会降低on-policy严格性）

2. **如果训练不稳定**:
   - 增加rollout_length
   - 检查学习率设置
   - 确认缓冲区大小充足

3. **如果内存不足**:
   - 减少rollout_length
   - 减少并行环境数量
   - 优化缓冲区内存使用
