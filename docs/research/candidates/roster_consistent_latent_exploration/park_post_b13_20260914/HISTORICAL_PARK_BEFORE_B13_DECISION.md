# RCLE — PARK 知识交接

> 2026-09-14 当前裁决：Portfolio 全文审阅后的 **CONTINUE 已应用，B13 已实际完成**，见
> [完整裁决与 DM 回应](pro_packets/20260914_e01_portfolio_direction/INTAKE.md)。原 DM 继续实际研究，
> 当前仍占用1席；完整 B13 结果审阅已读并回应，新的可逆 PARK 建议与继续反方案待 Portfolio 裁决，尚未应用。
> 下面的 PARK/record-only/Clerk 路由属于历史，不是当前状态或派发路线。

> 2026-09-14 后续决定：新 DM 完成全文 intake 后重入并选择一个独立 final1024 B11，见
> [重入记录](RCLE_REENTRY_INTAKE_20260914.md)。同一任务继续工程、执行与 intake。以下原 PARK
> 决定、record-only 工作范围和成本/保全事实作为历史完整保留；当前状态见 DIRECTION.md。

记录日期：2026-09-14 UTC（2026-09-13 本地日期）。方向：`roster_consistent_latent_exploration`。

## 状态与本文件范围

**PARKED / RECORD_ONLY。** 本文件保留已有可逆 PARK 的理由和可恢复知识，不重新作出关闭结论，不恢复科研，不占用研究执行槽位。B10 实验、独立科学评审、DM 完整回应和指定清理均已完成；**没有在途实验、未回评审、待发送请求或其他科学 producer**。本次唯一工作是新增此文件、提交推送并向 Clerk 交接，之后保持 record-only，供 Clerk 归档任务。

已有 [B10 intake](RCLE_B10_GREEDY_ANCHORED_1024_INTAKE_20260913.md)、[完整独立评审](pro_packets/20260913_b10_scientific_review/archive/RESPONSE.md)及其原始记录不被改写。本文件也不恢复此前已撤销的 AGENTS 指令、旧持续委托、自动派发或历史审批用语；旧卡片中的权限/状态措辞只是当时记录，不是当前执行授权。

## 为什么 PARK，以及这个理由的薄弱处

原科学问题是：在真实物理成员变化、合法公共信息和共同调度条件下，学习到的联合行为能否比已有协调规则提供更好的原生服务与恢复？当前 joint-quota-phase 家族测试一个学习的共同配额相位控制器，而不是只检验配额是否守恒。

B09、B10 均显示真实学习，但在各自观测中仍不及现成 fixed greedy 的服务 U；B10 的八类场景均值都保留这一劣势，恢复指标也有局部损害。DM 因而保留 greedy 作为**这些观测用途的服务偏好**，并判断暂不继续投入这一学习方案，选择可逆 PARK 而非永久 CLOSE。见 [B10 原决定与评审回应](RCLE_B10_GREEDY_ANCHORED_1024_INTAKE_20260913.md#dm-direction-decision-reversibly-park-current-advancement)。

必须同时保留这个判断的薄弱处：**从“本次不胜 greedy”到“下一项信息暂不值得购买”不是数据自动给出的结论。** DM 没有测得训练总体劣势，也没有估计下一次成功概率或信息价值。一个新的独立 final1024 实例有实际辨别力，可能改变 learned-versus-greedy 的开发取舍。当前 PARK 是定性的投入价值判断，接受未测训练变异、可能错过更好实例的机会成本；不是重复训练无用、家族不可学或所有后续问题无价值的证明。独立评审明确提出了这一挑战，DM 已接受并补清表述。

以下都不是此次科学 PARK 的依据：一次分配用完；600 秒支持计划接近或超出；浏览器/Agentify 故障；账户或操作暂停；缺少新客户、阳性先导结果、精确上界或 headroom 证书。此前误把自定 600 秒计划升级为 owner-only 限制、暂停主动评审观察并请求额外 60 秒，是另一项已承认的工作流错误，不能拿来证明科学方向应停。

## 关键证据与反证

U 是越低越好的未满足服务量。主结果对 ACTIVE_CONTINUATION 的 8→12、12→8 两条路径等权。三个差分别为：`G_U = U_own-init - U_final`，`D_n = U_nearest - U_final`，`D_g = U_greedy - U_final`；正值有利于学习终点。

| 独立对象 | 自身初始化学习 G_U | 对 nearest 的 D_n | 对 greedy 的 D_g | 实际完整 native 时间 |
| --- | ---: | ---: | ---: | ---: |
| B09：seed29 / final256 | +.05126953125 | +.1460205078125 | −.0317708333333 | 47.13 s |
| B10：seed30 / final1024 | +.061531575521 | +.154589843750 | −.019075520833 | 161.35 s |

数值直接来自 [B09 intake](RCLE_B09_GREEDY_ANCHORED_PHASE_INTAKE_20260913.md)、[B10 intake](RCLE_B10_GREEDY_ANCHORED_1024_INTAKE_20260913.md)和已发表的 [B10 分析记录](b10_greedy_anchored_1024_20260913/INTAKE_ANALYSIS.json)，本次没有重新计算实验结果。

B10 的绝对主 U：初始化 .186840820313，final1024 .125309244792，greedy .106233723958，nearest .279899088542。全部八格 U 均保留正 G_U、正 D_n、负 D_g。主场景对 greedy 为 2/128 有利、29/128 不利、97/128 平局；不能写成每个场景都输。

支持继续研究、反对过度停止的证据同样真实：学习终点明显改善自身初始化并超过 nearest；greedy 平均缺口较小；只有一个 final1024 训练实例；真实完整调用已在记录节点完成。这使独立重复成为严肃候选问题，而不是没有研究价值的机械重跑。另一方面，初始化本身已经优于 nearest，因此 D_n 是完整 package 的优势，不能全算成训练新增；G_U 才是本实例相对自身起点的新增学习读数，二者都不是锚定的独立因果效应。

恢复后果不能被主 U 遮蔽：B10 final 的 failure-coded tau 均值相对初始化在 3/8 格恶化，相对 greedy 在 5/8 格恶化；相对 nearest 有 7 格改善，但 active 12→8 有 +.1875 的小损害。两条主路径的 final tau40 失败码分别为 0/64 和 61/64。tau 均值和失败码计数可能反向变化，tau40 也不是“40 tick 必然恢复”。三个 quota 角色的 F=0 是结构性申领计数事实，不是到位、恢复或无害保证。完整 full-Y 与全部 U/F/tau/40U 后果仍在原分析中。

## 学到什么，仍不知道什么

- 合法公共信息、共同相位支持和正确组合似然，使当前比较有明确含义；它们不证明无通信分散执行、等计算/等通信公平性或总体性能。
- 参数真的更新、训练曲线提高与服务收益是不同事实。B10 有 1024 个真实非零更新，但 useful service 要看原生比较，不能只看位移或训练曲线。
- 采用强协调参照会暴露只与 nearest 比较时被掩盖的缺口。已有规则能力、学习增益和剩余 greedy 差距必须分开保留。
- B10 是一个 seed30/final1024 训练实例。四个 512-episode 面板、八格和 1024 个曲线点不是独立训练重复；报告的近似 95% 区间只是条件场景不确定性。
- B09 与 B10 的随机根、终点和场景实例不同，不能把负差变小归因为 256→1024 的训练预算效应，也不能把两者合并成两个 final1024 重复。
- 原 .025 U 兴趣尺度属于各参考收益，不是 G_U 门槛或事后对称等价界。小负差、大量平局不认证等价、非劣或相同动作策略。
- 训练实例变动、表示/优化限制、减少锚定策略随机偏离与真正有益服务修正各占多少，以及 U 与恢复的实际用途取舍，仍未识别。可能原因不是已证明故障；不要求先找到唯一原因才能提出未来有意义的问题。
- 没有稳定训练总体优势/劣势、锚定/优化器因果归因、全局最优、普遍不可学、规模化、C/UAV 迁移或全面无害结论；同信息 tuned headroom 仍缺失，但这种缺失本身不是 PARK 的门槛。

## 可复用实现与记录

这些是复用知识和核对历史的入口，不是启动命令。

| 资产 | 保留内容与入口 |
| --- | --- |
| 问题、家族及历史边界 | [DIRECTION.md](DIRECTION.md)、[joint-quota-phase 家族 intake](RCLE_JOINT_QUOTA_PHASE_FAMILY_INTAKE_20260912.md)。保留两项更早 exact-recipe HOLD：unanchored phase/Adam256/final256，以及 equal-unit/.99-prior/FLEX/final1000；不把它们扩大成普遍失败，也不回溯给 B09 新加 HOLD。 |
| 冻结设计与原结论 | [B10 card](RCLE_B10_GREEDY_ANCHORED_1024_SCIENCE_CARD_20260913.md)、[B10 intake](RCLE_B10_GREEDY_ANCHORED_1024_INTAKE_20260913.md)、[B10 E0](RCLE_B10_GREEDY_ANCHORED_1024_RESULT_EVIDENCE_20260913.md)、[B09 intake](RCLE_B09_GREEDY_ANCHORED_PHASE_INTAKE_20260913.md)。 |
| 实际策略与训练链 | [policy.py](../../../../experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/policy.py)、[study.py](../../../../experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/study.py)、[runner](../../../../scripts/run_rcle_joint_quota_phase.py)、[focused contract tests](../../../../tests/experiments/candidates/roster_consistent_latent_exploration/joint_quota_phase/test_contract.py)。B10 实际 source 是 `e5fd439735bcc52d7f4cba9943b8c5c5138e21c2`；当前分支文件不替代这个冻结版本。 |
| 真实执行与分析 | [summary](b10_greedy_anchored_1024_20260913/summary.json)、[完整已记录分析](b10_greedy_anchored_1024_20260913/INTAKE_ANALYSIS.json)、[分析脚本](b10_greedy_anchored_1024_20260913/ANALYZE_RECORDED.py)、[technical acceptance](b10_greedy_anchored_1024_20260913/TECHNICAL_ACCEPTANCE.md)、[独立工程 review](b10_greedy_anchored_1024_20260913/INDEPENDENT_REVIEW.md)、[原调用记录](b10_greedy_anchored_1024_20260913/LAUNCH_COMMAND.txt)。 |
| 独立科学 review 及完整回应 | [完整 RESPONSE](pro_packets/20260913_b10_scientific_review/archive/RESPONSE.md)、[配对、哈希及 DM intake facts](pro_packets/20260913_b10_scientific_review/RESPONSE_INTAKE_FACTS.json)、[dispatch/completion record](pro_packets/20260913_b10_scientific_review/DISPATCH_RECORD.json)、[短原生回执](pro_packets/20260913_b10_scientific_review/archive/NATIVE_CHAT_RECEIPT.md)、[中文结果 brief](../../portfolio/owner/briefs/roster_consistent_latent_exploration/2026-09-13_RCLE_B10_FINAL.md)。短回执不能替代全文。 |
| 保全、清理与成本 | [retention](b10_greedy_anchored_1024_20260913/RETENTION_RECEIPT.json)、[cleanup](b10_greedy_anchored_1024_20260913/CLEANUP_RECEIPT.json)、[bundle recovery](b10_greedy_anchored_1024_20260913/BUNDLE_RECOVERY.json)、[support account](b10_greedy_anchored_1024_20260913/SUPPORT_ACCOUNT.json)。retention 中早期 `cleanup_pending` 列表已由后来的 COMPLETE cleanup receipt 解决，不是新的待办。 |

B10 可复用 package 的识别要点：120-sector、六 beacon、H64 原生宿主，t24 先处理成员/epoch 事件，每四 tick 一次合法共同配额相位；`q=.9*1[phase=greedy]+.1/N`，`pi=softmax(log(q)+z)`，真实组合分布采样与 log likelihood；2,561 个 FP64 参数、full-Y score loss、单 Adam、八个 cell baseline。B10 固定 1024×64 训练 episodes 和四个新 512-episode 面板，总计 67,584 episodes、4,325,376 native ticks。详细法则以冻结 card/source 为准；本文件不新增配置、seed 或预算。

### 仅本机保存的原始证据

本次只读检查确认以下两文件仍存在，大小和 SHA-256 与保全记录一致。它们位于 authoring checkout 的未追踪 `temp/` 下，**不能假定一次普通 Git clone 会包含它们**。

- Authoring checkout：`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`，原有分支 `codex/rcle`。
- 相对目录：`temp/directions/roster_consistent_latent_exploration/exp/b10-collected-e5fd4/`。
- `rcle-b10-e5fd43973-evidence.tgz`：297,865 bytes；SHA-256 `b87737bf2bb42f3f2c7df497bdb04030602c51be2ad7c7aa891d74b3c4a14133`。保留模型/优化器、曲线、完整四角色面板和原执行证据；本次未展开或重新分析。
- `rcle-b10-e5fd43973-source.bundle`：24,822 bytes；SHA-256 `a461bd83347908a1e85a70b4374d9897fb82677f35db9230ea86aa8a5c7f9582`。这是增量 bundle：tip `bf98ebba6c088d282df10ff88844e3b7d97c1630`，需要前置 `d741be527662c5cec18ed03ae03531658059dff6`，包含实际 launch source `e5fd4397…`；不是自足的完整仓库备份。
- 已有两个 Transport 未追踪附属文件继续原样保留：本轮 `archive/GITHUB_RESPONSE_0366a47e.md` 的原始 LF 全文副本，以及 `delivery/HANDOFF_PREFLIGHT.json`。本次不把它们改成新请求、不提交或删除它们。

## 评审、清理和成本的完成边界

完整科学 review 的 immutable delivery commit 为 `0366a47e6a5b58a75dabdbb2772a33a0cdcb0eeb`，对应 37,180 UTF-8/LF bytes，SHA-256 `c9d8f998976a88ddfa3831a6bdc48dafb641da9b268d2d6c355835ad62751741`；fixed TASK 是 `34c7ad37324453a87e809222ed8849e0644c0b82`，配对 Issue #8 comment 为 `5657222254`。Windows checkout 的 CRLF 大小差异、原 163-byte chat receipt 和完整 GitHub 回答的区别已记录在 intake facts。

Reviewer 未发现足以使主比较失效、必须换终点或补跑的已证实科学缺陷；其范围是指定的 11 个证据/源码路径，不是重跑原生环境、独立重算 raw 统计或认证全成本。DM 读完八节及引用，接受“起点能力与新增学习分开”和“承认重复训练的信息价值及放弃它的机会成本”两项澄清。最终科学回应已发布于 `ea95465efdf3841ac9685ed39f055644530940ef`；review 不是生命周期批准。

历史运行 `rcle-b10-s30-e5fd43973` 已 finished/exit0。2026-09-13T23:54:45Z 的 cleanup receipt 记录远端 worktree、supervisor 和 staging raw 副本被移除，磁盘与 Git worktree 注册均确认不存在；本地 unique raw/source 未动。本次不重做远端轮询，也不重新分配 Monitor。历史 request `2026-09-13-rcle-b10-scientific-review-01`、operation `094a6cba-6f76-4140-860b-1358e15b6cd9` 已一次接受、自然结束、完整归档并回应，不能当成待发/待恢复请求。

成本不能因为已归档而抹去。B10 完整 native 实测 161.35 s；归档 support JSON 的明确检查点为 627.289636 s，native+known support 为 788.639636 s。此任务在最终发给 Clerk 的交接中另报告包含后续文档核验/发布尾部后的已知 support 641.3301317 s、native+known support 802.6801317 s；它不是 JSON 的原检查点，也不是完整费用发票。Monitor/Transport 初始准备及未测调用、provider/agent lifetime、部分集成尾项仍为 UNKNOWN，不计零。

原 native/support/complete 的 300/600/900 s 计划及其实际支持超支保留。普通 DM wall 计划与真实 owner/平台硬限、冻结科学 exposure/比较终点必须区分；接近 600 s 不是通用 stop、Send 或上报门槛。网络 staging/打包停滞是实际工程成本，不是科学无效、另一个训练实例或 PARK 证明。本次知识整理不重开这次调用、不重置成本，也不把文档操作当训练量。

## 明确的科学复开条件（候选问题，不是当前任务）

以下说明何时值得重新提出 RCLE 研究。没有条件自动触发实验、Pro 请求、任务唤醒或槽位占用；本次 record-only 指令保持有效。

1. **训练实例变异确实会改变开发选择。** 如果当前需要决定是否继续采用/发展 final1024 学习 package，而对 greedy 的缺口是否依赖训练实例会改变这一选择，则一个前瞻定义的新独立训练比较是有意义的问题。更好的 greedy 对比可能削弱当前偏好，相近缺口可能加强它，混合结果会揭示不稳定性。它不需要先取得阳性结果或换一个机制才有科学价值；本文件不选择 seed、样本数或执行。
2. **有具体方法或服务用途问题能区分现有解释。** 例如确实需要解决 U 与成员变化后恢复之间的取舍，或一个明确的合法共同相位方法变化可能改变这种取舍。未来提案须说明所需选择、允许信息、保持有竞争力的实际参照、会区分哪些结果；不能削弱 greedy、换评价权重或把旧终点改名来制造成功。解释机制尚不唯一并不自动禁止提出有辨别力的问题。
3. **出现改变当前理由的实质证据。** 新的可信观察或具体的主量/比较器缺陷，使当前服务偏好或学习解释需要修正。先说明哪个主张受影响及什么观察可解决；不把一般技术故障、浏览器恢复或运行时间偏差等同于科学反证，也不自动撤销全部历史结果。

这不是“必须先有新客户、精确 headroom、唯一病因、显著性或 Pro 批准”的清单。真正要交代的是：所问问题、竞争选项、能改变选择的观察及相称工作范围。后续是否正式重开，须在新的有效工作指令下明确选择；本交接本身不授予科研或恢复旧持续授权。若没有这样的选择，维持 PARK/record-only，而不是制造实验保持忙碌。

## 交接后行动

仅把本文件的精确路径和提交号返回当前 Clerk，供其记录并归档本任务。原 authoring branch、冻结证据和本机保全资产保留；不创建 Pro 请求、Monitor、Reviewer 或后继对象。不需要等待科学 review、清理、实验结果或其他外部 producer。归档任务是关闭这个记录性工作入口，不是删除证据或永久关闭研究问题。
