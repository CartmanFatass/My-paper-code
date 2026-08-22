# HMASD 当前控制面审阅 Prompt

请对以下远程 Git 分支做一次只读、证据驱动的控制面审阅：

- 仓库：`https://github.com/CartmanFatass/My-paper-code`
- 分支：`codex/control-plane-review-20260822`
- 当前审阅提交：`1102e23ef4f632dc6edafdbbbc1be08c5fab7f91`
- 基线提交：`7cc1a56c188d39af61ee70979adc4e2dd1e9c0ae`（`origin/aggressive`）
- 提交差异：`git diff 7cc1a56c..1102e23e`

不要依据本地工作区中未推送的文件作结论。尤其不要把 `.tmp/`、`runtime/`、`artifacts/`、实验 checkpoint 或锁文件当作控制面规范；它们是本地运行产物，不属于本次远程审阅提交。

## 审阅目标

判断当前控制面是否满足以下要求，并找出会改变结论的具体缺陷：

1. 角色、权限、任务分派、恢复、资源租约和 Git 边界是否在各文件之间一致。
2. 低侵入漂移控制是否真的把“观察事实、局部动作禁区、科学阶段延续、Root 决策类别”分开，避免子任务自行制造全局暂停、失败、阻断或权限结论。
3. assignment → intake → lease/resource → child execution → event wait → handoff → recovery → acceptance 的链路是否可执行、可恢复且不会重复发送或重复消费。
4. 控制面在进程崩溃、重启、重复事件、旧状态、provider 发送歧义和跨会话交接时是否保持原子性、可追溯性和 no-resend 约束。
5. 文档规范、`.codex` 配置、hooks、脚本和验收证据是否相互实现，而不是只在文档中宣称。
6. 当前三文件变更是否正确反映了最新的 provider/runtime authority boundary，是否引入了新的矛盾或遗漏。

## 一、角色路由与控制面入口

请先阅读：

```text
AGENTS.md
.agents/roles/ROOT.md
.agents/roles/CODE_PROJECT_MANAGER.md
.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md
.agents/roles/WORKFLOW_RECOVERY_MANAGER.md
.agents/roles/CPM_AGENTIFY_TRANSPORT_OPERATOR.md
.agents/roles/EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md
.agents/skills/hmasd-agentify-transport/SKILL.md
.agents/skills/hmasd-portfolio-operational-handoff/SKILL.md
.agents/skills/hmasd-workflow-anomaly-routing/SKILL.md
.agents/skills/hmasd-independent-research-exploration/SKILL.md
.codex/config.toml
.codex/semantic-actors.toml
.codex/hooks.json
.codex/hooks/hmasd_subagent_start.py
.codex/hooks/hmasd_subagent_stop.py
```

重点检查：角色层级是否与 `AGENTS.md` 一致；子 agent 是否可能越权写入、spawn、提交、推送、暂停方向或重复 provider 操作；hooks/config 是否会绕过 assignment、mailbox、lease 或 completion 约束。

## 二、项目策略与规范

```text
docs/project/LOW_INTRUSION_CONTROL_PLANE.md
docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md
docs/project/INCIDENT_SCOPE_AND_RECOVERY_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/project/CODEX_SUPERVISOR_DURABILITY_KERNEL_V1.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md
docs/project/CONTEXT_PRECEDENCE.md
docs/project/CONTEXT_PROMOTION_POLICY.md
docs/project/CONTEXT_RETENTION_POLICY.md
docs/project/CONTEXT_SOURCE_REGISTRY.toml
docs/project/EXECUTION_BACKEND_REGISTRY.toml
docs/project/EVIDENCE_COMPLEXITY_POLICY.md
docs/project/CODE_STRICTNESS_POLICY.md
docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md
docs/project/PROJECT_MAP.md
docs/project/CURRENT_WORK.md
docs/project/DECISIONS_INDEX.md
```

重点检查：

- “blocked/failed/ready/terminal”等历史词是否被错误当成全局状态机或 Root 决策。
- incident、authority boundary、no-resend、restart、lease 和 science-stage continuation 是否有明确适用范围。
- context precedence、canonical state、handoff packet 与 runtime/status stream 是否被混用。
- 资源或模型路由是否错误地改变角色权限、技术验收或科学所有权。

## 三、当前低侵入控制面验收证据

```text
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/BASELINE.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/RUNTIME_BASELINE.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/SYNTHETIC_ACCEPTANCE.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/LIVE_PILOT_REPORT.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/ROLLOUT_ACCEPTANCE.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/assignments/ASSIGNMENT_constraint_lint.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/assignments/ASSIGNMENT_native_execution_preflight.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/resources/MANIFEST_native_execution.toml
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/resources/RESOURCE_PREFLIGHT_native_execution.json
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/results/RESULT_asg_constraint_lint_seed.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/results/RESULT_asg_constraint_lint_seed_E1.md
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/results/RESULT_asg_native_execution_preflight.md
```

请区分：验收文档证明了什么、没有证明什么、是否仍可由仓库中的实现复现。不要把“页面可见”“文件存在”当作完整的 postcondition 或技术验收。

## 四、相关历史控制面验收与设计

```text
docs/research/workflow-runs/2026-08-20_control-plane-mcp-v1_1/ACCEPTANCE.md
docs/research/workflow-runs/2026-08-20_control-plane-mcp-v1_1/POST_V1_1_EXTENSION_PLAN.md
docs/research/workflow-runs/2026-08-20_control-plane-observability-v1/ACCEPTANCE.md
docs/research/workflow-runs/2026-08-19_codex-supervisor-durability-kernel/BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/SYNTHETIC_CONTROL_PLANE_REREVIEW_PROMPT.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/SESSION_HANDOFF.md
docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/ACCEPTANCE_REPORT.md
docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/CANARY_PROTOCOL.md
docs/research/workflow-runs/2026-08-15_codex-semantic-mvp/NATIVE_RUNTIME_STATUS.md
```

这些文件是历史证据和设计背景，不自动覆盖当前分支的最新规范；出现冲突时，请指出冲突双方、时间/版本和应采用的当前来源。

## 五、跨会话与当前状态锚点

```text
docs/research/workflow-runs/2026-08-11_five-round-research-team/CROSS_DIRECTION_PORTFOLIO_HANDOFF_SOL_ULTRA.md
docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md
docs/research/workflow-runs/2026-08-11_five-round-research-team/events_v2.jsonl
```

本次审阅提交只修改上述三个文件。请重点检查：

- `AUTHORITY_BOUNDARY`、`NO_SUPPORTED_NONRESTART_INJECTION`、`EXPLICIT_AUTHORITY_REQUIRED` 是否只作用于明确的 runtime/provider 操作，而没有扩大成方向级或科学级暂停。
- `DISH` exact Pro tuple release 是否与 no-resend、single-send、VNFC/VQFP held 和后续 intake 顺序一致。
- `events_v2.jsonl` 新事件是否与两个 reconciliation anchor 的字段一致，且没有把普通运行状态写成 Root 决策。

## 六、实现与可验证脚本

```text
scripts/hmasd_append_workflow_event.py
scripts/hmasd_workspace_boundary_guard.py
scripts/codex-semantic-mvp-enable.ps1
scripts/codex-semantic-mvp-disable.ps1
scripts/codex-semantic-mvp-test.ps1
```

请沿调用关系检查这些脚本是否尊重 assignment、workspace boundary、事件追加原子性、可重复执行和失败后的恢复边界。若实现位于其他文件，请给出实际被调用的路径，不要只引用脚本名称。

## 审阅输出格式

请只提交一份审阅报告，按以下顺序：

### 1. 总体结论

用一句话给出：`ACCEPT`、`ACCEPT_WITH_FINDINGS` 或 `REJECT`，并说明最主要依据。不要使用没有定义范围的“基本没问题”。

### 2. Findings

每条问题必须包含：

```text
ID: CP-001
Severity: P0 | P1 | P2 | P3
File: <仓库相对路径>
Section/Anchor: <标题、键名或函数名；必要时附行号>
Observed fact: <可直接从仓库验证的事实>
Requirement: <违反的控制面要求>
Impact: <会导致的具体错误、越权、重复操作或不可恢复性>
Reproduction/Evidence: <命令、输入、事件序列或文档交叉引用>
Minimal fix: <最小修复方向，不要直接改仓库>
```

P0/P1 只用于会导致越权、重复 provider 发送、错误科学暂停、不可恢复状态、数据丢失或验收失真的问题。仅凭风格偏好不要报 P1。

### 3. 跨文件矛盾矩阵

列出每个矛盾涉及的两个或多个文件、冲突字段/规则、当前应优先的来源，以及是否会改变运行时决策。

### 4. 未覆盖的验证

列出当前证据没有验证的关键路径，并给出最小可执行验证建议；明确哪些只是建议，不能被写成当前失败事实。

### 5. 结论边界

明确说明本次审阅没有判断的内容，例如科学算法质量、实验结果有效性、未推送的 runtime 状态或 provider 的远程页面内容。

## 审阅纪律

- 只读审阅，不修改、提交、推送、删除或重启任何资源。
- 每个结论都必须有仓库路径和可复核证据。
- 不把子任务返回的状态词直接提升为 Root 决策。
- 不把缺少某个观测、工具或刷新端点推断成整个方向暂停或科学失败。
- 不把历史文档、运行日志、临时目录或模型输出当作当前规范，除非明确说明其证据地位。
