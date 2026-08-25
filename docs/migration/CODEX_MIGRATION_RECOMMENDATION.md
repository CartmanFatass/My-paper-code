# HMASD OMP 工作流迁移到 Codex 的当前建议

## 1. 决策状态

状态：适配层先在本地 `omp/workflow` 完成，随后按用户指令选择性集成到本地
`main`；`omp/workflow` 仅作为迁移源，不推送。首轮真实 peer-task smoke 已完成，
重启后 depth/task-recovery 产品 smoke 仍待执行。本版取代此前两种假设：

- Root → EM/CM → leaf 的两级 Codex subagent 树；
- Root 兼任 Portfolio 决策者、Portfolio 退化为只读 Audit。

本迁移以 `omp/workflow@c5dd9801` 为已实现行为基线。OMP 已经建立了清晰的
科学、工程、文件、状态、run、Agentify 和 Git 权威；Codex 迁移只替换编排与
互动平面，不重新发明文件系统管理。

## 2. 修正后的核心认识

Root 的价值是低成本、稳定、可恢复的 orchestration。它可以拥有完成编排所需
的最高操作权限，但不适合作为高价值决策者。稳定工作流下，较低成本模型应能
按冻结 instructions 完成：task 创建/恢复、消息路由、等待、状态核对、worktree
调度、effect 去重、Git 集成和用户可见报告。

Portfolio 是另一种角色。它使用 Sol max，负责跨方向判断、方向 lifecycle、
优先级和是否进入 CM 工程工作的决定。它不是只读审查者；只是决策频率低，
不需要像旧拓扑那样持续持有并 dispatch EM。它由周期性触发或用户直接互动
唤醒，形成决定后发送 Decision Packet 给 Root，Root 再进行编排。

Root 也不是唯一入口。用户可以直接进入 Portfolio、EM、CM 或 Root task。
顶层 task 的意义是：互动可被保留、用户可以直接检查历史，并且每个角色拥有
完成其职责所需的完整操作权限。谁创建 task 不决定其语义 authority。

## 3. Codex 官方语义依据

当前 OpenAI Docs 支持把相关工作放在同一 project、为不同 outcome 使用独立
chat/task；这些 task 共享项目文件和指令，但保留各自会话上下文。每个 chat
也保留自己的 messages、results 和 goal。Subagent 适合一个 task 内有界、可
并行的独立工作；并行写入仍应隔离。

- [Projects and chats](https://learn.chatgpt.com/codex/projects)
- [Subagents](https://learn.chatgpt.com/codex/agent-configuration/subagents)
- [Long-running work](https://learn.chatgpt.com/codex/long-running-work)

跨 task 的 create/list/read/send/wait/pin/archive 和互动记录细节仍需在目标
Codex 安装上完成 smoke。产品能力不能在未验证前替代恢复合同。

## 4. 目标 task 平面

```text
HMASD local project
├── HMASD Root                         低成本 operational orchestrator
├── HMASD Portfolio                    Sol max，跨方向决策 task
├── EM/<direction-id>/g<generation>    方向科学 task
└── CM/<direction-id>/g<generation>    方向工程 task
```

四类 task 同级、可直接互动：

- 用户可以把新信息、约束或决定直接发送到其所属角色；
- 会话保存互动来源；
- material 决定仍必须进入其所属 durable authority，才能被其他 task 在恢复后
  可靠消费；
- task 创建关系不是权限继承或组织上下级。

Portfolio、EM、CM 可长期保留其可信 generation，并在没有工作时 idle；它们
不是常驻 inference loop。Portfolio 的低频不等于每次审查后必须销毁，也不等于
只读。是否轮换 generation 由身份、checkpoint、上下文可信度和任务语义决定。

## 5. 决策权、操作权与入口

| 角色 | Decision Authority | Operational Authority | 用户可直接互动 |
| --- | --- | --- | --- |
| User | 全局最高；可修改任何冻结范围 | 可授权任何范围内效果 | 是 |
| Portfolio | 跨方向选择、排序、生命周期、CM/资源投入 | 写 Portfolio 权威；形成并发送 Decision Packet | 是 |
| EM | 一个方向内的科学判断、结论和研究下一步 | 写该方向科学与 research/external 状态 | 是 |
| CM | 一个方向内有界工程范围的技术判断 | 写 engineering state，协调实现、验证和 Operator | 是 |
| Root | 无 material Portfolio/科学/工程决策权；仅做机械调度选择 | 最高工作流操作权限、跨 task 编排、恢复和最终集成 | 是 |

Root 可以按 instructions 做低风险机械选择，例如选择空闲并发槽、复用匹配
task、等待已知 effect、执行无冲突集成。遇到需要改变 Portfolio、科学或工程
含义的分支，Root 必须向相应 authority 或用户返回，而不是自行补全。

“最高权限”在这里指 tool/sandbox/workspace/task-management 能力，不等同于
Decision Authority。

## 6. 决策与编排流

### 6.1 Portfolio 驱动

```text
EM durable result(s)
  -> Portfolio 周期性盘点或用户直接互动
  -> Portfolio 形成跨方向/CM 决定
  -> Portfolio 写 PORTFOLIO.md + registry（如有 lifecycle 变化）
  -> Portfolio 向 Root 发送 Decision Packet
  -> Root 创建/恢复/通知相应 EM 或 CM 并等待结果
```

Portfolio 不直接持有或 dispatch EM/CM。它决定“做什么、为何做、优先级和边界”；
Root 决定“如何可靠地路由、等待、去重和整合”。

### 6.2 用户直接互动

- 用户与 Portfolio 的互动可以形成跨方向或 CM 决定；Portfolio 记录 durable
  decision 并通知 Root。
- 用户与 EM 的互动可以改变该方向的科学问题或证据边界；EM 更新 direction
  authority 并通知 Portfolio/Root。
- 用户与 CM 的互动可以改变工程 scope；CM 更新工程 authority，并在改变科学
  意义时返回 EM/Portfolio。
- 用户与 Root 的互动可直接启动、暂停、恢复或重排已决工作；若内容要求新的
  material 判断，Root 路由给对应 authority。

## 7. 单层 subagent 平面

每个顶层 task 内最多一层 direct subagent；所有 direct subagent 都是叶子：

```text
Root task
└── project/code scout / verifier / recovery / integration support

Portfolio task
└── research scout / critic / principles analyst / optional reviewer

EM task
└── research scout / innovator / critic / principles analyst /
    code scout / artifact writer / external transport

CM task
└── project/code scout / implementer / reviewer / verifier /
    experiment operator / research scout
```

Codex 配置目标是 `max_depth = 1`。Root 不通过 subagent API 创建 Portfolio、
EM 或 CM。`.codex/agents/` 保留 main 分支注册的 18 个角色配置，其中 15 个是
直接叶子角色，另有 3 个兼容性的 manager/recovery 配置；四类顶层 task 仍使用
bootstrap instructions/skills，不从该目录创建。

2026-08-25 的第一次 depth smoke 复用了配置落地前已启动的 Codex 宿主；虽然
观察到 nested child 完成，但该结果不能验证重启后 `max_depth = 1` 的约束。当前
main-compatible 配置保持不变，clean cutover 前必须完全重启 Codex，再从新 Root
task 重做 direct-leaf/nested-child smoke。官方 config schema 对 V2 的说明与预期
重启行为存在差异，也应以同一次 fresh-host 结果一并核对；在此之前状态是
`UNVERIFIED_AFTER_RESTART`，不是 hard-gate failure。

Delegation 只用于并行和上下文隔离，不是必须满足的工作流形状。

## 8. OMP 文件与命名管理核查结论

OMP 的文件管理应被视为迁移的规范来源，而不是待重做模块。它同时存在于
`.omp/AGENTS.md`、各 agent/Skill instructions、schema validator、CLI 和 focused
tests 中。

### 8.1 Durable authorities 与 writer

| 事实 | 路径/权威 | Writer |
| --- | --- | --- |
| Portfolio 目标、排序、综合、lifecycle 理由 | `docs/research/portfolio/PORTFOLIO.md` | Portfolio |
| lifecycle 与依赖 | `docs/research/portfolio/workflow/registry.json` | `Portfolio` |
| 方向科学 | `docs/research/candidates/<id>/DIRECTION.md` | `EM-<id>` / exact Artifact Writer assignment |
| research action/state | `<direction>/workflow/research/state.json` | `EM-<id>` |
| engineering state | `<direction>/workflow/engineering/state.json` | `CM-<id>` |
| external-review index | `<direction>/workflow/external-review/index.json` | `EM-<id>` |
| accepted result pair | `<direction>/results/<result-id>.md/.json` | `EM-<id>` |
| local run | `temp/directions/<id>/exp/<run-id>/` | `Operator-<run-id>` |
| runtime task/worktree refs | ignored runtime JSON | Root |
| Agentify commitment | Agentify ledger | Agentify only |
| verified archive import与最终 Git integration | exact helper / Git | Root |

`hmasd_state.py` 已机械验证 Portfolio、EM、CM、Operator writer 与精确 path；
expected-revision CAS、原子 replace、symlink/path refusal 和 focused tests 已存在。
Codex 适配不得把这些边界降级为 prompt-only 约定。

### 8.2 稳定命名

- direction ID：`[a-z0-9][a-z0-9_-]{1,63}`；
- logical identity：`EM-<direction-id>`、`CM-<direction-id>`；
- task title 只是上述 logical identity 的可见映射，不替代 identity；
- worktree：`<sibling-root>/<direction>-<kind>-<assignment>`；
- assignment branch：`omp/<direction>/<kind>/<assignment>`；
- disposable output：`temp/directions/<direction-id>/exp/` 或 `test/`；
- external round：`docs/external-review/directions/<direction-id>/<round-id>/`。

CM 的长期 identity 仍按方向，而不是每个 scope 新造不同 writer。一个 CM task
可在兼容 checkpoint 下处理连续的有界 scope；不兼容时轮换 generation。每个
并行 assignment 仍使用独立 worktree/branch 和 allowed paths。

### 8.3 Assignment ownership

- Implementer 只写 initial assignment 明确拥有的文件；material scope 变化要
  停止或替换 leaf。
- Artifact Writer 只写一个精确命名 artifact。
- CM 只写 provisioned worktree 的 assignment-owned paths 和 engineering state。
- Root integration helper 要求至少一个 `--allowed-path`，拒绝 dirty/stale/
  conflict/out-of-scope/symlink candidate。
- raw runs、runtime refs 和 generated artifacts 保持 ignored；durable 结果只按
  既有 promotion contract 进入 tracked paths。

因此新计划删除“重新设计 peer-task 文件所有权”的工作项，只保留“把同一 OMP
assignment contract 注入 Codex 顶层 task/leaf，并证明 helper 仍强制执行”。

### 8.4 当前 Windows Codex host 的适配缺口

OMP 文件合同完整，但当前实现是 Linux-native，不能声称在 Windows Codex
worktree 中可直接运行：

- `hmasd_state.py` 与 `hmasd_worktree.py` 使用 `fcntl`；Windows 项目 Python
  没有该模块；
- 当前 Git 全局 `core.autocrlf=true` 把 authority Markdown 检出为 CRLF，而
  registry SHA 对应 Git blob 的 LF bytes；对工作树文件做 LF byte normalization
  后 SHA 与 registry 完全匹配，证明是 host checkout 表示差异而非内容漂移；
- Windows Git 创建的 worktree `.git` 文件包含 Windows gitdir，WSL Git 不能把
  该 worktree 当作原生仓库，因此不能把“Windows task + WSL helper”当作零成本
  替代。

Codex migration 必须选择一个一致的执行面。当前优先方案是保留 Windows Codex
和 Windows sibling worktrees，增加等价的 cross-platform short-lock adapter，并
通过 `.gitattributes` 或同等 checkout contract 强制 durable authority 使用 LF
exact bytes。不得在 validator 内静默把任意内容规范化后冒充 exact-byte authority。
Windows sibling worktree 根固定为 `C:/Projects/HMASD-worktrees`；不把 Linux/WSL
路径映射字符串传给 Codex。`<direction>-<kind>-<assignment>` 命名和全部安全检查
保持不变。

## 9. 跨 task 记录与 Decision Packet

每个 material 互动需要两个层次：

1. **Conversation provenance**：Codex task 保存用户和角色的直接互动，方便用户
   复查原因与推理。
2. **Durable decision**：Portfolio/EM/CM 将结论写入其既有 authority，并发送
   一个包含引用、revision、SHA、scope 和下一动作的 Decision Packet。

Decision Packet 不是 approval token，也不新建 tracked handoff 文件。通常使用
跨 task 消息加已有 durable file refs；只有原 OMP contract 已要求 durable artifact
时才写文件。Root 校验引用后编排，不重新评估决定内容。

## 10. 需要翻译与不应迁移的内容

### 需要翻译

- `.omp/AGENTS.md`、RULES、Skills → 根 `AGENTS.md` 与四类顶层 task bootstrap；
- OMP Hub job/message → Codex peer task create/list/read/send/wait；
- Root→manager→leaf lineage → peer task + task 内 direct leaf；
- OMP runtime job refs → 可重建的 Codex task refs；
- Dashboard Agent Hub tree → 顶层 task 视图和各 task 内 subagent 视图。

### 不应迁移

- `max_depth=2`；
- Portfolio、EM、CM 作为可 spawn custom agent；
- Root 兼任 Portfolio/科学/工程决策者；
- Portfolio 只读、一次性归档的 Audit 模型；
- OMP Advisor、Hub lineage 或 autoResume 的一比一仿制；
- 为 Codex 另造文件命名、writer、worktree 或状态 authority；
- “Root 是唯一入口”约束。

## 11. 保留的硬边界

1. 精确解析破坏性目标并限制在用户范围内。
2. 永不暴露秘密。
3. 外部 send 每个 operation 最多一次；commitment unknown 禁止重发。
4. 每个 result-bearing command 只有一个 Experiment Operator 直到终态。
5. unsafe memory 必须缩减、分批或分片。
6. 预计超过 7200 秒的本地结果命令先尝试性能合理性审查，再请求用户批准。
7. 不静默改变科学、数值、RNG、checkpoint、bit identity 或 external-effect
   语义。
8. 角色、task、subagent、测试、审查、Dashboard、hash 和历史文档都不是授权
   令牌。
9. OMP 与 Codex 在 cutover 后不得同时调度同一方向、run、external operation
   或 Git integration。

## 12. Material checkpoint Git 持久化

Codex 迁移必须补上 OMP 实际运行中缺失的 checkpoint 执行约束。触发器是
event-driven，而不是定时器或后台模型轮询：

- research/engineering round 完成；
- accepted result promotion；
- terminal run evidence promotion；
- external prompt/archive readiness；
- Portfolio lifecycle material change；
- schema migration。

每个顶层工作 task 在 material completion 时向 Root 返回 exact changed paths 和
durable refs。Root 必须在依赖该 checkpoint 的下一次 dispatch 或 Root stop 之前，
验证路径、按 exact allowlist 暂存，并提交到 `main` 的本地 checkpoint。只有用户
对该次 effect 明确授权时才推送；本次迁移不得推送本地 `omp/workflow`，也没有
获得推送 `main` 的授权。自动 checkpoint 禁止 `git add -A`；无关用户修改保持 unstaged，
同一路径混合 ownership 时返回冲突。runtime refs、raw runs、generated logs、
secrets 和未验证 source 不得进入 checkpoint。

普通中间事件可以批量进入下一 checkpoint，但已完成的 material checkpoint
不得跨越一个 Root wake-cycle 仍未 commit。推送前 fetch 并比较 remote tip；
push outcome unknown 时先 fetch/reconcile，禁止盲目重推或把它混入后续
checkpoint。Codex 工作 task 和 leaf 不自行 commit/push；Root 保持唯一 Git
integration 与 checkpoint writer。

## 13. 结论

目标模型是“同级高权限工作 task + 单层执行 subagent”：Root 便宜而可靠，
Portfolio 稀疏但强，EM/CM 各自保有专业决策权，用户可以直接与任一 task 互动。
Root 负责 faithfully orchestrate 已形成的决定，不成为所有决定和上下文的中心。
OMP 已验证的文件路径、命名、writer、worktree、run 和 effect 管理完整保留，
并新增 material checkpoint 的 exact-path local-commit 约束；push 始终是单独的
显式 effect，防止再次累积大批未提交修改或误推迁移源分支。
