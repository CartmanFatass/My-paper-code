# HMASD 后续研究方案：Claude 与 Pro 回复的综合复核

日期：2026-09-09。作者：Codex。性质：应 owner 要求出具的研究建议，供审阅和后续决策使用；不是已执行的 Portfolio 决定、科学卡或新实验分配。

## 1. 建议先做什么

**建议以两项小规模实证比较作为下一轮重点：FOLR 检查重置收益是否与成员事件的时机有关；UCOPE 检查短保持策略相对逐步反馈的收益是否随训练预算改变。** 把学习曲线直接放进这项算法比较，先做一个新训练对、连续训练到 2048 episode；暂不采用 Claude 的 3×8192 episode 主机能力普查。交付前主仓库已分配 FOLR 第三个同配方训练对，本文三臂建议是该既有分配之后、结合其结果再判断的候选，不替换该训练对。ACVC 的固定 retrace 发现值得保留并检查可复用性，VSP03 可作为便宜的预算敏感性候选。FSD 需要纠正诊断，不能以“原终点关闭了机制”为理由直接重开。

Claude 抓住了两个实际问题：不少比较缺少充分的训练预算记录，FOLR 的最终评价噪声不小。但它把这些问题进一步推成“主机整体不会学”“先证明能力再研究机制”，证据不够；其 FSD、RCLE 和部分统计解读也需要修改。Pro 专项复审的总体原则更可取：保留有限实验事实，缩小解释，分别处理科学负结果和技术缺失；仍然优先考虑能改变下一步选择的真实学习实验。

这也给出项目主题上的分工：**N 线先把成员变化后的状态处理做实，k 线先把保持时间带来的有限训练收益做实。** 固定重置和固定持续律首先是有用对照与可检验现象，还不是“学会灵活 N/k”的完整算法贡献。后续再据结果选择学习状态保留或学习终止时机，不同时打开两个大改动。

本报告比较 Claude 涉及的十个方向。其他 Portfolio 方向不据此获得新的科学判断。这里的建议顺序不修改现有 ACTIVE/PARKED、Priority、recast 或五链执行目标，也不要求正在承担其他授权工作的方向停下来。

## 2. 证据边界与两项新结果

本轮实际读到一份第三方规划答复，即 [Claude 增强版回复](RESPONSE_CLAUDE_FABLE_WITH_SPECS_20260909.md)，以及十个相关方向的 Pro 回复和 [Pro 科学有效性专项复审](../20260909_foundations_special_review/archive/RESPONSE.md)。背景包括 [Portfolio](../../PORTFOLIO.md)、[证据规范](../../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) 的相关类别与 §11、工程范围和运行时规范、[FOUNDATIONS](../../../../rl-marl-foundations-20260907/FOUNDATIONS.md) 及四篇专题。对改变结论的争点补查了卡、结果和直接源码；没有重新运行学习器、环境或评价器。

主仓库初读基线是 `aae3f2ac89d91d6584732862df184e19b11bcd57`；交付前补查了 `4f216bc9e` 已集成的新 intake 和原研究任务分配。第三方原提示的科学截止点是 `4b997913e2a7ea91391058e40d4781fd9c0a78bc`；以下两项在该条件计划之后已经形成结果。为避免把正在编辑的草稿当成决定，只使用注明版本的已提交文件：

| 结果 | 已读事实 | 对后续方案的影响 |
| --- | --- | --- |
| UCOPE normalization /8501 | normalized−raw = **−0.0047834239**，条件评价 SE **0.0115532614**，原卡读法 WITHIN。normalized/raw/H 分别 **0.1512980461 / 0.1560814700 / 0.1706160337**。 | 归一化没有在这一个实例带来所选尺度的点增益，两臂均低于 H。DM 已选择不做不变的 normalization 后续；不能仍按“若 UP 就用 normalized”安排。下一候选使用 raw 的理由是保留已知配方、检验另一问题，并非证明 raw 普遍更优。 |
| FOLR public-lifecycle B02 | RETAIN/RESET = **1.3278125 / 3.250625**；RETAIN−RESET = **−1.9228125**，科学验收为有效 B、RESET_ABOVE_MEI。B01 为 **−2.0021875**。 | 两个独立训练对都出现约 2 个原生回报单位的 RESET 优势，足以提高“比较重置时机”的边际价值；仍不证明总体稳定优势或遗忘机制。原 DM intake 已集成 `71c781aec`；Root 已另分配一个不变两臂新实例。 |

UCOPE 的补充科学结果与 intake 初读于方向分支提交 [860f98bf6](https://github.com/CartmanFatass/My-paper-code/blob/860f98bf6ea4ce8882ccd340e40af3b0af7eed0c/docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_8501_RESULT_EVIDENCE_20260909.md)，执行源为 `7c88fb8405c75339e9634b78f1ef6de770f24e31`；主仓库也已有[终态执行证据](../../../candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_8501_EXECUTION_EVIDENCE_20260909.md)。FOLR B02 使用已提交的 [429e4df7b 技术证据](https://github.com/CartmanFatass/My-paper-code/blob/429e4df7bbb1712ffe98917ca50183093374203d/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_RESULT_EVIDENCE_20260909.md)，执行源为 `434f10cf95f16dd342cbf754382aa76155fcd2b7`。交付前分别核对了 main 已集成的 [UCOPE intake](../../../candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_8501_INTAKE_20260909.md)、[FOLR intake](../../../candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_INTAKE_20260909.md)与 `83f3dfc19` 的分配记录。没有把其他会话的未提交内容纳入结论。

Claude 的 normalization UP 概率 0.55 在这次结果上没有命中；这只是一个预测事件。当前只有一份增强版答复，且作者披露了旧上下文，不能据此评价不同模型的总体能力，或归因于“读了基础知识所以更好”。

## 3. 对 Claude 建议的关键修正

### 3.1 主机能力值得检查，但 H 不是上界，现有证据也不是“都不会学”

UCOPE P85 的四个学习模式确实都低于该次 H。这是该训练对、该执行方式下的事实。其他记录却包含 F、G 或普通 MLP 超过 H 的情况：例如 UCOPE P82 的 F−H/G−H 约 **+0.02855/+0.02000**，P83 的 F−H **+0.01688**；MGTAP DENSE 两次比 H 高 **0.04439/0.02739**。P84 虽然 F−G 很大，F−H 却为负，因此“战胜学习对照”和“相对悬停有实际价值”必须同时报告。[UCOPE 卡与前次结果](../../../candidates/ucope/UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md)、[MGTAP intake](../../../candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_POST_B01_CONVERGENCE_INTAKE_20260909.md)。

**J−H 不是规范定义的 headroom。** 后者需要同一主机上注明的上参考与调优的同信息 baseline；H 是合法而有用的固定参照，既非已知最优策略，也不自动构成上参考。一个“展开后悬停”脚本最多提供另一可行参照；若使用特权信息还需单独标明，不能因为是脚本就称为上界。若几条训练曲线停在 H 附近，仍可能是优化、探索、策略表示或奖励权衡，不能直接推出悬停近似最优、奖励没有可学信号，或者应该惩罚静止。[证据规范 §§11.7–11.8](../../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)、[RL 专题](../../../../rl-marl-foundations-20260907/topic-notes/01_RL.md)。

这些方向共享 native host，但不共享完全相同的 learner：critic、动作保持、训练参数量、更新语义不同。一个 G 曲线结果可作为共享参照，不能一次“认证”四个方向，也不能把 SCDMP/VSP-C1 的研究资格绑定到 UCOPE 是否先出现阳性结果。

### 3.2 已有连续训练端点，而且它们支持“看曲线”而非“零曲线”

VSP-C1 Pro 已保留三个配对训练实例的 512→768 episode 连续训练对照：

| 训练实例 | GATED−MLP @512 | GATED−MLP @768 | MLP @512→768 |
| --- | ---: | ---: | ---: |
| 8501 | +0.0638797040 | +0.0096406106 | 0.1364368028→0.1944619882 |
| 8502 | +0.0213148509 | +0.0093906006 | 0.1877980590→0.2000085677 |
| 8503 | −0.0149815972 | −0.0735897558 | 0.1803206645→0.2347539933 |

三对的相对差值都下降，普通 MLP 都继续改善。这是预算会改变比较结论的具体理由；不是所有 learner 已收敛的证据，也不是对 UCOPE 同样变化的预测保证。应复用这份有限曲线事实，再在待选 UCOPE 比较中加少量固定端点。[完整 Pro](../../../candidates/vsp_c1/pro_packets/20260909_native_hold_value_post_b13_convergence/archive/RESPONSE.md)、[B10 intake](../../../candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B10_INTAKE_20260909.md)。

### 3.3 不能用跨对象 SD 宣布单对结果“主要是抽样”，也不能令 MEI 跟着 SD 走

MGTAP 的两个 REL−DENSE 值给出描述性 SD **0.02930**；VSP-C1 的三个值来自另一训练包；UCOPE 又有不同持续律和执行方式。它们不能合并为“同一配方在主机上的训练 SD≈0.03”。即便同一配方，换了评价世界的 fit 均值波动也包含有限评价噪声。

一个独立训练对的 UP/DOWN 是该冻结对象的点读法，既不是训练总体显著性，也不会因条件 SE 较大而自动失效。MEI 要由值得关心的任务收益来说明；噪声决定精度、预算和结论措辞，不把 MEI 改成 SD 的倍数。后续多 seed 可以检验重复性，但没有“三个或五个才准做 B”的门槛。[经验研究专题](../../../../rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)、[证据规范 §11.8.3–5](../../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)。

### 3.4 FSD 的零 gap 是观测结果，不是评价器关闭终止逻辑

源码 `_batched_assign_skills_d2` 在 deterministic 路径仍计算 `max(logits)−held_logit` 并与阈值比较；`deterministic` 随后影响技能选择。原生执行路径又把同一模式传给 primitive action。因此把它改为采样，会同时改变技能选择与底层动作，不能把回报变化唯一归于“打开 renewal”。固定 cap/expiry 仍有高层续约；训练中额外 gap 决策也已非零。原终点的“额外 gap 决策为零”不等于“全程没有续约”。[源码](../../../../../hmasd/agent.py)、[P72 结果 §§2–4](../../../candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md)。

两次 I−D0 为 **−0.0496705632、−0.0353127253**，是有效的训练包负结果；“I 训练回报较高”不能替代隔离评价。D0 的技能时钟固定，但 primitive actor 每步仍能响应新观测；它并非十步完全盲飞。`.25` 在已核验的 gap 路径是触发阈值，不能直接当作每次续约在原生奖励上扣 `.25`。[FSD Pro](../../../candidates/flexible_skill_duration/pro_packets/20260909_p74_post_uav_b02_convergence/archive/RESPONSE.md)。

所以不接受 F1 的“纠错后必重做”理由，也不把非零 gap 设为结果有效性的门槛。如果应用确实需要采样执行，可以提出新的比较；它回答新的用途问题，保留旧负结果。

### 3.5 FOLR 加评价合理，但原报告的 SE 上界与因果承诺过强

由 B01 两臂 32 个完整终点回报重算，样本 SD 分别为 **6.8881、7.9968**。忽略协方差的差均值 SE 为 **1.8658**，并不是上界。若两个终点均值来自可合法配对的随机变量，

`SE(diff)² = (s_RETAIN² + s_RESET² − 2 cov)/n`。

仅知两个边际 SD 时，该表达式允许的 SE 范围约 **0.1960–2.6313**。当前相同 seed 不保证相同外生交通流，不能擅自给出配对因果精度。B02 的零协方差近似为 **1.9047**；两个训练对差值的描述性均值 **−1.9625**、SD **0.05613** 也不足以宣称训练方差很小。原始数组见 [B01 summary](../../../candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_RESULT_SUMMARY_20260909.json) 和 [B02 summary](https://github.com/CartmanFatass/My-paper-code/blob/429e4df7bbb1712ffe98917ca50183093374203d/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_RESULT_SUMMARY_20260909.json)。

下一对象用 128 个最终 episode 是合理预算选择：固定策略、独立评价抽样下，可望比 32 个降低条件误差；不降低训练实例不确定性，也不是所有 FOLR 后续统一的最低数。应一次冻结，不看结果再追加到跨过 MEI。

随机重置值得比较，但“事件 reset 优于随机 reset”只支持所比较训练系统中的时机价值。事件、动作和成员流相互影响，三臂分别训练；即使效应出现，也不是纯粹定位了哪段记忆过时。随机重置同样好，只削弱该事件律的独特优势，不能自动确认“正则化”是原因。[FOLR Pro](../../../candidates/vap_folr_core/pro_packets/20260909_p78_public_lifecycle_convergence/archive/RESPONSE.md)。

### 3.6 RCLE、归一化与 ACVC 应按实际干预解释

RCLE 的 actor100 是把更新方向从 `g_M+g_A` 改成 `g_M+100g_A`，再固定整体步长范数 `.02`；不是多训练 100 倍。W100 失败且未知前缀，不能推断训练无效，也不能用完成的 W1 代替该比较。已有 A02 正是在研究梯度来源；下一步若值得花钱，应是解决缺失比较的可行性，而不是再做一轮泛化的“是否能学”诊断。[RCLE Pro](../../../candidates/roster_consistent_latent_exploration/pro_packets/20260909_post_a02_innovator_recovery/archive/RESPONSE.md)、[最终 intake](../../../candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_INTAKE_20260909.md)。

UCOPE 的联合梯度裁剪确有耦合通路，但“raw critic 饿死 actor”仍是假说。Adam 对持续的统一梯度缩放有近似抵消，不能只看 critic loss 大或裁剪后的 actor 梯度小就诊断更新停滞。此次两臂 actor 都发生参数移动，normalized 的 actor 位移还较小；这也不单独证明因果。若后续确有优化问题，在已选训练内记录少量分组梯度和实际更新摘要即可，不为此新建长期遥测或诊断普查。

ACVC 的 F−C **+0.09626/+0.10784** 值得保留，但两次 native 比较都依赖同一个事后选中的 DENSE8201 proposer。F 的 retrace 规则固定，底层 proposer 仍是训练过、带循环状态并采样动作的策略。因此它是有条件的执行规则发现，不是“完全无训练的确定性方法在两个独立基础 fit 上胜出”。链路丢失也不是 roster churn。[ACVC Pro](../../../candidates/acvc/pro_packets/20260909_native_link_loss_followup_convergence/archive/RESPONSE.md)。

## 4. 十方向的研究判断

以下“建议”都是本报告的非执行性建议。具名 Pro 停止保留原范围；提出更有价值的新问题，不等于本报告已重开该对象家族。

| 方向 | 当前证据最能支持什么 | 后续建议及改变建议的证据 |
| --- | --- | --- |
| **FOLR / N3** | 两个 public-lifecycle 训练对都支持 RESET 的有限终点优势；真实成员事件、续存者与实际 reset 已记录。第三个不变训练对已分配。 | 现有第三对按其分配推进，之后优先评估三臂时机候选。若事件方案只胜 RETAIN 而不胜随机方案，保留状态管理价值、缩小事件专属解释；若新比较反向，保留混合性，不自动迁移。 |
| **UCOPE / K3** | fixed short F 相对 G 有收益，H 对照结果混合；normalization 这次 WITHIN。尚未证明学会了续约或付费取信息。 | 优先准备 raw F/G 的连续训练曲线比较。若差值随普通 G 改善而消失，就不再围绕 512 endpoint 复制固定律增益；若仍有任务收益，再问 learned duration。 |
| **ACVC** | outcome-informed 固定 proposer 上的 F 规则有较大 native 收益；学习选择器输给 F。 | 保留 F 作为候选强对照。优先于新选择器的是检查 F 对另一个现有 proposer 和 dwell 控制是否有价值；若仅选中 fit 有效，不扩大主张。 |
| **VSP03 / K1** | 三个 greedy G−R0 值混合，均远小于 .02；stochastic 执行更差；计算很便宜。 | 可排入小预算连续训练检查，非必做。若更长预算仍无有用收益，结束这个普通 G 用途；若出现收益，先做有限重复，不直接跳到 10 seed。 |
| **RCLE / N3** | W1 完整；W100 和参考缺失，没有配对效应。 | 原 CM 可行性判断先行，投入有上限的技术恢复。只有能保留冻结语义、明确失败效应及新调用额度，才考虑补足比较；故障不是方向阴性。 |
| **FSD / K1** | .25/k10/五次更新包在两个实例有效负向；额外 gap 在终点未触发，训练中触发。 | 当前包的停止合理。仅在采样用途本身值得研究时准备隔离面板，优先级低于前两项；零 gap 不构成修复需求。 |
| **VSP-C1 / K4** | 延长训练已使若干早期 GATED 优势消失；新 B13 完整负向，且新增 gate 的参数数并非严格匹配。 | 保留当前包停止，复用曲线教训。重新投入需要一个解释力更强且比较明确的表示问题；不以 UCOPE 阳性作为准入条件。 |
| **SCDMP / K4** | residual B01 +0.0067374、条件 SE .0055965，非零约束实际发生；不足以展示所选尺度收益。 | 不做不变重复。二次 recast 已带来最低争用顺序，不需再以 H 附近为理由自动改 HIGH→LOW。停止本次投入不等于整个 residual 家族失败。 |
| **MGTAP / N5** | native REL−DENSE 两实例一负一小负；DENSE 本身两次高于 H。 | 保留当前 geometry actor 家族暂停。共享 DENSE 的参照价值；固定槽数的 mean 与 sum 可由线性缩放吸收，单换 pooling 不是充分的新假说。 |
| **CRTO / K2** | 选中历史上的诊断完整，competent-reference 限定未建立；记录的 RAW regret ceiling 低于 .0025。 | 保留当前 selected-panel 停止。重新进入需要会改变决策的控制机会或信用路径，不能因为修好了 finite-zero 检查就恢复原科学问题。 |

SCDMP 与 CRTO 的细节分别来自 [SCDMP Pro](../../../candidates/semigroup_consistent_duration_model_policy/pro_packets/20260908_held_residual_context_repair/archive/RESPONSE.md)、[CRTO Pro](../../../candidates/commitment_residual_triggered_options/pro_packets/20260908_post_b08_convergence/archive/RESPONSE.md)。MGTAP、VSP03 的正式范围见 [MGTAP Pro](../../../candidates/metric_ground_transport_allocation/pro_packets/20260909_post_b01_convergence/archive/RESPONSE.md)、[VSP03 Pro](../../../candidates/vsp_03/pro_packets/20260909_post_b05_convergence/archive/RESPONSE.md)。

## 5. 建议的最小实验批次

### 5.1 UCOPE：把预算曲线放进 F/G 比较

**决策问题：** 现有短保持 F 的收益，到了普通反馈 G 有更多学习机会时，是否仍有任务价值？最低证据类别为 B/EXPLORE；一个训练对首先给出有限轨迹证据，不估计稳定的跨 seed 优势。

**比较与预算草案：** 一个新 master，独立训练 raw F 和 raw G，各 2048 episode；F 沿用固定 `{1,2}`、各半概率，duration head 不训练。保留当前原生五 UAV、256 步、信息边界、每步 GRU 更新、gamma、loss、Adam 与 sampled 评价。只改总训练预算和预定评价安排，不同时加 normalization、reward shaping、critic 架构或新上参考。512/1024/2048 三点各评价 64 个 episode，最后 2048 是主终点，H 在同一冻结评价世界集上计算一次。评价状态/RNG 与训练隔离，normalizer 冻结，全部端点保留，不选最佳 checkpoint。扩展 episode 数后，旧卡 `b+1000+e` 训练 reset 区间会碰到 `b+2000+e` 评价区间；新卡必须为训练、评价 reset 分配互不重叠的键空间，不能只扩大循环次数。[原 F/G 卡 §§2–5](../../../candidates/ucope/UCOPE_UAV_SHORT_FIXED_RENEWAL_B03_SCIENCE_CARD_20260909.md)。

**主要量：** 每点 F−G、F−H、G−H；2048 的 F−G 为主，沿用 .01 J 作为当前候选的实用效应尺度。并列看完整曲线，而不是从三点中挑阳性。H 检查实际价值，不是 B 有效性门槛。

| 预先分支 | 如何改变下一步 |
| --- | --- |
| F−G 的有用增益在 2048 保留，且 F 相对 H 有益 | 值得考虑第二个独立训练对；再比较可学习 duration 与固定律。仍无稳定、纯时长因果或付费信息主张。 |
| G 随预算改善，F−G 收缩、消失或反向 | 记录固定律的早期预算效应；不继续仅复制 512 的优势。是否投资样本效率问题由其用途决定。 |
| F 胜 G，但二者仍低于 H | 包比较有效，实际用途价值有限。优先明确一个具体学习假说或有实际用途的新 host 条件，不从此推出奖励无梯度。 |
| 两条曲线混合或对 .01 的分辨力不足 | 保留不确定性；只有第二个训练对能改变选择时才买第二对，负向或混合结果也可以成为重复理由。 |
| 技术缺失 | 完成部分按原单位保存；不补值、不从失败推断科学阴性，不自动续跑。 |

机器计数：两 fit 共 **4096 训练 episode、1,048,576 训练步、8192 Adam 调用**；评价 **448 episode**（2×3×64+64），计 **114,688 步**；总 **1,163,264 native 步**。按原卡的 `6×训练 renewals + 2×评价 renewals`，本草案 F head 为 **8,110,080–16,220,160 rows**、每 row 2208 dense MAC，共约 **17.91–35.81 G MAC**；这是独属于 F 的有界额外工作，不能把两臂参数数相同当成相同计算量。

按原 F/G 完整 pair 约 314–318 秒外推，提议预算约 **20–30 分钟 summed wall**；提出 **1800 秒/完整臂、3600 秒/整项**的卡上限，均为新计划数，尚非已分配额度。工程只需现有 runner 的预算/固定端点评价、RNG 隔离和曲线输出；不新增恢复系统或 checkpoint 选择。若原训练器已有足够钩子就复用，不能把估计代码行数当作验收或成本保证。

### 5.2 FOLR：三臂比较重置时机

**决策问题：** 在已有两次 RESET 优势之后，成员事件对齐是否比一种不对齐事件的重置律更有价值？类别 B/EXPLORE。当前第三个不变两臂实例的已分配额度不用于这项候选；其结果进入下一次选择，可能降低或提高三臂比较的价值。三臂分别训练 RETAIN、RESET-on-event、RESET-random，保留 public lifecycle 信息、真正续存者集合、训练器与 20 步 TJ 主机。online 与 target unroll 必须使用各自同一状态规则；评价时不学习参数。

**随机对照必须在新输出出现前说清：** 对每个实际续存者，在读取下一个观测前按独立外生随机律决定是否清零；新生/不活动 slot 的共同清理保持不变。将实际 random-reset mask 随轨迹保存，供 online/target replay unroll 一致复用，不能在每次 replay 时重新抽样后继续把它当成原行为历史。若要称“同频率”，概率应由既有开发轨迹中“事件清零次数/全部合格续存者机会”的定义算出并冻结，随机流与交通和探索隔离。现有汇总的 `survivor_opportunities` 是事件下的机会数，并非所有时步续存者分母，不能直接据此宣称频率匹配。该分母能否从保留日志恢复，是卡冻结前一个具体未决事实；只读日志即可解决，不值得另开科学普查。

若分母没有保存，最小可执行替代是明确使用固定 Bernoulli `p=0.1` 的候选控制，称“一个预设随机重置律”，不称频率匹配或纯事件因果实验；`.1` 只是每个合格续存者平均十次机会重置一次的稀疏控制，没有最优性依据。若所要决策必须严格区分时机与频率，就应先把这点设计清楚，而不能在新三臂结果出来后调 p。也不能用当前试验中处理臂诱发的未来事件去匹配、强制回放或筛选另一臂。

**训练与评价草案：** 一个新三臂训练实例，各 5000 episode/100000 ticks/4969 RMSprop；各 128 个预定 greedy 最终 episode。总 **15000 训练 episode、300000 训练 ticks、14907 更新、384 评价 episode、7680 评价 ticks**，合计 **307680 native ticks**。新评价键预先分配；相同 seed 标签不作为外生事件已严格配对的证明。主要量为 event−retain、random−retain、event−random，保留所有回报及各臂实际事件、清零计数。

沿用原单位的 **1 回报单位**作为候选实用效应尺度。event 同时有用地胜 retain 与 random，支持继续检验事件时机价值；两种 reset 相近且都胜 retain，保留重置作为强对照，降低事件专属解释；混合或反向则结束这次投入并按完整证据重新比较下一对象。零计数或暴露不足限制解释，不能丢弃结果。各分支都不自动证明“过时记忆”或“正则化”。

B02 的实测每臂约 753–768 秒，三臂训练加上述评价估计 **38–45 分钟 summed wall**；建议卡上限 **1800 秒/完整臂、5400 秒/整项**。这比再做数个不变两臂对更能区分下一研究选择，但不会把128次评价等价成128次训练重复。

### 5.3 便宜候选与暂缓项

**ACVC：先检查固定 F 的复用价值。** 若两份既有 DENSE8201/8202 checkpoint 可用，分别在新的 64 个 native 世界上评价 C、F 和 dwell 控制；dwell 在相同自身链路条件及同一 proposal 条件下发零速度，F 按已有定义逆向上一实际位移。这样比较“回撤”相对“少移动”这一更具体的问题。零新 fit、2×3×64 = **384 评价 episode/98304 步**，仍是新的科学评价，不能因为不训练而冒充零暴露 A。两个基座是旧训练实例，且8201是事后选择的；保留这种选择条件，不能声称两个新独立训练对。checkpoint 可用性和该模式的完整耗时尚未在本报告实测，因此排在有明确成本参照的两项之后，不先承诺“免费”。

**VSP03：选择一个小预算检查，不做15次独立网格训练。** 可先选3个新 G fit、各连续512更新，在128/512处评价；每点保留 greedy、stochastic、R0、R 各1024世界，主终点固定512，不选最佳。总 **196608训练 episode、7864320训练 ticks、1536 Adam**；按每点四面板保守计 **24576评价 episode、983040评价 ticks**，合计 **8847360 ticks**。旧128更新整项4.191728秒只提供外推依据，估计为分钟量级；建议60秒/完整fit、180秒/三fit的候选上限，是否足够由原 CM 依据实际工作量确认。暂不预分配2048：若512曲线提出了会改变选择的具体剩余问题，再选下一预算。原 `.02` MEI 与 R/R0 不变，采样优劣不能单独诊断收敛。更长训练是新问题，仍需处理原 Pro 停止的具体范围。

**FSD：若真的研究采样用途，先明确要分离哪件事。** 不推荐现在把 `.25` 包原样再训一对。可选的新 B 是：新 D0/I 各一 fit，保留两臂旧 deterministic 面板、两臂 sampled 面板，再对同一 I 权重增加“同 sampled primitive 模式但禁止额外 gap”面板。这样最后一项才直接比较该固定 I 下额外终止的执行影响；它仍不是整体训练机制的纯因果效应。按原训练80,000步和五个32×500评价面板计，约 **160,000总步**，完整耗时尚需按 evaluator 成本重新投影。旧 runner 在内存中同步 evaluator，本轮没有核实可恢复的旧 checkpoint，不能先承诺无须新训练即可重评。现有 Pro 停止与新增用途的价值须先在原节点说明。

**RCLE：恢复比较的可行性优先于新诊断。** 保留 W1 与失败事实，原 CM 用已留诊断提出一个有界修复方案；若能恢复精确语义，原 DM 再明确是否补 W100/参考或重新分配完整比较及其调用预算。未知训练前缀不允许盲重试或假定零消耗。本报告不预分配这一技术上尚未定界的运行。

## 6. 成本、顺序与研究产出

### 6.1 先比较诚实的成本窗口

这十个方向在本报告所涉当前主机上都没有完整的“上参考−调优同信息 baseline” headroom 记录。历史 toy、固定 H、选中 RAW ceiling 或前后初始化差不能移植为当前记录。应在相关比较中积累参照和预算证据；缺记录不成为普通 B 的停止条件。

| 方向及明确窗口 | 一个有效结果自身的已知计算 | 已接受尝试计算/有效结果 | 主机或重要限制 |
| --- | --- | --- | --- |
| UCOPE /8501 | 303.11 s 完整过程 wall | 同窗口1接受/1有效：303.11 s | WSL CPU FP32/1线程；aggregate CPU未测 |
| FOLR B02 | 1520.95 s 两臂完整科学wall之和；含已测支持操作1528.79684 s | 2臂接受/1完整pair：科学wall1520.95 s；同支持窗口1528.79684 s | WSL CPU FP32/1线程；CPU1523.30 s、关键路径1622 s另记 |
| FSD P72 | 1768.78 s 两臂wall之和；CPU7016.85 s另记 | 2臂接受/1完整pair：1768.78 s | WSL CPU FP32/4线程，不能与单线程wall直接排名 |
| VSP-C1 B13 | 477.99 s 完整调用 | 1接受/1有效：477.99 s | WSL CPU FP32；aggregate CPU未测 |
| SCDMP residual B01 | 323.02 s 完整pair过程 | 1接受/1有效：323.02 s | WSL CPU FP32/1线程；checks另记 |
| MGTAP native B01/P75 | 722.64 s 两master完整窗口 | 两接受native提交形成1两master聚合结果：722.64 s | CPU FP32；单pair353.71/368.12 s，关键路径899.40 s另记 |
| ACVC native B01/B02 | 373.40697/362.98968 s，各含必要检查 | 两窗口共736.39665 s/2有效 = 368.19833 s | CPU FP32/1线程；两项共享同一选中proposer |
| VSP03 P76 | 4.191728 s 完整调用 | 1接受/1有效：4.191728 s | CPU FP32；CPU3.500596 s另记 |
| CRTO B08/P71 | 169 s 完整诊断包 | 1接受/1有效诊断包：169 s | CPU FP32/1线程；不是有效的合格对照效应 |
| RCLE actor100 B03 | 没有有效配对结果 | 分母0，未定义；132.54 s链与160 s保守计费是不同窗口 | CPU FP64/1线程；不能写成0成本或一个负结果 |

来源为[当前 Portfolio 的注明窗口](../../PORTFOLIO.md)、[FSD P72 成本](../../../candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_INTAKE_20260909.md)、[VSP-C1 B13 成本](../../../candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_INTAKE_20260909.md)及第2节新结果。完整历史尝试、工程/控制平面时间尚未聚合的项目仍记未测；表中 scoped 均值不是方向全历史成本，不能凭这些数计算通用“效应/秒”排行榜。

### 6.2 顺序是可修改的投入建议

1. **先与已有结果和分配对齐。** UCOPE /8501 与 FOLR B02 的科学 intake 已集成；FOLR 第三个不变训练对已分配，沿其原卡推进，本报告没有改种子、预算、臂或终点。复用 VSP-C1 既有曲线和本报告的 FSD 直接代码事实，不增设资格实验。
2. **准备 UCOPE 曲线对，并在 FOLR 现有第三对之后评估三臂候选。** 前者同时回答预算与固定保持的用途，后者在当前两次同向证据下有较直接的新信息，但要读入第三对的全部结果并先写清随机对照的频率/主张界限。UCOPE 准备不依赖 FOLR；两项候选各自成立且资源允许时可独立推进。
3. **保留小额候选。** VSP03 有很低的已测学习成本；ACVC 有可复用的较大条件效应。选择哪项取决于准备成本和能否改变下一步，不由绝对效应大小直接决定。RCLE 的技术恢复与上述科学计算可以独立准备。
4. **不购买不变的 SCDMP、VSP-C1、MGTAP、ACVC selector、CRTO 或 FSD 当前包重复。** 这是边际信息判断，不把所有方向整体 PARK，也不限制合理的新问题。

两项核心候选比较估计 **约1–1.25小时 summed invocation wall**，不含已分配的 FOLR 第三个不变训练对或尚未实测的工程工作，也不宣称并行 elapsed。把第二个 UCOPE 训练对作为条件追加，约再20–30分钟；不是提前买3×8192普查与后续3×8192算法比较。各臂上限、外推误差及实际资源 admission 在正式卡/执行中分别处理；43200秒UAV调查阈值不是可花预算。现有 remote-first、精确提交、逐调用内存准入、detached执行和指定观察责任足够，无需新建调度器或审批层。

### 6.3 下一阶段应形成算法问题，而不只累积诊断

**N 线候选：成员事件下的选择性状态保留。** FOLR 如显示值得继续，可在 public-lifecycle 信息边界下比较 learned retention 与 RETAIN、RESET 和已声明的随机律；或先把最简单的 RETAIN/RESET 比较迁到一个明确的 UAV 失效/加入任务。迁移只改变一个事件问题，控制器、奖励与 primitive 动作尽量复用。真正的用户价值是事件后服务与恢复，不能用 reset 次数或事件条件子集替代完整 native return。无需等固定五机 H0 达到某个统一阈值，但新 host 必须有实际成员事件、可用对照和明确任务效应尺度。

**k 线候选：学习持续时间是否超过固定律。** 若固定 short F 的用途仍在，下一算法比较可以只学习一个 duration/termination 选择，直接对照固定 F 与合法每步 G，保留相同信息和信用/预算口径。即使固定 F 不稳定获益，也可以因一个具体的新预测选择学习型对象，不能把“固定律先阳性”发明为全局门槛。当前 F 每步仍读观测与更新 GRU，不能把它的优劣写成节约信息获取成本。

之后若要形成 C-BENCH 主张，再按选定的实用性、跨训练重复和跨场景问题规划验证。没有由本报告推出的固定 seed 配额、先完成普查/因果解释的条件，或仅因一个点结果就自动升级 UAV、升优先级的规则。

## 7. 依据如何改变了建议

| 背景知识 | 这次具体改变了什么 | 推断边界 |
| --- | --- | --- |
| 状态/观测/记忆递推与参数学习不同 | FOLR/ACVC 的固定规则可以影响真实学习系统；FSD 零终止不等于零学习 | 没有因此识别唯一的内部机制 |
| CTDE 与同信息公平比较 | 共享 host 允许共享参照，但不把不同 critic/策略包当成一个 learner；特权脚本单列 | 不要求所有方向换成一种统一算法 |
| primitive 动作、观测刷新、duration 与高层决策时钟不同 | FSD 采样切换需要分离底层动作；UCOPE 每步读观测不支持 paid-information 主张 | 不是要求精确 Bellman 闭合后才做 B |
| 训练单位、评价噪声、选择偏差不同 | 保留单对点结果；增加冻结评价面板，减少事后挑seed/预算/基座 | 少量训练重复仍不能保证稳健性 |
| §11.8 的比例原则 | 用小 B 直接比较活选项，复用已有曲线和诊断 | 经济起点不等于充分性；失败与未测仍明确报告 |

外部主文献仅用于校验这些一般判断，不代替 HMASD 实验：Engstrom 等的 [Implementation Matters in Deep RL](https://arxiv.org/abs/2005.12729) 摘要支持“实现选择会影响有限训练结果”，不能诊断本项目的具体 PPO 问题；Agarwal 等的 [Deep RL at the Edge of the Statistical Precipice](https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html) 摘要强调少量运行下的不确定性，不提供统一 seed 配额；Jung 等的 [ACAC](https://proceedings.mlr.press/v267/jung25a.html) 摘要提供异步动作/信用处理的相关方法背景，不构成本轮必须移植的 baseline。

实际检索先查看了本地 My-lib 和 Inst-sci 索引：前者当前默认 registry 的 synthetic fixtures 被排除；后者检索了190条元数据中的相关题名，没有把本地未命中写成没有相关研究。上述外部依据仅访问了列出的摘要/官方条目，未声称完整论文复核或新颖性检索完成。数值重算及方案暴露计数使用 Python 标准库；没有额外科学执行。

## 附：可复核来源

- Claude 文件在本轮未提交，读取内容 SHA256：`523640fb5787dce3e3c700c42e21ae86abd2baa94d9e3aa735458685c9a6e888`。其“无spec版/有spec版”原提示都在本目录；本报告不是提示词对照实验。
- 基础知识：[FOUNDATIONS §§1–6](../../../../rl-marl-foundations-20260907/FOUNDATIONS.md)、[01_RL](../../../../rl-marl-foundations-20260907/topic-notes/01_RL.md)、[02_MARL](../../../../rl-marl-foundations-20260907/topic-notes/02_MARL.md)、[03_HIERARCHY_ASYNC](../../../../rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md)、[04_EMPIRICAL](../../../../rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)。
- 规范：[MARL empirical evidence §§11.7–11.10](../../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)、[工程范围](../../../../project/ENGINEERING_SCOPE_SPEC.md)、[运行时工程](../../../../project/MARL_RUNTIME_ENGINEERING_SPEC.md)。知识是解释依据，当前卡/spec 决定历史结果应如何读取。
- UCOPE 当前选择的完整来源：[post-mean-velocity Pro](../../../candidates/ucope/pro_packets/20260909_post_mean_velocity_b01_convergence/archive/RESPONSE.md)；本报告其余九个方向 Pro 正文及专项复审均已在对应论断旁链接。
- 直接代码核验聚焦 [FSD agent](../../../../../hmasd/agent.py) 的 `_batched_assign_skills_d2` 与 primitive action 调用，及 [FSD runner](../../../../../scripts/run_fsd_uav_individual_renewal_b01.py) 的 evaluator 同步。对照 FSD 冻结源 `08199a932671d9bacdbe4eb0bfebab38c37fca1f`，这两个文件与阅读时 main 的差异为空。UCOPE 联合裁剪判断按其 normalization 执行源中的 learner 路径核验，不声称运行复现。
- 没有重新逐字节核查 Claude 声称读过的20项全部材料，也没有把它的阅读声明当作本人的覆盖证明。本报告以正文列出的 Pro、关键原始结果和直接争点代码为实际复核范围。

本报告交付的是可审阅的下一步方案及其修改理由。任何后续正式卡、方向重开或跨方向投入决定，都应保留这里的新结果和反证，并通过已有 DM/适当节点处理；本报告没有发起新的 Pro Send、实验或状态修改。
