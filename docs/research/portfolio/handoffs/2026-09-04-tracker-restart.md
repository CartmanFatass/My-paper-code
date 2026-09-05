# Tracker 配置重载前的研究交接

Status: `FINAL / SAFE_BOUNDARY / PAUSED`
Updated: 2026-09-04T23:13:10Z
Provenance: `OWNER_DIRECT`

本轮已经完整收尾。七位 DM、对应 CM/子代理和临时 tracker 均完成当前分派，没有中断任何
方向进程，也没有补位或启动后继对象。可以在此边界重新加载 Root/配置；本交接不自动重启
应用或恢复研究。依据是[所有者收尾指令](../decisions/2026-09-04-drain-for-tracker-restart.md)。

本次只暂停执行。两类、六族、九路线及 **14 ACTIVE / 8 PARKED** 来源方向、优先级和冻结
科学含义全部保持。VNFC 的第二次 RECAST 保持最低排序，R03 未启动；K4 的旧 D6 家族
继续停放，整个方向未关闭。其余 queued 路线与 reserves 没有新增分派。

## Root 与 Git 恢复入口

- 当前 Root task：`01a06df5-528a-7b32-8475-9b098c2b33c2`。
- 整合工作树：`C:/Projects/HMASD-worktrees/root-integration-02-20260904`；
  分支 `codex/root-integration-02-20260904`，upstream `origin/main`。
  此分支推送目标为 `git push origin HEAD:main`。
- 本交接前最后一笔主线证据整合：`be45adb17f6d170c8127cd975cfe56c6529993fc`（N5 最终 intake）。
  本交接自己的提交位于它之后；用主线日志读取最终交接 commit，不把原始分支 SHA 当成
  cherry-pick 后的主线 SHA。
- 保存项目 `C:/Projects/HMASD` 的 HEAD 仍旧，且有所有者独立的配置/模型修改，包括 DM/CM
  使用 Astra 的修改。保留这些修改；不要用主线文件整体覆盖、reset、stash 或直接拉取旧主分支。
  tracker 配置先前已按文件核对并同步到保存项目，备份回执在整合树 ignored
  `temp/sessions/two-line-consolidation-20260904/sibling-runtime-backup/receipt.json`。
- 以下已接受实现、结果、intake、曲线、brief、owner items 和共享 audit 已整合并推送 main。
  **CBSC 尚未接受的资源处理源码是明确例外**，仅保存在工程分支；主线只整合它的报告。
  ignored 原始实验数据仍在具名本地/远端根中，Git 保存其可恢复定位与证据摘要，未删除或搬迁。

## 各 DM 的最终结果与未启动下一步

| DM / 路线 | 本轮完成事实 | 以后明确恢复时的入口 |
| --- | --- | --- |
| `dm_amx_fsd_resume` / K1 | medium_d0_seed3 为完整有效单元；E3 **11/18 有效、0 运行、7 格未创建**。20 rollouts、128000 transitions，必需产物及 10 项传输哈希一致；峰值 RSS 缺失标为 resources_unmeasured，不使此非资源声明失效。 | 下一格恰为 `medium_d2_seed3`，之后是六格 large D0/D2。它们均未建任务、receipt 或科学根；保持原卡，不重跑已完成格，18/18 前不作 E3 聚合判决。 |
| `dm_amx_frrie_resume` / N1 | r04 退出 1；training-tape 序列化出现 tuple_iterator/name 异常。没有 summary、checkpoint 或失败 update/address 状态，无法从留存状态复现该步；原因仍未确认，未形成科学结果。 | 先基于已记录字节与缺失状态做有界诊断设计，再决定工程修复；不盲重跑。attempt05 未创建，旧 attempt02 的未解异常保持独立。 |
| `dm_amx_cbsc_resume` / N4 | r07 仍是未完成 assignment。资源处理补丁 42 项 focused 检查通过，但 runtime 460/460 改动行均为 orchestration，超 30% 限额；历史 fixture 的总体 source/law 绑定仍不匹配。正式 publication、15 表和 consumer readback 未验证。 | 先处理未接受 diff 的 scope 违例，并恢复真实历史绑定或另行选定合法完整 offline fixture，再作具名工程验证。未接受 source 不可作新科学启动依据；无 r08。 |
| `dm_amx_n3_state_recovery` / N3 | B04 有效 `B04_WITHIN_MEI`：typed−generic 曲线 AUC **+0.00260417**，MEI 0.05；两者末值均 0.98828125，RESET 0.50651042、LATCH 0.99869792。状态保留有信息价值，本次 typed mask 未显示达到 MEI 的额外收益。 | 下一候选是 DISH B01 状态来源干预，仍有既存 checkout 依赖；只是提案，未启动。固定 generic 不是调优 headroom，三种子也不证明等价或整个 N3 无效。 |
| `dm_amx_n5_allocation` / N5 | B02 pilot 与三种子固定 panel 有效 `B02_INSIDE_MEI`：METRIC−FREE AUC **+0.00839669**，MEI 0.01，三种子均正。完整曲线、intake、brief 已收录；main 8.17278 秒，含 pilot 8.93954 秒。 | 下一候选是同信息量的步长/conditioning 控制，未冻结或启动。结果限于训练 N=4/8 的组合坐标 toy；不能排除优化条件解释，也未升级为稳定优势、等价或正式 UAV 证据。 |
| `dm_amx_crto_resume` / K2 | A03 为单独命名、有效的既有数据读取；五个 phase-0 checkpoint 胜任，但相对 update 256 的聚合 regret 均无改善，变化均在 MEI 0.0025 内。A01 native crash 仍未解；A02 仅是 NO-FAULT-WITHIN-BOUND。 | 完整三次 update 周期的 RAW 后续读取尚未冻结；无新卡、运行或 Pro。保留 A01/A02/A03 各自证据身份，不把 phase-0 读取解释成因果 phase 收益。 |
| `dm_amx_ucope_resume` / K3 | 数值计划未执行。direct-reuse 草案独立审查为 127/219=57.9909% orchestration，归档后移除自有未接受文件；无新 diagnostic、preflight 或训练。既有 paid-acquisition 5/6、+0.021437 保留。 | 保持 one-seed/fold、two-pinned-node 计划，寻求具体符合 scope 的实现；不能通过填充无关科学代码或默认豁免预算启动。该草案失败不代表所有架构不可行。 |

### 证据与提交定位

下表路径后缀均置于 `C:/Projects/HMASD-worktrees/`；分支是 `codex/<后缀>`。
短 SHA 均是当前仓库可唯一解析的原始提交，已推送对应分支。

| 方向 | DM 工作树后缀 / 最终 commit | CM 工作树后缀 / 最终 commit | 主线科学/工程 intake |
| --- | --- | --- | --- |
| FSD | `dm-fsd-resume-20260904` / `463e7da857` | `cm-fsd-seed3-resume-20260904` / `570670403f` | [完整单元 intake](../../candidates/flexible_skill_duration/FSD_E3_MEDIUM_D0_SEED3_INTAKE_20260904.md)；[运行与原始根](../../../Claude_docs/experiments/FSD_E3_MEDIUM_D0_SEED3_REMOTE_RUN_20260904.md) |
| FRRIE | `dm-frrie-resume-20260904` / `33766289e2` | `cm-frrie-r02-resume-20260904` / `e8df4b6d48` | [r04 terminal intake](../../candidates/finite_resource_relational_inductive_efficiency/FRRIE_B01_CONTACT_ACTIVE_R128_R02_R04_TERMINAL_INTAKE_20260904.md) |
| CBSC | `dm-cbsc-resume-20260904` / `263415231e` | `cm-cbsc-r07-launch-20260904` / `93d6ba1414` | [未接受修复 intake](../../candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_R07_RESOURCE_REPAIR_RETURN_INTAKE_20260904.md)；[CM 完整边界报告](../../candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_R07_RESOURCE_REPAIR_CM_RESULT_20260904.md) |
| N3 | `dm-n3-state-recovery-20260904` / `94892274c3` | `cm-n3-folr-b04-20260904` / `6f9e3716f1` | [B04 intake](../../candidates/vap_folr_core/N3_FOLR_ROUTING_B04_INTAKE_20260904.md)；[CM return](../../candidates/vap_folr_core/N3_FOLR_ROUTING_B04_CM_RETURN_20260904.md) |
| N5 | `dm-n5-allocation-20260904` / `db326070b2` | `cm-n5-b02-20260904` / `c8d6cb6184` | [B02 intake](../../candidates/metric_ground_transport_allocation/MGTAP_B02_MAIN_INTAKE_20260904.md)；[完整结果](../../candidates/metric_ground_transport_allocation/MGTAP_B02_MAIN_RESULT_EVIDENCE_20260904.md) |
| CRTO | `dm-crto-resume-20260904` / `62db9de4e8` | `cm-crto-resume-20260904` / `576f8b713e` | [A03 intake](../../candidates/commitment_residual_triggered_options/CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_INTAKE_20260904.md) |
| UCOPE | `dm-ucope-resume-20260904` / `34177bee6c` | `cm-ucope-locus-resume-20260904` / `7e61d4520a` | [数值草案阻塞](../../candidates/ucope/UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_DIRECT_REUSE_BLOCKER_20260904.md)；[terminal intake](../../candidates/ucope/UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_RESUME_TERMINAL_INTAKE_20260904.md) |

临时 tracker 的工作树/分支后缀为 `experiment-tracker-20260904`，最终提交
`ed4f218b2a8926d9c9e4eedf741dff31cb1aa6b2`，已整合为 `ffc38622c`。
[共享 tracking 记录](../EXPERIMENT_TRACKING.md)保留任务观察历史；其中早于最终 intake 的
“待 Root relay/收集”文字以本表的最终 DM 确认为准。没有未处理的 terminal 通知或 reminder。

所有七个 DM、七个 CM、tracker 和本轮使用的五个 implementer 工作树已核对，20 个均无待提交文件；其中有提交的 19 个分支均与各自 upstream 一致。
N3/N5 implementer 留存的 1/5 个未跟踪文件与主线仅换行不同；Root 核对 Git 规范化后的
staged blob 与已接受主线 blob 完全一致后，仅作分支收尾提交并推送：
`impl-n3-folr-b04-20260904` / `927366eaab9fe2911657d0adf43f10fb9a8b18ce`，
`impl-n5-b02-20260904` / `da42b17303c5b363ea6c31a8273286100ff8802e`。
它们不需要再次整合，也不是新的实验 source SHA。UCOPE implementer 无自有待提交文件、
无新提交/upstream；不要为此复制、重跑或重开已拒绝实现。

CBSC 的 `impl-cbsc-resource-downgrade-20260904` 位于
`ce94f5afd1ea91b2b212ea219467ef5dc9dd27f8`；runtime 实现提交是
`261ca37e2825af36d37ef58647a8b1fc8f6e0f98`。这两个推送的 SHA **均未获整合接受**。
CRLF 重现了十二项 wrapper 的 literal-spec hash，但 aggregate source/law hash 仍不符；
未修改既有证据身份来通过检查。静态 replay locator 疑点尚未复现，不能写成已确认生产缺陷。
三次远端 profile 都已 terminal；第二次因 argv 引号拆分意外重复了 focused 测试，偏差已记录。
Root 停止扩展后没有接受第四个 profile 或 r08。

## 已终止的运行与原始证据

远端节点是 `wsl_4070`（SSH alias `hmasd-wsl-node`），原有 supervisor
`/usr/local/bin/agent-task`。以下仅是恢复定位，不是启动指令。每个 handle 的日志/exit
保留在 `/home/wu/.agent-tasks/<handle>/`。terminal 后 status 的 uptime 不作为实际运行时间。

| 对象 | 已接受 handle / 最终退出 | exact source SHA | remote cwd 与根/receipt |
| --- | --- | --- | --- |
| FSD 当前格 | `fsd_e3_medium_d0_seed3_20260904_01` / 0，22:26:00Z | `9c0a990537a8ffef58306429a1ff402550fc4b82` | cwd `/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed3_20260904_01`；根 `temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`；根内 `preflight.json` |
| FRRIE r04 | `frrie_b01_contact_r02_732cc2b2_04` / 1，22:26:33Z | `732cc2b2299821a58d644e202c4b95c392932447` | cwd `/home/wu/hmasd-worktrees/frrie-contact-r02-r04-732cc2b2`；空根 `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r04`；receipt `temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r04_admission.json` |
| N3 B04 | `n3-folr-b04-full-20260904-a1` / 0 | `0f83132fb3484f8366eaaa5863559d203f0cb369` | cwd `/home/wu/hmasd-worktrees/cm-n3-folr-b04-20260904-a1`；根 `temp/directions/vap_folr_core/exp/n3_routing_b04_full_20260904_a1`；根内 `resource_admission.json` |
| N5 pilot / main | `mgtap_b02_pilot_1907_f3595bfe` / 0，22:42:12Z；`mgtap_b02_main_203_211_223_f3595bfe` / 0，22:47:40Z | `f3595bfe3e90024f3b31eb8a82910304b90543d3` | cwd `/home/wu/hmasd-worktrees/mgtap_b02_20260904`；根 `temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_pilot_1907` 及 `mgtap_b02_main_<203,211,223>`；每个根内 `admission.json` |
| CBSC 最后 formal node | `cbsc-r07-formal-profile-ce94f5afd-01` / 1，22:42:45Z | `ce94f5afd1ea91b2b212ea219467ef5dc9dd27f8`，未接受工程 source | cwd `/home/wu/hmasd-worktrees/cbsc-r07-formal-profile-ce94f5afd-01`；既有 fixture 位于 `/home/wu/hmasd-inputs/cbsc-r07-resource-repair-20260904/`，完整定位与 digest 见 CM return |
| CRTO A02 | `crto_raw_phase_native_repro_a02_8d1c5978_01` / 0，21:52:18Z | `8d1c597871b38edc7d5f139f34f5a3ce2941c7d0` | cwd `/home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02`；根 `temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01`；receipt 是相邻 `attempt01_admission.json`。A03 只读已有 trace，其来源见 intake。 |

FSD 的 canonical 完整新格位于
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/medium_d0_seed3`；
CM 的收集副本在
`C:/Projects/HMASD-worktrees/cm-fsd-seed3-resume-20260904/temp/directions/flexible_skill_duration/exp/E3_20260904/remote_fetch_seed3_terminal_01/medium_d0_seed3`。
FRRIE 的失败日志、admission 和 native binary 在 CM 树
`temp/directions/finite_resource_relational_inductive_efficiency/technical/r04-terminal-handoff`。
N3/N5 完整原始根分别收集在对应 CM 树的同名相对路径；N5 aggregate 同层
`mgtap_b02_main_aggregate/summary.json`。CBSC 本地控制证据在 CM 树
`temp/directions/capability_bound_semantic_currentness/control/r07-repair/`。
所有旧隔离根保持原样；UCOPE 本次没有被接受的数值 diagnostic 根。

以后获准恢复时，新结果调用仍需按原卡 exact committed/pushed bytes、detached supervisor、
在实际节点紧邻 runner 的新 memory admission 执行。旧 receipt 不接纳新调用，已 terminal
的任务不重放。FSD 下一格原有保守成本投影 4.63 小时 / 8 小时 cap 仍在 intake 中。

## 完成核对与调度状态

- 最后整体核对：远端 `agent-task list` 全部已终止、TMUX_ACTIVE 均为 no；本轮没有 live
  accepted handle。本地 Win32_Process 中未发现命令行匹配 HMASD/本轮 runner 的 Python 进程。
  DM、CM 与子代理的完成状态和具名 supervisor 记录相互核对；不能从单一 exit 0 推断科学有效。
- Transport task `01a06c45-e279-7813-822f-9ea90cb14a72`（`transport_lxh_project_singleton`）
  compact snapshot 为 idle、最后 turn completed；无 in-flight 请求。本轮收尾没有新增 Pro Send。
  所有者复制的后续 6 Pro 回复已在
  [完整归档](../../../external-review/2026-09-04-two-line-consolidation-6pro/OWNER_FOLLOWUP_02_RESPONSE.md)
  并经[九路线采纳决策](../decisions/2026-09-04-adopt-nine-routes-and-resume.md)执行；
  旧 request02 的 Transport Send=0 是接管历史，不是待重投任务。
- `python tools/owner_console/item.py reviews --json` 最后返回 `[]`，没有未应用 review；
  ledger 非空 owner 栏的恢复研究、专用 tracker、N5 收尾指令均已应用，其中旧自动推进由
  本次收尾指令取代。FSD 三行和 CBSC015/016 行已从各 intake 原文追加到共享
  [2026-09-04 audit](../audit/2026-09-04.md)，已有 owner 行未覆盖。
- 现有 heartbeat `hmasd-research-loop` 已通过 automation tool 在 **23:04:29Z 设置 PAUSED**，
  保存文件复查一致；保留 30 分钟 recurrence、原 task 绑定及完整 drain prompt。
  旧 Pro request wakeups 仍暂停。无另建 automation 或 app/task 重启。
- 本轮有效结果、技术失败和未接受修复分别保留自己的判断。生命周期、优先级及科学证据
  层级未因进程、tracker 或配置问题改变。

## 新 runtime 先核对的事项

专用配置已在
[角色文件](../../../../.codex/agents/hmasd-experiment-tracker.toml)和
[项目配置](../../../../.codex/config.toml)中定义：`hmasd-experiment-tracker`，
`gpt-5.6-luna` / `xhigh`，含本地/远端观察、记录、提醒以及同树 DM 交接 instructions。
旧临时实例使用 default，不能记为已加载该 custom role。

原生 sibling 已被实际验证：FSD → CRTO → FSD 的 send/ACK，以及 CRTO → idle FSD → CRTO
的 followup/ACK；Root 没有转发这两组消息。[说明文档](../../../project/SIBLING_COMMUNICATION.md)
保存 token、操作语义、官方文档范围和本轮工具限制。

新的 Root/配置加载先检查是否发现该 role，再做一次 tracker 与 DM 的实际双向 ACK。
模型选择、role 发现、工具暴露和收件 ACK 分别记录；这些是能力核对，不新增科学 launch gate。
当前 runtime 两次选择该 role 都得到 unknown agent_type，而 default Luna 实例缺少
collaboration namespace；这些事实尚未证明具体加载原因，也未证明 Luna 普遍不支持 sibling。
重启可能重新加载配置，但不能保证修复。

测试只使用原生 collaboration 的实际 callable 能力；没有一个另名 sibling 的专属工具。
不得通过已拒绝的 app-server/task-message 接口绕过多代理边界。无论能力验证结果如何，
此 handoff 的默认执行状态仍是 PAUSED，后续研究恢复需要新的明确推进指令。
