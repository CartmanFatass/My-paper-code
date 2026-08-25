# HMASD OMP → Codex 控制面运行时迁移计划

## 1. 当前状态与目标

截至 2026-08-25，Codex project config/agents/skills、Root/Portfolio/EM/CM 顶层
task 原型、Windows state/run/worktree/external helper 兼容、Dashboard Codex task
投影，以及 OMP durable authority/effect contracts 的保留均已落地。Work package A
与 B 的 runtime ownership 代码也已实现：`runtime_tasks` 和
`runtime_worktrees` 均由 Root 通过 `hmasd_state.py` 的 schema/path/writer/expected-
revision CAS 管理；canonical worktree journal 是 `.codex/runtime/worktrees.json`；
`runtime_agents` 已退役；legacy `.omp/runtime/worktrees.json` 只允许校验后一次性
导入，不双写。legacy row 缺少 receipt 时必须在导入和 Git orphan 分类之前 fail
closed。

尚未完成的是产品级 fresh-host 与 ownership cutover 证据：

- `max_depth = 1` 尚未在完全重启后的 Codex host 上复验；旧宿主结果不计入验收；
- task restart/compaction、stale cursor、native task-list 重建和完整 Dashboard
  projection 仍需 fresh-host/集成证据；
- OMP shadow reconciliation、停止 OMP dispatch 和用户确认的 clean cutover 尚未
  执行。

### 当前实施状态（2026-08-25）

| Work package | 状态 | 证据边界 |
| --- | --- | --- |
| A — `runtime_tasks` schema/path/CAS | 已实现 | Root writer、canonical path、schema、duplicate/stale-revision 拒绝由 state CLI 与 focused tests 覆盖 |
| B — `runtime_worktrees` canonical/import | 已实现 | canonical-only、validated legacy import、receipt/reparse/Git facts fail-closed；legacy 不双写 |
| C — Root/skills/Dashboard 合同收口 | 已完成本次文档/测试收口 | runtime_agents retired、Root state writer、过渡期 fallback 与 dual-journal 规则已明确 |
| D — focused 集成验证 | 本次执行 | recovery receipt fail-closed regression 与 skill validation；全量矩阵仍由 Root 汇总 |
| E — fresh-host product smoke | 未完成 | 必须完全退出并重启 Codex 后验证 `max_depth = 1` 与 task recovery |
| F — shadow/clean cutover | 未完成 | 仍禁止 OMP/Codex 双 ownership；需 Root shadow 证据及用户确认 |

目标是把所有 live、可重建的运行时引用统一放入 `.codex/runtime/`，同时保持
Portfolio、direction、run、external archive、worktree/Git 的既有 durable/effect
合同不变。迁移完成前不得删除 `.omp`，不得让 OMP 与 Codex 同时拥有同一 effect。

## 2. 不变量

1. Tracked durable authorities 的路径、schema、writer 和 CAS 不迁移：
   `PORTFOLIO.md`、portfolio registry、`DIRECTION.md`、research/engineering state、
   external index、accepted results 保持原位。
2. `.codex/runtime/*.json` 是 ignored cache，不是 identity、decision 或 permission
   authority；丢失时只能从 durable facts、Git 和 native task listing 重建。
3. Runtime writer 只能是 Root，并通过 `hmasd_state.py` expected-revision CAS。
4. `.omp/runtime` 在过渡期只允许 validated read/import；一旦 canonical Codex
   document 存在，任何 helper 都不得再写 legacy path。canonical revision 正常推进
   后可以高于仍保持只读的 legacy revision；这不是 split-brain。
5. 未知 run、Git apply/push 或 external send 结果保持 observe-only，不因迁移重放。
6. Windows native Git/Python、canonical path、reparse refusal 和 exact LF bytes
   合同保持。
7. 当前 `.omp/runtime/{agents,worktrees}.json` 均不存在，因此本次代码迁移没有
   live journal 搬运效果；测试必须覆盖存在 legacy journal 的模拟场景。

## 3. 目标运行时布局

```text
.codex/runtime/                         # ignored, Root-owned, reconstructable
├── tasks.json                          # runtime_tasks, Codex peer task refs
└── worktrees.json                      # runtime_worktrees, Git worktree journal

.omp/runtime/                           # transition-only legacy source
├── agents.json                         # retired; native task list/tasks.json replaces it
└── worktrees.json                      # optional one-time validated import source
```

`runtime_agents` 不建立新的 Codex canonical writer。OMP manager/session mapping 被
native Codex task listing + `runtime_tasks` 取代；Dashboard 可在 cutover 前只读旧
`agents.json`，但 Root 不再生成它。

## 4. Work package A：runtime_tasks schema 与 CAS

Owner files：

- `scripts/hmasd_state.py`
- `scripts/schemas/hmasd_runtime_tasks.schema.json`
- `tests/hmasd_state_phase0_test.py`

实施：

1. 注册 `runtime_tasks` kind/schema。
2. 强制 canonical path 为 `.codex/runtime/tasks.json`，writer 为 `Root`。
3. 验证 `logical_identity` 唯一、kind、generation、title、thread/host/cursor、
   project root、worktree/checkpoint refs、lifecycle 和 timestamps。
4. Transition 使用 expected-revision CAS；同一 identity 的 kind/generation 不得
   静默改变，runtime handles/lifecycle/last_seen 可更新。
5. 允许 Root 增删可重建 task rows，但拒绝 duplicate identity、错误 writer、错误
   path、stale revision、symlink/reparse alias 和 tracked output。
6. 用现有 state CLI 初始化/替换当前 task cache；不新增第二个 state writer。

验收：wrong-path/writer/schema/duplicate/stale-revision 全部 fail closed；合法
initialize/replace/validate 在 Windows 通过。

## 5. Work package B：worktree journal canonical cutover

Owner files：

- `scripts/hmasd_worktree.py`
- `tests/hmasd_worktree_test.py`

实施：

1. canonical journal 改为 `.codex/runtime/worktrees.json`。
2. 若 canonical 不存在而 `.omp/runtime/worktrees.json` 存在：
   - 先用 state CLI 验证 legacy bytes/schema/writer；
   - 核对每个 row 的 Git registration、branch、HEAD、worktree path 和 receipt；
   - 通过 canonical state initialize 一次性导入；
   - legacy 文件保持只读，不删除、不覆盖。
3. 若 canonical 不存在而 legacy 存在，先完成 receipt、Git registration/path 和
   schema/CAS 校验，再一次性导入；若 canonical 已存在而 legacy 缺失，允许
   canonical-only，继续使用 canonical。若两份同时存在，canonical 是唯一使用的
   journal：canonical revision 高于 legacy 是导入后的正常前进，直接使用 canonical；
   revision 相同则要求 rows/facts 一致；legacy revision 高于 canonical，或同 revision
   facts 不同，均按 split-brain fail closed，不自动合并。
4. 所有后续 provision/record/prepare/apply/release/retain 只写 canonical journal。
5. 更新 docstring、error message 和 tests，禁止任何新 `.omp/runtime` 写入。

验收：fresh canonical、legacy-only import、canonical-only、canonical-forward
revision、same-revision agreement/conflict、legacy-ahead split-brain、缺 receipt
早期拒绝、Windows case/reparse、dirty/stale/out-of-scope/apply/release race tests
全部通过。

## 6. Work package C：Root/skills/Dashboard 合同收口

Owner files：

- `AGENTS.md`
- `.agents/skills/hmasd-root-task/SKILL.md`
- `.agents/skills/hmasd-root-control/SKILL.md`
- `.agents/skills/hmasd-git-integration/SKILL.md`
- `.agents/skills/hmasd-workflow-recovery/SKILL.md`
- `docs/migration/*.md`
- 必要的只读 contract tests

实施：

1. 明确 `tasks.json` 和 `worktrees.json` 都由 Root 通过 state CLI/CAS 写入。
2. 明确 `runtime_agents` retired，不建立 Codex 双写。
3. Dashboard 在过渡期优先 Codex、只读 fallback OMP；clean cutover 后是否删除
   fallback 作为单独可逆清理，不阻塞核心迁移。
4. 记录 fresh-host depth smoke，旧宿主结果不计。
5. 更新 capability matrix 和实施状态，不宣称尚未执行的 restart/cutover 已完成。

## 7. Work package D：集成验证

顺序：A 与 B 并行；二者完成后执行 C；最后 Root 集成验证。

最小测试矩阵：

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest `
  tests/hmasd_state_phase0_test.py `
  tests/hmasd_worktree_test.py `
  tests/hmasd_dashboard_test.py `
  tests/hmasd_recovery_test.py `
  tests/codex_config_contract_test.py `
  tests/hmasd_topology_contract_test.py `
  --basetemp temp/directions/workflow-codex-migration/test/runtime-cutover
```

随后运行全部 `tests/hmasd_*_test.py`、skill validation、`git diff --check`、host
exact-byte check，并确认：

- `.codex/agents/*.toml` 仍与 main 逐字一致；
- `.codex/config.toml` 仍仅有 `max_depth = 1` 差异；
- tracked 文件没有 thread/host/cursor/PID/绝对 worktree path；
- `.omp/runtime` 没有新增写入。

## 8. Work package E：需要重启的产品 smoke

代码验证通过后完全退出并重启 Codex，再创建一个新 Root fixture：

1. 顶层 task 创建 direct leaf 应成功。
2. direct leaf 再 spawn 必须被 `max_depth = 1` 拒绝。
3. list/read/send/wait 后用 state CLI/CAS 更新 `tasks.json`。
4. 删除 runtime map 后，从 native task list 唯一重建；ambiguity 必须 fail closed。
5. 恢复 idle task 并验证历史、model、skills、MCP 和 project root。

该阶段需要用户执行/确认 Codex 重启；旧宿主结果不能替代。

## 9. Work package F：shadow 与 clean cutover

1. 只读核对所有 durable state、Git worktree、run manifest、Agentify operation 和
   native tasks。
2. 证明没有 OMP Hub/manager/process 持有同一方向、run、send 或 Git integration。
3. 若发现 RUNNING/UNKNOWN/commitment-unknown，只观察并停止 cutover。
4. 冻结 OMP dispatch，启用 Codex runtime writers。
5. 执行一个无 effect Decision Packet、一个 worktree provision/release fixture、
   一个 task-map delete/rebuild fixture。
6. 用户确认后才删除或归档 `.omp` 编排定义；历史 plans 与 Git provenance 保留。

## 10. 回滚

- A/B/C 的代码变化未 commit 前可按文件范围恢复；不得触碰用户其他修改。
- legacy journal import 不删除源文件；canonical 文件可在无 live worktree/effect
  时移走并从 legacy/durable facts 重建。
- clean cutover 前任何失败都回到 OMP read-only baseline，不同时启用两个 writer。
- external/run/Git unknown outcome 永远不通过“回滚后重试”解决。

## 11. 完成定义

只有以下全部成立才能宣布“OMP 控制面已迁移到 Codex”：

1. 所有 live runtime writes 只进入 `.codex/runtime`。
2. task/worktree caches 都受 Root writer、schema、path ownership 和 CAS 保护。
3. native task recovery、fresh-host depth、worktree import 和 Dashboard projection
   均有实际证据。
4. OMP 不再 dispatch 或拥有任何 live effect。
5. 全部 focused/full tests 通过，且用户确认 clean cutover。
