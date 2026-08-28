# HMASD Session Envelope Protocol v3

本协议是 HMASD 正常跨 Codex session 的唯一协议。Codex 原生负责 task 身份、历史、
create/send/read/wait 与同 task 继续；v3 只定义 HMASD 的状态语义、消息 body、角色
转移、恢复和项目边界。本文中的 MUST/必须均为规范要求。

## 1. 权威与五维状态

v3 不允许一个字段同时表示“方向是否继续”“谁应行动”“task 是否运行”“领域工作到
哪一步”和“消息是否送达”。五个维度严格分离：

| 维度 | 唯一事实源 | 允许的解释 |
| --- | --- | --- |
| `lifecycle` | `docs/research/portfolio/workflow/registry.json` | Portfolio durable state：`REGISTERED / ACTIVE / PARKED / CLOSED` |
| `owner_stage` | Clerk 基于本 turn 新鲜事实生成的短期只读投影 | 当前 next event 的责任角色或阶段；不写回 authority |
| `native_task_status` | Codex native task list/read | task 的产品状态；原值保留，不归一化成 lifecycle |
| `research_phase / engineering_phase` | 对应 direction state | 领域进度；不能充当 delivery 或 owner |
| `delivery_state` | recipient 的 native task history | exact v3 message 与 correlation 是否可见；locator 文件存在、mtime 或 Dashboard 不算送达 |

任何 script、prompt 或 Dashboard 都不得把一个维度的值写成另一个维度的事实。尤其：

- research/engineering `COMPLETE` 不关闭方向；
- task `idle`、`completed`、`notLoaded` 不释放 standing authority；
- envelope 文件存在不证明 native send；
- Dashboard 看到新 state 不证明 Clerk 已消费 RETURN；
- `owner_stage` 只可由注明 provenance/freshness 的投影生成，不是 durable registry。

### 1.1 Lifecycle invariants

`REGISTERED` 表示 Portfolio 已知但尚未投资的候选。它不是 `CLOSED`，可以没有 EM/CM
task，也不会仅因 idle 产生 recovery。

`ACTIVE` 在每次 Clerk final drain 后必须恰好有一个 material next event：

1. 一个 current ASSIGNMENT 已在同方向 standing owner 的 native history 中；或
2. owner 用 `WAIT_RESOURCE` 保持 responsibility，且唯一 heartbeat 回到该 task；或
3. validated RETURN/PORTFOLIO_RETURN 正在本 Clerk turn 内被展开，且 ready send 在
   final 前完成。

缺代码、缺测试、当前 slice 完成、task idle、future Operator 尚未创建都不能让
ACTIVE 静默无 owner。非当前 owner 的 EM/CM idle 正常。

`PARKED` 必须同时具有：Portfolio durable transition、material reason、evidence refs、
明确 reactivation condition，以及该 condition 所需的用户/外部端点已经 native 送达。
PARKED 没有 current assignment、resource heartbeat 或 active Operator。普通内存/容量
重试与“实现不存在”不是 PARKED。

`CLOSED` 必须同时具有：Portfolio durable terminal reason、evidence refs、
`next_role=NONE`、无 next objective、无 current assignment/heartbeat/active experiment。
participant 局部完成不能产生 CLOSED。CLOSED 在当前 protocol epoch 内是 terminal；若
新证据要求重开，Portfolio 必须作显式新 decision，并由 Clerk 创建新的 manager
generation，而不能恢复已终止的 assignment。

## 2. Codex task plane 与 standing authority

Root、Workflow-Clerk、Portfolio、EM 和 CM 是 top-level tasks，不是 custom subagents。
Clerk 与 Portfolio 是 global long-lived tasks；EM/CM 在第一次成为某 direction 的 next
owner 时按需创建，之后在相同 `protocol_epoch / direction / role / generation` 下复用。

Clerk 每次创建前必须从 native task list/read 查找 exact identity；它不得依据本地
registry、runtime JSON 或 thread title 猜 task。已存在的同 identity task 即使 idle 也
继续使用；出现两个候选或 identity/history 冲突时停止该 direction 的 send，并把 exact
facts 交 Root。task 缺失时才使用 Codex 原生 create 创建真实可见 top-level task。

每个 standing task 的 bootstrap 固定角色、direction、generation、`protocol_epoch`、
expected `control_release`、role prompt 与本协议。assignment 只给 bounded slice，不
终止 standing mandate。EM/CM 不需要全局 topology，也不能创建或直接联系其他
top-level manager。

manager 的 direct leaves 可以并行，但 leaf 不能再次 delegate、不能调用
`send_message_to_thread` 联系 Clerk/其他 manager，也不能持有跨 session recipient ID。
Experiment Operator 固定是 CM direct leaf；即使 Dashboard 显示 `owner_stage=OPERATOR`，
方向的 top-level standing authority 仍在 CM，Operator terminal result 只回 CM。

## 3. Session Envelope v3

### 3.1 唯一 native line

每次跨 session send 的完整 native message 必须恰好是一行，字段顺序固定为：

```text
HMASD_SESSION_ENVELOPE_V3 kind=<kind> direction=<id> from=<role> to=<role> next=<role|NONE> id=<uuid> locator=<repo-relative-path>
```

不得在此前、此后或第二行添加 JSON、摘要、称呼或解释。`kind` 只能是：

- `ASSIGNMENT`
- `RETURN`
- `PORTFOLIO_RETURN`
- `CONTROL_NOTICE`

`id` 是 message UUID；`locator` 是 gitignored、repository-relative POSIX path。session
transport 不做 authentication，也不为本地 envelope body 生成或校验 digest。script 使用
exclusive create 先写 envelope；同一 locator 只有 canonical JSON bytes 完全相同时才可复用，
任何冲突都在 send 前拒绝；随后输出该 exact line。
Root 与 Clerk 用唯一 `assignment-from-brief` 入口，只提供 bounded objective 与
slice-specific semantic flags。Root→Clerk 使用 `--current-control-release` 由 script 观察当前
publishable release；Clerk→participant 用 `--control-release-envelope` 指向 validated ingress
并复制 release。script 读取固定 role/direction context、为这些外部内容生成 content refs、
补齐固定 return boundary 与 workspace default，并直接生成完整 body 和 envelope。两者都不创建 ASSIGNMENT
body 或 control-release JSON。
message ID 与 locator 共同承担本地幂等相关性；它们不是认证凭据。

recipient 把 Codex delegation 的 exact `input` 交给 v3 `read-message`。只有整行
full-match、body/schema/endpoint/control metadata 均通过才是工作流事件。裸 locator、
raw JSON、自然语言、非 V3 header、附带说明的 line 和 leaf report 都是 `NON_ENVELOPE`。
用户在可见 task 中的直接对话仍是用户输入，但其跨 task 控制影响必须转成
`CONTROL_NOTICE`。

locator 文件只是 write-once transport body，不是 delivery receipt、inbox、ack 或
lifecycle state。只有 recipient native history 中可见的 exact line 才改变
`delivery_state`。send 结果 unknown 时，sender 先观察 recipient native history；不得
盲目再 send。显式 separate worktree 的 assignment 必须在 send 前把相同 write-once body
materialize 到 recipient workspace 的对应 repo-relative locator；recipient 不依赖 shared
checkout 的隐藏 runtime 文件。

### 3.2 固定 metadata 与 correlation

canonical envelope 固定包含并由 script 生成/复制：

- `schema_version=3`
- `protocol_epoch`
- `control_release` object（含 `control_release_id` 与 publishability facts）
- `message_id`
- `direction_id`
- sender/recipient identity 与 native thread ID
- `kind`
- `reply_to`
- body

`control_release` 不是 envelope script 的 Git observation。调用者必须先用
`scripts/hmasd_control_release.py inspect` 生成 exact JSON record，再把该 record 显式交给
envelope CLI；envelope 只校验/复制该 record，不运行 Git，也不调用 release inspector。
record 固定且仅含 `control_release_id, protocol_epoch, head, origin_main, branch,
control_paths, dirty_control_paths, publishable, observed_at`。`control_release_id` 是当前
committed control-path blob set 的 content digest；metadata 同时记录 HEAD、origin/main、
branch、dirty control paths 与 `publishable`。只有 shared
`main` 的 HEAD 已发布到 origin/main 且 control paths clean 时，该 release 才可用于新
ASSIGNMENT、initiating CONTROL_NOTICE 或 REANCHOR；dirty working tree 或单独一个 Git
commit ID 都不能冒充 release。
`scripts/hmasd_control_release.py inspect/verify` 是该事实的唯一机械生成/校验 seam；它
不批准用户行为，也不决定 lifecycle/owner。
RETURN 与 PORTFOLIO_RETURN 必须把 `reply_to` 绑定到触发它的 ASSIGNMENT；
CONTROL_NOTICE 绑定被控制的 message/notice（没有时显式 null）。RETURN 与
PORTFOLIO_RETURN byte-semantically 复制 triggering ASSIGNMENT 的 release；Clerk relay 的
CONTROL_NOTICE 同样复制 initiating notice 的 release。script 校验 direction、反向
endpoints、reply chain、body contract 与 changed-path containment；不验证 Codex 本身。

ASSIGNMENT 的 `context_refs` 是 point-in-time 定位信息，不是 freshness gate；recipient 按 path
读取当前 authority。RETURN/PORTFOLIO_RETURN/CONTROL_NOTICE 不用 assignment-time context SHA 否定合法
mutation 或恢复重读。本地 envelope 文件属于可信协作输入；v3 不建立 body digest、
authentication、tamper archive、不可变消息账本或二次摘要层。RETURN/Portfolio 新产生的
artifact refs 仍按当前 bytes 检查。

header 的 `next` 由 kind/body 机械派生，LLM 不填写：

| kind/body | header `next` |
| --- | --- |
| ASSIGNMENT | `NONE` |
| PORTFOLIO_RETURN | `NONE`；多个 transition 不压缩进 header |
| CONTROL_NOTICE | `NONE` |
| RETURN `REQUEST_EM` | `EM` |
| RETURN `REQUEST_CM` | `CM` |
| RETURN `REQUEST_PORTFOLIO` | `Portfolio` |
| RETURN `REQUEST_USER` | `Root` |
| RETURN `WAIT_RESOURCE` | sender 的同一 manager role |
| RETURN `FAILED` | `failure.responsible_role`；不是合法 role 时 `NONE` |

### 3.3 合法 edges

新 v3 ASSIGNMENT 只有 `Root -> Workflow-Clerk` 的 bounded coordination objective，和
`Workflow-Clerk -> Root/Portfolio/EM/CM` 的 bounded responsibility slice。Portfolio、
EM、CM 不给另一个 participant 创建 ASSIGNMENT。

Root/EM/CM 的工作结果只用 RETURN 给 Clerk；Portfolio global decision 只用
PORTFOLIO_RETURN 给 Clerk。CONTROL_NOTICE 由观察到 authoritative user/control change
的 top-level task 发给 Clerk，再由 Clerk 发给受影响 task；participant 不直接形成新的
peer edge。所有跨 session send 只使用 CLI 输出的 exact recipient thread ID 与 exact
one-line message。

除以上 V3 edges 外的 participant-to-participant forwarding 和 RETURN 转发均非法。

## 4. Body contracts

### 4.1 ASSIGNMENT

ASSIGNMENT body 固定包含：

- `objective`：本 slice 的一个 bounded outcome；
- `context_refs`：recipient 必须读取的 repository-relative path+SHA authority/prompt refs；
- `owned_paths`：可写的 exact path 或目录前缀；
- `effects`：本 slice 允许的 exact external/local Effect；
- `constraints`：resource、Git、review、result-command 与非目标；
- `done_when`：何时必须产生 RETURN，而不是方向 terminal 条件。
- `workspace_mode`：只能是 `shared-main` 或显式 `separate-worktree`。

这些字段的 JSON shape、固定 role context、当前 SHA、默认 RETURN effect/完成条件和
`shared-main` default 由 `assignment-from-brief` 生成。Root/Clerk 只通过 CLI flags 提供
bounded objective、额外 context path、owned path、Effect 与真正 slice-specific 的约束/
完成条件；release 由 script 当前观察或从 validated ingress 复制；不手写完整 body、
control-release 或 SHA。

Portfolio assignment 必须引用 `.codex/prompts/hmasd-portfolio.md`，EM assignment 引用
`.codex/prompts/hmasd-em.md`，CM assignment 引用 `.codex/prompts/hmasd-cm.md`。slice
可以禁止当前 result-bearing command、冻结路径/Effect，但不能用 blanket “no subagent”
删除 manager 的 direct-leaf interface。static CM slice 不使用 Operator，不代表后续
eligible execution slice 没有 Operator。

### 4.2 Participant RETURN

RETURN body 固定包含：

- `status`
- `summary`
- `changed_paths`
- `artifact_refs`
- `next_objective`
- `failure`
- `wait_resource`
- `git_closure`

`status` 只能是以下六个 exact token：

- `REQUEST_EM`
- `REQUEST_CM`
- `REQUEST_PORTFOLIO`
- `REQUEST_USER`
- `WAIT_RESOURCE`
- `FAILED`

不存在 participant terminal status。四个 `REQUEST_*` 必须提供一个非空、bounded
`next_objective`；`failure` 必须为空。`REQUEST_USER` 必须提供 exact material
question/Effect，而不是模糊批准请求。

`WAIT_RESOURCE` 保持 sender 为 standing owner，且 `wait_resource` 固定且仅含
`resource_fingerprint, frozen_command_or_operation, immutable_refs, retry_condition,
earliest_retry_at, direction_id, run_id, heartbeat`。frozen value 必须是 exact argv command
或 immutable operation identity；`immutable_refs` 是 path+SHA refs；heartbeat 固定含唯一
`binding_id` 和返回同一 manager native task 的 `target_thread_id`。这些字段机械表达
resource fingerprint、retry condition、最早 retry time、run/direction identity 与唯一
heartbeat binding；它不创建 next manager 或 Operator，且 `failure` 必须为空。
`REQUEST_*`、`FAILED` 或其他非 wait return 的 `wait_resource` 必须为 null，不能把 wait
facts 藏进 summary/next_objective。

`FAILED` 必须提供 failure；当 `responsible_role` 可路由时，`next_objective` 给出 bounded
recovery outcome。failure 固定且仅含以下字段：

- `scope`
- `code`
- `fingerprint`
- `responsible_role`
- `retryable`
- `attempt`
- `max_attempts`
- `summary`

`scope` 只能是 `project / direction / feature / effect`；`code` 是非空稳定 token，本
协议不冻结全量 code enum。`attempt` 从 1 开始，`max_attempts` 必须在 1..3。fingerprint
绑定 scope/code 与原 assignment 中的 immutable failing inputs，排除 summary、时间和
attempt；不得通过改写 prose 规避计数。相同 fingerprint 只有在 `retryable=true` 且
`attempt < max_attempts` 时可重试。达到上限后 Clerk 不再发同一 retry，而按
`responsible_role` 路由一次明确处理。合法 responsible role 是 `Root`、
`Workflow-Clerk`、`Portfolio`、`EM` 或 `CM`；其他值令 header `next=NONE` 并成为机械
defect。外部 Effect 的 UNKNOWN code 必须
`retryable=false`、observe-only，任何 retry budget 都不授权 resend。code 经大小写与
separator canonicalization 后只要包含 exact `UNKNOWN` token（包括
`COMMITMENT_UNKNOWN`、`UNKNOWN_COMMITMENT` 与 `PUSH_OUTCOME_UNKNOWN`）就受此约束；
failure-history 永远不得把它报告为 retry eligible。

script 检查 `changed_paths` 全部位于原 ASSIGNMENT `owned_paths`，并只校验调用者提供的
structured `git_closure`，不运行 Git、不解析 summary。`changed_paths=[]` 时 closure 必须
exact 为 `{kind: NO_CHANGES}`；非空时必须 exact 为 `{kind: PUBLISHED, branch,
commit_sha, remote, ref, push_outcome: SUCCEEDED}`，其中 commit SHA 是 full Git SHA。
closure 由 `scripts/hmasd_direction_git.py` 在 envelope 外生成。

direction Git CLI 不读取或解析 session envelope；调用者给它一个冻结的 Git-specific
input JSON，固定且仅含 `schema_version, assignment_message_id, assignment_locator,
direction_id, recipient_identity, workspace_mode, owned_paths, commit_subject`。它仍只 stage
exact requested owned paths；push 穿过 external Effect boundary 后，失败或未知只允许
`observe-push`，不得 resend。`no-changes` 对全部 frozen owned paths 作 observation 并仅在
确实没有 Git-visible change 时产生 exact `NO_CHANGES` closure。

### 4.3 PORTFOLIO_RETURN

Portfolio global ASSIGNMENT 与 PORTFOLIO_RETURN 的 header 固定使用
`direction=portfolio`；这个 transport correlation 不缩小其全局 considered scope。

Portfolio global wake 的 body 固定包含 `registry_revision`、`snapshot_digest`、`summary`、
`decision_ref`、`artifact_refs`、`failure`，以及恰好三个语义决策区块：

- `considered[]`
- `transitions[]`
- `capacity`

`registry_revision` 是本 wake 成功持久化后的 exact registry revision；
`snapshot_digest` 绑定 Portfolio 实际比较的完整 global input，而不是单方向 registry
bytes（后者由 decision 的 `expected_registry_sha256` 单独绑定）。
`decision_ref` exact 为 `{path, sha256}`。成功 RETURN 必须指向
`docs/research/portfolio/decisions/<decision_id>.json` 的 committed apply authority；body 的
summary/snapshot/considered/transitions/capacity 必须与 authority 完全一致，registry revision、
transition lifecycle、ACTIVE set 与 lifecycle decision refs 必须与当前 committed registry
一致。envelope 不复制 Portfolio 规则，而调用 `hmasd_state.validate_portfolio_return` 的
read-only seam。

`considered[]` 覆盖 assignment snapshot 的全部方向及本 wake 的 proposed candidate。
每项 exact 为 `{direction_id, disposition, priority, summary, evidence_refs}`；direction ID
不得重复，priority 必须可全局比较，evidence refs 必须 hash-bound。没有 transition 的
方向仍须记录 disposition/rationale。Clerk 不能预先把 global input 缩成一个方向，
Portfolio 也不能只返回获选项而隐藏未选 capacity trade-off。

`transitions[]` 只记录 actual material outcome，包括 lifecycle 不变但 next owner 变化的
`ACTIVE -> ACTIVE`。每项 exact 为 `{direction_id, lifecycle, summary, next_role,
next_objective, reactivation_condition, new_direction}`；prior lifecycle 由
`snapshot_digest` 绑定的 registry snapshot 唯一确定：

- `REGISTERED -> ACTIVE`、`PARKED -> ACTIVE` 或 `ACTIVE -> ACTIVE` 必须选择 EM 或 CM
  和 bounded objective，`reactivation_condition=null`；new ACTIVE direction 必须选择 EM；
- `* -> PARKED` 必须 `next_role=Root`，`next_objective` 是 exact user question，且
  `reactivation_condition` 非空；
- `* -> CLOSED` 或 `* -> REGISTERED` 必须让 `next_role`、`next_objective` 与
  `reactivation_condition` 全为 null；CLOSED `summary` 就是 durable terminal reason；
- existing direction 的 `new_direction=null`；新 direction 的 definition fixed 为
  `{title, abbreviation, scientific_question, dependencies, base_sha}`；
- lifecycle/责任均未改变的 candidate 只留在 considered，不伪造 transition。

`capacity` exact 为 `{active_limit, active_before, active_after, active_direction_ids,
resource_constraints, unused_capacity_reason}`。before/after 与 apply 前后 registry 必须
一致，active_after 不超过 limit，IDs 必须等于结果中的 ACTIVE set。关闭释放 capacity
时，同一次 wake 必须重新 consider 全局 cohort；若 active_after 低于 limit，
`unused_capacity_reason` 必须非空并解释为何空闲容量优于任一候选。

`failure` 正常为 null；Portfolio 本身或 `portfolio-apply` 失败时仍只能发送
PORTFOLIO_RETURN，不能绕到普通 RETURN。此时必须填写同一八字段 typed failure，仍提供
完整 `considered[]`，`transitions[]` 只列已成功 durable 持久化的变化，`capacity` 反映
失败后 registry 的真实 committed 状态。未提交或已回滚的 proposed transition 不得写入。
atomic `portfolio-apply` 失败时 transitions 因而必须为空；`decision_ref` 可以指向原
attempted decision input 而不能冒充 committed authority。validator 仍以 current registry
和 decision 中的 proposed cohort 校验完整 considered、evidence、capacity 与 snapshot。
Clerk 只按 `failure.responsible_role` 路由，header `next` 仍为 `NONE`。

Clerk 在任何 native send 前先校验完整 `considered/transitions/capacity` 和 registry
revision，再在同一事件 turn 展开所有独立 ready transition。一个 transition 的 FAILED
不删除、延迟或改写其他 ready transition。

### 4.4 新方向 atomic apply

Portfolio 对新方向只能调用：

```text
python scripts/hmasd_state.py portfolio-apply ...
```

`portfolio-apply` decision 固定携带 `expected_registry_revision`、
`expected_registry_sha256`（CAS 当前 registry bytes）、`proposed_candidates`（exact
`[{direction_id}]`）与 `snapshot_digest`（全局 snapshot provenance）。snapshot digest
绑定 sorted proposed direction identities，因此 declined proposal 即使没有 transition，
也仍是本次 considered input 的可验证部分。decision 在一个 logical transaction 中：

1. 校验 direction ID、path、abbreviation、logical identity、依赖与 capacity 唯一性；
2. 写 decision authority；
3. 如有新方向，staging 完整 `DIRECTION.md`、research state、engineering state、
   external-review index 与 registry entry；
4. 应用全部 transitions/capacity；
5. 最后 CAS registry，并验证所有 refs/postconditions。

任一步失败必须回滚 staged changes；registry 与 candidate scaffold 要么全部可见且一致，
要么保持原 revision，reserved direction root 不得 partial 存在。PORTFOLIO_RETURN 只引用
一次成功 apply 的 revision/decision authority。Clerk 在 apply 成功前不得为 proposed
direction 创建 task 或 send；`REGISTERED -> ACTIVE` 成功后必须在同一 Clerk event turn
按需创建/复用 EM 并发送 ASSIGNMENT。

### 4.5 CONTROL_NOTICE

`CONTROL_NOTICE.action` 只能是：

- `PAUSE`
- `RESUME`
- `OVERRIDE`
- `CANCEL`
- `REANCHOR`

body 固定包含 `action`、`reason`、`target_identity` 与 `scope`；`scope` 标明
direction、authoritative provenance 和被控制的 message/assignment；至少包含 exact
`direction_id` 与 `affected_locator`（没有 affected message 时显式 null）。envelope 的
`reply_to` 必须等于 affected locator 中的 message ID。initiating notice 只能由 participant
发给 Clerk；Clerk relay 必须 reply to 该 initiating notice、复制 action/target/release，并
发给 exact target。除 hop-local `affected_locator` 外，relay 必须 byte-semantically 复制
initiating action、reason、target 与全部 scope semantics。任何 direct participant peer edge
非法。PAUSE/CANCEL 必须有 affected locator；RESUME 必须关联同 direction/target 的 validated
PAUSE 或 CANCEL notice；OVERRIDE scope 必须包含 exact
`replacement:{objective,effects[]}`，同时冻结 replacement objective 与 Effect boundary。
REANCHOR 的 scope
必须给 `expected_control_release_id`。PAUSE/CANCEL 立即停止新的 launch/send，但不能假装取消已经发生的
外部 Effect；未知 commitment 继续 observe 到可判定状态。OVERRIDE 必须给 exact replacement
objective/Effect boundary。RESUME 必须关联原 pause/cancel facts。

CONTROL_NOTICE 只改变 transport/control expectation，不直接写 lifecycle 或领域 phase。
如果用户动作意味着长期 PARKED/CLOSED，Clerk 另行请求 Portfolio durable decision。

每个 envelope 的 `control_release` 是固定 metadata，不是一种 kind/body action。同一
`protocol_epoch` 内 release 更新时，Clerk 只在 recipient turn boundary 发送
`REANCHOR`，带新 committed release 和必须重读的 authority refs；recipient 的下一条
v3 message 必须携带新 release，才算 adoption 可见。REANCHOR 不改变 lifecycle。
`protocol_epoch` 固定为 `3`；其他 epoch 均为无效输入。

## 5. 唯一转换表

Clerk 只按 validated typed fields 执行下表，不从 summary、方向名词或 Dashboard prose
推导下一角色：

| validated event | Clerk action | stable owner outcome |
| --- | --- | --- |
| RETURN `REQUEST_EM` | create/reuse same-direction EM/gN；send bounded ASSIGNMENT | EM |
| RETURN `REQUEST_CM` | create/reuse same-direction CM/gN；send bounded ASSIGNMENT | CM |
| RETURN `REQUEST_PORTFOLIO` | send one global Portfolio ASSIGNMENT with full cohort/capacity refs | Portfolio |
| RETURN `REQUEST_USER` | send exact material question to Root/user | User/Root |
| RETURN `WAIT_RESOURCE` | retain same manager assignment；create/update its one heartbeat | same sender |
| RETURN `FAILED` retry eligible | redeliver a bounded repair to `responsible_role` with incremented attempt | responsible role |
| RETURN `FAILED` exhausted/nonretryable | no same-fingerprint retry；route explicit decision/facts to responsible role | responsible role or visible defect |
| PORTFOLIO_RETURN with `failure` | route typed failure to its responsible role；continue every successfully persisted ready transition | responsible role plus independent transition owners |
| PORTFOLIO_RETURN active transition | create/reuse transition EM/CM and send every ready assignment | transition role |
| PORTFOLIO_RETURN parked transition | native deliver exact question/condition；ensure no owner heartbeat | User/Root |
| PORTFOLIO_RETURN closed transition | emit terminal summary；ensure no owner/heartbeat/active experiment | terminal |
| CONTROL_NOTICE | apply only named control action；correlate affected delivery | target/control owner |

Portfolio/EM/CM 不互相 send；Clerk 只执行明确 transition。缺 source、test、CLI、candidate、
dossier、manifest、prepare 或 Operator 是 CM objective；科研对象、判据、比较或 evidence
interpretation 是 EM objective；跨方向 priority/investment/lifecycle/capacity 是 Portfolio；
用户材料、user-owned irreversible Effect、shared-core、identity conflict 或不可机械解释
的协议矛盾才到 Root。protocol question 只上报 exact facts，不把方向工作转给 Root。

## 6. Clerk event algorithm

每个 Clerk event turn 必须按以下顺序执行：

1. **Ingress**：对 exact native delegation input 执行 v3 `read-message`；不把 leaf prose、
   locator 文件或历史 cache 当事件。
2. **Topology**：用 fresh native task list/read 构造只存在于本 turn 的最小 snapshot：
   exact task IDs、identity/generation/epoch/status，以及 native history 中的 current v3
   correlations。不得落盘为第二 registry。
3. **Validate**：校验 protocol epoch/control release、reply chain、direction、role、
   owned paths、failure attempt、Portfolio revision/capacity。机械错误只报告 exact field；
   不新增批准 gate。
4. **Route**：按第 5 节处理所有 ready events。正交方向可并行准备，但必须在结束前
   完成每个独立 native send；普通 event turn 不调用长期 wait。
5. **Project**：可把本次 fresh observations 写入 ignored、只读
   `owner_stage`/Dashboard projection；它不是 authority 或 delivery receipt。
6. **Bounded final drain**：final 前重新 native read 当前 Clerk history，以本 turn 内存
   set 排除已处理 message IDs，读取所有新到达 exact v3 lines并完成其 ready sends。重复
   fresh pass 直到一次没有新 message，或到达 control release 规定的小固定上限；若到达
   上限仍有输入，继续同一 Clerk task/heartbeat，不把未处理输入静默留在 completed turn。

final drain 不创建 durable inbox、ack、cursor、receipt 或消费 registry。native history
仍是 delivery truth。新的消息在 drain 后到达，由 native delivery 或只属于 Clerk 的
transport-recovery heartbeat 唤醒；方向 resource heartbeat 永远回到其 manager。

若 exact native list/read/send/create 能力不可用，Clerk 必须停止受影响动作并向用户报告
capability gap。它不得从本地文件、数据库或私有 history parser 推导 native topology。

## 7. Recovery 与 retry

recovery 只修 transport/topology，不重做 domain decision：

- ASSIGNMENT 已在 native history，owner stopped/idle 且没有 correlated RETURN：继续
  exact same task，重用同一 assignment/message ID；先读取其 history/artifacts，禁止重做
  已有 material work。
- body 文件存在但 native line 不在 recipient history：这只是未送达。sender 在确认没有
  unknown send 后原生发送；未知 send 只 observe。
- RETURN 已送达但没有 next ASSIGNMENT/terminal/control summary：Clerk 读取同一 RETURN
  并按表补齐；不能要求 participant 生成第二 RETURN。
- ACTIVE final drain 后没有 owner/WAIT_RESOURCE/ready send：标为 scoped workflow defect，
  由 Clerk修复原 correlation；不能改成 PARKED、CLOSED 或 local terminal。
- current epoch 找不到 next manager：按需创建一个 visible standing task；找到多个则
  identity conflict 到 Root，不任选其一。
- 同 failure fingerprint 只能沿 validated native correlation 把 attempt 增到
  `max_attempts<=3`。新 prose、task generation 或 heartbeat 不重置计数；material inputs
  真正改变才形成新 fingerprint。

Clerk 可把本次从 native history 观察到的、按 oldest-to-newest 排列的 correlated FAILED
RETURN locators 交给纯函数式 `hmasd_session_envelope.py failure-history --return ...`。
validator 要求 attempt 恰为 `1..N`、每个 locator/message 恰出现一次、fingerprint 的
immutable facts 与 `max_attempts` 稳定，并报告 retry eligibility/exhaustion；它不持久化
registry、cursor 或第二状态机。

scripts 可以纯函数式生成 schema/correlation/recovery action，但不得创建、等待、归档
task，不得解释 direction prose，不得维护 retry FSM 或权限状态。

## 8. EM、CM 与 Operator completion

EM 与 CM 只在各自 standing task 内创建一层 bounded direct leaf；leaf 不再 delegate，
不持有或联系其他 top-level task，只把 typed result final return 给 spawning manager。
manager 仍是 durable writer、判断者和对 Clerk 的唯一 RETURN sender。

### Role-local instrument request/result v1

instrument request/result 是 EM 或 CM 与其 direct leaf 之间的 role-local contract，
不是新的 envelope kind，也不进入 Clerk transport、Portfolio lifecycle 或 research/
engineering state schema。manager 先按证据问题类型读取
`configs/scientific-capabilities-v1.toml`，只选择 owner/leaf role 匹配的最小充分
`active` capability；skill 必须由 manager 显式调用，不能依赖隐式触发。

manager 派 leaf 前冻结一个 bounded request，至少绑定：`direction_id`、`evidence_id`、
owner/producer role、capability/skill/tool/environment 的版本与 hash ref、objective、
hash-bound input refs、judgment criteria、适用 constraints、Effect、argv 数组、cwd、
platform、raw artifact root 和 requested output。command/API 还必须绑定 catalog 中
repo-contained dedicated entrypoint 的 content ref；manual invocation 的 entrypoint ref
为 null。shell 字符串不是 argv，未声明的
external Effect 不得发生。能力不可用时报告 `UNAVAILABLE`，不得安装、替换 provider
或扩大 Effect。

leaf 只执行这一项冻结操作并 final return typed observation。结果必须绑定 request
identity，报告 `OBSERVED | FAILED | UNAVAILABLE`、实际 invocation/platform、artifact
locator 与 SHA、core observations、assumptions、limitations 和 failure information；
typed observation 必须符合
`scripts/schemas/hmasd_instrument_observation_v1.schema.json`；
不得用 `PASS` 表示 scientific acceptance，也不得写 direction authority、sidecar 或
lifecycle。raw output 只留在
`temp/directions/<direction_id>/{exp,test}/instruments/<evidence_id>/`。

manager 是唯一 durable writer：EM/CM 检查 typed observation，先在对应 instrument
temp root 序列化 sidecar candidate；candidate 内的 `sidecar_path` 必须是
`docs/research/candidates/<direction_id>/evidence/<evidence_id>.json`。manager 用
`scripts/hmasd_science_capabilities.py validate-evidence --path ... --direction-id ...`
fail closed 校验 repo-contained input/target/artifact SHA、capability/Effect/invocation/tool
binding、dedicated entrypoint content ref、typed observation identity，以及 candidate、raw
artifact 与 intended sidecar parent 的 resolved exact root。CLI 只读并返回 candidate
`content_sha256`；校验成功后 manager 在写入前再次确认 exact sidecar parent，才把
完全相同的 bytes 原子写入 `sidecar_path`，并核对最终 SHA。sidecar 必须
解释该观测如何改变或约束具体 scientific claim 或 engineering judgment；长期 authority
只引用并解释 sidecar，不复制 raw output。leaf 工具成功本身没有 acceptance、routing
或 approval 语义。

Portfolio 只消费足以改变 investment/lifecycle 判断的 manager-authored evidence 摘要，
不直接调用 capability。Clerk 不读 catalog、不解释 evidence，也不因工具结果改变路由。
普通检索、静态数学验证和分析 probe 不自动成为 Operator 工作；任何 result-bearing
command 仍须遵守 CM prepare/唯一 Experiment Operator 路径。

EM 的 role-local leaf interfaces 固定为：

- **Research Scout**：检索一个冻结问题的 primary evidence、方法与反证边界，返回可核对
  refs/facts，不作最终方向判断；
- **Research Innovator**：提出 bounded mechanism、comparator 与 discriminator，显式列出
  可区分预测和失败条件；
- **Research Principles Analyst**：审查学习动力学、因果归因、数值/优化原则与跨任务可迁移
  约束；
- **Research Critic**：对一个冻结 claim/object 作独立 constructive 或 adversarial Pro
  review，不能同时充当被审对象作者；
- **Agentify external transport**：只传输一次 bounded external research consultation，
  保留 provider/effect provenance 与 at-most-once/UNKNOWN 语义，不成为 durable writer。

结论性或 direction-changing scientific object 的接受顺序固定为：先形成 constructive
case；再做 constructive Pro review；EM 根据 review 修订冻结对象；最后由未参与该对象构造
或第一次 review 的独立 Research Critic 做 adversarial Pro review。只有修订后对象通过该
独立 adversarial review，EM 才能把结论写入 authority 或请求 material lifecycle/engineering
变化。普通事实检索或不改变结论的机械更新不伪装成这条 review sequence。

CM 的 role-local leaf interfaces 固定为：

- **Implementer**：拥有一个 exact path/contract 的非机械实现与相应 focused tests；不改
  assignment 外路径，不回退其他 session work；
- **Reviewer**：在 fixed diff/base 上独立检查 repository Standards 与 accepted Spec；高影响
  production/protocol/scientific/numerical/RNG/checkpoint 代码在 CM 接受前必须经过 Reviewer；
- **Verifier**：对一个冻结行为或 result command 做 focused runtime verification，报告
  command、环境、observations 与 limits，不顺带取得实现 ownership；
- **Experiment Operator**：从 launch 到 terminal observation 只运行一个 exact frozen
  result-bearing command，保存 payload/result/stdout/stderr/checkpoint，terminal result 只回 CM。

非机械 implementation 必须交 Implementer；纯格式、已完全机械的生成或 manager 自身小型
transport edit 不强制创建 leaf。Reviewer/Verifier evidence 是 risk-proportionate acceptance
evidence，不是新的 authority 或用户 approval gate。

EM 写入 research authority 后，在同一 turn 生成并 native send RETURN。若科研 object 已
接受但实现不存在，返回 `REQUEST_CM`；若 evidence 需要新科研解释，返回 `REQUEST_EM`；
若需要 investment/lifecycle/capacity 判断，返回 `REQUEST_PORTFOLIO`。局部 scientific
completion 不能省略 next responsibility。

CM 对 source/test/CLI/instrumentation/batching/dossier/manifest/prepare/Git 负责。static
dossier 不调用 `hmasd_run.py`；runtime prepare 只生成 manifest/preflight 并做 resource
admission。只有 PREPARED、authority 覆盖、Effect 合法的 exact result command 才交一个
唯一 Operator。

Operator 从 launch 到 terminal observation 只持有一个冻结 command，不修改 command、
parameters、code SHA 或 authority，不再 spawn。它必须给 CM 一个 typed terminal result，
绑定 assignment/run/command、manifest、exit/terminal reason 与 evidence refs。Operator
不得给 Clerk/EM/Portfolio发消息。CM 对 terminal result 做工程/数值完整性解释，再用六个
RETURN status 之一把 next responsibility 交 Clerk。

authority 已覆盖、memory-safe、没有新 external/shared-core semantic change 且预计不
超过 7200 秒的本地 PREPARED command 不需要仅因“是真实科学执行”请求用户；超过
7200 秒的 exact command 必须先有 performance sanity review 和用户批准。

## 9. Memory admission 与 heartbeat

`hmasd_run.py prepare` 必须在创建 reserved output root 前评估内存。不安全计划先缩小、
batch 或 shard；refusal 保持 root 不存在。历史 partial root 只能由 run CLI 对以下 exact
安全形状机械回收：direction/run/preflight identity 匹配、`memory_safe=false`、无
manifest/log/checkpoint/artifact，且仅含允许的空目录。额外文件、非空目录、symlink 或
identity mismatch 一律拒绝。

WAIT_RESOURCE 的 heartbeat 绑定 exact direction/run/fingerprint、frozen retry 与当前
manager native task；每个 direction/run 至多一个。prepare 默认回 CM，不得放在 Root 或
Clerk。heartbeat 只唤醒同 task 重新观察/尝试，不修改 estimate/command/code SHA，不创建
Operator。PREPARED 后先 native send correlated RETURN，再取消 heartbeat。

## 10. Dashboard provenance

Dashboard 只监听 `127.0.0.1`，所有 mutation method 返回 read-only failure。它只投影：

- Portfolio registry/lifecycle 与 decision refs；
- research/engineering state；
- run manifest/terminal evidence；
- Clerk 从 fresh native list/read 产生的 `owner_stage` 与 `delivery_state` observation。

每个 displayed control fact 必须带 source path 或 native thread/message ID、
`protocol_epoch`、`control_release`、真实 observed time 与 stale/unknown flag。仅重新请求
页面不能刷新 observation time。缺 correlation 时显示 `UNKNOWN/UNOBSERVED`，不得从
idle、文件存在或 runtime task map 猜 transport gap。

Dashboard 不写 authority、不 native send/create/wait、不执行 recovery、不持有 owner，
也不生成第二 task registry。Dashboard 停止、projection 删除或陈旧不改变 lifecycle、
owner、delivery 或 heartbeat。

## 11. Shared workspace、Git 与 paths

`C:/Projects/HMASD` 是 shared checkout 且永久保持 `main`。Root、Clerk、Portfolio、EM、
CM 不得在这里运行 `git switch` 或 `git checkout`。方向 branch 只允许存在于 ASSIGNMENT
明确绑定的 separate worktree；否则 workspace mode 是 shared main。

owner 只能修改/stage ASSIGNMENT `owned_paths` 内由本 slice 产生的 exact paths，不得
回退、stage 或提交其他 session 的 dirty/staged files。parallel domain work 可以并行，
但 shared Git index mutation 必须串行；不能保证时 assignment 必须使用 explicit worktree。
有 Git-visible 改动的正常 top-level owner 在 RETURN 前 commit/push exact paths，并报告
branch、完整 SHA、remote/ref 与 push result。push commitment unknown 时只 observe
remote，不盲目 push；worktree 要么精确回收，要么 RETURN 报 retained path/branch/HEAD/
reason。leaf 和 Root 不代做普通方向 Git closure。

方向运行产物只在 `temp/directions/<id>/{exp,test}/`；source 在
`experiments/candidates/`，tests 在 `tests/experiments/candidates/`，durable science 在
`docs/research/candidates/<id>/`。共享 C++ backend、神经网络基座或跨方向核心修改前，
必须向用户说明 exact paths、目标、非目标和 scientific/numerical/RNG/checkpoint/bit
identity/Effect 影响并取得确认。

## 12. 必须闭合的静默点

以下情形不得依靠模型记忆或 Dashboard 猜测：

1. participant 已写 durable authority/commit、尚未 RETURN：恢复同 task，读取既有
   evidence 后补同一 assignment 的 RETURN，不重做写入。
2. Portfolio `portfolio-apply` 已成功、尚未 PORTFOLIO_RETURN：同一 Portfolio task 引用
   已存在 decision revision 补 RETURN；不得再次 apply。
3. 新 direction 已 ACTIVE：Clerk 同一 event turn 创建/复用 EM 并 native send；不能留下
   ACTIVE/无 owner 窗口到 final。
4. valid message 在 Clerk 处理另一个 event 时到达：bounded final drain 必须消费。
5. 同 direction 两个 assignments 将要发送：Clerk 在 send 前按 native correlation
   serialize；不得交给 CM/EM 自行猜 stale。
6. user 直接 PAUSE/OVERRIDE/CANCEL participant：该 task 发 CONTROL_NOTICE，Clerk 停止
   被控制 assignment 的 redelivery；已启动 Effect 仍按 at-most-once observe。
7. Operator terminal：typed result 先回 CM；CM interpretation/RETURN 不能由 Clerk 或
   run manifest 自动替代。
8. control release 变化：在 V3 内先 REANCHOR；task 不能因 cwd 指向新 main 就假装已经
   采用新 release。
9. Dashboard 复用 stale observation：保持 stale，不得只改时间。
10. native task API 不可用：显式 capability failure；不得启用本地替代 task plane。

## 13. 明确非职责

`hmasd_session_envelope.py` 只负责 v3 canonical body/header、correlation、endpoint、
status、failure attempt 和 path containment；它不创建/等待 task、不决定 next role、不
维护 lifecycle、task registry、inbox、receipt 或 retry FSM，也不解析 native task history。

`hmasd_state.py portfolio-apply` 只机械应用 Portfolio 已决定的 authority/scaffold/
registry CAS；它不作 Portfolio 判断或派发 task。`hmasd_run.py` 继续独占实验 command/
process/manifest 事实；session protocol 不重写实验运行器。

除本文列出的 native task plane、V3 envelope、state、run、Operator 和 Dashboard projection
seams 外，不得增加第二 task plane、隐藏 manager、私有 inbox/receipt 或替代调度器。
