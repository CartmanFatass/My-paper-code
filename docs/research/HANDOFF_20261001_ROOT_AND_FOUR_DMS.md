# 本轮研究交接：Root 与四位 DM（2026-10-01）

> **状态：整理中，尚未完成交接。** 当前已接受的研究和已开始的选题评估继续完成，
> 不启动下一轮实验。最终状态由 Root 在四位 DM 完成各自部分后更新。

<!-- ROOT_OVERVIEW_BEGIN -->
## Root 总览

Owner 本次要求：完成这一轮，不打断正在进行的工作，然后写一个独立 handoff；
Root 负责总览，四位 DM 各自撰写负责部分，方便后续继续。本文件按该明确请求建立，
不替代原始 NOTES、运行证据或 RESEARCH 当前状态。

本轮边界是完成已接受的 S7 C/H/F 比较及三份已经开始的后续选题评估。
三个较早完成的研究已经发表、独立判读和清理。后续候选尚未选定；
即使建议可行，也不据此启动下一轮。交接完成后，本 Root 及这四位 DM 停在交接边界，
等待 owner 明确继续。状态询问、阅读 handoff 或工作流修改本身不恢复研究。
Claude 的独立授权、FSD/PPC 暂停、G33 冻结和 Milan 数据依赖保持原范围。

### 四位 DM 与本轮责任

| DM | 本轮结果性研究 | 当前交接事项 |
| --- | --- | --- |
| /root/dm_fleet_transmission | S7 C/H/F：预测信息是否改善完整服务控制 | 原操作继续至完整读出、独立判读、发表和清理 |
| /root/dm_fleet_adaptation | B10：联合本地运动与发射控制学习 | 已关闭；完成静默与下一次观测问题的资料及成本评估 |
| /root/dm_parent_adaptation | RF information B01：付费信息包与普通先验控制 | 已关闭；完成整体 U32_FULL/P_PRIOR 候选的独立评估 |
| /root/dm_user_waiting | RF uncertainty B01：U32 与同测量信息的 P | 已关闭；完成策略参数搜索与等投入普通校准候选的资料及成本评估 |

四个现有会话均未被 owner 归档。后续若仍未归档，可按 RESEARCH 路由复用；
若 owner 已归档完成会话，创建新的 DM 并继承其已发表证据，不恢复归档会话。
Oracle、Scout 和 Reviewer 是辅助工作，不计为第五个 DM。

### 已经改变的判断

- **U32 有条件的目标收益成立，等待代价必须同时保留。** 对 P 的 payload-J 增量
  为 +.007529588，32 世界中 26 正、6 负；服务数量增量仍未确定。平均年龄、
  最差用户年龄和最长未服务间隔均恶化，存在目标收益为正但连续排除长达
  129/127 tick 的闭合间隔。该结果不证明共同测量包值得购买。
- **普通 P 的 FULL 信息包没有挣回完整成本。** 对 P_PRIOR 的 payload-J 为
  −.015929915，32 世界均为负，其中一例近乎持平。部分等待改善与严重反例并存；
  不能将这一效应与另一面板的 U32−P 相加得到 U32_FULL−P_PRIOR。
- **B10 两个联合学习实例均未形成超出强参照的增量。** 对实际 INIT90 的 J
  为 −.0229865/−.0261492，并低于 P0、Bstar、Hdirect 的所列强组合。训练真实激活，
  保留既有 P0/HIDDEN/普通控制能力以及 CJ 的即时正例；不据此断言一般不可学习，
  也未识别各次失败的共同原因。
- **S7 的判断待完整结果。** 部分进度不作科学结论。由负责 DM 在下文写入完整结果
  和独立判读后，Root 再整合本项。

三个已完成研究的被清理目标合计释放 **6,550,663,168 allocated bytes（约 6.10 GiB）**；
这是各自实际清理目标的净下降，不能称为整台机器的空闲空间变化。S7 本轮清理尚未计入。
各研究保留必要的单份正面、负面和失败证据，详见各 DM 部分。

### 下一轮候选和实际审阅状态

当前只有三个资料评估中的候选问题，没有新实验被选定：

1. RF 完整 U32_FULL 对 P_PRIOR 包比较，补足两项既有比较不能相减回答的用途问题。
2. 本地静默的即时收益与下一次被遮蔽观测之间，合法保留信息或不同观测合同是否有用。
3. 完整回合参数搜索是否能使小幅上下文策略发展超过等投入全局校准及已有强参照。

最终建议、完整成本、是否建议购买及反对理由由各负责 DM 在对应部分保留。
候选名称和空余算力均不构成执行授权。

模型来源已作纠正：RF 早期资料建议来自原 age_control_interface Scout，
实际为 Luna/medium；先前把它称为 Astra Max Oracle 是 Root 的错误。
原建议和来源纠正已分别保存于
[RF 原始建议与更正](candidates/uav_radio_information_cost/NOTES.md#b02-original-opportunity-advice)。
新的 /root/oracle_rf_integrated 已核对实际运行是 Astra/max，正在进行独立科学评估；
另两位 Oracle 实际运行同样已核对为 Astra/max。旧建议保留为资料，不替代这次独立评估。

### 继续时先恢复什么

以 [RESEARCH 当前状态](RESEARCH.md) 和各 DM 下列精确证据为入口。工作区是
/home/fires/hmasd-wsl 的 main；节点和解释器取自 .codex/hmasd-compute.toml。
保持原始输入和操作身份，已结束的 worker、reader 和观察句柄不重启。
新研究须在 owner 明确继续后，重新作科学投入选择、前瞻声明、精确输入发表和实际节点准入。

各 DM 负责其方向目录及 NOTES；共享 Git 索引/提交仍串行且只提交明确拥有的路径。
恢复时检查当前他方改动，不从本文件复制旧版 RESEARCH 覆盖共享文件。
本文件各 DM 部分由本人撰写；Root 在全部完成后更新总览和交接状态。

**Root 最后核对：待本轮全部结果、三份完整建议、四份 DM 交接和终态清理齐备后填写。**
<!-- ROOT_OVERVIEW_END -->

<!-- DM_FLEET_TRANSMISSION_BEGIN -->
## DM：机群发射控制与 S7 预测用途

待 /root/dm_fleet_transmission 完成当前研究后本人填写。
<!-- DM_FLEET_TRANSMISSION_END -->

<!-- DM_FLEET_ADAPTATION_BEGIN -->
## DM：机群策略发展与本地联合控制

**本节完成于 2026-10-01 UTC。方向 `uav_fleet_adaptation` 为 reserve；B01–B10
均已完整判读、独立审阅、发表和清理。** 本轮最后的源码／成本评估也已结束，完整
Oracle 建议已读并保留。没有运行中的 worker、reader、observer、未读意见或已选后继。
遵照 owner 的本轮收尾要求，停在交接边界。建议可行不构成实施或运行授权。

### 延续的问题与已保留能力

持续问题是：在只能看到本机局部信息、队友独立响应的服务任务中，继承的策略能否通过
学习运动、发射和近期行为信息，发展出超越有能力普通控制的完整合作价值？各批回答的是
有限方法与合同下的子问题。学习的正例、原控制器的能力和后续失败都应继承；没有证据把
这些不同失败归为统一的 critic、信用分配、熵或表示原因，也不能据此否定一般可学习性。

资产名须保持清楚：`P0/S` 是 B02 原始学生；`P1` 是 B03 独立构造，未按最终得分择优
替换 P0；`Bstar0` 是付费校准的 P0 温度版本；`Hdirect` 是原 P0 与 C 的固定概率混合；
`HIDDEN` 是 B08 的冻结局部门控。`A` 表示全 ON，`ZERO` 只允许当前用户计数为零的
当轮成员 OFF。完整 CPU 仍须支付 C 的局部无线／导航特征，不因用了网络而自动节省。

下表链接到本方向原始记录；这些 B 编号不能与其他方向的同号研究混用。J 是原宿主的
完整回合目标，service 是每步团队服务数；p10/minimum 是回合内团队服务尾部，不能
替代单用户持续服务或安全。跨世界区间为条件、逐项描述区间，不是独立训练总体结论。

| 研究 | 保留的能力、负面证据与停止范围 | 本批已付成本 |
| --- | --- | --- |
| [B02](candidates/uav_fleet_adaptation/NOTES.md#b02-complete-reading) | C 模仿与聚合得到可执行起点：sampled−C J +.046566、service +3.352905，区间为正；greedy 增量未确定，最低服务均值 −.78125。查询 CPU 是 C 的 1.34×/5.26×，未得到加速。 | 1 fit；114,688 原生步；8,000 updates；107.544 worker+reader CPU-s。 |
| [B03](candidates/uav_fleet_adaptation/NOTES.md#b03-independent-disposition) | 新训练世界／初始化／打乱再次达到构造标准；sampled−C J +.056548、service +4.114014，但最低服务 −.4375、路径 +990.66m/UAV。评价仍是同一暴露面板，不是新总体复现；保留两资产。 | 1 fit；98,304 步；8,000 updates；97.502 CPU-s。 |
| [B04](candidates/uav_fleet_adaptation/NOTES.md#b04-independent-disposition) | 完整 PPO 继续训练未形成增量：R−S J −.040278/−.005212，首项区间为负；物理动作真实改变。原 S−普通随机 Q 为 +.014836/+.021881（L0 的 J 区间仍跨零），且 p10 更好、路径更短；温度校准含尾部／路径代价。停止原继续训练配方。 | 2 fits＋2 次付费校准；335,872 步；517.603 chain CPU-s。 |
| [B05](candidates/uav_fleet_adaptation/NOTES.md#b05-independent-disposition) | 2,048 配对上下文／4,096 获取回合的原生后果标签，未使 CONT 超过 S 或同数据 CAL；CONT−S J −.005135/−.005498，区间跨零。S−Q +.023534/+.027712 仍为正。L1 世界29483104的 S/Bstar、CAL 零服务 tick 已有明确文字更正，不能沿用早期“无中断”叙述。 | 4 fits；4,448 回合／1,138,688 步；1,620.467 chain CPU-s。 |
| [B06](candidates/uav_fleet_adaptation/NOTES.md#b06-independent-disposition) | N4/N6 混合 M−F J +.005574 未确定，M−原 P 为 −.001980；质量提高但多飞584m。P−Q 在六个 N4/N5/N6 单元均正。count 分支激活，但保存观测最多只见2个同伴，不能称验证了大可见 roster。停止该混合配方。 | 4 fits；679,976 步；978.664 chain CPU-s，另有 A01 零曝光技术失败1.286 CPU-s。 |
| [B07](candidates/uav_fleet_adaptation/NOTES.md#b07-independent-disposition) | T 目标拟合很好（KL .000188），T−P、T−H、Tdirect−P 的 J 仍未确定；学习者均低于付费 Bstar。保留 Hdirect−P +.007329 的条件正例及15个负世界、计算／尾部代价。停止该目标发展投入。 | 2 fits；172,032 步；560.463 chain CPU-s。 |
| [B08](candidates/uav_fleet_adaptation/NOTES.md#b08-independent-disposition) | HIDDEN−RAW J +.007318、HIDDEN−P0_A +.010576，区间为正：保留这项有限学习增量。没有超过 Bstar0_ZERO/Hdirect_ZERO 的完整证据；对 P0_A 的 p10/minimum −.789/−.781，路径 +821m。特征容量和正则化同时改变，非已识别语义。最终7个零服务 tick／6回合、获取38 tick／13回合均保留。 | 2 ridge fits；507,904 步；1,488.812 完整 worker/reader CPU-s。 |
| [B09](candidates/uav_fleet_adaptation/NOTES.md#b09-independent-disposition) | 固定但响应的异构队友中，四个 H−F J 对比区间均跨零，没有超过 P0/Bstar/Hdirect 的端点。全部16,384最终 H 输入将历史置零后，已保存抽样命令／物理路径均不变；不能把 H0 的局部路径节省归功于已执行历史响应。停止该焦点残差配方。 | 4 fits；655,360 步；3,027.478 chain CPU-s。 |
| [B10](candidates/uav_fleet_adaptation/NOTES.md#b10-independent-disposition) | 两个完整联合局部运动／物理发射学习实例均低于实际 INIT90 与强保留参照；保留 CJ 即时机会和 ZERO 尾部能力，结束该学习投入。详见下文。 | 2 fits；1,376回合／352,256步；1,780.045981 enclosing CPU-s。 |

**B02–B10 累计 22 fits＋2 次校准、4,055,080 原生步。** 表中时间保持各自真实的
进程范围／节点，不能改称同一机器的总 wall；有限正确性检查、未完整计时的工程／审阅
支持和更早 [B01](candidates/uav_fleet_adaptation/NOTES.md#b01-complete-reading) 成本另计。
零 fit 后继也不会消除这些既付投入。B08 正例和 S 的持续能力不因 B10 失败而撤销。

### 最新 B10：结果、核验与独立判断

合同为原 N5/U50/H256 静态用户、free-space 宿主，每4 tick 决策；五个局部动作先取
旧 mask 的观测，再只安装一次新 mask。轮转 `r=(tick//4)%5` 的一员可 OFF，其余
强制 ON；关闭发射同时遮蔽该成员用户和同伴观测。两个训练块共用原 P0/HIDDEN，
54 类联合头及 body 均训练；实际初始化 `INIT90` 的门控是 .9/.1 平滑，不能与
门控确定、运动仍抽样的 P0_HIDDEN 当作相同轨迹。最终15程序、32共同世界30012000–30012031，
随机程序两 tapes 在世界内平均；32预定对比，20,000共同 world bootstrap。

| 完整对比 | J 差与逐项95%区间 | service 差 |
| --- | --- | ---: |
| J0−INIT90 | −.022986507 [−.032303, −.014040] | −1.609558 |
| J1−INIT90 | −.026149186 [−.034239, −.017991] | −1.612427 |
| J0−Hdirect_ZERO | −.028599759 [−.041855, −.015758] | −1.938599 |
| J1−Hdirect_ZERO | −.031762438 [−.043734, −.019441] | −1.941467 |

两端点对 P0_A/ZERO/HIDDEN、Bstar0_A/ZERO、Hdirect_A/ZERO 的14个 J/service
单元区间全部为负。对 C/CJ 的窄收益存在，但不能当作此次训练增量。J0 比 Bstar0
少飞约502–535m且 ON 暴露略低，J1 比 INIT90 多飞2,241.5m；没有能源模型来给这些
取舍定价。两端点前半／后半均损失，每 fit 实际512次 actor＋512次 critic Adam，
参数和物理行为均改变，4,352初始行的原 logits 精确复制；不是未训练、仅启动期失败，
两者 OFF 频率反向改变也不能支持单一 OFF 频率解释。最终19个零服务 tick／6回合保留。
P0_HIDDEN/INIT90 本身已有反例：世界30012025的共享前缀中，关闭一员让四步服务
从[10,10,10,10]降到[1,0,0,0]；它不是新学习损失的充分原因。

CJ 的五次首次发射差异，在命令／位置相同的接续四步均有真实原生收益；完整
CJ−C_ZERO 却是2正、3负、27同轨，J均值+.000604。这是原 critic 的事后诊断，
不是补加的冻结主对比或完整升级。在30012030，静默成员下一次命令双方仍为零，
其他成员命令／mask 已不同；不能把全部损失归给该成员的下一次移动。五个普通
ZERO−A 的 J 区间仍跨零，但平均最低服务全部改善，保留其条件尾部能力。

全量 reader 检查1,376回合／352,256保存步、441,696标量状态、2,208,480局部行、
119,257,920标量功率链路、440,320实际策略请求、88,064次 mask，及256训练组全部
模型链。它重建物理／观测／策略／采样、critic、优势与首 epoch loss，核验最终 Adam
状态和每参数步数；**未独立重放后续 epoch 梯度与 Adam 算术**。额外原生步、优化器
更新、重拟合均为零。独立 ResearchCritic 先重建证据再读原建议，核对全部 raw／资产
哈希、摘要和101个 raw 回合；其完整意见与 DM 回应均已发表，`MATERIAL_DISSENT: no`。
处置为停止本次学习投入，保留能力／反例和较宽问题；没有 confirmation 或自动修补。

最新实测完整生产成本为 worker 860.761 CPU-s、reader 918.283 CPU-s，enclosing
1,780.045981 CPU-s／1,717.667 perf-counter wall-s，峰值731,560 KiB RSS。
另计有限正确性检查26.70 wall-s／20.59 CPU-s；最初12–24支持小时是预测，不是实测劳动。

### 可恢复证据与清理状态

- 精确执行源码：[73278079](https://github.com/CartmanFatass/My-paper-code/tree/73278079be41ad8068b73594a32cde5841119032/experiments/candidates/uav_fleet_adaptation/b10_joint_control)。完整结果／原独立意见：[4a0db116](https://github.com/CartmanFatass/My-paper-code/blob/4a0db1166d00511f45a4ee40689e67190a67ea87/docs/research/candidates/uav_fleet_adaptation/NOTES.md#b10-independent-disposition)；最终 standing／清理：[bc327826](https://github.com/CartmanFatass/My-paper-code/blob/bc3278267d83515506bbf3aee8cf7054964f9967/docs/research/candidates/uav_fleet_adaptation/NOTES.md#b10-final-cleanup)。原设计意见及采用记录在 [B10 original advice](candidates/uav_fleet_adaptation/NOTES.md#b10-original-oracle-advice)，不以事后摘要替代。
- Git 中的[完整紧凑面板](../../runs/uav_fleet_adaptation/b10_joint_control_a01/publication.json)为1,056,941 bytes，SHA256 `a78ebbe0318fcb48f9b16f5dffdf5b88cc59cf5a538a5e14ff0d202798ce6f2c`；同目录含 exact config、准入、原生 terminal／exit。全量唯一副本在配置节点 `wsl_4070`（SSH `hmasd-wsl-node`）的 `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b10_joint_control_a01/`：1,647 files，1,115,774,100 logical／1,119,678,464 allocated bytes，含1,376 raw NPZ、256 pregroup模型及2实际最终模型／Adam。summary/reading/ledger完整哈希在[完整读出](candidates/uav_fleet_adaptation/NOTES.md#b10-complete-reading)，清理后已重验；不要重跑来恢复。
- 原 P0 在同节点 `/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt`，424,487 bytes，SHA256 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`；原 source `e945483b85c7f8ddfc315c57f36938d6c14201c7`。HIDDEN 在 `runs/uav_fleet_adaptation/b08_local_gate_a01/assets/HIDDEN.npz`，5,119 bytes，SHA256 `e8f6ecea525d7892edc1e82c407070d14ea234dae3c90c6c054ce16804eaa026`。两份 canonical 输入保持不变；其他批次原始资产／留存节点由上表各自 cleanup 记录恢复。
- B10 实际删除：远端两个精确 managed snapshots `cdc6962ab4704c9e94c544741b8474cc`、`80bde676266946438831245ee20f8634`；远端 `/home/wu/hmasd-inputs/uav_fleet_adaptation/b10_joint_control_a01/` 及空父目录；本地 B10 code/test 的两个 `__pycache__`；早期原意见临时文件及最后 `temp/directions/uav_fleet_adaptation/`。合计净释放 **1,639,141,376 allocated bytes**，所有目标已不存在、无清理工具 blocker；不是整机空闲空间估计。13个有用实现模块、3份检查以及必需正／负证据保留，未建立第二备份树。
- B10 唯一接受操作于09:29:32 UTC exit0；原 runner/supervisor均已消失，observer generation44已停止，事件全部消费，未重启／迁移／重发。最终 Oracle 已声明读取完成，不再占用 raw 或 staging。此次纯资料评估没有新增临时数据或计算进程；不需新的删除目标。

### 已完成评估但未选定的后续比较

**状态：UNSELECTED。** 完整[原问题](candidates/uav_fleet_adaptation/NOTES.md#post-b10-original-source-question)、
[DM 源码／完整报价](candidates/uav_fleet_adaptation/NOTES.md#post-b10-original-source-price)、
[Oracle 最终原文与覆盖范围](candidates/uav_fleet_adaptation/NOTES.md#post-b10-original-oracle-recommendation)、
[DM 处置](candidates/uav_fleet_adaptation/NOTES.md#post-b10-assessment-disposition)均已保留。
三份完整原文及各自哈希已先发表于
[855046e1](https://github.com/CartmanFatass/My-paper-code/blob/855046e1f165a3deb13571367215effc47e47555/docs/research/candidates/uav_fleet_adaptation/NOTES.md#post-b10-blind-return-source-assessment)；Root 已读完整原问答和最终建议，采纳未选定保留的处置。
Oracle 在分开的 Astra/max 上下文中建议值得保留这一有限研究，无实质异议；它明确收到
Root 的候选解释，不是盲化 B10 判读。其新增原始 trace 读取仅限既有五世界的10份
CJ/C_ZERO首分歧／下一边界记录，完整重建仍依赖已接受 reader／critic；三处书库的
实际 primary 覆盖和不可用本地 PDF 的替代来源均保存在原意见中，不作新颖性宣称。

**问题与预测：** 已知自行静默产生空观测后，合法保存一条既算好的本机命令，能否让
即时无线收益保留到完整回合？反解释是队友无线响应、旧评分和改变的访问路径主导结果，
两种承诺仍可能无益或更差。这是经验理解问题，未指定学习架构，未识别 B10 失败原因。

原 N5/U50/H256、4 tick、轮转 eligibility、old-row/单 setter 合同不变。比较精确
`C_ZERO`、`CJ`、`CJ_KEEP`、`CJ_RETURN`、`Hdirect_ZERO`。两记忆程序只在本机
eligible OFF 且先前本机当前用户数为正时保存一次承诺；源码证明它恰是严格正服务
CJ OFF 分支。KEEP 保存已发出的零命令，RETURN 保存 CJ 改写前的 C ON 选择
`answer['c_index']`。下一边界收到实际被遮蔽行，跳过 C 评分及空行导航变更，保持
origin 的 post-nav，发保存命令、请求不 OFF 并消费 pending。命令选择先于 setter；
setter 随公开轮转强制该员 ON，随后四步移动发生在 ON 状态。tick252新建而未消费的
承诺如实留作 terminal 证据，reset 清空，不延长回合。不能偷加 ACK、新观测、全局
mask、同伴动作、奖励输入、当前 C shadow query 或额外 OFF 四步。

`ZERO_INDEX=0`；保留严格 score 比较、稳定 tie、原零服务例外和零计数 fallback。
相同 retained FP32 行／校准／算术／nav 下，重复评分只会恢复原 C 选择，不需要新增
几何 replanner；这只是条件源码等式，旧计划是否仍准确未知。C_ZERO/Hdirect_ZERO
的正计数 OFF guard 永不触发，因此给予相同记忆机会后行为恒同，不多跑冗余臂。
原 all-ON history 的 no-hearing 推断也不能免费套到已知自身静默。

最重要的未决点：既有五个 origin 的原 C ON 命令也都是零，KEEP/RETURN 在那里
保存相同命令；新面板是否有不同命令、是否物理介入、是否有完整收益均未证明。
pending 数本身不是激活。保存 origin行／计数／clock、C与承诺类别、nav、创建／消费／
终止、实际 clipping 后位移；分歧后的跨臂动作不能当作同状态中介比较。

候选一次完整面板：32 fresh worlds，四个确定程序各一次、Hdirect两 tapes，共
**192回合、49,152原生步、0 fits／0 optimizer／0新目标获取**。待定标识为 worlds
30021000–30021031、Hdirect roots30022031/32、bootstrap30022041、constructor30022051；
源码静态搜查未见本地冲突，不是全局预留。九对比：CJ−C_ZERO，KEEP−CJ，RETURN−CJ，
RETURN−KEEP，KEEP−C_ZERO，RETURN−C_ZERO，CJ−Hdirect_ZERO，KEEP−Hdirect_ZERO，
RETURN−Hdirect_ZERO。每世界平均 Hdirect tapes，所有32世界保留，20,000共同 bootstrap；
J/service/quality/p10/minimum/outage/path/silent path/exposure/switch/CPU 全量读取。
区间逐项且条件于原 P0；不能择赢家、稀有激活后加世界、补 pilot 或原生 suffix。

读法事先保留：同时优于 CJ 和 C_ZERO 才支持有限完整 gating 价值；只优于 CJ 是缓解；
RETURN 需有实际区别且超过 KEEP，才支持保留特定 C 计划的增量。即便超过 C_ZERO
而低于 Hdirect，仍可增加经验理解，但不是完整控制升级。无触发／相同／有介入仍无益
均可结束此投入；所有尾部和路径损失保留，没有自动扩大、再训练或 Pro 轮次。

**完整报价，尚未发生：** worker 192 resets＋1 constructor reset、12,288 mask、
61,440 policy请求、6,144 CJ OFF评分／24,576逻辑 OFF tick、20,480 Hdirect uniforms。
原生无线16,949,075 dense SINR slots、12,829,700 distance、308,165观测行，含丢弃的
刷新行。每记忆臂最多2,048创建／2,016消费，差为末端 pending；若消费为 K/R，
C请求61,440−K−R，实际 cache misses M 决定27M paths／108M modeled ticks。
不扣未知命中／旁路的每 pass 上界是1,658,880 paths／6,635,520 modeled ticks／
139,468,800 controller power links；跳过的空行自身无线工作为零，不能每次虚报
2,260 links节省。Hdirect每 pass需320–20,480冻结 P0 rows，仍生成40,960个T/H概率向量，
无额外 feature-helper 搜索。worker另有22,195布局 uniforms；worker/reader各做22,080
布局核验 uniforms、640,000 bootstrap integers；本次评估没有抽取任何这些样本。

完整 reader另付61,632标量状态／308,160局部行、16,640,640功率链路、16,024,320
距离、16,948,800 dense slots，并重放全部实际策略／C／OFF／P0／draw及独立 memory
递推，0原生步／0优化。它不能信任新 wrapper 的 pending 字段；旁路 C 字段须明确为
未执行。B10 frozen runner不可直接改参数复用，需有界 adapter、P0-only loader、显式
确定臂表、计数／schema／对比及独立状态机；不修改旧 B10 合同。

只需原 P0一份冻结输入，worker/reader各构造并全量加载一次34,715参数Student，无
HIDDEN或训练 checkpoints。预计 staging425,984 allocated bytes加目录；基础 raw
shape386,588,032未压缩 bytes，origin行最多另1,703,936 bytes加状态。预测新 canonical
压缩证据0.12–0.25GB，连同B10量级源码snapshot临时约0.95–1.2GB；无第二结果副本。
同节点单线程预测 worker60–240、reader100–360、enclosing180–720 CPU-s，wall4–20分钟
另加不确定排队，RSS0.4–1.0GiB。**工程／检查／review及完整判读／发表／清理预计8–16
支持小时当量**，不是已计时劳动。以上均为报价，未来须实测节点准入和实际计数。

正确性也有成本：原建议给出可前瞻绑定的12个 fake H24回合／288 fake transitions、
每 pass360策略行、72 masks、372 reader状态／100,440标量links、至多120 fabricated
P0 rows／36 OFF scores，另计 guard/tie/reset/terminal/cache/corruption 单元 fixture。
这不是已执行或已授权测试预算；无需额外原生 pilot。新增 memory/provenance/reader
应独立工程审阅；成本详单、cache payload、reader能力边界均在原报价，不用“零fit”隐藏。

### 恢复条件

先由 owner 明确继续，再由 Root 选择跨题投入；本候选尚未分配 direction/tag 或执行
预算。若被选，先读当前 RESEARCH、上述完整原问答／建议／处置和 frozen B10 source，
保留既有停止与反例，绑定最终 seeds／源输入／前瞻成本，完成有界实现及审阅，发表
精确输入后才按 `.codex/hmasd-compute.toml` 实际节点准入。不得重启 B10 已终止句柄或
将该候选叫作未完成的 B10 修复。本 DM 尚未归档时可依现行路由继续；若 owner 已归档，
创建后继 DM 继承这里的证据与约束。没有数据交付或外部生产者依赖需要持续轮询。
<!-- DM_FLEET_ADAPTATION_END -->

<!-- DM_PARENT_ADAPTATION_BEGIN -->
## DM：父策略发展与无线信息成本

待 /root/dm_parent_adaptation 完成当前资料评估后本人填写。
<!-- DM_PARENT_ADAPTATION_END -->

<!-- DM_USER_WAITING_BEGIN -->
## DM：用户等待、无线不确定性与后续策略发展候选

待 /root/dm_user_waiting 完成当前资料评估后本人填写。
<!-- DM_USER_WAITING_END -->
