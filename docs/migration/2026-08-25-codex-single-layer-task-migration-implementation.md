# Codex 单层 Subagent / 顶层 Task 迁移实施计划

## 1. 元数据

- 状态：Codex adapter 已实现并通过本机 focused tests；首轮 peer-task smoke
  已执行，尚未 clean cutover。
- 日期：2026-08-25。
- 行为基线：`omp/workflow@c5dd980158570c8611ae23c8f30623d680f1de0a`。
- 术语：根 `CONTEXT.md`。
- OMP 设计史：
  - `docs/plans/2026-08-24-omp-autonomous-multidirection-research-concept.md`
  - `docs/plans/2026-08-24-omp-autonomous-multidirection-research-implementation.md`
- 当前迁移决策：`docs/migration/CODEX_MIGRATION_RECOMMENDATION.md`。
- 当前实施工作区：直接使用 `omp/workflow`，不再建立隔离对比分支或额外
  worktree；`main` 保持不动。当前变化在用户确认前不 commit/push。

## 2. 完成定义

迁移完成时必须同时成立：

1. Root、Portfolio、EM、CM 是项目中同级、用户可直接进入的顶层 task。
2. 用户与任一顶层 task 的互动保留在该 task 历史中；material 决定同时进入
   对应 durable authority。
3. Root 使用经验证的低成本模型，拥有完整 in-scope operational permissions，
   但不形成 material Portfolio、科学或工程决定。
4. Portfolio 使用 `gpt-5.6-sol` max，按周期或用户互动形成跨方向、lifecycle、
   优先级和 CM 投入决定，并把 Decision Packet 发给 Root 编排。
5. Portfolio 不直接 dispatch/持有 EM 或 CM；Root 负责创建、恢复、通知、等待
   和去重。
6. 每个方向至多有一个可信的当前 `EM-<direction-id>` generation 和一个可信的
   当前 `CM-<direction-id>` generation；CM 的具体工作仍是有界 assignment。
7. 每个顶层 task 内最多一层 direct subagent；完全重启 Codex 后，direct leaf
   再派生必须由 `max_depth = 1` 拒绝。
8. OMP 既有文件路径、writer、logical identity、worktree、branch、temp、run、
   external-review 和 Git contracts 原样保留，只有平台 runtime refs 做适配。
9. Root 重启或 compaction 后能发现和核对现有 peer tasks，不会盲建重复 manager
   或重复 effect。
10. OMP 与 Codex 不会同时拥有同一方向、run、external operation 或 Git
    integration。

## 3. 非目标

本迁移不：

- 修改科学结论、Portfolio 排名或已冻结工程范围；
- 执行新的科学结果命令或 provider live send；
- 重写已经通过 OMP focused tests 的 state/run/worktree/external helper；
- 把 Root 提升为决策者或唯一用户入口；
- 把 Portfolio 降级为只读 Audit；
- 为 peer task 另造一套文件命名、writer 或 assignment ownership；
- 引入 workflow database、event sourcing、常驻模型轮询或第二个控制面；
- 模拟 OMP Advisor/Hub 的内部实现；
- 在 cutover 前删除 OMP 行为基线。

## 4. Target task 与模型

```text
HMASD Root                         low-cost model, operational orchestrator
HMASD Portfolio                    gpt-5.6-sol, max
EM/<direction-id>/g<generation>    gpt-5.6-sol, max
CM/<direction-id>/g<generation>    gpt-5.6-sol, high
```

Root 的确切低成本模型在 capability/cost smoke 后冻结；候选是能够稳定使用跨 task
工具和执行长工作流 instructions 的 Luna 或 Terra。不能仅因 Root 有最高 tool
权限就为其选择最高推理模型。

四类 task 均获得完成其 in-scope 职责所需的最高操作权限。语义限制来自角色
instructions、writer contracts 和用户范围，而不是通过削弱 tool access 迫使角色
遵守。Decision Authority 仍按 `CONTEXT.md` 分离。

## 5. Target Codex 文件布局

```text
AGENTS.md                                  # 硬边界、task authority 和 OMP 文件合同
.codex/
├── config.toml                            # multi-agent + max_depth=1
├── agents/                                # main 注册的 18 个角色配置
│   ├── hmasd-code-project-manager.toml
│   ├── hmasd-independent-research-explorer.toml
│   ├── hmasd-project-scout.toml
│   ├── hmasd-code-scout.toml
│   ├── hmasd-implementer.toml
│   ├── hmasd-implementer-terra.toml
│   ├── hmasd-reviewer.toml
│   ├── hmasd-verifier.toml
│   ├── hmasd-experiment-operator.toml
│   ├── hmasd-workflow-recovery-manager.toml
│   ├── hmasd-cpm-agentify-transport.toml
│   ├── hmasd-explorer-agentify-transport.toml
│   ├── hmasd-external-gemini-transport.toml
│   ├── hmasd-research-scout.toml
│   ├── hmasd-research-innovator.toml
│   ├── hmasd-research-critic.toml
│   ├── hmasd-research-principles-analyst.toml
│   └── hmasd-research-artifact-writer.toml
└── runtime/                                # ignored,可重建
    └── tasks.json
.agents/skills/                             # project skills
├── hmasd-root-task/
├── hmasd-portfolio-task/
├── hmasd-em-task/
└── hmasd-cm-task/
```

Bootstrap 已选择 Codex project skill，实际目录为 `.agents/skills/`。
Portfolio、EM、CM 不进入 `.codex/agents/`，因为它们不是可 spawn subagent。

## 6. 保留的 OMP domain/effect plane

以下实现是迁移输入，不是新计划待设计项：

```text
docs/research/portfolio/PORTFOLIO.md
docs/research/portfolio/workflow/registry.json
docs/research/candidates/<direction-id>/DIRECTION.md
docs/research/candidates/<direction-id>/workflow/research/state.json
docs/research/candidates/<direction-id>/workflow/engineering/state.json
docs/research/candidates/<direction-id>/workflow/external-review/index.json
docs/research/candidates/<direction-id>/results/**
scripts/hmasd_state.py
scripts/hmasd_worktree.py
scripts/hmasd_resource_preflight.py
scripts/hmasd_run.py
scripts/hmasd_external_review.py
scripts/hmasd_dashboard.py
scripts/schemas/hmasd_*.schema.json
```

### Writer 与路径合同

| 内容 | Writer / owner |
| --- | --- |
| `PORTFOLIO.md` 与 registry lifecycle | Portfolio / `writer: Portfolio` |
| `DIRECTION.md`、research state、external index、accepted result | `EM-<direction-id>`；精确 artifact 可委托 Artifact Writer |
| engineering state | `CM-<direction-id>` |
| assignment worktree source | CM 分配的 Implementer，限 exact allowed paths |
| run manifest/output | `Operator-<run-id>` |
| runtime refs/worktree map | Root |
| Agentify commitment | Agentify only |
| exact external archive validation 与 canonical Git integration | Root |

Codex adapter 必须调用现有 CLI 和 schema validator；不能只在 bootstrap 中重复
这些文字而绕过机械检查。

### Host compatibility boundary

当前 OMP helper 使用 Linux `fcntl`，而本 Codex desktop/worktree 是 Windows。
同时 Git `core.autocrlf=true` 会让 working-tree authority bytes 与 registry 中的
LF blob SHA 不同。迁移必须保留 contract、替换 host adapter：

1. 为短时 state/worktree lock 提供 Windows 与 Linux 等价实现，保持同一
   CAS、临界区和 unknown-outcome 语义；
2. 对 durable Markdown/JSON 建立明确 LF checkout contract；验证 raw working
   bytes、Git blob bytes 与 stored SHA 一致，不在 hash 函数里静默 normalize；
3. Windows sibling worktree 根使用 `C:/Projects/HMASD-worktrees`，保留既有
   `<direction>-<kind>-<assignment>` 命名；
4. 不混用 Windows-created worktree 与 WSL Git；Windows Codex 迁移固定使用
   native-host Git、Python、Node 和 Windows sibling paths。

这是一层运行时适配，不授权修改 writer、path、branch、result 或 effect authority。

### 稳定命名

```text
direction-id       [a-z0-9][a-z0-9_-]{1,63}
EM identity        EM-<direction-id>
CM identity        CM-<direction-id>
worktree           <sibling-root>/<direction>-<kind>-<assignment>
branch             omp/<direction>/<kind>/<assignment>
run root           temp/directions/<direction-id>/exp/<run-id>/
test root          temp/directions/<direction-id>/test/
external round     docs/external-review/directions/<direction-id>/<round-id>/
```

Codex task title 映射 logical identity 和 generation，但不替代它们。CM 不按每个
scope 改 writer identity；连续 assignment 在 identity/checkpoint 兼容时复用同一
CM task，不兼容时轮换 generation。并行 assignment 仍各用独立 worktree/branch。

## 7. Task runtime map

忽略的 `.codex/runtime/tasks.json` 最少包含：

```json
{
  "schema_version": 1,
  "revision": 1,
  "updated_at": "<utc>",
  "writer": "Root",
  "tasks": [
    {
      "logical_identity": "Portfolio",
      "kind": "portfolio",
      "direction_id": null,
      "generation": 1,
      "task_title": "HMASD Portfolio",
      "thread_id": "<runtime-only>",
      "host_id": "<runtime-only-or-null>",
      "last_cursor": null,
      "project_root": "<canonical-local-path>",
      "worktree_ref": null,
      "checkpoint_sha": "<sha-or-null>",
      "lifecycle": "IDLE",
      "last_seen_at": "<utc>"
    }
  ]
}
```

该 map 是 cache，不是 identity authority。丢失时 Root 列出项目 tasks，再按标题、
项目路径、bootstrap identity、generation 和 checkpoint 核对。无法证明唯一匹配
时报告冲突，不创建第二个 effect-capable task。

现有 tracked registry 的 `agent.logical_identity/job_name/generation/runtime_ref`
先保持不变。只有 Phase 4 证明字段无法承载 Codex task refs 时才注册最小 schema
migration；live thread/host/cursor 永远只进入 ignored runtime state。

## 8. 互动与 Decision Packet 合同

### 8.1 用户直接互动

任何顶层 task 都是入口：

- User → Portfolio：形成跨方向、lifecycle、优先级或 CM 选择；
- User → EM：改变一个方向的科学问题、证据或结论；
- User → CM：改变有界工程目标、约束或技术选择；
- User → Root：启动、暂停、恢复、重排或查询已决定工作。

task transcript 保存 conversation provenance。Material 互动必须由接收角色写入其
OMP durable authority；只有对话而无 durable update 的内容不能在恢复后驱动其他
task effect。

### 8.2 Decision Packet

跨 task 消息携带已有 durable refs，而不是默认新增 handoff 文件：

```json
{
  "contract_version": 1,
  "sender_identity": "Portfolio",
  "sender_generation": 1,
  "decision_kind": "DISPATCH_CM",
  "objective": "<bounded outcome>",
  "done_criteria": [],
  "non_goals": [],
  "authority_refs": [],
  "state_revisions": {},
  "checkpoint_sha": "<sha>",
  "direction_id": "<id>",
  "assignment_id": "<id>",
  "owned_paths": [],
  "worktree_ref": null,
  "effect_refs": [],
  "requested_action": "<orchestration action>"
}
```

Root 校验 refs/revisions/identity 后执行 requested action，不重新判断 decision。
Material scope 变化由原 Decision Authority 更新 durable state 和 packet；Root 不
自行扩展。Decision Packet 不是 permission gate，也不建立新的 tracked ledger。

## 9. 单层 direct subagent graph

项目单层策略允许：

| 顶层 task | 可直接派生的叶子 |
| --- | --- |
| Root | project/code scout、verifier、workflow recovery、必要的 integration support |
| Portfolio | research scout、research critic、principles analyst、必要的 reviewer |
| EM | research scout/innovator/critic/principles analyst、code scout、artifact writer、Pro/Gemini transport |
| CM | project/code scout、两类 implementer、reviewer、verifier、experiment operator、research scout |

所有 direct subagent 都是 leaves。Root 不派生 Portfolio/EM/CM；Portfolio 不直接
dispatch EM/CM。顶层角色可以直接完成其职责，delegation 仅用于有价值的并行和
上下文隔离。2026-08-25 首次 smoke 使用了配置变更前启动的宿主，因此 nested
child 完成不能用于判断重启后的 depth gate。下表同时是 instruction allowlist；
clean cutover 前还必须在完全重启后的新 task 中证明运行时拒绝。

## 10. Bounded cycles

### Root：低成本 orchestration

```text
START_OR_RESUME
  -> LIST/RECONCILE PROJECT TASKS + RUNTIME REFS ONCE
  -> READ PENDING DECISION PACKETS
  -> VALIDATE AUTHORITY REFS WITHOUT REDECIDING
  -> CREATE/RESUME/MESSAGE TARGET TASK
  -> ALLOCATE WORKTREE/PROCESS CAPACITY
  -> WAIT WITH COMPACT CURSOR-AWARE SNAPSHOTS
  -> ROUTE MATERIAL RESULT TO ITS DECISION AUTHORITY
  -> APPLY EXACT ROOT-OWNED ARCHIVE/GIT/RUNTIME EFFECT
  -> CHECKPOINT | IDLE | USER/OWNER DECISION | BLOCKED
```

Root 只做 frozen workflow 中的机械选择。需要改变方向价值、科学含义、工程设计
或 scope 时，返回 Portfolio、EM、CM 或 User。

### Portfolio：稀疏高能力决策

```text
PERIODIC WAKE OR USER INTERACTION
  -> RECONCILE PORTFOLIO + REGISTRY + MATERIAL EM/CM RESULTS
  -> OPTIONAL DIRECT READ-ONLY SPECIALISTS
  -> FORM CROSS-DIRECTION / LIFECYCLE / CM DECISION
  -> WRITE PORTFOLIO.md AND REGISTRY VIA CAS WHEN CHANGED
  -> SEND DECISION PACKET TO ROOT
  -> IDLE
```

Portfolio 不持有 EM/CM，不等待所有工作完成后才存在，也不被限定为只读。它可
保留同一 task 历史，低频 wake 后继续工作。

### EM：方向科学

```text
USER/ROOT ASSIGNMENT OR MATERIAL EVIDENCE
  -> RECONCILE DIRECTION + RESEARCH/EXTERNAL STATE
  -> FREEZE QUESTION/EVIDENCE
  -> OPTIONAL DIRECT SPECIALIST WAVE
  -> LOCAL SYNTHESIS / EXTERNAL REVIEW
  -> WRITE EM-OWNED AUTHORITIES
  -> SEND MATERIAL RESULT TO PORTFOLIO AND ORCHESTRATION REF TO ROOT
  -> IDLE | CONTINUE | REQUEST ENGINEERING
```

### CM：方向工程

```text
PORTFOLIO/USER DECISION ROUTED BY ROOT
  -> RECONCILE DIRECTION + ENGINEERING STATE + WORKTREE
  -> FREEZE BOUNDED ASSIGNMENT AND ALLOWED PATHS
  -> OPTIONAL DIRECT IMPLEMENT/VERIFY WAVE
  -> OPTIONAL UNIQUE OPERATOR
  -> WRITE CM-OWNED STATE / PREPARE CANDIDATE
  -> SEND TECHNICAL RESULT TO PORTFOLIO/EM AND INTEGRATION REF TO ROOT
  -> IDLE | CONTINUE | BLOCKED
```

## 11. 分阶段实施

截至 2026-08-25 的本机实现快照：Phase 0、Phase 2、Windows host adapter、
Dashboard quiet fallback 和 non-sending focused regression 已完成；Phase 1 已
完成三个 Luna-xhigh fixture peer tasks 的 create/read/send/wait、direct leaf 和
共享目录 smoke，并发现 V2 depth hard gate 不成立；Phase 3 只完成无 durable
decision 的路由原型，Phase 8、9 仍未执行。以下条目保留完整完成定义，不能把
本机 smoke 当作 clean cutover。

### Phase 0：冻结基线与术语

1. 记录远端 `omp/workflow` 精确 SHA 与 focused test 基线。
2. 直接在 `omp/workflow` 工作区实施；不修改 main 用户工作区，不建立迁移用
   对比 worktree。
3. 保留 `docs/plans` OMP 原文；跟踪本 migration 文档和 `CONTEXT.md`。
4. 建 preserve/translate/retire 清单，明确 OMP 文件管理整体 preserve。

验收：`CONTEXT.md` 不含实现细节；原 OMP 合同可由 Git 精确恢复。

### Phase 1：Codex task/interaction 能力核验

使用无副作用 fixture 验证：

1. 四类 peer task 的创建、直接用户互动、历史记录和独立上下文。
2. list/read/send/wait/handoff/pin/archive 的参数、cursor、attention 和终态语义。
3. 任一 task 重启/继续后互动记录、goal 和 runtime identity 的保留情况。
4. `max_depth=1`：完全重启 Codex 后，顶层 direct leaf 成功，leaf 再派生失败；
   旧宿主上的结果不计入验收。
5. task 使用不同 worktree/local project 时的文件可见性。
6. sandbox/approval/skills/AGENTS/MCP 在顶层 task 与 leaf 的继承。
7. Root 候选低成本模型对 50+ 次 deterministic orchestration fixture 的稳定性、
   tool-call 正确率、重复 effect 率、延迟和 token 成本。
8. Portfolio task 能否固定 `gpt-5.6-sol` max 并在 idle 后继续原历史。
9. Windows-native helper、Python、Node 和 worktree gitdir 的可运行性；WSL helper
   与跨 host 路径拼接不属于当前执行面。
10. LF exact-byte checkout：working bytes、Git blob 和 registry SHA 必须一致。

输出 `CODEX_CAPABILITY_MATRIX.md`。未经实测的 task API、模型绑定或恢复语义
不得成为后续前提。

### Phase 2：AGENTS、顶层 bootstrap 与 main 角色配置

1. 将 OMP RULES、writer/path contracts 和 Decision Authority 写入根 `AGENTS.md`。
2. 建 `.codex/config.toml`，启用 multi-agent，目标 `max_depth = 1`。
3. 保留 main 分支的 18 个角色 TOML（其中 15 个为 direct leaf，3 个为兼容性
   manager/recovery 配置）；不创建 Portfolio/EM/CM custom agent。
4. 建 Root、Portfolio、EM、CM bootstrap instructions/skills。
5. 将 OMP agent/Skill 的 exact owned paths、spawns、禁止效果和结果 envelope
   逐项移植；不得概括成较弱的通用提示。
6. 不伪造 continuous Advisor；使用显式 frozen reviewer/critic。

验收：main 注册角色 discovery 正确；四类顶层 task 的模型/authority/allowed leaves
与本计划一致；fresh-host leaf 无法再派生。

### Phase 3：Peer task 与 Decision Packet 原型

1. 建 Root、Portfolio、一个 EM 和一个 CM fixture task。
2. 从 User → Portfolio 记录一个无 effect 决定，写 fixture authority，并由
   Portfolio 向 Root 发 Decision Packet。
3. Root 只校验和转发，不改变目标；EM/CM 可被用户直接追加兼容约束。
4. Portfolio、EM、CM 各派一个 read-only direct leaf；Root 用 compact wait
   跟随，但不吞入全量 transcript。
5. 验证 title/identity/generation 冲突时 fail closed，不盲建重复 task。

验收：Root 不是唯一入口或决策者；conversation provenance 与 durable decision
都可恢复；Portfolio 不是 Root subagent 或只读 Audit。

### Phase 4：Runtime task refs 与 Dashboard

1. 新增最小 `.codex/runtime/tasks.json` adapter，或证明原生 task list 足以覆盖
   全部恢复场景后删除该需求。
2. 保持 tracked registry logical identity/job/generation，live task refs 仅在
   ignored runtime state。
3. 覆盖 missing map、stale cursor、duplicate title、parked task、late result、
   generation mismatch 和 direct-user-update-after-root-snapshot。
4. Dashboard agent 页面改为同级 Root/Portfolio/EM/CM tasks + 每个 task 内
   direct leaves；仍只读且不暴露 transcript/secrets。

验收：Root/runtime map 丢失不会创建重复 effect-capable task；Dashboard 不成为
唯一互动记录或权威。

### Phase 5：证明 OMP 文件合同在 Codex 下保持

1. 不设计新 ownership；先实现最小 cross-platform lock 与 LF checkout adapter，
   再逐项复跑 OMP state/path/writer/schema focused tests。
2. 增加 Codex bootstrap → existing CLI 的 adapter tests，证明传入 writer、
   direction、assignment、allowed paths、revision 和 SHA 未丢失。
3. 验证 Portfolio 而非 Root 写 Portfolio authority；EM/CM/Operator writers 不变。
4. 验证 direct user interaction 造成 material change 时仍通过原 writer/CAS path。
5. 只有实际 runtime 字段不兼容时才提 schema migration；科学字段零变化。

验收：`hmasd_state.py` 的 wrong-writer/wrong-path/stale-revision tests 和
`hmasd_worktree.py` 的 dirty/stale/conflict/out-of-scope/symlink tests 全部保持。
Windows native run 不得出现 `fcntl` import failure，authority working bytes SHA
必须等于 registry/Git blob SHA。

### Phase 6：CM worktree、Git 与 result run

1. Root 为每个 CM assignment provision 独立既有命名的 worktree/branch。
2. CM 与 direct Implementer 使用 exact allowed paths；Root canonical integration
   仍只应用一个 verified candidate。
3. 用无科学含义短命令验证 CM direct Operator：一个 command 一个 Operator。
4. 验证 CM/Root task 重启只 reconcile，不盲目重启 RUNNING/UNKNOWN run。
5. 保留 7200/7201、memory preflight/TOCTOU 和 child identity checks。

验收：Codex task 拓扑未改变任何 worktree、branch、run 或 integration 语义。

### Phase 7：External review 与 Agentify

1. Pro/Gemini transport 作为 EM direct leaves，保持 provider-specific binding。
2. 仅做 non-sending preflight 和 existing-operation observe。
3. 保留 prompt/evidence SHA、operation refs、archive exact bytes、blind ordering、
   EM synthesis 和 commitment-unknown no-resend。
4. Root 只做 exact archive validation；EM 做 scientific intake；Portfolio 消费
   material结论；task/thread ID 不进入 Agentify authority。

验收：无 live send、无第二 ledger、无 Root 科学解释。

### Phase 8：Portfolio wake 与用户交互策略

支持以下 wake：

- configured periodic cadence；
- material EM/CM result；
- 用户直接进入 Portfolio；
- 高成本资源投入、direction merge/close/reactivate 前；
- Root 发现 pending 决策但不自行判断时。

Portfolio task 保留历史并在 wake 间 idle。它可直接使用只读 scientific leaves，
写 Portfolio authority，然后把 Decision Packet 发给 Root。Cadence、时区和是否用
scheduled task 由用户另行确定；本阶段不擅自创建 automation。

验收：Portfolio 具有写入和决策能力，不持有 EM/CM dispatch，也不持续轮询。

### Phase 9：只读 shadow 与 clean cutover

1. Codex Root 对 OMP durable state/tasks 做只读 reconciliation。
2. 两个 fixture directions 完成 User→Portfolio→Root→EM/CM 流程。
3. 运行 Phase 2–8 focused tests 和 final diff review。
4. 证明 OMP 无 live manager/job/process/unknown effect ownership。
5. 停止 OMP dispatch，激活 Codex 写入；禁止双运行窗口。
6. Portfolio 完成一次真实无 effect 决策盘点并进入 idle；Root 忠实编排一条
   no-op Decision Packet 并进入 idle。
7. 经用户确认后才删除不再需要的 `.omp` 编排文件；保留 Git 历史、OMP plans
   和所有 domain/effect plane 文件。

## 12. 验证矩阵

| 声明 | 最小直接证据 |
| --- | --- |
| 四类顶层 task 均可直接互动 | 分别发送用户消息、恢复 task 并读取历史 |
| Root 不是唯一入口 | User→Portfolio/EM/CM 不经 Root 的记录与 durable update |
| Root 低成本且稳定 | deterministic orchestration fixture 的正确率/重复 effect/成本 |
| Portfolio Sol max 且可写 | resolved model evidence + Portfolio CAS writer smoke |
| Portfolio 不 dispatch EM/CM | spawn graph/contract test + Decision Packet→Root smoke |
| subagent 只有一层 | 完全重启后的顶层 direct spawn 成功 + leaf 再派生拒绝 |
| Decision 与 permission 分离 | Root 高权限但 material choice 返回 owner 的场景 |
| OMP 文件合同不变 | writer/path/schema/worktree/run focused tests |
| conversation 与 durable decision 均可恢复 | task history + authority revision/SHA 对照 |
| Root 恢复不重复 task/effect | runtime map 删除后的 list/reconcile smoke |
| Portfolio 非只读、非轮询 | material write + idle/wake continuation |
| external send 不重复 | Agentify commitment-unknown observe-only tests |
| Dashboard 非权威 | mutation 405 + byte comparison + task projection smoke |

测试提供证据，不授予权限。不得为了测试形状创建新的长期控制角色。

## 13. 回滚与删除条件

- Phase 1–8 均可通过放弃 Codex adapter 分支回滚；不得修改 OMP authority 来
  证明迁移。
- peer task 历史/恢复不可靠时停止 cutover；不退回隐藏两级 subagent 树。
- Portfolio/EM/CM custom agent 定义在 task-plane smoke 通过后删除，不能与
  顶层 bootstrap 长期并存。
- `.codex/runtime/tasks.json` 只有在原生 list/reconcile 覆盖全部恢复场景时删除。
- Portfolio automation 只在用户确定 cadence 后创建；删除 automation 不改变
  Portfolio task 的决策和写入 authority。
- `.omp` 编排文件只在 clean cutover 和用户确认后删除；其 file/state/run/Git
  contracts 已移植且继续由 tests 保护。

## 14. 当前下一步

下一步先完全重启 Codex，并在 fresh host 上复验 `max_depth = 1`。之后补齐 task
restart/compaction、handoff、archive/unarchive、stale cursor、真实 Sol-max
Portfolio 模型回显和 Decision Packet smoke，并决定原生 task list 是否足以
取代 `.codex/runtime/tasks.json`。

当前不改 main 注册的 agent TOML（OMP 工作区副本已保持与 main 逐字一致），不
迁移 state schema、不启动科学命令、不发送 provider 请求、不创建 Portfolio
automation，也不关闭 OMP。完成 shadow/cutover 证据并由用户确认前，Codex
adapter 不接管真实方向或 effect。
