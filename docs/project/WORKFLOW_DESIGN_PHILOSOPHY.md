# HMASD 工作流设计哲学

## 文件地位

本文件是 informational design rationale：记录为什么采用某些工作流
设计取向，供后续设计、评审和故障复盘参考。

本文件不是 Durable Authority。

本文件不是 registry、状态机、permission gate、approval gate、schema
或 checklist。

它不创建新的事实来源、任务状态、权限边界、审批条件或持久化协议。

执行规则来自 `AGENTS.md` 与匹配的 project skill；existing authority 承载
其范围内的 durable facts/decisions。本文件不覆盖二者。

Evidence reviewed: 2026-08-25。以下第一方链接会随上游项目演进；pattern
cards 是参考记录，不是冻结 authority。

文中的开源项目只提供问题—方案—原则的设计样例，不是 HMASD 的上游
依赖，也不把上游术语直接加入 HMASD 状态词汇。

## 稳定哲学

以下是 HMASD 作者的综合推论，不是上游项目事实或实施义务。

共同内核是：可恢复单元绑定版本化意图与稳定身份；执行前读取当前事实；
明确 Effect 边界；由幂等性与提交不确定性决定重试；由依赖、写集与资源
决定并行；恢复时服从用户最新意图并重新核验。

### 1. 先区分想要什么与看见什么

- desired 是目标或意图；observed 是当前可核验事实。
- 任何推进行动都必须以当前 observed 为输入，而不是把旧意图当成
  已发生的结果。
- 目标未变不代表外部 Effect 未发生；没有观察到变化也不等于没有变化。
- 设计文档可以解释两者关系，但不替 authority 产生新状态。

### 2. 用有界 reconcile 面对不确定性

- 每次 reconcile 只处理一个明确 scope、target 和 revision 的有界动作。
- 动作结束后重新观察事实；不要在一次调用中隐式展开无限循环。
- 失败范围必须具体到 project、direction、feature 或 Effect，不能传播
  一个无范围的全局失败标签。
- 若依据不足，停止在最小可恢复事实边界，并留下可复核的观察点。

### 3. 协调与 Effect 分离

- 协调负责选择、排序、分派和观察；Effect 负责实际改变外部世界。
- 协调记录“已请求”不等于 Effect 已提交或已完成。
- 外部调用返回 UNKNOWN 时先观察、核对提交证据或最终事实；未知承诺
  未消除前不重发同一 at-most-once 操作。
- 跨 session 消息必须绑定确知的 owner/authority/Effect refs；session 更换
  可重传未变化 refs，但只有实际变化成为新的 durable fact，瞬时猜测不成为
  持久依赖。

### 4. 在责任和语义边界内恢复

- 恢复动作只能修复自身拥有的 scope，不能借故改写别的 owner 的事实。
- 不静默改变科学、数值、RNG、checkpoint、bit-identity 或外部 Effect
  语义；这不要求普通数值工作默认 bit identity。
- 任务创建、会话连续性或历史文档本身不授予额外决策权。
- 能靠重新观察解决的问题，不升级为全局重建或跨边界补偿。
- 无人值守恢复只在 owner 内对可逆、语义不变故障做有界动作；用真实
  证据选择下一尝试，不设全局固定 retry 数。合理本地路线用尽或缺少
  用户/material authority 时，只等待精确 scope 与 resume condition，
  无关方向继续。

### 5. 跨 session 与 handoff

- session 切分可因容量或上下文发生，不等同材料边界。
- handoff 把会话、摘要和 packet 当 locator/provenance，重新读取 authority，
  并核验 revision、hash、base、owned paths、current owner、allowed Effects
  和 unknown external state。
- 现有 Work Packet refs 仍然传递；只有真正变化才成为新的 durable fact。

### 6. 让方向与 Git/worktree 默认正交

- 方向的科学或工程工作不自动等于 Git 集成工作。
- worktree 只隔离写入，不证明可集成；以写集、shared-core、target ref
  和显式依赖判断相交。无交集可并行，相交处串行，集成前重验 prospective
  target state。
- 需要跨边界时，绑定精确路径、基线、目标和允许效果；不要由目录名
  或历史分支猜测归属。
- 一个冻结动作应产生一个可观察结果，不把冻结、打包、动作再包成
  第二套元流程。

### 7. 资源是并发的现实边界

- 并发度由 CPU、内存、外部配额、人工注意力和故障半径共同决定。
- 先用 CPU、RAM、GPU、配额和注意力限制 in-flight。只批处理独立同质且
  不改变顺序、RNG、授权或 Effect 语义的项；UNKNOWN external Effect、
  冲突写入、依赖或自适应调查保持串行。
- 批大小由吞吐、峰值内存、尾延迟和失败半径测量。
- 资源紧张时先减少工作集、批处理或分片；不把不安全的内存计划交给
  审批来侥幸通过。
- 并发是容量事实，不自动证明需要 lease、queue 或 DAG。

### 8. 可观测性服务于下钻

- Dashboard 和日志是可下钻的投影，不是 authority。
- 投影应能回指稳定的 scope、revision、owner、Effect 和证据引用。
- 摘要是有损压缩；LLM 摘要不能取代原始事实、原始响应或精确归档。
- handoff 绑定稳定 refs，接收方按 refs 重新读取必要事实，不递归复制
  全部祖先上下文。

### 9. 用户最高控制权

- 用户可暂停、取消、收窄或改写未来 desired；Root 是永久最高操作能力，
  可使用全部 genuine leaf。
- 角色、重试和历史不能凌驾新指令；新指令不能抹去已发生或 UNKNOWN 的
  Effect。材料决定写入既有 authority 后，才能跨任务依赖。
- 警告和记录不成为权限服务；Root 的高能力不使其成为默认文件作者或
  Git staging scene。

### 10. 新机制由可检验需要证明

- 证据可以是已观察失败、可信反例或风险、测得规模/资源阈值，或与
  HMASD 同构的上游故障类；再讨论新组件或新层次。
- 不为想象中的未来故障预先建设 daemon、全局事件总线或第二套 authority。

## 反 cargo-cult 推导规则

以下推导一律不成立：

- desired state 不能自动推出 daemon。
- 恢复不能自动推出 event sourcing。
- 并发不能自动推出 lease、queue 或 DAG。
- 角色不能自动推出 RBAC。
- Git 安全不能自动推出 merge queue。
- 失败不能自动推出 incident 系统或全局 `BLOCKED`。

本文件只为能以可检验需要说明相对现有最小设计的因果收益、可否证性和
撤回路径的提案提供设计理由；否则不背书，但不产生必填字段、artifact、
状态或阻塞条件。

## 当前 HMASD 的含义

- 基础仍是 existing durable Authority+CAS、exact Work Packet、typed Effect/ref
  observers，以及 bounded `reconcile --once` + native adapter。Return witness
  只是 canonical typed `agent_result` 与可选 draft 的 ignored runtime 表示，
  不是独立 completion ledger；resource comparator 与 short dispatch lock 是
  reconcile/adapter 内部纯机制，不升格为原语。
- Live evidence 已分层：real no-model list/read/resume 已通过；ephemeral Luna-low
  read-only no-network conformance 返回 `CONFORMANCE_OK`；`LOCAL_FAKE_TRANSPORT_GOLDEN`
  已通过且含真实短命令 `hmasd_run`；真实唯一 Experiment Operator leaf 已一次执行至
  `SUCCEEDED/exit0/group_quiescent/stdout marker`。完整 real-native
  EM→CM→Operator→Root unattended chain 仍未证明。
- 正常路径由无状态、确定性的协议内核承担：输入是单个 exact `work_id`
  和 fresh observed snapshot，生产者直接输出 machine-valid result 与可选的
  完整 next-packet draft，内核只产生一个闭合 atomic verb。它不从 Markdown、
  路径或自由文本推断责任、Effect、terminality 或 next owner。
- `Workflow-Clerk` 不是 runtime coordinator，而是低介入的异常文书席。它只
  接程序生成的 exact typed-field/ref/schema/identity 缺陷或 legacy unroutable；
  authority/path/Effect identity conflict 固定交 Root，材料决定交 domain
  owner/user，Root override 直接记录 warning/reason；不负责普通 packet
  projection、routing、wait、fan-in、retry、create、dispatch 或 authority 写入。
  普通流程零 Clerk，普通 packet 不得以 Workflow-Clerk 为 target_identity。
- 该收缩回应本地 fresh-agent 压力测试中的可复现失效：把简单哲学交给多个
  session 会诱发自行增加 packet、gate 和 authority hops。稳定协议与程序化
  原子动作应先约束这些行为；Clerk 只保留无法机械判定的异常入口。
- 协议内核与适配层不新增 queue、lease、cursor、ack、completion ledger、
  daemon 或第二套 durable workflow schema；若 native routing 能消除异常
  入口，应按删除标准移除 Clerk。
- normal path 是 Root exact reconcile 后进入短 native-dispatch critical section：
  fresh identity/active peers/resource compare，再 create-or-reuse/send。receiver
  先 exact return lookup，完成 slice，publish return witness，再发消息；消息丢失
  从 witness 重建，terminal 无 return 时仅按 native history 对同一 work_id resume
  最多三次。UNKNOWN send/create 只观察。`done_criteria` 只是 hash-bound 描述，
  terminal proof 来自 typed owner result/domain refs，不由程序理解自然语言。
- Effect 采用 typed kind/resource_id/optional operation；legacy path-only 只读兼容并
  在自动流报告精确冲突，不建立 generic Effect executor。所有 common file evidence
  使用 path+sha `file_ref`，legacy string file refs 为 schema-invalid；true operation
  IDs 保持 opaque。
- `file_ref` 与 `changed_paths` 采用 Windows-safe canonical repo-relative 规则，拒绝
  absolute/`..`/backslash/symlink-reparse alias，统一 slash，并以 casefold 去重。
- Protocol Defect envelope 必须含 `field_path`、`ref`（null 或 typed）、`actual`、
  `expected`、`failure_scope`、`producing_command` 和 `responsible_owner`；v1 protocol
  recovery owner 固定为 Root，不从 target 或 prose 猜测。
- shared-core 仅 CM/Root code/Git action 可写；EM、Portfolio 和 ordinary leaf 携带
  非 writer-owned shared-core path 时拒绝，Portfolio 仅其两条 existing authority
  writer path 豁免。exact v1 authority allowlist 仅为 `AGENTS.md`、
  `docs/project/WORKFLOW_PROTOCOL.md`、`docs/research/portfolio/PORTFOLIO.md` 和
  `docs/research/candidates/<id>/DIRECTION.md`；其他 Markdown（包括本文件）不是
  authority。Portfolio registry JSON 仅 writer-path 豁免，不承载 fence。record 必须来自
  base 已跟踪的 existing durable Markdown authority，
  使用顶层 fenced `hmasd-shared-core-action-v1`，同 bytes 重验 hash，并绑定 current
  base/all paths/objective/non-goals/allowed effects；程序只证明 byte match，不证明
  对话真实同意。direction-owned 与 Portfolio/EM authority 不新增 gate。
- Root 可用 `--root-override-reason` 绕过 known overlap/active-unknown，并把 warning
  写入 native history；不能伪装 UNKNOWN send/create 或绕过 hard effect identity。
- 同一 frozen packet、owned paths 和 Effect envelope 内的可逆实现与修复，
  可保持一个可恢复上下文；session 可以更换。Reviewer、SANCheck、Operator
  和 result-command 的独立 owner、Effect、receipt 不被合并。
- Portfolio 只在投资决定或生命周期改变时介入，不为普通 scope 内推进
  充当额外协调层。
- Work Packet 只引用当前 scope 和必要证据；它不递归复制全部祖先，
  也不成为新的 durable authority。
- Root Git 沿用现有 confirmation、Work Packet、worktree 和 receipt 边界，
  不在其外再建 freeze-of-freeze 或 action-about-action 平行元流程。
- 不新增 complexity gate；复杂度判断留在真实失败证据和现有 authority
  的决策责任内。
- Dashboard、日志、任务身份和历史摘要都只是投影或证据入口，不能改变
  当前 owner、Effect 或执行规则。

## 开源项目 pattern cards

### Adoption firewall

卡片的存在、顺序、数量或缺失不代表 adopted、rejected 或 pending，不产生
backlog、coverage、兼容性或评审义务，也不能授权、阻塞或证明实现。

### Pattern Card 1：Kubernetes controllers

**上游问题**：声明目标与实际对象会偏离，需要持续观察并趋近目标。

**实际方案（第一方事实）**：Kubernetes 描述 controller 观察当前状态并使
其接近期望状态；其对象区分 spec 与 status。controller-runtime 的
Reconciler 读取请求并返回结果或错误。[Kubernetes Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)
、[controller-runtime Reconcile](https://github.com/kubernetes-sigs/controller-runtime/blob/main/pkg/reconcile/reconcile.go)

**HMASD 作者推论（非实施建议）**：desired/observed 分离和重新读取当前状态，有助于避免把意图误当结果。

**HMASD 当前选择与证据边界**：HMASD 使用自己的四原语；“有界一次动作”
是 HMASD 的收窄，不冒充 Kubernetes 事实。

**何时重新评估**：出现可复现的 stale read、重复 Effect 或 scope 无法
有界收敛的证据时重新核对，而非由卡片自动触发机制。

### Pattern Card 2：Temporal

**上游问题**：长流程需要确定性执行依据、事件历史和有边界的重试。

**实际方案（第一方事实）**：Temporal 区分 deterministic Workflow、durable
append-only Event History 与外部/LLM/API Activity；Activities 默认 retry，
Workflows 默认不 retry。[事件](https://github.com/temporalio/documentation/blob/main/docs/encyclopedia/workflow/workflow-execution/event.mdx)
、[重试策略](https://github.com/temporalio/documentation/blob/main/docs/encyclopedia/retry-policies.mdx)
、[定义](https://github.com/temporalio/documentation/blob/main/docs/encyclopedia/workflow/workflow-definition.mdx)

**HMASD 作者推论（非实施建议）**：定义、事件和外部 Effect 的边界应分开说明；不能把 deterministic Workflow、Event History 和 retry 混写。

**HMASD 当前选择与证据边界**：HMASD 依据 idempotency 与提交不确定性
决定观察或重试，不由 Temporal 的默认值推导本地规则。

**何时重新评估**：出现跨 session 重放不一致、Activity 类 UNKNOWN 或已
观察的重复提交时，重新核对是否需要不同的本地证据边界。

### Pattern Card 3：Zuul

**上游问题**：独立变更的测试结果不足以证明依赖变更组合的集成安全。

**实际方案（第一方事实）**：independent manager 处理独立事件；dependent
gate 构造 speculative merged future state，前序失败会使后项结果失效并
重测，相关项目才共享 queue。[Gating](https://zuul-ci.org/docs/zuul/latest/gating.html)
、[Pipeline](https://zuul-ci.org/docs/zuul/latest/config/pipeline.html)
、[Project](https://zuul-ci.org/docs/zuul/latest/config/project.html)

**HMASD 作者推论（非实施建议）**：写集和目标状态比任务数量更能说明
哪些工作必须串行。

**HMASD 当前选择与证据边界**：Git/worktree 正交；只在显式依赖、相交
写集和现有集成边界下重验，不采用 Zuul queue 语义。

**何时重新评估**：观察到 prospective target 与独立验证结果系统性偏离
时，重新核对写集、target ref 和依赖证据。

### Pattern Card 4：Ray Core

**上游问题**：任务过细放大调度开销，pending 工作挤压资源，actor 故障
与重试又带来提交不确定性。

**实际方案（第一方事实）**：Ray 分别讨论 logical resource admission、
pending backpressure、task granularity/batching，以及 actor retry、
at-most-once 与 unknown outcome。[任务粒度](https://docs.ray.io/en/latest/ray-core/patterns/too-fine-grained-tasks.html)
、[限制 pending tasks](https://docs.ray.io/en/latest/ray-core/patterns/limit-pending-tasks.html)
、[资源](https://docs.ray.io/en/latest/ray-core/scheduling/resources.html)
、[Actor 容错](https://docs.ray.io/en/latest/ray-core/fault_tolerance/actors.html)

**HMASD 作者推论（非实施建议）**：资源、批量粒度、pending 规模和外部
Effect 应分别测量，不以一个“并发”标签代替因果解释。

**HMASD 当前选择与证据边界**：只按本地 CPU/RAM/GPU/配额/注意力与写集
控制 in-flight；不从 Ray 推导 scheduler、actor、queue 或 lease。

**何时重新评估**：测得峰值内存、尾延迟或失败半径随批大小恶化，或出现
重复/UNKNOWN Effect 时，重新测量并调整最小本地路线。

### Pattern Card 5：Dagster

**上游问题**：持久化数据对象需要声明、物化、追踪和可操作的运行视图。

**实际方案（第一方事实）**：Dagster asset 是 persistent data object；其
UI/webserver 可查询，也可 launch、re-execute、materialize。[Assets](https://docs.dagster.io/guides/build/assets)
、[Webserver](https://docs.dagster.io/guides/operate/webserver)

**HMASD 作者推论（非实施建议）**：产物、定义、运行和证据应以稳定引用
关联，但可操作投影仍不等于事实 authority。

**HMASD 当前选择与证据边界**：本地 Dashboard 保持 read-only；不把
Dagster UI 的操作能力解释为 HMASD 的实现义务。

**何时重新评估**：用户无法从投影下钻到稳定 scope/revision/effect 证据，
或出现投影与 authority 分歧时，重新检查投影边界。

### Pattern Card 6：OpenHands

**上游问题**：对话执行要跨会话保存上下文，并保留可追踪的事件历史与
压缩视图。

**实际方案（第一方事实）**：OpenHands 使用 `base_state.json` 与每事件
append files，保留完整历史，并提供 condensation view。[会话持久化](https://docs.openhands.dev/sdk/guides/convo-persistence)
、[事件架构](https://docs.openhands.dev/sdk/arch/events)

**HMASD 作者推论（非实施建议）**：摘要、locator/provenance 与原始证据
应分层；handoff 应重新读取 authority，而非复制全部祖先。

**HMASD 当前选择与证据边界**：这是 conversation-local 方案的记录，不能
证明 HMASD 需要 project event store、事件文件族或新 registry。

**何时重新评估**：出现跨 session 丢失稳定 refs、无法重建关键事件或摘要
掩盖 UNKNOWN Effect 时，重新核对 handoff 所需证据。

## 结语

好的工作流设计首先减少误读、重复提交和跨边界恢复，其次才增加能力。

每一次新增机制都应能指出它替代了哪条更复杂的路径，以及未来何时可以
删除它。

若只能提供更多名词、层次或持久化对象，却不能提供可检验需要和因果收益，
则维持现有四原语更符合本哲学。
