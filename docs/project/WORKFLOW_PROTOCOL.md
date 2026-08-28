# HMASD native Codex workflow

Workflow revision: 2026-08-28.5

本文是 HMASD 唯一控制 authority。HMASD 直接信任 Codex Desktop 提供的可见 task ID、
history、status、parent/child relation、create/send/read/wait、同 task 继续、archive 与
worktree。项目不对这些产品事实再做身份认证，也不建立恶意参与者或本地篡改 threat model。

## 1. Topology and roles

长期同级 task 只有 Root、Portfolio、`EM/<direction>` 与 `CM/<direction>`。不使用中转协调
task 或 generation。Task ID 是真实身份，title 只是人类标签；出现两个候选时停止发送并请
用户选择。

- **Root**：永久用户入口；处理 shared-core、用户材料、task 冲突、协议矛盾和最终跨方向
  Git 集成。
- **Portfolio**：维护 considered set、lifecycle、priority、capacity 和跨方向投资判断。
- **EM**：直接冻结问题、创新、原则分析、综合、修订、设置 claim ceiling/discriminator，
  并写方向科研 authority 与 research state。
- **CM**：直接理解代码、实现、测试、普通验证、解释工程证据、写 engineering state 并完成
  Git 收尾。

Long-lived participant 必须是 top-level task。Leaf 是 parent 内的 bounded direct subagent，
不再次 delegate，不持有跨 session recipient ID，只 final return 给 spawning parent。

## 2. Native messages

跨 top-level task 只使用以下可读 Markdown；不生成本地 envelope、body locator、digest、
reply chain 或 validator。

```text
[WORK]
Direction: <id or shared>
Objective: <bounded outcome>
Owned paths: <exact paths or none>
Effects: <none or exact effects>
Acceptance: <observable checks>
Refs: <current authority and evidence>
Return task: <native task id of the requester>
```

```text
[RESULT]
Direction: <id or shared>
Outcome: DONE | WAITING | FAILED | CANCELLED
Summary: <decision or completed outcome>
Refs: <durable refs and Git facts>
Blocker: <required for WAITING/FAILED, otherwise none>
Reentry: <required for WAITING, otherwise none>
```

```text
[CONTROL]
Action: PAUSE | RESUME | CANCEL
Direction: <id or shared>
Reason: <why>
Updated at: <timestamp>
```

`Return task` 只是当前请求的 native routing locator，不是身份认证、reply ledger、receipt 或
durable state。Callee 必须把 RESULT 直接发送回该 task；requester 收到结果后自行决定是否产生
下一条完整 WORK。用户直接进入某 participant 时不制造 Return task；该 participant 直接在当前
task 回答用户。不得把 Summary、Refs 或 Portfolio 表格行交给第三方推断成新任务。

固定正常 edges：Root ↔ Portfolio、Portfolio ↔ EM、EM ↔ CM。Root 也可按用户明确要求直接
联系 EM/CM。CONTROL 直接投递给 affected participant。CM 的 leaves 只回 CM；EM 的 leaves
只回 EM。跨 top-level handoff 由作出该需求判断的 requester 编写并发送完整 WORK。

### 2.1 Role-local scientific content

上述 `[WORK]` / `[RESULT]` 是唯一 transport shape；以下内容只是相邻角色必须写入其中的
领域语义，不是新 envelope、validator 或状态机。

- Portfolio → EM：要支持的组合决定、方向问题、共同背景、该方向独有 lens、decisive
  uncertainty、预期 discriminator、资源边界以及要求返回的决策影响。
- EM → CM：cycle question、竞争解释、各结果分支的不同预测、discriminator、baseline
  commit/config/data/RNG、exact paths、资源/Effect、运行计划以及 observation 要求。
- CM → EM：实际 command/tests、直接 observation、artifact、适用限制、失败位置和未取得
  observation 的原因。代码或测试成功不得表述为 scientific acceptance。
- EM → Portfolio：decision impact、当前 claim ceiling、最强 observation、正反证据、仍存
  替代解释、共享依赖、下一 discriminator、粗粒度成本/时间以及建议的继续、收窄、暂停、
  关闭、融合或派生动作。

负科学结果在 assignment 已按合同完成时使用 `Outcome: DONE`；`FAILED` 只表示该 WORK 没有
完成。上述动作是 RESULT 中的判断文字，不增加 lifecycle 或 RETURN outcome。

## 3. Native dispatch and liveness

每个 top-level requester：

1. 从 native task list/history 确认自身、目标 task 与当前 authority；
2. 复用一个 exact current-protocol target；仅在不存在时创建，出现两个候选时停止并请用户选择；
3. 自己冻结并发送一条完整 bounded WORK，包括 objective、paths、Effects、acceptance、refs 与
   自己的 Return task ID；
4. callee 在同一 task 完成、等待、失败或取消，并把 RESULT 直接返回 requester；
5. requester 解释结果并决定停止、继续同一 callee，或向相邻角色发送一条新的完整 WORK。

每个 top-level target 同时最多持有一个 unfinished inbound WORK。该 WORK 的 Return task 在
终结前不可改变；target 为 ACTIVE、WAITING 或被 PAUSE 时，任何 requester 都不得发送新 WORK。
只有 terminal `DONE | FAILED | CANCELLED` RESULT 释放 target。用户需要替换目标时也先 CANCEL，
待 external commitment 可判定且收到 CANCELLED RESULT 后，再发送一条完整的新 WORK。

`DONE` 只表示当前 WORK 完成，不自动产生 successor。`WAITING` 必须给出具体 Reentry，并仍由
callee 持有；条件满足后由同一 task 继续同一 WORK，不得用新 WORK 恢复。Requester 或用户可以
用 RESUME 唤醒，或在用户要求自动复查时使用 Codex 原生 heartbeat。`FAILED` 不自动 retry。
Stopped/idle 且当前 WORK 尚未完成时继续同一 task，不创建替代者。

Portfolio 可以在一个当前比较性 WORK 内向多个不同、idle 的 direction EM 并行发送
direction-specific WORK。所有已发送 EM 必须 terminal，或由 Portfolio 逐一 CANCEL 并收到
terminal RESULT 后，Portfolio 才能向自己的 Return task 返回 terminal RESULT。忙碌 EM 不得
被覆盖或用替代 task 绕过；其 unavailable/WAITING 事实必须保留在比较结果中。该 fan-out 和
join 由 native task history/status 承担，不写本地 batch、queue 或 task registry。

Participant 可以为完成当前 acceptance 向另一个 idle 相邻角色发送 bounded downstream WORK，
但不得在自己的 inbound WORK 终结前向当前 Return task 反向发送新 WORK。任何由本轮决定产生的
successor 都先返回 terminal RESULT，再确认 target 已释放，最后以独立完整 WORK 发送。

CONTROL 动作只有以下语义：PAUSE 保留当前 WORK 并停止新的 launch/send；RESUME 只继续同一个
PAUSED 或 WAITING WORK；CANCEL 停止新的 Effect，已提交或 commitment unknown 的 Effect 继续
观察到终态，然后写必要的 CANCELLED milestone snapshot、返回 CANCELLED RESULT 并释放 target。
CONTROL 不携带替代 objective；新目标一律使用释放后的完整 WORK。

所有 participant 都不验证身份、不维护 attempt/retry ledger、owner cache、cursor、receipt、
release adoption 或本地路由表，也不常驻轮询。Native list/read/create/send 不可用时停止受影响
动作并报告，不从本地文件或数据库重建 topology。

### 3.1 Complete direction loop

正常完整链路为 `Portfolio → EM → CM → EM → Portfolio`：

1. Portfolio 作出 ACTIVE/投资决定、更新 current table，并直接向 direction EM 发送科研 WORK；
2. EM 在 material cycle 内冻结科学问题与 discriminator；需要可执行观测时直接向同方向 CM
   发送工程 WORK；
3. CM 实现、验证并将 RESULT 返回该 EM，不直接作科研或 Portfolio 判断；
4. EM 解释 observation，必要时以新的 discriminator 继续向 CM 发新 WORK；完成 evidence-grounded
   synthesis 与 adversarial convergence 后将 RESULT 返回 Portfolio；
5. Portfolio 依据 EM 的 durable refs 更新 lifecycle、priority、capacity 或 Direction owner。

每一次箭头的左侧 participant 都是 WORK 内容和投递动作的来源。中间没有 router、隐藏 manager
或从 prose 合成任务的角色。

## 4. Milestone memory

EM 与 CM 各自只维护一个 current snapshot：

- EM：`docs/research/candidates/<direction>/workflow/research/state.json`
- CM：`docs/research/candidates/<direction>/workflow/engineering/state.json`

共同字段为 `direction, role, revision, updated_at, milestone, status, completed_summary, refs,
blockers, reentry_condition, next_action`。EM 另有 `claim_ceiling, next_discriminator,
research_cycle`；CM 另有 `worktree, branch, changed_paths, verification_summary, run`。

EM milestones：`SCOPE_FROZEN`、`SYNTHESIS_READY`、`REVIEW_RESOLVED`、`HANDOFF_READY`。
CM milestones：`SCOPE_FROZEN`、`CANDIDATE_READY`、`REVIEW_RESOLVED`、
`RUN_OR_HANDOFF_READY`。Status：`ACTIVE | WAITING | FAILED | CANCELLED | COMPLETE`。

只有上下文消失会导致重做有实质成本的工作，或可能重新作出不同 material judgment 时，才
跨越 milestone。跨越后立即用 `hmasd_state.py update` 原子覆盖 snapshot；revision 加一并更新
时间。Leaf return、单次测试、普通 lookup、单文件写入或工具成功本身不是 milestone。

恢复顺序：role skill、本文、native WORK/CONTROL history、direction authority、state refs、
owned-path diff、Git facts。State 是最后接受的 milestone；其后的 dirty work 是 in-flight，
必须保留。无法判断修改归属时停止对应 path，不自动 reset、checkout 或删除。

旧 state 不迁移。新协议下首次创建 EM/CM 时由 owner 根据当前 authority 写全新 state；
REGISTERED/CLOSED direction 不预建空 state。

## 5. Manager-direct work and leaves

Manager 默认直接完成本职工作。Leaf 数量由彼此独立的信息缺口决定，不设固定配额；
`max_depth = 1`、`max_threads = 8` 只是技术上限。强顺序依赖、共享可变状态、单一慢操作或
manager 已能可靠完成的工作不为并行而 delegate。

### 5.1 General chore leaf

`hmasd-general-leaf`（Luna xhigh）用于与当前主判断弱耦合、可精确界定的非主线任务，例如
论文/资料下载、文件整理、机械格式转换、fixture 生成、独立清单、低风险杂务或正交检查。
Root、Portfolio、EM、CM 都应主动把这类工作卸载给它，以减轻主 session 的上下文与注意力
压力。Parent 必须给 exact objective、inputs、owned paths、Effects、output shape 和 stop
condition；leaf 不得作 owner judgment、扩大 scope、commit/push、联系 top-level task 或再
delegate。

EM 也可给 general leaf 一个冻结、非权威的正交 lens，例如 competing explanation、falsifier、
measurement boundary 或 unused-evidence question。此类 leaf 必须返回 mechanism、assumptions、
supporting/contradicting evidence、observable prediction、falsifier、next discriminator，或明确
`NO_MATERIAL_INSIGHT`。相同模型、prompt 或来源的一致只算搜索覆盖，不算独立科学证据。

通用 leaf 不替代以下专业边界：

- **CM Scout**（Luna medium，必保留）：非平凡、陌生代码面且当前 milestone 无可信 surface
  map 时先调用；返回 files、symbols、callers、consumers、tests、shared boundaries。
- **Reviewer**（Sol xhigh）：shared-core 或 scientific/numerical/RNG/checkpoint/bit-identity/
  external-Effect 语义改变时强制；普通 direction-local 实现可选。
- **Verifier**（Luna high）：只有 acceptance 依赖 CM 自身测试/静态审查不能充分回答的独立
  runtime/equivalence observation 时使用。
- **Experiment Operator**（Luna low）：只持有一个 exact frozen result-bearing command。
- **Research Scout**（Sol high）：external primary evidence、多来源检索或大范围 evidence
  acquisition；简单下载可交通用 leaf，证据判断仍由 EM 完成。
- **Research Critic**（Sol max）：External Pro 留下 material objection、EM 拒绝其核心建议、
  shared scientific core 或用户明确要求时使用一次。
- **External engineering transport**（Luna medium）：按需一次工程咨询。

## 6. Material research cycle and External Pro

新 direction、mechanism/comparator/discriminator、可能实质提高 claim ceiling 的变化、新结果
推翻核心假设或 Portfolio 要求重估时，EM 开启新的 material cycle。事实补充、措辞修订、
claim 收窄、工程结果录入或同一问题继续不新开 cycle。

每个 material cycle 的顺序：

1. EM 写 `SCOPE_FROZEN`；
2. 完成必要的 neutral grounding；EM、彼此独立的 bounded lenses 和一个 fresh
   `hmasd-explorer-agentify-transport` `Mode: INNOVATOR` 可以从同一 frozen scope 并行探索，
   不向彼此暴露 favored route；
3. EM 比较机制、assumptions、反证与 unused evidence，选择最可能改变判断的最小 discriminator；
4. 需要可执行 observation 时，进行一轮或多轮 `EM → CM → EM`；每轮必须有新的 discriminator，
   不能用重复运行制造进展；
5. EM 解释 observation、竞争解释、limitations 和 claim ceiling，形成 evidence packet 并写
   `SYNTHESIS_READY`；纯理论/静态证据对象可以不调用 CM，但必须说明为何无需或无法取得新的
   executable observation；
6. 启动另一个 fresh `hmasd-explorer-agentify-transport`，以 `Mode: CONVERGENCE` send-once；
   它只接收当前 evidence packet，不接收 Innovator transcript，并作独立 adversarial review；
7. EM 逐项 disposition objection；必要时按既有条件调用 Research Critic，随后写
   `REVIEW_RESOLVED`；
8. EM 写 `HANDOFF_READY`，返回 Portfolio 或发送已冻结的下一条完整 WORK。

每个 cycle 最多一次 Innovator 和一次 Convergence；二者是两个独立的 fresh transport
instances，修订不自动重审。State 的 current
`research_cycle` 只保存 `label, opened_at, reason, pro_innovator, pro_convergence`，两项 status
为 `PENDING | COMPLETE | WAITING | WAIVED`，不保存历史 ledger。

每个 material cycle 的两次 Pro 调用已获自动授权。以下情况必须回用户：非项目公开材料、
secret/个人数据、provider/账号/付费方式变化、超出两次、unknown send 后考虑新发送、用户暂停
外部 Effect。Unknown commitment 只观察不重发；明确未发送失败则 EM 进入 WAITING。用户可以
对 exact cycle 明确 waiver。不得用本地 Critic 或其他 provider 静默替代。

若 observation 或 objection 推翻 frozen scope，EM 结束当前 cycle 并开启新 cycle，不在原
cycle 中重发 Pro。`SCOPE_FROZEN` 同时冻结可能结果及其 claim/Portfolio 含义、共享 baseline、
最大 observation rounds 或资源上限、提前停止条件和 scope-invalidated 条件。没有新的可检验
机制、没有能改变决定的 discriminator、资源边界耗尽或只有重复失败时，EM 必须降低 claim、
返回 `NO_MATERIAL_INSIGHT`/精确 gap，或建议 PARK/CLOSE，而不是无限追加实验。

完整问答保存为：

```text
docs/research/candidates/<direction>/external/
  <date>-<cycle>-pro-innovator.md
  <date>-<cycle>-pro-convergence.md
```

Transport 只负责一次发送、自然完成和完整归档，不解释科研。HMASD 当前流程不注册或调用
其他 research provider fallback。

## 7. Portfolio

`docs/research/portfolio/PORTFOLIO.md` 是唯一 current lifecycle/priority/capacity authority，
固定表格字段为 Direction、Lifecycle、Priority、Direction owner、Updated at、Reason/condition。
Lifecycle 只允许 `REGISTERED | ACTIVE | PARKED | CLOSED`，且只有 Portfolio 可以改变。

`Direction owner` 是稳定的 Portfolio 责任投影，不是每一次 task send 的日志。ACTIVE direction
由 `PORTFOLIO` 或 `EM` 持有；短暂 CM slice 不改变该字段。REGISTERED、PARKED、CLOSED 使用
`NONE`。Portfolio 先原子更新该表，再直接发送必要的 EM WORK 或向当前 Return task 返回 RESULT。
重大投资或关闭决定可写独立 Markdown decision note；普通 priority 更新只改表。历史 decision
note 必须清楚标为 historical，不能作为 current workflow state。

Portfolio 先判断最低科学质量：问题与非目标清楚、evidence 可追溯、存在可解释的
discriminator、负结果能区分理论与执行失败、claim 不超过证据。通过后再定性比较：方向间的
互补/替代/信息相关、共享假设与共同失败风险、下一 observation 是否会改变组合动作、成本/
时间/可逆性以及长期 option value。没有明确概率、效用和成本模型时不得生成数值 VOI、综合
分数、Elo 或投票裁决。

继续、收窄、暂停、关闭、融合或派生是一次性 Portfolio action，不新增 lifecycle。融合先形成
新的科学 synthesis question，并明确源方向继续/PARK/CLOSE；代码或 shared-core 集成仍由 Root
处理。派生先在 Portfolio 登记新 direction，再由新的 EM 建立 direction science。

## 8. Scientific capabilities and evidence

`configs/scientific-capabilities-v1.toml` 只记录 capability、`active | unavailable`、purpose、
entrypoint、environment、allowed Effects。`hmasd_science_capabilities.py` 只提供
`list/show/doctor`，不运行科研 workload、不安装、不路由也不改变 state。`doctor` 唯一允许的
process observation 是对 catalog 中 active interpreter 执行无副作用的 `--version` 探针。

确定性本地工具由 EM/CM 直接调用。只有观测实际改变或限制 claim/engineering judgment 时，
manager 才写 `docs/research/candidates/<direction>/evidence/<descriptive-name>.md`，包括 Question、
Observed at、Inputs、Tool/command、Observation、Limitations、Judgment impact、Result paths。
Raw output 留在 direction temp。工具成功没有 scientific acceptance、routing 或 lifecycle
语义。

## 9. Operator, run, and Effects

Operator assignment 冻结 argv、cwd、output root 与 stop condition；一个 Operator 只 launch
一次并观察到 terminal。Terminal witness 使用简单 JSON 保存 run ID、manifest/stdout/stderr
paths、status、exit code 和 observed time。它不绑定 session 身份。

该本地 witness 有意不为这些 paths 再建立内容认证：Codex 内部单用户流程不假设本地恶意
篡改。需要重现性或 byte identity 的事实继续由 run manifest、checkpoint/result 格式和其
科学 checksum 负责；不得把它们复制成第二套 Operator/session 认证手续。

实验 run layer 继续独占 prepare/resource admission、memory safety、exact argv/cwd、process、
checkpoint/result/stdout/stderr 与 terminal facts。科学 reproducibility 或 byte identity 所需
的 checksum 可以保留，但不能扩散为 task/session identity。

外部 transport 由 parent 冻结 provider、question、archive path 与 send-once。一个 operation
至多发送一次；commitment 未知时只 observe，不盲目重发。

## 10. Git closure and control

`C:/Projects/HMASD` 是 Root 的 primary `main` checkout，不在其中 switch/checkout。只有 ACTIVE
direction 按需拥有至多一个 sibling Git worktree，位于 `C:/Projects/HMASD-worktrees/<name>`，
并由用户或 Root 一次性保存为 Codex Desktop local project。EM 与 CM 都在该 saved project 中
以 local environment 创建 top-level task；不得用 per-chat managed worktree 假装共享方向目录，
也不得建立 project/worktree mapping registry。缺少 saved project 时显式 WAITING。

新建 top-level participant 时，`create_thread` 的 initial prompt 本身就是完整 `[WORK]`；不得
先创建空 task 再二次发送。Setup 只返回 client ID 时等待 ready thread ID，不得重建或把 client
ID 当 recipient。旧 archived tasks 不复用。

同一 direction worktree 同时只有一个 Git-visible writer phase。EM 向 CM 发送 WORK 前提交自身
owned refs；CM terminal RESULT 前 EM 对整个 direction worktree 只读且不得 stage/commit；CM
只提交 exact owned paths并返回 known diff，随后 writer phase 回到 EM。Leaf 不 commit/push，
也不创建 worker worktree。不同 direction worktrees 可以并行；每个新 cycle 以 WORK 指定的
exact committed direction-worktree baseline/HEAD 为起点，无法安全同步或涉及 shared-core 时交 Root。

Owner 只修改/stage owned paths并保留其他修改。跨 top-level role handoff 且 refs 有 Git-visible
内容时必须 commit；push 在用户要求远端同步、跨 worktree 集成或正式方向交付时强制。

用户直接控制 participant 时，该输入已经是 authority，不需要 CONTROL 转发。Root 或 requester
需要影响另一 task 时，直接向 affected participant 发送 CONTROL，并遵守第 3 节对应动作语义。
PAUSE/CANCEL 不等于 Portfolio lifecycle 变化。

不兼容任何旧控制层。旧 task、messages、state、scripts、schemas、prompts 或 fixtures 不读取、
不迁移、不翻译；问题一律 fix-forward。
