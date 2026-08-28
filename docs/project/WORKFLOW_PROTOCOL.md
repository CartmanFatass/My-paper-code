# HMASD native Codex workflow

Workflow revision: 2026-08-28.1

本文是 HMASD 唯一控制 authority。HMASD 直接信任 Codex Desktop 提供的可见 task ID、
history、status、parent/child relation、create/send/read/wait、同 task 继续、archive 与
worktree。项目不对这些产品事实再做身份认证，也不建立恶意参与者或本地篡改 threat model。

## 1. Topology and roles

长期同级 task 只有 Root、Workflow-Clerk、Portfolio、`EM/<direction>` 与
`CM/<direction>`。不使用 generation。Task ID 是真实身份，title 只是人类标签；出现两个
候选时停止发送并请用户选择。

- **Root**：永久用户入口；处理 shared-core、用户材料、task 冲突、协议矛盾和最终跨方向
  Git 集成。
- **Workflow-Clerk**：唯一长期协调 task；使用 native list/read/create/send 查找、创建、
  继续和路由 task。它不解释科研/工程结果，不维护第二状态机。
- **Portfolio**：维护 considered set、lifecycle、priority、capacity 和跨方向投资判断。
- **EM**：直接冻结问题、创新、原则分析、综合、修订、设置 claim ceiling/discriminator，
  并写方向科研 authority 与 research state。
- **CM**：直接理解代码、实现、测试、普通验证、解释工程证据、写 engineering state 并完成
  Git 收尾。

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
```

```text
[RESULT]
Direction: <id or shared>
Outcome: DONE | WAITING | FAILED
Next: EM | CM | PORTFOLIO | ROOT | SAME | NONE
Summary: <decision or completed outcome>
Refs: <durable refs and Git facts>
Blocker: <required for WAITING/FAILED, otherwise none>
Reentry: <required for WAITING, otherwise none>
```

```text
[CONTROL]
Action: PAUSE | RESUME | CANCEL | REPLACE | RELOAD
Direction: <id or shared>
Reason: <why>
Updated at: <timestamp>
Replacement: <required only for REPLACE; objective and Effects>
```

`Outcome` 与 `Next` 正交。Clerk 只按显式 `Next` 路由，不从 Summary 猜责任。ACTIVE direction
不能 `Next: NONE`；只有 Portfolio 已关闭的方向可以 NONE。

固定 top-level edges：Root → Clerk；Clerk → Root/Portfolio/EM/CM；Root/Portfolio/EM/CM →
Clerk；participant → Clerk → affected participant 的 CONTROL。EM、CM、Portfolio 不直接互发。

## 3. Clerk routing and liveness

Clerk 每个 event turn：

1. 从 native task list/history 确认当前 task 与输入；
2. 按 `Next` 找到或创建当前协议 task；
3. 发送一个 bounded WORK 或 CONTROL；
4. 在 final 前对本 turn 新到达输入做一次 bounded drain。

Clerk 不验证身份、不维护 attempt/retry ledger、owner cache、cursor、receipt 或 release
adoption，不常驻轮询，也不自动 retry。WAITING 默认无 heartbeat；只有存在明确可观察条件且
用户希望自动复查时，才为当前责任 task 使用 Codex 原生 heartbeat。

Stopped/idle 且当前 WORK 尚未完成时继续同一个当前协议 task。Native task 能力不可用时停止
受影响动作并报告，不从本地文件或数据库重建 topology。

## 4. Milestone memory

EM 与 CM 各自只维护一个 current snapshot：

- EM：`docs/research/candidates/<direction>/workflow/research/state.json`
- CM：`docs/research/candidates/<direction>/workflow/engineering/state.json`

共同字段为 `direction, role, revision, updated_at, milestone, status, completed_summary, refs,
blockers, reentry_condition, next_action`。EM 另有 `claim_ceiling, next_discriminator,
research_cycle`；CM 另有 `worktree, branch, changed_paths, verification_summary, run`。

EM milestones：`SCOPE_FROZEN`、`SYNTHESIS_READY`、`REVIEW_RESOLVED`、`HANDOFF_READY`。
CM milestones：`SCOPE_FROZEN`、`CANDIDATE_READY`、`REVIEW_RESOLVED`、
`RUN_OR_HANDOFF_READY`。Status：`ACTIVE | WAITING | FAILED | COMPLETE`。

只有上下文消失会导致重做有实质成本的工作，或可能重新作出不同 material judgment 时，才
跨越 milestone。跨越后立即用 `hmasd_state.py update` 原子覆盖 snapshot；revision 加一并更新
时间。Leaf return、单次测试、普通 lookup、单文件写入或工具成功本身不是 milestone。

恢复顺序：role skill、本文、native WORK/CONTROL history、direction authority、state refs、
owned-path diff、Git facts。State 是最后接受的 milestone；其后的 dirty work 是 in-flight，
必须保留。无法判断修改归属时停止对应 path，不自动 reset、checkout 或删除。

旧 state 不迁移。新协议下首次创建 EM/CM 时由 owner 根据当前 authority 写全新 state；
REGISTERED/CLOSED direction 不预建空 state。

## 5. Manager-direct work and leaves

Manager 默认直接完成本职工作。正常 slice 预期 0–2 个 leaves；agent tree 固定
`max_depth = 1`、`max_threads = 8`。

### 5.1 General chore leaf

`hmasd-general-leaf`（Luna xhigh）用于与当前主判断弱耦合、可精确界定的非主线任务，例如
论文/资料下载、文件整理、机械格式转换、fixture 生成、独立清单、低风险杂务或正交检查。
Root、Portfolio、EM、CM 都应主动把这类工作卸载给它，以减轻主 session 的上下文与注意力
压力。Parent 必须给 exact objective、inputs、owned paths、Effects、output shape 和 stop
condition；leaf 不得作 owner judgment、扩大 scope、commit/push、联系 top-level task 或再
delegate。

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

## 6. Material research cycle and External Pro

新 direction、mechanism/comparator/discriminator、可能实质提高 claim ceiling 的变化、新结果
推翻核心假设或 Portfolio 要求重估时，EM 开启新的 material cycle。事实补充、措辞修订、
claim 收窄、工程结果录入或同一问题继续不新开 cycle。

每个 material cycle 的固定顺序：

1. EM 写 `SCOPE_FROZEN`；
2. 必要的 Scout evidence 完成；
3. `hmasd-external-pro-transport` 以 `Mode: INNOVATOR` send-once；
4. EM 综合并写 `SYNTHESIS_READY`；
5. 同一 transport 以 `Mode: CONVERGENCE` send-once，要求独立、adversarial convergence；
6. EM 处理意见并写 `REVIEW_RESOLVED`；
7. 决定 CM、Portfolio 或 handoff。

每个 cycle 最多一次 Innovator 和一次 Convergence；修订不自动重审。State 的 current
`research_cycle` 只保存 `label, opened_at, reason, pro_innovator, pro_convergence`，两项 status
为 `PENDING | COMPLETE | WAITING | WAIVED`，不保存历史 ledger。

每个 material cycle 的两次 Pro 调用已获自动授权。以下情况必须回用户：非项目公开材料、
secret/个人数据、provider/账号/付费方式变化、超出两次、unknown send 后考虑新发送、用户暂停
外部 Effect。Unknown commitment 只观察不重发；明确未发送失败则 EM 进入 WAITING。用户可以
对 exact cycle 明确 waiver。不得用本地 Critic 或其他 provider 静默替代。

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
固定表格字段为 Direction、Lifecycle、Priority、Next role、Updated at、Reason/condition。
Lifecycle 只允许 `REGISTERED | ACTIVE | PARKED | CLOSED`，且只有 Portfolio 可以改变。

Portfolio 先原子更新该表，再向 Clerk 返回 RESULT。重大投资或关闭决定可写独立 Markdown
decision note；普通 priority 更新只改表。历史 decision note 必须清楚标为 historical，不能
作为 current workflow state。

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

Shared checkout 保持 `main`；不在其中 switch/checkout。Owner 只修改/stage owned paths，保留
其他修改，shared index mutation 串行。跨 top-level role handoff 且 refs 有 Git-visible 内容
时必须 commit；push 在用户要求远端同步、跨 worktree 集成或正式方向交付时强制。

用户直接控制 participant 时，该 task 向 Clerk 发送 CONTROL；Clerk 转发并停止新的相关
launch/send。已经发生或 commitment 未知的外部 Effect 继续观察到可判定状态。PAUSE/CANCEL
不等于 Portfolio lifecycle 变化。

不兼容任何旧控制层。旧 task、messages、state、scripts、schemas、prompts 或 fixtures 不读取、
不迁移、不翻译；问题一律 fix-forward。
