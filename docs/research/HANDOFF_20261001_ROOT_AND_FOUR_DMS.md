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

**本节由 /root/dm_fleet_transmission 本人于 2026-10-01 UTC 完成。方向
`uav_fleet_transmission` 为 reserve；B01–B09 均已完整判读、独立审阅、发表和收尾。**
本轮最后的 B09 保留“预测在这个规划器内有原生服务价值”的正结论，同时结束明显落后于
C 的 H/F 完整规划包投入。没有运行中的 worker、reader、observer、未读意见或已选后继。
本节完成后释放独占写入轮次给 Root，停在 owner 明确要求的交接边界。

### 延续的问题、责任与不能丢失的解释

目前问题是：**在用户已经移动的原生任务中，合法用户历史能否提高完整协同服务，超过
有能力的当前状态控制？** 更早的 B01–B07 分别研究发射授权、静默移动、时间互补、普通
随机控制、反馈节奏与联合更新。它们保留了一批普通控制能力和固定学习资产的条件性价值；
目录连续不代表九批是同一个估计量，也不能把旧 S1 的归一化 J 与 S7 的 H3000 总 J 混用。

本 DM 通过可修订方案承担问题内的科学推理与执行；Root 负责新问题与跨题分配。当前原生
句柄为 `/root/dm_fleet_transmission`，线程标识 `01a0f02a-2102-7aa3-be5a-adfb99e49910`；
共享主工作区 `/home/fires/hmasd-wsl` 的 `main`。当前没有要迁移或重启的操作。
若 owner 以后明确继续且会话未归档，可按当前 RESEARCH 路由复用；已归档则由新 DM 继承
已发表证据，不复活旧句柄。状态询问、读交接文件和工作流编辑均不解除本轮停止。

判断必须分开：任务存在机会、表示实际准确、控制实际改变、完整包有用途，以及能否通过
学习进一步发展。B08 建立准确表示却没有完整增量；B09 新增了规划器内的 J／服务正收益，
但没有使该规划器超过 C。九批自身均为 **0 新 fit**，不诊断一般学习成败。P_BS 作为 C 的
条件性性能参照仍带有既往世界 28100224 的储备电量／默认替换限制；本轮相对胜出不清除它。

### B01–B08 累计能力、反证与停止范围

| 研究 | 保留的实质结论 | 不能改写的限制／反证 |
| --- | --- | --- |
| B01，固定 H6／SET 的发射授权 | N8 的 E 相对 all：H6 J +.096344、服务 +6.235125；SET J +.254920、服务 +15.029375，均为 16/16 世界服务增加。普通 C/E 同样有能力。 | N4/H6 E−all J −.02005、服务 −1.474375，10 降／3 升／3 同值；不作全配置默认或学习修复。 |
| B02，普通静默移动 R 对 C/J | C/J/R 平均 J .615036/.631313/.648963，服务 39.049875/40.300750/41.853；R 的静默再定位与恢复真实激活，有完整收益。 | 保留质量、服务尾部和路径代价；不证明必须采用 option 或学习。完整 C/J/R 比较的运行代价不同。 |
| B03，完整继续后果 T 对 R | T−R J +.007400 [.001879,.014257]，服务 +.558625 [.148197,1.038134]；J 为 9 升／7 同值，普通完整后果判断有条件收益。 | 服务有一个负世界；世界 11 的服务／路径取舍仍在。T 约为 R 的 4.019 倍回合 CPU，不证明普遍优势。A01 的执行前技术失败保留。 |
| B04，固定两次机会的时间互补 | T/G2/A2 平均 J .658213/.660257/.661963，服务 42.5455/42.72575/42.969625；六个首次承诺牺牲早期价值而换取完整收益。80 个实际预测的命令、mask、服务均核验。 | 已知有限模型和固定时序已经能形成该能力，不推出最优性或学习必要性；J 不含路径成本，质量／路径不利仍在。原始 B04/N8 证据有跨方向消费者，不能删。 |
| B05，普通评分尾部采样 G 对 Q 与固定 S | S_L1−G J +.023431 [.012843,.033524]、服务 +1.868；S_L0−G J +.013616 的区间跨零，但保留服务／路径价值。G 对 Q10 的平均 J 增量未定，服务 p10／质量／计算等取舍有用。 | 世界 29630013 的 S_L0/S_L1/Bstar_L0 六条轨迹有原生零服务；普通臂本面板无此例也不等于安全。固定资产重复评价不增加训练复制，G 未吸收 S_L1 并不证明学习必需。 |
| B06，H4／计数损失触发 E／H1 | E 对两 S 的 H4 平均路径减少约 41%/44%；对 H1 有较高 J／服务、较低 CPU。普通 E 也保留低运动能力。 | E−H4 J／服务均未定，不能称保持；H1−H4 在所有六个普通／S 父策略上 J 均下降。S_L0 世界 29670024 的 19 tick 零服务不被 E 覆盖；首次额外查询是 tick30/agent0，原 tick26 说法已更正。 |
| B07，同步／分散更新，匹配个人时钟和抽样 | 分散显著减少同时物理变化、降低路径；Q10 的平均服务能力仍在。 | C/Q10 的分散−同步 J／服务均为负均值、区间跨零；不证明服务保持、优越或等价。4 个 offset 与 2 个动作 tape 均在世界内平均，不能虚增样本量。 |
| B08，原 S7-S2 的 C/M/V | 普通匿名跟踪和固定 t+15 外推在自身 68,979 个来源绑定预测上，平均误差 .733m，对保持最后坐标 33.218m；32 世界均改善，实际轨迹均改变。 | V−M J −21.410 [−67.939,25.119]、累计 QoS −32.818 [−74.707,9.071]；M−C/V−C 亦未建立完整增量。少数大误差、身份切换与服务／能源不利保留；准确表示不等于 H1 质心／中点控制有用。 |

每批的完整正反世界、原始独立诊断与本人处置仍在
[B01](candidates/uav_fleet_transmission/NOTES.md#b01-complete-reading)、
[B02](candidates/uav_fleet_transmission/NOTES.md#b02-complete-reading)、
[B03](candidates/uav_fleet_transmission/NOTES.md#b03-complete-reading)、
[B04](candidates/uav_fleet_transmission/NOTES.md#b04-complete-reading)、
[B05](candidates/uav_fleet_transmission/NOTES.md#b05-independent-disposition)、
[B06](candidates/uav_fleet_transmission/NOTES.md#b06-independent-disposition)、
[B07](candidates/uav_fleet_transmission/NOTES.md#b07-independent-disposition)、
[B08](candidates/uav_fleet_transmission/NOTES.md#b08-independent-disposition)。
这些旧比较均已结束，没有因 B09 或此次交接重新获得加世界、调参数、训练或确认的授权。

### 本轮 B09：固定比较及完整结论

原始源代码／成本询问、完整 Astra Max 选题建议及实际文献覆盖、Root 独立选择与前瞻合同，分别见
[源码与报价](candidates/uav_fleet_transmission/NOTES.md#post-b08-source-feasibility)、
[完整原建议](candidates/uav_fleet_transmission/NOTES.md#b09-original-selection-advice)、
[Root 采纳](candidates/uav_fleet_transmission/NOTES.md#b09-root-adoption)、
[固定合同／L0](candidates/uav_fleet_transmission/NOTES.md#b09-selected-contract)。
此前三处书库、July 和外审的实际覆盖由原建议保留；它们支持比较结构，不保证 S7 效果，
也没有给出新颖性或一般可学习性结论。已完成的完整选择块按 Root 授权原样归档：
[精确计划历史](archive/2026-10-01/RESEARCH-service-prediction-completion.md)。
归档源为 `ddedb339ad268b6e327fe6202dd870fbcc8d9fe2`，原选择为 `2376d6835`；只退役计划，未改判历史。

原生宿主保持 fault-free S7-S2、N8/U30/H3000、dt1、每用户 1Mbps、已有移动规律及无线／路由／
能源／奖励／终止。32 个新配对世界 **29890001–29890032**，C/H/F 各一条，完整 96 回合。
C 为精确 B08 C/P_BS。H/F 共用匿名跟踪、估计当前坐标 `clip(last + age*v)`、合法 BS 观测／
记忆／先验优先级、30 tick 计划钟与原 shield；H 将当前估计保持到未来，F 外推到 10/20/30。
H 因而不是 B08 的保持最后坐标 M。二者共用四种初始布局和两轮有限 pattern 搜索，
每个候选模拟 30 个联合运动／能源 tick，并在三个时刻计算 QoS 与返航代价；没有按结果扩展搜索。
空用户／无合法 BS 的原 fallback 保留。全部八机观测免费汇集，是继承的信息合同。

模型由公开配置独立构造，不复制实时隐藏状态、真实用户 ID／速度／未来／RNG；没有 reset/step。
未知用户按零服务计入 30 人分母但不产生竞争，**这不是服务下界**。省略 guard、中间关联、
部分能量顺序和原生势函数／事件等，预测不是精确原生后续。F−H 是固定未来输入干预的完整
闭环效果；后续观测／搜索不同是其后果，既不破坏该比较，也不识别准确率的中介作用。

| 指标 | C | H | F |
| --- | ---: | ---: | ---: |
| 平均原生总 J | 2156.274 | 1636.023 | 1701.997 |
| 平均 QoS／step | .731664 | .561128 | .581384 |
| 平均最差用户累计 QoS | 1511.078 | 775.514 | 828.979 |
| 平均最长个体零交付间隔，tick | 378.781 | 1144.906 | 1060.281 |
| 全队平均推进耗能，Wh | 1387.118 | 1239.261 | 1240.642 |
| 平均储备不足 UAV-step | 116.313 | 278.344 | 147.625 |
| 平均控制提案 CPU／任务，s | .903 | 172.093 | 171.810 |

| 配对差 | 总 J 均值 [描述性 t95] | 累计 QoS 均值 [描述性 t95] | J／QoS 均为升／降／同值 |
| --- | ---: | ---: | ---: |
| **F−H，主要比较** | **+65.974 [12.281,119.668]** | **+60.769 [9.617,111.922]** | **17／9／6** |
| F−C | −454.277 [−640.312,−268.243] | −450.839 [−630.752,−270.925] | 6／26／0 |
| H−C | −520.251 [−698.775,−341.727] | −511.608 [−685.056,−338.160] | 3／29／0 |

F−H 的主要 J 增益来自 QoS +60.769，另有返航罚项约 +5.253、势函数 −.049；不是只靠返航
罚分减少。其 J 中位数只有 +3.968；世界 28、31 贡献约 51% 的有符号总增益，九个负世界
和六个完全同轨世界不删除。以上是固定程序在 32 外生世界上的描述性区间，不是独立训练
复制、等价检验或多重性校正的确认；J 和 QoS 共享分量，不能算两个独立证明。

F 在自身 **132,480** 个来源／时距记录上，10/20/30 平均误差 **.375/1.208/2.484m**，
对保持同一当前估计的 **21.654/43.130/64.450m**。每个世界／时距均值改善，但 2,008 个
记录更差，最大误差 183.928m，RMSE 9.507m；没有模糊、无绑定或未来截尾预测来源。
H/F 仍保留 6/7 次身份切换和各 8 个模糊当前点。准确性只覆盖其自身表示到的用户。

H/F 执行 **3027/3044** 个模型搜索轮和 **243276/242468** 个候选。F/H 在 26/32 世界
物理轨迹改变；六个同轨世界为 08、10、12、13、19、21，各自仍有 77–97 个模型轮，
并非规划器未执行。H−C/F−C 在全部 32 世界改变轨迹。

两个关键反例约束下一次解释：

- **29890021：** H/F 全 3000 步没有服务，30 名用户全部从未交付，无原生路由或直接 BS
  连接；各自执行 96 轮、6996 候选，所有**选中**候选在三个时刻都预测零 QoS。
  第一轮选当前位置、下一轮选 carried。C 使用同一个全程错误的推断 BS（约 1159.56m
  误差），却得到 1610.210 累计 QoS 和 4750 直接 BS 连接 UAV-step。不能归因于空搜索，
  也不能用所有选中方案都过度乐观预测正服务来解释；共同先验误差本身不足以解释差异。
  未声称所有未选候选也为零，未识别足以修复的改动。
- **29890012：** H/F 两名用户从未服务、3202 个储备不足 UAV-step、最低电量 .06894，
  最终八机全低于储备阈值；C 无从未服务用户、仅一个储备不足步、最终无低储备成员。
  此例已获得真实观测／记忆 BS，不能以全程 BS 未知排除。

F−C 平均最差用户累计 QoS 少 682.099，用户 p10 少 629.887；最长个体零交付间隔增加
681.5 tick [370.365,992.635]。F−H 的个体尾部改善未定。H/F 在所有世界少运动、少推进
耗能，仍明显少服务；这是有测量的取舍，不能称匹配服务下更高效率。全批 cutoff／耗尽
均为零，不建立安全或 H3000 以外持续性。世界 14、24 同时胜 H 和 C 的正例保留；没有
能提前合法识别这些世界的选择器。世界 31 最大 F−H 增益仍低于 C；世界 2 服务下降与
储备改善并存，不能用一个能源指标覆盖服务损失。

**本人的判断与独立复核一致：保留预测在该规划器内的用途，保留 C/P_BS 性能参照，
结束当前 H/F 完整包投入。** 可能的问题包括短时域内建立路线、候选／同分行为和不完整
用户表示，但未分离出唯一原因。B09 不追认 H1 是 B08 失败原因，更不支持“预测无用”或
“需要学习预测”的结论。原始 ResearchCritic 全文及独立检查范围见
[完整诊断](candidates/uav_fleet_transmission/NOTES.md#b09-original-result-critic)，
本人回应及 Root 另行采纳见[处置](candidates/uav_fleet_transmission/NOTES.md#b09-independent-disposition)。
`MATERIAL_DISSENT: no`；没有用一致意见替代实验复制。

### 已验证范围与实际完整成本

科学 worker／完整 reader 均结束，所有 96 个任务到 H3000 正常截断，无科学失败回合或替换
世界。reader 为 **VERIFIED / errors=[]**：全部 288000 原生步、288000 实际 proposal／feedback
及 **485744** 实际候选完整重建；38 个 launch-source 绑定及 26 个冻结依赖身份核对，
每个配对世界的全部 3001 边界用户路径一致。没有遗漏／未知／中断候选、未验证 rank 或
虚构未执行搜索。独立 critic 自己核对 96 回合与 126 组符号／均值归约、主要区间和源身份；
没有重跑每个远端 NPZ、控制器或独立原生 RF。原完整 reader 也不声称证明近似模型等于真实未来。

工程的独立 REF/C/H/F 四条 61-step 流共 **244** 原生步，C 与原参照逐项一致；该前缀没有
任何用户观测和候选，非空搜索正确性另由已计费的有限夹具与后续完整科学回放支持。
55 个不同有限检查通过，首次两个夹具预期错误及修正仍保留；没有把这两次失败隐藏为未执行。

| B09 支出范围 | 已付数量／测量 |
| --- | --- |
| 科学 native | 96 回合、288000 步、192 stream/probe 构造、96 reset、0 fit／标签／更新 |
| 科学执行＋完整回放 | 971488 候选预测、29144640 联合 nominal tick、2914464 RF／service 调用，128 私有模型 |
| 工程与有限检查 | 244 额外 native 步；检查另有 420 候选／独立 nominal 执行、12554 tick、1259 RF 尝试；总 153 个真实模型构造及一个模拟构造失败 |
| 科学完整 CPU／wall | 28774.227778 CPU s；9566.774583 wall s，4 个 worker 后接 2 个 reader，包含 reaped 子进程与父链计时 |
| 工程／有限检查／静态遥测 | 11.887242／21.96／.187309 CPU s；含前两项约 **8.002 CPU h**，静态遥测另计 |
| 内存 | worker／reader／parent 峰值 619936／652304／484704 KiB，各进程峰值不相加作同时峰值 |
| 科学原始证据 | 96 NPZ＋96 progress：906262386 logical／906805248 allocated bytes；ndarray 未压缩 6954552608 bytes |
| 工程原始证据 | 4 NPZ＋4 progress：789587 logical／811008 allocated bytes |
| 支持成本 | 源码／设计、实现、独立审查、准入、解释、发表和清理均另计且未完整计时；24–40 人时当量只是原预测，不能报为已测劳动 |

控制提案约 190 倍于 C 的 CPU 代价未计入 J。上述是占用节点下完整程序的已测成本，不是
孤立速度基准或物理实时保证。两个 reader 阶段均不增加 native 样本，0 fit 也不等于廉价。

本方向 B01–B09 的**已完成科学**总量为 **2800 回合、1317824 原生步、0 新 fit、
51975.807299 已记录 worker／full-reader CPU s（约 14.438h）**。各批依次为
160/48/48/48/416/1120/768/96/96 回合；不同宿主／计时边界只作已付成本相加。
工程、有限检查、支持与原始资产获得仍另计：B01 原资产等价检查 352 native 步，B02
含独立复核的正确性检查 2013 步，B03/B04 各 26 步，B08/B09 各 244 步；这些明确单列
合计至少 **2905 native 工程步**，并非完整所有检查的总计。B03 A01 在任何回合／native／
查询前失败，2.419563 wall s、CPU／RSS 未测。原始两份 H6/SET final45 的 run-fit 墙时
合计 158.146 分钟，不能把继承资产当成免费或本轮新增训练。至 B07 的另一条继承 S 链记录 8 fits、2 calibrations、
2277376 native 步／约 3584.279 CPU s，**与本表 B05–B07 重叠，不能整块再加**。
完整分批成本与限制在[本方向 NOTES](candidates/uav_fleet_transmission/NOTES.md#b09-final-cleanup)后的累计表。

### 精确证据、源码与保留位置

B09 冻结运行源 **`93166e7ac6cffa3c76da113afdc84e7317bb585c`**；原完整工程审查和修正前检查
均保留。完整原始收集／reader 发表 **`6da7fe816561ce42091dbf69518df559b2526608`**，
科学判读／原 critic／共享背景／计划退役发表 **`1ec491d983373bc630d5c476a0df89878d501f97`**，
实际清理及累计成本发表 **`b6abd917530275579a617b4331cc54dde240e634`**。

入口是[完整结果与全部 32 符号世界](candidates/uav_fleet_transmission/NOTES.md#b09-complete-reading)，
以及 [config](../../runs/uav_fleet_transmission/b09_service_prediction_a01/config.json)、
[summary](../../runs/uav_fleet_transmission/b09_service_prediction_a01/summary.json)、
[perworld](../../runs/uav_fleet_transmission/b09_service_prediction_a01/perworld.json)、
[reading](../../runs/uav_fleet_transmission/b09_service_prediction_a01/reading.json)、
[逐世界回放](../../runs/uav_fleet_transmission/b09_service_prediction_a01/reading_worlds.json)、
[静态遥测](../../runs/uav_fleet_transmission/b09_service_prediction_a01/telemetry_reading.json)、
[收集验证](../../runs/uav_fleet_transmission/b09_service_prediction_a01/collection.json)。
这些紧凑记录在 Git 中；完整候选／轨迹留一份必要原始数据，未复制到本地。

| B09 文件 | SHA-256 |
| --- | --- |
| config.json | `bfaaac99a3068158a5a2d63d3fe2629c48ebbfd8cdd025bcc69eef5e673c9beb` |
| manifest.json | `2c2f58b6c58de4281f54e911e2fe0dc6ce8f4b728b7353680c36c8e17e6afe8e` |
| summary.json | `382c9dfece3d6fe9d10fd9134aa0c4d40d9148d54cec5078af63886cfc60ced2` |
| reading.json | `be5173390e9c9632adc3603ad240daebdb6b89f076eb2388900c690b90a3d909` |
| reading_worlds.json | `48b83e463b662c61ee3b12dd2a7bbe0771ce2f2de2d62e59d226f7556222eda3` |
| telemetry_reading.json | `37ea61c3c404b2829fb35aa17723dd12d3d6028d356e549790e5524302727fcd` |

科学唯一大数据位置：`wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_transmission/b09_service_prediction_a01/raw/`；
工程在同父目录 `b09_service_prediction_engineering_a01/raw/`。manifest 逐文件记录 hash／大小；
全部原始记录已流式 SHA256／size 核验，清理后数量、分配大小和重要汇总 hash 仍一致。
工程 manifest SHA256 为 `9f63cd910fa7d95593d0cc87e9452c4d9660ae9016e2610a644a933ffd2e81d0`。

历史入口与源身份如下；所有原始能力、反例和技术失败保持原样：

| 批次／run tag（均在 runs/uav_fleet_transmission/） | 冻结源 | 唯一必要 bulk 位置 |
| --- | --- | --- |
| b01_native_s1_a01 | `a2f62e613a12331ad380876a6c764f8a46a893ee` | 本地 `/home/fires/hmasd-artifacts/uav_fleet_transmission/b01_native_s1_a01/raw/`，run 下为指向它的链接 |
| b02_silent_repositioning_a01 | `9928d34b54628baaa542961debb65c5ce7ef0f23` | 同本地 artifact 父目录、对应 tag/raw/ |
| b03_complete_continuation_a02 | `02e8c1adc5a625037490facc6388e4b8bc9fd74e` | 同本地 artifact 父目录、对应 tag/raw/；A01 失败记录另外保留 |
| b04_temporal_complementarity_a01 | `239360b03f5d7acf788bd9ae5d4dccbde4f9237e` | 同本地 artifact 父目录，对应 raw/ 和完整 reading.json；Git 为 reading-summary.json，保留既有跨方向消费者 |
| b05_score_sampling_a01 | `54c57af8d2e3860f25a278850055a6aa020e5beb` | wsl_4070 `/home/wu/projects/HMASD/runs/uav_fleet_transmission/b05_score_sampling_a01/raw/` |
| b06_cadence_a01 | `df149ac620a90931d81fac727fe91a898b9ab760` | 本地共享主工作区 `runs/uav_fleet_transmission/b06_cadence_a01/raw/`，1120 文件 |
| b07_joint_renewal_a01 | `2261ccb709b8f5d166902a602f9c7ba33d510e8a` | 本地共享主工作区 `runs/uav_fleet_transmission/b07_joint_renewal_a01/raw/`，768 文件 |
| b08_anonymous_memory_a01 | `94f08627050b7d495b4c9e9af18db02ab17a5c1e` | wsl_4070 同 runs 父目录、对应 tag/raw/；工程对应 `_engineering_a01/raw/` |

B04 完整 reading SHA256 为 `c9eaac15e69d1195e73710e4b071b5c196402bc6811b3a0bac333c771fd39363`；
B08 reading 为 `303a7b6abaab626b2fddd22d168f0e9687aa0b40c84f7908e3b902175e223020`。
其余每批的 config／manifest／summary／reading 与 NOTES 保留完整内容身份；恢复某题时读其
原卡与直接绑定输入，不从这个表构造替代合同或作递归历史预加载。

### 实际清理、保留代码与操作终态

[测量与逐目标清单](candidates/uav_fleet_transmission/NOTES.md#b09-final-cleanup)记录本轮 B09
净释放 **1641795584 allocated bytes**，不是整台机器的空闲空间变化，也不是 Git 对象回收。
实际已删除：

- 工程源快照 `4c59c5f284bc4057ba2a0db7ff541fd8`，已测 818995200 bytes；登记也已不存在，
  未额外虚计未单列的登记大小。
- 科学源快照 `643469c7928a44aa8bd0bb6bee5b0d6e` 及 `.git/worktrees/` 同 ID 登记，
  分别 818991104／3670016 bytes。
- 本地 B09 `capture.py`、`metrics.py`、`reader.py`、`run.py`、`study.py` 和镜像
  `test_reader.py`，共 126976 bytes；停止的两个 observer 请求及其目录 12288 bytes。
- 两份本地空日志已删除，释放 0 bytes；原远端日志及必要正反证据仍保留。

总计远端／本地已测目标真实消失；没有备份包、第二份 raw、另一个 authoring checkout 或
清理遗留阻碍。普通进程扫描遇到受保护 `/proc/660/cwd`，工具已有的只读
`--sudo-process-scan` 解决后才完成精确目标删除，不是绕过执行拒绝。

当前 main 保留 B09 的六个有用 Python 模块 `__init__/contract/controller/model/nominal/trace`、
`frozen_sources.json` 及两个 controller/model 测试文件；八个 Python 文件逐字节等于运行源，
静态语法／相对 import 闭合检查通过，没有新增 runtime／model／native 测试。B08 tracker/controller
和其规则测试、B05–B07 有用包及旧 B04/N8 消费者都保留。废弃运行／reader 驱动从当前树退役，
准确历史源码仍在[运行提交](https://github.com/CartmanFatass/My-paper-code/tree/93166e7ac6cffa3c76da113afdc84e7317bb585c/experiments/candidates/uav_fleet_transmission/b09_service_prediction)；
不能直接对当前 main 重跑已退役入口，也不能把需要重建历史源码误写为丢失结果。

原科学操作为远端 `.git/hmasd-admission/ec1d59fe992e79d1bbebfdc6ec7486df245b40a75f0bdf2f0a78941b6dc3a157.json`，
源仍为93166e7ac；exit0 的 finished epoch 为1790854551.1702433。最新清理后状态继续确认
runner1231375／supervisor1231374 不存在，记录一致。observer generation40 已停止、daemon2146440
不存在、所有23事件已消费、无待交付 wake；原生 child 的 App queue −32600 限制没有导致丢失
收集，本 DM 全程保持活动并直接读到结束。**不要重启、重发或迁移这些已完成句柄。**

### 下一步的选择边界

当前没有选定追加世界、原样复制、跟踪／horizon／guard／search 调参、学习器或确认。
本轮三份已经完成的后续资料评估属于另外三位 DM；这里**没有第四份完成评估**。
critic 提到的“在短模型给出零服务时保留普通路线建立行为，再在可服务时利用预测”只是一条
**UNSELECTED、尚未报价**的后续构想，源码可行性和总代价未决。它不是已诊断修复，也不在交接后自动实施。

若 owner 以后明确继续、Root 再选择本题，先明确要改变什么判断：只问完整包用途可比较
C 与新包；若还要宣称预测增量，则需匹配的新 H/F 加 C。二者都改善而 F 无增量会支持普通
控制改进；F 另有收益且新包超过 C 才支持新的预测组合；继续完整损失则削弱该路线。
这些只是可区分结果的结构，不是已固定实验或成本承诺。任何更丰富信息权利应同样提供给
有能力的普通参照并计入获得代价。另一轮准确率成功本身不改变采用判断。

现在完成交接并停止，无外部 producer、未读结果或等待审批的实验。Root 下一步只需整合本文件
总览和停止状态；研究再进入条件是 owner 明确继续及后续实际选择。
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

**本节由 `/root/dm_parent_adaptation` 本人于 2026-10-01 UTC 撰写。**
`uav_parent_adaptation` B01–B09、其后的低运动方案评估，以及
`uav_radio_information_cost` B01 均已完成判读、独立科学审阅、发表和清理。
两个方向均为 reserve。本轮 RF 后续方案的源码／完整成本评估和真正的 Astra Max
独立评估也已结束；没有运行中的 worker、reader、observer、未读结果、待收意见或
已选后继。Owner 要求完成本轮交接后停止，以下候选不构成恢复或执行授权。

### 研究连续性：保留能力，同时保留失败限定

父方向的持续问题是：经验能否发展或保留有用的完整 UAV 控制能力，并降低实际决策
成本？它经过了局部校准／发展、联合采样、与无线管理组合、规划摊销及实际 S2 内发展。
当前 RF 信息问题是：把测量、报告、交付和计算都计入后，购买当前信道状态是否改善
完整控制？这两个问题的开放性不等于任何旧配方可以自动续跑。

下表保留各研究最影响下一次选择的正反证据；每行链接均通向完整结果、所有反例、
原独立意见和 DM 处置。固定资产上的新世界不是新的训练重复，区间跨零也不是等价。
在后期离散控制比较中，C 是普通局部控制器，Q 是围绕 C 的普通随机分布，S 是已付费
获得的冻结学生；S2/T2 是有明确报告、交付及承诺时钟的管理器，不能与全开合同混用。

| 父研究 | 已保留能力与不能抹去的反例 | 本次关闭范围 |
| --- | --- | --- |
| [B01：三个未经筛选的父策略](candidates/uav_parent_adaptation/NOTES.md#b01-complete-reading) | K、D 都提高各自父策略 P 的所测均值；D−K 等权 J 为 +.001452，区间跨零。父策略生成在两条谱系损失服务；D1/world1 相对 P 新增 78 个零服务 tick，而另一世界消除 51 个。 | 有限上下文发展相对普通校准的额外价值未确定；不能以小的同历史动作幅度保证闭环服务。 |
| [B02：普通全策略继续训练 U](candidates/uav_parent_adaptation/NOTES.md#b02-complete-reading) | U3−P3 的 J +.053578、服务 +3.338379/tick，零服务 tick 233→1；另外两条 U 谱系均值恶化，U2 一个新世界增加 85 个零服务 tick，其中连续 76 个。 | 保留 U3 与所有不良端点；没有默认继续训练、冻结优越性或父质量因果结论。 |
| [B03：普通 C 初始化及学习](candidates/uav_parent_adaptation/NOTES.md#b03-complete-reading) | 零 fit 的 I−C 为 J +.023721、服务 +1.709106；代价是路径约 +1651 m/UAV、回合内服务 p10 下降。实际采样学习 Ls−I 为 −.077879 J，96 世界中 93 个下降；表、网络和评论家均真实更新。 | 未激活或只看贪心端点不能解释损失；保留 I/C，未来学习必须面对强普通随机参照。 |
| [B04：固定边缘分布的联合采样](candidates/uav_parent_adaptation/NOTES.md#b04-complete-reading) | 主比较 S_A−S_I 为 −.002998 J，预定点预测失败，物理干预真实存在。独立次级正例 S_I−Q_I 为 +.024075 J、服务 +1.767029、p10 +3.546875、路径 −1232 m/UAV；仍有单世界 J −.100149、p10 −9.25 的损失。 | 关闭固定 A/B 耦合配方；保留 S 的有条件资产能力，不把三个相关采样视图算作三次训练复现。 |
| [B05：学生与无线管理组合](candidates/uav_parent_adaptation/NOTES.md#b05-complete-reading) | 全开 S 的优势复现，但 S_S2−C_S2 为 −.004497 J、区间跨零；对 C_T2 为 −.010311 J、服务 −.915955/tick。S 保留较短路径；普通 C_S2/C_T2 的强能力及 C_E 的低成本取舍保留。 | 原有优势不简单相加；没有识别具体的学习／遮蔽原因，也不自动要求奖励训练修复。 |
| [B06：固定学习排序器摊销延续价值](candidates/uav_parent_adaptation/NOTES.md#b06-complete-reading) | L−R 为 +.004071640 J、区间跨零，正均值集中于一个大收益世界；仅保留 T_E−R 所测增量的 44.23%，低于预定 75% 点目标，但通过计算成本部分。普通 T_E−R/K2_E−R 为 +.009206103/+.003741182 J，区间均正。 | 保留廉价 L 的局部正例、普通规划与精确复用；更低预测误差不等于保留大部分决策价值。 |
| [B07：学习排序器只分配两个精确分支](candidates/uav_parent_adaptation/NOTES.md#b07-complete-reading) | 相近分支预算下未建立 L2_E 超过普通 K2_E 的均值增量；一个有用选择和尾部优势保留。K2_E/T_E 对 R 的 J +.004478/+.005398；全部 168 个模型分支发生精确递归。 | 关闭此固定排序器购买；不自动追加标签、重拟合或新面板。 |
| [B08：G2/A2 精确计算复用](candidates/uav_parent_adaptation/NOTES.md#b08-complete-reading) | 64 条旧 H500 历史／1400 个片段证书均保持原程序；G2/A2 的 worker+reader CPU 分别降至原版 46.11%/45.65%。优化后 A2 仍为 G2 的 2.888 倍；旧 J 增量 +.001706077、路径 +42.947 m/UAV、质量下降及一个服务损失世界原样保留。 | 是普通计算能力，不是新原生结果或学习收益；记录了同时运行的其他负载，不声称隔离测时或可移植时延保证。 |
| [B09：实际 S2 内 CAL/CONT 发展](candidates/uav_parent_adaptation/NOTES.md#b09-complete-reading) | CONT−CAL J +.000094 [−.005340,+.005528]；CONT−S −.000550 [−.005529,+.004429]。两者真实更新，CONT 改变全部 64 条配对终点评估历史；路径分别短 555/596 m/UAV，均在 27/32 世界更短。C_S2 相对 CONT 的 J +.006204、服务 +.611816，完整 CPU 相近而路径更长；原 S−Q 的 J +.006528 再现。 | 保留 CONT 的条件低运动能力及全部服务损失／启动中断；不建立服务保持、能耗节省、上下文必要性或新的默认策略。A01 技术失败的两步证据单独保留。 |

B09 的 CAL、CONT 各只有一个训练实例，最终是 32 世界簇内平均两条动作 tape。
其最差 CONT−CAL/S 世界均值 J −.037965，单 tape 服务约 −6.99/tick；较少路径不能
消去这些损失。[独立原意见与处置](candidates/uav_parent_adaptation/NOTES.md#b09-independent-disposition)
已接受关闭原样发展程序。随后只作过一次普通 `0.9 p_S + 0.1 δ_STAY` 的完整源码定价；
Root 已明确不购买该低运动面板、校准、复现或 B09 修复。原因是当时的相对信息价值和
机会成本，**不是所有探索都必须先有部署价格／服务阈值**。
[完整原始往来和单独采用决定](candidates/uav_parent_adaptation/NOTES.md#post-b09-source-allocation-closeout)。

### RF 信息成本 B01：完整负结果与仍保留的正面取舍

冻结源码为 `a80e2be9e3341b3bebfa743dacfda5e4ff13d977`：32 个配对世界，
N5/U50/H256，P_FULL 与 P_PRIOR 使用相同已知移动相关信道规律和普通期望功率规划。
FULL 每轮买 250 个当前链路测量，付 0.1 秒探测及 391 字节、三 tick 交付；
PRIOR 无中央 CSI 探测／码字，付 141 字节、两 tick 交付，仍使用合法的局部 C
观测、提案和导航信息。它是强普通参照，并非利用所有间接信息的最优后验。

完整 payload-J 的 FULL−PRIOR 为 **−.015929914563
[−.019169457985,−.012690371141]**，32/32 世界负，其中一例接近零。
payload 服务 −.994324/tick、原始服务 −.301147/tick，平均路径多 783.740 m/UAV。
FULL 的等待证据有条件地保留：平均年龄在 24 个世界改善，但总均差 −.057305 的
区间跨零；最差用户平均年龄在 20 个世界改善，区间亦跨零。两者都有严重个体尾部：
PRIOR/world29651010/user45 的终端右删失间隔 203，FULL/world29651029/user31 为 150。
没有全队零服务或从未服务用户，不等于个体连续性良好。

全部 4096 轮按时，两个程序广泛改变实际命令／mask。完整独立 reader 重建物理状态、
全部实际候选、两次 C 信息核验及全部用户结果；独立 ResearchCritic 接受关闭固定
FULL 购买并保留 PRIOR 和 FULL 的局部等待正例。合同允许任一效应符号，因此这是
**预定问题的负结果分支**，不是事后声称某个从未承诺的正向预测已被推翻。
时延、测量、payload 和路径共同变化，不能把损失单独归于 CSI 老化或任一组件。
[完整观察](candidates/uav_radio_information_cost/NOTES.md#b01-complete-reading)、
[原独立判读与回应](candidates/uav_radio_information_cost/NOTES.md#b01-independent-disposition)。

### 完整投入与可恢复证据

以下为各原记录的实际计量；CPU 口径在早期研究间并不完全一致，不能当作同一计时器的
性能排行。固定检查、重读和失败额外成本按下文保留；工程、文献、意见、迁移和发表支持
未被完整计量。其他方向的原始 S、标签和强参照获取也不是免费，不能把重叠累计账再次相加。

| 研究 | 新完成 fit | 新原生 team steps | 原记录的 measured CPU 秒 |
| --- | ---: | ---: | ---: |
| 父 B01 | 12 | 1671168 | 2280.176845，含三次完整 reader 尝试 |
| 父 B02 | 3 | 491520 | 855.845039 |
| 父 B03 | 3 | 491520 | 590.256484 |
| 父 B04 | 0 | 106496 | 115.438290 |
| 父 B05 | 0 | 131072 | 1902.346056492 |
| 父 B06 | 1 | 32000 | 1529.662480；另有 2.200606 检查及 2.020257 已存输入审计 |
| 父 B07 | 0 | 32000 | 1684.564490 |
| 父 B08 | 0 | 0 | 4827.801616813，完整旧历史 replay→reader |
| 父 B09 A02 | 2 | 262144 | 4814.172477586，worker+完整 reader |
| RF 信息 B01，含 H8／固定检查 | 0 | 16400 | 430.588630 own CPU；另 .010114 waited-child |

B09 A01 另有 **1 个失败启动的 fit、2 个原生步、0 更新**：worker
2.337792371 CPU 秒及有界失败 reader 1.675545 秒，属于掩蔽观测 factory 的已修复
技术错误，不作为有效负科学结果。父方向累计为 **21 个完成 fit，加该失败启动；
3217922 个原生步**。原记录按各历史范围累加的主测量为 18602.60157077 CPU 秒，
失败 reader、支持和继承获取另列。RF B01 在此之外增加 66 回合／16400 步；没有 fit。

原始配置、源绑定、所有世界／用户读数与必要哈希由以下记录恢复，摘要不会替代唯一原件：

| 证据 | 精确位置与保留范围 |
| --- | --- |
| 父 B01–B04 | `wsl_4070:/home/wu/projects/HMASD/runs/uav_parent_adaptation/` 下的 `b01_unscreened_a01/`、`b02_full_continuation_a01/`、`b03_c_prior_a01/`、`b04_joint_sampling_a01/`；原轨迹、端点／更新流及完整 reader 的单份规范副本。各研究 NOTES 记录文件清单和 SHA。 |
| 父 B05 | 本地 [b05_radio_composition_a01](../../runs/uav_parent_adaptation/b05_radio_composition_a01/)；512 个原始 raw 文件共 231301715 字节，完整 summary／reading 和输入绑定保留。 |
| 父 B06/B07 | `/home/fires/hmasd-artifacts/uav_parent_adaptation/b06_continuation_amortization_a01/` 与 `b07_shortlist_amortization_a01/`；原 runs 的 raw／summary 是指向同一份原件的符号链接。B06 为 446 个 raw 文件加原 summary；B07 为 528 个 raw 文件加 summary，共 90731614 字节。训练排序器及标签的精确绑定在 [B06 config](../../runs/uav_parent_adaptation/b06_continuation_amortization_a01/config.json)，不可换成新拟合。 |
| 父 B08 | `/home/fires/hmasd-artifacts/uav_parent_adaptation/b08_exact_planning_reuse_a01/`，129 个必要文件／8953742 字节；[result](../../runs/uav_parent_adaptation/b08_exact_planning_reuse_a01/result.json) 给出全部身份。原 N8 物理证据仍在 `/home/fires/hmasd-artifacts/uav_fleet_transmission/b04_temporal_complementarity_a01/`。B08 重复容器已删除，原 reader 如需重跑须按记录重建容器，不能声称所有旧 raw 仍在。 |
| 父 B09 | 本地 [A02](../../runs/uav_parent_adaptation/b09_managed_development_a02/) 保留 1550 个原始文件／744998114 字节，含全部训练、端点和更新原件；[result](../../runs/uav_parent_adaptation/b09_managed_development_a02/result.json) 是紧凑完整读数入口。A01 同级失败目录保留 14 个原件／792482 字节。[最终源码](../../experiments/candidates/uav_parent_adaptation/b09_managed_development/) 绑定 `8e5659881dc1f3e8419f9c406cabdf07abe1a5a1`；结果发表 `753fab32e2b74b4bfaa0dd841423d6580aedb879`。 |
| RF 信息 B01 | 唯一大体积原件在 `wsl_4070:/home/wu/projects/HMASD/runs/uav_radio_information_cost/`，包含主面板、H8 与 reader；134 个必要 NPZ／151033826 逻辑字节，整个规范树 152395776 allocated bytes。Git 保留 [主 summary](../../runs/uav_radio_information_cost/b01_pilot_package_a01/summary.json)、[完整 reader](../../runs/uav_radio_information_cost/b01_pilot_package_read_a01/reading.json)、config、状态和全部紧凑证据，结果提交 `4ec3dd759f481da2e0caa7205d7f51d321432125`，关闭提交 `0052b7dd5de658ac24b911a3ca9847a5602d632f`。 |

RF 主 summary 的 SHA256 是 `d16d488a384a339f0374f95c8b67a3a3b4689cee58833464e5720f0ab2e8783a`，
reader 是 `e5dec257f082b98ff726eec87408d592cd6f1ea7d4f7336cf2c0e7e2bf614409`。
已有 useful 源码／tests、固定资产和不良端点均保留；没有为交接复制原始数据或建立备份链。

### 已完成清理与操作终态

各关闭时均先释放 worker／reader／独立审阅消费者，再验证单份规范证据，最后删除
已无消费者的接受快照、重复数据和 scratch。以下是较近几次关闭的**已测量**回收，
不是本次写交接再次回收，也不能再加入 Root 的本轮三项清理总数：

| 关闭 | 实际删除的主要目标 | 已记录净 allocated bytes 下降 |
| --- | --- | ---: |
| [父 B07](candidates/uav_parent_adaptation/NOTES.md#b07-final-cleanup) | 快照 `c110bfbadd8241c6920763a323e1ea25` 及注册项、所列 code/test caches、已停 observer 请求；原件只移动一次 | 1739776000 |
| [父 B08](candidates/uav_parent_adaptation/NOTES.md#b08-final-cleanup) | 快照 `c060d43367b841d2b1852d9aefd4b26a`、2902 个重复 raw 文件、64 个重复历史摘要及 caches/temp；129 个独有文件保留 | 2137665536 |
| [父 B09](candidates/uav_parent_adaptation/NOTES.md#b09-final-cleanup) | 远端快照 `5da2b2e3d044498fae1c794f8479971c`、`f1ddd48003da40fb90b15ae9222a48bf`，已经验证迁至本地的远端重复 raw/assets/updates/大摘要，消耗后的输入暂存和本地 B09 temp | 1634500608，已扣新规范副本增长；另 225280 cache bytes 单列 |
| [RF 信息 B01](candidates/uav_radio_information_cost/NOTES.md#b01-final-cleanup) | 远端快照 `f7b4ac15bb384229a7eb888003b49595`、`a6c37c7d307f42dfb91cdf24b5b79a5e`、`4817eb50f066476785ddbfb5da300032`，以及本地 `temp/directions/uav_radio_information_cost/` 的停机 observer 请求 | 2455994368 |

上述目标在各自关闭时均已验证不存在；更早 B01–B06 的实际目标与净数见其清理条目。
没有清理工具阻塞。父 B09 原 worker→reader 已 exit0，观察事件清空并停止；RF B01
worker 和 reader 均 exit0，最后 observer generation48 停止、events 为空、wake 为 null。
两个方向没有活跃实验或遗留观察义务。后续 source／意见保存没有创建科学操作或新的
可删除 scratch；没有待完成的模型训练、转移、Pro 请求或隐含重试。

### 唯一已定价 RF 选项：U32_FULL 对 P_PRIOR，尚未选定

这是完整付费程序的直接比较：已证明有条件增量的 U32 加上它的全部 CSI 购买合同，
是否超过廉价 P_PRIOR？另一方向的 U32−P 为 +.007529588 J，同时年龄／间隔恶化；
本方向 P_FULL−P_PRIOR 为负。**不能相加减两块独立面板得到新效应。**
任务贡献可以是完整用途与经验边界，无需假装是新学习方法、纯信息因果效应或实地验证。

意见来源必须正确恢复：`/root/age_control_interface` 的早期无购买建议和更新建议，
实际均来自原 **Luna/medium Scout**；Root 后来的 “Astra Max Oracle” 标签错误已改正。
[两份完整原建议、旧的 P/U 尚未返回前提及来源更正](candidates/uav_radio_information_cost/NOTES.md#b02-original-opportunity-advice)
均原样保留，不作为真正的 Astra 独立科学审阅。随后 Root 以注册
`hmasd-research-critic` 角色委派 `/root/oracle_rf_integrated`，核对实际 Astra/max。
其**完整 15655 字符原意见、我的单独回应及 Root 处置**已发表于
[42b0fe1d8：完整独立评估](https://github.com/CartmanFatass/My-paper-code/blob/42b0fe1d8a5cf9645455dbce9e9705b4e6c41959/docs/research/candidates/uav_radio_information_cost/NOTES.md#b02-original-independent-selection-review)。

真正的独立结论是：保留这一项为值得考虑、但**未选定**的后续选项，
`MATERIAL_DISSENT: no`；定性预期偏向 PRIOR 仍占优，但不是跨面板相减或数值后验。
有利结果会建立此总体目标下的完整付费参照，同时保留等待损失；不利或不确定结果结束
这一次固定购买而不自动扩展。技术失败不能改写为活跃干预的负结果。最强停止理由是
短时、近似 host 上的窄结论可能不值得 6–12 小时支持投入；该评估没有比较其他候选的
完整最终价格，因而不声称跨项目优先级。我的回应接受这个有范围的经验问题；Root 仅
保留建议供后续分配，**没有选它执行**。

原文及独立评估保留了实际三库、July／外审和主论文阅读覆盖。两项来源勘误也应继承：
Jagannathan MIT PDF 首三页印刷页码为 491–493，不是 136–138；MARL-0451 是
**Shi 等关于一般和（general-sum）鲁棒 Markov 博弈**，不是 Zhao／仅零和论文。旧 helper 文本
没有被覆盖。这些论文只支持信息权利、成本和转移限制；目录漏检不证明新颖性，
3.5 GHz 校园拟合／二维水平相关标准也不校准当前 2 GHz、三维路径增量、悬停残差冻结的 host。

完整原始源码账与接口说明见
[source-only 全文](candidates/uav_radio_information_cost/NOTES.md#b02-integrated-package-source-only)；
它已获上述独立评估认可，不需要为交接再请求一次成本或性能试点。

| 若以后选定才实施的固定内容 | 完整范围／条件价格 |
| --- | --- |
| 程序与接口 | 外部标签 U32_FULL、内部保持 RF 协议 V5 的字面 `U32`，源码 `9b6f493b343c2939b374a1ce21384266d3257456`；PRIOR 保持协议 V6 的 `P_PRIOR`，源码 `a80e2be9e3341b3bebfa743dacfda5e4ff13d977`。复用两套现有 per-episode collector／独立 reader，新增本方向调度、源绑定、配对聚合和 reader 编排；不改冻结全局 ARMS/WORLDS 或包内身份。C 输入是 104 维观测，不是“104 米”模型。 |
| 原生暴露 | 世界 29661000–29661031，32 个配对 H256、轮换顺序；另一个配对 H8 集成 fixture。共 **66 回合、16400 team steps、0 fit／更新**；主 constructor29661999，H8 world29661900、constructor29661998。这些值只是已查未用的候选输入，尚未发表执行合同。 |
| 控制／信息权利 | U32 每报告 250 测量、0.1 秒探测、391 B、三 tick 交付、1.336 秒计算余量；PRIOR 141 B、两 tick、1.436 秒余量、无中央 CSI。原 27 命令、31 非空 mask、S2 两顺序搜索保留。配对初始几何和物理创新地址，路径不同后不要求真实残差相同。 |
| 读数 | 全 32 世界完整 payload-J/256 的配对均值及 mean±1.96SE、每个符号和两臂水平；原始／payload 服务与质量、50 用户年龄／间隔／删失、启动与末尾、路径／发射暴露、命令／mask、计时／fallback 和完整资源同行保留。1600 用户对不是1600独立实验单位。 |
| worker＋完整 reader | **61500 次 C 调用**、1660500 条 C 路径、6642000 模型 tick、至多138990000 C 链路评估；**30479724–59889984 次候选 fleet score**、7619931000–14972496000 个稠密评分条目。reader 重建全部实际候选与部分完成工作、物理和两遍 C 信息核验；自身新增 native step 为0，计算不免费。 |
| RNG 与测量账 | 两侧共114800000个 base-normal materializations、229600000个带符号粒子值；每侧4117000个物理正态、7820个几何 uniform、20568个 radio／SINR／grant 状态。真实购买512500链路测量、102500探测槽／205模拟秒、1090600循环wire bytes＋26400 map bytes；reader不再购买一次测量。 |
| 正确性与实现 | 恰好两回合 H8 及其完整 reader 已计入上账；最多8个新增纯数据编排用例不增加科学查询。继承已完成核心数值／时钟检查，新增身份／输入／编排需独立工程审阅。存在真实新缺陷时另作前瞻成本判断，不能把任意追加修复藏在此价格内。 |
| CPU／内存 | 总计约 **0.7–1.5 CPU-hour**：主 worker5–12分钟、完整 reader35–75分钟、集成检查.01–.05小时；顺序单进程峰值约 **0.5–1.5 GiB**。依据是已有 RF 完整 reader 的实测，不能用两种廉价 P 的430秒总账给 U32 完整 reader 定价。不是新 benchmark 或时限保证。 |
| 存储／支持 | 单份规范证据约 **0.15–0.35 GB**；先清 fixture 快照时远端峰值约2–3GB，否则3–4GB；原本地拓扑约4–5GB。源码／编排／reader／检查／工程及科学阅读／发表／清理约 **6–12 focused support-hour equivalents**，为前瞻估算而非实测人工／模型工时。尚未做新的实际节点和磁盘准入检查。 |

若以后选定，拟用 `experiments/candidates/uav_radio_information_cost/b02_integrated_package/`
及对应 tests、`runs/uav_radio_information_cost/b02_integrated_package_a01`、read/check tags
和本方向 temp；这些只是路径提案，没有实现或启动。已有 RF 全价 worker+reader
3154.216731 CPU 秒、含固定检查3166.677581秒是另一已完成研究的历史实测，保留为
价格锚点，不能计成这项候选已发生的成本。当前源码／文献／意见支持确已发生且未完整计量，
其“0 查询”也不能被误读成未来模型／allocator 不收费。

### 交接停止与恢复条件

到本节提交，当前分配给我的结果、源码评估和两类意见保存均已完成；没有需要接着
收集的科学操作。先等待 owner 明确继续，再由 Root 比较机会成本、选择具体问题；
不能仅凭本候选有完整价格和独立支持就创建 run。若选 RF 候选，再核对最新
RESEARCH 的 owner pause／lead，复用仍适用的完整科学审阅，写前瞻合同和 L0，完成
新增编排的工程审阅，发表精确输入，再按实际节点准入；不重启任何已结束的旧句柄。
如果问题或关键比较发生实质变化，应重新作针对性科学选择，而非沿用标签自动放行。
父 B09／低运动和其余旧配方的停止范围仍生效，正面资产和不良证据同时继承。
本会话若尚未归档可按现有路由继续；owner 若已归档，则新 DM 从上述规范证据接续。
<!-- DM_PARENT_ADAPTATION_END -->

<!-- DM_USER_WAITING_BEGIN -->
## DM：用户等待、无线不确定性与后续策略发展候选

本人为同一未归档 native DM `/root/dm_user_waiting`。先前负责 `uav_user_waiting`
B01–B07，随后由 Root 明确分配 `uav_radio_uncertainty` B01；两条结果线现均已完整
读出、独立判读、发表并收尾，处于 reserve。研究问题从“怎样改善个人等待且保留
服务”延续到“对共同获得的无线测量，联合不确定性积分是否有完整控制价值”。
后者没有被用来解释前者的确定性宿主失败。最新策略发展工作只是 Root 分配的
资料和完整计价评估，**未实现、未选定、未启动**。本节完成后遵守 owner 交接停止边界。

### 等待研究留下的能力与负面约束

这些研究区分最差用户的平均年龄、平均用户的最长间隔、全回合最大间隔和总服务。
它们不能互相替代。B01–B04 各有完整配对世界；B05–B07 复用 B04 的 64 个已曝光
开发世界，不能称为新世界确认。表中的差值均按所写顺序，等待指标越小越好。

| 研究与完整证据 | 保留的结果 | 必须一起保留的限制 |
| --- | --- | --- |
| [B01 累积负担 R](../../runs/uav_user_waiting/b01_burden_a01/result.json) | R−O 最差用户平均年龄 −1.889343，描述性区间 [−3.013856,−.764831]；服务 +2.873962、J +.038074，后两项 64 世界均正 | 平均用户最大间隔 +3.387500、年龄 p95 +2.499219。时间平均负担改善没有保护连续等待；相对 W/M 仍付服务代价 |
| [B02 连续性 A/S](../../runs/uav_user_waiting/b02_continuity_a03/result.json) | 普通 S−M 回合最大间隔 −8.953125、最差用户平均年龄 −3.078491，并有较低调度成本 | A−M 主指标“平均用户最大间隔” +.628750，区间跨零；A 的延伸预测未挣回指定用途。S−M 服务 −3.662537、J 在 64 世界均负；98 tick 闭合间隔反例的年龄和累积负担在全部锚点都正确 |
| [B03 剩余中断价值 LR/LN](../../runs/uav_user_waiting/b03_value_a01/result.json) | 已训练、已进入决策的负面结果；普通 S 的部分极端尾部优势仍保留 | LN−M 平均用户最大间隔 +11.902813，64 世界全差；LN−G0 +8.317188，59 差/5 好。不是未训练或未激活，也不能据此归因于缺 ACK、历史或某一个优化器 |
| [B04 扩展搜索 U、局部服务底线 K](../../runs/uav_user_waiting/b04_service_floor_a01/result.json) | U−S 服务 +.486389、最差用户平均年龄 −1.599670、J +.005405；这是有用普通能力 | 最大间隔增量尚不确定，计算/质量仍有代价。K 的模型服务底线每次成立，K−M 的服务 −.036499、最大间隔 −2.562500 和最差平均年龄 −1.018494 区间却均跨零，未通过完整服务保留的固定联合判读 |
| [B05 同路径本地分配 RR/LRS](../../runs/uav_user_waiting/b05_local_allocation_a02/result.json) | LRS 在 M/S/U 三条物理路径上逐 tick 保留联系总数，三种路径各 64 世界的最差用户平均年龄全改善；均值差 −3.857300/−4.676819/−3.554871 | 每条路径的质量和 J 均在全部世界下降；重分配不能创造本不存在的物理联系。路径与分配的权利不同于旧冻结合同 |
| [B06 将实际 LRS 纳入普通 S_F 规划](../../runs/uav_user_waiting/b06_fair_model_a01/result.json) | S_F:LRS 最大间隔 12.156250；S_F−S 为 −22.937500 [−25.663278,−20.211722]，64 世界全好，闭合间隔也全好；每回合服务全部用户且无零服务 tick | 服务 −4.234070，63 世界下降；J −.039678，62 世界下降。保留极端连续性能力及真实服务价格，不称为无损升级 |
| [B07 便宜 C2:LRS](../../runs/uav_user_waiting/b07_cap_two_a02/result.json) | 相对 S_F，服务 +2.999878、J +.040663，分别 59/61 世界改善，模型搜索明显更少 | 最大间隔 +80.328125 [67.767168,92.889082]，64 世界全差；C2 平均最大间隔 92.484375。最长无联系区间平均 89.890625，同路径换分配几乎没有补救空间。29426031/user1 仅获一次服务，随后 [5,256) 为右删失 251 tick 间隔，其中 250 tick 无联系 |

七次完整独立判读均保留这些正面、负面和不同用途，不把“所有用户最终被服务”
当连续性保证。C2 的全回合平均开启数 2.0234375 还高于 S_F 的 1.765625，
所以 B07 也不是单独识别“较低平均并发”的因果实验。原样 C2 连续性替代和其后
较长规划器提案已停止；后者是投入判断，非长规划或合法未来 C 模型的经验反证。
完整原始审查、DM 决议、失败与后续不购买理由在
[等待 NOTES](candidates/uav_user_waiting/NOTES.md#b07-independent-review-and-disposition)及
[后续原始往来](candidates/uav_user_waiting/NOTES.md#post-b07-original-continuity-advice)。

较早成本不因 RF 转向而归零。以下是各记录已发表的主要科学曝光及 worker/reader
CPU；计时范围、节点和核验深度不同，不能当同质性能基准，正确性、失败及未计量
支持费用另见各次 Complete cost：

| 等待研究 | 新科学曝光 | 已记录 worker/reader CPU 秒 |
| --- | --- | ---: |
| B01 | 256 回合 /65,536 步，0 fit | 1,824.068 |
| B02 | 完整面板 65,536 步，另保留失败前缀，0 fit | 2,651.306173；另有未测完整 CPU 的失败/支持 |
| B03 | 512 回合 /131,072 步，2 fit | 6,475.228561 |
| B04 | 256 回合 /65,536 步，0 fit | 2,342.870991 |
| B05 | 192 旧路径、576 分配结果；0 新 native 步/fit | 成功 A02 65.478097；A01 不完整账单另保留 |
| B06 | 64 回合 /16,384 步，0 fit | 987.521216 |
| B07 | 64 回合 /16,384 步，0 fit | 110.806311 自身 +.051802 等待子进程；另 A01 零查询失败 1.218674 |

等待证据保持一份 canonical 副本：B01–B04 和 B07 主数据在配置节点 `wsl_4070`
的 `/home/wu/projects/HMASD/runs/uav_user_waiting/`；B05 A02、B06 原始数据在
`local_linux` 本工作区对应 runs 目录。上表 compact result 保存精确路径、哈希、
完整输出/reader 定位和所有世界符号，不能把已删除的本地阅读副本当 canonical。
B05 A01 的崩溃 core 和必要原始 snapshot 属于 Root 保留的故障取证，A02 成功没有
解释或修复它。B07 最终清理净回收 **2,594,779,136 allocated bytes**：三个已终结
source snapshot、320 个临时输入副本、重复本地结果/观察和提取 scratch；留下
130 个唯一 raw/outcome/summary/reading 文件、31,865,551 payload bytes。
[精确清理记录](../../runs/uav_user_waiting/b07_cap_two_a02/cleanup.json)与 notebook
最终更正优先于早先少 4,096 bytes 的临时总数。等待研究没有活跃 worker、reader、
未读建议或自动续跑；保留代码是能力/证据复用，不是运行中的依赖。

### RF B01：条件性 U32 目标收益，以及等待损失

固定问题是在同一有成本测量/通信权利下，积分联合 RF 结果能否优于已有正确随机
规律的平均功率控制 P。宿主为 N5/U50/H256、静态用户、原生贪心分配和 J；用户链路
额外损耗标准差 4.14 dB，相关系数为 `exp(−实际三维位移/17.62)`，悬停冻结残差。
这是声明的近似 Markov 信道，不是已校准的真实空间场。A2A 不变。

P 与 U32 都获得 0.5 dB 量化的全 250 链路当前测量、相同地图和 C 提案；每轮
391 bytes/2,000 bit/s 加 0.1 s sounding，共 1.664 s，三 tick 后交付，留下
1.336 s 全轮计算余量，命令保持四 tick。P 用解析期望接收功率；U32 用 16 条
Gaussian tape 及 16 条反向 tape 积分完整分配/J。两者沿相同两顺序、轮换单机
27 运动×31 mask 的受限搜索，完整时每轮 116 请求。采样数不是独立世界数。
报告 tick 的 payload 权重为 .9，其余为 1；错过期限则旧命令和 mask 原子保留。

32 个新配对世界 29641000…29641031 全部完成。固定主判读是每回合 payload-J/256
的 U32−P；以下区间均为描述性 mean±1.96SE：

| 指标 | U32−P |
| --- | ---: |
| payload-J | **+.007529588 [.004058439,.011000736]**；26 正/6 负 |
| payload 服务数/tick | +.259631 [−.034786,+.554048]，仍不确定 |
| 平均用户年龄 | **+.940410** [.1350,1.7458] |
| 回合最大未服务间隔 | **+18.40625** [6.7631,30.0494] |
| 最差用户平均年龄 | **+4.7302** [1.3276,8.1329] |

正收益不能抹掉个人伤害。29641005 的 J +.0324744、服务 +1.953125，同时最大
间隔 28→129，user28 的 [118,247) 是闭合间隔；29641020 也有闭合 127 tick
间隔。29641019 的 J 增加，但 user34 在 [118,256) 持续不服务，138 tick 是
右删失观察长度。最差 J 世界 29641031 则下降 .0163034，最大间隔却从 51 改善
为 35。没有全队零服务 tick、没有从未服务用户，均不等于连续性满意。

全部 **4,096** 决策按时，模型与动作确实改变；此前担心的计算期限失败在这次
实现/节点上没有发生。每任务累计全轮计算均值 P 1.3823 s、U32 9.4351 s。
完整独立 ResearchCritic 建议且本人接受：保留有限 U32 相对同信息 P 的条件性
payload 目标能力，关闭固定购买，不自动复制/加粒子/调期限/改连续性目标。
结果没有隔离“精确积分”、有限 Monte Carlo 搜索路径和后续轨迹相互作用；
悬停残差持久性与无个人等待惩罚可能同时帮助稳定受益者和持续排除，仍不是已识别
中介机制。它不是学习、场景实证、服务保留或默认部署结论。

另一 DM 已发表 FULL−PRIOR 的 payload-J −.015929915、32 世界全负，这要求将来
讨论 U32 的实际购买价值时认真面对便宜 PRIOR。但两个面板/信息/延迟不同，
**不能相加或相减得到 U32_FULL−P_PRIOR**。这没有推翻这里的 U32−P 正结果。

**证据、完整成本和终态。** 冻结执行源 `9b6f493b343c2939b374a1ce21384266d3257456`；
完整结果/原始独立审查发布 `1e363409be4502f81fb1f91a847d83162a38a325`；
最后 standing/cleanup 发布 `d2cc6a4ed89fa58228b3a82c693d541898e6d09c`。
入口为 [compact result](../../runs/uav_radio_uncertainty/b01_correlated_shadow_a01/result.json)、
[完整数值 reader](../../runs/uav_radio_uncertainty/b01_correlated_shadow_read_a01/reading.json)、
[原始科学审查与 DM 决议](candidates/uav_radio_uncertainty/NOTES.md#b01-independent-review-and-disposition)。

本批 0 fit/更新；64 个 H256 科学回合、16,384 步，另四个 H8 正确性回合/32 步，
共 **16,416 native 步**。Worker 380.244 wall /392.749 CPU-s，reader
2,678.822 wall /2,761.467 CPU-s；峰值 RSS 分别 426,208/402,112 KiB。
各 pass 都核算 20,529,026 候选 fleet scores，完整 reader 不是免费验证。
正确性另 4.512 CPU-s、synthetic checks 另 7.949 child CPU-s；source/advice、
失败启动壳、工程、传输/发表支持未全面计量。二者均支付声明的测量/流量/sounding/
交付成本，没有实验性的采集价值比较被暗中加入。

唯一主 bulk 在 `wsl_4070:/home/wu/projects/HMASD/runs/uav_radio_uncertainty/b01_correlated_shadow_a01/`，
129 个 canonical artifacts 共 150,807,102 bytes；`summary.json` SHA256
`6dca1d6ed767d689b36bcd7aa932e8076a616613ececfeadafb111a03341c140`。
reader 在同级 `b01_correlated_shadow_read_a01/reading.json`，SHA256
`099d634bc5ee3536193f36e3e2a76382ca9cb6e0edf9d8f9448d52bab38721dd`。
另九个 H8 evidence 文件 330,780 bytes 原位保留。compact result 及完整小 reader
在 Git；原始正面、负面和删失记录没有因结论而删减。

已删除远端 `.git/hmasd-launch-sources/` 下
`2df8b39b75684520824fa178ccb43788`、`58bb94a971024c3eb35b5215eaa224ef`、
`c7d012083adb4ec3a05a57514b71f91d`，以及本地
`temp/directions/uav_radio_uncertainty/`（688,128 bytes）；六个空日志额外回收 0 bytes。
这些目标净回收 **2,455,527,424 allocated bytes**，无工具阻塞、无移动备份。
[cleanup.json](../../runs/uav_radio_uncertainty/b01_correlated_shadow_a01/cleanup.json)保留
精确目标、终态和删除后哈希验证。观察器最后已 drain/stop，无未消费事件；worker、
reader、科学审查和其他 raw 消费者全结束。P/U32 源码/测试保留，因为它们仍是有用
能力且 information-cost 包有实际 import；源依赖不表示还有运行中研究。

### 已完整评估、尚未选择的策略搜索候选

资料任务现已完成。本人完整 source/price 在
[623ab06fb 原始账单](https://github.com/CartmanFatass/My-paper-code/blob/623ab06fb29cba36299e0a3e385267ce3feb2a6f/docs/research/candidates/uav_radio_uncertainty/NOTES.md#episode-search-complete-source-price)；
Astra/max 独立评估的完整原答、实际阅读覆盖及本人回应在
[d9183bdf 原始建议](https://github.com/CartmanFatass/My-paper-code/blob/d9183bdf99b1e17f35e568bb6494f30861cdf3dc/docs/research/candidates/uav_radio_uncertainty/NOTES.md#episode-search-original-advice)。
它是同一独立会话中的 follow-up，复用了其先前审查，不是新盲审；三库/原论文与
July/G50 阅读的页段、遗漏及限度都保留。本人没有把 adviser 共识当新实验。

建议保留一个未来可考虑购买的问题：**完整回合参数搜索能否让冻结 P0 上的小幅
上下文读出，优于等 native 曝光的全局校准和已有强普通参照？** Oracle 支持将来
owner 恢复且 Root 分配后的一次完整探索；Root 已完整阅读并明确 **本次不选择新
run 或 claim**。`uav_episode_policy_search` 仍 unowned/unactivated/UNSELECTED，
未创建目录、代码、测试、reader 或实验句柄。

候选合同足够具体，恢复者不应把它改写成任意 ES 配方：原 B08 N5/U50/free-space/
H256、训练全部发射机 ON、27 运动、四 tick 决策；保留 P0 的 114 合法字段及
34,715 个冻结参数，用同一次原始 FP32 单行 forward 获得 l0 和第二 ReLU h128。
定义 `hbar=h/max(1,||h||2)`；CAL 为 `l0/exp(tau)+tanh(b)`，28 参数；CONT 为
`l0/exp(tau)+tanh(b+W hbar)`，3,484 参数。新参数全零，无 actor 新信息/历史、
公用动作 coin、teacher、critic 或 Adam。新 head/归一化/fitness/更新用 FP64。

两独立配对 block 各有 CAL/CONT，共四 fit；每 fit 16 iteration，每次 16 Gaussian
方向，尺度 .05，每方向两全新世界/tape 在正负号和两家族间共享。方向用各 fit
独立地址流，不将不同维度扰动说成相同。每个扰动策略在完整回合控制全部五 actor；
fitness 是两世界完整 native J 均值。令 `d_k=(Jplus−Jminus)/2`，scale 为
`max(sqrt(sum(d_k²)/16),1e−8)`，更新为 `.02/(16*scale)*sum((Jplus−Jminus)*delta_k)`，
所有方向均保留；**每个扰动策略内部**及更新后中心均把 tau 限于 ±ln2。
只评四个最终中心，无部分 fitness、排序精英、验证/调参、checkpoint 选择或额外
中心 rollout。它是 ARS-inspired 明示改造，不是精确 ARS-V1、无偏原始 J 梯度或
保证单调改进的方法。邻域 fitness 与最终中心存在实质差别。

本次资料审查纠正了一个关键合同错误：**A 为全 ON；ZERO 是物理静默规则**，
轮换 eligible actor 的 capped 可见用户数为零才关闭该发射机，不是实际服务数。
沿用 B08 的旧观测后装 mask 语义。匹配参照为 P0_A、已付校准的 temperature-two
Bstar0_A、Hdirect_A；另保留 G_A、C_A，以及更丰富动作权利的
P0_ZERO/Bstar0_ZERO/Hdirect_ZERO，不能混称全部 ON。Hdirect 支付 C+P0 及其实际
T/H 两向量计算；G 随机、C 确定。三个 ZERO 的实践比较不能自动给 learner 增加 gate。

端点评估用 32 全新世界×两固定私有 tape，11 随机程序各 64 回合，C_A 32 回合；
四 endpoint 对八参照、两 CONTb−CALb、三 ZERO−A，共 **37 contrasts**，20,000 次
共享 world-bootstrap/640,000 indices，按世界平均 tape、分别保留 block 与所有符号。
完整读 J、服务/质量、travel、team p10/minimum/zero-service 和计算成本，不加个人
连续性或物理能源结论。另在每 worker/reader 已付首轮上下文执行 81,920 次零 head
对照，复用 l0/h/innovation，0 额外 native/P0/RNG；这是有限上下文初始化核验，
不是初始策略完整 rollout 或全域精确一致断言。

**拟购完整价格：**4 fit；4,096 训练 +736 endpoint =4,832 回合，**1,236,992 team
steps**、6,184,960 UAV ticks、1,546,240 actor 请求、1,536,000 categorical draws；
1,024 独立训练世界，32 新评价世界。每 worker 及完整 policy-replay 各支付
1,392,640 head 请求、至多 1,515,520 P0 forward、71,680 full-C 请求/
1,935,360 paths/7,741,440 model ticks，helper+C 链路上界 368,435,200。
CONT 每 pass 读出乘加上界 2,406,481,920；P0 上界 52,182,384,640；
1,024 方向/1,798,144 normal 坐标、64 次中心更新及其完整重构也在账内。
标量 reader 另核验 **1,551,072 状态、7,755,360 局部行、418,789,440 power links**，
所有物理/旧行/mask/政策/更新/完整 return 绑定，不只查 hash。

预算是 worker **.6–2.0 CPU-h**、full reader **.75–2.5 CPU-h**、synthetic 正确性
**.01–.05 CPU-h**，合计 **1.36–4.55 machine CPU-h**；顺序 node-wall **1.5–6h**，
另 **14–24 focused support-hour equivalents**，不等于已测人时或 Codex elapsed。
RSS **.5–1.5GiB/process**；单份 canonical **3–6GB compressed /9–12GB uncompressed**，
工作空间 **12–16GB**。这些是由 B08/B10 推算的未基准测试估计，不是上限、节点
准入或免费支持承诺；正确性 native 额外回合当前计为零，未来具体需求须先计价。

继承费用保留：P0 B02 1 fit/114,688 步、81,920 labels、8,000 updates/
4,096,000 presentations、107.543822 worker+reader CPU-s；Bstar0 已付 256 校准
回合/65,536 步及 32 final 世界，139.828009 CPU-s 是两个 lineage 校准合计而非
可对半归属。Hdirect/G/ZERO 无须重 fit，但原始 B07、transmission B05、B08 投入
以及新每请求 model work 均非免费。Fleet B02–B10 历史合计 **22 fit、2 calibration、
4,055,080 步**，不能再把其中单批费用重复相加；更早 B01 与 actual-S2 父方向另计。

主要未解决因素是 3,484 维/16 更新是否能取得有信息的搜索，以及普通 CAL 是否
已经吸收实际增量。完整回合 fitness 没有诊断旧 PPO/critic 失败；B04/B10/S2 也已
使用完整回合。旧 B05 的 critic-free 完整反事实及其负面结果必须保留。若 CAL
匹配/胜过 CONT，保留校准价值；若胜 P0 却不胜 Bstar/Hdirect，则强普通参照仍是
用途判断；若只在较窄权利下胜而输 ZERO，分开表述能力与采用。混合 block、区间
不确定、稀疏/无动作改变、活跃损害均结束该有限购买，不自动加 seeds、步数、
head、gate 或修复。确切 seeds、失败规则、序列化/输入绑定和有限 fixtures 尚待
将来选中后的 L0；现在没有任何新政策收益、运行时间或初始化一致性测量。

### 继续时的边界与所有权

本次资料工作仅有 source/记录读取和整数成本计算，0 新实验、native/model/C/
allocator/RNG 查询、保存结果 reduction、test/prototype；交接没有启动下一轮。
Root 原文 disposition 另保存在 [RF NOTES](candidates/uav_radio_uncertainty/NOTES.md#episode-search-dm-response)
末尾，和 Oracle 建议分开。无悬而未决的科学分歧，无等待生产者或需补读结果。

交接后须 owner 明确继续；状态询问、阅读本节或空余算力不会恢复工作。若将来
选择策略搜索，先核对当时 RESEARCH 的 pause/lead、原建议前提和强参照，再由
Root 作投入分配。未归档时可复用此 DM；已归档则依 owner 规则新建 DM、继承
全部正负证据。建议方向拥有 `experiments/candidates/uav_episode_policy_search/b01/`、
对应 tests、`docs/research/candidates/uav_episode_policy_search/`、runs 和 temp 路径；
这些仅是拟议所有权，不接管 fleet、parent、静默/信息或 Claude 的其他问题。
精确输入发表、适用工程审查和实际节点准入在任何未来执行前完成；旧终态句柄、
已删 source snapshots 和完成操作不重启。没有外部数据或他人 ACK 是本节尚未
完成的依赖：**本轮完成，停在 handoff 边界。**
<!-- DM_USER_WAITING_END -->
