REQUEST_ID=2026-09-05-vnfc-r03-cost-convergence-01
PINNED_REFERENCE=3d0171e0d53f53b602092e9791f45ea00e803568

# FINAL_DECISION：CONTINUE

**最小支持家族：** `VNFC-CONTROLLER-HEADROOM-A-RECON-CAUSAL-ONE-DEVIATION-R03`，严格限于原十六世界、同信息、至多一次偏离、完整原生终局的精确有限对象。

**唯一下一对象：** `VNFC-R03-EXACT-BATCH-FEASIBILITY-E01`——原R03下的一项**有界、结果盲、语义等价的批处理执行可行性评估**，不是新的科学RECAST。

**当前执行状态仍为 `BLOCKED_WALL_CAP`。** 本裁决不放行完整census，不重开已完成的校准，也不声称任何新实现已经合规或可运行。新增评估额度及并行执行条款必须先由正确的Portfolio Pro节点形成对象限定方案；当前所有者的常设委托允许Root随后按该完整方案执行，无需再次逐项投票，但并不把本方向节点变成Portfolio授权节点。

## 先回答所有者的执行设计疑问

**已使用C++，已实现粗粒度跨语言批调用，但尚未证明完成了有效的批处理／并行优化。不能把当前串行投影当作充分优化后的最低成本。**

`native_backend.py::build_native_backend`使用C++20、`-O2 -fno-fast-math -ffp-contract=off`；`calibrate_native`通过一次ctypes调用完成整组native校准。因此，主要问题不是“每个候选都从Python跨一次边界”。但`native/calibration.cpp::calibrate`中的六个BCRH调用、tick和prehistory循环均为串行；`bpcr_general.hpp::grun_bcrh`的候选评分以及已读batch导出也仍是串行循环。现有实现确实在**每次BCRH调用内部**复用了公共权重，不能把这个已经存在的优化重新列为新增收益。

高成本来自嵌套的完整比较器计算：最多94,128条world–epoch–action continuation，产生376,688次完整BCRH调用，内部累计上界738,685,168个候选行，每行成本包含评分、独立checker、独立枚举和候选记录核对。**这不是把一个廉价物理tick重复九百万次的问题。**

原卡§10明确要求“一进程一计算线程”。所以，接受的串行校准符合当时的执行限制；它既不能因此被判定为违反原卡，也不能因此被认证为已经满足充分利用batch／parallel的性能目标。改用并行必须显式处理这条限制。

# CALIBRATION_READING

## 观察与投影必须分开

| 项目           | 接受的记录及其含义                                                                       |
| ------------ | ------------------------------------------------------------------------------- |
| 实际校准         | 源码`9c41484a068e266581b6456bddfd3f6448d3931c`；节点`wsl_4070`；一次完成                  |
| Runner实际wall | `4.096142977999989 s`，不是96小时                                                    |
| 实际peak RSS   | `122736640 B`                                                                   |
| 当次准入内存       | physical/effective均为`15428743168 B`；这是当次记录，不代表现在仍有这些资源                          |
| 合成测量工作       | 11,766个BCRH候选行、10,240个ticks、31,376个solver action records、502,016个created states |
| 完整BCRH投影     | `338401.855830688 s`                                                            |
| 精确solver投影   | `9152.017350242992 s`                                                           |
| 总投影          | `347623.18427552027 s`；原cap为`2700 s`                                            |
| 技术结论         | `VALID_RESULT_BLIND_CALIBRATION / BLOCKED_WALL_CAP`                             |
| 科学结果         | 无；完整census未实现、未执行                                                               |

上述数据来自完整机器证据的`summary`、`admission`和`supervisor`字段。总投影约为原cap的128.75倍，BCRH完整调用分项约占97.3%。这是上界工作量与合成单位计时组成的经验规划投影，不是实际完整运行时长，也不是任何语义等价实现均不可行的定理。

机器零暴露记录保持原样：

```text
new_rng_draws = 0
models = 0
optimizer_updates = 0
training_transitions = 0
checkpoints = 0
native_panel_worlds = 0
native_candidate_endpoints = 0
scientific_result = false
full_census_implemented = false
```

参数初始化尺度和参数位移不适用。合成计时与人工有理数solver输入不能充当目标面板终点；当前没有CI-A、CI-B或CI-C结果。

**原拒绝仍然成立。** 仅反对solver外推，不能消除已经超限的BCRH分项；反过来，只改善BCRH而保留现有9,152秒solver投影，也不足以准入完整对象。并且`R_fail_60`的60秒计分窗口不等于完整原生终局：每个候选仍须完成120秒post-loss episode及全部终局检查，不能截掉后半段降成本。

# PRESERVED_SCIENCE

## 不改变的问题、原生链与最强同信息null

保留原命名空间`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02/B1-B3-PRIMARY/2026090311`，`heldout-N7`，失败区1、2各八个历史世界，以及全部既定外生tape。偏离epoch仍为全局固定的`d∈{0,1,2}`；策略在此前及此后均执行不变的`BCRH-PERSIST`，只允许在`d`对完整、合法、因果历史采取一个合法物理命令。相同历史和mask必须共享命令；世界编号、未来tape、隐藏状态及动作后终点不能进入决策key。

原生链保持：

> 未预告executor loss → 幸存实体及角色责任变化 → BCRH实际公开历史与legal mask → 至多一次四token物理重分配 → 不变BCRH后续控制 → 60秒failed-zone服务比值，同时完成120秒原生终局及全部检查。

最强已接受同信息null仍是**不变的BCRH-PERSIST**，不是特权K搜索，也不是`1-R_BCRH`。精确类包含BCRH本身。证据类仍为A/RECON；科学MEI仍为绝对`0.10 R_fail_60`。

继续完整计算：

$$
D_z(\pi)=\frac18\sum_{i\in z}(R_i^\pi-R_i^{BCRH}),\qquad
D_{\rm all}(\pi)=\frac{D_1(\pi)+D_2(\pi)}2,
$$

$$
M_{\rm robust}=\max_\pi\min(D_1,D_2),\quad
M_{\rm all}=\max_\pi D_{\rm all},\quad
M_z=\max_\pi D_z.
$$

稳健主选择的tie顺序不变：较小区均值最大、aggregate最大、偏离历史类数最少、epoch最早、canonical物理action-map序列最小。稳健、aggregate及两个zone-optimal map都必须保留。CI-X／CI-A／CI-B／CI-C顺序及原谓词全部不变。

## 最强支持、反证与未解解释

**支持继续这一小步的科学证据**是局部物理机会确实存在：zone 2 row 3的特权witness为`7/60`；zone 1 row 5的K1024相对K256改善`1/8`，证明前驱确有剪枝损失。

**最强反证**是后者只追平BCRH/PERSIST，没有新增headroom下界。aggregate、zone 1、zone 2仍为`7/960`、`0`、`7/480`；十五个世界没有已见证的BCRH改善。历史64-update MAPR在held-out N7各seed均负于BCRH的预算特定观察也保留，不能被本次工程讨论抹除。

因此，局部机会、全局epoch兼容性限制、特权机会不能被该因果类实现，以及超出一次偏离的机制仍未被区分。当前成本证据没有为这些解释增加科学正负号。

前一完成节点的结论原样保留：

```text
PRO_FINAL=RECAST_ESTIMAND_OR_INFORMATION_BOUNDARY
DECISION_FORMED=true
BLOCKER=NONE
```

本次处理的是它规定的后续成本返回，不是重试一个未回答的问题，也不是推翻前一RECAST。特权宽度家族仍停在已接受K256/K1024，不再加宽。

# NEXT_SINGLE_OBJECT_OR_NONE

## 选定：`VNFC-R03-EXACT-BATCH-FEASIBILITY-E01`

该对象只回答：

> 对同一个完整R03，能否用一项预先界定的等价执行设计，给出覆盖全部原生计算、精确选择、检查和发布的可信成本准入路径，而不是继续沿用未经充分优化的串行实现投影？

它不测headroom，不选择native action map，不训练，不产生新的目标面板终点。工程成功门槛不是另一个科学MEI，而是完整性成立、成本有据、完整wall投影严格低于原`2700 s`，且所需资源政策已获正确节点处理。

### 一、先利用两个结果盲的结构事实，而非盲目增加核心数

#### 1. 公开失败区使原精确优化可分解——但不能各区自行选epoch

这是本次从冻结定义与已读源码得出的**数学推论，不是已运行的分组结果**。

`gobservation`明确公开失败区one-hot；技术合同要求完整key保留这些实际公开观测。因此，两个失败区的合规完整历史不可能相同。固定epoch下，每个历史类只属于一个失败区。该事实不依赖候选终点，也不需要读取行政zone标签。

设固定epoch下历史类\(h\)的候选命令贡献为

$$
q_h(a)=\sum_{i\in h}(R_i^a-R_i^{BCRH}).
$$

定义

$$
A_{z,d}=\frac18
\sum_{\substack{h\text{在epoch }d\\h\subset z}}
\max_{a\in\mathcal A_h}q_h(a).
$$

由于不同历史类的命令选择没有额外耦合，一个合法map可以同时达到两个区的\(A_{z,d}\)。固定\(d\)的稳健目标加aggregate次级目标因此由该逐类精确最大化达到。跨epoch仍必须执行：

$$
M_{\rm robust}=\max_d\min(A_{1,d},A_{2,d}),\qquad
M_{\rm all}=\max_d\frac{A_{1,d}+A_{2,d}}2,\qquad
M_z=\max_d A_{z,d}.
$$

**不能让zone 1选择一个epoch、zone 2选择另一个epoch来构成稳健策略。** 全局epoch限制保持原样，因而不同epoch之间仍可能存在机会不兼容。

实现必须完整保留原tie规则及四类map；尤其zone-optimal map在另一zone上的tie不能被aggregate-optimal map替代。现有`solver.py`已经分别处理scalar aggregate／zone目标，可作为这些tie语义的参考。

这个等价分解有机会把本对象的选择工作从通用双区Pareto扩展转为对全部历史类合法选项的精确扫描。其选项数上界仍不超过94,128；**所有候选终点仍须先完整获得，不能借此跳过native continuation。** 它改变计算实现，不改变estimator、policy类或信息边界，所以不构成RECAST。实际因果key尚未实现，故目前不能声称该优化已被源码验收。

#### 2. 检验跨调用公共权重复用，而不是重复宣称已有的调用内复用

已读`gweights`只依赖epoch、失败区、当前demand／blocked组合，以及已累计的fail／total demand；其返回权重不依赖候选所造成的服务分子、agent位置或所选命令。沿同一既定世界的同一epoch，这些需求累计量由外生输入决定。

因此，一个具体的等价候选设计是：**按这些实际公开输入的完整值tuple复用不可变权重**，而不是按world ID缓存。对原十六世界、六个post-loss epochs，scorer侧这类权重输入至多有96个world–epoch来源，再按实际tuple去重。

这只支持复用公共权重，不支持复用完整score、候选后果或隐藏状态。实际独立checker必须继续独立计算和检查；不能借用scorer输出来“证明相等”。本次清单没有展开`independent_checker`的实现，因此**尚不能给checker侧记入任何缓存收益，也不能认证其线程安全**。完整BCRH批次计时必须仍然包含它。

### 二、仅评估一项固定批处理设计

选择的执行候选是：

> **按公开公共输入分组的完整BCRH调用批处理，使用一个进程内的固定native并行团队；每条continuation内部保持原顺序，配合上述精确选择分解。**

并行单位是相互独立的完整调用／continuation工作，不是擅自并行同一轨迹的前后决策。线程数和batch宽度须在计时前根据**实际配置节点的CPU约束与内存可容纳值**写成具体值；不得按测得性能挑选，不得假设远端已有额外容量，不开多节点或多进程搜索。

该候选必须保留原精确整数／limb运算、数值语义、所有候选记录、独立枚举、独立checker和canonical tie。每个任务使用独立可变状态、独立输出缓冲；结果和错误按固定逻辑序号汇合，不能以完成先后决定动作或发布内容。调度用的世界地址不能流入因果决策key。上述线程安全、错误次序及发布行为目前均是**待验证事实**，不是本回复的源码接受结论。

只允许一份候选实现、一个固定配置和一次新的工程评估。评估fixture必须在执行前冻结，采用确定性非目标合成输入，覆盖六个epochs、同公共权重但不同物理状态、不同公共权重输入、完整候选记录、tie及完整数据发布路径。参考语义比较是新实现验证，不是再次运行原六调用校准来获取更好计时。

**若实际没有改变执行设计或被检验的不确定性，则不执行该评估：它会退化为被禁止的同一计时重复。**

### 三、完整成本律

旧计数与旧证据不删除：

$$
N_{\rm tick}^{+}=9{,}418{,}560,\quad
N_{\rm call}^{+}=376{,}688,\quad
N_{\rm row}^{+}=738{,}685{,}168,\quad
N_{\rm cont}^{+}=94{,}128.
$$

旧通用solver上界903,722,928次扩展及其9,152秒投影仍作为旧实现记录；只有上述等价选择实现得到验证后，才可以用其完整扫描／tie／map构造成本替代，而不是直接把solver项删掉。

拟议完整wall规划律为：

$$
\widehat T_{\rm wall}
=
60+
2\left[
N_{\rm tick}^{+}\hat t_{\rm tick}
+\sum_r Q_r^{+}\hat\tau^{\rm batch}_{r}(P)
+U_W^{+}\hat t_W
+\widehat T_{\rm exact\ selection}
+\widehat T_{\rm history/records/publication}
+96\hat t_{\rm prehistory}
+\widehat T_{\rm uncovered}
\right].
$$

这里：

* \(Q_r^{+}\)是完整支持下必须执行的批次数；\(\hat\tau^{\rm batch}_{r}(P)\)必须来自**该固定配置的完整批次**，包含scorer、独立checker、枚举、记录核对、必要分配、同步和汇合，不能用旧串行时间除以\(P\)。
* \(U_W^{+}\hat t_W\)只单列经验证可共享的权重构造；同一成本不得漏计或重复扣除。未验证的checker优化收益一律不计。
* history、精确选择、输出构造、磁盘发布及未覆盖工作必须逐项有来源。保留原factor 2及60秒固定allowance；allowance不够时报告缺口，不能假装已覆盖。
* 并行时另报**aggregate CPU工作量**与peak RSS。`wall<2700`不等于CPU工作量也小于2700；二者不能混用。未知吞吐量或未覆盖阶段不能填零。

该律仍是经验准入规划，不是普遍运行时间定理。当前所有新单位成本均未知，本回复不赋予任何加速倍数或新的“实测秒数”。

### 四、额度、停止与两个有判别力的结果

**拟议新增工程评估wall上限为60秒，仅作为提交正确Portfolio节点的明确提案，不是现有授权。** 原校准额度已经使用，不能把其未用完的时间当作余额，也不能通过改名重置。并行评估的aggregate CPU上限须在同一方案中按固定线程配置明确列出。源码仍从原R03基线累计计数，保留2,000行、600行runner、现行编排及测试预算；已有483行非测试源码和58行runner不是一笔可重置的额度。

| 评估结果                                  | 能区分的解释与下一边界                                                                                                                       |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **等价性及覆盖成立，完整成本投影严格低于2700秒，所需资源政策明确** | 支持“当前拒绝主要依赖特定执行设计／保守核算，未证明该有限对象本身不可做”。可进入原R03完整实现与技术接受；仍须补齐因果key、完整census及发布，随后才可能按修订后的明确执行政策、fresh admission和原单结果限制运行。不是CI-A。    |
| **不等价、覆盖不足、成本仍超限、评估超时，或资源／规范方案未成立**   | 停止这一项工程投入，保留具体缺口和`BLOCKED_WALL_CAP`或相应工程状态，返回本Convergence节点。不得继续自动调核数、换机器、改fixture或追加计时。它不证明没有headroom，也不自动产生CI-C或Portfolio PARK。 |

这项投入之所以值得选择，是因为它同时针对**真实但尚未利用的结构简化**和**尚未验证的执行并发性**，而不是仅要求“再优化一下”。反对它的最强理由也保留：128.75倍的原始差距很大；即使某些项显著改善，完整路径仍可能远超预算。选择这一小步不构成“最终一定能跑”的承诺。

# RECAST_AND_PORTFOLIO_BOUNDARIES

本次没有改变estimator、信息、policy类、host、完整支持或科学结果规则，因此**不新增科学RECAST**；保留已有`recasts: 2`及其既有排序，不作Portfolio生命周期或priority变更。已有其他方向的对象限定工程例外不能继承到VNFC。

直接的下一程序性动作是：将上述E01作为**唯一方案**送正确Portfolio Pro节点，明确处理原R03单线程限制、一次新增结果盲工程评估额度，以及必要的固定native并行／成本报告范围。**本次不提议扩大完整R03的2700秒wall cap。** 若以后完整运行需要新增aggregate CPU额度或其他工程预算，也必须在正确节点的方案中定量列明，不能由“wall仍是2700”暗中取得。

最新授权记录已经移除了这类完整Pro方案之后的重复逐项所有者投票；Root应按正确节点形成的方案执行并保留高亮来源／应用痕迹。仍需正确节点的方案，不等于仍需重新请求所有者逐项批准。

精确等价验证在这里服务于**原本就定义为精确census的这个A对象**，不是对其他A/B研究追加C-FORMAL义务，也不新增learner启动门槛。

# ACTUALLY_READ_PATHS

以下20个清单路径均通过连接的GitHub只读接口，在本回复顶部的**同一固定提交**读取。除`DIRECTION.md`读取第1–150行外，其余全文读取；长响应截断部分通过同一路径、同一ref的后续行窗口补读。前一节点完整response已读至末尾。

```text
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_INTAKE_AND_PAUSE_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_E0_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_CALIBRATION_EVIDENCE_20260904.json
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_COST_ACCOUNTING_ADDENDUM_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_TECHNICAL_CONTRACT_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_A_RECON_CAUSAL_ONE_DEVIATION_R03_SCIENCE_CARD_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CAUSAL_ONE_DEVIATION_R03_CONTINUATION_INTAKE_20260904.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_RECAST_ESTIMAND_CONVERGENCE_02_INTAKE_20260904.md
docs/research/candidates/variable_n_fleet_churn/external/2026-09-04-vnfc-controller-headroom-convergence-02/2026-09-04-vnfc-controller-headroom-convergence-02--variable_n_fleet_churn--attempt-01__02_RESPONSE.md
docs/research/candidates/variable_n_fleet_churn/VNFC_CONTROLLER_HEADROOM_A_RECON_MEMORY_BOUNDED_K1024_R02_RESULT_EVIDENCE_20260904.md
docs/research/candidates/variable_n_fleet_churn/DIRECTION.md
experiments/candidates/variable_n_fleet_churn_causal_headroom/calibration.py
experiments/candidates/variable_n_fleet_churn_causal_headroom/native/calibration.cpp
experiments/candidates/variable_n_fleet_churn_causal_headroom/solver.py
docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
docs/project/ENGINEERING_SCOPE_SPEC.md
docs/research/candidates/variable_n_fleet_churn/VNFC_R03_CPP_BATCH_PARALLEL_REVIEW_20260905.md
experiments/candidates/variable_n_fleet_churn_causal_headroom/native_backend.py
experiments/candidates/variable_n_fleet_churn_bpcr_r09/native/bpcr_general.hpp
docs/research/portfolio/decisions/2026-09-05-pro-directed-spec-delegation.md
```

**连接器、repository、ref及列明路径的访问缺口：无。** 未读取移动分支、未列明仓库文件、web镜像或本地clone；未执行代码、重做计时或修改仓库。

**尚未验证的执行事实：** 新批处理实现及其线程安全；独立checker依赖的并发行为；实际可用CPU容量；新配置的完整吞吐量、CPU工作量与内存；完整因果key、native census及发布路径；正确Portfolio节点的对象限定执行方案。这些是所选下一步要解决的具体缺口，不是本节点无法形成方向裁决的连接器阻塞。

# DECISION_TEXT

```text
REQUEST_ID=2026-09-05-vnfc-r03-cost-convergence-01
PINNED_REFERENCE=3d0171e0d53f53b602092e9791f45ea00e803568
DECISION_AUTHORITY=PRO_FINAL
DECISION_FORMED=true
FINAL_DECISION=CONTINUE
SMALLEST_SUPPORTED_FAMILY=VNFC-CONTROLLER-HEADROOM-A-RECON-CAUSAL-ONE-DEVIATION-R03
NEXT_SINGLE_OBJECT=VNFC-R03-EXACT-BATCH-FEASIBILITY-E01
CURRENT_EXECUTION_STATUS=BLOCKED_WALL_CAP
CONNECTOR_GAP=NONE

接受并保留唯一已完成校准的VALID_RESULT_BLIND_CALIBRATION /
BLOCKED_WALL_CAP。347623.18427552027秒是完整操作上界与合成计时组成的
经验规划投影，不是实际96小时运行、无headroom结果或普遍不可实现定理。
当前scientific_result=false，full_census_implemented=false；
目标面板、候选终点、learner、训练、checkpoint和新RNG暴露均为零。

保留原R03全部科学含义：N7、十六历史世界、epochs0/1/2、
一个全局固定epoch的至多一次因果历史keyed合法命令、不变BCRH前后控制、
全部合法continuations、60秒原生指标及120秒完整原生终局、
全部检查和观测、精确四类最优map、原tie、MEI0.10及CI分支顺序。

唯一继续投入是一项结果盲的等价批处理可行性评估。
选定路线为公开输入公共权重复用、固定进程内native批处理，
以及利用公开失败区使历史类不跨区的精确选择分解。
不得改变全局epoch限制，不得跳过任何候选native后果，
不得以scorer输出替代独立checker，不得按核心数除旧投影准入。
上述路线尚未实现或技术接受，不承诺加速或完整可行。

原完整运行wall cap保持2700秒，不放行census，不重跑旧校准。
拟议一次新增工程评估上限60秒及并行执行政策须先交正确Portfolio
Pro节点形成对象限定完整方案；额外CPU和工程额度不得默认取得。
正确节点形成方案后，Root按最新所有者常设委托执行并高亮追踪，
无需再次逐项所有者投票。其他方向例外不适用。

评估只有在等价性、完整覆盖、全部成本项及资源政策成立时才支持
继续原R03完整实现与技术接受；不是科学阳性。否则停止本项投入，
带精确缺口返回Convergence，不自动追加优化、计时、预算或科学对象。

本次不新增科学RECAST，不变更recasts:2、Portfolio生命周期或priority。
保留MB1024-D、7/960、0、7/480、7/60特权witness及历史MAPR反证。
前一完成节点RECAST_ESTIMAND_OR_INFORMATION_BOUNDARY及其完整原文保留。
```
