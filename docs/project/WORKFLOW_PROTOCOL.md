# HMASD native Codex workflow

Workflow revision: 2026-08-28.7

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

Top-level task 的 model policy 是用户确认的目标配置，不是从历史 task 推断的事实：

| Role | Model | Thinking |
| --- | --- | --- |
| Portfolio | `gpt-5.6-sol` | `max` |
| EM | `gpt-5.6-sol` | `max` |
| CM | `gpt-5.6-sol` | `high` |
| Root | user-selected | user-selected |

创建 Portfolio、EM、CM 时，native `create_thread` 必须显式传入对应 `model` 与 `thinking`，
不得继承 Desktop 默认模型。API 接受这些字段只证明请求配置被接受；没有 runtime 回显时不得
宣称 resolved model 已验证。Leaf 的模型和 reasoning 只来自对应 `.codex/agents/*.toml`。

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
<the fixed fields owned by this role from section 2.2>
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
  替代解释、共享依赖、下一 discriminator、粗粒度成本/时间以及 exact `Recommendation`。

负科学结果在 assignment 已按合同完成时使用 `Outcome: DONE`；`FAILED` 只表示该 WORK 没有
完成。上述动作是 RESULT 中的判断文字，不增加 lifecycle 或 RETURN outcome。

### 2.2 Field namespaces

`Outcome:` 是所有 top-level task 共用且唯一的 assignment-liveness 字段：

- `DONE`：当前 WORK 的 acceptance 已回答，包括得到负科学结果或无变化结果；
- `WAITING`：同一 WORK 仍被 callee 持有，正在等待明确 reentry condition；
- `FAILED`：当前 WORK 已终局结束，但 acceptance 未完成；
- `CANCELLED`：只在收到合法 `[CONTROL] Action: CANCEL` 且已提交 Effect 已观察到安全终态后使用。

它不表达科学正负、工程验证、provider send、方向质量或 lifecycle。每个角色在 RESULT 中只写
自己的固定字段；不得复制或代填其他 owner 的字段。

| Owner | Fixed RESULT fields | Scope |
| --- | --- | --- |
| Root | `Root status: IN_PROGRESS | CHANGED | UNCHANGED | BLOCKED`; `Integration status: IN_PROGRESS | INTEGRATED | NOT_INTEGRATED | NOT_APPLICABLE` | shared-core 与跨分支集成 |
| Portfolio | `Portfolio action: NONE | ACTIVATE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Capacity action: KEEP | SET <n>` | lifecycle、priority、capacity 与跨方向投资 |
| EM | `Scientific status: IN_PROGRESS | SYNTHESIZED | NO_MATERIAL_INSIGHT | NOT_REACHED`; `Decision impact: <text or NONE>`; `Recommendation: NONE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Pro Innovator: <transport state>`; `Pro Convergence: <transport state>` | 科学综合、claim ceiling、discriminator 与对 Portfolio 的建议 |
| CM | `Engineering status: IN_PROGRESS | IMPLEMENTED | UNCHANGED | BLOCKED | NOT_REACHED`; `Observation status: IN_PROGRESS | OBSERVED | NOT_OBSERVED | NOT_REQUIRED`; `Verification status: IN_PROGRESS | SATISFIED | UNSATISFIED | NOT_RUN`; `Commit: <sha or NONE>` | 实现、工程验证与直接 observation |

Portfolio action 是唯一能改变 `PORTFOLIO.md` lifecycle 的字段；EM Recommendation 只是建议。
CM Verification status 只描述冻结工程检查，不是 scientific PASS。transport failure 不得推导
Portfolio action、Scientific status、Recommendation 或 lifecycle。

## 3. Native dispatch and liveness

每个 top-level requester：

1. 从 native task list/history 确认自身、目标 task 与当前 authority；
2. 复用一个 exact current-protocol target；仅在不存在时创建，出现两个候选时停止并请用户选择；
3. 自己冻结并发送一条完整 bounded WORK，包括 objective、paths、Effects、acceptance、refs 与
   自己的 Return task ID；
4. callee 在同一 task 完成、等待、失败或取消，并把 RESULT 直接返回 requester；
5. requester 解释结果并决定停止、继续同一 callee，或向相邻角色发送一条新的完整 WORK。

每个 top-level target 同时最多持有一个 unfinished inbound WORK。该 WORK 的 Return task 在
终结前不可改变；native target 为 `ACTIVE`、`WAITING` 或被 PAUSE 时，任何 requester 都不得发送新 WORK。
只有 terminal `DONE | FAILED | CANCELLED` RESULT 释放 target。用户需要替换目标时也先 CANCEL，
待 external commitment 可判定且收到 CANCELLED RESULT 后，再发送一条完整的新 WORK。

`DONE` 只表示当前 WORK 完成，不自动产生 successor。`WAITING` 必须给出具体 Reentry，并仍由
callee 持有；条件满足后由同一 task 继续同一 WORK，不得用新 WORK 恢复。Requester 或用户可以
用 RESUME 唤醒，或在用户要求自动复查时使用 Codex 原生 heartbeat。`FAILED` 不自动 retry。
Stopped/idle 且当前 WORK 尚未完成时继续同一 task，不创建替代者。

Portfolio 可以在一个当前比较性 WORK 内向多个不同、idle 的 direction EM 并行发送
direction-specific WORK。所有已发送 EM 必须自然 terminal，Portfolio 才能向自己的 Return task
返回 terminal RESULT。只有收到用户对本轮的明确 `[CONTROL] Action: CANCEL` 时，Portfolio 才
逐一转达该 CONTROL 并等待每个 EM terminal；Portfolio 不得自行 CANCEL 子 WORK 来释放 join。
忙碌 EM 不得被覆盖或用替代 task 绕过；其 unavailable/WAITING 事实必须保留在比较结果中。该
fan-out 和 join 由 native task history/status 承担，不写本地 batch、queue 或 task registry。

纯 transport failure 时保持同一 WORK 为 WAITING，并保留 exact reentry。Portfolio 可以把自己
的 inbound WORK 同样报告为 WAITING，但不得把 provider/transport 事实解释为方向 PARK/CLOSE，
也不得仅为释放 Portfolio join 而 CANCEL 子 WORK。只有用户明确 CONTROL CANCEL 才产生
CANCELLED；之后是否改变方向 lifecycle 仍是 Portfolio 的独立投资判断。

Participant 可以为完成当前 acceptance 向另一个 idle 相邻角色发送 bounded downstream WORK，
但不得在自己的 inbound WORK 终结前向当前 Return task 反向发送新 WORK。任何由本轮决定产生的
successor 都先返回 terminal RESULT，再确认 target 已释放，最后以独立完整 WORK 发送。

CONTROL 动作只有以下语义：PAUSE 保留当前 WORK 并停止新的 launch/send；RESUME 只继续同一个
PAUSED 或 WAITING WORK；CANCEL 停止新的 Effect，已提交或 commitment unknown 的 Effect 继续
观察到终态，然后写必要的 `TERMINAL_GAP` milestone snapshot（记录用户取消事实）、返回
CANCELLED RESULT 并释放 target。
CONTROL 不携带替代 objective；新目标一律使用释放后的完整 WORK。

所有 participant 都不验证身份、不维护 attempt/retry ledger、owner cache、cursor、receipt、
release adoption 或本地路由表，也不常驻轮询。Native list/read/create/send 不可用时停止受影响
动作并报告，不从本地文件或数据库重建 topology。

### 3.1 Complete direction loop

正常完整链路为 `Portfolio → EM → CM → EM → Portfolio`：

1. Portfolio 作出 `ACTIVATE | CONTINUE | NARROW` 等投资动作、更新 current table，并直接向
   direction EM 发送科研 WORK；
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

共同字段为 `direction, role, revision, updated_at, milestone, snapshot_state, completed_summary, refs,
blockers, reentry_condition, next_action`。EM 另有 `claim_ceiling, next_discriminator,
research_cycle`；CM 另有 `worktree, branch, changed_paths, verification_summary, run`。

EM milestones：`SCOPE_FROZEN`、`SYNTHESIS_READY`、`REVIEW_RESOLVED`、`HANDOFF_READY`。
CM milestones：`SCOPE_FROZEN`、`CANDIDATE_READY`、`REVIEW_RESOLVED`、
`RUN_OR_HANDOFF_READY`。`snapshot_state` 只描述 checkpoint 本身：`WORKING` 表示 milestone 后仍有
in-flight 工作，`WAITING_REENTRY` 表示该 snapshot 等待明确条件，`TERMINAL_GAP` 表示当前 slice
未进入下一 milestone 即已停止，`COMPLETE` 表示该 snapshot 所述 bounded work 已完成。它不是
assignment liveness，不能释放 native target，也不能替代 RESULT `Outcome:`。

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
“未发现新的 decision-relevant observation”。这只是 leaf-local observation；只有 EM 可以将其
映射为自己的 Scientific status。相同模型、prompt 或来源的一致只算搜索覆盖，不算独立科学证据。

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

### 5.2 Leaf result namespaces

Leaf 没有 durable workflow state，也不返回 top-level `[RESULT]`。每个 leaf 的
`developer_instructions` 只定义自己的 observation 字段、输入边界和 stop condition；parent 解释
其含义。Leaf 不得输出 `Outcome:` 或任何 Portfolio/EM/CM owner 字段。

| Leaf | Own final field | Scope only |
| --- | --- | --- |
| General leaf | `Chore status: COMPLETE | PARTIAL | UNAVAILABLE` | assigned chore/lens completion |
| CM Scout | `Surface status: MAPPED | PARTIAL | UNAVAILABLE` | code-surface map |
| Reviewer | `Review status: FINDINGS | NO_FINDINGS | INCOMPLETE` | advisory findings |
| Verifier | `Verification observation: OBSERVED | NOT_OBSERVED | UNAVAILABLE` | one independent probe |
| Experiment Operator | `Run observation: TERMINAL | LAUNCH_FAILED | OBSERVATION_LOST` | exact command terminal fact |
| Research Scout | `Evidence status: FOUND | CONFLICTED | NOT_FOUND | UNAVAILABLE` | source/evidence acquisition |
| Research Critic | `Critique status: OBJECTIONS | NO_MATERIAL_OBJECTION | INCOMPLETE` | adversarial scientific critique |
| External engineering transport | `Engineering transport state: ZERO_SEND_FAILED | COMMITMENT_UNKNOWN | SENT_WAITING | COMPLETE | SENT_UNREADABLE` | provider facts only |
| External Pro transport | `Pro transport state: ZERO_SEND_FAILED | COMMITMENT_UNKNOWN | SENT_WAITING | COMPLETE | SENT_UNREADABLE` | provider facts only |

`NO_FINDINGS` 不是批准，`OBSERVED` 不是 acceptance，`TERMINAL` 不表示 exit code zero，
`FOUND` 不验证 claim，transport `COMPLETE` 也不接受其回答。任何 leaf failure 都先回 spawning
parent，不能自行产生 WAITING/FAILED/CANCELLED、Portfolio action 或 lifecycle 变化。

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
instances，修订不自动重审。State 的 current `research_cycle` 只保存 `label, opened_at,
reason, pro_innovator, pro_convergence`，不保存历史 ledger。两项 transport status 的完备含义为：

| Status | Meaning | Next legal behavior |
| --- | --- | --- |
| `PENDING` | 尚未进入 send-capable call | 可以做无发送 preflight 或由用户 waiver |
| `ZERO_SEND_FAILED` | 明确 provider 未收到请求且未创建 operation；无论 send-capable tool 是否已被调用 | 本地 bounded recovery 用尽后保持 WAITING；恢复时可重新 preflight/send |
| `COMMITMENT_UNKNOWN` | 无法证明 provider 是否收到请求 | 只观察同一 tab/conversation，不发送 |
| `SENT_WAITING` | 已确认发送，回答尚未自然完成 | 使用无发送 wait/observe |
| `COMPLETE` | 自然完成且完整 question/response 已归档 | immutable |
| `SENT_UNREADABLE` | 已确认发送，但回答在 bounded observation 后仍不可归档 | 不重发；等待恢复可读或用户终止 cycle |
| `WAIVED` | 用户对 exact operation 明确豁免，且此前没有未知/已发送 commitment | immutable |

`COMMITMENT_UNKNOWN`、`SENT_WAITING`、`SENT_UNREADABLE` 永远不能回到 zero-send；
`SENT_UNREADABLE` 仅可保持或在回答重新可读后变为 `COMPLETE`。只有 `COMPLETE | WAIVED`
满足该 Pro stage。Unknown commitment 只观察不重发。

存在 `COMMITMENT_UNKNOWN | SENT_WAITING | SENT_UNREADABLE` 的 external operation 时，不得用新
material cycle 覆盖当前 cycle。EM 保留同一 operation locator，并在原 task 中按冻结的观察边界
继续无发送观察；只有它变成 `COMPLETE` 后才能开始新 cycle。用户仍可取消当前 WORK，但取消不
清除该 operation，也不把 transport 事实解释为科学失败、方向取消或 lifecycle 变化。

每个 material cycle 的两次 Pro 调用已获自动授权。以下情况必须回用户：非项目公开材料、
secret/个人数据、provider/账号/付费方式变化、超出两次、unknown send 后考虑新发送、用户暂停
外部 Effect。Transport 在任何 send-capable call 前先完成 bounded non-sending preflight；简单
主页重定向、Pro 控件未刷新或 stale tab 使用最多两个 fresh-tab recovery 后再调用一次普通
`agentify_query`。`agentify_query` 是该 operation 唯一的 send-capable call。它返回 in-progress
时用 `agentify_wait_response` 等待；调用前或调用后，只要工具明确证明 provider 未收到请求且未
创建 operation，就记 `ZERO_SEND_FAILED`；否则异常立即记 `COMMITMENT_UNKNOWN` 并只观察。
`ZERO_SEND_FAILED` 时 EM 保持同一 WORK 为 WAITING。用户可以对尚未未知/发送的 exact operation
明确 waiver。不得用本地 Critic 或其他 provider 静默替代。

External Pro 的 frozen prompt 必须给出 GitHub remote、exact origin-reachable commit 和所需
repository-relative refs，要求 Pro 通过 GitHub connector 读取。代码只作为 mechanism、treatment/
comparator、measurement 与 result-validity 的科学参考，不能把任务降格为一般 code review。
Transport 不上传本地源码、不自行 push；未公开材料或 commit 尚不可远程读取时先返回 parent。

若 observation 或 objection 推翻 frozen scope，EM 结束当前 cycle 并开启新 cycle，不在原
cycle 中重发 Pro。`SCOPE_FROZEN` 同时冻结可能结果及其 claim/Portfolio 含义、共享 baseline、
最大 observation rounds 或资源上限、提前停止条件和 scope-invalidated 条件。没有新的可检验
机制、没有能改变决定的 discriminator、资源边界耗尽，或工程合同已完成但重复 observation
仍无决策信息时，EM 必须降低 claim、返回 `NO_MATERIAL_INSIGHT`/精确 gap，或提出 Portfolio
Recommendation，而不是无限追加实验。Provider/transport/Effect failure 明确排除在此判断之外；
它们只产生对应 transport fact 和同一 WORK 的 WAITING/reentry。

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

`CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF` 是一次性 Portfolio action，不新增
lifecycle。FUSE 先形成新的科学 synthesis question，并明确源方向 `CONTINUE | PARK | CLOSE`；代码或 shared-core 集成仍由 Root
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

`C:/Projects/HMASD` 是 Root 的 primary `main` checkout，不在其中 switch/checkout。Portfolio、
EM、CM 都从已保存的 HMASD project 使用 Codex 原生 `environment: worktree` 创建 top-level task；
需要特定基线时，`startingState` 指向 requester 已核对的 exact existing branch。Codex 原生持有
每个 task 的 worktree、branch、history 与 ready thread ID；方向目录不需要另存为 Desktop
project，也不建立 project/worktree mapping registry。Native worktree 创建失败时才显式 WAITING。

新建 top-level participant 时，`create_thread` 的 initial prompt 本身就是完整 `[WORK]`；不得
先创建空 task 再二次发送。Setup 只返回 client ID 时等待 ready thread ID，不得重建或把 client
ID 当 recipient。旧 archived tasks 不复用。Native worktree 属于该 top-level participant；leaf
不创建 worktree，也不把自己的临时执行面提升为长期 participant。

同一 direction 同时只有一个 Git-visible writer phase，即使 EM 与 CM 位于不同 native task
worktree。EM 向 CM 发送 WORK 前提交自身 owned refs并给出 exact commit；已有 CM task 先将
自己的 branch fast-forward 到该 commit，新建 CM task 则以包含该 commit 的 exact branch 为
starting state。CM terminal RESULT 前 EM 不得 stage/commit；CM 只提交 exact owned paths并返回
known commit/diff，随后 EM 将自己的 branch fast-forward 到 exact CM commit，writer phase 才
回到 EM。任一方向不能 fast-forward 时，当前 participant 停止并向当前 `Return task` 返回
terminal blocker，不得越过 requester 直接联系 Root，也不得 cherry-pick、rebase 或重写历史。
Requester 按既有链路关闭 inbound；Root 只在收到独立 bounded repair WORK 后处理。Leaf 不
commit/push，也不创建 worktree。不同 directions 可以并行；每个新 cycle 以 WORK 指定的 exact
committed baseline 为起点；shared-core 需求也先按当前 Return task 链路关闭再交 Root。

Owner 只修改/stage owned paths并保留其他修改。跨 top-level role handoff 且 refs 有 Git-visible
内容时必须 commit；同一 saved HMASD repository 内的 native-worktree 交接只使用本地 exact
commit，不需要 push。Push 只在用户要求远端同步、跨主机交付或正式方向交付时强制。

用户直接控制 participant 时，该输入已经是 authority，不需要 CONTROL 转发。Requester 可以按
当前 WORK 需要向 affected participant 发送 PAUSE/RESUME；CANCEL 只能由用户直接发送，或由
requester 逐字转达用户对 exact WORK 的明确取消指令。PAUSE/CANCEL 不等于 Portfolio lifecycle
变化。

不兼容任何旧控制层。旧 task、messages、state、scripts、schemas、prompts 或 fixtures 不读取、
不迁移、不翻译；问题一律 fix-forward。
