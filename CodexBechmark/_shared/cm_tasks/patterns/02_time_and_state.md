# 模式 02：时间、episode 边界和状态生命周期

适用：环境适配、termination/truncation、动作保持、循环状态、出生/离开等边界变更。
参考 FOLR continuation、UCOPE HoldState 和 SCDMP 段回报任务；不默认它们的算法相同。

## 五项交接的本次差异

1. 目标：在 `<具体边界事件>` 后，`<哪些状态/输出>` 应怎样变化。
2. 路径：`<adapter / collector / storage / target consumer>` 的必要调用链和 owned 文件。
3. 语义：任务 horizon、终止/截断含义、reward 与折扣时钟、actor/critic 可见信息、状态归属。
4. 验收：给最小事件序列与期望可观察结果；比较连续/新 episode/实体替换的相关路径。
5. 边界：不改任务定义、动作时机或信息条件；工程修复不授权新的科学设计。

## L1 增量

定义 primitive step 与 decision/segment 的区别；列本题相关状态的 owner、shape、更新与重置
位置。说明 adapter 返回的是 final observation 还是自动 reset 后的 observation。
不要用一个 `done` 名称代替这些事实，也不要由某环境库的默认约定倒推本任务语义。

## L2 增量

按“读 pre-state → 选/保持动作 → 环境 step → 记录 reward/final state → 判断 continuation →
决定 bootstrap/trace/reset → 下一状态”写本题需要的次序。
实体索引复用时，指出是否仍是同一实体；不同 agent 的 held/RNN state 不能互相继承。
若任务用持续时间折扣或有限 horizon，精确引用其已选公式；不要擅自加 bootstrap。

## L3 增量

[transition_masks.py](examples/transition_masks.py) 演示一种持续任务被外部时间限制截断的
情形：bootstrap 与跨 reset 连接使用不同 mask。任务本身的 finite horizon 终止不能直接
照搬。范例不覆盖一般 recurrent buffer、auto-reset observation 或 SMDP。

依据：[Gymnasium 对 termination/truncation 的说明](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)。
任务/信息/时间解释同时参照 HMASD 已发布 foundations §§1–2、§5；不由概念说明变更原卡。
