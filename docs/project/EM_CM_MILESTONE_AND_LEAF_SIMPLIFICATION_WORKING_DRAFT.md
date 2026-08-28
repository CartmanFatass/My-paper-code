# HMASD 原生工作流简化与 milestone memory 需求

状态：用户已确认的重设计需求工作稿；非当前 authority，尚未实施

Decision owner：User

确认日期：2026-08-28

本文汇总本轮设计访谈中已经确认的目标和边界。它用于下一次继续制定 exact affected-path
inventory 与实施计划，不修改当前 `WORKFLOW_PROTOCOL.md`、AGENTS、skills、scripts、schemas
或 tests。新控制层正式 cutover 前，现有 authority 仍然有效。

## 1. 总体目标

HMASD 强依赖 Codex Desktop 的原生能力：可见 top-level tasks、task history、context
isolation、create/send/read/wait、task continuation、archive、worktree 和 parent/child
subagent return。项目不复制这些产品事实。

本次重设计同时解决两个问题：

1. LLM 长期近似无状态、上下文会压缩，需要少量 milestone snapshot 留住 material 成果与
   next action。
2. 方向已经由长期 EM/CM sessions 隔离，大量认知与实施 subagents 会重复读取、移交和综合，
   造成延迟、token 与判断质量损失。

新流程追求最少机制：manager 默认直接完成本职工作；subagent 只服务于独立性、专业证据
收集、外部 Effect 或长命令托管；state 只保存当前恢复快照，不形成日志数据库。

## 2. 信任、安全与版本标准

### 2.1 原生 Codex 事实直接可信

- Codex task ID、可见 history、task status 和 parent/child relation 直接作为 identity、
  delivery 与 return facts。
- 项目不设计 task authentication、签名、token、challenge、receipt、immutable message
  ledger、本地 task registry、raw history parser 或替代 scheduler。
- 这是单用户、本地项目、Codex 内部协作流程；协议不建立 malicious participant、message
  forgery、本地 tampering 或攻击者 threat model。
- native Codex task能力不可用时流程显式停止，不启用本地替代 task plane。

### 2.2 不使用控制面 SHA256

以下对象不使用 SHA256 证明 identity、freshness 或防篡改：

- session messages 与 task identity；
- workflow revision/control release；
- authority refs、state refs 与 milestone；
- material evidence notes 与本地 tool invocation；
- 本地 artifact path containment。

需要 freshness 时使用 `revision + updated_at/observed_at`；需要代码版本时使用正常 Git
branch/commit facts。checksum 只允许两类例外：

1. 外部发布物自身提供 checksum，下载流程需要核对；
2. 科学验收明确要求 byte identity，例如 checkpoint bit-identity 或大型结果一致性。

这些 checksum 不能扩散回 session protocol。

### 2.3 唯一当前版本

- 删除 `protocol_epoch`、generation 和 hash-derived control release ID。
- 唯一协议顶部只保留人类可读 `Workflow revision: YYYY-MM-DD.N`。
- 不兼容旧控制层；不提供 adapter、translator、dual-read、fallback、legacy message
  acceptance 或 runtime migration。
- active paths 永远只代表唯一最新控制层。

## 3. Standing topology 与身份

保留以下可见 top-level tasks：

- Root；
- Workflow-Clerk；
- Portfolio；
- 每个需要工作的 direction 一个 `EM/<direction>`；
- 每个需要工作的 direction 一个 `CM/<direction>`。

不再使用 `gN` generation。真实身份是 Codex task ID；title 只是人类标签。若出现重复候选，
停止发送并交用户选择，不建立本地 identity registry。

新 task bootstrap 只包含：role、direction、repository、`WORKFLOW_PROTOCOL.md`、对应 role
skill、direction authority path 与 state path。每个 turn 开始时 role skill重读当前协议与
state。

本轮 cutover 前的旧 direction sessions 已由用户全部退役。它们不 reload、不迁移、不
unarchive；新协议下需要方向工作时创建新的长期 EM/CM task。

## 4. 最小原生消息

跨 top-level tasks 只使用 Codex Desktop 原生消息，不生成本地 body locator、canonical
envelope、message digest、reply-chain 文件或 validator。

消息种类只有：

- `WORK`：交付一个 bounded objective；
- `RESULT`：报告 manager/Portfolio 判断及下一责任；
- `CONTROL`：用户或 authority 改变正在进行的工作。

使用固定、简短、可读的 Markdown headings，不要求 JSON parser。建议字段：

```text
[WORK]
Direction: ...
Objective: ...
Owned paths: ...
Effects: ...
Acceptance: ...
Refs: ...
```

`RESULT` 使用两个正交字段：

- `Outcome: DONE | WAITING | FAILED`
- `Next: EM | CM | PORTFOLIO | ROOT | SAME | NONE`

并包含 summary、refs，以及 WAITING/FAILED 所需 blocker/reentry condition。Clerk只读取
`Next`，不从 prose推理路由。ACTIVE direction不能使用 `Next: NONE`；只有 Portfolio正式
关闭方向后可以 NONE。

`CONTROL` 使用：

- `Action: PAUSE | RESUME | CANCEL | REPLACE | RELOAD`
- direction、reason、updated_at；
- REPLACE 时附 replacement objective/Effect。

没有 message ID、reply-to、locator、digest 或身份验证。

### 4.1 固定 endpoints

- Root → Clerk：跨方向或 shared-core WORK；
- Clerk → Portfolio/EM/CM/Root：bounded WORK 或转发 CONTROL；
- Portfolio/EM/CM/Root → Clerk：RESULT；
- participant → Clerk：用户直接控制产生的 CONTROL；
- Clerk → affected participant：转发 CONTROL；
- subagent → spawning parent：Codex原生 final return。

EM、CM、Portfolio 不直接互发 top-level messages。

## 5. Workflow-Clerk 最小职责

Clerk只负责：

1. 使用 Codex Desktop 原生 task list/history找到或创建 standing task；
2. 根据消息显式 `Next` 转发工作；
3. stopped/idle 且工作尚未完成时继续同一个当前协议 task；
4. 在事件到达时修复 ACTIVE direction没有明显 next owner的缺口。

Clerk不验证身份、不解释领域结果、不维护 retry FSM、attempt ledger、owner cache、cursor、
receipt、release adoption 或 Dashboard projection。它完全事件驱动，只在收到消息、原生
heartbeat、用户检查或手动继续时观察 liveness，不常驻轮询。

Clerk不自动 retry。EM/CM在当前 WORK内自行诊断和修复；无法继续时返回 WAITING/FAILED。
external Effect继续严格 at-most-once。

## 6. EM/CM milestone memory

### 6.1 单一当前 snapshot

现有 `workflow/research/state.json` 与 `workflow/engineering/state.json` 各自成为唯一当前
milestone snapshot。继续使用 JSON，但不保存历史或 transport状态。

共同字段：

- `direction`
- `role`
- `revision`
- `updated_at`
- `milestone`
- `status`
- `completed_summary`
- `refs`
- `blockers`
- `reentry_condition`
- `next_action`

EM额外字段：

- `claim_ceiling`
- `next_discriminator`
- 当前 `research_cycle`

CM额外字段：

- `worktree`
- `branch`
- `changed_paths`
- `verification_summary`
- `run`

删除 active_agents、round ID、registry revision、question/evidence-set digest、base/candidate
SHA、integration CAS 等旧控制字段。

### 6.2 Milestone 与 status

EM milestones：

- `SCOPE_FROZEN`
- `SYNTHESIS_READY`
- `REVIEW_RESOLVED`
- `HANDOFF_READY`

CM milestones：

- `SCOPE_FROZEN`
- `CANDIDATE_READY`
- `REVIEW_RESOLVED`
- `RUN_OR_HANDOFF_READY`

共同 status：

- `ACTIVE`
- `WAITING`
- `FAILED`
- `COMPLETE`

milestone 表示完成到哪里；status 表示当前能否继续。leaf返回、单次测试、普通 lookup、单文件
写入或工具成功本身不构成 milestone。

### 6.3 写入与恢复

只有当上下文消失会导致重做一项有实质成本的工作，或可能重新作出不同 material judgment
时，才跨越 milestone。跨越后立即原子覆盖 state、revision +1、更新时间并写清 next action；
不要求立即 commit/push。简单 slice可以只写最终一次。

恢复时：读取 role skill与协议、native WORK/CONTROL history、direction authority、最新
state refs、owned-path diff和Git facts。state表示最后接受的 milestone；其后的 dirty work
是 in-flight work，必须保留和检查。无法判断修改归属时停止对应 path并报告，绝不自动
reset、checkout或删除。

### 6.4 最小 state helper

保留最小 research/engineering schemas 与 `hmasd_state.py validate/update`。`update` 只负责：

- writer role；
- revision +1；
- updated_at；
- 基本字段/enum校验；
- 同目录原子替换。

删除 initialize/replace CAS、portfolio-apply、migration、lifecycle mutation与旧 schema支持。

## 7. 减少 subagent 的工作模型

manager默认直接工作。只有独立 fresh-context review、专业证据收集、外部 Effect、长命令托管
或收益明确的正交并行工作才创建 leaf。

### 7.1 CM 主 session

CM直接完成：

- repository/code理解；
- implementation与focused tests；
- 普通runtime verification；
- engineering state与material evidence interpretation；
- Git closure。

不再保留 HMASD Implementer或RoutineImplementer。

CM Scout必须保留，合并原ProjectScout/CodeScout为一个 `hmasd-cm-scout`，使用 Luna medium、
read-only，只返回 affected files、symbols、callers、consumers、tests与shared boundaries。
非平凡实现如果当前 milestone/state没有可信surface map，CM必须先调用Scout；exact小改或同一
milestone内已有map时可以复用，不重复spawn。

CM leaves：

- Reviewer：Sol xhigh。shared-core或scientific/numerical/RNG/checkpoint/bit-identity/
  external-Effect语义改变时强制；普通direction-local实现可选。
- Verifier：Luna high。只有acceptance依赖静态review和CM tests不能充分回答的独立runtime/
  equivalence observation时使用。
- Experiment Operator：Luna low。持有一个exact frozen result-bearing command和terminal
  witness。
- external engineering consultation transport：Luna medium，按需、send-once。

### 7.2 EM 主 session

EM直接完成：question freezing、mechanism/innovation、principles analysis、constructive
case、synthesis、revision、claim ceiling、next discriminator、research artifact/state写作。

EM leaves：

- Research Scout：Sol high。只用于external primary evidence、多来源检索或大范围evidence
  acquisition；本地authority读取由EM直接完成。
- Research Critic：Sol max。只在External Pro留下material objection、EM拒绝Pro核心建议、
  跨方向/shared scientific core或用户明确要求时使用一次。
- External Pro transport：Luna medium，见第8节。

删除独立Research Innovator、Research Principles Analyst、Research Artifact Writer和
`hmasd-scientific-critical-thinking` skill。其有价值的claim-ceiling checklist并入EM skill。

### 7.3 Agent limits

- `max_depth = 1`
- 每个manager task tree `max_threads = 8`
- 正常slice预期使用0–2个leaves；8只是上限，不是目标。

## 8. Mandatory External Pro Innovator/Convergence

### 8.1 Material research cycle

External Pro按material research cycle强制，而不是按turn/WORK调用。以下情况开启新cycle：

- 新direction；
- 新mechanism/comparator/discriminator；
- claim ceiling可能实质上升；
- 新结果推翻核心假设；
- Portfolio要求重新评估投资方向。

事实补充、措辞修订、claim收窄、工程结果录入或相同问题继续不启动新cycle。

EM state只保存当前cycle：

```json
{
  "research_cycle": {
    "label": "short-human-readable-name",
    "opened_at": "...",
    "reason": "...",
    "pro_innovator": {"status": "PENDING", "response": null},
    "pro_convergence": {"status": "PENDING", "response": null}
  }
}
```

status允许 `PENDING | COMPLETE | WAITING | WAIVED`。不保存cycle history、attempt ledger或
安全ID。

### 8.2 顺序与频率

1. EM到达 `SCOPE_FROZEN`；
2. 必要Scout evidence完成；
3. External Pro `INNOVATOR` 一次；
4. EM综合形成 `SYNTHESIS_READY`；
5. External Pro `CONVERGENCE` 一次，prompt明确要求independent/adversarial convergence；
6. EM修订并形成 `REVIEW_RESOLVED`；
7. 再决定engineering/Portfolio/handoff。

每个cycle Innovator最多一次、Convergence最多一次。修订不自动re-review；只有material
objective/mechanism/comparator/evidence/claim变化形成新cycle时才允许新的两次调用。

### 8.3 Effect、failure与waiver

本需求授权每个material cycle自动发送一次Innovator和一次Convergence，不逐次询问。以下
情况必须回用户：非项目公开材料/secret/个人数据、provider/账号/付费方式变化、超出两次、
unknown send后考虑新发送、用户暂停外部Effect。

unknown commitment只观察、不重发；明确未发送失败则EM进入WAITING；长期不可用交Root，用户
可以对一个exact cycle明确waiver。不得以本地Critic或其他provider静默替代。

完整question/response保存为：

```text
docs/research/candidates/<direction>/external/
  <date>-<cycle>-pro-innovator.md
  <date>-<cycle>-pro-convergence.md
```

不维护external review index、receipt、SHA或额外handoff files。一个
`hmasd-external-pro-transport`按assignment的 `Mode: INNOVATOR | CONVERGENCE` 执行
send-once并归档，EM负责解释。

External Pro Convergence承担正常cycle的mandatory independent scientific review。本地Critic
仅为上述例外second opinion。Gemini在HMASD active control layer完全停止：不注册、不调用、
不作为fallback；旧Gemini config进入backup，但不卸载系统级组件。

## 9. Portfolio

只保留一个结构稳定、人类可读的 `PORTFOLIO.md` 作为当前lifecycle/priority/capacity
authority，使用固定表格：

| Direction | Lifecycle | Priority | Next role | Updated at | Reason/condition |
| --- | --- | --- | --- | --- | --- |

保留四态：`REGISTERED | ACTIVE | PARKED | CLOSED`。只有Portfolio改变lifecycle。重大投资或
关闭决定可以保留独立Markdown decision note；普通priority更新只更新表格。删除JSON registry、
revision DAG与CAS。

Portfolio先原子写 `PORTFOLIO.md`，再向Clerk发送RESULT。Clerk不读取文件重做判断。历史
decision notes若保留，顶部标明 `Historical decision; not current workflow state`；纯transport、
receipt、return body和CAS artifacts进入backup。

## 10. Scientific capability 与material evidence

保留极简capability catalog：

- `capability`
- `status = active | unavailable`
- `purpose`
- `entrypoint`
- `environment`
- `allowed_effects`

删除candidate lifecycle、owner/leaf routing、skill/source/manifest hashes与自动activation gate。
CLI只保留 `list/show/doctor`，不提供run/install/router/validate-evidence。

确定性本地科研工具由EM/CM直接调用。只有观测实际改变或限制claim/engineering judgment时，
manager才写：

`docs/research/candidates/<direction>/evidence/<descriptive-name>.md`

内容只需Question、Observed at、Inputs、Tool/command、Observation、Limitations、Judgment impact、
Result paths。raw output留在direction temp。删除candidate→typed observation→SHA validation→
sidecar pipeline。工具成功本身没有acceptance、routing或lifecycle语义。

## 11. Operator、external transport 与run layer

Operator command/terminal witness继续使用简单JSON，因为argv、cwd、outputs和exit reason需要
机器精确性；删除command/code/authority SHA与多阶段session binding。

external transport由parent冻结provider、question、archive path与send-once；不建立transport
envelope schema。unknown send不重发。

本次不重写实验运行器。保留prepare/resource admission、exact argv/cwd、memory safety、
checkpoint/result/stdout/stderr、terminal witness与Operator at-most-once。只删除纯session
authentication/binding字段；科学reproducibility、checkpoint identity和结果格式需要的内容
继续保留。

## 12. Dashboard、authority 与skills

Dashboard退出控制层和验收，不再显示或推导task owner、delivery、heartbeat、release、routing
或recovery。以后如有需要，可单独建立轻量科研/实验结果浏览页。

唯一控制authority是精简后的 `docs/project/WORKFLOW_PROTOCOL.md`。现有
`WORKFLOW_GOALS_AND_ACCEPTANCE.md`有价值内容合并进去，旧文件进入backup。

session skills只保留：

- `hmasd-root-task`
- `hmasd-workflow-clerk-task`
- `hmasd-portfolio-task`
- `hmasd-em-task`
- `hmasd-cm-task`

删除 `hmasd-slice-interface` 与 `hmasd-operations-manual`。角色操作规则直接写在五个skills中；
删除重复的 `.codex/prompts/hmasd-*.md`。AGENTS只保留authority索引和真正硬边界。

## 13. Waiting、archive 与task恢复

WAITING默认不创建heartbeat。只有存在明确可观察条件、用户希望自动复查，且heartbeat只唤醒
当前责任task时，才使用Codex Desktop原生heartbeat；不维护本地registry。

未来新协议tasks中：PARKED task可以保持idle；CLOSED task确认没有命令/handoff后归档。当前
旧direction sessions已全部退役，不复用。新协议第一次需要该direction时创建新的长期task。

## 14. Workspace 与Git

默认shared `main`，严格direction-owned paths。同一direction EM/CM不同时修改同一文件；
shared-core、path overlap、长时间并行或无法串行index时才使用Codex Desktop原生worktree，
不建立worktree registry。

- milestone update立即写工作树，不commit；
- 同一EM/CM继续不要求Git transaction；
- 跨top-level role handoff且refs含Git-visible内容时必须commit；
- push只在用户要求远端同步、跨worktree集成或正式方向交付时强制；
- 不创建空commit；
- shared index mutation必须串行。

本轮用户确认所有旧方向sessions已经暂停并退役，因此当前Git-visible paused work可以直接在
shared main建立一个boundary commit；后续控制重设计也可在main串行完成，不需要新worktree。

## 15. 无兼容cutover与workflow backup

旧控制层统一备份到一个从未存在的目录：

`C:/Projects/workflow backup/HMASD-control-pre-cutover-20260828-01/`

若已存在则使用 `-02` 等新目录，绝不覆盖或合并。保留repository-relative目录结构：

- 被删除文件：move原文件到backup；
- 被修改文件：修改前copy原版本到backup，再原地修改；
- 新文件无需backup；
- `BACKUP_NOTES.md`只记录时间、原路径和deleted/modified；不生成hash、restore script、
  migration map或runtime fallback。

任一copy/move失败立即停止cutover，不写新active files。已复制内容保留并标明incomplete。

cutover后active discovery/control paths只出现唯一最新版本，backup不被repo、skills、tests、
runtime、control release或recovery引用。backup只供人工查阅；Git是仓库历史。新版本集成后
出现问题时暂停WORK并fix-forward，不自动恢复旧版本。

旧research/engineering state先copy到backup并从active repo移除。由于旧sessions已退役，
不批量唤醒或迁移；新协议下第一次创建EM/CM task时，由owner根据当前authority写全新最小
state。REGISTERED/CLOSED不预建空state。

## 16. 实施范围与非目标

本次未来实施范围只包括：

- Codex task/session protocol；
- AGENTS、role skills、agent configs；
- milestone state与schemas/helper；
- Portfolio当前authority格式；
- capability/evidence流程；
- control/release/envelope旧入口；
- Dashboard控制投影；
- 对应tests与backup cutover。

明确不改变任何候选算法、训练逻辑、numerical behavior、RNG、checkpoint兼容性、实验结果或
scientific claim。若旧控制字段与这些语义耦合，先保留并单独报告，不能静默删除。

## 17. 最小验收

只测试可观察不变量：

1. active discovery paths只存在最新skills/agents；
2. research/engineering state校验最小字段与milestone enums；
3. 代表性EM可从state+refs恢复；
4. 代表性CM直接实现不要求Implementer，高影响change触发Reviewer；
5. CM Scout在非平凡未知surface前使用且可复用已有map；
6. External Pro每material cycle严格一次Innovator、一次Convergence，unknown send不重发；
7. active repo没有legacy envelope/release/hash-authentication入口；
8. backup没有被任何active file、test或runtime引用；
9. experiment run/Operator关键正确性语义没有变化。

避免逐句prompt snapshots、旧版本compatibility fixtures、message digest tests、本地task-history
simulation和第二份authority断言。

## 18. 后续接续

本轮只把已确认需求形成Git边界，不实施重设计。下一次继续时应先：

1. 盘点exact affected paths并区分delete/modify/retain；
2. 制定单向main cutover顺序；
3. 明确旧Portfolio历史decision的domain/transport分类；
4. 确认备份目录不存在并核对exact targets；
5. 用户明确授权实施后再执行backup、修改、测试、commit和必要push。
