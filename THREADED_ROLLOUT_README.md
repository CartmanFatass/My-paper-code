# HMASD 多线程 Rollout-based 训练

基于论文 Appendix E 的严格实现，采用 16 个 training threads + 32 个 rollout threads 的多线程架构。

## 📊 架构对比

### 原版本 vs 多线程版本

| 特性 | 原版本 | 多线程版本 |
|------|--------|------------|
| 训练架构 | 串行（收集→训练→收集） | 并行（收集∥训练） |
| 环境交互 | 32个进程（SubprocVecEnv） | 32个线程（持续交互） |
| 训练方式 | 主线程训练 | 16个专用训练线程 |
| 硬件利用率 | 训练时环境空闲 | GPU/CPU同时工作 |
| 论文符合度 | Algorithm 1 | Algorithm 1 + Appendix E |
| 数据传输 | 直接访问 | 线程安全队列 |

### 性能提升预期

1. **更高的样本收集效率**: rollout线程持续运行，无等待时间
2. **更好的硬件利用率**: GPU训练时CPU继续收集数据
3. **更稳定的训练**: 持续的数据流，减少batch间隔
4. **更快的收敛**: 更频繁的模型更新

## 🏗️ 多线程架构详解

### 核心组件

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   32个 Rollout  │───▶│  线程安全数据   │───▶│   16个 Training │
│     Threads     │    │     缓冲区      │    │     Threads     │
│                 │    │                 │    │                 │
│ - 环境交互      │    │ - Queue机制     │    │ - 模型训练      │
│ - 数据收集      │    │ - 自动负载均衡  │    │ - 参数更新      │
│ - 持续运行      │    │ - 线程安全      │    │ - 15轮PPO       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1. Rollout Threads (32个)

**功能**: 持续环境交互和数据收集
- 每个线程管理一个独立环境实例
- 执行 `agent.step()` 获取动作
- 与环境交互获取经验
- 将经验放入线程安全缓冲区
- 无等待，持续运行

**关键代码**:
```python
class RolloutWorker:
    def run_step(self, agent_proxy):
        # 获取动作
        actions, action_info = agent_proxy.get_actions(...)
        
        # 环境交互
        next_observations, rewards, dones, next_state = self.step_environment(actions)
        
        # 构造经验并放入缓冲区
        experience = {...}
        self.data_buffer.put(experience, block=False)
```

### 2. Training Threads (16个)

**功能**: 持续模型训练和参数更新
- 从缓冲区获取经验数据
- 批量存储到 agent 的 replay buffer
- 触发 rollout 更新（15轮PPO）
- 只有 worker 0 执行更新，其他继续处理数据

**关键代码**:
```python
class TrainingWorker:
    def perform_update(self):
        if self.worker_id == 0:  # 只有第一个worker执行更新
            update_info = self.agent_proxy.update()
            # 执行15轮PPO + 判别器训练
```

### 3. 线程安全数据缓冲区

**功能**: 连接 rollout 和 training 线程
- 使用 `queue.Queue` 实现线程安全
- 自动负载均衡
- 防止数据丢失
- 统计监控

**关键代码**:
```python
class DataBuffer:
    def __init__(self, maxsize=10000):
        self.queue = queue.Queue(maxsize=maxsize)
        self.total_added = ThreadSafeCounter()
        self.total_consumed = ThreadSafeCounter()
```

### 4. AgentProxy (线程安全代理)

**功能**: 为多线程提供线程安全的 agent 接口
- 使用 Lock 保护 agent 访问
- 管理环境特定的状态
- 批量经验存储
- 统一更新触发

## 🚀 使用指南

### 快速开始

1. **快速测试**:
```bash
python test_threaded_rollout.py
```

2. **查看架构对比**:
```bash
python test_threaded_rollout.py --compare
```

3. **启动完整训练**:
```bash
python start_threaded_rollout_training.py --duration 2.0
```

### 命令行参数

#### 线程配置（论文标准）
- `--training_threads 16`: 训练线程数
- `--rollout_threads 32`: Rollout线程数
- `--buffer_size 10000`: 数据缓冲区大小

#### 训练配置
- `--duration 2.0`: 训练持续时间（小时）
- `--scenario 2`: 场景选择
- `--device auto`: 计算设备

#### 环境配置
- `--n_uavs 5`: 无人机数量
- `--n_users 50`: 用户数量
- `--user_distribution uniform`: 用户分布

### 示例命令

```bash
# 论文标准配置（2小时训练）
python start_threaded_rollout_training.py \
  --duration 2.0 \
  --training_threads 16 \
  --rollout_threads 32 \
  --scenario 2

# 轻量级测试配置
python start_threaded_rollout_training.py \
  --duration 0.5 \
  --training_threads 4 \
  --rollout_threads 8 \
  --n_uavs 3 \
  --n_users 20

# 高性能配置
python start_threaded_rollout_training.py \
  --duration 4.0 \
  --training_threads 32 \
  --rollout_threads 64 \
  --buffer_size 20000 \
  --device cuda
```

## 📈 监控和调试

### 训练进度监控

训练过程中会每分钟输出进度信息：
```
训练进度: 25.0% (0.5h / 2.0h), 剩余: 1.5h
Rollout: 样本=12,543, Episodes=156
Training: 更新=8, 处理样本=12,340
Buffer: 队列=45, 添加=12,543, 消费=12,498
```

### 详细统计信息

每10分钟输出详细统计：
```
=== 详细统计信息 ===
Rollout Workers:
  Worker 0: 样本=423, Episodes=5, 当前Episode步数=67
  Worker 1: 样本=401, Episodes=6, 当前Episode步数=23
  ...
Training Workers:
  Worker 0: 更新=8, 处理样本=3,245
  Worker 1: 更新=0, 处理样本=3,190
  ...
```

### 线程健康检查

自动检测线程状态：
- 死亡线程检测
- 数据流检查
- 内存使用监控

## ⚙️ 配置优化

### 线程数量调优

1. **Training Threads**:
   - 默认: 16 (论文配置)
   - CPU密集型: 等于CPU核心数
   - GPU瓶颈: 可以减少到4-8

2. **Rollout Threads**:
   - 默认: 32 (论文配置)  
   - 环境简单: 可以增加到64
   - 内存限制: 减少到16

3. **缓冲区大小**:
   - 默认: 10000
   - 高速训练: 增加到20000
   - 内存限制: 减少到5000

### 性能调优建议

1. **CPU优化**:
   - rollout_threads ≈ CPU核心数
   - 避免过度调度开销

2. **GPU优化**:
   - training_threads = 4-16
   - 保证GPU利用率

3. **内存优化**:
   - 监控buffer使用率
   - 调整batch_size

## 🔧 故障排除

### 常见问题

1. **线程死锁**:
   - 检查AgentProxy的Lock使用
   - 确保异常处理正确

2. **内存泄漏**:
   - 监控缓冲区大小
   - 检查环境资源释放

3. **性能下降**:
   - 调整线程数量
   - 检查GIL影响

### 调试技巧

1. **启用调试模式**:
```bash
python start_threaded_rollout_training.py --debug
```

2. **减少线程数测试**:
```bash
python start_threaded_rollout_training.py \
  --training_threads 2 \
  --rollout_threads 4
```

3. **检查日志**:
```bash
tail -f logs/threaded_rollout_training_*/threaded_rollout_training.log
```

## 📝 开发说明

### 与原版本的兼容性

- 保持相同的 agent 接口
- 相同的配置系统
- 相同的模型保存格式
- 相同的TensorBoard日志

### 扩展性

- 可以轻松调整线程数量
- 支持不同的缓冲区策略
- 可以添加新的监控指标
- 支持分布式扩展

### 测试覆盖

- 单元测试: `test_threaded_rollout.py`
- 集成测试: 完整训练流程
- 性能测试: 与原版本对比
- 稳定性测试: 长时间运行

---

## 🎯 总结

多线程版本严格按照论文 Appendix E 实现，提供：

1. **更高的训练效率**: 并行数据收集和模型训练
2. **更好的资源利用**: GPU和CPU同时工作
3. **更稳定的性能**: 持续的数据流
4. **完全的论文符合**: 16+32线程架构

这个实现解决了原版本中数据收集和训练串行执行的瓶颈，显著提升了训练效率和硬件利用率。
