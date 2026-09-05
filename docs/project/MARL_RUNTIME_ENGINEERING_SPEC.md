# MARL runtime engineering specification

Status: operative, 2026-09-05. Complete Portfolio Pro plan applied under AGENTS §4.7
and the owner's standing specification delegation. This is engineering guidance, not a
new scientific evidence class or launch condition. The original object contract remains controlling
except for an explicitly named applicable appendix below.

Source: [complete Pro decision](../research/portfolio/pro_packets/20260905_marl_runtime_spec/pro_review_01/archive/RESPONSE.md),
response SHA-256 `da9e86d05bb34e070b936ca69aafdf4a1b912caf88bb4d1b150c3831e9a2125f`.
Application: [decision record](../research/portfolio/decisions/2026-09-05-marl-runtime-engineering-spec.md).
Reference evidence: [six-library synthesis](../research/portfolio/pro_packets/20260905_marl_runtime_spec/REFERENCE_EVIDENCE.md),
[pinned source manifest](../research/portfolio/pro_packets/20260905_marl_runtime_spec/SOURCE_MANIFEST.json),
and [navigation index](../research/portfolio/pro_packets/20260905_marl_runtime_spec/REF_LIB_INDEX.md).
These are static source studies with explicit unread dependency boundaries, not library benchmark
results or measured HMASD speedups. Archived draft and historical measurements remain evidence.

## General requirements

### 1．目的、适用范围与调查阈值

本规范要求以适当的算法实现、数据布局和执行方式完成已经选定的科学观察。工程优化不得通过删除比较器、世界、种子、候选、独立检查、完整终局或必需输出，把不同科学对象冒充为更快的原对象。

**调查阈值按单臂、单训练种子的完整逻辑调用计算：toy主机超过2700秒，UAV主机超过43,200秒。** 无训练种子的A类对象，以该卡规定的一次完整对象调用为单位。初始化、rollout、学习、replay、全部必需评估与检查、终局处理及最终发布属于同一工作链，分脚本、分阶段或分slice不重置阈值。

若一个调用包含不可分离的多臂共同计算，按整个调用调查，同时如实披露可归属的各臂工作；不得通过事后均分一个不可分离耗时规避调查。主机类别在既有任务说明中声明，不由文件名、目录名或重命名决定；混合路径分别说明组成及整次成本，不自动采用较宽松阈值。

预计或实测越过上述阈值时，CM必须在既有任务和最近可行的干净边界完成具体工程查证：完整工作量、主要源码路径、批处理与依赖关系、编译／设备／并行边界、已有计时及缺口。先读源码和现有证据；需要新测量时，选择有明确预算与停止条件的有界工程任务。

**阈值不是新的wall cap、计算额度、科学结果规则或第五个启动条件。** 仍执行原对象更严格的cap和停止规则。仅越过调查阈值不自动终止一个原本合规的活动调用；已有投影超过原卡硬cap的调用也不能因此被允许。历史有效结果不追溯失效。

### 2．完整调用、完整study和计算工作分别核算

每个被调查或作性能比较的调用，必须声明实际计时起止点。整次计时包含该调用实际支付的import、专属编译／初始化、计算、设备同步、检查、输出构造、写入和必要子进程等待；不能把必需publication移出计时，再称为端到端成本。

冷启动、稳态和已有编译产物的复用分别披露。确实共享的一次准备成本在study账中记录一次，不重复收费，也不能假定大量未来调用来摊薄尚未实现的成本。Git、SSH、输入复制、代理工作及外部排队另记其范围；未测值写为未测，不填零。

完整study至少区分：

* 从首个实际执行到最后完整输出的elapsed critical path；
* 各逻辑调用wall之和；
* 能够完整核算时，各调用aggregate CPU之和。

并发调用wall之和可以大于study elapsed；两者不是同一指标。多个小调用组成的大study不因单项都低于阈值而免于总成本披露，但**45分钟／12小时不同时充当study总上限**。

争用、配额节流、IPC等待和设备排队属于实际wall。已知争用条件要记录；未测争用损失不得凭推断扣除，也不得用空闲节点或线性并行的假设改写实测值。异步设备计时在所声称的完成边界同步，不能把dispatch时间当执行完成时间。JaxMARL的编译外计时与Mava的首次调用包含编译，正说明二者不应不加区分地比较。

### 3．先说明完整工作量，再讨论加速器

CM必须沿真实输入到最终输出的调用链，列出决定成本的少量主要项及完整计数。按对象需要包括：环境和agent数量、时间步与内部子步、rollout、优化epoch／minibatch、recurrent长度、分叉／候选、比较器调用、独立枚举／checker、记录和发布。

共享policy的环境×agent batch、独立policy逐agent执行、模拟器内部子步和learner更新频率必须分别说明。不能只报告“环境步数”，遗漏其内部昂贵比较器或组合枚举；也不能把增加总采样量、优化量或模型副本所得吞吐提升当作相同工作更快。

成本律使用与实际实现匹配的完整阶段或完整batch测量，记录源码版本、节点、设备、shape、线程数、数值语义及计时范围。合成输入外推是规划估计，不是完整运行实测或优化下界。未覆盖工作必须列出，不能设为零；不能把旧串行时间除以核心数作为新执行设计的准入依据。

### 4．batch与并行的允许范围

优先考虑在已接受语义下合并真正独立的环境、兼容的共享policy agent、replica或反事实分支轴；同时声明每个轴及其状态所有权。时间、因果前后、autoregressive动作和recurrent状态依赖保持原顺序，除非另有适用的算法等价依据。

batch变化不是当然的行为保持修改。必须检查RNG地址／消耗顺序、mask、terminal与truncation、bootstrap、recurrent reset、样本与更新频率、replay比例、policy新旧程度、reduction和tail处理。不能复制参考库中与原对象不一致的截断、补齐或丢尾行为。

以下两类在明确的工程任务内属于允许的计算实现，不按“通用worker池”退回：

**普通进程内tensor／array batching；以及一个命名计算函数内、单层、固定规模、同步完成的native计算团队。** 后者必须有固定生命周期、明确计算参与者上限、私有可变状态与输出空间、必要的内部同步，以及按逻辑序号归并结果与错误的规则。它不提供动态任务提交接口、通用executor、队列服务或新的执行控制面。

分布式、多科研进程、多节点框架、通用worker池、scheduler、retry、lease、恢复服务和新增runtime guard仍按现行§4处理。普通编译器子进程不是多进程科研worker，但其成本和退出状态不能隐藏。库内部的线程、BLAS/OpenMP/Torch并行也计入实际拓扑；不得由外层四线程再隐含四套内部线程团队。

**原卡明定的单线程、设备、batch或进程隔离条件不会被本通用条文覆盖。** 改动这些条件必须有该对象明确适用的附款。参考库采用某种拓扑，不构成对HMASD的授权或速度证明。

### 5．native、编译和设备选择

对实际CPU热点，先辨认是否存在重复构造、过细的跨语言调用、逐项Python循环、不必要的pack／copy或可等价复用的计算，再选择array、tensor或粗粒度native边界。已有C++、编译优化标志或一次大ctypes调用，不证明内部工作已经合理。

对设备路径，分别说明采样、训练、buffer和输出所在设备，以及必须的搬运与同步。小tensor在某一设备慢、大batch在另一设备可能更合适，均需受当前对象的完整数值和成本合同约束；**不强制每个已满足预算的A/B对象再跑CPU/GPU对照或worker数量扫描**。不得默认引入新语言、GPU、JIT、CUDA graph或额外依赖。

### 6．最小CPU核算及资源含义

当并行改变预算含义，或当前命名工程任务本身判断资源／吞吐可行性时，允许在现有wall和RSS之外增加**最小的整次aggregate CPU核算**：

$$
C_{\mathrm{CPU}}
=\sum_{p}\Delta\bigl(\mathrm{userCPU}_p+\mathrm{systemCPU}_p\bigr).
$$

求和覆盖被测科研进程及其实际子进程，包括编译器；进程累计值已含其线程时，不再把线程逐项重复相加。wall包含等待，CPU累计表示实际处理器工作，两者不能互换。GPU计算也不能由CPU累计代替。

使用现有操作系统／执行工具的累计记账和有限起止读数，不建立采样服务、常驻profiler、进程注册表或新的遥测框架。RSS注明是主进程、子进程最大值还是实际同时占用范围；不能把多个进程各自峰值称为同时峰值。

普通科学结果缺失非主张必需的资源量，沿用现有`resources_unmeasured`含义；但**以CPU上限合规为结论的工程评估，缺失完整CPU账就不能声称该资源结论成立**。这不是对其他A/B结果增加资源遥测有效性门槛。

### 7．完整性、验证和预算

数值验证采用当前对象已经规定的精确性或容差。精确census的原整数／limb、完整支持和tie必须保持；普通A/B对象不因本规范获得通用bit-identity或C-FORMAL义务。

必需的独立checker不能直接复用被检查者答案来证明一致。未被主分支读取、但已规定为报告诊断的量也不能删除。对于重复计算，可以研究保持原责任分离的等价实现，不能先省略、再以速度改善补作理由。

保留既有源码、runner、编排比例和测试预算，按完整逻辑变更累计；本规范不产生新的额度。smoke、规则测试、必要语义验证和命名工程评估分别说明用途，禁止借测试反复预跑正式fixture、挑最快配置或追加计时。

科学必需验证不能因超过测试预算而删除；应优化验证实现或返回具体缺口，需要另选有界工程工作时按既有权限处理，不能自动把超时测试变成无限预算实验。完整发布失败后，保留既有“同证据离线发布、真实常量和全部必需读回”要求；局部pass或程序退出不能替代完整结果。

### 8．既有角色和执行边界

CM在原任务中记录完整工作／成本律、实际热点、参考模式、shape／拓扑、保护语义、资源范围、验证和停止条件；semantic implementer实现这个最小完整路径；routine implementer不自行选择或修改batch、native backend、并行、reduction、资源核算及数值语义；既有独立reviewer检查整个变更、消费者、完整科学量与成本覆盖。

没有具体超预算或待判性能问题的对象，不增加固定profiling任务。需要新测量时，既有链条明确选定一次有界任务；不新增角色或审批层。实际缺口返回原责任节点，不能用更小科学问题替换工程问题。

本规范不增加证据规范§11.4之外的启动条件，不修改既有源码接受或实际节点资源准入要求。技术正确、可运行、完整发布、资源合规和科学效果是不同判断，不能相互替代。

---

## VNFC唯一对象限定附款

本附款只适用于 **`VNFC-R03-EXACT-BATCH-FEASIBILITY-E01`**，回答：改变执行设计后，能否为原R03提供有完整等价性、成本覆盖和资源依据的实施路径。它不是新headroom观察，也不是新科学recast。方向Pro已选择的三个组成部分全部保留，不只增加线程。

### 1．固定配置与准确授权范围

| 项目        | 最终限定                                                                                      |
| --------- | ----------------------------------------------------------------------------------------- |
| 执行节点      | 配置中的`wsl_4070`，原CPU／数值／工具链路径；本次不选择GPU、其他节点或新fallback                                      |
| 科研进程      | 一个；编译阶段允许原有正常编译器子进程，纳入完整成本，不作为科研worker                                                    |
| native计算队 | **总共四个计算参与者：调用线程参与计算，加三个native线程**；单层、同步完成，不存在额外第五个协调计算者或第二计算队                            |
| batch     | **固定宽度8**，承载相互独立的完整调用／continuation工作；轨迹内部仍顺序执行                                            |
| 分配与归并     | 按固定逻辑索引分配工作；每项私有可变状态和输出；结果、tie输入及错误按逻辑顺序归并，不按完成先后决定                                       |
| 隐含并行      | 与该native队无关的BLAS／Torch等内部计算线程限制为1，禁止嵌套计算队；编译单作业、先于并行测量执行                                  |
| 唯一工程评估    | **整次wall不超过60秒，aggregate CPU不超过300秒**；包含import、build、参照比较、候选执行、检查、归并与最终发布                 |
| 内存        | 原实际节点physical/effective各至少4 GiB准入；另外由CM据实际私有scratch、八项输入／输出、共享数据及编译阶段说明可容纳范围，不从旧RSS乘线程数猜测 |
| 源码与验证预算   | 原R03累计2000非测试源码行、600行runner及现行编排／测试规则不变；已有483行源码、58行runner计入，不重新起算                        |
| 禁止自动扩展    | 不改线程数、batch、节点或fixture，不追加计时，不把未使用的旧校准额度或本次余额转成下一次调用                                      |

四参与者和batch8有节点快照作为有限规划依据：报告观察了20个online logical CPU、允许列表0–19及所查cgroup限制，但没有证明独占资源或全部后代约束；旧可用内存也不是新调用的准入。若实际限制或scratch所有权不能支持该固定配置，返回具体缺口，不能临场改成另一配置继续计时。

**300 CPU秒是整次评估的保守上限，不是承诺消耗量，不表示允许第五个计算参与者，也不是各阶段分别获得300秒。** 四线程与60秒的乘积不能代替实际CPU核算。

原R03§10的单计算线程限制，**只在本次E01评估内由上述固定配置替代**。这不追溯改变原串行校准的合规性，也不自动把完整census改成四线程运行。完整census的2700秒wall保持；本次没有默认为它授予四倍CPU预算。

### 2．必须保留的科学对象

原N7、十六个历史世界及外生tape、两个失败区各八世界、全局固定偏离epoch \(d\in\{0,1,2\}\)、至多一次合法因果历史命令、不变BCRH前后控制、全部候选、60秒`R_fail_60`及120秒完整原生终局都不变。四类最优map、原tie、原MEI 0.10和完整原结果规则不变。E01不读取目标终点、不选择目标policy map、不产生learner、训练、checkpoint或新RNG暴露。

保留的机会证据仍为aggregate下界 \(7/960\)、zone 1为0、zone 2为 \(7/480\)，以及特权 \(7/60\) witness；它们不是已实现的因果gap或调优同信息headroom。

### 3．唯一候选设计的三个必要组成部分

**精确选择分解。** 按原方向裁决，公开失败区的实际观察使完整因果历史类不跨区。固定同一个 \(d\)，令

$$
q_h(a)=\sum_{i\in h}(R_i^a-R_i^{BCRH}),\qquad
A_{z,d}=\frac18\sum_{h\subset z}\max_{a\in\mathcal A_h}q_h(a).
$$

对应完整目标为

$$
M_{\mathrm{robust}}=\max_d\min(A_{1,d},A_{2,d}),\quad
M_{\mathrm{all}}=\max_d\frac{A_{1,d}+A_{2,d}}2,\quad
M_z=\max_d A_{z,d}.
$$

不能让两个区各自选择不同epoch组成一个稳健策略。实现须验证原最少偏离、epoch及canonical tie，特别是zone-optimal map在另一zone上的tie，不能直接套用aggregate-optimal map。该分解最多改变选择算法，不删除任何候选的完整native后果。这里保留的是方向裁决的数学推论，实际因果key和实现尚未验收。

**跨完整调用的不可变公共权重复用。** 仅按权重函数实际依赖的完整公开值tuple复用，不按world ID、未来tape、隐藏状态或候选后果建key。原实现已有的调用内复用不得再次计为新增收益。独立checker必须保持独立；其实现依赖、scratch和线程安全在当前报告中未得到证明，因此不给checker缓存或并行效率记入预期收益。

**固定native批处理。** 将独立完整调用按公开输入关系组织为固定宽度8的批次，由四参与者处理；continuation内部的前后决策不并行化。普通tensor布局、公共权重复用与计算队是执行实现，不改变信息集、候选支持、数值语义或选择对象。

### 4．执行前冻结的验证与非目标fixture

CM必须在任何E01测得输出之前，把一份确定性非目标fixture及其确切规模写入原技术任务并提交。当前资料不足以替代实际fixture字节；这一工作属于本次选定的实施任务，不能在计时后改样本。

完整覆盖至少包括：

| 覆盖项                         | 要回答的具体问题                                                     |
| --------------------------- | ------------------------------------------------------------ |
| 六个post-loss epochs及完整合法候选支持 | 新路径是否真正执行完整BCRH评分、独立checker、独立枚举和记录核对，而非只执行一个便宜子函数           |
| 相同公共tuple、不同物理状态；不同公共tuple  | 复用是否只覆盖真正不变的权重，是否污染候选状态、结果或失效边界                              |
| 原串行参照与新固定批路径                | 完整候选记录、合法命令、精确算术及canonical顺序是否一致；不能只比较最终最大值                  |
| 完整batch及尾批语义                | 尾部不丢项、不把padding计为科学候选、不因线程完成顺序改变输出                           |
| 合成精确选择输入                    | 四类map和所有tie，包括跨epoch不兼容、zone-optimal另一zone的tie及BCRH包含关系，是否保持 |
| 非目标完整轨迹／终局路径                | 60秒指标之外的原120秒终局、检查、history及continuation记录是否仍被完成              |
| 输出与资源核算                     | 实际写出并读回所需记录、map和summary；wall、CPU及RSS范围是否覆盖所声称路径              |

用于本次固定配置成本结论的参照与候选工作，全部计入唯一E01评估；不能先跑一次“验证”取得速度，再以“正式评估”重复计时。原预算内的普通smoke／规则测试可以验证非正式fixture的接口、分支和发布，但不能用来扫描配置或预跑E01正式fixture。原已完成六调用校准不重跑。

### 5．完整成本律及CPU边界

完整R03成本账使用后续校准及方向裁决确认的完整终局上界：

| 完整工作项                            |          上界 |
| -------------------------------- | ----------: |
| native ticks                     |   9,418,560 |
| 完整BCRH调用                         |     376,688 |
| BCRH候选行                          | 738,685,168 |
| world–epoch–action continuations |      94,128 |

原卡§9仍可见较小的早期计数；本轮不能无说明地回用那些数值。技术附款应并列保留历史计数，并明确上述完整终局计数是新成本律的依据。旧solver的903,722,928扩展及9,152.0174秒投影也保留，只有完整替代选择的等价性成立后，才由真实扫描、tie及map构造成本替换。

采用方向裁决给出的完整wall规划律：

$$
\widehat T_{\mathrm{wall}}
=60+2\left[
N_{\mathrm{tick}}^+\hat t_{\mathrm{tick}}
+\sum_r Q_r^+\hat\tau^{\mathrm{batch}}_r(4)
+U_W^+\hat t_W
+\widehat T_{\mathrm{selection}}
+\widehat T_{\mathrm{history/records/publication}}
+96\hat t_{\mathrm{prehistory}}
+\widehat T_{\mathrm{uncovered}}
\right].
$$

其中：

* \(Q_r^+\)按完整支持的分组与尾批计算，不能简单把总调用数除以8；每组的尾批仍有成本。
* \(\hat\tau_r\)来自**该固定配置的完整批次**，包括独立checker／枚举、分配、记录核对、同步和归并，不使用旧串行时间除以4。
* 权重构造若已包含在批成本中，不再单列重复收费；只有验证了跨调用复用后，才可正确拆出共享项，不能重复扣减。
* 精确选择、history、记录构造、磁盘发布和未覆盖工作都有完整来源。固定60秒allowance覆盖不足时，明确记录和计入缺口，不能假装已覆盖。
* 保留factor 2及完整调用的固定allowance；它们是经验保守规划，不是普遍运行时间定理。

**上述公式的60秒固定allowance，与E01本身60秒硬上限是两回事，不能相加作为E01的新额度。**

另按同样完整阶段建立aggregate CPU工作投影，使用各阶段实际user＋system CPU及完整计数；不得以wall乘线程数冒充实测CPU。当前尚无新完整CPU单位成本，必须保持未知。

若未来完整census采用四参与者，必须依据E01实测和完整实现明确整次CPU额度及适用的执行附款；本轮仅分配E01的300 CPU秒，**不自动授予完整运行10,800 CPU秒或其他倍增额度**。这不要求再次逐项请批，但仍要按既有权限形成有量化依据的完整运行方案。

### 6．通过、停止与后续边界

只有以下事实同时成立，E01才支持进入原R03的完整实现与技术接受：选定设计实际发生改变；精确等价及完整覆盖成立；实际60秒wall、300 CPU秒及资源范围合规；所有完整成本项有依据；完整wall投影**严格低于2700秒**。

这个结论只说明出现了值得继续实现的执行路径，不是headroom阳性、完整census结果或直接启动许可。原因果key、完整census和publication仍须完成并被技术接受。

遇到不等价、线程安全／内存所有权不成立、缺少必需输入或成本、wall／CPU超限、完整投影仍不低于2700秒时，结束这一项工程投入，带准确缺口返回原Convergence节点。不得自动换线程、batch、机器、fixture、增加计时或重做旧校准；不得据此生成“没有headroom”的科学结论。该停止不改变原方向生命周期、优先级或已有两次recast记录。

---
