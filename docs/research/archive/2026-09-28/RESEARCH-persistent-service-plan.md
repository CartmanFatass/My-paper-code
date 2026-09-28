# Retired persistent-service project plan

Historical evidence only. This prospective project-plan subsection, from
`ad55c6e43fdbd38bf78abc42f9e48e762535b357`, was retired on 2026-09-28 after
the complete result and independent scientific answer were read. It changes
neither the experiment's fixed inputs nor another direction's accepted work.
Current priorities are in [RESEARCH](../../RESEARCH.md#current-research-plan).

## Prior project plan

**本轮选定问题：有限的返航准入、补能停留和重新部署承诺，能否改善完整协作路径与服务？**
由新的`uav_persistent_service` DM负责；不恢复已完成归档的DM，不把空闲槽位当选题理由。
旧I已经主动选择充电站且保持目标，本次不同在于跨普通重规划执行的有限停留承诺；
重复低储备和旧I/L的失败不诊断充电机制，也不证明可用增益。
中央当前快照是明确的初始边界，原TransitHold P保持精确普通参照；合法观测P_BS是另一程序，不能混称。

一次完整探索比较直接PPO调度器L、同权利普通调度器O和不变P：
**1fit、64个H3000训练世界、3臂各16个新配对评价世界，共112回合/336k原生步/640次优化更新。**
只有最终checkpoint，无中间挑选、额外arm或自动补跑；零预测环境推进，但最多638400次radio snapshots，
真实执行、学习、工程、审查、保全及读取仍有成本。历史P线性缩放约2.45 worker-hours不是本次时长预测或上界；
真实节点准入和实测为准。完整规则、种子及风险取舍见[方向NOTES](../../candidates/uav_persistent_service/NOTES.md)。

同一次独立选择审查提出的实质异议已被Root采纳，并由DM修正规则：margin已经扣除返航能量，
因此D是到F进入的近似出发deadline，不能再用D-tau排序或算占位；O以D排序、以其他成员D+tau估算到站，
另行计入有限端点前的返程服务恢复。无可行停留则继续服务，D超出剩余H不触发补能。
停留明确为首次几何到达后的经过时间，包含排队和离开范围的时间，不是获配充电时长。
完整原异议及处置保留在[选择记录](RESEARCH-native-round3-selection.md#decision)；
不因修正规则新增fit、预筛查或第二套选题审查。

不同结果改变投入：L在完整J/服务和观察到的风险代价上超出O与P，才值得给独立fit复制定价；
O有用而L无额外用途则保留条件性普通资产；两者都未建立用途则结束此包。
未激活、到达失败、充电中断、标签执行重合、风险冲突和技术不完整分别读取，不自动授权修补。
本次是中央信息、有限H3000下的经验用途问题，不宣称持续服务保证、PPO/MARL算法新颖性或已识别能量瓶颈。
用户运动预测暂不另开方向：当前并无足够明确的条件性收益预测；这不是已经测出预测无用。

## Root disposition

The complete result and full independent answer are published at `ad55c6e43` in
[the direction notebook](../../candidates/uav_persistent_service/NOTES.md#full-independent-answer).
Root read that answer and the DM disposition, and checked compact episode,
identity, discrepancy and cost counts. Root did not repeat the DM and reviewer's
294-file/112-trajectory audit. The independent reviewer recorded no material
dissent. Reuse that review; no additional review or run is selected.

Retain O as a conditional ordinary central-information S7-S2/H3000 reference;
stop this PPO recipe. O improves complete J and service in 15 of 16 worlds,
while L reproduces P's native arrays bitwise in all 16. Preserve the losing
world, nine longer below-half-service spells, early-service loss and net stored
energy withdrawal in every O world. This is finite package usefulness, not
sustainability, component attribution or an unconditional default replacement.

Training executed 1,155 commitments, but 17 received charging without the
geometric arrival event that starts the dwell clock. This changes experienced
control duration, including a 120-second label commanded for 900 steps. L's
as-executed deployment is unchanged; intended duration learning was not fully
realized. The discrepancy does not invalidate O/P or identify why L equals P.
Neither a detector-patch retry nor stochastic-deployment rescue is selected.

The broader scheduling question stays open without an automatic follow-up.
This result arrived after joint-transition acceptance: do not insert O into
that fixed panel or infer an O-versus-path-planner ranking across different
worlds. Root continues the independently selected joint-motion question;
Claude's accepted work and autonomous question selection remain unchanged.
