# HMASD Workflow Protocol v1

本文件是可操作的协议规范，不是新的 durable authority、权限系统或任务
数据库。它约束正常运行时的输入、输出和原子动作；科学与工程含义仍由
现有 authority 的 owner 决定。

v1 基础是 existing durable Authority+CAS、exact Work Packet、typed Effect/ref
observer，以及 bounded `reconcile --once` + native adapter。Return witness 是
canonical typed `agent_result` 与可选 draft 的 ignored runtime 表示，不是独立
completion ledger；resource comparator 与 short dispatch lock 是 reconcile/adapter
内部纯机制，不升格为原语。Workflow-Clerk 的专用 top-level intake 是
正常入口：它调用既有 scripts 与 `run-chain`，不自己实现第二控制面。

## 1. 参与者与边界

- **协议内核**：无状态、确定性、一次只处理一个 `work_id`。它读取精确
  的 Work Packet 与 fresh observed snapshot，校验并产生一个闭合动作；不
  从 Markdown、路径名称或自由文本推断任务含义。
- **生产者**（Root、Portfolio、EM、CM 或被授权的 bounded worker）：直接
  产生 machine-valid `agent_result`，必要时附带完整的 next-packet draft。
  生产者负责 domain judgment，不负责跨 session transport。
- **运行时适配层**：执行内核已经闭合的发送、创建意图、Effect 观察或等待
  操作，并返回可观察事实。它不改变 packet 或 authority 的语义。
- **Workflow-Clerk**：低介入的正常 top-level 协调席。它从专用 intake 为一个
  exact 起始 `work_id` 调用 `run-chain`，由程序完成 task create/reuse、
  publish/dispatch、wait、有界恢复和 result collection。Clerk 不解释 FSM、
  不从 prose 猜路由、不发明 gate、不写 authority 且不持有 Effect。同一任务
  的异常路径只记录程序生成的 exact typed-field/ref/schema/identity 缺陷
  或 legacy-unroutable input，并返回 program-named owner。
- **Root / 用户**：最高能力，可对 exact scope 直接 override，不需要 Clerk
  ack；危险操作只须发出警告并保留记录，不得用额外 gate 制造逻辑死锁。

## 2. Message contracts

### 2.1 Protocol input

每次调用必须携带：

1. 一个 exact `work_id`（不得全局扫描 ready items）；
2. 该 packet 的 locator、canonical content/hash、authority refs、revision、
   `owned_paths`、Effects、done criteria 和 receiver identity；
3. 一个 fresh observed snapshot：目标 task identity/lifecycle、相关
   authority revision、相关 Effect 状态和 packet existence；
4. 可选的同一 `work_id` 的 `agent_result`。

缺失、过期或互相矛盾的字段是协议错误，不得由内核猜测、补全文案或改变
   objective、non-goals、owned paths、Effect、terminality、next owner。
普通 Work Packet 的 `target_identity=Workflow-Clerk` 非法；Clerk 使用专用
top-level task intake，不走普通 packet 合同。

### 2.2 Producer result

结果使用现有 `hmasd_agent_result` envelope，并要求：

- `assignment_id == work_id`，`logical_identity`、`role`、`generation` 与
  observed task identity 一致；
- `status`、`materiality`、`state_refs`、`artifact_refs`、`next_action` 和
  `payload` 通过 schema 校验；
- `payload` 只陈述本 slice 的事实、结果和证据。`next_action.kind` 必须是
  闭合集合：`NONE`、`RESUME_SAME_SLICE`、`REQUEST_PORTFOLIO_DECISION`、
  `REQUEST_EM_DECISION`、`REQUEST_CM_ENGINEERING`、`REQUEST_ROOT_ACTION`、
  `OBSERVE_EFFECT`、`WAIT_FOR_REF`；
- 当结果包含 next-packet draft 且 `next_action.kind` 为 `REQUEST_*` 时，
  `next_action.input_refs` 必须恰好包含该 draft 的 `work_id`；result 与 draft
  不得跨 `work_id` 绑定。
- 可选 `next_packet_draft` 必须包含完整 objective、non-goals、authority
  refs/revisions、exact owned paths、done criteria、Effect refs 和 receiver
  identity；draft 是候选输入，不是 authority，也不自动发布。

成功实验由 `hmasd_run.py` 机械发布固定 `operator-result.json`（R）。令 M 为
manifest、S/E 为 stdout/stderr：R 自身精确保持 `state_refs=[M]`、
`artifact_refs=[S,E]`，不 self-reference；CM typed return 精确保持
`state_refs=[M]`、`artifact_refs=[R,S,E]`、
`payload.verification_refs=[M,S,E]`，顺序固定且无额外或重复 ref。R 是既有 run
evidence 的机械文件表示，不是新的 workflow primitive、authority、receipt 或
completion ledger。

不得使用裸 `BLOCKED` 传播故障。结果必须给出 `failure_scope`（project、
direction、feature 或 effect）和 `failure_ref`；没有范围的 blocked 结果为
`CONFLICT`。

## 3. Atomic verbs

内核的唯一闭合输出是以下七项之一，且一次最多一个：

- `PUBLISH_PACKET_INTENT`：携带已完整校验的 canonical next-packet draft，
  仅表示发布意图；调用者随后必须使用既有 publish CLI 原子发布，内核不
  偷偷执行 publish。发布成功后，再以新 `work_id` 执行 event-local
  reconcile。
- `DISPATCH_EXISTING`：向已观测存在且身份匹配的 receiver 发送既有 packet
  locator；重复 delivery 由 `work_id` 幂等处理。
- `CREATE_TASK_INTENT`：输出 canonical manager identity 的创建意图；`run-chain` 调用者
  （正常为 Clerk）重新观察 task list 后至多执行一次 create，未知结果
  先观察，不盲目重试。
- `OBSERVE_EFFECT_ONLY`：对 `UNKNOWN_EFFECT` 只做观察，不 retry、不重发。
- `WAIT_FOR_REF`：等待指定 task/effect/ref 的外部完成事实，不轮询模型、不
  创建新 packet。
- `NOOP_TERMINAL`：snapshot 已证明 terminal 或该 `work_id` 已处理，什么也
  不发送。
- `CONFLICT`：身份、revision、schema、target 或责任边界冲突；authority/path/
  Effect identity conflict 固定交 Root，内核不得自行修复语义。

内核永远不输出 `AUTHORIZED`、`APPROVE`、`DENY`、`FREEZE`、`RETRY` 或新的
owner 决策。

## 4. Normal flow

1. domain owner 冻结 authority；sender 从该 authority 生成并使用既有 publish
   CLI 原子发布一个完整 Work Packet。Clerk 的专用 top-level turn 以该
   exact `work_id` 调用 `run-chain`；Clerk 本身不成为 packet receiver。
2. receiver 接收该 packet，完成其 bounded work，写入 owned facts；随后才
   产生对应 machine-valid `agent_result`，必要时附带 next-packet draft。
3. 适配层调用 `reconcile --once --work-id X`，内核只读取 X 和 fresh
   snapshot。
4. 内核校验 identity、revision、write set、Effect 和 result binding，闭合
   一个 atomic verb。
5. 适配层执行该 verb；发送/创建/等待/观察的事实写入现有运行时记录，不能
   变成新的 authority、queue、lease 或 completion ledger。
6. receiver 以同一 `work_id` 幂等处理；若需后续工作，receiver 先 build
   canonical `next_packet_draft`，再在 REQUEST result 的 `input_refs` 写入
   `[draft.work_id]`。内核只在 draft 完整且 authority/revision 仍匹配时产生
   `PUBLISH_PACKET_INTENT`；调用者原子发布后，才以新 `work_id` 重新 reconcile，
   由内核产生 `DISPATCH_EXISTING` 或 `CREATE_TASK_INTENT`。
7. receiver 先按 exact `work_id` 查找已有 return witness，再完成 slice、发布
   immutable witness，最后才发送消息。消息丢失时从 witness 重建；terminal
   且无 return 时依据 native history 对同一 `work_id` resume，最多三次。
   UNKNOWN send/create 只观察，不重放；不因 session 更换创建语义相同的新 packet。

Native dispatch 的关键区仅包括 fresh identity、active peers 和 resource
comparison，然后 create-or-reuse 与 send；它由 Clerk 调用的 `run-chain` 机械
组合，不是新的持久控制层。普通 packet/result 仍只投递给真实 participant；
Clerk 收集 run-chain 的 terminal fact 并向用户报告。

## 5. Exception predicates

仅以下由程序生成、并明确指出缺失字段或引用的条件可进入 Clerk：

- 缺少指定的 typed field（字段路径必须列出）；
- 缺少指定的 ref（ref 类型与 locator 必须列出）；
- 指定 field/ref 的 schema 或 identity 不匹配（实际值与期望约束必须列出）；
- legacy packet 的 receiver/责任无法从闭合表机械解析。

前三类缺陷不得以“无法定位”或其他模糊描述表示；Protocol Defect envelope
必须输出 `field_path`、`ref`（null 或 typed ref）、`actual`、`expected`、
`failure_scope`、`producing_command` 和 `responsible_owner`。v1 protocol
recovery 的 `responsible_owner` 固定为 `Root`；模型不得从 target 或 prose
猜测责任。

以下情况不进入 Clerk 的异常文书路径：普通 dispatch、create、wait、
fan-in、同 identity 恢复、`UNKNOWN_EFFECT`、已有 terminal 结果、authority/path/
Effect identity conflict、材料决定和 Root override。这些仍是 normal `run-chain` 的
机械 fact。`UNKNOWN_EFFECT` 固定走 `OBSERVE_EFFECT_ONLY`；identity conflict 固定
交 Root；`RECOVERY_EXHAUSTED` 由 Clerk 以 exact scope/ref/evidence 向用户报告。
Clerk 不把异常扩大为项目级阻塞，也不把 `BLOCKED` 当 session 终止词。

## 6. Concurrency and idempotency

- 同一 `work_id`、receiver、authority revision 和 Effect envelope 串行；不同
  direction 且 write set/effect 不相交时可并行。
- packet delivery 是 at-least-once；`work_id` 是幂等键，重复输入只能得到
  相同事实/动作，不得派生新 packet。
- task creation 是 repeatable intent，不是 receipt；`run-chain` 调用者（正常为
  Clerk）对 canonical identity 单飞，unknown commitment 只观察不重试。
- 内核无 queue、lease、cursor、ack、completion ledger、daemon、global scan
  或 generic handler；不存在第二个 selector。

不同 `work_id` 是否可并行由 explicit resource comparator 比较 write/effect
资源后确定；比较器是原子读式判断，不持有 lease 或 claim。Root 可用
`--root-override-reason` 绕过已知 overlap/active-unknown，并将 warning 写入
native history；不能伪装 UNKNOWN send/create，也不能绕过 hard effect identity。

## 7. Current Stage D boundary

本地协议合同已闭合；live evidence 分层如下：

- `LOCAL_FAKE_TRANSPORT_GOLDEN` 已通过，包含真实短命令 `hmasd_run`；
  它只是底层 fake transport 证据，不是 zero-Clerk 或 full-workflow acceptance；
- real no-model probe（list/read/resume）已通过；
- ephemeral Luna-low read-only no-network conformance 已返回 `CONFORMANCE_OK`；
- 真实唯一 Experiment Operator leaf 已在 OMP worktree 一次执行至
  `SUCCEEDED/exit0/group_quiescent/stdout marker`；
- 完整 real-native Clerk→EM→CM→Operator→Clerk unattended chain 仍未证明。

`done_criteria` 只是 hash-bound 描述；terminal proof 来自 typed owner result
与 domain refs，程序不声称理解自然语言。Effect 必须有 typed
`kind`、`resource_id` 和可选 `operation`；legacy path-only Effect 仅作只读兼容
并在自动流中报告精确冲突，不建立 generic Effect executor。opaque file refs
必须结构化并验证新鲜度；所有 common file evidence 使用 path+sha `file_ref`，
legacy string file refs 为 schema-invalid；真正的 operation ID 保持 opaque。
`file_ref` 与 `changed_paths` 均采用 Windows-safe canonical repo-relative 规则：
拒绝绝对路径、`..`、反斜杠别名、symlink/reparse alias，统一 slash 表示，并以
casefold 后集合去重；不得把 case-only 差异视为两个资源。

Shared-core 只有 CM/Root code/Git action 可写。其 fenced record 的 exact v1
authority allowlist 仅为 `AGENTS.md`、`docs/project/WORKFLOW_PROTOCOL.md`、
`docs/research/portfolio/PORTFOLIO.md` 和对应的
`docs/research/candidates/<id>/DIRECTION.md`；任何其他 Markdown（包括
`WORKFLOW_DESIGN_PHILOSOPHY.md`）即使已在 base 中跟踪也不是 authority。
Portfolio registry JSON 仅是既有 writer-path 豁免，不承载 fence。EM、Portfolio 和 ordinary leaf
携带非 writer-owned shared-core path 时拒绝；Portfolio 仅其两条 existing
authority writer path 豁免。action 必须来自 base 已跟踪的 existing durable
Markdown authority，使用顶层 fenced `hmasd-shared-core-action-v1` record，
同 bytes 重验 hash，并绑定 current base、全部路径、objective、non-goals 与
allowed effects；程序证明 byte match，不证明对话中真实同意。direction-owned
与 Portfolio/EM authority 不增加新 gate。

以下能力已由 Stage A/B/C/D 本地验证覆盖：exact `--work-id`、typed result binding、
closed protocol `next_action`、complete draft validation、Portfolio project→direction
identity、scoped `BLOCKED`，fair cursor/global scan/generic handler 的移除、
self-cycle 拒绝、result↔draft `work_id` 唯一绑定、structured result refs
freshness、explicit task snapshot 与 dispatchable locator、payload/envelope paths
一致、status/action 一致，以及 absolute input ref 拒绝。

## 8. Acceptance tests (8)

1. **Exact-key**：给出两个 ready packet，指定一个 `work_id`，内核只读并处
   理该 key，不扫描或改变另一个。
2. **Typed return**：result 的 `assignment_id`、identity、schema 任一不匹配
   时输出 `CONFLICT`，不猜测 next owner。
3. **Complete draft**：缺 objective、paths、Effect 或 done criteria 的 draft
   不得产生 publish intent；完整且 revision 匹配时只输出一个
   `PUBLISH_PACKET_INTENT`，发布后必须使用新 `work_id` 再 reconcile。
4. **Same-scope slice**：CM 的 review→repair→test→verify 在同一 packet/
   work_id 内完成，不产生 EM/CM 链式 packet 或 Clerk exception intake。
5. **Unknown effect**：Effect commitment unknown 时只输出
   `OBSERVE_EFFECT_ONLY`，重复观察不产生 retry 或新 command。
6. **Identity conflict**：目标 task identity 冲突时只输出 `CONFLICT` 并路由
   Root；不创建第二 task、不由 Clerk 修复。
7. **Idempotent redelivery**：同一 packet 重复 delivery 得到相同 result/动作，
   不生成新 packet、ack ledger 或 completion state。
8. **Parallel disjointness**：两个不相交 direction 并行成功；同一 direction
   或重叠 write set 的并发输入被串行或 `CONFLICT`，无双重 Effect。

## 9. OSS reference cards

Codex native transport follows the documented [Codex App Server](https://learn.chatgpt.com/docs/app-server)
interface: stdio JSONL with thread/turn methods. ChatKit and Assistants threads
are not used as a Codex task API.

这些是设计参照，不是要照搬的基础设施：

- Kubernetes sample-controller 用窄 key 触发、重新读取对象、幂等 reconcile；
  对应本协议的 exact `work_id`、fresh snapshot 和 bounded verb。见
  [sample-controller](https://github.com/kubernetes/sample-controller)。
- Temporal 把 typed command 与 Effect/历史分离，允许从事实恢复；对应
  packet/result 合同与 Effect observe-only。见
  [Temporal concepts](https://docs.temporal.io/workflows#event-history)。
- Zuul 以 UUID、ready marker 和明确 pipeline 状态连接异步阶段；对应
  stable identity 与显式 terminal/ready 事实。见
  [Zuul](https://zuul-ci.org/docs/zuul/latest/).
- Ray 的稳定 task/object identity 与幂等边界可作参考；其分布式运行时
  复杂度也说明不要把基础设施整体引入本项目。见
  [Ray architecture](https://docs.ray.io/en/latest/ray-core/key-concepts.html)。

## 10. Cutover standard

Workflow-Clerk 的 normal top-level intake 与 terminal reporting 是用户确认的目标，不因
adapter 自动化程度提高而删除。退役的是独立 Workflow Recovery Manager 与历史
control-plane skills；恢复只组合 `run-chain`、`execute-plan`、`hmasd_run.py
reconcile`、`hmasd_direction_git.py observe-push` 和既有 Effect observers。
切换不得新增替代 queue、lease、daemon、recovery role/skill 或第二套 durable
workflow schema。
