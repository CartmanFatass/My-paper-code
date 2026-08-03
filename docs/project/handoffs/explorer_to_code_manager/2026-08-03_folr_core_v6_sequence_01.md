# Sequence 01：FOLR Core v6 的只读工程侦察与单候选科学审计准备

这份 brief 只交接 `CAND-VAP-FOLR-CORE@constructive-revision-v6`。它是原顺序任务的 sequence 01；其他候选不在本次范围内，也不应因为阅读本文件而被预加载、比较、合并或执行。

当前最有价值的下一步不是实现完整 FOLR，也不是训练或跑回报实验，而是确认一个更窄的问题是否在现有代码中可被干净检验：在同一、不间断的 owner epoch 内，S03 私有载荷中的一个二元差异，是否能够在排除缓存、待执行动作、随机数状态和其他旁路以后，因果地改变事件后第一次重新计算的动作核。

Code Manager 现在可以先做候选局部的只读工程侦察，并据此准备一次单候选 External Pro 科学审计。本文不授予代码修改、运行、训练或计算权限，也不把侦察结果当作候选的正负科学结论。

## 候选的科学核心

FOLR 的较大目标是：在 join、leave、replacement、rejoin 和 slot reuse 中，正确处理 survivor continuity、所有权 epoch 与延迟 credit routing，而不假设隐藏状态能跨所有权 epoch 携带。

完整机制设想包含一个权威生命周期 ledger：它为新 owner epoch 建立新身份，拒绝过期观察，重建 typed masks，只保留经过反事实见证的 survivor-private state，并按不可变 action instance 路由迟到奖励。上述完整机制不是当前验证对象；当前只验证 S03 在第一次事件后动作中的可访问信息作用。基础 learner 不应为这个判别器而改变，也不应引入 learned lifecycle driver。

本次允许检验的最窄主张是：

> 对一个已注册、对 readout 敏感的 cell，在同一不间断 owner epoch 内，只有当固定载荷 null 与 complete-reset null 都通过以后，才能主张 S03 payload 保存了一个私有二元区别，并因果介导了该区别对第一次全新重算的事件后动作核的影响。

这个主张不包含跨 epoch 携带、不包含 partner transfer、不包含长期回报改进，也不包含完整生命周期 ledger 的正确性。

## 必须闭合的因果歧义

观察到动作核依赖分支标签 `B`，本身不能证明信息来自安装后的 S03 payload。`B` 还可能通过以下路径越过事件边界：

- 事件前已经确定、事件后才执行的 pending action；
- 缓存的 action kernel、logit、sample 或 policy output；
- slot-local buffer 或未清空的临时状态；
- 以 `B` 为条件或被先前调用次序改变的 RNG state；
- owner/epoch、mask、observation、rebuild 或其他非 S03 的可见字段；
- event linearization 前后顺序不清造成的读取竞态。

因此，工程侦察的第一目标是重建这些路径，而不是直接寻找一个看起来能跑的实验入口。

## 六个确定性动作核判别器

选择一个冻结的 registered cell。它必须具有正权重、至少两个合法动作、共同的写入前 snapshot，并在整个判别过程中保持同一个 owner epoch。令分支标签为 `B∈{0,1}`，令安装到 S03 的私有 payload 为 `P∈{0,1}`。

需要得到四个 payload-factorial 核和两个 complete-reset 核：

- `K_(0<-0)`：分支 `B=0`，安装 payload `P=0`；
- `K_(0<-1)`：分支 `B=1`，但强制安装 payload `P=0`；
- `K_(1<-0)`：分支 `B=0`，但强制安装 payload `P=1`；
- `K_(1<-1)`：分支 `B=1`，安装 payload `P=1`；
- `K_reset_0`：分支 `B=0`，在第一次事件后 readout 前执行 complete reset；
- `K_reset_1`：分支 `B=1`，执行同样的 complete reset。

这里的箭头记法是 `payload <- branch`。四个 factorial 分支共享同一个写入前 snapshot；除了终端的私有 S03 写入之外，`B` 不得进入任何状态、动作或其他对 readout 可见的路径。

必须冻结并核对以下时序：

1. 私有值写入并完成 S03 更新；
2. 权威事件发生并完成 linearization；
3. owner/epoch、observation、typed mask 与其他事件后输入完成 rebuild；
4. 在没有复用旧 kernel、logit、sample 或 pending action 的条件下读取第一次全新计算的动作核。

估计量是第一次事件后动作核之间的精确 total variation，以及应相等或应不相等的核关系。优先使用确切概率核；如果实现只能暴露 logits 或 sample，Code Manager 应明确记录这一事实，不得自行把代理量升级为确切 kernel 证据。

### 通过条件

只有同时满足以下条件，才支持上述窄主张：

- 固定 payload 为 `0` 时，改变 branch label 不改变动作核：`K_(0<-0) = K_(0<-1)`；
- 固定 payload 为 `1` 时，改变 branch label 不改变动作核：`K_(1<-0) = K_(1<-1)`；
- 至少一个固定 branch 下的 payload 对比非零，例如 `K_(0<-0) != K_(1<-0)` 或 `K_(0<-1) != K_(1<-1)`；
- complete reset 擦除 branch 依赖：`K_reset_0 = K_reset_1`；
- owner/epoch 连续、共同 pretreatment snapshot、合法动作集和正 cell 权重等前置见证全部成立；
- event 后 readout 确认是新计算结果，而非缓存或 pending-action 复用。

### 立即停止或记为对象不足的条件

出现任一情况，都不能把结果解释为 S03 payload 的因果访问证据：

- owner 或 epoch 在比较中发生中断；
- slot authority 或身份信息泄漏 branch label；
- 写入前 snapshot 或其他 pretreatment 条件不一致；
- `B` 存在任何非 S03 路径；
- 第一次事件后动作来自缓存、预采样或 pending action；
- 任一固定-payload branch-label null 失败；
- complete-reset null 失败；
- 当前实现无法获得可比较的确切动作核；
- payload 变化对动作核没有任何可见影响；
- 找不到满足正权重和至少两个合法动作的 registered cell。

这些情况需要区分“设计被反驳”与“实例或接口尚不具备”。缺少可读取对象、无法冻结 snapshot 或没有确切 kernel readout，首先是工程对象不足，不是完整 FOLR 的科学 NO_GO。

## Code Manager 现在应完成的只读侦察

请在不修改代码、不运行计算的前提下，围绕这个候选建立一张候选局部的接口与数据流图。至少回答：

1. owner identity 与 epoch identity 在哪里创建、保存、比较和失效；slot reuse 是否可能绕开 epoch 检查。
2. S03 的私有状态保存在哪里，终端写入和 S03 update 的调用顺序是什么；哪些代码能读取它。
3. 权威事件的 linearization 点在哪里；observation、typed/legal-action mask 和其他事件后输入何时 rebuild。
4. 第一次事件后 action kernel 从哪些数据计算；是否存在 kernel、logit、sample、RNG、pending action 或 slot-local buffer 缓存。
5. 如何证明 event 后 readout 是 fresh recomputation；需要清除或禁止哪些缓存路径。
6. `B` 可能到达 readout 的所有非 S03 路径；哪些路径能通过构造共同 snapshot 与强制 payload transplant 被封闭。
7. complete reset 在当前实现中的真实含义和入口；它是否同时擦除 S03、缓存、pending action、slot-local 临时状态与相关 RNG 条件。
8. 是否已有一个 registered cell 能满足正权重、至少两个合法动作、共同写入前 snapshot 和不间断 owner epoch；若没有，具体缺少哪个对象。
9. 当前接口能否直接读取确切动作概率核；如果不能，只读侦察能确认的最接近对象是什么，以及为何它不足以支持主张。

侦察输出应给出确切代码路径、关键函数/类型/字段和读写顺序，并明确哪些结论来自静态代码、哪些仍需未来运行见证。可以指出最小候选局部 instrumentation 或 fixture 需求，但不要实现它们。

## 随后准备的单候选 External Pro 科学审计

在完成语义 intake 和只读接口重建后，Code Manager 应为这个候选单独准备一次 `EXPLORER_TOY_DESIGN_ASSERTION_AUDIT`。审计问题应携带上述六核定义、事件时序、已发现的真实实现路径与仍未闭合的旁路，至少请 External Pro 判断：

- 六核设计在精确 event/cache/RNG closure 下，是否足以识别“payload 介导第一次事件后动作”的窄主张；
- 固定-payload 2×2 transplant 与 complete-reset equality 是否是最强的简单 null，还是还必须加入另一个 information-matched null；
- 在任何代码或计算之前，必须冻结哪些实现见证、实例对象和时序条件；
- 哪些结果类别能够支持或反驳哪一级主张，哪些推断必须继续保持不支持。

External Pro 负责科学审计结论；Code Manager 负责根据真实实现准备问题、提交和机械 intake。本文件不预先替 External Pro 选择答案，也不授权实验。

## 明确不允许从本次工作推出的结论

即使六核判别器未来通过，也不能据此声称：

- FOLR 对任务回报有益；
- 完整 lifecycle ledger 已正确；
- 私有状态可跨 owner epoch 携带；
- delayed-credit routing 已正确；
- joint coordination 或 partner-state transfer 已成立；
- 任意未注册 cell 或任意环境都具有相同性质。

本候选也不得与后续 sequence 的候选共享未审计的实例、证据或科学结论。

## 回传给 Explorer 的内容

请用自然语言结论开头，并在 `docs/project/handoffs/code_manager_to_explorer/` 写一份候选局部结果；如果公共反向文件暂不可用，可向 Explorer 任务 `019fc29d-ef93-7681-abba-2b9d63a866cf` 发送原生消息。结果应说明：

- 只读接口重建是否可行；
- 找到的确切代码位置、数据流和事件顺序；
- 哪些具体对象或接口仍缺失；
- 建议冻结的单候选 External Pro 审计边界与问题；
- 哪些观察只是工程事实，尚未构成科学 disposition。

在 Explorer 收到并解释 sequence 01 的结果之前，不应自动开始 sequence 02。任何计算仍需在科学合同冻结后取得单独、明确的用户授权。
