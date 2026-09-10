# HMASD CM 任务清点与 benchmark 候选

本清点使用 `C:/Users/fires/.codex/state_5.sqlite` 的只读 URI（`mode=ro`）和每个会话对应的 rollout JSONL。严格分母是 `agent_role='hmasd-cm'`：全库 131 个会话；主分析窗为 `2026-09-06T07:00:00Z <= created_at < 2026-09-10T01:00:00Z`，并要求 cwd 为 HMASD（含 `\\?\\` 前缀）或 HMASD-worktrees，得到 27 个会话。严格角色会话均满足 cwd 范围。会话是统计单位，不等于独立任务；同一 rollout 内的 review、回执、收尾或小修复没有再次计数。CSV/JSON 的 `observed_session_git_sha` 只是 SQLite `threads.git_sha` 的建会话观测值，不代表交付 patch 或冻结输入。

## 类别分布

| 主类别 | 会话数 | 27 会话分母 |
|---|---:|---:|
| new_or_extended_implementation | 13 | 48.1% |
| bug_repair | 7 | 25.9% |
| parameter_wiring | 2 | 7.4% |
| integration | 1 | 3.7% |
| execution_collection | 3 | 11.1% |
| governance_support | 1 | 3.7% |

允许 secondary_tags 多标签；主类别按最初可见目标和操作的交付物形态判定。RNG、gradient、terminal、recurrence 等是 secondary risk tags，不改变主类。`cm_task_census.csv` 与 `cm_task_census.json` 给出相同 27 行字段；`excerpt_kind` 区分可见 handoff 与 CM 计划摘要。

## 适合真实代码编辑与独立 review 的候选

以下 9 个候选覆盖 runner 扩展、跨模块 seed/身份传播、终止/折扣/状态语义、checkpoint/RNG 隔离、发布路径和集成；受限性能任务可从队列中的 CRTO/MGTAP 另选。这里列待冻结的输入与保护语义，不记录历史完整正确 patch 或结果，避免给未来被测任务泄题。

| 候选 | 原始 CM assignment 与可追溯路径 | 最小冻结输入 | 保护语义 | 验收建议 | 直接 CM / 委派 |
|---|---|---|---|---|---|
| VSPC1 reactive queues B01 | thread `01a07a35...`; `daed52c9`; `experiments/candidates/vsp_c1/k4_reactive_queues_b01/`; `scripts/run_vspc1_k4_reactive_queues_b01.py` | frozen card、现有 host、technical fixture | old-`h` 服务时序、完整 segment、terminal target | fixture 检查队列守恒/overflow/partner；独立 review 后 runner contract check | 直接 CM，语义边界较集中 |
| UCOPE native return B01 | `01a07ab8...`; `373d1872`; `experiments/candidates/ucope/native_return_acquisition_b01/`; `scripts/run_ucope_native_return_acquisition_b01.py` | frozen card、existing host、固定初始化 seed | displayed count 与 paid reward 顺序、selected-action log-prob、RNG 隔离 | 初始化不污染全局 RNG；categorical boundary；partial summary schema；独立 review | 直接 CM；可委派独立 reviewer |
| DISH seed101 B05 | `01a079cf...`; `c24ddec6`; `experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b04/study.py` | B04 shared path、seed=101、master-family string | initialization/training/eval reset 与 reduction 的 seed 传播；checkpoint 格式 | 同 seed digest/不同 seed 分离；B04 compatibility fixture；independent review | 直接 CM，跨 runner seed 传播需 review |
| ACVC native link loss B01 | `01a085cc...`; `a601e607`; `experiments/candidates/acvc/native_link_loss_b01/{binding.py,model.py,learner.py}` | frozen native adapter、fixed observation fixture | private recurrence、realized command feedback、gate-only PPO credit、base exclusion | synthetic binding/retrace；optimizer parameter inclusion；RNG unchanged；独立 semantics review | 直接 CM + 独立 reviewer |
| FOLR public lifecycle B01 | `01a08702...`; `75df5334`; `experiments/candidates/vap_folr_core/public_lifecycle_b01/{collection.py,environment.py,native_env.py}` | pinned CAMA adapter、lifecycle fixture | inactive removal no-op、real departure、same-step birth 不继承旧 trip | collision/no-collision fixture；transition counter；RNG comparison；publication smoke | 直接 CM，终止/状态风险高，必须独立 review |
| SCDMP hold residual B01 | `01a0870c...`; `56e5b6b2`; `experiments/candidates/vsp_c1/native_hold_value_b01/` 与 SCDMP card | fixed environment、recorded counts、held duration | held segment 的 residual/discount 定义、MC path 与 publication estimand | one-step hand calculation fixture；terminal vs nonterminal target；summary schema；review | 直接 CM，语义风险高 |
| RCLE actor100 B03 | `01a08730...`; `664afecaf36c6f436dbe870fd6c80afb11a05d75`; `experiments/candidates/roster_consistent_latent_exploration_tbcfv_b03/study.py`; `scripts/run_rcle_tbcfv_b03.py` | B02 learning path、FLEX arm、seed 19、fixed runner contract | FLEX 必须贯穿 rollout/RNG；claim weight 在实际 actor loss；baseline/order 不变 | weight=0/1 fixture；seed/master digest；paired readout shape；independent review | 直接 CM + reviewer；跨模块传播适合真实 episode |
| CBSC opportunity-credit B04 | `01a079fc...`; `77c249ff`; `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/{ppo.py,tapes.py}` | B01 actor/Adam path、decision-only fixture | actor/Adam ordering、full episode BPTT、decision-only critic supervision | target/mask fixture；optimizer order；snapshot identity；review | 直接 CM；可委派 fixture reviewer |
| UCOPE main integration P70 | `01a0847a...`; `7e7ad937`; `experiments/candidates/ucope/`；对应 UCOPE docs card | accepted renewal changes + main normalization path | normalization compatibility、accepted ancestry、public adapter behavior | focused integration tests；old/new normalization equivalence on fixture；independent review | 直接 CM；integration review 必须独立 |

## 可模拟连续压力的自然任务串

这些不是新增会话计数，而是从单个 rollout 的连续 assistant/tool 事件中抽取的 episode 形状；可用同一 CM 会话重放“初次改动 → review 修复 → launch/collection 回执 → 小改动/seed wiring → Git/证据杂务”。只保留事件证据指针，不复制长日志。

1. **FOLR public lifecycle**（`01a08702-...`，rollout `...rollout-2026-09-09T09-31-44-01a08702...jsonl`）：历史事实：行 13 `16:31:56Z` 初始目标；行 67 `16:33:29Z` 创建 source surface；行 72 `16:34:19Z` 新增 environment；行 97 `16:35:27Z` 新增 runner；行 121 `16:37:31Z` 新增 tests；行 205 `16:39:25Z` focused checks/review；行 275 `16:42:19Z` review/staging；行 363 `16:45:43Z` accepted remote run。建议插入：review 后追加 publication 小修，再接 evidence/Git 杂务。
2. **UCOPE p47 / 7001-7002-8602**（`01a081bf-...`，rollout `...rollout-2026-09-08T09-00-05-01a081bf...jsonl`）：历史事实：行 13 `16:00:16Z` B02 clipping；行 47 `16:02:01Z` policy 修改；行 75 `16:04:53Z` focused suite；行 161 `16:09:49Z` fixture 超时；行 211 `16:11:53Z` reviewer 结论；行 255 `16:14:56Z` 提交实现；行 266 `17:08:28Z` staging；行 410 `17:39:29Z` cwd 修复；行 475 `19:10:38Z` 7001 接受；行 506 `19:12:40Z` 推送；行 594 `19:26:30Z` 7002/联合算术；行 604 `20:23:53Z` 下一 B03 小改。后续同一 CM 任务链实际复用到 8602。建议插入：7001/7002/8602 receipt 后加一次 seed/summary wiring，再接 Git 记录。
3. **RCLE actor100**（`01a08730-...`，rollout `...rollout-2026-09-09T10-21-09-01a08730...jsonl`）：历史事实：行 13 `17:21:20Z` weighted actor loss；行 520 `17:47:58Z` 不完整 pair readback；行 677 `21:48:56Z` recovery；行 721 `21:50:50Z` focused check；行 741 `21:52:03Z` review/launch；行 777 `21:53:49Z` Monitor adoption；行 788 `21:55:33Z` terminal completion；行 1291 `23:14:34Z` technical readback；同一 CM 在行 966 `22:33:10Z` 做 feasibility，行 1046 `22:56:39Z` 复用到 seed20 wiring。建议插入：recovery receipt 与 seed20 小改之间加入 identity/seed review，再接 evidence/Git 杂务。

## 局限

首个 Root handoff 在部分 rollout 中以加密 inter-agent payload 存储，无法从本地 JSONL 还原全文；因此逐行 excerpt 是人工初筛的可见目标，均标 `assistant_plan_summary`，不能宣称等同原始 handoff。未核实路径标为 unresolved；rollout 只保留指针、短摘要和可核实路径，不保存凭证或完整日志。没有按结果好坏剔除失败或未完成任务，也没有运行 benchmark 或成本分析。最近五方向中已覆盖 UCOPE、FOLR、ACVC、VSP03；其余 CM 任务来自 RCLE、DISH、CBSC、SCDMP、CRTO、FRRIE、FSD、VSP02、MGTAP 与 foundations。
