# 模式 01：loss、credit 与更新路径

适用：修改既有 learner 的 loss、credit、mask、参数权重或 critic 监督面。
不是设计新算法的授权。参考边界：UCOPE `clipped_policy_loss`、RCLE `weighted_loss`、
CBSC learner；具体任务必须绑定自己的版本。

## 五项交接的本次差异

1. 目标：从 `<已有可观察行为>` 改为 `<卡中选定行为>`；验收观察 loss、gradient 或参数变化中哪一项。
2. 路径：`<learner / 调用方 / 必须联动的 tests>`；保留其余文件与其他未提交改动。
3. 语义：精确引用样本单位、合法信息、reward/return、mask、归约、可训练参数与已选更新顺序。
4. 验收：`<最少的数值/梯度反例>` 及已有 focused tests；禁止用学习曲线变好替代实现验收。
5. 边界：只实施选定 loss；不擅改 dtype、normalization、seed、optimizer、预算或训练长度。

## L1 增量：工程约定

把适用的 shape/轴、类型、device、输入是否已 detach、是否允许原地修改写明；指出复用哪个
现有函数。输出 loss 的单位与分母必须来自共同任务事实。不要只写“按 PPO 标准实现”。
若共同卡已有定义，引用到具体段即可，无需重复整份推导。

## L2 增量：执行逻辑

说明“逐样本项 → 哪些项进入目标 → 怎样归约 → 哪些参数收梯度 → 何时更新”。
对本题相关的 clipping 位置、advantage/baseline 梯度隔离和 update 顺序给伪代码。
明确无有效决策时是零项、跳过更新还是其他已选行为；不要让执行者通过习惯决定。
参数出现在 Config/JSON 不够，必须能追到实际 loss 和受影响参数。

## L3 增量：局部范例

可引用 [masked_reduction.py](examples/masked_reduction.py)：agent 项先求和、再按完整 row
取均值的微例子。它强调 held row 是否保留在分母；不规定任何任务必须采用这个归约。
如果本任务按 eligible decision 平均或有权重，必须明确说明与范例不同。

用于验收的反例可覆盖一行有决策/另一行全 held、同一批中不同 agent mask、以及任务明确
要求的梯度去向。只选能改变结论的检查，不把整套列项变成每题必跑测试。
