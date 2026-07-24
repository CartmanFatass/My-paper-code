# 第 1 轮结论性迭代：G0 无访问结果

## 本轮科学问题与运行前决策

本轮测试 `EVENT_HELD_COMMITMENT_LINK_G0`：在冻结的 OR/DUM/EHC 比较中，
事件保持承诺链路是否能够在当前非日历 benchmark 上被学习并产生可解释的
效用增益。运行前已冻结奖励、观察、PPO、种子、预算、阈值、因果审计和
first-match 结果优先级；运行后不得通过调参、改名或增加诊断来救援结果。

## 实验环境与证据

```text
source_commit=fb9909711a2ca8628f3d534936b771885e53b26d
run=logs/formal_event_held_cpu_20260722_fb99097_r2
backend=cpu
torch_threads=1
training=1250/1250 updates
evaluation=60/60 cells
formal=true
```

本机为 AMD CPU-only 环境，使用注册的 CPU 解释器；本项目明确不要求
CPU/CUDA 等价比较。训练、评估和分析均完整，`operational_valid=true`，
`operational_errors=[]`，所以结果不是工程失败。

## 登记结果

冻结的访问阈值为 `0.78`。OR/DUM 效用 CI95 为
`[0.4487899933, 0.6897088860]`，EHC 为
`[0.4448965615, 0.6722709391]`；最大上界仍低于访问阈值。主增益 G 的
CI95 为 `[-0.06003934, 0.05759664]`，但在 first-match 规则中访问失败先于
机制解释。

登记分支为：

```text
NO_ACCESS_THIS_BENCHMARK
```

## 对科学决策的影响

- 永久关闭这一精确 G0 benchmark/比较，不再重跑、调参、改名或救援。
- 本轮只说明当前 benchmark 在冻结预算与策略类下没有提供足够访问，不能据此
  判断 EHC 链路有效或无效。
- 外部 Pro 复核确认了 first-match 解释，并选择独立的 access-positive、
  mechanism-matched G1，而不是修改 G0。
- 本轮消耗 1 次结论性迭代，结束时剩余 4 次。

## 本轮不能支持的结论

本轮不能证明 EHC 无用、普通 recurrence 更好、CPU 导致失败，也不能支持改变
奖励、观察、阈值、预算或种子来重新解释 G0。

## 下一边界

定义并运行独立的 `ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1`，先保证所有组
可以访问，再解释 EHC 相对普通 recurrence 和 link-null control 的增益。
