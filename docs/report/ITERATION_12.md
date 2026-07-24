# 第 12 轮：动态成员槽位布局不变性

## 本轮问题和决定

前几轮的成员编号始终较密集，而且 padding 容量接近实际活跃成员数。这留下了一个
重要反例：算法可能并没有真正学会处理“动态集合”，而只是依赖低编号、连续槽位和
固定容量。第 12 轮冻结现有模型和逻辑 episode，只改变同一批 lifecycle key 在张量中
的物理位置。

正式结果为 `SLOT_LAYOUT_INVARIANT_G11`。同一逻辑行为在反转、稀疏和更大 padding
容量下逐 episode 完全一致。因此，在本轮覆盖的 N=12–40 和八次成员变更条件内，当前
算法没有依赖“agent 必须占据前缀槽位”这一隐藏假设。

## 算法、环境和预算

- 源码 commit：`5713af3d477f10c41cb3f1925a2b920dfdc7dd74`
- 正式目录：`logs/formal_slot_layout_g11_cpu_20260723_5713af3_r1`
- 模型：G8 的三个 update-250 终态 checkpoint
- 新训练：无，optimizer steps 为 0
- 逻辑环境：G10 的 oscillating scale-churn profile，N=12–40、八次成员编辑
- 物理布局：dense-48、reverse-48、odd sparse-96、affine scattered-128
- 评估：3 replicates × 4 layouts × deterministic/stochastic，共 24 cells；
  每 cell 64 episodes，共 1,536 个 utility 值
- 设备：AMD CPU、PyTorch 2.7.0+cpu、单线程；无 CUDA 比较、回退或混合

## 证据闭合

冻结 checkpoint 导入、评估和分析均正常退出。三个 checkpoint 的复制最大差异均为
0，全部 cell 的模型状态保持精确不变。24 个组合唯一且完整，每个数组恰好包含 64 个
episode。四种布局的成员事件、owner/presentation/frontier priority、wave、需求和
lifecycle 冻结/恢复均通过构造性控制。

我以 dense-48 为基准，逐 replicate、逐随机模式、逐 episode 比较 persistent、short
和 utility。reverse-48、sparse-96、affine-padded-128 的组件不匹配数均为 0。独立按
冻结的 first-match 顺序复算，也得到 `SLOT_LAYOUT_INVARIANT_G11`。

## 正式结果

四种布局的 deterministic utility CI95 完全相同：

`[0.92529296875, 0.9513706931089744, 0.9991316105769231]`

最低 layout/replicate deterministic mean 为 `0.92529296875`，全部 stochastic cell 的
均值为 `0.8969245793269232`。二者分别高于 0.85 和 0.80 的冻结稳定性门槛。

## 科学影响与限制

本轮排除了三个直接的固定布局解释：低编号偏好、连续 key 偏好，以及容量必须接近
活跃 N。结合第 11 轮结果，当前测试版已经在 N≤40、八次高频 churn、二者组合以及
多种物理槽位布局上保持可用。这比单纯“网络参数量不依赖 agent 数”更强，因为它验证
了实际闭环行为的集合式等变性。

仍不能推出：

- N>40 或任意 N 都可用；
- 任意非双射映射、任意事件密度或任意任务分布都稳定；
- 生命周期/技能周期、技能选择或 EHC 已被解决；
- 相对其他算法存在性能优势。

## 下一轮

最近的剩余反例是规模上限，而不是槽位排列。下一边界为
`ULTRA_SCALE_OPEN_ROSTER_G12`：保持 G8 checkpoint、任务语义和零训练不变，测试 N>40
时当前前缀归一化算法是否仍能维持绝对可用性。若失败，后续轮次再针对实际暴露的规模
瓶颈做最小算法修正，而不会通过降低门槛救结果。

本轮消耗 1 次结论性迭代，剩余 5 次。
