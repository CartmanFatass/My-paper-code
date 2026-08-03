# HMASD 工作流审计快速指南（Claude）

```text
document_kind=advisory_workflow_audit_guide
authority=none
authoritative_router=AGENTS.md
workflow_owner=workflow_design_manager
snapshot_inventory=17_roles|7_skills|13_codex_profiles|3_claude_helpers
snapshot_workflow_commit=8a6ffad9a277a85f64b31e95b5bb751d96ccf37e
```

## 1. 用途和边界

本文件帮助 Claude 快速理解 HMASD 的现行多代理工作流，并对角色、
Skill、profile 和路由进行只读审计。它不是第二套工作流合同，不授予
修改、Git、科研、运行时、外审或验收权限。

审计时按以下优先级判断：

1. 用户当前的直接指令；
2. 仓库根目录 `AGENTS.md`；
3. 被审计角色的 `.agents/roles/*.md`；
4. 该角色被授权读取的当前合同；
5. 被点名的 `.agents/skills/*/SKILL.md`；
6. `.codex/agents/*.toml` 或 `.claude/agents/*.md` 的启动配置。

如果本文件与上述权威表面冲突，以权威表面为准，并将冲突报告给
Workflow Design Manager（WDM）。不要自行修复。

## 2. 最小加载顺序

不要一开始读取整个仓库。先确定审计对象，再使用最小路径集：

1. 读取 `AGENTS.md`，确认 active identity、权限和禁止默认加载的内容。
2. 读取该角色唯一的 charter。
3. 读取该角色实际调用的 Skill；没有调用就不要读取。
4. 对自定义 subagent，读取对应 `.codex/agents/*.toml`。
5. 只读取本次审计指向的合同、测试和脚本。

以下通常不是现行指令：

- `docs/project/archive/` 中的历史状态；
- `docs/external-review/` 中的旧轮次记录；
- `docs/superpowers/specs/` 中的历史设计稿；
- `.codex/better-harness/` 中的旧报告；
- Git 已删除文件在历史提交中的内容。

历史材料可以解释事故，但不能覆盖当前合同。

## 3. 四类指令表面

| 表面 | 负责什么 | 不应负责什么 |
|---|---|---|
| `AGENTS.md` | 身份路由、共享权限、全局最小原则、公共路径索引 | 角色的完整操作步骤、项目历史 |
| `.agents/roles/*.md` | 结果所有权、观察空间、动作空间、判断权、恢复能力、完成证据 | 重复 Skill 的逐步操作或 profile 配置 |
| `.agents/skills/*/SKILL.md` | 一个角色的正常路径和最多一个简单 fallback | 新权限、第二验收者、角色历史 |
| `.codex/agents/*.toml` | 模型、reasoning effort、sandbox、角色指针 | 第二份角色 charter 或状态机 |

`.claude/agents/*.md` 只是 Claude 侧薄入口，必须指向共享 role charter，
不得复制另一套流程。

## 4. 持久角色与外部角色

| 角色 | 核心职责 | 权威路径 |
|---|---|---|
| Workflow Design Manager | 唯一工作流控制面设计、修改、验收和相关 Git owner；无代码、科研、运行时权力 | `.agents/roles/WORKFLOW_DESIGN_MANAGER.md` |
| Code Project Manager | 项目协调、代码范围、技术验收、运行时、实验调度、正式外审请求和 intake | `.agents/roles/CODE_PROJECT_MANAGER.md` |
| Independent Research Explorer | 独立科研探索、候选形成、科研子代理调度、独立外审请求和 intake | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md` |
| Agentify Transport Operator | 批量读取问题路径、控制 Agentify 页面、投递、等待和返回原始响应；不解释科研 | `.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md` |
| External Pro | 在用户给定问题边界内作科学判断；不是代码或工作流 owner | `.agents/roles/EXTERNAL_PRO.md` |

审计重点：WDM 不能成为每个操作的批准门；CPM 不能修改工作流；
Explorer 不能把科研判断交给 WDM；Transport Operator 必须有完成页面任务
所需的页面观察和可逆控制能力，但不得吸收科研决策。

## 5. Code Manager 子代理

| agent type | 模型 / effort / sandbox | 职责 | 角色路径 |
|---|---|---|---|
| `hmasd-code-scout` | Luna / medium / read-only | 精确代码接口和依赖映射 | `.agents/roles/CODE_SCOUT.md` |
| `hmasd-implementer` | Sol / high / workspace-write | 受保护或复杂的冻结实现任务 | `.agents/roles/IMPLEMENTER.md` |
| `hmasd-implementer-terra` | Terra / high / workspace-write | 日常、边界清楚的实现任务；与上项共享 charter | `.agents/roles/IMPLEMENTER.md` |
| `hmasd-reviewer` | Sol / xhigh / read-only | 一次集成代码审阅；必须评价收益、复杂度和维护成本 | `.agents/roles/REVIEWER.md` |
| `hmasd-verifier` | Luna / high / workspace-write | proof-sized 机械验证；不是科研或验收者 | `.agents/roles/VERIFIER.md` |
| `hmasd-experiment-operator` | Luna / low / workspace-write | 执行一份精确 CPM 实验 assignment | `.agents/roles/EXPERIMENT_OPERATOR.md` |

对应 profile：

```text
.codex/agents/hmasd-code-scout.toml
.codex/agents/hmasd-implementer.toml
.codex/agents/hmasd-implementer-terra.toml
.codex/agents/hmasd-reviewer.toml
.codex/agents/hmasd-verifier.toml
.codex/agents/hmasd-experiment-operator.toml
```

## 6. Explorer 科研子代理

| agent type | 模型 / effort / sandbox | 职责 | 角色路径 |
|---|---|---|---|
| `hmasd-research-scout` | Sol / high / read-only | 精确吸收指定来源与结果 | `.agents/roles/RESEARCH_SCOUT.md` |
| `hmasd-research-innovator` | Sol / max / read-only | 从指定来源形成算法启发 | `.agents/roles/RESEARCH_INNOVATOR.md` |
| `hmasd-research-principles-analyst` | Sol / max / read-only | 建设性数学、RL/MARL 和机制分析 | `.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md` |
| `hmasd-research-critic` | Sol / max / read-only | 对已经形成的候选作一次对抗性科学批评 | `.agents/roles/RESEARCH_CRITIC.md` |

对应 profile 位于：

```text
.codex/agents/hmasd-research-scout.toml
.codex/agents/hmasd-research-innovator.toml
.codex/agents/hmasd-research-principles-analyst.toml
.codex/agents/hmasd-research-critic.toml
```

这些角色提供科研意见，但不接管 Explorer 的候选排序、研究状态或外审
intake。科研严格性不能被误写成固定多代理流水线；Explorer 按问题需要
选择子代理。

## 7. WDM 子代理

| agent type | 模型 / effort / sandbox | 职责 | 角色路径 |
|---|---|---|---|
| `hmasd-workflow-auditor` | Luna / high / read-only | 有界影响映射或变更后机械核对 | `.agents/roles/WORKFLOW_AUDITOR.md` |
| `hmasd-workflow-implementer` | Luna / high / workspace-write | 一个确认计划中的非重叠文件族 | `.agents/roles/WORKFLOW_IMPLEMENTER.md` |
| `hmasd-workflow-reviewer` | Sol / xhigh / read-only | 只在权限、路由、模型锁定、动作脚本等高风险变化时审阅一次 | `.agents/roles/WORKFLOW_REVIEWER.md` |

对应 profile：

```text
.codex/agents/hmasd-workflow-auditor.toml
.codex/agents/hmasd-workflow-implementer.toml
.codex/agents/hmasd-workflow-reviewer.toml
```

子代理没有独立验收权。WDM 必须亲自处理语义交界、最终 diff、Git 和
reload。普通文档变化不应自动触发 Reviewer。

## 8. Claude 侧辅助入口

| 入口 | 指向 |
|---|---|
| `.claude/agents/hmasd-scout.md` | `.agents/roles/CODE_SCOUT.md` |
| `.claude/agents/hmasd-implementer.md` | `.agents/roles/IMPLEMENTER.md` + agile development Skill |
| `.claude/agents/hmasd-reviewer.md` | `.agents/roles/REVIEWER.md` |

Claude 入口中的 model/tool frontmatter 只负责启动；共享 charter 才定义
能力和边界。若两者冲突，应报告表面不一致，不应选择更严格或更复杂的一方
自行拼接。

## 9. 当前七个项目 Skill

| Skill | 使用者与用途 | 路径 |
|---|---|---|
| Agentify transport | Transport Operator 完成一个有序文件批次 | `.agents/skills/hmasd-agentify-transport/SKILL.md` |
| Agile research development | CPM、Implementer、Verifier 的实现和 proof-sized 验证合同 | `.agents/skills/hmasd-agile-research-development/SKILL.md` |
| Collaborative workflow design | WDM 把用户请求或 defect 变成一个完整计划 | `.agents/skills/hmasd-collaborative-workflow-design/SKILL.md` |
| Workflow change audit | 计划确认后由 WDM 实现、验证、Git 和 reload | `.agents/skills/hmasd-workflow-change-audit/SKILL.md` |
| Independent research exploration | Explorer 的来源吸收、创新、原则分析和候选研究 | `.agents/skills/hmasd-independent-research-exploration/SKILL.md` |
| Independent research Pro review | Explorer 形成外审问题和 batch 请求，不执行页面传输 | `.agents/skills/hmasd-independent-research-pro-review/SKILL.md` |
| Explorer project validation | 将成熟 Explorer 候选转成项目 toy-validation 建议包 | `.agents/skills/hmasd-explorer-project-validation/SKILL.md` |

Skill 审计要回答：正常路径是否足够短？是否只有一个简单 fallback？
Skill 是否悄悄增加了角色没有的权限？是否复制了 role/profile 的内容？

## 10. 重要公共合同与工具路径

```text
docs/project/CURRENT_WORK.md
docs/project/SESSION_WORKSPACE_CONTRACT.md
docs/project/EVIDENCE_COMPLEXITY_POLICY.md
docs/project/ALGORITHM_PRINCIPLES.md
docs/project/SCIENTIFIC_ASSERTION_AUDIT.md
docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md
docs/project/AGENT_CONTEXT.md
docs/session-workspaces/workflow_design_manager/WORKFLOW_DEFECT_QUEUE.md
.agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py
scripts/hmasd_workspace_ticket.py
scripts/hmasd_workspace_boundary_guard.py
```

`CURRENT_WORK.md` 是公共索引，不是所有角色都应读取的全局状态文件。
WDM 只读取自己的 workflow records；Explorer 默认不读取它；CPM 按自己的
charter 管理项目状态。

## 11. 历史上反复出现的问题

### 11.1 重复指令源和过期引用

曾经存在 `AGENTS.md`、`CLAUDE.md`、角色文件、Skill、profile 各自保存一套
流程的情况，导致已退休角色、错误 Python 路径和不存在的 Skill 继续影响新
session。审计时检查：一个规则是否有且只有一个定义者，其余表面是否只引用。

### 11.2 结果所有权与能力不匹配

角色被要求完成任务，却看不到必要页面、进程、文件或状态，也没有普通可逆
动作权。模型随后只能机械返回 `BLOCKED` 或猜测。对每个角色使用第 12 节的
六项能力检查，不能用禁止条款代替能力设计。

### 11.3 把智能角色写成脆弱状态机

过密的终态、身份字段、恢复分支和禁止清单降低了模型判断能力。特别是网页
传输曾因稳定键、哈希、会话身份和重复恢复合同叠加而长期空转。若失败后只需
重试，不应建立永久状态机；让工具保存机械状态，让角色观察后判断。

### 11.4 过度身份与哈希验证

内容 SHA、字节数和多层 identity receipt 曾把简单传递任务变成控制面工程。
现行工作流禁止把 hash、digest、byte count 或 fingerprint 用作路由、handoff、
恢复和验收条件。Git revision 只作源码定位。

### 11.5 Reviewer 只找漏洞、不计算代价

过去的 Reviewer 倾向提出更多 gate、测试和边缘情况，却不比较正常路径风险与
代码量、维护、时间和迭代延迟。现行 Reviewer 只有在修复净收益明显为正时才
提出 actionable finding；可信研究仓库不按对抗性商业安全系统设计。

### 11.6 跨 session 控制权漂移

固定 session 路由、保存 model/effort、语义 relay 和多层批准曾让控制权与执行者
分离。当前跨任务消息使用 Codex 原生 task ID，发送时不覆盖 model/thinking；
每个持久角色保留自己的业务权，只有工作流表面交给 WDM。

### 11.7 把批处理拆成逐项协调

外审和重复机械任务若天然是有序 batch，应使用一个持久 batch 文件和一个聚合
结果。不要因为删除复杂状态机而同时删除 batch 边界，也不要用十五次跨 session
对话替代一个文件清单。

### 11.8 一次事故立一条永久法律

一次性失败只修根因并记录事实。至少两次独立复发才考虑永久规则。新机制必须
说明删除什么，并以净活跃行变化、正常路径成本和用户可见收益审查。

## 12. 角色能力六项检查

对每个被审计角色写出六个简短答案：

1. **Outcome**：它实际拥有哪个结果？
2. **Observation**：完成结果必须看到哪些页面、文件、状态或诊断？
3. **Action**：必须允许哪些普通、可逆动作？
4. **Judgment**：哪些局部判断应由模型自己完成，而不是编码成状态机？
5. **Recovery**：一个正常 fallback 是什么？何时才真正缺少权限？
6. **Completion**：什么用户可见证据说明任务完成？

典型缺陷包括：拥有结果却不能观察；允许观察却不能修复；要求判断却禁止读取
判断依据；把可恢复错误标为永久 blocked；完成条件只是内部 token 而不是用户
要求的结果。

## 13. 成本与比例性检查

任何审计建议先回答：

- 它对应哪个已观测、可复现的正常路径失败？
- 失败后果是否不可逆或高代价？若只是重试，不得建机制。
- 最小根因修复是多少行、多少文件、多少长期认知成本？
- 新规则会删除哪段旧机制或重复文字？
- 修复的预期收益是否明显超过代码、耦合、维护、wall-clock 和迭代延迟？

低于行数预算不代表自动合理。预算是上限，不是鼓励用满。

## 14. 不应默认提出的方案

- 新增 Controller、Monitor、dispatcher、semantic relay 或 approval role；
- 新增固定路由表、全局 lease、跨 session 状态机；
- 为可重试网页动作增加身份 ledger、哈希 fence 或多重 receipt；
- 每个任务都强制 Reviewer、全套测试、成本报告或二次验收；
- 为旧接口增加 compatibility wrapper；Git 已经是历史档案；
- 因理论 hostile input 增加商业安全级防御；
- 仅为“更完整”而增加字段、终态、模板或文档。

## 15. 推荐审计输出

Claude 的审计结果应保持短而可执行：

```text
AUDIT_SCOPE
- inspected paths
- active authority source

ACTIONABLE_FINDINGS
- severity, exact path/anchor, observed normal-path effect, smallest repair,
  proportionality rationale

STALE_OR_DELETION_CANDIDATES
- exact inactive surface and evidence that no active consumer remains

ACCEPTED_RESIDUAL_RISK
- issue not worth fixing and why

NO_NEW_MECHANISM
- confirm whether the recommendation adds a gate/state/registry; if yes, name
  the irreversible failure and deleted predecessor
```

严重度建议：

- **P0**：现行引用失效、权限冲突或角色无法完成拥有的正常结果；
- **P1**：能力、成本或单一事实源不匹配，已产生现实维护风险；
- **P2**：legacy 张力，无当前失败，只在 touched 时收缩；
- **Residual**：真实但收益不足以覆盖修复成本，不行动。

审计建议是 advisory input。只有 WDM 修改和验收工作流控制面；Claude 不应
直接修改这些文件，除非用户明确将它置于 WDM 执行角色并遵循现行合同。

