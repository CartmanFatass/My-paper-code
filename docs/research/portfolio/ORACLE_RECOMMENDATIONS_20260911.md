# HMASD 当前 Oracle 科学建议 — 2026-09-12

作者：Root 指定的 Portfolio 材料与科学核对 DM，`/root/dm_a_mx_portfolio_resume`。本次按 owner 要求覆盖当前建议页；旧版由 Git 保存。本文是科学建议，不是 Portfolio 决定、实验卡或新增运行预算。

**当前应继续 ACVC 验收后的具体用途/下一问题准备、FOLR 原未执行配对的工程恢复，以及 VNFC 已获条件资助的新配对准备；RCLE 继续恢复同一 Pro 请求。其余方向没有隐藏在 Monitor 或 Transport 中的在途实验。五个独立方向槽位仍是执行目标，不能用已完成记录、待定请求或这份跨方向审阅补足计数。**

本次逐一核对 22 个 DIRECTION 的相关当前段落、最新结果/技术 intake 和适用决定。科学证据基线为已发布 main `d24e49025`，在共享 `codex/portfolio` 合入为 `1c50e6857f5b0e89c149efcd12fc297dc4a52aa4`；ACVC 最终 intake 已由原 DM 发布为 `48b278091`、Root 集成为 `77c17d111`；后续 VNFC 恢复派发及独立任务迁移为 Root 本轮回执事实。未重跑、重算各方向原始实验，未独立检查远端运行或浏览器。实时数量与新任务入口以 [PORTFOLIO](PORTFOLIO.md)、[EXPERIMENT_TRACKING](EXPERIMENT_TRACKING.md) 和主控配置为准。

## 当前就绪判断

Root 已交付三条实际方向工作：ACVC、FOLR、VNFC。RCLE 尚无已确认 provider Send/生成，在确认前不计推进槽；没有被这次审阅确认的运行中实验。独立 Monitor 的空集合是合法空闲状态，不能为了显示运行而创建空目标。Transport 的工具/浏览器修复影响请求传输，不产生方向科学负面结论。新 Root 与新独立任务的当前路由由 Root 维护；本文不复制会过期的会话 ID。

- **ACVC：**五个完整训练单位已给出冻结的 qualified JOINT_ABOVE_MEI，C01 满足消费条件。最终英文 intake、DIRECTION 与预测已经完成并集成；当前 DM 准备原 Convergence 的最小下一问题及用途，不做第六个 fit。新问题/对象尚未选择或获得新增预算。
- **FOLR：**原 B03 科研配对尚未执行，owner 已明确 300 秒 support 是参考；308.8422538 秒不能单独挡住恢复。原每臂 native 1350 秒、两臂 native 2700 秒与科学定义保持。RETAIN 是有 GRU 历史适应的合法强对照。
- **VNFC：**Portfolio 已给一个新的条件配对，科学款为 native 总计 600 秒（含参考）、support 300 秒、complete 900 秒；旧失败 B02 不复活。Root 已接续有限工程工作。接受相关最小修复或有证据的同义独立路径，不能仅凭绕开 Fraction 调用就宣布内存问题已修好，也不要求完整还原全部历史。
- **RCLE：**只恢复 `2026-09-11-rcle-channel-normalization-convergence-01`；未确认 Send 不等于已在生成。完成后按原节点答复 intake，不能把“发出恢复消息”当作选择了方法或实验。

除此之外，本次没有发现另一份已接受、无实质依赖且可直接执行的现成研究分配。Root 应持续派出实际就绪工作；不足部分需要具体新投资选择，不能把“上一个分配结束”扩大成永久无研究价值，也不能反过来把空位当新预算。

## 15 个 ACTIVE 方向的科学与接续边界

下列 Priority 是现有 Portfolio 登记。MEI 只在自己的宿主和量纲解释；表中未选的未来问题都不是运行授权。所有这些方向均缺少匹配当前宿主的“明确上参考 − 调优后的同信息通用基线”完整 headroom 记录；固定规则、未调参比较或历史精确零差不能代替它，缺失也不阻止合法 B。

| 方向 / Priority | 最新直接证据与最强限制 | 当前动作；未来真正能区分什么 |
| --- | --- | --- |
| [ACVC / MEDIUM](../candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md) | 五 fit 的 F−C 为 +0.09591597，区间 [0.07485046, 0.11698148]；F−dwell 为 +0.06513377，[0.03828639, 0.09198115]，两个下界均超过 MEI .01。区间只按预设 iid-normal fit-panel 模型成立，实际神经训练校准未证明；46/320 个 F−dwell world 差为负。 | 最终 intake 已完成；下一用途/问题准备在做。支持固定完整执行方案的限定收益，不支持 learned selector、纯 retrace、等剂量或一般历史必要性。recasts 2，保持最低争用排序。 |
| [FOLR / MEDIUM](../candidates/vap_folr_core/FOLR_LEARNED_RETENTION_B02_INTAKE_20260911.md) | learned retention gate−RETAIN 的两次完整差为 +1.763359375 / −1.769531250，MEI 1，方向相反。gate 移动不能解释收益；普通 GRU 已能适应。 | 继续原未执行 B03。一次原样新配对可改变是否保留可选 gate 作为同宿主开发候选；不设置第三次必须阳性、全机制归因或自动第四对。 |
| [VNFC / HIGH](../candidates/variable_n_fleet_churn/VNFC_N7_NATIVE_SERVICE_CREDIT_B02_RESULT_INTAKE_20260911.md#portfolio-conditioned-static-intake--2026-09-11) | B02 exit139，480 次已记录更新、无最终 primary，预测未评分。精确解释器公式需 40 字节，offset32 的 False 合法；与保存的 32-byte 元数据矛盾，尚未证明写坏者。 | 新条件配对工程恢复在做。若路径可信，首次完整 INTERVAL−TERMINAL recovery（MEI .02）及全 J/分区代价可回答时间信用问题。相关 focused 证据即可；科学款不是调试费。recasts 2。 |
| [RCLE / MEDIUM](../candidates/roster_consistent_latent_exploration/RCLE_B06_NEAREST99_PRIOR1000_RESULT_INTAKE_20260911.md) | B06 reference contrast −.00575765，八个 service cell 全输 attained nearest；相对自身初始化 −.00010783。旧 W100/W1 的真实大幅学习收益保留，不能替代 reference 缺口。 | 同请求 Transport 恢复。后续应区分在有竞争力的起点上新增的学习收益，保留 nearest 与 fragmentation；不是概率扫描或“更多参数移动”证明。 |
| [FSD / HIGH](../candidates/flexible_skill_duration/FSD_UAV_RENEWAL_BATCH_B02_771103_INTAKE_20260911.md) | I1280−authentic D0 三次为 +.05697747 / +.20628590 / −.01243043，MEI .01；最新 16 正/16 负且无额外 endpoint individual-gap，I 约为 D0 的 2.17 倍 wall。旧 batch128 负值另列。 | 分配完成；F+U 明确不增 FSD 问题或实验。未来问题需说明要改变哪项实际使用/研究选择；完整方案复现与 isolated renewal/批量因果不是一回事。 |
| [MGTAP / MEDIUM](../candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8213_INTAKE_20260911.md) | COND−intact DENSE 为 +.00576132 / −.02246957；第二次 5 正/27 负，MEI .01。真实 branch 更新没有挽救负 native primary；两次不能推出稳定劣势。 | 两配对完成，DENSE 保持；无第三对、诊断或咨询分配。健康的既有执行路径使未来有限 B 可具体定价，但第三次原样结果是否会改变选择仍需论证。 |
| [UCOPE / HIGH](../candidates/ucope/pro_packets/20260911_post_8801_convergence/INTAKE.md) | 最新 8801 L−F = −.02410561，MEI .01，40/64 world 负；完整 native 1384.14 秒。只有一个 L/F 配对；旧固定短 F 的收益和 8703 的原生/H 改善保留。 | post8801 已窄 PARK 此固定五 UAV、own-expiry {1,2}、final2048 的 continue/end-credit L 配方，无 successor。不是所有 renewal/ordinary feedback 停放；不能继续沿旧 8701 状态派发。 |
| [SCDMP / HIGH](../candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b02_convergence/CONVERGENCE_INTAKE_20260910.md) | B01 +.00673741、B02 +.00365806，均 WITHIN .01；真实 residual 非零，B02 MLP−H 为 −.00065955。两正点和条件不确定性保留。 | post-B02 已窄 PARK opening t1–3→同 episode t4、full-MC、系数 1 包，无第三对/修改/诊断。具体新 loss/credit 或有用途的复现仍可提案，recasts 2。 |
| [DISH / MEDIUM](../candidates/degraded_incumbent_shadow_handover/DISH_POST_B08_CONVERGENCE_INTAKE_20260910.md) | B08 HALF_RETAIN−REPLACE 为 −6.5 service ticks，WITHIN ±24；四条件 −15/0/−8/−3，额外四个 invalid commit，能耗较低。ordinary CAS 为零，source-origin 效果未估计。 | REPLACE 默认；retained-A03 arrival-bridge retention 家族窄 PARK，无 successor。未来要有具体 receipt→控制→native-service 问题，不能用旧 P62 DIRECT 代替当前方案。 |
| [VSP-C1 / MEDIUM](../candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_P81_CONVERGENCE_INTAKE_20260909.md) | B13 GATED−完整 MLP 为 −.03206858，25/32 负；MLP−H +.03556246。旧 512 正值与单配对限制保留；head/body 参数差异存在。 | P81 结束 tested intact-body+gate、768/final 包，无 successor。合法 hold 信息经 critic/训练链的更广问题仍在，不能把早期 checkpoint 收益当最终收益。 |
| [CBSC / HIGH](../candidates/capability_bound_semantic_currentness/CBSC_P47_TECHNICAL_UNBLOCKING_INTAKE_20260911.md) | 两个旧完整 RAW/STRUCT 表达差为零。新 B04 RAW 12.0375 低于 REQUEST_ONLY 12.375，STRUCT 无最终比较。source-only 六替换/AST 路径已验证，不是 production 修复。 | 无在途任务，retained52 未跑/未分配。完整且可信的 RAW/STRUCT 同信息 native 比较仍有未答问题；新路径不必恢复所有旧 publication/故障史，旧未知 turn 拒绝不能泛化为全方法禁令。 |
| [FRRIE / HIGH](../candidates/finite_resource_relational_inductive_efficiency/NATIVE_CRASH_P63_STATIC_UNBLOCK_INTAKE_20260911.md) | R06 N15 +.005548 超过 .005、R07 −.001948；R08 是既有 fit 的分析。P59/P63 九帧 source-only 观察成功，factory fault 未定位；崩溃不是算法负值。 | 无 production patch 或新 P63/R09 allowance。未来值得选择的是能恢复完整 native 比较的最小可信路径；不重复已完成 AST 观察，不把定位全部历史写坏者作为一切研究门槛。 |
| [CRTO / MEDIUM](../candidates/commitment_residual_triggered_options/CRTO_POST_B08_P72_CONVERGENCE_INTAKE_20260908.md) | RAW/TRUE/DERANGED 在 16 决策上相同；matched alignment gain 为零。记录 RAW 的 .00212945 regret 上限小于旧 .0025 MEI；RAW 有真实 native 学习但仍不满足原 competence 解释。 | P72 保留 selected-panel balanced residual family PARK，无 successor。新合法 action/credit 问题可以另提，不为保留旧阈值再做 census 或换弱对照。 |
| [VSP02 / LOW](../candidates/vsp_02/VSP02_TEAMMATE_POLICY_CHANGE_POST_B01_CONVERGENCE_INTAKE_20260907.md) | 两个 independent prefix 的 RESET−CARRY 为 +.01855469 / −.00878906，均远小于 .5 deliveries MEI；不能据两次小差作等效结论。 | P19 结束固定成员/通知 teammate policy switch/P4096-Q1024/full Adam RESET 包，CARRY 默认。原成员恢复问题未解决，无 successor 或 UAV 分配。 |
| [VSP03 / LOW](../candidates/vsp_03/pro_packets/20260911_question_fallback/archive/RESPONSE.md) | 四个分别保留的 fixed512 G−R0 终点 +.02599609 / +.01450684 / +.00968750 / +.01156738；最新 Q512−128 = −.00160645。MEI .02，不构成稳定胜利。 | post-B07 与 9/11 fallback 均维持 ordinary-G continuous512/publicN2/fixed128–512 greedy family 暂停，无 successor。历史单 fit 约 8–9 秒，仍须算完整必要工作；原样 B 合法但本轮没有新使用决定支撑重复同一咨询。 |

UAV 计数需要方向决定、卡和真实执行三者相连。本轮核实了 [UCOPE B01 卡 §9](../candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#9-observed-p21-completion-and-uav-entry--2026-09-07) 的明确 entry 记录；其余若只是用了原生 UAV host，不能由此新认定已正式进入。尤其 ACVC C01 不自动形成 UAV-entry 结论。本轮未核实到五份满足这三个条件的独立 entry，故不能据“多个目录有 UAV”宣布五槽目标已结束。

## 七个 PARKED 方向

这些目录没有 2026-09-04 以后的新科学提交，当前无运行或 Transport 生成。旧 DIRECTION 中残留的 ACTIVE 或下一步句子不能覆盖 Portfolio 停放状态。各行都没有匹配的 tuned headroom；这不是停放理由本身。

| 方向 / Priority | 最后可用证据与仍有意义的问题 |
| --- | --- |
| [APFI / LOW](../candidates/active_post_churn_population_flow_identification/DIRECTION.md) | 旧 CCF 可化为两事件 XOR/DFA，新 censored-flow 构造未接受。若重入，应比较明确低阶/有限资源的同信息控制器是否用到会改变 native 行动的流历史；不能要求有限时域对象“不能由任何 DFA 表示”。 |
| [EC4G / LOW](../candidates/ec4g_r1/EC4G_CURRENT_HOST_HEADROOM_A_RECON_INTAKE_20260904.md) | 旧 content/physical/selectivity 没有建立独立效用；B1 聚合不能当有效基线，A1 明确上参考和 tuned generic 均缺。结构差不等于控制收益；无具体新对象。 |
| [EOCIV / MEDIUM](../candidates/eociv_lite/DIRECTION.md) | B10 固定 score exposure 放大相对 J，却使整体 receiver CORRECT/绝对 native 差更负；A1 有正初始化证据，不能隐藏 A0/global harm。receiver-addressed 包已停；旧文 ACTIVE 句是历史状态。 |
| [EGRCR / MEDIUM](../candidates/expressibility_gated_renewal_credit_relay/DIRECTION.md#current-direction-disposition--2026-09-04) | 当前 factorization PARK。平滑温度一 utility +.0120448，但 sampled utility 相同、两 critic 都 8/8，generic Q/gradient error 更好。保留正值，不把它当 association-credit 价值或重开旧 B02。 |
| [ORBIT / LOW](../candidates/orbit_shadow_read/DIRECTION.md) | owner-by-role action-kernel sensitivity 已有，独立 return population、learner 比较及超出 currentness provenance 的效用未建立。若重入需具体 return-bearing 问题，不能把可达动作当价值。 |
| [RECCT / MEDIUM](../candidates/recct_lite/RECCT_HEADROOM_CENSUS_A01_INTAKE_20260904.md) | 当前 one-port target separation 八对全零；旧 B1 INVALID，不供机制负值或 baseline。未来需 consequence-distinct target 的同信息学习比较，headroom 缺失不应变成先做 exact upper 的要求。 |
| [SCOPE-1s / LOW](../candidates/scope_1s/SCOPE1S_GUIDANCE_A1_HEADROOM_CENSUS_INTAKE_20260904.md) | synthetic correct-Q16 上参考 60、current-only 32；信息不同，差 28 不是 tuned headroom。唯一被测行动未绑定实际 roster/时钟/信用/partner 非平稳性，尚无真实变量轴学习对象。 |

## 科学建议与下一次投资问题

**优先把现有结果接成可用选择，避免再增加准备负担。** ACVC 能保留固定 F 的限定执行收益，而不声称 learned selector 被挽救；FOLR 用原配对检验可选 gate 是否继续值得开发；VNFC 将有限工程证据用于保护真实 primary；RCLE 保留 nearest 强参照。上述四条独立推进，不等待本次 Portfolio 材料或彼此收尾。

剩余槽位的选择应是一个新的、具体的 Portfolio 投资问题，覆盖仍 ACTIVE 的候选而不把“上轮 no successor”写成永久禁入。可比较三类真实选择：①健康已有路径上的小 B，例如 MGTAP 一个独立 COND/DENSE 配对；②已存在明确未答对照的有限执行路径恢复，例如 CBSC 的完整 RAW/STRUCT native 比较；③保持当前投入、等待自然到达的新方向判断。VSP03 的低 native 成本是重要反方，但其两轮窄暂停和低于 MEI 的多数终点也必须保留，不能为凑槽再循环同一问题。FSD、UCOPE、DISH、SCDMP 或其他方向提出具体不同问题也可比较，不能因本表无现成卡而永久排除。

我的建议是将**CBSC 的有限可信路径与完整比较**作为下一次新增投入首先审议的候选，MGTAP 小额独立配对作为健康执行路径上的实质备选，保持投入为强保守选项。理由是 CBSC 当前机会信用包尚缺首个完整 RAW/STRUCT 对照；它比重复已观测的 source-only 事实有更直接的决策价值。反方是旧两个零差、RAW 已输 REQUEST_ONLY、当前工程完成成本未知，所以不预先承诺生产修复成功，不给无限调试，也不在本报告分配训练款。选择与预算必须由 Portfolio Pro 决定；涉及改变已暂停家族的范围仍由适用方向节点处理。

成本建议从已知乘数出发。MGTAP 原配对为 2 arms ×512 episodes ×256 ticks，加每臂 32×256 final ticks，共 278,528 ticks、2,048 Adam 调用；8213 complete native 为 358.11 秒。VNFC 新已选配对为 4,544 complete episodes、1,090,560 native ticks、4,096 optimizer calls，含 BCRH 原算法工作；不能把必要参考当额外验证删掉。CBSC 既有机会信用定义为每臂 48 rollouts/768 Adam，运行路径调整和 complete cost 未知，不能从 RAW 的 53.46 秒推出两个有效臂一定便宜。任何新选择都先问下一观察是否值得，再决定最小 B/有限测量；不做全 N×k×seed、逐前缀枚举、best-of-many 搜索或全历史 replay 的默认前置。

## 本次使用规范与基础知识得出的限制

已使用 [evidence spec §§7–8.1、11.4、11.7–11.10](../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)、[FOUNDATIONS §§3–6](../../rl-marl-foundations-20260907/FOUNDATIONS.md) 和 [实证专题](../../rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md)。具体假设是：保存的各方向 accepted intake 准确描述其绑定执行，独立单位按原卡的完整 fit/pair 定义；本轮只复核决策含义与现状，不声称再现其原始计算。条件 episode SE、checkpoint 和 Pro 解释均不增加 independent fit。完整方法优劣与组件因果分开；一个结构可表达、参数移动或时钟改变，不保证 finite learner 获益。

300 秒问题首先是成本口径和工程比例问题：308.8422538 = 274.81 Git 父事务 +34.0322538 其他命令，client timeout 与存活父事务不能重复累计。这是部分 command-wall 之和，不是 CPU 或 study elapsed。owner 的参考值澄清适用于此次 FOLR 恢复；不暗改其他 frozen cap。科学复杂度的正确问题是“该工作是否为下一决策所需”，而不是“能否把任意准备计数硬塞进 300”。

本次无新 learner、环境轨迹、optimizer、评估或实验；owner prediction 为 not taken。主控 owner-console 当前无未处理 review。所有建议都保留负结果、资源未知和最小处置边界，不以工具缺失、故障或材料复杂度制造科学极性。
