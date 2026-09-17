# HMASD 控制面总览

描述性参考，不是 operating authority、启动门禁或必读 preload。核对基点：`b24c4c8be1387b3f0963c8ce9229581a82001acd`；本次工程配额修改不改变下述 runtime 分工。未解决的跨文件冲突见[前后审计](../Claude_docs/reviews/CONTROL_PLANE_REWRITE_AUDIT_20260916.md)。仓库声明、生成结果和已运行会话的有效状态不是同一件事。

## 1. 权威、入口与生成关系

```text
Owner 的实际指令／暂停
  └─ docs/project/OPERATING_CONSTITUTION.md       唯一 operating governance
       ├─ AGENTS.md → 最近目录的 AGENTS.md        入口／局部执行方法
       ├─ CLAUDE.md → @AGENTS.md                 Claude 入口
       └─ docs/research/RESEARCH.md               方向、lead、pause、standing

.agents/skills/hmasd-*/                          手工维护：共享方法、引用、helper
.codex/agents/*.toml                             手工维护：角色正文＋Codex 原生配置
.claude/agents/*.md 的 YAML frontmatter          手工维护：Claude 模型／工具／描述
tools/publish_claude_control.py                  手工维护：生成规则＋runtime 适配
  ├─ .claude/skills/hmasd-*/                     生成副本，包括递归复制的旧 helper
  ├─ .claude/agents/*.md 正文                    Codex 正文＋Claude 适配
  ├─ hmasd-research-hub/SKILL.md                 DM 正文＋Claude 专用替换
  └─ hmasd-pro-transport/SKILL.md                transport 方法别名
```

| 面 | 维护位置 | 边界 |
| --- | --- | --- |
| 权威／状态 | [Constitution](OPERATING_CONSTITUTION.md)、[RESEARCH](../research/RESEARCH.md) | 状态标签不解除 owner pause；旧结果不产生新授权。 |
| 自动／任务入口 | [AGENTS](../../AGENTS.md)、[CLAUDE](../../CLAUDE.md)；`docs/`、`experiments/`、`scripts/`、`tests/`、`envs/`、`ha_ctse_process/` 的 AGENTS | 局部入口也是迁移面；`docs/AGENTS.md` 仍含旧 card/intake 要求。 |
| Codex 默认值／注册 | [.codex/config.toml](../../.codex/config.toml)、`.codex/agents/*.toml` | Root 模型由 app 选择；原生 thread 上限不是方向额度。 |
| Claude 默认值／注册 | [.claude/settings.json](../../.claude/settings.json)、agent frontmatter | frontmatter 不从 Codex 生成；仓库设置不等于用户全局或运行中有效配置。 |
| 方法／发布 | `.agents/skills/`、[publisher](../../tools/publish_claude_control.py)、[publication tests](../../tests/skills/test_control_publication.py) | 源修改后生成正文；`--check` 只检查预期输出，不证明语义、孤儿清理或会话采纳。 |
| 机器／服务路由 | [.codex/hmasd-compute.toml](../../.codex/hmasd-compute.toml)、[hmasd-transport.toml](../../.codex/hmasd-transport.toml) | transport 配置仍有旧 registry/binding 字段；不能据此恢复旧治理。 |

## 2. 两个 runtime 与 roles→skills

| 维度 | Codex | Claude |
| --- | --- | --- |
| 方向责任 | Root 协调 DM children；owner 选择三个 DM 的 soft ceiling，不要求填满 | session 自身是单方向 DM；同方向不能由两边同时驱动 |
| Implementer | `HMASDImplementer`，Sol/high；DM 接受 diff | `hmasd-implementer`，Opus；high effort 写在描述中，未见原生 effort 字段 |
| 结果启动 | DM 自己或受派 Operator | 入口指定只有 `hmasd-experiment-operator` 启动 |
| 观察回传 | 可复用 Monitor，直接 adoption/terminal 给 DM | Operator 回 session，session 派 Tracker 做有界观察窗口 |
| Pro | DM 所属 Transport child | session 使用 Agentify 或派 Sonnet transport |
| main／共享索引 | Root 声明拥有 main/index 并更新 RESEARCH | 生成 hub 也指示自行集成 main、更新 RESEARCH；并发边界尚未统一 |
| 审阅隔离 | Reviewer/Critic TOML 声明 read-only sandbox | Reviewer 描述只读，但 tools 包含 Bash；不等于已验证的同等隔离 |

简称：science=`hmasd-scientific-tools`，engineering=`hmasd-research-engineering`，question=`hmasd-pro-research-prompt-author`，transport=`hmasd-chatgpt-pro-transport`；共享源均在 `.agents/skills/`。

| 角色／入口 | 方法连接 | 返回／权限 |
| --- | --- | --- |
| Codex Root | `hmasd-loop-dispatch`；owner review 用 `hmasd-portfolio-task` | 集成与共享依赖，不替 DM 接受科学结论 |
| Codex DM／Claude session | DM TOML／生成的 `hmasd-research-hub` → science、engineering、question | 方向端到端责任；Claude 没有另一个 Root/DM child 层 |
| Implementer | engineering＋L0 scope | diff、checks、偏差；不选科学、不启动结果、不发 Pro、不派子代理 |
| Reviewer | engineering；涉及科学含义时加 science | 返回具体失效路径；接受责任在 DM／Root |
| Transport | transport；问题来自 question 或 Portfolio | 发送、观察、完整答案收集，不做科学判断 |
| Operator／Monitor／Tracker | engineering 执行部分、角色正文、compute 配置 | Operator 启动／受派收集；Monitor/Tracker 仅观察 supplied handles |
| Scout／Verifier／ResearchCritic | 原生角色正文；Critic 用 science | 仍注册且 DM 列为 optional leaves，但 Constitution 封闭角色列表未解释其身份 |

Claude `hmasd-cm-scout` 与 `hmasd-research-scout` 同源于 Codex Scout，是别名而非两套独立职责。skill 的存在不授予角色或实验权限。

## 3. 状态、记录与退休面

| 类别 | 位置与作用 | 状态 |
| --- | --- | --- |
| 当前项目状态 | `docs/research/RESEARCH.md`：active/reserve/archived、lead、pause、standing、月度指标、owner review | 直接维护的唯一当前索引 |
| 科学记录 | `candidates/<direction>/NOTES.md`、`CLAIM_<slug>.md` | notebook／Pro 问答；确认前计划＋追加结果。FSD B01 以原冻结卡替代 claim note |
| 运行证据 | `runs/<direction>/<tag>/`：config、sha、summary/status、曲线、必要底层输出 | runner 生成；外部保存时保留可恢复位置；失败保留 |
| 操作状态 | supervisor handle、preflight 输出、monitor notice、Agentify operation/idempotency、tab、conversation URL | 防重复启动／Send 与收集所需；不是新增审批账本；已有位置／notebook 承载 |
| 旧输出接口 | `temp/directions/<id>/exp/`；旧 runner 与局部 AGENTS | 与新 `runs/` 的适用边界尚待澄清；不能搬迁冻结结果以满足新版布局 |
| 已删除的角色／skill | Sonnet clerk、Grok skill | 与 owner 后来重新加入的 Implementer 不同 |
| 退役但仍在当前目录 | `hmasd-owner-item` notice；prompt 的 `render_packet.py` 和旧 delivery refs；transport 的 binding/registry/archive helpers 及生成副本 | 日志记载删除 pending；publisher 仍复制。不能标作“已删除” |
| 历史证据／说明 | PORTFOLIO、APPROVED_SET、dossiers、tracking、cards/intakes/handoffs/pro_packets、`docs/agents/`、旧 project specs | 不再是新工作的规则来源；冻结对象保留原含义 |
| 迁移／审计 | `docs/project/CONTROL_PLANE_MIGRATION_*`、`docs/Claude_docs/changes/`、`reviews/` | 一次性事实记录；早先 Codex migration 证明不等于本次 Claude rewrite 的运行中采纳 |

## 4. 执行与 Transport 路径

```text
执行：owner 未暂停 → 当前方向／lead → 已声明实验与 fits
  → 实现 → 必要独立 review → DM 接受 → commit/push
  → compute 指定 node/interpreter、detached exact-sha checkout
  → 同一 supervisor command 内 admit-memory && runner
  → Codex：DM/Operator → Monitor adoption → terminal → DM/受派 Operator 收集
     Claude：Operator → session → Tracker 窗口 → session/受派 Operator 收集
  → 验证本地 artifact → DM 判读 → notebook / claim / RESEARCH

Pro：NOTES question → commit/push → pinned link + branch + answer section
  → Agentify dedicated non-protected tab → preflight → Send 一次
  → sendAttempted true/unknown：同一操作的非发送观察，不另发问题
  → 取得完整答案 → DM 读全文并记录采用／拒绝理由

Portfolio：owner 显式触发 → RESEARCH review section → 同一 Transport → owner Decision
  !! 当前 Transport 却把验收位置写死为 NOTES；审计已记录，尚未修复。
```

默认结果 node 为 `wsl_4070`，控制面为 `local_windows`；`ssh`／`scp` 与外部 `agent-task` 承载远程执行。`scripts/hmasd_resource_preflight.py admit-memory` 的实际安全底线仍是物理及有效可用内存各 4 GiB，不随工程行数／时长配额删除；`assess-run` 是另一路旧评估方式，不要混用。

Agentify 实现在仓库外 `C:/Projects/agentify-desktop/`。用户级配置、WSL/Windows 部署、运行中的 handles、会话缓存和外部工具 schema 未由本图验证。退役 repository registry 不等于删除工具自身的防重复操作状态。

## 5. 维护方式

当真实入口、来源归属、生成目标或执行／transport 路由变化时，在同一变更中更新相关行；不逐次实验维护，不建立定期审计、签字或新 registry。迁移时沿生产者→消费者核对具体版本，证据留在现有 PR／change/review。图与源不一致时核对源并修图，不用图创造规则。
