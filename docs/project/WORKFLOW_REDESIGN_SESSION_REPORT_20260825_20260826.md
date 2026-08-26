# HMASD 并发工作流重设计完整会话报告

> 时间范围：2026-08-25 至 2026-08-26  
> 读者：后续接手本项目的 Codex task、其他模型、设计审阅者和维护者  
> 文档性质：历史、决策演化与交接报告；**不是 Durable Authority，也不是新的工作流规范**  
> 当前规则入口：`AGENTS.md`、匹配的 project skill、`docs/project/WORKFLOW_PROTOCOL.md` 以及各领域现有 authority

## 0. 如何阅读本报告

这轮会话经历了多次主动修正。某个方案曾经被用户接受，不代表它现在仍然有效。后续模型必须区分四种状态：

- **当前有效**：已经进入当前 `AGENTS.md`、协议、skill 或程序合同；
- **本地已实现但 live proof 未完成**：代码或测试已存在，但尚不能宣称真实无人值守链路已经证明；
- **探索性建议**：用于暴露问题，没有成为当前规则；
- **已撤回或 superseded**：即使在早期 grilling 中得到过同意，也不得重新执行。

本报告解释“为什么形成当前设计”。执行时不要从本报告恢复旧状态词、旧 Q 编号或旧控制面。若本报告与当前 `AGENTS.md`、project skill 或协议实现冲突，以后者为准。

## 1. 执行摘要

这次会话最重要的发现是：HMASD 表面上在设计“多个 LLM session 的协作流程”，实际上是在设计一个具有并发、故障恢复、外部副作用和多写者约束的小型分布式系统。

最初的直觉是给每个 session 更多背景、职责说明、权限规则、handoff 文档和恢复手续，让它们自行协调。实际结果相反：每个模型只看到局部上下文，为了降低自己的不确定性，会独立增加 approval、状态、claim、review、交接和恢复层。每一层局部看似合理，组合后形成了手续爆炸、语义漂移、串行往返和潜在逻辑死锁。

这暴露出一个通用结论：

> LLM 的灵活性适合切面内部的科学与工程判断；跨 session 边界若仍依赖自由解释，灵活性就会变成全局不确定性。

因此设计从“让所有模型理解完整控制面”转向：

> 协议集中、执行分散；切面内部允许智能，切面边界拒绝自由解释。

当前方向是让程序负责身份、消息形状、引用新鲜度、幂等、Effect 观察、资源冲突和原子动作；让 LLM 只负责被分配的科学、工程或真实异常判断。Workflow-Clerk 从预想中的活跃协调者退回为默认停驻、只处理程序精确报告的异常文书角色。

## 2. 必须先理解的 Codex 上下文

### 2.1 Project、top-level task 与 subagent 不是同一种东西

Codex/ChatGPT 的 project 用来共享文件、项目说明和相关来源；不同 chat/task 仍保留各自 transcript。官方文档也建议把不同 outcome 放在独立 chat 中，并把持久项目说明放入 `AGENTS.md` 或受版本控制的文档。[Projects and chats](https://learn.chatgpt.com/codex/projects)

HMASD 据此区分：

- **Top-level Task**：用户可直接进入、可独立停驻和恢复的长期身份；Root、Workflow-Clerk、Portfolio、EM、CM 属于这一层。
- **Subagent**：由某个 task 为一个有界切面临时派出的 agent thread；适合只读探索、测试、审阅和正交实现，不承担长期领域身份。
- **Leaf**：项目把 direct subagent 限制为一层；leaf 不再派生下一层 agent。

官方文档说明 subagent 可以并行执行并把结果汇总到主线程，也特别提醒并行写入会增加冲突和协调成本。[Subagents](https://learn.chatgpt.com/codex/agent-configuration/subagents) 这正是本项目要求 assignment 路径正交、worktree 隔离和 Root 只汇总结果的产品背景。

### 2.2 同一项目文件共享，不等于上下文共享

各 task 可以看到同一工作区，但不会天然拥有其他 task 的完整推理上下文。对话压缩还会进一步丢失长程细节。这轮会话中已经真实出现：压缩后模型忘记 `grilling`/skill 的操作原则，用户因此要求把相关 skill 安装到项目级，避免只靠某次会话记忆。

所以：

- transcript 是 provenance，不是跨 task authority；
- 文件共享不解决语义漂移；
- 摘要不能代替当前 authority；
- 新 task 必须通过稳定入口、精确 Work Packet 和被点名的 authority refs 恢复。

### 2.3 `AGENTS.md` 与 skill 的作用边界

Codex 在开始任务时读取适用的 `AGENTS.md` 指令链；离当前目录更近的项目说明会覆盖更上层说明。[AGENTS.md](https://learn.chatgpt.com/codex/agent-configuration/agents-md) 但 `AGENTS.md` 仍然是给模型的行为约束，不是原子写入器、去重器或 Effect ledger。

Skills 使用渐进披露：模型先看到名称与描述，真正使用时才加载完整 `SKILL.md`；skill 还可以携带脚本和 references。[Build skills](https://learn.chatgpt.com/codex/build-skills) 这启发了 HMASD 的操作手册设计，但也带来一项限制：如果关键正确性只写在 skill prose 中，多个模型仍可能重新解释它。

因此当前原则是：

- `AGENTS.md` 写任务平面、硬边界和禁止事项；
- skill 写一个角色面对一个精确输入时的短操作路径；
- schema/CLI 实现机械语义；
- Durable Authority 保存材料事实和决定；
- 不能让 skill 复制一套平行工作流。

### 2.4 Codex App Server 与 native adapter

Codex App Server 是 Codex 自身用于 rich client 的公开 JSON-RPC 接口，不是 ChatKit thread，也不是已弃用的 Assistants thread。官方接口覆盖连接初始化、`thread/start`、`thread/resume`、`thread/list`、`thread/read`、`turn/start` 和 streamed completion 等能力；默认可使用 stdio JSONL。[Codex App Server](https://learn.chatgpt.com/docs/app-server)

这使“native task adapter”在技术上可实现。但产品接口存在版本和历史模式兼容边界。本轮本机观察到：无模型 `initialize/list` 可以工作；桌面已有 task 使用 paginated history 时，完整 read/resume 可能 fail closed；一次 ephemeral fork conformance 尝试又因参数兼容在启动模型 turn 前被拒绝。因此本地 adapter 代码存在，不等于旧 task 和真实回合已经全部 live-proven。

## 3. 会话起点：用户提出的八类问题

会话从八个彼此相关的担忧开始：

1. **串行链路的无缝传递**：EM 做完科学设计后不能因为没有代码权限就停止；CM 做完代码也不能因缺少科学权限而停止。角色边界应决定交给谁，不应成为终止理由。
2. **多方向文件与 Git 正交**：方向应拥有自己的文件、目录和 Git 工作面，避免 Root 变成所有方向共同的提交现场。
3. **跨 session dispatch 防漂移**：同一上下文中有意义的简称、代词或 `blocked`，跨 session 后可能失去作用域和因果含义。
4. **缺少并发系统经验**：用户明确指出自己缺少高并发工作流设计经验，难以识别可用性、安全性与手续复杂度之间的边界，希望借鉴成熟开源项目的设计哲学。
5. **可视化与可控化**：用户既要了解系统发生了什么，也要拥有最高控制权；但权限机制不能把用户挡在流程外。
6. **目录与抽象管理**：项目快速膨胀时必须同时对人类和无固定记忆的 LLM 可读。
7. **代码轻重分级**：C++ backend、网络基座和公共算法等 shared core 与方向私有实现不能采用相同修改政策。
8. **Matt skills 的定位**：可以借鉴其 grilling、spec、handoff、TDD 和 review 思想，但 HMASD 是研究加代码、异步并行和分级 Effect 项目，不能强行套用线性软件开发流程。

用户随后不断修正模型的抽象冲动：MARL toy env 的 float64/逐路径确认/三天耗时只是一种失败案例，不得在缺少上下文时上升为全项目规则；开源项目调查的目标也不是引入组件，而是理解它们如何控制并发复杂度。

## 4. 完整决策演化

### 4.1 第一阶段：用 grilling 暴露根问题

最初 Q1–Q7 冻结了几个方向：

- “无缝”首先指逻辑可恢复，而不是保证某个模型进程永远在线；
- `direction-id + generation` 被考虑为并发隔离单元；
- EM→CM→实验→EM 在已有明确 authority 时应自动传递；
- 用户拥有最高权限，agent 可以警告和记录，但不能反复审批形成逻辑死锁；
- Matt 只作为模式来源；
- 应先有一个单方向黄金路径，再扩大并发。

早期还提出了“文件/CAS + SQLite 投影 + 本地 supervisor”、DBOS/Prefect POC 等候选。这些是当时为了无人值守和可视化提出的探索性方案，**后来因缺乏真实失败证据和控制面膨胀风险被撤回**。

### 4.2 第二阶段：从裸 `BLOCKED` 认识故障作用域

用户进一步要求无人值守时能够区分项目、方向、部分功能和 Effect 故障，尝试有界修复后才等待用户，同时不能让一个 session 的 `BLOCKED` 传播成其他 session 的退出信号。

审计发现，当时危险的不是 Python 已经实现了全局关闭，而是通用 result/skill 允许模型自由解释 `BLOCKED`。由此形成的长期原则是：

- 故障来源与影响范围分开；
- 项目、方向、feature、Effect 必须显式限定；
- `UNKNOWN` external Effect 只观察、不重发；
- 无关方向和无依赖动作继续；
- 不用一个裸状态词代表 agent、方向和项目三个层次。

这个阶段曾进一步构想 incident schema、监督层级、route registry 和重试预算。后来审阅认为这些会形成第二控制面。当前只保留“作用域明确、Effect 专用恢复、失败不跨域扩散”的不变量，不保留通用 Incident FSM 或全局 recovery engine。

### 4.3 第三阶段：Root、长期 task 与 leaf 的重新定位

用户明确要求 Root 是最高能力入口，可以使用所有真实 leaf 能力和角色文档，因为 Root 最常与用户交流，必须具有最高灵活性。与此同时，在 dispatch 尚未落实前不应急于恢复旧 EM/CM session，避免跨 session 漂移。

因此一度把所有旧 EM/CM session 退休，只保留 Root 作为迁移起点。后续冻结的最终拓扑不是“永远只有 Root”，而是：

- Root 永久存在并拥有最高 operational capability；
- Portfolio、EM、CM 是按需创建的独立 top-level tasks，一旦创建可以 idle/parked 并独立恢复；
- Root 可以在用户已授权时直接形成材料结论，但必须写入正确既有 authority，并记录真实 decision owner；
- task 创建关系不产生权限继承；
- Root 能用全部 genuine leaves，其他 top-level task 使用与其切面匹配的 leaf 菜单；
- leaf 只做有界切面，不承担跨 session 路由。

这里关键地区分了：权限、决策责任、durable writer 和 runtime actor。早期的 `acting_as` 生命周期、角色 lease、session incarnation 等扩展后来被删除；当前不再为“谁可以做什么”建立额外权限状态机。

### 4.4 第四阶段：MARL 代码收集与项目可读性

用户要求先收集代码而不是立即做经验分析，并指定多个 Luna xhigh native child、`fork_turns=1`。最终在 `C:/Projects/HMASD-oss-landscape` 收集了 121 个浅克隆且 clean 的官方/作者仓库，其中包括 InstSci 对应实现、MARL、RL、DL、环境/benchmark 和 model-based 算法仓库。

这一产物是后续证据库，不是当前工作流 authority，也没有直接把某个库的默认精度、目录或算法风格提升为 HMASD 规则。

同时确认项目需要面向人和 LLM 的渐进式文档：根入口、项目 map、研究 map、方向 authority、代码和历史逐层下钻。但经过简化审阅，v1 没有立即增加手工维护的 `llms.txt`、Code Index 或文档 registry。理由是：它们只有在冷启动检索测试证明现有入口不足时才有价值，并且最好从现有文档/源码生成，而不是成为新的真相来源。

### 4.5 第五阶段：长轮 grilling 本身演化成复杂度样本

Q50–Q107 一度提出了大量机制：

- 四文件 handoff；
- `STAGING → READY → CLAIMED → RESULT_WRITTEN → INTAKEN`；
- 全部方向预建 EM/CM；
- `session_incarnation`；
- scope-local directive 文件；
- Root 唯一 directive writer；
- incident 字段与生命周期；
- recovery route catalog 与三次预算；
- Dashboard 写控制与命令状态；
- 三级代码分类；
- `omp/` 分支迁移为 `codex/`；
- 根 `llms.txt` 行数上限、Code Index 和 current-search CLI。

这些建议中很多曾被用户逐项接受，因为单独看都能解释一个风险。但用户随后再次指出“复杂性又开始叠加”，并要求用开源项目原则审阅此前全部决策。

这成为整个会话的第一个元级失败证据：

> 即使目标是防止 LLM 过度设计，长轮逐项 grilling 仍可能把每个局部担忧固化成一个新实体；逐项接受不等于组合后的系统仍然简单。

### 4.6 第六阶段：全量减法审阅

独立审阅把此前决定分为 keep、merge、defer、delete，并指出开源项目只能支持 reconcile、局部故障、Effect 幂等、机械合并和渐进读取等原则，不能证明 HMASD 需要具体的五阶段 handoff、全方向 task、固定数字预算或多个平行 authority。

由此撤回了大量机制：

- 不预建所有方向的 EM/CM，改为懒创建；
- 不新增 session incarnation，runtime handles 可重建；
- 不迁移 `omp/` 分支 namespace；
- 不建独立 directive/outbox/incident 数据模型；
- 不建 SQLite、daemon、全局 frontier engine 或 route registry；
- Dashboard v1 保持只读；
- 代码分类从三级恢复为 `shared-core / direction-owned` 两级；
- handoff 压缩为一个 immutable Work Packet；
- Work Packet 只属于 ignored runtime transport，不成为 durable workflow state；
- 当前 authority、CAS、run/worktree/external manifests 继续作为事实来源。

Q108–Q135 的最终简化基线可以概括为当时的四个概念：Existing Authority、Work Packet、Effect、一次有界的 `reconcile --once`。这轮确认后才进入实际实现。

### 4.7 第七阶段：初版 v1 与真实 UCOPE 压力测试

用户询问“v1 是否实现完毕”时，模型明确回答尚未实现；随后用精确 base、路径和 action digest 取得 shared-core 实施确认，再开始修改。

初版机械面落地后，UCOPE 现实方向被用于压力测试。它暴露了一个极有价值的失败模式：同一 current bytes 围绕 S2 构造、独立 review、repair、SANCheck、技术验收、Portfolio 和 Root Git freeze 产生约十四次串行交接和大量重复 ref 绑定。

真实缺陷、单一 owner、Effect 幂等和 worktree 隔离本身是合理的；错误在于把同一 CM scope 内的实现、review、repair、SANCheck 和验证拆成多个 EM↔CM 往返，并在 Root Git 之前又引入 freeze packet 与 action packet 两层元授权。

由此形成的重要修正是：

> 只有责任所有者、材料 authority 或外部 Effect 真正改变时才跨 session；同一 frozen scope 内的普通实现、review、repair、测试和验证应保持为一个可恢复 slice。

这也是为什么当前 skill 明确“一次 CM assignment 覆盖普通 review、同范围 repair、测试、verification/SANCheck 和终态工程返回”。

### 4.8 第八阶段：把开源 insight 写成非权威哲学 spec

用户要求建立防偏移的哲学 spec，并把开源项目实际方案作为范例记录。于是形成 `WORKFLOW_DESIGN_PHILOSOPHY.md`，同时强调：

- 它是 rationale，不是 authority、schema、gate 或 backlog；
- pattern card 不自动产生 adoption；
- 引用项目是设计样例，不是 HMASD 依赖；
- 每个上游 pattern 都必须写清“借什么”和“不借什么”。

这一阶段重点参考了 Kubernetes、Temporal、Zuul、Ray、Dagster 和 OpenHands，并把“新机制必须由可检验需要证明”写成反 cargo-cult 原则。

### 4.9 第九阶段：从 active Clerk 设想到 exception-only Clerk

即使哲学 spec 已经写明“保持简单”，用户观察到多个控制者在上下文不足时仍会自行增加控制层，于是提出专门的 Workflow-Clerk：让普通 session 只完成单个切面，把复杂协调交给一个 Luna xhigh、拥有完整拓扑和操作手册的文书管理员。

这个想法很快暴露出第二个元级失败证据：Clerk 首次 bootstrap 就把“不能作材料决定”误读为“不能选择 runtime target”。这证明：

- 一个更聪明、更了解全局的 LLM 并不能消除自由解释；
- 把多模型不确定性集中到一个 LLM，只是把随机性换了位置；
- 仅靠文档说明权限和职责仍不稳定；
- 正常路径必须在没有 LLM Clerk 的情况下也能运行。

于是 Clerk 的职责被大幅收缩：

- 默认 parked；
- 只接程序已经精确分类的 missing field/ref、legacy-unroutable 或有限协议缺陷；
- 不扫描拓扑，不推断 owner，不 publish/dispatch/create/wait/retry，不持有 Effect，不成为 approval gate；
- identity conflict 回 Root，材料决定回 domain owner/user，`UNKNOWN` Effect 走程序 observe-only，Root override 不经过 Clerk。

### 4.10 第十阶段：确定性协议内核 Stage A–C

Clerk 收缩后，工作转为“协议内核 + 程序化 reconciler”。实现采用 TDD，先制造反例再收敛。

**Stage A：exact-key planner**

- 命令必须显式提供一个 `work_id`；
- 删除全局 ready 扫描、fair cursor、线程池、capacity scheduler 和 generic handler；
- 无关 packet 即使损坏也不能影响当前 work；
- 相同输入必须得到字节一致结果；
- planner 不执行 task、Git 或外部 Effect。

Stage A 先形成 40 个通过测试。

**Stage B：typed result 与 next packet**

- `assignment_id == work_id`；
- logical identity、generation 和 changed paths 必须与 receiver/owned paths 一致；
- follow-on 必须先构建完整 canonical draft；
- `REQUEST_*` result 只通过 `next_action.input_refs=[draft.work_id]` 绑定它；
- 未发布 draft 只能产生 `PUBLISH_PACKET_INTENT`，不能假称已可 dispatch。

Stage A+B focused suites 达到 92 tests。

**Stage C：独立审阅后的确定性补洞**

反例包括：一个 result 绑定两个 draft、自环 packet、Portfolio 到具体方向的合法转换、structured ref freshness、payload changed paths、status/action 一致性和显式 task snapshot。Stage C 完成后，四个 focused suites 为 112 passed，recovery matrix 为 8 passed，skill 和静态检查通过。

Stage A–C 的关键成果不是“更多状态”，而是删除模型可以自由发挥的入口。

### 4.11 第十一阶段：闭合剩余缺口与 Stage D

用户要求“闭合缺口”后，剩余问题被重新审阅并收敛为少量程序原语：

- exact `work_id` 的 immutable return witness；
- typed Effect/ref，并复用 run、worktree、external operation 的现有 domain validator/observer；
- explicit resource comparator；
- Codex App Server native adapter。

这里做了一个重要的证据驱动回补：简化阶段曾反对独立 `result.json` 和 completion ledger，但 lost-return 反例证明，receiver 在完成工作后、返回消息前崩溃时，没有一个 `work_id` 键控的不可变结果事实就无法机械恢复。因此当前允许“每个 work_id 至多一个 immutable return witness”。它不是可变 ack、claim 或 completion ledger，也不引入生命周期；它只保存 owner result/domain refs，用于重复接收和丢失返回恢复。

同样，`done_criteria` 没有被扩展成通用 DSL。内核只能证明 owner 发布了与 `work_id` 绑定且 refs 新鲜的 typed return；科学或工程语义仍由相应领域证据合同判断。

Stage D 期间又通过 fresh-session 和独立审阅发现：

- 普通 packet 不能把 parked Clerk 当 receiver；
- active runtime row 不能把原生已 idle task 永久算作占用；
- EM 不能携带 shared-core 路径绕过确认；
- 任意 Markdown 不能伪装 shared-core authority；
- comparator 需要覆盖 write↔frozen-ref 相交和 Windows 大小写别名；
- native send/create outcome unknown 仍必须 observe-only。

截至本报告快照，Stage D 的本地模块和测试文件已经出现，当前 `AGENTS.md`/协议把本地合同描述为已闭合，但 live proof 仍分层 pending。由于主 Root 仍在进行独立审阅和兼容修复，本报告不把 Stage D 写成最终无人值守 GREEN。

## 5. 这次真正遇到的系统性困境

### 5.1 局部理性导致全局复杂度

每个 session 为了让自己的步骤“更安全”，会增加一个看似合理的检查或状态。其他 session 不知道它的因果背景，只看到新制度，又在外面包一层保护。复杂度由多个局部补丁乘法增长，而不是由一个人有意设计出来。

### 5.2 文档原则无法约束原子行为

“保持简单”“Root 权限最高”“不要过度审批”都太抽象。模型在缺少上下文时仍会自行解释。只有职责、输入、输出、原子命令和失败返回都明确时，模型才不容易扩展制度。

### 5.3 多方共同持有约定会产生解释分叉

让 Root、Portfolio、EM、CM、Clerk 和 leaves 都持有完整流程说明，看似提高一致性，实际让每个角色都成为临时流程设计者。正确方向是让它们只持有单切面接口，跨切面复杂度由统一协议承载。

### 5.4 灵活性与确定性的边界放错了

LLM 应在科学判断、工程权衡和真实异常处灵活；路径规范、去重、Effect identity、引用新鲜度、消息发布和状态比较必须确定。如果机械层也依赖 LLM，恢复时无法区分事实与解释。

### 5.5 “为了恢复而记录一切”会制造第二真相

早期 directive、handoff、incident、checkpoint、Dashboard command 等设计都试图提高可恢复性，但它们与已有 research/engineering/run/worktree authority 平行后，会产生写者冲突和同步问题。最终恢复原则是尽量从既有 authority、typed Effect 和不可变 packet/return 重建，而不是复制整个流程状态。

## 6. 开源项目提供了什么方向

这些项目被用来学习设计哲学，不是要求采用其组件或术语。

| 项目/方向 | 观察到的方案 | HMASD 借鉴 | 明确不照搬 |
| --- | --- | --- | --- |
| Kubernetes | controller 按 key 重读 spec/observed state 并 reconcile | exact work、fresh observation、一次有界推进 | API Server、常驻集群、完整 Condition 词汇 |
| Temporal | Workflow 与 Activity/Effect 分离，历史与幂等支持恢复 | typed command、Effect identity、UNKNOWN 只观察 | 第二套 event-sourcing workflow engine |
| Zuul | 独立变更并行，真正相关时才组合验证 | worktree/branch 正交、冲突才串行 | 默认建设完整 merge queue |
| Ray | 粗粒度任务、资源准入、pending backpressure、故障容错 | 不把微步骤拆成 agent；批量与资源是真并发边界 | Ray runtime 作为控制面 |
| Erlang/OTP | supervision tree 和 one-for-one 局部故障 | 故障有范围，不自动全局升级 | 用 supervisor 代替 durable workflow |
| Dagster | durable assets 与可下钻观察 UI | Dashboard 是只读投影、从摘要下钻事实 | 复制 asset/orchestration 状态模型 |
| OpenHands | event persistence、恢复与 condensation view | 会话可丢失；摘要是视图，不是 authority | 复刻其完整 conversation event system |
| mini-SWE-agent | 主动删除专用工具和重复状态层 | 最小接口优先，复杂度必须证明净收益 | 把软件修复 agent 当研究控制面 |
| MCP / `llms.txt` | 结构化资源和渐进暴露 | 项目地图、按需取用、机器友好入口 | 手工维护的新文档 registry 或 authority |
| Matt skills | grilling、domain language、spec、TDD、handoff | 将已知工作方法写成可触发 skill，配脚本和 references | 线性 feature→ticket→implementation 总控流程 |

这些项目的共同点不是“拥有一个理解全局的智能协调者”，而是：稳定 ID、窄协议、可观察事实、幂等/Effect 边界、局部故障和少量原子转移。它们在没有 LLM 时也能运行，这正是当前协议主路径的目标。

## 7. 当前有效的设计决策

### 7.1 权限与责任

- 用户拥有最高决策权；危险行为应明确警告和记录，但不能形成重复审批死锁。
- Root 是永久最高能力 orchestrator，可调用全部 genuine leaves。
- 角色表示责任，不是 permission gate。
- Root 在用户已授权时可以形成 Portfolio、科学或工程结论，但必须写入正确既有 authority，并记录真实 decision owner。
- 普通 reversible 工作不因 review、Dashboard、hash、Clerk 或 task lineage 获得或失去权限。

### 7.2 Task 平面

- Root、Workflow-Clerk、Portfolio、EM、CM 是 top-level tasks，不从 `.codex/agents` spawn。
- Portfolio/EM/CM 按需懒创建；一旦存在可 idle/parked 和恢复。
- 每个 direct subagent 是 leaf；并行用于独立、正交切面。
- 用户可直接与任一 top-level task 互动；材料决定仍要落入 durable authority。

### 7.3 正常跨 session 协议

- 输入是一个 exact、validated、runtime-only Work Packet；
- `work_id` 来自 canonical 内容；
- receiver 先查 exact return witness；
- result 必须 `assignment_id=work_id` 并绑定 receiver identity/generation；
- follow-on 先 canonical build 完整 draft，再由 `input_refs=[draft.work_id]` 唯一绑定；
- planner 每次只处理一个 `work_id` 和显式 fresh task snapshot；
- 普通路径零 Clerk；
- 不从自然语言选择 route，不从 opaque string 猜路径。

### 7.4 故障与恢复

- failure scope 必须是 project、direction、feature 或 Effect；
- 禁止跨 task 传播裸 `BLOCKED`；
- `UNKNOWN` external commitment 只观察，不重发；
- 一个 result-bearing command 由一个 Experiment Operator 从启动持有到终态；
- lost return 从 immutable return witness 恢复；
- terminal packet 无 return 时只恢复相同 work/target，不能创造新工作或新 Effect；
- 无关方向和无依赖工作继续。

### 7.5 文件、代码和 Git

- 方向工作使用 assignment-owned paths、独立 worktree 和分支；
- 方向可自治修改、测试、commit，并在精确 assignment 授权时 push；
- shared-core 修改需要一次与 exact base、路径、objective/non-goals 和 allowed Git effects 绑定的用户确认；
- path policy 只分类，不授予权限；
- Root 机械集成验证后的 candidate，不手工解决冲突，不使用 `git add -A`；
- native Windows Git/Python 与 Windows worktree 保持一致，不混用 WSL Git。

### 7.6 可视化与文档

- Dashboard v1 只读；它展示派生事实，不成为 authority 或写控制面；
- 当前文档按 `AGENTS.md → project map/context → protocol/skill → direction authority → code/evidence` 渐进读取；
- `CONTEXT.md` 只保存稳定术语，不保存实现细节；
- `WORKFLOW_DESIGN_PHILOSOPHY.md` 只解释 rationale；
- 不因“模型可能需要”就预建 `llms.txt`、Code Index、SQLite 或文档 registry。

## 8. 已撤回方案：后续模型不得复活

| 已撤回方案 | 撤回原因 | 当前替代 |
| --- | --- | --- |
| 常驻 LLM supervisor / active Clerk | 把解释随机性集中到另一个模型 | 确定性协议主路径；Clerk exception-only |
| SQLite 第二控制面 | 与现有 authority 漂移，尚无失败证据 | 文件/CAS、runtime packet、typed Effect observation |
| 全局 ready scan、fair cursor、thread pool | 形成隐藏 scheduler，读取无关 work | exact `work_id` 的 `reconcile --once` |
| generic handler / generic Effect executor | 模糊原子 Effect 的因果语义 | 每种 Effect 复用现有 domain CLI/observer |
| 四文件/五阶段 handoff FSM | claim、intake、ack 等状态膨胀 | immutable packet + 必要的 immutable return witness |
| completion ledger / ack queue / lease | 第二生命周期和恢复歧义 | content identity、return witness、native history observation |
| 通用 Incident FSM 和 recovery route registry | 把局部失败固化为全局控制模型 | scoped facts + domain-specific recovery |
| 全方向预建约 66 个 EM/CM | 大量无工作 task 和管理噪音 | 按需创建，创建后可 parked |
| `session_incarnation` 新语义层 | runtime handle 已可替换 | logical identity + generation + observed handles |
| 独立 directive/outbox authority | 与现有 Portfolio/EM/CM authority 竞争 | 用户决定写入所属既有 authority |
| Root 唯一 directive writer | Root 瓶颈并混淆 writer/actor | domain writer 保持，Root 可记录用户授权决定 |
| 三级代码分类 `protected/shared-extension/private` | 升级逻辑过重、边界不稳定 | `shared-core / direction-owned` 两级 |
| `omp/` 分支重命名为 `codex/` | 大量改动无功能收益 | 保留现有 namespace |
| Dashboard v1 写控制和命令状态机 | 后端 typed CLI 尚未证明需要，形成第三控制面 | 只读 Dashboard + task/CLI 交互 |
| 固定行数的手写根 `llms.txt`、全量 Code Index | 无证据数字和维护漂移 | 先修已有 maps；需要时生成 |
| 把 `done_criteria` 解释为通用 DSL | 通用内核不能判定科学/工程语义 | hash-bound 描述 + domain typed evidence |
| 每个 review/repair/SANCheck 都跨 session | 同 scope 往返爆炸 | 一个 CM slice 内连续完成普通工程闭环 |
| freeze packet 后再发 action packet | 元授权重复 | 一次 exact shared-core/Git action binding |

## 9. 当前代码与文档落点

核心入口包括：

- `AGENTS.md`：当前任务平面与硬边界；
- `CONTEXT.md`：稳定领域术语；
- `docs/project/WORKFLOW_PROTOCOL.md`：当前协议；
- `docs/project/WORKFLOW_DESIGN_PHILOSOPHY.md`：开源 pattern 与设计 rationale；
- `docs/migration/CODEX_MIGRATION_RECOMMENDATION.md`：当前 v1 摘要及较早迁移历史；
- `scripts/hmasd_work_packet.py`：Work Packet、planner、return witness 等；
- `scripts/hmasd_protocol_contracts.py`：typed Effect/ref、shared-core binding 和资源合同；
- `scripts/hmasd_codex_tasks.py`：Codex App Server native adapter；
- `scripts/hmasd_state.py`、`hmasd_run.py`、`hmasd_worktree.py`、`hmasd_external_review.py`：既有 authority/Effect 专用实现；
- `.agents/skills/hmasd-*`：各 top-level task 和 leaf 面向一个切面的短操作手册。

相关 focused tests 当前分布在：

- `tests/hmasd_work_packet_test.py`；
- `tests/hmasd_workflow_protocol_test.py`；
- `tests/hmasd_work_return_overlap_test.py`；
- `tests/hmasd_protocol_contracts_test.py`；
- `tests/hmasd_codex_tasks_test.py`；
- `tests/hmasd_workflow_golden_path_test.py`；
- state、recovery、run、worktree、external-review 的既有测试。

Stage A–C 已有明确的 112 focused tests 通过记录。Stage D 文件在本报告写作时仍处于主 Root 的独立审阅和 live compatibility 收口阶段；不要从“文件已存在”推断所有真实 Codex task 行为已经通过。

## 10. 当前仍需区分的证明层级

后续报告不得把以下层级混写：

1. **纯协议单元测试**：证明 canonicalization、绑定、幂等和 conflict predicate。
2. **Fake transport integration**：证明程序模块可以组合，但不能证明 Codex 产品接口。
3. **真实无模型 App Server smoke**：只验证 initialize/list/read/resume 等 transport 能力，不验证模型遵守协议。
4. **Ephemeral real-turn conformance**：验证一个真实模型回合收到协议并产生预期结构；仍不是完整研究流水线。
5. **Zero-Clerk golden path**：真实独立 EM→CM→Operator→Root，包含低成本 result-bearing command、重复 delivery、session 中断和 UNKNOWN Effect，且不唤醒 Clerk。
6. **无人值守 production GREEN**：只有上述链路及恢复边界在目标 Codex host 上通过后才能声明。

截至本报告快照，Stage A–C 是已验证本地协议合同；Stage D 本地合同已大体落地；完整 live conformance 和 zero-Clerk 黄金路径仍不能因文档声明而自动视为完成。

## 11. 给后续模型的操作指引

接手前：

1. 读取当前 `AGENTS.md`，不要从本报告恢复执行规则。
2. 读取与你身份匹配的 bootstrap skill 和 `hmasd-slice-interface`。
3. 若处理一个 work，只接收 exact `work_id` 和 packet locator。
4. 重新读取 packet 点名的 authority refs；不要依赖本报告或聊天摘要判断当前 revision。
5. 观察 Effect 现状后再行动；UNKNOWN 不重放。

设计新机制前：

1. 写出一个可复现失败；
2. 说明现有 packet、return、typed Effect、comparator 或 native adapter 为什么不能解决；
3. 先写失败测试；
4. 证明新机制没有建立第二 authority、queue、ledger、daemon 或 permission gate；
5. 写出它的删除条件。

必须避免：

- 从 `BLOCKED`、`FAILED`、`READY` 等单词推断全局语义；
- 让 Workflow-Clerk 参与普通 routing；
- 扫描整个 ready tree 来“寻找工作”；
- 从 opaque string 猜文件路径；
- 把 review/test 当授权令牌；
- 因 session 消失而提升研究 generation；
- 为了“更安全”增加未被失败测试要求的审批；
- 把一次局部 MARL 数值事故上升为全项目精度政策；
- 把开源项目的术语、数据库或状态机直接搬入 HMASD。

## 12. 最终高级结论

这轮会话不是简单地“设计了一套更完整的工作流”。它首先亲自复现了工作流过度设计：用户和模型通过一百多个局部问题不断增加制度，直到真实黄金路径的串行交接成本暴露出组合失败；随后又亲自复现了“用一个更聪明的 Clerk 解决多模型歧义”仍然会失败。

最终得到的认识是：

> HMASD 不应是很多 LLM 共同理解并管理一个复杂流程，而应是一个由确定性协议约束的并发系统，只在需要科学、工程和真实异常判断的位置调用 LLM。

换句话说：

- 协议统一，但执行分散；
- authority 稳定，但 session 可丢失；
- 方向可并行，但文件和 Effect 必须正交；
- Root 能力最高，但不是所有文件和决定的默认所有者；
- 用户可以覆盖普通流程，但未知外部提交不能被语言伪装成已知；
- Clerk 可以记录异常，但不能成为常规控制器；
- 文档解释为什么，程序决定原子动作；
- 新复杂度必须由真实失败证明，而不是由模型的不安证明。

这才是本次完整对话留给后续模型的核心交接。
