# HMASD native Codex workflow

Workflow revision: 2026-08-29.6

本文只规定 top-level task 之间的通信、存活、Effect 与 Git 交接。公共字段含义、caller
matrix、模型、leaf 与 workspace 边界只由 `AGENTS.md` 定义；每个角色的内部方法只由自己的
top-level session skill 定义。这里不复制这些内容。

HMASD 直接使用 Codex Desktop 可见的 task ID、history、status、create/send/read/wait、archive
和 native worktree。项目不为这些产品事实创建第二套身份、收件箱、注册表、回执、重试器或
调度器。

## 1. Top-level participants and edges

长期 participant 只有四类：Root、Portfolio、`EM/<direction>` 和
`CM/<direction-or-shared>`。正常相邻链路是：

`Root ↔ Portfolio ↔ EM/<direction> ↔ CM/<direction>`

由产生需求的 requester 编写并直接投递完整消息；callee 只向该 requester 返回结果。Root
可按用户明确要求直接联系一个 EM/CM。Portfolio 不直接联系 CM。一个 leaf 不是 top-level
participant，不持有 recipient，也不参与本协议。

完整研究链路为 `Portfolio → EM → CM → EM → Portfolio`。纯静态或理论对象可以没有 CM
阶段，但这是 EM 自身方法中的科学判断，不改变相邻 edge。

## 2. Native messages

跨 top-level participant 只使用以下三种可读 Markdown 消息。它们不是本地 envelope 或需要
机器验证的 packet。

```text
[WORK]
Direction: <direction id or shared>
Objective: <bounded outcome in plain language>
Why it matters: <decision or observable this work supports>
Owned paths: <exact paths or none>
Effects: <none or exact external/result effects>
Acceptance: <observable completion checks>
Refs: <current authority, evidence, and exact Git baseline>
Return task: <native task id of requester>
```

```text
[RESULT]
Direction: <direction id or shared>
Summary: <conclusion and direct consequence>
Outcome: <AGENTS-defined top-level outcome>
<only this role's fixed fields from AGENTS.md>
Refs: <durable evidence and Git facts>
Blocker: <required for WAITING or FAILED; otherwise none>
Reentry: <required for WAITING; otherwise none>
```

```text
[CONTROL]
Action: PAUSE | RESUME | CANCEL
Direction: <direction id or shared>
Reason: <why>
Updated at: <timestamp>
```

The conclusion comes before compact fields. A message is a self-contained natural-language task
model; IDs, paths, fields, and commits are factual anchors after meaning and cannot substitute for
role judgment. `Return task` is a native routing locator for this one assignment, not authentication
or a durable message ledger.

用户直接进入某 participant 时，不制造 `Return task`；该 participant 在当前 task 回答用户。

## 3. Dispatch and task creation

Requester 执行下列最小动作：

1. 从 native task list/history 确认目标不存在、空闲，或是唯一的 current-protocol target。
2. 若需要创建 Portfolio/EM/CM，使用保存的 HMASD project 与 Codex 原生
   `environment: worktree`，并显式传入 `AGENTS.md` 的 model/thinking。方向目录不需要另存为
   Desktop project。
3. 新 task 的 initial prompt 本身就是完整 `[WORK]`；不得先建空 task 再重复发送。setup
   client ID 只用于等待，只有 ready thread ID 可以接收后续消息。
4. 复用 current task 时，确认其没有 unfinished inbound WORK，再直接发送一条完整 WORK。
5. 旧 archived task 不复用。若出现两个 current 候选，停止投递并让用户选择；不从本地文件
   重建 target identity。

若 native send 的返回不能证明消息是否进入 recipient history，requester 先读取同一 recipient
history；看到完整消息即视为已投递，确认不存在才允许发送一次。不得因 API 超时、UI 未刷新或
本地未知状态盲目重复 WORK/CONTROL。

每个 target 同时最多持有一个 unfinished inbound WORK，且其 `Return task` 在 terminal 前不变。
一个 successor 必须等当前 WORK terminal 并释放 target 后，才作为新的完整 WORK 投递。

## 4. Liveness and CONTROL

- `WAITING` 仍由同一个 callee 持有，必须给出具体 Reentry。条件满足后继续该 WORK，不发送
  一个伪装成恢复的新 WORK。
- `FAILED` 不自动 retry。需要修复后重做时，由 requester 在旧 WORK terminal 后创建新的
  WORK。新 WORK 本身不是 retry authority。
- 任何 nonterminal Effect 都留在同一个 WORK 并由既有 owner/assignment 继续；观察困难或等待
  超时不结束 WORK、不释放 target。External browser conversation 的完整方法只由显式
  `hmasd-browser-conversation` skill 定义；该 leaf 理解页面与对话阶段，但不解释 owner 内容。
- Ordinary provider-page recovery stays inside the existing browser-conversation assignment. A wait
  bound or tool-local failure predicate does not create a Root/shared repair or a Portfolio
  decision. Only a demonstrated implementation defect outside page-local recovery may later become
  a separately framed shared repair through the normal requester chain.
- Fresh external operation 只允许出现在 `AGENTS.md` 已定义的共享边界内；它不构成 successor
  WORK、retry message 或 lifecycle event。
- `PAUSE` 保留当前 WORK，禁止新的 launch/send。
- `RESUME` 只继续同一个 paused 或 waiting WORK。
- `CANCEL` 只来自用户或用户明确授权的 requester。Callee 停止尚未提交的 Effect；已经提交
  或 commitment unknown 的 Effect 只观察到可说明的安全终态，然后按 `AGENTS.md` 返回
  `CANCELLED`。CONTROL 不携带替代 objective。

Native task 进入 idle、stopped、completed 或 not-loaded 等产品状态，但其 inbound WORK 没有
terminal RESULT 时，requester 恢复或继续该 exact task，并先读取已有 history/artifacts；不得重做
material work 或以新 task 伪造 successor。若 callee 已写完 authority/commit 但尚未返回，只补同一
assignment 的 RESULT；若 RESULT 已在 requester history 中，则 requester 直接消费，不要求第二份。

Native task 能力不可用时，停止受影响动作并报告。不得创建中转协调 task、本地 task plane、
inbox、history parser、registry、receipt 或 scheduler 作为替代。

## 5. Portfolio fan-out and join

Portfolio 可在一个比较性 WORK 下，向多个不同且空闲的 EM 并行投递 direction-specific WORK。
每个 WORK 必须说明共同决策问题、该方向独有 lens、要减少的不确定性和返回的决策影响；第一轮
不能把其他方向的首选结论泄露给该 EM。

Portfolio 必须等待所有已投递 EM 自然 terminal 后，才能向自己的 requester 返回 terminal
RESULT。它不得为了释放 join 自行取消子 WORK，不得为 busy EM 创建替身，也不得把一个方向的
transport failure 解释成该方向 lifecycle 结论。若收到用户的 CANCEL，Portfolio 逐一转达并
等待所有受影响 EM terminal。Fan-out/join 只存在于 native history/status，不写本地 batch、queue
或 task registry。

这个 all-terminal join 是 Portfolio terminal RESULT 的 return barrier, not a refill barrier。
Portfolio 立即消费每个 terminal leg；完成自身投资处置后，它可以在其他 join legs 仍
nonterminal 时向已释放的 exact idle target 投递 successor，或按授权 considered set 选择替代方向。
不得用尚未完成的 join 掩盖未处置 RESULT、未完成筛选或低于授权 advancing capacity 的空槽。

一个 terminal EM RESULT 已结束该 join leg，即使它只报告 technical 或 measurement gap。任何
后续 repair、discriminator 或 observation 都是 Portfolio 比较投资替代方案后主动决定的
successor WORK；下游建议不得自动继承为旧 WORK 的 reentry 或 Portfolio 前置条件。

## 6. Adjacent scientific content

所有相邻 WORK/RESULT 仍使用 §2 的一种形状；以下只是 meaning-complete 内容要求，不是新的字段
schema。

### 6.1 Portfolio ↔ EM

- Portfolio → EM：要支持的投资决定、共同背景、方向独有 lens、decisive uncertainty、预期
  discriminator、资源边界、停止条件，以及必须返回的 decision impact。
- EM → Portfolio：decision impact、claim ceiling、最强 observation、正反证据、仍存替代解释、
  shared dependencies、下一 discriminator、粗粒度成本/时间和 EM recommendation。

### 6.2 EM ↔ CM

- EM → CM：当前 cycle question、竞争解释、不同预测、discriminator、acceptance、explicit
  non-goals、受保护的 scientific/numerical/RNG/checkpoint/Effect semantics、baseline commit、
  config/data/RNG、exact paths、资源与 Effect、运行计划、观察分支、artifacts 和 limitations。
- CM → EM：实际 command/tests、直接 observation、artifact、工程适用范围、失败位置，以及未
  取得 observation 的具体原因。代码、测试或 command 成功不得表述为 scientific acceptance。

负或歧义 scientific observation 在 CM 按工程合同完成时仍可使 CM `Outcome: DONE`。EM 负责其
科学解释，Portfolio 负责其投资解释；任何一方都不得让下游状态代替自己的字段。

若 acceptance、non-goals、受保护语义与直接技术事实不可同时满足，CM 保持 scope 不变，在任何
write/launch 前向 requester 返回 exact conflict；不得自行缩小 acceptance 或改写科学合同。

## 7. Git-visible writer transfer

同一 direction 同时只有一个 Git-visible writer phase：

1. EM 向 CM 交付前提交自身 exact owned paths，记录 exact commit，并停止写入。
2. CM 的 native branch 必须 fast-forward 到该 commit 后才开始工作。
3. CM 只提交其 exact owned paths，返回 known commit/diff，然后停止写入。
4. EM branch fast-forward 到 CM commit 后，writer phase 才回到 EM。

任一步无法 fast-forward 时，当前 participant 停止并向当前 `Return task` 返回 blocker；不得越过
requester 直接联系 Root，不得 cherry-pick、rebase 或重写历史。既有链路 terminal 后，如需
shared repair，由 requester 创建单独的 Root 或 `CM/shared` WORK。

`CM/shared → Root` 使用同样的单 writer、fast-forward 交接：

1. Root 在 dispatch 前冻结并提交 intended target 的 exact baseline、owned paths、acceptance 与
   protected semantics，并停止写这些 shared paths。
2. `CM/shared` 的 native branch fast-forward 到该 baseline 后才开始；它只提交 exact owned paths，
   以 terminal RESULT 返回 reviewed commit/diff，然后停止写入。
3. Root 消费该 exact RESULT 和针对同一 base/diff 的 terminal Reviewer observation。只有 intended
   target 仍可 fast-forward 到该 commit 时，Root 才执行 fast-forward 并恢复 shared-path writer。
4. 无法 fast-forward、review object 改变或 owned-path 外出现修改时，Root 冻结集成并报告冲突；
   不 cherry-pick、rebase、重建 diff、创建替代 CM，或用绿测绕过 exact handoff。

跨 top-level handoff 的 refs 含 Git-visible 内容时必须 commit。同一 saved HMASD repository 内
的 native-worktree 交接只使用本地 exact commit，不需要 push。Push 只在用户要求远端同步、
跨主机交付或正式交付时强制。若 required push 的返回未知，先观察 intended remote ref；确认
目标提交不存在才允许再次 push，不能在未知时重推或宣称已交付。
