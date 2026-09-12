# HMASD 独立 Oracle 建议 — 2026-09-11

作者：按 owner 要求启动的 Astra / max 独立 Oracle。

**最值得做的是完成正在推进的两项清楚问题，并提高下一轮问题的比较质量。** ACVC 已有较一致的固定执行方案收益，正在完成一个有明确限制的确认对象；FOLR 的学习遗忘门出现幅度相近、方向相反的两个结果，已获资助的一次原样新配对有实际信息价值。多数其他方向的问题，是专用结构能否在有限学习中胜过现成强对照，以及已有收益是否触及所声称的机制。新增名称、形式化区分、参数移动或更多条件评估，都不能替代这个答案。

本文是建议，不是 Portfolio 决定、方向处置、实验卡或新预算。下文把“现有授权应执行什么”和“以后值得审议什么”分开。建议顺序不修改仓库 Priority、recast、生命周期或冻结对象；不启动实验、Pro 问题或实现。

## 1. 阅读边界与当前快照

科学证据主快照固定为 **f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7**。引用默认指向该提交的具体文件；文件中的旧日期、旧权限和旧运行状态保留其历史含义。当前生命周期以 Portfolio 为准，不能从旧 DIRECTION/intake 的 ACTIVE 或 PARK 字样反推。

只追加以下明确的后续事实：

| 补充来源 | 本文采用的事实 |
| --- | --- |
| [当前执行表][live]，86e5c9aed8c8af8434b0a07b378989bab93f12b9 | 22 个登记方向中 15 ACTIVE、7 PARKED；两条实际推进链是 ACVC、FOLR，三个工作集空位。FOLR 原 DM 已确认继续，尚无该新配对的 native launch 事实。 |
| [ACVC 组件 intake][acvc-unit1]，03053c42f2e190767bf14a1f2cf064f7b079b5fb；Root 本次回执 | unit 1 已完整接受；unit 2 于 2026-09-12 04:52:15Z 接受，04:52:30Z 确认 Monitor adoption，handle 为 acvc-fresh-dense-c01-11477-3fd9062d5。后两项是 Root 回执事实，Oracle 未另行查询执行节点。 |
| [FOLR 资金决定/intake][folr-funding-intake]，主线出版 5f0cbde26517d415eed810f8caf329e9e1c804e0 | F+U 已接受并映射到原 DM；只资助一个新 FOLR 原样配对，FSD 不增加问题或实验。完整 Pro 源为 f4bbe6cae2d351b4c80c5e0d9d66690d337749ce。 |
| Root 本次状态纠正回执 | MGTAP 旧 BLOCKED 原文保留，但登记状态已为 DELIVERY_RECONCILED、observation_pending=false；不能据旧字段制造待回收 Pro 任务。RCLE 则仍是有明确 Transport 负责的同请求恢复。 |

这是有版本的审阅，不是之后运行状态的实时看板。unit 1、unit 2 的完成或接受都不等于 ACVC 全部 C01 的结果。以下判断不使用尚未读到的后续结果。[当前工作集][live]

已读当前 evidence spec 全文，工程/运行规范的适用约束，FOUNDATIONS 及四篇主题笔记、知识阅读索引，RESEARCH_MAP、Portfolio/追踪与近期决定；覆盖全部 22 个 DIRECTION 的当前问题及相关最新证据。ACVC 五-fit Innovator、FOLR post-B02 Convergence 与 F+U 完整答复作了深入直接核对；其他方向的处置结合当前 DIRECTION、最新相关卡/result/intake 及其完整答复引用核对。没有递归审计所有历史档案，也没有重新运行或独立重算各方向的原始实验。[规范][spec] [基础知识][foundations] [研究导航][research-map]

## 2. 核心判断

### 2.1 已有真实进展，但“方案有效”和“专用机制有效”之间仍有很大距离

近期工作已不只停在静态接口、可表示性或代理指标：ACVC、FOLR、FSD、RCLE、MGTAP、UCOPE 等均已有实际 learner、非零更新和原生回报。应承认这个进展，也应保留负结果。最容易误读的是把以下不同层次接起来：

| 已观察到什么 | 目前能支持什么 | 仍不能由此推出什么 |
| --- | --- | --- |
| ACVC 固定 F 在三个新学得 DENSE 基础上胜过 C 和 dwell | 固定完整执行方案在这几次实例上有收益；值得完成已冻结 C01 | 学习到的选择器有效、纯 retrace 因果、等剂量比较、一般历史必要性 |
| RCLE W100 相比 W1 有大幅服务改善 | 整套有限学习法确实学到了有用行为 | 已胜过合法 nearest 参考，或改进来自单独一条 actor 梯度 |
| FSD 改变续期/批量后曾出现较大收益 | 完整学习方案在某些新配对上更好 | 单独中断、单独 batch、端点评估中的额外 renewal 是原因 |
| EGRCR 温度一的平滑效用更高 | 指定评估变换下的该项观察为正 | critic 更准确、信用估计更有效或贪心控制更好 |
| ORBIT owner/role 交互到达动作概率 | 指定接口具有行动可达性 | 学得语义、任务价值、泛化或部署收益 |

基础知识对此的约束很直接：同信息不等于同有限优化结果；可表示不等于可学好；参数不变的 recurrent policy 仍会随历史适应；全局 critic 不自动赋予 actor 全局信息；完整训练方案之间的差异不是其中一个组件的因果效应。[RL][rl] [MARL][marl] [经验方法][empirical]

**建议：以后每个对外结论先说清楚正在主张完整方案、组件因果、信息价值还是跨任务迁移。** 这可以直接改善现有 intake 的表达，不要求每个 B 加做一套机制消融。选择方案本身就是合法研究产出；只有要作更强主张时，才为那个具体主张购买区分证据。

### 2.2 现成强对照，比“专用结构是否动了”更有信息价值

FOLR 的 RETAIN 自带 GRU 适应；UCOPE 的固定 F、MGTAP 的 intact DENSE、VSP-C1 的完整普通 MLP、RCLE 的 nearest，以及 FSD 的 authentic D0，都是必须认真对待的现成选择。比较对象不需要先被证明最优，才有价值；反过来，胜过弱控制也不能说明有部署或下一阶段优势。

当前最突出的例子是 RCLE：W100/W1 三个完整训练根的服务差分别约 +0.3791、+0.3678、+0.3033，属于真实学习收益；但三次仍输给 attained nearest，第三根的八个 fragmentation 单元全部更差。后来的 .99 prior/1000-update 方案仍在全部八个 service 单元输 nearest，且相对自身初始化的聚合增益为 −0.0001078。这支持改变“下一步想区分什么”的讨论，不支持继续把 W1 当作充分的实用性参照。[RCLE S23][rcle-s23] [RCLE B06][rcle-b06]

**建议：未来比较保留目前最有竞争力的合法参照，并把初始策略收益与训练新增收益分开。** 这是下一问题的设计建议，不把初始化面板、调参扫描或额外 baseline 变成每个已冻结 B 的新条件。当前 15 ACTIVE 的匹配 tuned headroom 仍缺失；缺失不等于零，也不阻止合法 B。Headroom 是“明确上参考减去调优后的同信息基线”，不是任意规则、旧对照、参数移动上界或跨宿主分数差。[当前 Portfolio][live] [规范 §§11.4、11.7][spec]

### 2.3 证据稀疏时，既不能宣布稳定胜利，也不能把暂停解释成科学失败

FOLR learned gate−RETAIN 的 +1.763359375 与 −1.76953125 幅度相近。FSD I1280/D0 的两个正值与一个 −0.0124304 共存，最后一个均值仅略过 −0.01，条件 episode SE 为 0.0192675。SCDMP 两个正值都小于自己的 0.01；VSP03 四条分别记录的 512 端点为正，但最新的 128→512 变化为负。这些都能改变边际投入判断，却不提供稳定总体排序。[FOLR][folr-dir] [FSD 最新 intake][fsd-intake] [SCDMP][scdmp-intake] [VSP03 答复][vsp03-pro]

独立单位是一个完整训练实例，或有共同初始化/训练随机性设计的一个配对。一个 fit 的 32、64、128 或 1024 个 evaluation worlds，不是同样数量的独立训练样本；两个 checkpoint、多个指标、恢复后的同一 root、更多 Pro 解释也不增加它。FOLR 相同评价标签下，动作会改变交通及 RNG 消耗，不能称为完全相同的后续世界。[经验方法][empirical] [FOLR 完整决定][folr-pro]

ACVC C01 则是另一种明确约定：五个完整 fit-panel 均值，两个主要比较，在预设 iid-normal 模型下使用 t(0.9875,4) 构造同时区间，两个下界都严格大于 0.01 才共同通过。五个 fit 不是普遍充分的统计样本数；模型校准未被证明。应完整保留这个限定，同时执行已接受协议，不临时换 bootstrap、增样本、做正态性资格测试或因中途负值停下。[ACVC C01 卡 §§3–5][acvc-card] [ACVC Innovator][acvc-pro]

### 2.4 原生 UAV 分数和目标 HMASD 能力之间，需要明确的连接

许多近期方向采用固定成员的五-UAV、50-user、H256 宿主；FSD 当前 I1280/D0 用的是六-UAV、50-user、H500。二者不能合并。RCLE、FOLR、VSP03 等又有各自的流、交通或共享服务宿主。即便目录写着 UAV，某一固定 N、固定信息和行动 law 的 B 仍不自动成为正式 UAV validation，更不自动证明变 N、异步时间或接替迁移。

本地阅读的 HMASD 方法段描述固定每 k 步的高层协调及逐 agent 的技能选择；ACAC 则将各 agent 的异步历史表征用于 centralized critic。它们提示要区分四件事：动作何时能更新、谁拥有历史/状态、训练信用如何跨时间计量、评价时是否还在参数学习。这些是设计线索，不是 HMASD 当前实现已达到某个性能或支持任意 N/k 的外部证据。[层次/异步基础][hierarchy] [ACAC 原论文][acac-paper]

**建议：未来选择下一对象时，只指出它要新增或验证哪一条目标能力，并选能触及该能力的一个最小原生问题。** 不要求每项 B 同时做 N 扫描、持续时间扫描、所有机制消融和跨宿主迁移。若只是固定执行方案收益，就明确保留该用途；若要研究成员替换或异步控制，就不能让固定成员或不触发事件的评估替它回答。

### 2.5 现在的主要管理风险，是科学状态、执行状态和历史措辞被混在一起

当前不是“15 ACTIVE 就应有 15 个运行”，也不是“三个空位就有三份待花预算”。五条推进链是目标工作集；空位可见、原 DM 负责、下一合法动作可追溯，就没有必要为凑满数字创建工作。对确有科学价值的未选备选，下一次适当 Portfolio 问题应该比较它们，而不是从“上次分配结束”推导永久无资格。

已有修正说明这个差别是现实问题：旧 vacancy 问题明确排除了已结束边界，得到零新增；随后 broader open-direction 问题重新比较具体新投入，选出了真实 B。前一回答没有错，回答的范围更窄。今后应保留这个区别，避免让“固定排除条件下没有备选”被转述成“整个研究集没有值得问的问题”。[旧 vacancy 问题/intake][vacancy] [broader program][open-program]

## 3. 全部方向：证据、区分价值与实际下一步

数值只在各自宿主、定义、预算和 MEI 下解释。表中“以后可区分”均是未分配的研究可能性，除非“当前动作”明确写为已授权。表内的 ACTIVE/PARKED 是主快照的 Portfolio 生命周期；窄家族暂停另列。

### 3.1 当前 ACTIVE 的 15 个方向

| 方向与精确问题 | 最强证据与主要反证 | 以后有信息价值的区分；与其他方向的区别 | 当前就绪与授权动作 |
| --- | --- | --- | --- |
| **[ACVC][acvc-dir] / MEDIUM，recasts 2**：固定 F 执行 law 在 fresh DENSE 上的完整收益 | 三个 development fit 的 F−C 为 +0.12293/+0.09153/+0.14143，F−dwell 为 +0.08772/+0.06390/+0.09441；dwell 自身有益，也有 F 输 dwell 的 worlds。旧 learned T/G 输固定 F，不能借固定 F 的结果挽救。 | 现 C01 增加预先固定的新训练实例，检验限定总体的两个期望收益。它改变执行选择，不等于 FOLR 的记忆 gate 或价值网络结构。 | **执行中。** unit 1 已接受、unit 2 已接受并 adopted；完成固定五单元及两主要量，沿原卡处理真正的 integrity/resource/cap 限制。无中途 efficacy gate、替换或第六 fit。 |
| **[FOLR][folr-dir] / MEDIUM**：TrafficJunction 中 public lifecycle 触发的 129 系数 learned retention gate，相比 RETAIN | 两个新配对 +1.76336/−1.76953；每臂 5000 train、128 final、4969 RMSprop。RETAIN 已可 recurrent 适应；固定 HALF、完全 EVENT 的旧证据是其他方案。 | 一个原样新配对增加一条真实训练历史。仍区分不了额外容量、0.99 初始化和 co-adaptation 的单独贡献。这里是实体存续与记忆保留，不是 DISH 接收预测包或 VSP02 optimizer reset。 | **已获资助，原 DM 已开始绑定/实施。** 新上限 1350/arm、2700 native、300 support、3000 complete；快照未见新 native launch。完成即结束本份 grant，不自动有第四配对。 |
| **[FSD][fsd-dir] / HIGH**：I1280 续期/批量方案对 authentic D0 | 分别 +0.05698、+0.20629、−0.01243；旧 batch128 的两个负值独立保留。最新 16/16 episode 符号、I 耗时为 D0 的 2.17 倍；最终两臂都没有额外 individual gap 事件。 | 若再选问题，应说明是方案复现、训练信用/分组，还是实际 online renewal；现终点没有直接触发额外 renewal，不能隔离其作用。与 UCOPE 的 duration law/credit 不同。 | 最新配对及本次 cleanup 完成。F+U 明确**不增加 FSD 问题或运行**；没有第四配对、C 晋级或 successor。[最新 intake][fsd-intake] |
| **[RCLE][rcle-dir] / MEDIUM**：合法流/roster 信息下，学习能否改善服务并胜过 attained nearest | W100/W1 三根改善大，但 nearest 始终更好；S23 fragmentation 八单元全差。B06 .99 prior 的 reference contrast −0.005758，自初始化增益 −0.000108，全部八 reference 单元输。非零梯度/参数移动不等于新策略价值。 | 待原 Convergence 决定的 channel normalization 候选可能区分有限梯度分配问题；先验收益与后续学习收益必须分开。不是“再提高概率必然更好”。[B06][rcle-b06] | **Transport 负责同请求恢复。** 请求 2026-09-11-rcle-channel-normalization-convergence-01 尚未接受，两次无效点击不等于两次 Pro 生成。方法未选择，无新数值授权，不计推进槽。 |
| **[MGTAP][mgtap-dir] / MEDIUM**：context-weighted 用户 pooling 对 intact DENSE | COND 两配对 +0.005761/−0.022470；第二次 27/32 worlds 负。旧 REL 的损失是不同已暂停方案。 | 可以增加 COND 的实例变异信息，或区分一种具体表达/优化假设；不能因 relational 名字认定通用 DENSE 忽略几何。 | 当前配对完成，**无第三配对、准备或咨询**。旧 Pro delivery 已 reconcile；这不是遗失的研究任务。保留 DENSE 及所有证据。[8213 intake][mgtap-intake] |
| **[UCOPE][ucope-dir] / HIGH**：learned continue/end 信用方案 L 对固定 F | 8801 L−F = −0.024106，40/64 worlds 负；完整 native 1384.14 s。旧 learned-short T 也有对 F 的损失；固定短 F 对 G 的两次正值保留。 | 下一问题要说明为什么学习 duration/credit 能改善当前固定 F，而非只胜过弱 G 或 hover。仅改变首动作不可受 duration 影响的数学信用分解，不保证 clipped learner 获益。 | L/F allocation 完成，**无 successor**；未来新信用/学习设计须经适当方向/投资选择。[最新 intake][ucope-intake] |
| **[SCDMP][scdmp-dir] / HIGH，recasts 2**：固定开场 t1–3→t4 双端 residual-MC 对 intact MLP-MC | 两配对 +0.006737/+0.003658，均小于 .01；B02 MLP−H 为 −0.000660。作用非零，正值仍是真证据，但不证明 semigroup 必要性或可靠收益。 | 具体信用/损失假设或有决策用途的新复现问题仍可能有价值；与 FSD/UCOPE 改 actor 时钟不同，当前作用在 critic/训练链。 | 完整 Pro 已**窄 PARK 当前开场 residual-MC 包**，无第三配对、loss 修改或诊断；不是整个方向失败。[intake][scdmp-intake] |
| **[VSP-C1][vspc1-dir] / MEDIUM**：完整普通 value body 加 remaining-hold gate | B13 GATED−MLP = −0.032069，25/32 worlds 负；MLP−H = +0.035562。旧 512 gains 保留，768 后普通网络追上/超过；hold 非零训练行约 1.13%，添加 640 参数非等容量。 | 只有具体 hold-value 或有限学习问题才值得重新比；不能从 early checkpoint gain 推断 final gain，也不能把少量事件行自动认定为优化故障。 | P81 完整决定结束这一个 additive 包，**无 successor**；普通完整 body 是局部支持的选择。[P81 intake][vspc1-intake] |
| **[VNFC][vnfc-dir] / HIGH，recasts 2**：INTERVAL/TERMINAL 的原生服务时间信用 | 早期 MAPR/DIRECT 两臂都学会部分恢复，机制差小；新 pair 缺完整 primary，旧 exit139 和 480 updates 是工程/暴露事实。E01 exact projection 超过原 cap 不是负 headroom。 | 同含义可用执行路径可让首个完整配对回答信用问题；需要解决威胁该训练/primary 的具体依赖，或说明可信独立路径。 | source-only 调查没有 attributable repair。原 **900=600 native/reference+300 support** 条件 allocation 仍 queued/unready；无额外 repair 或 retry 预算。 |
| **[CBSC][cbsc-dir] / HIGH**：语义 currentness 表达/信用能否胜过合法普通历史 | RAW/STRUCT 的旧完整短比较同选 REFRESH；新 local-credit RAW 12.0375，低于 REQUEST_ONLY 12.375。STRUCT 对应结果缺失，不能补成一个负配对。 | 有效的完整共同学习比较，才能区分结构收益与请求规则/信用问题；与 FOLR 的 retention intervention 不同。 | P47 六处替换的 source/AST 路径已重建；旧拒绝 payload 与具体 native 原因未定位，**retained52 未跑、未分配**。不得把 static success 当 production repair。[技术 intake][cbsc-tech] |
| **[FRRIE][frrie-dir] / HIGH**：相同 chart 下有限资源 tight/wide 归纳约束 | R06 的 N15 gain +0.005548 超过 .005，R07 −0.001948；既有路径不支持 chart 必要性，R08 是同 fit 分析。后续 native crash 不具有算法负极性。 | 新的、可归因的短边界检查或可信独立路径可能恢复信息获取；是否改变科学问题仍需本方向/Portfolio 选择。 | P59/P63 六文件九帧 source-only 观察成功，但 native corrupting writer 未知；**无 production patch 或新数值 allowance**。[技术 intake][frrie-tech] |
| **[VSP03][vsp03-dir] / LOW，recasts 1**：公开固定 N2 共享槽上 ordinary G 的 fixed512 规则替代 | B06 三 fit D512 +0.025996/+0.014507/+0.009688；B07 +0.011567，Q512−128 = −0.001606。全部四个端点分别为正，不合成新 primary；旧 independent128 负/小正及 stochastic 历史保留。 | 一个新相同 fit 仍可能提供新反例或更大收益，且 native 曾仅 8.38–8.93 s。也可能继续得到小正、并不改变选择。它是公开调度学习，未证明 MARL 专属原因。 | 原节点完整复审仍保留 **continuous512 窄暂停，无追加、条件释放或新预算**。这是值得保留反方的边际选择，不是方向无价值。[完整答复][vsp03-pro] |
| **[DISH][dish-dir] / MEDIUM**：接收 forecast/control 包后 HALF_RETAIN 对 REPLACE | B08 service 434.5 vs 441，差 −6.5，在 ±24 内；四条件 −15/0/−8/−3。HALF 能耗较低但服务也较少，并多四个 invalid commits。普通 CAS 全零，source/COPY/SHADOW 效应未估计。 | 若再问，应针对真实 receipt→控制的具体选择；18 字段预测包不等于 incumbent GRU 状态传递，源价值不能由 bridge 比较代答。 | Pro 窄 PARK tested arrival-bridge retention family、保留 REPLACE，**无 successor**。[intake][dish-intake] |
| **[CRTO][crto-dir] / MEDIUM**：已选 panel 上 residual alignment 是否改变 option-review 原生动作 | B08 RAW/TRUE/DERANGED 在 33、258 两端点选择同一 16 动作向量；RAW 的 REPLAN exact 5/8 未达旧 6/8 qualifier，保留零 contrast 诊断。记录中的最大可改善 regret 0.002129，小于原 .0025 margin。 | 同一固定参照/panel 不可能达到该原 margin；若问新问题，须明确变的是 population、暴露还是有意义效应，不能移动旧门槛或筛暴露错误。此廉价界限比继续穷举更有用。 | 完整 Pro 保留所选 panel 家族窄 PARK，**无 successor**；不是整个 residual 研究的否定。[P72 intake][crto-intake] |
| **[VSP02][vsp02-dir] / LOW，recasts 1**：固定成员、teammate 脚本切换后 Adam RESET/CARRY | 两个独立 learned prefix 的完整适应窗口差 +0.018555/−0.008789，均远小于 .5；符号不同，不能推等价。无 join/leave/rejoin 或 partner co-adaptation。 | 若有真实的 optimizer-state 选择需要，才值得明确新的 bounded comparison；单智能体面对变化环境的 warm-start 也是强解释。 | Pro 结束此 host/learner/P4096/Q1024 的 instantiated family 及原样 seed 扩展；**无第三 prefix 或 successor**，CARRY 保持普通默认。[intake][vsp02-intake] |

### 3.2 当前 PARKED 的 7 个方向

| 方向 | 已有证据与不能跨越的界限 | 若以后重新投资，最有信息价值的区分 | 当前动作 |
| --- | --- | --- | --- |
| **[EGRCR][egrcr-dir] / MEDIUM** | FRCS 中 generic 的 Q/gradient error 更小；factor 的 temperature-one expected utility 高 +0.012045，但 greedy 8/8 均 competent、sampled utility 都为 .484375。32 参数相同不代表算术工作相同。 | 明确是估计效率还是尺度/校准问题；结果启发的 common-calibration 对象必须另立含义，不能修成旧结果的“成功”。 | 保留 PARK_CURRENT_FACTORIZATION 及 mixed 结果；无 B02。[intake][egrcr-intake] |
| **[EOCIV-lite][eociv-dir] / MEDIUM** | 接收端/来源端的相对 J 改善可与更差绝对 native ΔR 并存；A1 没有 matched upper。0.00681469 是参数位移界，不是 return headroom。 | 必须保留 unchanged semantic baseline，让相对提升不能靠更伤害另一臂产生；未来同信息实用对照仍可合法研究。 | Portfolio PARKED；旧 9 月 4 日 intake 的 ACTIVE 是历史。无新 learner/upper census。[A1 intake][eociv-intake] |
| **[RECCT-lite][recct-dir] / MEDIUM** | source→receiver pointer 暴露存在，但 one-port 八对 LR/RL 的原生差全零；旧 B1 INVALID，不能借其回报填 baseline。 | 一个确实具有不同原生后果的接收目标比较，能分开“地址变化”与“价值变化”；无需先证明所有可能 host 的性质。 | PARKED，无 successor。Headroom 两项均缺，不等于零。[A1 intake][recct-intake] |
| **[Scope-1s][scope-dir] / LOW** | synthetic Q16 上 upper 60、current-only 32，但信息不同；没有 same-information tuned learner。一个冻结 actor 做唯一被评价动作，N3 标签未建立 binding MARL 结构。 | 若未来有明确用途，检验同样可见 Q16 的普通 controller/learner；别用信息集分离代替算法优势。 | PARKED，保留形式结果；无 baseline 建造或生产认证任务。[A1 intake][scope-intake] |
| **[EC4G][ec4g-dir] / LOW** | A5 行为 discordance 1/4 没有 native value；B1 在自身 activity aggregation 边界不完整/无效，raw 负差不是算法证据。当前是 single-leave receipt 信息流。 | 一个有效同信息通用 learner 的原生比较，可能说明剩余任务难在哪里；别为一个无 baseline 的 headroom 数字先造昂贵 upper。 | PARKED，无修复/重跑授权；headroom 未识别。[A1 intake][ec4g-intake] |
| **[ORBIT][orbit-dir] / LOW** | verified owner-binding 的 15 route calls 建立接口到 kernel；environment、learner、return 均为零。旧 eight-cell 的 owner-agnostic payload null 能重现结果。 | 若某接收对象确实需要 owner 信息，直接研究它改变什么原生后果；重复接口审计不会产生 learned value。 | PARKED；现有 code/science asset 可供明确接收对象引用，不因此恢复独立链。[代码—科学索引][orbit-index] |
| **[APFI][apfi-dir] / LOW** | 已知 witness 可化成简单 XOR/DFA；censored-flow-order 仍为未接受定义。DIRECTION 的“non-XOR/non-DFA”措辞需要有限资源解释。 | 在明确 history length、状态/学习预算和低阶 null 下构造后果不同的问题；先区分特定小型 null 的局限与抽象可表示性。 | PARKED，无 executable object。下面第 5.2 节只建议适当原节点澄清，未改其现有边界。 |

### 3.3 可以共享资产，但这些问题现在不应因关键词相同而合并

| 可交流/复用的主题 | 仍然不同的科学对象 |
| --- | --- |
| FOLR、DISH、VSP02、CBSC 的 event/history 实现经验 | 存续实体的隐藏状态保留；接收预测包后的控制；optimizer 状态重置；语义 currentness。状态所有者、处理时刻、学习对象和主要量都不同。 |
| FSD、UCOPE、VSP03、CRTO 的时间/机会建模 | joint renewal 与 batch；learned duration/credit；公开共享槽提交；option review 的 residual alignment。不能仅因都出现 clock/hold 就融合。 |
| SCDMP、VSP-C1、EGRCR 的 critic/信用经验 | 双端 residual 正则；remaining-hold 特征/门；factorized 精确信用估计。有限优化、校准与信息假设不同。 |
| 同一 native UAV 家族里的普通 actor/critic、日志与评价工具 | 先核对实际宿主、N、H、信息、动作 law、训练/评价预算和 source bytes。FSD 六-UAV/H500 不可直接复用五-UAV/H256 的效果或 headroom。即使可复用代码，也不共享 RNG、输出或冻结 primary。 |

现行机制“有共同资产”不推出“应融合方向”。只有 question、comparator、estimand 和下一对象实质相同，才值得正式提出 fusion；本次没有提出具体融合。[AGENTS §2][agents]

## 4. 优先建议：哪些现在做，哪些以后审议

### 4.1 当前授权的优先执行

1. **让 ACVC 原 DM 完成固定 C01。** 当前最清楚的信息增量来自剩余预选 fit 及完整两主要量。source 为 3fd9062d5456a6b61a132a16ebd33a7099810143；五单元合计 901120 ticks、5120 Adam、3520 episodes。每 native 单元 270 s、native sum 1350、support 1650、complete 3000，包含该账户既有支持工作。每个 intact 弱/负/极端结果都保留。完整有效对象无论正负都按原规则消费 C；primary 不完整不消费，也不自动给替换预算。[C01 卡][acvc-card]
2. **让 FOLR 原 DM 完成唯一新原样配对。** 原生主要量保持两臂各 128 次 final episode return 的均值差；MEI 1 的原分支不变。新增两 fits 只是一项独立配对，不是 256 个训练样本。205120 team ticks、9938 RMSprop 的完整链沿新 3000 s ceiling 执行，保留所有符号和 failure；结束本 grant 后不自动追加。[资金完整答复][folr-funding-pro]
3. **RCLE 的 Transport 恢复与两条实验链独立推进。** 恢复的是原请求，先协调是否实际被接受/形成完整回答，不能因两次 ineffective clicks 另造问题。原 Edge 不可用是具体工具状态，不是必须由那个 Codex task/浏览器“拥有”才可 Send 的权限条件；Transport 应按当前 owner 指令核对可访问登录 surface、准确会话/请求绑定和一-Send 状态。Oracle 没有查询浏览器，也不据此声称另一 surface 已就绪。[AGENTS 的 2026-09-11 Transport 指令][agents] [当前执行表][live]
4. **Root 按已有返回路径集成、接受并续接。** 有完整可行动返回就唤醒原 DM；原 DM 负责科学/技术 intake。已确认 Monitor goal adoption 才完成观察转交。全部当前就绪工作派出后按既有规则结束 Root turn，由 relay/Monitor/Transport 唤醒，继续滚动；不等待跨方向齐步完成。[当前执行表][live] [协作返回规则][sibling]

这些动作不需要 Oracle 新开审批或 Pro。它们也不能因为本文还在审阅、其他方向 cleanup 或 RCLE 外部依赖而等待。

### 4.2 下一次适当投资选择中，建议优先审议的三类问题

下列是**建议处理顺序，不是已作出的优先级或经费决定**。

| 建议 | 为什么可能改变决策 | 成本与不确定性 | 什么证据会削弱这条建议；权限 |
| --- | --- | --- | --- |
| **先把强现成参照带进问题，再追加专用结构。** 复用已接受的原生基线配置/证据；新方案优先回答相对该参照的具体有限学习问题。 | RCLE 的大 W100/W1 gain 与 nearest deficit、UCOPE/VSP-C1 的固定/普通网络优势表明，这比单看参数或代理指标有更大选择价值。MAPPO 文献也提示简单 PPO 基线的实现与配置值得认真对待；它不证明 MAPPO 在本仓库最优。[MAPPO][mappo-paper] | 复用记录便宜；新 tuning 或新 native comparison 需要另行预算，不能默认为免费公共工程。不同宿主的参照不能互换。 | 若现成参照被证明信息/动作不匹配，必须先修正对照解释；若新方案稳定改善既定实用比较，这一问题就已得到推进。现有冻结卡不变；新对象由 DM/方向/Portfolio 在各自范围决定。 |
| **对廉价而可能有用的普通学习收益，保留真实机会成本比较。** VSP03 是应保留的反方；不要把它仅因非专用机制或已暂停从未来材料中永久删除。 | 四条分别记录的正512 endpoint、8–9 s native cost，意味着“再获得一个真实训练实例”的代价可能很低；它也可能只是多一个不改选择的小正点。现 Pro 已看见这点仍略选 pause，应尊重这个 close call。 | 历史 native 便宜不等于整次研究便宜；B06 native sum 25.99 s 与 study elapsed 457.62 s 口径不同，全部 support 未聚合。不能拿未选的 30/30/60 提案当现成额度。[完整答复][vsp03-pro] | 若完整必要 support 明显昂贵，或新观察不能影响任何研究/使用选择，保持 pause 更合理；若有具体使用决定与可信低成本，新投资更值得重新权衡。改变现暂停回原方向节点，资金归 Portfolio；本文不请求循环同一咨询。 |
| **为目标任务建立一次清楚的“能力连接”，别一次性建全框架。** 后续候选只选择一个确实会绑定的变量：成员事件、控制时钟、接收状态，或训练信用。 | 可避免固定-N 的收益被写成 variable-N，或训练期 gap 被写成评价期 interruption。也能看清一个正 package 作为工程方案是否已经足够有用，而无需伪装成普适机制。 | 新宿主、adapter、算法/环境匹配或大 sweep 成本未知。先利用现有 source/卡的事实设计；不能自动要求每项都做完整 N×k×seed 矩阵。 | 若目标用途本来只需固定成员/时钟，跨 N/k 不是其必要目标；保留窄收益即可。若具体目标能力对回报不产生约束，换问题比继续加结构更合适。新的方向/目标/UAV 提案仍由适当节点选择。 |

ACVC 与 FOLR 的后续结果会自然改变下一次比较材料，但不需要等它们一起完成才处理其他独立就绪动作。当前 HIGH/MEDIUM/LOW、二次 recast 的 contention 次序继续有效；这里没有凭不同量纲的 Δ 值作统一排行榜。

## 5. 对规范、基础知识和实际流程的具体纠偏

### 5.1 把“收益、机制、曝光、成本”的名字写准确

- **自适应不等于评价期训练。** RETAIN 的 GRU 可以靠状态随历史变；称它“完全不适应”会削弱对照。FOLR、DISH 的 memory evolution 与 VSP02 的参数/optimizer 更新要分开。[RL][rl]
- **执行时钟不同，训练折扣也不能机械照抄。** 若原目标按 primitive ticks 折扣，跨时长 bootstrap 要与实际时长一致；按 decision discount 则是另一个声明的目标。不能因为某篇异步算法使用一种形式，就改变现冻结目标。ACAC 的 recurrent/attention 设计支持处理异步历史，不替当前策略类或 reward law 作决定。[层次基础][hierarchy] [ACAC][acac-paper]
- **critic baseline、信用系数和优化步长不等价。** 特定 baseline 的无偏条件不能扩展为任意 target/loss 改动都无偏。正比例奖励保持固定策略排序，并不保持有限优化轨迹；RCLE 的联合梯度归一化尤其不能被解释为“100 倍更新”或纯 actor 效应。[RL][rl] [RCLE S23][rcle-s23]
- **代理暴露不是功效。** 实际更新、gate 参数移动、actionability、loss 变化各有意义，但不能救一个相对强对照的负 native primary。相反，技术缺陷也不能被冒充负回报。
- **评估样本不能替代独立 fit。** 条件 episode SE 对固定策略有用；训练人群结论需要相应单位的设计与不确定性。不要用更多旧 checkpoint rollout 修补缺失的训练复现。现代 RL 评估文献强调区间及跨运行变异；这不使 IQM 或某个 seed 数成为本仓库的新强制项目。[经验方法][empirical] [评估论文][eval-paper]

现行 spec §11 已覆盖以上多数问题；主要需要在实际问题和文字中落实，不需要新设一般审计层。

### 5.2 APFI 的历史 non-DFA 表述应澄清

这是本次发现的一个具体基础概念问题。[APFI DIRECTION][apfi-dir] 将 re-entry 写为 non-XOR/non-DFA construction。**若事件字母表有限、时域有界，保存每个可能前缀就能构造一个有限状态机。** 因而“不能由任何 DFA 表示”的字面要求，不适合作为这类有限经验对象的一般要求。

有科学意义的目标可以是：某个明确低阶、少状态、有限样本/计算预算的对照无法有效利用 censored flow，而另一个同信息 learner 能改善原生后果。它研究的是具体资源限制下的表达/学习差异；不需要声称超越所有有限状态控制器。

这项建议不撤销 APFI 的当前 PARKED、未接受构造或旧 witness 反证。若以后重新投资，应由原方向节点澄清它实际排除的 null、资源和范围；如涉及现行规范变更，沿既有适当节点授权执行。不要把历史措辞扩张成所有 A/B 的形式证明门槛。[规范 §§11.4、11.8][spec]

### 5.3 工程修复应沿依赖前进，避免历史原因变成永久前置条件

CBSC、FRRIE、VNFC 的最新 source-only 结果确有收益：CBSC 可重建源编辑与 AST，FRRIE 可解析六文件九帧，VNFC 的 retained 类型/分配事实更具体。它们都没有定位可归因的 production defect，也没有产生完整新 primary。两边都要写清楚：

1. 不能以静态可读、命令成功或没有再次出现错误，宣布 crash 已修复。
2. 也不能把一个未定位历史拒绝或 crash，扩大为所有后来方法不可运行。现行 §11.8.7 明确允许可信的独立路径，不要求解开所有历史原因。

**建议的未来技术粒度**是一个与当前科学依赖直接相关的边界、一个可归因反例或明确独立的等义路径、一个很小的修复和相称验证。高风险的 reward、information、RNG、训练/primary 变更保留独立 review；生产代码没有可归因缺陷就不猜测修改。这里没有追加 VNFC repair、CBSC retained52 或 FRRIE P63 预算，更没有建议全局换解释器、全局升级依赖或重建诊断框架。[CBSC][cbsc-tech] [FRRIE][frrie-tech] [规范 §11.8.7][spec] [工程 §7][engineering]

### 5.4 完整成本要进入投资判断，但不可替代科学结果

跨方向只数 episodes、ticks 或参数个数会严重失真。例如 VSP03 一个 fit 的已给计数为 2949120 team ticks，native 约 8.9 s；FOLR 一个 pair 为 205120 ticks，历史 native 约 1703/1816 s，另含 66783360 replay GRU rows 与 33930120 learned gate forwards。两者宿主、模型、实现和单位不同，不能由 tick 比值预测成本，也不能直接比较效果。小门只有 129 个系数，不等于完整 recurrent replay 便宜。[VSP03 完整答复][vsp03-pro] [FOLR 资金答复][folr-funding-pro]

建议使用已有 runner 工作律和既有 support 记录，分别报告：

| 口径 | 应回答的问题 |
| --- | --- |
| 完整逻辑 invocation wall | 一次实际学习、必要评价/检查、发布与退出有没有在原 cap 内？跨脚本拆分不重置它。 |
| invocation wall 之和与 study elapsed | 总机器占用与关键路径分别多少？并发和等待使它们不相等。 |
| aggregate CPU / 资源 | 实际资源工作是多少？无法归属的字段保留 unknown。 |
| 必要 support 与咨询/作者努力 | 为获得一个有效结果付出了什么？已知部分计一次；Pro/思考 elapsed 不伪装为 native CPU，未知不记零。 |

先改善现有账户的未来记录，保留旧账的测量范围；不要为补漂亮 telemetry 重跑科学，也不要以未知 support 宣布已超 cap 或额外可花余额。若昂贵的是问题本身的 census、搜索或外层验证，先问更窄的真实学习问题能否作出同一决策，再考虑优化原来大程序。[运行规范][runtime] [规范 §11.9][spec]

### 5.5 防静默断链：只修真正缺失的接收/动作

| 情况 | 正确解释 | 相称动作 |
| --- | --- | --- |
| 完整结果已经返回，却没有明确接收 owner 或下一动作 | 真正可能的交接丢失 | Root 接受/路由给原 DM；在现有 tracking 加结果/commit、owner、下一动作及其 wake，一次闭合。 |
| RCLE 原请求未接受，Transport 负责恢复且具体 surface 失败已记录 | 有主的外部依赖；不是 orphaned decision | 保留同请求与失效尝试，协调真实 provider 状态；不重复 Send、不创建替代科学决定，不把它算推进槽。 |
| MGTAP 旧 BLOCKED 与后续完整决定/intake 并存 | 历史字段漂移；本次 Root 已 reconcile | 保留原记录、使用已协调当前状态；不唤醒已结束旧请求。 |
| FSD/MGTAP/UCOPE/VSP03 等 named allocation 完整结束、未选 successor | 合法边界；不是监控失联 | 保留结果与空位。需要新投资时提出具体备选，不自动重跑或偷换 family 状态。 |
| creator-owned scratch cleanup 被拒绝，但 primary 完整 | 有独立责任人的 housekeeping 限制 | 保留具体路径、拒绝及 owner；按已允许方法在可行时收尾，不让独立研究或有效结论等待它。 |

现有 relay、Monitor goal、Transport receipt、原 DM 和 Root tracking 已具备所需路径。**不建议新增常驻状态扫描器、重复 dashboard、跨方向总等待、另一个 coordinator 或全量历史 replay。** 一行当前状态应能回答“谁负责、什么证据、下一步是什么、何时由哪条返回唤醒”；旧表留作历史即可。[当前执行表][live] [协作返回规则][sibling]

## 6. 可执行的近期边界与停止清单

近期结果应是两份完整可读科学返回：ACVC 固定五-unit C01 的两个限定 primary，以及 FOLR 唯一新 pair 的 native reading、全部符号与成本限制；RCLE 则等待同请求的真实 Transport 恢复并由原 DM 完整 intake。任一独立方向达到可行动边界就处理它，不组成必须同步结束的批次。

已有完整证据足以现在停止以下做法；它们不是本报告新增的实验门槛：

- 不把结束的 allocation 余额、失败尝试或别人的 native 节省转成新预算。
- 不用挑出的早 checkpoint、条件 SE、旧 recovered root 或增加 rollout 数制造独立训练复现。
- 不把 small/WITHIN、短期无收益、技术 failure、missing headroom 或 narrow PARK 翻译成等价、全方向无效或永久无资格。
- 不为每个合法 B 先做 exact upper、全支持集搜索、完整因果证明、全历史故障定位或新的 Pro 资格审查。
- 不让同一证据上的反复咨询代替新观测，或只为维持“活跃”计数而继续咨询；需要时把具体边际选择一次说清楚。
- 不因当前 fit 看起来好就自动追加，也不因它看起来差就修改冻结终点、comparators、MEI 或 ACVC 五单元顺序。

如果只采纳一项研究设计建议，我建议：**下一次正式提出新投入时，写出“这个新观测将怎样改变对现成强方案的选择”，同时给出最强反方和完整成本的已知/未知部分。** 它允许普通 learner、负结果、廉价复现和新的机制问题公平竞争，也能防止形式证明、复杂工程和流程状态取代真正的信息增量。

## 7. 来源与审阅限制

规范与基础知识按当前约束读取，而非把历史 ALGORITHM_PRINCIPLES 或知识包的 SESSION_CHOICES 当通用新指令。所有方向结论均限于其卡和已接受记录；部分旧 intake 中“先有 headroom/upper”的下一步文字只描述旧对象，不在本报告中变成普通 B 的启动条件。

本地文献优先使用现有来源：查看本地文献能力/索引后，实际读取 InstSci 库 MARL-0449（ACAC）有关 per-agent history、attention critic、duration discount 的段落，以及 MARL-0553（HMASD）有关固定 k 协调、技能选择、低层 actor/critic 的方法段。My-lib 当前访问到的索引不提供可验证的相关真实 corpus 支撑；这限制本次检索覆盖，不等于文献不存在或方向新颖。没有安装、全库重建或迁移工具链。

外部核对只使用一手来源：ACAC 的正式会议页、MAPPO 原论文及 NeurIPS 的 RL 评估论文。文献用于约束方法解释，不提供本仓库未测的效能、因果、最优性或 UAV 迁移证据。未逐项复现代码/原始 run、审计全部历史 support 或给出美元成本；未访问实际浏览器、Monitor 或运行节点验证后续动态。关于科学结果的数值，依赖本文直接读取的已接受文件；这是一份独立综合评议，不是新实验。

[agents]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/AGENTS.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[sibling]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/project/SIBLING_COMMUNICATION.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[rl]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/rl-marl-foundations-20260907/topic-notes/01_RL.md
[marl]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md
[hierarchy]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[research-map]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/RESEARCH_MAP.md
[live]: https://github.com/CartmanFatass/My-paper-code/blob/86e5c9aed8c8af8434b0a07b378989bab93f12b9/docs/research/portfolio/PORTFOLIO.md
[vacancy]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/portfolio/decisions/2026-09-11-current-vacancies-refill.md
[open-program]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/portfolio/decisions/2026-09-11-open-directions-research-program.md
[acvc-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/acvc/DIRECTION.md
[acvc-card]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_SCIENCE_CARD_20260911.md
[acvc-pro]: https://github.com/CartmanFatass/My-paper-code/blob/b1709632efa060aa7e71ad377bd0559154289f12/docs/research/candidates/acvc/pro_packets/20260911_five_fit_prefreeze_innovator/archive/RESPONSE.md
[acvc-unit1]: https://github.com/CartmanFatass/My-paper-code/blob/03053c42f2e190767bf14a1f2cf064f7b079b5fb/docs/research/candidates/acvc/ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md
[folr-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vap_folr_core/DIRECTION.md
[folr-pro]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vap_folr_core/pro_packets/20260911_learned_retention_post_b02_convergence/archive/RESPONSE.md
[folr-funding-pro]: https://github.com/CartmanFatass/My-paper-code/blob/f4bbe6cae2d351b4c80c5e0d9d66690d337749ce/docs/research/portfolio/pro_packets/20260911_folr_unchanged_pair_funding/archive/RESPONSE.md
[folr-funding-intake]: https://github.com/CartmanFatass/My-paper-code/blob/5f0cbde26517d415eed810f8caf329e9e1c804e0/docs/research/portfolio/decisions/2026-09-11-folr-unchanged-pair-funding.md
[fsd-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/flexible_skill_duration/DIRECTION.md
[fsd-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/flexible_skill_duration/FSD_UAV_RENEWAL_BATCH_B02_771103_INTAKE_20260911.md
[rcle-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/roster_consistent_latent_exploration/DIRECTION.md
[rcle-s23]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B03_FRESH1000_S23_RESULT_INTAKE_20260910.md
[rcle-b06]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/roster_consistent_latent_exploration/RCLE_B06_NEAREST99_PRIOR1000_RESULT_INTAKE_20260911.md
[mgtap-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[mgtap-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8213_INTAKE_20260911.md
[ucope-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/ucope/DIRECTION.md
[ucope-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/ucope/UCOPE_UAV_CONTINUE_END_CREDIT_B01_8801_INTAKE_20260911.md
[scdmp-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/semigroup_consistent_duration_model_policy/DIRECTION.md
[scdmp-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/semigroup_consistent_duration_model_policy/pro_packets/20260910_post_b02_convergence/CONVERGENCE_INTAKE_20260910.md
[vspc1-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_c1/DIRECTION.md
[vspc1-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_P81_CONVERGENCE_INTAKE_20260909.md
[vnfc-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/variable_n_fleet_churn/DIRECTION.md
[cbsc-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md
[cbsc-tech]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/capability_bound_semantic_currentness/CBSC_P47_TECHNICAL_UNBLOCKING_INTAKE_20260911.md
[frrie-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md
[frrie-tech]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/finite_resource_relational_inductive_efficiency/NATIVE_CRASH_P63_STATIC_UNBLOCK_INTAKE_20260911.md
[vsp03-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_03/DIRECTION.md
[vsp03-pro]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_03/pro_packets/20260911_question_fallback/archive/RESPONSE.md
[dish-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[dish-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_B08_CONVERGENCE_INTAKE_20260910.md
[crto-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md
[crto-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/commitment_residual_triggered_options/CRTO_POST_B08_P72_CONVERGENCE_INTAKE_20260908.md
[vsp02-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_02/DIRECTION.md
[vsp02-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/vsp_02/VSP02_TEAMMATE_POLICY_CHANGE_POST_B01_CONVERGENCE_INTAKE_20260907.md
[egrcr-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/expressibility_gated_renewal_credit_relay/DIRECTION.md
[egrcr-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/expressibility_gated_renewal_credit_relay/EGRCR_FINITE_RESOURCE_CENSORED_SUBSTITUTION_B01_INTAKE_20260904.md
[eociv-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/eociv_lite/DIRECTION.md
[eociv-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/eociv_lite/EOCIV_A1_HEADROOM_REFERENCE_INVENTORY_INTAKE_20260904.md
[recct-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/recct_lite/DIRECTION.md
[recct-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/recct_lite/RECCT_HEADROOM_CENSUS_A01_INTAKE_20260904.md
[scope-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/scope_1s/DIRECTION.md
[scope-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/scope_1s/SCOPE1S_GUIDANCE_A1_HEADROOM_CENSUS_INTAKE_20260904.md
[ec4g-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/ec4g_r1/DIRECTION.md
[ec4g-intake]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/ec4g_r1/EC4G_CURRENT_HOST_HEADROOM_A_RECON_INTAKE_20260904.md
[orbit-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/orbit_shadow_read/DIRECTION.md
[orbit-index]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/orbit_shadow_read/CODE_SCIENCE_INDEX.md
[apfi-dir]: https://github.com/CartmanFatass/My-paper-code/blob/f13c19c8d039a6cb8bed9d0c9403e2acbf8713f7/docs/research/candidates/active_post_churn_population_flow_identification/DIRECTION.md
[acac-paper]: https://proceedings.mlr.press/v267/jung25a.html
[mappo-paper]: https://arxiv.org/abs/2103.01955
[eval-paper]: https://proceedings.neurips.cc/paper/2021/hash/f514cec81cb148559cf475e7426eed5e-Abstract.html
