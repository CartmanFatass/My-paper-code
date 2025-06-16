# HMASD Rollout-based训练架构

## 概述

本实现严格按照论文《Hierarchical Multi-Agent Skill Discovery》Algorithm 1和附录E的超参数设置，实现了rollout-based训练架构。这是论文推荐的标准训练方式，具有更好的训练稳定性和样本效率。

## 核心特性

### 1. 严格的论文实现
- **Rollout长度**: 128步（每个rollout收集的步数）
- **并行环境**: 32个（对应论文中的rollout_threads）
- **PPO轮数**: 15轮（严格对应论文附录E中的ppo_epoch=15）
- **小批次数量**: 1（使用全部rollout数据，不采样）

### 2. 数据收集流程
```
并行收集: 32个环境 × 128步 = 4096个样本
├── 技能分配: 每k=50步重新分配技能
├── 经验存储: 分别存入B_h(高层), B_l(低层), D(判别器)
└── 技能多样性: 自动确保技能探索的多样性
```

### 3. 训练阶段控制
```
PPO训练: 使用全部4096个样本训练15轮
├── 1. 更新协调器（高层策略）- 15轮
├── 2. 更新发现器（低层策略）- 15轮
├── 3. 更新判别器（从D中采样）- 每轮
└── 4. 清空缓冲区: 清空B_h和B_l，保留D
```

### 4. 缓冲区管理
- **严格PPO on-policy**: 训练后清空B_h和B_l
- **判别器数据保留**: 持久数据集D用于监督学习
- **技能分配追踪**: 跟踪每个环境的技能状态

## 配置参数

### 核心参数
```python
# Rollout-based训练参数（论文标准实现）
rollout_based_training = True       # 启用rollout模式
rollout_length = 128                # 每个rollout收集的步数
num_parallel_envs = 32              # 并行环境数量
ppo_epochs = 15                     # PPO训练轮数
num_mini_batch = 1                  # 小批次数量（使用全部数据）

# 目标样本计算
rollout_target_samples = 4096       # 32 × 128 = 4096个样本
```

### 流程控制参数
```python
# 数据收集阶段
rollout_skill_reassign_interval = 50   # 技能重新分配间隔
rollout_max_episode_length = 500       # 单个episode最大长度
rollout_early_termination = True       # 启用early termination

# 训练阶段控制
rollout_coordinator_first = True       # 优先更新协调器
rollout_clear_buffers_after_update = True  # 更新后清空PPO缓冲区
rollout_preserve_discriminator_data = True # 保留判别器数据
```

### 监控和调试
```python
# 调试和监控
rollout_log_interval = 10              # 日志间隔（每N个rollout）
rollout_save_interval = 100            # 模型保存间隔
rollout_eval_interval = 50             # 评估间隔
rollout_detailed_logging = True        # 详细日志记录
```

## 使用方法

### 1. 快速开始
```bash
# 基本训练（使用默认参数）
python train_rollout_based.py

# 指定rollout数量
python train_rollout_based.py --rollouts 1000

# 使用CPU训练
python train_rollout_based.py --device cpu

# 详细日志
python train_rollout_based.py --log-level DEBUG
```

### 2. 配置测试
```bash
# 测试配置的正确性和兼容性
python test_rollout_config.py
```

### 3. 自定义配置
```python
from config import Config

config = Config()
# 修改配置参数
config.rollout_length = 256        # 增加rollout长度
config.num_parallel_envs = 64      # 增加并行环境
config.ppo_epochs = 20             # 增加训练轮数

# 验证配置
config.validate_rollout_config()
config.print_config_summary()
```

## 训练流程详解

### 1. 初始化阶段
```python
# 创建32个并行环境
envs = [create_env() for _ in range(32)]

# 初始化HMASD智能体
agent = HMASDAgent(config, rollout_based_training=True)

# 验证配置
config.validate_training_mode()
config.validate_rollout_config()
```

### 2. 数据收集循环
```python
for step in range(128):  # rollout_length
    for env_id in range(32):  # num_parallel_envs
        # 技能分配（每k=50步）
        if step % 50 == 0:
            assign_skills(env_id)
        
        # 执行动作
        actions = agent.step(state, obs, env_id=env_id)
        
        # 环境交互
        next_state, next_obs, reward, done = env.step(actions)
        
        # 存储经验
        agent.store_transition(...)
```

### 3. 训练阶段
```python
# 检查更新条件
if agent.should_rollout_update():
    # 执行15轮PPO训练
    update_info = agent.rollout_update()
    
    # 缓冲区自动清空（PPO on-policy要求）
    # B_h和B_l被清空，D保留
```

### 4. 评估和保存
```python
# 定期评估
if rollout_id % eval_interval == 0:
    eval_reward = evaluate_policy(agent)
    
# 定期保存
if rollout_id % save_interval == 0:
    agent.save_model(f"checkpoint_{rollout_id}.pth")
```

## 性能优化

### 1. 数值稳定性
- **梯度裁剪**: 防止梯度爆炸
- **价值函数裁剪**: 限制价值函数输出范围
- **Advantage标准化**: 稳定PPO训练

### 2. 内存管理
- **自动缓冲区清空**: 防止内存累积
- **判别器数据管理**: 限制持久数据集大小
- **GRU状态重置**: 定期重置防止数值不稳定

### 3. 计算优化
- **向量化环境**: 提高并行效率
- **GPU加速**: 支持CUDA训练
- **混合精度**: 可选的内存优化

## 监控和调试

### 1. TensorBoard监控
```python
# 损失监控
writer.add_scalar('Rollout/CoordinatorLoss', loss, rollout_id)
writer.add_scalar('Rollout/DiscovererLoss', loss, rollout_id)
writer.add_scalar('Rollout/DiscriminatorLoss', loss, rollout_id)

# 性能监控
writer.add_scalar('Rollout/UpdateDuration', duration, rollout_id)
writer.add_scalar('Rollout/TotalSteps', total_steps, rollout_id)

# 缓冲区监控
writer.add_scalar('Rollout/BufferSizeBefore', size_before, rollout_id)
writer.add_scalar('Rollout/BufferSizeAfter', size_after, rollout_id)
```

### 2. 日志系统
```python
# 详细训练日志
main_logger.info(f"Rollout #{rollout_id} 完成: "
                f"奖励={total_reward:.4f}, "
                f"步数={total_steps}, "
                f"耗时={duration:.2f}s")

# 缓冲区状态日志
main_logger.info(f"缓冲区状态: 高层({size_before}→{size_after}), "
                f"低层({low_before}→{low_after})")
```

### 3. 配置验证
```python
# 自动配置检查
config.validate_training_mode()     # 训练模式一致性
config.validate_rollout_config()    # Rollout参数合理性
config.print_config_summary()       # 打印配置摘要
```

## 与其他训练模式的比较

| 特性 | Rollout-based | Episode-based | Sync模式 |
|------|--------------|---------------|----------|
| **论文标准** | ✅ 严格按照论文 | ⚠️ 变体实现 | ❌ 实验性质 |
| **训练稳定性** | ✅ 高稳定性 | ⚠️ 中等稳定性 | ❌ 可能不稳定 |
| **样本效率** | ✅ 高效率 | ⚠️ 中等效率 | ❌ 低效率 |
| **实现复杂度** | ✅ 中等复杂度 | ✅ 简单 | ❌ 高复杂度 |
| **推荐程度** | ✅ 强烈推荐 | ⚠️ 可选 | ❌ 不推荐 |

## 故障排除

### 常见问题

1. **内存不足**
   ```python
   # 减少并行环境数量
   config.num_parallel_envs = 16  # 从32减少到16
   
   # 减少rollout长度
   config.rollout_length = 64     # 从128减少到64
   ```

2. **训练过慢**
   ```python
   # 减少PPO轮数
   config.ppo_epochs = 10         # 从15减少到10
   
   # 增加日志间隔
   config.rollout_log_interval = 20  # 减少日志频率
   ```

3. **数值不稳定**
   ```python
   # 启用梯度裁剪
   config.rollout_gradient_clip_enabled = True
   
   # 启用advantage标准化
   config.rollout_advantage_normalization = True
   
   # 减小学习率
   config.lr_coordinator = 1e-4
   config.lr_discoverer = 1e-4
   ```

### 调试技巧

1. **使用测试配置**
   ```bash
   # 先运行测试验证配置
   python test_rollout_config.py
   ```

2. **启用详细日志**
   ```bash
   # 使用DEBUG级别日志
   python train_rollout_based.py --log-level DEBUG
   ```

3. **小规模测试**
   ```python
   # 修改为测试参数
   config.rollout_length = 16
   config.num_parallel_envs = 4
   config.ppo_epochs = 2
   ```

## 结论

Rollout-based训练架构是HMASD算法的标准实现方式，具有以下优势：

1. **严格按照论文**: 确保实验结果的可重复性
2. **训练稳定性**: PPO on-policy特性确保稳定训练
3. **样本效率**: 批量训练提高样本利用率
4. **易于调试**: 清晰的训练流程便于问题定位

推荐在实际应用中优先使用此训练模式。
